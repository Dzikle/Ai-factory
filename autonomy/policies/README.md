# Policies

Policies turn architectural invariants into explicit runtime and agent rules.

V1 should progressively split this directory into focused policies for:

- authority and provenance;
- memory admission and promotion;
- retry/escalation budgets;
- permissions and least privilege;
- token/cost budgets;
- external side effects and idempotency;
- promotion/deprecation lifecycle;
- security and untrusted content;
- documentation/specification integrity.

Until those files exist, `AGENTS.md` and `autonomy/GOVERNANCE.md` are canonical.

## Precedence

Security/runtime restrictions outrank project/task convenience. Canonical project policy outranks skill suggestions. Historical memory and agent inference never override current canonical policy merely because retrieval relevance is high.
