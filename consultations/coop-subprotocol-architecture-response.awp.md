---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 9b3e5f1a7c2d4068a1c9e7f3b5d2a604
workstate_id: urn:uuid:awp-coop-subprotocol-architecture-response-2026-09-05
frontier:
  - evt:coop-subprotocol-architecture-response
checkpoint: checkpoint:coop-subprotocol-architecture-response
generated_at: 2026-09-05T22:15:00Z
generated_digest: sha256:38bf28493f154e0896e9afef66ff76b7eee7b564f191ac1aed0f4d4fde08f5c1
---
<!-- awp:generated:start -->
# COOP work-coordination and consultation architecture — response

`actor:claude-review`'s response to `consultation:coop-subprotocol-architecture`. This was
answered COOP-0 style: the request granted no mutation authority and named no ledger, so this
capsule is the only artifact produced. Terminal outcome: **accepted** — a definite
recommendation, not a menu, with one explicit limitation and one open naming-policy question
for `principal:mark`.

## Recommendation

Split the two clusters, but not into new `contract` values. Keep `contract` as
`COOP-0` / `COOP-1` / `COOP-2` exactly as it is today, and add a `subprotocols` object to the
existing `cooperation_binding` disclosure: `work` and `consult`, each independently carrying
its own `claim_state` (`selected` / `partial` / `conformant`) from the enum the schema already
defines. Reject `COOP-1/WORK` and `COOP-1/CONSULT` as literally proposed — a slash-qualified
contract string reopens the exact "competing axes" failure this repository has already paid
for three times in one day (Coordination `C0`–`C3` versus draft `CC-0`..`CC-2`; the `CC-1` /
`COOP-1` naming collision; and the unification into one ladder at `5a30c74`, itself the fix for
the second collision). A new enumerated axis is the shape of the mistake, not an accident of
naming; an object field composes without touching the enum and degrades safely for a reader
that does not understand it yet, the same way `capabilities` and `tested_envelope` already do
in this schema.

## Verified basis for the recommendation

Read at `git:5a30c74378c0d7bc89022dff6f830dba41f07d39`, not summarized from memory:

- `schemas/awp-cooperation-0.1.schema.json`'s `binding.allOf` currently requires ALL SIX of
  `deterministic-coordination-projector`, `coordination-awareness`,
  `guarded-scope-announce-check`, `participant-leases`, `bounded-interactions`, and
  `checkpoint-handoff` together before a `COOP-1` `conformant` claim validates. Five of those
  six are safety machinery for concurrent mutation; exactly one, `bounded-interactions`, is
  reasoning-quality machinery. The schema already forces them into one bundle at the strongest
  claim level — this is the literal mechanism of the conflation the request describes.
- `conformance/matrix.md`'s own "COOP-1 default small-group contract" row states its current
  evidence gap as "deterministic projection, guarded work, bounded interaction, checkpoint,
  recovery, and fresh-entry evidence are not yet demonstrated together by one binding." That
  sentence is a direct symptom of bundling unrelated capabilities into one demonstration
  requirement: five properties about safe concurrent mutation and one property about answer
  quality do not obviously need the same binding, the same trial, or the same evidence run to
  each be independently true.
- `tools/awp_coordination.py` at `git:5a30c74378c0d7bc89022dff6f830dba41f07d39` has zero `cooperation_interaction`,
  `repeat_key`, or RFC 8785 code. `bounded-interactions` exists today only as spec text and a
  hand-assembled capsule field, while `guarded-scope-announce-check`, `participant-leases`, and
  `checkpoint-handoff` are implemented, tested (17+ tests), and have been exercised live across
  four bilateral rounds. The two clusters are not just conceptually separable — they are at
  visibly different implementation maturity today, and bundling them means a real `COOP-1`
  binding cannot currently claim `conformant` for the parts it has actually built.
- Section 3's `COOP-0` interaction paragraph ("Every `COOP-0` cooperation interaction MUST have
  a purpose, question or task, decision owner, and terminal outcome") already specifies the
  interaction vocabulary one full contract level below where guarded-scope blocking exists.
  That is internal evidence the consult cluster does not inherently depend on `COOP-1`'s guarded
  work machinery — it only borrows the same binding today for convenience, the same way this
  very response borrows none of it, because this request declared no guarded scope at all.

## Answers to the five questions

**1. Independent profiles, or one required as part of a complete `COOP-1` claim?**
Neither cleanly. `work` is `COOP-1`'s load-bearing definitional core — section 4 opens with
guarded work, sections 4.1, 4.4, 4.5, and 4.6 are almost entirely about it, and an unqualified
`COOP-1` claim should keep meaning what it already means: `subprotocols.work.claim_state ==
"conformant"` is necessary for an unqualified `COOP-1 conformant` claim. `consult` should be
optional and independently gated: a binding MAY claim `COOP-1` with `subprotocols.consult`
absent or merely `selected`, and MAY separately claim `subprotocols.consult.claim_state ==
"conformant"` as an addition, at either `COOP-0` or `COOP-1`, since consult's baseline
vocabulary already lives at `COOP-0`.

**2. Relationship to `COOP-0` / `COOP-1` / `COOP-2`?** `work` is intrinsically `COOP-1`-and-up
(`COOP-0` explicitly makes no active-coordination guarantee, so `work` cannot reach
`conformant` below `COOP-1`); `COOP-2` extends `work` with the semantic-awareness,
integration-assurance, and live-enforcement bundles it already defines in section 5 and in
Coordination section 3 — no change needed there. `consult` can be declared at `COOP-0` or
`COOP-1` and does not need a `COOP-2` tier yet; nothing in this repository's four live rounds
showed a consult need beyond what section 4.2's bounded two-participant loop already covers, and
inventing a `COOP-2`-consult tier now would be manufacturing a ladder rung ahead of evidence,
the same mistake this split is meant to fix in the other direction.

**3. Declaration and conformance-claim syntax?** Add to the `binding` schema:
`"subprotocols": {"type": "object", "properties": {"work": {"$ref": "#/$defs/subprotocolClaim"},
"consult": {"$ref": "#/$defs/subprotocolClaim"}}}` with `subprotocolClaim` reusing the existing
`claim_state` enum. Move the current six-item `allOf.contains` gate so a `COOP-1` `conformant`
claim requires `subprotocols.work.claim_state == "conformant"` (backed by
`deterministic-coordination-projector`, `coordination-awareness`, `guarded-scope-announce-check`,
`participant-leases`, `checkpoint-handoff`) and add a second, independent `allOf` branch:
`subprotocols.consult.claim_state == "conformant"` requires `bounded-interactions` plus a
declared `interaction_policy.enforcement != "not-implemented"`. `contract` and its enum do not
change. This is unambiguous to a simple model: read one enum for the ladder rung, one enum for
the claim strength, and now one small nested object for which of two named clusters that
strength applies to — three lookups, no new pattern-matching, no combinatorial label strings.

**4. Invariants against implied authority, forced participation, or runaway loops?**
Three, one already present and two the split newly requires:
- Already present and correct: section 4.2's rule that an interaction "MUST NOT silently
  authorize a guarded mutation" — keep this verbatim; it is the load-bearing anti-authority
  invariant and does not need to change when `consult` becomes independently declarable.
- New: a `work` lease MUST NOT be interpreted as consent to be interrupted for consultation, and
  a binding MUST NOT require a live lease as a precondition for initiating or responding to a
  `consult` interaction. Today's section 4.1 frames leases as required "before guarded work"
  and section 4.2 as something that MAY happen "while performing compatible work," which reads
  as implicitly lease-scoped. Once `consult` is independently claimable, a stateless
  reviewer with no scope of its own — exactly the role this response is playing right now, with
  no lease entered — must be explicitly a valid `consult` participant, not an edge case.
- New: the section 4.3 loop budget (`max_rounds`, `max_tool_calls`, `on_limit`) applies to
  `cooperation_interaction` records only and MUST NOT be conflated with a lease's `ttl_seconds`
  or an intent's retry behavior. The two are adjacent generic-sounding "budget" concepts today;
  splitting the subprotocols is the right moment to say explicitly that they are unrelated
  mechanisms so a simple model does not reach for one when it means the other.

**5. Minimal normative changes?**
Spec: one new cooperation-contracts.md subsection defining `work` and `consult` as the two
capability clusters with a table mapping each existing numbered requirement to one cluster, plus
the three invariants above. Schema: the `subprotocols` object and the two independent `allOf`
gates described in question 3; no change to `contract`, `interaction`, `policy`, or
`participantLease`. Fixtures: replace the single combined `cooperation-0.1-binding` fixture with
three — work-conformant/consult-absent, consult-conformant-at-COOP-0, and one negative fixture
where a `COOP-1` `conformant` claim omits `subprotocols.work` — and split
`conformance/matrix.md`'s one combined "COOP-1 default small-group contract" row into a `work`
row and a `consult` row, since the combined row's own evidence-gap sentence is the symptom this
split is meant to resolve. Adapter: no change required for the split label itself, but the
adapter's `status` output still does not emit the schema's `cooperation_binding` shape at all —
that is a pre-existing, separately tracked gap — and the new `subprotocols` field belongs on
that emission once it exists, not bolted onto today's ad hoc `binding_identity` /
`binding_observation` keys. AGENTS.md: one added sentence in the COOP-1-aligned workflow section
naming the lease/intent steps as `work` and the interaction step as `consult`, since that file is
the actual on-ramp a new agent reads first.

## Limitation

No live evidence yet exists for a lease-less `consult` interaction — every interaction round run
in this repository so far, including this response, either entered a lease first as ceremony or,
in this case, was answered by a plain `consultation` record because none was requested. Question
4's second invariant is argued from the specification text and this response's own shape, not
from a trial where a genuine stateless participant answered without ever touching the ledger.
That evidence gap is worth naming as a scenario 11 candidate once the split lands, not something
this response can close today.

## Remaining disagreement

None of substance. Open for `principal:mark`, not disagreement: whether an unqualified `COOP-1`
claim should continue to require `work` `conformant` (this response's recommendation) or whether
the label itself should require nothing and every claim should state its subprotocols
explicitly — a naming-policy choice rather than a technical one.
<!-- awp:generated:end -->

<!-- awp:9b3e5f1a7c2d4068a1c9e7f3b5d2a604:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-subprotocol-architecture-response-2026-09-05",
  "title": "COOP work-coordination and consultation architecture — response",
  "created_at": "2026-09-05T22:15:00Z",
  "created_by": "actor:claude-review",
  "completeness": "portable",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.8.0",
      "required": true
    },
    {
      "id": "urn:awp:capsule",
      "version": "0.5.0",
      "required": true
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.5.0",
      "required": true
    },
    {
      "id": "urn:awp:cooperation",
      "version": "0.1.0",
      "required": true
    }
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:9b3e5f1a7c2d4068a1c9e7f3b5d2a604:manifest:end -->

<!-- awp:9b3e5f1a7c2d4068a1c9e7f3b5d2a604:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-subprotocol-architecture-response-2026-09-05",
  "frontier": [
    "evt:coop-subprotocol-architecture-response"
  ],
  "generated_at": "2026-09-05T22:15:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop-subprotocol-architecture",
        "type": "consultation",
        "revision": 2,
        "question": "Should AWP separate collision-resistant work coordination from bounded cross-agent consultation into independently configurable COOP profiles, and what is the smallest robust architecture?",
        "status": "answered",
        "requested_action": "Provide one independent architecture review answering the five numbered questions in the briefing. Return a response capsule. Do not modify protocol sources, commit, or make external changes.",
        "context": {
          "draft_version": "0.8.0",
          "base_revision": "git:5a30c74378c0d7bc89022dff6f830dba41f07d39",
          "decision_owner": "principal:mark"
        },
        "read_first": [
          "decision:subprotocol-split",
          "claim:six-capability-bundling",
          "claim:consult-baseline-already-at-coop0"
        ],
        "desired_output": "One independent architecture review with a definite recommendation and any serious flaw identified.",
        "answer": "Split into work and consult clusters, but as an object field (subprotocols.work / subprotocols.consult, each with the existing claim_state enum) inside the current cooperation_binding disclosure, not as new contract enum values such as COOP-1/WORK or COOP-1/CONSULT. work stays load-bearing to an unqualified COOP-1 claim; consult becomes independently declarable at COOP-0 or COOP-1. No serious flaw found against the underlying split; the slash-qualified naming as literally proposed is rejected because it reopens the competing-axes failure this repository has already paid for three times.",
        "responded_by": "actor:claude-review",
        "responded_at": "2026-09-05T22:15:00Z",
        "response_evidence": [
          "evidence:schema-bundling",
          "evidence:matrix-gap",
          "evidence:adapter-interaction-absent",
          "evidence:coop0-interaction-baseline"
        ],
        "disposition": "accepted"
      }
    ],
    "decisions": [
      {
        "id": "decision:subprotocol-split",
        "type": "decision",
        "question": "How should work coordination and consultation be declared independently without recreating a competing conformance axis?",
        "status": "proposed",
        "choice": "Add subprotocols.work and subprotocols.consult (each reusing the existing claim_state enum) to the cooperation_binding schema; keep contract as COOP-0/COOP-1/COOP-2 unchanged; require subprotocols.work conformant for an unqualified COOP-1 conformant claim; allow subprotocols.consult to be claimed independently at COOP-0 or COOP-1.",
        "decided_by": "actor:claude-review",
        "requires_authority": "principal:mark"
      }
    ],
    "claims": [
      {
        "id": "claim:six-capability-bundling",
        "type": "claim",
        "statement": "awp-cooperation-0.1.schema.json's binding.allOf requires all six of deterministic-coordination-projector, coordination-awareness, guarded-scope-announce-check, participant-leases, bounded-interactions, and checkpoint-handoff together for a COOP-1 conformant claim, bundling five safety-of-mutation capabilities with one answer-quality capability at the strongest claim level.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:schema-bundling"
        ]
      },
      {
        "id": "claim:matrix-gap-is-symptom",
        "type": "claim",
        "statement": "conformance/matrix.md's COOP-1 evidence row states that deterministic projection, guarded work, bounded interaction, checkpoint, recovery, and fresh-entry evidence are not yet demonstrated together by one binding, which is a direct symptom of requiring unrelated capabilities to be evidenced jointly.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:matrix-gap"
        ]
      },
      {
        "id": "claim:adapter-interaction-absent",
        "type": "claim",
        "statement": "tools/awp_coordination.py at git:5a30c74 contains no cooperation_interaction, repeat_key, or RFC 8785 implementation, while guarded-scope-announce-check, participant-leases, and checkpoint-handoff are implemented and tested, showing the two clusters are at visibly different implementation maturity today.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:adapter-interaction-absent"
        ]
      },
      {
        "id": "claim:consult-baseline-already-at-coop0",
        "type": "claim",
        "statement": "Section 3 (COOP-0) already requires every cooperation interaction to have a purpose, question or task, decision owner, and terminal outcome, one full contract level below where guarded-scope blocking exists, showing the consult baseline does not inherently depend on COOP-1's guarded-work machinery.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop0-interaction-baseline"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:schema-bundling",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "Read schemas/awp-cooperation-0.1.schema.json binding.allOf at git:5a30c74: the COOP-1-conformant branch's capabilities.allOf requires contains on all six named capabilities together.",
        "observed_at": "2026-09-05T22:15:00Z"
      },
      {
        "id": "evidence:matrix-gap",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "Read conformance/matrix.md's 'COOP-1 default small-group contract' row at git:5a30c74: current-evidence column states the six behaviors are not yet demonstrated together by one binding.",
        "observed_at": "2026-09-05T22:15:00Z"
      },
      {
        "id": "evidence:adapter-interaction-absent",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "grep of tools/awp_coordination.py at git:5a30c74 for interaction/repeat_key/rfc8785 symbols returns none; enter_lease, resolve_overlap, and checkpoint functions exist and are covered by tests.",
        "observed_at": "2026-09-05T22:15:00Z"
      },
      {
        "id": "evidence:coop0-interaction-baseline",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "Read spec/drafts/0.8.0/cooperation-contracts.md section 3 at git:5a30c74: the COOP-0 interaction requirement (purpose, question or task, decision owner, terminal outcome) is stated before section 4's guarded-work machinery.",
        "observed_at": "2026-09-05T22:15:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop-subprotocol-architecture-response",
        "type": "checkpoint",
        "frontier": [
          "evt:coop-subprotocol-architecture-response"
        ],
        "created_at": "2026-09-05T22:15:00Z",
        "summary": "Architecture review answered: split work and consult as an object field on the existing cooperation_binding disclosure, not as new contract enum values; work stays load-bearing to an unqualified COOP-1 claim, consult becomes independently declarable at COOP-0 or COOP-1. No serious flaw found in the underlying split; the literal COOP-1/WORK and COOP-1/CONSULT naming is rejected.",
        "recommended_next_action": {
          "action": "principal:mark decides whether an unqualified COOP-1 claim should keep requiring subprotocols.work conformant, then the spec/schema/fixture changes in question 5 can be scheduled as the next slice.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:9b3e5f1a7c2d4068a1c9e7f3b5d2a604:snapshot:end -->
