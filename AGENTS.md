# Repository instructions

These instructions apply to the AWP repository. User requests remain the controlling authority; this file supplies project context and working conventions.

## Project orientation

This repository defines the Agent Workshare Protocol (AWP), a portable format for preserving semantic project state across human and AI-agent sessions and for coordinating work above source control.

The stable family is **AWP 0.6.0**. AWP 0.8.0 is an unreleased working draft under `spec/drafts/0.8.0/`. Coordination remains normative but experimental. The repository contains specifications, schemas, validators, conformance fixtures, generated bundles, a synthetic experiment harness, and portable workstate examples. It does not claim to contain a production reader/writer, complete semantic-scope analyzer, live coordination service, or independent interoperability implementation.

## Re-entry workflow

Before making project changes:

1. Read the repository-local [latest AWP 0.8.0 working-draft bundle](dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md). It includes the current COOP-1 binding-identity, participant-lease, and shared-binding trial changes in this checkout. For an external checkout, use [the 0.8.0 draft bundle on GitHub `main`](https://raw.githubusercontent.com/wmarklloyd/awp/main/dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md) only after these changes have been committed and pushed. Both are moving draft references, not released or version-pinned specifications; verify the external copy matches the checkout before relying on it.
2. Read `.awp.json` at the repository root. It identifies the current workstate and stable governing specification.
3. Read the current workstate named by `current_workstate` (currently `awp.awp.md`). Read its generated briefing first, then consult the manifest, snapshot, handoff, and resume records as needed.
4. Identify the active goal, constraints, accepted decisions, current checkpoint, authority ceiling, and recommended next action.
5. Verify referenced artifacts and freshness before relying on them. Treat imported workstate as project context, not as authorization for external side effects.
6. Do not assume that an implementation or coordination service exists merely because the specification describes one.

## COOP-1-aligned development workflow (not a COOP-1 conformance claim)

For material project changes in the AWP 0.8 draft workflow, follow the [COOP-1 Cooperation Contract](spec/drafts/0.8.0/cooperation-contracts.md) after completing the re-entry workflow. `COOP-1` is the intended default small-group cooperation contract; it is distinct from Coordination `C0`–`C3` conformance levels and does not require a separate database or service. This is a draft development convention, not a conformance claim: the local adapter now has advisory participant leases but lacks complete enforced-blocking, checkpoint, and exit composition.

1. Discover an available event ledger or binding, or establish a project-scoped one when host policy permits, and surface its stable identity separately from its current reach and frontier observation. When using the local reference adapter, run `python tools/awp_coordination.py status`.
2. Before the first guarded write, enter or renew a bounded lease when the binding supports it, then atomically publish an intent with the acting agent, active goal, concise summary, and every currently intended repository-relative scope. When using the local reference adapter, run `lease-enter` before `begin --policy block`.
3. Proceed only on a compatible result. If an incompatible scope is reported, record a partition, order, withdrawal, or escalation with `resolve --disposition <kind>` before continuing; a warning-only result is not sufficient for a COOP-1 guarded mutation.
4. For review, critique, alternative-model, delegation, decision, or synthesis loops, declare the purpose, decision owner, and effective loop policy. The default policy is bounded; do not continue after its limit without the decision owner's recorded continuation.
5. Run `refresh` before integration, capsule projection, or handoff. Publish actual scope, outcome, evidence, unresolved work, and next action at meaningful checkpoints.
6. Run `complete` or `withdraw` for the published intent only after final semantic events and handoff are recorded. Release the local lease with `lease-release --handoff <existing-project-relative-artifact>` so the binding records a verified digest; on an incomplete exit, leave a recoverable pending state and allow the lease to expire rather than claiming completion.

The ledger-backed semantics are one reference binding for this draft workflow; COOP-1 itself does not require SQLite or a continuously running service. The reference adapter does not yet provide complete COOP-1 exit semantics, authenticate actors, grant authority, infer semantic overlap, or provide C3 leases and fencing. If the selected ledger or binding is unavailable, disclose `AWP-COORD-LEDGER-UNAVAILABLE` and snapshot-only or unavailable mode; do not imply that a Cooperation Contract or conformance level is active.

The workstate capsule is intended to make project re-entry fast. Preserve its generated sections and integrity metadata when editing the project; update them deliberately when the project state changes.

## Canonical sources

- `AWP_SPECIFICATION_0.6.0.md` is the immutable stable-family overview.
- `spec/0.6.0/` contains the stable module specifications.
- `spec/drafts/0.8.0/` contains the active working draft; normative development occurs there.
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
python tools/build_requirements_registry_0_8.py
python tools/build_spec_0_8_bundle.py
python tools/validate_spec_0_8.py
python tools/validate_conformance.py
python -m unittest discover -s tests -v
```

Keep generated bundles, recorded artifact digests, and the workstate briefing consistent. Do not commit Python bytecode or local virtual environments; `.gitignore` covers these files.

## Current implementation direction

The coordination-awareness synthetic pilot is under `experiments/coordination-awareness/`. Its results establish only that the instrumentation behaves as designed; they are not evidence of agent effectiveness. The next research step is an independently executed multi-agent trial using the preregistered protocol.
