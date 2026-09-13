# AWP Action Boundary 0.1.0

**Status:** Experimental working-draft profile specification
**Module ID:** `urn:awp:action-boundary`
**Direct dependencies:** Core; Handoff, for the `decision_context` axis this module gates on; Security, for permit binding and signing

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Decision Durability (index.md §Purpose) makes an accepted decision discoverable and applicable. It does not, by itself, stop a participant from proceeding when that decision context could not be established. In an observed incident, a participant received a correctly reported `budget_exceeded` structural-selection result and an absent `decision_context` result from a Handoff-conformant re-entry projection, and performed guarded work anyway: it generated and committed public product imagery depicting an interface that did not exist in the product. The projection was honest; nothing independent of the participant's own judgment stood between that honest incomplete result and the mutation it should have blocked. A second, separate failure compounded it: the durable rule the work violated existed only in prose and Git history, never promoted into the capsule as a structured, scope-`affects`-bound decision, so even a diligent resolver could not have found it mechanically. This module addresses the first failure. Record-authoring diagnostics for the second are noted in §8.

This module turns Decision Durability from a context-presentation obligation into a verifiable precondition for a declared class of consequential actions. It does not claim that AWP replaces runtime authorization, sandboxing, or an organization's own policy enforcement, and it does not claim that a well-formed resolution proves the resulting artifact is true, safe, or correct — only that the applicable decisions were resolved and bound to the exact action before it proceeded. A deployment that records these structures without gating a real mutation path MUST NOT claim the `action-enforced` or `output-attested` levels defined in §9; §1 of the Adapter Framework already establishes that a portable guardrail is policy state, not proof of enforcement, and this module inherits that distinction rather than replacing it.

This module is informed by, but not limited to, the incident summarized above. Its source analysis is preserved for traceability in `research/model-assisted-reviews/`.

## 2. Terms

An **action intent** is a participant- or host-authored description of a contemplated operation, sufficient to compute which decisions apply to it. It describes semantic effect, not only a file path: a target path alone does not disclose that an operation makes a public claim about an existing product interface.

An **applicable decision set** is the resolver's output for one action intent: the effective decisions selected against it, both completeness axes, any conflicts or unknowns, and a permit-or-deny-or-unresolved result.

An **action permit** is a short-lived, digest-bound record asserting that a specific action intent was resolved against a specific capsule state and produced a permit result. It authorizes nothing by itself; an enforcement adapter is what a protected operation actually depends on.

An **artifact claim record** binds an externally visible artifact's stated claims (for example, "this image depicts an existing product interface") to the evidence that supports each claim.

An **enforcement adapter** is a component outside the participant's own control — a tool gateway, source-control hook, CI rule, deployment or publication service — that independently checks a permit and required evidence before a protected operation is allowed to take effect.

## 3. Action intent

Before performing a governed action, a participant MUST describe the contemplated operation, semantic artifact kinds, affected scopes, external claims, inputs, and targets in an action intent sufficient to compute applicable decision closure. Reading, validating, acknowledging, or summarizing a workstate MUST NOT by itself satisfy action-boundary decision resolution; resolution is computed per action intent, not once at session entry.

```json
{
  "id": "action:play-baseball-feature-graphic",
  "operation": "create",
  "artifact_kinds": ["public-promotional-watch-imagery"],
  "scopes": ["repo:android_sports_watches", "google-play:baseball"],
  "external_claims": ["depicted-watch-interface-exists"],
  "tools": ["image-generation"],
  "inputs": [],
  "targets": ["play-store-assets/baseball"],
  "intent_digest": "sha256:..."
}
```

## 4. Applicable-decision resolution

A resolver MUST report structural selection and `decision_context` as independent axes, matching Handoff's existing two-axis requirement (handoff.md §Bounded re-entry projection). Absence of either result MUST NOT be interpreted as complete. A participant MUST NOT infer that no applicable decision exists merely because a bounded presentation omitted a decision, decision source, required artifact, or entry record — an empty selection is evidence of a budget limit, not evidence of an empty decision set.

```json
{
  "action_intent": "action:play-baseball-feature-graphic",
  "intent_digest": "sha256:...",
  "capsule_digest": "sha256:...",
  "selection": "complete",
  "decision_context": "complete",
  "applicable_decisions": ["decision:public-watch-imagery-uses-literal-product-surfaces"],
  "requirements": ["depicted screen pixels must derive from a verified product capture"],
  "result": "permit"
}
```

When the capsule projection is `budget_exceeded`, when independent `decision_context` is absent, or when semantic applicability is unknown, the result MUST be `unresolved`, never `permit`. Delegated, tool-mediated, decomposed, retried, and derived operations MUST inherit every mandatory decision and guardrail applicable to the originating action intent; a child image-generation call under a permitted parent task does not re-resolve scope independently of that parent.

## 5. Action permit

For an operation that local policy protects, a resolution with result `permit` MAY be represented as a short-lived action permit, bound to: the action-intent digest; the capsule digest and frontier it was resolved against; the selected decision IDs and revisions; exact input artifact digests; the allowed operation and target scope; required postconditions; issuer and enforcement profile; and expiry and invalidation conditions.

A permit MUST be bound to the action-intent digest, governing workstate and frontier, applicable decision revisions, permitted operation, and target scope. Material intent or context drift — the prompt, inputs, operation, target, applicable decision revisions, or capsule frontier changing after issuance — MUST invalidate the permit. A broad permit such as "create marketing assets" MUST NOT authorize a narrower action whose newly introduced claim was not described in the intent that produced it.

## 6. Artifact claim record

When an externally visible artifact makes a product, provenance, safety, or compliance claim, an enforcing profile MAY require an artifact claim record before publication.

```json
{
  "artifact": "play-store-assets/baseball/feature-graphic.png",
  "claims": [
    {
      "claim": "depicted-watch-interface-exists",
      "evidence": {
        "source_artifact": "website/assets/baseball-live.svg",
        "source_digest": "sha256:...",
        "transformation": "literal-composite"
      },
      "status": "verified"
    }
  ]
}
```

If required evidence is absent or unverifiable, publication MUST remain blocked unless an authorized owner records a bounded continuation identifying the accepted risk, exact scope, and expiry — the same decision-owner escape hatch Handoff already defines for incomplete decision context, not a new authority path.

## 7. Enforcement adapter

AWP continues to distinguish policy records from enforcement (adapters.md §1). This module becomes preventative only when a host, tool gateway, source-control hook, CI rule, deployment adapter, or publication service requires the bound resolution described above. An enforcement adapter MUST independently verify: the permit and action-intent digests; the current capsule/frontier binding; the target and operation scope; required evidence records; expiry and revocation; and the absence of unresolved diagnostics. A deployment claiming enforced action-boundary conformance MUST use an enforcement point independent of the participant's unsupported assertion; the enforcement point MUST reject a missing, invalid, stale, mismatched, or unresolved permit. The participant's own statement that it complied is evidence, not enforcement.

## 8. Diagnostics

| Code | Meaning |
|---|---|
| `AWP-ACTION-INTENT-REQUIRED` | A governed action lacks a sufficient contemplated-work description. |
| `AWP-ACTION-DECISION-RESOLUTION-REQUIRED` | Applicable decision closure was not computed for the action. |
| `AWP-ACTION-DECISION-CONTEXT-INCOMPLETE` | Selection or decision context cannot justify the action. |
| `AWP-ACTION-PERMIT-MISSING` | An enforcing adapter received no permit. |
| `AWP-ACTION-PERMIT-MISMATCH` | The permit does not match the operation, inputs, target, or current context. |
| `AWP-ACTION-INTENT-DRIFT` | The action changed materially after resolution. |
| `AWP-ARTIFACT-CLAIM-UNVERIFIED` | An externally visible claim lacks required evidence. |

These diagnostics preserve the existing `AWP-DECISION-CONTEXT-INCOMPLETE` semantics from Handoff rather than creating an alternate decision model; the action-specific codes identify where that existing decision failure reached an operational boundary.

A projector SHOULD disclose when a frequently referenced requirement in an authoritative artifact has no corresponding effective decision, so an owner can promote it explicitly — for example: "the authoritative artifact contains a relied-upon product-imagery rule, but no effective decision or required constraint declares applicability to public promotional assets." A projector MUST NOT autonomously convert arbitrary prose into a binding decision.

## 9. Conformance claims

| Claim | Required evidence |
|---|---|
| `context-aware` | The authoritative workstate was discovered and validated. |
| `decision-resolved` | A task/action-scoped applicable decision set was computed with both completeness axes. |
| `action-bound` | The resolution is content-digest bound to the exact contemplated action. |
| `action-enforced` | An independent adapter rejects protected operations without a valid bound permit. |
| `output-attested` | Required externally visible claims are mapped to verified evidence and checked at publication. |

A host MUST NOT claim a stronger level merely because a participant produced a well-formed record. `context-aware` alone describes correct entry behavior; it does not justify an `action-enforced` claim.

## 10. Limits and non-goals

Semantic applicability is not made infallible by this module. A participant or host can misdescribe an action, a projector can fail to promote an important rule, and a poorly configured policy can classify consequential work as unguarded. Accordingly:

- Protected action classes MUST be declared by receiver or project policy; this module does not define a default protected set.
- Ambiguous applicability MUST produce `unknown` and fail closed for a protected operation.
- Enforcement MUST occur outside the model's own unsupported assertion.
- A bounded owner override MUST be exact, expiring, and auditable.
- This module MUST NOT be represented as proof that a record's subject matter is true, safe, or correct — only that applicable decisions were resolved and bound before the action proceeded.

A deployment MAY remain advisory and honestly claim only `context-aware` or `decision-resolved` behavior. A permit becomes mandatory only when the deployment claims prevention or enforcement for a declared protected action class.

## 11. Open questions

Design questions not yet resolved by this draft are tracked in [open-issues.md](open-issues.md).
