"""Atomic request/response spool for agents that cannot safely write SQLite."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable


PROFILE = "awp-request-spool-v1"


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True)
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


def safe_token(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:24]


class RequestSpool:
    def __init__(self, project: Path) -> None:
        self.root = project.resolve() / ".awp-runtime"
        self.requests = self.root / "requests"
        self.responses = self.root / "responses"

    def submit(self, client_id: str, operation_id: str, request: dict[str, Any]) -> Path:
        if not client_id or not operation_id:
            raise ValueError("client_id and operation_id are required")
        path = self.requests / safe_token(client_id) / f"{safe_token(operation_id)}.request"
        value = {"profile": PROFILE, "client_id": client_id, "operation_id": operation_id, "request": request}
        if path.exists():
            prior = json.loads(path.read_text(encoding="utf-8"))
            if prior != value:
                raise ValueError("operation_id was reused with different content")
            return path
        _atomic_write(path, value)
        return path

    def response(self, client_id: str, operation_id: str) -> dict[str, Any] | None:
        path = self.responses / safe_token(client_id) / f"{safe_token(operation_id)}.response"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None

    def process(self, handler: Callable[[dict[str, Any]], dict[str, Any]], limit: int = 100,
                accept: Callable[[dict[str, Any]], bool] | None = None) -> list[Path]:
        processed = []
        for path in sorted(self.requests.glob("*/*.request"))[:limit]:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if accept is not None and not accept(envelope):
                continue
            client_id, operation_id = envelope["client_id"], envelope["operation_id"]
            response_path = self.responses / safe_token(client_id) / f"{safe_token(operation_id)}.response"
            if not response_path.exists():
                try:
                    result = handler(envelope["request"])
                except Exception as error:
                    result = {"state": "refused", "reason": str(error)[:500]}
                _atomic_write(response_path, {"profile": PROFILE, "client_id": client_id,
                                              "operation_id": operation_id, "result": result})
            processed.append(path)
        return processed
