from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

from tools.awp_coop2 import DOORBELL_PROFILE, GIT_REF_DOORBELL_PROFILE, GitRefDoorbell, LocalDoorbell


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

    def test_git_ref_doorbell_uses_a_local_ref_safe_event_name(self) -> None:
        doorbell = GitRefDoorbell(self.project)
        with patch("tools.awp_coop2.subprocess.run") as run:
            run.return_value.returncode = 0
            signal = doorbell.publish("evt:one")
        self.assertEqual(signal["profile"], GIT_REF_DOORBELL_PROFILE)
        self.assertEqual(signal["ref"], "refs/awp/signal/evt-one")
        self.assertEqual(signal["state"], "current")
        self.assertEqual(run.call_args.args[0], ["git", "update-ref", "refs/awp/signal/evt-one", "HEAD"])

    def test_git_ref_doorbell_updates_a_local_git_namespace(self) -> None:
        subprocess.run(["git", "init"], cwd=self.project, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=AWP Test", "-c", "user.email=awp@example.test", "commit", "--allow-empty", "-m", "init"],
            cwd=self.project,
            check=True,
            capture_output=True,
            text=True,
        )
        signal = GitRefDoorbell(self.project).publish("evt:local")
        target = subprocess.run(
            ["git", "rev-parse", "refs/awp/signal/evt-local"],
            cwd=self.project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(signal["state"], "current")
        self.assertEqual(target, subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.project, check=True, capture_output=True, text=True).stdout.strip())


if __name__ == "__main__":
    unittest.main()
