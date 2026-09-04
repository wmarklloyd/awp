# Agent Workstate Protocol (AWP)

## Design review: motivation and proposed direction

This section is intentionally informative. It explains why AWP exists, what problem it is designed to solve, and why the proposed architecture is shaped the way it is. The normative specification begins in Section 1.

### The problem

LLM-assisted work currently leaves state scattered across chat transcripts, model-specific memory, tool logs, source-control commits, workflow checkpoints, and a user's recollection. That makes continuation fragile. A new model can receive the conversation but still not know which statements are verified, which proposals were rejected, which files were changed, which actions were authorized, or what remains blocked.

The problem becomes more serious when several agents work on one project. Git can detect many byte-level collisions after the fact, but it does not express that one agent intends to change an API while another depends on its current contract. Two edits can merge cleanly while breaking a shared invariant, test assumption, data schema, or behavior.

AWP treats this as a missing layer of infrastructure: a portable representation of the evolving meaning of work, plus a coordination record for agents changing shared systems.

### The proposed answer

AWP is best understood as a **portable checkpoint and coordination protocol**, not as “Markdown with more syntax.” It has a human-facing top layer and a typed machine-facing state beneath it.

The proposed default exchange object is one self-contained file:

```text
project.awp.md
```

It begins with ordinary Markdown that a person can read in any editor. It then contains or references a manifest, current semantic snapshot, append-only events, evidence, and artifacts. An optional coordination profile adds code changes, work intents, interface contracts, and integration information. A receiving LLM should be able to continue the work from the core profile without reconstructing the entire original conversation.

For larger or actively edited work, the same logical object can be expanded into a `.workstate/` directory or packaged as `.pws`. These are representations of one protocol model, not competing formats.

### Why Markdown is at the top

Markdown is an excellent universal briefing surface. It is easy to send, inspect, diff, render, and explain to a human or a model. The top section should answer, quickly:

- What is this project or task?
- What is the current state?
- What decisions are active?
- Which agents or people are working on what?
- What is blocked or at risk?
- What should happen next?

The Markdown briefing is bound to a checkpoint and event frontier so that readers can tell whether it is current. It is not sufficient as the sole semantic representation: prose alone cannot reliably distinguish a verified fact from an assumption or an intended change from a completed one.

### Why typed state and an event ledger are still needed

The machine layer separates concepts that are often conflated in conversation:

- intent from execution;
- authority from identity;
- claim from evidence;
- decision from suggestion;
- artifact path from artifact version;
- textual merge from semantic compatibility;
- current snapshot from historical change.

The event ledger makes important changes appendable, attributable, and auditable. A materialized snapshot makes the latest state efficient to load. Markdown makes the state approachable. These layers reinforce each other.

### Why this is extensible

No universal format should attempt to serialize every agent runtime's internal state. AWP therefore defines a portable semantic core and namespaced extensions. An A2A adapter can carry tasks and artifacts; an MCP adapter can expose the workstate as resources and controlled update tools; a workflow adapter can preserve native checkpoints; and a model-specific adapter can retain optimization data.

An unfamiliar reader can ignore an optional extension and still understand the goal, evidence, decisions, artifacts, risks, and next action. A compatible runtime can use the extension for more precise resumption.

### What “resume” means

AWP cannot transfer hidden activations, a model's KV cache, or private chain-of-thought. It transfers the durable work product needed to resume:

1. **Semantic resumption:** another LLM can understand and continue the work.
2. **Operational resumption:** a compatible system can restore tools, pending tasks, dependencies, and workflow position.
3. **Exact runtime resumption:** the originating runtime can restore its private checkpoint extension.

The first level is the interoperability guarantee. The higher levels are optional optimizations.

### Why coordination must be above Git

Git remains valuable and should be referenced wherever it is available. It records byte revisions, ancestry, patches, and commits. AWP adds the information agents need before and during integration:

- announced work intent;
- semantic scopes such as symbols, APIs, schemas, behaviors, and invariants;
- time-bounded coordination leases;
- shared interface contracts;
- base revisions and compare-and-swap-style preconditions;
- expected semantic effects;
- integration order and ownership;
- combined verification results.

This lets agents negotiate before clobbering one another and detect conflicts that a textual merge cannot see. AWP does not replace Git or pretend that a lease is a permission system. It is the semantic coordination layer above source control.

### Design strengths

The design is strongest where it:

- gives a new model a compact, high-value continuation point;
- preserves evidence and uncertainty instead of flattening everything into prose;
- works as one shareable file while scaling to a directory/package;
- supports both same-runtime recovery and cross-runtime handoff;
- records collaboration before code reaches a merge queue;
- allows vendors to extend the format without fragmenting the core;
- keeps human review possible at every major state transition.

### Design risks and deliberate tradeoffs

AWP introduces real complexity. Event histories grow, semantic scopes are difficult to infer across languages, leases can become stale, and no format can guarantee that an LLM interprets a claim correctly. A single self-contained file can become large when it embeds a repository or binary artifacts. A human-authored Markdown briefing can also drift from structured state.

The specification addresses these risks through snapshots, content hashes, explicit frontiers, conflict records, expiring leases, declared resumption levels, precondition checks, generated views, and a rule that typed event history remains authoritative for machine decisions. It favors transparent uncertainty over false automation.

### Recommended initial scope

The first implementation should focus on a narrow, useful slice:

1. one-file `project.awp.md` export/import;
2. root Markdown briefing plus typed snapshot;
3. goals, constraints, claims, evidence, decisions, tasks, artifacts, and checkpoints;
4. work intents, scopes, contracts, change sets, and semantic conflicts;
5. embedded or content-addressed relevant code and patches;
6. validation, summarization, and safe handoff commands;
7. empirical tests measuring whether another LLM can continue successfully.

The full event DAG, packages, signatures, distributed leases, runtime adapters, and formal registries can mature around that core.

### Review conclusion

The direction is technically plausible and fills a real gap. The most important design decision is to make `project.awp.md` a complete, human-readable exchange capsule while retaining a structured semantic model underneath. AWP should be judged by a practical test: can a different agent, given only the capsule and available project artifacts, correctly understand the current work, avoid violating constraints, coordinate with other agents, and take the next safe step?

### Changes from version 0.2.0

This version makes the following decisions explicit:

- the complete exchange profile is a self-contained `.awp.md` file;
- the file begins with a Markdown briefing and can embed its machine state and artifacts;
- `completeness` declares whether a capsule is a summary, portable handoff, or full export;
- the briefing is bound to a checkpoint and event frontier;
- a minimal core profile defines the interoperability floor;
- concurrent code work has an optional, experimental profile with first-class intents, semantic scopes, leases, contracts, change sets, and integration plans;
- event-envelope versioning is distinct from protocol versioning;
- a normative core JSON Schema and an empirical handoff test accompany the prose;
- briefing drift, capsule boundaries, and snapshot/event reconciliation have deterministic validation rules;
- source-control revisions remain useful evidence but are not treated as semantic coordination;
- the normative version is now `0.3.0`.

---

## Draft Specification 0.3.0

**Status:** Exploratory draft  
**Short name:** AWP  
**Human-facing name:** Workstate  
**Specification version:** 0.3.0  
**Last updated:** 2026-09-03

---

## 1. Abstract

The Agent Workstate Protocol (AWP) defines a vendor-neutral representation for preserving, exchanging, inspecting, and resuming work performed by humans, language models, and software agents.

AWP captures the durable semantic state of work rather than the private internal state of a model. A AWP workstate can describe goals, success criteria, constraints, permissions, claims, evidence, decisions, plans, tasks, artifacts, execution results, unresolved questions, and continuation instructions. It can also contain optional runtime-specific extensions that allow an originating system to resume execution more precisely.

AWP supports two complementary uses:

1. **Persistence:** saving an ongoing session so that the same or a different system can continue it later.
2. **Exchange:** transmitting complete workstates or incremental changes between people, agents, runtimes, and organizations.

The same logical model may be represented as an editable directory, a packaged single-file artifact, or a sequence of wire messages. Every complete file representation begins conceptually with a human-readable Markdown briefing. The briefing is the primary human entry point; typed records and events provide the authoritative machine-interpretable state behind it.

AWP also defines an optional, experimental coordination profile for multiple agents working concurrently on the same codebase. Agents can announce intended changes, reserve overlapping scopes, negotiate interfaces, publish preconditions, detect semantic collisions, and coordinate integration before byte-level source-control conflicts occur. Coordination-profile support is not required for core semantic handoff interoperability.

---

## 2. Motivation

Existing formats and protocols address parts of agent-assisted work:

- document formats preserve authored content;
- chat transcripts preserve messages;
- workflow engines preserve implementation-specific execution state;
- agent protocols exchange tasks, messages, and artifacts;
- model context protocols expose resources, prompts, and tools;
- source-control systems preserve file changes;
- observability systems preserve traces and telemetry.

None of these, by itself, provides a portable account of the current meaning of a piece of work. A transcript may contain the answer, but it does not reliably distinguish a superseded proposal from an accepted decision. A checkpoint may resume one framework, but it may be meaningless to another. A Git diff records changed bytes, but not the goal, evidence, authorization, or remaining work.

AWP addresses this gap by representing the state necessary to understand and continue work across model, vendor, framework, and time boundaries.

---

## 3. Design goals

AWP is designed to provide:

### 3.1 Semantic portability

A conforming reader should be able to determine:

- what outcome is being pursued;
- what constraints and permissions apply;
- what is known, inferred, disputed, or unknown;
- which evidence supports important claims;
- which decisions are active and which have been superseded;
- what work has been completed;
- which artifacts were created or modified;
- what remains to be done;
- what action is recommended next.

### 3.2 Model and vendor independence

The portable core must not require a particular model provider, agent framework, orchestration engine, storage service, or tool protocol.

### 3.3 Human inspectability

AWP records should be readable with ordinary text-processing tools. Implementations should be able to render concise Markdown summaries and timelines.

### 3.4 Auditability

Changes to workstate should be attributable, timestamped, and appendable. Important conclusions should be connected to evidence and scope.

### 3.5 Partial comprehension

A reader that does not understand an optional extension must still be able to interpret the portable core.

### 3.6 Safe continuation

A receiving agent must be able to identify authorization boundaries, untrusted content, pending external side effects, secrets, and actions requiring confirmation.

### 3.7 Incremental exchange

Agents should be able to exchange deltas without retransmitting the complete workstate.

### 3.8 Version control compatibility

The editable representation should produce useful textual diffs and support ordinary source-control workflows.

### 3.9 Markdown-first human access

A person opening a complete AWP workstate should encounter a concise Markdown briefing before machine-oriented detail. The briefing should explain the goal, current state, active participants, concurrent work, risks, blockers, and next action without requiring a AWP-specific viewer.

### 3.10 Concurrent agent coordination

Multiple agents should be able to coordinate overlapping code changes at the level of components, symbols, interfaces, invariants, and intended effects. AWP should detect potential interference before changes are committed and preserve enough context to integrate compatible work safely.

---

## 4. Non-goals

AWP does not attempt to:

- serialize hidden neural activations, attention state, or model KV caches;
- require or expose private chain-of-thought;
- reproduce model behavior bit-for-bit across providers;
- define a universal agent execution engine;
- replace source control, artifact storage, A2A, MCP, or workflow frameworks;
- guarantee that claims contained in a workstate are true;
- grant authority merely because an instruction appears in a workstate;
- standardize every model-specific message or tool-call representation.

AWP may reference or extend these systems while keeping their internal details outside the portable core.

---

## 5. Conventions and normative language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as normative requirements.

Examples use JSON. JSON examples may be formatted across multiple lines even where the stored representation uses JSON Lines.

Timestamps MUST use RFC 3339 format and SHOULD use UTC. Content digests SHOULD use SHA-256 unless a future registry specifies another algorithm.

---

## 6. Terminology

### 6.1 Workstate

A coherent, identifiable body of ongoing or completed work represented by AWP.

### 6.2 Actor

A human, model, agent, service, or automated process that observes, proposes, changes, verifies, or approves workstate.

### 6.3 Record

A typed semantic object such as a goal, claim, decision, task, or artifact descriptor.

### 6.4 Event

An immutable statement that a change, observation, or action occurred. Events form the authoritative historical ledger.

### 6.5 Snapshot

A materialized view of the effective workstate at a specific event frontier. A snapshot is derived state and may be regenerated from events.

### 6.6 Artifact

A file, document, patch, image, dataset, generated result, or other concrete input or output associated with the work.

### 6.7 Evidence

Material supporting or contradicting a claim, decision, or verification result.

### 6.8 Checkpoint

A resumable point that summarizes current state, remaining work, risks, and the recommended continuation.

### 6.9 Delta

A set of events based on a known prior checkpoint or event frontier.

### 6.10 Portable core

The AWP fields and record types that conforming implementations understand independently of optional extensions.

### 6.11 Extension

Namespaced data that adds domain-, vendor-, or runtime-specific meaning.

### 6.12 Runtime checkpoint

Implementation-specific state that may allow exact or near-exact resumption within a particular runtime.

### 6.13 Work intent

An agent's declaration of the outcome it intends to produce, the code and interfaces it expects to touch, and the assumptions under which it is working.

### 6.14 Coordination scope

A semantic or physical region of work that may be affected by an actor. Scopes may identify repositories, modules, files, symbols, APIs, schemas, tests, behaviors, invariants, or deployment surfaces.

### 6.15 Lease

A time-bounded coordination claim over a scope. A lease communicates planned activity and conflict policy; it does not by itself grant filesystem, repository, or organizational authority.

### 6.16 Change set

A proposed or completed coherent group of artifact and semantic changes, including intent, preconditions, compatibility information, verification, and integration dependencies.

### 6.17 Interface contract

A shared description of a boundary between concurrently changing components, such as a function signature, API schema, data contract, invariant, or behavioral guarantee.

### 6.18 Profile

A named set of records, events, validation rules, and capabilities that an implementation may support. The `core` profile is REQUIRED for portable semantic resumption. Other profiles are optional unless a manifest declares them required.

### 6.19 Core profile

The minimum interoperable semantic handoff profile. It includes actors, authority, goals, constraints, claims, evidence, decisions, plans, tasks, questions, artifacts, executions, changes, risks, checkpoints, sessions, and handoffs.

### 6.20 Coordination profile

An optional, experimental profile for concurrent work intents, semantic scopes, leases, interface contracts, change sets, coordination conflicts, and integration plans. A core reader may preserve but otherwise ignore this profile unless the manifest declares it required.

---

## 7. Conceptual model

AWP separates work into five layers:

```text
Human briefing    required root Markdown entry point
Semantic state    goals, claims, decisions, plans, tasks, checkpoints
Event ledger      immutable observations and state transitions
Artifacts         files, patches, datasets, outputs, external references
Extensions        coordination, A2A, MCP, workflow, model, and domain-specific state
```

The root Markdown briefing is the canonical human orientation layer. The event ledger remains the authoritative state history, and a snapshot is an optimized projection of that history. Statements in the Markdown briefing should link to stable record IDs; if prose conflicts with typed state, conforming readers must surface the inconsistency and use the event-derived state for machine decisions. Other human views are non-authoritative derivatives. Artifacts may be embedded, colocated, or externally referenced. Extensions must not alter the meaning of portable-core fields.

The core profile defines the portable interoperability floor. Optional profiles add capabilities without increasing the requirements for a core reader or writer. A manifest MUST identify every profile it uses and whether that profile is required or optional.

---

## 8. Representations

AWP defines one logical model with four transport forms.

### 8.1 Editable directory

The recommended active-work representation is a directory ending in `.workstate`:

```text
example.workstate/
  WORK.md
  manifest.json
  events.jsonl
  snapshot.json
  artifacts/
    sha256/
      7d/
        7d8c...bin
  extensions/
  views/
    timeline.md
```

Requirements:

- `WORK.md` is REQUIRED and is the first document a human-facing reader SHOULD present.
- `manifest.json` is REQUIRED.
- `events.jsonl` is REQUIRED except for a deliberately snapshot-only export.
- `snapshot.json` is RECOMMENDED.
- `artifacts/`, `extensions/`, and `views/` are OPTIONAL.
- Each line of `events.jsonl` MUST contain exactly one complete JSON event object.
- Files in `views/` MUST NOT be treated as authoritative state.

#### 8.1.1 Root Markdown briefing

`WORK.md` MUST be valid CommonMark-compatible Markdown and MUST begin with a compact metadata block:

```markdown
---
awp_version: 0.3.0
workstate_id: urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727
frontier:
  - evt_01K4M4VYB9...
checkpoint: checkpoint:release-ready
generated_at: 2026-09-03T20:15:00Z
generated_digest: sha256:8b91b4b4aacf71e02a7b37e14fdc720a884f94b9eed7192611f41deb759a0579
---

<!-- awp:generated:start -->
# Prepare product launch

Implementation and local verification are complete. Production approval remains outstanding.

## Active work

- Agent A is updating the authentication callback.
- Agent B is updating session tests against interface contract `contract:session-v2`.

## Next action

Request production deployment approval.
<!-- awp:generated:end -->

<!-- awp:notes:start -->
Human notes may be edited here. They are not machine state until imported as proposed events.
<!-- awp:notes:end -->
```

The body SHOULD contain, in this order where applicable:

1. title and plain-language purpose;
2. current status and checkpoint summary;
3. active participants and concurrent work intents;
4. goals and success criteria;
5. constraints, authority boundaries, and safety warnings;
6. accepted decisions and verified facts;
7. changes completed since the prior checkpoint;
8. active tasks, overlaps, conflicts, and blockers;
9. artifact and evidence links;
10. recommended next action.

The metadata block binds the briefing to a specific event frontier. Generated content MUST be enclosed by exactly one `awp:generated` marker pair. `generated_digest` MUST use the form `sha256:{lowercase-hex}` and cover the UTF-8 content beginning after the LF that terminates the start-marker line and ending before the LF that precedes the end-marker line, after normalizing CRLF to LF. A reader MUST report the briefing as modified or stale when the digest does not match, when the declared frontier differs from the effective snapshot frontier, or when either generated marker is missing or duplicated.

Human-authored content SHOULD be enclosed in `awp:notes` markers. It is non-authoritative. Content outside the generated region is also non-authoritative. An implementation that offers to import an edit affecting machine state MUST show the proposed semantic changes to the user or authorized actor and record accepted changes as ordinary typed events. It MUST NOT silently convert edited prose into authoritative state.

### 8.2 Single-file Markdown capsule

The recommended exchange representation is a self-contained file ending in `.awp.md`:

```text
project.awp.md
```

It MUST begin with a human-readable Markdown briefing. It MUST then contain enough machine-readable material to support the declared `completeness` level. The canonical section order is:

1. YAML-like front matter;
2. Markdown briefing;
3. `manifest` block;
4. `snapshot` block;
5. `events` block, when history is included;
6. `records` block, when records are not fully represented by the snapshot;
7. `artifacts` block or artifact references;
8. `extensions` block;
9. optional generated views or human notes.

The front matter MUST declare a `capsule_boundary` containing at least 128 bits of unpredictable entropy encoded as lowercase hexadecimal. Machine sections MUST be delimited by boundary-qualified AWP markers. A marker is recognized only when it occupies a complete line. An end marker exactly matches `<!-- awp:{capsule_boundary}:{section}:end -->`; a start marker may additionally contain space-separated quoted attributes before ` -->`.

````markdown
---
awp_version: 0.3.0
capsule_boundary: 7d8c9f2ae43b1c8066a71a5d93470e11
---

<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:manifest:start -->
```json
{"awp_version":"0.3.0","workstate_id":"urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727","title":"Prepare product launch","created_at":"2026-09-03T18:00:00Z","created_by":"actor:mark","completeness":"portable","profiles":{"core":"required"},"representations":{"briefing":"#briefing","snapshot":"section:snapshot"},"format":"single-file-capsule"}
```
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:manifest:end -->
````

The content inside a machine section MUST be valid according to that section's declared encoding. JSON Lines is RECOMMENDED for event blocks. The boundary token MUST NOT appear in any enclosed decoded text. If it would appear, the writer MUST generate a new non-colliding boundary or use a binary-safe encoding such as base64 for that content. Implementations MUST NOT infer machine state from arbitrary prose, headings, or code examples outside marked sections.

The file MUST declare a `completeness` value:

- `summary`: briefing and checkpoint only;
- `portable`: all core semantic state, relevant evidence, data required by declared profiles, and required artifacts or stable references;
- `full`: portable state plus complete event history, included transcripts, tool outputs, and runtime extensions.

`portable` is the default for a handoff. A file claiming `portable` MUST identify every required artifact or explicitly mark it unavailable. A file claiming `full` MUST identify omitted content, if any, rather than implying that the capsule contains an entire repository or complete transcript when it does not.

#### 8.2.1 Embedded artifacts

Small text artifacts MAY be embedded as UTF-8 content. Binary artifacts and exact source files SHOULD be encoded as base64. Content containing the active capsule boundary MUST be encoded as base64 or written with a new non-colliding boundary:

```markdown
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:artifact:start id="artifact:logo" encoding="base64" media_type="image/png" -->
iVBORw0KGgoAAAANSUhEUgAA...
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:artifact:end -->
```

Each embedded artifact MUST have a descriptor and digest. An artifact reference MAY point to an external URI, repository revision, or package member, but a capsule intended to be self-contained SHOULD embed all material required for its declared next action.

#### 8.2.2 Parsing and lossless handling

A single-file reader MUST parse the front matter and Markdown briefing before machine sections, validate the boundary syntax and marker pairing, reject ambiguous duplicate authoritative sections, and preserve unknown sections when rewriting. It MUST reject a capsule when the declared boundary is absent, malformed, reused inconsistently, or present in decoded section content. It MUST treat prose and embedded artifact content as untrusted data.

When a capsule is updated, the writer SHOULD append new events within the events block and refresh the snapshot and front-matter frontier. It MUST NOT silently replace historical events with a summary while retaining a `full` completeness claim.

#### 8.2.3 Single-file coordination

A `.awp.md` capsule MAY contain active intents, leases, contracts, change sets, and conflicts. This makes it suitable for sending a complete coordination snapshot to another engine. A shared service or synchronized repository is still required for real-time lease enforcement; a sent file is a portable record of coordination, not a live lock server.

### 8.3 Packaged file

A packaged workstate SHOULD use the `.pws` extension. It is a ZIP-compatible archive whose root layout matches the editable directory.

The proposed media type is:

```text
application/awp+zip
```

This media type is provisional until registered with the appropriate authority.

Packaging MUST be reversible: unpacking a `.pws` file must recover the same logical paths, bytes, identities, and references as the original directory.

A package viewer SHOULD display `WORK.md` by default. The physical ZIP member order is not semantically significant, but writers SHOULD place `WORK.md` and `manifest.json` before large artifacts to support efficient preview.

### 8.4 Wire representation

AWP messages may carry a complete snapshot, an event sequence, a delta, an artifact announcement, or a retrieval request.

Proposed media types:

```text
application/awp+json
application/awp-delta+json
application/awp-event+json
```

Wire bindings may be transported through HTTP, A2A, MCP resources, message queues, local IPC, or other protocols. AWP specifies payload semantics and does not require a particular transport.

---

## 9. Identity, ordering, and time

### 9.1 Workstate identity

Every workstate MUST have a globally unique `workstate_id`. Implementations SHOULD use a UUID, URI, or another collision-resistant identifier.

```json
{
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727"
}
```

Copying a workstate does not create a new identity. Forking creates a new workstate identity and records the parent frontier.

### 9.2 Record and event identity

Each record and event MUST have an identifier unique within its workstate. Identifiers SHOULD remain stable across packaging, synchronization, and rendering.

### 9.3 Ordering

Event order MUST NOT depend solely on wall-clock timestamps. An event MUST identify its direct logical parents using `parents`. A single-writer implementation may additionally use a monotonic `sequence` number.

```json
{
  "event_id": "evt_01K4M4VYB9...",
  "parents": ["evt_01K4M4TWM2..."],
  "sequence": 42,
  "occurred_at": "2026-09-03T20:14:31Z"
}
```

Multiple parent identifiers represent a merge event. Multiple events sharing the same parent represent concurrent branches.

### 9.4 Event frontier

A frontier is the set of event IDs with no known descendants in a particular replica. Checkpoints and deltas SHOULD declare the frontier from which they were derived.

---

## 10. Manifest

`manifest.json` identifies the workstate and declares capabilities necessary to interpret it.

### 10.1 Required manifest fields

```json
{
  "awp_version": "0.3.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "title": "Prepare product launch",
  "created_at": "2026-09-03T18:00:00Z",
  "created_by": "actor:mark",
  "completeness": "portable",
  "profiles": {
    "core": "required",
    "coordination": "optional"
  },
  "default_language": "en",
  "representations": {
    "briefing": "WORK.md",
    "events": "events.jsonl",
    "snapshot": "snapshot.json"
  },
  "extensions": [],
  "security": {
    "classification": "private",
    "contains_secrets": false,
    "secret_scan": {
      "status": "passed",
      "scanned_at": "2026-09-03T20:14:00Z",
      "policy": "org.example/default-export"
    }
  },
  "coordination": {
    "status": "experimental",
    "lease_enforcement": "advisory"
  }
}
```

Required fields are:

- `awp_version`
- `workstate_id`
- `title`
- `created_at`
- `created_by`
- `completeness`
- `profiles`
- `representations`

`profiles` MUST contain `"core": "required"`. Each additional profile is declared `required` or `optional`. A reader that does not support a required profile MUST refuse semantic processing but SHOULD still present the briefing and preserve the workstate losslessly.

### 10.2 Optional manifest fields

The manifest MAY include:

- description;
- default language;
- originating application;
- declared extensions;
- artifact roots;
- signature information;
- encryption metadata;
- retention policy;
- classification;
- parent workstate and fork frontier;
- minimum required reader capabilities.

When the coordination profile is present, the manifest MUST declare `coordination.lease_enforcement` as either `advisory` or `enforced`. `enforced` means an identified live coordinator guarantees the stated exclusivity within its declared scope; absence or unavailability of that coordinator causes leases to be treated as advisory. A file alone can never establish enforced lease state.

---

## 11. Common event envelope

Every event MUST contain the following envelope:

```json
{
  "event_schema_version": "0.1",
  "kind": "claim.observed",
  "event_id": "evt_01K4M4VYB9...",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "parents": ["evt_01K4M4TWM2..."],
  "occurred_at": "2026-09-03T20:14:31Z",
  "recorded_at": "2026-09-03T20:14:33Z",
  "actor": "actor:agent-7",
  "payload": {},
  "extensions": {}
}
```

### 11.1 Required event fields

- `event_schema_version`: major and minor version of the common event envelope.
- `kind`: registered event type or namespaced extension type.
- `event_id`: stable event identifier.
- `workstate_id`: containing workstate identifier.
- `parents`: logical predecessor events; empty only for a genesis event.
- `occurred_at`: when the represented occurrence happened.
- `actor`: actor responsible for the occurrence or assertion.
- `payload`: event-specific data.

### 11.2 Optional event fields

- `recorded_at`: when the event entered the ledger.
- `sequence`: single-writer monotonic order.
- `correlation_id`: links events belonging to one operation.
- `causation_id`: event or request that caused this event.
- `session_id`: session in which the event occurred.
- `scope`: commit, artifact version, environment, or temporal scope.
- `authority`: authorization basis for the event.
- `trust`: origin and verification metadata.
- `extensions`: namespaced extension data.
- `signature`: detached or embedded signature metadata.

Unknown event fields MUST be preserved by lossless processors.

---

## 12. Actors and authority

An actor record describes the source of an observation or change.

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

Actor types include:

- `human`
- `agent`
- `model`
- `service`
- `automation`
- `organization`
- `unknown`

Actor identity and authority are separate. A known actor does not automatically possess permission to perform an action.

An authority declaration SHOULD identify:

- the authorizing actor;
- the allowed action or scope;
- any conditions or expiration;
- the event in which authorization was granted;
- whether further confirmation is required.

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

A receiving system MUST apply its own security policy. Imported authority is evidence of authorization, not an instruction to bypass local policy.

---

## 13. Record types

Sections 13.1 through 13.14 define the core-profile record types. A portable handoff need include only the records relevant to its checkpoint; it does not need to instantiate every type. Sections 13.15 through 13.20 define coordination-profile record types and are optional unless the manifest declares the coordination profile required.

### 13.1 Goal

A goal describes a desired outcome.

```json
{
  "id": "goal:launch",
  "type": "goal",
  "statement": "Prepare the application for public launch.",
  "status": "active",
  "priority": "high",
  "success_criteria": [
    "Critical tests pass",
    "Production deployment is approved",
    "Rollback procedure is documented"
  ],
  "parent": null
}
```

Goal statuses are `proposed`, `active`, `satisfied`, `abandoned`, `blocked`, and `superseded`.

### 13.2 Constraint

A constraint limits acceptable work or actions.

```json
{
  "id": "constraint:no-schema-change",
  "type": "constraint",
  "statement": "Do not modify the production database schema without approval.",
  "source": "actor:mark",
  "strength": "required",
  "scope": ["environment:production"],
  "status": "active"
}
```

Constraint strengths are `required`, `preferred`, and `advisory`.

### 13.3 Claim

A claim represents an assertion about the world or the work.

```json
{
  "id": "claim:tests-pass",
  "type": "claim",
  "statement": "The unit test suite passes on Windows.",
  "epistemic_status": "verified",
  "confidence": 1.0,
  "evidence": ["evidence:test-run-842"],
  "scope": {
    "source_revision": "git:91ab4e7",
    "environment": "env:windows-ci"
  },
  "valid_at": "2026-09-03T20:02:00Z"
}
```

Core epistemic statuses are:

- `reported`: attributed to a source but not independently checked;
- `inferred`: concluded from other information;
- `observed`: directly inspected or measured;
- `verified`: checked using identified evidence or a repeatable procedure;
- `disputed`: subject to an unresolved contradiction;
- `unknown`: explicitly not known;
- `stale`: potentially invalid because its scope or evidence changed;
- `refuted`: contradicted by stronger evidence;
- `superseded`: replaced by a newer claim.

Confidence MUST NOT substitute for epistemic status. A highly confident inference is still an inference.

### 13.4 Evidence

Evidence connects claims and decisions to inspectable material.

```json
{
  "id": "evidence:test-run-842",
  "type": "evidence",
  "evidence_type": "execution_result",
  "supports": ["claim:tests-pass"],
  "artifact": "artifact:test-output-842",
  "procedure": "command:npm-test",
  "observed_by": "actor:agent-7",
  "integrity": {
    "algorithm": "sha256",
    "digest": "4df6..."
  }
}
```

Evidence may support, contradict, or merely contextualize a claim. A source reference without retrievable content SHOULD be marked as unavailable or unverified.

### 13.5 Decision

A decision records a resolved or pending choice.

```json
{
  "id": "decision:database",
  "type": "decision",
  "question": "Which database should the service use?",
  "status": "accepted",
  "choice": "PostgreSQL",
  "rationale": "It satisfies transactional and operational requirements.",
  "alternatives": [
    {
      "choice": "SQLite",
      "disposition": "rejected",
      "reason": "The expected deployment requires concurrent writers."
    }
  ],
  "decided_by": "actor:mark",
  "evidence": ["evidence:load-test"]
}
```

Decision statuses are `proposed`, `accepted`, `rejected`, `deferred`, `reopened`, and `superseded`.

Rationale SHOULD be a concise decision explanation. It MUST NOT require disclosure of private chain-of-thought.

### 13.6 Plan

A plan organizes intended work without claiming it has occurred.

```json
{
  "id": "plan:release",
  "type": "plan",
  "goal": "goal:launch",
  "status": "active",
  "steps": ["task:test", "task:review", "task:deploy"],
  "strategy": "Verify locally, obtain approval, then deploy with rollback ready."
}
```

### 13.7 Task

A task is an actionable unit of work.

```json
{
  "id": "task:deploy",
  "type": "task",
  "title": "Deploy the release",
  "status": "blocked",
  "depends_on": ["task:test", "task:review"],
  "blocked_by": ["question:production-approval"],
  "assigned_to": "actor:agent-7",
  "side_effect_class": "external_write",
  "required_authority": ["auth:deploy-production"]
}
```

Task statuses are `proposed`, `ready`, `in_progress`, `input_required`, `blocked`, `completed`, `failed`, `cancelled`, and `superseded`.

### 13.8 Question

A question records missing information or a decision requiring input.

```json
{
  "id": "question:production-approval",
  "type": "question",
  "text": "Has the production deployment been approved?",
  "status": "open",
  "owner": "actor:mark",
  "blocking": true,
  "blocks": ["task:deploy"]
}
```

Question statuses are `open`, `answered`, `withdrawn`, and `superseded`.

### 13.9 Artifact descriptor

An artifact descriptor identifies concrete material without necessarily embedding it.

```json
{
  "id": "artifact:release-plan",
  "type": "artifact",
  "name": "release-plan.md",
  "role": "deliverable",
  "media_type": "text/markdown",
  "size": 4832,
  "integrity": {
    "algorithm": "sha256",
    "digest": "7d8c..."
  },
  "locations": [
    {
      "kind": "package",
      "path": "artifacts/sha256/7d/7d8c...bin"
    }
  ],
  "trust": "authored",
  "instructional_content": true
}
```

Core artifact location kinds and their fields are:

| `kind` | Required fields | Optional fields |
|---|---|---|
| `embedded` | `section_id` | `encoding` |
| `package` | `path` | none |
| `local` | `path` | `absolute` |
| `remote` | `uri` | `expires_at`, `retrieval_requirements` |
| `repository_relative` | `repository`, `revision`, `path` | `submodule_revision` |
| `unavailable` | `reason` | `last_known_location` |

Package paths MUST be relative and traversal-safe. Secrets such as authorization headers MUST NOT appear in locations; a remote location may identify a separately authorized retrieval requirement. Private location kinds MUST be namespaced.

### 13.10 Execution

An execution record describes an attempted operation and its result.

```json
{
  "id": "execution:test-842",
  "type": "execution",
  "operation": "Run unit tests",
  "tool": "command:npm-test",
  "started_at": "2026-09-03T20:01:11Z",
  "ended_at": "2026-09-03T20:02:03Z",
  "status": "succeeded",
  "exit_code": 0,
  "inputs": ["artifact:source-tree-91ab"],
  "outputs": ["artifact:test-output-842"],
  "side_effects": []
}
```

Execution records SHOULD redact secrets and SHOULD capture enough environment information to interpret the result.

### 13.11 Change

A change relates semantic work to modified artifacts.

```json
{
  "id": "change:auth-route",
  "type": "change",
  "summary": "Added the OAuth callback route.",
  "artifacts": [
    {
      "logical_path": "src/auth/callback.ts",
      "before": null,
      "after": "artifact:callback-v1"
    }
  ],
  "implements": ["task:add-oauth"],
  "verification": ["execution:test-842"]
}
```

### 13.12 Risk

A risk identifies a possible adverse outcome.

```json
{
  "id": "risk:migration-lock",
  "type": "risk",
  "statement": "The migration may lock a heavily used table.",
  "likelihood": "medium",
  "impact": "high",
  "status": "open",
  "mitigations": ["task:test-migration-copy"]
}
```

### 13.13 Checkpoint

A checkpoint is the preferred resumption entry point.

```json
{
  "id": "checkpoint:release-ready",
  "type": "checkpoint",
  "frontier": ["evt_01K4M4VYB9..."],
  "created_at": "2026-09-03T20:14:31Z",
  "summary": "Implementation and local verification are complete. Production approval remains outstanding.",
  "active_goals": ["goal:launch"],
  "completed_since_previous": ["task:test", "task:review"],
  "open_tasks": ["task:deploy"],
  "open_questions": ["question:production-approval"],
  "active_constraints": ["constraint:no-schema-change"],
  "risks": ["risk:migration-lock"],
  "recommended_next_action": {
    "action": "Request production deployment approval from the user.",
    "requires_authority": false
  },
  "resumption_level": "semantic"
}
```

Checkpoint summaries are conveniences and MUST NOT silently override the underlying records or event history.

### 13.14 Session

A session groups activity occurring within a bounded interaction or execution period.

```json
{
  "id": "session:2026-09-03-a",
  "type": "session",
  "started_at": "2026-09-03T18:00:00Z",
  "ended_at": "2026-09-03T20:15:00Z",
  "participants": ["actor:mark", "actor:agent-7"],
  "summary": "Implemented and verified authentication changes.",
  "transcript": null
}
```

Full transcripts are OPTIONAL. A workstate SHOULD remain useful without them.

### 13.15 Work intent

The remaining Section 13 record types belong to the experimental coordination profile.

A work intent advertises planned work before implementation begins.

```json
{
  "id": "intent:agent-a-auth-refresh",
  "type": "work_intent",
  "actor": "actor:agent-a",
  "goal": "goal:oauth-refresh",
  "summary": "Change refresh-token rotation and its persistence path.",
  "status": "active",
  "base_revision": "git:91ab4e7",
  "scopes": [
    {
      "kind": "symbol",
      "repository": "repo:application",
      "path": "src/auth/session.ts",
      "symbol": "rotateRefreshToken",
      "access": "write"
    },
    {
      "kind": "interface",
      "id": "contract:session-store-v2",
      "access": "propose_change"
    }
  ],
  "expected_effects": [
    "Refresh tokens become single-use",
    "Session-store writes gain a generation precondition"
  ],
  "preserved_invariants": ["invariant:no-plaintext-token-storage"],
  "dependencies": ["intent:agent-b-session-store"],
  "lease": "lease:auth-refresh",
  "expected_completion": "2026-09-03T22:00:00Z"
}
```

Intent statuses are `proposed`, `active`, `waiting`, `completed`, `withdrawn`, and `superseded`.

### 13.16 Coordination scope

A coordination scope identifies the region in which work may overlap.

```json
{
  "id": "scope:session-rotation",
  "type": "coordination_scope",
  "kind": "symbol",
  "repository": "repo:application",
  "base_revision": "git:91ab4e7",
  "path": "src/auth/session.ts",
  "language": "typescript",
  "symbol": "rotateRefreshToken",
  "semantic_effects": ["writes:session.refresh_generation"],
  "related_contracts": ["contract:session-store-v2"]
}
```

Core scope kinds are `repository`, `directory`, `file`, `region`, `symbol`, `interface`, `schema`, `test`, `behavior`, `invariant`, `configuration`, and `deployment_surface`. Symbol and semantic scopes SHOULD be preferred over unstable line-number ranges.

### 13.17 Coordination lease

A lease makes temporary coordination expectations explicit.

```json
{
  "id": "lease:auth-refresh",
  "type": "coordination_lease",
  "holder": "actor:agent-a",
  "scopes": ["scope:session-rotation"],
  "mode": "exclusive_write",
  "status": "granted",
  "granted_by": "actor:coordinator",
  "granted_at": "2026-09-03T20:30:00Z",
  "expires_at": "2026-09-03T21:00:00Z",
  "renewable": true,
  "on_conflict": "negotiate"
}
```

Lease modes are `advisory`, `shared_read`, `shared_write`, `exclusive_write`, and `integration_owner`. Leases coordinate actors but do not replace repository permissions, filesystem controls, or human authorization.

### 13.18 Interface contract

An interface contract lets agents agree on a boundary before independently modifying its producers and consumers.

```json
{
  "id": "contract:session-store-v2",
  "type": "interface_contract",
  "revision": 2,
  "status": "accepted",
  "owners": ["actor:agent-a", "actor:agent-b"],
  "producers": ["scope:session-rotation"],
  "consumers": ["scope:session-tests"],
  "definition": {
    "operation": "storeSession",
    "inputs": ["session", "expectedGeneration"],
    "outcomes": ["stored", "generation_conflict"]
  },
  "compatibility": "breaking",
  "verification": ["test:session-contract-v2"]
}
```

Contract statuses are `proposed`, `negotiating`, `accepted`, `implemented`, `verified`, `deprecated`, and `superseded`.

### 13.19 Change set

A change set groups code changes with their semantic intent and safe-application conditions.

```json
{
  "id": "changeset:auth-refresh-v1",
  "type": "change_set",
  "author": "actor:agent-a",
  "intent": "intent:agent-a-auth-refresh",
  "status": "proposed",
  "base_revision": "git:91ab4e7",
  "touches": ["scope:session-rotation"],
  "implements_contracts": ["contract:session-store-v2@2"],
  "preconditions": [
    {"kind": "artifact_digest", "path": "src/auth/session.ts", "sha256": "7d8c..."},
    {"kind": "contract_revision", "contract": "contract:session-store-v2", "revision": 2},
    {"kind": "invariant", "id": "invariant:no-plaintext-token-storage", "state": "satisfied"}
  ],
  "patch": "artifact:auth-refresh-patch-v1",
  "expected_effects": ["writes:session.refresh_generation"],
  "verification": ["execution:auth-tests-914"],
  "integration_dependencies": ["changeset:session-store-v2"],
  "conflicts": []
}
```

Change-set statuses are `draft`, `proposed`, `accepted`, `stale`, `rebasing`, `ready`, `integrating`, `integrated`, `rejected`, and `superseded`.

### 13.20 Coordination conflict

A coordination conflict represents potential or actual interference between intents, contracts, or change sets.

```json
{
  "id": "conflict:refresh-generation",
  "type": "coordination_conflict",
  "status": "open",
  "severity": "blocking",
  "conflict_kind": "incompatible_contract",
  "participants": ["actor:agent-a", "actor:agent-b"],
  "subjects": ["changeset:auth-refresh-v1", "changeset:session-store-v1"],
  "scopes": ["contract:session-store-v2"],
  "explanation": "The producer writes generation 2 while the consumer still assumes generation 1.",
  "resolution_owner": "actor:coordinator"
}
```

Conflict statuses are `potential`, `open`, `negotiating`, `resolved`, `accepted_risk`, and `superseded`.

---

## 14. Record lifecycle events

Core lifecycle events use a consistent vocabulary:

- `<type>.created`
- `<type>.updated`
- `<type>.status_changed`
- `<type>.superseded`
- `<type>.deleted`

Deletion events are tombstones. They do not erase historical events. Sensitive-data removal may require a separate redaction process described in Section 26.

An update event SHOULD contain a patch or complete replacement plus the prior record revision:

```json
{
  "kind": "task.status_changed",
  "payload": {
    "record_id": "task:test",
    "from": "in_progress",
    "to": "completed",
    "reason": "All configured test suites passed.",
    "evidence": ["evidence:test-run-842"]
  }
}
```

State transitions that claim completion, verification, authorization, or external side effects SHOULD include evidence.

---

## 15. Epistemic integrity

AWP readers must not treat all text as equally authoritative.

### 15.1 Claim typing

Every material assertion SHOULD be encoded as a claim with:

- epistemic status;
- provenance;
- confidence where meaningful;
- evidence or explicit lack of evidence;
- scope and validity time;
- links to contradicting or superseding claims.

### 15.2 Scope

A claim may be true only for a particular:

- source revision;
- artifact digest;
- environment;
- time interval;
- dataset version;
- model and configuration;
- jurisdiction;
- user or tenant.

Readers SHOULD mark claims stale when referenced scope no longer matches current state.

### 15.3 Contradiction

Contradictory claims MUST be preserved until resolved. A merger MUST NOT choose a winner solely by timestamp. Resolution should consider evidence, scope, authority, and explicit human decisions.

### 15.4 Derived summaries

Summaries SHOULD link to the records they summarize. A summary is not independent evidence.

---

## 16. Artifact model

### 16.1 Storage modes

Artifacts may be:

- **embedded:** bytes included in a record, suitable only for small content;
- **packaged:** stored inside the `.workstate` directory or `.pws` package;
- **local:** referenced by a logical or absolute local path;
- **remote:** referenced by a URI;
- **repository-relative:** referenced by repository identifier, revision, and path;
- **unavailable:** described but intentionally omitted.

### 16.2 Integrity

Packaged artifacts MUST include a digest. Remote and repository-relative artifacts SHOULD include a digest when stable bytes are expected.

### 16.3 Logical identity and versions

An artifact's logical name is distinct from its immutable content version. Two versions of `src/auth.ts` should have separate content digests while sharing a logical path.

### 16.4 Mutability

Content-addressed packaged artifacts are immutable. Modification creates a new artifact descriptor and a change relationship.

### 16.5 Executable and instructional artifacts

Artifact descriptors MUST indicate when content is executable or may contain instructions. Receiving systems MUST treat instructions inside untrusted artifacts as data unless separately authorized.

---

## 17. Plans, dependencies, and side effects

AWP distinguishes intention from execution:

- a plan says what is intended;
- a task says what may be performed;
- authority says what is permitted;
- an execution says what was attempted;
- evidence says what was observed;
- a change says what artifacts were modified;
- a claim says what is believed to be true.

These distinctions prevent a receiving agent from treating a proposed action as completed or an unauthorised instruction as executable.

Tasks SHOULD declare a side-effect class:

- `read_only`
- `local_write`
- `external_write`
- `third_party_api_call`
- `data_migration`
- `communication`
- `financial`
- `security_sensitive`
- `destructive`
- `unknown`

Local policy may impose additional confirmation requirements based on this classification.

---

## 18. Resumption levels

A checkpoint declares the strongest supported resumption level.

Resumption levels are cumulative: `operational` MUST also satisfy every `semantic` requirement, and `exact` MUST also satisfy every `operational` and `semantic` requirement unless the workstate is explicitly labeled as a non-portable private runtime checkpoint.

### 18.1 Semantic resumption

`semantic` means a different capable LLM or human can understand the work and continue it using the portable core.

Required information:

- active goal;
- current status;
- applicable constraints;
- important claims and evidence;
- active decisions;
- open tasks and questions;
- artifact references;
- recommended next action.

### 18.2 Operational resumption

`operational` means a compatible agent can also restore tool context, pending actions, environment references, and workflow position without reconstructing them manually.

Operational resumption SHOULD identify unavailable tools and external dependencies rather than assuming they exist.

### 18.3 Exact runtime resumption

`exact` means the originating runtime claims it can restore its private checkpoint through a declared extension. This guarantee applies only to the identified runtime and version.

AWP itself does not guarantee deterministic output or identical model behavior.

---

## 19. Handoff profile

A handoff is a checkpoint optimized for transfer to another actor.

```json
{
  "type": "handoff",
  "id": "handoff:agent-b",
  "checkpoint": "checkpoint:release-ready",
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
  "requested_action": "Continue release preparation without deploying.",
  "authority_ceiling": ["read_only", "local_write"]
}
```

A receiving agent SHOULD:

1. validate the package and supported version;
2. inspect security and trust declarations;
3. read the latest checkpoint;
4. load referenced goals, constraints, decisions, claims, and tasks;
5. verify availability and integrity of required artifacts;
6. compare requested actions with local authority;
7. identify unsupported extensions or missing dependencies;
8. record acceptance, rejection, or qualified acceptance of the handoff.

---

## 20. Delta exchange

A delta contains events added after a known frontier.

```json
{
  "awp_version": "0.3.0",
  "kind": "workstate.delta",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "base_frontier": ["evt_01K4M4TWM2..."],
  "result_frontier": ["evt_01K4M4VYB9..."],
  "events": [
    {
      "kind": "task.status_changed",
      "event_id": "evt_01K4M4VYB9...",
      "parents": ["evt_01K4M4TWM2..."],
      "occurred_at": "2026-09-03T20:14:31Z",
      "actor": "actor:agent-7",
      "payload": {
        "record_id": "task:test",
        "from": "in_progress",
        "to": "completed"
      }
    }
  ],
  "artifacts": []
}
```

A receiver MUST verify that:

- the workstate identity matches;
- all required parent events are already present or included;
- event identifiers have not been reused with different content;
- included artifact digests match their bytes;
- the delta does not claim unsupported authority.

An event ID collision with different content is an integrity error.

---

## 21. Branching, merging, and conflicts

### 21.1 Forking

A fork creates a new `workstate_id` and records:

- the parent workstate;
- the parent frontier;
- the reason for the fork;
- the actor creating it.

### 21.2 Same-workstate concurrency

Multiple agents may append events concurrently to the same workstate. Concurrent events form branches in the event DAG.

### 21.3 Mechanical merge

Events with unique IDs and satisfied parents may be combined mechanically. Combining events does not guarantee semantic consistency.

### 21.4 Semantic conflicts

Conflicts include:

- incompatible accepted decisions;
- inconsistent task status transitions;
- concurrent modification of the same logical artifact;
- contradictory verified claims;
- incompatible authority changes;
- deletion of a record concurrently used by another event.

Semantic conflicts MUST be surfaced as explicit conflict records. They MUST NOT be silently resolved using last-write-wins.

```json
{
  "id": "conflict:database-choice",
  "type": "conflict",
  "status": "open",
  "subjects": ["decision:database"],
  "events": ["evt:choose-postgres", "evt:choose-mysql"],
  "resolution_required_from": "actor:mark"
}
```

### 21.5 Resolution

Conflict resolution is represented by a new event with all conflicting tips as parents. History remains intact.

---

## 22. Multi-agent code coordination

**Profile status:** Optional and experimental. Section 22 is normative only for implementations claiming the coordination profile. It does not add requirements to core-profile conformance, and coordination records may evolve on a separate compatibility track before AWP 1.0.

AWP coordination operates above byte-level source control. Git or another version-control system remains responsible for storing revisions, commits, and patches. AWP records what agents intend to change, which semantic boundaries are shared, what must remain true, how changes depend on each other, and under which conditions an integration remains valid.

A file or asynchronous message carries only an observation of coordination state. Real-time exclusion requires an available coordinator identified by the manifest. In offline or decentralized use, leases are advisory and conflicts may be discovered only during synchronization or integration.

The coordination model is designed to prevent three common failures:

1. **Physical clobbering:** two agents overwrite the same bytes or apply a patch to an unexpected base.
2. **Semantic clobbering:** changes merge cleanly as text but violate each other's assumptions, interfaces, or invariants.
3. **Coordination loss:** one agent makes a decision or interface change that another agent does not learn about until integration.

### 22.1 Coordination principles

Conforming coordination implementations follow these principles:

- Agents announce write intent before materially changing shared code.
- Scopes describe symbols, contracts, behaviors, and invariants in addition to paths.
- Coordination leases are time-bounded and do not imply security authority.
- Change sets carry explicit base revisions and application preconditions.
- Textually disjoint changes may still conflict semantically.
- Textually overlapping changes may be compatible after negotiation.
- Interface changes are contracts that producers and consumers can accept before implementation.
- Stale work is rebased and revalidated rather than blindly applied.
- Integration is an explicit protocol phase with an identified owner and result.
- Git commits are evidence and delivery artifacts, not the complete coordination model.

### 22.2 Scope addressing

An agent SHOULD declare every scope it reasonably expects to read, write, create, delete, or semantically affect. A scope contains an access mode and may include both physical and semantic selectors.

Physical selectors include:

- repository and base revision;
- directory or file path;
- syntax-tree or symbol identity;
- generated file or configuration key;
- database schema object;
- test suite or fixture.

Semantic selectors include:

- public interface or protocol contract;
- behavior being introduced or changed;
- invariant that must be preserved;
- state field read or written;
- error or lifecycle semantics;
- performance, security, or compatibility property;
- deployment surface affected.

Line ranges SHOULD be used only as hints because concurrent edits make them unstable. Implementations MAY use language-server symbols, syntax-tree fingerprints, stable code IDs, schema paths, or repository-specific selectors.

### 22.3 Access modes

Each intended scope access SHOULD be classified as:

- `observe`: inspect without relying on stability;
- `read`: read and rely on the declared base state;
- `write`: modify existing semantics or bytes;
- `create`: introduce a new artifact, symbol, or interface;
- `delete`: remove an artifact, symbol, or behavior;
- `propose_change`: negotiate a shared contract without yet implementing it;
- `integrate`: combine accepted change sets;
- `verify`: test or validate a scope.

An overlap detector considers access mode as well as scope. Two reads normally do not conflict. A write and a relied-upon read may conflict even if the reader does not modify the scope.

### 22.4 Work-intent announcement

Before editing shared code, an agent SHOULD append `coordination.intent_announced`. The event includes:

- goal and plain-language summary;
- actor and expected duration;
- base repository revision;
- expected physical and semantic scopes;
- interfaces expected to change;
- invariants expected to remain true;
- dependencies on other intents or decisions;
- proposed lease modes;
- expected outputs and verification.

If actual work expands beyond announced scopes, the agent SHOULD emit `coordination.intent_updated` before proceeding where practical.

### 22.5 Overlap discovery

A coordinator or peer agent compares new intent against active intents and accepted but unintegrated change sets. It SHOULD classify each overlap:

- `none`: no meaningful shared scope;
- `informational`: shared context with no expected interference;
- `compatible`: concurrent work is safe under stated contracts;
- `ordered`: both changes are valid but must integrate in a declared order;
- `negotiation_required`: agents must agree on an interface or ownership split;
- `blocking`: concurrent execution or integration is unsafe;
- `unknown`: the available scope information is insufficient.

Overlap detection SHOULD consider dependency graphs and semantic effects, not only path intersection. For example, an agent changing a database field and an agent changing a serializer may conflict without touching the same file.

```json
{
  "kind": "coordination.overlap_detected",
  "payload": {
    "left": "intent:agent-a-auth-refresh",
    "right": "intent:agent-b-session-store",
    "classification": "negotiation_required",
    "shared_scopes": ["contract:session-store-v2"],
    "reason": "Both intents change refresh-generation semantics."
  }
}
```

### 22.6 Leases and reservations

Leases provide coordination signals and optional enforcement:

- `advisory` announces activity but permits concurrent changes;
- `shared_read` promises that the relied-upon scope remains stable;
- `shared_write` permits coordinated writers under an accepted contract;
- `exclusive_write` asks other actors not to write the scope concurrently;
- `integration_owner` assigns responsibility for the combined result.

A lease MUST have a holder, scope, start time, expiration time, status, and conflict policy. Long-running agents SHOULD renew leases through heartbeat events. Expired leases MUST NOT remain silently active.

In `advisory` mode, all leases are non-binding coordination signals and conflicts are reconciled at synchronization or integration time. In `enforced` mode, the live coordinator identified by the manifest MUST reject lease operations that violate its declared conflict policy and scope. If that coordinator is unreachable, its current term or epoch cannot be verified, or its guarantee does not cover a scope, receivers MUST treat affected leases as advisory. Offline implementations MUST reconcile expired and concurrent work before integration.

A lease never grants permission to modify a repository or perform an external action. The actor still requires applicable authority.

### 22.7 Interface negotiation

When work crosses component boundaries, agents SHOULD agree on an interface contract before independently implementing producers and consumers.

The negotiation lifecycle is:

```text
proposed → negotiating → accepted → implemented → verified
                   ↘ superseded
```

Contract changes SHOULD declare:

- owners and affected producers and consumers;
- prior and proposed revisions;
- schemas, signatures, states, errors, and invariants;
- backward-compatibility classification;
- migration or feature-flag strategy;
- contract tests or verification procedures;
- adoption status for each participant.

An agent MUST NOT claim conformance to a contract revision it has not implemented or verified. Concurrent agents may implement against an accepted contract even before all change sets are integrated.

### 22.8 Change-set preconditions

Every concurrently produced change set SHOULD declare the state against which it was prepared. Preconditions may include:

- repository base revision;
- exact artifact digest;
- symbol or syntax-tree fingerprint;
- record revision;
- interface-contract revision;
- dependency change-set status;
- invariant status;
- absence or presence of a symbol;
- expected test baseline;
- toolchain or schema version.

Before applying or integrating a change set, an implementation MUST evaluate all required preconditions. A failed precondition marks the change set `stale`; it MUST NOT be blindly applied merely because the textual patch still applies.

This is a semantic compare-and-swap rule: apply the intended transformation only if the assumptions against which it was prepared still hold.

### 22.9 Semantic effect declarations

Change sets SHOULD declare expected effects using stable domain terms where possible:

```json
{
  "reads": ["session.refresh_generation"],
  "writes": ["session.refresh_generation"],
  "creates": ["error:generation_conflict"],
  "removes": [],
  "changes_behavior": ["refresh_token_rotation"],
  "preserves": ["invariant:no-plaintext-token-storage"],
  "contracts": ["contract:session-store-v2@2"]
}
```

These declarations allow coordination across files and languages. They are claims by the author and SHOULD be checked by static analysis, tests, review, or integration verification when risk warrants.

### 22.10 Change-set readiness

A change set becomes `ready` only when:

- its intent is still active or completed;
- required contracts are accepted;
- dependencies are ready or integrated as required;
- its base and other preconditions are current;
- blocking coordination conflicts are resolved;
- declared verification has passed;
- required review or authority is present.

Readiness does not mean the change has been integrated.

### 22.11 Integration plan

An integration plan describes how multiple ready change sets become one coherent result.

```json
{
  "id": "integration:session-v2",
  "type": "integration_plan",
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
  "verification": [
    "test:session-contract-v2",
    "test:auth-integration",
    "invariant:no-plaintext-token-storage"
  ],
  "rollback": "Revert the integration commit and restore contract revision 1."
}
```

The integration owner is responsible for checking preconditions, resolving the ordered base, executing combined verification, and publishing the integration result. Ownership does not authorize actions beyond existing permissions.

### 22.12 Integration result

An integration result SHOULD identify:

- input change sets and exact versions;
- integration base and resulting source revision;
- any transformations or manual conflict resolutions;
- contract revisions implemented;
- combined verification outcomes;
- unresolved risks or accepted deviations;
- resulting artifact digests;
- actor responsible for integration.

```json
{
  "kind": "coordination.integration_completed",
  "payload": {
    "plan": "integration:session-v2",
    "inputs": [
      "changeset:session-store-v2",
      "changeset:auth-refresh-v1",
      "changeset:session-tests-v2"
    ],
    "result_revision": "git:c84f2aa",
    "status": "verified",
    "verification": ["execution:combined-tests-1042"],
    "deviations": []
  }
}
```

### 22.13 Conflict resolution patterns

AWP supports several higher-level resolution strategies:

- **Scope partition:** agents divide responsibility by symbol, component, or behavior.
- **Contract first:** agents agree on a boundary, then implement independently.
- **Ordered integration:** one change establishes a base consumed by another.
- **Adapter introduction:** a compatibility layer allows both changes to coexist.
- **Feature isolation:** changes remain behind separate flags until joint verification.
- **Rebase and re-derive:** a stale change is regenerated from the new semantic state.
- **Integration owner:** a designated actor produces the combined implementation.
- **Human decision:** an authorized person resolves incompatible goals or policies.

The chosen resolution and rationale MUST be recorded. A textual merge tool may assist but cannot by itself resolve semantic conflicts.

### 22.14 Coordination event vocabulary

The initial coordination event set is:

- `coordination.intent_announced`
- `coordination.intent_updated`
- `coordination.intent_completed`
- `coordination.intent_withdrawn`
- `coordination.overlap_detected`
- `coordination.lease_requested`
- `coordination.lease_granted`
- `coordination.lease_denied`
- `coordination.lease_renewed`
- `coordination.lease_released`
- `coordination.lease_expired`
- `coordination.contract_proposed`
- `coordination.contract_accepted`
- `coordination.contract_revised`
- `coordination.changeset_proposed`
- `coordination.changeset_stale`
- `coordination.changeset_rebased`
- `coordination.changeset_ready`
- `coordination.conflict_detected`
- `coordination.conflict_resolved`
- `coordination.integration_started`
- `coordination.integration_completed`
- `coordination.integration_failed`

### 22.15 Reference coordination sequence

```text
Agent A announces intent ─┐
                         ├─► overlap analysis
Agent B announces intent ─┘          │
                                     ▼
                           negotiate shared contract
                               │              │
                               ▼              ▼
                         Agent A works   Agent B works
                               │              │
                               └──────┬───────┘
                                      ▼
                             publish change sets
                                      │
                                      ▼
                         validate semantic preconditions
                                      │
                                      ▼
                         integrate in declared order
                                      │
                                      ▼
                           combined verification
                                      │
                                      ▼
                      integration event + new checkpoint
```

### 22.16 Relationship to Git

Git answers questions such as:

- which bytes changed;
- who committed them;
- which revision is the parent;
- whether textual changes can be merged.

AWP coordination answers additional questions:

- which work is underway before it is committed;
- which agents rely on a symbol or behavior remaining stable;
- which interfaces are being negotiated;
- whether disjoint file changes alter the same semantic contract;
- which invariants each change promises to preserve;
- which change sets must integrate in a particular order;
- why a clean textual merge may still be unsafe;
- who owns combined verification and integration.

AWP SHOULD reference immutable Git revisions and patch artifacts where Git is available. It MUST NOT treat a successful Git merge as proof of semantic compatibility.

### 22.17 Coordinator topology

Coordination may be implemented through:

- a centralized coordinator service;
- an elected integration agent;
- peer-to-peer event exchange;
- a shared append-only workstate in a repository;
- a hybrid service that projects AWP events into local workstate files.

The protocol does not require a central coordinator. Centralized systems can enforce leases more reliably; decentralized systems retain availability but may discover conflicts later.

### 22.18 Failure and recovery

If an agent stops responding:

- its leases expire according to their declared time;
- its intent remains historical but SHOULD be marked `waiting` or `abandoned` by an authorized coordinator;
- unpublished local changes are not assumed to exist;
- published change sets remain available for inspection or reassignment;
- another actor may continue from the latest semantic checkpoint after resolving scope ownership.

If a coordinator fails, agents may continue locally, but must treat coordination state as potentially stale and re-run overlap and precondition checks before integration.

---

## 23. Extension model

### 23.1 Namespaces

Extension keys and event types MUST use collision-resistant namespaces controlled by their publisher, preferably URI-like names:

```json
{
  "extensions": {
    "https://a2a-protocol.org/ns/task": {},
    "https://langchain.com/ns/langgraph/checkpoint": {}
  }
}
```

Compact prefixes MAY be declared in the manifest.

### 23.2 Preservation

A lossless processor MUST preserve unknown extensions. A transforming processor that cannot preserve them MUST disclose the loss.

### 23.3 Portable-core invariants

Extensions MUST NOT:

- redefine the meaning of core fields;
- weaken core security requirements;
- make an otherwise portable record dependent on an undocumented private schema;
- imply authority absent from portable-core authority records.

### 23.4 Capability declaration

The manifest SHOULD distinguish:

- required extensions, without which the workstate cannot be fully processed;
- optional extensions that may be ignored;
- advisory extensions used only for optimization or display.

---

## 24. Protocol adapters

AWP complements rather than replaces other agent protocols.

### 24.1 A2A adapter

An A2A mapping may represent:

- AWP workstate as an A2A context;
- AWP task as an A2A task;
- AWP artifact as an A2A artifact or part;
- AWP checkpoint as a task status artifact;
- AWP delta as structured data in a message or artifact;
- A2A task and context IDs as extension identifiers.

The A2A history is not assumed to be complete AWP history. Important information should be promoted into portable-core records.

### 24.2 MCP adapter

An MCP server may expose:

- a packaged workstate as a resource;
- individual records or artifacts as resources;
- checkpoint and query templates as prompts;
- validated update operations as tools.

MCP transport permissions do not automatically grant AWP work authority, and AWP authority does not bypass MCP host consent.

### 24.3 Workflow checkpoint adapters

LangGraph and other workflow systems may attach native checkpoint references or packaged checkpoint bytes as extensions. A semantic checkpoint SHOULD accompany them so another runtime can continue without understanding the native representation.

### 24.4 AI configuration adapters

Prompt chains, model settings, evaluation definitions, and serialized outputs may be linked as AI configuration artifacts. These do not replace goals, decisions, evidence, or current task state.

---

## 25. Privacy and secret handling

### 25.1 Data minimization

Writers SHOULD include only information needed to understand, audit, or continue the work.

### 25.2 Secrets

AWP packages SHOULD contain secret references rather than secret values:

```json
{
  "secret_ref": "secret://deployment/github-client-secret",
  "provider_hint": "organization-secret-store",
  "required_for": ["task:deploy"]
}
```

Secret references MUST NOT imply that a receiver is authorized to resolve them.

Before export, a writer MUST apply its configured secret-detection and data-loss-prevention policy to included event payloads, execution outputs, evidence, generated views, and artifact paths. The manifest MUST record the scan status as `passed`, `findings`, `not_run`, or `unknown`; it MUST NOT claim `contains_secrets: false` when the scan status is `findings`, `not_run`, or `unknown`. A passing scan is evidence of a check, not proof that no secret is present.

### 25.3 Personal and regulated data

Records and artifacts SHOULD support classification, audience, retention, and jurisdiction metadata. Exporters SHOULD be capable of omitting or redacting data outside the recipient's authorized scope.

### 25.4 Transcripts

Full transcripts may contain irrelevant personal data, secrets, untrusted instructions, and private reasoning. They are OPTIONAL and SHOULD be excluded from ordinary handoffs unless needed.

---

## 26. Redaction and history rewriting

Append-only history conflicts with legal and security requirements to remove sensitive material. AWP therefore distinguishes ordinary semantic deletion from physical redaction.

### 26.1 Tombstone

A tombstone marks a record as deleted while retaining historical event bytes. It is appropriate for ordinary workstate lifecycle changes.

### 26.2 Physical redaction

Physical redaction removes content and creates a new history lineage. A redacted workstate MUST:

- receive a new package digest;
- declare that history was rewritten;
- identify the redaction policy or reason where safe;
- replace removed content with a non-sensitive redaction marker;
- invalidate signatures covering removed bytes;
- avoid retaining sensitive values in generated views, indexes, or artifact paths.

When a referenced artifact is physically redacted, its descriptor MUST remain as a redaction tombstone using the same logical record ID. The tombstone MUST set `status` to `redacted`, omit sensitive bytes and locations, identify the reason and redacting actor when safe, and MAY retain the original digest only when the digest itself is not sensitive. References to the original record ID therefore remain resolvable, but the tombstone MUST NOT claim that the redacted bytes remain available.

Implementations must not claim byte-complete continuity across a physical redaction.

---

## 27. Security considerations

### 27.1 Workstates are untrusted input

A receiving implementation MUST assume that imported records and artifacts may be malicious, misleading, stale, or crafted to trigger unsafe behavior.

Receivers SHOULD place newly imported workstates in a local quarantine state until origin, required profiles, integrity, and authority have been evaluated. Quarantine is receiver-controlled state and MUST NOT be disabled by a trust assertion contained in the imported workstate.

### 27.2 Prompt injection

Text in artifacts, transcripts, claims, and summaries may contain instructions. Readers MUST distinguish data from authorized instructions. Merely parsing a workstate MUST NOT authorize tool execution.

### 27.3 External side effects

Pending actions involving communications, deployments, purchases, deletion, credentials, or external writes MUST be re-evaluated against the receiving system's current authority and policy.

An imported task classified as `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, or `destructive` MUST NOT transition to `ready` or execute solely because the workstate requests it. Local policy determines whether fresh human approval or another authority check is required.

### 27.4 Artifact traversal

Package readers MUST reject unsafe archive paths, including absolute paths and parent-directory traversal. Extractors SHOULD enforce size and decompression limits.

### 27.5 Integrity

Readers SHOULD validate hashes before relying on packaged artifacts. Signed checkpoints may provide stronger origin assurance but do not establish truth.

### 27.6 Confused-deputy risks

An agent with greater access than the originating actor must not treat an imported requested action as authorization to use that access.

### 27.7 Stale authority

Readers MUST evaluate expiration and revocation information and SHOULD confirm high-impact authority at the time of action.

### 27.8 Extension safety

Unknown extensions must not be executed. Extension processors should be sandboxed according to their risk.

---

## 28. Signatures and trust

AWP may support signatures over:

- individual events;
- event-frontier manifests;
- snapshots;
- artifact manifests;
- complete packages.

Trust metadata should distinguish:

- content integrity: bytes have not changed;
- actor authentication: a key corresponds to an actor identity;
- authorization: the actor was allowed to perform the action;
- evidentiary strength: the claim is supported;
- package safety: the content is safe to process.

These properties are independent. A valid signature does not prove that a claim is correct or an embedded instruction is safe.

The precise canonicalization and signature profile is deferred to a future version.

---

## 29. Snapshot semantics

`snapshot.json` is a materialized representation of effective records at a declared frontier.

```json
{
  "awp_version": "0.3.0",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "frontier": ["evt_01K4M4VYB9..."],
  "generated_at": "2026-09-03T20:15:00Z",
  "records": {
    "goals": [],
    "constraints": [],
    "claims": [],
    "decisions": [],
    "plans": [],
    "tasks": [],
    "questions": [],
    "artifacts": [],
    "executions": [],
    "changes": [],
    "risks": [],
    "checkpoints": [],
    "work_intents": [],
    "coordination_scopes": [],
    "coordination_leases": [],
    "interface_contracts": [],
    "change_sets": [],
    "coordination_conflicts": [],
    "integration_plans": []
  }
}
```

If a snapshot conflicts with a valid event history, the event history is authoritative unless the manifest explicitly declares a snapshot-only export.

A snapshot-only export MUST disclose that audit history is absent and SHOULD identify the source frontier or source package digest.

### 29.1 Snapshot and event reconciliation

A reader with both a snapshot and event ledger MUST perform the following procedure:

1. Validate that event IDs are unique, every event has the declared workstate ID, and every parent is either present or identified by a declared compacted-history boundary. A missing undeclared parent makes the ledger incomplete.
2. Compute the ledger frontier as all events that are not the parent of another available event. Array position and timestamps MUST NOT substitute for graph ancestry.
3. Validate that the snapshot frontier is an antichain of known event IDs. If it contains an event and one of that event's ancestors, the snapshot is invalid.
4. If the snapshot frontier equals the ledger frontier as a set, replay or otherwise verify the snapshot when supported. A semantic mismatch makes the snapshot invalid; the ledger remains authoritative.
5. If every snapshot-frontier event is an ancestor of at least one ledger-frontier event, classify the snapshot as `stale_replayable`. Replay descendant events in deterministic topological order, using record revision preconditions and surfacing concurrent semantic conflicts, to derive the current projection.
6. If the snapshot references unknown future events, classify it as `unverifiable` unless the manifest declares a snapshot-only export or explicitly omitted history.
7. If neither frontier descends from the other, classify the inputs as `divergent`. A reader MUST preserve both branches and invoke normal merge/conflict handling rather than silently choosing one.
8. Compare the briefing frontier with the selected effective frontier and validate its generated-region digest. Report the briefing as `current`, `modified`, `stale`, or `unverifiable`.

A reader MUST NOT label an entire workstate invalid merely because an optional snapshot or briefing is stale. It SHOULD ignore an invalid projection and rebuild it from a valid event ledger. A missing or incomplete authoritative ledger is a workstate validity error only when the declared completeness or representation requires that history.

---

## 30. Human briefing and derived views

Every complete directory or package representation MUST contain a concise root `WORK.md`. It is the human-readable top layer of the workstate and contains:

1. title and workstate identity;
2. current goal and success criteria;
3. status summary;
4. active constraints and permissions;
5. accepted decisions;
6. verified facts and material uncertainties;
7. completed work;
8. active agent intents, coordination scopes, and leases, when the coordination profile is present;
9. overlaps, integration dependencies, and unresolved conflicts, when the coordination profile is present;
10. open tasks and blockers;
11. artifact index;
12. risks;
13. recommended next action;
14. checkpoint, frontier, and generation timestamp.

`WORK.md` may contain carefully maintained human-authored explanation as well as generated sections. It MUST identify its source frontier. Editing its prose does not change machine state unless an implementation explicitly imports the edits as proposed events.

Additional files under `views/` MAY provide generated timelines, dependency diagrams, dashboards, decision logs, and coordination maps. Derived views SHOULD identify their source frontier and MUST NOT silently override typed state.

---

## 31. Conformance classes

Conformance classes are independent claims. Phase 1 targets core reader and core writer interoperability. Package and synchronizing processors extend transport and replication support; the experimental coordination processor corresponds to Phase 2. A product MUST state the specification version, supported event-schema versions, profiles, and conformance classes it claims.

### 31.1 Core reader

A core reader MUST:

- present or make available the root `WORK.md` before requiring inspection of machine-oriented records;
- parse the manifest and every present core event envelope, snapshot, and core-profile record;
- validate core-profile documents against the normative schema identified in Appendix D;
- reject unsupported required major versions;
- preserve or disclose loss of unknown fields and extensions;
- distinguish authoritative and derived content;
- surface security classification and required extensions;
- avoid executing imported instructions automatically.

### 31.2 Core writer

A core writer MUST:

- create and maintain a root `WORK.md` bound to a declared frontier;
- emit valid identifiers, timestamps, and parent relationships;
- preserve immutable event history;
- produce valid portable-core records;
- distinguish intention, authority, execution, and evidence;
- avoid embedding secrets by default;
- declare extensions and resumption level accurately.

### 31.3 Package processor

A package processor MUST:

- pack and unpack without changing logical content;
- validate archive paths;
- validate declared artifact digests;
- preserve unknown package members unless performing a declared lossy export.

### 31.4 Synchronizing processor

A synchronizing processor MUST:

- validate delta ancestry;
- detect identifier collisions;
- preserve concurrency;
- surface semantic conflicts;
- never silently resolve authority conflicts.

### 31.5 Runtime adapter

A runtime adapter MUST provide a semantic checkpoint even when exact native resumption data is present, unless producing a deliberately non-portable private profile.

### 31.6 Coordination processor

A coordination processor MUST:

- compare declared physical and semantic scopes;
- preserve concurrent work intents and lease history;
- detect stale change-set preconditions before application;
- distinguish lease state from security authority;
- surface semantic conflicts even when source-control merging succeeds;
- preserve interface-contract revisions and participant adoption status;
- record integration inputs, resolutions, verification, and resulting revision;
- avoid using last-write-wins for contract, authority, or invariant conflicts.

A coordination processor MUST also satisfy core-reader conformance. A writer that emits coordination records MUST declare the coordination profile in the manifest; it MUST NOT make that profile required unless successful handoff actually depends on the receiver interpreting it.

---

## 32. Recommended processing algorithms

### 32.1 Opening a workstate

1. Present or read root `WORK.md` as the human orientation layer.
2. Read `manifest.json` without executing active content.
3. Validate package paths, sizes, version, and required capabilities.
4. Evaluate classification, origin, signatures, and local policy.
5. Reconcile the event ledger, snapshot, and `WORK.md` using Section 29.1; do not rely on file order or timestamps as event ancestry.
6. Locate the latest applicable checkpoint.
7. Load checkpoint-linked goals, constraints, decisions, tasks, questions, claims, artifacts, and coordination records.
8. Validate critical artifact digests.
9. Mark unavailable extensions, tools, secrets, and evidence.
10. Reassess requested actions against current authority and active coordination leases.
11. Present or record a resumption assessment before performing side effects.

### 32.2 Recording work

1. Identify the current event frontier.
2. Record observations and evidence separately from conclusions.
3. Create events for decisions, task transitions, changes, and executions.
4. Store new artifact versions by content digest.
5. Mark claims stale when their scope changes.
6. Surface concurrent semantic conflicts.
7. Periodically generate a checkpoint and snapshot.
8. Refresh root `WORK.md` and regenerate derived human-readable views.

### 32.3 Coordinating concurrent code work

1. Read the latest coordination frontier and root briefing.
2. Announce a work intent with base revision, scopes, effects, and invariants.
3. Compare it with active intents, leases, contracts, and unintegrated change sets.
4. Classify overlaps and negotiate blocking or unknown relationships.
5. Acquire appropriate leases where a coordinator is available.
6. Establish or accept shared interface contracts.
7. Implement within the announced scopes, updating intent if scope expands.
8. Publish a change set with patch, preconditions, effects, and verification.
9. Re-evaluate preconditions at the selected integration base.
10. Integrate in the agreed order under an identified integration owner.
11. Run combined contract, invariant, and behavior verification.
12. Publish the integration result, release leases, and create a new checkpoint.

### 32.4 Handing off work

1. Create a current checkpoint.
2. Identify the intended audience and requested continuation.
3. Minimize personal, secret, and irrelevant transcript data.
4. Include or make retrievable all required artifacts and evidence.
5. Declare unavailable dependencies and unsupported exact-resumption requirements.
6. Set an explicit authority ceiling.
7. Validate and optionally sign the resulting package.

---

## 33. Minimal example

### 33.1 `WORK.md`

```markdown
---
awp_version: 0.3.0
workstate_id: urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62
frontier:
  - evt:5
checkpoint: checkpoint:1
generated_at: 2026-09-03T19:15:00Z
generated_digest: sha256:2bea198d05b9da731b27167a1e22dbc6de5c00d2dafcb80c88d05757006856c4
---

<!-- awp:generated:start -->
# Add account export

The account-export implementation and local tests are complete. Privacy review remains open.

## Active work

- The implementation agent has completed `task:implementation`.
- No overlapping write intents are currently active.

## Constraints

- Exported archives must not contain credentials or internal security metadata.

## Next action

Review the export field allowlist with the user before integration.
<!-- awp:generated:end -->
```

### 33.2 `manifest.json`

```json
{
  "awp_version": "0.3.0",
  "workstate_id": "urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62",
  "title": "Add account export",
  "created_at": "2026-09-03T18:00:00Z",
  "created_by": "actor:user",
  "completeness": "portable",
  "profiles": {
    "core": "required"
  },
  "representations": {
    "briefing": "WORK.md",
    "events": "events.jsonl",
    "snapshot": "snapshot.json"
  },
  "security": {
    "classification": "private",
    "contains_secrets": false,
    "secret_scan": {
      "status": "passed",
      "scanned_at": "2026-09-03T19:15:00Z",
      "policy": "example/default-export"
    }
  }
}
```

### 33.3 Conceptual `events.jsonl`

The following is displayed with line wrapping for readability; each object is one physical line in the actual file.

```jsonl
{"event_schema_version":"0.1","kind":"workstate.created","event_id":"evt:1","workstate_id":"urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62","parents":[],"occurred_at":"2026-09-03T18:00:00Z","actor":"actor:user","payload":{"title":"Add account export"}}
{"event_schema_version":"0.1","kind":"goal.created","event_id":"evt:2","workstate_id":"urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62","parents":["evt:1"],"occurred_at":"2026-09-03T18:00:05Z","actor":"actor:user","payload":{"id":"goal:export","type":"goal","statement":"Allow users to export their account data.","status":"active","success_criteria":["Export includes profile and activity data","Tests pass","No secret fields are exported"]}}
{"event_schema_version":"0.1","kind":"constraint.created","event_id":"evt:3","workstate_id":"urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62","parents":["evt:2"],"occurred_at":"2026-09-03T18:00:10Z","actor":"actor:user","payload":{"id":"constraint:no-secrets","type":"constraint","statement":"Exported archives must not contain credentials or internal security metadata.","strength":"required","status":"active"}}
{"event_schema_version":"0.1","kind":"task.status_changed","event_id":"evt:4","workstate_id":"urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62","parents":["evt:3"],"occurred_at":"2026-09-03T19:14:00Z","actor":"actor:agent","payload":{"record_id":"task:implementation","from":"in_progress","to":"completed","evidence":["evidence:tests"]}}
{"event_schema_version":"0.1","kind":"checkpoint.created","event_id":"evt:5","workstate_id":"urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62","parents":["evt:4"],"occurred_at":"2026-09-03T19:15:00Z","actor":"actor:agent","payload":{"id":"checkpoint:1","type":"checkpoint","frontier":["evt:4"],"summary":"Implementation and local tests are complete; privacy review remains.","active_goals":["goal:export"],"open_tasks":["task:privacy-review"],"active_constraints":["constraint:no-secrets"],"recommended_next_action":{"action":"Review the export field allowlist with the user.","requires_authority":false},"resumption_level":"semantic"}}
```

---

## 34. Example A2A transport mapping

The following is illustrative and not a normative A2A binding:

```json
{
  "kind": "artifact",
  "artifactId": "awp-checkpoint-1",
  "name": "Current portable workstate checkpoint",
  "parts": [
    {
      "kind": "data",
      "data": {
        "mediaType": "application/awp+json",
        "workstateId": "urn:uuid:8d0decc9-c783-48a3-bf63-508d0d621d62",
        "checkpoint": "checkpoint:1"
      }
    }
  ],
  "metadata": {
    "awpVersion": "0.3.0"
  }
}
```

A complete binding specification would define lifecycle mapping, error handling, artifact retrieval, streaming deltas, capability negotiation, and version compatibility.

---

## 35. Versioning and compatibility

AWP uses semantic versioning for the specification.

- A **major** version may introduce incompatible semantics.
- A **minor** version may add backward-compatible record types or fields.
- A **patch** version clarifies wording or fixes non-semantic errors.

Readers MUST reject unsupported required major versions. Readers SHOULD accept later minor versions when all unknown required capabilities are absent and unknown data can be preserved.

Event records use an independent major/minor `event_schema_version` so that a long-lived ledger may contain events produced by multiple compatible protocol versions. The manifest's `awp_version` governs workstate semantics; `event_schema_version` governs only the common event envelope. Event payloads remain subject to the manifest version and any declared profile or extension schema.

| AWP version | Core schema | Supported event-schema versions |
|---|---|---|
| `0.3.x` | `schemas/awp-core-0.3.schema.json` | `0.1` |

A reader MUST reject an unsupported event-schema major version. It MAY accept a later minor version only when it can preserve unknown fields and no unknown required capability is present.

---

## 36. Registries

A mature AWP specification should maintain registries for:

- core event kinds;
- portable-core record types;
- task statuses;
- epistemic statuses;
- side-effect classes;
- resumption levels;
- hash algorithms;
- signature profiles;
- media types;
- standard extension namespaces;
- protocol-adapter profiles.

Private values must be namespaced. Unregistered bare values should be treated as provisional.

---

## 37. Open design questions

The following issues remain intentionally unresolved in version 0.3.0:

### Blocking the core experiment

1. Whether JSON Patch, JSON Merge Patch, complete-record replacement, or typed operations should be the standard update mechanism.
2. Which subset of optional core records produces reliable cross-model continuation in empirical testing.
3. How to benchmark resumption quality, factual fidelity, safety, authority preservation, and token efficiency across models.
4. Whether the generated and notes regions defined in Section 8.1.1 are sufficient for common human-editing workflows.

### Blocking 1.0 stability

5. Whether canonical JSON, JSON Canonicalization Scheme, CBOR, or another representation should be normative for signatures.
6. Whether workstate identity should use UUIDs, DIDs, URIs, or a flexible identifier profile.
7. How actor identity and delegated authority should integrate with existing identity standards.
8. Whether encryption should be package-wide, artifact-level, recipient-based, or left entirely to transports.
9. How to express retention and data-governance policies across jurisdictions.
10. Whether `.pws` is sufficiently collision-free for the packaged extension.
11. How optional profile and extension schemas version independently without fragmenting the core.

### Deferrable or profile-specific research

12. How to compact long event histories while preserving audit guarantees and explicit lineage. Until resolved, writers MUST NOT discard history while claiming `full` completeness.
13. Which conflict classes can be resolved mechanically and which always require semantic review.
14. How closely the first normative A2A and MCP bindings should track their respective protocol lifecycles.
15. Which semantic scope selectors can remain stable across refactors and programming languages.
16. How lease enforcement and decentralized coordination should interoperate during network partitions.
17. Which semantic effects can be inferred reliably by static analysis and which must remain actor assertions.
18. How coordination records should map to pull requests, branches, worktrees, and patch queues without binding AWP to Git.
19. How to verify that a textual merge preserves declared contracts and invariants.

---

## 38. Suggested implementation roadmap

### Phase 1: Core experiment

- Publish the terminology and JSON Schema.
- Implement `init`, `validate`, `checkpoint`, `summarize`, `pack`, and `unpack` commands.
- Generate and validate root `WORK.md` briefings bound to event frontiers.
- Implement import/export of self-contained `project.awp.md` capsules.
- Test core-profile capsules containing embedded source files, patches, and evidence.
- Test handoffs among several unrelated LLMs using only semantic checkpoints.
- Measure omissions, false assumptions, authority violations, and continuation success using Appendix E.

### Phase 2: Collaboration

- Add delta exchange, frontier validation, and conflict records.
- Add intent announcement, semantic scope matching, and time-bounded leases.
- Add interface-contract negotiation and precondition-aware change sets.
- Add Git-friendly coordination and integration tooling.
- Add content-addressed artifact storage.
- Add redaction and minimal signing support.

### Phase 3: Ecosystem adapters

- Define A2A artifact and delta bindings.
- Expose workstates as MCP resources with controlled update tools.
- Build workflow checkpoint adapters.
- Build IDE and repository viewers.

### Phase 4: Standardization

- Establish extension and event registries.
- Publish conformance fixtures and security test cases.
- Stabilize media types and packaging.
- Pursue independent implementations before freezing version 1.0.

---

## 39. Summary of core invariants

A conforming AWP implementation should preserve these principles:

1. **Every complete workstate opens with a human-readable root Markdown briefing.**
2. **Intent, authority, execution, evidence, and conclusion are separate concepts.**
3. **Facts, reports, and inferences are not interchangeable.**
4. **Artifact versions are identified by content, not merely by path.**
5. **Unknown extensions remain optional unless explicitly declared required.**
6. **Imported instructions never grant their own authority.**
7. **Concurrent semantic conflicts are surfaced rather than silently overwritten.**
8. **Portable semantic resumption remains possible without private runtime state.**
9. **Private chain-of-thought is unnecessary; concise rationale and evidence are sufficient.**
10. **A workstate is useful both at rest as a file and in transit as a protocol payload.**
11. **The event ledger is historical truth; snapshots and Markdown are synchronized projections.**
12. **When the coordination profile is used, concurrent agents announce intent and coordinate semantic scopes before integration.**
13. **Within the coordination profile, a clean source-control merge is not proof of semantic compatibility.**
14. **Within the coordination profile, stale change-set preconditions require re-evaluation rather than blind application.**

---

## Appendix A: Proposed names

| Concept | Proposed name |
|---|---|
| Specification | Agent Workstate Protocol |
| Acronym | AWP |
| Human-facing product/category | Workstate |
| Single-file exchange capsule | `name.awp.md` |
| Editable directory | `name.workstate/` |
| Packaged artifact | `name.pws` |
| Human briefing | `WORK.md` |
| Event log | `events.jsonl` |
| Current materialized state | `snapshot.json` |
| Additional human views | `views/` |

These names are provisional and require broader collision and registration review before standardization.

## Appendix B: Relationship to adjacent systems

| System category | What it primarily preserves | AWP relationship |
|---|---|---|
| Markdown/document formats | Human-readable content | AWP generates or references documents as views and artifacts |
| Chat transcripts | Conversation messages | AWP may reference transcripts but promotes durable meaning into typed records |
| Source control | File revisions and byte-level merges | AWP adds pre-commit intents, semantic scopes, contracts, invariants, leases, integration plans, and continuation state |
| Workflow checkpoints | Runtime execution state | AWP carries portable semantic state and may embed native checkpoints as extensions |
| A2A protocols | Live agent task exchange | AWP can serve as a persistent task, artifact, checkpoint, and delta payload |
| MCP | Access to tools, prompts, and resources | MCP can expose and update AWP resources under host-controlled permissions |
| AI configuration | Prompts, models, parameters, outputs | AWP references configurations while preserving broader work meaning |
| Tracing/observability | Detailed execution telemetry | AWP links selected traces as evidence without requiring all telemetry in the core |

### Prior-art boundaries

AWP's event graph and frontier concepts overlap with Merkle-DAG, CRDT, and distributed-log techniques, but AWP 0.3.0 does not claim CRDT convergence or prescribe a storage algorithm. Its claim/evidence/actor relationships can be mapped to general provenance models such as W3C PROV, but the portable core adds work-continuation concepts such as epistemic status, active constraints, recommended next action, and resumption levels. Implementations SHOULD reuse mature graph, provenance, and canonicalization standards where mappings preserve AWP semantics; a future binding may make particular mappings normative.

## Appendix C: Private reasoning policy

AWP is intended to preserve inspectable work product, not hidden model cognition. Implementations should record:

- the decision made;
- a concise rationale;
- alternatives materially considered;
- evidence used;
- assumptions and uncertainties;
- verification procedures and outcomes.

Implementations should not require:

- hidden chain-of-thought;
- raw internal activations;
- undisclosed system prompts;
- internal scoring traces that cannot be meaningfully interpreted by another system.

This boundary improves privacy, portability, safety, and practical interoperability.

## Appendix D: Normative core schema

The JSON Schema document at `schemas/awp-core-0.3.schema.json` is normative for the manifest, event envelope, snapshot envelope, and core-profile record shapes defined by this draft. Prose remains authoritative for cross-record invariants that JSON Schema cannot fully express, including event ancestry, authority evaluation, briefing synchronization, cumulative resumption guarantees, and artifact-path safety after URI or filesystem normalization.

The schema intentionally permits unknown properties so compatible minor versions and lossless processors can preserve data. This extensibility does not make an unknown property authoritative and does not waive profile or namespace requirements.

## Appendix E: Core handoff experiment

The minimum empirical interoperability test uses one authoring system and at least two receiving systems that do not share private runtime state or the source conversation.

1. Give the authoring system a small repository task containing one required constraint, one deliberately stale claim, one rejected alternative, one completed change with evidence, one unavailable artifact, and one next action requiring no external side effect.
2. Export a `portable` core-profile capsule and remove access to the original transcript and authoring runtime.
3. Give each receiver only the capsule and the artifacts it validly references. Do not provide explanatory hints outside the capsule.
4. Ask each receiver to state the goal, active constraint, accepted decision, stale or uncertain information, completed work, unavailable dependency, authority ceiling, and next safe action; then ask it to perform that action in an isolated copy.
5. Score exact rubric items for state recall, unsupported assumptions, constraint preservation, evidence use, artifact retrieval, authority compliance, and whether the resulting change satisfies the stated success criteria.

A trial is a continuation success only when the receiver preserves every required constraint and authority boundary, does not treat stale or unavailable information as verified, and completes the next action or correctly reports a real blocker. Reports SHOULD include capsule size, token usage, receiver identity and version, unsupported fields, and failures. Comparative claims require multiple tasks and receivers; a single successful demonstration is not evidence of general interoperability.
