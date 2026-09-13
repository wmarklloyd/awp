# AWP Open Issues 0.8.0

**Status:** Informative issue register  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

These questions are intentionally unresolved. A module must not imply that an open issue has a portable solution unless it declares a separate experimental capability or binding.

## Core and handoff blockers

1. Which update representation—typed operations, complete replacement, JSON Patch, or another form—best preserves revision preconditions and unknown module data?
2. Which minimum Core record set produces reliable continuation across unrelated models?
3. What benchmark adequately measures factual fidelity, constraint preservation, authority compliance, token efficiency, and result quality?
4. Which identifier profiles should be recommended for workstates, actors, events, and records?
5. How should delegated authority map to established identity and authorization systems without making AWP an identity provider?

## Capsule and artifact questions

6. Should generated Markdown regions use a canonical Markdown subset in addition to normalized-byte hashing?
7. Under what concrete use case, authority model, and lifecycle rules should the archived package and wire-representation directions be reconsidered?
8. Which artifact retrieval profiles can express expiring access without placing credentials in workstate data?
9. Which media types require mandatory sandboxing or sanitization profiles?

## Synchronization questions

10. How can histories be compacted while proving lineage, preserving unknown-module effects, and retaining adequate audit evidence?
11. Which semantic conflict classes can be resolved mechanically?
12. Should a future convergence profile adopt an existing CRDT or Merkle-DAG representation?
13. What canonical state representation is suitable for replay equivalence proofs?

## Coordination questions

14. Which Python, TypeScript, and later language selector profiles best preserve semantic identity across rename, move, extraction, and replacement?
15. What semantic-integration profile should establish COOP-2 interoperability, and what formally verified COOP-3 coordinator algorithm and enforcing adapter should follow it?
16. Which semantic effects can tools infer reliably, how should confidence be calibrated, and which effects must remain actor assertions?
17. Which verification procedures provide adequate evidence for particular contract and invariant classes?
18. Which Git, worktree, CI, and forge mappings should become standard adapter profiles?
19. What policy-composition rules resolve multiple organization-specific contract decision policies without silently weakening a required party, including when user arbitration is required?
20. What measured false-positive rate makes semantic overlap useful rather than disruptive?

## Security and governance questions

21. Which canonicalization and signature profiles should be registered first, and can RFC 8785 be adopted with acceptable I-JSON and number constraints?
22. Should encryption be standardized at package, module, artifact, or recipient-envelope level?
23. How should retention, legal deletion, classification, and jurisdiction metadata interoperate across organizations?
24. What privacy-preserving evidence can demonstrate secret scanning or coordination compliance without exposing sensitive findings?

## Adapter questions

25. How closely should A2A, MCP, and MPAC bindings track upstream protocol release cycles?
26. Which round-trip losses are acceptable for workflow and model-runtime adapters?
27. How should bindings negotiate module versions when their transport has a different capability model?

## Resume and discovery questions

28. Which agent runtimes will recognize the conventional `.awp.md` filename directly, and which will require an agent-specific instruction shim or launcher integration?
29. What context-selection benchmark demonstrates that Resume Profile loading reduces tokens and startup time without omitting safety-critical state?

## Silo implementation and evidence questions

30. Which first `silo-v1` binding will demonstrate pinned derivation, explicit base updates, dependency-complete adoption, scoped approval, and crash recovery across separate workstates? The normative profile is in [silos.md](silos.md); the current schema fixtures establish structure only.
31. What common physical-resource binding can atomically coordinate several semantic workstates, including aliases and shared external resources, without merging their independent event histories?
32. Which dependency walkers and provenance mappings can safely preserve required references across the first supported module set? Unknown required dependency semantics must block adoption; automatic reconciliation, multiple inheritance, and cross-project adoption remain deferred.

## Startup doorbell questions

33. Which second agent host will demonstrate that the startup doorbell of Cooperation Contracts section 9 is host neutral in practice, and how should a host that fires its startup hook only on the first input meet the no-manual-step acceptance rule?
34. What wake binding, if any, should a cloud-hosted agent session without a local endpoint expose so that it can be woken rather than reached only through entry recovery?

## Requirement identifier questions

35. How should requirement identifiers be anchored in the source text before 0.8 is released? Identifiers are currently positional per source file, so normative text inserted mid-file silently reassigns existing identifiers to unrelated statements (observed with section 5.2 on 2026-09-10); until they are anchored, new normative text is appended at the end of its source file.

## Git ledger questions

36. Which mechanism should authenticate the actor behind a `git-ledger-v1` ref (for example signed commits, forge-side push rules, or per-actor deploy keys), so that ref ownership becomes verifiable rather than self-asserted?
37. What remote-sync trigger should replace polling of advertised heads where a forge offers webhooks or push notifications, and what latency bound should a remote profile declare?

## Any-agent wake questions

38. Does a Claude routine with an API trigger, bound to the principal's computer, give hosted Claude sessions a dependable `W3` wake (latency, daily caps, research-preview stability), and what is the equivalent for other hosted agents?
39. Where should the relay run for teams whose participants include sleeping laptops and hosted agents, and how should several relays divide bindings without double waking?


## Notification architecture review questions (2026-09-11)

40. How can a relay address the open conversation of an agent desktop app whose sessions expose no thread identifier (for example the Codex app), so that its `W1` reaches the session the principal is watching instead of a new `W2` run?
41. What signal transport lets a hosted agent's subscription be woken without polling a Git remote, given sandboxes that block third-party push services, and should that transport be standardized as a binding profile?
42. How should a hosted agent re-arm its subscription automatically after its vendor recycles the workspace, rather than on its next entry?

## Action boundary questions (2026-09-13, revised twice: after a critical review, then after finding the module duplicated Security's guardrail mechanism)

0.2.0 collapsed action_intent and applicable_decision_set into one action-resolution record, per a critical review (research/model-assisted-reviews/deepseek-action-boundary-critique.md). 0.3.0 then found that 0.2.0's policy record, operation vocabulary, and policy-author role substantially duplicated Security 0.5's existing guardrail (security.md §4: `operation_classes`, `resources`, `policy_owner`, `enforcement`, `propagation`) and removed the duplication -- see action-boundary.md §1. A first-pass reference resolver, schema, conformance fixtures, and tests now exist (tools/awp_action_boundary.py, schemas/awp-action-boundary-0.3.schema.json, tests/test_awp_action_boundary.py, conformance/valid/action-boundary-0.3-*.json) and reproduce the original incident as a passing "deny" test. Questions below are revised to match; several are now substantially answered and are marked as such rather than removed, so the answer stays attached to the question it resolves.

43. Resolved by the 0.3.0 reframe: no new policy-record format is needed. A protected action class is declared as an ordinary Security guardrail (security.md §4); this module adds no declaration format of its own. Remaining question: should `generative:freeform` / `generative:composite` (action-boundary.md §3) be promoted into Security's own `operation_classes` vocabulary documentation, so a guardrail author discovers them without reading this module first?
44. Substantially answered by the first-pass resolver's `fnmatch`-based selector matching (tools/awp_action_boundary.py `_matches_selector`), tested in test_awp_action_boundary.py against a target that postdates the guardrail. Remaining question: what happens when two guardrails' selectors overlap with conflicting effects (for example one `deny`, one `require_review`) for the same action -- the first-pass resolver takes the most restrictive (deny wins), matching security.md §4's stated precedence, but this has not been reviewed against a real conflicting-selector case.
45. Still open. Under what concrete distributed or asynchronous enforcement scenario does AWP need a standalone, transportable action permit separate from an action resolution, and what should its lifecycle be? Deferred in 0.3.0 pending a real cross-host case (action-boundary.md §4) — AWP's own multi-host Cooperation Contracts layer is the most likely source of one.
46. Partially answered: tools/awp_action_boundary.py's `resolve` CLI is callable as a CI-gate check today (exit 0 permit, 1 deny, 2 unresolved) and is capsule-agnostic by design -- it takes plain guardrail/decision/entry-status JSON rather than parsing `awp.awp.md` directly. Still open: wiring it to actually read a project's live guardrails and decisions out of a capsule (rather than hand-built fixture files), and standing up a real CI workflow that calls it against this repository's own guarded-mutation path.
47. Answered for two of the three original record types: schemas/awp-action-boundary-0.3.schema.json covers action-resolution and artifact-claim. The third type (the project policy record) no longer exists as a separate thing to schema -- see #43.
48. Still open. Now that action resolution uses guardrail operation classes verified by an enforcement adapter or tool gateway rather than free-text intent, what happens when a tool cannot be intercepted or wrapped at all (a third-party SaaS image generator with no gateway hook, for instance)? Is "no enforceable gateway exists" sufficient grounds to deny every protected operation through that tool, or does it need its own diagnostic and a distinct decision-owner override path?
49. Still open. How should an enforcement adapter's documented bypass paths (action-boundary.md §11) be recorded so a conformance claim can be checked against them mechanically, rather than trusting prose in a README?
50. Reframed by 0.3.0: this module now reuses Security's existing `policy_owner` rather than a new "policy-author" role, but adds a stricter rule on top of it -- `policy_owner` MUST NOT equal the acting participant, for a guardrail governing a class under this module (action-boundary.md §3). Remaining question: should that stricter distinctness rule be promoted into security.md §4 itself, generally, rather than only applying under this module? And what is the correct behavior for a single-maintainer project where no second human exists to hold the role?
51. The first-pass resolver (tools/awp_action_boundary.py) treats any accepted `require_authorization` / `require_confirmation` / `require_review` guardrail as `unresolved` rather than modeling an actual review/confirmation workflow that could later turn it into `permit`. Is `unresolved` the right terminal state for those three effects under this module, or does the module need a fourth result value (something like `pending`) to distinguish "needs a human step" from "the resolver couldn't determine an answer"?
52. Resolved in 0.3.1: the first-pass resolver and §3.1 matched a decision against a contemplated action by reading Core's `affects` field as a glob selector, and aggregated an unqualified top-level `requirements` field Core does not define -- both a reinterpretation of a Core-owned field, caught by an independent review of a related harness proposal (research/model-assisted-reviews/, harness reconciliation exchange, 2026-09-13). Fixed by moving both under this module's own `modules."urn:awp:action-boundary"` extension namespace on the decision record, per core.md's existing `modules.{module-id}` convention -- Core's `affects` is now untouched and unread by this module. A new test (`test_core_affects_alone_does_not_make_a_decision_apply`) locks in that a decision setting only plain `affects` does not match. Remaining question: should a capsule authoring tool (a projector, or a future decision-authoring UX per the harness proposal's decision-capture UX, item still tracked informally) warn a policy owner who sets a decision's `affects` to something that looks like it was meant as an action-boundary selector, since the two are easy to conflate exactly as this defect shows?
