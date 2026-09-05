from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_workstate():
    spec = importlib.util.spec_from_file_location(
        "awp_workstate_test", ROOT / "tools" / "awp_workstate.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load workstate tool")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class WorkstateWriterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_workstate()

    def copy_capsule(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        capsule = project / "project.awp.md"
        shutil.copy2(ROOT / "awp.awp.md", capsule)
        return temporary, project, capsule

    def request(self, capsule: Path, **changes: object) -> dict[str, object]:
        integrity = self.module.capsule_integrity(capsule)
        return {
            "request_id": "request:test-workstate",
            "expected_capsule_digest": self.module.capsule_artifact_digest(capsule),
            "expected_generated_digest": integrity["computed_digest"],
            "expected_frontier": self.module._frontier(capsule.read_text(encoding="utf-8")),
            "checkpoint": "checkpoint:test-workstate",
            "briefing": "# Test workstate\n\nA deterministic checkpoint.",
            **changes,
        }

    def test_no_change_does_not_rewrite_capsule(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        before = capsule.read_bytes()
        result = self.module.checkpoint(
            project, capsule, self.request(capsule, mode="no_change")
        )
        self.assertEqual(result["status"], "no_change")
        self.assertEqual(capsule.read_bytes(), before)

    def test_status_names_semantic_frontier_separately(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        result = self.module.status(project, capsule)
        self.assertIn("semantic_frontier", result)
        self.assertNotIn("frontier", result)

    def test_checkpoint_rewrites_briefing_and_returns_receipt(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        result = self.module.checkpoint(project, capsule, self.request(capsule))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            self.module.capsule_integrity(capsule)["state"], "current"
        )
        self.assertEqual(result["capsule_digest"], self.module.capsule_artifact_digest(capsule))
        self.assertIn("# Test workstate", capsule.read_text(encoding="utf-8"))

    def test_checkpoint_projects_supplied_records(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        result = self.module.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                records=[
                    {
                        "id": "task:projected-checkpoint",
                        "type": "task",
                        "title": "Projected checkpoint",
                        "status": "completed",
                    }
                ],
            ),
        )
        self.assertEqual(result["status"], "complete")
        sections = self.module._sections(capsule.read_text(encoding="utf-8"))
        task_ids = [item["id"] for item in sections["snapshot"]["records"]["tasks"]]
        self.assertIn("task:projected-checkpoint", task_ids)
        self.assertEqual(result["updated_record_ids"], ["task:projected-checkpoint"])

    def test_changed_artifact_requires_revision_or_new_identity(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(self.module.CoordinationError):
            self.module.checkpoint(
                project,
                capsule,
                self.request(
                    capsule,
                    records=[
                        {
                            "id": "artifact:selective-reentry-evaluation",
                            "type": "artifact",
                            "name": "changed",
                            "modules": {
                                "urn:awp:artifact": {
                                    "status": "retrievable",
                                    "locations": [{"kind": "local", "path": "changed"}],
                                    "integrity": {"algorithm": "sha256", "digest": "f" * 64},
                                }
                            },
                        }
                    ],
                ),
            )

    def test_whole_capsule_compare_and_swap_rejects_stale_request(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        request = self.request(capsule)
        capsule.write_text(capsule.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        before = capsule.read_bytes()
        with self.assertRaises(self.module.CoordinationError):
            self.module.checkpoint(project, capsule, request)
        self.assertEqual(capsule.read_bytes(), before)

    def test_recover_clears_journal_when_proposed_file_is_present(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        digest = self.module.capsule_artifact_digest(capsule)
        journal = project / self.module.JOURNAL_NAME
        journal.parent.mkdir(parents=True)
        journal.write_text(
            json.dumps(
                {
                    "profile": self.module.PROFILE,
                    "state": "file_replaced",
                    "capsule": capsule.name,
                    "expected_capsule_digest": digest,
                    "proposed_capsule_digest": digest,
                }
            ),
            encoding="utf-8",
        )
        result = self.module.recover(project, capsule)
        self.assertEqual(result["state"], "recovered")
        self.assertFalse(journal.exists())


if __name__ == "__main__":
    unittest.main()
