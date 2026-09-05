from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from tools.awp_coordination import CoordinationLedger
from tools.awp_projector import DeterministicProjector


WORKSTATE = "workstate:test"


def intent_record(status: str, revision: int) -> dict:
    return {
        "id": "intent:test",
        "type": "intent",
        "module": "urn:awp:coordination",
        "revision": revision,
        "status": status,
        "created_by": "actor:test",
        "created_at": "2026-09-04T20:00:00Z",
        "goal": "goal:test",
        "summary": "Projector fixture",
        "base": {"repository": "repo:test", "revision": "git:base"},
        "declared_scopes": ["scope:test@1"],
    }


def scope_record() -> dict:
    return {
        "id": "scope:test",
        "type": "scope",
        "module": "urn:awp:coordination",
        "revision": 1,
        "status": "active",
        "created_by": "actor:test",
        "created_at": "2026-09-04T20:00:00Z",
        "selector": {"kind": "file", "repository": "repo:test", "base_revision": "git:base", "path": "src/app.py"},
        "access": "write",
    }


def event(event_id: str, parents: list[str], kind: str, record: dict, **payload: object) -> dict:
    body = {
        "record_id": record["id"],
        "revision": record["revision"],
        "replacement": record,
    }
    body.update(payload)
    return {
        "event_schema_version": "0.2",
        "module": "urn:awp:coordination",
        "kind": kind,
        "event_id": event_id,
        "workstate_id": WORKSTATE,
        "parents": parents,
        "occurred_at": "2026-09-04T20:00:00Z",
        "actor": "actor:test",
        "payload": body,
    }


class DeterministicProjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.projector = DeterministicProjector()
        self.scope_created = event("evt:scope", [], "scope.created", scope_record())
        self.created = event("evt:create", [], "intent.announced", intent_record("proposed", 1))

    def test_topological_projection_is_independent_of_transport_order(self) -> None:
        activated = intent_record("active", 2)
        activated_event = event(
            "evt:activate", ["evt:create"], "intent.activated", activated,
            prior_revision=1, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([activated_event, self.created, self.scope_created], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["status"], "active")
        self.assertEqual(result["diagnostics"], [])

    def test_concurrent_non_commuting_updates_are_contested_order_independently(self) -> None:
        activated = intent_record("active", 2)
        withdrawn = intent_record("withdrawn", 2)
        first = event(
            "evt:activate", ["evt:create"], "intent.activated", activated,
            prior_revision=1, transition={"from": "proposed", "to": "active"},
        )
        second = event(
            "evt:withdraw", ["evt:create"], "intent.withdrawn", withdrawn,
            prior_revision=1, transition={"from": "proposed", "to": "withdrawn"},
        )
        left = self.projector.project([self.created, first, second, self.scope_created], WORKSTATE)
        right = self.projector.project([second, self.created, first, self.scope_created], WORKSTATE)
        self.assertEqual(left["records"], right["records"])
        self.assertEqual(left["contested"], {"intent:test": ["evt:activate", "evt:withdraw"]})
        self.assertEqual(right["contested"], left["contested"])
        self.assertIn("AWP-COORD-RECORD-CONTESTED", {item["code"] for item in left["diagnostics"]})

    def test_invalid_transition_does_not_change_projection(self) -> None:
        completed = intent_record("completed", 2)
        invalid = event(
            "evt:complete", ["evt:create"], "intent.completed", completed,
            prior_revision=1, transition={"from": "proposed", "to": "completed"},
        )
        result = self.projector.project([self.created, invalid, self.scope_created], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["status"], "proposed")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-INVALID-TRANSITION")

    def test_creation_kind_must_match_record_type(self) -> None:
        invalid = event("evt:bad-create", [], "intent.completed", intent_record("proposed", 1))
        result = self.projector.project([invalid], WORKSTATE)
        self.assertEqual(result["records"], {})
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-INVALID-TRANSITION")

    def test_revision_conflict_is_diagnosed(self) -> None:
        activated = intent_record("active", 2)
        invalid = event(
            "evt:activate", ["evt:create"], "intent.activated", activated,
            prior_revision=4, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([self.created, invalid, self.scope_created], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["revision"], 1)
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-REVISION-CONFLICT")

    def test_missing_parent_is_not_applied(self) -> None:
        activated = intent_record("active", 2)
        missing = event(
            "evt:activate", ["evt:missing"], "intent.activated", activated,
            prior_revision=1, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([self.created, missing, self.scope_created], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["status"], "proposed")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-MISSING-DEPENDENCY")

    def test_missing_cross_record_reference_is_diagnosed(self) -> None:
        orphan = intent_record("proposed", 1)
        orphan["declared_scopes"] = ["scope:missing@1"]
        orphan_event = event("evt:orphan", [], "intent.announced", orphan)
        result = self.projector.project([orphan_event], WORKSTATE)
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-MISSING-DEPENDENCY")

    def test_verification_must_bind_to_subject_base_revision(self) -> None:
        verification = {
            "id": "verification:test",
            "type": "verification_result",
            "module": "urn:awp:coordination",
            "revision": 1,
            "status": "final",
            "created_by": "actor:test",
            "created_at": "2026-09-04T20:00:00Z",
            "subjects": ["intent:test@1"],
            "repository": "repo:test",
            "base_revision": "git:wrong",
            "result_revision": "git:result",
            "procedure": {"kind": "command", "command_id": "test:fixture", "tool": "fixture", "tool_version": "1"},
            "environment": {"platform": "test"},
            "outcome": "pass",
            "observations": {"passed": 1},
        }
        verification_event = event("evt:verification", [], "verification.completed", verification)
        result = self.projector.project([self.created, verification_event, self.scope_created], WORKSTATE)
        self.assertIn("AWP-COORD-VERIFICATION-UNBOUND", {item["code"] for item in result["diagnostics"]})

    def test_workstate_mismatch_is_not_applied(self) -> None:
        mismatched = self.created.copy()
        mismatched["event_id"] = "evt:other"
        mismatched["workstate_id"] = "workstate:other"
        result = self.projector.project([mismatched], WORKSTATE)
        self.assertEqual(result["records"], {})
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-WORKSTATE-MISMATCH")

    def test_projector_replays_events_from_the_local_ledger_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = CoordinationLedger(Path(directory) / "coordination.sqlite3")
            ledger.begin(
                workstate_id=WORKSTATE,
                project_id="repo:test",
                actor="actor:test",
                goal="goal:test",
                summary="Transport fixture",
                base_revision="git:base",
                scopes=[("file", "src/app.py")],
            )
            result = self.projector.project(ledger.export_events(WORKSTATE), WORKSTATE)
            self.assertEqual(result["diagnostics"], [])
            self.assertEqual(
                sorted(record["type"] for record in result["records"].values()),
                ["intent", "scope"],
            )


if __name__ == "__main__":
    unittest.main()
