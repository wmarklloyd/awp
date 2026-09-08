# AWP 0.8.0 Working Draft — Review

> **Archival note.** This review was produced by Claude (Opus) on 2026-09-08 against the
> repository at `375ec40` plus uncommitted work. It is an informative research input, not
> normative text or independent validation, and its measurements were taken at that revision.
> Its recommendations were implemented across `8e0c815`..`91a6cc9`; where a measured outcome
> differed from the estimate here, the commit message records the measured figure. Two items
> remain open as `task:capsule-artifact-manifest` and `task:coordination-contract-dedupe`.

**Scope:** token footprint of the specification, cost of maintaining `awp.awp.md`, and robustness of inter-agent communication.
**Basis:** repository at `375ec40` plus the nine uncommitted working-tree files present on 2026-09-08 15:40Z. All byte counts are measured; token figures are bytes ÷ 4 and should be read as ±15%.
**Author:** actor:claude, from one full day of live COOP-2 operation with actor:codex on this repository. Every failure mode in §3 was observed, not hypothesised.

---

## Summary

**Token footprint.** The draft is 267 KB of source modules (~67K tokens), but the prescribed entry path for coordination work reads ~67K tokens before any work starts, and the "read the complete bundle" fallback is 510 KB (~128K tokens) because the bundle embeds nine JSON schemas. The prose is 62% normative statements by sentence, so there is little filler to cut; savings have to come from *structure* — routing agents to the requirements registry instead of the prose, splitting `coordination.md`, and not shipping schemas inline. Realistic target for the coordination route: **~67K → ~20K tokens** with no loss of normative content.

**Capsule maintenance.** `awp.awp.md` is 92 KB (~23K tokens). Half of it is 106 artifact digest records, 44 of which nothing references. Because the capsule is effectively a digest manifest for 106 files, *any* edit to a tracked file stales it, and the checkpoint tool requires the agent to pre-supply the capsule's expected digest — an optimistic lock on the whole document. The result is visible in `.awp-runtime/`: 21 checkpoint request files for 12 logical checkpoints, six attempts for one of them. The tool itself runs in under a second; the cost is agent round-trips. Moving artifact digests out of the capsule and letting the tool compute its own preconditions should take a checkpoint from 2–6 attempts to one and halve the capsule.

**Inter-agent communication.** The durable parts work and were verified repeatedly: Claude→Codex signal delivery in 0.1–2 s across five sends including a Codex session restart, a fail-closed entry-recovery path, and a COOP-1 collision check that stopped duplicate work. What does not work is everything the protocol *describes but nothing observes*: watcher liveness is "not verified", response windows expire on paper only (one interaction sat open 12.2 hours against a 1-hour window), delivery receipts arrive hours after the work they acknowledge, and a one-word response ("This") closed an interaction as answered. The fix is not more mechanism; it is making the four states the spec already names — delivered, observed, alive, expired — *derived from evidence* rather than asserted.

---

## 1. Specification token footprint

### 1.1 Measured

**Source modules (`spec/drafts/0.8.0/`)**

| Module | Bytes | ~Tokens | Share |
|---|---:|---:|---:|
| coordination.md | 98,785 | 24,700 | 37% |
| cooperation-contracts.md | 43,192 | 10,800 | 16% |
| silos.md | 26,683 | 6,670 | 10% |
| core.md | 16,433 | 4,110 | 6% |
| index.md | 15,510 | 3,880 | 6% |
| handoff.md | 13,785 | 3,450 | 5% |
| capsule.md | 13,386 | 3,350 | 5% |
| security.md | 11,234 | 2,810 | 4% |
| synchronization.md | 9,199 | 2,300 | 3% |
| adapters.md | 7,721 | 1,930 | 3% |
| artifact.md | 6,004 | 1,500 | 2% |
| open-issues.md | 4,887 | 1,220 | 2% |
| requirements.md | 741 | 185 | — |
| **Total** | **267,560** | **~66,900** | |

**Generated / companion artifacts**

| Artifact | Bytes | ~Tokens | Note |
|---|---:|---:|---|
| `AWP-0.8.0-draft.bundle.md` | 510,009 | 127,500 | modules + 9 embedded schemas |
| `requirements.json` | 170,693 | 42,700 | 321 statements, verbatim copies of prose |
| `schemas/*.json` (24 files) | 206,898 | 51,700 | |
| `AWP-0.8.0-agent-entry-core.md` | 6,929 | 1,730 | the only small thing |

**What an agent actually reads per route** (`awp_spec_entry.py --route`)

| Route | Docs | Schemas | Read set | ~Tokens |
|---|---:|---:|---:|---:|
| general | 2 | 0 | 31,943 | 8,000 |
| security | 4 | 2 | 65,203 | 16,300 |
| workstate | 5 | 3 | 81,089 | 20,300 |
| coordination | 7 | 3 | 266,425 | **66,600** |
| silos | 10 | 6 | 323,760 | **80,900** |

Add the capsule re-entry output (~17K) and AGENTS.md (~3K): a coordination task costs **~87K tokens of orientation** before the first edit. Every COOP-2 interaction today was coordination-route work.

**Normative density.** 605 `MUST` + 186 `MUST NOT` + 56 `SHOULD` + 87 `MAY` across roughly 1,276 sentences. About 62% of sentences carry a normative keyword. This matters for strategy: there is not much explanatory prose to trim. The requirements *are* the text.

### 1.2 Where the tokens go

1. **`coordination.md` is 37% of everything**, and its largest sections are not COOP-1 material: §18.2 Scaling requirements (1.9K tokens, COOP-3), §18.1 Presence and monitoring (1.5K), §10 Negotiation (1.8K), §12 Typed preconditions (1.3K), §24 Conformance fixtures (0.8K). A COOP-1 lease-and-intent task pulls all of it.

2. **The registry duplicates the prose verbatim.** `requirements.json` holds 321 entries of `{id, source, line, statement}` at ~495 bytes each. The `statement` is the sentence from the module. So every normative sentence exists twice, and the registry is larger than most modules.

3. **The bundle embeds schemas.** 268 KB of modules becomes 510 KB. AGENTS.md step 2 tells agents to read the complete bundle on any full-source trigger. That is a 128K-token read.

4. **Routes pull full schemas for orientation.** The coordination route ships three schema files (~50 KB) that an agent needs only when *authoring* a record, not when orienting.

5. **Contract text is owned twice.** `coordination.md` §3 (3K tokens) and `cooperation-contracts.md` both describe COOP-level integration. The boundary consultation earlier this week found term collisions (staleness, precondition, verification) between them for exactly this reason.

6. **Disclosure boilerplate repeats.** "MUST disclose" ×18, "unavailable" ×62, "snapshot-only" ×10, "AWP-COORD-LEDGER-UNAVAILABLE" ×5, "experimental" ×14. The same unavailable/snapshot-only/disclose semantics are restated per module rather than defined once and referenced.

### 1.3 Recommendations

**S1 — Route to the registry, not the prose.** Make `requirements.json` the *routed read unit*: `--route coordination` returns the registry entries for the in-scope modules (id + statement only; move `source`/`line` to a side index). The prose modules become rationale and examples, read on demand when a statement is ambiguous. The coordination route's seven documents (~55K tokens of prose) collapse to the **249 registry statements** that govern them — measured at ~25K tokens of statement text. That is a 55% cut on its own, and after S2 splits COOP-3 material out of `coordination.md` the COOP-1 statement set should be closer to 150 entries (~15K). This is the single largest lever and it requires no normative change: the registry is already declared `normative_authority`.

**S2 — Split `coordination.md` by contract tier.** Move §18.2 (scaling) and the COOP-3 portions of §18.1 to a `coordination-scale.md`; move §24 fixtures to `conformance/`; move §10 negotiation and §12 typed preconditions behind a `coordination-advanced` route. `coordination.md` proper drops from ~25K to ~12K tokens and the COOP-1 route stops paying for COOP-3.

**S3 — Reference schemas by digest; stop embedding them.** The bundle drops from 128K to ~67K tokens. For routes, ship a generated *schema digest* per schema (type name, required fields, enums, `$defs` names — roughly 5% of the JSON) for orientation; load the full schema only in the tool that validates a record.

**S4 — Single owner for contract-level text.** Delete `coordination.md` §3's duplicate of the COOP integration model and replace it with a pointer to `cooperation-contracts.md`. Resolves the term collisions at the same time.

**S5 — Define disclosure semantics once.** One section (core or index) defines `unavailable`, `snapshot-only`, `degraded`, the disclosure obligation, and the `AWP-COORD-*` diagnostic family. Modules say "disclose per Core §N" instead of restating the paragraph. Modest saving (~2–3K tokens) but removes a class of drift.

**S6 — Fix the 0.6.0 / 0.8.0 authority conflict.** `.awp.json` and the capsule still name the v0.6.0 bundle as the governing specification while AGENTS.md calls 0.8.0 "the sole source of operative requirements". An agent that follows step 3 literally reads the wrong spec. This is not a token issue but it has been open all week and it determines which spec an agent loads.

Estimated effect on the coordination route: S1 alone **~67K → ~38K** (25K statements + 13K schemas); S1 + S3 **→ ~26K**; S1 + S2 + S3 **→ ~15–20K**. The general route is already at 8K.

---

## 2. Capsule maintenance (`awp.awp.md`)

### 2.1 Measured

| | Value |
|---|---:|
| Capsule size | 91,589 B (~22,900 tokens) |
| Generated briefing region | 853 B |
| Manifest | 1,174 B |
| Snapshot | 86,259 B |
| Indexed records | 203 |
| Records selected on entry | **9** |

**Snapshot by record type**

| Type | Records | Bytes | Share |
|---|---:|---:|---:|
| artifacts | 106 | 43,681 | **51%** |
| changes | 26 | 12,448 | 15% |
| decisions | 20 (5 superseded) | 8,235 | 10% |
| evidence | 12 | 6,606 | 8% |
| claims | 10 | 4,420 | 5% |
| risks | 8 | 3,843 | 4% |
| tasks | 20 | 3,362 | 4% |
| checkpoints | 3 | 1,912 | 2% |
| other | 4 | 1,066 | 1% |

- **44 of 105 artifact records are referenced by no other record.** They are tracked digests and nothing else.
- Each artifact record is ~412 bytes for what is functionally `{id, path, sha256}` (~120 bytes), because of `modules → urn:awp:artifact → status/locations/integrity` nesting.
- **Retry churn:** 21 checkpoint request files in `.awp-runtime/` for 12 logical checkpoints. `checkpoint:coop2-entry-recovery` took six attempts; two others took three.
- Tool runtime is not the cost: full re-entry validation 0.78 s, entry-core verify 0.04 s.

### 2.2 Why it is expensive

The capsule is doing two jobs with one document and one digest:

1. **It is a semantic workstate** — goals, decisions, claims, evidence, next action. This changes when the project's *meaning* changes. Small, slow-moving, high value.
2. **It is a digest manifest for 106 files.** This changes whenever *any* tracked file changes, including files unrelated to the current work. Large, fast-moving, mechanical.

Because they share one document, every mechanical change looks like a semantic change and demands a semantic checkpoint. Then the checkpoint workflow compounds it:

- `awp_workstate.py checkpoint --request <json>` requires the agent to supply `expected_capsule_digest` and `expected_generated_digest`. That is an optimistic lock on the entire capsule. The agent must read the whole capsule, compute digests, write the request, and run — and if anything moved in between, it fails and the loop restarts. That is what six request files for one checkpoint looks like.
- Each request also carries a hand-written `briefing`. The 450-byte briefing is rewritten per attempt.
- Required-artifact verification (`verification_state: modified`) and capsule-digest verification are two *independent* staleness sources. This week both fired separately on the same edit.

None of this is wasted design — the digests exist so that a capsule cannot silently lie about the files it depends on. The problem is that the guarantee is applied at the wrong granularity.

### 2.3 Recommendations

**C1 — Split the artifact manifest out of the capsule.** Generate `awp.artifacts.json` (`{id, path, sha256, status}` per entry, flat) by tool, and have the capsule reference it by one digest. Capsule shrinks by ~50% (→ ~11K tokens). Editing a tracked file regenerates the manifest — a mechanical, tool-only step — without a semantic checkpoint. The capsule's own digest changes only when its meaning changes.

**C2 — Track only what is load-bearing.** Keep artifacts that are `required_artifacts`, in a `read_first` list, or referenced by evidence/decision/claim records. That is 61 of 105 today. Drop the 44 orphans.

**C3 — Let `checkpoint` compute its own preconditions.** Add `--from-current`: the tool reads the current capsule, uses its digest as the expected value, and proceeds. Keep the explicit `--request` form for the rare case where the caller genuinely needs to guard against a concurrent change. This alone removes most of the retry loop.

**C4 — Derive the briefing.** Default the briefing from the checkpoint's decision/summary text; allow override. Stop requiring fresh prose per attempt.

**C5 — Archive superseded records.** Five superseded decisions and completed changes still live in the entry-loaded snapshot. Move them to an `archive` section that the selective re-entry never loads. The full history stays in the capsule; the entry read gets smaller.

**C6 — Emit an entry slice.** Selective re-entry already proves 9 of 203 records are what a session needs. Have the projector write `awp.entry.json` alongside the capsule: briefing, active checkpoint, resume, read_first, required artifacts. The host validates the full capsule (fast, 0.78 s); the model reads the ~4K-token slice. AGENTS.md step 4 already describes this behaviour — make it a file rather than a runtime computation.

**C7 — One staleness check.** Fold the required-artifact digest check into the manifest check from C1 so there is one thing that can be stale, reported once.

Estimated effect: capsule **~23K → ~10K tokens**; checkpoint attempts **2–6 → 1**; model-facing entry read **~17K → ~4K**.

---

## 3. Inter-agent communication robustness

### 3.1 What is verified working

Everything here was observed on this repository this week, with ledger evidence.

- **Signal delivery, Claude → Codex:** five sends, all recorded by the watcher; the four that were timed were picked up in 2.0 s, 0.7 s, 0.4 s, and 0.1 s — including one after Codex was restarted without session resume. The durable registration, the doorbell file, and `codex-local-queue-watcher-v1` all survived the restart.
- **Entry-recovery path:** after `375ec40`, coordination payload is 475 bytes, `read_verified: true`, and `unavailable`/`skipped` fail closed with exit code 2. Verified against a forced failure.
- **COOP-1 collision detection:** publishing an intent for doorbell work returned `advisory_status: block` against Codex's active `intent:f63f9594` on the same scope. It prevented a duplicate implementation. This is the protocol doing its job.
- **Cross-agent review loop:** four defects reported through COOP-2 were fixed by the other agent and re-verified — read-implies-accept conflation, watcher subprocess hang, silent coordination drop under budget, dual-import exception identity.

### 3.2 Failure modes observed

Each entry is: what happened → evidence → why it matters.

**F1 — One-directional signalling reported as `reach: shared`.** Claude→Codex works; Codex→Claude has no channel (no process on Claude's host watches the local file; Claude's only persistent watcher polls GitHub, where nothing is pushed). The binding reports `reach: shared` because both actors registered in one ledger. That is true of the *mailbox* and false of the *signal*. Hours were spent discovering this manually. → Signal reach must be per ordered pair. `afaebc1` added `participant_watchers` to the schema; `tools/awp_coop2.py` does not yet populate it.

**F2 — Watcher liveness is asserted, never observed.** The binding literally reports `watcher_liveness: "not verified by this binding"`. A dead watcher and a live one look identical. → Heartbeat: watchers write `{actor, last_seen, cursor}` into the ledger on every poll; the binding derives `active | stale | none` per actor from it. This converts a disclaimer into a measurement.

**F3 — Delivery, acknowledgement, and work are decoupled.** After a fresh Codex session picked up a message at 03:42:37.110, it edited files for 45 minutes with the interaction still `requested` in the ledger, and *fixed the reported bug before ever publishing an `observed` receipt*. From the protocol's point of view nothing was happening. → The watcher should publish `observed` at the moment it queues the notification (it already has the event id and frontier). The session should publish `accepted` on pickup, before starting work, not after finishing.

**F4 — Response windows are declarative.** `interaction:a38af63c…` declared `response_window_seconds: 3600` and remained `requested` for 12.2 hours. The lifecycle defines `delivered_unanswered → timed_out`; nothing applies it. → Derive expiry on read: `inbox` and the entry check compute `timed_out` from `occurred_at + window` and report it. No daemon required — this is a pure function of the ledger and the clock authority the policy already names.

**F5 — Response content is unvalidated.** The liveness check was answered with the single word "This" and closed as `responded`/`accepted`. → Minimum response requirements: non-empty, and for `outcome ∈ {accepted, revised}` at least one of `{evidence, change_ref, decision_ref, text ≥ N chars}`. The policy already has `progress_requirement: new_artifact_evidence_decision_or_disagreement`; enforce it at `respond`.

**F6 — Stale intents hold scope from absent participants.** `intent:f63f9594` is `active` on base `8822a40` (seven commits stale) with no live lease behind it, and it blocked both my intent and — later — Codex's own next intent (seven overlaps at 01:13:52 against its own stale scope). → Intents inherit their lease's TTL; `refresh` reports base-revision drift and downgrades an intent whose base is behind `HEAD` by more than N commits to `stale`, which does not block.

**F7 — Unbounded watcher cursor.** `coop2-codex-watcher.json` keeps every notified event id forever (`[*state["notified_events"], event_id]`), read and rewritten every poll. → Bound it to events newer than the last frontier the watcher has fully processed.

**F8 — Git-backed anything inherits git's locks.** Every git write in this repository left an unremovable `index.lock` behind under the device shell's delete restriction, and each stale lock jammed the next operation. A doorbell built on `git update-ref` will fail the same way. → Any git-backed signal must tolerate and recover from stale lock files explicitly.

**F9 — No cross-host channel, and the escalation stalled.** The proposed `refs/awp/coop2-signal/<event>` push was escalated on egress grounds ("each push exports repository objects") and has been waiting on an in-session authorization since 21:07 yesterday. → Two-step: (a) **local** `refs/awp/signal/<event_id>` via `update-ref` needs no authorization and gives every AWP project a transport with zero setup, because every AWP project is a git repository; (b) for cross-host, point the ref at a commit **already on origin** so the push transmits only the ref name and exports no new objects — which removes the stated objection.

**F10 — Closing an interaction requires the recipient's identity, and there is no authentication.** Codex asked that "Claude's open review interaction" be closed from "your normal shell". The only close path is `observe → accept → respond --actor actor:codex`. Doing that from Claude's shell would forge the receipts the lifecycle exists to make trustworthy. (Codex closed it itself minutes later.) → Add a sender-side `withdraw`. Keep close recipient-only. Note in the profile that receipts are unauthenticated so readers weight them accordingly.

**F11 — Two ledgers.** COOP-1 coordination lives in `.git/awp/coordination.sqlite3`; COOP-2 rendezvous in `.awp-runtime/coop2-rendezvous.sqlite3`. Two things to discover, keep alive, and back up; the entry check reads one of them. → Either unify, or have each binding descriptor name the other so discovery of one yields both.

### 3.3 Recommendations, prioritised

**P0 — Make the state honest (no new transport needed).**
- Heartbeat per watcher (F2), and derive per-actor liveness from it.
- Per-direction reach matrix populated from registered observation capability (F1).
- `observed` published by the watcher on queue; `accepted` by the session on pickup (F3).
- Expiry derived on read (F4).
These four turn every "not verified" and "pending" in today's output into a measured value. They are all tooling changes inside `tools/awp_coop2.py` and `tools/awp_codex_wake.py` plus one paragraph in `cooperation-contracts.md` §5.

**P1 — Make the doorbell implicit.**
- Local git-ref doorbell `refs/awp/signal/<event_id>`, emitted alongside the filesystem doorbell (F9a), with stale-lock recovery (F8).
- Bounded cursor (F7).
- Entry-time doorbell establishment: `awp_reentry.py --actor` registers the actor's observation capability and starts or verifies its watcher, so entering a project *is* arming the doorbell.

**P2 — Tighten the lifecycle.**
- Sender-side `withdraw` (F10); response validation (F5); intent staleness (F6); ledger cross-reference (F11).
- Cross-host push using already-published commit objects (F9b), once P0 makes the resulting `codex→claude: reachable` claim verifiable rather than asserted.

### 3.4 A note on "should not fail"

The stated goal is a doorbell that does not fail. No transport can promise that; processes die, locks stick, sessions stall — all three happened this week. What the protocol can promise, and mostly already does, is that a doorbell failure **cannot lose an interaction** (entry recovery) and **cannot be silent** (P0). The second half is the open work. Once liveness, reach, and expiry are derived from evidence, a dead watcher shows up as `stale` within one heartbeat interval instead of as a mystery twelve hours later — and that is what robust means here.

---

## Suggested order of work

1. **C3 + C4** (tool computes checkpoint preconditions; derived briefing) — small, immediate relief from retry churn.
2. **P0** — four tooling changes that make the coordination state truthful.
3. **S1** — route to the registry; largest token saving, no normative change.
4. **C1 + C2** — split the artifact manifest, prune orphans.
5. **P1** — local git-ref doorbell + entry-time establishment.
6. **S2 + S3** — split `coordination.md`, stop embedding schemas.
7. **S6** — resolve the 0.6.0/0.8.0 authority conflict (one-line change, long overdue).
8. **P2**, **S4**, **S5**, **C5–C7** as follow-ups.
