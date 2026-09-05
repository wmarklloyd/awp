# AWP Project Reference

This document collects release, validation, repository, research, and governance information that supports the Agent Workshare Protocol without interrupting the introductory path in the main [README](../README.md).

## Release status

| Track | Version | Status | Entry point |
|---|---:|---|---|
| Stable specification | 0.6.0 | Exploratory release | [Family overview](../AWP_SPECIFICATION_0.6.0.md) |
| Active development | 0.8.0 | Working draft; not a release | [Draft overview](../spec/drafts/0.8.0/index.md) |
| Coordination | 0.3.0 stable-family module / 0.4.0 draft | Normative but experimental | [Released module](../spec/0.6.0/coordination.md) |

AWP 0.8.0 introduces explicit governing-specification binding and separately versioned draft semantics. It is not a published release.

The current version-pinned external bundle reference is:

```text
https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md
```

Do not use a moving branch URL as though it were a released specification. A sandboxed or offline project may reference a repository-relative copy of the exact 0.6.0 bundle. A detached 0.8.0 consultation may instead reference the local draft bundle explicitly.

## Protocol modules

Core is required. Capsule, Handoff, Artifact, Synchronization, Coordination, and Security are separately declared modules. See the [architecture overview](architecture.md) for their boundaries, the [informative formal model](formal-model.md) for the event and projection structure, and the [design rationale](design-rationale.md) for the principal choices.

## Boundaries and limitations

AWP is not an agent runtime, source control system, artifact store, authentication or authorization system, distributed-consensus system, or project policy engine. A workstate can describe claims, constraints, and requested actions, but it does not grant authority to perform external side effects.

The repository currently provides:

- Modular normative prose and machine-readable module registries.
- Versioned JSON Schemas for structural validation.
- Generated self-contained specification bundles.
- Executable positive and negative conformance fixtures.
- Deterministic bundle-reproducibility tests.
- A synthetic coordination-awareness instrumentation pilot.

It does not yet provide a production reader/writer, complete cross-record validator, semantic-scope analyzer, live coordination service, two independent implementations, or empirical evidence that AWP improves real multi-agent outcomes.

## Validation

Python 3.10 or later is required. Install the pinned development dependency:

```bash
python -m pip install --requirement requirements-dev.txt
```

Run the released validators, conformance fixtures, and repository tests:

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
python tools/build_requirements_registry.py
python tools/build_spec_0_7_bundle.py
```

Generated bundles are checked in continuous integration for byte-for-byte reproducibility.

## Repository map

```text
.awp.json                   Repository discovery document
awp.awp.md                  Current portable project workstate
AWP_SPECIFICATION_0.6.0.md Stable 0.6.0 family overview
spec/                       Released modules, historical families, and drafts
schemas/                    Versioned JSON Schemas
dist/                       Generated bundles, release manifests, and checksums
conformance/                Positive, negative, and interoperability fixtures
experiments/                Reproducible research harnesses and results
docs/                       Architecture, rationale, governance records, and releases
research/                   Design history and disclosed model-assisted reviews
tools/                      Validators and reproducible-build utilities
tests/                      Repository-integrity tests
```

The [specification index](../spec/README.md) distinguishes immutable releases from working drafts. Protocol changes follow the [evolution policy](protocol-evolution.md), and consequential decisions are recorded under [decision records](decisions).

## Research, governance, and citation

AWP composes ideas from event sourcing, distributed version control, provenance models, workflow checkpointing, software-supply-chain attestations, CRDT research, and agent transports. The [related-work note](related-work.md) describes that lineage. Model-assisted critiques are archived under [research/model-assisted-reviews](../research/model-assisted-reviews) with their provenance disclosed.

See the [project scope](project-scope.md), [contribution guidance](../CONTRIBUTING.md), [governance policy](../GOVERNANCE.md), [security policy](../SECURITY.md), and [citation metadata](../CITATION.cff).
