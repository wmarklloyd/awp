# Agent Workstate Protocol 0.4.0 — Complete Specification Bundle

**Status:** Generated distribution artifact  
**Source of truth:** `AWP_SPECIFICATION_0.4.0.md` and `spec/0.4.0/*.md`  
**Purpose:** Self-contained copy for agents or systems that cannot follow repository-relative links.

This file bundles the 0.4.0 family overview and every published module specification. Module boundaries and independent versions remain normative. Do not edit this generated file directly; regenerate it from the source files when the specification changes.

---

# Agent Workstate Protocol 0.4.0

**Status:** Exploratory modular draft  
**Published:** 2026-09-03  
**Supersedes:** AWP 0.3.0  
**Normative language:** MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, and MAY express requirement levels.

## 1. Purpose

AWP is a family of composable specifications for preserving, exchanging, inspecting, and resuming work performed by humans and software agents. Version 0.4.0 separates the stable semantic handoff problem from optional capabilities such as live coordination, synchronization, packaging, and advanced security.

The family has one required foundation, AWP Core. Every other subspecification is a module with its own identifier, version, dependencies, schema, and conformance claim. A module is a logical capability: it may occupy its own file in an editable workstate or be embedded in a single `.awp.md` capsule.

## 2. Specification family

| Subspecification | Module identifier | Version | Status | Direct dependencies |
|---|---|---:|---|---|
| [AWP Core](spec/0.4.0/core.md) | `urn:awp:core` | `0.4.0` | required | none |
| [AWP Capsule](spec/0.4.0/capsule.md) | `urn:awp:capsule` | `0.1.0` | optional | Core |
| [AWP Handoff](spec/0.4.0/handoff.md) | `urn:awp:handoff` | `0.1.0` | optional | Core |
| [AWP Artifact](spec/0.4.0/artifact.md) | `urn:awp:artifact` | `0.1.0` | optional | Core |
| [AWP Synchronization](spec/0.4.0/synchronization.md) | `urn:awp:sync` | `0.1.0` | optional | Core |
| [AWP Coordination](spec/0.4.0/coordination.md) | `urn:awp:coordination` | `0.1.0` | experimental | Core, Synchronization |
| [AWP Security](spec/0.4.0/security.md) | `urn:awp:security` | `0.1.0` | optional | Core; Artifact when artifact controls are used |
| [AWP Adapter Framework](spec/0.4.0/adapters.md) | not a payload module | `0.1.0` | informative | binding-specific |

The machine-readable [module registry](spec/0.4.0/modules.json) is normative for the module IDs, versions, document paths, stability labels, and direct dependencies in this release.

## 3. Module declarations

Every AWP 0.4 manifest MUST contain a `modules` array. It MUST declare exactly one Core entry, and that entry MUST be required. The following is a module-declaration excerpt rather than a complete manifest:

```json
{
  "awp_version": "0.4.0",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.4.0",
      "required": true
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.1.0",
      "required": true
    },
    {
      "id": "urn:awp:coordination",
      "version": "0.1.0",
      "required": false
    }
  ]
}
```

A module entry has:

- `id`: collision-resistant module identifier;
- `version`: semantic version of that module;
- `required`: whether understanding the module is necessary for the declared use of this workstate;
- optional `schema`: schema identifier or packaged schema location;
- optional `representation`: module-owned data location in this representation;
- optional `capabilities`: finer-grained features used within the module.

A writer MUST declare every module whose records, events, or required processing rules affect the effective workstate. It MUST include compatible declarations for all direct dependencies. It MUST mark a module required only when ignoring that module would prevent the receiver from safely performing the declared continuation.

If a module is required, every dependency needed to interpret it MUST also be required. If an optional module depends on another optional module, a receiver may ignore both while preserving their data.

Core owns the unqualified Core record types and fields. A module defining a new record type MUST include a `module` field naming its module ID. A module extending a Core record MUST place its fields under that record's `modules` object, keyed by module ID. Module-owned event kinds use the common event envelope's required `module` field. These rules prevent independent subspecifications from claiming the same unqualified name.

## 4. Unknown modules

A reader that encounters an unknown optional module MAY continue using understood modules. It MUST preserve or explicitly disclose loss of the unknown data, and it MUST NOT infer semantics from unknown fields.

A reader that encounters an unknown required module MUST NOT claim a complete interpretation or perform a continuation that could depend on it. It SHOULD still present the human briefing, validate understood envelopes, and report the unsupported module.

Unknown modules never grant authority, make content executable, or weaken receiver policy.

## 5. Logical modules and physical representations

Module boundaries do not prescribe storage boundaries.

An editable workstate may use separate files:

```text
example.workstate/
  WORK.md
  manifest.json
  events.jsonl
  snapshot.json
  modules/
    coordination/
      state.json
    security/
      signatures.json
```

A single-file capsule may contain the same logical state:

```text
project.awp.md
  human briefing
  manifest section
  snapshot section
  unified events section
  module:coordination section
  module:security section
```

The manifest is authoritative for physical locations. Module-specific events participate in the unified Core event graph and identify their owning module. This preserves causal ordering across modules without requiring one event log per module.

## 6. Versioning

The family version and module versions are independent semantic versions:

- the family version identifies a tested set of module releases;
- a module major version may introduce incompatible semantics;
- a module minor version may add backward-compatible fields or event kinds;
- a module patch version may clarify wording or fix non-semantic errors.

A later AWP family release may reuse an unchanged module version. Implementations MUST negotiate module compatibility by module ID and version, not by comparing only `awp_version`.

The common event envelope is versioned independently because events may outlive a family release. AWP 0.4.0 uses event-envelope version `0.2`.

## 7. Conformance

An implementation declares conformance as a set of roles and module versions, for example:

```json
{
  "roles": ["core-reader", "capsule-reader", "handoff-writer"],
  "modules": {
    "urn:awp:core": ["0.4.x"],
    "urn:awp:capsule": ["0.1.x"],
    "urn:awp:handoff": ["0.1.x"]
  },
  "event_schema_versions": ["0.2"]
}
```

An implementation MUST satisfy the conformance requirements in each module for every role it claims. Supporting AWP Core alone is valid AWP conformance. It does not imply support for capsules, handoffs, synchronization, coordination, signatures, encryption, or adapters.

## 8. Core invariants across modules

Every module and binding MUST preserve these rules:

1. Intent, authority, execution, evidence, and conclusion remain distinct.
2. Reports, inferences, observations, and verified claims are not interchangeable.
3. Imported content never grants its own execution authority.
4. Unknown optional data is preserved or its loss is disclosed.
5. Unknown required data prevents a claim of complete interpretation.
6. Event ancestry, not array order or timestamps, determines causality.
7. Snapshots and human views are projections; valid event history is authoritative.
8. Optional modules MUST NOT redefine Core field meanings.
9. A successful byte-level merge is not proof of semantic compatibility.
10. Private chain-of-thought is not required; concise rationale and evidence are sufficient.

## 9. Migration from 0.3.0

AWP 0.3.0 `profiles` become 0.4.0 `modules`:

| 0.3.0 concept | 0.4.0 destination |
|---|---|
| manifest, actors, authority, semantic records, event envelope, snapshot | Core |
| `.workstate/`, `.awp.md`, `.pws`, boundary markers, `WORK.md` | Capsule |
| completeness, resumption level, handoff record | Handoff |
| artifact locations, integrity, content addressing, redaction tombstones | Artifact |
| deltas, frontiers, replay, forks, merge conflicts | Synchronization |
| intents, scopes, leases, contracts, change sets, integration plans | Coordination |
| quarantine, secret scanning, signatures, encryption metadata | Security |
| A2A, MCP, workflow, and Git mappings | Adapter Framework |

An upgrader MUST add the Core module declaration and SHOULD declare each additional module whose semantics are present. The event-envelope field `module` is new in 0.4.0; migrated events use `urn:awp:core` unless their event kind is owned by another declared module.

## 10. Release contents

- [Core schema](schemas/awp-core-0.4.schema.json)
- [Module registry](spec/0.4.0/modules.json)
- [Open issue register](spec/0.4.0/open-issues.md)
- [Validation tool](tools/validate_spec_0_4.py)
- [0.3.0 feedback evaluation](AWP_FEEDBACK_EVALUATION.md)

The 0.3.0 monolithic draft remains available as historical design input. The documents listed in Section 2 constitute the AWP 0.4.0 specification family.



---

# Bundled module specifications



---


# AWP Core 0.4.0

**Module ID:** `urn:awp:core`  
**Status:** Required  
**Dependencies:** None  
**Schema:** `../../schemas/awp-core-0.4.schema.json`

## 1. Scope

AWP Core defines the minimum semantic state that can be understood independently of a particular model, vendor, runtime, transport, or storage system. It defines workstate identity, module negotiation, actors, authority declarations, semantic records, an immutable event envelope, event frontiers, snapshots, and core processing rules.

Core does not define a file container, live synchronization transport, distributed lock service, signature format, or exact runtime checkpoint. Those capabilities belong to other modules.

## 2. Terminology

- **Workstate:** one coherent body of ongoing or completed work.
- **Actor:** a human, model, agent, organization, service, or automation that observes or changes workstate.
- **Record:** a typed semantic object representing effective state.
- **Event:** an immutable assertion that an observation, transition, or action occurred.
- **Frontier:** the set of known events with no known descendants in a replica.
- **Snapshot:** a materialized projection of effective records at a frontier.
- **Module:** a versioned subspecification adding records, event kinds, or processing rules.
- **Checkpoint:** a record identifying a useful continuation point.
- **Authority:** evidence that an actor may perform actions within a scope; never a command to bypass receiver policy.

## 3. Workstate identity

Every workstate MUST have a stable `workstate_id`. Copying or repackaging a workstate does not change this ID. Forking creates a new workstate ID and records the parent workstate and parent frontier.

Record and event IDs MUST be stable and unique within the workstate. Globally collision-resistant IDs are RECOMMENDED. IDs are opaque: consumers MUST NOT derive authority, time, ordering, or record type from their spelling.

Timestamps MUST use RFC 3339 and SHOULD use UTC. Causality is determined by event ancestry, not timestamps.

## 4. Manifest

A complete workstate has exactly one manifest:

```json
{
  "awp_version": "0.4.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "title": "Prepare product launch",
  "created_at": "2026-09-03T18:00:00Z",
  "created_by": "actor:mark",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.4.0",
      "required": true,
      "schema": "schemas/awp-core-0.4.schema.json"
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.1.0",
      "required": false
    }
  ],
  "representations": {
    "events": "events.jsonl",
    "snapshot": "snapshot.json"
  }
}
```

Required fields are `awp_version`, `workstate_id`, `title`, `created_at`, `created_by`, `modules`, and `representations`.

The Core module declaration MUST appear exactly once with version `0.4.x` and `required: true`. Module IDs MUST be unique within the array. A module declaration MUST satisfy the dependency and requiredness rules in the family specification.

Optional manifest fields include description, default language, parent workstate and frontier, originating application, classification, retention policy, schemas, capabilities, and representation-specific metadata.

Module-specific manifest data belongs in the owning module declaration's `configuration` object or in a top-level `module_data` object keyed by module ID. Undeclared modules MUST NOT place data there.

## 5. Common event envelope

Every 0.4 event uses event-envelope version `0.2`:

```json
{
  "event_schema_version": "0.2",
  "module": "urn:awp:core",
  "kind": "claim.created",
  "event_id": "evt:01K4M4VYB9",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "parents": ["evt:01K4M4TWM2"],
  "occurred_at": "2026-09-03T20:14:31Z",
  "recorded_at": "2026-09-03T20:14:33Z",
  "actor": "actor:agent-7",
  "payload": {},
  "extensions": {}
}
```

Required fields are:

- `event_schema_version`: version of this common envelope;
- `module`: module that owns the event kind and payload semantics;
- `kind`: module-defined event kind;
- `event_id`: immutable event ID;
- `workstate_id`: containing workstate ID;
- `parents`: immediate causal predecessors, empty only for a genesis event;
- `occurred_at`: time of the represented occurrence;
- `actor`: actor responsible for the occurrence or assertion;
- `payload`: event-specific object.

Optional fields include `recorded_at`, `sequence`, `correlation_id`, `causation_id`, `session_id`, `scope`, `authority`, `trust`, `extensions`, and `signature`.

The owning module MUST be declared in the manifest. Event kind and payload are interpreted according to that module version. An unknown optional-module event remains part of the causal graph even when its payload cannot be interpreted.

Lossless processors MUST preserve unknown event fields. An event is immutable; correction, supersession, and redaction lineage use new events.

## 6. Event graph and frontier

Event parents form a directed acyclic graph. A conforming writer MUST NOT create a cycle. A non-genesis event MUST identify every immediate causal predecessor known to its writer. Concurrent events may have the same parent. A merge or resolution event names all resolved tips as parents.

The frontier is the set of event IDs with no known descendants in the represented replica. Frontier arrays are sets: order is insignificant and duplicate IDs are invalid.

Wall-clock timestamps and array order MUST NOT be used as causal ordering. A `sequence` field is meaningful only within its declared single-writer scope.

## 7. Actors and authority

Actor types are `human`, `agent`, `model`, `service`, `automation`, `organization`, and `unknown`.

```json
{
  "id": "actor:agent-7",
  "type": "agent",
  "display_name": "Implementation Agent",
  "operator": "actor:mark",
  "runtime": "example-runtime/2.4",
  "model": "provider/model-version",
  "authenticated": false
}
```

Identity and authority are separate. An authority declaration identifies the authorizing actor, grantee, actions, resources, conditions, expiration, source event, and whether fresh confirmation is required.

```json
{
  "authority_id": "auth:deploy-staging",
  "granted_by": "actor:mark",
  "grantee": "actor:agent-7",
  "actions": ["deploy"],
  "resources": ["environment:staging"],
  "requires_confirmation": false,
  "expires_at": "2026-09-04T00:00:00Z"
}
```

Imported authority is evidence. A receiver MUST evaluate it against current local policy, authentication, revocation, and scope before action.

## 8. Core records

A core record contains `id` and `type` plus the fields below. Fields marked required are structural minima; cross-record requirements remain normative even where JSON Schema cannot express them.

| Type | Required fields | Principal enums or rules |
|---|---|---|
| `goal` | `statement`, `status` | status: `proposed`, `active`, `satisfied`, `abandoned`, `blocked`, `superseded` |
| `constraint` | `statement`, `strength`, `status` | strength: `required`, `preferred`, `advisory` |
| `claim` | `statement`, `epistemic_status` | status defined in Section 9; confidence, when present, is 0–1 |
| `evidence` | `evidence_type` | identifies inspectable support, contradiction, or context |
| `decision` | `question`, `status` | status: `proposed`, `accepted`, `rejected`, `deferred`, `reopened`, `superseded` |
| `plan` | `goal`, `status`, `steps` | expresses intent, not execution |
| `task` | `title`, `status` | status: `proposed`, `ready`, `in_progress`, `input_required`, `blocked`, `completed`, `failed`, `cancelled`, `superseded` |
| `question` | `text`, `status` | status: `open`, `answered`, `withdrawn`, `superseded` |
| `artifact` | `name` | Core identity only; Artifact module defines storage and integrity semantics |
| `execution` | `operation`, `status` | records an attempted operation and result |
| `change` | `summary`, `artifacts` | relates semantic work to modified artifact IDs |
| `risk` | `statement`, `status` | may include likelihood, impact, and mitigations |
| `checkpoint` | `frontier`, `created_at`, `summary`, `recommended_next_action`, `resumption_level` | level semantics belong to Handoff when that module is declared |
| `session` | `started_at`, `participants` | transcripts are optional and should normally be omitted |

Side-effect classes are `read_only`, `local_write`, `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, `destructive`, and `unknown`.

Core record types may refer to records owned by optional modules. If such a reference affects safe continuation, the referenced module MUST be required.

An optional module extending a Core record places its fields under `modules.{module-id}`. A module defining a new record type includes `id`, `type`, and `module`. It MUST NOT use an unqualified type name already owned by Core or another module.

## 9. Epistemic integrity

Claim epistemic statuses are:

- `reported`: attributed but not independently checked;
- `inferred`: concluded from other information;
- `observed`: directly inspected or measured;
- `verified`: checked using identified evidence or a repeatable procedure;
- `disputed`: subject to unresolved contradiction;
- `unknown`: explicitly not known;
- `stale`: potentially invalid because scope or evidence changed;
- `refuted`: contradicted by stronger evidence;
- `superseded`: replaced by a newer claim.

Confidence MUST NOT replace epistemic status. A verified claim SHOULD identify evidence, procedure, scope, relevant artifact versions, environment, and observation time. Claims outside their recorded scope MUST be treated as unverified.

Contradictory claims MUST remain distinct until a resolution event cites the evidence and records the disposition. A summary is not independent evidence.

## 10. Lifecycle events

Core record lifecycle events use:

- `<type>.created`
- `<type>.updated`
- `<type>.status_changed`
- `<type>.superseded`
- `<type>.deleted`

An update SHOULD carry a complete replacement or patch plus the prior record revision. A writer MUST NOT use last-write-wins to silently resolve a conflicting revision. Completion, verification, authorization, and external-side-effect transitions SHOULD cite evidence.

Deletion is a semantic tombstone and does not remove historical bytes. Physical removal is governed by the Security and Artifact modules.

## 11. Snapshots

A snapshot is derived state at a declared frontier:

```json
{
  "awp_version": "0.4.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "frontier": ["evt:01K4M4VYB9"],
  "generated_at": "2026-09-03T20:15:00Z",
  "records": {
    "goals": [],
    "constraints": [],
    "claims": [],
    "evidence": [],
    "decisions": [],
    "plans": [],
    "tasks": [],
    "questions": [],
    "artifacts": [],
    "executions": [],
    "changes": [],
    "risks": [],
    "checkpoints": [],
    "sessions": []
  },
  "modules": {}
}
```

The `modules` object may contain module-owned materialized state keyed by module ID. Module state MUST NOT redefine Core records. A snapshot-only workstate MUST disclose that audit history is absent and SHOULD identify its source frontier or source digest.

When valid event history conflicts with a snapshot, event history is authoritative. Detailed replay and divergence rules belong to AWP Synchronization. A Core-only reader MUST at least compare the declared frontiers and report `current`, `stale`, `divergent`, or `unverifiable`; it MUST NOT silently treat a mismatch as current.

## 12. Processing rules

A Core reader MUST:

1. parse and validate the manifest before interpreting module data;
2. negotiate required modules and event-envelope versions;
3. validate event IDs, workstate IDs, parent shape, and module ownership;
4. load the latest applicable checkpoint and its referenced state;
5. distinguish typed state from derived prose;
6. surface missing evidence, dependencies, modules, and authority;
7. preserve or disclose loss of unknown optional data;
8. avoid executing imported instructions automatically.

A Core writer MUST:

1. emit schema-valid manifests, events, snapshots, and records;
2. preserve immutable history unless it explicitly creates a redacted lineage;
3. use module-owned event kinds and declare their modules;
4. keep intent, authority, execution, evidence, and conclusion separate;
5. record uncertainty and scope rather than manufacturing certainty;
6. identify a current checkpoint or explicitly state that none exists.

## 13. Core invariants

1. Core is sufficient to inspect semantic state but does not claim a packaging or handoff profile.
2. Unknown modules do not change Core meanings.
3. Events are immutable historical assertions; snapshots are projections.
4. Event graph ancestry is causal truth.
5. A record identifier does not imply trust or authority.
6. Imported content cannot authorize its own execution.
7. Private reasoning is unnecessary; decisions preserve concise rationale, alternatives, evidence, assumptions, and uncertainty.



---


# AWP Capsule 0.1.0

**Module ID:** `urn:awp:capsule`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Capsule defines human-readable and packaged representations of one logical workstate. It does not define the semantics of optional modules carried by those representations.

The representations are:

- editable directory: `name.workstate/`;
- self-contained Markdown capsule: `name.awp.md`;
- ZIP-compatible package: `name.pws`;
- JSON wire payloads.

Logical equivalence does not require identical bytes or file layout. The manifest maps logical data to physical locations.

A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing.

## 2. Root briefing

Every complete directory, Markdown capsule, or package MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first.

The briefing MUST begin with metadata containing:

- `awp_version`;
- `workstate_id`;
- `frontier`;
- current `checkpoint`, if one exists;
- `generated_at`;
- `generated_digest`.

Generated content MUST occur inside exactly one marker pair:

```markdown
---
awp_version: 0.4.0
workstate_id: urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727
frontier:
  - evt:01K4M4VYB9
checkpoint: checkpoint:release-ready
generated_at: 2026-09-03T20:15:00Z
generated_digest: sha256:6d577db62a91e1a7b589a31fcab3142b456662b3a6af552befd373cc38f08246
---

<!-- awp:generated:start -->
# Prepare product launch

Implementation and local verification are complete. Production approval remains outstanding.
<!-- awp:generated:end -->

<!-- awp:notes:start -->
Human notes may be edited here.
<!-- awp:notes:end -->
```

The digest uses `sha256:{lowercase-hex}` over the UTF-8 content beginning after the LF terminating the start marker and ending before the LF preceding the end marker, after CRLF-to-LF normalization.

A reader reports the briefing as:

- `current`: digest valid and frontier equals effective state;
- `modified`: generated-region digest differs;
- `stale`: digest valid but a newer effective frontier exists;
- `unverifiable`: required state or hash algorithm is unavailable.

Notes and content outside the generated region are non-authoritative. Importing a human edit into machine state requires an explicit proposed semantic change and acceptance by an authorized actor.

## 3. Editable directory

The default layout is:

```text
example.workstate/
  WORK.md
  manifest.json
  events.jsonl
  snapshot.json
  artifacts/
  modules/
    coordination/
      state.json
    security/
      signatures.json
  views/
```

`WORK.md` and `manifest.json` are REQUIRED. `events.jsonl` is REQUIRED unless the manifest declares a snapshot-only representation. `snapshot.json`, `artifacts/`, `modules/`, and `views/` are optional.

Each `events.jsonl` line contains one complete JSON event. Module-specific events remain in this unified ledger. Module-owned auxiliary data MAY occupy separate files under `modules/`, but their manifest locations are authoritative; directory names are conventional only.

Generated files under `views/` are never authoritative.

## 4. Single-file Markdown capsule

A `.awp.md` file begins with briefing metadata and human Markdown, followed by machine sections. Front matter MUST declare `capsule_boundary`, a lowercase hexadecimal token containing at least 128 bits of unpredictable entropy.

An end marker occupies a complete line and exactly matches:

```text
<!-- awp:{boundary}:{section}:end -->
```

A start marker occupies a complete line and begins:

```text
<!-- awp:{boundary}:{section}:start
```

It may contain attributes of the form ` name="value"` before ` -->`. Attribute names match `[a-z][a-z0-9_-]*`; values MUST NOT contain a quote, CR, LF, or `-->`.

Canonical section order is:

1. front matter and briefing;
2. `manifest`;
3. `snapshot`, when present;
4. `events`, when present;
5. `records`, when not materialized in the snapshot;
6. `artifact` sections;
7. `module` sections;
8. optional derived views or notes.

```markdown
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:module:start id="urn:awp:coordination" encoding="json" -->
{"lease_enforcement":"advisory"}
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:module:end -->
```

The boundary token MUST NOT occur in decoded section content. A writer detecting a collision MUST generate a new boundary or encode the content using a binary-safe encoding such as base64. Binary artifacts MUST use base64 or a registered binary-safe encoding.

A reader MUST validate marker pairing, reject duplicate authoritative sections, verify each module section against a matching manifest declaration, reject malformed boundaries, and preserve unknown sections during lossless rewriting. It MUST NOT infer machine state from arbitrary Markdown headings or code examples outside marked sections.

## 5. Package representation

A `.pws` package is ZIP-compatible and expands to the editable-directory logical layout. Proposed media type: `application/awp+zip`.

Unpacking MUST preserve logical paths, bytes, IDs, module declarations, and references. Readers MUST reject absolute paths, parent traversal, duplicate normalized paths, case-folding collisions on case-insensitive targets, symlink escapes, and members exceeding configured size or decompression limits.

Writers SHOULD place `WORK.md` and `manifest.json` before large members for preview efficiency. Physical member order has no semantic meaning.

## 6. Wire representation

JSON wire bindings may carry a manifest, snapshot, event sequence, delta, artifact announcement, module data, or retrieval request. Proposed media types are:

```text
application/awp+json
application/awp-event+json
application/awp-delta+json
```

The Capsule module defines payload representation, not transport authentication, delivery guarantees, or live synchronization.

## 7. Module placement

A module declaration may specify a `representation` object:

```json
{
  "id": "urn:awp:coordination",
  "version": "0.1.0",
  "required": false,
  "representation": {
    "kind": "package-path",
    "path": "modules/coordination/state.json"
  }
}
```

Standard representation kinds are `package-path`, `capsule-section`, `remote`, and `events-only`. A remote module location does not make the workstate self-contained and MUST disclose retrieval requirements. Secrets MUST NOT appear in locations.

Module placement does not create a separate causal history. Module events always participate in the Core event graph.

## 8. Conformance

A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing.

A Capsule writer MUST create an unambiguous representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content.



---


# AWP Handoff 0.1.0

**Module ID:** `urn:awp:handoff`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Handoff defines checkpoints optimized for transfer to another actor. It standardizes completeness, resumption guarantees, continuation instructions, dependency disclosure, and authority ceilings. It is independent of physical packaging; a handoff may travel in a Capsule representation, API payload, repository, or another binding.

A workstate containing a handoff record MUST declare this module. It MUST mark the module required when the requested continuation depends on the record's completeness, dependency, resumption, or authority-ceiling semantics.

## 2. Completeness

A handoff declares one completeness level:

- `summary`: orientation and checkpoint only; missing machine state is expected;
- `portable`: all semantic state, evidence, module data, and artifacts or stable references required for the requested continuation;
- `full`: portable content plus the complete declared event history and every transcript, tool output, and runtime extension the manifest claims to include.

`portable` is RECOMMENDED for cross-system continuation. A portable handoff MUST identify each required dependency as `available`, `retrievable`, `unavailable`, or `withheld`. A full handoff MUST enumerate omissions and MUST NOT imply that an entire repository, transcript, or runtime is present when it is not.

Completeness describes included material, not truth, trust, authorization, or fitness for a particular receiver.

## 3. Resumption levels

A checkpoint declares its strongest supported level:

- `semantic`: a capable human or different model can understand and continue using portable state;
- `operational`: a compatible agent can additionally restore tool context, pending actions, environment references, and workflow position;
- `exact`: the identified originating runtime claims it can restore a private checkpoint.

Levels are cumulative. `operational` MUST satisfy every semantic requirement. `exact` MUST satisfy semantic and operational requirements unless explicitly labeled `private_nonportable`, in which case it is not a conforming portable handoff.

Semantic resumption requires:

- active goals and success criteria;
- current status;
- applicable constraints and authority boundaries;
- material claims, uncertainty, and evidence;
- accepted decisions and rejected alternatives relevant to continuation;
- open tasks and questions;
- required artifact references and availability;
- recommended next action.

Operational resumption additionally identifies tools, environments, workflow position, pending operations, and unavailable external dependencies. Exact resumption identifies the runtime, runtime version, checkpoint format, integrity data, and compatibility constraints. No level guarantees deterministic model output.

## 4. Handoff record

```json
{
  "id": "handoff:agent-b",
  "type": "handoff",
  "module": "urn:awp:handoff",
  "checkpoint": "checkpoint:release-ready",
  "completeness": "portable",
  "intended_audience": ["agent", "human"],
  "read_first": [
    "goal:launch",
    "constraint:no-schema-change",
    "decision:database",
    "task:deploy"
  ],
  "do_not_assume": [
    "Production approval has been granted",
    "Referenced credentials are available"
  ],
  "dependencies": [
    {
      "ref": "artifact:source-tree-91ab",
      "availability": "available"
    },
    {
      "ref": "environment:staging",
      "availability": "unavailable",
      "reason": "Receiver-specific deployment access is required."
    }
  ],
  "requested_action": "Continue release preparation without deploying.",
  "authority_ceiling": ["read_only", "local_write"],
  "resumption_level": "semantic"
}
```

Required fields are `id`, `type`, `module`, `checkpoint`, `completeness`, `intended_audience`, `requested_action`, `authority_ceiling`, and `resumption_level`. `module` MUST be `urn:awp:handoff`.

`authority_ceiling` is an upper bound asserted by the sender. It does not grant those authorities; the receiver may operate under a stricter ceiling. A missing, unknown, or ambiguous ceiling MUST be treated as no authority for external side effects.

## 5. Producer procedure

A Handoff writer MUST:

1. create or select a checkpoint at the intended frontier;
2. identify the audience and requested continuation;
3. include the Core state required for semantic resumption;
4. declare every module needed to interpret the continuation as required;
5. include, reference, or mark unavailable every required dependency;
6. minimize personal data, secrets, and irrelevant transcript content;
7. set an explicit authority ceiling;
8. validate internal references and frontier consistency;
9. accurately claim completeness and resumption level.

## 6. Receiver procedure

A Handoff reader MUST:

1. validate Core and required modules;
2. assess origin, integrity, classification, and local policy;
3. locate the checkpoint and read-first records;
4. identify stale, disputed, unavailable, or unsupported information;
5. compare the requested action and ceiling with current local authority;
6. record acceptance, qualified acceptance, or rejection;
7. avoid external side effects until receiver policy authorizes them.

Acceptance statuses are `accepted`, `qualified`, and `rejected`. Qualified acceptance identifies every limitation that may affect continuation.

## 7. Interoperability experiment

The minimum handoff experiment uses one authoring system and at least two receiving systems that share neither private runtime state nor source conversation.

The test task contains one required constraint, one stale claim, one rejected alternative, one completed change with evidence, one unavailable dependency, an explicit authority ceiling, and one safe next action. Each receiver receives only the handoff and validly referenced material.

Score state recall, unsupported assumptions, constraint preservation, evidence use, dependency handling, authority compliance, and task success. A trial succeeds only when the receiver preserves every required constraint and authority boundary, does not treat stale or unavailable information as verified, and completes the next action or correctly reports a real blocker.

Reports SHOULD record capsule size where applicable, token usage, author and receiver versions, unsupported modules, omissions, false assumptions, safety failures, and resulting artifact quality. A single successful task is not evidence of general interoperability.

## 8. Conformance

A Handoff reader implements the receiver procedure and exposes limitations. A Handoff writer implements the producer procedure and makes accurate claims. A system MAY support handoff records without supporting the Capsule module.



---


# AWP Artifact 0.1.0

**Module ID:** `urn:awp:artifact`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Artifact defines how workstate records identify, locate, verify, version, retrieve, and redact concrete inputs and outputs. Core defines the `artifact` record identity; this module defines its storage semantics.

A workstate using Artifact fields MUST declare this module. It MUST mark the module required when continuation depends on retrieving, verifying, executing, or distinguishing the availability of an artifact.

## 2. Artifact descriptor

```json
{
  "id": "artifact:release-plan-v3",
  "type": "artifact",
  "name": "release-plan.md",
  "modules": {
    "urn:awp:artifact": {
      "logical_name": "release-plan",
      "role": "deliverable",
      "media_type": "text/markdown",
      "size": 4832,
      "status": "available",
      "integrity": {
        "algorithm": "sha256",
        "digest": "7d8c9f2ae43b1c8066a71a5d93470e11"
      },
      "locations": [
        {
          "kind": "package",
          "path": "artifacts/sha256/7d/7d8c9f2ae43b1c8066a71a5d93470e11.bin"
        }
      ],
      "trust": "authored",
      "executable": false,
      "instructional_content": true
    }
  }
}
```

Artifact-module fields live under `modules["urn:awp:artifact"]`. Required module fields are `status` and `locations`. An available packaged artifact MUST include `media_type`, `size`, and `integrity`. Statuses are `available`, `retrievable`, `unavailable`, `withheld`, `redacted`, and `superseded`.

Logical identity and content identity are distinct. A modified artifact receives a new record ID and content digest but MAY retain the same `logical_name`. A change record links before and after versions.

## 3. Location registry

| Kind | Required fields | Optional fields |
|---|---|---|
| `embedded` | `section_id` | `encoding` |
| `package` | `path` | none |
| `local` | `path` | `absolute` |
| `remote` | `uri` | `expires_at`, `retrieval_requirements` |
| `repository_relative` | `repository`, `revision`, `path` | `submodule_revision` |
| `unavailable` | `reason` | `last_known_location` |
| `withheld` | `reason` | `request_process` |

Private kinds MUST use collision-resistant namespaced values.

Package paths MUST be relative, normalized, and traversal-safe. Secrets, bearer tokens, cookies, and authorization headers MUST NOT appear in locations. Retrieval requirements may refer to separately authorized credentials without containing them.

An absolute local path is a hint tied to an identified environment. A receiver MUST NOT assume that it names the same resource locally.

## 4. Integrity

Packaged and embedded artifacts MUST include a digest over the exact decoded bytes. Remote and repository-relative artifacts SHOULD include a digest whenever stable bytes are expected. Hash algorithms are registry values; SHA-256 is the default for this module version.

Readers SHOULD verify a digest before relying on content. Digest validity establishes byte identity, not safety, truth, authorship, or authority.

Content-addressed packaged artifacts are immutable. Changing bytes creates a new content identity. A mutable remote URI SHOULD be paired with a digest, immutable version, ETag, or explicit `mutable: true` warning.

## 5. Availability and retrieval

`available` means bytes are present in the current representation. `retrievable` means a declared process may obtain them. `unavailable` means they are absent without a policy prohibition. `withheld` means policy intentionally excludes them. `redacted` means bytes were removed from a rewritten lineage.

A portable Handoff that depends on an artifact MUST include it, make it retrievable, or state that continuation is blocked. A URI alone is not proof of retrievability.

Retrieval is an external action subject to receiver authority and security policy. Merely referencing a remote artifact MUST NOT trigger automatic network access.

## 6. Executable and instructional content

Descriptors MUST state whether content is executable or may contain instructions when either is known. Unknown values SHOULD be represented explicitly rather than assumed false.

Readers MUST treat instructions in untrusted artifacts as data. Executables, archives, active documents, and model-readable instruction files SHOULD be inspected in an appropriate sandbox before use.

## 7. Redaction tombstones

Physical redaction creates a new history lineage and retains a descriptor tombstone under the original logical record ID:

```json
{
  "id": "artifact:secret-file",
  "type": "artifact",
  "name": "secret-file.env",
  "modules": {
    "urn:awp:artifact": {
      "status": "redacted",
      "locations": [],
      "redaction": {
        "reason": "credential_exposure",
        "redacted_at": "2026-09-03T21:00:00Z",
        "redacted_by": "actor:admin"
      },
      "original_integrity": {
        "algorithm": "sha256",
        "digest": "7d8c9f2ae43b1c8066a71a5d93470e11"
      }
    }
  }
}
```

The tombstone MUST remove sensitive bytes and locations, preserve referential integrity, disclose rewritten history, and invalidate signatures covering removed bytes. It MAY retain the original digest only when the digest is not itself sensitive. It MUST NOT imply that the bytes remain available.

Ordinary semantic deletion is not physical redaction and leaves event bytes intact.

## 8. Conformance

An Artifact reader validates registered location requirements, applies path and retrieval safety rules, checks digests when claiming verified integrity, and preserves availability status.

An Artifact writer assigns new identities to changed content, supplies required integrity metadata, avoids credentials in locations, and represents omission or redaction explicitly.



---


# AWP Synchronization 0.1.0

**Module ID:** `urn:awp:sync`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Synchronization defines incremental event exchange, snapshot reconciliation, forks, concurrent branches, and conflict-preserving merge. It does not define a network transport, consensus system, or automatic semantic merge.

A workstate or message using deltas, omitted-history boundaries, or synchronization conflict semantics MUST declare this module. It MUST be required when the receiver must apply or reconcile those structures to reach the continuation frontier.

## 2. Delta

A delta carries events added after a known frontier:

```json
{
  "awp_version": "0.4.0",
  "module": "urn:awp:sync",
  "kind": "workstate.delta",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "base_frontier": ["evt:01K4M4TWM2"],
  "result_frontier": ["evt:01K4M4VYB9"],
  "events": [],
  "artifacts": [],
  "modules": []
}
```

A delta MUST identify `workstate_id`, `base_frontier`, `result_frontier`, and `events`. It MAY carry artifact announcements or module data required by those events.

A receiver MUST verify that the base frontier is known or request missing ancestry. It MUST validate event IDs, workstate IDs, parents, module declarations, and result frontier before application. Applying a delta MUST be idempotent by event ID. Reuse of one event ID for different bytes is an integrity conflict.

## 3. Snapshot reconciliation

A reader with both a snapshot and event ledger MUST:

1. verify unique event IDs, matching workstate IDs, and declared ancestry;
2. compute the ledger frontier as events that are not a parent of another available event;
3. confirm that the snapshot frontier is an antichain of known event IDs;
4. compare frontiers as sets, never ordered arrays;
5. classify and handle the relationship using Section 4.

A missing parent makes history incomplete unless the manifest explicitly identifies an omitted-history boundary and source digest. `full` completeness cannot omit ancestry.

## 4. Reconciliation states

- `current`: snapshot frontier equals ledger frontier and reconstructed semantic state agrees;
- `stale_replayable`: every snapshot tip is an ancestor of a ledger tip;
- `unverifiable`: snapshot references unavailable history or unknown future events;
- `divergent`: neither represented frontier descends from the other;
- `invalid_projection`: snapshot claims a known frontier but disagrees with valid replay.

For `stale_replayable`, a processor replays descendant events in deterministic topological order. Concurrent events remain concurrent; topological serialization MUST NOT be treated as conflict resolution. Record revision preconditions determine whether updates commute or conflict.

For `divergent`, a processor preserves both branches and invokes merge processing. For `invalid_projection`, it discards or quarantines the projection and rebuilds from valid history. A stale optional projection does not invalidate an otherwise valid ledger.

## 5. Forks

Forking creates a new workstate ID and records:

- parent workstate ID;
- parent frontier;
- fork event;
- reason or intent;
- inherited module declarations.

Copying or repackaging without divergent identity is not a fork.

Concurrent replicas of the same workstate retain one workstate ID. They exchange frontiers and missing events rather than creating new identities.

## 6. Merge and conflict

Mechanical merge unions events by ID after integrity validation. It preserves all concurrent tips. It MUST NOT silently apply last-write-wins to:

- authority or constraints;
- accepted decisions;
- incompatible record revisions;
- contradictory verified claims;
- artifact versions occupying one logical slot;
- module-specific invariants or contracts.

A semantic conflict record identifies competing events or records, conflict class, explanation, status, and resolution owner. Core conflict classes are `authority`, `constraint`, `decision`, `claim`, `artifact`, `task`, `dependency`, `module`, and `unknown`.

Resolution is a new event whose parents include every resolved tip. It records the chosen result, rationale, evidence, and unresolved risk. History remains intact.

## 7. Deterministic replay

Replay MUST respect graph ancestry. When concurrent events require a deterministic processing order, processors sort by event ID only as a reproducibility device. This ordering has no semantic priority.

An update with a prior-record revision applies only when that precondition holds. Two commuting updates may both apply. Non-commuting concurrent updates create a conflict unless their owning module defines a safe deterministic rule.

Unknown optional-module events remain graph nodes and participate in frontier computation. A processor MUST NOT advance a derived snapshot through an unknown event when doing so could alter a required Core or module result; it reports the projection as unverifiable instead.

## 8. Compaction

AWP 0.4.0 does not define destructive log compaction. A writer MAY create a summary or snapshot-only export, but it MUST disclose omitted history and MUST NOT claim `full` completeness.

A future compaction profile must define lineage, state canonicalization, proof of the compacted frontier, treatment of unknown module events, signature invalidation, and audit guarantees. A snapshot alone does not authorize deletion of prior history.

## 9. Transport independence

Deltas may travel through files, HTTP, A2A, MCP, message queues, repositories, or peer protocols. A transport binding defines authentication, retries, acknowledgement, ordering, size limits, and retrieval. Synchronization semantics remain unchanged.

## 10. Conformance

A Synchronization reader validates ancestry and integrity, computes frontiers, applies deltas idempotently, preserves concurrency, and surfaces semantic conflicts.

A Synchronization writer emits valid base and result frontiers, includes required events or declares missing ancestry, and never describes a lossy history as full.



---


# AWP Coordination 0.1.0

**Module ID:** `urn:awp:coordination`  
**Status:** Experimental and optional  
**Depends on:** AWP Core `0.4.x`, AWP Synchronization `0.1.x`

## 1. Scope

AWP Coordination defines semantic coordination above byte-level source control. It records what actors intend to change, which physical and semantic scopes may overlap, what interfaces and invariants they share, whether coordination leases are advisory or enforced, and under which preconditions independently produced change sets may be integrated.

It does not replace Git, grant repository authority, define a distributed consensus protocol, or prove that code is correct. A file carries a snapshot of coordination state; real-time exclusion requires a live coordinator.

A workstate carrying Coordination records or events MUST declare this module. It MUST be required when active intents, leases, contracts, conflicts, or integration preconditions constrain the requested continuation; otherwise a receiver could incorrectly act on incomplete Core state.

## 2. Failure model

The module addresses:

1. **Physical clobbering:** changes overwrite the same bytes or apply to an unexpected base.
2. **Semantic clobbering:** text merges while assumptions, interfaces, behaviors, or invariants conflict.
3. **Coordination loss:** a relevant intent or decision reaches another actor too late.

Coordination reduces these risks by making claims inspectable. It cannot eliminate undisclosed scopes, incorrect semantic assertions, offline races, or faulty verification.

## 3. Manifest configuration

```json
{
  "id": "urn:awp:coordination",
  "version": "0.1.0",
  "required": false,
  "capabilities": ["intents", "scopes", "leases", "contracts", "change-sets"],
  "configuration": {
    "lease_enforcement": "advisory"
  }
}
```

`lease_enforcement` is `advisory` or `enforced`. Enforced mode MUST identify a live coordinator, its protected scope, and its current term or epoch. If that coordinator is unavailable, unverifiable, or does not cover a scope, affected leases are advisory.

The module SHOULD be optional in ordinary handoffs. A writer marks it required only when safe continuation depends on interpreting active coordination state.

## 4. Work intent

Before materially changing shared code, an actor SHOULD announce a work intent:

```json
{
  "id": "intent:agent-a-auth-refresh",
  "type": "work_intent",
  "module": "urn:awp:coordination",
  "actor": "actor:agent-a",
  "goal": "goal:oauth-refresh",
  "summary": "Change refresh-token rotation and its persistence path.",
  "status": "active",
  "base_revision": "git:91ab4e7",
  "scopes": ["scope:rotate-refresh", "scope:session-contract"],
  "expected_effects": ["effect:refresh-generation"],
  "preserves": ["invariant:no-plaintext-token-storage"],
  "expected_outputs": ["changeset:auth-refresh-v1"]
}
```

Statuses are `proposed`, `active`, `waiting`, `completed`, `withdrawn`, `abandoned`, and `superseded`.

An intent identifies goal, actor, base revision, expected duration, scopes, interfaces expected to change, invariants expected to remain true, dependencies, output, and verification where known. If actual work expands beyond announced scope, the actor SHOULD update the intent before proceeding when practical.

## 5. Coordination scope

A scope describes a physical or semantic region and intended access:

```json
{
  "id": "scope:rotate-refresh",
  "type": "coordination_scope",
  "module": "urn:awp:coordination",
  "kind": "symbol",
  "repository": "repo:application",
  "base_revision": "git:91ab4e7",
  "path": "src/auth/session.ts",
  "symbol": "rotateRefreshToken",
  "access": "write",
  "semantic_effects": ["behavior:refresh-token-rotation"]
}
```

Physical selectors include repository, revision, directory, file, syntax-tree node, symbol, configuration key, generated output, schema object, test, and fixture. Semantic selectors include public contract, behavior, invariant, state field, error semantics, lifecycle, performance property, security property, compatibility promise, and deployment surface.

Access modes are `observe`, `read`, `write`, `create`, `delete`, `propose_change`, `integrate`, and `verify`. A relied-upon read may conflict with a write. Line ranges are hints only and SHOULD NOT be the sole selector.

## 6. Overlap classification

A coordinator or peer compares a new intent with active intents and accepted, unintegrated change sets. It classifies overlap as:

- `none`;
- `informational`;
- `compatible` under stated assumptions;
- `ordered` with a required integration sequence;
- `negotiation_required`;
- `blocking`;
- `unknown` because scope information is insufficient.

Overlap analysis SHOULD consider dependency graphs, contracts, effects, and invariants in addition to path intersection. `unknown` is not equivalent to compatible.

```json
{
  "event_schema_version": "0.2",
  "module": "urn:awp:coordination",
  "kind": "overlap.detected",
  "event_id": "evt:overlap-1",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "parents": ["evt:intent-a", "evt:intent-b"],
  "occurred_at": "2026-09-03T20:20:00Z",
  "actor": "actor:coordinator",
  "payload": {
    "left": "intent:agent-a-auth-refresh",
    "right": "intent:agent-b-session-store",
    "classification": "negotiation_required",
    "shared_scopes": ["contract:session-store-v2"],
    "reason": "Both intents change refresh-generation semantics."
  }
}
```

## 7. Leases

Lease modes are:

- `advisory`: announces activity without exclusion;
- `shared_read`: promises relied-upon state remains stable;
- `shared_write`: permits coordinated writers under an accepted contract;
- `exclusive_write`: requests exclusive mutation of a scope;
- `integration_owner`: assigns combined integration responsibility.

A lease record MUST contain holder, scope, mode, start time, expiration time, status, conflict policy, coordinator identity, and coordinator term when enforced. Statuses are `requested`, `active`, `denied`, `released`, `expired`, `revoked`, and `superseded`.

Expired leases MUST NOT remain active. Long work SHOULD renew through heartbeat events. Conflicting work discovered after an advisory or disconnected period MUST be reconciled before integration.

A lease is coordination state, not filesystem, repository, deployment, or organizational authority.

## 8. Interface contracts

Actors working across a shared boundary SHOULD negotiate an interface contract before independent implementation.

Lifecycle:

```text
proposed -> negotiating -> accepted -> implemented -> verified
                    \-> superseded
```

A contract identifies owners, producers, consumers, previous and proposed revisions, schemas or signatures, states, errors, invariants, compatibility classification, migration or feature-flag strategy, tests, and adoption status per participant.

An actor MUST NOT claim conformance to a contract revision it has not implemented or verified. A revised accepted contract creates a new version and may make dependent intents or change sets stale.

## 9. Change sets

A change set is an integration candidate, not merely a patch:

```json
{
  "id": "changeset:auth-refresh-v1",
  "type": "change_set",
  "module": "urn:awp:coordination",
  "intent": "intent:agent-a-auth-refresh",
  "status": "ready",
  "base_revision": "git:91ab4e7",
  "artifacts": ["artifact:auth-refresh-patch"],
  "preconditions": [
    "contract:session-store-v2@2",
    "invariant:no-plaintext-token-storage"
  ],
  "effects": {
    "reads": ["session.refresh_generation"],
    "writes": ["session.refresh_generation"],
    "creates": ["error:generation_conflict"],
    "removes": [],
    "changes_behavior": ["refresh_token_rotation"],
    "preserves": ["invariant:no-plaintext-token-storage"]
  },
  "verification": ["execution:auth-tests-842"]
}
```

Preconditions may include repository revision, artifact digest, syntax fingerprint, record revision, contract revision, dependency state, invariant state, symbol presence, test baseline, toolchain, and schema version.

Before application or integration, every required precondition MUST be evaluated against the chosen base. Failure marks the change set `stale`; textual applicability does not override a failed semantic precondition.

Change-set statuses are `proposed`, `in_progress`, `ready`, `stale`, `integrating`, `integrated`, `failed`, `withdrawn`, and `superseded`. `ready` requires accepted contracts, satisfied dependencies and preconditions, resolved blocking conflicts, declared verification, and required review or authority. It does not mean integrated.

Effects are author claims and SHOULD be checked by static analysis, tests, review, or integration verification according to risk.

## 10. Integration plan and result

An integration plan identifies owner, base revision, exact change-set versions, order, contracts, verification, rollback, and required authority:

```json
{
  "id": "integration:session-v2",
  "type": "integration_plan",
  "module": "urn:awp:coordination",
  "owner": "actor:integration-agent",
  "base_revision": "git:91ab4e7",
  "change_sets": [
    "changeset:session-store-v2",
    "changeset:auth-refresh-v1",
    "changeset:session-tests-v2"
  ],
  "order": [
    "changeset:session-store-v2",
    "changeset:auth-refresh-v1",
    "changeset:session-tests-v2"
  ],
  "shared_contracts": ["contract:session-store-v2@2"],
  "verification": ["test:session-contract-v2", "test:auth-integration"],
  "rollback": "Revert the integration revision and restore contract revision 1."
}
```

The owner re-evaluates preconditions, resolves the ordered base, integrates, runs combined contract/invariant/behavior verification, and publishes a result. The result identifies exact inputs, base, resulting revision, transformations, manual resolutions, contract versions, verification outcomes, deviations, resulting artifact digests, and responsible actor.

Integration ownership does not grant authority beyond current permissions.

## 11. Resolution patterns

Recognized patterns include scope partition, contract first, ordered integration, compatibility adapter, feature isolation, rebase and re-derive, designated integration owner, and authorized human decision.

The chosen resolution, rationale, evidence, and accepted risk MUST be recorded. A textual merge tool cannot by itself resolve a semantic conflict.

## 12. Event kinds

Module event kinds use the `urn:awp:coordination` owner and these initial kinds:

- `intent.announced`, `intent.updated`, `intent.completed`, `intent.withdrawn`;
- `overlap.detected`;
- `lease.requested`, `lease.granted`, `lease.denied`, `lease.renewed`, `lease.released`, `lease.expired`, `lease.revoked`;
- `contract.proposed`, `contract.accepted`, `contract.revised`, `contract.verified`;
- `changeset.proposed`, `changeset.stale`, `changeset.rebased`, `changeset.ready`;
- `conflict.detected`, `conflict.resolved`;
- `integration.started`, `integration.completed`, `integration.failed`.

Private kinds use a controlled namespaced module ID rather than adding unregistered bare kinds to this module.

## 13. Reference sequence

```text
announce intents
      |
analyze overlap
      |
negotiate contract or ownership
      |
implement independently
      |
publish change sets
      |
recheck semantic preconditions
      |
integrate in declared order
      |
combined verification
      |
publish result and release leases
```

## 14. Relationship to Git

Git stores revisions, ancestry, commits, and patches and detects many byte-level conflicts. Coordination records intent before commit, relied-upon reads, semantic effects, interfaces, invariants, integration order, and combined verification.

Implementations SHOULD reference immutable Git revisions and patch artifacts when available. Branch, worktree, pull-request, and forge mappings belong to Git adapter profiles. A successful Git merge MUST NOT be treated as proof of semantic compatibility.

## 15. Failure and recovery

If an actor stops responding, leases expire; its intent remains historical and may be marked waiting or abandoned by an authorized coordinator. Unpublished changes are not assumed to exist. Published change sets remain inspectable and may be reassigned.

If a coordinator fails, actors may continue locally, but coordination state is potentially stale. Before integration they MUST refresh events when possible, recompute overlaps, verify coordinator term, and re-evaluate every precondition.

Network partitions make enforced leases unverifiable outside the coordinator's reachable guarantee. This version defines safe degradation to advisory behavior, not distributed consensus.

## 16. Conformance

A Coordination reader compares physical and semantic scopes, distinguishes lease state from authority, preserves contract versions and actor adoption, detects stale preconditions, and surfaces semantic conflicts even after a clean source-control merge.

A Coordination writer announces scope changes, records lease lifecycle, publishes change-set assumptions and effects, and records integration inputs and results. A Coordination implementation MUST also conform as a Core reader and Synchronization reader.



---


# AWP Security 0.1.0

**Module ID:** `urn:awp:security`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`; AWP Artifact `0.1.x` when `artifact-controls` is declared

## 1. Scope

Core requires safe interpretation and local authority checks. This module adds portable security metadata for classification, import assessment, secret scanning, physical redaction lineage, signatures, and encryption declarations.

Security metadata is evidence, not an instruction to trust content or weaken receiver policy.

A workstate using Security metadata MUST declare this module. It MUST be required when interpreting a registered signature, encryption, redaction, or handling profile is necessary for the receiver's declared continuation. Core safety rules still apply when this module is absent.

## 2. Threat model

A workstate may contain malicious, misleading, stale, or compromised records; prompt injection; executable artifacts; archive traversal; decompression bombs; forged authority; replayed events; secrets; personal data; and references that trigger external side effects.

AWP does not make untrusted content safe merely by structuring or signing it. Receivers apply current local policy and least authority.

## 3. Manifest security metadata

```json
{
  "module_data": {
    "urn:awp:security": {
      "classification": "private",
      "contains_secrets": false,
      "contains_personal_data": "unknown",
      "secret_scan": {
        "status": "passed",
        "scanned_at": "2026-09-03T20:14:00Z",
        "policy": "org.example/default-export",
        "scanner": "example-scanner/4.2"
      },
      "redaction_lineage": null,
      "signatures": []
    }
  }
}
```

The displayed object is the module-owned portion of a Core manifest. Security fields live under `module_data["urn:awp:security"]`.

Classification and privacy vocabularies may be organization-specific but private values MUST be namespaced. `contains_secrets` is `true`, `false`, or `unknown`. A writer MUST NOT use `false` when secret-scan status is `findings`, `not_run`, or `unknown`.

## 4. Import quarantine

Receivers SHOULD place newly imported workstates in local quarantine until they evaluate:

- origin and transport context;
- required modules and schemas;
- package-path and size safety;
- declared and verified integrity;
- classification and handling policy;
- active instructions and executables;
- authority, expiration, and revocation;
- requested external side effects.

Quarantine is receiver-owned state. A serialized assertion MAY describe the sender's handling state but MUST NOT disable receiver quarantine or grant trust.

## 5. Prompt injection and active content

Text in artifacts, summaries, claims, evidence, transcripts, extensions, and module data may contain instructions. Merely parsing, rendering, retrieving, verifying, or signing a workstate MUST NOT authorize execution.

Readers MUST distinguish descriptive content from an authorized requested action. Unknown modules and executable content MUST NOT run automatically. Module processors SHOULD be isolated according to risk.

## 6. External side effects

An imported task classified as `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, or `destructive` MUST NOT become ready or execute solely because the workstate requests it.

The receiver re-evaluates current identity, resource scope, authority source, conditions, expiration, revocation, confirmation requirements, and local policy. A receiver with greater access than the sender MUST avoid becoming a confused deputy.

## 7. Secrets and data minimization

Writers SHOULD use secret references instead of values:

```json
{
  "secret_ref": "secret://deployment/github-client-secret",
  "provider_hint": "organization-secret-store",
  "required_for": ["task:deploy"]
}
```

A reference does not authorize resolution. Exporters MUST apply their configured secret and data-loss-prevention policy to included event payloads, execution output, evidence, generated views, module data, and artifact paths. Scan status is `passed`, `findings`, `not_run`, or `unknown`. Passing is evidence of a check, not proof of absence.

Writers SHOULD omit irrelevant transcripts and personal data and support classification, audience, retention, and jurisdiction metadata. Omission must not be disguised by a stronger completeness claim.

## 8. Physical redaction lineage

Physical redaction creates a new workstate history lineage. It MUST:

- receive a new package or representation digest;
- identify the source workstate and source frontier where safe;
- declare that history was rewritten;
- state policy or reason where safe;
- replace removed records with non-sensitive tombstones when references remain;
- invalidate signatures covering removed bytes;
- remove sensitive values from views, indexes, paths, caches, and module data;
- avoid claiming byte-complete continuity.

Artifact tombstones follow AWP Artifact. Physical redaction is not ordinary semantic deletion.

## 9. Signatures and trust

Signatures may cover individual events, frontier manifests, snapshots, artifact manifests, module data, or complete packages. Signature metadata MUST identify algorithm, key identifier, coverage, canonicalization profile, signer, and verification status.

Trust dimensions remain independent:

- byte integrity;
- actor authentication;
- action authorization;
- evidentiary strength;
- processing safety.

A valid signature proves none of the other dimensions by itself.

AWP Security 0.1.0 does not select a normative canonicalization or signature algorithm. Implementations MUST NOT claim interoperable AWP signature conformance without naming an external or future registered signature profile.

## 10. Encryption

Encryption metadata may describe package-wide, module-level, artifact-level, or recipient-based protection. It MUST identify the encryption profile and protected scope without exposing keys or secret values.

Encryption does not replace minimal disclosure. Metadata remaining in plaintext, including paths, sizes, module names, actors, and timing, may itself be sensitive.

This version does not define a normative encryption profile.

## 11. Package and artifact safety

When Capsule or Artifact is used, processors MUST apply their traversal, normalization, size, decompression, integrity, executable-content, and retrieval rules. A signature over an unsafe archive does not make extraction safe.

## 12. Conformance

A Security reader evaluates and surfaces declared metadata without converting it into trust, validates registered security profiles it claims to support, and enforces receiver policy.

A Security writer minimizes sensitive data, reports scan and redaction state accurately, scopes signatures precisely, and never embeds credentials in locations or retrieval metadata.



---


# AWP Adapter Framework 0.1.0

**Status:** Informative framework  
**Payload module:** None

## 1. Purpose

Adapters map AWP modules to an external protocol, runtime, source-control system, or workflow without redefining AWP semantics. Each binding is versioned independently and declares which AWP family and module versions it supports.

An adapter is not automatically a payload module. It receives a module ID only if it introduces portable records or events that must survive outside the external system.

## 2. Binding requirements

A normative binding should specify:

- external system and versions;
- supported AWP modules and versions;
- identity mapping;
- lifecycle and status mapping;
- artifact and evidence retrieval;
- authority and authentication boundaries;
- ordering, retries, deduplication, and acknowledgement;
- lossless and lossy fields;
- streaming or delta behavior;
- errors and recovery;
- security considerations;
- conformance fixtures.

A binding MUST NOT treat external authentication as blanket AWP authority, invent verified claims from unverified external status, collapse concurrent Core events into silent last-write-wins, or claim lossless round trips when information is discarded.

## 3. Git binding shape

A future Git binding should map:

| AWP concept | Candidate Git representation |
|---|---|
| workstate base | repository ID plus immutable commit |
| work intent | branch, worktree, issue, or binding-owned note |
| coordination scope | path plus optional symbol/contract metadata |
| change set | commit range, patch, branch tip, or pull request |
| artifact version | blob ID plus AWP digest |
| integration result | merge/rebase commit and verification evidence |
| event reference | note, trailer, sidecar, or service record |

No single mapping is normative in 0.4.0. Branches and pull requests are forge conventions rather than universal Git objects. Git object IDs establish repository object identity, not semantic safety, actor authority, or AWP event identity.

## 4. A2A binding shape

A2A tasks may carry a workstate ID, checkpoint, requested continuation, and Capsule or wire representation as artifacts or data parts. A binding should map task lifecycle to AWP events without assuming the A2A message history is complete workstate history.

Material goals, constraints, decisions, claims, evidence, and outcomes should be promoted into typed AWP records. Authentication of an A2A peer does not automatically authorize external side effects.

## 5. MCP binding shape

An MCP server may expose the briefing, manifest, snapshot, events, module data, and artifacts as resources. Controlled tools may append events, create checkpoints, announce intents, or publish change sets.

Read access and mutation authority remain host-controlled. Resource text is untrusted data, and tool availability does not itself authorize a call.

## 6. Workflow and runtime bindings

A workflow adapter may map nodes, pending tasks, interrupts, retries, and native checkpoints into Operational or Exact Handoff data. It MUST still provide a semantic Core checkpoint for a portable handoff.

Private runtime state should use a namespaced module or artifact type and identify compatible runtime versions. Its presence must not make private chain-of-thought part of the portable contract.

## 7. Binding registry

A future registry entry should contain binding ID, version, publisher, external protocol range, AWP module ranges, specification URI, schemas, security profile, test vectors, and stability.

Private bindings use collision-resistant IDs. An unknown binding may be ignored only when every resulting module and field is optional and preserved or its loss disclosed.

