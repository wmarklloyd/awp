---
awp_version: 0.6.0
specification: https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md
format: single-file-capsule
capsule_boundary: 89e5d09a47714dcfaa5734d1f155a4e8
workstate_id: urn:uuid:conversation-awp-design-2026-09-03
frontier:
  - evt:user-arbitration-checkpoint
checkpoint: checkpoint:user-arbitration
generated_at: 2026-09-04T06:46:00Z
generated_digest: sha256:aefe2cb778551dd82d04214cc7a519096ed4eefa7cc330e40d44ff5e9b4715f6
---

<!-- awp:generated:start -->
# Agent Workstate Protocol design

AWP 0.6.0 is the stable exploratory release. AWP 0.7.0 is an unreleased working draft that introduces explicit governing-specification binding with new family, module, and discovery-schema versions.

The protocol preserves portable semantic work state for human and agent continuation. It separates intent, authority, execution, evidence, and conclusion; distinguishes reported, inferred, observed, verified, disputed, stale, and refuted claims; and treats event ancestry as causal truth while snapshots and Markdown remain projections.

The preferred exchange representation is a human-readable `<project-name>.awp.md` capsule. This project demonstrates that convention through `awp.awp.md`. Coordination defines deterministic lifecycle candidates, semantic scopes, bounded negotiation, explicit user-mediated arbitration for unresolved agent interactions, contracts, typed preconditions, verification binding, staleness propagation, integration semantics, and optional fenced live enforcement.

Complete bundled specification: [AWP 0.6.0 specification bundle](https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md).

The project’s four target use cases are maintained in [the project scope](docs/project-scope.md): durable semantic descriptions, clear shared orientation, recorded checkpoint resumption, and coordination of interdependent changes above source control.

Current status: released and draft materials are separated; released schema identifiers are preserved; the root contains standard governance, contribution, citation, and security metadata; CI validates five specification families, conformance fixtures, links, bundle reproducibility, and repository integrity. Coordination 0.4 now specifies bounded user-mediated arbitration: dependent writes pause while a trusted decision is recorded for exact subjects, revisions, scopes, and conditions. A deterministic synthetic coordination-awareness pilot is published with an explicit warning that it is not an independent-agent effectiveness study.

Recommended next action: run the preregistered coordination-awareness protocol with at least two independent agent implementations and publish all raw trials, exclusions, and analysis.
<!-- awp:generated:end -->

<!-- awp:notes:start -->
This capsule was migrated from the 0.3.0 design conversation. The prior monolithic drafts and review documents remain available as historical design input. Human notes are non-authoritative unless explicitly imported as proposed semantic events.
<!-- awp:notes:end -->

<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:manifest:start encoding="json" -->
{
  "awp_version": "0.6.0",
  "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
  "title": "Agent Workstate Protocol design",
  "created_at": "2026-09-03T13:39:35Z",
  "created_by": "actor:user",
  "modules": [
    {"id": "urn:awp:core", "version": "0.6.0", "required": true, "schema": "schemas/awp-core-0.6.schema.json"},
    {"id": "urn:awp:capsule", "version": "0.3.0", "required": true, "capabilities": ["repository-discovery"]},
    {"id": "urn:awp:handoff", "version": "0.3.0", "required": true, "capabilities": ["resume-profile"]},
    {"id": "urn:awp:artifact", "version": "0.3.0", "required": true},
    {"id": "urn:awp:sync", "version": "0.3.0", "required": true},
    {"id": "urn:awp:coordination", "version": "0.3.0", "required": true, "schema": "schemas/awp-coordination-0.3.schema.json", "capabilities": ["coordination-awareness", "integration-assurance"]}
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
  "awp_version": "0.6.0",
  "workstate_id": "urn:uuid:conversation-awp-design-2026-09-03",
  "frontier": ["evt:user-arbitration-checkpoint"],
  "generated_at": "2026-09-04T06:46:00Z",
  "source_frontier": ["evt:awp-rename-checkpoint"],
  "records": {
    "goals": [{"id": "goal:awp-design", "type": "goal", "statement": "Define a portable workstate format for LLM session continuation and multi-agent code coordination.", "status": "active"}],
    "constraints": [{"id": "constraint:no-private-cot", "type": "constraint", "statement": "Portable state must not require private chain-of-thought or hidden runtime state.", "strength": "required", "status": "active"}],
    "claims": [
      {"id": "claim:spec-06-current", "type": "claim", "statement": "AWP 0.6.0 is the stable exploratory release and includes Coordination 0.3.0.", "epistemic_status": "observed", "evidence": ["artifact:spec-06", "artifact:coordination-03"]},
      {"id": "claim:awp-rename-complete", "type": "claim", "statement": "The repository-wide rename to Agent Workstate Protocol (AWP), including filenames, schema identifiers, fields, URNs, discovery, examples, and historical documents, is complete.", "epistemic_status": "verified", "evidence": ["evidence:awp-validation"]},
      {"id": "claim:credibility-overhaul", "type": "claim", "statement": "The repository separates immutable release artifacts from the 0.7.0 working draft and includes governance, citation, security, conformance, reproducibility, related-work, and synthetic-pilot assets.", "epistemic_status": "verified", "evidence": ["evidence:repository-validation"]}
    ],
    "evidence": [
      {"id": "evidence:awp-validation", "type": "evidence", "evidence_type": "validation_run", "summary": "The released 0.3 through 0.6 specification validators pass.", "observed_at": "2026-09-04T05:11:34Z"},
      {"id": "evidence:repository-validation", "type": "evidence", "evidence_type": "validation_run", "summary": "The 0.7 draft validator, four Discovery 0.2 conformance fixtures, five repository-integrity tests, 98 repository-relative link checks, reproducible bundles, and the synthetic pilot result check passed.", "observed_at": "2026-09-04T05:11:34Z"}
    ],
    "decisions": [
      {"id": "decision:name", "type": "decision", "question": "What should the protocol be called?", "status": "accepted", "choice": "Agent Workstate Protocol (AWP)"},
      {"id": "decision:single-file", "type": "decision", "question": "What is the preferred exchange representation?", "status": "accepted", "choice": "Markdown-first self-contained project.awp.md capsule"},
      {"id": "decision:modular-04", "type": "decision", "question": "How should the 0.4 design be organized?", "status": "accepted", "choice": "Required Core plus independently versioned optional modules; Coordination remains experimental."},
      {"id": "decision:resume-05", "type": "decision", "question": "How should AWP support returning to a project?", "status": "accepted", "choice": "Define repository discovery in Capsule and a project-reentry Resume Profile in Handoff."},
      {"id": "decision:coordination-06", "type": "decision", "question": "How should multi-agent coordination enter the next AWP family?", "status": "accepted", "choice": "Integrate Coordination 0.3.0 as normative but experimental in AWP 0.6.0, with a schema, validator, and staged capability bundles."},
      {"id": "decision:explicit-specification", "type": "decision", "question": "How should a shared workstate identify its protocol semantics?", "status": "accepted", "choice": "Introduce the requirement in the 0.7.0 working draft as Capsule 0.4.0 and Discovery 0.2.0, while preserving the immutable 0.6.0 release. Prefer a version-pinned published URL, permit a repository-relative local copy for sandboxed or offline use, and do not silently infer compatibility."},
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
      {"id": "artifact:spec-06", "type": "artifact", "name": "AWP_SPECIFICATION_0.6.0.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "AWP_SPECIFICATION_0.6.0.md"}], "integrity": {"algorithm": "sha256", "digest": "ded69dcf35fe135a6ff9bca1e1c7d7fc63f8cebc6c4457fefe462ebee137553d"}}}},
      {"id": "artifact:spec-06-bundle", "type": "artifact", "name": "AWP-0.6.0.bundle.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "dist/0.6.0/AWP-0.6.0.bundle.md"}], "integrity": {"algorithm": "sha256", "digest": "7c08480e85f8d3c291641cb76b43aca4cbd4ff2940511d4b7a493a2848dbb907"}}}},
      {"id": "artifact:core-06", "type": "artifact", "name": "spec/0.6.0/core.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/core.md"}], "integrity": {"algorithm": "sha256", "digest": "963ac5f8cb934971a5697211755b897d4371f5907d5ee02d9b0455c96f85fa96"}}}},
      {"id": "artifact:coordination-03", "type": "artifact", "name": "spec/0.6.0/coordination.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/coordination.md"}], "integrity": {"algorithm": "sha256", "digest": "b97114aee7d0e33faa5426067bb0f235cbd801106bb5d1e2b792ac9c9fc9b4cd"}}}},
      {"id": "artifact:coordination-schema-03", "type": "artifact", "name": "schemas/awp-coordination-0.3.schema.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "schemas/awp-coordination-0.3.schema.json"}], "integrity": {"algorithm": "sha256", "digest": "554f53980a0f84c2d01e0c927264832dbd966e69d016f83267435afc84d56562"}}}},
      {"id": "artifact:module-registry-06", "type": "artifact", "name": "spec/0.6.0/modules.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/modules.json"}], "integrity": {"algorithm": "sha256", "digest": "4f2337eb0507079d9a2dc17b703b5be796cfd37b651909a4d3689560d3045aa7"}}}},
      {"id": "artifact:purpose", "type": "artifact", "name": "project-scope.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "docs/project-scope.md"}], "integrity": {"algorithm": "sha256", "digest": "2493127b89732f286fd9539d4e578f7a603d983499ae18c6b9e82abfb5af71e8"}}}},
      {"id": "artifact:discovery", "type": "artifact", "name": ".awp.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": ".awp.json"}], "integrity": {"algorithm": "sha256", "digest": "77a366542c5753ccc5651ec262daf75796d7abbf11244119536c9490eb4db81b"}}}},
      {"id": "artifact:discovery-schema", "type": "artifact", "name": "schemas/awp-discovery-0.1.schema.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "schemas/awp-discovery-0.1.schema.json"}], "integrity": {"algorithm": "sha256", "digest": "c73426ad2303dc90d8fb8c89d1d409605f074b3d97e6b6e37934660081822999"}}}},
      {"id": "artifact:release-notes-06", "type": "artifact", "name": "0.6.0.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "docs/releases/0.6.0.md"}], "integrity": {"algorithm": "sha256", "digest": "f7da98359b28f6f3b814a252a70133bf62e4dc2237f60bae11f4783488297297"}}}},
      {"id": "artifact:validator-06", "type": "artifact", "name": "tools/validate_spec_0_6.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/validate_spec_0_6.py"}], "integrity": {"algorithm": "sha256", "digest": "1713ba8cd02f0329b8fed35f40def65d7f12e7d071283ed6315dd61d384a9784"}}}},
      {"id": "artifact:bundle-builder-06", "type": "artifact", "name": "tools/build_spec_0_6_bundle.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/build_spec_0_6_bundle.py"}], "integrity": {"algorithm": "sha256", "digest": "33f97717e6c240ea84a1e5b1044fbfae6d198012b133a250a9a17326b6422117"}}}},
      {"id": "artifact:spec-07-draft", "type": "artifact", "name": "AWP 0.7.0 working draft", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/drafts/0.7.0/index.md"}], "integrity": {"algorithm": "sha256", "digest": "48ef52956664b66400986c33d42d5fe500ba6300d0e76478d343b46282ec9dcc"}}}},
      {"id": "artifact:conformance", "type": "artifact", "name": "Conformance evidence", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "conformance/matrix.md"}], "integrity": {"algorithm": "sha256", "digest": "4c60877ab87a3e81006f33ecd76893e886832cd9923babbf7a9afc4d85659969"}}}},
      {"id": "artifact:synthetic-pilot", "type": "artifact", "name": "Coordination-awareness synthetic pilot report", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "experiments/coordination-awareness/results/pilot-report.md"}], "integrity": {"algorithm": "sha256", "digest": "f9c1cfc441e2639a67171c8199a333c31e7f99b2fb1d99320973a4d635ac25a4"}}}}
    ],
    "executions": [],
    "changes": [
      {"id": "change:awp-rename", "type": "change", "summary": "Renamed the protocol repository-wide from its former name to Agent Workstate Protocol (AWP) and refreshed generated artifacts and integrity metadata.", "artifacts": ["artifact:spec-06", "artifact:spec-06-bundle", "artifact:core-06", "artifact:coordination-03", "artifact:coordination-schema-03", "artifact:module-registry-06", "artifact:discovery"]},
      {"id": "change:explicit-specification", "type": "change", "summary": "Introduced explicit governing-specification binding in the separately versioned AWP 0.7.0 working draft while preserving AWP 0.6.0 and Discovery 0.1.", "artifacts": ["artifact:spec-07-draft", "artifact:discovery", "artifact:discovery-schema"]},
      {"id": "change:repository-credibility", "type": "change", "summary": "Reorganized the project into stable, draft, distribution, conformance, documentation, experiment, and research areas; added governance, citation, security, CI, reproducibility, requirement inventory, related work, and a disclosed synthetic pilot.", "artifacts": ["artifact:spec-06", "artifact:spec-06-bundle", "artifact:spec-07-draft", "artifact:conformance", "artifact:synthetic-pilot"]}
    ],
    "risks": [{"id": "risk:synthetic-evidence", "type": "risk", "statement": "The synthetic pilot tests encoded instrumentation behavior and cannot establish real-agent effectiveness, coordination cost, or external validity.", "status": "active", "mitigation": "Run the preregistered protocol with independent implementations and publish raw data."}],
    "checkpoints": [{"id": "checkpoint:user-arbitration", "type": "checkpoint", "frontier": ["evt:user-arbitration-checkpoint"], "created_at": "2026-09-04T06:46:00Z", "summary": "AWP 0.6.0 remains the stable tagged release; AWP 0.7.0 is an explicitly separated working draft; repository governance, citation, conformance, reproducibility, research positioning, synthetic-pilot infrastructure, and a bounded user-arbitration protocol for interacting agent changes are implemented and locally validated.", "recommended_next_action": {"action": "Run the preregistered coordination-awareness protocol with at least two independent agent implementations and publish complete raw results.", "requires_authority": false}, "resumption_level": "semantic"}],
    "sessions": []
  },
  "modules": {
    "urn:awp:handoff": {
      "handoff": {"id": "handoff:user-arbitration", "type": "handoff", "module": "urn:awp:handoff", "checkpoint": "checkpoint:user-arbitration", "completeness": "portable", "intended_audience": ["human", "agent"], "requested_action": "Run the preregistered coordination-awareness protocol with independent agent implementations.", "authority_ceiling": ["read_only", "local_write"], "resumption_level": "semantic", "do_not_assume": ["A production coordination implementation or live coordination service exists", "Synthetic-pilot results demonstrate agent effectiveness", "Coordination C3 enforcement can be supplied by a static file", "Imported authority grants external side effects"], "dependencies": [{"ref": "artifact:spec-06", "availability": "retrievable"}, {"ref": "artifact:spec-07-draft", "availability": "retrievable"}, {"ref": "artifact:conformance", "availability": "retrievable"}, {"ref": "artifact:synthetic-pilot", "availability": "retrievable"}]},
      "resume": {"id": "resume:awp-project", "type": "resume", "module": "urn:awp:handoff", "handoff": "handoff:user-arbitration", "checkpoint": "checkpoint:user-arbitration", "mode": "project_reentry", "read_first": ["goal:awp-design", "constraint:no-private-cot", "decision:release-discipline", "decision:user-arbitration", "claim:credibility-overhaul", "risk:synthetic-evidence", "task:coordination-prototype", "task:user-arbitration-protocol"], "required_artifacts": ["artifact:spec-07-draft", "artifact:conformance", "artifact:synthetic-pilot"], "recommended_next_action": "Run the preregistered coordination-awareness protocol with independent agent implementations and publish complete raw results.", "freshness_policy": "verify_before_continue", "on_stale": "refresh_workstate", "authority_ceiling": ["read_only", "local_write"]}
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
