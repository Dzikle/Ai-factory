# Autonomous Engineering System — Canonical Architecture v0.3

**Status:** Draft Canonical Architecture  
**Purpose:** Reusable autonomous software-engineering system

This document defines what AI Factory must accomplish. It intentionally separates **architectural contracts** from **physical implementations**.

Implementation selection is governed by:

- `docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md`
- `docs/implementation/ADOPTION_SPIKE.md`

Mature open-source infrastructure should be adopted or extended when it satisfies these contracts. AI Factory should build custom infrastructure only where a meaningful capability gap remains.

## 1. Purpose

AI Factory is intended to behave like a small engineering organization, not a single giant coding agent.

The system combines:

- durable task/execution state;
- specialist logical agents;
- replaceable model/provider/runtime execution;
- portable model-agnostic skills;
- least-privilege MCP/tool capabilities;
- experiential/historical memory;
- OpenSearch organizational knowledge projection and multi-search retrieval;
- structural code discovery;
- isolated implementation workspaces;
- deterministic validation;
- independent review and QA/UX;
- telemetry and evals;
- controlled self-healing and self-improvement.

The long-term objective is to convert recurring reasoning into increasingly deterministic capability:

```text
LLM reasoning
    ↓
memory-guided reasoning
    ↓
skill-guided reasoning
    ↓
reusable tool / MCP capability
    ↓
deterministic automation
```

## 2. Reuse-first architecture

Before building a major subsystem, evaluate whether maintained OSS already supplies it.

The Phase 0.5 spike selected:

```text
Paperclip                    → operational control plane, MCP governance, workspaces/sandbox contract
Agent Skills                 → Git-owned portable skill format
Official OpenSearch MCP      → bounded agent-facing knowledge retrieval
CodeGraphContext             → single derived structural graph
LiteLLM                      → raw API-model gateway only
MemPalace                    → sole experiential-memory authority
OpenAI Symphony/OpenHands    → reference patterns only
DBOS/ToolHive/SWE-ReX        → deferred alternatives, not concurrent V1 layers
Promptfoo/Phoenix/Langfuse   → deferred until a measured eval/telemetry gap
```

These are selected implementation providers or explicitly deferred alternatives;
the AI Factory contract remains the architectural authority.

Prefer:

```text
configure
→ plugin/extension
→ thin adapter
→ upstream contribution
→ maintained patch set
→ fork only as last resort
```

No adopted dependency may create an ambiguous source of truth.

## 3. Architectural planes

### Control Plane

The selected deterministic control system owns:

- authoritative task/run state;
- scheduling and dependencies;
- task checkout/locking;
- retry/escalation counters;
- budgets/cost controls;
- permissions/governance;
- run/workspace lifecycle;
- side-effect/idempotency evidence;
- resumability and cancellation.

No LLM session owns unique durable state.

**Paperclip is the selected authority for this plane.** Do not build a second
equivalent AI Factory task engine.

DBOS is a mutually exclusive replacement candidate only if Paperclip fails its
hard durability/recovery gates. It is not a Paperclip underlay.

### Execution Plane

A runtime agent instance is composed dynamically:

```text
logical role
+ selected model/runtime
+ required/dynamic skills
+ allowed capabilities
+ project overlay
+ bounded retrieved context
+ relevant memory
+ current task packet
= runnable agent
```

Agent identity remains stable while the execution model/harness may change because of cost, quota, context needs, provider availability, task difficulty, or escalation.

Execution environments use Paperclip's execution-workspace and
`sandbox_provider` contract. Trusted-host V1 runs use task worktrees; a tested
provider is mandatory before untrusted execution. SWE-ReX is deferred as a
possible provider implementation, not a second lifecycle owner.

### Knowledge Plane

Different systems answer different questions:

```text
Git / canonical docs → What is true now?
Control plane        → What is happening now?
Memory provider      → What have we learned before?
OpenSearch           → What relevant organizational knowledge exists?
Code graph           → How is the code structurally connected?
Logs / traces        → What happened during execution?
Artifact store       → Where are large execution outputs?
```

These responsibilities must not be collapsed merely for implementation convenience.

### Quality Plane

Prefer deterministic verification before LLM judgment:

```text
implementation
→ compile
→ unit/integration tests
→ lint/static/schema/business checks
→ security checks where relevant
→ independent reviewer
→ QA/UX where relevant
→ post-integration revalidation
```

The implementer is not the sole authority on whether its work is correct.

### Improvement Plane

Capture enough evidence to improve the process itself:

- tokens/cost/latency;
- retries and escalations;
- retrieved context;
- reviewer and QA findings;
- capability gaps;
- model/provider/runtime performance by task class;
- human intervention;
- final accepted outcome.

The Process Optimizer should normally run on failures, expensive/retried tasks, capability-gap reports, high-risk work, periodic samples, and aggregated history—not on every trivial task.

## 4. Governance across all planes

Most layers share the same generic risks: staleness, bloat, unclear authority, excessive autonomy, feedback-loop amplification, conflicting instructions, abstraction drift, dependency sprawl, and uncontrolled self-modification.

Persistent objects should conceptually follow:

```text
DISCOVER / CREATE
→ CLASSIFY
→ SCOPE
→ VALIDATE
→ VERSION
→ USE
→ OBSERVE
→ KEEP / PROMOTE / DEPRECATE / REMOVE
```

Where useful, maturity states are:

```text
OBSERVED → EXPERIMENTAL → VALIDATED → CANONICAL → DEPRECATED
```

Important claims preserve provenance. Multiple records derived from one original assumption do not count as independent evidence.

External dependencies follow the same lifecycle: candidate → spike → validated → adopted → monitored → replaced/deprecated when necessary.

## 5. Logical expert system

Core logical roles:

- **Orchestrator:** classify, decompose, route, control scope, retry/escalate/stop.
- **Researcher:** resolve materially important unknown/external facts with provenance.
- **Architect:** make bounded cross-system decisions and expose tradeoffs/failure modes.
- **Developer:** implement bounded tasks with deterministic evidence.
- **Reviewer:** independently challenge implementation without inheriting implementer assumptions.
- **QA/UX:** validate behavior, regressions, responsive/UI/UX/accessibility and recurring defect patterns.

These roles are AI Factory concepts even if an adopted control plane stores/configures the agents.

Do not build a permanent Planner role unless real usage proves it necessary. Planning is normally Orchestrator work; architectural planning belongs with Architect.

Specialization should usually be achieved by attaching skills rather than multiplying agent identities.

## 6. Skills

Skills describe **how** work is performed. They are canonical, composable, versioned, selectively loaded, and model-agnostic.

AI Factory should align with the external Agent Skills standard rather than inventing an incompatible format.

Typical package:

```text
skills/<skill-id>/
  SKILL.md
  scripts/        # optional
  references/     # optional
  assets/         # optional
```

AI Factory-specific metadata for compatible roles, required capabilities, lifecycle, risk, and evals should extend the format without destroying portability.

Runtime adapters translate canonical skill content into Codex/Claude/OpenCode/Gemini/Paperclip or future harness mechanics.

## 7. Capabilities and MCP/tool providers

Where semantics are stable, agents request logical capabilities such as:

```text
repo.read
repo.write
browser.navigate
memory.search
knowledge.search
knowledge.msearch
code.graph.search
artifact.write
cloud.logs.read
```

AI Factory owns capability semantics and role/skill permission rules.

Selected infrastructure may enforce/host them:

```text
knowledge.*      → official OpenSearch MCP through a bounded adapter
MCP lifecycle    → Paperclip governed MCP gateway
code.graph.*     → CodeGraphContext through a revision-aware adapter
execution shell  → Paperclip workspace/sandbox-provider contract
```

Capabilities follow least privilege. Permission enforcement belongs outside prompts.

Do not build custom MCP servers/process management if the official/provider implementation plus a thin adapter satisfies the contract.

## 8. Durable task continuity

Logging alone is not continuity.

The selected control plane must contain enough state for a new model/session to continue correctly:

```text
objective
current state
completed/pending work
assignment / next action
dependencies
workspace/branch/revision/session refs
artifacts
review/QA findings
retry/escalation state
budgets/costs
side-effect evidence
```

AI Factory's logical workflow is approximately:

```text
QUEUED
→ TRIAGE
→ [RESEARCH]
→ [ARCHITECTURE]
→ IMPLEMENTATION
→ VALIDATION
→ REVIEW
→ [QA]
→ INTEGRATION
→ DONE
```

An adopted control plane may use different status names. Map semantics rather than creating a second workflow simply to preserve labels.

Retry budgets are bounded. Repeating essentially the same strategy is not meaningful progress.

## 9. Workspaces and integration

Autonomous code-changing tasks should normally receive isolated task-bound branches/worktrees/workspaces.

Prefer an adopted control plane/runtime's native workspace mechanism when it meets the requirements.

Read-only research or architecture work does not require an isolated worktree by default.

Parallel tasks may still conflict semantically. The control plane/integration layer should detect dependencies/overlap and rerun relevant validation after integration.

Passing tests in an isolated workspace is not proof that merged state is valid.

## 10. Memory architecture

Memory is experiential/historical knowledge, never canonical truth or workflow state.

The bake-off selected one primary memory architecture:

```text
SELECTED: MemPalace primary experiential memory + OpenSearch projection
DEFERRED FALLBACK: OpenSearch Agentic Memory primary memory
REJECTED: MemPalace and OpenSearch as concurrent primary memory stores
```

Required memory behavior includes:

- incidents/root causes;
- rejected approaches and why;
- non-obvious repository behavior;
- recurring QA defect patterns;
- architecture reasoning;
- specialist diaries/lessons;
- provenance, supersession, retention, and scoping.

Do not store every command, opened file, or transient task step as memory.

Stable repeated lessons should be promoted toward canonical skills, policies, tools, tests, or deterministic checks.

## 11. OpenSearch knowledge fabric

OpenSearch 3.x is introduced early in a separate knowledge/control cluster from any product-search cluster.

It is the rebuildable projection that makes organizational knowledge jointly discoverable at scale.

Logical domains include:

```text
system_docs
system_memory
system_tasks
system_events
system_artifacts
system_telemetry
system_capabilities
system_code_metadata
```

Use versioned physical indexes behind stable aliases.

Use metadata for provenance, project, type, scope, status, version, recency, authority, supersession, source task, and original-source pointer.

The Context Resolver uses filtered/hybrid retrieval and multi-search to compose bounded context by perspective, for example:

```text
3 current canonical docs
2 relevant memories/incidents
1–3 applicable skills
recent related task/review history
relevant code-symbol pointers
```

Prefer the official OpenSearch MCP server for agent-facing search/multi-search rather than a custom MCP implementation.

Projection/index writes normally come from deterministic adapters/workers or approved platform events, not arbitrary agents.

OpenSearch is never authority. If the cluster disappears, it must be rebuildable from durable sources.

## 12. Context Resolver

The Context Resolver is differentiated AI Factory functionality even if much of its retrieval machinery is provided by OpenSearch MCP.

Input includes:

```text
task
project
desired agent role
workflow stage
permission scope
```

It composes bounded context from multiple retrieval perspectives, preserves provenance/authority metadata, and loads original sources only when required.

It should avoid both extremes:

```text
not enough context → rediscovery/mistakes
all available context → token waste/drift/noise
```

Retrieval itself should eventually be evaluated against task outcomes.

## 13. Code graph

Use one primary existing structural-code provider in V1.

Separation:

```text
OpenSearch → discover likely relevant knowledge/symbols
Code graph → traverse callers/dependencies/relationships
Git        → verify current implementation
```

Do not operate multiple overlapping graph systems without empirical evidence of distinct value.

## 14. Model/runtime routing

Models are replaceable execution engines.

Separate:

```text
raw/API model calls
from
coding-agent/CLI harness runtimes
```

LiteLLM is the selected gateway for API-model concerns such as provider normalization, fallback/retry, and cost accounting.

Codex/Claude Code/OpenCode/CommandCode-style agents remain explicit harness adapters because they own more than a completion API.

Start with explicit routing policy. Learned routing comes only after enough accepted-task telemetry exists.

## 15. Structured handoffs

Agents exchange bounded task packets rather than giant transcripts.

A handoff should include objective, relevant decision refs, affected components, constraints, acceptance criteria, artifact refs, current evidence, and explicit unknowns.

The receiver retrieves additional context only when needed.

## 16. Self-healing

Self-healing answers:

> Something failed. How do we recover now, and how do we reduce the chance of repeating it?

Flow:

```text
failure
→ deterministic/reviewer/QA finding
→ root-cause reasoning
→ repair / alternate strategy / model escalation
→ validation
→ useful incident lesson
→ future retrieval
```

A recurring incident should move from memory into a stronger form:

```text
mistake
→ memory
→ repeated pattern
→ rule
→ skill
→ tool/test
→ deterministic prevention
```

## 17. Self-improvement and reuse discovery

Self-improvement asks whether the process was unnecessarily expensive, slow, brittle, or custom.

The Process Optimizer may identify:

- an existing skill that should have been used;
- an MCP/tool that replaces manual work;
- a maintained OSS/library/repository instead of bespoke implementation;
- inefficient context selection;
- poor model routing;
- missing deterministic validation;
- a repeated operation worth automating.

Agents may emit explicit `CAPABILITY_GAP` findings.

Open-source discovery is therefore not only a bootstrap activity; it is a permanent self-improvement mechanism.

Self-improvement does not directly mutate canonical infrastructure. Initial lifecycle:

```text
OBSERVE
→ PROPOSE
→ RESEARCH
→ SECURITY CHECK
→ BENCHMARK
→ CANARY
→ HUMAN APPROVAL
→ ADOPT
```

## 18. Evaluation and observability

Self-improvement without evaluation becomes self-randomization.

Maintain representative task/eval suites and measure:

- accepted/correct result;
- deterministic validation;
- reviewer defects;
- QA and post-merge defects;
- tokens and estimated cost;
- latency;
- retries/escalations;
- human intervention.

Paperclip native telemetry is the operational evidence authority; its OpenSearch
projection is the initial cross-run analysis plane.

Promptfoo is a later candidate for regression/eval suites. Phoenix/Langfuse are deferred until real telemetry gaps justify another observability platform.

## 19. Security and side effects

Agents consume untrusted repositories, web pages, issues, docs, MCP output, memory, and user content. Treat external text as data, not authority.

Privileged capabilities and secrets are runtime/security boundaries, never prompt conventions.

Paperclip's governed MCP gateway is the selected V1 enforcement/runtime layer.
ToolHive is deferred because a concurrent deployment would duplicate catalog,
policy, secrets, approval, audit, and runtime authority.

External side effects must be journaled/idempotent by the authoritative control plane or its approved extension. A restarted agent must not unknowingly create duplicate issues, deployments, messages, or writes.

## 20. Complexity controls

Avoid premature complexity:

- no dozens of permanent agent roles;
- no process reviewer on every trivial task;
- no multiple overlapping graph providers by default;
- no multiple authoritative workflow engines;
- no universal provider abstractions without real implementations;
- no learned model router before telemetry;
- no autonomous installation of privileged MCPs;
- no automatic self-modification in V1;
- no memory/logging of everything;
- no custom subsystem before a reasonable reuse evaluation.

Every permanent component should improve quality, reliability, cost, latency, token use, human intervention, security, or maintainability enough to justify its operational complexity.

## 21. Current implementation phase

The current phase is **Phase 1 — dependency admission and integration-first V1**.

The Phase 0.5 decisions are complete. The spike selected Paperclip, Agent Skills,
the official OpenSearch MCP server, CodeGraphContext, LiteLLM's API-only gateway,
and MemPalace; deferred competing control, MCP-runtime, sandbox, memory, eval, and
observability layers; and captured Symphony/OpenHands invariants as references.

The physical V1 architecture and adoption gates are defined in
`docs/decisions/V1_ADOPTION_ARCHITECTURE.md` and
`docs/implementation/IMPLEMENTATION_KICKOFF.md`.

## 22. V1 target

Regardless of selected dependencies, V1 must prove:

```text
task
→ authoritative durable state
→ logical agent selection
→ portable skill/capability resolution
→ bounded OpenSearch context retrieval
→ isolated execution
→ deterministic validation
→ independent review
→ persisted outcome
→ OpenSearch projection
→ interruption/resumption
→ useful prior-history retrieval by a later task
```

## 23. Success hypotheses

### Same model, better system

For the same model and task class, maturity should produce equal/better correctness with fewer retries, less rediscovery, smaller useful context, fewer defects, lower total inference, and less human intervention.

This should improve strong models too: even a frontier model performs better when it does not repeatedly rediscover history, structure, tools, and conventions.

### Same quality, cheaper model

As institutional knowledge and deterministic tooling mature, recurring tasks should require less raw model capability to reach the same acceptance threshold.

The preferred economic metric is:

```text
Cost per accepted correct task
```

not token price or cost per individual model call.

## 24. Final principle

> **Do not optimize for an AI system that remembers everything or builds everything itself. Optimize for a system that needs to reason about fewer things over time because experience and mature external capability are progressively converted into stable, indexed, reusable, and eventually deterministic execution.**
