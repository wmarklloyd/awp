---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
workstate_id: urn:uuid:awp-coop1-current-protocol-review-2026-09-05
frontier:
  - evt:17d857a5-c249-4bd1-a918-d71ae4cea018
checkpoint: checkpoint:coop1-current-protocol-review
generated_at: 2026-09-05T18:14:27Z
generated_digest: sha256:f09e2e281b8108d012c2bdcf82f653b68fed8b92080cdebd8e667a0ac6955082
---

<!-- awp:generated:start -->
# COOP-1 current-protocol bilateral review

This is a bounded `critique` interaction intended to exercise COOP-1 with two
independent agents. It is not a COOP-1 conformance claim until both participants
complete the shared-binding procedure and record the terminal outcome.

## Required shared-binding handshake

Both participants use this exact ledger path relative to this repository:

```text
.awp-runtime/coop1-current-review.sqlite3
```

Before reviewing, each participant runs `status` with that `--ledger` value and
compares `workstate_id`, `project_id`, `store_id`, `scope_model`, `binding_epoch`,
`operational_reach`, and `frontier`. Any mismatch, an unreachable path, or a
worktree that cannot access this same SQLite file is terminal outcome `blocked`.

Claude enters a lease as `actor:claude-review`, declares a `verify` or `read`
intent for the review scope, and returns a response sibling. Codex is
`actor:codex-review`. Both use the default bounded policy: at most two rounds,
three participant responses, and eight tool calls. `principal:mark` is the
decision owner; no agent may silently continue beyond a limit.

## Review question

Does the current 0.8 COOP-1 draft provide a robust, implementable default for a
small group of agents working in one project? Identify only issues that materially
affect safe cooperation, a simpler model's ability to follow the procedure, or an
honest conformance claim. For every finding, provide an actionable recommendation
and say whether it blocks a bilateral trial, a COOP-1 conformance claim, or neither.

## Required terminal response

Return `accepted`, `revised`, `inconclusive`, `declined`, `timed_out`, or
`escalated`; identify any remaining disagreement; cite the reviewed artifact and
binding receipt; and publish the result before releasing the participant lease.
<!-- awp:generated:end -->

<!-- awp:review:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-current-protocol-review-2026-09-05",
  "title": "COOP-1 current-protocol bilateral review",
  "created_at": "2026-09-05T18:14:27Z",
  "created_by": "actor:codex-review",
  "modules": [
    {"id": "urn:awp:core", "version": "0.8.0", "required": true},
    {"id": "urn:awp:capsule", "version": "0.5.0", "required": true},
    {"id": "urn:awp:handoff", "version": "0.5.0", "required": true},
    {"id": "urn:awp:cooperation", "version": "0.1.0", "required": true}
  ],
  "representations": {"briefing": "#briefing", "manifest": "#manifest", "snapshot": "#snapshot"}
}
<!-- awp:review:manifest:end -->

<!-- awp:review:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-current-protocol-review-2026-09-05",
  "frontier": ["evt:17d857a5-c249-4bd1-a918-d71ae4cea018"],
  "generated_at": "2026-09-05T18:14:27Z",
  "records": {
    "consultations": [{
      "id": "consultation:coop1-current-protocol-review",
      "type": "consultation",
      "revision": 1,
      "status": "open",
      "question": "Does the current 0.8 COOP-1 draft provide a robust, implementable default for a small group of agents working in one project?",
      "decision_owner": "principal:mark",
      "participants": ["actor:codex-review", "actor:claude-review"],
      "requested_action": "Complete the shared-binding handshake and return a bounded independent critique with an explicit terminal outcome."
    }],
    "interactions": [{
      "type": "cooperation_interaction",
      "module": "urn:awp:cooperation",
      "interaction_id": "interaction:coop1-current-protocol-review",
      "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
      "purpose": "critique",
      "subject": {"artifact": "spec/drafts/0.8.0/cooperation-contracts.md", "focus": "Current COOP-1 binding completeness and implementability"},
      "participants": [{"id": "actor:codex-review", "role": "requester"}, {"id": "actor:claude-review", "role": "responder"}],
      "decision_owner": "principal:mark",
      "policy": {"policy_id": "coop-1-default-loop-v1", "digest": "sha256:fe7aede1f3d66000b4befb26c5b39a498c4cfe5db191ea6935dd08c4b41335ff"},
      "round": 1,
      "repeat_basis": {"purpose": "critique", "subject": {"artifact": "spec/drafts/0.8.0/cooperation-contracts.md", "focus": "Current COOP-1 binding completeness and implementability"}, "context_frontier": ["evt:17d857a5-c249-4bd1-a918-d71ae4cea018"], "participant_set_digest": "sha256:1e7f376c6cc540a5403eda3d42b1635a15bd039f56c608612b77a44036a7db57", "policy_digest": "sha256:fe7aede1f3d66000b4befb26c5b39a498c4cfe5db191ea6935dd08c4b41335ff"},
      "repeat_key": "sha256:69c5ab64e94b72b62f36b94490eb25f24702c0b7b4fb30688050e5488fc47c37",
      "progress": {"kind": "artifact", "ref": "artifact:cooperation-contracts"},
      "result": {"outcome": "inconclusive", "recorded_at": "2026-09-05T18:14:27Z", "remaining_disagreement": "Awaiting the independent participant response and shared-binding proof."}
    }]
  },
  "modules": {}
}
<!-- awp:review:snapshot:end -->
