# ADR 0006: First-class consultation records

**Status:** Accepted for the AWP 0.7.0 working draft  
**Date:** 2026-09-04

## Context

A user or agent may become stuck on a bounded problem and want to ask another model, chatbot, human, or specialist for an opinion. A generic question, task, or handoff does not distinguish that request from ordinary project work or delegation. A portable exchange also needs to preserve the problem statement, relevant facts, attempted remedies, constraints, and the limits on the response.

## Decision

AWP Core adds a first-class `consultation` record. The record requires a specific `question`, `status`, `requested_action`, portable `context`, and ordered `read_first` references. Optional response fields support recording a later answer, respondent, uncertainty, and evidence on a subsequent revision.

The record is model- and domain-neutral. It can request debugging advice, design critique, analytical review, or another bounded form of assistance. A consultation is advice-seeking state, not a task delegation or authority grant. Existing authority ceilings, shared guardrails, and receiver policy apply to the consulting actor and to any action considered after the response.

## Consequences

An AWP workstate can now be exported as a focused question for another model while retaining enough structured context to be useful even when repository or artifact references are not retrievable. Producers should embed the necessary excerpts and observations for that case. The record does not make those observations true, does not require private chain-of-thought, and does not cause the receiving model to execute the proposed next steps.
