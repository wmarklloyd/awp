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

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coordination import CoordinationError, find_project
    from tools.awp_request_spool import RequestSpool
else:
    from .awp_coordination import CoordinationError, find_project
    from .awp_request_spool import RequestSpool

PROFILE = "awp-prompt-receipt-v1"
VIA = "host-prompt-hook"
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


def handle(payload: dict[str, Any], wait_seconds: float = 10.0) -> str | None:
    """Return developer context for the host, or None for an ordinary prompt."""
    keep_relay_running(payload)
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
    del argv
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        context = handle(payload)
    except Exception:  # a receipt must never break the user's prompt
        return 0
    if context:
        print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
