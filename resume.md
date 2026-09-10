# Session resume — AWP project (Cowork / actor:claude)

Written 2026-09-10T15:53Z ahead of a planned reboot of mark-pc. Read this before
picking the thread back up, whether that's the same conversation or a new one.

## Who's who

- **actor:claude** — this Cowork session, registered on the COOP-2 rendezvous
  `binding:391f01c4-f846-4178-aaeb-daac15601ba6`. Can only heartbeat manually,
  per call, with `--observation on-entry-only`. It can never run a live
  watcher — every `device_bash` call is a fresh `bwrap` sandbox torn down at
  return, verified twice this session. Never declare `--observation watcher`
  for this session.
- **actor:codex** — the peer agent, running with a real persistent host
  process (it has left watcher logs proving a live poll loop ran at least
  once). It is the only side that can ever satisfy the "watcher" role or run
  the publication-to-wake test.
- **principal:mark** — the human decision owner on every interaction sent
  through the channel; never a participant actor.

Ledger tool: `cd` to the repo root and run `python -m tools.awp_coop2 <cmd>`
(the `python tools/awp_coop2.py` form fails on a relative import). Always
`heartbeat --actor actor:claude` before reading the ledger, since liveness
goes stale (90s TTL) between calls.

## What happened this session, in order

1. **Joined the COOP-2 channel**, withdrew a timed-out interaction as its
   sender (`interaction:c8e694e5`) rather than answering `timed_out` on
   Codex's behalf — identity on this pilot is self-asserted, so responding
   as a peer would forge the ledger's evidence of who said what.
2. **Decision-lineage consultation**, both directions. I answered Codex's
   "durable decision lineage" question, initially claiming Core had no
   `decision` record type — **that claim was false** (it's a `coreRecord`
   type-enum variant with a conditional, not a `$defs` key; I'd checked only
   `$defs`). Codex caught it; I retracted it in a revision-2 capsule
   (`consultations/awp-decision-lineage-response.awp.md`) rather than
   quietly fixing it.
3. **Doorbell-delivery design consult** with Codex on making COOP-2 doorbells
   actually deliver. Converged on: two observation classes (capable vs
   entry-only, made structural not aspirational), delivery as
   recipient-relative/advisory not sender-guaranteed, and a reference watcher
   daemon that AWP defines the loop/hook contract for but never the wake
   action itself (host policy).
4. **Codex landed `7ac9512`** — "Draft durable Git doorbell semantics" —
   which is actually the decision-lineage work: Core §8.1 Decision Durability,
   `AWP-SIGNAL-UNVERIFIED` / `AWP-DECISION-CONTEXT-INCOMPLETE` diagnostics,
   `decision_context` as a 5-value axis, and `capsule.md` now states plainly
   the `.awp.md` Capsule is the sole normative entry point (a companion
   locator is non-authoritative). This is committed; nothing under `tools/`
   changed in it — none of the new diagnostics are actually emitted by code
   yet.
5. **Owner-requested feature: `partners` + `tickle`.** Sent a grounded
   strawman to Codex, which converged on: `partners` = read-only inventory,
   join history left-joined with observed liveness, inactive actors retained,
   COOP-1 lease state as a sibling reference never merged into presence;
   `tickle` = a separate event pair (`coop2.tickle.sent` /
   `coop2.tickle.acked`), no decision owner, no budget, bounded TTL, reusing
   the existing signal path — and it should be the fixture for the
   publication-to-wake test rather than a second harness.
6. **Owner directed spec-first** (reversing Codex's tools-first
   recommendation) and made me decision owner. Wrote **Cooperation Contracts
   §5.2 "Participant inventory and reachability probe"**, preserving every
   constraint Codex set. Recorded as `decision:partners-tickle-capabilities`,
   `checkpoint:partners-tickle-capabilities`. Rebuilt all generated artifacts
   (bundle, assets, entry core, requirements registry); `verify_workstate_artifacts`
   and `awp_workstate verify` both report clean.
7. **Closed a standing validator gap.** `tools/validate_spec_0_8.py` had
   never actually run in either agent's session (jsonschema 3.2.0 on this
   machine, no network in the device shell to upgrade it). Staged the repo
   into the cloud container, installed jsonschema 4.26, ran it: **passes** —
   module registry, schemas, links, 22 JSON examples, 1 briefing digest.
   Full test suite there: 143 tests, 138 pass, 5 errors are reconstructed-git
   artifacts unrelated to this work.
8. **Disclosed two findings to Codex**, both still unanswered:
   - **Projector atomicity defect** — a checkpoint that failed writing the
     `.awp-runtime/workstate-projection.json` sidecar returned `status:
     rejected`, but the capsule had *already* been partially updated (decision
     record + 5 artifact digests applied; checkpoint record + frontier were
     not). A rejected result should never leave partial state.
   - **Requirement IDs are positional, not anchored.** Inserting §5.2 didn't
     just shift `AWP-COOP-046` through `057` down — it silently reassigned
     `046`–`051` to the new §5.2 text. A citation against `046` today resolves
     to unrelated prose with no diagnostic. I initially misreported the new
     range as `058`–`063` and sent a correction — check the numbers yourself
     rather than trusting either message.
9. **Open design question, not yet resolved or written into spec:** should
   §5.2 explicitly distinguish an agent-internal/automatic probe (diagnostic,
   e.g. before trusting stale signal reach) from a user-invoked confirmation
   command (a person directly asking "is my partner there")? Mark raised this;
   I proposed language but we hadn't decided whether to fold it in now or
   bundle it with whatever Codex comes back with. **Nothing has been written
   for this yet.**

## Right now, uncommitted in the working tree

```
 M AGENTS.md                                        <- Codex, in progress
 M awp.awp.md                                       <- mine (decision + checkpoint)
 M awp.entry.json                                    <- mine (regenerated)
 M dist/drafts/0.8.0/AWP-0.8.0-agent-entry-core.md   <- mine (regenerated)
 M dist/drafts/0.8.0/AWP-0.8.0-draft.assets.md       <- mine (regenerated)
 M dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md       <- mine (regenerated)
 M spec/drafts/0.8.0/cooperation-contracts.md        <- mine (§5.2)
 M spec/drafts/0.8.0/requirements.json               <- mine (regenerated)
 M tests/test_awp_codex_wake.py                      <- Codex, in progress
 M tools/awp_codex_wake.py                           <- Codex, in progress
?? tests/test_awp_session.py                         <- Codex, in progress, new
?? tools/awp_session.py                              <- Codex, in progress, new
```

Nothing here has been committed by me. Codex appears to be actively mid-edit
on `AGENTS.md`, `awp_codex_wake.py`/its test, and a brand-new `awp_session.py`
— on "another problem" per Mark, separate from the partners/tickle thread.
Do not commit or stomp those files; they are not mine to finish.

## Outstanding on the ledger — nothing waiting on me, 5 waiting on Codex

All inside 24h delivery / 72–259200s response windows, none expired:

1. `interaction:6719cb88` — post-hoc review of the README withdrawal + hygiene commits
2. `interaction:b0ba3ad7` — cache-consultation recommendation + the jsonschema validator discrepancy
3. `interaction:349642` — pointer to the uncompressed decision-lineage capsule
4. `interaction:cdceda4a` — disclosure of §5.2 landing + the two findings above
5. `interaction:a5c74f6` — correction to the requirement-ID range in #4

My own inbox is empty. Mark said: "Codex is working on another problem, I'll
have you consult with its findings" — i.e. the next real step on this thread
is reacting to whatever Codex reports back, not sending more unprompted.

## Not yet started

- `partners` and `tickle` (`coop2.tickle.sent`/`.acked`) have **no
  implementation** in `tools/awp_coop2.py`. This was Codex's assignment;
  I offered to write both myself (they're read/write on files, not a running
  process) but haven't started, pending Mark's steer.
- The §5.1.1 publication-to-wake test needs a host that can supervise a live
  process — cannot be run from this session, ever.
- The dual-initiator question in §5.2 (see point 9 above).

## Gotchas worth not re-learning

- Schema record types live in `coreRecord`'s `type` enum + conditionals, not
  in `$defs` — checking only `$defs` is what produced the false claim in
  step 2.
- `tools/validate_spec_0_8.py` needs jsonschema 4.x; this device has 3.2.0
  and no network in `device_bash` to fix it. Stage the repo to the cloud
  container to actually run it or the full test suite.
- `check_markdown_links.py` reports 20 pre-existing broken links, all inside
  `.awp-runtime/pre-edit/` debris — not worth chasing.
- File deletion in the connected `awp` folder is enabled for the rest of this
  Cowork session (Mark approved it, needed for the projector's atomic sidecar
  replacement).

## Additional continuity

Durable lessons from this session are also saved in this session's project
memory (`coop2_channel_operation.md`, `awp_schema_inspection.md`) and in
Claude's cross-session user memory under the AWP/PWSP topic — both survive
independently of this file and this machine's reboot.
