"""Measure the local SQLite presence profile without claiming production capacity."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.awp_presence import PresenceRegistry  # noqa: E402


def elapsed(operation):
    started = time.perf_counter()
    value = operation()
    return value, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=1000)
    args = parser.parse_args()
    if args.sessions <= 0:
        parser.error("--sessions must be positive")

    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory() as directory:
        registry = PresenceRegistry(Path(directory) / "presence.sqlite3")

        def populate():
            for number in range(args.sessions):
                registry.enter(
                    agent_id=f"agent:{number}",
                    principal="principal:benchmark",
                    project_id="project:benchmark",
                    workstate_id="workstate:benchmark",
                    worktree=f"worktree:{number}",
                    branch="main",
                    revision="git:benchmark",
                    scopes=[f"scope:{number}@1"],
                    session_id=f"session:{number}",
                    at=now,
                )

        _, populate_seconds = elapsed(populate)
        exact, exact_seconds = elapsed(
            lambda: registry.enter(
                agent_id="agent:exact-conflict",
                principal="principal:benchmark",
                project_id="project:benchmark",
                workstate_id="workstate:benchmark",
                worktree="worktree:exact-conflict",
                branch="main",
                revision="git:benchmark",
                scopes=[f"scope:{args.sessions // 2}@1"],
                session_id="session:exact-conflict",
                at=now,
            )
        )
        wildcard, wildcard_seconds = elapsed(
            lambda: registry.enter(
                agent_id="agent:wildcard",
                principal="principal:benchmark",
                project_id="project:benchmark",
                workstate_id="workstate:benchmark",
                worktree="worktree:wildcard",
                branch="main",
                revision="git:benchmark",
                scopes=["*"],
                session_id="session:wildcard",
                at=now,
            )
        )
        scan, scan_seconds = elapsed(
            lambda: registry.scan("watcher:benchmark", limit=args.sessions * 3, at=now)
        )

    print(
        json.dumps(
            {
                "profile": "local-sqlite-presence-v1",
                "sessions": args.sessions,
                "sequential_entry_seconds": round(populate_seconds, 6),
                "entries_per_second": round(args.sessions / populate_seconds, 3),
                "exact_scope_lookup_seconds": round(exact_seconds, 6),
                "exact_scope_conflicts": len(exact["conflicts"]),
                "wildcard_lookup_seconds": round(wildcard_seconds, 6),
                "wildcard_conflicts": len(wildcard["conflicts"]),
                "initial_scan_seconds": round(scan_seconds, 6),
                "initial_scan_events": len(scan["events"]),
                "disclaimer": "Local synthetic timing; not a production capacity claim.",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
