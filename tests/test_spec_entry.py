from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "tools" / "awp_spec_entry.py"
    spec = importlib.util.spec_from_file_location("awp_spec_entry", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load awp_spec_entry")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SpecEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entry = load_module()

    def test_generated_profile_is_current_and_reproducible(self) -> None:
        self.assertEqual(self.entry.verify()["state"], "current")
        expected = self.entry.OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(self.entry.render(), expected)

    def test_routes_reference_existing_sources(self) -> None:
        for route in self.entry.ROUTES.values():
            for relative in [*route["documents"], *route["schemas"]]:
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_coordination_route_includes_direct_dependencies(self) -> None:
        documents = self.entry.ROUTES["coordination"]["documents"]
        self.assertIn("spec/drafts/0.8.0/core.md", documents)
        self.assertIn("spec/drafts/0.8.0/synchronization.md", documents)
        self.assertIn("spec/drafts/0.8.0/coordination.md", documents)


    def test_routes_resolve_to_registry_statements_that_cost_less_than_prose(self) -> None:
        for name in self.entry.ROUTES:
            view = self.entry.route_view(name)
            self.assertGreater(view["statement_count"], 0, name)
            sources = {item["source"] for item in view["statements"]}
            self.assertTrue(sources <= set(view["modules_on_demand"]), name)
            prose = sum((ROOT / path).stat().st_size for path in view["modules_on_demand"])
            self.assertLess(view["statement_bytes"], prose * 0.6, name)
            for item in view["statements"]:
                self.assertTrue(item["id"].startswith("AWP-"))
                self.assertTrue(item["statement"].strip())

    def test_statement_rendering_is_grouped_and_names_schema_digests(self) -> None:
        text = self.entry.render_statements("coordination")
        self.assertIn("# AWP 0.8.0 routed requirements — `coordination`", text)
        self.assertIn("## spec/drafts/0.8.0/coordination.md", text)
        self.assertIn("- **AWP-", text)
        self.assertIn("## Schema digests", text)
        self.assertIn("schemas/awp-cooperation-0.1.schema.json", text)
        self.assertNotIn('"$schema"', text, "digests must not inline the schema")

    def test_schema_digest_is_compact_and_lists_definitions(self) -> None:
        import json

        digest = self.entry.schema_digest("schemas/awp-cooperation-0.1.schema.json")
        self.assertIn("binding", digest["definitions"])
        self.assertIn("participantLease", digest["definitions"])
        self.assertEqual(digest["definitions"]["binding"]["const"]["type"], "cooperation_binding")
        self.assertIn("COOP-1", digest["definitions"]["binding"]["enums"]["contract"])
        self.assertLess(len(json.dumps(digest)), digest["bytes"] * 0.35)

    def test_bundle_carries_asset_digests_not_asset_bodies(self) -> None:
        bundle = (ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-draft.bundle.md").read_text(encoding="utf-8")
        assets = (ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-draft.assets.md").read_text(encoding="utf-8")
        self.assertTrue("| Requirement inventory | `spec/drafts/0.8.0/requirements.json` |" in bundle)
        # The embedded-asset sections moved to the companion file; prose modules keep their own JSON examples.
        for heading in ("## Requirement inventory —", "## Core schema —", "## Cooperation schema —"):
            self.assertFalse(heading in bundle, f"{heading} should not be embedded in the bundle")
            self.assertTrue(heading in assets, f"{heading} missing from the assets companion")
        self.assertFalse('"normative_authority"' in bundle)
        self.assertTrue('"normative_authority"' in assets)


if __name__ == "__main__":
    unittest.main()
