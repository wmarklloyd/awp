from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_reentry():
    spec = importlib.util.spec_from_file_location("awp_reentry_test", ROOT / "tools" / "awp_reentry.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load re-entry tool")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class ReentryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_reentry()

    def test_root_capsule_selects_resume_context_without_full_snapshot(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        self.assertEqual(view["integrity"]["state"], "current")
        self.assertTrue(view["selection"]["complete"])
        resume = view["entry"]["resume"]
        self.assertEqual(
            [record["id"] for record in view["entry"]["read_first"]],
            resume["read_first"],
        )
        self.assertLess(len(json.dumps(view).encode("utf-8")), view["source"]["bytes"])
        self.assertNotIn("events", view)
        self.assertEqual(view["selection"]["required_artifact_failures"], [])
        self.assertTrue(
            all(
                artifact["verification_state"] == "current"
                for artifact in view["entry"]["required_artifacts"]
            )
        )

    def test_required_artifact_digest_mismatch_is_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact_path = root / "artifact.txt"
            artifact_path.write_text("changed", encoding="utf-8")
            record = {
                "id": "artifact:test",
                "name": "test",
                "modules": {
                    "urn:awp:artifact": {
                        "status": "retrievable",
                        "locations": [{"kind": "local", "path": "artifact.txt"}],
                        "integrity": {
                            "algorithm": "sha256",
                            "digest": hashlib.sha256(b"expected").hexdigest(),
                        },
                    }
                },
            }
            projection = self.module._artifact_projection(record, root)
            self.assertEqual(projection["verification_state"], "modified")

    def test_historical_artifact_is_not_treated_as_active_failure(self) -> None:
        record = {
            "id": "artifact:historical",
            "type": "artifact",
            "modules": {
                "urn:awp:artifact": {
                    "status": "superseded",
                    "locations": [{"kind": "local", "path": "missing-old-file"}],
                    "integrity": {"algorithm": "sha256", "digest": "0" * 64},
                }
            },
        }
        projection = self.module._artifact_projection(record, Path.cwd())
        self.assertEqual(projection["verification_state"], "historical")

    def test_stale_capsule_integrity_is_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            capsule = Path(directory) / "awp.awp.md"
            source = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
            capsule.write_text(
                source.replace("<!-- awp:generated:start -->\n", "<!-- awp:generated:start -->\nModified generated briefing\n", 1),
                encoding="utf-8",
            )
            view = self.module.build_reentry_view(capsule)
            self.assertEqual(view["integrity"]["state"], "modified")
            self.assertFalse(view["selection"]["complete"])

    def test_brief_only_does_not_parse_or_claim_complete_context(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md", brief_only=True)
        self.assertEqual(view["selection"]["state"], "brief_only")
        self.assertFalse(view["selection"]["complete"])
        self.assertNotIn("entry", view)

    def test_budget_failure_is_explicit_and_nonzero(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "awp_reentry.py"),
                "--project",
                str(ROOT),
                "--max-output-bytes",
                "1000",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selection"]["state"], "budget_exceeded")
        self.assertFalse(payload["selection"]["complete"])
        self.assertEqual(payload["selection"]["omitted"], ["entry"])

    def test_budget_failure_retains_coordination_status(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        view["coordination"] = {
            "state": "available",
            "open_count": 1,
            "open_items": [{"interaction_id": "interaction:critical"}],
        }
        rendered, complete = self.module.bounded_json(view, 1000)
        self.assertFalse(complete)
        payload = json.loads(rendered)
        self.assertEqual(payload["selection"]["state"], "budget_exceeded")
        self.assertEqual(payload["coordination"]["open_items"][0]["interaction_id"], "interaction:critical")

    def test_unavailable_coordination_never_claims_complete(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        view["coordination"] = {
            "state": "unavailable",
            "read_verified": False,
            "diagnostic": "AWP-COORD-LEDGER-UNAVAILABLE",
        }
        rendered, complete = self.module.bounded_json(view, 100_000)
        payload = json.loads(rendered)
        self.assertFalse(complete)
        self.assertFalse(payload["selection"]["complete"])
        self.assertEqual(payload["selection"]["state"], "incomplete")

    def test_measurement_settles_on_a_rounding_tie_instead_of_refusing(self) -> None:
        # Construct a view whose rendered size sits exactly where round(ratio, 2)
        # flips width by one character, producing a 2-cycle in the measurement.
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        view["coordination"] = {"state": "available", "read_verified": True, "open_count": 0}
        found = False
        for pad in range(0, 400):
            trial = json.loads(json.dumps(view))
            trial["briefing"] = view["briefing"] + ("x" * pad)
            trial["selection"].pop("output_bytes", None)
            trial["selection"].pop("source_to_output_ratio", None)
            sizes = []
            for _ in range(4):
                rendered = json.dumps(trial, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
                required = len(rendered.encode("utf-8"))
                sizes.append(required)
                trial["selection"]["output_bytes"] = required
                trial["selection"]["source_to_output_ratio"] = round(trial["source"]["bytes"] / required, 2)
            if len(set(sizes[-2:])) == 2 and sizes[-1] == sizes[-3]:
                found = True
                rendered, complete = self.module.bounded_json(trial, 1_000_000)
                payload = json.loads(rendered)
                self.assertEqual(payload["selection"]["measurement"], "settled-on-rounding-tie")
                self.assertLessEqual(abs(payload["selection"]["output_bytes"] - len(rendered.encode("utf-8"))), 1)
                self.assertTrue(complete)
                break
        self.assertTrue(found, "no rounding tie found within 400 bytes of padding; widen the search")

    def test_skipped_coordination_never_claims_complete(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        view["coordination"] = {
            "state": "skipped",
            "diagnostic": "AWP-COORD-ACTOR-REQUIRED",
        }
        rendered, complete = self.module.bounded_json(view, 100_000)
        payload = json.loads(rendered)
        self.assertFalse(complete)
        self.assertFalse(payload["selection"]["complete"])

    def test_missing_actor_is_explicitly_disclosed(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "awp_reentry.py"), "--project", str(ROOT), "--max-output-bytes", "70000"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["coordination"]["state"], "skipped")
        self.assertEqual(payload["coordination"]["diagnostic"], "AWP-COORD-ACTOR-REQUIRED")

    def test_reported_output_size_matches_serialized_bytes(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        rendered, complete = self.module.bounded_json(view, 100_000)
        self.assertTrue(complete)
        self.assertEqual(
            view["selection"]["output_bytes"], len(rendered.encode("utf-8"))
        )

    def test_coordination_entry_view_reads_mailbox_and_doorbell(self) -> None:
        binding = {"profile": "local-coop2-rendezvous-v1", "doorbell": {"state": "current"}}
        inbox = {"binding": binding, "inbox": [{"interaction_id": "interaction:test"}], "responses": []}
        with patch("tools.awp_coop2.Rendezvous") as rendezvous_type:
            rendezvous_type.return_value.inbox.return_value = inbox
            view = self.module.coordination_entry_view(ROOT, "actor:codex")
        self.assertEqual(view["state"], "available")
        self.assertTrue(view["read_verified"])
        self.assertEqual(view["open_items"][0]["interaction_id"], "interaction:test")
        self.assertNotIn("doorbell", view["binding"])
        rendezvous_type.return_value.inbox.assert_called_once_with("actor:codex")

    def test_coordination_entry_view_discloses_unavailable_binding(self) -> None:
        with patch("tools.awp_coop2.Rendezvous", side_effect=OSError("locked")):
            view = self.module.coordination_entry_view(ROOT, "actor:codex")
        self.assertEqual(view["state"], "unavailable")
        self.assertFalse(view["read_verified"])
        self.assertEqual(view["diagnostic"], "AWP-COORD-LEDGER-UNAVAILABLE")

    def test_coordination_entry_view_discloses_sqlite_failure(self) -> None:
        with patch("tools.awp_coop2.Rendezvous", side_effect=sqlite3.OperationalError("locked")):
            view = self.module.coordination_entry_view(ROOT, "actor:codex")
        self.assertEqual(view["state"], "unavailable")
        self.assertFalse(view["read_verified"])
        self.assertEqual(view["diagnostic"], "AWP-COORD-LEDGER-UNAVAILABLE")

    def test_coordination_entry_view_catches_package_coordination_error(self) -> None:
        from tools.awp_coordination import CoordinationError as PackageCoordinationError

        with patch("tools.awp_coop2.Rendezvous", side_effect=PackageCoordinationError("git unavailable")):
            view = self.module.coordination_entry_view(ROOT, "actor:codex")
        self.assertEqual(view["state"], "unavailable")
        self.assertFalse(view["read_verified"])
        self.assertEqual(view["diagnostic"], "AWP-COORD-LEDGER-UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()


class EntrySliceTests(unittest.TestCase):
    """The generated entry slice is a convenience bound to a capsule revision."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_reentry()
        spec = importlib.util.spec_from_file_location(
            "awp_workstate_slice_test", ROOT / "tools" / "awp_workstate.py"
        )
        workstate = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT))
        try:
            spec.loader.exec_module(workstate)
        finally:
            sys.path.pop(0)
        cls.workstate = workstate

    def project(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        capsule = project / "awp.awp.md"
        shutil.copy2(ROOT / "awp.awp.md", capsule)
        return temporary, project, capsule

    def test_slice_is_a_strict_subset_bound_to_the_capsule_digest(self) -> None:
        temporary, project, capsule = self.project()
        self.addCleanup(temporary.cleanup)
        written = self.workstate.write_entry_slice(project, capsule)
        document = json.loads((project / "awp.entry.json").read_text(encoding="utf-8"))
        full = self.module.build_reentry_view(capsule)
        self.assertEqual(document["capsule_digest"], written["capsule_digest"])
        self.assertEqual(document["briefing"], full["briefing"])
        self.assertEqual(document["entry"], full["entry"])
        self.assertLess((project / "awp.entry.json").stat().st_size, capsule.stat().st_size // 4)

    def test_current_slice_is_accepted(self) -> None:
        temporary, project, capsule = self.project()
        self.addCleanup(temporary.cleanup)
        self.workstate.write_entry_slice(project, capsule)
        result = self.module.read_entry_slice(project, capsule)
        self.assertEqual(result["state"], "current")
        self.assertEqual(result["entry"], self.module.build_reentry_view(capsule)["entry"])

    def test_slice_for_another_capsule_revision_is_refused(self) -> None:
        temporary, project, capsule = self.project()
        self.addCleanup(temporary.cleanup)
        self.workstate.write_entry_slice(project, capsule)
        capsule.write_text(capsule.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        result = self.module.read_entry_slice(project, capsule)
        self.assertEqual(result["state"], "stale")
        self.assertNotEqual(result["slice_capsule_digest"], result["capsule_digest"])

    def test_absent_and_unreadable_slices_are_reported_not_guessed(self) -> None:
        temporary, project, capsule = self.project()
        self.addCleanup(temporary.cleanup)
        self.assertIsNone(self.module.read_entry_slice(project, capsule))
        (project / "awp.entry.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(self.module.read_entry_slice(project, capsule)["state"], "unusable")

    def test_checkpoint_refreshes_the_slice(self) -> None:
        temporary, project, capsule = self.project()
        self.addCleanup(temporary.cleanup)
        self.workstate.write_entry_slice(project, capsule)
        before = json.loads((project / "awp.entry.json").read_text(encoding="utf-8"))["capsule_digest"]
        request = self.workstate.fill_preconditions_from_current(
            capsule,
            {
                "request_id": "request:slice-refresh",
                "checkpoint": "checkpoint:slice-refresh",
                "summary": "Refresh the slice.",
                "next_action": "None.",
            },
        )
        receipt = self.workstate.checkpoint(project, capsule, request)
        self.assertEqual(receipt["status"], "complete")
        after = json.loads((project / "awp.entry.json").read_text(encoding="utf-8"))["capsule_digest"]
        self.assertNotEqual(before, after)
        self.assertEqual(after, receipt["entry_slice"]["capsule_digest"])
        self.assertEqual(self.module.read_entry_slice(project, capsule)["state"], "current")
