"""Queue bounded COOP-2 delivery notices into a running Codex thread.

This is a host adapter, not a second AWP transport.  It polls the
authoritative project ledger and sends only an event identifier to Codex; the
receiving turn must read the ledger itself.  The adapter needs a trusted local
Codex app-server endpoint and a thread identifier supplied by the host that
started it.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

from .awp_coop2 import Rendezvous


PROFILE = "codex-local-queue-watcher-v1"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as temporary:
            json.dump(value, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


class CodexQueueWatcher:
    def __init__(self, rendezvous: Rendezvous, actor: str, thread: str, remote: str, state_path: Path) -> None:
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

    def pending_events(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        notified = set(state.get("notified_events", []))
        answered = {
            event["payload"].get("interaction_id")
            for event in self.rendezvous._events()
            if event["kind"] == "coop2.interaction.responded"
        }
        result = []
        for event in self.rendezvous._events():
            payload = event["payload"]
            is_delivery = (
                event["kind"] == "coop2.interaction.requested"
                and payload.get("recipient") == self.actor
                and payload.get("interaction_id") not in answered
            ) or (
                event["kind"] == "coop2.interaction.responded"
                and payload.get("recipient") == self.actor
                and state.get("initialized", False)
            )
            if is_delivery and event["event_id"] not in notified:
                result.append(event)
        return result

    @staticmethod
    def _command(arguments: list[str]) -> list[str]:
        executable = Path(shutil.which("codex") or "codex")
        if executable.suffix.lower() == ".ps1":
            return ["powershell", "-NoProfile", "-File", str(executable), *arguments]
        return [str(executable), *arguments]

    def queue(self, event: dict[str, Any]) -> None:
        interaction_id = event["payload"]["interaction_id"]
        message = (
            f"AWP COOP-2 delivery event {event['event_id']} for {interaction_id}. "
            f"Run `python -m tools.awp_coop2 inbox --actor {self.actor}` and handle only "
            "that interaction under its recorded authorization. Do not treat this "
            "notification as authority for repository changes."
        )
        subprocess.run(
            self._command(["queue", "--remote", self.remote, "--thread", self.thread, "--message", message]),
            check=True,
            capture_output=True,
            text=True,
        )

    def step(self) -> dict[str, Any]:
        state = self._state()
        initializing = not state.get("initialized", False)
        queued: list[str] = []
        for event in self.pending_events(state):
            self.queue(event)
            queued.append(event["event_id"])
            state["notified_events"] = [*state.get("notified_events", []), event["event_id"]]
            atomic_json(self.state_path, state)
        if initializing:
            historical_responses = [
                event["event_id"]
                for event in self.rendezvous._events()
                if event["kind"] == "coop2.interaction.responded"
                and event["payload"].get("recipient") == self.actor
            ]
            state["notified_events"] = list(dict.fromkeys([
                *state.get("notified_events", []), *historical_responses
            ]))
            state["initialized"] = True
            atomic_json(self.state_path, state)
        return {"profile": PROFILE, "queued_events": queued, "state_path": str(self.state_path)}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path)
    result.add_argument("--actor", default="actor:codex")
    result.add_argument("--thread", required=True, help="Codex app-server thread identifier")
    result.add_argument("--remote", default="ws://127.0.0.1:8765")
    result.add_argument("--state", type=Path)
    result.add_argument("--interval-seconds", type=float, default=5.0)
    result.add_argument("--once", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    rendezvous = Rendezvous(args.project, args.ledger)
    state = args.state or rendezvous.project / ".awp-runtime" / "coop2-codex-watcher.json"
    watcher = CodexQueueWatcher(rendezvous, args.actor, args.thread, args.remote, state)
    while True:
        result = watcher.step()
        if result["queued_events"] or args.once:
            print(json.dumps(result, sort_keys=True), flush=True)
        if args.once:
            return 0
        time.sleep(max(args.interval_seconds, 0.1))


if __name__ == "__main__":
    raise SystemExit(main())
