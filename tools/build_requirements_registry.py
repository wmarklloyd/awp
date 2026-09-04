"""Build a deterministic inventory of BCP 14 requirements in the 0.7 draft."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "spec" / "drafts" / "0.7.0"
OUTPUT = DRAFT / "requirements.json"
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


def build() -> dict:
    requirements = []
    for code, relative in SOURCES.items():
        path = DRAFT / relative
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
                    "source": f"spec/drafts/0.7.0/{relative}",
                    "line": line_number,
                    "statement": line.strip(),
                }
            )
    return {
        "family": "AWP",
        "version": "0.7.0-draft",
        "status": "generated-review-inventory",
        "normative_authority": "source prose",
        "requirements": requirements,
    }


def main() -> int:
    OUTPUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
