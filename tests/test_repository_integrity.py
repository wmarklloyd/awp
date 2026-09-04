from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryIntegrityTests(unittest.TestCase):
    def test_stable_bundle_matches_release_manifest(self) -> None:
        manifest_path = ROOT / "dist" / "0.6.0" / "release-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for artifact in manifest["artifacts"]:
            payload = (ROOT / artifact["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), artifact["sha256"])

    def test_sha256sums_matches_release_manifest(self) -> None:
        release = ROOT / "dist" / "0.6.0"
        manifest = json.loads((release / "release-manifest.json").read_text(encoding="utf-8"))
        expected = {
            artifact["path"].removeprefix("dist/0.6.0/"): artifact["sha256"]
            for artifact in manifest["artifacts"]
        }
        recorded = {}
        for line in (release / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, path = line.split(maxsplit=1)
            recorded[path] = digest
        self.assertEqual(recorded, expected)

    def test_archived_release_files_match_tagged_git_objects(self) -> None:
        manifest = json.loads(
            (ROOT / "dist" / "0.6.0" / "release-manifest.json").read_text(encoding="utf-8")
        )
        for artifact in manifest["artifacts"]:
            tagged_blob = subprocess.run(
                ["git", "rev-parse", f"{manifest['git_tag']}:{artifact['tagged_path']}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            archived_blob = subprocess.run(
                ["git", "hash-object", artifact["path"]],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(tagged_blob, artifact["tagged_git_blob_sha1"])
            self.assertEqual(archived_blob, tagged_blob)

    def test_stable_bundle_is_reproducible(self) -> None:
        builder = load_module(ROOT / "tools" / "build_spec_0_6_bundle.py", "awp_build_06")
        expected = (ROOT / "dist" / "0.6.0" / "AWP-0.6.0.bundle.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(builder.build(), expected)

    def test_draft_bundle_is_reproducible(self) -> None:
        builder = load_module(ROOT / "tools" / "build_spec_0_7_bundle.py", "awp_build_07")
        expected = (
            ROOT / "dist" / "drafts" / "0.7.0" / "AWP-0.7.0-draft.bundle.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(builder.build(), expected)

    def test_released_and_draft_discovery_schemas_have_distinct_ids(self) -> None:
        released = json.loads(
            (ROOT / "schemas" / "awp-discovery-0.1.schema.json").read_text(encoding="utf-8")
        )
        draft = json.loads(
            (ROOT / "schemas" / "awp-discovery-0.2.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(released)
        Draft202012Validator.check_schema(draft)
        self.assertNotEqual(released["$id"], draft["$id"])
        self.assertNotIn("specification", released["required"])
        self.assertIn("specification", draft["required"])

    def test_repository_discovery_matches_capsule_specification(self) -> None:
        discovery = json.loads((ROOT / ".awp.json").read_text(encoding="utf-8"))
        capsule = (ROOT / discovery["current_workstate"]).read_text(encoding="utf-8")
        metadata = capsule.split("---", 2)[1]
        expected = f"specification: {discovery['specification']}"
        self.assertIn(expected, metadata)


if __name__ == "__main__":
    unittest.main()
