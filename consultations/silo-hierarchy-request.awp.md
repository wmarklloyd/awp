---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: a64f2ce1197b4a90b85d3e6f742c18d5
workstate_id: urn:uuid:awp-silo-hierarchy-2026-09-07
frontier:
  - evt:silo-hierarchy-request
checkpoint: checkpoint:silo-hierarchy-request
generated_at: 2026-09-07T16:15:00Z
generated_digest: sha256:cc177b89035805a70ea51ac9e5af1409e6f4bf9015e9caea86f7c66ebbc8a8ec
---

<!-- awp:generated:start -->
# Silo hierarchy and canonical-publication consultation

This is one bounded critique round about a proposed AWP 0.8.0 Silos feature. A silo is a durable, shareable non-canonical project state for proposed or exploratory work. It can have its own capsule, coordination binding, participants, goals, evidence, and lifecycle without changing the canonical project capsule.

## Proposed model

A silo may derive from the canonical project state or a parent silo. A child records its parent identity, exact parent capsule digest and frontier, creation checkpoint, inherited records, and explicit overrides. Parent/child derivation is an immutable base snapshot, not live inheritance: later parent changes do not silently alter a child. A child may explicitly rebase or promote selected results to its parent. Promotion to canonical state requires a decision-owner approval, fresh comparison with the current canonical frontier, and a canonical publication receipt.

For larger projects, separate the project owner or policy authority, a silo owner, and a canonical publisher. The canonical publisher serializes approved root-capsule changes but does not silently make governance decisions. Delegated component stewards may approve limited promotions under recorded policy. Silo-local leases and intents coordinate only that silo and do not reserve canonical project work.

## Requested critique

Assess whether hierarchical immutable-base silos are a sound protocol model. Identify lifecycle, identity, isolation, promotion, rebase, authority, and coordination hazards. Recommend a minimal normative data model and exact boundaries between canonical state, parent silos, child silos, and Git worktrees. Distinguish specification requirements from future implementation or evidence work. Do not modify protocol sources.

Decision owner: principal:mark. Effective loop policy: one responder critique, then the decision owner decides whether to open a 0.8.0 draft revision. Write the response at consultations/silo-hierarchy-response.awp.md.
<!-- awp:generated:end -->

<!-- awp:a64f2ce1197b4a90b85d3e6f742c18d5:manifest:start encoding="json" -->
{"awp_version":"0.8.0","workstate_id":"urn:uuid:awp-silo-hierarchy-2026-09-07","title":"Silo hierarchy and canonical-publication consultation","created_at":"2026-09-07T16:15:00Z","created_by":"actor:codex","completeness":"portable","modules":[{"id":"urn:awp:core","version":"0.8.0","required":true},{"id":"urn:awp:capsule","version":"0.5.0","required":true},{"id":"urn:awp:handoff","version":"0.5.0","required":true}]}
<!-- awp:a64f2ce1197b4a90b85d3e6f742c18d5:manifest:end -->

<!-- awp:a64f2ce1197b4a90b85d3e6f742c18d5:snapshot:start encoding="json" -->
{"awp_version":"0.8.0","workstate_id":"urn:uuid:awp-silo-hierarchy-2026-09-07","frontier":["evt:silo-hierarchy-request"],"generated_at":"2026-09-07T16:15:00Z","records":{"consultations":[{"id":"consultation:silo-hierarchy","type":"consultation","revision":1,"status":"open","purpose":"critique","question":"Is a hierarchical immutable-base Silo model a sound way to preserve and coordinate non-canonical project-state futures?","requested_action":"Return one independent critique with a minimal normative data model and exact boundaries. Do not modify protocol sources.","decision_owner":"principal:mark","participants":["actor:codex","actor:claude-review"],"effective_loop_policy":{"max_rounds":1,"continuation_requires":"recorded decision-owner approval"},"context":{"proposed_terms":["canonical state","silo","parent silo","child silo","silo owner","canonical publisher","promotion receipt"],"response_path":"consultations/silo-hierarchy-response.awp.md"}}]}}
<!-- awp:a64f2ce1197b4a90b85d3e6f742c18d5:snapshot:end -->
