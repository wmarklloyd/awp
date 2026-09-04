# ADR 0002: Explicit governing-specification binding

- **Status:** Accepted for the 0.7.0 working draft
- **Date:** 2026-09-03

## Context

An AWP reader cannot safely infer protocol semantics from a filename, a moving branch, or an assumption that versions are compatible.

## Decision

A shared capsule and its repository discovery document identify the same exact governing specification artifact. A version-pinned published URI is preferred. A repository-relative local copy is permitted for sandboxed or offline environments. Readers do not silently substitute a different specification.

## Consequences

Capsule advances to 0.4.0 in the AWP 0.7.0 working draft. The later single-file discovery decision records that this binding belongs in the capsule itself; the 0.6.0 and Discovery 0.1 formats remain unchanged historical protocols.
