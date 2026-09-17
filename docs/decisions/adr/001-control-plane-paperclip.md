# ADR 001: Adopt Paperclip as the operational control plane

**Status:** Preferred candidate; WAITING FOR UPSTREAM — Milestone 1 blocked

**Date:** 2026-09-15

## Milestone 0B amendment — 2026-09-17

Reuse upstream [PR #13515](https://github.com/paperclipai/paperclip/pull/13515),
merged as `e1f245a6607f3920d1618409ee0d5b90c822d81e`, rather than carrying its
old PR-head patches. Real re-admission discovered a narrower remaining defect:
local/SSH ephemeral leases have database-only release semantics, but the new
sweep sends them to sandbox teardown and strands them in `pending_cleanup`.
A small upstream-compatible correction atomically releases recorded host leases
without deleting shared workspaces and repairs previously capped pending rows.
Four new real-PostgreSQL regression cases fail on the baseline and pass locally,
including overlapping/idempotent cleanup and a live successor sharing a host.

The pre-run proposal extends the existing plugin SDK/worker RPC, not the adapter
registry: `agent.run.enrich` / `onRunContextEnrich` executes before dispatch,
receives the run's governed MCP surface, validates bounded artifact/prompt/
metadata, and persists the snapshot before the **original selected adapter**
executes under the **same run ID**. There is no Context Resolver implementation,
nested run, copied native adapter, or second state machine.

Temporary composite revision `b75cbb5fa6ee408c516e04544365cdcd2ff1a383` and its
immutable admission image are recorded in the lock/report. Patches and an exact
test-commit bundle are prepared; **neither proposal has been submitted/merged**.
These are evaluation artifacts, not an authorized private production fork.
Admission waits for upstream acceptance, a supported release build/image, and
repetition of the real gates against that immutable release. The source-layer
image retains the baseline native runner/CLI layer, uses server `--noCheck`, and
does not prove an in-place migration of the old database: the newer migration
journal failed against it with duplicate existing relations. Preserve and restore
database, storage, and secrets together; do not silently repair journal entries.

Authority boundaries below are unchanged. The existing admission report is the
current regression/result ledger; the 2026-09-15 section below is baseline
failure evidence, not the current remediation result.
Final 0B image verification: 41 focused tests pass; real child loss, fast
controller restart and startup after controller expiry release all nine tracked
source/successor/cancelled-run leases. Repeated startup keeps receipts unchanged,
locks clear and writers non-overlapping. Paired DB/storage restore reproduces
48 runs, 42 leases, 16 issues and the native-consumed artifact's exact digest.
These results resolve the technical defects locally, not the upstream admission
or supported migration/release gates.

## Milestone 0 amendment — 2026-09-15

Paperclip remains the preferred control-plane candidate, but commit `5282cab`
is **not admitted**. A real controller-container kill terminalized and recovered
the task/run, but left the crashed run's ephemeral environment lease permanently
`active` with no expiry or release time. The supported external-adapter contract
also cannot transparently enrich one run and delegate to another registered
native adapter, and invocation-context mutations do not persist to the run's
context snapshot.

Do not start Milestone 1, install DBOS beside Paperclip, or carry a private fork.
Require an upstream-compatible lease-reaper fix and pre-run enrichment/
delegation seam, pin the fixed revision, and rerun the admission suite. Full
evidence is in
[`MILESTONE_0_DEPENDENCY_ADMISSION.md`](../../implementation/MILESTONE_0_DEPENDENCY_ADMISSION.md).

## Context

AI Factory needs logical agents, durable task/run state, atomic ownership,
continuation after process loss, budgets, approvals, workspaces, independent
review stages, runtime adapters, skills, artifacts, and audit. Building those
from a new PostgreSQL state machine would duplicate commodity infrastructure.
Exactly one system may own operational workflow truth.

## Decision

Select [Paperclip](https://github.com/paperclipai/paperclip) at evaluated commit
`5282cabde84624320e63bd942f6ed5124952f2a2` (MIT; release
`v2026.831.1`) as the intended single operational control plane, conditional on
admission. Integrate only after the blocking amendment above is resolved, using
supported configuration, execution-policy templates, launcher/runtime adapters,
plugin events, storage, governed MCP, and sandbox-provider interfaces. Do not
fork.

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
- The Milestone 0 child-process kill produced an explicit failed run and a
  successful retry-linked successor with issue locks and both environment
  leases released.
- The controller-container kill produced `orphaned_running_run`, then a
  successful explicitly resumed successor, but source lease
  `1663b64b-ce98-46be-a56f-05222519cae0` remained active. Source tracing found
  stale-issue recovery can terminalize the run before the orphan reaper releases
  its lease.
- Runtime MCP allow/deny worked after removing the auto-bound broad application
  profile: an assigned search succeeded, unassigned msearch returned 403
  `deny_default`, and the run credential was revoked after execution.
- The external adapter executed at the pre-provider boundary and received
  runtime MCP, but the public contract exposed no delegate-to-native-adapter
  operation and did not persist adapter-context mutation into the host snapshot.

### Requirement classification

| Requirement | Result | Basis / required adaptation |
| --- | --- | --- |
| Logical identity independent of provider/model/runtime | PASS | Separate agent identity and adapter/runtime configuration. |
| Durable task/run/session state | PASS | Persistent issue, heartbeat run, wakeup, task-session, and context rows. |
| Atomic claim/locking/recovery | ADAPT — WAITING | Claim/CAS and host-lease remediation pass locally; supported upstream release re-admission required. |
| Heartbeats/recurring execution | PASS | Durable wake queue, timers/routines, leases, retry scheduling. |
| Budgets/cost accounting | PASS | Agent budgets and run-linked cost events. |
| Native CLI/provider adapters | PASS | Codex/Claude/OpenCode/Gemini/Cursor/ACP and launcher surfaces. |
| Git workspaces/worktrees | PASS | Execution workspace and isolated worktree lifecycle. |
| Approvals/governance | PASS | Approval records, execution policies, governed MCP decisions. |
| Portable AI Factory skills | ADAPT | Sync Git-owned Agent Skills packages; do not make Paperclip rows canonical. |
| Secrets/artifacts/storage | PASS | Encrypted secrets and local/S3 storage provider interfaces. |
| Plugin/events/OpenSearch projection | ADAPT | At-least-once events require idempotency/reconciliation; runtime is alpha. |
| Context Resolver before a run | ADAPT — WAITING | Optional plugin enrichment proposal persists bounded same-run context before original dispatch; upstream acceptance required. |
| Independent Reviewer and QA | PASS | Separate agents and execution-policy participants with distinct grants. |
| Resume without original conversation/model | PASS | Reattach session when safe or reinvoke from durable task/context/workspace. |
| Operational truth without canonical project ownership | PASS | Git/memory/OpenSearch remain external authorities/projections. |
| Avoid a long-term fork | BLOCKER — UPSTREAM ACCEPTANCE | Clean independent proposals are prepared; no production private patch/fork is admitted. |

## Authority boundary

Once admitted, Paperclip owns task/run state, leases, wakeups, active agent/runtime bindings,
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

After admission, AI Factory custom work moves to Context Resolver, projections, engineering
workflow policy, capability compilation, memory/graph/model adapters, and evals.
Paperclip status terminology is mapped to AI Factory's logical lifecycle rather
than copied into another database. Native harness capabilities are preserved.

## Risks and gates

Paperclip is fast-moving and has correctness issues involving recovery,
silent-run liveness, MCP tokens/sessions, review replacement, and workspace
cleanup. The pinned revision failed two mandatory gates: environment-lease
cleanup after controller loss and transparent pre-run enrichment/delegation.
It must pass those plus the remaining restart/kill/stale-lock/duplicate-wakeup/
review/MCP-expiry tests at a fixed immutable revision. Source installation also
exposed Windows path, symlink, and native-build friction, so a supported
container/server deployment is the baseline.

## Exit/replacement strategy

All AI Factory-specific behavior talks through a control-plane integration
contract and stores canonical non-operational data outside Paperclip. To replace
it: stop admission, drain/reconcile leases, export operational rows and artifact
references, import the normalized task/run state into one replacement, switch
adapters, and rebuild OpenSearch projections. DBOS is a candidate only in that
mutually exclusive replacement architecture.
