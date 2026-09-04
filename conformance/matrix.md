# Conformance evidence matrix

This matrix distinguishes specified roles from evidence currently present in the repository. “Structural” means JSON Schema validation only; it does not establish cross-record semantics.

| Role or capability | Normative source | Structural fixtures | Procedural fixtures | Independent implementations | Current evidence |
|---|---|---:|---:|---:|---|
| Core reader | Core 0.6 / draft 0.7 | Embedded examples | None | 0 | Specification validation only |
| Capsule reader | Capsule 0.3 / draft 0.4 | Briefing digest examples | None | 0 | Representation examples only |
| Repository discovery 0.1 | Capsule 0.3 | Embedded examples | None | 0 | Released schema validation |
| Repository discovery 0.2 | Capsule 0.4 draft | 4 positive/negative cases | Path-policy expectations | 0 | Draft fixture validation |
| Handoff reader/writer | Handoff 0.3 / draft 0.4 | Embedded examples | Proposed experiment | 0 | No interoperability claim |
| Coordination C0/C1 | Coordination 0.3 / draft 0.4 | 3 valid and 2 invalid draft records plus embedded examples | Synthetic awareness pilot | 0 | Structural and instrumentation checks only |
| Coordination C2 | Coordination draft 0.4 | Partial schema coverage | Synthetic semantic cases | 0 | No analyzer evidence |
| Coordination C3 | Coordination draft 0.4 | Partial schema coverage | None | 0 | Specification concept only |
| Bundle reproducibility | Build tools | N/A | Byte equality tests | 1 tool | Automated repository test |

The next evidence milestone is a complete event-transition fixture set with expected frontiers, materialized records, and diagnostics, followed by two independently implemented projectors.
