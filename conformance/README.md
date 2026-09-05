# Conformance assets

This directory contains machine-readable examples with explicit expected outcomes. It separates executable evidence from examples embedded in explanatory prose.

- `valid/` contains documents that must validate under the named schema.
- `invalid/` contains documents that must fail for the stated reason.
- `expected-diagnostics/` records stable expected validation outcomes.
- `projector/` contains transport-neutral C1 event histories with expected frontiers, materialized records, contested conditions, and diagnostic signatures.
- `interoperability/` reserves results from independent implementations.

Passing structural fixtures is necessary but not sufficient for protocol conformance. Cross-record, event-graph, authority, and projection invariants require procedural fixtures and independently implemented processors.

The default ledger workflow is a protocol contract for an AWP-aware agent/model and its host binding. A model may emit records or requested operations without directly persisting them. SQLite and `tools/awp_coordination.py` are optional reference aids; procedural C1 fixtures remain transport-neutral and record the expected frontier, materialized state, and diagnostics independently of any storage engine. `tools/validate_conformance.py` executes every JSON fixture in `projector/` through the reference projector.
