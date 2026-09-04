# AWP 0.5.0 — Specification Review

**Subject:** `AWP_SPECIFICATION_0_5_0_bundle.md` (family overview + Core, Capsule, Handoff, Artifact, Synchronization, Coordination, Security, Adapter Framework)
**Review date:** 2026-09-03

---

## 0. Context for this review

This review was written in two passes. The first pass evaluated the bundle on its own terms, as a standards document. The second pass revised that assessment after the stated intent became clear:

1. Send another agent a problem description with more structure than a Markdown file provides.
2. Let a new agent entering a project get context from a canonical source instead of scraping the whole repository.
3. Let a returning agent re-enter a project and get up to speed the same way.
4. Let multiple agents work on one project, coordinating above the level of git commits on interdependent code.

That intent matters, because it invalidates a chunk of the first pass and sharpens the rest. Sections are marked where the framing changed the conclusion.

**One-line summary:** the semantic model is strong and the security posture is consistently right, but the spec is roughly twice the size the goals require, the parts that matter most are the least developed, and almost nothing in it is currently testable.

---

## 1. What is working well

These are worth protecting through any restructuring.

- **Epistemic integrity model (Core §9).** Claim statuses, the rule that confidence must not replace epistemic status, the requirement that contradictory claims stay distinct until a resolution event cites evidence, and "a summary is not independent evidence." This is the strongest part of the document and is directly aimed at the real failure mode of agent-written state.
- **Authority as evidence, never as command.** Imported authority is evaluated against local policy. A receiver with more access than the sender is warned about becoming a confused deputy. Consistent throughout.
- **No implicit side effects.** Referencing a remote artifact does not trigger retrieval. Discovering a URI does not trigger network access. Parsing or signing does not authorize execution.
- **`do_not_assume` (Handoff §4).** The single most useful field in the spec for use case 1, because it targets the exact failure mode of a fresh agent confidently filling gaps.
- **Availability vocabulary** (`available` / `retrievable` / `unavailable` / `withheld` / `redacted`) with the rule that a URI alone is not proof of retrievability.
- **Honesty about limits.** "A successful byte-level merge is not proof of semantic compatibility." "A valid signature proves none of the other dimensions." "Passing is evidence of a check, not proof of absence." The spec does not oversell itself.
- **The separation of logical modules from physical representation.** Correct call, and it survives the restructuring proposed below.

---

## 2. Scope: the spec is about twice the size the goals require

### 2.1 Synchronization duplicates git and should be cut

*(This conclusion is a result of the second pass; the first pass reviewed Sync on its own terms.)*

Use cases 2, 3 and 4 all live inside a repository, with the workstate committed alongside the code. Git is therefore already the replication layer: it handles concurrent replicas, ancestry, merge, and conflict detection.

AWP Synchronization rebuilds all of that — deltas, base and result frontiers, antichains, divergence classification, idempotent application — for a file git is already synchronising. Worse, AWP's DAG cannot see git's, so two ancestry graphs exist that can disagree.

**Recommendation.** Remove Synchronization. Let the workstate be an ordinary tracked file. Concurrent edits produce a git merge conflict, which every agent and every human already knows how to handle.

What replaces it is much smaller:

- an append-mostly file layout that merges cleanly (one record per line, stable ordering, no rewritten preamble);
- a `.gitattributes` union merge driver for append-only paths;
- a documented convention for resolving a conflicted region.

This also removes the frontier machinery from Core and removes Coordination's dependency on Sync.

The event log is still worth keeping as an **append-only history** — what happened, in order, with evidence. It is not worth keeping as a **replicated causal graph**. With one canonical file per project, a monotonic sequence number plus RFC 3339 timestamps is sufficient.

### 2.2 Split orientation from coordination

Use cases 1–3 are read-mostly orientation. Use case 4 is concurrent write coordination. They share record vocabulary and almost nothing else. Bundling them means anyone who wants "give the new agent context" must implement leases, overlap classification, and integration plans.

**Recommendation.** A base specification covering orientation only: manifest, records, checkpoint, resume, discovery, briefing. That is a genuinely small document — on the order of 150–200 lines — and it delivers most of the value. Coordination ships separately, once the base has been exercised.

### 2.3 Standards-process items are not relevant here

The first pass flagged URN namespace registration, IANA media-type registration, ABNF grammars, internationalisation, and IPR/licence furniture. For a convention that a handful of agents and some repo tooling need to agree on, these do not matter. **Ignore them** unless the project later aims at external adoption.

Two carve-outs:

- `"$schema": "schemas/awp-discovery-0.1.schema.json"` inside a *user project's* `.awp.json` resolves to a path that does not exist there. Use an absolute URI. This is a functional bug, not a process nicety.
- The capsule marker syntax still needs to be exact enough that two implementations agree, even if it is never written as formal ABNF.

---

## 3. Blocking correctness issues

These are real defects that will propagate into implementations.

### 3.1 The example SHA-256 digests are 128-bit

`"algorithm": "sha256", "digest": "7d8c9f2ae43b1c8066a71a5d93470e11"` is 32 hex characters. SHA-256 is 64. This appears in:

- the Artifact descriptor (Artifact §2);
- the content-addressed package path `artifacts/sha256/7d/7d8c9f2ae43b1c8066a71a5d93470e11.bin`;
- the redaction tombstone (Artifact §7).

The same string is also used as the capsule boundary token in Capsule §5, which suggests copy-paste. Anyone implementing from the examples will get this wrong.

### 3.2 `revision` is required by two rules and never defined

Core §10 says an update "SHOULD carry ... the prior record revision." Synchronization §7 says "an update with a prior-record revision applies only when that precondition holds." No `revision` field appears in the Core record structure (§8).

Without it, the rule against silent last-write-wins is unenforceable. This matters specifically for use case 4.

### 3.3 Actors have no defined storage location

Core §7 defines an actor object shape. The record table in §8 does not list `actor` as a record type. The snapshot `records` object has no `actors` array. `created_by` in the manifest is a bare reference with nothing to resolve it against.

### 3.4 "Source digest" is referenced but never defined

Core §11 and Synchronization §3 both require disclosing a source digest for omitted history. Nothing defines what bytes it covers or how they are canonicalised. The same applies to the snapshot digest implied by `invalid_projection`.

### 3.5 No integrity binding over machine state in a capsule

`generated_digest` covers only the prose region between the generated markers. The `manifest`, `snapshot`, and `events` sections have no digest. A machine-state section inside a `.awp.md` can be edited while the briefing still reports `current`.

Given that Security §2's threat model explicitly includes compromised records, this is a gap. Add a `state_digest` in front matter covering the canonicalised machine sections, and define what canonicalised means.

### 3.6 Digest byte-range edge cases are unspecified

The briefing digest rule ("after the LF terminating the start marker and ending before the LF preceding the end marker") does not say what happens with an empty region, a missing final newline, a byte-order mark, or trailing whitespace. Add these, plus an explicit statement on Unicode normalisation — including "none is applied," if that is the intent.

---

## 4. Design concerns in the base layer

### 4.1 Module versions are bumped for the wrong reason

Family §9 says the optional modules advance to 0.2.0 "to declare compatibility with this Core release." That defeats independent versioning: Artifact 0.2.0 appears semantically identical to its 0.4.0 predecessor.

The point of per-module semver is that a module bumps when *it* changes. Core compatibility belongs in a declared dependency range:

```json
{
  "id": "urn:awp:artifact",
  "version": "0.1.0",
  "depends": { "urn:awp:core": ">=0.5.0 <0.6.0" }
}
```

Otherwise every Core release forces a lockstep bump across the family, `modules.json` becomes the real version authority, and the module numbers become decoration.

Related: the version range syntax (`"0.5.x"`) is used in the conformance example and in dependency declarations but never defined. Adopt a named scheme or use explicit `min`/`max` fields.

### 4.2 Module data has four possible homes

A module's data can live in:

- the module declaration's `configuration` object;
- the manifest's top-level `module_data`;
- the snapshot's `modules` object;
- a capsule `module:` section.

Coordination §3 uses `configuration`. Security §3 uses `module_data`. Pick one location for manifest-time configuration and one for materialised state, and define precedence when both are present. This will cause reader bugs between your own tools long before it causes them between vendors.

### 4.3 Core leaks optional-module semantics in three places

- The `checkpoint` record requires `resumption_level`, but "level semantics belong to Handoff when that module is declared." Core mandates a field it cannot interpret.
- Family §3 defines a `representation` field on module declarations, but its `kind` values (`package-path`, `capsule-section`, `remote`, `events-only`) are defined in Capsule §8.
- Handoff's `authority_ceiling` uses the Core side-effect class enum but never says so; a reader has to infer the vocabulary.

Fix the first two by moving the fields into module extension objects. Fix the third by stating the reference explicitly.

### 4.4 `resume` and `handoff` are near-duplicate records

Both carry `checkpoint`, `read_first`, `authority_ceiling`, and an action field (`requested_action` versus `recommended_next_action`). Nothing states what happens when both exist and disagree — which ceiling wins?

Either make `resume` a mode of `handoff`, or add an explicit precedence rule.

### 4.5 Nine epistemic statuses is more than will be used consistently

`verified / observed / reported / inferred / unknown`, plus `stale` as a derived flag, covers real agent behaviour. `disputed`, `refuted`, and `superseded` overlap with each other and with record lifecycle events. Fewer categories get applied correctly; nine get guessed at.

### 4.6 Other underspecified points

- **Frontier semantics.** Core §6 defines the frontier relative to "the represented replica," but the manifest serialises it. State that a serialised frontier is relative to the events present in that representation. Core should also require the frontier to be an antichain (Sync §3 requires it of snapshots; Core never does) and say what a reader does when it is not.
- **Genesis and forks.** "`parents` empty only for a genesis event" is singular — is more than one genesis permitted? When a fork creates a new `workstate_id` with a recorded parent frontier, do the first events reference parents from the other workstate? Cross-workstate parent references are otherwise implicitly forbidden.
- **`sequence` scope.** Described as "meaningful only within its declared single-writer scope," but there is no field in which to declare that scope.
- **Unknown fields in known modules.** Unknown *modules* are handled thoroughly; there is no must-ignore rule for unrecognised fields inside a recognised event kind. Minor-version additivity depends on it.
- **Snapshot completeness is undeclarable.** Empty arrays cannot distinguish "no goals exist" from "goals are not materialised here." Add a `materialized` list.
- **No common diagnostic structure.** There are at least five result vocabularies (`current`/`stale`/`divergent`/`unverifiable`; `absent`/`invalid`/`unsafe`/`unavailable`; `accepted`/`qualified`/`rejected`; artifact statuses; overlap classes). Many rules say "MUST report," but a report with no defined shape cannot be tested for. Define one diagnostic object — code, severity, subject, detail — and let each vocabulary be a code namespace.
- **`plan` requires a field named `goal`** while `goal` is also a record type. Rename to `goal_ref`.
- **Conditional dependency.** Family §2 gives Security a dependency on Artifact "when artifact controls are used." `modules.json` likely cannot express that; model it as a capability-conditional dependency with explicit syntax.

---

## 5. Use-case-specific gaps

### 5.1 Use case 1 — sending another agent a problem

This is a *message*, not a workstate, but the current design requires carrying `workstate_id`, a frontier, a manifest, and module declarations in order to send one.

The valuable content already exists in the Handoff record: `do_not_assume`, `read_first`, `requested_action`, `authority_ceiling`, and dependency availability.

**Recommendation.** Give this a standalone profile with no identity ceremony: the problem, constraints, what has been tried and ruled out with reasons, what is unknown, and what a good answer looks like.

### 5.2 Use cases 2 and 3 — re-entry without scraping

Three things decide whether this works. None is currently addressed.

**Freshness against the actual repository.** The workstate says work is in progress at `git:91ab4e7`; HEAD is now elsewhere. Nothing lets an agent tell whether the capsule is still true. `freshness_policy` describes what to do about staleness but provides no means of detecting it. The failure mode is worse than scraping, because the agent trusts a confidently-worded stale document.

> Minimum fix: every checkpoint records the revision it was written at, and every verified claim records the revision it was verified at. The reader diffs against HEAD and downgrades anything touching changed paths to `stale`. **This single mechanism is worth more than the entire Synchronization module.**

**Context budget.** The premise is "do not read the whole project," yet a capsule carrying manifest, snapshot, events, and module sections can easily cost more than a targeted scrape. Handoff §5 says the receiver "MUST NOT omit relevant required state merely to meet a context budget," which is backwards for a real agent — it always has a budget.

> Invert it. Define a bounded brief (goals, constraints, current status, next action, what is uncertain, what not to assume) with a hard size ceiling, and make everything else explicitly fetch-on-demand with an index. Design for *correct after reading only the brief, plus knowing what it has not read*.

**Who updates it.** If maintaining the workstate is a separate manual step, it rots within days and use cases 2 and 3 die with it. The realistic answer is that the working agent updates it at end of session, which means the write path must be cheap. It currently is not: regenerating a manifest, recomputing `generated_digest`, and maintaining boundary-token sections is tooling-only work.

> Either ship that tooling as part of the protocol, or make the format hand-writable and treat digests as optional — present means tool-generated and verifiable, absent means hand-maintained and trust-but-verify.

**Related format issue.** The boundary-token capsule format is hostile to its primary reader. An LLM asked to edit a file containing `<!-- awp:7d8c9f2a...:module:start id="..." -->` will eventually corrupt it. Make the directory layout the default and the single file an export.

---

## 6. Coordination (use case 4) — detailed review

Assume compliance is enforced at a chokepoint. Enforcement can verify that a declaration exists, that it matches the actual diff, and that a precondition still holds. It **cannot** verify that an agent declared the right semantic effects, or that two agents mean the same thing by an identifier. The protocol must be designed so the checkable parts carry the weight.

Reviewed in dependency order, since each sub-protocol rests on the previous.

### 6.1 Scopes are declared before the work exists

Overlap classification, leases, and conflict detection all consume declared scopes. But an agent announcing an intent has not yet read the code it will change. It declares `src/auth/session.ts` and `rotateRefreshToken`, then discovers the token store needs a schema change, then discovers a caller in a module it never mentioned.

The spec's answer — the actor "SHOULD update the intent before proceeding when practical" — will not happen. The agent is mid-task, the update is friction, and nothing detects the omission.

**Fix.** Treat the declared scope as a checkable claim, not a fact. At publish time the chokepoint computes the actual touched scope from the diff and compares it to the declared scope. Divergence becomes a first-class event. A change set whose actual scope exceeds its declared scope cannot reach `ready` until the intent is amended or the overlap is re-run against the true scope.

Under-declaration then becomes detectable rather than silently corrupting every downstream classification — and repeated under-declaration becomes a measurable signal about which agents produce unreliable coordination data.

### 6.2 The semantic namespace is unshared — the deepest problem

The entire "above git" claim rests on this.

Path intersection is what git already gives you. The new capability is semantic selectors: `behavior:refresh-token-rotation`, `invariant:no-plaintext-token-storage`, `contract:session-store-v2`. Two agents overlap semantically when they name the same behaviour.

Nothing makes them name it the same way. Agent A writes `behavior:refresh-token-rotation`. Agent B writes `behavior:token-refresh` or `session.refresh_generation`. They collide in reality and never collide in the record. The classifier sees nothing, and you have fallen back to path intersection.

**Fix.** A project-scoped registry, declared in the workstate, listing the contracts, invariants, and behaviours this project recognises. Selectors reference registered IDs. Minting a new one is an explicit, reviewable event rather than a side effect of writing an intent. An unregistered selector classifies as `unknown`, which under enforcement means blocking.

This converts free text into an actual coordination surface, and it plays to what LLM agents are good at: proposing a new behaviour identifier, and noticing that a proposed one duplicates an existing entry.

### 6.3 Overlap classification has no procedure and no ownership

Seven categories, no algorithm, and "a coordinator or peer" as the actor. In the peer case, two agents can classify the same pair differently and both proceed.

**Fix.** Classification is a proposal by one party requiring acknowledgement from the other before it binds. Unacknowledged classification is not a result. Disagreement between two classifications is its own state that escalates. Otherwise `compatible` means "one agent decided it was fine," which is the situation you already have without the protocol.

`unknown` also needs a stated posture rather than "not equivalent to compatible." Under enforcement, unknown blocks.

### 6.4 `negotiation_required` is a dead end

It is a classification with no defined next step: no message shape, no initiator, no termination condition, no arbiter.

This is where LLM agents have a real advantage over any prior coordination system, and it is the least developed part of the module. They can genuinely negotiate — propose a scope partition, counter with a contract, explain why an ordering is required. What is missing is the frame that makes it terminate.

**Fix.** A negotiation record with `proposal`, `counter`, `accepted`, and `escalated` states; a bounded number of rounds or a wall-clock timeout; and a designated decider when the rounds run out (integration owner, priority rule, or human). Escalation should be cheap and expected, not a failure — two agents recognising in three exchanges that a human should decide is a good outcome.

Without termination, two agents can negotiate indefinitely or both stall waiting for the other.

### 6.5 Relied-upon reads are the best idea here and have no mechanism

`shared_read` promising that relied-upon state stays stable, and "a relied-upon read may conflict with a write," is a genuine capability git does not have. Git has no idea you read a file and built an assumption on it.

But there is no way for a writer to discover an outstanding read.

**Fix.** A reverse index from scope to active readers, and a rule that writing into a scope with an active `shared_read` is at minimum `negotiation_required`. The read declaration must also state *what* was relied on — relying on a function's existence differs from relying on its error semantics.

Under enforcement this is implementable and high-value. Develop it further than exclusive leases, which need a live coordinator and are mostly inert in the file-based case.

### 6.6 Contracts: the lifecycle contradicts per-participant adoption

The stated lifecycle is a single global progression: `proposed → negotiating → accepted → implemented → verified`. The prose also says a contract tracks "adoption status per participant." These conflict — a contract is routinely implemented by the producer and not yet by the consumer.

**Fix.** Split them. The contract revision has a global status of `proposed`, `accepted`, or `superseded`. Each participant has its own adoption state against that revision. `implemented` and `verified` are per-participant facts, not properties of the contract.

Acceptance also has no quorum rule — nothing says who may move a contract to `accepted`. It should require the owner plus every declared consumer, or one agent accepts unilaterally and the other finds out later.

Contract-first is the pattern that works with no coordinator at all. Invest here before anywhere else in the module.

### 6.7 Preconditions mix two different kinds of thing

The example lists `contract:session-store-v2@2` and `invariant:no-plaintext-token-storage` in one array. The first is mechanically checkable by comparing a revision. The second is not checkable by anything.

**Fix.** Separate them.

- **Mechanical preconditions:** revision, digest, symbol presence, schema version, test baseline, toolchain. A hook evaluates these and fails hard.
- **Asserted preconditions:** invariants and behavioural properties. Each must name the verification execution that established it, plus the base revision that execution ran against.

As written, a hook receiving a mixed list cannot tell which entries it is capable of enforcing, so it either fails on the ones it cannot evaluate or silently passes them.

### 6.8 Verification has no base binding, so it never goes stale

`verification: ["execution:auth-tests-842"]` records that tests ran but not what base they ran against. When the base moves or a precondition changes, the change set becomes `stale` while the verification field still looks satisfied.

**Fix.** Verification results carry the base revision and the contract revisions in effect when they ran. A change set whose base has moved past its verification base is unverified, not verified.

### 6.9 Staleness does not propagate

Revising a contract makes dependent change sets stale — the spec says so. But nothing computes the dependents: there is no reverse index and no declared dependency between change sets. Change set B may build on A's declared effects with no way to express that.

**Fix.** Change-set-to-change-set dependencies plus a transitive staleness rule, so revising a contract or superseding a change set marks the downstream closure stale in one operation. Without it, staleness is discovered one integration failure at a time.

### 6.10 Integration order is hand-supplied when it is derivable

The integration plan carries `order` as a literal list. It should be derived by topological sort over declared preconditions, contract dependencies, and read/write effects, with an author-supplied order treated as an override requiring justification when it contradicts the derived order.

As written, an ordering mistake is silent — and ordering mistakes are exactly what this module exists to catch.

### 6.11 Deadlock and liveness are unaddressed

Coordination §15 covers an actor going away. It does not cover two agents each holding what the other needs. With enforcement, mutual blocking becomes a real stall rather than an advisory annoyance.

**Fix.** Detection over the lease and dependency graph, plus a resolution rule: a total order on scope acquisition, preemption by the integration owner, or escalation on timeout.

### 6.12 Statuses exist that no event can produce

Change-set statuses include `stale`, `integrating`, `failed`, `withdrawn`, and `superseded`. The event kinds are `changeset.proposed`, `changeset.stale`, `changeset.rebased`, `changeset.ready`. Nothing produces `withdrawn`, `superseded`, `integrating`, or `failed`.

Contracts have the same problem: no `contract.rejected`, and no per-participant adoption event.

Every status needs a transition that reaches it, or the state machine cannot be replayed. Also missing and needed: scope expansion, precondition failure, verification invalidation, and the negotiation kinds.

### 6.13 Suggested restructuring: three tiers

The module is weighted toward the before-work layer, which is the hard layer to enforce and the one most damaged by scope drift. The after-work layer is where enforcement is easy and the value is concrete.

**Tier 1 — works with no coordinator, no live state, no registry.**
Contracts, mechanically checkable preconditions, combined verification at integration. Two agents agree on an interface before implementing; a change set carries the contract revisions it assumed; the chokepoint refuses to integrate when those have moved. This already delivers what git cannot do.

**Tier 2 — the real "above git" capability.**
Semantic registry, declared scopes with publish-time drift checking, relied-upon reads, overlap classification with acknowledgement. Depends on the registry existing.

**Tier 3 — needs a live coordinator to be worth much.**
Leases, negotiation, integration ownership, deadlock handling.

The strongest sentence in the module is that a successful git merge is not proof of semantic compatibility. The most defensible claim is that the protocol forces combined verification against declared assumptions at integration time. Restructure around that claim and treat the intent and lease machinery as the optional early-warning layer it actually is.

---

## 7. A standard cooperation ledger

The spec already has one — `events.jsonl`, described as a unified append-only log that all module events join — but it is used as the wrong kind of thing. Coordination state lives in `modules/coordination/state.json` and in records with independently maintained status fields. The ledger records what happened *alongside* the state rather than *defining* it.

**Making the ledger authoritative for coordination is the single change that fixes the most problems in this review.**

### 7.1 What it buys

- **Every status gets a producing event by construction.** §6.12's class of bug becomes impossible to write, because there is no other way to reach any status.
- **It is the chokepoint.** Claiming work and doing work become the same act: you do not hold a lease, you appended a `lease.granted` that no one has superseded. A hook checking "did this agent append a claim covering the scope this diff touches" is trivial to write — which matters, because an enforcement mechanism that is hard to implement will not be implemented.
- **Concurrent claims become deterministically resolvable without a coordinator.** Two agents append conflicting `lease.granted` events for the same scope, neither having seen the other. With a total order over the ledger plus a fixed tie-break (lowest event ID wins), both agents independently compute the same winner and the loser knows to back off. You get the practical effect of mutual exclusion from a conflict-resolution rule — no live coordinator, no term or epoch, no distributed consensus. Coordination §7's honest admission that leases are inert without a live coordinator stops being a limitation.
- **Git already provides the atomicity.** A non-fast-forward push is rejected: that is compare-and-swap on a ref. If the ledger is a committed file, git enforces that you saw the current tip before extending it. What you need is a union merge driver on the ledger path plus the deterministic tie-break above. Small machinery for real coordination semantics.
- **Negotiation gets a medium.** Proposals, counters, and acceptances are appends with visible ordering, which is what makes rounds countable and timeouts enforceable. `negotiation_required` currently terminates nowhere partly because there is no medium for the exchange.
- **Identifier registration becomes first-writer-wins.** The §6.2 registry is naturally a ledger projection. Minting `behavior:refresh-token-rotation` is an append; a second agent proposing a near-duplicate can see the existing one.

This is consistent with cutting Synchronization (§2.1). Git remains the replication layer; the ledger is a file it replicates. You are not rebuilding delta exchange and frontier reconciliation, you are choosing a file format that merges cleanly and defining a fold over it.

### 7.2 What it does not buy

- It will not detect under-declared scope. That still needs diff-versus-declaration checking at publish time (§6.1).
- It will not make two agents mean the same thing by an identifier. It makes the registry possible, which is different from making it correct.
- It will not terminate a negotiation. It only records one.

### 7.3 Design points

- **Separate the coordination ledger from the work history.** Coordination events are high-churn and short-lived: leases, heartbeats, classifications, negotiation rounds. Work history is durable: decisions, claims, evidence, changes. Mixing them means the file every agent reads on entry is dominated by expired leases, which directly damages the context-budget goal in §5.2. Two streams, one fold each.
- **Define the fold normatively.** If coordination state is a projection, two implementations disagreeing about how to project it is a coordination failure, not a display inconsistency. For a coordination ledger this is tractable: the state machines are small and mostly last-event-wins per subject, with explicit conflict rules for the exclusive cases.
- **Specify compaction before it is needed.** A coordination ledger on an active project accumulates fast. Closed leases, completed intents, and resolved negotiations fold into a checkpoint once no open item references them. Say so now, or agents will start reading only the tail and quietly diverge.
- **Treat ledger text as untrusted.** Every agent reads it, and fields like `reason`, `explanation`, and `rollback` are free text written by other agents. The existing rule that imported content is data, not instruction, needs to apply explicitly to the coordination ledger — it is the one file every participant is required to consume.
- **Keep it out of the orientation path.** A re-entering agent should read a derived brief, not replay a ledger. The ledger is the coordination substrate; the brief is the product. Conflating them reintroduces the cost you are trying to avoid.

---

## 8. Testing and validation

### 8.1 Conformance is currently unfalsifiable

Every module ends with a paragraph of the form "A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements..." None of that can be mechanically checked.

The highest-value addition is a fixture corpus: for each MUST, a valid case and an invalid case, with expected diagnostics. This depends on §4.6's common diagnostic structure, which is why that item matters more than its size suggests.

Handoff §8's interoperability experiment is a good instinct but describes one hand-run trial, and it belongs in a separate test-plan document rather than a normative module.

### 8.2 The test that actually matters

Not conformance fixtures. The measurable claim is:

> An agent given only the capsule reaches a correct first action faster, and makes fewer wrong assumptions, than the same agent scraping the repository.

Run that head-to-head on several real re-entry situations from actual project history. If the capsule does not beat scraping on wrong-assumption rate, the format is not the problem — the freshness and maintenance story is (§5.2).

For coordination, the equivalent is: two agents working on genuinely interdependent code, with and without tier-1 contracts and preconditions, measured on integration failures caught before merge versus after.

---

## 9. Recommended sequence

1. Fix the blocking correctness issues (§3). Small, mechanical, and they will otherwise propagate.
2. Cut Synchronization; adopt git as the replication layer (§2.1).
3. Extract an orientation-only base spec (§2.2) and add revision-binding for freshness (§5.2). This alone delivers use cases 2 and 3.
4. Make the ledger authoritative for coordination and split it from work history (§7).
5. Ship coordination tier 1 — contracts, mechanical preconditions, integration-time verification (§6.13).
6. Run the head-to-head test (§8.2) before building tiers 2 and 3.

---

*Prepared as a review of the 0.5.0 bundle. Section references are to the bundled module documents as numbered in that file.*
