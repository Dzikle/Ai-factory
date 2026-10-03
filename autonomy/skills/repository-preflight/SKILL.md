---
name: repository-preflight
description: Verify the assigned workspace is clean, on the recorded branch, and at the expected revision before implementing. Use at task start and before every commit.
license: MIT
compatibility: Requires read-only repository and Git metadata access; makes no writes.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: low
  ai-factory/required-capabilities: '["repo.read","git.read","git.diff.read"]'
  ai-factory/roles: '["developer","reviewer","qa"]'
  ai-factory/eval-refs: '["evals/repository-preflight-v1"]'
---

# Repository preflight

Confirm the workspace matches Paperclip's recorded branch and revision before touching code.

## Trigger / intent

Starting implementation, resuming after interruption, or preparing a commit in a Paperclip task worktree.

## Prerequisites

- The assigned worktree path and Paperclip-recorded branch/revision.
- No running task of your own that already owns uncommitted changes.

## Read-only preflight

1. Confirm the current branch equals the Paperclip-recorded branch.
2. Confirm the worktree is clean (`git status --short` shows nothing).
3. Confirm HEAD equals the recorded revision; never fast-forward someone else's task branch yourself.

## Exact existing command

```text
python -m milestone2.task status AIF-61
python -m milestone3.check
```

`status` reads Paperclip's authoritative progress; it does not poll, advance stages, or read private run logs.

## Expected evidence

Branch name, HEAD commit/tree, and clean `git status` recorded in the handoff note.

## Failure recovery

- Dirty worktree: stop and report; do not stash or reset another agent's work.
- Branch/revision mismatch: re-read the Paperclip issue; if the recorded branch moved, resume from Paperclip state, not from memory.

## Authorization boundary

Read-only. This skill never commits, pushes, merges, publishes, deploys, or restarts services.

## Related skill

`verified-commit` — prepares a commit only after this preflight passes.
