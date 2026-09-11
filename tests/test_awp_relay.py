from __future__ import annotations

from datetime import timedelta
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error

from tools import awp_wake as wake
from tools.awp_activation import activation_result
from tools.awp_git_ledger import PROFILE as GIT_PROFILE
from tools.awp_relay import RELAY_ACTOR, Relay
import tests.test_awp_coop2 as coop2_tests


class FakeAdapter:
    def __init__(self, state: str = "accepted") -> None:
        self.state = state
        self.calls: list[list[dict]] = []

    def deliver_many(self, envelopes):
        self.calls.append(list(envelopes))
        return activation_result(self.state, receipt="fake" if self.state == "accepted" else None,
                                 reason=None if self.state == "accepted" else "fake failure")


class RelayFixture(coop2_tests.RendezvousFixture):
    def setUp(self) -> None:
        self._env = mock.patch.dict(os.environ, {"AWP_COOP2_LEDGER": GIT_PROFILE, "AWP_RELAY_ID": "relay:test"})
        self._env.start()
        super().setUp()
        self.rendezvous.join("actor:codex", [], observation="on-entry-only")
        self.rendezvous.join("actor:claude", [], observation="on-entry-only")
        self.adapters: dict[str, FakeAdapter] = {}
        self.offset = timedelta(0)
        self.relay = Relay(self.rendezvous, "relay:test", self.project / ".awp-runtime" / "relay-state.json",
                           adapter_factory=self.adapter, clock=lambda: wake.utc_now() + self.offset)

    def tearDown(self) -> None:
        super().tearDown()
        self._env.stop()

    def adapter(self, binding):
        return self.adapters.setdefault(binding["binding_id"], FakeAdapter())

    def declare(self, actor: str, wake_class: str, adapter: str, **extra):
        return wake.declare(self.rendezvous, actor, wake_class, adapter, **extra)["binding"]

    def settle(self, steps: int = 3) -> list[dict]:
        return [self.relay.step() for _ in range(steps)]

    def relay_events(self, kind: str | None = None) -> list[dict]:
        return [event for event in self.rendezvous._events()
                if event["actor"] == RELAY_ACTOR and (kind is None or event["kind"] == kind)]

    def ingress(self, actor: str, event_id: str, via: str = "host-prompt-hook") -> dict:
        return self.relay._handle_request({"actor": actor, "event_id": event_id, "via": via,
                                           "evidence": {"session_id": "s1"}})


class DeclarationTests(RelayFixture):
    def test_secrets_are_references_and_credential_values_are_refused(self) -> None:
        with self.assertRaises(wake.WakeError):
            self.declare("actor:claude", "W3", "claude-routine", secret_ref="sk-ant-oat01-abc")
        with self.assertRaises(wake.WakeError):
            self.declare("actor:claude", "W3", "claude-routine", params={"routine_id": "sk-ant-oat01-abc"})
        with self.assertRaises(wake.WakeError):
            self.declare("actor:claude", "W3", "claude-routine", secret_ref="file:/etc/passwd")
        binding = self.declare("actor:claude", "W3", "claude-routine", params={"routine_id": "trig_123"},
                               secret_ref="file:~/.awp/secrets/claude-routine")
        self.assertEqual(binding["relay"], "relay:test")
        again = wake.declare(self.rendezvous, "actor:claude", "W3", "claude-routine", params={"routine_id": "trig_123"},
                             secret_ref="file:~/.awp/secrets/claude-routine")
        self.assertTrue(again["deduplicated"])
        wake.retire(self.rendezvous, "actor:claude", binding["binding_id"])
        self.assertEqual(wake.active_bindings(self.rendezvous._events()), {})

    def test_only_the_participant_may_declare_or_retire_its_bindings(self) -> None:
        binding = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "t1"})
        with self.assertRaises(wake.WakeError):
            wake.retire(self.rendezvous, "actor:claude", binding["binding_id"])
        # A declaration published by another actor is ignored.
        payload = dict(binding); payload.pop("event_id"); payload.pop("declared_at", None)
        self.rendezvous._append("actor:claude", wake.DECLARED, payload | {"adapter": "codex-exec", "class": "W2",
                                                                          "binding_id": "wake:forged"})
        self.assertNotIn("wake:forged", wake.active_bindings(self.rendezvous._events()))

    def test_local_profiles_come_from_relay_config_not_the_ledger(self) -> None:
        binding = self.declare("actor:claude", "W2", "my-agent")
        with self.assertRaises(wake.WakeError):
            wake.adapter_for(binding, self.project, wake.local_profiles(self.project, home=self.project))
        wake.register_local_command(self.project, "my-agent", "W2", ["my-agent", "--prompt", "{prompt}"], kind="headless")
        adapter = wake.adapter_for(binding, self.project, wake.local_profiles(self.project, home=self.project))
        self.assertIsInstance(adapter, wake.HeadlessAdapter)


class LadderTests(RelayFixture):
    def test_declaration_is_probed_and_reach_is_measured(self) -> None:
        binding = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "t1"})
        self.assertEqual(wake.reach(self.rendezvous._events())["participants"]["actor:codex"]["best"]["state"],
                         "declared-unverified")
        self.settle()
        probe = next(event for event in self.rendezvous._events() if event["kind"] == "coop2.tickle.sent")
        self.assertEqual(probe["actor"], RELAY_ACTOR)
        self.assertEqual(probe["payload"]["probe_binding"], binding["binding_id"])
        self.assertEqual(len(self.adapters[binding["binding_id"]].calls), 1)
        self.ingress("actor:codex", probe["event_id"])
        self.settle(1)
        row = wake.reach(self.rendezvous._events())["participants"]["actor:codex"]
        self.assertEqual(row["best"], {"rung": "W1", "binding_id": binding["binding_id"], "state": "wake-verified"})
        self.assertEqual(row["bindings"][0]["acknowledged_via"], "host-prompt-hook")
        # The relay never records a recipient receipt itself.
        self.assertFalse([e for e in self.relay_events() if e["kind"] in {"coop2.tickle.acked", "coop2.interaction.observed"}])

    def test_no_receipt_within_window_escalates_to_the_next_binding(self) -> None:
        live = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "t1"})
        headless = self.declare("actor:codex", "W2", "codex-exec")
        self.settle()  # probes both declarations
        sent = self.rendezvous.send("actor:claude", "actor:codex", "review", "s", "q?", "actor:claude", 1, 4, 1200, 300, 600)
        event_id = sent["receipt"]["event_id"]
        self.settle(1)
        transports = [e for e in self.relay_events("coop2.interaction.transport_queued") if e["payload"]["event_id"] == event_id]
        self.assertEqual([e["payload"]["wake_class"] for e in transports], ["W1"])
        self.offset = timedelta(seconds=live["ack_window_seconds"] + 10)
        self.settle(1)
        escalated = [e for e in self.relay_events(wake.ESCALATED) if e["payload"]["event_id"] == event_id]
        self.assertEqual(escalated[0]["payload"]["binding_id"], live["binding_id"])
        transports = [e for e in self.relay_events("coop2.interaction.transport_queued") if e["payload"]["event_id"] == event_id]
        self.assertEqual([e["payload"]["wake_class"] for e in transports], ["W1", "W2"])
        self.ingress("actor:codex", event_id, via="host-launch")
        self.settle(1)
        result = wake.outcome(self.rendezvous._events(), event_id)
        self.assertEqual(result["state"], "received")
        self.assertIn("host-launch", [row["via"] for row in result["trail"]])
        self.assertEqual(self.relay.state()["jobs"][event_id]["state"], "received")
        self.assertEqual(headless["class"], "W2")

    def test_failing_binding_trips_the_breaker_and_is_disclosed(self) -> None:
        live = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "gone"})
        self.adapters[live["binding_id"]] = FakeAdapter("deferred")
        self.settle()
        for index in range(3):
            self.rendezvous.send("actor:claude", "actor:codex", "review", f"s{index}", "q?", "actor:claude", 1, 4, 1200, 300, 600)
            self.settle(1)
        suspended = self.relay_events(wake.SUSPENDED)
        self.assertEqual(len(suspended), 1)
        self.assertEqual(suspended[0]["payload"]["binding_id"], live["binding_id"])
        calls = len(self.adapters[live["binding_id"]].calls)
        sent = self.rendezvous.send("actor:claude", "actor:codex", "review", "later", "q?", "actor:claude", 1, 4, 1200, 300, 600)
        self.settle(1)
        self.assertEqual(len(self.adapters[live["binding_id"]].calls), calls)  # skipped, not tried
        reasons = [e["payload"]["reason"] for e in self.relay_events(wake.ESCALATED)
                   if e["payload"]["event_id"] == sent["receipt"]["event_id"]]
        self.assertTrue(any(reason.startswith("skipped: binding suspended") for reason in reasons))
        self.assertEqual(wake.reach(self.rendezvous._events())["participants"]["actor:codex"]["bindings"][0]["suspended"][:1], "3")
        # A later probe through the binding that succeeds resumes it.
        self.adapters[live["binding_id"]].state = "accepted"
        with mock.patch("tools.awp_relay.PROBE_BACKOFF_SECONDS", 0):
            self.settle(2)
        probes = [e for e in self.rendezvous._events() if e["kind"] == "coop2.tickle.sent"
                  and e["payload"].get("probe_binding") == live["binding_id"]]
        self.assertGreaterEqual(len(probes), 2)
        self.ingress("actor:codex", probes[1]["event_id"])
        self.settle(1)
        self.assertEqual(len(self.relay_events(wake.RESUMED)), 1)

    def test_exhausted_ladder_notifies_principal_or_discloses_entry_only(self) -> None:
        sent = self.rendezvous.send("actor:codex", "actor:claude", "review", "s", "q?", "actor:codex", 1, 4, 1200, 300, 600)
        self.settle(1)
        outcome = wake.outcome(self.rendezvous._events(), sent["receipt"]["event_id"])
        self.assertEqual(outcome["state"], "entry-only")
        notify = self.declare("actor:claude", "W5", "desktop-notify")
        second = self.rendezvous.send("actor:codex", "actor:claude", "review", "s2", "q?", "actor:codex", 1, 4, 1200, 300, 600)
        self.settle(1)
        self.assertEqual(wake.outcome(self.rendezvous._events(), second["receipt"]["event_id"])["state"], "principal-notified")
        self.assertEqual(len(self.adapters[notify["binding_id"]].calls), 1)

    def test_parked_item_is_woken_when_a_live_session_is_declared(self) -> None:
        sent = self.rendezvous.send("actor:claude", "actor:codex", "review", "s", "q?", "actor:claude", 1, 4, 1200, 300, 600)
        self.settle(1)
        live = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "new"})
        self.settle(2)
        delivered = [call[0]["event_id"] for call in self.adapters[live["binding_id"]].calls]
        self.assertIn(sent["receipt"]["event_id"], delivered)

    def test_hosted_wakes_coalesce_and_respect_budget(self) -> None:
        hosted = self.declare("actor:claude", "W3", "claude-routine", params={"routine_id": "trig_1"},
                              secret_ref="env:AWP_TEST_TOKEN", budget={"runs": 2, "per_seconds": 3600})
        self.settle()  # the declaration probe uses one run
        first = self.rendezvous.send("actor:codex", "actor:claude", "review", "a", "q?", "actor:codex", 1, 4, 1200, 300, 600)
        second = self.rendezvous.send("actor:codex", "actor:claude", "review", "b", "q?", "actor:codex", 1, 4, 1200, 300, 600)
        self.settle(1)
        self.assertEqual(len(self.adapters[hosted["binding_id"]].calls), 1)  # waiting to coalesce
        self.offset = timedelta(seconds=10)
        self.settle(1)
        calls = self.adapters[hosted["binding_id"]].calls
        self.assertEqual(len(calls), 2)
        self.assertEqual(sorted(e["event_id"] for e in calls[1]),
                         sorted([first["receipt"]["event_id"], second["receipt"]["event_id"]]))
        third = self.rendezvous.send("actor:codex", "actor:claude", "review", "c", "q?", "actor:codex", 1, 4, 1200, 300, 600)
        self.offset = timedelta(seconds=30)
        self.settle(1)
        self.assertEqual(len(calls), 2)  # budget of two runs per hour is spent
        reasons = [e["payload"]["reason"] for e in self.relay_events(wake.ESCALATED)
                   if e["payload"]["event_id"] == third["receipt"]["event_id"]]
        self.assertTrue(reasons and reasons[0].startswith("skipped: budget exhausted"))

    def test_binding_for_another_relay_is_never_executed(self) -> None:
        other = self.declare("actor:codex", "W2", "codex-exec", relay="relay:elsewhere")
        self.rendezvous.send("actor:claude", "actor:codex", "review", "s", "q?", "actor:claude", 1, 4, 1200, 300, 600)
        self.settle()
        self.assertNotIn(other["binding_id"], self.adapters)
        self.assertEqual(self.relay_events(wake.OUTCOME), [])  # the other relay owns the outcome

    def test_first_start_does_not_rewake_old_items(self) -> None:
        self.rendezvous.send("actor:claude", "actor:codex", "review", "old", "q?", "actor:claude", 1, 4, 1200, 300, 600)
        live = self.declare("actor:codex", "W1", "codex-queue", params={"session_ref": "t"})
        self.offset = timedelta(hours=2)
        self.settle()
        delivered = [call[0]["event_kind"] for call in self.adapters.get(live["binding_id"], FakeAdapter()).calls]
        self.assertNotIn("coop2.interaction.requested", delivered)
        jobs = [job for job in self.relay.state()["jobs"].values() if job["event_kind"] == "coop2.interaction.requested"]
        self.assertTrue(jobs and jobs[0].get("historical"))


class AdapterTests(unittest.TestCase):
    def envelope(self, event_id: str = "evt:1") -> dict:
        return {"type": "cooperation_activation_envelope", "module": "urn:awp:cooperation",
                "profile": "awp-host-activation-v1", "operation_id": "op", "binding_id": "b", "project_id": "p",
                "workstate_id": "w", "recipient_actor": "actor:claude", "route_id": "wake:x", "route_generation": "g",
                "event_id": event_id, "event_kind": "coop2.interaction.requested", "interaction_id": "interaction:1",
                "ledger_frontier": []}

    def test_routine_adapter_posts_identifiers_with_a_referenced_token(self) -> None:
        seen = {}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"type": "routine_fire", "claude_code_session_id": "session_01X"}).encode()

        def opener(request, timeout):
            seen.update(url=request.full_url, headers=dict(request.header_items()), body=json.loads(request.data))
            return Response()

        binding = {"binding_id": "wake:x", "params": {"routine_id": "trig_abc"}, "secret_ref": "env:AWP_TOKEN"}
        adapter = wake.RoutineAdapter(binding, environment={"AWP_TOKEN": "sk-ant-oat01-secret"}, opener=opener)
        result = adapter.deliver_many([self.envelope()])
        self.assertEqual(result["state"], "accepted")
        self.assertEqual(result["endpoint_receipt"], "session_01X")
        self.assertEqual(seen["url"], "https://api.anthropic.com/v1/claude_code/routines/trig_abc/fire")
        self.assertEqual(seen["headers"]["Anthropic-beta"], wake.ROUTINE_BETA)
        self.assertIn("evt:1", seen["body"]["text"])
        self.assertNotIn("secret", json.dumps(result))

    def test_routine_adapter_reports_missing_secret_and_rate_limits(self) -> None:
        binding = {"binding_id": "wake:x", "params": {"routine_id": "trig_abc"}, "secret_ref": "env:AWP_TOKEN"}
        self.assertEqual(wake.RoutineAdapter(binding, environment={}).deliver(self.envelope())["state"], "unavailable")

        def limited(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, "limit", {"Retry-After": "60"}, None)

        adapter = wake.RoutineAdapter(binding, environment={"AWP_TOKEN": "t"}, opener=limited)
        result = adapter.deliver(self.envelope())
        self.assertEqual(result["state"], "deferred")
        self.assertIn("429", result["reason"])

    def test_secret_files_are_confined_to_the_awp_secrets_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / ".awp" / "secrets").mkdir(parents=True)
            (home / ".awp" / "secrets" / "token").write_text("value\n", encoding="utf-8")
            self.assertEqual(wake.resolve_secret("file:~/.awp/secrets/token", home=home), "value")
            with self.assertRaises(wake.WakeError):
                wake.resolve_secret("file:~/.awp/secrets/../x", home=home)

    def test_headless_adapter_launches_the_runner_with_the_notice(self) -> None:
        launched = []
        with tempfile.TemporaryDirectory() as directory, mock.patch("tools.awp_wake.shutil.which", return_value="/bin/agent"):
            project = Path(directory)
            adapter = wake.HeadlessAdapter(project, {"binding_id": "wake:h", "actor": "actor:claude"},
                                           ["agent", "-p", "{prompt}"], launcher=lambda *a, **k: launched.append((a, k)))
            result = adapter.deliver_many([self.envelope("evt:1"), self.envelope("evt:2")])
            self.assertEqual(result["state"], "accepted")
            spec_path = Path(launched[0][0][0][launched[0][0][0].index("--spec") + 1])
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        self.assertEqual(spec["events"], ["evt:1", "evt:2"])
        self.assertEqual(spec["command"][:2], ["/bin/agent", "-p"])
        self.assertIn("tools.awp_ingress --actor actor:claude --event evt:2", spec["command"][2])

    def test_headless_run_records_host_launch_only_on_success(self) -> None:
        from tools.awp_headless_run import run
        from tools.awp_request_spool import RequestSpool

        spec = {"run_id": "run:1", "binding_id": "wake:h", "actor": "actor:claude", "events": ["evt:1"], "command": ["x"]}
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            failed = run(project, spec, runner=lambda *a, **k: mock.Mock(returncode=1, stdout="", stderr="no"))
            self.assertEqual(failed["state"], "failed")
            self.assertEqual(list((project / ".awp-runtime").glob("requests/*/*.request")), [])
            done = run(project, spec, runner=lambda *a, **k: mock.Mock(returncode=0, stdout='{"session_id":"abc123"}', stderr=""))
            self.assertEqual(done["state"], "receipt-submitted")
            seen = []
            RequestSpool(project).process(lambda request: seen.append(request) or {"ok": True})
        self.assertEqual(seen[0]["via"], "host-launch")
        self.assertEqual(seen[0]["evidence"]["session_id"], "abc123")

    def test_notifier_always_logs_and_passes_text_out_of_band(self) -> None:
        calls = []
        with tempfile.TemporaryDirectory() as directory, mock.patch(
                "tools.awp_wake.desktop_notification_command", return_value=["notify"]):
            project = Path(directory)
            adapter = wake.NotifyAdapter(project, runner=lambda command, **kwargs: calls.append((command, kwargs)) or mock.Mock(returncode=0))
            result = adapter.deliver(self.envelope())
            log = (project / ".awp-runtime" / "notifications.log").read_text(encoding="utf-8")
        self.assertEqual(result["endpoint_receipt"], "desktop-notification")
        self.assertIn("actor:claude", log)
        self.assertEqual(calls[0][0], ["notify"])
        self.assertIn("actor:claude", calls[0][1]["env"]["AWP_NOTICE"])


if __name__ == "__main__":
    unittest.main()
