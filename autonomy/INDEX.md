# Autonomy Index

This is the context router for AI Factory. Load the smallest relevant set of documents for the current task.

## Start here

- Product goals and success criteria → [`GOALS.md`](GOALS.md)
- System-wide governance and lifecycle → [`GOVERNANCE.md`](GOVERNANCE.md)
- Full architecture → [`../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`](../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md)
- Reuse-first/open-source policy → [`../docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md`](../docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md)
- State/storage boundaries → [`../docs/architecture/STATE_AND_STORAGE.md`](../docs/architecture/STATE_AND_STORAGE.md)
- OpenSearch knowledge fabric → [`../docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md`](../docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md)
- MCP/capability model → [`../docs/architecture/MCP_AND_CAPABILITY_MODEL.md`](../docs/architecture/MCP_AND_CAPABILITY_MODEL.md)
- Current adoption spike → [`../docs/implementation/ADOPTION_SPIKE.md`](../docs/implementation/ADOPTION_SPIKE.md)
- Completed adoption matrix → [`../docs/decisions/ADOPTION_MATRIX.md`](../docs/decisions/ADOPTION_MATRIX.md)
- Selected physical V1 architecture → [`../docs/decisions/V1_ADOPTION_ARCHITECTURE.md`](../docs/decisions/V1_ADOPTION_ARCHITECTURE.md)
- V1 implementation contract → [`../docs/implementation/IMPLEMENTATION_KICKOFF.md`](../docs/implementation/IMPLEMENTATION_KICKOFF.md)

## Specialist roles

- Role catalog → [`agents/README.md`](agents/README.md)
- Orchestrator → `agents/orchestrator.md`
- Researcher → `agents/researcher.md`
- Architect → `agents/architect.md`
- Developer → `agents/developer.md`
- Reviewer → `agents/reviewer.md`
- QA/UX → `agents/qa-ux.md`

## System registries

- Skills → `skills/README.md`
- Capabilities and MCP/tool providers → `capabilities/README.md`
- Models and routing → `models/README.md`
- Workflows → `workflows/README.md`
- Policies → `policies/README.md`
- Evaluation framework → `evals/README.md`
- Project overlays → `projects/README.md`
- Versioned Git contracts → [`contracts/README.md`](contracts/README.md)

## Current phase rule

Phase 0.5 and the Paperclip Milestone 0 dependency gate are complete. During
Phase 1, agents must follow the selected integration boundaries. The first
Milestone 1 contract slice does not activate runtime permissions or workflows.

Changes that introduce a second task/workflow, MCP policy, memory, sandbox
lifecycle, or graph authority require a new ADR and evidence that the existing
selected boundary cannot satisfy the requirement.

## Context-loading rule

Do not load all documents simply because they exist.

Start with:

```text
Task
+ AGENTS.md
+ GOALS / governance as needed
+ current specialist role
```

Then resolve only the skills, capabilities, project documents, memories, task history, and code references needed for the task.

Runtime context retrieval should eventually be handled by the Context Resolver using OpenSearch multi-search plus direct source verification.
