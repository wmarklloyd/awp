from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.awp_coordination import CoordinationLedger
from tools.awp_participation import ParticipationAdapter


class ParticipationAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        ledger = CoordinationLedger(Path(self.temporary.name) / "coordination.sqlite3")
        self.adapter = ParticipationAdapter(
            ledger,
            workstate_id="workstate:test",
            project_id="project:test",
            actor="actor:one",
            base_revision="git:base",
        )
        self.validator = Draft202012Validator(
            json.loads(
                (Path(__file__).parents[1] / "schemas" / "awp-participation-0.1.schema.json").read_text(
                    encoding="utf-8"
                )
            ),
            format_checker=FormatChecker(),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_request(self) -> dict:
        return {
            "operation": "read",
            "request_id": "request:read",
            "project": "project:test",
            "goal": "goal:test",
        }

    def announce_request(self, request_id: str = "request:announce") -> dict:
        return {
            "operation": "announce",
            "request_id": request_id,
            "project": "project:test",
            "context": "ctx:test",
            "goal": "goal:test",
            "summary": "Update the test file",
            "scope": [{"path": "src/app.py", "access": "write"}],
        }

    def test_read_returns_bounded_context_and_frontier(self) -> None:
        result = self.adapter.read(self.read_request())
        self.assertEqual(result["publication"], "not_applicable")
        self.assertEqual(result["coordination"], "clear")
        self.assertTrue(result["context"].startswith("ctx:"))
        self.assertEqual(result["frontier"], [])
        self.assertEqual(result["next"]["operation"], "announce")

    def test_all_supported_operation_responses_match_the_contract(self) -> None:
        responses = []
        read = self.adapter.read(self.read_request())
        responses.append(read)
        announcement = self.adapter.announce(self.announce_request())
        responses.append(announcement)
        responses.append(
            self.adapter.publish(
                {
                    "operation": "publish",
                    "request_id": "request:contract-publish",
                    "project": "project:test",
                    "context": "ctx:test",
                    "intent": announcement["intent"],
                    "summary": "Contract validation result",
                    "actual_scope": [{"path": "src/app.py", "access": "write"}],
                    "evidence": ["artifact:contract-test"],
                }
            )
        )
        responses.append(
            self.adapter.checkpoint(
                {
                    "operation": "checkpoint",
                    "request_id": "request:contract-checkpoint",
                    "project": "project:test",
                    "context": "ctx:test",
                    "intent": announcement["intent"],
                    "next_action": "Continue contract validation",
                    "mode": "continue",
                    "capsule_confirmation": {
                        "frontier": responses[-1]["frontier"],
                        "digest": "sha256:contract-test",
                    },
                }
            )
        )
        first = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:contract",
            project_id="project:test",
            actor="actor:first",
            base_revision="git:base",
        )
        first.announce(self.announce_request("request:contract-first"))
        second = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:contract",
            project_id="project:test",
            actor="actor:second",
            base_revision="git:base",
        )
        second_announcement = second.announce(self.announce_request("request:contract-second"))
        responses.append(
            second.resolve(
                {
                    "operation": "resolve",
                    "request_id": "request:contract-resolve",
                    "project": "project:test",
                    "context": "ctx:test",
                    "intent": second_announcement["intent"],
                    "overlap": second_announcement["overlaps"][0]["handle"],
                    "disposition": "ordered",
                    "rationale": "Contract validation disposition",
                }
            )
        )
        for response in responses:
            self.assertEqual([], list(self.validator.iter_errors(response)))
            if "publication_receipt" in response:
                self.assertEqual([], list(self.validator.iter_errors(response["publication_receipt"])))

    def test_announce_is_confirmed_and_retry_is_idempotent(self) -> None:
        request = self.announce_request()
        first = self.adapter.announce(request)
        second = self.adapter.announce(request)
        self.assertEqual(first["publication"], "confirmed")
        self.assertEqual(first["coordination"], "clear")
        self.assertEqual(first["publication_receipt"], second["publication_receipt"])
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 2)

    def test_reusing_request_id_with_changed_content_is_rejected(self) -> None:
        self.adapter.announce(self.announce_request())
        changed = self.announce_request()
        changed["summary"] = "Different content"
        result = self.adapter.announce(changed)
        self.assertEqual(result["publication"], "rejected")
        self.assertIn("request ID", result["diagnostics"][0]["message"])
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 2)

    def test_second_writer_receives_overlap_warning(self) -> None:
        self.adapter.announce(self.announce_request("request:first"))
        second = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:test",
            project_id="project:test",
            actor="actor:two",
            base_revision="git:base",
        )
        result = second.announce(self.announce_request("request:second"))
        self.assertEqual(result["publication"], "confirmed")
        self.assertEqual(result["coordination"], "warning")
        self.assertEqual(result["next"]["operation"], "resolve")
        self.assertTrue(result["overlaps"])

    def test_publish_records_a_proposed_change_set_and_receipt(self) -> None:
        announcement = self.adapter.announce(self.announce_request())
        request = {
            "operation": "publish",
            "request_id": "request:publish",
            "project": "project:test",
            "context": "ctx:test",
            "intent": announcement["intent"],
            "summary": "Updated the test file",
            "actual_scope": [{"path": "src/app.py", "access": "write"}],
            "evidence": ["artifact:test-log"],
        }
        result = self.adapter.publish(request)
        self.assertEqual(result["publication"], "confirmed")
        self.assertEqual(result["coordination"], "clear")
        self.assertTrue(result["coverage"]["scope_complete"])
        self.assertEqual(result["next"]["operation"], "checkpoint")
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 3)
        retry = self.adapter.publish(request)
        self.assertEqual(result["publication_receipt"], retry["publication_receipt"])
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 3)

    def test_publish_reports_scope_mismatch_and_missing_evidence(self) -> None:
        announcement = self.adapter.announce(self.announce_request())
        result = self.adapter.publish(
            {
                "operation": "publish",
                "request_id": "request:publish-mismatch",
                "project": "project:test",
                "context": "ctx:test",
                "intent": announcement["intent"],
                "summary": "Updated another file",
                "actual_scope": [{"path": "README.md", "access": "write"}],
            }
        )
        self.assertEqual(result["publication"], "confirmed")
        self.assertEqual(result["coordination"], "warning")
        self.assertFalse(result["coverage"]["scope_complete"])
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertEqual(codes, {"AWP-COORD-SCOPE-MISMATCH", "AWP-COORD-EVIDENCE-MISSING"})

    def test_publish_unknown_intent_is_rejected(self) -> None:
        result = self.adapter.publish(
            {
                "operation": "publish",
                "request_id": "request:unknown-publish",
                "project": "project:test",
                "context": "ctx:test",
                "intent": "intent:missing",
                "summary": "No change",
                "actual_scope": [{"path": "README.md", "access": "write"}],
            }
        )
        self.assertEqual(result["publication"], "rejected")
        self.assertIn("unknown intent", result["diagnostics"][0]["message"])

    def test_resolve_can_order_an_overlap_and_retry_is_idempotent(self) -> None:
        self.adapter.announce(self.announce_request("request:first"))
        second = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:test",
            project_id="project:test",
            actor="actor:two",
            base_revision="git:base",
        )
        announcement = second.announce(self.announce_request("request:second"))
        overlap_id = announcement["overlaps"][0]["handle"]
        request = {
            "operation": "resolve",
            "request_id": "request:resolve",
            "project": "project:test",
            "context": "ctx:test",
            "intent": announcement["intent"],
            "overlap": overlap_id,
            "disposition": "ordered",
            "rationale": "The second writer proceeds after the first scope is complete.",
        }
        result = second.resolve(request)
        self.assertEqual(result["publication"], "confirmed")
        self.assertEqual(result["coordination"], "clear")
        self.assertEqual(result["next"]["operation"], "read")
        self.assertEqual(second.ledger.refresh("workstate:test")["open_overlaps"], [])
        retry = second.resolve(request)
        self.assertEqual(result["publication_receipt"], retry["publication_receipt"])
        self.assertEqual(len(second.ledger.export_events("workstate:test")), 6)

    def test_resolve_requires_an_overlap_participant(self) -> None:
        self.adapter.announce(self.announce_request("request:first"))
        second = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:test",
            project_id="project:test",
            actor="actor:two",
            base_revision="git:base",
        )
        announcement = second.announce(self.announce_request("request:second"))
        outsider = ParticipationAdapter(
            self.adapter.ledger,
            workstate_id="workstate:test",
            project_id="project:test",
            actor="actor:outsider",
            base_revision="git:base",
        )
        result = outsider.resolve(
            {
                "operation": "resolve",
                "request_id": "request:outsider-resolve",
                "project": "project:test",
                "context": "ctx:test",
                "intent": announcement["intent"],
                "overlap": announcement["overlaps"][0]["handle"],
                "disposition": "ordered",
                "rationale": "Unauthorized disposition.",
            }
        )
        self.assertEqual(result["publication"], "rejected")
        self.assertIn("not an overlap participant", result["diagnostics"][0]["message"])

    def test_checkpoint_continue_requires_and_records_capsule_confirmation(self) -> None:
        announcement = self.adapter.announce(self.announce_request())
        request = {
            "operation": "checkpoint",
            "request_id": "request:checkpoint",
            "project": "project:test",
            "context": "ctx:test",
            "intent": announcement["intent"],
            "next_action": "Run the integration review",
            "unresolved_work": [],
            "mode": "continue",
            "capsule_confirmation": {
                "frontier": announcement["frontier"],
                "digest": "sha256:capsule-test",
            },
        }
        result = self.adapter.checkpoint(request)
        self.assertEqual(result["publication"], "confirmed")
        self.assertEqual(result["coordination"], "clear")
        self.assertTrue(result["checkpoint"].startswith("checkpoint:"))
        self.assertEqual(result["publication_receipt"]["event_ids"], [])
        retry = self.adapter.checkpoint(request)
        self.assertEqual(result["publication_receipt"], retry["publication_receipt"])
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 2)

    def test_checkpoint_returns_pending_for_stale_capsule_frontier(self) -> None:
        announcement = self.adapter.announce(self.announce_request())
        result = self.adapter.checkpoint(
            {
                "operation": "checkpoint",
                "request_id": "request:stale-checkpoint",
                "project": "project:test",
                "context": "ctx:test",
                "intent": announcement["intent"],
                "next_action": "Refresh the capsule",
                "mode": "continue",
                "capsule_confirmation": {
                    "frontier": ["evt:not-current"],
                    "digest": "sha256:stale",
                },
            }
        )
        self.assertEqual(result["publication"], "pending")
        self.assertEqual(result["coordination"], "stale")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-CAPSULE-FRONTIER-STALE")

    def test_checkpoint_exit_stays_pending_without_terminal_bindings(self) -> None:
        announcement = self.adapter.announce(self.announce_request())
        result = self.adapter.checkpoint(
            {
                "operation": "checkpoint",
                "request_id": "request:exit-checkpoint",
                "project": "project:test",
                "context": "ctx:test",
                "intent": announcement["intent"],
                "next_action": "Stop this session",
                "mode": "exit",
            }
        )
        self.assertEqual(result["publication"], "pending")
        self.assertEqual(result["coordination"], "needs_input")
        self.assertEqual(result["diagnostics"][0]["code"], "AWP-CAPSULE-INCOMPLETE-HANDOFF")

    def test_mixed_access_scopes_are_rejected_by_local_slice(self) -> None:
        request = self.announce_request()
        request["scope"].append({"path": "README.md", "access": "read"})
        result = self.adapter.announce(request)
        self.assertEqual(result["publication"], "rejected")
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 0)


if __name__ == "__main__":
    unittest.main()
