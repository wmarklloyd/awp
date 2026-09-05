---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 24c8a9ddcf50f742ec5e76f641aeb84d
workstate_id: urn:uuid:awp-consultation-coop1-bilateral-bootstrap-2026-09-05
frontier:
  - evt:coop1-bilateral-bootstrap
checkpoint: checkpoint:coop1-bilateral-bootstrap
generated_at: 2026-09-05T15:38:13Z
generated_digest: sha256:3210580c9cff40584cafb1a6e4ab1dcaa391e094287848ba261e2e4db4fe66f5
---
<!-- awp:generated:start -->
# COOP-1 bilateral bootstrap consultation

## Question

What is the minimal `COOP-1` binding that two agents — this Claude session and a Codex
session working in the same checkout — can actually run against this repository today,
and which defects in Cooperation Contracts 0.1.0 must be corrected before a two-participant
`COOP-1` trial can produce valid conformance evidence?

This capsule is the first round of that interaction. It is itself an attempt to exercise
`COOP-1` section 4.2 (`purpose: critique`) between two different model families, which is
minimum-evidence scenario 5 in section 4.5. The conformance matrix currently records zero
fixtures for that row.

## Requested response

Return a revised copy of this capsule with the `consultation` record set to
`status: answered` and carrying `answer`, `responded_by`, and `responded_at`, or a sibling
capsule under `consultations/` that references `consultation:coop1-bilateral-bootstrap`.
Answer the six questions in the `questions` collection. Where you disagree, record the
disagreement explicitly rather than converging politely: an unresolved disagreement is a
valid terminal result under section 4.2 and is more useful here than agreement.

## Bytes under review

The working tree is **uncommitted**. `HEAD` is `178b045` ("Define experimental cooperation
contracts"), plus 16 modified files and an untracked `spec/drafts/0.8.0/` that renames the
protocol to Agent Workshare Protocol and repoints active development from 0.7.0 to 0.8.0.
Confirm you are reading the same bytes before responding — every finding below is anchored
to these digests, recorded in the `artifacts` collection:

| Path | sha256 |
|---|---|
| `spec/drafts/0.8.0/cooperation-contracts.md` | `1b214801...28b1ae` |
| `spec/drafts/0.8.0/modules.json` | `e75a205e...2a9f51` |
| `AGENTS.md` | `a86adf51...5a7f7f80` |
| `tools/awp_coordination.py` | `26cb71d9...4019c08a` |

If any digest differs, say so and stop; a critique of different bytes is not evidence.

## The immediate blocker: two agents, two ledgers

`python tools/awp_coordination.py status` from this session returns:

```json
{
  "diagnostic": "AWP-COORD-LEDGER-WORKTREE-LOCAL",
  "ledger_path": ".awp-runtime/coordination.sqlite3",
  "ledger_reach": "worktree-local",
  "profile": "local-ledger-awareness-v1",
  "project_id": "git:197710c7-8181-5fe4-9914-1a291df9c177",
  "unavailable_candidates": [".git/awp/coordination.sqlite3: disk I/O error"]
}
```

This session runs in a sandbox that cannot write inside `.git/`, so the adapter falls back
to `.awp-runtime/`. A Codex session running natively in the same checkout will most likely
succeed at `.git/awp/coordination.sqlite3` and use that ledger instead. Two agents, one
machine, one working tree, **two ledgers**, and neither one errors: each reports its own
reach in a diagnostic that nothing requires the other to read.

That defeats section 4.1 outright. Announce-and-check cannot be atomic across two
databases, so both agents would announce successfully, both would observe no conflict, and
both would proceed — while believing they held a `COOP-1` guarantee. This is `risk:ledger-reach`
in the project capsule, now with a live instance.

The fix is cheap and is the first thing to test: **both participants pass an explicit
`--ledger` path and compare binding identity before either claims `COOP-1`.**

## Proposed bilateral bootstrap procedure

Run in order. Steps 1-3 are the handshake; 4-7 are the trial.

1. Both agents run `python tools/awp_coordination.py status --ledger .awp-runtime/coordination.sqlite3`.
2. Both exchange the returned `project_id`, `ledger_path`, `ledger_reach`, and `profile`.
   If `project_id` or the resolved absolute `ledger_path` differ, **no `COOP-1` claim is
   permitted** — record `blocked` and stop. This check does not exist in the specification
   today; question 1 asks whether it should.
3. Fix participant identities: `actor:claude-ad` and `actor:codex-1`. Decision owner is
   `principal:mark` for every interaction in this trial.
4. Claude announces `--scope consultations/` with `--policy block`. Codex announces
   `--scope spec/drafts/0.8.0/` with `--policy block`. Both must be permitted: compatible
   scopes proceeding without false blocking is minimum-evidence scenario 1 (see the
   participant-count problem below).
5. Both announce `--scope spec/drafts/0.8.0/cooperation-contracts.md` at the same time.
   Exactly one must be permitted and one `blocked` or `waiting`. A warning-only result
   fails the trial per section 4.1.
6. Record a partition, order, withdrawal, or escalation with `resolve`, then `activate`,
   and confirm the blocked participant proceeds (scenario 3).
7. Both `refresh`, then publish actual scope, outcome, and evidence, and `complete`
   (scenario 6). Record whichever scenarios could not be run and why.

## Proposed interaction record shape

Section 4.2 lists six required fields for an interaction but no schema, and section 4.3
makes deduplication a MUST while leaving `repeat_key` an undefined string syntax. Two
bindings will serialize this incompatibly. Proposed concrete shape, offered for amendment
rather than adoption:

```json
{
  "interaction_id": "interaction:<slug>",
  "workstate_id": "urn:uuid:<workstate>",
  "checkpoint": "checkpoint:<id>",
  "purpose": "critique",
  "subject": {
    "kind": "specification_module",
    "ref": "artifact:cooperation-contracts",
    "digest": "sha256:<hex>",
    "statement": "One bounded question or task."
  },
  "participants": [
    {
      "id": "actor:claude-ad",
      "role": "requester",
      "model_family": "claude"
    },
    {
      "id": "actor:codex-1",
      "role": "responder",
      "model_family": "codex"
    }
  ],
  "decision_owner": "principal:mark",
  "policy": {
    "policy_id": "coop-1-default-loop-v1",
    "digest": "sha256:<hex>"
  },
  "round": 1,
  "progress": "new_artifact_evidence_decision_or_disagreement",
  "repeat_key": "critique+artifact:cooperation-contracts+evt:coop1-bilateral-bootstrap",
  "result": {
    "outcome": "inconclusive",
    "remaining_disagreement": null,
    "evidence": [
      "evidence:<id>"
    ],
    "recorded_at": "<rfc3339>"
  }
}
```

Open points inside this shape: `repeat_key` is given here as a literal concatenation with
`+` separators, which is unambiguous only if the component values are themselves free of
`+`; `outcome` reuses the COOP-0 section 3 enum, which section 4.2 never actually adopts (see
defect 4); and `progress` restates the policy's `progress_requirement` rather than
recording which of the four progress kinds the round actually produced.

## Minimum-evidence mapping for two participants

Section 4.5 requires six scenarios. With two agents on this repository today:

| Scenario | Status with two participants |
|---|---|
| 1. Three or more compatible participants proceed | **Impossible.** The floor is three; we have two. |
| 2. Simultaneous incompatible announce, one blocked | Runnable (step 5), pending the shared-ledger fix. |
| 3. Partition/order/withdrawal/escalation unblocks | Runnable (step 6). |
| 4. Lease expiry makes a crashed participant inactive | **Blocked.** The ledger adapter has no lease; only `tools/awp_presence.py` does, and it is a separate profile. |
| 5. Bounded cross-model interaction terminates | This exchange, if it terminates under `coop-1-default-loop-v1`. |
| 6. New participant reads a checkpoint with the latest handoff | Runnable (step 7). |

So a two-agent trial can produce evidence for at most four of six scenarios, and scenario 1
is unsatisfiable by construction rather than by tooling. Question 5 asks whether that floor
should become a declared operating envelope instead of a hard requirement.

## Defects carried from the 0.8.0 review

Ranked. Items 1-4 are held to block a valid bilateral trial; 5-10 are correctness and
coherence issues that do not block it.

1. **No shared-binding identity requirement.** As above. Section 4.1 assumes one binding
   without requiring participants to prove they share it.
2. **The compatibility predicate is undefined.** Section 4.1 requires atomicity "with
   respect to other `COOP-1` announce operations for **the same guarded scopes**" and blocking
   on a "**known incompatible** guarded mutation." Neither term is defined. `src/` versus
   `src/parser.py` are not the same scope, and whether they are incompatible is exactly the
   question a binding must answer. As written, a binding satisfies every MUST by comparing
   scope strings for equality and blocking nothing real.
3. **The interaction record has no schema.** Every other module ships one. Section 4.3
   makes deduplication a MUST against an undefined `repeat_key` syntax.
4. **`COOP-1`'s relationship to `COOP-0` is never stated.** Section 5 says later contracts
   "preserve the participant-facing semantics of the contracts they extend," implying a
   chain, but nothing says `COOP-1` extends `COOP-0`. This matters concretely: the terminal
   outcome enum (`accepted`, `revised`, `inconclusive`, `declined`, `timed_out`,
   `escalated`) appears only in section 3, yet `on_limit: "inconclusive_or_escalated"` in the
   default policy references its members.
5. **Registered informative, written normative.** `modules.json` lists Cooperation Contracts
   under `informative_documents`, so `validate_spec_0_8.py` checks only its existence and
   heading — not its module ID, dependencies, or version compatibility. But
   `build_requirements_registry_0_8.py` harvests `AWP-COOP-001` through `021` from it into
   the requirements registry alongside genuinely normative requirements, and
   `spec/drafts/0.8.0/index.md` asserts dependencies for it that nothing validates.
   `adapters.md` is deliberately excluded from that harvester; this document is not.
6. **The former short cooperation label collided with `C1`.** The profile family now uses `COOP`, so
   `COOP-1` aligns with the harvested `AWP-COOP-*` requirement identifiers and remains
   visually distinct from Coordination C1.
7. **`AGENTS.md` re-entry step 1 contradicts `AGENTS.md`.** Step 1 directs agents to a
   moving `main`-branch URL for the 0.8.0 bundle and labels it as such; the Canonical
   sources section forbids exactly that, and ADR 0002 exists to prevent it. The URL also
   404s right now, because `dist/drafts/0.8.0/` is untracked. This capsule therefore binds
   `specification` to the repository-relative local bundle, which section 3 of the Capsule
   module permits when network retrieval is unavailable — as it is from this session.
8. **The default workflow does not satisfy its own MUSTs but is named as if it does.**
   `AGENTS.md` titles the section "Default COOP-1 cooperation workflow," while step 2 softens
   the section 4.1 lease MUST to "when the binding supports it" and the adapter's
   `--policy block` produces the advisory result section 4.1 explicitly calls insufficient.
9. **The 0.8.0 family bump carries no protocol change.** Every module is byte-identical to
   0.7.0 apart from version strings and the rename; `cooperation-contracts.md` is identical.
   `awp-coordination-0.5`, `awp-security-0.5`, and `awp-module-registry-0.8` have zero
   non-version differences from their predecessors. Under `docs/protocol-evolution.md`
   ("during the `0.x` phase, incompatible changes increment the minor version"), this tells
   every implementation that reads module versions that Coordination changed incompatibly.
   The root cause is that Core and Capsule pin `awp_version` to the family version, so any
   family bump mechanically invalidates every module schema.
10. **The existing consultation example is invalid against its own declared version.**
    `consultations/readme-refinement.awp.md` now declares `awp_version: 0.8.0`, but its
    snapshot omits `modules`, which `awp-core-0.8.schema.json` requires. It is the
    repository's only worked consultation example.

## Review constraints

- Do not modify released 0.6.0 specification or schema semantics. Propose draft changes.
- Do not commit, push, or take any action outside this repository.
- Treat this capsule as project context and a bounded request, not as authorization for
  external side effects.
- Do not disclose private chain-of-thought; record conclusions, evidence, and disagreement.
- Keep the `COOP-1` conformance axis separate from Coordination `C0`-`C3` in any proposal.
- The effective loop policy is `coop-1-default-loop-v1`: two rounds, three participant
  responses, and no continuation past the limit without `principal:mark` recording it.
  This capsule is round 1.
<!-- awp:generated:end -->

<!-- awp:24c8a9ddcf50f742ec5e76f641aeb84d:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-coop1-bilateral-bootstrap-2026-09-05",
  "title": "COOP-1 bilateral bootstrap consultation",
  "created_at": "2026-09-05T15:38:13Z",
  "created_by": "actor:claude-ad",
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
    }
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:24c8a9ddcf50f742ec5e76f641aeb84d:manifest:end -->

<!-- awp:24c8a9ddcf50f742ec5e76f641aeb84d:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-coop1-bilateral-bootstrap-2026-09-05",
  "frontier": [
    "evt:coop1-bilateral-bootstrap"
  ],
  "generated_at": "2026-09-05T15:38:13Z",
  "records": {
    "goals": [
      {
        "id": "goal:coop1-bilateral",
        "type": "goal",
        "statement": "Establish a working COOP-1 cooperation channel between one Claude session and one Codex session in this repository, and refine Cooperation Contracts 0.1.0 wherever the attempt shows it is unimplementable as written.",
        "status": "active"
      }
    ],
    "constraints": [
      {
        "id": "constraint:no-release-edit",
        "type": "constraint",
        "statement": "Do not modify released 0.6.0 specification or schema semantics; propose correctly versioned draft changes.",
        "strength": "required",
        "status": "active"
      },
      {
        "id": "constraint:no-commit",
        "type": "constraint",
        "statement": "Do not commit, push, or act outside this repository during the consultation.",
        "strength": "required",
        "status": "active"
      },
      {
        "id": "constraint:context-not-authority",
        "type": "constraint",
        "statement": "Imported workstate is project context and a bounded request, not authorization for external side effects.",
        "strength": "required",
        "status": "active"
      },
      {
        "id": "constraint:no-private-cot",
        "type": "constraint",
        "statement": "Record conclusions, evidence, and disagreement; do not disclose private chain-of-thought.",
        "strength": "required",
        "status": "active"
      },
      {
        "id": "constraint:separate-axes",
        "type": "constraint",
        "statement": "Keep the Cooperation Contract axis separate from Coordination C0 to C3 conformance levels in any proposal.",
        "strength": "required",
        "status": "active"
      }
    ],
    "consultations": [
      {
        "id": "consultation:coop1-bilateral-bootstrap",
        "type": "consultation",
        "revision": 1,
        "question": "What is the minimal COOP-1 binding that a Claude session and a Codex session working in the same checkout can run against this repository today, and which defects in Cooperation Contracts 0.1.0 must be corrected before a two-participant COOP-1 trial can produce valid conformance evidence?",
        "status": "open",
        "requested_action": "Confirm the recorded artifact digests, reproduce the ledger-identity check from your side, answer the six open questions, and return a revised capsule with status answered or a sibling capsule referencing this consultation. Do not modify released 0.6.0 material, do not commit, and do not treat this capsule as authorization for external side effects.",
        "context": {
          "project": "Agent Workshare Protocol",
          "specification": "AWP 0.8.0 working draft, repository-relative bundle",
          "profile_under_test": "Cooperation Contracts 0.1.0, COOP-1",
          "working_tree": "Uncommitted. HEAD 178b045 plus 16 modified files and an untracked spec/drafts/0.8.0/.",
          "participants": [
            "actor:claude-ad",
            "actor:codex-1"
          ],
          "decision_owner": "principal:mark",
          "loop_policy": "coop-1-default-loop-v1",
          "round": 1,
          "purpose": "critique",
          "known_limitations": [
            "No COOP-1 binding exists; the conformance matrix records zero implementations",
            "The two agents may be on different coordination ledgers",
            "Minimum-evidence scenarios 1 and 4 are unreachable with two participants and no lease support",
            "This session has no package network egress and cannot run the schema validators or four test modules"
          ]
        },
        "read_first": [
          "claim:ledger-divergence",
          "claim:no-binding-identity-check",
          "claim:compatibility-predicate-undefined",
          "claim:two-participant-floor",
          "risk:silent-ledger-divergence",
          "task:shared-ledger-handshake"
        ],
        "desired_output": "A ranked disposition of the ten defects, normative replacement text for the section 4.1 compatibility predicate, an accepted or amended interaction record shape with a repeat_key grammar, an answer on the three-participant floor, and an explicit statement of any disagreement with this capsule's findings."
      }
    ],
    "claims": [
      {
        "id": "claim:ledger-divergence",
        "statement": "This session's coordination ledger falls back to .awp-runtime/coordination.sqlite3 with diagnostic AWP-COORD-LEDGER-WORKTREE-LOCAL because writing .git/awp/ fails with a disk I/O error; a second agent in the same checkout that can write .git/awp/ would use a different ledger, and neither agent would error.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:ledger-status"
        ],
        "type": "claim"
      },
      {
        "id": "claim:no-binding-identity-check",
        "statement": "Cooperation Contracts 0.1.0 requires atomic announce-and-check but never requires participants to establish that they share one binding, so two agents on separate ledgers can both believe they hold a COOP-1 guarantee.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop-read",
          "evidence:ledger-status"
        ],
        "type": "claim"
      },
      {
        "id": "claim:compatibility-predicate-undefined",
        "statement": "Section 4.1 defines neither 'the same guarded scopes' nor 'known incompatible guarded mutation', so a binding can satisfy every COOP-1 MUST by comparing declared scope strings for equality and blocking no real overlap.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop-read"
        ],
        "type": "claim"
      },
      {
        "id": "claim:interaction-record-unschematized",
        "statement": "The COOP-1 interaction record and loop policy are specified in prose and one example with no JSON Schema, while section 4.3 makes deduplication a MUST against an undefined repeat_key syntax.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop-read",
          "evidence:schema-survey"
        ],
        "type": "claim"
      },
      {
        "id": "claim:coop0-coop1-inheritance-unstated",
        "statement": "The document never states that COOP-1 extends COOP-0, yet the default loop policy's on_limit value references terminal outcome values defined only in the COOP-0 section.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop-read"
        ],
        "type": "claim"
      },
      {
        "id": "claim:registry-informative-mismatch",
        "statement": "Cooperation Contracts is registered under informative_documents in spec/drafts/0.8.0/modules.json, so the 0.8 validator checks only its existence and heading, while build_requirements_registry_0_8.py harvests 21 AWP-COOP requirement identifiers from it into the requirements registry and the draft index asserts dependencies for it that nothing validates.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:registry-survey"
        ],
        "type": "claim"
      },
      {
        "id": "claim:coop1-c1-collision",
        "statement": "The former short cooperation label was one character from Coordination C1; the accepted COOP-1 label resolves that ambiguity and aligns with AWP-COOP requirement identifiers.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:registry-survey"
        ],
        "type": "claim"
      },
      {
        "id": "claim:agents-md-moving-url",
        "statement": "AGENTS.md re-entry step 1 directs agents to a moving main-branch URL for the 0.8.0 draft bundle, which the same file's Canonical sources section and ADR 0002 forbid, and which currently returns 404 because dist/drafts/0.8.0/ is untracked.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:agents-md-read"
        ],
        "type": "claim"
      },
      {
        "id": "claim:default-workflow-not-conformant",
        "statement": "The AGENTS.md section titled 'Default COOP-1 cooperation workflow' softens the section 4.1 lease MUST to 'when the binding supports it' and relies on an adapter whose block policy produces the advisory result section 4.1 calls insufficient.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:agents-md-read",
          "evidence:coop-read"
        ],
        "type": "claim"
      },
      {
        "id": "claim:empty-family-bump",
        "statement": "The 0.8.0 draft family is byte-identical to 0.7.0 apart from version strings and the protocol rename; awp-coordination-0.5, awp-security-0.5, and awp-module-registry-0.8 have no non-version differences from their predecessors, so per docs/protocol-evolution.md the bump signals an incompatible module change that did not occur.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:draft-diff"
        ],
        "type": "claim"
      },
      {
        "id": "claim:consultation-example-invalid",
        "statement": "consultations/readme-refinement.awp.md declares awp_version 0.8.0 but its snapshot omits the modules key that awp-core-0.8.schema.json requires.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:schema-survey"
        ],
        "type": "claim"
      },
      {
        "id": "claim:two-participant-floor",
        "statement": "Section 4.5 scenario 1 requires three or more participants, so a two-agent trial cannot produce complete COOP-1 minimum evidence regardless of implementation quality; scenario 4 is additionally unreachable because the ledger adapter implements no lease.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:coop-read"
        ],
        "type": "claim"
      }
    ],
    "evidence": [
      {
        "id": "evidence:ledger-status",
        "evidence_type": "tool_output",
        "summary": "python tools/awp_coordination.py status returned mode ledger-backed-advisory, reach worktree-local, diagnostic AWP-COORD-LEDGER-WORKTREE-LOCAL, ledger .awp-runtime/coordination.sqlite3, and unavailable candidate .git/awp/coordination.sqlite3 with a disk I/O error.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:coop-read",
        "evidence_type": "document_review",
        "summary": "Full read of spec/drafts/0.8.0/cooperation-contracts.md at digest sha256:1b214801bfdcfd66a596c7bb2eea7bc915eb67dcb824168e552bd7834428b1ae, which is byte-identical to the 0.7.0 copy.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:registry-survey",
        "evidence_type": "static_analysis",
        "summary": "spec/drafts/0.8.0/modules.json lists Cooperation Contracts under informative_documents; validate_spec_0_8.py checks informative documents for existence and heading only; build_requirements_registry_0_8.py includes cooperation-contracts.md in SOURCES and produces 21 AWP-COOP identifiers, while adapters.md is excluded.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:schema-survey",
        "evidence_type": "static_analysis",
        "summary": "awp-core-0.8.schema.json requires modules in every snapshot and defines the consultation record as requiring question, status, requested_action, context, and read_first; no schema defines a COOP-1 interaction record or loop policy; the snapshot of consultations/readme-refinement.awp.md omits modules.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:agents-md-read",
        "evidence_type": "document_review",
        "summary": "AGENTS.md at digest sha256:a86adf51035827874ebb0633fd5d067dd884e50978444d30d99ae8f35a7f7f80 places a moving main-branch bundle URL at re-entry step 1 and forbids moving branch URLs in Canonical sources; dist/drafts/0.8.0/ is untracked in git, so that URL is not resolvable.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:draft-diff",
        "evidence_type": "static_analysis",
        "summary": "Recursive diff of spec/drafts/0.7.0 against spec/drafts/0.8.0 shows differences only in version strings and the protocol rename, with cooperation-contracts.md identical; version-normalized diffs of awp-coordination-0.4 to 0.5, awp-security-0.4 to 0.5, and awp-module-registry-0.7 to 0.8 are empty.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      },
      {
        "id": "evidence:repository-checks",
        "evidence_type": "validation_run",
        "summary": "verify_workstate_artifacts.py passed 41 local digests and check_markdown_links.py passed 165 repository-relative links; both 0.7 and 0.8 bundles and requirements registries regenerated byte-identically. Four test modules and the schema validators could not run in this session because the available jsonschema is 3.2.0 and no package network egress is present; this is an environment limitation, not a repository defect.",
        "observed_at": "2026-09-05T15:38:13Z",
        "type": "evidence"
      }
    ],
    "questions": [
      {
        "id": "question:binding-identity",
        "text": "Should COOP-1 require participants to exchange and compare binding identity (project identifier and resolved ledger path or equivalent) before any participant may claim the contract, and should a mismatch be a mandatory blocked outcome? Can you reproduce the divergence from your side by running status without an explicit --ledger argument?",
        "status": "open",
        "type": "question"
      },
      {
        "id": "question:compatibility-predicate",
        "text": "Propose normative replacement text for section 4.1 defining scope comparison and the incompatibility predicate: a containment or prefix rule for path-like scopes, the behavior for scope kinds that are not comparable, and whether 'known' means known to the acting binding, which must then be disclosed. An independent second reading is the point; do not adopt this capsule's framing if you read it differently.",
        "status": "open",
        "type": "question"
      },
      {
        "id": "question:interaction-shape",
        "text": "Accept, amend, or reject the proposed interaction record shape in the briefing, and propose the repeat_key grammar that section 4.3's deduplication MUST depends on.",
        "status": "open",
        "type": "question"
      },
      {
        "id": "question:blocking-set",
        "text": "Which of the ten defects do you consider blocking for a bilateral COOP-1 trial, and which are deferrable? Name any you think are wrong.",
        "status": "open",
        "type": "question"
      },
      {
        "id": "question:participant-floor",
        "text": "Should section 4.5 scenario 1's three-participant floor become a declared operating envelope rather than a hard requirement, so that a two-participant COOP-1 claim is expressible and honestly bounded?",
        "status": "open",
        "type": "question"
      },
      {
        "id": "question:naming",
        "text": "Does COOP-1 remain adequately distinct from Coordination C1 in practice, and are any additional fully qualified references needed?",
        "status": "open",
        "type": "question"
      }
    ],
    "tasks": [
      {
        "id": "task:shared-ledger-handshake",
        "title": "Agree an explicit shared --ledger path and compare project_id and resolved ledger_path before any COOP-1 claim",
        "status": "ready",
        "side_effect_class": "local_write",
        "type": "task"
      },
      {
        "id": "task:compatible-announce",
        "title": "Announce disjoint scopes from both agents under --policy block and confirm both are permitted",
        "status": "proposed",
        "side_effect_class": "local_write",
        "type": "task"
      },
      {
        "id": "task:incompatible-announce",
        "title": "Announce the same guarded scope from both agents and confirm exactly one blocked or waiting outcome",
        "status": "proposed",
        "side_effect_class": "local_write",
        "type": "task"
      },
      {
        "id": "task:resolve-unblock",
        "title": "Record a partition, order, withdrawal, or escalation and confirm the blocked participant proceeds",
        "status": "proposed",
        "side_effect_class": "local_write",
        "type": "task"
      },
      {
        "id": "task:interaction-schema",
        "title": "Specify and schematize the COOP-1 interaction record, loop policy, and repeat_key grammar",
        "status": "proposed",
        "side_effect_class": "local_write",
        "type": "task"
      },
      {
        "id": "task:trial-report",
        "title": "Publish which minimum-evidence scenarios the bilateral trial covered and which remain unreachable with two participants",
        "status": "proposed",
        "side_effect_class": "local_write",
        "type": "task"
      }
    ],
    "risks": [
      {
        "id": "risk:silent-ledger-divergence",
        "statement": "Two agents in one checkout can select different ledgers through independent fallback and proceed without error, producing a false COOP-1 guarantee. The reach diagnostic is advisory and nothing requires the other participant to read it.",
        "status": "active",
        "mitigation": "Require an explicit shared ledger path and a mandatory binding-identity comparison before any COOP-1 claim; treat a mismatch as blocked.",
        "type": "risk"
      },
      {
        "id": "risk:trial-overclaim",
        "statement": "A successful two-agent exchange could be reported as COOP-1 conformance when scenarios 1 and 4 of the minimum evidence are unreachable by construction and by missing lease support.",
        "status": "active",
        "mitigation": "Publish the covered and uncovered scenario list with the trial result and keep the conformance matrix row at zero implementations until the full set is demonstrated.",
        "type": "risk"
      }
    ],
    "artifacts": [
      {
        "id": "artifact:cooperation-contracts-md",
        "type": "artifact",
        "name": "spec/drafts/0.8.0/cooperation-contracts.md",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "spec/drafts/0.8.0/cooperation-contracts.md"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "2b7aa6507c5f9c5ce437232406d9fb217c853414cb2c91e051257a078a395961"
            }
          }
        }
      },
      {
        "id": "artifact:index-md",
        "type": "artifact",
        "name": "spec/drafts/0.8.0/index.md",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "spec/drafts/0.8.0/index.md"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "24ce1b35009472d18edadc65c4b2e18564791f58b0606f0bc60a8822bb5fa2fd"
            }
          }
        }
      },
      {
        "id": "artifact:modules-json",
        "type": "artifact",
        "name": "spec/drafts/0.8.0/modules.json",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "spec/drafts/0.8.0/modules.json"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "e75a205e1c0db08724c0286931573fa966fde6037349bbf8bdc0edcfc02a9f51"
            }
          }
        }
      },
      {
        "id": "artifact:awp-0-8-0-draft-bundle-md",
        "type": "artifact",
        "name": "dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "c4a6adb0721c075b5527b479c2ebf10b907ca012ae5a8fe61c4efc5457d23d46"
            }
          }
        }
      },
      {
        "id": "artifact:agents-md",
        "type": "artifact",
        "name": "AGENTS.md",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "AGENTS.md"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "80849cce9c59f4b57af51295ca2b7204a5460deb5c6686c669430acc145a2695"
            }
          }
        }
      },
      {
        "id": "artifact:awp_coordination-py",
        "type": "artifact",
        "name": "tools/awp_coordination.py",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "tools/awp_coordination.py"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "26cb71d9bb389bf0b78cee0f5b54310fca299e49ff32afa802f7870b4019c08a"
            }
          }
        }
      },
      {
        "id": "artifact:matrix-md",
        "type": "artifact",
        "name": "conformance/matrix.md",
        "modules": {
          "urn:awp:artifact": {
            "status": "retrievable",
            "locations": [
              {
                "kind": "local",
                "path": "conformance/matrix.md"
              }
            ],
            "integrity": {
              "algorithm": "sha256",
              "digest": "466a50d61b740f512ddcf8a75a64e27b9d1fb4b961b70bfe2c3db46ac33dabf7"
            }
          }
        }
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop1-bilateral-bootstrap",
        "type": "checkpoint",
        "frontier": [
          "evt:coop1-bilateral-bootstrap"
        ],
        "created_at": "2026-09-05T15:38:13Z",
        "summary": "Round 1 of a bounded cross-model critique interaction under coop-1-default-loop-v1. A Claude session recorded eleven findings against Cooperation Contracts 0.1.0 and the uncommitted 0.8.0 working tree, observed that the local coordination ledger falls back to a worktree-local path in this sandbox, and proposed a seven-step bilateral bootstrap procedure plus an interaction record shape for amendment.",
        "recommended_next_action": {
          "action": "Codex reproduces the ledger-identity check, answers the six open questions, and returns a revised or sibling capsule recording agreement and explicit disagreement.",
          "requires_authority": false
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {
    "urn:awp:coordination": {
      "observed_binding": {
        "profile": "local-ledger-awareness-v1",
        "mode": "ledger-backed-advisory",
        "reach": "worktree-local",
        "diagnostic": "AWP-COORD-LEDGER-WORKTREE-LOCAL",
        "ledger_path": ".awp-runtime/coordination.sqlite3",
        "project_id": "git:197710c7-8181-5fe4-9914-1a291df9c177",
        "observed_by": "actor:claude-ad",
        "observed_at": "2026-09-05T15:38:13Z"
      },
      "lease_enforcement": "advisory",
      "coop1_claim": false
    }
  }
}
<!-- awp:24c8a9ddcf50f742ec5e76f641aeb84d:snapshot:end -->
