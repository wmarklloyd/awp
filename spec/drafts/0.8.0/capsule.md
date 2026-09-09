# AWP Capsule 0.5.0

**Module ID:** `urn:awp:capsule`  
**Status:** Optional  
**Depends on:** AWP Core `0.8.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

AWP Capsule defines the human-readable, project-local representation of one logical workstate. It does not define the semantics of optional modules carried by that representation.

The active 0.8 direction uses one canonical Markdown capsule, `<project-name>.awp.md`, inside a declared project. The project discovery document identifies that capsule and its governing specification. Standalone capsule exchange, editable-directory packages, ZIP packages, and JSON wire payloads are archived directions; they are not active 0.8 collaboration or conformance profiles.

For a project-named Markdown capsule, the default conventional filename is `<project-name>.awp.md`. When the project name is unavailable or ambiguous, producers SHOULD use `project.awp.md`. A producer MAY retain multiple capsule revisions using `<project-name>.v<revision>.awp.md`, for example `awp.v2.awp.md` or `project.v2026-09-04.awp.md`. The filename is a human-facing locator; it is not the AWP protocol version and MUST NOT override the capsule metadata.

A workstate using one of these representations MUST declare the Capsule module. It MUST mark Capsule required when no alternative declared representation makes the required Core and module state accessible without Capsule processing.

## 2. Project discovery

A single-file Markdown capsule is the canonical project workstate document. It MUST carry the metadata needed to interpret itself and be named by the project discovery document. The discovery document and capsule MUST identify the same governing specification and current workstate.

The front matter of a project capsule MUST include `format: single-file-capsule` and `discovery: project`. Its `specification` metadata identifies the exact specification artifact governing the workstate. A host MUST resolve the capsule through the project discovery document or a declared project entry point; an arbitrary supplied capsule path is not, by itself, a project or collaboration boundary.

When no project entry point names the capsule, an implementation MAY look for the conventional `<project-name>.awp.md` or `project.awp.md` in the project root. It MUST NOT silently choose among multiple candidate capsules. A filename is only a locator and MUST NOT be used to infer protocol compatibility. Discovering a declared URI MUST NOT trigger automatic network access.

Agent-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` are outside AWP. They MAY point directly to a capsule, but their presence is not required for AWP conformance.

## 3. Root briefing

Every project capsule MUST begin with or contain a root `WORK.md`-equivalent briefing. A human-facing reader SHOULD present it first.

The briefing MUST begin with metadata containing:

- `awp_version`;
- `specification`;
- `format: single-file-capsule` and `discovery: project` for a project Markdown capsule;
- `workstate_id`;
- `frontier`;
- current `checkpoint`, if one exists;
- `generated_at`;
- `generated_digest`.

Generated content MUST occur inside exactly one marker pair:

```markdown
---
awp_version: 0.8.0
specification: https://example.org/awp/0.8.0/AWP-0.8.0.bundle.md
format: single-file-capsule
discovery: project
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

A participant MUST NOT replace another participant's authored capsule content in place. A revision to an existing record MUST increment its `revision` and SHOULD record the prior generated digest. A revised capsule SHOULD identify its predecessor by artifact digest or explicit supersession reference. Consistency edits following an accepted decision belong in a new revision or superseding capsule; recomputing `generated_digest` does not by itself establish authorship, authorization, or continuity with the prior artifact.

`specification` identifies the exact specification artifact that governs the workstate. It SHOULD be an immutable, version-pinned URI when the specification is hosted remotely, such as a tagged GitHub raw URL. It MUST NOT use a moving branch URL as though it were version-pinned. A repository-relative local copy MAY be used when network retrieval is unavailable or inappropriate. A reader MUST NOT silently substitute another specification. An unavailable or unsupported declared specification makes the workstate `unverifiable` for protocol interpretation.

The digest uses `sha256:{lowercase-hex}` over the UTF-8 content beginning after the LF terminating the start marker and ending before the LF preceding the end marker, after CRLF-to-LF normalization.

A reader reports the briefing as:

- `current`: digest valid and frontier equals effective state;
- `modified`: generated-region digest differs;
- `stale`: digest valid but a newer effective frontier exists;
- `unverifiable`: required state or hash algorithm is unavailable.

Notes and content outside the generated region are non-authoritative. Importing a human edit into machine state requires an explicit proposed semantic change and acceptance by an authorized actor.

### 3.1 Briefing-first machine presentation

A host MAY read and validate the complete capsule without presenting every source byte to a human or model participant. A model-facing entry view SHOULD present the front matter and generated briefing first, then materialize only the active Resume, referenced Handoff and checkpoint, ordered `read_first` records, and compact descriptors for required artifacts. The source capsule remains authoritative; the entry view is a disposable projection and MUST identify its source capsule, source size, integrity state, and selection status.

A bounded entry view MUST report `complete` only when the active Resume, its explicitly selected records, referenced Handoff and checkpoint, and required artifact descriptors were resolved and verified according to the declared presentation profile. This status asserts structural completeness of the author-declared entry set, not that no other historical context can be relevant. If a byte or token budget cannot carry the declared entry set, the host MUST report `budget_exceeded` or `incomplete`, identify omitted or unresolved material, and stop or obtain more context according to receiver policy. It MUST NOT silently truncate required state or treat a generated briefing alone as complete semantic re-entry.

This two-stage presentation limits model context consumption, not validation. A Capsule reader claiming briefing-first presentation MUST still parse and validate the full representation, required modules, internal references, and integrity metadata before it reports the selected view as complete.

### 3.2 Canonical workstate maintenance

When a project maintains one current writable Capsule, its host SHOULD expose a canonical maintenance binding. The binding owns parsing, record projection, briefing rendering, artifact-integrity calculation, and serialization. An agent or model MAY submit semantic facts, a synchronization delta, or a checkpoint request, but MUST NOT be required to edit embedded JSON, calculate digests, or rewrite the canonical Capsule directly.

A checkpoint request for a canonical Capsule MUST carry an idempotency key, the expected whole-Capsule digest, the expected generated-region digest, the expected semantic frontier, the proposed semantic frontier, the checkpoint or no-change disposition, and the semantic handoff fields required by Handoff. The host MUST compare all expected values immediately before replacement. A mismatch MUST produce `stale_base` or an equivalent recoverable result; it MUST NOT use last-write-wins.

The host MUST serialize canonical replacement per workstate, write through a temporary file with flush and sync before atomic replacement, and return a receipt containing the prior and resulting whole-Capsule digests, generated-region digests, semantic frontier, checkpoint, and publication status. A no-change exit MUST return a verified receipt without rewriting identical bytes. A crash between replacement and durable publication MUST leave recoverable journal state and MUST NOT be reported as a confirmed checkpoint until recovery resolves it.

Artifact locations are not artifact identity. When bytes at a mutable location change, the writer MUST preserve the prior digest as historical evidence and create or reference a new artifact revision. It MUST NOT silently rewrite an old artifact claim to match new bytes. Routine entry MAY verify only active required artifacts; a full historical audit MUST be an explicit operation.

### 3.3 Informative efficient-maintenance guidance

The requirements above define observable safety and recovery behavior, not a requirement to reread or rewrite every workstate byte after every source-file write. An implementation can keep the common editing path small while preserving those requirements by separating an in-progress refresh from a semantic checkpoint.

During ordinary work that has not reached a handoff, integration, publication, or other semantic boundary, a host can append a compact, idempotent refresh record instead of immediately rewriting the canonical Capsule. A useful record binds its request identifier, current whole-Capsule and generated-region digests, semantic frontier, concise change summary, next action, and evidence references, and identifies its projection state as deferred. This record is durable progress evidence; it is not a replacement Capsule, a new semantic frontier, or proof that changed artifact digests are current. A receiver still treats affected artifact claims and any dependent entry selection as stale until a canonical projection incorporates and verifies the change.

A full canonical projection remains appropriate when semantic records, frontier, briefing, Resume, Handoff, required-artifact descriptors, or participant-facing entry state change; before integration or publication relies on the new state; and before a completed handoff claims current or complete state. A verified no-change operation remains preferable to rewriting identical bytes. Implementations can compact or discard superseded refresh records only under a declared retention and recovery policy that preserves every fact needed by the next projection.

Within one locked maintenance operation, an implementation can read the Capsule once, derive its whole-artifact digest, generated-region integrity, frontier, parsed snapshot, and proposed replacement from that same byte snapshot, and reuse those results through serialization and entry-view generation. The lock or equivalent serialization boundary still covers the final expected-state comparison and replacement. Cached artifact verification can likewise be reused only when it is bound to the exact artifact digest and verification policy and is invalidated by a relevant byte, policy, dependency, or environment change.

After a successful projection, a host can build a digest-bound entry slice from the already validated proposed state rather than reparsing the new Capsule and reverifying unchanged artifacts. The resulting slice remains disposable and gains no authority: it is accepted only when its recorded Capsule digest matches the authoritative Capsule, and a participant-facing `complete` result still depends on all validation required by Sections 3.1 and 3.2.

Model-facing maintenance requests and receipts should carry concise semantic fields, identifiers, digests, statuses, omissions, and diagnostics rather than embedding the full Capsule or unchanged artifact content. This reduces context consumption without hiding stale, incomplete, unavailable, or budget-exceeded state. Platform-specific buffering, memory mapping, cache layout, and filesystem primitives are implementation choices; implementers should benchmark the complete cold and warm paths on their supported filesystems and report what was measured rather than infer performance from a storage technology.

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

## 6. Archived representation directions

Editable-directory packages, ZIP packages, JSON wire payloads, and standalone capsule exchange are archived design directions. They have no active AWP 0.8 conformance claim and MUST NOT be represented as a substitute for a project-scoped workstate or a COOP binding. A future version MAY define a transport or inter-project profile with its own discovery, authority, integrity, and lifecycle rules.

## 7. Module placement

A module declaration may specify a `representation` object:

```json
{
  "id": "urn:awp:coordination",
  "version": "0.5.0",
  "required": false,
  "representation": {
    "kind": "project-path",
    "path": "modules/coordination/state.json"
  }
}
```

Standard representation kinds are `capsule-section`, `project-path`, `remote`, and `events-only`. A remote module location MUST disclose retrieval requirements. Secrets MUST NOT appear in locations.

Module placement does not create a separate causal history. Module events always participate in the Core event graph.

## 8. Conformance

A Capsule reader MUST validate the project representation safely, present the briefing, expose manifest module requirements, and preserve unknown sections when claiming lossless processing. A reader claiming repository-discovery support MUST implement Section 2 and expose discovery failures.

A Capsule writer MUST create an unambiguous project representation, bind generated prose to a frontier and digest, include or declare every required component, and accurately identify omitted or remote content. A project Markdown writer MUST include its discovery mode and governing specification in the capsule metadata.
