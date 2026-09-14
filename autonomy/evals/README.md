# Evaluation Framework

Self-improvement without evaluation becomes self-randomization.

The eval system should measure whether changes to skills, routing, retrieval, tools, or policies improve accepted outcomes.

## Candidate task suites

```text
java-refactor-01
spring-bug-01
opensearch-change-01
ui-regression-01
terraform-change-01
repo-discovery-01
```

## Core metrics

- successful/accepted result;
- deterministic tests passed;
- reviewer defects;
- QA defects;
- post-merge defects;
- tokens;
- latency;
- cost;
- retry count;
- escalation count;
- human intervention.

## Retrieval evals

Context retrieval should have query sets with expected relevant sources. Compare BM25, vector, hybrid/RRF, metadata filters, and future context-composition strategies using actual downstream task success where possible.

The system should eventually be able to prove that a new skill, search configuration, model route, or tool is better rather than merely plausible.
