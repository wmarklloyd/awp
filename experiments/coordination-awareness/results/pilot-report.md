# Synthetic pilot report

**Status:** Instrumentation check; not an independent-agent experiment

The pilot evaluated 5 fixed cases. The ground truth and detection rules are encoded in the repository, so the results establish only that the measurement implementation behaves as specified.

| Condition | TP | TN | FP | FN | Recall | Warning phase |
|---|---:|---:|---:|---:|---:|---|
| `chat_only_proxy` | 0 | 2 | 0 | 3 | 0.00 | message-time-if-explicit |
| `git_only_proxy` | 1 | 2 | 0 | 2 | 0.33 | post-change |
| `awp_assisted_proxy` | 3 | 2 | 0 | 0 | 1.00 | pre-implementation-declaration |

The AWP-assisted proxy recognizes all encoded physical and semantic overlaps; the Git-only proxy recognizes only the same-file case; and the chat-only proxy recognizes none because the fixtures contain no explicit chat warning. This is an expected consequence of the fixture definitions, not a measured treatment effect.

Agent behavior, authoring time, coordination delay, token cost, and integration success were not measured. The preregistered independent-agent protocol must be run before making effectiveness claims.
