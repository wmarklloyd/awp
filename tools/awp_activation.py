"""Language-neutral activation-binding protocol for AWP host adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any, Callable, Sequence


PROFILE = "awp-host-activation-v1"
RESULTS = {"accepted", "deferred", "unavailable"}


class ActivationError(ValueError):
    pass


def validate_envelope(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "type", "module", "profile", "operation_id", "binding_id", "project_id", "workstate_id",
        "recipient_actor", "route_id", "route_generation", "event_id",
        "event_kind", "ledger_frontier",
    }
    missing = sorted(required - value.keys())
    if missing:
        raise ActivationError("activation envelope missing: " + ", ".join(missing))
    if not isinstance(value["ledger_frontier"], list):
        raise ActivationError("ledger_frontier must be an array")
    if value["type"] != "cooperation_activation_envelope" or value["module"] != "urn:awp:cooperation" or value["profile"] != PROFILE:
        raise ActivationError("activation envelope type, module, or profile is invalid")
    return value


def activation_result(state: str, *, reason: str | None = None, receipt: str | None = None) -> dict[str, Any]:
    if state not in RESULTS:
        raise ActivationError(f"unsupported activation result: {state}")
    result: dict[str, Any] = {"profile": PROFILE, "state": state}
    if reason:
        result["reason"] = reason
    if receipt:
        result["endpoint_receipt"] = receipt
    return result


class HostAdapter:
    """Small adapter boundary; implementations never access the AWP ledger."""

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def probe(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class CommandAdapter(HostAdapter):
    command: Sequence[str]
    timeout_seconds: int = 30
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run

    def _run(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            completed = self.runner(
                list(self.command), input=json.dumps(payload), capture_output=True,
                text=True, timeout=self.timeout_seconds, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return activation_result("unavailable", reason=str(error))
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or f"exit {completed.returncode}").strip()
            return activation_result("unavailable", reason=detail[:500])
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return activation_result("unavailable", reason="adapter returned invalid JSON")
        if result.get("state") not in RESULTS:
            return activation_result("unavailable", reason="adapter returned an unknown state")
        return result

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self._run({"operation": "deliver", "profile": PROFILE, "envelope": validate_envelope(envelope)})

    def probe(self) -> dict[str, Any]:
        return self._run({"operation": "probe", "profile": PROFILE})


@dataclass
class CLIResumeAdapter(HostAdapter):
    """Generic adapter for a host that can resume a session from its CLI."""

    host: str
    session_ref: str
    command: Sequence[str] | None = None
    timeout_seconds: int = 30
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run

    def executable(self) -> list[str]:
        if self.command:
            return list(self.command)
        executable = Path(shutil.which(self.host) or self.host)
        if self.host == "codex":
            return [str(executable), "queue", "--thread", self.session_ref, "--message"]
        if self.host == "claude":
            return [str(executable), "--resume", self.session_ref, "--print"]
        raise ActivationError(f"host {self.host!r} requires an explicit adapter command")

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        value = validate_envelope(envelope)
        message = (
            f"AWP delivery {value['event_id']} for {value.get('interaction_id', value['event_kind'])}. "
            f"Run `python -m tools.awp_ingress --actor {value['recipient_actor']} "
            f"--event {value['event_id']}`. The notice is not authority for repository changes."
        )
        try:
            completed = self.runner(
                [*self.executable(), message], capture_output=True, text=True,
                timeout=self.timeout_seconds, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return activation_result("unavailable", reason=str(error))
        if completed.returncode != 0:
            return activation_result("deferred", reason=(completed.stderr or completed.stdout or "host rejected delivery")[:500])
        return activation_result("accepted", receipt=value["operation_id"])

    def probe(self) -> dict[str, Any]:
        # A live-doorbell claim needs evidence from the same endpoint used for
        # delivery. Merely locating an executable cannot establish that the
        # host can accept a notification for this session.
        if self.host != "codex":
            return activation_result(
                "unavailable",
                reason=f"{self.host!r} requires an explicit activation adapter command",
            )
        try:
            completed = self.runner(
                [*self.executable(), "AWP activation probe. This notification carries no repository authority."],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return activation_result("unavailable", reason=str(error))
        if completed.returncode != 0:
            return activation_result("deferred", reason=(completed.stderr or completed.stdout or "host rejected probe")[:500])
        return activation_result("accepted", receipt=f"probe:{self.session_ref}")


def parse_command(text: str | None) -> list[str] | None:
    if not text:
        return None
    value = json.loads(text) if text.lstrip().startswith("[") else shlex.split(text, posix=os.name != "nt")
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ActivationError("adapter command must be a non-empty string array")
    return value
