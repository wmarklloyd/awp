# Specification tools

The tools in this directory provide reproducible stable and archived-draft bundle generation, schema/example validation, conformance checking, link checking, workstate-integrity verification, requirement-inventory generation, and an experimental local presence monitor.

`awp_presence.py` is a reference implementation of the draft `local-sqlite-presence-v1` profile. It keeps advisory heartbeats and watcher cursors in a SQLite registry under the Git common directory by default, so worktrees share one registry. It is not an enforcing coordinator, authority source, semantic-scope analyzer, or production service.

The remaining tools are repository-maintenance tools, not a production AWP implementation. Passing them establishes only the properties each tool explicitly checks.

Run the complete command set documented in the repository [README](../README.md#validation) or rely on the same checks in GitHub Actions.
