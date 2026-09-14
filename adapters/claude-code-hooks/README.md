# `claude-code-hooks-v1` (illustrative, advisory-only)

An illustrative binding of `urn:awp:action-boundary` 0.3.1 to Claude Code's
hook system, following `adapters.md`'s framework. It is documented as a
concrete profile in `spec/drafts/0.8.0/adapters.md` section 8, which is the
normative-adjacent description; this directory is the runnable prototype
that profile describes.

**Advisory only.** action-boundary.md section 7 already states that a hook
the gated participant's own host executes is not an independent enforcement
point -- the same reason a commit hook is inadequate there. It can be
disabled in settings, bypassed by a shell escape, or simply not exist for a
different agent runtime. The binding this repository actually relies on for
an enforcement claim is `tools/awp_ci_gate.py`, which is agent-blind and does
not trust anything a hook did or logged. Use this binding for fast local
feedback and for populating the event log the session-end compliance report
reads -- not as a substitute for the CI gate.

## Files

- `pretooluse.py` -- gates a tool call before it runs; maps to `tools/awp_harness.py`'s `gate()`.
- `posttooluse.py` -- recomputes the invocation binding against the call that actually ran; maps to `enforce()`.
- `stop.py` -- session-end fresh-context-style reviewer; maps to `session_compliance_report()`.
- `config.example.json` -- copy to `config.json` and fill in real paths for a specific project.
- `../protected_write_classifier.py` -- shared with `../codex-hooks/`, not duplicated. Primary classification: matches a tool call's target path (path-like `tool_input` arguments, or command text) against a project's `protected_paths` config, regardless of the calling tool's name. `config.json`'s `mappings` list is kept only as an optional, more-precise override for a *confirmed* tool_name -- see that module's docstring for why a name-keyed table alone is fragile in general (a host may never confirm a stable tool_name for a given capability, or may report one too generic to key off, as `../codex-hooks/README.md` documents for Codex CLI specifically).

See `../codex-hooks/README.md` for the equivalent Codex CLI binding, which
can share a project's policy files (guardrails/decisions/protected-paths)
and the same classifier, with its own host-specific caveats.

**Note (2026-09-14):** this binding was revised from a tool_name-mapping-only
design to the classifier-based one described above. `spec/drafts/0.8.0/adapters.md`
section 8, referenced above as this binding's normative-adjacent description,
has not yet been revised to match and may still describe the older,
mapping-only shape -- reconcile that doc against this directory before
treating section 8 as authoritative on the current classification logic.

## Wiring into a project

In the project's Claude Code settings, register:

```json
{
  "hooks": {
    "PreToolUse": [{"hooks": [{"type": "command", "command": "python3 adapters/claude-code-hooks/pretooluse.py"}]}],
    "PostToolUse": [{"hooks": [{"type": "command", "command": "python3 adapters/claude-code-hooks/posttooluse.py"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python3 adapters/claude-code-hooks/stop.py"}]}]
  }
}
```

Each script exits 0 in every ordinary case (per the verified hook contract,
blocking is expressed through the JSON `permissionDecision` field, not
through the process exit code) and reads its one JSON payload from stdin.

## Known bypasses (do not treat this binding as sufficient by itself)

- A shell command, a different tool alias, or a direct API call outside the
  mapped `tool_name` set is not gated at all.
- Hooks can be disabled in local settings by anyone with write access to them.
- A delegated subagent invoking the same underlying tool through a different
  entry point may not pass through the same hook registration.
- `posttooluse.py`'s verification is advisory context, not a rollback -- by
  the time it runs, the tool has already executed.

`tools/awp_ci_gate.py` is unaffected by all of the above, because it runs
after the fact against the actual repository content, regardless of how it
got there.
