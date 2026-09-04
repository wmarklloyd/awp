# Protocol evolution

## Version model

AWP uses semantic-version-shaped identifiers. During the `0.x` phase, incompatible changes increment the minor version; compatible editorial or defect corrections may increment the patch version. Released bytes and schema identifiers are immutable.

Family and module versions are separately declared. A family release identifies one tested set of module versions. Implementations determine support from the governing specification, module identifiers, and module versions rather than the family number alone.

## Working drafts

Development occurs under `spec/drafts/<target-version>/`. Draft files may change without compatibility guarantees and must state that they are not releases. A draft may refer to an exact repository commit or local specification copy when used for experiments.

## Release procedure

1. Resolve or explicitly defer open normative issues.
2. Assign final family, module, schema, and event-envelope versions.
3. Freeze requirement identifiers and conformance roles.
4. Pass schemas, procedural validation, fixtures, and bundle-reproducibility checks.
5. Publish release notes, checksums, citation metadata, and known limitations.
6. Create an annotated, preferably signed tag and never move it.

## Errata and deprecation

An erratum documents a defect without changing released bytes. A semantic correction is issued as a new version. Deprecated features remain interpretable for the versions that defined them; removal or changed meaning requires an incompatible release.
