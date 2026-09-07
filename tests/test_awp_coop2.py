from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.awp_coop2 import DOORBELL_PROFILE, LocalDoorbell


class LocalDoorbellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        self.doorbell = LocalDoorbell(self.project)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def publish(self, event_id: str) -> dict:
        return self.doorbell.publish(
            project_id="project:test",
            workstate_id="workstate:test",
            binding_id="binding:test",
            event_id=event_id,
            frontier=[event_id],
            interaction_id="interaction:test",
            kind="coop2.interaction.requested",
        )

    def test_signal_is_content_free_and_verifiable(self) -> None:
        self.publish("evt:one")
        status = self.doorbell.status(
            project_id="project:test", workstate_id="workstate:test", binding_id="binding:test"
        )
        self.assertEqual(status["state"], "current")
        self.assertEqual(status["signal"]["profile"], DOORBELL_PROFILE)
        self.assertEqual(status["signal"]["event_id"], "evt:one")
        self.assertNotIn("question", status["signal"])
        self.assertEqual(status["content"], "none; watchers refresh the authoritative ledger")

    def test_latest_signal_coalesces_and_identity_mismatch_is_unverifiable(self) -> None:
        self.publish("evt:one")
        self.publish("evt:two")
        current = self.doorbell.status(
            project_id="project:test", workstate_id="workstate:test", binding_id="binding:test"
        )
        self.assertEqual(current["signal"]["event_id"], "evt:two")
        mismatch = self.doorbell.status(
            project_id="project:other", workstate_id="workstate:test", binding_id="binding:test"
        )
        self.assertEqual(mismatch["state"], "unverifiable")


if __name__ == "__main__":
    unittest.main()
