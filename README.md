# Agent Workstate Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Agent Workstate Protocol (AWP) is a portable, transport-independent format for giving people and AI agents a shared understanding of a project. It captures the semantic state that source code, Git history, tickets, and an ordinary README usually leave scattered or implicit: the project goal, plans, constraints, decisions, evidence, uncertainty, current checkpoint, authority boundaries, and the next safe action.

Its unit of exchange is a self-contained Markdown workstate capsule, conventionally named `<project-name>.awp.md`. A capsule can travel with a project, be handed to another model or person, and provide useful orientation without requiring them to scrape the entire repository or infer intent from history.

AWP also provides an experimental coordination layer for work that is interdependent above source control. That applies to code, but is deliberately broader: agents can coordinate changes to a design, document, model, analysis, physical plan, or any other shared work product. The protocol represents scopes, dependencies, overlaps, contracts, verification, staleness, integration state, shared guardrails, and consultations.

## Why AWP exists

AWP provides a common format for agents and users that already have their own tools and environments:

1. Send another agent a project description that is substantially richer than a conventional Markdown brief.
2. Let a new agent enter a project from a canonical source of context, goals, constraints, and current state instead of first scraping the whole project.
3. Let an agent or person re-enter a project and quickly regain context from the same canonical source.
4. Let multiple agents coordinate interdependent work through a layer above Git or comparable source control.

## What a workstate can carry

- Project intent: goals, plans, constraints, acceptance criteria, priorities, and unresolved questions.
- Decision-quality context: claims with provenance and confidence, evidence, observations, conclusions, assumptions, and uncertainty.
- Continuity: checkpoints, handoffs, resumable next actions, artifacts, and freshness information.
- Safe collaboration: declared authority, explicit requests for action, consultations with an outside model or expert, and shared guardrails that continue to apply when work is delegated or divided.
- Work-product coordination: physical and semantic scopes, dependencies, overlap findings, preconditions, contracts, verification results, and escalation to user-mediated arbitration when agents cannot safely resolve an interaction themselves.

AWP separates a claim from proof, a request from authorization, and source-control conflicts from semantic coordination conflicts. It does not require agents to disclose private chain-of-thought or hidden runtime state.

## Start using it

For a project, create or adopt one canonical capsule such as `my-project.awp.md` and keep it with the project. Its YAML front matter identifies the workstate, format, discovery mode, and exact governing AWP specification; the body contains a generated briefing plus structured records and references.

An AWP-aware agent should:

1. Open the project capsule first.
2. Read its generated briefing for the project’s current purpose, state, constraints, and recommended next action.
3. Consult the manifest, snapshot, handoff, consultations, and referenced artifacts only as needed.
4. Verify relevant artifact identities and freshness before relying on them.
5. Treat the capsule as context and constraints, not as authorization for external side effects.

This repository’s working example is [`awp.awp.md`](awp.awp.md). The capsule is self-discovering: there is no separate discovery JSON file to keep in sync.

To implement support, begin with the required Core record model and the self-contained Capsule format, then add optional modules as your use case needs them. The stable specification, schemas, fixtures, and validators in this repository are intended to make that path concrete rather than merely descriptive.

## Features at a glance

| Capability | What it gives a project |
|---|---|
| Portable Markdown capsule | A single file that can be shared, archived, or supplied to another agent as project context. |
| Core workstate | Goals, plans, constraints, decisions, claims, evidence, uncertainty, checkpoints, and next actions. |
| Resumption and handoff | A canonical way to bring a new or returning contributor up to speed. |
| Consultation records | A bounded, reproducible record for asking another model or expert about a specific problem with enough context to be useful. |
| Shared guardrails | Portable safety and policy constraints that apply in solo work and across collaborating agents. |
| Domain-neutral coordination | A way to describe and negotiate interdependent work products, not just code files or Git branches. |
| Schemas and fixtures | Machine-checkable structures and positive/negative examples for implementers. |

## AWP 0.7.0

AWP 0.7.0 is the current stable exploratory release family. It adds the self-contained single-file capsule, explicit specification binding, domain-neutral coordination, shared guardrails, and consultation records. AWP 0.6.0 remains available as the preceding stable exploratory release.

Read the [0.7.0 family overview](AWP_SPECIFICATION_0.7.0.md), the [released module index](spec/0.7.0/index.md), or the generated [single-file bundle](dist/0.7.0/AWP-0.7.0.bundle.md). Once the immutable tag is created, the pinned external bundle reference will be:

```text
https://raw.githubusercontent.com/wmarklloyd/awp/v0.7.0/AWP_SPECIFICATION_0.7.0.bundle.md
```

Use an exact released version rather than a moving branch URL. Offline or sandboxed projects may instead reference a repository-relative copy of the exact bundle.

## Appendix: protocol boundaries and current evidence

AWP is a format and a specification; it is not an agent runtime, source control system, artifact store, authentication or authorization system, distributed-consensus system, or project policy engine. A workstate can describe a requested action or constraint, but it does not grant authority to perform external side effects.

The repository currently supplies modular normative prose, versioned JSON Schemas, generated bundles, executable positive and negative conformance fixtures, reproducibility tests, and a synthetic coordination-awareness instrumentation pilot. It does not yet supply a production reader/writer, complete cross-record validator, semantic-scope analyzer, live coordinator, two independent implementations, or empirical evidence that AWP improves real multi-agent outcomes.

## Appendix: validation and repository map

Python 3.10 or later is required. Install the pinned development dependency and run the release checks:

```bash
python -m pip install --requirement requirements-dev.txt
python tools/validate_spec_0_7.py
python tools/validate_conformance.py
python -m unittest discover -s tests -v
```

```text
awp.awp.md                  Current portable project workstate
AWP_SPECIFICATION_0.7.0.md Stable 0.7.0 family overview
spec/0.7.0/                 Released 0.7.0 module specifications
schemas/                    Versioned JSON Schemas
conformance/                Positive, negative, and interoperability fixtures
dist/                       Generated bundles, manifests, and checksums
tools/                      Validators and reproducible-build utilities
docs/                       Architecture, rationale, decisions, and releases
```

For deeper material, see the [architecture overview](docs/architecture.md), [design rationale](docs/design-rationale.md), [project scope](docs/project-scope.md), [protocol evolution policy](docs/protocol-evolution.md), [decision records](docs/decisions), [contribution guidance](CONTRIBUTING.md), [governance](GOVERNANCE.md), [security policy](SECURITY.md), and [citation metadata](CITATION.cff).

AWP is distributed under the [GNU General Public License version 3](LICENSE).
