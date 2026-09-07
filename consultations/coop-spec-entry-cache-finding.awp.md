---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 2f8a4c6e0b3d5197c4e2a0b8d6f3e719
workstate_id: urn:uuid:awp-coop-spec-entry-cache-finding-2026-09-06
frontier:
  - evt:coop-spec-entry-cache-finding
checkpoint: checkpoint:coop-spec-entry-cache-finding
generated_at: 2026-09-06T00:12:00Z
generated_digest: sha256:5caf9a27505ae1927dbaf15784ae6ca23c627b7ac570ad088f353c963e461377
---
<!-- awp:generated:start -->
# Spec-entry cache freshness key — finding

`actor:claude-review` records one finding for `actor:codex-*`'s in-progress, uncommitted work
on `tools/awp_spec_entry.py` and the `AGENTS.md` re-entry step it backs. This is advice only:
no protocol source, schema, or workstate file was modified to produce it, and no ledger lease
was entered, matching the COOP-0-style handling of the prior architecture consultation. This
capsule is time-sensitive: it concerns a file that is currently uncommitted and under active
edit, so please check the working tree before acting on it.

## The question that prompted this

`principal:mark` asked whether `AGENTS.md` could tell an agent to persist caching the
specification file longer than default when its version number is unchanged. The direct answer
was no, not safely, in this repository specifically — and the working tree already confirms why.

## Finding: `awp_version` is a family label here, not a per-edit counter

`spec/drafts/0.8.0/cooperation-contracts.md` declared `Cooperation Contracts 0.1.0` across all
four of its substantive 0.8-draft commits: `f000a2f` (defined the COOP contracts), `2e1cd1b`
(hardened binding integrity and checkpoints), `3c9418b` (workstate projection), and `5a30c74`
(the cooperation/coordination unification, which rewrote large parts of the document). The
version string never moved while the normative content did, repeatedly, in one working day. A
cache keyed on "version number unchanged" would have kept serving a stale reading through all
three of those later changes.

## What the working tree already does about this, and it is correct

The uncommitted `tools/awp_spec_entry.py` and the matching uncommitted `AGENTS.md` re-entry step
1 already key the generated Agent Entry Core's validity on the full bundle's SHA-256 digest, not
on `awp_version`, and hold it valid indefinitely with no time expiry as long as that digest still
matches (`verify()`'s `state: "current"` branch). This is confirmed working right now:
`python tools/awp_spec_entry.py --verify` returns `state: current` against the present working
tree. This is the right freshness key for a document whose version label does not track its
edits, and it should not be changed to a version-number check.

## The remaining gap: no session-scoped skip for the verify call itself

`AGENTS.md` step 1, as currently drafted uncommitted, still runs `python
tools/awp_spec_entry.py --verify` unconditionally on every re-entry, inside one continuous
session as much as across sessions. The check itself is cheap, so this is not a correctness
problem, only a redundant-call one. If the goal behind the original question was also to reduce
that redundancy, the safe form is a session-scoped rule, not a time- or version-based one:
an agent that has already observed `state: current` for a given source-bundle digest earlier in
its own continuous session MAY skip re-running `--verify` again in that same session, provided
it has no reason to believe the bundle changed since — it did not itself edit a spec, schema, or
tooling file, and it has not been told another participant did. It MUST re-run `--verify` on a
new session, after editing any file under `spec/drafts/0.8.0/`, `schemas/`, or
`tools/awp_spec_entry.py` itself, or after any indication (a capsule, a checkpoint, a ledger
event) that another participant may have changed the bundle. This adds no new freshness key; it
only says the existing digest check need not be repeated when nothing could plausibly have
invalidated it.

## Recommended next step

Fold one sentence adding that session-scoped allowance into `AGENTS.md` re-entry step 1 when
this in-progress change is otherwise ready to commit; no schema or tooling change is required,
since the digest mechanism doing the real work is already correct as built. No remaining
disagreement is known; this is a documentation refinement, not a defect in what already landed.
<!-- awp:generated:end -->

<!-- awp:2f8a4c6e0b3d5197c4e2a0b8d6f3e719:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-spec-entry-cache-finding-2026-09-06",
  "title": "Spec-entry cache freshness key — finding",
  "created_at": "2026-09-06T00:12:00Z",
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
    }
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:2f8a4c6e0b3d5197c4e2a0b8d6f3e719:manifest:end -->

<!-- awp:2f8a4c6e0b3d5197c4e2a0b8d6f3e719:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-spec-entry-cache-finding-2026-09-06",
  "frontier": [
    "evt:coop-spec-entry-cache-finding"
  ],
  "generated_at": "2026-09-06T00:12:00Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop-spec-entry-cache-finding",
        "type": "consultation",
        "revision": 1,
        "status": "open",
        "question": "Should the AGENTS.md re-entry step for the Agent Entry Core add a session-scoped allowance to skip a redundant --verify call, without changing its digest-based freshness key to the specification version number?",
        "requested_action": "Consider folding the session-scoped skip allowance into the in-progress, uncommitted AGENTS.md re-entry step 1 before it is committed. No code or schema change is proposed; the digest mechanism already built is correct as is.",
        "context": {
          "base_revision": "git:5a30c74378c0d7bc89022dff6f830dba41f07d39",
          "prompted_by": "principal:mark asked whether the specification file's cache could persist longer than default when its version number is unchanged",
          "decision_owner": "principal:mark",
          "entry_tool_verify_state": "current"
        },
        "read_first": [
          "claim:version-label-does-not-track-edits",
          "claim:digest-key-already-correct",
          "claim:verify-call-redundant-within-session"
        ],
        "desired_output": "A decision on whether to add the session-scoped verify-skip sentence to AGENTS.md, or an explanation of why the current unconditional per-re-entry verify call is preferred."
      }
    ],
    "claims": [
      {
        "id": "claim:version-label-does-not-track-edits",
        "type": "claim",
        "statement": "spec/drafts/0.8.0/cooperation-contracts.md declared version 0.1.0 unchanged across commits f000a2f, 2e1cd1b, 3c9418b, and 5a30c74, each of which materially changed its normative content, showing awp_version is a family label rather than a per-edit counter in this repository.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:version-pinned-across-commits"
        ]
      },
      {
        "id": "claim:digest-key-already-correct",
        "type": "claim",
        "statement": "The uncommitted tools/awp_spec_entry.py keys Agent Entry Core validity on the full bundle's SHA-256 digest with no time expiry, and python tools/awp_spec_entry.py --verify currently returns state current against the working tree, confirming the mechanism functions and correctly avoids the version-number gate that would have missed the changes above.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:verify-state-current"
        ]
      },
      {
        "id": "claim:verify-call-redundant-within-session",
        "type": "claim",
        "statement": "AGENTS.md re-entry step 1, as currently drafted uncommitted, runs the verify call unconditionally on every re-entry including repeated re-entries within one continuous session where no participant has changed the bundle, which is redundant though not unsafe.",
        "epistemic_status": "observed",
        "evidence": [
          "evidence:agents-md-diff"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:version-pinned-across-commits",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "git log and per-commit grep of spec/drafts/0.8.0/cooperation-contracts.md at git:5a30c74: the string 'Cooperation Contracts 0.1.0' appears unchanged in f000a2f, 2e1cd1b, 3c9418b, and 5a30c74 despite each commit's diff touching this file's normative sections.",
        "observed_at": "2026-09-06T00:12:00Z"
      },
      {
        "id": "evidence:verify-state-current",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "python3 tools/awp_spec_entry.py --verify against the current working tree returns state current with matching declared and actual source_bundle_sha256.",
        "observed_at": "2026-09-06T00:12:00Z"
      },
      {
        "id": "evidence:agents-md-diff",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "git diff AGENTS.md (uncommitted) shows re-entry step 1 rewritten to run --verify and read the Agent Entry Core on digest match, with no session-scoped condition on repeating that call.",
        "observed_at": "2026-09-06T00:12:00Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop-spec-entry-cache-finding",
        "type": "checkpoint",
        "frontier": [
          "evt:coop-spec-entry-cache-finding"
        ],
        "created_at": "2026-09-06T00:12:00Z",
        "summary": "Finding recorded: the digest-based Agent Entry Core mechanism already in progress is the correct freshness key for this repository, where the specification version label does not track edits; a one-sentence session-scoped verify-skip addition to AGENTS.md would close the remaining redundant-call gap without weakening the freshness key.",
        "recommended_next_action": {
          "action": "actor:codex-* folds the session-scoped allowance into AGENTS.md re-entry step 1 before committing the in-progress spec-entry work, or explains why the unconditional per-re-entry verify call is preferred.",
          "requires_authority": false
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:2f8a4c6e0b3d5197c4e2a0b8d6f3e719:snapshot:end -->
