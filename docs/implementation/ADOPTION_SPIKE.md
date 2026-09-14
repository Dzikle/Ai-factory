# AI Factory — Open Source Adoption Spike

**Status:** Required before substantial V1 implementation

The architecture is now reuse-first. Do not begin by writing a custom control plane, skills system, MCP runtime, sandbox, or provider gateway.

The purpose of this spike is to determine which mature open-source components can satisfy AI Factory's architectural contracts with minimal custom code.

## 1. Spike outcome

At the end of the spike, produce a decision matrix and one proposed V1 stack.

No candidate should be adopted merely because it has more features. The selected combination must minimize duplicated responsibility and preserve AI Factory's key invariants.

## 2. Control-plane spike — Paperclip first

Evaluate `paperclipai/paperclip` as the primary control-plane foundation.

Prove or disprove the following requirements:

1. Logical agent identity is separable from model/provider/runtime.
2. A coding task has durable task/run state across process/model restarts.
3. Atomic checkout/locking prevents duplicate work.
4. Budgets and cost accounting can be enforced.
5. Agent runs can be resumed/reinvoked without relying on an original chat session.
6. Execution workspaces/worktrees can be bound to a task.
7. Codex/Claude/CLI-style agents can be attached through supported adapters or plugins.
8. We can add our Context Resolver/OpenSearch retrieval before a run without forking core orchestration.
9. We can enforce our role/capability policy.
10. We can project task/run/review/telemetry data into our OpenSearch knowledge fabric.
11. Independent Reviewer and QA stages can be represented without making the implementer the sole authority.
12. Project overlays and reusable expert definitions can remain portable across repositories.
13. The control plane can run without owning our canonical Git/docs or memory truth.
14. The extension surfaces are sufficient to avoid a long-lived hard fork.

### Paperclip acceptance result

Classify each requirement:

```text
PASS — available directly
ADAPT — achievable with small plugin/adapter
GAP — substantial custom extension required
BLOCKER — conflicts with architecture
```

If the majority of core control-plane requirements are PASS/ADAPT, prefer Paperclip over a custom task engine.

## 3. DBOS fallback spike

Do not adopt DBOS automatically.

Evaluate `DBOS` only if Paperclip or the selected control plane fails the hard continuity/recovery requirements.

Determine whether DBOS can provide the missing durable workflow layer without creating two authoritative workflow engines.

Reject architectures where:

```text
Paperclip says task state = X
DBOS says workflow state = Y
custom AI Factory DB says state = Z
```

unless the authority and reconciliation model is explicit and demonstrably safe.

## 4. Skills spike

Adopt the `agentskills/agentskills` format as the compatibility target unless a blocking limitation is discovered.

Prototype at least two AI Factory skills using the standard:

```text
repository-discovery
code-review
```

Verify that the same canonical skill content can be loaded by at least two different execution harnesses/models through adapters.

If AI Factory needs extra metadata for:

- compatible agent roles;
- required capabilities;
- lifecycle/status;
- risk;
- eval suites;

store it in a compatible extension/sidecar rather than unnecessarily replacing `SKILL.md` conventions.

## 5. OpenSearch MCP spike

Use `opensearch-project/opensearch-mcp-server-py` before writing custom MCP code.

Verify:

1. filtered search over our knowledge indexes;
2. multi-search/context composition;
3. mapping/index metadata reads;
4. least-privilege read-only agent access;
5. clean integration through our logical capability names;
6. acceptable context/tool overhead.

If a thin adapter can supply missing capability naming or result normalization, build that adapter rather than another MCP server.

## 6. ToolHive spike

Evaluate `stacklok/toolhive` as the MCP runtime/security/registry layer.

Verify whether it can supply enough of:

- server lifecycle;
- isolation;
- identity/policy enforcement;
- tool discovery/registry;
- secrets wiring;
- audit/telemetry;

that AI Factory does not need its own MCP process manager.

AI Factory should continue to own the logical capability policy and role-to-capability rules.

## 7. Sandbox/runtime spike

Evaluate `SWE-agent/SWE-ReX` for coding-agent execution.

Required proof:

- execute shell/build/test commands in a task-bound environment;
- clean separation between agent logic and environment runtime;
- usable with local/Docker-style V1 execution;
- recover/reconnect semantics sufficient for task continuity;
- easy artifact/log collection.

Do not adopt a heavier sandbox infrastructure in V1 unless the threat model requires it.

## 8. Code-graph spike

Select one existing structural-code provider.

Evaluate CodeGraphContext or another MCP-compatible provider against:

- language coverage needed by target projects;
- symbol lookup;
- caller/dependency traversal;
- incremental indexing/update cost;
- MCP/API ergonomics;
- pointer/metadata projection into OpenSearch.

Do not run multiple overlapping graph systems in V1.

## 9. Model gateway spike

Evaluate LiteLLM for API-based model providers only.

Determine which responsibilities it can own:

- provider normalization;
- fallback/retry;
- cost/accounting;
- model routing primitives;

Do not force CLI/harness agents through a raw-model abstraction. Codex/Claude Code/OpenCode/CommandCode-style runtimes remain explicit adapters.

## 10. Memory bake-off

Evaluate three architectures:

```text
A. MemPalace primary memory + OpenSearch projection
B. OpenSearch Agentic Memory primary memory
C. MemPalace specialist memory + OpenSearch shared/system memory
```

Create representative test memories:

- architecture decision and later supersession;
- QA recurring defect pattern;
- developer debugging lesson;
- incident/root-cause/remediation;
- specialist diary retrieval.

Measure:

- correct recall;
- filtering/scoping;
- supersession/staleness behavior;
- retrieval size/tokens;
- operational duplication;
- agent-specific versus shared knowledge;
- provenance;
- retention/pruning;
- ease of projecting/querying through the Context Resolver.

Choose the simplest architecture that preserves specialist learning and provenance.

## 11. Evaluation/observability spike

Do not install every observability/eval product.

For V1, determine whether our native run telemetry + OpenSearch is enough.

Evaluate Promptfoo later for regression suites.

Evaluate Phoenix/Langfuse only if real runs reveal a meaningful gap that they solve better than our existing telemetry path.

## 12. Reference architecture mining

Review OpenAI Symphony for invariants worth adopting, particularly:

- workspace safety;
- reconciliation;
- backoff/retries;
- concurrency;
- lifecycle cleanup.

Treat Symphony as reference material unless it supplies a clearly missing runtime component. Do not install a second control plane just to copy its ideas.

## 13. Required deliverables

Commit:

1. `docs/decisions/ADOPTION_MATRIX.md`
2. one ADR per adopted foundational dependency;
3. proposed V1 component diagram;
4. exact source-of-truth ownership table;
5. list of custom components still required;
6. list of planned adapters/plugins/extensions;
7. list of rejected candidates and why;
8. license/security/maintenance notes for adopted components;
9. proof-of-concept commands/tests for the selected stack;
10. updated implementation plan.

## 14. Spike completion criterion

We should be able to answer precisely:

```text
What are we actually building ourselves?
What are we integrating?
What does each selected dependency own?
Where is every source of truth?
What happens if each dependency disappears or fails?
How do we upgrade/replace it without rewriting AI Factory?
```

Do not begin substantial bespoke control-plane implementation until these questions are answered.
