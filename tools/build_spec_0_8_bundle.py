"""Build the self-contained AWP 0.8 specification bundle."""

from __future__ import annotations

from pathlib import Path


import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-draft.bundle.md"
ASSETS_OUTPUT = ROOT / "dist" / "drafts" / "0.8.0" / "AWP-0.8.0-draft.assets.md"

MODULES = (
    "core.md",
    "capsule.md",
    "handoff.md",
    "artifact.md",
    "synchronization.md",
    "silos.md",
    "coordination.md",
    "security.md",
    "adapters.md",
    "cooperation-contracts.md",
)

ASSETS = (
    ("Silo profile schema — `schemas/awp-silo-0.1.schema.json`", "schemas/awp-silo-0.1.schema.json"),
    ("Module registry — `spec/drafts/0.8.0/modules.json`", "spec/drafts/0.8.0/modules.json"),
    (
        "Requirement inventory — `spec/drafts/0.8.0/requirements.json`",
        "spec/drafts/0.8.0/requirements.json",
    ),
    ("Core schema — `schemas/awp-core-0.8.schema.json`", "schemas/awp-core-0.8.schema.json"),
    ("Cooperation schema — `schemas/awp-cooperation-0.1.schema.json`", "schemas/awp-cooperation-0.1.schema.json"),
    ("Capsule schema — `schemas/awp-capsule-0.5.schema.json`", "schemas/awp-capsule-0.5.schema.json"),
    (
        "Coordination schema — `schemas/awp-coordination-0.5.schema.json`",
        "schemas/awp-coordination-0.5.schema.json",
    ),
    ("Security schema — `schemas/awp-security-0.5.schema.json`", "schemas/awp-security-0.5.schema.json"),
    (
        "Module-registry schema — `schemas/awp-module-registry-0.8.schema.json`",
        "schemas/awp-module-registry-0.8.schema.json",
    ),
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").rstrip("\n")


def digest(relative_path: str) -> tuple[str, int]:
    data = (ROOT / relative_path).read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def build_assets() -> str:
    """The machine-readable assets, kept out of the prose bundle so an agent
    reading the specification does not also read every schema and a verbatim
    copy of every requirement statement."""
    sections = [
        "# Agent Workshare Protocol 0.8.0 — Working Draft Assets",
        "",
        "**Status:** Generated working-draft artifact; not a release  ",
        "**Companion of:** `dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`  ",
        "**Purpose:** Verbatim copies of the module registry, requirement inventory, and draft schemas for systems that cannot read `schemas/` and `spec/drafts/0.8.0/` directly. Orientation does not require this file; the bundle's asset table carries each asset's digest.",
        "",
        "Do not edit this generated file directly; regenerate it from the source files when the draft changes.",
    ]
    for title, path in ASSETS:
        sections.extend(("", "---", "", f"## {title}", "", "```json", read(path), "```"))
    return "\n".join(sections) + "\n"


def build() -> str:
    sections = [
        "# Agent Workshare Protocol 0.8.0 — Working Draft Bundle",
        "",
        "**Status:** Generated working-draft artifact; not a release  ",
        "**Source of truth:** `spec/drafts/0.8.0/*` and the schemas named in the draft module registry  ",
        "**Purpose:** Complete prose of the working draft in one file, with a digest table for its machine-readable assets.",
        "",
        "This file bundles the 0.8.0 working draft and its module specifications. The module registry, requirement inventory, and draft schemas are identified here by path, size, and SHA-256 and reproduced verbatim in the companion `AWP-0.8.0-draft.assets.md` for systems that cannot read the repository. It is not a published specification. Do not edit this generated file directly; regenerate it from the source files when the draft changes.",
        "",
        "Repository-relative links are preserved as source-location identifiers.",
        "",
        "---",
        "",
        read("spec/drafts/0.8.0/index.md"),
        "",
        "---",
        "",
        "# Bundled module specifications",
    ]

    for module in MODULES:
        sections.extend(("", "---", "", read(f"spec/drafts/0.8.0/{module}")))

    sections.extend(
        (
            "",
            "---",
            "",
            "# Machine-readable assets",
            "",
            "Identified by digest; reproduced verbatim in `dist/drafts/0.8.0/AWP-0.8.0-draft.assets.md`.",
            "",
            "| Asset | Path | Bytes | SHA-256 |",
            "|---|---|---:|---|",
        )
    )
    for title, path in ASSETS:
        name = title.split(" — ", 1)[0]
        sha, size = digest(path)
        sections.append(f"| {name} | `{path}` | {size} | `{sha}` |")

    return "\n".join(sections) + "\n"


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8", newline="\n")
    ASSETS_OUTPUT.write_text(build_assets(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} and {ASSETS_OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
