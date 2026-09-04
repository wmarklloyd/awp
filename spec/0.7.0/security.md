# AWP Security 0.4.0

**Module ID:** `urn:awp:security`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`; AWP Artifact `0.4.x` when `artifact-controls` is declared  
**Document status:** Stable Exploratory Release  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

Core requires safe interpretation and local authority checks. This module adds portable security metadata for classification, import assessment, guardrails, secret scanning, physical redaction lineage, signatures, and encryption declarations.

Security metadata is evidence, not an instruction to trust content or weaken receiver policy.

A workstate using Security metadata MUST declare this module. It MUST be required when interpreting a registered signature, encryption, redaction, or handling profile is necessary for the receiver's declared continuation. Core safety rules still apply when this module is absent.

## 2. Threat model

A workstate may contain malicious, misleading, stale, or compromised records; prompt injection; executable artifacts; archive traversal; decompression bombs; forged authority; replayed events; secrets; personal data; and references that trigger external side effects.

AWP does not make untrusted content safe merely by structuring or signing it. Receivers apply current local policy and least authority.

## 3. Manifest security metadata

```json
{
  "module_data": {
    "urn:awp:security": {
      "classification": "private",
      "contains_secrets": false,
      "contains_personal_data": "unknown",
      "secret_scan": {
        "status": "passed",
        "scanned_at": "2026-09-03T20:14:00Z",
        "policy": "org.example/default-export",
        "scanner": "example-scanner/4.2"
      },
      "redaction_lineage": null,
      "signatures": []
    }
  }
}
```

The displayed object is the module-owned portion of a Core manifest. Security fields live under `module_data["urn:awp:security"]`.

Classification and privacy vocabularies may be organization-specific but private values MUST be namespaced. `contains_secrets` is `true`, `false`, or `unknown`. A writer MUST NOT use `false` when secret-scan status is `findings`, `not_run`, or `unknown`.

## 4. Shared guardrails

A guardrail is a portable, structured security constraint that limits what an actor or runtime may do with a workstate. It is a security extension of a Core `constraint` record and MUST remain subordinate to receiver policy and currently verified authority. A guardrail communicates a prohibition or required control across models, agents, runtimes, and transports; it is not merely a system-prompt convention.

A guardrail SHOULD identify:

- the operation classes and resources it governs;
- the actors, roles, or `all_actors` population to which it applies;
- its effect, such as `deny`, `require_authorization`, `require_confirmation`, or `require_review`;
- conditions, exceptions, effective period, policy owner, and provenance;
- whether its enforcement is `advisory`, `receiver_policy`, or `protected_adapter`.

For example, a workstate may carry this module extension under a Core constraint:

```json
{
  "id": "constraint:no-unauthorized-third-party-access",
  "type": "constraint",
  "statement": "Do not access, probe, exploit, or alter third-party systems unless explicit authority and scope permit the operation.",
  "strength": "required",
  "status": "active",
  "modules": {
    "urn:awp:security": {
      "guardrail": {
        "profile": "awp-security-guardrail-v1",
        "effect": "deny",
        "applies_to": "all_actors",
        "operation_classes": ["third_party_api_call", "security_sensitive", "external_write"],
        "resources": ["resource:third-party-systems"],
        "conditions": ["Only explicitly authorized resources are in scope."],
        "policy_owner": "actor:project-owner",
        "provenance": {
          "issued_by": "actor:project-owner",
          "basis": "authority:project-security-policy",
          "authority_evidence": "evidence:security-policy-approval"
        },
        "enforcement": "receiver_policy",
        "propagation": "mandatory"
      }
    }
  }
}
```

Guardrails apply in both solo and collaborative work. A lone agent's requested action is evaluated against the applicable guardrails before execution. In a collaboration, the same guardrails apply to every participating agent, delegated task, change set, integration plan, and derived operation. An agent MUST NOT evade a guardrail by asking another agent to perform the prohibited step, splitting it into individually innocuous steps, or moving it into an adapter. A collaborator may add a stricter guardrail, but MUST NOT weaken or override an applicable required guardrail through an intent, authority claim, contract, or user-arbitration alternative.

Portable guardrails are shared policy state, not proof of enforcement. A host or protected adapter must enforce them. If a required guardrail cannot be interpreted, its scope or policy owner is ambiguous, or its enforcement status is unverifiable, the affected external or security-sensitive operation MUST remain blocked pending local policy evaluation. Guardrail changes are new revisions with provenance; they do not silently mutate prior workstate history.

An imported guardrail is effective only when its `policy_owner`, `provenance`, and authority basis are accepted by the receiving policy. A record cannot make itself an effective guardrail by asserting `strength: required`, and an untrusted participant cannot globally block unrelated receiver work merely by importing one. An unverified guardrail is surfaced as a proposed or unverifiable policy condition; when the declared continuation depends on it, the affected operation remains blocked until local policy resolves it.

For applicable guardrails, the receiver first evaluates scope, actors, operation class, resources, conditions, and effective period. Among guardrails accepted by the receiver, a deny is more restrictive than a requirement, and a requirement is more restrictive than no control. Equal-authority disagreement is `unverifiable` and cannot silently permit a guarded operation. Only an authorized successor from the policy owner or a superior receiver policy may relax, replace, or retire a required guardrail. Delegated, decomposed, derived, and adapter-mediated operations inherit every applicable mandatory guardrail.

## 5. Import quarantine

Receivers SHOULD place newly imported workstates in local quarantine until they evaluate:

- origin and transport context;
- required modules and schemas;
- package-path and size safety;
- declared and verified integrity;
- classification and handling policy;
- active instructions and executables;
- authority, expiration, and revocation;
- requested external side effects.

Quarantine is receiver-owned state. A serialized assertion MAY describe the sender's handling state but MUST NOT disable receiver quarantine or grant trust.

## 6. Prompt injection and active content

Text in artifacts, summaries, claims, evidence, transcripts, extensions, and module data may contain instructions. Merely parsing, rendering, retrieving, verifying, or signing a workstate MUST NOT authorize execution.

Readers MUST distinguish descriptive content from an authorized requested action. Unknown modules and executable content MUST NOT run automatically. Module processors SHOULD be isolated according to risk.

## 7. External side effects

An imported task classified as `external_write`, `third_party_api_call`, `data_migration`, `communication`, `financial`, `security_sensitive`, or `destructive` MUST NOT become ready or execute solely because the workstate requests it.

The receiver re-evaluates current identity, resource scope, authority source, conditions, expiration, revocation, confirmation requirements, and local policy. A receiver with greater access than the sender MUST avoid becoming a confused deputy.

## 8. Secrets and data minimization

Writers SHOULD use secret references instead of values:

```json
{
  "secret_ref": "secret://deployment/github-client-secret",
  "provider_hint": "organization-secret-store",
  "required_for": ["task:deploy"]
}
```

A reference does not authorize resolution. Exporters MUST apply their configured secret and data-loss-prevention policy to included event payloads, execution output, evidence, generated views, module data, and artifact paths. Scan status is `passed`, `findings`, `not_run`, or `unknown`. Passing is evidence of a check, not proof of absence.

Writers SHOULD omit irrelevant transcripts and personal data and support classification, audience, retention, and jurisdiction metadata. Omission must not be disguised by a stronger completeness claim.

## 9. Physical redaction lineage

Physical redaction creates a new workstate history lineage. It MUST:

- receive a new package or representation digest;
- identify the source workstate and source frontier where safe;
- declare that history was rewritten;
- state policy or reason where safe;
- replace removed records with non-sensitive tombstones when references remain;
- invalidate signatures covering removed bytes;
- remove sensitive values from views, indexes, paths, caches, and module data;
- avoid claiming byte-complete continuity.

Artifact tombstones follow AWP Artifact. Physical redaction is not ordinary semantic deletion.

## 10. Signatures and trust

Signatures may cover individual events, frontier manifests, snapshots, artifact manifests, module data, or complete packages. Signature metadata MUST identify algorithm, key identifier, coverage, canonicalization profile, signer, and verification status.

Trust dimensions remain independent:

- byte integrity;
- actor authentication;
- action authorization;
- evidentiary strength;
- processing safety.

A valid signature proves none of the other dimensions by itself.

AWP Security 0.4.0 does not select a normative canonicalization or signature algorithm. Implementations MUST NOT claim interoperable AWP signature conformance without naming an external or future registered signature profile.

## 11. Encryption

Encryption metadata may describe package-wide, module-level, artifact-level, or recipient-based protection. It MUST identify the encryption profile and protected scope without exposing keys or secret values.

Encryption does not replace minimal disclosure. Metadata remaining in plaintext, including paths, sizes, module names, actors, and timing, may itself be sensitive.

This version does not define a normative encryption profile.

## 12. Package and artifact safety

When Capsule or Artifact is used, processors MUST apply their traversal, normalization, size, decompression, integrity, executable-content, and retrieval rules. A signature over an unsafe archive does not make extraction safe.

## 13. Conformance

A Security reader evaluates and surfaces declared metadata without converting it into trust, validates registered security profiles it claims to support, and enforces receiver policy.

A Security writer minimizes sensitive data, reports scan and redaction state accurately, scopes signatures precisely, and never embeds credentials in locations or retrieval metadata.
