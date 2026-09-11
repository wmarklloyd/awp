from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.awp_activation import activation_result
from tools.awp_supervisor import Supervisor


class FakeLedger:
    def __init__(self, events): self.events = events
    def binding_id(self): return "binding:test"
    def refresh(self, workstate_id): return {"frontier": [self.events[-1]["event_id"]] if self.events else []}
    def events_after(self, workstate_id, cursor=0, limit=256):
        events = [dict(item, _ledger_sequence=index + 1) for index, item in enumerate(self.events) if index + 1 > cursor][:limit]
        return {"cursor": cursor, "next_cursor": events[-1]["_ledger_sequence"] if events else cursor,
                "has_more": False, "events": events}


class FakeRendezvous:
    project_id = "project:test"; workstate_id = "workstate:test"
    def __init__(self, events): self.ledger = FakeLedger(events); self.receipts = []
    def _events(self): return self.ledger.events
    def _append(self, actor, kind, payload):
        receipt = {"event_id": f"receipt:{len(self.receipts)}", "kind": kind, "payload": payload}
        self.receipts.append(receipt); return receipt
    def tickle_ack(self, actor, tickle_id):
        receipt = {"event_id": f"ack:{tickle_id}"}
        self.receipts.append({"event_id": receipt["event_id"], "kind": "coop2.tickle.acked",
                              "payload": {"tickle_id": tickle_id, "sender": actor}})
        return {"tickle_id": tickle_id, "publication": "confirmed", "receipt": receipt}
    def heartbeat(self, actor, profile): return {"last_seen": "now", "path": "heartbeat"}


class Adapter:
    def __init__(self, state="accepted"): self.state = state; self.calls = []
    def deliver(self, envelope): self.calls.append(envelope); return activation_result(self.state)
    def probe(self): return activation_result("accepted")


def tickle(index: int, recipient="actor:test"):
    return {"event_id": f"evt:{index}", "kind": "coop2.tickle.sent",
            "payload": {"tickle_id": f"tickle:{index}", "recipient": recipient}}


class SupervisorTests(unittest.TestCase):
    def test_replays_more_than_signal_ref_retention_with_immediate_acknowledgements(self):
        with tempfile.TemporaryDirectory() as directory:
            rendezvous = FakeRendezvous([tickle(index) for index in range(40)])
            adapter = Adapter(); supervisor = Supervisor(rendezvous, "actor:test", "fake", "session", "generation",
                                                          adapter, Path(directory) / "state.json")
            result = supervisor.step(limit=100)
        self.assertEqual(len(result["acknowledged"]), 40)
        self.assertEqual(result["cursor"], 40)
        self.assertEqual(adapter.calls, [])
        self.assertTrue(all(item["kind"] == "coop2.tickle.acked" for item in rendezvous.receipts))

    def test_cursor_does_not_advance_past_unavailable_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            rendezvous = FakeRendezvous([{
                "event_id": "evt:0", "kind": "coop2.interaction.requested",
                "payload": {"interaction_id": "interaction:0", "recipient": "actor:test"},
            }])
            supervisor = Supervisor(rendezvous, "actor:test", "fake", "session", "generation",
                                    Adapter("unavailable"), Path(directory) / "state.json")
            result = supervisor.step()
        self.assertEqual(result["cursor"], 0)
        self.assertEqual(result["unavailable"], ["evt:0"])

    def test_delivers_tickle_acknowledgement_to_the_sender_endpoint(self):
        acknowledgement = {
            "event_id": "evt:ack", "kind": "coop2.tickle.acked",
            "payload": {"tickle_id": "tickle:one", "recipient": "actor:test"},
        }
        with tempfile.TemporaryDirectory() as directory:
            rendezvous = FakeRendezvous([acknowledgement])
            adapter = Adapter()
            result = Supervisor(rendezvous, "actor:test", "fake", "session", "generation",
                                adapter, Path(directory) / "state.json").step()
        self.assertEqual(result["delivered"], ["evt:ack"])
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(rendezvous.receipts[0]["kind"], "coop2.tickle.ack.transport_queued")


if __name__ == "__main__":
    unittest.main()
