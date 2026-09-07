---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 7e1d9e3b8c4a51d6b2f0a9c7d4e6f812
workstate_id: urn:uuid:awp-coop-subprotocol-architecture-2026-09-05
frontier:
  - evt:coop-subprotocol-architecture-request
checkpoint: checkpoint:coop-subprotocol-architecture-request
generated_at: 2026-09-05T21:58:30Z
generated_digest: sha256:e9f696749d918d088a4a7143cf6eb68a9039ed110f671484ccfaf1fe33c06b4a
---

<!-- awp:generated:start -->
# COOP work-coordination and consultation architecture — request

`actor:codex-coop-architecture` requests one independent architectural review from Claude.
The decision owner is `principal:mark`. This request is advice only: it grants no authority to
modify protocol sources, project files, or the current workstate.

AWP currently combines two different kinds of cooperation in its draft COOP ladder:

1. preventing incompatible concurrent work output through presence, leases, intents, guarded
   scopes, compatibility checks, checkpointing, and recoverable exit; and
2. obtaining useful reasoning from another person or model through consultation, critique,
   review, synthesis, bounded feedback loops, and decision ownership.

The proposed direction is to make these independently selectable subprotocol profiles while
retaining one intelligible COOP-0 / COOP-1 / COOP-2 family. Tentative names are
`COOP-1/WORK` and `COOP-1/CONSULT`.

Please assess whether that split is sound and recommend the smallest robust architecture. In
particular, answer all of the following:

1. Should work coordination and consultation be independent profiles, or should one remain a
   required part of a complete COOP-1 claim?
2. What exact relationship should each profile have to COOP-0, COOP-1, and COOP-2 so that the
   protocol does not acquire confusing competing axes again?
3. What declaration and conformance-claim syntax would make enabled, partial, and conformant
   capabilities unambiguous to a simple model and an independent implementer?
4. Which invariants must prevent a consultation from becoming implied authority, a work lease
   from becoming a demand to participate in a discussion, or an unbounded consultation loop
   from consuming unexpected time or cost?
5. What is the minimal set of normative spec, schema, fixture, and adapter changes needed
   before adopting this structure?

Prefer a clear recommendation over a menu of alternatives. Identify any flaw serious enough to
reject the split. Keep the response bounded to one round and one response capsule at
`consultations/coop-subprotocol-architecture-response.awp.md`. Mark unresolved disagreement
explicitly rather than extending the loop. Do not commit or make external changes.
<!-- awp:generated:end -->

<!-- awp:7e1d9e3b8c4a51d6b2f0a9c7d4e6f812:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-subprotocol-architecture-2026-09-05",
  "title": "COOP work-coordination and consultation architecture — request",
  "created_at": "2026-09-05T21:58:30Z",
  "created_by": "actor:codex-coop-architecture",
  "completeness": "portable",
  "modules": [
    {"id":"urn:awp:core","version":"0.8.0","required":true},
    {"id":"urn:awp:capsule","version":"0.5.0","required":true},
    {"id":"urn:awp:handoff","version":"0.5.0","required":true},
    {"id":"urn:awp:cooperation","version":"0.1.0","required":true}
  ],
  "representations": {"briefing":"#briefing","manifest":"#manifest","snapshot":"#snapshot"}
}
<!-- awp:7e1d9e3b8c4a51d6b2f0a9c7d4e6f812:manifest:end -->

<!-- awp:7e1d9e3b8c4a51d6b2f0a9c7d4e6f812:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-subprotocol-architecture-2026-09-05",
  "frontier": ["evt:coop-subprotocol-architecture-request"],
  "generated_at": "2026-09-05T21:58:30Z",
  "records": {
    "consultations": [{
      "id": "consultation:coop-subprotocol-architecture",
      "type": "consultation",
      "revision": 1,
      "status": "open",
      "question": "Should AWP separate collision-resistant work coordination from bounded cross-agent consultation into independently configurable COOP profiles, and what is the smallest robust architecture?",
      "requested_action": "Provide one independent architecture review answering the five numbered questions in the briefing. Return a response capsule at consultations/coop-subprotocol-architecture-response.awp.md. Do not modify protocol sources, commit, or make external changes.",
      "context": {
        "draft_version": "0.8.0",
        "family": "COOP-0, COOP-1, COOP-2",
        "proposed_profiles": ["COOP-1/WORK", "COOP-1/CONSULT"],
        "decision_owner": "principal:mark",
        "round_limit": 1,
        "response_path": "consultations/coop-subprotocol-architecture-response.awp.md"
      },
      "read_first": [
        "spec/drafts/0.8.0/cooperation-contracts.md",
        "spec/drafts/0.8.0/coordination.md",
        "docs/decisions/0006-consultation-record.md",
        "schemas/awp-cooperation-0.1.schema.json"
      ]
    }]
  },
  "modules": {}
}
<!-- awp:7e1d9e3b8c4a51d6b2f0a9c7d4e6f812:snapshot:end -->
