# ADR 0008: The capsule is the only persisted project workstate

**Status:** Accepted for the AWP 0.8.0 working draft
**Date:** 2026-09-10
**Supersedes:** The persisted `awp.entry.json` entry-slice practice

## Context

The project already chose the Markdown Capsule as its normative discovery and
workstate document.  Maintaining a generated `awp.entry.json` beside it adds
a second persisted representation, digest synchronization, stale-slice
handling, and a distinct re-entry path.  Its only benefit is a local context
and I/O optimization.  That benefit does not justify another durable project
file or another interpretation path.

## Decision

`awp.awp.md` is the only persisted project workstate and re-entry input.
`awp.entry.json` is retired: implementations MUST NOT generate, read, require,
or commit it.  Re-entry validates and reads the Capsule directly.

A host may construct an in-memory bounded presentation from the Capsule for a
participant after it has validated that Capsule.  Such a presentation is
ephemeral, has no independent filename or lifecycle, and is never a project
artifact or authority.

## Consequences

The project has one durable entry file and one re-entry code path.  The former
entry-slice cache, its command-line flag, generated-artifact references, and
tests must be removed.  Re-entry may cost more local I/O than a cache hit, but
it no longer risks stale companion state or makes a participant choose between
two files.
