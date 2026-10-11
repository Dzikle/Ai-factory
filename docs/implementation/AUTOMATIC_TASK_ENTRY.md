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

## Current native proof (updated 2026-10-11)

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
Later live deployment, fallback and restart results are recorded below; do not
infer them from these tests.

The compatibility image was deployed and returned the exact native Codex
assistant sentinel in AIF-83, but it exposed a second durability gap: the direct
(`legacy` runtime mode) initializer dropped the sealed fallback receipt. An
unwanted fresh primary/fallback pair followed. The test principal was paused;
these responses are **not a passing bounded fallback proof**. The three-line
atomic receipt preservation fix `e40e5b9730280b549e8adc1aec9114bd133d85d2`
reproduced the missing row evidence RED, then passed the real database regression
and serial 24-test route/fallback suite. That historical replacement image was:
`e40e5b9730280b549e8adc1aec9114bd133d85d2` / immutable index
`sha256:f816b541c61ecf73b48fb2801a26e6114db7212282759cf67153090317f3c2c9`.
The exact image passed 24 actual database/fallback tests and 64 OpenCode tests,
without overlays; the fresh pinned Factory check passed 339 tests (2 skipped).
Cutover preserved all seven authority tables, schema, configured credentials,
storage, networks and ports. The existing paired backup was still current by
exact preflight on October 11; all earlier backups are retained.

The real no-tool replay succeeded on Codex in run
`3c7b29ee-06f2-407c-9aba-0c251992e65a`, returned the exact assistant sentinel,
and retained the full sealed one-switch receipt. An idle controller restart
preserved that receipt, the three task states/plans, native independent decisions,
the clean exact AIF-82 candidate, Tests artifact and qualified registry.

The next replay exposed another gap: native `finish_successful_run_handoff` created a new
primary OpenCode run after that success because the no-tool canary intentionally
did not choose an issue disposition. This path is separate from immediate
recovery, whose guard already respects the receipt. Only the canary was paused;
its extra scheduled fallback was cancelled, and there are no active runs.
The earlier positive fixture completed its issue inside the external adapter
double and did not cover this unfinished-issue followup. On October 11 the owner
approved retaining the already qualified selection for same-agent/same-task
native continuations. Source `3f1194caa926084d1862ac4ce8690841a690c5b0` now
passes 134 focused tests and direct server type-checking. Actual PostgreSQL
regressions cover unfinished success, bounded/liveness followups, deferred
promotion/restart, competing runs, lineage forgery, revocation and lock release.
A fresh review's two Important queue-path findings were reproduced RED and
fixed GREEN in one pass; no Critical or Minor findings. The normal multiarch
build and PID-1 gate passed. This fix is now deployed at immutable index
`sha256:b1ed65f02e37aaccd9566db0852d0440048aaf28f95fd86f94bd7b8109eb343a`
(AMD64 `sha256:b3e1edc8179d3aa76809c38e70cc7fb702e316a1e3111306ae2bba0dc36f6044`).
Exact-image tests, without overlays or production mounts, passed 134 actual
database/policy tests and 64 OpenCode tests. Node 24.21.0, Codex 0.161.0 and
OpenCode 1.18.35 were verified by isolated CLI invocations.

The new same-task replay has exactly three native runs: rejected OpenCode
`e3d52f5e-deb6-41b7-8c70-cc84ab086295`, selected Codex success
`ee9c6a98-e5f7-4f12-bb37-a85f81a64a6c`, and automatic Codex handoff success
`1176ebe4-05ce-4da9-9ae9-4216a8d235e0`. Both successful runs returned exactly
`AIF_NATIVE_FALLBACK_READY`, retained identical sealed one-switch receipts, and
started with no prior session and `forceFreshSession: true`. The persisted
system/heartbeat `finish_successful_run_handoff` wake links the latter to the
selected parent. The logical agent remained configured as OpenCode; no principal
provider rewrite, second switch or fresh primary bounce occurred. The native
handoff limit stopped further runs. Only this operator test was marked done;
its principal is paused/hidden and all prior failed attempts remain in history.

Cutover and a fresh idle-controller restart preserved all seven authority
tables, schema, configured credentials, storage, networks and ports. Restart
also preserved all three task states, plans, independent decisions, the exact
clean AIF-82 candidate, native Tests artifact and installed qualified registry.
Restart baseline SHA256:
`169413a8539635a1b2ce26cbef8f1ba78dfed97333227a6f63ce684c607c1f53`.
This completes the automatic-entry correction's trusted-local evidence gates;
AIF-82 still requires owner approval and has not been integrated or published.
See `milestone2/results/automatic-task-entry-20261010.json`.

Owner-approved disk cleanup removed only the unused a15 and, under separate
approval, unused 940 intermediate images. New 3f, prior e40 and stable rollback
images, all 38 volumes and all backups remain intact. Windows C had 6.6GB free
immediately after removing 940 and about 4.6GB after the new backup/image proof.
The fresh paired backup for this cutover is
`.milestone0/automatic-entry-followup-cutover-20261011/` (archive/hash validated,
not a fresh restore rehearsal); earlier backups and the e40 image are retained.
No broad prune, Docker reset or virtual-disk compaction was performed.

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
5. Require separate immutable deployment, live provider and restart evidence
   for the review's declined runtime judgment; cost if wrong: green source tests
   would not support local runtime acceptance.
6. Disclose unrelated full-repository failures without expanding remediation or
   claiming a clean repository; cost if wrong: those defects may affect other paths.

Deferred minor: the automatic-intake UI label can appear for a non-todo task;
this does not dispatch backlog work. The execution/verification skills kept the
final fix pass bounded and prevented treating configuration as live proof.
