# ADR 0004: Single-file capsule is the portable discovery unit

- **Status:** Accepted for the 0.7.0 working draft
- **Date:** 2026-09-04
- **Supersedes:** The companion-file portion of ADR 0002 for the 0.7.0 draft

## Context

AWP's preferred exchange representation is a self-contained Markdown capsule. Requiring a second project-root JSON file for a short filename pointer and duplicated specification reference weakens that portability and creates two files that must remain synchronized.

## Decision

The 0.7.0 draft makes the Markdown capsule its own discovery unit. Its front matter carries `format: single-file-capsule`, `discovery: self`, and the exact governing `specification`. A host may receive an explicit capsule path or locate one by the conventional `.awp.md` filename. A companion `.awp.json` file is not required for a portable capsule and is not part of the canonical workstate representation.

The stable 0.6.0 discovery document and schema remain immutable historical formats.

## Consequences

There is one canonical portable file and no pointer/specification duplication. Hosts must provide a path or apply an unambiguous filename convention; they must not silently choose among multiple capsules. Repository-specific launchers may still point directly to the capsule.
