# AWP 0.3.0 — Structured Review & Recommendations

> **Document type:** External review feedback  
> **Target version:** AWP Draft Specification 0.3.0  
> **Date:** 2026-09-03  
> **Reviewer perspective:** Protocol implementer / cross-runtime interoperability

---

## Executive Summary

AWP 0.3.0 correctly identifies a genuine gap in the agent infrastructure stack: the missing **semantic layer** between raw chat transcripts and byte-level source control. The five-layer model (briefing → semantic state → event ledger → artifacts → extensions) is architecturally sound, and the insistence on separating **intent, authority, execution, and evidence** is exactly the right philosophical foundation.

The main risk to AWP's success is **overloading the initial implementation**. This review recommends ruthlessly separating the *portable core* (single-agent semantic checkpointing) from the *coordination extension* (multi-agent lease and contract management), hardening the single-file capsule format against real-world parsing hazards, and validating the core through empirical cross-model handoffs before expanding scope.

---

## 1. What Works Exceptionally Well

| Strength | Why It Matters |
|---|---|
| **Markdown-first human access** (§3.9, §8.1.1) | Guarantees that a human can always orient themselves without special tooling. This is the correct default for debugging and trust. |
| **Epistemic status on claims** (§13.3, §15) | Prevents the common failure mode where LLMs treat "suggested" as "verified." The `stale` and `refuted` statuses are particularly important for long-running work. |
| **Untrusted-by-default security posture** (§27) | The explicit warnings about prompt injection, confused deputy, and stale authority are stronger than most protocol drafts at this stage. |
| **Completeness taxonomy** (§8.2) | `summary` / `portable` / `full` gives implementers a clear dial for tradeoffs between fidelity and size. |
| **Empirical testing as a success criterion** (Design Review conclusion, §38) | Defining success as "can another LLM continue the work?" keeps the spec honest and grounded. |

---

## 2. Critical Issues & High-Priority Suggestions

### 2.1 Markdown / Typed-State Drift (§7, §8.1.1)

**Problem:** The spec states that if prose conflicts with typed state, typed state wins. However, it provides no mechanism to detect that drift has occurred. A human (or agent) will inevitably edit `WORK.md` and forget to emit a corresponding event.

**Suggestion:** Introduce a machine-verifiable boundary in `WORK.md`:

- Require auto-generated sections to be wrapped in explicit markers (e.g., `<!-- awp:generated:start frontier=evt_01K4... -->`).
- Define a **consistency check algorithm** in §32: a reader must be able to hash the generated sections and compare them against a `snapshot.json` digest, or at minimum verify that the `WORK.md` frontier matches the manifest frontier.
- Distinguish **three classes of content** in `WORK.md`:
  1. **Machine-generated from snapshot** — regenerated on every checkpoint
  2. **Human-authored but bounded** — within declared sections, imported as proposed events if edited
  3. **Free-form notes** — never authoritative for machine decisions

**Proposed addition to §8.1.1:**

```markdown
<!-- awp:generated:start frontier="evt_01K4M4VYB9..." digest="sha256:7d8c..." -->
## Active work
- Agent A is updating the authentication callback.
<!-- awp:generated:end -->

<!-- awp:human:start -->
## Notes
I think we should also consider rate limiting here.
<!-- awp:human:end -->
```

---

### 2.2 Event Schema Version Confusion (§11 vs §35)

**Problem:** Events carry `"awp": "0.1"` while the specification is `0.3.0`. This is ambiguous: does the event envelope version track the spec version independently? If so, the relationship is unexplained.

**Suggestion:** Rename the event field to `event_schema_version` (or `event_schema`) and add a normative mapping. For example:

```json
{
  "event_schema_version": "0.1",
  "protocol_version": "0.3.0"
}
```

This makes it clear that the event envelope can be stable even as the protocol gains new record types. Add a version compatibility matrix to §35:

| Protocol Version | Minimum Event Schema | Maximum Event Schema |
|---|---|---|
| 0.3.0 | 0.1 | 0.1 |
| 0.4.0 | 0.1 | 0.2 |

---

### 2.3 Single-File Marker Fragility (§8.2)

**Problem:** The `<!-- awp:manifest:start -->` HTML-comment markers are vulnerable to collision with artifact content or even natural Markdown prose. The spec says exact source files "SHOULD" be base64-encoded, but this is not strict enough.

**Suggestion:**

- **Option A (Recommended):** Change the encoding rule to **MUST** base64-encode any artifact or content block that could contain the substring `<!-- awp:`.
- **Option B:** Adopt a more robust delimiter strategy: require a random boundary token generated per-file and declared in the manifest, similar to MIME multipart. This prevents all collision attacks and accidents.

```markdown
<!-- awp:artifact:start id="artifact:logo" boundary="----awp-7d8c9f2a----" encoding="base64" -->
iVBORw0KGgoAAAANSUhEUgAA...
<!-- awp:artifact:end boundary="----awp-7d8c9f2a----" -->
```

---

### 2.4 Coordination Scope Creep (§22)

**Problem:** Section 22 defines an elaborate multi-agent coordination framework (leases, contracts, integration plans, semantic effects). It is excellent work, but it more than doubles the conceptual surface area of the protocol. The Design Review itself recommends a "narrow, useful slice" for the first implementation, yet §22 is presented as normative core.

**Suggestion:**

- **Define a Core Profile** for v0.4.0 that excludes coordination. Move §22 into an **optional extension namespace** (e.g., `https://awp.io/ns/coordination/0.3`) or mark it explicitly as *Experimental*.
- This allows Phase 1 implementations to achieve interoperability without implementing lease expiration, overlap classification, and integration plans. The coordination model can mature in parallel once the core capsule format is proven.

**Proposed Core Profile record types:**
- `goal`
- `constraint`
- `claim`
- `evidence`
- `decision`
- `plan`
- `task`
- `question`
- `artifact`
- `execution`
- `change`
- `risk`
- `checkpoint`
- `session`
- `handoff`

**Deferred to coordination extension:**
- `work_intent`
- `coordination_scope`
- `coordination_lease`
- `interface_contract`
- `change_set`
- `coordination_conflict`
- `integration_plan`

---

### 2.5 Missing Formal Schema

**Problem:** The specification is prose + examples. While the examples are clear, they are not normative. Two independent implementers will inevitably diverge on edge cases (e.g., can `claim.confidence` be `null`? Is `artifact.locations` required if the artifact is embedded?).

**Suggestion:**

- Add a **normative JSON Schema** appendix for the manifest, event envelope, and all portable-core record types.
- Define **strict validation rules**: which fields are required, which are nullable, and the exact enum values for statuses.

**Example schema excerpt for `claim`:**

```json
{
  "$id": "https://awp.io/schema/0.3.0/claim.json",
  "type": "object",
  "required": ["id", "type", "statement", "epistemic_status"],
  "properties": {
    "id": { "type": "string", "pattern": "^claim:[a-zA-Z0-9_-]+$" },
    "type": { "const": "claim" },
    "statement": { "type": "string", "minLength": 1 },
    "epistemic_status": {
      "type": "string",
      "enum": ["reported", "inferred", "observed", "verified", "disputed", "unknown", "stale", "refuted", "superseded"]
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "evidence": {
      "type": "array",
      "items": { "type": "string", "pattern": "^evidence:[a-zA-Z0-9_-]+$" }
    }
  }
}
```

---

## 3. Architectural Suggestions

### 3.1 Snapshot-Event Consistency Algorithm (§29)

The spec says events are authoritative over snapshots, but does not specify the algorithm a reader uses to verify consistency. Add a normative procedure to §32:

```
1. Read manifest.json.
2. Read snapshot.json and note its frontier.
3. Read events.jsonl and verify that the final event IDs equal the snapshot frontier.
4. If the event log extends beyond the snapshot frontier, the snapshot is STALE;
   the reader must replay events from the snapshot frontier forward.
5. If the snapshot cannot be regenerated from events (e.g., missing parent),
   the workstate is INVALID.
```

---

### 3.2 Artifact Reference Registry (§13.9, §16)

The `locations` array uses a `kind` field with values like `package`, `remote`, `local`. Define a minimal registry of standard location kinds and their required fields to prevent fragmentation.

| `kind` | Required Fields | Optional Fields |
|---|---|---|
| `package` | `path` | — |
| `remote` | `uri` | `headers`, `expires_at` |
| `local` | `path` | `absolute` (boolean) |
| `repository_relative` | `repository`, `revision`, `path` | — |
| `unavailable` | `reason` | — |

---

### 3.3 Lease Modes in Decentralized Settings (§22.6)

The spec admits that offline implementations may treat leases as advisory. This creates a dangerous ambiguity: a lease in one system is a hard lock; in another, it is a suggestion. Be explicit:

- **Advisory mode:** All leases are non-binding signals. Conflicts are detected at integration time.
- **Enforced mode:** A coordinator service guarantees lease exclusivity.

A workstate should declare which mode it assumes via a manifest field:

```json
{
  "coordination_mode": "advisory"
}
```

---

### 3.4 Redaction vs. Content Addressing (§26)

Physical redaction removes content, but artifacts are content-addressed. If `artifact:secret-file` is redacted, its SHA-256 digest changes, breaking all references from evidence and change sets.

**Suggestion:** Specify that redaction creates a **tombstone artifact** (preserving the original ID and a redaction marker) rather than removing the descriptor. This preserves referential integrity while scrubbing bytes.

```json
{
  "id": "artifact:secret-file",
  "type": "artifact",
  "name": "secret-file.env",
  "status": "redacted",
  "redaction": {
    "reason": "credential_exposure",
    "redacted_at": "2026-09-03T21:00:00Z",
    "redacted_by": "actor:admin"
  },
  "original_integrity": {
    "algorithm": "sha256",
    "digest": "7d8c..."
  }
}
```

---

## 4. Editorial & Structural Suggestions

| Issue | Recommendation |
|---|---|
| **Design Review length** | The informative preamble (pre-§1) is ~30% of the document. Consider publishing it as a separate *Design Rationale* companion document so the spec itself is scannable. |
| **Open Questions taxonomy** (§37) | Group the 18 open questions by impact: *Blocking Phase 1*, *Blocking v1.0*, and *Deferrable*. This signals to implementers what they can safely ignore for now. |
| **Conformance mapping** (§31) | Map the six conformance classes to the implementation phases in §38. For example, "Core Reader/Writer = Phase 1; Coordination Processor = Phase 2." |
| **Secret scanning** (§25) | Add a normative warning that execution outputs and evidence artifacts MUST be scanned for accidental secret inclusion before packaging. |
| **Side-effect taxonomy** (§17) | Consider adding `data_migration` and `third_party_api_call` as side-effect classes. These are common in agent workflows and have distinct risk profiles. |
| **Checkpoint resumption level** (§18) | Clarify whether a checkpoint claiming `operational` resumption must also satisfy all requirements of `semantic`. The current text implies this but does not state it. |

---

## 5. Proposed v0.4.0 Priorities

If editing the next draft, focus on these seven items in this order:

1. **Define the Core Profile** — A strict, minimal subset of record types (goals, constraints, decisions, tasks, claims, evidence, artifacts, checkpoints) required for a `portable` handoff. Everything else is an extension.
2. **Publish JSON Schema** — Normative schemas for manifest, event envelope, and Core Profile records.
3. **Resolve event versioning** — Clarify `event_schema_version` vs `protocol_version`.
4. **Harden single-file parsing** — Mandate collision-proof delimiters or base64 requirements.
5. **Specify WORK.md consistency checks** — Algorithm to detect stale or edited generated sections.
6. **Mark coordination as experimental** — Move §22 into an extension namespace; keep the portable core simple.
7. **Draft empirical test protocol** — Define the exact handoff scenario, success criteria, and failure modes for the "can another LLM continue?" test.

---

## 6. Summary

AWP 0.3.0 is one of the more thoughtful protocol drafts in the agent interoperability space. Its core insight—that work meaning must be preserved separately from conversation history and file diffs—is correct and increasingly urgent.

The specification should be judged by its own excellent criterion: **can a different agent, given only the capsule and available project artifacts, correctly understand the current work, avoid violating constraints, coordinate with other agents, and take the next safe step?**

To maximize the probability of passing that test across independent implementations, the next version should:

- **Shrink the normative core** to the smallest set of record types that enables reliable semantic resumption.
- **Harden the capsule format** against parsing hazards that will appear in real-world use.
- **Add normative schemas** so implementers agree on edge cases without reverse-engineering from examples.
- **Defer coordination complexity** until the core is proven through empirical cross-model handoffs.

The foundation is strong. The priority now is to prove it works in practice before expanding it.

---

*End of review.*
