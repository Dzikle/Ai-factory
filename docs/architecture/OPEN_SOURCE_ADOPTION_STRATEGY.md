# AI Factory — Open Source Adoption Strategy

**Status:** Canonical architectural policy  
**Purpose:** Prevent AI Factory from rebuilding mature infrastructure without evidence.

The Phase 0.5 candidates below have now been evaluated. Their binding decisions,
versions, authority boundaries, gates, and replacements are in
[`../decisions/ADOPTION_MATRIX.md`](../decisions/ADOPTION_MATRIX.md) and
[`../decisions/V1_ADOPTION_ARCHITECTURE.md`](../decisions/V1_ADOPTION_ARCHITECTURE.md).
Candidate descriptions are retained to explain the evaluated hypotheses; the
decision records take precedence over old candidate language.

## 1. Reuse-first principle

AI Factory is not a greenfield exercise in reimplementing agent infrastructure.

Before building a substantial subsystem, the responsible agent must determine whether a mature open-source project already provides the required capability. Prefer adaptation, composition, plugins, adapters, or upstream-compatible extensions over bespoke infrastructure when the existing project satisfies the architectural contract.

The question is not:

> Can we build this ourselves?

The question is:

> Which parts are differentiated AI Factory capability, and which parts are commodity infrastructure we should reuse?

A custom implementation requires an explicit gap statement explaining why available projects are insufficient.

## 2. AI Factory remains the architectural contract

External projects are implementation providers or alternatives, not the definition of AI Factory.

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

## 3. Evaluated implementation stack

The following projects were evaluated before equivalent custom code was authorized.

### Paperclip — selected control plane

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

**Adoption status:** **ADAPT** — selected as the sole operational authority,
subject to pinned-release recovery/MCP/workspace gates in ADR 001.

The first implementation milestone must validate the pinned Paperclip release
against the documented recovery, MCP, workspace, and pre-run integration gates
without creating competing sources of truth.

Prefer extending Paperclip through its supported plugin/adapter surfaces over forking it.

### DBOS — deferred replacement, not an underlay

DBOS was evaluated and remains available only if Paperclip cannot meet the hard
continuity requirement.

Potential value:

- PostgreSQL-backed durable workflows;
- checkpoints and recovery;
- retries/queues;
- durable AI/tool-call execution patterns.

**Adoption status:** **DEFER** — mutually exclusive Paperclip replacement only.

Do not combine Paperclip task state + DBOS workflow state + a third AI Factory state model without a demonstrated need and a clearly defined authority boundary.

### Agent Skills — adopted skill packaging format

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

**Adoption status:** **ADOPT** — Git owns canonical skill packages.

### Official OpenSearch MCP server — selected knowledge MCP provider

Repository: `opensearch-project/opensearch-mcp-server-py`.

Do not build a custom OpenSearch MCP server unless the official server lacks a required contract that cannot be supplied through a thin adapter.

AI Factory capabilities should map to the official server where appropriate, including search/multi-search and read-only knowledge discovery.

**Adoption status:** **ADAPT** — fixed-cluster/read-only with a bounded logical
adapter and Paperclip gateway enforcement.

### ToolHive — deferred MCP runtime alternative

Repository: `stacklok/toolhive`.

ToolHive was evaluated for:

- MCP server lifecycle;
- MCP isolation;
- identity/access policy;
- tool registry/discovery;
- secrets/policy integration;
- audit/observability around MCP calls.

**Adoption status:** **DEFER** — duplicates Paperclip's selected V1 MCP
catalog/policy/secrets/approval/audit/runtime responsibilities.

AI Factory still owns logical capability definitions (`knowledge.search`,
`repo.read`, etc.). Paperclip is the active enforcement/runtime authority in V1;
ToolHive has no V1 authority.

### SWE-ReX — deferred sandbox-provider option

Repository: `SWE-agent/SWE-ReX`.

SWE-ReX was evaluated before selecting Paperclip's execution abstraction. Agent
logic still does not own environment provisioning or shell-runtime details.

**Adoption status:** **DEFER** — Paperclip owns execution lifecycle; reconsider
SWE-ReX only behind Paperclip's `sandbox_provider` contract.

A heavier sandbox such as E2B may be evaluated later if stronger hostile-code isolation or remote execution semantics become necessary.

### CodeGraphContext — selected structural graph

Use CodeGraphContext as the one primary code-graph provider in V1 rather than
writing our own structural index.

**Adoption status:** **ADAPT** — one containerized, revision-aware, bounded V1
provider; Git remains code truth.

### LiteLLM — selected raw API-model gateway

Use LiteLLM for models exposed through standard APIs where it reduces custom
provider routing, retry, and cost-accounting code.

CLI/harness agents such as Codex, Claude Code, OpenCode, or CommandCode remain adapter-driven because they are not equivalent to raw model API calls.

**Adoption status:** **ADAPT** — raw/API agents only; native harnesses remain
Paperclip adapters.

### Memory — MemPalace selected by bake-off

The memory architecture must not operate two overlapping primary stores. The
completed bake-off evaluated:

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

**Adoption status:** MemPalace **ADAPT** as the sole experiential-memory
authority with OpenSearch projection. OpenSearch Agentic Memory is a mutually
exclusive deferred fallback; dual-primary memory is rejected.

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

Selected Paperclip boundary:

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

Paperclip is authoritative for task state. Do not duplicate the same workflow
state into a separate custom PostgreSQL task engine. Project/analytics
projections are acceptable; dual-authoritative workflow engines are not.

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

**Paperclip exception (owner decision, 2026-09-23):** Maintain the two narrow
lease/enrichment fixes in the account-owned `Dzikle/paperclip` fork. The former
upstream PRs are closed; future upstream submissions require separate owner
approval. Keep the fork delta auditable, track upstream read-only, and require
exact-image migration and fault/security re-admission before V1 use. This
exception does not authorize forks of other dependencies or a second task engine.

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
