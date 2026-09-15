# AI Factory — State and Storage Architecture

**Status:** Canonical V1 architecture; physical owners selected by the adoption spike

This document defines responsibility and authority boundaries. It does **not** require AI Factory to build every datastore or workflow engine itself.

The most important rule is:

> Exactly one system owns authoritative operational task/execution state.

Paperclip is adopted as the control plane; its durable database/state model owns
this role. Do not build a second authoritative AI Factory task database beside
it.

## 1. Storage roles

| Logical store / owner | Primary responsibility | Authority |
| --- | --- | --- |
| Paperclip control plane | durable task/run/execution state | execution truth |
| Git + canonical Markdown/YAML | current system/project definitions | canonical configuration / project truth |
| MemPalace | experiential and episodic memory | historical knowledge, not current truth |
| OpenSearch 3.x | rebuildable search projection across organizational knowledge | projection only |
| Artifact store | large task outputs, reports, screenshots, traces, patches | artifact source |
| Code graph provider | structural code relationships | derived structural index |
| Logs/traces | detailed execution evidence | operational evidence |

## 2. Control-plane persistence

The control plane must persist enough durable state to reconstruct what the system is doing without relying on an active LLM session.

Required logical information includes:

```text
task / issue
  id
  project
  objective
  classification
  state
  priority
  next action / assignment
  retry/budget information
  timestamps

run / execution attempt
  task
  logical agent role
  model/provider/runtime
  status
  workspace/session reference
  token/cost/latency telemetry
  started/completed timestamps

workspace
  task/project binding
  repository
  branch/worktree/runtime reference
  base/current revision

operation journal / side-effect evidence
  operation type
  idempotency key
  status
  external id

artifact reference
  task/run
  type
  URI/checksum/metadata

review / QA finding
  severity/category/status
  provenance

event / activity
  actor
  task/run
  type
  timestamp
  payload/ref
```

These are architectural data requirements, not a mandate to recreate the schema if the selected control plane already stores equivalent information.

### Paperclip selection

The adoption spike determined that Paperclip's tasks/issues, agent runs,
workspaces, budgets/costs, activities, approvals, and execution state satisfy
these requirements directly or through bounded adapters and adoption gates.

```text
Paperclip durable state
    = execution truth
```

AI Factory may still project normalized copies into OpenSearch for search/analytics, but those copies are not authoritative.

### DBOS replacement fallback

If Paperclip fails its pinned-release continuity gates, DBOS may be evaluated as
part of a mutually exclusive replacement control plane.

Do not operate multiple workflow engines as competing authorities.

## 3. State-machine contract

Regardless of physical implementation, AI Factory requires equivalent workflow semantics:

```text
QUEUED
→ TRIAGE
→ [RESEARCH]
→ [ARCHITECTURE]
→ IMPLEMENTATION
→ VALIDATION
→ REVIEW
→ [QA]
→ INTEGRATION
→ DONE
```

Exceptional semantics include:

```text
BLOCKED
WAITING_QUOTA
WAITING_DEPENDENCY
RETRY
ESCALATE
REVIEW_FAILED
QA_FAILED
CANCELLED
```

The selected control plane may use different internal status names. Provide a mapping rather than duplicating the workflow merely to preserve naming.

A fresh process/model invocation must be able to determine the correct next action from durable state.

## 4. Control state is not the knowledge/search fabric

Do not turn the operational database into the cross-organizational retrieval engine.

The control plane owns current execution state. Relevant tasks, runs, reviews, events, telemetry, goals, and outcomes are projected asynchronously into OpenSearch for discovery, context assembly, and analysis.

The OpenSearch projection can be deleted and rebuilt without damaging task continuity.

## 5. Projection/outbox boundary

Prefer durable event/activity hooks or transactional outbox semantics from the selected control plane.

Conceptually:

```text
authoritative state change
        ↓
durable event / outbox / plugin event
        ↓
AI Factory projection adapter
        ↓
OpenSearch
```

OpenSearch indexing failure must not roll back valid task-state transitions.

Projection must be retryable, idempotent, and replayable.

If Paperclip exposes suitable activity/event/plugin hooks, use them rather than duplicating writes into another task database solely to obtain an outbox.

## 6. Artifact storage

Large or binary outputs do not belong in task rows or memory stores.

Use the selected artifact/storage provider for:

- screenshots/video;
- browser/Playwright traces;
- large logs;
- patches/diffs;
- benchmark reports;
- research reports;
- reviewer reports;
- generated archives.

The authoritative control plane stores stable references and metadata when appropriate.

Prefer an adopted platform's storage interface if it satisfies the requirement; add an AI Factory artifact adapter rather than a competing storage subsystem.

## 7. Memory boundary — MemPalace selected

The bake-off decision is:

```text
SELECTED: MemPalace primary experiential memory + OpenSearch projection
DEFERRED FALLBACK: OpenSearch Agentic Memory primary memory
REJECTED: two concurrent primary memory authorities
```

MemPalace may own reusable experience such as:

- incidents/root causes;
- rejected approaches and reasons;
- non-obvious repository behavior;
- recurring QA patterns;
- specialist lessons/diaries.

Memory must **not** own:

- current task state;
- current permissions;
- current project configuration;
- canonical architecture;
- operation idempotency.

## 8. Rebuildability rule

The system must survive loss of OpenSearch indexes and active model sessions.

Durable recovery sources are the selected authoritative systems:

```text
control-plane database/state
Git/canonical manifests
MemPalace
artifact storage
side-effect/operation evidence
```

OpenSearch and code-graph indexes remain rebuildable derived state.

## 9. No duplicate truth

Before adding a datastore, answer:

```text
What unique authoritative fact lives here?
Why can the existing selected component not own it?
Is this authoritative state or only a projection/cache/index?
How is conflict resolved?
```

If no unique authoritative responsibility exists, do not add the datastore.
