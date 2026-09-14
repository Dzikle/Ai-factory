# Models and Routing

Models are replaceable execution engines. Do not encode a logical agent identity into a provider/model name.

## V1 routing

Start with explicit, simple policy rather than learned routing.

Conceptually:

```text
simple / repetitive bounded work
    → low-cost capable model

large-context discovery
    → model with appropriate context/retrieval strengths

architecture / novel / high-risk reasoning
    → stronger reasoning model

critical independent review
    → strongest suitable available model

failure
    → alternate strategy/model, then bounded escalation
```

## Routing telemetry

Capture:

- agent role;
- task class;
- model/provider;
- input/output tokens;
- latency;
- cost estimate;
- retry/escalation count;
- review result;
- QA result;
- accepted-task outcome.

Only after sufficient history should routing become data-driven.

## Success criterion

System maturity should improve execution in two ways:

1. the **same model** should need fewer tokens/retries and make fewer mistakes;
2. the **same quality threshold** should eventually be achievable with cheaper models for recurring task classes.
