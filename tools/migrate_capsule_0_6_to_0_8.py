"""Migrate a project capsule and its discovery document from AWP 0.6.0 to the 0.8.0 draft.

AWP 0.6.0 is legacy. A capsule that still declares it is not merely dated: it
fails the active draft's own Capsule schema, which requires ``awp_version``
matching ``^0\\.8\\.[0-9]+$`` and a ``discovery: project`` front-matter field
that capsule.md states as a MUST. This tool performs that one-time metadata
migration.

It rewrites identity metadata only -- front matter, the manifest's declared
module versions and schema paths, and the snapshot's ``awp_version``. It never
touches semantic records; those remain the canonical projector's responsibility.
Running it twice is a no-op.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.awp_workstate import _render_snapshot


DRAFT_VERSION = "0.8.0"
# 0.8.0 is an unreleased working draft: no version-pinned remote artifact exists,
# so the capsule binds to the repository-relative generated bundle, which
# capsule.md permits when remote retrieval is unavailable or inappropriate.
SPECIFICATION = "dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md"
REGISTRY = "spec/drafts/0.8.0/modules.json"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SECTION = re.compile(
    r'(<!-- awp:(?:[^:\s]+:)?(manifest|snapshot):start encoding="json" -->\n)(.*?)(\n<!-- awp:(?:[^:\s]+:)?(?:manifest|snapshot):end -->)',
    re.DOTALL,
)

# Modules the capsule actually declares, mapped to the draft registry. The
# capsule declares a subset; anything it does not declare is not added here.
REQUIRED_MODULES = {
    "urn:awp:core": True,
    "urn:awp:capsule": True,
    "urn:awp:handoff": True,
    "urn:awp:artifact": True,
    "urn:awp:sync": True,
    "urn:awp:coordination": True,
}


def registry_modules(root: Path) -> dict[str, dict]:
    data = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    result = {}
    for module in data["modules"]:
        entry = {"id": module["id"], "version": module["version"]}
        schema = module.get("schema")
        if schema:
            # Registry paths are relative to spec/drafts/0.8.0/; the capsule
            # records repository-relative paths.
            entry["schema"] = schema.replace("../../../", "")
        result[module["id"]] = entry
    return result


def migrate_front_matter(text: str) -> tuple[str, list[str]]:
    match = FRONT_MATTER.search(text)
    if not match:
        raise SystemExit("capsule has no front matter")
    block = match.group(1)
    changes = []

    def set_field(block: str, field: str, value: str) -> str:
        pattern = re.compile(rf"(?m)^{re.escape(field)}:[ \t]*[^\n]*$")
        if pattern.search(block):
            current = pattern.search(block).group(0).split(":", 1)[1].strip()
            if current == value:
                return block
            changes.append(f"{field}: {current} -> {value}")
            return pattern.sub(f"{field}: {value}", block, count=1)
        changes.append(f"{field}: (absent) -> {value}")
        # Insert after `format:` so related identity fields stay together.
        anchor = re.compile(r"(?m)^format:[^\n]*$")
        if anchor.search(block):
            return anchor.sub(lambda m: m.group(0) + f"\n{field}: {value}", block, count=1)
        return block + f"\n{field}: {value}"

    block = set_field(block, "awp_version", DRAFT_VERSION)
    block = set_field(block, "specification", SPECIFICATION)
    block = set_field(block, "discovery", "project")
    return text[: match.start(1)] + block + text[match.end(1) :], changes


def _render_manifest(document: dict) -> str:
    """Render a Capsule manifest the way this capsule already stores it.

    Container values are expanded exactly one level -- each module entry and each
    representation on its own line -- and everything below that stays compact with
    json's default separators.
    """
    lines = ["{"]
    items = list(document.items())
    for index, (key, value) in enumerate(items):
        comma = "," if index < len(items) - 1 else ""
        if isinstance(value, list) and value:
            lines.append(f"  {json.dumps(key)}: [")
            for inner_index, entry in enumerate(value):
                inner_comma = "," if inner_index < len(value) - 1 else ""
                lines.append(f"    {json.dumps(entry, ensure_ascii=False)}{inner_comma}")
            lines.append(f"  ]{comma}")
        elif isinstance(value, dict) and value:
            lines.append(f"  {json.dumps(key)}: {{")
            inner_items = list(value.items())
            for inner_index, (inner_key, inner_value) in enumerate(inner_items):
                inner_comma = "," if inner_index < len(inner_items) - 1 else ""
                lines.append(
                    f"    {json.dumps(inner_key)}: {json.dumps(inner_value, ensure_ascii=False)}{inner_comma}"
                )
            lines.append(f"  }}{comma}")
        else:
            lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
    lines.append("}")
    return "\n".join(lines)


def render_section(kind: str, document: dict) -> str:
    """Render a section in the style the canonical projector already uses.

    The snapshot is not pretty-printed: the projector emits one compact line per
    record bucket, so re-serializing it with indent=2 would reformat thousands of
    lines and the next checkpoint would reformat them back.
    """
    if kind == "snapshot":
        return _render_snapshot(document)
    return _render_manifest(document)


def check_render_fidelity(text: str) -> list[str]:
    """Parse and re-render every section unchanged; report any that would churn.

    A migration that reformats bytes it did not intend to change is a migration
    whose diff cannot be reviewed, so this refuses rather than guessing.
    """
    problems = []
    for match in SECTION.finditer(text):
        _, kind, body, _ = match.groups()
        if render_section(kind, json.loads(body)) != body:
            problems.append(kind)
    return problems


def migrate_sections(text: str, modules: dict[str, dict]) -> tuple[str, list[str]]:
    changes: list[str] = []

    def replace(match: re.Match) -> str:
        opening, kind, body, closing = match.groups()
        document = json.loads(body)
        if document.get("awp_version") != DRAFT_VERSION:
            changes.append(f"{kind}.awp_version: {document.get('awp_version')} -> {DRAFT_VERSION}")
            document["awp_version"] = DRAFT_VERSION
        if kind == "manifest":
            declared = []
            for module in document.get("modules", []):
                target = modules.get(module["id"])
                if not target:
                    declared.append(module)
                    continue
                updated = dict(module)
                if module.get("version") != target["version"]:
                    changes.append(
                        f"module {module['id']}: {module.get('version')} -> {target['version']}"
                    )
                    updated["version"] = target["version"]
                if "schema" in module or "schema" in target:
                    if target.get("schema") and module.get("schema") != target["schema"]:
                        changes.append(
                            f"module {module['id']} schema: {module.get('schema')} -> {target['schema']}"
                        )
                        updated["schema"] = target["schema"]
                    elif not target.get("schema") and "schema" in updated:
                        changes.append(f"module {module['id']} schema: removed (none in registry)")
                        updated.pop("schema")
                updated["required"] = REQUIRED_MODULES.get(module["id"], module.get("required", False))
                declared.append(updated)
            document["modules"] = declared
        rendered = render_section(kind, document)
        return opening + rendered + closing

    return SECTION.sub(replace, text), changes


def migrate_discovery(root: Path) -> list[str]:
    path = root / ".awp.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("specification") == SPECIFICATION:
        return []
    changes = [f".awp.json specification: {document.get('specification')} -> {SPECIFICATION}"]
    document["specification"] = SPECIFICATION
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--capsule", type=Path)
    parser.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = parser.parse_args(argv)

    root = args.project.resolve()
    capsule = args.capsule.resolve() if args.capsule else root / json.loads(
        (root / ".awp.json").read_text(encoding="utf-8")
    )["current_workstate"]

    original = capsule.read_text(encoding="utf-8")
    churn = check_render_fidelity(original)
    if churn:
        print(json.dumps({"state": "refused", "reason": "renderer does not reproduce these sections byte-for-byte", "sections": churn}, indent=2))
        return 2
    modules = registry_modules(root)
    text, changes = migrate_front_matter(original)
    text, section_changes = migrate_sections(text, modules)
    changes.extend(section_changes)

    if args.check:
        discovery = json.loads((root / ".awp.json").read_text(encoding="utf-8"))
        if discovery.get("specification") != SPECIFICATION:
            changes.append(f".awp.json specification: {discovery.get('specification')} -> {SPECIFICATION}")
        print(json.dumps({"state": "pending" if changes else "current", "changes": changes}, indent=2))
        return 0 if not changes else 1

    changes.extend(migrate_discovery(root))
    if text != original:
        capsule.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"state": "migrated" if changes else "current", "changes": changes}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
