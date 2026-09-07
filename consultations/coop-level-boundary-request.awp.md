---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: c041c2a04b9248628fe15379d6b2a5e4
workstate_id: urn:uuid:awp-coop-level-boundary-2026-09-07
frontier:
  - evt:coop-level-boundary-request
checkpoint: checkpoint:coop-level-boundary-request
generated_at: 2026-09-07T15:38:00Z
generated_digest: sha256:4e0231c8e93214d63f80f7e22f2158319148e9bfe7d7e3ceddce7fa2759af53f
---

<!-- awp:generated:start -->
# COOP-1 and COOP-2 functional-boundary consultation

This is one bounded critique round. It asks whether COOP-1 is the smallest durable, physical-scope coordination layer for small groups, while COOP-2 adds semantic-scope and integration assurance without adding COOP-3 enforcement.

## Requested review

Review the proposed boundary in the consultation record below. Identify any responsibility assigned to the wrong level and recommend exact normative edits. Distinguish a specification defect from a missing binding or missing evidence. Do not modify protocol sources; write a response at `consultations/coop-level-boundary-response.awp.md`.

## Proposed boundary

COOP-1: stable binding identity; durable event frontier; advisory participant liveness; idempotent physical path or artifact scopes with access modes; deterministic overlap outcomes; atomic guarded intent admission where supported; refresh, checkpoint, handoff, and recoverable terminal records. It does not infer semantic overlap, establish integration readiness, authenticate principals, fence writes, or protect mutation.

COOP-2: all COOP-1 behavior plus revision-pinned semantic selectors; declared-versus-observed scope comparison; explicit same/related/different/ambiguous/unresolvable results; change-set dependencies, preconditions, verification, staleness, and integration readiness under policy. It preserves uncertainty and evidence, but does not require a universal analyzer or add COOP-3 authority or enforcement.

Decision owner: principal:mark. Effective loop policy: one responder critique, then the owner decides whether to revise the 0.8.0 draft.
<!-- awp:generated:end -->

<!-- awp:c041c2a04b9248628fe15379d6b2a5e4:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-level-boundary-2026-09-07",
  "title": "COOP-1 and COOP-2 functional-boundary consultation",
  "created_at": "2026-09-07T15:38:00Z",
  "created_by": "actor:codex",
  "completeness": "portable",
  "modules": [
    {"id": "urn:awp:core", "version": "0.8.0", "required": true},
    {"id": "urn:awp:capsule", "version": "0.5.0", "required": true},
    {"id": "urn:awp:handoff", "version": "0.5.0", "required": true}
  ]
}
<!-- awp:c041c2a04b9248628fe15379d6b2a5e4:manifest:end -->

<!-- awp:c041c2a04b9248628fe15379d6b2a5e4:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-coop-level-boundary-2026-09-07",
  "frontier": ["evt:coop-level-boundary-request"],
  "generated_at": "2026-09-07T15:38:00Z",
  "records": {
    "consultations": [{
      "id": "consultation:coop-level-boundary",
      "type": "consultation",
      "revision": 1,
      "status": "open",
      "purpose": "critique",
      "question": "What is the smallest useful functional boundary between COOP-1 and COOP-2 in the AWP 0.8.0 draft?",
      "requested_action": "Return one bounded independent critique identifying misplaced responsibilities and exact recommended normative edits. Do not modify protocol sources.",
      "decision_owner": "principal:mark",
      "participants": ["actor:codex", "actor:claude-review"],
      "effective_loop_policy": {"max_rounds": 1, "continuation_requires": "recorded decision-owner approval"},
      "context": {
        "artifacts": ["spec/drafts/0.8.0/cooperation-contracts.md", "spec/drafts/0.8.0/coordination.md", "schemas/awp-cooperation-0.1.schema.json"],
        "proposed_coop1": "Durable physical-scope collision reduction, advisory liveness, deterministic guarded intent decisions, checkpoint, handoff, and recovery; no semantic inference, integration assurance, or protected enforcement.",
        "proposed_coop2": "All COOP-1 behavior plus revision-pinned semantic scope resolution, declared-versus-observed scope checks, dependency and verification binding, staleness, and policy-controlled integration readiness; no COOP-3 enforcement."
      },
      "response_path": "consultations/coop-level-boundary-response.awp.md"
    }]
  }
}
<!-- awp:c041c2a04b9248628fe15379d6b2a5e4:snapshot:end -->
