# AWP Coordination 0.3.0

**Module ID:** `urn:awp:coordination`  
**Status:** Experimental  
**Depends on:** AWP Core `0.6.x`, AWP Synchronization `0.3.x`  
**Supersedes:** AWP Coordination `0.2.0`  
**Schema:** `../../schemas/awp-coordination-0.3.schema.json`

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
  "version": "0.3.0",
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

Coordination 0.3.0 is normative but experimental in AWP 0.6.0. It should not advance from experimental status until:

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

Coordination 0.3.0 turns Coordination from a descriptive vocabulary into a candidate executable protocol. C1 defines durable deterministic coordination that works across agents and hosts. C2 adds semantic awareness and early conflict detection. C3 adds live enforcement only where a protected system can prove it.

The essential invariant is:

> No actor, record, message, clean merge, or passing claim may silently promote asserted coordination into observed fact, verified compatibility, or external authority.
