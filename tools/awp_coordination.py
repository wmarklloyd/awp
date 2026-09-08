"""Service-free ledger-backed coordination for writable AWP projects.

The local-ledger-awareness-v1 profile is the default advisory coordination
path for agents that share a Git common directory.  It stores durable AWP
Coordination events in SQLite so publication and projection are atomic without
requiring a daemon.  It does not authenticate actors, enforce protected leases,
fence writes, or claim complete COOP-1, COOP-2, or COOP-3 conformance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Iterator, Sequence


PROFILE = "local-ledger-awareness-v1"
MODULE = "urn:awp:coordination"
COOPERATION_MODULE = "urn:awp:cooperation"
SCOPE_MODEL = "awp-repository-path-v1"
ACCESS_MODE_TABLE = "awp-access-mode-compatibility-v1"
TERMINAL_INTENT_STATES = {"completed", "withdrawn", "abandoned", "superseded"}
MUTATING_ACCESS = {"write", "create", "delete", "propose_change", "integrate"}
READ_ACCESS = {"observe", "read", "verify"}
ACCESS_MODES = MUTATING_ACCESS | READ_ACCESS | {"relied_upon_read"}
POLICIES = {"warn", "block"}
# COOP-1 section 4.1 requires participants to record a partition, order,
# withdrawal, or escalation. An escalation does not clear a blocking overlap.
DISPOSITION_KINDS = {"partition", "order", "withdrawal", "escalation"}
CLEARING_DISPOSITIONS = {"partition", "order", "withdrawal"}
DEFAULT_LEASE_SECONDS = 900
LEASE_STATES = {"active", "released", "expired"}
GENERATED_REGION = re.compile(
    r"<!-- awp:generated:start -->\n(.*?)\n<!-- awp:generated:end -->", re.DOTALL
)
GENERATED_DIGEST = re.compile(r"(?m)^generated_digest:\s*(sha256:[0-9a-f]{64})\s*$")
FRONTIER_BLOCK = re.compile(r"(?m)^frontier:\n(?:[ \t]*-\s*[^\n]+\n?)*")
CHECKPOINT_FIELD = re.compile(r"(?m)^checkpoint:\s*[^\n]*$")
GENERATED_AT_FIELD = re.compile(r"(?m)^generated_at:\s*[^\n]*$")


class CoordinationError(RuntimeError):
    """Raised when ledger discovery or a coordination transition is invalid."""


def utc_timestamp(value: datetime | None = None) -> str:
    current = value or datetime.now(timezone.utc)
    return current.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def generated_region_digest(text: str) -> str:
    """Return the Capsule generated-region digest after newline normalization."""
    normalized = text.replace("\r\n", "\n")
    match = GENERATED_REGION.search(normalized)
    if not match:
        raise CoordinationError("capsule has no generated region")
    return f"sha256:{hashlib.sha256(match.group(1).encode('utf-8')).hexdigest()}"


def capsule_integrity(path: Path) -> dict:
    """Read the current Capsule integrity state without changing it."""
    text = path.read_text(encoding="utf-8")
    declared = GENERATED_DIGEST.search(text)
    try:
        computed = generated_region_digest(text)
    except CoordinationError as error:
        return {
            "state": "stale",
            "path": path.name,
            "reason": str(error),
        }
    if not declared:
        return {
            "state": "stale",
            "path": path.name,
            "computed_digest": computed,
            "reason": "capsule has no generated_digest",
        }
    return {
        "state": "current" if declared.group(1) == computed else "modified",
        "path": path.name,
        "declared_digest": declared.group(1),
        "computed_digest": computed,
    }


def capsule_artifact_digest(path: Path) -> str:
    """Return the exact UTF-8 byte digest of a Capsule artifact."""
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def replace_capsule_projection(
    path: Path,
    *,
    expected_frontier: Sequence[str],
    expected_digest: str,
    expected_capsule_digest: str | None = None,
    frontier: Sequence[str],
    checkpoint_id: str,
    generated_at: str,
) -> dict:
    """Replace only Capsule projection metadata after optimistic checks.

    The caller holds the binding transaction.  `os.replace` gives readers either
    the old or new capsule; a crash between replacement and SQLite commit is
    intentionally surfaced as recoverable frontier divergence on the next read.
    """
    original = path.read_text(encoding="utf-8")
    actual_capsule_digest = capsule_artifact_digest(path)
    if expected_capsule_digest and actual_capsule_digest != expected_capsule_digest:
        raise CoordinationError("capsule whole-artifact digest is stale")
    integrity = capsule_integrity(path)
    if integrity["state"] != "current" or integrity["computed_digest"] != expected_digest:
        raise CoordinationError("capsule digest is stale or does not match expected digest")
    frontier_match = FRONTIER_BLOCK.search(original)
    if not frontier_match:
        raise CoordinationError("capsule has no readable frontier")
    actual_frontier = re.findall(r"(?m)^\s*-\s*(\S+)\s*$", frontier_match.group(0))
    if actual_frontier != list(expected_frontier):
        raise CoordinationError("capsule frontier is stale")
    # Substituted through a function so backslashes in generated content are not
    # read as replacement escapes; see _replace_once in awp_workstate.py.
    replacement_frontier = "frontier:\n" + "".join(f"  - {item}\n" for item in frontier)
    rewritten, count = FRONTIER_BLOCK.subn(lambda _match: replacement_frontier, original, count=1)
    if count != 1:
        raise CoordinationError("could not replace capsule frontier")
    rewritten, count = CHECKPOINT_FIELD.subn(lambda _match: f"checkpoint: {checkpoint_id}", rewritten, count=1)
    if count != 1:
        raise CoordinationError("capsule has no readable checkpoint")
    rewritten, count = GENERATED_AT_FIELD.subn(lambda _match: f"generated_at: {generated_at}", rewritten, count=1)
    if count != 1:
        raise CoordinationError("capsule has no readable generated_at")
    # The generated region is unchanged, so its declared digest remains valid.
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as temporary:
            temporary.write(rewritten)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return {
        "path": path.name,
        "digest": capsule_artifact_digest(path),
        "previous_digest": actual_capsule_digest,
        "generated_digest": integrity["computed_digest"],
        "frontier": list(frontier),
    }


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
    roots = sorted(
        line.strip()
        for line in git_value(project, "rev-list", "--max-parents=0", "HEAD").splitlines()
        if line.strip()
    )
    if not roots:
        raise CoordinationError("the Git repository has no discoverable root commit")
    if len(roots) == 1:
        return f"git-root:{roots[0]}"
    digest = hashlib.sha256("\n".join(roots).encode("ascii")).hexdigest()
    return f"git-roots-sha256:{digest}"


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
        raise CoordinationError("scope repository identity mismatch; overlap decision blocked")
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
    def __init__(self, path: Path, *, read_only: bool = False):
        self.path = path.resolve()
        self.read_only = read_only
        if read_only:
            if not self.path.is_file():
                raise CoordinationError(f"read-only ledger does not exist: {self.path}")
            # Immutable mode never creates a lock, journal, or WAL sidecar.
            # It is safe only when no WAL contains newer committed pages.
            if self.path.with_name(self.path.name + "-wal").exists():
                raise CoordinationError(
                    "read-only ledger fallback is unsafe while a WAL sidecar exists"
                )
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self.read_only:
            connection = sqlite3.connect(
                f"file:{self.path.as_posix()}?immutable=1", uri=True,
                isolation_level=None,
            )
        else:
            connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        if not self.read_only:
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
                CREATE TABLE IF NOT EXISTS binding_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO binding_metadata(key, value) VALUES ('binding_id', ?)",
                (f"binding:{uuid.uuid4()}",),
            )

    def binding_id(self) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM binding_metadata WHERE key = 'binding_id'"
            ).fetchone()
        if row is None:
            raise CoordinationError("coordination ledger has no binding identity")
        return str(row["value"])

    def participant_actors(self, workstate_id: str) -> list[str]:
        """Return actors that have independently entered this binding."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT actor FROM events WHERE workstate_id = ? "
                "AND kind = 'lease.entered' ORDER BY actor",
                (workstate_id,),
            ).fetchall()
        return [str(row["actor"]) for row in rows]

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        if self.read_only:
            raise CoordinationError("coordination ledger is available read-only")
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
            self._expire_due_leases(connection, workstate_id, occurred_at)
            acting_lease = self._active_lease(connection, workstate_id, actor, occurred_at)
            if policy == "block" and acting_lease is None:
                # COOP-1 section 4.1 orders the lease before the guarded announcement.
                raise CoordinationError(
                    "a guarded announcement requires an active lease; "
                    "run lease-enter before begin --policy block"
                )
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
                "lease": acting_lease["id"] if acting_lease else None,
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

    def refresh(self, workstate_id: str, at: datetime | None = None) -> dict:
        observed_at = utc_timestamp(at)
        with self._transaction() as connection:
            newly_expired = self._expire_due_leases(connection, workstate_id, observed_at)
            leases = self._records(connection, workstate_id, "cooperation_lease", {"active"})
            intents = self._records(
                connection, workstate_id, "intent", {"proposed", "active", "waiting"}
            )
            overlaps = self._records(
                connection, workstate_id, "overlap", {"open", "negotiating", "escalated"}
            )
            live_actors = sorted({lease["actor"] for lease in leases})
            stale_intents = self._stale_intents(intents, leases, live_actors)
            stale_ids = {item["intent"] for item in stale_intents}
            for intent in intents:
                if intent["id"] in stale_ids:
                    intent["holder_state"] = "stale"
            # An intent whose holder is gone and whose base has drifted no longer
            # describes work in progress, so it must not hold scope against a
            # present participant. The overlap stays visible; it stops blocking.
            blocking = [
                record
                for record in overlaps
                if record["policy_action"] == "block" and not self._only_stale_subjects(record, stale_ids)
            ]
            for record in overlaps:
                if record["policy_action"] == "block" and self._only_stale_subjects(record, stale_ids):
                    record["policy_action_effective"] = "warn"
                    record["downgrade_reason"] = "every other party is a stale intent with no live lease"
            return {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "workstate_id": workstate_id,
                "observed_at": observed_at,
                "frontier": self._frontier(connection, workstate_id),
                "active_intents": intents,
                "open_overlaps": overlaps,
                "active_leases": leases,
                "live_participants": live_actors,
                "expired_leases": [lease["id"] for lease in newly_expired],
                "inactive_participants": sorted(
                    {lease["actor"] for lease in newly_expired} - set(live_actors)
                ),
                "lease_enforcement": "advisory",
                "stale_intents": stale_intents,
                "advisory_status": "block" if blocking else ("warn" if overlaps else "clear"),
            }

    STALE_INTENT_COMMITS = 5

    def _project_root(self) -> Path | None:
        """Walk up from the ledger to the working tree that contains it.

        The ledger normally lives under the Git common directory, but its path can
        be overridden, so this is best effort: when no working tree is found the
        caller simply performs no staleness detection, which downgrades nothing.
        """
        cached = getattr(self, "_cached_project_root", False)
        if cached is not False:
            return cached
        root = None
        for candidate in [self.path, *self.path.parents]:
            if (candidate / ".git").exists() and candidate.is_dir():
                root = candidate
                break
        self._cached_project_root = root
        return root

    def _stale_intents(self, intents: list[dict], leases: list[dict], live_actors: list[str]) -> list[dict]:
        """Intents whose holder is not present and whose base revision has drifted.

        A stale intent is still a real record and is still reported; it simply
        stops counting as a blocking party, because an absent participant holding
        scope on a base that HEAD has moved past is indistinguishable from
        abandoned work and blocks everyone else indefinitely.
        """
        held = {intent["lease"] for intent in intents if intent.get("lease")}
        live_leases = {lease["id"] for lease in leases if lease["id"] in held}
        project = self._project_root()
        if project is None:
            return []
        try:
            head = f"git:{git_value(project, 'rev-parse', 'HEAD')}"
            behind = {}
            for intent in intents:
                base = (intent.get("base") or {}).get("revision")
                if not base or not head or base == head:
                    continue
                count = git_value(project, "rev-list", "--count", f"{base.removeprefix('git:')}..HEAD")
                behind[intent["id"]] = int(count)
        except (CoordinationError, OSError, ValueError):
            return []
        result = []
        for intent in intents:
            distance = behind.get(intent["id"])
            if distance is None or distance < self.STALE_INTENT_COMMITS:
                continue
            if intent.get("lease") in live_leases or intent.get("created_by") in live_actors:
                continue
            result.append(
                {
                    "intent": intent["id"],
                    "created_by": intent.get("created_by"),
                    "base_revision": (intent.get("base") or {}).get("revision"),
                    "commits_behind": distance,
                    "holder_present": False,
                    "reason": "base revision drifted and no live lease or participant holds it",
                }
            )
        return result

    @staticmethod
    def _only_stale_subjects(overlap: dict, stale_ids: set[str]) -> bool:
        """True when no live contention remains: at most one party is not stale.

        Contention requires two live claimants. An overlap whose only other
        parties are abandoned intents is not a conflict, it is debris, so it
        stops blocking. The requesting participant's own intent is of course
        not stale, which is why this counts live parties rather than requiring
        every subject to be stale.
        """
        subjects = {subject.split("@", 1)[0] for subject in overlap.get("subjects", [])}
        if len(subjects) < 2:
            return False
        return len(subjects - stale_ids) <= 1

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

    def record_checkpoint(
        self,
        *,
        workstate_id: str,
        actor: str,
        mode: str,
        next_action: str,
        unresolved_work: Sequence[str],
        capsule_frontier: Sequence[str],
        capsule_digest: str,
        request_id: str,
        request_hash: str,
    ) -> dict:
        """Record a publisher-confirmed checkpoint without inventing a Core event."""
        if mode != "continue":
            raise CoordinationError("local checkpoint binding supports continue mode only")
        with self._transaction() as connection:
            prior_request = connection.execute(
                "SELECT request_hash, response_json FROM requests "
                "WHERE workstate_id = ? AND request_id = ?",
                (workstate_id, request_id),
            ).fetchone()
            if prior_request:
                if prior_request["request_hash"] != request_hash:
                    raise CoordinationError("request ID was reused with different content")
                return json.loads(prior_request["response_json"])
            current_frontier = self._frontier(connection, workstate_id)
            if list(capsule_frontier) != current_frontier:
                raise CoordinationError("capsule frontier is stale")
            checkpoint_id = self._identifier("checkpoint")
            result = {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "checkpoint": checkpoint_id,
                "checkpoint_mode": mode,
                "next_action": next_action,
                "unresolved_work": list(unresolved_work),
                "capsule_frontier": list(capsule_frontier),
                "capsule_digest": capsule_digest,
                "actor": actor,
                "event_ids": [],
                "frontier": current_frontier,
            }
            connection.execute(
                "INSERT INTO requests(workstate_id, request_id, request_hash, response_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    workstate_id,
                    request_id,
                    request_hash,
                    json.dumps(result, sort_keys=True, separators=(",", ":")),
                ),
            )
            return result

    def publish_checkpoint(
        self,
        *,
        workstate_id: str,
        actor: str,
        capsule: Path,
        expected_capsule_frontier: Sequence[str],
        expected_ledger_frontier: Sequence[str],
        expected_digest: str,
        expected_capsule_digest: str | None = None,
        next_action: str,
        unresolved_work: Sequence[str],
        request_id: str,
        request_hash: str,
    ) -> dict:
        """Publish a receipt-backed canonical Capsule projection.

        This local profile serializes publishers with SQLite and atomically
        replaces the Capsule file.  It deliberately reports a recoverable
        mismatch if a process crashes between the file replacement and commit.
        """
        occurred_at = utc_timestamp()
        with self._transaction() as connection:
            prior_request = connection.execute(
                "SELECT request_hash, response_json FROM requests "
                "WHERE workstate_id = ? AND request_id = ?",
                (workstate_id, request_id),
            ).fetchone()
            if prior_request:
                if prior_request["request_hash"] != request_hash:
                    raise CoordinationError("request ID was reused with different content")
                return json.loads(prior_request["response_json"])
            current_frontier = self._frontier(connection, workstate_id)
            if list(expected_ledger_frontier) != current_frontier:
                raise CoordinationError("expected ledger frontier is stale")
            checkpoint_id = self._identifier("checkpoint")
            event, _ = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="checkpoint.published",
                payload={
                    "checkpoint": checkpoint_id,
                    "expected_capsule_frontier": list(expected_capsule_frontier),
                    "expected_ledger_frontier": list(expected_ledger_frontier),
                    "expected_digest": expected_digest,
                    "expected_capsule_digest": expected_capsule_digest,
                    "next_action": next_action,
                    "unresolved_work": list(unresolved_work),
                    "capsule": capsule.name,
                },
                occurred_at=occurred_at,
            )
            projection = replace_capsule_projection(
                capsule,
                expected_frontier=expected_capsule_frontier,
                expected_digest=expected_digest,
                expected_capsule_digest=expected_capsule_digest,
                frontier=[event["event_id"]],
                checkpoint_id=checkpoint_id,
                generated_at=occurred_at,
            )
            result = {
                "profile": PROFILE,
                "mode": "ledger-backed-advisory",
                "checkpoint": checkpoint_id,
                "expected_capsule_frontier": list(expected_capsule_frontier),
                "expected_ledger_frontier": list(expected_ledger_frontier),
                "next_action": next_action,
                "unresolved_work": list(unresolved_work),
                "receipt": projection,
                "frontier": [event["event_id"]],
                "atomicity": {
                    "mechanism": "sqlite-begin-immediate plus atomic file replace",
                    "recovery": "a crash between file replacement and database commit is reported as recoverable frontier divergence",
                },
            }
            connection.execute(
                "INSERT INTO requests(workstate_id, request_id, request_hash, response_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    workstate_id,
                    request_id,
                    request_hash,
                    json.dumps(result, sort_keys=True, separators=(",", ":")),
                ),
            )
            return result

    # ------------------------------------------------------------------
    # COOP-1 section 4.1 step 3: bounded participant leases.
    #
    # A lease is advisory. It records that a participant is present, where it is
    # executing, and until when, so that a crashed participant becomes visibly
    # inactive without requiring a capsule rewrite (section 4.4). Expiry is
    # evaluated lazily on read, because this profile runs no daemon.
    # ------------------------------------------------------------------

    @staticmethod
    def _lease_is_live(lease: dict, now: str) -> bool:
        return lease["status"] == "active" and lease["expires_at"] > now

    def _expire_due_leases(
        self, connection: sqlite3.Connection, workstate_id: str, now: str
    ) -> list[dict]:
        expired = []
        for lease in self._records(connection, workstate_id, "cooperation_lease", {"active"}):
            if lease["expires_at"] > now:
                continue
            replacement = dict(lease)
            replacement.update(
                revision=lease["revision"] + 1,
                status="expired",
                updated_at=now,
                expired_at=now,
            )
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=lease["actor"],
                kind="lease.expired",
                payload={
                    "record_id": lease["id"],
                    "prior_revision": lease["revision"],
                    "revision": replacement["revision"],
                    "transition": {"from": "active", "to": "expired"},
                    "replacement": replacement,
                },
                occurred_at=now,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            expired.append(replacement)
        return expired

    def _active_lease(
        self, connection: sqlite3.Connection, workstate_id: str, actor: str, now: str
    ) -> dict | None:
        for lease in self._records(connection, workstate_id, "cooperation_lease", {"active"}):
            if lease["actor"] == actor and self._lease_is_live(lease, now):
                return lease
        return None

    def enter_lease(
        self,
        *,
        workstate_id: str,
        project_id: str,
        actor: str,
        location: str,
        base_revision: str,
        intended_scopes: Sequence[str] = (),
        ttl_seconds: int = DEFAULT_LEASE_SECONDS,
        at: datetime | None = None,
    ) -> dict:
        if ttl_seconds < 1:
            raise CoordinationError("lease ttl_seconds must be positive")
        moment = at or datetime.now(timezone.utc)
        occurred_at = utc_timestamp(moment)
        expires_at = utc_timestamp(moment + timedelta(seconds=ttl_seconds))
        with self._transaction() as connection:
            self._expire_due_leases(connection, workstate_id, occurred_at)
            existing = self._active_lease(connection, workstate_id, actor, occurred_at)
            if existing:
                raise CoordinationError(
                    f"actor already holds an active lease: {existing['id']}"
                )
            lease = {
                "id": self._identifier("lease"),
                "type": "cooperation_lease",
                "module": COOPERATION_MODULE,
                "revision": 1,
                "status": "active",
                "actor": actor,
                "project_id": project_id,
                "execution_location": location,
                "base_revision": base_revision,
                "intended_scopes": list(intended_scopes),
                "entered_at": occurred_at,
                "renewed_at": occurred_at,
                "expires_at": expires_at,
                "ttl_seconds": ttl_seconds,
                "extensions": {"profile": PROFILE, "enforcement": "advisory"},
            }
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="lease.entered",
                payload={"record_id": lease["id"], "revision": 1, "replacement": lease},
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, lease, sequence)
            return {
                "profile": PROFILE,
                "lease": lease,
                "event_id": event["event_id"],
                "frontier": self._frontier(connection, workstate_id),
            }

    def renew_lease(
        self,
        *,
        workstate_id: str,
        lease_id: str,
        actor: str,
        ttl_seconds: int | None = None,
        at: datetime | None = None,
    ) -> dict:
        moment = at or datetime.now(timezone.utc)
        occurred_at = utc_timestamp(moment)
        with self._transaction() as connection:
            self._expire_due_leases(connection, workstate_id, occurred_at)
            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id = ? AND type = 'cooperation_lease'",
                (workstate_id, lease_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown lease: {lease_id}")
            prior = json.loads(row["record_json"])
            if prior["actor"] != actor:
                raise CoordinationError(f"actor does not hold lease: {lease_id}")
            if prior["status"] != "active":
                raise CoordinationError(
                    f"only an active lease can be renewed: {lease_id} is {prior['status']}"
                )
            window = ttl_seconds or prior["ttl_seconds"]
            if window < 1:
                raise CoordinationError("lease ttl_seconds must be positive")
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                renewed_at=occurred_at,
                updated_at=occurred_at,
                expires_at=utc_timestamp(moment + timedelta(seconds=window)),
                ttl_seconds=window,
            )
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="lease.renewed",
                payload={
                    "record_id": lease_id,
                    "prior_revision": prior["revision"],
                    "revision": replacement["revision"],
                    "replacement": replacement,
                },
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            return {
                "profile": PROFILE,
                "lease": replacement,
                "event_id": event["event_id"],
                "frontier": self._frontier(connection, workstate_id),
            }

    def release_lease(
        self,
        *,
        workstate_id: str,
        lease_id: str,
        actor: str,
        handoff_receipt: dict | None = None,
        reason: str = "",
        at: datetime | None = None,
    ) -> dict:
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM records WHERE workstate_id = ? "
                "AND record_id = ? AND type = 'cooperation_lease'",
                (workstate_id, lease_id),
            ).fetchone()
            if not row:
                raise CoordinationError(f"unknown lease: {lease_id}")
            prior = json.loads(row["record_json"])
            if prior["actor"] != actor:
                raise CoordinationError(f"actor does not hold lease: {lease_id}")
            if prior["status"] != "active":
                raise CoordinationError(f"lease is already terminal: {lease_id}")
            active_intents = self._records(
                connection, workstate_id, "intent", {"proposed", "active", "waiting"}
            )
            if any(intent.get("lease") == lease_id for intent in active_intents):
                raise CoordinationError("lease has an active intent; publish a terminal intent first")
            if not handoff_receipt:
                raise CoordinationError(
                    "lease release requires a verified handoff receipt for an existing artifact"
                )
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                status="released",
                updated_at=occurred_at,
                released_at=occurred_at,
                handoff_receipt=handoff_receipt,
            )
            if reason:
                replacement["release_reason"] = reason
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="lease.released",
                payload={
                    "record_id": lease_id,
                    "prior_revision": prior["revision"],
                    "revision": replacement["revision"],
                    "transition": {"from": "active", "to": "released"},
                    "replacement": replacement,
                },
                occurred_at=occurred_at,
            )
            self._project_record(connection, workstate_id, replacement, sequence)
            return {
                "profile": PROFILE,
                "lease": replacement,
                "event_id": event["event_id"],
                "frontier": self._frontier(connection, workstate_id),
            }

    def leases(self, workstate_id: str, at: datetime | None = None) -> dict:
        occurred_at = utc_timestamp(at)
        with self._transaction() as connection:
            expired = self._expire_due_leases(connection, workstate_id, occurred_at)
            active = self._records(connection, workstate_id, "cooperation_lease", {"active"})
            return {
                "profile": PROFILE,
                "workstate_id": workstate_id,
                "observed_at": occurred_at,
                "active_leases": active,
                "expired_now": [lease["id"] for lease in expired],
                "lease_enforcement": "advisory",
            }

    def resolve_overlap(
        self,
        *,
        workstate_id: str,
        overlap_id: str,
        actor: str,
        disposition: str,
        reason: str,
        at: datetime | None = None,
    ) -> dict:
        if disposition not in DISPOSITION_KINDS:
            raise CoordinationError(
                "disposition must be one of "
                f"{', '.join(sorted(DISPOSITION_KINDS))}: {disposition}"
            )
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
            target_status = "resolved" if disposition in CLEARING_DISPOSITIONS else "escalated"
            replacement = dict(prior)
            replacement.update(
                revision=prior["revision"] + 1,
                status=target_status,
                updated_at=occurred_at,
                owner=actor,
                disposition={
                    "kind": disposition,
                    "reason": reason,
                    "resolved_by": actor,
                    "recorded_at": occurred_at,
                },
            )
            event, sequence = self._append(
                connection,
                workstate_id=workstate_id,
                actor=actor,
                kind="overlap.dispositioned"
                if disposition in CLEARING_DISPOSITIONS
                else "overlap.escalated",
                payload={
                    "record_id": overlap_id,
                    "prior_revision": prior["revision"],
                    "revision": replacement["revision"],
                    "transition": {"from": prior["status"], "to": target_status},
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
            [(ledger_override.resolve(), "configured-unverified", "configured")]
            if ledger_override
            else [
                (default_ledger(project), "shared", "git-common"),
                (
                    project / ".awp-runtime" / "coordination.sqlite3",
                    "worktree-local",
                    "worktree-fallback",
                ),
            ]
        )
        failures: list[str] = []
        for ledger_path, reach, source in candidates:
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
                    "ledger_source": source,
                    "ledger": ledger,
                }
                observation = ledger.refresh(workstate_id)
                independent_participants = ledger.participant_actors(workstate_id)
                if ledger_override and len(independent_participants) >= 2:
                    reach = "shared"
                    context["ledger_reach"] = reach
                    context["shared_reach_evidence"] = {
                        "kind": "distinct-lease-actors",
                        "actors": independent_participants,
                    }
                context["binding_identity"] = {
                    "workstate_id": workstate_id,
                    "project_id": context["project_id"],
                    "store_id": ledger.binding_id(),
                    "scope_model": SCOPE_MODEL,
                    "binding_epoch": 1,
                }
                context["binding_observation"] = {
                    "observed_at": observation["observed_at"],
                    "operational_reach": reach,
                    "frontier": observation["frontier"],
                    "atomicity_mechanism": "sqlite-begin-immediate",
                    "access_mode_table": ACCESS_MODE_TABLE,
                    "scope_model_behavior": {
                        "case": "case-sensitive comparison after host path resolution",
                        "unicode": "no additional normalization",
                        "symbolic_links": "resolved by the host filesystem before repository-relative comparison",
                    },
                    "storage_assumptions": [
                        "all participants open the same SQLite database file",
                        "the filesystem preserves SQLite locking and atomic commit semantics",
                    ],
                }
                context["capsule_integrity"] = capsule_integrity(capsule)
                context["cooperation_binding"] = {
                    "type": "cooperation_binding",
                    "module": COOPERATION_MODULE,
                    "contract": "COOP-1",
                    "claim_state": "partial",
                    "capabilities": [
                        "coordination-awareness",
                        "guarded-scope-announce-check",
                        "participant-leases",
                        "checkpoint-recovery",
                    ],
                    "operational_mode": context["mode"],
                    "identity": context["binding_identity"],
                    "observation": context["binding_observation"],
                    "atomicity_mechanism": "sqlite-begin-immediate",
                    "storage_assumptions": context["binding_observation"]["storage_assumptions"],
                    "subprotocols": {
                        "work": {"enabled": True, "claim_state": "partial"},
                        "consultation": {"enabled": False},
                    },
                    "limitations": [
                        "advisory enforcement; source-control writes are not fenced",
                        "path-like physical scopes only; semantic conflicts can remain undetected",
                        "local checkpoint projection recovers explicitly from a crash between file replacement and database commit",
                    ],
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
    resolve.add_argument(
        "--disposition",
        required=True,
        choices=sorted(DISPOSITION_KINDS),
        help="the COOP-1 section 4.1 disposition being recorded",
    )
    resolve.add_argument("--reason", required=True)

    lease_enter = subparsers.add_parser(
        "lease-enter", help="enter a bounded participant lease"
    )
    lease_enter.add_argument("--actor", required=True)
    lease_enter.add_argument(
        "--location",
        default=None,
        help="execution location; defaults to the resolved project path",
    )
    lease_enter.add_argument("--scope", action="append", default=[])
    lease_enter.add_argument("--ttl-seconds", type=int, default=DEFAULT_LEASE_SECONDS)

    lease_renew = subparsers.add_parser("lease-renew", help="renew an active lease")
    lease_renew.add_argument("--actor", required=True)
    lease_renew.add_argument("--lease-id", required=True)
    lease_renew.add_argument("--ttl-seconds", type=int, default=None)

    lease_release = subparsers.add_parser("lease-release", help="release a held lease")
    lease_release.add_argument("--actor", required=True)
    lease_release.add_argument("--lease-id", required=True)
    lease_release.add_argument(
        "--handoff",
        type=Path,
        required=True,
        help="repository-relative handoff artifact that must already exist",
    )
    lease_release.add_argument("--reason", default="")

    subparsers.add_parser("leases", help="report live leases and expire due ones")

    scan = subparsers.add_parser("scan", help="read new ledger events from a durable cursor")
    scan.add_argument("--watcher-id", required=True)
    scan.add_argument("--limit", type=int, default=1000)

    checkpoint = subparsers.add_parser(
        "checkpoint", help="publish a receipt-backed canonical capsule projection"
    )
    checkpoint.add_argument("--actor", required=True)
    checkpoint.add_argument("--expected-capsule-frontier", action="append", required=True)
    checkpoint.add_argument("--expected-ledger-frontier", action="append", required=True)
    checkpoint.add_argument("--expected-digest", required=True)
    checkpoint.add_argument("--expected-capsule-digest")
    checkpoint.add_argument("--next-action", required=True)
    checkpoint.add_argument("--unresolved", action="append", default=[])
    checkpoint.add_argument("--request-id", required=True)

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
            if args.policy == "block" and context["capsule_integrity"]["state"] != "current":
                raise CoordinationError(
                    "canonical capsule integrity is not current; refresh or re-project before guarded work"
                )
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
                disposition=args.disposition,
                reason=args.reason,
            )
        elif args.command == "lease-enter":
            revision = f"git:{git_value(context['project'], 'rev-parse', 'HEAD')}"
            scopes = [
                normalize_scope(context["project"], scope)[1] for scope in args.scope
            ]
            result = ledger.enter_lease(
                workstate_id=context["workstate_id"],
                project_id=context["project_id"],
                actor=args.actor,
                location=args.location or str(context["project"]),
                base_revision=revision,
                intended_scopes=scopes,
                ttl_seconds=args.ttl_seconds,
            )
        elif args.command == "lease-renew":
            result = ledger.renew_lease(
                workstate_id=context["workstate_id"],
                lease_id=args.lease_id,
                actor=args.actor,
                ttl_seconds=args.ttl_seconds,
            )
        elif args.command == "lease-release":
            handoff_path = (context["project"] / args.handoff).resolve()
            try:
                relative_handoff = handoff_path.relative_to(context["project"].resolve())
            except ValueError as error:
                raise CoordinationError("handoff artifact resolves outside the project") from error
            if not handoff_path.is_file():
                raise CoordinationError("handoff artifact does not exist")
            handoff_receipt = {
                "path": relative_handoff.as_posix(),
                "digest": f"sha256:{hashlib.sha256(handoff_path.read_bytes()).hexdigest()}",
                "verified_at": utc_timestamp(),
            }
            result = ledger.release_lease(
                workstate_id=context["workstate_id"],
                lease_id=args.lease_id,
                actor=args.actor,
                handoff_receipt=handoff_receipt,
                reason=args.reason,
            )
        elif args.command == "leases":
            result = ledger.leases(context["workstate_id"])
        elif args.command == "scan":
            result = ledger.scan(context["workstate_id"], args.watcher_id, args.limit)
        elif args.command == "checkpoint":
            request = {
                "actor": args.actor,
                "expected_capsule_frontier": args.expected_capsule_frontier,
                "expected_ledger_frontier": args.expected_ledger_frontier,
                "expected_digest": args.expected_digest,
                "next_action": args.next_action,
                "unresolved_work": args.unresolved,
            }
            result = ledger.publish_checkpoint(
                workstate_id=context["workstate_id"],
                actor=args.actor,
                capsule=context["capsule"],
                expected_capsule_frontier=args.expected_capsule_frontier,
                expected_ledger_frontier=args.expected_ledger_frontier,
                expected_digest=args.expected_digest,
                expected_capsule_digest=args.expected_capsule_digest,
                next_action=args.next_action,
                unresolved_work=args.unresolved,
                request_id=args.request_id,
                request_hash=hashlib.sha256(
                    json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            )
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
