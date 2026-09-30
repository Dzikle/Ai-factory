# AI Factory

AI Factory is a reusable autonomous software-engineering system built around durable tasks, specialist agents, model-agnostic skills, least-privilege capabilities, institutional memory, indexed knowledge, independent verification, and continuous improvement.

Its purpose is not to create one giant coding agent. It is to build a small software engineering organization whose execution models are replaceable and whose accumulated experience progressively becomes cheaper, safer, and more deterministic automation.

## North-star loop

```text
DO
↓
VERIFY
↓
RECOVER
↓
REMEMBER
↓
ANALYZE
↓
IMPROVE
↓
STANDARDIZE
↓
AUTOMATE
↓
DO BETTER NEXT TIME
```

## Core design

- **Control plane:** durable task state, scheduling, retries, budgets, permissions, idempotency.
- **Execution plane:** specialist agents, model routing, skills, MCP/tool capabilities, isolated execution/workspaces.
- **Knowledge plane:** Git/canonical docs, experiential memory, OpenSearch knowledge projection, code graph, artifacts.
- **Quality plane:** deterministic checks, independent review, QA/UX, integration validation.
- **Improvement plane:** telemetry, capability-gap detection, evals, process review, controlled self-improvement.

## Reuse-first architecture

AI Factory should not rebuild mature infrastructure merely because we can.

Before substantial custom implementation, evaluate existing open-source components against the AI Factory architectural contract. The completed adoption spike evaluated these candidates; selections and deferrals are recorded in the [adoption matrix](docs/decisions/ADOPTION_MATRIX.md):

- **Paperclip** — control plane / tasks / agents / budgets / workspaces / adapters;
- **Agent Skills** — canonical portable skill format;
- **official OpenSearch MCP server** — knowledge retrieval interface;
- **ToolHive** — MCP runtime, policy, registry, and isolation;
- **SWE-ReX** — coding-agent execution/runtime abstraction;
- **existing code-graph MCP/provider** — structural discovery;
- **LiteLLM** — API-model gateway where appropriate;
- **MemPalace vs OpenSearch Agentic Memory** — explicit memory bake-off;
- **DBOS** — durable workflow fallback only if the chosen control plane cannot meet continuity requirements.

AI Factory remains the architecture and product contract. External projects are implementation candidates underneath it.

## Canonical reading order

1. [`AGENTS.md`](AGENTS.md) — rules for every agent working in this repository.
2. [`autonomy/GOALS.md`](autonomy/GOALS.md) — product goals and success criteria.
3. [`autonomy/INDEX.md`](autonomy/INDEX.md) — context router for the autonomous system.
4. [`docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`](docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md) — full architecture specification.
5. [`docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md`](docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md) — reuse-first implementation policy and candidate stack.
6. [`docs/implementation/ADOPTION_SPIKE.md`](docs/implementation/ADOPTION_SPIKE.md) — required open-source adoption spike.
7. [`docs/implementation/IMPLEMENTATION_KICKOFF.md`](docs/implementation/IMPLEMENTATION_KICKOFF.md) — V1 builder contract after the spike.

## Current phase

**Trusted-local V1 accepted by the owner — 2026-09-30.**

The revised M0–M4 local roadmap is complete: task submission/progress, independent
tests/Reviewer/QA/owner approval, bounded Git-verified context, supervised memory,
native scorecards and restore/rebuild/recovery runbooks. The accepted implementation
is on `milestone1-contracts`; this acceptance does not merge or rewrite `main`.

Complete cost measurement for interrupted coding handoffs is explicitly deferred,
not passed. No model-performance/cost improvement or production readiness is claimed.
Additional isolation and the existing post-V1 deferrals remain unchanged.

See the [accepted implementation scope](docs/implementation/IMPLEMENTATION_KICKOFF.md),
[task commands](milestone2/README.md), and
[acceptance record](milestone4/results/local-v1-acceptance-20260930.json).
