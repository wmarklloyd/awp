"""`git-coordination-v1`: the COOP-1 coordination ledger stored in Git.

COOP-1 requires announce-and-check to be atomic across participants
(Cooperation Contracts section 4.1).  This profile provides that with one
shared ref per project, ``refs/awp/coordination/<project>``, updated by
compare-and-swap:

1. read the ref's current commit and rebuild the ledger state at that commit;
2. run the operation (for example: check a new intent against every active
   intent and lease, then announce it);
3. write the operation's events as one commit whose only parent is that
   commit, and move the ref only if it still points there.

If another participant moved the ref first, nothing is written; the operation
is re-run against the new state.  No participant can act between the check and
the write, which is the same guarantee SQLite's ``BEGIN IMMEDIATE`` gave, with
no database file shared between processes, operating systems, or machines.

Each commit carries one ``transaction.json``: the AWP events the operation
appended, plus the request-idempotency and scan-cursor entries it wrote.
Intents, scopes, leases, and overlaps are not stored separately: they are
rebuilt from the events' ``replacement`` records, and every transaction is
checked to make sure that rebuilding reproduces exactly what the operation
wrote.  Python's built-in in-memory SQLite is used only as the query engine
for that rebuilt state inside one process; nothing is written to a database
file.

With a remote configured, the push itself is the compare-and-swap: a push that
is not a fast-forward is rejected, and the operation is re-run on the fetched
state.
"""

from __future__ import annotations

from contextlib import contextmanager
import functools
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Iterator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coordination import CoordinationError, CoordinationLedger
    from tools.awp_git_ledger import GitLedger, IDENTITY, ZERO, canonical, ref_token
else:
    from .awp_coordination import CoordinationError, CoordinationLedger
    from .awp_git_ledger import GitLedger, IDENTITY, ZERO, canonical, ref_token

PROFILE = "git-coordination-v1"
REF_ROOT = "refs/awp/coordination"
BINDING_ROOT = "refs/awp/binding-coordination"
TRANSACTION_FILE = "transaction.json"
WRITE_METHODS = ("begin", "publish_change_set", "transition_intent", "refresh", "interact_overlap",
                 "record_checkpoint", "publish_checkpoint", "enter_lease", "renew_lease", "release_lease",
                 "leases", "resolve_overlap", "scan")
SCHEMA = """
CREATE TABLE events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
    workstate_id TEXT NOT NULL, kind TEXT NOT NULL, occurred_at TEXT NOT NULL, actor TEXT NOT NULL,
    event_json TEXT NOT NULL);
CREATE INDEX events_workstate_sequence ON events(workstate_id, sequence);
CREATE TABLE records (workstate_id TEXT NOT NULL, record_id TEXT NOT NULL, type TEXT NOT NULL,
    revision INTEGER NOT NULL, status TEXT NOT NULL, record_json TEXT NOT NULL,
    updated_sequence INTEGER NOT NULL, PRIMARY KEY(workstate_id, record_id));
CREATE INDEX records_workstate_type_status ON records(workstate_id, type, status);
CREATE TABLE watchers (workstate_id TEXT NOT NULL, watcher_id TEXT NOT NULL, cursor INTEGER NOT NULL,
    PRIMARY KEY(workstate_id, watcher_id));
CREATE TABLE requests (workstate_id TEXT NOT NULL, request_id TEXT NOT NULL, request_hash TEXT NOT NULL,
    response_json TEXT NOT NULL, PRIMARY KEY(workstate_id, request_id));
CREATE TABLE binding_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


class _Conflict(Exception):
    """Another participant moved the coordination ref first."""


class GitCoordinationLedger(CoordinationLedger):
    profile = PROFILE
    atomicity_mechanism = "git compare-and-swap on one shared coordination ref"

    def __init__(self, project: Path, remote: str | None = None) -> None:
        self.git = GitLedger(project, remote=remote)
        self.project = self.git.project
        self.remote = remote or None
        self.path = self.project / ".git" / "awp" / "(git refs)"  # descriptive only; no file is used
        self.read_only = False
        self._db: sqlite3.Connection | None = None
        self._head: str | None = None
        self._depth = 0
        self._cached_project_root = self.project

    # -- identity -----------------------------------------------------------
    def ref(self) -> str:
        return f"{REF_ROOT}/{ref_token(self.git.project_id())}"

    def binding_id(self) -> str:
        ref = f"{BINDING_ROOT}/{ref_token(self.git.project_id())}"
        found = self.git._git("cat-file", "-p", ref, check=False)
        if found.returncode == 0:
            return json.loads(found.stdout.decode("utf-8"))["binding_id"]
        return self.initialize_binding()

    def initialize_binding(self, binding_id: str | None = None) -> str:
        import uuid
        ref = f"{BINDING_ROOT}/{ref_token(self.git.project_id())}"
        value = {"binding_id": binding_id or f"binding:{uuid.uuid4()}", "profile": PROFILE,
                 "project_id": self.git.project_id()}
        blob = self.git._git("hash-object", "-w", "--stdin", data=canonical(value).encode()).stdout.decode().strip()
        if self.git._git("update-ref", ref, blob, ZERO, check=False).returncode != 0:
            return json.loads(self.git._git("cat-file", "-p", ref).stdout.decode("utf-8"))["binding_id"]
        return value["binding_id"]

    # -- state rebuilt from Git ---------------------------------------------
    def _current_head(self) -> str | None:
        if self.remote:
            self.git._git("fetch", "--quiet", self.remote, f"+{self.ref()}:{self.ref()}", check=False)
        head = self.git._git("rev-parse", "--verify", "-q", self.ref(), check=False).stdout.decode().strip()
        return head or None

    def _new_db(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:", isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.executescript(SCHEMA)
        return connection

    def _transactions(self, since: str | None, head: str) -> list[dict]:
        span = f"{since}..{head}" if since else head
        shas = self.git._git("rev-list", "--reverse", "--first-parent", span).stdout.decode().split()
        if not shas:
            return []
        data = self.git._git("cat-file", "--batch",
                             data="".join(f"{sha}:{TRANSACTION_FILE}\n" for sha in shas).encode()).stdout
        result, offset = [], 0
        for sha in shas:
            end = data.index(b"\n", offset)
            header = data[offset:end].decode().split()
            if len(header) < 3 or header[1] != "blob":
                raise CoordinationError(f"coordination commit {sha} has no {TRANSACTION_FILE}")
            size = int(header[2])
            result.append(json.loads(data[end + 1:end + 1 + size].decode("utf-8")))
            offset = end + 1 + size + 1
        return result

    @staticmethod
    def _replay(connection: sqlite3.Connection, transaction: dict) -> None:
        for event in transaction.get("events", []):
            cursor = connection.execute(
                "INSERT INTO events(event_id, workstate_id, kind, occurred_at, actor, event_json) VALUES (?, ?, ?, ?, ?, ?)",
                (event["event_id"], event["workstate_id"], event["kind"], event["occurred_at"], event["actor"],
                 json.dumps(event, sort_keys=True, separators=(",", ":"))))
            replacement = (event.get("payload") or {}).get("replacement")
            if isinstance(replacement, dict) and "id" in replacement:
                CoordinationLedger._project_record(connection, event["workstate_id"], replacement, int(cursor.lastrowid))
        for workstate_id, request_id, request_hash, response_json in transaction.get("requests", []):
            connection.execute("INSERT OR REPLACE INTO requests VALUES (?, ?, ?, ?)",
                               (workstate_id, request_id, request_hash, response_json))
        for workstate_id, watcher_id, cursor in transaction.get("watchers", []):
            connection.execute("INSERT OR REPLACE INTO watchers VALUES (?, ?, ?)", (workstate_id, watcher_id, cursor))

    def _sync(self) -> sqlite3.Connection:
        head = self._current_head()
        if self._db is not None and head == self._head:
            return self._db
        incremental = (self._db is not None and self._head and head and
                       self.git._git("merge-base", "--is-ancestor", self._head, head, check=False).returncode == 0)
        if not incremental:
            self._db, since = self._new_db(), None
        else:
            since = self._head
        if head:
            for transaction in self._transactions(since, head):
                self._replay(self._db, transaction)
        self._head = head
        return self._db

    # -- the CoordinationLedger storage hooks ---------------------------------
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:  # read-only use by the base class
        yield self._sync()

    @staticmethod
    def _snapshot(connection: sqlite3.Connection) -> dict:
        return {
            "sequence": connection.execute("SELECT COALESCE(MAX(sequence), 0) FROM events").fetchone()[0],
            "requests": {(r[0], r[1]) for r in connection.execute("SELECT workstate_id, request_id FROM requests")},
            "watchers": {(r[0], r[1]): r[2] for r in connection.execute("SELECT workstate_id, watcher_id, cursor FROM watchers")},
            "records": {(r[0], r[1]): (json.loads(r[2]), r[3], r[4], r[5]) for r in connection.execute(
                "SELECT workstate_id, record_id, record_json, type, revision, status FROM records")},
        }

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        if self._depth:
            raise CoordinationError("nested coordination transactions are not supported")
        connection = self._sync()
        parent = self._head
        before = self._snapshot(connection)
        connection.execute("BEGIN")
        self._depth += 1
        try:
            yield connection
            after = self._snapshot(connection)
            events = [json.loads(row[0]) for row in connection.execute(
                "SELECT event_json FROM events WHERE sequence > ? ORDER BY sequence", (before["sequence"],))]
            requests = [list(row) for row in connection.execute(
                "SELECT workstate_id, request_id, request_hash, response_json FROM requests")
                if (row[0], row[1]) not in before["requests"]]
            watchers = [[key[0], key[1], value] for key, value in after["watchers"].items()
                        if before["watchers"].get(key) != value]
            self._check_records(before["records"], after["records"], events)
            if events or requests or watchers:
                self._publish(parent, {"profile": PROFILE, "events": events, "requests": requests, "watchers": watchers})
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            self._db, self._head = None, None  # rebuild from Git on the next use
            raise
        finally:
            self._depth -= 1

    @staticmethod
    def _check_records(before: dict, after: dict, events: list[dict]) -> None:
        """Fail closed unless the events alone reproduce every record change."""
        changed = {key: value for key, value in after.items() if before.get(key) != value}
        derived: dict = {}
        for event in events:
            replacement = (event.get("payload") or {}).get("replacement")
            if isinstance(replacement, dict) and "id" in replacement:
                derived[(event["workstate_id"], replacement["id"])] = (
                    replacement, replacement.get("type"), replacement.get("revision"), replacement.get("status"))
        if changed != derived:
            raise CoordinationError("coordination records changed without a replayable event; nothing was written")

    def _publish(self, parent: str | None, transaction: dict) -> None:
        git = self.git
        blob = git._git("hash-object", "-w", "--stdin", data=canonical(transaction).encode("utf-8")).stdout.decode().strip()
        tree = git._git("mktree", data=f"100644 blob {blob}\t{TRANSACTION_FILE}\n".encode()).stdout.decode().strip()
        kinds = sorted({event["kind"] for event in transaction["events"]}) or ["state"]
        message = f"awp coordination: {', '.join(kinds)[:200]}\n".encode()
        commit = git._git("commit-tree", tree, *(["-p", parent] if parent else []), data=message, env=IDENTITY).stdout.decode().strip()
        if self.remote:
            pushed = git._git("push", "--porcelain", self.remote, f"{commit}:{self.ref()}", check=False)
            if pushed.returncode != 0:
                raise _Conflict()  # the remote moved: re-run against the fetched state
        updated = git._git("update-ref", self.ref(), commit, parent or ZERO, check=False)
        if updated.returncode != 0:
            if git._recover_stale_lock(updated.stderr.decode("utf-8", "replace")):
                if git._git("update-ref", self.ref(), commit, parent or ZERO, check=False).returncode == 0:
                    self._head = commit
                    return
            raise _Conflict()
        self._head = commit

    def participant_actors(self, workstate_id: str) -> list[str]:
        connection = self._sync()
        rows = connection.execute("SELECT DISTINCT actor FROM events WHERE workstate_id = ? AND kind = 'lease.entered' ORDER BY actor",
                                  (workstate_id,)).fetchall()
        return [str(row["actor"]) for row in rows]


def _retrying(method):
    @functools.wraps(method)
    def run(self, *args, **kwargs):
        delay = 0.02
        for _ in range(60):
            try:
                return method(self, *args, **kwargs)
            except _Conflict:
                time.sleep(delay); delay = min(delay * 2, 0.5)
        raise CoordinationError("the coordination ref kept moving; the operation was not applied")
    return run


for _name in WRITE_METHODS:
    setattr(GitCoordinationLedger, _name, _retrying(getattr(CoordinationLedger, _name)))


def migrate(project: Path, sqlite_path: Path) -> dict:
    """Copy a SQLite coordination ledger into Git in one transaction, unchanged.

    Events keep their identifiers and documents, records are rebuilt from them
    and compared with the SQLite projection, request responses are carried
    over, scan cursors are translated to the new sequence numbers, and the
    binding identity is preserved.  Refuses to run if the Git ledger already
    has history.
    """
    source = CoordinationLedger(sqlite_path, read_only=True)
    target = GitCoordinationLedger(project)
    if target._current_head():
        raise CoordinationError("the Git coordination ledger already has history; refusing to migrate over it")
    target.initialize_binding(source.binding_id())
    with source._connect() as connection:
        rows = connection.execute("SELECT sequence, event_json FROM events ORDER BY sequence").fetchall()
        events = [json.loads(row["event_json"]) for row in rows]
        old_sequences = [int(row["sequence"]) for row in rows]
        requests = [list(row) for row in connection.execute(
            "SELECT workstate_id, request_id, request_hash, response_json FROM requests ORDER BY workstate_id, request_id")]
        old_watchers = [tuple(row) for row in connection.execute("SELECT workstate_id, watcher_id, cursor FROM watchers")]
        source_records = {(r["workstate_id"], r["record_id"]): (json.loads(r["record_json"]), r["updated_sequence"])
                          for r in connection.execute("SELECT * FROM records")}
    new_sequence = {old: index + 1 for index, old in enumerate(old_sequences)}
    watchers = []
    for workstate_id, watcher_id, cursor in old_watchers:
        covered = [new_sequence[s] for s in old_sequences if s <= cursor]
        watchers.append([workstate_id, watcher_id, covered[-1] if covered else 0])
    transaction = {"profile": PROFILE, "migrated_from": "local-ledger-awareness-v1 (SQLite)",
                   "events": events, "requests": requests, "watchers": watchers}
    check = target._new_db()
    GitCoordinationLedger._replay(check, transaction)
    rebuilt = {(r["workstate_id"], r["record_id"]): (json.loads(r["record_json"]), r["updated_sequence"])
               for r in check.execute("SELECT * FROM records")}
    if {k: v[0] for k, v in rebuilt.items()} != {k: v[0] for k, v in source_records.items()}:
        raise CoordinationError("replaying the SQLite events does not reproduce its records; nothing was written")
    order = lambda records: [k for k, _ in sorted(records.items(), key=lambda item: item[1][1])]
    if order(rebuilt) != order({k: (v[0], v[1]) for k, v in source_records.items()}):
        raise CoordinationError("replay changes record order; nothing was written")
    target._publish(None, transaction)
    return {"profile": PROFILE, "events": len(events), "records": len(rebuilt), "requests": len(requests),
            "watchers": len(watchers), "binding_id": target.binding_id(), "ref": target.ref()}


if __name__ == "__main__":
    import argparse
    if __package__ in {None, ""}:
        from tools.awp_coordination import default_ledger, find_project
    else:
        from .awp_coordination import default_ledger, find_project
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    move = sub.add_parser("migrate", help="copy the SQLite coordination ledger into Git")
    move.add_argument("--from", dest="source", type=Path)
    sub.add_parser("status")
    args = parser.parse_args()
    project = find_project(args.project)
    if args.command == "migrate":
        print(json.dumps(migrate(project, args.source or default_ledger(project)), indent=2, sort_keys=True))
    else:
        ledger = GitCoordinationLedger(project)
        connection = ledger._sync()
        print(json.dumps({"profile": PROFILE, "ref": ledger.ref(), "head": ledger._head,
                          "events": connection.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                          "records": connection.execute("SELECT COUNT(*) FROM records").fetchone()[0],
                          "binding_id": ledger.binding_id()}, indent=2, sort_keys=True))
