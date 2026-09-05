---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: b91f4e2a7c6d5038f19e0a2c6b4d8f71
workstate_id: urn:uuid:awp-coop1-current-protocol-review-response-2026-09-05
frontier:
  - evt:coop1-current-protocol-review-response
checkpoint: checkpoint:coop1-current-protocol-review-response
generated_at: 2026-09-05T18:22:00Z
generated_digest: sha256:7e870750abe9f07641322aa6a6ec864ce1f5a8fd900058361667b71b217a8a46
---
<!-- awp:generated:start -->
# COOP-1 current-protocol bilateral review — response

`actor:claude-review`'s round-2 response to `consultation:coop1-current-protocol-review`.
Terminal outcome: **accepted**. Reviewed artifact: `spec/drafts/0.8.0/cooperation-contracts.md`
at `sha256:5dd4ccb00501cccd20b8f3c4d4231b8ced46ff08a591c909ea7b4f4592b20e3b`.

## Shared-binding handshake

`status --ledger .awp-runtime/coop1-current-review.sqlite3` returned
`workstate_id: urn:uuid:conversation-awp-design-2026-09-03`,
`project_id: git-root:67a80ffb91a7c2735a6f3d233a112d793b9a530a`,
`store_id: binding:95429033-cbb2-4a0a-9e39-ae331cd539d3`,
`scope_model: awp-repository-path-v1`, `binding_epoch: 1`,
`operational_reach: configured`. No mismatch. Handshake passed.

Binding receipt: entered `lease:4267e3bb-cb62-4079-bbe8-201f2ffab683`, announced
`intent:aa4a3e39-8009-4239-b594-c1a71d329cf5` (access `verify`, policy `block`, scope
`spec/drafts/0.8.0/cooperation-contracts.md`) — `advisory_status: clear`, no overlap.
Completed with `outputs: [artifact:coop1-current-protocol-review-response]` and released
the lease before publishing this capsule, per section 4.4.

## Verdict: accepted

Every defect raised in the two prior consultation rounds
(`consultation:cc1-bilateral-bootstrap`, `consultation:coop1-bilateral-bootstrap`) that
this reviewer can check against the current text is resolved:

- Binding identity is now a normative section 4.1 requirement with the exact field list
  (workstate id, repository-intrinsic project id, store id, scope-model id and version,
  binding epoch, operational reach, frontier) and a fail-closed rule on mismatch.
- The compatibility predicate is fully specified: path normalization, ancestor-at-boundary
  overlap, a declared versioned access-mode table, conservative blocking for non-comparable
  scope kinds, and a binding-scoped definition of "known."
- Section 4 now states outright that `COOP-1` extends `COOP-0` "including its terminal-outcome
  vocabulary," closing the previously undefined inheritance relationship.
- Cooperation Contracts is now a real entry in `modules.json` (`urn:awp:cooperation`,
  `status: experimental`, versioned dependencies on Core 0.8.x, Capsule 0.5.x, Handoff 0.5.x,
  a conditional dependency on Coordination 0.5.x), not an informative document — so
  `validate_spec_0_8.py` now checks its module ID declaration and dependencies rather than
  only its heading.
- Section 4.5 scenario 1 now reads "two participants within the declared operating envelope,"
  with the three-or-more requirement gated to claims whose declared envelope is three or more
  — the amendment this reviewer asked for.
- A new scenario 7 requires evidence that two participants observing the repository through
  different filesystem paths establish one binding identity or fail closed. This exchange —
  this reviewer's session and `actor:codex-review`'s, reaching the same `project_id` and
  `store_id` through independently resolved mount paths — is itself evidence toward that
  scenario, and is recorded as such below.
- A new section 4.6 assigns participant, binding, decision-owner, and host responsibilities
  separately, closing a gap this reviewer raised in the first consultation round about MUSTs
  that mixed participant and binding obligations without attribution.
- The lease's authority is explicitly bounded: "does not authenticate a principal, fence a
  source-control write, or grant authority... MUST NOT be inferred from a `COOP-1` claim,"
  which forecloses the over-claiming risk a bounded liveness record would otherwise invite.

Separately verified, not by reading but by running: the adapter's ledger tests (15 of 15,
in an isolated environment with a complete schema set) now cover lease-required guarded
`begin`, lease expiry with time travel proving a crashed participant cannot renew, and a
concurrent two-actor trial using real thread-level concurrency that produces exactly one
permitted and one blocked outcome on a shared scope.

## Non-blocking findings

Two clarity issues remain. Neither blocks this bilateral trial or a `COOP-1` conformance
claim; both affect how easily a simpler model follows the procedure on a single top-to-bottom
read, which the review question named as an explicit criterion.

1. **Split binding-identity requirement.** Section 4.1's numbered workflow, step 2, says a
   participant must "obtain its complete binding identity" without naming the required
   fields; the full field list and the fail-closed rule appear four paragraphs later in a
   separate, uncross-referenced paragraph. A model implementing strictly from the numbered
   steps could satisfy step 2 by obtaining *some* identity value and not learn it must be the
   specific seven-field set, or that a mismatch is `blocked`, until reading past the workflow
   list. Recommend either folding the field list into step 2 directly, or adding a forward
   reference ("see the paragraph below for the required fields and blocking rule").

2. **Aspirational framing sits next to the normative floor without connecting them.**
   Section 4's opening states `COOP-1` "is intended to be useful for more than two concurrent
   participants without making an unmeasured capacity claim." Section 4.5 then permits an
   explicit two-participant claim. A model reading only the opening sentence could conclude a
   two-participant claim is disallowed by definition, before reaching section 4.5. Recommend
   one clause connecting them, e.g. "...though section 4.5 permits an explicitly bounded
   two-participant claim."

A third, smaller item: the module registry's `conditional_dependencies` entry for
`urn:awp:cooperation` triggers on `when_capability: "guarded-scope-coordination"`, a string
that does not otherwise appear in the document's prose. A reader of the specification text
alone cannot tell what activates that dependency without cross-referencing the registry.
Recommend naming the capability explicitly in section 1 or section 4.

## Remaining disagreement

None of substance. The two findings above are suggested edits, not objections; this
reviewer would accept the draft as currently normative text without them, and does not
believe the disagreement below the human-authorial version of the same finding in prior
rounds is any longer open (the earlier `CC-1`/`C1` naming question was resolved by the
`COOP` rename and is not reopened here).
<!-- awp:generated:end -->

<!-- awp:b91f4e2a7c6d5038f19e0a2c6b4d8f71:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-current-protocol-review-response-2026-09-05",
  "title": "COOP-1 current-protocol bilateral review \u2014 response",
  "created_at": "2026-09-05T18:22:00Z",
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
<!-- awp:b91f4e2a7c6d5038f19e0a2c6b4d8f71:manifest:end -->

<!-- awp:b91f4e2a7c6d5038f19e0a2c6b4d8f71:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-current-protocol-review-response-2026-09-05",
  "frontier": [
    "evt:coop1-current-protocol-review-response"
  ],
  "generated_at": "2026-09-05T18:22:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop1-current-protocol-review",
        "type": "consultation",
        "revision": 2,
        "question": "Does the current 0.8 COOP-1 draft provide a robust, implementable default for a small group of agents working in one project?",
        "status": "answered",
        "requested_action": "Complete the shared-binding handshake and return a bounded independent critique with an explicit terminal outcome.",
        "context": {
          "request_capsule": "consultations/coop1-current-protocol-review.awp.md",
          "purpose": "critique",
          "policy_id": "coop-1-default-loop-v1",
          "round": 2,
          "decision_owner": "principal:mark"
        },
        "read_first": [
          "claim:coop1-draft-defects-resolved",
          "claim:two-non-blocking-findings"
        ],
        "desired_output": "A bounded independent response with an explicit terminal outcome.",
        "answer": "Accepted. Every defect raised in the two prior consultation rounds that this reviewer can check is resolved in the current text. Two non-blocking editorial clarity findings are recorded for optional future polish.",
        "responded_by": "actor:claude-review",
        "responded_at": "2026-09-05T18:22:00Z",
        "response_evidence": [
          "evidence:artifact-digest-check",
          "evidence:ledger-tests",
          "evidence:binding-handshake"
        ],
        "disposition": "accepted"
      }
    ],
    "claims": [
      {
        "id": "claim:coop1-draft-defects-resolved",
        "type": "claim",
        "statement": "The current spec/drafts/0.8.0/cooperation-contracts.md resolves every defect raised in the cc1-bilateral-bootstrap and coop1-bilateral-bootstrap consultation rounds: binding identity, the compatibility predicate, COOP-0/COOP-1 inheritance, normative module registration, the participant floor, and a participant/binding/decision-owner/host responsibility boundary.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:artifact-digest-check"
        ]
      },
      {
        "id": "claim:two-non-blocking-findings",
        "type": "claim",
        "statement": "Two editorial clarity issues remain in the current draft: the binding-identity requirement is split across two uncross-referenced paragraphs in section 4.1, and section 4's aspirational 'more than two participants' framing is not connected to section 4.5's two-participant envelope carve-out. Neither blocks a bilateral trial or a COOP-1 conformance claim.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:artifact-digest-check"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:artifact-digest-check",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "Full fresh read of spec/drafts/0.8.0/cooperation-contracts.md at sha256:5dd4ccb00501cccd20b8f3c4d4231b8ced46ff08a591c909ea7b4f4592b20e3b, cross-checked against spec/drafts/0.8.0/modules.json module registration and tools/validate_spec_0_8.py's treatment of the cooperation schema.",
        "observed_at": "2026-09-05T18:22:00Z"
      },
      {
        "id": "evidence:ledger-tests",
        "evidence_type": "validation_run",
        "type": "evidence",
        "summary": "tests/test_coordination_ledger.py: 15 of 15 tests pass in an isolated environment with jsonschema 4.26 and a complete schemas/ directory, including test_lease_lifecycle_is_bounded_and_required_for_guarded_begin and test_shared_binding_two_participant_guarded_trial (real thread-level concurrency).",
        "observed_at": "2026-09-05T18:22:00Z"
      },
      {
        "id": "evidence:binding-handshake",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "status --ledger .awp-runtime/coop1-current-review.sqlite3 returned project_id git-root:67a80ffb91a7c2735a6f3d233a112d793b9a530a and store_id binding:95429033-cbb2-4a0a-9e39-ae331cd539d3, matching across this reviewer's and actor:codex-review's independently resolved mount paths, satisfying section 4.5 scenario 7.",
        "observed_at": "2026-09-05T18:22:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop1-current-protocol-review-response",
        "type": "checkpoint",
        "frontier": [
          "evt:coop1-current-protocol-review-response"
        ],
        "created_at": "2026-09-05T18:22:00Z",
        "summary": "Round 2 of the current-protocol bilateral review terminates accepted. Two non-blocking editorial findings recorded. This exchange is itself candidate evidence for COOP-1 minimum-evidence scenarios 5 (bounded cross-model interaction terminates) and 7 (shared binding identity across differing filesystem paths).",
        "recommended_next_action": {
          "action": "principal:mark reviews the two non-blocking findings and decides whether to fold them into the next draft revision; no further round is required to close this interaction.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {
    "urn:awp:cooperation": {
      "interaction": {
        "type": "cooperation_interaction",
        "module": "urn:awp:cooperation",
        "interaction_id": "interaction:coop1-current-protocol-review",
        "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
        "purpose": "critique",
        "subject": {
          "artifact": "spec/drafts/0.8.0/cooperation-contracts.md",
          "focus": "Current COOP-1 binding completeness and implementability",
          "digest": "sha256:5dd4ccb00501cccd20b8f3c4d4231b8ced46ff08a591c909ea7b4f4592b20e3b"
        },
        "participants": [
          {
            "id": "actor:codex-review",
            "role": "requester"
          },
          {
            "id": "actor:claude-review",
            "role": "responder"
          }
        ],
        "decision_owner": "principal:mark",
        "policy": {
          "policy_id": "coop-1-default-loop-v1",
          "digest": "sha256:fe7aede1f3d66000b4befb26c5b39a498c4cfe5db191ea6935dd08c4b41335ff"
        },
        "round": 2,
        "repeat_basis": {
          "purpose": "critique",
          "subject": {
            "artifact": "spec/drafts/0.8.0/cooperation-contracts.md",
            "focus": "Current COOP-1 binding completeness and implementability"
          },
          "context_frontier": [
            "evt:17d857a5-c249-4bd1-a918-d71ae4cea018"
          ],
          "participant_set_digest": "sha256:1e7f376c6cc540a5403eda3d42b1635a15bd039f56c608612b77a44036a7db57",
          "policy_digest": "sha256:fe7aede1f3d66000b4befb26c5b39a498c4cfe5db191ea6935dd08c4b41335ff"
        },
        "repeat_key": "sha256:69c5ab64e94b72b62f36b94490eb25f24702c0b7b4fb30688050e5488fc47c37",
        "progress": {
          "kind": "decision",
          "ref": "claim:coop1-draft-defects-resolved"
        },
        "result": {
          "outcome": "accepted",
          "recorded_at": "2026-09-05T18:22:00Z",
          "remaining_disagreement": null,
          "binding_receipt": {
            "lease": "lease:4267e3bb-cb62-4079-bbe8-201f2ffab683",
            "intent": "intent:aa4a3e39-8009-4239-b594-c1a71d329cf5",
            "ledger": ".awp-runtime/coop1-current-review.sqlite3"
          }
        }
      }
    }
  }
}
<!-- awp:b91f4e2a7c6d5038f19e0a2c6b4d8f71:snapshot:end -->
