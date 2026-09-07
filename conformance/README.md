# Conformance assets

This directory contains machine-readable examples with explicit expected outcomes. It separates executable evidence from examples embedded in explanatory prose.

- `valid/` contains documents that must validate under the named schema.
- `invalid/` contains documents that must fail for the stated reason.
- `expected-diagnostics/` records stable expected validation outcomes.
- `projector/` contains transport-neutral deterministic Coordination event histories with expected frontiers, materialized records, contested conditions, and diagnostic signatures.
- `valid/participation-0.1-*.json` and its expectation manifest contain structural examples for the experimental model participation request, response, and publication receipt contract.
- `interoperability/` reserves results from independent implementations.

Passing structural fixtures is necessary but not sufficient for protocol conformance. Cross-record, event-graph, authority, and projection invariants require procedural fixtures and independently implemented processors.

The default ledger workflow is part of the COOP-1 work contract for an AWP-aware agent/model and its host binding; it does not require the optional consultation subprotocol. A model may emit records or requested operations without directly persisting them. SQLite and `tools/awp_coordination.py` are optional reference aids; deterministic projector fixtures remain transport-neutral and record the expected frontier, materialized state, and diagnostics independently of any storage engine. `tools/validate_conformance.py` executes every JSON fixture in `projector/` through the reference projector.
