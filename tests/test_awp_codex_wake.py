from __future__ import annotations

import tempfile
import unittest
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from tools.awp_codex_wake import CodexQueueWatcher, atomic_json


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


if __name__ == "__main__":
    unittest.main()
