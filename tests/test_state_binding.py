"""Tests for `git-staged-tree-v1` state bindings (AWP Handoff section 10)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.awp_state_binding import (  # noqa: E402
    PROFILE,
    REVISION_PREFIX,
    StateBindingError,
    staged_tree_binding,
    verify_binding,
)
from tools import awp_workstate  # noqa: E402
from tools.awp_coordination import CoordinationError  # noqa: E402


def git(project: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(project),
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


class StagedTreeBindingTests(unittest.TestCase):
    def repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        git(project, "init", "--quiet")
        git(project, "config", "user.email", "test@example.invalid")
        git(project, "config", "user.name", "AWP Test")
        (project / "src").mkdir()
        (project / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(project, "add", "src/app.py")
        git(project, "commit", "--quiet", "-m", "initial")
        return temporary, project

    def test_revision_names_the_staged_tree(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        binding = staged_tree_binding(project, "repo:application")
        self.assertEqual(binding["profile"], PROFILE)
        self.assertTrue(binding["revision"].startswith(REVISION_PREFIX))
        self.assertEqual(
            binding["revision"][len(REVISION_PREFIX):],
            git(project, "rev-parse", "HEAD^{tree}"),
        )

    def test_staging_a_change_moves_the_revision(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        before = staged_tree_binding(project, "repo:application")["revision"]
        (project / "src" / "app.py").write_text("value = 2\n", encoding="utf-8")
        git(project, "add", "src/app.py")
        after = staged_tree_binding(project, "repo:application")["revision"]
        self.assertNotEqual(before, after)

    def test_unstaged_change_is_reported_not_asserted_clean(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        (project / "src" / "app.py").write_text("value = 3\n", encoding="utf-8")
        binding = staged_tree_binding(project, "repo:application", ["src/"])
        self.assertEqual(binding["working_tree"], "modified")
        self.assertIn("src/app.py", binding["divergence"]["unstaged"])

    def test_scope_excludes_unrelated_divergence(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        (project / "src" / "app.py").write_text("value = 4\n", encoding="utf-8")
        binding = staged_tree_binding(project, "repo:docs", ["docs/"])
        self.assertEqual(binding["working_tree"], "clean")

    def test_binding_survives_the_commit_it_describes(self) -> None:
        """The point of the profile: one value is current on both sides."""
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        (project / "src" / "app.py").write_text("value = 5\n", encoding="utf-8")
        git(project, "add", "src/app.py")
        binding = staged_tree_binding(project, "repo:application")
        self.assertEqual(verify_binding(project, binding)["matched"], "staged-index")
        git(project, "commit", "--quiet", "-m", "change")
        after = verify_binding(project, binding)
        self.assertEqual(after["state"], "current")
        self.assertEqual(after["recorded_tree"], git(project, "rev-parse", "HEAD^{tree}"))

    def test_a_commit_differing_only_at_excluded_paths_is_current(self) -> None:
        """The capsule holding the binding cannot be inside the tree it names."""
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        capsule = project / "project.awp.md"
        capsule.write_text("before\n", encoding="utf-8")
        git(project, "add", "project.awp.md")
        binding = staged_tree_binding(
            project, "repo:application", None, ["project.awp.md"]
        )
        self.assertEqual(binding["excludes"], ["project.awp.md"])
        capsule.write_text("after the binding was written\n", encoding="utf-8")
        git(project, "add", "project.awp.md")
        git(project, "commit", "--quiet", "-m", "work plus capsule")
        result = verify_binding(project, binding)
        self.assertEqual(result["state"], "current")
        self.assertEqual(result["matched"], "commit-tree-modulo-excludes")
        self.assertEqual(result["excluded_differences"], ["project.awp.md"])

    def test_a_commit_touching_more_than_the_excluded_path_is_stale(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        capsule = project / "project.awp.md"
        capsule.write_text("before\n", encoding="utf-8")
        git(project, "add", "project.awp.md")
        binding = staged_tree_binding(
            project, "repo:application", None, ["project.awp.md"]
        )
        capsule.write_text("after\n", encoding="utf-8")
        (project / "src" / "app.py").write_text("value = 9\n", encoding="utf-8")
        git(project, "add", "project.awp.md", "src/app.py")
        git(project, "commit", "--quiet", "-m", "capsule plus unbound work")
        result = verify_binding(project, binding)
        self.assertEqual(result["state"], "stale")
        self.assertIn("src/app.py", result["differing_paths"])

    def test_excluded_path_does_not_count_as_working_tree_divergence(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        (project / "project.awp.md").write_text("untracked capsule\n", encoding="utf-8")
        binding = staged_tree_binding(
            project, "repo:application", None, ["project.awp.md"]
        )
        self.assertEqual(binding["working_tree"], "clean")
        self.assertNotIn("divergence", binding)

    def test_later_commit_makes_the_binding_stale(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        binding = staged_tree_binding(project, "repo:application")
        (project / "src" / "app.py").write_text("value = 6\n", encoding="utf-8")
        git(project, "add", "src/app.py")
        git(project, "commit", "--quiet", "-m", "later")
        self.assertEqual(verify_binding(project, binding)["state"], "stale")

    def test_foreign_profile_is_unavailable_not_current(self) -> None:
        temporary, project = self.repository()
        self.addCleanup(temporary.cleanup)
        result = verify_binding(project, {"profile": "git-state-v1", "revision": "git:91ab4e7"})
        self.assertEqual(result["state"], "unavailable")

    def test_outside_a_repository_it_declines(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(StateBindingError):
            staged_tree_binding(Path(temporary.name), "repo:application")


class CheckpointBindingTests(unittest.TestCase):
    def project_with_capsule(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        git(project, "init", "--quiet")
        git(project, "config", "user.email", "test@example.invalid")
        git(project, "config", "user.name", "AWP Test")
        capsule = project / "project.awp.md"
        shutil.copy2(ROOT / "awp.awp.md", capsule)
        git(project, "add", "project.awp.md")
        git(project, "commit", "--quiet", "-m", "capsule")
        return temporary, project, capsule

    def request(self, capsule: Path, **changes: object) -> dict[str, object]:
        integrity = awp_workstate.capsule_integrity(capsule)
        return {
            "request_id": "request:test-state-binding",
            "expected_capsule_digest": awp_workstate.capsule_artifact_digest(capsule),
            "expected_generated_digest": integrity["computed_digest"],
            "expected_frontier": awp_workstate._frontier(capsule.read_text(encoding="utf-8")),
            "checkpoint": "checkpoint:test-state-binding",
            "briefing": "# Binding test\n\nA deterministic checkpoint.\n\nNext action: none.",
            **changes,
        }

    def resume(self, capsule: Path) -> dict:
        snapshot = awp_workstate._sections(
            capsule.read_text(encoding="utf-8").replace("\r\n", "\n")
        )["snapshot"]
        return snapshot["modules"]["urn:awp:handoff"]["resume"]

    def test_checkpoint_records_the_binding_and_bumps_the_resume(self) -> None:
        temporary, project, capsule = self.project_with_capsule()
        self.addCleanup(temporary.cleanup)
        before = self.resume(capsule)["revision"]
        receipt = awp_workstate.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                state_binding={"mode": "staged-tree", "state_space": "repo:application"},
            ),
        )
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["state_binding"]["profile"], PROFILE)
        resume = self.resume(capsule)
        self.assertEqual(resume["revision"], before + 1)
        bindings = resume["state_bindings"]
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0]["state_space"], "repo:application")
        self.assertTrue(bindings[0]["revision"].startswith(REVISION_PREFIX))

    def test_checkpoint_excludes_the_capsule_from_its_own_binding(self) -> None:
        temporary, project, capsule = self.project_with_capsule()
        self.addCleanup(temporary.cleanup)
        receipt = awp_workstate.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                state_binding={"mode": "staged-tree", "state_space": "repo:application"},
            ),
        )
        self.assertEqual(receipt["state_binding"]["excludes"], ["project.awp.md"])
        binding = self.resume(capsule)["state_bindings"][0]
        git(project, "add", "project.awp.md")
        git(project, "commit", "--quiet", "-m", "checkpoint")
        self.assertEqual(verify_binding(project, binding)["state"], "current")

    def test_rebinding_the_same_state_space_replaces_rather_than_appends(self) -> None:
        temporary, project, capsule = self.project_with_capsule()
        self.addCleanup(temporary.cleanup)
        specification = {"mode": "staged-tree", "state_space": "repo:application"}
        awp_workstate.checkpoint(project, capsule, self.request(capsule, state_binding=specification))
        (project / "note.txt").write_text("second\n", encoding="utf-8")
        git(project, "add", "note.txt")
        awp_workstate.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                checkpoint="checkpoint:test-state-binding-2",
                state_binding=specification,
            ),
        )
        self.assertEqual(len(self.resume(capsule)["state_bindings"]), 1)

    def test_a_caller_cannot_assert_its_own_binding_mode(self) -> None:
        temporary, project, capsule = self.project_with_capsule()
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(CoordinationError):
            awp_workstate.checkpoint(
                project,
                capsule,
                self.request(
                    capsule,
                    state_binding={"mode": "asserted", "state_space": "repo:application"},
                ),
            )

    def test_outside_a_repository_the_checkpoint_is_rejected(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name)
        capsule = project / "project.awp.md"
        shutil.copy2(ROOT / "awp.awp.md", capsule)
        with self.assertRaises(CoordinationError):
            awp_workstate.checkpoint(
                project,
                capsule,
                self.request(
                    capsule,
                    state_binding={"mode": "staged-tree", "state_space": "repo:application"},
                ),
            )


if __name__ == "__main__":
    unittest.main()
