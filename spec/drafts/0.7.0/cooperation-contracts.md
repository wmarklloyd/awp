# AWP Cooperation Contracts 0.1.0

**Status:** Experimental working-draft profile specification

**Profile family:** Cooperation Contracts (`CC`)

**Direct dependencies:** Capsule, Handoff, and Coordination when the selected contract requires active coordination

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals.

## 1. Purpose and status

Cooperation Contracts define what several human or software-agent participants can expect while working on the same project. They cover both safe coordination of guarded work and productive collaboration: independent perspectives, critique, review, delegation, synthesis, and durable handoff.

`CC-0`, `CC-1`, and later `CC-*` labels are cooperation-profile claims. They are not replacements for the Coordination module's `C0`–`C3` conformance levels. A binding MAY implement a Coordination conformance level and one Cooperation Contract, but it MUST declare each independently.

This document is an experimental profile specification. It does not change released AWP 0.6.0 semantics or make the current reference tools conformant to a contract they do not fully implement.

## 2. Common terms

A **participant** is a human or agent performing work or supplying a bounded collaboration response. A **decision owner** is the participant or declared human principal responsible for accepting a result, continuing a loop, or escalating an unresolved issue. A **guarded scope** is a declared part of a work product whose incompatible modification is controlled by the selected contract.

A **cooperation interaction** is a bounded request for critique, alternative analysis, review, delegation, decision support, or synthesis. It is not an authorization grant and does not require participants to disclose private chain-of-thought.

An implementation MUST identify the selected contract, effective interaction policy, operational mode, and any material limitations in its entry or operation response. Imported workstate remains context, not authorization for external effects.

## 3. CC-0 — uncoordinated collaboration

`CC-0` permits substantial collaboration but makes no active-coordination guarantee. Participants MAY exchange capsules, handoffs, artifacts, consultation requests, critiques, alternative perspectives, and synthesized conclusions. This supports deliberately using different models or people for different viewpoints.

`CC-0` MUST NOT claim that participants discovered one another, reserved a scope, prevented a conflicting mutation, or incorporated a contemporaneous result unless a binding provides evidence for that claim. A participant MAY make a local change under host policy, but it MUST disclose that no Cooperation Contract conflict protection was active.

Every `CC-0` cooperation interaction MUST have a purpose, question or task, decision owner, and terminal outcome. The outcome is `accepted`, `revised`, `inconclusive`, `declined`, `timed_out`, or `escalated`.

## 4. CC-1 — default cooperation contract

`CC-1` is the default contract for a small shared project group. It is intended to be useful for more than two concurrent participants without making an unmeasured capacity claim. It MUST NOT require a separate database or continuously running service. A binding MAY use repository-local files, atomic filesystem operations, an embedded store, or another local mechanism, provided it preserves the requirements below.

### 4.1 Required participant workflow

Before guarded work, a `CC-1` participant MUST:

1. Read the selected capsule or disclosed current workstate and its current checkpoint;
2. Refresh the shared cooperation binding and disclose whether its reach is shared, worktree-local, degraded, snapshot-only, or unavailable;
3. Enter or renew a bounded participant lease containing an identifier, project/worktree or equivalent execution location, revision, intended scope when known, and expiry;
4. Atomically announce its intent, guarded scopes, access modes, and applicable interaction policy before the first guarded mutation; and
5. Obey the resulting compatibility decision.

The binding MUST make the announce-and-check operation atomic with respect to other `CC-1` announce operations for the same guarded scopes. Compatible work MAY proceed concurrently. A known incompatible guarded mutation MUST return `blocked`, `waiting`, or an equivalent non-permitted outcome until participants record a partition, order, withdrawal, or escalation. A warning-only result is insufficient for a binding to claim the `CC-1` guarded-mutation guarantee.

`CC-1` requires only declared physical or otherwise explicitly comparable scope. It MUST disclose that semantic conflicts outside its declared scope model can remain undetected. A clean source-control merge is not proof of compatibility.

### 4.2 Cooperation and symbiosis

`CC-1` participants MAY initiate cooperation interactions while performing compatible work. Examples include asking a different model for an independent design, requesting a critique before integration, delegating a bounded investigation, or asking a decision owner to synthesize alternatives.

An interaction MUST identify:

- `interaction_id` and the relevant workstate or checkpoint;
- `purpose`: `review`, `critique`, `alternative`, `delegation`, `decision`, or `synthesis`;
- a bounded question, task, or artifact subject;
- participants and a decision owner;
- the effective loop policy and its policy identifier or digest; and
- the terminal result or explicit remaining disagreement.

An interaction MUST NOT silently authorize a guarded mutation. An accepted recommendation becomes actionable only when the decision owner records the resulting partition, order, intent, or other required project decision.

### 4.3 Bounded feedback loops

The default `CC-1` loop policy is deliberately conservative:

```json
{
  "policy_id": "cc-1-default-loop-v1",
  "max_rounds": 2,
  "max_participant_responses": 3,
  "max_tool_calls": 8,
  "progress_requirement": "new_artifact_evidence_decision_or_disagreement",
  "repeat_key": "purpose+subject+context_frontier",
  "on_limit": "inconclusive_or_escalated",
  "continuation_authority": "decision_owner"
}
```

A round MUST add a new artifact, evidence item, explicit decision, or identified disagreement. A binding MUST deduplicate a repeated interaction with the same repeat key, or return the prior outcome, unless the context frontier or declared subject changed. On reaching a limit, it MUST return `inconclusive` or `escalated`; it MUST NOT start an unbounded optimization loop.

The loop policy is extensible. A project or binding MAY declare additional parameters, higher budgets, stricter cost limits, time limits, evaluator thresholds, model diversity requirements, or domain-specific stopping predicates. Unknown policy parameters MUST be preserved. A participant that does not understand a parameter marked required by the effective policy MUST NOT claim to enforce that policy and MUST request a compatible policy, delegate enforcement to the binding, or decline the interaction.

Only the declared decision owner MAY continue an interaction after the effective budget is exhausted. A policy MAY assign that authority to a human principal, a project role, or a bounded automated evaluator; it MUST identify the authority and its basis.

### 4.4 Checkpoint, exit, and recovery

At a meaningful checkpoint and before exit, a participant MUST publish its actual scope, outcome, evidence references, unresolved work, and recommended next action through the selected binding. The canonical capsule projection MUST identify the frontier it includes and its integrity digest. One logical publisher per workstate MUST serialize canonical capsule replacement using an expected frontier and digest comparison or an equivalent stale-writer exclusion rule.

On exit, the participant MUST publish its final semantic handoff before releasing its lease. If the capsule projection, terminal publication, or lease release cannot be confirmed, it MUST report a recoverable pending exit rather than claim completion. If a participant crashes, its lease MUST expire without requiring a capsule rewrite; the durable capsule remains the last confirmed semantic handoff.

### 4.5 Minimum conformance evidence

A `CC-1` claim requires evidence for at least these scenarios:

1. Three or more participants with compatible scopes proceed without false blocking;
2. Simultaneous incompatible scope announcements produce one permitted and one blocked or waiting outcome;
3. A partition, order, withdrawal, or escalation unblocks the appropriate next action;
4. A lease expiry makes a crashed participant visibly inactive;
5. A bounded cross-model critique or synthesis interaction terminates under its loop policy; and
6. A new participant reads a checkpoint containing the latest confirmed handoff or an explicit freshness limitation.

The claim MUST state the tested operating envelope. It MUST NOT infer an upper participant limit, cross-host reliability, semantic-conflict detection, or effectiveness from this minimum evidence.

## 5. CC-2 and later contracts

`CC-2` and later contracts preserve the participant-facing semantics of the contracts they extend while defining a stronger operating envelope. They MAY require a database, broker, sharded registry, subscription system, authenticated identity, or another scalable binding.

A `CC-2` claim MUST declare its tested participant count, scope distribution, latency and throughput measurements, failure behavior, retention policy, and the guarantees retained during restart, partition, duplicate delivery, and concurrent capsule projection. It MUST NOT claim that a storage technology alone supplies cooperation semantics.

## 6. Agent-facing implementation procedure

An agent implementing `CC-1` from project instructions can use this bounded procedure:

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
