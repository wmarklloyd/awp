# Coordination-awareness experiment

This directory operationalizes the early experiment proposed by AWP Coordination. It contains a reproducible synthetic pilot and a preregistered protocol for later trials with independent agent systems.

## What the synthetic pilot tests

The pilot checks whether three instrumentation conditions classify a fixed set of conflicts as designed:

- **chat-only proxy:** only an explicit conflict warning is observable;
- **Git-only proxy:** overlap is detected only after changed paths intersect;
- **AWP-assisted proxy:** declared physical and semantic scopes are compared before implementation.

This is a unit test of measurement logic, not evidence that AWP improves agent performance. The cases encode their own ground truth, and no language model makes decisions during the run.

## Run

```bash
python experiments/coordination-awareness/run_pilot.py --check
```

Use `--write` to regenerate the checked-in JSON and Markdown reports.

## Next experiment

The preregistered procedure in [`protocol.md`](protocol.md) requires independent receiving systems, randomized condition assignment, blinded ground-truth scoring, time and token measurement, and publication of all raw trials. Until that study is run, claims about false-positive rates, coordination cost, or outcome improvement remain unsupported.
