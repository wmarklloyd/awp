"""Enter an AWP project and make its host-neutral doorbell operational.

The bootstrap discovers the project-local COOP-2 rendezvous, declares the
current host session as a W1 wake binding, attaches to or starts the clone's
single relay (``tools/awp_relay.py``), waits for an observed heartbeat, and
then runs the ordinary AWP re-entry check.  It reports success
only when the watcher is actually live; durable entry-only recovery remains
available through ``awp_reentry.py``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_runtime import atomic_json, hidden_process_options
    from tools.awp_supervisor import PROFILE as WATCHER_PROFILE
    from tools.awp_activation import CLIResumeAdapter, CommandAdapter, parse_command
    from tools.awp_coop2 import Rendezvous
    from tools.awp_coordination import CoordinationError
    from tools import awp_relay, awp_wake
else:
    from .awp_runtime import atomic_json, hidden_process_options
    from .awp_supervisor import PROFILE as WATCHER_PROFILE
    from .awp_activation import CLIResumeAdapter, CommandAdapter, parse_command
    from .awp_coop2 import Rendezvous
    from .awp_coordination import CoordinationError
    from . import awp_relay, awp_wake


PROFILE = "awp-agent-session-bootstrap-v1"
DEFAULT_LEDGER = Path(".awp-runtime/coop2-rendezvous.sqlite3")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def thread_id(explicit: str | None, environment: dict[str, str] | None = None) -> str | None:
    values = environment if environment is not None else os.environ
    return explicit or values.get("CODEX_THREAD_ID") or values.get("CODEX_SESSION_ID")


def actor_token(actor: str) -> str:
    """Return a filesystem-safe, non-revealing component for one actor."""
    return hashlib.sha256(actor.encode("utf-8")).hexdigest()[:16]


def control_path(project: Path, actor: str = "actor:codex") -> Path:
    return project / ".awp-runtime" / f"awp-session-{actor_token(actor)}.json"


def watcher_state_path(project: Path, actor: str = "actor:codex") -> Path:
    return project / ".awp-runtime" / f"awp-supervisor-{actor_token(actor)}.json"


def _windows_process_is_running(pid: int) -> bool:
    """Check process liveness without signalling it.

    Unlike POSIX, ``os.kill(pid, 0)`` on Windows is not a harmless existence
    probe: Python maps it to a process termination request with exit code zero.
    The session bootstrap must never use it for the watcher it just started.
    """
    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    still_active = 259
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def process_is_running(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        return _windows_process_is_running(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def watcher_command(
    project: Path,
    ledger: Path,
    actor: str,
    thread: str,
    generation: str,
    interval_seconds: float,
    remote: str | None,
    host: str = "codex",
    adapter_command: str | None = None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "tools.awp_supervisor",
        "--project",
        str(project),
        "--ledger",
        str(ledger),
        "--actor",
        actor,
        "--host",
        host,
        "--session-ref",
        thread,
        "--state",
        str(watcher_state_path(project, actor)),
        "--control",
        str(control_path(project, actor)),
        "--generation",
        generation,
        "--interval-seconds",
        str(interval_seconds),
    ]
    if adapter_command:
        command.extend(["--adapter-command", adapter_command])
    return command


def _watcher_row(rendezvous: Rendezvous, actor: str) -> dict[str, Any]:
    return next(
        (item for item in rendezvous.participant_watchers() if item.get("actor") == actor),
        {"actor": actor, "watcher_liveness": "none"},
    )


def _stop_legacy_supervisor(project: Path, actor: str) -> None:
    """Retire a per-actor supervisor started by older code; the relay replaces it."""
    path = control_path(project, actor)
    prior = read_json(path)
    if prior.get("desired_state") == "running" and prior.get("profile") == PROFILE and "relay_generation" not in prior:
        prior.update({"desired_state": "stopped", "generation": uuid.uuid4().hex, "state": "superseded-by-relay",
                      "stopped_at": utc_now()})
        atomic_json(path, prior)


def start_watcher(
    project: Path,
    ledger: Path,
    actor: str,
    thread: str,
    *,
    remote: str | None = None,
    interval_seconds: float = 5.0,
    startup_timeout_seconds: float = 12.0,
    host: str = "codex",
    adapter_command: str | None = None,
) -> dict[str, Any]:
    """Bind this session as a W1 wake binding and make sure the clone's relay runs.

    The relay (``tools/awp_relay.py``) serves every declared binding in the
    clone, for every agent, so there is one watcher process however many
    agents are active.  Success is reported only after the relay's heartbeat
    for this actor has been observed.
    """
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    rendezvous = Rendezvous(project, ledger)
    command = parse_command(adapter_command)
    adapter = CommandAdapter(command) if command else CLIResumeAdapter(host, thread)
    probe = adapter.probe()
    if probe["state"] != "accepted":
        return {
            "profile": PROFILE,
            "state": "unavailable",
            "diagnostic": "AWP-HOST-ACTIVATION-UNAVAILABLE",
            "reason": probe.get("reason", "host endpoint did not accept the startup probe"),
            "probe": probe,
        }
    # Register the safe fallback before attempting a live claim.  A later join
    # promotes the same actor only after a fresh heartbeat has been observed.
    rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    started_at = utc_now()
    declared = awp_relay.declare_live_session(rendezvous, actor, host, thread, command)
    binding = (declared or {}).get("binding", {})
    _stop_legacy_supervisor(project, actor)
    relay = awp_relay.ensure(project, interval_seconds, startup_timeout_seconds)
    control = {
        "profile": PROFILE, "actor": actor, "host": host, "thread": thread, "remote": remote,
        "ledger": str(ledger), "started_at": started_at, "desired_state": "running",
        "binding_id": binding.get("binding_id"), "binding_event": binding.get("event_id"),
        "relay_generation": (relay.get("status") or {}).get("generation"), "relay_state": relay["state"],
    }
    watcher = {"actor": actor, "watcher_liveness": "none"}
    if relay["state"] in {"attached", "started"} and binding:
        deadline = time.monotonic() + max(startup_timeout_seconds, 0.1)
        while time.monotonic() < deadline:
            watcher = _watcher_row(rendezvous, actor)
            if watcher.get("watcher_liveness") == "active" and watcher.get("last_seen", "") >= started_at[:19]:
                rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "watcher")
                control.update({"state": "active", "heartbeat_observed_at": watcher.get("last_seen")})
                atomic_json(control_path(project, actor), control)
                return {"profile": PROFILE, "state": "attached" if relay["state"] == "attached" else "active",
                        "control": control, "watcher": watcher, "relay": relay["state"]}
            time.sleep(min(interval_seconds, 0.25))
    control.update({"state": "unavailable", "failed_at": utc_now()})
    atomic_json(control_path(project, actor), control)
    rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    return {
        "profile": PROFILE,
        "state": "unavailable",
        "diagnostic": "AWP-SIGNAL-UNVERIFIED" if binding else "AWP-NO-LIVE-SESSION-BINDING",
        "control": control,
        "watcher": watcher,
        "relay": relay,
        "logs": {"stdout": str(project / ".awp-runtime" / "awp-relay.out.log"),
                 "stderr": str(project / ".awp-runtime" / "awp-relay.err.log")},
    }


def stop_watcher(project: Path, ledger: Path, actor: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    """Stop waking this actor's open session: retire its W1 binding.

    The relay keeps serving other bindings; ``python -m tools.awp_relay stop``
    stops the relay itself.
    """
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    rendezvous = Rendezvous(project, ledger)
    retired = []
    for binding in awp_wake.active_bindings(rendezvous._events()).values():
        if binding["actor"] == actor and binding["class"] == "W1":
            awp_wake.retire(rendezvous, actor, binding["binding_id"], "session stopped")
            retired.append(binding["binding_id"])
    _stop_legacy_supervisor(project, actor)
    path = control_path(project, actor)
    control = read_json(path)
    control.update({"profile": PROFILE, "desired_state": "stopped", "state": "stopped", "stopped_at": utc_now(),
                    "retired_bindings": retired})
    atomic_json(path, control)
    rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    return {"profile": PROFILE, "state": "stopped", "control": control}


def session_status(project: Path, ledger: Path, actor: str) -> dict[str, Any]:
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    control = read_json(control_path(project, actor))
    rendezvous = Rendezvous(project, ledger)
    watcher = _watcher_row(rendezvous, actor)
    relay = awp_relay.relay_status(project)
    running = bool(relay.get("live")) or process_is_running(control.get("pid"))
    live = running and watcher.get("watcher_liveness") == "active"
    return {
        "profile": PROFILE,
        "state": "active" if live else "unavailable",
        "diagnostic": None if live else "AWP-SIGNAL-UNVERIFIED",
        "process_running": running,
        "relay": {key: relay.get(key) for key in ("live", "age_seconds")},
        "control": control,
        "watcher": watcher,
    }


def coordination_unavailable(error: Exception) -> dict[str, Any]:
    """Return the fail-closed result used when the ledger cannot be opened."""
    return {
        "profile": PROFILE,
        "state": "unavailable",
        "diagnostic": "AWP-COORD-LEDGER-UNAVAILABLE",
        "reason": str(error),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("command", choices=["enter", "start", "status", "stop"])
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    result.add_argument("--actor", default="actor:codex")
    result.add_argument("--thread")
    result.add_argument("--remote")
    result.add_argument("--host", default="codex")
    result.add_argument("--adapter-command", help="JSON string array or shell words for a trusted host adapter")
    result.add_argument("--interval-seconds", type=float, default=5.0)
    result.add_argument("--startup-timeout-seconds", type=float, default=12.0)
    result.add_argument("--max-output-bytes", type=int, default=24_000)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    project = args.project.resolve()
    try:
        if args.command == "status":
            result = session_status(project, args.ledger, args.actor)
        elif args.command == "stop":
            result = stop_watcher(project, args.ledger, args.actor)
        else:
            selected_thread = thread_id(args.thread)
            if not selected_thread:
                result = {
                    "profile": PROFILE,
                    "state": "unavailable",
                    "diagnostic": "AWP-CODEX-THREAD-REQUIRED",
                    "reason": "supply --thread or start from a host that exposes CODEX_THREAD_ID",
                }
            else:
                result = start_watcher(
                    project,
                    args.ledger,
                    args.actor,
                    selected_thread,
                    remote=args.remote,
                    interval_seconds=args.interval_seconds,
                    startup_timeout_seconds=args.startup_timeout_seconds,
                    host=args.host,
                    adapter_command=args.adapter_command,
                )
    except CoordinationError as error:
        result = coordination_unavailable(error)
    if args.command in {"enter", "start"}:
        if args.command == "enter":
            observation = "watcher" if result.get("state") in {"active", "attached"} else "on-entry-only"
            command = [
                sys.executable,
                str(project / "tools" / "awp_reentry.py"),
                "--project",
                str(project),
                "--actor",
                args.actor,
                "--register-observation",
                observation,
                "--host",
                args.host,
                "--max-output-bytes",
                str(args.max_output_bytes),
            ]
            reentry = subprocess.run(command, cwd=project, capture_output=True, text=True, check=False,
                                     **hidden_process_options())
            try:
                entry = json.loads(reentry.stdout)
            except json.JSONDecodeError:
                entry = {"state": "unavailable", "reason": reentry.stderr.strip() or "invalid re-entry output"}
            result = {"profile": PROFILE, "doorbell": result, "reentry": entry}
    print(json.dumps(result, indent=2, sort_keys=True))
    doorbell = result.get("doorbell", result)
    return 0 if doorbell.get("state") in {"active", "attached", "stopped"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
