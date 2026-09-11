# Preventing agent doom loops

## Problem

AWP must preserve not only project history, but also the decision boundary
around active work. A detailed capsule and a narrow resume instruction can
still let an agent reopen a settled architecture when it encounters a local
runtime failure.

## Proposed addition: active execution contract

Every active task should have one compact, machine-readable execution contract
generated into `awp.entry.json` and presented first on startup. It contains:

- `goal`: the exact outcome in one sentence.
- `acceptance_test`: the single observable definition of done.
- `settled_design`: the selected architecture and its non-negotiable parts.
- `rejected_diversions`: approaches explicitly ruled out, with reasons.
- `current_phase`: the current bounded stage of the work.
- `allowed_next_actions`: a small list of permitted next actions.
- `blocker_policy`: how to classify a failure without reopening architecture.
- `supersession_rule`: changing a settled field requires a new,
  user-authorized decision record.

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

## Enforced responses

| Failure observed | Required response |
| --- | --- |
| SQLite or filesystem failure | Diagnose implementation or environment within the selected binding. |
| Host adapter unavailable | Record unavailable and repair that adapter. |
| Proposal changes architecture | Require a superseding decision and user authority. |
| Claim of success | Require recorded evidence for every acceptance-test stage. |

The re-entry tool should display this card first and require the agent to echo
the active goal and acceptance test before guarded work. The coordination tool
should reject an intent or checkpoint that omits the active goal and phase.

`resume.md` must not become an independent, weaker instruction stream. It
should be generated from the active execution contract or explicitly point to
it.

## Limit

A protocol cannot guarantee that an agent never reasons badly. It can make
deviation visible, reject it at mutation and checkpoint boundaries, and make
continuing the agreed path easier than reopening settled choices.
