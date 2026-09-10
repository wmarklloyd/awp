"""Compatibility wrapper for the generic AWP SessionStart activation hook.

Codex provides the durable session identifier in the hook payload.  Reusing it
as the queue thread and deriving a stable per-session actor keeps the watcher
addressable without relying on an undocumented environment variable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coordination import CoordinationError, find_project
else:
    from .awp_coordination import CoordinationError, find_project
from tools.awp_agent_start import run_hook as run_generic_hook


HOOK_EVENT = "SessionStart"
ROLE_ACTOR = "actor:codex"


def actor_for_session(session_id: str) -> str:
    """Return an opaque actor identifier stable for one Codex session."""
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
    return f"actor:codex-session:{digest}"


def bootstrap_command(project: Path, session_id: str) -> list[str]:
    return [
        sys.executable,
        str(project / "tools" / "awp_session.py"),
        "enter",
        "--project",
        str(project),
        "--actor",
        ROLE_ACTOR,
        "--thread",
        session_id,
    ]


def hook_result(message: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": message,
        }
    }


def run_hook(
    payload: dict[str, Any],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Start or attach through the generic activation path."""
    if runner is subprocess.run:
        return run_generic_hook(payload, host="codex", actor=ROLE_ACTOR)
    if payload.get("hook_event_name") != HOOK_EVENT:
        return hook_result("AWP doorbell bootstrap skipped: unexpected hook event.")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    if not isinstance(session_id, str) or not session_id or not isinstance(cwd, str) or not cwd:
        return hook_result("AWP doorbell bootstrap skipped: Codex did not provide session identity and cwd.")
    try:
        project = find_project(Path(cwd))
    except CoordinationError:
        return hook_result("AWP doorbell bootstrap skipped: this session is outside an AWP project.")
    try:
        completed = runner(
            bootstrap_command(project, session_id),
            cwd=project,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return hook_result(f"AWP doorbell bootstrap unavailable: {error}")
    if completed.returncode == 0:
        return hook_result(
            f"AWP doorbell bootstrap active for {ROLE_ACTOR}; session binding is {actor_for_session(session_id)}."
        )
    detail = (completed.stderr or completed.stdout or "bootstrap command failed").strip()
    return hook_result(f"AWP doorbell bootstrap unavailable: {detail[:500]}")


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
        print(json.dumps(hook_result(f"AWP doorbell bootstrap skipped: invalid hook input ({error}).")))
        return 0
    if not isinstance(payload, dict):
        print(json.dumps(hook_result("AWP doorbell bootstrap skipped: hook input is not an object.")))
        return 0
    print(json.dumps(run_hook(payload), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
