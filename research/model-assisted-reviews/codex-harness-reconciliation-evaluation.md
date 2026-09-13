**Model:** Codex (version unrecorded)
**Date:** 2026-09-13
**Document type:** Critical evaluation of `awp-harness-reconciliation-brief.md` (filed alongside this document)
**Review question:** Is the reconciliation brief's own critique of DeepSeek's harness proposal internally consistent with the actual state of AWP Core and action-boundary 0.3.0?
**Human verification:** Each of the four corrections below was independently checked against `core.md`, `action-boundary.md`, and `tools/awp_action_boundary.py` before being accepted. The most significant finding -- that action-boundary 0.3.0's shipped resolver read Core's `affects` field as a glob selector and an undefined top-level `requirements` field, both reinterpreting a Core-owned field in violation of core.md's own extension rule -- was fixed in action-boundary.md 0.3.1 (see that document's revision note and open-issues.md #52). The other three corrections (decision `source` is not authorship; the harness's H0-H4 ladder duplicates action-boundary's existing conformance ladder; a Compliance Report fits Core's `execution`/`claim`/`evidence` vocabulary better than `change`/`checkpoint`) apply to future harness/adapter-profile design and are not yet acted on.

---

# Evaluation of the AWP Harness Reconciliation Brief

**Evaluated artifact:** `awp-harness-reconciliation-brief.md`  
**Evaluation basis:** the operative AWP 0.8.0 working-draft bundle, with particular attention to Core, Security, Handoff, Action Boundary 0.3.0, and the Adapter Framework 0.5.0.  
**Recommendation:** accept the architectural reframe, but revise the record-level details before incorporating the proposal into normative AWP.

## Overall assessment

The reconciliation brief is directionally strong and worth preserving, but it should not be incorporated into normative AWP verbatim. Its main architectural judgment is correct:

- do not introduce `urn:awp:harness` merely to bind existing AWP semantics to a runtime;
- reuse Core decisions, Security guardrails, and Action Boundary resolutions;
- express the runtime mechanism as a versioned Action Boundary adapter profile;
- preserve the five-stage lifecycle, fresh-context review, and decision-capture UX.

This follows the Adapter Framework's rule that adapters map AWP modules into external runtimes without redefining their semantics. An adapter needs a payload-module identity only when it introduces portable records or events that must survive outside the external system.

Four substantive issues should be corrected before the design proceeds.

## 1. Decision `source` is not authorship

The brief maps its proposed `authored_by` and `authored_at` fields to Core's `source` plus implicit event provenance. That mapping is not exact.

Core defines `source` as a reference to a Core artifact record. It identifies supporting material; it does not identify the decision's author or authorship time. When immutable event history is available, the lifecycle event's actor and occurrence time can supply provenance. A snapshot-only decision, however, may not carry equivalent explicit authorship metadata.

The revised proposal should distinguish:

- the supporting source artifact;
- the actor and occurrence time of the decision lifecycle event;
- host-local capture metadata that has not been promoted into portable AWP state.

It should not imply that `source` substitutes for decision authorship.

## 2. Decision selectors and `requirements` need a legitimate schema location

The brief correctly rejects the proposed nested replacement for Core `affects`, but saying that selector matching is only a resolver-side concern leaves a portability gap.

Core `affects` is an array of record or artifact references. It is not an operation-class, artifact-class, or target-glob field. A portable resolver still needs a portable, typed place from which to obtain the selectors that apply a decision to a contemplated action.

The same issue applies to `requirements`. The Action Boundary resolver currently reads an unqualified `requirements` property from decisions, but Core does not define that property. A module that extends a Core record must put its fields under `modules.{module-id}`; it must not add new unqualified Core semantics informally.

A clean design would retain Core `affects` unchanged and define an Action Boundary decision extension, for example:

```json
{
  "modules": {
    "urn:awp:action-boundary": {
      "selectors": {
        "resources": ["path:store-assets/**"],
        "artifact_classes": ["artifact-class:public-promotional-imagery"]
      },
      "requirements": ["Use literal product surfaces"]
    }
  }
}
```

An alternative would be to represent selectors as typed records referenced by Core `affects`. Either approach needs explicit normative semantics and schema coverage. Core's existing explicit decision-closure algorithm should remain unchanged.

This also exposes a current Action Boundary issue: section 3.1 and the first-pass resolver treat decision `affects` values as glob-capable action selectors, while Core defines them as record or artifact references. The reconciliation should resolve that cross-module mismatch rather than simply inheriting it.

## 3. H0-H4 duplicates Action Boundary's conformance claims

The brief says that the proposed H0-H4 levels need no changes. That is inconsistent with its own anti-duplication argument.

Action Boundary 0.3.0 already defines these conformance claims:

- `context-aware`;
- `decision-resolved`;
- `action-bound`;
- `action-enforced`;
- `output-attested`.

The runtime binding should report evidence against those existing claims. H0-H4 should be removed or explicitly treated as non-portable host shorthand mapped one-to-one to the Action Boundary claims. It should not become a second AWP conformance taxonomy.

## 4. A Compliance Report is not naturally a Core `change` or `checkpoint`

A Core `change` relates semantic work to modified artifact identifiers. A Core `checkpoint` records a useful continuation point and its frontier. Neither type naturally represents a compliance assessment.

Prefer existing Core records when they preserve the necessary meaning:

- an `execution` record for the review run;
- a `claim` for each resulting finding or verdict, with an appropriate epistemic status;
- `evidence` identifying the reviewed inputs, procedure, environment, and result.

If the assessment must remain a portable structured object with fields such as reviewed action digest, capsule digest, reviewer identity, verdict, and findings, Action Boundary should define a module-owned `compliance_assessment` or `review_assessment` record. That need would justify extending Action Boundary, but not creating a separate Harness module.

The fresh-context reviewer is useful defense in depth, but context separation alone does not establish organizational or technical independence. A model reviewer may share systematic blind spots with the acting model. Its report is evidence; it becomes a blocking control only when an enforcement point requires an acceptable result before allowing the protected operation.

## Tool-invocation binding

`tool_arguments_digest` is a valuable addition because the existing abstract `action_digest` does not necessarily bind a resolution to the exact intercepted call. A digest alone, however, is not enforcement.

The binding must specify:

- canonical serialization of tool arguments;
- tool identity and version;
- digest algorithm and domain separation;
- binding to the action, capsule state or frontier, and resolution;
- gateway-side recomputation from the actual intercepted invocation;
- expiry, replay prevention, and time-of-check/time-of-use behavior;
- handling of secrets or low-entropy sensitive values in arguments;
- failure behavior when arguments cannot be captured or normalized reliably.

A structured `invocation_binding` within the Action Boundary resolution is likely clearer than a bare digest field. The enforcement adapter must calculate or independently verify it from the actual call. A digest supplied only by the participant being gated provides no independent assurance.

## Decision-capture UX

Corrective-commit and review-comment capture are promising responses to Action Boundary's acknowledged decision-capture gap. They must remain an authoring workflow, not an automatic policy-conversion mechanism.

A corrective commit or review comment may propose a candidate decision or guardrail, but it may be incomplete, mistaken, local to one incident, or authored by someone without policy authority. The binding should therefore:

1. detect and present the candidate rule;
2. collect explicit applicability, rationale, provenance, and intended owner;
3. require acceptance by the applicable policy owner;
4. publish a typed decision or guardrail only after that acceptance;
5. preserve the original source as evidence without treating its prose as self-authorizing.

This is consistent with Action Boundary's rule that a projector must not autonomously convert arbitrary prose into a binding decision or guardrail.

## Recommended adapter-profile shape

The revised proposal should become an independently versioned profile such as `claude-code-action-boundary-v1`. It may be referenced by `adapters.md`, but a separate profile document will be easier to version, test, and eventually register.

Following the Adapter Framework checklist, it should declare:

- the exact external host and supported versions;
- supported AWP family and module versions;
- identity, authority, and authentication mappings;
- mappings for session start, prompt classification, pre-tool gating, post-tool verification, and session-end review;
- which lifecycle stages are advisory and which can actually block an operation;
- ordering, retries, idempotency, cancellation, crash recovery, and acknowledgement;
- artifact and evidence retrieval;
- lossy fields and unavailable host capabilities;
- all known bypass paths, including equivalent tools, shell or filesystem access, direct API calls, delegation, and disabled hooks;
- conformance fixtures and the evidence required for each existing Action Boundary claim.

If Claude Code and Cowork do not expose identical lifecycle and blocking behavior, they should use separate profiles or explicit host-specific mappings rather than one profile that implies equivalent enforcement.

## Minimum conformance fixtures

The smallest useful implementation should demonstrate at least:

1. a protected freeform operation is blocked before invocation;
2. complete context and a matching permitted operation can proceed;
3. incomplete, absent, stale, or budget-exceeded context fails closed;
4. tool arguments changed after resolution produce a mismatch and block;
5. a tool alias, shell path, direct API call, or delegated subagent cannot silently bypass a mandatory guardrail;
6. missing or failed post-tool verification quarantines the result when prevention was impossible;
7. missing or failed fresh-context review cannot satisfy a required-review control;
8. decision-capture suggestions never become binding without policy-owner acceptance;
9. the profile reports the exact known bypasses that remain;
10. claimed `context-aware`, `decision-resolved`, `action-bound`, `action-enforced`, and `output-attested` levels are backed by distinct evidence.

## Inclusion recommendation

Accept `awp-harness-reconciliation-brief.md` as a reconciliation or design-review artifact after the corrections above. Do not copy its present wording directly into the normative specification.

A suitable long-term location is:

```text
research/model-assisted-reviews/awp-harness-reconciliation-brief.md
```

The next design response should provide a revised adapter profile that:

- uses Core's actual decision record and a properly namespaced Action Boundary extension where needed;
- reuses Security guardrails and Action Boundary's operation and resolution semantics;
- resolves the selector-applicability mismatch;
- reuses Action Boundary's existing conformance claims rather than H0-H4;
- defines an independently verified invocation binding;
- preserves the five-stage lifecycle, fresh-context reviewer, and policy-owner-mediated decision-capture UX;
- documents bypasses and supplies host-specific conformance fixtures.

**Final verdict:** accept the architectural reframe and preserve the brief as design history, but require the four record-level corrections before treating the proposal as part of operative AWP semantics.
