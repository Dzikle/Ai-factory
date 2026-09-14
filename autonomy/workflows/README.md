# Workflows

Workflows are durable state-machine paths, not conversational scripts.

## Baseline V1 state machine

```text
QUEUED
  ↓
TRIAGE
  ↓
[RESEARCH]
  ↓
[ARCHITECTURE]
  ↓
IMPLEMENTATION
  ↓
VALIDATION
  ↓
REVIEW
  ↓
[QA]
  ↓
INTEGRATION
  ↓
DONE
```

Optional stages are selected by task classification.

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

## Complexity paths

### Simple
Developer → deterministic validation → optional light review.

### Normal
Developer → validation → reviewer → QA if behavior is user-facing.

### High-risk / novel
Research if needed → architect → developer → validation → strong independent review → relevant QA/security → integration validation.

## Continuity

Every transition must be reconstructable from durable state. The next model should be able to resume from the recorded `next_action` without needing the previous chat session.
