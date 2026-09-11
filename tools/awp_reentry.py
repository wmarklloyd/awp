"""Produce a bounded, briefing-first AWP project re-entry view.

The host reads and validates the complete capsule.  The model-facing output is
limited to the generated briefing, the active Resume/Handoff/Checkpoint, the
ordered ``read_first`` records, and compact required-artifact descriptors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.awp_coordination import (
    CoordinationError,
    capsule_artifact_digest,
    capsule_integrity,
    find_project,
)


PROFILE = "selective-reentry-v1"
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
GENERATED = re.compile(
    r"<!-- awp:generated:start -->\n(.*?)\n<!-- awp:generated:end -->", re.DOTALL
)
JSON_SECTION = re.compile(
    r'<!-- awp:(?:[^:\s]+:)?(manifest|snapshot):start encoding="json" -->\n'
    r"(.*?)\n"
    r"<!-- awp:(?:[^:\s]+:)?\1:end -->",
    re.DOTALL,
)


def _metadata(text: str) -> dict[str, str]:
    match = FRONT_MATTER.search(text)
    if not match:
        raise CoordinationError("capsule has no leading front matter")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def _sections(text: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for kind, payload in JSON_SECTION.findall(text):
        if kind in result:
            raise CoordinationError(f"capsule has more than one {kind} section")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as error:
            raise CoordinationError(f"capsule {kind} section is invalid JSON: {error}") from error
        if not isinstance(parsed, dict):
            raise CoordinationError(f"capsule {kind} section must be an object")
        result[kind] = parsed
    if "manifest" not in result or "snapshot" not in result:
        raise CoordinationError("capsule requires manifest and snapshot JSON sections")
    return result


def _walk_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("id"), str) and isinstance(value.get("type"), str):
            yield value
        for child in value.values():
            yield from _walk_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_records(child)


def _record_index(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in _walk_records(
        {"records": snapshot.get("records", {}), "modules": snapshot.get("modules", {})}
    ):
        identifier = record["id"]
        if identifier in index and index[identifier] != record:
            raise CoordinationError(f"duplicate record identifier in capsule: {identifier}")
        index[identifier] = record
    return index


def _choose_resume(
    index: dict[str, dict[str, Any]], checkpoint_id: str | None
) -> dict[str, Any]:
    resumes = [record for record in index.values() if record.get("type") == "resume"]
    if checkpoint_id:
        matching = [record for record in resumes if record.get("checkpoint") == checkpoint_id]
        if len(matching) == 1:
            return matching[0]
    if len(resumes) != 1:
        raise CoordinationError("capsule does not identify exactly one active Resume record")
    return resumes[0]


def _artifact_projection(record: dict[str, Any], root: Path) -> dict[str, Any]:
    artifact = record.get("modules", {}).get("urn:awp:artifact", {})
    projection = {
        "id": record.get("id"),
        "name": record.get("name"),
        "status": artifact.get("status"),
        "locations": artifact.get("locations", []),
        "integrity": artifact.get("integrity"),
    }
    if artifact.get("status") in {"superseded", "historical", "archived"}:
        projection["verification_state"] = "historical"
        return projection
    local = next(
        (
            location
            for location in projection["locations"]
            if location.get("kind") == "local" and location.get("path")
        ),
        None,
    )
    integrity = projection["integrity"] or {}
    if local and integrity.get("algorithm") == "sha256" and integrity.get("digest"):
        path = (root / local["path"]).resolve()
        if not path.is_file():
            projection["verification_state"] = "unavailable"
        else:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            projection["verification_state"] = (
                "current" if actual == integrity["digest"] else "modified"
            )
            if projection["verification_state"] == "modified":
                projection["actual_digest"] = actual
    else:
        projection["verification_state"] = "unverifiable"
    return projection


def build_reentry_view(capsule: Path, *, brief_only: bool = False) -> dict[str, Any]:
    text = capsule.read_text(encoding="utf-8").replace("\r\n", "\n")
    metadata = _metadata(text)
    generated = GENERATED.search(text)
    if not generated:
        raise CoordinationError("capsule has no generated briefing")
    view: dict[str, Any] = {
        "profile": PROFILE,
        "source": {
            "path": capsule.as_posix(),
            "bytes": len(capsule.read_bytes()),
            "characters": len(text),
        },
        "integrity": capsule_integrity(capsule),
        "metadata": {
            key: metadata.get(key)
            for key in (
                "awp_version",
                "specification",
                "workstate_id",
                "checkpoint",
                "generated_at",
                "generated_digest",
            )
        },
        "briefing": generated.group(1),
    }
    if brief_only:
        view["selection"] = {"state": "brief_only", "complete": False}
        return view

    sections = _sections(text)
    manifest = sections["manifest"]
    snapshot = sections["snapshot"]
    index = _record_index(snapshot)
    resume = _choose_resume(index, metadata.get("checkpoint"))
    checkpoint = index.get(str(resume.get("checkpoint")))
    handoff = index.get(str(resume.get("handoff"))) if resume.get("handoff") else None
    read_first_ids = list(resume.get("read_first", []))
    required_artifact_ids = list(resume.get("required_artifacts", []))
    missing = [
        identifier
        for identifier in [*read_first_ids, *required_artifact_ids]
        if identifier not in index
    ]
    selected = [index[identifier] for identifier in read_first_ids if identifier in index]
    artifacts = [
        _artifact_projection(index[identifier], capsule.parent)
        for identifier in required_artifact_ids
        if identifier in index
    ]
    artifact_failures = [
        artifact["id"]
        for artifact in artifacts
        if artifact["verification_state"] != "current"
    ]
    selection_complete = (
        view["integrity"]["state"] == "current"
        and not missing
        and not artifact_failures
    )
    # A resume that still points at finished work sends the next session to the
    # wrong place, and nothing else notices: the records exist, so the index and
    # the digests are all satisfied.  Report it rather than silently orienting a
    # cold session toward work that is already done.
    closed_states = {"completed", "superseded", "withdrawn", "closed", "resolved"}
    stale_references = sorted(
        {
            record["id"]
            for record in selected
            if isinstance(record, dict) and record.get("status") in closed_states
        }
    )
    view.update(
        manifest={
            "awp_version": manifest.get("awp_version"),
            "workstate_id": manifest.get("workstate_id"),
            "title": manifest.get("title"),
            "modules": manifest.get("modules", []),
        },
        entry={
            "resume": resume,
            "handoff": handoff,
            "checkpoint": checkpoint,
            "read_first": selected,
            "required_artifacts": artifacts,
        },
        selection={
            "state": "complete" if selection_complete else "incomplete",
            "complete": selection_complete,
            "missing_record_ids": missing,
            "required_artifact_failures": artifact_failures,
            "stale_resume_references": stale_references,
            "indexed_record_count": len(index),
            "selected_record_count": len(selected),
        },
    )
    return view


def bounded_json(view: dict[str, Any], max_output_bytes: int) -> tuple[str, bool]:
    coordination = view.get("coordination")
    if coordination is not None and coordination.get("state") != "available":
        # An unread or unverifiable mailbox is never equivalent to an empty
        # mailbox.  Keep the safety gate closed even when the failure makes the
        # serialized view smaller.
        view["selection"]["state"] = "incomplete"
        view["selection"]["complete"] = False
    # The measurement fields affect their own serialization size. Iterate to a
    # fixed point so output_bytes describes the bytes a participant receives.
    # The iteration can enter a 2-cycle when the rounded ratio flips between
    # "5.4" and "5.41" and shifts the size by one byte; that is a rounding tie,
    # not a failure, so settle on the larger size rather than refusing entry.
    seen: list[int] = []
    for _ in range(8):
        rendered = json.dumps(view, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        required = len(rendered.encode("utf-8"))
        ratio = round(view["source"]["bytes"] / max(required, 1), 2)
        if (
            view["selection"].get("output_bytes") == required
            and view["selection"].get("source_to_output_ratio") == ratio
        ):
            break
        if required in seen:
            view["selection"]["measurement"] = "settled-on-rounding-tie"
            # Two more passes with the marker present: the first absorbs the
            # marker's width, the second confirms; take the larger if they tie.
            widths = []
            for _ in range(2):
                rendered = json.dumps(view, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
                widths.append(len(rendered.encode("utf-8")))
                view["selection"]["output_bytes"] = max(widths)
                view["selection"]["source_to_output_ratio"] = round(view["source"]["bytes"] / max(widths), 2)
            rendered = json.dumps(view, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            required = len(rendered.encode("utf-8"))
            break
        seen.append(required)
        view["selection"]["output_bytes"] = required
        view["selection"]["source_to_output_ratio"] = ratio
    if max_output_bytes and required > max_output_bytes:
        refusal = {
            "profile": PROFILE,
            "source": view["source"],
            "integrity": view["integrity"],
            "metadata": view["metadata"],
            "briefing": view["briefing"],
            "selection": {
                "state": "budget_exceeded",
                "complete": False,
                "required_output_bytes": required,
                "max_output_bytes": max_output_bytes,
                "omitted": ["entry"],
                "reason": "entry context was omitted; coordination status was retained",
            },
        }
        if "coordination" in view:
            refusal["coordination"] = view["coordination"]
        return json.dumps(refusal, indent=2, sort_keys=True, ensure_ascii=False) + "\n", False
    return rendered, bool(view["selection"].get("complete"))


def _self_observation(binding: dict[str, Any], actor: str, registration: dict[str, Any] | None) -> dict[str, Any]:
    """What this actor's own doorbell looks like from the binding's side, compactly."""
    mine = next((item for item in binding.get("participant_watchers", []) if item.get("actor") == actor), {})
    inbound = {
        pair.split("->", 1)[0]: value.get("signal_reach")
        for pair, value in binding.get("signal_reach", {}).items()
        if pair.endswith("->" + actor)
    }
    result = {
        "declared_observation": mine.get("declared_observation", "unregistered"),
        "watcher_liveness": mine.get("watcher_liveness", "none"),
        "inbound_signal_reach": inbound,
    }
    if registration is not None:
        result["registered"] = "confirmed" if registration.get("publication") == "confirmed" else "failed"
        result["registration_deduplicated"] = bool(registration.get("deduplicated"))
    return result


def coordination_entry_view(project: Path, actor: str, register_observation: str | None = None) -> dict[str, Any]:
    """Read the durable COOP-2 mailbox and doorbell during project entry.

    This is intentionally a read-only safety net.  The doorbell watcher remains
    the low-latency wake path; entry-time inspection guarantees that a missed
    wake cannot hide an authorized interaction from a newly started session.
    """
    try:
        project_root = str(Path(__file__).resolve().parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from tools.awp_coop2 import Rendezvous

        rendezvous = Rendezvous(project)
        registration = None
        if register_observation:
            # Explicit publication requested by the entering session; the check
            # itself stays read-only.  Joining is idempotent per declared mode.
            registration = rendezvous.join(actor, [], observation=register_observation)
        inbox = rendezvous.inbox(actor)
        binding = inbox.get("binding", {})
        observation = binding.get("observation", {})
        doorbell = binding.get("doorbell", {})
        open_items = [
            {
                key: item[key]
                for key in ("interaction_id", "sender", "subject", "purpose", "decision_owner")
                if item.get(key) is not None
            }
            for item in inbox.get("inbox", [])
        ]
        return {
            "state": "available",
            "read_verified": True,
            "actor": actor,
            "binding": {
                key: binding[key]
                for key in ("binding_id", "profile", "ledger_profile", "project_id", "workstate_id", "reach", "delivery_mode", "operational_mode", "read_only_reason")
                if binding.get(key) is not None
            },
            "frontier": observation.get("frontier", []),
            "doorbell": {
                key: doorbell[key]
                for key in ("state", "event_id", "interaction_id", "kind")
                if doorbell.get(key) is not None
            },
            "open_count": len(open_items),
            "open_items": open_items,
            "response_count": len(inbox.get("responses", [])),
            "self": _self_observation(binding, actor, registration),
        }
    except (CoordinationError, OSError, ValueError, sqlite3.Error) as error:
        return {
            "state": "unavailable",
            "read_verified": False,
            "actor": actor,
            "diagnostic": "AWP-COORD-LEDGER-UNAVAILABLE",
            "reason": str(error),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--capsule", type=Path)
    parser.add_argument("--brief-only", action="store_true")
    parser.add_argument("--actor", help="actor identity for the bounded COOP-2 entry check")
    parser.add_argument(
        "--register-observation",
        choices=["watcher", "on-entry-only"],
        help="also publish this actor's observation mode to the rendezvous (explicit; the entry check itself stays read-only)",
    )
    parser.add_argument("--max-output-bytes", type=int, default=24_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        project = find_project(args.project)
        if args.capsule:
            capsule = args.capsule.resolve()
        else:
            discovery = json.loads((project / ".awp.json").read_text(encoding="utf-8"))
            capsule = (project / discovery["current_workstate"]).resolve()
        view = build_reentry_view(capsule, brief_only=args.brief_only)
        if not args.brief_only:
            view["coordination"] = (
                coordination_entry_view(project, args.actor, args.register_observation)
                if args.actor
                else {
                    "state": "skipped",
                    "diagnostic": "AWP-COORD-ACTOR-REQUIRED",
                    "reason": "entry recovery requires the host-bound actor identity",
                }
            )
        rendered, complete = bounded_json(view, args.max_output_bytes)
        print(rendered, end="")
        return 0 if complete or args.brief_only else 2
    except (CoordinationError, OSError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"profile": PROFILE, "state": "unavailable", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
