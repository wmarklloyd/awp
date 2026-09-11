from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from tools.awp_activation import delivery_message
from tools.awp_prompt_receipt import handle, parse_notice
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


if __name__ == "__main__":
    unittest.main()
