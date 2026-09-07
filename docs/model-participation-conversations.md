# Worked model participation conversations

These conversations are compact behavioral examples for the experimental participation contract. They show the model-visible request and response. Host metadata, Core event envelopes, and storage details are omitted unless they explain a result. The adapter must return a receipt before the model describes a publication as confirmed.

Each example assumes the model has already read the short participant instruction. `ctx:*` handles identify a frontier and coverage; they are not permanent truth.

## 1. Ordinary re-entry

The model enters a project and asks for the task context.

```json
// model → adapter
{"operation":"read","request_id":"request:1","project":"project:watches","goal":"goal:battery-review"}

// adapter → model
{
  "request_id":"request:1", "project":"project:watches", "publication":"not_applicable",
  "coordination":"clear", "context":"ctx:1", "frontier":["evt:checkpoint-17"],
  "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[],
  "next":{"operation":"announce","reason":"Declare the files and facts this task will change or rely on."}
}
```

The model may now announce work. The context handle tells the adapter exactly which state the model read.

## 2. Compatible readers

Two agents read the same scope. A read does not create a write conflict.

```json
// model B → adapter
{"operation":"announce","request_id":"request:2","context":"ctx:1","project":"project:watches","summary":"Review battery data without changing it","scope":[{"path":"data/battery.csv","access":"read"}]}

// adapter → model B
{
  "request_id":"request:2", "project":"project:watches", "publication":"confirmed",
  "coordination":"clear", "intent":"intent:2", "receipt":"receipt:2",
  "frontier":["evt:2"], "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[],
  "next":{"operation":"publish","reason":"Report observations and evidence when review is complete."}
}
```

If another reader announces the same scope, the adapter returns the same coordination result. Read access does not imply permission to write.

## 3. Conflicting writers

The second writer announces a scope already being written by another intent.

```json
// model B → adapter
{"operation":"announce","request_id":"request:3","context":"ctx:1","project":"project:watches","summary":"Normalize battery values","scope":[{"path":"data/battery.csv","access":"write"}]}

// adapter → model B
{
  "request_id":"request:3", "project":"project:watches", "publication":"confirmed",
  "coordination":"warning", "intent":"intent:3", "receipt":"receipt:3",
  "frontier":["evt:3"], "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "overlaps":[{"handle":"overlap:3","summary":"intent:1 also writes data/battery.csv"}],
  "diagnostics":[{"code":"AWP-COORD-OVERLAP","severity":"warning","message":"A writer overlap requires an ordering or disposition."}],
  "next":{"operation":"resolve","reason":"Propose an order or request arbitration before changing the shared file."}
}
```

The intent publication can be confirmed while the requested work remains guarded. The model must not interpret `confirmed` as permission to ignore the warning.

## 4. Scope expansion

The model discovers that it must also edit a parser.

```json
// model → adapter
{"operation":"announce","request_id":"request:4","context":"ctx:3","project":"project:watches","intent":"intent:3","summary":"Normalize battery values and update the parser","scope":[{"path":"data/battery.csv","access":"write"},{"path":"src/parse_battery.py","access":"write"}]}

// adapter → model
{
  "request_id":"request:4", "project":"project:watches", "publication":"confirmed",
  "coordination":"warning", "intent":"intent:3", "receipt":"receipt:4",
  "frontier":["evt:4"], "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[{"code":"AWP-COORD-SCOPE-EXPANDED","severity":"warning","message":"The declared scope changed and overlap was reevaluated."}],
  "next":{"operation":"resolve","reason":"Resolve the newly reported parser overlap before writing."}
}
```

A previous scope declaration never authorizes an undisclosed path. Expansion repeats the freshness and overlap checks.

## 5. Changed relied-upon fact

The model relied on a measurement-method claim that advanced after the intent was announced.

```json
// model → adapter
{"operation":"publish","request_id":"request:5","context":"ctx:4","project":"project:watches","intent":"intent:3","summary":"Battery comparison completed","actual_scope":[{"path":"data/battery.csv","access":"write"}],"evidence":["artifact:comparison-log"],"unfinished_work":[]}

// adapter → model
{
  "request_id":"request:5", "project":"project:watches", "publication":"not_applicable",
  "coordination":"stale", "frontier":["evt:method-3"], "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[{"code":"AWP-COORD-STALE","severity":"error","message":"claim:battery-method@2 changed to revision 3; re-evaluate the comparison."}],
  "next":{"operation":"read","reason":"Read the changed claim and choose whether to re-run or rebase the comparison."}
}
```

The result remains a reportable attempted result, but it is not presented as current or ready for integration until the dependency is revalidated.

## 6. Stale capsule with replayable events

The capsule is behind the ledger, but the missing events are available.

```json
// model → adapter
{"operation":"read","request_id":"request:6","project":"project:watches","goal":"goal:battery-review"}

// adapter → model
{
  "request_id":"request:6", "project":"project:watches", "publication":"not_applicable",
  "coordination":"warning", "context":"ctx:6", "frontier":["evt:checkpoint-19"],
  "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[{"code":"AWP-SYNC-STALE-REPLAYABLE","severity":"warning","message":"The capsule was refreshed by replaying two available descendant events."}],
  "next":{"operation":"announce","reason":"Use the refreshed context for new work."}
}
```

The adapter refreshes its context handle before returning it. If the events were unavailable, the response would use `unverifiable` and identify the missing ancestry.

## 7. Missing evidence

The model reports a change but has no inspectable test output.

```json
// model → adapter
{"operation":"publish","request_id":"request:7","context":"ctx:6","project":"project:watches","intent":"intent:7","summary":"Parser update completed","actual_scope":[{"path":"src/parse_battery.py","access":"write"}],"unfinished_work":[]}

// adapter → model
{
  "request_id":"request:7", "project":"project:watches", "publication":"confirmed",
  "coordination":"unverifiable", "result":"result:7", "receipt":"receipt:7", "frontier":["evt:7"],
  "authority_ceiling":["read_only","local_write"],
  "coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},
  "diagnostics":[{"code":"AWP-COORD-EVIDENCE-MISSING","severity":"warning","message":"No inspectable verification artifact was supplied."}],
  "next":{"operation":"publish","reason":"Attach test output or explicitly leave verification incomplete before integration."}
}
```

`publication=confirmed` means the result record was stored. `coordination=unverifiable` means the result cannot support a verified integration claim.

## 8. Lost response after publication

The host committed the announce request but the model did not receive its response.

```json
// model → adapter, retry with the same request ID and identical content
{"operation":"announce","request_id":"request:8","context":"ctx:6","project":"project:watches","summary":"Update watch battery comparisons","scope":[{"path":"data/battery.csv","access":"write"}]}

// adapter → model
{"request_id":"request:8","project":"project:watches","publication":"confirmed","coordination":"warning","intent":"intent:8","receipt":"receipt:8","frontier":["evt:8"],"coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},"authority_ceiling":["read_only","local_write"],"diagnostics":[],"next":{"operation":"resolve","reason":"A writer overlap is still pending."}}
```

The adapter returns the original receipt and creates no duplicate intent. If the model changed the summary while keeping `request:8`, the adapter would return `rejected` with an idempotency integrity error.

## 9. Crash during exit

The model asks to exit after publishing its result. The host crashes after the result is stored but before the capsule is confirmed.

```json
// model → adapter
{"operation":"checkpoint","request_id":"request:9","context":"ctx:8","project":"project:watches","intent":"intent:8","next_action":"Wait for the next battery review","unresolved_work":[],"mode":"exit"}

// adapter → model after recovery
{"request_id":"request:9","project":"project:watches","publication":"pending","coordination":"needs_input","intent":"intent:8","frontier":["evt:result-8"],"coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},"authority_ceiling":["read_only","local_write"],"diagnostics":[{"code":"AWP-CAPSULE-INCOMPLETE-HANDOFF","severity":"error","message":"The result is durable but capsule confirmation was interrupted."}],"next":{"operation":"checkpoint","reason":"Retry capsule projection with request:9 before releasing the session."}}
```

The recovered adapter resumes the checkpoint state machine. It does not release presence or claim that exit completed until capsule confirmation, terminal intent publication, and presence release are each confirmed.

## 10. Pending human arbitration

Two changes have a semantic contract conflict that the agents cannot resolve.

```json
// model → adapter
{"operation":"resolve","request_id":"request:10","context":"ctx:9","project":"project:watches","intent":"intent:8","overlap":"overlap:10","disposition":"escalated","rationale":"Both changes alter the battery normalization contract; a user must choose the compatible behavior.","evidence":["artifact:contract-diff"]}

// adapter → model
{"request_id":"request:10","project":"project:watches","publication":"confirmed","coordination":"needs_input","overlap":"overlap:10","frontier":["evt:10"],"coverage":{"scope_complete":true,"history":"complete","semantic_analysis":"reported_only"},"authority_ceiling":["read_only","local_write"],"diagnostics":[{"code":"AWP-COORD-ARBITRATION-PENDING","severity":"policy","message":"A user decision is required for overlap:10."}],"next":{"operation":"read","reason":"Wait for the named user decision; do not write the guarded scope while arbitration is pending."}}
```

The overlap-resolution publication is confirmed, but the decision is not. The model may continue explicitly permitted independent work only when the response names that scope; it cannot treat escalation as acceptance.

## Review use

These examples should be run through the participation schema and adapter tests. Each scenario needs assertions for the visible response, durable event or receipt identity, retry behavior, and authority ceiling. The examples intentionally keep the model request small; the adapter must retain the richer AWP records needed for audit and projection.
