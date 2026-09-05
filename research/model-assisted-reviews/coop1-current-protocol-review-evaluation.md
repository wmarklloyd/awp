# Evaluation of the COOP-1 current-protocol bilateral review

**Date:** 2026-09-05  
**Reviewed response:** `consultations/coop1-current-protocol-review-response.awp.md`  
**Disposition:** useful accepted specification review; partial interaction evidence; not exit-conformance evidence

Claude's response is structurally sound: its generated-section digest matches, its Cooperation interaction validates against `awp-cooperation-0.1.schema.json`, and it records a bounded terminal outcome. The shared runtime ledger confirms that `actor:claude-review` reached the same repository-intrinsic project identifier and persistent store identifier from a different execution path. This is useful evidence for cross-path binding discovery and a bounded cross-model critique.

The exercise also exposed two defects that the response itself did not identify.

First, the draft incorrectly treated `frontier` and operational reach as fields whose values had to match inside a stable binding identity. The ledger necessarily advanced between the requester's and responder's status observations, so exact frontier equality was neither demonstrated nor desirable. Stable identity is now limited to workstate, project, store, scope-model, and binding-epoch fields. Reach and frontier are separately timestamped observations; participants reconcile advancing frontiers and block only on an unverifiable history gap.

Second, the response says the lease was released before the response capsule was published. The ledger confirms `intent.completed` at `2026-09-05T18:19:06.524674Z` and `lease.released` at `2026-09-05T18:19:06.824518Z`, while the response declares `generated_at: 2026-09-05T18:22:00Z` and was written later. An output identifier naming a not-yet-existing artifact is not publication confirmation. This ordering violates Cooperation Contracts Section 4.4 and means the exchange does not demonstrate conforming exit or fresh-handoff behavior.

The response capsule is preserved unchanged as authored evidence. The draft now requires release rejection while a linked intent is nonterminal or when no durable receipt identifies an already published handoff artifact and digest. The local adapter now verifies the handoff path and records its SHA-256 digest before accepting lease release.

Accordingly, this review may support the bounded-interaction and cross-path shared-store scenarios within its stated limits. It must not be cited as evidence that canonical checkpoint projection or recoverable COOP-1 exit is complete.
