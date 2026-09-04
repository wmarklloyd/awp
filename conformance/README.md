# Conformance assets

This directory contains machine-readable examples with explicit expected outcomes. It separates executable evidence from examples embedded in explanatory prose.

- `valid/` contains documents that must validate under the named schema.
- `invalid/` contains documents that must fail for the stated reason.
- `expected-diagnostics/` records stable expected validation outcomes.
- `interoperability/` reserves results from independent implementations.

Passing structural fixtures is necessary but not sufficient for protocol conformance. Cross-record, event-graph, authority, and projection invariants require procedural fixtures and independently implemented processors.
