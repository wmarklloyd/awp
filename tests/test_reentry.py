from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
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

    def test_stale_capsule_integrity_is_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            capsule = Path(directory) / "awp.awp.md"
            source = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
            capsule.write_text(
                source.replace("# Agent Workshare Protocol design", "# Modified design", 1),
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

    def test_reported_output_size_matches_serialized_bytes(self) -> None:
        view = self.module.build_reentry_view(ROOT / "awp.awp.md")
        rendered, complete = self.module.bounded_json(view, 100_000)
        self.assertTrue(complete)
        self.assertEqual(
            view["selection"]["output_bytes"], len(rendered.encode("utf-8"))
        )


if __name__ == "__main__":
    unittest.main()
