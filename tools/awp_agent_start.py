"""Generic SessionStart shim that activates any AWP host binding."""

from __future__ import annotations

import argparse
import os
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coordination import CoordinationError, find_project
    from tools.awp_runtime import hidden_process_options
else:
    from .awp_coordination import CoordinationError, find_project
    from .awp_runtime import hidden_process_options


PROFILE = "awp-agent-start-v1"
HOOK_EVENT = "SessionStart"


def opaque_session_ref(host: str, session_id: str) -> str:
    digest = hashlib.sha256(f"{host}\0{session_id}".encode()).hexdigest()[:24]
    return f"session:{host}:{digest}"


def bootstrap_command(project: Path, host: str, actor: str, session_id: str,
                      adapter_command: str | None = None) -> list[str]:
    command = [sys.executable, str(project / "tools" / "awp_session.py"), "enter",
               "--project", str(project), "--host", host, "--actor", actor,
               "--thread", session_id]
    if adapter_command:
        command.extend(["--adapter-command", adapter_command])
    return command


def hook_result(message: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": HOOK_EVENT, "additionalContext": message}}


def run_hook(payload: dict[str, Any], *, host: str, actor: str | None = None,
             adapter_command: str | None = None,
             runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    if payload.get("hook_event_name") != HOOK_EVENT:
        return hook_result("AWP activation skipped: unexpected hook event.")
    session_id, cwd = payload.get("session_id"), payload.get("cwd")
    if not isinstance(session_id, str) or not session_id or not isinstance(cwd, str) or not cwd:
        return hook_result("AWP activation unavailable: host did not provide session identity and cwd.")
    try:
        project = find_project(Path(cwd))
    except CoordinationError:
        return hook_result("AWP activation skipped: this session is outside an AWP project.")
    role_actor = actor or f"actor:{host}"
    try:
        completed = runner(bootstrap_command(project, host, role_actor, session_id, adapter_command),
                           cwd=project, capture_output=True, text=True, timeout=25, check=False,
                           **hidden_process_options())
    except (OSError, subprocess.TimeoutExpired) as error:
        return hook_result(f"AWP-HOST-ACTIVATION-UNAVAILABLE: {error}")
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "activation failed").strip()
        return hook_result(f"AWP-HOST-ACTIVATION-UNAVAILABLE: {detail[:500]}")
    return hook_result(
        f"AWP activation active for {role_actor}; route session is {opaque_session_ref(host, session_id)}. "
        "Git signals are hints; durable ledger recovery remains authoritative."
    )


def _log_invocation(project_hint: str | None, record: dict[str, Any]) -> None:
    """Leave evidence that the shim ran at all, even when it skips.

    A hook that a host silently skips and a hook that runs but bails out look
    identical from outside unless the shim records every invocation.
    """
    try:
        project = find_project(Path(project_hint or Path.cwd()))
    except (CoordinationError, OSError):
        return
    try:
        from datetime import datetime, timezone
        line = json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}, sort_keys=True)
        runtime = project / ".awp-runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        with (runtime / "agent-start.log").open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    except OSError:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--actor")
    parser.add_argument("--adapter-command")
    parser.add_argument("--session-ref", help="direct activation session identifier; otherwise read hook JSON")
    parser.add_argument("--project", type=Path, help="project path for direct activation")
    args = parser.parse_args(argv)
    if args.session_ref:
        payload = {"hook_event_name": HOOK_EVENT, "session_id": args.session_ref,
                   "cwd": str((args.project or Path.cwd()).resolve())}
    else:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
            _log_invocation(None, {"host": args.host, "outcome": "invalid-hook-input", "detail": str(error)[:200]})
            print(json.dumps(hook_result(f"AWP activation skipped: invalid hook input ({error}).")))
            return 0
    if os.environ.get("AWP_HEADLESS_RUN"):
        # A run the relay started (W2) is not a live session: registering it
        # would point the agent's live-session binding at a run about to end.
        _log_invocation(payload.get("cwd") if isinstance(payload, dict) else None,
                        {"host": args.host, "actor": args.actor, "outcome": "skipped: relay-started headless run"})
        print(json.dumps(hook_result("AWP activation skipped: this is a headless run started by the AWP relay.")))
        return 0
    result = run_hook(payload, host=args.host, actor=args.actor, adapter_command=args.adapter_command)
    _log_invocation(payload.get("cwd") if isinstance(payload, dict) else None, {
        "host": args.host, "actor": args.actor, "source": payload.get("source") if isinstance(payload, dict) else None,
        "session_id": payload.get("session_id") if isinstance(payload, dict) else None,
        "outcome": result["hookSpecificOutput"]["additionalContext"][:300],
    })
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
