"""Agent-agnostic CI gate for AWP Action Boundary (urn:awp:action-boundary 0.3.1).

This is the `action-enforced`-tier binding action-boundary.md section 7 asks
for: a component outside the participant's own control that independently
recomputes an action resolution before a protected operation takes effect.
It is the part of this harness prototype that is actually cross-agent in the
strong sense -- it runs against a changed-files list and does not accept,
read, or care about which agent (or human) produced the diff. A Claude Code
session, a Codex session, and a person editing by hand all pass through the
identical check, because none of them are asked to cooperate with it.

Two things this gate checks per changed file that falls under a declared
protected path (see `--protected-paths`):

  1. A matching artifact-claim record exists (action-boundary.md section 6),
     and its evidence is mechanically re-verified against the actual current
     repository content right now -- not merely present, not merely trusted.
     A claim's `evidence.source_digest` is recomputed from
     `evidence.source_artifact` on disk; a mismatch is a violation. This
     defends the same thing action-boundary.md section 6 states in prose --
     "must be a mechanical byproduct of a constrained transformation
     pipeline, not a participant's self-report" -- by actually recomputing
     the one piece of it a CI job can recompute cheaply.
  2. The declared production of that artifact class still resolves to
     `permit` against a freshly loaded guardrail/decision set (never a
     resolution handed to this gate by whatever produced the change --
     tools/awp_action_boundary.py's own module docstring already states this
     principle for any enforcement adapter).

This gate does not attempt to verify freeform-vs-composite *how* an artifact
was actually produced -- that is the protected-kind tool constraint's job
(action-boundary.md section 5, enforced at the tool-call boundary, not after
the fact) and is out of scope for a prototype CI check that only sees a
diff. What this gate adds is a second, independent, agent-blind layer: even
if a tool-call-time gate was bypassed, disabled, or simply does not exist
for the agent that made the change, a protected artifact still cannot merge
without a verified claim and a permitted resolution.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from tools.awp_action_boundary import RESULT_PERMIT, resolve_action


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


def matching_protected_paths(changed_path: str, protected_paths: Sequence[dict]) -> list[dict]:
    matches = []
    for entry in protected_paths:
        for pattern in entry.get("path_globs", []):
            if fnmatch.fnmatch(changed_path, pattern):
                matches.append(entry)
                break
    return matches


def find_claim_for_artifact(artifact_path: str, claims: Sequence[dict]) -> dict | None:
    for claim in claims:
        if claim.get("artifact") == artifact_path:
            return claim
    return None


def verify_artifact_claim(claim: dict, *, repo_root: Path) -> list[str]:
    """Mechanically re-verify a claim record's evidence against the files on
    disk right now. Returns a list of problem strings (empty means clean).
    """
    problems: list[str] = []
    for entry in claim.get("claims", []):
        claim_name = entry.get("claim")
        artifact = claim.get("artifact")
        if entry.get("status") != "verified":
            problems.append(f"claim {claim_name!r} is not status=verified")
            continue
        evidence = entry.get("evidence") or {}
        source_artifact = evidence.get("source_artifact")
        source_digest = evidence.get("source_digest")
        if not source_artifact or not source_digest:
            problems.append(f"claim {claim_name!r} is missing evidence.source_artifact/source_digest")
            continue
        source_path = repo_root / source_artifact
        if not source_path.exists():
            problems.append(f"claim {claim_name!r} cites a source artifact that does not exist: {source_artifact}")
            continue
        actual_digest = _file_digest(source_path)
        if actual_digest != source_digest:
            problems.append(
                f"claim {claim_name!r} evidence.source_digest does not match the current content of "
                f"{source_artifact} (recomputed {actual_digest}, claim says {source_digest})"
            )
    return problems


def run_gate(
    *,
    changed_paths: Sequence[str],
    protected_paths: Sequence[dict],
    artifact_claims: Sequence[dict],
    guardrails: Sequence[dict],
    decisions: Sequence[dict],
    repo_root: Path,
    entry_status: dict | None = None,
) -> tuple[bool, list[str]]:
    """`entry_status` defaults to complete/complete because a CI job that
    freshly loads the whole guardrail and decision set genuinely has
    complete structural selection and decision context -- unlike a
    budget-bounded agent session, nothing here is a bounded projection.
    """
    entry_status = entry_status or {"selection": "complete", "decision_context": "complete"}
    violations: list[str] = []
    for changed_path in changed_paths:
        for entry in matching_protected_paths(changed_path, protected_paths):
            claim = find_claim_for_artifact(changed_path, artifact_claims)
            if claim is None:
                violations.append(
                    f"{changed_path}: protected by {entry.get('artifact_class')} but has no artifact-claim record"
                )
            else:
                violations.extend(f"{changed_path}: {p}" for p in verify_artifact_claim(claim, repo_root=repo_root))

            action = {
                "operation_class": "generative:composite",
                "resource": entry.get("resource", changed_path),
                "artifact_class": entry.get("artifact_class"),
                "actor": "actor:ci-gate",
            }
            resolution = resolve_action(action, guardrails, decisions, entry_status)
            if resolution["result"] != RESULT_PERMIT:
                violations.append(
                    f"{changed_path}: composite production of {entry.get('artifact_class')} does not resolve to "
                    f"permit (result={resolution['result']}, diagnostics={resolution.get('diagnostics')})"
                )
    return (len(violations) == 0), violations


def _cmd_check(args: argparse.Namespace) -> int:
    changed_paths = [
        line.strip()
        for line in Path(args.changed_files).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    protected_paths = _load_json(args.protected_paths).get("protected_paths", [])
    artifact_claims = _load_json(args.artifact_claims) if args.artifact_claims else []
    guardrails = _load_json(args.guardrails) if args.guardrails else []
    decisions = _load_json(args.decisions) if args.decisions else []
    ok, violations = run_gate(
        changed_paths=changed_paths,
        protected_paths=protected_paths,
        artifact_claims=artifact_claims,
        guardrails=guardrails,
        decisions=decisions,
        repo_root=Path(args.repo_root),
    )
    if ok:
        print(json.dumps({"result": "pass", "violations": []}, indent=2))
        return 0
    print(json.dumps({"result": "fail", "violations": violations}, indent=2), file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser(
        "check",
        help="Check a changed-files list against declared protected paths. Exit 0 pass, 1 fail.",
    )
    c.add_argument("--changed-files", required=True, help="File listing changed repo-relative paths, one per line.")
    c.add_argument("--protected-paths", required=True, help="JSON config: {\"protected_paths\": [...]}.")
    c.add_argument("--artifact-claims", help="JSON array of artifact-claim records.")
    c.add_argument("--guardrails", help="JSON array of Security guardrails.")
    c.add_argument("--decisions", help="JSON array of Core decisions.")
    c.add_argument("--repo-root", default=".")
    c.set_defaults(func=_cmd_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
