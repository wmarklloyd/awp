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

    def test_start_declares_the_live_session_and_attaches_to_one_relay(self) -> None:
        from tools.awp_session import start_watcher

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with patch("tools.awp_session.Rendezvous") as rendezvous, patch(
                "tools.awp_session.CLIResumeAdapter"
            ) as adapter, patch("tools.awp_session.awp_relay.declare_live_session",
                                return_value={"binding": {"binding_id": "wake:1", "event_id": "evt:1"}}) as declare, patch(
                "tools.awp_session.awp_relay.ensure", return_value={"state": "started", "status": {"generation": "g"}}
            ) as ensure, patch("tools.awp_session._watcher_row",
                               return_value={"actor": "actor:codex", "watcher_liveness": "active", "last_seen": "2999-01-01T00:00:00Z"}):
                adapter.return_value.probe.return_value = {"state": "accepted"}
                result = start_watcher(project, Path("ledger"), "actor:codex", "thread:t")
            self.assertEqual(result["state"], "active")
            self.assertEqual(result["control"]["binding_id"], "wake:1")
            declare.assert_called_once_with(rendezvous.return_value, "actor:codex", "codex", "thread:t", None)
            ensure.assert_called_once()

    def test_relaunched_legacy_supervisor_declares_and_defers_to_a_live_relay(self) -> None:
        from tools import awp_relay
        from tools.awp_supervisor import parser as supervisor_parser

        args = supervisor_parser().parse_args(["--project", ".", "--actor", "actor:codex", "--host", "codex",
                                               "--session-ref", "thread:t", "--generation", "g"])
        with patch("tools.awp_relay.Rendezvous") as rendezvous, patch(
            "tools.awp_relay.declare_live_session"
        ) as declare, patch("tools.awp_relay.relay_status", return_value={"live": True}), patch(
            "tools.awp_relay.run_loop"
        ) as loop:
            self.assertEqual(awp_relay.adopt_legacy(args), 0)
        declare.assert_called_once_with(rendezvous.return_value, "actor:codex", "codex", "thread:t")
        loop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
