# ADR 005: Adopt LiteLLM only for raw API model access

**Status:** Accepted with narrow scope

**Date:** 2026-09-15

## Context

API-based agents need provider normalization, retry/fallback, cost estimates,
and routing primitives. Native coding harnesses such as Codex and Claude Code
also contain valuable tools, session protocols, and execution behavior that a
raw chat/completions proxy cannot preserve.

## Decision

Adopt [LiteLLM](https://github.com/BerriAI/litellm) package 1.102.0 at commit
`b94b8bca211e366328bcee3acd57d859fd35e52c` for raw API model calls only.
The evaluated open-source code is MIT; the repository's enterprise directory is
separately licensed and is outside this decision.

LiteLLM owns per-call provider translation, bounded API retry/fallback, primitive
routing, and usage/cost estimates. Paperclip adapters continue to launch native
Codex/Claude/OpenCode/Gemini/Cursor/ACP runtimes directly. Paperclip owns task
retry, logical agents, run state, and final budget/cost accounting. AI Factory
owns model-selection policy.

## Evidence

The Router source implements provider/model normalization, retries, context/
content/policy fallbacks, cooldowns, budget-aware and least-cost routing
primitives, and callback/usage interfaces across many providers. Current issue
volume and recurring protocol/cost translation defects argue for a narrow,
pinned adapter rather than making LiteLLM the universal agent runtime.

## Authority boundary

LiteLLM owns no durable AI Factory data. It returns provider/model/usage/latency/
error evidence to the Paperclip run/cost ledger. It does not own native harness
sessions, task retries, model policy definitions, or canonical prices/budgets.

## Alternatives

- **Custom provider gateway:** rejected while LiteLLM covers commodity API
  translation and fallback.
- **Route all coding agents through LiteLLM:** rejected because it destroys
  native harness semantics and duplicates Paperclip adapters.
- **No gateway:** rejected for API agents because provider-specific integrations
  would spread across the codebase.

## Consequences

There are two explicit runtime classes—API gateway and native harness adapter—
with common normalized telemetry but no fake common execution protocol. Retry
counts are reconciled so LiteLLM call fallback is not mistaken for a Paperclip
task retry.

## Risks

Rapid provider API changes, translation bugs, inconsistent price data, and
double retry/cost counting require contract tests and version pins. Provider
credentials remain scoped to the gateway or native adapter that needs them.

## Exit/replacement strategy

Replace the raw-model gateway adapter and preserve Paperclip/native runtimes.
The AI Factory model policy and normalized run telemetry remain provider-neutral.
