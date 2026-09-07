# Agent Workshare Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

The **Agent Workshare Protocol (AWP)** is a project-level communication and coordination system for AI agents—and for the people who direct or work alongside them. It gives agents a structured way to announce work, share relevant findings and evidence, ask bounded questions, report conflicts, and hand off responsibility, so every participant can act on a shared, current picture of the project.

One person can use AWP to direct several agents; a human team can use it with agents; and different agents can work together under one owner’s rules. Multiple agents do not imply multiple users. AWP makes the participants, their authority, their shared context, and the limits on their communication explicit.

Without that shared picture, projects lose their memory at the end of a conversation. The files remain, but the reasons behind them disappear: what the project was trying to achieve, which alternatives were rejected, what has actually been checked, which assumptions have gone stale, and what should happen next. AWP works alongside source-control systems such as Git, rather than depending on any one of them, to coordinate the purpose, dependencies, contracts, evidence, and authority behind changes. Standalone capsule exchange outside a project is intentionally deferred; the live draft focuses on keeping one project's shared work understandable and controllable.

## The goals

AWP has five practical goals:

1. **Preserve intent.** Keep goals, constraints, decisions, alternatives, risks, and requested actions together with the work they govern.
2. **Make handoffs reliable.** Let a new person or agent understand the current state and continue from a checkpoint instead of reconstructing the project from chat history.
3. **Coordinate meaning, not just files.** Record who is changing what, what each person relied on, where work may overlap, and what must be agreed before integration.
4. **Make exploration safe.** Allow promising but unapproved directions to be developed as persistent, shareable alternatives without changing the accepted project state.
5. **Keep people in control.** Separate advice from permission, evidence from assertion, and technical publication from authority to accept a change or create an external side effect.

## How AWP works

The central object is a **workstate**: one coherent body of ongoing work inside a project. The project keeps it in a canonical `.awp.md` capsule alongside its discovery file, source, and other project materials.

A capsule combines a human briefing with structured records for goals, constraints, decisions, claims, evidence, tasks, artifacts, checkpoints, and handoffs. Behind the readable view is an immutable event history. Snapshots and briefing text are generated views of that history, so a summary cannot silently replace the underlying record of what happened.

When an agent enters a project, a host can validate the complete capsule and present a compact entry view containing the current briefing, checkpoint, handoff, selected records, and artifact status. This reduces the context an agent normally needs to read while retaining an explicit `incomplete` or `budget_exceeded` result when required material cannot fit. The entry profile is a routing aid; the governing specification and the complete capsule remain authoritative.

AWP records provenance and epistemic status directly. A report, an inference, an observation, and a verified result are different things. A digest proves byte identity; it does not prove that content is true, safe, or authorized. Imported workstate is project context, never automatic permission to act.

## Cooperation levels

AWP lets a project choose how much agent communication and coordination it wants. The levels accumulate capability, but direct agent-to-agent communication is enabled only when the project explicitly authorizes it.

| Level | What it provides | How people stay in control |
|---|---|---|
| **COOP-1** | Small-group coordination through structured work announcements, declared physical scopes, bounded leases, atomic announce-and-check, conflict decisions, and durable exit handoffs | Material work-affecting decisions are surfaced to the user or named decision owner; agents do not start autonomous collaboration loops |
| **COOP-2** | Semantic scope awareness, dependency freshness, contracts, verification, and integration assurance | Direct agent collaboration is optional and requires recorded authorization, named participants, purpose, scope, and turn, tool, and token budgets |
| **COOP-3** | Authenticated protected mutation, epochs, fencing, and a declared operating envelope for scale | Protected infrastructure enforces authority and rejects stale or unauthenticated operations |

COOP-1 is intended to be useful for a small team without requiring a daemon or a large service. A local file or transactional ledger can provide the coordination record. COOP-2 may use richer services when semantic analysis is worth the cost. A2A is an optional communications and execution-control binding for the protected COOP-3 profile; it is not required for COOP-1 or COOP-2 use. The current draft does not define a separate standalone-capsule or cross-project collaboration level.

The [Cooperation Contracts specification](spec/drafts/0.8.0/cooperation-contracts.md) defines the claims, boundaries, and evidence required at each level. The [Coordination specification](spec/drafts/0.8.0/coordination.md) defines the records and mechanisms.

## Silos: explore a future without rewriting the present

A **silo** is a persistent alternative project state. It is useful when a team wants to explore a feature, architecture, research direction, or plan that has not yet been accepted by the project owners.

A silo has its own identity, purpose, goals, decisions, participants, history, owner, lifecycle, and optional work location. It begins from a pinned parent state, so everyone can see exactly what the exploration was based on. A silo may have one child silo, creating a clear single-parent hierarchy. Parent changes do not silently flow into children, and closing a parent does not erase a child’s history.

When an exploration produces something worth considering, it can submit selected results for **adoption** into the canonical project state or an ancestor silo. Adoption requires current destination approval, dependency-complete results, review of changed assumptions, and a recoverable publication receipt. Adopting one result does not automatically approve the entire feature or close the silo; the source can remain active and contribute again later.

Silos are separate from worktrees. A planning-only silo needs no separate checkout. A silo that edits shared files must use an isolated location or one common atomic coordination binding that covers every writer, including writers working on canonical state. Creating a silo never enables agent-to-agent communication, grants authority, or creates additional spending.

The [Silo Profile](spec/drafts/0.8.0/silos.md) contains the normative `silo-v1` rules, and the [silo schema](schemas/awp-silo-0.1.schema.json) describes its structural records.

## Using AWP in a project

The usual integration point is the project’s `AGENTS.md` (or equivalent agent-entry file). It should tell an entering agent which specification and workstate govern the project. For this repository, the current unreleased specification is explicitly included at:

```text
dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
```

A minimal project entry looks like this:

```markdown
## Agent Workshare Protocol

Before beginning work, read:

- AWP specification: `dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`
- Project workstate: `awp.awp.md`

Use the workstate as project context and constraints. It does not grant
authority for external side effects.
```

For a project that uses an earlier AWP format, use its immutable, version-pinned specification. The 0.8.0 material in this repository is the active working draft and is not yet a release. The [project history](docs/project-history.md) explains how the current design grew from those earlier formats.

The repository includes a generated [Agent Entry Core](dist/drafts/0.8.0/AWP-0.8.0-agent-entry-core.md) for bounded orientation. The reference commands are intentionally small:

```bash
# Validate the entry profile and receive the normal routed reading set
python tools/awp_spec_entry.py --verify
python tools/awp_spec_entry.py --route coordination

# Read the current project workstate through its bounded entry view
python tools/awp_reentry.py --project .

# Inspect the local coordination mode
python tools/awp_coordination.py status
```

For a semantic checkpoint, the host-owned projector accepts a request and calculates capsule digests and serialization. Agents provide semantic facts and evidence; the host protects the representation and returns a receipt:

```bash
python tools/awp_workstate.py checkpoint --request checkpoint.json
python tools/awp_workstate.py verify --full
```

The service-free local ledger and deterministic projector are reference components. They demonstrate the shape of the workflow, but they do not by themselves provide authenticated authority, semantic overlap analysis, protected writes, or a complete COOP conformance claim.

## Current state of this project

The active project is developing **AWP 0.8.0** as an unreleased working draft. The draft includes the COOP-1/2/3 work-coordination ladder, optional managed consultation, the `silo-v1` profile, A2A mapping for protected COOP-3 coordination, versioned schemas, generated bundles, and conformance fixtures.

The current checkout has passing specification validation, 80 repository tests, 41 structural conformance fixtures, and four deterministic projector fixtures. These checks establish repository consistency and structural behavior. They do not claim that the protocol has a production reader/writer, a complete semantic-scope analyzer, a silo runtime, a cross-workstate dependency evaluator, a shared-resource binding, an adoption publisher, a live coordinator, two independent implementations, or measured improvement in real multi-agent outcomes.

## Read next

- [AWP 0.8.0 working-draft overview](spec/drafts/0.8.0/index.md)
- [Generated 0.8.0 specification bundle](dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md)
- [Silo Profile](spec/drafts/0.8.0/silos.md)
- [Cooperation Contracts](spec/drafts/0.8.0/cooperation-contracts.md)
- [Coordination mechanisms](spec/drafts/0.8.0/coordination.md)
- [Architecture overview](docs/architecture.md)
- [Design rationale](docs/design-rationale.md)
- [Project history](docs/project-history.md)
- [Example project workstate](awp.awp.md)
- [Schemas](schemas)
- [Conformance fixtures](conformance)
- [Project reference](docs/project-reference.md)

AWP is distributed under the [GNU General Public License version 3](LICENSE).
