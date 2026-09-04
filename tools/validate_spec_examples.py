"""Validate the AWP core schema and applicable JSON examples in the draft."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "0.3.0" / "index.md"
SCHEMA = ROOT / "schemas" / "awp-core-0.3.schema.json"

CORE_TYPES = {
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
    "handoff",
}
ACTOR_TYPES = {"human", "agent", "model", "service", "automation", "organization", "unknown"}


def schema_kind(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    if "event_schema_version" in value:
        return "event"
    if "awp_version" in value and "title" in value:
        return "manifest"
    if "awp_version" in value and "records" in value:
        return "snapshot"
    if value.get("type") in CORE_TYPES:
        return "coreRecord"
    if "authority_id" in value:
        return "authority"
    if value.get("type") in ACTOR_TYPES:
        return "actor"
    return None


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    text = SPEC.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)

    failures: list[str] = []
    checked = 0
    for index, block in enumerate(blocks, start=1):
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        kind = schema_kind(value)
        if kind is None:
            continue
        checked += 1
        wrapper = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"#/$defs/{kind}",
            "$defs": schema["$defs"],
        }
        errors = sorted(Draft202012Validator(wrapper).iter_errors(value), key=lambda error: list(error.path))
        for error in errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            failures.append(f"JSON block {index} ({kind}) at {location}: {error.message}")

    markdown_blocks = re.findall(r"```markdown\n(.*?)\n```", text, re.DOTALL)
    briefing_count = 0
    for index, block in enumerate(markdown_blocks, start=1):
        match = re.search(
            r"generated_digest: sha256:([0-9a-f]{64}).*?"
            r"<!-- awp:generated:start -->\n(.*?)\n<!-- awp:generated:end -->",
            block.replace("\r\n", "\n"),
            re.DOTALL,
        )
        if match is None:
            continue
        briefing_count += 1
        declared, generated = match.groups()
        actual = hashlib.sha256(generated.encode("utf-8")).hexdigest()
        if declared != actual:
            failures.append(
                f"Markdown block {index} generated digest: declared {declared}, calculated {actual}"
            )

    if failures:
        print("\n".join(failures))
        print(
            f"FAILED: {len(failures)} validation error(s) across "
            f"{checked} JSON and {briefing_count} briefing examples"
        )
        return 1
    print(f"OK: schema, {checked} JSON examples, and {briefing_count} briefing digests validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
