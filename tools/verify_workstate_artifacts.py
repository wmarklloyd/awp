"""Verify local artifact digests recorded in the repository's current AWP capsule."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / ".awp.json"


def main() -> int:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    capsule_path = (ROOT / discovery["current_workstate"]).resolve()
    if ROOT.resolve() not in capsule_path.parents:
        print("FAILED: current workstate resolves outside the repository")
        return 1
    text = capsule_path.read_text(encoding="utf-8")
    match = re.search(
        r'<!-- awp:[^:]+:snapshot:start encoding="json" -->\n(.*?)\n<!-- awp:[^:]+:snapshot:end -->',
        text,
        re.DOTALL,
    )
    if match is None:
        print("FAILED: capsule snapshot section not found")
        return 1
    snapshot = json.loads(match.group(1))
    failures = []
    checked = 0
    for artifact in snapshot["records"]["artifacts"]:
        descriptor = artifact.get("modules", {}).get("urn:awp:artifact", {})
        integrity = descriptor.get("integrity")
        if descriptor.get("status") != "retrievable" or not integrity:
            continue
        if integrity.get("algorithm") != "sha256":
            continue
        local_locations = [
            location for location in descriptor.get("locations", []) if location.get("kind") == "local"
        ]
        for location in local_locations:
            path = (ROOT / location["path"]).resolve()
            if ROOT.resolve() not in path.parents:
                failures.append(f"{artifact['id']}: path escapes repository")
                continue
            if not path.is_file():
                failures.append(f"{artifact['id']}: missing {location['path']}")
                continue
            checked += 1
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != integrity["digest"]:
                failures.append(
                    f"{artifact['id']}: expected {integrity['digest']}, got {actual}"
                )
    if failures:
        for failure in failures:
            print(failure)
        print(f"FAILED: {len(failures)} workstate artifact issue(s)")
        return 1
    print(f"OK: {checked} local workstate artifact digests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
