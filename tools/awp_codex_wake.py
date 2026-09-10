"""Queue bounded COOP-2 delivery notices into a running Codex thread.

This is a host adapter, not a second AWP transport.  It polls the
authoritative project ledger and sends only an event identifier to Codex; the
receiving turn must read the ledger itself.  The adapter needs a trusted local
Codex app-server endpoint and a thread identifier supplied by the host that
started it.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    # Support `python awp_codex_wake.py` from the tools directory as well as
    # package execution via `python -m tools.awp_codex_wake`.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coop2 import Rendezvous
    from tools.awp_runtime import atomic_json, control_is_current
else:
    from .awp_coop2 import Rendezvous
    from .awp_runtime import atomic_json, control_is_current


PROFILE = "codex-local-queue-watcher-v1"
QUEUE_TIMEOUT_SECONDS = 30
MAX_NOTIFIED_EVENTS = 256


def _state_path_usable(path: Path) -> bool:
    """Check that both a watcher cursor and its lock can be opened."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        for candidate in (path, path.with_name(path.name + ".lock")):
            existed = candidate.exists()
            with candidate.open("a+b"):
                pass
            if not existed:
                candidate.unlink()
        return True
    except OSError:
        return False


def default_state_path(project: Path, actor: str = "actor:codex") -> tuple[Path, bool]:
    """Return an actor-scoped cursor location, preferring project runtime."""
    actor_digest = hashlib.sha256(actor.encode("utf-8")).hexdigest()[:12]
    preferred = project / ".awp-runtime" / f"coop2-codex-watcher-{actor_digest}.json"
    if _state_path_usable(preferred):
        return preferred, False
    digest = hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()[:12]
    fallback = Path(tempfile.gettempdir()) / "awp" / f"coop2-codex-watcher-{digest}-{actor_digest}.json"
    if not _state_path_usable(fallback):
        raise OSError("no writable watcher state path is available")
    return fallback, True


def bounded_event_ids(values: list[str]) -> list[str]:
    """Keep a bounded, order-preserving at-least-once notification cursor."""
    unique_reversed: list[str] = []
    seen: set[str] = set()
    for value in reversed(values):
        if value not in seen:
            seen.add(value)
            unique_reversed.append(value)
    return list(reversed(unique_reversed))[-MAX_NOTIFIED_EVENTS:]


class CodexQueueWatcher:
    def __init__(self, rendezvous: Rendezvous, actor: str, thread: str, remote: str | None, state_path: Path) -> None:
        self.rendezvous = rendezvous
        self.actor = actor
        self.thread = thread
        self.remote = remote
        self.state_path = state_path

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"profile": PROFILE, "initialized": False, "notified_events": []}
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"profile": PROFILE, "initialized": False, "notified_events": []}
        return value if value.get("profile") == PROFILE else {"profile": PROFILE, "initialized": False, "notified_events": []}

    @contextmanager
    def _claim_lock(self):
        """Serialize cursor claim and queue publication across watcher processes."""
        lock_path = self.state_path.with_name(self.state_path.name + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock:
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    lock.seek(0)
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def pending_events(self, events: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
        notified = set(state.get("notified_events", []))
        answered = {
            event["payload"].get("interaction_id")
            for event in events
            if event["kind"] in {"coop2.interaction.responded", "coop2.interaction.withdrawn"}
        }
        result = []
        for event in events:
            payload = event["payload"]
            is_delivery = (
                event["kind"] == "coop2.interaction.requested"
                and payload.get("recipient") == self.actor
                and payload.get("interaction_id") not in answered
                and not self._delivery_expired(event)
            ) or (
                event["kind"] == "coop2.interaction.responded"
                and payload.get("recipient") == self.actor
                and state.get("initialized", False)
            ) or (
                event["kind"] == "coop2.tickle.sent"
                and payload.get("recipient") == self.actor
                and not any(
                    item["kind"] == "coop2.tickle.acked"
                    and item["payload"].get("tickle_id") == payload.get("tickle_id")
                    for item in events
                )
            ) or (
                event["kind"] == "coop2.tickle.acked"
                and payload.get("recipient") == self.actor
                and state.get("initialized", False)
            )
            if is_delivery and event["event_id"] not in notified:
                result.append(event)
        return result

    @staticmethod
    def _delivery_expired(event: dict[str, Any]) -> bool:
        """Keep expired mailbox items durable, but do not wake a fresh session for them."""
        if event.get("kind") != "coop2.interaction.requested":
            return False
        try:
            occurred_at = datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
            seconds = int(event["payload"]["authorization"]["delivery_window_seconds"])
        except (KeyError, TypeError, ValueError, AttributeError):
            return False
        return datetime.now(timezone.utc) > occurred_at + timedelta(seconds=seconds)

    @staticmethod
    def _command(arguments: list[str]) -> list[str]:
        executable = Path(shutil.which("codex") or "codex")
        if executable.suffix.lower() == ".ps1":
            return ["powershell", "-NoProfile", "-File", str(executable), *arguments]
        return [str(executable), *arguments]

    @staticmethod
    def _hidden_process_options() -> dict[str, Any]:
        """Prevent a background watcher from stealing the user's desktop on Windows."""
        if os.name != "nt":
            return {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        return {
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
            "startupinfo": startupinfo,
        }

    def queue(self, event: dict[str, Any]) -> None:
        payload = event["payload"]
        if event["kind"] == "coop2.tickle.sent":
            message = (
                f"AWP COOP-2 reachability probe {payload['tickle_id']} arrived in event {event['event_id']} "
                "and was acknowledged by the host watcher. This is path evidence, not authority "
                "for repository changes."
            )
        elif event["kind"] == "coop2.tickle.acked":
            message = (
                f"AWP COOP-2 reachability probe {payload['tickle_id']} was acknowledged in event {event['event_id']}. "
                "This is path evidence, not authority for repository changes."
            )
        else:
            interaction_id = payload["interaction_id"]
            message = (
                f"AWP COOP-2 delivery event {event['event_id']} for {interaction_id}. "
                f"Run `python -m tools.awp_coop2 inbox --actor {self.actor}` and handle only "
                "that interaction under its recorded authorization. Do not treat this "
                "notification as authority for repository changes."
            )
        arguments = ["queue"]
        if self.remote:
            arguments.extend(["--remote", self.remote])
        arguments.extend(["--thread", self.thread, "--message", message])
        subprocess.run(
            self._command(arguments),
            check=True,
            capture_output=True,
            text=True,
            timeout=QUEUE_TIMEOUT_SECONDS,
            **self._hidden_process_options(),
        )

    def _heartbeat(self) -> dict[str, Any] | None:
        """Publish liveness so the binding can observe this watcher instead of assuming it."""
        publish = getattr(self.rendezvous, "heartbeat", None)
        if publish is None:
            return None
        try:
            return publish(self.actor, PROFILE)
        except Exception as error:  # liveness must never break delivery
            return {"error": str(error)}

    def step(self) -> dict[str, Any]:
        with self._claim_lock():
            state = self._state()
            events = self.rendezvous._events()
            heartbeat = self._heartbeat()
            initializing = not state.get("initialized", False)
            queued: list[str] = []
            failed: list[str] = []
            for event in self.pending_events(events, state):
                try:
                    self.queue(event)
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError) as error:
                    failed.append(event["event_id"])
                    state["delivery_state"] = "unavailable"
                    state["last_error"] = str(error)
                    state["last_failed_event"] = event["event_id"]
                    atomic_json(self.state_path, state)
                    break
                queued.append(event["event_id"])
                state["notified_events"] = bounded_event_ids(
                    [*state.get("notified_events", []), event["event_id"]]
                )
                state["delivery_state"] = "available"
                state.pop("last_error", None)
                state.pop("last_failed_event", None)
                atomic_json(self.state_path, state)
            if initializing:
                historical_responses = [
                    event["event_id"]
                    for event in events
                    if event["kind"] == "coop2.interaction.responded"
                    and event["payload"].get("recipient") == self.actor
                ]
                state["notified_events"] = bounded_event_ids(
                    [*state.get("notified_events", []), *historical_responses]
                )
                state["initialized"] = True
                atomic_json(self.state_path, state)
            result = {"profile": PROFILE, "queued_events": queued, "failed_events": failed,
                      "transport_state": "transport_queued" if queued else "idle",
                      "state_path": str(self.state_path)}
            if heartbeat is not None:
                result["heartbeat"] = {key: heartbeat[key] for key in ("last_seen", "path", "error") if key in heartbeat}
            return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path)
    result.add_argument("--actor", default="actor:codex")
    result.add_argument("--thread", required=True, help="Codex app-server thread identifier")
    result.add_argument(
        "--remote",
        help="optional Codex app-server endpoint; omit to use the host's local session state",
    )
    result.add_argument("--state", type=Path)
    result.add_argument("--control", type=Path, help="session-bootstrap control record")
    result.add_argument("--generation", help="generation expected in the control record")
    result.add_argument("--interval-seconds", type=float, default=5.0)
    result.add_argument("--once", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    rendezvous = Rendezvous(args.project, args.ledger)
    state, state_fallback = (
        (args.state, False) if args.state else default_state_path(rendezvous.project, args.actor)
    )
    watcher = CodexQueueWatcher(rendezvous, args.actor, args.thread, args.remote, state)
    while True:
        if not control_is_current(args.control, args.generation):
            return 0
        try:
            result = watcher.step()
        except Exception as error:
            print(json.dumps({"profile": PROFILE, "state": "retrying", "error": str(error)}, sort_keys=True), flush=True)
            time.sleep(min(max(args.interval_seconds * 2, 1.0), 60.0))
            continue
        if state_fallback:
            result["state_fallback"] = "temporary-user-runtime"
        if result["queued_events"] or args.once:
            print(json.dumps(result, sort_keys=True), flush=True)
        if args.once:
            return 0
        if not control_is_current(args.control, args.generation):
            return 0
        delay = max(args.interval_seconds, 0.1)
        if result.get("failed_events"):
            delay = min(max(delay * 2, 1.0), 60.0)
        time.sleep(delay)


if __name__ == "__main__":
    raise SystemExit(main())
