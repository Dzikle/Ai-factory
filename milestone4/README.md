# Milestone 4 — bounded task measurement

Status: **FIRST SLICE OWNER-APPROVED AND INTEGRATED; native handoff accounting
repair and supervised restore/rebuild/recovery drills verified. Full Milestone
4/V1 acceptance remains incomplete: interrupted coding handoffs still lack
complete task cost. No performance/cost improvement is claimed.**

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
reports exit code 1 instead of `SIGTERM`/`SIGINT`). On a new disposable
migrated PostgreSQL instance, the exact published Linux production image then
passed **24/24** focused Stop, retry, independent-exit and delayed-handoff
tests, including the 16-case owned-Stop matrix. The prior revision's Linux
16/16 result remains historical; this 24/24 is evidence for the final revision.

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

### Restore, rebuild and model-call measurement — 2026-09-30

[Operations receipt](results/operations-20260930.json) records real dependency
loss and restore, not only archive readability or configured policy:

- Paired Paperclip PostgreSQL/storage restore used the exact deployed image,
  a separate PostgreSQL instance and internal network with no published port.
  All seven core authority-table row checksums/counts and schema matched before
  and after the restored controller started. The final capture contains 57
  issues, 257 runs and 241 leases; all 95 agents remained paused. AIF-55/56/57
  context artifact bytes matched their durable digests. Native result/usage
  snapshots are included in the full restored run-row comparison.
- MemPalace's pinned, prewarmed offline embeddinggemma image restored both full
  primary lesson envelopes into disposable storage; real semantic search
  returned four primary-resolvable results. The restored 24-tool read-only
  catalog was checked against an explicit allowlist. An actual add-drawer call
  returned the pinned server's read-only refusal `-32003`; the primary manifest
  stayed unchanged. The source service restarted and passed readiness/readback.
- The existing `ai_factory_docs_v1` index was actually deleted. Missing-index
  retrieval was observed before rebuilding 60 documents: 49 committed Git
  documents, two primary MemPalace records (including true superseded status)
  and nine selected native Paperclip scorecards. Full non-admin readback matched
  the primary snapshots. Native telemetry replay wrote zero documents.
- Five Git-path judgments passed recall@5=1, MRR=0.8667 and zero stale relevant
  hits after that rebuild. This is a small lexical smoke, not broad retrieval
  quality or proof of model improvement. Earlier ranks differed with corpus
  statistics; no relevance benefit is inferred from that change.
- Real OpenSearch MCP child SIGKILL/restart passed again. The server exposed
  only its four admitted tools; the two tested native agent profiles still
  exposed exactly `SearchIndexTool`. No grants or security roles were expanded.

Disposable drill containers, networks and volumes are removed. Private paired
backups/receipts remain under `.milestone0`; credentials, model transcripts and
backup bytes are not committed. These are supervised runbooks, not a new
autonomous healing service, event queue or observability store.

The bounded tools reuse existing credentials supplied by the operator:

```powershell
python -m milestone4.retrieval_eval --suite autonomy/evals/git-docs-v1.json --expect-revision <committed-head> --insecure-localhost
python -m milestone4.project_telemetry --state <private-board-state.json> --roster autonomy/evals/telemetry-v1.json
python -m milestone4.rebuild_projection --expect-revision <committed-head> --suite autonomy/evals/git-docs-v1.json --telemetry-roster autonomy/evals/telemetry-v1.json --paperclip-state <private-board-state.json> --confirm-rebuild-ai-factory-docs-v1
python -m milestone4.restore_drill --backup-dir .milestone0/<new-directory> --image <immutable-owner-image> --revision <paperclip-source-sha> --run <enriched-run-id>
python -m milestone4.memory_restore_drill --help
```

Reader variables are `AIF_DOCS_URL`, `AIF_DOCS_READER_USER/PASSWORD`; the telemetry
writer additionally uses `AIF_DOCS_WRITER_USER/PASSWORD`. For the local self-signed
cluster, telemetry requires `AIF_DOCS_LOCAL_TEST=1`. The destructive fixed-index
drill alone needs operator credentials (`AIF_DOCS_OPERATOR_USER/PASSWORD`) and
the existing primary `AIF_MEMORY_TOKEN`; those never enter native agents.
All agents must be paused with zero queued/running work before restore/rebuild.
Recovery is bounded: after a failed index replacement, retry source-derived
restoration once without a second delete; never report that failed drill PASS.
The telemetry roster is deliberately selected/bounded, not complete event history.

### Native free-model read-only probe

[Frozen probe receipt](results/read-only-20260930.json) retains three successful
native `opencode_local` primary calls under one logical agent and search-only
MCP profile. No coding stages were bypassed: these are explicitly read-only
policy questions with a pending owner disposition, not software candidates.

| Primary call | Exact answers | Input / cached input / output | Active seconds | Native reported USD |
| --- | --- | --- | --- | --- |
| AIF-55, Muse baseline | 8/8 | 44,983 / 30,276 / 2,043 | 38.451 | 0 |
| AIF-56, same Muse +4,354 context bytes | 8/8 | 55,580 / 36,932 / 1,705 | 83.834 | 0 |
| AIF-57, same agent/adapter, MiMO free | 7/8 | 20,272 / 55,040 / 1,498 | 38.997 | 0 |

Both Muse calls retain the ordinary canonical pre-run enrichment; this is not
a no-retrieval baseline. Additional context was verified against current Git
and the scoped projection before execution. MiMO returned `Git + canonical
Markdown/YAML` rather than the frozen literal `Git`. That is semantically
consistent with current documentation but remains **QUALITY_FAILED** under the
predefined exact-answer rubric; no automatic binding promotion follows.

The context call used more reported input and took longer with equal checked
quality. n=1, order/cache/provider variation prevent causal claims. Reported
free USD 0 is not invoice validation, paid-model coverage, task-total cost or
operator overhead. Configured prompt hashes identify supplied configuration,
not an independently captured rendered provider prompt. Supplied context does
not prove causal use. All three task workspaces stayed clean at `83c826a`; all
three primary leases were released. The original smoke actor configuration was
restored and it is paused. Prompt instructions are not filesystem/shell access
enforcement; the approved trusted-local isolation deferral is unchanged.

Two initial setup attempts (AIF-53/54) failed before provider invocation because
the runtime source/tracking ref and frozen project base disagreed with the
indexed accepted commit. They were cancelled, not counted as model failures.
The clean source and its tracking ref were fast-forwarded from the owner branch;
fresh probe issues used explicit immutable base refs. Old task worktrees and the
project's historical default base were not rewritten during those probes. The successful AIF-55
baseline was re-observed after an observer parsing correction, not reinferred.

Deployment synchronization must advance the clean controller source branch and
its tracking ref to the committed accepted branch, then set the project's
**future-task default** base to that same immutable revision through the native
project API. Preserve all other policy fields and existing task/worktree refs.
This avoids the next ordinary submission repeating the stale-base failure;
old run identities/artifacts and task branches are never reset. Prior default
`7254867f3172253a445f34511ae01e6ebbb94f5d` is retained here for configuration
rollback, which would also require a matching Git projection/source revision.

Fresh final validation: **182 Python tests run, 180 passed/two optional live
skips; 26/26 Node context/handoff/identity regressions; 9/9 formatter QA**.
Live drills above are separate evidence, not inferred from those skips.

### Remaining exit decision

The finite M0–M4 roadmap has no new milestone or dependency. M0–M3's approved
trusted-local demonstrations and M4's accepted scorecard remain usable. These
drills close the bounded operations evidence gaps, not full production readiness.
The remaining strict M4/V1 exit is **complete cost per owner-accepted correct
coding task across native handoff**, against its recorded baseline. The existing
cancel-on-handoff path can interrupt the provider's final usage report: retain
partial subtotals, never call them complete. The read-only calls above cannot
substitute for that gate or approve a code integration. Completing that gate
requires a fresh coding comparison with reliable full settlement and owner
acceptance; historical missing reports cannot be recovered by guessing.

Alternatively the owner may explicitly accept the bounded trusted-local V1 and
defer that measurement criterion. No such scope change has been assumed. Do not
declare all milestones finished, auto-approve pending tasks, add a second workflow
engine, or expand memory injection on this negative measurement evidence.
