# Changelog

This file records protocol-family changes. Released artifacts remain immutable; detailed module changes belong in versioned release notes.

## Unreleased — 0.7.0 working draft

- Drafts exact governing-specification binding and embedded discovery for self-contained capsules.
- Drafts coordination for shared work products and arbitrary state-space adapters.
- Drafts portable cross-model consultations and model-independent shared guardrails.
- Drafts explicit governing-specification binding, embedded discovery, cross-model consultations, and shared guardrails.
- Draft validation and conformance assets are available for review; this is not a published release.
- `awp_state_binding.staged_tree_binding` now caps per-category divergence (unstaged/untracked) at a configurable limit (default 2000, `AWP_DIVERGENCE_LIMIT`, or a checkpoint request's `state_binding.divergence_limit`), reporting a truncated sample plus an honest total instead of embedding an unbounded file list -- a project with an ignore-pattern gap around a build/dependency cache no longer produces a Capsule sized to its whole working tree.

## 0.6.0 — 2026-09-03

- Integrated Coordination 0.3.0 as a normative experimental module.
- Added deterministic coordination lifecycles, scopes, contracts, verification binding, diagnostics, and staged conformance capabilities.
- Added the 0.6 schemas, validator, generated bundle, and release notes.

## 0.5.0

- Added repository discovery and project-reentry semantics.

## 0.4.0

- Split the protocol into Core and independently declared modules.

## 0.3.0

- Published the initial monolithic exploratory design.
