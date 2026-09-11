from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.awp_activation import CLIResumeAdapter, CommandAdapter, activation_result, validate_envelope
from tools.awp_agent_start import bootstrap_command, opaque_session_ref, run_hook
from tools.awp_request_spool import RequestSpool


def envelope() -> dict:
    return {
        "type": "cooperation_activation_envelope", "module": "urn:awp:cooperation",
        "profile": "awp-host-activation-v1",
        "operation_id": "op:one", "binding_id": "binding:one", "project_id": "project:one",
        "workstate_id": "workstate:one", "recipient_actor": "actor:test", "route_id": "route:one",
        "route_generation": "generation:one", "event_id": "evt:one", "event_kind": "coop2.tickle.sent",
        "ledger_frontier": ["evt:one"],
    }


class ActivationContractTests(unittest.TestCase):
    def test_envelope_requires_correlation_fields(self) -> None:
        self.assertEqual(validate_envelope(envelope())["event_id"], "evt:one")
        with self.assertRaises(ValueError):
            validate_envelope({"event_id": "evt:one"})

    def test_command_adapter_is_json_and_identifier_only(self) -> None:
        calls = []
        class Completed:
            returncode = 0
            stdout = json.dumps(activation_result("accepted", receipt="endpoint:one"))
            stderr = ""
        def runner(*args, **kwargs):
            calls.append((args, kwargs)); return Completed()
        result = CommandAdapter(["adapter"], runner=runner).deliver(envelope())
        self.assertEqual(result["state"], "accepted")
        payload = json.loads(calls[0][1]["input"])
        self.assertEqual(payload["envelope"]["event_id"], "evt:one")
        self.assertNotIn("question", payload["envelope"])

    def test_codex_probe_uses_the_actual_queue_endpoint(self) -> None:
        calls = []
        class Completed:
            returncode = 0
            stdout = "queued"
            stderr = ""
        def runner(*args, **kwargs):
            calls.append((args, kwargs)); return Completed()
        result = CLIResumeAdapter("codex", "thread:test", command=["codex", "queue", "--thread", "thread:test", "--message"], runner=runner).probe()
        self.assertEqual(result["state"], "accepted")
        self.assertIn("activation probe", calls[0][0][0][-1])

    def test_tickle_acknowledgement_does_not_request_ingress(self) -> None:
        calls = []
        class Completed:
            returncode = 0
            stdout = "queued"
            stderr = ""
        def runner(*args, **kwargs):
            calls.append((args, kwargs)); return Completed()
        acknowledgement = envelope() | {"event_kind": "coop2.tickle.acked", "interaction_id": "tickle:one"}
        result = CLIResumeAdapter("codex", "thread:test", command=["codex", "queue"], runner=runner).deliver(acknowledgement)
        self.assertEqual(result["state"], "accepted")
        self.assertIn("tickle:one acknowledged", calls[0][0][0][-1])
        self.assertNotIn("awp_ingress", calls[0][0][0][-1])

    def test_generic_hook_uses_same_command_for_any_host(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory); project.joinpath(".awp.json").write_text("{}", encoding="utf-8")
            calls = []
            class Completed: returncode = 0; stdout = ""; stderr = ""
            def runner(*args, **kwargs): calls.append((args, kwargs)); return Completed()
            result = run_hook({"hook_event_name": "SessionStart", "session_id": "raw", "cwd": str(project)},
                              host="claude", runner=runner)
        command = calls[0][0][0]
        self.assertEqual(command, bootstrap_command(project, "claude", "actor:claude", "raw"))
        self.assertIn("awp_agent_start.py", str(Path(__file__).parents[1] / "tools" / "awp_agent_start.py"))
        self.assertNotIn("raw", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(opaque_session_ref("claude", "raw"), opaque_session_ref("claude", "raw"))

    def test_request_spool_is_idempotent_and_writes_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spool = RequestSpool(Path(directory))
            first = spool.submit("client", "operation", {"kind": "join"})
            self.assertEqual(first, spool.submit("client", "operation", {"kind": "join"}))
            with self.assertRaises(ValueError):
                spool.submit("client", "operation", {"kind": "different"})
            spool.process(lambda request: {"accepted": request["kind"]})
            self.assertEqual(spool.response("client", "operation")["result"], {"accepted": "join"})

    def test_claude_project_hook_uses_generic_entrypoint(self) -> None:
        path = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        command = value["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("awp_agent_start.py", command)
        self.assertIn("--host claude", command)


if __name__ == "__main__":
    unittest.main()
