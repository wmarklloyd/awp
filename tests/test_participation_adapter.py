from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
        self.assertEqual(result["next"]["operation"], "interact")
        self.assertTrue(result["interactions"])

    def test_mixed_access_scopes_are_rejected_by_local_slice(self) -> None:
        request = self.announce_request()
        request["scope"].append({"path": "README.md", "access": "read"})
        result = self.adapter.announce(request)
        self.assertEqual(result["publication"], "rejected")
        self.assertEqual(len(self.adapter.ledger.export_events("workstate:test")), 0)


if __name__ == "__main__":
    unittest.main()
