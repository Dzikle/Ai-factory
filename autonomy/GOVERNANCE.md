# Governance

**Status:** Canonical

Governance applies across agents, skills, models, capabilities, memories, workflows, documents, routing rules, tools, and self-improvement proposals.

## Generic risks

Nearly every persistent layer is vulnerable to the same classes of failure:

- staleness;
- bloat;
- unclear authority;
- excessive autonomy;
- feedback-loop amplification;
- conflicting instructions;
- abstraction drift;
- uncontrolled self-modification.

These should be addressed through common lifecycle rules rather than unrelated ad-hoc fixes.

## Universal lifecycle

```text
DISCOVER / CREATE
      ↓
CLASSIFY
      ↓
SCOPE
      ↓
VALIDATE
      ↓
VERSION
      ↓
USE
      ↓
OBSERVE
      ↓
KEEP / PROMOTE / DEPRECATE / REMOVE
```

## Maturity states

Use these states where meaningful:

```text
OBSERVED
→ EXPERIMENTAL
→ VALIDATED
→ CANONICAL
→ DEPRECATED
```

Not every object needs the same literal schema, but durable system objects should preserve equivalent semantics for identity, scope, status, provenance, and version.

## Authority model

The system must preserve source type and provenance. Never turn retrieved relevance into authority.

Conceptual hierarchy:

```text
Explicit current human decision
        ↓
Canonical specification / policy
        ↓
Current repository implementation evidence
        ↓
Current verified external state
        ↓
Task artifacts
        ↓
Historical memory
        ↓
Agent inference
```

A lower source can reveal that a higher-level specification is no longer implemented correctly; therefore conflicts must be surfaced, not silently resolved by rank.

## Projection rule

OpenSearch is an optimized, rebuildable projection of organizational knowledge. It may contain canonical documents, memories, events, tasks, reviews, telemetry, capabilities, and code metadata, but the original source remains authoritative.

If an index is lost, it must be reconstructable from durable sources.

## Memory rule

Memory captures what was learned, believed, rejected, or observed in the past. Memory is not current truth.

Useful recurring memories should mature toward project rules, skills, tools, tests, or deterministic enforcement.

## Independence rule

Do not count multiple derived artifacts as independent evidence merely because they exist in different stores.

Example failure:

```text
agent assumption
→ memory
→ documentation
→ indexed projection
→ reviewer retrieves all three
```

Those records share one origin and must preserve that provenance.

## Autonomy contract

Every autonomous mechanism should have appropriate:

- scope;
- permissions;
- budget;
- stop conditions;
- observability;
- rollback/recovery behavior.

## Self-improvement rule

Self-improvement can identify opportunities, research alternatives, benchmark candidates, and propose canonical changes. It must not directly install privileged capabilities or mutate canonical infrastructure without the promotion process.

Initial promotion flow:

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

## Complexity rule

More agents, memories, skills, MCPs, indexes, routing rules, or abstractions do not automatically make the system better.

Every permanent addition should justify itself against:

- quality;
- reliability;
- cost;
- latency;
- token use;
- human intervention;
- security;
- maintainability;
- operational complexity.

Prefer deletion or simplification when an element does not produce measurable value.
