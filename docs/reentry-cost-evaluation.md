# AWP re-entry cost evaluation

**Status:** implementation evaluation  
**Date:** 2026-09-05  
**Subject:** model-facing cost of reading and maintaining `awp.awp.md`

## Finding

The root capsule is inexpensive for a host to read and hash, but unnecessarily expensive to place wholesale in a model context. At the evaluated checkpoint it is approximately 56–59 KB and contains approximately 130–140 indexed records. A participant entering the project needs the generated briefing, active Resume/Handoff/checkpoint, seven ordered `read_first` records, and compact descriptors for seven required artifacts—not every historical record and artifact body.

The distinction is architectural: full-file parsing is host work; semantic orientation is model work. AWP should require the former for validation without requiring the latter for every participant prompt.

## Implemented projection

`tools/awp_reentry.py` implements the experimental `selective-reentry-v1` profile. Against the current capsule:

| View | Approximate output | Completeness |
|---|---:|---|
| Entire source capsule | Approximately 58 KB | Authoritative source |
| Briefing only | 992 characters | Explicitly incomplete orientation |
| Selective re-entry view | 13,813 bytes | Complete for the active Resume |

The complete selective view reduces participant-facing input by about 76 percent while retaining capsule integrity, governing metadata, authority ceiling, checkpoint, recommended action, the ordered re-entry records, and verified required-artifact digests and locations.

## Safety boundary

The tool does not rewrite or summarize authoritative records. It parses the full capsule, verifies the generated-region digest, indexes records by stable ID, verifies local SHA-256 artifacts required by the active Resume, and copies the selected records verbatim into a disposable JSON projection. A stale capsule, missing record, or unavailable, unverifiable, or modified required artifact makes the result `incomplete`. If the configured output budget is too small, it emits `budget_exceeded`, identifies the omitted entry section, and exits nonzero instead of silently truncating required context.

This addresses routine re-entry cost. It does not solve long-term capsule compaction, historical retention, or semantic dependency inference. Those remain separate work: a future writer may archive superseded history while preserving event ancestry and artifact references, and a stronger reader may compute transitive dependencies beyond the explicit Resume selection.

## Maintenance-cost findings

The read reduction does not remove the cost of maintaining the source Capsule. The current root Capsule is approximately 56–59 KB across fewer than 100 lines, with approximately 130–140 indexed records. Its snapshot is approximately 50 KB and its generated briefing is approximately 1 KB. It contains approximately 60 artifact descriptors with integrity digests. A full local artifact audit checks the historical and current descriptors; routine selective entry checks the seven artifacts required by the active Resume.

The host computation is inexpensive on this repository: a representative run took about 73 ms for selective entry, 59 ms for artifact verification, and 216 ms for the 0.8 validator. The larger recurring cost was authoring and synchronization. Before the canonical projector, a semantic update could require manual record editing, briefing editing, generated-digest repair, and artifact-digest repair. The repository history contains 24 Capsule-touching commits with 566 insertions and 343 deletions, illustrating that the file is a frequently revised shared projection rather than a low-churn static document.

The `local-workstate-projector-v1` reference tool addresses the highest-value maintenance failures. It makes the host own serialization, checks the whole-Capsule digest as well as the generated digest, supports a verified no-change exit, writes through a synchronized temporary file and atomic replacement, and leaves a recoverable journal across an interrupted replacement. It does not yet implement semantic event projection, immutable artifact revision storage, or continuation-history export; those remain the next maintenance reductions.
