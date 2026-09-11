# ADR 0010: Store the COOP-1 coordination ledger in Git

**Status:** Accepted for the AWP 0.8.0 working draft
**Date:** 2026-09-11

## Context

ADR 0009 moved the COOP-2 rendezvous ledger into Git, but the COOP-1 coordination ledger (intents, scopes, leases, overlaps) still lived in `.git/awp/coordination.sqlite3`. COOP-1 and COOP-2 have no performance needs that call for a database engine, and the SQLite file carried the same cross-process and cross-machine problems as before.

COOP-1 has one requirement the per-actor refs of ADR 0009 cannot meet: announce-and-check must be atomic across participants (Cooperation Contracts section 4.1). Two actors writing their own refs at the same moment could each miss the other's overlapping scope. SQLite provided the guarantee with `BEGIN IMMEDIATE`.

## Decision

Adopt `git-coordination-v1` (section 11): one shared coordination ref per project, advanced by compare-and-swap. An operation rebuilds the state at the ref's commit, runs its check, and publishes one transaction commit on top; if the ref moved, it writes nothing and runs again on the new state. With a remote, the fast-forward push is the compare-and-swap, so the remote serializes participants on different machines.

Records are derived from events, never stored beside them, and every transaction is checked to make sure replay reproduces it. The reference implementation keeps the existing COOP-1 logic unchanged and swaps only its storage: Python's in-memory SQLite serves as a process-local query engine over the rebuilt state; nothing is written to a database file.

## Consequences

- The existing COOP-1 suite, including its simultaneous-announcement tests, passes against the Git store; new tests race four announcers on one scope (exactly one passes each round) and two clones through a shared remote.
- The SQLite coordination history migrates in one verified transaction (events, records and their order, request answers, scan cursors, binding identity).
- SQLite remains available as a legacy profile and for COOP-3 bindings that declare a scale needing a database.
- Contention on one ref is low at COOP-1 group sizes; sustained retries are to be disclosed.
