#!/usr/bin/env python3
"""Stop binding: session-end fresh-context-style reviewer, Codex side.

Produces the same Core execution/claim/evidence compliance triple as
../claude-code-hooks/stop.py (see that file's docstring), from
tools/awp_harness.py's `session_compliance_report`, summarizing this
session's logged action resolutions -- Codex-observed ones only, subject to
the same "Bash-like local tool calls only" coverage caveat documented in
./pretooluse.py. Informational, not a blocking control; Codex's Stop hook
(per the same third-party sources as ./pretooluse.py's docstring) is not
used here to force session continuation.
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
        reviewer_actor=config.get("actor", "actor:codex-session"),
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
