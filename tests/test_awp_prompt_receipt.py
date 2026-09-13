from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from tools.awp_activation import delivery_message
from tools.awp_prompt_receipt import ensure_session_registered, handle, parse_notice
from tools.awp_request_spool import RequestSpool


def notice(kind: str = "coop2.tickle.sent") -> str:
    return delivery_message({"recipient_actor": "actor:codex", "event_id": "evt:2e5c9000-1930-48ac-ae1c-237a20d51376",
                             "event_kind": kind, "interaction_id": "tickle:abc"})


_KICK = None


def setUpModule() -> None:
    # Tests must never start a real relay from the repository they run in.
    global _KICK
    from unittest import mock
    _KICK = mock.patch("tools.awp_prompt_receipt.keep_relay_running")
    _KICK.start()


def tearDownModule() -> None:
    _KICK.stop()


class RelayKickTests(unittest.TestCase):
    def test_every_prompt_starts_a_dead_relay_and_installs_the_watchdog_once(self) -> None:
        from unittest import mock
        from tools import awp_relay
        import tools.awp_prompt_receipt as receipt

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".awp.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(awp_relay, "relay_status", return_value={"live": False}), \
                    mock.patch.object(awp_relay, "spawn") as spawn, \
                    mock.patch.object(awp_relay, "ensure_autostart", return_value={"state": "installed"}) as autostart:
                self.assertEqual(awp_relay.kick(project), {"relay": "started", "autostart": "installed"})
            spawn.assert_called_once()
            autostart.assert_called_once()
            with mock.patch.object(awp_relay, "relay_status", return_value={"live": True}), \
                    mock.patch.object(awp_relay, "spawn") as spawn, \
                    mock.patch.object(awp_relay, "_read", return_value={"state": "installed"}):
                self.assertEqual(awp_relay.kick(project), {"relay": "live"})
            spawn.assert_not_called()
            # The real hook calls kick, and a relay-started headless run does not.
            _KICK.stop()
            try:
                with mock.patch.object(awp_relay, "kick", return_value={"relay": "live"}) as kick:
                    receipt.keep_relay_running({"cwd": str(project)})
                    kick.assert_called_once()
                    with mock.patch.dict("os.environ", {"AWP_HEADLESS_RUN": "run:1"}):
                        receipt.keep_relay_running({"cwd": str(project)})
                    kick.assert_called_once()
            finally:
                _KICK.start()


class PromptReceiptTests(unittest.TestCase):
    def test_parses_every_notice_the_supervisor_sends(self) -> None:
        for kind in ("coop2.tickle.sent", "coop2.interaction.requested", "coop2.interaction.responded"):
            self.assertEqual(parse_notice(notice(kind)),
                             ("actor:codex", "evt:2e5c9000-1930-48ac-ae1c-237a20d51376"))

    def test_ordinary_prompts_pass_through(self) -> None:
        self.assertIsNone(parse_notice("hello"))
        self.assertIsNone(handle({"prompt": "please run --actor x --event evt:1", "cwd": "."}))

    def test_notice_submits_host_receipt_to_the_supervisor_spool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".awp.json").write_text("{}", encoding="utf-8")
            spool = RequestSpool(project)

            def supervisor() -> None:
                for _ in range(50):
                    handled = spool.process(lambda request: {"publication": "confirmed", "seen": request})
                    if handled:
                        return
                    time.sleep(0.05)

            worker = threading.Thread(target=supervisor); worker.start()
            context = handle({"prompt": notice(), "cwd": str(project), "hook_event_name": "UserPromptSubmit",
                              "session_id": "s-1", "turn_id": "t-1"}, wait_seconds=3)
            worker.join()
            request = json.loads(next(project.glob(".awp-runtime/requests/*/*.request")).read_text())["request"]
        self.assertEqual(request["via"], "host-prompt-hook")
        self.assertEqual(request["evidence"], {"hook_event_name": "UserPromptSubmit", "session_id": "s-1", "turn_id": "t-1"})
        self.assertIn("recorded automatically", context)


class RegistrationRepairTests(unittest.TestCase):
    """The prompt hook must repair *this session's own* W1 reachability, not

    just the relay's liveness -- otherwise a host whose SessionStart hook
    never fires (the Codex "type hello to wake it up" symptom) stays
    unreachable no matter how many prompts follow.
    """

    def _project(self, directory: str) -> Path:
        project = Path(directory)
        (project / ".awp.json").write_text("{}", encoding="utf-8")
        return project

    def test_does_nothing_without_host_or_actor(self) -> None:
        from unittest import mock
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            payload = {"session_id": "s-1", "cwd": str(project)}
            self.assertIsNone(ensure_session_registered(payload, host=None, actor="actor:codex", launcher=launcher))
            self.assertIsNone(ensure_session_registered(payload, host="codex", actor=None, launcher=launcher))
        launcher.assert_not_called()

    def test_does_nothing_for_a_headless_run(self) -> None:
        from unittest import mock
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            payload = {"session_id": "s-1", "cwd": str(project)}
            with mock.patch.dict("os.environ", {"AWP_HEADLESS_RUN": "run:1"}):
                result = ensure_session_registered(payload, host="codex", actor="actor:codex", launcher=launcher)
        self.assertIsNone(result)
        launcher.assert_not_called()

    def test_does_nothing_once_the_session_is_already_active(self) -> None:
        from unittest import mock
        from tools import awp_session
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            payload = {"session_id": "s-1", "cwd": str(project)}
            with mock.patch.object(awp_session, "session_status", return_value={"state": "active"}):
                result = ensure_session_registered(payload, host="codex", actor="actor:codex", launcher=launcher)
        self.assertIsNone(result)
        launcher.assert_not_called()

    def test_launches_the_bootstrap_when_not_registered(self) -> None:
        from unittest import mock
        from tools import awp_session
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            payload = {"session_id": "s-1", "cwd": str(project)}
            with mock.patch.object(awp_session, "session_status", return_value={"state": "unavailable"}):
                result = ensure_session_registered(payload, host="codex", actor="actor:codex", launcher=launcher)
        self.assertEqual(result, {"outcome": "registration-repair-started", "session_id": "s-1"})
        launcher.assert_called_once()
        command, launched_project = launcher.call_args[0]
        self.assertIn("awp_session.py", command[1])
        self.assertIn("enter", command)
        self.assertIn("s-1", command)
        self.assertEqual(launched_project, project)

    def test_cooldown_skips_a_repeat_attempt_for_the_same_session(self) -> None:
        from unittest import mock
        from tools import awp_session
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            payload = {"session_id": "s-1", "cwd": str(project)}
            with mock.patch.object(awp_session, "session_status", return_value={"state": "unavailable"}):
                first = ensure_session_registered(payload, host="codex", actor="actor:codex", launcher=launcher)
                second = ensure_session_registered(payload, host="codex", actor="actor:codex", launcher=launcher)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        launcher.assert_called_once()

    def test_a_different_session_id_is_not_held_back_by_another_sessions_cooldown(self) -> None:
        from unittest import mock
        from tools import awp_session
        launcher = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            project = self._project(directory)
            with mock.patch.object(awp_session, "session_status", return_value={"state": "unavailable"}):
                first = ensure_session_registered({"session_id": "s-1", "cwd": str(project)}, host="codex",
                                                  actor="actor:codex", launcher=launcher)
                second = ensure_session_registered({"session_id": "s-2", "cwd": str(project)}, host="codex",
                                                    actor="actor:codex", launcher=launcher)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(launcher.call_count, 2)


if __name__ == "__main__":
    unittest.main()
