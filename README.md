# Agent Workstate Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

When a session ends, the part of a project that was never written down ends with it: why a decision was made, what has actually been verified, which constraints must not be broken, and what the next participant should do first. The files survive; the working state does not.

**Agent Workstate Protocol (AWP) is a portable, transport-independent format for that working state.** A single self-contained capsule carries a project's intent and current position across people, AI agents, tools, and sessions — without requiring private chain-of-thought, a full conversation transcript, or hidden runtime state. AWP assumes the agents reading it already have their own working environments; it supplies the shared semantics they lack.

## Four purposes

1. **Send a project, not a prompt.** Hand another agent a problem description that carries goals, constraints, accepted decisions, evidence, and open questions — substantially more durable state than an ordinary Markdown brief.
2. **Orient a new agent in one read.** Give an agent entering a project a canonical statement of what the project is for and where it stands, before it starts scraping a repository for context that was never recorded in the first place.
3. **Resume instead of reconstruct.** Let a returning agent or person continue from a recorded checkpoint — active goal, authority ceiling, verified artifacts, recommended next action — rather than rebuilding the situation from scratch.
4. **Coordinate above source control.** Let multiple agents negotiate interdependent changes to shared work products — code, documents, designs, models, analyses, schedules — at a semantic layer that Git's byte-level merge cannot see.

## What a capsule carries

A capsule is one portable `.awp.md` file. It has no required filename or location, and it can be committed, attached to a model, emailed, or archived unchanged. It records:

- **Intent** — goals, plans, constraints, guardrails, and the authority boundary that separates a request from permission to act on it.
- **Evidence** — claims with provenance and status, distinguishing what was reported, inferred, observed, verified, disputed, stale, or refuted.
- **Continuity** — an event history, generated snapshots and briefing prose, checkpoints, handoffs, and resumable next actions.
- **Consultations** — a precise question packaged with exactly the context needed to answer it, for a focused review by another model or person.
- **Coordination** — work intent, physical and semantic scopes, overlaps, contracts, preconditions, verification, staleness, and integration state, with bounded user-mediated arbitration when agents cannot safely resolve an interaction themselves.
- **Integrity** — an exact governing-specification binding, machine-readable module declarations, and digests over generated sections.

Core is required; Capsule, Handoff, Artifact, Synchronization, Coordination, and Security are separately declared modules, so a producer adopts only what it needs. Every record type is backed by a versioned JSON Schema and executable conformance fixtures.

## Adopting AWP

**Bootstrap a project.** The integration point is a link in `AGENTS.md` — not merely the presence of a capsule in the repository. Add:

```markdown
## Agent Workstate Protocol

Before beginning work, read:

- [AWP 0.6.0 specification](https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md)
- Project workstate: `<project-name>.awp.md`

Treat the project workstate as canonical project context and constraints, not
as authorization for external side effects.
```

The first link binds the agent to an exact, immutable specification; the second identifies the project's current workstate. Do not substitute a moving branch URL. A sandboxed or offline project may point both at a repository-relative copy of the same bundle. An explicitly configured capsule path or a discovery document such as [`.awp.json`](.awp.json) is an advanced option, not a prerequisite.

**Hand a capsule to an agent directly.** Because a capsule is self-contained, it can be attached to a model with no repository access at all — as a project brief, a checkpoint to resume from, or an archived record of how a decision was reached.

**Ask a focused question.** A detached consultation capsule packages a question with its context and review constraints. [`consultations/readme-refinement.awp.md`](consultations/readme-refinement.awp.md) is a working example; it uses 0.7.0 draft-only semantics and must be read against the local draft bundle.

**Coordinate several agents.** Coordination records describe scopes and dependencies above source control. The service-free local ledger adapter ([`tools/awp_coordination.py`](tools/awp_coordination.py)) is the default advisory path for writable AWP projects: agents publish intents before material writes, refresh before integration, and complete or withdraw their intents at handoff. The experimental local presence registry ([`tools/awp_presence.py`](tools/awp_presence.py)) optionally adds low-latency session discovery. Both profiles are single-host and advisory: neither authenticates principals, fences writes, or infers semantic overlap.

The default workflow requires no daemon:

```bash
python tools/awp_coordination.py status
python tools/awp_coordination.py begin --actor actor:agent-one --goal goal:example --summary "Implement the requested change" --scope src/
python tools/awp_coordination.py refresh --actor actor:agent-one
python tools/awp_coordination.py complete --actor actor:agent-one --intent-id intent:<generated-id> --reason "Implementation and verification completed" --output artifact:change
```

`begin` atomically publishes scope and intent events and reports known incompatible overlaps. The default policy warns; `--policy block` records a conflicting intent as proposed and reports an advisory block until `resolve` records its disposition and `activate` records the valid lifecycle transition. The adapter prefers the Git common directory so linked worktrees share one ledger. If sandbox policy prevents that write, it uses the ignored `.awp-runtime/` directory and reports that its reach is worktree-local; pass the same `--ledger` path to agents in other worktrees. If neither location is safe, it reports `AWP-COORD-LEDGER-UNAVAILABLE` with snapshot-only or unavailable operational mode. The narrow `local-ledger-awareness-v1` profile does not claim complete C1/C2/C3 conformance.

## Status

| Track | Version | Status | Entry point |
|---|---:|---|---|
| Stable specification | 0.6.0 | Exploratory release | [Family overview](AWP_SPECIFICATION_0.6.0.md) |
| Active development | 0.7.0 | Working draft; not a release | [Draft overview](spec/drafts/0.7.0/index.md) |
| Coordination | 0.3.0 released module / 0.4.0 draft | Normative but experimental | [Released module](spec/0.6.0/coordination.md) |

The 0.6.0 release is fixed by the immutable tag [`v0.6.0`](https://github.com/wmarklloyd/awp/tree/v0.6.0). Draft material must not be represented as a published AWP release.

AWP is not an agent runtime, source-control system, artifact store, authentication or authorization system, consensus protocol, or policy engine. Imported workstate describes claims and requested actions; it never grants authority for external side effects.

The repository provides normative prose, JSON Schemas, generated bundles, positive and negative conformance fixtures, reproducibility tests, a service-free local ledger-awareness reference adapter, an informative transport-neutral C1 projector foundation, and a synthetic coordination-awareness pilot. It does **not** yet provide a production general-purpose reader/writer, a complete cross-record validator, a semantic-scope analyzer, a live coordinator, two independent implementations, or empirical evidence that AWP improves real multi-agent outcomes. That distinction is deliberate and is maintained throughout the repository.

## Start here

- [Generated single-file specification](dist/0.6.0/AWP-0.6.0.bundle.md) — the whole stable family in one file
- [Example portable workstate](awp.awp.md) — this project's own capsule
- [Architecture overview](docs/architecture.md) and [design rationale](docs/design-rationale.md)
- [Schemas](schemas) and [conformance fixtures](conformance)
- [AWP 0.7.0 working draft](spec/drafts/0.7.0/index.md)
- [Project reference](docs/project-reference.md) — release details, validation commands, repository map, research position, and governance

AWP is distributed under the [GNU General Public License version 3](LICENSE). The licensing scope may be revisited before a stable 1.0 specification.
