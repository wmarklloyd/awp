from __future__ import annotations

import copy
import unittest

from tools.awp_projector import C1Projector


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


class C1ProjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.projector = C1Projector()
        self.created = event("evt:create", [], "intent.announced", intent_record("proposed", 1))

    def test_topological_projection_is_independent_of_transport_order(self) -> None:
        activated = intent_record("active", 2)
        activated_event = event(
            "evt:activate", ["evt:create"], "intent.activated", activated,
            prior_revision=1, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([activated_event, self.created], WORKSTATE)
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
        left = self.projector.project([self.created, first, second], WORKSTATE)
        right = self.projector.project([second, self.created, first], WORKSTATE)
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
        result = self.projector.project([self.created, invalid], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["status"], "proposed")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-INVALID-TRANSITION")

    def test_revision_conflict_is_diagnosed(self) -> None:
        activated = intent_record("active", 2)
        invalid = event(
            "evt:activate", ["evt:create"], "intent.activated", activated,
            prior_revision=4, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([self.created, invalid], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["revision"], 1)
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-REVISION-CONFLICT")

    def test_missing_parent_is_not_applied(self) -> None:
        activated = intent_record("active", 2)
        missing = event(
            "evt:activate", ["evt:missing"], "intent.activated", activated,
            prior_revision=1, transition={"from": "proposed", "to": "active"},
        )
        result = self.projector.project([self.created, missing], WORKSTATE)
        self.assertEqual(result["records"]["intent:test"]["status"], "proposed")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-MISSING-DEPENDENCY")

    def test_workstate_mismatch_is_not_applied(self) -> None:
        mismatched = copy.deepcopy(self.created)
        mismatched["event_id"] = "evt:other"
        mismatched["workstate_id"] = "workstate:other"
        result = self.projector.project([mismatched], WORKSTATE)
        self.assertEqual(result["records"], {})
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-COORD-WORKSTATE-MISMATCH")


if __name__ == "__main__":
    unittest.main()
