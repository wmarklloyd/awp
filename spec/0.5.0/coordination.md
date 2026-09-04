# AWP Coordination 0.2.0

**Module ID:** `urn:awp:coordination`  
**Status:** Experimental and optional  
**Depends on:** AWP Core `0.5.x`, AWP Synchronization `0.2.x`

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
  "version": "0.2.0",
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


