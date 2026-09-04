# AWP 0.5.0 Multi-Agent Coordination: State-of-the-Art Review

**Review date:** 2026-09-03  
**Reviewed component:** AWP Coordination 0.2.0 in AWP 0.5.0  
**Status:** Design review and research roadmap; not a normative specification

## Executive assessment

AWP is addressing a real and increasingly well-measured problem. Current coding agents are capable in isolation, but collaboration adds a coordination penalty: CooperBench reports an average 30% success-rate reduction when agents work together, caused by vague or mistimed messages, broken commitments, and incorrect beliefs about other agents' plans. Long-running work also accumulates state: ChainSWE reports performance declines of up to 70% as dependent issue chains grow. These results support AWP's premise that durable intent, assumptions, dependencies, contracts, and evidence should survive conversations, tools, machines, and agent vendors.

The current Coordination module has the right conceptual center. Its strongest ideas are:

- semantic as well as physical scopes;
- relied-upon reads, rather than treating only writes as conflicts;
- versioned interface contracts and invariants;
- change sets with explicit preconditions, effects, and verification;
- separation of a clean textual merge from semantic compatibility;
- an honest distinction between advisory state and live enforcement;
- repository-bound, transport-independent state that can outlive any orchestrator.

It is not yet state of the art as an implementable protocol. It is currently a strong vocabulary and process narrative, but several safety-critical behaviors remain prose: state transitions, acknowledgement, conflict ownership, concurrency control, observed-versus-declared effects, verification binding, staleness propagation, security, and liveness. There are no conformance fixtures or comparative coordination benchmark yet.

The recommended direction is not to make AWP a larger chat or agent-to-agent protocol. AWP should become the **durable semantic control plane for project work**, interoperating with A2A or other transports and with Git, worktrees, forges, CI, and live coordinators as enforcement adapters.

## 1. What the state of the art now contains

No single system supplies the whole solution. The frontier is a combination of five lines of work.

### 1.1 Role and workflow orchestration

ChatDev and MetaGPT demonstrated that specialized roles, structured conversations, and software-development operating procedures can improve multi-agent production. Their main unit is the orchestrated conversation or workflow. This is useful, but it does not by itself establish durable cross-runtime truth about a changing repository.

- [ChatDev](https://aclanthology.org/2024.acl-long.810/) guides specialized agents through a communication chain spanning design, coding, and testing.
- [MetaGPT](https://openreview.net/forum?id=VtmBAGCN7o) encodes standardized operating procedures into a role-based multi-agent workflow.

AWP should remain compatible with these systems without adopting their particular team topology. Roles are execution policy; the project workstate should remain valid when the next agent uses a different topology or no multi-agent framework at all.

### 1.2 Protocols, contracts, and explicit lifecycle

SEMAP applies explicit behavioral contracts, structured messages, lifecycle-guided execution, and verification over A2A. Its evaluation reports substantial failure reductions across development and vulnerability-detection tasks. MPAC is even closer to AWP's coordination problem: it defines session, intent, operation, conflict, and governance layers for agents controlled by different principals, using normative state machines, causal watermarking, and optimistic concurrency control.

- [SEMAP](https://arxiv.org/abs/2510.12120) supplies direct evidence for contracts plus lifecycle-bound verification.
- [MPAC](https://arxiv.org/abs/2604.09744) supplies a close comparison point for intent declaration, first-class conflicts, governance, state machines, security profiles, and shared-state concurrency control.
- The official [A2A core specification](https://agent2agent.info/specification/core/) standardizes discovery, messages, task lifecycle, and artifacts; it is a transport/task substrate, not a repository-semantic coordination model.

Older multi-agent-systems research also matters. FIPA's Contract Net specifies proposals, acceptance, rejection, completion/failure, conversation identity, and reply deadlines. Commitment-based protocol research shows how independently operated agents can align their view of obligations, and how protocols can be analyzed for safety and liveness.

- [FIPA Contract Net](https://www.fipa.org/specs/fipa00029/SC00029H.html) is a useful precedent for bounded negotiation and explicit exceptional outcomes.
- [Clouseau](https://ojs.aaai.org/index.php/AAAI/article/view/6215) generates decentralized protocols from commitments and checks correctness, safety, and liveness.
- [Tosca](https://www.ijcai.org/proceedings/2017/37) addresses alignment of commitments across decentralized participants.

The lesson for AWP is that record names and lifecycle arrows are insufficient. Normative transition tables, roles permitted to cause each transition, timeouts, rejection paths, cancellation semantics, and locally checkable conformance are part of the protocol.

### 1.3 Isolated execution and evidence-based integration

The strongest recent software-engineering result is prosaic but important: isolate concurrent work and integrate it through executable checks. CAID uses a dependency-aware central plan, asynchronous execution in isolated workspaces, branch-and-merge, and test-based verification. It reports material gains over single-agent baselines on two long-horizon benchmarks.

- [Effective Strategies for Asynchronous Software Engineering Agents](https://arxiv.org/abs/2603.21489) identifies Git worktrees, commits, merges, dependency-aware delegation, and executable verification as effective coordination primitives.

This supports AWP's choice to complement Git rather than replace it. AWP should describe semantic intent and integration conditions; Git adapters should provide immutable bases, isolated branches/worktrees, patches, merge ancestry, and resulting revisions.

### 1.4 Shared verified context and workspace awareness

DeLM coordinates decentralized workers through a shared task queue and compact verified results rather than routing every update through a central agent. Earlier workspace-awareness research reached a related conclusion for humans: exposing ongoing changes and dependency violations earlier produces earlier conflict detection and fewer unresolved conflicts.

- [DeLM](https://arxiv.org/abs/2606.10662) provides evidence for asynchronous coordination through shared, verified context.
- [Palantir](https://digitalcommons.unl.edu/csearticles/104/) found that awareness of parallel changes and dependency conflicts improves the timing and outcome of conflict resolution.

This validates the role of a portable AWP snapshot plus event history. It also implies that the shared context must be compact, queryable, causally fresh, and explicit about what has and has not been verified.

### 1.5 Measurement, enforcement, and formal verification

The field is moving away from judging a team only by whether a final patch passes.

- [MAST](https://arxiv.org/abs/2503.13657) identifies 14 failure modes in specification/system design, inter-agent misalignment, and verification/termination.
- [CooperBench](https://arxiv.org/abs/2601.13295) isolates collaborative coding conflicts and demonstrates the coordination penalty.
- [TeamBench](https://arxiv.org/abs/2605.07073) uses operating-system-enforced role separation. It finds that verifiers approve 49.4% of grader-rejected work, showing that an agent's approval is not strong evidence by itself.
- [FeatureBench](https://arxiv.org/abs/2602.10975) measures multi-commit feature development with execution-based evaluation; its reported frontier success rates remain low.
- [ChainSWE](https://arxiv.org/abs/2607.02606) measures sequential dependent changes in a persistent codebase.
- [TraceFix](https://arxiv.org/abs/2605.07935) uses TLA+ counterexamples to repair coordination protocols and reports substantially less deadlock/livelock than prompt-only coordination.

These are recent results, several still preprints or newly published, so their numerical claims should be treated as promising rather than settled. Collectively, however, they strongly favor structural enforcement, deterministic evidence, explicit failure diagnostics, and protocol-level testing.

## 2. AWP compared with the frontier

| Capability | AWP 0.5.0 | Frontier expectation | Assessment |
|---|---|---|---|
| Durable project context | Core snapshot and events | Shared compact context with provenance | Strong foundation |
| Work declaration | Work intents | Intent required before mutation in protected settings | Present, not enforceable |
| Concurrent isolation | Deferred to adapters/Git | Worktree or equivalent isolation | Correct boundary; adapter profile missing |
| Conflict model | Physical and semantic overlap | First-class conflict objects and deterministic concurrency checks | Semantically strong; mechanically incomplete |
| Negotiation | Mentioned in overlap and contracts | Typed messages, acknowledgement, deadlines, terminal outcomes | Major gap |
| Contracts | Versioned interfaces and participant adoption | Explicit obligations, acceptance/quorum, lifecycle guards | Strong concept; incomplete state model |
| Preconditions | Broad list of possible conditions | Typed, machine-evaluable predicates bound to a base | Major gap |
| Verification | References to executions/tests | Independent, reproducible evidence bound to exact inputs and environment | Partial |
| Staleness | Revised contracts may stale dependents | Mechanical dependency propagation | Missing algorithm |
| Live exclusion | Coordinator term/epoch mentioned | OCC or leases with compare-and-swap/fencing semantics | Underspecified |
| Governance | Authority caveats | Principals, policy, arbitration, audit, security profiles | Major gap |
| Protocol safety | Recovery prose | Normative transitions plus safety/liveness model checking | Missing |
| Evaluation | No coordination benchmark | Conflict-specific, longitudinal, ablated evaluation | Missing |

## 3. Recommended target architecture

AWP should use one durable event history with three logical planes. These are views and responsibilities, not separate competing ledgers.

```text
Project meaning                 Concurrent work                 External enforcement
---------------------------     ----------------------------    ---------------------------
goals                           intents                         Git branches/worktrees
semantic registry              claims and acknowledgements     forge checks/reviews
contracts and invariants   ->  overlaps and negotiations  ->   CI/test/static analysis
dependency graph                leases and coordinator terms    policy/authority systems
decisions                       integration plans               deployment systems
        \___________________________ AWP events ___________________________/
                                  |
                    deterministic snapshot/projection
                                  |
                 resume, handoff, audit, cross-agent transfer
```

### 3.1 Semantic plane

Add a project-scoped registry of stable identifiers for interfaces, behaviors, invariants, state fields, schemas, tests, deployment surfaces, and compatibility promises. Each definition needs an owner, revision, aliases, evidence links, and lifecycle. Without a registry, two agents can use different identifiers for the same concept or the same identifier for different concepts, defeating semantic overlap detection.

Contracts should express observable obligations rather than internal implementation preferences. A participant's adoption must be separate from the contract's global status. Acceptance policy should say whether unanimity, named-party consent, an owner decision, or another quorum is required.

### 3.2 Coordination plane

Make the following first-class records:

- `intent`: desired outcome, declared scopes, base, dependencies, termination condition;
- `claim`: actor assertion over a scope, including relied-upon reads;
- `observed_scope`: mechanically extracted files, symbols, schemas, dependencies, and tests touched by actual work;
- `overlap`: classification, basis, confidence, policy result, owner, and required acknowledgements;
- `negotiation`: proposals, counterproposals, accept/reject/abstain, deadline, escalation, and outcome;
- `commitment`: debtor, creditor or beneficiary, trigger, promised condition, deadline, discharge/violation evidence;
- `dependency`: typed edge between intents, contracts, change sets, or verifications;
- `integration`: ordered inputs and a reproducible result.

Every lifecycle needs a complete transition table. Each row should define source state, event, permitted actor/authority, required evidence, target state, emitted diagnostics, and effects on dependents. Unknown or concurrently modified records should fail closed only in declared enforced profiles; advisory profiles should surface risk without pretending to block external work.

### 3.3 Enforcement plane

Keep external mutation authority outside AWP, but specify adapter contracts that can prove what happened:

- a Git adapter binds an intent/change set to repository identity, full base revision, branch/worktree, patch digest, and result revision;
- a scope analyzer compares declared scopes/effects with the actual diff and dependency graph;
- precondition evaluators return typed pass/fail/unknown results with observed values;
- verification adapters bind command, environment/toolchain, exact revision, inputs, outputs, exit status, logs, and artifact digests;
- authority adapters report whether an actor may approve, integrate, or deploy, without turning a self-asserted AWP record into permission.

The system must distinguish four statements that are often collapsed: **declared by an agent**, **observed by a tool**, **verified by a check**, and **authorized by a principal**.

## 4. Protocol changes with the highest value

### P0: Make offline coordination deterministic

This should be the next Coordination revision's minimum viable core.

1. Define normative state machines for intents, overlaps/conflicts, contracts, change sets, negotiation, and integration.
2. Define a deterministic event fold/projection, including concurrent-event behavior and invalid-transition diagnostics.
3. Split preconditions into `mechanical` and `asserted`; a mechanical precondition has a registered evaluator and an evidence result.
4. Bind every verification to exact repository revision, change-set version, contract revisions, tool/environment identity, and evidence digest.
5. Define dependency-based staleness propagation and recovery (`revalidate`, `rebase`, `supersede`, or `withdraw`).
6. Add common diagnostics and positive/negative conformance fixtures.

This tier works from files and source control alone and directly improves cross-machine handoff and project re-entry.

### P1: Detect semantic coordination failures early

1. Add the semantic registry and alias rules.
2. Require observed-versus-declared scope comparison at change-set publication.
3. Create a reverse index from a scope to writers and relied-upon readers.
4. Make overlap acknowledgement explicit; record which parties saw, accepted, rejected, or failed to answer.
5. Add a policy matrix mapping overlap classification and confidence to warn, negotiate, order, block, or escalate.
6. Derive integration order from dependency edges and reject cycles unless an explicit combined-integration plan resolves them.

This tier is AWP's most valuable differentiator from general A2A and workflow frameworks.

### P2: Add safe live coordination

1. Define optimistic concurrency control for coordination records using expected revision or causal frontier.
2. Specify coordinator identity, epoch, protected namespace, lease generation, and monotonic fencing token.
3. Require protected adapters to reject mutations carrying an older fencing token; an epoch in a file is not enforcement.
4. Specify heartbeat, timeout, cancellation, retry/idempotency, starvation policy, deadlock detection, and arbitration.
5. Add authenticated actor/principal identity, signatures where needed, replay protection, confidentiality/redaction policy, and audit requirements.
6. Define exactly what remains safe during a partition. If the enforcement path cannot validate the coordinator, the system must not call the lease exclusive.

This tier should be optional. It requires a live service or an existing forge/CI authority capable of enforcing it.

### P3: Prove utility rather than adding vocabulary

Build a AWP coordination benchmark and reference adapter before expanding further. Compare:

- single agent;
- multiple agents with chat only;
- isolated Git branches/worktrees plus tests;
- AWP P0;
- AWP P0 + P1;
- AWP P0 + P1 + live enforcement.

Use tasks with same-file textual conflicts, different-file semantic conflicts, relied-upon reads, interface migration, stale bases, under-declared scope, agent crash, delayed messages, concurrent updates, contract revision, integration cycles, and malicious or unauthorized assertions.

Measure final correctness, semantic conflicts caught before merge, false-positive conflict rate, stale work avoided, successful parallel speedup, coordination token/time overhead, verifier false accepts, recovery after failure, and context-reconstruction cost on a new machine.

## 5. Conformance levels

A tiered model prevents the optional module from becoming unusably heavy.

| Level | Name | Required behavior |
|---|---|---|
| C0 | Portable | Parse and preserve coordination records; show active intents, contracts, risks, and evidence |
| C1 | Deterministic | Validate transitions, typed preconditions, verification binding, staleness, and diagnostics |
| C2 | Aware | Maintain semantic registry, compare declared/observed scope, analyze relied-upon reads, require overlap acknowledgement |
| C3 | Enforced | Provide authenticated live coordination, OCC, fencing, expiry, policy enforcement, and auditable arbitration |

An implementation must never imply a stronger level than it actually enforces. A plain Markdown/JSON bundle can be C0 or C1. C3 cannot be achieved by convention alone.

## 6. Positioning relative to adjacent protocols

AWP should publish a precise non-competition statement:

- **MCP connects an agent to tools and resources.**
- **A2A transports delegated tasks, messages, status, and artifacts between agents.**
- **MPAC coordinates operations and governance among multiple principals over shared state.**
- **Git records and combines source revisions.**
- **AWP preserves project meaning and evidence across sessions and systems, and specializes shared-codebase coordination through semantic scopes, contracts, preconditions, and integration history.**

AWP can be carried in A2A artifacts, manipulated through MCP tools, mapped to MPAC operations/conflicts, and anchored to Git revisions. Its portable representation should remain useful when none of those services is running.

Because MPAC now occupies much of the general-purpose multi-principal coordination space, AWP should avoid claiming novelty merely for intents, conflicts, governance, Lamport-style causality, or OCC. The credible novel combination is:

1. agent-agnostic, durable project re-entry and handoff;
2. repository-bound semantic concurrency awareness;
3. change-set preconditions and contract adoption;
4. evidence- and authority-aware integration across heterogeneous tools;
5. graceful operation from static portable state through live enforcement.

## 7. Concrete recommendation

Do not immediately publish a broad AWP 0.6 specification. First create a **Coordination 0.3 design package** containing:

1. the six normative state machines and transition tables;
2. JSON Schemas for the P0 records and events;
3. deterministic projection and staleness algorithms;
4. a Git/worktree plus test-runner reference adapter;
5. at least 20 adversarial conformance fixtures;
6. a small paired-agent benchmark derived from CooperBench-style conflict cases;
7. an explicit mapping to A2A and MPAC.

Once P0 and a narrow slice of P1 work end to end, promote them into the next AWP family version. Keep live leases experimental until fencing and enforcement are demonstrated. This sequence would move AWP from a thoughtful coordination ontology to a testable protocol while preserving its most important property: useful durable state that is independent of any one model, agent runtime, host, or source-control service.

## 8. Bottom line

AWP's coordination direction is valid and timely, but “state of the art” now requires more than rich records. It requires executable semantics, enforced boundaries, causally safe updates, verification tied to exact state, explicit governance, formal protocol checks, and empirical comparison against chat-only and Git-only baselines.

The highest-leverage next move is to make the smallest coordination tier deterministic and testable. The semantic registry and declared-versus-observed scope check should follow immediately. Live multi-agent locking is valuable, but it is the third step—not the foundation.
