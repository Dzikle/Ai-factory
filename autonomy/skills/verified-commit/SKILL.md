---
name: verified-commit
description: Prepare a verified, reviewable commit on the assigned task branch. Use after implementation and deterministic validation pass.
license: MIT
compatibility: Requires workspace write access and the pinned validation environment.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: medium
  ai-factory/required-capabilities: '["repo.read","repo.write","git.read","git.diff.read","validation.run"]'
  ai-factory/roles: '["developer"]'
  ai-factory/eval-refs: '["evals/verified-commit-v1"]'
---

# Verified commit

Commit only what the task allows, only after deterministic evidence passes.

## Trigger / intent

Implementation is complete in the worktree and the task calls for a checkpoint commit.

## Prerequisites

- `repository-preflight` passes: correct branch, expected revision, clean except your own changes.
- Only task-allowed paths differ; unrelated local work is untouched.

## Read-only preflight

1. List changed paths and confirm each is inside the task's allowed paths.
2. Review the full diff for secrets, credentials, or private operator state.

## Exact existing command

```text
python -m milestone3.check
```

Run in the pinned environment (`PYTHONPATH=/paperclip/m1-python-libs:$PWD python3`). Commit only when it passes.

## Expected evidence

Passing check output, the exact file list committed, and the commit message recorded in the handoff.

## Failure recovery

- Failing checks: fix and re-run; never commit red work to request review.
- Unexpected paths in the diff: stop and report rather than widening the commit.

## Authorization boundary

Commits stay on the assigned task branch. Never push, merge, publish, deploy, or rewrite another agent's commits.

## Related skill

`repository-preflight` — the read-only check that precedes every commit.
