# ADR 001: Adopt Paperclip as the operational control plane

**Status:** Accepted with adoption gates

**Date:** 2026-09-15

## Context

AI Factory needs logical agents, durable task/run state, atomic ownership,
continuation after process loss, budgets, approvals, workspaces, independent
review stages, runtime adapters, skills, artifacts, and audit. Building those
from a new PostgreSQL state machine would duplicate commodity infrastructure.
Exactly one system may own operational workflow truth.

## Decision

Adopt [Paperclip](https://github.com/paperclipai/paperclip) at evaluated commit
`5282cabde84624320e63bd942f6ed5124952f2a2` (MIT; release
`v2026.831.1`) as the single operational control plane. Integrate by supported
configuration, execution-policy templates, launcher/runtime adapters, plugin
events, storage, governed MCP, and sandbox-provider interfaces. Do not fork.

DBOS must not run as a second workflow engine. Paperclip's MCP gateway and
workspace/sandbox contracts are also the V1 runtime layers, avoiding parallel
ToolHive and SWE-ReX authorities.

## Evidence

- Agent rows separate stable logical identity/role/capabilities from
  `adapterType`, adapter configuration, model, and runtime configuration.
- Issues use versioned status plus checkout/execution locks. Checkout is a
  conditional update; stale adoption verifies terminal/missing owners and uses
  compare-and-swap semantics.
- Heartbeat runs persist status, usage, result, session identifiers, liveness,
  retry lineage, context snapshots, and controller leases. Wakeup requests have
  claim/finish state and idempotency keys; task sessions survive finite runs.
- Startup recovery reaps orphaned runs, promotes due retries, resumes queued
  work, and reconciles stranded issues. See the pinned
  [durable continuation design](https://github.com/paperclipai/paperclip/blob/5282cabde84624320e63bd942f6ed5124952f2a2/doc/architecture/durable-continuation-scheduler.md)
  and [execution semantics](https://github.com/paperclipai/paperclip/blob/5282cabde84624320e63bd942f6ed5124952f2a2/doc/execution-semantics.md).
- Execution policies can model separate implementer, Reviewer, approver, and QA
  participants; `in_review` and anti-zombie review recovery are durable.
- Current schemas/services include cost events, budgets, approvals, execution
  workspaces, artifacts/storage providers, activity history, plugins, skills,
  secrets, and governed MCP profiles/audit.
- Targeted upstream tests at the pinned commit: 52 recovery/context/reviewer/
  stale-lock tests passed across two final runs. An earlier stale-lock run had
  host skips and an embedded DB setup timeout; unit tests are not accepted as
  production continuity proof.

### Requirement classification

| Requirement | Result | Basis / required adaptation |
| --- | --- | --- |
| Logical identity independent of provider/model/runtime | PASS | Separate agent identity and adapter/runtime configuration. |
| Durable task/run/session state | PASS | Persistent issue, heartbeat run, wakeup, task-session, and context rows. |
| Atomic claim/locking/recovery | PASS | Conditional checkout, execution locks, stale-owner CAS, startup reconciliation. |
| Heartbeats/recurring execution | PASS | Durable wake queue, timers/routines, leases, retry scheduling. |
| Budgets/cost accounting | PASS | Agent budgets and run-linked cost events. |
| Native CLI/provider adapters | PASS | Codex/Claude/OpenCode/Gemini/Cursor/ACP and launcher surfaces. |
| Git workspaces/worktrees | PASS | Execution workspace and isolated worktree lifecycle. |
| Approvals/governance | PASS | Approval records, execution policies, governed MCP decisions. |
| Portable AI Factory skills | ADAPT | Sync Git-owned Agent Skills packages; do not make Paperclip rows canonical. |
| Secrets/artifacts/storage | PASS | Encrypted secrets and local/S3 storage provider interfaces. |
| Plugin/events/OpenSearch projection | ADAPT | At-least-once events require idempotency/reconciliation; runtime is alpha. |
| Context Resolver before a run | ADAPT | Wrapper/launcher uses adapter context and context snapshot; upstream hook preferred. |
| Independent Reviewer and QA | PASS | Separate agents and execution-policy participants with distinct grants. |
| Resume without original conversation/model | PASS | Reattach session when safe or reinvoke from durable task/context/workspace. |
| Operational truth without canonical project ownership | PASS | Git/memory/OpenSearch remain external authorities/projections. |
| Avoid a long-term fork | ADAPT | Supported interfaces appear sufficient; the pre-run POC is a release gate. |

## Authority boundary

Paperclip owns task/run state, leases, wakeups, active agent/runtime bindings,
execution policies, approvals, budgets/cost events, runtime MCP policy/audit,
workspace lifecycle, and artifact metadata. It does not own canonical Git/docs,
skill source, experiential memory, OpenSearch truth, or the code graph.

Task/run/review/QA/cost/approval/audit metadata is projected idempotently into
OpenSearch. Plugin events are at-least-once and not globally ordered; projectors
must use stable event/entity keys and periodic reconciliation.

## Alternatives

- **Custom PostgreSQL engine:** rejected because Paperclip already implements the
  difficult ownership, recovery, workspace, approval, and adapter surfaces.
- **DBOS-backed custom control plane:** deferred as a mutually exclusive fallback;
  it is not safe as a second state machine under Paperclip.
- **Symphony/OpenHands controller:** reference patterns only; neither improves
  this authority split enough to justify a second controller.

## Consequences

AI Factory custom work moves to Context Resolver, projections, engineering
workflow policy, capability compilation, memory/graph/model adapters, and evals.
Paperclip status terminology is mapped to AI Factory's logical lifecycle rather
than copied into another database. Native harness capabilities are preserved.

## Risks and gates

Paperclip is fast-moving and has correctness issues involving recovery,
silent-run liveness, MCP tokens/sessions, review replacement, and workspace
cleanup. The pinned release must pass restart/kill/stale-lock/duplicate-wakeup/
review/MCP-expiry fault injection listed in the V1 adoption architecture. Source
installation also exposed Windows path, symlink, and native-build friction, so a
supported container/server deployment is the baseline.

## Exit/replacement strategy

All AI Factory-specific behavior talks through a control-plane integration
contract and stores canonical non-operational data outside Paperclip. To replace
it: stop admission, drain/reconcile leases, export operational rows and artifact
references, import the normalized task/run state into one replacement, switch
adapters, and rebuild OpenSearch projections. DBOS is a candidate only in that
mutually exclusive replacement architecture.
