"""Service-free ledger-backed coordination for writable AWP projects.

The local-ledger-awareness-v1 profile is the default advisory coordination
path for agents that share a Git common directory.  It stores durable AWP
Coordination events in SQLite so publication and projection are atomic without
requiring a daemon.  It does not authenticate actors, enforce leases, fence
writes, or claim complete C1/C2/C3 conformance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterator, Sequence


PROFILE = "local-ledger-awareness-v1"
MODULE = "urn:awp:coordination"
TERMINAL_INTENT_STATES = {"completed", "withdrawn", "abandoned", "superseded"}
MUTATING_ACCESS = {"write", "create", "delete", "propose_change", "integrate"}
READ_ACCESS = {"observe", "read", "verify"}
ACCESS_MODES = MUTATING_ACCESS | READ_ACCESS | {"relied_upon_read"}
POLICIES = {"warn", "block"}


class CoordinationError(RuntimeError):
    """Raised when ledger discovery or a coordination transition is invalid."""


def utc_timestamp(value: datetime | None = None) -> str:
    current = value or datetime.now(timezone.utc)
    return current.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def git_value(project: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CoordinationError(
            f"git {' '.join(arguments)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def find_project(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".awp.json").is_file():
            return candidate
    raise CoordinationError("no .awp.json was found at or above the current directory")


def discover_workstate(project: Path) -> tuple[str, Path]:
    discovery_path = project / ".awp.json"
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    location = discovery.get("current_workstate")
    if not isinstance(location, str) or not location:
        raise CoordinationError(".awp.json does not identify current_workstate")
    capsule = (project / location).resolve()
    try:
        capsule.relative_to(project.resolve())
    except ValueError as error:
        raise CoordinationError("current_workstate resolves outside the project") from error
    text = capsule.read_text(encoding="utf-8")
    match = re.search(r"(?m)^workstate_id:\s*(\S+)\s*$", text)
    if not match:
        match = re.search(r'"workstate_id"\s*:\s*"([^"]+)"', text)
    if not match:
        raise CoordinationError("the current workstate has no readable workstate_id")
    return match.group(1), capsule


def default_ledger(project: Path) -> Path:
    common = Path(git_value(project, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = (project / common).resolve()
    return common / "awp" / "coordination.sqlite3"


def stable_project_id(project: Path) -> str:
    common = default_ledger(project).parent.parent.resolve()
    return f"git:{uuid.uuid5(uuid.NAMESPACE_URL, common.as_uri())}"


def normalize_scope(project: Path, raw: str) -> tuple[str, str]:
    if raw in {"*", ".", "./"}:
        return "repository", "."
    candidate = Path(raw)
    absolute = candidate.resolve() if candidate.is_absolute() else (project / candidate).resolve()
    try:
        relative = absolute.relative_to(project.resolve())
    except ValueError as error:
        raise CoordinationError(f"scope is outside the project: {raw}") from error
    normalized = PurePosixPath(relative.as_posix()).as_posix()
    if normalized in {"", "."}:
        return "repository", "."
    kind = "directory" if absolute.is_dir() or raw.endswith(("/", "\\")) else "file"
    return kind, normalized


def scopes_overlap(left: dict, right: dict) -> bool:
    if left["repository"] != right["repository"]:
        return False
    if left["kind"] == "repository" or right["kind"] == "repository":
        return True
    left_path = PurePosixPath(left["path"])
    right_path = PurePosixPath(right["path"])
    if left["kind"] == "file" and right["kind"] == "file":
        return left_path == right_path
    if left["kind"] == "directory" and right["kind"] == "directory":
        return (
            left_path == right_path
            or left_path in right_path.parents
            or right_path in left_path.parents
        )
    directory, file_path = (
        (left_path, right_path)
        if left["kind"] == "directory"
        else (right_path, left_path)
    )
    return directory == file_path or directory in file_path.parents


def access_conflicts(left: str, right: str) -> bool:
    if left == "relied_upon_read" or right == "relied_upon_read":
        other = right if left == "relied_upon_read" else left
        return other in MUTATING_ACCESS
    return left in MUTATING_ACCESS and right in MUTATING_ACCESS


class CoordinationLedger:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    workstate_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_workstate_sequence
                    ON events(workstate_id, sequence);
                CREATE TABLE IF NOT EXISTS records (
                    workstate_id TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    updated_sequence INTEGER NOT NULL,
                    PRIMARY KEY(workstate_id, record_id)
                );
                CREATE INDEX IF NOT EXISTS records_workstate_type_status
                    ON records(workstate_id, type, status);
                CREATE TABLE IF NOT EXISTS watchers (
                    workstate_id TEXT NOT NULL,
                    watcher_id TEXT NOT NULL,
                    cursor INTEGER NOT NULL,
                    PRIMARY KEY(workstate_id, watcher_id)
                );
                CREATE TABLE IF NOT EXISTS requests (
                    workstate_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    PRIMARY KEY(workstate_id, request_id)
                );
                """
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _identifier(prefix: str) -> str:
        return f"{prefix}:{uuid.uuid4()}"

    @staticmethod
    def _frontier(connection: sqlite3.Connection, workstate_id: str) -> list[str]:
        row = connection.execute(
            "SELECT event_id FROM events WHERE workstate_id = ? ORDER BY sequence DESC LIMIT 1",
            (workstate_id,),
        ).fetchone()
        return [row["event_id"]] if row else []

    def _append(
        self,
        connection: sqlite3.Connection,
        *,
        workstate_id: str,
        actor: str,
        kind: str,
        payload: dict,
        occurred_at: str,
    ) -> tuple[dict, int]:
        event = {
            "event_schema_version": "0.2",
            "module": MODULE,
            "kind": kind,
            "event_id": self._identifier("evt"),
            "workstate_id": workstate_id,
            "parents": self._frontier(connection, workstate_id),
            "occurred_at": occurred_at,
            "actor": actor,
            "payload": payload,
            "extensions": {"awp_profile": PROFILE},
        }
        cursor = connection.execute(
            "INSERT INTO events(event_id, workstate_id, kind, occurred_at, actor, event_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event["event_id"],
                workstate_id,
                kind,
                occurred_at,
                actor,
                json.dumps(event, sort_keys=True, separators=(",", ":")),
            ),
        )
        return event, int(cursor.lastrowid)

    @staticmethod
    def _project_record(
        connection: sqlite3.Connection, workstate_id: str, record: dict, sequence: int
    ) -> None:
        existing = connection.execute(
            "SELECT revision FROM records WHERE workstate_id = ? AND record_id = ?",
            (workstate_id, record["id"]),
        ).fetchone()
        if existing and record["revision"] != existing["revision"] + 1:
            raise CoordinationError(
                f"record revision must advance by one: {record['id']}"
            )
        if not existing and record["revision"] != 1:
            raise CoordinationError(f"new record must begin at revision 1: {record['id']}")
        connection.execute(
            "INSERT INTO records(workstate_id, record_id, type, revision, status, record_json, updated_sequence) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(workstate_id, record_id) DO UPDATE SET "
            "type=excluded.type, revision=excluded.revision, status=excluded.status, "
            "record_json=excluded.record_json, updated_sequence=excluded.updated_sequence",
            (
                workstate_id,
                record["id"],
                record["type"],
                record["revision"],
                record["status"],
                json.dumps(record, sort_keys=True, separators=(",", ":")),
                sequence,
            ),
        )

    @staticmethod
    def _records(
        connection: sqlite3.Connection,
        workstate_id: str,
        record_type: str,
        statuses: set[str] | None = None,
    ) -> list[dict]:
        rows = connection.execute(
            "SELECT record_json FROM records WHERE workstate_id = ? AND type = ? ORDER BY updated_sequence",
            (workstate_id, record_type),
        ).fetchall()
        records = [json.loads(row["record_json"]) for row in rows]
        return [record for record in records if not statuses or record["status"] in statuses]

    @staticmethod
    def _scope_map(connection: sqlite3.Connection, workstate_id: str) -> dict[str, dict]:
        return {
            f"{record['id']}@{record['revision']}": record
            for record in CoordinationLedger._records(connection, workstate_id, "scope", {"active"})
        }

    def begin(
        self,
        *,
        workstate_id: str,
        project_id: str,
        actor: str,
        goal: str,
        summary: str,
        base_revision: str,
        scopes: Sequence[tuple[str, str]],
        access: str = "write",
        policy: str = "warn",
        at: datetime | None = None,
        request_id: str | None = None,
        request_hash: str | None = None,
    ) -> dict:
        if not scopes:
            raise CoordinationError("at least one scope is required")
        if access not in ACCESS_MODES:
            raise CoordinationError(f"unsupported access mode: {access}")
        if policy not in POLICIES:
            raise CoordinationError(f"unsupported overlap policy: {policy}")
        occurred_at = utc_timestamp(at)
        events: list[dict] = []
        with self._transaction() as connection:
            if request_id:
                prior_request = connection.execute(
                    "SELECT request_hash, response_json FROM requests "
                    "WHERE workstate_id = ? AND request_id = ?",
                    (workstate_id, request_id),
                ).fetchone()
                if prior_request:
                    if prior_request["request_hash"] != request_hash:
                        raise CoordinationError("request ID was reused with different content")
                    return json.loads(prior_request["response_json"])
            existing_intents = self._records(
                connection, workstate_id, "intent", {"proposed", "active", "waiting"}
            )
            existing_scopes = self._scope_map(connection, workstate_id)
            declared_scopes: list[str] = []
            new_scopes: list[dict] = []
            for kind, path in scopes:
                scope_id = self._identifier("scope")
                record = {
                    "id": scope_id,
                    "type": "scope",
                    "module": MODULE,
                    "revision": 1,
                    "status": "active",
                    "created_by": actor,
                    "created_at": occurred_at,
                    "selector": {
                        "kind": kind,
                        "repository": project_id,
                        "base_revision": base_revision,
                        "path": path,
                    },
                    "access": access,
                }
                event, sequence = self._append(
                    connection,
                    workstate_id=workstate_id,
                    actor=actor,
                    kind="scope.created",
                    payload={"record_id": scope_id, "revision": 1, "replacement": record},
                    occurred_at=occurred_at,
                )
                self._project_record(connection, workstate_id, record, sequence)
                events.append(event)
                new_scopes.append(record)
                declared_scopes.append(f"{scope_id}@1")

            intent_id = self._identifier("intent")
            conflicts: list[dict] = []
            for other in existing_intents:
                for other_ref in other["declared_scopes"]:
                    other_scope = existing_scopes.get(other_ref)
                    if not other_scope:
                        continue
                    for scope in new_scopes:
                        if scopes_overlap(scope["selector"], other_scope["selector"]) and access_conflicts(
                            scope["access"], other_scope["access"]
                        ):
                            conflicts.append(
                                {
                                    "other_intent": f"{other['id']}@{other['revision']}",
                                    "other_actor": other["created_by"],
                                    "scope": f"{scope['id']}@1",
                                    "other_scope": other_ref,
                                }
                            )

            intent = {
                "id": intent_id,
                "type": "intent",
                "module": MODULE,
                "revision": 1,
                "status": "proposed" if conflicts and policy == "block" else "active",
                "created_by": actor,
                "created_at": occurred_at,
                "goal": goal,
                "summary": summary,
                "base": {"repository": project_id, "revision": base_revision},
                "declared_scopes": declared_scopes,
                "extensions": {"overlap_policy": policy, "profile": PROFILE},
            }
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="intent.announced",
                payload={"record_id": intent_id, "revision": 1, "replacement": intent},
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, intent, sequence)
            events.append(event)

            overlaps: list[dict] = []
            for conflict in conflicts:
                overlap_id = self._identifier("overlap")
                overlap = {
                    "id": overlap_id,
                    "type": "overlap",
                    "module": MODULE,
                    "revision": 1,
                    "status": "open",
                    "created_by": actor,
                    "created_at": occurred_at,
                    "subjects": [f"{intent_id}@1", conflict["other_intent"]],
                    "classification": "blocking" if policy == "block" else "negotiation_required",
                    "basis": [{
                        "scope": conflict["scope"],
                        "other_scope": conflict["other_scope"],
                        "reason": "overlapping advisory ledger scopes with incompatible access",
                    }],
                    "policy_action": policy,
                }
                overlap_event, overlap_sequence = self._append(
                    connection,
                    workstate_id=workstate_id,
                    actor=actor,
                    kind="overlap.detected",
                    payload={"record_id": overlap_id, "revision": 1, "replacement": overlap},
                    occurred_at=occurred_at,
                )
                self._project_record(connection, workstate_id, overlap, overlap_sequence)
                events.append(overlap_event)
                overlaps.append(overlap)

            result = {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "intent": intent,
                "overlaps": overlaps,
                "advisory_status": "block" if conflicts and policy == "block" else ("warn" if conflicts else "clear"),
                "event_ids": [event["event_id"] for event in events],
                "frontier": self._frontier(connection, workstate_id),
            }
            if request_id:
                connection.execute(
                    "INSERT INTO requests(workstate_id, request_id, request_hash, response_json) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        workstate_id,
                        request_id,
                        request_hash or hashlib.sha256(b"").hexdigest(),
                        json.dumps(result, sort_keys=True, separators=(",", ":")),
                    ),
                )
            return result

    def publish_change_set(
        self,
        *,
        workstate_id: str,
        intent_id: str,
        project_id: str,
        actor: str,
        summary: str,
        actual_scopes: Sequence[tuple[str, str]],
        artifacts: Sequence[str] = (),
        unfinished_work: Sequence[str] = (),
        request_id: str | None = None,
        request_hash: str | None = None,
        at: datetime | None = None,
    ) -> dict:
        """Store a proposed change set and return its durable publication receipt."""
        if not actual_scopes:
            raise CoordinationError("at least one actual scope is required")
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            if request_id:
                prior_request = connection.execute(
                    "SELECT request_hash, response_json FROM requests "
                    "WHERE workstate_id = ? AND request_id = ?",
                    (workstate_id, request_id),
                ).fetchone()
                if prior_request:
                    if prior_request["request_hash"] != request_hash:
                        raise CoordinationError("request ID was reused with different content")
                    return json.loads(prior_request["response_json"])

            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id = ? AND type = 'intent'",
                (workstate_id, intent_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown intent: {intent_id}")
            intent = json.loads(row["record_json"])
            owner = intent.get("owner", intent.get("created_by"))
            if actor != owner:
                raise CoordinationError(f"actor is not authorized to publish intent: {intent_id}")
            if intent["status"] in TERMINAL_INTENT_STATES:
                raise CoordinationError(f"intent is already terminal: {intent_id}")
            if intent["base"].get("repository") != project_id:
                raise CoordinationError("intent project does not match the publication project")

            scopes = self._scope_map(connection, workstate_id)
            declared_selectors = {
                (scopes[reference]["selector"]["kind"], scopes[reference]["selector"]["path"])
                for reference in intent["declared_scopes"]
                if reference in scopes
            }
            actual_scope_set = set(actual_scopes)
            change_set_id = self._identifier("changeset")
            change_set = {
                "id": change_set_id,
                "type": "change_set",
                "module": MODULE,
                "revision": 1,
                "status": "proposed",
                "created_by": actor,
                "created_at": occurred_at,
                "intent": f"{intent_id}@{intent['revision']}",
                "base": intent["base"],
                "artifacts": list(artifacts),
                "declared_scopes": list(intent["declared_scopes"]),
                "preconditions": [],
                "effects": {
                    "reads": [],
                    "writes": [],
                    "creates": [],
                    "removes": [],
                    "changes_behavior": [],
                    "preserves": [],
                },
                "extensions": {
                    "profile": PROFILE,
                    "summary": summary,
                    "actual_scope": [
                        {"kind": kind, "path": path} for kind, path in actual_scopes
                    ],
                    "unfinished_work": list(unfinished_work),
                },
            }
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="changeset.proposed",
                payload={
                    "record_id": change_set_id,
                    "revision": 1,
                    "replacement": change_set,
                },
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, change_set, sequence)
            result = {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "result": change_set,
                "event_ids": [event["event_id"]],
                "frontier": self._frontier(connection, workstate_id),
                "scope_complete": actual_scope_set == declared_selectors,
                "declared_scope": [
                    {"kind": kind, "path": path}
                    for kind, path in sorted(declared_selectors)
                ],
                "actual_scope": [
                    {"kind": kind, "path": path} for kind, path in actual_scopes
                ],
            }
            if request_id:
                connection.execute(
                    "INSERT INTO requests(workstate_id, request_id, request_hash, response_json) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        workstate_id,
                        request_id,
                        request_hash or hashlib.sha256(b"").hexdigest(),
                        json.dumps(result, sort_keys=True, separators=(",", ":")),
                    ),
                )
            return result

    def transition_intent(
        self,
        *,
        workstate_id: str,
        intent_id: str,
        actor: str,
        target: str,
        reason: str,
        outputs: Sequence[str] = (),
        at: datetime | None = None,
    ) -> dict:
        transitions = {
            "active": "intent.activated",
            "completed": "intent.completed",
            "withdrawn": "intent.withdrawn",
            "abandoned": "intent.abandoned",
        }
        if target not in transitions:
            raise CoordinationError(f"unsupported target state: {target}")
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? AND record_id = ? AND type = 'intent'",
                (workstate_id, intent_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown intent: {intent_id}")
            prior = json.loads(row["record_json"])
            owner = prior.get("owner", prior.get("created_by"))
            if actor != owner:
                raise CoordinationError(f"actor is not authorized to transition intent: {intent_id}")
            if prior["status"] in TERMINAL_INTENT_STATES:
                raise CoordinationError(f"intent is already terminal: {intent_id}")
            if target == "active":
                if prior["status"] not in {"proposed", "waiting"}:
                    raise CoordinationError("only proposed or waiting intents can be activated")
                blocking = connection.execute(
                    "SELECT record_json FROM records WHERE workstate_id = ? AND type = 'overlap' "
                    "AND status IN ('open','negotiating','escalated')",
                    (workstate_id,),
                ).fetchall()
                intent_ref = f"{intent_id}@{prior['revision']}"
                if any(
                    intent_ref in json.loads(item["record_json"])["subjects"]
                    and json.loads(item["record_json"]).get("policy_action") == "block"
                    for item in blocking
                ):
                    raise CoordinationError("blocking overlaps must be resolved before activation")
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                status=target,
                updated_at=occurred_at,
            )
            if outputs:
                replacement["outputs"] = list(outputs)
            if reason:
                replacement["termination_reason"] = reason
            payload = {
                "record_id": intent_id,
                "prior_revision": prior["revision"],
                "revision": replacement["revision"],
                "transition": {"from": prior["status"], "to": target},
                "reason": reason,
                "replacement": replacement,
            }
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind=transitions[target],
                payload=payload,
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            return {
                "intent": replacement,
                "event_id": event["event_id"],
                "frontier": self._frontier(connection, workstate_id),
            }

    def refresh(self, workstate_id: str) -> dict:
        with self._connect() as connection:
            intents = self._records(
                connection, workstate_id, "intent", {"proposed", "active", "waiting"}
            )
            overlaps = self._records(
                connection, workstate_id, "overlap", {"open", "negotiating", "escalated"}
            )
            blocking = [record for record in overlaps if record["policy_action"] == "block"]
            return {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "workstate_id": workstate_id,
                "frontier": self._frontier(connection, workstate_id),
                "active_intents": intents,
                "open_overlaps": overlaps,
                "advisory_status": "block" if blocking else ("warn" if overlaps else "clear"),
            }

    def interact_overlap(
        self,
        *,
        workstate_id: str,
        overlap_id: str,
        actor: str,
        disposition: str,
        rationale: str,
        evidence: Sequence[str] = (),
        request_id: str | None = None,
        request_hash: str | None = None,
        at: datetime | None = None,
    ) -> dict:
        """Record one model response to an active overlap."""
        event_kinds = {
            "acknowledged": ("overlap.acknowledged", "open"),
            "proposed": ("overlap.negotiation_started", "negotiating"),
            "ordered": ("overlap.dispositioned", "resolved"),
            "escalated": ("overlap.escalated", "escalated"),
            "unresolved": ("overlap.acknowledged", "open"),
        }
        if disposition not in event_kinds:
            raise CoordinationError(f"unsupported overlap disposition: {disposition}")
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            if request_id:
                prior_request = connection.execute(
                    "SELECT request_hash, response_json FROM requests "
                    "WHERE workstate_id = ? AND request_id = ?",
                    (workstate_id, request_id),
                ).fetchone()
                if prior_request:
                    if prior_request["request_hash"] != request_hash:
                        raise CoordinationError("request ID was reused with different content")
                    return json.loads(prior_request["response_json"])
            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id = ? AND type = 'overlap'",
                (workstate_id, overlap_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown overlap: {overlap_id}")
            prior = json.loads(row["record_json"])
            if prior["status"] not in {"open", "negotiating", "escalated"}:
                raise CoordinationError(f"overlap is not active: {overlap_id}")
            participant_ids = {subject.split("@", 1)[0] for subject in prior.get("subjects", [])}
            placeholders = ",".join("?" * len(participant_ids))
            rows = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id IN (%s)" % placeholders,
                (workstate_id, *participant_ids),
            ).fetchall() if participant_ids else []
            participants = {json.loads(item["record_json"]).get("created_by") for item in rows}
            if actor not in participants and actor != prior.get("created_by"):
                raise CoordinationError(f"actor is not an overlap participant: {overlap_id}")
            kind, target_status = event_kinds[disposition]
            if disposition in {"acknowledged", "unresolved"} and prior["status"] != "open":
                raise CoordinationError("acknowledgement requires an open overlap")
            if disposition == "proposed" and prior["status"] != "open":
                raise CoordinationError("a negotiation proposal requires an open overlap")
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                status=target_status,
                updated_at=occurred_at,
                interaction={
                    "disposition": disposition,
                    "rationale": rationale,
                    "evidence": list(evidence),
                    "actor": actor,
                },
            )
            if disposition == "ordered":
                replacement["disposition"] = {
                    "kind": "ordered",
                    "rationale": rationale,
                    "evidence": list(evidence),
                    "resolved_by": actor,
                }
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind=kind,
                payload={
                    "record_id": overlap_id,
                    "prior_revision": prior["revision"],
                    "revision": replacement["revision"],
                    "transition": {"from": prior["status"], "to": target_status},
                    "disposition": replacement["interaction"],
                    "replacement": replacement,
                },
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            result = {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "interaction": replacement["interaction"],
                "overlap": replacement,
                "event_ids": [event["event_id"]],
                "frontier": self._frontier(connection, workstate_id),
            }
            if request_id:
                connection.execute(
                    "INSERT INTO requests(workstate_id, request_id, request_hash, response_json) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        workstate_id,
                        request_id,
                        request_hash or hashlib.sha256(b"").hexdigest(),
                        json.dumps(result, sort_keys=True, separators=(",", ":")),
                    ),
                )
            return result

    def resolve_overlap(
        self,
        *,
        workstate_id: str,
        overlap_id: str,
        actor: str,
        reason: str,
        at: datetime | None = None,
    ) -> dict:
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id = ? AND type = 'overlap'",
                (workstate_id, overlap_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown overlap: {overlap_id}")
            prior = json.loads(row["record_json"])
            if prior["status"] not in {"open", "negotiating", "escalated"}:
                raise CoordinationError(f"overlap is not open: {overlap_id}")
            participant_ids = {subject.split("@", 1)[0] for subject in prior.get("subjects", [])}
            rows = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? AND record_id IN (%s)" % ",".join("?" * len(participant_ids)),
                (workstate_id, *participant_ids),
            ).fetchall() if participant_ids else []
            participants = {json.loads(item["record_json"]).get("created_by") for item in rows}
            if actor not in participants and actor != prior.get("created_by"):
                raise CoordinationError(f"actor is not an overlap participant: {overlap_id}")
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                status="resolved",
                updated_at=occurred_at,
                owner=actor,
                disposition={"reason": reason, "resolved_by": actor},
            )
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="overlap.dispositioned",
                payload={
                    "record_id": overlap_id,
                    "prior_revision": prior["revision"],
                    "revision": replacement["revision"],
                    "transition": {"from": prior["status"], "to": "resolved"},
                    "disposition": replacement["disposition"],
                    "replacement": replacement,
                },
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            return {
                "overlap": replacement,
                "event_id": event["event_id"],
                "frontier": self._frontier(connection, workstate_id),
            }

    def scan(self, workstate_id: str, watcher_id: str, limit: int = 1000) -> dict:
        if limit < 1:
            raise CoordinationError("scan limit must be positive")
        with self._transaction() as connection:
            cursor_row = connection.execute(
                "SELECT cursor FROM watchers WHERE workstate_id = ? AND watcher_id = ?",
                (workstate_id, watcher_id),
            ).fetchone()
            previous = int(cursor_row["cursor"]) if cursor_row else 0
            rows = connection.execute(
                "SELECT sequence, event_json FROM events WHERE workstate_id = ? AND sequence > ? "
                "ORDER BY sequence LIMIT ?",
                (workstate_id, previous, limit),
            ).fetchall()
            cursor = int(rows[-1]["sequence"]) if rows else previous
            connection.execute(
                "INSERT INTO watchers(workstate_id, watcher_id, cursor) VALUES (?, ?, ?) "
                "ON CONFLICT(workstate_id, watcher_id) DO UPDATE SET cursor=excluded.cursor",
                (workstate_id, watcher_id, cursor),
            )
            remaining = connection.execute(
                "SELECT 1 FROM events WHERE workstate_id = ? AND sequence > ? LIMIT 1",
                (workstate_id, cursor),
            ).fetchone()
            return {
                "previous_cursor": previous,
                "cursor": cursor,
                "has_more": remaining is not None,
                "events": [json.loads(row["event_json"]) for row in rows],
            }

    def export_events(self, workstate_id: str) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_json FROM events WHERE workstate_id = ? ORDER BY sequence",
                (workstate_id,),
            ).fetchall()
            return [json.loads(row["event_json"]) for row in rows]


def operational_context(start: Path, ledger_override: Path | None = None) -> dict:
    try:
        project = find_project(start)
        workstate_id, capsule = discover_workstate(project)
        candidates = (
            [(ledger_override.resolve(), "configured")]
            if ledger_override
            else [
                (default_ledger(project), "git-common"),
                (project / ".awp-runtime" / "coordination.sqlite3", "worktree-local"),
            ]
        )
        failures: list[str] = []
        for ledger_path, reach in candidates:
            try:
                ledger = CoordinationLedger(ledger_path)
                context = {
                    "mode": "ledger-backed-advisory",
                    "profile": PROFILE,
                    "fallback": False,
                    "project": project,
                    "project_id": stable_project_id(project),
                    "workstate_id": workstate_id,
                    "capsule": capsule,
                    "ledger_path": ledger_path,
                    "ledger_reach": reach,
                    "ledger": ledger,
                }
                if reach == "worktree-local":
                    context.update(
                        diagnostic="AWP-COORD-LEDGER-WORKTREE-LOCAL",
                        limitation="agents in other Git worktrees require a shared --ledger path",
                        unavailable_candidates=failures,
                    )
                return context
            except (OSError, sqlite3.Error) as error:
                failures.append(f"{ledger_path}: {error}")
        raise CoordinationError("; ".join(failures))
    except (CoordinationError, OSError, sqlite3.Error, json.JSONDecodeError) as error:
        return {
            "mode": "unavailable",
            "profile": None,
            "fallback": True,
            "diagnostic": "AWP-COORD-LEDGER-UNAVAILABLE",
            "reason": str(error),
        }


def printable_context(context: dict) -> dict:
    return {key: str(value) if isinstance(value, Path) else value for key, value in context.items() if key != "ledger"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path, help="override the shared ledger path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="report the default coordination mode")

    begin = subparsers.add_parser("begin", help="publish scopes and a work intent")
    begin.add_argument("--actor", required=True)
    begin.add_argument("--goal", required=True)
    begin.add_argument("--summary", required=True)
    begin.add_argument("--scope", action="append", required=True)
    begin.add_argument("--access", choices=sorted(ACCESS_MODES), default="write")
    begin.add_argument("--policy", choices=sorted(POLICIES), default="warn")

    refresh = subparsers.add_parser("refresh", help="project current intents and overlaps")
    refresh.add_argument("--actor")

    complete = subparsers.add_parser("complete", help="complete an intent")
    complete.add_argument("--actor", required=True)
    complete.add_argument("--intent-id", required=True)
    complete.add_argument("--reason", required=True)
    complete.add_argument("--output", action="append", default=[])

    withdraw = subparsers.add_parser("withdraw", help="withdraw an intent")
    withdraw.add_argument("--actor", required=True)
    withdraw.add_argument("--intent-id", required=True)
    withdraw.add_argument("--reason", required=True)

    activate = subparsers.add_parser("activate", help="activate a proposed or waiting intent")
    activate.add_argument("--actor", required=True)
    activate.add_argument("--intent-id", required=True)
    activate.add_argument("--reason", required=True)

    resolve = subparsers.add_parser("resolve", help="record an overlap disposition")
    resolve.add_argument("--actor", required=True)
    resolve.add_argument("--overlap-id", required=True)
    resolve.add_argument("--reason", required=True)

    scan = subparsers.add_parser("scan", help="read new ledger events from a durable cursor")
    scan.add_argument("--watcher-id", required=True)
    scan.add_argument("--limit", type=int, default=1000)

    subparsers.add_parser("export", help="write the unified event stream as JSON Lines")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = operational_context(args.project, args.ledger)
    if args.command == "status":
        print(json.dumps(printable_context(context), indent=2, sort_keys=True))
        return 0 if not context["fallback"] else 2
    if context["fallback"]:
        print(json.dumps(printable_context(context), indent=2, sort_keys=True))
        return 2

    ledger: CoordinationLedger = context["ledger"]
    try:
        if args.command == "begin":
            revision = f"git:{git_value(context['project'], 'rev-parse', 'HEAD')}"
            scopes = [normalize_scope(context["project"], scope) for scope in args.scope]
            result = ledger.begin(
                workstate_id=context["workstate_id"],
                project_id=context["project_id"],
                actor=args.actor,
                goal=args.goal,
                summary=args.summary,
                base_revision=revision,
                scopes=scopes,
                access=args.access,
                policy=args.policy,
            )
        elif args.command == "refresh":
            result = ledger.refresh(context["workstate_id"])
            if args.actor:
                result["actor"] = args.actor
        elif args.command in {"activate", "complete", "withdraw"}:
            result = ledger.transition_intent(
                workstate_id=context["workstate_id"],
                intent_id=args.intent_id,
                actor=args.actor,
                target={"activate": "active", "complete": "completed", "withdraw": "withdrawn"}[args.command],
                reason=args.reason,
                outputs=args.output if args.command == "complete" else (),
            )
        elif args.command == "resolve":
            result = ledger.resolve_overlap(
                workstate_id=context["workstate_id"],
                overlap_id=args.overlap_id,
                actor=args.actor,
                reason=args.reason,
            )
        elif args.command == "scan":
            result = ledger.scan(context["workstate_id"], args.watcher_id, args.limit)
        else:
            for event in ledger.export_events(context["workstate_id"]):
                print(json.dumps(event, sort_keys=True))
            return 0
    except (CoordinationError, sqlite3.Error, OSError) as error:
        print(json.dumps({"error": str(error)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
