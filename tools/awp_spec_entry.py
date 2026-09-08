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
REGISTRY = ROOT / "spec" / "drafts" / "0.8.0" / "requirements.json"
OUTPUT = ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-agent-entry-core.md"
PROFILE_VERSION = "agent-entry-core-v2"

READ_PLAN = (
    "Read the routed requirement statements first; they are the normative authority and cost a fraction "
    "of the prose. Open a listed module only when a statement is ambiguous or you need its rationale. "
    "Open a listed schema only when authoring or validating a record of that type; the schema digest "
    "is enough for orientation."
)

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


def registry_statements(documents: Sequence[str]) -> list[dict[str, str]]:
    """The requirement statements that govern the given source modules, in registry order."""
    if not REGISTRY.is_file():
        raise FileNotFoundError(f"requirement registry is unavailable: {REGISTRY}")
    wanted = set(documents)
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [
        {"id": item["id"], "source": item["source"], "statement": item["statement"]}
        for item in data.get("requirements", [])
        if item.get("source") in wanted
    ]


def schema_digest(relative_path: str) -> dict[str, Any]:
    """A compact orientation view of a JSON Schema: what record types it defines and
    what each requires, without the constraints an author needs only when writing one."""
    path = ROOT / relative_path
    schema = json.loads(path.read_text(encoding="utf-8"))
    definitions = {}
    for name, definition in (schema.get("$defs") or {}).items():
        if not isinstance(definition, dict):
            continue
        entry: dict[str, Any] = {}
        if isinstance(definition.get("required"), list):
            entry["required"] = definition["required"]
        enums = {
            key: value["enum"]
            for key, value in (definition.get("properties") or {}).items()
            if isinstance(value, dict) and isinstance(value.get("enum"), list)
        }
        if enums:
            entry["enums"] = enums
        constant = {
            key: value["const"]
            for key, value in (definition.get("properties") or {}).items()
            if isinstance(value, dict) and "const" in value
        }
        if constant:
            entry["const"] = constant
        definitions[name] = entry
    return {
        "path": relative_path,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "title": schema.get("title") or schema.get("$id"),
        "top_level_required": schema.get("required", []),
        "definitions": definitions,
    }


def route_view(name: str) -> dict[str, Any]:
    route = ROUTES[name]
    statements = registry_statements(route["documents"])
    return {
        "task_class": name,
        "summary": route["summary"],
        "read_plan": READ_PLAN,
        "statement_count": len(statements),
        "statement_bytes": sum(len(item["statement"]) for item in statements),
        "statements": statements,
        "schema_digests": [schema_digest(item) for item in route["schemas"]],
        "modules_on_demand": route["documents"],
        "schemas_on_demand": route["schemas"],
    }


def render_statements(name: str) -> str:
    """Compact Markdown: one requirement per line, grouped by source module."""
    view = route_view(name)
    lines = [
        f"# AWP 0.8.0 routed requirements — `{name}`",
        "",
        view["summary"],
        "",
        f"{view['statement_count']} statements, {view['statement_bytes']} bytes. {READ_PLAN}",
    ]
    current = None
    for item in view["statements"]:
        if item["source"] != current:
            current = item["source"]
            lines.extend(("", f"## {current}", ""))
        lines.append(f"- **{item['id']}** {item['statement']}")
    if view["schema_digests"]:
        lines.extend(("", "## Schema digests (open the file only to author a record)", ""))
        for digest in view["schema_digests"]:
            names = ", ".join(sorted(digest["definitions"])) or "none"
            lines.append(f"- `{digest['path']}` ({digest['bytes']} B, sha256 `{digest['sha256'][:16]}…`): {names}")
    return "\n".join(lines) + "\n"


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
        statements = registry_statements(route["documents"])
        documents = "\n".join(f"- `{item}`" for item in route["documents"])
        schemas = "\n".join(f"- `{item}`" for item in route["schemas"]) or "- None"
        routes.append(
            f"### `{name}`\n\n{route['summary']}\n\n"
            f"Read first: `python tools/awp_spec_entry.py --route {name} --statements` "
            f"({len(statements)} statements, {sum(len(item['statement']) for item in statements)} bytes).\n\n"
            f"Modules on demand:\n{documents}\n\nSchemas on demand (digest in the route output):\n{schemas}"
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
            READ_PLAN,
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
    parser.add_argument("--statements", action="store_true", help="with --route: print the routed requirement statements as compact Markdown instead of JSON")
    args = parser.parse_args(argv)
    if args.build:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
        print(json.dumps({"state": "built", "path": OUTPUT.relative_to(ROOT).as_posix()}))
        return 0
    if args.route:
        if args.statements:
            print(render_statements(args.route), end="")
        else:
            print(json.dumps(route_view(args.route), indent=2))
        return 0
    result = verify()
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "current" else 2


if __name__ == "__main__":
    raise SystemExit(main())
