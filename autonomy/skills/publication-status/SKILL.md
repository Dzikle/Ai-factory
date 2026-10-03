---
name: publication-status
description: Inspect an exact publication candidate without pushing, or publish only the owner-approved candidate through the existing command. Publication itself is operator-only.
license: MIT
compatibility: Status inspection is read-only; publication requires the existing exact approval inputs.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: medium
  ai-factory/required-capabilities: '["repo.read","git.read"]'
  ai-factory/roles: '["orchestrator"]'
  ai-factory/eval-refs: '["evals/publication-status-v1"]'
---

# Publication status

Check what would be published before anything leaves the repository.

## Trigger / intent

A candidate is accepted and its publication or integration boundary is in question.

## Prerequisites

- The exact candidate commit/tree identity and the recorded owner approval.
- The existing publication command; no hand-built push sequence.

## Read-only preflight

1. Run preflight to inspect the exact candidate without pushing.
2. Confirm the candidate matches the approved commit/tree byte for byte.

## Exact existing command

```text
python -m milestone2.publish preflight
python -m milestone2.publish publish
```

`preflight` never pushes. `publish` publishes only the exact owner-approved candidate and records evidence; it is operator-or-authorized-orchestrator only.

## Expected evidence

Preflight output naming the candidate, plus the publication receipt after an authorized publish.

## Failure recovery

- Candidate mismatch: stop; no old approval qualifies a corrected candidate.
- Missing approval: stop at the boundary with a ready-to-act report.

## Authorization boundary

Read-only unless an operator supplies the existing exact publication approval inputs. This skill grants no agent runtime publish right; discovery of the command does not change stage restrictions.

## Related skill

`review-resolution` — clears review findings before a candidate becomes publishable.
