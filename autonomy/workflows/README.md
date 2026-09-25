# Workflows

Workflows are durable state-machine paths, not conversational scripts.

The stages below describe engineering semantics. In V1, Paperclip is the sole
runtime state owner: Developer is the issue assignee; deterministic validation,
Reviewer, optional QA/UX, and human integration approval map to ordered native
`IssueExecutionPolicy` review/approval participants. See the live Milestone 1.2
policy probe in `docs/implementation/IMPLEMENTATION_KICKOFF.md`. This document
does not authorize a second implementation state machine.

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
