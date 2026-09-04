# AWP Capsule 0.2.0

**Module ID:** `urn:awp:capsule`  
**Status:** Optional  
**Depends on:** AWP Core `0.5.x`

## 1. Scope

AWP Capsule defines human-readable and packaged representations of one logical workstate. It does not define the semantics of optional modules carried by those representations.

The representations are:

- editable directory: `name.workstate/`;
- self-contained Markdown capsule: `name.awp.md`;
- ZIP-compatible package: `name.pws`;
- JSON wire payloads.

Logical equivalence does not require identical bytes or file layout. The manifest maps logical data to physical locations.

A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing.

## 2. Repository discovery

A project MAY place a `.awp.json` discovery document at its declared project root so that a AWP-aware agent or tool can locate the current workstate without scanning the project. The discovery document is a pointer, not a workstate, trust assertion, or authority grant.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "awp_schema": "urn:awp:schema:discovery:0.1.0",
  "awp_discovery_version": "0.1",
  "current_workstate": "conversation.awp.md",
  "specification": "AWP_SPECIFICATION_0.5.0.bundle.md",
  "fallback_workstates": []
}
```

`awp_schema`, `awp_discovery_version`, and `current_workstate` are REQUIRED. `awp_schema` identifies this AWP discovery schema without assuming that a copied project contains AWP's source tree. `specification` and `fallback_workstates` are optional. Relative paths are resolved from the directory containing `.awp.json`. A local path MUST be relative, normalized, remain within the project root after resolution, and identify a regular file. A URI MAY be used only by a binding that defines retrieval and security behavior; discovering a URI MUST NOT trigger automatic network access.

A AWP-aware project-entry implementation SHOULD look for `.awp.json` in the project root supplied by its host, repository binding, invocation, or configuration. It MUST NOT search above that root. When the file is present, it MUST validate [the discovery schema](../../schemas/awp-discovery-0.1.schema.json) before following a pointer. It then opens `current_workstate` using the normal Capsule and Core procedures.

If `.awp.json` is missing, invalid, unsafe, or points to unavailable content, the implementation reports discovery as `absent`, `invalid`, `unsafe`, or `unavailable`. It MAY accept an explicitly supplied capsule instead. It MUST NOT silently select a fallback whose identity conflicts with an already selected workstate.

Agent-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` are outside AWP. They MAY point to `.awp.json` or directly to a capsule, but their presence is not required for AWP conformance.

## 3. Root briefing

Every complete directory, Markdown capsule, or package MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first.

The briefing MUST begin with metadata containing:

- `awp_version`;
- `workstate_id`;
- `frontier`;
- current `checkpoint`, if one exists;
- `generated_at`;
- `generated_digest`.

Generated content MUST occur inside exactly one marker pair:

```markdown
---
awp_version: 0.5.0
workstate_id: urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727
frontier:
  - evt:01K4M4VYB9
checkpoint: checkpoint:release-ready
generated_at: 2026-09-03T20:15:00Z
generated_digest: sha256:6d577db62a91e1a7b589a31fcab3142b456662b3a6af552befd373cc38f08246
---

<!-- awp:generated:start -->
# Prepare product launch

Implementation and local verification are complete. Production approval remains outstanding.
<!-- awp:generated:end -->

<!-- awp:notes:start -->
Human notes may be edited here.
<!-- awp:notes:end -->
```

The digest uses `sha256:{lowercase-hex}` over the UTF-8 content beginning after the LF terminating the start marker and ending before the LF preceding the end marker, after CRLF-to-LF normalization.

A reader reports the briefing as:

- `current`: digest valid and frontier equals effective state;
- `modified`: generated-region digest differs;
- `stale`: digest valid but a newer effective frontier exists;
- `unverifiable`: required state or hash algorithm is unavailable.

Notes and content outside the generated region are non-authoritative. Importing a human edit into machine state requires an explicit proposed semantic change and acceptance by an authorized actor.

## 4. Editable directory

The default layout is:

```text
example.workstate/
  WORK.md
  manifest.json
  events.jsonl
  snapshot.json
  artifacts/
  modules/
    coordination/
      state.json
    security/
      signatures.json
  views/
```

`WORK.md` and `manifest.json` are REQUIRED. `events.jsonl` is REQUIRED unless the manifest declares a snapshot-only representation. `snapshot.json`, `artifacts/`, `modules/`, and `views/` are optional.

Each `events.jsonl` line contains one complete JSON event. Module-specific events remain in this unified ledger. Module-owned auxiliary data MAY occupy separate files under `modules/`, but their manifest locations are authoritative; directory names are conventional only.

Generated files under `views/` are never authoritative.

## 5. Single-file Markdown capsule

A `.awp.md` file begins with briefing metadata and human Markdown, followed by machine sections. Front matter MUST declare `capsule_boundary`, a lowercase hexadecimal token containing at least 128 bits of unpredictable entropy.

An end marker occupies a complete line and exactly matches:

```text
<!-- awp:{boundary}:{section}:end -->
```

A start marker occupies a complete line and begins:

```text
<!-- awp:{boundary}:{section}:start
```

It may contain attributes of the form ` name="value"` before ` -->`. Attribute names match `[a-z][a-z0-9_-]*`; values MUST NOT contain a quote, CR, LF, or `-->`.

Canonical section order is:

1. front matter and briefing;
2. `manifest`;
3. `snapshot`, when present;
4. `events`, when present;
5. `records`, when not materialized in the snapshot;
6. `artifact` sections;
7. `module` sections;
8. optional derived views or notes.

```markdown
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:module:start id="urn:awp:coordination" encoding="json" -->
{"lease_enforcement":"advisory"}
<!-- awp:7d8c9f2ae43b1c8066a71a5d93470e11:module:end -->
```

The boundary token MUST NOT occur in decoded section content. A writer detecting a collision MUST generate a new boundary or encode the content using a binary-safe encoding such as base64. Binary artifacts MUST use base64 or a registered binary-safe encoding.

A reader MUST validate marker pairing, reject duplicate authoritative sections, verify each module section against a matching manifest declaration, reject malformed boundaries, and preserve unknown sections during lossless rewriting. It MUST NOT infer machine state from arbitrary Markdown headings or code examples outside marked sections.

## 6. Package representation

A `.pws` package is ZIP-compatible and expands to the editable-directory logical layout. Proposed media type: `application/awp+zip`.

Unpacking MUST preserve logical paths, bytes, IDs, module declarations, and references. Readers MUST reject absolute paths, parent traversal, duplicate normalized paths, case-folding collisions on case-insensitive targets, symlink escapes, and members exceeding configured size or decompression limits.

Writers SHOULD place `WORK.md` and `manifest.json` before large members for preview efficiency. Physical member order has no semantic meaning.

## 7. Wire representation

JSON wire bindings may carry a manifest, snapshot, event sequence, delta, artifact announcement, module data, or retrieval request. Proposed media types are:

```text
application/awp+json
application/awp-event+json
application/awp-delta+json
```

The Capsule module defines payload representation, not transport authentication, delivery guarantees, or live synchronization.

## 8. Module placement

A module declaration may specify a `representation` object:

```json
{
  "id": "urn:awp:coordination",
  "version": "0.2.0",
  "required": false,
  "representation": {
    "kind": "package-path",
    "path": "modules/coordination/state.json"
  }
}
```

Standard representation kinds are `package-path`, `capsule-section`, `remote`, and `events-only`. A remote module location does not make the workstate self-contained and MUST disclose retrieval requirements. Secrets MUST NOT appear in locations.

Module placement does not create a separate causal history. Module events always participate in the Core event graph.

## 9. Conformance

A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing. A reader claiming repository-discovery support MUST implement Section 2 and expose discovery failures.

A Capsule writer MUST create an unambiguous representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content. A writer that emits `.awp.json` MUST produce a schema-valid, traversal-safe discovery document.


