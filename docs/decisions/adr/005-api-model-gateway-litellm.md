# ADR 005: Adopt LiteLLM only for raw API model access

**Status:** Amended — MIT core Router only; server proxy not admitted

**Date:** 2026-09-15

## Milestone 0 amendment — 2026-09-15

At 1.102.0 the `proxy` optional dependency directly includes
`litellm-enterprise==0.1.67` under `LicenseRef-Proprietary`; production use of
that package requires an enterprise license. The open-source V1 selection is
therefore narrowed to the MIT core `litellm.Router` library embedded behind the
raw-API runtime adapter. The LiteLLM server proxy is not admitted unless the
project explicitly approves/procures its commercial deployment.

An exact-source/frozen-lock Linux core image contained neither enterprise nor
proxy-extras. Against deterministic endpoints, primary HTTP 503 fell back in
318 ms with normalized usage, complete endpoint loss returned a bounded
`ServiceUnavailableError` in 331 ms, and restarting the fallback restored
success. The admission image is 4.39 GB because it retains compilers; produce a
trimmed runtime image before use.

## Context

API-based agents need provider normalization, retry/fallback, cost estimates,
and routing primitives. Native coding harnesses such as Codex and Claude Code
also contain valuable tools, session protocols, and execution behavior that a
raw chat/completions proxy cannot preserve.

## Decision

Adopt the MIT core of [LiteLLM](https://github.com/BerriAI/litellm) package
1.102.0 at commit `b94b8bca211e366328bcee3acd57d859fd35e52c`
for raw API model calls only. Do not install the `proxy` extra under this ADR;
its direct proprietary dependency is outside the open-source decision.

The embedded core Router owns per-call provider translation, bounded API
retry/fallback, primitive routing, and usage/cost estimates. Paperclip adapters continue to launch native
Codex/Claude/OpenCode/Gemini/Cursor/ACP runtimes directly. Paperclip owns task
retry, logical agents, run state, and final budget/cost accounting. AI Factory
owns model-selection policy.

## Evidence

The Router source implements provider/model normalization, retries, context/
content/policy fallbacks, cooldowns, budget-aware and least-cost routing
primitives, and callback/usage interfaces across many providers. Current issue
volume and recurring protocol/cost translation defects argue for a narrow,
pinned adapter rather than making LiteLLM the universal agent runtime. The live
Milestone 0 probe verified fallback selection, normalized usage, bounded total
upstream failure, and recovery at the exact source revision.

## Authority boundary

LiteLLM owns no durable AI Factory data. It returns provider/model/usage/latency/
error evidence to the Paperclip run/cost ledger. It does not own native harness
sessions, task retries, model policy definitions, or canonical prices/budgets.

## Alternatives

- **Custom provider gateway:** rejected while LiteLLM covers commodity API
  translation and fallback.
- **Route all coding agents through LiteLLM:** rejected because it destroys
  native harness semantics and duplicates Paperclip adapters.
- **LiteLLM server proxy:** not admitted as an open-source V1 dependency at
  1.102.0 because its supported proxy extra directly installs proprietary code.
- **No normalization library:** rejected for API agents because provider-specific
  integrations would spread across the codebase.

## Consequences

There are two explicit runtime classes—an API adapter using the core Router and a native harness adapter—
with common normalized telemetry but no fake common execution protocol. Retry
counts are reconciled so LiteLLM call fallback is not mistaken for a Paperclip
task retry.

## Risks

Rapid provider API changes, translation bugs, inconsistent price data, and
double retry/cost counting require contract tests and version pins. Provider
credentials remain scoped to the API or native adapter that needs them. The
proxy's license boundary and the core image's large source-build footprint must
be checked on every upgrade.

## Exit/replacement strategy

Replace the raw-model gateway adapter and preserve Paperclip/native runtimes.
The AI Factory model policy and normalized run telemetry remain provider-neutral.
