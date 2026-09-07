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


if __name__ == "__main__":
    unittest.main()
