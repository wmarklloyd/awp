# Preventing agent doom loops

## Definition and goal

A *doom loop* is what happens when agents lose the active goal or fail to
carry forward lessons already learned, and so re-derive, re-litigate, or
repeat work the project has already done. Reopening a settled architecture
after a local runtime failure is one symptom. Re-discovering a known failure
cause, restating a goal in new words each session, and retrying a fix that
already failed are others.

Sharply reducing doom looping is a primary goal of AWP (stated by the project
principal, 2026-09-10). A workstate format that preserves history but lets
goals drift and lessons evaporate does not meet it.

The problem has two halves, and both need protocol support:

1. **Goal loss.** The active goal, its definition of done, and its settled
   design are restated in prose instead of referenced, so they drift.
2. **Lesson loss.** What a session learned (a failure cause, a constraint of
   the host, a convention that keeps being violated) is not recorded where the
   next session or the peer agent will see it, so it is learned again.

## Observed case: 2026-09-10

The startup-doorbell work on 2026-09-10 is a complete worked example.

Goal loss:

- The principal stated the primary goal as "doorbells work seamlessly after a
  reboot." The capsule regenerated at 22:55Z, after five consultations on that
  work, held a single goal record (`goal:awp-design`) and did not mention a
  reboot or restart goal at all. Its Resume record still recommended
  task-scoped decision-closure work.
- Five consultations in about two and a half hours restated the goal five
  ways: "doorbell bootstrap failure", "robust COOP-2 doorbell bootstrap",
  "robust unattended same-host doorbells after bootstrap/reboot", "generic
  AWP startup doorbell over Git events", and "universal AWP startup doorbell".
  Each re-derived its context from scratch because there was no goal record to
  cite.
- `resume.md` became an independent, hand-written instruction stream. It
  directs the next Codex session to skip the re-entry workflow, which is the
  step that would surface goals and lessons, and its test sends a tickle from
  `actor:codex` to `actor:codex`, dropping the cross-agent goal.
- Consultation answers (Claude's included) folded new architecture into plans
  (a single-writer supervisor, a cross-boundary request queue, a deferred
  outcome for hosts without a wake endpoint) without marking any of it as
  requiring a superseding decision.

Lesson loss:

| Lesson | Known since | Recurred as |
| --- | --- | --- |
| Size delivery and response windows for the recipient's observation mode; short windows to an on-entry-only participant guarantee a timeout. | 2026-09-09 | `interaction:c99ec2fe5a1b5527867679ab` sent to on-entry-only Claude with a 300 s delivery window; it timed out undelivered. |
| `decision_owner` names a human principal, never a participant actor. | 2026-09-09 (COOP-1 section 5) | Three of the five consultations named `actor:user`. |
| A Cowork session cannot host a watcher; device-shell processes end with each call. | 2026-09-09, verified | A proposed acceptance test required Claude to acknowledge a tickle within the heartbeat TTL after restart. |
| SQLite WAL across the Windows host / Cowork VM file mount fails intermittently. | 2026-09-10, doorbell WAL recovery checkpoint | Re-diagnosed as a new finding in later consultations; hit again during responses (`disk I/O error`, `unable to open database file`). |
| Git index-writing commands from across that mount can strand `.git/index.lock`. | 2026-09-10 | Not yet recurred; recorded only in one agent's private memory. |

Where those lessons actually lived: in the text of closed COOP-2 responses,
and in each agent's host-private memory (Claude's project memory; presumably
Codex's own). None were in the capsule. Each agent was therefore learning
alone, which is exactly the failure AWP exists to prevent.

## Principles

1. **The workstate remembers, not the agent.** Host-private memory is a cache.
   A project lesson that exists only there is lost for every other participant.
2. **Goals are referenced, not restated.** Work cites a goal record by
   identifier and revision.
3. **Every closed discussion leaves a trace.** A closed interaction or a
   diagnosed failure is either promoted into records or explicitly marked as
   carrying no durable lesson.
4. **Re-entry leads with the goal and the relevant lessons.** Before history,
   briefing prose, or artifacts.
5. **A repeat is a signal.** The same failure, question, or restated goal
   recurring is evidence that something was lost, and should be detected.
6. **Only the principal changes settled fields.**

## Mechanisms

### 1. Active execution contract (goal half)

Every active task has one compact, machine-readable execution contract,
derived in memory from `awp.awp.md` and presented first on startup:

- `goal`: reference to the goal record (identifier and revision) and its
  one-sentence statement.
- `acceptance_test`: the single observable definition of done, naming the
  ledger evidence required for each stage.
- `settled_design`: the selected architecture and its non-negotiable parts.
- `rejected_diversions`: approaches explicitly ruled out, with reasons.
- `current_phase`: the current bounded stage of the work.
- `allowed_next_actions`: a small list of permitted next actions.
- `blocker_policy`: how to classify a failure without reopening architecture.
- `supersession_rule`: changing a settled field requires a new decision record
  whose `decision_owner` is a human principal.

Enforcement should rest on citation rather than recitation. Intents,
checkpoints, and consultation requests carry the contract's identifier,
revision, and digest; the coordination tools reject a stale or missing
citation. (Asking an agent to echo the goal is cheap to satisfy without
following it.) A consultation that asks to critique a settled field must cite
the contract and is answered inside it; proposals that would change a settled
field are returned separately, labelled as requiring a superseding decision.

For the startup-doorbell work, the generated card would say:

```text
Goal: generic unattended cross-agent startup tickle.
Done: restart test completes publication -> accepted transport -> acknowledgement.
Settled design: Git event/ref trigger; generic watcher; real host adapters are
part of the complete solution.
Do not substitute: SQLite mailbox, temporary fallback, Codex-only design, or a
deferred receipt.
On failure: diagnose the selected binding; do not propose another architecture
without a superseding decision.
```

Open clarifications for the principal (they change settled fields, so they are
listed here rather than applied):

- "SQLite mailbox" should be distinguished from the SQLite ledger, which
  current tools treat as the authoritative record; the likely intent is that
  SQLite is not the delivery trigger.
- "Done" should state both directions and whether the acknowledgement is the
  watcher's transport receipt or the recipient agent's observation.
- For a host with no known wake endpoint (currently Cowork), "repair that
  adapter" may be infeasible. The blocker policy needs an explicit route for
  that case (below) so an agent neither loops nor quietly redesigns.

### 2. Lesson records (lesson half)

A lesson is a first-class record:

- `statement`: the rule to follow next time.
- `observation`: what happened.
- `evidence`: references to events, interactions, or evidence records.
- `failure_signature`: a normalized error class and component, for matching.
- `affects`: goal, task, artifact, or binding identifiers it applies to.
- `learned_at`, `source`, `status` (`active`, `superseded`, `retired`),
  `revision`.

Until the core schema defines a `lesson` type, record lessons as `constraint`
records (identifier prefix `constraint:lesson-`, `strength` of `required` or
`advisory`) with `evidence` and `affects` references. The 2026-09-10 lessons
above are recorded that way in the project capsule.

### 3. Promotion obligation

At a checkpoint, every COOP-2 interaction closed since the previous checkpoint,
and every failure the session diagnosed, carries a disposition: `promoted`
(with the record identifiers) or `no_durable_lesson` (with a reason). The
projector rejects a checkpoint that leaves any undispositioned. This is what
turns a closed consultation into project memory instead of ledger history.

### 4. Re-entry ordering

The Resume record's `read_first` begins with the active goal records and the
lesson records whose `affects` match the active task, before decisions, tasks,
and artifacts. The bounded presentation budget reserves room for them.

### 5. Repeat detection

- At diagnosis, match the failure signature against active lessons and show
  any match before the agent proposes a fix.
- Attempt budget: the same failure signature three times within the selected
  binding stops the work and escalates to the principal.
- Flag a consultation whose subject or goal statement restates an open or
  recently closed one without citing it.

### 6. One instruction stream

`resume.md` and any other startup instruction is generated from the capsule's
Resume record and execution contract, or is a pointer to them. It must never
tell an agent to skip entry recovery before guarded work. Agents must not keep
project rules in host-private memory that are absent from the capsule.

## Enforced responses

| Failure observed | Required response |
| --- | --- |
| SQLite or filesystem failure | Check lesson records first; then diagnose within the selected binding. |
| Host adapter unavailable | Record `unavailable` and repair that adapter. |
| Host adapter infeasible on this host (no known endpoint) | Record `unavailable`, never count it as done, and escalate to the principal; do not redesign. |
| Same failure signature a third time | Stop and escalate to the principal with the prior attempts. |
| Proposal changes architecture | Require a superseding decision with a principal as decision owner. |
| Closed interaction or diagnosed failure without a disposition | Reject the checkpoint. |
| Claim of success | Require recorded evidence for every acceptance-test stage. |

## Status

Applied now: the goals and lessons from the observed case are recorded in the
project capsule and surfaced by its Resume record, and `AGENTS.md` states the
goal-reference and lesson-promotion conventions.

Proposed, not yet normative: a `lesson` record type in the 0.8 core schema;
the promotion check in `tools/awp_workstate.py checkpoint`; contract citation
checks in the coordination and COOP-2 tools; failure-signature matching at
re-entry; generation of `resume.md` from the capsule.

## Limit

A protocol cannot guarantee that an agent never reasons badly. It can make
deviation visible, reject it at mutation and checkpoint boundaries, carry
lessons across sessions and agents, and make continuing the agreed path easier
than reopening settled choices.
