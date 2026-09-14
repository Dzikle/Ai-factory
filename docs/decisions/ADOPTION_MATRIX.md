# AI Factory — Foundational Dependency Adoption Matrix

**Status:** In progress  
**Owner:** adoption spike  
**Rule:** A candidate is not canonical merely because it appears in this table. Record evidence and an explicit decision.

## Decision codes

```text
PENDING  — not adequately evaluated
ADOPT    — selected as canonical implementation/provider
ADAPT    — selected with a bounded adapter/plugin/extension
REFERENCE— mine patterns/invariants; not a runtime dependency
DEFER    — useful later, not V1
REJECT   — evaluated and not selected
```

## Matrix

| Capability | Candidate | Current status | What it could replace | Key questions before decision |
| --- | --- | --- | --- | --- |
| Control plane / agents / tasks / budgets / workspaces | `paperclipai/paperclip` | PENDING | custom task DB, scheduler, agent registry, budget/workspace/heartbeat plumbing | continuity, plugin surfaces, Context Resolver injection, review/QA stages, authority fit, upgrade/fork risk |
| Durable workflow fallback | DBOS | PENDING | custom checkpoint/retry/recovery engine | needed only if control plane continuity is insufficient; avoid competing workflow truth |
| Portable skill format | `agentskills/agentskills` | PENDING (preferred direction) | custom skill packaging specification | required metadata extensions, multi-runtime portability |
| Knowledge MCP | `opensearch-project/opensearch-mcp-server-py` | PENDING (preferred provider) | custom OpenSearch MCP server | msearch/filtering, result normalization, permissions, context overhead |
| MCP runtime/security/registry | `stacklok/toolhive` | PENDING | custom MCP process manager, isolation/policy/registry | identity, policy, secrets, registry, deployment complexity, audit |
| Coding runtime / sandbox | `SWE-agent/SWE-ReX` | PENDING | custom shell/container/runtime abstraction | local/Docker workflow, reconnection, artifacts, security boundary |
| Heavier sandbox | E2B Runtime | DEFER | advanced sandbox infrastructure | only if V1 threat model/runtime needs exceed SWE-ReX/local isolation |
| Structural code graph | CodeGraphContext / selected existing provider | PENDING | custom code graph | language coverage, freshness, MCP ergonomics, incremental cost |
| API-model gateway | LiteLLM | PENDING | custom provider normalization/fallback/cost layer | boundary vs control-plane retries/budgets; API models only |
| Specialist/episodic memory | MemPalace | PENDING | custom memory subsystem | specialist diaries, provenance, supersession, operational complexity |
| Shared/agent memory | OpenSearch Agentic Memory | PENDING | separate shared memory service | overlap with MemPalace, scoping, retrieval quality, retention |
| Orchestration invariants | `openai/symphony` | REFERENCE | bespoke lifecycle design mistakes | extract workspace/reconciliation/backoff/concurrency invariants only |
| Eval runner | Promptfoo | DEFER | custom eval execution harness | adopt when regression suites become real V1+/V2 need |
| LLM observability/eval platform | Phoenix | DEFER | additional trace/eval UI | only if native telemetry/OpenSearch is insufficient |
| LLM observability platform | Langfuse | DEFER | additional trace/eval UI | only if native telemetry/OpenSearch is insufficient |

## Required evidence per ADOPT/ADAPT decision

For each selected foundational dependency record:

```text
repository/version/commit evaluated
license
maintenance/activity signal
capabilities used
capabilities intentionally not used
authoritative data it owns
AI Factory data projected from it
extension mechanism
security/secret boundary
failure/recovery behavior
upgrade strategy
replacement/exit strategy
custom code eliminated
adapter/custom code introduced
POC/tests proving the decision
```

## Source-of-truth draft

This table must be finalized after the spike.

| Information | Authoritative owner | Projection/index |
| --- | --- | --- |
| Canonical architecture/project rules | Git/Markdown/YAML | OpenSearch docs |
| Task/run operational state | **TBD — selected control plane** | OpenSearch tasks/events/telemetry |
| Experiential memory | **TBD — memory bake-off** | OpenSearch memory/search view as applicable |
| Organizational search/retrieval | original sources remain authority | OpenSearch knowledge fabric |
| Code structure | Git source; graph is derived | code-graph provider + OpenSearch code metadata |
| Large artifacts | **TBD — selected storage provider** | OpenSearch artifact metadata if useful |
| MCP/runtime permissions | canonical AI Factory policy + selected enforcement layer | capabilities projection |

## Final spike decision

When complete, add:

```text
SELECTED V1 STACK
-----------------
control plane:
skills format:
knowledge MCP:
MCP runtime/security:
execution runtime:
code graph:
API model gateway:
memory:
artifact storage:
eval/telemetry:

CUSTOM AI FACTORY COMPONENTS
----------------------------
...

REJECTED / DEFERRED
-------------------
...
```
