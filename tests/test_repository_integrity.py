from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import yaml


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

    def test_requirements_inventory_is_reproducible(self) -> None:
        builder = load_module(ROOT / "tools" / "build_requirements_registry.py", "awp_build_requirements")
        expected = json.loads(
            (ROOT / "spec" / "drafts" / "0.7.0" / "requirements.json").read_text(encoding="utf-8")
        )
        self.assertEqual(builder.build(), expected)
        ids = [requirement["id"] for requirement in expected["requirements"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_stable_requirements_inventory_is_reproducible(self) -> None:
        builder = load_module(ROOT / "tools" / "build_requirements_registry.py", "awp_build_requirements_stable")
        expected = json.loads(
            (ROOT / "spec" / "0.7.0" / "requirements.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            builder.build(
                ROOT / "spec" / "0.7.0",
                "0.7.0",
                "spec/0.7.0",
                "frozen-release-inventory",
            ),
            expected,
        )

    def test_stable_overview_matches_tagged_git_object(self) -> None:
        current_text = (ROOT / "AWP_SPECIFICATION_0.6.0.md").read_text(encoding="utf-8").rstrip()
        tagged_bytes = subprocess.run(
            ["git", "show", "v0.6.0:AWP_SPECIFICATION_0.6.0.md"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        tagged_text = tagged_bytes.decode("utf-8").rstrip()
        self.assertEqual(current_text, tagged_text)

    def test_architecture_decision_numbers_are_unique(self) -> None:
        numbers = [path.name.split("-", 1)[0] for path in (ROOT / "docs" / "decisions").glob("*.md")]
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_draft_bundle_is_reproducible(self) -> None:
        builder = load_module(ROOT / "tools" / "build_spec_0_7_bundle.py", "awp_build_07")
        expected = (
            ROOT / "dist" / "drafts" / "0.7.0" / "AWP-0.7.0-draft.bundle.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(builder.build(), expected)

    def test_stable_0_7_bundle_is_reproducible(self) -> None:
        builder = load_module(
            ROOT / "tools" / "build_spec_0_7_release_bundle.py", "awp_build_07_release"
        )
        expected = (ROOT / "dist" / "0.7.0" / "AWP-0.7.0.bundle.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(builder.build(), expected)

    def test_stable_0_7_checksums_match_release_manifest(self) -> None:
        release = ROOT / "dist" / "0.7.0"
        manifest = json.loads((release / "release-manifest.json").read_text(encoding="utf-8"))
        recorded = {}
        for line in (release / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, path = line.split(maxsplit=1)
            recorded[path] = digest
        expected = {
            str(Path(artifact["path"]).relative_to("dist/0.7.0")).replace("\\", "/"): artifact["sha256"]
            for artifact in manifest["artifacts"]
        }
        self.assertEqual(recorded, expected)
        for artifact in manifest["artifacts"]:
            self.assertEqual(
                hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest(),
                artifact["sha256"],
            )

    def test_released_discovery_schema_remains_historical(self) -> None:
        released = json.loads(
            (ROOT / "schemas" / "awp-discovery-0.1.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(released)
        self.assertNotIn("specification", released["required"])

    def test_current_capsule_contains_embedded_discovery_metadata(self) -> None:
        self.assertFalse((ROOT / ".awp.json").exists())
        capsule = (ROOT / "awp.awp.md").read_text(encoding="utf-8")
        metadata = yaml.load(capsule.split("---", 2)[1], Loader=yaml.BaseLoader)
        schema = json.loads((ROOT / "schemas" / "awp-capsule-0.4.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(metadata))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
