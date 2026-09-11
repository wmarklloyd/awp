"""Enter an AWP project and make its host-neutral doorbell operational.

The bootstrap discovers the project-local COOP-2 rendezvous, binds the current
host session, starts or replaces a detached supervisor, waits for an observed
heartbeat, and then runs the ordinary AWP re-entry check.  It reports success
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
    from tools.awp_runtime import atomic_json
    from tools.awp_supervisor import PROFILE as WATCHER_PROFILE
    from tools.awp_activation import CLIResumeAdapter, CommandAdapter, parse_command
    from tools.awp_coop2 import Rendezvous
    from tools.awp_coordination import CoordinationError
else:
    from .awp_runtime import atomic_json
    from .awp_supervisor import PROFILE as WATCHER_PROFILE
    from .awp_activation import CLIResumeAdapter, CommandAdapter, parse_command
    from .awp_coop2 import Rendezvous
    from .awp_coordination import CoordinationError


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
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    rendezvous = Rendezvous(project, ledger)
    adapter = CommandAdapter(parse_command(adapter_command)) if adapter_command else CLIResumeAdapter(host, thread)
    probe = adapter.probe()
    if probe["state"] != "accepted":
        return {
            "profile": PROFILE,
            "state": "unavailable",
            "diagnostic": "AWP-HOST-ACTIVATION-UNAVAILABLE",
            "reason": probe.get("reason", "host endpoint did not accept the startup probe"),
            "probe": probe,
        }
    control_file = control_path(project, actor)
    prior = read_json(control_file)
    observed = _watcher_row(rendezvous, actor)
    if (
        prior.get("profile") == PROFILE
        and prior.get("desired_state") == "running"
        and prior.get("thread") == thread
        and prior.get("host") == host
        and process_is_running(prior.get("pid"))
        and observed.get("watcher_liveness") == "active"
    ):
        return {"profile": PROFILE, "state": "attached", "control": prior, "watcher": observed}

    # Register the safe fallback before attempting a live claim.  A later join
    # promotes the same actor only after a fresh heartbeat has been observed.
    rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    generation = uuid.uuid4().hex
    started_at = utc_now()
    control = {
        "profile": PROFILE,
        "generation": generation,
        "desired_state": "running",
        "state": "starting",
        "actor": actor,
        "host": host,
        "thread": thread,
        "remote": remote,
        "ledger": str(ledger),
        "started_at": started_at,
    }
    atomic_json(control_file, control)

    runtime = project / ".awp-runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    output_path = runtime / f"awp-supervisor-{actor_token(actor)}.out.log"
    error_path = runtime / f"awp-supervisor-{actor_token(actor)}.err.log"
    command = watcher_command(project, ledger, actor, thread, generation, interval_seconds, remote, host, adapter_command)
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        start_new_session = True
    with output_path.open("ab") as output, error_path.open("ab") as error:
        process = subprocess.Popen(
            command,
            cwd=project,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=error,
            close_fds=True,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
    control.update({"pid": process.pid, "state": "waiting_for_heartbeat"})
    atomic_json(control_file, control)

    deadline = time.monotonic() + max(startup_timeout_seconds, 0.1)
    watcher = {"actor": actor, "watcher_liveness": "none"}
    while time.monotonic() < deadline:
        if not process_is_running(process.pid):
            break
        watcher = _watcher_row(rendezvous, actor)
        if watcher.get("watcher_liveness") == "active" and watcher.get("last_seen", "") >= started_at:
            rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "watcher")
            control.update({"state": "active", "heartbeat_observed_at": watcher.get("last_seen")})
            atomic_json(control_file, control)
            return {"profile": PROFILE, "state": "active", "control": control, "watcher": watcher}
        time.sleep(min(interval_seconds, 0.25))

    control.update({"desired_state": "stopped", "state": "unavailable", "failed_at": utc_now()})
    atomic_json(control_file, control)
    rendezvous.join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    return {
        "profile": PROFILE,
        "state": "unavailable",
        "diagnostic": "AWP-SIGNAL-UNVERIFIED",
        "control": control,
        "watcher": watcher,
        "logs": {"stdout": str(output_path), "stderr": str(error_path)},
    }


def stop_watcher(project: Path, ledger: Path, actor: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    path = control_path(project, actor)
    control = read_json(path)
    pid = control.get("pid")
    control.update(
        {
            "profile": PROFILE,
            "generation": uuid.uuid4().hex,
            "desired_state": "stopped",
            "state": "stopping",
            "stopped_at": utc_now(),
        }
    )
    atomic_json(path, control)
    deadline = time.monotonic() + timeout_seconds
    while process_is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    control["state"] = "stopped" if not process_is_running(pid) else "stop_pending"
    atomic_json(path, control)
    Rendezvous(project, ledger).join(actor, ["managed-collaboration", "git-ref-doorbell"], "on-entry-only")
    return {"profile": PROFILE, "state": control["state"], "control": control}


def session_status(project: Path, ledger: Path, actor: str) -> dict[str, Any]:
    project = project.resolve()
    ledger = ledger if ledger.is_absolute() else (project / ledger)
    control = read_json(control_path(project, actor))
    watcher = _watcher_row(Rendezvous(project, ledger), actor)
    live = process_is_running(control.get("pid")) and watcher.get("watcher_liveness") == "active"
    return {
        "profile": PROFILE,
        "state": "active" if live else "unavailable",
        "diagnostic": None if live else "AWP-SIGNAL-UNVERIFIED",
        "process_running": process_is_running(control.get("pid")),
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
                "--max-output-bytes",
                str(args.max_output_bytes),
            ]
            reentry = subprocess.run(command, cwd=project, capture_output=True, text=True, check=False)
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
