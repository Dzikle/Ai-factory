# ADR 001: Adopt Paperclip as the operational control plane

**Status:** Admitted owner-maintained fork `62760ac9fc69572866c8eed5ad714ab1ddd6cc23`; Milestone 1 unblocked

**Date:** 2026-09-15

## Milestone 0 final admission — 2026-09-25 (current)

The owner-maintained fork is admitted as the **sole task/run/workspace and active
MCP-policy authority** at commit
`62760ac9fc69572866c8eed5ad714ab1ddd6cc23`, local production-image ID
`sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455`
and PostgreSQL 17.11/283-row Drizzle journal. The exact image's 66 focused
regressions passed; an isolated 279→283-row in-place migration preserved all
baseline issue/run/lease/workspace identities without journal edits.

Real Docker kills of active controller runs were repeated with restart before
and after the controller lease expired. Startup/orphan recovery and explicit
effect reconciliation/resume produced terminal source and successor leases,
stable cleanup receipts on repeated checks, cleared locks and non-overlapping
writers. The exact effective external MCP catalog was search-only after broad
generated grants were removed; disallowed msearch remained deny-default. The
optional pre-run hook persisted a verified artifact ref/SHA-256 in the same
run, then the original native `process` adapter consumed it. The record
survived restarts and a paired DB/storage restore; restored counts and artifact
bytes matched. Full receipts are in the [admission report](../../implementation/MILESTONE_0_DEPENDENCY_ADMISSION.md).

This changes admission status, **not** the authority split or selected OSS
stack. AI Factory still owns the narrow fork delta, upstream tracking,
security rebases and build provenance. The admitted image is local, not a
registry-published release; publish an owner-controlled immutable artifact
before remote deployment. Git, MemPalace and OpenSearch keep their separate
canonical/projection roles. CodeGraphContext remains disabled under its own
security gate. The older pending/waiting statements below are historical.

## Owner fork amendment — 2026-09-23 (historical pending state)

The owner explicitly chose to keep the required Paperclip changes in the
account-owned [Dzikle/paperclip](https://github.com/Dzikle/paperclip) fork rather
than seek upstream merge. The two upstream PRs were closed at the owner's
direction. The maintained branch `ai-factory/milestone0-maintained` combines
the SSH lease fix and optional pre-run enrichment at immutable commit
`a0225e8f8ae7ce16d9f52ac25e64702d7ddb173f` (upstream base
`8326e33adad63e26c918edf6adf6db114997eced`). No future upstream PR or
direct upstream push is authorized without separate owner approval.

This changes **distribution and maintenance ownership**, not execution
authority: Paperclip remains the intended sole task/run/workspace/MCP-policy
authority; AI Factory does not add DBOS or a second task engine. AI Factory now
owns rebases, security updates, release provenance, regression tests, and an
exit path back to upstream or another control plane. Prefer a small auditable
fork delta; track upstream read-only. The combined source-equivalent Linux tree
passed 121/121 focused server tests, 2/2 plugin SDK tests, monorepo typecheck,
and normal build. This is **not admission**: the build stamp is not the exact
fork revision, and baseline database migration plus live Docker/PostgreSQL
recovery/capability/enrichment/restore gates remain unrun. Milestone 1 stays
blocked until the [admission report](../../implementation/MILESTONE_0_DEPENDENCY_ADMISSION.md)
records an immutable fork image and all gates PASS.

The 2026-09-22 and earlier amendments below are historical evidence; their
upstream-release and no-fork requirements are superseded by this owner decision.

## Historical Milestone 0C amendment — 2026-09-22

The two independent, upstream-compatible remediations are now real Paperclip
contributions: [PR #13772](https://github.com/paperclipai/paperclip/pull/13772)
for SSH host-workspace lease recovery and
[PR #13773](https://github.com/paperclipai/paperclip/pull/13773) for optional
durable pre-run run-context enrichment. Both target upstream
`8326e33adad63e26c918edf6adf6db114997eced` and remain open. Exact heads
are respectively
`e319a7e8ddeba95274616d042d143c2343fc6031` and
`0b455c84c0c4b52a7bd6b6b99e16863cd4a16c10`.

Upstream #13717 landed local bookkeeping-lease recovery during preparation, so
#13772 was narrowed to the missing SSH equivalent while retaining local/SSH
regression coverage. This preserves upstream architecture instead of carrying a
redundant private implementation. The enrichment proposal remains a separate,
generic plugin contract. Review drove a narrower credential lifecycle: one
five-minute, run-scoped MCP token per enricher callback, immediate revocation,
and a separate native-adapter token. A further security review led to explicit
instance-admin approval per plugin/company; ordinary company settings cannot
activate enrichment. Plugin workers remain trusted installed code, not an
untrusted-code sandbox. Company access also gates the approval route. Focused
tests pass 58/58 and 54/54;
recovery also reapplies persisted bounded prompt text when the task prompt is
rebuilt. Monorepo typecheck and normal production build passed through the
preceding enrichment revision; the final company-access guard passed its route
suite and server TypeScript check. The next CI run identified a missing OpenAPI
entry for the approval endpoint; `0b455c84c` adds the contract and regression
test (52/52 affected tests and server TypeScript check pass). Upstream review
and corrected-head CI remain
merge gates.

The decision remains conditional. No supported merged revision/release contains
both requirements, so no baseline-database migration or release re-admission was
performed. Paperclip is **WAITING FOR UPSTREAM**, Milestone 1 remains blocked,
and neither fork branch is an authorized production distribution.

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
| Atomic claim/locking/recovery | ADAPT — ADMITTED | Claim/CAS, child loss, both live controller-loss timings, source/successor lease convergence and repeated receipts pass on the exact fork image. |
| Heartbeats/recurring execution | PASS | Durable wake queue, timers/routines, leases, retry scheduling. |
| Budgets/cost accounting | PASS | Agent budgets and run-linked cost events. |
| Native CLI/provider adapters | PASS | Codex/Claude/OpenCode/Gemini/Cursor/ACP and launcher surfaces. |
| Git workspaces/worktrees | PASS | Execution workspace and isolated worktree lifecycle. |
| Approvals/governance | PASS | Approval records, execution policies, governed MCP decisions. |
| Portable AI Factory skills | ADAPT | Sync Git-owned Agent Skills packages; do not make Paperclip rows canonical. |
| Secrets/artifacts/storage | PASS | Encrypted secrets and local/S3 storage provider interfaces. |
| Plugin/events/OpenSearch projection | ADAPT | At-least-once events require idempotency/reconciliation; runtime is alpha. |
| Context Resolver before a run | ADAPT — ADMITTED SEAM | Optional plugin enrichment persists bounded same-run artifact/digest before original adapter dispatch; the actual AI Factory Resolver remains Milestone 1 work. |
| Independent Reviewer and QA | PASS | Separate agents and execution-policy participants with distinct grants. |
| Resume without original conversation/model | PASS | Reattach session when safe or reinvoke from durable task/context/workspace. |
| Operational truth without canonical project ownership | PASS | Git/memory/OpenSearch remain external authorities/projections. |
| Owner-maintained fork discipline | ADAPT — ADMITTED | Exact-image migration and live gates passed. Track upstream read-only, maintain security/rebase provenance, and publish an immutable owner-controlled artifact before remote deployment. |

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
