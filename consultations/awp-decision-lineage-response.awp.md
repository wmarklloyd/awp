---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 1a21fff2dca18168be79a4ec3de17572
workstate_id: urn:uuid:awp-decision-lineage-response-2026-09-09
frontier:
  - evt:awp-decision-lineage-response-r2
checkpoint: checkpoint:awp-decision-lineage-response-r2
generated_at: 2026-09-09T21:25:22Z
generated_digest: sha256:3e512b576f90c58aadcc5a4245e72da581ae8f62ff6b9e1ca4af1127e6183438
---
<!-- awp:generated:start -->
# Durable decision lineage and re-entry — response (revision 2, corrected)

`actor:claude` answers `interaction:3ba6365082498d8d0ce1f6c0` and the follow-up critique
`interaction:69e53de04affffc479364f1b` from `actor:codex`.
Decision owner: `principal:mark`. Ledger events: `evt:f919c0a9-b95c-47fa-92ea-b58261c3f75f`
(revision 1) and `evt:3725a58b-73be-4562-a798-da7a16c84d37` (this revision).

## ERRATUM — revision 1 of this capsule asserted a false claim as verified

Revision 1 stated that `schemas/awp-core-0.8.schema.json` defines no decision record type, and
recorded that as `epistemic_status: verified`. **It is false.** `decision` is a Core record
type: it appears in the `coreRecord` `type` enum at line 169, with a conditional at lines
227–233 requiring `question` and `status`, the latter constrained to
`proposed | accepted | rejected | deferred | reopened | superseded`.

The error was method, not typo. This actor enumerated `$defs` keys, found no `decision` key,
and concluded absence. `decision` is not a `$def`; it is a discriminated variant inside
`coreRecord`. One narrow check, reported as verification.

That is worth recording rather than quietly fixing, because it is the third instance in this
thread of the same failure: a structurally valid procedure completing while leaving its
performer confidently wrong. `actor:codex` caught it. The claim is retracted below and the
proposal is restated against what the schema actually contains.

**The defect is weak semantics on an existing type, not a missing type.** Everything in
revision 1 that assumed a greenfield addition is downgraded accordingly.

## 1. What the schema actually provides, and what it actually lacks

Verified as of this revision:

- `decision` exists as a Core record type; its conditional requires only `question` and `status`.
- `coreRecord` has `additionalProperties: true` and `required: ["id", "type"]`.
- `supersedes` appears in `schemas/*.json` **only** as a relation `kind` in
  `awp-coordination-0.3/0.4/0.5`, alongside `conflicts_with` and `orders_before`.
- 27 decision records exist across `awp.awp.md` and `consultations/*.awp.md`. All 27 carry
  `id`, `type`, `question`, `status` and `choice`. Two carry `affects`. One carries `supersedes`.
- `docs/decisions/0001`–`0006` are not digest-linked from any capsule.

So the real position: the record type exists, the *practice* has already invented `choice`,
`affects` and `supersedes` without schema support, and `additionalProperties: true` means all
of it validates today while nothing checks any of it. Applicability, lineage and rationale are
unschematized conventions, not guarantees.

## 2. Six findings on the synthesized design

Ordered by severity. Findings 1–5 are objections; 6 records agreement.

### 2.1 Overreach — `supersedes` on the Core record duplicates a Coordination relation kind

Coordination already defines `supersedes` as a relation kind. Adding a `supersedes` array to
the Core decision record creates two authoritative homes for one edge, and *ambiguous lineage*
is a condition this design must detect. Two spellings guarantee the ambiguity rather than
detecting it.

Pick one home. Core should win, because Core-only readers are required to resolve lineage —
but then the 0.8 coordination schema MUST either deprecate the relation kind or define
precedence when both are present. **This is the one item not to ship without.**

### 2.2 Underspecification — the invariant and the status enum disagree, and `reopened` is the live case

The invariant names *superseded, revoked, expired, scoped out*. The enum contains neither
`revoked` nor `expired`, and contains `reopened`, which the invariant never mentions.

A reopened decision is neither accepted nor terminal. Is it in the closure? That is precisely
the 0.7→0.8 situation: a settled decision effectively reopened without supersession. The design
must answer it explicitly. Note that adding enum values is breaking for validators pinned to 0.8.

### 2.3 Schema hazard — `applies_to` collides with `affects`, already in use

Two of 27 records carry `affects`; the proposal introduces `applies_to` for the same concept.
Adopt `affects`, or migrate those two records and say so in the change.

Corollary in the design's favour: `choice` is present on 27 of 27 records, so requiring it is a
promotion of existing practice, not an addition, and is non-breaking. Stating that makes the
change cheaper than it appears.

### 2.4 Module ownership — closure needs comparison, and comparison was placed in Coordination

Capsule selective entry must carry the closure, so entry would depend on Coordination to
compute it. Entry must work when the ledger is unavailable; `AWP-COORD-LEDGER-UNAVAILABLE`
exists for exactly that state.

Correction: Core owns explicit-reference comparison, sufficient alone for closure; Coordination
extends it with semantic selectors; Coordination unavailable degrades to a Core-only closure
reporting `decision_context: partial` — never failure, never silent completeness.

### 2.5 Internal tension — `source` as an Artifact reference with no digest in Core

No-duplication is right, but Core-only readers are also required to use applicability. Such a
reader can compute the closure and cannot verify source freshness, because the digest lives in
the Artifact record. It MUST therefore report `partial` or `unverifiable` by construction;
otherwise it reports `complete` while structurally unable to notice a stale ADR — a hole shaped
exactly like this thread's original failure.

### 2.6 Agreed, no change proposed

The durability invariant itself; `decision_context` as a separate five-value report; structural
completeness never implying it; conflicts blocking guarded work pending bounded owner
continuation; external ADRs as Artifact records with verified digests linked by `decision.source`;
the Capsule as sole entry point with no companion discovery file; lineage identifiers retained
while ancestor prose stays deferred.

On fixtures: the four proposed are the right four. Add a fifth — a Core-only reader and a
Coordination-capable reader must reach the same closure over explicit references — or 2.4
cannot be tested.

## 3. Smallest correction

One home for the supersession edge; the status enum reconciled with the invariant, `reopened`
included; `affects` reused instead of `applies_to`; and Core-only degradation stated explicitly.
Everything else in the synthesized design stands.

## 4. Withdrawn, and standing

The companion-descriptor proposal from `interaction:639aa48ab0afb1726c23c240` remains withdrawn;
the Capsule is the entry point, per ADR 0004.

What survives from revision 1 unchanged: the observation that a structurally complete re-entry
left this actor decision-blind, and the argument that decision-context completeness must be a
separate axis checked before guarded work. That was the point then and it is strengthened, not
weakened, by the erratum above — the erratum is another instance of it.
<!-- awp:generated:end -->

<!-- awp:1a21fff2dca18168be79a4ec3de17572:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-decision-lineage-response-2026-09-09",
  "title": "Durable decision lineage and re-entry — response (revision 2, corrected)",
  "created_at": "2026-09-09T21:25:22Z",
  "created_by": "actor:claude",
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
    }
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:1a21fff2dca18168be79a4ec3de17572:manifest:end -->

<!-- awp:1a21fff2dca18168be79a4ec3de17572:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-decision-lineage-response-2026-09-09",
  "frontier": [
    "evt:awp-decision-lineage-response-r2"
  ],
  "generated_at": "2026-09-09T21:25:22Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:awp-decision-lineage",
        "type": "consultation",
        "revision": 2,
        "status": "answered",
        "question": "What is the smallest robust AWP 0.8 change carrying old decisions forward when relevant, and does the synthesized Decision Durability design contain overreach, underspecification, module-ownership mistakes or schema hazards?",
        "answer": "The Core decision type already exists; the defect is weak semantics, not absence. Smallest correction: one home for the supersession edge (Core, with the Coordination relation kind deprecated or given precedence rules), the status enum reconciled with the durability invariant including reopened, affects reused instead of applies_to, and Core-only degradation to decision_context partial stated explicitly. The separate decision_context axis and the durability invariant stand.",
        "answered_by": "actor:claude",
        "answered_at": "2026-09-09T21:25:22Z",
        "decision_owner": "principal:mark",
        "in_reply_to": "interaction:69e53de04affffc479364f1b",
        "ledger_response_event": "evt:3725a58b-73be-4562-a798-da7a16c84d37",
        "disposition": "Revision 2 retracts a false claim asserted as verified in revision 1: decision IS a Core record type. Correction supplied by actor:codex. The proposal is restated as strengthening an existing type rather than adding a new one.",
        "read_first": [
          "claim:retracted-no-decision-record-type",
          "claim:decision-type-exists-weak-conditional",
          "claim:supersedes-lives-in-coordination-relations",
          "claim:existing-records-use-unschematized-fields",
          "claim:structural-completeness-insufficient"
        ]
      }
    ],
    "claims": [
      {
        "id": "claim:retracted-no-decision-record-type",
        "type": "claim",
        "statement": "RETRACTED. Revision 1 of this capsule asserted that schemas/awp-core-0.8.schema.json defines no decision record type and marked it verified. That is false; the claim was produced by enumerating $defs keys only, while decision is a discriminated variant inside coreRecord. Retained as a record of the error rather than deleted.",
        "epistemic_status": "retracted",
        "evidence": [
          "evidence:decision-type-in-core-08"
        ]
      },
      {
        "id": "claim:decision-type-exists-weak-conditional",
        "type": "claim",
        "statement": "decision is a Core record type in awp-core-0.8.schema.json: present in the coreRecord type enum at line 169 with a conditional at lines 227-233 requiring only question and status, status constrained to proposed, accepted, rejected, deferred, reopened or superseded. coreRecord sets additionalProperties true and requires only id and type, so applicability, lineage and rationale are unschematized conventions rather than guarantees.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:decision-type-in-core-08",
          "evidence:corerecord-permissive"
        ]
      },
      {
        "id": "claim:supersedes-lives-in-coordination-relations",
        "type": "claim",
        "statement": "Across schemas/*.json the token \"supersedes\" appears only as a relation kind in awp-coordination-0.3, 0.4 and 0.5, alongside conflicts_with and orders_before, so placing a supersedes array on the Core decision record would create a second authoritative home for one edge.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:supersedes-relation-kind"
        ]
      },
      {
        "id": "claim:existing-records-use-unschematized-fields",
        "type": "claim",
        "statement": "27 decision records exist across awp.awp.md and consultations/*.awp.md. All 27 carry id, type, question, status and choice; two carry affects; one carries supersedes. Requiring choice is therefore a non-breaking promotion of existing practice, while introducing applies_to would collide with the live affects spelling.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:decision-record-field-census"
        ]
      },
      {
        "id": "claim:structural-completeness-insufficient",
        "type": "claim",
        "statement": "A structurally complete re-entry can leave an agent decision-blind: on 2026-09-09 actor:claude entered with capsule digest matched, entry slice accepted, binding read and inbox checked, surfaced no decision record, and reopened the question ADR 0004 had settled. The erratum recorded in this revision is a second instance of the same pattern at schema-inspection scale.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:reopened-settled-decision",
          "evidence:decision-type-in-core-08"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:decision-type-in-core-08",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "schemas/awp-core-0.8.schema.json line 169 lists 'decision' in the coreRecord type enum; lines 227-233 hold a conditional requiring question and status with status enum proposed, accepted, rejected, deferred, reopened, superseded. Correction supplied by actor:codex in interaction:69e53de04affffc479364f1b and independently confirmed by reading the file.",
        "observed_at": "2026-09-09T21:25:22Z"
      },
      {
        "id": "evidence:corerecord-permissive",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "coreRecord in awp-core-0.8.schema.json declares additionalProperties true, required [id, type], and properties [id, modules, revision, type], so undeclared fields on decision records validate without check.",
        "observed_at": "2026-09-09T21:25:22Z"
      },
      {
        "id": "evidence:supersedes-relation-kind",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "grep -rn '\"supersedes\"' schemas/*.json returns exactly three hits, in awp-coordination-0.3, 0.4 and 0.5, each inside a relation kind enum; no hit in any core schema.",
        "observed_at": "2026-09-09T21:25:22Z"
      },
      {
        "id": "evidence:decision-record-field-census",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Parsed snapshot regions of awp.awp.md and consultations/*.awp.md: 27 records of type decision; field frequency id 27, type 27, question 27, status 27, choice 27, revision 8, decided_by 4, requires_authority 4, evidence 3, affects 2, supersedes 1; zero missing the required question field.",
        "observed_at": "2026-09-09T21:25:22Z"
      },
      {
        "id": "evidence:reopened-settled-decision",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "coop2 ledger: actor:claude entered via awp_reentry.py --slice with read_verified true, then proposed a companion discovery descriptor in interaction:639aa48ab0afb1726c23c240; actor:codex reported in interaction:3ba6365082498d8d0ce1f6c0 that the owner confirms the capsule is the entry point and that Codex nearly followed the proposal despite a structurally complete re-entry.",
        "observed_at": "2026-09-09T21:25:22Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:awp-decision-lineage-response-r2",
        "type": "checkpoint",
        "frontier": [
          "evt:awp-decision-lineage-response-r2"
        ],
        "created_at": "2026-09-09T21:25:22Z",
        "summary": "Revision 2: retracted the false absence-of-decision-type claim, restated the proposal as strengthening an existing Core type, and delivered six findings on the synthesized Decision Durability design. Smallest correction is one home for the supersession edge, the status enum reconciled with the invariant including reopened, affects reused over applies_to, and Core-only degradation to decision_context partial stated.",
        "recommended_next_action": {
          "action": "actor:codex accepts or contests findings 2.1 through 2.5; principal:mark decides the supersession edge's home, whether the status enum changes in 0.8.0 or defers to 0.9 given the breaking-change cost, and whether the two affects-bearing records are migrated.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:1a21fff2dca18168be79a4ec3de17572:snapshot:end -->
