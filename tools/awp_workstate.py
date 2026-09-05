"""Host-owned, compare-and-swap maintenance for a single AWP Capsule.

Models submit semantic checkpoint requests; this tool owns Capsule parsing,
briefing rendering, digest calculation, atomic replacement, and recovery
reporting.  It intentionally does not infer authority from a request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from awp_coordination import (
    CHECKPOINT_FIELD,
    FRONTIER_BLOCK,
    GENERATED_AT_FIELD,
    CoordinationError,
    capsule_artifact_digest,
    capsule_integrity,
    discover_workstate,
    find_project,
    generated_region_digest,
    operational_context,
)
from awp_reentry import GENERATED, _artifact_projection, _record_index, _sections


PROFILE = "local-workstate-projector-v1"
GENERATED_DIGEST_FIELD = re.compile(r"(?m)^generated_digest:\s*[^\n]+$")
SNAPSHOT_SECTION = re.compile(
    r"(?P<start><!-- awp:[^:]+:snapshot:start encoding=\"json\" -->)\n"
    r".*?\n(?P<end><!-- awp:[^:]+:snapshot:end -->)",
    re.DOTALL,
)
JOURNAL_NAME = ".awp-runtime/workstate-projection.json"
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
RECORD_BUCKETS = {
    "goal": "goals",
    "constraint": "constraints",
    "claim": "claims",
    "evidence": "evidence",
    "decision": "decisions",
    "plan": "plans",
    "task": "tasks",
    "question": "questions",
    "artifact": "artifacts",
    "execution": "executions",
    "change": "changes",
    "risk": "risks",
    "checkpoint": "checkpoints",
    "session": "sessions",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _front_matter_value(text: str, field: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(field)}:\s*([^\n]+)$", text)
    return match.group(1).strip() if match else None


def _frontier(text: str) -> list[str]:
    match = FRONTIER_BLOCK.search(text)
    if not match:
        raise CoordinationError("capsule has no readable frontier")
    return re.findall(r"(?m)^\s*-\s*(\S+)\s*$", match.group(0))


def _require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise CoordinationError(f"{field} must be sha256 followed by 64 lowercase hex characters")
    return value


def _briefing_from_request(request: dict[str, Any]) -> str:
    supplied = request.get("briefing")
    if isinstance(supplied, str) and supplied.strip():
        briefing = supplied.strip()
    else:
        fields = request.get("briefing_fields")
        if not isinstance(fields, dict):
            raise CoordinationError("checkpoint requires briefing or briefing_fields")
        required = ("title", "status", "next_action")
        if any(not isinstance(fields.get(item), str) or not fields[item].strip() for item in required):
            raise CoordinationError("briefing_fields requires title, status, and next_action")
        lines = [
            f"# {fields['title'].strip()}",
            "",
            fields["status"].strip(),
            "",
            f"Next action: {fields['next_action'].strip()}",
        ]
        if isinstance(fields.get("constraints"), list) and fields["constraints"]:
            lines.extend(["", "Constraints:", *[f"- {item}" for item in fields["constraints"]]])
        if isinstance(fields.get("unresolved"), list) and fields["unresolved"]:
            lines.extend(["", "Unresolved:", *[f"- {item}" for item in fields["unresolved"]]])
        briefing = "\n".join(lines)
    if "<!-- awp:generated:" in briefing or "<!-- awp:generated:end -->" in briefing:
        raise CoordinationError("briefing must not contain Capsule section markers")
    if "\r" in briefing:
        raise CoordinationError("briefing must use LF line endings")
    return briefing


def _apply_records(snapshot: dict[str, Any], request: dict[str, Any]) -> list[str]:
    updates = request.get("records", [])
    if updates is None:
        return []
    if not isinstance(updates, list):
        raise CoordinationError("records must be an array")
    record_sets = snapshot.setdefault("records", {})
    updated_ids: list[str] = []
    for record in updates:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not isinstance(record.get("type"), str):
            raise CoordinationError("each record update requires id and type")
        identifier = record["id"]
        found = None
        for bucket in record_sets.values():
            if isinstance(bucket, list):
                for index, existing in enumerate(bucket):
                    if isinstance(existing, dict) and existing.get("id") == identifier:
                        found = (bucket, index, existing)
                        break
            if found:
                break
        if found:
            bucket, index, existing = found
            old_revision = existing.get("revision")
            new_revision = record.get("revision")
            if old_revision is not None and (not isinstance(new_revision, int) or new_revision <= old_revision):
                raise CoordinationError(f"record {identifier} requires a higher revision")
            if record.get("type") == "artifact":
                old_digest = existing.get("modules", {}).get("urn:awp:artifact", {}).get("integrity", {}).get("digest")
                new_digest = record.get("modules", {}).get("urn:awp:artifact", {}).get("integrity", {}).get("digest")
                if old_digest and new_digest and old_digest != new_digest:
                    if not isinstance(new_revision, int) or not record.get("supersedes"):
                        raise CoordinationError(
                            f"artifact {identifier} changed bytes; create a new ID or a revision with supersedes"
                        )
            bucket[index] = record
        else:
            bucket_name = RECORD_BUCKETS.get(record["type"])
            if not bucket_name:
                raise CoordinationError(f"unsupported snapshot record type: {record['type']}")
            record_sets.setdefault(bucket_name, []).append(record)
        updated_ids.append(identifier)
    return updated_ids


def _render_snapshot(snapshot: dict[str, Any]) -> str:
    """Render a stable Capsule snapshot without pretty-printing every record."""
    lines = ["{"]
    top_items = list(snapshot.items())
    for top_index, (key, value) in enumerate(top_items):
        top_comma = "," if top_index < len(top_items) - 1 else ""
        if key == "records" and isinstance(value, dict):
            lines.append('  "records": {')
            buckets = list(value.items())
            for bucket_index, (bucket, records) in enumerate(buckets):
                comma = "," if bucket_index < len(buckets) - 1 else ""
                payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
                lines.append(f"    {json.dumps(bucket)}: {payload}{comma}")
            lines.append(f"  }}{top_comma}")
        else:
            payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            lines.append(f"  {json.dumps(key)}: {payload}{top_comma}")
    lines.append("}")
    return "\n".join(lines)


def _replace_once(pattern: re.Pattern[str], text: str, replacement: str, label: str) -> str:
    rewritten, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise CoordinationError(f"capsule has no readable {label}")
    return rewritten


def _proposal(capsule: Path, request: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    original_bytes = capsule.read_bytes()
    original = original_bytes.decode("utf-8").replace("\r\n", "\n")
    old_digest = capsule_artifact_digest(capsule)
    expected_capsule = _require_digest(request.get("expected_capsule_digest"), "expected_capsule_digest")
    if old_digest != expected_capsule:
        raise CoordinationError("capsule whole-artifact digest is stale")
    integrity = capsule_integrity(capsule)
    expected_generated = _require_digest(
        request.get("expected_generated_digest"), "expected_generated_digest"
    )
    if integrity.get("state") != "current" or integrity.get("computed_digest") != expected_generated:
        raise CoordinationError("capsule generated-region digest is stale")
    expected_frontier = request.get("expected_frontier")
    if not isinstance(expected_frontier, list) or _frontier(original) != expected_frontier:
        raise CoordinationError("capsule semantic frontier is stale")
    if request.get("mode", "checkpoint") == "no_change":
        return original_bytes, {
            "status": "no_change",
            "profile": PROFILE,
            "capsule_digest": old_digest,
            "generated_digest": expected_generated,
            "frontier": expected_frontier,
        }
    if request.get("mode", "checkpoint") != "checkpoint":
        raise CoordinationError("mode must be checkpoint or no_change")
    new_frontier = request.get("frontier", expected_frontier)
    if not isinstance(new_frontier, list) or not all(isinstance(item, str) and item for item in new_frontier):
        raise CoordinationError("frontier must be an array of nonempty identifiers")
    checkpoint = request.get("checkpoint")
    if not isinstance(checkpoint, str) or not checkpoint.strip():
        raise CoordinationError("checkpoint requires a nonempty checkpoint identifier")
    briefing = _briefing_from_request(request)
    sections = _sections(original)
    snapshot = sections["snapshot"]
    updated_records = _apply_records(snapshot, request)
    snapshot["frontier"] = new_frontier
    snapshot["generated_at"] = request.get("generated_at") or utc_timestamp()
    generated_match = GENERATED.search(original)
    if not generated_match:
        raise CoordinationError("capsule has no generated briefing")
    generated_marker_start = original[generated_match.start():].split("\n", 1)[0]
    generated_marker_end = "<!-- awp:generated:end -->"
    generated_digest = generated_region_digest(
        generated_marker_start + "\n" + briefing + "\n" + generated_marker_end
    )
    replacement = generated_marker_start + "\n" + briefing + "\n" + generated_marker_end
    rewritten = original[:generated_match.start()] + replacement + original[generated_match.end():]
    if updated_records:
        snapshot_payload = _render_snapshot(snapshot)
        rewritten = _replace_once(
            SNAPSHOT_SECTION,
            rewritten,
            SNAPSHOT_SECTION.search(rewritten).group("start") + "\n" + snapshot_payload + "\n" + SNAPSHOT_SECTION.search(rewritten).group("end"),
            "snapshot",
        )
    rewritten = _replace_once(
        FRONTIER_BLOCK,
        rewritten,
        "frontier:\n" + "".join(f"  - {item}\n" for item in new_frontier),
        "frontier",
    )
    rewritten = _replace_once(CHECKPOINT_FIELD, rewritten, f"checkpoint: {checkpoint}", "checkpoint")
    rewritten = _replace_once(
        GENERATED_AT_FIELD,
        rewritten,
        f"generated_at: {request.get('generated_at') or utc_timestamp()}",
        "generated_at",
    )
    rewritten = _replace_once(
        GENERATED_DIGEST_FIELD,
        rewritten,
        f"generated_digest: {generated_digest}",
        "generated_digest",
    )
    new_bytes = rewritten.encode("utf-8")
    return new_bytes, {
        "status": "prepared",
        "profile": PROFILE,
        "previous_capsule_digest": old_digest,
        "previous_generated_digest": expected_generated,
        "capsule_digest": f"sha256:{hashlib.sha256(new_bytes).hexdigest()}",
        "generated_digest": generated_digest,
        "frontier": new_frontier,
        "checkpoint": checkpoint,
        "updated_record_ids": updated_records,
    }


@contextmanager
def _capsule_lock(project: Path) -> Iterator[None]:
    lock_dir = project / ".awp-runtime"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "workstate.lock"
    with lock_path.open("a+b") as handle:
        handle.seek(0)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, payload: bytes) -> None:
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _journal_path(project: Path) -> Path:
    return project / JOURNAL_NAME


def _write_journal(path: Path, value: dict[str, Any]) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(path, payload)


def checkpoint(project: Path, capsule: Path, request: dict[str, Any]) -> dict[str, Any]:
    with _capsule_lock(project):
        proposed, receipt = _proposal(capsule, request)
        if receipt["status"] == "no_change":
            return receipt
        journal_path = _journal_path(project)
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        journal = {
            "profile": PROFILE,
            "state": "prepared",
            "capsule": str(capsule.relative_to(project).as_posix()),
            "request_id": request.get("request_id"),
            "expected_capsule_digest": receipt["previous_capsule_digest"],
            "proposed_capsule_digest": receipt["capsule_digest"],
        }
        _write_journal(journal_path, journal)
        _atomic_write(capsule, proposed)
        journal["state"] = "file_replaced"
        _write_journal(journal_path, journal)
        journal_path.unlink(missing_ok=True)
        receipt["status"] = "complete"
        receipt["request_id"] = request.get("request_id")
        return receipt


def recover(project: Path, capsule: Path) -> dict[str, Any]:
    path = _journal_path(project)
    if not path.is_file():
        return {"profile": PROFILE, "state": "none"}
    journal = json.loads(path.read_text(encoding="utf-8"))
    current = capsule_artifact_digest(capsule)
    if current == journal.get("proposed_capsule_digest"):
        state = "recovered"
        path.unlink()
    elif current == journal.get("expected_capsule_digest"):
        state = "pending"
    else:
        state = "diverged"
    return {"profile": PROFILE, "state": state, "current_capsule_digest": current, "journal": journal}


def status(project: Path, capsule: Path) -> dict[str, Any]:
    text = capsule.read_text(encoding="utf-8")
    integrity = capsule_integrity(capsule)
    result = {
        "profile": PROFILE,
        "capsule": capsule.relative_to(project).as_posix(),
        "capsule_digest": capsule_artifact_digest(capsule),
        "integrity": integrity,
        "semantic_frontier": _frontier(text),
        "checkpoint": _front_matter_value(text, "checkpoint"),
        "pending_projection": _journal_path(project).is_file(),
    }
    context = operational_context(project)
    if not context.get("fallback"):
        binding_frontier = context["binding_observation"]["frontier"]
        result["binding_observation"] = {
            "frontier": binding_frontier,
            "reach": context["binding_observation"]["operational_reach"],
            "freshness": "same" if binding_frontier == result["semantic_frontier"] else "operational_events_ahead",
        }
    else:
        result["binding_observation"] = {
            "freshness": "unavailable",
            "diagnostic": context.get("diagnostic"),
        }
    return result


def verify(project: Path, capsule: Path, full: bool) -> dict[str, Any]:
    sections = _sections(capsule.read_text(encoding="utf-8"))
    index = _record_index(sections["snapshot"])
    resume = next(record for record in index.values() if record.get("type") == "resume")
    identifiers = list(index) if full else list(resume.get("required_artifacts", []))
    artifacts = [
        _artifact_projection(index[item], project)
        for item in identifiers
        if item in index and index[item].get("type") == "artifact"
    ]
    failures = [
        item["id"]
        for item in artifacts
        if item.get("status") == "retrievable" and item.get("verification_state") != "current"
    ]
    return {
        "profile": PROFILE,
        "scope": "full" if full else "active",
        "capsule_digest": capsule_artifact_digest(capsule),
        "capsule_integrity": capsule_integrity(capsule),
        "checked": len(artifacts),
        "failures": failures,
        "status": "complete" if not failures else "incomplete",
    }


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--capsule", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("recover")
    verify_command = commands.add_parser("verify")
    verify_command.add_argument("--full", action="store_true")
    checkpoint_command = commands.add_parser("checkpoint")
    checkpoint_command.add_argument("--request", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        project = find_project(args.project)
        capsule = args.capsule.resolve() if args.capsule else discover_workstate(project)[1]
        if args.command == "status":
            result = status(project, capsule)
        elif args.command == "recover":
            result = recover(project, capsule)
        elif args.command == "verify":
            result = verify(project, capsule, args.full)
        else:
            request = json.loads(args.request.read_text(encoding="utf-8"))
            if not isinstance(request, dict):
                raise CoordinationError("checkpoint request must be a JSON object")
            result = checkpoint(project, capsule, request)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("status", result.get("state")) not in {"incomplete", "diverged"} else 2
    except (CoordinationError, OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"profile": PROFILE, "status": "rejected", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
