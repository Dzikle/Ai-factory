# Models and Routing

Models are replaceable execution engines. Do not encode a logical agent identity into a provider/model name.

## Two execution lanes

AI Factory should distinguish between:

```text
A. raw/API model calls
B. coding-agent / CLI harness runtimes
```

These are not the same abstraction.

Examples of API-model execution may be routed through a gateway such as **LiteLLM** if the adoption spike shows that it eliminates useful provider-normalization, retry/fallback, cost-accounting, and policy code.

Coding-agent runtimes such as Codex, Claude Code, OpenCode, CommandCode, Gemini-style CLIs, or future harnesses remain explicit runtime adapters because they own tools, sessions, files, and execution behavior beyond a raw completion API.

Do not force CLI/harness agents through a fake raw-model abstraction.

## V1 routing

Start with explicit, simple policy rather than learned routing.

Conceptually:

```text
simple / repetitive bounded work
    → low-cost capable model/runtime

large-context discovery
    → model/runtime with appropriate context/retrieval strengths

architecture / novel / high-risk reasoning
    → stronger reasoning model

critical independent review
    → strongest suitable available model

failure
    → alternate strategy/model, then bounded escalation
```

The logical agent role and canonical skills remain stable while the selected execution engine can change.

## LiteLLM candidate boundary

If adopted, LiteLLM may own API-provider concerns such as:

- provider normalization;
- basic fallback/retry;
- usage/cost accounting;
- API-model routing primitives.

AI Factory still owns:

- logical expert routing;
- task-class policy;
- quality/escalation rules;
- CLI/harness adapter selection;
- accepted-task outcome telemetry;
- project/runtime capability constraints.

Avoid duplicating the same retry/budget logic in both LiteLLM and the authoritative control plane without a clear boundary.

## Routing telemetry

Capture:

- agent role;
- task class;
- execution type (API model vs harness/CLI agent);
- model/provider/runtime;
- input/output tokens when available;
- latency;
- cost estimate;
- retry/escalation count;
- review result;
- QA result;
- accepted-task outcome.

Only after sufficient history should routing become data-driven.

## Existing automatic-entry selector

The owner-configured catalogue is
[`milestone2/config/automatic-entry-projects.json`](../../milestone2/config/automatic-entry-projects.json)
(`modelProfiles`). The coding handoff filters by qualification, native adapter,
agent availability, task kind and risk, then selects by tier, explicit priority
and ID. Paid profiles require explicit owner enablement; high-risk plans keep
the admitted subscription restriction. Selection/rejection evidence is persisted
in the native Paperclip plan, not a second routing ledger.

Codex, OpenCode and Claude Code have supported model-override paths. Claude's
catalogue entry is disabled pending runtime authentication and exact native
qualification. Cline and Command Code are requested but have no registered
execution adapters in the current checkout; disabled catalogue entries are
not integrations. Full scope, activation inputs and limits are in
[`AUTOMATIC_TASK_ENTRY.md`](../../docs/implementation/AUTOMATIC_TASK_ENTRY.md#configurable-routing-follow-up-2026-10-11--source-change-not-deployed).

## Success criterion

System maturity should improve execution in two ways:

1. the **same model** should need fewer tokens/retries and make fewer mistakes;
2. the **same quality threshold** should eventually be achievable with cheaper models for recurring task classes.
