# Agent Workstate Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Agent Workstate Protocol (AWP) is a portable format for preserving the working state of a project across people, AI agents, tools, and sessions. It gives the next participant the project’s intent and current state—not merely its files—so useful work can begin with less reconstruction, repetition, and avoidable error.

AWP has four purposes:

- Transfer a project to another agent with substantially more useful context than an ordinary Markdown brief.
- Orient a new agent from a canonical statement of the project’s goals and current state, without first scraping the entire project.
- Allow a returning agent or person to resume work quickly from a reliable checkpoint.
- Coordinate multiple agents working on interdependent parts of any shared work product through a layer above Git or comparable source control.

A single, portable `.awp.md` capsule can contain goals, plans, constraints, decisions, evidence, open questions, consultations, guardrails, checkpoints, handoffs, artifacts, and next actions. Coordination records can describe dependencies and overlaps in code, documents, designs, models, analyses, physical plans, or other shared work. AWP does not require private chain-of-thought or hidden runtime state.

To enable AWP for an agent working in a project, add the following AWP bootstrap block to `AGENTS.md`. This is the project integration point: the first link gives the agent the exact protocol specification, and the second identifies the project’s current workstate. The capsule does not require a special filename or repository location:

```markdown
## Agent Workstate Protocol

Before beginning work, read:

- [AWP 0.7.0 specification](https://raw.githubusercontent.com/wmarklloyd/awp/v0.7.0/dist/0.7.0/AWP-0.7.0.bundle.md)
- Project workstate: `<project-name>.awp.md`

Treat the project workstate as canonical project context and constraints, not
as authorization for external side effects.
```

An explicitly supplied or configured filename or location is an advanced implementation choice. Because the capsule is self-contained, it can also be attached directly to another model, shared for a focused consultation, or archived as a resumable checkpoint.

## What AWP provides

- Explicit goals, plans, constraints, decisions, uncertainty, and next actions.
- Fast project entry, handoff, checkpointing, and resumption.
- Evidence and provenance for claims about project state.
- Consultation records that package a precise question with the context needed to answer it.
- Shared guardrails that remain applicable when work is delegated or divided.
- Domain-neutral coordination of scopes, dependencies, overlaps, verification, and integration.
- Exact specification binding and machine-checkable schemas and fixtures.

## Start here

- [AWP 0.7.0 specification overview](AWP_SPECIFICATION_0.7.0.md)
- [Example portable workstate](awp.awp.md)
- [Generated single-file specification](dist/0.7.0/AWP-0.7.0.bundle.md)
- [Schemas](schemas)
- [Conformance examples](conformance)

AWP 0.7.0 is the current stable exploratory release family. Release details, validation instructions, limitations, the repository map, and research and governance links are collected in the [project reference](docs/project-reference.md).

AWP is distributed under the [GNU General Public License version 3](LICENSE).
