"""Reference harness core for AWP Action Boundary (urn:awp:action-boundary 0.3.1).

This module is the host-agnostic enforcement core the harness prototype is
built around. It is deliberately not written against any one agent runtime's
hook API: every function here takes and returns plain dicts/JSON, and the CLI
at the bottom of this file is callable by anything that can start a
subprocess and read stdout -- a Claude Code hook, a Codex session shelling
out to it, a CI job, a human at a terminal. Cross-agent compatibility in this
design does not come from writing one adapter per agent; it comes from
putting the actual decision point somewhere no agent-specific integration is
required to reach it at all. adapters/ under this repository root holds two
concrete, deliberately thin bindings on top of this core:

  - adapters/claude-code-hooks/ -- an illustrative, advisory-only binding to
    Claude Code's PreToolUse/PostToolUse/Stop hook contract (verified against
    https://code.claude.com/docs/en/hooks, 2026-09-13). It is fast local
    feedback, not enforcement -- action-boundary.md section 7 already states
    that a hook a participant's own host executes is not an independent
    enforcement point, the same way a commit hook is inadequate. It can be
    disabled, bypassed by a shell escape, or simply not exist for a different
    host, and this harness does not claim otherwise.
  - tools/awp_ci_gate.py -- the actual `action-enforced`-tier binding. It
    runs after any agent's (or any human's) change lands in a diff, and does
    not know or care which agent produced it. This is what makes the
    guarantee cross-agent: enforcement that does not depend on the acting
    party's cooperation applies equally regardless of which acting party it
    was.

Record-shape corrections applied here (see research/model-assisted-reviews/
codex-harness-reconciliation-evaluation.md, the four numbered corrections,
and awp-harness-reconciliation-brief.md for the exchange that produced them):

  1. Decision `source` is not authorship (correction 1). `propose_decision`
     below returns a clean, portable Core decision record plus a *separate*
     host-local provenance dict -- it never writes an unqualified authorship
     field onto the record itself, and it never uses Core `source` for
     anything but an actual supporting artifact reference.
  2. Decision selectors and `requirements` already moved to
     `modules."urn:awp:action-boundary"` in action-boundary.md 0.3.1 (see
     tools/awp_action_boundary.py's `_module_extension`); this harness reuses
     that, and reuses the module's `MODULE_ID` constant rather than
     hardcoding the URN a second time.
  3. This harness reports against action-boundary's existing five-level
     conformance ladder (context-aware / decision-resolved / action-bound /
     action-enforced / output-attested) -- see `conformance_levels_achieved`
     below -- not a new, parallel taxonomy.
  4. A session-end compliance assessment is produced as a Core
     `execution`/`claim`/`evidence` triple (correction 4), not a `change` or
     `checkpoint` -- see `session_compliance_report`.

Fields this harness needs that neither Core nor action-boundary 0.3.1 define
(`invocation_binding`'s internal shape, and small descriptive fields on the
compliance triple) are namespaced under `modules."urn:awp:harness-runtime"`
rather than added to a Core or action-boundary record unqualified -- the
exact discipline core.md's extension rule requires, and the one the resolver
itself violated before the 0.3.1 fix. `urn:awp:harness-runtime` is an
informative, host-local namespace, not a registered AWP payload module; per
adapters.md section 1, an adapter is not automatically a payload module, and
this harness does not introduce a portable record that must survive outside
this prototype.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from tools.awp_action_boundary import (
    MODULE_ID,
    RESULT_DENY,
    RESULT_PERMIT,
    RESULT_UNRESOLVED,
    _module_extension,
    resolve_action,
)

HARNESS_NS = "urn:awp:harness-runtime"
INVOCATION_DIGEST_DOMAIN = "awp-harness-invocation-binding-v1"
INDEX_DIGEST_DOMAIN = "awp-harness-decision-index-v1"

DIAG_INVOCATION_BINDING_MISSING = "AWP-HARNESS-INVOCATION-BINDING-MISSING"
DIAG_INVOCATION_MISMATCH = "AWP-HARNESS-INVOCATION-MISMATCH"

CONFORMANCE_LEVELS = (
    "context-aware",
    "decision-resolved",
    "action-bound",
    "action-enforced",
    "output-attested",
)


class HarnessError(Exception):
    """Raised for a harness-level misuse (not a deny/unresolved resolution)."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _domain_digest(payload: bytes, domain: str) -> str:
    h = hashlib.sha256()
    h.update(domain.encode("utf-8"))
    h.update(b"\x00")
    h.update(payload)
    return "sha256:" + h.hexdigest()


# ---------------------------------------------------------------------------
# Stage 0: Decision Index (budget-bounded projection, informative only)
# ---------------------------------------------------------------------------

def decision_index(
    decisions: Sequence[dict],
    *,
    capsule_digest: str,
    frontier: str | None = None,
    budget_bytes: int = 2048,
    generated_at: str | None = None,
) -> dict:
    """A budget-bounded projection of the action-boundary-relevant decisions.

    This has no normative status (core.md's own decision-closure algorithm
    remains authoritative). Its only purpose is to survive a bounded-context
    entry by putting a small, durable signal where an agent will see it at
    turn zero -- the same rationale DeepSeek's original Decision Index
    proposal gave, kept here as a genuinely useful idea independent of the
    record-shape corrections. Only decisions carrying this module's
    extension (`modules."urn:awp:action-boundary"`) are included -- a
    decision without it does not participate in action-boundary resolution
    (see action-boundary.md section 3.1) and would be misleading to list
    here as if it did.
    """
    entries = []
    for d in decisions:
        ext = _module_extension(d)
        selectors = ext.get("selectors")
        if not selectors:
            continue
        if isinstance(selectors, dict):
            flat = list(selectors.get("resources", [])) + list(selectors.get("artifact_classes", []))
        elif isinstance(selectors, list):
            flat = list(selectors)
        else:
            flat = []
        entries.append(
            {
                "id": d.get("id"),
                "revision": d.get("revision"),
                "choice": d.get("choice"),
                "affects_summary": ", ".join(flat) if flat else None,
                "status": d.get("status"),
            }
        )

    projection = {
        "kind": "projection",
        "projection_of": "action-boundary-decision-selectors",
        "capsule_digest": capsule_digest,
        "frontier": frontier,
        "generated_at": generated_at or _utc_now_iso(),
        "decisions": entries,
        "truncated": False,
    }
    encoded = _canonical_json(projection)
    if len(encoded) > budget_bytes:
        trimmed = [
            {"id": e["id"], "affects_summary": e["affects_summary"], "status": e["status"]}
            for e in entries
        ]
        projection = dict(projection, decisions=trimmed, truncated=True)
        encoded = _canonical_json(projection)
    projection["index_digest"] = _domain_digest(encoded, INDEX_DIGEST_DOMAIN)
    return projection


# ---------------------------------------------------------------------------
# Invocation binding: bind a resolution to the exact tool call it was for
# ---------------------------------------------------------------------------

def compute_invocation_binding(
    *,
    tool_name: str,
    tool_version: str | None,
    arguments: dict,
    action_digest: str,
    capsule_digest: str,
    computed_at: str | None = None,
) -> dict:
    """Build a structured `invocation_binding`, not a bare digest.

    Per the reconciliation evaluation's "Tool-invocation binding" section:
    canonical serialization, tool identity+version, a named digest algorithm
    and domain-separated digest, and explicit binding to the action and
    capsule state it was computed against. This function alone is not
    enforcement -- see `verify_invocation`, which an enforcement adapter
    calls against the *actual* intercepted call, never trusting a value the
    gated participant supplied.
    """
    canonical_args = _canonical_json(arguments)
    return {
        "type": "invocation_binding",
        "tool": tool_name,
        "tool_version": tool_version,
        "digest_algorithm": "sha256",
        "domain": INVOCATION_DIGEST_DOMAIN,
        "arguments_digest": _domain_digest(canonical_args, INVOCATION_DIGEST_DOMAIN),
        "action_digest": action_digest,
        "capsule_digest": capsule_digest,
        "computed_at": computed_at or _utc_now_iso(),
    }


def verify_invocation(resolution: dict, *, tool_name: str, tool_version: str | None, arguments: dict) -> tuple[bool, list[str]]:
    """Recompute the invocation binding from the actual call and compare.

    This is the gateway-side recomputation the evaluation calls out as the
    part a bare digest field cannot provide by itself: a mismatch here means
    the resolution that was granted does not describe what is actually about
    to happen (arguments changed, or no binding was ever declared), and the
    caller MUST NOT treat the resolution's `result` as still valid.
    """
    declared = resolution.get("invocation_binding")
    if not declared:
        return False, [DIAG_INVOCATION_BINDING_MISSING]
    recomputed = compute_invocation_binding(
        tool_name=tool_name,
        tool_version=tool_version,
        arguments=arguments,
        action_digest=resolution.get("action_digest", ""),
        capsule_digest=resolution.get("capsule_digest", ""),
    )
    mismatched = [
        field
        for field in ("tool", "tool_version", "arguments_digest", "action_digest", "capsule_digest")
        if recomputed.get(field) != declared.get(field)
    ]
    if mismatched:
        return False, [f"{DIAG_INVOCATION_MISMATCH}:{','.join(mismatched)}"]
    return True, []


# ---------------------------------------------------------------------------
# Event log (append-only JSONL of action-resolution records)
# ---------------------------------------------------------------------------

def _append_event(path: str | Path, record: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, ensure_ascii=False))
        f.write("\n")


def _read_event_log(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    entries = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---------------------------------------------------------------------------
# Stage 2/3: gate a contemplated action, optionally binding and logging it
# ---------------------------------------------------------------------------

def gate(
    action: dict,
    guardrails: Sequence[dict],
    decisions: Sequence[dict],
    entry_status: dict,
    *,
    tool_name: str | None = None,
    tool_version: str | None = None,
    tool_arguments: dict | None = None,
    action_digest: str | None = None,
    capsule_digest: str | None = None,
    event_log_path: str | Path | None = None,
) -> tuple[dict, int]:
    """Resolve one action, optionally bind it to a concrete tool call, and
    optionally log it. Returns (resolution, exit_code) -- exit_code follows
    tools/awp_action_boundary.py's convention (0 permit, 1 deny, 2
    unresolved) so a caller (hook, CI step, or a human at a shell) can use
    this function's result directly as a process exit status.
    """
    resolution = resolve_action(
        action, guardrails, decisions, entry_status,
        action_digest=action_digest, capsule_digest=capsule_digest,
    )
    if tool_name is not None:
        resolution["invocation_binding"] = compute_invocation_binding(
            tool_name=tool_name,
            tool_version=tool_version,
            arguments=tool_arguments or {},
            action_digest=resolution["action_digest"],
            capsule_digest=resolution["capsule_digest"],
        )
    if event_log_path is not None:
        _append_event(event_log_path, resolution)
    exit_code = {RESULT_PERMIT: 0, RESULT_DENY: 1, RESULT_UNRESOLVED: 2}[resolution["result"]]
    return resolution, exit_code


def enforce(resolution: dict, *, tool_name: str, tool_version: str | None, arguments: dict) -> tuple[dict, int]:
    """The actual enforcement step: recompute the invocation binding from the
    real call and downgrade a stale or mismatched `permit` to `deny`. A
    resolution that was never `permit` is returned unchanged -- a known deny
    or unresolved is not something a valid binding could upgrade.
    """
    if resolution.get("result") != RESULT_PERMIT:
        exit_code = {RESULT_PERMIT: 0, RESULT_DENY: 1, RESULT_UNRESOLVED: 2}[resolution["result"]]
        return resolution, exit_code
    ok, diagnostics = verify_invocation(resolution, tool_name=tool_name, tool_version=tool_version, arguments=arguments)
    if ok:
        return resolution, 0
    downgraded = dict(resolution)
    downgraded["result"] = RESULT_DENY
    downgraded["diagnostics"] = list(resolution.get("diagnostics", [])) + diagnostics
    return downgraded, 1


# ---------------------------------------------------------------------------
# Decision-capture UX: propose, then require explicit policy-owner acceptance
# ---------------------------------------------------------------------------

def propose_decision(
    *,
    decision_id: str,
    choice: str,
    rationale: str | None = None,
    selectors: list[str] | dict | None = None,
    requirements: list[str] | None = None,
    source_artifact: str | None = None,
    proposed_by_actor: str,
    occurred_at: str | None = None,
) -> tuple[dict, dict]:
    """Build a candidate Core decision record, status `proposed`, plus a
    *separate* host-local provenance dict describing who proposed it and
    when. The provenance is deliberately not written onto the decision
    record -- Core `source` names supporting evidence, not authorship
    (correction 1), and this harness does not repeat that conflation.
    Nothing returned here is binding: see `accept_decision`.
    """
    decision: dict = {"id": decision_id, "type": "decision", "status": "proposed", "choice": choice}
    if rationale:
        decision["rationale"] = rationale
    if source_artifact:
        decision["source"] = source_artifact
    extension: dict = {}
    if selectors:
        extension["selectors"] = selectors
    if requirements:
        extension["requirements"] = requirements
    if extension:
        decision["modules"] = {MODULE_ID: extension}

    provenance = {
        "kind": "harness_local_provenance",
        "note": "host-local capture metadata; not promoted into portable AWP state",
        "proposed_by_actor": proposed_by_actor,
        "proposed_at": occurred_at or _utc_now_iso(),
        "decision_id": decision_id,
    }
    return decision, provenance


def accept_decision(
    decision: dict,
    *,
    policy_owner: str,
    actor: str,
    proposed_by_actor: str | None = None,
    occurred_at: str | None = None,
) -> tuple[dict, dict]:
    """Promote a `proposed` decision to `accepted`.

    `policy_owner` legitimately equaling `actor` is the ordinary case -- the
    accountable human reviewing and accepting their own accountable
    decision -- and is not rejected. What action-boundary section 3's
    distinctness rule actually guards against, applied to decision capture,
    is self-dealing by the party whose incident or proposal produced the
    candidate: pass `proposed_by_actor` (from the `provenance` dict
    `propose_decision` returned) and neither the accepting `actor` nor the
    named `policy_owner` may equal it. Omitting `proposed_by_actor` skips
    this check -- appropriate only when acceptance is being driven from
    outside the harness's own propose/accept pair (a decision authored
    directly by a policy owner, never through `propose_decision`).
    Returns (accepted_decision, acceptance_event); the event is host-local
    metadata, kept off the decision record for the same reason
    `propose_decision`'s provenance is.
    """
    if decision.get("status") != "proposed":
        raise HarnessError(
            f"cannot accept a decision whose status is {decision.get('status')!r}; only 'proposed' may be accepted"
        )
    if proposed_by_actor is not None and proposed_by_actor in (actor, policy_owner):
        raise HarnessError(
            "the actor who proposed this candidate decision MUST NOT also be the accepting actor or the "
            "named policy_owner (action-boundary.md section 3 distinctness rule, applied here to decision "
            "capture: the party whose incident or proposal produced the candidate cannot self-accept it)"
        )
    accepted = dict(decision, status="accepted")
    event = {
        "kind": "harness_local_provenance",
        "note": "host-local acceptance event; not promoted into portable AWP state",
        "policy_owner": policy_owner,
        "accepted_by_actor": actor,
        "accepted_at": occurred_at or _utc_now_iso(),
        "decision_id": decision.get("id"),
    }
    return accepted, event


# ---------------------------------------------------------------------------
# Stage 4: session-end compliance assessment (execution/claim/evidence)
# ---------------------------------------------------------------------------

def session_compliance_report(
    event_log_path: str | Path,
    *,
    session_id: str,
    reviewer_actor: str,
    capsule_digest: str | None = None,
    occurred_at: str | None = None,
) -> dict:
    """Produce a Core `execution`/`claim`/`evidence` triple summarizing one
    session's logged action resolutions (correction 4: this is not a
    `change` or `checkpoint`, neither of which naturally represents a
    compliance assessment). Descriptive fields Core does not define are kept
    under `modules."urn:awp:harness-runtime"` rather than added to the
    records unqualified.

    This report is evidence, not a control. A model reviewer, fresh-context
    or not, can share the acting model's blind spots; it becomes a blocking
    control only when an enforcement point (tools/awp_ci_gate.py) requires
    an acceptable result before letting a protected operation take effect.
    """
    entries = _read_event_log(event_log_path)
    permits = [e for e in entries if e.get("result") == RESULT_PERMIT]
    denies = [e for e in entries if e.get("result") == RESULT_DENY]
    unresolved = [e for e in entries if e.get("result") == RESULT_UNRESOLVED]
    bound = [e for e in entries if e.get("invocation_binding")]

    occurred_at = occurred_at or _utc_now_iso()

    execution = {
        "id": f"execution:action-boundary-review-{session_id}",
        "type": "execution",
        "operation": "action-boundary-session-review",
        "status": "completed",
        "modules": {
            HARNESS_NS: {
                "reviewer_actor": reviewer_actor,
                "capsule_digest": capsule_digest,
                "occurred_at": occurred_at,
                "conformance_levels_observed": _conformance_levels_observed(entries),
            }
        },
    }
    claim = {
        "id": f"claim:action-boundary-review-{session_id}",
        "type": "claim",
        "statement": (
            f"Session {session_id} resolved {len(entries)} action(s): "
            f"{len(permits)} permit, {len(denies)} deny, {len(unresolved)} unresolved; "
            f"{len(bound)} carried a recomputed invocation binding."
        ),
        "epistemic_status": "verified" if entries else "unverified",
    }
    evidence = {
        "id": f"evidence:action-boundary-review-{session_id}",
        "type": "evidence",
        "evidence_type": "action-resolution-log",
        "modules": {
            HARNESS_NS: {
                "source_path": str(event_log_path),
                "entry_count": len(entries),
            }
        },
    }
    return {"execution": execution, "claim": claim, "evidence": evidence}


def _conformance_levels_observed(entries: list[dict]) -> list[str]:
    """Which of action-boundary.md section 10's existing conformance levels
    this session's own log gives *some* evidence for -- honestly bounded:
    this harness cannot itself certify `action-enforced` (that requires an
    independent adapter outside the participant's control, i.e.
    tools/awp_ci_gate.py, not this session-local report) or
    `output-attested` (requires artifact-claim verification at publication).
    """
    if not entries:
        return []
    levels = ["context-aware"]
    if any(e.get("selection") == "complete" and e.get("decision_context") == "complete" for e in entries):
        levels.append("decision-resolved")
    if any(e.get("invocation_binding") for e in entries):
        levels.append("action-bound")
    return levels


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _cmd_decision_index(args: argparse.Namespace) -> int:
    decisions = _load_json(args.decisions)
    projection = decision_index(
        decisions,
        capsule_digest=args.capsule_digest,
        frontier=args.frontier,
        budget_bytes=args.budget_bytes,
    )
    _print(projection)
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    action = _load_json(args.action)
    guardrails = _load_json(args.guardrails) if args.guardrails else []
    decisions = _load_json(args.decisions) if args.decisions else []
    entry_status = _load_json(args.entry_status) if args.entry_status else {
        "selection": "complete",
        "decision_context": "complete",
    }
    tool_arguments = _load_json(args.tool_arguments) if args.tool_arguments else None
    resolution, exit_code = gate(
        action, guardrails, decisions, entry_status,
        tool_name=args.tool_name,
        tool_version=args.tool_version,
        tool_arguments=tool_arguments,
        event_log_path=args.event_log,
    )
    _print(resolution)
    return exit_code


def _cmd_enforce(args: argparse.Namespace) -> int:
    resolution = _load_json(args.resolution)
    arguments = _load_json(args.tool_arguments) if args.tool_arguments else {}
    result, exit_code = enforce(
        resolution, tool_name=args.tool_name, tool_version=args.tool_version, arguments=arguments
    )
    _print(result)
    return exit_code


def _cmd_compliance_report(args: argparse.Namespace) -> int:
    report = session_compliance_report(
        args.event_log,
        session_id=args.session_id,
        reviewer_actor=args.reviewer_actor,
        capsule_digest=args.capsule_digest,
    )
    _print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    di = sub.add_parser("decision-index", help="Print a budget-bounded decision-selector projection.")
    di.add_argument("--decisions", required=True)
    di.add_argument("--capsule-digest", required=True)
    di.add_argument("--frontier")
    di.add_argument("--budget-bytes", type=int, default=2048)
    di.set_defaults(func=_cmd_decision_index)

    g = sub.add_parser("gate", help="Resolve and optionally bind/log one action. Exit: 0 permit, 1 deny, 2 unresolved.")
    g.add_argument("--action", required=True)
    g.add_argument("--guardrails")
    g.add_argument("--decisions")
    g.add_argument("--entry-status")
    g.add_argument("--tool-name")
    g.add_argument("--tool-version")
    g.add_argument("--tool-arguments")
    g.add_argument("--event-log")
    g.set_defaults(func=_cmd_gate)

    e = sub.add_parser("enforce", help="Recheck a prior resolution against the actual call. Exit: 0 permit, 1 deny, 2 unresolved.")
    e.add_argument("--resolution", required=True)
    e.add_argument("--tool-name", required=True)
    e.add_argument("--tool-version")
    e.add_argument("--tool-arguments")
    e.set_defaults(func=_cmd_enforce)

    c = sub.add_parser("compliance-report", help="Summarize a session's event log as an execution/claim/evidence triple.")
    c.add_argument("--event-log", required=True)
    c.add_argument("--session-id", required=True)
    c.add_argument("--reviewer-actor", required=True)
    c.add_argument("--capsule-digest")
    c.set_defaults(func=_cmd_compliance_report)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
