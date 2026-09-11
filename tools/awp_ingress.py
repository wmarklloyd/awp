"""Recipient-side automatic reconciliation for one AWP delivery event."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Sequence

from .awp_request_spool import RequestSpool


def handle(project: Path, actor: str, event_id: str, timeout_seconds: float = 30.0) -> dict:
    spool = RequestSpool(project)
    operation_id = f"ingress:{actor}:{event_id}"
    spool.submit(actor, operation_id, {"actor": actor, "event_id": event_id})
    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    while time.monotonic() <= deadline:
        response = spool.response(actor, operation_id)
        if response is not None:
            return {"profile": "awp-agent-ingress-v1", "actor": actor,
                    "source_event": event_id, "state": "accepted", "result": response["result"]}
        time.sleep(0.1)
    # Do not report a timeout if the supervisor completed the response at the
    # deadline boundary between the final poll and this return.
    response = spool.response(actor, operation_id)
    if response is not None:
        return {"profile": "awp-agent-ingress-v1", "actor": actor,
                "source_event": event_id, "state": "accepted", "result": response["result"]}
    return {"profile": "awp-agent-ingress-v1", "actor": actor,
            "source_event": event_id, "state": "deferred", "reason": "supervisor response timeout"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--actor", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args(argv)
    result = handle(args.project.resolve(), args.actor, args.event, args.timeout_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
