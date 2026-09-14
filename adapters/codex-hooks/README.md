# `codex-hooks` (illustrative, advisory-only)

A binding of `urn:awp:action-boundary` to Codex CLI's hook system,
mirroring `../claude-code-hooks/` and able to share a project's policy
files with it (`guardrails`/`decisions`/`protected_paths`/`entry_status` in
config.json). One project policy, multiple host bindings.

**Advisory only**, for the same reason as the Claude binding: a hook the
gated participant's own host executes is not an independent enforcement
point. `tools/awp_ci_gate.py`, run in CI, is the actual enforcement point --
agent-blind and host-blind, it does not trust anything either binding did
or logged.

## Files

- `pretooluse.py` -- gates a tool call before it runs; maps to `tools/awp_harness.py`'s `gate()`.
- `posttooluse.py` -- recomputes the invocation binding against the call that actually ran; maps to `enforce()`.
- `stop.py` -- session-end fresh-context-style reviewer; maps to `session_compliance_report()`.
- `config.example.json` -- copy to `config.json` and fill in real paths for a specific project.

Classification logic (`../protected_write_classifier.py`) is shared with
the Claude binding, not duplicated. See that module's docstring for why it
matches on the *target path* of a call rather than the tool's name.

## Why this binding leans on the classifier more than Claude's does

Codex's `PreToolUse`/`PostToolUse` hooks are documented, across three
independently-fetched third-party sources consulted 2026-09-13/14 (the
official docs at `developers.openai.com/codex/hooks` and
`learn.chatgpt.com/docs/hooks` repeatedly failed to fetch during that
research and should be re-checked when they become reachable), to fire only
for locally-executed tool calls, reported with a generic `tool_name` such as
`"Bash"` or `"exec_command"` regardless of what the underlying command
actually does; hosted/remote tool calls may not be covered at all. A
`tool_name`-keyed mapping table (`config.json`'s `mappings`, kept for parity
with the Claude binding) is therefore close to useless here in principle --
this is a harder case than "the real tool_name was never confirmed," which
is the gap the Claude binding's `mappings` was originally meant to close.
What this binding can actually see and act on is the *text* of a
locally-executed command -- exactly what
`protected_write_classifier.classify()` inspects (`tool_input.command` and
any path-like arguments) irrespective of tool identity.

**Practical consequence:** this binding gates shell-mediated writes into a
protected path (a `cp`/generator script/redirect that Codex runs locally). It
does not claim visibility into a call made through a hosted tool Codex does
not route through `PreToolUse`. If Codex's coverage changes (the three
sources disagree on scope; one describes broader coverage including
`apply_patch` and MCP tool calls), re-verify and revise this note.

## Wiring into a project

In the project's Codex CLI hooks config (`~/.codex/hooks.json` for a
user-level binding, or `<repo>/.codex/hooks.json` for a repo-level one),
register:

```json
{
  "hooks": {
    "PreToolUse": [{"hooks": [{"type": "command", "command": "python3 adapters/codex-hooks/pretooluse.py"}]}],
    "PostToolUse": [{"hooks": [{"type": "command", "command": "python3 adapters/codex-hooks/posttooluse.py"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python3 adapters/codex-hooks/stop.py"}]}]
  }
}
```

No `matcher` field is set on any of these -- an absent matcher means "match
every tool call," the same convention Claude Code uses, so this hook sees
every call Codex routes through `PreToolUse` rather than only a named subset.

Each script exits 0 in every ordinary case (blocking is expressed through
the JSON `permissionDecision` field, not the process exit code) and reads
its one JSON payload from stdin.

## Shared event log, shared caveat

`config.json`'s `event_log` can point at the same event log the Claude
binding writes to. Each logged `action_resolution` carries an `actor` field
(`actor:codex-session` here, `actor:agent-session` for Claude) so a reader
can filter by host. `tools/awp_harness.py`'s `session_compliance_report` --
what `stop.py` calls -- summarizes the **entire** log regardless of which
host's session asked for the report; this is that function's own existing
behavior, not something either binding layers on top. A `Stop` report from
either host currently describes combined cross-host, cross-session activity
when the log is shared, not just its own turn. Point `event_log` in
`config.json` at a host-specific file if a binding needs an exact,
host-scoped compliance report instead.

## Known bypasses (do not treat this binding as sufficient by itself)

Same list as `../claude-code-hooks/README.md`, plus the coverage limitation
above:

- A tool call Codex does not route through `PreToolUse` (documented to
  include hosted/remote tools) is not gated at all -- treat this as a real
  gap in a deployment's coverage, not a hypothetical one, for any protected
  class that a hosted tool could produce.
- Hooks can be disabled in local settings by anyone with write access to them.
- `posttooluse.py`'s verification is advisory context, not a rollback -- by
  the time it runs, the tool has already executed.

`tools/awp_ci_gate.py` is unaffected by all of the above, because it runs
after the fact against the actual repository content, regardless of how it
got there or which host (or no host) produced it.
