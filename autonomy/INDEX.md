# Autonomy Index

This is the context router for AI Factory. Load the smallest relevant set of documents for the current task.

## Start here

- Product goals and success criteria → [`GOALS.md`](GOALS.md)
- System-wide governance and lifecycle → [`GOVERNANCE.md`](GOVERNANCE.md)
- Full architecture → [`../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`](../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md)
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
