---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: 4f8a1c9d7b3e52a6f0c481de93b72568
workstate_id: urn:uuid:awp-consultation-readme-refinement-2026-09-04
frontier:
  - evt:readme-refinement-consultation-cancelled
checkpoint: checkpoint:readme-refinement-consultation-cancelled
generated_at: 2026-09-09T17:37:25.630969Z
generated_digest: sha256:1f5c0a9e715e96f1ddb6913eae644b6f402718e9e9ea417fb16ed41a95f73720
---

<!-- awp:generated:start -->
# README refinement consultation

## Question

How should the AWP README be refined so that it is concise, technically credible to experienced computer engineers, and immediately useful to a person or agent evaluating or adopting the protocol?

## Requested response

Provide an editorial critique and a proposed replacement for any weak passages, especially the onboarding and activation instructions. Identify the highest-value changes to information architecture, terminology, claims, examples, and adoption guidance. Return recommendations or a patch; do not modify the repository, commit changes, or perform external actions.

## Important correction already made

The project integration point is an AWP bootstrap link in `AGENTS.md`. The README must not imply that AWP is enabled merely by placing a capsule in a repository. A capsule is the portable workstate artifact; it may be supplied, configured, attached, or stored according to the host project's workflow. The `AGENTS.md` link directs an agent to the version-pinned specification and, when available, the current project workstate.

## Review constraints

- Preserve the distinction between protocol conformance, project integration, and runtime support.
- Do not claim that AWP supplies an agent runtime, source control, authentication, authorization, consensus, or a live coordinator.
- Keep the specification reference version-pinned and distinguish stable release material from drafts.
- Preserve the distinction between context and authorization for external side effects.
- Do not require private chain-of-thought or an unbounded conversation transcript.
- Keep the README domain-neutral: it applies to code and other shared work products.
- Treat the current README as a draft for review. Do not assume that every sentence is accepted policy.

## Current README under review

```markdown
# Agent Workshare Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Agent Workshare Protocol (AWP) is a portable format for preserving the working state of a project across people, AI agents, tools, and sessions. It gives the next participant the project’s intent and current state—not merely its files—so useful work can begin with less reconstruction, repetition, and avoidable error.

AWP has four purposes:

- Transfer a project to another agent with substantially more useful context than an ordinary Markdown brief.
- Orient a new agent from a canonical statement of the project’s goals and current state, without first scraping the entire project.
- Allow a returning agent or person to resume work quickly from a reliable checkpoint.
- Coordinate multiple agents working on interdependent parts of any shared work product through a layer above Git or comparable source control.

A single, portable `.awp.md` capsule can contain goals, plans, constraints, decisions, evidence, open questions, consultations, guardrails, checkpoints, handoffs, artifacts, and next actions. Coordination records can describe dependencies and overlaps in code, documents, designs, models, analyses, physical plans, or other shared work. AWP does not require private chain-of-thought or hidden runtime state.

To enable AWP for an agent working in a project, add the following AWP bootstrap block to `AGENTS.md`. This is the project integration point: the first link gives the agent the exact protocol specification, and the second identifies the project’s current workstate. The capsule does not require a special filename or repository location:

```markdown
## Agent Workshare Protocol

Before beginning work, read:

- [AWP 0.6.0 specification](https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md)
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

- [AWP 0.8.0 working draft](../spec/drafts/0.8.0/index.md)
- [Example portable workstate](../awp.awp.md)
- [Generated single-file specification](../dist/0.6.0/AWP-0.6.0.bundle.md)
- [Schemas](../schemas)
- [Conformance examples](../conformance)

AWP 0.6.0 is the current stable exploratory release family. AWP 0.8.0 remains a working draft. Release details, validation instructions, limitations, the repository map, and research links are collected in the [project reference](../docs/project-reference.md).

AWP is distributed under the [GNU General Public License version 3](../LICENSE).
```
<!-- awp:generated:end -->

<!-- awp:4f8a1c9d7b3e52a6f0c481de93b72568:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-readme-refinement-2026-09-04",
  "title": "README refinement consultation",
  "created_at": "2026-09-04T16:12:36Z",
  "created_by": "actor:user",
  "completeness": "portable",
  "modules": [
    {"id": "urn:awp:core", "version": "0.8.0", "required": true},
    {"id": "urn:awp:capsule", "version": "0.4.0", "required": true}
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:4f8a1c9d7b3e52a6f0c481de93b72568:manifest:end -->

<!-- awp:4f8a1c9d7b3e52a6f0c481de93b72568:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-readme-refinement-2026-09-04",
  "frontier": ["evt:readme-refinement-consultation-cancelled"],
  "generated_at": "2026-09-09T17:37:25.630751Z",
  "records": {
    "consultations": [{"id":"consultation:readme-refinement","type":"consultation","revision":2,"question":"How should the AWP README be refined so that it is concise, technically credible to experienced computer engineers, and immediately useful to a person or agent evaluating or adopting the protocol?","status":"cancelled","requested_action":"Provide an editorial critique and proposed replacement prose or patch. Do not modify or commit repository files.","context":{"project":"Agent Workshare Protocol","specification":"AWP 0.8.0","integration_point":"An AWP bootstrap link in AGENTS.md","activation_correction":"Do not say that placing a capsule in a repository enables AWP. The capsule is a portable workstate artifact; AGENTS.md is the project bootstrap point.","review_scope":"The full current README is embedded in the generated briefing above.","known_limitations":["No production reader/writer is claimed","No live coordinator is claimed","No independent interoperability evidence is claimed"]},"read_first":[],"desired_output":"Ranked critique, precise replacement wording for weak passages, and a concise adoption-oriented README outline.","disposition":"Withdrawn by direct project-owner instruction on 2026-09-09: disregard this 2026-09-04 request rather than answer it. No editorial critique was produced."}]
  },
  "modules": {}
}
<!-- awp:4f8a1c9d7b3e52a6f0c481de93b72568:snapshot:end -->
