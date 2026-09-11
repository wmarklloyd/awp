"""Experimental local AWP presence registry and monitor.

This is a reference implementation for the AWP 0.7 coordination-awareness
profile.  It provides advisory presence, not COOP-3 protected lease enforcement or
authorization.  SQLite transactions make entry, expiry, and watcher cursors
atomic for processes that share one local Git common directory.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Sequence

try:
    from .awp_runtime import hidden_process_options
except ImportError:  # executed as a script from tools/
    from awp_runtime import hidden_process_options


PROFILE = "local-sqlite-presence-v1"
DEFAULT_TTL_SECONDS = 90
DEFAULT_HEARTBEAT_SECONDS = 30
ACCESS_MODES = {"observe", "read", "write"}


class PresenceError(RuntimeError):
    """Raised when a presence lifecycle transition is invalid."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def default_registry(project: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
        **hidden_process_options(),
    )
    if result.returncode != 0:
        raise PresenceError("the default registry requires a Git repository")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = (project / common).resolve()
    return common / "awp" / "presence.sqlite3"


def git_value(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
        **hidden_process_options(),
    )
    if result.returncode != 0:
        raise PresenceError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


class PresenceRegistry:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    principal TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    workstate_id TEXT NOT NULL,
                    worktree TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    revision TEXT NOT NULL,
                    access_mode TEXT NOT NULL CHECK(access_mode IN ('observe', 'read', 'write')),
                    profile TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    heartbeat_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    expires_unix REAL NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active', 'released', 'expired'))
                );
                CREATE TABLE IF NOT EXISTS session_scopes (
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    scope TEXT NOT NULL,
                    PRIMARY KEY (session_id, scope)
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS watchers (
                    watcher_id TEXT PRIMARY KEY,
                    cursor INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS sessions_active_expiry
                    ON sessions(project_id, status, expires_unix);
                CREATE INDEX IF NOT EXISTS session_scopes_scope
                    ON session_scopes(scope, session_id);
                CREATE INDEX IF NOT EXISTS events_session_sequence
                    ON events(session_id, sequence);
                """
            )

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        kind: str,
        at: datetime,
        session_id: str,
        payload: dict,
    ) -> int:
        cursor = connection.execute(
            "INSERT INTO events(kind, occurred_at, session_id, payload) VALUES (?, ?, ?, ?)",
            (kind, timestamp(at), session_id, json.dumps(payload, sort_keys=True)),
        )
        return int(cursor.lastrowid)

    def _expire(self, connection: sqlite3.Connection, at: datetime) -> list[str]:
        rows = connection.execute(
            "SELECT session_id, agent_id, project_id FROM sessions "
            "WHERE status = 'active' AND expires_unix <= ? ORDER BY session_id",
            (at.timestamp(),),
        ).fetchall()
        for row in rows:
            connection.execute(
                "UPDATE sessions SET status = 'expired' WHERE session_id = ? AND status = 'active'",
                (row["session_id"],),
            )
            self._event(
                connection,
                "presence.expired",
                at,
                row["session_id"],
                {
                    "agent_id": row["agent_id"],
                    "project_id": row["project_id"],
                    "reason": "heartbeat_deadline_elapsed",
                },
            )
        return [str(row["session_id"]) for row in rows]

    @staticmethod
    def _session(connection: sqlite3.Connection, session_id: str) -> dict:
        row = connection.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise PresenceError(f"unknown session: {session_id}")
        result = dict(row)
        result.pop("expires_unix")
        result["scopes"] = [
            scope["scope"]
            for scope in connection.execute(
                "SELECT scope FROM session_scopes WHERE session_id = ? ORDER BY scope",
                (session_id,),
            ).fetchall()
        ]
        return result

    @staticmethod
    def _conflicts(
        connection: sqlite3.Connection,
        *,
        project_id: str,
        session_id: str,
        scopes: Sequence[str],
        access_mode: str,
    ) -> list[dict]:
        if access_mode not in ACCESS_MODES:
            raise PresenceError(f"unsupported access mode: {access_mode}")
        requested = set(scopes)
        if "*" in requested:
            active = connection.execute(
                "SELECT session_id, agent_id, access_mode FROM sessions "
                "WHERE project_id = ? AND status = 'active' AND session_id <> ? "
                "ORDER BY session_id",
                (project_id, session_id),
            ).fetchall()
        else:
            placeholders = ",".join("?" for _ in requested)
            active = connection.execute(
                "SELECT DISTINCT s.session_id, s.agent_id, s.access_mode "
                "FROM sessions AS s JOIN session_scopes AS ss ON ss.session_id = s.session_id "
                "WHERE s.project_id = ? AND s.status = 'active' AND s.session_id <> ? "
                f"AND (ss.scope = '*' OR ss.scope IN ({placeholders})) ORDER BY s.session_id",
                (project_id, session_id, *sorted(requested)),
            ).fetchall()
        conflicts: list[dict] = []
        for other in active:
            other_scopes = {
                row["scope"]
                for row in connection.execute(
                    "SELECT scope FROM session_scopes WHERE session_id = ?",
                    (other["session_id"],),
                ).fetchall()
            }
            overlap = (
                sorted(requested & other_scopes)
                if "*" not in requested and "*" not in other_scopes
                else sorted((requested | other_scopes) - {"*"}) or ["*"]
            )
            if overlap and "write" in {access_mode, str(other["access_mode"])}:
                conflicts.append(
                    {
                        "other_session_id": other["session_id"],
                        "other_agent_id": other["agent_id"],
                        "other_access_mode": other["access_mode"],
                        "overlapping_scopes": overlap,
                    }
                )
        return conflicts

    def enter(
        self,
        *,
        agent_id: str,
        principal: str,
        project_id: str,
        workstate_id: str,
        worktree: str,
        branch: str,
        revision: str,
        scopes: Sequence[str],
        access_mode: str = "write",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        session_id: str | None = None,
        at: datetime | None = None,
    ) -> dict:
        if not scopes or any(not scope or any(character.isspace() for character in scope) for scope in scopes):
            raise PresenceError("at least one non-whitespace scope identifier is required")
        if access_mode not in ACCESS_MODES:
            raise PresenceError(f"unsupported access mode: {access_mode}")
        if ttl_seconds <= 0:
            raise PresenceError("ttl_seconds must be positive")
        now = at or utc_now()
        identifier = session_id or f"session:{uuid.uuid4()}"
        expiry = now + timedelta(seconds=ttl_seconds)
        with self._write() as connection:
            self._expire(connection, now)
            if connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?", (identifier,)
            ).fetchone():
                raise PresenceError(f"session ID already exists: {identifier}")
            connection.execute(
                """
                INSERT INTO sessions(
                    session_id, agent_id, principal, project_id, workstate_id, worktree, branch,
                    revision, access_mode, profile, started_at, heartbeat_at,
                    expires_at, expires_unix, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (
                    identifier,
                    agent_id,
                    principal,
                    project_id,
                    workstate_id,
                    worktree,
                    branch,
                    revision,
                    access_mode,
                    PROFILE,
                    timestamp(now),
                    timestamp(now),
                    timestamp(expiry),
                    expiry.timestamp(),
                ),
            )
            connection.executemany(
                "INSERT INTO session_scopes(session_id, scope) VALUES (?, ?)",
                [(identifier, scope) for scope in sorted(set(scopes))],
            )
            conflicts = self._conflicts(
                connection,
                project_id=project_id,
                session_id=identifier,
                scopes=scopes,
                access_mode=access_mode,
            )
            self._event(
                connection,
                "presence.entered",
                now,
                identifier,
                {
                    "agent_id": agent_id,
                    "principal": principal,
                    "project_id": project_id,
                    "workstate_id": workstate_id,
                    "worktree": worktree,
                    "branch": branch,
                    "revision": revision,
                    "access_mode": access_mode,
                    "scopes": sorted(set(scopes)),
                    "expires_at": timestamp(expiry),
                    "profile": PROFILE,
                },
            )
            for conflict in conflicts:
                self._event(
                    connection,
                    "presence.conflict_detected",
                    now,
                    identifier,
                    {"project_id": project_id, **conflict},
                )
            return {"session": self._session(connection, identifier), "conflicts": conflicts}

    def heartbeat(
        self,
        session_id: str,
        *,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        at: datetime | None = None,
    ) -> dict:
        if ttl_seconds <= 0:
            raise PresenceError("ttl_seconds must be positive")
        now = at or utc_now()
        expiry = now + timedelta(seconds=ttl_seconds)
        with self._write() as connection:
            self._expire(connection, now)
            row = connection.execute(
                "SELECT status FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise PresenceError(f"unknown session: {session_id}")
            if row["status"] != "active":
                raise PresenceError(f"cannot renew {row['status']} session: {session_id}")
            connection.execute(
                "UPDATE sessions SET heartbeat_at = ?, expires_at = ?, expires_unix = ? "
                "WHERE session_id = ? AND status = 'active'",
                (timestamp(now), timestamp(expiry), expiry.timestamp(), session_id),
            )
            return self._session(connection, session_id)

    def leave(self, session_id: str, *, at: datetime | None = None) -> dict:
        now = at or utc_now()
        with self._write() as connection:
            self._expire(connection, now)
            row = connection.execute(
                "SELECT status, agent_id, project_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise PresenceError(f"unknown session: {session_id}")
            if row["status"] != "active":
                raise PresenceError(f"cannot release {row['status']} session: {session_id}")
            connection.execute(
                "UPDATE sessions SET status = 'released' WHERE session_id = ?",
                (session_id,),
            )
            self._event(
                connection,
                "presence.released",
                now,
                session_id,
                {"agent_id": row["agent_id"], "project_id": row["project_id"]},
            )
            return self._session(connection, session_id)

    def active(self, project_id: str, *, at: datetime | None = None) -> list[dict]:
        now = at or utc_now()
        with self._write() as connection:
            self._expire(connection, now)
            identifiers = connection.execute(
                "SELECT session_id FROM sessions WHERE project_id = ? AND status = 'active' "
                "ORDER BY session_id",
                (project_id,),
            ).fetchall()
            return [self._session(connection, row["session_id"]) for row in identifiers]

    def scan(
        self,
        watcher_id: str,
        *,
        limit: int = 1000,
        at: datetime | None = None,
    ) -> dict:
        if limit <= 0:
            raise PresenceError("scan limit must be positive")
        now = at or utc_now()
        with self._write() as connection:
            expired = self._expire(connection, now)
            watcher = connection.execute(
                "SELECT cursor FROM watchers WHERE watcher_id = ?", (watcher_id,)
            ).fetchone()
            cursor = int(watcher["cursor"]) if watcher else 0
            rows = connection.execute(
                "SELECT sequence, kind, occurred_at, session_id, payload FROM events "
                "WHERE sequence > ? ORDER BY sequence LIMIT ?",
                (cursor, limit),
            ).fetchall()
            events = [
                {
                    "sequence": row["sequence"],
                    "kind": row["kind"],
                    "occurred_at": row["occurred_at"],
                    "session_id": row["session_id"],
                    "payload": json.loads(row["payload"]),
                }
                for row in rows
            ]
            next_cursor = int(rows[-1]["sequence"]) if rows else cursor
            has_more = connection.execute(
                "SELECT 1 FROM events WHERE sequence > ? LIMIT 1", (next_cursor,)
            ).fetchone() is not None
            connection.execute(
                "INSERT INTO watchers(watcher_id, cursor, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(watcher_id) DO UPDATE SET cursor = excluded.cursor, "
                "updated_at = excluded.updated_at",
                (watcher_id, next_cursor, timestamp(now)),
            )
            return {
                "watcher_id": watcher_id,
                "previous_cursor": cursor,
                "cursor": next_cursor,
                "expired_sessions": expired,
                "has_more": has_more,
                "events": events,
            }


def print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, help="SQLite registry path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enter = subparsers.add_parser("enter", help="announce an active agent session")
    enter.add_argument("--agent-id", required=True)
    enter.add_argument("--principal", required=True)
    enter.add_argument("--session-id")
    enter.add_argument("--project-id", required=True)
    enter.add_argument("--workstate-id", required=True)
    enter.add_argument("--worktree", type=Path, default=Path.cwd())
    enter.add_argument("--branch")
    enter.add_argument("--revision")
    enter.add_argument("--scope", action="append", required=True)
    enter.add_argument("--access", choices=sorted(ACCESS_MODES), default="write")
    enter.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)

    heartbeat = subparsers.add_parser("heartbeat", help="renew an active presence session")
    heartbeat.add_argument("--session-id", required=True)
    heartbeat.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)

    leave = subparsers.add_parser("leave", help="release an active presence session")
    leave.add_argument("--session-id", required=True)

    active = subparsers.add_parser("active", help="list active project sessions")
    active.add_argument("--project-id", required=True)

    scan = subparsers.add_parser("scan", help="read new presence events once")
    scan.add_argument("--watcher-id", required=True)
    scan.add_argument("--limit", type=int, default=1000)

    watch = subparsers.add_parser("watch", help="continuously announce new presence events")
    watch.add_argument("--watcher-id", required=True)
    watch.add_argument("--interval-seconds", type=float, default=5.0)
    watch.add_argument("--duration-seconds", type=float, default=0.0)
    watch.add_argument("--page-size", type=int, default=1000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path.cwd().resolve()
    registry = PresenceRegistry(args.registry or default_registry(project))
    try:
        if args.command == "enter":
            worktree = args.worktree.resolve()
            revision = args.revision or f"git:{git_value(worktree, 'rev-parse', 'HEAD')}"
            branch = args.branch
            if branch is None:
                branch = git_value(worktree, "branch", "--show-current") or "(detached)"
            print_json(
                registry.enter(
                    agent_id=args.agent_id,
                    principal=args.principal,
                    session_id=args.session_id,
                    project_id=args.project_id,
                    workstate_id=args.workstate_id,
                    worktree=str(worktree),
                    branch=branch,
                    revision=revision,
                    scopes=args.scope,
                    access_mode=args.access,
                    ttl_seconds=args.ttl_seconds,
                )
            )
        elif args.command == "heartbeat":
            print_json(registry.heartbeat(args.session_id, ttl_seconds=args.ttl_seconds))
        elif args.command == "leave":
            print_json(registry.leave(args.session_id))
        elif args.command == "active":
            print_json(registry.active(args.project_id))
        elif args.command == "scan":
            print_json(registry.scan(args.watcher_id, limit=args.limit))
        elif args.command == "watch":
            if args.interval_seconds <= 0 or args.duration_seconds < 0:
                raise PresenceError("watch intervals and duration must be non-negative")
            started = time.monotonic()
            while True:
                while True:
                    result = registry.scan(args.watcher_id, limit=args.page_size)
                    for event in result["events"]:
                        print(json.dumps(event, sort_keys=True), flush=True)
                    if not result["has_more"]:
                        break
                if args.duration_seconds and time.monotonic() - started >= args.duration_seconds:
                    break
                time.sleep(args.interval_seconds)
    except PresenceError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
