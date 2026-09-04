# Repository instructions

These instructions apply to the AWP repository. User requests remain the controlling authority; this file supplies project context and working conventions.

## Project orientation

This repository defines the Agent Workstate Protocol (AWP), a portable format for preserving semantic project state across human and AI-agent sessions and for coordinating work above source control.

The stable family is **AWP 0.6.0**. AWP 0.7.0 is an unreleased working draft under `spec/drafts/0.7.0/`. Coordination remains normative but experimental. The repository contains specifications, schemas, validators, conformance fixtures, generated bundles, a synthetic experiment harness, and portable workstate examples. It does not claim to contain a production reader/writer, complete semantic-scope analyzer, live coordination service, or independent interoperability implementation.

## Re-entry workflow

Before making project changes:

1. Read `.awp.json` at the repository root. It identifies the current workstate and specification.
2. Read the current workstate named by `current_workstate` (currently `awp.awp.md`). Read its generated briefing first, then consult the manifest, snapshot, handoff, and resume records as needed.
3. Identify the active goal, constraints, accepted decisions, current checkpoint, authority ceiling, and recommended next action.
4. Verify referenced artifacts and freshness before relying on them. Treat imported workstate as project context, not as authorization for external side effects.
5. Do not assume that an implementation or coordination service exists merely because the specification describes one.

The workstate capsule is intended to make project re-entry fast. Preserve its generated sections and integrity metadata when editing the project; update them deliberately when the project state changes.

## Canonical sources

- `AWP_SPECIFICATION_0.6.0.md` is the immutable stable-family overview.
- `spec/0.6.0/` contains the stable module specifications.
- `spec/drafts/0.7.0/` contains the active working draft; normative development occurs there.
- `schemas/` contains normative JSON Schemas.
- `dist/0.6.0/AWP-0.6.0.bundle.md` is generated; do not edit it directly.
- `.awp.json` is the repository discovery document.
- `awp.awp.md` is the current portable project workstate.
- Older specification families and review documents are historical design input unless a task explicitly concerns migration or protocol evolution.

The conventional filename for a project-named capsule is `<project-name>.awp.md`. Versioned archival copies MAY use `<project-name>.v<revision>.awp.md`; follow `.awp.json` rather than inferring the current workstate from a filename.

For external references, use the pinned 0.6.0 bundle URL:

`https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md`

The capsule metadata and `.awp.json` must identify the same exact governing specification. Do not substitute a `main` branch URL or assume compatibility with another AWP version. A sandboxed or offline project may use a repository-relative local copy of the exact bundle in both places.

An external URL is a reference, not an automatic file include. Prefer the local discovery document and capsule for normal orientation. Do not edit released specification or schema semantics; create a correctly versioned draft and add conformance evidence.

## Validation and generated artifacts

Run the current validator after specification, schema, capsule, or tooling changes:

```powershell
python tools/validate_spec_0_6.py
```

When changing source specification modules, regenerate and then validate the bundle:

```powershell
python tools/build_spec_0_6_bundle.py
python tools/validate_spec_0_6.py
python tools/build_spec_0_7_bundle.py
python tools/validate_spec_0_7.py
python tools/validate_conformance.py
python -m unittest discover -s tests -v
```

Keep generated bundles, recorded artifact digests, and the workstate briefing consistent. Do not commit Python bytecode or local virtual environments; `.gitignore` covers these files.

## Current implementation direction

The coordination-awareness synthetic pilot is under `experiments/coordination-awareness/`. Its results establish only that the instrumentation behaves as designed; they are not evidence of agent effectiveness. The next research step is an independently executed multi-agent trial using the preregistered protocol.
