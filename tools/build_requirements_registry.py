"""Build a deterministic inventory of BCP 14 requirements for AWP 0.7.0."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "spec" / "drafts" / "0.7.0"
OUTPUT = DRAFT / "requirements.json"
STABLE = ROOT / "spec" / "0.7.0"
SOURCES = {
    "FAMILY": "index.md",
    "CORE": "core.md",
    "CAPSULE": "capsule.md",
    "HANDOFF": "handoff.md",
    "ARTIFACT": "artifact.md",
    "SYNC": "synchronization.md",
    "COORD": "coordination.md",
    "SECURITY": "security.md",
}
KEYWORDS = re.compile(
    r"\b(?:MUST|MUST NOT|REQUIRED|SHALL|SHALL NOT|SHOULD|SHOULD NOT|"
    r"RECOMMENDED|NOT RECOMMENDED|MAY|OPTIONAL)\b"
)


def build(
    source_dir: Path = DRAFT,
    version: str = "0.7.0-draft",
    source_prefix: str = "spec/drafts/0.7.0",
    status: str = "generated-review-inventory",
) -> dict:
    requirements = []
    for code, relative in SOURCES.items():
        path = source_dir / relative
        in_fence = False
        sequence = 0
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not KEYWORDS.search(line):
                continue
            sequence += 1
            requirements.append(
                {
                    "id": f"AWP-{code}-{sequence:03d}",
                    "source": f"{source_prefix}/{relative}",
                    "line": line_number,
                    "statement": line.strip(),
                }
            )
    return {
        "family": "AWP",
        "version": version,
        "status": status,
        "normative_authority": "source prose",
        "requirements": requirements,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stable", action="store_true", help="build the frozen stable-release inventory")
    args = parser.parse_args()
    if args.stable:
        output = STABLE / "requirements.json"
        inventory = build(STABLE, "0.7.0", "spec/0.7.0", "frozen-release-inventory")
    else:
        output = OUTPUT
        inventory = build()
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
