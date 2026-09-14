"""Reference resolver for the AWP Action Boundary module (urn:awp:action-boundary 0.3.0).

This is a first-pass, standalone implementation of the resolution logic
described in spec/drafts/0.8.0/action-boundary.md sections 3-5: it combines
a Security 0.5 guardrail evaluation (security.md section 4) with Handoff's
two-axis decision_context completeness check, plus this module's
`generative:freeform` / `generative:composite` operation-class convention,
into one action-resolution record.

It is intentionally capsule-agnostic: it takes plain guardrail, decision,
and entry-status structures (as dicts, or JSON files via the CLI) rather
than parsing an .awp.md capsule directly. This mirrors how the silo-v1
module shipped a structural schema and fixtures before a binding -- the
capsule-reading integration is a follow-up (open-issues.md #46), not part
of this first pass.

An enforcement adapter (a CI gate, a tool gateway) is expected to call
`resolve_action` with a freshly loaded guardrail/decision/entry-status set
-- recomputed at the point of enforcement, never trusting a resolution
handed to it by the participant being gated -- and act on the `result`
field: reject the operation unless it is exactly ``"permit"``.

Optionally, a caller MAY also pass a `taxonomy` (tools/awp_taxonomy.py,
built for the design note "AWP semantic inheritance for guarded work",
android_sports_watches/docs/awp-semantic-inheritance-design-note.md) so an
action whose `concept` is a validated descendant of a guardrail's or
decision's own concept selector inherits that rule -- the "a Collie is a
dog" problem the note names: explicit-selector matching alone cannot
establish that relationship, and informal model reasoning about it is not
stable enforcement. This is strictly additive and off by default:
`concept_mode="observe"` (the default whenever a taxonomy is passed) never
changes `result` -- it only attaches a `concept_resolution` record so a
policy owner can review what concept inheritance *would* have matched
before trusting it. Passing `concept_mode="enforce"` is what actually folds
a concept-matched guardrail or decision into `applicable_guardrails` /
`applicable_decisions`, per the design note's own step 7 ("Roll out in
observe-only mode... then enable enforcement for one owner-approved
scope").
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

# Keep both invocation forms working: `python tools/awp_action_boundary.py`
# and `python -m tools.awp_action_boundary` (mirrors tools/awp_ci_gate.py's
# own bootstrap for the same reason).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.awp_taxonomy import Taxonomy, TaxonomyError  # noqa: E402


PROFILE = "action-boundary-resolver-v1"

# Reserved operation classes (action-boundary.md section 3).
GENERATIVE_FREEFORM = "generative:freeform"
GENERATIVE_COMPOSITE = "generative:composite"

RESULT_PERMIT = "permit"
RESULT_DENY = "deny"
RESULT_UNRESOLVED = "unresolved"

DIAG_DECISION_CONTEXT_INCOMPLETE = "AWP-ACTION-DECISION-CONTEXT-INCOMPLETE"
DIAG_GUARDRAIL_OWNER_INVALID = "AWP-ACTION-GUARDRAIL-OWNER-INVALID"
DIAG_RESOLUTION_REQUIRED = "AWP-ACTION-DECISION-RESOLUTION-REQUIRED"
DIAG_CONCEPT_UNRESOLVED = "AWP-ACTION-CONCEPT-UNRESOLVED"

CONCEPT_MODE_OBSERVE = "observe"
CONCEPT_MODE_ENFORCE = "enforce"
CONCEPT_MODES = (CONCEPT_MODE_OBSERVE, CONCEPT_MODE_ENFORCE)


class ActionBoundaryError(Exception):
    """Raised for malformed inputs to the resolver, not for a deny/unresolved result."""


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _matches_selector(candidates: Iterable[str], target: str) -> bool:
    """Match a guardrail/decision selector against an action's resource or
    artifact class. Supports exact identifiers and glob-style patterns
    (fnmatch), per action-boundary.md section 3.1 -- a selector authored
    before a target exists must still match it later.
    """
    for candidate in candidates:
        if not candidate:
            continue
        if candidate == target:
            return True
        if any(ch in candidate for ch in "*?[") and fnmatch.fnmatch(target, candidate):
            return True
    return False


def _guardrail_applies(guardrail: dict, action: dict) -> bool:
    operation_classes = _as_list(guardrail.get("operation_classes"))
    if action.get("operation_class") not in operation_classes:
        return False
    resources = _as_list(guardrail.get("resources"))
    targets = [t for t in (action.get("resource"), action.get("artifact_class")) if t]
    return any(_matches_selector(resources, target) for target in targets)


MODULE_ID = "urn:awp:action-boundary"


def _module_extension(decision: dict) -> dict:
    """Return this module's extension object on a decision record, per
    core.md's `modules.{module-id}` convention (core.md section "Records":
    "An optional module extending a Core record places its fields under
    `modules.{module-id}`."). Core's own `affects` field is a record/artifact
    reference array for Core's decision-closure algorithm -- it is not a
    glob-matchable selector, and this module MUST NOT reinterpret it
    (core.md, same section: "Optional modules MAY extend applicability, but
    they MUST NOT replace or reinterpret the Core `affects` and `supersedes`
    fields."). A decision with no `modules.urn:awp:action-boundary` entry
    simply does not participate in this module's action resolution -- it
    may still matter to Core's own closure, independently.
    """
    modules = decision.get("modules")
    if not isinstance(modules, dict):
        return {}
    extension = modules.get(MODULE_ID)
    return extension if isinstance(extension, dict) else {}


def _decision_applies(decision: dict, action: dict) -> bool:
    selectors = _as_list(_module_extension(decision).get("selectors"))
    if not selectors:
        return False
    targets = [t for t in (action.get("resource"), action.get("artifact_class")) if t]
    return any(_matches_selector(selectors, target) for target in targets)


def _concept_selectors(record: dict) -> list[dict]:
    """Read a guardrail's or decision's concept selectors, per core.md's
    `modules.{module-id}` extension convention (the same namespace
    `_module_extension` already reads `selectors`/`requirements` from --
    concept selectors live alongside them, not in a separate mechanism).

    Each entry is `{"concept": <declared concept id>, "include_descendants":
    <bool>}`. `include_descendants` defaults to False: per the design note,
    "Without include_descendants, a Dog rule does not automatically apply to
    a Collie. This prevents accidental expansion of policy scope" -- a
    concept selector opts into inheritance explicitly, it is never implied.
    """
    entries = _as_list(_module_extension(record).get("concepts"))
    selectors = []
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("concept"), str) and entry["concept"].strip():
            selectors.append(
                {
                    "concept": entry["concept"],
                    "include_descendants": bool(entry.get("include_descendants", False)),
                }
            )
    return selectors


def resolve_concept_inheritance(
    action: dict,
    guardrails: Sequence[dict],
    decisions: Sequence[dict],
    taxonomy: "Any | None",
) -> dict:
    """Compute which guardrails/decisions an action's declared `concept`
    matches through validated `is-a` inheritance (tools/awp_taxonomy.py),
    independent of ordinary resource/artifact-class selector matching.

    Returns a record with a `state`:

      - "not_applicable": the action declares no `concept`, or no taxonomy
        was supplied. Concept inheritance simply does not participate.
      - "resolved": the concept exists in the taxonomy; `chain` is the
        concept followed by its ancestors, nearest first; `matched_*` list
        the ids of every guardrail/decision whose concept selector matched
        -- either exactly (the selector's concept equals the action's own
        concept) or, when `include_descendants` is set, an ancestor in
        `chain`. Per the design note, "Mandatory requirements accumulate":
        this deliberately does not pick just the nearest match and stop --
        every matching level contributes, so a Collie-specific decision can
        add to a Dog decision's requirements but structurally can never
        cause them to be dropped.
      - "unresolved": the concept is unknown to this taxonomy version, or
        the taxonomy itself failed validation. Per the design note's "Safe
        failure behavior": this MUST NOT quietly fall back to a
        less-specific rule or to no rule -- see how `resolve_action` treats
        this state under `concept_mode="enforce"`.
    """
    concept = action.get("concept")
    if not concept or taxonomy is None:
        return {"state": "not_applicable"}

    version = getattr(taxonomy, "version", None)
    try:
        ancestors = taxonomy.ancestors(concept)
    except TaxonomyError as error:
        return {"state": "unresolved", "reason": str(error), "taxonomy_version": version}
    except AttributeError as error:  # pragma: no cover - defensive, malformed caller input
        return {"state": "unresolved", "reason": f"invalid taxonomy object: {error}", "taxonomy_version": version}

    chain = [concept, *ancestors]
    rank_of = {node: index for index, node in enumerate(chain)}

    def concept_matches(record: dict) -> bool:
        for selector in _concept_selectors(record):
            selector_concept = selector["concept"]
            if selector_concept not in rank_of:
                continue
            rank = rank_of[selector_concept]
            if rank == 0 or selector["include_descendants"]:
                return True
        return False

    def matched_guardrails(records: Sequence[dict]) -> list[str]:
        ids: list[str] = []
        for record in records:
            record_id = record.get("id")
            if not record_id or not concept_matches(record):
                continue
            # A guardrail's operation_classes scope what it governs exactly
            # as _guardrail_applies already requires for ordinary
            # resource-selector matching (action-boundary.md section 3); a
            # concept match is a different way of establishing *which*
            # target a guardrail covers, not a way around that scope. A
            # freeform-only deny must not reach a composite action just
            # because their concepts happen to line up.
            if action.get("operation_class") not in _as_list(record.get("operation_classes")):
                continue
            ids.append(record_id)
        return ids

    def matched_decisions(records: Sequence[dict]) -> list[str]:
        # Decisions carry no operation_class of their own (_decision_applies
        # does not filter by it either) -- a decision's requirements apply
        # to the concept regardless of operation class.
        return [record["id"] for record in records if record.get("id") and concept_matches(record)]

    return {
        "state": "resolved",
        "taxonomy_version": version,
        "taxonomy_digest": getattr(taxonomy, "digest", None),
        "concept": concept,
        "chain": chain,
        "matched_guardrails": matched_guardrails(guardrails),
        "matched_decisions": matched_decisions(decisions),
    }


def _merge_by_id(base: list[dict], extra: list[dict]) -> list[dict]:
    """Union two record lists, de-duplicated by `id`, preserving `base`'s
    order and appending any new ids from `extra`. Used to fold
    concept-matched guardrails/decisions into ordinarily-matched ones under
    `concept_mode="enforce"` without ever double-counting a record matched
    both ways.
    """
    seen = {record.get("id") for record in base if record.get("id")}
    merged = list(base)
    for record in extra:
        record_id = record.get("id")
        if record_id and record_id in seen:
            continue
        if record_id:
            seen.add(record_id)
        merged.append(record)
    return merged


def resolve_action(
    action: dict,
    guardrails: Sequence[dict],
    decisions: Sequence[dict],
    entry_status: dict,
    *,
    action_digest: str | None = None,
    capsule_digest: str | None = None,
    taxonomy: "Any | None" = None,
    concept_mode: str = CONCEPT_MODE_OBSERVE,
) -> dict:
    """Compute one action-resolution record for `action`.

    `guardrails` and `decisions` are whatever the caller was able to load
    (possibly a budget-limited subset -- that is exactly what
    `entry_status` communicates). A deny found among them is honored
    immediately, because incomplete visibility elsewhere cannot turn a
    known prohibition into a permit. A permit is reached only when both
    completeness axes are `complete` and nothing applicable blocks it.

    `taxonomy` (an `awp_taxonomy.Taxonomy`, optional) and `concept_mode`
    together control semantic-inheritance resolution (see the module
    docstring and `resolve_concept_inheritance`). Omitting `taxonomy`
    reproduces this function's exact pre-existing behavior byte-for-byte --
    no `concept_resolution` key is even added to the returned record. When
    `taxonomy` is supplied, `concept_mode` defaults to `"observe"`: concept
    inheritance is computed and reported for review, but never changes
    `applicable_guardrails`, `applicable_decisions`, or `result`. Only
    `concept_mode="enforce"` folds a concept-matched guardrail or decision
    into the ordinary resolution -- and, symmetrically, an unresolved
    concept classification under `"enforce"` forces `result` to
    `"unresolved"` rather than letting an ambiguous classification silently
    fall through to whatever the non-concept selectors alone would have
    decided.
    """
    if concept_mode not in CONCEPT_MODES:
        raise ActionBoundaryError(f"concept_mode must be one of {CONCEPT_MODES}, got {concept_mode!r}")

    diagnostics: list[str] = []

    applicable_guardrails = [g for g in guardrails if _guardrail_applies(g, action)]
    applicable_decisions = [d for d in decisions if _decision_applies(d, action)]

    concept_resolution: dict | None = None
    if taxonomy is not None:
        concept_resolution = resolve_concept_inheritance(action, guardrails, decisions, taxonomy)
        concept_resolution["mode"] = concept_mode
        if concept_mode == CONCEPT_MODE_ENFORCE and concept_resolution["state"] == "resolved":
            concept_guardrails = [
                g for g in guardrails if g.get("id") in concept_resolution["matched_guardrails"]
            ]
            concept_decisions = [
                d for d in decisions if d.get("id") in concept_resolution["matched_decisions"]
            ]
            applicable_guardrails = _merge_by_id(applicable_guardrails, concept_guardrails)
            applicable_decisions = _merge_by_id(applicable_decisions, concept_decisions)

    selection = entry_status.get("selection")
    decision_context = entry_status.get("decision_context")

    # An applicable guardrail whose policy_owner is the acting participant
    # is invalid for this module's purposes (action-boundary.md section 3)
    # regardless of anything else -- it cannot be trusted to gate its own
    # author.
    actor = action.get("actor")
    invalid_owner_guardrails = [
        g for g in applicable_guardrails
        if actor is not None and g.get("policy_owner") == actor
    ]
    if invalid_owner_guardrails:
        diagnostics.append(DIAG_GUARDRAIL_OWNER_INVALID)

    deny_guardrails = [
        g for g in applicable_guardrails
        if g.get("effect") == "deny" and g not in invalid_owner_guardrails
    ]
    concept_unresolved_in_enforce = (
        concept_mode == CONCEPT_MODE_ENFORCE
        and concept_resolution is not None
        and concept_resolution["state"] == "unresolved"
    )
    if deny_guardrails:
        result = RESULT_DENY
    elif invalid_owner_guardrails:
        result = RESULT_UNRESOLVED
    elif selection != "complete" or decision_context != "complete":
        if not diagnostics:
            diagnostics.append(DIAG_DECISION_CONTEXT_INCOMPLETE)
        result = RESULT_UNRESOLVED
    elif concept_unresolved_in_enforce:
        # Design note, "Safe failure behavior": an unresolved classification
        # "must not quietly fall back to a less-specific rule or to no
        # rule." A known deny above still wins (it is already the most
        # restrictive outcome available), but nothing here may reach
        # permit while the action's own declared concept could not be
        # placed in the taxonomy.
        diagnostics.append(DIAG_CONCEPT_UNRESOLVED)
        result = RESULT_UNRESOLVED
    else:
        require_guardrails = [
            g for g in applicable_guardrails
            if g.get("effect") in ("require_authorization", "require_confirmation", "require_review")
        ]
        if require_guardrails:
            diagnostics.append(DIAG_RESOLUTION_REQUIRED)
            result = RESULT_UNRESOLVED
        else:
            result = RESULT_PERMIT

    requirements = []
    for decision in applicable_decisions:
        requirements.extend(_as_list(_module_extension(decision).get("requirements")))

    resolution = {
        "type": "action_resolution",
        "action": action,
        "action_digest": action_digest or _digest_of(action),
        "capsule_digest": capsule_digest or "sha256:" + "0" * 64,
        "selection": selection,
        "decision_context": decision_context,
        "applicable_guardrails": [g.get("id") for g in applicable_guardrails if g.get("id")],
        "applicable_decisions": [d.get("id") for d in applicable_decisions if d.get("id")],
        "requirements": requirements,
        "diagnostics": diagnostics,
        "result": result,
    }
    if concept_resolution is not None:
        resolution["concept_resolution"] = concept_resolution
    return resolution


def _digest_of(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_resolve(args: argparse.Namespace) -> int:
    action = _load_json(args.action)
    guardrails = _load_json(args.guardrails) if args.guardrails else []
    decisions = _load_json(args.decisions) if args.decisions else []
    entry_status = _load_json(args.entry_status) if args.entry_status else {
        "selection": "complete",
        "decision_context": "complete",
    }
    taxonomy = Taxonomy.from_file(args.taxonomy) if args.taxonomy else None
    resolution = resolve_action(
        action, guardrails, decisions, entry_status,
        taxonomy=taxonomy, concept_mode=args.concept_mode,
    )
    print(json.dumps(resolution, indent=2, sort_keys=True))
    if resolution["result"] == RESULT_PERMIT:
        return 0
    if resolution["result"] == RESULT_DENY:
        return 1
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser(
        "resolve",
        help="Resolve one action against guardrails/decisions/entry-status JSON files "
        "and print the action-resolution record. Exit code: 0 permit, 1 deny, 2 unresolved "
        "-- suitable as a CI-gate check.",
    )
    resolve.add_argument("--action", required=True, help="Path to an action JSON file.")
    resolve.add_argument("--guardrails", help="Path to a JSON array of applicable-candidate guardrails.")
    resolve.add_argument("--decisions", help="Path to a JSON array of applicable-candidate decisions.")
    resolve.add_argument(
        "--entry-status",
        help="Path to a JSON object with 'selection' and 'decision_context' "
        "(defaults to both 'complete' if omitted -- pass the real re-entry projection result).",
    )
    resolve.add_argument(
        "--taxonomy",
        help="Path to an awp_taxonomy.py concept-taxonomy JSON file, for semantic-inheritance "
        "resolution (design note: android_sports_watches/docs/awp-semantic-inheritance-design-note.md). "
        "Omit to reproduce plain selector-only resolution unchanged.",
    )
    resolve.add_argument(
        "--concept-mode",
        choices=list(CONCEPT_MODES),
        default=CONCEPT_MODE_OBSERVE,
        help="'observe' (default) records concept-inheritance matches for review without changing "
        "the result; 'enforce' folds them into applicable_guardrails/applicable_decisions and fails "
        "closed on an unresolved concept classification. Ignored unless --taxonomy is also given.",
    )
    resolve.set_defaults(func=_cmd_resolve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
