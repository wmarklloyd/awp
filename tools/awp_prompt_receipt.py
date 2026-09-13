"""Host prompt hook: record that an AWP doorbell notice entered an agent's session.

Register this script on the host's "prompt submitted" hook (UserPromptSubmit in
Codex and Claude Code; any host with an equivalent hook can use it unchanged).
It reads the hook's JSON from stdin.  When the prompt is an ``[AWP doorbell]``
notice, it hands a receipt to the recipient's supervisor through the ingress
spool, recorded as ``acknowledged_via: host-prompt-hook`` with the host's
session and turn identifiers as evidence.  Every other prompt passes through
untouched.

Why a hook: a delivered notice proves nothing until the agent's session takes
it as input, and asking the model to run a command proved unreliable (the
model repeatedly replied that it had acknowledged without running anything).
The host hook fires exactly when the notice enters the session, so the receipt
no longer depends on model compliance.  The script never blocks or alters a
prompt and always exits 0.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
    from tools.awp_coordination import CoordinationError, find_project
    from tools.awp_request_spool import RequestSpool
else:
    from .awp_coordination import CoordinationError, find_project
    from .awp_request_spool import RequestSpool

PROFILE = "awp-prompt-receipt-v1"
VIA = "host-prompt-hook"
REGISTRATION_COOLDOWN_SECONDS = 60
NOTICE = re.compile(r"\[AWP doorbell\].*?--actor\s+(?P<actor>[^\s`]+)\s+--event\s+(?P<event>evt:[0-9A-Za-z-]+)", re.S)


def parse_notice(prompt: str) -> tuple[str, str] | None:
    match = NOTICE.search(prompt or "")
    return (match.group("actor"), match.group("event")) if match else None


def _log(project: Path, record: dict[str, Any]) -> None:
    try:
        runtime = project / ".awp-runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}, sort_keys=True)
        with (runtime / "prompt-receipt.log").open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    except OSError:
        pass


def _registration_state_path(project: Path, actor: str) -> Path:
    safe_actor = re.sub(r"[^A-Za-z0-9_.-]+", "_", actor)
    return project / ".awp-runtime" / f"prompt-registration-{safe_actor}.json"


def _read_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _write_state(path: Path, value: dict[str, Any]) -> None:
    try:
        if __package__ in {None, ""}:
            from tools.awp_runtime import atomic_json
        else:
            from .awp_runtime import atomic_json
        atomic_json(path, value)
    except OSError:
        pass


def _spawn_detached(command: list[str], project: Path) -> subprocess.Popen:
    """Launch a registration repair that outlives this hook process.

    Mirrors awp_relay._detached_popen: on Windows a host (Codex, for one) may
    run its hooks inside a job object that kills every child when the host
    process exits, so this asks to break away from the job and falls back
    only if the job forbids it.
    """
    windows = os.name == "nt"
    flags = 0
    if windows:
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200) | getattr(subprocess, "DETACHED_PROCESS", 0x8)
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0x8000000))
    runtime_dir = project / ".awp-runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    with (runtime_dir / "prompt-registration.out.log").open("ab") as output, \
         (runtime_dir / "prompt-registration.err.log").open("ab") as error:
        options = dict(cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL, stdout=output,
                       stderr=error, close_fds=True, start_new_session=not windows)
        if windows:
            try:
                return subprocess.Popen(command, creationflags=flags | 0x01000000, **options)
            except OSError:
                pass  # the job does not allow breakaway; the next prompt retries after the cooldown
        return subprocess.Popen(command, creationflags=flags, **options)


def ensure_session_registered(
    payload: dict[str, Any],
    *,
    host: str | None,
    actor: str | None,
    launcher: Callable[..., Any] | None = None,
) -> dict[str, Any] | None:
    """Repair this session's own W1 reachability if the host never registered it.

    ``keep_relay_running`` above only repairs the relay daemon's liveness; it
    says nothing about whether *this session* is reachable through it.  A host
    whose SessionStart hook fails to fire (documented for Codex -- the "type
    hello to wake it up" symptom) never registers a W1 binding at all, no
    matter how many prompts follow.  This closes that gap the same way: a
    cheap status check first, and only when unregistered does it launch the
    normal session-enter bootstrap, detached so the hook process can exit
    without killing it, and throttled per session_id so a burst of prompts
    does not spawn a burst of ``codex queue``/``claude --resume`` probes.
    """
    if not host or not actor or os.environ.get("AWP_HEADLESS_RUN"):
        return None
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    if not isinstance(session_id, str) or not session_id or not isinstance(cwd, str) or not cwd:
        return None
    try:
        project = find_project(Path(cwd))
    except (CoordinationError, OSError):
        return None
    try:
        if __package__ in {None, ""}:
            from tools.awp_session import session_status, DEFAULT_LEDGER
            from tools.awp_agent_start import bootstrap_command
        else:
            from .awp_session import session_status, DEFAULT_LEDGER
            from .awp_agent_start import bootstrap_command
        status = session_status(project, DEFAULT_LEDGER, actor)
    except Exception as error:
        _log(project, {"actor": actor, "outcome": "registration-status-check-failed", "detail": str(error)[:200]})
        return None
    if status.get("state") == "active":
        return None
    state_path = _registration_state_path(project, actor)
    state = _read_state(state_path)
    now = time.time()
    if state.get("session_id") == session_id and (now - state.get("attempted_epoch", -1e9)) < REGISTRATION_COOLDOWN_SECONDS:
        return None
    _write_state(state_path, {"session_id": session_id, "attempted_epoch": now,
                              "attempted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    command = bootstrap_command(project, host, actor, session_id)
    launcher = launcher or _spawn_detached
    try:
        launcher(command, project)
    except OSError as error:
        _log(project, {"actor": actor, "session_id": session_id, "outcome": "registration-repair-launch-failed",
                       "detail": str(error)[:200]})
        return None
    _log(project, {"actor": actor, "session_id": session_id, "outcome": "registration-repair-started"})
    return {"outcome": "registration-repair-started", "session_id": session_id}


def keep_relay_running(payload: dict[str, Any]) -> None:
    """Every prompt a local host processes repairs the doorbell if it is down.

    This needs no user action and costs two file reads when the relay is live.
    Headless runs the relay itself started are skipped.
    """
    import os

    if os.environ.get("AWP_HEADLESS_RUN"):
        return
    try:
        project = find_project(Path(payload.get("cwd") or Path.cwd()))
    except (CoordinationError, OSError):
        return
    try:
        if __package__ in {None, ""}:
            from tools.awp_relay import kick
        else:
            from .awp_relay import kick
        result = kick(project)
    except Exception as error:  # the prompt always goes through
        _log(project, {"outcome": "relay-kick-failed", "detail": str(error)[:200]})
        return
    if result.get("relay") != "live" or result.get("autostart"):
        _log(project, {"outcome": "relay-kick", **result})


def handle(
    payload: dict[str, Any],
    wait_seconds: float = 10.0,
    *,
    host: str | None = None,
    host_actor: str | None = None,
) -> str | None:
    """Return developer context for the host, or None for an ordinary prompt."""
    keep_relay_running(payload)
    ensure_session_registered(payload, host=host, actor=host_actor)
    parsed = parse_notice(str(payload.get("prompt") or ""))
    if parsed is None:
        return None
    actor, event_id = parsed
    try:
        project = find_project(Path(payload.get("cwd") or Path.cwd()))
    except (CoordinationError, OSError):
        return None
    evidence = {key: payload.get(key) for key in ("hook_event_name", "session_id", "turn_id") if payload.get(key)}
    spool = RequestSpool(project)
    operation_id = f"prompt-receipt:{actor}:{event_id}"
    try:
        spool.submit(actor, operation_id, {"actor": actor, "event_id": event_id, "via": VIA, "evidence": evidence})
    except (OSError, ValueError) as error:
        _log(project, {"actor": actor, "event_id": event_id, "outcome": "submit-failed", "detail": str(error)[:200]})
        return None
    deadline = time.monotonic() + max(wait_seconds, 0.0)
    response = spool.response(actor, operation_id)
    while response is None and time.monotonic() < deadline:
        time.sleep(0.1)
        response = spool.response(actor, operation_id)
    result = (response or {}).get("result") or {}
    state = "recorded" if response and result.get("state") != "refused" else (
        "refused" if response else "pending-supervisor")
    _log(project, {"actor": actor, "event_id": event_id, "outcome": state, "evidence": evidence,
                   "reason": result.get("reason")})
    if state == "recorded":
        return (f"AWP doorbell receipt for {event_id} was recorded automatically by the host hook. "
                "For a reachability probe no further action is needed. For a consultation, read your inbox "
                f"with `python -m tools.awp_coop2 inbox --actor {actor}` and handle it under its authorization.")
    return (f"AWP doorbell receipt for {event_id} is {state}"
            + (f" ({result.get('reason')})" if result.get("reason") else "")
            + ". Run the command in the notice to acknowledge it.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AWP host prompt-submit hook.")
    parser.add_argument("--host", default=None, help="Host identifier (e.g. codex, claude).")
    parser.add_argument("--actor", default=None, help="This session's own actor (e.g. actor:codex).")
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        context = handle(payload, host=args.host, host_actor=args.actor)
    except Exception:  # a receipt must never break the user's prompt
        return 0
    if context:
        print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
