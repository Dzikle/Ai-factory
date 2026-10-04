# Milestone 2 — usable local engineering loop

**Status: trusted-local Milestone 2 demonstration COMPLETE (2026-09-28).**
Reusable task commands and owner-approved AIF-48 satisfy the revised local-demo
exit. This is not full V1 or production readiness. The official OpenSearch MCP
server remains the provider; Paperclip remains the runtime catalog, profile,
and run authority. Broader integration and hardening work remains deferred.

## Current direction: useful local functions

The owner approved functionality-first development on 2026-09-28. Extra runner
isolation and production hardening are deferred, not passed. The older isolation
gate recommendation below is superseded for this trusted local prototype.
Keep credential containment, existing scoped MCP, separate tests/review and owner
integration approval. No new image, scheduler or task database is needed.

## Phone/dashboard questions — working 2026-10-04

**Travel Agent added 2026-10-05:** its separate project and five roles are
registered, and native read-only **AIF-79 passed**. See [Travel Agent usage and
limits](TRAVEL_AGENT.md) for phone questions and the prepared coding preset.
No Travel Agent application changes or app test execution occurred.

Open the [private dashboard](https://desktop-t58n2b9.tail14d8ec.ts.net/) with
Tailscale enabled. **AIF-77 / Test2 is answered and Done.**

For another repository question:

1. Choose **New Task** and enter the question.
2. Choose project **Licitacija mobile import help**.
3. Choose agent **Licitacija Assistant**, not **Milestone 0** (the human account).
4. Choose **Ask** mode, then create/send the task. Read its reply in the task.

The successful AIF-77 configuration is retained, but the assistant is currently
paused following the AIF-78 correction below. Its earlier free-provider success
does not prove current availability. Timed heartbeats are disabled. Historical
fixture agents remain paused; do not resume the whole organization.
The model is already configured; there is no need to choose one for each question.

This assistant reads the existing partial Git snapshot at `0b8cb9647bf08cb8c269c1c89ad746d0db76d95c`,
not the current live website, its database or the latest remote branch. It has
no coding, publication or deployment role. Engineering changes still use the
owner-authorized Developer → validation → independent Reviewer/QA path below.

The existing engineering-context fixture now omits its kickoff lookup for
Paperclip's authoritative **Ask** mode, recording a no-context artifact instead.
Ordinary engineering enrichment remains fail-closed. No irrelevant OpenSearch
grant was added to the assistant. A small run-scoped completion helper posts
only its own bounded Ask answer and marks that question Done, preventing an
unnecessary missing-disposition follow-up. This is not an OS sandbox claim.

[Configuration and selected live evidence](results/licitacija-assistant-20261004.json).
Owner-only, exact AIF-77 provisioning is reproducible with
`python -m milestone2.scripts.assistant_setup --state <private-state-file>`;
add `--apply` only with current authorization. This is not a generic task
submitter or an automatic retry command. The fixture/role/config live under
`milestone2/{scripts,fixtures,config}`. An existing agent is never automatically
reused for a new assignment; already-assigned replay reports **no changes**, not
runtime configuration verification. Coding-policy/non-Ask replay is rejected.
The completion helper rejects terminal/stale runs and bypasses HTTP proxies and
redirects; an uncertain result requires inspection, not an automatic repost.
Deployment uses the existing persistent
`/paperclip` storage: `assistant_reply.py` at `/paperclip/assistant-reply.py`,
and the existing context-plugin files at `/paperclip/m1-context-enricher-plugin/dist/`.
Managed role instructions and native configuration are updated through
Paperclip's supported agent APIs. No new controller image or website change.

## AIF-78 coding routing — corrected 2026-10-04

**AIF-78 is waiting for owner approval, 3/4 gates passed.** It had been assigned
to the read-only Assistant in Standard mode with no engineering policy. A
company-wide Factory kickoff fixture then required an irrelevant MCP lookup.
The operator paused the wrong assignee, checked idle locks/worktree, reassigned
the same issue and attached the existing native independent policy. No duplicate
issue, wrapper adapter, scheduler or custom workflow state was introduced.

Four clearly named, task-selected roles now exist: **Licitacija Developer,
Validator, Reviewer and QA**. Developer/Reviewer use native **Codex / OpenAI,
gpt-5.6-sol, low effort**, authenticated through the existing ChatGPT login.
Validator/QA are deterministic browser scripts, not models. OpenCode's free
Muse provider rejected the attempted coding runs; those failures are retained,
not counted as successful execution or cost savings.

The extra inner Codex Linux namespace sandbox could not launch (`bwrap` denied).
The existing owner-approved trusted-local Docker profile is used explicitly:
`--sandbox danger-full-access`, bypass flag false. Reviewer is a separate trusted
read-only role, not a claimed OS/filesystem boundary. Exact external MCP catalogs
for these four roles are empty; no broad grants or privileged credentials were added.

The fixture has a bounded, operator-configured `excludedProjectIds` list, scoped
by company through Paperclip's `configChanged`/startup replay. This Licitacija
project and the separately registered Travel Agent project are excluded.
Missing/other project IDs still use the original fail-closed
Factory behavior; Ask/process omissions are unchanged. A no-context artifact
records the deliberate omission. Re-enable and full idle-controller restart
replayed the saved scope without a resave; approvals and artifact hashes survived.

The native Developer reused the earlier AIF-58 candidate on AIF-78's own branch;
fresh independent tests, Reviewer and QA verified the same commit/tree. All five
real-browser cases passed (360/390/412px, existing guide, inherited-key rejection,
context path, ordinary profile help). No new website fix was authored here and
**no website push, shared-branch merge or deployment occurred**.

[Evidence and screenshots](results/licitacija-routing-20261004/README.md).
These role fixtures are this known-file frontend task's bindings, not universal
agents or a full backend build. For a new coding task use the existing
`task submit` command with a verified task-class workflow and current role/test
contract. Do not assign coding work to Assistant or reuse this narrow four-file
profile for arbitrary tasks. UI assignment alone does not add review gates.
The proposed generic existing-issue `route` command was not shipped: the deployed
PATCH API has no conditional-write guard against concurrent board edits.

## Submit a task and see progress

For repository preflight and owner-approved feature-branch publication, use
[`python -m milestone2.publish`](PUBLISH.md). It preserves unrelated local
work, checks the exact Paperclip approval, and saves a verifiable publication
receipt. It does not merge, deploy, approve tasks or start services.

**Script-first follow-up — 2026-10-03:** 22 new real-Git/HTTP-boundary tests
passed; full Python suite **205 tests, OK, 2 optional live tests skipped**.
Independent review findings were reproduced and fixed, then re-reviewed.
[Verification record](results/script-publication-20261003.json) distinguishes
local integration tests from unperformed live GitHub/Paperclip publication.

**Agent-discovery continuation — 2026-10-03:** commands are linked from the
canonical agent/role instructions and refreshed runtime source/projection.
Native read-only **AIF-60** found and executed publication preflight help;
Developer/Reviewer publication rights remain unchanged. The saved-evidence
checker adds seven regressions; full suite **212 tests, OK, 2 optional skips**.
[Discovery evidence](results/script-discovery-20261003.json) records the failed
first probe separately, the successful run, exact revision/profile and cleanup.

From the repository root, use Python 3.11+ (or prefix commands with
`uv run --offline --no-project`). Authentication stays in the existing ignored
board state file, never in a task, workflow preset or command-line token.

```powershell
$env:AIF_PAPERCLIP_STATE = '.milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json'
python -m milestone2.task status AIF-47
python -m milestone2.task submit --workflow milestone2/config/ai-factory-projection-workflow.json --task milestone2/tasks/projection-help.json --dry-run
python -m milestone2.task submit --workflow milestone2/config/ai-factory-projection-workflow.json --task milestone2/tasks/projection-help.json
```

Submission defaults to **backlog**, without requesting agent dispatch. Add
`--start` at creation to submit as `todo`; task-selected agents must already be
active in Paperclip. The command never silently resumes paused agents, changes
model bindings or approves integration. A task already saved in backlog is
started through Paperclip; resubmitting its key is a replay, not a start action.
Keep the same `requestKey` when retrying an uncertain submission: Paperclip owns
deduplication. Use a new key for a different task. No automatic POST retry.

The workflow preset reuses the AIF-47 projection-task roles in this local
instance. Their Validator/QA are task-class-specific; use appropriate existing
agent bindings for another repository or task class. Omit `qaAgentId` for a
task that does not require QA. Developer, tests, Reviewer and optional QA must
remain distinct. Both commands accept global `--json` before the subcommand.
`status` reports Paperclip's saved stage; it does not poll, advance stages or
read private run logs.

### Task-command verification — 2026-09-28

- Full Python suite after review: **71 tests, OK, 2 opt-in live tests skipped**. The 12 new
  subprocess/HTTP-boundary tests cover submission, independent native stages,
  optional QA, company checks, paused/error-agent handling, redaction and no POST retry.
- CLI help and the actual local preset/task `--dry-run` passed without a server.
  Paperclip's pinned source confirms identifier resolution and native issue-create
  idempotency; runtime deduplication is not claimed from the boundary tests.
- The initial live status attempt could not connect. Docker
  Desktop 4.55.0 failed startup at its stale `run/dockerInference` socket.
  A recoverable rename failed; this session's policy blocked targeted cleanup.
  No image rebuild, reset, volume deletion or task dispatch was performed.
- The optional OpenCode free-model reviewer rejected CLI access to its free
  tier; no independent model-review result is claimed for this command.

**Live continuation:** Docker recovered after preserving and atomically renaming
only its stale runtime socket folders; no reset or data deletion. The five
existing AI Factory services restarted without a build. The CLI read AIF-47 as
`done`, 4/4 gates. It created **AIF-48**
(`5284995a-ee36-4b8d-9841-e9f00b7fc21e`) as backlog; replay returned the same ID.
The actual issue has distinct tests, Reviewer, QA and owner-approval participants.
All 95 agents were still paused and no runs were active before dispatch.

Preparation commit `408fabdb654dcb2a3bba91ad96ce422f67c53182` corrects the
example task's nonexistent `--apply` flag, rejects `error` agents before
`--start` POST, and supplies reusable current-issue Developer/Reviewer instructions.
The review fix had an observed RED and 12-test GREEN; independent re-review
found no remaining CLI or role-instruction findings. Dry-run intentionally displays the locally
supplied task payload; normal/status output does not disclose API descriptions.

The existing source snapshot fast-forwarded from `4f50570` to `408fabd` using
a 79,802-byte Git bundle. An old empty Git index lock (2026-09-27) was preserved
only after confirming no Git process, active run or unpaused agent owned it.
The existing one-shot projector refreshed 49 canonical documents at `02d80f1`;
reader-only replay planned zero writes. No new projection worker was introduced.

The same native Developer/Reviewer bindings use `/paperclip/m2-projection-roles`
with `developer.md` / `reviewer.md` (external instruction bundles); stale AIF-47
`--dir` overrides were removed. Initially deployed bytes matched the Git fixtures:
Developer SHA-256 `df5c73c78fbabbe1e3babe8e1e6ffcf4f847239cea34e591bde4d102ce6cb80e`;
Reviewer `182933316887a760396975ebc7bf6940d2f8bc99b0aa207023c9c48c4ede8d1c`.
Only the four selected agents were resumed, with timer execution still disabled.
Paperclip's native backlog-to-todo transition dispatched AIF-48. No custom stage
advancer, model gateway or scheduler was added; final approval remains the owner.
Milestone 2 stays in progress until the native task evidence is collected.

The first three AIF-48 runs failed **before provider work**: the project had no
explicit source ref, so its new worktree used stale `origin/milestone1-contracts`
at `8955be9`, although the local source branch was current. The enrichment plugin
correctly rejected the newer indexed revision as not an ancestor. Automatic
retries were paused; the clean, untouched task branch fast-forwarded to `408fabd`.
The existing project's `repoRef` and `defaultRef` now explicitly select
`milestone1-contracts`. The same task/workspace was resumed, without disabling
provenance validation or changing provider/permission bindings.

Run `f77ef2d6-f398-41d2-890b-0da66969153c` then persisted a verified context
artifact, but stopped after OpenCode denied a redundant reread of its external
role file. Native continuation `e8a150fb-2a3b-4670-9fc3-be2111cb7dae` produced
candidate `7fd60f8`. The role fixtures now explicitly say they are already
injected and resolve repository paths from the assigned worktree. Updated,
independently verified deployment hashes: Developer
`bf1d782a6504cf2ae3bd3eb5d11ac7b013c8f8b0154ba2f4950840b2a726ea90`;
Reviewer `af03cade5d6c426fd7b5ab5c330174694876560e77b098a08254c3c9975962b7`.
No external-directory permission was added.

The existing Python test-library directory initially lacked `jsonschema`.
Installing Linux/Python 3.13 wheels for the existing test requirements
`jsonschema[format]==4.25.1` and `PyYAML==6.0.2` into that directory, without
an image build or repository dependency change, made the full candidate suite
pass: **72 tests, OK, 2 opt-in live tests skipped**. Independent Validator and
Reviewer passed `7fd60f8`; a subsequent integration check found that its displayed
examples split shell commands across lines without continuation. A supported
board reassignment returned AIF-48 to its Developer and reset the review round,
preserving all four participants and final human approval. No old approval
may qualify the corrected candidate.

### AIF-48 final candidate — owner-approved and integrated

Candidate **`36bc6cc293f8e99b21c742858d05df7933ff4896`**, tree
`a8cba28abfb9a1076060a28eb77e8a15bc2916df`, adds complete single-line help
examples and a credential-free CLI regression. Only the original two allowed
files differ from base `408fabd`. The native task worktree is clean. Its two
commits were fetched by Git bundle into the same named branch in this owned
repository. The owner explicitly approved AIF-48 in this chat on 2026-09-28.
Merge **`b78b4c53e7808aab414dee2817a5c8a850dce69a`** integrates that exact
candidate into `milestone1-contracts`; the task branch is retained for provenance.

| Gate | Exact corrected-candidate evidence | Result |
| --- | --- | --- |
| Developer | `959995da-ee06-4403-907f-0149bc3ccb29`; observed stronger-test RED, then GREEN | Committed handoff |
| Deterministic tests | `aa15ac84-0900-438a-a29a-93a4bd7b3a6c`; immutable commit copy, 15 targeted tests | PASS |
| Independent Reviewer | `22d6e76d-d296-4bf4-88f0-8b69491c9b6a`; verified candidate/tree, help output and full 72-test suite | PASS |
| Independent QA | `a9d13d12-da0e-49f7-ac78-586ef9749602`; six black-box preview/apply/replay/failure checks, no live credentials or index writes | PASS |
| Human integration | Owner approval `9b75e70e-1af8-477e-b488-52bbbe7603fa` at `2026-09-28T20:08:07.236Z`; merge `b78b4c5` | PASS |

Paperclip records AIF-48 as **`done`, 4/4 gates**, with checkout/execution locks
clear. Before approval, the stored Validator and QA artifact bytes were hashed
again and both matched the exact approved commit/tree and recorded digests.
The two integrated implementation/test files are byte-identical to the candidate.
Fresh verification before integration and on the merged result:

- Full Python suite: **72 tests run, 70 passed, 2 opt-in live tests skipped**.
- Independent functional CLI QA: **6/6 passed** on the merged result.
- Context, Git handoff and Validator identity Node suites: **26/26 passed**.
- `git diff --check` passed. No new image, service, schema or model invocation.

Python checks use the existing offline `uv` environment with
`jsonschema[format]==4.25.1` and `PyYAML==6.0.2`. An initial QA invocation omitted
these dependencies and failed at import; the corrected invocation passed without
changing application or test code. No skipped live test is counted as executed.

An independent full-suite rerun on the final candidate passed **72 tests,
2 opt-in live tests skipped**. Validator receipt SHA-256:
`aa32260f4694b84888b217f33d189b4fea99def9277d6f4f40eea5a7f0578439`;
QA receipt: `25d7ba4566e45c9f6516e193729af14abba37a28bd6fdd048aaf0a8a3468f328`.
Their actual artifact bytes were independently hashed and identify the final
candidate/tree. Developer context artifact SHA-256:
`9cb0de582b953ef65d6c5818713e3fa5b578f6456af974e528157888ddbdd592`;
Reviewer context: `13140999b7ce42fe85a186b03ab57f8a01bd6d0914badfc7be8ef4a6933cf629`.
These remain in each original native run's durable enrichment snapshot.

**Observed runtime limitation:** Paperclip marks these run-scoped handoffs
`cancelled / issue_reassigned` while separately persisting their successful
decisions and receipts. Re-entering validation encountered a hold for earlier
run `8ea979ae-1539-49e5-8893-421fab3b96fb`. Its stopped-provider acknowledgment,
successful immutable receipt and prior native decision were verified. Recovery
action `72604bfd-c5cb-4248-b767-47ed920a9a6f` was reconciled through the supported
API with `actionOutcome: completed`, after aborting the incomplete review round.
The attempted direct restoration returned 409 (pending review); the first
fresh-round assignment attempt returned 422. Dispatch configuration was restored
in `finally`; Paperclip's durable continuation then executed fresh tests and
review, followed by an explicit native QA wake. No SQL edits, run-status rewrite,
approval impersonation, new scheduler or control-plane patch was used.

After recovery, Paperclip's review return-assignee is the Validator rather than
the original Developer. Rejection therefore requires an explicit board hand-back
to the Developer; do not claim unattended correction-loop support. The current
candidate still has separate Developer, Validator, Reviewer and QA evidence, all
three independent gates completed, no execution/checkout lock or recovery hold,
and the original human owner as the final approver. Native cost/usage fields on
cancelled handoff runs are unavailable; do not infer savings or completed-run
telemetry from model names. Owner approval and integration now complete the
revised **trusted-local** Milestone 2 demonstration, not an unattended correction
loop or the deferred production gates. Milestone 3's next bounded demonstration
is one provenance-backed lesson retrieved by a later task without overriding Git.
Final live check: four selected agents idle, 91 admission agents paused, no
queued/running/retry runs, and the four core services healthy (existing SSH
runner also running). The repository checkpoint suite passed 71 tests with
two live skips; the unmerged candidate has the additional help regression.

## Local deployment

- Source: `opensearch-project/opensearch-mcp-server-py` commit
  `fcb23ec17186ba905590fb06b2eeecb063bc54a7`, frozen `uv.lock`.
- Build: `docker compose -f milestone2/compose/opensearch-mcp.yaml build`.
- Start: supply `AIF_M2_OPENSEARCH_READER_PASSWORD` from a secret store, then
  `docker compose -f milestone2/compose/opensearch-mcp.yaml up -d --no-build`.
  The password belongs to the `aif_agent` reader user and **must differ** from
  the OpenSearch admin password. Never commit it or print it in logs.
- Local image ID: `sha256:c47f67f75b31370868424a9176784f8cf212d293507e70467911a2c9736cc4a8`.
  Publish an immutable owner-controlled image before remote deployment.
- The local admission cluster has a self-signed certificate, so this Compose
  profile disables TLS verification. A real deployment must supply a trusted
  CA and turn verification on.

Apply `config/opensearch-mcp-reader-role.json` as the OpenSearch Security role
`aif_agent_reader`, bound to the `aif_agent` user. It can search both the
historical admission alias and active Git-docs alias, but has no write action.
On 2026-09-26 the local reader password was rotated away from the previously
shared admin password. Live checks: current reader search 200, write 403;
the former shared password as `aif_agent` returns 401. The rotated value is
stored only in the running local container configuration, not this repository.

The active Paperclip connection is
`34e29b2e-e5f2-455e-ab47-b1187eb38537` at
`http://opensearch-mcp:9900/mcp`. Its cached catalog is exactly four tools.
Developer `7a134376-dd89-4006-97bb-eeba855e443d`, Reviewer
`74519fa4-15c6-437c-9694-5d2579b76356`, and the admission seam probe
have only `SearchIndexTool` in their effective profiles and only this
connection installed. When creating or changing installs, Paperclip may
auto-bind an additive `app:<connection-id>` profile; unbind its company and
agent grants **after the final install update**, then assert the effective
catalog. Do not regard the profile configuration alone as proof.

The former connection `61bc2d0d-11ba-41e3-a989-6d47f79576df` is disabled.
Its 19 remaining installations belong to paused admission/policy fixtures.
The former Windows host MCP process on port 19901 was stopped. A generic
Paperclip MCP connection's catalog refresh retained removed tools; changing
the upstream tool surface required a fresh connection instead of refreshing
the stale one. Revisit catalog retirement in the owner-maintained Paperclip
fork before attempting an in-place tool-surface contraction.

## Verification

Run `python milestone2/scripts/verify_opensearch_mcp.py --fault-inject
--paperclip-state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json
--connection-id 34e29b2e-e5f2-455e-ab47-b1187eb38537
--agent-id 7a134376-dd89-4006-97bb-eeba855e443d
--agent-id 74519fa4-15c6-437c-9694-5d2579b76356` from the repository
root (put the command on one line). The state file is ignored and contains a
board key; never commit or display it. The test checks distinct reader/admin
secrets, direct four-tool catalog, two real searches, Paperclip's exact
catalog/profile/install state, and restart after killing the MCP child.

Run-scoped Paperclip probe `0d5050af-e948-4c75-a31b-054c9e7b856f` finished
`succeeded`: one governed server, allowed search HTTP 200, denied msearch
HTTP 403 with `deny_default`. After reader-secret rotation and another MCP
crash/restart, run `c60ea56e-4f8e-488c-b548-abb940753efc` repeated that
same result. The probe agent was paused afterward. Its Git
workspace was seeded from the already accepted AI Factory commit because the
globally enabled Milestone 1 pre-run plugin requires a Git source. This is a
test fixture, not a new Context Resolver or workflow implementation.

## Native Codex MCP catalog: deployed; final search blocked on quota

Paperclip fork branch `ai-factory/milestone2-codex-mcp-headers`, commit
`c2f23c8102461a93cb07d294748c32f185d8ecdd`, changes its managed Codex
MCP writer from `headers` to Codex's supported `http_headers` field. A focused
regression failed before and passed after the change; the adapter typecheck
passed. Codex CLI 0.154.0 independently parsed `http_headers.Authorization`
but ignored `headers.Authorization`. The Windows run had unrelated symlink/
permission failures. On 2026-09-27 the complete `codex-home.test.ts` file ran
inside the exact Linux production image below: **53/53 passed**.

`scripts/verify_native_codex_mcp.mjs` asserts the exact Codex-visible server
names and recognized bearer headers without printing tokens. Feed it to the
controller with `docker exec -i <controller> node - <company-codex-home>
paperclip-projects paperclip-connections paperclip-assigned`. The initial
saved home contained five historical `native-*` entries. A new native run
regenerated its managed block automatically; no manual TOML deletion or
named-gateway disabling was needed. The assertion now **passes**, including
after controller restart: exactly three servers with recognized bearer headers
under controller Codex 0.157.1. This proves CLI parsing, not a successful
model-initiated MCP call. The SSH runner remains on its existing pinned image
with Codex 0.156.1.

The attempted normal local source build did **not** produce an image. Docker
build record `var0uzzifz2e2eqio8n9vaydf` failed at the runner's generated
protocol-manifest check. The Windows checkout has CRLF working-tree bytes for
generated files whose Git blobs are LF. An exact Git-archive retry avoided
checkout conversion but missed Docker's package-install cache; it was stopped
at about 7 GB remaining host space to protect other running work. No live
controller, database, or storage was changed.

The owner fork's normal Linux Docker workflow now builds the same fix from
commit `d57c0b7c5cbd2e29c25363df7dc30531e44f5ad1`. The additional commit
normalizes mixed-case GitHub owner names for GHCR and skips the unrelated cloud
image on manual branch builds. [Run 36332581214](https://github.com/Dzikle/paperclip/actions/runs/36332581214)
passed both production architecture builds, manifest merge, and the published
image's PID-1 orphan-reaping check. Immutable multi-arch image:
`ghcr.io/dzikle/paperclip@sha256:95f6708217d9b34b10c9a3637d024e121a2bdaf6fa0008eb3fca5983b80f1676`.
The image is **deployed locally**, but the native end-to-end gate is incomplete.
The Milestone 0 admitted/rollback pin is retained separately from this active
Milestone 2 candidate in `milestone0/dependencies.lock.yaml`.

### Controlled cutover and evidence, 2026-09-27

Docker recovered after the owner restarted Desktop; no purge was performed.
Before cutover, the stopped controller's PostgreSQL database and storage volume
were backed up together under ignored `.milestone0/m2-precutover-20260927/`:

| Backup | Bytes | SHA-256 |
| --- | ---: | --- |
| `paperclip_fork_m0.dump` | 3613915 | `ccfcced7b3b2ec1e65e3bdcde3872927932751408ec79c8a585337a094c37aba` |
| `paperclip-storage.tar` | 421519360 | `3764b58e848c6f57608033b31f2efdc01350eebc3949163730bf32c13b66d5b2` |

Matching PostgreSQL 17 `pg_restore -l` read 2142 entries; the storage tar listed
11526 entries. These are archive checks, **not a new restore rehearsal**. The
earlier Windows directory copy failed on symlinks; the Linux tar is the storage
backup. Backups contain credentials and must never be committed.

Use `compose/paperclip-native-mcp.yaml` after
`milestone0/compose/paperclip-fork-readmission.yaml`. Supply the existing
`AIF_M0_POSTGRES_PASSWORD`, `AIF_M0_BETTER_AUTH_SECRET`,
`AIF_M0_AGENT_JWT_SECRET`, and `AIF_M0_SECRETS_MASTER_KEY` in the invoking shell
from the local secret store (or an explicitly supplied ignored `--env-file`).
Do not generate replacements or commit/display the values. The override preserves the native runner network,
previously attached manually. Cutover used `up -d --no-build --pull never
--no-deps paperclip-fork` after verifying rendered environment values matched
the saved controller. The PostgreSQL and storage volumes were not replaced.
Immediate before/after counts matched: 202 runs, 43 issues, 91 agents.
PostgreSQL remains 17.11; the Drizzle journal remains 283 rows, latest
`1790018362070`. The fork diff introduces no schema/migration changes.

- Health reports exact commit `d57c0b7c5cbd2e29c25363df7dc30531e44f5ad1`.
- Linux adapter regressions: 53/53. Exact direct MCP catalog, Developer/Reviewer
  search-only effective profiles, live searches and MCP child-kill/restart: PASS.
- Repository validation: 52 Python tests run, 2 opt-in live tests skipped, no
  failures, using the documented pinned `uv` dependencies; 18 Node fixture tests
  passed. The separate live MCP checks above did run. Bare system Python lacked
  `jsonschema`; it was not used for the successful suite.
- Read-only probe **AIF-44** (`a73c46a0-8900-401c-bc3b-6a9af3db7f4d`) first
  failed before provider invocation: the project template's old
  `origin/milestone1-contracts` ref produced a workspace behind the indexed Git
  source. The clean probe worktree alone was fast-forwarded to existing source
  commit `4f50570ae6a8efb67ff7840d629ad2fb3dd6a0c3`. No prior task or projection
  was changed. Repeatable source-ref/Git handoff remains separate work.
- Run `6f410fba-5852-4835-9722-a4df0e02ff30` then completed governed enrichment,
  wrote the exact three-server configuration, synced it to the existing SSH
  runner, and launched the original native `codex_local` adapter. Codex returned
  **`provider_quota` before a model tool call**. This is not a successful native
  search, completed task, or full native authorization admission.
- The run snapshot retains
  `file:///paperclip/milestone1-context/6f410fba-5852-4835-9722-a4df0e02ff30.json`,
  3545 bytes, SHA-256
  `1c07706becbd54e5aee27e533d55cf247c58a18823a5f77310aca7db88e530e1`.
  Actual bytes independently matched the digest before and after restart.
  Lease `341f3bc5-c5d8-48ab-a3a5-3a861e916472` is terminal (`failed`) with stable
  release receipt `2026-09-27T18:57:35.096Z`; task execution/checkout locks cleared.
- Developer is paused, queued retries cancelled, AIF-44 explicitly blocked on
  provider quota. No active/queued/scheduled-retry runs remained at the final
  check. Historical named gateways remain unchanged pending the native search.

**Next:** when Codex quota is available, resume this same read-only AIF-44 probe
with a fresh session, reassert the exact catalog/profile, and require a real
governed search in its native event log before closing this gate. Do not change
providers, buy credits, or call the raw OpenSearch API to simulate this result.
Then finish reliable Git handoff and the second independently accepted task
with conditional QA. Milestone 2 remains **IN PROGRESS**; the trusted-only
runner's isolated `seccomp=unconfined` exception also remains.

## Git handoff implementation, 2026-09-27

The Codex quota blocks AIF-44 only; independent Milestone 2 implementation
continues. The source checkout's `origin` was still the initial offline
`/paperclip/m1-first-task.bundle`. It is now
`https://github.com/Dzikle/Ai-factory.git`, matching the owned repository.
The existing Paperclip `git_worktree` policy and `milestone1-contracts` base
branch are unchanged. Fetching updated the remote-tracking ref without moving
the shared checkout or any existing task branch. After restoring an old backup,
verify this origin before admitting another new task; do not use an old bundle
as a moving branch's authority.

Paperclip created AIF-45's isolated worktree at then-current published commit
`15660c717f00f12f097cd13644c9c1b753b4a1ae`, independently confirmed with Git.
The diagnostic process itself failed because its explicit cwd was `/paperclip`,
not that worktree; no successful agent run is claimed. The read-only diagnostic
was cancelled and its agent paused. This is workspace-source evidence, not a
second accepted engineering task. Nine selected upstream workspace-runtime
regressions passed in the pinned image as non-root: fresh remote bases, clean
idle-worktree refresh, and preservation of existing task work (152 other cases
not selected).

The existing Git-doc Validator now requires Paperclip's recorded branch,
a clean committed worktree, and an unchanged commit before/after validation.
It tests a temporary **non-hardlinked copy of the captured commit**, then checks
both the copy and original before submitting a decision. This also avoids
testing transient edits made and restored in the original checkout. The copy
is removed afterward; it is a test input, not a second operational workspace
manager or a security sandbox. Trusted-repository execution restrictions remain.

Validation evidence and the stage comment carry `gitHead`, `gitTree`, and
`branchName`; evidence also names `validationSource: isolated_commit_copy`.
Reviewer instructions require comparing the current clean branch with those
identities before a verdict. This is not deterministic enforcement of a future
human merge: final approval and integration remain human-owned. Nothing commits,
pushes, or merges the task automatically.

Verification: 28 Node unit/fixture tests and nine disposable Linux validator
integration cases pass. The integration tests execute the real Validator,
Git and Python against a test HTTP API; they are not live Paperclip approvals.
They cover clean approval, dirty input, dirty/committed changes to both the
copy and original during tests, wrong branch, failed tests, and a synchronized outside edit/restore. The last
case failed before isolated-copy validation was added. The Python suite still
passes 52 tests with two opt-in live skips.

Run the unit checks with `node --test milestone1/fixtures/git-handoff.test.mjs
milestone1/fixtures/git-doc-validator-identity.test.mjs`. Run the opt-in
integration file **only in a disposable container with no live storage mounted**:

```powershell
$repo = (Get-Location).Path
docker run --rm --network none --mount "type=bind,source=$repo/milestone1/fixtures,target=/fixtures,readonly" --env AIF_VALIDATOR_INTEGRATION=1 --entrypoint node ghcr.io/dzikle/paperclip@sha256:95f6708217d9b34b10c9a3637d024e121a2bdaf6fa0008eb3fca5983b80f1676 --test /fixtures/git-doc-validator.integration.test.mjs
```

The Validator/identity/helper/Reviewer runtime copies under `/paperclip` were
updated while no runs were active and verified byte-for-byte against source.
Their previous copies are backed up in ignored
`.milestone0/m2-validator-prehandoff-20260927/`. Native end-to-end handoff and
the second independently accepted task with conditional QA are still open;
these deterministic changes do not close them.

Live deployment smoke **AIF-46**, run
`4009d95b-6e42-42d0-97c5-5f36db062baf`, succeeded using the existing Validator
agent and real Paperclip API. Its isolated-copy test suite passed 10/10;
the issue is `done` with clear execution/checkout locks. Stored artifact
`/paperclip/milestone1-validation/4009d95b-6e42-42d0-97c5-5f36db062baf.json`
independently hashes to
`24010c74f2cba47246bdb58344729a6507eb13095147a0d4c94daa7eb74b8a04`
and records commit `15660c717f00f12f097cd13644c9c1b753b4a1ae`, tree
`454b0382254312e55c3eda58793343ee5ff62ed3`, and `isolated_commit_copy`.
This verifies the deployed deterministic stage, not independent model review
or human acceptance of a new engineering task.

## Second task: preview and independent QA, 2026-09-27

**AIF-47 is owner-approved, `done`, and integrated**, not a Milestone 2 exit.
Issue `bf01619d-4359-423e-bc58-36362ddf6c99` implements a reader-only
`--dry-run` for the existing Git-doc projector. Native OpenCode
`opencode/muse-spark-1.3-contributor-free` implemented and separately reviewed
the change. Candidate commit `43a379add55538cdf8a2e3e87e5c7c25d045e28a`, tree
`50ea2aa7138f6bb5e336ab5b11f2af395f54dbf4`, is on the owned repository branch
`milestone2-projection-preview`. The owner explicitly approved this exact commit
with `approve AIF-47`. Paperclip recorded human approval at
`2026-09-27T20:33:53.753Z`, decision
`172a5c0f-f97b-423e-bf76-4f4dba0c9047`; all four policy stages are completed and
execution/checkout locks are clear. Merge
`52dee7fa2d1d8b298dff8e43a56bca010fa4f558` integrates the candidate into
`milestone1-contracts`, preserving its task branch and workspace history.

The command previews upserts and tombstones using the existing reconciliation
algorithm, accepts only reader credentials, reports actual `writes: 0`, and
leaves ordinary apply behavior unchanged. `fixtures/projection-preview-task.md`
is the exact task contract; `fixtures/projection-preview-reviewer.md` is the
separate review instruction. No new service, dependency or workflow engine.

| Native participant | Agent / run | Evidence |
| --- | --- | --- |
| Developer | `2ef551a8-e8e0-4cfe-855c-bf78f795c3a0` / final handoff `8479598d-975a-43a6-9a40-8d5a368b21af` | Four allowed files committed; targeted 27 tests passed. |
| Validator | Existing `e86e8b20-2f2c-44c3-8279-27c6378ed98d` / `40cf0273-2fff-4157-b06b-40fb8fbc1c26` | 14 CLI-unit tests; exact commit/tree artifact. |
| Reviewer | `55f721f8-54d4-4f02-ba19-f55fb24c501e` / `65c404fb-faa0-42f6-91e2-9831b7b49292` | Native review approved the same commit/tree. |
| Functional QA | `4964fe25-762e-41ff-a780-d5ee8f17e472` / `bbbb0b44-0cd3-4945-88f5-c0827c0c70b0` | Six independent black-box CLI checks passed. |

QA uses `fixtures/projection-preview-qa.mjs` and `projection_preview_qa.py`,
deployed under `/paperclip/m2-preview/milestone2/fixtures/`, with the existing
Git handoff helpers under `/paperclip/m2-preview/milestone1/fixtures/`. It tests
an isolated committed copy, checks ownership of the current QA stage, and passes
no live Paperclip/model/OpenSearch credentials into tested subprocesses. Its
loopback HTTP fixture exercises reader-only preview, repeat preview, writer
credentials present but unused, tombstone counts, apply/replay, bad revision
and malformed response. It is functional CLI QA, not browser/UX evidence.
Before implementation, five of six cases failed on the missing preview flag;
afterward all six passed against the candidate. QA script SHA-256:
`2b865f2bfc85d2dc9f5ed0e569039ed859238b8d7348acf03086a3392757b6b9`.

Actual artifact bytes independently verified:

- `/paperclip/milestone1-validation/40cf0273-2fff-4157-b06b-40fb8fbc1c26.json`:
  `ab1d39bc25257a2869e7ed14e2d5821a142c94bf49858c40dc375674475058e8`.
- `/paperclip/milestone2-qa/bbbb0b44-0cd3-4945-88f5-c0827c0c70b0.json`:
  `6a29f1eb5aa9f64df91e19fcf44511922fa1de86fd2a785d0103255a160149c6`.

The candidate full suite runs **59 tests: 57 passed, two opt-in live skips**, using the
pinned `uv` dependencies in a real Git clone. The native model runtimes lacked
`jsonschema`, so their claimed full-suite attempts were incomplete; they are not
the full-suite evidence. An archive-only host test also failed its Git-snapshot
case; the successful repeat used a Git clone, not modified tests.
After integration, the full Python suite repeated with the same result; all six
independent CLI QA checks and all 29 Node context/handoff/Validator tests passed.
`git diff --check` passed. No opt-in live test is counted as executed here.

A separate real OpenSearch check loaded candidate code, previewed the published
`c85738a` source twice with only the existing non-admin reader credentials, and
reported 49 documents, zero planned/actual writes. The 49 indexed documents,
including sequence/primary-term metadata, were unchanged (snapshot SHA-256
`ae67a3b3a65048e0b42a33e2c2adfc4d6cad8d70220f2e89cf6f53919537e42d`).
The offline QA covers nonzero planned writes without mutation. This is projector
verification, not a replacement for the still-open native Codex MCP-search gate.
The merged CLI also previewed merge revision `52dee7f` against the real cluster
with reader credentials only: 49 documents, 49 planned writes, zero actual
writes. This covers a real pending refresh without granting preview a writer.

Two launch issues were corrected without relaxing security checks:

- Paperclip redacted the innocuous phrase `bearer headers` inside retrieved
  canonical prose. Git and raw OpenSearch digests agreed; the governed text did
  not. The plugin now requests metadata without `content`, then composes text
  from the authorized Git source only after revision/blob/SHA-256 verification.
  Supplied altered text and missing/bad digests still fail. Eleven context tests
  pass, including a failing-before/passing-after metadata-only regression.
  Gateway redaction is unchanged. Old plugin files are preserved in ignored
  `.milestone0/m2-preview-pre-plugin/`; deployed files match repository bytes.
- This installed OpenCode runtime started in `/app` without explicit `--dir`.
  Both task-specific native bindings now name the Paperclip-recorded AIF-47
  worktree in `extraArgs`; permissions were not broadened. General automatic
  OpenCode directory binding remains work, not a claimed solved runtime gate.

Developer/Reviewer effective profiles remain exactly `SearchIndexTool` on the
supervised connection; generated broad grants were removed after installation.
QA has zero external tools/connections. Live catalog/profile verification passed.
Reviewer and QA were initially paused during fixture deployment, so Paperclip
correctly blocked unavailable participants; restoring the existing QA stage
preserved both earlier decisions. Their post-decision run status is `cancelled`
with `issue_reassigned`, not a failed review or a fabricated successful run.
All seven task leases are terminal with release timestamps; issue checkout and
execution locks are clear. The three task-specific agents are paused again.

The existing policy has completed its fourth, human approval stage after the
explicit owner decision; no autonomous board approval was substituted. This
closes the second accepted task and conditional functional-QA slice. Publish the
integration and refresh Git-docs at the published HEAD; verify apply/replay and
a zero-write preview, then fetch the source checkout's remote tracking ref
without moving completed task branches. The final publication/projection receipt
belongs in the Paperclip issue history.

Milestone 2 remains **IN PROGRESS**: skill/capability synchronization,
task-history projections, model-change recovery
and active-projection restore/rebuild are still open. The native Codex MCP-search
probe remains separately quota-blocked; accepting AIF-47 does not waive it.

## Automatic OpenCode worktree binding, 2026-09-27

**Source-validation checkpoint; subsequently deployed on 2026-09-28 in `6f19a0d0`
(see the containment/cutover evidence below).** Owner-fork commit
`379fe383d0e21a8e6194e799ba224762f7245cf4`, branch
`ai-factory/milestone2-opencode-workspace`, builds on active source `d57c0b7c`.
No upstream PR, new runtime, schema change, or live-controller modification.

Root cause: OpenCode 1.18.32 chooses its session directory using inherited
`PWD` before `process.cwd()` in its [run command](https://github.com/anomalyco/opencode/blob/v1.18.32/packages/opencode/src/cli/cmd/run.ts#L322).
The initial instance/adapter metadata can show the correct task path while the
native session and tools bind to `/app`. The adapter now supplies `--dir` from
the final local/prepared remote workspace on every attempt, including resume
and missing-session retry. Matching legacy explicit directory flags normalize;
conflicting/missing values fail before native invocation. Other arguments,
model/native adapter, permissions and Paperclip run ownership remain unchanged.

Evidence:

- Linux baseline: 15/15 existing execution tests. Windows baseline had five
  symlink-related failures; Linux is the deployed/tested target, not a waived
  cross-platform regression.
- RED: eight new real-child cases and two SSH cases failed on the old adapter.
  GREEN: all 58 OpenCode package tests pass, including ten new real-child cases.
  Package `typecheck`, normal package `build`, and `git diff --check` pass.
  Independent scoped review found no issues. Repo-wide build/tests were not run;
  these results do not substitute for a normal published production image.
- `fixtures/opencode-workspace-probe.mjs` runs the real 1.18.32 binary through
  the adapter with inherited `PWD=/app`. The unchanged image fails because the
  real native session records `/app`; a read-only source overlay passes with
  session `ses_f1b4a4659ffe1eVps5FK0hvOvM` bound to the task directory.
  The container has no network, live volume or credentials. A deliberately
  nonexistent model stops execution before inference; this is a directory
  regression, **not** a successful model task or durable Paperclip run.

Reproduce from this repository in PowerShell (set `$adapter` to the fork's
`packages/adapters/opencode-local/src/server/execute.ts` at the candidate SHA):

```powershell
$fixture = (Resolve-Path milestone2/fixtures/opencode-workspace-probe.mjs).Path
docker run --rm --network none --mount "type=bind,source=$fixture,target=/probe.mjs,readonly" --mount "type=bind,source=$adapter,target=/app/packages/adapters/opencode-local/src/server/execute.ts,readonly" --entrypoint node --workdir /app ghcr.io/dzikle/paperclip@sha256:95f6708217d9b34b10c9a3637d024e121a2bdaf6fa0008eb3fca5983b80f1676 --import ./server/node_modules/tsx/dist/loader.mjs /probe.mjs
```

Omit the adapter mount to reproduce the old failure. The source-overlay image
is test evidence only; image pins were unchanged at this checkpoint. A separate
free-model probe was rejected by the provider with 403; no access workaround
was attempted and no successful inference is claimed.

### Native-child credential containment, 2026-09-28

Historical AIF-47 local-agent output contains a controller database credential
in inherited `DATABASE_URL`. Do not copy raw output or its value into Git,
issues, public artifacts or model prompts. A value-comparison scan of seven
AIF-47 stored logs reported only the database credential; authentication,
signing and encryption keys are not rotated without evidence of exposure.
Historical hashed artifacts are preserved, not silently scrubbed.

Owner-fork commit `6f19a0d07f02fdaaca4085b07bb32b3f7b260383` replaces ambient
child-environment inheritance with a closed OS/startup allowlist. Explicit
agent/project/run bindings still win, including run identity, scoped API/MCP
tokens and deliberately assigned provider credentials. Native execution,
preflight, model discovery, quota helpers, provider-placeholder expansion and
local GitHub credential discovery use the same boundary. Ambient private
variables, provider definitions/keys, proxies and executable startup options
are no longer forwarded; integrations relying on them must bind them explicitly.
Native credential-file/home behavior is unchanged. No schema, adapter identity,
task engine or permission authority changes.

Validation before rollout:

- Failing-before/passing-after shared-boundary, provider/model and local GitHub
  tests. Two independent scoped reviews identified bypasses; each finding was
  corrected and regression-tested.
- Linux non-root targeted run across adapter utilities and all 13 native
  adapters: 1,246 tests, 1,239 passed, six skipped, one failed. The failure is an
  existing Cursor managed-sandbox archive-size fixture, reproduced on the
  unmodified previous image; this is **not** an all-green repo-wide test claim.
  All touched package typechecks and normal Linux package builds pass.
- Normal production amd64/arm64 builds and PID-1 orphan-reaping check pass in
  [the owner workflow](https://github.com/Dzikle/paperclip/actions/runs/36381672435).
  Published image: `ghcr.io/dzikle/paperclip@sha256:37ab79a0ea5da736bb32cded7d82a1c47873369fdc711d43e5ecec22f2797b0a`;
  amd64 manifest: `sha256:c9ae6864d9ce8ec9a5ab5ae2b64a4ce583ed30171ab3f5799634b4adc26b3bb7`.
  This includes the automatic OpenCode directory correction above; no source
  overlay or hybrid build is used for deployment.
- `fixtures/native-agent-env-probe.mjs` checks actual child `/proc` environments
  through built-in process and native OpenCode adapters, without logging values.
  Source-overlay sentinels pass; the original image fails. The deliberately
  nonexistent model prevents inference. Fixture tokens are fake, not a claim of
  a durable Paperclip run or an actual minted capability profile.
- Three operator-transport regressions pass: password stays in stdin, real TCP
  authentication is used, and failed driver output is not disclosed. Live
  preflight correctly stopped before mutation when a loopback probe accepted a
  random password: this cluster's initdb rules trust Unix sockets **and** loopback.
  A failing-before/passing-after regression now requires the exact controller
  service address, `aif-m0-paperclip-postgres-1:5432`, which uses SCRAM. No HBA
  rules or migration journals were modified to obtain a pass.

**Deployed and password rotated; bounded security gate PASS.** The immutable
published image passed 97/97 focused tests with no source overlays, plus both
real-native environment and directory fixtures. Runtime versions: Node 24.21.0,
Codex CLI 0.158.0, OpenCode 1.18.33. The latter recorded native session
`ses_f194647ecffefJgScSQQCTuOUY` in the fixture task directory despite supplied
`PWD=/app`; the nonexistent model was rejected before inference.

The owner-approved `scripts/rotate_local_paperclip_database.py` backed up
PostgreSQL and paired storage, rotated only the exposed local database password,
and restarted only PostgreSQL and the fork controller. Controller downtime:
28.4 seconds. Old-password authentication fails and new-password authentication
succeeds through the service address, before and after restart. Other
authentication/signing/encryption keys remain unchanged. PostgreSQL 17.11 and
Drizzle journal `283|1790018362070` are unchanged; no migration was required.

Complete authoritative-row checksums match before/after for 1 company, 95
agents, 47 issues, 217 runs, 1 project workspace, 12 execution workspaces and
204 leases, including run context snapshots and lease receipts. Protected
recovery material is in Git-ignored `.milestone0/m2-security-rotation-20260928/`:

- PostgreSQL dump SHA-256:
  `2aa6e2e89479578ed45022cb0ffa048e93823cd3d1036fc2ef9c95761c1aced1`
  (2,142 validated archive-list entries).
- Storage tar SHA-256:
  `a823b618cfeecc0f71370826ac1524bc5c3ae66064aae25b8a82bfc13e81297c`
  (12,710 readable archive entries).
- `receipt.json` contains row checksums and authentication assertions without
  credentials. `previous.env` / `rotated.env` are private recovery inputs, never
  publication material. Archive validation is **not** a new restore rehearsal.

Post-restart, both services are healthy. The same native-child fixture passes
inside the real controller, observing no forbidden inherited variable names
while preserving explicitly assigned run/MCP bindings; no values are printed.
All 95 saved agent configurations were also checked: no explicit binding
contains the controller credentials. The supervised MCP catalog is exactly
`ListIndexTool`, `IndexMappingTool`, `SearchIndexTool`, `MsearchTool`; Developer
and Reviewer retain search-only effective profiles, allowed searches pass and
denied operations remain denied. AIF-47 remains `done` with both issue locks
clear, and six persisted context artifacts independently match SHA-256 and
byte-size assertions after restart. Zero queued/running runs; all agents paused.

This closes an **environment/configuration inheritance** defect, not filesystem,
`/proc`, container-root or hostile-code isolation. Do not infer that native agents
cannot read controller-accessible files or privileged process state. Keep agents
paused until the relevant execution/access boundary is verified for their next
task. Stored-log access/redaction remains separate work; do not re-enable it by
rolling back to a pre-containment image. Milestone 2 is still in progress and the
native Codex search probe remains quota-blocked.

### Implementation restart checkpoint, 2026-09-28

After the owner completed Docker disk cleanup, restarted only the five current
services: fork controller, PostgreSQL, OpenSearch, supervised OpenSearch MCP and
native SSH runner. Reused existing containers, images and volumes; no image
build, migration, new dependency or model invocation. Old admission stacks and
other projects remain stopped.

Fresh checks:

- Controller, PostgreSQL, OpenSearch and MCP are healthy; runner SSH is running
  and its `codex sandbox` / `unshare -Ur` mechanics pass.
- Authoritative counts remain 1 company, 95 agents, 47 issues, 217 runs,
  1 project workspace, 12 execution workspaces and 204 environment leases.
  Schema journal remains `283|1790018362070`. AIF-47 is still `done`, with
  checkout/execution locks clear. All agents are paused; zero queued/running runs.
- Live MCP search and the exact four-tool catalog pass; Developer/Reviewer
  effective profiles remain search-only. The deployed native environment probe
  passes without inference or printing secret values.
- Offline Python suite: 59 tests, 57 passed / 2 live tests skipped. Targeted
  Node Git-handoff/validator-identity suites: 15/15 passed.

**Execution/access gate remains OPEN.** The non-root runner has zero effective
Linux capabilities, a read-only root, a separate controller PID namespace and
private `/paperclip` tmpfs rather than controller storage. Its `/paperclip/.codex`
temporary launch files are runner-local, not proof of a controller-volume leak.
However, the negative database DNS lookup passes while direct TCP connection to
PostgreSQL `172.20.0.2:5432` succeeds from runner `172.24.0.2`. Current engine:
Docker Desktop 29.1.3; both networks are non-internal bridges. No authentication
attempt or database read was performed from the runner. This is a demonstrated
network-boundary gap, not evidence of authenticated database access or a newly
exposed credential.

Minimal TCP-only reproduction with the recorded database IP (re-inspect the
address after any container recreation):

```powershell
docker exec --user node aif-m1-codex-ssh-runner node -e 'const s=require("net").connect(5432,"172.20.0.2");s.setTimeout(2500);s.on("connect",()=>{console.log("DATABASE_TCP_REACHABLE");s.destroy();process.exitCode=1});s.on("error",()=>{console.log("DATABASE_TCP_DENIED");s.destroy()});s.on("timeout",()=>{console.log("DATABASE_TCP_TIMEOUT");s.destroy()});'
```

Next slice: enforce and verify the intended runner access boundary without
changing other projects' Docker settings, then prove the governed native SSH
task path (workspace/context/MCP bindings and cleanup) before unpausing the
selected task agents. Do not mark isolation complete from DNS or container
configuration alone. Milestone 0/1 stay complete; Milestone 2 remains in progress.

## Self-enhancement programs: one authorization, four waves

`python -m milestone2.program` submits and inspects a governed
self-enhancement program: one idempotent backlog parent issue plus four
dependency-ordered child wave issues, all bound to a single validated
authorization digest. Child waves carry independent review stages but no
per-wave human approval gate; remote publication, merge, deployment, and
service restart remain unavailable unless the persisted envelope explicitly
allows the exact action and an existing command supports it.

Submission requires the private operator state file (owner identity plus
board credential, via `AIF_PAPERCLIP_STATE` or `--state`); agent/run
identities are rejected. The state file is ignored local input and is never
copied into a task description, document, workspace, or runtime environment.

```powershell
$env:AIF_PAPERCLIP_STATE = '.milestone0/self-enhancement/operator-state.json'
python -m milestone2.program submit --workflow .milestone0/self-enhancement/workflow.json --program milestone2/tasks/self-enhancement-program.json --dry-run
python -m milestone2.program submit --workflow .milestone0/self-enhancement/workflow.json --program milestone2/tasks/self-enhancement-program.json --output .milestone0/self-enhancement/submission.json
python -m milestone2.program submit --workflow .milestone0/self-enhancement/workflow.json --program milestone2/tasks/self-enhancement-program.json --output .milestone0/self-enhancement/submission.json --start
$program = Get-Content -Raw -LiteralPath '.milestone0/self-enhancement/submission.json' | ConvertFrom-Json
python -m milestone2.program status $program.parentId
```

Behavior:

- `submit --dry-run` validates the program and prints every payload without
  network or filesystem writes.
- `submit` without `--start` leaves all five issues in backlog. `--start`
  sets only the first unblocked wave to `todo`; selected agents must already
  be active, and `--start` is rejected for any read-only classification
  rather than allocating a runtime.
- Every write uses a stable request key, document content, or
  `clientRequestId`: rerunning after an interruption (parent creation,
  authorization-document write, each child POST, blocker PATCH, or receipt
  creation) converges to the same five issue IDs and one receipt. A replay
  whose stored project, parent, title, request key, document digest,
  blockers, or policy differs stops instead of overwriting.
- `submit --output` atomically writes the same receipt object it returns
  (parent/child IDs, digest, and Paperclip URL paths, no secrets).
- `status` reads Paperclip's authoritative parent/child state and rejects
  cross-company rows, more than eight children, duplicate IDs, unexpected
  child titles, or a missing authorization document/digest.
- `report PARENT --output outcome.md` renders the stored program outcome
  report as Markdown after validating its fields and candidate lineage.

## Whole-lifecycle command sequence

Each lifecycle operation lives on its owning module; there is no second
all-powerful CLI. `AIF_PAPERCLIP_STATE` already points to the current
private operator state, and `.milestone0/self-enhancement/workflow.json`
contains the admitted current V1 project and distinct agent IDs. Both are
ignored local inputs prepared once by the current operator, not additional
approval steps, and neither may enter Git or a runtime workspace.

```powershell
New-Item -ItemType Directory -Force -Path '.milestone0/self-enhancement' | Out-Null
python -m milestone2.capabilities doctor --output .milestone0/self-enhancement/health.json
python -m milestone2.program submit --workflow .milestone0/self-enhancement/workflow.json --program milestone2/tasks/self-enhancement-program.json --health .milestone0/self-enhancement/health.json --output .milestone0/self-enhancement/submission.json --start
$program = Get-Content -Raw -LiteralPath '.milestone0/self-enhancement/submission.json' | ConvertFrom-Json
python -m milestone2.program status $program.parentId
python -m milestone2.program report $program.parentId --output .milestone0/self-enhancement/outcome.md
python -m milestone3.check
```

Supporting reads stay on their owners: `python -m milestone3.context
evidence --program ... --wave ...` builds one bounded local-Git evidence
pack; `python -m milestone3.verification verify --contract ... --root ...`
executes a contract to a compact digest; `python -m milestone3.maintenance
maintenance-preview --root ... --patch ...` dry-runs a knowledge patch.
