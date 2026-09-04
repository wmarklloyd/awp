# ADR 0001: Immutable released specifications

- **Status:** Accepted
- **Date:** 2026-09-03

## Context

AWP workstates bind to an exact governing specification. Changing a published file under the same version or schema identifier would make that binding ambiguous.

## Decision

Released specification files, schemas, generated bundles, checksums, and tags are immutable. Normative development occurs in a separately versioned working-draft directory. Post-release defects are handled through errata or a new release.

## Consequences

Repository organization distinguishes releases from drafts. Incompatible `0.x` changes increment the minor version. Release automation verifies reproducibility and recorded digests.
