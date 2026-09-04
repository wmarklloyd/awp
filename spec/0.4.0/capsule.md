# AWP Capsule 0.1.0

**Module ID:** `urn:awp:capsule`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Capsule defines human-readable and packaged representations of one logical workstate. It does not define the semantics of optional modules carried by those representations.

The representations are:

- editable directory: `name.workstate/`;
- self-contained Markdown capsule: `name.awp.md`;
- ZIP-compatible package: `name.pws`;
- JSON wire payloads.

Logical equivalence does not require identical bytes or file layout. The manifest maps logical data to physical locations.

A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing.

## 2. Root briefing

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
awp_version: 0.4.0
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

## 3. Editable directory

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

## 4. Single-file Markdown capsule

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

## 5. Package representation

A `.pws` package is ZIP-compatible and expands to the editable-directory logical layout. Proposed media type: `application/awp+zip`.

Unpacking MUST preserve logical paths, bytes, IDs, module declarations, and references. Readers MUST reject absolute paths, parent traversal, duplicate normalized paths, case-folding collisions on case-insensitive targets, symlink escapes, and members exceeding configured size or decompression limits.

Writers SHOULD place `WORK.md` and `manifest.json` before large members for preview efficiency. Physical member order has no semantic meaning.

## 6. Wire representation

JSON wire bindings may carry a manifest, snapshot, event sequence, delta, artifact announcement, module data, or retrieval request. Proposed media types are:

```text
application/awp+json
application/awp-event+json
application/awp-delta+json
```

The Capsule module defines payload representation, not transport authentication, delivery guarantees, or live synchronization.

## 7. Module placement

A module declaration may specify a `representation` object:

```json
{
  "id": "urn:awp:coordination",
  "version": "0.1.0",
  "required": false,
  "representation": {
    "kind": "package-path",
    "path": "modules/coordination/state.json"
  }
}
```

Standard representation kinds are `package-path`, `capsule-section`, `remote`, and `events-only`. A remote module location does not make the workstate self-contained and MUST disclose retrieval requirements. Secrets MUST NOT appear in locations.

Module placement does not create a separate causal history. Module events always participate in the Core event graph.

## 8. Conformance

A Capsule reader MUST validate the representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing.

A Capsule writer MUST create an unambiguous representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content.
