# Action Boundary harness deployment

This repository contains a host-agnostic Action Boundary harness and two
advisory runtime bindings. The runtime hooks provide immediate feedback and
invocation logging. The `awp-action-boundary` GitHub Actions workflow is the
agent-blind gate for protected artifacts.

## Protected scope

The checked-in policy protects `protected-artifacts/**` as
`artifact-class:protected-generated-assets`. Freeform generation is denied;
traceable composite production requires a matching artifact claim. Ordinary
repository paths are not protected by this default policy.

Policy inputs live in `config/awp-action-boundary/`:

- `guardrails.json` -- Security guardrails;
- `decisions.json` -- Core decisions with Action Boundary extensions;
- `entry-status.json` -- complete CI context;
- `protected-paths.json` -- path-to-artifact classification;
- `artifact-claims.json` -- claims required for protected changes.

## Runtime hooks

The repository-local `.claude/settings.json` and `.codex/hooks.json` register
PreToolUse, PostToolUse, and Stop hooks in addition to the existing AWP
doorbell hooks. The bindings read their host-specific configuration from
`adapters/claude-code-hooks/config.json` and `adapters/codex-hooks/config.json`.

Runtime hooks are advisory. They can be disabled or bypassed and PostToolUse
cannot undo an operation that already ran. The CI gate must remain a required
protected-branch check for `action-enforced` behavior.

## Local verification

```text
python -m unittest tests.test_awp_harness -v
python tools/awp_ci_gate.py check --changed-files changed-files.txt --protected-paths config/awp-action-boundary/protected-paths.json --artifact-claims config/awp-action-boundary/artifact-claims.json --guardrails config/awp-action-boundary/guardrails.json --decisions config/awp-action-boundary/decisions.json
```

To protect another artifact class, update the policy files together and add
fixtures for denied freeform production, permitted traceable production,
changed invocation arguments, missing claims, and bypass paths. Do not claim
`output-attested` without a gateway that constrains the actual generation
operation before it executes.
