# Review — AWP Coordination 0.3.0-draft.1

Overall: this is a serious, unusually disciplined draft. The provenance separation (asserted / observed / verified / authorized), the refusal to let a clean merge imply compatibility, and the honesty about C3 enforcement being unprovable without a protected system are the parts that make it worth building on. The summary invariant in §27 is the right invariant.

The problems below are mostly in the machinery that has to be executable, not in the model. I've ordered them by how much they'd hurt if left unresolved.

---

## A. Structural gaps that block "two implementations produce identical projections"

### A1. A revision conflict has no recovery path

§4 mandates a strictly incrementing integer `revision` with a `prior_revision` check. §17.4 says concurrent non-commuting updates to the same record revision are a conflict. Both are right individually, but together they wedge the record:

- Two events claim `revision: 3` from `prior_revision: 2`.
- Neither can be applied (the projection would be order-dependent).
- The record's effective state is... what? Still revision 2? Is it usable? Can either author retry?
- Every recovery move you'd want — `supersede`, `withdraw`, a merge — is itself an update that needs `prior_revision: 3`, which doesn't exist in the valid projection.

§21's event list has no reconciliation event, and §18's `AWP-COORD-REVISION-CONFLICT` is a diagnostic with no defined exit.

**Fix:** define a `contested` effective state for a record with divergent successors, and add a normative reconciliation event (`record.reconciled` or type-specific `*.reconciled`) that names all competing revisions as causal parents and produces `max(competing) + 1`. Specify who may emit it (record owner, or any actor under policy) and what the resulting content must be. Without this, the fixture in §24.11 ("concurrent updates from one prior record revision") has no expected output to assert.

### A2. Monotonic integer revisions and commutative merges are incompatible as written

§17.5 permits acknowledgement-set union and evidence-reference-set union as commutative. But `evidence` is a common optional field (§4) on every record, so an evidence append *is* a record update, which must bump `revision`. Two concurrent evidence appends from revision 2 both produce revision 3 and commute — so the merged state is one record at revision 3 or 4? Undefined, and the answer changes the projection.

**Fix:** state explicitly that commutative fields are not part of the revision-counted record body — they're separate append-only sets keyed as §17 describes, and mutating them does not increment `revision`. That also cleanly explains why acknowledgements can arrive in any order (§24.12) while everything else can't.

### A3. Frontier-bound precondition results over-invalidate

§12: "Evaluation results are valid only for their recorded subject versions, repository revision, workstate frontier, evaluator version, and environment constraints." §13's readiness gate then requires every mechanical precondition to be `pass` "for the selected base/frontier."

Read literally, *any* event anywhere in the workstate advances the frontier and invalidates every precondition result. In a project with more than two active agents, `ready` becomes unreachable — the gate can never close faster than events arrive.

**Fix:** bind result validity to a declared read-set, not the frontier. The result should record `depends_on: ["contract:session-store-v2@2", "repo:app@git:91ab..."]` — the exact records/revisions the evaluator consulted — and be invalidated only when one of those changes. Keep the frontier in the record for audit, but don't make it the freshness predicate. This is the same discipline you already apply to verification binding in §14; preconditions should get it too.

### A4. Mechanical predicates are named but not defined

The twelve predicates in §12 have no argument signature, no evaluation semantics, no purity requirement, no error taxonomy, and no timeout rule. `toolchain_satisfies` and `schema_version_satisfies` imply a constraint expression language that doesn't exist anywhere in the draft. Promotion criterion §25.2 cannot be met against this section.

Also: several of these are host-relative. `toolchain_satisfies` evaluated on agent A's machine is not evidence for agent B. Either mark host-relative predicates as such and require them to record an environment block like verification results do, or move them out of the "mechanical" (portable, reproducible) category entirely — right now `record_revision_equals` and `toolchain_satisfies` sit in the same list with very different portability.

**Fix:** a predicate registry table with `predicate | subject type | argument schema | determinism class (pure / repo-relative / host-relative) | unknown conditions | error conditions`. And enumerate the permitted values of `on_false` / `on_unknown` — the example uses `"stale"` and `"block_ready"` and the spec never lists the vocabulary.

### A5. Selector drift across revisions is the hardest problem and is under-owned

Scopes (§6) are `path` + `symbol` pinned to a `base_revision`. Overlap analysis (§9) compares scopes from *different* bases. Resolving `src/auth/session.ts#rotateRefreshToken` at base X against base Y — after a rename, a move, an extraction — is the load-bearing operation for the module's central claim, and it's specified nowhere. Open issue §26.2 mentions "language-specific selector profiles" as if this were a completeness detail; it's actually the correctness core of C2.

Note also that this failure mode has no diagnostic code. Add `AWP-COORD-SELECTOR-UNRESOLVABLE` (selector does not resolve at the revision being compared) and specify that unresolvable selectors force `unknown` overlap, never `none`. Right now §9's `none` ("no relevant intersection was found") is dangerously reachable by a resolution failure.

### A6. No event example anywhere

The projection model is entirely event-driven, `prior_revision` lives on the event, and §21 lists 80+ event kinds — but the document never shows a single event. Every example is a materialized record. A reader cannot tell what the envelope/payload split is, where `causal_parents` live, or how an event references the record revision it produces.

**Fix:** one canonical event example early (§4 or a new §4.1), plus a short table mapping event kind → required payload fields for at least the C1 set.

---

## B. Internal contradictions and lifecycle defects

### B1. Terminal-state claims contradict their own tables

- §10: "All states except `open` are terminal." The table immediately permits `timed_out` → `escalated` and `rejected` → `escalated`. Those are transitions out of terminal states.
- §9: `resolved` → `overlap.reopened` → `open`, while `overlap.superseded` applies "from nonterminal." Is `resolved` terminal or not?
- §11 and §13 and §16 never state their terminal sets at all; only §7 does.

**Fix:** every lifecycle section gets an explicit terminal set, and "terminal" must mean *no outgoing transitions*. If escalation from a timed-out negotiation is desired, either the state isn't terminal or escalation creates a successor record that references it (which is what §10's "a further round creates a successor negotiation" already implies — apply the same rule to escalation).

### B2. `stale` → `ready` contradicts §15

§13's table permits `changeset.ready` from `stale`. §15 says staleness "is cleared only by a successful `revalidate`, `rebase`, or `supersede` transition with fresh evidence." Also: `revalidate` is named in §15 as one of the three clearing mechanisms and appears in *no* event list in §21 (only `.rebased` exists).

**Fix:** add `changeset.revalidated` (and the general `revalidate` event shape), and remove `stale` from the direct predecessors of `ready`.

### B3. `status` is overloaded with two different meanings

§4 makes `status` a required common field carrying lifecycle state. But the examples use it for outcome: `observed_scope` has `status: "complete"`, `precondition_result` has `status: "pass"`, `verification_result` has `status: "pass"` *and* an `outcome` object. So `status` means "where is this record in its lifecycle" for mutable records and "what did it conclude" for immutable results.

**Fix:** immutable result records get `status: final | superseded` (lifecycle) and `outcome: pass | fail | unknown | error` (conclusion). Otherwise a generic C0 processor that reasons over `status` — which §3 explicitly invites — will draw wrong conclusions.

### B4. The precondition example is not a valid record

§12's precondition object has no `type`, `module`, `revision`, `created_by`, or `created_at`, all of which §4 says *every* module record contains. Yet §21 defines `precondition.created/.updated/.superseded`, so it is a record.

Related: §6 says a scope "is embedded in or referenced by" an intent/claim/change set, while the scope example is a full record with its own `id` and `revision`. Embedding a revisioned record inside another revisioned record creates two update paths for one piece of state. Pick one — I'd make scopes and preconditions first-class records referenced by ID only, since staleness propagation (§15) needs stable edges into them.

### B5. Reference grammar is never defined

`contract:session-store-v2@2`, `intent:auth-refresh@1`, `semantic:session-store-contract@2` are load-bearing throughout, but the draft never says: what `@N` means, what a bare reference resolves to ("latest" is ill-defined under concurrency), what happens when a pinned revision is contested (A1) or doesn't exist, or whether a reference to a superseded revision is valid.

**Fix:** a short normative subsection on reference syntax and resolution, including the rule that safety-relevant references MUST be revision-pinned.

### B6. Time never causes state changes — say so

Deadlines appear in intents (§7 `termination.deadline`), commitments (§10), negotiations (§10), and leases (§19 `expired`). Only negotiation timeout mentions a "clock authority." But a projection must be a pure function of events, so nothing can transition because a clock passed a value — some actor must observe it and emit an event.

**Fix:** a global rule: *the passage of time never changes projected state; an identified actor MUST record a `.timed_out` / `.expired` event under a declared clock authority.* This matters most for leases, where an implicit expiry would be a safety claim you can't back up — and §19 already makes exactly this argument about fencing.

### B7. "Authorized actor" conditions are unverifiable below C3

`intent.abandoned` requires an "authorized actor," `integration.approved` requires "required policy/authority," `contract.withdrawn` requires a "permitted owner" — but §20 only binds principals at C3. §3 is admirably honest that `block` has no external effect below C3; apply the same sentence to authority generally: *below C3, all authority fields are asserted claims, and a C1/C2 processor MUST present them as asserted, never as verified.* Otherwise `AWP-COORD-AUTHORITY-INSUFFICIENT` implies a check that no C1 implementation can actually perform.

### B8. Integration plans have no partial-failure semantics

§16's plan carries "exact change-set revisions" (plural) and a dependency-derived order. If a plan of five change sets integrates three and fails on the fourth, the plan goes to `failed` — but what happens to the three integrated change sets, whose own lifecycle (§13) already says `integrated`? Is a plan atomic? Is rollback required or advisory? "Rollback status" appears in the result fields with no state model behind it.

**Fix:** declare whether plans are atomic, all-or-nothing-per-step, or best-effort; add per-input disposition to the integration result; and specify the change-set states after a partially failed plan.

---

## C. Naming and modeling inconsistencies

- **Three identifier namespaces for the same idea.** §13's `effects.reads/writes` use bare dotted strings (`"session.refresh_generation"`), which is neither a `semantic:` ID nor a `scope:` ID. Either make them semantic definition references or define the third namespace. As it stands, effects can't participate in overlap analysis, which seems to defeat their purpose.
- **Post-change revision has three names.** `result_revision` (§8), `revision_tested` (§14), and the integration result's "resulting repository revision" (§16). Unify on `base_revision` / `result_revision`.
- **Evaluator versioning is doubled.** `"evaluator": "urn:awp:evaluator:record-revision:1"` (§12 precondition) vs `"evaluator": {"id": "urn:awp:evaluator:record-revision:1", "version": "1.0.0"}` (§12 result). Is the trailing `:1` an interface version and `1.0.0` an implementation version? Say so, or drop one.
- **`unknown_overlap_policy` vs per-record `policy_action`.** §3 sets a module-level policy; §9's overlap record carries `policy_action`. Precedence is unspecified. Also enumerate `lease_enforcement` values (only `"none"` appears).
- **Diagnostic severity is unassigned.** §18 says diagnostics have severity and that errors invalidate while warnings preserve — but no code is assigned a severity, and several are policy-dependent. For reproducibility (§25.2/§25.3), severity must be a normative function of `(code, configuration)`. Two implementations disagreeing on error-vs-warning is a projection difference.
- **Missing diagnostic codes** for: commitment violation, fencing-token rejection (distinct from `ENFORCEMENT-UNVERIFIABLE`), selector resolution failure (A5), and contested-record state (A1).
- **§17.2 determinism is stated too weakly.** "Deterministic topological order, using event ID only to break ties" doesn't pin an algorithm — topological orders aren't unique, and tie-breaking depends on *when* you break ties. Specify it concretely (e.g. Kahn's algorithm with a min-heap on event ID over the ready set), or — better — state that the projection is order-independent by construction and use the ordering only for diagnostic emission order. The second is a much stronger and more testable claim, and given that non-commuting concurrency is already a conflict, you may be close to being able to make it.

---

## D. Missing concerns

1. **Retention and compaction.** Append-only coordination on a long-lived repo grows without bound, and portability (a bundle you hand to another agent) is one of AWP's four purposes. What may be dropped after terminal states? Does a snapshot license pruning? Currently unaddressed even in open issues.
2. **Ownership handoff.** §24.15 tests "agent abandonment and reassignment" and the module's whole point includes re-entry and handoff, but `owners` is an optional common field with no transition rule and there is no `intent.reassigned` event. Reassignment is currently expressible only as withdraw-plus-successor, which loses continuity.
3. **`relied_upon_read` scale.** §6 introduces the best idea in the document, and §7 tells actors to announce relied-upon reads. In practice an agent reads dozens to hundreds of symbols per task. What's the guidance on granularity — is this for deliberately narrow assumptions, or is a tool expected to emit them automatically? Without a stated discipline, this either goes unused or floods overlap analysis. A short "authoring guidance" note would help more than another field.
4. **MPAC citation.** §22 maps to MPAC without a reference, version, or URL. If it's external, cite it; if it's aspirational, mark it so. Also mark §22 explicitly non-normative — §25.7 asks for a semantic-overclaiming review, which is easier if the section already disclaims normativity.

---

## E. The strategic point

The readiness gate (§13) has eight clauses. Reaching `ready` on one change set requires an intent, scopes, an observed scope, preconditions with evaluated results, contract references at pinned revisions, verification bound to exact inputs, resolved overlaps with acknowledgements, and valid authority. That is a lot of authored state per unit of work, and C1 — the first level that does anything beyond preserving records — demands nearly all of it.

Two suggestions:

**Split C1.** Something like C1a = intents, scopes, overlap records, revision/transition validation, staleness propagation; C1b = typed preconditions, verification binding, change-set readiness gate. A pair of agents can adopt C1a in an afternoon and get the module's core value (durable declared intent + overlap detection across sessions). C1 as currently scoped is a months-long implementation before anyone learns whether the model helps.

**Move the benchmark forward.** §25.6 is the only promotion criterion that tests whether the protocol *helps*; the other seven test whether it's internally consistent. And §26.7 already names the metric that decides adoption: false alarms. A C2 semantic analyzer with a high false-positive rate on `negotiation_required` gets switched off within a week, no matter how sound the projection semantics are. Consider running a cheap version of that benchmark against C1a before finishing C1b/C2/C3 — it's the experiment most likely to change the design, and right now it's scheduled last.

---

## F. Small things

- §3: "A reader MAY support a lower level, but it MUST reject the workstate for safe continuation when the module is required and unsupported semantics affect the requested action." Worth clarifying that this is per-action, not per-workstate — a C0 reader should still be able to *display* a C2 workstate.
- §4: the unknown-record-type rule needs to distinguish "unknown to this spec version" from "known to the spec but above my conformance level." As written, a C1 implementation encountering `semantic_definition` records (a C2 feature, §5) may have to declare the projection `unverifiable`, which would make C1 unusable in any project also using C2. State that C1 preserves and passes through higher-level record types without interpreting them, and that only genuinely unregistered types trigger `unverifiable`.
- §8: `status: "complete"` for an observed scope — see B3.
- §13: `"removes": []` — confirm empty arrays are meaningful (asserted "nothing removed") rather than omissible, since the readiness gate reasons over effects.
- §19: "Renewal creates a new expiration and MUST NOT reduce the fencing token" — should be MUST increase, or state that renewal may reuse the token while grants must increase. As written a renewal could reuse the same token indefinitely, which is probably intended but reads ambiguously next to "monotonically increasing."
- §23: the reference procedure is linear, but the model is explicitly concurrent and includes reopening, staleness, and rebasing. A note that this is the happy path, with pointers to where loops re-enter, would prevent implementers from reading it as a state machine.
