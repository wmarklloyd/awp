# AWP Cooperation Contracts 0.1.0

**Status:** Experimental working-draft profile specification

**Module ID:** `urn:awp:cooperation`

**Profile family:** Cooperation Contracts (`COOP`)

**Direct dependencies:** Capsule, Handoff, and Coordination when the selected contract requires active coordination

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Cooperation Contracts define what several human or software-agent participants can expect while working on the same project. They cover both safe coordination of guarded work and productive collaboration: independent perspectives, critique, review, delegation, synthesis, and durable handoff.

`COOP-0`, `COOP-1`, and later `COOP-*` labels are cooperation-profile claims. They are not replacements for the Coordination module's `C0`–`C3` conformance levels. A binding MAY implement a Coordination conformance level and one Cooperation Contract, but it MUST declare each independently.

This document is an experimental profile specification. It does not change released AWP 0.6.0 semantics or make the current reference tools conformant to a contract they do not fully implement.

The module capability `guarded-scope-coordination` means that the selected contract uses Coordination records or an equivalent binding to compare declared scopes and return guarded mutation decisions. Selecting that capability activates the Cooperation module's conditional dependency on `urn:awp:coordination`.

## 2. Common terms

A **participant** is a human or agent performing work or supplying a bounded collaboration response. A **decision owner** is the participant or declared human principal responsible for accepting a result, continuing a loop, or escalating an unresolved issue. A **guarded scope** is a declared part of a work product whose incompatible modification is controlled by the selected contract.

A **cooperation interaction** is a bounded request for critique, alternative analysis, review, delegation, decision support, or synthesis. It is not an authorization grant and does not require participants to disclose private chain-of-thought.

An implementation MUST identify the selected contract, effective interaction policy, operational mode, and any material limitations in its entry or operation response. Imported workstate remains context, not authorization for external effects.

The machine-readable binding disclosure, loop policy, interaction, and result shapes are defined by `../../../schemas/awp-cooperation-0.1.schema.json`. Module-owned records MUST declare `module: urn:awp:cooperation`.

## 3. COOP-0 — uncoordinated collaboration

`COOP-0` permits substantial collaboration but makes no active-coordination guarantee. Participants MAY exchange capsules, handoffs, artifacts, consultation requests, critiques, alternative perspectives, and synthesized conclusions. This supports deliberately using different models or people for different viewpoints.

`COOP-0` MUST NOT claim that participants discovered one another, reserved a scope, prevented a conflicting mutation, or incorporated a contemporaneous result unless a binding provides evidence for that claim. A participant MAY make a local change under host policy, but it MUST disclose that no Cooperation Contract conflict protection was active.

Every `COOP-0` cooperation interaction MUST have a purpose, question or task, decision owner, and terminal outcome. The outcome is `accepted`, `revised`, `inconclusive`, `declined`, `timed_out`, or `escalated`.

## 4. COOP-1 — default cooperation contract

`COOP-1` is the default contract for a small shared project group. It is intended to be useful for more than two concurrent participants without making an unmeasured capacity claim, though Section 4.5 permits an explicitly bounded two-participant operating envelope. It MUST NOT require a separate database or continuously running service. A binding MAY use repository-local files, atomic filesystem operations, an embedded store, or another local mechanism, provided it preserves the requirements below.

`COOP-1` extends `COOP-0` and includes all of its requirements, including its terminal-outcome vocabulary.

A `COOP-1` participant lease is a bounded liveness record in the cooperation binding. It lets participating agents discover an active participant and recover when its renewal stops; it does not authenticate a principal, fence a source-control write, or grant authority. A binding's guarded-mutation guarantee applies only to participants that use the binding and obey its returned decision. Protected mutation paths, authenticated principals, epochs, and fencing remain separate Coordination C3 semantics and MUST NOT be inferred from a `COOP-1` claim.

### 4.1 Required participant workflow

Before guarded work, a `COOP-1` participant MUST:

1. Read the selected capsule or disclosed current workstate and its current checkpoint;
2. Refresh the cooperation binding, obtain the stable five-field binding identity defined below, and read a current observation containing reach and frontier; treat any stable-identity mismatch as `blocked`;
3. Enter or renew a bounded participant lease containing an identifier, project/worktree or equivalent execution location, revision, intended scope when known, and expiry;
4. Atomically announce its intent, guarded scopes, access modes, and applicable interaction policy before the first guarded mutation; and
5. Obey the resulting compatibility decision.

The binding MUST make the announce-and-check operation atomic with respect to other `COOP-1` announce operations for the same guarded scopes. Compatible work MAY proceed concurrently. A known incompatible guarded mutation MUST return `blocked`, `waiting`, or an equivalent non-permitted outcome until participants record a partition, order, withdrawal, or escalation. A warning-only result is insufficient for a binding to claim the `COOP-1` guarded-mutation guarantee.

Before guarded work, participants MUST compare a stable binding identity containing the workstate identifier, repository-intrinsic project identifier, canonical store identifier, scope-model identifier and version, and binding epoch. The project identifier MUST derive from repository-intrinsic state and MUST NOT derive from a filesystem path or mount location. Any mismatched or unverifiable stable identity field MUST produce `blocked`.

Operational reach and frontier are observations, not stable identity. Each observation MUST identify its observation time, reach, and current frontier. Frontier values MAY differ as the binding advances; a participant MUST refresh, reconcile an ancestor or newer frontier, and block on an unverifiable history gap rather than require byte equality with another participant's earlier frontier. Reach is `shared`, `worktree-local`, `configured-unverified`, `degraded`, `snapshot-only`, or `unavailable`. An explicit store path begins as `configured-unverified`; participants establish `shared` reach for their interaction only after each independently accesses the same stable store identity. A binding MUST disclose its atomicity mechanism and the storage or filesystem assumptions under which it is valid.

A binding MUST normalize a path-like guarded scope to a repository-relative path, normalize separators and dot segments, and reject parent traversal outside the repository. Two path scopes overlap when they are equal or either is an ancestor of the other at a path-segment boundary. For every overlapping pair, the binding MUST apply a declared, versioned access-mode compatibility table. If either operation may mutate and the table does not explicitly permit the pair, the pair is incompatible. A scope kind without a declared comparison function is non-comparable; the binding MUST either conservatively block a guarded mutation or disclose that the scope is outside its guarded guarantee. “Known” means visible in the same atomic decision from all active, non-expired intents within the binding's declared reach and frontier. Case-folding, Unicode normalization, and symbolic-link treatment MUST be declared by the scope model.

`COOP-1` requires only declared physical or otherwise explicitly comparable scope. It MUST disclose that semantic conflicts outside its declared scope model can remain undetected. A clean source-control merge is not proof of compatibility.

### 4.2 Cooperation and symbiosis

`COOP-1` participants MAY initiate cooperation interactions while performing compatible work. Examples include asking a different model for an independent design, requesting a critique before integration, delegating a bounded investigation, or asking a decision owner to synthesize alternatives.

An interaction MUST identify:

- `interaction_id` and the relevant workstate or checkpoint;
- `purpose`: `review`, `critique`, `alternative`, `delegation`, `decision`, or `synthesis`;
- a bounded question, task, or artifact subject;
- participants and a decision owner;
- the effective loop policy and its policy identifier or digest; and
- a terminal result using the `COOP-0` outcome vocabulary and any explicit remaining disagreement.

An interaction MUST NOT silently authorize a guarded mutation. An accepted recommendation becomes actionable only when the decision owner records the resulting partition, order, intent, or other required project decision.

### 4.3 Bounded feedback loops

The default `COOP-1` loop policy is deliberately conservative:

```json
{
  "policy_id": "coop-1-default-loop-v1",
  "max_rounds": 2,
  "max_participant_responses": 3,
  "max_tool_calls": 8,
  "progress_requirement": "new_artifact_evidence_decision_or_disagreement",
  "repeat_key_algorithm": "rfc8785-sha256-v1",
  "on_limit": "inconclusive_or_escalated",
  "continuation_authority": "decision_owner"
}
```

A round MUST add a new artifact, evidence item, explicit decision, or identified disagreement. The interaction MUST record that contribution as `progress.kind` with a reference to the new item. The `repeat_basis` MUST contain the purpose, canonical subject, context frontier, participant-set digest, and policy digest. `repeat_key` MUST equal `sha256:` followed by the SHA-256 digest of the RFC 8785 canonical JSON serialization of `repeat_basis`. A binding MUST deduplicate a repeated interaction with the same repeat key, or return the prior outcome, unless the repeat basis changed. On reaching a limit, it MUST return `inconclusive` or `escalated`; it MUST NOT start an unbounded optimization loop.

The loop policy is extensible. A project or binding MAY declare additional parameters, higher budgets, stricter cost limits, time limits, evaluator thresholds, model diversity requirements, or domain-specific stopping predicates. Unknown policy parameters MUST be preserved. A participant that does not understand a parameter marked required by the effective policy MUST NOT claim to enforce that policy and MUST request a compatible policy, delegate enforcement to the binding, or decline the interaction.

Only the declared decision owner MAY continue an interaction after the effective budget is exhausted. A policy MAY assign that authority to a human principal, a project role, or a bounded automated evaluator; it MUST identify the authority and its basis.

### 4.4 Checkpoint, exit, and recovery

At a meaningful checkpoint and before exit, a participant MUST publish its actual scope, outcome, evidence references, unresolved work, and recommended next action through the selected binding. The canonical capsule projection MUST identify the frontier it includes and its integrity digest. One logical publisher per workstate MUST serialize canonical capsule replacement using an expected frontier and digest comparison or an equivalent stale-writer exclusion rule.

On exit, the participant MUST publish its final semantic handoff before releasing its lease. The binding MUST reject release while an intent linked to the lease remains nonterminal or unless a durable receipt identifies an already published handoff artifact and its integrity digest. Recording a planned output identifier before the artifact exists is not publication confirmation. If the capsule projection, terminal publication, or lease release cannot be confirmed, the participant MUST report a recoverable pending exit rather than claim completion. If a participant crashes, its lease MUST expire without requiring a capsule rewrite; the durable capsule remains the last confirmed semantic handoff.

### 4.5 Minimum conformance evidence

A `COOP-1` claim requires evidence for at least these scenarios:

1. Two participants within the declared operating envelope with compatible scopes proceed without false blocking;
2. Simultaneous incompatible scope announcements produce one permitted and one blocked or waiting outcome;
3. A partition, order, withdrawal, or escalation unblocks the appropriate next action;
4. A lease expiry makes a crashed participant visibly inactive;
5. A bounded cross-model critique or synthesis interaction terminates under its loop policy; and
6. A new participant reads a checkpoint containing the latest confirmed handoff or an explicit freshness limitation; and
7. Two participants observing the same repository through different filesystem paths establish the same binding identity or fail closed with `blocked`.

The claim MUST state the tested operating envelope. A claim with a maximum concurrent participant count of three or more MUST additionally show three or more compatible participants proceeding without false blocking. It MUST NOT infer a larger participant limit, cross-host reliability, semantic-conflict detection, or effectiveness from this minimum evidence.

### 4.6 Responsibility boundary

The participant declares purpose, scope, access, evidence, progress, and actual outcome; obeys blocked decisions; and supplies a concise rationale without private chain-of-thought. The binding normalizes and compares scopes, owns transactions and leases, computes repeat keys and digests, deduplicates requests, returns receipts, and enforces loop limits. The decision owner accepts or rejects recommendations, authorizes continuation after an exhausted budget, and resolves escalations. A host enforces its own authority and side-effect policy; cooperation metadata MUST NOT expand that authority.

## 5. COOP-2 and later contracts

`COOP-2` and later contracts preserve the participant-facing semantics of the contracts they extend while defining a stronger operating envelope. They MAY require a database, broker, sharded registry, subscription system, authenticated identity, or another scalable binding.

A `COOP-2` claim MUST declare its tested participant count, scope distribution, latency and throughput measurements, failure behavior, retention policy, and the guarantees retained during restart, partition, duplicate delivery, and concurrent capsule projection. It MUST NOT claim that a storage technology alone supplies cooperation semantics.

## 6. Agent-facing implementation procedure

An agent implementing `COOP-1` from project instructions can use this bounded procedure:

```text
read current capsule and contract policy
enter/renew lease
announce intent and guarded scope atomically
if compatible: work
if incompatible: partition, order, withdraw, or escalate
optionally run a bounded cooperation interaction
publish actual outcome and evidence
checkpoint canonical handoff
exit only after handoff confirmation; otherwise leave pending state visible
```

The agent does not need to construct raw event ancestry, revisions, capsule digests, or storage transactions. The binding or adapter owns those details and returns durable receipts. The agent remains responsible for accurately declaring its scope, respecting blocked outcomes, supplying concise rationale and evidence, and not treating context as authorization.
