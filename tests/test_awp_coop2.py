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


class RendezvousFixture(unittest.TestCase):
    """A throwaway Git project with a copied capsule so Rendezvous can bind."""

    def setUp(self) -> None:
        import shutil

        root = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        shutil.copy2(root / ".awp.json", self.project / ".awp.json")
        shutil.copy2(root / "awp.awp.md", self.project / "awp.awp.md")
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        for command in (["git", "init", "-q", "."], ["git", "add", "-A"], ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init"]):
            subprocess.run(command, cwd=self.project, check=True, capture_output=True, env={**__import__("os").environ, **env})
        from tools.awp_coop2 import Rendezvous

        self.rendezvous = Rendezvous(self.project)

    def tearDown(self) -> None:
        self.temporary.cleanup()


class HeartbeatAndReachTests(RendezvousFixture):
    def test_liveness_is_derived_from_heartbeats_not_declared(self) -> None:
        from tools.awp_coop2 import HEARTBEAT_TTL_SECONDS

        self.rendezvous.join("actor:a", [], observation="watcher")
        self.rendezvous.join("actor:b", [], observation="on-entry-only")
        watchers = {item["actor"]: item for item in self.rendezvous.participant_watchers()}
        # Declaring "watcher" earns nothing until a heartbeat is observed.
        self.assertEqual(watchers["actor:a"]["declared_observation"], "watcher")
        self.assertEqual(watchers["actor:a"]["watcher_liveness"], "none")
        self.assertEqual(watchers["actor:b"]["watcher_liveness"], "none")
        self.rendezvous.heartbeat("actor:a", "test-watcher")
        watchers = {item["actor"]: item for item in self.rendezvous.participant_watchers()}
        self.assertEqual(watchers["actor:a"]["watcher_liveness"], "active")
        self.assertEqual(watchers["actor:a"]["profile"], "test-watcher")
        self.assertLessEqual(watchers["actor:a"]["age_seconds"], HEARTBEAT_TTL_SECONDS)

    def test_stale_heartbeat_degrades_and_wrong_binding_is_unverified(self) -> None:
        import json
        from datetime import datetime, timedelta, timezone

        self.rendezvous.join("actor:a", [])
        path = self.rendezvous.heartbeats.path("actor:a")
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        signal = self.rendezvous.heartbeat("actor:a", "test-watcher")
        signal.pop("path")
        path.write_text(json.dumps(signal | {"last_seen": old}), encoding="utf-8")
        self.assertEqual(self.rendezvous.participant_watchers()[0]["watcher_liveness"], "stale")
        path.write_text(json.dumps(signal | {"binding_id": "binding:other"}), encoding="utf-8")
        self.assertEqual(self.rendezvous.participant_watchers()[0]["watcher_liveness"], "unverified")

    def test_signal_reach_is_per_direction_while_mailbox_reach_is_shared(self) -> None:
        self.rendezvous.join("actor:a", [])
        self.rendezvous.join("actor:b", [])
        self.rendezvous.heartbeat("actor:b", "test-watcher")
        status = self.rendezvous.status()
        self.assertEqual(status["mailbox_reach"], "shared")
        self.assertEqual(status["signal_reach"]["actor:a->actor:b"]["signal_reach"], "reachable")
        self.assertEqual(status["signal_reach"]["actor:b->actor:a"]["signal_reach"], "entry-recovery-only")
        self.assertIn("active: actor:b", status["doorbell"]["watcher_liveness"])
        self.assertFalse(any("not verified" in item for item in status["limitations"]))

    def test_join_records_observation_mode_and_rejects_unknown(self) -> None:
        from tools.awp_coop2 import CoordinationError

        self.rendezvous.join("actor:a", [], observation="watcher")
        peers = {item["actor"]: item for item in self.rendezvous.peers()["participants"]}
        self.assertEqual(peers["actor:a"]["observation"], "watcher")
        with self.assertRaises(CoordinationError):
            self.rendezvous.join("actor:c", [], observation="telepathy")


class LifecycleExpiryTests(RendezvousFixture):
    def send(self, delivery_window: int = 600, response_window: int = 600) -> str:
        self.rendezvous.join("actor:sender", [])
        self.rendezvous.join("actor:recipient", [])
        return self.rendezvous.send(
            "actor:sender", "actor:recipient", "review", "subject", "question", "actor:recipient",
            1, 4, 1200, delivery_window, response_window,
        )["interaction_id"]

    def inbox_item(self) -> dict:
        items = self.rendezvous.inbox("actor:recipient")["inbox"]
        self.assertEqual(len(items), 1)
        return items[0]

    def test_pending_request_reports_deadline_and_time_remaining(self) -> None:
        self.send(delivery_window=600)
        item = self.inbox_item()
        self.assertEqual(item["lifecycle_state"], "pending")
        self.assertFalse(item["timed_out"])
        self.assertGreater(item["seconds_remaining"], 500)

    def test_expired_delivery_window_is_undelivered_on_read_without_any_write(self) -> None:
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch

        self.send(delivery_window=1)
        before = len(self.rendezvous._events())
        future = datetime.now(timezone.utc) + timedelta(seconds=5)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return future if tz else future.replace(tzinfo=None)

        with patch("tools.awp_coop2.datetime", Clock):
            item = self.inbox_item()
        self.assertEqual(item["lifecycle_state"], "undelivered")
        self.assertTrue(item["timed_out"])
        self.assertGreater(item["overdue_seconds"], 0)
        self.assertEqual(len(self.rendezvous._events()), before, "expiry must be derived, never published")

    def test_accepted_but_unanswered_past_deadline_is_delivered_unanswered(self) -> None:
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch

        interaction = self.send(response_window=1)
        self.rendezvous.observe("actor:recipient", interaction)
        self.rendezvous.accept("actor:recipient", interaction, 1)
        future = datetime.now(timezone.utc) + timedelta(seconds=5)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return future if tz else future.replace(tzinfo=None)

        with patch("tools.awp_coop2.datetime", Clock):
            item = self.inbox_item()
        self.assertEqual(item["lifecycle_state"], "delivered_unanswered")
        self.assertTrue(item["timed_out"])


class WatcherObservedOnQueueTests(unittest.TestCase):
    def test_watcher_publishes_observed_and_heartbeat_when_it_queues(self) -> None:
        from tools.awp_codex_wake import CodexQueueWatcher, atomic_json

        class Rendezvous:
            def __init__(self) -> None:
                self.events = [{"event_id": "evt:req", "kind": "coop2.interaction.requested", "payload": {"interaction_id": "interaction:x", "recipient": "actor:codex"}}]
                self.observed: list[tuple[str, str]] = []
                self.heartbeats = 0

            def _events(self):
                return self.events

            def observe(self, actor, interaction_id):
                self.observed.append((actor, interaction_id))
                return {"receipt": {"event_id": "evt:observed"}}

            def heartbeat(self, actor, profile):
                self.heartbeats += 1
                return {"last_seen": "now", "path": "p"}

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        state = Path(temporary.name) / "w.json"
        atomic_json(state, {"profile": "codex-local-queue-watcher-v1", "initialized": True, "notified_events": []})
        rendezvous = Rendezvous()
        watcher = CodexQueueWatcher(rendezvous, "actor:codex", "thread", "ws://t", state)
        with patch.object(watcher, "queue"):
            result = watcher.step()
        self.assertEqual(rendezvous.observed, [("actor:codex", "interaction:x")])
        self.assertEqual(result["observed_receipts"], {"evt:req": "evt:observed"})
        self.assertEqual(rendezvous.heartbeats, 1)
        self.assertEqual(result["heartbeat"]["last_seen"], "now")

    def test_watcher_tolerates_rendezvous_without_liveness_methods(self) -> None:
        from tools.awp_codex_wake import CodexQueueWatcher, atomic_json

        class Bare:
            def _events(self):
                return [{"event_id": "evt:req", "kind": "coop2.interaction.requested", "payload": {"interaction_id": "interaction:x", "recipient": "actor:codex"}}]

        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        state = Path(temporary.name) / "w.json"
        atomic_json(state, {"profile": "codex-local-queue-watcher-v1", "initialized": True, "notified_events": []})
        watcher = CodexQueueWatcher(Bare(), "actor:codex", "thread", "ws://t", state)
        with patch.object(watcher, "queue"):
            result = watcher.step()
        self.assertEqual(result["queued_events"], ["evt:req"])
        self.assertEqual(result["observed_receipts"], {})
        self.assertNotIn("heartbeat", result)
