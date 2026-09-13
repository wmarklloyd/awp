# AWP Adapter Framework 0.6.0

**Status:** Informative framework  
**Payload module:** None  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-13  
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

No single mapping is normative in 0.8.0. Branches and pull requests are forge conventions rather than universal Git objects. Git object IDs establish repository object identity, not semantic safety, actor authority, or AWP event identity.

### 3.1 Local ledger-awareness reference profile

The informative `local-ledger-awareness-v1` profile provides the default Coordination 0.4 awareness path for agents sharing one Git common directory. It uses a transactional local database as a service-free durable Core event transport, publishes scope and intent records before work, projects active intents and overlaps, maintains durable watcher cursors, and exports the unified event stream as JSON Lines. Repository-relative file and directory containment is its only automatic physical overlap rule; it does not infer semantic overlap. When policy prevents writes under the Git common directory, an adapter MAY use an ignored worktree-local runtime directory, but it MUST report `AWP-COORD-LEDGER-WORKTREE-LOCAL` and disclose that agents in other worktrees require an explicitly shared ledger path.

The profile enables useful ledger-backed coordination without presence heartbeats. It does not authenticate actors, grant authority, enforce exclusions, fence mutations, provide cross-host availability, or by itself establish complete COOP-1 conformance. If the shared ledger cannot be discovered, opened, atomically updated, or refreshed, the adapter reports `AWP-COORD-LEDGER-UNAVAILABLE` and explicitly falls back to uncontracted portable behavior instead of silently continuing as actively coordinated.

An agent-runtime binding using this profile invokes `begin` before material writes, `refresh` before integration or handoff, and `complete` or `withdraw` when the intent terminates. Presence monitoring is a COOP-1 component; authenticated protected enforcement belongs to COOP-3.

## 4. A2A binding shape

A2A tasks may carry a workstate ID, checkpoint, requested continuation, and Capsule or wire representation as artifacts or data parts. A binding should map task lifecycle to AWP events without assuming the A2A message history is complete workstate history.

Material goals, constraints, decisions, claims, evidence, and outcomes should be promoted into typed AWP records. Authentication of an A2A peer does not automatically authorize external side effects.

### 4.1 `coop3-a2a-v1` binding shape

The named `coop3-a2a-v1` profile uses A2A as a communications and execution control plane for a COOP-3 protected binding. It does not make A2A a mandatory AWP transport, and it does not make an A2A server, task queue, or Agent Card the authoritative coordination store.

| AWP protected operation | A2A role | Required authoritative result |
|---|---|---|
| participant entry or renewal | task/request delivery | authenticated actor-to-principal binding and durable lease receipt |
| guarded intent announcement | task/request delivery | atomic admission, conflict, or block receipt |
| guarded decision or resolution | task update or result | durable decision record with binding epoch and frontier |
| protected mutation | task/request delivery | gateway acceptance only after expected-state and fencing validation |
| checkpoint or handoff | artifact/data delivery | canonical projector receipt with artifact digest and included frontier |
| terminal completion or withdrawal | task/request delivery | idempotent terminal intent receipt |

Every A2A request in this profile carries an immutable AWP operation ID, workstate ID, stable binding identity, actor ID, and the operation's expected state. The adapter records the A2A task ID and endpoint only as correlation metadata. It persists or obtains the AWP binding result before returning success. Duplicate A2A delivery, a resumed task, or a request received by a replacement endpoint must return the same receipt or a stable rejection; it must not duplicate a lease, intent, or fencing generation.

The binding declares its supported A2A interfaces and protocol version, transport authentication mechanism, actor/principal mapping, store identity, and protected mutation gateway. A2A authentication is evidence for that mapping, not blanket AWP authority. The protected store and gateway independently validate authorization, expected epoch/frontier or revision, scope, and fencing token. The adapter reports A2A reachability separately from store and gateway reachability, and fails closed for protected mutation when any required check is unavailable.

## 5. MCP binding shape

An MCP server may expose the briefing, manifest, snapshot, events, module data, and artifacts as resources. Controlled tools may append events, create checkpoints, announce intents, or publish change sets.

Read access and mutation authority remain host-controlled. Resource text is untrusted data, and tool availability does not itself authorize a call.

## 6. Workflow and runtime bindings

A workflow adapter may map nodes, pending tasks, interrupts, retries, and native checkpoints into Operational or Exact Handoff data. It MUST still provide a semantic Core checkpoint for a portable handoff.

Private runtime state should use a namespaced module or artifact type and identify compatible runtime versions. Its presence must not make private chain-of-thought part of the portable contract.

## 7. Binding registry

A future registry entry should contain binding ID, version, publisher, external protocol range, AWP module ranges, specification URI, schemas, security profile, test vectors, and stability.

Private bindings use collision-resistant IDs. An unknown binding may be ignored only when every resulting module and field is optional and preserved or its loss disclosed.

## 8. Action Boundary harness bindings

Section 2's binding-requirements checklist applies in full to a runtime binding of `urn:awp:action-boundary`. This section adds one further principle specific to that module: because action-boundary's own purpose is enforcement independent of the gated participant's cooperation (action-boundary.md section 7), a binding to one agent runtime's hook or plugin API is necessarily advisory, not enforcement, no matter how well it is built -- the participant's own host executing the check is exactly the case action-boundary.md section 7 already excludes from an "enforcement adapter." A binding that wants to make an `action-enforced` conformance claim (action-boundary.md section 10) needs a component outside every agent's control, most concretely a CI gate on the protected branch, evaluated identically regardless of which agent, or human, produced the change.

This repository's own reference implementation of the above is `tools/awp_harness.py` (the host-agnostic resolution/binding/compliance-report core, callable by any agent or CI system that can start a subprocess) plus two concrete profiles built on it:

- **`claude-code-hooks-v1`** (`adapters/claude-code-hooks/` in this repository) -- advisory. Maps Claude Code's PreToolUse, PostToolUse, and Stop hooks (verified against the current Claude Code hooks reference, 2026-09-13) to `tools/awp_harness.py`'s `gate`, `enforce`, and `session_compliance_report` respectively. Declares, per the checklist above: external system Claude Code, hook JSON contract as observed 2026-09-13; supported modules `urn:awp:action-boundary` 0.3.1, `urn:awp:core` 0.8.x; identity mapping is a project-local `actor` string in `config.json`, not an authenticated identity; lifecycle mapping is the three hooks above; artifact/evidence retrieval is filesystem-local, relative to the repository root; authority boundary is none -- this binding grants no authority, it only reports a resolution; ordering is per-tool-call, correlated by Claude Code's `tool_use_id`; no deduplication or retry handling is attempted in this prototype; lossy fields: the hook contract's `permissionDecisionReason` truncates a resolution's full diagnostics to one string; errors and recovery: a missing or unparsable `config.json` fails open (allow), by design, since this binding is advisory and a broken local hook must not be able to freeze a session -- see Known bypasses below and in `adapters/claude-code-hooks/README.md`; security considerations and known bypasses are enumerated in that README rather than duplicated here; conformance fixtures are `tests/test_awp_harness.py`'s `GateTests` and `EnforceTests`.
- **`action-boundary-ci-gate-v1`** (`tools/awp_ci_gate.py`) -- the binding this repository's own `action-enforced` claim, if made, would rest on. It is agent-blind by construction: its only inputs are a changed-files list, a declared protected-paths configuration, the current guardrail and decision set, and artifact-claim records, none of which name or depend on which agent produced the change. It mechanically re-verifies each protected artifact's claim evidence against the actual current repository content (recomputing a source digest, not trusting a recorded one) and re-resolves the action against a freshly loaded guardrail/decision set, per `tools/awp_action_boundary.py`'s own stated principle that an enforcement adapter must recompute, never trust a resolution handed to it. Conformance fixtures: `tests/test_awp_harness.py`'s `CiGateTests`.

Both profiles report against action-boundary.md section 10's existing five-level conformance ladder (`context-aware` / `decision-resolved` / `action-bound` / `action-enforced` / `output-attested`) -- see `tools/awp_harness.py`'s `_conformance_levels_observed` -- rather than defining a second, parallel taxonomy; an earlier harness proposal's own draft H0-H4 levels were reframed out during reconciliation for exactly this reason (`research/model-assisted-reviews/codex-harness-reconciliation-evaluation.md`, correction 3).

Neither profile is a payload module: per section 1, an adapter receives a module ID only if it introduces a portable record that must survive outside the external system. `invocation_binding` is owned by `urn:awp:action-boundary` itself (it is meaningful independent of any one host); small descriptive fields this harness needs that neither Core nor action-boundary define (a reviewer's actor string, a source event-log path, and similar) are namespaced under `modules."urn:awp:harness-runtime"`, an informative, host-local convention, not a registered module -- deliberately following the same `modules.{module-id}` discipline core.md requires of real modules, so this harness does not repeat the unqualified-field mistake action-boundary 0.3.1 itself had to correct.

Known limitations, stated up front rather than discovered later: this prototype does not implement a tool-call gateway stronger than a hook (action-boundary.md section 5's protected-kind tool constraint, for a tool that cannot be wrapped at all, remains open per open-issues.md item 48); it does not implement the decision-capture UX's "detect a candidate from a corrective commit or review comment" step, only the propose/accept pair once a candidate has been identified by some other means; and it has not been run against a real CI system in this repository -- `tools/awp_ci_gate.py` is tested directly (`tests/test_awp_harness.py`) but not yet wired into an actual protected-branch check here.
