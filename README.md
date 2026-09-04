# Agent Workstate Protocol

[![Validate specification](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml/badge.svg)](https://github.com/wmarklloyd/awp/actions/workflows/validate.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Agent Workstate Protocol (AWP) is an exploratory, transport-independent format for preserving and exchanging semantic project state across human and software-agent sessions. It represents goals, constraints, decisions, evidence, uncertainty, authority boundaries, progress, and resumable next actions without requiring private chain-of-thought or hidden runtime state.

AWP also defines experimental coordination records above source control: work intent, physical and semantic scopes, overlaps, contracts, preconditions, verification, staleness, and integration state.

## Status

| Track | Version | Status | Entry point |
|---|---:|---|---|
| Stable specification | 0.6.0 | Exploratory release | [Family overview](AWP_SPECIFICATION_0.6.0.md) |
| Active development | 0.7.0 | Working draft; not a release | [Draft overview](spec/drafts/0.7.0/index.md) |
| Coordination | 0.3.0 stable-family module / 0.4.0 draft | Normative but experimental | [Released module](spec/0.6.0/coordination.md) |

The 0.6.0 release is identified by immutable tag [`v0.6.0`](https://github.com/wmarklloyd/awp/tree/v0.6.0). The 0.7.0 working draft introduces explicit governing-specification binding and separately versioned Discovery 0.2.0 semantics. Draft material must not be represented as a published AWP release.

## Scope

The [project scope](docs/project-scope.md) defines four target uses: portable project descriptions, rapid project orientation, checkpoint-based resumption, and coordination of interdependent changes above Git or comparable source-control systems.

AWP does not replace an agent runtime, source control, artifact storage, authentication, authorization, distributed consensus, or project policy. Imported workstate describes claims and requested actions; it does not grant authority for external side effects.

## Evidence and limitations

The repository currently provides:

- modular normative prose and machine-readable module registries;
- JSON Schemas for structural validation;
- generated self-contained specification bundles;
- executable positive and negative conformance fixtures;
- deterministic bundle-reproducibility tests;
- a synthetic coordination-awareness instrumentation pilot.

It does not yet provide a production reader/writer, complete cross-record validator, semantic-scope analyzer, live coordinator, two independent implementations, or empirical evidence that AWP improves real multi-agent outcomes. The distinction between demonstrated properties and research hypotheses is intentional.

## Project entry

An AWP-aware agent or tool starts at [`.awp.json`](.awp.json), follows `current_workstate`, and reads the capsule briefing and checkpoint. This repository’s current workstate is [`awp.awp.md`](awp.awp.md).

The released 0.6.0 bundle is available locally at [`dist/0.6.0/AWP-0.6.0.bundle.md`](dist/0.6.0/AWP-0.6.0.bundle.md). A version-pinned external reference is:

```text
https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md
```

Do not use a moving branch URL as though it were a released specification. The 0.7.0 draft permits an exact repository-relative local copy for sandboxed or offline environments.

## Protocol model

AWP separates:

- intent from authority;
- execution from evidence and conclusion;
- reported, inferred, observed, verified, disputed, stale, and refuted claims;
- causal event history from generated snapshots and prose;
- byte-level source-control conflicts from semantic coordination conflicts;
- agent negotiation from bounded user-mediated arbitration when an interaction cannot be safely resolved by the agents.

Core is required. Capsule, Handoff, Artifact, Synchronization, Coordination, and Security are separately declared modules. The [architecture overview](docs/architecture.md) describes their boundaries, the [informative formal model](docs/formal-model.md) states the underlying event and projection structure, and the [design rationale](docs/design-rationale.md) explains the principal choices.

## Validation

Python 3.10 or later is required. Install the pinned development dependency:

```bash
python -m pip install --requirement requirements-dev.txt
```

Run all released and draft validators, conformance fixtures, and repository tests:

```bash
python tools/validate_spec_examples.py
python tools/validate_spec_0_4.py
python tools/validate_spec_0_5.py
python tools/validate_spec_0_6.py
python tools/validate_spec_0_7.py
python tools/validate_conformance.py
python -m unittest discover -s tests -v
```

Regenerate the stable and working-draft bundles with:

```bash
python tools/build_spec_0_6_bundle.py
python tools/build_spec_0_7_bundle.py
```

Generated bundles are checked in CI for byte-for-byte reproducibility.

## Repository map

```text
.awp.json                   Repository discovery document
awp.awp.md                  Current portable project workstate
AWP_SPECIFICATION_0.6.0.md Stable family overview
spec/                       Released modules, historical families, and drafts
schemas/                    Versioned normative and draft JSON Schemas
dist/                       Generated bundles, release manifests, and checksums
conformance/                Positive, negative, and interoperability fixtures
experiments/                Reproducible research harnesses and results
docs/                       Architecture, rationale, governance records, and releases
research/                   Design history and disclosed model-assisted reviews
tools/                      Validators and reproducible-build utilities
tests/                      Repository-integrity tests
```

The [specification index](spec/README.md) distinguishes immutable releases from working drafts. Protocol changes follow [the evolution policy](docs/protocol-evolution.md) and consequential decisions are recorded under [`docs/decisions`](docs/decisions).

## Research position

AWP composes ideas from event sourcing, distributed version control, provenance models, workflow checkpointing, software-supply-chain attestations, CRDT research, and agent transports. The [related-work note](docs/related-work.md) identifies that lineage and states the project’s narrower proposed contribution. The [open-issues register](spec/0.6.0/open-issues.md) records unresolved technical questions.

Model-assisted design critiques are archived under [`research/model-assisted-reviews`](research/model-assisted-reviews) with an explicit provenance disclaimer. They are not described as independent peer review.

## Contributing, governance, and citation

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), and [SECURITY.md](SECURITY.md). Cite the exact specification version using [CITATION.cff](CITATION.cff).

AWP is currently distributed under the [GNU General Public License version 3](LICENSE). The licensing scope may be revisited before a stable 1.0 specification; no relicensing is implied by the working draft.
