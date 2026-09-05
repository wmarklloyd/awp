# Conformance evidence matrix

This matrix distinguishes specified roles from evidence currently present in the repository. “Structural” means JSON Schema validation only; it does not establish cross-record semantics.

| Role or capability | Normative source | Structural fixtures | Procedural fixtures | Independent implementations | Current evidence |
|---|---|---:|---:|---:|---|
| Core reader | Core 0.6 / draft 0.7 | Embedded examples; consultation fixtures | None | 0 | Specification validation only |
| Capsule reader | Capsule 0.3 / draft 0.4 | Metadata and briefing digest examples | None | 0 | Representation examples only |
| Repository discovery 0.1 | Capsule 0.3 | Embedded examples | None | 0 | Released schema validation |
| Historical Repository discovery 0.2 | Former Capsule 0.4 draft | 4 positive/negative cases | Path-policy expectations | 0 | Retained compatibility fixture; not required by the single-file working draft |
| Handoff reader/writer | Handoff 0.3 / draft 0.4 | Embedded examples | Proposed experiment | 0 | No interoperability claim |
| COOP-0 portable collaboration | Cooperation Contracts 0.1 draft | Binding and interaction schema fixtures | Consultation and capsule round trips | 0 | Portable substantive collaboration is specified; no active-coordination guarantee |
| COOP-1 default small-group contract | Cooperation Contracts 0.1 and Coordination 0.5 drafts | Binding, interaction, participant-lease, and Coordination record fixtures | Shared-binding guarded-work trial, bounded cross-model review, projector fixtures, ledger and workstate component tests | 0 | Experimental composed contract only; deterministic projection, guarded work, bounded interaction, checkpoint, recovery, and fresh-entry evidence are not yet demonstrated together by one binding |
| Deterministic Coordination projector capability | Coordination draft 0.5, Sections 4, 15, and 17 | Coordination event schema coverage | 4 transport-neutral fixtures plus 10 transport-order, ancestry, revision, lifecycle, cross-record, verification-binding, contest, and mismatch tests | 0 | Reusable component and expected projection outcomes; complete COOP-1 transition fixtures and independent implementation remain outstanding |
| Simpler model participation adapter | Experimental participation contract 0.1 | 3 request/response/receipt examples | 14 local read/announce/publish/interact/checkpoint, idempotency, overlap, scope, freshness, and contract-validation tests | 0 | Continue-checkpoint slice only; exit checkpointing, host authority, and complete COOP-1 composition remain outstanding |
| Presence monitoring | Coordination draft 0.5 | Presence valid/invalid records | 8 local registry lifecycle tests | 0 | One advisory SQLite reference component; no COOP-2 protected enforcement, cross-host, semantic-overlap, or effectiveness claim |
| Security guardrails | Security draft 0.4 | Guardrail valid/invalid fixtures | None | 0 | Structural schema checks only; receiver enforcement is not claimed |
| COOP-2 aware, enforced, scalable contract | Cooperation Contracts 0.1 and Coordination 0.5 drafts | COOP-2 binding example and partial Coordination schema coverage | Synthetic semantic cases only | 0 | Specification concept; no semantic analyzer, protected enforcing adapter, distributed fault evidence, or complete implementation |
| Bundle reproducibility | Build tools | N/A | Byte equality tests | 1 tool | Automated repository test |

The next evidence milestone is a complete COOP-1 event-transition fixture set with expected frontiers, materialized records, and diagnostics, followed by two independently implemented projectors and one end-to-end binding trial. This evidence is required before a complete COOP-1 conformance claim; it is not a prerequisite for an agent/model to follow the workflow when its binding already provides the required semantics and discloses its limitations.
