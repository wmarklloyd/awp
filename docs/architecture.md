# Architecture

## System boundary

AWP defines portable workstate semantics and representations. It does not provide an agent runtime, source-control system, identity provider, authorization service, consensus system, artifact store, or deployment controller.

## Layers

1. **Core** defines identity, actors, typed semantic records, event ancestry, frontiers, snapshots, provenance, and epistemic status.
2. **Representation modules** define how logical state is carried in directories, Markdown capsules, packages, or wire payloads.
3. **Continuation modules** define checkpoints, handoffs, resume profiles, artifact references, and synchronization.
4. **Coordination** defines intents, scopes, overlaps, contracts, preconditions, verification, staleness, and integration records.
5. **Bindings** map AWP concepts to external repositories, transports, runtimes, and policy systems without importing their authority implicitly.

## State model

The event graph is causal history. A frontier identifies the maximal events known to a projection. Snapshots and generated prose are derived views and cannot override valid event ancestry. Unknown required semantics make an affected operation unverifiable rather than silently successful.

An [informative formal model](formal-model.md) states the event DAG, frontier, projection, revision, and overlap concepts and identifies their outstanding proof obligations.

## Trust model

Structure, provenance, integrity, trust, and authority are distinct. A digest establishes byte identity. A signature may establish control of a key. Neither establishes truth, safety, current authorization, or permission for an external side effect.

## Conformance boundary

JSON Schemas validate local structure. Cross-record invariants—including ancestry, revision transitions, authority evaluation, reference resolution, and deterministic projection—require procedural validators and conformance fixtures. Claims beyond that evidence are explicitly experimental.
