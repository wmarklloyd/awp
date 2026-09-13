#!/usr/bin/env python3
"""Illustrative Stop binding: the fresh-context session-end reviewer.

Produces a Core execution/claim/evidence compliance triple (see
tools/awp_harness.py's `session_compliance_report`, and correction 4 in
research/model-assisted-reviews/codex-harness-reconciliation-evaluation.md)
summarizing this session's logged action resolutions, and writes it to
`.awp-runtime/compliance-reports/<session_id>.json`. This report is evidence
for a later reviewer or CI step -- it is not itself a blocking control (the
reviewing model here is the same session that did the work; it can share
that session's blind spots, per the evaluation's own caution). Claude Code's
Stop hook (verified against https://code.claude.com/docs/en/hooks,
2026-09-13) can prevent the session from stopping via exit code 2, but this
binding does not use that -- a compliance report is informational, not a
reason to force the session to continue.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from tools.awp_harness import session_compliance_report  # noqa: E402

CONFIG_PATH = Path(__file__).with_name("config.json")


def main() -> int:
    payload = json.load(sys.stdin)
    session_id = payload.get("session_id", "unknown-session")

    if not CONFIG_PATH.exists():
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop"}}))
        return 0

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    event_log = _REPO_ROOT / config.get("event_log", ".awp-runtime/action-boundary-events.jsonl")

    report = session_compliance_report(
        event_log,
        session_id=session_id,
        reviewer_actor=config.get("actor", "actor:agent-session"),
        capsule_digest=config.get("capsule_digest"),
    )

    out_dir = _REPO_ROOT / ".awp-runtime" / "compliance-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{session_id}.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "systemMessage": f"AWP Action Boundary: {report['claim']['statement']}",
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
