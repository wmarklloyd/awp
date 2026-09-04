# AWP Artifact 0.1.0

**Module ID:** `urn:awp:artifact`  
**Status:** Optional  
**Depends on:** AWP Core `0.4.x`

## 1. Scope

AWP Artifact defines how workstate records identify, locate, verify, version, retrieve, and redact concrete inputs and outputs. Core defines the `artifact` record identity; this module defines its storage semantics.

A workstate using Artifact fields MUST declare this module. It MUST mark the module required when continuation depends on retrieving, verifying, executing, or distinguishing the availability of an artifact.

## 2. Artifact descriptor

```json
{
  "id": "artifact:release-plan-v3",
  "type": "artifact",
  "name": "release-plan.md",
  "modules": {
    "urn:awp:artifact": {
      "logical_name": "release-plan",
      "role": "deliverable",
      "media_type": "text/markdown",
      "size": 4832,
      "status": "available",
      "integrity": {
        "algorithm": "sha256",
        "digest": "7d8c9f2ae43b1c8066a71a5d93470e11"
      },
      "locations": [
        {
          "kind": "package",
          "path": "artifacts/sha256/7d/7d8c9f2ae43b1c8066a71a5d93470e11.bin"
        }
      ],
      "trust": "authored",
      "executable": false,
      "instructional_content": true
    }
  }
}
```

Artifact-module fields live under `modules["urn:awp:artifact"]`. Required module fields are `status` and `locations`. An available packaged artifact MUST include `media_type`, `size`, and `integrity`. Statuses are `available`, `retrievable`, `unavailable`, `withheld`, `redacted`, and `superseded`.

Logical identity and content identity are distinct. A modified artifact receives a new record ID and content digest but MAY retain the same `logical_name`. A change record links before and after versions.

## 3. Location registry

| Kind | Required fields | Optional fields |
|---|---|---|
| `embedded` | `section_id` | `encoding` |
| `package` | `path` | none |
| `local` | `path` | `absolute` |
| `remote` | `uri` | `expires_at`, `retrieval_requirements` |
| `repository_relative` | `repository`, `revision`, `path` | `submodule_revision` |
| `unavailable` | `reason` | `last_known_location` |
| `withheld` | `reason` | `request_process` |

Private kinds MUST use collision-resistant namespaced values.

Package paths MUST be relative, normalized, and traversal-safe. Secrets, bearer tokens, cookies, and authorization headers MUST NOT appear in locations. Retrieval requirements may refer to separately authorized credentials without containing them.

An absolute local path is a hint tied to an identified environment. A receiver MUST NOT assume that it names the same resource locally.

## 4. Integrity

Packaged and embedded artifacts MUST include a digest over the exact decoded bytes. Remote and repository-relative artifacts SHOULD include a digest whenever stable bytes are expected. Hash algorithms are registry values; SHA-256 is the default for this module version.

Readers SHOULD verify a digest before relying on content. Digest validity establishes byte identity, not safety, truth, authorship, or authority.

Content-addressed packaged artifacts are immutable. Changing bytes creates a new content identity. A mutable remote URI SHOULD be paired with a digest, immutable version, ETag, or explicit `mutable: true` warning.

## 5. Availability and retrieval

`available` means bytes are present in the current representation. `retrievable` means a declared process may obtain them. `unavailable` means they are absent without a policy prohibition. `withheld` means policy intentionally excludes them. `redacted` means bytes were removed from a rewritten lineage.

A portable Handoff that depends on an artifact MUST include it, make it retrievable, or state that continuation is blocked. A URI alone is not proof of retrievability.

Retrieval is an external action subject to receiver authority and security policy. Merely referencing a remote artifact MUST NOT trigger automatic network access.

## 6. Executable and instructional content

Descriptors MUST state whether content is executable or may contain instructions when either is known. Unknown values SHOULD be represented explicitly rather than assumed false.

Readers MUST treat instructions in untrusted artifacts as data. Executables, archives, active documents, and model-readable instruction files SHOULD be inspected in an appropriate sandbox before use.

## 7. Redaction tombstones

Physical redaction creates a new history lineage and retains a descriptor tombstone under the original logical record ID:

```json
{
  "id": "artifact:secret-file",
  "type": "artifact",
  "name": "secret-file.env",
  "modules": {
    "urn:awp:artifact": {
      "status": "redacted",
      "locations": [],
      "redaction": {
        "reason": "credential_exposure",
        "redacted_at": "2026-09-03T21:00:00Z",
        "redacted_by": "actor:admin"
      },
      "original_integrity": {
        "algorithm": "sha256",
        "digest": "7d8c9f2ae43b1c8066a71a5d93470e11"
      }
    }
  }
}
```

The tombstone MUST remove sensitive bytes and locations, preserve referential integrity, disclose rewritten history, and invalidate signatures covering removed bytes. It MAY retain the original digest only when the digest is not itself sensitive. It MUST NOT imply that the bytes remain available.

Ordinary semantic deletion is not physical redaction and leaves event bytes intact.

## 8. Conformance

An Artifact reader validates registered location requirements, applies path and retrieval safety rules, checks digests when claiming verified integrity, and preserves availability status.

An Artifact writer assigns new identities to changed content, supplies required integrity metadata, avoids credentials in locations, and represents omission or redaction explicitly.
