---
name: scoped-audit
description: Run a bounded read-only audit inside an explicit scope and report findings with evidence. Use for policy, provenance, or security spot-checks.
license: MIT
compatibility: Strictly read-only; writes nothing and changes no policy.
metadata:
  ai-factory/version: "0.1.0"
  ai-factory/lifecycle: experimental
  ai-factory/risk: low
  ai-factory/required-capabilities: '["repo.read","git.read","knowledge.search","memory.search"]'
  ai-factory/roles: '["reviewer","qa"]'
  ai-factory/eval-refs: '["evals/scoped-audit-v1"]'
---

# Scoped audit

Answer a bounded audit question from current sources, with citations.

## Trigger / intent

A policy, provenance, capability, or evidence question needs an independent read-only answer.

## Prerequisites

- A written scope: paths, revisions, capabilities, and the question under audit.
- Current Git and canonical sources; memory and projection are corroboration, never authority.

## Read-only preflight

1. Record the scope, budget, and source precedence before reading.
2. Confirm no write, merge, deploy, or credential access is required; if it is, stop.

## Exact existing command

```text
python -m milestone2.program status LATEST_PARENT_ID
```

Status reads authoritative program state without writes; repository evidence comes from bounded Git reads and the evidence-pack operation.

## Expected evidence

A short report naming the scope, sources with citations and freshness, explicit unknowns, and any deferred findings for follow-up.

## Failure recovery

- An unavailable optional source: report an explicit degraded state, never fabricated evidence.
- A missing required source or authority: fail closed before concluding.

## Authorization boundary

Read-only. This skill changes no code, policy, memory, projection, or runtime state, and inspects no private operator state.

## Related skill

`deferred-finding` — captures anything the audit surfaces outside its scope.
