# Skills Registry

Skills are canonical, reusable, model-agnostic procedures describing **how a class of work should be performed**.

They are separate from agent identity, project context, memory, and model/provider implementation.

## Canonical packaging direction

AI Factory should align with the external **Agent Skills** standard (`agentskills/agentskills`) instead of inventing an incompatible skill format.

Preferred package:

```text
skills/<skill-id>/
  SKILL.md
  scripts/        # optional
  references/     # optional
  assets/         # optional
```

AI Factory may add a small compatible sidecar/extension for system-specific metadata such as:

```yaml
ai_factory:
  version: 0.1.0
  status: experimental
  compatible_agents:
    - architect
    - developer
    - reviewer
  requires_capabilities:
    - repo.read
  optional_capabilities:
    - code.graph.search
  risk: read_only
  eval_suites:
    - repository-discovery-01
```

Do not replace the portable skill format merely to encode metadata that can live alongside it.

## Principles

- Load only skills relevant to the current task.
- Prefer composable skills over giant role manuals.
- Keep provider-specific mechanics in runtime adapters where possible.
- Preserve portability across Codex/Claude/OpenCode/Gemini and future harnesses.
- Version/evaluate material skill changes.
- Promote recurring lessons into skills only after the lesson is stable enough to generalize.
- Mature repeated skill reasoning toward tools/tests/deterministic enforcement.
- Reuse maintained external skills where appropriate instead of recreating equivalent procedures.

## Progressive loading

Avoid context bloat by loading only what is required:

```text
skill metadata / short description
→ SKILL.md procedure
→ references/scripts/assets only when needed
```

The exact runtime mechanics may differ by harness, but the canonical skill content should remain portable.

## Adoption-spike specimens

The adoption spike includes two representative portable skill specimens:

- `repository-discovery`
- `code-review`

They are stored under `docs/implementation/pocs/agent-skills/` and were validated
both as directly loaded `SKILL.md` procedures and through an indexed metadata-first
catalog flow. A live two-harness execution remains an admission test before the
first production skill is promoted; the file-format POC alone does not claim
behavioral parity between harnesses.

## Later candidate skills

Create these only as real tasks justify them:

- git-worktree / workspace operation
- implementation
- deterministic-testing
- documentation-update
- browser-testing
- responsive-ui-audit
- accessibility-audit
- Java/Spring
- OpenSearch
- database-migration
- Terraform/AWS

## Promotion path

```text
incident / lesson
→ repeated pattern
→ canonical skill update
→ reusable tool/check
→ deterministic enforcement where practical
```
