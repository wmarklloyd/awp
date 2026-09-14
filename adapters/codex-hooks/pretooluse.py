#!/usr/bin/env python3
"""PreToolUse binding: Codex CLI -> AWP Action Boundary.

Advisory only, same caveat as ../claude-code-hooks/pretooluse.py: a hook the
gated participant's own host executes is not an independent enforcement
point. The actual enforcement point is tools/awp_ci_gate.py, run in CI,
which is agent-blind and does not trust anything this hook did or logged.

Codex CLI's PreToolUse hook contract, as researched 2026-09-13/14 (the
official docs at developers.openai.com/codex/hooks and
learn.chatgpt.com/docs/hooks repeatedly failed to fetch during that research;
reconstructed then from three independently-fetched third-party sources):
one JSON object arrives on stdin with `turn_id`, `tool_name`, `tool_use_id`,
`tool_input.command`, plus common fields `session_id`, `transcript_path`,
`cwd`, `hook_event_name`, `model`. To deny, print
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision":
"deny", "permissionDecisionReason": "..."}}` to stdout and exit 0.

CORRECTION (2026-09-14, confirmed against a real "Hook failed" error a user
hit running this binding): unlike Claude Code, Codex CLI's PreToolUse hook
can only *deny* -- it has no way to *grant* permission. An earlier version
of this file printed `{"hookSpecificOutput": {"hookEventName": "PreToolUse",
"permissionDecision": "allow"}}` for the allow case, mirroring Claude Code's
contract; Codex CLI rejected that at runtime with "Hook failed: PreToolUse
hook returned unsupported permissionDecision:allow" (reproduced independently
in https://github.com/safishamsi/graphify/issues/249 against codex-cli
0.120.0, and documented at
https://codex.danielvaughan.com/2026/04/15/codex-cli-hooks-complete-guide-events-policy-patterns/,
which states plainly: "Hooks can only deny, never grant permissions" -- note
this contradicts the "allow" example shown on learn.chatgpt.com/docs/hooks
at the time of that same research pass, so treat the runtime behavior, not
that page, as authoritative until reconciled). The correct way to let a call
proceed is to print **nothing** to stdout and exit 0 -- empty output is
treated as a no-op success, not a decision. This file no longer prints an
explicit allow.

IMPORTANT COVERAGE LIMITATION (why this binding leans on the classifier, not
a tool_name table, more than the Claude binding does): Codex's
PreToolUse/PostToolUse are documented, across all three sources, to fire
only for locally-executed tool calls -- commonly surfaced with a generic
`tool_name` such as "Bash" or "exec_command" regardless of what the
underlying command actually does, and hosted/remote tool calls may not be
covered at all. A tool_name -> operation_class mapping table is therefore
close to useless here even in principle: unlike a host where the gap is
simply an unconfirmed tool_name, Codex's tool_name is reported to be
uninformative by design for this hook. This binding's classification is
genuinely dependent on ../protected_write_classifier.py, which inspects
`tool_input.command` text (and any path-like arguments) for a protected
path, regardless of tool identity. config.json's `mappings` list is kept
only for parity with the Claude binding and for the rare case Codex someday
reports a specific, confirmed tool_name -- do not expect it to carry real
coverage here.

Given the "Bash-only" scope, this hook mainly protects hand-run or
agent-run shell commands (cp/mv/a generator script piping to a protected
path) invoked through Codex's exec tool. It does not claim to see everything
Codex can do; tools/awp_ci_gate.py is what actually blocks a bad commit
regardless of what this hook did or did not observe.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from tools.awp_harness import gate  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from protected_write_classifier import classify  # noqa: E402

CONFIG_PATH = Path(__file__).with_name("config.json")


def _load(path: str) -> dict:
    return json.loads((_REPO_ROOT / path).read_text(encoding="utf-8"))


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input", {})
    tool_use_id = payload.get("tool_use_id")

    if not CONFIG_PATH.exists():
        # No output = proceed normally, per the empirical fix below.
        return 0

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    guardrails = _load(config["guardrails"]) if config.get("guardrails") else []
    protected_paths = _load(config["protected_paths"]).get("protected_paths", []) if config.get("protected_paths") else []

    mapping = next((m for m in config.get("mappings", []) if m.get("tool_name") == tool_name), None)
    if mapping is not None:
        classification = {
            "operation_class": mapping["operation_class"],
            "resource": tool_input.get(mapping.get("resource_from_argument"), mapping.get("default_resource", tool_name)),
            "artifact_class": mapping.get("artifact_class"),
        }
    else:
        classification = classify(tool_name, tool_input, protected_paths)
        if classification is None:
            return 0

    decisions = _load(config["decisions"]) if config.get("decisions") else []
    entry_status = (
        _load(config["entry_status"])
        if config.get("entry_status")
        else {"selection": "complete", "decision_context": "complete"}
    )
    action = {
        "operation_class": classification["operation_class"],
        "resource": classification["resource"],
        "artifact_class": classification["artifact_class"],
        "actor": config.get("actor", "actor:codex-session"),
    }

    resolution, _exit_code = gate(
        action, guardrails, decisions, entry_status,
        tool_name=tool_name,
        tool_arguments=tool_input,
        event_log_path=(_REPO_ROOT / config["event_log"]) if config.get("event_log") else None,
    )

    if config.get("pending_dir") and tool_use_id:
        pending_dir = _REPO_ROOT / config["pending_dir"]
        pending_dir.mkdir(parents=True, exist_ok=True)
        (pending_dir / f"{tool_use_id}.json").write_text(
            json.dumps(resolution, sort_keys=True), encoding="utf-8"
        )

    if resolution["result"] == "permit":
        # No output = proceed normally (see module docstring: Codex CLI
        # rejects an explicit permissionDecision:"allow").
        return 0

    reason = (
        f"AWP Action Boundary: {resolution['result']} "
        f"(guardrails={resolution.get('applicable_guardrails')}, "
        f"decisions={resolution.get('applicable_decisions')}, "
        f"diagnostics={resolution.get('diagnostics')})"
    )
    print(json.dumps(_deny(reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
