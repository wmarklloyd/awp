from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.awp_coordination import CoordinationError, CoordinationLedger


START = datetime(2026, 9, 4, 20, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


class CoordinationLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "coordination.sqlite3"
        self.ledger = CoordinationLedger(self.path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def begin(
        self,
        actor: str,
        scope: tuple[str, str] = ("file", "src/app.py"),
        *,
        access: str = "write",
        policy: str = "warn",
    ):
        return self.ledger.begin(
            workstate_id="workstate:test",
            project_id="repo:test",
            actor=actor,
            goal="goal:test",
            summary=f"Work by {actor}",
            base_revision="git:abc123",
            scopes=[scope],
            access=access,
            policy=policy,
            at=START,
        )

    def test_begin_emits_schema_valid_scope_and_intent_events(self) -> None:
        result = self.begin("actor:one")
        events = self.ledger.export_events("workstate:test")
        self.assertEqual([event["kind"] for event in events], ["scope.created", "intent.announced"])
        for family, coordination in (("0.6", "0.3"), ("0.7", "0.4")):
            core_schema = json.loads(
                (ROOT / "schemas" / f"awp-core-{family}.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            coordination_schema = json.loads(
                (ROOT / "schemas" / f"awp-coordination-{coordination}.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            core_validator = Draft202012Validator(core_schema)
            coordination_validator = Draft202012Validator(coordination_schema)
            for event in events:
                self.assertEqual(list(core_validator.iter_errors(event)), [])
                self.assertEqual(list(coordination_validator.iter_errors(event)), [])
                replacement = event["payload"]["replacement"]
                self.assertEqual(list(coordination_validator.iter_errors(replacement)), [])
        self.assertEqual(result["advisory_status"], "clear")

    def test_overlapping_writers_are_reported_before_work(self) -> None:
        self.begin("actor:one", ("directory", "src"))
        result = self.begin("actor:two", ("file", "src/app.py"))
        self.assertEqual(len(result["overlaps"]), 1)
        self.assertEqual(result["overlaps"][0]["policy_action"], "warn")
        self.assertEqual(result["advisory_status"], "warn")

    def test_block_policy_keeps_conflicting_intent_proposed(self) -> None:
        self.begin("actor:one")
        result = self.begin("actor:two", policy="block")
        self.assertEqual(result["advisory_status"], "block")
        self.assertEqual(result["intent"]["status"], "proposed")
        self.assertEqual(self.ledger.refresh("workstate:test")["advisory_status"], "block")
        resolved = self.ledger.resolve_overlap(
            workstate_id="workstate:test",
            overlap_id=result["overlaps"][0]["id"],
            actor="actor:one",
            reason="Scopes were partitioned",
            at=START,
        )
        self.assertEqual(resolved["overlap"]["status"], "resolved")
        self.assertEqual(self.ledger.refresh("workstate:test")["advisory_status"], "clear")
        activated = self.ledger.transition_intent(
            workstate_id="workstate:test", intent_id=result["intent"]["id"], actor="actor:two",
            target="active", reason="blocking overlap resolved",
        )
        self.assertEqual(activated["intent"]["status"], "active")

    def test_same_actor_overlap_is_reported(self):
        first = self.ledger.begin(
            workstate_id="workstate:test", project_id="project:test", actor="actor:one",
            goal="first", summary="first", base_revision="git:abc", scopes=[("file", "src/a.py")],
        )
        second = self.ledger.begin(
            workstate_id="workstate:test", project_id="project:test", actor="actor:one",
            goal="second", summary="second", base_revision="git:abc", scopes=[("file", "src/a.py")],
        )
        self.assertTrue(second["overlaps"])

    def test_only_owner_can_transition(self):
        result = self.ledger.begin(
            workstate_id="workstate:test", project_id="project:test", actor="actor:one",
            goal="first", summary="first", base_revision="git:abc", scopes=[("file", "src/a.py")],
        )
        with self.assertRaises(CoordinationError):
            self.ledger.transition_intent(
                workstate_id="workstate:test", intent_id=result["intent"]["id"], actor="actor:two",
                target="completed", reason="unauthorized",
            )

    def test_readers_are_compatible_but_relied_read_conflicts_with_write(self) -> None:
        self.begin("actor:one", access="read")
        compatible = self.begin("actor:two", access="read")
        self.assertEqual(compatible["overlaps"], [])
        relied = self.begin("actor:three", access="relied_upon_read")
        self.assertEqual(relied["overlaps"], [])
        writer = self.begin("actor:four", access="write")
        self.assertEqual(len(writer["overlaps"]), 1)

    def test_completion_removes_intent_from_active_projection(self) -> None:
        intent = self.begin("actor:one")["intent"]
        result = self.ledger.transition_intent(
            workstate_id="workstate:test",
            intent_id=intent["id"],
            actor="actor:one",
            target="completed",
            reason="Implementation and tests completed",
            outputs=["artifact:patch"],
            at=START,
        )
        self.assertEqual(result["intent"]["revision"], 2)
        self.assertEqual(self.ledger.refresh("workstate:test")["active_intents"], [])
        with self.assertRaises(CoordinationError):
            self.ledger.transition_intent(
                workstate_id="workstate:test",
                intent_id=intent["id"],
                actor="actor:one",
                target="completed",
                reason="again",
                at=START,
            )

    def test_scan_has_durable_per_watcher_cursor(self) -> None:
        self.begin("actor:one")
        first = self.ledger.scan("workstate:test", "watcher:one", limit=1)
        second = self.ledger.scan("workstate:test", "watcher:one", limit=10)
        third = self.ledger.scan("workstate:test", "watcher:one", limit=10)
        self.assertTrue(first["has_more"])
        self.assertEqual(len(second["events"]), 1)
        self.assertEqual(third["events"], [])

    def test_simultaneous_intents_are_serialized_and_conflict_is_preserved(self) -> None:
        def publish(number: int):
            ledger = CoordinationLedger(self.path)
            return ledger.begin(
                workstate_id="workstate:test",
                project_id="repo:test",
                actor=f"actor:{number}",
                goal="goal:test",
                summary="Concurrent work",
                base_revision="git:abc123",
                scopes=[("file", "src/app.py")],
                at=START,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(publish, range(2)))
        self.assertEqual(sorted(len(result["overlaps"]) for result in results), [0, 1])
        self.assertEqual(len(self.ledger.export_events("workstate:test")), 5)


if __name__ == "__main__":
    unittest.main()
