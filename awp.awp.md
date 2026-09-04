---
awp_version: 0.7.0
specification: dist/0.7.0/AWP-0.7.0.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 89e5d09a47714dcfaa5734d1f155a4e8
workstate_id: urn:uuid:conversation-awp-design-2026-09-03
frontier:
  - evt:protocol-audit-repair
checkpoint: checkpoint:protocol-audit-repair
generated_at: 2026-09-04T15:08:12Z
generated_digest: sha256:317ddae17b48ed8f774ea754dab6ebe9be18263da4bd6848d1869f1c3ee59fdc
---

<!-- awp:generated:start -->
# Agent Workstate Protocol design

AWP 0.7.0 is the stable exploratory release, succeeding AWP 0.6.0. This current capsule is governed by the released 0.7.0 specification, which introduces explicit specification binding, embedded discovery, domain-neutral coordination, shared guardrails, and consultation records.

The protocol preserves portable semantic work state for human and agent continuation. It separates intent, authority, execution, evidence, and conclusion; distinguishes reported, inferred, observed, verified, disputed, stale, and refuted claims; and treats event ancestry as causal truth while snapshots and Markdown remain projections. Coordination applies to shared work products across code, models, documents, physical designs, schedules, and other domains.

The preferred exchange representation is a human-readable `<project-name>.awp.md` capsule. This project demonstrates that convention through `awp.awp.md`. Coordination defines deterministic lifecycle candidates, semantic scopes, bounded negotiation, explicit user-mediated arbitration for unresolved agent interactions, contracts, typed preconditions, verification binding, staleness propagation, integration semantics, and optional fenced live enforcement.

Complete bundled specification: [AWP 0.7.0 release bundle](dist/0.7.0/AWP-0.7.0.bundle.md).

The project’s target use cases are maintained in [the project scope](docs/project-scope.md): durable semantic descriptions, clear shared orientation, recorded checkpoint resumption, and coordination of interdependent changes to shared work products.

Current status: the 0.7.0 exploratory release is prepared with released and pre-release materials separated; released schema identifiers are preserved; the root contains standard governance, contribution, citation, and security metadata; CI validates specification families, conformance fixtures, links, reproducibility, and repository integrity. The 0.7 release includes bounded user-mediated arbitration, domain-neutral state-space coordination, portable guardrails, and model-neutral consultations. A deterministic synthetic coordination-awareness pilot is published with an explicit warning that it is not an independent-agent effectiveness study.

Recommended next action: run the preregistered coordination-awareness protocol with at least two independent agent implementations and publish all raw trials, exclusions, and analysis.
<!-- awp:generated:end -->

<!-- awp:notes:start -->
This capsule was migrated from the 0.3.0 design conversation. The prior monolithic drafts and review documents remain available as historical design input. Human notes are non-authoritative unless explicitly imported as proposed semantic events.
<!-- awp:notes:end -->

<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:manifest:start encoding="json" -->
{
  "awp_version": "0.7.0",
  "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
  "title": "Agent Workstate Protocol design",
  "created_at": "2026-09-03T13:39:35Z",
  "created_by": "actor:user",
  "modules": [
    {"id": "urn:awp:core", "version": "0.7.0", "required": true, "schema": "schemas/awp-core-0.7.schema.json"},
    {"id": "urn:awp:capsule", "version": "0.4.0", "required": true, "schema": "schemas/awp-capsule-0.4.schema.json", "capabilities": ["embedded-discovery"]},
    {"id": "urn:awp:handoff", "version": "0.4.0", "required": true, "capabilities": ["resume-profile"]},
    {"id": "urn:awp:artifact", "version": "0.4.0", "required": true},
    {"id": "urn:awp:sync", "version": "0.4.0", "required": true},
    {"id": "urn:awp:coordination", "version": "0.4.0", "required": true, "schema": "schemas/awp-coordination-0.4.schema.json", "capabilities": ["coordination-awareness", "integration-assurance"]},
    {"id": "urn:awp:security", "version": "0.4.0", "required": false, "schema": "schemas/awp-security-0.4.schema.json", "capabilities": ["shared-guardrails"]}
  ],
  "representations": {
    "capsule": {"kind": "single-file-markdown"},
    "snapshot": {"kind": "capsule-section", "section": "snapshot"},
    "events": {"kind": "snapshot-only", "reason": "Historical 0.3 event ledger is referenced but not embedded in this portable migration."}
  }
}
<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:manifest:end -->

<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:snapshot:start encoding="json" -->
{
  "awp_version": "0.7.0",
  "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
  "frontier": ["evt:protocol-audit-repair"],
  "generated_at": "2026-09-04T15:08:12Z",
  "source_frontier": ["evt:user-arbitration-checkpoint"],
  "records": {
    "goals": [{"id": "goal:awp-design", "type": "goal", "statement": "Define a portable workstate format for LLM session continuation and multi-agent coordination of shared work products across digital, physical, spatial, documentary, analytical, and mixed domains.", "status": "active"}],
    "constraints": [{"id": "constraint:no-private-cot", "type": "constraint", "statement": "Portable state must not require private chain-of-thought or hidden runtime state.", "strength": "required", "status": "active"}],
    "claims": [
      {"id": "claim:spec-06-current", "type": "claim", "statement": "AWP 0.6.0 is the stable exploratory release and includes Coordination 0.3.0.", "epistemic_status": "observed", "evidence": ["artifact:spec-06", "artifact:coordination-03"]},
      {"id": "claim:awp-rename-complete", "type": "claim", "statement": "The repository-wide rename to Agent Workstate Protocol (AWP), including filenames, schema identifiers, fields, URNs, discovery, examples, and historical documents, is complete.", "epistemic_status": "verified", "evidence": ["evidence:awp-validation"]},
      {"id": "claim:credibility-overhaul", "type": "claim", "statement": "The repository separates immutable release artifacts from the 0.7.0 release and its archived pre-release source, and includes governance, citation, security, conformance, reproducibility, related-work, and synthetic-pilot assets.", "epistemic_status": "verified", "evidence": ["evidence:repository-validation"]}
    ],
    "evidence": [
      {"id": "evidence:awp-validation", "type": "evidence", "evidence_type": "validation_run", "summary": "The released 0.3 through 0.6 specification validators pass.", "observed_at": "2026-09-04T05:11:34Z"},
      {"id": "evidence:repository-validation", "type": "evidence", "evidence_type": "validation_run", "summary": "The 0.7 release validator, capsule, consultation, guardrail, and domain-neutral coordination conformance fixtures, repository-integrity tests, repository-relative link checks, reproducible bundles, and the synthetic pilot result check passed.", "observed_at": "2026-09-04T15:08:12Z"}
    ],
    "decisions": [
      {"id": "decision:name", "type": "decision", "question": "What should the protocol be called?", "status": "accepted", "choice": "Agent Workstate Protocol (AWP)"},
      {"id": "decision:single-file", "type": "decision", "question": "What is the preferred exchange representation?", "status": "accepted", "choice": "Markdown-first self-contained project.awp.md capsule"},
      {"id": "decision:modular-04", "type": "decision", "question": "How should the 0.4 design be organized?", "status": "accepted", "choice": "Required Core plus independently versioned optional modules; Coordination remains experimental."},
      {"id": "decision:resume-05", "type": "decision", "question": "How should AWP support returning to a project?", "status": "accepted", "choice": "Define repository discovery in Capsule and a project-reentry Resume Profile in Handoff."},
      {"id": "decision:coordination-06", "type": "decision", "question": "How should multi-agent coordination enter the next AWP family?", "status": "accepted", "choice": "Integrate Coordination 0.3.0 as normative but experimental in AWP 0.6.0, with a schema, validator, and staged capability bundles."},
      {"id": "decision:explicit-specification", "type": "decision", "question": "How should a shared workstate identify its protocol semantics?", "status": "accepted", "choice": "Introduce the requirement in the 0.7.0 working draft as Capsule 0.4.0 embedded metadata, while preserving the immutable 0.6.0 release. Prefer a version-pinned published URL, permit a repository-relative local copy for sandboxed or offline use, and do not silently infer compatibility."},
      {"id": "decision:single-file-capsule", "type": "decision", "question": "Where should discovery metadata live for a portable workstate?", "status": "accepted", "choice": "Keep the Markdown capsule self-describing with embedded discovery metadata; do not require a companion .awp.json pointer for the 0.7.0 working draft."},
      {"id": "decision:domain-neutral-coordination", "type": "decision", "question": "What kinds of shared state should multiple agents coordinate?", "status": "accepted", "choice": "Coordinate changes to shared work products across digital, physical, spatial, documentary, analytical, and mixed domains. Repositories are one state-space adapter; scopes and selector profiles also cover model elements, spatial regions, assemblies, interfaces, and other domain objects."},
      {"id": "decision:shared-guardrails", "type": "decision", "question": "How should safety guardrails apply across models and collaboration modes?", "status": "accepted", "choice": "Carry model-independent, structured guardrails as portable Security constraints in the workstate. Apply them to lone agents and collaborative agents, including delegated and derived operations; cooperation cannot weaken or evade a required prohibition, while enforcement remains the responsibility of the receiving runtime or protected adapter."},
      {"id": "decision:consultation-record", "type": "decision", "question": "How should a workstate package a bounded request for another model or specialist's advice?", "status": "accepted", "choice": "Add a model-neutral Core consultation record with a precise question, requested response, portable context, read-first references, and optional response provenance. Consultation advice never grants authority or overrides guardrails."},
      {"id": "decision:release-discipline", "type": "decision", "question": "How should AWP distinguish released protocol semantics from development?", "status": "accepted", "choice": "Keep released artifacts and identifiers immutable; develop normative changes under spec/drafts; use minor versions for incompatible 0.x changes; publish errata or new versions rather than moving tags."},
      {"id": "decision:user-arbitration", "type": "decision", "question": "How should AWP handle interacting agent changes that cannot be safely resolved by the agents?", "status": "accepted", "choice": "Create a bounded arbitration request with exact subjects, revisions, alternatives, blocked scopes, and safe interim work; pause dependent writes; require a trusted decision from the declared user or principal; preserve both branches; and apply the decision only under its recorded conditions with fresh verification."}
    ],
    "plans": [{"id": "plan:coordination-test", "type": "plan", "goal": "goal:awp-design", "status": "active", "steps": ["Build the coordination-awareness test harness", "Run physical and semantic conflict fixtures", "Compare chat-only, Git-only, and AWP-assisted runs", "Measure false alarms, conflicts caught, overhead, and recovery"]}],
    "tasks": [
      {"id": "task:json-schema", "type": "task", "title": "Maintain normative Core and module schemas", "status": "completed"},
      {"id": "task:single-file-prototype", "type": "task", "title": "Implement a minimal capsule and resume reader/writer", "status": "proposed"},
      {"id": "task:cross-model-test", "type": "task", "title": "Run cross-model semantic handoff test", "status": "proposed"},
      {"id": "task:coordination-spec-06", "type": "task", "title": "Integrate Coordination 0.3.0 into AWP 0.6.0", "status": "completed"},
      {"id": "task:awp-rename", "type": "task", "title": "Rename the protocol and all repository representations to Agent Workstate Protocol (AWP)", "status": "completed"},
      {"id": "task:repository-credibility", "type": "task", "title": "Reorganize the repository around standards-project release, governance, conformance, and research practices", "status": "completed"},
      {"id": "task:synthetic-pilot", "type": "task", "title": "Build and run the deterministic coordination-awareness instrumentation pilot", "status": "completed"},
      {"id": "task:coordination-prototype", "type": "task", "title": "Run the preregistered coordination-awareness experiment with independent agent implementations", "status": "ready"},
      {"id": "task:user-arbitration-protocol", "type": "task", "title": "Specify user-mediated arbitration for interacting agent changes", "status": "completed"}
    ],
    "questions": [],
    "artifacts": [
      {"id": "artifact:spec-06", "type": "artifact", "name": "AWP_SPECIFICATION_0.6.0.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "AWP_SPECIFICATION_0.6.0.md"}], "integrity": {"algorithm": "sha256", "digest": "f955c70ee3899b7e64fa1a10ed39f408dbacc1a7a714c818068da8ac1cd6fa7a"}}}},
      {"id": "artifact:spec-06-bundle", "type": "artifact", "name": "AWP-0.6.0.bundle.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "dist/0.6.0/AWP-0.6.0.bundle.md"}], "integrity": {"algorithm": "sha256", "digest": "7c08480e85f8d3c291641cb76b43aca4cbd4ff2940511d4b7a493a2848dbb907"}}}},
      {"id": "artifact:core-06", "type": "artifact", "name": "spec/0.6.0/core.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/core.md"}], "integrity": {"algorithm": "sha256", "digest": "963ac5f8cb934971a5697211755b897d4371f5907d5ee02d9b0455c96f85fa96"}}}},
      {"id": "artifact:coordination-03", "type": "artifact", "name": "spec/0.6.0/coordination.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/coordination.md"}], "integrity": {"algorithm": "sha256", "digest": "b97114aee7d0e33faa5426067bb0f235cbd801106bb5d1e2b792ac9c9fc9b4cd"}}}},
      {"id": "artifact:coordination-schema-03", "type": "artifact", "name": "schemas/awp-coordination-0.3.schema.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "schemas/awp-coordination-0.3.schema.json"}], "integrity": {"algorithm": "sha256", "digest": "554f53980a0f84c2d01e0c927264832dbd966e69d016f83267435afc84d56562"}}}},
      {"id": "artifact:module-registry-06", "type": "artifact", "name": "spec/0.6.0/modules.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/modules.json"}], "integrity": {"algorithm": "sha256", "digest": "4f2337eb0507079d9a2dc17b703b5be796cfd37b651909a4d3689560d3045aa7"}}}},
      {"id": "artifact:purpose", "type": "artifact", "name": "project-scope.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "docs/project-scope.md"}], "integrity": {"algorithm": "sha256", "digest": "cb4dbaeac086760e6c90050778972d0cb3041f8ae8f835a48d8239e1abf96e2b"}}}},
      {"id": "artifact:release-notes-06", "type": "artifact", "name": "0.6.0.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "docs/releases/0.6.0.md"}], "integrity": {"algorithm": "sha256", "digest": "f7da98359b28f6f3b814a252a70133bf62e4dc2237f60bae11f4783488297297"}}}},
      {"id": "artifact:validator-06", "type": "artifact", "name": "tools/validate_spec_0_6.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/validate_spec_0_6.py"}], "integrity": {"algorithm": "sha256", "digest": "1713ba8cd02f0329b8fed35f40def65d7f12e7d071283ed6315dd61d384a9784"}}}},
      {"id": "artifact:bundle-builder-06", "type": "artifact", "name": "tools/build_spec_0_6_bundle.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/build_spec_0_6_bundle.py"}], "integrity": {"algorithm": "sha256", "digest": "33f97717e6c240ea84a1e5b1044fbfae6d198012b133a250a9a17326b6422117"}}}},
      {"id": "artifact:spec-07-release", "type": "artifact", "name": "AWP 0.7.0 stable exploratory release", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.7.0/index.md"}], "integrity": {"algorithm": "sha256", "digest": "ae8077859ef11ac69416d288cb7a913c1ba146c551f994c9c055ecf6e0ce79cc"}}}},
      {"id": "artifact:spec-07-bundle", "type": "artifact", "name": "AWP-0.7.0.bundle.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "dist/0.7.0/AWP-0.7.0.bundle.md"}], "integrity": {"algorithm": "sha256", "digest": "c90d14960b71617eeeb7c2b273ab470285322661f115e4aef2990b385fdd1937"}}}},
      {"id": "artifact:conformance", "type": "artifact", "name": "Conformance evidence", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "conformance/matrix.md"}], "integrity": {"algorithm": "sha256", "digest": "b1f6ff19e8673f13f67d54b25ce674709dd8c7b5915ca6f28d7bc1b80739e2b5"}}}},
      {"id": "artifact:synthetic-pilot", "type": "artifact", "name": "Coordination-awareness synthetic pilot report", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "experiments/coordination-awareness/results/pilot-report.md"}], "integrity": {"algorithm": "sha256", "digest": "f9c1cfc441e2639a67171c8199a333c31e7f99b2fb1d99320973a4d635ac25a4"}}}}
    ],
    "executions": [],
    "changes": [
      {"id": "change:awp-rename", "type": "change", "summary": "Renamed the protocol repository-wide from its former name to Agent Workstate Protocol (AWP) and refreshed generated artifacts and integrity metadata.", "artifacts": ["artifact:spec-06", "artifact:spec-06-bundle", "artifact:core-06", "artifact:coordination-03", "artifact:coordination-schema-03", "artifact:module-registry-06"]},
      {"id": "change:explicit-specification", "type": "change", "summary": "Introduced explicit governing-specification binding in the separately versioned AWP 0.7.0 release while preserving AWP 0.6.0 and its historical Discovery 0.1 format.", "artifacts": ["artifact:spec-07-release", "artifact:spec-07-bundle"]},
      {"id": "change:repository-credibility", "type": "change", "summary": "Reorganized the project into stable, archived-draft, distribution, conformance, documentation, experiment, and research areas; added governance, citation, security, CI, reproducibility, requirement inventory, related work, and a disclosed synthetic pilot.", "artifacts": ["artifact:spec-06", "artifact:spec-06-bundle", "artifact:spec-07-release", "artifact:spec-07-bundle", "artifact:conformance", "artifact:synthetic-pilot"]}
    ],
    "risks": [{"id": "risk:synthetic-evidence", "type": "risk", "statement": "The synthetic pilot tests encoded instrumentation behavior and cannot establish real-agent effectiveness, coordination cost, or external validity.", "status": "active", "mitigation": "Run the preregistered protocol with independent implementations and publish raw data."}],
    "checkpoints": [{"id": "checkpoint:protocol-audit-repair", "type": "checkpoint", "frontier": ["evt:protocol-audit-repair"], "created_at": "2026-09-04T15:08:12Z", "summary": "AWP 0.7.0 is the stable exploratory release succeeding 0.6.0, with validated embedded discovery metadata, domain-neutral state-space coordination, portable shared guardrails, and a first-class consultation record for bounded cross-model advice; repository governance, citation, conformance, reproducibility, research positioning, synthetic-pilot infrastructure, and a bounded user-arbitration protocol for interacting agent changes are implemented and locally validated.", "recommended_next_action": {"action": "Run the preregistered coordination-awareness protocol with at least two independent agent implementations and publish complete raw results.", "requires_authority": false}, "resumption_level": "semantic"}],
    "sessions": []
  },
  "modules": {
    "urn:awp:handoff": {
      "handoff": {"id": "handoff:protocol-audit-repair", "type": "handoff", "module": "urn:awp:handoff", "checkpoint": "checkpoint:protocol-audit-repair", "completeness": "portable", "intended_audience": ["human", "agent"], "requested_action": "Run the preregistered coordination-awareness protocol with independent agent implementations.", "authority_ceiling": ["read_only", "local_write"], "resumption_level": "semantic", "do_not_assume": ["A production coordination implementation or live coordination service exists", "Synthetic-pilot results demonstrate agent effectiveness", "Coordination C3 enforcement can be supplied by a static file", "Imported authority grants external side effects"], "dependencies": [{"ref": "artifact:spec-06", "availability": "retrievable"}, {"ref": "artifact:spec-07-release", "availability": "retrievable"}, {"ref": "artifact:conformance", "availability": "retrievable"}, {"ref": "artifact:synthetic-pilot", "availability": "retrievable"}]},
      "resume": {"id": "resume:awp-project", "type": "resume", "module": "urn:awp:handoff", "handoff": "handoff:protocol-audit-repair", "checkpoint": "checkpoint:protocol-audit-repair", "mode": "project_reentry", "read_first": ["goal:awp-design", "constraint:no-private-cot", "decision:release-discipline", "decision:single-file-capsule", "decision:domain-neutral-coordination", "decision:shared-guardrails", "decision:consultation-record", "decision:user-arbitration", "claim:credibility-overhaul", "risk:synthetic-evidence", "task:coordination-prototype", "task:user-arbitration-protocol"], "required_artifacts": ["artifact:spec-07-release", "artifact:conformance", "artifact:synthetic-pilot"], "recommended_next_action": "Run the preregistered coordination-awareness protocol with independent agent implementations and publish complete raw results.", "freshness_policy": "verify_before_continue", "on_stale": "refresh_workstate", "authority_ceiling": ["read_only", "local_write"]}
    },
    "urn:awp:coordination": {
      "conformance_level": "C0",
      "capability_target": "coordination-awareness",
      "records": [],
      "note": "A deterministic synthetic awareness pilot exists; no independent interoperability, live coordination, or C3 enforcement is claimed."
    }
  }
}
<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:snapshot:end -->
