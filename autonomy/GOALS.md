# AI Factory Goals

**Status:** Canonical

## Product goal

Create a reusable autonomous software-engineering system that behaves like a small, continuously improving engineering organization rather than a single coding chatbot.

The system should coordinate specialist roles, retain useful history, retrieve bounded context, use controlled tools, verify work independently, recover from interruption, and gradually convert recurring reasoning into deterministic capability.

## Core success hypotheses

### H1 — Same model, better system

For the same model and task class, a more mature AI Factory should produce equal or better quality with:

- fewer tokens;
- less repository rediscovery;
- fewer retries;
- fewer reviewer defects;
- fewer post-merge regressions;
- less human intervention;
- lower total cost per accepted task.

This applies to strong models as well as cheap models. A frontier model should execute better with high-quality retrieved context, history, skills, tools, and deterministic checks than it does with naked context and repeated rediscovery.

### H2 — Same quality, cheaper execution

As knowledge, skills, retrieval, validation, and deterministic tooling improve, the minimum model capability required to meet a fixed quality threshold should decrease.

The system should progressively make recurring task classes easier rather than merely route the same hard problem to a cheaper model.

## Primary KPI

```text
Cost per accepted correct task
```

Important supporting metrics:

- accepted-task rate;
- first-pass review acceptance;
- QA regression rate;
- post-merge defect rate;
- retries per accepted task;
- tokens per accepted task;
- frontier-model calls per accepted task;
- human interventions per accepted task;
- completion latency.

## Long-term maturity direction

```text
LLM reasoning
    ↓
Memory-guided reasoning
    ↓
Skill-guided reasoning
    ↓
Reusable tool / MCP capability
    ↓
Deterministic automation
```

The goal is not a system that remembers everything. The goal is a system that needs to reason about fewer recurring problems because experience has been converted into stable capability.

## V1 goal

Prove one durable vertical slice:

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

A coding task must be able to lose its active model/session and later continue correctly from durable state.

## Explicit V1 non-goals

Do not attempt to build these before the core loop is reliable:

- autonomous self-modification;
- learned/ML model routing;
- dozens of agent roles;
- automatic installation of arbitrary MCP servers;
- multiple production code-graph providers for the same job;
- universal abstractions for hypothetical future providers;
- unrestricted autonomous production changes.
