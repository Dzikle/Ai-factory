# Milestone 4 — bounded task measurement

Status: **FIRST SLICE VERIFIED — awaiting owner approval/integration. Full
Milestone 4 remains incomplete; no performance/cost improvement is claimed.**

Owner-approved scope: a read-only task scorecard and one small serial pair of
native tasks, with/without the current verified memory lesson. Existing services,
model bindings, authentication and review policy stay unchanged. No new image,
store, scheduler, routing or self-healing platform.

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
Live task state remains exclusively in Paperclip.

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

Recommended integration candidate: **AIF-50**, commit
`4afce50c325129ad0ad8168c146b3fad7dd8d302`, with its smaller formatter body and
equivalent checked contract. Its original commit is preserved on local branch
`m4-aif50-candidate`; the alternate `c653361216a9c2333f5695346feb5da3c73dfc87`
is preserved on `m4-aif51-candidate`. The independently reviewed foundation and
evaluator corrections are on `milestone4-scorecard`; no candidate has been
merged into accepted `milestone1-contracts` or primary `main`.

Foundation validation: **130 run, 128 passed/two optional live skips**, including
24 CLI/API scorecard tests and six evaluator regressions; existing context,
committed-handoff and identity Node regressions **26/26**. Candidate validation
counts differ because the evaluator corrections remain outside their frozen
task trees. The full current foundation and candidate must be tested together
again after approved integration. No skipped test is counted as live evidence.

Next: owner selects/approves one candidate, then integrate that exact commit,
retest and deploy through the existing source checkout. Full Milestone 4 remains
open for trustworthy native handoff telemetry, broader retrieval judgments and
recorded bounded operations/drills. Do not add another observability platform
or routing/healing system merely to fill this telemetry gap.
