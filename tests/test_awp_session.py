from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.awp_session import (
    PROFILE,
    control_path,
    main,
    process_is_running,
    session_status,
    thread_id,
    watcher_state_path,
    watcher_command,
)
from tools.awp_coordination import CoordinationError


class SessionBootstrapTests(unittest.TestCase):
    def test_thread_identity_comes_from_current_codex_session(self) -> None:
        self.assertEqual(thread_id(None, {"CODEX_THREAD_ID": "thread:current"}), "thread:current")
        self.assertEqual(thread_id("thread:explicit", {}), "thread:explicit")
        self.assertIsNone(thread_id(None, {}))

    def test_watcher_command_uses_generic_supervisor_and_host(self) -> None:
        project = Path("project")
        local = watcher_command(project, Path("ledger"), "actor:codex", "thread:test", "generation", 5.0, None)
        self.assertIn("tools.awp_supervisor", local)
        self.assertIn("--host", local)
        self.assertIn("codex", local)
        claude = watcher_command(project, Path("ledger"), "actor:claude", "session:test", "generation", 5.0, None, "claude")
        self.assertIn("claude", claude)

    def test_two_actors_have_isolated_control_and_cursor_paths(self) -> None:
        project = Path("project")
        first_control = control_path(project, "actor:one")
        second_control = control_path(project, "actor:two")
        self.assertNotEqual(first_control, second_control)
        self.assertNotEqual(
            watcher_state_path(project, "actor:one"),
            watcher_state_path(project, "actor:two"),
        )
        first = watcher_command(project, Path("ledger"), "actor:one", "thread:one", "one", 5.0, None)
        second = watcher_command(project, Path("ledger"), "actor:two", "thread:two", "two", 5.0, None)
        self.assertIn("tools.awp_supervisor", first)
        self.assertIn("tools.awp_supervisor", second)

    def test_status_requires_process_and_observed_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            project.joinpath(".awp-runtime").mkdir()
            with patch("tools.awp_session.Rendezvous") as rendezvous, patch(
                "tools.awp_session.process_is_running", return_value=False
            ):
                rendezvous.return_value.participant_watchers.return_value = [
                    {"actor": "actor:codex", "watcher_liveness": "active"}
                ]
                status = session_status(project, Path("ledger"), "actor:codex")
            self.assertEqual(status["state"], "unavailable")
            self.assertEqual(status["diagnostic"], "AWP-SIGNAL-UNVERIFIED")

    def test_current_process_is_detectable(self) -> None:
        self.assertTrue(process_is_running(os.getpid()))

    def test_windows_liveness_never_signals_the_process(self) -> None:
        with patch("tools.awp_session.os.name", "nt"), patch(
            "tools.awp_session._windows_process_is_running", return_value=True
        ) as windows_check, patch("tools.awp_session.os.kill") as kill:
            self.assertTrue(process_is_running(1234))
        windows_check.assert_called_once_with(1234)
        kill.assert_not_called()

    def test_start_reports_ledger_unavailable_instead_of_raising(self) -> None:
        stdout = io.StringIO()
        with patch(
            "tools.awp_session.start_watcher",
            side_effect=CoordinationError("read-only ledger fallback is unsafe while a WAL sidecar exists"),
        ), contextlib.redirect_stdout(stdout):
            exit_code = main(["start", "--thread", "thread:test"])

        self.assertEqual(exit_code, 2)
        output = stdout.getvalue()
        self.assertIn("AWP-COORD-LEDGER-UNAVAILABLE", output)
        self.assertIn("read-only ledger fallback is unsafe", output)


if __name__ == "__main__":
    unittest.main()
