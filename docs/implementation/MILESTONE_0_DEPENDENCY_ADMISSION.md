# AI Factory — Milestone 0 Dependency Admission

**Status:** ADMITTED — owner-maintained Paperclip fork; Milestone 1 unblocked (CodeGraphContext remains disabled)

**Executed:** 2026-09-15 (baseline); 2026-09-16–17 (Milestone 0B); 2026-09-21–23 (Milestone 0C/fork decision); 2026-09-25 (fork re-admission)

**Architecture baseline:** `71b5a5d50e7bf0e25aa1d643895779654a1522ca`

**Scope:** dependency deployment, extension-seam proof, recovery and permission
fault tests only. No Context Resolver or production workflow was implemented.

## 1. Executive verdict

On 2026-09-23 the owner changed the Paperclip distribution decision: maintain
the fixes in the account-owned [Dzikle/paperclip](https://github.com/Dzikle/paperclip)
fork, not via upstream pull requests. Both previously submitted PRs were closed
at the owner's direction; their public history remains, but neither is an open
merge request. The two fixes are combined at immutable fork commit
`a0225e8f8ae7ce16d9f52ac25e64702d7ddb173f` on
`ai-factory/milestone0-maintained`. This changes the distribution/maintenance
boundary, not Paperclip's intended sole operational authority. No Context
Resolver or V1 workflow was implemented.

The current fork head is `62760ac9fc69572866c8eed5ad714ab1ddd6cc23`.
After host disk recovery, the exact Git-blob archive built with the normal
self-hosted `production` target. Docker exported local image ID
`sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455`;
its embedded build information names that exact commit. The earlier failed
default-cloud export and a stale extracted-context lockfile error are historical,
not results for this tar-streamed production build.

The earlier combined source-equivalent Linux tree passed 121/121 focused server
tests, 2/2 plugin SDK tests, monorepo typecheck, and normal `pnpm build`. That
tree's build stamp named an older test-tree Git commit. The exact fork image
passed 66/66 focused tests. An isolated restored baseline migrated in place.
Child loss, locking, effective capability, same-run enrichment/restart, both
live controller-loss timings, orphan reconciliation, explicit resume, repeated
lease-receipt checks, and paired DB/storage restore passed on that image. The
original baseline database/storage were not migrated or overwritten. Paperclip
is admitted as the sole operational authority; Milestone 1 may begin within
the boundaries of the implementation plan.

| Dependency boundary | Verdict | Admission result |
| --- | --- | --- |
| Paperclip control plane | **ADMITTED — OWNER-MAINTAINED FORK** | Exact owner-fork image, isolated baseline migration, both live controller-loss timings, capability/enrichment and post-recovery restore pass. Section 3.0 is current evidence. |
| PostgreSQL durability | **PASS** | Persistent restart and `pg_dump`/restore counts match. |
| Agent Skills format | **PASS** | Both skills validate and lazily load in metadata and prompt-catalog styles. |
| OpenSearch 3.8.0 | **PASS** | Role isolation, filtered/multi-search, alias rebuild, persistence and loss recovery pass. |
| Official OpenSearch MCP | **PASS WITH ADAPTER** | Four-tool read-only surface and bounded results pass; explicit core-tool disables are required. |
| MemPalace 3.9.0 | **PASS WITH GATES** | Real embeddinggemma SQLite authenticated add/search and offline restart now pass; application read-only required, organizational retrieval quality not inferred from smoke. |
| CodeGraphContext 0.6.13 | **ENABLEMENT DEFERRED** | Functional graph/rebuild works; mandatory vulnerable protobuf cannot be safely overridden without regenerating old SCIP bindings. Current V1 image disabled. |
| LiteLLM 1.102.0 core | **PASS WITH NARROWED BOUNDARY** | MIT core Router fallback/loss/recovery passes. The `proxy` profile is not admitted as open source because it directly depends on proprietary `litellm-enterprise`. |

No dependency in this report becomes authoritative merely because its mechanics
passed. The source-of-truth assignments in the architecture decision remain in
force, except that Paperclip cannot assume its intended authority until the
blocking gates pass.

## 2. Reproducible environment and pins

Sections 2 and 3.1–8 retain the **Milestone 0A baseline** pins/failure evidence.
Section 3.0, secondary amendments, and the current lock supersede them for 0B/0C;
do not deploy the old Paperclip revision as an admitted fallback.

Host observations:

- Windows 11 host, Docker Desktop engine/client 29.1.3, Compose
  2.40.3-desktop.1, Linux `amd64` containers;
- Git 2.52.0.windows.1, host Python 3.14.3, Node 24.14.0;
- all service ports bind to `127.0.0.1` and all containers/volumes use the
  `aif-m0-*` prefix;
- runtime credentials live only in ignored `.milestone0/admission.env`;
- exact source checkouts lived outside the repository at
  `C:\aif-m0-src-71b5a5d`.

The canonical pins and licenses are in
[`milestone0/dependencies.lock.yaml`](../../milestone0/dependencies.lock.yaml).
The most important runtime identities are:

| Component | Exact runtime/source identity |
| --- | --- |
| Paperclip | commit `5282cabde84624320e63bd942f6ed5124952f2a2`; image `sha256:99f4de5e419e0292db9912753adb800cca2d761cb839f21c7c1f1096f689fa83` |
| PostgreSQL | 17.11 from `postgres@sha256:7456ef82e5f5bc43d997f4781bbd7c0d6389bff397564649a356e206ba473aee` |
| Agent Skills | `skills-ref` 0.1.0; commit `69ef37e9424c0a7ea9dd2293b559e43ec8176379` |
| OpenSearch | 3.8.0; image `sha256:39a8f8c63028e8b5d6b70539af1d0339b15a6729002dd5b3f4a65f520376fd30` |
| OpenSearch MCP | 0.11.0; commit `fcb23ec17186ba905590fb06b2eeecb063bc54a7` |
| MemPalace | 3.9.0; commit `38260df588968604186b525ecdffb41c140e5f61`; image `sha256:65da0834ab5ddc2d8247de43aff611393a151eac2893108e66b64f077bf1f232` |
| CodeGraphContext | 0.6.13; commit `2ef71b05a2ad1c5fd644c3ba52d77b502adaf1cf`; locally built image `sha256:9b299edcef77e86e2250dbb8f1d3cafdca576a23165bdea8522dfc35403c88b3` |
| LiteLLM | 1.102.0; commit `b94b8bca211e366328bcee3acd57d859fd35e52c`; frozen `uv.lock`; core image `sha256:c735b6415326127a4aed012df3c30dab07cd218a1887cc7184512c85e16bf63c` |

The Paperclip registry had no manifest for the source's claimed
`v2026.831.1` tag, so the test pins the immutable commit-image digest. LiteLLM
1.102.0 was not available as a final PyPI release; no neighboring release was
substituted.

During testing Docker Desktop itself stopped responding. The exact stale local
runtime directories were moved aside and empty runtime directories recreated;
unrelated containers and volumes were not modified. This was a host failure,
not attributed to a candidate dependency.
On 2026-09-17 the stale inference socket directory
`C:\Users\User\AppData\Local\Docker\run` was preserved as
`run-m0b-preserved-20260917` before Docker Desktop was restarted. That host
repair removed no repository, image, persistent volume, or unrelated container.

## 3. Paperclip admission

### 3.0 Milestone 0C fork decision / current status

#### Owner-maintained fork decision — 2026-09-23 (current)

| Required record | Result |
| --- | --- |
| Fork | [Dzikle/paperclip](https://github.com/Dzikle/paperclip), branch `ai-factory/milestone0-maintained`, current commit `62760ac9fc69572866c8eed5ad714ab1ddd6cc23`; fixes combined at `a0225e8f8ae7ce16d9f52ac25e64702d7ddb173f` (merge parents `0b455c84c0c4b52a7bd6b6b99e16863cd4a16c10` enrichment and `e319a7e8ddeba95274616d042d143c2343fc6031` SSH lease). |
| Upstream PRs | [#13772](https://github.com/paperclipai/paperclip/pull/13772) and [#13773](https://github.com/paperclipai/paperclip/pull/13773) **CLOSED** at owner request; do not reopen or submit future upstream PRs without explicit approval. |
| Normal source validation | Source-equivalent Linux tree: 121/121 focused server tests, 2/2 plugin SDK tests, `pnpm -r typecheck` PASS, `pnpm build` PASS. Build stamp names the older test-tree Git commit, so it is not an exact-commit release artifact. |
| Immutable fork image | **ADMITTED**. Exact Git-blob tar SHA-256 `5BECC12868C829A9A10934511ED54DA0236841373DC51EB8C56654775E70BC7B`; normal `--target production` build exited 0. Local `aif-paperclip-fork:62760ac` image ID `sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455`, linux/amd64; platform manifest `sha256:5a663d9396e6461ecaf55ac5fed005fc4ca423da87fe6ce4c1292efc56987ab7`. `/app/server/dist/build-info.json` records the full fork commit. Exact-image focused regressions: 66/66. This is a local immutable image, not a registry-published release; preserve the source pin and rebuild receipt. The old 0B hybrid image remains historical only. |
| Migration result | **PASS on isolated restored baseline**. PostgreSQL 17.11 database `paperclip_fork_m0` migrated in place from 279 to 283 Drizzle rows (latest journal timestamp `1790018362070`) with no manual journal/schema editing. A fresh pre-upgrade dump restored separately; all issue/run/lease/workspace ID hashes matched afterward (6/22/21/0). Paired pre-upgrade DB/storage backups are under ignored `.milestone0/fork-readmission-20260923/pre-migration-20260925/`; original baseline untouched. |
| Re-admission result | **PASS**. Child kill/reconciliation/successor and atomic checkout 200/409 passed. Controller exit 137 while source run+lease were active was tested with restart both before and after controller-lease expiry. Startup/orphan recovery, explicit reconciliation and resume produced terminal source/successor leases, stable repeated cleanup receipts, clear issue locks and non-overlapping execution intervals. The effective external MCP catalog remained exactly one search tool; allowed search succeeded and denied msearch returned 403 `deny_default` after broad grants were removed. The optional enricher persisted one ref/digest consumed by the original `process` adapter under the same run ID; it survived multiple restarts and restored bytes verified its SHA-256. Post-recovery paired DB/storage restore matched all source identities/statuses. |
| Milestone 0 final status | **ADMITTED — Paperclip gate PASS; Milestone 1 unblocked.** CodeGraphContext stays disabled pending its separate security gate. |

Live fork-image fault evidence (2026-09-25): fast controller kill at
`10:10:16Z` interrupted run `c21df6b9-991e-4b8f-b6c6-fbd2181517a7`;
restart preceded its refreshed controller-lease expiry. The source lease
converged to `expired` at `10:14:34Z`; explicit resume run
`0135da35-0748-4558-bfc3-8a7802118696` succeeded and released its lease.
The second kill at `10:52:51Z` stopped live run
`964637e2-9bf7-465e-ba70-41e69cc4a2ea`; restart occurred after its
`10:53:44Z` lease expiry. Startup marked the lost process failed, required
explicit effect reconciliation, then successful successor runs released their
leases. A competing queued run was cancelled during `preparing` before any
environment lease existed (zero matching DB rows). The admission driver's
repeat-check regression now handles that narrow case without excusing a missing
lease from a run that acquired one. Repeated reports found eight tracked runs,
all acquired leases terminal, unchanged release receipts, clear locks, no live
writer and no overlapping task intervals.

The post-recovery quiesced snapshot restored to separate database
`paperclip_fork_postrecovery_restore` and volume
`aif-m0-fork-postrecovery-restore`. Source/restored fingerprints matched for
1 company, 4 agents, 17 issues, 46 runs, 43 leases and 0 workspaces. Both
volumes' artifact bytes hash to
`d18224e97e0931f8a26b62e99ed0c6f65ea5f231a83e91442926fb0747a4a35c`,
matching both run snapshots. Ignored paired backup SHA-256 receipts are
`DEC52D6AD323C166380A537CF94482867553698ABBD211AB585D8BDF9EC115FB`
(DB) and `27A473F9FB5FA2F4BC4390B7537C464E48751AE8B67DCCB7EBE67918F2B5AB6E`
(storage). The source controller restarted healthy; a further recovery report
kept all receipts stable. The admission-driver regression suite passes 2/2.

The owner started Docker Desktop for this attempt. The normal default-cloud
source build passed compilation but exhausted host disk during image export;
Docker's Linux engine stopped and Docker Desktop was then shut down cleanly.
Three obsolete, reproducible source archives and the stopped 0B test
container/image were removed; paired backups, the original and isolated
baseline database/storage, and unrelated containers/volumes were retained.
C: still had only about 0.8 GB free at that time. On 2026-09-25 the owner
restarted the host, freeing about 25 GB. The first retry accidentally used an
older extracted context whose lockfile lacked the pinned `@lezer/common`
override; the verified archive contained it. Streaming that exact tar directly
to Docker avoided the stale copy and Windows symlink extraction errors. The
production export then completed normally. The subsequent live controller-loss
gates above passed; the earlier disk and extraction failures are historical.

Maintaining this fork is an explicit owner decision and transfers security
updates, upstream rebases, regression testing, and release-image provenance to
AI Factory. Track upstream read-only; do not make the fork a second workflow
authority. The fork can be replaced by upstream later only after the same
migration/re-admission gates pass. The 2026-09-22 submission record below is
historical and superseded.

#### Historical upstream submission record — 2026-09-22

| Required record | Result |
| --- | --- |
| Upstream PR #1 | [paperclipai/paperclip#13772](https://github.com/paperclipai/paperclip/pull/13772) — SSH logical lease recovery; open and CI passed at the 2026-09-22 capture; subsequently closed. |
| Upstream PR #2 | [paperclipai/paperclip#13773](https://github.com/paperclipai/paperclip/pull/13773) — optional pre-run run-context enrichment; open/mergeable and corrected-head CI running at the 2026-09-22 capture; CI subsequently passed and PR closed. |
| Upstream base revision | `8326e33adad63e26c918edf6adf6db114997eced` for both PRs. |
| Proposal revisions | Lease `e319a7e8ddeba95274616d042d143c2343fc6031`; enrichment `0b455c84c0c4b52a7bd6b6b99e16863cd4a16c10`. |
| Upstream revision/release tested | No supported merged release contains both changes. Proposal source branches only; not production admission. |
| Migration result | **NOT RUN** in 0C: no supported target release exists. The preserved baseline database/storage remain the future upgrade fixture. |
| Re-admission result | **WAITING**: release Docker/PostgreSQL fault, capability, enrichment, restart, and restore gates are deliberately deferred until a supported merged revision exists. |
| Milestone 0 final status | **WAITING FOR UPSTREAM — Milestone 1 BLOCKED**. |

Current upstream already contains local bookkeeping-lease cleanup introduced in
#13717, so PR #13772 was narrowed to the missing SSH equivalent and regression
coverage; it does not duplicate the local implementation. Current upstream has
no equivalent synchronous durable enrichment hook.

Post-rebase focused validation passes: lease recovery 58/58 tests (21 orphaned
active-lease plus 37 pending-cleanup cases) and enrichment 54/54 tests (two SDK,
six enrichment, forty-one plugin-route authorization and five MCP policy). Both
proposal source trees passed `pnpm -r typecheck` and normal `pnpm build` with
the release Rust runner through `de8b22d7f`; the final `79c7479d7` route guard
additionally passed its 41/41 route tests and server `tsc --noEmit`. The
`0b455c84c` OpenAPI correction passed 52/52 contract and route-authorization
tests plus server `tsc --noEmit`. The Linux
test tree was source-equivalent but its build stamp names the preceding commit.
A broad comparison found 16 environment-dependent failures identically on
pristine upstream among 163 tests
in eight compared suites (`jq`, Cursor executable, and WSL symlink assumptions),
with no proposal-specific failure. The large chat-channel suite was not counted
after sustained fixture-only warning output.

Upstream review found that the initial enrichment proposal reused the native
adapter's live MCP token. The 2026-09-22 revision gives each enricher a distinct
run-scoped token (five-minute maximum expiry), revokes it after the callback,
and mints a separate native-adapter token. The exact effective permission profile
and Paperclip budget/run authority remain unchanged. This is proposal validation,
not supported release admission.

A subsequent upstream review found that restart can rebuild task text after
the enrichment marker was persisted. The same proposal now retains the bounded
prompt separately in the run snapshot and reapplies it idempotently to rebuilt
full/compact task text; the regression covers repeated recovery without a
second plugin invocation.

Security review then identified that an ordinary company-settings row could
implicitly enable an enricher receiving a short-lived MCP bearer. Revision
`de8b22d7f` requires a separate instance-admin approval per plugin/company;
local-folder setup cannot opt in. Review of that new route found a missing
company-boundary check, corrected with a failing cross-company regression in
`79c7479d7`. The plugin must still declare
`agent.run.enrich`, be ready, and inherit only the agent's effective run-scoped
MCP profile. The five-minute token is revoked after the callback and is not
shared with native dispatch. This is a **trusted-plugin** contract, not a
guarantee that arbitrary plugin code cannot exfiltrate its temporary token;
maintainer security review remains open.

PR #13772 has completed upstream CI successfully. On #13773, an earlier head
`c844f87e7` failed two untouched CI shards (Runner Codex protocol integrity
and chat edit/delete ordering). The later `79c7479d7` run exposed one
proposal-specific failure: the new instance-admin approval route was missing
from Paperclip's OpenAPI contract. This was reproduced locally, then fixed in
`0b455c84c` with an explicit schema, authorization metadata, and regression
test; the affected suites pass 52/52. Corrected-head upstream CI later passed.
No proposal CI result is supported release evidence.

#### Milestone 0B immutable identity and compatibility

- Official base: `e1f245a6607f3920d1618409ee0d5b90c822d81e`, merged
  [lease PR #13515](https://github.com/paperclipai/paperclip/pull/13515) on
  2026-09-16. Its bounded active-lease sweep and same-tick sandbox cleanup are
  reused, not redundantly patched.
- Latest inspected upstream: `165b10bd98f842d5a3f1b1f8bd1cf731271b4a4e`
  on 2026-09-17; relevant newer source changes supplied no equivalent host-lease
  correction or enrichment/delegation hook.
- Temporary composite: `b75cbb5fa6ee408c516e04544365cdcd2ff1a383`, tree
  `8414940ca75347bd85f6b1be58af40697c82c03c`.
- Image index/observed ID:
  `sha256:3b4d342b8262f5d6ccc97d0dd6307034c5f3d644e5b52e5a92da33e9527f7943`;
  Linux manifest `sha256:97e08a86247823eba27851706e9af268f9ce20ed5315f2db187933255c9de0b5`.
- PostgreSQL 17.11 remains the same pinned durable container, with isolated
  `paperclip_m0b` database and `aif-m0b-paperclip-data` volume. Original database,
  Paperclip data volume and pre-upgrade backup are preserved.

The normal upstream server build is obstructed by runner-manifest freshness and
optional Sentry peer typings. The POC rebuilds shared/plugin SDK normally and
server with `tsc --noCheck`, retaining the pinned baseline native runner/CLI
layer and UI. Tests validate this exact hybrid image, **not** a normal upstream
release or paid Codex/Claude execution. The original database could not be
migrated using the newer divergent journal: duplicate existing
`agent_runtime_state` relation. A backup preceded the attempt; fresh-database
admission cannot prove an upgrade. No manual journal/schema rewrite is approved.

Pre-upgrade dump SHA-256:
`f0dcc74931513ba01363676d163b01b17ceeca4691880ecb7dbaf291a708c5cc`.

#### Recovery defect and correction

The original baseline source lease `1663b64b-ce98-46be-a56f-05222519cae0`
was still active/released-null when reproduced before the image change.
Upstream #13515 resolves the stranded **sandbox** ordering but is not enough
for built-in host drivers. On official base + enrichment, real controller source
`4b6531c8-db57-4b68-80a7-4b429b10ccbc` became `interrupted` /
`orphaned_running_run`; lease `b0393e93-9c8d-48b8-824d-be85bb4a1a7b` moved
from active into `pending_cleanup`, failed cleanup, and stayed stranded.

Root cause: local/SSH drivers acquire ephemeral logical leases and normally
release only their DB records. Pending cleanup routes every ephemeral lease to
`retryPendingSandboxTeardown`, an operation these drivers do not have. The
sandbox shared-resource guard also incorrectly defers SSH logical release when
a successor holds the same host/workspace URI. The correction uses recorded
`metadata.driver` + ephemeral policy, CAS-releases only the logical record,
preserves an existing release timestamp, and never deletes shared directories
or tears down a host. It repairs capped/missing-environment pending host rows
before sandbox retry-cap logic. Unknown drivers are not blanket-exempted.

No migration, provider contract, new task writer or state engine is added.
Existing sandbox resource ownership guards, teardown and bounded retries remain.
After corrected-image startup the actual stranded lease above became
`expired` / cleanup `success`, preserving its existing receipt
`2026-09-17T05:07:43.484Z`. A timestamp alone was **not** counted as cleanup:
terminal lease state and successful cleanup were required for this repair.

Relevant source: `server/src/services/heartbeat.ts` active/pending lease sweeps;
`server/src/services/environment-runtime.ts` local/SSH release vs sandbox
teardown; `server/src/services/environments.ts` lease persistence. See the two
independent patches and compatibility/reproduction notes in
[`milestone0/patches/paperclip/README.md`](../../milestone0/patches/paperclip/README.md).

#### Optional pre-run extension contract

Existing plugin SDK/worker RPC is extended with explicit `agent.run.enrich`,
`onRunContextEnrich`, and `enrichRunContext`, rather than introducing a wrapper
adapter or nested executor:

```text
existing Paperclip run + selected adapter + governed MCP assignment
→ ready/company-enabled optional plugin enrichment
→ bounded artifact ref + SHA-256 + metadata / optional prompt
→ context_snapshot.paperclipRunContextEnrichment persisted before dispatch
→ original native/legacy adapter, same run ID, existing budget/permission logic
```

Maximum eight enrichers, 64 KiB prompt and 16 KiB metadata each, 2,048-char
artifact URI and required SHA-256. Plugin/validation/persistence failure stops
before provider invocation. Existing snapshots make repeat same-run enrichment
idempotent; before-persist crashes may repeat the hook, so artifact writes must
be idempotent. Worker timeout/cancellation/token expiry remain Paperclip's.
The host validates a digest assertion; it does not fetch arbitrary URIs.
Artifact bytes are independently hashed by the admission fixture.

Production plugins must not persist credentials. Installing the capability
trusts the plugin with **run-scoped governed** MCP credentials, not privileged
OpenSearch access. Role-specific composition/token policy remains future
Resolver work; no Resolver, capability compiler, projections or workflow pack
was built.

Native proof run `a0b156c5-1312-4c21-b607-1ecfb0bd490f` succeeded using the
unchanged built-in **process** adapter and logical Developer identity
`bca6f9d6-9755-440b-93af-698a3fb20f76`. The placeholder plugin wrote:

- ref: `file:///paperclip/milestone0-context/a0b156c5-1312-4c21-b607-1ecfb0bd490f.json`;
- SHA-256: `8741004fc254a0af35726afd51ae4dfe62eac55f3631b4e1441578773f9fa5d2`;
- 1,094 bytes, fixture `placeholder-v1`, one governed MCP assignment.

The native process itself consumed those bytes and recorded the identical
ref/digest. The artifact, durable snapshot and completed run stayed identical
after controller restart. This proves order/identity/delegation using a real
native adapter; it does **not** claim live Codex/Claude harness admission.

#### Regression and live gates

Baseline Linux red run: original 12 tests PASS; four new local/SSH cases FAIL
with active/pending leases rather than expired. An earlier synthetic reaper
fixture also caused an unrelated FK cleanup error; that run was discarded and
the lease sweeps isolated. First fix attempt exposed SQL Date parameter
encoding; it was corrected, not counted as green.

Final immutable-image command:

```sh
docker run --rm --user node --tmpfs /tmp:rw,exec,nosuid,size=512m,mode=1777 \
  --entrypoint sh aif-paperclip-m0b:b75cbb5fa -lc \
  'cd /app && ./node_modules/.bin/vitest run server/src/__tests__/heartbeat-orphaned-active-lease-sweep.test.ts server/src/__tests__/heartbeat-pending-cleanup-sweep.test.ts server/src/__tests__/heartbeat-run-context-enrichment.test.ts packages/plugins/sdk/tests/run-context-enrichment.test.ts --silent --no-file-parallelism --maxWorkers=1'
```

Fresh pre-commit result: **4 files / 41 tests PASS**, no skips, 27.75 s,
Vitest 4.1.11. An earlier same-image full pass took 194.42 s. Two final
overlay-filesystem rechecks (parallel and serialized) timed out in the existing
20-second embedded-PostgreSQL setup hook: 25 passed, 16 not executed, suite
failure. They are not counted as passes. Moving only disposable test DBs to
tmpfs and serializing files restored the full pass without changing source,
assertions or timeouts. Production recovery tests still used real durable
Docker/PostgreSQL volumes, not tmpfs. Upstream should align this old 20-second
hook with its existing embedded-DB test-cost budget; this operational test
flakiness remains a review note, not a claimed recovery assertion failure.
The passing tests include overlapping
CAS cleanup, stable repeated receipts, live shared-host successor preservation,
capped pending repair, existing sandbox backoff/retry-cap/provider-unavailable
tests, durable pre-dispatch snapshot, and SDK opt-in/backward compatibility.
Host Windows runs had cold embedded-PostgreSQL setup/path/symlink failures and
were not counted as integration passes. Full upstream CI/typecheck/release
build remains required for merge/release.

Live capability proof `55561903-b4d3-4e99-a703-46cbba36385c` succeeded. Company
profile and agent-generated broad grants were unbound; effective external grant
was exactly `SearchIndexTool` on connection
`9a746e83-f6a3-437f-9b26-d05c96949bdd`, with search HTTP 200/isError false and
msearch HTTP 403/`deny_default`. The enricher independently initialized the
assigned gateway and got the same exact allow/deny surface. Four built-in
Paperclip resource/prompt context helpers are explicitly permitted, not hidden
external grants. The process adapter's separate connection-intent gateway 404
responses are **not** permission evidence.

Concurrent checkout issue `d8afbe9f-91ec-4ca9-942d-1c73894c1c8c`: HTTP
200/409, one persisted Developer owner. The probe task was cancelled afterward;
its run/claim evidence remains durable.

Live child kill: PID 672, source `85b345c4-cc09-4ea6-ae3f-e05de916fd37`
failed with `adapter_failed`, reconciliation action
`1f79c024-1557-462b-aa3b-a390fe241d7d` explicitly acknowledged provider stop
and recorded effects, successor `935a2227-1b17-4f5a-9578-f054ef03893c`
succeeded. This is not automatic replay of uncertain side effects.

Fast controller kill/restart (exit 137, before controller lease expiry): source
`ea4ce4f7-e6df-4dae-a9c5-49ed3c661101` terminalized by backstop as
`interrupted` / `orphaned_running_run`; explicit issue resume coalesced to live
successor `ba114391-dd1f-405c-9186-10101bd22079`, which succeeded. An additive
deferred wake made a **sequential**, not concurrent, extra run
`9ef2d2b5-c15f-4c9f-8e5f-631f4a2bfad2`; closing the completed test task
cancelled it. Its lease was included, not hidden from release assertions.
Source host lease expired with cleanup success on the eligible periodic sweep,
after the configured five-minute backoff (no test-only DB timestamp editing).

| Fast-restart / child-loss run | Lease | Terminal state / unchanged release receipt |
| --- | --- | --- |
| `85b345c4-cc09-4ea6-ae3f-e05de916fd37` | `211ca0eb-6aeb-49cc-a8cc-15e7f162bfbb` | failed; `2026-09-17T05:25:23.774Z` |
| `935a2227-1b17-4f5a-9578-f054ef03893c` | `ddc4da8e-7270-4102-ad69-141ba0f78ca8` | released; `2026-09-17T05:25:36.291Z` |
| `ea4ce4f7-e6df-4dae-a9c5-49ed3c661101` | `61ad1891-58c2-4ec2-87df-f035c4cd2042` | expired / cleanup success; `2026-09-17T05:31:17.302Z` |
| `ba114391-dd1f-405c-9186-10101bd22079` | `405cdacf-be29-4455-812c-62f02b8ba0eb` | released; `2026-09-17T05:27:55.071Z` |
| `9ef2d2b5-c15f-4c9f-8e5f-631f4a2bfad2` | `8bee6f42-448c-4325-902e-40b88d60062a` | expired; `2026-09-17T05:27:55.425Z` |

`recovery-report` PASS: every acquired source/successor lease terminal, cleared
checkout/execution locks, no remaining live writers, no overlapping task run
intervals, repeat receipts unchanged. Delayed cleanup within configured backoff
is acceptable **eventual** release, not an exactly-once external side-effect
claim. For host leases the corrected release is a single status-guarded DB write.

Restart after controller-lease expiry was tested separately. Source
`e2b6b9a4-0f80-44ce-be8d-e580116e2a30` had lease expiry
`2026-09-17T05:32:50.334Z`; controller exit 137 occurred at
`05:31:50.617456526Z`, and restart at `05:33:08.037879478Z`. Startup recovered
it as `failed` / `process_lost`, immediately releasing its environment lease.
Reconciliation action `0c7f7f63-5e1c-42a3-b398-e941172a6bf7` required explicit
provider-stopped acknowledgement; recovery successor
`cbeb08ff-e988-43d0-bd6d-d4c214f63da9` succeeded. A further explicit task
resume `30c7acc3-124f-4fde-b161-44c509c27b9f` succeeded. Closing the completed
fixture task cancelled its sequential deferred-wake extra run; that lease was
also checked. No timestamp manipulation or uncertain-side-effect auto-replay
was used.

| Expired-controller startup run | Lease | Terminal state / unchanged release receipt |
| --- | --- | --- |
| `e2b6b9a4-0f80-44ce-be8d-e580116e2a30` | `8143ac46-4c4f-433f-9811-e17ae6f3a74d` | failed; `2026-09-17T05:33:15.259Z` |
| `cbeb08ff-e988-43d0-bd6d-d4c214f63da9` | `1c05241f-c11c-4e3f-bf80-3a41d51cea61` | released; `2026-09-17T05:33:32.099Z` |
| `30c7acc3-124f-4fde-b161-44c509c27b9f` | `72ec334d-d1ae-43fd-8389-7f42f1955274` | released; `2026-09-17T05:33:52.612Z` |
| `bae8407f-1483-4ffe-afae-af1aedf735bd` | `a6563b39-3c8e-4f3c-bf5c-787b4427ac92` | expired; `2026-09-17T05:33:52.935Z` |

#### Final backup/restore and repeat-startup check

With the original controller stopped to quiesce writes, `pg_dump -Fc` of
`paperclip_m0b` was restored with `pg_restore --exit-on-error` into the isolated
`paperclip_m0b_readmission_restore` database. Both databases contained **48 runs,
42 leases, 16 issues**. The restored completed native run retained the exact
artifact ref/digest above, and the fast-restart/startup source lease states and
release receipts matched. Separately, a read-only tar backup of
`aif-m0b-paperclip-data` was extracted into disposable volume
`aif-m0b-readmission-restore`; independently hashing the restored artifact
returned the same `8741004f…` SHA-256. The original storage was never overwritten.

Ignored local backup integrity receipts (contain secrets; do not commit):

- `paperclip-m0b-readmission-20260917.dump`:
  `375199a0c9ce91175f7f7de4d7ed04f8513a9e73b938583f2149edbbd96a9588`;
- `paperclip-m0b-data-readmission-20260917.tar.gz`:
  `a0a0c9f08e04082f409fc84ebbc68bfb76bc914af1499174bba894925872f541d`.

This proves snapshot/data restoration, not an automated disaster-recovery SLA
or old-database migration. Restore the same deployment secrets with the paired
database/storage snapshot. After restarting the original controller and waiting
for health, both commands passed again:

```sh
python milestone0/scripts/paperclip_admission.py recovery-report
python milestone0/scripts/paperclip_admission.py enrichment-report
```

All **nine** acquired source/successor/cancelled-run leases above remained
terminal with identical receipts; task execution intervals did not overlap,
checkout/execution locks were clear, and there were no live task writers.
The enriched run/artifact still had the same durable ref and full SHA-256.
The exact external search-only effective MCP profile was also reasserted after
this restart; both Paperclip and offline MemPalace Compose configs validate.
A first verification request during `health=starting` disconnected and was not
counted as a pass; healthy retry supplied the evidence. Disposable restoration
targets were removed after validation; paired backup files and original data
remain recoverable.

| Paperclip 0B gate | Local immutable-image result | Admission consequence |
| --- | --- | --- |
| Child-process loss / reconciliation / successor | PASS | Explicit effects acknowledgement, both leases released. |
| Controller loss before expiry / orphan backstop | PASS | Source eventually released at eligible sweep; sequential extra accounted for. |
| Startup after controller expiry / explicit resume | PASS | Startup source release, both successors and extra released. |
| Idempotent recovery / task locking / no duplicate writer | PASS | Nine stable receipts, non-overlapping intervals, 200/409 checkout. |
| Generated broad grant removal / exact MCP profile | PASS | Search only externally; msearch deny-default; same governed surface in hook. |
| Pre-run enrichment / original native dispatch / durable artifact | PASS | Same process-adapter run consumed bytes, snapshot survives restart/restore. |
| Paired database/storage backup and restore | PASS | Counts and durable/actual artifact identity match. |
| Supported upstream fixes / normal release build / migration | **WAITING** | Prepared independent proposals are not merged; hybrid image and fresh DB are insufficient. |

Therefore the local technical remediation gates passed, but the **historical
0B overall Paperclip admission gate remained WAITING FOR UPSTREAM**, not PASS.

Failed fixture attempts (duplicate issue titles/idempotency, an external adapter
artifact-path collision, unfinished probe-task re-wakes, and the initial native
consumption assertion) were excluded. The harness now uses unique test rounds,
exact wake/source exclusions, closes completed probe tasks, asserts native
consumption, and includes all discovered source/successor/cancelled runs in its
lease inventory. It checks cleared locks, terminal leases, stable repeated
release receipts, and non-overlapping task execution intervals.

#### Secondary gate dispositions

**LiteLLM:** final V1 selection is embedded **MIT core Router only** at the
existing exact pin. Licensed proxy DEFERRED; no V1 procurement or second gateway
service. Native harnesses remain native adapters.

**MemPalace:** real embeddinggemma q8 CPU/two-thread SQLite path warmed and
tested. Exact HF snapshot
`5090578d9565bb06545b4552f76e6bc2c93e4a66`, tokenizer/model hashes in lock,
offline runtime. Warm six-document ingest 8.65 s; semantic order query returned
relevant Java/TS paths with cosine 0.76/0.73/0.69 and zero BM25 contribution.
Authenticated add/search returned provenance-rich drawer
`drawer_ai-factory_pitfalls_e5c23039eaa28a2725c05cd0` at similarity 0.676;
same search survived next-day restart offline. This is mechanics/semantic smoke,
not organizational retrieval-quality proof. Cache material must be backed up,
verified and prewarmed before offline readiness.

**CodeGraphContext:** current V1 integration **disabled / enablement DEFERRED**.
`pip-audit` 2.9.0 found eight advisories in pip 25.0.1 (six installer-only) and
protobuf 3.20.3 (two runtime DoS). The mandatory source constraint prevents a
supported fixed protobuf; 5.29.6 breaks generated `scip_pb2` import. Optional
SCIP is default-disabled, but that is not a vulnerability waiver. Regenerate
bindings/lift pin upstream, trim runtime dependencies and re-audit/retest before
enabling the one graph candidate. See
[protobuf parser advisory](https://github.com/protocolbuffers/protobuf/security/advisories/GHSA-8qvm-5x2c-j2w7)
and [JSON parser advisory](https://github.com/advisories/GHSA-7gcm-g887-7qv7).
Separate npm build/web findings are not conflated with Python query reachability.

No authority boundary changes: Paperclip is still the intended **sole** task/
run/workspace owner only **after** admission; Git owns current canonical truth,
MemPalace experiential memory, and OpenSearch/code graph remain projections.

### 3.1 Deployed shape

Paperclip ran against durable PostgreSQL with authenticated/private deployment,
strict encrypted secrets, loopback exposure, persistent Paperclip/PostgreSQL
volumes, and four stable logical agents: Developer, Reviewer, QA, and the seam
probe. Reviewer and QA were independent agent rows with independent bindings;
logical identities did not change during runtime tests.

### 3.2 Pre-run Context Resolver seam — blocker

The throwaway external adapter in
[`milestone0/fixtures/paperclip/context-seam-adapter`](../../milestone0/fixtures/paperclip/context-seam-adapter)
was installed as `aif_context_seam_poc`. It executed after Paperclip created the
run and before any model/provider invocation, received `runtimeMcp`, wrote a
placeholder context artifact, and exercised the governed MCP gateway. This
proves a supported adapter may itself perform pre-provider work.

It does **not** prove the required wrapper seam:

1. `ServerAdapterModule.execute` has no public operation to delegate to another
   registered Paperclip native adapter while preserving the same run;
2. the invocation receives a shallow adapter-context copy, so mutating
   `ctx.context` does not persist an `aiFactoryContext` field to
   `heartbeat_runs.context_snapshot`;
3. the process adapter consumes connection-intent MCP environment rather than
   the external adapter's `runtimeMcp` object.

Run `660a82cf-393e-4218-b5a2-d65572e00329` completed the placeholder adapter,
but its host context snapshot had no persisted AI Factory context and its native
runtime remained a placeholder. The gate requires either a small general
upstream pre-run enrichment/delegation hook or an equally supported wrapper that
does not duplicate run state. A standalone adapter that reimplements each
native runtime is not an acceptable seam.

### 3.3 Capability enforcement — pass with configuration hazard

The final effective profile exposed only `SearchIndexTool`. Through the
per-run named gateway the adapter saw that tool plus Paperclip's four context
helper tools. Calling search returned HTTP 200 and `isError: false`; calling
`MsearchTool` returned HTTP 403 with `deny_default`. The gateway credential row
was revoked after the run while its nominal expiry remained in the future.
After the OpenSearch stop/restart test, integrated seam run
`c4b939d8-6743-4184-80a8-8870c0c6b117` repeated the same one-tool catalog,
successful search and denied msearch through Paperclip, proving the governed
path recovered with its dependency.

Two integration hazards require explicit admission configuration:

- installing an MCP application/connection auto-binds an additive broad
  `app:<connection-id>` profile; it had to be explicitly unbound;
- a profile entry containing only a tool name appeared in policy but did not
  resolve to a deliverable connection. The admitted profile uses the exact
  catalog entry.

Permissions therefore work at runtime, but the future capability compiler must
assert the complete effective profile after installation rather than assuming a
narrow profile replaces broad generated grants.

### 3.4 Agent child-process loss — pass

An exact child PID was killed during run
`1c6735d4-3f54-4c38-97f9-4f25d043e533`. Paperclip persisted the failure as
`adapter_failed`/`legacy_execution_requires_reconciliation`, retained task
assignment, captured and resolved an explicit recovery action, and launched
successor run `32fcdb73-1704-4c9e-b94d-fbd743c78ac0`.

The successor succeeded, preserved the issue ID, recorded
`retry_of_run_id`/`contextSnapshot.previousRunId`, forced a fresh session, and
cleared issue execution/checkout locks. Both source and successor environment
leases were released. This is safe explicit reconciliation, not blind replay.

### 3.5 Paperclip controller/container loss — task recovery passes, lease recovery fails

Run `f5b6afa8-5fa1-41d8-9c9f-e9fde88a198e` was active when the exact Paperclip
container was killed. After starting the same container/database:

- startup recovery terminalized the run as `interrupted` with
  `error_code=orphaned_running_run`;
- the issue lock was cleared and the stranded assigned issue was blocked for
  explicit operator disposition;
- after an explicit resume, run `795d79ce-79a0-4a52-a643-acb46f139974`
  succeeded and its environment lease was released.

The original lease did not recover. Fresh database evidence after all recovery
work completed was:

```text
1663b64b-ce98-46be-a56f-05222519cae0
run=f5b6afa8-5fa1-41d8-9c9f-e9fde88a198e
status=active  lease_policy=ephemeral  expires_at=NULL  released_at=NULL
```

Source tracing identifies an ordering race: stale-issue recovery terminalizes
the orphaned run and clears its issue lock before the heartbeat orphan reaper
handles it. The normal reaper ignores an already-terminal run, so its
environment lease is never released. This violates the one-writer and cleanup
invariant and blocks Paperclip admission.

### 3.6 Backup/restore — pass

A custom-format `pg_dump` was 1,248,538 bytes. It restored into a temporary
database with counts matching the live authority: 1 company, 4 agents, 6
issues, and 20 heartbeat runs. The temporary restore database was then dropped;
the ignored dump remains local admission evidence.

## 4. OpenSearch and official MCP admission

OpenSearch 3.8.0 ran as a dedicated single-node cluster with a persistent named
volume. The admission provisioner created versioned indices/aliases and
separate test roles:

- agent write attempt: HTTP 403;
- projector read attempt: HTTP 403;
- filtered current-project search: one expected fixture hit;
- `_msearch` hit counts: `[11, 1]` before the later 12-document bound fixture;
- delete/rebuild: 12 documents restored and alias moved to `aif_docs_v2`.

The official MCP negotiated protocol `2025-06-18`. The upstream configuration
implicitly includes `core_tools`, so four explicit disables were required in
addition to `enabled_tools`. The final surface was exactly:

```text
ListIndexTool
IndexMappingTool
SearchIndexTool
MsearchTool
```

Mapping, filtered search, and multi-search completed against the real cluster.
A request for `size: 100` returned at most eight hits while retaining the true
total, proving the upstream result cap. AI Factory still needs byte/token/source
budgets in its thin adapter.

For the local self-signed test cluster only, the MCP process used
`OPENSEARCH_SSL_VERIFY=false`. Production must use a trusted certificate and
must not copy that setting.

Fault injection stopped OpenSearch while leaving the MCP process running. A
search failed in 5,178 ms under the five-second client bound. Restarting the
same OpenSearch volume restored MCP operation without restarting MCP, and a
match-all search reported all 12 documents. OpenSearch remains rebuildable
projection state, never canonical truth.

## 5. MemPalace admission

The admitted mechanics profile is one writer, `sqlite_exact`, an
OpenAI-compatible embedding interface, persistent volume, and Paperclip-side
tool allowlisting. A deterministic local eight-dimensional embedding endpoint
was used to test storage/recovery mechanics; this does not admit production
retrieval quality.

One representative repository-pitfall drawer was added and retrieved with its
wing, room, source document and text intact. A second writer against the same
palace refused the lease and exited, proving single-writer enforcement. Stopping
the service caused bounded connection refusal; restarting it recovered the same
drawer.

Export required stopping the writer because the exporter also acquires the
writer lock. With the writer stopped, export produced one wing, one room, and
one drawer. Restoring a copy of the volume into a second service succeeded when
the application used `--read-only`; search returned the same drawer and a
mutating `mempalace_add_drawer` call returned MCP error `-32003`, “Server is in
read-only mode.”

Two important hazards remain:

- the default MiniLM profile reported healthy before its first authenticated
  write downloaded about 79.3 MB and held the writer lease for more than 70
  seconds. Readiness must include a warmed embedding/index operation;
- a filesystem read-only `/data` mount reported healthy but could not open the
  palace because MemPalace writes `/data/.mempalace` lock/sync state. Peer-sync
  also attempted logstream schema writes. Disaster-recovery validation must use
  application read-only mode on a writable restored volume.

The writable server negotiated MCP `2025-06-18` and exposed 45 tools, including
task, artifact, sync, delete, graph-write and patch operations. Ordinary agents
must receive only the exact memory operations needed by their role.

## 6. CodeGraphContext admission

CodeGraphContext was built from the exact source revision into Linux image
`sha256:9b299edcef77e86e2250dbb8f1d3cafdca576a23165bdea8522dfc35403c88b3`.
The fixture includes Java, TypeScript, and Go source.

Cold indexing took 108 seconds and produced six source/config files, eight
functions, two classes, and six `CALLS` relationships. Symbol lookup found Java
`validate`, TypeScript `validateOrder`, and Go `Validate`. Caller/callee tests
found the expected `submit`, `submitOrder`, and `Submit` relationships. The
module-level `deps orders` query returned no useful dependency result.

MCP negotiated protocol `2025-03-26` and reported version 0.6.13. Real MCP
`find_code` and `analyze_code_relationships(find_callers)` calls returned the
expected path and caller. Its 29-tool surface also contains graph writes,
repository deletion, raw Cypher, watchers and simulations; the AI Factory
adapter must publish only bounded read operations.

A final smoke invocation that omitted the backend auto-selected an empty
FalkorDB store even though the volume contained the admitted LadybugDB graph.
Repeating with explicit `--database ladybugdb` found repository `workspace` and
TypeScript symbol `validateOrder`. Deployment must pin the backend and path; it
must not rely on auto-detection.

Adding one function and running `cgc update` took 64.01 seconds and deleted/
reindexed the repository rather than performing a true incremental update.
This changes the performance assumption in ADR 004. After deleting the exact
graph volume, queries returned no elements; rebuilding solely from the tracked
Git fixture took 113.63 seconds and restored the original graph statistics.

The source build reported 16 npm audit findings (1 low, 6 moderate, 9 high).
They are a supply-chain remediation gate before broader deployment, not a reason
to grant the graph canonical status.

## 7. Agent Skills admission

The canonical `repository-discovery` and `code-review` packages both validated
with `skills-ref` 0.1.0. A metadata-only catalog loaded names/descriptions
without loading bodies; a second prompt-catalog style lazily loaded both skill
bodies/resources. AI Factory metadata remains in external-standard-compatible
frontmatter/sidecars. Git remains the authority, and `allowed-tools` text is not
used as runtime authorization.

## 8. LiteLLM admission

The exact-source Linux image reports LiteLLM 1.102.0 and contains neither
`litellm-enterprise` nor `litellm-proxy-extras`. With the primary endpoint
returning HTTP 503, the core Router selected `admission-fallback` in 318 ms,
returned `fallback-ok`, and preserved usage as seven prompt plus three
completion tokens. With the fallback listener also removed, the call returned a
bounded `ServiceUnavailableError` in 331 ms. Restarting the fallback restored
the same successful result in 318 ms.

The selected deployment boundary nevertheless changes: at 1.102.0 the `proxy`
optional dependency directly includes
`litellm-enterprise==0.1.67`, whose `LicenseRef-Proprietary` permits development
and testing but requires an enterprise license for production. The cold proxy
build also exceeded 1 GB before Python dependencies and was abandoned during a
large nonessential proxy artifact download.

The test image itself is 4.39 GB because it retains its Linux compiler layer;
this is an admission artifact, not a production image. AI Factory admits the
MIT core `litellm.Router` for raw API calls. A production integration needs a
small embedded raw-API adapter/runtime image. Milestone 0B explicitly defers the
licensed proxy; it is not an alternative V1 deployment shape.
It must not label the current proxy deployment wholly open source. Native coding
harnesses remain outside both paths.

## 9. Dependency-loss matrix

| Injected loss | Observed failure | Recovery | Authority effect |
| --- | --- | --- | --- |
| Agent child process | Durable failed run and explicit reconciliation | Successor run succeeded; locks/leases released | No task loss or duplicate writer |
| Paperclip controller container | Orphan terminalized; uncertain effects require explicit disposition | Local 0B fast restart/resume and eventual original lease cleanup pass | Sole operational-owner design retained; production admission waits for exact fork-image re-admission |
| OpenSearch under live MCP | Client timeout at 5.178 s | Same MCP recovered after cluster restart; 12 docs persisted | Paperclip/Git truth unaffected |
| MemPalace service | Connection refused | Same drawer recovered after restart | Task/canonical truth unaffected; memory context degrades |
| CodeGraph volume | Empty graph | Rebuilt from Git in 113.63 s | Git truth unaffected |
| LiteLLM upstream(s) | Primary 503 fell back successfully; both endpoints down returned `ServiceUnavailableError` in 331 ms | Restarted fallback restored success in 318 ms | No task authority; provider call only |

This validates the intended failure domains. It does not authorize automatic
self-healing workflows; those remain post-admission implementation work.

## 10. Configuration and evidence map

| Evidence/configuration | Repository location |
| --- | --- |
| Exact dependency pins and rollback rule | [`milestone0/dependencies.lock.yaml`](../../milestone0/dependencies.lock.yaml) |
| Isolated service definitions | [`milestone0/compose/`](../../milestone0/compose) |
| Official OpenSearch MCP allowlist | [`milestone0/config/opensearch-mcp.yaml`](../../milestone0/config/opensearch-mcp.yaml) |
| Paperclip seam/recovery fixture | [`milestone0/fixtures/paperclip/`](../../milestone0/fixtures/paperclip) |
| Java/TS/Go graph fixture | [`milestone0/fixtures/codegraph/`](../../milestone0/fixtures/codegraph) |
| Deterministic API/embedding test endpoint | [`milestone0/fixtures/mock-openai/server.py`](../../milestone0/fixtures/mock-openai/server.py) |
| Admission probes | [`milestone0/scripts/`](../../milestone0/scripts) |
| LiteLLM exact-source core build | [`milestone0/containers/litellm-core.Dockerfile`](../../milestone0/containers/litellm-core.Dockerfile) |
| Paperclip independent upstream proposals / exact test bundle | [`milestone0/patches/paperclip/README.md`](../../milestone0/patches/paperclip/README.md) |
| Paperclip immutable admission-only source-layer build | [`milestone0/containers/paperclip-m0b.Dockerfile`](../../milestone0/containers/paperclip-m0b.Dockerfile) |
| MemPalace prewarmed offline production-embedding profile | [`milestone0/compose/mempalace-production-embedding.yaml`](../../milestone0/compose/mempalace-production-embedding.yaml) |

Generated secrets, database dumps, board state, cloned upstream sources, graph
databases, and runtime logs are deliberately ignored and are not canonical
repository artifacts.

## 11. Next implementation milestone

**Milestone 1 is unblocked, but was not implemented by this admission work.**
Start with the canonical Git contracts, project overlays and source-of-truth
schemas in the [integration-first kickoff](IMPLEMENTATION_KICKOFF.md). Then
implement the bounded Context Resolver against the admitted pre-run hook and
governed MCP surface, followed by idempotent OpenSearch projections and
role/capability policy templates. Do not add a second task engine or MCP
authority. Keep CodeGraphContext disabled until compatible SCIP/protobuf
remediation, trimmed audited runtime and functional re-admission pass; carry
forward MIT-core-only LiteLLM and the pinned MemPalace embedding cache.

No actual Context Resolver, projection worker, capability compiler, engineering
workflow, model selection, self-healing or self-improvement was implemented in
Milestone 0. The local admitted image is not registry-published; publish an
owner-controlled immutable artifact before deploying beyond this host, without
changing the recorded admission result or silently retagging it.
