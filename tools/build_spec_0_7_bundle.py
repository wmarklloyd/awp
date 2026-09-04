"""Build the self-contained AWP 0.7 specification bundle."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "drafts" / "0.7.0" / "AWP-0.7.0-draft.bundle.md"

MODULES = (
    "core.md",
    "capsule.md",
    "handoff.md",
    "artifact.md",
    "synchronization.md",
    "coordination.md",
    "security.md",
    "adapters.md",
)

ASSETS = (
    ("Module registry — `spec/drafts/0.7.0/modules.json`", "spec/drafts/0.7.0/modules.json"),
    (
        "Requirement inventory — `spec/drafts/0.7.0/requirements.json`",
        "spec/drafts/0.7.0/requirements.json",
    ),
    ("Core schema — `schemas/awp-core-0.7.schema.json`", "schemas/awp-core-0.7.schema.json"),
    (
        "Coordination schema — `schemas/awp-coordination-0.4.schema.json`",
        "schemas/awp-coordination-0.4.schema.json",
    ),
    (
        "Module-registry schema — `schemas/awp-module-registry-0.7.schema.json`",
        "schemas/awp-module-registry-0.7.schema.json",
    ),
    ("Discovery schema — `schemas/awp-discovery-0.2.schema.json`", "schemas/awp-discovery-0.2.schema.json"),
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").rstrip("\n")


def build() -> str:
    sections = [
        "# Agent Workstate Protocol 0.7.0 — Working Draft Bundle",
        "",
        "**Status:** Generated working-draft artifact; not a release  ",
        "**Source of truth:** `spec/drafts/0.7.0/*` and the schemas named in the draft module registry  ",
        "**Purpose:** Self-contained copy for agents or systems that cannot follow repository-relative links.",
        "",
        "This file bundles the 0.7.0 working draft, its module specifications, the module registry, and the draft schemas. It is not a published specification. Do not edit this generated file directly; regenerate it from the source files when the draft changes.",
        "",
        "Repository-relative links are preserved as source-location identifiers. When those paths are unavailable, use the corresponding embedded module or machine-readable asset later in this bundle.",
        "",
        "---",
        "",
        read("spec/drafts/0.7.0/index.md"),
        "",
        "---",
        "",
        "# Bundled module specifications",
    ]

    for module in MODULES:
        sections.extend(("", "---", "", read(f"spec/drafts/0.7.0/{module}")))

    sections.extend(("", "---", "", "# Bundled machine-readable assets"))
    for title, path in ASSETS:
        sections.extend(("", f"## {title}", "", "```json", read(path), "```"))

    return "\n".join(sections) + "\n"


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
