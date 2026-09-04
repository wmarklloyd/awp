# Governance

## Project status

AWP is an independent exploratory protocol project, not a standard of an accredited standards-development organization. The repository editor is responsible for accepting changes and publishing releases. This status must remain explicit until governance changes.

## Roles

- **Editor:** Maintains normative text, resolves proposals, and publishes releases.
- **Contributor:** Submits issues, proposals, fixtures, implementations, or reviews.
- **Implementer:** Reports interoperability results and may claim only the conformance actually demonstrated.
- **Reviewer:** Evaluates a named revision. A review is not described as independent peer review unless its provenance and review process support that claim.

The current editor is Mark Lloyd.

## Decision process

Normative proposals must identify motivation, affected requirements, compatibility, security consequences, alternatives, and validation evidence. Substantive accepted decisions receive an architecture-decision record under `docs/decisions/`. Unresolved objections are recorded rather than erased.

The editor may accept, revise, defer, or reject a proposal. Decisions should favor demonstrated interoperability and falsifiable requirements over feature breadth.

## Releases

1. Development occurs in `spec/drafts/<version>/`.
2. Automated validation and conformance fixtures must pass.
3. Release contents and checksums are generated reproducibly.
4. The release is copied to an immutable version directory and tagged.
5. Published files and schema identifiers are never reused for changed semantics.
6. Post-release corrections are errata or new versions; tags are never moved.

During the `0.x` series, an incompatible change increments the minor version. Patch releases contain compatible corrections only. Support for one version does not imply support for another.
