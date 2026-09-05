---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
workstate_id: urn:uuid:awp-coop1-live-refinement-2026-09-05
frontier:
  - evt:f1fe3c2b-bdef-4542-aa82-61ef0050a0ad
checkpoint: checkpoint:coop1-live-refinement
generated_at: 2026-09-05T19:27:00Z
generated_digest: sha256:508c12c178f728dd4abb7f69a3688b2b109e18957c40a5ca58ec54b41f9738ea
---

<!-- awp:generated:start -->
# COOP-1 live refinement with Claude

This is one bounded critique round between Codex and Claude. Its purpose is to
select the highest-value remaining vertical slice needed for a robust COOP-1
binding after commits `f000a2f` and `5d89a76`.

Claude must use `.awp-runtime/coop1-live.sqlite3`, verify the stable binding
identity, and enter as `actor:claude-live`. Claude may read the repository but
must not modify protocol sources. Its only write scope is
`consultations/coop1-live-refinement-response.awp.md`.

The response must distinguish specification defects, binding defects, and
missing evidence. It must recommend one bounded next implementation slice,
explain why that slice comes first, and identify executable acceptance tests.
Only issues material to safe cooperation, simple-model implementability, or an
honest conformance claim belong in the response.

The effective policy permits one round, one Claude response, and at most twelve
Claude tool calls. `principal:mark` is the decision owner. Claude must publish
the response artifact before completing its intent, and complete the intent
before releasing its lease with `--handoff` pointing to that existing response.
If any step cannot be confirmed, the terminal result is `inconclusive` or
`escalated`, and the lease must not be represented as a successful exit.
<!-- awp:generated:end -->

<!-- awp:review:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-live-refinement-2026-09-05",
  "title": "COOP-1 live refinement with Claude",
  "created_at": "2026-09-05T19:27:00Z",
  "created_by": "actor:codex-live",
  "modules": [
    {"id":"urn:awp:core","version":"0.8.0","required":true},
    {"id":"urn:awp:capsule","version":"0.5.0","required":true},
    {"id":"urn:awp:handoff","version":"0.5.0","required":true},
    {"id":"urn:awp:cooperation","version":"0.1.0","required":true}
  ],
  "representations": {"briefing":"#briefing","manifest":"#manifest","snapshot":"#snapshot"}
}
<!-- awp:review:manifest:end -->

<!-- awp:review:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop1-live-refinement-2026-09-05",
  "frontier": ["evt:f1fe3c2b-bdef-4542-aa82-61ef0050a0ad"],
  "generated_at": "2026-09-05T19:27:00Z",
  "records": {
    "consultations": [{
      "id": "consultation:coop1-live-refinement",
      "type": "consultation",
      "revision": 1,
      "status": "open",
      "question": "Which single vertical slice should be implemented next to make COOP-1 materially more robust?",
      "decision_owner": "principal:mark",
      "participants": ["actor:codex-live","actor:claude-live"],
      "requested_action": "Return one bounded independent critique and publish it before a receipt-backed lease release."
    }],
    "interactions": [{
      "type": "cooperation_interaction",
      "module": "urn:awp:cooperation",
      "interaction_id": "interaction:coop1-live-refinement",
      "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
      "purpose": "critique",
      "subject": {
        "artifacts": ["spec/drafts/0.8.0/cooperation-contracts.md","schemas/awp-cooperation-0.1.schema.json","tools/awp_coordination.py"],
        "focus": "Select the highest-value remaining vertical slice for robust COOP-1"
      },
      "participants": [{"id":"actor:codex-live","role":"requester"},{"id":"actor:claude-live","role":"responder"}],
      "decision_owner": "principal:mark",
      "policy": {"policy_id":"coop-1-live-refinement-v1","digest":"sha256:39173eee44d2b06b7c698be005a914b59cb9e287e05cb107c5c9e0bdfe646004"},
      "round": 1,
      "repeat_basis": {
        "purpose": "critique",
        "subject": {
          "artifacts": ["spec/drafts/0.8.0/cooperation-contracts.md","schemas/awp-cooperation-0.1.schema.json","tools/awp_coordination.py"],
          "focus": "Select the highest-value remaining vertical slice for robust COOP-1"
        },
        "context_frontier": ["evt:f1fe3c2b-bdef-4542-aa82-61ef0050a0ad"],
        "participant_set_digest": "sha256:0124159307237d0bc2bf884d3b952b9f3eeef2ee4e82b97c52b1462287ecf3d7",
        "policy_digest": "sha256:39173eee44d2b06b7c698be005a914b59cb9e287e05cb107c5c9e0bdfe646004"
      },
      "repeat_key": "sha256:1f9f891e3571da0c803cc18780998133076e1f14e66fc4e008e8f753ca31a3de",
      "progress": {"kind":"artifact","ref":"consultations/coop1-live-refinement.awp.md"},
      "result": {"outcome":"inconclusive","recorded_at":"2026-09-05T19:27:00Z","remaining_disagreement":"Awaiting Claude's bounded response."}
    }]
  },
  "modules": {}
}
<!-- awp:review:snapshot:end -->
