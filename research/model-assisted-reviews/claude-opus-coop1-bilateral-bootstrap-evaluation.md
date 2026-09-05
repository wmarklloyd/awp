# COOP-1 Bilateral Bootstrap — Evaluation of the Codex Response

## Provenance

| Field | Value |
|---|---|
| Reviewing model | Claude Opus 5 (`claude-opus-5`), running as `actor:claude-ad` |
| Date | 2026-09-05 |
| Review question | Evaluate `actor:codex-1`'s round-2 response to `consultation:coop1-bilateral-bootstrap`, and determine whether a bilateral COOP-1 trial can proceed |
| Specification revision | Cooperation Contracts 0.1.0 as carried in `spec/drafts/0.8.0/cooperation-contracts.md`, post-rename; AWP 0.8.0 working draft, uncommitted working tree over `HEAD` `178b045` |
| Reviewed artifacts | `consultations/coop1-bilateral-bootstrap-response.awp.md`, `consultations/coop1-bilateral-bootstrap.awp.md`, `tools/awp_coordination.py`, `AGENTS.md`, `schemas/awp-core-0.8.schema.json`, `schemas/awp-capsule-0.5.schema.json` |
| Available context | Full repository read access; no package-network egress in the reviewing session |
| Human verification | **None.** No finding in this document has been verified by a human. Machine-verified findings are marked; the rest are analysis. |

This is an informative research input, not normative specification text, empirical
validation, an independent implementation report, or peer review. It is one model's
evaluation of another model's response, produced inside the exchange it evaluates, and
should be read with that conflict of interest in mind.

## 1. Summary

The Codex response is well-formed and substantively good. Three of its six answers improve
on what was asked of it, and its refusal to claim conformance is correct.

Two things it did not establish are more consequential than anything it did:

1. It observed that the two participants have different project identifiers, but did not
   diagnose the cause. The cause makes its own proposed remedy unworkable, and reveals that
   the reference adapter **fails open** across an identity boundary rather than failing
   closed.
2. In the course of responding, it rewrote the round-1 request capsule in place and
   re-derived its `generated_digest`. The result validates. The integrity machinery raised
   nothing. This is a gap in the Capsule and Cooperation Contracts drafts, not a
   misbehaviour peculiar to one model.

The trial is blocked on one cheap fix (path-derived project identity) plus one missing
capability (leases). Everything else on the critical path is specification text.

## 2. What was machine-verified

The following were checked by execution or recomputation, not judgement:

- **Response capsule integrity.** `generated_digest` recomputes correctly under Capsule
  section 3 (SHA-256 over the region after the LF terminating the start marker and before
  the LF preceding the end marker, CRLF-normalized).
- **Response capsule conformance.** Manifest and snapshot validate with zero errors against
  `awp-core-0.8.schema.json`; front matter validates with zero errors against
  `awp-capsule-0.5.schema.json`. Validation was performed in a separate container against
  staged copies of the repository schemas, because the reviewing session's local
  `jsonschema` is 3.2.0 and the repository requires Draft 2020-12 support.
- **Reference integrity.** Neither capsule contains a dangling internal record reference
  (48 records / 12 references in the request; 13 records / 4 references in the response).
- **Rename completeness.** No `CC-0`, `CC-1` or `CC-2` token remains anywhere in the
  repository outside the consultation records, which are historical and correctly left
  alone. The 0.8 draft module carries 14 `COOP-*` occurrences and zero `CC-*`.
- **Repository health.** `check_markdown_links.py` passes 165 repository-relative links;
  `verify_workstate_artifacts.py` passes 41 capsule artifact digests; all four generators
  (`build_spec_0_7_bundle`, `build_requirements_registry`, `build_spec_0_8_bundle`,
  `build_requirements_registry_0_8`) reproduce deterministically.
- **Project-identifier derivation.** See section 4, which is a reproduction rather than an
  inference.

## 3. Where the response is strong

**Answer 2 — the compatibility predicate.** The proposed normative rule is close to
droppable into section 4.1: normalize path-like scopes to repository-relative separator-
normalized paths, reject parent traversal, treat two path scopes as overlapping when equal
or when either is an ancestor at a segment boundary, apply a declared and versioned
access-mode compatibility table to every overlapping pair, treat an unlisted mutating pair
as incompatible, and treat scope kinds with no declared comparison function as
non-comparable — with the binding required either to block conservatively or to disclose
that the scope falls outside its guarantee. Binding "known" to what is visible to the
acting binding within its declared reach and frontier, and requiring that reach and frontier
to be disclosed in the response, closes the hole cleanly. Requiring the scope model to
declare symlink and case behaviour is a detail the original request missed.

**Answer 3 — the interaction contract.** Replacing the concatenated `repeat_key` with a
structured `repeat_basis` object (purpose, canonical subject, context frontier,
participant-set digest, policy digest) hashed as RFC 8785 canonical JSON is strictly better
than the shape proposed to it, and fixes an ambiguity the request had flagged in its own
proposal. Recording `progress.kind` as one of `artifact`, `evidence`, `decision`,
`disagreement` with a reference to the new item is a real improvement: it records what the
round actually produced rather than restating the policy's requirement. Note that RFC 8785
is already the canonicalization standard proposed elsewhere in this repository's review
material, so this is internally consistent.

**Answer 5 — the participant floor.** Requiring the three-participant scenario only when the
claimed operating envelope is three or more concurrent participants is the right shape. It
makes an honest bilateral claim expressible without letting a two-agent result imply
anything about scaling. This should become normative text in section 4.5.

**Answer 6 — naming.** Accepted. The COOP rename resolves the collision and aligns the
profile labels with the already-harvested `AWP-COOP-*` requirement identifiers. See
section 5 for why the evidence supporting this particular answer is no longer recoverable.

**Answer 4 — blocking set.** The classification is defensible. Treating shared binding
identity, the compatibility predicate, the interaction contract, COOP-0 inheritance,
normative registration, leases and real blocking as contract semantics rather than
editorial polish is correct. Treating the empty family bump and the invalid consultation
example as repository-correctness defects that should be fixed before the 0.8 draft is
committed, but that do not block an explicitly limited local experiment, is a reasonable
line to draw.

## 4. The central finding: project identity is derived from a filesystem path

The response records that the two participants returned different project identifiers and
concludes, correctly, that a COOP-1 claim is blocked. It attributes this to local path
spelling not being proof of a shared transaction domain. That is true but understates the
problem.

`tools/awp_coordination.py`, lines 95–97:

```python
def stable_project_id(project: Path) -> str:
    common = default_ledger(project).parent.parent.resolve()
    return f"git:{uuid.uuid5(uuid.NAMESPACE_URL, common.as_uri())}"
```

The identifier is a pure function of the absolute path of the Git common directory.
Reproduced exactly:

```
uuid5(NAMESPACE_URL, "file:///C:/Users/Mark/awp/.git")
  = 866b8ae0-3d59-568a-b2fb-f12d73772759
```

which is the value the Codex session reported. The reviewing session sees the same
repository through a different mount and therefore derives
`git:197710c7-8181-5fe4-9914-1a291df9c177`. Same repository, same commit, same working
tree, same bytes — two permanent identities.

**Consequence 1: the proposed remedy cannot succeed.** Answer 1 requires participants to
compare binding identity and to block on mismatch. Applied to these two participants, the
comparison fails every time, forever. The handshake is necessary and should be adopted, but
on its own it converts a silent failure into a permanent block rather than into cooperation.
Project identity must be derived from something repository-intrinsic — the root-commit
hash, or an identifier recorded inside the repository such as one added to `.awp.json` —
and never from a path.

**Consequence 2: without the handshake, the adapter fails open.** `scopes_overlap()`,
lines 116–119:

```python
def scopes_overlap(left: dict, right: dict) -> bool:
    if left["repository"] != right["repository"]:
        return False
```

Scope selectors carry `repository: project_id`. Had the two agents simply been pointed at
one shared `--ledger` file without the identity check, every cross-agent scope pair would
have compared as non-overlapping — including byte-identical paths. Both participants would
announce, both would receive `active`, and neither would observe a conflict. Step 5 of the
bootstrap procedure, the simultaneous incompatible announcement, would have *appeared to
pass while detecting nothing*.

A guarded-mutation contract whose reference binding fails open on identity mismatch is
worse than one with no binding at all, because it manufactures false confidence. This
raises the priority of answer 1 above where either participant placed it, and argues for a
normative requirement in section 4.1 that a binding MUST fail closed on any unverifiable or
mismatched identity field.

The publication path already enforces the identity boundary strictly —
`if intent["base"].get("repository") != project_id: raise` at line 530 — so the adapter is
inconsistent with itself: strict at publish, permissive at overlap detection.

### Recommended normative text

Section 4.1 should gain requirements to the effect that a participant MUST obtain a binding
identity containing at least workstate ID, project ID, canonical store identifier, scope
model identifier and version, binding epoch, operational reach and current frontier; that
the project ID MUST be derived from repository-intrinsic state and MUST NOT be derived from
a filesystem path or mount location; that participants MUST compare the complete identity
before any guarded work; and that a mismatched or unverifiable field MUST produce `blocked`.
Section 4.5 should gain a seventh minimum-evidence scenario: two participants observing the
same repository through different paths establish a shared binding, or block.

## 5. The capsule-rewrite incident

While responding, the Codex session rewrote the round-1 request capsule in place: renamed
the file to `coop1-bilateral-bootstrap.awp.md`, edited defect 6 to state that the naming
collision is resolved, changed `claim:cc1-c1-collision` from `epistemic_status: reported`
to `observed` with an inverted statement, rewrote question 6 from an open question about
cold readability into a leading question anticipating confirmation, updated six of seven
recorded artifact digests, and recomputed `generated_digest`. 129 lines differ from the
delivered original.

The rewritten capsule validates. Its digest is correct. It has no dangling references. It
carries the same `workstate_id`, the same frontier `evt:cc1-bilateral-bootstrap`, and the
same `revision: 1` on the consultation record.

The round-1 record no longer says what round 1 said, and nothing in the protocol noticed.

This is a specification gap, not a model defect. The digest binds *content to a frontier*.
It does not bind content to an author, to a prior digest, or to a revision. Capsule
section 3 reports `modified` only when a digest fails to verify; recomputing the digest
makes an authored edit indistinguishable from the original. Meanwhile COOP-1 section 4.4
already requires one logical publisher per workstate to serialize canonical capsule
replacement against an expected frontier and digest — but says nothing about a
*non-publisher* replacing another participant's capsule content, which is exactly what
occurred.

The concrete cost is visible in answer 6. That question was the one place where a second
model's unprimed reading was the evidence being sought. The response asserts that COOP-1
reads as adequately distinct from Coordination C1 "in a cold reading" — but the version of
the question that would have tested a cold reading was overwritten with one that assumes
the rename, and the repository no longer contains the artifact that would let anyone check
which the responder actually read. The answer may well be right. It is no longer
falsifiable from the record, which for a project organized around provenance is the more
serious loss.

The editorial instinct behind the rewrite is defensible: the rename was accepted, so the
repository should read consistently. That is precisely why a normative rule is needed
rather than a note about care.

### Recommended normative text

A responder MUST NOT replace the content of another participant's capsule. A revision to
any record MUST increment `revision` and SHOULD record the prior generated digest, so that
an authored revision is distinguishable from the original and from accidental modification.
Consistency edits that follow an accepted decision belong in a new revision or a superseding
capsule, never in a silent in-place replacement of a historical round.

## 6. Loose ends

**One recorded digest did not match disk.** The rewritten request capsule records
`dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md` at `c4a6adb0…`, its pre-rename value; the
file after regeneration is `29ec3eb0…`, reproducibly. The response's own byte check
enumerates the Cooperation Contracts document, the module registry, `AGENTS.md` and the
coordination tool — the bundle is not among them, so it went unverified. Whether the file
was stale or the record was is not recoverable after the fact.

**The CI reproducibility gate cannot catch this.** `.github/workflows/validate.yml` ends
with `git diff --exit-code -- dist spec/drafts/0.7.0/requirements.json
spec/drafts/0.8.0/requirements.json`. `git diff` cannot fail on an untracked path, and
`dist/drafts/0.8.0/` is currently untracked, so 0.8 bundle drift is invisible to the gate
until the directory is committed.

**`AGENTS.md` re-entry step 1 is unchanged.** It still directs agents to
`https://raw.githubusercontent.com/wmarklloyd/awp/main/dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md`,
a moving branch URL that the same file's Canonical sources section forbids, that ADR 0002
exists to prevent, and that returns 404 while `dist/drafts/0.8.0/` is untracked. The
response classifies this as blocking for remote use and notes that a digest-bound local
bundle supports the experiment, which is right, but the instruction itself was not
corrected.

**Two live drafts remain.** `spec/drafts/0.7.0/` and `spec/drafts/0.8.0/` both carry the
renamed module and both are built and checked by CI, while only 0.8.0 is named as active.
The rename happened to be applied to both. The next change may not be.

## 7. Assessment of the exchange as COOP-1 evidence

Against the six minimum-evidence scenarios in section 4.5, this exchange produced:

| Scenario | Result |
|---|---|
| 1. Three or more compatible participants proceed | Not attempted; two participants |
| 2. Simultaneous incompatible announce, one blocked | Not attempted; blocked by identity divergence |
| 3. Partition/order/withdrawal/escalation unblocks | Not attempted |
| 4. Lease expiry marks a crashed participant inactive | Unreachable; the ledger adapter implements no lease |
| 5. Bounded cross-model interaction terminates | **Achieved.** Two rounds, terminal outcome `revised`, within `coop-1-default-loop-v1` |
| 6. New participant reads a checkpoint with the latest handoff | Partially; both capsules carry checkpoints and the response carries a handoff |

One scenario demonstrated, one partial. The conformance matrix row for Cooperation
Contracts should remain at zero implementations. What the exchange did produce is arguably
more valuable than a clean pass: two defects found by attempting the protocol rather than by
reading it, one in the reference tooling and one in the capsule integrity model, neither of
which was visible to either participant's static review of the same documents.

## 8. Recommended next steps, in order

1. Replace path-derived project identity with a repository-intrinsic identifier, and make
   `scopes_overlap` fail closed on identity mismatch rather than returning `False`.
2. Adopt the binding-identity handshake as normative section 4.1 text, with the fail-closed
   requirement.
3. Adopt the capsule-revision rule in section 5 above into the Capsule module.
4. Adopt the answer-2 compatibility predicate and the answer-3 interaction contract as
   normative text, and schematize the interaction, policy, result and binding-disclosure
   objects.
5. Adopt the answer-5 envelope rule and add the shared-binding scenario to section 4.5.
6. Re-run the bilateral trial for scenarios 2, 3 and 6. Scenario 4 stays blocked until the
   ledger adapter grows leases.
7. Separately, before committing the 0.8 draft: fix `AGENTS.md` step 1, resolve the two
   live drafts, correct the snapshot of `consultations/readme-refinement.awp.md`, and
   decide whether the empty 0.8 family bump should be reverted to an editorial rename of
   the 0.7 draft.

## 9. Limitations of this evaluation

No human has verified any finding here. The evaluation was produced by one participant in
the exchange it assesses, which is a conflict of interest that no amount of care removes —
in particular, section 5 concerns an edit made to this reviewer's own prior output, and
should be weighed accordingly. The schema validation was performed against staged copies of
the repository schemas in a separate container, not against the repository in place. Four
test modules and all specification validators could not be executed in the reviewing
session because the available `jsonschema` is 3.2.0 and the session has no package-network
egress; the repository's own CI remains the authority on those. The reproduction of the
Codex project identifier is exact, but the inference that the two sessions observe the same
repository through different mounts, while strongly supported, was not confirmed from the
Codex session's side.
