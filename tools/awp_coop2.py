"""Experimental project-scoped COOP-2 rendezvous over the local AWP ledger.

This is a bounded managed-collaboration pilot, not a COOP-2 conformance claim.
It gives sessions sharing one project a stable place to join, discover peers,
send a typed interaction, and receive a durable reply without exchanging paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .awp_coordination import CoordinationError, CoordinationLedger, discover_workstate, find_project, stable_project_id


PROFILE = "local-coop2-rendezvous-v1"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Rendezvous:
    def __init__(self, project: Path, ledger_path: Path | None = None) -> None:
        self.project = find_project(project)
        self.workstate_id, _ = discover_workstate(self.project)
        self.project_id = stable_project_id(self.project)
        self.ledger = CoordinationLedger(ledger_path or self.project / ".awp-runtime" / "coop2-rendezvous.sqlite3")

    def _events(self) -> list[dict]:
        return self.ledger.export_events(self.workstate_id)

    def _append(self, actor: str, kind: str, payload: dict) -> dict:
        with self.ledger._transaction() as connection:
            event, _ = self.ledger._append(connection, workstate_id=self.workstate_id, actor=actor, kind=kind, payload=payload, occurred_at=now())
            return {"event_id": event["event_id"], "frontier": self.ledger._frontier(connection, self.workstate_id)}

    def status(self) -> dict:
        return {"profile": PROFILE, "project_id": self.project_id, "workstate_id": self.workstate_id, "binding_id": self.ledger.binding_id(), "reach": "shared-if-same-ledger", "limitations": ["experimental pilot", "no semantic analyzer", "no authentication", "budget declaration is recorded but not host-enforced"]}

    def join(self, actor: str, capabilities: list[str]) -> dict:
        for event in reversed(self._events()):
            if event["kind"] == "coop2.participant.joined" and event["payload"]["actor"] == actor:
                return {"participant": actor, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": event["event_id"]}, "binding": self.status()}
        receipt = self._append(actor, "coop2.participant.joined", {"actor": actor, "project_id": self.project_id, "workstate_id": self.workstate_id, "binding_id": self.ledger.binding_id(), "capabilities": sorted(set(capabilities)), "availability": "available"})
        return {"participant": actor, "publication": "confirmed", "deduplicated": False, "receipt": receipt, "binding": self.status()}

    def peers(self, actor: str | None = None) -> dict:
        latest: dict[str, dict] = {}
        for event in self._events():
            if event["kind"] == "coop2.participant.joined":
                payload = event["payload"]
                latest[payload["actor"]] = {"actor": payload["actor"], "capabilities": payload["capabilities"], "availability": payload["availability"], "event_id": event["event_id"]}
        if actor:
            latest.pop(actor, None)
        return {"binding": self.status(), "participants": sorted(latest.values(), key=lambda item: item["actor"])}

    def send(self, actor: str, recipient: str, purpose: str, subject: str, question: str, decision_owner: str, max_rounds: int, max_tool_calls: int, max_tokens: int) -> dict:
        if recipient not in {item["actor"] for item in self.peers()["participants"]}:
            raise CoordinationError("recipient is not registered in this project rendezvous")
        interaction_id = "interaction:" + hashlib.sha256(canonical([self.project_id, self.workstate_id, actor, recipient, purpose, subject, question]).encode()).hexdigest()[:24]
        for event in self._events():
            if event["kind"] == "coop2.interaction.requested" and event["payload"]["interaction_id"] == interaction_id:
                return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": event["event_id"]}}
        payload = {"interaction_id": interaction_id, "sender": actor, "recipient": recipient, "purpose": purpose, "subject": subject, "question": question, "decision_owner": decision_owner, "authorization": {"participants": sorted([actor, recipient]), "max_rounds": max_rounds, "max_tool_calls": max_tool_calls, "max_total_output_tokens": max_tokens}, "status": "open"}
        return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": False, "receipt": self._append(actor, "coop2.interaction.requested", payload)}

    def inbox(self, actor: str) -> dict:
        answered = {event["payload"]["interaction_id"] for event in self._events() if event["kind"] == "coop2.interaction.responded"}
        requests = [event["payload"] | {"event_id": event["event_id"]} for event in self._events() if event["kind"] == "coop2.interaction.requested" and event["payload"]["recipient"] == actor and event["payload"]["interaction_id"] not in answered]
        responses = [event["payload"] | {"event_id": event["event_id"]} for event in self._events() if event["kind"] == "coop2.interaction.responded" and event["payload"]["recipient"] == actor]
        return {"binding": self.status(), "inbox": requests, "responses": responses}

    def respond(self, actor: str, interaction_id: str, outcome: str, response: str) -> dict:
        request = next((event["payload"] for event in self._events() if event["kind"] == "coop2.interaction.requested" and event["payload"]["interaction_id"] == interaction_id), None)
        if request is None:
            raise CoordinationError("unknown interaction")
        if request["recipient"] != actor:
            raise CoordinationError("only the named recipient may respond")
        if any(event["kind"] == "coop2.interaction.responded" and event["payload"]["interaction_id"] == interaction_id for event in self._events()):
            raise CoordinationError("interaction already has a response")
        return {"interaction_id": interaction_id, "publication": "confirmed", "receipt": self._append(actor, "coop2.interaction.responded", {"interaction_id": interaction_id, "sender": actor, "recipient": request["sender"], "outcome": outcome, "response": response, "status": "closed"})}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    join = commands.add_parser("join"); join.add_argument("--actor", required=True); join.add_argument("--capability", action="append", default=[])
    peers = commands.add_parser("peers"); peers.add_argument("--actor")
    send = commands.add_parser("send"); send.add_argument("--actor", required=True); send.add_argument("--to", required=True); send.add_argument("--purpose", choices=["review", "critique", "alternative", "delegation", "decision", "synthesis"], required=True); send.add_argument("--subject", required=True); send.add_argument("--question", required=True); send.add_argument("--decision-owner", required=True); send.add_argument("--max-rounds", type=int, default=1); send.add_argument("--max-tool-calls", type=int, default=4); send.add_argument("--max-tokens", type=int, default=1200)
    inbox = commands.add_parser("inbox"); inbox.add_argument("--actor", required=True)
    respond = commands.add_parser("respond"); respond.add_argument("--actor", required=True); respond.add_argument("--interaction", required=True); respond.add_argument("--outcome", choices=["accepted", "revised", "inconclusive", "declined", "timed_out", "escalated"], required=True); respond.add_argument("--response", required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        rendezvous = Rendezvous(args.project, args.ledger)
        if args.command == "status": result = rendezvous.status()
        elif args.command == "join": result = rendezvous.join(args.actor, args.capability)
        elif args.command == "peers": result = rendezvous.peers(args.actor)
        elif args.command == "send": result = rendezvous.send(args.actor, args.to, args.purpose, args.subject, args.question, args.decision_owner, args.max_rounds, args.max_tool_calls, args.max_tokens)
        elif args.command == "inbox": result = rendezvous.inbox(args.actor)
        else: result = rendezvous.respond(args.actor, args.interaction, args.outcome, args.response)
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    except (CoordinationError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
