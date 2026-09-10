# ADR 0007: Generic startup activation for managed doorbells

**Status:** Accepted for the AWP 0.8.0 working draft
**Date:** 2026-09-10

## Context

The local rendezvous durably preserves interactions, but a durable mailbox is not an unattended doorbell. Earlier experiments coupled ledger polling, queue submission, and recipient observation to one host. They could also appear successful after a user manually repaired startup, even though ordinary AWP entry had failed to arm the path. That does not satisfy the project goal: any supported agent must become reachable as a consequence of ordinary AWP startup.

## Decision

AWP uses `awp-host-activation-v1`, a host-neutral activation contract. Ordinary startup or resume invokes one generic entrypoint, which establishes a generation-scoped route and starts or attaches an `awp-supervisor-v1` process. The supervisor owns durable ledger replay, retry state, heartbeats, transport receipts, and atomic recipient-ingress requests. Git refs and filesystem signals remain content-free, coalescing hints; the ledger and its cursor are the lossless source of work.

Host adapters translate only attach, probe, and wake operations. Codex initially uses its session queue and Claude initially uses resumable CLI delivery, but neither adapter owns AWP policy or ledger semantics. Queue admission records `transport_queued`, not agent observation. Only recipient-side ingress can publish `observed`, `accepted`, `refused`, or `responded` evidence.

A clean-start run passes only when the ordinary host entry arms delivery without a later manual command. Manual recovery is useful troubleshooting evidence but cannot convert that run into a pass.

## Consequences

New agent hosts implement the activation adapter contract instead of adding another watcher. Restarts replay from the durable cursor and endpoint operations use stable identifiers. The current implementation remains an experimental local profile: it does not authenticate actors, provide a cross-host broker, guarantee that every vendor can inject a turn into an already-open UI, or establish full COOP-2 conformance.
