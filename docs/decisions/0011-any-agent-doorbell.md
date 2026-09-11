# ADR 0011: Wake any agent, local or hosted

**Status:** Accepted for the AWP 0.8.0 working draft
**Date:** 2026-09-11

## Context

The startup doorbell (ADR 0007, Cooperation Contracts section 9) and the Git ledgers (ADRs 0009 and 0010) made delivery reliable for an agent whose open session a local process can inject into, which today means the Codex CLI. A hosted Claude session in the desktop or web app, which is how most people use Claude, runs in the vendor's cloud: nothing on the user's machine stays running between its turns, and nothing local can start a turn for it. Messages to it were durable but waited until a person next opened it. The limitation had been recorded since 2026-09-09 but was treated as a footnote rather than as a threat to the goal, and so surfaced late.

## Decision

Generalize the doorbell into wake classes (W1 live session, W2 headless run, W3 hosted API, W4 forge mention, W5 principal notification, with W0 entry recovery underneath) behind the existing adapter contract, and run a per-recipient delivery ladder in a host-neutral relay: try each declared binding, wait for a recipient receipt, escalate, and finally notify the principal. Every participant declares its bindings; the relay verifies them by probe and reports only measured reach; senders see in advance which rung a recipient will get. Nothing is ever silent. Normative text is section 12; the design is `docs/doorbell-architecture.md`.

## Consequences

- Any local CLI agent becomes wakeable through W2, even without an injection command, at the cost of a new run instead of the open conversation.
- Hosted agents become wakeable where their vendor exposes an API or forge trigger. For Claude in the desktop and web apps the candidate is a routine with an API trigger, bound to the user's computer; it is to be proven by experiment before being claimed.
- Headless and hosted runs spend the recipient's usage, so bindings carry budgets and circuit breakers, and start with minimal permissions.
- The relay needs a machine that stays on. For teams, sleeping laptops, and hosted agents that is an always-on LAN host with a private remote.
- Every host binding now states its wake class up front, so a host that can only be reached on entry is visible as such.
