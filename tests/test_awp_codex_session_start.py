from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.awp_codex_session_start import (
    HOOK_EVENT,
    ROLE_ACTOR,
    actor_for_session,
    bootstrap_command,
    run_hook,
)


class CodexSessionStartHookTests(unittest.TestCase):
    def test_actor_is_stable_per_session_and_not_the_raw_session_id(self) -> None:
        actor = actor_for_session("thread:one")
        self.assertEqual(actor, actor_for_session("thread:one"))
        self.assertNotIn("thread:one", actor)
        self.assertNotEqual(actor, actor_for_session("thread:two"))

    def test_hook_enters_with_codex_session_as_queue_thread(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            project.joinpath(".awp.json").write_text("{}", encoding="utf-8")
            calls = []

            class Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            def runner(*args, **kwargs):
                calls.append((args, kwargs))
                return Completed()

            result = run_hook(
                {"hook_event_name": HOOK_EVENT, "session_id": "thread:current", "cwd": str(project)},
                runner=runner,
            )

        command = calls[0][0][0]
        self.assertEqual(command, bootstrap_command(project, "thread:current"))
        self.assertIn("enter", command)
        self.assertIn(ROLE_ACTOR, command)
        self.assertIn(ROLE_ACTOR, result["hookSpecificOutput"]["additionalContext"])
        self.assertIn(actor_for_session("thread:current"), result["hookSpecificOutput"]["additionalContext"])

    def test_non_awp_directory_is_a_safe_noop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_hook(
                {"hook_event_name": HOOK_EVENT, "session_id": "thread:current", "cwd": directory}
            )
        self.assertIn("outside an AWP project", result["hookSpecificOutput"]["additionalContext"])

    def test_project_hook_configuration_is_valid_and_uses_session_start(self) -> None:
        hook_file = Path(__file__).resolve().parents[1] / ".codex" / "hooks.json"
        configuration = json.loads(hook_file.read_text(encoding="utf-8"))
        session_start = configuration["hooks"]["SessionStart"][0]
        handler = session_start["hooks"][0]
        self.assertEqual(session_start["matcher"], "^(startup|resume)$")
        # Some Codex releases skip async command hooks entirely, which left the
        # doorbell unarmed after every fresh start; activation must run
        # synchronously within its timeout.
        self.assertFalse(handler.get("async", False))
        self.assertGreaterEqual(handler["timeout"], 30)
        self.assertIn("awp_agent_start.py", handler["command"])
        self.assertIn("awp_agent_start.py", handler["commandWindows"])
        self.assertIn("--host codex", handler["command"])
        receipt = configuration["hooks"]["UserPromptSubmit"][0]["hooks"][0]
        self.assertIn("awp_prompt_receipt.py", receipt["command"])
        self.assertIn("awp_prompt_receipt.py", receipt["commandWindows"])
        self.assertFalse(receipt.get("async", False))


if __name__ == "__main__":
    unittest.main()
