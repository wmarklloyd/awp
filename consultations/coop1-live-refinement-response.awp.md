---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 7d1f3b9e5a2c4068c1e9f7a3b5d2e604
workstate_id: urn:uuid:awp-coop1-live-refinement-response-2026-09-05
frontier:
  - evt:coop1-live-refinement-response
checkpoint: checkpoint:coop1-live-refinement-response
generated_at: 2026-09-05T19:33:00Z
generated_digest: sha256:f69d09eadf256bcd5a019965e05c54c67d210d3dda0492e6921b060dc9cd3cbd
---
<!-- awp:generated:start -->
# COOP-1 live refinement — response

`actor:claude-live`, round 1 responder to `interaction:coop1-live-refinement`. Terminal
outcome: **accepted** — one slice recommended, with acceptance tests. Tool calls used on this
interaction: 8 of 12 (2 read, 1 enter+announce, 2 build+validate, 2 publish, 1 complete+release).

Handshake: `status --ledger .awp-runtime/coop1-live.sqlite3` → `project_id git-root:67a80ffb…`,
`store_id binding:9ceb4284-c982-4262-9035-c687e0649ec7`, `workstate_id
urn:uuid:conversation-awp-design-2026-09-03`, `scope_model awp-repository-path-v1`,
`binding_epoch 1`. Match. Entered `lease:6887d81a-bc26-44c9-917a-d8fa00333d9f`, announced `intent:4df537ec-2d79-4957-97e7-15c6c427d0b8` (`create` on this file,
policy `block`, `clear`) while `actor:codex-live`'s intent was still active on five other
scopes — a live instance of scenario 1 (compatible participants proceed concurrently).
Request-capsule checks: generated digest valid; `repeat_key`
reproduces under RFC 8785; `participant_set_digest`
reproduces as SHA-256 of canonical JSON of the sorted participant-id array.
The policy digest `39173eee…` cannot be checked: `coop-1-live-refinement-v1` is described in prose
only and the policy object is not in the capsule.

## Classification of what remains (material items only)

**Specification defects** — text fixes, no code needed, should not wait for any slice:
- S1. `participant_set_digest` derivation is undefined (section 4.3). Observed practice in both
  Codex capsules is canonical JSON of the sorted id array; make it normative.
- S2. Policy digest derivation is undefined; the round-1/2 value `fe7aede1…` is not reproducible
  from the section 4.3 block by RFC 8785, verbatim text, or any repository file, and a bespoke
  policy (`coop-1-live-refinement-v1`) is unverifiable when its object is not carried. Require
  `sha256(RFC 8785(policy object))` and require the policy object to travel with the interaction
  when it is not the published default.
- S3. Section 4.4 requires canonical capsule projection with expected-frontier + digest
  stale-writer exclusion but gives no receipt shape or CLI-level operation for it, so no binding
  can be tested against it.

**Binding defects** — reference adapter vs draft, at `git:5d89a76d30883ae43e3123ff6b43485152327023`:
- B1. No interaction record type, repeat-key computation, deduplication, or budget counter
  (sections 4.3, 4.6). Disclosed in `risk:coop1-completeness`.
- B2. No canonical capsule projection: `record_checkpoint` exists with staleness and idempotency
  checks but has no CLI verb and never writes the capsule.
- B3. `operational_reach` for an explicit `--ledger` never leaves `configured-unverified`
  (section 4.1 says independent access to one `store_id` establishes `shared`).
- B4. `status` output is not the schema's `cooperation_binding` record.

**Missing evidence** — against section 4.5:
- E1. Scenario 6 is currently *failing*, not merely untested: `awp.awp.md` at `git:5d89a76d30883ae43e3123ff6b43485152327023`
  declares `generated_digest 44c11fd2…`, the region hashes to `b75fb7b1…`; `generated_at
  06:00:00Z` predates its checkpoint's `18:30:00Z`. No test or validator checks the live
  capsule's own digest, so CI is green on a `modified` canonical capsule.
- E2. Escalation-does-not-clear is untested; scenario 4 has test-only evidence.
- E3. Scenario 5 evidence is participant-honoured because of B1.

## Recommended next slice: binding-owned checkpoint projection and fresh entry

Build the section 4.4 exit end-to-end in the adapter: a `checkpoint` verb that, in one
transaction with stale-writer exclusion (`--expected-frontier`, `--expected-digest`), rewrites the
canonical capsule's frontier, `generated_at`, and `generated_digest`, appends the checkpoint
record, and returns a receipt `{path, digest, frontier}`; and a fresh-entry check in `status`
that recomputes the capsule's `generated_digest` and reports `current`, `modified`, or `stale`.
Add the same check to `tests/test_repository_integrity.py` so the root capsule can never again be
committed in a `modified` state.

Why this first, ahead of B1: (i) it is the only scenario that is failing today in the committed
repository, and it fails silently; (ii) every other participant's correctness — including the
handoff receipt now required for lease release — depends on the canonical capsule being what its
digest says it is; (iii) it closes the exact gap the previous round exposed (release before
publish) by giving "publish" a machine-checked meaning; (iv) it is small: `record_checkpoint`
and the release-receipt code already contain the pieces. B1 (interaction enforcement) is the
right second slice; S1–S3 are text and can land immediately.

## Executable acceptance tests

1. `test_root_capsule_generated_digest_is_current` (repository integrity): recompute
   `awp.awp.md`'s generated digest under the Capsule rule; assert equality. Must fail at
   `git:5d89a76d30883ae43e3123ff6b43485152327023` and pass after the fix — that failure is the proof the test is live.
2. `test_checkpoint_rejects_stale_expected_frontier`: two ledgers, one checkpoints; the other
   checkpoints with the pre-advance frontier → `CoordinationError`, capsule bytes unchanged.
3. `test_checkpoint_rewrite_is_atomic_and_receipt_matches_bytes`: after `checkpoint`, the
   returned receipt digest equals SHA-256 of the file on disk, and the capsule's declared
   `generated_digest` validates.
4. `test_fresh_entry_reports_modified_on_digest_drift`: mutate one byte in the generated region;
   `status` reports `modified` and the adapter refuses `begin --policy block` until re-projected.
5. `test_release_requires_receipt_from_checkpoint_or_existing_artifact`: extend the existing
   release test so a receipt whose digest does not match the on-disk file is rejected.
6. Live: `actor:codex-*` re-enters after the projection and reads the checkpoint with a passing
   integrity check — scenario 6 evidence for the matrix.

## Remaining disagreement

None known. Two crossing requests exist right now (this one on `coop1-live.sqlite3`, the
requester's `interaction:coop1-joint-state-evaluation` on `coop1-current-review.sqlite3`);
the draft has no rule for which store is canonical when two participants each open one, which
the decision owner may want on the list after the slice above.
<!-- awp:generated:end -->

<!-- awp:7d1f3b9e5a2c4068c1e9f7a3b5d2e604:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-live-refinement-response-2026-09-05",
  "title": "COOP-1 live refinement — response",
  "created_at": "2026-09-05T19:33:00Z",
  "created_by": "actor:claude-live",
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
<!-- awp:7d1f3b9e5a2c4068c1e9f7a3b5d2e604:manifest:end -->

<!-- awp:7d1f3b9e5a2c4068c1e9f7a3b5d2e604:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-live-refinement-response-2026-09-05",
  "frontier": [
    "evt:coop1-live-refinement-response"
  ],
  "generated_at": "2026-09-05T19:33:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop1-live-refinement",
        "type": "consultation",
        "revision": 2,
        "question": "Which single vertical slice should be implemented next to make COOP-1 materially more robust?",
        "status": "answered",
        "requested_action": "Return one bounded independent critique and publish it before a receipt-backed lease release.",
        "context": {
          "ledger": ".awp-runtime/coop1-live.sqlite3",
          "base_revision": "git:5d89a76d30883ae43e3123ff6b43485152327023",
          "round": 2,
          "decision_owner": "principal:mark"
        },
        "read_first": [
          "decision:next-slice-checkpoint-projection",
          "claim:scenario-6-failing"
        ],
        "answer": "Binding-owned checkpoint projection and fresh entry: a checkpoint verb with expected-frontier/digest stale-writer exclusion that rewrites the canonical capsule and returns a receipt, a fresh-entry integrity check in status, and a repository test asserting the root capsule's generated_digest. It comes first because scenario 6 is failing silently in the committed repository and every other participant's correctness depends on the canonical capsule being what its digest says.",
        "responded_by": "actor:claude-live",
        "responded_at": "2026-09-05T19:33:00Z",
        "response_evidence": [
          "evidence:root-capsule-digest",
          "evidence:adapter-inspection",
          "evidence:request-capsule-checks"
        ],
        "disposition": "accepted"
      }
    ],
    "decisions": [
      {
        "id": "decision:next-slice-checkpoint-projection",
        "type": "decision",
        "question": "Which vertical slice next?",
        "status": "proposed",
        "choice": "Binding-owned checkpoint projection and fresh-entry integrity check, with six acceptance tests; interaction enforcement second; digest-derivation text fixes immediately.",
        "decided_by": "actor:claude-live",
        "requires_authority": "principal:mark"
      }
    ],
    "claims": [
      {
        "id": "claim:scenario-6-failing",
        "type": "claim",
        "statement": "awp.awp.md at git:5d89a76 declares generated_digest 44c11fd2… but hashes to b75fb7b1…, and generated_at 06:00:00Z predates its checkpoint created_at 18:30:00Z; no validator or test checks it, so scenario 6 currently fails silently.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:root-capsule-digest"
        ]
      },
      {
        "id": "claim:digest-derivations-undefined",
        "type": "claim",
        "statement": "participant_set_digest and policy digest have no normative derivation; the sorted-id-array construction reproduces both Codex values, while policy digests fe7aede1 and 39173eee are unverifiable from published material.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:request-capsule-checks"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:root-capsule-digest",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "Recomputed awp.awp.md generated digest under the Capsule rule after CRLF normalization: b75fb7b1da92451d64f21034d6b740480d2abf544776aeec0eb6c39d122c96d5 vs declared 44c11fd2aea96cedfffe9293de8bfe13d3c925c0173d08cfeb0bf3581e2e284b; include-trailing-LF variant also mismatches; working tree identical to HEAD.",
        "observed_at": "2026-09-05T19:33:00Z"
      },
      {
        "id": "evidence:adapter-inspection",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "tools/awp_coordination.py at git:5d89a76: record_checkpoint has staleness and idempotency checks but no CLI verb and no capsule write; no interaction/repeat_key symbols; 'shared' reach only for the git-common default path; 17/17 ledger tests pass in isolation with jsonschema 4.26.",
        "observed_at": "2026-09-05T19:33:00Z"
      },
      {
        "id": "evidence:request-capsule-checks",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "consultations/coop1-live-refinement.awp.md: generated digest valid; repeat_key reproduces under RFC 8785; participant_set_digest reproduces as canonical JSON of sorted participant ids; policy digest unverifiable (policy object absent).",
        "observed_at": "2026-09-05T19:33:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop1-live-refinement-response",
        "type": "checkpoint",
        "frontier": [
          "evt:coop1-live-refinement-response"
        ],
        "created_at": "2026-09-05T19:33:00Z",
        "summary": "Round 1 of coop1-live-refinement answered: next slice = binding-owned checkpoint projection and fresh entry, with acceptance tests; spec digest-derivation fixes recommended immediately; interaction enforcement second.",
        "recommended_next_action": {
          "action": "principal:mark accepts or amends the slice choice; implementer starts with acceptance test 1, which must fail at git:5d89a76.",
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
        "interaction_id": "interaction:coop1-live-refinement",
        "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
        "purpose": "critique",
        "subject": {
          "artifacts": [
            "spec/drafts/0.8.0/cooperation-contracts.md",
            "schemas/awp-cooperation-0.1.schema.json",
            "tools/awp_coordination.py"
          ],
          "focus": "Select the highest-value remaining vertical slice for robust COOP-1"
        },
        "participants": [
          {
            "id": "actor:codex-live",
            "role": "requester"
          },
          {
            "id": "actor:claude-live",
            "role": "responder"
          }
        ],
        "decision_owner": "principal:mark",
        "policy": {
          "policy_id": "coop-1-live-refinement-v1",
          "digest": "sha256:39173eee44d2b06b7c698be005a914b59cb9e287e05cb107c5c9e0bdfe646004"
        },
        "round": 2,
        "repeat_basis": {
          "purpose": "critique",
          "subject": {
            "artifacts": [
              "spec/drafts/0.8.0/cooperation-contracts.md",
              "schemas/awp-cooperation-0.1.schema.json",
              "tools/awp_coordination.py"
            ],
            "focus": "Select the highest-value remaining vertical slice for robust COOP-1"
          },
          "context_frontier": [
            "evt:f1fe3c2b-bdef-4542-aa82-61ef0050a0ad"
          ],
          "participant_set_digest": "sha256:0124159307237d0bc2bf884d3b952b9f3eeef2ee4e82b97c52b1462287ecf3d7",
          "policy_digest": "sha256:39173eee44d2b06b7c698be005a914b59cb9e287e05cb107c5c9e0bdfe646004"
        },
        "repeat_key": "sha256:1f9f891e3571da0c803cc18780998133076e1f14e66fc4e008e8f753ca31a3de",
        "progress": {
          "kind": "decision",
          "ref": "decision:next-slice-checkpoint-projection"
        },
        "result": {
          "outcome": "accepted",
          "recorded_at": "2026-09-05T19:33:00Z",
          "remaining_disagreement": null,
          "responder_binding_receipt": {
            "lease": "lease:6887d81a-bc26-44c9-917a-d8fa00333d9f",
            "intent": "intent:4df537ec-2d79-4957-97e7-15c6c427d0b8",
            "ledger": ".awp-runtime/coop1-live.sqlite3"
          }
        }
      }
    }
  }
}
<!-- awp:7d1f3b9e5a2c4068c1e9f7a3b5d2e604:snapshot:end -->
