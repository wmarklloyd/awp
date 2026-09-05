# Agent Workshare Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

When a session ends, the part of a project that was never written down ends with it: why a decision was made, what has actually been verified, which constraints must not be broken, and what the next participant should do first. The files survive; the working state does not.

**Agent Workshare Protocol (AWP) is a portable, transport-independent format for that working state.** A single self-contained capsule carries a project's intent and current position across people, AI agents, tools, and sessions — without requiring private chain-of-thought, a full conversation transcript, or hidden runtime state. AWP assumes the agents reading it already have their own working environments; it supplies the shared semantics they lack.

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

Core is required; Capsule, Handoff, Artifact, Synchronization, Coordination, Cooperation, and Security are separately declared modules, so a producer adopts only what it needs. Every record type is backed by a versioned JSON Schema and executable conformance fixtures.

## Cooperation is a first-class AWP feature

AWP defines cooperation as an explicit profile choice, not an informal promise between agents. The Cooperation Contracts family describes what participants can expect while exchanging perspectives, reviewing work, delegating bounded tasks, synthesizing results, and changing shared project artifacts. A project should disclose its selected contract, effective interaction policy, operating mode, and material limitations at entry.

- **COOP-0 — substantive uncoordinated collaboration.** Participants may exchange capsules, consultations, critiques, alternative analyses, and synthesized conclusions. It supports using different models or people for independent points of view, but it makes no contract-level guarantee of participant discovery, scope reservation, conflict prevention, or contemporaneous incorporation.
- **COOP-1 — default small-group cooperation.** Participants use bounded leases, atomic guarded-scope announce-and-check, compatible concurrent work, durable checkpoint and exit handoff, and bounded feedback loops. It requires no separate database or continuously running service and is intended to support more than two participants within a tested operating envelope.
- **COOP-2 — aware, enforced, and scalable cooperation.** COOP-2 adds semantic scope awareness, integration assurance, authenticated protected mutation, epochs and fencing, and a declared higher-scale or higher-performance operating envelope. It may use a database, broker, sharded registry, or other service. The draft specifies the contract, but this repository does not yet implement or claim it.

COOP is AWP's single cumulative cooperation and coordination conformance ladder. The Coordination module supplies the records and mechanisms used by the contracts; it does not define a competing `C0`–`C3` axis in the 0.8 draft. Selecting COOP-1 does not imply COOP-2 authority, fencing, authentication, semantic conflict detection, or any untested participant capacity. The [Cooperation Contracts specification](spec/drafts/0.8.0/cooperation-contracts.md) defines the contracts and their evidence requirements.

## Adopting AWP

**Bootstrap a project.** The integration point is a link in `AGENTS.md` — not merely the presence of a capsule in the repository. Add:

```markdown
## Agent Workshare Protocol

Before beginning work, read:

- [AWP 0.6.0 specification](https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md)
- Project workstate: `<project-name>.awp.md`

Treat the project workstate as canonical project context and constraints, not
as authorization for external side effects.
```

The first link binds the agent to an exact, immutable specification; the second identifies the project's current workstate. Do not substitute a moving branch URL. A sandboxed or offline project may point both at a repository-relative copy of the same bundle. An explicitly configured capsule path or a discovery document such as [`.awp.json`](.awp.json) is an advanced option, not a prerequisite.

Cooperation Contracts are currently an AWP 0.8 working-draft feature, not part of the immutable 0.6 release. A project experimenting with COOP should bind its agents and capsule to the same exact 0.8 draft snapshot; a moving `main` URL is suitable for active co-development only, not a stable conformance claim.

**Hand a capsule to an agent directly.** Because a capsule is self-contained, it can be attached to a model with no repository access at all — as a project brief, a checkpoint to resume from, or an archived record of how a decision was reached.

**Keep re-entry bounded.** A host can validate the complete capsule without placing its entire history in the model context. The experimental `selective-reentry-v1` reference tool emits the generated briefing, active Resume/Handoff/checkpoint, ordered `read_first` records, and compact required-artifact descriptors:

```bash
python tools/awp_reentry.py --project .
```

It reports `incomplete` or `budget_exceeded` rather than silently dropping required context. See the [re-entry cost evaluation](docs/reentry-cost-evaluation.md) for the measured reduction on this repository.

**Update the workstate through its host-owned projector.** For a semantic checkpoint or a no-change exit, submit a JSON request to the canonical writer:

```bash
python tools/awp_workstate.py checkpoint --request checkpoint.json
```

The writer verifies the whole-Capsule compare-and-swap base, renders the briefing, performs atomic replacement, and returns a receipt. Use `python tools/awp_workstate.py recover` after an interrupted publication and `python tools/awp_workstate.py verify --full` for an explicit historical artifact audit. Models supply semantic facts; the host owns serialization and digests.

**Ask a focused question.** A detached consultation capsule packages a question with its context and review constraints. [`consultations/readme-refinement.awp.md`](consultations/readme-refinement.awp.md) is a working example; it uses 0.8.0 draft-only semantics and must be read against the local draft bundle.

**Use COOP-1 when several agents cooperate on one project.** The experimental [COOP-1 Cooperation Contract](spec/drafts/0.8.0/cooperation-contracts.md) combines guarded-scope coordination with bounded review, critique, alternative-model, delegation, and synthesis interactions. Its default binding requires no separate database or service, but a COOP-1 claim requires atomic incompatible-scope blocking, bounded feedback loops, durable handoff, and recovery evidence. The service-free local ledger adapter ([`tools/awp_coordination.py`](tools/awp_coordination.py)) and optional local presence registry ([`tools/awp_presence.py`](tools/awp_presence.py)) are reusable single-host reference components, not a complete COOP-1 implementation.

The default workflow requires no daemon:

```bash
python tools/awp_coordination.py status
python tools/awp_coordination.py lease-enter --actor actor:agent-one --scope src/
python tools/awp_coordination.py begin --actor actor:agent-one --goal goal:example --summary "Implement the requested change" --scope src/ --policy block
python tools/awp_coordination.py refresh --actor actor:agent-one
python tools/awp_coordination.py complete --actor actor:agent-one --intent-id intent:<generated-id> --reason "Implementation and verification completed" --output artifact:change
python tools/awp_coordination.py lease-release --actor actor:agent-one --lease-id lease:<generated-id> --handoff awp.awp.md --reason "Final handoff published"
```

`lease-enter` creates a bounded advisory participant-liveness record; `lease-renew`, `lease-release`, and `leases` renew, release, and inspect it. `begin` atomically publishes scope and intent events and reports known incompatible overlaps. The reference CLI defaults to a warning policy; guarded `--policy block` announcements require an active lease and record a conflicting intent as proposed until `resolve --disposition partition|order|withdrawal|escalation` records the outcome and `activate` records the valid lifecycle transition. `lease-release` rejects an active linked intent and requires `--handoff` to name an existing repository artifact whose digest is recorded in the release receipt. The adapter prefers the Git common directory so linked worktrees share one ledger. If sandbox policy prevents that write, it uses the ignored `.awp-runtime/` directory and reports that its reach is worktree-local; an explicit `--ledger` starts as configured-unverified until participants compare the stable store identity. If neither location is safe, it reports `AWP-COORD-LEDGER-UNAVAILABLE` with snapshot-only or unavailable operational mode. The narrow `local-ledger-awareness-v1` profile is a component, not a complete COOP-1 binding, and it does not provide COOP-2 semantic awareness or protected enforcement.

## Status

| Track | Version | Status | Entry point |
|---|---:|---|---|
| Stable specification | 0.6.0 | Exploratory release | [Family overview](AWP_SPECIFICATION_0.6.0.md) |
| Active development | 0.8.0 | Working draft; not a release | [Draft overview](spec/drafts/0.8.0/index.md) |
| Cooperation Contracts | 0.1.0 | Experimental single ladder: COOP-0, COOP-1, and COOP-2 | [Cooperation Contracts](spec/drafts/0.8.0/cooperation-contracts.md) |
| Coordination mechanisms | 0.3.0 released module / 0.5.0 draft | Normative but experimental; no separate draft conformance ladder | [Draft mechanisms](spec/drafts/0.8.0/coordination.md) |

The 0.6.0 release is fixed by the immutable tag [`v0.6.0`](https://github.com/wmarklloyd/awp/tree/v0.6.0). Draft material must not be represented as a published AWP release.

AWP is not an agent runtime, source-control system, artifact store, authentication or authorization system, consensus protocol, or policy engine. Imported workstate describes claims and requested actions; it never grants authority for external side effects.

The repository provides normative prose, JSON Schemas, generated bundles, positive and negative conformance fixtures, reproducibility tests, Cooperation Contract definitions, a service-free local ledger-awareness reference adapter, an informative transport-neutral deterministic projector foundation, and a synthetic coordination-awareness pilot. It does **not** yet provide a production general-purpose reader/writer, a complete cross-record validator, a semantic-scope analyzer, a live coordinator, a complete COOP-1 or COOP-2 binding, two independent implementations, or empirical evidence that AWP improves real multi-agent outcomes. That distinction is deliberate and is maintained throughout the repository.

## Start here

- [Generated single-file specification](dist/0.6.0/AWP-0.6.0.bundle.md) — the whole stable family in one file
- [Example portable workstate](awp.awp.md) — this project's own capsule
- [Architecture overview](docs/architecture.md) and [design rationale](docs/design-rationale.md)
- [Schemas](schemas) and [conformance fixtures](conformance)
- [AWP 0.8.0 working draft](spec/drafts/0.8.0/index.md)
- [Project reference](docs/project-reference.md) — release details, validation commands, repository map, research position, and governance

AWP is distributed under the [GNU General Public License version 3](LICENSE). The licensing scope may be revisited before a stable 1.0 specification.
