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
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


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


def _decision_applies(decision: dict, action: dict) -> bool:
    affects = _as_list(decision.get("affects"))
    if not affects:
        return False
    targets = [t for t in (action.get("resource"), action.get("artifact_class")) if t]
    return any(_matches_selector(affects, target) for target in targets)


def resolve_action(
    action: dict,
    guardrails: Sequence[dict],
    decisions: Sequence[dict],
    entry_status: dict,
    *,
    action_digest: str | None = None,
    capsule_digest: str | None = None,
) -> dict:
    """Compute one action-resolution record for `action`.

    `guardrails` and `decisions` are whatever the caller was able to load
    (possibly a budget-limited subset -- that is exactly what
    `entry_status` communicates). A deny found among them is honored
    immediately, because incomplete visibility elsewhere cannot turn a
    known prohibition into a permit. A permit is reached only when both
    completeness axes are `complete` and nothing applicable blocks it.
    """
    diagnostics: list[str] = []

    applicable_guardrails = [g for g in guardrails if _guardrail_applies(g, action)]
    applicable_decisions = [d for d in decisions if _decision_applies(d, action)]

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
    if deny_guardrails:
        result = RESULT_DENY
    elif invalid_owner_guardrails:
        result = RESULT_UNRESOLVED
    elif selection != "complete" or decision_context != "complete":
        if not diagnostics:
            diagnostics.append(DIAG_DECISION_CONTEXT_INCOMPLETE)
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
        requirements.extend(_as_list(decision.get("requirements")))

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
    resolution = resolve_action(action, guardrails, decisions, entry_status)
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
    resolve.set_defaults(func=_cmd_resolve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
