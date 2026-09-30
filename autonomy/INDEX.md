# Autonomy Index

This is the context router for AI Factory. Load the smallest relevant set of documents for the current task.

## Start here

- Product goals and success criteria → [`GOALS.md`](GOALS.md)
- System-wide governance and lifecycle → [`GOVERNANCE.md`](GOVERNANCE.md)
- Full architecture → [`../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`](../docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md)
- Reuse-first/open-source policy → [`../docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md`](../docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md)
- State/storage boundaries → [`../docs/architecture/STATE_AND_STORAGE.md`](../docs/architecture/STATE_AND_STORAGE.md)
- OpenSearch knowledge fabric → [`../docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md`](../docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md)
- MCP/capability model → [`../docs/architecture/MCP_AND_CAPABILITY_MODEL.md`](../docs/architecture/MCP_AND_CAPABILITY_MODEL.md)
- Current adoption spike → [`../docs/implementation/ADOPTION_SPIKE.md`](../docs/implementation/ADOPTION_SPIKE.md)
- Completed adoption matrix → [`../docs/decisions/ADOPTION_MATRIX.md`](../docs/decisions/ADOPTION_MATRIX.md)
- Selected physical V1 architecture → [`../docs/decisions/V1_ADOPTION_ARCHITECTURE.md`](../docs/decisions/V1_ADOPTION_ARCHITECTURE.md)
- V1 implementation contract → [`../docs/implementation/IMPLEMENTATION_KICKOFF.md`](../docs/implementation/IMPLEMENTATION_KICKOFF.md)

## Specialist roles

- Role catalog → [`agents/README.md`](agents/README.md)
- Orchestrator → `agents/orchestrator.md`
- Researcher → `agents/researcher.md`
- Architect → `agents/architect.md`
- Developer → `agents/developer.md`
- Reviewer → `agents/reviewer.md`
- QA/UX → `agents/qa-ux.md`

## System registries

- Skills → `skills/README.md`
- Capabilities and MCP/tool providers → `capabilities/README.md`
- Models and routing → `models/README.md`
- Workflows → `workflows/README.md`
- Policies → `policies/README.md`
- Evaluation framework → `evals/README.md`
- Project overlays → `projects/README.md`
- Versioned Git contracts → [`contracts/README.md`](contracts/README.md)

## Current phase rule

**Trusted-local V1 accepted by the owner on 2026-09-30.** The revised finite
M0–M4 roadmap is closed for that scope. Complete cost per accepted correct coding
task across interrupted native handoffs is explicitly deferred, not passed.
Missing/partial telemetry remains unknown/partial; no improvement is proven.
See [the acceptance record](../milestone4/results/local-v1-acceptance-20260930.json)
and [current plan](../docs/implementation/IMPLEMENTATION_KICKOFF.md).
Pending/unapproved native tasks are not accepted by this scope decision. Keep
credential containment, scoped MCP profiles, independent review and human approval;
production readiness and existing post-V1 deferrals are unchanged. New work follows
an actual requested feature/task, not another mandatory milestone. The earlier
checkpoint history below retains its evidence, not a current acceptance blocker.

Phase 0.5 and the Paperclip Milestone 0 dependency gate are complete. Milestone 1
proved one real, independently reviewed native coding task and model-change
recovery. Milestone 2's revised trusted-local demonstration is complete; the supervised OpenSearch MCP slice and
second accepted task (AIF-47), including independent functional QA, have passed.
The owner's 2026-09-28 decision prioritizes the trusted local task workflow.
Extra execution/network isolation is deferred, not passed; keep the deployed
credential fix, existing scoped MCP profiles, separate review and human approval.
Resume only task-selected agents; admission fixtures stay paused.
The task submission/status commands are verified live. AIF-48's corrected
candidate passed fresh tests, independent review and functional QA; the owner
approved it and merge `b78b4c53` integrated the exact candidate. Paperclip records
`done`, 4/4 gates, with clear locks; post-merge tests and QA passed.
Cancelled-handoff recovery still needs supervised reconciliation; see
`milestone2/README.md`. This closes the local demo, not full V1 or production
readiness. Milestone 3's supervised trusted-local demonstration is complete: MemPalace
capture/recall and native later-task use pass real-service checks, independent
tests, full Reviewer assessment and functional QA. Restart preserved context and
receipts. The owner approved AIF-49 on 2026-09-29; Paperclip records `done`, 4/4
gates, with clear locks. Integration `a46ec83` retains the exact candidate on
`milestone1-contracts`; fresh merged checks and isolated Git rollback/reapply
passed. Milestone 4's owner-approved bounded measurement slice is verified:
a read-only native task scorecard and one serial baseline/memory task pair,
without additional services. The owner selected AIF-50 with the explicit Merge
instruction; Paperclip records `done`, 4/4 gates. Integration `03e443a` preserves
the original candidate on `milestone1-contracts`; 139 Python tests (two optional
skips), 9/9 QA and 26/26 Node checks passed. The existing source checkout is
updated; primary `main` is unchanged. AIF-51 remains unapproved, not integrated.
This pair shows no demonstrated memory
benefit; missing telemetry is not zero or evidence of cost savings. Full
measurement remains deferred under the later local acceptance above. See
`milestone3/README.md` and `milestone4/README.md`.
Keep the selected integration boundaries and see
`docs/implementation/IMPLEMENTATION_KICKOFF.md` for current receipts and exit gates.

Changes that introduce a second task/workflow, MCP policy, memory, sandbox
lifecycle, or graph authority require a new ADR and evidence that the existing
selected boundary cannot satisfy the requirement.

## Context-loading rule

Do not load all documents simply because they exist.

Start with:

```text
Task
+ AGENTS.md
+ GOALS / governance as needed
+ current specialist role
```

Then resolve only the skills, capabilities, project documents, memories, task history, and code references needed for the task.

Runtime context retrieval should eventually be handled by the Context Resolver using OpenSearch multi-search plus direct source verification.
