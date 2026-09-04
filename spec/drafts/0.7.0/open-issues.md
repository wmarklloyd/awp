# AWP Open Issues 0.7.0

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
7. Is `.pws` sufficiently collision-free and registrable as a package extension?
8. Which artifact retrieval profiles can express expiring access without placing credentials in workstate data?
9. Which media types require mandatory sandboxing or sanitization profiles?

## Synchronization questions

10. How can histories be compacted while proving lineage, preserving unknown-module effects, and retaining adequate audit evidence?
11. Which semantic conflict classes can be resolved mechanically?
12. Should a future convergence profile adopt an existing CRDT or Merkle-DAG representation?
13. What canonical state representation is suitable for replay equivalence proofs?

## Coordination questions

14. Which Python, TypeScript, and later language selector profiles best preserve semantic identity across rename, move, extraction, and replacement?
15. What formally verified C3 coordinator algorithm and enforcing adapter should become the first interoperability profile?
16. Which semantic effects can tools infer reliably, how should confidence be calibrated, and which effects must remain actor assertions?
17. Which verification procedures provide adequate evidence for particular contract and invariant classes?
18. Which Git, worktree, CI, and forge mappings should become standard adapter profiles?
19. What policy-composition rules resolve multiple organization-specific contract decision policies without silently weakening a required party?
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

28. Which agent runtimes will adopt `.awp.json` discovery directly, and which will require an agent-specific instruction shim or launcher integration?
29. What context-selection benchmark demonstrates that Resume Profile loading reduces tokens and startup time without omitting safety-critical state?

