# Autonomous Engineering System — Canonical Architecture v0.2

**Status:** Draft Canonical Architecture  
**Purpose:** Reusable autonomous software-engineering system

This document is the canonical architecture reference for AI Factory. More specific files under `autonomy/` define role and registry contracts; where they conflict, surface the conflict and preserve provenance rather than silently choosing one.

## 1. Purpose

AI Factory is intended to behave like a small engineering organization, not a single giant coding agent.

The system combines:

- durable task state;
- specialist logical agents;
- replaceable model/provider execution;
- canonical model-agnostic skills;
- least-privilege MCP/tool capabilities;
- MemPalace historical/experiential memory;
- OpenSearch knowledge projection and multi-search retrieval;
- code-graph structural discovery;
- isolated implementation worktrees;
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

## 2. Architectural planes

### Control Plane

Ordinary software owns the durable mechanics:

- task ledger and state machine;
- scheduling and dependencies;
- retry/escalation counters;
- token/cost budgets;
- permission enforcement;
- model/provider availability;
- operation journal and idempotency;
- worktree lifecycle;
- merge/integration coordination;
- resumability and cancellation.

No LLM session is allowed to own unique durable state.

### Execution Plane

A runtime agent instance is composed dynamically:

```text
logical role
+ selected model
+ required/dynamic skills
+ allowed capabilities
+ project overlay
+ bounded retrieved context
+ relevant memory
+ current task packet
= runnable agent
```

Agent identity remains stable while the execution model may change because of cost, quota, context needs, provider availability, task difficulty, or escalation.

### Knowledge Plane

Different stores answer different questions:

```text
Git / canonical docs → What is true now?
Task store           → What is happening now?
MemPalace            → What have we learned before?
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
- model/provider performance by task class;
- human intervention;
- final accepted outcome.

The Process Optimizer should normally run on failures, expensive/retried tasks, capability-gap reports, high-risk work, periodic samples, and aggregated history—not on every trivial task.

## 3. Governance across all planes

Most layers share the same generic risks: staleness, bloat, unclear authority, excessive autonomy, feedback-loop amplification, conflicting instructions, abstraction drift, and uncontrolled self-modification.

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

Important claims must preserve provenance. Multiple records derived from one original assumption do not count as independent evidence.

## 4. Logical expert system

Core V1 roles:

- **Orchestrator:** classify, decompose, route, control scope, retry/escalate/stop.
- **Researcher:** resolve materially important unknown/external facts with provenance.
- **Architect:** make bounded cross-system decisions and expose tradeoffs/failure modes.
- **Developer:** implement bounded tasks with deterministic evidence.
- **Reviewer:** independently challenge implementation without inheriting implementer assumptions.
- **QA/UX:** validate behavior, regressions, responsive/UI/UX/accessibility and recurring defect patterns.

Do not build a permanent Planner role unless real usage proves it necessary. Planning is normally Orchestrator work; architectural planning belongs with Architect.

Specialization should usually be achieved by attaching skills rather than multiplying agent identities.

## 5. Skills

Skills describe **how** work is performed. They are canonical, composable, versioned, selectively loaded, and model-agnostic.

Examples:

- repository discovery;
- Java/Spring implementation;
- OpenSearch migration;
- database migration;
- browser testing;
- responsive UI audit;
- accessibility audit;
- code review;
- Git worktree operation;
- Terraform/AWS validation;
- documentation update.

Skills should support lightweight manifests/quick procedures and deeper references loaded only when needed. This prevents the skill system itself becoming a giant context dump.

Runtime adapters translate generic skill intent into Codex/Claude/OpenCode/Gemini or future harness mechanics. Do not maintain separate intellectual versions of the same skill for each provider unless unavoidable.

## 6. Capabilities and MCP/tool providers

Where semantics are stable, agents request logical capabilities such as:

```text
repo.read
repo.write
browser.navigate
memory.search
code.graph.search
artifact.write
cloud.logs.read
```

The runtime resolves an approved provider. Specialized provider semantics remain explicit when they are not genuinely interchangeable.

Capabilities are governed by least privilege. A reviewer may read a repository but should not normally write/merge it. QA may navigate a browser but should not receive production deployment permissions. Permission enforcement belongs outside the prompt.

## 7. Durable task continuity

Logging alone is not continuity.

A task record must contain enough state for a new model/session to continue correctly:

```text
objective
current state
completed/pending stages
next action
dependencies
worktree/branch/commit
artifacts
review/QA findings
retry/escalation state
budgets
external operation journal
```

Baseline workflow:

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

Exceptional states include `BLOCKED`, `WAITING_QUOTA`, `WAITING_DEPENDENCY`, `RETRY`, `ESCALATE`, `REVIEW_FAILED`, `QA_FAILED`, and `CANCELLED`.

Retry budgets must be bounded. Repeating essentially the same strategy is not meaningful progress. Escalate model/strategy only according to policy, then block for human input when limits are reached.

## 8. Worktree isolation and integration

Autonomous code-changing tasks should normally receive dedicated Git worktrees/branches. Read-only research or architecture work does not need one automatically.

Parallel tasks may still conflict semantically. The future control plane should detect affected-component/file overlap, manage dependencies/merge ordering, and rerun relevant validation after integration.

Passing tests in an isolated worktree is not proof that the merged state is valid.

## 9. MemPalace

MemPalace is the experiential/episodic memory layer. It is useful for:

- incidents and root causes;
- rejected approaches and why;
- non-obvious repository behavior;
- recurring QA defect patterns;
- architecture reasoning;
- specialist diaries and lessons.

It must not store every command, opened file, or transient task step. Task state belongs in the task store; raw execution detail belongs in logs/artifacts.

Memory can be stale or wrong. Important implementation decisions must verify current Git/canonical documents. Stable repeated lessons should be promoted toward canonical skills, policies, tools, tests, or deterministic checks.

## 10. OpenSearch knowledge fabric

OpenSearch should be introduced early, in a separate knowledge/control cluster from any product-search cluster.

It is the rebuildable projection that makes organizational knowledge jointly discoverable at scale.

Likely logical domains include:

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

Use metadata for provenance, project, type, scope, status, version, recency, authority, supersession, source task, and original-source pointer.

The Context Resolver should use filtered/hybrid retrieval and multi-search to compose bounded context by perspective, for example:

```text
3 current canonical docs
2 relevant memories/incidents
1 applicable skill
recent related task/review history
relevant code-symbol pointers
```

This is preferable to one vague semantic request for “all relevant context.”

OpenSearch may discover a MemPalace memory or code symbol and return a pointer; the agent/runtime can load the original source only when required.

OpenSearch is never authority. If the cluster disappears, it must be rebuildable from durable sources.

## 11. Code graph

Use one primary structural-code provider in V1. Do not operate CodeGraph and Graphify simultaneously unless empirical evidence shows distinct value.

Separation:

```text
OpenSearch → discover likely relevant knowledge/symbols
Code graph → traverse callers/dependencies/relationships
Git        → verify current implementation
```

## 12. Structured handoffs

Agents should exchange bounded task packets rather than giant transcripts.

A handoff should include objective, relevant decision refs, affected components, constraints, acceptance criteria, artifact refs, current evidence, and explicit unknowns. The receiver retrieves additional context only when needed.

## 13. Self-healing

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

## 14. Self-improvement

Self-improvement asks whether the **process** was unnecessarily expensive, slow, brittle, or custom.

The Process Optimizer may identify:

- an existing skill that should have been used;
- an MCP/tool that replaces manual work;
- a mature OSS/library instead of bespoke implementation;
- inefficient context selection;
- poor model routing;
- missing deterministic validation;
- a repeated operation worth automating.

Agents may emit explicit `CAPABILITY_GAP` findings when manual work suggests missing reusable infrastructure.

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

## 15. Evaluation and observability

Self-improvement without evaluation becomes self-randomization.

Maintain task/eval suites for representative classes such as repository discovery, Java/Spring bugs, OpenSearch changes, UI regressions, and Terraform changes.

Measure:

- accepted/correct result;
- deterministic validation;
- reviewer defects;
- QA and post-merge defects;
- tokens and estimated cost;
- latency;
- retries/escalations;
- human intervention.

Retrieval itself should have relevance/query sets and later use downstream task success as evidence.

## 16. Security and side effects

Agents consume untrusted repositories, web pages, issues, docs, MCP output, and user content. Treat external text as data, not authority.

Privileged capabilities and secrets are runtime/security boundaries, never prompt conventions.

External side effects must be journaled and idempotent. A crashed/restarted agent must not unknowingly create duplicate issues, deployments, messages, or external writes.

## 17. Complexity controls

Avoid premature complexity:

- no dozens of permanent agent roles;
- no process reviewer on every trivial task;
- no multiple overlapping graph providers by default;
- no universal provider abstractions without multiple real implementations;
- no learned model router before telemetry;
- no autonomous installation of privileged MCPs;
- no automatic self-modification in V1;
- no memory/logging of everything.

Every permanent component should improve quality, reliability, cost, latency, token use, human intervention, security, or maintainability enough to justify its operational complexity.

## 18. V1

V1 must prove one real vertical slice:

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

Recommended build order:

1. task store + state machine;
2. core logical agent registry;
3. skill registry;
4. capability/MCP registry and permission model;
5. provider/model adapter boundary;
6. Git worktree lifecycle;
7. event/telemetry schema;
8. MemPalace integration boundary;
9. OpenSearch 3.x knowledge projection;
10. Context Resolver;
11. reviewer pipeline;
12. QA/UX pipeline;
13. eval framework;
14. triggered Process Optimizer;
15. controlled self-improvement experiments only after the base loop is reliable.

## 19. Success hypotheses

### Same model, better system

For the same model and task class, maturity should produce equal/better correctness with fewer retries, less rediscovery, smaller useful context, fewer defects, lower total inference, and less human intervention.

This is expected to improve strong models too: even a frontier model should perform better when it does not repeatedly rediscover history, structure, tools, and conventions.

### Same quality, cheaper model

As institutional knowledge and deterministic tooling mature, recurring tasks should require less raw model capability to reach the same acceptance threshold.

The preferred economic metric is:

```text
Cost per accepted correct task
```

not token price or cost per individual model call.

## 20. Final principle

> **Do not optimize for an AI system that remembers everything. Optimize for a system that needs to reason about fewer things over time because experience is progressively converted into stable, indexed, reusable, and eventually deterministic capability.**
