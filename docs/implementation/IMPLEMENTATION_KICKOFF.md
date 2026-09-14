# AI Factory — Implementation Kickoff Contract

You are implementing the system defined by `docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md` and the canonical rules under `autonomy/`.

Treat those documents as architectural source of truth unless repository reality proves a detail must be adapted. If adaptation is required, document the conflict and proposed decision instead of silently deviating.

## Objective

Build the smallest durable V1 that proves:

```text
task
→ durable state
→ agent selection
→ skill/capability resolution
→ bounded context retrieval
→ isolated execution
→ deterministic validation
→ independent review
→ persisted outcome
→ OpenSearch projection
→ resumability
```

Do **not** implement the complete imagined end-state platform in one pass.

## First work package

Inspect the repository and produce an implementation plan for:

1. canonical repository/module structure;
2. durable Task model and state machine;
3. logical agent registry for Orchestrator, Researcher, Architect, Developer, Reviewer, QA/UX;
4. canonical skill registry with lazy/selective loading;
5. capability registry and permission model;
6. provider/model adapter boundary;
7. Git worktree lifecycle for coding tasks;
8. event/telemetry schema from day one;
9. OpenSearch 3.x knowledge projection schema and indexing boundary;
10. clear integration boundaries for MemPalace and one code-graph provider.

## Constraints

- LLM sessions are disposable; durable state lives outside the model.
- Do not use an agent where deterministic code is sufficient.
- OpenSearch is a rebuildable projection, never canonical truth.
- MemPalace is experiential memory, never canonical truth.
- Git/canonical docs represent current project truth.
- Task storage represents execution truth.
- Permissions must be enforced outside prompts.
- Retries are bounded.
- External side effects must be idempotent/journaled.
- Skills are model-agnostic.
- Tool/MCP access follows least privilege.
- Specialize primarily through skills, not dozens of agent types.
- Use explicit routing policy before learned routing.
- Do not implement autonomous self-modification in V1.
- Instrument the system so cost per accepted correct task can be measured.

## Design bias

When deciding whether to add another agent, service, abstraction, MCP wrapper, provider, memory class, or datastore, prefer the simpler design until real usage demonstrates the need.

The system should become more sophisticated because of measured friction, not because future complexity is imaginable.

## Deliverables before substantial implementation

Produce and commit:

1. current-repository assessment;
2. proposed module/package structure;
3. Task state-machine definition;
4. core persistent schemas;
5. agent/skill/capability manifest formats;
6. OpenSearch index/alias design;
7. runtime sequence diagram for one code-changing task;
8. V1 milestone breakdown;
9. risks, unknowns, and architecture decisions requiring approval;
10. explicit list of deferred post-V1 features.

After the plan is internally consistent, begin the first vertical slice.

## V1 completion test

A real coding task must be able to start, lose its active model/session, and later continue correctly from durable state with enough selectively retrieved context to complete deterministic validation and independent review.

If that cannot be demonstrated, V1 is not complete.
