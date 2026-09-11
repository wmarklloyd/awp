from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

from tools.awp_git_ledger import GitLedger, PROFILE, migrate
import tests.test_awp_coop2 as coop2_tests

ROOT = Path(__file__).resolve().parents[1]
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(["git", *arguments], cwd=cwd, check=True, capture_output=True, text=True, env=GIT_ENV).stdout


def make_project(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / ".awp.json", path / ".awp.json")
    shutil.copy2(ROOT / "awp.awp.md", path / "awp.awp.md")
    git(path, "init", "-q", ".")
    git(path, "add", "-A")
    git(path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")
    return path


class GitLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = make_project(Path(self.temporary.name) / "p")
        self.ledger = GitLedger(self.project)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def append(self, ledger: GitLedger, actor: str, kind: str = "k", **payload) -> dict:
        event, _ = ledger._append(workstate_id="ws:1", actor=actor, kind=kind, payload=payload,
                                  occurred_at="2026-09-11T00:00:00Z")
        return event

    def test_events_round_trip_in_per_actor_order(self) -> None:
        ids = [self.append(self.ledger, "actor:a", n=i)["event_id"] for i in range(5)]
        self.append(self.ledger, "actor:b", n=99)
        fresh = GitLedger(self.project)  # a restart reads the same history
        events = fresh.export_events("ws:1")
        self.assertEqual([e["event_id"] for e in events if e["actor"] == "actor:a"], ids)
        self.assertEqual(len(events), 6)
        self.assertTrue(all(e["extensions"]["awp_profile"] == PROFILE for e in events))

    def test_concurrent_writers_lose_nothing(self) -> None:
        errors = []

        def writer(tag: str) -> None:
            ledger = GitLedger(self.project)
            try:
                for i in range(10):
                    self.append(ledger, "actor:shared", tag=tag, n=i)
            except Exception as error:  # pragma: no cover - reported below
                errors.append(error)

        threads = [threading.Thread(target=writer, args=(tag,)) for tag in "wxyz"]
        [thread.start() for thread in threads]; [thread.join() for thread in threads]
        self.assertEqual(errors, [])
        events = GitLedger(self.project).export_events("ws:1")
        self.assertEqual(len(events), 40)
        self.assertEqual(len({e["event_id"] for e in events}), 40)
        ref = self.ledger.ref_for("ws:1", "actor:shared")
        self.assertEqual(git(self.project, "rev-list", "--count", ref).strip(), "40")  # one unbroken chain

    def test_cursor_replay_is_exact(self) -> None:
        for i in range(3):
            self.append(self.ledger, "actor:a", n=i)
        page = self.ledger.events_after("ws:1", {}, limit=2)
        self.assertEqual(len(page["events"]), 2)
        self.assertTrue(page["has_more"])
        rest = self.ledger.events_after("ws:1", page["events"][-1]["_ledger_sequence"])
        self.assertEqual(len(rest["events"]), 1)
        self.append(self.ledger, "actor:b", n=7)
        newer = self.ledger.events_after("ws:1", rest["next_cursor"])
        self.assertEqual([e["actor"] for e in newer["events"]], ["actor:b"])
        self.assertEqual(self.ledger.events_after("ws:1", newer["next_cursor"])["events"], [])

    def test_binding_identity_is_created_once(self) -> None:
        first = self.ledger.binding_id()
        self.assertEqual(GitLedger(self.project).binding_id(), first)
        self.assertEqual(GitLedger(self.project).initialize_binding("binding:other"), first)

    def test_ledger_refs_are_not_branches(self) -> None:
        self.append(self.ledger, "actor:a")
        self.assertEqual(git(self.project, "branch", "--list").strip().splitlines(), ["* " + git(self.project, "branch", "--show-current").strip()])
        self.assertTrue(git(self.project, "for-each-ref", "refs/awp/ledger/").strip())


class TwoMachineTests(unittest.TestCase):
    """Two clones sharing a bare remote stand in for two machines."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        origin = make_project(base / "origin-src")
        self.remote = base / "shared.git"
        git(base, "clone", "-q", "--bare", str(origin), str(self.remote))
        self.a = base / "a"; self.b = base / "b"
        git(base, "clone", "-q", str(self.remote), str(self.a))
        git(base, "clone", "-q", str(self.remote), str(self.b))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_events_flow_both_ways_through_the_remote(self) -> None:
        a, b = GitLedger(self.a, remote="origin"), GitLedger(self.b, remote="origin")
        binding = a.binding_id(); a.push("ws:1")
        sent, _ = a._append(workstate_id="ws:1", actor="actor:a", kind="ping", payload={}, occurred_at="2026-09-11T00:00:01Z")
        self.assertTrue(b.remote_heads("ws:1"))  # a cheap change check a watcher can poll
        b.fetch("ws:1")
        self.assertEqual(b.binding_id(), binding)
        self.assertEqual([e["event_id"] for e in b.export_events("ws:1")], [sent["event_id"]])
        reply, _ = b._append(workstate_id="ws:1", actor="actor:b", kind="pong", payload={}, occurred_at="2026-09-11T00:00:02Z")
        a.fetch("ws:1")
        self.assertEqual([e["event_id"] for e in a.export_events("ws:1")], [sent["event_id"], reply["event_id"]])

    def test_a_clone_behind_on_its_own_ref_is_not_overwritten_by_fetch(self) -> None:
        a = GitLedger(self.a, remote="origin")
        a._append(workstate_id="ws:1", actor="actor:a", kind="one", payload={}, occurred_at="2026-09-11T00:00:01Z")
        a.remote = None  # an unpushed local event
        local, _ = a._append(workstate_id="ws:1", actor="actor:a", kind="two", payload={}, occurred_at="2026-09-11T00:00:02Z")
        a.remote = "origin"
        a.fetch("ws:1")
        self.assertIn(local["event_id"], [e["event_id"] for e in a.export_events("ws:1")])
        a.push("ws:1")
        b = GitLedger(self.b, remote="origin"); b.fetch("ws:1")
        self.assertIn(local["event_id"], [e["event_id"] for e in b.export_events("ws:1")])


class MigrationTests(coop2_tests.RendezvousFixture):
    def test_sqlite_history_moves_into_git_unchanged(self) -> None:
        self.rendezvous.join("actor:a", [], observation="on-entry-only")
        self.rendezvous.join("actor:b", [], observation="on-entry-only")
        sent = self.rendezvous.tickle("actor:a", "actor:b")
        self.rendezvous.tickle_ack("actor:b", sent["tickle_id"])
        before = self.rendezvous._events()
        sqlite_path = self.project / ".awp-runtime" / "coop2-rendezvous.sqlite3"
        result = migrate(self.project, sqlite_path, self.rendezvous.workstate_id)
        self.assertEqual(result["migrated"], len(before))
        after = GitLedger(self.project).export_events(self.rendezvous.workstate_id)
        self.assertEqual(sorted(e["event_id"] for e in after), sorted(e["event_id"] for e in before))
        self.assertEqual({e["event_id"]: e for e in after}, {e["event_id"]: e for e in before})
        self.assertEqual(GitLedger(self.project).binding_id(), self.rendezvous.ledger.binding_id())
        self.assertEqual(migrate(self.project, sqlite_path, self.rendezvous.workstate_id)["migrated"], 0)


class GitProfileSupervisorTests(coop2_tests.RendezvousFixture):
    def setUp(self) -> None:
        self.patch = mock.patch.dict(os.environ, {"AWP_COOP2_LEDGER": PROFILE}); self.patch.start()
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown(); self.patch.stop()

    def test_tickle_reaches_the_agent_and_the_host_receipt_closes_it(self) -> None:
        from tools.awp_activation import activation_result
        from tools.awp_supervisor import SignalWatch, Supervisor

        self.assertEqual(self.rendezvous.ledger.profile, PROFILE)
        self.rendezvous.join("actor:codex", [], observation="watcher")
        self.rendezvous.join("actor:claude", [], observation="on-entry-only")
        watch = SignalWatch(self.project, "actor:codex"); before = watch.fingerprint()
        sent = self.rendezvous.tickle("actor:claude", "actor:codex")
        self.assertEqual(sent["doorbell"]["git_ref"]["profile"], PROFILE)
        self.assertNotEqual(watch.fingerprint(), before)  # the ledger ref update is the Git event

        class Adapter:
            calls = []
            def deliver(self, envelope): self.calls.append(envelope); return activation_result("accepted")

        adapter = Adapter()
        supervisor = Supervisor(self.rendezvous, "actor:codex", "fake", "s", "g", adapter,
                                self.project / ".awp-runtime" / "sup.json")
        first = supervisor.step()
        self.assertEqual(len(first["delivered"]), 1)
        self.assertEqual(supervisor.step()["delivered"], [])  # the cursor makes replay exact
        supervisor._handle_request({"actor": "actor:codex", "event_id": sent["receipt"]["event_id"],
                                    "via": "host-prompt-hook", "evidence": {"session_id": "s1"}})
        state = {t["tickle_id"]: t for t in self.rendezvous.tickles("actor:claude")}[sent["tickle_id"]]
        self.assertEqual(state["state"], "acknowledged")


def _git_profile(case: type) -> type:
    """Run an existing rendezvous test class against the Git ledger profile."""
    def setUp(self) -> None:
        self._profile = mock.patch.dict(os.environ, {"AWP_COOP2_LEDGER": PROFILE}); self._profile.start()
        case.setUp(self)
        self.assertEqual(self.rendezvous.ledger.profile, PROFILE)

    def tearDown(self) -> None:
        case.tearDown(self); self._profile.stop()

    return type(f"Git{case.__name__}", (case,), {"setUp": setUp, "tearDown": tearDown})


GitHeartbeatAndReachTests = _git_profile(coop2_tests.HeartbeatAndReachTests)
GitLifecycleExpiryTests = _git_profile(coop2_tests.LifecycleExpiryTests)
GitEntryRegistrationTests = _git_profile(coop2_tests.EntryRegistrationTests)
GitLifecycleGuardTests = _git_profile(coop2_tests.LifecycleGuardTests)
GitInventoryAndProbeTests = _git_profile(coop2_tests.InventoryAndProbeTests)


if __name__ == "__main__":
    unittest.main()
