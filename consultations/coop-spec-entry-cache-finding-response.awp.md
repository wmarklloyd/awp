---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 72d07713693310488462a8858534f959
workstate_id: urn:uuid:awp-coop-spec-entry-cache-response-2026-09-09
frontier:
  - evt:coop-spec-entry-cache-response
checkpoint: checkpoint:coop-spec-entry-cache-response
generated_at: 2026-09-09T20:58:56Z
generated_digest: sha256:b996514a93ef525536b5f7b2f63d4fdba6fd975f35b420016db80d9d8ca03e8f
---
<!-- awp:generated:start -->
# Spec-entry cache freshness key — response

`actor:claude` answers `consultation:coop-spec-entry-cache-finding`, open since 2026-09-06.
The decision owner is `principal:mark`. This is advice only: no protocol source, schema, or
workstate file was modified to produce it, and no ledger lease was entered.

**Recommendation: decline the session-scoped skip allowance. Keep `AGENTS.md` re-entry step 1's
`--verify` call unconditional.** The finding's two substantive claims are re-verified and
affirmed; only its recommended next step is declined.

## 1. The exemption costs more to evaluate than the check it saves

Measured on this host today, three runs each:

| operation | cost |
| --- | --- |
| `python tools/awp_spec_entry.py --verify` | 0.03 s |
| ledger read establishing "no peer changed the bundle" | 0.69–0.97 s |
| `git status --porcelain` for the same purpose | 1.05–1.06 s |

The allowance is conditioned on the agent having "no reason to believe the bundle changed" and
on "no indication another participant may have changed" it. Establishing that precondition
honestly costs 23–35x the check it avoids. The optimization is self-defeating whenever it is
evaluated properly, and when it is not evaluated properly it substitutes an agent's recollection
for a mechanical digest comparison — a worse trade at any price.

## 2. The exemption's own re-run condition now fires in the normal case

When the finding was written, a second participant editing the bundle mid-session was
hypothetical. It is not now. Exploratory COOP-2 is the selected project cooperation level
(`2e9de6b`), and `actor:codex` was active in this repository during this very session: it sent
`interaction:639aa48ab0afb1726c23c240` at 2026-09-09T20:49:04Z, between this actor's entry and
this response. The allowance requires re-verification after any indication that another
participant may have changed the bundle; in a live two-agent project that indication is the
default condition, so the allowance would rarely apply legitimately even if adopted.

## 3. The premise is stale

The requested action was to fold the sentence in "before it is committed." That window closed.
`AGENTS.md` step 1 has since been committed and materially rewritten — it now carries the routed
`--statements` path, the entry slice, and `--register-observation`. Reopening committed
normative bootstrap text to save 30 ms is not the decision that was originally put.

## 4. It reintroduces judgment at the one boundary that was made mechanical

The finding is right that the digest key's value is that it does not depend on interpretation.
The allowance puts interpretation back, conditioned on the agent's account of its own edit
history, at the entry boundary. The capsule's own `do_not_assume` list already warns against
treating a declaration as a verified fact; this would add a sanctioned assumption in exactly
that position.

## Affirmed from the finding

Both substantive claims were re-verified today, not taken on trust.
`spec/drafts/0.8.0/cooperation-contracts.md` still reads `AWP Cooperation Contracts 0.1.0` at
all four of `f000a2f`, `2e1cd1b`, `3c9418b`, and `5a30c74`, confirming the version label does not
track edits. `verify()` is a pure digest comparison returning `state: current` if and only if
the declared and actual `source_bundle_sha256` match, with no time expiry. Keeping the
digest-based freshness key and refusing the version-number gate was correct and remains correct.

## If the redundancy is worth addressing, address it where it is free

Memoize inside the entry tool for the life of one process, or note in step 1 that `--verify` and
`--route` may be issued as a single invocation. Both are host tooling, cost no protocol surface,
and require no judgment from the agent.

## Relationship to the entry-architecture thread

Consistent with the position sent to `actor:codex` in `interaction:639aa48ab0afb1726c23c240`:
this belongs in host caching policy and should acquire no 0.8 specification surface.

## Note for the decision owner

The original finding capsule still records `status: open`. This response does not edit it;
`consultations/coop-level-boundary-request.awp.md` and
`consultations/coop-subprotocol-architecture.awp.md` also still read `open` beside completed
responses. Closing all three is one bookkeeping decision, deliberately left to
`principal:mark`.
<!-- awp:generated:end -->

<!-- awp:72d07713693310488462a8858534f959:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-spec-entry-cache-response-2026-09-09",
  "title": "Spec-entry cache freshness key — response",
  "created_at": "2026-09-09T20:58:56Z",
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
<!-- awp:72d07713693310488462a8858534f959:manifest:end -->

<!-- awp:72d07713693310488462a8858534f959:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-spec-entry-cache-response-2026-09-09",
  "frontier": [
    "evt:coop-spec-entry-cache-response"
  ],
  "generated_at": "2026-09-09T20:58:56Z",
  "records": {
    "consultations": [
      {
        "id": "consultation:coop-spec-entry-cache-finding",
        "type": "consultation",
        "revision": 2,
        "status": "answered",
        "question": "Should the AGENTS.md re-entry step for the Agent Entry Core add a session-scoped allowance to skip a redundant --verify call, without changing its digest-based freshness key to the specification version number?",
        "answer": "No. Keep the unconditional per-re-entry verify call and keep the digest-based freshness key. The proposed allowance costs 23-35x more to evaluate honestly than the check it skips, its own re-run condition now fires in the normal case because a second participant is active in this project, and its premise that AGENTS.md step 1 is still uncommitted is stale.",
        "answered_by": "actor:claude",
        "answered_at": "2026-09-09T20:58:56Z",
        "decision_owner": "principal:mark",
        "disposition": "Recommendation declined on the merits; the finding's two substantive claims are affirmed and were independently re-verified on 2026-09-09.",
        "read_first": [
          "claim:exemption-costlier-than-check",
          "claim:peer-activity-makes-exemption-inapplicable",
          "claim:agents-md-premise-stale",
          "claim:version-label-does-not-track-edits-reverified"
        ]
      }
    ],
    "claims": [
      {
        "id": "claim:exemption-costlier-than-check",
        "type": "claim",
        "statement": "Establishing the proposed allowance's own precondition costs 23-35x the check it would skip: --verify measured 0.03s across three runs, while a coop2 ledger read measured 0.69-0.97s and git status --porcelain measured 1.05-1.06s on the same host.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:timing-comparison"
        ]
      },
      {
        "id": "claim:peer-activity-makes-exemption-inapplicable",
        "type": "claim",
        "statement": "A second participant is active in this project, so the allowance's requirement to re-verify after any indication that another participant may have changed the bundle fires in the normal case: actor:codex sent interaction:639aa48ab0afb1726c23c240 at 2026-09-09T20:49:04Z, between this actor's entry and this response.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:codex-live-interaction"
        ]
      },
      {
        "id": "claim:agents-md-premise-stale",
        "type": "claim",
        "statement": "The requested action targeted an uncommitted AGENTS.md re-entry step 1; that step has since been committed and materially rewritten to add the routed --statements path, the entry slice, and --register-observation, so the original request's premise no longer holds.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:agents-md-current-text"
        ]
      },
      {
        "id": "claim:version-label-does-not-track-edits-reverified",
        "type": "claim",
        "statement": "The finding's claim:version-label-does-not-track-edits was independently re-verified on 2026-09-09: spec/drafts/0.8.0/cooperation-contracts.md reads 'AWP Cooperation Contracts 0.1.0' at each of f000a2f, 2e1cd1b, 3c9418b, and 5a30c74. The finding's claim:digest-key-already-correct was likewise re-verified: verify() compares declared to actual source_bundle_sha256 with no time expiry.",
        "epistemic_status": "verified",
        "evidence": [
          "evidence:version-recheck",
          "evidence:verify-source-read"
        ]
      }
    ],
    "evidence": [
      {
        "id": "evidence:timing-comparison",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Three timed runs each on 2026-09-09: python tools/awp_spec_entry.py --verify at 0.03s x3; python -m tools.awp_coop2 inbox --actor actor:claude at 0.97s, 0.69s, 0.94s; git status --porcelain at 1.06s, 1.05s, 1.06s.",
        "observed_at": "2026-09-09T20:58:56Z"
      },
      {
        "id": "evidence:codex-live-interaction",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "coop2-rendezvous ledger event evt:d1229395-7520-421a-b85d-ee57046707f5, kind coop2.interaction.requested, actor actor:codex, occurred_at 2026-09-09T20:49:04Z, parent evt:6ed91614 (this actor's send), demonstrating a second participant acting in the project within this session.",
        "observed_at": "2026-09-09T20:58:56Z"
      },
      {
        "id": "evidence:agents-md-current-text",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "Committed AGENTS.md step 1 reads 'Before work, run python tools/awp_spec_entry.py --verify; its digest must match that bundle', with no session-scoped condition; step 2 adds the routed --statements path and step 4 the entry slice and --register-observation, none of which existed in the uncommitted draft the finding examined.",
        "observed_at": "2026-09-09T20:58:56Z"
      },
      {
        "id": "evidence:version-recheck",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "git show <sha>:spec/drafts/0.8.0/cooperation-contracts.md for f000a2f, 2e1cd1b, 3c9418b and 5a30c74 each returns the heading '# AWP Cooperation Contracts 0.1.0'.",
        "observed_at": "2026-09-09T20:58:56Z"
      },
      {
        "id": "evidence:verify-source-read",
        "type": "evidence",
        "evidence_type": "document_review",
        "summary": "tools/awp_spec_entry.py verify() returns state 'current' if declared == expected else 'stale', where expected is profile_data()['source_bundle_sha256']; no TTL, mtime, or version comparison appears in the function.",
        "observed_at": "2026-09-09T20:58:56Z"
      }
    ],
    "checkpoints": [
      {
        "id": "checkpoint:coop-spec-entry-cache-response",
        "type": "checkpoint",
        "frontier": [
          "evt:coop-spec-entry-cache-response"
        ],
        "created_at": "2026-09-09T20:58:56Z",
        "summary": "consultation:coop-spec-entry-cache-finding answered: keep the unconditional verify call and the digest-based freshness key; the session-scoped skip allowance is declined because establishing its precondition costs more than the check, a second participant is now active, and its uncommitted-AGENTS.md premise is stale.",
        "recommended_next_action": {
          "action": "principal:mark accepts or overrides the recommendation, and separately decides whether to close the status: open records still carried by this finding and by the coop-level-boundary and coop-subprotocol-architecture requests.",
          "requires_authority": true
        },
        "resumption_level": "semantic"
      }
    ]
  },
  "modules": {}
}
<!-- awp:72d07713693310488462a8858534f959:snapshot:end -->
