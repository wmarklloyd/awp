from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.awp_presence import PresenceError, PresenceRegistry


START = datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc)


class PresenceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.registry = PresenceRegistry(Path(self.temporary.name) / "presence.sqlite3")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def enter(self, session_id: str, *, access: str = "write", scopes=("scope:app@1",)):
        return self.registry.enter(
            session_id=session_id,
            agent_id=f"agent:{session_id}",
            principal="principal:test",
            project_id="project:test",
            workstate_id="workstate:test",
            worktree=f"C:\\worktrees\\{session_id}",
            branch="main",
            revision="git:abc123",
            scopes=scopes,
            access_mode=access,
            ttl_seconds=90,
            at=START,
        )

    def test_entry_is_visible_once_per_watcher_cursor(self) -> None:
        self.enter("session:one")
        first = self.registry.scan("watcher:one", at=START)
        second = self.registry.scan("watcher:one", at=START)
        self.assertEqual([event["kind"] for event in first["events"]], ["presence.entered"])
        self.assertEqual(second["events"], [])
        self.assertEqual(second["previous_cursor"], first["cursor"])

    def test_overlapping_writer_announces_conflict(self) -> None:
        self.enter("session:one", access="read")
        result = self.enter("session:two", access="write")
        self.assertEqual(result["conflicts"][0]["other_session_id"], "session:one")
        events = self.registry.scan("watcher:conflicts", at=START)["events"]
        self.assertIn("presence.conflict_detected", [event["kind"] for event in events])

    def test_readers_on_same_scope_are_compatible(self) -> None:
        self.enter("session:one", access="read")
        result = self.enter("session:two", access="read")
        self.assertEqual(result["conflicts"], [])

    def test_heartbeat_extends_expiry_and_expired_session_cannot_revive(self) -> None:
        self.enter("session:one")
        renewed = self.registry.heartbeat(
            "session:one", ttl_seconds=90, at=START + timedelta(seconds=60)
        )
        self.assertEqual(renewed["status"], "active")
        self.assertEqual(
            self.registry.active("project:test", at=START + timedelta(seconds=120))[0][
                "session_id"
            ],
            "session:one",
        )
        self.assertEqual(
            self.registry.active("project:test", at=START + timedelta(seconds=151)), []
        )
        with self.assertRaises(PresenceError):
            self.registry.heartbeat("session:one", at=START + timedelta(seconds=152))

    def test_crash_expiry_is_announced_and_release_is_terminal(self) -> None:
        self.enter("session:crash")
        result = self.registry.scan("watcher:expiry", at=START + timedelta(seconds=91))
        self.assertEqual(result["expired_sessions"], ["session:crash"])
        self.assertIn("presence.expired", [event["kind"] for event in result["events"]])

        self.enter("session:clean")
        released = self.registry.leave("session:clean", at=START + timedelta(seconds=1))
        self.assertEqual(released["status"], "released")
        with self.assertRaises(PresenceError):
            self.registry.leave("session:clean", at=START + timedelta(seconds=2))

    def test_wildcard_writer_conflicts_with_narrow_scope(self) -> None:
        self.enter("session:one", access="read", scopes=("scope:docs@1",))
        result = self.enter("session:two", access="write", scopes=("*",))
        self.assertEqual(result["conflicts"][0]["overlapping_scopes"], ["scope:docs@1"])

    def test_simultaneous_entries_are_atomic(self) -> None:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(self.enter, f"session:{number}") for number in range(2)
            ]
        conflict_counts = sorted(len(future.result()["conflicts"]) for future in futures)
        self.assertEqual(conflict_counts, [0, 1])

    def test_watcher_delivery_is_bounded_and_resumable(self) -> None:
        for number in range(3):
            self.enter(f"session:{number}", access="read", scopes=(f"scope:{number}@1",))
        first = self.registry.scan("watcher:paged", limit=2, at=START)
        second = self.registry.scan("watcher:paged", limit=2, at=START)
        self.assertEqual(len(first["events"]), 2)
        self.assertTrue(first["has_more"])
        self.assertEqual(len(second["events"]), 1)
        self.assertFalse(second["has_more"])
        self.assertEqual(second["previous_cursor"], first["cursor"])


if __name__ == "__main__":
    unittest.main()
