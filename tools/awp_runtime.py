"""Small host-neutral helpers shared by AWP runtime processes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


def hidden_process_options() -> dict[str, Any]:
    """Keep child processes of background AWP processes off the user's desktop.

    On Windows a console program (git, codex, python) started by a process that
    has no console of its own gets a new, visible console window. Background
    supervisors and watchers run without a console, so every such child must be
    started hidden. Elsewhere this returns no options.
    """
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0), "startupinfo": startupinfo}


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def control_is_current(path: Path | None, generation: str | None) -> bool:
    """Return false after a newer activation generation supersedes this process."""
    if path is None and generation is None:
        return True
    if path is None or not generation:
        return False
    try:
        control = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return control.get("generation") == generation and control.get("desired_state") == "running"
