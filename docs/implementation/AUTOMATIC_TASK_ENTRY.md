# Automatic task entry — owner-authorized correction

Approved by the owner on 2026-10-06 for continuous execution, without step-by-step
approval. This completes the original Orchestrator contract; it does not reopen
dependency adoption or add a control plane.

## Acceptance

Select a registered project, enter a task, and start it. Its project Orchestrator
is the default entry point. It saves classification, acceptance criteria and
provider decisions in Paperclip. Questions/analysis return evidence directly;
coding hands the same task to a Developer with native independent Tests,
Reviewer, relevant QA and owner integration approval. The owner need not select
a workflow/model. Explicit specialist assignments and existing staged tasks
remain respected. Historical fixtures are hidden, not deleted.

Models are selected from explicit, currently qualified runtime profiles:
free-first, then approved authenticated fallbacks. Catalogue entries or installed
binaries alone are not readiness evidence. Unsupported/uncredentialed runtimes
remain unavailable. Native harness adapters remain native. Decisions and bounded
fallback attempts must be visible and durable; missing cost is unknown.

## Implementation boundaries

- Paperclip owns tasks, locks, runs, budgets, retries and stage transitions.
- Project bindings and routing policy are versioned Factory configuration.
- Only run-scoped credentials reach agent helpers; no board token in agents.
- No background queue/database, nested CLI execution, duplicate adapter, or
  automatic integration approval.
- Use a small opt-in native task-entry default plus deterministic handoff helpers.
  Preserve explicit assignments and fail closed on invalid project bindings.
- Do not modify dirty source repositories or publish sparse mobile snapshots.

## Execution / evidence ledger

1. Baseline: 301 Python tests pass (2 skipped). Mobile controller UID1000 cannot
   inspect root-owned snapshot: reproduced Git dubious ownership. Targeted
   ownership repair of the mobile snapshot and its worktree parent now passes
   plain Git as UID1000, clean pinned HEAD unchanged. Provisioner regression
   prevents repeating the root-only admission mistake.
2. Implement/test native default entry, bounded classification/plan persistence,
   native handoff and provider readiness/fallback policy.
3. Provision/reconcile only real project roles; hide historical fixtures with
   preserved audit history. Keep existing tasks and approvals intact.
4. Prove actual dashboard/API default task path, resume AIF-81, exercise coding
   delegation and provider-loss fallback; verify durable results after restart.
5. Run full checks and independent review, record exact deployed revisions and
   residual credential limits, commit/push owner repositories.

## Current native proof (2026-10-10)

The opted-in root-task start path is deployed. AIF-82 started with only its
registered project selected: Paperclip selected the Mobile Orchestrator,
persisted plan revision `d3293a97-5889-4da3-b450-9c7fd0e9ae9b`, and handed the
same issue to its Developer. The helper selected the qualified subscription
profile because a fresh free-runtime probe returned provider 403. No operator
selected a specialist, installed the task's policy, or advanced a review stage.

Native Tests and Reviewer independently approved README candidate
`c78f55809a98a4713ca5cc5006d7ed0419829617` / tree
`9947fcb2dea26f6f0e1e89a2a51eee9d0c76d7fb`; their run-linked records report
82 passing mobile tests, typecheck, lint and documentation checks. The task is
`in_review`, with two completed stages and **owner approval pending**. Native
handoffs cancel the outgoing runs with `issue_reassigned`; these are not failed
task executions. This is a README-only task (`ux: false`), so QA is not required.
No mobile integration, publication, deployment or owner acceptance is claimed.

AIF-81's earlier recovered analysis result and revisioned plan remain durable;
its successful Codex native run is the qualification receipt used by the
subscription binding. A historical free success is not current availability.
Exactly 18 real logical roles across the three projects are reconciled and
active; historical fixture principals are hidden with metadata, not deleted.

The first AIF-83 no-tool fault probe exposed a real OpenCode 1.18.35 wire-format
gap: bootstrap rejection is `APIError` with numeric status 403, not only
`APICallError`. Its unsuccessful attempts are retained. The minimal typed-event
compatibility fix (`94061426a665f7edabe8add6e69de7bba133f8b5`) passed a failing-
then-passing regression and 64 Linux OpenCode source tests. It keeps the
no-text/no-tool/no-completed-step guard and one qualified, board-approved switch.
Final deployment, real fallback and restart receipts are being completed; do not
infer them from these tests.

The compatibility image was deployed and returned the exact native Codex
assistant sentinel in AIF-83, but it exposed a second durability gap: the direct
(`legacy` runtime mode) initializer dropped the sealed fallback receipt. An
unwanted fresh primary/fallback pair followed. The test principal is paused;
these responses are **not a passing bounded fallback proof**. The three-line
atomic receipt preservation fix `e40e5b9730280b549e8adc1aec9114bd133d85d2`
reproduced the missing row evidence RED, then passed the real database regression
and serial 24-test route/fallback suite. Its replacement image is building.
Final replay and restart acceptance must use that replacement, not the flawed
intermediate image. See `milestone2/results/automatic-task-entry-20261010.json`.

## Using the entry point

In the existing Paperclip dashboard, select Licitacija Web, Travel Agent or
Licitacija Mobile, enter a task, and start it (`todo`). Leave the assignee and
workflow unspecified to use project intake. Backlog entries do not run. Explicit
specialist assignments, child tasks, existing staged tasks, holds and budgets
retain their native semantics. An unavailable opted-in Orchestrator fails closed.

The owner-only reconciler is `python -m milestone2.scripts.automatic_entry_setup`
with `--state <private-board-state>` and `--output <private-receipt>`; it defaults
to dry run. Apply only after a fresh paired database/storage backup, with
`--apply`. It does not dispatch tasks. Project bindings live in
`milestone2/config/automatic-entry-projects.json`; helper code and the per-project
qualified registry are installed root-owned and read-only to agent UID1000.
Only native run-scoped credentials reach the Orchestrator helper.

## Limits and decisions

Full Paperclip verification is not green: the Windows root launcher fails at
`spawnSync pnpm ENOENT`; Windows adapter symlink/skill fixtures fail; existing UI
token violations remain. The earlier broad Linux run exhausted local disk and
did not finish. It was not repeated. Targeted source/image tests and production
builds are reported separately. Complete cost per accepted coding task remains
unknown across interrupted handoffs; no saving or zero-cost conclusion follows
from partial native usage. Additional isolation and physical-device validation
remain outside this trusted-local proof.

Rulings carried from the execution ledger:

1. Use this owner-approved five-step evidence plan as the recovery contract;
   cost if wrong: manual task briefs and explicit review packaging.
2. Treat the fresh readiness probe as authoritative over historical free
   success; cost if wrong: a subscription is used when free may sometimes work.
3. Put opt-in entry in Paperclip's native create/start route, not another queue;
   cost if wrong: the owner fork carries a route patch.
4. Admit one typed zero-work bootstrap fallback only; cost if wrong: post-work
   provider loss remains fail-closed.

Deferred minor: the automatic-intake UI label can appear for a non-todo task;
this does not dispatch backlog work. The execution/verification skills kept the
final fix pass bounded and prevented treating configuration as live proof.
