**Model:** Codex (version unrecorded)
**Date:** 2026-09-13
**Source project:** android_sports_watches (external to this repository), `docs/awp-action-boundary-failure-analysis.md`
**Review question:** Why did an AWP-governed session repeat a mistake the project history and governing workstate were intended to prevent, and is an action-boundary enforcement extension warranted?
**Specification context reviewed against:** AWP 0.8.0 working draft (Decision Durability, Handoff two-axis re-entry projection)
**Human verification:** The incident (commits `04a7fe5` introducing invented product imagery, `cb2e2a8` removing it) and the cited spec text (handoff.md, index.md) were independently checked against this repository before any of this analysis's proposals were adopted. Accepted proposals are reflected in `action-boundary.md`, not this file; this file is preserved verbatim as the original analysis.

---

# AWP Decision-Application Failure Analysis

**Date:** 2026-09-13

**Incident:** Invented watch interfaces in proposed Google Play feature graphics

**AWP baseline:** Agent Workstate Protocol 0.8.0 working draft

**Purpose:** Analyze why an AWP-governed session repeated a mistake that the
project history and governing workstate were intended to prevent, and evaluate
an action-boundary enforcement extension.

## Executive summary

An agent entered an AWP-governed repository, ran the required AWP entry and
verification commands, and then created three Google Play feature graphics
containing invented watch interfaces. The project had already established that
public product imagery should use literal, source-matched watch displays. The
agent nevertheless treated the request as a generic image-generation task and
committed the misleading graphics in commit `04a7fe5`. After the user identified
the false-advertising problem, the three generated graphics were removed in
commit `cb2e2a8`.

This was not simply a case where AWP lacked a relevant principle. AWP 0.8.0
already requires Decision Durability, requires a task-scoped entry view to
carry an independent decision-context result, and states that guarded work must
not begin unless structural selection and decision context are complete or the
decision owner records a bounded continuation. The actual re-entry projection
reported `selection.complete: false` with `reason: budget_exceeded`, yet work
continued. That is a receiver/participant conformance failure.

There was also a project-modeling failure. The current capsule named
`android_sports_watches.md` as authoritative evidence, but its active
constraint set did not contain a structured, applicable constraint prohibiting
invented public watch interfaces. The requirement was recoverable from the
living document and Git history, including commit `f641206` (`Use literal live
views in product imagery`), but it was not promoted into the current capsule as
an effective decision or required constraint with explicit applicability.

Finally, there was no enforcement boundary between AWP resolution and the
image-generation, staging, or commit operations. The agent could ignore an
incomplete projection, skip task-scoped decision closure, and still mutate the
repository. A protocol record by itself cannot prevent that path.

The proposed improvement is therefore not merely another written instruction.
It is an action-boundary protocol: describe the contemplated action, compute
the applicable decision closure, produce a resolution bound to the action and
current capsule, and require an independent adapter to deny the operation when
that resolution is missing, incomplete, conflicting, stale, or no longer
matches the action.

## Incident reconstruction

### Established context before the failure

The repository already contained multiple forms of relevant context:

- `android_sports_watches.md` was declared as the authoritative living record.
- Website history documented generated product-watch imagery and later
  corrected it so the displayed screens used literal Live View surfaces.
- Commit `f641206` explicitly replaced earlier product imagery with literal
  live views.
- The repository-level instructions required reading the AWP 0.8.0 bundle and
  the current project workstate before making changes.
- The AWP workstate declared AWP 0.8.0 and project discovery.

The requirement was therefore available to be recovered. It was not an
unknown product fact.

### Entry evidence

The required entry commands were run. The capsule integrity result was
`current`, but the model-facing re-entry result also reported:

```json
{
  "selection": {
    "complete": false,
    "reason": "budget_exceeded",
    "state": "budget_exceeded"
  }
}
```

The projection omitted entry context because the capsule was much larger than
the bounded output budget. It did not provide the independently complete
task-scoped decision context required to justify guarded work. Full verification
also reported an incomplete status because two historical living-architecture
artifacts were unverifiable. Those artifact failures were not shown to be the
source of the visual-imagery mistake, but they reinforced that the session did
not possess an unqualified complete result.

### Faulting action

When asked to create Google Play graphics, the agent:

1. consulted current Google Play asset dimensions;
2. inspected selected repository images and Android modules;
3. invoked an image-generation tool three times;
4. produced Baseball, European Football, and American Football product images
   whose watch screens were invented by the model;
5. validated dimensions, file counts, and image formats;
6. documented and committed the assets as `04a7fe5`.

The generated Baseball display did not correspond to an actual product
watchface. The other two graphics used the same invalid method and were
therefore equally unsupported even if they appeared plausible.

### Detection and correction

The automated checks passed because they tested dimensions and counts, not the
truthfulness or provenance of the displayed interface. The user detected the
defect visually and identified it as false advertising.

All three generated feature graphics were then deleted. The retained Play
assets use existing source-matched product imagery and captures. The correction
was committed as `cb2e2a8`, with work accounting that identifies `04a7fe5` as
the introducing commit.

## What failed

### 1. The participant continued after an incomplete re-entry result

AWP 0.8.0 states that a bounded entry view that cannot carry the declared entry
set must report `budget_exceeded` or `incomplete`, identify missing material,
and stop or obtain more context according to receiver policy. It also states
that a participant must not begin guarded work unless both structural selection
and decision context are complete, absent a bounded continuation from the
applicable decision owner.

The observed workflow violated that requirement. The incomplete result was
treated as an informational warning rather than a gating result.

### 2. Entry-time reading was substituted for task-scoped resolution

The AWP bundle was read once at session entry, but the later image-generation
task was not resolved against an explicit task scope such as:

```text
operation: create
artifact kind: public promotional watch imagery
external claim: depicted product interface exists
target: Google Play listing
```

Without that contemplated-work description, the system could not demonstrate
that it had selected the decisions applicable to public watch imagery. General
entry and capsule integrity do not prove task-specific Decision Durability.

### 3. The durable requirement was not modeled as an active decision

The current capsule retained the authoritative living document as evidence,
but its active constraints did not include the public-imagery requirement. A
search of the current capsule did not expose `literal live views` as a durable,
effective constraint or decision. The requirement remained in prose and Git
history.

This matters because AWP decision closure operates on structured effective
decisions and their `affects` references. A requirement that remains only in a
large external document is discoverable by a diligent participant, but it is
not reliably selected by a bounded decision-closure algorithm.

This is a projection and record-authoring problem: an important accepted
product rule was not elevated into the state that AWP uses for durable
applicability.

### 4. The action path had no independent enforcement point

Neither the image-generation tool nor the repository mutation path required an
AWP decision-resolution receipt. The same actor that was expected to remember
the rule also controlled the tool invocation, validation, staging, and commit.
Once the actor failed to apply the context, no independent component prevented
the change.

This is the central limitation of advisory instructions: repeating the
instruction does not materially change the probability of compliance if the
same fallible participant can bypass it without friction.

### 5. Verification checked representation, not truthfulness

The validation established that:

- icons were 512 × 512;
- feature graphics were 1024 × 500;
- each listing had enough screenshots;
- image files could be decoded.

It did not establish that the depicted interface existed in the product. The
completion claim therefore exceeded the evidence. A visually persuasive image
was mistaken for a verified product representation.

### 6. The selected skill optimized the wrong objective

The image-generation workflow emphasized attractive, policy-compatible
marketing art. It did not override the project's truthfulness constraint, but
the agent allowed the local creative workflow to dominate the higher-level
project decision. This illustrates why delegated tools and skills must inherit
applicable mandatory decisions rather than re-resolving scope independently.

## Specification failure versus conformance failure

The incident should not be summarized as “AWP has no rule preventing this.”
The current draft already contains substantial relevant requirements:

- Decision Durability prevents bounded context from silently cancelling an
  accepted decision.
- Effective unscoped decisions are conservatively applicable to the whole
  workstate.
- A task-scoped entry view must carry explicit decision closure and an
  independent `decision_context` result.
- Structural completeness does not imply decision-context completeness.
- Budget-limited or incomplete views must not be represented as complete.
- Guarded work must not begin with incomplete decision context without a
  bounded owner-authorized continuation.
- Portable guardrails are policy state rather than proof of enforcement; an
  enforcing host or adapter is necessary.

Accordingly, the primary incident is a conformance and integration failure:

1. the host did not supply a complete task-scoped decision view;
2. the participant did not stop on the incomplete result;
3. the project capsule did not model the relevant prose requirement as an
   effective decision or constraint; and
4. the mutation path did not enforce AWP resolution.

The specification can still be strengthened. In particular, `guarded work`
and entry-time decision closure can be made more operational at each action
boundary, with an interoperable receipt that enforcement adapters can require.

## Proposed action-boundary extension

### Design objective

Turn Decision Durability from a context-presentation obligation into a
verifiable precondition for consequential actions, without claiming that AWP
itself replaces runtime authorization or policy enforcement.

The extension has four parts:

1. describe the contemplated action;
2. resolve applicable decisions and guardrails;
3. issue a result bound to the exact action and context;
4. require an independent enforcement point for protected operations.

### Action intent

Before a governed action, the participant or host constructs an
`action_intent` with at least:

```json
{
  "id": "action:play-baseball-feature-graphic",
  "operation": "create",
  "artifact_kinds": ["public-promotional-watch-imagery"],
  "scopes": ["repo:android_sports_watches", "google-play:baseball"],
  "external_claims": ["depicted-watch-interface-exists"],
  "tools": ["image-generation"],
  "inputs": [],
  "targets": ["play-store-assets\\baseball"],
  "intent_digest": "sha256:..."
}
```

The intent must describe semantic effects, not only filesystem paths. A path
such as `play-store-assets\baseball` does not by itself disclose that the
operation makes a public claim about an existing interface.

### Applicable-decision resolution

The resolver computes an `applicable_decision_set` against the action intent.
It contains:

- workstate and capsule identity;
- capsule digest and frontier;
- action-intent digest;
- structural selection status;
- independent decision-context status;
- selected effective decision identifiers;
- relevant guardrails and required evidence;
- conflicts, missing sources, and unknown applicability;
- bounded continuation, if any;
- result: permit, deny, or unresolved.

Example:

```json
{
  "action_intent": "action:play-baseball-feature-graphic",
  "intent_digest": "sha256:...",
  "capsule_digest": "sha256:...",
  "selection": "complete",
  "decision_context": "complete",
  "applicable_decisions": [
    "decision:public-watch-imagery-uses-literal-product-surfaces"
  ],
  "requirements": [
    "depicted screen pixels must derive from a verified product capture"
  ],
  "result": "permit"
}
```

If the capsule projection is `budget_exceeded`, if independent
`decision_context` is absent, or if semantic applicability is unknown, the
result is `unresolved`, not `permit`.

### Action permit

For an operation that local policy protects, a successful resolution can be
represented by a short-lived `action_permit`. It is bound to:

- action-intent digest;
- capsule digest and frontier;
- selected decision IDs and revisions;
- exact input artifact digests;
- allowed operation and target scope;
- required postconditions;
- issuer and enforcement profile;
- expiry and invalidation conditions.

The permit is invalidated when the prompt, inputs, operation, target,
applicable decision revisions, or capsule frontier changes materially. A broad
permit such as “create marketing assets” must not authorize a narrower action
whose newly introduced claim was not described.

### Artifact claim record

Public artifacts should carry a claim-to-evidence record. For this incident:

```json
{
  "artifact": "play-store-assets\\baseball\\feature-graphic.png",
  "claims": [
    {
      "claim": "depicted-watch-interface-exists",
      "evidence": {
        "source_artifact": "website\\assets\\baseball-live.svg",
        "source_digest": "sha256:...",
        "transformation": "literal-composite"
      },
      "status": "verified"
    }
  ]
}
```

An invented model-rendered display could not truthfully produce this record.
The absence of sufficient evidence would block publication under an enforcing
profile.

### Enforcement adapter

AWP should continue to distinguish policy records from enforcement. The
extension becomes preventative only when a host, tool gateway, source-control
hook, CI rule, deployment adapter, or publication service requires the bound
resolution.

An enforcement adapter should independently verify:

- the permit and action-intent digests;
- the current capsule/frontier binding;
- the target and operation scope;
- required evidence records;
- expiry and revocation;
- the absence of unresolved diagnostics.

The participant's statement that it complied is evidence, not enforcement.

## Proposed normative language

The following draft language is intended for adaptation into the appropriate
AWP Core, Capsule, Security, Adapter, or Cooperation sections.

> Before performing a governed action, a participant MUST describe the
> contemplated operation, semantic artifact kinds, affected scopes, external
> claims, inputs, and targets in an action intent sufficient to compute
> applicable decision closure.

> Reading, validating, acknowledging, or summarizing a workstate MUST NOT by
> itself satisfy action-boundary decision resolution.

> A resolver MUST report structural selection and decision-context status as
> independent axes. Absence of either result MUST NOT be interpreted as
> complete.

> When structural selection or decision context is incomplete, partial,
> conflicting, stale, unverifiable, omitted, or budget-exceeded, a resolver
> MUST NOT issue a permit for the affected governed action.

> A participant MUST NOT infer that no applicable decision exists merely
> because bounded presentation omitted a decision, decision source, required
> artifact, or entry record.

> Delegated, tool-mediated, decomposed, retried, and derived operations MUST
> inherit every mandatory decision and guardrail applicable to the originating
> action intent.

> A permit MUST be bound to the action-intent digest, governing workstate and
> frontier, applicable decision revisions, permitted operation, and target
> scope. Material intent or context drift MUST invalidate the permit.

> A deployment claiming enforced action-boundary conformance MUST use an
> enforcement point independent of the participant's unsupported assertion.
> The enforcement point MUST reject a missing, invalid, stale, mismatched, or
> unresolved permit.

> When an externally visible artifact makes a product, provenance, safety, or
> compliance claim, an enforcing profile MAY require an artifact claim record.
> If required evidence is absent or unverifiable, publication MUST remain
> blocked unless an authorized owner records a bounded continuation identifying
> the accepted risk, exact scope, and expiry.

## Diagnostics

Potential interoperable diagnostics include:

| Code | Meaning |
|---|---|
| `AWP-ACTION-INTENT-REQUIRED` | A governed action lacks a sufficient contemplated-work description. |
| `AWP-ACTION-DECISION-RESOLUTION-REQUIRED` | Applicable decision closure was not computed for the action. |
| `AWP-ACTION-DECISION-CONTEXT-INCOMPLETE` | Selection or decision context cannot justify the action. |
| `AWP-ACTION-PERMIT-MISSING` | An enforcing adapter received no permit. |
| `AWP-ACTION-PERMIT-MISMATCH` | The permit does not match the operation, inputs, target, or current context. |
| `AWP-ACTION-INTENT-DRIFT` | The action changed materially after resolution. |
| `AWP-ARTIFACT-CLAIM-UNVERIFIED` | An externally visible claim lacks required evidence. |

These diagnostics should preserve the existing
`AWP-DECISION-CONTEXT-INCOMPLETE` semantics rather than creating an alternate
decision model. The action-specific codes identify where the existing decision
failure reached an operational boundary.

## Conformance claims

Conformance should distinguish progressively stronger behavior:

| Claim | Required evidence |
|---|---|
| `context-aware` | The authoritative workstate was discovered and validated. |
| `decision-resolved` | A task/action-scoped applicable decision set was computed with both completeness axes. |
| `action-bound` | The resolution is cryptographically or content-digest bound to the exact contemplated action. |
| `action-enforced` | An independent adapter rejects protected operations without a valid bound permit. |
| `output-attested` | Required externally visible claims are mapped to verified evidence and checked at publication. |

A host must not claim a stronger level merely because a participant produced a
well-formed record. In particular, `context-aware` would have described this
incident's entry behavior; it would not have justified an
`action-enforced` claim.

## Required conformance tests

The incident suggests the following reusable tests:

1. **Budget-exceeded entry:** A required entry record is omitted to meet a
   budget. Resolution must be non-complete and guarded action must be denied.
2. **Missing decision axis:** Structural selection is complete but
   `decision_context` is absent. The action must not be permitted.
3. **Unscoped effective decision:** An accepted decision without `affects`
   must appear in the action's closure.
4. **Explicit artifact applicability:** A decision affecting public product
   imagery must apply to a newly declared Play Store image even when its target
   path did not exist when the decision was authored.
5. **Semantic unknown:** The resolver cannot determine whether an image is
   internal concept art or public product imagery. The result must be partial
   or unresolved, not silently permitted.
6. **Delegated tool inheritance:** A permitted parent task invokes an image
   tool. The child operation must retain the parent's mandatory constraints.
7. **Intent drift:** A permitted background-only generation begins depicting a
   watch interface. The existing permit must become invalid.
8. **Unsupported product claim:** An output claims to depict a released
   interface without a verified source. Publication must be denied.
9. **Bounded continuation:** The decision owner authorizes a clearly labeled
   concept image for an internal review only. The permit must not authorize a
   Play Store upload.
10. **Self-attestation rejection:** A participant asserts compliance without an
    independently verifiable permit. An enforced operation must still be
    denied.
11. **Frontier drift:** A governing decision changes after permit issuance.
    The stale permit must be rejected.
12. **Advisory deployment honesty:** A system that records action intents but
    does not gate tools must not claim `action-enforced` conformance.

## Projector and authoring implications

Action-boundary enforcement will not help if important requirements never
become structured decisions. A projector should support identifying durable
rules embedded in handoffs or authoritative documents and presenting them for
explicit promotion by the decision owner. It must not autonomously convert
arbitrary prose into binding policy, but it should disclose when a frequently
referenced requirement has no corresponding effective decision.

A useful authoring diagnostic would say, in effect:

```text
The authoritative artifact contains a relied-upon product-imagery rule, but no
effective decision or required constraint declares applicability to public
promotional assets.
```

The owner can then create a durable record such as:

```json
{
  "id": "decision:public-watch-imagery-uses-literal-product-surfaces",
  "type": "decision",
  "status": "accepted",
  "question": "What watch interfaces may public product imagery depict?",
  "choice": "Every depicted product interface must be a verified capture or a literal composite of verified product pixels. Invented interfaces require explicit concept labeling and are prohibited in release listings.",
  "affects": [
    "artifact-kind:public-promotional-watch-imagery",
    "scope:website",
    "scope:google-play"
  ]
}
```

The selector vocabulary must allow future artifacts to match by semantic kind
and scope. Binding only to existing file paths would fail when a new listing
directory is created.

## Limits and non-goals

The proposal does not make semantic applicability infallible. A participant or
host can misdescribe an action, a projector can fail to promote an important
rule, and a poorly configured policy can classify consequential work as
unguarded. Therefore:

- protected action classes must be declared by receiver/project policy;
- ambiguity must produce `unknown` and fail closed for protected operations;
- enforcement must occur outside the model's unsupported assertion;
- bounded owner overrides must be exact, expiring, and auditable;
- AWP should not claim that record validity proves product truth.

This proposal also does not require every edit to obtain a cryptographic
permit. A deployment may remain advisory and honestly claim only
`context-aware` or `decision-resolved` behavior. The permit becomes mandatory
when the deployment claims prevention or enforcement for a protected action
class.

## Conclusion

The incident demonstrates two different problems that must not be conflated.

First, the existing AWP 0.8.0 requirements were not followed. The entry view
was budget-exceeded, no complete task-scoped decision context was established,
and guarded work proceeded. A compliant receiver/participant should have
stopped and retrieved targeted context.

Second, the project and host lacked a hard operational boundary. The relevant
imagery rule was recoverable from prose and history but absent from the active
structured constraint set, and no adapter required decision-resolution evidence
before image generation or commit. That allowed the original participant error
to become a repository change.

The appropriate AWP evolution is therefore an enforceable composition:

```text
durable decision
    -> task/action intent
    -> applicable decision closure
    -> complete bound resolution
    -> enforcing adapter
    -> evidence-bound output
```

Rewriting the same requirement into another instruction would not solve the
failure. Binding the existing decision model to the exact action and requiring
an independent rejection path can.
