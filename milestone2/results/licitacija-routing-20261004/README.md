# AIF-78 — coding route repaired, awaiting owner approval

The same task now has Developer → tests → independent Reviewer → QA → owner
approval. Paperclip records `in_review`, **3/4 gates**, no active execution or
checkout lock. The correction and native checks are complete; website integration
and deployment are **not authorized/performed**.

Candidate `b7d35ccc67437a28d43446e6e88894e200920c63`, tree
`9b5af0234779dfb6c030c462516acc19fff8705b`, snapshot base
`0b8cb9647bf08cb8c269c1c89ad746d0db76d95c`. Native Developer reused AIF-58's
existing reviewed code on AIF-78's own task branch rather than duplicating the fix.
The old feature-branch publication is historical, not a new merge/deployment.

| Independent stage | Run | Result |
| --- | --- | --- |
| Developer / native Codex | `164644fc-7575-4128-8520-18e93239bcd3` | Exact candidate reused; browser 5/5, syntax and diff checks passed. |
| Validator / process | `7c1f6106-141e-4eab-95ba-1737b31f17eb` | [5/5](validator.json), SHA-256 `075df9a3bda0cc639ac8f6ff6bb587ca355e53044b6e81a7034293772eb9bc86`. |
| Reviewer / native Codex | `67c06c89-d4f9-4ced-9d30-5715c5e3e13e` | Own source/diff inspection and fresh 5/5 checks; approved same commit/tree. |
| QA / process | `aac9c3c1-d57f-495a-83e5-d893f0e185c0` | [5/5](qa/evidence.json), SHA-256 `92af28121979b5c6aefd716f9315a7b7cec19d14c63510297e4d8c788e0ea23e`. |

These runs end `cancelled / issue_reassigned` because Paperclip advances the
next participant after a recorded decision. Their accepted stage decisions—not
the process exit alone—prove handoff. Screenshots: [360px](qa/drawer-help-360.png),
[390px](qa/drawer-help-390.png), [412px](qa/drawer-help-412.png),
[guide final step](qa/tour-final-step.png). Real frontend templates/JS/CSS with
mocked HTTP/auth and external URLs blocked; not full backend/prod QA.

## Failures retained, not hidden

The original read-only Assistant failed before provider invocation because
Standard mode hit the Factory-only kickoff lookup without MCP capabilities.
Its scheduled retries were cancelled before reassignment.
The first dedicated Developer runs hit the same error until company config was
explicitly delivered. OpenCode then rejected its free Muse model request.
Authenticated Codex initially could not launch commands because inner `bwrap`
namespaces were unavailable; those runs made no repository changes. Supported
missing-disposition recovery and a normal task resume followed verified clean
Git/clear locks. No stage or owner approval was fabricated.

The trusted-local Docker profile, previously approved by the owner, explicitly
defers the inner Linux sandbox. Native adapter, run-scoped credentials, budgets,
empty external MCP catalogs and independent/human stages remain. Read-only review
is not a hardened filesystem isolation claim. Usage across failed/recovery runs
is not reported as complete task cost or a token saving.

## Persistence and source verification

Paperclip image unchanged:
`ghcr.io/dzikle/paperclip@sha256:fcca079223714bc67c3e87e14f64e57594d720b54ae69f84d18c774491b1995f`.
PostgreSQL **17.11**; migration identity **283 | 1790018362070**, unchanged.
No image rebuild or new service. Exact role IDs: [workflow](../../config/licitacija-workflow.json).

Company-scoped plugin config excludes only project
`a5758cd0-d9c4-4f3f-a004-2194691f6ef3`. Fresh worker re-enable and full quiescent
controller restart both logged `Git context scope loaded: 1 excluded projects`
without resaving config. The pinned host bootstraps with `{}` and supplies stored
company config via `configChanged`; ignoring company config in `initialize` is
therefore intentional. Task gates, owner participant, clear locks, exact empty
external MCP catalogs and all four run-context artifact digests were checked after restart.

All **14** AIF-78 environment leases are terminal with release timestamps:
4 expired, 7 failed, 3 released; zero active. These statuses include failed and
cancelled attempts, not fourteen successful runs. Cleanup-status fields are null;
no broader cleanup-receipt claim is inferred.

Deployed source matches repository SHA-256:

- worker: `4a6471554626a767a1a7836b6b7c1e07c9d7967d8f05aaa02bfd89fb8e3fcb5b`
- context: `0d9481e6480be32ed64d116c28149911ee40c07c552e5f143ca8368bfb78b83a`
- browser stage: `163399a2ea05ad958aae206bfb3071a06b2e96647b65fa29dd36ea1dbd917e09`

Fresh Factory validation: **284 Python tests, OK, two opt-in live tests skipped**;
**15/15 context tests**; stage/worker syntax and diff whitespace checks. An initial
plain Python environment check correctly failed missing/mismatched dependencies;
the pinned offline `uv` environment passed. Independent source review found no
remaining blockers. The unsafe generic reassignment utility was removed rather
than shipping a race or adding another Paperclip build.

Next: human decision for AIF-78. No website publication, merge or deploy follows
automatically from this repair.
