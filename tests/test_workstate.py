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

    def test_small_refresh_records_durable_event_without_rewriting_capsule(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        before = capsule.read_bytes()
        result = self.module.small_refresh(
            project,
            capsule,
            {
                "request_id": "refresh:test-small",
                "event_id": "evt:test-small",
                "checkpoint": "checkpoint:test-small",
                "summary": "Updated one presentation asset.",
                "next_action": "Verify the rendered asset at handoff.",
                "evidence": ["tests:visual-check"],
            },
        )
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["projection"], "deferred")
        self.assertTrue(result["capsule_unchanged"])
        self.assertEqual(capsule.read_bytes(), before)
        log = project / self.module.REFRESH_LOG_NAME
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)
        duplicate = self.module.small_refresh(
            project,
            capsule,
            {
                "request_id": "refresh:test-small",
                "event_id": "evt:test-small",
                "checkpoint": "checkpoint:test-small",
                "summary": "Updated one presentation asset.",
                "next_action": "Verify the rendered asset at handoff.",
                "evidence": ["tests:visual-check"],
            },
        )
        self.assertEqual(duplicate["status"], "deduplicated")
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)

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

    def test_checkpoint_replaces_explicit_module_projection(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        module_state = {
            "contract": "COOP-1",
            "claim_state": "partial",
            "capabilities": ["deterministic-coordination-projector"],
        }
        result = self.module.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                module_updates={"urn:awp:cooperation": module_state},
            ),
        )
        sections = self.module._sections(capsule.read_text(encoding="utf-8"))
        self.assertEqual(sections["snapshot"]["modules"]["urn:awp:cooperation"], module_state)
        self.assertEqual(result["updated_module_ids"], ["urn:awp:cooperation"])

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

    def test_checkpoint_updates_all_duplicate_record_projections(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        result = self.module.checkpoint(
            project,
            capsule,
            self.request(
                capsule,
                records=[
                    {
                        "id": "artifact:participation-conversations",
                        "type": "artifact",
                        "revision": 3,
                        "supersedes": "artifact:participation-conversations",
                        "name": "Updated conversations",
                        "modules": {
                            "urn:awp:artifact": {
                                "status": "retrievable",
                                "locations": [{"kind": "local", "path": "changed"}],
                                "integrity": {"algorithm": "sha256", "digest": "e" * 64},
                            }
                        },
                    }
                ],
            ),
        )
        artifacts = self.module._sections(capsule.read_text(encoding="utf-8"))["snapshot"]["records"]["artifacts"]
        projected = [item for item in artifacts if item["id"] == "artifact:participation-conversations"]
        self.assertEqual(len(projected), 2)
        self.assertTrue(all(item["revision"] == 3 for item in projected))
        self.assertEqual(result["updated_record_ids"], ["artifact:participation-conversations"])

    def test_whole_capsule_compare_and_swap_rejects_stale_request(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        request = self.request(capsule)
        capsule.write_text(capsule.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        before = capsule.read_bytes()
        with self.assertRaises(self.module.CoordinationError):
            self.module.checkpoint(project, capsule, request)
        self.assertEqual(capsule.read_bytes(), before)

    def test_from_current_fills_missing_preconditions_and_checkpoints(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        bare = {
            "request_id": "request:test-from-current",
            "checkpoint": "checkpoint:test-from-current",
            "briefing": "# From current\n\nPreconditions derived by the tool.",
        }
        filled = self.module.fill_preconditions_from_current(capsule, bare)
        self.assertEqual(filled["expected_capsule_digest"], self.module.capsule_artifact_digest(capsule))
        self.assertEqual(
            filled["expected_generated_digest"], self.module.capsule_integrity(capsule)["computed_digest"]
        )
        self.assertEqual(
            filled["expected_frontier"], self.module._frontier(capsule.read_text(encoding="utf-8"))
        )
        self.assertEqual(filled["preconditions_source"], "from-current")
        self.assertNotIn("expected_capsule_digest", bare)
        result = self.module.checkpoint(project, capsule, filled)
        self.assertEqual(result["status"], "complete")

    def test_from_current_keeps_explicit_preconditions_as_guards(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        stale = "sha256:" + "0" * 64
        filled = self.module.fill_preconditions_from_current(
            capsule, {"checkpoint": "checkpoint:test-guard", "expected_capsule_digest": stale, "mode": "no_change"}
        )
        self.assertEqual(filled["expected_capsule_digest"], stale)
        with self.assertRaises(self.module.CoordinationError):
            self.module.checkpoint(project, capsule, filled)

    def test_briefing_is_derived_from_summary_and_next_action(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        request = self.request(capsule)
        del request["briefing"]
        request["summary"] = "Derived briefings remove per-attempt prose."
        request["next_action"] = "Ship phase two."
        result = self.module.checkpoint(project, capsule, request)
        self.assertEqual(result["status"], "complete")
        text = capsule.read_text(encoding="utf-8")
        self.assertIn("# Test workstate", text)
        self.assertIn("Derived briefings remove per-attempt prose.", text)
        self.assertIn("Next action: Ship phase two.", text)

    def test_briefing_is_derived_from_checkpoint_record(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        request = self.request(capsule, checkpoint="checkpoint:from-record")
        del request["briefing"]
        request["records"] = [
            {
                "id": "checkpoint:from-record",
                "type": "checkpoint",
                "summary": "Summary carried on the checkpoint record.",
                "next_action": "Next from record.",
            }
        ]
        result = self.module.checkpoint(project, capsule, request)
        self.assertEqual(result["status"], "complete")
        self.assertIn("Summary carried on the checkpoint record.", capsule.read_text(encoding="utf-8"))

    def test_checkpoint_without_any_briefing_source_is_rejected(self) -> None:
        temporary, project, capsule = self.copy_capsule()
        self.addCleanup(temporary.cleanup)
        request = self.request(capsule)
        del request["briefing"]
        with self.assertRaises(self.module.CoordinationError):
            self.module.checkpoint(project, capsule, request)

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


class CapsuleMigrationTests(unittest.TestCase):
    """The 0.6.0 -> 0.8.0 capsule metadata migration."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "awp_migrate_test", ROOT / "tools" / "migrate_capsule_0_6_to_0_8.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        cls.module = module

    def test_repository_capsule_is_migrated_and_stays_migrated(self) -> None:
        result = self.module.main(["--project", str(ROOT), "--check"])
        self.assertEqual(result, 0, "the repository capsule should already declare 0.8.0")

    def test_renderers_reproduce_every_section_byte_for_byte(self) -> None:
        text = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
        self.assertEqual(self.module.check_render_fidelity(text), [])

    def test_migration_rewrites_identity_metadata_only(self) -> None:
        import json as json_module
        import re

        text = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
        legacy = text.replace("awp_version: 0.8.0", "awp_version: 0.6.0", 1)
        legacy = legacy.replace("discovery: project\n", "", 1)
        legacy = legacy.replace('"awp_version": "0.8.0"', '"awp_version": "0.6.0"')
        before = json_module.loads(
            re.search(
                r'<!-- awp:(?:[^:\s]+:)?snapshot:start encoding="json" -->\n(.*?)\n<!-- awp:(?:[^:\s]+:)?snapshot:end -->',
                legacy,
                re.DOTALL,
            ).group(1)
        )
        migrated, changes = self.module.migrate_front_matter(legacy)
        migrated, section_changes = self.module.migrate_sections(
            migrated, self.module.registry_modules(ROOT)
        )
        after = json_module.loads(
            re.search(
                r'<!-- awp:(?:[^:\s]+:)?snapshot:start encoding="json" -->\n(.*?)\n<!-- awp:(?:[^:\s]+:)?snapshot:end -->',
                migrated,
                re.DOTALL,
            ).group(1)
        )
        self.assertIn("awp_version: 0.6.0 -> 0.8.0", changes)
        self.assertIn("discovery: (absent) -> project", changes)
        self.assertTrue(any("snapshot.awp_version" in item for item in section_changes))
        # Semantic records are the projector's business, not the migration's.
        self.assertEqual(before["records"], after["records"])
        self.assertEqual(before["frontier"], after["frontier"])

    def test_migration_is_idempotent(self) -> None:
        text = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
        once, first = self.module.migrate_front_matter(text)
        once, first_sections = self.module.migrate_sections(once, self.module.registry_modules(ROOT))
        self.assertEqual(first + first_sections, [])
        self.assertEqual(once, text)
