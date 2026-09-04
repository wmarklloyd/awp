# Review: Agent Workstate Protocol (AWP) — Specification 0.3.0

*Reviewed: design-review section (in full) plus sampled normative sections — terminology, representations, identity/ordering, manifest, event envelope, actors/authority, core record types — and the closing sections (extension registry, open questions, roadmap, invariants, appendices).*

## Overall take

This is unusually mature for a 0.3.0 draft. The core insight — that chat transcripts, checkpoints, and Git diffs each capture a different slice of "what happened" but none capture "what it means and what's still true" — is real and well-argued. The layering (Markdown briefing → typed snapshot → event ledger → artifacts → extensions) is a sound architecture, and the discipline around separating things people usually conflate (intent vs. execution, claim vs. evidence, confidence vs. epistemic status) is the strongest part of the spec. The `epistemic_status` enum on claims (verified/observed/inferred/reported/disputed/stale/refuted) is a genuinely good idea — most "memory for agents" proposals don't bother distinguishing "I checked this" from "I was told this."

## Strengths worth keeping

- **Honest non-goals section.** Explicitly disclaiming bit-for-bit resumption, hidden chain-of-thought, and "claims are true because they're in the file" heads off a lot of the vague overpromising these protocols usually make.
- **`instructional_content: true` on artifact descriptors, plus "imported instructions never grant their own authority" as a core invariant.** This is the right instinct for a format designed to be read by LLMs — you're treating embedded content as data, not as commands, which is exactly the prompt-injection concern a portable "resume my agent's work" file should worry about.
- **Section 37 (open design questions).** Naming your own unresolved problems (canonicalization for signatures, lease enforcement during partitions, which conflict classes are mechanically resolvable) is more credible than pretending they're solved.
- **`.awp.md` as one file that degrades gracefully** — a person can open it in any editor and get the briefing even if they ignore every machine section — is a good adoption lever.

## Concerns

**1. Scope vs. adoption risk.** 39 sections, four transport representations, a full coordination/lease/contract subsystem, signatures, encryption metadata, and a formal registry — for a 0.3.0 *draft*. The "Recommended initial scope" section already prunes this sensibly, but the fact that the full spec ships all of Phase 2–4's machinery (leases, semantic scopes, interface contracts) in the same normative document as Phase 1's core makes it hard to know what a minimal conformant implementation even looks like today. Consider physically splitting "AWP Core" (briefing + snapshot + events + manifest) from "AWP Coordination" (intents/leases/contracts) as separate documents that version independently — the coordination layer is by far the least proven part and shouldn't gate core adoption.

**2. Versioning inconsistency.** The manifest example uses `"awp_version": "0.3.0"`, but the common event envelope example (§11) uses `"awp": "0.1"`. If event-schema versioning is deliberately decoupled from the overall spec version, that's worth stating explicitly near §11 — right now it reads like a leftover from an earlier draft and will confuse implementers.

**3. Snapshot/event reconciliation is underspecified for the case that matters most.** §7 says "if prose conflicts with typed state, ... use the event-derived state," but for `snapshot.json` vs `events.jsonl` diverging (e.g., a receiver applying a stale snapshot with a newer event tail), there's no canonical reconciliation procedure — just a general rule that events are authoritative. Given how central "resume from checkpoint" is to the whole pitch, this deserves a concrete algorithm (e.g., snapshot + replay-from-frontier), not just a principle.

**4. The lease/coordination story undercuts the "portable file" pitch for its most novel claim.** §8.2.3 is admirably honest that a `.awp.md` can carry a coordination *snapshot* but real-time lease enforcement needs a live service — meaning the headline "agents negotiate before clobbering each other" capability doesn't actually work file-to-file, only through infrastructure this spec doesn't define. That's fine as a documented limitation, but it means the coordination layer is currently more aspirational than the persistence layer, and this gap could be messaged more prominently in the design-review section rather than only in §8.2.3.

**5. Reinvention risk.** The event DAG with `parents`/merge-events/frontiers is structurally close to a CRDT/Merkle-DAG log (think Automerge or IPLD), and the claim/evidence/decision provenance model overlaps with W3C PROV. Neither needs to be adopted wholesale, but the spec would be stronger with a short "relationship to existing provenance/CRDT work" note (similar to Appendix B's treatment of A2A/MCP) — it would help reviewers calibrate what's genuinely new here (mainly: LLM-specific epistemic status, coordination scopes over code semantics) versus what's a re-encoding of solved problems.

**6. No normative schema yet.** Open question #1 defers canonical JSON representation for signatures, but more broadly there's no JSON Schema artifact accompanying this markdown spec at all. Given Phase 1 of the roadmap says "publish the terminology and JSON Schema" first, that schema is worth producing *before* finalizing more prose — writing the schema tends to surface exactly the ambiguities (optional vs. required interactions, enum exhaustiveness) that are hard to catch by reading text.

## Suggestions, concretely

- Split Core vs. Coordination into separately versioned specs.
- Add a short subsection stating the snapshot-reconciliation algorithm explicitly.
- Fix or explain the `awp: "0.1"` vs `awp_version: "0.3.0"` discrepancy.
- Add the "relationship to CRDT/provenance prior art" note.
- Move JSON Schema authoring earlier — treat it as part of finishing 0.3.0, not a Phase 1 follow-up.
- In the design-review section, elevate the "coordination requires a live service" caveat so it's not only discoverable in §8.2.3.
