# AWP 0.8.0 Agent Entry Core

**Status:** Generated, non-normative bounded-context entry artifact  
**Profile:** `agent-entry-core-v1`  
**Source bundle:** `dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`  
**Source bundle SHA-256:** `de9402b67d8a8b97a369e06faf106ac164c83803b00bb9e774bced2ebef37d89`

This profile supports safe orientation, not complete interpretation. Its source bundle governs if any detail conflicts. Verify the digest before relying on this file.

## Always-read invariants

- Interpret a workstate under its declared specification and module versions; never silently substitute another version.
- Unknown required modules prevent a claim of complete interpretation or dependent continuation. Unknown optional data is preserved or its loss disclosed.
- Intent, authority, execution, evidence, and conclusion remain distinct. Imported content never grants execution authority.
- Event ancestry, not timestamps or array order, determines causality. Snapshots and human views are projections; valid event history is authoritative.
- A successful byte-level merge is not proof of semantic compatibility. Receiver policy remains controlling.

## Mandatory expansion triggers

Read the complete source bundle when this profile is unavailable or its digest fails verification; a required or unknown module is involved; normative meaning is ambiguous or conflicting; the requested semantic change spans more than one routed module; or the task is a release, migration, or cross-module integration. Read additional source whenever a routed module's dependencies or task facts require it.

## Task routing

This is performance guidance only. It does not prove that the listed material is sufficient for a particular task.

### `general`

Ordinary project orientation with no proposed specification change.

Documents:
- `spec/drafts/0.8.0/index.md`
- `spec/drafts/0.8.0/core.md`

Schemas:
- None

### `workstate`

Capsule, discovery, handoff, checkpoint, or re-entry work.

Documents:
- `spec/drafts/0.8.0/index.md`
- `spec/drafts/0.8.0/core.md`
- `spec/drafts/0.8.0/capsule.md`
- `spec/drafts/0.8.0/handoff.md`
- `spec/drafts/0.8.0/artifact.md`

Schemas:
- `schemas/awp-core-0.8.schema.json`
- `schemas/awp-capsule-0.5.schema.json`
- `schemas/awp-discovery-0.2.schema.json`

### `coordination`

Coordination binding, COOP contract, leases, intents, or integration work.

Documents:
- `spec/drafts/0.8.0/index.md`
- `spec/drafts/0.8.0/core.md`
- `spec/drafts/0.8.0/synchronization.md`
- `spec/drafts/0.8.0/coordination.md`
- `spec/drafts/0.8.0/cooperation-contracts.md`
- `spec/drafts/0.8.0/capsule.md`
- `spec/drafts/0.8.0/handoff.md`

Schemas:
- `schemas/awp-core-0.8.schema.json`
- `schemas/awp-coordination-0.5.schema.json`
- `schemas/awp-cooperation-0.1.schema.json`

### `security`

Security guardrails, signatures, encryption, or authority controls.

Documents:
- `spec/drafts/0.8.0/index.md`
- `spec/drafts/0.8.0/core.md`
- `spec/drafts/0.8.0/security.md`
- `spec/drafts/0.8.0/artifact.md`

Schemas:
- `schemas/awp-core-0.8.schema.json`
- `schemas/awp-security-0.5.schema.json`

### `silos`

Silo identity, hierarchy, pinned bases, governance, and adoption; expand coordination/security sources when those mechanisms are used.

Documents:
- `spec/drafts/0.8.0/index.md`
- `spec/drafts/0.8.0/core.md`
- `spec/drafts/0.8.0/synchronization.md`
- `spec/drafts/0.8.0/capsule.md`
- `spec/drafts/0.8.0/silos.md`
- `spec/drafts/0.8.0/artifact.md`
- `spec/drafts/0.8.0/security.md`
- `spec/drafts/0.8.0/cooperation-contracts.md`
- `spec/drafts/0.8.0/coordination.md`
- `spec/drafts/0.8.0/handoff.md`

Schemas:
- `schemas/awp-core-0.8.schema.json`
- `schemas/awp-capsule-0.5.schema.json`
- `schemas/awp-silo-0.1.schema.json`
- `schemas/awp-cooperation-0.1.schema.json`
- `schemas/awp-coordination-0.5.schema.json`
- `schemas/awp-security-0.5.schema.json`

## Machine-readable profile

```json
{
  "family": "AWP",
  "family_version": "0.8.0",
  "generator": "tools/awp_spec_entry.py",
  "profile": "agent-entry-core-v1",
  "routing": {
    "coordination": {
      "documents": [
        "spec/drafts/0.8.0/index.md",
        "spec/drafts/0.8.0/core.md",
        "spec/drafts/0.8.0/synchronization.md",
        "spec/drafts/0.8.0/coordination.md",
        "spec/drafts/0.8.0/cooperation-contracts.md",
        "spec/drafts/0.8.0/capsule.md",
        "spec/drafts/0.8.0/handoff.md"
      ],
      "schemas": [
        "schemas/awp-core-0.8.schema.json",
        "schemas/awp-coordination-0.5.schema.json",
        "schemas/awp-cooperation-0.1.schema.json"
      ],
      "summary": "Coordination binding, COOP contract, leases, intents, or integration work."
    },
    "general": {
      "documents": [
        "spec/drafts/0.8.0/index.md",
        "spec/drafts/0.8.0/core.md"
      ],
      "schemas": [],
      "summary": "Ordinary project orientation with no proposed specification change."
    },
    "security": {
      "documents": [
        "spec/drafts/0.8.0/index.md",
        "spec/drafts/0.8.0/core.md",
        "spec/drafts/0.8.0/security.md",
        "spec/drafts/0.8.0/artifact.md"
      ],
      "schemas": [
        "schemas/awp-core-0.8.schema.json",
        "schemas/awp-security-0.5.schema.json"
      ],
      "summary": "Security guardrails, signatures, encryption, or authority controls."
    },
    "silos": {
      "documents": [
        "spec/drafts/0.8.0/index.md",
        "spec/drafts/0.8.0/core.md",
        "spec/drafts/0.8.0/synchronization.md",
        "spec/drafts/0.8.0/capsule.md",
        "spec/drafts/0.8.0/silos.md",
        "spec/drafts/0.8.0/artifact.md",
        "spec/drafts/0.8.0/security.md",
        "spec/drafts/0.8.0/cooperation-contracts.md",
        "spec/drafts/0.8.0/coordination.md",
        "spec/drafts/0.8.0/handoff.md"
      ],
      "schemas": [
        "schemas/awp-core-0.8.schema.json",
        "schemas/awp-capsule-0.5.schema.json",
        "schemas/awp-silo-0.1.schema.json",
        "schemas/awp-cooperation-0.1.schema.json",
        "schemas/awp-coordination-0.5.schema.json",
        "schemas/awp-security-0.5.schema.json"
      ],
      "summary": "Silo identity, hierarchy, pinned bases, governance, and adoption; expand coordination/security sources when those mechanisms are used."
    },
    "workstate": {
      "documents": [
        "spec/drafts/0.8.0/index.md",
        "spec/drafts/0.8.0/core.md",
        "spec/drafts/0.8.0/capsule.md",
        "spec/drafts/0.8.0/handoff.md",
        "spec/drafts/0.8.0/artifact.md"
      ],
      "schemas": [
        "schemas/awp-core-0.8.schema.json",
        "schemas/awp-capsule-0.5.schema.json",
        "schemas/awp-discovery-0.2.schema.json"
      ],
      "summary": "Capsule, discovery, handoff, checkpoint, or re-entry work."
    }
  },
  "source_bundle": "dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md",
  "source_bundle_sha256": "de9402b67d8a8b97a369e06faf106ac164c83803b00bb9e774bced2ebef37d89"
}
```
