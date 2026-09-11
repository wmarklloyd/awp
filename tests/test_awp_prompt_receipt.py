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
