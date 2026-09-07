# AWP project history

AWP began as a compact format for carrying project intent and handoff context between sessions. As the project was exercised with increasingly demanding multi-agent scenarios, the design expanded from a portable state document into a protocol for preserving meaning, coordinating changes, and exploring alternatives safely.

## Early specifications

The early 0.x families established the core vocabulary: workstates, capsules, artifacts, handoffs, synchronization, and explicit specification binding. They remain useful for understanding the design’s foundations and for maintaining compatibility with older projects, but they are historical inputs to the current work rather than the project’s active direction.

The preserved release and module documents are available in the repository’s [release archive](releases/) and [design-history archive](../research/design-history/). These records are intentionally kept immutable so that older projects can continue to identify exactly which semantics they used.

## The current direction

The active design is the unreleased **AWP 0.8.0 working draft**. It unifies cooperation into the COOP-1/2/3 ladder, adds optional managed consultation, introduces persistent silos for alternative project states, and defines an optional A2A binding for protected COOP-3 coordination. The draft is developed alongside schemas, generated bundles, validators, conformance fixtures, reference tools, and explicit evidence of what remains unimplemented.

The [main README](../README.md) is the best starting point for the current project. The [0.8.0 draft overview](../spec/drafts/0.8.0/index.md) and [generated draft bundle](../dist/drafts/0.8.0/AWP-0.8.0-draft.bundle.md) are the normative development references.

## Reading the history

Historical documents describe the decisions and terminology of their time. They should not be read as claims about the capabilities or conformance of the current 0.8.0 draft. For the current status of releases, drafts, validation, and implementation boundaries, see the [project reference](project-reference.md).
