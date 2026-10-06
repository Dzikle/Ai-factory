# Licitacija Mobile App in AI Factory

This project is for the native Expo / React Native app under `mobile/` in
`Dzikle/licitacija.mk`, not the older website/import-help project.

## Use from the dashboard

Choose **New Task → Licitacija Mobile App → Licitacija Mobile Assistant → Ask**
for repository questions. The Assistant does not edit code. Native Assistant,
Developer and independent Reviewer use Codex / OpenAI `gpt-5.6-sol`, low effort,
with the existing signed-in runtime. Tests and QA execute scripts, not models.
Timed heartbeats are disabled. New tasks start work only when assigned;
registration itself does not dispatch a task or resume old admission agents.

Coding uses the existing operator task command and
`milestone2/config/licitacija-mobile-workflow.json` to attach independent
**Developer → Tests → Reviewer → QA → owner** stages. Merely choosing Developer
in the dashboard does not attach those gates. Keep a stable task `requestKey`.

```powershell
uv run --offline --no-project python -m milestone2.task --state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json submit --workflow milestone2/config/licitacija-mobile-workflow.json --task <task.json> --dry-run
```

Remove `--dry-run` to create a backlog task; use `--start` only when dispatch is
authorized. Owner approval is required before integration/publication. These
roles have no permission to push, merge, deploy, run EAS/native builds, contact
live services or change the Java/backend. Ask for missing backend context.

## Source and separation

The source is a committed **subset**, exported from local Git commit
`c1fa8bd42249635960def34f2034f6d03cf4e0ab`: tracked `mobile/`, root/mobile
contracts and focused documentation. `mobile/google-services.json` is omitted;
no local uncommitted changes or private `.env` files are copied. The empty
public `.env.example` template is included. Remote GitHub main freshness is
not claimed. Source snapshot `7c3dbd0ed96722d98cb2847885fe226cf5ae86e9` lives at
`/paperclip/licitacija-mobile-source`; it does not auto-follow GitHub.
The Windows export converted 232 text files from LF to CRLF. All 236 selected
files were checked against canonical Git blobs: exact bytes or that line-ending
conversion only; no other content changes. This synthetic snapshot is not a
branch of upstream main and must not be pushed as a replacement repository.

The project has separate task history, role identities and task branches under
`/paperclip/m1-first-task-worktrees/licitacija-mobile`. This remains trusted local
execution, **not OS-enforced isolation**. The stage checks its project/participant,
lexical and real task paths before cloning, ancestry, a clean commit/tree, and
mobile-only changes. Missing files/context are reported, not supplied by reading
another project's checkout. The unrelated Factory kickoff-context fixture stays
excluded for this project. No mobile indexing/memory is claimed.

## Validation limits

Tests run frozen `npm ci --ignore-scripts --no-audit --no-fund`, then mobile
typecheck, Vitest and lint. Independent QA repeats focused API-client, safe-link,
image-upload, location, notification-routing and market-summary regressions from
another committed copy. Child commands receive an allowlisted environment with
no Paperclip/provider/owner credentials. Temporary copies and npm caches are
removed; no extra image or service is created.

These checks are **not physical-device UX, Android/iOS build, signing, app-store,
release-target or live API proof**. Release-target validation needs an explicitly
approved target/environment and is not silently run against production. Report
baseline and future validation failures; attaching roles does not waive them.
No mobile coding task has yet exercised the complete native workflow.
The onboarding readiness smoke did run these commands on a temporary committed
copy: 82 tests in 27 files, typecheck and lint passed; the focused QA command
passed 19 tests in six files. Dependency deprecation warnings were reported;
this smoke is not a dependency vulnerability audit or a native task verdict.

## Repeatable setup

From the Factory root, inspect the prepared runtime source and saved bindings:

```powershell
uv run --offline --no-project python -m milestone2.scripts.project_setup --state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json --preset milestone2/config/licitacija-mobile-project.json
```

`--apply` requires owner authorization. The preset explicitly upgrades only the
recorded planning project/workspace, keeping their IDs. Exact original/target
fields support recovery between the two native PATCHes; foreign/drifted state
stops. Existing agents are checked, not automatically overwritten or resumed.
Runtime stage/policy/config files must be installed first. The supported effective
MCP catalog is checked for each role; no external tools are requested. Replay is
not exhaustive proof of unchanged API-redacted secret values.

[Setup and validation receipt](results/licitacija-mobile-onboarding-20261006.json).
