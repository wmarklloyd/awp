# Schema index

JSON Schemas validate structural constraints. Normative prose remains authoritative for cross-record invariants that a schema cannot express.

## Released schemas

- Core: `awp-core-0.3.schema.json` through `awp-core-0.6.schema.json`
- Module registry: `awp-module-registry-0.4.schema.json` through `awp-module-registry-0.6.schema.json`
- Coordination: `awp-coordination-0.3.schema.json`
- Repository discovery: `awp-discovery-0.1.schema.json`

## AWP 0.7.0 stable exploratory schemas

- Core: `awp-core-0.7.schema.json`
- Module registry: `awp-module-registry-0.7.schema.json`
- Capsule metadata: `awp-capsule-0.4.schema.json`
- Coordination: `awp-coordination-0.4.schema.json`
- Security guardrails: `awp-security-0.4.schema.json`
- The former `awp-discovery-0.2.schema.json` is retained as historical compatibility evidence; the working draft itself uses embedded discovery in the Markdown capsule and does not require a companion schema.

Published `$id` values and released schema bytes are immutable. Incompatible semantics require a new schema identifier.
