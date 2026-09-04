# Presence-monitoring scalability probe

This synthetic probe measures the experimental `local-sqlite-presence-v1` reference tool. It creates independent exact scopes, measures one indexed exact-scope conflict, measures one project-wide wildcard conflict, and performs an initial watcher scan.

```bash
python experiments/presence-monitoring/run_benchmark.py --sessions 1000
```

The result is local instrumentation evidence only. It does not establish production capacity, cross-host behavior, agent effectiveness, semantic-scope accuracy, fairness, or availability under failure. Sequential entry includes opening a SQLite connection and transaction for each session. Wildcard work intentionally touches every active session and represents a hot project-wide scope.

Use the probe to detect regressions and compare indexing strategies on the same machine. Do not compare raw timings across machines as if they were a protocol guarantee.
