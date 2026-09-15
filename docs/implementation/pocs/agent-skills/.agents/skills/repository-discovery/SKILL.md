---
name: repository-discovery
description: Discover an unfamiliar software repository's structure, governing instructions, build system, tests, and architectural entry points. Use before planning or changing a repository that has not yet been mapped.
license: MIT
compatibility: Requires read-only filesystem access, Git metadata access, and a recursive text-search tool.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: low
  ai-factory/required-capabilities: '["repo.read","repo.search","git.read"]'
  ai-factory/roles: '["researcher","architect","developer","reviewer","qa"]'
  ai-factory/eval-refs: '["evals/repository-discovery-v1"]'
---

# Repository discovery

Build a concise, evidence-backed map before proposing changes.

1. Read the repository's governing agent/instruction file before other work.
2. Inspect tracked files with a bounded file listing; exclude generated/vendor
   directories unless they are directly relevant.
3. Identify languages, package/build manifests, test entry points, CI workflows,
   deployment definitions, architecture records, and ownership boundaries.
4. Read the smallest set of entry points that explains the requested area.
5. Record uncertainty as a question or verification task; do not infer behavior
   from filenames alone.
6. Report the current branch/revision and unrelated working-tree changes before
   edits.

Return:

- governing constraints;
- component and data-flow map;
- build/test commands supported by repository evidence;
- likely change surface and risks;
- unresolved questions with exact file pointers.

Do not write files, install dependencies, or access the network under this skill
unless the task separately grants those capabilities.
