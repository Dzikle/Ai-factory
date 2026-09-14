# Skills Registry

Skills are canonical, reusable, model-agnostic procedures describing **how a class of work should be performed**.

They are separate from agent identity, project context, memory, and model/provider implementation.

## Principles

- Load only skills relevant to the current task.
- Prefer composable skills over giant role manuals.
- Keep provider-specific mechanics in runtime adapters where possible.
- Version skills and evaluate material changes.
- Promote recurring lessons into skills only after the lesson is stable enough to generalize.
- Mature repeated skill reasoning toward tools/tests/deterministic enforcement.

## Suggested skill package

```text
skills/<skill-id>/
  SKILL.md
  manifest.yaml
```

Example manifest:

```yaml
id: repository-discovery
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
```

## Loading levels

Avoid context bloat by supporting layered material:

```text
manifest / summary
→ quick procedure
→ full reference only when needed
```

## Early candidate skills

Do not create all of these immediately; add when implementation needs them:

- repository-discovery
- git-worktree
- implementation
- code-review
- deterministic-testing
- documentation-update
- browser-testing
- responsive-ui-audit
- accessibility-audit
- Java/Spring
- OpenSearch
- database-migration
- Terraform/AWS
