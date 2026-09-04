"""Check repository-relative Markdown links without performing network access."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", "dist"}


def main() -> int:
    failures = []
    checked = 0
    for document in sorted(ROOT.rglob("*.md")):
        if SKIP_PARTS.intersection(document.relative_to(ROOT).parts):
            continue
        for raw_target in LINK.findall(document.read_text(encoding="utf-8")):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            target = unquote(target.split("#", 1)[0])
            if not target or "://" in target or target.startswith(("mailto:", "urn:")):
                continue
            checked += 1
            resolved = (document.parent / target).resolve()
            if ROOT.resolve() != resolved and ROOT.resolve() not in resolved.parents:
                failures.append(f"{document.relative_to(ROOT)}: link escapes repository: {raw_target}")
            elif not resolved.exists():
                failures.append(f"{document.relative_to(ROOT)}: missing link target: {raw_target}")

    if failures:
        for failure in failures:
            print(failure)
        print(f"FAILED: {len(failures)} broken repository link(s)")
        return 1
    print(f"OK: {checked} repository-relative Markdown links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
