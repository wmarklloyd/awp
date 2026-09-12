# AWP Handoff 0.5.0

**Module ID:** `urn:awp:handoff`  
**Status:** Optional  
**Depends on:** AWP Core `0.8.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

AWP Handoff defines checkpoints optimized for transfer to another actor. It standardizes completeness, resumption guarantees, continuation instructions, dependency disclosure, and authority ceilings. It is independent of physical packaging; a handoff may travel in a Capsule representation, API payload, repository, or another binding.

A workstate containing a handoff record MUST declare this module. It MUST mark the module required when the requested continuation depends on the record's completeness, dependency, resumption, or authority-ceiling semantics.

## 2. Completeness

A handoff declares one completeness level:

- `summary`: orientation and checkpoint only; missing machine state is expected;
- `portable`: all semantic state, evidence, module data, and artifacts or stable references required for the requested continuation;
- `full`: portable content plus the complete declared event history and every transcript, tool output, and runtime extension the manifest claims to include.

`portable` is RECOMMENDED for cross-system continuation. A portable handoff MUST identify each required dependency as `available`, `retrievable`, `unavailable`, or `withheld`. A full handoff MUST enumerate omissions and MUST NOT imply that an entire repository, transcript, or runtime is present when it is not.

Completeness describes included material, not truth, trust, authorization, or fitness for a particular receiver.

## 3. Resumption levels

A checkpoint declares its strongest supported level:

- `semantic`: a capable human or different model can understand and continue using portable state;
- `operational`: a compatible agent can additionally restore tool context, pending actions, environment references, and workflow position;
- `exact`: the identified originating runtime claims it can restore a private checkpoint.

Levels are cumulative. `operational` MUST satisfy every semantic requirement. `exact` MUST satisfy semantic and operational requirements unless explicitly labeled `private_nonportable`, in which case it is not a conforming portable handoff.

Semantic resumption requires:

- active goals and success criteria;
- current status;
- applicable constraints and authority boundaries;
- material claims, uncertainty, and evidence;
- accepted decisions and rejected alternatives relevant to continuation;
- open tasks and questions;
- open consultations and the portable context required to answer them;
- required artifact references and availability;
- recommended next action.

Operational resumption additionally identifies tools, environments, workflow position, pending operations, and unavailable external dependencies. Exact resumption identifies the runtime, runtime version, checkpoint format, integrity data, and compatibility constraints. No level guarantees deterministic model output.

## 4. Handoff record

```json
{
  "id": "handoff:agent-b",
  "type": "handoff",
  "module": "urn:awp:handoff",
  "checkpoint": "checkpoint:release-ready",
  "completeness": "portable",
  "intended_audience": ["agent", "human"],
  "read_first": [
    "goal:launch",
    "constraint:no-schema-change",
    "decision:database",
    "task:deploy"
  ],
  "do_not_assume": [
    "Production approval has been granted",
    "Referenced credentials are available"
  ],
  "dependencies": [
    {
      "ref": "artifact:source-tree-91ab",
      "availability": "available"
    },
    {
      "ref": "environment:staging",
      "availability": "unavailable",
      "reason": "Receiver-specific deployment access is required."
    }
  ],
  "requested_action": "Continue release preparation without deploying.",
  "authority_ceiling": ["read_only", "local_write"],
  "resumption_level": "semantic"
}
```

Required fields are `id`, `type`, `module`, `checkpoint`, `completeness`, `intended_audience`, `requested_action`, `authority_ceiling`, and `resumption_level`. `module` MUST be `urn:awp:handoff`.

`authority_ceiling` is an upper bound asserted by the sender. It does not grant those authorities; the receiver may operate under a stricter ceiling. A missing, unknown, or ambiguous ceiling MUST be treated as no authority for external side effects.

## 5. Resume Profile

The Resume Profile standardizes project re-entry after an actor or runtime leaves and later returns, or when a new actor starts without the source conversation. It uses a module-owned `resume` record and the capability name `resume-profile`.

```json
{
  "id": "resume:project-current",
  "type": "resume",
  "module": "urn:awp:handoff",
  "handoff": "handoff:agent-b",
  "checkpoint": "checkpoint:release-ready",
  "mode": "project_reentry",
  "read_first": [
    "goal:launch",
    "constraint:no-schema-change",
    "decision:database",
    "task:deploy"
  ],
  "required_artifacts": ["artifact:source-tree-91ab"],
  "state_bindings": [
    {
      "state_space": "repo:application",
      "revision": "git:91ab4e7",
      "profile": "git-state-v1",
      "scope": ["src/", "tests/"]
    }
  ],
  "recommended_next_action": "Continue release preparation without deploying.",
  "freshness_policy": "verify_before_continue",
  "on_stale": "refresh_workstate",
  "authority_ceiling": ["read_only", "local_write"]
}
```

Required fields are `id`, `type`, `module`, `checkpoint`, `mode`, `read_first`, `required_artifacts`, `recommended_next_action`, `freshness_policy`, `on_stale`, and `authority_ceiling`. `type` MUST be `resume`, `module` MUST be `urn:awp:handoff`, and the only standard mode in this version is `project_reentry`. Optional `handoff` identifies the handoff record this resume record refines.

When both a Resume and referenced Handoff record are present, the Resume record is the project-entry instruction for the named checkpoint. Its `authority_ceiling` MUST be equal to or narrower than the Handoff ceiling, and its action MUST be a compatible refinement of the Handoff requested action. A receiver that cannot establish those conditions MUST qualify or reject the resume; it MUST NOT choose one record silently.

`freshness_policy` is one of:

- `verify_before_continue`: validate the selected checkpoint, frontier, briefing digest, required modules, and required artifacts before performing the recommended action;
- `allow_stale_orientation`: stale state may be used only for orientation while the receiver refreshes or verifies it;
- `receiver_policy`: defer the minimum freshness requirement to an identified receiver policy.

`on_stale` is `refresh_workstate`, `report_and_stop`, or `read_only_orientation`. A receiver MUST NOT interpret any value as permission to perform an external side effect from stale or unverifiable state.

`state_bindings`, when present, bind a resume checkpoint to the state spaces and immutable revisions against which it was prepared. Each entry requires `state_space` and `revision` and MAY identify an adapter `profile` and narrower `scope`. A `project_reentry` record that depends on external or source-controlled work products MUST include each state binding required to assess safe continuation. A Git repository and source revision are one possible binding; they are not required for non-code work products.

A receiver that can identify the local state-space revision MUST compare it with `revision`. A mismatch makes the binding stale. When it can obtain a difference, claims, evidence, change sets, and verification results scoped to changed objects MUST be treated as stale until reverified or explicitly re-scoped. When the receiver cannot identify or compare the state-space revision, the binding is unverifiable rather than current. A matching revision does not establish that remote services, credentials, or other dependencies remain current.

`read_first` is an ordered presentation hint, not causal ordering or authority. A receiver MAY load additional records required to interpret dependencies, evidence, conflicts, or safety constraints. It MUST NOT omit relevant required state merely to meet a context budget. Optional context-selection metadata MAY state a token or byte budget, priority groups, and deferred artifacts, but it cannot weaken completeness, freshness, or authority requirements.

For task-scoped re-entry, `decision_context` is an orthogonal result with values `complete`, `partial`, `conflicting`, `stale`, or `unverifiable`. Handoff `completeness` describes the declared transfer; `decision_context` describes whether the applicable Core decision closure was selected, its lineage closed, and required sources verified. A `portable` or `full` Handoff MUST NOT be interpreted as decision-context complete merely because its `read_first` list names some decisions. Resume and Handoff producers SHOULD identify affected records, artifacts, concepts, and physical scopes sufficiently for closure selection; ambiguity requires conservative inclusion or a non-complete decision-context result.

A receiver MAY implement the Capsule briefing-first presentation profile `selective-reentry-v1`. That profile reads and validates the complete source representation in the host, but returns a bounded participant-facing projection containing:

- source identity, byte size, and Capsule integrity state;
- the generated briefing and governing metadata;
- the active Resume, its referenced Handoff and checkpoint;
- the ordered `read_first` records;
- the bounded explicit decision closure and its independent `decision_context` result; and
- compact location, availability, and integrity descriptors for `required_artifacts`.

The projection MUST include a structural selection status of `complete`, `incomplete`, or `budget_exceeded`, an independent `decision_context` result, every missing record identifier, and every required artifact or decision source that could not be verified. Structural `complete` means that the Capsule integrity is current, the complete author-declared Resume selection is present, and each required local artifact with supported integrity metadata is current. It does not establish Decision Durability. `brief_only` is an explicitly incomplete orientation mode. A receiver MUST NOT call either axis complete when it omitted required entry or decision records to satisfy a budget, and a participant MUST NOT begin guarded work unless both axes are complete or the decision owner records a bounded continuation.

A host MAY expose a canonical Capsule checkpoint operation. A model-facing checkpoint request supplies semantic content such as the proposed frontier, checkpoint, concise briefing fields, unresolved work, evidence references, and recommended next action. The host supplies whole-Capsule and generated-region digests, performs serialization and artifact verification, and returns a receipt or a recoverable stale or pending result. `mode: no_change` confirms that the current Capsule was checked without rewriting it.

A Resume Profile receiver MUST:

1. discover or receive the workstate location;
2. validate the manifest, Core, and every required module;
3. locate the resume record and referenced checkpoint;
4. classify the checkpoint, snapshot, briefing, and required artifacts as current, stale, divergent, unavailable, or unverifiable using applicable modules;
5. apply `freshness_policy` and `on_stale` without weakening receiver policy;
6. load `read_first` records plus every dependency necessary for safe interpretation;
7. compare the recommended action and authority ceiling with current local authority;
8. report acceptance, qualified acceptance, or rejection before continuation.

The Resume Profile does not require a command-line interface. Commands such as `awp resume`, `awp status`, and `awp checkpoint` are informative implementation examples.

## 6. Producer procedure

A Handoff writer MUST:

1. create or select a checkpoint at the intended frontier;
2. identify the audience and requested continuation;
3. include the Core state required for semantic resumption;
4. declare every module needed to interpret the continuation as required;
5. include, reference, or mark unavailable every required dependency;
6. minimize personal data, secrets, and irrelevant transcript content;
7. set an explicit authority ceiling;
8. validate internal references and frontier consistency;
9. accurately claim completeness and resumption level.

## 7. Receiver procedure

A Handoff reader MUST:

1. validate Core and required modules;
2. assess origin, integrity, classification, and local policy;
3. locate the checkpoint and read-first records;
4. identify stale, disputed, unavailable, or unsupported information;
5. compare the requested action and ceiling with current local authority;
6. record acceptance, qualified acceptance, or rejection;
7. avoid external side effects until receiver policy authorizes them.

Acceptance statuses are `accepted`, `qualified`, and `rejected`. Qualified acceptance identifies every limitation that may affect continuation.

## 8. Interoperability experiment

The minimum handoff experiment uses one authoring system and at least two receiving systems that share neither private runtime state nor source conversation.

The test task contains one required constraint, one stale claim, one rejected alternative, one completed change with evidence, one unavailable dependency, an explicit authority ceiling, and one safe next action. Each receiver receives only the handoff and validly referenced material.

Score state recall, unsupported assumptions, constraint preservation, evidence use, dependency handling, authority compliance, and task success. A trial succeeds only when the receiver preserves every required constraint and authority boundary, does not treat stale or unavailable information as verified, and completes the next action or correctly reports a real blocker.

Reports SHOULD record capsule size where applicable, token usage, author and receiver versions, unsupported modules, omissions, false assumptions, safety failures, and resulting artifact quality. A single successful task is not evidence of general interoperability.

## 9. Conformance

A Handoff reader implements the receiver procedure and exposes limitations. A Handoff writer implements the producer procedure and makes accurate claims. A Resume Profile reader additionally implements Section 5 and declares the `resume-profile` capability. A system MAY support handoff and resume records without supporting the Capsule module; repository discovery requires Capsule support.

## 10. Pre-commit state bindings

Section 5 allows a `state_binding` to name a source-controlled revision. When that revision is a commit identifier, a producer cannot compute it until the commit exists, and the commit cannot describe the checkpoint until the checkpoint is written. Implementations resolve that ordering by committing and then amending, which rewrites the published revision and invalidates any binding a receiver already read.

A binding MAY instead name the content the producer staged for the commit rather than the commit itself. This version defines one such adapter profile, `git-staged-tree-v1`.

```json
{
  "state_space": "repo:application",
  "revision": "git-tree:4b825dc642cb6eb9a060e54bf8d69288fbee4904",
  "profile": "git-staged-tree-v1",
  "scope": ["src/", "tests/"],
  "working_tree": "clean"
}
```

Under `git-staged-tree-v1` the `revision` value MUST be `git-tree:` followed by the object identifier of the tree recorded by the producer's staged index, and that identifier MUST be obtained from the index itself rather than from a commit, a branch, or the working tree.

A producer MUST compute that tree identifier over the whole staged index. The `scope` array narrows which claims, evidence, and verification results the binding carries; it MUST NOT be read as narrowing what the recorded identifier covers.

The identifier is stable across the commit that follows it: when the index does not change between staging and committing, the resulting commit's tree is that same object. A receiver MUST therefore accept either an identical recomputed staged-tree identifier or a commit whose tree object equals the recorded identifier as a current binding, and MUST NOT report the binding stale merely because the producer's checkpoint predates the commit.

Because the profile names content and not history, a matching identifier establishes only that the same tree is present. It does not establish that the tree was committed, that it is reachable from any branch, or that commit metadata such as message, author, parents, or time matches anything the checkpoint describes.

A tree that is staged and never committed is unreachable and MAY be removed by repository maintenance. A producer that publishes a handoff for another participant SHOULD replace the staged-tree binding with a commit revision once the commit exists, and MUST disclose the retention limitation while the binding remains pre-commit.

A producer MUST NOT record a `git-staged-tree-v1` binding as clean when tracked paths within `scope` carry unstaged modifications, because the staged tree is then not the content on disk. It MUST either stage those changes, narrow `scope` to exclude them, or record the divergence so the receiver can treat affected claims as unverified.

Claims, evidence, and verification results bound to a staged tree MUST have been produced against the staged content. A producer MUST NOT bind a verification that ran against a different working-tree state, and a receiver MUST treat such a binding as unverifiable when the producer cannot establish which content was verified.

A host that cannot compute a staged-index tree identifier MUST report the binding as unavailable and fall back to a commit revision rather than substitute a working-tree or branch identifier.

A Capsule that carries the binding cannot be inside the tree the binding names: writing the identifier changes the Capsule, which changes the tree, which changes the identifier. A producer MUST therefore compute the identifier from the staged index as it stands before the Capsule revision is written, and MUST list the Capsule path, and any other path excluded for the same reason, in an `excludes` array on the binding.

A receiver MUST treat a commit whose tree differs from the recorded identifier only at excluded paths as current, and MUST report any other difference as stale. A producer MUST NOT use `excludes` to omit a work product from the binding; it carries only paths whose content depends on the identifier itself.
