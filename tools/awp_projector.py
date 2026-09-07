"""Transport-neutral deterministic projector for the AWP Coordination 0.5 draft.

The projector consumes Coordination event envelopes and returns a deterministic
materialized view.  It is deliberately independent of the SQLite ledger: a
file, broker, database, or host binding can supply the same event sequence.
This is a deterministic Coordination projector foundation, not a complete
COOP-1 binding, authority source, semantic analyzer, or COOP-3 enforcer.
"""

from __future__ import annotations

import argparse
import heapq
import json
import re
from pathlib import Path
from typing import Iterable, Sequence

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CORE_SCHEMA = ROOT / "schemas" / "awp-core-0.7.schema.json"
COORDINATION_SCHEMA = ROOT / "schemas" / "awp-coordination-0.4.schema.json"


TRANSITIONS: dict[str, dict[tuple[str, str], str]] = {
    "semantic_definition": {
        ("active", "semantic_definition.updated"): "active",
        ("active", "semantic_definition.superseded"): "superseded",
    },
    "scope": {
        ("active", "scope.updated"): "active",
        ("active", "scope.retired"): "retired",
    },
    "intent": {
        ("proposed", "intent.activated"): "active",
        ("active", "intent.waiting"): "waiting",
        ("waiting", "intent.resumed"): "active",
        ("active", "intent.completed"): "completed",
        ("waiting", "intent.completed"): "completed",
        ("proposed", "intent.withdrawn"): "withdrawn",
        ("active", "intent.withdrawn"): "withdrawn",
        ("waiting", "intent.withdrawn"): "withdrawn",
        ("active", "intent.abandoned"): "abandoned",
        ("waiting", "intent.abandoned"): "abandoned",
        ("proposed", "intent.reassigned"): "proposed",
        ("active", "intent.reassigned"): "active",
        ("waiting", "intent.reassigned"): "waiting",
    },
    "overlap": {
        ("open", "overlap.acknowledged"): "open",
        ("open", "overlap.negotiation_started"): "negotiating",
        ("open", "overlap.dispositioned"): "resolved",
        ("negotiating", "overlap.dispositioned"): "resolved",
        ("escalated", "overlap.dispositioned"): "resolved",
        ("open", "overlap.escalated"): "escalated",
        ("negotiating", "overlap.escalated"): "escalated",
        ("resolved", "overlap.reopened"): "open",
    },
    "negotiation": {
        ("open", "negotiation.proposal_revised"): "open",
        ("open", "negotiation.accepted"): "accepted",
        ("open", "negotiation.rejected"): "rejected",
        ("open", "negotiation.timed_out"): "timed_out",
        ("open", "negotiation.cancelled"): "cancelled",
        ("open", "negotiation.escalated"): "escalated",
    },
    "commitment": {
        ("conditional", "commitment.activated"): "active",
        ("active", "commitment.satisfied"): "satisfied",
        ("active", "commitment.violated"): "violated",
        ("conditional", "commitment.cancelled"): "cancelled",
        ("active", "commitment.cancelled"): "cancelled",
        ("conditional", "commitment.released"): "released",
        ("active", "commitment.released"): "released",
        ("conditional", "commitment.superseded"): "superseded",
        ("active", "commitment.superseded"): "superseded",
    },
    "arbitration": {
        ("awaiting_user", "arbitration.updated"): "awaiting_user",
        ("awaiting_user", "arbitration.decided"): "decided",
        ("awaiting_user", "arbitration.declined"): "declined",
        ("awaiting_user", "arbitration.expired"): "expired",
        ("awaiting_user", "arbitration.cancelled"): "cancelled",
    },
    "contract": {
        ("proposed", "contract.negotiation_started"): "negotiating",
        ("proposed", "contract.accepted"): "accepted",
        ("negotiating", "contract.accepted"): "accepted",
        ("accepted", "contract.implementation_reported"): "implemented",
        ("implemented", "contract.verified"): "verified",
        ("proposed", "contract.rejected"): "rejected",
        ("negotiating", "contract.rejected"): "rejected",
        ("proposed", "contract.withdrawn"): "withdrawn",
        ("negotiating", "contract.withdrawn"): "withdrawn",
        ("accepted", "contract.revised"): "accepted",
        ("implemented", "contract.revised"): "implemented",
    },
    "change_set": {
        ("proposed", "changeset.work_started"): "in_progress",
        ("in_progress", "changeset.ready"): "ready",
        ("stale", "changeset.revalidated"): "in_progress",
        ("stale", "changeset.rebased"): "in_progress",
        ("ready", "changeset.integration_started"): "integrating",
        ("integrating", "changeset.integrated"): "integrated",
        ("integrating", "changeset.failed"): "failed",
        ("proposed", "changeset.withdrawn"): "withdrawn",
        ("in_progress", "changeset.withdrawn"): "withdrawn",
        ("ready", "changeset.withdrawn"): "withdrawn",
        ("stale", "changeset.withdrawn"): "withdrawn",
    },
    "integration_plan": {
        ("proposed", "integration.approved"): "approved",
        ("approved", "integration.started"): "integrating",
        ("integrating", "integration.completed"): "completed",
        ("integrating", "integration.failed"): "failed",
        ("proposed", "integration.cancelled"): "cancelled",
        ("approved", "integration.cancelled"): "cancelled",
    },
    "observed_scope": {
        ("final", "observed_scope.superseded"): "superseded",
    },
    "precondition": {
        ("active", "precondition.retired"): "retired",
        ("active", "precondition.superseded"): "superseded",
    },
    "precondition_result": {
        ("final", "precondition_result.superseded"): "superseded",
    },
    "verification_result": {
        ("final", "verification.superseded"): "superseded",
    },
    "presence": {
        ("active", "presence.scope_updated"): "active",
        ("active", "presence.released"): "released",
        ("active", "presence.expired"): "expired",
        ("active", "presence.superseded"): "superseded",
    },
}


CREATION_KINDS = {
    "semantic_definition": "semantic_definition.created",
    "scope": "scope.created",
    "intent": "intent.announced",
    "observed_scope": "observed_scope.published",
    "overlap": "overlap.detected",
    "negotiation": "negotiation.opened",
    "arbitration": "arbitration.requested",
    "commitment": "commitment.created",
    "contract": "contract.proposed",
    "precondition": "precondition.created",
    "precondition_result": "precondition.evaluated",
    "change_set": "changeset.proposed",
    "verification_result": "verification.completed",
    "dependency": "dependency.created",
    "integration_plan": "integration.proposed",
    "integration_result": "integration.completed",
    "presence": "presence.entered",
    "lease": "lease.requested",
}


class DeterministicProjector:
    """Project a Coordination event set independently of transport ordering."""

    def __init__(self) -> None:
        checker = FormatChecker()
        self._core = Draft202012Validator(
            json.loads(CORE_SCHEMA.read_text(encoding="utf-8")), format_checker=checker
        )
        self._coordination = Draft202012Validator(
            json.loads(COORDINATION_SCHEMA.read_text(encoding="utf-8")), format_checker=checker
        )

    @staticmethod
    def _diagnostic(
        code: str,
        event_id: str | None,
        message: str,
        *,
        record_id: str | None = None,
        severity: str = "error",
    ) -> dict:
        return {
            "code": code,
            "severity": severity,
            "event_id": event_id,
            "record_id": record_id,
            "message": message,
        }

    @staticmethod
    def _error_text(errors: Iterable) -> str:
        return "; ".join(error.message for error in sorted(errors, key=lambda item: list(item.path)))

    @staticmethod
    def _canonical(value: dict) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _event_record(event: dict) -> tuple[str | None, dict | None]:
        payload = event.get("payload")
        if not isinstance(payload, dict):
            return None, None
        record_id = payload.get("record_id")
        replacement = payload.get("replacement")
        return record_id if isinstance(record_id, str) else None, replacement if isinstance(replacement, dict) else None

    def _validate_events(
        self, events: Sequence[dict], workstate_id: str | None
    ) -> tuple[dict[str, dict], list[dict], list[dict]]:
        by_id: dict[str, dict] = {}
        diagnostics: list[dict] = []
        history: list[dict] = []
        for event in events:
            event_id = event.get("event_id") if isinstance(event, dict) else None
            if not isinstance(event, dict):
                diagnostics.append(self._diagnostic("AWP-COORD-INVALID-EVENT", None, "event is not an object"))
                continue
            if not isinstance(event_id, str):
                diagnostics.append(self._diagnostic("AWP-COORD-INVALID-EVENT", None, "event_id is missing"))
                continue
            history.append(event)
            previous = by_id.get(event_id)
            if previous is not None:
                chosen = min((previous, event), key=self._canonical)
                by_id[event_id] = chosen
                diagnostics.append(self._diagnostic("AWP-COORD-DUPLICATE-EVENT", event_id, "duplicate event identity; canonical bytes selected"))
                continue
            by_id[event_id] = event
            core_errors = list(self._core.iter_errors(event))
            coordination_errors = list(self._coordination.iter_errors(event))
            if core_errors or coordination_errors:
                errors = core_errors or coordination_errors
                diagnostics.append(self._diagnostic("AWP-COORD-INVALID-EVENT", event_id, self._error_text(errors)))
                by_id.pop(event_id)
                continue
            if workstate_id is not None and event["workstate_id"] != workstate_id:
                diagnostics.append(self._diagnostic("AWP-COORD-WORKSTATE-MISMATCH", event_id, "event workstate_id differs from requested projection"))
                by_id.pop(event_id)
                continue
            record_id, replacement = self._event_record(event)
            if replacement is not None:
                replacement_errors = list(self._coordination.iter_errors(replacement))
                if replacement_errors:
                    diagnostics.append(self._diagnostic("AWP-COORD-INVALID-REPLACEMENT", event_id, self._error_text(replacement_errors), record_id=record_id))
                    by_id.pop(event_id)
        history.sort(key=lambda event: (event.get("event_id", ""), self._canonical(event)))
        return by_id, diagnostics, history

    def _topological_order(self, events: dict[str, dict], diagnostics: list[dict]) -> list[dict]:
        children: dict[str, list[str]] = {event_id: [] for event_id in events}
        indegree: dict[str, int] = {}
        for event_id, event in events.items():
            parents = event["parents"]
            unknown = [parent for parent in parents if parent not in events]
            if unknown:
                diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", event_id, f"unknown event parent(s): {', '.join(sorted(unknown))}"))
                indegree[event_id] = -1
                continue
            indegree[event_id] = len(parents)
            for parent in parents:
                children[parent].append(event_id)
        ready = [event_id for event_id, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        ordered: list[dict] = []
        while ready:
            event_id = heapq.heappop(ready)
            ordered.append(events[event_id])
            for child in sorted(children[event_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    heapq.heappush(ready, child)
        for event_id, degree in indegree.items():
            if degree > 0:
                diagnostics.append(self._diagnostic("AWP-COORD-DEPENDENCY-CYCLE", event_id, "event ancestry contains a cycle"))
        return ordered

    @staticmethod
    def _reference_values(record: dict) -> list[tuple[str, str]]:
        fields = {
            "scope": ("semantic_targets",),
            "intent": ("declared_scopes", "expected_effects", "preserves"),
            "observed_scope": ("subject", "observed"),
            "overlap": ("subjects",),
            "conflict": ("subjects",),
            "negotiation": ("subject",),
            "arbitration": ("subjects", "blocked_scopes"),
            "precondition": ("subject",),
            "precondition_result": ("precondition",),
            "change_set": ("intent", "declared_scopes", "preconditions", "observed_scope", "verification"),
            "verification_result": ("subjects",),
            "dependency": ("source", "target"),
            "integration_plan": ("change_sets", "order", "verification"),
            "integration_result": ("plan",),
            "lease": ("scope",),
            "presence": ("declared_scopes",),
        }.get(record.get("type"), ())
        values: list[tuple[str, str]] = []
        for field in fields:
            value = record.get(field)
            if isinstance(value, str):
                values.append((field, value))
            elif isinstance(value, list):
                values.extend((field, item) for item in value if isinstance(item, str))
        return values

    def _validate_cross_record_references(
        self, records: dict[str, dict], diagnostics: list[dict]
    ) -> None:
        pinned = re.compile(r"^(\S+)@([1-9][0-9]*)$")
        for record_id in sorted(records):
            record = records[record_id]
            if record.get("condition", {}).get("type") == "contested":
                diagnostics.append(self._diagnostic("AWP-COORD-RECORD-CONTESTED", None, "cross-record validation cannot safely resolve references from a contested record", record_id=record_id))
                continue
            for field, value in self._reference_values(record):
                match = pinned.fullmatch(value)
                if not match:
                    diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", None, f"{field} is not a pinned record reference: {value}", record_id=record_id))
                    continue
                target_id, revision_text = match.groups()
                target = records.get(target_id)
                if target is None:
                    diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", None, f"{field} references unavailable record {value}", record_id=record_id))
                elif target.get("revision") != int(revision_text):
                    diagnostics.append(self._diagnostic("AWP-COORD-STALE", None, f"{field} references stale {value}; the projected record is revision {target.get('revision')}", record_id=record_id))

    def _validate_bindings(self, records: dict[str, dict], diagnostics: list[dict]) -> None:
        for record_id in sorted(records):
            record = records[record_id]
            record_type = record.get("type")
            if record_type == "precondition_result":
                precondition_ref = record.get("precondition")
                if isinstance(precondition_ref, str):
                    target_id = precondition_ref.rsplit("@", 1)[0]
                    target = records.get(target_id)
                    if target is not None and target.get("type") != "precondition":
                        diagnostics.append(self._diagnostic("AWP-COORD-VERIFICATION-UNBOUND", None, f"precondition result points to {target.get('type')} rather than a precondition", record_id=record_id))
                for dependency in record.get("depends_on", []):
                    if not isinstance(dependency, dict) or not isinstance(dependency.get("id"), str) or not isinstance(dependency.get("revision"), int):
                        diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", None, "precondition result depends_on entry lacks an id and integer revision", record_id=record_id))
                        continue
                    target = records.get(dependency["id"])
                    if target is None:
                        diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", None, f"precondition dependency is unavailable: {dependency['id']}@{dependency['revision']}", record_id=record_id))
                    elif target.get("revision") != dependency["revision"]:
                        diagnostics.append(self._diagnostic("AWP-COORD-STALE", None, f"precondition dependency is stale: {dependency['id']}@{dependency['revision']}", record_id=record_id))
            elif record_type == "verification_result":
                for subject in record.get("subjects", []):
                    if not isinstance(subject, str) or "@" not in subject:
                        continue
                    target = records.get(subject.rsplit("@", 1)[0])
                    if target is None:
                        continue
                    expected = None
                    if isinstance(target.get("base"), dict):
                        expected = target["base"].get("revision")
                    if expected is None and isinstance(target.get("selector"), dict):
                        expected = target["selector"].get("base_revision")
                    if expected is not None and record.get("base_revision") != expected:
                        diagnostics.append(self._diagnostic("AWP-COORD-VERIFICATION-UNBOUND", None, f"verification base {record.get('base_revision')} does not match subject base {expected}", record_id=record_id))
            elif record_type == "change_set":
                for field, expected_type in (("preconditions", "precondition"), ("verification", "verification_result")):
                    for reference in record.get(field, []):
                        if not isinstance(reference, str) or "@" not in reference:
                            continue
                        target = records.get(reference.rsplit("@", 1)[0])
                        if target is not None and target.get("type") != expected_type:
                            diagnostics.append(self._diagnostic("AWP-COORD-MISSING-DEPENDENCY", None, f"{field} points to {target.get('type')} rather than {expected_type}", record_id=record_id))

    @staticmethod
    def _heads(events: dict[str, dict]) -> list[str]:
        referenced = {parent for event in events.values() for parent in event["parents"]}
        return sorted(event_id for event_id in events if event_id not in referenced)

    def project(self, events: Sequence[dict], workstate_id: str | None = None) -> dict:
        by_id, diagnostics, history = self._validate_events(events, workstate_id)
        ordered = self._topological_order(by_id, diagnostics)
        records: dict[str, dict] = {}
        versions: dict[str, list[dict]] = {}
        heads: dict[str, set[str]] = {}
        contested: dict[str, set[str]] = {}
        event_ancestors: dict[str, set[str]] = {}

        for event in ordered:
            event_id = event["event_id"]
            event_ancestors[event_id] = set(event["parents"])
            for parent in event["parents"]:
                event_ancestors[event_id].update(event_ancestors.get(parent, set()))
            record_id, replacement = self._event_record(event)
            if replacement is None:
                continue
            if record_id != replacement.get("id"):
                diagnostics.append(self._diagnostic("AWP-COORD-INVALID-EVENT", event_id, "payload record_id does not match replacement.id", record_id=record_id))
                continue
            record_id = str(record_id)
            prior_revision = event["payload"].get("prior_revision")
            revision = event["payload"].get("revision", replacement.get("revision"))
            if replacement.get("revision") != revision or not isinstance(revision, int):
                diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, "event and replacement revisions do not agree", record_id=record_id))
                continue
            if prior_revision is None:
                expected_creation_kind = CREATION_KINDS.get(replacement.get("type"))
                if revision != 1 or record_id in versions:
                    diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, "creation must begin at revision 1 and cannot replace an existing record", record_id=record_id))
                    continue
                if expected_creation_kind and event["kind"] != expected_creation_kind:
                    diagnostics.append(self._diagnostic("AWP-COORD-INVALID-TRANSITION", event_id, f"{event['kind']} cannot create a {replacement.get('type')} record", record_id=record_id))
                    continue
                versions[record_id] = [{"event_id": event_id, "revision": 1, "record": replacement}]
                heads[record_id] = {event_id}
                records[record_id] = dict(replacement)
                continue
            if not isinstance(prior_revision, int) or revision != prior_revision + 1:
                diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, "revision must advance exactly one from prior_revision", record_id=record_id))
                continue
            candidates = [version for version in versions.get(record_id, []) if version["revision"] == prior_revision]
            if not candidates:
                diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, f"prior revision {prior_revision} is not effective", record_id=record_id))
                continue
            if event["kind"].endswith(".reconciled"):
                resolved = set(event["payload"].get("resolves_events", []))
                known = contested.get(record_id, set())
                if not known or not known.issubset(resolved):
                    diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, "reconciliation does not resolve every known competing successor", record_id=record_id))
                    continue
                contested.pop(record_id, None)
                versions.setdefault(record_id, []).append({"event_id": event_id, "revision": revision, "record": replacement})
                heads[record_id] = {event_id}
                records[record_id] = dict(replacement)
                continue
            if record_id in contested:
                diagnostics.append(self._diagnostic("AWP-COORD-RECORD-CONTESTED", event_id, "record has unresolved competing successors", record_id=record_id))
                continue
            if len(candidates) != 1:
                diagnostics.append(self._diagnostic("AWP-COORD-REVISION-CONFLICT", event_id, "multiple effective bases exist for prior revision", record_id=record_id))
                continue
            current = candidates[0]["record"]
            transition = event["payload"].get("transition")
            expected = TRANSITIONS.get(current.get("type"), {}).get((current.get("status"), event["kind"]))
            if expected is None or not isinstance(transition, dict) or transition.get("from") != current.get("status") or transition.get("to") != replacement.get("status") or expected != replacement.get("status"):
                diagnostics.append(self._diagnostic("AWP-COORD-INVALID-TRANSITION", event_id, f"{event['kind']} is not valid from {current.get('status')!r}", record_id=record_id))
                continue
            base = candidates[0]
            if base["event_id"] not in heads.get(record_id, set()) or base["event_id"] not in event_ancestors[event_id]:
                contested[record_id] = set(heads.get(record_id, set())) | {event_id}
                contested_record = dict(base["record"])
                contested_record["condition"] = {"type": "contested", "events": sorted(contested[record_id])}
                records[record_id] = contested_record
                diagnostics.append(self._diagnostic("AWP-COORD-RECORD-CONTESTED", event_id, "concurrent non-commuting successors preserved as contested", record_id=record_id))
                continue
            versions[record_id].append({"event_id": event_id, "revision": revision, "record": replacement})
            heads[record_id] = {event_id}
            records[record_id] = dict(replacement)

        self._validate_cross_record_references(records, diagnostics)
        self._validate_bindings(records, diagnostics)
        diagnostics.sort(key=lambda item: (item.get("event_id") or "", item["code"], item.get("record_id") or ""))
        return {
            "capability_profile": "deterministic-coordination-projector-v1",
            "workstate_id": workstate_id or (ordered[0]["workstate_id"] if ordered else None),
            "frontier": self._heads(by_id),
            "records": {record_id: records[record_id] for record_id in sorted(records)},
            "contested": {record_id: sorted(event_ids) for record_id, event_ids in sorted(contested.items())},
            "diagnostics": diagnostics,
            "history": history,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workstate-id")
    args = parser.parse_args()
    events = [json.loads(line) for line in __import__("sys").stdin if line.strip()]
    print(json.dumps(DeterministicProjector().project(events, args.workstate_id), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
