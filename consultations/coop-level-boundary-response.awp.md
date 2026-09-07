---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 7d2b9e64c0a1483fb85e37d19c6a02f5
workstate_id: urn:uuid:awp-coop-level-boundary-response-2026-09-07
frontier:
  - evt:coop-level-boundary-response
checkpoint: checkpoint:coop-level-boundary-response
generated_at: 2026-09-07T15:52:00Z
generated_digest: sha256:3420918487c630f53985a061af03fa328bef2f04dc02b0b0deb2d72852f79fcc
---
<!-- awp:generated:start -->
# COOP-1 and COOP-2 functional-boundary consultation — response

`actor:claude-review`'s response to `consultation:coop-level-boundary`, one bounded critique
round under `max_rounds: 1`. Answered COOP-0 style: no protocol source, schema, or workstate
file was modified, no ledger lease was entered, and no guarded intent was announced. This
capsule is the only artifact produced. Continuation past this round requires
`principal:mark`'s recorded approval.

Terminal outcome: **revised**. The proposed cut is the right cut, and I would accept it after
the six normative edits below. The physical/semantic division between COOP-1 and COOP-2 is
sound and I found no argument for moving it. What I did find: two responsibilities pulled up
to COOP-2 that COOP-1 already owns today, one conditional clause that would dissolve COOP-1's
only substantive guarantee, one omission that hides the lease's real job, and — most
importantly — a structural reason the boundary cannot currently be audited at all.

## Verdict on the proposed boundary

Correct as proposed: stable binding identity, durable event frontier, physical path/artifact
scopes with access modes, deterministic overlap outcomes, and the refresh/checkpoint/handoff/
recoverable-terminal cluster all belong at COOP-1. Revision-pinned semantic selectors, the
`same`/`related`/`different`/`ambiguous`/`unresolvable` resolution results, integration
readiness, and the change-set dependency graph all belong at COOP-2. Neither the "no universal
analyzer" nor the "no COOP-3 enforcement" exclusion is overreaching.

Everything below is a correction to the edges of that cut, not to its location.

## F1 — The boundary is unauditable: Coordination does not attribute its mechanisms to contract levels

This is the finding that matters most, and it is a defect in the draft rather than in the
proposal.

The boundary is asserted in `cooperation-contracts.md`, but the mechanisms it partitions are
defined in `coordination.md`, and that document mostly does not say which contract owns what.
Thirteen of its twenty-seven sections contain no `COOP-1`, `COOP-2`, or `COOP-3` mention at
all — and they are precisely the sections this consultation reassigns:

| Section | Contract attribution present |
|---|---|
| §6 Scopes and access claims | none |
| §8 Observed scope | none |
| §9 Overlap and conflict | none |
| §10 Negotiation and commitments | none |
| §11 Interface contracts | none |
| §12 Typed preconditions | none |
| §14 Verification | none |
| §15 Dependency graph and staleness | none |
| §16 Integration plan and result | none |
| §17 Deterministic projection | none |
| §24 Minimum conformance fixtures | none |

An implementer reading `coordination.md` §15 cannot tell whether staleness propagation is
required for a COOP-1 claim. An assessor cannot falsify a COOP-1 claim that omits it. Until
this is fixed, any boundary statement — including this one, if accepted — lives in one document
and is contradicted by silence in the other.

**Edit 1.** Add to `coordination.md` §3, after the cumulative-ladder table, a normative
mechanism-attribution table assigning every mechanism section its minimum contract, and add a
`**Minimum contract:**` line beneath each mechanism section heading. Proposed assignment,
consistent with the rest of this response: §6 COOP-1 for physical selector kinds and access
modes, COOP-2 for `semantic_targets` and `relied_upon_read`; §7 COOP-1; §8 COOP-2; §9 COOP-1
for `none`/`informational`/`compatible`/`ordered`/`blocking` over physical scopes, COOP-2 for
`unknown` arising from semantic ambiguity and for `negotiation_required`; §10 COOP-2; §11–§14
COOP-2; §15 split per Edit 3; §16 COOP-2; §17 COOP-1; §19 COOP-3.

## F2 — "where supported" would dissolve COOP-1's only substantive guarantee

The proposal grants COOP-1 "atomic guarded intent admission **where supported**".
`cooperation-contracts.md` §4.1 contains no such conditionality: "The binding MUST make the
announce-and-check operation atomic with respect to other `COOP-1` announce operations for the
same guarded scopes," reinforced by "A warning-only result is insufficient for a binding to
claim the `COOP-1` guarded-mutation guarantee."

Atomic admission is the one thing COOP-1 promises that portable exchange does not. Made
conditional, evidence scenario 5 in §4.3 — simultaneous incompatible announcements producing
one permitted and one blocked outcome — becomes unfalsifiable, because any binding that fails
it can claim atomicity was not "supported". A store that cannot supply atomic admission is not
a degraded COOP-1; it is not COOP-1. The draft already has the correct escape hatch for that
case, and it is not a conditional MUST: `operational_mode` of `snapshot-only` or `degraded` in
the cooperation binding schema, plus `AWP-COORD-LEDGER-UNAVAILABLE`.

**Edit 2.** Strike "where supported" from the boundary statement. If accommodation for weak
stores is wanted, state it as the converse in §4.1: "A binding that cannot make announce-and-
check atomic with respect to concurrent announcements for the same guarded scopes MUST NOT
claim `COOP-1` and MUST disclose `operational_mode` `snapshot-only` or `degraded`."

## F3 — "staleness", "preconditions", and "verification" each name two different obligations at two different levels

The proposal assigns "change-set dependencies, preconditions, verification, staleness" wholly
to COOP-2. That silently deletes an existing COOP-1 requirement. `cooperation-contracts.md` §4
already requires of a COOP-1 binding: "validate workstate identity, event identity, ancestry,
revisions, lifecycle transitions, pinned references, **typed precondition and verification
bindings, and applicable staleness rules**." §4.3 scenario 3 makes it an evidence obligation:
"Invalid ancestry, revision, transition, precondition, verification, or staleness input is
excluded or blocks the affected action with a stable diagnostic."

Two distinct obligations are wearing the same nouns:

- **Record-validity staleness** — is this event admissible given ancestry, revision, pinned
  references, and applicable staleness rules. Structural, analyzer-free, already COOP-1, and
  already carrying fixture obligations.
- **Dependency staleness** — `coordination.md` §15's reverse-dependency propagation,
  transitive cause retention, and the `*.revalidated`/`*.rebased`/`*.superseded` clearing
  transitions that gate readiness. Genuinely COOP-2.

The same doubling applies to preconditions and verification: COOP-1 validates that a typed
precondition or verification record is *bound* correctly — pinned to the right revision, well
formed, referring to records that exist. COOP-2 *evaluates* whether the predicate still holds
and lets the answer gate readiness. Scenario 8 in §24, "verification bound to the wrong
revision", is a COOP-1 fixture by this reading; evaluating whether a passing verification is
still trustworthy is COOP-2.

**Edit 3.** Define both terms in `cooperation-contracts.md` §2 and use them consistently in
§4, §6, and `coordination.md` §15. In the boundary statement, COOP-1 keeps "record-validity
staleness and precondition/verification binding validation"; COOP-2 takes "dependency staleness
propagation and precondition/verification predicate evaluation".

## F4 — Declared-versus-observed comparison is already partly COOP-1

The proposal assigns "declared-versus-observed scope comparison" entirely to COOP-2. Two
existing clauses contradict that. §4.2 requires a COOP-1 participant, at every meaningful
checkpoint and before exit, to "publish its **actual scope**, outcome, evidence references,
unresolved work, and recommended next action" — actual, not declared, so a COOP-1 participant
already reconciles the two. And `coordination.md` §7 states the deviation obligation
unconditionally — "the writer MUST either update the intent before publishing a ready change
set or record an explicit deviation" — qualifying only the readiness gate as COOP-2.

The line falls in a different place than proposed. COOP-1 owns the participant's own
self-declared actual-versus-declared reconciliation at checkpoint, over physical scopes, with
no analyzer. COOP-2 owns the tool-produced `observed_scope` record of §8, with its required
`analyzer`, `method`, `base_revision`, `result_revision`, and evidence digest, and owns
readiness gating on material under-declaration.

A related latent ambiguity: §4.2 says "actual scope" and §8 says "observed scope", and nothing
in either document says whether these are the same concept. They are not — one is an assertion
by the actor, one is evidence produced about the actor — and the draft should say so.

**Edit 4.** In the boundary statement, give COOP-1 "self-declared actual-versus-declared scope
reconciliation at checkpoint" and give COOP-2 "analyzer-produced observed scope with method and
evidence digest, and readiness gating on undeclared scope". In §4.2, add: "Actual scope is the
participant's own assertion about work performed. It is not an `observed_scope` record, which
is analyzer-produced evidence under COOP-2 and does not overwrite the participant's
declaration."

## F5 — The COOP-1 lease is not only liveness

"Advisory participant liveness" is accurate but drops the obligation that makes recovery work.
§4.2: "The binding MUST reject release while an intent linked to the lease remains nonterminal
or unless a durable receipt identifies an already published handoff artifact and its integrity
digest." The schema enforces it — `$defs.participantLease` conditionally requires
`handoff_receipt` when `status` is `released`.

That is exit integrity, not liveness. An implementer reading the boundary statement as written
would build a TTL heartbeat, satisfy "advisory participant liveness", and fail §4.2 without
noticing. The lease is doing two jobs and only one is named.

**Edit 5.** In the boundary statement, replace "advisory participant liveness" with "advisory
participant liveness with enforced exit coupling: release requires a nonterminal-intent check
and a durable handoff receipt".

## F6 — COOP-2's claim unit is inconsistent with COOP-1's

§4 is explicit that the claim attaches to a composition: "A component MAY advertise a
`deterministic-coordination-projector` capability, but that component alone MUST NOT claim
`COOP-1`; the contract applies to the composed participant, binding, projector, checkpoint, and
recovery behavior." §6 has no equivalent. It attaches every COOP-2 obligation to "a `COOP-2`
binding", and the proposal inherits that framing by stating the boundary purely as a capability
list.

As written, a semantic-registry vendor can satisfy every sentence in §6 and claim COOP-2
without any participant, checkpoint, or recovery behavior — the exact overclaim §4 exists to
prevent. This will matter more at COOP-2 than at COOP-1, because COOP-2's components are the
ones plausibly sold separately.

**Edit 6.** Add to §6, mirroring §4: "A registry, analyzer, or readiness evaluator alone MUST
NOT claim `COOP-2`; the contract applies to the composed participant, binding, registry,
analyzer, integration-readiness evaluator, checkpoint, and recovery behavior."

## F7 — Two readiness gates, neither named (editorial)

COOP-1 already has a readiness gate: §4.2's "a binding MUST NOT permit guarded work while the
canonical capsule is `modified`". COOP-2 adds a second one over change-set and dependency
state. The proposal's phrase "policy-controlled integration readiness" reads as though COOP-1
gates nothing. One clarifying sentence in §4.2 distinguishing capsule-freshness readiness from
integration readiness would prevent the misreading. Editorial, not structural.

## Classification: what is not a boundary defect

The consultation asked to separate specification defects from missing bindings and missing
evidence. Two things that look like boundary problems are not:

**Missing binding, not a defect.** No COOP-2 binding exists in this repository. There is no
semantic registry implementation, no selector analyzer, and no integration-readiness evaluator
under `tools/`; the only substantive `semantic` handling is inside `awp_projector.py`.
`coordination.md` §26 open issue 5 already records this. The consequence for this consultation
is narrow but real: the COOP-1/COOP-2 boundary is currently a paper split, and no
implementation can yet demonstrate that a responsibility placed on the COOP-2 side is
implementable there. I would not freeze the boundary text as final until one COOP-2 binding
exercises it, though the edits above should land now, because they correct statements that are
wrong today regardless.

**Missing evidence, not a defect.** §4.3 lists nine COOP-1 evidence scenarios; §24 lists
thirty-two conformance fixtures; nothing maps them to each other, and §24 carries no contract
attribution (see F1). An assessor cannot currently determine which of the thirty-two are
required for a COOP-1 claim. Separately, the live binding reports `operational_reach:
worktree-local` and `claim_state: partial`, which means scenarios 4, 5, and 9 — the
multi-participant and cross-filesystem-path cases — are the ones least likely to have been
exercised. Recommended, though outside this consultation's requested action: add a mapping
table from each §4.3 scenario to the §24 fixtures that discharge it.

## Remaining disagreement

None on the location of the boundary. F2 is the one place where I am asserting the proposal is
substantively wrong rather than imprecise, and I would expect that to be the point Codex
contests if any: the argument for "where supported" is presumably that a repository-local
file binding cannot always guarantee atomicity, and §4 does promise COOP-1 "MUST NOT require a
separate database or continuously running service". My position is that this tension is real
but already resolved by the existing `operational_mode` disclosure, and that resolving it
instead by weakening the MUST would leave COOP-1 claiming nothing testable.
<!-- awp:generated:end -->

<!-- awp:7d2b9e64c0a1483fb85e37d19c6a02f5:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-level-boundary-response-2026-09-07",
  "title": "COOP-1 and COOP-2 functional-boundary consultation — response",
  "created_at": "2026-09-07T15:52:00Z",
  "created_by": "actor:claude-review",
  "completeness": "portable",
  "modules": [
    {"id": "urn:awp:core", "version": "0.8.0", "required": true},
    {"id": "urn:awp:capsule", "version": "0.5.0", "required": true},
    {"id": "urn:awp:handoff", "version": "0.5.0", "required": true}
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:7d2b9e64c0a1483fb85e37d19c6a02f5:manifest:end -->

<!-- awp:7d2b9e64c0a1483fb85e37d19c6a02f5:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-level-boundary-response-2026-09-07",
  "frontier": [
    "evt:coop-level-boundary-response"
  ],
  "generated_at": "2026-09-07T15:52:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop-level-boundary",
        "type": "consultation",
        "revision": 2,
        "status": "answered",
        "purpose": "critique",
        "question": "What is the smallest useful functional boundary between COOP-1 and COOP-2 in the AWP 0.8.0 draft?",
        "requested_action": "Return one bounded independent critique identifying misplaced responsibilities and exact recommended normative edits. Do not modify protocol sources.",
        "decision_owner": "principal:mark",
        "participants": ["actor:codex", "actor:claude-review"],
        "effective_loop_policy": {"max_rounds": 1, "continuation_requires": "recorded decision-owner approval"},
        "context": {
          "base_revision": "git:5a30c74378c0d7bc89022dff6f830dba41f07d39",
          "working_tree_state": "uncommitted changes present in spec/drafts/0.8.0 and schemas at review time",
          "response_path": "consultations/coop-level-boundary-response.awp.md"
        },
        "read_first": [
          "decision:coop-level-boundary-revised",
          "claim:mechanism-attribution-absent",
          "claim:atomic-admission-unconditional",
          "claim:staleness-term-collision",
          "claim:actual-scope-already-coop1",
          "claim:lease-exit-coupling-omitted",
          "claim:coop2-claim-unit-inconsistent"
        ],
        "desired_output": "A decision on whether the proposed COOP-1/COOP-2 boundary is correct, with exact recommended normative edits.",
        "answer": "The proposed boundary places the physical/semantic cut correctly and is accepted with six normative edits. Corrections: strike the 'where supported' conditional on atomic guarded intent admission, which contradicts the unconditional MUST in cooperation-contracts.md 4.1 and would make COOP-1 evidence scenario 5 unfalsifiable; return record-validity staleness and precondition/verification binding validation to COOP-1, keeping only dependency-staleness propagation and predicate evaluation at COOP-2; return self-declared actual-versus-declared scope reconciliation at checkpoint to COOP-1, keeping analyzer-produced observed_scope and readiness gating at COOP-2; restate COOP-1 participant liveness as including enforced exit coupling via handoff receipt; add a composed-claim-unit sentence to section 6 so a registry or analyzer alone cannot claim COOP-2; and, prerequisite to auditing any of this, add per-section contract attribution to coordination.md, thirteen of whose twenty-seven sections currently name no contract. COOP-2 having no reference binding is a missing binding, and the unmapped 4.3-to-24 evidence relationship is missing evidence; neither is a boundary defect.",
        "terminal_result": "revised"
      }
    ],
    "decisions": [
      {
        "id": "decision:coop-level-boundary-revised",
        "type": "decision",
        "question": "Is the proposed COOP-1/COOP-2 functional boundary the smallest useful one, and what must change before it is adopted into the 0.8.0 draft?",
        "status": "proposed",
        "choice": "Adopt the proposed boundary with six normative edits: (1) add per-section contract attribution to coordination.md and a mechanism-attribution table to section 3; (2) strike 'where supported' from atomic guarded intent admission and add the converse disclosure requirement to 4.1; (3) define record-validity staleness versus dependency staleness in section 2 and split precondition/verification into binding validation at COOP-1 and predicate evaluation at COOP-2; (4) assign self-declared actual-scope reconciliation to COOP-1 and analyzer-produced observed_scope to COOP-2, and state in 4.2 that actual scope is not an observed_scope record; (5) restate COOP-1 lease as advisory liveness with enforced exit coupling; (6) add a composed-claim-unit sentence to section 6 mirroring section 4.",
        "decided_by": "actor:claude-review",
        "requires_authority": "principal:mark",
        "affects": [
          "spec/drafts/0.8.0/cooperation-contracts.md",
          "spec/drafts/0.8.0/coordination.md"
        ]
      }
    ],
    "claims": [
      {
        "id": "claim:mechanism-attribution-absent",
        "type": "claim",
        "statement": "Thirteen of coordination.md's twenty-seven sections contain no COOP-1, COOP-2, or COOP-3 mention, including sections 6, 8, 9, 10, 11, 12, 14, 15, 16, 17 and 24 — precisely the mechanisms the proposed boundary reassigns — so the boundary cannot be audited against the module that defines those mechanisms.",
        "epistemic_status": "verified",
        "evidence": ["evidence:section-attribution-scan"]
      },
      {
        "id": "claim:atomic-admission-unconditional",
        "type": "claim",
        "statement": "cooperation-contracts.md 4.1 requires atomic announce-and-check unconditionally and states that a warning-only result is insufficient for the COOP-1 guarded-mutation guarantee, so the proposal's 'where supported' qualifier weakens an existing MUST and would make section 4.3 evidence scenario 5 unfalsifiable.",
        "epistemic_status": "verified",
        "evidence": ["evidence:coop1-atomicity-text"]
      },
      {
        "id": "claim:staleness-term-collision",
        "type": "claim",
        "statement": "cooperation-contracts.md section 4 already requires a COOP-1 binding to validate typed precondition and verification bindings and applicable staleness rules, and section 4.3 scenario 3 makes that an evidence obligation, so assigning staleness, preconditions and verification wholly to COOP-2 would delete an existing COOP-1 requirement; the draft uses one set of nouns for two distinct obligations at two levels.",
        "epistemic_status": "verified",
        "evidence": ["evidence:coop1-validation-text", "evidence:dependency-staleness-text"]
      },
      {
        "id": "claim:actual-scope-already-coop1",
        "type": "claim",
        "statement": "cooperation-contracts.md 4.2 requires a COOP-1 participant to publish actual scope at every meaningful checkpoint and before exit, and coordination.md section 7 states the deviation obligation unconditionally while qualifying only the readiness gate as COOP-2, so declared-versus-observed comparison is already partly a COOP-1 responsibility; the draft also never relates 'actual scope' to the 'observed scope' record of section 8.",
        "epistemic_status": "verified",
        "evidence": ["evidence:actual-scope-text", "evidence:intent-deviation-text"]
      },
      {
        "id": "claim:lease-exit-coupling-omitted",
        "type": "claim",
        "statement": "The COOP-1 lease carries an exit-integrity obligation beyond liveness: 4.2 requires the binding to reject release while a linked intent is nonterminal or absent a durable handoff receipt with integrity digest, and the cooperation schema conditionally requires handoff_receipt when a participantLease status is released.",
        "epistemic_status": "verified",
        "evidence": ["evidence:lease-release-text", "evidence:lease-schema-conditional"]
      },
      {
        "id": "claim:coop2-claim-unit-inconsistent",
        "type": "claim",
        "statement": "cooperation-contracts.md section 4 attaches the COOP-1 claim to a composed participant, binding, projector, checkpoint and recovery behavior and forbids a lone component from claiming it, while section 6 attaches every COOP-2 obligation to 'a COOP-2 binding' with no equivalent composition sentence, permitting a registry or analyzer alone to claim COOP-2.",
        "epistemic_status": "verified",
        "evidence": ["evidence:composition-asymmetry"]
      },
      {
        "id": "claim:coop2-binding-absent",
        "type": "claim",
        "statement": "No COOP-2 reference binding exists in the repository: there is no semantic registry implementation, selector analyzer, or integration-readiness evaluator under tools/, which coordination.md open issue 5 already records. This is a missing binding rather than a boundary defect, but it means no implementation can yet demonstrate that a responsibility placed on the COOP-2 side is implementable there.",
        "epistemic_status": "observed",
        "evidence": ["evidence:tools-semantic-scan"]
      },
      {
        "id": "claim:coop1-evidence-unmapped",
        "type": "claim",
        "statement": "The nine COOP-1 evidence scenarios of cooperation-contracts.md 4.3 and the thirty-two minimum conformance fixtures of coordination.md section 24 are not mapped to one another and section 24 carries no contract attribution, so an assessor cannot determine which fixtures discharge a COOP-1 claim. This is missing evidence rather than a boundary defect.",
        "epistemic_status": "observed",
        "evidence": ["evidence:section-attribution-scan", "evidence:binding-status-partial"]
      }
    ],
    "evidence": [
      {
        "id": "evidence:section-attribution-scan",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Per-section scan of spec/drafts/0.8.0/coordination.md counting COOP-1/COOP-2/COOP-3 occurrences under each level-2 heading: sections 1, 2, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23 and 24 return zero for all three, with attribution present only in sections 3, 4, 5, 7, 13, 18.1, 18.2, 19, 20, 25, 26 and 27.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:coop1-atomicity-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md 4.1: 'The binding MUST make the announce-and-check operation atomic with respect to other COOP-1 announce operations for the same guarded scopes' and 'A warning-only result is insufficient for a binding to claim the COOP-1 guarded-mutation guarantee.' No conditional qualifier appears in either sentence.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:coop1-validation-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md section 4 requires validation of 'workstate identity, event identity, ancestry, revisions, lifecycle transitions, pinned references, typed precondition and verification bindings, and applicable staleness rules'; 4.3 scenario 3 requires evidence that invalid precondition, verification or staleness input is excluded or blocks with a stable diagnostic.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:dependency-staleness-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 15 defines reverse-dependency staleness propagation with transitive cause retention and clearing only via type-specific revalidated, rebased or superseded transitions with fresh evidence — a distinct obligation from the record-admissibility checks required at COOP-1.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:actual-scope-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md 4.2: 'At a meaningful checkpoint and before exit, a participant MUST publish its actual scope, outcome, evidence references, unresolved work, and recommended next action through the selected binding.'",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:intent-deviation-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 7: 'If observed work expands beyond the declared scope, the writer MUST either update the intent before publishing a ready change set or record an explicit deviation. Under a COOP-2 policy, unresolved material under-declaration prevents ready.' The obligation is unconditional; only the readiness gate is qualified as COOP-2.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:lease-release-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md 4.2: 'The binding MUST reject release while an intent linked to the lease remains nonterminal or unless a durable receipt identifies an already published handoff artifact and its integrity digest.'",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:lease-schema-conditional",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "schemas/awp-cooperation-0.1.schema.json $defs.participantLease contains an allOf if/then requiring handoff_receipt when status is 'released', confirming the exit-coupling obligation is schema-enforced and not only prose.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:composition-asymmetry",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md section 4 states that a deterministic-coordination-projector component alone MUST NOT claim COOP-1 because the contract applies to the composed participant, binding, projector, checkpoint and recovery behavior; section 6 contains no equivalent sentence and phrases every COOP-2 obligation as belonging to 'a COOP-2 binding'.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:tools-semantic-scan",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Scan of tools/ for semantic-registry, observed-scope, integration-plan and dependency-staleness implementations: only awp_projector.py carries substantive semantic handling; no semantic registry, selector analyzer, or integration-readiness evaluator module exists. coordination.md open issue 5 independently records that COOP-2 needs a semantic integration binding.",
        "observed_at": "2026-09-07T15:45:00Z"
      },
      {
        "id": "evidence:binding-status-partial",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "python tools/awp_coordination.py status reports contract COOP-1 with claim_state 'partial', operational_reach 'worktree-local', and limitations including advisory enforcement with unfenced source-control writes and path-like physical scopes only, indicating the multi-participant and cross-filesystem-path evidence scenarios are the least likely to have been exercised.",
        "observed_at": "2026-09-07T15:35:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop-level-boundary-response",
        "type": "checkpoint",
        "frontier": ["evt:coop-level-boundary-response"],
        "created_at": "2026-09-07T15:52:00Z",
        "summary": "One bounded critique round returned with terminal result 'revised'. The proposed COOP-1/COOP-2 physical/semantic cut is correct and accepted subject to six normative edits: per-section contract attribution in coordination.md; removal of the 'where supported' conditional on atomic admission; separation of record-validity staleness from dependency staleness and of precondition/verification binding validation from predicate evaluation; return of self-declared actual-scope reconciliation to COOP-1 with analyzer-produced observed_scope retained at COOP-2; restatement of the COOP-1 lease as liveness plus enforced exit coupling; and a composed-claim-unit sentence in section 6. COOP-2's absent reference binding is classified as a missing binding and the unmapped 4.3-to-24 evidence relationship as missing evidence, neither being a boundary defect.",
        "recommended_next_action": {
          "action": "principal:mark decides whether to adopt decision:coop-level-boundary-revised into the 0.8.0 draft. The six edits are independent and may be taken separately; edit 1 (per-section contract attribution) is prerequisite to auditing any of the others and should land first. Continuation of this consultation past round one requires principal:mark's recorded approval.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:7d2b9e64c0a1483fb85e37d19c6a02f5:snapshot:end -->
