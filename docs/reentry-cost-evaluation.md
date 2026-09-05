# AWP re-entry cost evaluation

**Status:** implementation evaluation  
**Date:** 2026-09-05  
**Subject:** model-facing cost of reading and maintaining `awp.awp.md`

## Finding

The root capsule is inexpensive for a host to read and hash, but unnecessarily expensive to place wholesale in a model context. At the evaluated checkpoint it is 55,130 bytes and contains 118 indexed records. A participant entering the project needs the generated briefing, active Resume/Handoff/checkpoint, seven ordered `read_first` records, and compact descriptors for seven required artifacts—not every historical record and artifact body.

The distinction is architectural: full-file parsing is host work; semantic orientation is model work. AWP should require the former for validation without requiring the latter for every participant prompt.

## Implemented projection

`tools/awp_reentry.py` implements the experimental `selective-reentry-v1` profile. Against the current capsule:

| View | Approximate output | Completeness |
|---|---:|---|
| Entire source capsule | 55,130 bytes | Authoritative source |
| Briefing only | 2,731 characters | Explicitly incomplete orientation |
| Selective re-entry view | 15,450 bytes | Complete for the active Resume |

The complete selective view reduces participant-facing input by about 72 percent while retaining capsule integrity, governing metadata, authority ceiling, checkpoint, recommended action, the ordered re-entry records, and verified required-artifact digests and locations.

## Safety boundary

The tool does not rewrite or summarize authoritative records. It parses the full capsule, verifies the generated-region digest, indexes records by stable ID, verifies local SHA-256 artifacts required by the active Resume, and copies the selected records verbatim into a disposable JSON projection. A stale capsule, missing record, or unavailable, unverifiable, or modified required artifact makes the result `incomplete`. If the configured output budget is too small, it emits `budget_exceeded`, identifies the omitted entry section, and exits nonzero instead of silently truncating required context.

This addresses routine re-entry cost. It does not solve long-term capsule compaction, historical retention, or semantic dependency inference. Those remain separate work: a future writer may archive superseded history while preserving event ancestry and artifact references, and a stronger reader may compute transitive dependencies beyond the explicit Resume selection.
