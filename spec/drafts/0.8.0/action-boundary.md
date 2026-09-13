# AWP Action Boundary 0.2.0

**Status:** Experimental working-draft profile specification
**Module ID:** `urn:awp:action-boundary`
**Direct dependencies:** Core; Handoff, for the `decision_context` axis this module gates on; Security, for signing and evidence binding

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Decision Durability (index.md §Purpose) makes an accepted decision discoverable and applicable. It does not, by itself, stop a participant from proceeding when that decision context could not be established. In an observed incident, a participant received a correctly reported `budget_exceeded` structural-selection result and an absent `decision_context` result from a Handoff-conformant re-entry projection, and performed guarded work anyway: it generated and committed public product imagery depicting an interface that did not exist in the product.

0.1.0 of this module addressed that gap with a resolver-and-permit design (an `action_intent`, an `applicable_decision_set`, a bound `action_permit`, and an enforcement adapter). A subsequent critical review identified three defects severe enough to redesign around rather than patch: (1) a free-text intent description is unverifiable and can be honestly-or-dishonestly mislabeled to avoid matching an applicable decision — "intent laundering"; (2) the design named no role responsible for authoring protected-action declarations and decisions, leaving the same fallible actor implicitly responsible for both doing the work and being governed by the rule; and (3) the design verified generated output for truthfulness after the fact, when the artifact that caused the incident (an invented image) could have been made structurally incapable of an untraceable claim by constraining the generation tool itself, rather than policing its output. This revision (0.2.0) is a substantial redesign addressing all three. It is informed by, but not limited to, the original incident and both reviews; both are preserved for traceability in `research/model-assisted-reviews/`.

This module does not claim that AWP replaces runtime authorization, sandboxing, or an organization's own policy enforcement, and it does not claim that a well-formed resolution proves the resulting artifact is true, safe, or correct — only that a declared, vocabulary-matched action was checked against structured decisions, by a component the acting participant does not control, before it took effect. A deployment that records these structures without gating a real mutation path MUST NOT claim the `action-enforced` or `output-attested` levels defined in §9; §1 of the Adapter Framework already establishes that a portable guardrail is policy state, not proof of enforcement, and this module inherits that distinction rather than replacing it.

This module explicitly does **not** solve decision capture — getting a durable rule out of prose and Git history and into a structured, `affects`-scoped decision record in the first place. That remains a projector- and human-authoring problem (§8, and open-issues.md). An action-boundary resolver operating over an incomplete decision set will resolve incorrectly no matter how well the rest of this module works; this module assumes decision capture as a precondition, not a feature it provides.

## 2. Terms

A **protected action class** is a receiver- or project-declared category of consequential operation (for example, "public promotional imagery") that this module's resolution and enforcement apply to. It is named from a fixed **operation vocabulary** (§3), never from free text.

A **policy author** is the human role responsible for declaring protected action classes and authoring the decisions that govern them. The policy author is distinct from, and MUST NOT be, the participant whose actions are being gated — the same actor cannot both be constrained by a policy and be its sole author, or the policy constrains nothing. A project MAY name its decision owner as policy author, but MUST record that as an explicit choice, not a default.

An **action resolution** is one record produced per contemplated action: it names the vocabulary operation, target, and artifact class; carries both Handoff completeness axes evaluated for that specific action; lists the applicable decisions; and states a result of `permit`, `deny`, or `unresolved`. It replaces the separate `action_intent` and `applicable_decision_set` records of 0.1.0 — they are produced and consumed together and have no independent lifecycle.

An **enforcement adapter** is a component outside the participant's own control — most concretely a CI gate on a protected branch, or a tool gateway that intercepts a specific tool call — that independently recomputes or verifies an action resolution before a protected operation is allowed to take effect.

An **artifact claim record** binds an externally visible artifact's stated claims to the evidence that supports each claim. For a protected artifact kind, this module requires the record to be a mechanical byproduct of a constrained transformation pipeline (§5), not a participant's self-report.

## 3. Operation vocabulary and protected action classes

Reading, validating, acknowledging, or summarizing a workstate MUST NOT by itself satisfy action-boundary decision resolution; resolution is computed per action, not once at session entry.

A participant MUST NOT describe a contemplated action in free text for resolution purposes. It MUST name: an **operation** drawn from a project's declared operation vocabulary (for example `image.composite`, `image.generate.freeform`, `asset.publish`); a **target** (a scope or scope-matching selector, not necessarily an existing path — see §3.1); and an **artifact class**, when the operation produces or publishes an artifact.

```json
{
  "operation": "image.generate.freeform",
  "target": "google-play:baseball",
  "artifact_class": "public-promotional-watch-imagery",
  "scopes": ["repo:android_sports_watches", "google-play:baseball"]
}
```

The vocabulary and the set of protected action classes are declared by the policy author in a project policy record, versioned and content-addressed the same way every other durable AWP record is. A resolver or enforcement adapter MUST treat an operation not present in the declared vocabulary as `unresolved` for a protected class, never as implicitly unprotected.

Naming an operation does not by itself prove the participant's actual tool call matches it — see §4 for how an enforcement adapter verifies that match rather than trusting it.

### 3.1 Selector matching against future targets

A decision's applicability MUST be expressible by artifact class and scope-matching selector (for example a path glob or a platform/listing identifier pattern), not only by a path that already exists. A decision authored before a target exists (before a new product listing directory is created, for instance) MUST still match that target once it exists, provided the target falls within the decision's declared selector.

## 4. Action resolution

A resolver MUST report structural selection and `decision_context` as independent axes for the specific action being resolved, matching Handoff's existing two-axis requirement (handoff.md §Bounded re-entry projection) rather than reusing a stale session-entry result. Absence of either result MUST NOT be interpreted as complete. A participant MUST NOT infer that no applicable decision exists merely because a bounded presentation omitted a decision, decision source, required artifact, or entry record — an empty selection is evidence of a budget limit, not evidence of an empty decision set.

```json
{
  "action": {
    "operation": "image.generate.freeform",
    "target": "google-play:baseball",
    "artifact_class": "public-promotional-watch-imagery"
  },
  "action_digest": "sha256:...",
  "capsule_digest": "sha256:...",
  "selection": "complete",
  "decision_context": "complete",
  "applicable_decisions": ["decision:public-watch-imagery-uses-literal-product-surfaces"],
  "requirements": ["depicted screen pixels must derive from a verified product capture"],
  "result": "deny"
}
```

(This example denies `image.generate.freeform` against a protected class — see §5; the operation that would resolve `permit` for this target is `image.composite`.)

When the capsule projection is `budget_exceeded`, when independent `decision_context` is absent, when the operation is not in the declared vocabulary, or when class or scope applicability is unknown, the result MUST be `unresolved`, never `permit`. Delegated, tool-mediated, decomposed, retried, and derived operations MUST inherit every mandatory decision and guardrail applicable to the originating action; a child tool call under a resolved parent task does not re-resolve scope independently of that parent.

A resolution's `result: permit` MAY carry binding fields — expiry, the exact input artifact digests it was granted against — directly on the resolution record. A standalone, transportable permit object, separate from the resolution that produced it, is NOT part of this module's core design; it is an extension point for a deployment whose resolution and enforcement are genuinely on different hosts or asynchronous in time (relevant to AWP's own multi-host Cooperation Contracts layer, but not required for a single-repository deployment) and is deferred to open-issues.md rather than specified here.

## 5. Protected-kind tool constraint

For a declared protected artifact class, an enforcement adapter MUST NOT permit invocation of a freeform-generation operation. It MUST restrict invocation to a composite or otherwise traceable operation whose inputs are named, verifiable source artifacts. This is the module's primary defense, not a fallback: verifying a freely generated artifact's truthfulness after the fact is a strictly harder problem than preventing the untraceable artifact from being producible at all. A generation tool that has no composite or traceable mode for a protected class MUST NOT be invocable for that class under an enforcing profile; that is a tooling gap to close, not a policy exception to grant.

This directly determines what an artifact claim record can honestly contain (§6): a composite operation's claim record is a byproduct of the transformation, and a freeform operation's claim record cannot be produced honestly at all.

## 6. Artifact claim record

When an externally visible artifact makes a product, provenance, safety, or compliance claim, an enforcing profile MAY require an artifact claim record before publication. For a protected artifact class, the record MUST be emitted by the transformation pipeline itself as a byproduct of a composite or traceable operation (§5), not authored or asserted by the participant.

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

AWP continues to distinguish policy records from enforcement (adapters.md §1). This module becomes preventative only when an enforcement point independently recomputes or verifies the action resolution before a protected operation takes effect.

A client-side commit hook is NOT an adequate enforcement point on its own: it is trivially bypassed (`git commit --no-verify`) and does not run on a party the participant doesn't control. The reference enforcement pattern for a single-repository deployment is a CI gate that runs on the target branch, recomputes the action resolution independently rather than trusting a submitted one, and blocks the merge unless the result is `permit` — enforceable to the extent the repository's branch protection actually prevents a direct push around it. A stronger, complementary pattern is a tool gateway that intercepts the specific tool call (for example the image-generation invocation itself) and verifies the requested operation against §5 before the call is allowed to execute; this is stronger than a CI gate because it constrains what can be *produced*, not only what can be *merged*, and it is what makes §4's operation-vocabulary claim verifiable rather than self-reported — the gateway checks the actual tool invocation against the declared operation, and denies on mismatch.

An enforcement adapter MUST independently verify: the action and capsule digest binding; the target and operation scope; required evidence records; expiry; and the absence of unresolved diagnostics. A deployment claiming enforced action-boundary conformance MUST use an enforcement point independent of the participant's unsupported assertion, and MUST document what its enforcement point does and does not prevent a determined participant from bypassing (§10). The participant's own statement that it complied is evidence, not enforcement.

## 8. Decision capture

The resolver in §4 can only find a decision that already exists as structured, `affects`-scoped state. This module does not, by itself, get a rule out of prose and history and into that state — that remains the policy author's responsibility, assisted by projector diagnostics. A projector SHOULD disclose when a frequently referenced requirement in an authoritative artifact has no corresponding effective decision, so the policy author can promote it explicitly — for example: "the authoritative artifact contains a relied-upon product-imagery rule, but no effective decision or required constraint declares applicability to public promotional assets." A projector MUST NOT autonomously convert arbitrary prose into a binding decision; only the policy author does that.

## 9. Diagnostics

| Code | Meaning |
|---|---|
| `AWP-ACTION-VOCAB-UNKNOWN` | The named operation is not in the project's declared vocabulary. |
| `AWP-ACTION-DECISION-RESOLUTION-REQUIRED` | Applicable decision closure was not computed for the action. |
| `AWP-ACTION-DECISION-CONTEXT-INCOMPLETE` | Selection or decision context cannot justify the action. |
| `AWP-ACTION-RESOLUTION-MISSING` | An enforcing adapter received or independently computed no resolution. |
| `AWP-ACTION-RESOLUTION-MISMATCH` | The resolution does not match the operation, inputs, target, or current context. |
| `AWP-ACTION-GATEWAY-MISMATCH` | A tool gateway's intercepted call does not match the resolved operation. |
| `AWP-ARTIFACT-CLAIM-UNVERIFIED` | An externally visible claim lacks required evidence, or was not produced mechanically for a protected class. |
| `AWP-ACTION-POLICY-AUTHOR-UNDECLARED` | A protected action class has no declared policy author distinct from the acting participant. |

These diagnostics preserve the existing `AWP-DECISION-CONTEXT-INCOMPLETE` semantics from Handoff rather than creating an alternate decision model; the action-specific codes identify where that existing decision failure reached an operational boundary.

## 10. Conformance claims

| Claim | Required evidence |
|---|---|
| `context-aware` | The authoritative workstate was discovered and validated. |
| `decision-resolved` | An action-scoped resolution was computed with both completeness axes, against a declared vocabulary operation. |
| `action-bound` | The resolution is content-digest bound to the exact action and capsule state. |
| `action-enforced` | An independent adapter recomputes or verifies the resolution and rejects a protected operation without a matching `permit` result. |
| `output-attested` | Protected-class artifacts are produced only via a constrained, traceable transformation (§5), with a mechanically emitted claim record checked at publication. |

A host MUST NOT claim a stronger level merely because a participant produced a well-formed record. `context-aware` alone describes correct entry behavior; it does not justify an `action-enforced` claim. `action-enforced` alone does not justify `output-attested` unless the tool constraint in §5 is actually in place — an adapter can faithfully enforce a resolution and still gate a freeform-generation tool whose output cannot honestly carry a claim record.

## 11. Limits and non-goals

- This module does not solve decision capture (§8); it assumes structured decisions exist and degrades to `unresolved` when they don't, which is a correct but not sufficient response — the missing decision is still missing.
- No enforcement point is unconditionally bypass-proof. A CI gate depends on branch protection actually blocking a direct push; a tool gateway depends on there being no equivalent ungated tool. A conformance claim MUST document its specific enforcement point's known bypass paths rather than imply general bypass-resistance.
- Protected action classes, their vocabulary, and their policy author MUST be declared by receiver or project policy; this module does not define a default protected set or assume any project has appointed a policy author.
- Ambiguous applicability MUST produce `unknown` and fail closed for a protected operation.
- A bounded owner override MUST be exact, expiring, and auditable.
- This module MUST NOT be represented as proof that a record's subject matter is true, safe, or correct — only that a declared, vocabulary-matched action was checked against structured decisions by a component the participant does not control, before it took effect.

A deployment MAY remain advisory and honestly claim only `context-aware` or `decision-resolved` behavior. Enforcement and the tool constraint in §5 become mandatory only when the deployment claims prevention for a declared protected action class.

## 12. Open questions

Design questions not yet resolved by this draft, including standalone-permit portability (§4) and a first concrete enforcement-adapter implementation, are tracked in [open-issues.md](open-issues.md).
