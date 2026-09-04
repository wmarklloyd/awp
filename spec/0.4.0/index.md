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
| [AWP Core](core.md) | `urn:awp:core` | `0.4.0` | required | none |
| [AWP Capsule](capsule.md) | `urn:awp:capsule` | `0.1.0` | optional | Core |
| [AWP Handoff](handoff.md) | `urn:awp:handoff` | `0.1.0` | optional | Core |
| [AWP Artifact](artifact.md) | `urn:awp:artifact` | `0.1.0` | optional | Core |
| [AWP Synchronization](synchronization.md) | `urn:awp:sync` | `0.1.0` | optional | Core |
| [AWP Coordination](coordination.md) | `urn:awp:coordination` | `0.1.0` | experimental | Core, Synchronization |
| [AWP Security](security.md) | `urn:awp:security` | `0.1.0` | optional | Core; Artifact when artifact controls are used |
| [AWP Adapter Framework](adapters.md) | not a payload module | `0.1.0` | informative | binding-specific |

The machine-readable [module registry](modules.json) is normative for the module IDs, versions, document paths, stability labels, and direct dependencies in this release.

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

- [Core schema](../../schemas/awp-core-0.4.schema.json)
- [Module registry](modules.json)
- [Open issue register](open-issues.md)
- [Validation tool](../../tools/validate_spec_0_4.py)
- [0.3.0 feedback evaluation](../../research/model-assisted-reviews/awp-feedback-evaluation.md)

The 0.3.0 monolithic draft remains available as historical design input. The documents listed in Section 2 constitute the AWP 0.4.0 specification family.
