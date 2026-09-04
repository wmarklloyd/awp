# Related work and novelty boundary

AWP combines established ideas rather than claiming that work provenance, event graphs, or distributed coordination are new. Its proposed contribution is a portable, agent-oriented composition of semantic workstate, resumable checkpoints, epistemic status, explicit authority boundaries, and coordination records that remain useful without a live coordinator.

## Related systems

| Area | Established contribution | AWP relationship |
|---|---|---|
| Git and distributed version control | Content-addressed source history and byte-level merge | AWP references repository revisions and adds semantic intent, dependency, and conflict records; it does not replace Git. |
| Event sourcing and logical clocks | Causal history, replay, and ordering without relying solely on wall-clock time | AWP uses an event DAG and frontiers, but deterministic replay remains subject to defined module transition rules. |
| CRDT research | Convergence for formally specified concurrent data types | AWP does not claim general CRDT convergence; unknown or non-commutative changes remain conflicts. |
| W3C PROV | A general model for entities, activities, agents, and provenance | AWP uses domain-specific workstate records and may require a future explicit mapping. |
| in-toto and supply-chain attestations | Verifiable statements about software-supply-chain steps and artifacts | AWP artifact and verification records may reference attestations but do not replace their trust models. |
| Workflow checkpointing | Resumption of execution or orchestration state | AWP distinguishes semantic, operational, and exact resumption and does not promise deterministic model output. |
| Agent transports and tool protocols | Message exchange and tool/resource access | AWP is transport-independent and does not treat authenticated transport or tool availability as authorization. |

## Primary references

- L. Lamport, [“Time, Clocks, and the Ordering of Events in a Distributed System”](https://doi.org/10.1145/359545.359563), *Communications of the ACM*, 1978.
- M. Shapiro et al., [“Conflict-Free Replicated Data Types”](https://doi.org/10.1007/978-3-642-24550-3_29), SSS 2011.
- W3C, [“PROV-O: The PROV Ontology”](https://www.w3.org/TR/prov-o/), W3C Recommendation, 2013.
- IETF, [RFC 8785, “JSON Canonicalization Scheme”](https://www.rfc-editor.org/rfc/rfc8785), 2020.
- in-toto Project, [“in-toto Specification”](https://github.com/in-toto/attestation/tree/main/spec).

## Claims requiring evidence

AWP has not yet demonstrated broad interoperability, lower coordination cost, reliable semantic-conflict detection, or production safety. Those are hypotheses for conformance testing and controlled experiments, not established results.
