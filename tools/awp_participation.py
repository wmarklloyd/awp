"""Small model-facing participation adapter for the local advisory ledger.

This is an experimental read/announce slice. It accepts the proposed
participation requests, keeps Core event construction in the host adapter, and
delegates durable publication and request idempotency to CoordinationLedger.
It does not authenticate actors, authorize project mutations, or claim full C1.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .awp_coordination import CoordinationError, CoordinationLedger, normalize_scope


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "awp-participation-0.1.schema.json"


class ParticipationError(RuntimeError):
    """Raised when a participation request cannot be prepared or published."""


class ParticipationAdapter:
    """Implement the model-facing read and announce operations."""

    def __init__(
        self,
        ledger: CoordinationLedger,
        *,
        workstate_id: str,
        project_id: str,
        actor: str,
        base_revision: str = "git:unknown",
        project_root: Path | None = None,
        authority_ceiling: tuple[str, ...] = ("read_only", "local_write"),
    ) -> None:
        self.ledger = ledger
        self.workstate_id = workstate_id
        self.project_id = project_id
        self.actor = actor
        self.base_revision = base_revision
        self.project_root = project_root.resolve() if project_root else None
        self.authority_ceiling = list(authority_ceiling)
        self._validator = Draft202012Validator(
            json.loads(SCHEMA.read_text(encoding="utf-8")),
            format_checker=FormatChecker(),
        )

    @staticmethod
    def _request_id(request: dict[str, Any]) -> str:
        return request.get("request_id") or f"request:{uuid.uuid4()}"

    @staticmethod
    def _request_hash(request: dict[str, Any]) -> str:
        canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _validate(self, request: dict[str, Any], operation: str) -> None:
        errors = sorted(self._validator.iter_errors(request), key=lambda item: list(item.path))
        if errors or request.get("operation") != operation:
            message = "; ".join(error.message for error in errors) or f"operation must be {operation}"
            raise ParticipationError(message)
        requested_project = request.get("project")
        if requested_project and requested_project != self.project_id:
            raise ParticipationError("request project does not match the adapter project")

    def _coverage(self) -> dict[str, Any]:
        return {
            "scope_complete": True,
            "history": "complete",
            "semantic_analysis": "reported_only",
        }

    def _base_response(self, request_id: str, refresh: dict[str, Any]) -> dict[str, Any]:
        overlaps = refresh["open_overlaps"]
        coordination = "blocked" if refresh["advisory_status"] == "block" else (
            "warning" if overlaps else "clear"
        )
        diagnostics = [
            {
                "code": "AWP-COORD-OVERLAP",
                "severity": "policy" if item["policy_action"] == "block" else "warning",
                "message": f"Open overlap requires review: {item['id']}",
                "recovery": "Use interact to record an order, disposition, or arbitration request.",
            }
            for item in overlaps
        ]
        return {
            "request_id": request_id,
            "project": self.project_id,
            "publication": "not_applicable",
            "coordination": coordination,
            "authority_ceiling": self.authority_ceiling,
            "frontier": refresh["frontier"],
            "coverage": self._coverage(),
            "diagnostics": diagnostics,
            "interactions": [
                {"handle": item["id"], "summary": f"Open {item['policy_action']} overlap"}
                for item in overlaps
            ],
        }

    def read(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = self._request_id(request)
        try:
            self._validate(request, "read")
            refresh = self.ledger.refresh(self.workstate_id)
            response = self._base_response(request_id, refresh)
            context_material = {
                "project": self.project_id,
                "workstate_id": self.workstate_id,
                "frontier": refresh["frontier"],
                "goal": request.get("goal"),
                "requested_scope": request.get("requested_scope"),
            }
            response["context"] = "ctx:" + hashlib.sha256(
                json.dumps(context_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:20]
            response["briefing"] = {
                "active_intents": refresh["active_intents"],
                "open_overlaps": refresh["open_overlaps"],
                "mode": refresh["mode"],
                "workstate_id": self.workstate_id,
            }
            response["next"] = {
                "operation": "announce",
                "reason": "Declare the files and facts this task will change or rely on.",
            }
            return response
        except (ParticipationError, CoordinationError) as error:
            return self._rejected(request_id, str(error))

    def announce(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = self._request_id(request)
        try:
            self._validate(request, "announce")
            scopes = request["scope"]
            accesses = {item["access"] for item in scopes}
            if len(accesses) != 1:
                raise ParticipationError("the local ledger slice requires one access mode for all scopes")
            normalized: list[tuple[str, str]] = []
            for item in scopes:
                raw_path = item["path"]
                if self.project_root:
                    normalized.append(normalize_scope(self.project_root, raw_path))
                else:
                    kind = item.get("selector") or ("directory" if raw_path.endswith(("/", "\\")) else "file")
                    normalized.append((kind, raw_path.replace("\\", "/")))
            result = self.ledger.begin(
                workstate_id=self.workstate_id,
                project_id=request.get("project", self.project_id),
                actor=self.actor,
                goal=request.get("goal", "goal:unspecified"),
                summary=request["summary"],
                base_revision=request.get("base_revision", self.base_revision),
                scopes=normalized,
                access=next(iter(accesses)),
                policy=request.get("policy", "warn"),
                request_id=request_id,
                request_hash=self._request_hash(request),
            )
            overlaps = result["overlaps"]
            blocked = result["advisory_status"] == "block"
            response = {
                "request_id": request_id,
                "project": self.project_id,
                "publication": "confirmed",
                "coordination": "blocked" if blocked else ("warning" if overlaps else "clear"),
                "authority_ceiling": self.authority_ceiling,
                "frontier": result["frontier"],
                "coverage": self._coverage(),
                "diagnostics": [
                    {
                        "code": "AWP-COORD-OVERLAP",
                        "severity": "policy" if blocked else "warning",
                        "message": "The announced intent overlaps an active coordination scope.",
                        "recovery": "Use interact to record an order, disposition, or arbitration request.",
                    }
                    for _ in overlaps
                ],
                "intent": result["intent"]["id"],
                "receipt": f"receipt:{request_id}",
                "interactions": [
                    {"handle": overlap["id"], "summary": "Overlapping active intent"}
                    for overlap in overlaps
                ],
                "publication_receipt": {
                    "receipt_id": f"receipt:{request_id}",
                    "request_id": request_id,
                    "status": "confirmed",
                    "event_ids": result["event_ids"],
                    "frontier": result["frontier"],
                    "binding": {
                        "profile": result["profile"],
                        "operational_mode": "ledger_bound",
                        "reach": "shared",
                        "confirmation": "event IDs and frontier returned by local ledger",
                    },
                },
            }
            response["next"] = {
                "operation": "interact" if overlaps else "publish",
                "reason": "Resolve the reported overlap before guarded work." if overlaps else "Report actual changes and evidence when work is complete.",
            }
            return response
        except (ParticipationError, CoordinationError) as error:
            return self._rejected(request_id, str(error))

    def _rejected(self, request_id: str, message: str) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "project": self.project_id,
            "publication": "rejected",
            "coordination": "unverifiable",
            "authority_ceiling": self.authority_ceiling,
            "frontier": self.ledger.refresh(self.workstate_id)["frontier"],
            "coverage": {"scope_complete": False, "history": "unknown", "semantic_analysis": "unknown"},
            "diagnostics": [{"code": "AWP-PARTICIPATION-INVALID-REQUEST", "severity": "error", "message": message}],
            "next": {"operation": "read", "reason": "Correct the request and obtain a fresh context."},
        }
