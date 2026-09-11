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

## Amendment 2026-09-11: Git-event trigger and host prompt receipts

The first passing startup-doorbell probe (tickle:0bfc8fb10aa65185b9775cf8, Claude to Codex, 2026-09-11 03:25Z) completed publication, supervisor wake, transport, and recipient receipt in six seconds after an ordinary Codex start. Getting there changed four things, now specified in Cooperation Contracts section 9:

- **Git event as trigger.** The supervisor wakes on a change in `refs/awp/signal/` and replays the ledger immediately; timed replay remains only as a safety net and heartbeat.
- **No supervisor acknowledgement.** An earlier shortcut let the supervisor acknowledge probes itself, so a passing probe proved only that the supervisor was alive. Receipts now carry provenance (`direct`, `agent-ingress`, `host-prompt-hook`), and delivering components record transport evidence only.
- **Host prompt receipt.** Four deliveries reached the Codex session and the model replied that it had acknowledged without running the receipt command. A shared hook on the host's prompt-submitted event now records receipt when the notice enters the session, independent of model compliance.
- **Host integration traps.** The Codex startup hook was declared asynchronous and was skipped; Codex re-requires approval whenever a hook definition changes; and Codex fires its startup hook only after the first input. Hook definitions stay fixed, entry points log every invocation, and the first-input requirement is disclosed.

Still open: a second agent host must pass the same probe before the path is shown to be host neutral in practice, and hosts without a local wake endpoint (for example, a cloud-hosted Claude session) participate through entry recovery only.

