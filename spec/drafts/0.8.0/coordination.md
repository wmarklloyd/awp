# AWP Coordination 0.5.0

**Module ID:** `urn:awp:coordination`  
**Status:** Experimental  
**Depends on:** AWP Core `0.8.x`, AWP Synchronization `0.5.x`  
**Supersedes:** AWP Coordination `0.3.0`  
**Schema:** `../../../schemas/awp-coordination-0.5.schema.json`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Purpose and scope

AWP Coordination defines durable semantic coordination for multiple actors working on a shared project or work product. A work product may be digital, physical, spatial, documentary, analytical, or mixed: source code, a building information model, a room, a roof assembly, a drawing set, a dataset, a schedule, or a manufactured component. It records intended work before integration, dependencies between work, physical and semantic overlap, negotiated commitments, candidate changes, integration preconditions, and verification evidence.

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
9. **Human arbitration is explicit.** When agents cannot safely resolve an interaction, the protocol records a bounded user decision rather than treating silence, convenience, or one agent's preference as authority.

## 3. Capability profiles and Cooperation Contract integration

The module declaration advertises the Coordination capabilities actually implemented and, when Cooperation is active, the selected Cooperation Contract. Coordination capabilities describe component behavior; `COOP-1`, `COOP-2`, and `COOP-3` are the only cumulative project-level work-coordination conformance claims in AWP 0.8. Portable collaboration has no named Cooperation Contract, and optional consultation is configured independently of work coordination.

```json
{
  "id": "urn:awp:coordination",
  "version": "0.5.0",
  "required": false,
  "capabilities": [
    "presence-monitoring",
    "intents",
    "contracts",
    "change-sets",
    "typed-preconditions",
    "deterministic-projection"
  ],
  "configuration": {
    "cooperation_contract": "COOP-1",
    "unknown_overlap_policy": "warn",
    "lease_enforcement": "none"
  }
}
```

The Cooperation Contract maps those capabilities into one cumulative ladder:

| Contract | Coordination behavior incorporated by the contract |
|---|---|
| No Cooperation Contract | Portable records and asynchronous consultation may be exchanged, with no active-coordination guarantee |
| `COOP-1` | Coordination awareness, deterministic projection, atomic guarded-scope decisions, bounded participant leases, checkpoint freshness, recovery, and user-mediated escalation for material work decisions |
| `COOP-2` | All COOP-1 work behavior plus semantic awareness, integration assurance, and optionally enabled managed inter-agent collaboration under a decision-owner authorization and declared budget |
| `COOP-3` | All COOP-2 work behavior plus authenticated protected mutation, epochs, fencing, and a declared scalable operating envelope |

The following table attributes the Coordination mechanisms to their minimum contract. A mechanism may be implemented below that level, but it MUST NOT be used to support a higher contract claim until its listed composition is present.

| Mechanism sections | Minimum contract | Boundary |
|---|---|---|
| §§4, 6 physical selectors/access modes, 7, 9 physical overlap, 17 structural projection | `COOP-1` | Durable physical-scope collision reduction, record-validity checks, actual-scope reconciliation, guarded decisions, and checkpoint/recovery |
| §5; §6 semantic targets and relied-upon reads; §§8, 10–16; §17 dependency-staleness propagation | `COOP-2` | Semantic evidence and selector resolution, dependency predicate evaluation and propagation, negotiation, readiness, and integration assurance |
| §19 and protected portions of §20 | `COOP-3` | Authenticated principals, live protected mutation, epochs, and fencing |
| §§1–3, 18, 21–27 | baseline or informative as marked | Definitions, diagnostics, mappings, fixtures, maturity, and open issues do not independently establish a contract claim |

A processor MUST NOT advertise a Cooperation Contract whose required composed behaviors it does not implement. A reader MAY support a weaker contract, but it MUST reject safe continuation when unsupported required semantics affect the requested action. A component such as a projector, registry, or enforcing gateway advertises capabilities and evidence rather than claiming a complete contract by itself.

Under `COOP-1`, a processor MAY surface a material conflict, ambiguity, or bounded question to the decision owner, but it MUST NOT autonomously start a work-affecting agent-to-agent consultation or negotiation loop. `COOP-2` and `COOP-3` may do so only through an enabled managed-collaboration policy that declares authorization, participants, purpose, scope, decision owner, and all budget limits. The availability of a messaging transport, A2A task, model, or tool does not enable collaboration by itself.

Cooperation Contract, operational mode, and ledger reach remain separate declarations because the latter two describe current availability rather than another conformance ladder. Operational mode is `ledger_bound`, `snapshot_only`, `degraded`, or `unavailable`. Ledger reach is `shared`, `worktree_local`, or `cross_host`. Ledger unavailability changes what work may safely proceed and MUST be disclosed; it does not silently convert one contract into another.

`unknown_overlap_policy` is `allow`, `warn`, `negotiate`, or `block`. `lease_enforcement` is `none`, `advisory`, or `enforced`. A COOP-1 guarded decision binds conforming participants but does not fence an external mutation path. Protected external effect requires the authenticated epochs and fencing guarantees of COOP-3 or an explicitly identified enforcing adapter.

The module defines three cumulative capability bundles used by the Cooperation Contracts:

| Bundle | Purpose | Minimum capabilities |
|---|---|---|
| `coordination-awareness` | Low-cost useful adoption | presence monitoring, intents, revision-pinned scopes, overlaps, acknowledgements, conflict-preserving projection |
| `integration-assurance` | Safe candidate integration | contracts, typed preconditions, verification binding, change sets, staleness, integration results |
| `live-enforcement` | Protected concurrent mutation | authenticated principals, OCC, leases, epochs, fencing, governance |

An implementation MAY adopt `coordination-awareness` before implementing the complete integration-assurance workflow. Capability declarations state what a component processes; the selected Cooperation Contract states the end-to-end guarantees participants may rely upon.

### 3.1 Default ledger-backed awareness

An AWP-aware writer that discovers a writable shared event ledger and supports the `coordination-awareness` bundle MUST enable ledger-backed advisory coordination by default unless project or receiver policy explicitly disables it. Before materially changing shared state, the writer MUST refresh the available ledger frontier, publish its intent and revision-pinned declared scopes, evaluate known overlaps under the effective policy, and make resulting warnings or guarded outcomes visible. Before integration or handoff, it MUST refresh again and publish the terminal intent, change-set, checkpoint, or synchronization delta required to explain its result.

This default is a protocol behavior, not a required runtime service. A local append-only file, immutable event package, transactional database, source-control binding, or remote event transport MAY supply the ledger when it preserves Core event identity, ancestry, atomic publication, and conflict-preserving replay. SQLite and the local adapter are optional implementation aids. Presence monitoring MAY reduce discovery latency but is not a prerequisite. Authenticated protected leases, epochs, and fencing are COOP-3 capabilities and remain separately configured from COOP-1 participant liveness leases.

If no safe writable ledger is discoverable, the writer SHOULD attempt to establish a project-scoped ledger through an authorized writable binding, provided it can publish the binding location, workstate identity, retention, and access expectations to the intended participants. If it cannot establish or discover such a binding, it MUST disclose operational mode `snapshot_only` or `unavailable` with diagnostic `AWP-COORD-LEDGER-UNAVAILABLE` before material mutation. A private temporary file, process memory, unshared worktree, or unconfirmed model output is not a shared ledger. A worktree-local ledger MAY be used when its limited reach is disclosed. The writer MUST NOT silently describe metadata preservation, a stale snapshot, or an unvalidated event sink as active coordination. Receiver policy determines whether work may continue. A tool MUST NOT advertise COOP-1 merely because it implements this default; its contract claim remains limited to the complete composed behavior it can demonstrate.

The default is an agent/model workflow contract. A model may produce valid intents, events, deltas, diagnostics, or a requested ledger operation as output, while a host binding performs persistence and authorization. A model is not required to open a database, run a service, or possess mutation authority. A host that exposes only a capsule or read-only event view MUST make that limitation visible; it MUST NOT imply that a model-generated event was durably published until the binding confirms persistence. Prompt instructions, tool schemas, MCP resources, A2A data parts, repository files, and other bindings MAY carry the same records when they preserve the declared ledger semantics.

For the default workflow, an AWP-aware agent or model SHOULD follow this sequence:

1. discover the governing specification, workstate, coordination module, and available ledger binding;
2. read and validate the known frontier before material work;
3. publish an intent with a complete base and revision-pinned declared scopes;
4. inspect known overlap, policy, dependency, precondition, and authority state and surface warnings or guarded outcomes;
5. refresh the frontier immediately before integration, capsule projection, or handoff;
6. publish the resulting change-set, verification, checkpoint, synchronization delta, and terminal intent events through the binding.

The sequence is advisory with respect to external mutation under COOP-1: an unresolved `warn` outcome is visible but does not itself grant or deny authority. A receiver MAY require `block`, user arbitration, or an external policy gate. A model's claim that it followed the sequence is reported evidence until the binding makes the event bytes and resulting frontier inspectable.

### 3.2 Ledger-binding descriptor

An active Coordination binding MUST expose a transport-neutral descriptor containing at least the profile identifier, workstate identity, ledger location or retrieval reference, operational mode, ledger reach, durability and retention policy, event publication semantics, frontier-read semantics, and publication confirmation method. The descriptor MAY be carried in a manifest, Capsule module state, repository discovery file, tool resource, MCP resource, A2A data part, or another binding-owned record. A location alone is not confirmation that a ledger is shared or writable. A binding that cannot provide a descriptor MUST report its mode and reach as `unverifiable` and MUST NOT claim cross-participant coordination.

```json
{
  "profile": "local-ledger-awareness-v1",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "location": "repo-relative:.awp/events",
  "operational_mode": "ledger_bound",
  "reach": "shared",
  "durability": "retained-until-project-policy",
  "publication": "atomic-event-create",
  "frontier": "antichain",
  "confirmation": "event-id-and-frontier-returned-by-binding"
}
```

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

Unknown fields MUST be preserved by lossless processors. A processor MUST distinguish a registered record type above its advertised capability or Cooperation Contract from a genuinely unregistered type. It preserves registered stronger-contract records without interpreting them and may still perform weaker-contract actions that do not depend on their meaning. A genuinely unregistered type owned by this required module makes only the affected action or projection `unverifiable` unless a declared compatibility rule permits preservation without interpretation. A weaker-contract reader MAY always perform safe display or export.

### 4.1 References and revision resolution

A record reference has one of these forms:

- `record-id@N` pins integer record revision `N`;
- `record-id` is an unpinned discovery reference and resolves only when the projection has one uncontested effective revision.

Safety-relevant references in contracts, preconditions, readiness decisions, verification, overlaps, and integration plans MUST be revision-pinned. A missing, superseded, or contested pinned revision remains historically addressable but MUST NOT be silently replaced by another revision. An unpinned reference that is absent, contested, or ambiguous is unresolved.

State-space revisions use adapter-qualified immutable identifiers. A Git object ID is one example; a BIM model revision, CAD vault revision, drawing-issue identifier, survey snapshot, or controlled physical-inspection record are other possible bases. Record revisions and state-space revisions are different namespaces.

### 4.2 Time and authority

The passage of time never changes projected state. An identified actor or service MUST emit a valid timeout, expiration, or deadline-observation event under a declared clock authority. Until that event is present, a deadline may be overdue but the prior projected lifecycle state remains unchanged; processors SHOULD surface the overdue condition.

Without COOP-3 protected enforcement, authority may be `asserted`, `verified`, or `unverifiable`. Verification identifies the evaluator, receiver policy, evidence, time, scope, and relevant revocation state. COOP-3 is required for live cross-principal enforcement, not for every authority check. No AWP authority record implies an external side effect by itself.

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

The COOP-2 semantic-awareness capability maintains stable project-scoped definitions for semantic coordination targets.

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
    {"kind": "symbol", "repository": "repo:app", "base_revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a", "path": "src/session/store.ts", "symbol": "SessionStore"}
  ]
}
```

Kinds include `interface`, `behavior`, `invariant`, `state_field`, `schema`, `error_semantics`, `lifecycle`, `compatibility_promise`, `performance_property`, `security_property`, `test_surface`, `deployment_surface`, and `other`.

Within one workstate, an active alias MUST resolve to at most one semantic definition. Merging ambiguous aliases creates diagnostic `AWP-COORD-REGISTRY-AMBIGUOUS` and affected overlap analysis becomes `unknown` until resolved.

Changing the meaning of a definition requires a new revision. Reusing an identifier for unrelated meaning is invalid.

Selector comparison across pinned state-space revisions is a COOP-2 semantic-awareness operation. An analyzer MUST resolve both selectors against their pinned bases and attempt to relate moved, renamed, subdivided, aggregated, or replaced targets using a declared selector profile. Resolution results are `same`, `related`, `different`, `unresolvable`, or `ambiguous`, with evidence and confidence. `unresolvable` or `ambiguous` forces overlap classification `unknown`; it MUST NOT yield `none`.

Language-specific selector syntax and drift algorithms belong to registered adapter profiles. The initial reference implementation SHOULD provide Python AST and TypeScript compiler-symbol profiles, but their identifiers and outputs remain usable by agents implemented in any language.

## 6. Scopes and access claims

**Minimum contract:** `COOP-1` for physical or otherwise explicitly comparable selectors and access modes. `COOP-2` is required for semantic targets and relied-upon reads whose relationship is established semantically.

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

Physical selector kinds include `repository`, `directory`, `file`, `symbol`, `syntax_node`, `configuration_key`, `schema_object`, `generated_output`, `test`, `fixture`, `spatial_region`, `model_element`, `assembly`, `document_region`, `domain_object`, and `interface`. A selector profile defines how a domain resolves fields such as `state_space`, `object_id`, geometry, containment, adjacency, or document coordinates. Coordinates or line ranges are hints and MUST NOT be the only selector for a safety-relevant claim.

Access is `observe`, `read`, `relied_upon_read`, `write`, `create`, `delete`, `propose_change`, `integrate`, or `verify`.

A `relied_upon_read` asserts that the actor's result depends on the selected state remaining compatible. It participates in overlap analysis against relevant writes, deletes, contract revisions, and semantic changes.

Authors SHOULD declare relied-upon reads only for assumptions whose incompatible change could invalidate the output, not every file or symbol inspected. Tools may propose candidates from dependency traces, but the published set SHOULD be summarized at stable interface, invariant, schema, or behavior boundaries. Fine-grained automatic reads MAY remain evidence behind that summary. This keeps the reverse index useful rather than turning ordinary repository browsing into conflicts.

### 6.1 Domain-neutral work-product example

In a building-design project, agents may coordinate against the same model or document state while owning different portions of the work product:

```json
[
  {
    "id": "scope:room-204",
    "type": "scope",
    "module": "urn:awp:coordination",
    "revision": 1,
    "status": "active",
    "created_by": "actor:architect-a",
    "created_at": "2026-09-04T16:00:00Z",
    "selector": {
      "kind": "spatial_region",
      "state_space": "bim:building-model",
      "base_revision": "bim:issue-18",
      "object_id": "room:204",
      "profile": "ifc-spatial-v1"
    },
    "access": "write",
    "semantic_targets": ["semantic:room-boundary@1"]
  },
  {
    "id": "scope:room-205",
    "type": "scope",
    "module": "urn:awp:coordination",
    "revision": 1,
    "status": "active",
    "created_by": "actor:architect-b",
    "created_at": "2026-09-04T16:00:00Z",
    "selector": {
      "kind": "spatial_region",
      "state_space": "bim:building-model",
      "base_revision": "bim:issue-18",
      "object_id": "room:205",
      "profile": "ifc-spatial-v1"
    },
    "access": "write",
    "semantic_targets": ["semantic:shared-wall-fire-rating@2"]
  },
  {
    "id": "scope:main-roof",
    "type": "scope",
    "module": "urn:awp:coordination",
    "revision": 1,
    "status": "active",
    "created_by": "actor:engineer-c",
    "created_at": "2026-09-04T16:00:00Z",
    "selector": {
      "kind": "assembly",
      "state_space": "bim:building-model",
      "base_revision": "bim:issue-18",
      "object_id": "assembly:main-roof",
      "profile": "ifc-element-v1"
    },
    "access": "write",
    "semantic_targets": ["semantic:roof-load-path@1", "semantic:roof-penetration-zone@1"]
  }
]
```

The first two scopes may overlap at their shared wall even though they are different rooms. The roof scope may overlap the rooms through load paths, ceiling interfaces, drainage, fire separation, or service penetrations. Coordination records the relationship and the required agreement; it does not assume that a file merge, model export, or separate agent ownership resolves it.

## 7. Work intent

**Minimum contract:** `COOP-1`. A participant's self-declared actual-versus-declared physical-scope reconciliation is a checkpoint obligation at this level; analyzer-produced observed scope and readiness gating are `COOP-2`.

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

If observed work expands beyond the declared scope, the writer MUST either update the intent before publishing a ready change set or record an explicit deviation. Under a COOP-2 policy, unresolved material under-declaration prevents `ready`.

## 8. Observed scope

**Minimum contract:** `COOP-2`.

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
  "repository": "repo:app",
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

**Minimum contract:** `COOP-1` for physical-scope `none`, `informational`, `compatible`, `ordered`, and `blocking` outcomes. `COOP-2` is required when semantic ambiguity produces `unknown` or policy requires semantic negotiation.

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

`superseded` is the only terminal overlap state. `resolved` is quiescent but may reopen when its basis changes. The overlap record's `policy_action` is the evaluated result of the module configuration plus any identified scope, state-space, or organization policy. More specific applicable policy takes precedence; equal-specificity disagreement produces `unknown` and a policy-conflict diagnostic rather than silent selection.

A conflict is an overlap whose policy action requires resolution. A conflict records competing claims, responsible owner, allowed resolution strategies, evidence, accepted risk, and final disposition. Resolution strategies include scope partition, contract first, ordered integration, compatibility adapter, feature isolation, rebase and re-derive, combined implementation, authorized risk acceptance, and withdrawal.

## 10. Negotiation and commitments

**Minimum contract:** `COOP-2`.

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

### 10.1 User-mediated arbitration

Agent-to-agent negotiation is preferred for routine, low-risk coordination. It MUST escalate to user-mediated arbitration when the agents cannot reach a permitted outcome within the declared negotiation bounds, when applicable policies disagree, when a decision requires authority held by the user or another named principal, or when the competing changes have material safety, compatibility, data-loss, security, or delivery consequences.

An arbitration request is a durable coordination record. It MUST identify:

- every affected subject and pinned revision;
- all participating agents and the decision authority;
- one precise question that the authority can answer;
- at least two materially distinct alternatives, including consequences, reversibility, and known risks;
- the response deadline and clock authority;
- the physical and semantic scopes blocked pending a decision;
- explicitly permitted interim work, if any; and
- the evidence, assumptions, and policy that led to escalation.

The request MUST NOT embed private chain-of-thought or require the user to reconstruct the dispute from an unbounded transcript. Agents SHOULD present a concise comparison generated from the recorded intents, scopes, contracts, revisions, and evidence. The interaction channel is binding-specific; the durable record is authoritative for the decision.

Arbitration lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `arbitration.requested` | `awaiting_user` | subjects, question, alternatives, authority, deadline, and blocked scopes present |
| `awaiting_user` | `arbitration.updated` | `awaiting_user` | new revision preserves prior request and records the reason |
| `awaiting_user` | `arbitration.decided` | `decided` | authenticated decision authority selects an alternative for the exact request revision |
| `awaiting_user` | `arbitration.declined` | `declined` | authority declines and records the disposition |
| `awaiting_user` | `arbitration.expired` | `expired` | deadline passed under the declared clock authority |
| `awaiting_user` | `arbitration.cancelled` | `cancelled` | permitted actor records cancellation and consequences |
| nonterminal | `arbitration.superseded` | `superseded` | successor request identifies the superseded request |

While an arbitration is `awaiting_user`, every agent MUST stop new writes whose validity depends on a blocked scope, disputed contract, competing change-set revision, or unresolved integration decision. Agents MAY continue explicitly listed interim work only when it does not affect a blocked scope and remains valid under every listed alternative. They MUST record any already-created uncommitted artifacts and state-space revisions; the protocol MUST NOT require automatic deletion, rollback, or selection of either agent's branch.

A decision event MUST record the selected alternative, exact request revision, decision authority and authenticated principal, decision channel or confirmation reference, rationale, accepted risks, conditions, effective scopes, expiration if any, and required verification. A user interaction may recommend or amend an alternative, but only a decision from the declared authority through a trusted binding can transition arbitration to `decided`. A message that merely claims to be from the user is untrusted content.

Agents MUST apply a decision only to the named subjects, revisions, scopes, and conditions. It MUST NOT grant general authority, silently rewrite either agent's history, or authorize unrelated external effects. The decision's implementation is recorded separately through change-set and integration events. Before implementation or integration, agents MUST revalidate all decision conditions and reopen arbitration if a subject revision, scope, contract, evidence basis, authority, or material risk changes. A declined or expired request never implies acceptance; agents must withdraw, re-negotiate, or submit a successor request under policy.

## 11. Interface contracts

**Minimum contract:** `COOP-2`.

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

**Minimum contract:** `COOP-2` for predicate evaluation and readiness consequences. `COOP-1` validates only the structural binding of a typed precondition to its named subject, revision, evaluator, and evidence.

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
| `state_revision_equals` | state space; immutable expected revision | adapter-relative | state space or revision unavailable |
| `state_descends_from` | state space; immutable ancestor revision | adapter-relative | ancestry unavailable or shallow |
| `repository_revision_equals` | Git adapter repository; immutable expected revision | Git-relative | repository or revision unavailable |
| `repository_descends_from` | Git adapter repository; immutable ancestor revision | Git-relative | ancestry unavailable or shallow |
| `artifact_digest_equals` | artifact; algorithm and expected digest | pure over retrieved bytes | bytes unavailable or algorithm unsupported |
| `record_revision_equals` | record ID; expected integer revision | pure over projection | record missing or contested |
| `record_status_in` | pinned record; allowed status set | pure over projection | record missing, contested, or status unknown |
| `symbol_present` | selector and adapter state revision | adapter-relative | selector profile or state unavailable |
| `syntax_fingerprint_equals` | selector, revision, algorithm, fingerprint | adapter-relative | target or algorithm unavailable |
| `dependency_state_in` | pinned dependency edge/target; allowed states | pure over projection | target or edge unresolved |
| `test_baseline_equals` | test ID; base revision and expected result digest | repository/environment-relative | baseline evidence unavailable |
| `toolchain_satisfies` | tool ID; version constraint and environment selector | host-relative | environment or version cannot be observed |
| `schema_version_satisfies` | schema ID/revision; registered version constraint | pure over identified schema | schema or constraint profile unavailable |
| `verification_passed_for` | pinned subject; verification policy | projection/environment-relative | valid bound verification unavailable |

`pure` evaluators read only the identified AWP projection or supplied bytes. Adapter-relative and host-relative results MUST record the state space or environment they observed. All evaluators MUST be side-effect-free with respect to the project, deterministic for identical declared inputs, bounded by an explicit timeout, and return `error` rather than partial success after timeout or internal failure. Constraint syntax is owned by the registered evaluator-interface version; an implementation MUST NOT guess unsupported syntax.

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

**Minimum contract:** `COOP-2`.

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
7. declared and observed scopes have been compared when COOP-2 semantic awareness is required;
8. required authority is currently valid under receiver policy.

`ready` does not mean integrated, correct, authorized for deployment, or free of unknown risk.

Terminal change-set states are `integrated`, `failed`, `withdrawn`, and `superseded`. `stale` is nonterminal but cannot transition directly to `ready`; it first transitions through `revalidated` or `rebased`. Superseding a stale change set creates a successor record and leaves the original terminal.

## 14. Verification

**Minimum contract:** `COOP-2` for verification evaluation and readiness consequences. `COOP-1` validates only the structural binding of a verification record to its named subject, base, evaluator, and evidence.

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

Verification becomes stale when its subject revision, tested state-space revision, relevant contract, required tool/environment constraint, or relied-upon baseline changes. A verifier's approval does not grant integration authority unless separately authorized.

## 15. Dependency graph and staleness

**Minimum contract:** `COOP-2` for dependency-staleness propagation and readiness consequences. `COOP-1` retains record-validity staleness checks defined by the Cooperation Contract.

Dependency edge kinds are `requires`, `implements`, `verifies`, `derived_from`, `relies_on`, `orders_before`, `conflicts_with`, `supersedes`, and `integrates`.

For each event that changes a record revision or status, a deterministic Coordination projector MUST:

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

**Minimum contract:** `COOP-2`.

An integration plan identifies owner, target state space and base revision, exact change-set revisions, dependency-derived order, shared contracts, required precondition evaluations, verification plan, rollback, authority requirements, and `atomicity`. A repository and commit are one possible adapter representation of the target state space.

`atomicity` is:

- `atomic`: no input is considered integrated unless the complete plan commits and passes required combined verification;
- `stepwise`: each ordered input may commit independently and remains integrated if a later step fails unless rollback policy reverses it;
- `best_effort`: independent inputs may integrate in any dependency-valid subset, with an explicit disposition for every input.

An adapter MUST reject `atomic` when its state-space transaction mechanism cannot supply the claimed atomic boundary. Rollback is a separately recorded operation and MUST NOT be assumed successful.

Before starting integration, the owner MUST refresh available coordination events, compare the target base, re-evaluate expiring or base-bound preconditions, confirm contract revisions, and re-open any invalidated overlap dispositions.

Integration lifecycle:

| From | Event | To | Required condition |
|---|---|---|---|
| — | `integration.proposed` | `proposed` | exact inputs, base, owner, order, verification present |
| `proposed` | `integration.approved` | `approved` | required policy/authority approves exact plan revision |
| `approved` | `integration.started` | `integrating` | current readiness and concurrency checks pass |
| `integrating` | `integration.completed` | `completed` | result revision, transformations, and required verification recorded |
| `integrating` | `integration.failed` | `failed` | failure evidence and state-space disposition recorded |
| `proposed`, `approved` | `integration.cancelled` | `cancelled` | permitted actor and reason recorded |
| nonterminal | `integration.superseded` | `superseded` | successor plan present |

An integration result identifies exact plan revision, inputs, target base, resulting state-space revision, adapter transformations, resolved conflicts, contract revisions, verification results, deviations, output artifact digests, responsible actors, and rollback status.

The result contains one disposition per planned input: `integrated`, `not_attempted`, `failed`, `rolled_back`, `rollback_failed`, or `superseded`, plus any intermediate and final state-space revisions. After partial failure, each change set transitions according to its own disposition; the plan may be `failed` even though stepwise inputs remain `integrated`. An atomic plan that fails leaves no change set integrated unless the enforcing adapter records an atomicity violation.

A successful adapter transaction or source-control merge MUST NOT by itself transition an integration to `completed` when combined semantic verification is required.

Terminal integration states are `completed`, `failed`, `cancelled`, and `superseded`. `proposed`, `approved`, and `integrating` are nonterminal.

## 17. Deterministic projection

**Minimum contract:** `COOP-1` for structural event validation and deterministic projection. Dependency-staleness propagation after valid semantic change is `COOP-2`.

Coordination state is derived from valid Core events at a declared frontier.

A deterministic Coordination projector MUST:

1. validate the Core envelope, module declaration, ancestry, and workstate identity;
2. compute semantic state independently of the serialization chosen for concurrent valid events;
3. apply an event only when its record revision precondition and lifecycle transition are valid;
4. treat concurrent non-commuting updates from the same uncontested record revision as a contested record conflict;
5. allow only module-defined commutative operations, currently acknowledgement-set union and evidence-reference-set union;
6. preserve invalid or unknown events in history while excluding their claimed state change from the valid projection;
7. order diagnostic emission using Kahn's topological algorithm with the lexicographically smallest event ID selected from the ready set;
8. when `COOP-2` dependency semantics are active, propagate dependency staleness after applying each valid semantic change;
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
| `AWP-COORD-ARBITRATION-PENDING` | policy | A user-mediated decision is pending for a guarded scope or transition |
| `AWP-COORD-USER-DECISION-UNVERIFIABLE` | policy | The claimed user decision cannot be bound to the declared authority and exact request revision |
| `AWP-COORD-ARBITRATION-SCOPE-MISMATCH` | error | An implementation or integration exceeds the scopes or conditions authorized by the decision |
| `AWP-COORD-LEDGER-UNAVAILABLE` | warning | No safe writable or readable ledger binding is available; snapshot-only or unavailable operational mode is explicit |
| `AWP-COORD-LEDGER-WORKTREE-LOCAL` | warning | Coordination is active only for agents sharing one worktree-local ledger; other worktrees require an explicit shared path |

Errors invalidate the affected transition. Warnings preserve state but MUST be visible before a safety-relevant continuation. Implementations MAY add namespaced diagnostics.

## 18.1 Agent presence and monitoring

Presence monitoring makes active participation observable before agents mutate a shared project. It is an advisory coordination capability incorporated by COOP-1 and COOP-2. Presence does not grant authority, reserve a scope, establish exclusivity, or imply that the announced actor is trusted. An authenticated fenced lease remains a COOP-3 operation distinct from a COOP-1 participant liveness lease.

A presence record identifies one runtime session:

```json
{
  "id": "presence:agent-17-session-4",
  "type": "presence",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "active",
  "created_by": "actor:agent-17",
  "created_at": "2026-09-04T18:00:00Z",
  "agent_id": "agent:17",
  "session_id": "session:4",
  "principal": "principal:team-a",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "project": "project:application",
  "execution_location": {
    "kind": "worktree",
    "location": "worktree:agent-17-session-4",
    "branch": "feature/auth-refresh"
  },
  "base": {
    "repository": "repo:application",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
    "profile": "git-state-v1"
  },
  "declared_scopes": ["scope:auth-refresh@2"],
  "access_mode": "write",
  "monitoring_profile": "local-sqlite-presence-v1",
  "heartbeat_at": "2026-09-04T18:00:30Z",
  "expires_at": "2026-09-04T18:02:00Z"
}
```

Required fields are `agent_id`, `session_id`, `principal`, `workstate_id`, `project`, `execution_location`, `base`, `declared_scopes`, `access_mode`, `monitoring_profile`, `heartbeat_at`, and `expires_at`. Project identity MUST be stable across worktrees or execution locations. `session_id` identifies one runtime generation and MUST NOT be reused after release or expiry. `base` binds the announcement to the revision from which work began. `declared_scopes` contains pinned Coordination scope references; a broad provisional scope MAY be announced and narrowed by a later revision.

Presence states are `active`, `released`, `expired`, and `superseded`. Entry MUST publish an active presence record before the actor performs a declared write. A heartbeat atomically advances `heartbeat_at` and `expires_at` for the same active session. It MUST NOT revive an expired, released, or superseded session; a returning runtime creates a new session identity.

The monitoring profile defines heartbeat interval, session duration, registry clock authority, retry policy, watcher cursor retention, and notification delivery. A monitor classifies a session as expired only through the profile's registry clock and an atomic compare against the latest heartbeat. Client wall clocks alone MUST NOT authoritatively expire a shared session. In an advisory deployment, an observer that cannot reach the registry reports presence as `unverifiable`, not absent.

A watcher maintains a durable cursor over lifecycle notifications. It announces at least new sessions, terminal sessions, and newly detected overlaps or conflicts. Delivery MUST be idempotent by notification identity. Restarting a watcher MUST resume from its stored cursor or explicitly disclose an observation gap. Heartbeats SHOULD update materialized live state without producing a durable event for every renewal; implementations MAY sample heartbeat evidence under a declared retention policy.

On entry, an implementation using presence monitoring MUST:

1. resolve stable project and workstate identity;
2. read and verify the current workstate and repository revision;
3. create a unique session and publish its initial scope before writing;
4. inspect active sessions and evaluate physical, semantic, and relied-upon-read overlap under current policy;
5. surface required warnings, negotiation, ordering, or blocking before mutation;
6. begin heartbeat renewal or declare that liveness cannot be maintained.

On normal exit, an implementation MUST stop new mutation, publish its final change set and semantic checkpoint or synchronization delta, refresh the canonical Capsule through the current projection owner, and then release its presence session. If the Capsule cannot be refreshed, the writer MUST publish an incomplete-handoff diagnostic rather than presenting the prior Capsule as current. Crash recovery relies on expiry and MUST preserve an `expired` terminal observation.

Heartbeats and other high-frequency live values MUST NOT be written into the project Capsule. The Capsule remains a durable semantic projection updated at checkpoints and handoff. Entry, release, expiry, conflict, and incomplete-handoff facts MAY be retained as durable Coordination events when they affect interpretation or audit.

Multiple agents MUST NOT independently overwrite one canonical Capsule from the same base frontier. Each agent publishes events or deltas; a single current projection owner updates the Capsule using compare-and-swap against its frontier and generated digest. A stale writer merges, retries, or reports divergence through Synchronization. It MUST NOT use last-write-wins.

### 18.1.1 Local SQLite presence profile

The informative profile `local-sqlite-presence-v1` supports agents sharing one local Git common directory. It uses SQLite transactions for atomic entry, expiry, release, and watcher-cursor advancement. Its registry clock is the host running the transaction. The profile uses a 90-second session duration, recommends renewal at most every 30 seconds, and treats exact pinned-scope equality plus an explicit wildcard as its only automatic overlap evidence.

This profile is advisory. It does not authenticate principals, fence writes, provide cross-host availability, infer semantic overlap, or satisfy COOP-2 or COOP-3. A deployment that changes its timing, clock, matching, or retention behavior declares a distinct profile or explicit profile parameters.

## 18.2 Scaling requirements

An implementation intended for many concurrent agents MUST avoid project-wide polling and all-pairs overlap comparison. It SHOULD:

- partition presence and event streams by stable project and state-space identity;
- index active sessions by project, pinned scope, access mode, and expiration;
- route scope changes only to watchers subscribed to potentially interacting scopes;
- coalesce heartbeats in materialized state rather than append every renewal to durable history;
- provide cursor-based incremental delivery, bounded pages, backpressure, and idempotent retry;
- define retention for terminal sessions, watcher cursors, diagnostics, and sampled liveness evidence;
- isolate hot scopes so one heavily contended component does not serialize unrelated work;
- measure active sessions, renewal latency, expiry lag, notification lag, conflict candidates, false alarms, dropped observations, and projection retries;
- preserve a recovery path when an index, subscriber, projector, or coordinator restarts.

Sharding MUST NOT change the semantic result of overlap evaluation. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants require an identified routing or aggregation strategy. An implementation MUST disclose any scope class it cannot compare completely.

### 18.2.1 Brokered and sharded presence profile

The candidate profile `brokered-sharded-presence-v1` defines advisory presence for deployments in which agents may run on different hosts and a single local registry is insufficient. This profile remains an advisory presence capability: it does not become a COOP-3 protected lease merely because its transport is distributed.

The profile has four logical responsibilities, which MAY be implemented by one service or separate replicated services:

1. a session registry stores current presence and heartbeat state;
2. a scope router identifies partitions and subscribers that may interact with a declaration;
3. an event broker delivers lifecycle, conflict, gap, and handoff notifications;
4. a Capsule projector consumes durable semantic events or deltas and serializes the canonical Capsule projection for each workstate.

#### Partitioning and routing

The primary partition key MUST include stable project identity and state-space identity. Session ownership, renewal, release, and expiry for one session MUST be linearizable within its owning partition. Exact pinned scopes SHOULD use an inverted index keyed by scope identity and access mode rather than scanning all active sessions.

A scope router MUST identify every partition that can contain a potentially interacting scope under the declared comparison policy. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants MUST be routed to an aggregator or a declared global-scope partition. If any required partition or index is unavailable, the result is `unverifiable`; the implementation MUST NOT report that no conflict exists.

Partition rebalancing MUST preserve session generation, terminal state, watcher position, and overlap results. A former partition owner MUST NOT accept a renewal or release after ownership has transferred. Implementations SHOULD use epochs, compare-and-swap, or equivalent stale-owner rejection even though presence itself remains advisory.

#### Heartbeats and expiry

Heartbeats MUST route directly by session identity and update coalesced materialized state. They MUST NOT produce one durable broker event per renewal. A heartbeat update MUST compare the session generation and current active state atomically, so a delayed message cannot revive a terminal or replaced session.

Expiry MUST be scheduled from the authoritative registry time of the owning partition. An expiry worker MUST atomically compare the expected session generation and latest expiration before publishing `presence.expired`. Duplicate expiry attempts and duplicate lifecycle delivery MUST converge through stable event identity and idempotent processing.

#### Subscriptions, retention, and backpressure

Watchers SHOULD subscribe by project plus pinned scopes, scope classes, or declared global interest. The broker MUST support durable cursors, bounded delivery pages, idempotent retry, and an explicit retention interval. Cursor state MAY be compacted, but a watcher whose cursor falls behind retained history MUST receive `presence.observation_gap` before current state is presented as complete.

When a hot or wildcard scope matches many sessions, the registry SHOULD publish a bounded conflict-set summary plus a resumable cursor instead of one unbounded notification per pair. Backpressure MUST NOT silently discard a safety-relevant lifecycle, conflict, gap, or incomplete-handoff observation. A deployment MUST declare queue limits, overflow behavior, retry limits, and the point at which presence becomes `unverifiable`.

Terminal sessions, lifecycle events, watcher cursors, conflict summaries, and sampled liveness evidence MUST have explicit retention policies. Retention expiry MUST NOT erase durable semantic events already incorporated into a checkpoint or Capsule projection.

#### Identity, authorization, and confidentiality

The registry MUST authenticate the submitting runtime and bind it to the asserted agent and principal under deployment policy. Authorization MUST constrain which projects, scopes, subscriptions, and presence details that identity may publish or observe. Authentication of presence proves only who made the announcement; it grants no project authority and no permission to mutate a scope.

Deployments spanning trust boundaries MUST define transport protection, replay protection, tenant isolation, audit retention, and redaction of worktree, branch, scope, and principal metadata. A monitor MUST distinguish unauthorized, unreachable, stale, and absent state.

#### Capsule projection

Agents MUST publish final semantic events or synchronization deltas before release; they MUST NOT race to overwrite the canonical Capsule. For each workstate, the projection service MUST expose one logical writer and compare the expected frontier and generated digest before replacement. Replicated projectors MUST use fenced ownership or an equivalent mechanism that prevents a stale projector from publishing after ownership transfer.

A projection conflict MUST reload and reconcile the new frontier, retry under policy, or publish divergence. It MUST NOT resolve by last-write-wins. Projector failure does not keep heartbeat values in the Capsule: it produces an incomplete-handoff observation while the live registry and durable event stream remain separate.

#### Capacity and failure disclosure

A conforming deployment MUST publish the profile parameters and tested envelope on which its capacity claim depends, including session duration, heartbeat interval, active-session count, scope distribution, wildcard rate, partitions, replication, event retention, and watcher fan-out. It SHOULD report p50, p95, and p99 entry, renewal, expiry, notification, conflict-query, and projection latency together with error, retry, gap, and false-alarm rates.

Load tests MUST include synchronized renewal bursts, hot scopes, wildcard scopes, broker restart, partition-owner failover, delayed and duplicated messages, watcher lag beyond retention, network partition, clock skew, and concurrent Capsule projection. A deployment MUST identify which guarantees remain available during each failure. Results from the local SQLite profile or a sequential synthetic probe MUST NOT be presented as evidence of distributed capacity.

## 19. Live coordination and leases

**Minimum contract:** `COOP-3`.

COOP-3 protected mutation enforcement requires a live coordinator or an external protected system, not merely a shared file.

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

A COOP-3 enforcement profile MUST specify retry limits, heartbeat interval, lease duration, expiry clock authority, deadlock detection, starvation policy, cancellation consequences, and human/organizational arbitration. The base module defines no universal timing defaults because safe values depend on task duration, network delay, and the protected system. Named interoperability and test profiles MAY define explicit defaults.

## 20. Security, principals, and governance

Actor identity, principal identity, trust, and authority are separate.

A principal is the human or organization accountable for an actor's participation. A COOP-3 session MUST bind authenticated actors to principals and declare the governing policy. Cross-principal coordination MUST identify:

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

- `presence.entered`, `.scope_updated`, `.released`, `.expired`, `.superseded`;
- `presence.conflict_detected`, `.observation_gap`, `.handoff_incomplete`;
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
- `arbitration.requested`, `.updated`, `.decided`, `.declined`, `.expired`, `.cancelled`, `.superseded`;
- `lease.requested`, `.granted`, `.denied`, `.renewed`, `.released`, `.expired`, `.revoked`, `.superseded`.
- `evidence.linked`, `evidence.unlinked`, and `record.reconciled`.

Minimum deterministic-projection payload requirements supplement the common event rules in Section 4.3:

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
| integration completion/failure | pinned plan, per-input dispositions, state-space revisions, verification and rollback outcomes |
| arbitration request | pinned subjects, question, alternatives, decision authority, deadline, blocked scopes, interim-work policy, evidence, and escalation basis |
| arbitration decision | exact request revision, selected alternative, authenticated authority, confirmation reference, rationale, accepted risks, conditions, effective scopes, expiration, and verification requirements |

An unlink event removes an association from effective projection but preserves its historical addition. It identifies the exact association ID and authority evaluation; it does not edit the subject record.

Private event kinds use a controlled namespaced module ID. They MUST NOT add unregistered bare kinds to this module.

## 22. Interoperability mappings

This section is non-normative. A registered adapter profile may make a particular mapping normative for that profile.

### Git and source-control systems

Git revisions map to immutable `base.revision` and `result_revision` values. Branches and worktrees map to isolated execution locations. Commits and patches map to artifacts and change-set inputs. Pull requests map to review/integration adapters. Git merge success is mechanical evidence only.

### A2A

An A2A Task may carry an AWP intent reference. A2A Artifacts may carry AWP deltas, bundles, change sets, evidence, or integration results. A2A Task state does not replace AWP record state; adapters record the mapping and preserve both identities.

For the named `coop3-a2a-v1` profile, A2A is the distributed communications and execution control plane for typed AWP coordination operations. An A2A request MUST carry the operation identifier, workstate identifier, stable binding identity, acting AWP actor, and the expected revision, frontier, or fencing token applicable to the operation. A response MUST carry either a durable AWP receipt that identifies the accepted event or protected decision, or a stable rejection or conflict diagnostic. A2A delivery, task completion, or peer authentication does not replace the binding's durable persistence, principal mapping, authorization decision, epoch comparison, or fencing check.

An A2A adapter MUST preserve idempotency across retry, reconnect, duplicate delivery, endpoint migration, and task-status polling. It MUST make transport reachability and AWP store or gateway reachability separately observable. If protected enforcement cannot verify the actor/principal, binding epoch, expected state, protected scope, or fencing token, it MUST reject the protected operation even if the A2A task was successfully delivered. A2A is optional outside a binding that explicitly claims `coop3-a2a-v1`.

### MCP

MCP tools may read, validate, project, query, or append AWP data. Tool availability and invocation do not establish project authority.

### MPAC

[MPAC, arXiv:2604.09744 version 1](https://arxiv.org/abs/2604.09744v1) session, intent, operation, conflict, and governance objects may map to corresponding AWP records. AWP retains domain-specific semantic scopes, contracts, preconditions, verification binding, persistent project history, and resume/handoff state. A mapping MUST identify information loss and MUST NOT equate MPAC transport/session acceptance with AWP integration readiness.

## 23. Reference procedure

This is a non-normative happy path, not a lifecycle state machine. Reopened overlaps return to analysis or negotiation; stale change sets return to implementation/revalidation; failed integrations follow their recorded retry, rollback, or supersession disposition.

```text
refresh workstate and repository identity
              |
publish presence session and begin heartbeat renewal
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
publish checkpoint/delta, refresh Capsule through projection owner
              |
complete intents and release presence and live coordination state
```

## 24. Minimum conformance fixtures

The experimental module is not ready for stable status without fixtures covering at least:

The fixture inventory does not itself establish a Cooperation Contract claim. The following minimum attribution makes the evidence boundary auditable: a `COOP-1` claim needs the applicable scenarios in Cooperation Contracts §4.3, including deterministic replay, record-validity rejection, compatible and incompatible physical scopes, resolution, lease expiry, fresh handoff, and binding identity across filesystem paths. This inventory contributes direct coverage for physical non-overlap and same-file conflict (1–2), structural precondition or verification binding (7–8), contested projection (11–12), recovery and expiry (14–15, 23–25), and presence overlap behavior (21–22). A `COOP-2` claim additionally needs semantic conflict, relied-upon read, material undeclared scope, contract revision, dependency cycle, and integration-readiness coverage (3–6, 9–10, 13). A `COOP-3` claim additionally needs fenced mutation, epoch, authorization, and protected-operation coverage (16–18, 26–32 as applicable). A claimed operating envelope MUST identify any required scenario that has no corresponding executable fixture; the present inventory does not by itself discharge COOP-1 §4.3 scenario 9's different-filesystem-path binding-identity evidence.

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
21. simultaneous presence entry with compatible read scopes;
22. simultaneous presence entry with an overlapping writer;
23. heartbeat renewal racing registry-authoritative expiry;
24. crashed session expiry and watcher restart from a durable cursor;
25. two exit projections attempting to update one Capsule frontier.
26. cross-partition exact-scope overlap with identical results before and after partition rebalancing;
27. unavailable scope partition producing `unverifiable` rather than a false no-conflict result;
28. synchronized heartbeat burst with duplicate and delayed renewals;
29. hot or wildcard scope producing bounded, resumable conflict-set delivery;
30. watcher cursor falling behind retention and receiving an observation-gap notification;
31. stale partition owner and stale Capsule projector rejected after ownership transfer;
32. authenticated presence accepted without promoting it to mutation authority.

Each fixture SHOULD include input events, expected frontier, expected materialized records, expected diagnostics, and an explanation of the safety property.

## 25. Implementation maturity criteria

Before the complete integration-assurance schema is frozen, the project SHOULD run an early `coordination-awareness` experiment comparing chat-only coordination with durable intents, pinned scopes, overlaps, acknowledgements, and conflict-preserving projection. It MUST measure false-positive and false-negative overlap classifications, authoring cost, coordination delay, and whether warnings arrive before conflicting implementation. Results may change the scope and record model before further standardization.

Coordination 0.5.0 is normative but experimental in AWP 0.8.0. It should not advance from experimental status until:

1. JSON Schemas exist for all records and events required by COOP-1 deterministic projection;
2. two independent implementations produce identical projections for the fixture suite;
3. invalid transitions and revision conflicts are consistently rejected;
4. staleness propagation is deterministic;
5. a Git/worktree and test-runner reference adapter demonstrates one end-to-end workflow;
6. an expanded benchmark compares chat-only, Git-only, and AWP-assisted coordination across awareness and integration-assurance bundles;
7. the A2A and MPAC mappings are reviewed for semantic overclaiming;
8. security review confirms that records cannot self-authorize external actions;
9. the brokered/sharded profile has independent interoperability, load, failover, loss, and projection-race evidence across its declared operating envelope.

The repository's `tools/awp_projector.py` is an informative deterministic Coordination projector foundation. It is transport-neutral and currently covers structural event validation, workstate and ancestry checks, deterministic topological replay, revision and lifecycle checks for the declared transition tables, cross-record pinned-reference and verification-base checks, and preservation of concurrent contested successors. Its tests do not yet constitute the complete COOP-1 deterministic fixture suite, a complete cross-record validator, a complete COOP-1 binding, or independent interoperability evidence.

## 26. Open issues

1. Canonical JSON and digest rules remain a Core/Artifact/Security family issue and must be resolved before signed coordination evidence is portable. The family profile should evaluate RFC 8785 JCS while explicitly handling its I-JSON, IEEE-754 number, and Unicode-preservation constraints; Coordination MUST NOT select a conflicting local canonicalization.
2. The initial semantic registry needs language-specific selector profiles for symbols, schemas, and dependency graphs.
3. Confidence calibration for inferred semantic overlap is unspecified; policy must not confuse a model score with verification.
4. Composition and conflict rules for multiple organization-specific contract decision policies need implementation experience.
5. COOP-2 needs a semantic integration binding, while COOP-3 additionally needs a formally modeled coordinator protocol and at least one real enforcing adapter.
6. The candidate brokered/sharded presence profile needs independent implementations and measured interoperability, capacity, notification-loss, failover, privacy, and operating-cost evidence before its parameters can be stabilized.
7. Privacy-preserving coordination across principals may require selective disclosure or commitments to hidden evidence.
8. Benchmark tasks must measure false alarms and coordination overhead as well as conflicts caught.

## 27. Summary

Coordination 0.5.0 supplies the durable records and executable mechanisms used by AWP Cooperation Contracts. Portable collaboration needs no Cooperation Contract, COOP-1 adds deterministic small-group conflict reduction without requiring a service, COOP-2 adds semantic awareness and integration assurance, and COOP-3 adds authenticated enforcement, fencing, and a scalable operating envelope. Consultation is a separately enabled optional Cooperation subprotocol.

The essential invariant is:

> No actor, record, message, clean merge, or passing claim may silently promote asserted coordination into observed fact, verified compatibility, or external authority.
