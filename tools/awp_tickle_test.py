"""End-to-end reachability test: one tickle from any agent to any agent.

Publishes a tickle (ledger event plus Git signal ref), then waits and reports
each stage from the authoritative ledger:

  published      the sender's coop2.tickle.sent event
  transport      the relay's transport receipt for each wake attempt (actor:awp-relay)
  ladder         escalations and the recorded outcome, if the first rung did not answer
  acknowledged   the recipient's coop2.tickle.acked event and how it was produced

The test passes only when the recipient acknowledges within the TTL through its
own agent turn (``acknowledged_via`` is not a supervisor shortcut).  It is host
neutral: sender and recipient are just COOP-2 actors.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coop2 import Rendezvous
    from tools import awp_wake
else:
    from .awp_coop2 import Rendezvous
    from . import awp_wake


def _stages(rendezvous: Rendezvous, tickle_id: str) -> dict[str, Any]:
    stages: dict[str, Any] = {}
    for event in rendezvous._events():
        payload = event.get("payload", {})
        if payload.get("tickle_id") != tickle_id and payload.get("interaction_id") != tickle_id:
            continue
        entry = {"event_id": event["event_id"], "at": event.get("occurred_at"), "actor": event.get("actor")}
        if event["kind"] == "coop2.tickle.sent":
            stages["published"] = entry
        elif event["kind"].startswith("coop2.tickle.transport_"):
            stages["transport"] = entry | {"state": payload.get("transport_state"), "route_id": payload.get("route_id"),
                                           "wake_class": payload.get("wake_class"), "reason": payload.get("reason")}
            stages.setdefault("attempts", []).append(stages["transport"])
        elif event["kind"] in {"coop2.wake.escalated", "coop2.wake.outcome"}:
            stages.setdefault("ladder", []).append(entry | {"kind": event["kind"], "binding_id": payload.get("binding_id"),
                                                            "outcome": payload.get("outcome"), "reason": payload.get("reason")})
        elif event["kind"] == "coop2.tickle.acked":
            stages["acknowledged"] = entry | {"via": payload.get("acknowledged_via")}
    return stages


def run(project: Path, ledger: Path | None, sender: str, recipient: str, ttl: int, wait: float) -> dict[str, Any]:
    rendezvous = Rendezvous(project, ledger)
    if not ttl:
        ttl = awp_wake.suggested_ttl(rendezvous._events(), recipient)
        wait = wait or float(ttl)
    # Section 12: before sending, state which rung the recipient will get.
    reach = awp_wake.reach(rendezvous._events(), recipient)["participants"].get(recipient, {}).get("best")
    key = f"tickle-test-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    sent = rendezvous.tickle(sender, recipient, ttl_seconds=ttl, idempotency_key=key)
    tickle_id = sent["tickle_id"]
    deadline = time.monotonic() + wait
    stages: dict[str, Any] = {}
    while time.monotonic() < deadline:
        stages = _stages(rendezvous, tickle_id)
        if "acknowledged" in stages:
            break
        time.sleep(1.0)
    ack = stages.get("acknowledged")
    passed = bool(ack) and ack.get("via") not in {None, "supervisor"}
    return {"profile": "awp-tickle-test-v1", "tickle_id": tickle_id, "sender": sender, "recipient": recipient,
            "ttl_seconds": ttl, "git_signal": (sent.get("doorbell") or {}).get("git_ref", {}).get("state"),
            "expected_reach": reach, "stages": stages, "result": "pass" if passed else "fail"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--from", dest="sender", required=True)
    parser.add_argument("--to", dest="recipient", required=True)
    parser.add_argument("--ttl-seconds", type=int, help="default: long enough for the recipient's first wake rung")
    parser.add_argument("--wait-seconds", type=float, help="how long to wait (default: the TTL)")
    args = parser.parse_args(argv)
    result = run(args.project.resolve(), args.ledger, args.sender, args.recipient, args.ttl_seconds,
                 args.wait_seconds if args.wait_seconds is not None else float(args.ttl_seconds or 0))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
