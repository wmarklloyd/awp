"""Tests for tools/awp_taxonomy.py, the concept-taxonomy prototype for the
design note "AWP semantic inheritance for guarded work"
(android_sports_watches/docs/awp-semantic-inheritance-design-note.md).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.awp_taxonomy import Taxonomy, TaxonomyError  # noqa: E402


ANIMAL_TAXONOMY = {
    "taxonomy": "animal-imagery-2026-09-14",
    "concepts": ["concept:animal", "concept:dog", "concept:collie"],
    "edges": [
        {"child": "concept:dog", "relation": "is-a", "parent": "concept:animal"},
        {"child": "concept:collie", "relation": "is-a", "parent": "concept:dog"},
    ],
}


class TaxonomyLoadingTests(unittest.TestCase):
    def test_ancestors_are_nearest_first(self) -> None:
        taxonomy = Taxonomy.from_dict(ANIMAL_TAXONOMY)
        self.assertEqual(taxonomy.ancestors("concept:collie"), ["concept:dog", "concept:animal"])

    def test_root_concept_has_no_ancestors(self) -> None:
        taxonomy = Taxonomy.from_dict(ANIMAL_TAXONOMY)
        self.assertEqual(taxonomy.ancestors("concept:animal"), [])

    def test_unknown_concept_fails_closed(self) -> None:
        taxonomy = Taxonomy.from_dict(ANIMAL_TAXONOMY)
        with self.assertRaises(TaxonomyError):
            taxonomy.ancestors("concept:lassie")

    def test_digest_is_deterministic_and_content_bound(self) -> None:
        first = Taxonomy.from_dict(ANIMAL_TAXONOMY)
        second = Taxonomy.from_dict(dict(ANIMAL_TAXONOMY))
        self.assertEqual(first.digest, second.digest)
        changed = Taxonomy.from_dict(
            {**ANIMAL_TAXONOMY, "concepts": [*ANIMAL_TAXONOMY["concepts"], "concept:labrador"]}
        )
        self.assertNotEqual(first.digest, changed.digest)

    def test_cyclic_is_a_chain_is_rejected(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict(
                {
                    "taxonomy": "cyclic",
                    "concepts": ["concept:a", "concept:b"],
                    "edges": [
                        {"child": "concept:a", "relation": "is-a", "parent": "concept:b"},
                        {"child": "concept:b", "relation": "is-a", "parent": "concept:a"},
                    ],
                }
            )

    def test_self_referential_edge_is_rejected(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict(
                {
                    "taxonomy": "self-loop",
                    "concepts": ["concept:a"],
                    "edges": [{"child": "concept:a", "relation": "is-a", "parent": "concept:a"}],
                }
            )

    def test_unsupported_relation_is_rejected(self) -> None:
        """Design note: "Looser relationships such as resembles,
        often-used-with, or marketed-as must not silently inherit
        requirements." Only is-a is enforceable in this first version.
        """
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict(
                {
                    "taxonomy": "loose",
                    "concepts": ["concept:a", "concept:b"],
                    "edges": [{"child": "concept:a", "relation": "resembles", "parent": "concept:b"}],
                }
            )

    def test_edge_naming_an_undeclared_concept_is_rejected(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict(
                {
                    "taxonomy": "dangling",
                    "concepts": ["concept:a"],
                    "edges": [{"child": "concept:a", "relation": "is-a", "parent": "concept:ghost"}],
                }
            )

    def test_duplicate_concept_id_is_rejected(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict(
                {"taxonomy": "dup", "concepts": ["concept:a", "concept:a"], "edges": []}
            )

    def test_missing_taxonomy_version_is_rejected(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_dict({"concepts": ["concept:a"], "edges": []})

    def test_from_file_reports_a_taxonomy_error_not_a_bare_os_error(self) -> None:
        with self.assertRaises(TaxonomyError):
            Taxonomy.from_file("/nonexistent/path/taxonomy.json")

    def test_from_file_reports_a_taxonomy_error_on_invalid_json(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "taxonomy.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(TaxonomyError):
                Taxonomy.from_file(path)


if __name__ == "__main__":
    unittest.main()
