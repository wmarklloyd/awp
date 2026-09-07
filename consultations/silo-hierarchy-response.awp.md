---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: e35c8a17d94b426f9a02fd6b81c47e93
workstate_id: urn:uuid:awp-silo-hierarchy-response-2026-09-07
frontier:
  - evt:silo-hierarchy-response
checkpoint: checkpoint:silo-hierarchy-response
generated_at: 2026-09-07T16:34:00Z
generated_digest: sha256:2bbb4276d0d7bcd49eaa84647f7ea17460b9ac9ac3be2f0df94a32cad6d0b7e2
---
<!-- awp:generated:start -->
# Silo hierarchy and canonical publication — response

`actor:claude-review`'s response to `consultation:silo-hierarchy`, one bounded critique round
under `max_rounds: 1`. Answered COOP-0 style: no protocol source, schema, or workstate file was
modified, no ledger lease was entered, and no guarded intent was announced. This capsule is the
only artifact produced. Continuation past this round requires `principal:mark`'s recorded
approval.

Terminal outcome: **revised**. Hierarchical immutable-base silos are a sound protocol model and
I found no argument against the hierarchy or against immutable derivation. Two changes are
structural rather than cosmetic: the feature should be re-based onto the fork mechanism the
family already defines instead of introduced as a new primitive, and promotion needs a
causal-closure requirement it currently lacks. Six further hazards follow, then a minimal
normative data model, the requested boundaries, and the specification/implementation/evidence
split.

## H1 — Silos are forks, and forks are already a Core invariant

`core.md` §3 states it at family level: "Forking creates a new workstate ID and records the
parent workstate and parent frontier." `synchronization.md` §5 gives the record — parent
workstate ID, parent frontier, fork event, reason or intent, inherited module declarations —
and draws the line the silo proposal also needs: "Copying or repackaging without divergent
identity is not a fork," and "Concurrent replicas of the same workstate retain one workstate
ID."

A silo has its own capsule, participants, and lifecycle, and therefore its own workstate ID. By
the family's own definition it *is* a fork. The proposal's genuine additions are three: the
parent **capsule digest** (§5 pins only the frontier, which fixes semantic state but not the
representation the child was derived from — a real gap worth closing), the governance overlay,
and promotion.

The draft already carries three divergence concepts — fork, branch, and replica — with
different rules and different owning modules. Introducing a fourth with its own derivation
record would leave four mechanisms answering overlapping questions, in a document family that
does not yet consistently attribute its existing mechanisms to contract levels. Fixing that
attribution is already outstanding work.

**Recommendation.** Define Silo as a *profile* composed from mechanisms that exist: a
Synchronization §5 fork for derivation and identity, Capsule §3.2 canonical maintenance for
publication, and exactly one new record type for promotion. Extend the §5 fork record with the
optional `parent_capsule_digest` the silo model needs, rather than defining a parallel
derivation record. This keeps one answer to "how did this workstate come to exist".

## H2 — Partial promotion breaks causal closure; this is the model's missing central rule

Promotion of "selected results" is a cherry-pick across a divergence boundary, and the draft
currently has no rule for it. `synchronization.md` §6 governs *merging tips* — mechanical merge
unions events by ID and must not silently apply last-write-wins to authority, constraints,
accepted decisions, incompatible record revisions, contradictory verified claims, artifact
versions, or module invariants. Promotion is a different operation: a proper subset of one
branch applied to another.

The failure is concrete. Promote record `X` whose pinned reference depends on record `Y` that
was not selected, and canonical projection resolves a dangling pinned reference and emits
`AWP-COORD-MISSING-DEPENDENCY`. Worse, the promotion can appear to succeed — the capsule
replaces cleanly, the receipt is issued, and the defect surfaces only at the next projection or
the next participant's fresh entry.

**Requirement.** A promotion set MUST be causally closed over the pinned references of its
members, evaluated against the target's frontier at promotion time. A promotion whose closure
is incomplete MUST either extend the set to include the missing records, re-derive the affected
references against the target and record that re-derivation as evidence, or be rejected with a
stable diagnostic. Silent partial promotion MUST NOT be permitted. I would put this ahead of
every other silo requirement; without it the feature can corrupt canonical state through its
intended happy path.

## H3 — Silo coordination isolation plus a shared worktree is a collision hole

`cooperation-contracts.md` §4.1 requires the COOP-1 binding identity's `project_id` to derive
from repository-intrinsic state and explicitly not from a filesystem path or mount location,
and it forbids merging records across store identities: "A participant MUST NOT merge records
from different store identifiers into one work decision; it MUST select one declared binding or
return `blocked`."

Apply that to a silo with its own coordination binding in the same repository. `project_id` is
shared, because it is repository-intrinsic. `workstate_id` and `store_id` differ. The
specification therefore correctly isolates the two bindings — and that isolation is exactly the
hazard. A participant working in the silo and a participant working on canonical state, in the
same worktree, each hold a valid COOP-1 binding, each obey its returned decisions, and neither
can see the other's guarded scopes. Both proceed. Both write the same file. Every rule was
followed.

This is the sharpest coordination hazard in the proposal and it is invisible from inside either
binding.

**Requirement.** One of two rules, and I recommend the first for COOP-1: a silo that performs
guarded work MUST occupy a distinct physical work location from its parent and from canonical
state, and the silo record MUST declare that location; or, where a shared location is
unavoidable, silo bindings MUST publish their guarded scopes to the canonical binding as
cross-binding `informational` claims and MUST disclose that cross-binding comparison is outside
the COOP-1 guarded-mutation guarantee.

## H4 — Inherited-record staleness does not propagate across a derivation boundary

Immutable derivation is the right choice; it is what makes child state reproducible. Its
consequence is that a child can hold an inherited constraint, accepted decision, or verified
claim that the parent has since revised or revoked, with nothing marking it. `coordination.md`
§15's reverse-dependency staleness propagates within a workstate; there is no defined
propagation across a fork boundary, and under immutable derivation there must not be one.

The exposure is not during silo work — that is the point of isolation — but at promotion, when
the child's results re-enter a state that has moved.

**Requirement.** `inherited_records` MUST carry the parent revision each was pinned at.
Promotion MUST re-resolve every inherited pin against the target's current frontier and record
the result as a divergence observation identifying each pin that moved, was superseded, or
became unresolvable. A moved pin underneath a promoted record MUST block promotion pending an
explicit decision-owner disposition. Divergence observation belongs in the promotion receipt,
not in the silo record, because it is only meaningful at a moment in time.

## H5 — No lifecycle, and no rule for orphans

Every other AWP record family with meaningful state carries an explicit lifecycle table with
required transition conditions and named terminal states — intents, overlaps, negotiations,
integrations, leases. Silos are proposed with none. The gap that will actually bite is the
orphan case: a parent silo reaching a terminal state while live children still derive from it.

**Recommendation.** States `active`, `promoted`, `abandoned`, `superseded`, and `orphaned`, with
`promoted`, `abandoned` and `superseded` terminal. Terminating a parent MUST NOT implicitly
terminate its children — that would destroy work the parent's owner does not own. A child whose
parent has become terminal MUST record `orphaned` and MUST re-anchor to canonical state, or to
a surviving ancestor, before any promotion. An `orphaned` silo retains its immutable base; the
base does not become invalid merely because the parent's lifecycle ended.

## H6 — The three-role separation conflates a COOP-1 mechanism with a COOP-3 guarantee

"Canonical publisher" is doing two jobs that belong at different contract levels.

As a **serializer**, it is already specified and achievable at COOP-1. `capsule.md` §3.2
requires a checkpoint request carrying an idempotency key, expected whole-capsule digest,
expected generated-region digest, expected semantic frontier, proposed frontier, and
disposition, with mismatch producing `stale_base` rather than last-write-wins;
`synchronization.md` §9.1 requires a deployment with one canonical capsule to identify how
projection ownership is serialized, and explicitly states that "Projection ownership controls
representation updates only; it does not grant authority over project changes."

As an **authority gate** — the role implied by "approved root-capsule changes" and by delegated
component stewards approving limited promotions — it requires authenticated actors bound to
principals and a protected mutation path, which are COOP-3 guarantees.

**Requirement.** State the split explicitly. Canonical publication serialization is COOP-1 and
MUST reuse the §3.2 compare-and-swap rather than defining a second mechanism. Enforced
role separation — that only the canonical publisher can write canonical state, and that a
steward's delegated approval is authentic — is COOP-3, and at COOP-1 these roles are advisory
labels that MUST be disclosed as unenforced. `synchronization.md` §9.1's sentence is the model
to follow.

## H7 — Depth is unbounded and skipped ancestors are unaccounted

A promotion from a depth-N child either walks N−1 intermediate promotions or goes directly to
canonical. Direct promotion is the one people will use, and it silently invalidates every
skipped ancestor's base: the intermediate silos still declare a parent digest and frontier that
no longer describes what canonical contains.

**Recommendation.** Permit direct promotion to canonical from any depth, but require the
promotion receipt to name every bypassed ancestor, and require each bypassed ancestor to record
a divergence observation against its own declared base. A declared maximum depth is a weaker
alternative and I do not recommend it — it constrains users without addressing the actual
defect.

## H8 — "Promotion" collides with the family's central invariant (editorial, but load-bearing)

`coordination.md` closes with the essential invariant: "No actor, record, message, clean merge,
or passing claim may silently **promote** asserted coordination into observed fact, verified
compatibility, or external authority." Fixture 32 uses the word the same way: "authenticated
presence accepted without promoting it to mutation authority." In the current family,
"promote" names the unwarranted elevation the specification exists to prevent.

The silo model would make promotion a first-class legitimate operation with its own receipt. A
reader will meet both senses within one document family.

**Recommendation.** Either name the operation something unambiguous — `canonical_publication`
or `adoption` are both free — or, if `promotion` is kept, define it in Section 2 terms
explicitly as the receipted, non-silent, decision-owner-approved form, and adjust the closing
invariant to say "silently promote" cannot occur *except* through a recorded promotion receipt.
Leaving both senses undefined in the same family is the outcome to avoid.

## Minimal normative data model

Two record types, both composed from existing mechanisms. Field names are illustrative; the
requirement is the content.

**Silo** — a Synchronization §5 fork with governance fields:

```
id, type: silo, module, revision, status
workstate_id                       own identity, distinct per Core section 3
derivation:
  parent_kind                      canonical | silo
  parent_workstate_id
  parent_frontier                  Sync section 5
  parent_capsule_digest            NEW: whole-capsule and generated-region digests
  created_at_checkpoint
owner                              silo owner; advisory below COOP-3
purpose
work_location:
  kind                             worktree | none
  path                             required when kind is worktree; see H3
coordination_binding:
  store_id                         or absent for a planning-only silo
inherited_records[]:
  record_id, parent_revision       pinned; see H4
overrides[]                        record ids the silo redefines
promotion_policy:
  decision_owner, permitted_targets
```

**Promotion receipt** — the new record; everything else reuses Capsule §3.2:

```
id, type: promotion_receipt, module, revision
source_workstate_id
target                             canonical | parent silo workstate id
bypassed_ancestors[]               H7
promoted_record_ids[]
causal_closure                     complete | extended | re-derived | rejected   H2
closure_evidence[]                 records added or references re-derived
divergence_observation[]:          H4
  inherited_record_id, pinned_revision, current_revision, disposition
target_frontier_before, target_frontier_after
target_capsule_digest_before, target_capsule_digest_after
approved_by, approval_evidence     advisory below COOP-3   H6
publisher, publication_status
```

A silo that performs no guarded work needs neither `work_location.path` nor
`coordination_binding`; a planning-only silo is the cheap common case and the model should not
tax it.

## Requested boundaries

| Concern | Canonical state | Parent silo | Child silo | Git worktree |
|---|---|---|---|---|
| Identity | project workstate ID | own workstate ID | own workstate ID | none; not a workstate |
| Divergence kind | — | semantic | semantic | physical |
| Base | — | canonical frontier + digest | parent frontier + digest | working revision |
| Authority to publish canonical | decision owner via publisher | none | none | none |
| Coordination store | canonical binding | own or none | own or none | not a binding |
| Lifecycle | continuous | H5 states | H5 states | Git-owned |

Silo and worktree are orthogonal: one is divergence of *meaning*, the other of *location*. The
specification should say so plainly and then constrain the cardinality. Silo-to-worktree 1:1 is
recommended; 1:0 is valid for a planning-only silo; many-silos-to-one-worktree MUST be rejected
for guarded work per H3. A Git branch is neither — `coordination.md` already establishes that a
clean source-control merge is not proof of compatibility, and a branch carries no workstate
identity, no participants, and no lifecycle.

## Specification requirements versus implementation and evidence

**Specification, and needed before any implementation starts.** The H2 causal-closure rule; the
H5 lifecycle table and orphan rule; the H6 split of publication serialization from publication
authority across contract levels; the H3 work-location constraint; the H4 divergence
observation at promotion; the H1 decision on whether Silo is a profile or a module; and the H8
terminology resolution. H1 and H8 should be settled first because both change the vocabulary
every other requirement is written in.

**Implementation, not specification.** No silo binding exists. `tools/awp_workstate.py`
projects one canonical capsule and has no derivation, promotion, or cross-workstate path, and
nothing in `tools/` reads a parent digest. None of that blocks the specification work above,
and none of it should be treated as a gap in the model.

**Evidence, deferred.** No evidence is owed until a binding exists. Worth recording now: the
minimum conformance fixture set contains nothing for cross-workstate promotion, causal-closure
rejection, orphaned-child re-anchoring, or two bindings sharing one physical location. Those
four are the fixtures this feature will need, and naming them now is cheaper than rediscovering
them after a binding is built.

## Remaining disagreement

None on hierarchy or on immutable derivation; both are correct. H1 is where I expect
disagreement, and the case against my recommendation is reasonable: a silo carries governance
and lifecycle that Synchronization forks do not, and a profile spread across three modules is
harder to read than one self-contained module. My position is that the family can afford a
fourth divergence vocabulary less than it can afford a longer specification, and that the
attribution problem already outstanding in the draft argues for composing from existing
mechanisms rather than adding new ones. If the decision owner prefers a standalone module,
H2 through H8 apply unchanged — only H1 depends on that choice.
<!-- awp:generated:end -->

<!-- awp:e35c8a17d94b426f9a02fd6b81c47e93:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-silo-hierarchy-response-2026-09-07",
  "title": "Silo hierarchy and canonical publication — response",
  "created_at": "2026-09-07T16:34:00Z",
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
<!-- awp:e35c8a17d94b426f9a02fd6b81c47e93:manifest:end -->

<!-- awp:e35c8a17d94b426f9a02fd6b81c47e93:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-silo-hierarchy-response-2026-09-07",
  "frontier": [
    "evt:silo-hierarchy-response"
  ],
  "generated_at": "2026-09-07T16:34:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:silo-hierarchy",
        "type": "consultation",
        "revision": 2,
        "status": "answered",
        "purpose": "critique",
        "question": "Is a hierarchical immutable-base Silo model a sound way to preserve and coordinate non-canonical project-state futures?",
        "requested_action": "Return one independent critique with a minimal normative data model and exact boundaries. Do not modify protocol sources.",
        "decision_owner": "principal:mark",
        "participants": ["actor:codex", "actor:claude-review"],
        "effective_loop_policy": {"max_rounds": 1, "continuation_requires": "recorded decision-owner approval"},
        "context": {
          "response_path": "consultations/silo-hierarchy-response.awp.md",
          "working_tree_state": "uncommitted changes present in spec/drafts/0.8.0 and schemas at review time"
        },
        "read_first": [
          "decision:silo-as-fork-profile",
          "claim:silo-is-a-fork",
          "claim:promotion-causal-closure-missing",
          "claim:silo-binding-isolation-hazard",
          "claim:inherited-pin-staleness",
          "claim:silo-lifecycle-absent",
          "claim:publisher-role-conflation",
          "claim:promote-term-collision"
        ],
        "desired_output": "One independent critique with a minimal normative data model, exact boundaries between canonical state, parent silos, child silos and Git worktrees, and a specification-versus-implementation-versus-evidence split.",
        "answer": "Hierarchical immutable-base silos are sound; hierarchy and immutable derivation are both correct and no argument was found against either. Two structural changes are recommended. First, re-base the feature onto the fork mechanism the family already defines: Core section 3 makes forking a family invariant and Synchronization section 5 already records parent workstate, parent frontier, fork event, reason and inherited module declarations, so a silo is a fork with a governance overlay; define Silo as a profile over Synchronization forks plus Capsule 3.2 canonical maintenance plus one new promotion receipt, and extend the fork record with the parent capsule digest it lacks, rather than adding a fourth divergence primitive alongside fork, branch and replica. Second, promotion of selected results is a cherry-pick with no causal-closure rule: a promotion set must be causally closed over its members' pinned references against the target frontier, or extend, re-derive, or be rejected, because silent partial promotion corrupts canonical projection through the feature's intended happy path. Six further hazards: silo binding isolation plus a shared worktree defeats COOP-1 collision detection while every rule is obeyed; inherited pins can go stale across the immutable derivation boundary and must be re-resolved at promotion; no lifecycle or orphan rule is proposed; canonical publisher conflates COOP-1 serialization with COOP-3 authority; skipped ancestors in deep promotion are unaccounted; and 'promotion' collides with the family's closing invariant against silently promoting assertions into fact.",
        "terminal_result": "revised"
      }
    ],
    "decisions": [
      {
        "id": "decision:silo-as-fork-profile",
        "type": "decision",
        "question": "Should Silos be a new AWP module with their own derivation record, or a profile composed from the family's existing fork, canonical-maintenance and receipt mechanisms?",
        "status": "proposed",
        "choice": "Define Silo as a profile: Synchronization section 5 fork for derivation and identity, extended with an optional parent_capsule_digest; Capsule 3.2 canonical maintenance for publication serialization; and one new promotion_receipt record type. Add normatively, independent of that choice: a causal-closure requirement on promotion sets; a silo lifecycle with active, promoted, abandoned, superseded and orphaned states and a non-cascading parent-termination rule; a work-location constraint forbidding two guarded bindings in one physical location; mandatory re-resolution of inherited pins at promotion recorded as a divergence observation; an explicit split of canonical-publication serialization at COOP-1 from enforced role separation at COOP-3; bypassed-ancestor accounting for deep promotion; and resolution of the promote terminology collision.",
        "decided_by": "actor:claude-review",
        "requires_authority": "principal:mark",
        "affects": [
          "spec/drafts/0.8.0/synchronization.md",
          "spec/drafts/0.8.0/capsule.md",
          "spec/drafts/0.8.0/core.md",
          "spec/drafts/0.8.0/coordination.md",
          "spec/drafts/0.8.0/cooperation-contracts.md"
        ]
      }
    ],
    "claims": [
      {
        "id": "claim:silo-is-a-fork",
        "type": "claim",
        "statement": "A silo has its own capsule, participants and lifecycle and therefore its own workstate identity, which makes it a fork under the family's existing definition: core.md section 3 states that forking creates a new workstate ID recording the parent workstate and parent frontier, and synchronization.md section 5 already records parent workstate ID, parent frontier, fork event, reason or intent, and inherited module declarations. The proposal's only novel derivation field is the parent capsule digest.",
        "epistemic_status": "verified",
        "evidence": ["evidence:core-fork-invariant", "evidence:sync-fork-record"]
      },
      {
        "id": "claim:promotion-causal-closure-missing",
        "type": "claim",
        "statement": "Promotion of selected results is a partial application of one divergent branch to another, which synchronization.md section 6 does not cover because that section governs merging tips rather than promoting subsets. Without a causal-closure requirement, promoting a record whose pinned reference depends on an unpromoted record yields a dangling reference and AWP-COORD-MISSING-DEPENDENCY at the next canonical projection, after the promotion has already been receipted as successful.",
        "epistemic_status": "verified",
        "evidence": ["evidence:sync-merge-rules", "evidence:coord-missing-dependency-code"]
      },
      {
        "id": "claim:silo-binding-isolation-hazard",
        "type": "claim",
        "statement": "cooperation-contracts.md 4.1 derives project_id from repository-intrinsic state and forbids merging records across store identifiers, so a silo binding and its parent's binding in one repository are correctly isolated. The consequence is that a silo participant and a canonical participant sharing one worktree each hold a valid COOP-1 binding, each obey their returned decisions, and neither can observe the other's guarded scopes, producing an undetected collision with every rule obeyed.",
        "epistemic_status": "verified",
        "evidence": ["evidence:binding-identity-rules"]
      },
      {
        "id": "claim:inherited-pin-staleness",
        "type": "claim",
        "statement": "coordination.md section 15 propagates reverse-dependency staleness within a workstate and defines no propagation across a derivation boundary, which immutable derivation requires. A child can therefore hold an inherited constraint, accepted decision or verified claim that the parent has since revised, with nothing marking it; the exposure materializes at promotion, so inherited records must carry parent revision pins that are re-resolved against the target frontier at that moment.",
        "epistemic_status": "verified",
        "evidence": ["evidence:dependency-staleness-scope"]
      },
      {
        "id": "claim:silo-lifecycle-absent",
        "type": "claim",
        "statement": "Every AWP record family with meaningful state carries an explicit lifecycle table with required transition conditions and named terminal states, including intents, overlaps, negotiations, integrations and leases. The silo proposal specifies none, and in particular has no rule for a live child whose parent has reached a terminal state.",
        "epistemic_status": "verified",
        "evidence": ["evidence:lifecycle-tables-present"]
      },
      {
        "id": "claim:publisher-role-conflation",
        "type": "claim",
        "statement": "The canonical publisher role combines a COOP-1 mechanism with a COOP-3 guarantee. Serialized canonical replacement is already specified at COOP-1 by capsule.md 3.2's expected-digest and expected-frontier comparison with a stale_base result instead of last-write-wins, and synchronization.md 9.1 already states that projection ownership controls representation updates only and does not grant authority over project changes. Enforcing that only the publisher may write canonical state, and that a delegated steward's approval is authentic, requires authenticated principals and a protected mutation path, which are COOP-3.",
        "epistemic_status": "verified",
        "evidence": ["evidence:capsule-canonical-maintenance", "evidence:sync-projection-ownership"]
      },
      {
        "id": "claim:promote-term-collision",
        "type": "claim",
        "statement": "coordination.md's closing essential invariant uses 'promote' for the unwarranted elevation the specification exists to prevent — no actor, record, message, clean merge or passing claim may silently promote asserted coordination into observed fact, verified compatibility or external authority — and fixture 32 uses it identically. Making promotion a first-class legitimate silo operation introduces a second sense of the term into one document family.",
        "epistemic_status": "verified",
        "evidence": ["evidence:promote-invariant-text"]
      },
      {
        "id": "claim:silo-implementation-absent",
        "type": "claim",
        "statement": "No silo binding exists in the repository: tools/awp_workstate.py projects a single canonical capsule with no derivation, promotion or cross-workstate path, and no tool reads a parent capsule digest. The minimum conformance fixture set likewise contains no cross-workstate promotion, causal-closure rejection, orphaned-child re-anchoring, or shared-location dual-binding fixture. Both are future implementation and evidence work rather than defects in the proposed model.",
        "epistemic_status": "observed",
        "evidence": ["evidence:tools-silo-scan", "evidence:fixture-gap-scan"]
      }
    ],
    "evidence": [
      {
        "id": "evidence:core-fork-invariant",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/core.md section 3: 'Every workstate MUST have a stable workstate_id. Copying or repackaging a workstate does not change this ID. Forking creates a new workstate ID and records the parent workstate and parent frontier.'",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:sync-fork-record",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/synchronization.md section 5: forking records parent workstate ID, parent frontier, fork event, reason or intent, and inherited module declarations; 'Copying or repackaging without divergent identity is not a fork'; 'Concurrent replicas of the same workstate retain one workstate ID.' No parent capsule digest is recorded.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:sync-merge-rules",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/synchronization.md section 6: mechanical merge unions events by ID after integrity validation and preserves all concurrent tips, and must not silently apply last-write-wins to authority or constraints, accepted decisions, incompatible record revisions, contradictory verified claims, artifact versions occupying one logical slot, or module-specific invariants. The section addresses merging tips and does not define promotion of a proper subset of one branch into another.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:coord-missing-dependency-code",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 18 diagnostics table defines AWP-COORD-MISSING-DEPENDENCY at severity error for a referenced record, revision, event, artifact or evaluator that is unavailable, which is the diagnostic a causally incomplete promotion produces at the target's next projection.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:binding-identity-rules",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/cooperation-contracts.md 4.1: the stable binding identity contains workstate identifier, repository-intrinsic project identifier, canonical store identifier, scope-model identifier and version, and binding epoch; 'The project identifier MUST derive from repository-intrinsic state and MUST NOT derive from a filesystem path or mount location'; and 'A participant MUST NOT merge records from different store identifiers into one work decision; it MUST select one declared binding or return blocked.'",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:dependency-staleness-scope",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 15 defines staleness as reverse-dependency propagation over records within one projection, cleared only by a type-specific revalidated, rebased or superseded transition with fresh evidence. No cross-workstate or cross-derivation propagation is defined anywhere in the module.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:lifecycle-tables-present",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md defines explicit lifecycle tables with required conditions and named terminal states for intents (section 7), overlaps (section 9), negotiations (section 10), integrations (section 16) and leases (section 19), establishing the family convention the silo proposal omits.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:capsule-canonical-maintenance",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/capsule.md 3.2: a canonical checkpoint request must carry an idempotency key, expected whole-capsule digest, expected generated-region digest, expected semantic frontier, proposed semantic frontier, checkpoint or no-change disposition, and required handoff fields; the host compares all expected values immediately before replacement and a mismatch must produce stale_base or an equivalent recoverable result rather than last-write-wins.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:sync-projection-ownership",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/synchronization.md 9.1: 'A deployment with one canonical Capsule MUST identify how projection ownership is serialized. An enforced deployment may use a fenced integration_owner lease. An advisory deployment may use a single local writer with atomic compare-and-swap. Projection ownership controls representation updates only; it does not grant authority over project changes.'",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:promote-invariant-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 27 essential invariant: 'No actor, record, message, clean merge, or passing claim may silently promote asserted coordination into observed fact, verified compatibility, or external authority.' Section 24 fixture 32 uses the same sense: 'authenticated presence accepted without promoting it to mutation authority.'",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:tools-silo-scan",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Scan of spec/drafts/0.8.0/ and tools/ for silo, derivation and promotion concepts: the term silo appears in no specification module; promote appears only in coordination.md's prohibitive invariant and fixture 32 and in adapters.md's record-promotion sense; no tool implements derivation, promotion, or any cross-workstate path, and awp_workstate.py projects one canonical capsule only.",
        "observed_at": "2026-09-07T16:25:00Z"
      },
      {
        "id": "evidence:fixture-gap-scan",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "spec/drafts/0.8.0/coordination.md section 24 lists thirty-two minimum conformance fixtures, none of which covers cross-workstate promotion, causal-closure rejection, orphaned-child re-anchoring, or two coordination bindings sharing one physical work location.",
        "observed_at": "2026-09-07T16:25:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:silo-hierarchy-response",
        "type": "checkpoint",
        "frontier": ["evt:silo-hierarchy-response"],
        "created_at": "2026-09-07T16:34:00Z",
        "summary": "One bounded critique round returned with terminal result 'revised'. Hierarchical immutable-base silos are sound; hierarchy and immutable derivation stand unchallenged. Two structural recommendations: define Silo as a profile over the existing Synchronization fork, Capsule canonical maintenance and one new promotion receipt rather than as a fourth divergence primitive, extending the fork record with the parent capsule digest it lacks; and require promotion sets to be causally closed over pinned references against the target frontier. Six further hazards recorded: shared-worktree binding isolation defeating COOP-1 collision detection, inherited-pin staleness across the derivation boundary, absent lifecycle and orphan rule, canonical-publisher conflation of COOP-1 serialization with COOP-3 authority, unaccounted bypassed ancestors in deep promotion, and the 'promote' terminology collision with the family's closing invariant. A minimal two-record data model and canonical/parent/child/worktree boundaries are supplied; absent tooling and four missing conformance fixtures are classified as implementation and evidence work rather than model defects.",
        "recommended_next_action": {
          "action": "principal:mark decides whether to open a 0.8.0 draft revision adopting decision:silo-as-fork-profile. H1 (profile versus module) and H8 (promote terminology) should be settled first because both determine the vocabulary the remaining requirements are written in; H2 through H7 apply unchanged under either H1 outcome. Continuation of this consultation past round one requires principal:mark's recorded approval.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:e35c8a17d94b426f9a02fd6b81c47e93:snapshot:end -->
