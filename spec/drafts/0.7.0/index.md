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
