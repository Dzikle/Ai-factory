# AI Factory — Open Source Adoption Strategy

**Status:** Canonical architectural policy  
**Purpose:** Prevent AI Factory from rebuilding mature infrastructure without evidence.

## 1. Reuse-first principle

AI Factory is not a greenfield exercise in reimplementing agent infrastructure.

Before building a substantial subsystem, the responsible agent must determine whether a mature open-source project already provides the required capability. Prefer adaptation, composition, plugins, adapters, or upstream-compatible extensions over bespoke infrastructure when the existing project satisfies the architectural contract.

The question is not:

> Can we build this ourselves?

The question is:

> Which parts are differentiated AI Factory capability, and which parts are commodity infrastructure we should reuse?

A custom implementation requires an explicit gap statement explaining why available projects are insufficient.

## 2. AI Factory remains the architectural contract

External projects are implementation candidates, not the definition of AI Factory.

The following AI Factory properties remain non-negotiable:

- disposable model sessions and durable execution state;
- logical expert roles independent from model/provider identity;
- model-agnostic selectively loaded skills;
- least-privilege tools/MCPs;
- bounded context resolution;
- OpenSearch organizational knowledge fabric;
- provenance-aware retrieval;
- historical/experiential memory separated from canonical truth;
- independent review and deterministic validation;
- telemetry and evals around cost per accepted correct task;
- self-healing and controlled self-improvement;
- experience progressively compressed toward deterministic automation.

If an external control plane or runtime cannot preserve these properties through configuration, plugins, adapters, or bounded extensions, it does not automatically become the foundation merely because it already exists.

## 3. Candidate implementation stack

The following projects should be evaluated before equivalent custom code is written.

### Paperclip — primary control-plane candidate

Repository: `paperclipai/paperclip`  
License: MIT at time of evaluation.

Paperclip already provides many capabilities that overlap with our planned commodity control plane:

- logical agents separated from execution adapters;
- task/work management and persistent context;
- atomic task checkout / execution locking;
- goals and organizational hierarchy;
- budgets and cost tracking;
- heartbeats and scheduled execution;
- persistent run/session state;
- governance and approvals;
- workspaces and Git worktrees;
- agent adapters including Codex/Claude/CLI-style execution;
- skills management;
- plugins, secrets, storage, events, and audit surfaces.

**Adoption status:** primary candidate, not yet canonical dependency.

The first implementation phase must determine whether Paperclip can supply the control-plane foundation without creating competing sources of truth or preventing our knowledge/retrieval/improvement architecture.

Prefer extending Paperclip through its supported plugin/adapter surfaces over forking it.

### DBOS — durable workflow fallback / optional underlay

DBOS should be evaluated only if the chosen control plane cannot meet our hard continuity requirement.

Potential value:

- PostgreSQL-backed durable workflows;
- checkpoints and recovery;
- retries/queues;
- durable AI/tool-call execution patterns.

**Adoption status:** fallback candidate.

Do not combine Paperclip task state + DBOS workflow state + a third AI Factory state model without a demonstrated need and a clearly defined authority boundary.

### Agent Skills — canonical skill packaging direction

Repository: `agentskills/agentskills`.

AI Factory should align its skill packages with the Agent Skills format rather than inventing an incompatible skill layout.

Canonical direction:

```text
skills/<skill-id>/
  SKILL.md
  scripts/        # optional
  references/     # optional
  assets/         # optional
```

AI Factory may maintain additional machine-readable metadata where required for permissions, evaluation, lifecycle, or capability resolution, but should preserve compatibility with the external skill standard whenever practical.

**Adoption status:** preferred/canonical format direction.

### Official OpenSearch MCP server — canonical knowledge MCP provider

Repository: `opensearch-project/opensearch-mcp-server-py`.

Do not build a custom OpenSearch MCP server unless the official server lacks a required contract that cannot be supplied through a thin adapter.

AI Factory capabilities should map to the official server where appropriate, including search/multi-search and read-only knowledge discovery.

**Adoption status:** canonical provider unless spike reveals a blocking gap.

### ToolHive — MCP runtime/security/registry candidate

Repository: `stacklok/toolhive`.

Evaluate ToolHive before building custom infrastructure for:

- MCP server lifecycle;
- MCP isolation;
- identity/access policy;
- tool registry/discovery;
- secrets/policy integration;
- audit/observability around MCP calls.

**Adoption status:** candidate.

AI Factory still owns the logical capability policy (`knowledge.search`, `repo.read`, etc.); ToolHive may provide enforcement/runtime infrastructure underneath it.

### SWE-ReX — execution/sandbox candidate

Repository: `SWE-agent/SWE-ReX`.

Evaluate SWE-ReX before building a custom execution abstraction for coding agents. The desired boundary is that agent logic should not own environment provisioning or shell-runtime details.

**Adoption status:** primary lightweight sandbox/runtime candidate.

A heavier sandbox such as E2B may be evaluated later if stronger hostile-code isolation or remote execution semantics become necessary.

### CodeGraphContext / code graph provider — structural discovery candidate

Use one primary code-graph provider in V1. Evaluate an existing MCP-compatible code graph before writing our own structural index.

**Adoption status:** candidate; only one provider should be active initially.

### LiteLLM — API-model gateway candidate

Evaluate LiteLLM for models exposed through standard APIs when it can reduce custom provider routing, retry, budget, and cost-accounting code.

CLI/harness agents such as Codex, Claude Code, OpenCode, or CommandCode remain adapter-driven because they are not equivalent to raw model API calls.

**Adoption status:** candidate.

### Memory — explicit bake-off required

The memory architecture must not blindly operate two overlapping stores.

Evaluate:

```text
A. MemPalace as experiential memory, projected into OpenSearch
B. OpenSearch Agentic Memory as the primary memory layer
C. MemPalace specialist/episodic memory + OpenSearch shared/system memory
```

Compare at least:

- specialist/agent scoping;
- provenance/history;
- retention and supersession;
- retrieval quality;
- operational complexity;
- token/context impact;
- MCP/runtime integration;
- portability;
- rebuildability;
- ability to support the experience → skill → deterministic automation lifecycle.

Until this spike is complete, `MemPalace` is a preferred candidate, not an irreversible V1 dependency.

### OpenAI Symphony — orchestration reference, not required dependency

Use the public Symphony specification/implementation as a source of tested orchestration invariants, especially around:

- deterministic workspace naming and safety;
- retries/backoff;
- reconciliation;
- concurrency;
- issue/workspace lifecycle.

Do not add it as another competing control plane if Paperclip or our selected runtime already owns those responsibilities.

### Promptfoo — evaluation harness candidate

Evaluate Promptfoo when AI Factory reaches the stage of model/skill/workflow regression suites.

Do not block the control-plane V1 on a full external eval platform.

### Phoenix / Langfuse — deferred observability candidates

Do not adopt these in the first vertical slice unless OpenSearch/native telemetry proves insufficient.

Avoid creating multiple observability stores before the telemetry requirements are understood from real runs.

## 4. Adoption decision framework

For every candidate compare:

```text
architectural fit
maturity / maintenance
license
security model
extension surfaces
operational complexity
performance
recovery semantics
observability
portability
lock-in / fork risk
amount of custom code eliminated
amount of adapter code introduced
```

A mature dependency is not automatically better if integration complexity exceeds the code it removes.

## 5. Source-of-truth rule

Adoption must not create competing authorities.

For any selected external component, document exactly what it owns.

Example if Paperclip is adopted:

```text
Paperclip
  → agent/task/control-plane operational state

Git / canonical docs
  → architecture/project truth

OpenSearch
  → rebuildable organizational knowledge projection

Memory provider
  → experiential/historical memory

Artifact store
  → large outputs
```

If Paperclip becomes authoritative for task state, do not duplicate the same workflow state into a separate custom PostgreSQL task engine. Project/analytics projections into our own schema are acceptable; dual-authoritative workflow engines are not.

## 6. Extension-before-fork rule

Order of preference:

```text
configure existing project
→ plugin/extension
→ adapter/wrapper
→ upstream contribution
→ small maintained patch set
→ fork only as last resort
```

Forking transfers long-term maintenance cost to AI Factory and must be justified explicitly.

## 7. Reuse is part of self-improvement

Open-source discovery is not only a one-time bootstrap step.

The Process Optimizer should continue asking whether repeated custom work can be replaced by:

- a maintained library;
- an MCP server;
- a CLI/tool;
- an upstream feature;
- an external skill;
- a reusable repository/component.

This is one of the primary mechanisms by which AI Factory converts expensive reasoning into cheaper capability.
