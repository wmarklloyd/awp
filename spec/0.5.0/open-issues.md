# AWP Open Issues 0.5.0

**Status:** Informative issue register

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

14. Which semantic scope selectors remain stable across refactors and languages?
15. How should enforced coordinators expose term, scope, fencing tokens, and partition behavior?
16. Which semantic effects can tools infer reliably, and which must remain actor assertions?
17. How can verification establish that a textual merge preserves contracts and invariants?
18. Which Git and forge mappings should become standard adapter profiles?

## Security and governance questions

19. Which canonicalization and signature profiles should be registered first?
20. Should encryption be standardized at package, module, artifact, or recipient-envelope level?
21. How should retention, legal deletion, classification, and jurisdiction metadata interoperate across organizations?
22. What privacy-preserving evidence can demonstrate secret scanning without exposing scanner configuration or findings?

## Adapter questions

23. How closely should A2A and MCP bindings track upstream protocol release cycles?
24. Which round-trip losses are acceptable for workflow and model-runtime adapters?
25. How should bindings negotiate module versions when their transport has a different capability model?

## Resume and discovery questions

26. Which agent runtimes will adopt `.awp.json` discovery directly, and which will require an agent-specific instruction shim or launcher integration?
27. What context-selection benchmark demonstrates that Resume Profile loading reduces tokens and startup time without omitting safety-critical state?

