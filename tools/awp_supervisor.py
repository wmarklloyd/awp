"""Host-neutral AWP Git-hint and durable-ledger delivery supervisor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Sequence

from .awp_activation import CLIResumeAdapter, CommandAdapter, HostAdapter, parse_command
from .awp_request_spool import RequestSpool
from .awp_runtime import atomic_json, control_is_current
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
            return not any(item["kind"] == "coop2.tickle.acked" and item.get("payload", {}).get("tickle_id") == payload.get("tickle_id") for item in all_events)
        if event["kind"] == "coop2.interaction.requested":
            terminal = {"coop2.interaction.responded", "coop2.interaction.withdrawn", "coop2.interaction.refused"}
            return not any(item["kind"] in terminal and item.get("payload", {}).get("interaction_id") == payload.get("interaction_id") for item in all_events)
        return event["kind"] in {"coop2.tickle.acked", "coop2.interaction.responded"}

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
        page = self.rendezvous.ledger.events_after(self.rendezvous.workstate_id, int(state["cursor"]), limit)
        all_events = self.rendezvous._events()
        delivered, deferred, unavailable = [], [], []
        acknowledged = []
        for event in page["events"]:
            sequence = event.pop("_ledger_sequence")
            if self._is_actionable(event, all_events):
                if event["kind"] == "coop2.tickle.sent":
                    # A reachability probe is transport plumbing, not model work.
                    # A live recipient supervisor acknowledges it immediately; the
                    # acknowledgement event is then available to the sender's
                    # supervisor without asking either model to run ingress.
                    receipt = self.rendezvous.tickle_ack(self.actor, event["payload"]["tickle_id"])
                    state["jobs"][event["event_id"]] = {"state": "acknowledged", "receipt": receipt["receipt"]["event_id"]}
                    acknowledged.append(event["event_id"])
                else:
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
        if event["kind"] == "coop2.tickle.sent":
            return self.rendezvous.tickle_ack(self.actor, payload["tickle_id"])
        if event["kind"] == "coop2.interaction.requested":
            return self.rendezvous.observe(self.actor, payload["interaction_id"])
        return {"publication": "not-required", "event_id": event_id}


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
    result.add_argument("--interval-seconds", type=float, default=5.0)
    result.add_argument("--once", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    rendezvous = Rendezvous(args.project, args.ledger)
    adapter_command = parse_command(args.adapter_command)
    adapter = CommandAdapter(adapter_command) if adapter_command else CLIResumeAdapter(args.host, args.session_ref)
    supervisor = Supervisor(rendezvous, args.actor, args.host, args.session_ref, args.generation,
                            adapter, args.state or default_state(rendezvous.project, args.actor))
    while True:
        if not control_is_current(args.control, args.generation):
            return 0
        output = supervisor.step()
        if args.once or output["delivered"] or output["deferred"] or output["unavailable"]:
            print(json.dumps(output, sort_keys=True), flush=True)
        if args.once:
            return 0 if not output["unavailable"] else 2
        if not control_is_current(args.control, args.generation):
            return 0
        time.sleep(max(args.interval_seconds, 0.1))


if __name__ == "__main__":
    raise SystemExit(main())
