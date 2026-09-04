# AWP Core 0.5.0

**Module ID:** `urn:awp:core`  
**Status:** Required  
**Dependencies:** None  
**Schema:** `../../schemas/awp-core-0.5.schema.json`

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
  "awp_version": "0.5.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "title": "Prepare product launch",
  "created_at": "2026-09-03T18:00:00Z",
  "created_by": "actor:mark",
  "modules": [
    {
      "id": "urn:awp:core",
      "version": "0.5.0",
      "required": true,
      "schema": "schemas/awp-core-0.5.schema.json"
    },
    {
      "id": "urn:awp:handoff",
      "version": "0.2.0",
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

The Core module declaration MUST appear exactly once with version `0.5.x` and `required: true`. Module IDs MUST be unique within the array. A module declaration MUST satisfy the dependency and requiredness rules in the family specification.

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
  "awp_version": "0.5.0",
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

