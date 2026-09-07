# Model participation responsibility matrix

This matrix turns the proposed model participation architecture into an implementation boundary. It is informative until a versioned participation profile incorporates it. The owner is the component responsible for producing or checking the result; other components may delegate the work but must preserve the stated evidence.

| ID | Behavior | Triggering operation | Model provides | Primary owner | Required result | Failure shown to model |
|---|---|---|---|---|---|---|
| MP-01 | Select the governing specification and one named workstate | `read` | Project identity or explicit capsule path | Adapter | Specification, capsule, and binding identity | `unverifiable` with the missing or conflicting identity |
| MP-02 | Bind the request to an agent/session and project | Every operation | Session handle and request ID, when available | Host binding | Stable actor, project, worktree or revision, and idempotency context | `rejected` or `unverifiable` |
| MP-03 | Build a bounded briefing from the current workstate | `read` | Goal, task, or requested scope | Adapter and projector | Goal, constraints, decisions, checkpoint, authority ceiling, active interactions, frontier, coverage | `needs_input` when required context is outside the returned page |
| MP-04 | Announce intended work and revision-pinned scopes before material changes | `announce` | Summary, intended scope, access, relied-upon facts | Adapter and binding | Confirmed intent and scope events, receipt, current frontier | `pending`, `warning`, or `blocked` according to policy |
| MP-05 | Compare current work with known participants and dependencies | `announce`, `read`, `resolve` | Scope expansion and requested context | Projector and coordination evaluator | Physical/declared overlap results with coverage and freshness | `warning` or `unverifiable`; never silent no-conflict |
| MP-06 | Record a conflict, acknowledgement, order, or user question | `resolve` | Proposed disposition, rationale, evidence, requested decision | Adapter, projector, and policy binding | Durable overlap-resolution state and any pending authority requirement | `needs_input`, `blocked`, or `unverifiable` |
| MP-07 | Recheck before integration, scope expansion, and handoff | `read`, `publish`, `checkpoint` | Current intent and requested action | Adapter and projector | Fresh frontier comparison and applicable precondition results | `stale`, `warning`, or `blocked` |
| MP-08 | Describe actual changes and evidence | `publish` | Actual scope, outputs, evidence, unfinished work | Model plus host execution tools | Change-set/result records that distinguish reported from verified facts | `rejected` for malformed data; `unverifiable` for missing evidence |
| MP-09 | Evaluate typed preconditions and verification bindings | `publish` | Requested evaluator inputs or interpretation of returned results | Evaluator and projector | Pinned dependencies, outcome, evaluator identity, subject/base binding | `unknown`, `error`, or `stale` |
| MP-10 | Create a semantic checkpoint and durable handoff | `checkpoint` | Next action, unresolved work, continuation or exit choice | Capsule publisher | Atomic capsule replacement with frontier and digest receipt | `pending` or `incomplete_handoff` |
| MP-11 | Complete exit in recoverable steps | `checkpoint` with `exit` | Confirmation to stop new work | Adapter, publisher, and presence binding | Results published, capsule confirmed, terminal intent, presence release | Explicit unfinished exit state; retry handle |
| MP-12 | Make retries safe after lost responses or crashes | Every mutating operation | Same request ID on retry | Storage binding | Idempotent original receipt or integrity conflict | Original receipt, or `rejected` for changed content |
| MP-13 | Maintain liveness observations without changing semantic state | Session lifetime | Heartbeat while active | Presence worker and watcher | Lease/session expiry observations and bounded notifications | `unavailable` or observation gap |
| MP-14 | Preserve authority boundaries | Every operation with an external effect | Requested action and named scope | Host policy and trusted binding | Explicit authority ceiling and approval evidence | `blocked` or `unverifiable`; no authority inferred from prose |
| MP-15 | Handle incomplete or unknown history | `read`, `resolve`, `publish` | Choice to request another page or stop | Projector and adapter | Missing ancestry, retention gap, or unsupported semantics exposed | `unverifiable` with recovery action |
| MP-16 | Maintain deterministic event projection | Binding replay or `read` | None beyond supplied events | Projector | Same materialized state, frontier, contested conditions, and diagnostics for equivalent event sets | Diagnostic plus excluded invalid transition |

## Composition rules

The model participant is responsible for semantic intent, scope disclosure, interpretation of returned conditions, and accurate reporting of actual work. It is not responsible for creating a valid Core envelope, choosing record revisions, computing a capsule digest, or asserting that an event was durably published.

The adapter owns the small model-facing interface. It converts requests into candidate AWP records and events, checks the request context, obtains fresh state, and reports the binding result. The adapter may be implemented by a host tool, service, or human-operated procedure.

The projector owns deterministic interpretation of accepted event bytes. It validates structure, ancestry, workstate identity, revision transitions, typed cross-record references, conflicts, and freshness according to the supported profile. Its output is evidence for the adapter; it does not authorize host actions.

The binding owns atomic publication, request idempotency, event retrieval, and the publication receipt. A binding that cannot provide these properties must disclose its mode and reach and may offer preparation without claiming confirmed publication.

The publisher owns the serialized capsule projection. It must compare the expected frontier and capsule digest before replacement and retain a recoverable pending state when projection fails. Heartbeats and watcher cursors belong to runtime state and do not enter the semantic capsule.

## Conformance composition

An implementation may claim the proposed model participation profile only for operations whose owners and failure outcomes it can demonstrate. A model plus adapter may claim request-level participation while delegating deterministic projection and atomic publication. A complete COOP-1 work claim additionally requires evidence for the applicable projector behavior, binding semantics, checkpoint, exit, and cross-record freshness rules. Bounded interaction evidence is required only when the optional consultation subprotocol is claimed. Delegation is valid only when the response identifies the delegated owner and its coverage.

The matrix should be reviewed against each operation schema, worked conversation, fixture, and test. A schema field without an owner is an unresolved design issue; an owner without a failure result is an incomplete contract.
