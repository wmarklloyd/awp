# Design rationale

## Portable semantic state

Chat transcripts and repositories contain useful evidence but do not provide a compact, typed statement of current goals, constraints, decisions, uncertainty, authority, and resumable next actions. AWP represents those concepts directly while retaining links to their evidence.

## Events and projections

Events preserve causal history and concurrent contributions. Snapshots make that history practical to inspect. Treating snapshots as projections avoids making a convenient summary silently override the evidence from which it was derived.

## Modular protocol family

Core is intentionally smaller than the complete protocol. A reader can support portable state without claiming support for packages, synchronization, coordination, cryptography, or external bindings. Explicit module identifiers and versions prevent optional features from changing Core semantics invisibly.

## Epistemic separation

Reported, inferred, observed, verified, disputed, stale, and refuted states are not interchangeable. The distinction is intended to prevent agent assertions, tool output, and accepted conclusions from collapsing into one undifferentiated confidence label.

## Authority separation

Imported workstate describes authority claims but cannot authorize itself. The receiving environment evaluates identity, scope, expiration, revocation, and local policy before an external action.

## Exact specification binding

A shared workstate identifies the specification artifact governing its interpretation. This permits exploratory protocol evolution without guessing compatibility. Published releases remain immutable; incompatible `0.x` changes increment the minor version.
