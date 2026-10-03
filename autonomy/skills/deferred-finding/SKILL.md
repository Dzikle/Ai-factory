---
name: deferred-finding
description: Capture an incidental discovery as a low-cost deferred finding without widening the current task. Use when useful work is out of scope.
license: MIT
compatibility: Read-only capture; creates no task, branch, or workspace by itself.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: low
  ai-factory/required-capabilities: '["repo.read","artifact.write"]'
  ai-factory/roles: '["developer","reviewer","qa"]'
  ai-factory/eval-refs: '["evals/deferred-finding-v1"]'
---

# Deferred finding

Record out-of-scope observations so they triage later instead of expanding now.

## Trigger / intent

An incidental discovery arises that the current task must not absorb.

## Prerequisites

- The observation, the evidence for it, and the reason it is out of scope.
- A severity and confidence estimate; duplicates are linked, not re-filed.

## Read-only preflight

1. Confirm the finding is genuinely outside the authorized paths and objective.
2. Check existing findings for the same fingerprint before writing.

## Exact existing command

```text
python -m milestone2.task status AIF-61
```

Status confirms which task owns the observation; the finding itself is emitted in the lifecycle's deferred-finding record shape (`project_id`, `affected_components`, `summary`, `origin_task_ids`, `fingerprint`).

## Expected evidence

One finding record following `observation -> deferred finding -> triaged candidate -> approved task`, with origin task IDs preserved.

## Failure recovery

- A duplicate fingerprint: append the new origin task ID instead of creating a second record.
- A finding that blocks the current task: escalate as an unresolved item, not as silent scope growth.

## Authorization boundary

Emitting a finding never creates a full task, branch, or workspace automatically, and never authorizes the extra work it describes.

## Related skill

`scoped-audit` — the bounded pass that often surfaces deferred findings.
