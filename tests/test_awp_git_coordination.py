from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import tests.test_coordination_ledger as coop1_tests
from tools.awp_coordination import CoordinationError, CoordinationLedger
from tools.awp_git_coordination import GitCoordinationLedger, migrate

START = datetime(2026, 9, 4, 20, 0, tzinfo=timezone.utc)
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=cwd, check=True, capture_output=True, text=True, env=GIT_ENV).stdout


def repository(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if not (path / ".git").exists():
        (path / "README").write_text("x", encoding="utf-8")
        git(path, "init", "-q", "."); git(path, "add", "-A")
        git(path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")
    return path


def git_factory(path: Path, *, read_only: bool = False) -> GitCoordinationLedger:
    """Stand-in for CoordinationLedger(path): the same ledger, stored in Git."""
    return GitCoordinationLedger(repository(Path(path).parent))


SQLITE_ONLY = {"test_existing_ledger_can_be_opened_immutable_for_recovery_reads",
               "test_recovery_reads_committed_wal_pages",
               "test_binding_identity_is_stable_and_frontier_is_an_observation",
               "test_explicit_store_becomes_shared_after_two_distinct_lease_entries",
               "test_checkpoint_projection_rejects_stale_frontier_and_returns_matching_receipt"}


def _git_profile(case: type) -> type:
    """Rerun an existing COOP-1 test class with every ledger stored in Git."""
    def setUp(self) -> None:
        if self._testMethodName in SQLITE_ONLY:
            self.skipTest("exercises the SQLite file itself")
        self._factory = mock.patch.object(coop1_tests, "CoordinationLedger", side_effect=git_factory)
        self._factory.start()
        case.setUp(self)
        self.assertIsInstance(self.ledger, GitCoordinationLedger)

    def tearDown(self) -> None:
        if hasattr(self, "_factory"):
            self._factory.stop()
        if hasattr(self, "temporary"):
            case.tearDown(self)

    return type(f"Git{case.__name__}", (case,), {"setUp": setUp, "tearDown": tearDown})


GitCoordinationLedgerTests = _git_profile(coop1_tests.CoordinationLedgerTests)
GitStaleIntentDowngradeTests = _git_profile(coop1_tests.StaleIntentDowngradeTests)


class AtomicAnnounceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = repository(Path(self.temporary.name) / "p")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def announce(self, ledger: CoordinationLedger, actor: str, path: str = "src/app.py") -> dict:
        return ledger.begin(workstate_id="ws:1", project_id="repo:1", actor=actor, goal="g", summary="s",
                            base_revision="git:1", scopes=[("file", path)], policy="warn", at=START)

    def test_racing_announcements_never_both_pass(self) -> None:
        for round_number in range(5):
            path = f"src/file{round_number}.py"
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda n: self.announce(GitCoordinationLedger(self.project), f"actor:{n}", path), range(4)))
            clear = [r for r in results if r["advisory_status"] == "clear"]
            self.assertEqual(len(clear), 1, f"round {round_number}: exactly one announcement may pass")
            self.assertEqual(sorted(len(r["overlaps"]) for r in results)[0], 0)
        history = git(self.project, "rev-list", "--count", GitCoordinationLedger(self.project).ref()).strip()
        self.assertEqual(int(history), 20)  # one commit per announcement, one unbroken chain

    def test_records_must_be_replayable_from_events(self) -> None:
        ledger = GitCoordinationLedger(self.project)
        self.announce(ledger, "actor:a")
        with self.assertRaises(CoordinationError):
            with ledger._transaction() as connection:
                connection.execute("UPDATE records SET status = 'tampered'")
        self.assertEqual(GitCoordinationLedger(self.project).export_events("ws:1"), ledger.export_events("ws:1"))

    def test_reads_do_not_write(self) -> None:
        ledger = GitCoordinationLedger(self.project)
        self.announce(ledger, "actor:a")
        head = git(self.project, "rev-parse", ledger.ref()).strip()
        ledger.refresh("ws:1", at=START)
        ledger.export_events("ws:1")
        self.assertEqual(git(self.project, "rev-parse", ledger.ref()).strip(), head)


class TwoMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        source = repository(base / "src")
        self.remote = base / "shared.git"
        git(base, "clone", "-q", "--bare", str(source), str(self.remote))
        self.a, self.b = base / "a", base / "b"
        git(base, "clone", "-q", str(self.remote), str(self.a))
        git(base, "clone", "-q", str(self.remote), str(self.b))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_the_remote_serializes_announcements_from_two_machines(self) -> None:
        def announce(clone: Path, actor: str) -> dict:
            return GitCoordinationLedger(clone, remote="origin").begin(
                workstate_id="ws:1", project_id="repo:1", actor=actor, goal="g", summary="s",
                base_revision="git:1", scopes=[("file", "shared.py")], policy="warn", at=START)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda args: announce(*args), [(self.a, "actor:a"), (self.b, "actor:b")]))
        self.assertEqual(sorted(r["advisory_status"] for r in results), ["clear", "warn"])
        a_view = GitCoordinationLedger(self.a, remote="origin").export_events("ws:1")
        b_view = GitCoordinationLedger(self.b, remote="origin").export_events("ws:1")
        self.assertEqual(a_view, b_view)


class MigrationTests(unittest.TestCase):
    def test_sqlite_history_moves_into_git_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = repository(Path(directory) / "p")
            sqlite_path = Path(directory) / "coordination.sqlite3"
            source = CoordinationLedger(sqlite_path)
            lease = source.enter_lease(workstate_id="ws:1", project_id="repo:1", actor="actor:a",
                                       location=str(project), base_revision="git:1", intended_scopes=["src"], at=START)
            source.enter_lease(workstate_id="ws:1", project_id="repo:1", actor="actor:b",
                               location=str(project), base_revision="git:1", intended_scopes=["src"], at=START)
            first = source.begin(workstate_id="ws:1", project_id="repo:1", actor="actor:a", goal="g", summary="s",
                                 base_revision="git:1", scopes=[("file", "src/x.py")], policy="block", at=START,
                                 request_id="request:1", request_hash="h")
            second = source.begin(workstate_id="ws:1", project_id="repo:1", actor="actor:b", goal="g", summary="s",
                                  base_revision="git:1", scopes=[("file", "src/x.py")], policy="block", at=START)
            source.resolve_overlap(workstate_id="ws:1", overlap_id=second["overlaps"][0]["id"], actor="actor:b",
                                   disposition="order", reason="after a", at=START)
            source.scan("ws:1", "watcher:1", limit=3)
            result = migrate(project, sqlite_path)
            target = GitCoordinationLedger(project)
            self.assertEqual(target.export_events("ws:1"), source.export_events("ws:1"))
            self.assertEqual(target.binding_id(), source.binding_id())
            self.assertEqual(result["requests"], 1)
            # The idempotent request answers from history, and the scan cursor survived.
            again = target.begin(workstate_id="ws:1", project_id="repo:1", actor="actor:a", goal="g", summary="s",
                                 base_revision="git:1", scopes=[("file", "src/x.py")], policy="block", at=START,
                                 request_id="request:1", request_hash="h")
            self.assertEqual(again["intent"]["id"], first["intent"]["id"])
            self.assertEqual(target.scan("ws:1", "watcher:1")["previous_cursor"], source.scan("ws:1", "watcher:2", limit=3)["cursor"])
            self.assertIn(lease["lease"]["id"], [item["id"] for item in target.leases("ws:1", at=START)["active_leases"]])
            with self.assertRaises(CoordinationError):
                migrate(project, sqlite_path)


if __name__ == "__main__":
    unittest.main()
