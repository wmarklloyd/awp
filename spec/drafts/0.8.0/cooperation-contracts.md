# AWP Cooperation Contracts 0.1.0

**Status:** Experimental working-draft profile specification
**Module ID:** `urn:awp:cooperation`
**Profile family:** Cooperation Contracts (`COOP`)
**Direct dependencies:** Capsule and Handoff; Coordination for `COOP-1`, `COOP-2`, and `COOP-3`

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Cooperation Contracts define what several human or software-agent participants can expect while working on the same project. AWP separates two independent concerns:

1. **work coordination** reduces incompatible concurrent work output through discovery, leases, intents, guarded scopes, compatibility decisions, checkpoints, and recovery; and
2. **consultation** exchanges bounded analysis, critique, review, delegation, or synthesis without granting authority or reserving a work scope.

`COOP-1`, `COOP-2`, and `COOP-3` are AWP 0.8's single cumulative **work-coordination** ladder. The Coordination module defines the durable records, capability bundles, and mechanisms used by those contracts; it does not define a competing conformance axis. There is no `COOP-0` contract. Ordinary portable AWP exchange—including capsules, handoffs, and Core `consultation` records—remains useful without selecting any Cooperation Contract and makes no active coordination guarantee.

`COOP-1` is the first named contract because it provides immediately useful conflict reduction for a small group while keeping material inter-agent decisions user-mediated. `COOP-2` adds semantic and integration coordination and permits explicitly authorized, budgeted inter-agent collaboration. `COOP-3` adds protected, scalable coordination. Consultation and managed collaboration are disabled unless the binding explicitly enables them.

This document is an experimental profile specification. It does not change released AWP 0.6.0 semantics or make the current reference tools conformant to a contract they do not fully implement.

The module capability `guarded-scope-coordination` means that the selected contract uses Coordination records or an equivalent binding to compare declared scopes and return guarded mutation decisions. It is required by every named COOP contract and activates this module's dependency on `urn:awp:coordination`.

### 1.1 Migration from the earlier draft ladder

| Earlier draft behavior | AWP 0.8 location |
|---|---|
| Portable preservation, display, and asynchronous consultation | AWP baseline; no Cooperation Contract required |
| Deterministic event validation, projection, and guarded physical work | `COOP-1` |
| Semantic registry, scope analysis, and integration assurance | `COOP-2` |
| Authenticated protected mutation, epochs, leases, fencing, and scalable operating envelope | `COOP-3` |

This mapping is not an automatic conformance upgrade. An implementation MUST satisfy the additional guarded-work, checkpoint, recovery, operating-envelope, and evidence requirements of the claimed contract. A workstate governed by released AWP 0.6 continues to interpret its original Coordination declaration under that released specification.

## 2. Common terms and binding disclosure

A **participant** is a human or agent performing work or supplying a bounded consultation response. A **decision owner** is the participant or declared human principal responsible for accepting a result, continuing a loop, or escalating an unresolved issue. A **guarded scope** is a declared part of a work product whose incompatible modification is controlled by the selected contract.

A **cooperation interaction** is a bounded request for critique, alternative analysis, review, delegation, decision support, or synthesis. It is not an authorization grant, a work reservation, or a request for private chain-of-thought.

**Record-validity staleness** asks whether a record or event is admissible: its identity, ancestry, revision, pinned references, and typed precondition or verification bindings must be structurally valid. It is analyzer-free and belongs to `COOP-1`. **Dependency staleness** asks whether an already valid record's relied-upon predicates still hold after a relevant dependency changes. Its propagation, re-evaluation, and readiness consequences belong to `COOP-2`.

Likewise, `COOP-1` validates that a typed precondition or verification is correctly formed and bound to its named subject, revision, evaluator, and evidence. `COOP-2` evaluates the predicate and determines whether its result permits readiness or integration under the effective policy.

An implementation with an active Cooperation Contract MUST identify the selected contract, top-level claim state, operational mode, material limitations, and a `subprotocols` object. `subprotocols.work` identifies whether guarded work is enabled and its claim state. `subprotocols.consultation` identifies whether consultation is disabled, `user-mediated`, or `managed`, and, when enabled, its policy and claim state. A disabled consultation subprotocol MUST NOT require agents to initiate, answer, or wait for a consultation. A `user-mediated` subprotocol lets an agent publish a bounded question or escalation for the decision owner but MUST NOT authorize agents to run a work-affecting exchange among themselves. A `managed` subprotocol is available only to `COOP-2` or `COOP-3` and requires the explicit authorization and budget defined in Section 5.

An unqualified conformant `COOP-1`, `COOP-2`, or `COOP-3` claim describes the corresponding **work** contract. It does not imply that consultation is enabled or conformant. A conformant optional consultation claim is additional and MUST be stated in `subprotocols.consultation`; it MUST NOT be inferred from a Core `consultation` record alone. Merely selecting a contract or implementing one capability MUST NOT be represented as conformance. Imported workstate remains context, not authorization for external effects.

The machine-readable binding disclosure, subprotocol claims, loop policy, interaction, and result shapes are defined by `../../../schemas/awp-cooperation-0.1.schema.json`. Module-owned records MUST declare `module: urn:awp:cooperation`.

## 3. Portable collaboration without a contract

Without a selected Cooperation Contract, participants MAY exchange capsules, handoffs, artifacts, Core `consultation` records, critiques, alternative perspectives, and synthesized conclusions. This supports deliberately using different models or people for independent points of view.

A processor that receives recognized Cooperation or Coordination records without supporting their required semantics MUST preserve and expose them without implying that it validated their operational effect. Unknown fields MUST be preserved by a lossless processor.

An uncontracted participant MUST NOT claim that participants discovered one another, reserved a scope, prevented a conflicting mutation, or incorporated a contemporaneous result unless a binding provides evidence for that claim. A participant MAY make a local change under host policy, but it MUST disclose that no active Cooperation Contract conflict protection was present.

Core `consultation` records remain available for asynchronous advice seeking. They require no participant lease or shared ledger. A response MUST identify uncertainty and supporting evidence when available; advice MUST NOT be treated as authorization for an action.

## 4. COOP-1 — small-group conflict reduction

`COOP-1` is the default contract for a small shared project group. It reduces collisions in guarded, explicitly comparable work without requiring agents to exchange reasoning beyond the structured coordination information needed to proceed or block. A material conflict, ambiguity, or request for a work-affecting decision is surfaced to the declared decision owner; it does not start an autonomous agent-to-agent loop. It is intended to be useful for more than two concurrent participants without making an unmeasured capacity claim, though Section 4.3 permits an explicitly bounded two-participant operating envelope. It MUST NOT require a separate database or continuously running service. A binding MAY use repository-local files, atomic filesystem operations, an embedded store, or another local mechanism, provided it preserves the requirements below.

For every Coordination record or event used to make a work-coordination decision, the binding MUST perform `COOP-1` record-validity validation of workstate identity, event identity, ancestry, revisions, lifecycle transitions, pinned references, and typed precondition and verification bindings. It MUST exclude or block structurally stale or unverifiable input with a stable diagnostic. Projection MUST be independent of transport order, preserve concurrent non-commuting successors as contested, and return stable diagnostics for excluded or unverifiable input. A component MAY advertise a `deterministic-coordination-projector` capability, but that component alone MUST NOT claim `COOP-1`; the contract applies to the composed participant, binding, projector, checkpoint, and recovery behavior.

A `COOP-1` participant lease is a bounded liveness record with exit coupling in the cooperation binding. It lets participating agents discover an active participant and recover when its renewal stops; release is permitted only after the linked work is terminal and a durable handoff receipt is available. It does not authenticate a principal, fence a source-control write, grant authority, or require its holder to participate in a consultation. A binding's guarded-mutation guarantee applies only to participants that use the binding and obey its returned decision. Protected mutation paths, authenticated principals, epochs, and fencing are `COOP-3` guarantees and MUST NOT be inferred from a `COOP-1` claim.

### 4.1 Required participant workflow

Before guarded work, a `COOP-1` participant MUST:

1. Read the selected capsule or disclosed current workstate and its current checkpoint;
2. Refresh the cooperation binding, obtain the stable five-field binding identity defined below, and read a current observation containing reach and frontier; treat any stable-identity mismatch as `blocked`;
3. Enter or renew a bounded participant lease containing an identifier, project/worktree or equivalent execution location, revision, intended scope when known, and expiry;
4. Atomically announce its intent, guarded scopes, and access modes before the first guarded mutation; and
5. Obey the resulting compatibility decision.

The binding MUST make the announce-and-check operation atomic with respect to other `COOP-1` announce operations for the same guarded scopes. Compatible work MAY proceed concurrently. A known incompatible guarded mutation MUST return `blocked`, `waiting`, or an equivalent non-permitted outcome until participants record a partition, order, withdrawal, or escalation. A warning-only result is insufficient for a binding to claim the `COOP-1` guarded-mutation guarantee.

A binding that cannot make announce-and-check atomic with respect to concurrent announcements for the same guarded scopes MUST NOT claim `COOP-1`; it MUST disclose operational mode `snapshot_only`, `degraded`, or `unavailable` as applicable.

Before guarded work, participants MUST compare a stable binding identity containing the workstate identifier, repository-intrinsic project identifier, canonical store identifier, scope-model identifier and version, and binding epoch. The project identifier MUST derive from repository-intrinsic state and MUST NOT derive from a filesystem path or mount location. Any mismatched or unverifiable stable identity field MUST produce `blocked`.

Operational reach and frontier are observations, not stable identity. Each observation MUST identify its observation time, reach, and current frontier. Frontier values MAY differ as the binding advances; a participant MUST refresh, reconcile an ancestor or newer frontier, and block on an unverifiable history gap rather than require byte equality with another participant's earlier frontier. Reach is `shared`, `worktree-local`, `configured-unverified`, `degraded`, `snapshot-only`, or `unavailable`. An explicit store path begins as `configured-unverified`; it becomes `shared` only after at least two declared work participants have each recorded a binding entry that names the same stable store identity. A binding MUST retain or return that handshake evidence. A participant MUST NOT merge records from different store identifiers into one work decision; it MUST select one declared binding or return `blocked`. A binding MUST disclose its atomicity mechanism and the storage or filesystem assumptions under which it is valid.

A binding MUST normalize a path-like guarded scope to a repository-relative path, normalize separators and dot segments, and reject parent traversal outside the repository. Two path scopes overlap when they are equal or either is an ancestor of the other at a path-segment boundary. For every overlapping pair, the binding MUST apply a declared, versioned access-mode compatibility table. If either operation may mutate and the table does not explicitly permit the pair, the pair is incompatible. A scope kind without a declared comparison function is non-comparable; the binding MUST either conservatively block a guarded mutation or disclose that the scope is outside its guarded guarantee. “Known” means visible in the same atomic decision from all active, non-expired intents within the binding's declared reach and frontier. Case-folding, Unicode normalization, and symbolic-link treatment MUST be declared by the scope model.

`COOP-1` requires only declared physical or otherwise explicitly comparable scope. It MUST disclose that semantic conflicts outside its declared scope model can remain undetected. A clean source-control merge is not proof of compatibility.

### 4.2 Checkpoint, exit, and recovery

At a meaningful checkpoint and before exit, a participant MUST publish its actual scope, outcome, evidence references, unresolved work, and recommended next action through the selected binding. Actual scope is the participant's own assertion about work performed and its declared physical scopes; it is not an `observed_scope` record. An `observed_scope` record is analyzer-produced evidence under `COOP-2`, does not overwrite the participant's declaration, and may impose additional readiness consequences. The canonical capsule projection MUST identify the frontier it includes and its integrity digest. One logical publisher per workstate MUST serialize canonical capsule replacement using an expected capsule-frontier and digest comparison or an equivalent stale-writer exclusion rule. When a binding has a distinct event frontier, it MUST compare that expected event frontier independently; a legacy capsule frontier and a binding event frontier MUST NOT be assumed equal. A checkpoint receipt MUST identify the capsule path, whole-artifact digest, generated-region digest, and included frontier. A fresh-entry operation MUST report the capsule as `current`, `modified`, or `stale`; a binding MUST NOT permit guarded work while the canonical capsule is `modified` unless a host explicitly records an override outside the `COOP-1` claim.

On exit, the participant MUST publish its final semantic handoff before releasing its lease. The binding MUST reject release while an intent linked to the lease remains nonterminal or unless a durable receipt identifies an already published handoff artifact and its integrity digest. Recording a planned output identifier before the artifact exists is not publication confirmation. If the capsule projection, terminal publication, or lease release cannot be confirmed, the participant MUST report a recoverable pending exit rather than claim completion. If a participant crashes, its lease MUST expire without requiring a capsule rewrite; the durable capsule remains the last confirmed semantic handoff.

### 4.3 Minimum work-conformance evidence

A `COOP-1` work claim requires evidence for at least these scenarios:

1. Recognized records and unknown fields survive a portable round trip;
2. The same valid event set produces the same projected frontier, records, contested state, and diagnostics in different transport orders;
3. Invalid ancestry, revision, transition, precondition, verification, or staleness input is excluded or blocks the affected action with a stable diagnostic;
4. Two participants within the declared operating envelope with compatible scopes proceed without false blocking;
5. Simultaneous incompatible scope announcements produce one permitted and one blocked or waiting outcome;
6. A partition, order, withdrawal, or escalation unblocks the appropriate next action;
7. A lease expiry makes a crashed participant visibly inactive;
8. A new participant reads a checkpoint containing the latest confirmed handoff or an explicit freshness limitation; and
9. Two participants observing the same repository through different filesystem paths establish the same binding identity or fail closed with `blocked`.

The claim MUST state the tested operating envelope. A claim with a maximum concurrent participant count of three or more MUST additionally show three or more compatible participants proceeding without false blocking. It MUST NOT infer a larger participant limit, cross-host reliability, semantic-conflict detection, or effectiveness from this minimum evidence.

### 4.4 Work responsibility boundary

The work participant declares scope, access, evidence, and actual outcome; obeys blocked decisions; and supplies a concise rationale without private chain-of-thought. The work binding normalizes and compares scopes, owns transactions and leases, returns receipts, and enforces guarded-work lifecycle rules. A host enforces its own authority and side-effect policy; work metadata MUST NOT expand that authority.

## 5. Consultation and managed collaboration subprotocol

`subprotocols.consultation` is disabled unless explicitly enabled. Portable Core consultations may occur with no selected contract under Section 3. A `COOP-1` binding MAY enable only `user-mediated` consultation: agents may publish a bounded question, conflict, or escalation for the decision owner, but MUST NOT autonomously ask another agent to analyze, negotiate, delegate, or decide work whose outcome affects guarded work. Until the decision owner records a disposition, the affected work remains blocked, waiting, or explicitly outside the `COOP-1` guarantee.

`COOP-2` and `COOP-3` MAY enable `managed` collaboration. This is the level at which agents may directly exchange richer context, critique an approach, reconcile semantic conflicts, prepare an integration plan, or delegate bounded analysis. A managed interaction is never implicit: before its first agent-to-agent request, the binding MUST record an authorization reference from the decision owner or authorized principal and a policy naming the permitted participants, purpose, subject or scopes, decision owner, maximum rounds, maximum participant responses, maximum tool calls, maximum context tokens per request, maximum output tokens per response, and maximum total output tokens. A binding MUST stop or return `inconclusive` or `escalated` when any limit is reached. Token values are declared budget ceilings; a binding that cannot measure a value MUST disclose that limit as unenforced and MUST NOT claim enforced managed-collaboration budgeting.

Managed collaboration is not a prerequisite for a `COOP-2` work claim: a project may use COOP-2 semantic and integration mechanisms while leaving it disabled. When it is enabled, however, only the recorded policy—not a model preference, an A2A task, a tool invitation, or another participant's request—authorizes the interaction.

When enabled, a cooperation interaction MUST identify:

- `interaction_id` and the relevant workstate or checkpoint;
- `purpose`: `review`, `critique`, `alternative`, `delegation`, `decision`, or `synthesis`;
- a bounded question, task, or artifact subject;
- participants and a decision owner;
- the complete effective loop policy, its policy identifier, and its digest; and
- a terminal result of `accepted`, `revised`, `inconclusive`, `declined`, `timed_out`, or `escalated`, including any explicit remaining disagreement.

A managed interaction MUST additionally identify its authorization reference and the policy budget consumption or an explicit measurement limitation. A `user-mediated` interaction MUST identify the decision owner and MUST NOT treat a responder's advice as a disposition or permission for guarded work.

A consultation interaction MUST NOT silently authorize a guarded mutation or reserve a work scope. An accepted recommendation becomes actionable only when the decision owner records the resulting partition, order, intent, or other required project decision. A work lease MUST NOT be interpreted as consent to be interrupted for consultation, and a binding MUST NOT require a work lease as a precondition for initiating or responding to consultation.

The default enabled policy is deliberately conservative:

```json
{
  "policy_id": "coop-consult-default-loop-v1",
  "max_rounds": 2,
  "max_participant_responses": 3,
  "max_tool_calls": 8,
  "max_context_tokens_per_request": 12000,
  "max_output_tokens_per_response": 2000,
  "max_total_output_tokens": 6000,
  "progress_requirement": "new_artifact_evidence_decision_or_disagreement",
  "repeat_key_algorithm": "rfc8785-sha256-v1",
  "on_limit": "inconclusive_or_escalated",
  "continuation_authority": "decision_owner"
}
```

A round MUST add a new artifact, evidence item, explicit decision, or identified disagreement. The interaction MUST record that contribution as `progress.kind` with a reference to the new item. The `repeat_basis` MUST contain the purpose, canonical subject, context frontier, participant-set digest, and policy digest. `participant_set_digest` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of the lexicographically sorted array of participant identifier strings. `policy_digest` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of the complete effective policy object. `repeat_key` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of `repeat_basis`. A binding MUST reject an interaction whose supplied participant-set or policy digest does not match these calculations. A binding MUST deduplicate a repeated interaction with the same repeat key, or return the prior outcome, unless the repeat basis changed. On reaching a limit, it MUST return `inconclusive` or `escalated`; it MUST NOT start an unbounded optimization loop.

Loop budgets are independent of participant-lease duration and work-operation retry policy. A project or binding MAY declare additional parameters, higher budgets, stricter cost limits, time limits, evaluator thresholds, model diversity requirements, or domain-specific stopping predicates. Unknown policy parameters MUST be preserved. A participant that does not understand a parameter marked required by the effective policy MUST NOT claim to enforce that policy and MUST request a compatible policy, delegate enforcement to the binding, or decline the interaction. Only the declared decision owner MAY continue an interaction after the effective budget is exhausted.

A conformant consultation claim requires a binding-owned interaction record, repeat-key validation and deduplication, enforcement or declared delegation of the loop policy, and evidence that a bounded cross-model critique or synthesis terminates under policy. It is an additional claim, not evidence for a work contract.

The consultation participant declares purpose, question, subject, evidence, progress, and outcome. The consultation binding computes repeat keys and digests, deduplicates requests, returns receipts, and enforces or delegates loop limits. The decision owner accepts or rejects recommendations, authorizes continuation after an exhausted budget, and resolves escalations. A host enforces its own authority and side-effect policy.

## 6. COOP-2 — semantic, integration, and managed collaboration

`COOP-2` extends `COOP-1` work coordination with semantic awareness and integration assurance. It is also the first contract that may enable managed, directly inter-agent collaboration under Section 5's explicit authorization and budget. It MAY require a database, broker, registry, subscription system, or another service-backed binding, but neither a storage technology nor consultation alone supplies `COOP-2` semantics.

A `COOP-2` binding MUST maintain a stable semantic registry; resolve comparable selectors against pinned state revisions; compare declared scope, observed scope, and relied-upon reads; preserve `unknown` when relation evidence is ambiguous; and require acknowledgement or blocking under the effective policy. It MUST bind interface contracts, typed preconditions, verification results, staleness, change-set readiness, and integration results so that a stale or unsatisfied dependency cannot silently become integration-ready.

A `COOP-2` claim MUST declare its semantic-analysis coverage, selector and scope model, integration policy, tested participant count, and the failure behavior for unavailable or ambiguous semantic evidence. It MUST NOT infer protected external mutation, authentication, fencing, cross-host availability, or scalability from this claim.

A registry, selector analyzer, verification evaluator, or integration-readiness evaluator alone MUST NOT claim `COOP-2`; the contract applies to the composed participant, binding, semantic registry, analyzer, readiness evaluator, checkpoint, and recovery behavior.

## 7. COOP-3 — protected and scalable coordination

`COOP-3` extends `COOP-2` with authenticated protected mutation and a declared scalable operating envelope. It MAY require a database, broker, sharded registry, protected mutation gateway, or another service-backed binding.

For guarded mutation, a `COOP-3` binding MUST authenticate actors to principals and use protected optimistic-concurrency or lease operations with epochs and fencing tokens. It MUST reject stale owners at the protected mutation path; advisory metadata or an unprotected lock file is insufficient. Its policy MUST define retry bounds, lease duration, clock authority, deadlock and starvation behavior, cancellation consequences, and human or organizational arbitration.

A `COOP-3` claim MUST declare its tested participant count, scope distribution, latency and throughput measurements, failure behavior, retention policy, trust boundary, protected mutation paths, and the guarantees retained during restart, partition, duplicate delivery, and concurrent capsule projection. It MUST include fault evidence for stale-owner rejection, event loss or retention gaps, projector races, binding-identity disagreement, and recovery after interruption. It MUST NOT infer scale, availability, semantic accuracy, or enforcement from a storage technology alone.

### 7.1 `coop3-a2a-v1` distributed binding profile

`coop3-a2a-v1` is a named optional COOP-3 binding profile for participants that communicate across runtimes, hosts, or organizational boundaries through the Agent2Agent (A2A) protocol. A2A is the profile's communications and execution control plane; it is not the authoritative coordination state or a substitute for protected mutation enforcement. An A2A task accepted, updated, completed, failed, cancelled, or resumed state MUST NOT by itself be interpreted as an AWP intent decision, lease grant, fenced mutation, checkpoint, integration result, or authority grant.

A binding claiming `transport.profile: coop3-a2a-v1` MUST declare the supported A2A protocol version and interfaces, the authenticated mapping from A2A peer identity to AWP actor and accountable principal, its task-to-AWP-operation correlation and idempotency rule, its authoritative coordination-store identity, and its protected mutation gateway. It MUST carry an immutable AWP operation identifier and the relevant workstate and binding identity in every coordination request. The binding MUST durably record the resulting AWP event or return a stable rejection before it acknowledges the operation as accepted to a participant.

The profile MAY use A2A tasks, messages, artifacts, or data parts to carry typed AWP coordination requests and receipts. At minimum it MUST support carrying a request and response for participant entry or renewal, guarded intent announcement, guarded decision or conflict result, checkpoint or handoff publication, and terminal completion or withdrawal. A retry, reconnect, duplicate delivery, or a task routed to another A2A endpoint MUST resolve through the same AWP operation identifier; it MUST return the prior receipt or a stable conflict or rejection, and MUST NOT create a second lease, intent, fencing generation, or protected mutation.

The authoritative COOP-3 store and protected mutation gateway MUST enforce the actor/principal authorization, expected binding epoch and frontier or revision, protected scope, and current fencing token independently of A2A task state. The gateway MUST reject a stale, unauthenticated, or mismatched request even when A2A reports successful delivery. A binding MUST disclose A2A reachability, authentication failure, transport retry, and store or gateway availability separately; it MUST fail closed for protected mutation when any required enforcement check is unavailable.

`coop3-a2a-v1` does not require A2A for portable AWP exchange, COOP-1, COOP-2, or another conformant COOP-3 transport. A local file or transactional-ledger binding remains a valid low-administration option where its declared reach and guarantees are sufficient. A2A use alone is not evidence of COOP-3 conformance.

The current AWP repository specifies `COOP-2` and `COOP-3` but does not provide complete implementations or conformance claims for either.

## 8. Agent-facing implementation procedure

An agent implementing `COOP-1` from project instructions can use this bounded procedure:

```text
read current capsule and work policy
enter/renew lease
announce intent and guarded scope atomically
if compatible: work
if incompatible: partition, order, withdraw, or escalate
publish actual outcome and evidence
checkpoint canonical handoff
exit only after handoff confirmation; otherwise leave pending state visible
```

The checkpoint step SHOULD use the selected canonical workstate projector. A verified `no_change` receipt is sufficient when no semantic state changed; an incomplete or stale projection is not.

If the optional consultation subprotocol is enabled, the agent may separately initiate or answer a bounded interaction under its declared policy. The agent does not need to construct raw event ancestry, revisions, capsule digests, or storage transactions. The binding or adapter owns those details and returns durable receipts. The agent remains responsible for accurately declaring work scope, respecting blocked outcomes, supplying concise rationale and evidence, and not treating context or consultation advice as authorization.
