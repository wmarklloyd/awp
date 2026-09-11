"""`git-ledger-v1`: the COOP-2 event ledger stored in Git itself.

Every participant appends events as commits on its own ref,
``refs/awp/ledger/<workstate>/<actor>``.  Each commit holds one ``event.json``
blob and has exactly one parent: the actor's previous event.  A ref therefore
has a single writer and only ever moves forward, updated with compare-and-swap,
so concurrent writers cannot overwrite each other, events cannot be lost or
reordered within an actor, and every event is content addressed.

The ref update *is* the Git event: there is no separate signal to fall out of
step with the data.  Readers cache per-ref history and read only new commits;
a consumer cursor is the map of ref -> last processed commit, so replay after a
crash, restart, or missed notification is exact.

The same refs can be pushed to and fetched from any Git remote (a bare
repository on disk, SSH, or a hosted forge) with no merge ever needed, because
no two machines write the same ref.  Remote sync is optional and off unless a
remote is configured; a remote's visibility is the privacy boundary of every
event pushed to it.

This module deliberately exposes the small interface the rendezvous and the
supervisor already use (``binding_id``, ``refresh``, ``export_events``,
``events_after``, ``_transaction``, ``_append``, ``_frontier``), so another
store, for example one built on another version-control system, can be added
as another profile without touching delivery semantics.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from typing import Any, Iterator, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_coordination import CoordinationError, MODULE, stable_project_id
    from tools.awp_runtime import hidden_process_options
else:
    from .awp_coordination import CoordinationError, MODULE, stable_project_id
    from .awp_runtime import hidden_process_options

PROFILE = "git-ledger-v1"
REF_ROOT = "refs/awp/ledger"
BINDING_ROOT = "refs/awp/binding"
ZERO = "0" * 40
EVENT_FILE = "event.json"
IDENTITY = {"GIT_AUTHOR_NAME": "AWP ledger", "GIT_AUTHOR_EMAIL": "awp-ledger@localhost",
            "GIT_COMMITTER_NAME": "AWP ledger", "GIT_COMMITTER_EMAIL": "awp-ledger@localhost"}
_LOCK = re.compile(r"'([^']+\.lock)'")
STALE_LOCK_SECONDS = 30


def ref_token(value: str) -> str:
    """A readable, collision-resistant Git ref component for any identifier."""
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-") or "x"
    return f"{clean[:60]}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]}"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class GitLedger:
    profile = PROFILE
    read_only = False
    fallback_reason = None

    def __init__(self, project: Path, remote: str | None = None) -> None:
        self.project = Path(project).resolve()
        self.remote = remote or None
        self._cache: dict[str, tuple[str, list[tuple[str, dict]]]] = {}
        self._project_id: str | None = None

    # -- git plumbing -----------------------------------------------------
    def _git(self, *arguments: str, data: bytes | None = None, env: dict | None = None,
             check: bool = True) -> subprocess.CompletedProcess:
        environment = None
        if env:
            environment = dict(os.environ); environment.update(env)
        completed = subprocess.run(["git", *arguments], cwd=self.project, input=data, capture_output=True,
                                   check=False, env=environment, **hidden_process_options())
        if check and completed.returncode != 0:
            raise CoordinationError(f"git {' '.join(arguments[:3])} failed: "
                                    f"{completed.stderr.decode('utf-8', 'replace').strip()[:300]}")
        return completed

    def _recover_stale_lock(self, stderr: str) -> bool:
        match = _LOCK.search(stderr)
        if not match:
            return False
        lock = Path(match.group(1))
        if not lock.is_absolute():
            lock = self.project / lock
        try:
            if time.time() - lock.stat().st_mtime < STALE_LOCK_SECONDS:
                return False
            lock.unlink()
            return True
        except OSError:
            return False

    # -- identity -----------------------------------------------------------
    def project_id(self) -> str:
        if self._project_id is None:
            self._project_id = stable_project_id(self.project)
        return self._project_id

    def workstate_root(self, workstate_id: str) -> str:
        return f"{REF_ROOT}/{ref_token(workstate_id)}"

    def ref_for(self, workstate_id: str, actor: str) -> str:
        return f"{self.workstate_root(workstate_id)}/{ref_token(actor)}"

    def binding_ref(self) -> str:
        return f"{BINDING_ROOT}/{ref_token(self.project_id())}"

    def binding_id(self) -> str:
        """Binding identity shared by every clone: a JSON blob behind a ref."""
        ref = self.binding_ref()
        found = self._git("cat-file", "-p", ref, check=False)
        if found.returncode == 0:
            return json.loads(found.stdout.decode("utf-8"))["binding_id"]
        return self.initialize_binding()

    def initialize_binding(self, binding_id: str | None = None) -> str:
        ref = self.binding_ref()
        value = {"binding_id": binding_id or f"binding:{uuid.uuid4()}", "profile": PROFILE,
                 "project_id": self.project_id()}
        blob = self._git("hash-object", "-w", "--stdin", data=canonical(value).encode()).stdout.decode().strip()
        created = self._git("update-ref", ref, blob, ZERO, check=False)
        if created.returncode != 0:  # another writer created it first; theirs wins
            return json.loads(self._git("cat-file", "-p", ref).stdout.decode("utf-8"))["binding_id"]
        return value["binding_id"]

    # -- reading ------------------------------------------------------------
    def heads(self, workstate_id: str) -> dict[str, str]:
        output = self._git("for-each-ref", "--format=%(refname) %(objectname)",
                           self.workstate_root(workstate_id) + "/").stdout.decode()
        return dict(line.split(" ", 1) for line in output.splitlines() if line.strip())

    def _read_commits(self, ref: str, head: str, since: str | None) -> list[tuple[str, dict]]:
        span = f"{since}..{head}" if since else head
        shas = self._git("rev-list", "--reverse", "--first-parent", span).stdout.decode().split()
        if not shas:
            return []
        request = "".join(f"{sha}:{EVENT_FILE}\n" for sha in shas).encode()
        data = self._git("cat-file", "--batch", data=request).stdout
        events, offset = [], 0
        for sha in shas:
            header_end = data.index(b"\n", offset)
            header = data[offset:header_end].decode().split()
            if len(header) < 3 or header[1] != "blob":
                raise CoordinationError(f"{ref} commit {sha} has no {EVENT_FILE}")
            size = int(header[2])
            body = data[header_end + 1: header_end + 1 + size]
            offset = header_end + 1 + size + 1
            events.append((sha, json.loads(body.decode("utf-8"))))
        return events

    def _ref_events(self, ref: str, head: str) -> list[tuple[str, dict]]:
        cached = self._cache.get(ref)
        if cached and cached[0] == head:
            return cached[1]
        if cached and self._git("merge-base", "--is-ancestor", cached[0], head, check=False).returncode == 0:
            events = cached[1] + self._read_commits(ref, head, cached[0])
        else:
            events = self._read_commits(ref, head, None)
        self._cache[ref] = (head, events)
        return events

    def _ordered(self, workstate_id: str) -> list[tuple[str, int, str, dict]]:
        rows = []
        for ref, head in sorted(self.heads(workstate_id).items()):
            for index, (sha, event) in enumerate(self._ref_events(ref, head)):
                rows.append((ref, index, sha, event))
        # Per-actor order is exact (commit ancestry); across actors, order by
        # occurrence time, then ref and position for a deterministic total order.
        rows.sort(key=lambda row: (row[3].get("occurred_at", ""), row[0], row[1]))
        return rows

    def export_events(self, workstate_id: str) -> list[dict]:
        return [dict(row[3]) for row in self._ordered(workstate_id)]

    def events_after(self, workstate_id: str, cursor: Any = None, limit: int = 256) -> dict:
        """Events not yet covered by ``cursor`` (a map of ref -> last commit).

        Each returned event carries ``_ledger_sequence``: the cursor to persist
        once that event, and every earlier one in the page, has a disposition.
        """
        if limit < 1 or limit > 4096:
            raise CoordinationError("limit must be between 1 and 4096")
        position = dict(cursor) if isinstance(cursor, dict) else {}
        pending = []
        for ref, index, sha, event in self._ordered(workstate_id):
            done = position.get(ref)
            if done:
                shas = [item[0] for item in self._cache[ref][1]]
                if done in shas and index <= shas.index(done):
                    continue
            pending.append((ref, sha, event))
        page, running = [], dict(position)
        for ref, sha, event in pending[:limit]:
            running[ref] = sha
            page.append(dict(event, _ledger_sequence=dict(running)))
        return {"cursor": position, "next_cursor": running, "has_more": len(pending) > limit, "events": page}

    def refresh(self, workstate_id: str) -> dict:
        ordered = self._ordered(workstate_id)
        return {"frontier": [ordered[-1][3]["event_id"]] if ordered else []}

    # -- writing ------------------------------------------------------------
    @contextmanager
    def _transaction(self) -> Iterator["GitLedger"]:
        yield self

    def _frontier(self, _connection: Any, workstate_id: str) -> list[str]:
        return self.refresh(workstate_id)["frontier"]

    def _commit(self, ref: str, event: dict) -> str:
        blob = self._git("hash-object", "-w", "--stdin", data=canonical(event).encode("utf-8")).stdout.decode().strip()
        tree = self._git("mktree", data=f"100644 blob {blob}\t{EVENT_FILE}\n".encode()).stdout.decode().strip()
        stamp = event.get("occurred_at") or ""
        env = dict(IDENTITY, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp) if stamp else dict(IDENTITY)
        message = f"awp {event['kind']} {event['event_id']}\n".encode()
        delay = 0.05
        for _ in range(40):
            old = self._git("rev-parse", "--verify", "-q", ref, check=False).stdout.decode().strip()
            arguments = ["commit-tree", tree] + (["-p", old] if old else [])
            commit = self._git(*arguments, data=message, env=env).stdout.decode().strip()
            updated = self._git("update-ref", ref, commit, old or ZERO, check=False)
            if updated.returncode == 0:
                return commit
            if not self._recover_stale_lock(updated.stderr.decode("utf-8", "replace")):
                time.sleep(delay); delay = min(delay * 2, 1.0)
        raise CoordinationError(f"could not append to {ref}: the ref kept moving or stayed locked")

    def _append(self, _connection: Any = None, *, workstate_id: str, actor: str, kind: str,
                payload: dict, occurred_at: str) -> tuple[dict, None]:
        event = {
            "event_schema_version": "0.2", "module": MODULE, "kind": kind,
            "event_id": f"evt:{uuid.uuid4()}", "workstate_id": workstate_id,
            "parents": self._frontier(None, workstate_id), "occurred_at": occurred_at,
            "actor": actor, "payload": payload, "extensions": {"awp_profile": PROFILE},
        }
        ref = self.ref_for(workstate_id, actor)
        commit = self._commit(ref, event)
        event["_ref"], event["_commit"] = ref, commit
        if self.remote:
            self.push(workstate_id)
        return event, None

    # -- remote sync (optional) --------------------------------------------
    def push(self, workstate_id: str) -> dict:
        """Push this clone's ledger refs.  Refs other clones own are rejected as
        non-fast-forward if they are behind, which is harmless: their owner
        pushes them."""
        if not self.remote:
            return {"state": "local-only"}
        root = self.workstate_root(workstate_id)
        for attempt in range(3):
            done = self._git("push", "--porcelain", self.remote, f"{root}/*:{root}/*",
                             f"{BINDING_ROOT}/*:{BINDING_ROOT}/*", check=False)
            text = done.stdout.decode("utf-8", "replace")
            if done.returncode == 0 or "[rejected]" in text:
                return {"state": "pushed" if done.returncode == 0 else "partial", "detail": text[-400:]}
            time.sleep(0.5 * (attempt + 1))
        return {"state": "unavailable", "detail": done.stderr.decode("utf-8", "replace")[-400:]}

    def fetch(self, workstate_id: str) -> dict:
        if not self.remote:
            return {"state": "local-only"}
        root = self.workstate_root(workstate_id)
        done = self._git("fetch", "--quiet", self.remote, f"{root}/*:{root}/*",
                         f"{BINDING_ROOT}/*:{BINDING_ROOT}/*", check=False)
        # A non-fast-forward rejection for a ref this clone owns and has not
        # pushed yet is expected; every other ref still updates.
        return {"state": "fetched" if done.returncode == 0 else "partial",
                "detail": done.stderr.decode("utf-8", "replace")[-400:]}

    def remote_heads(self, workstate_id: str) -> dict[str, str]:
        if not self.remote:
            return {}
        output = self._git("ls-remote", self.remote, self.workstate_root(workstate_id) + "/*", check=False)
        return {name: sha for sha, name in (line.split("\t", 1) for line in output.stdout.decode().splitlines() if "\t" in line)}


def migrate(project: Path, sqlite_path: Path, workstate_id: str) -> dict:
    """Copy a SQLite rendezvous into Git refs, preserving every event unchanged.

    Idempotent: events already present (by event identifier) are skipped.  The
    SQLite binding identity is carried over so existing receipts still match.
    """
    if __package__ in {None, ""}:
        from tools.awp_coordination import CoordinationLedger
    else:
        from .awp_coordination import CoordinationLedger
    source = CoordinationLedger(sqlite_path, read_only=True)
    ledger = GitLedger(project)
    ledger.initialize_binding(source.binding_id())
    present = {event["event_id"] for event in ledger.export_events(workstate_id)}
    events = [event for event in source.export_events(workstate_id) if event["event_id"] not in present]
    by_ref: dict[str, list[dict]] = {}
    for event in events:
        by_ref.setdefault(ledger.ref_for(workstate_id, event["actor"]), []).append(event)
    # One fast-import stream: a blob, tree, and commit per event, each ref's
    # commits chained in the source ledger's order.
    lines: list[bytes] = []
    mark = 0
    for ref, items in sorted(by_ref.items()):
        head = ledger._git("rev-parse", "--verify", "-q", ref, check=False).stdout.decode().strip()
        previous = head or None
        for event in items:
            body = canonical(event).encode("utf-8")
            mark += 1
            lines += [b"blob\n", f"mark :{mark}\n".encode(), f"data {len(body)}\n".encode(), body, b"\n"]
            blob_mark = mark
            mark += 1
            when = _epoch(event.get("occurred_at"))
            message = f"awp {event['kind']} {event['event_id']}\n".encode()
            lines += [f"commit {ref}\n".encode(), f"mark :{mark}\n".encode(),
                      f"author AWP ledger <awp-ledger@localhost> {when} +0000\n".encode(),
                      f"committer AWP ledger <awp-ledger@localhost> {when} +0000\n".encode(),
                      f"data {len(message)}\n".encode(), message]
            if previous:
                lines.append(f"from {previous}\n".encode())
            lines += [f"M 100644 :{blob_mark} {EVENT_FILE}\n".encode(), b"\n"]
            previous = f":{mark}"
    if lines:
        ledger._git("fast-import", "--quiet", data=b"".join(lines) + b"done\n")
    return {"profile": PROFILE, "migrated": len(events), "refs": len(by_ref),
            "binding_id": ledger.binding_id(), "total": len(ledger.export_events(workstate_id))}


def _epoch(stamp: str | None) -> int:
    from datetime import datetime
    if not stamp:
        return int(time.time())
    return int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())


def main(argv: Sequence[str] | None = None) -> int:
    if __package__ in {None, ""}:
        from tools.awp_coordination import discover_workstate, find_project
    else:
        from .awp_coordination import discover_workstate, find_project
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    move = commands.add_parser("migrate", help="copy the SQLite rendezvous into Git refs")
    move.add_argument("--from", dest="source", type=Path, default=Path(".awp-runtime/coop2-rendezvous.sqlite3"))
    commands.add_parser("status", help="show ledger refs and event counts")
    args = parser.parse_args(argv)
    project = find_project(args.project)
    workstate_id, _ = discover_workstate(project)
    if args.command == "migrate":
        source = args.source if args.source.is_absolute() else project / args.source
        result = migrate(project, source, workstate_id)
    else:
        ledger = GitLedger(project)
        heads = ledger.heads(workstate_id)
        result = {"profile": PROFILE, "binding_id": ledger.binding_id(), "refs": {
            ref: len(ledger._ref_events(ref, sha)) for ref, sha in sorted(heads.items())}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
