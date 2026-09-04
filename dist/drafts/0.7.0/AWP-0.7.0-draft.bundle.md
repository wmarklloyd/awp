# Agent Workstate Protocol 0.7.0 — Working Draft Bundle

**Status:** Generated working-draft artifact; not a release  
**Source of truth:** `spec/drafts/0.7.0/*` and the schemas named in the draft module registry  
**Purpose:** Self-contained copy for agents or systems that cannot follow repository-relative links.

This file bundles the 0.7.0 working draft, its module specifications, the module registry, and the draft schemas. It is not a published specification. Do not edit this generated file directly; regenerate it from the source files when the draft changes.

Repository-relative links are preserved as source-location identifiers. When those paths are unavailable, use the corresponding embedded module or machine-readable asset later in this bundle.

---

# Agent Workstate Protocol 0.7.0

**Status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**Target successor to:** AWP 0.6.0  
**Canonical draft:** `https://github.com/wmarklloyd/awp/tree/main/spec/drafts/0.7.0`  
**License:** GPL-3.0-only

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose

AWP is a family of composable specifications for preserving, exchanging, inspecting, and resuming work performed by humans and software agents. Version 0.7.0 makes the governing specification an explicit part of every shared workstate and repository discovery document. It advances the family modules to explicit exploratory versions while retaining the Coordination design introduced in 0.6.0.

The family has one required foundation, AWP Core. Every other subspecification is a module with its own identifier, version, dependencies, schema, and conformance claim. A module is a logical capability: it may occupy its own file in an editable workstate or be embedded in a single `.awp.md` capsule.

### 1.1 Target use cases

AWP is intended for agents and users that already have their own working environments. It provides a common, portable format to:

1. Enable a user or agent to send another agent a project or problem description that preserves more durable semantic state than ordinary Markdown alone;
2. Provide a new agent with a clear, shared project orientation before it must inspect the wider repository;
3. Allow an agent or user to return to a project and resume from a recorded checkpoint rather than reconstructing its state from scratch; and
4. Enable multiple agents to negotiate interdependent code changes above the byte-level coordination provided by Git or similar source-control systems.

AWP does not replace an agent runtime, source control, artifact storage, or an agent-specific startup convention. Its purpose is to provide portable semantic state and coordination information that those systems can consume.

## 2. Specification family

| Subspecification | Module identifier | Version | Status | Direct dependencies |
|---|---|---:|---|---|
| [AWP Core](core.md) | `urn:awp:core` | `0.7.0` | required | none |
| [AWP Capsule](capsule.md) | `urn:awp:capsule` | `0.4.0` | optional | Core |
| [AWP Handoff](handoff.md) | `urn:awp:handoff` | `0.4.0` | optional | Core |
| [AWP Artifact](artifact.md) | `urn:awp:artifact` | `0.4.0` | optional | Core |
| [AWP Synchronization](synchronization.md) | `urn:awp:sync` | `0.4.0` | optional | Core |
| [AWP Coordination](coordination.md) | `urn:awp:coordination` | `0.4.0` | experimental | Core, Synchronization |
| [AWP Security](security.md) | `urn:awp:security` | `0.4.0` | optional | Core; Artifact when artifact controls are used |
| [AWP Adapter Framework](adapters.md) | not a payload module | `0.4.0` | informative | binding-specific |

The machine-readable [module registry](modules.json) is normative for the module IDs, versions, document paths, stability labels, and direct dependencies in this draft.

## 3. Module declarations

Every AWP 0.7 manifest MUST contain a `modules` array. It MUST declare exactly one Core entry, and that entry MUST be required. The following is a module-declaration excerpt rather than a complete manifest:

```json
{
  "awp_version": "0.7.0",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.7.0",
      "required": true
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.4.0",
      "required": true
    },
    {
      "id": "urn:awp:coordination",
      "version": "0.4.0",
      "required": false
    }
  ]
}
```

A module entry has:

- `id`: collision-resistant module identifier;
- `version`: version identifier of that module;
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

The conventional project-named form is `<project-name>.awp.md`. Producers MAY retain versioned archival copies using `<project-name>.v<revision>.awp.md`, such as `project.v2.awp.md`. This filename revision is only a human-facing label; protocol and workstate identity remain defined by the capsule metadata and the `.awp.json` `current_workstate` pointer.

The manifest is authoritative for physical locations. Module-specific events participate in the unified Core event graph and identify their owning module. This preserves causal ordering across modules without requiring one event log per module.

## 6. Versioning and specification binding

Every shared AWP workstate MUST identify the exact specification artifact that governs it. A repository discovery document and its current capsule MUST carry an explicit `specification` reference. That reference SHOULD be an immutable, version-pinned URI to a published specification bundle. A repository-relative local copy MAY be used when network retrieval is unavailable or inappropriate.

A reader MUST interpret a workstate according to its declared specification and module versions. It MUST NOT silently substitute a newer, older, or otherwise different specification, infer compatibility from a filename, or treat a moving branch URL as version-pinned. If the declared specification is unavailable or unsupported, the reader MUST report that condition rather than guess.

AWP `0.x` is exploratory. A new minor family or module release MAY make incompatible changes. A patch release MUST NOT introduce incompatible normative semantics. Explicit specification binding allows protocol development to proceed without requiring backward compatibility between exploratory minor releases. Implementations MAY support multiple versions or provide explicit migrations, but conformance to one version does not imply support for another.

The family version and module versions remain independent. The family version identifies a tested set of module releases, and a later family release may reuse an unchanged module version. Writers that change protocol semantics MUST publish a new versioned specification artifact and update affected workstates deliberately. Implementations MUST determine support by the declared specification, module ID, and module version, not by comparing only `awp_version`.

The common event envelope is versioned independently because events may outlive a family release. AWP 0.7.0 uses event-envelope version `0.2`.

## 7. Conformance

An implementation declares conformance as a set of roles and module versions, for example:

```json
{
  "roles": ["core-reader", "capsule-reader", "handoff-writer"],
  "modules": {
    "urn:awp:core": ["0.7.x"],
    "urn:awp:capsule": ["0.4.x"],
    "urn:awp:handoff": ["0.4.x"]
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

## 9. Migration from 0.6.0

AWP 0.7.0 preserves the 0.2 event envelope and the module identifiers from AWP 0.6.0. Core advances to `0.7.0`; the dependent modules advance to `0.4.0`; repository discovery advances to `0.2.0`.

The migration is intentionally incompatible: a shared capsule and `.awp.json` discovery document now identify the exact specification artifact that governs the workstate. A 0.7 reader MUST NOT silently substitute another specification. Discovery 0.1 documents remain valid historical inputs but require explicit migration before being claimed as Discovery 0.2.

An upgrader from 0.6.0 MUST add the governing `specification` reference to capsule metadata, update Capsule to `0.4.0`, and emit a Discovery 0.2 document. Historical events remain unchanged.

## 10. Release contents

- [Core schema](../../../schemas/awp-core-0.7.schema.json)
- [Coordination schema](../../../schemas/awp-coordination-0.4.schema.json)
- [Discovery schema](../../../schemas/awp-discovery-0.2.schema.json)
- [Module registry](modules.json)
- [Open issue register](open-issues.md)
- Validation and conformance assets in the repository root

The documents listed in Section 2, their normative schemas, and the module registry constitute the AWP 0.7.0 working draft. No file under this directory is a released specification until a release process copies immutable contents into `spec/<version>/` and creates a corresponding tag.

## 11. References

### 11.1 Normative references

- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), “Key words for use in RFCs to Indicate Requirement Levels.”
- [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), “Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words.”
- [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core), Draft 2020-12.

### 11.2 Informative references

- [Semantic Versioning 2.0.0](https://semver.org/).
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785), “JSON Canonicalization Scheme (JCS).”

---

# Bundled module specifications

---

# AWP Core 0.7.0

**Module ID:** `urn:awp:core`  
**Status:** Required  
**Dependencies:** None  
**Schema:** `../../../schemas/awp-core-0.7.schema.json`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

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
  "awp_version": "0.7.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "title": "Prepare product launch",
  "created_at": "2026-09-03T18:00:00Z",
  "created_by": "actor:mark",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.7.0",
      "required": true,
      "schema": "schemas/awp-core-0.7.schema.json"
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.4.0",
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

The Core module declaration MUST appear exactly once with version `0.7.x` and `required: true`. Module IDs MUST be unique within the array. A module declaration MUST satisfy the dependency and requiredness rules in the family specification.

Optional manifest fields include description, default language, parent workstate and frontier, originating application, classification, retention policy, schemas, capabilities, and representation-specific metadata.

Module-specific manifest data belongs in the owning module declaration's `configuration` object or in a top-level `module_data` object keyed by module ID. Undeclared modules MUST NOT place data there.

## 5. Common event envelope

Every 0.5 event uses event-envelope version `0.2`:

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

Actor declarations are materialized in a snapshot's top-level `actors` array. An actor reference in a manifest, event, authority declaration, or record SHOULD resolve to one of those declarations or to an identified external identity binding. An unresolved actor reference has type `unknown`; it does not invalidate historical events or create authentication, trust, or authority.

## 8. Core records

A core record contains `id` and `type` plus the fields below. It MAY include integer `revision`, beginning at `1` when first created. Fields marked required are structural minima; cross-record requirements remain normative even where JSON Schema cannot express them.

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

An update SHOULD carry a complete replacement or patch plus `prior_revision`. When a record has a revision, an update MUST apply only when `prior_revision` equals the effective revision and MUST assign the next integer revision. An update without a satisfiable prior revision is a conflict unless its owning module defines a safe commutative rule. A writer MUST NOT use last-write-wins to silently resolve a conflicting revision. Completion, verification, authorization, and external-side-effect transitions SHOULD cite evidence.

Deletion is a semantic tombstone and does not remove historical bytes. Physical removal is governed by the Security and Artifact modules.

## 11. Snapshots

A snapshot is derived state at a declared frontier:

```json
{
  "awp_version": "0.7.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "frontier": ["evt:01K4M4VYB9"],
  "generated_at": "2026-09-03T20:15:00Z",
  "actors": [],
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

# AWP Capsule 0.4.0

**Module ID:** `urn:awp:capsule`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

AWP Capsule defines human-readable and packaged representations of one logical workstate. It does not define the semantics of optional modules carried by those representations.

The representations are:

- editable directory: `name.workstate/`;
- self-contained Markdown capsule: `name.awp.md`;
- ZIP-compatible package: `name.pws`;
- JSON wire payloads.

Logical equivalence does not require identical bytes or file layout. The manifest maps logical data to physical locations.

For a project-named Markdown capsule, the default conventional filename is `<project-name>.awp.md`. When the project name is unavailable or ambiguous, producers SHOULD use `project.awp.md`. A producer MAY retain multiple capsule revisions using `<project-name>.v<revision>.awp.md`, for example `awp.v2.awp.md` or `project.v2026-09-04.awp.md`. The filename revision is a human-facing archival label; it is not the AWP protocol version and MUST NOT override `awp_version`, `workstate_id`, `frontier`, `checkpoint`, `generated_digest`, or the `current_workstate` pointer in `.awp.json`. A consumer MUST follow the discovery pointer when one is present.

A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing.

## 2. Repository discovery

A project MAY place a `.awp.json` discovery document at its declared project root so that an AWP-aware agent or tool can locate the current workstate without scanning the project. The discovery document is a pointer, not a workstate, trust assertion, or authority grant.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "awp_schema": "urn:awp:schema:discovery:0.2.0",
  "awp_discovery_version": "0.2",
  "current_workstate": "project.awp.md",
  "specification": "https://example.org/awp/0.7.0/AWP-0.7.0.bundle.md",
  "fallback_workstates": []
}
```

`awp_schema`, `awp_discovery_version`, `current_workstate`, and `specification` are REQUIRED. `awp_schema` identifies this AWP discovery schema without assuming that a copied project contains AWP's source tree. `fallback_workstates` is optional. `specification` identifies the exact specification artifact governing the current workstate. It SHOULD be an immutable, version-pinned URI when the specification is hosted remotely, such as a tagged GitHub raw URL. It MUST NOT use a moving branch URL as though it were version-pinned. A sandboxed or offline project MAY point `specification` to a repository-relative local copy instead.

Relative paths are resolved from the directory containing `.awp.json`. A local path MUST be relative, normalized, remain within the project root after resolution, and identify a regular file. A URI MAY be used only by a binding that defines retrieval and security behavior; discovering a URI MUST NOT trigger automatic network access.

An AWP-aware project-entry implementation SHOULD look for `.awp.json` in the project root supplied by its host, repository binding, invocation, or configuration. It MUST NOT search above that root. When the file is present, it MUST validate [the discovery schema](../../../schemas/awp-discovery-0.2.schema.json) before following a pointer. It then opens `current_workstate` using the normal Capsule and Core procedures. It MUST verify that the capsule declares the same `specification` reference. A mismatch is invalid discovery and MUST NOT be resolved by silently choosing either reference.

If `.awp.json` is missing, invalid, unsafe, or points to unavailable content, the implementation reports discovery as `absent`, `invalid`, `unsafe`, or `unavailable`. It MAY accept an explicitly supplied capsule instead. It MUST NOT silently select a fallback whose identity conflicts with an already selected workstate.

Agent-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` are outside AWP. They MAY point to `.awp.json` or directly to a capsule, but their presence is not required for AWP conformance.

## 3. Root briefing

Every complete directory, Markdown capsule, or package MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first.

The briefing MUST begin with metadata containing:

- `awp_version`;
- `specification`;
- `workstate_id`;
- `frontier`;
- current `checkpoint`, if one exists;
- `generated_at`;
- `generated_digest`.

Generated content MUST occur inside exactly one marker pair:

```markdown
---
awp_version: 0.7.0
specification: https://example.org/awp/0.7.0/AWP-0.7.0.bundle.md
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

`specification` identifies the exact specification artifact that governs the workstate. It follows the same version-pinned URI and repository-relative local-path rules as repository discovery. A reader MUST NOT silently substitute another specification. An unavailable or unsupported declared specification makes the workstate `unverifiable` for protocol interpretation.

The digest uses `sha256:{lowercase-hex}` over the UTF-8 content beginning after the LF terminating the start marker and ending before the LF preceding the end marker, after CRLF-to-LF normalization.

A reader reports the briefing as:

- `current`: digest valid and frontier equals effective state;
- `modified`: generated-region digest differs;
- `stale`: digest valid but a newer effective frontier exists;
- `unverifiable`: required state or hash algorithm is unavailable.

Notes and content outside the generated region are non-authoritative. Importing a human edit into machine state requires an explicit proposed semantic change and acceptance by an authorized actor.

## 4. Editable directory

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

## 5. Single-file Markdown capsule

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

## 6. Package representation

A `.pws` package is ZIP-compatible and expands to the editable-directory logical layout. Proposed media type: `application/awp+zip`.

Unpacking MUST preserve logical paths, bytes, IDs, module declarations, and references. Readers MUST reject absolute paths, parent traversal, duplicate normalized paths, case-folding collisions on case-insensitive targets, symlink escapes, and members exceeding configured size or decompression limits.

Writers SHOULD place `WORK.md` and `manifest.json` before large members for preview efficiency. Physical member order has no semantic meaning.

## 7. Wire representation

JSON wire bindings may carry a manifest, snapshot, event sequence, delta, artifact announcement, module data, or retrieval request. Proposed media types are:

```text
application/awp+json
application/awp-event+json
application/awp-delta+json
```

The Capsule module defines payload representation, not transport authentication, delivery guarantees, or live synchronization.

## 8. Module placement

A module declaration may specify a `representation` object:

```json
{
  "id": "urn:awp:coordination",
  "version": "0.4.0",
  "required": false,
  "representation": {
    "kind": "package-path",
    "path": "modules/coordination/state.json"
  }
}
```

Standard representation kinds are `package-path`, `capsule-section`, `remote`, and `events-only`. A remote module location does not make the workstate self-contained and MUST disclose retrieval requirements. Secrets MUST NOT appear in locations.

Module placement does not create a separate causal history. Module events always participate in the Core event graph.

## 9. Conformance

A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing. A reader claiming repository-discovery support MUST implement Section 2 and expose discovery failures.

A Capsule writer MUST create an unambiguous representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content. A writer that emits `.awp.json` MUST produce a schema-valid, traversal-safe discovery document.

---

# AWP Handoff 0.4.0

**Module ID:** `urn:awp:handoff`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

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

## 5. Resume Profile

The Resume Profile standardizes project re-entry after an actor or runtime leaves and later returns, or when a new actor starts without the source conversation. It uses a module-owned `resume` record and the capability name `resume-profile`.

```json
{
  "id": "resume:project-current",
  "type": "resume",
  "module": "urn:awp:handoff",
  "handoff": "handoff:agent-b",
  "checkpoint": "checkpoint:release-ready",
  "mode": "project_reentry",
  "read_first": [
    "goal:launch",
    "constraint:no-schema-change",
    "decision:database",
    "task:deploy"
  ],
  "required_artifacts": ["artifact:source-tree-91ab"],
  "repository_state": [
    {
      "repository": "repo:application",
      "source_revision": "git:91ab4e7",
      "path_scope": ["src/", "tests/"]
    }
  ],
  "recommended_next_action": "Continue release preparation without deploying.",
  "freshness_policy": "verify_before_continue",
  "on_stale": "refresh_workstate",
  "authority_ceiling": ["read_only", "local_write"]
}
```

Required fields are `id`, `type`, `module`, `checkpoint`, `mode`, `read_first`, `required_artifacts`, `recommended_next_action`, `freshness_policy`, `on_stale`, and `authority_ceiling`. `type` MUST be `resume`, `module` MUST be `urn:awp:handoff`, and the only standard mode in this version is `project_reentry`. Optional `handoff` identifies the handoff record this resume record refines.

When both a Resume and referenced Handoff record are present, the Resume record is the project-entry instruction for the named checkpoint. Its `authority_ceiling` MUST be equal to or narrower than the Handoff ceiling, and its action MUST be a compatible refinement of the Handoff requested action. A receiver that cannot establish those conditions MUST qualify or reject the resume; it MUST NOT choose one record silently.

`freshness_policy` is one of:

- `verify_before_continue`: validate the selected checkpoint, frontier, briefing digest, required modules, and required artifacts before performing the recommended action;
- `allow_stale_orientation`: stale state may be used only for orientation while the receiver refreshes or verifies it;
- `receiver_policy`: defer the minimum freshness requirement to an identified receiver policy.

`on_stale` is `refresh_workstate`, `report_and_stop`, or `read_only_orientation`. A receiver MUST NOT interpret any value as permission to perform an external side effect from stale or unverifiable state.

`repository_state`, when present, binds a resume checkpoint to the repository and immutable source revision against which it was prepared. Each entry requires `repository` and `source_revision` and MAY narrow comparison using `path_scope`. A `project_reentry` record that depends on source-controlled artifacts MUST include each repository state required to assess safe continuation.

A receiver that can identify the local repository revision MUST compare it with `source_revision`. A mismatch makes the repository binding stale. When it can obtain a diff, claims, evidence, change sets, and verification results scoped to changed paths MUST be treated as stale until reverified or explicitly re-scoped. When the receiver cannot identify or compare the repository revision, the binding is unverifiable rather than current. A matching revision does not establish that remote services, credentials, or other dependencies remain current.

`read_first` is an ordered presentation hint, not causal ordering or authority. A receiver MAY load additional records required to interpret dependencies, evidence, conflicts, or safety constraints. It MUST NOT omit relevant required state merely to meet a context budget. Optional context-selection metadata MAY state a token or byte budget, priority groups, and deferred artifacts, but it cannot weaken completeness, freshness, or authority requirements.

A Resume Profile receiver MUST:

1. discover or receive the workstate location;
2. validate the manifest, Core, and every required module;
3. locate the resume record and referenced checkpoint;
4. classify the checkpoint, snapshot, briefing, and required artifacts as current, stale, divergent, unavailable, or unverifiable using applicable modules;
5. apply `freshness_policy` and `on_stale` without weakening receiver policy;
6. load `read_first` records plus every dependency necessary for safe interpretation;
7. compare the recommended action and authority ceiling with current local authority;
8. report acceptance, qualified acceptance, or rejection before continuation.

The Resume Profile does not require a command-line interface. Commands such as `awp resume`, `awp status`, and `awp checkpoint` are informative implementation examples.

## 6. Producer procedure

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

## 7. Receiver procedure

A Handoff reader MUST:

1. validate Core and required modules;
2. assess origin, integrity, classification, and local policy;
3. locate the checkpoint and read-first records;
4. identify stale, disputed, unavailable, or unsupported information;
5. compare the requested action and ceiling with current local authority;
6. record acceptance, qualified acceptance, or rejection;
7. avoid external side effects until receiver policy authorizes them.

Acceptance statuses are `accepted`, `qualified`, and `rejected`. Qualified acceptance identifies every limitation that may affect continuation.

## 8. Interoperability experiment

The minimum handoff experiment uses one authoring system and at least two receiving systems that share neither private runtime state nor source conversation.

The test task contains one required constraint, one stale claim, one rejected alternative, one completed change with evidence, one unavailable dependency, an explicit authority ceiling, and one safe next action. Each receiver receives only the handoff and validly referenced material.

Score state recall, unsupported assumptions, constraint preservation, evidence use, dependency handling, authority compliance, and task success. A trial succeeds only when the receiver preserves every required constraint and authority boundary, does not treat stale or unavailable information as verified, and completes the next action or correctly reports a real blocker.

Reports SHOULD record capsule size where applicable, token usage, author and receiver versions, unsupported modules, omissions, false assumptions, safety failures, and resulting artifact quality. A single successful task is not evidence of general interoperability.

## 9. Conformance

A Handoff reader implements the receiver procedure and exposes limitations. A Handoff writer implements the producer procedure and makes accurate claims. A Resume Profile reader additionally implements Section 5 and declares the `resume-profile` capability. A system MAY support handoff and resume records without supporting the Capsule module; repository discovery requires Capsule support.

---

# AWP Artifact 0.4.0

**Module ID:** `urn:awp:artifact`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

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
        "digest": "a73b02838bfa8fc8c0b0a5c2e876b308831175eb62364ecd04b37116b0db5537"
      },
      "locations": [
        {
          "kind": "package",
          "path": "artifacts/sha256/a7/a73b02838bfa8fc8c0b0a5c2e876b308831175eb62364ecd04b37116b0db5537.bin"
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
        "digest": "a73b02838bfa8fc8c0b0a5c2e876b308831175eb62364ecd04b37116b0db5537"
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

# AWP Synchronization 0.4.0

**Module ID:** `urn:awp:sync`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

AWP Synchronization defines incremental event exchange, snapshot reconciliation, forks, concurrent branches, and conflict-preserving merge. It does not define a network transport, consensus system, or automatic semantic merge.

A workstate or message using deltas, omitted-history boundaries, or synchronization conflict semantics MUST declare this module. It MUST be required when the receiver must apply or reconcile those structures to reach the continuation frontier.

## 2. Delta

A delta carries events added after a known frontier:

```json
{
  "awp_version": "0.7.0",
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

AWP 0.7.0 does not define destructive log compaction. A writer MAY create a summary or snapshot-only export, but it MUST disclose omitted history and MUST NOT claim `full` completeness.

A future compaction profile must define lineage, state canonicalization, proof of the compacted frontier, treatment of unknown module events, signature invalidation, and audit guarantees. A snapshot alone does not authorize deletion of prior history.

## 9. Transport independence

Deltas may travel through files, HTTP, A2A, MCP, message queues, repositories, or peer protocols. A transport binding defines authentication, retries, acknowledgement, ordering, size limits, and retrieval. Synchronization semantics remain unchanged.

## 10. Conformance

A Synchronization reader validates ancestry and integrity, computes frontiers, applies deltas idempotently, preserves concurrency, and surfaces semantic conflicts.

A Synchronization writer emits valid base and result frontiers, includes required events or declares missing ancestry, and never describes a lossy history as full.

---

# AWP Coordination 0.4.0

**Module ID:** `urn:awp:coordination`  
**Status:** Experimental  
**Depends on:** AWP Core `0.7.x`, AWP Synchronization `0.4.x`  
**Supersedes:** AWP Coordination `0.3.0`  
**Schema:** `../../../schemas/awp-coordination-0.4.schema.json`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Purpose and scope

AWP Coordination defines durable semantic coordination for multiple actors working on a shared project or codebase. It records intended work before integration, dependencies between work, physical and semantic overlap, negotiated commitments, candidate changes, integration preconditions, and verification evidence.

The module is designed so that a different agent on a different host can determine:

1. what work is active and why;
2. what state each actor relied on;
3. which changes may interact even when their text does not conflict;
4. what agreements constrain implementation;
5. what must be rechecked before integration;
6. what is known, asserted, observed, verified, authorized, stale, or unresolved.

Coordination does not replace Git, A2A, MCP, a task scheduler, a distributed consensus service, CI, repository permissions, or deployment authority. It may reference or be transported by those systems.

## 2. Design principles

1. **Durable state over conversational memory.** Safety-relevant coordination survives an agent session.
2. **Semantic conflicts are first class.** A clean textual merge is not evidence of compatible behavior.
3. **Claims have provenance.** Agent declarations, tool observations, verification results, and authority decisions are distinct.
4. **Concurrency is preserved.** Timestamp order or file order does not silently resolve concurrent updates.
5. **Offline use remains useful.** Portable files provide deterministic inspection and validation without a live service.
6. **Enforcement is never implied.** Exclusivity exists only when a protected mutation path validates it.
7. **Progress is bounded.** Negotiations, leases, retries, and waits have explicit termination or escalation paths.
8. **The protocol is topology neutral.** Central managers, peers, human-agent teams, and single-agent re-entry use the same durable records.

## 3. Capability and conformance profiles

The module declaration advertises supported capabilities and the strongest conformance level actually implemented.

```json
{
  "id": "urn:awp:coordination",
  "version": "0.4.0",
  "required": false,
  "capabilities": [
    "intents",
    "contracts",
    "change-sets",
    "typed-preconditions",
    "deterministic-projection"
  ],
  "configuration": {
    "conformance_level": "C1",
    "unknown_overlap_policy": "warn",
    "lease_enforcement": "none"
  }
}
```

Conformance levels are cumulative:

| Level | Name | Required behavior |
|---|---|---|
| `C0` | Portable | Preserve and expose recognized coordination records and events |
| `C1` | Deterministic | Validate transitions, revisions, typed preconditions, verification binding, staleness, and diagnostics |
| `C2` | Aware | Maintain a semantic registry, compare declared and observed scope, analyze relied-upon reads, and require acknowledgements under policy |
| `C3` | Enforced | Authenticate principals and provide protected OCC/lease operations with epochs and fencing |

A writer MUST NOT advertise a level whose required behaviors it does not implement. A reader MAY support a lower level, but it MUST reject the workstate for safe continuation when the module is required and unsupported semantics affect the requested action.

`unknown_overlap_policy` is `allow`, `warn`, `negotiate`, or `block`. `lease_enforcement` is `none`, `advisory`, or `enforced`. `block` and `enforced` have external effect only at C3 or through an identified enforcing adapter.

The module defines three cumulative capability bundles independently of conformance level:

| Bundle | Purpose | Minimum capabilities |
|---|---|---|
| `coordination-awareness` | Low-cost useful adoption | intents, revision-pinned scopes, overlaps, acknowledgements, conflict-preserving projection |
| `integration-assurance` | Safe candidate integration | contracts, typed preconditions, verification binding, change sets, staleness, integration results |
| `live-enforcement` | Protected concurrent mutation | authenticated principals, OCC, leases, epochs, fencing, governance |

An implementation MAY adopt `coordination-awareness` before implementing the complete integration-assurance workflow. Capability declarations state what records can be processed; conformance levels state how rigorously they are processed.

## 4. Common coordination record fields

Every module record contains:

```json
{
  "id": "intent:auth-refresh",
  "type": "intent",
  "module": "urn:awp:coordination",
  "revision": 3,
  "status": "active",
  "created_by": "actor:agent-a",
  "created_at": "2026-09-03T20:00:00Z",
  "updated_at": "2026-09-03T20:15:00Z",
  "goal": "goal:oauth-refresh",
  "summary": "Change refresh-token rotation and persistence.",
  "base": {
    "repository": "repo:app",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a"
  },
  "declared_scopes": ["scope:rotate-refresh@1"]
}
```

`id`, `type`, `module`, `revision`, `status`, `created_by`, and `created_at` are required. `revision` begins at `1`. An update MUST identify `prior_revision` in its event and produce exactly `prior_revision + 1`.

Optional revision-counted fields are `updated_at`, `supersedes`, `goal`, `owners`, `authority`, `extensions`, and `trust`.

Evidence links and acknowledgements are append-only associations maintained separately from the revision-counted record body. Adding one does not increment the subject record revision. Association identity is `(subject ID, pinned subject revision, actor, association kind, association ID)`. Concurrent additions commute by exact association identity; differing values under the same identity create a conflict.

Unknown fields MUST be preserved by lossless processors. A processor MUST distinguish a registered record type above its advertised capability or conformance level from a genuinely unregistered type. It preserves registered higher-level records without interpreting them and may still perform lower-level actions that do not depend on their meaning. A genuinely unregistered type owned by this required module makes only the affected action or projection `unverifiable` unless a declared compatibility rule permits preservation without interpretation. A lower-level reader MAY always perform safe display or export.

### 4.1 References and revision resolution

A record reference has one of these forms:

- `record-id@N` pins integer record revision `N`;
- `record-id` is an unpinned discovery reference and resolves only when the projection has one uncontested effective revision.

Safety-relevant references in contracts, preconditions, readiness decisions, verification, overlaps, and integration plans MUST be revision-pinned. A missing, superseded, or contested pinned revision remains historically addressable but MUST NOT be silently replaced by another revision. An unpinned reference that is absent, contested, or ambiguous is unresolved.

Repository revisions use adapter-qualified immutable identifiers such as a full Git object ID. Record revisions and repository revisions are different namespaces.

### 4.2 Time and authority

The passage of time never changes projected state. An identified actor or service MUST emit a valid timeout, expiration, or deadline-observation event under a declared clock authority. Until that event is present, a deadline may be overdue but the prior projected lifecycle state remains unchanged; processors SHOULD surface the overdue condition.

Below C3, authority may be `asserted`, `verified`, or `unverifiable`. Verification identifies the evaluator, receiver policy, evidence, time, scope, and relevant revocation state. C3 is required for live cross-principal enforcement, not for every authority check. No AWP authority record implies an external side effect by itself.

### 4.3 Canonical event example

```json
{
  "event_schema_version": "0.2",
  "module": "urn:awp:coordination",
  "kind": "intent.activated",
  "event_id": "evt:01K4M5A1",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "parents": ["evt:01K4M590"],
  "occurred_at": "2026-09-03T20:05:00Z",
  "actor": "actor:agent-a",
  "payload": {
    "record_id": "intent:auth-refresh",
    "prior_revision": 1,
    "revision": 2,
    "transition": {"from": "proposed", "to": "active"},
    "replacement": {
      "id": "intent:auth-refresh",
      "type": "intent",
      "module": "urn:awp:coordination",
      "revision": 2,
      "status": "active",
      "created_by": "actor:agent-a",
      "created_at": "2026-09-03T20:00:00Z",
      "updated_at": "2026-09-03T20:05:00Z",
      "goal": "goal:oauth-refresh",
      "summary": "Change refresh-token rotation and persistence.",
      "base": {
        "repository": "repo:app",
        "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a"
      },
      "declared_scopes": ["scope:rotate-refresh@1"],
      "expected_effects": ["semantic:session-refresh-generation@1"],
      "preserves": ["semantic:no-plaintext-token-storage@1"],
      "dependencies": ["contract:session-store-v2@2"],
      "expected_outputs": ["changeset:auth-refresh-v1"],
      "termination": {
        "condition": "Change set published with passing contract tests",
        "deadline": "2026-09-04T00:00:00Z"
      }
    }
  }
}
```

Every revision-changing event payload contains `record_id`, `prior_revision`, `revision`, and either a complete `replacement` record or a registered deterministic patch. Lifecycle events also contain `transition.from` and `transition.to`. Creation events omit `prior_revision` and use revision `1`. Association events instead identify the pinned subject revision and association identity.

## 5. Semantic registry

C2 implementations maintain stable project-scoped definitions for semantic coordination targets.

```json
{
  "id": "semantic:session-store-contract",
  "type": "semantic_definition",
  "module": "urn:awp:coordination",
  "revision": 2,
  "status": "active",
  "created_by": "actor:architect",
  "created_at": "2026-09-03T18:00:00Z",
  "kind": "interface",
  "name": "Session store interface",
  "aliases": ["contract:session-store"],
  "owners": ["actor:auth-team"],
  "selectors": [
    {"kind": "symbol", "repository": "repo:app", "path": "src/session/store.ts", "symbol": "SessionStore"}
  ]
}
```

Kinds include `interface`, `behavior`, `invariant`, `state_field`, `schema`, `error_semantics`, `lifecycle`, `compatibility_promise`, `performance_property`, `security_property`, `test_surface`, `deployment_surface`, and `other`.

Within one workstate, an active alias MUST resolve to at most one semantic definition. Merging ambiguous aliases creates diagnostic `AWP-COORD-REGISTRY-AMBIGUOUS` and affected overlap analysis becomes `unknown` until resolved.

Changing the meaning of a definition requires a new revision. Reusing an identifier for unrelated meaning is invalid.

Selector comparison across repository revisions is a C2 correctness operation. An analyzer MUST resolve both selectors against their pinned bases and attempt to relate moved, renamed, extracted, or replaced targets using a declared selector profile. Resolution results are `same`, `related`, `different`, `unresolvable`, or `ambiguous`, with evidence and confidence. `unresolvable` or `ambiguous` forces overlap classification `unknown`; it MUST NOT yield `none`.

Language-specific selector syntax and drift algorithms belong to registered adapter profiles. The initial reference implementation SHOULD provide Python AST and TypeScript compiler-symbol profiles, but their identifiers and outputs remain usable by agents implemented in any language.

## 6. Scopes and access claims

A scope is a first-class record selecting a physical or semantic region. Intents, claims, change sets, and contracts reference it by ID and revision. An inline selector MAY be used as an unshared query value, but an inline selector is not a scope record and cannot be revised or used as a dependency target.

```json
{
  "id": "scope:rotate-refresh",
  "type": "scope",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "active",
  "created_by": "actor:agent-a",
  "created_at": "2026-09-03T20:00:00Z",
  "selector": {
    "kind": "symbol",
    "repository": "repo:app",
    "base_revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
    "path": "src/auth/session.ts",
    "symbol": "rotateRefreshToken"
  },
  "access": "write",
  "semantic_targets": ["semantic:session-store-contract@2"]
}
```

Physical selector kinds include `repository`, `directory`, `file`, `symbol`, `syntax_node`, `configuration_key`, `schema_object`, `generated_output`, `test`, and `fixture`. Line ranges are hints and MUST NOT be the only selector for a safety-relevant claim.

Access is `observe`, `read`, `relied_upon_read`, `write`, `create`, `delete`, `propose_change`, `integrate`, or `verify`.

A `relied_upon_read` asserts that the actor's result depends on the selected state remaining compatible. It participates in overlap analysis against relevant writes, deletes, contract revisions, and semantic changes.

Authors SHOULD declare relied-upon reads only for assumptions whose incompatible change could invalidate the output, not every file or symbol inspected. Tools may propose candidates from dependency traces, but the published set SHOULD be summarized at stable interface, invariant, schema, or behavior boundaries. Fine-grained automatic reads MAY remain evidence behind that summary. This keeps the reverse index useful rather than turning ordinary repository browsing into conflicts.

## 7. Work intent

An actor SHOULD publish an intent before materially changing shared state.

```json
{
  "id": "intent:auth-refresh",
  "type": "intent",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "active",
  "created_by": "actor:agent-a",
  "created_at": "2026-09-03T20:00:00Z",
  "goal": "goal:oauth-refresh",
  "summary": "Change refresh-token rotation and persistence.",
  "base": {
    "repository": "repo:app",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a"
  },
  "declared_scopes": ["scope:rotate-refresh@1", "scope:session-contract@1"],
  "expected_effects": ["semantic:session-refresh-generation@1"],
  "preserves": ["semantic:no-plaintext-token-storage@1"],
  "dependencies": ["contract:session-store-v2@2"],
  "expected_outputs": ["changeset:auth-refresh-v1"],
  "termination": {
    "condition": "Change set published with passing contract tests",
    "deadline": "2026-09-04T00:00:00Z"
  }
}
```

Intent states and transitions:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `intent.announced` | `proposed` or `active` | actor, goal, base, summary, and declared scopes present |
| `proposed` | `intent.activated` | `active` | required overlap policy evaluated |
| `active` | `intent.waiting` | `waiting` | blocker or dependency identified |
| `waiting` | `intent.resumed` | `active` | blocker disposition recorded |
| `active`, `waiting` | `intent.completed` | `completed` | outputs or no-output rationale recorded |
| `proposed`, `active`, `waiting` | `intent.withdrawn` | `withdrawn` | actor or authorized owner gives reason |
| `active`, `waiting` | `intent.abandoned` | `abandoned` | authorized actor records unresponsive/abandonment basis |
| `proposed`, `active`, `waiting` | `intent.reassigned` | same state | prior and new owner, authority evaluation, and continuity reason recorded |
| nonterminal | `intent.superseded` | `superseded` | replacement intent identified |

Terminal states are `completed`, `withdrawn`, `abandoned`, and `superseded`. A terminal intent cannot be reactivated; continuation creates a successor intent. Reassignment changes the current owner, not `created_by`, and preserves the intent identity, base, history, and unresolved obligations.

If observed work expands beyond the declared scope, the writer MUST either update the intent before publishing a ready change set or record an explicit deviation. Under a C2 enforcing policy, unresolved material under-declaration prevents `ready`.

## 8. Observed scope

An observed scope is tool-produced evidence about actual work. It does not overwrite the author's declaration.

```json
{
  "id": "observed-scope:auth-refresh-v1",
  "type": "observed_scope",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "final",
  "created_by": "actor:scope-analyzer",
  "created_at": "2026-09-03T21:00:00Z",
  "subject": "changeset:auth-refresh-v1@2",
  "base_revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
  "result_revision": "git:5b7e912ba94d32ddf03778b63a751a06d920f399",
  "analyzer": {"id": "tool:scope-analyzer", "version": "1.0.0"},
  "method": "typescript-compiler-symbols-v1",
  "observed": ["scope:rotate-refresh@1", "scope:session-schema@1"],
  "outcome": "complete",
  "comparison": {
    "covered": ["scope:rotate-refresh@1"],
    "undeclared": ["scope:session-schema@1"],
    "declared_not_observed": ["scope:session-contract@1"]
  },
  "evidence_artifacts": ["artifact:scope-report-sha256"]
}
```

Observed-scope lifecycle statuses are `final` and `superseded`; outcome is `complete`, `partial`, or `error`. The analyzer, base, result, method, and evidence digest MUST be recorded. `declared_not_observed` is informational unless policy says otherwise. `undeclared` MUST be evaluated for new overlaps and may stale earlier acknowledgements. An omitted effect or scope means unknown; an explicitly present empty array asserts that none were observed or declared under the stated method.

## 9. Overlap and conflict

Overlap classifications are:

- `none`: no relevant intersection was found;
- `informational`: awareness is useful but no ordering or agreement is required;
- `compatible`: compatible under recorded assumptions;
- `ordered`: compatible only in a stated order;
- `negotiation_required`: participants must agree on a resolution;
- `blocking`: work or integration must not proceed under current policy;
- `unknown`: available scope or semantic information is insufficient.

An overlap record identifies the compared subjects and revisions, shared physical and semantic scopes, analyzer or deciding actor, confidence, assumptions, policy decision, owner, required acknowledgements, and disposition.

```json
{
  "id": "overlap:auth-session",
  "type": "overlap",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "open",
  "created_by": "actor:coordinator",
  "created_at": "2026-09-03T20:20:00Z",
  "subjects": ["intent:auth-refresh@1", "intent:session-store@2"],
  "classification": "negotiation_required",
  "semantic_scopes": ["semantic:session-store-contract@2"],
  "basis": "Both intents alter refresh-generation semantics.",
  "policy_action": "negotiate",
  "owner": "actor:integration-agent",
  "required_acknowledgements": ["actor:agent-a", "actor:agent-b"]
}
```

Overlap lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `overlap.detected` | `open` | subjects and classification present |
| `open` | `overlap.acknowledged` | `open` | acknowledgement appended idempotently |
| `open` | `overlap.negotiation_started` | `negotiating` | negotiation record identified |
| `open`, `negotiating`, `escalated` | `overlap.dispositioned` | `resolved` | disposition, owner, assumptions, and required acknowledgements satisfied |
| `open`, `negotiating` | `overlap.escalated` | `escalated` | authority target and reason present |
| `resolved` | `overlap.reopened` | `open` | changed scope, contract, base, or evidence identified |
| nonterminal | `overlap.superseded` | `superseded` | successor identified |

`unknown` MUST NOT be treated as `compatible`. The configured policy determines whether it warns, negotiates, or blocks.

`superseded` is the only terminal overlap state. `resolved` is quiescent but may reopen when its basis changes. The overlap record's `policy_action` is the evaluated result of the module configuration plus any identified scope, repository, or organization policy. More specific applicable policy takes precedence; equal-specificity disagreement produces `unknown` and a policy-conflict diagnostic rather than silent selection.

A conflict is an overlap whose policy action requires resolution. A conflict records competing claims, responsible owner, allowed resolution strategies, evidence, accepted risk, and final disposition. Resolution strategies include scope partition, contract first, ordered integration, compatibility adapter, feature isolation, rebase and re-derive, combined implementation, authorized risk acceptance, and withdrawal.

## 10. Negotiation and commitments

A negotiation makes coordination dialogue finite, typed, and auditable.

Required fields are subject, participants, facilitator if any, opening proposal, response deadline, decision policy, permitted outcomes, and escalation target.

Message acts are `propose`, `counter`, `accept`, `reject`, `abstain`, `clarify`, `withdraw`, `cancel`, and `escalate`. Every act identifies `negotiation_id`, proposal revision where applicable, actor, event ID, and causal parents.

Negotiation lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `negotiation.opened` | `open` | participants, proposal, policy, deadline present |
| `open` | `negotiation.proposal_revised` | `open` | next proposal revision and causal basis present |
| `open` | `negotiation.accepted` | `accepted` | decision policy and required acceptances satisfied |
| `open` | `negotiation.rejected` | `rejected` | terminal rejection permitted by policy |
| `open` | `negotiation.timed_out` | `timed_out` | deadline passed under identified clock authority |
| `open` | `negotiation.cancelled` | `cancelled` | permitted actor and cancellation consequences recorded |
| `open` | `negotiation.escalated` | `escalated` | escalation target and unresolved question present |

`accepted`, `rejected`, `timed_out`, `cancelled`, and `escalated` are terminal. Escalation after rejection or timeout creates a successor negotiation referencing the terminal record. A further round likewise creates a successor. A processor MUST NOT infer acceptance from silence unless the declared decision policy explicitly defines silence and the enforcing authority supports it.

An accepted proposal MAY create commitments. A commitment identifies:

- obligated actor (`debtor`);
- beneficiary or relying participants;
- trigger condition;
- promised condition or delivery;
- deadline or discharge condition;
- verification requirement;
- violation and cancellation consequences.

Commitment transitions are:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `commitment.created` | `conditional` or `active` | debtor, beneficiary, promised condition, and discharge/violation criteria present |
| `conditional` | `commitment.activated` | `active` | trigger observation recorded |
| `active` | `commitment.satisfied` | `satisfied` | discharge evidence satisfies verification policy |
| `active` | `commitment.violated` | `violated` | violation observation and clock/basis recorded |
| `conditional`, `active` | `commitment.cancelled` | `cancelled` | cancellation policy and consequences recorded |
| `conditional`, `active` | `commitment.released` | `released` | beneficiary or authorized actor releases obligation |
| `conditional`, `active` | `commitment.superseded` | `superseded` | successor identified |

`satisfied`, `violated`, `cancelled`, `released`, and `superseded` are terminal. A remedy after violation creates a successor commitment and retains the violation. State changes require the triggering event or evidence. Commitments express social/project obligations; they do not create external legal authority.

## 11. Interface contracts

A contract identifies owners, producers, consumers, prior and proposed revisions, observable interface/schema/behavior, states, errors, invariants, compatibility class, migration strategy, tests, decision policy, and participant adoption.

Contract decision policy is a machine-readable object:

```json
{
  "kind": "threshold",
  "eligible_participants": ["actor:architect", "actor:security", "actor:consumer"],
  "threshold": 2,
  "required_participants": ["actor:security"],
  "abstention": "counts_as_no",
  "decides_revision": 2
}
```

`kind` is `unanimous`, `threshold`, `named_participants`, or `authorized_owner`. `eligible_participants` is required except for `authorized_owner`; `threshold` is required only for `threshold` and MUST be between 1 and the eligible count. `required_participants` defaults to empty. `abstention` is `counts_as_no`, `reduces_eligible`, or `prohibited`. Votes and acceptances MUST pin `decides_revision`. Role names alone are not participant identity; a policy using roles must resolve them to an uncontested eligible actor set before evaluation.

Contract states:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `contract.proposed` | `proposed` | owners, participants, content, and decision policy present |
| `proposed` | `contract.negotiation_started` | `negotiating` | negotiation identified |
| `proposed`, `negotiating` | `contract.accepted` | `accepted` | decision policy satisfied |
| `accepted` | `contract.implementation_reported` | `implemented` | required producers report implementation evidence |
| `implemented` | `contract.verified` | `verified` | required verification results pass |
| nonterminal | `contract.revised` | `superseded` | successor contract revision created |
| `proposed`, `negotiating` | `contract.rejected` | `rejected` | decision outcome recorded |
| nonterminal | `contract.withdrawn` | `withdrawn` | permitted owner and reason recorded |

Global contract status MUST NOT be derived from a single participant's adoption status. Each participant has one of `unaware`, `reviewing`, `accepted`, `implementing`, `implemented`, `verified`, `rejected`, `withdrawn`, or `not_applicable`, with its own evidence and revision.

The contract's decision policy specifies named required parties or a quorum. A contract MUST NOT become `accepted`, `implemented`, or `verified` until that state's policy is satisfied.

A revised accepted contract triggers staleness evaluation for every dependent intent, change set, integration plan, commitment, and verification result.

Terminal contract states are `verified`, `superseded`, `rejected`, and `withdrawn`. `accepted` and `implemented` are nonterminal. A change to verified contract content creates a successor revision or successor contract rather than reopening the verified record.

## 12. Typed preconditions

A precondition is either `mechanical` or `asserted`.

```json
{
  "id": "precondition:session-contract-v2",
  "type": "precondition",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "active",
  "created_by": "actor:integration-agent",
  "created_at": "2026-09-03T21:15:00Z",
  "kind": "mechanical",
  "predicate": "record_revision_equals",
  "subject": "contract:session-store-v2@2",
  "expected": 2,
  "evaluator_interface": "urn:awp:evaluator:record-revision:1",
  "on_false": "stale",
  "on_unknown": "block_ready"
}
```

Precondition lifecycle statuses are `active`, `retired`, and `superseded`. `on_false` is `warn`, `block_ready`, `stale`, or `escalate`. `on_unknown` is `warn`, `block_ready`, or `escalate`; it MUST NOT silently pass.

Registered mechanical predicates have the following minimum semantics:

| Predicate | Subject and arguments | Determinism class | `unknown` when |
|---|---|---|---|
| `repository_revision_equals` | repository; immutable expected revision | repository-relative | repository or revision unavailable |
| `repository_descends_from` | repository; immutable ancestor revision | repository-relative | ancestry unavailable or shallow |
| `artifact_digest_equals` | artifact; algorithm and expected digest | pure over retrieved bytes | bytes unavailable or algorithm unsupported |
| `record_revision_equals` | record ID; expected integer revision | pure over projection | record missing or contested |
| `record_status_in` | pinned record; allowed status set | pure over projection | record missing, contested, or status unknown |
| `symbol_present` | selector and repository revision | repository-relative | selector profile or source unavailable |
| `syntax_fingerprint_equals` | selector, revision, algorithm, fingerprint | repository-relative | target or algorithm unavailable |
| `dependency_state_in` | pinned dependency edge/target; allowed states | pure over projection | target or edge unresolved |
| `test_baseline_equals` | test ID; base revision and expected result digest | repository/environment-relative | baseline evidence unavailable |
| `toolchain_satisfies` | tool ID; version constraint and environment selector | host-relative | environment or version cannot be observed |
| `schema_version_satisfies` | schema ID/revision; registered version constraint | pure over identified schema | schema or constraint profile unavailable |
| `verification_passed_for` | pinned subject; verification policy | projection/environment-relative | valid bound verification unavailable |

`pure` evaluators read only the identified AWP projection or supplied bytes. Repository-relative and host-relative results MUST record the repository or environment they observed. All evaluators MUST be side-effect-free with respect to the project, deterministic for identical declared inputs, bounded by an explicit timeout, and return `error` rather than partial success after timeout or internal failure. Constraint syntax is owned by the registered evaluator-interface version; an implementation MUST NOT guess unsupported syntax.

An asserted precondition records a natural-language statement, asserting actor, scope, epistemic status, evidence if any, and required reviewer or authority. It MUST NOT be presented as machine-verified.

Evaluation produces a separate immutable result:

```json
{
  "id": "precondition-result:session-contract-v2:17",
  "type": "precondition_result",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "final",
  "created_by": "actor:precondition-runner",
  "created_at": "2026-09-03T21:30:00Z",
  "precondition": "precondition:session-contract-v2@1",
  "outcome": "pass",
  "evaluated_against": {
    "repository": "repo:app",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
    "frontier": ["evt:01K4M4VYB9"]
  },
  "depends_on": [
    {"kind": "record", "id": "contract:session-store-v2", "revision": 2},
    {
      "kind": "repository",
      "id": "repo:app",
      "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a"
    }
  ],
  "observed": 2,
  "evaluator": {
    "interface": "urn:awp:evaluator:record-revision:1",
    "implementation": "example-precondition-runner",
    "implementation_version": "1.0.0",
    "timeout_ms": 5000
  },
  "evidence_artifacts": ["artifact:precondition-log"]
}
```

Result lifecycle status is `final` or `superseded`; outcome is `pass`, `fail`, `unknown`, or `error`. `depends_on` is the complete read set used for freshness. Evaluation results are valid only while those pinned dependencies, evaluator interface, and relevant environment constraints remain satisfied. The recorded frontier is audit context and does not by itself invalidate a result when unrelated events advance the workstate.

## 13. Change sets

A change set is an integration candidate rather than merely a patch.

```json
{
  "id": "changeset:auth-refresh-v1",
  "type": "change_set",
  "module": "urn:awp:coordination",
  "revision": 3,
  "status": "ready",
  "created_by": "actor:agent-a",
  "created_at": "2026-09-03T20:00:00Z",
  "intent": "intent:auth-refresh@2",
  "base": {
    "repository": "repo:app",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a"
  },
  "artifacts": ["artifact:auth-refresh-patch"],
  "declared_scopes": ["scope:rotate-refresh@1", "scope:session-contract@1"],
  "observed_scope": "observed-scope:auth-refresh-v1@1",
  "preconditions": ["precondition:session-contract-v2@1"],
  "effects": {
    "reads": ["semantic:session-refresh-generation@1"],
    "writes": ["semantic:session-refresh-generation@1"],
    "creates": ["semantic:generation-conflict-error@1"],
    "removes": [],
    "changes_behavior": ["semantic:refresh-token-rotation@1"],
    "preserves": ["semantic:no-plaintext-token-storage@1"]
  },
  "contracts": ["contract:session-store-v2@2"],
  "verification": ["verification:auth-tests-842@1"]
}
```

Change-set lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `changeset.proposed` | `proposed` | intent, base, artifacts, scopes, effects present |
| `proposed` | `changeset.work_started` | `in_progress` | responsible actor present |
| `proposed`, `in_progress` | `changeset.ready` | `ready` | readiness gate passes |
| nonterminal | `changeset.stale` | `stale` | stale cause and dependency path present |
| `stale` | `changeset.revalidated` | `in_progress` | stale causes evaluated and fresh evidence recorded |
| `stale` | `changeset.rebased` | `in_progress` | successor base and transformation evidence present |
| `ready` | `changeset.integration_started` | `integrating` | integration plan and owner present |
| `integrating` | `changeset.integrated` | `integrated` | integration result identifies resulting revision |
| `integrating` | `changeset.failed` | `failed` | failure evidence and retry disposition present |
| nonterminal | `changeset.withdrawn` | `withdrawn` | reason present |
| nonterminal | `changeset.superseded` | `superseded` | successor present |

The readiness gate requires:

1. required contracts are accepted at referenced revisions;
2. dependencies are in allowed states;
3. every required mechanical precondition is `pass` for the selected base and its still-valid dependency/read set;
4. asserted preconditions have required reviews or recorded risk acceptance;
5. blocking overlaps are resolved and required acknowledgements are present;
6. verification required by policy passes and is correctly bound;
7. declared and observed scopes have been compared when C2 is required;
8. required authority is currently valid under receiver policy.

`ready` does not mean integrated, correct, authorized for deployment, or free of unknown risk.

Terminal change-set states are `integrated`, `failed`, `withdrawn`, and `superseded`. `stale` is nonterminal but cannot transition directly to `ready`; it first transitions through `revalidated` or `rebased`. Superseding a stale change set creates a successor record and leaves the original terminal.

## 14. Verification

A verification result MUST bind the claim being checked to exact inputs.

```json
{
  "id": "verification:auth-tests-842",
  "type": "verification_result",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "final",
  "created_by": "actor:ci-runner",
  "created_at": "2026-09-03T21:20:00Z",
  "subjects": ["changeset:auth-refresh-v1@3", "contract:session-store-v2@2"],
  "repository": "repo:app",
  "result_revision": "git:5b7e912ba94d32ddf03778b63a751a06d920f399",
  "base_revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
  "procedure": {
    "kind": "command",
    "command_id": "test:auth-contract-suite",
    "tool": "pytest",
    "tool_version": "9.0.0"
  },
  "environment": {
    "platform": "linux/amd64",
    "image_digest": "sha256:4f6c..."
  },
  "outcome": "pass",
  "observations": {"exit_code": 0, "passed": 84, "failed": 0},
  "evidence_artifacts": ["artifact:test-log", "artifact:junit-report"]
}
```

Verification lifecycle status is `final` or `superseded`; outcome is `pass`, `fail`, `inconclusive`, or `error`. An agent's statement that tests passed is `reported` evidence unless the execution and outputs are independently inspectable under the declared policy.

Verification becomes stale when its subject revision, tested repository revision, relevant contract, required tool/environment constraint, or relied-upon baseline changes. A verifier's approval does not grant integration authority unless separately authorized.

## 15. Dependency graph and staleness

Dependency edge kinds are `requires`, `implements`, `verifies`, `derived_from`, `relies_on`, `orders_before`, `conflicts_with`, `supersedes`, and `integrates`.

For each event that changes a record revision or status, a C1 projector MUST:

1. identify reverse dependencies on the changed record and revision;
2. evaluate whether each edge or recorded evaluator read-set predicate still holds;
3. emit or derive a stale cause when it does not hold or becomes unknown;
4. continue transitively through records whose validity depends on the newly stale record;
5. retain all causes and paths rather than only the first cause;
6. stop propagation across an edge whose predicate remains satisfied;
7. never clear staleness solely because a later timestamp exists.

Staleness is cleared only by a successful type-specific `*.revalidated`, `*.rebased`, or `*.superseded` transition with fresh evidence. Revalidation returns a stale record to its pre-readiness working state; readiness is evaluated in a subsequent transition.

Cycles in `requires` or `orders_before` are diagnostic `AWP-COORD-DEPENDENCY-CYCLE`. A cycle blocks automatic readiness or integration ordering until an integration plan explicitly groups the cycle into one combined unit or an authorized resolution changes the graph.

## 16. Integration plan and result

An integration plan identifies owner, target repository and base, exact change-set revisions, dependency-derived order, shared contracts, required precondition evaluations, verification plan, rollback, authority requirements, and `atomicity`.

`atomicity` is:

- `atomic`: no input is considered integrated unless the complete plan commits and passes required combined verification;
- `stepwise`: each ordered input may commit independently and remains integrated if a later step fails unless rollback policy reverses it;
- `best_effort`: independent inputs may integrate in any dependency-valid subset, with an explicit disposition for every input.

An adapter MUST reject `atomic` when its repository or transaction mechanism cannot supply the claimed atomic boundary. Rollback is a separately recorded operation and MUST NOT be assumed successful.

Before starting integration, the owner MUST refresh available coordination events, compare the target base, re-evaluate expiring or base-bound preconditions, confirm contract revisions, and re-open any invalidated overlap dispositions.

Integration lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `integration.proposed` | `proposed` | exact inputs, base, owner, order, verification present |
| `proposed` | `integration.approved` | `approved` | required policy/authority approves exact plan revision |
| `approved` | `integration.started` | `integrating` | current readiness and concurrency checks pass |
| `integrating` | `integration.completed` | `completed` | result revision, transformations, and required verification recorded |
| `integrating` | `integration.failed` | `failed` | failure evidence and repository disposition recorded |
| `proposed`, `approved` | `integration.cancelled` | `cancelled` | permitted actor and reason recorded |
| nonterminal | `integration.superseded` | `superseded` | successor plan present |

An integration result identifies exact plan revision, inputs, target base, resulting repository revision, merge/rebase/manual transformations, resolved conflicts, contract revisions, verification results, deviations, output artifact digests, responsible actors, and rollback status.

The result contains one disposition per planned input: `integrated`, `not_attempted`, `failed`, `rolled_back`, `rollback_failed`, or `superseded`, plus any intermediate and final repository revisions. After partial failure, each change set transitions according to its own disposition; the plan may be `failed` even though stepwise inputs remain `integrated`. An atomic plan that fails leaves no change set integrated unless the enforcing adapter records an atomicity violation.

A successful source-control merge MUST NOT by itself transition an integration to `completed` when combined semantic verification is required.

Terminal integration states are `completed`, `failed`, `cancelled`, and `superseded`. `proposed`, `approved`, and `integrating` are nonterminal.

## 17. Deterministic projection

Coordination state is derived from valid Core events at a declared frontier.

A C1 projector MUST:

1. validate the Core envelope, module declaration, ancestry, and workstate identity;
2. compute semantic state independently of the serialization chosen for concurrent valid events;
3. apply an event only when its record revision precondition and lifecycle transition are valid;
4. treat concurrent non-commuting updates from the same uncontested record revision as a contested record conflict;
5. allow only module-defined commutative operations, currently acknowledgement-set union and evidence-reference-set union;
6. preserve invalid or unknown events in history while excluding their claimed state change from the valid projection;
7. order diagnostic emission using Kahn's topological algorithm with the lexicographically smallest event ID selected from the ready set;
8. propagate staleness after applying each valid semantic change;
9. compute module state at the same frontier as the containing Core snapshot.

Acknowledgements commute only when keyed by `(subject revision, actor, acknowledgement kind, association ID)`. Two differing acknowledgements with the same identity conflict; they do not use last-write-wins.

When two or more concurrent non-commuting events propose successors from the same uncontested revision, none becomes the effective successor. The last uncontested record remains readable, and the projection attaches a `contested` condition containing every competing event and descendant whose validity depends on one competing branch. Safety-relevant unpinned references to the record are unresolved.

A reconciliation event:

- uses kind `<type>.reconciled` or the generic `record.reconciled` kind owned by this module;
- names every competing branch tip as Core event parents;
- identifies the last uncontested `prior_revision`;
- includes `resolves_events` naming every competing successor event known to the resolver;
- provides a complete replacement record and concise disposition for each competing value;
- produces `prior_revision + 1`, regardless of revision numbers claimed only on contested branches;
- cites the authority evaluation and policy permitting reconciliation.

A valid reconciliation clears the contested condition for the resolved branches. An omitted concurrent branch remains unresolved and causes a new contested condition when discovered. This rule is specific to Coordination records until Core/Synchronization defines a family-wide equivalent.

Snapshot module state is stored at `snapshot.modules["urn:awp:coordination"]`. When valid event history disagrees with the snapshot, the event-derived projection is authoritative under Synchronization rules.

### 17.1 Retention and portable views

Synchronization 0.2 governs retention and compaction: a snapshot does not authorize destructive pruning, and snapshot-only exports disclose omitted history. A portable Coordination view MAY omit terminal records irrelevant to the requested continuation only when it declares the omission and does not claim full audit completeness. It MUST retain or make retrievable every active dependency, unresolved conflict, governing contract, precondition, verification, authority decision, and causal record needed to justify current readiness. Physical deletion or redaction follows Synchronization, Artifact, and Security rules.

## 18. Diagnostics

Diagnostics have stable code, severity, event or record subjects, explanation, and suggested recovery. Severity is `info`, `warning`, or `error`. Unless a table entry says `policy`, its listed severity is normative. For `policy`, severity is a deterministic result of the cited effective policy and module configuration; absent or conflicting policy produces at least `warning` and cannot silently permit a guarded transition. Minimum codes are:

| Code | Default severity | Meaning |
|---|---|---|
| `AWP-COORD-INVALID-TRANSITION` | error | Event is not valid from the effective state |
| `AWP-COORD-REVISION-CONFLICT` | error | Prior revision is unsatisfied or concurrent updates conflict |
| `AWP-COORD-RECORD-CONTESTED` | error | A record has unresolved non-commuting successors |
| `AWP-COORD-MISSING-DEPENDENCY` | error | Referenced record, revision, event, artifact, or evaluator is unavailable |
| `AWP-COORD-STALE` | error | A dependency predicate no longer holds |
| `AWP-COORD-PRECONDITION-FAILED` | policy | A required precondition evaluated false |
| `AWP-COORD-PRECONDITION-UNKNOWN` | policy | A required precondition cannot be evaluated |
| `AWP-COORD-VERIFICATION-UNBOUND` | error | Verification omits or mismatches required subject/base/environment binding |
| `AWP-COORD-OVERLAP-UNRESOLVED` | policy | Policy-required overlap disposition is absent |
| `AWP-COORD-ACK-MISSING` | policy | Required participant acknowledgement is absent |
| `AWP-COORD-SCOPE-UNDERDECLARED` | policy | Observed material scope is not covered by declared scope |
| `AWP-COORD-SELECTOR-UNRESOLVABLE` | warning | A selector cannot be related across the compared revisions; overlap becomes unknown |
| `AWP-COORD-REGISTRY-AMBIGUOUS` | error | Semantic identifier or alias resolves ambiguously |
| `AWP-COORD-DEPENDENCY-CYCLE` | error | Ordering/readiness dependencies contain an unresolved cycle |
| `AWP-COORD-AUTHORITY-INSUFFICIENT` | policy | Claimed transition lacks currently accepted authority |
| `AWP-COORD-AUTHORITY-UNVERIFIABLE` | policy | Authority cannot be checked under current receiver policy |
| `AWP-COORD-COMMITMENT-VIOLATED` | policy | A commitment has entered the violated state |
| `AWP-COORD-POLICY-CONFLICT` | warning | Applicable policies disagree at equal specificity |
| `AWP-COORD-FENCING-REJECTED` | error | A protected operation carries an obsolete or invalid fencing token |
| `AWP-COORD-ENFORCEMENT-UNVERIFIABLE` | error | Live exclusion cannot be proven for the requested operation |

Errors invalidate the affected transition. Warnings preserve state but MUST be visible before a safety-relevant continuation. Implementations MAY add namespaced diagnostics.

## 19. Live coordination and leases

C3 is optional. It requires a live coordinator or an external protected system, not merely a shared file.

Protected operations use optimistic concurrency control with:

- coordinator and principal identity;
- protected namespace;
- expected record revision or causal frontier;
- coordinator epoch;
- monotonically increasing fencing token;
- idempotency key;
- authenticated decision and expiration.

Lease modes are `shared_read`, `shared_write`, `exclusive_write`, and `integration_owner`. An advisory activity announcement is an intent or claim, not an enforced lease.

Lease states are `requested`, `active`, `denied`, `released`, `expired`, `revoked`, and `superseded`. The coordinator grants a lease only after an atomic comparison against current protected state. Renewal creates a new expiration and MUST NOT reduce the fencing token.

An adapter claiming enforcement MUST reject a protected mutation whose token is older than the highest token it has accepted for that namespace. A new grant, new holder, or new coordinator epoch MUST issue a token strictly greater than every previously issued token in that protected namespace. Renewal of the same uninterrupted lease retains its token; it changes expiration but does not create a new ownership generation. Without this fencing check, a paused or partitioned former holder may act after its lease expires.

If coordinator identity, epoch, authentication, protected scope, or fencing validation is unavailable, the lease is `unverifiable` outside the reachable enforcement guarantee. The implementation MUST NOT describe it as exclusive. Local work may continue under policy, but integration MUST refresh state and re-evaluate overlap and preconditions.

The C3 profile MUST specify retry limits, heartbeat interval, lease duration, expiry clock authority, deadlock detection, starvation policy, cancellation consequences, and human/organizational arbitration. The base module defines no universal timing defaults because safe values depend on task duration, network delay, and the protected system. Named interoperability and test profiles MAY define explicit defaults.

## 20. Security, principals, and governance

Actor identity, principal identity, trust, and authority are separate.

A principal is the human or organization accountable for an actor's participation. A C3 session MUST bind authenticated actors to principals and declare the governing policy. Cross-principal coordination MUST identify:

- permitted operations and visible scopes;
- confidentiality and redaction rules;
- signature and replay-protection requirements;
- authority required to accept risk, revise contracts, integrate, or deploy;
- dispute and arbitration path;
- audit retention requirements.

AWP content is untrusted input. Imported intents, contracts, commitments, leases, and authority records MUST NOT cause execution without receiver policy evaluation. Secret values SHOULD be referenced through protected artifacts rather than embedded in coordination records.

Coordination defines no separate protected-artifact envelope. A protected input uses the Artifact module's availability, remote-location, retrieval-requirement, and integrity fields together with Security classification or `secret_ref` metadata. A URI or digest alone proves neither confidentiality nor retrievability. Digests of low-entropy secrets may themselves enable guessing attacks and MUST be omitted or protected when receiver policy classifies the digest as sensitive.

## 21. Event kinds

Events use Core envelope version `0.2` and module `urn:awp:coordination`.

Initial event kinds are:

- `semantic_definition.created`, `.updated`, `.superseded`;
- `scope.created`, `.updated`, `.retired`;
- `intent.announced`, `.activated`, `.updated`, `.waiting`, `.resumed`, `.reassigned`, `.completed`, `.withdrawn`, `.abandoned`, `.superseded`, `.reconciled`;
- `observed_scope.published`, `.superseded`;
- `overlap.detected`, `.acknowledged`, `.negotiation_started`, `.dispositioned`, `.escalated`, `.reopened`, `.superseded`;
- `conflict.detected`, `.resolved`, `.reopened`;
- `negotiation.opened`, `.proposal_revised`, `.accepted`, `.rejected`, `.timed_out`, `.cancelled`, `.escalated`;
- `commitment.created`, `.activated`, `.satisfied`, `.violated`, `.cancelled`, `.released`, `.superseded`;
- `contract.proposed`, `.negotiation_started`, `.accepted`, `.implementation_reported`, `.verified`, `.revised`, `.rejected`, `.withdrawn`, `.reconciled`;
- `precondition.created`, `.updated`, `.evaluated`, `.superseded`;
- `verification.started`, `.completed`, `.superseded`;
- `dependency.created`, `.removed`;
- `changeset.proposed`, `.work_started`, `.ready`, `.stale`, `.revalidated`, `.rebased`, `.integration_started`, `.integrated`, `.failed`, `.withdrawn`, `.superseded`, `.reconciled`;
- `integration.proposed`, `.approved`, `.started`, `.completed`, `.failed`, `.cancelled`, `.superseded`;
- `lease.requested`, `.granted`, `.denied`, `.renewed`, `.released`, `.expired`, `.revoked`, `.superseded`.
- `evidence.linked`, `evidence.unlinked`, and `record.reconciled`.

Minimum C1 payload requirements supplement the common event rules in Section 4.3:

| Event class | Additional required payload |
|---|---|
| creation | complete revision-1 record |
| revision-changing update | record ID, prior and new revision, complete replacement or registered patch |
| lifecycle transition | explicit from/to state and transition-specific evidence |
| acknowledgement/evidence association | pinned subject, association identity, actor, value, evidence |
| precondition evaluation | pinned precondition, complete read set, evaluator identity/context, outcome |
| verification completion | pinned subjects, base/result revision, procedure, environment, outcome, evidence |
| staleness | subject, invalidated dependency/read-set entry, causal path, prior valid evidence |
| reconciliation | last uncontested revision, all known competing events and tips, replacement, dispositions, authority evaluation |
| integration completion/failure | pinned plan, per-input dispositions, repository revisions, verification and rollback outcomes |

An unlink event removes an association from effective projection but preserves its historical addition. It identifies the exact association ID and authority evaluation; it does not edit the subject record.

Private event kinds use a controlled namespaced module ID. They MUST NOT add unregistered bare kinds to this module.

## 22. Interoperability mappings

This section is non-normative. A registered adapter profile may make a particular mapping normative for that profile.

### Git and source-control systems

Git revisions map to immutable `base.revision` and `result_revision` values. Branches and worktrees map to isolated execution locations. Commits and patches map to artifacts and change-set inputs. Pull requests map to review/integration adapters. Git merge success is mechanical evidence only.

### A2A

An A2A Task may carry a AWP intent reference. A2A Artifacts may carry AWP deltas, bundles, change sets, evidence, or integration results. A2A Task state does not replace AWP record state; adapters record the mapping and preserve both identities.

### MCP

MCP tools may read, validate, project, query, or append AWP data. Tool availability and invocation do not establish project authority.

### MPAC

[MPAC, arXiv:2604.09744 version 1](https://arxiv.org/abs/2604.09744v1) session, intent, operation, conflict, and governance objects may map to corresponding AWP records. AWP retains repository-specific semantic scopes, contracts, preconditions, verification binding, persistent project history, and resume/handoff state. A mapping MUST identify information loss and MUST NOT equate MPAC transport/session acceptance with AWP integration readiness.

## 23. Reference procedure

This is a non-normative happy path, not a lifecycle state machine. Reopened overlaps return to analysis or negotiation; stale change sets return to implementation/revalidation; failed integrations follow their recorded retry, rollback, or supersession disposition.

```text
refresh workstate and repository identity
              |
announce intent and relied-upon reads
              |
analyze physical + semantic overlap
              |
acknowledge / negotiate / establish contract
              |
work in isolated repository state
              |
publish change set + observed scope
              |
compare declaration with observation
              |
evaluate typed preconditions at exact base and dependency read set
              |
verify exact change-set and contract revisions
              |
derive integration order and approve exact plan
              |
integrate, run combined verification, publish result
              |
complete intents and release live coordination state
```

## 24. Minimum conformance fixtures

The experimental module is not ready for stable status without fixtures covering at least:

1. independent non-overlapping changes;
2. same-file physical conflict;
3. different-file semantic contract conflict;
4. writer versus relied-upon reader;
5. material undeclared scope;
6. accepted contract revised after a change set becomes ready;
7. precondition pass, fail, unknown, and evaluator error;
8. verification bound to the wrong revision;
9. missing participant acknowledgement;
10. negotiation timeout and escalation;
11. concurrent updates from one prior record revision;
12. commutative acknowledgements arriving in opposite orders;
13. dependency cycle and combined-integration resolution;
14. stale snapshot with replayable coordination events;
15. agent abandonment and reassignment;
16. expired lease holder attempting a fenced mutation;
17. coordinator epoch change during a partition;
18. unauthorized integration approval;
19. unknown required event kind;
20. cross-host resume with missing repository revision.

Each fixture SHOULD include input events, expected frontier, expected materialized records, expected diagnostics, and an explanation of the safety property.

## 25. Implementation maturity criteria

Before the complete integration-assurance schema is frozen, the project SHOULD run an early `coordination-awareness` experiment comparing chat-only coordination with durable intents, pinned scopes, overlaps, acknowledgements, and conflict-preserving projection. It MUST measure false-positive and false-negative overlap classifications, authoring cost, coordination delay, and whether warnings arrive before conflicting implementation. Results may change the scope and record model before further standardization.

Coordination 0.4.0 is normative but experimental in AWP 0.7.0. It should not advance from experimental status until:

1. JSON Schemas exist for all C1 records and events;
2. two independent implementations produce identical projections for the fixture suite;
3. invalid transitions and revision conflicts are consistently rejected;
4. staleness propagation is deterministic;
5. a Git/worktree and test-runner reference adapter demonstrates one end-to-end workflow;
6. an expanded benchmark compares chat-only, Git-only, and AWP-assisted coordination across awareness and integration-assurance bundles;
7. the A2A and MPAC mappings are reviewed for semantic overclaiming;
8. security review confirms that records cannot self-authorize external actions.

## 26. Open issues

1. Canonical JSON and digest rules remain a Core/Artifact/Security family issue and must be resolved before signed coordination evidence is portable. The family profile should evaluate RFC 8785 JCS while explicitly handling its I-JSON, IEEE-754 number, and Unicode-preservation constraints; Coordination MUST NOT select a conflicting local canonicalization.
2. The initial semantic registry needs language-specific selector profiles for symbols, schemas, and dependency graphs.
3. Confidence calibration for inferred semantic overlap is unspecified; policy must not confuse a model score with verification.
4. Composition and conflict rules for multiple organization-specific contract decision policies need implementation experience.
5. C3 needs a formally modeled coordinator protocol and at least one real enforcing adapter.
6. Privacy-preserving coordination across principals may require selective disclosure or commitments to hidden evidence.
7. Benchmark tasks must measure false alarms and coordination overhead as well as conflicts caught.

## 27. Summary

Coordination 0.4.0 turns Coordination from a descriptive vocabulary into a candidate executable protocol. C1 defines durable deterministic coordination that works across agents and hosts. C2 adds semantic awareness and early conflict detection. C3 adds live enforcement only where a protected system can prove it.

The essential invariant is:

> No actor, record, message, clean merge, or passing claim may silently promote asserted coordination into observed fact, verified compatibility, or external authority.

---

# AWP Security 0.4.0

**Module ID:** `urn:awp:security`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`; AWP Artifact `0.4.x` when `artifact-controls` is declared  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

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

AWP Security 0.4.0 does not select a normative canonicalization or signature algorithm. Implementations MUST NOT claim interoperable AWP signature conformance without naming an external or future registered signature profile.

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

# AWP Adapter Framework 0.4.0

**Status:** Informative framework  
**Payload module:** None  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

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

No single mapping is normative in 0.7.0. Branches and pull requests are forge conventions rather than universal Git objects. Git object IDs establish repository object identity, not semantic safety, actor authority, or AWP event identity.

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

---

# Bundled machine-readable assets

## Module registry — `spec/drafts/0.7.0/modules.json`

```json
{
  "$schema": "../../../schemas/awp-module-registry-0.7.schema.json",
  "family": "AWP",
  "family_version": "0.7.0",
  "event_schema_versions": ["0.2"],
  "modules": [
    {
      "id": "urn:awp:core",
      "name": "AWP Core",
      "version": "0.7.0",
      "status": "required",
      "document": "core.md",
      "schema": "../../../schemas/awp-core-0.7.schema.json",
      "dependencies": []
    },
    {
      "id": "urn:awp:capsule",
      "name": "AWP Capsule",
      "version": "0.4.0",
      "status": "optional",
      "document": "capsule.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" }
      ]
    },
    {
      "id": "urn:awp:handoff",
      "name": "AWP Handoff",
      "version": "0.4.0",
      "status": "optional",
      "document": "handoff.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" }
      ]
    },
    {
      "id": "urn:awp:artifact",
      "name": "AWP Artifact",
      "version": "0.4.0",
      "status": "optional",
      "document": "artifact.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" }
      ]
    },
    {
      "id": "urn:awp:sync",
      "name": "AWP Synchronization",
      "version": "0.4.0",
      "status": "optional",
      "document": "synchronization.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" }
      ]
    },
    {
      "id": "urn:awp:coordination",
      "name": "AWP Coordination",
      "version": "0.4.0",
      "status": "experimental",
      "document": "coordination.md",
      "schema": "../../../schemas/awp-coordination-0.4.schema.json",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" },
        { "id": "urn:awp:sync", "version": "0.4.x" }
      ]
    },
    {
      "id": "urn:awp:security",
      "name": "AWP Security",
      "version": "0.4.0",
      "status": "optional",
      "document": "security.md",
      "dependencies": [
        { "id": "urn:awp:core", "version": "0.7.x" }
      ],
      "conditional_dependencies": [
        {
          "when_capability": "artifact-controls",
          "id": "urn:awp:artifact",
          "version": "0.4.x"
        }
      ]
    }
  ],
  "informative_documents": [
    {
      "name": "AWP Adapter Framework",
      "version": "0.4.0",
      "document": "adapters.md"
    },
    {
      "name": "AWP Open Issues",
      "version": "0.7.0",
      "document": "open-issues.md"
    }
  ]
}
```

## Requirement inventory — `spec/drafts/0.7.0/requirements.json`

```json
{
  "family": "AWP",
  "version": "0.7.0-draft",
  "status": "generated-review-inventory",
  "normative_authority": "source prose",
  "requirements": [
    {
      "id": "AWP-FAMILY-001",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 10,
      "statement": "The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals."
    },
    {
      "id": "AWP-FAMILY-002",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 46,
      "statement": "Every AWP 0.7 manifest MUST contain a `modules` array. It MUST declare exactly one Core entry, and that entry MUST be required. The following is a module-declaration excerpt rather than a complete manifest:"
    },
    {
      "id": "AWP-FAMILY-003",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 80,
      "statement": "A writer MUST declare every module whose records, events, or required processing rules affect the effective workstate. It MUST include compatible declarations for all direct dependencies. It MUST mark a module required only when ignoring that module would prevent the receiver from safely performing the declared continuation."
    },
    {
      "id": "AWP-FAMILY-004",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 82,
      "statement": "If a module is required, every dependency needed to interpret it MUST also be required. If an optional module depends on another optional module, a receiver may ignore both while preserving their data."
    },
    {
      "id": "AWP-FAMILY-005",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 84,
      "statement": "Core owns the unqualified Core record types and fields. A module defining a new record type MUST include a `module` field naming its module ID. A module extending a Core record MUST place its fields under that record's `modules` object, keyed by module ID. Module-owned event kinds use the common event envelope's required `module` field. These rules prevent independent subspecifications from claiming the same unqualified name."
    },
    {
      "id": "AWP-FAMILY-006",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 88,
      "statement": "A reader that encounters an unknown optional module MAY continue using understood modules. It MUST preserve or explicitly disclose loss of the unknown data, and it MUST NOT infer semantics from unknown fields."
    },
    {
      "id": "AWP-FAMILY-007",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 90,
      "statement": "A reader that encounters an unknown required module MUST NOT claim a complete interpretation or perform a continuation that could depend on it. It SHOULD still present the human briefing, validate understood envelopes, and report the unsupported module."
    },
    {
      "id": "AWP-FAMILY-008",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 125,
      "statement": "The conventional project-named form is `<project-name>.awp.md`. Producers MAY retain versioned archival copies using `<project-name>.v<revision>.awp.md`, such as `project.v2.awp.md`. This filename revision is only a human-facing label; protocol and workstate identity remain defined by the capsule metadata and the `.awp.json` `current_workstate` pointer."
    },
    {
      "id": "AWP-FAMILY-009",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 131,
      "statement": "Every shared AWP workstate MUST identify the exact specification artifact that governs it. A repository discovery document and its current capsule MUST carry an explicit `specification` reference. That reference SHOULD be an immutable, version-pinned URI to a published specification bundle. A repository-relative local copy MAY be used when network retrieval is unavailable or inappropriate."
    },
    {
      "id": "AWP-FAMILY-010",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 133,
      "statement": "A reader MUST interpret a workstate according to its declared specification and module versions. It MUST NOT silently substitute a newer, older, or otherwise different specification, infer compatibility from a filename, or treat a moving branch URL as version-pinned. If the declared specification is unavailable or unsupported, the reader MUST report that condition rather than guess."
    },
    {
      "id": "AWP-FAMILY-011",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 135,
      "statement": "AWP `0.x` is exploratory. A new minor family or module release MAY make incompatible changes. A patch release MUST NOT introduce incompatible normative semantics. Explicit specification binding allows protocol development to proceed without requiring backward compatibility between exploratory minor releases. Implementations MAY support multiple versions or provide explicit migrations, but conformance to one version does not imply support for another."
    },
    {
      "id": "AWP-FAMILY-012",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 137,
      "statement": "The family version and module versions remain independent. The family version identifies a tested set of module releases, and a later family release may reuse an unchanged module version. Writers that change protocol semantics MUST publish a new versioned specification artifact and update affected workstates deliberately. Implementations MUST determine support by the declared specification, module ID, and module version, not by comparing only `awp_version`."
    },
    {
      "id": "AWP-FAMILY-013",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 157,
      "statement": "An implementation MUST satisfy the conformance requirements in each module for every role it claims. Supporting AWP Core alone is valid AWP conformance. It does not imply support for capsules, handoffs, synchronization, coordination, signatures, encryption, or adapters."
    },
    {
      "id": "AWP-FAMILY-014",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 161,
      "statement": "Every module and binding MUST preserve these rules:"
    },
    {
      "id": "AWP-FAMILY-015",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 170,
      "statement": "8. Optional modules MUST NOT redefine Core field meanings."
    },
    {
      "id": "AWP-FAMILY-016",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 178,
      "statement": "The migration is intentionally incompatible: a shared capsule and `.awp.json` discovery document now identify the exact specification artifact that governs the workstate. A 0.7 reader MUST NOT silently substitute another specification. Discovery 0.1 documents remain valid historical inputs but require explicit migration before being claimed as Discovery 0.2."
    },
    {
      "id": "AWP-FAMILY-017",
      "source": "spec/drafts/0.7.0/index.md",
      "line": 180,
      "statement": "An upgrader from 0.6.0 MUST add the governing `specification` reference to capsule metadata, update Capsule to `0.4.0`, and emit a Discovery 0.2 document. Historical events remain unchanged."
    },
    {
      "id": "AWP-CORE-001",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 32,
      "statement": "Every workstate MUST have a stable `workstate_id`. Copying or repackaging a workstate does not change this ID. Forking creates a new workstate ID and records the parent workstate and parent frontier."
    },
    {
      "id": "AWP-CORE-002",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 34,
      "statement": "Record and event IDs MUST be stable and unique within the workstate. Globally collision-resistant IDs are RECOMMENDED. IDs are opaque: consumers MUST NOT derive authority, time, ordering, or record type from their spelling."
    },
    {
      "id": "AWP-CORE-003",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 36,
      "statement": "Timestamps MUST use RFC 3339 and SHOULD use UTC. Causality is determined by event ancestry, not timestamps."
    },
    {
      "id": "AWP-CORE-004",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 71,
      "statement": "The Core module declaration MUST appear exactly once with version `0.7.x` and `required: true`. Module IDs MUST be unique within the array. A module declaration MUST satisfy the dependency and requiredness rules in the family specification."
    },
    {
      "id": "AWP-CORE-005",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 75,
      "statement": "Module-specific manifest data belongs in the owning module declaration's `configuration` object or in a top-level `module_data` object keyed by module ID. Undeclared modules MUST NOT place data there."
    },
    {
      "id": "AWP-CORE-006",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 111,
      "statement": "The owning module MUST be declared in the manifest. Event kind and payload are interpreted according to that module version. An unknown optional-module event remains part of the causal graph even when its payload cannot be interpreted."
    },
    {
      "id": "AWP-CORE-007",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 113,
      "statement": "Lossless processors MUST preserve unknown event fields. An event is immutable; correction, supersession, and redaction lineage use new events."
    },
    {
      "id": "AWP-CORE-008",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 117,
      "statement": "Event parents form a directed acyclic graph. A conforming writer MUST NOT create a cycle. A non-genesis event MUST identify every immediate causal predecessor known to its writer. Concurrent events may have the same parent. A merge or resolution event names all resolved tips as parents."
    },
    {
      "id": "AWP-CORE-009",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 121,
      "statement": "Wall-clock timestamps and array order MUST NOT be used as causal ordering. A `sequence` field is meaningful only within its declared single-writer scope."
    },
    {
      "id": "AWP-CORE-010",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 153,
      "statement": "Imported authority is evidence. A receiver MUST evaluate it against current local policy, authentication, revocation, and scope before action."
    },
    {
      "id": "AWP-CORE-011",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 155,
      "statement": "Actor declarations are materialized in a snapshot's top-level `actors` array. An actor reference in a manifest, event, authority declaration, or record SHOULD resolve to one of those declarations or to an identified external identity binding. An unresolved actor reference has type `unknown`; it does not invalidate historical events or create authentication, trust, or authority."
    },
    {
      "id": "AWP-CORE-012",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 159,
      "statement": "A core record contains `id` and `type` plus the fields below. It MAY include integer `revision`, beginning at `1` when first created. Fields marked required are structural minima; cross-record requirements remain normative even where JSON Schema cannot express them."
    },
    {
      "id": "AWP-CORE-013",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 180,
      "statement": "Core record types may refer to records owned by optional modules. If such a reference affects safe continuation, the referenced module MUST be required."
    },
    {
      "id": "AWP-CORE-014",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 182,
      "statement": "An optional module extending a Core record places its fields under `modules.{module-id}`. A module defining a new record type includes `id`, `type`, and `module`. It MUST NOT use an unqualified type name already owned by Core or another module."
    },
    {
      "id": "AWP-CORE-015",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 198,
      "statement": "Confidence MUST NOT replace epistemic status. A verified claim SHOULD identify evidence, procedure, scope, relevant artifact versions, environment, and observation time. Claims outside their recorded scope MUST be treated as unverified."
    },
    {
      "id": "AWP-CORE-016",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 200,
      "statement": "Contradictory claims MUST remain distinct until a resolution event cites the evidence and records the disposition. A summary is not independent evidence."
    },
    {
      "id": "AWP-CORE-017",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 212,
      "statement": "An update SHOULD carry a complete replacement or patch plus `prior_revision`. When a record has a revision, an update MUST apply only when `prior_revision` equals the effective revision and MUST assign the next integer revision. An update without a satisfiable prior revision is a conflict unless its owning module defines a safe commutative rule. A writer MUST NOT use last-write-wins to silently resolve a conflicting revision. Completion, verification, authorization, and external-side-effect transitions SHOULD cite evidence."
    },
    {
      "id": "AWP-CORE-018",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 247,
      "statement": "The `modules` object may contain module-owned materialized state keyed by module ID. Module state MUST NOT redefine Core records. A snapshot-only workstate MUST disclose that audit history is absent and SHOULD identify its source frontier or source digest."
    },
    {
      "id": "AWP-CORE-019",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 249,
      "statement": "When valid event history conflicts with a snapshot, event history is authoritative. Detailed replay and divergence rules belong to AWP Synchronization. A Core-only reader MUST at least compare the declared frontiers and report `current`, `stale`, `divergent`, or `unverifiable`; it MUST NOT silently treat a mismatch as current."
    },
    {
      "id": "AWP-CORE-020",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 253,
      "statement": "A Core reader MUST:"
    },
    {
      "id": "AWP-CORE-021",
      "source": "spec/drafts/0.7.0/core.md",
      "line": 264,
      "statement": "A Core writer MUST:"
    },
    {
      "id": "AWP-CAPSULE-001",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 24,
      "statement": "For a project-named Markdown capsule, the default conventional filename is `<project-name>.awp.md`. When the project name is unavailable or ambiguous, producers SHOULD use `project.awp.md`. A producer MAY retain multiple capsule revisions using `<project-name>.v<revision>.awp.md`, for example `awp.v2.awp.md` or `project.v2026-09-04.awp.md`. The filename revision is a human-facing archival label; it is not the AWP protocol version and MUST NOT override `awp_version`, `workstate_id`, `frontier`, `checkpoint`, `generated_digest`, or the `current_workstate` pointer in `.awp.json`. A consumer MUST follow the discovery pointer when one is present."
    },
    {
      "id": "AWP-CAPSULE-002",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 26,
      "statement": "A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing."
    },
    {
      "id": "AWP-CAPSULE-003",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 30,
      "statement": "A project MAY place a `.awp.json` discovery document at its declared project root so that an AWP-aware agent or tool can locate the current workstate without scanning the project. The discovery document is a pointer, not a workstate, trust assertion, or authority grant."
    },
    {
      "id": "AWP-CAPSULE-004",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 43,
      "statement": "`awp_schema`, `awp_discovery_version`, `current_workstate`, and `specification` are REQUIRED. `awp_schema` identifies this AWP discovery schema without assuming that a copied project contains AWP's source tree. `fallback_workstates` is optional. `specification` identifies the exact specification artifact governing the current workstate. It SHOULD be an immutable, version-pinned URI when the specification is hosted remotely, such as a tagged GitHub raw URL. It MUST NOT use a moving branch URL as though it were version-pinned. A sandboxed or offline project MAY point `specification` to a repository-relative local copy instead."
    },
    {
      "id": "AWP-CAPSULE-005",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 45,
      "statement": "Relative paths are resolved from the directory containing `.awp.json`. A local path MUST be relative, normalized, remain within the project root after resolution, and identify a regular file. A URI MAY be used only by a binding that defines retrieval and security behavior; discovering a URI MUST NOT trigger automatic network access."
    },
    {
      "id": "AWP-CAPSULE-006",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 47,
      "statement": "An AWP-aware project-entry implementation SHOULD look for `.awp.json` in the project root supplied by its host, repository binding, invocation, or configuration. It MUST NOT search above that root. When the file is present, it MUST validate [the discovery schema](../../../schemas/awp-discovery-0.2.schema.json) before following a pointer. It then opens `current_workstate` using the normal Capsule and Core procedures. It MUST verify that the capsule declares the same `specification` reference. A mismatch is invalid discovery and MUST NOT be resolved by silently choosing either reference."
    },
    {
      "id": "AWP-CAPSULE-007",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 49,
      "statement": "If `.awp.json` is missing, invalid, unsafe, or points to unavailable content, the implementation reports discovery as `absent`, `invalid`, `unsafe`, or `unavailable`. It MAY accept an explicitly supplied capsule instead. It MUST NOT silently select a fallback whose identity conflicts with an already selected workstate."
    },
    {
      "id": "AWP-CAPSULE-008",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 51,
      "statement": "Agent-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` are outside AWP. They MAY point to `.awp.json` or directly to a capsule, but their presence is not required for AWP conformance."
    },
    {
      "id": "AWP-CAPSULE-009",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 55,
      "statement": "Every complete directory, Markdown capsule, or package MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first."
    },
    {
      "id": "AWP-CAPSULE-010",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 57,
      "statement": "The briefing MUST begin with metadata containing:"
    },
    {
      "id": "AWP-CAPSULE-011",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 67,
      "statement": "Generated content MUST occur inside exactly one marker pair:"
    },
    {
      "id": "AWP-CAPSULE-012",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 92,
      "statement": "`specification` identifies the exact specification artifact that governs the workstate. It follows the same version-pinned URI and repository-relative local-path rules as repository discovery. A reader MUST NOT silently substitute another specification. An unavailable or unsupported declared specification makes the workstate `unverifiable` for protocol interpretation."
    },
    {
      "id": "AWP-CAPSULE-013",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 124,
      "statement": "`WORK.md` and `manifest.json` are REQUIRED. `events.jsonl` is REQUIRED unless the manifest declares a snapshot-only representation. `snapshot.json`, `artifacts/`, `modules/`, and `views/` are optional."
    },
    {
      "id": "AWP-CAPSULE-014",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 126,
      "statement": "Each `events.jsonl` line contains one complete JSON event. Module-specific events remain in this unified ledger. Module-owned auxiliary data MAY occupy separate files under `modules/`, but their manifest locations are authoritative; directory names are conventional only."
    },
    {
      "id": "AWP-CAPSULE-015",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 132,
      "statement": "A `.awp.md` file begins with briefing metadata and human Markdown, followed by machine sections. Front matter MUST declare `capsule_boundary`, a lowercase hexadecimal token containing at least 128 bits of unpredictable entropy."
    },
    {
      "id": "AWP-CAPSULE-016",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 146,
      "statement": "It may contain attributes of the form ` name=\"value\"` before ` -->`. Attribute names match `[a-z][a-z0-9_-]*`; values MUST NOT contain a quote, CR, LF, or `-->`."
    },
    {
      "id": "AWP-CAPSULE-017",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 165,
      "statement": "The boundary token MUST NOT occur in decoded section content. A writer detecting a collision MUST generate a new boundary or encode the content using a binary-safe encoding such as base64. Binary artifacts MUST use base64 or a registered binary-safe encoding."
    },
    {
      "id": "AWP-CAPSULE-018",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 167,
      "statement": "A reader MUST validate marker pairing, reject duplicate authoritative sections, verify each module section against a matching manifest declaration, reject malformed boundaries, and preserve unknown sections during lossless rewriting. It MUST NOT infer machine state from arbitrary Markdown headings or code examples outside marked sections."
    },
    {
      "id": "AWP-CAPSULE-019",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 173,
      "statement": "Unpacking MUST preserve logical paths, bytes, IDs, module declarations, and references. Readers MUST reject absolute paths, parent traversal, duplicate normalized paths, case-folding collisions on case-insensitive targets, symlink escapes, and members exceeding configured size or decompression limits."
    },
    {
      "id": "AWP-CAPSULE-020",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 175,
      "statement": "Writers SHOULD place `WORK.md` and `manifest.json` before large members for preview efficiency. Physical member order has no semantic meaning."
    },
    {
      "id": "AWP-CAPSULE-021",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 205,
      "statement": "Standard representation kinds are `package-path`, `capsule-section`, `remote`, and `events-only`. A remote module location does not make the workstate self-contained and MUST disclose retrieval requirements. Secrets MUST NOT appear in locations."
    },
    {
      "id": "AWP-CAPSULE-022",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 211,
      "statement": "A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing. A reader claiming repository-discovery support MUST implement Section 2 and expose discovery failures."
    },
    {
      "id": "AWP-CAPSULE-023",
      "source": "spec/drafts/0.7.0/capsule.md",
      "line": 213,
      "statement": "A Capsule writer MUST create an unambiguous representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content. A writer that emits `.awp.json` MUST produce a schema-valid, traversal-safe discovery document."
    },
    {
      "id": "AWP-HANDOFF-001",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 15,
      "statement": "A workstate containing a handoff record MUST declare this module. It MUST mark the module required when the requested continuation depends on the record's completeness, dependency, resumption, or authority-ceiling semantics."
    },
    {
      "id": "AWP-HANDOFF-002",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 25,
      "statement": "`portable` is RECOMMENDED for cross-system continuation. A portable handoff MUST identify each required dependency as `available`, `retrievable`, `unavailable`, or `withheld`. A full handoff MUST enumerate omissions and MUST NOT imply that an entire repository, transcript, or runtime is present when it is not."
    },
    {
      "id": "AWP-HANDOFF-003",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 37,
      "statement": "Levels are cumulative. `operational` MUST satisfy every semantic requirement. `exact` MUST satisfy semantic and operational requirements unless explicitly labeled `private_nonportable`, in which case it is not a conforming portable handoff."
    },
    {
      "id": "AWP-HANDOFF-004",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 89,
      "statement": "Required fields are `id`, `type`, `module`, `checkpoint`, `completeness`, `intended_audience`, `requested_action`, `authority_ceiling`, and `resumption_level`. `module` MUST be `urn:awp:handoff`."
    },
    {
      "id": "AWP-HANDOFF-005",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 91,
      "statement": "`authority_ceiling` is an upper bound asserted by the sender. It does not grant those authorities; the receiver may operate under a stricter ceiling. A missing, unknown, or ambiguous ceiling MUST be treated as no authority for external side effects."
    },
    {
      "id": "AWP-HANDOFF-006",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 126,
      "statement": "Required fields are `id`, `type`, `module`, `checkpoint`, `mode`, `read_first`, `required_artifacts`, `recommended_next_action`, `freshness_policy`, `on_stale`, and `authority_ceiling`. `type` MUST be `resume`, `module` MUST be `urn:awp:handoff`, and the only standard mode in this version is `project_reentry`. Optional `handoff` identifies the handoff record this resume record refines."
    },
    {
      "id": "AWP-HANDOFF-007",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 128,
      "statement": "When both a Resume and referenced Handoff record are present, the Resume record is the project-entry instruction for the named checkpoint. Its `authority_ceiling` MUST be equal to or narrower than the Handoff ceiling, and its action MUST be a compatible refinement of the Handoff requested action. A receiver that cannot establish those conditions MUST qualify or reject the resume; it MUST NOT choose one record silently."
    },
    {
      "id": "AWP-HANDOFF-008",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 136,
      "statement": "`on_stale` is `refresh_workstate`, `report_and_stop`, or `read_only_orientation`. A receiver MUST NOT interpret any value as permission to perform an external side effect from stale or unverifiable state."
    },
    {
      "id": "AWP-HANDOFF-009",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 138,
      "statement": "`repository_state`, when present, binds a resume checkpoint to the repository and immutable source revision against which it was prepared. Each entry requires `repository` and `source_revision` and MAY narrow comparison using `path_scope`. A `project_reentry` record that depends on source-controlled artifacts MUST include each repository state required to assess safe continuation."
    },
    {
      "id": "AWP-HANDOFF-010",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 140,
      "statement": "A receiver that can identify the local repository revision MUST compare it with `source_revision`. A mismatch makes the repository binding stale. When it can obtain a diff, claims, evidence, change sets, and verification results scoped to changed paths MUST be treated as stale until reverified or explicitly re-scoped. When the receiver cannot identify or compare the repository revision, the binding is unverifiable rather than current. A matching revision does not establish that remote services, credentials, or other dependencies remain current."
    },
    {
      "id": "AWP-HANDOFF-011",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 142,
      "statement": "`read_first` is an ordered presentation hint, not causal ordering or authority. A receiver MAY load additional records required to interpret dependencies, evidence, conflicts, or safety constraints. It MUST NOT omit relevant required state merely to meet a context budget. Optional context-selection metadata MAY state a token or byte budget, priority groups, and deferred artifacts, but it cannot weaken completeness, freshness, or authority requirements."
    },
    {
      "id": "AWP-HANDOFF-012",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 144,
      "statement": "A Resume Profile receiver MUST:"
    },
    {
      "id": "AWP-HANDOFF-013",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 159,
      "statement": "A Handoff writer MUST:"
    },
    {
      "id": "AWP-HANDOFF-014",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 173,
      "statement": "A Handoff reader MUST:"
    },
    {
      "id": "AWP-HANDOFF-015",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 193,
      "statement": "Reports SHOULD record capsule size where applicable, token usage, author and receiver versions, unsupported modules, omissions, false assumptions, safety failures, and resulting artifact quality. A single successful task is not evidence of general interoperability."
    },
    {
      "id": "AWP-HANDOFF-016",
      "source": "spec/drafts/0.7.0/handoff.md",
      "line": 197,
      "statement": "A Handoff reader implements the receiver procedure and exposes limitations. A Handoff writer implements the producer procedure and makes accurate claims. A Resume Profile reader additionally implements Section 5 and declares the `resume-profile` capability. A system MAY support handoff and resume records without supporting the Capsule module; repository discovery requires Capsule support."
    },
    {
      "id": "AWP-ARTIFACT-001",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 15,
      "statement": "A workstate using Artifact fields MUST declare this module. It MUST mark the module required when continuation depends on retrieving, verifying, executing, or distinguishing the availability of an artifact."
    },
    {
      "id": "AWP-ARTIFACT-002",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 49,
      "statement": "Artifact-module fields live under `modules[\"urn:awp:artifact\"]`. Required module fields are `status` and `locations`. An available packaged artifact MUST include `media_type`, `size`, and `integrity`. Statuses are `available`, `retrievable`, `unavailable`, `withheld`, `redacted`, and `superseded`."
    },
    {
      "id": "AWP-ARTIFACT-003",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 51,
      "statement": "Logical identity and content identity are distinct. A modified artifact receives a new record ID and content digest but MAY retain the same `logical_name`. A change record links before and after versions."
    },
    {
      "id": "AWP-ARTIFACT-004",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 65,
      "statement": "Private kinds MUST use collision-resistant namespaced values."
    },
    {
      "id": "AWP-ARTIFACT-005",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 67,
      "statement": "Package paths MUST be relative, normalized, and traversal-safe. Secrets, bearer tokens, cookies, and authorization headers MUST NOT appear in locations. Retrieval requirements may refer to separately authorized credentials without containing them."
    },
    {
      "id": "AWP-ARTIFACT-006",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 69,
      "statement": "An absolute local path is a hint tied to an identified environment. A receiver MUST NOT assume that it names the same resource locally."
    },
    {
      "id": "AWP-ARTIFACT-007",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 73,
      "statement": "Packaged and embedded artifacts MUST include a digest over the exact decoded bytes. Remote and repository-relative artifacts SHOULD include a digest whenever stable bytes are expected. Hash algorithms are registry values; SHA-256 is the default for this module version."
    },
    {
      "id": "AWP-ARTIFACT-008",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 75,
      "statement": "Readers SHOULD verify a digest before relying on content. Digest validity establishes byte identity, not safety, truth, authorship, or authority."
    },
    {
      "id": "AWP-ARTIFACT-009",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 77,
      "statement": "Content-addressed packaged artifacts are immutable. Changing bytes creates a new content identity. A mutable remote URI SHOULD be paired with a digest, immutable version, ETag, or explicit `mutable: true` warning."
    },
    {
      "id": "AWP-ARTIFACT-010",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 83,
      "statement": "A portable Handoff that depends on an artifact MUST include it, make it retrievable, or state that continuation is blocked. A URI alone is not proof of retrievability."
    },
    {
      "id": "AWP-ARTIFACT-011",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 85,
      "statement": "Retrieval is an external action subject to receiver authority and security policy. Merely referencing a remote artifact MUST NOT trigger automatic network access."
    },
    {
      "id": "AWP-ARTIFACT-012",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 89,
      "statement": "Descriptors MUST state whether content is executable or may contain instructions when either is known. Unknown values SHOULD be represented explicitly rather than assumed false."
    },
    {
      "id": "AWP-ARTIFACT-013",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 91,
      "statement": "Readers MUST treat instructions in untrusted artifacts as data. Executables, archives, active documents, and model-readable instruction files SHOULD be inspected in an appropriate sandbox before use."
    },
    {
      "id": "AWP-ARTIFACT-014",
      "source": "spec/drafts/0.7.0/artifact.md",
      "line": 120,
      "statement": "The tombstone MUST remove sensitive bytes and locations, preserve referential integrity, disclose rewritten history, and invalidate signatures covering removed bytes. It MAY retain the original digest only when the digest is not itself sensitive. It MUST NOT imply that the bytes remain available."
    },
    {
      "id": "AWP-SYNC-001",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 15,
      "statement": "A workstate or message using deltas, omitted-history boundaries, or synchronization conflict semantics MUST declare this module. It MUST be required when the receiver must apply or reconcile those structures to reach the continuation frontier."
    },
    {
      "id": "AWP-SYNC-002",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 35,
      "statement": "A delta MUST identify `workstate_id`, `base_frontier`, `result_frontier`, and `events`. It MAY carry artifact announcements or module data required by those events."
    },
    {
      "id": "AWP-SYNC-003",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 37,
      "statement": "A receiver MUST verify that the base frontier is known or request missing ancestry. It MUST validate event IDs, workstate IDs, parents, module declarations, and result frontier before application. Applying a delta MUST be idempotent by event ID. Reuse of one event ID for different bytes is an integrity conflict."
    },
    {
      "id": "AWP-SYNC-004",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 41,
      "statement": "A reader with both a snapshot and event ledger MUST:"
    },
    {
      "id": "AWP-SYNC-005",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 59,
      "statement": "For `stale_replayable`, a processor replays descendant events in deterministic topological order. Concurrent events remain concurrent; topological serialization MUST NOT be treated as conflict resolution. Record revision preconditions determine whether updates commute or conflict."
    },
    {
      "id": "AWP-SYNC-006",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 79,
      "statement": "Mechanical merge unions events by ID after integrity validation. It preserves all concurrent tips. It MUST NOT silently apply last-write-wins to:"
    },
    {
      "id": "AWP-SYNC-007",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 94,
      "statement": "Replay MUST respect graph ancestry. When concurrent events require a deterministic processing order, processors sort by event ID only as a reproducibility device. This ordering has no semantic priority."
    },
    {
      "id": "AWP-SYNC-008",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 98,
      "statement": "Unknown optional-module events remain graph nodes and participate in frontier computation. A processor MUST NOT advance a derived snapshot through an unknown event when doing so could alter a required Core or module result; it reports the projection as unverifiable instead."
    },
    {
      "id": "AWP-SYNC-009",
      "source": "spec/drafts/0.7.0/synchronization.md",
      "line": 102,
      "statement": "AWP 0.7.0 does not define destructive log compaction. A writer MAY create a summary or snapshot-only export, but it MUST disclose omitted history and MUST NOT claim `full` completeness."
    },
    {
      "id": "AWP-COORD-001",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 72,
      "statement": "A writer MUST NOT advertise a level whose required behaviors it does not implement. A reader MAY support a lower level, but it MUST reject the workstate for safe continuation when the module is required and unsupported semantics affect the requested action."
    },
    {
      "id": "AWP-COORD-002",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 84,
      "statement": "An implementation MAY adopt `coordination-awareness` before implementing the complete integration-assurance workflow. Capability declarations state what records can be processed; conformance levels state how rigorously they are processed."
    },
    {
      "id": "AWP-COORD-003",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 110,
      "statement": "`id`, `type`, `module`, `revision`, `status`, `created_by`, and `created_at` are required. `revision` begins at `1`. An update MUST identify `prior_revision` in its event and produce exactly `prior_revision + 1`."
    },
    {
      "id": "AWP-COORD-004",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 116,
      "statement": "Unknown fields MUST be preserved by lossless processors. A processor MUST distinguish a registered record type above its advertised capability or conformance level from a genuinely unregistered type. It preserves registered higher-level records without interpreting them and may still perform lower-level actions that do not depend on their meaning. A genuinely unregistered type owned by this required module makes only the affected action or projection `unverifiable` unless a declared compatibility rule permits preservation without interpretation. A lower-level reader MAY always perform safe display or export."
    },
    {
      "id": "AWP-COORD-005",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 125,
      "statement": "Safety-relevant references in contracts, preconditions, readiness decisions, verification, overlaps, and integration plans MUST be revision-pinned. A missing, superseded, or contested pinned revision remains historically addressable but MUST NOT be silently replaced by another revision. An unpinned reference that is absent, contested, or ambiguous is unresolved."
    },
    {
      "id": "AWP-COORD-006",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 131,
      "statement": "The passage of time never changes projected state. An identified actor or service MUST emit a valid timeout, expiration, or deadline-observation event under a declared clock authority. Until that event is present, a deadline may be overdue but the prior projected lifecycle state remains unchanged; processors SHOULD surface the overdue condition."
    },
    {
      "id": "AWP-COORD-007",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 208,
      "statement": "Within one workstate, an active alias MUST resolve to at most one semantic definition. Merging ambiguous aliases creates diagnostic `AWP-COORD-REGISTRY-AMBIGUOUS` and affected overlap analysis becomes `unknown` until resolved."
    },
    {
      "id": "AWP-COORD-008",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 212,
      "statement": "Selector comparison across repository revisions is a C2 correctness operation. An analyzer MUST resolve both selectors against their pinned bases and attempt to relate moved, renamed, extracted, or replaced targets using a declared selector profile. Resolution results are `same`, `related`, `different`, `unresolvable`, or `ambiguous`, with evidence and confidence. `unresolvable` or `ambiguous` forces overlap classification `unknown`; it MUST NOT yield `none`."
    },
    {
      "id": "AWP-COORD-009",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 214,
      "statement": "Language-specific selector syntax and drift algorithms belong to registered adapter profiles. The initial reference implementation SHOULD provide Python AST and TypeScript compiler-symbol profiles, but their identifiers and outputs remain usable by agents implemented in any language."
    },
    {
      "id": "AWP-COORD-010",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 218,
      "statement": "A scope is a first-class record selecting a physical or semantic region. Intents, claims, change sets, and contracts reference it by ID and revision. An inline selector MAY be used as an unshared query value, but an inline selector is not a scope record and cannot be revised or used as a dependency target."
    },
    {
      "id": "AWP-COORD-011",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 241,
      "statement": "Physical selector kinds include `repository`, `directory`, `file`, `symbol`, `syntax_node`, `configuration_key`, `schema_object`, `generated_output`, `test`, and `fixture`. Line ranges are hints and MUST NOT be the only selector for a safety-relevant claim."
    },
    {
      "id": "AWP-COORD-012",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 247,
      "statement": "Authors SHOULD declare relied-upon reads only for assumptions whose incompatible change could invalidate the output, not every file or symbol inspected. Tools may propose candidates from dependency traces, but the published set SHOULD be summarized at stable interface, invariant, schema, or behavior boundaries. Fine-grained automatic reads MAY remain evidence behind that summary. This keeps the reverse index useful rather than turning ordinary repository browsing into conflicts."
    },
    {
      "id": "AWP-COORD-013",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 251,
      "statement": "An actor SHOULD publish an intent before materially changing shared state."
    },
    {
      "id": "AWP-COORD-014",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 296,
      "statement": "If observed work expands beyond the declared scope, the writer MUST either update the intent before publishing a ready change set or record an explicit deviation. Under a C2 enforcing policy, unresolved material under-declaration prevents `ready`."
    },
    {
      "id": "AWP-COORD-015",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 327,
      "statement": "Observed-scope lifecycle statuses are `final` and `superseded`; outcome is `complete`, `partial`, or `error`. The analyzer, base, result, method, and evidence digest MUST be recorded. `declared_not_observed` is informational unless policy says otherwise. `undeclared` MUST be evaluated for new overlaps and may stale earlier acknowledgements. An omitted effect or scope means unknown; an explicitly present empty array asserts that none were observed or declared under the stated method."
    },
    {
      "id": "AWP-COORD-016",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 374,
      "statement": "`unknown` MUST NOT be treated as `compatible`. The configured policy determines whether it warns, negotiates, or blocks."
    },
    {
      "id": "AWP-COORD-017",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 400,
      "statement": "`accepted`, `rejected`, `timed_out`, `cancelled`, and `escalated` are terminal. Escalation after rejection or timeout creates a successor negotiation referencing the terminal record. A further round likewise creates a successor. A processor MUST NOT infer acceptance from silence unless the declared decision policy explicitly defines silence and the enforcing authority supports it."
    },
    {
      "id": "AWP-COORD-018",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 402,
      "statement": "An accepted proposal MAY create commitments. A commitment identifies:"
    },
    {
      "id": "AWP-COORD-019",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 443,
      "statement": "`kind` is `unanimous`, `threshold`, `named_participants`, or `authorized_owner`. `eligible_participants` is required except for `authorized_owner`; `threshold` is required only for `threshold` and MUST be between 1 and the eligible count. `required_participants` defaults to empty. `abstention` is `counts_as_no`, `reduces_eligible`, or `prohibited`. Votes and acceptances MUST pin `decides_revision`. Role names alone are not participant identity; a policy using roles must resolve them to an uncontested eligible actor set before evaluation."
    },
    {
      "id": "AWP-COORD-020",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 458,
      "statement": "Global contract status MUST NOT be derived from a single participant's adoption status. Each participant has one of `unaware`, `reviewing`, `accepted`, `implementing`, `implemented`, `verified`, `rejected`, `withdrawn`, or `not_applicable`, with its own evidence and revision."
    },
    {
      "id": "AWP-COORD-021",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 460,
      "statement": "The contract's decision policy specifies named required parties or a quorum. A contract MUST NOT become `accepted`, `implemented`, or `verified` until that state's policy is satisfied."
    },
    {
      "id": "AWP-COORD-022",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 489,
      "statement": "Precondition lifecycle statuses are `active`, `retired`, and `superseded`. `on_false` is `warn`, `block_ready`, `stale`, or `escalate`. `on_unknown` is `warn`, `block_ready`, or `escalate`; it MUST NOT silently pass."
    },
    {
      "id": "AWP-COORD-023",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 508,
      "statement": "`pure` evaluators read only the identified AWP projection or supplied bytes. Repository-relative and host-relative results MUST record the repository or environment they observed. All evaluators MUST be side-effect-free with respect to the project, deterministic for identical declared inputs, bounded by an explicit timeout, and return `error` rather than partial success after timeout or internal failure. Constraint syntax is owned by the registered evaluator-interface version; an implementation MUST NOT guess unsupported syntax."
    },
    {
      "id": "AWP-COORD-024",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 510,
      "statement": "An asserted precondition records a natural-language statement, asserting actor, scope, epistemic status, evidence if any, and required reviewer or authority. It MUST NOT be presented as machine-verified."
    },
    {
      "id": "AWP-COORD-025",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 619,
      "statement": "A verification result MUST bind the claim being checked to exact inputs."
    },
    {
      "id": "AWP-COORD-026",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 658,
      "statement": "For each event that changes a record revision or status, a C1 projector MUST:"
    },
    {
      "id": "AWP-COORD-027",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 682,
      "statement": "An adapter MUST reject `atomic` when its repository or transaction mechanism cannot supply the claimed atomic boundary. Rollback is a separately recorded operation and MUST NOT be assumed successful."
    },
    {
      "id": "AWP-COORD-028",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 684,
      "statement": "Before starting integration, the owner MUST refresh available coordination events, compare the target base, re-evaluate expiring or base-bound preconditions, confirm contract revisions, and re-open any invalidated overlap dispositions."
    },
    {
      "id": "AWP-COORD-029",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 702,
      "statement": "A successful source-control merge MUST NOT by itself transition an integration to `completed` when combined semantic verification is required."
    },
    {
      "id": "AWP-COORD-030",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 710,
      "statement": "A C1 projector MUST:"
    },
    {
      "id": "AWP-COORD-031",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 742,
      "statement": "Synchronization 0.2 governs retention and compaction: a snapshot does not authorize destructive pruning, and snapshot-only exports disclose omitted history. A portable Coordination view MAY omit terminal records irrelevant to the requested continuation only when it declares the omission and does not claim full audit completeness. It MUST retain or make retrievable every active dependency, unresolved conflict, governing contract, precondition, verification, authority decision, and causal record needed to justify current readiness. Physical deletion or redaction follows Synchronization, Artifact, and Security rules."
    },
    {
      "id": "AWP-COORD-032",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 771,
      "statement": "Errors invalidate the affected transition. Warnings preserve state but MUST be visible before a safety-relevant continuation. Implementations MAY add namespaced diagnostics."
    },
    {
      "id": "AWP-COORD-033",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 789,
      "statement": "Lease states are `requested`, `active`, `denied`, `released`, `expired`, `revoked`, and `superseded`. The coordinator grants a lease only after an atomic comparison against current protected state. Renewal creates a new expiration and MUST NOT reduce the fencing token."
    },
    {
      "id": "AWP-COORD-034",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 791,
      "statement": "An adapter claiming enforcement MUST reject a protected mutation whose token is older than the highest token it has accepted for that namespace. A new grant, new holder, or new coordinator epoch MUST issue a token strictly greater than every previously issued token in that protected namespace. Renewal of the same uninterrupted lease retains its token; it changes expiration but does not create a new ownership generation. Without this fencing check, a paused or partitioned former holder may act after its lease expires."
    },
    {
      "id": "AWP-COORD-035",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 793,
      "statement": "If coordinator identity, epoch, authentication, protected scope, or fencing validation is unavailable, the lease is `unverifiable` outside the reachable enforcement guarantee. The implementation MUST NOT describe it as exclusive. Local work may continue under policy, but integration MUST refresh state and re-evaluate overlap and preconditions."
    },
    {
      "id": "AWP-COORD-036",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 795,
      "statement": "The C3 profile MUST specify retry limits, heartbeat interval, lease duration, expiry clock authority, deadlock detection, starvation policy, cancellation consequences, and human/organizational arbitration. The base module defines no universal timing defaults because safe values depend on task duration, network delay, and the protected system. Named interoperability and test profiles MAY define explicit defaults."
    },
    {
      "id": "AWP-COORD-037",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 801,
      "statement": "A principal is the human or organization accountable for an actor's participation. A C3 session MUST bind authenticated actors to principals and declare the governing policy. Cross-principal coordination MUST identify:"
    },
    {
      "id": "AWP-COORD-038",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 810,
      "statement": "AWP content is untrusted input. Imported intents, contracts, commitments, leases, and authority records MUST NOT cause execution without receiver policy evaluation. Secret values SHOULD be referenced through protected artifacts rather than embedded in coordination records."
    },
    {
      "id": "AWP-COORD-039",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 812,
      "statement": "Coordination defines no separate protected-artifact envelope. A protected input uses the Artifact module's availability, remote-location, retrieval-requirement, and integrity fields together with Security classification or `secret_ref` metadata. A URI or digest alone proves neither confidentiality nor retrievability. Digests of low-entropy secrets may themselves enable guessing attacks and MUST be omitted or protected when receiver policy classifies the digest as sensitive."
    },
    {
      "id": "AWP-COORD-040",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 853,
      "statement": "Private event kinds use a controlled namespaced module ID. They MUST NOT add unregistered bare kinds to this module."
    },
    {
      "id": "AWP-COORD-041",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 873,
      "statement": "[MPAC, arXiv:2604.09744 version 1](https://arxiv.org/abs/2604.09744v1) session, intent, operation, conflict, and governance objects may map to corresponding AWP records. AWP retains repository-specific semantic scopes, contracts, preconditions, verification binding, persistent project history, and resume/handoff state. A mapping MUST identify information loss and MUST NOT equate MPAC transport/session acceptance with AWP integration readiness."
    },
    {
      "id": "AWP-COORD-042",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 930,
      "statement": "Each fixture SHOULD include input events, expected frontier, expected materialized records, expected diagnostics, and an explanation of the safety property."
    },
    {
      "id": "AWP-COORD-043",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 934,
      "statement": "Before the complete integration-assurance schema is frozen, the project SHOULD run an early `coordination-awareness` experiment comparing chat-only coordination with durable intents, pinned scopes, overlaps, acknowledgements, and conflict-preserving projection. It MUST measure false-positive and false-negative overlap classifications, authoring cost, coordination delay, and whether warnings arrive before conflicting implementation. Results may change the scope and record model before further standardization."
    },
    {
      "id": "AWP-COORD-044",
      "source": "spec/drafts/0.7.0/coordination.md",
      "line": 949,
      "statement": "1. Canonical JSON and digest rules remain a Core/Artifact/Security family issue and must be resolved before signed coordination evidence is portable. The family profile should evaluate RFC 8785 JCS while explicitly handling its I-JSON, IEEE-754 number, and Unicode-preservation constraints; Coordination MUST NOT select a conflicting local canonicalization."
    },
    {
      "id": "AWP-SECURITY-001",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 17,
      "statement": "A workstate using Security metadata MUST declare this module. It MUST be required when interpreting a registered signature, encryption, redaction, or handling profile is necessary for the receiver's declared continuation. Core safety rules still apply when this module is absent."
    },
    {
      "id": "AWP-SECURITY-002",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 49,
      "statement": "Classification and privacy vocabularies may be organization-specific but private values MUST be namespaced. `contains_secrets` is `true`, `false`, or `unknown`. A writer MUST NOT use `false` when secret-scan status is `findings`, `not_run`, or `unknown`."
    },
    {
      "id": "AWP-SECURITY-003",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 53,
      "statement": "Receivers SHOULD place newly imported workstates in local quarantine until they evaluate:"
    },
    {
      "id": "AWP-SECURITY-004",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 64,
      "statement": "Quarantine is receiver-owned state. A serialized assertion MAY describe the sender's handling state but MUST NOT disable receiver quarantine or grant trust."
    },
    {
      "id": "AWP-SECURITY-005",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 68,
      "statement": "Text in artifacts, summaries, claims, evidence, transcripts, extensions, and module data may contain instructions. Merely parsing, rendering, retrieving, verifying, or signing a workstate MUST NOT authorize execution."
    },
    {
      "id": "AWP-SECURITY-006",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 70,
      "statement": "Readers MUST distinguish descriptive content from an authorized requested action. Unknown modules and executable content MUST NOT run automatically. Module processors SHOULD be isolated according to risk."
    },
    {
      "id": "AWP-SECURITY-007",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 74,
      "statement": "An imported task classified as `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, or `destructive` MUST NOT become ready or execute solely because the workstate requests it."
    },
    {
      "id": "AWP-SECURITY-008",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 76,
      "statement": "The receiver re-evaluates current identity, resource scope, authority source, conditions, expiration, revocation, confirmation requirements, and local policy. A receiver with greater access than the sender MUST avoid becoming a confused deputy."
    },
    {
      "id": "AWP-SECURITY-009",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 80,
      "statement": "Writers SHOULD use secret references instead of values:"
    },
    {
      "id": "AWP-SECURITY-010",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 90,
      "statement": "A reference does not authorize resolution. Exporters MUST apply their configured secret and data-loss-prevention policy to included event payloads, execution output, evidence, generated views, module data, and artifact paths. Scan status is `passed`, `findings`, `not_run`, or `unknown`. Passing is evidence of a check, not proof of absence."
    },
    {
      "id": "AWP-SECURITY-011",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 92,
      "statement": "Writers SHOULD omit irrelevant transcripts and personal data and support classification, audience, retention, and jurisdiction metadata. Omission must not be disguised by a stronger completeness claim."
    },
    {
      "id": "AWP-SECURITY-012",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 96,
      "statement": "Physical redaction creates a new workstate history lineage. It MUST:"
    },
    {
      "id": "AWP-SECURITY-013",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 111,
      "statement": "Signatures may cover individual events, frontier manifests, snapshots, artifact manifests, module data, or complete packages. Signature metadata MUST identify algorithm, key identifier, coverage, canonicalization profile, signer, and verification status."
    },
    {
      "id": "AWP-SECURITY-014",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 123,
      "statement": "AWP Security 0.4.0 does not select a normative canonicalization or signature algorithm. Implementations MUST NOT claim interoperable AWP signature conformance without naming an external or future registered signature profile."
    },
    {
      "id": "AWP-SECURITY-015",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 127,
      "statement": "Encryption metadata may describe package-wide, module-level, artifact-level, or recipient-based protection. It MUST identify the encryption profile and protected scope without exposing keys or secret values."
    },
    {
      "id": "AWP-SECURITY-016",
      "source": "spec/drafts/0.7.0/security.md",
      "line": 135,
      "statement": "When Capsule or Artifact is used, processors MUST apply their traversal, normalization, size, decompression, integrity, executable-content, and retrieval rules. A signature over an unsafe archive does not make extraction safe."
    }
  ]
}
```

## Core schema — `schemas/awp-core-0.7.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:core:0.7.0",
  "title": "AWP Core 0.7",
  "description": "Structural schema for AWP 0.7 manifests, event envelopes, snapshots, actors, authority declarations, and Core records.",
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
            "kind": { "enum": ["package-path", "capsule-section", "remote", "events-only"] }
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
        "awp_version": { "type": "string", "pattern": "^0\\.7\\.[0-9]+$" },
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
              "version": { "type": "string", "pattern": "^0\\.7\\.[0-9]+$" },
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
        "awp_version": { "type": "string", "pattern": "^0\\.7\\.[0-9]+$" },
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

## Coordination schema — `schemas/awp-coordination-0.4.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:coordination:0.4.0",
  "title": "AWP Coordination 0.4",
  "description": "Structural schema for AWP Coordination 0.4 records and event envelopes.",
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
    "repositoryState": {
      "type": "object",
      "required": ["repository", "revision"],
      "properties": {
        "repository": { "$ref": "#/$defs/identifier" },
        "revision": { "$ref": "#/$defs/identifier" }
      },
      "additionalProperties": true
    },
    "selector": {
      "type": "object",
      "required": ["kind"],
      "properties": {
        "kind": {
          "enum": [
            "repository", "directory", "file", "symbol", "syntax_node",
            "configuration_key", "schema_object", "generated_output", "test", "fixture"
          ]
        },
        "repository": { "$ref": "#/$defs/identifier" },
        "base_revision": { "$ref": "#/$defs/identifier" },
        "path": { "type": "string", "minLength": 1 },
        "symbol": { "type": "string", "minLength": 1 }
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
            "conflict", "negotiation", "commitment", "contract", "precondition",
            "precondition_result", "change_set", "verification_result", "dependency",
            "integration_plan", "integration_result", "lease"
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
                  "base": { "$ref": "#/$defs/repositoryState" },
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
                "properties": {
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
                  "base": { "$ref": "#/$defs/repositoryState" },
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
                "required": ["subjects", "repository", "base_revision", "result_revision", "procedure", "environment", "outcome", "observations"],
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
                "properties": {
                  "plan": { "$ref": "#/$defs/pinnedReference" }
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

## Module-registry schema — `schemas/awp-module-registry-0.7.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:module-registry:0.7.0",
  "title": "AWP 0.7 Module Registry",
  "type": "object",
  "required": ["family", "family_version", "event_schema_versions", "modules"],
  "properties": {
    "$schema": { "type": "string" },
    "family": { "const": "AWP" },
    "family_version": { "const": "0.7.0" },
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

## Discovery schema — `schemas/awp-discovery-0.2.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:awp:schema:discovery:0.2.0",
  "title": "AWP Repository Discovery 0.2",
  "description": "Locates the current AWP workstate and its governing specification bundle from a project root.",
  "type": "object",
  "required": ["awp_schema", "awp_discovery_version", "current_workstate", "specification"],
  "properties": {
    "$schema": { "const": "https://json-schema.org/draft/2020-12/schema" },
    "awp_schema": { "const": "urn:awp:schema:discovery:0.2.0" },
    "awp_discovery_version": { "const": "0.2" },
    "current_workstate": { "$ref": "#/$defs/location" },
    "specification": { "$ref": "#/$defs/location" },
    "fallback_workstates": {
      "type": "array",
      "items": { "$ref": "#/$defs/location" },
      "uniqueItems": true
    }
  },
  "additionalProperties": false,
  "$defs": {
    "location": {
      "type": "string",
      "minLength": 1,
      "allOf": [
        { "pattern": "^\\S+$" },
        { "not": { "pattern": "^(?:[A-Za-z]:|/|\\\\)" } },
        { "not": { "pattern": "(?:^|[\\\\/])\\.\\.(?:[\\\\/]|$)" } }
      ]
    }
  }
}
```
