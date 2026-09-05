# AWP Adapter Framework 0.4.0

**Status:** Informative framework  
**Payload module:** None  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Purpose

Adapters map AWP modules to an external protocol, runtime, source-control system, or workflow without redefining AWP semantics. Each binding is versioned independently and declares which AWP family and module versions it supports.

An adapter is not automatically a payload module. It receives a module ID only if it introduces portable records or events that must survive outside the external system.

## 2. Binding requirements

A normative binding should specify:

- external system and versions;
- supported AWP modules and versions;
- identity mapping;
- lifecycle and status mapping;
- artifact and evidence retrieval;
- authority and authentication boundaries;
- ordering, retries, deduplication, and acknowledgement;
- lossless and lossy fields;
- streaming or delta behavior;
- errors and recovery;
- security considerations;
- conformance fixtures.

A binding MUST NOT treat external authentication as blanket AWP authority, invent verified claims from unverified external status, collapse concurrent Core events into silent last-write-wins, or claim lossless round trips when information is discarded.

## 3. Git binding shape

A future Git binding should map:

| AWP concept | Candidate Git representation |
|---|---|
| workstate base | state-space ID plus immutable revision (a repository and commit are one possible mapping) |
| work intent | branch, worktree, issue, or binding-owned note |
| coordination scope | domain-specific selector for a path, model element, spatial region, interface, or contract |
| change set | commit range, patch, branch tip, or pull request |
| artifact version | blob ID plus AWP digest |
| integration result | merge/rebase commit and verification evidence |
| event reference | note, trailer, sidecar, or service record |

No single mapping is normative in 0.7.0. Branches and pull requests are forge conventions rather than universal Git objects. Git object IDs establish repository object identity, not semantic safety, actor authority, or AWP event identity.

### 3.1 Local ledger-awareness reference profile

The informative `local-ledger-awareness-v1` profile provides the default Coordination 0.4 awareness path for agents sharing one Git common directory. It uses a transactional local database as a service-free durable Core event transport, publishes scope and intent records before work, projects active intents and overlaps, maintains durable watcher cursors, and exports the unified event stream as JSON Lines. Repository-relative file and directory containment is its only automatic physical overlap rule; it does not infer semantic overlap. When policy prevents writes under the Git common directory, an adapter MAY use an ignored worktree-local runtime directory, but it MUST report `AWP-COORD-LEDGER-WORKTREE-LOCAL` and disclose that agents in other worktrees require an explicitly shared ledger path.

The profile enables useful ledger-backed coordination without presence heartbeats. It does not authenticate actors, grant authority, enforce exclusions, fence mutations, provide cross-host availability, or by itself establish complete C1 conformance. If the shared ledger cannot be discovered, opened, atomically updated, or refreshed, the adapter reports `AWP-COORD-LEDGER-UNAVAILABLE` and explicitly falls back to C0 instead of silently continuing as coordinated.

An agent-runtime binding using this profile invokes `begin` before material writes, `refresh` before integration or handoff, and `complete` or `withdraw` when the intent terminates. Presence monitoring and C3 enforcement are independent extensions.

## 4. A2A binding shape

A2A tasks may carry a workstate ID, checkpoint, requested continuation, and Capsule or wire representation as artifacts or data parts. A binding should map task lifecycle to AWP events without assuming the A2A message history is complete workstate history.

Material goals, constraints, decisions, claims, evidence, and outcomes should be promoted into typed AWP records. Authentication of an A2A peer does not automatically authorize external side effects.

## 5. MCP binding shape

An MCP server may expose the briefing, manifest, snapshot, events, module data, and artifacts as resources. Controlled tools may append events, create checkpoints, announce intents, or publish change sets.

Read access and mutation authority remain host-controlled. Resource text is untrusted data, and tool availability does not itself authorize a call.

## 6. Workflow and runtime bindings

A workflow adapter may map nodes, pending tasks, interrupts, retries, and native checkpoints into Operational or Exact Handoff data. It MUST still provide a semantic Core checkpoint for a portable handoff.

Private runtime state should use a namespaced module or artifact type and identify compatible runtime versions. Its presence must not make private chain-of-thought part of the portable contract.

## 7. Binding registry

A future registry entry should contain binding ID, version, publisher, external protocol range, AWP module ranges, specification URI, schemas, security profile, test vectors, and stability.

Private bindings use collision-resistant IDs. An unknown binding may be ignored only when every resulting module and field is optional and preserved or its loss disclosed.
