# Conformance evidence matrix

This matrix distinguishes specified roles from evidence currently present in the repository. “Structural” means JSON Schema validation only; it does not establish cross-record semantics.

| Role or capability | Normative source | Structural fixtures | Procedural fixtures | Independent implementations | Current evidence |
|---|---|---:|---:|---:|---|
| Core reader | Core 0.6 / draft 0.7 | Embedded examples; consultation fixtures | None | 0 | Specification validation only |
| Capsule reader | Capsule 0.3 / draft 0.4 | Metadata and briefing digest examples | None | 0 | Representation examples only |
| Repository discovery 0.1 | Capsule 0.3 | Embedded examples | None | 0 | Released schema validation |
| Historical Repository discovery 0.2 | Former Capsule 0.4 draft | 4 positive/negative cases | Path-policy expectations | 0 | Retained compatibility fixture; not required by the single-file working draft |
| Handoff reader/writer | Handoff 0.3 / draft 0.4 | Embedded examples | Proposed experiment | 0 | No interoperability claim |
| Coordination C0/C1 and default ledger workflow | Coordination 0.3 / draft 0.4 | 6 valid and 4 invalid draft records plus embedded examples | Synthetic awareness pilot; 7 local ledger lifecycle, schema, policy, cursor, and concurrency tests | 0 | Protocol default and host/model binding are specified; the local adapter is optional reference evidence and is not a complete C1 projector |
| C1 deterministic projector foundation | Coordination draft 0.4, Sections 4, 15, and 17 | Coordination event schema coverage | 4 transport-neutral fixtures plus 10 transport-order, ancestry, revision, lifecycle, cross-record, verification-binding, contest, and mismatch tests | 0 | Reusable projector foundation and expected projection outcomes; complete transition fixtures and independent implementation remain outstanding |
| Simpler model participation adapter | Experimental participation contract 0.1 | 3 request/response/receipt examples | 10 local read/announce/publish/interact, idempotency, overlap, scope, and request-validation tests | 0 | Read/announce/publish/interact slice only; checkpoint, host authority, and complete C1 composition remain outstanding |
| Presence monitoring | Coordination draft 0.4 | Presence valid/invalid records | 8 local registry lifecycle tests | 0 | One advisory SQLite reference tool; no C3, cross-host, semantic-overlap, or effectiveness claim |
| Security guardrails | Security draft 0.4 | Guardrail valid/invalid fixtures | None | 0 | Structural schema checks only; receiver enforcement is not claimed |
| Coordination C2 | Coordination draft 0.4 | Partial schema coverage | Synthetic semantic cases | 0 | No analyzer evidence |
| Coordination C3 | Coordination draft 0.4 | Partial schema coverage | None | 0 | Specification concept only |
| Bundle reproducibility | Build tools | N/A | Byte equality tests | 1 tool | Automated repository test |

The next evidence milestone is a complete event-transition fixture set with expected frontiers, materialized records, and diagnostics, followed by two independently implemented projectors. This evidence is required before the Coordination module is promoted from experimental status; it is not a prerequisite for an agent/model to follow the C1 workflow when its binding already provides the required semantics.
