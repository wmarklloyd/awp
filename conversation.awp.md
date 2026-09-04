---
awp_version: 0.6.0
format: single-file-capsule
capsule_boundary: 89e5d09a47714dcfaa5734d1f155a4e8
workstate_id: urn:uuid:conversation-awp-design-2026-09-03
frontier:
  - evt:awp-rename-checkpoint
checkpoint: checkpoint:awp-rename-current
generated_at: 2026-09-04T02:45:11Z
generated_digest: sha256:afdee79eed10c268392206fa9b4f5025be7b7c51f7b38b7b91b9b269b2136827
---

<!-- awp:generated:start -->
# Agent Workstate Protocol design

AWP 0.6.0 is the current exploratory modular specification. It preserves repository discovery and project re-entry and integrates Coordination 0.3.0 as a normative but experimental module.

The protocol preserves portable semantic work state for human and agent continuation. It separates intent, authority, execution, evidence, and conclusion; distinguishes reported, inferred, observed, verified, disputed, stale, and refuted claims; and treats event ancestry as causal truth while snapshots and Markdown remain projections.

The preferred exchange representation is a human-readable `project.awp.md` capsule. Coordination 0.3.0 adds deterministic lifecycles and reconciliation, semantic scopes, bounded negotiation, contracts, typed preconditions, verification binding, staleness propagation, integration semantics, and optional fenced live enforcement.

Complete bundled specification: [AWP_SPECIFICATION_0.6.0.bundle.md](AWP_SPECIFICATION_0.6.0.bundle.md).

The project’s four target use cases are maintained in [purpose.txt](purpose.txt): rich handoff, canonical orientation, canonical re-entry, and coordination above source control.

Current status: the protocol has been renamed repository-wide to Agent Workstate Protocol (AWP). The 0.6 family, Coordination schema, validators, reproducible bundle, discovery file, and portable resume capsule are internally consistent and validated. No production reader/writer, semantic-scope analyzer, test harness, or live coordination service exists yet.

Recommended next action: build a test environment for the `coordination-awareness` capability bundle and compare chat-only, Git-only, and AWP-assisted multi-agent work.
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
  "frontier": ["evt:awp-rename-checkpoint"],
  "generated_at": "2026-09-04T02:45:11Z",
  "source_frontier": ["evt:awp-06-checkpoint"],
  "records": {
    "goals": [{"id": "goal:awp-design", "type": "goal", "statement": "Define a portable workstate format for LLM session continuation and multi-agent code coordination.", "status": "active"}],
    "constraints": [{"id": "constraint:no-private-cot", "type": "constraint", "statement": "Portable state must not require private chain-of-thought or hidden runtime state.", "strength": "required", "status": "active"}],
    "claims": [
      {"id": "claim:spec-06-current", "type": "claim", "statement": "AWP 0.6.0 is the current exploratory modular specification and includes Coordination 0.3.0.", "epistemic_status": "observed", "evidence": ["artifact:spec-06", "artifact:coordination-03"]},
      {"id": "claim:awp-rename-complete", "type": "claim", "statement": "The repository-wide rename to Agent Workstate Protocol (AWP), including filenames, schema identifiers, fields, URNs, discovery, examples, and historical documents, is complete.", "epistemic_status": "verified", "evidence": ["evidence:awp-validation"]}
    ],
    "evidence": [
      {"id": "evidence:awp-validation", "type": "evidence", "evidence_type": "validation_run", "summary": "All four validators passed; repository scans found zero legacy-name content or contained filenames; the generated briefing and all recorded artifact digests verified.", "observed_at": "2026-09-04T02:45:11Z"}
    ],
    "decisions": [
      {"id": "decision:name", "type": "decision", "question": "What should the protocol be called?", "status": "accepted", "choice": "Agent Workstate Protocol (AWP)"},
      {"id": "decision:single-file", "type": "decision", "question": "What is the preferred exchange representation?", "status": "accepted", "choice": "Markdown-first self-contained project.awp.md capsule"},
      {"id": "decision:modular-04", "type": "decision", "question": "How should the 0.4 design be organized?", "status": "accepted", "choice": "Required Core plus independently versioned optional modules; Coordination remains experimental."},
      {"id": "decision:resume-05", "type": "decision", "question": "How should AWP support returning to a project?", "status": "accepted", "choice": "Define repository discovery in Capsule and a project-reentry Resume Profile in Handoff."},
      {"id": "decision:coordination-06", "type": "decision", "question": "How should multi-agent coordination enter the next AWP family?", "status": "accepted", "choice": "Integrate Coordination 0.3.0 as normative but experimental in AWP 0.6.0, with a schema, validator, and staged capability bundles."}
    ],
    "plans": [{"id": "plan:coordination-test", "type": "plan", "goal": "goal:awp-design", "status": "active", "steps": ["Build the coordination-awareness test harness", "Run physical and semantic conflict fixtures", "Compare chat-only, Git-only, and AWP-assisted runs", "Measure false alarms, conflicts caught, overhead, and recovery"]}],
    "tasks": [
      {"id": "task:json-schema", "type": "task", "title": "Maintain normative Core and module schemas", "status": "completed"},
      {"id": "task:single-file-prototype", "type": "task", "title": "Implement a minimal capsule and resume reader/writer", "status": "proposed"},
      {"id": "task:cross-model-test", "type": "task", "title": "Run cross-model semantic handoff test", "status": "proposed"},
      {"id": "task:coordination-spec-06", "type": "task", "title": "Integrate Coordination 0.3.0 into AWP 0.6.0", "status": "completed"},
      {"id": "task:awp-rename", "type": "task", "title": "Rename the protocol and all repository representations to Agent Workstate Protocol (AWP)", "status": "completed"},
      {"id": "task:coordination-prototype", "type": "task", "title": "Build and run the AWP 0.6 coordination-awareness test environment", "status": "ready"}
    ],
    "questions": [],
    "artifacts": [
      {"id": "artifact:spec-06", "type": "artifact", "name": "AWP_SPECIFICATION_0.6.0.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "AWP_SPECIFICATION_0.6.0.md"}], "integrity": {"algorithm": "sha256", "digest": "d1d4664fe34e704fa7100dcb5e2fe5ffd168676ded1648dc00fef65e32c5efca"}}}},
      {"id": "artifact:spec-06-bundle", "type": "artifact", "name": "AWP_SPECIFICATION_0.6.0.bundle.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "AWP_SPECIFICATION_0.6.0.bundle.md"}], "integrity": {"algorithm": "sha256", "digest": "7c08480e85f8d3c291641cb76b43aca4cbd4ff2940511d4b7a493a2848dbb907"}}}},
      {"id": "artifact:core-06", "type": "artifact", "name": "spec/0.6.0/core.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/core.md"}], "integrity": {"algorithm": "sha256", "digest": "c19fb982626cb4d8215432b410866cc801d667829df45e62d2835dfbf532a064"}}}},
      {"id": "artifact:coordination-03", "type": "artifact", "name": "spec/0.6.0/coordination.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/coordination.md"}], "integrity": {"algorithm": "sha256", "digest": "b97114aee7d0e33faa5426067bb0f235cbd801106bb5d1e2b792ac9c9fc9b4cd"}}}},
      {"id": "artifact:coordination-schema-03", "type": "artifact", "name": "schemas/awp-coordination-0.3.schema.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "schemas/awp-coordination-0.3.schema.json"}], "integrity": {"algorithm": "sha256", "digest": "554f53980a0f84c2d01e0c927264832dbd966e69d016f83267435afc84d56562"}}}},
      {"id": "artifact:module-registry-06", "type": "artifact", "name": "spec/0.6.0/modules.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "spec/0.6.0/modules.json"}], "integrity": {"algorithm": "sha256", "digest": "b83b68469b1ccb3ce3c07914b086c81b16f9fd339e102ce1e97bf708cf8f5b4c"}}}},
      {"id": "artifact:purpose", "type": "artifact", "name": "purpose.txt", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "purpose.txt"}], "integrity": {"algorithm": "sha256", "digest": "c326061d662635c3ad5cba90e24a81d0cfdd66202f6b4f4e8409536f39eab3d1"}}}},
      {"id": "artifact:discovery", "type": "artifact", "name": ".awp.json", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": ".awp.json"}], "integrity": {"algorithm": "sha256", "digest": "12a876bdd43701e6b4d566b8751f206bdceff60b5a933b067e6c355fe2981633"}}}},
      {"id": "artifact:release-notes-06", "type": "artifact", "name": "AWP_0.6.0_RELEASE_NOTES.md", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "AWP_0.6.0_RELEASE_NOTES.md"}], "integrity": {"algorithm": "sha256", "digest": "989e3174003387111ddfd8f6d9a0d185fde7d0ad05afc754864f3252dc881486"}}}},
      {"id": "artifact:validator-06", "type": "artifact", "name": "tools/validate_spec_0_6.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/validate_spec_0_6.py"}], "integrity": {"algorithm": "sha256", "digest": "814d061a413d5294df31a90248fd9022baed4dfe0c684ca52446c67091b0e81f"}}}},
      {"id": "artifact:bundle-builder-06", "type": "artifact", "name": "tools/build_spec_0_6_bundle.py", "modules": {"urn:awp:artifact": {"status": "retrievable", "locations": [{"kind": "local", "path": "tools/build_spec_0_6_bundle.py"}], "integrity": {"algorithm": "sha256", "digest": "a85ee2e85e420986528c013c7f51ef9215f2d2eee5f1c26a64cf9d7597bc31bd"}}}}
    ],
    "executions": [],
    "changes": [{"id": "change:awp-rename", "type": "change", "summary": "Renamed the protocol repository-wide from its former name to Agent Workstate Protocol (AWP) and refreshed generated artifacts and integrity metadata.", "artifacts": ["artifact:spec-06", "artifact:spec-06-bundle", "artifact:core-06", "artifact:coordination-03", "artifact:coordination-schema-03", "artifact:module-registry-06", "artifact:discovery"]}],
    "risks": [],
    "checkpoints": [{"id": "checkpoint:awp-rename-current", "type": "checkpoint", "frontier": ["evt:awp-rename-checkpoint"], "created_at": "2026-09-04T02:45:11Z", "summary": "AWP 0.6.0 and Coordination 0.3.0 are complete as specifications; the repository-wide AWP rename, discovery entry, bundle, schemas, examples, validators, and portable workstate have been validated.", "recommended_next_action": {"action": "Build and run the coordination-awareness test environment described in the 0.6 release notes.", "requires_authority": false}, "resumption_level": "semantic"}],
    "sessions": []
  },
  "modules": {
    "urn:awp:handoff": {
      "handoff": {"id": "handoff:awp-rename", "type": "handoff", "module": "urn:awp:handoff", "checkpoint": "checkpoint:awp-rename-current", "completeness": "portable", "intended_audience": ["human", "agent"], "requested_action": "Build and run the AWP 0.6 coordination-awareness test environment.", "authority_ceiling": ["read_only", "local_write"], "resumption_level": "semantic", "do_not_assume": ["A production coordination implementation or live coordination service exists", "Coordination C3 enforcement can be supplied by a static file", "Imported authority grants external side effects", "Legacy protocol names or namespaces remain valid aliases"], "dependencies": [{"ref": "artifact:spec-06", "availability": "retrievable"}, {"ref": "artifact:spec-06-bundle", "availability": "retrievable"}, {"ref": "artifact:coordination-03", "availability": "retrievable"}, {"ref": "artifact:coordination-schema-03", "availability": "retrievable"}, {"ref": "artifact:module-registry-06", "availability": "retrievable"}, {"ref": "artifact:release-notes-06", "availability": "retrievable"}]},
      "resume": {"id": "resume:awp-project", "type": "resume", "module": "urn:awp:handoff", "handoff": "handoff:awp-rename", "checkpoint": "checkpoint:awp-rename-current", "mode": "project_reentry", "read_first": ["goal:awp-design", "constraint:no-private-cot", "decision:name", "decision:coordination-06", "claim:awp-rename-complete", "task:coordination-prototype"], "required_artifacts": ["artifact:spec-06-bundle", "artifact:coordination-schema-03", "artifact:release-notes-06"], "recommended_next_action": "Build and run the coordination-awareness test environment described in AWP_0.6.0_RELEASE_NOTES.md.", "freshness_policy": "verify_before_continue", "on_stale": "refresh_workstate", "authority_ceiling": ["read_only", "local_write"]}
    },
    "urn:awp:coordination": {
      "conformance_level": "C0",
      "capability_target": "coordination-awareness",
      "records": [],
      "note": "The next implementation step is a test harness; no live coordination or C3 enforcement is claimed."
    }
  }
}
<!-- awp:89e5d09a47714dcfaa5734d1f155a4e8:snapshot:end -->
