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
