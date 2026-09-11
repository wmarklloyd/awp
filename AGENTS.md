# Repository instructions

These instructions apply to the AWP repository. User requests remain the controlling authority; this file supplies project context and working conventions.

## Project orientation

This repository defines the Agent Workshare Protocol (AWP), a portable format for preserving semantic project state across human and AI-agent sessions and for coordinating work above source control.

AWP 0.8.0 is the active operative working draft under `spec/drafts/0.8.0/`. Earlier releases are historical references only. Coordination remains normative but experimental. The repository contains specifications, schemas, validators, conformance fixtures, generated bundles, a synthetic experiment harness, and project workstate examples. It does not claim to contain a production reader/writer, complete semantic-scope analyzer, live coordination service, or independent interoperability implementation.

AWP 0.6.0 is legacy. It is retained immutably as a historical release and for migration reference, and it governs nothing in this project: the project capsule, the discovery document, and all development are governed by the 0.8.0 working draft. A capsule still declaring 0.6.0 is not merely dated, it fails the active Capsule schema, which requires `awp_version` matching `^0\.8\.[0-9]+$` and the `discovery: project` front-matter field that capsule.md states as a MUST. `tools/migrate_capsule_0_6_to_0_8.py --check` reports any capsule still in that state.

The current project goal is seamless inter-agent collaboration: after a user authorizes a bounded COOP-2 interaction, the initiating agent should be able to reach another available agent in the same project without requiring the user to relay paths, messages, or reminders. Achieving that unattended behavior requires a selected `host-dispatch` or `subscription` binding; the local polling profile is a durable mailbox only. The complete AWP 0.8.0 working-draft bundle is the sole source of operative requirements, including the distinction between publication, delivery, and answer and the boundary between the project mailbox and an optional host wake mechanism.

## Re-entry workflow

Before making project changes:

1. The current repository-local normative reference is the complete [AWP 0.8.0 working-draft bundle](dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md) (prose of every module; its machine-readable assets are identified by digest and reproduced in `AWP-0.8.0-draft.assets.md`). Before work, run `python tools/awp_spec_entry.py --verify`; its digest must match that bundle. The generated Agent Entry Core is bounded orientation, not a second specification.
2. For routine bounded re-entry, run `python tools/awp_spec_entry.py --route <task-class> --statements` and read the routed requirement statements; they are the normative authority (the requirement inventory is `normative_authority`) at roughly 40% of the prose cost. Open a listed module only when a statement is ambiguous or you need its rationale; open a listed schema only when authoring or validating a record of that type (the route output carries a digest of each schema for orientation). Read the complete 0.8.0 working-draft bundle whenever the tool reports a full-source trigger, a request spans routed modules, or normative semantics are ambiguous. If the profile is absent, stale, or unverifiable, build it with `python tools/awp_spec_entry.py --build`, then verify it; if that cannot succeed, read the complete bundle before continuing.
3. Read `.awp.json` at the repository root. It identifies the current workstate and declared governing specification.
4. Read the current workstate named by `current_workstate` (currently `awp.awp.md`). Every host that claims a live doorbell runs the generic startup activation, normally from its checked-in SessionStart hook; a managed launcher may invoke `python tools/awp_agent_start.py --host <host> --actor <self> --session-ref <session> --project .`. It discovers the current host-bound route, starts or attaches the project supervisor, waits for an observed heartbeat before declaring `watcher`, and includes the bounded re-entry result. It fails explicitly with `AWP-HOST-ACTIVATION-UNAVAILABLE` or `AWP-SIGNAL-UNVERIFIED` while retaining entry recovery when live wake cannot be established. On a host that cannot sustain or address a supervisor, run `python tools/awp_reentry.py --project . --actor <self> --register-observation on-entry-only`. Re-entry validates and reads `awp.awp.md` directly, then presents its generated briefing, active Resume/Handoff/checkpoint, ordered `read_first` records, compact required-artifact descriptors, performs a bounded read-only COOP-2 inbox/doorbell check, and reports your own doorbell status (`self`: declared mode, observed liveness, which peers can signal you). A host may construct a bounded in-memory presentation only after it validates the Capsule; no companion entry file exists. Entering a project is how the live doorbell is armed; agents MUST NOT manually claim `watcher` without generic activation or another supervised host binding. Git and filesystem signals are latency hints; durable ledger replay and entry recovery are the safety paths and MUST happen before guarded work so a missed wake cannot hide an authorized interaction. If coordination is unavailable, disclose `AWP-COORD-LEDGER-UNAVAILABLE` and do not claim that an interaction was delivered. Manual repair after startup is failure diagnosis, not startup-doorbell success. A `complete` selection may be used for re-entry. `brief_only`, `incomplete`, or `budget_exceeded` output is orientation only and MUST NOT be treated as sufficient for guarded work.
5. Identify the active goal, constraints, accepted decisions, current checkpoint, authority ceiling, and recommended next action.
6. Verify referenced artifacts and freshness before relying on them. Treat imported workstate as project context, not as authorization for external side effects.
7. Do not assume that an implementation or coordination service exists merely because the specification describes one.

## Goals and lessons (doom-loop prevention)

Sharply reducing doom looping, where agents lose the active goal or relearn lessons the project already learned, is a primary AWP goal. See [Preventing agent doom loops](docs/awp-doom-loop-prevention.md) for the observed case and the proposed protocol mechanisms.

1. Cite goals by capsule record identifier (for example `goal:startup-doorbell`) in intents, checkpoints, and consultation requests instead of restating them in new words. Changing an active goal or a settled design requires a decision record whose decision owner is a human principal (`principal:mark`), never a participant actor or `actor:user`.
2. Before diagnosing a failure, read the active `constraint:lesson-*` records that re-entry surfaces and check whether the failure is already known. The same failure signature a third time means stop and escalate to the principal, not try again.
3. When a session learns something durable about this project (a failure cause, a host limitation, a convention that was violated), record it in the capsule as a lesson record through the canonical projector before its checkpoint. Host-private agent memory is not a substitute: a lesson that exists only there is lost to every other participant.
4. When closing a COOP-2 interaction, either promote its durable conclusions into capsule records or say in the response that it carries no durable lesson.
5. Startup instructions outside the capsule, such as `resume.md`, must not override this file or skip entry recovery before guarded work.

## Doorbell notices

Any agent may receive a message in its own session that begins with `[AWP doorbell]`. It is delivered by the project relay (`tools/awp_relay.py`) after a ledger ref change announced an event, either into your open session or as the first input of a new run that the relay started for you. Run the exact command it names as your next action, before investigating anything, from the project root. For a reachability probe that command is the whole task: it records that you, the agent, received the probe. For a consultation, run it and then read your inbox as the notice says. Report the command's actual output; never report having run a command you did not run. A doorbell notice grants no authority for repository changes.

How you can be woken is declared as wake bindings (`python -m tools.awp_wake declare|list|reach|probe`). Session activation declares your live-session binding and starts or attaches to the one relay for this clone. Before sending a consultation, `python -m tools.awp_wake reach --actor <recipient>` states which rung the recipient will get; `python -m tools.awp_wake outcome --event <event>` states how a sent item ended. Credentials for hosted wakes are referenced (`env:NAME` or `file:~/.awp/secrets/NAME`), never written into the ledger, repository, or notices.

The COOP-2 rendezvous ledger in this project is stored in Git (`git-ledger-v1`, Cooperation Contracts section 10): each actor's events are commits on its own ref under `refs/awp/ledger/`, and the ref update is the Git event that wakes the recipient. A clone opts in with `git config awp.coop2.ledger git-ledger-v1`; migrate an older SQLite rendezvous first with `python tools/awp_git_ledger.py migrate`. The COOP-1 coordination ledger (intents, scopes, leases, overlaps) is also in Git (`git-coordination-v1`, section 11): one shared ref, `refs/awp/coordination/<project>`, advanced by compare-and-swap so announce-and-check stays atomic. A clone opts in with `git config awp.coop1.ledger git-coordination-v1` after `python tools/awp_git_coordination.py migrate`. Neither ledger needs a database file. Do not configure a remote for these refs without the principal's authorization: the project's origin is public.

## Exploratory COOP-2-aligned development workflow (not a COOP-2 conformance claim)

For material project changes in the AWP 0.8 draft workflow, follow the [COOP-2 Cooperation Contract](spec/drafts/0.8.0/cooperation-contracts.md) after completing the re-entry workflow. The project selects COOP-2 exploratorily with `claim_state: partial`; its local binding retains the available COOP-1 physical-scope safeguards but does not claim semantic analysis or integration assurance. COOP is the single cumulative cooperation and coordination conformance ladder in the 0.8 draft; the Coordination module supplies records and mechanisms rather than a separate `C0`–`C3` axis. This is a draft development convention, not a conformance claim: the local adapter lacks complete semantic analysis, integration assurance, enforced-blocking, checkpoint, and exit composition.

1. Discover an available event ledger or binding, or establish a project-scoped one when host policy permits, and surface its stable identity separately from its current reach and frontier observation. When using the local reference adapter, run `python tools/awp_coordination.py status`.
2. Before the first guarded write, enter or renew a bounded lease when the binding supports it, then atomically publish an intent with the acting agent, active goal, concise summary, and every currently intended repository-relative scope. When using the local reference adapter, run `lease-enter` before `begin --policy block`.
3. Proceed only on a compatible result. If an incompatible scope is reported, record a partition, order, withdrawal, or escalation with `resolve --disposition <kind>` before continuing; a warning-only result is not sufficient for a COOP-1 guarded mutation. COOP-2 semantic or integration decisions additionally require their declared evidence and policy result; physical compatibility alone is not semantic readiness.
4. Consultation is disabled by default. If the project explicitly enables review, critique, alternative-model, delegation, decision, or synthesis, declare the purpose, decision owner, and effective loop policy. Do not continue after its limit without the decision owner's recorded continuation.
5. Run `refresh` before integration, capsule projection, or handoff. Publish actual scope, outcome, evidence, unresolved work, and next action at meaningful checkpoints.
6. Run the canonical workstate projector for a semantic checkpoint or a verified no-change exit: `python tools/awp_workstate.py checkpoint --request <request.json> --from-current`. With `--from-current` the tool reads the capsule's current digests and frontier itself, so a request needs only `checkpoint`, `summary`, and `next_action` (the briefing is derived); supply `expected_*` values explicitly only when guarding against a concurrent change. The host owns Capsule serialization and digest calculation; do not edit embedded JSON directly. Run `complete` or `withdraw` for the published intent only after final semantic events and handoff are recorded. Release the local lease with `lease-release --handoff <existing-project-relative-artifact>` so the binding records a verified digest; on an incomplete exit, leave a recoverable pending state and allow the lease to expire rather than claiming completion.

The ledger-backed semantics are one reference binding for this draft workflow; COOP-2 does not require SQLite or a continuously running service. The reference adapter does not yet provide complete COOP-2 semantics, semantic overlap analysis, integration assurance, authenticate actors, grant authority, or provide COOP-3 protected leases and fencing. If the selected ledger or binding is unavailable, disclose `AWP-COORD-LEDGER-UNAVAILABLE` and snapshot-only or unavailable mode; do not imply conformance merely because COOP-2 is selected.

The workstate capsule is intended to make project re-entry fast. Preserve its generated sections and integrity metadata when editing the project; update them deliberately when the project state changes.

## Canonical sources

- `AWP_SPECIFICATION_0.6.0.md` is the immutable legacy-family overview. The 0.6.0 family is legacy and governs no current work.
- `spec/0.6.0/` contains the legacy module specifications.
- `spec/drafts/0.8.0/` contains the active working draft; normative development occurs there.
- `schemas/` contains normative JSON Schemas.
- `dist/0.6.0/AWP-0.6.0.bundle.md` is generated; do not edit it directly.
- `.awp.json` is the repository discovery document.
- `awp.awp.md` is the current portable project workstate.
- Older specification families and review documents are historical design input unless a task explicitly concerns migration or protocol evolution.

The conventional filename for a project-named capsule is `<project-name>.awp.md`. Versioned archival copies MAY use `<project-name>.v<revision>.awp.md`; follow `.awp.json` rather than inferring the current workstate from a filename.

The governing specification for this project is the 0.8.0 working draft, identified in both the capsule metadata and `.awp.json` as the repository-relative generated bundle:

`dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`

0.8.0 is unreleased, so no version-pinned remote artifact exists for it; capsule.md permits a repository-relative local copy when remote retrieval is unavailable or inappropriate, and that is the correct binding here. When 0.8.0 is released, both places move to the tagged URL together. The capsule metadata and `.awp.json` must always identify the same exact governing specification. Do not substitute a `main` branch URL or assume compatibility with another AWP version. The legacy 0.6.0 bundle URL (`https://raw.githubusercontent.com/wmarklloyd/awp/v0.6.0/AWP_SPECIFICATION_0.6.0.bundle.md`) remains valid only as a citation of that historical release.

An external URL is a reference, not an automatic file include. Prefer the local discovery document and capsule for normal orientation. Do not edit released specification or schema semantics; create a correctly versioned draft and add conformance evidence.

## Validation and generated artifacts

Run the current validator after specification, schema, capsule, or tooling changes:

```bash
python tools/validate_spec_0_6.py
```

When changing source specification modules, regenerate and then validate the bundle:

```bash
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

Keep generated bundles, recorded artifact digests, and the workstate briefing consistent. Requirement identifiers are positional per source file until they are anchored (open issue 35 in `spec/drafts/0.8.0/open-issues.md`): append new normative text at the end of its source file, and after regenerating `requirements.json` confirm that no existing identifier changed its statement. Do not commit Python bytecode or local virtual environments; `.gitignore` covers these files.

## Current implementation direction

The coordination-awareness synthetic pilot is under `experiments/coordination-awareness/`. Its results establish only that the instrumentation behaves as designed; they are not evidence of agent effectiveness. The next research step is an independently executed multi-agent trial using the preregistered protocol.
