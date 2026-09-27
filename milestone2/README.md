# Milestone 2 — MCP supervision and native-catalog hardening

This is one reliability slice of Milestone 2, not the Milestone 2 exit. The
official OpenSearch MCP server remains the provider; Paperclip remains the
runtime catalog, profile, and run authority.

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
