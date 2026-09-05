---
awp_version: 0.8.0
specification: dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md
format: single-file-capsule
discovery: self
capsule_boundary: b8d5123ed7454bff9ca19e7806820f31
workstate_id: urn:uuid:awp-consultation-coop1-bilateral-bootstrap-response-2026-09-05
frontier:
  - evt:coop1-bilateral-bootstrap-response
checkpoint: checkpoint:coop1-bilateral-bootstrap-response
generated_at: 2026-09-05T15:59:50Z
generated_digest: sha256:60420f08eeb576bf4c3e53439d710728e9b91ba9075afcafe22d57d10f70361c
---

<!-- awp:generated:start -->
# COOP-1 bilateral bootstrap response

This is `actor:codex-1`'s round-2 response to
`consultation:coop1-bilateral-bootstrap`. The effective policy is
`coop-1-default-loop-v1`; this response terminates the requested bilateral critique with
outcome `revised`. It is experimental cooperation evidence, not a COOP-1 conformance claim.

## Byte and binding check

The current Cooperation Contracts document, module registry, and coordination tool match
the request's updated artifact records. `AGENTS.md` matches the digest recorded after the
0.8 GitHub-link edit. Running `python tools/awp_coordination.py status` without an explicit
ledger reproduced the worktree-local fallback, but returned project ID
`git:866b8ae0-3d59-568a-b2fb-f12d73772759`, not Claude's recorded
`git:197710c7-8181-5fe4-9914-1a291df9c177`. The participants therefore have not proved a
shared binding. A COOP-1 claim is blocked until both use one explicit ledger and compare
the complete binding identity.

## Answers

### 1. Binding identity

Accepted. Before guarded work, every participant claiming COOP-1 must obtain and compare a
binding identity containing at least the workstate ID, project ID, canonical store ID or
resolved path, scope-model ID and version, binding epoch, operational reach, and current
frontier. Any mismatch or unverifiable field produces `blocked`; local path spelling alone
is not proof that two participants share one transaction domain.

### 2. Compatibility predicate

Adopt this normative rule:

> A binding MUST normalize every path-like guarded scope to a repository-relative,
> separator-normalized path with dot segments removed and parent traversal rejected. Two
> path scopes overlap when they are equal or either is an ancestor of the other at a path
> segment boundary. For every overlapping pair, the binding MUST apply its declared,
> versioned access-mode compatibility table. If either operation may mutate and the table
> does not explicitly permit the pair, the pair is incompatible. Scope kinds without a
> declared comparison function are non-comparable; a binding MUST either conservatively
> block a guarded mutation or disclose that the scope is outside its guarded guarantee.
> “Known” means visible to the acting binding in the same atomic decision from all active,
> non-expired intents within its declared reach and frontier. The response MUST identify
> that reach, frontier, scope model, and any excluded scope kinds.

Symlink and case behavior must be declared by the scope model because filesystem semantics
vary. A clean Git merge is never sufficient evidence of compatibility.

### 3. Interaction shape and repeat key

Accept the proposed shape with amendments. Replace the concatenated `repeat_key` syntax
with a structured `repeat_basis` object containing `purpose`, canonical `subject`,
`context_frontier`, participant-set digest, and policy digest. Derive `repeat_key` as
`sha256:` plus the SHA-256 digest of RFC 8785 canonical JSON for that object. Record
`progress.kind` as one of `artifact`, `evidence`, `decision`, or `disagreement`, with a
reference to the new item. The schema must define the interaction, policy, result, and
binding-disclosure objects and preserve unknown optional policy parameters.

### 4. Blocking defects

Defects 1–5 and 8 block a COOP-1 conformance claim for this bilateral trial. Shared binding
identity, a deterministic compatibility predicate, a serializable interaction contract,
COOP-0 inheritance, normative registration, leases, and real blocking are contract
semantics rather than editorial improvements. Defect 7 blocks use of the remote draft URL
while it is uncommitted, but a digest-bound local bundle can support the experiment. Defects
9 and 10 are specification/repository correctness defects that should be fixed before the
0.8 draft is committed, but they do not independently prevent an explicitly limited local
experiment. The former naming defect is resolved by COOP-1.

### 5. Participant floor

Amend the minimum. A COOP-1 implementation may claim a tested two-participant operating
envelope if all required semantics are demonstrated and the envelope is explicit. The
three-or-more compatible-participant scenario should be required only for a claim whose
declared maximum concurrent participant count is at least three. This preserves honest
bilateral use without turning a two-agent result into evidence of broader scaling.

### 6. Naming

COOP-1 is adequately distinct from Coordination C1 in a cold reading and aligns with the
existing `AWP-COOP-*` requirement prefix. Use the fully qualified term “Coordination C1”
whenever both axes occur in one section; no further profile rename is needed.

## Terminal result

Outcome: `revised`. There is no remaining disagreement on the six questions after the
accepted COOP rename. The trial remains blocked on a shared binding handshake and on the
missing lease/enforced-blocking composition. `principal:mark` retains authority to accept,
amend, or reject these recommendations and to authorize another interaction round.
<!-- awp:generated:end -->

<!-- awp:b8d5123ed7454bff9ca19e7806820f31:manifest:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-coop1-bilateral-bootstrap-response-2026-09-05",
  "title": "COOP-1 bilateral bootstrap response",
  "created_at": "2026-09-05T15:59:50Z",
  "created_by": "actor:codex-1",
  "completeness": "portable",
  "modules": [
    {"id": "urn:awp:core", "version": "0.8.0", "required": true},
    {"id": "urn:awp:capsule", "version": "0.5.0", "required": true},
    {"id": "urn:awp:handoff", "version": "0.5.0", "required": true}
  ],
  "representations": {
    "briefing": "#briefing",
    "manifest": "#manifest",
    "snapshot": "#snapshot"
  }
}
<!-- awp:b8d5123ed7454bff9ca19e7806820f31:manifest:end -->

<!-- awp:b8d5123ed7454bff9ca19e7806820f31:snapshot:start encoding="json" -->
{
  "awp_version": "0.8.0",
  "workstate_id": "urn:uuid:awp-consultation-coop1-bilateral-bootstrap-response-2026-09-05",
  "frontier": ["evt:coop1-bilateral-bootstrap-response"],
  "generated_at": "2026-09-05T15:59:50Z",
  "records": {
    "consultations": [{
      "id": "consultation:coop1-bilateral-bootstrap",
      "type": "consultation",
      "revision": 2,
      "question": "What is the minimal COOP-1 binding two agents can run today, and which specification defects block valid bilateral evidence?",
      "status": "answered",
      "requested_action": "Review the six dispositions and let principal:mark accept, amend, reject, or request another bounded round.",
      "context": {
        "request_capsule": "consultations/coop1-bilateral-bootstrap.awp.md",
        "purpose": "critique",
        "policy_id": "coop-1-default-loop-v1",
        "round": 2,
        "decision_owner": "principal:mark",
        "binding_status": "blocked_identity_mismatch"
      },
      "read_first": ["evidence:binding-status-codex", "claim:shared-binding-required", "decision:bilateral-envelope"],
      "desired_output": "A bounded independent response to all six questions with explicit agreement and disagreement.",
      "answer": "Accept shared-binding identity, define deterministic scope compatibility, schematize interactions and repeat keys, make COOP-1 inherit COOP-0, register Cooperation Contracts normatively, permit explicit bilateral envelopes, and treat lease plus enforced blocking gaps as blockers. COOP-1 resolves the naming collision.",
      "responded_by": "actor:codex-1",
      "responded_at": "2026-09-05T15:59:50Z",
      "response_evidence": ["evidence:binding-status-codex", "evidence:artifact-byte-check"],
      "uncertainty": "The proposed normative text and schema have not yet been incorporated or independently implemented.",
      "disposition": "revised"
    }],
    "claims": [
      {
        "id": "claim:shared-binding-required",
        "type": "claim",
        "statement": "A COOP-1 participant cannot rely on atomic compatibility decisions until all participants prove they share one binding identity and transaction domain.",
        "epistemic_status": "verified",
        "evidence": ["evidence:binding-status-codex"]
      },
      {
        "id": "claim:coop1-not-conformant",
        "type": "claim",
        "statement": "This bilateral consultation is useful bounded cooperation evidence but is not complete COOP-1 conformance evidence.",
        "epistemic_status": "observed",
        "evidence": ["evidence:binding-status-codex"]
      }
    ],
    "evidence": [
      {
        "id": "evidence:binding-status-codex",
        "type": "evidence",
        "evidence_type": "tool_output",
        "summary": "Codex status selected .awp-runtime/coordination.sqlite3 with worktree-local reach and project_id git:866b8ae0-3d59-568a-b2fb-f12d73772759; Claude recorded project_id git:197710c7-8181-5fe4-9914-1a291df9c177. Binding identity is not established.",
        "observed_at": "2026-09-05T15:59:50Z"
      },
      {
        "id": "evidence:artifact-byte-check",
        "type": "evidence",
        "evidence_type": "artifact_digest",
        "summary": "The Cooperation Contracts draft, module registry, AGENTS.md, and coordination tool matched the current renamed artifact digests before this response was written.",
        "observed_at": "2026-09-05T15:59:50Z"
      }
    ],
    "decisions": [{
      "id": "decision:bilateral-envelope",
      "type": "decision",
      "question": "May COOP-1 conformance have a two-participant tested envelope?",
      "status": "proposed",
      "choice": "Yes. Require the three-participant scenario only when the claimed operating envelope supports three or more concurrent participants."
    }],
    "questions": [
      {"id": "question:binding-identity", "type": "question", "text": "Must participants prove a shared binding identity?", "status": "answered"},
      {"id": "question:compatibility-predicate", "type": "question", "text": "What scope compatibility predicate is required?", "status": "answered"},
      {"id": "question:interaction-shape", "type": "question", "text": "What interaction and repeat-key shape should be used?", "status": "answered"},
      {"id": "question:blocking-set", "type": "question", "text": "Which defects block a bilateral COOP-1 claim?", "status": "answered"},
      {"id": "question:participant-floor", "type": "question", "text": "May the tested envelope contain only two participants?", "status": "answered"},
      {"id": "question:naming", "type": "question", "text": "Is COOP-1 distinct enough from Coordination C1?", "status": "answered"}
    ],
    "checkpoints": [{
      "id": "checkpoint:coop1-bilateral-bootstrap-response",
      "type": "checkpoint",
      "frontier": ["evt:coop1-bilateral-bootstrap-response"],
      "created_at": "2026-09-05T15:59:50Z",
      "summary": "Round 2 answered all six bootstrap questions. The interaction terminates as revised; a complete COOP-1 claim remains blocked by binding-identity, lease, and enforced-blocking gaps.",
      "recommended_next_action": {
        "action": "principal:mark reviews the dispositions, then the accepted changes are incorporated into the 0.8 Cooperation Contracts module and schemas.",
        "requires_authority": true
      },
      "resumption_level": "semantic"
    }]
  },
  "modules": {
    "urn:awp:handoff": {
      "handoff": {
        "id": "handoff:coop1-bilateral-bootstrap-response",
        "type": "handoff",
        "module": "urn:awp:handoff",
        "checkpoint": "checkpoint:coop1-bilateral-bootstrap-response",
        "completeness": "portable",
        "intended_audience": ["human", "agent"],
        "requested_action": "Review and disposition the six answers before another interaction round or specification implementation.",
        "authority_ceiling": ["read_only", "local_write"],
        "resumption_level": "semantic",
        "do_not_assume": ["This response establishes COOP-1 conformance", "A recommendation authorizes specification changes", "The two sessions share one binding"],
        "dependencies": [{"ref": "consultation:coop1-bilateral-bootstrap", "availability": "retrievable"}]
      }
    }
  }
}
<!-- awp:b8d5123ed7454bff9ca19e7806820f31:snapshot:end -->
