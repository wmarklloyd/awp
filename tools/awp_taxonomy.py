"""Versioned concept taxonomies for AWP Action Boundary semantic inheritance.

Prototype for the design note "AWP semantic inheritance for guarded work"
(android_sports_watches/docs/awp-semantic-inheritance-design-note.md,
2026-09-14): the Action Boundary resolver (tools/awp_action_boundary.py)
reliably enforces a rule against an explicit selector, but cannot on its own
establish that a validated child concept ("a Collie") should inherit a rule
declared against its parent ("dogs"). Informal model reasoning about that
relationship is not a stable enforcement mechanism -- it can be missed,
over-applied, or change between sessions -- and keyword matching does not
know a Collie is a dog either. This module gives that relationship a stable,
versioned, machine-checked home: a policy owner declares concept IDs and
directional `is-a` edges once; the resolver then answers "does this action's
concept descend from that selector's concept" deterministically.

Design commitments carried over from the note, load-bearing for the rest of
this module:

  - Only directional `is-a` edges are supported in this first version.
    Looser relationships (resembles, often-used-with, marketed-as) MUST NOT
    silently inherit requirements, so `Taxonomy.from_dict` rejects any edge
    whose `relation` is not in SUPPORTED_RELATIONS rather than trying to
    interpret it.
  - Validation is fail-closed and happens once, at load time: an edge naming
    a concept that isn't declared, a cyclic ancestry, or a malformed record
    raises TaxonomyError immediately. A taxonomy a caller could only
    partially trust is not something this module hands back as usable --
    the caller gets an exception, not a degraded object.
  - `ancestors()` raises TaxonomyError for a concept unknown to this
    taxonomy version, for the same reason: an unresolved classification
    must fail closed, never silently resolve to "no ancestors" (which would
    look identical to a concept that legitimately has no parent).

This module does not decide which concept an action belongs to -- that
classification (a model's proposed mapping, or a fixed concept declared on a
protected-paths entry) is the caller's job, exactly as the design note
scopes it: "A model may propose a mapping, but the resolver accepts it only
when the concept exists in the selected, validated taxonomy version."
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# The first version supports only directional is-a edges (design note,
# "Proposed model / Versioned taxonomy"). Adding a relation type here is a
# deliberate policy decision, not a parsing convenience -- it changes what
# the resolver is willing to let silently inherit requirements.
SUPPORTED_RELATIONS = frozenset({"is-a"})


class TaxonomyError(Exception):
    """The taxonomy is malformed, cyclic, or otherwise not fit to enforce against."""


class Taxonomy:
    """A versioned, validated set of concept IDs and `is-a` edges.

    Construct via `Taxonomy.from_dict` / `Taxonomy.from_file`, not directly --
    those are what run the fail-closed validation this module promises.
    """

    def __init__(
        self,
        version: str,
        concepts: frozenset[str],
        edges: tuple[tuple[str, str], ...],
        digest: str,
    ) -> None:
        self.version = version
        self.concepts = concepts
        self.edges = edges
        self.digest = digest
        parents: dict[str, list[str]] = {}
        for child, parent in edges:
            parents.setdefault(child, []).append(parent)
        # Deterministic order: the order edges were declared in the file.
        self._parents = {child: tuple(values) for child, values in parents.items()}

    def parents_of(self, concept: str) -> tuple[str, ...]:
        """Direct parents of `concept` (empty if it is a root or unknown)."""
        return self._parents.get(concept, ())

    def ancestors(self, concept: str) -> list[str]:
        """`concept`'s ancestors, nearest first, per validated `is-a` edges.

        Raises TaxonomyError if `concept` is not declared in this taxonomy
        version -- an unresolved classification must fail closed rather than
        silently returning "no ancestors", which would be indistinguishable
        from a legitimately rootless concept.
        """
        if concept not in self.concepts:
            raise TaxonomyError(
                f"concept {concept!r} is not defined in taxonomy {self.version!r}"
            )
        ordered: list[str] = []
        seen = {concept}
        frontier = [concept]
        while frontier:
            next_frontier: list[str] = []
            for node in frontier:
                for parent in self._parents.get(node, ()):
                    if parent in seen:
                        continue
                    seen.add(parent)
                    ordered.append(parent)
                    next_frontier.append(parent)
            frontier = next_frontier
        return ordered

    @classmethod
    def from_dict(cls, data: Any) -> "Taxonomy":
        if not isinstance(data, dict):
            raise TaxonomyError("taxonomy must be a JSON object")
        version = data.get("taxonomy")
        if not isinstance(version, str) or not version.strip():
            raise TaxonomyError("taxonomy requires a nonempty 'taxonomy' version string")

        raw_concepts = data.get("concepts")
        if not isinstance(raw_concepts, list) or not raw_concepts:
            raise TaxonomyError("taxonomy requires a nonempty 'concepts' array")
        concept_ids: list[str] = []
        for entry in raw_concepts:
            if isinstance(entry, str):
                concept_id = entry
            elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
                concept_id = entry["id"]
            else:
                raise TaxonomyError(f"malformed concept entry: {entry!r}")
            if not concept_id.strip():
                raise TaxonomyError("concept id must be a nonempty string")
            concept_ids.append(concept_id)
        if len(set(concept_ids)) != len(concept_ids):
            raise TaxonomyError("taxonomy declares a duplicate concept id")
        concepts = frozenset(concept_ids)

        raw_edges = data.get("edges", [])
        if not isinstance(raw_edges, list):
            raise TaxonomyError("taxonomy 'edges' must be an array")
        edges: list[tuple[str, str]] = []
        for edge in raw_edges:
            if not isinstance(edge, dict):
                raise TaxonomyError(f"malformed edge: {edge!r}")
            child = edge.get("child")
            parent = edge.get("parent")
            relation = edge.get("relation")
            if relation not in SUPPORTED_RELATIONS:
                raise TaxonomyError(
                    f"unsupported relation {relation!r} on edge {child!r}->{parent!r}; "
                    f"only {sorted(SUPPORTED_RELATIONS)} are enforceable"
                )
            if not isinstance(child, str) or child not in concepts:
                raise TaxonomyError(f"edge child {child!r} is not a declared concept")
            if not isinstance(parent, str) or parent not in concepts:
                raise TaxonomyError(f"edge parent {parent!r} is not a declared concept")
            if child == parent:
                raise TaxonomyError(f"concept {child!r} cannot be its own parent")
            edges.append((child, parent))

        _reject_cycles(concepts, edges)

        digest = _digest_of(
            {
                "taxonomy": version,
                "concepts": sorted(concepts),
                "edges": sorted(edges),
            }
        )
        return cls(version=version, concepts=concepts, edges=tuple(edges), digest=digest)

    @classmethod
    def from_file(cls, path: str | Path) -> "Taxonomy":
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise TaxonomyError(f"taxonomy file unavailable: {error}") from error
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise TaxonomyError(f"taxonomy file is not valid JSON: {error}") from error
        return cls.from_dict(data)


def _reject_cycles(concepts: frozenset[str], edges: list[tuple[str, str]]) -> None:
    """Fail closed on a cyclic `is-a` graph (design note: "Safe failure
    behavior": "an edge is cyclic, unsupported, or untrusted" must produce
    unresolved, not a taxonomy that quietly loops). Standard three-color DFS
    over the child->parent direction.
    """
    parents: dict[str, list[str]] = {}
    for child, parent in edges:
        parents.setdefault(child, []).append(parent)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {concept: WHITE for concept in concepts}

    def visit(node: str, path: list[str]) -> None:
        color[node] = GRAY
        for parent in parents.get(node, ()):
            if color[parent] == GRAY:
                cycle = " -> ".join([*path, node, parent])
                raise TaxonomyError(f"taxonomy contains a cyclic is-a chain: {cycle}")
            if color[parent] == WHITE:
                visit(parent, [*path, node])
        color[node] = BLACK

    for concept in concepts:
        if color[concept] == WHITE:
            visit(concept, [])


def _digest_of(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
