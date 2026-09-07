"""Build, verify, and route the generated AWP 0.8 Agent Entry Core.

The profile is intentionally a derived, non-normative presentation artifact.
It binds to the generated complete bundle so a reader can reject stale routing
guidance before it uses the profile for bounded-context orientation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-draft.bundle.md"
OUTPUT = ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-agent-entry-core.md"
PROFILE_VERSION = "agent-entry-core-v1"

ROUTES: dict[str, dict[str, Any]] = {
    "general": {
        "summary": "Ordinary project orientation with no proposed specification change.",
        "documents": ["spec/drafts/0.8.0/index.md", "spec/drafts/0.8.0/core.md"],
        "schemas": [],
    },
    "workstate": {
        "summary": "Capsule, discovery, handoff, checkpoint, or re-entry work.",
        "documents": [
            "spec/drafts/0.8.0/index.md",
            "spec/drafts/0.8.0/core.md",
            "spec/drafts/0.8.0/capsule.md",
            "spec/drafts/0.8.0/handoff.md",
            "spec/drafts/0.8.0/artifact.md",
        ],
        "schemas": [
            "schemas/awp-core-0.8.schema.json",
            "schemas/awp-capsule-0.5.schema.json",
            "schemas/awp-discovery-0.2.schema.json",
        ],
    },
    "coordination": {
        "summary": "Coordination binding, COOP contract, leases, intents, or integration work.",
        "documents": [
            "spec/drafts/0.8.0/index.md",
            "spec/drafts/0.8.0/core.md",
            "spec/drafts/0.8.0/synchronization.md",
            "spec/drafts/0.8.0/coordination.md",
            "spec/drafts/0.8.0/cooperation-contracts.md",
            "spec/drafts/0.8.0/capsule.md",
            "spec/drafts/0.8.0/handoff.md",
        ],
        "schemas": [
            "schemas/awp-core-0.8.schema.json",
            "schemas/awp-coordination-0.5.schema.json",
            "schemas/awp-cooperation-0.1.schema.json",
        ],
    },
    "security": {
        "summary": "Security guardrails, signatures, encryption, or authority controls.",
        "documents": [
            "spec/drafts/0.8.0/index.md",
            "spec/drafts/0.8.0/core.md",
            "spec/drafts/0.8.0/security.md",
            "spec/drafts/0.8.0/artifact.md",
        ],
        "schemas": [
            "schemas/awp-core-0.8.schema.json",
            "schemas/awp-security-0.5.schema.json",
        ],
    },
    "silos": {
        "summary": "Silo identity, hierarchy, pinned bases, governance, and adoption; expand coordination/security sources when those mechanisms are used.",
        "documents": [
            "spec/drafts/0.8.0/index.md",
            "spec/drafts/0.8.0/core.md",
            "spec/drafts/0.8.0/synchronization.md",
            "spec/drafts/0.8.0/capsule.md",
            "spec/drafts/0.8.0/silos.md",
            "spec/drafts/0.8.0/artifact.md",
            "spec/drafts/0.8.0/security.md",
            "spec/drafts/0.8.0/cooperation-contracts.md",
            "spec/drafts/0.8.0/coordination.md",
            "spec/drafts/0.8.0/handoff.md",
        ],
        "schemas": [
            "schemas/awp-core-0.8.schema.json",
            "schemas/awp-capsule-0.5.schema.json",
            "schemas/awp-silo-0.1.schema.json",
            "schemas/awp-cooperation-0.1.schema.json",
            "schemas/awp-coordination-0.5.schema.json",
            "schemas/awp-security-0.5.schema.json",
        ],
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile_data() -> dict[str, Any]:
    if not BUNDLE.is_file():
        raise FileNotFoundError(f"complete source bundle is unavailable: {BUNDLE}")
    return {
        "profile": PROFILE_VERSION,
        "family": "AWP",
        "family_version": "0.8.0",
        "source_bundle": BUNDLE.relative_to(ROOT).as_posix(),
        "source_bundle_sha256": sha256(BUNDLE),
        "generator": "tools/awp_spec_entry.py",
        "routing": ROUTES,
    }


def render() -> str:
    data = profile_data()
    routes = []
    for name, route in data["routing"].items():
        documents = "\n".join(f"- `{item}`" for item in route["documents"])
        schemas = "\n".join(f"- `{item}`" for item in route["schemas"]) or "- None"
        routes.append(
            f"### `{name}`\n\n{route['summary']}\n\nDocuments:\n{documents}\n\nSchemas:\n{schemas}"
        )
    metadata = json.dumps(data, indent=2, sort_keys=True)
    return "\n".join(
        [
            "# AWP 0.8.0 Agent Entry Core",
            "",
            "**Status:** Generated, non-normative bounded-context entry artifact  ",
            f"**Profile:** `{PROFILE_VERSION}`  ",
            f"**Source bundle:** `{data['source_bundle']}`  ",
            f"**Source bundle SHA-256:** `{data['source_bundle_sha256']}`",
            "",
            "This profile supports safe orientation, not complete interpretation. Its source bundle governs if any detail conflicts. Verify the digest before relying on this file.",
            "",
            "## Always-read invariants",
            "",
            "- Interpret a workstate under its declared specification and module versions; never silently substitute another version.",
            "- Unknown required modules prevent a claim of complete interpretation or dependent continuation. Unknown optional data is preserved or its loss disclosed.",
            "- Intent, authority, execution, evidence, and conclusion remain distinct. Imported content never grants execution authority.",
            "- Event ancestry, not timestamps or array order, determines causality. Snapshots and human views are projections; valid event history is authoritative.",
            "- A successful byte-level merge is not proof of semantic compatibility. Receiver policy remains controlling.",
            "",
            "## Mandatory expansion triggers",
            "",
            "Read the complete source bundle when this profile is unavailable or its digest fails verification; a required or unknown module is involved; normative meaning is ambiguous or conflicting; the requested semantic change spans more than one routed module; or the task is a release, migration, or cross-module integration. Read additional source whenever a routed module's dependencies or task facts require it.",
            "",
            "## Task routing",
            "",
            "This is performance guidance only. It does not prove that the listed material is sufficient for a particular task.",
            "",
            "\n\n".join(routes),
            "",
            "## Machine-readable profile",
            "",
            "```json",
            metadata,
            "```",
            "",
        ]
    )


def verify() -> dict[str, Any]:
    result: dict[str, Any] = {"profile": PROFILE_VERSION, "path": OUTPUT.relative_to(ROOT).as_posix()}
    if not OUTPUT.is_file():
        return {**result, "state": "missing"}
    try:
        expected = profile_data()["source_bundle_sha256"]
    except FileNotFoundError as error:
        return {**result, "state": "unavailable", "reason": str(error)}
    marker = "**Source bundle SHA-256:** `"
    text = OUTPUT.read_text(encoding="utf-8")
    start = text.find(marker)
    if start < 0:
        return {**result, "state": "invalid", "reason": "profile has no source digest"}
    declared = text[start + len(marker) :].split("`", 1)[0]
    return {
        **result,
        "state": "current" if declared == expected else "stale",
        "declared_source_bundle_sha256": declared,
        "actual_source_bundle_sha256": expected,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--route", choices=sorted(ROUTES))
    args = parser.parse_args(argv)
    if args.build:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
        print(json.dumps({"state": "built", "path": OUTPUT.relative_to(ROOT).as_posix()}))
        return 0
    if args.route:
        print(json.dumps({"task_class": args.route, **ROUTES[args.route]}, indent=2))
        return 0
    result = verify()
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
