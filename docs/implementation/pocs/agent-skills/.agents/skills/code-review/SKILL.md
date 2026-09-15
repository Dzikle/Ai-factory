---
name: code-review
description: Review a proposed code change for correctness, regressions, security, maintainability, and missing deterministic validation. Use after implementation when the reviewer must remain independent from the author.
license: MIT
compatibility: Requires read-only repository and diff access; may run explicitly approved deterministic checks.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: medium
  ai-factory/required-capabilities: '["repo.read","git.diff.read","validation.run"]'
  ai-factory/roles: '["reviewer"]'
  ai-factory/eval-refs: '["evals/code-review-v1"]'
---

# Code review

Review the change as an independent gate, not as a co-author.

1. Read the task acceptance criteria, governing repository instructions, and
   exact diff.
2. Trace changed behavior through callers, state transitions, persistence,
   permission boundaries, error paths, and tests.
3. Prefer deterministic evidence: reproduce the relevant checks and distinguish
   executed results from inferred risk.
4. Rank findings by user/system impact. Include an exact file and line, the
   failing scenario, and the smallest safe correction.
5. Check that the implementation did not weaken authorization, provenance,
   idempotency, retry bounds, source-of-truth boundaries, or observability.
6. If no blocking finding exists, say so explicitly and list residual test gaps.

Do not modify the implementation or approve your own prior work. A failed review
returns the task to implementation while preserving the review evidence.
