# ADR 0005: Portable guardrails apply across collaboration modes

- **Status:** Accepted for the 0.7.0 working draft
- **Date:** 2026-09-04

## Context

Safety requirements should not depend on which model is used, whether one agent is working alone, or whether several agents divide and combine a task. A prohibition such as unauthorized access to third-party systems must remain effective when work is handed off, delegated, decomposed, or integrated.

## Decision

AWP Security defines guardrails as structured extensions of Core `constraint` records. A guardrail identifies applicable actors, operations, resources, effect, conditions, provenance, and enforcement status. Guardrails travel with the workstate and are evaluated by the receiving runtime or protected adapter.

Required guardrails apply to solo actions and to every actor, delegated task, change set, integration plan, and derived operation in a collaboration. An agent cannot weaken or evade a guardrail through delegation, task decomposition, an authority claim, a contract, or an adapter. A required guardrail that cannot be interpreted or enforced remains blocking for the affected external or security-sensitive operation.

An imported assertion becomes effective only after the receiving policy accepts its policy owner, provenance, and authority basis. An untrusted actor may propose a stricter guardrail but cannot globally impose or relax policy merely by serializing a constraint. Applicable accepted guardrails compose by restrictive effect; equal-authority disagreement is unverifiable and blocks the affected guarded operation.

## Consequences

Different models can receive the same portable safety policy without relying on shared prompts or hidden runtime state. AWP can preserve, propagate, and diagnose guardrails, but it cannot make an arbitrary runtime obey them; enforcement remains a responsibility of the receiving environment or an identified protected adapter.
