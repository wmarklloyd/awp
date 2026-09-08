# AWP Coordination Scale 0.5.0

**Status:** Working draft; part of the AWP 0.8.0 draft family
**Module:** `urn:awp:coordination` (scale profile)

## 1. Scope

This document carries the presence-monitoring and scaling requirements that a
COOP-3 deployment needs and a COOP-1 or COOP-2 binding does not. It was split
out of `coordination.md` so that the ordinary coordination read path is not
obliged to carry material that only applies at authenticated, fenced, or
multi-host scale.

It is normative for a binding that claims those capabilities. Nothing here is
required to compose COOP-1 or COOP-2; a binding that does not claim presence
monitoring or the scaling profile simply does not implement this document.
Requirements common to every contract remain in `coordination.md`.

## 2. Agent presence and monitoring

Presence monitoring makes active participation observable before agents mutate a shared project. It is an advisory coordination capability incorporated by COOP-1 and COOP-2. Presence does not grant authority, reserve a scope, establish exclusivity, or imply that the announced actor is trusted. An authenticated fenced lease remains a COOP-3 operation distinct from a COOP-1 participant liveness lease.

A presence record identifies one runtime session:

```json
{
  "id": "presence:agent-17-session-4",
  "type": "presence",
  "module": "urn:awp:coordination",
  "revision": 1,
  "status": "active",
  "created_by": "actor:agent-17",
  "created_at": "2026-09-04T18:00:00Z",
  "agent_id": "agent:17",
  "session_id": "session:4",
  "principal": "principal:team-a",
  "workstate_id": "urn:uuid:596ae918-e7da-4e6f-a226-b13f8b084727",
  "project": "project:application",
  "execution_location": {
    "kind": "worktree",
    "location": "worktree:agent-17-session-4",
    "branch": "feature/auth-refresh"
  },
  "base": {
    "repository": "repo:application",
    "revision": "git:91ab4e7896d820c29ff5b9bd2a1f8d5ef67f734a",
    "profile": "git-state-v1"
  },
  "declared_scopes": ["scope:auth-refresh@2"],
  "access_mode": "write",
  "monitoring_profile": "local-sqlite-presence-v1",
  "heartbeat_at": "2026-09-04T18:00:30Z",
  "expires_at": "2026-09-04T18:02:00Z"
}
```

Required fields are `agent_id`, `session_id`, `principal`, `workstate_id`, `project`, `execution_location`, `base`, `declared_scopes`, `access_mode`, `monitoring_profile`, `heartbeat_at`, and `expires_at`. Project identity MUST be stable across worktrees or execution locations. `session_id` identifies one runtime generation and MUST NOT be reused after release or expiry. `base` binds the announcement to the revision from which work began. `declared_scopes` contains pinned Coordination scope references; a broad provisional scope MAY be announced and narrowed by a later revision.

Presence states are `active`, `released`, `expired`, and `superseded`. Entry MUST publish an active presence record before the actor performs a declared write. A heartbeat atomically advances `heartbeat_at` and `expires_at` for the same active session. It MUST NOT revive an expired, released, or superseded session; a returning runtime creates a new session identity.

The monitoring profile defines heartbeat interval, session duration, registry clock authority, retry policy, watcher cursor retention, and notification delivery. A monitor classifies a session as expired only through the profile's registry clock and an atomic compare against the latest heartbeat. Client wall clocks alone MUST NOT authoritatively expire a shared session. In an advisory deployment, an observer that cannot reach the registry reports presence as `unverifiable`, not absent.

A watcher maintains a durable cursor over lifecycle notifications. It announces at least new sessions, terminal sessions, and newly detected overlaps or conflicts. Delivery MUST be idempotent by notification identity. Restarting a watcher MUST resume from its stored cursor or explicitly disclose an observation gap. Heartbeats SHOULD update materialized live state without producing a durable event for every renewal; implementations MAY sample heartbeat evidence under a declared retention policy.

On entry, an implementation using presence monitoring MUST:

1. resolve stable project and workstate identity;
2. read and verify the current workstate and repository revision;
3. create a unique session and publish its initial scope before writing;
4. inspect active sessions and evaluate physical, semantic, and relied-upon-read overlap under current policy;
5. surface required warnings, negotiation, ordering, or blocking before mutation;
6. begin heartbeat renewal or declare that liveness cannot be maintained.

On normal exit, an implementation MUST stop new mutation, publish its final change set and semantic checkpoint or synchronization delta, refresh the canonical Capsule through the current projection owner, and then release its presence session. If the Capsule cannot be refreshed, the writer MUST publish an incomplete-handoff diagnostic rather than presenting the prior Capsule as current. Crash recovery relies on expiry and MUST preserve an `expired` terminal observation.

Heartbeats and other high-frequency live values MUST NOT be written into the project Capsule. The Capsule remains a durable semantic projection updated at checkpoints and handoff. Entry, release, expiry, conflict, and incomplete-handoff facts MAY be retained as durable Coordination events when they affect interpretation or audit.

Multiple agents MUST NOT independently overwrite one canonical Capsule from the same base frontier. Each agent publishes events or deltas; a single current projection owner updates the Capsule using compare-and-swap against its frontier and generated digest. A stale writer merges, retries, or reports divergence through Synchronization. It MUST NOT use last-write-wins.

### 18.1.1 Local SQLite presence profile

The informative profile `local-sqlite-presence-v1` supports agents sharing one local Git common directory. It uses SQLite transactions for atomic entry, expiry, release, and watcher-cursor advancement. Its registry clock is the host running the transaction. The profile uses a 90-second session duration, recommends renewal at most every 30 seconds, and treats exact pinned-scope equality plus an explicit wildcard as its only automatic overlap evidence.

This profile is advisory. It does not authenticate principals, fence writes, provide cross-host availability, infer semantic overlap, or satisfy COOP-2 or COOP-3. A deployment that changes its timing, clock, matching, or retention behavior declares a distinct profile or explicit profile parameters.

## 3. Scaling requirements

An implementation intended for many concurrent agents MUST avoid project-wide polling and all-pairs overlap comparison. It SHOULD:

- partition presence and event streams by stable project and state-space identity;
- index active sessions by project, pinned scope, access mode, and expiration;
- route scope changes only to watchers subscribed to potentially interacting scopes;
- coalesce heartbeats in materialized state rather than append every renewal to durable history;
- provide cursor-based incremental delivery, bounded pages, backpressure, and idempotent retry;
- define retention for terminal sessions, watcher cursors, diagnostics, and sampled liveness evidence;
- isolate hot scopes so one heavily contended component does not serialize unrelated work;
- measure active sessions, renewal latency, expiry lag, notification lag, conflict candidates, false alarms, dropped observations, and projection retries;
- preserve a recovery path when an index, subscriber, projector, or coordinator restarts.

Sharding MUST NOT change the semantic result of overlap evaluation. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants require an identified routing or aggregation strategy. An implementation MUST disclose any scope class it cannot compare completely.

### 18.2.1 Brokered and sharded presence profile

The candidate profile `brokered-sharded-presence-v1` defines advisory presence for deployments in which agents may run on different hosts and a single local registry is insufficient. This profile remains an advisory presence capability: it does not become a COOP-3 protected lease merely because its transport is distributed.

The profile has four logical responsibilities, which MAY be implemented by one service or separate replicated services:

1. a session registry stores current presence and heartbeat state;
2. a scope router identifies partitions and subscribers that may interact with a declaration;
3. an event broker delivers lifecycle, conflict, gap, and handoff notifications;
4. a Capsule projector consumes durable semantic events or deltas and serializes the canonical Capsule projection for each workstate.

#### Partitioning and routing

The primary partition key MUST include stable project identity and state-space identity. Session ownership, renewal, release, and expiry for one session MUST be linearizable within its owning partition. Exact pinned scopes SHOULD use an inverted index keyed by scope identity and access mode rather than scanning all active sessions.

A scope router MUST identify every partition that can contain a potentially interacting scope under the declared comparison policy. Cross-partition scopes, wildcard scopes, integration ownership, and project-wide invariants MUST be routed to an aggregator or a declared global-scope partition. If any required partition or index is unavailable, the result is `unverifiable`; the implementation MUST NOT report that no conflict exists.

Partition rebalancing MUST preserve session generation, terminal state, watcher position, and overlap results. A former partition owner MUST NOT accept a renewal or release after ownership has transferred. Implementations SHOULD use epochs, compare-and-swap, or equivalent stale-owner rejection even though presence itself remains advisory.

#### Heartbeats and expiry

Heartbeats MUST route directly by session identity and update coalesced materialized state. They MUST NOT produce one durable broker event per renewal. A heartbeat update MUST compare the session generation and current active state atomically, so a delayed message cannot revive a terminal or replaced session.

Expiry MUST be scheduled from the authoritative registry time of the owning partition. An expiry worker MUST atomically compare the expected session generation and latest expiration before publishing `presence.expired`. Duplicate expiry attempts and duplicate lifecycle delivery MUST converge through stable event identity and idempotent processing.

#### Subscriptions, retention, and backpressure

Watchers SHOULD subscribe by project plus pinned scopes, scope classes, or declared global interest. The broker MUST support durable cursors, bounded delivery pages, idempotent retry, and an explicit retention interval. Cursor state MAY be compacted, but a watcher whose cursor falls behind retained history MUST receive `presence.observation_gap` before current state is presented as complete.

When a hot or wildcard scope matches many sessions, the registry SHOULD publish a bounded conflict-set summary plus a resumable cursor instead of one unbounded notification per pair. Backpressure MUST NOT silently discard a safety-relevant lifecycle, conflict, gap, or incomplete-handoff observation. A deployment MUST declare queue limits, overflow behavior, retry limits, and the point at which presence becomes `unverifiable`.

Terminal sessions, lifecycle events, watcher cursors, conflict summaries, and sampled liveness evidence MUST have explicit retention policies. Retention expiry MUST NOT erase durable semantic events already incorporated into a checkpoint or Capsule projection.

#### Identity, authorization, and confidentiality

The registry MUST authenticate the submitting runtime and bind it to the asserted agent and principal under deployment policy. Authorization MUST constrain which projects, scopes, subscriptions, and presence details that identity may publish or observe. Authentication of presence proves only who made the announcement; it grants no project authority and no permission to mutate a scope.

Deployments spanning trust boundaries MUST define transport protection, replay protection, tenant isolation, audit retention, and redaction of worktree, branch, scope, and principal metadata. A monitor MUST distinguish unauthorized, unreachable, stale, and absent state.

#### Capsule projection

Agents MUST publish final semantic events or synchronization deltas before release; they MUST NOT race to overwrite the canonical Capsule. For each workstate, the projection service MUST expose one logical writer and compare the expected frontier and generated digest before replacement. Replicated projectors MUST use fenced ownership or an equivalent mechanism that prevents a stale projector from publishing after ownership transfer.

A projection conflict MUST reload and reconcile the new frontier, retry under policy, or publish divergence. It MUST NOT resolve by last-write-wins. Projector failure does not keep heartbeat values in the Capsule: it produces an incomplete-handoff observation while the live registry and durable event stream remain separate.

#### Capacity and failure disclosure

A conforming deployment MUST publish the profile parameters and tested envelope on which its capacity claim depends, including session duration, heartbeat interval, active-session count, scope distribution, wildcard rate, partitions, replication, event retention, and watcher fan-out. It SHOULD report p50, p95, and p99 entry, renewal, expiry, notification, conflict-query, and projection latency together with error, retry, gap, and false-alarm rates.

Load tests MUST include synchronized renewal bursts, hot scopes, wildcard scopes, broker restart, partition-owner failover, delayed and duplicated messages, watcher lag beyond retention, network partition, clock skew, and concurrent Capsule projection. A deployment MUST identify which guarantees remain available during each failure. Results from the local SQLite profile or a sequential synthetic probe MUST NOT be presented as evidence of distributed capacity.
