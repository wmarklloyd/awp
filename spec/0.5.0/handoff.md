# AWP Handoff 0.2.0

**Module ID:** `urn:awp:handoff`  
**Status:** Optional  
**Depends on:** AWP Core `0.5.x`

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
  "repository_state": [
    {
      "repository": "repo:application",
      "source_revision": "git:91ab4e7",
      "path_scope": ["src/", "tests/"]
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

`repository_state`, when present, binds a resume checkpoint to the repository and immutable source revision against which it was prepared. Each entry requires `repository` and `source_revision` and MAY narrow comparison using `path_scope`. A `project_reentry` record that depends on source-controlled artifacts MUST include each repository state required to assess safe continuation.

A receiver that can identify the local repository revision MUST compare it with `source_revision`. A mismatch makes the repository binding stale. When it can obtain a diff, claims, evidence, change sets, and verification results scoped to changed paths MUST be treated as stale until reverified or explicitly re-scoped. When the receiver cannot identify or compare the repository revision, the binding is unverifiable rather than current. A matching revision does not establish that remote services, credentials, or other dependencies remain current.

`read_first` is an ordered presentation hint, not causal ordering or authority. A receiver MAY load additional records required to interpret dependencies, evidence, conflicts, or safety constraints. It MUST NOT omit relevant required state merely to meet a context budget. Optional context-selection metadata MAY state a token or byte budget, priority groups, and deferred artifacts, but it cannot weaken completeness, freshness, or authority requirements.

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


