# Milestone 4 — bounded task measurement

Status: **FIRST SLICE OWNER-APPROVED AND INTEGRATED; bounded native handoff
accounting repair deployed and verified. Full Milestone 4 remains incomplete;
no performance/cost improvement is claimed.**

The initial owner-approved comparison used a read-only task scorecard and one
small serial pair of native tasks, with/without the current verified memory
lesson. It changed no image. The later accounting repair below updates only the
existing owner-fork controller image and scorecard; model bindings,
authentication and review policy remain unchanged. No new store, scheduler,
routing or self-healing platform was added.

## Scorecard

```powershell
python -m milestone2.task --state <private-board-state.json> scorecard AIF-49
python -m milestone2.task --state <private-board-state.json> --json scorecard AIF-49
```

The CLI reads the scoped native issue/run/activity/cost APIs. Paperclip still
owns all operational state. Output is a bounded, non-atomic observation, not a
new ledger; no prompts, logs, credentials or adapter configurations are exported.
At most 50 runs/1,000 activity records are supported. A descendant-inclusive
cost summary is rejected when it includes other issues.

Missing/invalid tokens or cost are **unknown**, even if the native aggregate is
zero. Coverage and known subtotals are separate from complete totals. Cost is
native reported USD, not invoice verification; cost per owner-accepted task is
not cost per accepted *correct* task until independent evidence is checked.
Run cancellation during native reassignment is a handoff, not automatically
task failure. Retry counts use explicit native retry lineage, not stage count.

Participant separation compares declared review identities with run-linked
first-stage request actors in native activity. Recovery's mutable return owner
is not used as original Developer identity. Missing linked evidence means
unknown. This is not proof that all declared participants actually reviewed;
stage decisions and independent commit-bound receipts remain necessary.

## Paired task contract

Both trials improve the human-readable scorecard formatter from the same
frozen foundation, using the existing Developer/Reviewer model and native
Tests → Reviewer → QA → owner policy. Only the formatter body and its new tests
may change. Independent stages validate isolated committed copies; the frozen
external presentation contract and protected collector AST cannot be edited
by a candidate. The baseline still gets ordinary Git/repository access and the
existing canonical Git pre-run enrichment. The treatment adds only one bounded
primary-verified MemPalace lesson prepared by the existing supervised recall.
No privileged memory credentials enter agent execution.

The task base is `e66b1ca34e8b8aeecb2faf8d14ffb01e7351763a`, passed explicitly
to the independent stage checker. Its reference comes from that committed tree,
not the controller source checkout's mutable HEAD/working files. Only one
formatter's body is normalized; signatures/decorators and all other AST nodes
remain protected. Independent review found these two initial guard weaknesses;
six focused regressions reproduced four failures and pass after correction.
The external presentation contract now includes complete nonzero accounting
as well as missing/zero/partial cases. Evaluator corrections are separate from
the frozen candidate base. AIF-50 was held before validation during this fix;
that supervised interruption must be recorded, not credited to either model.

This is one serial pair, not randomized or statistically conclusive. Provider
cache, ordering, free-tier variability and Reviewer behavior can affect timing.
Supplied context is verified separately from inferred use; output similarity or
a task comment is not evidence that a model used memory. Missing native usage
remains a measurement limitation, not an assumed saving. Unapproved candidates
must not be counted as accepted correct tasks or integrated.

## Results — 2026-09-29

[Machine-readable receipt](results/pair-20260929.json) contains the exact native
task/run/commit/tree identities, context and independent receipt digests, model
bindings and observed scorecards. It is an experiment snapshot, never task truth.
Live task state remains exclusively in Paperclip. The table below preserves
the pre-approval observation; the later approval/integration receipt follows.

| Observed metric | AIF-50: baseline | AIF-51: memory advice |
| --- | --- | --- |
| Native quality gates | Tests/Reviewer/QA passed; owner pending, 3/4 | Same, 3/4 |
| Python validation | 133 run, 131 passed, two optional live skips | Same |
| Independent presentation QA | 9/9 passed | 9/9 passed |
| Changes-requested rounds / failed runs / native retries | 0 / 0 / 0 | 0 / 0 / 0 |
| Active native runtime, all four stages | 226.396 s | 311.160 s |
| First-run-to-last-run execution window | 792.944 s | 359.375 s |
| Task description / additional advice | 3,237 bytes / none | 4,491 bytes / +1,254 bytes |
| Token/cost coverage | 0/4; totals unknown | 0/4; totals unknown |
| Owner-accepted correct tasks | 0 pending approval | 0 pending approval |

Both task titles and common instructions are identical. Recent-title duplicate
detection safely replayed AIF-50 during initial treatment creation; a new stable
request key plus Paperclip's supported `allowDuplicate: true` created the
intentional independent trial. General CLI deduplication was not disabled.
Both Developer runs had `sessionIdBefore: null`, the same pinned starting commit,
and the same configured native OpenCode model:
`opencode/muse-spark-1.3-contributor-free`. Separate logical Reviewer identity
used that same configured binding; deterministic Tests and QA used process
adapters with stripped child credentials. Selected bindings remained unchanged.

The canonical Git enrichment artifact was 3,545 bytes in each Developer run;
both durably retain its reference/digest, independently checked against actual
bytes. Their canonical document/source blob is identical. The treatment
description/run snapshot additionally contains primary-verified lesson
`lesson-python-test-dependencies-v2`. Recall prepared 1,253 bytes; existing task
text normalization trims its final newline, supplying 1,252 advice bytes plus
two separator bytes. Exact description/suffix digests are in the receipt.
Supplied advice is proven; causal model use is not.

The baseline's Validator was briefly paused before any validation while
independent review corrections were applied, leaving a native blocked state.
Supported resume reopened the same first review stage without approving it,
changing the candidate, or creating a second Developer writer. The corrected
guard reproduced four failures in the old fixture and passes all six regressions.
The independent reviewer rechecked all reported guard/accounting fixes. Both
QA stages needed explicit supervised native wakeups after Reviewer handoff;
they retained their own run identity/participant. All four handoff runs per
trial are `cancelled/issue_reassigned`, with durable stage decisions and
commit-bound receipts; these are not provider failures. Both tasks have clear
execution/checkout locks and zero live runs at receipt collection.

**Conclusion:** this pair shows equal checked quality, no demonstrated benefit
from adding this advice, and higher active runtime for the treatment. The
baseline's wall window includes infrastructure preparation; provider/cache/order
effects and n=1 prohibit causal/general speed claims. Both prompts already
included the dependency setup that the lesson advises. Native handoff usage
remains unavailable, not zero; no cost-per-accepted-correct-task metric or token
saving can be computed. Manual setup/orchestration/review costs are also outside
the native scorecard. Do not expand automatic memory injection on this evidence.

Owner-selected integration candidate: **AIF-50**, commit
`4afce50c325129ad0ad8168c146b3fad7dd8d302`, with its smaller formatter body and
equivalent checked contract. Its original commit is preserved on local branch
`m4-aif50-candidate`; the alternate `c653361216a9c2333f5695346feb5da3c73dfc87`
is preserved on `m4-aif51-candidate`. The independently reviewed foundation and
evaluator corrections remain in its history on `milestone4-scorecard`.
AIF-50 is integrated into accepted `milestone1-contracts`; AIF-51 is not.
Primary `main` remains unchanged.

Foundation validation: **130 run, 128 passed/two optional live skips**, including
24 CLI/API scorecard tests and six evaluator regressions; existing context,
committed-handoff and identity Node regressions **26/26**. Candidate validation
counts differ because the evaluator corrections remain outside their frozen
task trees. Fresh combined validation is recorded below; no skipped test is
counted as live evidence.

### Approved integration — 2026-09-29

The owner's explicit **Merge** instruction selected AIF-50. Its three stored
context/Tests/QA artifacts were rechecked against actual bytes and native run
identities before relaying approval. Paperclip recorded owner decision
`d725d2e4-147b-42e5-a69b-ada774c0c37d` at `2026-09-29T06:34:46.730Z`:
`done`, 4/4 gates, verified user actor, clear execution/checkout locks.
AIF-51 remains unapproved at 3/4; the original paired snapshot is unchanged.

Candidate merge `bd139d1dd9d6877f8cfc01807f2eac048316e8a4` preserves the native
commit. Accepted integration `03e443a5218032a2bbc55a1cfda29ce6b9368262` has tree
`2d45cd7285e84b4de0f7987ef8d9d706a52e96ca`. Fresh combined and accepted-branch
checks ran **139 Python tests: 137 passed, two optional live skips**; external
presentation QA **9/9** and context/handoff/identity Node regressions **26/26**
passed. No skipped test is counted as live evidence.

The existing controller source checkout was advanced to that accepted revision
on `milestone1-contracts`; workspace refs and the native project base matched.
Its credential-stripped checker repeated 139 tests (two skips) and QA 9/9.
Live read-only scorecard reports AIF-50 accepted, 4/4, with tokens/cost still
unknown. Zero company live runs were observed. Existing one-shot projection
updated 49 canonical documents; reader-only replay planned zero writes.
The subsequent receipt-only commit is carried through the same checkout and
projector. No image, service, credential, model binding or migration changed.
At that checkpoint this was a **local merge**, not a push or PR; primary `main`
stayed at `71b5a5d`.

Next: trustworthy native handoff usage/cost evidence. Full Milestone 4 remains
open for trustworthy native handoff telemetry, broader retrieval judgments and
recorded bounded operations/drills. Do not add another observability platform
or routing/healing system merely to fill this telemetry gap.

### Native handoff accounting repair — 2026-09-29 to 2026-09-30

The owner Paperclip fork branch `ai-factory/milestone4-handoff-usage` at
`3ef2f39c4ff0e7fd11b31bf472df09f36839195d` retains
a successful process-Stop settlement until its exact executor writes late
metadata, while failed Stops remain immediately retryable. Cancelled/failed
usage is marked `partial`. OpenCode no longer fabricates zero usage/cost from
an unfinished stream, and its finished-step usage is explicitly per-run.
The AI Factory branch `milestone4-handoff-usage` (now fast-forwarded into the
accepted `milestone1-contracts` branch) shows partial observations as known
subtotals, never as complete task totals. No new authority or service was
introduced; the running controller was **not** replaced at this checkpoint.

Test-first evidence: the handoff regression failed with `usageJson=null` before
the fix and passed **2/2** on a separate migrated PostgreSQL database; the
failed-Stop retry reproduced a regression during the first correction and
passed after preserving its retry path. Adjacent live-DB checks passed **5/5**,
and the existing owned-Stop matrix passed **16/16**. OpenCode parser checks
passed **14/14**, targeted adapter-result checks **3/3**, adapter typecheck and
isolated Linux server `tsc --noEmit` passed. Scorecard checks passed **43/43**;
independent formatter QA passed **9/9**. Local host server typecheck remains
blocked by a pre-existing stale generated runner manifest; the complete Python
suite ran 143 tests with two optional live skips and one unrelated, unchanged
provenance-schema test failure. The disposable test database and source shadow
were removed after verification.

Independent review found three more accounting gaps: Stop after child exit but
before adapter cleanup, historical cancelled runs without a completeness marker,
and malformed nonempty OpenCode JSONL lines. The final owner-fork commit
`3f4b73c8febcbc4956f8b8d84ff0d815f87786d2` retains same-run legacy
spawn ownership until adapter result settlement; the scorecard excludes unmarked
non-successful usage (old parser zeros are not evidence); malformed stream lines
leave usage/cost unknown. The post-child-exit regression failed on the old
condition with `usageJson=null`, then passed with the correction. On migrated
disposable PostgreSQL, delayed handoff cases passed **3/3**. OpenCode parser and
adjacent adapter tests passed **15/15**, adapter typecheck passed; AI Factory
scorecard **44/44** and independent formatter QA **9/9** passed. The broader
Windows process-Stop matrix had 17 POSIX signal-expectation failures (Windows
reports exit code 1 instead of `SIGTERM`/`SIGINT`); these are **not** counted as
passing Linux tests. The prior revision's Linux 16/16 result remains historical.

The owner-fork [CI run](https://github.com/Dzikle/paperclip/actions/runs/36650114983)
passed both normal production platform builds and the PID-1 reaping check.
The immutable deployed image is
`ghcr.io/dzikle/paperclip@sha256:d195b970b077b872bb4e720915dc53a97a9096d0f35e29030d37233cc0c0b273`
(linux/amd64 manifest
`sha256:c4b96d2af15c9e5d795e3bc862671760aa11eb06e767cfa22e3b3f49e64400ab`);
its revision label matches `3f4b73c8`. The existing PostgreSQL 17.11 database
remained at 283 Drizzle journal rows and core authority counts unchanged across
cutover: 1 company, 95 agents, 51 issues, 245 runs and 231 leases. All agents
were paused and no runs were active before cutover. The controller is healthy
after deployment and restart.

Paired pre-cutover recovery material remains in Git-ignored
`.milestone0/m4-usage-precutover-20260930/`: PostgreSQL custom dump SHA-256
`8bc5d460b26ace707c6abdadc75d58be254267c241692883613c003f1a251abd`
(2,142 readable archive-list lines) and storage tar SHA-256
`6c9284b22ef9194b579aaa151428ff29856f2cd089d8eafd531323200ceb2649`
(15,537 readable entries). This validates archive readability, **not** a fresh
restore rehearsal. Backups contain private data and must not be committed.

Fresh synthetic task **AIF-52**, defined by
`milestone4/tasks/native-handoff-accounting-probe.json`, ran the unchanged
native `opencode_local` adapter on
`opencode/muse-spark-1.3-contributor-free`. Its Developer run
`e5f65f3c-0910-4b00-ab0e-0ddf28a019f6` reached
`cancelled/issue_reassigned`, with durable `usageCompleteness=partial`,
27,487 observed input, 60,823 cached-input and 1,712 output tokens. The
provider reported USD 0 for this free model; no native cost-event row was
emitted for the zero-priced run. After controller restart, the same run still
has the partial snapshot. The read-only scorecard shows one handoff, one
partial-covered run, zero fully covered runs, known reported cost subtotal 0,
and **no** complete task cost or cost-per-accepted-task. The probe was cancelled
without merging its synthetic file; execution/checkout locks are clear, its
single ephemeral local lease is terminal (`expired`, `released_at` set), and
all agents are paused. The disposable PostgreSQL test container was removed;
the paired backup was retained. The accepted branch was pushed to the owner's
`Dzikle/Ai-factory` repository; primary `main` remains the earlier adoption
spike commit and was not rewritten.

This closes the bounded native handoff accounting repair, **not** all of
Milestone 4. Historical AIF-50/AIF-51 receipts were not backfilled. Their
unfinished final steps remain lower-bound observations, and broader retrieval
quality, priced-model coverage, and operational metrics remain open.
