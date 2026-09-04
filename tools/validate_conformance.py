"""Validate executable AWP conformance fixtures and expected diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
EXPECTATIONS = ROOT / "conformance" / "expected-diagnostics"


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

    print(f"OK: {checked} conformance fixtures matched expected outcomes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
