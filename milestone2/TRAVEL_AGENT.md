# Travel Agent in AI Factory

**Registered; native repository access proved by AIF-79 (Done).** No Travel
Agent application files were changed, and no app installs, tests or deployments ran.

## Use it from your phone

Open the [private dashboard](https://desktop-t58n2b9.tail14d8ec.ts.net/) with
Tailscale enabled. Choose **New Task → project Travel Agent → agent Travel
Agent Assistant → Ask**. Enter a repository question and create/send it.
Read the reply in that task. AIF-79 is the completed example.

Assistant, Developer and independent Reviewer use native **Codex / OpenAI,
gpt-5.6-sol**, low effort, through the existing signed-in runtime. Tests and
QA are scripts, not models. Timed heartbeats are disabled; assignment starts
work. Old admission agents were not resumed. The configured $10 monthly
native-agent budgets are Paperclip accounting limits, not measurements of
remaining ChatGPT subscription quota.

## Separation and limits

The full tracked Git repository is pinned to GitHub main commit
`fc5d95c2ce0e3606b26dc1d0f954143389cdcbdc` in persistent
`/paperclip/travel-agent-source`. It has its own project, task history, five
roles and coding worktree directory. No new image or service was created.
The transferred Git bundle was 509,473 bytes, not Windows dependency caches
or environment files. The original Windows checkout and its unrelated
untracked `apps/traveler/.gitignore` were preserved.

This remains the owner-approved **trusted-local profile**, not an OS-enforced
boundary between repositories. Assistant read-only behavior is role/task
intent. All five effective external MCP catalogs were checked and are empty.
No live travel-provider, database, GitHub publication or deployment access
was granted. The unrelated Factory kickoff-context lookup is excluded only
for this project; other projects retain their existing behavior. Travel
indexing, memory and retrieval are not claimed.

The checkout does **not automatically follow GitHub**. Refresh its source/base
deliberately for later tasks; never overwrite existing task branches.

## Coding tasks

Use the existing operator command from the Factory checkout with the Travel
Agent workflow preset. Do not assign coding work to the Assistant. Simply
choosing Developer in the dashboard does not attach independent gates.

```powershell
uv run --offline --no-project python -m milestone2.task --state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json submit --workflow milestone2/config/travel-agent-workflow.json --task <task.json> --dry-run
```

Task JSON contains `title`, `description` (scope, allowed changes, acceptance
checks and stop conditions) and a stable `requestKey`. Remove `--dry-run` to
create a backlog task; add `--start` only when authorized to dispatch. Keep
the same key after an uncertain submission and inspect state before retrying.
Never put private operator state in a task or agent environment.

The preset attaches native **Developer → Tests → Reviewer → QA → owner**
participants. Task branches live under
`/paperclip/m1-first-task-worktrees/travel-agent`. The stage script rejects
other project folders and symlink redirects before cloning. Tests use a
temporary committed copy for frozen install, `pnpm test`, `pnpm typecheck`
and static `pnpm migrations:check`. QA uses another copy for selected
travel-behavior Vitest regressions. Child commands receive no Paperclip,
provider or owner credentials; live/infra tests remain disabled. No
`db:migrate`, publication or deployment is authorized by this preset.

Coding bindings are **configured, not yet exercised end-to-end** on a Travel
Agent coding task. The first bounded request must prove dependency readiness
and the gates. Report failures rather than waiving them. QA is automated
behavior regression, not browser UX or real booking/payment proof. Owner
approval remains required before integration/publication.

## Repeatable registration

The owner-only provisioner uses supported Paperclip APIs; it does not copy
source, dispatch tasks or implement another workflow engine. Pinned source
and the existing runtime helpers plus `travel-agent-stage.mjs` and
`travel-agent-workspace.mjs` must already be installed. Inspect first:

```powershell
uv run --offline --no-project python -m milestone2.scripts.project_setup --state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json --preset milestone2/config/travel-agent-project.json
```

Add `--apply` only with current authorization. It rejects same-name foreign
resources, drifted public runtime fields, unexpected environment keys and
changed native managed instructions. Process roles execute scripts and have
no managed LLM bundle. API-redacted environment values cannot be exhaustively
compared; replay is not proof of unchanged hidden values. Apply also checks
the effective external catalogs. Unexpected/partial state requires operator
inspection, not automatic retry or wake. Live replay reused the same IDs.
This preset is instance-specific, not a discovery service.

[Selected evidence](results/travel-agent-onboarding-20261005.json).

## Documentation-first work — AIF-80

On 2026-10-06 the owner requested the intended operating flow: find existing
requirements, identify unfinished behavior, then dispatch implementation to
AI Factory. The source documents are `docs/architecture/ai-agent.md`, tool
contracts, grounding tests and conversation evaluations in the pinned Travel
Agent repo. Historical audits must be checked against current code, not blindly
reimplemented.

The first bounded slice is **AIF-80: Enforce the documented bound on Travel
Agent tool feedback**. It was dispatched through the existing task command
and verified running on its own native Developer branch, with independent
Tests/Reviewer/QA and final owner approval. The operator did not implement the
app fix. [Task brief](tasks/travel-agent-bounded-tool-feedback.json) and
[dispatch receipt](results/travel-agent-dispatch-20261006.json) preserve the
requirements, scope and submission identity. Read AIF-80 in Paperclip for live
progress; dispatch does not mean the fix or its gates have passed.
