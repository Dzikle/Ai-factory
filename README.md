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
- **Execution plane:** specialist agents, model routing, skills, MCP/tool capabilities, isolated worktrees.
- **Knowledge plane:** Git/canonical docs, MemPalace, OpenSearch knowledge projection, code graph, artifacts.
- **Quality plane:** deterministic checks, independent review, QA/UX, integration validation.
- **Improvement plane:** telemetry, capability-gap detection, evals, process review, controlled self-improvement.

## Canonical reading order

1. [`AGENTS.md`](AGENTS.md) — rules for every agent working in this repository.
2. [`autonomy/GOALS.md`](autonomy/GOALS.md) — product goals and success criteria.
3. [`autonomy/INDEX.md`](autonomy/INDEX.md) — context router for the autonomous system.
4. [`docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`](docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md) — full architecture specification.
5. [`docs/implementation/IMPLEMENTATION_KICKOFF.md`](docs/implementation/IMPLEMENTATION_KICKOFF.md) — V1 builder contract.

## Current phase

**Phase 0: canonical foundation.** The repository is intentionally documentation-first. The next step is to implement the smallest durable V1 vertical slice described in the kickoff contract, without prematurely building the full end-state platform.
