# AI Factory — State and Storage Architecture

**Status:** Canonical V1 decision

This document makes the persistence boundaries explicit. Each store has one primary responsibility. Do not collapse them for convenience.

## 1. Storage roles

| Store | Primary responsibility | Authority |
| --- | --- | --- |
| PostgreSQL | durable control/task execution state | execution truth |
| Git + canonical Markdown/YAML | current system/project definitions | canonical configuration / project truth |
| MemPalace | experiential and episodic memory | historical knowledge, not truth |
| OpenSearch 3.x | rebuildable search projection across organizational knowledge | projection only |
| Artifact store | large task outputs, reports, screenshots, traces, patches | artifact source |
| Code graph provider | structural code relationships | derived structural index |
| Logs/traces | detailed execution evidence | operational evidence |

## 2. PostgreSQL control database

V1 should use PostgreSQL as the durable control-plane database.

The database must be able to reconstruct what the system is doing without relying on an active LLM session.

Minimum V1 entities:

```text
task
  id
  project_id
  objective
  classification
  state
  priority
  created_at
  updated_at
  next_action
  retry_budget
  token_budget
  cost_budget

stage
  task_id
  stage_type
  state
  attempt
  started_at
  completed_at
  agent_role
  model_provider
  model_id

agent_run
  id
  task_id
  stage_id
  agent_role
  model_provider
  model_id
  status
  input_context_ref
  output_artifact_ref
  token_usage
  estimated_cost
  started_at
  completed_at

operation_journal
  id
  task_id
  operation_type
  idempotency_key
  status
  external_id
  started_at
  completed_at

artifact_ref
  id
  task_id
  type
  uri
  checksum
  metadata

review_finding
  id
  task_id
  stage_id
  severity
  category
  status
  description
  provenance

event
  id
  task_id
  event_type
  payload
  created_at
```

Exact schemas and migrations are implementation work, but the responsibility split is canonical.

## 3. State machine

Baseline task flow:

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

Exceptional states:

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

A new process/model must be able to read PostgreSQL and determine the correct next action.

## 4. PostgreSQL is not the search fabric

Do not turn the control DB into the cross-organizational retrieval engine.

PostgreSQL stores authoritative execution state. Relevant task/run/review/event metadata is projected asynchronously into OpenSearch for discovery and analysis.

The OpenSearch projection can be deleted and rebuilt without damaging task continuity.

## 5. Transactional events / outbox

Prefer a transactional outbox pattern for durable state changes that must be projected to other systems.

Example:

```text
PostgreSQL transaction
  update task state
  append event/outbox record
        ↓
projection worker
        ↓
OpenSearch / telemetry / notifications
```

Do not make successful OpenSearch indexing a prerequisite for committing task-state transitions.

## 6. Artifacts

Large or binary outputs do not belong in PostgreSQL or MemPalace.

Use an artifact store for:

- browser screenshots/video;
- Playwright traces;
- large logs;
- patches/diffs;
- benchmark reports;
- research reports;
- reviewer reports;
- generated archives.

PostgreSQL stores stable references and metadata.

## 7. MemPalace boundary

MemPalace stores reusable experience, such as:

- incidents/root causes;
- rejected approaches and reasons;
- non-obvious repository behavior;
- recurring QA patterns;
- specialist lessons.

It does **not** own:

- current task state;
- current permissions;
- current project configuration;
- canonical architecture;
- operation idempotency.

Useful memory metadata may be projected into OpenSearch with a pointer back to the original memory.

## 8. Rebuildability rule

The system must survive loss of OpenSearch indexes and active model sessions.

Durable recovery sources are:

```text
PostgreSQL
Git/canonical manifests
MemPalace
artifact storage
operation journal
```

OpenSearch and code-graph indexes must be rebuildable derived state.
