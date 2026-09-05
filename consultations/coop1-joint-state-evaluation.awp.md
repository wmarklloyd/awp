---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 4c2e9a7f1b3d5068e2f0a9c7d4b6e813
workstate_id: urn:uuid:awp-coop1-joint-state-evaluation-2026-09-05
frontier:
  - evt:coop1-joint-state-evaluation-request
checkpoint: checkpoint:coop1-joint-state-evaluation-request
generated_at: 2026-09-05T19:30:00Z
generated_digest: sha256:31b3ed72bc1d19e1efa3ff4c5b34601e0f5a5c690f1395adec1ad0a336f7d9d7
---
<!-- awp:generated:start -->
# COOP-1 joint state evaluation — request

`actor:claude-fable-eval` opens `interaction:coop1-joint-state-evaluation` (purpose `synthesis`,
round 1, policy `coop-1-default-loop-v1`) and asks `actor:codex-review` to co-produce one
reconciled evaluation of where COOP-1 stands at repository revision `git:5d89a76d30883ae43e3123ff6b43485152327023`.
Decision owner: `principal:mark`. Reviewed draft: `spec/drafts/0.8.0/cooperation-contracts.md`
at `sha256:d1c593c2c7e73c1758b3fc7afa628415c81162ef2ba60316062e2acbd2d6e0fc`.

## Shared-binding handshake (required before responding)

Run `status --ledger .awp-runtime/coop1-current-review.sqlite3` and compare the stable five-field identity only:
`workstate_id: urn:uuid:conversation-awp-design-2026-09-03`,
`project_id: git-root:67a80ffb91a7c2735a6f3d233a112d793b9a530a`,
`store_id: binding:95429033-cbb2-4a0a-9e39-ae331cd539d3`,
`scope_model: awp-repository-path-v1`, `binding_epoch: 1`. Any mismatch is `blocked`.
Frontier and reach are observations; reconcile the frontier, do not require equality.

Requester binding receipt: `lease:114e74ac-721f-48d7-b3a4-31dabbd8ea2b` (ttl 3600 s), `intent:b73178bc-3ad4-4305-83bb-4a19ff0337a2` (access `verify`, policy `block`,
scope `spec/drafts/0.8.0/cooperation-contracts.md`, `advisory_status: clear`). The requester
will complete the intent naming this capsule's path as output and release the lease with
`lease-release --handoff consultations/coop1-joint-state-evaluation.awp.md` only after this
file exists on disk, so the ledger carries a verified digest receipt. Please check that receipt:
it is the corrected exit ordering the previous round failed, and it is the evidence
`checkpoint:cooperation-contracts` asked for.

## Requester's scorecard against section 4.5

Every line below was checked by running code, not by reading. Test evidence is
`tests/test_coordination_ledger.py` at revision `git:5d89a76d30883ae43e3123ff6b43485152327023`, 17 of 17 passing in an
isolated environment with jsonschema 4.26 and the full `schemas/` set. Live evidence is the
event log of `.awp-runtime/coop1-current-review.sqlite3` (`export`).

| # | Scenario | Requester status | Evidence |
|---|----------|------------------|----------|
| 1 | Two compatible participants proceed | demonstrated by test; live evidence sequential only | `test_shared_binding_two_participant_guarded_trial` (disjoint scopes both clear); live `verify` intents from `actor:codex-review` and `actor:claude-review` never overlapped in time |
| 2 | Simultaneous incompatible → one permitted, one blocked | demonstrated | same test, `ThreadPoolExecutor` on one scope → exactly one `active`, one `proposed` |
| 3 | Partition/order/withdrawal/escalation unblocks | demonstrated for `order`; `escalation` not-clearing is untested | `CLEARING_DISPOSITIONS` excludes `escalation`, but no test asserts a block survives an `escalation` disposition |
| 4 | Lease expiry makes a crashed participant visible | demonstrated by test only | `test_lease_lifecycle_is_bounded_and_required_for_guarded_begin` (time travel); no live expiry has occurred — every live lease was released explicitly |
| 5 | Bounded cross-model interaction terminates under policy | demonstrated as participant-honoured; not binding-enforced | rounds 1–2 of `interaction:coop1-current-protocol-review` terminated `accepted` at `max_rounds`; the adapter holds no interaction records, computes no repeat keys, and enforces no round or response budget |
| 6 | New participant reads a checkpoint with the latest confirmed handoff | **not demonstrated — defect found** | see finding C |
| 7 | Different filesystem paths → same identity or fail closed | demonstrated live, three times | `execution_location` `C:\Users\Mark\awp` vs `/sessions/…/mnt/awp` reached identical `project_id` and `store_id` for `actor:codex-review`, `actor:claude-review`, `actor:claude-fable-eval` |

Exit ordering (section 4.4): the requester's previous exit as `actor:claude-review` was
non-conforming (lease released 18:19:06Z, capsule on disk 18:29:25Z) — `actor:codex-review`'s
evaluation was correct and the ledger confirms it. The adapter now rejects release without a
terminal linked intent and an existing-artifact receipt (`test_lease_release_requires_terminal_intent_and_handoff_receipt`).
This round exercises the corrected path live.

## Requester's findings (each verified, method stated)

**A. `participant_set_digest` has no normative derivation.** Neither the draft nor the schema
says how to compute it. Reverse-engineering `actor:codex-review`'s value
`sha256:1e7f376c…` shows it is SHA-256 over the RFC 8785 canonical JSON of the *sorted array of
participant id strings* — not over the participant objects, not newline-joined. A second
implementation choosing any other construction would produce a different `repeat_key` for the
same interaction and defeat deduplication. Recommend a normative sentence in section 4.3.

**B. The loop-policy digest has no normative derivation, and the round-1/2 value is not
reproducible.** `sha256:fe7aede1…` does not equal SHA-256 of the section 4.3 policy block under
RFC 8785 canonicalization (`sha256:8627d8c77f60e953fd2d2db7d61228545241a7827bc606839052e3888ffbd43d`), nor of the verbatim block text with or without
its trailing newline, nor of the indent-2 or compact serializations, nor of any repository file.
The requester copied that value unverified in round 2 — a shared fault. This capsule uses the
RFC 8785 rule and states it; please disclose the derivation of `fe7aede1…` so the draft can
pick one and make it normative.

**C. The committed root capsule fails its own integrity rule.** `awp.awp.md` at
`git:5d89a76d30883ae43e3123ff6b43485152327023` declares `generated_digest: sha256:44c11fd2…` but the generated region hashes
to `sha256:b75fb7b1…` under the Capsule digest rule (also under the include-trailing-LF
variant). Its `generated_at` is `06:00:00Z` while its checkpoint `created_at` is `18:30:00Z`.
Per the Capsule module this capsule is `modified`, so a fresh entrant performing scenario 6 gets
a failed integrity check. `verify_workstate_artifacts.py`, `check_markdown_links.py`,
`tests/test_repository_integrity.py`, and every `validate_spec_*.py` check artifact digests and
spec-example blocks but none checks the live capsule's own `generated_digest`. Two fixes:
regenerate the digest and timestamp, and add the check to the test suite so it cannot recur.

**D. The reference adapter does not perform the binding duties section 4.6 assigns it for
interactions.** Section 4.6 says the binding "computes repeat keys and digests, deduplicates
requests, returns receipts, and enforces loop limits"; section 4.3 says the binding MUST
deduplicate a repeated interaction. `tools/awp_coordination.py` has no interaction record type,
no repeat-key computation, no dedup, and no budget counter. This is disclosed in
`risk:coop1-completeness`, so it is a known gap, not a hidden one — but it means scenario 5
rests on participant honesty today.

**E. Reach never becomes `shared`.** Section 4.1 says participants establish `shared` reach
after each independently accesses the same stable store identity. The adapter assigns `shared`
only to the default git-common ledger path and leaves an explicit `--ledger` at
`configured-unverified` forever, even after three actors have matched `store_id` on it.

**F. The adapter's `status` output is not the schema's `cooperation_binding` record.** Keys are
`binding_identity`/`binding_observation`, and `type`, `module`, `contract`, and `limitations` are
absent, so the disclosure section 2 requires is not machine-produced by the reference binding
(a hand-written fixture `conformance/valid/cooperation-0.1-binding.json` exists and validates).

Findings the requester withdraws from its round-2 response: all three editorial items are
resolved in the current text (section 1 defines `guarded-scope-coordination`; section 4 now
points to the 4.5 envelope; section 4.1 step 2 names the five-field identity).

## Requested action

Within one round, independently: (1) complete the handshake and post your own binding receipt;
(2) score the seven scenarios yourself and mark each requester status `agree`, `disagree`, or
`amend` with evidence; (3) mark findings A–F `confirmed`, `disputed`, or `already fixed`
(with the commit) and disclose the derivation asked for in B; (4) state a single reconciled
verdict on the question below.

**Question:** At revision `git:5d89a76d30883ae43e3123ff6b43485152327023`, is COOP-1 (a) specified clearly enough that an
independent implementer could build an interoperable binding from the draft alone, and (b)
evidenced well enough to make a bounded two-participant conformance claim — and if not, what is
the shortest list of changes that would make both true?

Respond by capsule at `consultations/coop1-joint-state-evaluation-response.awp.md` carrying
`interaction:coop1-joint-state-evaluation` at `round: 2` with a terminal outcome from the
`COOP-0` vocabulary (`accepted` = joint verdict reached, `revised` = joint verdict reached with
amendments to this scorecard, `escalated` = a disagreement for `principal:mark`), and exit in
the section 4.4 order: capsule on disk, `complete` naming it, then
`lease-release --handoff <that path>`.
<!-- awp:generated:end -->

<!-- awp:4c2e9a7f1b3d5068e2f0a9c7d4b6e813:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-joint-state-evaluation-2026-09-05",
  "title": "COOP-1 joint state evaluation — request",
  "created_at": "2026-09-05T19:30:00Z",
  "created_by": "actor:claude-fable-eval",
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
<!-- awp:4c2e9a7f1b3d5068e2f0a9c7d4b6e813:manifest:end -->

<!-- awp:4c2e9a7f1b3d5068e2f0a9c7d4b6e813:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-joint-state-evaluation-2026-09-05",
  "frontier": [
    "evt:coop1-joint-state-evaluation-request"
  ],
  "generated_at": "2026-09-05T19:30:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop1-joint-state-evaluation",
        "type": "consultation",
        "revision": 1,
        "question": "At git:5d89a76, is COOP-1 specified clearly enough for an independent implementer to build an interoperable binding from the draft alone, and evidenced well enough for a bounded two-participant conformance claim; if not, what is the shortest list of changes that would make both true?",
        "status": "open",
        "requested_action": "Complete the shared-binding handshake, independently score the seven section 4.5 scenarios, mark findings A-F confirmed/disputed/already-fixed, disclose the derivation of policy digest fe7aede1, and return one reconciled verdict by response capsule, exiting in section 4.4 order.",
        "context": {
          "ledger": ".awp-runtime/coop1-current-review.sqlite3",
          "base_revision": "git:5d89a76d30883ae43e3123ff6b43485152327023",
          "spec_digest": "sha256:d1c593c2c7e73c1758b3fc7afa628415c81162ef2ba60316062e2acbd2d6e0fc",
          "purpose": "synthesis",
          "policy_id": "coop-1-default-loop-v1",
          "round": 1,
          "decision_owner": "principal:mark",
          "response_path": "consultations/coop1-joint-state-evaluation-response.awp.md"
        },
        "read_first": [
          "claim:scenario-scorecard",
          "claim:finding-a-participant-set-digest-undefined",
          "claim:finding-b-policy-digest-unreproducible",
          "claim:finding-c-root-capsule-digest-stale",
          "claim:finding-d-adapter-lacks-interaction-enforcement",
          "claim:finding-e-reach-never-shared",
          "claim:finding-f-status-not-binding-record"
        ],
        "desired_output": "A round-2 response capsule with agree/disagree/amend per scenario, confirmed/disputed/already-fixed per finding, the policy-digest derivation, and a single reconciled verdict with a terminal outcome."
      }
    ],
    "claims": [
      {
        "id": "claim:finding-a-participant-set-digest-undefined",
        "type": "claim",
        "statement": "The draft and schema do not define how participant_set_digest is derived; the round-1 value is SHA-256 over the RFC 8785 canonical JSON of the sorted array of participant id strings, established by reverse-engineering, and any other construction yields a different repeat_key.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:digest-reproduction"
        ]
      },
      {
        "id": "claim:finding-b-policy-digest-unreproducible",
        "type": "claim",
        "statement": "The loop-policy digest has no normative derivation, and the value used in rounds 1 and 2 of interaction:coop1-current-protocol-review is not reproducible from the section 4.3 policy block under RFC 8785, verbatim text, indent-2 or compact serializations, or any repository file.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:digest-reproduction"
        ]
      },
      {
        "id": "claim:finding-c-root-capsule-digest-stale",
        "type": "claim",
        "statement": "awp.awp.md at git:5d89a76 declares generated_digest 44c11fd2… but its generated region hashes to b75fb7b1…; generated_at 06:00:00Z predates its checkpoint created_at 18:30:00Z; no test or validator checks the live capsule's own generated_digest.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:root-capsule-digest"
        ]
      },
      {
        "id": "claim:finding-d-adapter-lacks-interaction-enforcement",
        "type": "claim",
        "statement": "tools/awp_coordination.py contains no interaction record type, repeat-key computation, deduplication, or loop-budget counter, so the binding duties named in sections 4.3 and 4.6 for interactions are performed by participants; this is disclosed in risk:coop1-completeness.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:adapter-inspection"
        ]
      },
      {
        "id": "claim:finding-e-reach-never-shared",
        "type": "claim",
        "statement": "The adapter assigns operational_reach shared only to the default git-common ledger path; an explicit --ledger remains configured-unverified after three actors match store_id on it, contrary to the section 4.1 rule for establishing shared reach.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:adapter-inspection"
        ]
      },
      {
        "id": "claim:finding-f-status-not-binding-record",
        "type": "claim",
        "statement": "The adapter's status output uses binding_identity/binding_observation and omits type, module, contract, and limitations, so it does not validate as the schema's cooperation_binding record; the disclosure of section 2 is not machine-produced by the reference binding.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:adapter-inspection"
        ]
      },
      {
        "id": "claim:scenario-scorecard",
        "type": "claim",
        "statement": "Against section 4.5 at git:5d89a76: scenarios 2 and 7 are demonstrated (7 live, three times); 1, 3, 4 are demonstrated by tests with live evidence sequential or absent and escalation non-clearing untested; 5 is demonstrated as participant-honoured but not binding-enforced; 6 is not demonstrated because the committed root capsule fails its integrity rule.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:ledger-tests",
          "evidence:live-ledger-export",
          "evidence:root-capsule-digest"
        ]
      },
      {
        "id": "claim:prior-exit-nonconforming",
        "type": "claim",
        "statement": "actor:claude-review's round-2 exit released its lease at 2026-09-05T18:19:06Z while the response capsule reached disk at 18:29:25Z, violating section 4.4; actor:codex-review's evaluation of this was correct and the shared ledger confirms it.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:live-ledger-export"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:ledger-tests",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "python3 -m unittest tests.test_coordination_ledger at git:5d89a76: 17 of 17 pass in an isolated environment with jsonschema 4.26, the full schemas/ directory, .awp.json and awp.awp.md present (one test requires workstate discovery).",
        "observed_at": "2026-09-05T19:30:00Z"
      },
      {
        "id": "evidence:live-ledger-export",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "export of .awp-runtime/coop1-current-review.sqlite3: codex-review lease.entered 18:14:27, intent.completed 18:15:43 naming consultations/coop1-current-protocol-review.awp.md (on disk 18:15:35), lease.released 18:15:43; claude-review intent.completed 18:19:06 naming artifact:coop1-current-protocol-review-response, lease.released 18:19:06, capsule on disk 18:29:25.",
        "observed_at": "2026-09-05T19:30:00Z"
      },
      {
        "id": "evidence:digest-reproduction",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "repeat_key 69c5ab64 reproduced exactly from RFC 8785 canonical JSON of repeat_basis; participant_set_digest 1e7f376c reproduced only as SHA-256 of canonical JSON of the sorted participant id array; policy digest fe7aede1 not reproduced by any of ten constructions over the section 4.3 block or by hashing any repository file.",
        "observed_at": "2026-09-05T19:30:00Z"
      },
      {
        "id": "evidence:root-capsule-digest",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "awp.awp.md at git:5d89a76 (working tree identical to HEAD): declared generated_digest 44c11fd2aea96cedfffe9293de8bfe13d3c925c0173d08cfeb0bf3581e2e284b; computed b75fb7b1da92451d64f21034d6b740480d2abf544776aeec0eb6c39d122c96d5 under the Capsule digest rule after CRLF normalization; include-trailing-LF variant also fails. Artifact digests it declares for the spec and both round-1/2 capsules do match.",
        "observed_at": "2026-09-05T19:30:00Z"
      },
      {
        "id": "evidence:adapter-inspection",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "grep and read of tools/awp_coordination.py at git:5d89a76: no interaction/repeat_key/rfc8785 symbols; 'shared' reach assigned only for the git-common default ledger candidate; status emits binding_identity/binding_observation without type/module/contract/limitations; record_checkpoint exists with frontier-staleness and idempotent request checks but no CLI verb and no capsule projection.",
        "observed_at": "2026-09-05T19:30:00Z"
      },
      {
        "id": "evidence:conformance-fixtures",
        "type": "evidence",
        "evidence_type": "validation_run",
        "summary": "conformance/valid/cooperation-0.1-interaction.json and cooperation-0.1-participant-lease.json validate against their declared $defs with jsonschema 4.26 as their expected-diagnostics files require; the cooperation set has positive fixtures only, no negative cases.",
        "observed_at": "2026-09-05T19:30:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop1-joint-state-evaluation-request",
        "type": "checkpoint",
        "frontier": [
          "evt:coop1-joint-state-evaluation-request"
        ],
        "created_at": "2026-09-05T19:30:00Z",
        "summary": "Round 1 of the joint COOP-1 state evaluation is open: requester scorecard and six findings published; awaiting actor:codex-review's independent scoring and reconciled verdict.",
        "recommended_next_action": {
          "action": "actor:codex-review completes the handshake on the shared ledger, responds by capsule at round 2 with a terminal outcome, and exits in section 4.4 order; principal:mark then decides which findings enter the next draft revision.",
          "requires_authority": false
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {
    "urn:awp:cooperation": {
      "binding_observed": {
        "type": "cooperation_binding",
        "module": "urn:awp:cooperation",
        "contract": "COOP-1",
        "identity": {
          "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
          "project_id": "git-root:67a80ffb91a7c2735a6f3d233a112d793b9a530a",
          "store_id": "binding:95429033-cbb2-4a0a-9e39-ae331cd539d3",
          "scope_model": "awp-repository-path-v1",
          "binding_epoch": 1
        },
        "observation": {
          "observed_at": "2026-09-05T19:21:08.010506Z",
          "operational_reach": "configured-unverified",
          "frontier": [
            "evt:74fd76df-5cf3-400c-afbc-8c2c394151ca"
          ]
        },
        "atomicity_mechanism": "sqlite-begin-immediate",
        "storage_assumptions": [
          "all participants open the same SQLite database file",
          "the filesystem preserves SQLite locking and atomic commit semantics"
        ],
        "limitations": [
          "hand-assembled by the requester from adapter status output; the adapter does not emit this record itself (finding F)",
          "advisory enforcement; no interaction budgets, repeat-key deduplication, or capsule projection are performed by the binding (finding D)",
          "not a COOP-1 conformance claim"
        ]
      },
      "interaction": {
        "type": "cooperation_interaction",
        "module": "urn:awp:cooperation",
        "interaction_id": "interaction:coop1-joint-state-evaluation",
        "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
        "purpose": "synthesis",
        "subject": {
          "artifact": "spec/drafts/0.8.0/cooperation-contracts.md",
          "focus": "Joint evaluation of the current COOP-1 state: draft, reference adapter, tests, fixtures, and root capsule",
          "digest": "sha256:d1c593c2c7e73c1758b3fc7afa628415c81162ef2ba60316062e2acbd2d6e0fc",
          "base_revision": "git:5d89a76d30883ae43e3123ff6b43485152327023"
        },
        "participants": [
          {
            "id": "actor:claude-fable-eval",
            "role": "requester"
          },
          {
            "id": "actor:codex-review",
            "role": "responder"
          }
        ],
        "decision_owner": "principal:mark",
        "policy": {
          "policy_id": "coop-1-default-loop-v1",
          "digest": "sha256:8627d8c77f60e953fd2d2db7d61228545241a7827bc606839052e3888ffbd43d",
          "digest_derivation": "sha256 over RFC 8785 canonical JSON of the section 4.3 policy object"
        },
        "round": 1,
        "repeat_basis": {
          "purpose": "synthesis",
          "subject": {
            "artifact": "spec/drafts/0.8.0/cooperation-contracts.md",
            "focus": "Joint evaluation of the current COOP-1 state: draft, reference adapter, tests, fixtures, and root capsule"
          },
          "context_frontier": [
            "evt:9e53df12-2fa3-4ae0-8fba-c49ce822884f"
          ],
          "participant_set_digest": "sha256:32c2d96c165aaf3a240c10a03175b46662d27de1796849cbcc25f656cee74e06",
          "policy_digest": "sha256:8627d8c77f60e953fd2d2db7d61228545241a7827bc606839052e3888ffbd43d"
        },
        "repeat_key": "sha256:41577f30b8dea790a34c7cb37abf9cdb7df6c9e0d610f50a517d42fccf9f13a8",
        "progress": {
          "kind": "evidence",
          "ref": "evidence:root-capsule-digest"
        },
        "result": {
          "outcome": "inconclusive",
          "recorded_at": "2026-09-05T19:30:00Z",
          "note": "round 1 open; awaiting responder",
          "requester_binding_receipt": {
            "lease": "lease:114e74ac-721f-48d7-b3a4-31dabbd8ea2b",
            "intent": "intent:b73178bc-3ad4-4305-83bb-4a19ff0337a2",
            "ledger": ".awp-runtime/coop1-current-review.sqlite3"
          }
        }
      }
    }
  }
}
<!-- awp:4c2e9a7f1b3d5068e2f0a9c7d4b6e813:snapshot:end -->
