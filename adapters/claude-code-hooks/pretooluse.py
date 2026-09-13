#!/usr/bin/env python3
"""Illustrative PreToolUse binding: Claude Code -> AWP Action Boundary.

Advisory only. action-boundary.md section 7 already states that a hook the
gated participant's own host executes is not an independent enforcement
point -- the same reason a commit hook is inadequate there. This exists for
fast local feedback and to populate the event log tools/awp_harness.py
compliance-report reads at session end. The actual enforcement point is
tools/awp_ci_gate.py, run in CI, which does not trust anything this hook
did or logged.

Claude Code's PreToolUse hook contract (verified against
https://code.claude.com/docs/en/hooks, 2026-09-13): one JSON object arrives
on stdin, including `tool_name`, `tool_input`, and `tool_use_id`. To block,
print `{"hookSpecificOutput": {"hookEventName": "PreToolUse",
"permissionDecision": "deny", "permissionDecisionReason": "..."}}` to stdout
and exit 0. (Exit 2 also blocks, via stderr, but bypasses this JSON contract
and the reason would not reach the agent as structured context.)

Project-specific tool_name -> operation_class/artifact_class mapping lives
in config.json next to this file (see config.example.json), never in this
script -- this script and tools/awp_harness.py stay project-agnostic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from tools.awp_harness import gate  # noqa: E402

CONFIG_PATH = Path(__file__).with_name("config.json")


def _load(path: str) -> dict:
    return json.loads((_REPO_ROOT / path).read_text(encoding="utf-8"))


def _allow(reason: str | None = None) -> dict:
    output = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    if reason:
        output["hookSpecificOutput"]["permissionDecisionReason"] = reason
    return output


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
        print(json.dumps(_allow()))
        return 0

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    mapping = next((m for m in config.get("mappings", []) if m.get("tool_name") == tool_name), None)
    if mapping is None:
        print(json.dumps(_allow()))
        return 0

    guardrails = _load(config["guardrails"]) if config.get("guardrails") else []
    decisions = _load(config["decisions"]) if config.get("decisions") else []
    entry_status = (
        _load(config["entry_status"])
        if config.get("entry_status")
        else {"selection": "complete", "decision_context": "complete"}
    )
    action = {
        "operation_class": mapping["operation_class"],
        "resource": tool_input.get(mapping.get("resource_from_argument"), mapping.get("default_resource", tool_name)),
        "artifact_class": mapping.get("artifact_class"),
        "actor": config.get("actor", "actor:agent-session"),
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
        print(json.dumps(_allow()))
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
