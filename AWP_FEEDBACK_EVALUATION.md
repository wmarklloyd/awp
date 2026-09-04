# AWP 0.3.0 feedback evaluation

**Reviewed inputs:** Kimi, Gemini, and Claude Sonnet review files  
**Spec updated:** `AWP_SPECIFICATION_0.3.0.md`  
**Evaluation date:** 2026-09-03

## Overall assessment

The reviews independently converge on the same central weakness: AWP's semantic handoff model is strong, but the draft made the unproven coordination subsystem appear to be part of the minimum interoperability burden. They also correctly identify concrete ambiguities in event versioning, snapshot replay, Markdown synchronization, capsule framing, and schema validation.

The most useful feedback is implementer-facing and falsifiable. Praise of the broad architecture is directionally helpful but does not itself change the protocol. Suggestions that add a flag or event without resolving its trust or consistency semantics need modification before adoption.

## Decision matrix

| Recommendation | Decision | Evaluation and resulting change |
|---|---|---|
| Define a minimal or lite core | Accepted with modification | The spec now defines a required `core` profile and an optional `coordination` profile. A portable handoff includes relevant core state, not an instance of every record type. |
| Move or split coordination | Accepted in substance | Coordination is now explicitly optional and experimental, has separate conformance requirements, and does not gate core interoperability. It remains in the same draft for review coherence rather than being physically split prematurely. |
| Clarify event versioning | Accepted | Ambiguous event field `awp` was renamed `event_schema_version`; the relationship among protocol, core schema, and event-envelope versions is now explicit. |
| Add normative JSON Schema | Accepted | `schemas/awp-core-0.3.schema.json` covers manifests, event envelopes, snapshots, actors, authority declarations, and core records. A validator checks applicable JSON examples in the draft. |
| Define snapshot/event consistency | Accepted with correction | Section 29.1 now uses DAG ancestry and frontier sets. The suggested “final event IDs” algorithm would have incorrectly imposed list order and mishandled concurrent tips. |
| Detect Markdown drift | Accepted | Generated regions now have explicit markers, a normalized-byte digest, and a frontier. Human notes remain non-authoritative; semantic edits are imported only as reviewed proposed events. |
| Harden single-file delimiters | Accepted | Capsules use a per-file 128-bit boundary, line-anchored markers, collision checks, and base64 or boundary regeneration when decoded content collides. |
| Add artifact location registry | Accepted with security adjustment | Core location kinds and required fields are specified. Raw remote authorization headers were not adopted because locations must not carry secrets; they may declare retrieval requirements instead. |
| Distinguish advisory/enforced leases | Accepted | The manifest declares lease enforcement. Enforced mode requires an identified, reachable live coordinator; otherwise leases degrade to advisory. |
| Preserve references through redaction | Accepted | Physical artifact redaction retains a logical-ID tombstone while removing sensitive bytes and locations. |
| Require secret scanning | Accepted with qualification | Exporters record `passed`, `findings`, `not_run`, or `unknown`. A passing scan is evidence, not proof, and `contains_secrets: false` cannot accompany an uncertain or failed scan. |
| Add side-effect classes | Accepted | `third_party_api_call` and `data_migration` were added and included in imported-task safety rules. |
| Make resumption levels cumulative | Accepted | `operational` includes `semantic`; `exact` includes both, except for an explicitly non-portable private checkpoint. |
| Add import quarantine flag | Partially accepted | Quarantine is receiver-controlled local state. A serialized sender-controlled flag would be forgeable and therefore cannot weaken receiver policy. |
| Formalize log truncation now | Deferred | Safe compaction requires explicit lineage, canonical state, and audit rules. The draft instead forbids discarding history while claiming `full` completeness and keeps compaction as research. |
| Add normative Git binding | Deferred | A required branch/PR mapping would bind the core to one forge workflow and would not solve semantic compatibility. Git adapters remain Phase 2 work. |
| Relate AWP to CRDT/provenance work | Accepted | Appendix B now distinguishes conceptual overlap from claims AWP does not make, including automatic CRDT convergence. |
| Split out the design rationale for length | Not adopted | The preamble is a small fraction of the document and provides useful context for an exploratory draft. It can move when the protocol stabilizes, but length is not currently the main adoption risk. |
| Group open questions by impact | Accepted | Questions are grouped into core-experiment blockers, 1.0 blockers, and deferrable/profile-specific research. |
| Define an empirical handoff test | Accepted | Appendix E specifies isolation, receiver count, task ingredients, scoring dimensions, and a minimum continuation-success condition. |

## Important non-changes

The update does not claim distributed lease safety, automatic semantic-merge correctness, canonical signature bytes, or lossless history compaction. Those are still research or later-profile work. It also does not treat an imported workstate, signature, lease, or quarantine assertion as execution authority.

## Verification

Run:

```powershell
python tools\validate_spec_examples.py
```

The validator checks the JSON Schema itself and every applicable JSON example in the draft. Cross-record properties such as event ancestry, authority, briefing synchronization, and normalized path safety remain prose invariants and require conformance fixtures in a later implementation phase.
