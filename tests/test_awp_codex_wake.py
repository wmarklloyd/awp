from __future__ import annotations

import tempfile
import unittest
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from tools.awp_codex_wake import (
    MAX_NOTIFIED_EVENTS,
    CodexQueueWatcher,
    atomic_json,
    bounded_event_ids,
    control_is_current,
    default_state_path,
)


class FakeRendezvous:
    def __init__(self, events: list[dict]) -> None:
        self.events = events

    def _events(self) -> list[dict]:
        return self.events


def event(event_id: str, kind: str, recipient: str, interaction_id: str = "interaction:test") -> dict:
    return {"event_id": event_id, "kind": kind, "payload": {"interaction_id": interaction_id, "recipient": recipient}}


class CodexQueueWatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state = Path(self.temporary.name) / "watcher.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_direct_script_invocation_loads_package_imports(self) -> None:
        result = subprocess.run(
            ["python", "awp_codex_wake.py", "--help"],
            cwd=Path(__file__).resolve().parents[1] / "tools",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Codex app-server thread identifier", result.stdout)

    def test_default_state_path_falls_back_when_project_runtime_is_unusable(self) -> None:
        project = Path(self.temporary.name) / "project"
        project.mkdir()
        with patch("tools.awp_codex_wake._state_path_usable", side_effect=[False, True]):
            state, fallback = default_state_path(project, "actor:claude")
        self.assertTrue(fallback)
        self.assertEqual(state.parent, Path(tempfile.gettempdir()) / "awp")
        self.assertNotEqual(state, default_state_path(project, "actor:codex")[0])

    def test_only_recipient_events_are_queued_once(self) -> None:
        atomic_json(self.state, {"profile": "codex-local-queue-watcher-v1", "initialized": True, "notified_events": []})
        watcher = CodexQueueWatcher(
            FakeRendezvous([
                event("evt:request", "coop2.interaction.requested", "actor:codex"),
                event("evt:other", "coop2.interaction.requested", "actor:claude"),
                event("evt:response", "coop2.interaction.responded", "actor:codex", "interaction:response"),
                event("evt:closed", "coop2.interaction.responded", "actor:claude"),
            ]), "actor:codex", "thread:test", "ws://test", self.state
        )
        with patch.object(watcher, "queue") as queue:
            first = watcher.step()
            second = watcher.step()
        self.assertEqual(first["queued_events"], ["evt:response"])
        self.assertEqual(second["queued_events"], [])
        self.assertEqual(queue.call_count, 1)

    def test_first_start_queues_open_requests_but_not_historical_responses(self) -> None:
        watcher = CodexQueueWatcher(
            FakeRendezvous([
                event("evt:request", "coop2.interaction.requested", "actor:codex"),
                event("evt:response", "coop2.interaction.responded", "actor:codex", "interaction:older"),
            ]), "actor:codex", "thread:test", "ws://test", self.state
        )
        with patch.object(watcher, "queue") as queue:
            result = watcher.step()
            second = watcher.step()
        self.assertEqual(result["queued_events"], ["evt:request"])
        self.assertEqual(second["queued_events"], [])
        self.assertEqual(queue.call_count, 1)

    def test_watcher_queues_an_open_probe_and_its_acknowledgement(self) -> None:
        probe = {"event_id": "evt:probe", "kind": "coop2.tickle.sent", "payload": {"tickle_id": "tickle:one", "recipient": "actor:codex"}}
        watcher = CodexQueueWatcher(FakeRendezvous([probe]), "actor:codex", "thread:test", None, self.state)
        with patch.object(watcher, "queue") as queue:
            first = watcher.step()
        self.assertEqual(first["queued_events"], ["evt:probe"])
        queue.assert_called_once_with(probe)

        acknowledgement = {"event_id": "evt:ack", "kind": "coop2.tickle.acked", "payload": {"tickle_id": "tickle:one", "recipient": "actor:codex"}}
        acknowledged = CodexQueueWatcher(FakeRendezvous([acknowledgement]), "actor:codex", "thread:test", None, self.state)
        with patch.object(acknowledged, "queue") as queue:
            result = acknowledged.step()
        self.assertEqual(result["queued_events"], ["evt:ack"])
        queue.assert_called_once_with(acknowledgement)

    def test_concurrent_watchers_claim_an_event_only_once(self) -> None:
        watchers = [
            CodexQueueWatcher(
                FakeRendezvous([event("evt:request", "coop2.interaction.requested", "actor:codex")]),
                "actor:codex", "thread:test", "ws://test", self.state
            )
            for _ in range(2)
        ]
        calls: list[str] = []
        for watcher in watchers:
            watcher.queue = lambda item: calls.append(item["event_id"])
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda watcher: watcher.step(), watchers))
        self.assertEqual(sum(len(result["queued_events"]) for result in results), 1)
        self.assertEqual(calls, ["evt:request"])

    def test_queue_failure_is_recorded_and_event_remains_retryable(self) -> None:
        watcher = CodexQueueWatcher(
            FakeRendezvous([event("evt:request", "coop2.interaction.requested", "actor:codex")]),
            "actor:codex", "thread:test", "ws://test", self.state
        )
        with patch.object(watcher, "queue", side_effect=subprocess.TimeoutExpired("codex", 30)):
            result = watcher.step()
        self.assertEqual(result["queued_events"], [])
        self.assertEqual(result["failed_events"], ["evt:request"])
        state = watcher._state()
        self.assertEqual(state["delivery_state"], "unavailable")
        self.assertEqual(state["last_failed_event"], "evt:request")
        self.assertNotIn("evt:request", state.get("notified_events", []))

    def test_local_queue_omits_dead_remote_endpoint(self) -> None:
        watcher = CodexQueueWatcher(FakeRendezvous([]), "actor:codex", "thread:test", None, self.state)
        with patch("tools.awp_codex_wake.subprocess.run") as run:
            watcher.queue(event("evt:request", "coop2.interaction.requested", "actor:codex"))
        command = run.call_args.args[0]
        self.assertIn("queue", command)
        self.assertIn("--thread", command)
        self.assertNotIn("--remote", command)

    def test_new_session_generation_retires_old_watcher(self) -> None:
        control = Path(self.temporary.name) / "control.json"
        atomic_json(control, {"generation": "new", "desired_state": "running"})
        self.assertTrue(control_is_current(control, "new"))
        self.assertFalse(control_is_current(control, "old"))
        atomic_json(control, {"generation": "new", "desired_state": "stopped"})
        self.assertFalse(control_is_current(control, "new"))

    def test_notification_cursor_is_bounded_and_keeps_recent_unique_ids(self) -> None:
        identifiers = [f"evt:{index}" for index in range(MAX_NOTIFIED_EVENTS + 20)]
        bounded = bounded_event_ids(["evt:0", *identifiers, "evt:20"])
        self.assertEqual(len(bounded), MAX_NOTIFIED_EVENTS)
        self.assertEqual(bounded[0], "evt:21")
        self.assertEqual(bounded[-1], "evt:20")


if __name__ == "__main__":
    unittest.main()
