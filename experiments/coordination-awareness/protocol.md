# Preregistered coordination-awareness protocol

**Status:** Proposed protocol; no independent-agent trial has been run  
**Protocol revision:** 1  
**Specification under test:** AWP Coordination 0.4.0 working draft

## Research question

Does structured publication of revision-pinned physical and semantic scopes warn independent agents about material conflicts earlier and more accurately than chat-only or Git-only coordination?

## Conditions

1. **Chat-only:** Participants may exchange ordinary task messages but receive no AWP records or automated overlap analysis.
2. **Git-only:** Participants use isolated branches or worktrees and standard Git status, diff, merge, and review information.
3. **AWP-assisted:** Participants receive the same repository and task information plus AWP intent, scope, overlap, and acknowledgement support.

The underlying task, repository revision, model/runtime class, tool permissions, time limit, and context budget must be held constant within each matched block.

## Tasks

Each block contains independent work, a same-file physical conflict, a different-file semantic-contract conflict, and a writer-versus-relied-upon-reader conflict. Fixtures must have ground truth defined before participant output is inspected.

## Primary outcomes

- Conflict detected before implementation begins.
- False-positive and false-negative conflict classifications.
- Successful integration without violating the fixture invariant.
- Time from task assignment to conflict warning and final integration.

## Secondary outcomes

- Input and output tokens.
- Number and byte size of coordination messages or records.
- Human interventions.
- Abandoned or repeated work.
- Stale-state recovery success.

## Scoring and blinding

Ground-truth conflict labels and invariant tests are hidden from participants. A scoring program evaluates repository outputs and recorded warnings. Manual adjudicators, if needed, receive anonymized condition labels. Every exclusion and failed run is retained with a reason.

## Minimum study

Use at least two independently implemented agent systems and enough randomized repetitions to report confidence intervals rather than only point estimates. Model versions, system prompts, tools, temperature or sampling controls, and repository commits must be recorded. Results from one implementation or deterministic synthetic fixtures are pilot evidence only.

## Analysis

Report confusion matrices by condition and conflict class. Compare early-warning rate, integration success, elapsed time, and coordination overhead within matched blocks. Publish raw trial records and analysis code. Exploratory analyses must be labeled separately from preregistered outcomes.

## Safety

Trials run in disposable repositories without production credentials or external deployment authority. Imported AWP authority records do not authorize side effects.
