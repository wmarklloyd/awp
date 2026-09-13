# AWP Action Boundary 0.3.1

**Status:** Experimental working-draft profile specification
**Module ID:** `urn:awp:action-boundary`
**Direct dependencies:** Core; Handoff, for the `decision_context` axis this module gates on; Security `0.5.x`, for the guardrail mechanism this module extends

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Decision Durability (index.md §Purpose) makes an accepted decision discoverable and applicable. It does not, by itself, stop a participant from proceeding when that decision context could not be established. In an observed incident, a participant received a correctly reported `budget_exceeded` structural-selection result and an absent `decision_context` result from a Handoff-conformant re-entry projection, and performed guarded work anyway: it generated and committed public product imagery depicting an interface that did not exist in the product.

Two earlier revisions of this module (0.1.0, 0.2.0) built a resolver-and-permit design with its own policy record, operation vocabulary, and named "policy author" role. Reviewing that design against the rest of the family found it substantially duplicated an existing mechanism: Security 0.5's **shared guardrail** (security.md §4) already provides a portable, structured, actor-subordinate policy record with `operation_classes`, `resources`, a `policy_owner`, `enforcement` levels including `protected_adapter`, and mandatory `propagation` to delegated and derived operations — everything 0.2.0 had reinvented under different names. This revision (0.3.0) removes that duplication: action-boundary no longer defines its own policy record. A protected action class is declared as a Security guardrail, exactly as security.md §4 already specifies. This module adds only what guardrails do not already provide:

1. binding a guardrail evaluation to Handoff's two-axis `decision_context` completeness check, so an action is never permitted on an incomplete or unverified projection (§4);
2. a reserved operation-class convention and normative rule constraining *how* a protected artifact class may be produced, not just whether an operation is allowed (§5) — the module's primary defense, addressing the incident directly;
3. an artifact claim record binding an externally visible claim to mechanically produced evidence (§6);
4. an action-resolution record that digest-binds one concrete action, at one specific capsule state, to the combined guardrail-and-decision result (§4).

It is informed by, but not limited to, the original incident, a critical review that produced 0.2.0, and the duplication finding that produced 0.3.0. All three are preserved for traceability in `research/model-assisted-reviews/`.

This module does not claim that AWP replaces runtime authorization, sandboxing, or an organization's own policy enforcement, and it does not claim that a well-formed resolution proves the resulting artifact is true, safe, or correct — only that a declared action was checked against applicable guardrails and decisions, by a component the acting participant does not control, before it took effect. A deployment that records these structures without gating a real mutation path MUST NOT claim the `action-enforced` or `output-attested` levels defined in §10; security.md §4 already establishes that a portable guardrail is shared policy state, not proof of enforcement, and this module inherits that distinction rather than replacing it.

This module explicitly does **not** solve decision capture — getting a durable rule out of prose and Git history and into a structured, `affects`-scoped decision or guardrail in the first place. That remains a projector- and policy-owner-authoring problem (§8, and open-issues.md). A resolver operating over an incomplete decision or guardrail set will resolve incorrectly no matter how well the rest of this module works; this module assumes decision capture as a precondition, not a feature it provides.

A patch revision (0.3.1) corrected a defect in 0.3.0 itself, found by an independent review of a related proposal: the first-pass resolver matched a decision against a contemplated action by reading Core's `affects` field as if it were a glob-matchable selector, and aggregated an unqualified top-level `requirements` field that Core does not define on decisions at all. Both are exactly the violation core.md already warns against — "Optional modules MAY extend applicability, but they MUST NOT replace or reinterpret the Core `affects` and `supersedes` fields" — and core.md's own remedy: "An optional module extending a Core record places its fields under `modules.{module-id}`." §3.1 and the resolver now read a decision's action-boundary selectors and requirements from `modules."urn:awp:action-boundary"` instead; Core's `affects` is untouched and unread by this module. No other part of the 0.3.0 design changed.

## 2. Terms

An **action** is one contemplated operation a participant is about to perform, described by an operation class (from security.md §4's `operation_classes` vocabulary, extended by §3 below for protected artifact production), a target resource, and, when it produces or publishes an artifact, an artifact class.

An **applicable guardrail** is a Security guardrail (security.md §4) whose `operation_classes` and `resources` match an action, evaluated by the receiver's existing guardrail-evaluation rule (security.md §4, fourth paragraph). This module does not change how guardrails are declared, owned, or evaluated; it changes what happens after that evaluation.

An **action resolution** is one record produced per contemplated action: it names the action; carries both Handoff completeness axes evaluated for that specific action; lists the applicable guardrails and applicable plain decisions; and states a result of `permit`, `deny`, or `unresolved`.

An **enforcement adapter** is a component outside the participant's own control — most concretely a CI gate on a protected branch, or a tool gateway that intercepts a specific tool call — that independently recomputes or verifies an action resolution before a protected operation is allowed to take effect.

An **artifact claim record** binds an externally visible artifact's stated claims to the evidence that supports each claim. For an artifact class governed by a `generative:freeform`-denying guardrail (§5), this module requires the record to be a mechanical byproduct of a constrained transformation pipeline, not a participant's self-report.

## 3. Declaring a protected artifact class

A project declares a protected artifact class exactly as security.md §4 already specifies: as a Security guardrail extending a Core `constraint` record, with `policy_owner` naming the accountable human and `resources` naming the artifact class (for example `artifact-class:public-promotional-watch-imagery`). This module adds no new declaration format.

This module reserves two `operation_classes` values for generative production of a resource:

- `generative:freeform` — the operation may produce content not traceable to any specific named source (for example, an image-generation call with no required input references).
- `generative:composite` — the operation is restricted to composing named, verifiable source artifacts; every output element is traceable to a source.

A guardrail with `effect: deny` and `operation_classes: ["generative:freeform"]` against a protected resource is how a project expresses "this artifact class MUST NOT be produced by an untraceable method" — the normative content of §5. A project MAY declare narrower or additional operation classes; `generative:freeform` and `generative:composite` are reserved so that this module's resolver and enforcement adapters have a portable convention to check without needing project-specific configuration for the tool-constraint rule in §5.

For a guardrail governing a protected artifact class under this module, `policy_owner` MUST NOT equal the actor whose action is being resolved. This is a stricter requirement than security.md §4 states in general (which allows any accepted `policy_owner`); it exists because the actor being gated authoring the rule that gates it defeats the guardrail's purpose for this module's specific use. A resolver encountering such a guardrail MUST treat it as `unresolved`, not as satisfied or absent.

### 3.1 Selector matching against future targets

A guardrail's `resources` MUST be matchable by artifact class and scope-matching selector (for example a path glob or a platform/listing identifier pattern), not only by a path that already exists. A guardrail authored before a target exists (before a new product listing directory is created, for instance) MUST still match that target once it exists, provided the target falls within the declared selector. Security 0.5 does not otherwise constrain how `resources` is matched, so this is this module's own resolver convention, not a reinterpretation of a Security-owned field.

A decision's applicability to a contemplated action is a different question from Core's `affects` field, and this module MUST NOT answer it by reading `affects` as a selector. Core defines `affects` as "an array of record or artifact references defining explicit Core-level applicability" for Core's own decision-closure algorithm (core.md §Records) — a reference to something, not a glob pattern matched against something that may not exist yet. A decision that a policy owner wants this module's resolver to match against a future or wildcarded action target instead carries that selector under this module's own extension namespace, per core.md's rule that "an optional module extending a Core record places its fields under `modules.{module-id}`":

```json
{
  "id": "decision:public-watch-imagery-uses-literal-product-surfaces",
  "type": "decision",
  "status": "accepted",
  "choice": "Public product imagery MUST depict only real, source-matched watch displays.",
  "affects": ["artifact:play-store-assets/baseball/feature-graphic.png"],
  "modules": {
    "urn:awp:action-boundary": {
      "selectors": ["artifact-class:public-promotional-*-imagery"],
      "requirements": ["depicted screen pixels must derive from a verified product capture"]
    }
  }
}
```

A resolver MUST match a decision against a contemplated action only via the `selectors` array under `modules."urn:awp:action-boundary"`, never via `affects`. A decision that omits this module's extension simply does not participate in this module's action resolution — that silence is not evidence the decision doesn't apply elsewhere; it may still be part of Core's own decision closure, computed independently, for other purposes. `requirements` surfaced in an action-resolution record (§4) are aggregated the same way, from each matched decision's `modules."urn:awp:action-boundary".requirements` — Core does not define a top-level `requirements` field on decisions, and this module MUST NOT add one informally outside its own namespace.

## 4. Action resolution

A resolver MUST report structural selection and `decision_context` as independent axes for the specific action being resolved, matching Handoff's existing two-axis requirement (handoff.md §Bounded re-entry projection) rather than reusing a stale session-entry result. Absence of either result MUST NOT be interpreted as complete. A participant MUST NOT infer that no applicable guardrail or decision exists merely because a bounded presentation omitted one — an empty selection is evidence of a budget limit, not evidence of an empty policy set.

```json
{
  "action": {
    "operation_class": "generative:freeform",
    "resource": "google-play:baseball",
    "artifact_class": "public-promotional-watch-imagery"
  },
  "action_digest": "sha256:...",
  "capsule_digest": "sha256:...",
  "selection": "complete",
  "decision_context": "complete",
  "applicable_guardrails": ["constraint:no-invented-product-imagery"],
  "applicable_decisions": ["decision:public-watch-imagery-uses-literal-product-surfaces"],
  "result": "deny"
}
```

(This example denies `generative:freeform` against a protected class per §5; the operation class that would resolve `permit` for this target is `generative:composite`, subject to the applicable decisions' other requirements.)

When the capsule projection is `budget_exceeded`, when independent `decision_context` is absent, when an applicable guardrail's `policy_owner` fails the §3 distinctness check, or when class or scope applicability is unknown, the result MUST be `unresolved`, never `permit`. Among applicable guardrails and decisions, security.md §4's existing precedence applies: a deny is more restrictive than a requirement, and a requirement is more restrictive than no control. Delegated, tool-mediated, decomposed, retried, and derived operations MUST inherit every mandatory guardrail and decision applicable to the originating action — this is the same propagation security.md §4 already requires (`propagation: mandatory`); this module does not weaken or duplicate it.

A resolution's `result: permit` MAY carry binding fields — expiry, the exact input artifact digests it was granted against — directly on the resolution record. A standalone, transportable permit object, separate from the resolution that produced it, is NOT part of this module's core design; it is an extension point for a deployment whose resolution and enforcement are genuinely on different hosts or asynchronous in time (relevant to AWP's own multi-host Cooperation Contracts layer, but not required for a single-repository deployment) and is deferred to open-issues.md rather than specified here.

## 5. Protected-kind tool constraint

For an artifact class governed by a guardrail denying `generative:freeform` (§3), an enforcement adapter MUST NOT permit invocation of a freeform-generation operation. It MUST restrict invocation to a `generative:composite` (or otherwise traceable) operation whose inputs are named, verifiable source artifacts. This is the module's primary defense, not a fallback: verifying a freely generated artifact's truthfulness after the fact is a strictly harder problem than preventing the untraceable artifact from being producible at all. A generation tool that has no composite or traceable mode for a protected class MUST NOT be invocable for that class under an enforcing profile; that is a tooling gap to close, not a policy exception to grant.

This directly determines what an artifact claim record can honestly contain (§6): a `generative:composite` operation's claim record is a byproduct of the transformation, and a `generative:freeform` operation's claim record cannot be produced honestly at all for a class the guardrail denies it for.

## 6. Artifact claim record

When an externally visible artifact makes a product, provenance, safety, or compliance claim, an enforcing profile MAY require an artifact claim record before publication. For an artifact class governed by a §5 guardrail, the record MUST be emitted by the transformation pipeline itself as a byproduct of a `generative:composite` or otherwise traceable operation, not authored or asserted by the participant.

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

AWP continues to distinguish policy records from enforcement (security.md §4). This module becomes preventative only when an enforcement point independently recomputes or verifies the action resolution before a protected operation takes effect — the same distinction security.md §4 already draws between a guardrail's `enforcement` value and an actual host or protected adapter enforcing it.

A client-side commit hook is NOT an adequate enforcement point on its own: it is trivially bypassed (`git commit --no-verify`) and does not run on a party the participant doesn't control. The reference enforcement pattern for a single-repository deployment is a CI gate that runs on the target branch, recomputes the action resolution independently rather than trusting a submitted one, and blocks the merge unless the result is `permit` — enforceable to the extent the repository's branch protection actually prevents a direct push around it. A stronger, complementary pattern is a tool gateway that intercepts the specific tool call (for example the image-generation invocation itself) and verifies the requested operation class against §5 before the call is allowed to execute; this is stronger than a CI gate because it constrains what can be *produced*, not only what can be *merged*.

An enforcement adapter MUST independently verify: the action and capsule digest binding; the target and operation-class scope; required evidence records; expiry; and the absence of unresolved diagnostics. A deployment claiming enforced action-boundary conformance MUST use an enforcement point independent of the participant's unsupported assertion, and MUST document what its enforcement point does and does not prevent a determined participant from bypassing (§11). The participant's own statement that it complied is evidence, not enforcement.

## 8. Decision capture

The resolver in §4 can only find a guardrail or decision that already exists as structured, matchable state. This module does not, by itself, get a rule out of prose and history and into that state — that remains the policy owner's responsibility, assisted by projector diagnostics. A projector SHOULD disclose when a frequently referenced requirement in an authoritative artifact has no corresponding effective decision or guardrail, so the policy owner can promote it explicitly — for example: "the authoritative artifact contains a relied-upon product-imagery rule, but no effective decision or guardrail declares applicability to public promotional assets." A projector MUST NOT autonomously convert arbitrary prose into a binding decision or guardrail; only the policy owner does that.

## 9. Diagnostics

| Code | Meaning |
|---|---|
| `AWP-ACTION-DECISION-RESOLUTION-REQUIRED` | Applicable guardrail/decision closure was not computed for the action. |
| `AWP-ACTION-DECISION-CONTEXT-INCOMPLETE` | Selection or decision context cannot justify the action. |
| `AWP-ACTION-RESOLUTION-MISSING` | An enforcing adapter received or independently computed no resolution. |
| `AWP-ACTION-RESOLUTION-MISMATCH` | The resolution does not match the operation class, resource, or current context. |
| `AWP-ACTION-GATEWAY-MISMATCH` | A tool gateway's intercepted call does not match the resolved operation class. |
| `AWP-ARTIFACT-CLAIM-UNVERIFIED` | An externally visible claim lacks required evidence, or was not produced mechanically for a §5-governed class. |
| `AWP-ACTION-GUARDRAIL-OWNER-INVALID` | An applicable guardrail's `policy_owner` equals the actor whose action is being resolved (§3). |

These diagnostics preserve the existing `AWP-DECISION-CONTEXT-INCOMPLETE` semantics from Handoff rather than creating an alternate decision model; the action-specific codes identify where that existing decision failure reached an operational boundary.

## 10. Conformance claims

| Claim | Required evidence |
|---|---|
| `context-aware` | The authoritative workstate was discovered and validated. |
| `decision-resolved` | An action-scoped resolution was computed with both completeness axes, against applicable guardrails and decisions. |
| `action-bound` | The resolution is content-digest bound to the exact action and capsule state. |
| `action-enforced` | An independent adapter recomputes or verifies the resolution and rejects a protected operation without a matching `permit` result — corresponding to an applicable guardrail's `enforcement: protected_adapter` (security.md §4) actually being backed by one. |
| `output-attested` | Artifact classes governed by a §5 guardrail are produced only via `generative:composite` (or otherwise traceable) operations, with a mechanically emitted claim record checked at publication. |

A host MUST NOT claim a stronger level merely because a participant produced a well-formed record. `context-aware` alone describes correct entry behavior; it does not justify an `action-enforced` claim. `action-enforced` alone does not justify `output-attested` unless the tool constraint in §5 is actually in place — an adapter can faithfully enforce a resolution and still gate a freeform-generation tool whose output cannot honestly carry a claim record.

## 11. Limits and non-goals

- This module does not solve decision capture (§8); it assumes structured guardrails and decisions exist and degrades to `unresolved` when they don't, which is a correct but not sufficient response — the missing rule is still missing.
- No enforcement point is unconditionally bypass-proof. A CI gate depends on branch protection actually blocking a direct push; a tool gateway depends on there being no equivalent ungated tool. A conformance claim MUST document its specific enforcement point's known bypass paths rather than imply general bypass-resistance.
- This module does not change how guardrails are declared, owned, evaluated, or propagated (security.md §4 governs all of that); it only adds the Handoff decision-context binding, the `generative:*` operation-class convention, the artifact claim record, and the action-resolution record.
- Ambiguous applicability MUST produce `unknown` and fail closed for a protected operation.
- A bounded owner override MUST be exact, expiring, and auditable.
- This module MUST NOT be represented as proof that a record's subject matter is true, safe, or correct — only that a declared action was checked against applicable guardrails and decisions by a component the participant does not control, before it took effect.

A deployment MAY remain advisory and honestly claim only `context-aware` or `decision-resolved` behavior. Enforcement and the tool constraint in §5 become mandatory only when the deployment claims prevention for a class governed by a required guardrail.

## 12. Open questions

Design questions not yet resolved by this draft, including standalone-permit portability (§4) and whether the §3 `policy_owner` distinctness rule belongs in Security generally rather than only under this module, are tracked in [open-issues.md](open-issues.md).
