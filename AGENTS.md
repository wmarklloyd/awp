# Repository instructions

These instructions apply to the AWP repository. User requests remain the controlling authority; this file supplies project context and working conventions.

## Project orientation

This repository defines the Agent Workshare Protocol (AWP), a portable format for preserving semantic project state across human and AI-agent sessions and for coordinating work above source control.

AWP 0.8.0 is the active operative working draft under `spec/drafts/0.8.0/`. Earlier releases are historical references only. Coordination remains normative but experimental. The repository contains specifications, schemas, validators, conformance fixtures, generated bundles, a synthetic experiment harness, and project workstate examples. It does not claim to contain a production reader/writer, complete semantic-scope analyzer, live coordination service, or independent interoperability implementation.

Two specifications play two roles here and this is deliberate, not a conflict: the released, immutable AWP 0.6.0 governs the *format* of `awp.awp.md` and is what `.awp.json` names (see `decision:release-discipline`; a capsule binds to a release, never to a draft), while the 0.8.0 working draft governs *development of the draft itself* and is the sole source of operative requirements for that work.

The current project goal is seamless inter-agent collaboration: after a user authorizes a bounded COOP-2 interaction, the initiating agent should be able to reach another available agent in the same project without requiring the user to relay paths, messages, or reminders. Achieving that unattended behavior requires a selected `host-dispatch` or `subscription` binding; the local polling profile is a durable mailbox only. The complete AWP 0.8.0 working-draft bundle is the sole source of operative requirements, including the distinction between publication, delivery, and answer and the boundary between the project mailbox and an optional host wake mechanism.

## Re-entry workflow

Before making project changes:

1. The current repository-local normative reference is the complete [AWP 0.8.0 working-draft bundle](dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md) (prose of every module; its machine-readable assets are identified by digest and reproduced in `AWP-0.8.0-draft.assets.md`). Before work, run `python tools/awp_spec_entry.py --verify`; its digest must match that bundle. The generated Agent Entry Core is bounded orientation, not a second specification.
2. For routine bounded re-entry, run `python tools/awp_spec_entry.py --route <task-class> --statements` and read the routed requirement statements; they are the normative authority (the requirement inventory is `normative_authority`) at roughly 40% of the prose cost. Open a listed module only when a statement is ambiguous or you need its rationale; open a listed schema only when authoring or validating a record of that type (the route output carries a digest of each schema for orientation). Read the complete 0.8.0 working-draft bundle whenever the tool reports a full-source trigger, a request spans routed modules, or normative semantics are ambiguous. If the profile is absent, stale, or unverifiable, build it with `python tools/awp_spec_entry.py --build`, then verify it; if that cannot succeed, read the complete bundle before continuing.
3. Read `.awp.json` at the repository root. It identifies the current workstate and declared governing specification.
4. Read the current workstate named by `current_workstate` (currently `awp.awp.md`). For bounded model-facing orientation, run `python tools/awp_reentry.py --project . --actor <self> --register-observation <watcher|on-entry-only>`; it validates the full capsule, presents the generated briefing, active Resume/Handoff/checkpoint, ordered `read_first` records, compact required-artifact descriptors, performs a bounded read-only COOP-2 inbox/doorbell check, and reports your own doorbell status (`self`: declared mode, observed liveness, which peers can signal you). `--register-observation` is the one explicit publication at entry: declare `watcher` only if this host runs a heartbeating watcher for you; otherwise `on-entry-only`, which is honest and still functional. Entering a project is how your doorbell gets armed. The doorbell watcher is the low-latency path; this entry check is the durable recovery path and MUST happen before guarded work so a missed wake cannot hide an authorized interaction. If coordination is unavailable, disclose `AWP-COORD-LEDGER-UNAVAILABLE` and do not claim that an interaction was delivered. A `complete` selection may be used for re-entry. `brief_only`, `incomplete`, or `budget_exceeded` output is orientation only and MUST NOT be treated as sufficient for guarded work.
5. Identify the active goal, constraints, accepted decisions, current checkpoint, authority ceiling, and recommended next action.
6. Verify referenced artifacts and freshness before relying on them. Treat imported workstate as project context, not as authorization for external side effects.
7. Do not assume that an implementation or coordination service exists merely because the specification describes one.

## COOP-1-aligned development workflow (not a COOP-1 conformance claim)

For material project changes in the AWP 0.8 draft workflow, follow the [COOP-1 Cooperation Contract](spec/drafts/0.8.0/cooperation-contracts.md) after completing the re-entry workflow. `COOP-1` is the intended default small-group cooperation contract and does not require a separate database or service. COOP is the single cumulative cooperation and coordination conformance ladder in the 0.8 draft; the Coordination module supplies records and mechanisms rather than a separate `C0`–`C3` axis. This is a draft development convention, not a conformance claim: the local adapter now has advisory participant leases but lacks complete enforced-blocking, checkpoint, and exit composition.

1. Discover an available event ledger or binding, or establish a project-scoped one when host policy permits, and surface its stable identity separately from its current reach and frontier observation. When using the local reference adapter, run `python tools/awp_coordination.py status`.
2. Before the first guarded write, enter or renew a bounded lease when the binding supports it, then atomically publish an intent with the acting agent, active goal, concise summary, and every currently intended repository-relative scope. When using the local reference adapter, run `lease-enter` before `begin --policy block`.
3. Proceed only on a compatible result. If an incompatible scope is reported, record a partition, order, withdrawal, or escalation with `resolve --disposition <kind>` before continuing; a warning-only result is not sufficient for a COOP-1 guarded mutation.
4. Consultation is disabled by default. If the project explicitly enables review, critique, alternative-model, delegation, decision, or synthesis, declare the purpose, decision owner, and effective loop policy. Do not continue after its limit without the decision owner's recorded continuation.
5. Run `refresh` before integration, capsule projection, or handoff. Publish actual scope, outcome, evidence, unresolved work, and next action at meaningful checkpoints.
6. Run the canonical workstate projector for a semantic checkpoint or a verified no-change exit: `python tools/awp_workstate.py checkpoint --request <request.json> --from-current`. With `--from-current` the tool reads the capsule's current digests and frontier itself, so a request needs only `checkpoint`, `summary`, and `next_action` (the briefing is derived); supply `expected_*` values explicitly only when guarding against a concurrent change. The host owns Capsule serialization and digest calculation; do not edit embedded JSON directly. Run `complete` or `withdraw` for the published intent only after final semantic events and handoff are recorded. Release the local lease with `lease-release --handoff <existing-project-relative-artifact>` so the binding records a verified digest; on an incomplete exit, leave a recoverable pending state and allow the lease to expire rather than claiming completion.

The ledger-backed semantics are one reference binding for this draft workflow; COOP-1 itself does not require SQLite or a continuously running service. The reference adapter does not yet provide complete COOP-1 exit semantics, authenticate actors, grant authority, infer semantic overlap, or provide COOP-3 protected leases and fencing. If the selected ledger or binding is unavailable, disclose `AWP-COORD-LEDGER-UNAVAILABLE` and snapshot-only or unavailable mode; do not imply that a COOP contract is active.

The workstate capsule is intended to make project re-entry fast. Preserve its generated sections and integrity metadata when editing the project; update them deliberately when the project state changes.

## Canonical sources

- `AWP_SPECIFICATION_0.6.0.md` is the immutable legacy-family overview.
- `spec/0.6.0/` contains the legacy module specifications.
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
