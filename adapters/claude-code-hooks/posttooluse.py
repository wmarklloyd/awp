#!/usr/bin/env python3
"""Illustrative PostToolUse binding: recompute the invocation binding against
the tool call Claude Code says actually ran, using tools/awp_harness.py's
`enforce`. Cannot block -- the tool already executed by the time PostToolUse
fires, and Claude Code's PostToolUse hook has no `permissionDecision` field
(verified against https://code.claude.com/docs/en/hooks, 2026-09-13); it can
only surface `additionalContext`/`systemMessage`. A mismatch here means
Stage 2's gate approved a different call than the one that actually ran
(TOCTOU) -- this cannot undo the tool call, but it is what feeds
tools/awp_ci_gate.py's later, blocking check an honest signal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from tools.awp_harness import enforce, _append_event  # noqa: E402

CONFIG_PATH = Path(__file__).with_name("config.json")


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input", {})
    tool_use_id = payload.get("tool_use_id")

    if not CONFIG_PATH.exists() or not tool_use_id:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse"}}))
        return 0

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    pending_dir = _REPO_ROOT / config.get("pending_dir", ".awp-runtime/pending")
    pending_path = pending_dir / f"{tool_use_id}.json"
    if not pending_path.exists():
        # No PreToolUse resolution was recorded for this call (untracked
        # tool, or the mapping did not match) -- nothing to verify.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse"}}))
        return 0

    resolution = json.loads(pending_path.read_text(encoding="utf-8"))
    verified, exit_code = enforce(resolution, tool_name=tool_name, tool_version=None, arguments=tool_input)

    if config.get("event_log"):
        log_entry = dict(verified, type="post_tool_verification", tool_use_id=tool_use_id)
        _append_event(_REPO_ROOT / config["event_log"], log_entry)

    pending_path.unlink(missing_ok=True)

    output = {"hookSpecificOutput": {"hookEventName": "PostToolUse"}}
    if exit_code != 0:
        output["hookSpecificOutput"]["additionalContext"] = (
            f"AWP Action Boundary: the invocation binding for tool_use_id={tool_use_id} did not verify "
            f"against the call that actually ran (diagnostics={verified.get('diagnostics')}). "
            "The prior permit is no longer valid; treat this operation as unverified."
        )
        output["hookSpecificOutput"]["systemMessage"] = "AWP Action Boundary: post-call verification failed."
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
