"""Host-neutral AWP Git-hint and durable-ledger delivery supervisor."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence

from .awp_activation import CLIResumeAdapter, CommandAdapter, HostAdapter, parse_command
from .awp_request_spool import RequestSpool, safe_token
from .awp_runtime import atomic_json, control_is_current, hidden_process_options
from .awp_coop2 import Rendezvous


PROFILE = "awp-supervisor-v1"


def route_id(actor: str, host: str, session_ref: str) -> str:
    digest = hashlib.sha256(f"{actor}\0{host}\0{session_ref}".encode()).hexdigest()[:24]
    return f"route:{digest}"


class Supervisor:
    def __init__(self, rendezvous: Rendezvous, actor: str, host: str, session_ref: str,
                 generation: str, adapter: HostAdapter, state_path: Path) -> None:
        self.rendezvous = rendezvous
        self.actor = actor
        self.host = host
        self.session_ref = session_ref
        self.generation = generation
        self.adapter = adapter
        self.state_path = state_path
        self.spool = RequestSpool(getattr(rendezvous, "project", state_path.parent))
        self.route = route_id(actor, host, session_ref)

    def state(self) -> dict[str, Any]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = {}
        if value.get("profile") != PROFILE or value.get("actor") != self.actor:
            return {"profile": PROFILE, "actor": self.actor, "route_id": self.route,
                    "route_generation": self.generation, "cursor": 0, "jobs": {}}
        value.update({"route_id": self.route, "route_generation": self.generation})
        return value

    def _is_actionable(self, event: dict[str, Any], all_events: list[dict[str, Any]]) -> bool:
        payload = event.get("payload", {})
        if payload.get("recipient") != self.actor:
            return False
        if event["kind"] == "coop2.tickle.sent":
            if _tickle_expired(event):
                return False
            return not any(item["kind"] == "coop2.tickle.acked" and item.get("payload", {}).get("tickle_id") == payload.get("tickle_id") for item in all_events)
        if event["kind"] == "coop2.interaction.requested":
            terminal = {"coop2.interaction.responded", "coop2.interaction.withdrawn", "coop2.interaction.refused"}
            return not any(item["kind"] in terminal and item.get("payload", {}).get("interaction_id") == payload.get("interaction_id") for item in all_events)
        if event["kind"] in {"coop2.tickle.acked", "coop2.interaction.responded"}:
            floor = getattr(self, "_informational_floor", None)
            return not floor or str(event.get("occurred_at", "")) >= floor
        return False

    def _envelope(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload", {})
        return {
            "type": "cooperation_activation_envelope",
            "module": "urn:awp:cooperation",
            "profile": "awp-host-activation-v1",
            "operation_id": f"deliver:{self.route}:{event['event_id']}",
            "binding_id": self.rendezvous.ledger.binding_id(),
            "project_id": self.rendezvous.project_id,
            "workstate_id": self.rendezvous.workstate_id,
            "recipient_actor": self.actor,
            "route_id": self.route,
            "route_generation": self.generation,
            "event_id": event["event_id"],
            "event_kind": event["kind"],
            "interaction_id": payload.get("interaction_id") or payload.get("tickle_id"),
            "ledger_frontier": self.rendezvous.ledger.refresh(self.rendezvous.workstate_id)["frontier"],
        }

    def _receipt(self, event: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload", {})
        if event["kind"] == "coop2.tickle.sent":
            kind = "coop2.tickle.transport_queued"
        elif event["kind"] == "coop2.tickle.acked":
            kind = "coop2.tickle.ack.transport_queued"
        else:
            kind = "coop2.interaction.transport_queued"
        if result["state"] != "accepted":
            kind = kind.rsplit(".", 1)[0] + ".transport_" + result["state"]
        return self.rendezvous._append("actor:awp-supervisor", kind, {
            "event_id": event["event_id"],
            "interaction_id": payload.get("interaction_id") or payload.get("tickle_id"),
            "recipient": self.actor,
            "route_id": self.route,
            "route_generation": self.generation,
            "transport_state": result["state"],
            "endpoint_receipt": result.get("endpoint_receipt"),
            "reason": result.get("reason"),
        })

    def step(self, limit: int = 256) -> dict[str, Any]:
        ingress = self.spool.process(
            self._handle_request, limit=limit,
            accept=lambda envelope: envelope.get("client_id") == self.actor,
        )
        state = self.state()
        ledger = self.rendezvous.ledger
        cursor = state.get("cursor", 0)
        profile = getattr(ledger, "profile", "sqlite")
        if state.get("ledger_profile", profile) != profile:
            cursor = None  # a new store: replay it; jobs below keep delivery idempotent
        if not cursor:
            # Replaying from the beginning (first start, lost state, or a new
            # store) must still deliver open requests and live probes, but
            # historical acknowledgements and responses are marked seen rather
            # than re-announced to the agent (Section 5.1.1's first-start rule).
            state["informational_floor"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if profile == "git-ledger-v1":
            cursor = cursor if isinstance(cursor, dict) else {}
        else:
            cursor = int(cursor) if isinstance(cursor, (int, str)) and str(cursor).isdigit() else 0
        state["ledger_profile"] = profile
        self._informational_floor = state.get("informational_floor")
        page = ledger.events_after(self.rendezvous.workstate_id, cursor, limit)
        all_events = self.rendezvous._events()
        delivered, deferred, unavailable = [], [], []
        acknowledged = []
        for event in page["events"]:
            sequence = event.pop("_ledger_sequence")
            if event["event_id"] not in state["jobs"] and self._is_actionable(event, all_events):
                # Every actionable event, reachability probes included, goes to
                # the recipient agent through the host adapter.  The supervisor
                # records only a transport receipt as actor:awp-supervisor; an
                # acknowledgement exists only after the agent's own turn runs
                # ingress (or tickle-ack), so a probe measures agent reach.
                result = self.adapter.deliver(self._envelope(event))
                receipt = self._receipt(event, result)
                state["jobs"][event["event_id"]] = {"state": result["state"], "receipt": receipt["event_id"]}
                {"accepted": delivered, "deferred": deferred, "unavailable": unavailable}[result["state"]].append(event["event_id"])
                if result["state"] != "accepted":
                    atomic_json(self.state_path, state)
                    break
            state["cursor"] = sequence
            atomic_json(self.state_path, state)
        heartbeat = self.rendezvous.heartbeat(self.actor, PROFILE)
        return {"profile": PROFILE, "cursor": state["cursor"], "delivered": delivered,
                "deferred": deferred, "unavailable": unavailable,
                "acknowledged": acknowledged,
                "ingress_processed": len(ingress), "heartbeat": heartbeat}

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("actor") != self.actor:
            raise ValueError("ingress actor does not match supervisor route")
        event_id = request.get("event_id")
        event = next((item for item in self.rendezvous._events() if item["event_id"] == event_id), None)
        if event is None or event.get("payload", {}).get("recipient") != self.actor:
            raise ValueError("unknown or misaddressed ingress event")
        payload = event["payload"]
        via = request.get("via") if request.get("via") in {"agent-ingress", "host-prompt-hook"} else "agent-ingress"
        evidence = request.get("evidence") if isinstance(request.get("evidence"), dict) else None
        if event["kind"] == "coop2.tickle.sent":
            return self.rendezvous.tickle_ack(self.actor, payload["tickle_id"], via=via, evidence=evidence)
        if event["kind"] == "coop2.interaction.requested":
            return self.rendezvous.observe(self.actor, payload["interaction_id"], via=via, evidence=evidence)
        return {"publication": "not-required", "event_id": event_id}


def _tickle_expired(event: dict[str, Any]) -> bool:
    try:
        sent = datetime.fromisoformat(str(event["occurred_at"]).replace("Z", "+00:00"))
        ttl = int(event.get("payload", {})["ttl_seconds"])
    except (KeyError, TypeError, ValueError):
        return False
    return datetime.now(timezone.utc) > sent + timedelta(seconds=ttl)


class SignalWatch:
    """Wake trigger: a change in the Git signal-ref namespace.

    Publishing any COOP-2 event writes ``refs/awp/signal/<event>`` in the Git
    common directory.  The watch fingerprints that namespace (loose refs and
    packed-refs) plus this actor's ingress spool with plain ``stat`` and
    directory listings, so waiting costs no child processes.  A changed
    fingerprint is only a hint: the supervisor then replays the authoritative
    ledger from its cursor.
    """

    def __init__(self, project: Path, actor: str) -> None:
        self.project = project.resolve()
        common = self._git_common_dir(self.project)
        self.paths = [common / "refs" / "awp" / "signal", common / "refs" / "awp" / "ledger", common / "packed-refs",
                      self.project / ".awp-runtime" / "requests" / safe_token(actor)]

    @staticmethod
    def _git_common_dir(project: Path) -> Path:
        try:
            completed = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=project,
                                       capture_output=True, text=True, check=False, timeout=15,
                                       **hidden_process_options())
            value = completed.stdout.strip() if completed.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            value = ""
        path = Path(value) if value else project / ".git"
        return path if path.is_absolute() else (project / path).resolve()

    def fingerprint(self) -> tuple:
        parts = []
        for path in self.paths:
            try:
                stat = path.stat()
            except OSError:
                parts.append((str(path), None))
                continue
            entries: tuple = ()
            if path.is_dir():
                found = []
                for root, _dirs, files in os.walk(path):
                    for name in files:
                        try:
                            item = os.stat(os.path.join(root, name))
                        except OSError:
                            continue
                        found.append((os.path.relpath(os.path.join(root, name), path), item.st_mtime_ns, item.st_size))
                entries = tuple(sorted(found))
            parts.append((str(path), stat.st_mtime_ns, stat.st_size, entries))
        return tuple(parts)


def _code_fingerprint() -> tuple:
    tools = Path(__file__).resolve().parent
    return tuple(sorted((item.name, item.stat().st_mtime_ns) for item in tools.glob("awp_*.py")))


def _relaunch(argv: Sequence[str], state_path: Path) -> None:
    """Replace this process with one running the current code, same generation."""
    flags = 0
    if os.name == "nt":
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    stem = state_path.with_suffix("")
    with open(f"{stem}.out.log", "ab") as output, open(f"{stem}.err.log", "ab") as error:
        subprocess.Popen([sys.executable, "-m", "tools.awp_supervisor", *argv],
                         cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL,
                         stdout=output, stderr=error, close_fds=True, creationflags=flags,
                         start_new_session=os.name != "nt")


def _claim_control(control: Path | None, generation: str) -> None:
    if control is None:
        return
    try:
        value = json.loads(control.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if value.get("generation") == generation and value.get("pid") != os.getpid():
        value["pid"] = os.getpid()
        atomic_json(control, value)


def default_state(project: Path, actor: str) -> Path:
    token = hashlib.sha256(actor.encode()).hexdigest()[:12]
    return project / ".awp-runtime" / f"awp-supervisor-{token}.json"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path)
    result.add_argument("--actor", required=True)
    result.add_argument("--host", required=True)
    result.add_argument("--session-ref", required=True)
    result.add_argument("--generation", required=True)
    result.add_argument("--adapter-command")
    result.add_argument("--state", type=Path)
    result.add_argument("--control", type=Path)
    result.add_argument("--interval-seconds", type=float, default=5.0,
                        help="safety replay interval when no Git signal arrives (also bounds heartbeat age)")
    result.add_argument("--signal-poll-seconds", type=float, default=0.25,
                        help="how often the Git signal-ref fingerprint is checked")
    result.add_argument("--once", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    rendezvous = Rendezvous(args.project, args.ledger)
    adapter_command = parse_command(args.adapter_command)
    adapter = CommandAdapter(adapter_command) if adapter_command else CLIResumeAdapter(args.host, args.session_ref)
    state_path = args.state or default_state(rendezvous.project, args.actor)
    supervisor = Supervisor(rendezvous, args.actor, args.host, args.session_ref, args.generation,
                            adapter, state_path)
    watch = SignalWatch(rendezvous.project, args.actor)
    code = _code_fingerprint()
    _claim_control(args.control, args.generation)
    trigger = "start"
    while True:
        if not control_is_current(args.control, args.generation):
            return 0
        seen = watch.fingerprint()
        output = supervisor.step()
        output["trigger"] = trigger
        if args.once or output["delivered"] or output["deferred"] or output["unavailable"]:
            print(json.dumps(output, sort_keys=True), flush=True)
        if args.once:
            return 0 if not output["unavailable"] else 2
        # Wait for a Git signal-ref change (the doorbell) or the safety replay.
        deadline = time.monotonic() + max(args.interval_seconds, 0.1)
        trigger = "replay"
        while time.monotonic() < deadline:
            if not control_is_current(args.control, args.generation):
                return 0
            if watch.fingerprint() != seen:
                trigger = "git-signal"
                break
            time.sleep(max(args.signal_poll_seconds, 0.05))
        if _code_fingerprint() != code:
            _relaunch(list(argv) if argv is not None else sys.argv[1:], state_path)
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
