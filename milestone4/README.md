# Milestone 4 — bounded task measurement

Status: **IN PROGRESS — first slice, not a completed performance claim.**

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

This is one serial pair, not randomized or statistically conclusive. Provider
cache, ordering, free-tier variability and Reviewer behavior can affect timing.
Supplied context is verified separately from inferred use; output similarity or
a task comment is not evidence that a model used memory. Missing native usage
remains a measurement limitation, not an assumed saving. Unapproved candidates
must not be counted as accepted correct tasks or integrated.

Test results, task/run/artifact identities and trial outcomes will be appended
here after execution. Full Milestone 4 exit criteria (complete telemetry,
broader retrieval judgments and recorded bounded operations/drills) remain open.
