# Notification architecture review, 2026-09-11

**Scope:** the any-agent doorbell as of commit `eb94293`: relay (`tools/awp_relay.py`), wake bindings and adapters (`tools/awp_wake.py`), hosted-agent watcher (`tools/awp_wake_watch.sh`), host hooks, Git ledger, and Cooperation Contracts section 12.
**Reviewer:** Claude (Fable 5.1), at the principal's request. **Dispositions:** Claude (Opus 5), same day.

## Verdict

The structure is sound: the Git ledger is the only truth, the relay is host neutral with small adapters, bindings are declared and then verified by probe, and nothing ends silently. It is proven live across three agent types (Codex CLI by session injection, the Codex app by a headless run, Claude in Cowork by a subscribed session). The weaknesses were in operational durability, the trust boundary, and places where status claimed more than was true.

## Findings and dispositions

| # | Finding | Disposition |
|---|---|---|
| 1 | The relay had no supervisor: after a reboot nothing ran until an agent activated, and two activations could race two relays. | Fixed. `SingletonLock` holds an exclusive OS lock for the relay's lifetime (a relaunch releases it first). Activation installs a per-user watchdog (Task Scheduler every five minutes, a systemd user timer, or a launchd agent) that runs `awp_relay.py ensure`; no administrator rights; `git config awp.relay.autostart false` opts out; `awp_relay uninstall-autostart` removes it. Spec: Relay supervision. |
| 2 | The Cowork watcher was hand-armed, lived only in the agent's workspace, and a first run swallowed an existing signal. | Fixed. `awp_wake arm-hook` installs the subscription idempotently; `awp_wake enter --host cowork` prints the exact arm and verify commands; a first run now treats an existing signal as pending. Re-arming after the vendor recycles the workspace remains open (open issue 42). |
| 3 | Liveness was overstated: the relay heartbeated every served actor, so a hosted agent looked active with no session running. | Fixed. Heartbeats only for bindings that inject into a session kept open on the relay's machine; reach expires after six hours (`wake-stale`). Spec: Honest reach. |
| 4 | The ladder stopped at receipt: a consultation that entered a session but was never taken up looked delivered. | Fixed. After receipt a consultation enters an engagement watch; no accept, refuse, or response within its delivery window notifies the principal, or records `received-not-engaged`. Spec: Engagement. |
| 5 | A headless run was reported as reaching the agent, though it is not the session the principal watches. | Fixed. Every reach row states what the rung reaches; a consultation handled by a new run also notifies the principal. Addressing the Codex app's own conversation remains open (open issue 40). |
| 6 | Identifiers were pasted into commands without validation; any process can write any actor's ref. | Partly fixed. Strict token grammar at registration, relay admission, and notice construction. Authenticating ref ownership remains open issue 36, required before a LAN relay. |
| 7 | Re-probing a suspended binding every 30 minutes costs a paid run each time; `codex exec` used `workspace-write`. | Fixed. Exponential probe backoff capped at a day; probes run `codex exec --sandbox read-only`. Consultations keep `workspace-write` so the agent can respond. |
| 8 | "Event-driven" was claimed for a transport that polls; the signal ref grew one commit per wake. | Fixed. The spec now separates the subscribed session (event driven) from its transport (which must disclose polling). The signal ref is one force-updated parentless commit. |
| 9 | The request spool was never pruned; two tests failed on Linux; no Windows CI for the doorbell. | Fixed. Hourly pruning of answered requests older than a week; the two tests now skip or patch correctly; a `doorbell-windows` CI job runs the doorbell tests on Windows. The full suite passes on Linux (274 tests). |
