---
name: review-resolution
description: Address independent review findings with candidate-linked evidence. Use when a reviewer requests changes; never dismiss findings without proof.
license: MIT
compatibility: Requires read access and the pinned validation environment; makes no publication decisions.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: low
  ai-factory/required-capabilities: '["repo.read","git.read","git.diff.read","validation.run","knowledge.search"]'
  ai-factory/roles: '["reviewer"]'
  ai-factory/eval-refs: '["evals/review-resolution-v1"]'
---

# Review resolution

Resolve each finding against the same candidate lineage, with evidence.

## Trigger / intent

A reviewer returned findings on a candidate commit/tree.

## Prerequisites

- The finding list, each tied to the candidate revision it was raised against.
- The verification digest for that same candidate.

## Read-only preflight

1. Confirm every finding names the current candidate; stale findings are re-checked, not assumed.
2. Reproduce each finding against the candidate before changing code.

## Exact existing command

```text
python -m milestone2.task status AIF-61
python -m milestone3.check
```

Status shows the authoritative stage; the pinned check re-proves the candidate after repair.

## Expected evidence

Per-finding resolution notes naming the fix commit, re-run digest, and reviewer re-verdict.

## Failure recovery

- A finding that does not reproduce: record the reproduction attempt and ask for clarification; never close it silently.
- Repair budget exhausted: produce one durable blocked outcome with evidence and the required next decision.

## Authorization boundary

Findings are never dismissed without candidate-linked evidence. No finding may weaken `milestone2.publish` owner approval or approve integration by itself.

## Related skill

`verified-commit` — records each bounded repair as its own verified commit.
