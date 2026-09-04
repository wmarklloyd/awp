# AWP 0.5.0 feedback evaluation

**Reviewed input:** `ClaudeOpus _AWP_0.5.0_review.md`  
**Project goals:** `purpose.txt`  
**Status:** Design disposition; not a claim that every proposed change is adopted

## Decision filter

AWP serves four linked goals: rich cross-agent handoff, canonical orientation for a new project agent, canonical re-entry after leaving a project, and coordination of interdependent work above source control. Changes are evaluated by whether they improve one of those goals without making AWP dependent on one source-control system or claiming unproven distributed coordination guarantees.

## Accepted priorities

The review correctly identifies these high-value issues:

1. Correct the shortened SHA-256 example digests.
2. Define record revisions and update preconditions.
3. Define where actor declarations are stored and resolved.
4. Define source-digest scope for omitted history.
5. Repair repository-discovery schema identification so copied `.awp.json` files do not point into this repository.
6. Define precedence when Handoff and Resume records both appear.
7. Add repository revision bindings and a conservative freshness procedure for project re-entry.
8. Clarify module-data placement, unknown-field preservation, frontier validation, genesis/fork rules, and digest edge cases.
9. Build conformance fixtures with expected diagnostics, then measure handoff and re-entry quality against ordinary repository orientation.

These items directly improve trustworthy handoff and re-entry. They should precede further work on advanced coordination.

## Direction retained

AWP remains transport- and source-control-independent. Synchronization stays optional because a Capsule can travel through APIs, queues, files, or repositories; a future Git binding may delegate replication to Git without removing the generic module.

Core, Capsule, and Handoff remain sufficient for orientation and re-entry. Coordination is already optional and experimental, so users of the first three goals do not need to implement leases, overlap classification, contracts, or integration plans.

Event ancestry remains the causal model. Timestamps, a single monotonic sequence, a Git merge, or a union merge driver are not equivalent to causal ordering or distributed mutual exclusion.

## Coordination backlog

The review’s most valuable future Coordination recommendations are diff-versus-declared-scope checks, a project-scoped registry for semantic selectors, a conservative posture for unknown overlap, per-participant contract adoption, mechanically checkable preconditions separated from asserted invariants, verification bound to its base revision, and complete lifecycle-event coverage.

These are Phase-2 research and fixture work. AWP must not claim that a file-based ledger, event-ID tie-break, or source-control merge alone provides enforced leases or consensus.

## Not adopted now

The following recommendations are deferred or rejected in their proposed form:

- removing Synchronization and making Git mandatory;
- replacing the event DAG with timestamps and one sequence number;
- treating a union-merged ledger as a distributed lock service;
- adding a separate identity-free message format outside the workstate model;
- reducing the epistemic-status vocabulary without empirical evidence;
- expanding the experimental coordination protocol before the handoff and re-entry path is tested.

## Success criterion

The primary test remains practical: compared with ordinary repository scraping, does an agent given a current AWP capsule take the correct first action sooner, make fewer unsupported assumptions, preserve constraints and authority boundaries, and identify when the state is stale or incomplete?
