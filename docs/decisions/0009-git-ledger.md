# ADR 0009: Store the rendezvous ledger in Git

**Status:** Accepted for the AWP 0.8.0 working draft
**Date:** 2026-09-11

## Context

The startup doorbell (Cooperation Contracts section 9) worked on one machine, but two properties blocked the project goal of reliable, cross-platform, agent-neutral delivery:

- The event store was a SQLite file under `.awp-runtime/`. SQLite's WAL mode fails intermittently across the Windows host and a Linux VM sharing the repository (`disk I/O error`, `unable to open database file`), and a remote machine cannot read it at all.
- The wake signal (a Git ref or a watched file) and the event it announced lived in different places, so a signal could exist without its data and every consumer had to reconcile the two.

File-change notifications were never the failure: they work on one machine. They do not cross machines, and neither does a local SQLite file.

## Decision

Adopt `git-ledger-v1` (section 10) as the reference ledger profile:

- Each actor appends events as commits on its own ref, `refs/awp/ledger/<workstate>/<actor>`: one event document per commit, one parent, compare-and-swap updates, never forced. A single writer per ref means concurrent writers cannot overwrite each other and no merge is ever needed.
- The ref update that stores an event is the Git event that wakes the recipient. No separate signal refs.
- Consumers keep a cursor of ref to last processed commit and deduplicate by event identifier, so replay after a crash or a missed trigger is exact.
- The same refs can be pushed to and fetched from any Git remote: a bare repository, SSH, or a forge. That gives Windows, macOS, and remote Linux participants one ledger without a shared filesystem.
- The profile is selected per clone (`git config awp.coop2.ledger git-ledger-v1`), behind the interface the rendezvous and supervisor already use, so another store can be added as another profile.

Remote sync is implemented and tested against a bare repository but is not configured: the project's GitHub origin is public, and pushing ledger refs there would publish consultation text. Remote use needs a remote whose readers match the audience, chosen by the principal.

## Consequences

- The SQLite rendezvous is migrated into Git unchanged (event identifiers, documents, and binding identity preserved) and the SQLite file becomes history.
- Readers pay a few Git process invocations per read; the reference implementation caches per-ref history and reads only new commits.
- Ledger refs are not branches: normal clones and fetches do not download them, and `git gc` keeps them because they are referenced.
- Actors remain self-asserted and events are not encrypted; authenticating ref ownership and a push-notification trigger for remotes are open issues 36 and 37.
- Other version-control systems are not targeted now. Git covers the large majority of developers; Perforce is the plausible second profile and can be added later against section 10's obligations.
