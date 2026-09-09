# Agent Workshare Protocol 0.8.0 — Working Draft Assets

**Status:** Generated working-draft artifact; not a release  
**Companion of:** `dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`  
**Purpose:** Verbatim copies of the module registry, requirement inventory, and draft schemas for systems that cannot read `schemas/` and `spec/drafts/0.8.0/` directly. Orientation does not require this file; the bundle's asset table carries each asset's digest.

Do not edit this generated file directly; regenerate it from the source files when the draft changes.

---

## Silo profile schema — `schemas/awp-silo-0.1.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:silo:0.1.0",
  "title": "AWP silo-v1 profile records",
  "description": "Structural records owned by Synchronization 0.5 in the AWP 0.8 draft. Does not validate ancestry, authority, dependency closure, or publication.",
  "oneOf": [{"$ref": "#/$defs/silo"}, {"$ref": "#/$defs/adoption"}],
  "$defs": {
    "id": {"type": "string", "minLength": 1, "pattern": "^\\S+$"},
    "text": {"type": "string", "minLength": 1},
    "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
    "ids": {"type": "array", "uniqueItems": true, "items": {"$ref": "#/$defs/id"}},
    "pin": {
      "type": "object",
      "required": ["workstate_id", "frontier", "specification", "capsule_digest"],
      "properties": {
        "workstate_id": {"$ref": "#/$defs/id"},
        "frontier": {"allOf": [{"$ref": "#/$defs/ids"}], "minItems": 1},
        "specification": {"$ref": "#/$defs/id"},
        "capsule_digest": {"$ref": "#/$defs/digest"},
        "generated_digest": {"$ref": "#/$defs/digest"},
        "checkpoint": {"$ref": "#/$defs/id"}
      },
      "additionalProperties": true
    },
    "recordPin": {
      "type": "object",
      "required": ["workstate_id", "record_id", "revision"],
      "properties": {
        "workstate_id": {"$ref": "#/$defs/id"},
        "record_id": {"$ref": "#/$defs/id"},
        "revision": {"type": "integer", "minimum": 1}
      },
      "additionalProperties": true
    },
    "pins": {"type": "array", "uniqueItems": true, "items": {"$ref": "#/$defs/recordPin"}},
    "common": {
      "type": "object",
      "required": ["id", "type", "module", "profile", "revision", "status", "created_by", "created_at"],
      "properties": {
        "id": {"$ref": "#/$defs/id"},
        "module": {"const": "urn:awp:sync"},
        "profile": {"const": "silo-v1"},
        "revision": {"type": "integer", "minimum": 1},
        "created_by": {"$ref": "#/$defs/id"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    },
    "policy": {
      "type": "object",
      "required": ["decision_owner", "policy_ref", "permitted_targets"],
      "properties": {
        "decision_owner": {"$ref": "#/$defs/id"},
        "policy_ref": {"$ref": "#/$defs/recordPin"},
        "permitted_targets": {"$ref": "#/$defs/ids"}
      },
      "additionalProperties": true
    },
    "bindingIdentity": {
      "type": "object",
      "required": ["workstate_id", "project_id", "store_id", "scope_model", "binding_epoch"],
      "properties": {
        "workstate_id": {"$ref": "#/$defs/id"},
        "project_id": {"$ref": "#/$defs/id"},
        "store_id": {"$ref": "#/$defs/id"},
        "scope_model": {"$ref": "#/$defs/id"},
        "binding_epoch": {"type": "integer", "minimum": 1}
      },
      "additionalProperties": true
    },
    "workLocation": {
      "type": "object",
      "required": ["mode"],
      "properties": {
        "mode": {"enum": ["none", "isolated", "shared"]},
        "location": {"$ref": "#/$defs/text"},
        "isolation_evidence": {"allOf": [{"$ref": "#/$defs/ids"}], "minItems": 1},
        "common_binding": {"$ref": "#/$defs/bindingIdentity"},
        "scope_mapping": {"$ref": "#/$defs/text"},
        "atomicity_mechanism": {"$ref": "#/$defs/text"},
        "coverage_evidence": {"allOf": [{"$ref": "#/$defs/ids"}], "minItems": 1}
      },
      "allOf": [
        {"if": {"properties": {"mode": {"const": "isolated"}}, "required": ["mode"]}, "then": {"required": ["location", "isolation_evidence"]}},
        {"if": {"properties": {"mode": {"const": "shared"}}, "required": ["mode"]}, "then": {"required": ["location", "common_binding", "scope_mapping", "atomicity_mechanism", "coverage_evidence"]}}
      ],
      "additionalProperties": true
    },
    "override": {
      "type": "object",
      "required": ["inherited", "operation", "reason"],
      "properties": {
        "inherited": {"$ref": "#/$defs/recordPin"},
        "operation": {"enum": ["replace", "tombstone"]},
        "replacement": {"$ref": "#/$defs/recordPin"},
        "reason": {"$ref": "#/$defs/text"}
      },
      "allOf": [
        {"if": {"properties": {"operation": {"const": "replace"}}, "required": ["operation"]}, "then": {"required": ["replacement"]}},
        {"if": {"properties": {"operation": {"const": "tombstone"}}, "required": ["operation"]}, "then": {"not": {"required": ["replacement"]}}}
      ],
      "additionalProperties": true
    },
    "silo": {
      "allOf": [{"$ref": "#/$defs/common"}],
      "type": "object",
      "required": ["workstate_id", "canonical_workstate_id", "parent_kind", "origin", "base", "fork_event", "purpose", "owner", "adoption_policy", "work_location", "inherited_records", "overrides"],
      "properties": {
        "type": {"const": "silo"},
        "status": {"enum": ["active", "paused", "closed"]},
        "workstate_id": {"$ref": "#/$defs/id"},
        "canonical_workstate_id": {"$ref": "#/$defs/id"},
        "parent_kind": {"enum": ["canonical", "silo"]},
        "origin": {"$ref": "#/$defs/pin"},
        "base": {"$ref": "#/$defs/pin"},
        "fork_event": {"$ref": "#/$defs/id"},
        "purpose": {"$ref": "#/$defs/text"},
        "owner": {"$ref": "#/$defs/id"},
        "adoption_policy": {"$ref": "#/$defs/policy"},
        "work_location": {"$ref": "#/$defs/workLocation"},
        "coordination_binding": {"$ref": "#/$defs/bindingIdentity"},
        "inherited_records": {"$ref": "#/$defs/pins"},
        "overrides": {"type": "array", "items": {"$ref": "#/$defs/override"}},
        "closure_reason": {"$ref": "#/$defs/text"},
        "checkpoint": {"$ref": "#/$defs/id"}
      },
      "if": {"properties": {"status": {"const": "closed"}}, "required": ["status"]},
      "then": {"required": ["closure_reason", "checkpoint"]},
      "additionalProperties": true
    },
    "mapping": {
      "type": "object",
      "required": ["source", "destination", "operation"],
      "properties": {
        "source": {"$ref": "#/$defs/recordPin"},
        "destination": {"$ref": "#/$defs/recordPin"},
        "operation": {"enum": ["create", "revise"]},
        "expected_revision": {"type": "integer", "minimum": 1},
        "transformation_evidence": {"$ref": "#/$defs/ids"}
      },
      "if": {"properties": {"operation": {"const": "revise"}}, "required": ["operation"]},
      "then": {"required": ["expected_revision"]},
      "additionalProperties": true
    },
    "divergence": {
      "type": "object",
      "required": ["inherited", "current", "basis", "result", "disposition"],
      "properties": {
        "inherited": {"$ref": "#/$defs/recordPin"},
        "current": {"oneOf": [{"$ref": "#/$defs/recordPin"}, {"type": "null"}]},
        "basis": {"$ref": "#/$defs/text"},
        "result": {"enum": ["unchanged", "changed", "missing", "contested", "unknown"]},
        "disposition": {"$ref": "#/$defs/text"},
        "evidence": {"$ref": "#/$defs/ids"}
      },
      "additionalProperties": true
    },
    "adoption": {
      "allOf": [
        {"$ref": "#/$defs/common"},
        {"if": {"properties": {"status": {"enum": ["approved", "pending", "adopted"]}}, "required": ["status"]}, "then": {"required": ["approval"], "properties": {"closure": {"properties": {"state": {"enum": ["complete", "extended", "rederived"]}}}}}},
        {"if": {"properties": {"status": {"const": "adopted"}}, "required": ["status"]}, "then": {"required": ["publication_ref"]}},
        {"if": {"properties": {"status": {"enum": ["stale", "rejected", "cancelled", "failed"]}}, "required": ["status"]}, "then": {"required": ["disposition"]}}
      ],
      "type": "object",
      "required": ["source", "target", "selected_records", "proposed_records", "mapping", "closure", "divergence", "scopes", "decision_owner", "policy_ref", "publisher", "idempotency_key", "bypassed_ancestors"],
      "properties": {
        "type": {"const": "silo_adoption"},
        "status": {"enum": ["proposed", "approved", "pending", "adopted", "stale", "rejected", "cancelled", "failed"]},
        "source": {"$ref": "#/$defs/pin"},
        "target": {"$ref": "#/$defs/pin"},
        "selected_records": {"allOf": [{"$ref": "#/$defs/pins"}], "minItems": 1},
        "proposed_records": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["id", "type", "revision"]}},
        "mapping": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/mapping"}},
        "closure": {
          "type": "object", "required": ["state", "evidence"],
          "properties": {"state": {"enum": ["complete", "extended", "rederived", "incomplete", "unknown"]}, "evidence": {"$ref": "#/$defs/ids"}},
          "additionalProperties": true
        },
        "divergence": {"type": "array", "items": {"$ref": "#/$defs/divergence"}},
        "scopes": {"allOf": [{"$ref": "#/$defs/ids"}], "minItems": 1},
        "decision_owner": {"$ref": "#/$defs/id"},
        "policy_ref": {"$ref": "#/$defs/recordPin"},
        "publisher": {"$ref": "#/$defs/id"},
        "idempotency_key": {"$ref": "#/$defs/id"},
        "bypassed_ancestors": {"$ref": "#/$defs/ids"},
        "approval": {
          "type": "object", "required": ["proposal_revision", "approved_by", "evidence"],
          "properties": {"proposal_revision": {"type": "integer", "minimum": 1}, "approved_by": {"$ref": "#/$defs/id"}, "evidence": {"allOf": [{"$ref": "#/$defs/ids"}], "minItems": 1}},
          "additionalProperties": true
        },
        "publication_ref": {"$ref": "#/$defs/id"},
        "disposition": {"$ref": "#/$defs/text"}
      },
      "additionalProperties": true
    }
  }
}
```

---

## Module registry — `spec/drafts/0.8.0/modules.json`

```json
{
  "$schema": "../../../schemas/awp-module-registry-0.8.schema.json",
  "family": "AWP",
  "family_version": "0.8.0",
  "event_schema_versions": ["0.2"],
  "modules": [
    {
      "id": "urn:awp:core",
      "name": "AWP Core",
      "version": "0.8.0",
      "status": "required",
      "document": "core.md",
      "schema": "../../../schemas/awp-core-0.8.schema.json",
      "dependencies": []
    },
    {
      "id": "urn:awp:capsule",
      "name": "AWP Capsule",
      "version": "0.5.0",
      "status": "optional",
      "document": "capsule.md",
      "schema": "../../../schemas/awp-capsule-0.5.schema.json",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" }
      ]
    },
    {
      "id": "urn:awp:handoff",
      "name": "AWP Handoff",
      "version": "0.5.0",
      "status": "optional",
      "document": "handoff.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" }
      ]
    },
    {
      "id": "urn:awp:artifact",
      "name": "AWP Artifact",
      "version": "0.5.0",
      "status": "optional",
      "document": "artifact.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" }
      ]
    },
    {
      "id": "urn:awp:sync",
      "name": "AWP Synchronization",
      "version": "0.5.0",
      "status": "optional",
      "document": "synchronization.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" }
      ],
      "conditional_dependencies": [
        { "when_capability": "silo-v1", "id": "urn:awp:capsule", "version": "0.5.x" }
      ]
    },
    {
      "id": "urn:awp:coordination",
      "name": "AWP Coordination",
      "version": "0.5.0",
      "status": "experimental",
      "document": "coordination.md",
      "schema": "../../../schemas/awp-coordination-0.5.schema.json",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" },
        { "id": "urn:awp:sync", "version": "0.5.x" }
      ]
    },
    {
      "id": "urn:awp:security",
      "name": "AWP Security",
      "version": "0.5.0",
      "status": "optional",
      "document": "security.md",
      "schema": "../../../schemas/awp-security-0.5.schema.json",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" }
      ],
      "conditional_dependencies": [
        {
          "when_capability": "artifact-controls",
          "id": "urn:awp:artifact",
          "version": "0.5.x"
        }
      ]
    },
    {
      "id": "urn:awp:cooperation",
      "name": "AWP Cooperation Contracts",
      "version": "0.1.0",
      "status": "experimental",
      "document": "cooperation-contracts.md",
      "schema": "../../../schemas/awp-cooperation-0.1.schema.json",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.8.x" },
        { "id": "urn:awp:capsule", "version": "0.5.x" },
        { "id": "urn:awp:handoff", "version": "0.5.x" }
      ],
      "conditional_dependencies": [
        {"when_capability": "guarded-scope-coordination", "id": "urn:awp:coordination", "version": "0.5.x"}
      ]
    }
  ],
  "informative_documents": [
    {
      "name": "AWP Adapter Framework",
      "version": "0.5.0",
      "document": "adapters.md"
    },
    {
      "name": "AWP Open Issues",
      "version": "0.8.0",
      "document": "open-issues.md"
    }
  ]
}
```

---

## Requirement inventory — `spec/drafts/0.8.0/requirements.json`

```json
{
  "family": "AWP",
  "version": "0.8.0-draft",
  "status": "generated-review-inventory",
  "normative_authority": "source prose",
  "requirements": [
    {
      "id": "AWP-FAMILY-001",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 9,
      "statement": "The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals."
    },
    {
      "id": "AWP-FAMILY-002",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 47,
      "statement": "Every AWP 0.8 manifest MUST contain a `modules` array. It MUST declare exactly one Core entry, and that entry MUST be required. The following is a module-declaration excerpt rather than a complete manifest:"
    },
    {
      "id": "AWP-FAMILY-003",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 81,
      "statement": "A writer MUST declare every module whose records, events, or required processing rules affect the effective workstate. It MUST include compatible declarations for all direct dependencies. It MUST mark a module required only when ignoring that module would prevent the receiver from safely performing the declared continuation."
    },
    {
      "id": "AWP-FAMILY-004",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 83,
      "statement": "If a module is required, every dependency needed to interpret it MUST also be required. If an optional module depends on another optional module, a receiver may ignore both while preserving their data."
    },
    {
      "id": "AWP-FAMILY-005",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 85,
      "statement": "Core owns the unqualified Core record types and fields. A module defining a new record type MUST include a `module` field naming its module ID. A module extending a Core record MUST place its fields under that record's `modules` object, keyed by module ID. Module-owned event kinds use the common event envelope's required `module` field. These rules prevent independent subspecifications from claiming the same unqualified name."
    },
    {
      "id": "AWP-FAMILY-006",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 89,
      "statement": "A reader that encounters an unknown optional module MAY continue using understood modules. It MUST preserve or explicitly disclose loss of the unknown data, and it MUST NOT infer semantics from unknown fields."
    },
    {
      "id": "AWP-FAMILY-007",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 91,
      "statement": "A reader that encounters an unknown required module MUST NOT claim a complete interpretation or perform a continuation that could depend on it. It SHOULD still present the human briefing, validate understood envelopes, and report the unsupported module."
    },
    {
      "id": "AWP-FAMILY-008",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 126,
      "statement": "The conventional project-named form is `<project-name>.awp.md`. Producers MAY retain versioned archival copies using `<project-name>.v<revision>.awp.md`, such as `project.v2.awp.md`. This filename revision is only a human-facing label; protocol and workstate identity remain defined by the capsule metadata."
    },
    {
      "id": "AWP-FAMILY-009",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 132,
      "statement": "Every shared AWP project workstate MUST identify the exact specification artifact that governs it. A project capsule MUST carry an explicit `specification` reference in its own metadata. That reference SHOULD be an immutable, version-pinned URI to a published specification bundle. A repository-relative local copy MAY be used when network retrieval is unavailable or inappropriate."
    },
    {
      "id": "AWP-FAMILY-010",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 134,
      "statement": "A reader MUST interpret a workstate according to its declared specification and module versions. It MUST NOT silently substitute a newer, older, or otherwise different specification, infer compatibility from a filename, or treat a moving branch URL as version-pinned. If the declared specification is unavailable or unsupported, the reader MUST report that condition rather than guess."
    },
    {
      "id": "AWP-FAMILY-011",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 136,
      "statement": "AWP `0.x` is exploratory. A new minor family or module release MAY make incompatible changes. A patch release MUST NOT introduce incompatible normative semantics. Explicit specification binding allows protocol development to proceed without requiring backward compatibility between exploratory minor releases. Implementations MAY support multiple versions or provide explicit migrations, but conformance to one version does not imply support for another."
    },
    {
      "id": "AWP-FAMILY-012",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 138,
      "statement": "The family version and module versions remain independent. The family version identifies a tested set of module releases, and a later family release may reuse an unchanged module version. Writers that change protocol semantics MUST publish a new versioned specification artifact and update affected workstates deliberately. Implementations MUST determine support by the declared specification, module ID, and module version, not by comparing only `awp_version`."
    },
    {
      "id": "AWP-FAMILY-013",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 158,
      "statement": "An implementation MUST satisfy the conformance requirements in each module for every role it claims. Supporting AWP Core alone is valid AWP conformance. It does not imply support for capsules, handoffs, synchronization, coordination, signatures, encryption, or adapters."
    },
    {
      "id": "AWP-FAMILY-014",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 162,
      "statement": "Every module and binding MUST preserve these rules:"
    },
    {
      "id": "AWP-FAMILY-015",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 171,
      "statement": "8. Optional modules MUST NOT redefine Core field meanings."
    },
    {
      "id": "AWP-FAMILY-016",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 179,
      "statement": "The migration is intentionally incompatible: a 0.8 project capsule identifies its exact governing specification and project discovery mode in its own metadata. A 0.8 reader MUST NOT silently substitute another specification. The project discovery document and the capsule MUST agree on the current workstate and governing specification."
    },
    {
      "id": "AWP-FAMILY-017",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 181,
      "statement": "An upgrader from an earlier AWP workstate MUST add the governing `specification` and `discovery: project` to capsule metadata, update Capsule to `0.5.0`, and create or update the project discovery document. Historical events remain unchanged."
    },
    {
      "id": "AWP-FAMILY-018",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 185,
      "statement": "A specification family MAY distribute a generated **Agent Entry Core** beside a complete specification bundle. Its purpose is to give a model or other bounded-context participant the minimum cross-cutting rules needed to orient safely before it retrieves task-specific modules. It is a derived presentation artifact, not an additional source of normative semantics."
    },
    {
      "id": "AWP-FAMILY-019",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 187,
      "statement": "An Agent Entry Core MUST identify its exact source bundle, source bundle SHA-256 digest, family version, generator identity, and the source documents and schemas that its task-routing guidance can name. A reader MUST verify the recorded digest against the available source bundle before relying on the profile. A profile whose bundle is unavailable or whose digest does not match is unavailable, not merely advisory; the reader MUST retrieve and use the complete governing specification or decline the continuation."
    },
    {
      "id": "AWP-FAMILY-020",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 189,
      "statement": "The Entry Core MUST include the family invariants needed before any continuation, a statement that it cannot override the source specification, and mandatory expansion triggers. Those triggers MUST include an unknown or required module, a missing or unverifiable profile, an ambiguity or conflict, a requested semantic change spanning more than one routed module, and release, migration, or cross-module integration work. A receiver MAY apply stricter triggers under its own policy."
    },
    {
      "id": "AWP-FAMILY-021",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 191,
      "statement": "Task-routing guidance in an Entry Core is non-normative performance guidance. It MUST name the source modules and schemas that a task class normally requires, including direct dependencies, but it MUST NOT claim that the listed material is sufficient in every circumstance or weaken a reader's obligation to obtain relevant normative state. When the profile and its governing source appear to disagree, the source governs and the reader MUST expand its reading rather than choose the profile."
    },
    {
      "id": "AWP-FAMILY-022",
      "source": "spec/drafts/0.8.0/index.md",
      "line": 193,
      "statement": "An implementation that claims Agent Entry Core support MUST generate or verify the profile as part of the same reproducible build that produces its source bundle. It MUST expose whether profile verification succeeded and which additional source documents it selected. A gateway MAY enforce selective access, but an instruction to a model alone is not evidence that the model did not read additional material."
    },
    {
      "id": "AWP-CORE-001",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 32,
      "statement": "Every workstate MUST have a stable `workstate_id`. Copying or repackaging a workstate does not change this ID. Forking creates a new workstate ID and records the parent workstate and parent frontier."
    },
    {
      "id": "AWP-CORE-002",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 34,
      "statement": "Record and event IDs MUST be stable and unique within the workstate. Globally collision-resistant IDs are RECOMMENDED. IDs are opaque: consumers MUST NOT derive authority, time, ordering, or record type from their spelling."
    },
    {
      "id": "AWP-CORE-003",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 36,
      "statement": "Timestamps MUST use RFC 3339 and SHOULD use UTC. Causality is determined by event ancestry, not timestamps."
    },
    {
      "id": "AWP-CORE-004",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 71,
      "statement": "The Core module declaration MUST appear exactly once with version `0.8.x` and `required: true`. Module IDs MUST be unique within the array. A module declaration MUST satisfy the dependency and requiredness rules in the family specification."
    },
    {
      "id": "AWP-CORE-005",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 75,
      "statement": "Module-specific manifest data belongs in the owning module declaration's `configuration` object or in a top-level `module_data` object keyed by module ID. Undeclared modules MUST NOT place data there."
    },
    {
      "id": "AWP-CORE-006",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 111,
      "statement": "The owning module MUST be declared in the manifest. Event kind and payload are interpreted according to that module version. An unknown optional-module event remains part of the causal graph even when its payload cannot be interpreted."
    },
    {
      "id": "AWP-CORE-007",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 113,
      "statement": "Lossless processors MUST preserve unknown event fields. An event is immutable; correction, supersession, and redaction lineage use new events."
    },
    {
      "id": "AWP-CORE-008",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 117,
      "statement": "Event parents form a directed acyclic graph. A conforming writer MUST NOT create a cycle. A non-genesis event MUST identify every immediate causal predecessor known to its writer. Concurrent events may have the same parent. A merge or resolution event names all resolved tips as parents."
    },
    {
      "id": "AWP-CORE-009",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 121,
      "statement": "Wall-clock timestamps and array order MUST NOT be used as causal ordering. A `sequence` field is meaningful only within its declared single-writer scope."
    },
    {
      "id": "AWP-CORE-010",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 153,
      "statement": "Imported authority is evidence. A receiver MUST evaluate it against current local policy, authentication, revocation, and scope before action."
    },
    {
      "id": "AWP-CORE-011",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 155,
      "statement": "Actor declarations are materialized in a snapshot's top-level `actors` array. An actor reference in a manifest, event, authority declaration, or record SHOULD resolve to one of those declarations or to an identified external identity binding. An unresolved actor reference has type `unknown`; it does not invalidate historical events or create authentication, trust, or authority."
    },
    {
      "id": "AWP-CORE-012",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 159,
      "statement": "A core record contains `id` and `type` plus the fields below. It MAY include integer `revision`, beginning at `1` when first created. Fields marked required are structural minima; cross-record requirements remain normative even where JSON Schema cannot express them."
    },
    {
      "id": "AWP-CORE-013",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 181,
      "statement": "Core record types may refer to records owned by optional modules. If such a reference affects safe continuation, the referenced module MUST be required."
    },
    {
      "id": "AWP-CORE-014",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 183,
      "statement": "A `consultation` is a bounded request for analysis, advice, critique, or diagnosis from another actor, including a different model or chatbot. It is not a task delegation, authority grant, or instruction to modify the work product. `question` states the specific problem; `requested_action` states the kind and limits of response sought; `context` carries portable facts, observations, attempts, constraints, excerpts, or other material needed to reason about the problem; and `read_first` gives an ordered presentation hint for related records and artifacts in the workstate. A producer SHOULD include the material needed for the consultation directly in `context` when the receiving actor cannot retrieve the referenced workstate or artifacts. A response SHOULD be recorded on a later revision with its respondent, answer, uncertainty, and supporting evidence. The receiving actor's authority ceiling and all applicable guardrails remain in force; advice from a consultation MUST NOT be treated as authorization for an action."
    },
    {
      "id": "AWP-CORE-015",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 208,
      "statement": "An optional module extending a Core record places its fields under `modules.{module-id}`. A module defining a new record type includes `id`, `type`, and `module`. It MUST NOT use an unqualified type name already owned by Core or another module."
    },
    {
      "id": "AWP-CORE-016",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 224,
      "statement": "Confidence MUST NOT replace epistemic status. A verified claim SHOULD identify evidence, procedure, scope, relevant artifact versions, environment, and observation time. Claims outside their recorded scope MUST be treated as unverified."
    },
    {
      "id": "AWP-CORE-017",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 226,
      "statement": "Contradictory claims MUST remain distinct until a resolution event cites the evidence and records the disposition. A summary is not independent evidence."
    },
    {
      "id": "AWP-CORE-018",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 238,
      "statement": "An update SHOULD carry a complete replacement or patch plus `prior_revision`. When a record has a revision, an update MUST apply only when `prior_revision` equals the effective revision and MUST assign the next integer revision. An update without a satisfiable prior revision is a conflict unless its owning module defines a safe commutative rule. A writer MUST NOT use last-write-wins to silently resolve a conflicting revision. Completion, verification, authorization, and external-side-effect transitions SHOULD cite evidence."
    },
    {
      "id": "AWP-CORE-019",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 274,
      "statement": "The `modules` object may contain module-owned materialized state keyed by module ID. Module state MUST NOT redefine Core records. A snapshot-only workstate MUST disclose that audit history is absent and SHOULD identify its source frontier or source digest."
    },
    {
      "id": "AWP-CORE-020",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 276,
      "statement": "When valid event history conflicts with a snapshot, event history is authoritative. Detailed replay and divergence rules belong to AWP Synchronization. A Core-only reader MUST at least compare the declared frontiers and report `current`, `stale`, `divergent`, or `unverifiable`; it MUST NOT silently treat a mismatch as current."
    },
    {
      "id": "AWP-CORE-021",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 280,
      "statement": "A Core reader MUST:"
    },
    {
      "id": "AWP-CORE-022",
      "source": "spec/drafts/0.8.0/core.md",
      "line": 291,
      "statement": "A Core writer MUST:"
    },
    {
      "id": "AWP-CAPSULE-001",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 17,
      "statement": "For a project-named Markdown capsule, the default conventional filename is `<project-name>.awp.md`. When the project name is unavailable or ambiguous, producers SHOULD use `project.awp.md`. A producer MAY retain multiple capsule revisions using `<project-name>.v<revision>.awp.md`, for example `awp.v2.awp.md` or `project.v2026-09-04.awp.md`. The filename is a human-facing locator; it is not the AWP protocol version and MUST NOT override the capsule metadata."
    },
    {
      "id": "AWP-CAPSULE-002",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 19,
      "statement": "A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing."
    },
    {
      "id": "AWP-CAPSULE-003",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 23,
      "statement": "A single-file Markdown capsule is the canonical project workstate document. It MUST carry the metadata needed to interpret itself and be named by the project discovery document. The discovery document and capsule MUST identify the same governing specification and current workstate."
    },
    {
      "id": "AWP-CAPSULE-004",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 25,
      "statement": "The front matter of a project capsule MUST include `format: single-file-capsule` and `discovery: project`. Its `specification` metadata identifies the exact specification artifact governing the workstate. A host MUST resolve the capsule through the project discovery document or a declared project entry point; an arbitrary supplied capsule path is not, by itself, a project or collaboration boundary."
    },
    {
      "id": "AWP-CAPSULE-005",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 27,
      "statement": "When no project entry point names the capsule, an implementation MAY look for the conventional `<project-name>.awp.md` or `project.awp.md` in the project root. It MUST NOT silently choose among multiple candidate capsules. A filename is only a locator and MUST NOT be used to infer protocol compatibility. Discovering a declared URI MUST NOT trigger automatic network access."
    },
    {
      "id": "AWP-CAPSULE-006",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 29,
      "statement": "Agent-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` are outside AWP. They MAY point directly to a capsule, but their presence is not required for AWP conformance."
    },
    {
      "id": "AWP-CAPSULE-007",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 33,
      "statement": "Every project capsule MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first."
    },
    {
      "id": "AWP-CAPSULE-008",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 35,
      "statement": "The briefing MUST begin with metadata containing:"
    },
    {
      "id": "AWP-CAPSULE-009",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 46,
      "statement": "Generated content MUST occur inside exactly one marker pair:"
    },
    {
      "id": "AWP-CAPSULE-010",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 73,
      "statement": "A participant MUST NOT replace another participant's authored capsule content in place. A revision to an existing record MUST increment its `revision` and SHOULD record the prior generated digest. A revised capsule SHOULD identify its predecessor by artifact digest or explicit supersession reference. Consistency edits following an accepted decision belong in a new revision or superseding capsule; recomputing `generated_digest` does not by itself establish authorship, authorization, or continuity with the prior artifact."
    },
    {
      "id": "AWP-CAPSULE-011",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 75,
      "statement": "`specification` identifies the exact specification artifact that governs the workstate. It SHOULD be an immutable, version-pinned URI when the specification is hosted remotely, such as a tagged GitHub raw URL. It MUST NOT use a moving branch URL as though it were version-pinned. A repository-relative local copy MAY be used when network retrieval is unavailable or inappropriate. A reader MUST NOT silently substitute another specification. An unavailable or unsupported declared specification makes the workstate `unverifiable` for protocol interpretation."
    },
    {
      "id": "AWP-CAPSULE-012",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 90,
      "statement": "A host MAY read and validate the complete capsule without presenting every source byte to a human or model participant. A model-facing entry view SHOULD present the front matter and generated briefing first, then materialize only the active Resume, referenced Handoff and checkpoint, ordered `read_first` records, and compact descriptors for required artifacts. The source capsule remains authoritative; the entry view is a disposable projection and MUST identify its source capsule, source size, integrity state, and selection status."
    },
    {
      "id": "AWP-CAPSULE-013",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 92,
      "statement": "A bounded entry view MUST report `complete` only when the active Resume, its explicitly selected records, referenced Handoff and checkpoint, and required artifact descriptors were resolved and verified according to the declared presentation profile. This status asserts structural completeness of the author-declared entry set, not that no other historical context can be relevant. If a byte or token budget cannot carry the declared entry set, the host MUST report `budget_exceeded` or `incomplete`, identify omitted or unresolved material, and stop or obtain more context according to receiver policy. It MUST NOT silently truncate required state or treat a generated briefing alone as complete semantic re-entry."
    },
    {
      "id": "AWP-CAPSULE-014",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 94,
      "statement": "This two-stage presentation limits model context consumption, not validation. A Capsule reader claiming briefing-first presentation MUST still parse and validate the full representation, required modules, internal references, and integrity metadata before it reports the selected view as complete."
    },
    {
      "id": "AWP-CAPSULE-015",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 98,
      "statement": "When a project maintains one current writable Capsule, its host SHOULD expose a canonical maintenance binding. The binding owns parsing, record projection, briefing rendering, artifact-integrity calculation, and serialization. An agent or model MAY submit semantic facts, a synchronization delta, or a checkpoint request, but MUST NOT be required to edit embedded JSON, calculate digests, or rewrite the canonical Capsule directly."
    },
    {
      "id": "AWP-CAPSULE-016",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 100,
      "statement": "A checkpoint request for a canonical Capsule MUST carry an idempotency key, the expected whole-Capsule digest, the expected generated-region digest, the expected semantic frontier, the proposed semantic frontier, the checkpoint or no-change disposition, and the semantic handoff fields required by Handoff. The host MUST compare all expected values immediately before replacement. A mismatch MUST produce `stale_base` or an equivalent recoverable result; it MUST NOT use last-write-wins."
    },
    {
      "id": "AWP-CAPSULE-017",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 102,
      "statement": "The host MUST serialize canonical replacement per workstate, write through a temporary file with flush and sync before atomic replacement, and return a receipt containing the prior and resulting whole-Capsule digests, generated-region digests, semantic frontier, checkpoint, and publication status. A no-change exit MUST return a verified receipt without rewriting identical bytes. A crash between replacement and durable publication MUST leave recoverable journal state and MUST NOT be reported as a confirmed checkpoint until recovery resolves it."
    },
    {
      "id": "AWP-CAPSULE-018",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 104,
      "statement": "Artifact locations are not artifact identity. When bytes at a mutable location change, the writer MUST preserve the prior digest as historical evidence and create or reference a new artifact revision. It MUST NOT silently rewrite an old artifact claim to match new bytes. Routine entry MAY verify only active required artifacts; a full historical audit MUST be an explicit operation."
    },
    {
      "id": "AWP-CAPSULE-019",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 139,
      "statement": "`WORK.md` and `manifest.json` are REQUIRED. `events.jsonl` is REQUIRED unless the manifest declares a snapshot-only representation. `snapshot.json`, `artifacts/`, `modules/`, and `views/` are optional."
    },
    {
      "id": "AWP-CAPSULE-020",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 141,
      "statement": "Each `events.jsonl` line contains one complete JSON event. Module-specific events remain in this unified ledger. Module-owned auxiliary data MAY occupy separate files under `modules/`, but their manifest locations are authoritative; directory names are conventional only."
    },
    {
      "id": "AWP-CAPSULE-021",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 147,
      "statement": "A `.awp.md` file begins with briefing metadata and human Markdown, followed by machine sections. Front matter MUST declare `capsule_boundary`, a lowercase hexadecimal token containing at least 128 bits of unpredictable entropy."
    },
    {
      "id": "AWP-CAPSULE-022",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 161,
      "statement": "It may contain attributes of the form ` name=\"value\"` before ` -->`. Attribute names match `[a-z][a-z0-9_-]*`; values MUST NOT contain a quote, CR, LF, or `-->`."
    },
    {
      "id": "AWP-CAPSULE-023",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 180,
      "statement": "The boundary token MUST NOT occur in decoded section content. A writer detecting a collision MUST generate a new boundary or encode the content using a binary-safe encoding such as base64. Binary artifacts MUST use base64 or a registered binary-safe encoding."
    },
    {
      "id": "AWP-CAPSULE-024",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 182,
      "statement": "A reader MUST validate marker pairing, reject duplicate authoritative sections, verify each module section against a matching manifest declaration, reject malformed boundaries, and preserve unknown sections during lossless rewriting. It MUST NOT infer machine state from arbitrary Markdown headings or code examples outside marked sections."
    },
    {
      "id": "AWP-CAPSULE-025",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 186,
      "statement": "Editable-directory packages, ZIP packages, JSON wire payloads, and standalone capsule exchange are archived design directions. They have no active AWP 0.8 conformance claim and MUST NOT be represented as a substitute for a project-scoped workstate or a COOP binding. A future version MAY define a transport or inter-project profile with its own discovery, authority, integrity, and lifecycle rules."
    },
    {
      "id": "AWP-CAPSULE-026",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 204,
      "statement": "Standard representation kinds are `capsule-section`, `project-path`, `remote`, and `events-only`. A remote module location MUST disclose retrieval requirements. Secrets MUST NOT appear in locations."
    },
    {
      "id": "AWP-CAPSULE-027",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 210,
      "statement": "A Capsule reader MUST validate the project representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing. A reader claiming repository-discovery support MUST implement Section 2 and expose discovery failures."
    },
    {
      "id": "AWP-CAPSULE-028",
      "source": "spec/drafts/0.8.0/capsule.md",
      "line": 212,
      "statement": "A Capsule writer MUST create an unambiguous project representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content. A project Markdown writer MUST include its discovery mode and governing specification in the capsule metadata."
    },
    {
      "id": "AWP-HANDOFF-001",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 15,
      "statement": "A workstate containing a handoff record MUST declare this module. It MUST mark the module required when the requested continuation depends on the record's completeness, dependency, resumption, or authority-ceiling semantics."
    },
    {
      "id": "AWP-HANDOFF-002",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 25,
      "statement": "`portable` is RECOMMENDED for cross-system continuation. A portable handoff MUST identify each required dependency as `available`, `retrievable`, `unavailable`, or `withheld`. A full handoff MUST enumerate omissions and MUST NOT imply that an entire repository, transcript, or runtime is present when it is not."
    },
    {
      "id": "AWP-HANDOFF-003",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 37,
      "statement": "Levels are cumulative. `operational` MUST satisfy every semantic requirement. `exact` MUST satisfy semantic and operational requirements unless explicitly labeled `private_nonportable`, in which case it is not a conforming portable handoff."
    },
    {
      "id": "AWP-HANDOFF-004",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 90,
      "statement": "Required fields are `id`, `type`, `module`, `checkpoint`, `completeness`, `intended_audience`, `requested_action`, `authority_ceiling`, and `resumption_level`. `module` MUST be `urn:awp:handoff`."
    },
    {
      "id": "AWP-HANDOFF-005",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 92,
      "statement": "`authority_ceiling` is an upper bound asserted by the sender. It does not grant those authorities; the receiver may operate under a stricter ceiling. A missing, unknown, or ambiguous ceiling MUST be treated as no authority for external side effects."
    },
    {
      "id": "AWP-HANDOFF-006",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 128,
      "statement": "Required fields are `id`, `type`, `module`, `checkpoint`, `mode`, `read_first`, `required_artifacts`, `recommended_next_action`, `freshness_policy`, `on_stale`, and `authority_ceiling`. `type` MUST be `resume`, `module` MUST be `urn:awp:handoff`, and the only standard mode in this version is `project_reentry`. Optional `handoff` identifies the handoff record this resume record refines."
    },
    {
      "id": "AWP-HANDOFF-007",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 130,
      "statement": "When both a Resume and referenced Handoff record are present, the Resume record is the project-entry instruction for the named checkpoint. Its `authority_ceiling` MUST be equal to or narrower than the Handoff ceiling, and its action MUST be a compatible refinement of the Handoff requested action. A receiver that cannot establish those conditions MUST qualify or reject the resume; it MUST NOT choose one record silently."
    },
    {
      "id": "AWP-HANDOFF-008",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 138,
      "statement": "`on_stale` is `refresh_workstate`, `report_and_stop`, or `read_only_orientation`. A receiver MUST NOT interpret any value as permission to perform an external side effect from stale or unverifiable state."
    },
    {
      "id": "AWP-HANDOFF-009",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 140,
      "statement": "`state_bindings`, when present, bind a resume checkpoint to the state spaces and immutable revisions against which it was prepared. Each entry requires `state_space` and `revision` and MAY identify an adapter `profile` and narrower `scope`. A `project_reentry` record that depends on external or source-controlled work products MUST include each state binding required to assess safe continuation. A Git repository and source revision are one possible binding; they are not required for non-code work products."
    },
    {
      "id": "AWP-HANDOFF-010",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 142,
      "statement": "A receiver that can identify the local state-space revision MUST compare it with `revision`. A mismatch makes the binding stale. When it can obtain a difference, claims, evidence, change sets, and verification results scoped to changed objects MUST be treated as stale until reverified or explicitly re-scoped. When the receiver cannot identify or compare the state-space revision, the binding is unverifiable rather than current. A matching revision does not establish that remote services, credentials, or other dependencies remain current."
    },
    {
      "id": "AWP-HANDOFF-011",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 144,
      "statement": "`read_first` is an ordered presentation hint, not causal ordering or authority. A receiver MAY load additional records required to interpret dependencies, evidence, conflicts, or safety constraints. It MUST NOT omit relevant required state merely to meet a context budget. Optional context-selection metadata MAY state a token or byte budget, priority groups, and deferred artifacts, but it cannot weaken completeness, freshness, or authority requirements."
    },
    {
      "id": "AWP-HANDOFF-012",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 146,
      "statement": "A receiver MAY implement the Capsule briefing-first presentation profile `selective-reentry-v1`. That profile reads and validates the complete source representation in the host, but returns a bounded participant-facing projection containing:"
    },
    {
      "id": "AWP-HANDOFF-013",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 154,
      "statement": "The projection MUST include a selection status of `complete`, `incomplete`, or `budget_exceeded`, plus every missing record identifier and every required artifact that could not be verified. In this profile, `complete` means that the Capsule integrity is current, the complete author-declared Resume selection is present, and each required local artifact with supported integrity metadata is current. It does not claim that the selection contains every fact a later task may expose as relevant. `brief_only` is an explicitly incomplete orientation mode. A receiver MUST NOT call the projection complete when it omitted the entry records to satisfy a budget, and a participant MUST NOT begin guarded work from an incomplete projection."
    },
    {
      "id": "AWP-HANDOFF-014",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 156,
      "statement": "A host MAY expose a canonical Capsule checkpoint operation. A model-facing checkpoint request supplies semantic content such as the proposed frontier, checkpoint, concise briefing fields, unresolved work, evidence references, and recommended next action. The host supplies whole-Capsule and generated-region digests, performs serialization and artifact verification, and returns a receipt or a recoverable stale or pending result. `mode: no_change` confirms that the current Capsule was checked without rewriting it."
    },
    {
      "id": "AWP-HANDOFF-015",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 158,
      "statement": "A Resume Profile receiver MUST:"
    },
    {
      "id": "AWP-HANDOFF-016",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 173,
      "statement": "A Handoff writer MUST:"
    },
    {
      "id": "AWP-HANDOFF-017",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 187,
      "statement": "A Handoff reader MUST:"
    },
    {
      "id": "AWP-HANDOFF-018",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 207,
      "statement": "Reports SHOULD record capsule size where applicable, token usage, author and receiver versions, unsupported modules, omissions, false assumptions, safety failures, and resulting artifact quality. A single successful task is not evidence of general interoperability."
    },
    {
      "id": "AWP-HANDOFF-019",
      "source": "spec/drafts/0.8.0/handoff.md",
      "line": 211,
      "statement": "A Handoff reader implements the receiver procedure and exposes limitations. A Handoff writer implements the producer procedure and makes accurate claims. A Resume Profile reader additionally implements Section 5 and declares the `resume-profile` capability. A system MAY support handoff and resume records without supporting the Capsule module; repository discovery requires Capsule support."
    },
    {
      "id": "AWP-ARTIFACT-001",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 15,
      "statement": "A workstate using Artifact fields MUST declare this module. It MUST mark the module required when continuation depends on retrieving, verifying, executing, or distinguishing the availability of an artifact."
    },
    {
      "id": "AWP-ARTIFACT-002",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 49,
      "statement": "Artifact-module fields live under `modules[\"urn:awp:artifact\"]`. Required module fields are `status` and `locations`. An available packaged artifact MUST include `media_type`, `size`, and `integrity`. Statuses are `available`, `retrievable`, `unavailable`, `withheld`, `redacted`, and `superseded`."
    },
    {
      "id": "AWP-ARTIFACT-003",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 51,
      "statement": "Logical identity and content identity are distinct. A modified artifact receives a new record ID and content digest but MAY retain the same `logical_name`. A change record links before and after versions."
    },
    {
      "id": "AWP-ARTIFACT-004",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 65,
      "statement": "Private kinds MUST use collision-resistant namespaced values."
    },
    {
      "id": "AWP-ARTIFACT-005",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 67,
      "statement": "Package paths MUST be relative, normalized, and traversal-safe. Secrets, bearer tokens, cookies, and authorization headers MUST NOT appear in locations. Retrieval requirements may refer to separately authorized credentials without containing them."
    },
    {
      "id": "AWP-ARTIFACT-006",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 69,
      "statement": "An absolute local path is a hint tied to an identified environment. A receiver MUST NOT assume that it names the same resource locally."
    },
    {
      "id": "AWP-ARTIFACT-007",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 73,
      "statement": "Packaged and embedded artifacts MUST include a digest over the exact decoded bytes. Remote and repository-relative artifacts SHOULD include a digest whenever stable bytes are expected. Hash algorithms are registry values; SHA-256 is the default for this module version."
    },
    {
      "id": "AWP-ARTIFACT-008",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 75,
      "statement": "Readers SHOULD verify a digest before relying on content. Digest validity establishes byte identity, not safety, truth, authorship, or authority."
    },
    {
      "id": "AWP-ARTIFACT-009",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 77,
      "statement": "Content-addressed packaged artifacts are immutable. Changing bytes creates a new content identity. A mutable remote URI SHOULD be paired with a digest, immutable version, ETag, or explicit `mutable: true` warning."
    },
    {
      "id": "AWP-ARTIFACT-010",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 83,
      "statement": "A portable Handoff that depends on an artifact MUST include it, make it retrievable, or state that continuation is blocked. A URI alone is not proof of retrievability."
    },
    {
      "id": "AWP-ARTIFACT-011",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 85,
      "statement": "Retrieval is an external action subject to receiver authority and security policy. Merely referencing a remote artifact MUST NOT trigger automatic network access."
    },
    {
      "id": "AWP-ARTIFACT-012",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 89,
      "statement": "Descriptors MUST state whether content is executable or may contain instructions when either is known. Unknown values SHOULD be represented explicitly rather than assumed false."
    },
    {
      "id": "AWP-ARTIFACT-013",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 91,
      "statement": "Readers MUST treat instructions in untrusted artifacts as data. Executables, archives, active documents, and model-readable instruction files SHOULD be inspected in an appropriate sandbox before use."
    },
    {
      "id": "AWP-ARTIFACT-014",
      "source": "spec/drafts/0.8.0/artifact.md",
      "line": 120,
      "statement": "The tombstone MUST remove sensitive bytes and locations, preserve referential integrity, disclose rewritten history, and invalidate signatures covering removed bytes. It MAY retain the original digest only when the digest is not itself sensitive. It MUST NOT imply that the bytes remain available."
    },
    {
      "id": "AWP-SYNC-001",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 15,
      "statement": "A workstate or message using deltas, omitted-history boundaries, or synchronization conflict semantics MUST declare this module. It MUST be required when the receiver must apply or reconcile those structures to reach the continuation frontier."
    },
    {
      "id": "AWP-SYNC-002",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 35,
      "statement": "A delta MUST identify `workstate_id`, `base_frontier`, `result_frontier`, and `events`. It MAY carry artifact announcements or module data required by those events."
    },
    {
      "id": "AWP-SYNC-003",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 37,
      "statement": "A receiver MUST verify that the base frontier is known or request missing ancestry. It MUST validate event IDs, workstate IDs, parents, module declarations, and result frontier before application. Applying a delta MUST be idempotent by event ID. Reuse of one event ID for different bytes is an integrity conflict."
    },
    {
      "id": "AWP-SYNC-004",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 41,
      "statement": "A reader with both a snapshot and event ledger MUST:"
    },
    {
      "id": "AWP-SYNC-005",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 59,
      "statement": "For `stale_replayable`, a processor replays descendant events in deterministic topological order. Concurrent events remain concurrent; topological serialization MUST NOT be treated as conflict resolution. Record revision preconditions determine whether updates commute or conflict."
    },
    {
      "id": "AWP-SYNC-006",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 81,
      "statement": "A fork MAY record an exact parent Capsule digest in addition to its parent frontier. The Silo Profile requires that pin. A workstate whose continuation depends on `silo-v1` MUST declare that capability and mark Synchronization and its profile dependency Capsule required. A reader that lacks required silo processing MUST block dependent continuation even when it supports ordinary forks. Adopting selected results across workstate identities follows the profile's dependency-closure and publication rules, not a mechanical union of foreign events into the local graph."
    },
    {
      "id": "AWP-SYNC-007",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 85,
      "statement": "Mechanical merge unions events by ID after integrity validation. It preserves all concurrent tips. It MUST NOT silently apply last-write-wins to:"
    },
    {
      "id": "AWP-SYNC-008",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 100,
      "statement": "Replay MUST respect graph ancestry. When concurrent events require a deterministic processing order, processors sort by event ID only as a reproducibility device. This ordering has no semantic priority."
    },
    {
      "id": "AWP-SYNC-009",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 104,
      "statement": "Unknown optional-module events remain graph nodes and participate in frontier computation. A processor MUST NOT advance a derived snapshot through an unknown event when doing so could alter a required Core or module result; it reports the projection as unverifiable instead."
    },
    {
      "id": "AWP-SYNC-010",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 108,
      "statement": "AWP 0.8.0 does not define destructive log compaction. A writer MAY create a summary or snapshot-only export, but it MUST disclose omitted history and MUST NOT claim `full` completeness."
    },
    {
      "id": "AWP-SYNC-011",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 118,
      "statement": "High-frequency coordination presence and heartbeat state is a live materialized view, not a substitute for the durable event graph. A synchronization transport SHOULD coalesce heartbeat renewal and MUST NOT require every heartbeat to advance the project workstate frontier. Lifecycle facts that affect semantic continuation, including entry, release, expiry, conflict, and incomplete handoff, MAY be published as Coordination events."
    },
    {
      "id": "AWP-SYNC-012",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 120,
      "statement": "Concurrent agents publish events or deltas rather than independently replacing one canonical Capsule. A Capsule projector MUST compare the Capsule's current frontier and generated digest with the base it read before replacement. If either differs, it MUST reload and reconcile through this module, retry from the new base, or report divergence. It MUST NOT silently overwrite the newer projection."
    },
    {
      "id": "AWP-SYNC-013",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 122,
      "statement": "A deployment with one canonical Capsule MUST identify how projection ownership is serialized. An enforced deployment may use a fenced `integration_owner` lease. An advisory deployment may use a single local writer with atomic compare-and-swap. Projection ownership controls representation updates only; it does not grant authority over project changes."
    },
    {
      "id": "AWP-SYNC-014",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 124,
      "statement": "The projection base MUST include the exact whole-Capsule artifact digest in addition to the semantic frontier and generated-region digest. The generated-region digest alone does not protect changes to the manifest, snapshot, notes, or other authoritative sections. A projection writer MUST reject a stale whole-Capsule digest even when the generated briefing is unchanged."
    },
    {
      "id": "AWP-SYNC-015",
      "source": "spec/drafts/0.8.0/synchronization.md",
      "line": 126,
      "statement": "A projection writer MUST make the replacement recoverable across a process crash. Before replacement it MUST durably record the expected and proposed whole-Capsule digests and the request identity in a projection journal or equivalent binding-owned state. Recovery MUST classify the result as `pending`, `recovered`, or `diverged`; it MUST never resolve an unknown result by last-write-wins."
    },
    {
      "id": "AWP-SILO-001",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 21,
      "statement": "An implementation using this profile MUST declare Synchronization with capability `silo-v1` and compatible Core and Capsule declarations. Synchronization and Capsule MUST be required when continuation depends on silo isolation, ancestry, or adoption. A receiver that does not support `silo-v1` MUST NOT claim a complete interpretation or perform dependent continuation, even if it supports ordinary Synchronization forks. Unknown optional profile data follows the family's preservation rules."
    },
    {
      "id": "AWP-SILO-002",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 23,
      "statement": "A silo requires no named COOP contract, service, Git installation, Node.js runtime, or network transport. Creating, entering, sharing, updating, or adopting a silo MUST NOT implicitly enable consultation, delegation, agent communication, or additional spending. Those actions remain subject to the currently authorized policy and Cooperation Contracts \u00a75 where applicable."
    },
    {
      "id": "AWP-SILO-003",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 27,
      "statement": "Every silo MUST have its own `workstate_id`, one current `silo` record, and a separate writable Capsule representation. Copies or replicas of that silo retain its identity. Its record MUST identify the canonical workstate, exactly one immediate parent, an immutable origin pin, purpose, owner, and current base pin. A new silo's origin and base MUST be equal. A parent may be canonical or another silo in the same canonical project."
    },
    {
      "id": "AWP-SILO-004",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 29,
      "statement": "A **state pin** identifies `workstate_id`, `frontier`, exact governing `specification`, and `capsule_digest` over the complete source Capsule bytes; it MAY also identify a checkpoint and generated-region digest. A generated-region digest MUST NOT substitute for a complete Capsule digest. The source Capsule and the state represented by its frontier MUST be validated before derivation or adoption; a digest alone proves neither a valid projection nor acceptance by the project. A snapshot-only source MUST disclose its omitted-history boundary and source digest under Synchronization and MUST NOT claim full replay evidence."
    },
    {
      "id": "AWP-SILO-005",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 31,
      "statement": "The parent relation MUST be acyclic, with exactly one parent for each silo. The origin pin and parent identity MUST remain immutable. A receiver MUST validate ancestry to the designated canonical root before claiming a complete hierarchy; a missing ancestor is `unavailable`, not proof of an independent root. Multiple inheritance and automatic parent selection are outside `silo-v1`. Implementations MAY impose and disclose depth or retrieval limits; exceeding one blocks the affected operation with a diagnostic rather than silently truncating ancestry."
    },
    {
      "id": "AWP-SILO-006",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 33,
      "statement": "The child fork genesis MUST identify its parent pin as external provenance. Parent events retain their original workstate IDs and MUST NOT be relabeled as child events or inserted as unresolved local event parents. A child starts its own event graph and retains or references the pinned parent state under Synchronization's history-completeness rules. Cross-workstate references MUST qualify the source workstate, record ID, and revision; matching local ID strings do not establish identity across forks."
    },
    {
      "id": "AWP-SILO-007",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 35,
      "statement": "Entry MUST explicitly select and display the current workstate identity, its silo purpose, canonical identity, base, lifecycle, and effective authority limits before dependent mutation. A locator or optional silo catalog is discovery data, not authority. Creating a silo MUST NOT require updating the canonical Capsule or switching the project's default discovery pointer. Registering it in a canonical catalog is a separate authorized canonical change. A host MUST NOT silently substitute a parent or canonical Capsule when the selected silo is unavailable."
    },
    {
      "id": "AWP-SILO-008",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 39,
      "statement": "The effective silo state consists of the validated pinned base plus explicit child additions, replacements, and tombstones. The silo record's `inherited_records` MUST enumerate the exact qualified revision pins selected from the base. It MUST include every record and module dependency necessary for the declared continuation; omission of unrelated material is permitted with an accurate completeness declaration. Retained pins MAY reference immutable packaged or retrievable source material rather than duplicate every byte."
    },
    {
      "id": "AWP-SILO-009",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 41,
      "statement": "An `overrides` entry MUST identify the inherited pin, operation (`replace` or `tombstone`), reason, and, for replacement, a qualified child record pin. At most one uncontested effective override may apply to an inherited pin. Additions are ordinary child-owned records. Replacements create child-owned records and retain origin provenance; they MUST NOT revise the parent record or erase a competing child revision. Tombstones affect only the child's effective view and preserve history. Omission from the view MUST NOT be interpreted as deletion in any parent or adoption target."
    },
    {
      "id": "AWP-SILO-010",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 43,
      "statement": "Parent changes MUST NOT automatically change a child's effective state. A base update is an explicit `silo.base_updated` event that pins the expected silo revision, prior base, new base from the same parent identity, and an approved reconciliation of inherited records and local overrides. The event MUST preserve the origin pin and old history, record the responsible actor, rationale, decision reference, dependency changes, and per-override disposition. A changed or missing inherited dependency MUST block the affected continuation until its disposition is recorded. A successor from a different parent requires a new fork identity with provenance to the prior silo."
    },
    {
      "id": "AWP-SILO-011",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 45,
      "statement": "A reader MUST distinguish historical project decisions inherited at the pinned base from current operational authority. Current host guardrails, authority expiry, revocation, and access restrictions apply immediately to operations; an old base MUST NOT preserve revoked permission or permit evasion of a mandatory guardrail. A silo MAY explore an alternative project constraint only within current operational authority and with the alternative explicitly scoped to that silo."
    },
    {
      "id": "AWP-SILO-012",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 49,
      "statement": "Project governance distinguishes three responsibilities, which MAY belong to the same principal:"
    },
    {
      "id": "AWP-SILO-013",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 57,
      "statement": "The destination MUST identify its decision owner and accepted policy for adoption. A project MAY appoint component stewards or use a threshold approval policy. Every relied-upon delegation MUST identify grantor, grantee, permitted actions, resources or scope, conditions, expiry or explicit absence of expiry, delegation permission, and revocation basis. Receivers MUST evaluate the delegation chain under current local policy before relying on it. Ownership transfer or policy revision MUST be an explicit accepted decision preserving prior provenance."
    },
    {
      "id": "AWP-SILO-014",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 59,
      "statement": "A child owner MUST NOT derive authority over a parent or canonical workstate from ancestry, ownership, a role label, or a local approval. A proposal to adopt authority or governance changes MUST undergo the destination's existing policy; it MUST NOT authorize its own acceptance. A role labeled `super-admin` has no special protocol privilege beyond its explicitly accepted grants. Authority conflict or an unavailable authorized decision owner blocks the affected adoption, not unrelated exploration."
    },
    {
      "id": "AWP-SILO-015",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 61,
      "statement": "Serialization and approval are distinct. A publisher MUST use Capsule \u00a73.2 and Synchronization \u00a79.1 for expected-state checks and recovery. Publication ownership MUST NOT grant authority over the content. COOP-1 may record responsibilities and human decisions and provide cooperating-writer exclusion; it does not authenticate all actors or prevent a bypassing writer. Claims of enforced cross-principal role separation or protected canonical mutation require COOP-3 and the named enforcing path. Below that boundary, the deployment MUST disclose unenforced roles; independently checked authority evidence remains useful without implying protected enforcement."
    },
    {
      "id": "AWP-SILO-016",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 67,
      "statement": "A silo performing guarded work on a work product MUST either use a verified isolated location or use one common atomic collision-control binding that covers every cooperating writer to the shared resource. Worktree names and path spelling alone are not isolation evidence; resource aliases, linked files, generated outputs, and shared services MUST be considered under the declared scope model. An isolated worktree does not isolate a shared database or deployment target."
    },
    {
      "id": "AWP-SILO-017",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 69,
      "statement": "For `shared` mode, the deployment MUST record the complete common binding identity, resource/scope mapping, atomicity mechanism, and observation of coverage. All participating silos and canonical actors MUST publish and check physical intents in that same binding before a guarded write. Intents MUST retain their originating semantic workstate as qualified provenance while using the common binding's workstate and event graph for admission. Silo-local semantic stores remain separate. Participants MUST NOT union unrelated store histories to manufacture a combined permission, and a local silo lease MUST NOT be treated as a reservation in the common binding."
    },
    {
      "id": "AWP-SILO-018",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 71,
      "statement": "If no such common binding is available, shared guarded mutation MUST be blocked or explicitly conducted outside an active COOP guarantee under host policy. Cross-binding informational notices, asynchronous mirroring, and separate successful announce operations are insufficient for atomic exclusion. A binding lacking the resource mapping or coverage evidence MUST NOT claim this shared-location capability."
    },
    {
      "id": "AWP-SILO-019",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 86,
      "statement": "`closed` is terminal; further exploration creates a successor silo. Closure reasons MAY include completed, abandoned, rejected, or superseded. A paused or closed silo MUST NOT start new implementation work; lifecycle administration, receipt recovery, read-only review, and adoption of previously pinned results MAY continue when separately authorized. Pause or closure MUST NOT silently complete intents, release leases, discard uncommitted artifacts, delete files, or claim a successful handoff; each binding's exit rules still apply."
    },
    {
      "id": "AWP-SILO-020",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 88,
      "statement": "Closing a parent MUST NOT close its children or invalidate their origin pins. Descendants retain their historical base. An unavailable parent representation or decision owner MUST be disclosed separately from lifecycle. A new destination or owner can be approved without rewriting ancestry. Silo deletion, redaction, retention, and artifact removal follow the existing family rules and are not implied by closure."
    },
    {
      "id": "AWP-SILO-021",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 90,
      "statement": "Partial or repeated adoption MUST NOT automatically pause or close a silo. A closed silo MAY remain a valid source of historical results if their pins, dependencies, and current destination approval can be verified."
    },
    {
      "id": "AWP-SILO-022",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 94,
      "statement": "**Adoption** is the explicit acceptance of selected results from a silo into canonical state or an ancestor silo. It may publish a proposal as a proposal; it does not inherently accept the proposal's substance. `silo-v1` permits adoption into an ancestor in the same canonical project; arbitrary cross-project adoption and sibling adoption are outside this profile. A source and destination MUST differ."
    },
    {
      "id": "AWP-SILO-023",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 96,
      "statement": "An adoption record MUST identify source and destination state pins, exact selected record revisions, proposed destination records, qualified source-to-destination mapping, dependency closure evidence, base-divergence observations, intended scopes, destination decision owner and policy reference, publisher, and an idempotency key. It MUST identify bypassed ancestors when the target is not the immediate parent. Bypassing an ancestor requires destination authorization and all applicable approval obligations, but does not require an intermediate adoption, invalidate historical ancestor bases, or authorize writing to those ancestors. Notices MAY be published when authorized."
    },
    {
      "id": "AWP-SILO-024",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 100,
      "statement": "Before approval and again before publication, the processor MUST establish that the selected result is causally closed over all references required to interpret or use it at the pinned destination frontier. Each dependency MUST resolve to (a) an included input, (b) an exact existing destination record or artifact, or (c) an explicit qualified source reference retained with its required availability and interpretation rules. Historical source ancestry may remain externally pinned; closure does not require copying the whole source event graph."
    },
    {
      "id": "AWP-SILO-025",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 102,
      "statement": "Missing dependencies MUST cause the processor to extend the selection, explicitly re-derive the affected result and its references with evidence, or reject it. A closure or reference rewrite that changes the proposed result MUST invalidate prior approval and require approval of the revised proposal. Unknown required modules, contested references, unsupported dependency semantics, or insufficient evidence MUST block adoption; a processor MUST NOT claim closure by inspecting only recognized fields."
    },
    {
      "id": "AWP-SILO-026",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 104,
      "statement": "New destination records MUST have destination-owned identities and explicit origin pins. Revising an existing destination record MUST use its expected revision and retain the source mapping. Bare ID equality MUST NOT select a destination record. Source events and revisions MUST remain immutable; adoption emits new destination events whose local parents belong to the destination graph, with source pins as external provenance. A dependency cycle MUST either be preserved as a valid combined unit under the owning modules or block adoption; it MUST NOT be broken by silently dropping an edge."
    },
    {
      "id": "AWP-SILO-027",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 108,
      "statement": "The processor MUST compare the selected results' inherited dependencies and all applicable destination constraints and policies with current destination state. Its `divergence` observations MUST identify each relied-upon pin, the current matching destination pin or its absence, comparison basis, result (`unchanged`, `changed`, `missing`, `contested`, or `unknown`), and disposition. Unrelated parent changes do not by themselves invalidate the selected result. Changed material assumptions require explicit reconciliation and destination-owner disposition; missing or unverifiable required dependencies remain blocking."
    },
    {
      "id": "AWP-SILO-028",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 110,
      "statement": "Adoption MUST preserve the distinction between proposals, accepted decisions, reports, and verified claims. Acceptance in a source silo MUST NOT imply destination acceptance. Verification evidence MUST retain its original subject, scope, artifact revisions, and environment; if those no longer support the destination claim, the claim MUST be revalidated or explicitly represented as unverified or stale. A clean Git merge or passing source test suite MUST NOT be sufficient evidence of destination semantic compatibility."
    },
    {
      "id": "AWP-SILO-029",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 114,
      "statement": "Approval MUST bind the exact adoption proposal revision, source pin, destination pin, resulting record mapping, declared scopes, and conditions. The publisher MUST re-evaluate current authority, conditions, applicable COOP decisions, and destination freshness immediately before publication. Any changed expected destination state MUST return `stale_base`; the writer MUST reconcile and obtain approval for a successor proposal rather than apply last-write-wins."
    },
    {
      "id": "AWP-SILO-030",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 116,
      "statement": "The adopted semantic records and the adoption fact MUST become visible together in one recoverable destination publication using Capsule \u00a73.2. This atomic boundary concerns the destination workstate only. File merges, deployments, and other external changes MUST have separately authorized operations and receipts; a binding MUST NOT claim a transaction spanning them without a mechanism that actually provides it. An adoption depending on external results MUST verify and pin those results before claiming completion."
    },
    {
      "id": "AWP-SILO-031",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 118,
      "statement": "The publication journal and returned receipt MUST bind the idempotency key, approved proposal revision, prior and resulting whole-Capsule digests, generated-region digests, destination frontier, checkpoint, and publication status. The resulting complete-Capsule digest MUST be stored in the external receipt or journal, not required inside the bytes it hashes. The Capsule's adoption fact identifies the operation and approved proposal; a processor confirms publication using the matching receipt or recovery evidence."
    },
    {
      "id": "AWP-SILO-032",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 120,
      "statement": "A retry of the same idempotency key and exact request MUST return the original result or recover its pending state. Reuse with a different request MUST be rejected. If a crash leaves publication uncertain, the binding MUST report `pending` and compare the journal's expected and proposed state before classifying it as adopted, not published, or diverged. It MUST NOT repeat uncertain external side effects or issue a success receipt based only on a planned filename. Source or ancestor receipt mirroring is optional and MUST NOT make a confirmed destination adoption appear uncommitted when only that mirroring failed."
    },
    {
      "id": "AWP-SILO-033",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 135,
      "statement": "`adopted`, `stale`, `rejected`, `cancelled`, and `failed` are terminal. A changed or retried failed proposal uses a successor record and new key; recovery of the same pending operation retains its key. An uncertain or diverged pending publication MUST remain unresolved until recovery establishes the outcome. Adoption lifecycle observations may live in binding-owned durable state; the confirmed adoption fact belongs in the destination graph. A source observation of that fact retains the destination pin and MUST NOT masquerade as a destination event."
    },
    {
      "id": "AWP-SILO-034",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 139,
      "statement": "The structural schema defines `silo` and `silo_adoption` records, both owned by `urn:awp:sync` with `profile: silo-v1`. Records MUST include `id`, `type`, `module`, `profile`, positive integer `revision`, `status`, `created_by`, and `created_at`. The silo record lives in `snapshot.modules[\"urn:awp:sync\"].silos`; adoption records, when projected in a workstate, live in that module state's `silo_adoptions`. Project governance MAY be recorded as accepted Core decisions and authority declarations referenced by `adoption_policy`; no parallel authority-grant record is introduced."
    },
    {
      "id": "AWP-SILO-035",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 141,
      "statement": "Profile events MUST use the Core envelope and owning module `urn:awp:sync`. In addition to the lifecycle events above, the profile defines `silo.updated` for purpose, ownership, policy, and override changes and `silo.base_updated` for explicit base reconciliation. An update MUST pin the prior revision, assign the next integer revision, and carry a complete replacement plus required decision or reconciliation evidence. It MUST NOT change immutable identity or origin fields or use `silo.updated` to bypass a lifecycle or base-update condition. Creation uses revision 1. Concurrent non-commuting updates remain contested and MUST block dependent adoption until a recorded Synchronization resolution identifies both outcomes and the selected successor. Transport order and timestamps do not resolve that conflict."
    },
    {
      "id": "AWP-SILO-036",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 153,
      "statement": "Profile processors MUST emit stable diagnostics with code, severity, operation or record subjects, explanation, and recovery. The following codes have severity `error` and block the affected operation:"
    },
    {
      "id": "AWP-SILO-037",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 170,
      "statement": "A profile claim MUST state supported roles (`silo-reader`, `silo-writer`, `silo-adopter`), representation and dependency coverage, any active COOP contract, authority enforcement, and the tested operating envelope. Writer claims require reader behavior; adopter claims additionally require closure, destination approval, atomic publication, and recovery. A structural schema validator alone MUST NOT claim these roles."
    },
    {
      "id": "AWP-SILO-038",
      "source": "spec/drafts/0.8.0/silos.md",
      "line": 172,
      "statement": "Before an operational claim, fixtures MUST demonstrate: reproducible pinned derivation; parent changes leaving children unchanged; explicit base reconciliation; local override and tombstone isolation; duplicate IDs across forks; missing and cyclic ancestry; partial adoption with missing dependencies; external historical dependency retention; changed constraints and stale evidence; proposal approval invalidation; repeated partial adoption without closure; closed parent with active child; direct ancestor adoption; unauthorized self-approval; shared-location collisions including aliases; independent locations with shared external resources; concurrent destination publishers; retry and crash recovery; unknown required semantics; and preservation of disabled collaboration and declared budgets."
    },
    {
      "id": "AWP-COORD-001",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 74,
      "statement": "The following table attributes the Coordination mechanisms to their minimum contract. A mechanism may be implemented below that level, but it MUST NOT be used to support a higher contract claim until its listed composition is present."
    },
    {
      "id": "AWP-COORD-002",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 83,
      "statement": "A processor MUST NOT advertise a Cooperation Contract whose required composed behaviors it does not implement. A reader MAY support a weaker contract, but it MUST reject safe continuation when unsupported required semantics affect the requested action. A component such as a projector, registry, or enforcing gateway advertises capabilities and evidence rather than claiming a complete contract by itself."
    },
    {
      "id": "AWP-COORD-003",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 85,
      "statement": "Under `COOP-1`, a processor MAY surface a material conflict, ambiguity, or bounded question to the decision owner, but it MUST NOT autonomously start a work-affecting agent-to-agent consultation or negotiation loop. `COOP-2` and `COOP-3` may do so only through an enabled managed-collaboration policy that declares authorization, participants, purpose, scope, decision owner, and all budget limits. The availability of a messaging transport, A2A task, model, or tool does not enable collaboration by itself."
    },
    {
      "id": "AWP-COORD-004",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 87,
      "statement": "Cooperation Contract, operational mode, and ledger reach remain separate declarations because the latter two describe current availability rather than another conformance ladder. Operational mode is `ledger_bound`, `snapshot_only`, `degraded`, or `unavailable`. Ledger reach is `shared`, `worktree_local`, or `cross_host`. Ledger unavailability changes what work may safely proceed and MUST be disclosed; it does not silently convert one contract into another."
    },
    {
      "id": "AWP-COORD-005",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 99,
      "statement": "An implementation MAY adopt `coordination-awareness` before implementing the complete integration-assurance workflow. Capability declarations state what a component processes; the selected Cooperation Contract states the end-to-end guarantees participants may rely upon."
    },
    {
      "id": "AWP-COORD-006",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 103,
      "statement": "An intent records work a participant is performing, so a binding MUST NOT let an abandoned one hold scope indefinitely. When a participant is not present and the intent's base revision has drifted materially behind the current revision, the binding MUST report that intent as stale and MUST NOT treat it as a blocking party; the overlap remains visible and the intent remains a durable record, but a present participant is not blocked by an absent one. A binding that publishes coordination records in more than one store MUST let a participant discover the others from any one of them, naming each sibling binding, its role, and how to query it."
    },
    {
      "id": "AWP-COORD-007",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 105,
      "statement": "An AWP-aware writer that discovers a writable shared event ledger and supports the `coordination-awareness` bundle MUST enable ledger-backed advisory coordination by default unless project or receiver policy explicitly disables it. Before materially changing shared state, the writer MUST refresh the available ledger frontier, publish its intent and revision-pinned declared scopes, evaluate known overlaps under the effective policy, and make resulting warnings or guarded outcomes visible. Before integration or handoff, it MUST refresh again and publish the terminal intent, change-set, checkpoint, or synchronization delta required to explain its result."
    },
    {
      "id": "AWP-COORD-008",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 107,
      "statement": "This default is a protocol behavior, not a required runtime service or database technology. A local append-only file, immutable event package, transactional database, source-control binding, or remote event transport MAY supply the ledger when it preserves Core event identity, ancestry, atomic publication, and conflict-preserving replay. No AWP module or Cooperation Contract requires SQLite, a continuously running service, or a particular storage engine merely to manage a ledger. SQLite and the local adapter are optional reference-binding implementation aids; they MUST NOT be treated as protocol prerequisites or as evidence that another binding is unavailable. A binding that uses SQLite MUST disclose its path, locking and atomic-commit assumptions, reach, and failure state, and MUST enter the explicit unavailable or snapshot-only mode if those assumptions cannot be verified. Presence monitoring MAY reduce discovery latency but is not a prerequisite. Authenticated protected leases, epochs, and fencing are COOP-3 capabilities and remain separately configured from COOP-1 participant liveness leases."
    },
    {
      "id": "AWP-COORD-009",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 109,
      "statement": "Ledger implementations MAY be selected or replaced according to project policy, provided the active binding exposes the transport-neutral descriptor in \u00a73.2 and preserves the required event semantics. A conforming deployment SHOULD provide at least one authorized fallback binding or a recoverable snapshot-only path when its preferred ledger is unavailable. Fallback selection MUST preserve the binding identity and declared reach when it is the same logical ledger; otherwise it MUST publish a new binding identity and make the change visible before guarded work continues. A filesystem mailbox, doorbell, or model-generated record alone is not a ledger unless the binding confirms durable publication, readable frontier state, and the required replay and conflict guarantees."
    },
    {
      "id": "AWP-COORD-010",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 111,
      "statement": "If no safe writable ledger is discoverable, the writer SHOULD attempt to establish a project-scoped ledger through an authorized writable binding, provided it can publish the binding location, workstate identity, retention, and access expectations to the intended participants. If it cannot establish or discover such a binding, it MUST disclose operational mode `snapshot_only` or `unavailable` with diagnostic `AWP-COORD-LEDGER-UNAVAILABLE` before material mutation. A private temporary file, process memory, unshared worktree, or unconfirmed model output is not a shared ledger. A worktree-local ledger MAY be used when its limited reach is disclosed. The writer MUST NOT silently describe metadata preservation, a stale snapshot, or an unvalidated event sink as active coordination. Receiver policy determines whether work may continue. A tool MUST NOT advertise COOP-1 merely because it implements this default; its contract claim remains limited to the complete composed behavior it can demonstrate."
    },
    {
      "id": "AWP-COORD-011",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 113,
      "statement": "The default is an agent/model workflow contract. A model may produce valid intents, events, deltas, diagnostics, or a requested ledger operation as output, while a host binding performs persistence and authorization. A model is not required to open a database, run a service, or possess mutation authority. A host that exposes only a capsule or read-only event view MUST make that limitation visible; it MUST NOT imply that a model-generated event was durably published until the binding confirms persistence. Prompt instructions, tool schemas, MCP resources, A2A data parts, repository files, and other bindings MAY carry the same records when they preserve the declared ledger semantics."
    },
    {
      "id": "AWP-COORD-012",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 115,
      "statement": "For the default workflow, an AWP-aware agent or model SHOULD follow this sequence:"
    },
    {
      "id": "AWP-COORD-013",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 124,
      "statement": "The sequence is advisory with respect to external mutation under COOP-1: an unresolved `warn` outcome is visible but does not itself grant or deny authority. A receiver MAY require `block`, user arbitration, or an external policy gate. A model's claim that it followed the sequence is reported evidence until the binding makes the event bytes and resulting frontier inspectable."
    },
    {
      "id": "AWP-COORD-014",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 128,
      "statement": "An active Coordination binding MUST expose a transport-neutral descriptor containing at least the profile identifier, workstate identity, ledger location or retrieval reference, operational mode, ledger reach, durability and retention policy, event publication semantics, frontier-read semantics, and publication confirmation method. When managed collaboration is enabled, it MUST also identify participant discovery and interaction publication/retrieval mechanisms, both bound to the same project, workstate, and binding identity. The descriptor MAY be carried in a manifest, Capsule module state, repository discovery file, tool resource, MCP resource, A2A data part, or another binding-owned record. A location alone is not confirmation that a ledger is shared or writable. A binding that cannot provide a descriptor MUST report its mode and reach as `unverifiable` and MUST NOT claim cross-participant coordination."
    },
    {
      "id": "AWP-COORD-015",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 168,
      "statement": "`id`, `type`, `module`, `revision`, `status`, `created_by`, and `created_at` are required. `revision` begins at `1`. An update MUST identify `prior_revision` in its event and produce exactly `prior_revision + 1`."
    },
    {
      "id": "AWP-COORD-016",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 174,
      "statement": "Unknown fields MUST be preserved by lossless processors. A processor MUST distinguish a registered record type above its advertised capability or Cooperation Contract from a genuinely unregistered type. It preserves registered stronger-contract records without interpreting them and may still perform weaker-contract actions that do not depend on their meaning. A genuinely unregistered type owned by this required module makes only the affected action or projection `unverifiable` unless a declared compatibility rule permits preservation without interpretation. A weaker-contract reader MAY always perform safe display or export."
    },
    {
      "id": "AWP-COORD-017",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 183,
      "statement": "Safety-relevant references in contracts, preconditions, readiness decisions, verification, overlaps, and integration plans MUST be revision-pinned. A missing, superseded, or contested pinned revision remains historically addressable but MUST NOT be silently replaced by another revision. An unpinned reference that is absent, contested, or ambiguous is unresolved."
    },
    {
      "id": "AWP-COORD-018",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 189,
      "statement": "The passage of time never changes projected state. An identified actor or service MUST emit a valid timeout, expiration, or deadline-observation event under a declared clock authority. Until that event is present, a deadline may be overdue but the prior projected lifecycle state remains unchanged; processors SHOULD surface the overdue condition."
    },
    {
      "id": "AWP-COORD-019",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 266,
      "statement": "Within one workstate, an active alias MUST resolve to at most one semantic definition. Merging ambiguous aliases creates diagnostic `AWP-COORD-REGISTRY-AMBIGUOUS` and affected overlap analysis becomes `unknown` until resolved."
    },
    {
      "id": "AWP-COORD-020",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 270,
      "statement": "Selector comparison across pinned state-space revisions is a COOP-2 semantic-awareness operation. An analyzer MUST resolve both selectors against their pinned bases and attempt to relate moved, renamed, subdivided, aggregated, or replaced targets using a declared selector profile. Resolution results are `same`, `related`, `different`, `unresolvable`, or `ambiguous`, with evidence and confidence. `unresolvable` or `ambiguous` forces overlap classification `unknown`; it MUST NOT yield `none`."
    },
    {
      "id": "AWP-COORD-021",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 272,
      "statement": "Language-specific selector syntax and drift algorithms belong to registered adapter profiles. The initial reference implementation SHOULD provide Python AST and TypeScript compiler-symbol profiles, but their identifiers and outputs remain usable by agents implemented in any language."
    },
    {
      "id": "AWP-COORD-022",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 278,
      "statement": "A scope is a first-class record selecting a physical or semantic region. Intents, claims, change sets, and contracts reference it by ID and revision. An inline selector MAY be used as an unshared query value, but an inline selector is not a scope record and cannot be revised or used as a dependency target."
    },
    {
      "id": "AWP-COORD-023",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 301,
      "statement": "Physical selector kinds include `repository`, `directory`, `file`, `symbol`, `syntax_node`, `configuration_key`, `schema_object`, `generated_output`, `test`, `fixture`, `spatial_region`, `model_element`, `assembly`, `document_region`, `domain_object`, and `interface`. A selector profile defines how a domain resolves fields such as `state_space`, `object_id`, geometry, containment, adjacency, or document coordinates. Coordinates or line ranges are hints and MUST NOT be the only selector for a safety-relevant claim."
    },
    {
      "id": "AWP-COORD-024",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 307,
      "statement": "Authors SHOULD declare relied-upon reads only for assumptions whose incompatible change could invalidate the output, not every file or symbol inspected. Tools may propose candidates from dependency traces, but the published set SHOULD be summarized at stable interface, invariant, schema, or behavior boundaries. Fine-grained automatic reads MAY remain evidence behind that summary. This keeps the reverse index useful rather than turning ordinary repository browsing into conflicts."
    },
    {
      "id": "AWP-COORD-025",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 378,
      "statement": "An actor SHOULD publish an intent before materially changing shared state."
    },
    {
      "id": "AWP-COORD-026",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 423,
      "statement": "If observed work expands beyond the declared scope, the writer MUST either update the intent before publishing a ready change set or record an explicit deviation. Under a COOP-2 policy, unresolved material under-declaration prevents `ready`."
    },
    {
      "id": "AWP-COORD-027",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 457,
      "statement": "Observed-scope lifecycle statuses are `final` and `superseded`; outcome is `complete`, `partial`, or `error`. The analyzer, base, result, method, and evidence digest MUST be recorded. `declared_not_observed` is informational unless policy says otherwise. `undeclared` MUST be evaluated for new overlaps and may stale earlier acknowledgements. An omitted effect or scope means unknown; an explicitly present empty array asserts that none were observed or declared under the stated method."
    },
    {
      "id": "AWP-COORD-028",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 506,
      "statement": "`unknown` MUST NOT be treated as `compatible`. The configured policy determines whether it warns, negotiates, or blocks."
    },
    {
      "id": "AWP-COORD-029",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 534,
      "statement": "`accepted`, `rejected`, `timed_out`, `cancelled`, and `escalated` are terminal. Escalation after rejection or timeout creates a successor negotiation referencing the terminal record. A further round likewise creates a successor. A processor MUST NOT infer acceptance from silence unless the declared decision policy explicitly defines silence and the enforcing authority supports it."
    },
    {
      "id": "AWP-COORD-030",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 536,
      "statement": "An accepted proposal MAY create commitments. A commitment identifies:"
    },
    {
      "id": "AWP-COORD-031",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 562,
      "statement": "Agent-to-agent negotiation is preferred for routine, low-risk coordination. It MUST escalate to user-mediated arbitration when the agents cannot reach a permitted outcome within the declared negotiation bounds, when applicable policies disagree, when a decision requires authority held by the user or another named principal, or when the competing changes have material safety, compatibility, data-loss, security, or delivery consequences."
    },
    {
      "id": "AWP-COORD-032",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 564,
      "statement": "An arbitration request is a durable coordination record. It MUST identify:"
    },
    {
      "id": "AWP-COORD-033",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 575,
      "statement": "The request MUST NOT embed private chain-of-thought or require the user to reconstruct the dispute from an unbounded transcript. Agents SHOULD present a concise comparison generated from the recorded intents, scopes, contracts, revisions, and evidence. The interaction channel is binding-specific; the durable record is authoritative for the decision."
    },
    {
      "id": "AWP-COORD-034",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 589,
      "statement": "While an arbitration is `awaiting_user`, every agent MUST stop new writes whose validity depends on a blocked scope, disputed contract, competing change-set revision, or unresolved integration decision. Agents MAY continue explicitly listed interim work only when it does not affect a blocked scope and remains valid under every listed alternative. They MUST record any already-created uncommitted artifacts and state-space revisions; the protocol MUST NOT require automatic deletion, rollback, or selection of either agent's branch."
    },
    {
      "id": "AWP-COORD-035",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 591,
      "statement": "A decision event MUST record the selected alternative, exact request revision, decision authority and authenticated principal, decision channel or confirmation reference, rationale, accepted risks, conditions, effective scopes, expiration if any, and required verification. A user interaction may recommend or amend an alternative, but only a decision from the declared authority through a trusted binding can transition arbitration to `decided`. A message that merely claims to be from the user is untrusted content."
    },
    {
      "id": "AWP-COORD-036",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 593,
      "statement": "Agents MUST apply a decision only to the named subjects, revisions, scopes, and conditions. It MUST NOT grant general authority, silently rewrite either agent's history, or authorize unrelated external effects. The decision's implementation is recorded separately through change-set and integration events. Before implementation or integration, agents MUST revalidate all decision conditions and reopen arbitration if a subject revision, scope, contract, evidence basis, authority, or material risk changes. A declined or expired request never implies acceptance; agents must withdraw, re-negotiate, or submit a successor request under policy."
    },
    {
      "id": "AWP-COORD-037",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 614,
      "statement": "`kind` is `unanimous`, `threshold`, `named_participants`, or `authorized_owner`. `eligible_participants` is required except for `authorized_owner`; `threshold` is required only for `threshold` and MUST be between 1 and the eligible count. `required_participants` defaults to empty. `abstention` is `counts_as_no`, `reduces_eligible`, or `prohibited`. Votes and acceptances MUST pin `decides_revision`. Role names alone are not participant identity; a policy using roles must resolve them to an uncontested eligible actor set before evaluation."
    },
    {
      "id": "AWP-COORD-038",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 629,
      "statement": "Global contract status MUST NOT be derived from a single participant's adoption status. Each participant has one of `unaware`, `reviewing`, `accepted`, `implementing`, `implemented`, `verified`, `rejected`, `withdrawn`, or `not_applicable`, with its own evidence and revision."
    },
    {
      "id": "AWP-COORD-039",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 631,
      "statement": "The contract's decision policy specifies named required parties or a quorum. A contract MUST NOT become `accepted`, `implemented`, or `verified` until that state's policy is satisfied."
    },
    {
      "id": "AWP-COORD-040",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 662,
      "statement": "Precondition lifecycle statuses are `active`, `retired`, and `superseded`. `on_false` is `warn`, `block_ready`, `stale`, or `escalate`. `on_unknown` is `warn`, `block_ready`, or `escalate`; it MUST NOT silently pass."
    },
    {
      "id": "AWP-COORD-041",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 683,
      "statement": "`pure` evaluators read only the identified AWP projection or supplied bytes. Adapter-relative and host-relative results MUST record the state space or environment they observed. All evaluators MUST be side-effect-free with respect to the project, deterministic for identical declared inputs, bounded by an explicit timeout, and return `error` rather than partial success after timeout or internal failure. Constraint syntax is owned by the registered evaluator-interface version; an implementation MUST NOT guess unsupported syntax."
    },
    {
      "id": "AWP-COORD-042",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 685,
      "statement": "An asserted precondition records a natural-language statement, asserting actor, scope, epistemic status, evidence if any, and required reviewer or authority. It MUST NOT be presented as machine-verified."
    },
    {
      "id": "AWP-COORD-043",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 798,
      "statement": "A verification result MUST bind the claim being checked to exact inputs."
    },
    {
      "id": "AWP-COORD-044",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 839,
      "statement": "For each event that changes a record revision or status, a deterministic Coordination projector MUST:"
    },
    {
      "id": "AWP-COORD-045",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 865,
      "statement": "An adapter MUST reject `atomic` when its state-space transaction mechanism cannot supply the claimed atomic boundary. Rollback is a separately recorded operation and MUST NOT be assumed successful."
    },
    {
      "id": "AWP-COORD-046",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 867,
      "statement": "Before starting integration, the owner MUST refresh available coordination events, compare the target base, re-evaluate expiring or base-bound preconditions, confirm contract revisions, and re-open any invalidated overlap dispositions."
    },
    {
      "id": "AWP-COORD-047",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 885,
      "statement": "A successful adapter transaction or source-control merge MUST NOT by itself transition an integration to `completed` when combined semantic verification is required."
    },
    {
      "id": "AWP-COORD-048",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 895,
      "statement": "A deterministic Coordination projector MUST:"
    },
    {
      "id": "AWP-COORD-049",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 927,
      "statement": "Synchronization 0.2 governs retention and compaction: a snapshot does not authorize destructive pruning, and snapshot-only exports disclose omitted history. A portable Coordination view MAY omit terminal records irrelevant to the requested continuation only when it declares the omission and does not claim full audit completeness. It MUST retain or make retrievable every active dependency, unresolved conflict, governing contract, precondition, verification, authority decision, and causal record needed to justify current readiness. Physical deletion or redaction follows Synchronization, Artifact, and Security rules."
    },
    {
      "id": "AWP-COORD-050",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 961,
      "statement": "Errors invalidate the affected transition. Warnings preserve state but MUST be visible before a safety-relevant continuation. Implementations MAY add namespaced diagnostics."
    },
    {
      "id": "AWP-COORD-051",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 968,
      "statement": "a binding that claims presence monitoring or the scaling profile MUST satisfy"
    },
    {
      "id": "AWP-COORD-052",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 990,
      "statement": "Lease states are `requested`, `active`, `denied`, `released`, `expired`, `revoked`, and `superseded`. The coordinator grants a lease only after an atomic comparison against current protected state. Renewal creates a new expiration and MUST NOT reduce the fencing token."
    },
    {
      "id": "AWP-COORD-053",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 992,
      "statement": "An adapter claiming enforcement MUST reject a protected mutation whose token is older than the highest token it has accepted for that namespace. A new grant, new holder, or new coordinator epoch MUST issue a token strictly greater than every previously issued token in that protected namespace. Renewal of the same uninterrupted lease retains its token; it changes expiration but does not create a new ownership generation. Without this fencing check, a paused or partitioned former holder may act after its lease expires."
    },
    {
      "id": "AWP-COORD-054",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 994,
      "statement": "If coordinator identity, epoch, authentication, protected scope, or fencing validation is unavailable, the lease is `unverifiable` outside the reachable enforcement guarantee. The implementation MUST NOT describe it as exclusive. Local work may continue under policy, but integration MUST refresh state and re-evaluate overlap and preconditions."
    },
    {
      "id": "AWP-COORD-055",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 996,
      "statement": "A COOP-3 enforcement profile MUST specify retry limits, heartbeat interval, lease duration, expiry clock authority, deadlock detection, starvation policy, cancellation consequences, and human/organizational arbitration. The base module defines no universal timing defaults because safe values depend on task duration, network delay, and the protected system. Named interoperability and test profiles MAY define explicit defaults."
    },
    {
      "id": "AWP-COORD-056",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1002,
      "statement": "A principal is the human or organization accountable for an actor's participation. A COOP-3 session MUST bind authenticated actors to principals and declare the governing policy. Cross-principal coordination MUST identify:"
    },
    {
      "id": "AWP-COORD-057",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1011,
      "statement": "AWP content is untrusted input. Imported intents, contracts, commitments, leases, and authority records MUST NOT cause execution without receiver policy evaluation. Secret values SHOULD be referenced through protected artifacts rather than embedded in coordination records."
    },
    {
      "id": "AWP-COORD-058",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1013,
      "statement": "Coordination defines no separate protected-artifact envelope. A protected input uses the Artifact module's availability, remote-location, retrieval-requirement, and integrity fields together with Security classification or `secret_ref` metadata. A URI or digest alone proves neither confidentiality nor retrievability. Digests of low-entropy secrets may themselves enable guessing attacks and MUST be omitted or protected when receiver policy classifies the digest as sensitive."
    },
    {
      "id": "AWP-COORD-059",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1059,
      "statement": "Private event kinds use a controlled namespaced module ID. They MUST NOT add unregistered bare kinds to this module."
    },
    {
      "id": "AWP-COORD-060",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1073,
      "statement": "For the named `coop3-a2a-v1` profile, A2A is the distributed communications and execution control plane for typed AWP coordination operations. An A2A request MUST carry the operation identifier, workstate identifier, stable binding identity, acting AWP actor, and the expected revision, frontier, or fencing token applicable to the operation. A response MUST carry either a durable AWP receipt that identifies the accepted event or protected decision, or a stable rejection or conflict diagnostic. A2A delivery, task completion, or peer authentication does not replace the binding's durable persistence, principal mapping, authorization decision, epoch comparison, or fencing check."
    },
    {
      "id": "AWP-COORD-061",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1075,
      "statement": "An A2A adapter MUST preserve idempotency across retry, reconnect, duplicate delivery, endpoint migration, and task-status polling. It MUST make transport reachability and AWP store or gateway reachability separately observable. If protected enforcement cannot verify the actor/principal, binding epoch, expected state, protected scope, or fencing token, it MUST reject the protected operation even if the A2A task was successfully delivered. A2A is optional outside a binding that explicitly claims `coop3-a2a-v1`."
    },
    {
      "id": "AWP-COORD-062",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1083,
      "statement": "[MPAC, arXiv:2604.09744 version 1](https://arxiv.org/abs/2604.09744v1) session, intent, operation, conflict, and governance objects may map to corresponding AWP records. AWP retains domain-specific semantic scopes, contracts, preconditions, verification binding, persistent project history, and resume/handoff state. A mapping MUST identify information loss and MUST NOT equate MPAC transport/session acceptance with AWP integration readiness."
    },
    {
      "id": "AWP-COORD-063",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1123,
      "statement": "The fixture inventory does not itself establish a Cooperation Contract claim. The following minimum attribution makes the evidence boundary auditable: a `COOP-1` claim needs the applicable scenarios in Cooperation Contracts \u00a74.3, including deterministic replay, record-validity rejection, compatible and incompatible physical scopes, resolution, lease expiry, fresh handoff, and binding identity across filesystem paths. This inventory contributes direct coverage for physical non-overlap and same-file conflict (1\u20132), structural precondition or verification binding (7\u20138), contested projection (11\u201312), recovery and expiry (14\u201315, 23\u201325), and presence overlap behavior (21\u201322). A `COOP-2` claim additionally needs semantic conflict, relied-upon read, material undeclared scope, contract revision, dependency cycle, and integration-readiness coverage (3\u20136, 9\u201310, 13). A `COOP-3` claim additionally needs fenced mutation, epoch, authorization, and protected-operation coverage (16\u201318, 26\u201332 as applicable). A claimed operating envelope MUST identify any required scenario that has no corresponding executable fixture; the present inventory does not by itself discharge COOP-1 \u00a74.3 scenario 9's different-filesystem-path binding-identity evidence."
    },
    {
      "id": "AWP-COORD-064",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1158,
      "statement": "Each fixture SHOULD include input events, expected frontier, expected materialized records, expected diagnostics, and an explanation of the safety property."
    },
    {
      "id": "AWP-COORD-065",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1162,
      "statement": "Before the complete integration-assurance schema is frozen, the project SHOULD run an early `coordination-awareness` experiment comparing chat-only coordination with durable intents, pinned scopes, overlaps, acknowledgements, and conflict-preserving projection. It MUST measure false-positive and false-negative overlap classifications, authoring cost, coordination delay, and whether warnings arrive before conflicting implementation. Results may change the scope and record model before further standardization."
    },
    {
      "id": "AWP-COORD-066",
      "source": "spec/drafts/0.8.0/coordination.md",
      "line": 1180,
      "statement": "1. Canonical JSON and digest rules remain a Core/Artifact/Security family issue and must be resolved before signed coordination evidence is portable. The family profile should evaluate RFC 8785 JCS while explicitly handling its I-JSON, IEEE-754 number, and Unicode-preservation constraints; Coordination MUST NOT select a conflicting local canonicalization."
    },
    {
      "id": "AWP-COORDSCALE-001",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 57,
      "statement": "Required fields are `agent_id`, `session_id`, `principal`, `workstate_id`, `project`, `execution_location`, `base`, `declared_scopes`, `access_mode`, `monitoring_profile`, `heartbeat_at`, and `expires_at`. Project identity MUST be stable across worktrees or execution locations. `session_id` identifies one runtime generation and MUST NOT be reused after release or expiry. `base` binds the announcement to the revision from which work began. `declared_scopes` contains pinned Coordination scope references; a broad provisional scope MAY be announced and narrowed by a later revision."
    },
    {
      "id": "AWP-COORDSCALE-002",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 59,
      "statement": "Presence states are `active`, `released`, `expired`, and `superseded`. Entry MUST publish an active presence record before the actor performs a declared write. A heartbeat atomically advances `heartbeat_at` and `expires_at` for the same active session. It MUST NOT revive an expired, released, or superseded session; a returning runtime creates a new session identity."
    },
    {
      "id": "AWP-COORDSCALE-003",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 61,
      "statement": "The monitoring profile defines heartbeat interval, session duration, registry clock authority, retry policy, watcher cursor retention, and notification delivery. A monitor classifies a session as expired only through the profile's registry clock and an atomic compare against the latest heartbeat. Client wall clocks alone MUST NOT authoritatively expire a shared session. In an advisory deployment, an observer that cannot reach the registry reports presence as `unverifiable`, not absent."
    },
    {
      "id": "AWP-COORDSCALE-004",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 63,
      "statement": "A watcher maintains a durable cursor over lifecycle notifications. It announces at least new sessions, terminal sessions, and newly detected overlaps or conflicts. Delivery MUST be idempotent by notification identity. Restarting a watcher MUST resume from its stored cursor or explicitly disclose an observation gap. Heartbeats SHOULD update materialized live state without producing a durable event for every renewal; implementations MAY sample heartbeat evidence under a declared retention policy."
    },
    {
      "id": "AWP-COORDSCALE-005",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 65,
      "statement": "On entry, an implementation using presence monitoring MUST:"
    },
    {
      "id": "AWP-COORDSCALE-006",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 74,
      "statement": "On normal exit, an implementation MUST stop new mutation, publish its final change set and semantic checkpoint or synchronization delta, refresh the canonical Capsule through the current projection owner, and then release its presence session. If the Capsule cannot be refreshed, the writer MUST publish an incomplete-handoff diagnostic rather than presenting the prior Capsule as current. Crash recovery relies on expiry and MUST preserve an `expired` terminal observation."
    },
    {
      "id": "AWP-COORDSCALE-007",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 76,
      "statement": "Heartbeats and other high-frequency live values MUST NOT be written into the project Capsule. The Capsule remains a durable semantic projection updated at checkpoints and handoff. Entry, release, expiry, conflict, and incomplete-handoff facts MAY be retained as durable Coordination events when they affect interpretation or audit."
    },
    {
      "id": "AWP-COORDSCALE-008",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 78,
      "statement": "Multiple agents MUST NOT independently overwrite one canonical Capsule from the same base frontier. Each agent publishes events or deltas; a single current projection owner updates the Capsule using compare-and-swap against its frontier and generated digest. A stale writer merges, retries, or reports divergence through Synchronization. It MUST NOT use last-write-wins."
    },
    {
      "id": "AWP-COORDSCALE-009",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 88,
      "statement": "An implementation intended for many concurrent agents MUST avoid project-wide polling and all-pairs overlap comparison. It SHOULD:"
    },
    {
      "id": "AWP-COORDSCALE-010",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 100,
      "statement": "Sharding MUST NOT change the semantic result of overlap evaluation. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants require an identified routing or aggregation strategy. An implementation MUST disclose any scope class it cannot compare completely."
    },
    {
      "id": "AWP-COORDSCALE-011",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 106,
      "statement": "The profile has four logical responsibilities, which MAY be implemented by one service or separate replicated services:"
    },
    {
      "id": "AWP-COORDSCALE-012",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 115,
      "statement": "The primary partition key MUST include stable project identity and state-space identity. Session ownership, renewal, release, and expiry for one session MUST be linearizable within its owning partition. Exact pinned scopes SHOULD use an inverted index keyed by scope identity and access mode rather than scanning all active sessions."
    },
    {
      "id": "AWP-COORDSCALE-013",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 117,
      "statement": "A scope router MUST identify every partition that can contain a potentially interacting scope under the declared comparison policy. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants MUST be routed to an aggregator or a declared global-scope partition. If any required partition or index is unavailable, the result is `unverifiable`; the implementation MUST NOT report that no conflict exists."
    },
    {
      "id": "AWP-COORDSCALE-014",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 119,
      "statement": "Partition rebalancing MUST preserve session generation, terminal state, watcher position, and overlap results. A former partition owner MUST NOT accept a renewal or release after ownership has transferred. Implementations SHOULD use epochs, compare-and-swap, or equivalent stale-owner rejection even though presence itself remains advisory."
    },
    {
      "id": "AWP-COORDSCALE-015",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 123,
      "statement": "Heartbeats MUST route directly by session identity and update coalesced materialized state. They MUST NOT produce one durable broker event per renewal. A heartbeat update MUST compare the session generation and current active state atomically, so a delayed message cannot revive a terminal or replaced session."
    },
    {
      "id": "AWP-COORDSCALE-016",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 125,
      "statement": "Expiry MUST be scheduled from the authoritative registry time of the owning partition. An expiry worker MUST atomically compare the expected session generation and latest expiration before publishing `presence.expired`. Duplicate expiry attempts and duplicate lifecycle delivery MUST converge through stable event identity and idempotent processing."
    },
    {
      "id": "AWP-COORDSCALE-017",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 129,
      "statement": "Watchers SHOULD subscribe by project plus pinned scopes, scope classes, or declared global interest. The broker MUST support durable cursors, bounded delivery pages, idempotent retry, and an explicit retention interval. Cursor state MAY be compacted, but a watcher whose cursor falls behind retained history MUST receive `presence.observation_gap` before current state is presented as complete."
    },
    {
      "id": "AWP-COORDSCALE-018",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 131,
      "statement": "When a hot or wildcard scope matches many sessions, the registry SHOULD publish a bounded conflict-set summary plus a resumable cursor instead of one unbounded notification per pair. Backpressure MUST NOT silently discard a safety-relevant lifecycle, conflict, gap, or incomplete-handoff observation. A deployment MUST declare queue limits, overflow behavior, retry limits, and the point at which presence becomes `unverifiable`."
    },
    {
      "id": "AWP-COORDSCALE-019",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 133,
      "statement": "Terminal sessions, lifecycle events, watcher cursors, conflict summaries, and sampled liveness evidence MUST have explicit retention policies. Retention expiry MUST NOT erase durable semantic events already incorporated into a checkpoint or Capsule projection."
    },
    {
      "id": "AWP-COORDSCALE-020",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 137,
      "statement": "The registry MUST authenticate the submitting runtime and bind it to the asserted agent and principal under deployment policy. Authorization MUST constrain which projects, scopes, subscriptions, and presence details that identity may publish or observe. Authentication of presence proves only who made the announcement; it grants no project authority and no permission to mutate a scope."
    },
    {
      "id": "AWP-COORDSCALE-021",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 139,
      "statement": "Deployments spanning trust boundaries MUST define transport protection, replay protection, tenant isolation, audit retention, and redaction of worktree, branch, scope, and principal metadata. A monitor MUST distinguish unauthorized, unreachable, stale, and absent state."
    },
    {
      "id": "AWP-COORDSCALE-022",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 143,
      "statement": "Agents MUST publish final semantic events or synchronization deltas before release; they MUST NOT race to overwrite the canonical Capsule. For each workstate, the projection service MUST expose one logical writer and compare the expected frontier and generated digest before replacement. Replicated projectors MUST use fenced ownership or an equivalent mechanism that prevents a stale projector from publishing after ownership transfer."
    },
    {
      "id": "AWP-COORDSCALE-023",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 145,
      "statement": "A projection conflict MUST reload and reconcile the new frontier, retry under policy, or publish divergence. It MUST NOT resolve by last-write-wins. Projector failure does not keep heartbeat values in the Capsule: it produces an incomplete-handoff observation while the live registry and durable event stream remain separate."
    },
    {
      "id": "AWP-COORDSCALE-024",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 149,
      "statement": "A conforming deployment MUST publish the profile parameters and tested envelope on which its capacity claim depends, including session duration, heartbeat interval, active-session count, scope distribution, wildcard rate, partitions, replication, event retention, and watcher fan-out. It SHOULD report p50, p95, and p99 entry, renewal, expiry, notification, conflict-query, and projection latency together with error, retry, gap, and false-alarm rates."
    },
    {
      "id": "AWP-COORDSCALE-025",
      "source": "spec/drafts/0.8.0/coordination-scale.md",
      "line": 151,
      "statement": "Load tests MUST include synchronized renewal bursts, hot scopes, wildcard scopes, broker restart, partition-owner failover, delayed and duplicated messages, watcher lag beyond retention, network partition, clock skew, and concurrent Capsule projection. A deployment MUST identify which guarantees remain available during each failure. Results from the local SQLite profile or a sequential synthetic probe MUST NOT be presented as evidence of distributed capacity."
    },
    {
      "id": "AWP-SECURITY-001",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 17,
      "statement": "A workstate using Security metadata MUST declare this module. It MUST be required when interpreting a registered signature, encryption, redaction, or handling profile is necessary for the receiver's declared continuation. Core safety rules still apply when this module is absent."
    },
    {
      "id": "AWP-SECURITY-002",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 49,
      "statement": "Classification and privacy vocabularies may be organization-specific but private values MUST be namespaced. `contains_secrets` is `true`, `false`, or `unknown`. A writer MUST NOT use `false` when secret-scan status is `findings`, `not_run`, or `unknown`."
    },
    {
      "id": "AWP-SECURITY-003",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 53,
      "statement": "A guardrail is a portable, structured security constraint that limits what an actor or runtime may do with a workstate. It is a security extension of a Core `constraint` record and MUST remain subordinate to receiver policy and currently verified authority. A guardrail communicates a prohibition or required control across models, agents, runtimes, and transports; it is not merely a system-prompt convention."
    },
    {
      "id": "AWP-SECURITY-004",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 55,
      "statement": "A guardrail SHOULD identify:"
    },
    {
      "id": "AWP-SECURITY-005",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 95,
      "statement": "Guardrails apply in both solo and collaborative work. A lone agent's requested action is evaluated against the applicable guardrails before execution. In a collaboration, the same guardrails apply to every participating agent, delegated task, change set, integration plan, and derived operation. An agent MUST NOT evade a guardrail by asking another agent to perform the prohibited step, splitting it into individually innocuous steps, or moving it into an adapter. A collaborator may add a stricter guardrail, but MUST NOT weaken or override an applicable required guardrail through an intent, authority claim, contract, or user-arbitration alternative."
    },
    {
      "id": "AWP-SECURITY-006",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 97,
      "statement": "Portable guardrails are shared policy state, not proof of enforcement. A host or protected adapter must enforce them. If a required guardrail cannot be interpreted, its scope or policy owner is ambiguous, or its enforcement status is unverifiable, the affected external or security-sensitive operation MUST remain blocked pending local policy evaluation. Guardrail changes are new revisions with provenance; they do not silently mutate prior workstate history."
    },
    {
      "id": "AWP-SECURITY-007",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 105,
      "statement": "Receivers SHOULD place newly imported workstates in local quarantine until they evaluate:"
    },
    {
      "id": "AWP-SECURITY-008",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 116,
      "statement": "Quarantine is receiver-owned state. A serialized assertion MAY describe the sender's handling state but MUST NOT disable receiver quarantine or grant trust."
    },
    {
      "id": "AWP-SECURITY-009",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 120,
      "statement": "Text in artifacts, summaries, claims, evidence, transcripts, extensions, and module data may contain instructions. Merely parsing, rendering, retrieving, verifying, or signing a workstate MUST NOT authorize execution."
    },
    {
      "id": "AWP-SECURITY-010",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 122,
      "statement": "Readers MUST distinguish descriptive content from an authorized requested action. Unknown modules and executable content MUST NOT run automatically. Module processors SHOULD be isolated according to risk."
    },
    {
      "id": "AWP-SECURITY-011",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 126,
      "statement": "An imported task classified as `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, or `destructive` MUST NOT become ready or execute solely because the workstate requests it."
    },
    {
      "id": "AWP-SECURITY-012",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 128,
      "statement": "The receiver re-evaluates current identity, resource scope, authority source, conditions, expiration, revocation, confirmation requirements, and local policy. A receiver with greater access than the sender MUST avoid becoming a confused deputy."
    },
    {
      "id": "AWP-SECURITY-013",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 132,
      "statement": "Writers SHOULD use secret references instead of values:"
    },
    {
      "id": "AWP-SECURITY-014",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 142,
      "statement": "A reference does not authorize resolution. Exporters MUST apply their configured secret and data-loss-prevention policy to included event payloads, execution output, evidence, generated views, module data, and artifact paths. Scan status is `passed`, `findings`, `not_run`, or `unknown`. Passing is evidence of a check, not proof of absence."
    },
    {
      "id": "AWP-SECURITY-015",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 144,
      "statement": "Writers SHOULD omit irrelevant transcripts and personal data and support classification, audience, retention, and jurisdiction metadata. Omission must not be disguised by a stronger completeness claim."
    },
    {
      "id": "AWP-SECURITY-016",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 148,
      "statement": "Physical redaction creates a new workstate history lineage. It MUST:"
    },
    {
      "id": "AWP-SECURITY-017",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 163,
      "statement": "Signatures may cover individual events, frontier manifests, snapshots, artifact manifests, module data, or complete packages. Signature metadata MUST identify algorithm, key identifier, coverage, canonicalization profile, signer, and verification status."
    },
    {
      "id": "AWP-SECURITY-018",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 175,
      "statement": "AWP Security 0.5.0 does not select a normative canonicalization or signature algorithm. Implementations MUST NOT claim interoperable AWP signature conformance without naming an external or future registered signature profile."
    },
    {
      "id": "AWP-SECURITY-019",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 179,
      "statement": "Encryption metadata may describe package-wide, module-level, artifact-level, or recipient-based protection. It MUST identify the encryption profile and protected scope without exposing keys or secret values."
    },
    {
      "id": "AWP-SECURITY-020",
      "source": "spec/drafts/0.8.0/security.md",
      "line": 187,
      "statement": "When Capsule or Artifact is used, processors MUST apply their traversal, normalization, size, decompression, integrity, executable-content, and retrieval rules. A signature over an unsafe archive does not make extraction safe."
    },
    {
      "id": "AWP-COOP-001",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 8,
      "statement": "The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals."
    },
    {
      "id": "AWP-COOP-002",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 17,
      "statement": "`COOP-1`, `COOP-2`, and `COOP-3` are AWP 0.8's single cumulative **work-coordination** ladder. The Coordination module defines the durable records, capability bundles, and mechanisms used by those contracts; it does not define a competing conformance axis. There is no `COOP-0` contract or separate portable-collaboration tier. The active draft is project-scoped: a project that does not select a COOP contract MAY maintain a workstate, but it MUST NOT claim cooperative coordination."
    },
    {
      "id": "AWP-COOP-003",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 33,
      "statement": "This mapping is not an automatic conformance upgrade. An implementation MUST satisfy the guarded-work, checkpoint, recovery, operating-envelope, and evidence requirements of the claimed contract. Historical workstates remain governed by the specification they explicitly declare."
    },
    {
      "id": "AWP-COOP-004",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 45,
      "statement": "An implementation with an active Cooperation Contract MUST identify the selected contract, top-level claim state, operational mode, material limitations, and a `subprotocols` object. `subprotocols.work` identifies whether guarded work is enabled and its claim state. `subprotocols.consultation` identifies whether consultation is disabled, `user-mediated`, or `managed`, and, when enabled, its policy and claim state. A disabled consultation subprotocol MUST NOT require agents to initiate, answer, or wait for a consultation. A `user-mediated` subprotocol lets an agent publish a bounded question or escalation for the decision owner but MUST NOT authorize agents to run a work-affecting exchange among themselves. A `managed` subprotocol is available only to `COOP-2` or `COOP-3` and requires the explicit authorization and budget defined in Section 5."
    },
    {
      "id": "AWP-COOP-005",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 47,
      "statement": "An unqualified conformant `COOP-1`, `COOP-2`, or `COOP-3` claim describes the corresponding **work** contract. It does not imply that consultation is enabled or conformant. A conformant optional consultation claim is additional and MUST be stated in `subprotocols.consultation`; it MUST NOT be inferred from a Core `consultation` record alone. Merely selecting a contract or implementing one capability MUST NOT be represented as conformance. Imported workstate remains context, not authorization for external effects."
    },
    {
      "id": "AWP-COOP-006",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 49,
      "statement": "The machine-readable binding disclosure, subprotocol claims, loop policy, interaction, and result shapes are defined by `../../../schemas/awp-cooperation-0.1.schema.json`. Module-owned records MUST declare `module: urn:awp:cooperation`."
    },
    {
      "id": "AWP-COOP-007",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 53,
      "statement": "The active draft does not define standalone capsule exchange, package exchange, wire-payload exchange, or cross-project collaboration. Those directions are archived for possible future profiles. A project without a selected Cooperation Contract MAY retain a local workstate under host policy, but it MUST NOT claim participant discovery, scope reservation, conflicting-mutation prevention, managed collaboration, or coordinated integration."
    },
    {
      "id": "AWP-COOP-008",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 55,
      "statement": "A processor that encounters recognized Cooperation or Coordination records without supporting their required semantics MUST preserve and expose them without implying that it validated their operational effect. Unknown fields MUST be preserved by a lossless processor."
    },
    {
      "id": "AWP-COOP-009",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 57,
      "statement": "Core `consultation` records MAY support a bounded question or escalation inside a declared project. They do not create an independent collaboration level, require no participant lease by themselves, and MUST NOT be treated as authorization for an action. A response MUST identify uncertainty and supporting evidence when available."
    },
    {
      "id": "AWP-COOP-010",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 61,
      "statement": "`COOP-1` is the default contract for a small shared project group. It reduces collisions in guarded, explicitly comparable work without requiring agents to exchange reasoning beyond the structured coordination information needed to proceed or block. A material conflict, ambiguity, or request for a work-affecting decision is surfaced to the declared decision owner; it does not start an autonomous agent-to-agent loop. It is intended to be useful for more than two concurrent participants without making an unmeasured capacity claim, though Section 4.3 permits an explicitly bounded two-participant operating envelope. It MUST NOT require a separate database or continuously running service. A binding MAY use repository-local files, atomic filesystem operations, an embedded store, or another local mechanism, provided it preserves the requirements below."
    },
    {
      "id": "AWP-COOP-011",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 63,
      "statement": "For every Coordination record or event used to make a work-coordination decision, the binding MUST perform `COOP-1` record-validity validation of workstate identity, event identity, ancestry, revisions, lifecycle transitions, pinned references, and typed precondition and verification bindings. It MUST exclude or block structurally stale or unverifiable input with a stable diagnostic. Projection MUST be independent of transport order, preserve concurrent non-commuting successors as contested, and return stable diagnostics for excluded or unverifiable input. A component MAY advertise a `deterministic-coordination-projector` capability, but that component alone MUST NOT claim `COOP-1`; the contract applies to the composed participant, binding, projector, checkpoint, and recovery behavior."
    },
    {
      "id": "AWP-COOP-012",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 65,
      "statement": "A `COOP-1` participant lease is a bounded liveness record with exit coupling in the cooperation binding. It lets participating agents discover an active participant and recover when its renewal stops; release is permitted only after the linked work is terminal and a durable handoff receipt is available. It does not authenticate a principal, fence a source-control write, grant authority, or require its holder to participate in a consultation. A binding's guarded-mutation guarantee applies only to participants that use the binding and obey its returned decision. Protected mutation paths, authenticated principals, epochs, and fencing are `COOP-3` guarantees and MUST NOT be inferred from a `COOP-1` claim."
    },
    {
      "id": "AWP-COOP-013",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 69,
      "statement": "Before guarded work, a `COOP-1` participant MUST:"
    },
    {
      "id": "AWP-COOP-014",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 77,
      "statement": "The binding MUST make the announce-and-check operation atomic with respect to other `COOP-1` announce operations for the same guarded scopes. Compatible work MAY proceed concurrently. A known incompatible guarded mutation MUST return `blocked`, `waiting`, or an equivalent non-permitted outcome until participants record a partition, order, withdrawal, or escalation. A warning-only result is insufficient for a binding to claim the `COOP-1` guarded-mutation guarantee."
    },
    {
      "id": "AWP-COOP-015",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 79,
      "statement": "A binding that cannot make announce-and-check atomic with respect to concurrent announcements for the same guarded scopes MUST NOT claim `COOP-1`; it MUST disclose operational mode `snapshot_only`, `degraded`, or `unavailable` as applicable."
    },
    {
      "id": "AWP-COOP-016",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 81,
      "statement": "Before guarded work, participants MUST compare a stable binding identity containing the workstate identifier, repository-intrinsic project identifier, canonical store identifier, scope-model identifier and version, and binding epoch. The project identifier MUST derive from repository-intrinsic state and MUST NOT derive from a filesystem path or mount location. Any mismatched or unverifiable stable identity field MUST produce `blocked`."
    },
    {
      "id": "AWP-COOP-017",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 83,
      "statement": "Operational reach and frontier are observations, not stable identity. Each observation MUST identify its observation time, reach, and current frontier. Frontier values MAY differ as the binding advances; a participant MUST refresh, reconcile an ancestor or newer frontier, and block on an unverifiable history gap rather than require byte equality with another participant's earlier frontier. Reach is `shared`, `worktree-local`, `configured-unverified`, `degraded`, `snapshot-only`, or `unavailable`. An explicit store path begins as `configured-unverified`; it becomes `shared` only after at least two declared work participants have each recorded a binding entry that names the same stable store identity. A binding MUST retain or return that handshake evidence. A participant MUST NOT merge records from different store identifiers into one work decision; it MUST select one declared binding or return `blocked`. A binding MUST disclose its atomicity mechanism and the storage or filesystem assumptions under which it is valid."
    },
    {
      "id": "AWP-COOP-018",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 85,
      "statement": "A binding MUST normalize a path-like guarded scope to a repository-relative path, normalize separators and dot segments, and reject parent traversal outside the repository. Two path scopes overlap when they are equal or either is an ancestor of the other at a path-segment boundary. For every overlapping pair, the binding MUST apply a declared, versioned access-mode compatibility table. If either operation may mutate and the table does not explicitly permit the pair, the pair is incompatible. A scope kind without a declared comparison function is non-comparable; the binding MUST either conservatively block a guarded mutation or disclose that the scope is outside its guarded guarantee. \u201cKnown\u201d means visible in the same atomic decision from all active, non-expired intents within the binding's declared reach and frontier. Case-folding, Unicode normalization, and symbolic-link treatment MUST be declared by the scope model."
    },
    {
      "id": "AWP-COOP-019",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 87,
      "statement": "`COOP-1` requires only declared physical or otherwise explicitly comparable scope. It MUST disclose that semantic conflicts outside its declared scope model can remain undetected. A clean source-control merge is not proof of compatibility."
    },
    {
      "id": "AWP-COOP-020",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 91,
      "statement": "At a meaningful checkpoint and before exit, a participant MUST publish its actual scope, outcome, evidence references, unresolved work, and recommended next action through the selected binding. Actual scope is the participant's own assertion about work performed and its declared physical scopes; it is not an `observed_scope` record. An `observed_scope` record is analyzer-produced evidence under `COOP-2`, does not overwrite the participant's declaration, and may impose additional readiness consequences. The canonical capsule projection MUST identify the frontier it includes and its integrity digest. One logical publisher per workstate MUST serialize canonical capsule replacement using an expected capsule-frontier and digest comparison or an equivalent stale-writer exclusion rule. When a binding has a distinct event frontier, it MUST compare that expected event frontier independently; a legacy capsule frontier and a binding event frontier MUST NOT be assumed equal. A checkpoint receipt MUST identify the capsule path, whole-artifact digest, generated-region digest, and included frontier. A fresh-entry operation MUST report the capsule as `current`, `modified`, or `stale`; a binding MUST NOT permit guarded work while the canonical capsule is `modified` unless a host explicitly records an override outside the `COOP-1` claim."
    },
    {
      "id": "AWP-COOP-021",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 93,
      "statement": "On exit, the participant MUST publish its final semantic handoff before releasing its lease. The binding MUST reject release while an intent linked to the lease remains nonterminal or unless a durable receipt identifies an already published handoff artifact and its integrity digest. Recording a planned output identifier before the artifact exists is not publication confirmation. If the capsule projection, terminal publication, or lease release cannot be confirmed, the participant MUST report a recoverable pending exit rather than claim completion. If a participant crashes, its lease MUST expire without requiring a capsule rewrite; the durable capsule remains the last confirmed semantic handoff."
    },
    {
      "id": "AWP-COOP-022",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 109,
      "statement": "The claim MUST state the tested operating envelope. A claim with a maximum concurrent participant count of three or more MUST additionally show three or more compatible participants proceeding without false blocking. It MUST NOT infer a larger participant limit, cross-host reliability, semantic-conflict detection, or effectiveness from this minimum evidence."
    },
    {
      "id": "AWP-COOP-023",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 113,
      "statement": "The work participant declares scope, access, evidence, and actual outcome; obeys blocked decisions; and supplies a concise rationale without private chain-of-thought. The work binding normalizes and compares scopes, owns transactions and leases, returns receipts, and enforces guarded-work lifecycle rules. A host enforces its own authority and side-effect policy; work metadata MUST NOT expand that authority."
    },
    {
      "id": "AWP-COOP-024",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 117,
      "statement": "`subprotocols.consultation` is disabled unless explicitly enabled. Portable Core consultations may occur with no selected contract under Section 3. A `COOP-1` binding MAY enable only `user-mediated` consultation: agents may publish a bounded question, conflict, or escalation for the decision owner, but MUST NOT autonomously ask another agent to analyze, negotiate, delegate, or decide work whose outcome affects guarded work. Until the decision owner records a disposition, the affected work remains blocked, waiting, or explicitly outside the `COOP-1` guarantee."
    },
    {
      "id": "AWP-COOP-025",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 119,
      "statement": "`COOP-2` and `COOP-3` MAY enable `managed` collaboration. This is the level at which agents may directly exchange richer context, critique an approach, reconcile semantic conflicts, prepare an integration plan, or delegate bounded analysis. A managed interaction is never implicit: before its first agent-to-agent request, the binding MUST record an authorization reference from the decision owner or authorized principal and a policy naming the permitted participants, purpose, subject or scopes, decision owner, maximum rounds, maximum participant responses, maximum tool calls, maximum context tokens per request, maximum output tokens per response, maximum total output tokens, a positive `delivery_window_seconds`, and its `clock_authority`. A binding MUST stop or return `inconclusive` or `escalated` when any limit is reached. Token values are declared budget ceilings; a binding that cannot measure a value MUST disclose that limit as unenforced and MUST NOT claim enforced managed-collaboration budgeting."
    },
    {
      "id": "AWP-COOP-026",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 123,
      "statement": "When enabled, a cooperation interaction MUST identify:"
    },
    {
      "id": "AWP-COOP-027",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 132,
      "statement": "A managed interaction MUST additionally identify its authorization reference and the policy budget consumption or an explicit measurement limitation. A `user-mediated` interaction MUST identify the decision owner and MUST NOT treat a responder's advice as a disposition or permission for guarded work."
    },
    {
      "id": "AWP-COOP-028",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 134,
      "statement": "A consultation interaction MUST NOT silently authorize a guarded mutation or reserve a work scope. An accepted recommendation becomes actionable only when the decision owner records the resulting partition, order, intent, or other required project decision. A work lease MUST NOT be interpreted as consent to be interrupted for consultation, and a binding MUST NOT require a work lease as a precondition for initiating or responding to consultation."
    },
    {
      "id": "AWP-COOP-029",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 156,
      "statement": "A round MUST add a new artifact, evidence item, explicit decision, or identified disagreement. The interaction MUST record that contribution as `progress.kind` with a reference to the new item. The `repeat_basis` MUST contain the purpose, canonical subject, context frontier, participant-set digest, and policy digest. `participant_set_digest` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of the lexicographically sorted array of participant identifier strings. `policy_digest` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of the complete effective policy object. `repeat_key` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of `repeat_basis`. A binding MUST reject an interaction whose supplied participant-set or policy digest does not match these calculations. A binding MUST deduplicate a repeated interaction with the same repeat key, or return the prior outcome, unless the repeat basis changed. On reaching a limit, it MUST return `inconclusive` or `escalated`; it MUST NOT start an unbounded optimization loop."
    },
    {
      "id": "AWP-COOP-030",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 158,
      "statement": "Loop budgets are independent of participant-lease duration and work-operation retry policy. A project or binding MAY declare additional parameters, higher budgets, stricter cost limits, time limits, evaluator thresholds, model diversity requirements, or domain-specific stopping predicates. Unknown policy parameters MUST be preserved. A participant that does not understand a parameter marked required by the effective policy MUST NOT claim to enforce that policy and MUST request a compatible policy, delegate enforcement to the binding, or decline the interaction. Only the declared decision owner MAY continue an interaction after the effective budget is exhausted."
    },
    {
      "id": "AWP-COOP-031",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 166,
      "statement": "When managed consultation is enabled, the binding MUST provide a project-scoped rendezvous. A participant MUST be able to register its actor identity, capabilities, current lease, and availability against the immutable tuple `(project_id, workstate_id, binding identity)`, and another authorized participant MUST be able to discover that registration and active interaction records through that tuple. Discovery MUST NOT depend on manually exchanging an artifact path, private prompt, or session-specific URL."
    },
    {
      "id": "AWP-COOP-032",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 168,
      "statement": "The binding descriptor MUST identify participant discovery and interaction publication/retrieval separately from the current frontier. If the rendezvous cannot be read or verified, the binding MUST report `unavailable` or `unverifiable` and MUST NOT imply that an agent-to-agent channel exists. Managed communication MUST use durable interaction identifiers and receipts; registration, discovery, request, response, acknowledgement, timeout, and withdrawal MUST be idempotent and correlated to the same interaction and binding identity. A host MAY persist records for a model, but a model-generated message is not delivered until the binding returns a publication receipt."
    },
    {
      "id": "AWP-COOP-033",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 170,
      "statement": "Initial authorization MUST name the participating actors (or a bounded participant set), decision owner, purpose, subject scope, and loop, tool, and token budgets. Discovery MUST NOT widen that authorization. A newly discovered participant is ineligible for work-affecting requests until covered by authorization and entered in the binding."
    },
    {
      "id": "AWP-COOP-034",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 172,
      "statement": "A managed-collaboration binding MUST separately declare its **delivery mode**: `host-dispatch`, `subscription`, `signalled-poll`, `polling`, or `unavailable`. `host-dispatch` means the host delivers a published request to the named active session or records a stable delivery failure. `subscription` means the receiving host has durably subscribed and the binding provides bounded retry or an explicit expiry outcome. `signalled-poll` means an independently identified signal channel tells a host watcher to refresh the authoritative binding; the signal contains no authoritative interaction state, and a watcher MUST correlate it to the binding by event identifier and frontier before reading. Its disclosure MUST name the signal channel, correlation rule, coalescing behavior, and the outcome when the signal channel is unavailable while the binding remains healthy. Watcher liveness MUST be disclosed per participant actor and MUST be derived from evidence the binding can observe (for example a watcher heartbeat with a declared time-to-live), never from a participant's own declaration; the derived states are `active`, `stale`, `none`, and `unverified`. A binding MUST report signal reach per ordered sender-recipient pair, separately from mailbox reach, because one shared mailbox does not imply a signal path in both directions; a pair whose recipient watcher is not `active` is `degraded` or `entry-recovery-only` and MUST NOT be represented as unattended collaboration. A watcher that queues a request to its session MUST publish the `observed` receipt at that moment, so the ledger reflects delivery when it happens rather than when work finishes. Delivery and response windows are declared in the interaction policy; a binding MUST apply them when it reads the mailbox and report an expired interaction as `undelivered` or `delivered_unanswered` (both `timed_out`) rather than as pending. Expiry is derived on read and requires no additional publication. A response closes an interaction, so a binding MUST reject one that carries nothing: an outcome asserting progress (`accepted` or `revised`) requires a response that states what changed, and a participant with nothing to report uses `inconclusive`. Closing MUST remain recipient-only, and a binding MUST also provide a sender-side withdrawal so an obsolete request can be retired by the participant who published it; without one the only way to clear a stale request is to publish receipts as the recipient, which forges the delivery evidence the lifecycle exists to establish. A signal channel alone MUST NOT be represented as a live watcher or successful session wake. `polling` means a request is only available when the receiving participant next reads the binding; it MAY support durable asynchronous exchange, but MUST NOT be represented as unattended or self-starting collaboration. A request publication receipt confirms durable acceptance, not recipient attention, unless a delivery receipt from `host-dispatch`, `subscription`, or an active `signalled-poll` watcher is also returned. A project that expects one agent to begin collaboration after another agent requests it without a human prompt MUST select `host-dispatch`, `subscription`, or `signalled-poll` with an active watcher, and disclose retry, expiry, and unavailable-recipient behavior."
    },
    {
      "id": "AWP-COOP-035",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 174,
      "statement": "Publication, delivery, and answer are three independent facts and MUST NOT be inferred from one another. A managed binding MUST represent them with separately inspectable receipts:"
    },
    {
      "id": "AWP-COOP-036",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 180,
      "statement": "A delivery receipt MUST identify the interaction, observing actor, observation time, observed binding frontier, disposition (`observed`, `accepted`, or `refused`), and, for `accepted`, the response deadline. Mere observation MUST NOT commit the recipient to answer. Reading an assigned open interaction through a conforming `host-dispatch` or `subscription` host MUST atomically publish or return the existing `observed` receipt; a recipient explicitly accepting or refusing MUST publish the corresponding subsequent receipt. Repeated observation MUST return the same effective receipt and MUST NOT create another round."
    },
    {
      "id": "AWP-COOP-037",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 182,
      "statement": "If publication has no delivery receipt within the policy's `delivery_window_seconds`, the interaction is `undelivered`; the sender MUST report that it is waiting and MUST NOT infer refusal. If an accepted delivery has no terminal answer by its response deadline, the interaction is `delivered_unanswered` and MUST resolve to `timed_out` under the effective loop policy. These states are derived from the binding's declared `clock_authority` and MUST NOT depend on unsynchronized participant wall clocks. If the binding is unavailable, the participant MUST disclose `AWP-COORD-LEDGER-UNAVAILABLE`, enter snapshot-only or unavailable mode, and make no active COOP claim. A participant ending gracefully while responsible for an accepted open interaction SHOULD publish `refused` or a terminal response; a crash MUST be handled by the deadline and recoverable pending rules rather than relying on a final event from the crashed participant."
    },
    {
      "id": "AWP-COOP-038",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 184,
      "statement": "AWP specifies the project rendezvous identity, interaction and receipt semantics, failure states, and required diagnostics. The host specifies when a session receives a turn, any optional wake or notification mechanism, actor-to-principal binding, enforcement of budgets and authority, and whether the session may act on a received request. A host adapter SHOULD expose two logical operations\u2014deliver an interaction to a named session and return the resulting delivery receipt\u2014but MAY implement them through MCP, a plug-in, a native API, or another host facility. These are host bindings, not additional project transports. With `polling`, worst-case delivery latency is unbounded and MUST be disclosed."
    },
    {
      "id": "AWP-COOP-039",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 186,
      "statement": "An AWP-enabled host that supports managed collaboration MUST perform a bounded entry-recovery check before guarded work whenever a session starts, resumes, or enters a project without a live watcher handoff. The check MUST read the authoritative binding for open requests addressed to the session's actor and MUST correlate any current doorbell signal by binding identity, event identifier, and frontier before treating it as a wake hint. A missed, coalesced, stale, or absent doorbell MUST NOT hide a durably published interaction from the session's first project-entry turn. The entry check MUST be read-only until the session or host explicitly publishes the applicable observation, acceptance, refusal, or response receipt. The bounded coordination result SHOULD contain only the read state, binding identity, frontier, and bounded open-item summaries; it MUST NOT consume the entry budget with a full binding descriptor or unbounded mailbox history. If the binding cannot be read or verified, the host MUST disclose `AWP-COORD-LEDGER-UNAVAILABLE`, mark the entry result incomplete, and MUST NOT claim that delivery occurred or that guarded re-entry is complete. If the host cannot supply the session's actor identity, it MUST disclose `AWP-COORD-ACTOR-REQUIRED`, mark the entry result incomplete, and MUST NOT silently skip the entry check or claim unattended delivery. A budget-limited re-entry view MUST retain the coordination status and any bounded open-item summary even when larger context is omitted. This entry-recovery check is the durable safety path; a live doorbell watcher or host-dispatch binding remains the latency path and MUST disclose its liveness and retry limits."
    },
    {
      "id": "AWP-COOP-040",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 190,
      "statement": "`local-coop2-rendezvous-v1` is an experimental project-local binding profile. It uses one shared transactional event ledger to publish participant entry, discover available peers, and publish or retrieve a bounded interaction request, delivery receipt, and response by durable interaction identifier. It publishes separate `observed`, `accepted`, and `refused` delivery receipts, and rejects a response that lacks an accepted receipt or exceeds the declared response window. A participant uses the project and binding identity to find the ledger; it does not need an exchanged consultation-document path for a later request or reply. Its reported reach is `configured-unverified` until at least two distinct participant entries name the same project, workstate, and store identity; it reports `shared` only with those retained entry receipts as handshake evidence. The profile also writes `local-filesystem-doorbell-v1`, an atomically replaced, content-free project-local signal file after each interaction event. The signal identifies the authoritative binding, event, and frontier; it coalesces to the latest event, so a watcher MUST refresh the ledger rather than treat the file as a queue. An implementation MAY additionally create a local Git ref under `refs/awp/signal/` for the already-published event, with the event identifier encoded in the ref name and the current `HEAD` as target. That ref is a content-free local hint only: its creation MUST NOT precede ledger publication, it MUST NOT be treated as a queue or authoritative event store, and no remote push is implied. `codex-local-queue-watcher-v1` is one experimental same-host adapter: it polls the authoritative ledger, persists a bounded recent-event cursor with at-least-once notification semantics, and queues a bounded inbox-check turn through a trusted local Codex app-server endpoint. It sends only event and interaction identifiers, never peer message content. Its delivery mode is `signalled-poll`: it can support unattended collaboration only when the watcher and its host queue endpoint are actually active for that participant. The profile also writes `local-filesystem-heartbeat-v1`: each watcher atomically replaces its own per-actor heartbeat file on every poll, and the binding derives that actor's liveness from the file's age against a declared time-to-live (`active`, `stale`) or its absence (`none`); a heartbeat whose identity does not match the binding is `unverified`. Participants declare an observation mode at join (`watcher` or `on-entry-only`), but the declaration earns nothing: reach is computed from observed liveness only. The binding reports `mailbox_reach` (shared once two participants register) and a per-direction `signal_reach` matrix (`reachable`, `degraded`, `entry-recovery-only`). `local-git-ref-doorbell-v1` is bounded: after each publication the `refs/awp/signal/` namespace is pruned to the ledger's most recent events, and an update that fails on a stale Git lock older than a declared threshold removes the lock and retries once, disclosing the recovery; a fresh lock is respected. `codex-local-queue-watcher-v1` publishes the heartbeat and the `observed` receipt as it queues each request. A participant entering the project declares its observation mode through the re-entry tool's explicit registration flag; the read-only entry check itself never publishes. A participant whose watcher is not `active` MUST rely on the entry-recovery check for delivery and MUST NOT be presented as woken by the doorbell. A filesystem doorbell serves only participants with access to that filesystem; a cross-host signal channel remains necessary otherwise. The profile records participant and budget declarations, repeat-safe entry and request publication, and receipts, but does not authenticate actors, enforce host budgets, provide semantic selector analysis, supply a cross-host signal channel, or claim complete COOP-2 conformance. A binding selecting this profile MUST disclose those limitations."
    },
    {
      "id": "AWP-COOP-041",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 192,
      "statement": "The `codex-local-queue-watcher-v1` cursor MUST be protected by a recoverable host lock or equivalent atomic claim spanning cursor read, event claim, queue submission, and cursor persistence. Concurrent watchers and restarts MUST NOT queue one event identifier more than once; first startup MUST mark historical responses seen while still queuing current open requests."
    },
    {
      "id": "AWP-COOP-042",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 194,
      "statement": "The local Codex watcher MUST bound queue submission with a timeout and catch endpoint, process, and timeout failures. It MUST record an unavailable delivery state, retain the unclaimed event for retry, and continue with bounded backoff rather than exiting silently or holding the claim lock indefinitely."
    },
    {
      "id": "AWP-COOP-043",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 198,
      "statement": "`COOP-2` extends `COOP-1` work coordination with semantic awareness and integration assurance. It is also the first contract that may enable managed, directly inter-agent collaboration under Section 5's explicit authorization and budget. It MAY require a database, broker, registry, subscription system, or another service-backed binding, but neither a storage technology nor consultation alone supplies `COOP-2` semantics."
    },
    {
      "id": "AWP-COOP-044",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 200,
      "statement": "A `COOP-2` binding MUST maintain a stable semantic registry; resolve comparable selectors against pinned state revisions; compare declared scope, observed scope, and relied-upon reads; preserve `unknown` when relation evidence is ambiguous; and require acknowledgement or blocking under the effective policy. It MUST bind interface contracts, typed preconditions, verification results, staleness, change-set readiness, and integration results so that a stale or unsatisfied dependency cannot silently become integration-ready."
    },
    {
      "id": "AWP-COOP-045",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 202,
      "statement": "A `COOP-2` claim MUST declare its semantic-analysis coverage, selector and scope model, integration policy, tested participant count, and the failure behavior for unavailable or ambiguous semantic evidence. It MUST NOT infer protected external mutation, authentication, fencing, cross-host availability, or scalability from this claim."
    },
    {
      "id": "AWP-COOP-046",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 204,
      "statement": "A registry, selector analyzer, verification evaluator, or integration-readiness evaluator alone MUST NOT claim `COOP-2`; the contract applies to the composed participant, binding, semantic registry, analyzer, readiness evaluator, checkpoint, and recovery behavior."
    },
    {
      "id": "AWP-COOP-047",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 208,
      "statement": "`COOP-3` extends `COOP-2` with authenticated protected mutation and a declared scalable operating envelope. It MAY require a database, broker, sharded registry, protected mutation gateway, or another service-backed binding."
    },
    {
      "id": "AWP-COOP-048",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 210,
      "statement": "For guarded mutation, a `COOP-3` binding MUST authenticate actors to principals and use protected optimistic-concurrency or lease operations with epochs and fencing tokens. It MUST reject stale owners at the protected mutation path; advisory metadata or an unprotected lock file is insufficient. Its policy MUST define retry bounds, lease duration, clock authority, deadlock and starvation behavior, cancellation consequences, and human or organizational arbitration."
    },
    {
      "id": "AWP-COOP-049",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 212,
      "statement": "A `COOP-3` claim MUST declare its tested participant count, scope distribution, latency and throughput measurements, failure behavior, retention policy, trust boundary, protected mutation paths, and the guarantees retained during restart, partition, duplicate delivery, and concurrent capsule projection. It MUST include fault evidence for stale-owner rejection, event loss or retention gaps, projector races, binding-identity disagreement, and recovery after interruption. It MUST NOT infer scale, availability, semantic accuracy, or enforcement from a storage technology alone."
    },
    {
      "id": "AWP-COOP-050",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 216,
      "statement": "`coop3-a2a-v1` is a named optional COOP-3 binding profile for participants that communicate across runtimes, hosts, or organizational boundaries through the Agent2Agent (A2A) protocol. A2A is the profile's communications and execution control plane; it is not the authoritative coordination state or a substitute for protected mutation enforcement. An A2A task accepted, updated, completed, failed, cancelled, or resumed state MUST NOT by itself be interpreted as an AWP intent decision, lease grant, fenced mutation, checkpoint, integration result, or authority grant."
    },
    {
      "id": "AWP-COOP-051",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 218,
      "statement": "A binding claiming `transport.profile: coop3-a2a-v1` MUST declare the supported A2A protocol version and interfaces, the authenticated mapping from A2A peer identity to AWP actor and accountable principal, its task-to-AWP-operation correlation and idempotency rule, its authoritative coordination-store identity, and its protected mutation gateway. It MUST carry an immutable AWP operation identifier and the relevant workstate and binding identity in every coordination request. The binding MUST durably record the resulting AWP event or return a stable rejection before it acknowledges the operation as accepted to a participant."
    },
    {
      "id": "AWP-COOP-052",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 220,
      "statement": "The profile MAY use A2A tasks, messages, artifacts, or data parts to carry typed AWP coordination requests and receipts. At minimum it MUST support carrying a request and response for participant entry or renewal, guarded intent announcement, guarded decision or conflict result, checkpoint or handoff publication, and terminal completion or withdrawal. A retry, reconnect, duplicate delivery, or a task routed to another A2A endpoint MUST resolve through the same AWP operation identifier; it MUST return the prior receipt or a stable conflict or rejection, and MUST NOT create a second lease, intent, fencing generation, or protected mutation."
    },
    {
      "id": "AWP-COOP-053",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 222,
      "statement": "The authoritative COOP-3 store and protected mutation gateway MUST enforce the actor/principal authorization, expected binding epoch and frontier or revision, protected scope, and current fencing token independently of A2A task state. The gateway MUST reject a stale, unauthenticated, or mismatched request even when A2A reports successful delivery. A binding MUST disclose A2A reachability, authentication failure, transport retry, and store or gateway availability separately; it MUST fail closed for protected mutation when any required enforcement check is unavailable."
    },
    {
      "id": "AWP-COOP-054",
      "source": "spec/drafts/0.8.0/cooperation-contracts.md",
      "line": 243,
      "statement": "The checkpoint step SHOULD use the selected canonical workstate projector. A verified `no_change` receipt is sufficient when no semantic state changed; an incomplete or stale projection is not."
    }
  ]
}
```

---

## Core schema — `schemas/awp-core-0.8.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:core:0.8.0",
  "title": "AWP Core 0.8",
  "description": "Structural schema for AWP 0.8 manifests, event envelopes, snapshots, actors, authority declarations, and Core records.",
  "oneOf": [
    { "$ref": "#/$defs/manifest" },
    { "$ref": "#/$defs/event" },
    { "$ref": "#/$defs/snapshot" },
    { "$ref": "#/$defs/actor" },
    { "$ref": "#/$defs/authority" },
    { "$ref": "#/$defs/coreRecord" }
  ],
  "$defs": {
    "identifier": {
      "type": "string",
      "minLength": 1,
      "pattern": "^\\S+$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "semver": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:-[0-9A-Za-z.-]+)?$"
    },
    "referenceArray": {
      "type": "array",
      "items": { "$ref": "#/$defs/identifier" },
      "uniqueItems": true
    },
    "moduleDeclaration": {
      "type": "object",
      "required": ["id", "version", "required"],
      "properties": {
        "id": { "type": "string", "format": "uri" },
        "version": { "$ref": "#/$defs/semver" },
        "required": { "type": "boolean" },
        "schema": { "type": "string", "minLength": 1 },
        "representation": {
          "type": "object",
          "required": ["kind"],
          "properties": {
            "kind": { "enum": ["project-path", "capsule-section", "remote", "events-only"] }
          },
          "additionalProperties": true
        },
        "capabilities": {
          "type": "array",
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true
        },
        "configuration": { "type": "object" }
      },
      "additionalProperties": true
    },
    "manifest": {
      "type": "object",
      "required": [
        "awp_version",
        "workstate_id",
        "title",
        "created_at",
        "created_by",
        "modules",
        "representations"
      ],
      "properties": {
        "awp_version": { "type": "string", "pattern": "^0\\.8\\.[0-9]+$" },
        "workstate_id": { "$ref": "#/$defs/identifier" },
        "title": { "type": "string", "minLength": 1 },
        "created_at": { "$ref": "#/$defs/timestamp" },
        "created_by": { "$ref": "#/$defs/identifier" },
        "modules": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/moduleDeclaration" },
          "contains": {
            "type": "object",
            "required": ["id", "version", "required"],
            "properties": {
              "id": { "const": "urn:awp:core" },
              "version": { "type": "string", "pattern": "^0\\.8\\.[0-9]+$" },
              "required": { "const": true }
            }
          },
          "minContains": 1,
          "maxContains": 1
        },
        "representations": {
          "type": "object",
          "minProperties": 1,
          "additionalProperties": true
        },
        "module_data": {
          "type": "object",
          "propertyNames": { "format": "uri" },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "event": {
      "type": "object",
      "required": [
        "event_schema_version",
        "module",
        "kind",
        "event_id",
        "workstate_id",
        "parents",
        "occurred_at",
        "actor",
        "payload"
      ],
      "properties": {
        "event_schema_version": { "const": "0.2" },
        "module": { "type": "string", "format": "uri" },
        "kind": { "type": "string", "minLength": 1 },
        "event_id": { "$ref": "#/$defs/identifier" },
        "workstate_id": { "$ref": "#/$defs/identifier" },
        "parents": { "$ref": "#/$defs/referenceArray" },
        "occurred_at": { "$ref": "#/$defs/timestamp" },
        "recorded_at": { "$ref": "#/$defs/timestamp" },
        "actor": { "$ref": "#/$defs/identifier" },
        "payload": { "type": "object" },
        "extensions": { "type": "object" }
      },
      "additionalProperties": true
    },
    "actor": {
      "type": "object",
      "required": ["id", "type"],
      "properties": {
        "id": { "$ref": "#/$defs/identifier" },
        "type": { "enum": ["human", "agent", "model", "service", "automation", "organization", "unknown"] },
        "display_name": { "type": "string", "minLength": 1 },
        "authenticated": { "type": "boolean" }
      },
      "additionalProperties": true
    },
    "authority": {
      "type": "object",
      "required": ["authority_id", "granted_by", "grantee", "actions", "resources", "requires_confirmation"],
      "properties": {
        "authority_id": { "$ref": "#/$defs/identifier" },
        "granted_by": { "$ref": "#/$defs/identifier" },
        "grantee": { "$ref": "#/$defs/identifier" },
        "actions": { "type": "array", "items": { "type": "string", "minLength": 1 } },
        "resources": { "type": "array", "items": { "type": "string", "minLength": 1 } },
        "requires_confirmation": { "type": "boolean" },
        "expires_at": { "$ref": "#/$defs/timestamp" }
      },
      "additionalProperties": true
    },
    "coreRecord": {
      "type": "object",
      "required": ["id", "type"],
      "properties": {
        "id": { "$ref": "#/$defs/identifier" },
        "revision": { "type": "integer", "minimum": 1 },
        "type": {
          "enum": [
            "goal",
            "constraint",
            "claim",
            "evidence",
            "decision",
            "plan",
            "task",
            "question",
            "consultation",
            "artifact",
            "execution",
            "change",
            "risk",
            "checkpoint",
            "session"
          ]
        },
        "modules": {
          "type": "object",
          "propertyNames": { "format": "uri" },
          "additionalProperties": true
        }
      },
      "allOf": [
        {
          "if": { "properties": { "type": { "const": "goal" } }, "required": ["type"] },
          "then": {
            "required": ["statement", "status"],
            "properties": {
              "statement": { "type": "string", "minLength": 1 },
              "status": { "enum": ["proposed", "active", "satisfied", "abandoned", "blocked", "superseded"] }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "constraint" } }, "required": ["type"] },
          "then": {
            "required": ["statement", "strength", "status"],
            "properties": {
              "statement": { "type": "string", "minLength": 1 },
              "strength": { "enum": ["required", "preferred", "advisory"] },
              "status": { "type": "string", "minLength": 1 }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "claim" } }, "required": ["type"] },
          "then": {
            "required": ["statement", "epistemic_status"],
            "properties": {
              "statement": { "type": "string", "minLength": 1 },
              "epistemic_status": { "enum": ["reported", "inferred", "observed", "verified", "disputed", "unknown", "stale", "refuted", "superseded"] },
              "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
              "evidence": { "$ref": "#/$defs/referenceArray" }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "evidence" } }, "required": ["type"] },
          "then": { "required": ["evidence_type"] }
        },
        {
          "if": { "properties": { "type": { "const": "decision" } }, "required": ["type"] },
          "then": {
            "required": ["question", "status"],
            "properties": {
              "question": { "type": "string", "minLength": 1 },
              "status": { "enum": ["proposed", "accepted", "rejected", "deferred", "reopened", "superseded"] }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "plan" } }, "required": ["type"] },
          "then": { "required": ["goal", "status", "steps"] }
        },
        {
          "if": { "properties": { "type": { "const": "task" } }, "required": ["type"] },
          "then": {
            "required": ["title", "status"],
            "properties": {
              "title": { "type": "string", "minLength": 1 },
              "status": { "enum": ["proposed", "ready", "in_progress", "input_required", "blocked", "completed", "failed", "cancelled", "superseded"] },
              "side_effect_class": { "enum": ["read_only", "local_write", "external_write", "third_party_api_call", "data_migration", "communication", "financial", "security_sensitive", "destructive", "unknown"] }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "question" } }, "required": ["type"] },
          "then": {
            "required": ["text", "status"],
            "properties": {
              "text": { "type": "string", "minLength": 1 },
              "status": { "enum": ["open", "answered", "withdrawn", "superseded"] }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "consultation" } }, "required": ["type"] },
          "then": {
            "required": ["question", "status", "requested_action", "context", "read_first"],
            "properties": {
              "question": { "type": "string", "minLength": 1 },
              "status": { "enum": ["proposed", "open", "answered", "declined", "cancelled", "superseded"] },
              "requested_action": { "type": "string", "minLength": 1 },
              "context": { "type": "object", "minProperties": 1 },
              "read_first": { "$ref": "#/$defs/referenceArray" },
              "desired_output": { "type": "string", "minLength": 1 },
              "answer": { "type": "string", "minLength": 1 },
              "responded_by": { "$ref": "#/$defs/identifier" },
              "responded_at": { "$ref": "#/$defs/timestamp" },
              "response_evidence": { "$ref": "#/$defs/referenceArray" },
              "uncertainty": { "type": "string", "minLength": 1 },
              "disposition": { "type": "string", "minLength": 1 }
            },
            "allOf": [
              {
                "if": { "properties": { "status": { "const": "answered" } }, "required": ["status"] },
                "then": { "required": ["answer", "responded_by", "responded_at"] }
              },
              {
                "if": { "properties": { "status": { "enum": ["declined", "cancelled"] } }, "required": ["status"] },
                "then": { "required": ["disposition"] }
              }
            ]
          }
        },
        {
          "if": { "properties": { "type": { "const": "artifact" } }, "required": ["type"] },
          "then": { "required": ["name"] }
        },
        {
          "if": { "properties": { "type": { "const": "execution" } }, "required": ["type"] },
          "then": { "required": ["operation", "status"] }
        },
        {
          "if": { "properties": { "type": { "const": "change" } }, "required": ["type"] },
          "then": { "required": ["summary", "artifacts"] }
        },
        {
          "if": { "properties": { "type": { "const": "risk" } }, "required": ["type"] },
          "then": { "required": ["statement", "status"] }
        },
        {
          "if": { "properties": { "type": { "const": "checkpoint" } }, "required": ["type"] },
          "then": {
            "required": ["frontier", "created_at", "summary", "recommended_next_action", "resumption_level"],
            "properties": {
              "frontier": { "$ref": "#/$defs/referenceArray" },
              "created_at": { "$ref": "#/$defs/timestamp" },
              "summary": { "type": "string", "minLength": 1 },
              "recommended_next_action": {
                "type": "object",
                "required": ["action", "requires_authority"],
                "properties": {
                  "action": { "type": "string", "minLength": 1 },
                  "requires_authority": { "type": "boolean" }
                },
                "additionalProperties": true
              },
              "resumption_level": { "enum": ["semantic", "operational", "exact"] }
            }
          }
        },
        {
          "if": { "properties": { "type": { "const": "session" } }, "required": ["type"] },
          "then": { "required": ["started_at", "participants"] }
        }
      ],
      "additionalProperties": true
    },
    "snapshot": {
      "type": "object",
      "required": ["awp_version", "workstate_id", "frontier", "generated_at", "records", "modules"],
      "properties": {
        "awp_version": { "type": "string", "pattern": "^0\\.8\\.[0-9]+$" },
        "workstate_id": { "$ref": "#/$defs/identifier" },
        "frontier": { "$ref": "#/$defs/referenceArray" },
        "generated_at": { "$ref": "#/$defs/timestamp" },
        "actors": {
          "type": "array",
          "items": { "$ref": "#/$defs/actor" }
        },
        "records": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": { "$ref": "#/$defs/coreRecord" }
          }
        },
        "modules": {
          "type": "object",
          "propertyNames": { "format": "uri" },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    }
  }
}
```

---

## Cooperation schema — `schemas/awp-cooperation-0.1.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:cooperation:0.1.0",
  "title": "AWP Cooperation Contracts 0.1",
  "oneOf": [
    {"$ref": "#/$defs/binding"},
    {"$ref": "#/$defs/policy"},
    {"$ref": "#/$defs/interaction"},
    {"$ref": "#/$defs/deliveryReceipt"},
    {"$ref": "#/$defs/participantLease"}
  ],
  "$defs": {
    "id": {"type": "string", "minLength": 1, "pattern": "^\\S+$"},
    "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
    "binding": {
      "type": "object",
      "required": ["type", "module", "contract", "claim_state", "capabilities", "operational_mode", "identity", "observation", "atomicity_mechanism", "storage_assumptions", "subprotocols", "limitations"],
      "properties": {
        "type": {"const": "cooperation_binding"},
        "module": {"const": "urn:awp:cooperation"},
        "contract": {"enum": ["COOP-1", "COOP-2", "COOP-3"]},
        "claim_state": {"enum": ["selected", "partial", "conformant"]},
        "capabilities": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}},
        "operational_mode": {"enum": ["portable", "ledger-backed-advisory", "ledger-bound", "snapshot-only", "degraded", "unavailable"]},
        "identity": {
          "type": "object",
          "required": ["workstate_id", "project_id", "store_id", "scope_model", "binding_epoch"],
          "properties": {
            "workstate_id": {"$ref": "#/$defs/id"},
            "project_id": {"$ref": "#/$defs/id"},
            "store_id": {"$ref": "#/$defs/id"},
            "scope_model": {"$ref": "#/$defs/id"},
            "binding_epoch": {"type": "integer", "minimum": 1}
          },
          "additionalProperties": true
        },
        "observation": {
          "type": "object",
          "required": ["observed_at", "operational_reach", "frontier"],
          "properties": {
            "observed_at": {"type": "string", "format": "date-time"},
            "operational_reach": {"enum": ["shared", "worktree-local", "configured-unverified", "degraded", "snapshot-only", "unavailable"]},
            "frontier": {"type": "array", "items": {"$ref": "#/$defs/id"}, "uniqueItems": true},
            "participant_watchers": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["actor", "watcher_liveness"],
                "properties": {
                  "actor": {"$ref": "#/$defs/id"},
                  "watcher_liveness": {"enum": ["active", "stale", "none", "unverified"]},
                  "profile": {"type": "string", "minLength": 1}
                },
                "additionalProperties": true
              }
            },
            "signal_reach": {
              "type": "object",
              "description": "per ordered sender->recipient pair; mailbox reach does not imply signal reach",
              "additionalProperties": {
                "type": "object",
                "required": ["signal_reach"],
                "properties": {
                  "signal_reach": {"enum": ["reachable", "degraded", "entry-recovery-only"]},
                  "recipient_watcher": {"enum": ["active", "stale", "none", "unverified"]}
                },
                "additionalProperties": true
              }
            }
          },
          "additionalProperties": true
        },
        "atomicity_mechanism": {"type": "string", "minLength": 1},
        "storage_assumptions": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
        "participant_discovery": {"$ref": "#/$defs/participantDiscovery"},
        "interaction_transport": {"$ref": "#/$defs/interactionTransport"},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "transport": {"$ref": "#/$defs/transportDescriptor"},
        "subprotocols": {
          "type": "object",
          "required": ["work", "consultation"],
          "properties": {
            "work": {"$ref": "#/$defs/workSubprotocolClaim"},
            "consultation": {"$ref": "#/$defs/consultationSubprotocolClaim"}
          },
          "additionalProperties": true
        },
        "tested_envelope": {"$ref": "#/$defs/testedEnvelope"}
      },
      "allOf": [
        {
          "if": {
            "properties": {"transport": {"properties": {"profile": {"const": "coop3-a2a-v1"}}, "required": ["profile"]}},
            "required": ["transport"]
          },
          "then": {
            "properties": {
              "contract": {"const": "COOP-3"},
              "capabilities": {"contains": {"const": "a2a-control-plane"}},
              "transport": {"$ref": "#/$defs/a2aTransportDescriptor"}
            },
            "required": ["contract", "capabilities", "transport"]
          }
        },
        {
          "if": {
            "properties": {"subprotocols": {"properties": {"consultation": {"properties": {"mode": {"const": "managed"}}, "required": ["mode"]}}, "required": ["consultation"]}},
            "required": ["subprotocols"]
          },
          "then": {
            "properties": {
              "contract": {"enum": ["COOP-2", "COOP-3"]},
              "capabilities": {"contains": {"const": "bounded-interactions"}}
            },
            "required": ["contract", "capabilities"]
          }
        },
        {
          "if": {
            "properties": {"contract": {"const": "COOP-1"}, "subprotocols": {"properties": {"consultation": {"properties": {"enabled": {"const": true}}, "required": ["enabled"]}}, "required": ["consultation"]}},
            "required": ["contract", "subprotocols"]
          },
          "then": {
            "properties": {"subprotocols": {"properties": {"consultation": {"properties": {"mode": {"const": "user-mediated"}}, "required": ["mode"]}}}}
          }
        },
        {
          "if": {"properties": {"contract": {"const": "COOP-1"}, "claim_state": {"const": "conformant"}}, "required": ["contract", "claim_state"]},
          "then": {
            "properties": {
              "capabilities": {
                "allOf": [
                  {"contains": {"const": "deterministic-coordination-projector"}},
                  {"contains": {"const": "coordination-awareness"}},
                  {"contains": {"const": "guarded-scope-announce-check"}},
                  {"contains": {"const": "participant-leases"}},
                  {"contains": {"const": "checkpoint-handoff"}}
                ]
              },
              "subprotocols": {
                "properties": {
                  "work": {
                    "properties": {"enabled": {"const": true}, "claim_state": {"const": "conformant"}},
                    "required": ["enabled", "claim_state"]
                  }
                },
                "required": ["work"]
              }
            }
          }
        },
        {
          "if": {"properties": {"contract": {"const": "COOP-2"}, "claim_state": {"const": "conformant"}}, "required": ["contract", "claim_state"]},
          "then": {
            "properties": {
              "capabilities": {
                "allOf": [
                  {"contains": {"const": "deterministic-coordination-projector"}},
                  {"contains": {"const": "coordination-awareness"}},
                  {"contains": {"const": "guarded-scope-announce-check"}},
                  {"contains": {"const": "participant-leases"}},
                  {"contains": {"const": "checkpoint-handoff"}},
                  {"contains": {"const": "semantic-awareness"}},
                  {"contains": {"const": "integration-assurance"}}
                ]
              },
              "subprotocols": {
                "properties": {
                  "work": {
                    "properties": {"enabled": {"const": true}, "claim_state": {"const": "conformant"}},
                    "required": ["enabled", "claim_state"]
                  }
                },
                "required": ["work"]
              }
            }
          }
        },
        {
          "if": {"properties": {"contract": {"const": "COOP-3"}, "claim_state": {"const": "conformant"}}, "required": ["contract", "claim_state"]},
          "then": {
            "required": ["tested_envelope"],
            "properties": {
              "capabilities": {
                "allOf": [
                  {"contains": {"const": "deterministic-coordination-projector"}},
                  {"contains": {"const": "coordination-awareness"}},
                  {"contains": {"const": "guarded-scope-announce-check"}},
                  {"contains": {"const": "participant-leases"}},
                  {"contains": {"const": "checkpoint-handoff"}},
                  {"contains": {"const": "semantic-awareness"}},
                  {"contains": {"const": "integration-assurance"}},
                  {"contains": {"const": "protected-mutation-enforcement"}},
                  {"contains": {"const": "scalable-binding"}}
                ]
              },
              "subprotocols": {
                "properties": {
                  "work": {
                    "properties": {"enabled": {"const": true}, "claim_state": {"const": "conformant"}},
                    "required": ["enabled", "claim_state"]
                  }
                },
                "required": ["work"]
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "subprotocols": {
                "properties": {
                  "consultation": {
                    "properties": {"enabled": {"const": true}, "claim_state": {"const": "conformant"}},
                    "required": ["enabled", "claim_state"]
                  }
                },
                "required": ["consultation"]
              }
            },
            "required": ["subprotocols"]
          },
          "then": {
            "properties": {
              "capabilities": {"contains": {"const": "bounded-interactions"}},
              "subprotocols": {
                "properties": {
                  "consultation": {
                    "properties": {
                      "policy": {
                        "properties": {"enforcement": {"enum": ["enforced", "delegated"]}},
                        "required": ["enforcement"]
                      }
                    },
                    "required": ["policy"]
                  }
                }
              }
            }
          }
        }
      ],
      "additionalProperties": true
    },
    "transportDescriptor": {
      "type": "object",
      "required": ["profile", "role"],
      "properties": {
        "profile": {"$ref": "#/$defs/id"},
        "role": {"enum": ["communications-control-plane", "event-transport", "hybrid"]}
      },
      "additionalProperties": true
    },
    "participantDiscovery": {
      "type": "object",
      "required": ["profile", "identity_key", "publication", "verification"],
      "properties": {
        "profile": {"$ref": "#/$defs/id"},
        "identity_key": {"const": "project-workstate-binding"},
        "publication": {"type": "string", "minLength": 1},
        "verification": {"type": "string", "minLength": 1}
      },
      "additionalProperties": true
    },
    "interactionTransport": {
      "type": "object",
      "required": ["profile", "publication", "retrieval", "idempotency", "delivery_mode"],
      "properties": {
        "profile": {"$ref": "#/$defs/id"},
        "publication": {"type": "string", "minLength": 1},
        "retrieval": {"type": "string", "minLength": 1},
        "idempotency": {"type": "string", "minLength": 1},
        "delivery_mode": {"enum": ["host-dispatch", "subscription", "signalled-poll", "polling", "unavailable"]}
      },
      "additionalProperties": true
    },
    "a2aTransportDescriptor": {
      "type": "object",
      "required": ["profile", "role", "a2a_protocol_version", "supported_interfaces", "actor_principal_mapping", "idempotency", "authoritative_store", "protected_mutation_gateway"],
      "properties": {
        "profile": {"const": "coop3-a2a-v1"},
        "role": {"const": "communications-control-plane"},
        "a2a_protocol_version": {"type": "string", "minLength": 1},
        "supported_interfaces": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}, "uniqueItems": true},
        "actor_principal_mapping": {"type": "string", "minLength": 1},
        "idempotency": {"type": "string", "minLength": 1},
        "authoritative_store": {"$ref": "#/$defs/id"},
        "protected_mutation_gateway": {"$ref": "#/$defs/id"}
      },
      "additionalProperties": true
    },
    "workSubprotocolClaim": {
      "type": "object",
      "required": ["enabled"],
      "properties": {
        "enabled": {"type": "boolean"},
        "claim_state": {"enum": ["selected", "partial", "conformant"]}
      },
      "allOf": [{
        "if": {"properties": {"enabled": {"const": true}}, "required": ["enabled"]},
        "then": {"required": ["claim_state"]}
      }],
      "additionalProperties": true
    },
    "consultationPolicy": {
      "type": "object",
      "required": ["policy_id", "enforcement"],
      "properties": {
        "policy_id": {"$ref": "#/$defs/id"},
        "enforcement": {"enum": ["enforced", "delegated", "not-implemented"]},
        "digest": {"$ref": "#/$defs/digest"}
      },
      "additionalProperties": true
    },
    "consultationSubprotocolClaim": {
      "type": "object",
      "required": ["enabled"],
      "properties": {
        "enabled": {"type": "boolean"},
        "mode": {"enum": ["user-mediated", "managed"]},
        "claim_state": {"enum": ["selected", "partial", "conformant"]},
        "policy": {"$ref": "#/$defs/consultationPolicy"}
      },
      "allOf": [{
        "if": {"properties": {"enabled": {"const": true}}, "required": ["enabled"]},
        "then": {"required": ["mode", "claim_state", "policy"]}
      }],
      "additionalProperties": true
    },
    "testedEnvelope": {
      "type": "object",
      "required": ["max_concurrent_participants", "scope_distribution", "latency_measurements", "failure_behavior", "retention_policy", "protected_mutation_paths"],
      "properties": {
        "max_concurrent_participants": {"type": "integer", "minimum": 2},
        "scope_distribution": {"type": "string", "minLength": 1},
        "latency_measurements": {"type": "object"},
        "failure_behavior": {"type": "object"},
        "retention_policy": {"type": "string", "minLength": 1},
        "protected_mutation_paths": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}}
      },
      "additionalProperties": true
    },
    "policy": {
      "type": "object",
      "required": ["policy_id", "max_rounds", "max_participant_responses", "progress_requirement", "repeat_key_algorithm", "on_limit", "continuation_authority"],
      "properties": {
        "policy_id": {"$ref": "#/$defs/id"},
        "max_rounds": {"type": "integer", "minimum": 1},
        "max_participant_responses": {"type": "integer", "minimum": 1},
        "max_tool_calls": {"type": "integer", "minimum": 0},
        "max_context_tokens_per_request": {"type": "integer", "minimum": 1},
        "max_output_tokens_per_response": {"type": "integer", "minimum": 1},
        "max_total_output_tokens": {"type": "integer", "minimum": 1},
        "delivery_window_seconds": {"type": "integer", "minimum": 1},
        "clock_authority": {"type": "string", "minLength": 1},
        "progress_requirement": {"const": "new_artifact_evidence_decision_or_disagreement"},
        "repeat_key_algorithm": {"const": "rfc8785-sha256-v1"},
        "on_limit": {"enum": ["inconclusive", "escalated", "inconclusive_or_escalated"]},
        "continuation_authority": {"$ref": "#/$defs/id"},
        "required_extensions": {"type": "array", "items": {"type": "string"}}
      },
      "additionalProperties": true
    },
    "interaction": {
      "type": "object",
      "required": ["type", "module", "interaction_id", "workstate_id", "purpose", "subject", "participants", "decision_owner", "binding", "policy", "round", "repeat_basis", "repeat_key", "progress", "result"],
      "properties": {
        "type": {"const": "cooperation_interaction"},
        "module": {"const": "urn:awp:cooperation"},
        "interaction_id": {"$ref": "#/$defs/id"},
        "workstate_id": {"$ref": "#/$defs/id"},
        "purpose": {"enum": ["review", "critique", "alternative", "delegation", "decision", "synthesis"]},
        "subject": {"type": "object", "minProperties": 1},
        "participants": {"type": "array", "minItems": 2, "items": {"type": "object", "required": ["id", "role"], "properties": {"id": {"$ref": "#/$defs/id"}, "role": {"type": "string"}}, "additionalProperties": true}},
        "decision_owner": {"$ref": "#/$defs/id"},
        "binding": {"$ref": "#/$defs/binding"},
        "policy": {"type": "object", "required": ["policy_id", "digest", "definition"], "properties": {"policy_id": {"$ref": "#/$defs/id"}, "digest": {"$ref": "#/$defs/digest"}, "definition": {"$ref": "#/$defs/policy"}}, "additionalProperties": true},
        "authorization_ref": {"$ref": "#/$defs/id"},
        "budget_consumption": {"type": "object", "properties": {"context_tokens": {"type": "integer", "minimum": 0}, "output_tokens": {"type": "integer", "minimum": 0}, "tool_calls": {"type": "integer", "minimum": 0}, "measurement_state": {"enum": ["measured", "unavailable"]}}, "additionalProperties": true},
        "round": {"type": "integer", "minimum": 1},
        "repeat_basis": {"type": "object", "required": ["purpose", "subject", "context_frontier", "participant_set_digest", "policy_digest"], "properties": {"purpose": {"type": "string"}, "subject": {"type": "object"}, "context_frontier": {"type": "array", "items": {"$ref": "#/$defs/id"}}, "participant_set_digest": {"$ref": "#/$defs/digest"}, "policy_digest": {"$ref": "#/$defs/digest"}}, "additionalProperties": false},
        "repeat_key": {"$ref": "#/$defs/digest"},
        "progress": {"type": "object", "required": ["kind", "ref"], "properties": {"kind": {"enum": ["artifact", "evidence", "decision", "disagreement"]}, "ref": {"$ref": "#/$defs/id"}}, "additionalProperties": false},
        "result": {"type": "object", "required": ["outcome", "recorded_at"], "properties": {"outcome": {"enum": ["accepted", "revised", "inconclusive", "declined", "timed_out", "escalated"]}, "recorded_at": {"type": "string", "format": "date-time"}}, "additionalProperties": true}
      },
      "allOf": [
        {
          "if": {
            "properties": {"binding": {"properties": {"subprotocols": {"properties": {"consultation": {"properties": {"mode": {"const": "managed"}}, "required": ["mode"]}}, "required": ["consultation"]}}, "required": ["subprotocols"]}},
            "required": ["binding"]
          },
          "then": {
            "required": ["authorization_ref", "budget_consumption"],
            "properties": {
              "policy": {
                "properties": {
                  "definition": {
                    "required": ["max_context_tokens_per_request", "max_output_tokens_per_response", "max_total_output_tokens", "delivery_window_seconds", "clock_authority"]
                  }
                }
              }
            }
          }
        }
      ],
      "additionalProperties": true
    },
    "deliveryReceipt": {
      "type": "object",
      "required": ["type", "module", "interaction_id", "observing_actor", "observed_at", "binding_frontier", "disposition"],
      "properties": {
        "type": {"const": "cooperation_delivery_receipt"},
        "module": {"const": "urn:awp:cooperation"},
        "interaction_id": {"$ref": "#/$defs/id"},
        "observing_actor": {"$ref": "#/$defs/id"},
        "observed_at": {"type": "string", "format": "date-time"},
        "binding_frontier": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/id"}, "uniqueItems": true},
        "disposition": {"enum": ["observed", "accepted", "refused"]},
        "response_deadline": {"type": "string", "format": "date-time"}
      },
      "allOf": [{
        "if": {"properties": {"disposition": {"const": "accepted"}}, "required": ["disposition"]},
        "then": {"required": ["response_deadline"]}
      }],
      "additionalProperties": true
    },
    "handoffReceipt": {"type": "object", "required": ["path", "digest", "verified_at"], "properties": {"path": {"type": "string", "minLength": 1}, "digest": {"$ref": "#/$defs/digest"}, "verified_at": {"type": "string", "format": "date-time"}}, "additionalProperties": false},
    "checkpointReceipt": {"type": "object", "required": ["path", "digest", "generated_digest", "frontier"], "properties": {"path": {"type": "string", "minLength": 1}, "digest": {"$ref": "#/$defs/digest"}, "generated_digest": {"$ref": "#/$defs/digest"}, "frontier": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/id"}, "uniqueItems": true}}, "additionalProperties": false},
    "participantLease": {
      "type": "object",
      "required": ["id", "type", "module", "revision", "status", "actor", "project_id", "execution_location", "base_revision", "entered_at", "renewed_at", "expires_at", "ttl_seconds"],
      "properties": {
        "id": {"$ref": "#/$defs/id"},
        "type": {"const": "cooperation_lease"},
        "module": {"const": "urn:awp:cooperation"},
        "revision": {"type": "integer", "minimum": 1},
        "status": {"enum": ["active", "released", "expired"]},
        "actor": {"$ref": "#/$defs/id"},
        "project_id": {"$ref": "#/$defs/id"},
        "execution_location": {"type": "string", "minLength": 1},
        "base_revision": {"$ref": "#/$defs/id"},
        "intended_scopes": {"type": "array", "items": {"type": "string"}},
        "entered_at": {"type": "string", "format": "date-time"},
        "renewed_at": {"type": "string", "format": "date-time"},
        "expires_at": {"type": "string", "format": "date-time"},
        "ttl_seconds": {"type": "integer", "minimum": 1},
        "handoff_receipt": {"$ref": "#/$defs/handoffReceipt"}
      },
      "allOf": [{"if": {"properties": {"status": {"const": "released"}}, "required": ["status"]}, "then": {"required": ["handoff_receipt"]}}],
      "additionalProperties": true
    }
  }
}
```

---

## Capsule schema — `schemas/awp-capsule-0.5.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:capsule:0.5.0",
  "title": "AWP Capsule 0.5 metadata",
  "description": "Structural schema for the front matter of an AWP 0.8 project-scoped Markdown capsule.",
  "type": "object",
  "required": [
    "awp_version",
    "specification",
    "format",
    "discovery",
    "capsule_boundary",
    "workstate_id",
    "frontier",
    "generated_at",
    "generated_digest"
  ],
  "properties": {
    "awp_version": { "type": "string", "pattern": "^0\\.8\\.[0-9]+$" },
    "specification": { "type": "string", "minLength": 1, "pattern": "^\\S+$" },
    "format": { "const": "single-file-capsule" },
    "discovery": { "const": "project" },
    "capsule_boundary": { "type": "string", "pattern": "^[0-9a-f]{32,}$" },
    "workstate_id": { "type": "string", "minLength": 1, "pattern": "^\\S+$" },
    "frontier": {
      "type": "array",
      "items": { "type": "string", "minLength": 1, "pattern": "^\\S+$" },
      "uniqueItems": true
    },
    "checkpoint": { "type": "string", "minLength": 1, "pattern": "^\\S+$" },
    "generated_at": { "type": "string", "format": "date-time" },
    "generated_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" }
  },
  "additionalProperties": true
}
```

---

## Coordination schema — `schemas/awp-coordination-0.5.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:coordination:0.5.0",
  "title": "AWP Coordination 0.5",
  "description": "Structural schema for AWP Coordination 0.5 records and event envelopes.",
  "oneOf": [
    { "$ref": "#/$defs/coordinationRecord" },
    { "$ref": "#/$defs/coordinationEvent" }
  ],
  "$defs": {
    "identifier": {
      "type": "string",
      "minLength": 1,
      "pattern": "^\\S+$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "referenceArray": {
      "type": "array",
      "items": { "$ref": "#/$defs/identifier" },
      "uniqueItems": true
    },
    "pinnedReference": {
      "type": "string",
      "pattern": "^\\S+@[1-9][0-9]*$"
    },
    "pinnedReferenceArray": {
      "type": "array",
      "items": { "$ref": "#/$defs/pinnedReference" },
      "uniqueItems": true
    },
    "stateReference": {
      "type": "object",
      "required": ["revision"],
      "oneOf": [
        { "required": ["repository"] },
        { "required": ["state_space"] }
      ],
      "properties": {
        "repository": { "$ref": "#/$defs/identifier" },
        "state_space": { "$ref": "#/$defs/identifier" },
        "revision": { "$ref": "#/$defs/identifier" },
        "profile": { "$ref": "#/$defs/identifier" }
      },
      "additionalProperties": true
    },
    "executionLocation": {
      "type": "object",
      "required": ["kind", "location"],
      "properties": {
        "kind": { "enum": ["checkout", "worktree", "remote", "other"] },
        "location": { "type": "string", "minLength": 1 },
        "branch": { "type": "string", "minLength": 1 },
        "instance": { "$ref": "#/$defs/identifier" }
      },
      "additionalProperties": true
    },
    "selector": {
      "type": "object",
      "required": ["kind", "base_revision"],
      "oneOf": [
        { "required": ["repository"] },
        { "required": ["state_space"] }
      ],
      "properties": {
        "kind": {
          "enum": [
            "repository", "directory", "file", "symbol", "syntax_node",
            "configuration_key", "schema_object", "generated_output", "test", "fixture",
            "spatial_region", "model_element", "assembly", "document_region", "domain_object", "interface", "custom"
          ]
        },
        "repository": { "$ref": "#/$defs/identifier" },
        "state_space": { "$ref": "#/$defs/identifier" },
        "base_revision": { "$ref": "#/$defs/identifier" },
        "path": { "type": "string", "minLength": 1 },
        "symbol": { "type": "string", "minLength": 1 },
        "object_id": { "$ref": "#/$defs/identifier" },
        "profile": { "$ref": "#/$defs/identifier" }
      },
      "additionalProperties": true
    },
    "decisionPolicy": {
      "type": "object",
      "required": ["kind", "decides_revision"],
      "properties": {
        "kind": { "enum": ["unanimous", "threshold", "named_participants", "authorized_owner"] },
        "eligible_participants": { "$ref": "#/$defs/referenceArray" },
        "threshold": { "type": "integer", "minimum": 1 },
        "required_participants": { "$ref": "#/$defs/referenceArray" },
        "abstention": { "enum": ["counts_as_no", "reduces_eligible", "prohibited"] },
        "decides_revision": { "type": "integer", "minimum": 1 }
      },
      "allOf": [
        {
          "if": { "properties": { "kind": { "const": "threshold" } }, "required": ["kind"] },
          "then": { "required": ["eligible_participants", "threshold"] }
        },
        {
          "if": { "properties": { "kind": { "enum": ["unanimous", "named_participants"] } }, "required": ["kind"] },
          "then": { "required": ["eligible_participants"] }
        }
      ],
      "additionalProperties": true
    },
    "commonRecord": {
      "type": "object",
      "required": ["id", "type", "module", "revision", "status", "created_by", "created_at"],
      "properties": {
        "id": { "$ref": "#/$defs/identifier" },
        "type": {
          "enum": [
            "semantic_definition", "scope", "intent", "observed_scope", "overlap",
            "conflict", "negotiation", "arbitration", "commitment", "contract", "precondition",
            "precondition_result", "change_set", "verification_result", "dependency",
            "integration_plan", "integration_result", "presence", "lease"
          ]
        },
        "module": { "const": "urn:awp:coordination" },
        "revision": { "type": "integer", "minimum": 1 },
        "status": { "type": "string", "minLength": 1 },
        "created_by": { "$ref": "#/$defs/identifier" },
        "created_at": { "$ref": "#/$defs/timestamp" },
        "updated_at": { "$ref": "#/$defs/timestamp" }
      }
    },
    "coordinationRecord": {
      "allOf": [
        { "$ref": "#/$defs/commonRecord" },
        {
          "type": "object",
          "allOf": [
            {
              "if": { "properties": { "type": { "const": "semantic_definition" } }, "required": ["type"] },
              "then": {
                "required": ["kind", "name"],
                "properties": {
                  "kind": {
                    "enum": [
                      "interface", "behavior", "invariant", "state_field", "schema",
                      "error_semantics", "lifecycle", "compatibility_promise",
                      "performance_property", "security_property", "test_surface",
                      "deployment_surface", "other"
                    ]
                  },
                  "name": { "type": "string", "minLength": 1 },
                  "aliases": { "$ref": "#/$defs/referenceArray" },
                  "selectors": { "type": "array", "items": { "$ref": "#/$defs/selector" } }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "scope" } }, "required": ["type"] },
              "then": {
                "required": ["selector", "access"],
                "properties": {
                  "selector": { "$ref": "#/$defs/selector" },
                  "access": {
                    "enum": [
                      "observe", "read", "relied_upon_read", "write", "create", "delete",
                      "propose_change", "integrate", "verify"
                    ]
                  },
                  "semantic_targets": { "$ref": "#/$defs/pinnedReferenceArray" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "intent" } }, "required": ["type"] },
              "then": {
                "required": ["goal", "summary", "base", "declared_scopes"],
                "properties": {
                  "status": { "enum": ["proposed", "active", "waiting", "completed", "withdrawn", "abandoned", "superseded"] },
                  "goal": { "$ref": "#/$defs/identifier" },
                  "summary": { "type": "string", "minLength": 1 },
                  "base": { "$ref": "#/$defs/stateReference" },
                  "declared_scopes": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "expected_effects": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "preserves": { "$ref": "#/$defs/pinnedReferenceArray" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "observed_scope" } }, "required": ["type"] },
              "then": {
                "required": ["subject", "base_revision", "result_revision", "analyzer", "method", "outcome", "observed", "comparison"],
                "oneOf": [
                  { "required": ["repository"] },
                  { "required": ["state_space"] }
                ],
                "properties": {
                  "repository": { "$ref": "#/$defs/identifier" },
                  "state_space": { "$ref": "#/$defs/identifier" },
                  "status": { "enum": ["final", "superseded"] },
                  "subject": { "$ref": "#/$defs/pinnedReference" },
                  "outcome": { "enum": ["complete", "partial", "error"] },
                  "observed": { "$ref": "#/$defs/pinnedReferenceArray" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "overlap" } }, "required": ["type"] },
              "then": {
                "required": ["subjects", "classification", "basis", "policy_action"],
                "properties": {
                  "status": { "enum": ["open", "negotiating", "resolved", "escalated", "superseded"] },
                  "subjects": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "classification": { "enum": ["none", "informational", "compatible", "ordered", "negotiation_required", "blocking", "unknown"] },
                  "policy_action": { "enum": ["allow", "warn", "negotiate", "order", "block", "escalate"] }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "negotiation" } }, "required": ["type"] },
              "then": {
                "required": ["subject", "participants", "opening_proposal", "response_deadline", "decision_policy", "permitted_outcomes", "escalation_target"],
                "properties": {
                  "status": { "enum": ["open", "accepted", "rejected", "timed_out", "cancelled", "escalated"] },
                  "decision_policy": { "$ref": "#/$defs/decisionPolicy" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "arbitration" } }, "required": ["type"] },
              "then": {
                "required": ["subjects", "participants", "question", "alternatives", "decision_authority", "response_deadline", "blocked_scopes", "allowed_interim_work"],
                "properties": {
                  "status": { "enum": ["awaiting_user", "decided", "declined", "expired", "cancelled", "superseded"] },
                  "subjects": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "participants": { "$ref": "#/$defs/referenceArray" },
                  "question": { "type": "string", "minLength": 1 },
                  "alternatives": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                      "type": "object",
                      "required": ["id", "summary", "consequences", "reversible"],
                      "properties": {
                        "id": { "$ref": "#/$defs/identifier" },
                        "summary": { "type": "string", "minLength": 1 },
                        "consequences": { "type": "string", "minLength": 1 },
                        "reversible": { "type": "boolean" },
                        "risk": { "type": "string" }
                      },
                      "additionalProperties": true
                    }
                  },
                  "decision_authority": { "$ref": "#/$defs/identifier" },
                  "response_deadline": { "$ref": "#/$defs/timestamp" },
                  "blocked_scopes": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "allowed_interim_work": { "type": "array", "items": { "type": "string" } },
                  "evidence": { "$ref": "#/$defs/referenceArray" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "commitment" } }, "required": ["type"] },
              "then": {
                "required": ["debtor", "beneficiaries", "promised_condition", "discharge_condition", "violation_condition"],
                "properties": {
                  "status": { "enum": ["conditional", "active", "satisfied", "violated", "cancelled", "released", "superseded"] }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "contract" } }, "required": ["type"] },
              "then": {
                "required": ["owners", "producers", "consumers", "content", "decision_policy", "participant_adoption"],
                "properties": {
                  "status": { "enum": ["proposed", "negotiating", "accepted", "implemented", "verified", "superseded", "rejected", "withdrawn"] },
                  "decision_policy": { "$ref": "#/$defs/decisionPolicy" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "precondition" } }, "required": ["type"] },
              "then": {
                "required": ["kind", "on_false", "on_unknown"],
                "properties": {
                  "status": { "enum": ["active", "retired", "superseded"] },
                  "kind": { "enum": ["mechanical", "asserted"] },
                  "on_false": { "enum": ["warn", "block_ready", "stale", "escalate"] },
                  "on_unknown": { "enum": ["warn", "block_ready", "escalate"] }
                },
                "allOf": [
                  {
                    "if": { "properties": { "kind": { "const": "mechanical" } }, "required": ["kind"] },
                    "then": { "required": ["predicate", "subject", "evaluator_interface"] }
                  },
                  {
                    "if": { "properties": { "kind": { "const": "asserted" } }, "required": ["kind"] },
                    "then": { "required": ["statement", "asserting_actor", "epistemic_status"] }
                  }
                ]
              }
            },
            {
              "if": { "properties": { "type": { "const": "precondition_result" } }, "required": ["type"] },
              "then": {
                "required": ["precondition", "outcome", "evaluated_against", "depends_on", "evaluator"],
                "properties": {
                  "status": { "enum": ["final", "superseded"] },
                  "precondition": { "$ref": "#/$defs/pinnedReference" },
                  "outcome": { "enum": ["pass", "fail", "unknown", "error"] },
                  "depends_on": { "type": "array", "minItems": 1, "items": { "type": "object" } }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "change_set" } }, "required": ["type"] },
              "then": {
                "required": ["intent", "base", "artifacts", "declared_scopes", "preconditions", "effects"],
                "properties": {
                  "status": { "enum": ["proposed", "in_progress", "ready", "stale", "integrating", "integrated", "failed", "withdrawn", "superseded"] },
                  "intent": { "$ref": "#/$defs/pinnedReference" },
                  "base": { "$ref": "#/$defs/stateReference" },
                  "declared_scopes": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "preconditions": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "observed_scope": { "$ref": "#/$defs/pinnedReference" },
                  "verification": { "$ref": "#/$defs/pinnedReferenceArray" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "verification_result" } }, "required": ["type"] },
              "then": {
                "required": ["subjects", "base_revision", "result_revision", "procedure", "environment", "outcome", "observations"],
                "anyOf": [
                  { "required": ["repository"] },
                  { "required": ["state_space"] }
                ],
                "properties": {
                  "status": { "enum": ["final", "superseded"] },
                  "subjects": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "outcome": { "enum": ["pass", "fail", "inconclusive", "error"] }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "dependency" } }, "required": ["type"] },
              "then": {
                "required": ["kind", "source", "target"],
                "properties": {
                  "kind": { "enum": ["requires", "implements", "verifies", "derived_from", "relies_on", "orders_before", "conflicts_with", "supersedes", "integrates"] },
                  "source": { "$ref": "#/$defs/pinnedReference" },
                  "target": { "$ref": "#/$defs/pinnedReference" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "integration_plan" } }, "required": ["type"] },
              "then": {
                "required": ["owner", "base", "change_sets", "order", "verification", "rollback", "atomicity"],
                "properties": {
                  "status": { "enum": ["proposed", "approved", "integrating", "completed", "failed", "cancelled", "superseded"] },
                  "change_sets": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "order": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "atomicity": { "enum": ["atomic", "stepwise", "best_effort"] }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "integration_result" } }, "required": ["type"] },
              "then": {
                "required": ["plan", "base_revision", "result_revision", "input_dispositions", "verification", "rollback_status"],
                "oneOf": [
                  { "required": ["repository"] },
                  { "required": ["state_space"] }
                ],
                "properties": {
                  "plan": { "$ref": "#/$defs/pinnedReference" },
                  "repository": { "$ref": "#/$defs/identifier" },
                  "state_space": { "$ref": "#/$defs/identifier" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "presence" } }, "required": ["type"] },
              "then": {
                "required": [
                  "agent_id", "session_id", "principal", "workstate_id", "project",
                  "execution_location", "base", "declared_scopes", "access_mode",
                  "monitoring_profile", "heartbeat_at", "expires_at"
                ],
                "properties": {
                  "status": { "enum": ["active", "released", "expired", "superseded"] },
                  "agent_id": { "$ref": "#/$defs/identifier" },
                  "session_id": { "$ref": "#/$defs/identifier" },
                  "principal": { "$ref": "#/$defs/identifier" },
                  "workstate_id": { "$ref": "#/$defs/identifier" },
                  "project": { "$ref": "#/$defs/identifier" },
                  "execution_location": { "$ref": "#/$defs/executionLocation" },
                  "base": { "$ref": "#/$defs/stateReference" },
                  "declared_scopes": { "$ref": "#/$defs/pinnedReferenceArray" },
                  "access_mode": { "enum": ["observe", "read", "write"] },
                  "monitoring_profile": { "$ref": "#/$defs/identifier" },
                  "heartbeat_at": { "$ref": "#/$defs/timestamp" },
                  "expires_at": { "$ref": "#/$defs/timestamp" }
                }
              }
            },
            {
              "if": { "properties": { "type": { "const": "lease" } }, "required": ["type"] },
              "then": {
                "required": ["holder", "scope", "mode", "coordinator", "epoch", "fencing_token", "expires_at"],
                "properties": {
                  "status": { "enum": ["requested", "active", "denied", "released", "expired", "revoked", "superseded"] },
                  "scope": { "$ref": "#/$defs/pinnedReference" },
                  "mode": { "enum": ["shared_read", "shared_write", "exclusive_write", "integration_owner"] },
                  "fencing_token": { "type": "integer", "minimum": 1 }
                }
              }
            }
          ],
          "additionalProperties": true
        }
      ]
    },
    "coordinationEvent": {
      "type": "object",
      "required": ["event_schema_version", "module", "kind", "event_id", "workstate_id", "parents", "occurred_at", "actor", "payload"],
      "properties": {
        "event_schema_version": { "const": "0.2" },
        "module": { "const": "urn:awp:coordination" },
        "kind": { "type": "string", "pattern": "^[a-z_]+\\.[a-z_]+$" },
        "event_id": { "$ref": "#/$defs/identifier" },
        "workstate_id": { "$ref": "#/$defs/identifier" },
        "parents": { "$ref": "#/$defs/referenceArray" },
        "occurred_at": { "$ref": "#/$defs/timestamp" },
        "actor": { "$ref": "#/$defs/identifier" },
        "payload": { "type": "object" }
      },
      "additionalProperties": true
    }
  }
}
```

---

## Security schema — `schemas/awp-security-0.5.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:security:0.5.0",
  "title": "AWP Security 0.5 guardrails",
  "description": "Structural schema for a Security guardrail extension on a Core constraint record.",
  "oneOf": [
    { "$ref": "#/$defs/guardrail" }
  ],
  "$defs": {
    "identifier": {
      "type": "string",
      "minLength": 1,
      "pattern": "^\\S+$"
    },
    "guardrail": {
      "type": "object",
      "required": [
        "profile",
        "effect",
        "applies_to",
        "operation_classes",
        "resources",
        "policy_owner",
        "provenance",
        "enforcement",
        "propagation"
      ],
      "properties": {
        "profile": { "$ref": "#/$defs/identifier" },
        "effect": { "enum": ["deny", "require_authorization", "require_confirmation", "require_review"] },
        "applies_to": {
          "oneOf": [
            { "const": "all_actors" },
            { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/identifier" }, "uniqueItems": true }
          ]
        },
        "operation_classes": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 },
          "uniqueItems": true
        },
        "resources": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/identifier" },
          "uniqueItems": true
        },
        "conditions": { "type": "array", "items": { "type": "string", "minLength": 1 } },
        "exceptions": { "type": "array", "items": { "type": "object" } },
        "effective_from": { "type": "string", "format": "date-time" },
        "effective_until": { "type": "string", "format": "date-time" },
        "policy_owner": { "$ref": "#/$defs/identifier" },
        "provenance": {
          "type": "object",
          "required": ["issued_by", "basis"],
          "properties": {
            "issued_by": { "$ref": "#/$defs/identifier" },
            "basis": { "$ref": "#/$defs/identifier" },
            "issued_at": { "type": "string", "format": "date-time" },
            "authority_evidence": { "$ref": "#/$defs/identifier" }
          },
          "additionalProperties": true
        },
        "enforcement": { "enum": ["advisory", "receiver_policy", "protected_adapter"] },
        "propagation": { "enum": ["mandatory", "inherited", "none"] }
      },
      "additionalProperties": true
    }
  }
}
```

---

## Module-registry schema — `schemas/awp-module-registry-0.8.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:module-registry:0.8.0",
  "title": "AWP 0.8 Module Registry",
  "type": "object",
  "required": ["family", "family_version", "event_schema_versions", "modules"],
  "properties": {
    "$schema": { "type": "string" },
    "family": { "const": "AWP" },
    "family_version": { "const": "0.8.0" },
    "event_schema_versions": {
      "type": "array",
      "contains": { "const": "0.2" },
      "items": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+$" },
      "uniqueItems": true
    },
    "modules": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/module" }
    },
    "informative_documents": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "version", "document"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "version": { "$ref": "#/$defs/semver" },
          "document": { "$ref": "#/$defs/relativePath" }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false,
  "$defs": {
    "semver": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(?:-[0-9A-Za-z.-]+)?$"
    },
    "versionRange": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+(?:\\.[0-9]+|\\.x)$"
    },
    "relativePath": {
      "type": "string",
      "minLength": 1,
      "pattern": "^(?![A-Za-z]:)(?!/).+$"
    },
    "dependency": {
      "type": "object",
      "required": ["id", "version"],
      "properties": {
        "id": { "type": "string", "format": "uri" },
        "version": { "$ref": "#/$defs/versionRange" }
      },
      "additionalProperties": false
    },
    "module": {
      "type": "object",
      "required": ["id", "name", "version", "status", "document", "dependencies"],
      "properties": {
        "id": { "type": "string", "format": "uri" },
        "name": { "type": "string", "minLength": 1 },
        "version": { "$ref": "#/$defs/semver" },
        "status": { "enum": ["required", "optional", "experimental", "deprecated"] },
        "document": { "$ref": "#/$defs/relativePath" },
        "schema": { "$ref": "#/$defs/relativePath" },
        "dependencies": {
          "type": "array",
          "items": { "$ref": "#/$defs/dependency" }
        },
        "conditional_dependencies": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["when_capability", "id", "version"],
            "properties": {
              "when_capability": { "type": "string", "minLength": 1 },
              "id": { "type": "string", "format": "uri" },
              "version": { "$ref": "#/$defs/versionRange" }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    }
  }
}
```
