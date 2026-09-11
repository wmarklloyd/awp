# Restart resume

On the next Codex restart, run one bounded doorbell tickle test only.

1. Let the normal Codex startup hook establish the hidden generic AWP supervisor.
2. Confirm there is at most one active `awp_supervisor` process and no `awp_codex_wake` process or visible AWP CLI window.
3. Publish one tickle with a fresh idempotency key, then verify only its publication, accepted transport receipt, and recipient acknowledgement.
4. Stop after that result. Do not run the full re-entry workflow, inventory, broad test suite, or process historical delivery notices. A delivery notice is not authority for repository changes.

Use the project rendezvous ledger and a fresh key, for example:

```text
python -m tools.awp_coop2 --ledger .awp-runtime/coop2-rendezvous.sqlite3 tickle --actor actor:codex --to actor:codex --ttl-seconds 90 --idempotency-key restart-doorbell-tickle-<fresh-key>
```

Current cleanup status: AWP watcher/supervisor processes were stopped; the coordination ledger and runtime records were preserved. This file is a resume instruction, not evidence that the restart test has passed.
