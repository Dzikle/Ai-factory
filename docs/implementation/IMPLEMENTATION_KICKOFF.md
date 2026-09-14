# AI Factory — V1 Implementation Kickoff Contract

**Status:** Blocked on completion of `docs/implementation/ADOPTION_SPIKE.md`.

You are implementing the system defined by:

- `docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`
- `docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md`
- `docs/architecture/STATE_AND_STORAGE.md`
- `docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md`
- `docs/architecture/MCP_AND_CAPABILITY_MODEL.md`
- the canonical rules under `autonomy/`
- the adopted/rejected dependency decisions produced by the adoption spike.

Do **not** assume the control plane, skills runtime, MCP runtime, sandbox, memory layer, or provider gateway must be built from scratch.

## Prerequisite

Before substantial V1 implementation, the adoption spike must answer:

```text
Which existing projects are adopted?
Which are rejected?
What does each adopted component own?
What custom AI Factory components remain necessary?
Where is every source of truth?
```

If those answers do not exist, continue the adoption spike rather than writing bespoke infrastructure.

## Fixed architectural requirements

These are requirements regardless of which OSS components implement them:

- exactly one authoritative durable control/task state owner;
- disposable LLM/model sessions;
- logical expert identity separated from model/provider runtime;
- portable model-agnostic skills;
- least-privilege capabilities enforced outside prompts;
- Git/canonical docs as current system/project truth;
- OpenSearch 3.x as a separate rebuildable organizational knowledge fabric;
- official OpenSearch MCP preferred for agent retrieval;
- bounded Context Resolver / multi-search retrieval;
- one primary code-graph provider in V1;
- large artifacts stored outside the control DB;
- deterministic validation before subjective LLM review where possible;
- independent Reviewer and QA roles;
- telemetry sufficient to measure cost per accepted correct task;
- bounded retries and idempotent external side effects;
- no autonomous self-modification in V1.

## Implementation ownership after the spike

The final adoption matrix determines the physical implementation.

Example if Paperclip passes:

```text
Paperclip
  → authoritative operational control plane / tasks / agent runs / budgets / workspaces

AI Factory extensions
  → Context Resolver
  → OpenSearch knowledge projection
  → expert workflow policies
  → capability mapping / selected plugins
  → reviewer/QA integration
  → memory integration chosen by bake-off
  → telemetry/eval/self-improvement logic
```

In this case, do **not** build a second custom PostgreSQL task engine simply because an earlier design document described logical task entities.

If Paperclip is rejected, implement the smallest control plane that satisfies the same contract, reusing DBOS or other components only where the adoption decisions justify them.

## Target V1 vertical slice

The selected stack must prove:

```text
task
→ authoritative durable state
→ agent selection
→ portable skill/capability resolution
→ OpenSearch MCP bounded context retrieval
→ isolated execution/workspace
→ deterministic validation
→ independent review
→ persisted outcome/artifacts
→ OpenSearch projection
→ interruption/recovery/resumability
```

## Custom pieces we expect may remain

Even with strong reuse, AI Factory will likely still need differentiated code for:

1. **Context Resolver** — compose bounded provenance-aware context from OpenSearch multi-search and original-source verification;
2. **OpenSearch projection adapters/workers** — project tasks, runs, docs, memory metadata, capabilities, code metadata, reviews, and telemetry from chosen durable sources;
3. **AI Factory expert/workflow policy** — Orchestrator/Architect/Developer/Reviewer/QA semantics and stage rules;
4. **project overlays** — reusable framework + repository-specific policy/context;
5. **capability mapping** — map logical AI Factory capabilities to selected MCP/runtime providers;
6. **memory adapter** — based on the selected memory architecture;
7. **quality/eval integration** — deterministic checks, independent review, task outcomes, and later process optimization;
8. **telemetry normalization** — enough common data to compare models/providers/task classes across runtimes.

Do not assume even these require large bespoke services; prefer plugins/adapters where the selected base supports them.

## Required implementation plan after adoption

Produce and commit:

1. final selected component diagram;
2. exact source-of-truth ownership table;
3. custom components/packages that remain to build;
4. extension/plugin/adapter points for adopted projects;
5. data-flow and failure/recovery sequence diagrams;
6. OpenSearch index mappings/versioned aliases/rebuild path;
7. Context Resolver retrieval contract;
8. skill/capability manifest contract compatible with Agent Skills;
9. runtime sequence for a code-changing task;
10. telemetry/eval schema;
11. V1 milestone breakdown;
12. explicit deferred post-V1 work.

## V1 completion test

A real coding task must be able to:

1. enter the selected authoritative control plane;
2. obtain a logical expert role and selected model/runtime;
3. load portable skills and least-privilege capabilities;
4. retrieve bounded knowledge through OpenSearch MCP/Context Resolver;
5. execute in an isolated task workspace;
6. survive intentional interruption of the active model/process;
7. resume from durable state without the original chat session;
8. complete deterministic validation;
9. receive an independent review;
10. persist outcome, telemetry, and artifact references;
11. project useful history into OpenSearch;
12. allow a later similar task to retrieve that prior experience.

If that cannot be demonstrated, V1 is not complete.
