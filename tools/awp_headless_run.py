"""Run one W2 headless agent wake and record a ``host-launch`` receipt.

The relay writes a run specification (binding, recipient, event identifiers,
and the resolved command whose input is the doorbell notice) under
``.awp-runtime/headless/`` and starts this wrapper detached, so the relay never
blocks on an agent run.  The wrapper runs the command hidden, keeps its output
in a local log, and, when the run exits successfully, submits a ``host-launch``
receipt for each event through the request spool.  That is the W2 equivalent
of a host prompt hook: the host runner started a session whose first input was
the notice (Cooperation Contracts section 12).  A run that fails records
nothing; the relay's acknowledgement window then escalates.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_request_spool import RequestSpool
    from tools.awp_runtime import hidden_process_options
else:
    from .awp_request_spool import RequestSpool
    from .awp_runtime import hidden_process_options


PROFILE = "awp-headless-run-v1"
SESSION_PATTERNS = (
    re.compile(r'"session_id"\s*:\s*"([A-Za-z0-9_-]{6,100})"'),
    re.compile(r'"thread_id"\s*:\s*"([A-Za-z0-9_-]{6,100})"'),
    re.compile(r"session id:\s*([A-Za-z0-9_-]{6,100})", re.IGNORECASE),
)


def session_identifier(output: str) -> str | None:
    for pattern in SESSION_PATTERNS:
        match = pattern.search(output)
        if match:
            return match.group(1)
    return None


def run(project: Path, spec: dict[str, Any], timeout_seconds: float = 900.0,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    started = time.monotonic()
    try:
        # AWP_HEADLESS_RUN tells the agent's own startup hook not to register
        # this run as a live session (it would hijack the live binding).
        completed = runner(list(spec["command"]), cwd=project, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds, check=False,
                           env={**os.environ, "AWP_HEADLESS_RUN": str(spec.get("run_id", "1"))},
                           **hidden_process_options())
        code, output, error = completed.returncode, completed.stdout or "", completed.stderr or ""
    except subprocess.TimeoutExpired as expired:
        code, output, error = None, str(expired.stdout or ""), "timed out"
    except OSError as failure:
        code, output, error = None, "", str(failure)
    duration = round(time.monotonic() - started, 1)
    result: dict[str, Any] = {"profile": PROFILE, "run_id": spec.get("run_id"), "binding_id": spec.get("binding_id"),
                              "actor": spec.get("actor"), "events": spec.get("events", []), "exit_code": code,
                              "duration_seconds": duration, "receipts": []}
    log = project / ".awp-runtime" / "headless" / f"{str(spec.get('run_id', 'run:unknown')).split(':')[-1]}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"exit={code} duration={duration}s\n--- stdout ---\n{output[-20000:]}\n--- stderr ---\n{error[-5000:]}\n",
                   encoding="utf-8")
    if code != 0:
        result["state"] = "failed"
        return result
    evidence = {"run_id": spec.get("run_id"), "binding_id": spec.get("binding_id"), "exit_code": 0,
                "duration_seconds": duration}
    session = session_identifier(output)
    if session:
        evidence["session_id"] = session
    spool = RequestSpool(project)
    for event_id in spec.get("events", []):
        operation = f"host-launch:{spec['actor']}:{event_id}"
        try:
            spool.submit(spec["actor"], operation, {"actor": spec["actor"], "event_id": event_id,
                                                    "via": "host-launch", "evidence": evidence})
            result["receipts"].append(operation)
        except ValueError:
            pass  # already submitted for this event; the first receipt stands
    result["state"] = "receipt-submitted"
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    args = parser.parse_args(argv)
    project = args.project.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    result = run(project, spec, args.timeout_seconds)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "receipt-submitted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
