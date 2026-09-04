# ADR 0002: Explicit governing-specification binding

- **Status:** Accepted for the 0.7.0 working draft
- **Date:** 2026-09-03

## Context

An AWP reader cannot safely infer protocol semantics from a filename, a moving branch, or an assumption that versions are compatible.

## Decision

A shared capsule and its repository discovery document identify the same exact governing specification artifact. A version-pinned published URI is preferred. A repository-relative local copy is permitted for sandboxed or offline environments. Readers do not silently substitute a different specification.

## Consequences

Capsule advances to 0.4.0 and repository discovery advances to 0.2.0 in the AWP 0.7.0 working draft. Discovery 0.1 and AWP 0.6.0 remain unchanged historical protocols.
