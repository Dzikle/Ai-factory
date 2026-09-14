# Agent Roles

AI Factory uses a small set of durable **logical roles**. A role is not tied to one model or provider.

```text
Agent = role + policies + allowed skills + allowed capabilities + memory perspective
Model = replaceable execution engine
```

## Core V1 roles

| Role | Primary responsibility | Spawn when |
|---|---|---|
| Orchestrator | classify, decompose, route, stop/escalate | every nontrivial task |
| Researcher | resolve external/unknown facts | external evidence materially changes the task |
| Architect | cross-system design and tradeoffs | architecture or high-risk design is affected |
| Developer | bounded implementation | code/config changes are required |
| Reviewer | independent adversarial verification | meaningful implementation needs review |
| QA/UX | behavioral, regression, UI/UX validation | user-facing or flow behavior is affected |

Specialization should normally come from **skills**, not from creating dozens of permanent agent roles.

## Shared rules

- Agent sessions are disposable.
- The task ledger owns continuity.
- An agent may not expand its own permissions.
- Agents load the smallest relevant skill/context set.
- Agents preserve provenance when creating decisions or findings.
- Agents do not silently change canonical architecture to match an implementation.
- Agents emit capability gaps when manual work indicates a missing reusable capability.
- Agents must stop/escalate when retry budgets or permission boundaries are reached.

See each role file for the role-specific contract.
