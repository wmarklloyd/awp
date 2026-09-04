"""Validate the AWP 0.7 modular specification family."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "spec" / "drafts" / "0.7.0" / "index.md"
SPEC_DIR = ROOT / "spec" / "drafts" / "0.7.0"
REGISTRY = SPEC_DIR / "modules.json"
REGISTRY_SCHEMA = ROOT / "schemas" / "awp-module-registry-0.7.schema.json"
CORE_SCHEMA = ROOT / "schemas" / "awp-core-0.7.schema.json"
COORDINATION_SCHEMA = ROOT / "schemas" / "awp-coordination-0.4.schema.json"
DISCOVERY_SCHEMA = ROOT / "schemas" / "awp-discovery-0.2.schema.json"

CORE_RECORD_TYPES = {
    "goal",
    "constraint",
    "claim",
    "evidence",
    "decision",
    "plan",
    "task",
    "question",
    "artifact",
    "execution",
    "change",
    "risk",
    "checkpoint",
    "session",
}
ACTOR_TYPES = {"human", "agent", "model", "service", "automation", "organization", "unknown"}
MODULE_RECORD_OWNERS = {
    "handoff": "urn:awp:handoff",
    "resume": "urn:awp:handoff",
}
COORDINATION_RECORD_TYPES = {
    "semantic_definition",
    "scope",
    "intent",
    "observed_scope",
    "overlap",
    "conflict",
    "negotiation",
    "commitment",
    "contract",
    "precondition",
    "precondition_result",
    "change_set",
    "verification_result",
    "dependency",
    "integration_plan",
    "integration_result",
    "lease",
}


def validator_for(schema: dict, definition: str | None = None) -> Draft202012Validator:
    if definition is None:
        target = schema
    else:
        target = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"#/$defs/{definition}",
            "$defs": schema["$defs"],
        }
    return Draft202012Validator(target, format_checker=FormatChecker())


def compatible(actual: str, requirement: str) -> bool:
    if requirement.endswith(".x"):
        return actual.startswith(requirement[:-1])
    return actual == requirement


def json_kind(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    if "event_schema_version" in value:
        return "event"
    if {"awp_version", "workstate_id", "title", "modules", "representations"} <= value.keys():
        return "manifest"
    if {"awp_version", "workstate_id", "frontier", "records", "modules"} <= value.keys():
        return "snapshot"
    if "authority_id" in value:
        return "authority"
    if value.get("type") in ACTOR_TYPES:
        return "actor"
    if value.get("type") in CORE_RECORD_TYPES:
        return "coreRecord"
    return None


def validate_registry(failures: list[str]) -> dict:
    registry_schema = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(registry_schema)
    for error in sorted(validator_for(registry_schema).iter_errors(registry), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in error.path) or "<root>"
        failures.append(f"module registry at {path}: {error.message}")

    modules = registry["modules"]
    by_id = {module["id"]: module for module in modules}
    if len(by_id) != len(modules):
        failures.append("module registry contains duplicate module IDs")

    core = by_id.get("urn:awp:core")
    if core is None or core["status"] != "required" or core["version"] != "0.7.0":
        failures.append("module registry must contain required urn:awp:core version 0.7.0")

    for module in modules:
        document = (SPEC_DIR / module["document"]).resolve()
        if not document.is_file() or SPEC_DIR.resolve() not in document.parents:
            failures.append(f"{module['id']} document is missing or outside the version directory")
        else:
            text = document.read_text(encoding="utf-8")
            if f"**Module ID:** `{module['id']}`" not in text:
                failures.append(f"{module['id']} document does not declare its registry module ID")
            if not text.startswith(f"# {module['name']} {module['version']}\n"):
                failures.append(f"{module['id']} document heading does not match registry name/version")
        if "schema" in module:
            schema_path = (SPEC_DIR / module["schema"]).resolve()
            if not schema_path.is_file() or ROOT.resolve() not in schema_path.parents:
                failures.append(f"{module['id']} schema path is missing or outside the workspace")
        for dependency in module["dependencies"]:
            target = by_id.get(dependency["id"])
            if target is None:
                failures.append(f"{module['id']} depends on unknown {dependency['id']}")
            elif not compatible(target["version"], dependency["version"]):
                failures.append(
                    f"{module['id']} requires {dependency['id']} {dependency['version']}, "
                    f"registry has {target['version']}"
                )

    for document in registry.get("informative_documents", []):
        path = (SPEC_DIR / document["document"]).resolve()
        if not path.is_file() or SPEC_DIR.resolve() not in path.parents:
            failures.append(f"informative document {document['name']} is missing or outside the version directory")
        elif not path.read_text(encoding="utf-8").startswith(
            f"# {document['name']} {document['version']}\n"
        ):
            failures.append(f"informative document {document['name']} heading does not match registry")
    return registry


def validate_markdown_links(documents: list[Path], failures: list[str]) -> None:
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("urn:"):
                continue
            resolved = (document.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{document.relative_to(ROOT)} has broken link: {raw_target}")


def validate_manifest_modules(
    value: dict, registry: dict, location: str, failures: list[str]
) -> None:
    registered = {module["id"]: module for module in registry["modules"]}
    declarations = value["modules"]
    declared = {module["id"]: module for module in declarations}
    if len(declared) != len(declarations):
        failures.append(f"{location}: manifest contains duplicate module IDs")
    for module_id, declaration in declared.items():
        module = registered.get(module_id)
        if module is None:
            continue
        if declaration["version"] != module["version"]:
            failures.append(
                f"{location}: {module_id} declares {declaration['version']}, "
                f"family registry has {module['version']}"
            )
        for dependency in module["dependencies"]:
            dependency_declaration = declared.get(dependency["id"])
            if dependency_declaration is None:
                failures.append(f"{location}: {module_id} omits dependency {dependency['id']}")
                continue
            if not compatible(dependency_declaration["version"], dependency["version"]):
                failures.append(
                    f"{location}: {module_id} needs {dependency['id']} {dependency['version']}, "
                    f"manifest declares {dependency_declaration['version']}"
                )
            if declaration["required"] and not dependency_declaration["required"]:
                failures.append(
                    f"{location}: required {module_id} has optional dependency {dependency['id']}"
                )
    for module_id in value.get("module_data", {}):
        if module_id not in declared:
            failures.append(f"{location}: module_data contains undeclared {module_id}")


def validate_examples(
    documents: list[Path], registry: dict, failures: list[str]
) -> tuple[int, int]:
    core_schema = json.loads(CORE_SCHEMA.read_text(encoding="utf-8"))
    coordination_schema = json.loads(COORDINATION_SCHEMA.read_text(encoding="utf-8"))
    discovery_schema = json.loads(DISCOVERY_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(core_schema)
    Draft202012Validator.check_schema(coordination_schema)
    Draft202012Validator.check_schema(discovery_schema)
    checked_json = 0
    checked_digests = 0

    for document in documents:
        text = document.read_text(encoding="utf-8")
        for block_index, block in enumerate(re.findall(r"```json\n(.*?)\n```", text, re.DOTALL), start=1):
            try:
                value = json.loads(block)
            except json.JSONDecodeError as error:
                failures.append(
                    f"{document.relative_to(ROOT)} JSON block {block_index} is invalid: {error.msg}"
                )
                continue
            if isinstance(value, dict) and "awp_discovery_version" in value:
                checked_json += 1
                location = f"{document.relative_to(ROOT)} JSON block {block_index}"
                for error in sorted(
                    validator_for(discovery_schema).iter_errors(value),
                    key=lambda item: list(item.path),
                ):
                    path = "/".join(str(part) for part in error.path) or "<root>"
                    failures.append(f"{location} (discovery) at {path}: {error.message}")
                continue
            if isinstance(value, dict) and value.get("type") in MODULE_RECORD_OWNERS:
                checked_json += 1
                expected_owner = MODULE_RECORD_OWNERS[value["type"]]
                if not isinstance(value.get("id"), str) or not value["id"]:
                    failures.append(
                        f"{document.relative_to(ROOT)} JSON block {block_index}: "
                        "module record has no non-empty id"
                    )
                if value.get("module") != expected_owner:
                    failures.append(
                        f"{document.relative_to(ROOT)} JSON block {block_index}: "
                        f"{value['type']} must declare module {expected_owner}"
                    )
                continue
            if isinstance(value, dict) and value.get("type") in COORDINATION_RECORD_TYPES:
                checked_json += 1
                location = f"{document.relative_to(ROOT)} JSON block {block_index}"
                for error in sorted(
                    validator_for(coordination_schema, "coordinationRecord").iter_errors(value),
                    key=lambda item: list(item.path),
                ):
                    path = "/".join(str(part) for part in error.path) or "<root>"
                    failures.append(f"{location} (coordinationRecord) at {path}: {error.message}")
                continue
            kind = json_kind(value)
            if kind is None:
                continue
            checked_json += 1
            location = f"{document.relative_to(ROOT)} JSON block {block_index}"
            for error in sorted(validator_for(core_schema, kind).iter_errors(value), key=lambda item: list(item.path)):
                path = "/".join(str(part) for part in error.path) or "<root>"
                failures.append(
                    f"{location} ({kind}) at {path}: "
                    f"{error.message}"
                )
            if kind == "event" and value.get("module") == "urn:awp:coordination":
                for error in sorted(
                    validator_for(coordination_schema, "coordinationEvent").iter_errors(value),
                    key=lambda item: list(item.path),
                ):
                    path = "/".join(str(part) for part in error.path) or "<root>"
                    failures.append(f"{location} (coordinationEvent) at {path}: {error.message}")
            if kind == "manifest":
                validate_manifest_modules(value, registry, location, failures)

        for block_index, block in enumerate(re.findall(r"```markdown\n(.*?)\n```", text, re.DOTALL), start=1):
            normalized = block.replace("\r\n", "\n")
            match = re.search(
                r"generated_digest: sha256:([0-9a-f]{64}).*?"
                r"<!-- awp:generated:start -->\n(.*?)\n<!-- awp:generated:end -->",
                normalized,
                re.DOTALL,
            )
            if match is None:
                continue
            checked_digests += 1
            declared, generated = match.groups()
            actual = hashlib.sha256(generated.encode("utf-8")).hexdigest()
            if declared != actual:
                failures.append(
                    f"{document.relative_to(ROOT)} Markdown block {block_index} generated digest "
                    f"declares {declared}, calculated {actual}"
                )
    return checked_json, checked_digests


def main() -> int:
    failures: list[str] = []
    registry = validate_registry(failures)
    documents = [FAMILY, *sorted(SPEC_DIR.glob("*.md"))]
    validate_markdown_links(documents, failures)
    checked_json, checked_digests = validate_examples(documents, registry, failures)

    if failures:
        print("\n".join(failures))
        print(f"FAILED: {len(failures)} issue(s)")
        return 1
    print(
        f"OK: module registry, schemas, links, {checked_json} JSON examples, "
        f"and {checked_digests} briefing digest(s) validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

