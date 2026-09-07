from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.awp_coordination import (
    CoordinationError,
    CoordinationLedger,
    replace_capsule_projection,
    capsule_integrity,
    operational_context,
    scopes_overlap,
    stable_project_id,
)


START = datetime(2026, 9, 4, 20, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


class CoordinationLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "coordination.sqlite3"
        self.ledger = CoordinationLedger(self.path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_project_identity_is_repository_intrinsic(self) -> None:
        self.assertTrue(stable_project_id(ROOT).startswith("git-root:"))
        self.assertNotIn(str(ROOT), stable_project_id(ROOT))

    def test_binding_identity_is_durable(self) -> None:
        first = self.ledger.binding_id()
        reopened = CoordinationLedger(self.path)
        self.assertEqual(reopened.binding_id(), first)

    def test_binding_identity_is_stable_and_frontier_is_an_observation(self) -> None:
        context = operational_context(ROOT, self.path)
        self.assertEqual(
            set(context["binding_identity"]),
            {"workstate_id", "project_id", "store_id", "scope_model", "binding_epoch"},
        )
        self.assertEqual(context["binding_observation"]["operational_reach"], "configured-unverified")
        self.assertIn("frontier", context["binding_observation"])
        self.assertEqual(
            context["binding_observation"]["atomicity_mechanism"],
            "sqlite-begin-immediate",
        )
        self.assertEqual(context["cooperation_binding"]["contract"], "COOP-1")
        self.assertEqual(context["cooperation_binding"]["claim_state"], "partial")
        self.assertEqual(
            context["cooperation_binding"]["subprotocols"]["work"],
            {"enabled": True, "claim_state": "partial"},
        )
        self.assertEqual(
            context["cooperation_binding"]["subprotocols"]["consultation"],
            {"enabled": False},
        )
        self.assertNotIn("conformance_level", context["cooperation_binding"])
        self.assertIn(
            "coordination-awareness", context["cooperation_binding"]["capabilities"]
        )
        cooperation_schema = json.loads(
            (ROOT / "schemas" / "awp-cooperation-0.1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            list(Draft202012Validator(cooperation_schema).iter_errors(context["cooperation_binding"])),
            [],
        )

    def test_explicit_store_becomes_shared_after_two_distinct_lease_entries(self) -> None:
        project_id = stable_project_id(ROOT)
        workstate_id = "urn:uuid:conversation-awp-design-2026-09-03"
        self.ledger.enter_lease(
            workstate_id=workstate_id,
            project_id=project_id,
            actor="actor:one",
            location="C:/one",
            base_revision="git:test",
            intended_scopes=[],
            ttl_seconds=900,
            at=START,
        )
        self.ledger.enter_lease(
            workstate_id=workstate_id,
            project_id=project_id,
            actor="actor:two",
            location="C:/two",
            base_revision="git:test",
            intended_scopes=[],
            ttl_seconds=900,
            at=START,
        )
        context = operational_context(ROOT, self.path)
        self.assertEqual(context["binding_observation"]["operational_reach"], "shared")
        self.assertEqual(context["shared_reach_evidence"]["actors"], ["actor:one", "actor:two"])

    def test_checkpoint_projection_rejects_stale_frontier_and_returns_matching_receipt(self) -> None:
        initial = self.begin("actor:one")["frontier"]
        capsule = Path(self.temporary.name) / "project.awp.md"
        capsule.write_text(
            "---\n"
            "awp_version: 0.8.0\n"
            "frontier:\n"
            f"  - {initial[0]}\n"
            "checkpoint: checkpoint:before\n"
            "generated_at: 2026-09-05T19:00:00Z\n"
            "generated_digest: sha256:PLACEHOLDER\n"
            "---\n\n"
            "<!-- awp:generated:start -->\n"
            "# Test capsule\n"
            "<!-- awp:generated:end -->\n",
            encoding="utf-8",
        )
        digest = "sha256:" + hashlib.sha256(b"# Test capsule").hexdigest()
        original_capsule_digest = "sha256:" + hashlib.sha256(capsule.read_bytes()).hexdigest()
        capsule.write_text(
            capsule.read_text(encoding="utf-8").replace("sha256:PLACEHOLDER", digest),
            encoding="utf-8",
        )
        result = self.ledger.publish_checkpoint(
            workstate_id="workstate:test",
            actor="actor:one",
            capsule=capsule,
            expected_capsule_frontier=initial,
            expected_ledger_frontier=initial,
            expected_digest=digest,
            next_action="continue",
            unresolved_work=[],
            request_id="request:checkpoint",
            request_hash="hash:checkpoint",
        )
        self.assertEqual(capsule_integrity(capsule)["state"], "current")
        self.assertEqual(
            result["receipt"]["digest"],
            "sha256:" + hashlib.sha256(capsule.read_bytes()).hexdigest(),
        )
        self.assertEqual(result["receipt"]["frontier"], result["frontier"])
        with self.assertRaises(CoordinationError):
            replace_capsule_projection(
                capsule,
                expected_frontier=result["frontier"],
                expected_digest=digest,
                expected_capsule_digest=original_capsule_digest,
                frontier=result["frontier"],
                checkpoint_id="checkpoint:stale-whole-file",
                generated_at="2026-09-05T19:00:00Z",
            )
        before = capsule.read_bytes()
        with self.assertRaises(CoordinationError):
            self.ledger.publish_checkpoint(
                workstate_id="workstate:test",
                actor="actor:one",
                capsule=capsule,
                expected_capsule_frontier=initial,
                expected_ledger_frontier=initial,
                expected_digest=digest,
                next_action="stale",
                unresolved_work=[],
                request_id="request:stale-checkpoint",
                request_hash="hash:stale",
            )
        self.assertEqual(capsule.read_bytes(), before)

    def test_repository_identity_mismatch_fails_closed(self) -> None:
        left = {"repository": "repo:one", "kind": "file", "path": "src/app.py"}
        right = {"repository": "repo:two", "kind": "file", "path": "src/app.py"}
        with self.assertRaises(CoordinationError):
            scopes_overlap(left, right)

    def test_mismatched_repository_identity_rolls_back_announce(self) -> None:
        self.begin("actor:one")
        self.enter_lease("actor:two")
        before = self.ledger.export_events("workstate:test")
        with self.assertRaises(CoordinationError):
            self.ledger.begin(
                workstate_id="workstate:test",
                project_id="repo:other",
                actor="actor:two",
                goal="goal:test",
                summary="Wrong repository identity",
                base_revision="git:abc123",
                scopes=[("file", "src/app.py")],
                policy="block",
                at=START,
            )
        self.assertEqual(self.ledger.export_events("workstate:test"), before)

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

    def enter_lease(self, actor: str, *, ttl_seconds: int = 900):
        return self.ledger.enter_lease(
            workstate_id="workstate:test",
            project_id="repo:test",
            actor=actor,
            location="C:/worktree",
            base_revision="git:abc123",
            intended_scopes=["src/app.py"],
            ttl_seconds=ttl_seconds,
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
        self.enter_lease("actor:two")
        result = self.begin("actor:two", policy="block")
        self.assertEqual(result["advisory_status"], "block")
        self.assertEqual(result["intent"]["status"], "proposed")
        self.assertEqual(self.ledger.refresh("workstate:test")["advisory_status"], "block")
        resolved = self.ledger.resolve_overlap(
            workstate_id="workstate:test",
            overlap_id=result["overlaps"][0]["id"],
            actor="actor:one",
            disposition="partition",
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

    def test_escalation_does_not_silently_clear_a_blocking_overlap(self) -> None:
        self.begin("actor:one")
        self.enter_lease("actor:two")
        blocked = self.begin("actor:two", policy="block")
        overlap_id = blocked["overlaps"][0]["id"]
        self.ledger.resolve_overlap(
            workstate_id="workstate:test",
            overlap_id=overlap_id,
            actor="actor:one",
            disposition="escalation",
            reason="Decision owner must choose an order.",
            at=START,
        )
        self.assertEqual(self.ledger.refresh("workstate:test")["advisory_status"], "block")

    def test_lease_lifecycle_is_bounded_and_required_for_guarded_begin(self) -> None:
        with self.assertRaises(CoordinationError):
            self.begin("actor:one", policy="block")
        lease = self.enter_lease("actor:one", ttl_seconds=5)["lease"]
        permitted = self.begin("actor:one", policy="block")
        self.assertEqual(permitted["intent"]["lease"], lease["id"])
        refreshed = self.ledger.refresh("workstate:test", at=START + timedelta(seconds=6))
        self.assertEqual(refreshed["active_leases"], [])
        self.assertEqual(refreshed["expired_leases"], [lease["id"]])
        with self.assertRaises(CoordinationError):
            self.ledger.renew_lease(
                workstate_id="workstate:test",
                lease_id=lease["id"],
                actor="actor:one",
                at=START + timedelta(seconds=7),
            )

    def test_lease_release_requires_terminal_intent_and_handoff_receipt(self) -> None:
        lease = self.enter_lease("actor:one")["lease"]
        intent = self.begin("actor:one", policy="block")["intent"]
        receipt = {
            "path": "awp.awp.md",
            "digest": "sha256:" + "a" * 64,
            "verified_at": "2026-09-04T20:00:00Z",
        }
        with self.assertRaises(CoordinationError):
            self.ledger.release_lease(
                workstate_id="workstate:test",
                lease_id=lease["id"],
                actor="actor:one",
                handoff_receipt=receipt,
                at=START,
            )
        self.ledger.transition_intent(
            workstate_id="workstate:test",
            intent_id=intent["id"],
            actor="actor:one",
            target="completed",
            reason="handoff published",
            at=START,
        )
        with self.assertRaises(CoordinationError):
            self.ledger.release_lease(
                workstate_id="workstate:test",
                lease_id=lease["id"],
                actor="actor:one",
                at=START,
            )
        released = self.ledger.release_lease(
            workstate_id="workstate:test",
            lease_id=lease["id"],
            actor="actor:one",
            handoff_receipt=receipt,
            at=START,
        )
        self.assertEqual(released["lease"]["status"], "released")
        self.assertEqual(released["lease"]["handoff_receipt"], receipt)
        cooperation_schema = json.loads(
            (ROOT / "schemas" / "awp-cooperation-0.1.schema.json").read_text(encoding="utf-8")
        )
        errors = list(
            Draft202012Validator(cooperation_schema).iter_errors(released["lease"])
        )
        self.assertEqual(errors, [])

    def test_shared_binding_two_participant_guarded_trial(self) -> None:
        first_ledger = CoordinationLedger(self.path)
        second_ledger = CoordinationLedger(self.path)
        self.assertEqual(first_ledger.binding_id(), second_ledger.binding_id())
        first_lease = self.enter_lease("actor:one")["lease"]
        second_lease = self.enter_lease("actor:two")["lease"]
        self.assertEqual(
            self.ledger.refresh("workstate:test", at=START)["live_participants"],
            ["actor:one", "actor:two"],
        )

        first = self.begin("actor:one", ("directory", "consultations"), policy="block")
        second = self.begin("actor:two", ("directory", "docs"), policy="block")
        self.assertEqual((first["advisory_status"], second["advisory_status"]), ("clear", "clear"))
        self.assertEqual(first["intent"]["lease"], first_lease["id"])
        self.assertEqual(second["intent"]["lease"], second_lease["id"])

        def announce_conflict(actor: str) -> dict:
            return CoordinationLedger(self.path).begin(
                workstate_id="workstate:test",
                project_id="repo:test",
                actor=actor,
                goal="goal:trial",
                summary="Simultaneous guarded trial",
                base_revision="git:abc123",
                scopes=[("file", "spec/drafts/0.8.0/cooperation-contracts.md")],
                policy="block",
                at=START,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            conflicts = list(executor.map(announce_conflict, ("actor:one", "actor:two")))
        permitted = next(result for result in conflicts if result["intent"]["status"] == "active")
        blocked = next(result for result in conflicts if result["intent"]["status"] == "proposed")
        self.assertEqual(permitted["advisory_status"], "clear")
        self.assertEqual(blocked["advisory_status"], "block")

        self.ledger.resolve_overlap(
            workstate_id="workstate:test",
            overlap_id=blocked["overlaps"][0]["id"],
            actor="actor:one",
            disposition="order",
            reason="The permitted actor integrates first.",
            at=START,
        )
        activated = self.ledger.transition_intent(
            workstate_id="workstate:test",
            intent_id=blocked["intent"]["id"],
            actor=blocked["intent"]["created_by"],
            target="active",
            reason="ordered overlap resolved",
            at=START,
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
