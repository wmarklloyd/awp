# Informative formal model

This note states the mathematical structure implied by the AWP event model. It is informative until its definitions are incorporated into a versioned normative module and exercised by complete replay fixtures.

## Event graph

Let a workstate history be a finite directed acyclic graph (G=(V,E)). Each vertex is an event. An edge ((p,e)) exists when event (e) names event (p) as a parent. The transitive closure (p \prec e) means that (p) causally precedes (e). Events (a) and (b) are concurrent when neither (a \prec b) nor (b \prec a).

A frontier (F \subseteq V) is an antichain containing the maximal known events:

\[
F = \{v \in V \mid \nexists w \in V : v \prec w\}.
\]

The history represented by a frontier is the ancestor closure (H(F)=F\cup\{v\mid\exists f\in F:v\prec f\}).

## Projection

For a declared module set (M), a projection is a partial function

\[
P_M : H(F) \rightarrow S \cup D,
\]

where (S) is materialized state and (D) is a diagnostic outcome such as invalid, divergent, conflicting, stale, or unverifiable.

A deterministic projection requires every valid topological ordering of causally independent events to produce the same state, or requires a module rule to preserve the alternatives as an explicit conflict. Last-write-wins based on arrival order or wall-clock time does not satisfy this condition.

## Revisioned records

For record identifier (r), accepted updates form a revision chain (r_1,r_2,\ldots,r_n). An update from revision (i) to (i+1) is applicable only when its declared prior revision equals the effective revision. Concurrent non-commutative updates from the same prior revision produce a conflict rather than an implicit winner.

## Knowledge and authority

Epistemic state and authority are separate projections. Evidence may change the epistemic status of a claim without granting an action. An authority assertion may be retained as evidence while the receiver’s authorization function rejects it under current identity, scope, expiration, revocation, or local policy.

## Coordination overlap

Let (S_a) and (S_b) be revision-pinned declared scopes with access modes. A physical overlap exists when their selectors resolve to intersecting repository objects at the declared bases. A semantic overlap exists when they reference the same semantic definition or when a registered relation connects their definitions. Material conflict is a policy function of overlap, access modes, relied-upon reads, accepted contracts, ordering constraints, and uncertainty.

The base specification does not claim that arbitrary semantic equivalence is decidable. Language-specific selectors, relation registries, and analyzer confidence require named profiles and empirical calibration.

## Outstanding proof obligations

- Define canonical event and state encodings.
- Prove or test confluence for every declared commutative transition.
- Specify behavior for unknown required event kinds.
- Establish replay equivalence across two independent implementations.
- Define compaction proofs that preserve lineage and unknown-module effects.
