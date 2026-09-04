# Agent Workstate Protocol (AWP)

AWP is an exploratory protocol for preserving portable, semantic work state across human and AI-agent sessions. It gives collaborators a durable, authoritative description of a project's intent, decisions, evidence, progress, and next actions without requiring every new participant to reconstruct that context from the repository or chat history.

AWP is designed to:

- enable a user or agent to send another agent a project or problem description that preserves more durable semantic state than ordinary Markdown alone;
- provide a new agent with a clear, shared project orientation before it must inspect the wider repository;
- allow an agent or user to return to a project and resume from a recorded checkpoint rather than reconstructing its state from scratch; and
- enable multiple agents to negotiate interdependent code changes above the byte-level coordination provided by Git or similar source-control systems.

## Current status

The current release is **AWP 0.6.0**, an exploratory modular specification. It includes Coordination 0.3.0 as a normative but experimental module.

The specification, schemas, discovery document, portable workstate capsule, generated bundle, and validators are present and internally validated. This repository does **not** yet contain a production reader/writer, semantic-scope analyzer, test harness, or live coordination service.

## Start here

For a quick project re-entry, follow the repository discovery document:

1. Read [`.awp.json`](.awp.json) to locate the current workstate and specification.
2. Read [`conversation.awp.md`](conversation.awp.md) for the current goal, decisions, status, constraints, and recommended next action.
3. Use [`AWP_SPECIFICATION_0.6.0.bundle.md`](AWP_SPECIFICATION_0.6.0.bundle.md) when you need the complete self-contained specification.

If you are evaluating the protocol itself, begin with the concise family overview in [`AWP_SPECIFICATION_0.6.0.md`](AWP_SPECIFICATION_0.6.0.md) and the [`0.6.0 release notes`](AWP_0.6.0_RELEASE_NOTES.md).

## Use AWP from `AGENTS.md`

Projects adopting AWP can add the following guidance to their repository-level `AGENTS.md`:

```markdown
## Agent Workstate Protocol

This project uses Agent Workstate Protocol 0.6.0.

Before beginning work:

1. Read `.awp.json` from the repository root.
2. Resolve `current_workstate` relative to the repository root.
3. Read the current workstate's generated briefing, checkpoint, constraints,
   authority ceiling, and recommended next action.
4. Consult the complete specification only when protocol interpretation is
   necessary:

   https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md
```

The versioned raw specification URL is:

```text
https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md
```

The `v0.6.0` tag keeps this reference stable. To deliberately follow ongoing development on `main`, use:

```text
https://raw.githubusercontent.com/wmarklloyd/awp/main/AWP_SPECIFICATION_0.6.0.bundle.md
```

An `AGENTS.md` link is a reference, not an automatic file include. Agents need network access to retrieve the remote specification. Keep routine startup guidance concise and use the local `.awp.json` discovery document and workstate capsule for normal project orientation.

## Core model

AWP separates:

- intent and authority;
- execution and evidence;
- observations, inferences, and conclusions;
- causal event history and generated snapshots;
- source-control conflicts and higher-level semantic coordination.

The preferred exchange representation is a human-readable, single-file Markdown capsule such as `project.awp.md`. Machine-readable JSON sections preserve structured state while generated prose provides rapid human and agent orientation.

For project-named capsules, use `<project-name>.awp.md` by default. A producer may retain versioned archival copies as `<project-name>.v<revision>.awp.md`, such as `project.v2.awp.md`. The filename revision is only a human-facing label; the capsule metadata and `.awp.json` `current_workstate` pointer remain authoritative.

AWP does not require or attempt to preserve private chain-of-thought or hidden runtime state.

## Specification modules

The 0.6.0 family is split into independently versioned modules under [`spec/0.6.0`](spec/0.6.0):

- **Core** — records, events, identity, provenance, and epistemic status.
- **Capsule** — portable representations and repository discovery.
- **Handoff** — checkpoints, resume profiles, and continuation semantics.
- **Artifact** — artifact identity, location, integrity, and availability.
- **Synchronization** — event exchange and state reconciliation.
- **Coordination** — intents, scopes, conflicts, contracts, verification, and integration.
- **Security** — trust boundaries, authority, and safe import behavior.
- **Adapters** — mappings between AWP and external systems.

The module registry is [`spec/0.6.0/modules.json`](spec/0.6.0/modules.json). Normative JSON Schemas are in [`schemas`](schemas).

## Validation

Validation requires Python 3 and the [`jsonschema`](https://pypi.org/project/jsonschema/) package.

```powershell
python -m pip install jsonschema
python tools/validate_spec_0_6.py
```

Historical specification families and examples have separate validators:

```powershell
python tools/validate_spec_examples.py
python tools/validate_spec_0_4.py
python tools/validate_spec_0_5.py
```

To regenerate the self-contained 0.6.0 bundle from its source files:

```powershell
python tools/build_spec_0_6_bundle.py
python tools/validate_spec_0_6.py
```

Do not edit `AWP_SPECIFICATION_0.6.0.bundle.md` directly; it is a generated distribution artifact.

## Repository layout

```text
.awp.json                           Repository discovery document
conversation.awp.md                Current portable project workstate
AWP_SPECIFICATION_0.6.0.md         Current family overview
AWP_SPECIFICATION_0.6.0.bundle.md  Complete generated specification bundle
AWP_0.6.0_RELEASE_NOTES.md         Current release notes and test guidance
spec/0.6.0/                        Source specification modules
schemas/                           Normative JSON Schemas
tools/                             Bundle builder and validators
```

Older specifications and review documents are retained as historical design input. Unless you are investigating protocol evolution, use the 0.6.0 family as the current source.

## Recommended next experiment

The next milestone is a test environment for the `coordination-awareness` capability bundle:

1. Give two agents the same repository base.
2. Have each publish an intent and revision-pinned physical and semantic scopes.
3. Introduce both same-file physical conflicts and different-file semantic conflicts.
4. Compare chat-only, Git-only, and AWP-assisted runs.
5. Measure conflicts caught before implementation, false alarms, authoring overhead, coordination delay, successful integration, and stale-state recovery.

Start with coordination awareness rather than live leases or enforcement. The goal is to test whether AWP's scope and overlap model is usable before building stronger coordination machinery.

## Maturity and compatibility

AWP 0.6.0 is experimental and may change based on implementation experience. Coordination 0.2 records are not compatible with Coordination 0.3 through a version-number change alone; preserve historical events and create explicit imported or successor records when migrating.
