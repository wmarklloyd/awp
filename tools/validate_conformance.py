"""Validate executable AWP conformance fixtures and expected diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

try:
    from tools.awp_projector import C1Projector
except ModuleNotFoundError:  # direct execution as `python tools/validate_conformance.py`
    from awp_projector import C1Projector


ROOT = Path(__file__).resolve().parents[1]
EXPECTATIONS = ROOT / "conformance" / "expected-diagnostics"
PROJECTOR_FIXTURES = ROOT / "conformance" / "projector"


def _diagnostic_signature(diagnostic: dict) -> dict:
    return {
        "code": diagnostic.get("code"),
        "severity": diagnostic.get("severity"),
        "event_id": diagnostic.get("event_id"),
        "record_id": diagnostic.get("record_id"),
    }


def _validate_projector_fixture(path: Path) -> list[str]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    required = {"fixture_id", "workstate_id", "events", "expected"}
    missing = sorted(required - set(fixture))
    if missing:
        return [f"{path}: missing fixture fields: {', '.join(missing)}"]
    expected = fixture["expected"]
    result = C1Projector().project(fixture["events"], fixture["workstate_id"])
    failures: list[str] = []
    for field in ("frontier", "records", "contested"):
        if result[field] != expected.get(field):
            failures.append(
                f"{path}: expected {field}={expected.get(field)!r}, got {result[field]!r}"
            )
    actual_diagnostics = [_diagnostic_signature(item) for item in result["diagnostics"]]
    if actual_diagnostics != expected.get("diagnostics"):
        failures.append(
            f"{path}: expected diagnostics={expected.get('diagnostics')!r}, got {actual_diagnostics!r}"
        )
    return failures


def main() -> int:
    failures: list[str] = []
    checked = 0

    for expectation_path in sorted(EXPECTATIONS.glob("*.json")):
        manifest = json.loads(expectation_path.read_text(encoding="utf-8"))
        schema = json.loads((ROOT / manifest["schema"]).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        if "definition" in manifest:
            target = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": f"#/$defs/{manifest['definition']}",
                "$defs": schema["$defs"],
            }
        else:
            target = schema
        validator = Draft202012Validator(target, format_checker=FormatChecker())
        for case in manifest["cases"]:
            checked += 1
            document = json.loads((ROOT / case["document"]).read_text(encoding="utf-8"))
            errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
            actual_valid = not errors
            if actual_valid != case["valid"]:
                failures.append(
                    f"{case['document']}: expected valid={case['valid']}, got valid={actual_valid}"
                )
                continue
            diagnostics = " ".join(
                f"{'/'.join(str(part) for part in error.path)} {error.message}" for error in errors
            ).lower()
            for keyword in case["expected_keywords"]:
                if keyword.lower() not in diagnostics:
                    failures.append(
                        f"{case['document']}: expected diagnostic keyword {keyword!r}; got {diagnostics!r}"
                    )

    if failures:
        for failure in failures:
            print(failure)
        print(f"FAILED: {len(failures)} conformance fixture issue(s)")
        return 1

    projector_checked = 0
    for fixture_path in sorted(PROJECTOR_FIXTURES.glob("*.json")):
        projector_checked += 1
        failures.extend(_validate_projector_fixture(fixture_path))

    if failures:
        for failure in failures:
            print(failure)
        print(f"FAILED: {len(failures)} conformance fixture issue(s)")
        return 1

    print(f"OK: {checked} conformance fixtures and {projector_checked} projector fixtures matched expected outcomes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
