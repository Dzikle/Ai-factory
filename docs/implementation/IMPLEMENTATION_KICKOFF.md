# AI Factory — Implementation Kickoff Contract

You are implementing the system defined by:

- `docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`
- `docs/architecture/STATE_AND_STORAGE.md`
- `docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md`
- `docs/architecture/MCP_AND_CAPABILITY_MODEL.md`
- the canonical rules under `autonomy/`

Treat those documents as architectural source of truth unless repository reality proves a detail must be adapted. If adaptation is required, document the conflict and proposed decision instead of silently deviating.

## Canonical V1 infrastructure decisions

The following are already decided and should not be reopened without evidence:

- **PostgreSQL** is the durable control/task execution database and execution source of truth.
- **OpenSearch 3.x** is introduced early as a separate rebuildable organizational knowledge/search projection, independent from any product-search cluster.
- **OpenSearch MCP** is the primary agent-facing retrieval interface for the knowledge fabric, including filtered search and multi-search/context composition.
- **MemPalace** is the experiential/episodic memory layer, not canonical truth or task state.
- **One code-graph provider** is used in V1 for structural code discovery; do not operate overlapping graph systems without measured value.
- **Git/canonical Markdown/YAML** remains current system/project truth.
- **Artifact storage** owns large task outputs; PostgreSQL stores references.
- **Logs/traces** are operational evidence; they do not replace durable task state.

## Objective

Build the smallest durable V1 that proves:

```text
task
→ PostgreSQL durable state
→ agent selection
→ skill/capability resolution
→ OpenSearch MCP bounded context retrieval
→ isolated execution
→ deterministic validation
→ independent review
→ persisted outcome/artifacts
→ OpenSearch projection
→ resumability
```

Do **not** implement the complete imagined end-state platform in one pass.

## First work package

Inspect the repository and produce an implementation plan for:

1. canonical repository/module structure;
2. PostgreSQL durable Task model, operation journal, events/outbox, artifacts references and state machine;
3. logical agent registry for Orchestrator, Researcher, Architect, Developer, Reviewer, QA/UX;
4. canonical skill registry with lazy/selective loading;
5. capability registry, permission model, and OpenSearch MCP integration boundary;
6. provider/model adapter boundary;
7. Git worktree lifecycle for coding tasks;
8. event/telemetry schema from day one;
9. OpenSearch 3.x versioned index + alias design and projection workers;
10. Context Resolver using bounded filtered/hybrid multi-search;
11. clear integration boundaries for MemPalace and one code-graph provider.

## Constraints

- LLM sessions are disposable; durable state lives outside the model.
- Do not use an agent where deterministic code is sufficient.
- PostgreSQL is execution truth; OpenSearch does not own task state.
- OpenSearch is a rebuildable projection, never canonical truth.
- OpenSearch indexing failure must not prevent PostgreSQL state commits; prefer outbox/replayable projection.
- MemPalace is experiential memory, never canonical truth.
- Git/canonical docs represent current project truth.
- Permissions must be enforced outside prompts.
- Agent-facing OpenSearch access should default to read/query; projection writes belong to deterministic services/workers.
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
3. PostgreSQL Task/control schema and state-machine definition;
4. outbox/projection and operation-journal design;
5. agent/skill/capability manifest formats;
6. OpenSearch index mappings, versioned aliases, projection boundaries, and rebuild procedure;
7. OpenSearch MCP + Context Resolver retrieval contract, including multi-search composition;
8. runtime sequence diagram for one code-changing task;
9. V1 milestone breakdown;
10. risks, unknowns, and architecture decisions requiring approval;
11. explicit list of deferred post-V1 features.

After the plan is internally consistent, begin the first vertical slice.

## V1 completion test

A real coding task must be able to start, persist authoritative execution state in PostgreSQL, lose its active model/session, and later continue correctly using selectively retrieved context from the OpenSearch knowledge fabric through the approved capability/MCP layer, then complete deterministic validation and independent review.

If that cannot be demonstrated, V1 is not complete.
