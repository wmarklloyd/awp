# AWP Synchronization 0.4.0

**Module ID:** `urn:awp:sync`  
**Status:** Optional  
**Depends on:** AWP Core `0.7.x`  
**Document status:** Working Draft  
**Editor:** Mark Lloyd  
**Updated:** 2026-09-03  
**License:** GPL-3.0-only

## 1. Scope

AWP Synchronization defines incremental event exchange, snapshot reconciliation, forks, concurrent branches, and conflict-preserving merge. It does not define a network transport, consensus system, or automatic semantic merge.

A workstate or message using deltas, omitted-history boundaries, or synchronization conflict semantics MUST declare this module. It MUST be required when the receiver must apply or reconcile those structures to reach the continuation frontier.

## 2. Delta

A delta carries events added after a known frontier:

```json
{
  "awp_version": "0.7.0",
  "module": "urn:awp:sync",
  "kind": "workstate.delta",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "base_frontier": ["evt:01K4M4TWM2"],
  "result_frontier": ["evt:01K4M4VYB9"],
  "events": [],
  "artifacts": [],
  "modules": []
}
```

A delta MUST identify `workstate_id`, `base_frontier`, `result_frontier`, and `events`. It MAY carry artifact announcements or module data required by those events.

A receiver MUST verify that the base frontier is known or request missing ancestry. It MUST validate event IDs, workstate IDs, parents, module declarations, and result frontier before application. Applying a delta MUST be idempotent by event ID. Reuse of one event ID for different bytes is an integrity conflict.

## 3. Snapshot reconciliation

A reader with both a snapshot and event ledger MUST:

1. verify unique event IDs, matching workstate IDs, and declared ancestry;
2. compute the ledger frontier as events that are not a parent of another available event;
3. confirm that the snapshot frontier is an antichain of known event IDs;
4. compare frontiers as sets, never ordered arrays;
5. classify and handle the relationship using Section 4.

A missing parent makes history incomplete unless the manifest explicitly identifies an omitted-history boundary and source digest. `full` completeness cannot omit ancestry.

## 4. Reconciliation states

- `current`: snapshot frontier equals ledger frontier and reconstructed semantic state agrees;
- `stale_replayable`: every snapshot tip is an ancestor of a ledger tip;
- `unverifiable`: snapshot references unavailable history or unknown future events;
- `divergent`: neither represented frontier descends from the other;
- `invalid_projection`: snapshot claims a known frontier but disagrees with valid replay.

For `stale_replayable`, a processor replays descendant events in deterministic topological order. Concurrent events remain concurrent; topological serialization MUST NOT be treated as conflict resolution. Record revision preconditions determine whether updates commute or conflict.

For `divergent`, a processor preserves both branches and invokes merge processing. For `invalid_projection`, it discards or quarantines the projection and rebuilds from valid history. A stale optional projection does not invalidate an otherwise valid ledger.

## 5. Forks

Forking creates a new workstate ID and records:

- parent workstate ID;
- parent frontier;
- fork event;
- reason or intent;
- inherited module declarations.

Copying or repackaging without divergent identity is not a fork.

Concurrent replicas of the same workstate retain one workstate ID. They exchange frontiers and missing events rather than creating new identities.

## 6. Merge and conflict

Mechanical merge unions events by ID after integrity validation. It preserves all concurrent tips. It MUST NOT silently apply last-write-wins to:

- authority or constraints;
- accepted decisions;
- incompatible record revisions;
- contradictory verified claims;
- artifact versions occupying one logical slot;
- module-specific invariants or contracts.

A semantic conflict record identifies competing events or records, conflict class, explanation, status, and resolution owner. Core conflict classes are `authority`, `constraint`, `decision`, `claim`, `artifact`, `task`, `dependency`, `module`, and `unknown`.

Resolution is a new event whose parents include every resolved tip. It records the chosen result, rationale, evidence, and unresolved risk. History remains intact.

## 7. Deterministic replay

Replay MUST respect graph ancestry. When concurrent events require a deterministic processing order, processors sort by event ID only as a reproducibility device. This ordering has no semantic priority.

An update with a prior-record revision applies only when that precondition holds. Two commuting updates may both apply. Non-commuting concurrent updates create a conflict unless their owning module defines a safe deterministic rule.

Unknown optional-module events remain graph nodes and participate in frontier computation. A processor MUST NOT advance a derived snapshot through an unknown event when doing so could alter a required Core or module result; it reports the projection as unverifiable instead.

## 8. Compaction

AWP 0.7.0 does not define destructive log compaction. A writer MAY create a summary or snapshot-only export, but it MUST disclose omitted history and MUST NOT claim `full` completeness.

A future compaction profile must define lineage, state canonicalization, proof of the compacted frontier, treatment of unknown module events, signature invalidation, and audit guarantees. A snapshot alone does not authorize deletion of prior history.

## 9. Transport independence

Deltas may travel through files, HTTP, A2A, MCP, message queues, repositories, or peer protocols. A transport binding defines authentication, retries, acknowledgement, ordering, size limits, and retrieval. Synchronization semantics remain unchanged.

## 10. Conformance

A Synchronization reader validates ancestry and integrity, computes frontiers, applies deltas idempotently, preserves concurrency, and surfaces semantic conflicts.

A Synchronization writer emits valid base and result frontiers, includes required events or declares missing ancestry, and never describes a lossy history as full.


