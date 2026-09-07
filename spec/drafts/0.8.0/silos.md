# AWP Silo Profile 0.1.0

**Profile:** `silo-v1`

**Owning module:** AWP Synchronization `urn:awp:sync`, `0.5.x`

**Dependencies:** Core `0.8.x`, Synchronization `0.5.x`, Capsule `0.5.x`; other modules when used

**Status:** Normative, experimental profile in the unreleased AWP 0.8.0 working draft

**Schema:** `../../../schemas/awp-silo-0.1.schema.json`

The capitalized requirement words have the BCP 14 meanings defined by the family specification.

## 1. Purpose and composition

A **silo** is a persistent, shareable alternative project workstate derived from a pinned parent state. It preserves an exploration's purpose, goals, constraints, plans, evidence, participants, and local decisions without making them accepted canonical project state. Several actors may work in one silo, and a silo may have child silos.

This profile composes the existing Synchronization fork, Core records and authority declarations, Capsule publication, and, when selected, Cooperation Contracts. A silo is a governed fork, not a new kind of replica or an automatic source-control branch. The project's **canonical workstate** is the root designated by current project policy; it needs no synthetic parent or silo record. A destination silo may itself accept results without making them canonical for the project.

An implementation using this profile MUST declare Synchronization with capability `silo-v1` and compatible Core and Capsule declarations. Synchronization and Capsule MUST be required when continuation depends on silo isolation, ancestry, or adoption. A receiver that does not support `silo-v1` MUST NOT claim a complete interpretation or perform dependent continuation, even if it supports ordinary Synchronization forks. Unknown optional profile data follows the family's preservation rules.

A silo requires no named COOP contract, service, Git installation, Node.js runtime, or network transport. Creating, entering, sharing, updating, or adopting a silo MUST NOT implicitly enable consultation, delegation, agent communication, or additional spending. Those actions remain subject to the currently authorized policy and Cooperation Contracts §5 where applicable.

## 2. Identity, discovery, and ancestry

Every silo MUST have its own `workstate_id`, one current `silo` record, and a separate writable Capsule representation. Copies or replicas of that silo retain its identity. Its record MUST identify the canonical workstate, exactly one immediate parent, an immutable origin pin, purpose, owner, and current base pin. A new silo's origin and base MUST be equal. A parent may be canonical or another silo in the same canonical project.

A **state pin** identifies `workstate_id`, `frontier`, exact governing `specification`, and `capsule_digest` over the complete source Capsule bytes; it MAY also identify a checkpoint and generated-region digest. A generated-region digest MUST NOT substitute for a complete Capsule digest. The source Capsule and the state represented by its frontier MUST be validated before derivation or adoption; a digest alone proves neither a valid projection nor acceptance by the project. A snapshot-only source MUST disclose its omitted-history boundary and source digest under Synchronization and MUST NOT claim full replay evidence.

The parent relation MUST be acyclic, with exactly one parent for each silo. The origin pin and parent identity MUST remain immutable. A receiver MUST validate ancestry to the designated canonical root before claiming a complete hierarchy; a missing ancestor is `unavailable`, not proof of an independent root. Multiple inheritance and automatic parent selection are outside `silo-v1`. Implementations MAY impose and disclose depth or retrieval limits; exceeding one blocks the affected operation with a diagnostic rather than silently truncating ancestry.

The child fork genesis MUST identify its parent pin as external provenance. Parent events retain their original workstate IDs and MUST NOT be relabeled as child events or inserted as unresolved local event parents. A child starts its own event graph and retains or references the pinned parent state under Synchronization's history-completeness rules. Cross-workstate references MUST qualify the source workstate, record ID, and revision; matching local ID strings do not establish identity across forks.

Entry MUST explicitly select and display the current workstate identity, its silo purpose, canonical identity, base, lifecycle, and effective authority limits before dependent mutation. A locator or optional silo catalog is discovery data, not authority. Creating a silo MUST NOT require updating the canonical Capsule or switching the project's default discovery pointer. Registering it in a canonical catalog is a separate authorized canonical change. A host MUST NOT silently substitute a parent or canonical Capsule when the selected silo is unavailable.

## 3. Pinned base and local changes

The effective silo state consists of the validated pinned base plus explicit child additions, replacements, and tombstones. The silo record's `inherited_records` MUST enumerate the exact qualified revision pins selected from the base. It MUST include every record and module dependency necessary for the declared continuation; omission of unrelated material is permitted with an accurate completeness declaration. Retained pins MAY reference immutable packaged or retrievable source material rather than duplicate every byte.

An `overrides` entry MUST identify the inherited pin, operation (`replace` or `tombstone`), reason, and, for replacement, a qualified child record pin. At most one uncontested effective override may apply to an inherited pin. Additions are ordinary child-owned records. Replacements create child-owned records and retain origin provenance; they MUST NOT revise the parent record or erase a competing child revision. Tombstones affect only the child's effective view and preserve history. Omission from the view MUST NOT be interpreted as deletion in any parent or adoption target.

Parent changes MUST NOT automatically change a child's effective state. A base update is an explicit `silo.base_updated` event that pins the expected silo revision, prior base, new base from the same parent identity, and an approved reconciliation of inherited records and local overrides. The event MUST preserve the origin pin and old history, record the responsible actor, rationale, decision reference, dependency changes, and per-override disposition. A changed or missing inherited dependency MUST block the affected continuation until its disposition is recorded. A successor from a different parent requires a new fork identity with provenance to the prior silo.

A reader MUST distinguish historical project decisions inherited at the pinned base from current operational authority. Current host guardrails, authority expiry, revocation, and access restrictions apply immediately to operations; an old base MUST NOT preserve revoked permission or permit evasion of a mandatory guardrail. A silo MAY explore an alternative project constraint only within current operational authority and with the alternative explicitly scoped to that silo.

## 4. Ownership and canonical governance

Project governance distinguishes three responsibilities, which MAY belong to the same principal:

| Responsibility | Scope |
|---|---|
| Project owner | Establish canonical policy, appoint or replace approvers, and delegate bounded authority |
| Silo owner | Manage purpose, local decisions, membership, and lifecycle within granted scope |
| Publisher | Serialize approved changes to a destination Capsule and return publication evidence |

The destination MUST identify its decision owner and accepted policy for adoption. A project MAY appoint component stewards or use a threshold approval policy. Every relied-upon delegation MUST identify grantor, grantee, permitted actions, resources or scope, conditions, expiry or explicit absence of expiry, delegation permission, and revocation basis. Receivers MUST evaluate the delegation chain under current local policy before relying on it. Ownership transfer or policy revision MUST be an explicit accepted decision preserving prior provenance.

A child owner MUST NOT derive authority over a parent or canonical workstate from ancestry, ownership, a role label, or a local approval. A proposal to adopt authority or governance changes MUST undergo the destination's existing policy; it MUST NOT authorize its own acceptance. A role labeled `super-admin` has no special protocol privilege beyond its explicitly accepted grants. Authority conflict or an unavailable authorized decision owner blocks the affected adoption, not unrelated exploration.

Serialization and approval are distinct. A publisher MUST use Capsule §3.2 and Synchronization §9.1 for expected-state checks and recovery. Publication ownership MUST NOT grant authority over the content. COOP-1 may record responsibilities and human decisions and provide cooperating-writer exclusion; it does not authenticate all actors or prevent a bypassing writer. Claims of enforced cross-principal role separation or protected canonical mutation require COOP-3 and the named enforcing path. Below that boundary, the deployment MUST disclose unenforced roles; independently checked authority evidence remains useful without implying protected enforcement.

## 5. Work locations and coordination

Semantic isolation does not imply physical isolation. A silo's `work_location.mode` is `none`, `isolated`, or `shared`. `none` permits planning and Capsule work but claims no isolated implementation location. Any shared writable resource, including a silo Capsule, remains subject to applicable host and coordination policy.

A silo performing guarded work on a work product MUST either use a verified isolated location or use one common atomic collision-control binding that covers every cooperating writer to the shared resource. Worktree names and path spelling alone are not isolation evidence; resource aliases, linked files, generated outputs, and shared services MUST be considered under the declared scope model. An isolated worktree does not isolate a shared database or deployment target.

For `shared` mode, the deployment MUST record the complete common binding identity, resource/scope mapping, atomicity mechanism, and observation of coverage. All participating silos and canonical actors MUST publish and check physical intents in that same binding before a guarded write. Intents MUST retain their originating semantic workstate as qualified provenance while using the common binding's workstate and event graph for admission. Silo-local semantic stores remain separate. Participants MUST NOT union unrelated store histories to manufacture a combined permission, and a local silo lease MUST NOT be treated as a reservation in the common binding.

If no such common binding is available, shared guarded mutation MUST be blocked or explicitly conducted outside an active COOP guarantee under host policy. Cross-binding informational notices, asynchronous mirroring, and separate successful announce operations are insufficient for atomic exclusion. A binding lacking the resource mapping or coverage evidence MUST NOT claim this shared-location capability.

Every selected Cooperation Contract applies to the binding and operations for which it is declared. COOP-1 keeps material decisions human-mediated; COOP-2 adds semantic/integration assurance and optional authorized managed collaboration; COOP-3 adds protected enforcement. Structural silo validation and human-approved adoption do not alone establish COOP-2. Automated semantic compatibility or Coordination readiness claims require the applicable COOP-2 mechanisms and evidence.

## 6. Lifecycle and independent descendants

Silo lifecycle is independent of adoption history:

| From | Event | To | Condition |
|---|---|---|---|
| — | `silo.created` | `active` | Valid fork, base, owner, purpose, and representation |
| `active` | `silo.paused` | `paused` | Owner disposition, checkpoint, and unresolved work recorded |
| `paused` | `silo.resumed` | `active` | Owner disposition and required freshness checks |
| `active`, `paused` | `silo.closed` | `closed` | Authorized closure reason and final checkpoint |

`closed` is terminal; further exploration creates a successor silo. Closure reasons MAY include completed, abandoned, rejected, or superseded. A paused or closed silo MUST NOT start new implementation work; lifecycle administration, receipt recovery, read-only review, and adoption of previously pinned results MAY continue when separately authorized. Pause or closure MUST NOT silently complete intents, release leases, discard uncommitted artifacts, delete files, or claim a successful handoff; each binding's exit rules still apply.

Closing a parent MUST NOT close its children or invalidate their origin pins. Descendants retain their historical base. An unavailable parent representation or decision owner MUST be disclosed separately from lifecycle. A new destination or owner can be approved without rewriting ancestry. Silo deletion, redaction, retention, and artifact removal follow the existing family rules and are not implied by closure.

Partial or repeated adoption MUST NOT automatically pause or close a silo. A closed silo MAY remain a valid source of historical results if their pins, dependencies, and current destination approval can be verified.

## 7. Adoption

**Adoption** is the explicit acceptance of selected results from a silo into canonical state or an ancestor silo. It may publish a proposal as a proposal; it does not inherently accept the proposal's substance. `silo-v1` permits adoption into an ancestor in the same canonical project; arbitrary cross-project adoption and sibling adoption are outside this profile. A source and destination MUST differ.

An adoption record MUST identify source and destination state pins, exact selected record revisions, proposed destination records, qualified source-to-destination mapping, dependency closure evidence, base-divergence observations, intended scopes, destination decision owner and policy reference, publisher, and an idempotency key. It MUST identify bypassed ancestors when the target is not the immediate parent. Bypassing an ancestor requires destination authorization and all applicable approval obligations, but does not require an intermediate adoption, invalidate historical ancestor bases, or authorize writing to those ancestors. Notices MAY be published when authorized.

### 7.1 Dependency closure and identity mapping

Before approval and again before publication, the processor MUST establish that the selected result is causally closed over all references required to interpret or use it at the pinned destination frontier. Each dependency MUST resolve to (a) an included input, (b) an exact existing destination record or artifact, or (c) an explicit qualified source reference retained with its required availability and interpretation rules. Historical source ancestry may remain externally pinned; closure does not require copying the whole source event graph.

Missing dependencies MUST cause the processor to extend the selection, explicitly re-derive the affected result and its references with evidence, or reject it. A closure or reference rewrite that changes the proposed result MUST invalidate prior approval and require approval of the revised proposal. Unknown required modules, contested references, unsupported dependency semantics, or insufficient evidence MUST block adoption; a processor MUST NOT claim closure by inspecting only recognized fields.

New destination records MUST have destination-owned identities and explicit origin pins. Revising an existing destination record MUST use its expected revision and retain the source mapping. Bare ID equality MUST NOT select a destination record. Source events and revisions MUST remain immutable; adoption emits new destination events whose local parents belong to the destination graph, with source pins as external provenance. A dependency cycle MUST either be preserved as a valid combined unit under the owning modules or block adoption; it MUST NOT be broken by silently dropping an edge.

### 7.2 Divergence and evidence

The processor MUST compare the selected results' inherited dependencies and all applicable destination constraints and policies with current destination state. Its `divergence` observations MUST identify each relied-upon pin, the current matching destination pin or its absence, comparison basis, result (`unchanged`, `changed`, `missing`, `contested`, or `unknown`), and disposition. Unrelated parent changes do not by themselves invalidate the selected result. Changed material assumptions require explicit reconciliation and destination-owner disposition; missing or unverifiable required dependencies remain blocking.

Adoption MUST preserve the distinction between proposals, accepted decisions, reports, and verified claims. Acceptance in a source silo MUST NOT imply destination acceptance. Verification evidence MUST retain its original subject, scope, artifact revisions, and environment; if those no longer support the destination claim, the claim MUST be revalidated or explicitly represented as unverified or stale. A clean Git merge or passing source test suite MUST NOT be sufficient evidence of destination semantic compatibility.

### 7.3 Approval, publication, and recovery

Approval MUST bind the exact adoption proposal revision, source pin, destination pin, resulting record mapping, declared scopes, and conditions. The publisher MUST re-evaluate current authority, conditions, applicable COOP decisions, and destination freshness immediately before publication. Any changed expected destination state MUST return `stale_base`; the writer MUST reconcile and obtain approval for a successor proposal rather than apply last-write-wins.

The adopted semantic records and the adoption fact MUST become visible together in one recoverable destination publication using Capsule §3.2. This atomic boundary concerns the destination workstate only. File merges, deployments, and other external changes MUST have separately authorized operations and receipts; a binding MUST NOT claim a transaction spanning them without a mechanism that actually provides it. An adoption depending on external results MUST verify and pin those results before claiming completion.

The publication journal and returned receipt MUST bind the idempotency key, approved proposal revision, prior and resulting whole-Capsule digests, generated-region digests, destination frontier, checkpoint, and publication status. The resulting complete-Capsule digest MUST be stored in the external receipt or journal, not required inside the bytes it hashes. The Capsule's adoption fact identifies the operation and approved proposal; a processor confirms publication using the matching receipt or recovery evidence.

A retry of the same idempotency key and exact request MUST return the original result or recover its pending state. Reuse with a different request MUST be rejected. If a crash leaves publication uncertain, the binding MUST report `pending` and compare the journal's expected and proposed state before classifying it as adopted, not published, or diverged. It MUST NOT repeat uncertain external side effects or issue a success receipt based only on a planned filename. Source or ancestor receipt mirroring is optional and MUST NOT make a confirmed destination adoption appear uncommitted when only that mirroring failed.

### 7.4 Adoption lifecycle

| From | Event | To | Condition |
|---|---|---|---|
| — | `silo_adoption.proposed` | `proposed` | Complete proposal and expected destination pin |
| `proposed` | `silo_adoption.approved` | `approved` | Closure, divergence dispositions, and current scoped approval |
| `approved` | `silo_adoption.started` | `pending` | Durable journal and fresh preconditions |
| `pending` | `silo_adoption.adopted` | `adopted` | Destination publication confirmed by receipt or recovery |
| `proposed`, `approved` | `silo_adoption.staled` | `stale` | Relevant proposal basis changed |
| `proposed` | `silo_adoption.rejected` | `rejected` | Destination decision and reason |
| `proposed`, `approved` | `silo_adoption.cancelled` | `cancelled` | Authorized cancellation |
| `pending` | `silo_adoption.failed` | `failed` | Recovery confirms no adoption; failure evidence retained |

`adopted`, `stale`, `rejected`, `cancelled`, and `failed` are terminal. A changed or retried failed proposal uses a successor record and new key; recovery of the same pending operation retains its key. An uncertain or diverged pending publication MUST remain unresolved until recovery establishes the outcome. Adoption lifecycle observations may live in binding-owned durable state; the confirmed adoption fact belongs in the destination graph. A source observation of that fact retains the destination pin and MUST NOT masquerade as a destination event.

## 8. Record and event representation

The structural schema defines `silo` and `silo_adoption` records, both owned by `urn:awp:sync` with `profile: silo-v1`. Records MUST include `id`, `type`, `module`, `profile`, positive integer `revision`, `status`, `created_by`, and `created_at`. The silo record lives in `snapshot.modules["urn:awp:sync"].silos`; adoption records, when projected in a workstate, live in that module state's `silo_adoptions`. Project governance MAY be recorded as accepted Core decisions and authority declarations referenced by `adoption_policy`; no parallel authority-grant record is introduced.

Profile events MUST use the Core envelope and owning module `urn:awp:sync`. In addition to the lifecycle events above, the profile defines `silo.updated` for purpose, ownership, policy, and override changes and `silo.base_updated` for explicit base reconciliation. An update MUST pin the prior revision, assign the next integer revision, and carry a complete replacement plus required decision or reconciliation evidence. It MUST NOT change immutable identity or origin fields or use `silo.updated` to bypass a lifecycle or base-update condition. Creation uses revision 1. Concurrent non-commuting updates remain contested and MUST block dependent adoption until a recorded Synchronization resolution identifies both outcomes and the selected successor. Transport order and timestamps do not resolve that conflict.

Schema validity checks structural shape only. Cross-record identity, ancestry, dependency closure, authority, location coverage, lifecycle, and publication recovery require profile processing and independent evidence.

### 8.1 Informative examples

The [planning silo fixture](../../../conformance/valid/silo-0.1-planning.json) shows an unaccepted search-feature exploration with its own workstate, owner, pinned canonical base, and no implementation worktree. The [adoption fixture](../../../conformance/valid/silo-0.1-adoption.json) selects one goal and maps it to a new canonical **proposed** goal. Accepting that publication does not approve implementation of the feature. The digest values and evidence identifiers in these standalone structural fixtures are synthetic and do not claim retrievable source history.

For example, `canonical → search exploration → ranking experiment` is a permitted ancestry chain. The ranking experiment can submit a dependency-complete result directly to canonical, identifying search exploration as a bypassed ancestor. Search exploration remains pinned to its historical base and may continue independently. The destination owner decides whether to accept the result; a successful adoption need not close either silo.

## 9. Diagnostics and conformance evidence

Profile processors MUST emit stable diagnostics with code, severity, operation or record subjects, explanation, and recovery. The following codes have severity `error` and block the affected operation:

| Code | Condition |
|---|---|
| `AWP-SILO-PROFILE-UNSUPPORTED` | Required silo processing is unsupported |
| `AWP-SILO-ANCESTRY-INVALID` | Cyclic, ambiguous, mismatched, or unsupported ancestry |
| `AWP-SILO-BASE-UNAVAILABLE` | Required pinned source cannot be retrieved or validated |
| `AWP-SILO-REVISION-CONFLICT` | Immutable field changed or prior revision contested |
| `AWP-SILO-TRANSITION-INVALID` | Lifecycle or base-update precondition fails |
| `AWP-SILO-SHARED-SCOPE-UNGUARDED` | Shared guarded mutation lacks common atomic coverage |
| `AWP-SILO-DEPENDENCY-INCOMPLETE` | Required adoption dependency unresolved |
| `AWP-SILO-DIVERGENCE-UNRESOLVED` | Material difference lacks valid disposition |
| `AWP-SILO-AUTHORITY-INSUFFICIENT` | Current destination policy does not permit adoption |
| `AWP-SILO-STALE-BASE` | Destination changed since the approved proposal |
| `AWP-SILO-IDEMPOTENCY-CONFLICT` | One key reused for different requests |
| `AWP-SILO-PUBLICATION-UNCONFIRMED` | Publication or recovery remains uncertain |

A profile claim MUST state supported roles (`silo-reader`, `silo-writer`, `silo-adopter`), representation and dependency coverage, any active COOP contract, authority enforcement, and the tested operating envelope. Writer claims require reader behavior; adopter claims additionally require closure, destination approval, atomic publication, and recovery. A structural schema validator alone MUST NOT claim these roles.

Before an operational claim, fixtures MUST demonstrate: reproducible pinned derivation; parent changes leaving children unchanged; explicit base reconciliation; local override and tombstone isolation; duplicate IDs across forks; missing and cyclic ancestry; partial adoption with missing dependencies; external historical dependency retention; changed constraints and stale evidence; proposal approval invalidation; repeated partial adoption without closure; closed parent with active child; direct ancestor adoption; unauthorized self-approval; shared-location collisions including aliases; independent locations with shared external resources; concurrent destination publishers; retry and crash recovery; unknown required semantics; and preservation of disabled collaboration and declared budgets.

The initial repository assets provide specification and structural examples only. They do not implement a silo runtime, dependency-closure evaluator, shared-resource binding, or adoption publisher and do not establish an operational conformance claim. Multiple inheritance, automatic cascading reconciliation, destructive silo deletion, and arbitrary cross-project adoption are deferred.
