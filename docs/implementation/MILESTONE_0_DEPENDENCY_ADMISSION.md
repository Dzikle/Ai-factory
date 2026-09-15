# AI Factory — Milestone 0 Dependency Admission

**Status:** BLOCKED — do not begin Milestone 1

**Executed:** 2026-09-15

**Architecture baseline:** `71b5a5d50e7bf0e25aa1d643895779654a1522ca`

**Scope:** dependency deployment, extension-seam proof, recovery and permission
fault tests only. No Context Resolver or production workflow was implemented.

## 1. Executive verdict

The selected data-plane components are usable behind the boundaries defined by
the adoption spike, but the selected control plane is not admitted at its
pinned revision. Paperclip recovers task/run state after a controller crash,
yet leaves the crashed run's ephemeral environment lease permanently active.
Its public external-adapter contract can run a pre-provider enrichment adapter,
but cannot transparently delegate to a separately registered native adapter or
persist mutations of the invocation context back into the host run snapshot.

Milestone 0 therefore does not exit. Do not implement Milestone 1 or substitute
a private Paperclip fork. The next milestone is a narrow upstream remediation
and re-admission cycle for Paperclip's lease reaper and pre-run extension seam.

| Dependency boundary | Verdict | Admission result |
| --- | --- | --- |
| Paperclip control plane | **BLOCKED** | Process-loss recovery passes; controller-loss lease cleanup and required transparent pre-run seam fail. |
| PostgreSQL durability | **PASS** | Persistent restart and `pg_dump`/restore counts match. |
| Agent Skills format | **PASS** | Both skills validate and lazily load in metadata and prompt-catalog styles. |
| OpenSearch 3.8.0 | **PASS** | Role isolation, filtered/multi-search, alias rebuild, persistence and loss recovery pass. |
| Official OpenSearch MCP | **PASS WITH ADAPTER** | Four-tool read-only surface and bounded results pass; explicit core-tool disables are required. |
| MemPalace 3.9.0 | **PASS WITH GATES** | Single-writer, persistence, export/restore, application read-only mode and loss recovery pass; default embedding readiness and filesystem read-only restore do not. |
| CodeGraphContext 0.6.13 | **PASS WITH ADAPTER** | Java/TS/Go symbol and caller tests plus destructive rebuild pass; update is a full reindex and MCP must be allowlisted. |
| LiteLLM 1.102.0 core | **PASS WITH NARROWED BOUNDARY** | MIT core Router fallback/loss/recovery passes. The `proxy` profile is not admitted as open source because it directly depends on proprietary `litellm-enterprise`. |

No dependency in this report becomes authoritative merely because its mechanics
passed. The source-of-truth assignments in the architecture decision remain in
force, except that Paperclip cannot assume its intended authority until the
blocking gates pass.

## 2. Reproducible environment and pins

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

## 3. Paperclip admission

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
small wrapper/runtime image, or an explicit commercial decision for the proxy.
It must not label the current proxy deployment wholly open source. Native coding
harnesses remain outside both paths.

## 9. Dependency-loss matrix

| Injected loss | Observed failure | Recovery | Authority effect |
| --- | --- | --- | --- |
| Agent child process | Durable failed run and explicit reconciliation | Successor run succeeded; locks/leases released | No task loss or duplicate writer |
| Paperclip controller container | Orphaned run terminalized; issue blocked for disposition | Explicit task resume succeeded | **Failed:** source environment lease remained active |
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

Generated secrets, database dumps, board state, cloned upstream sources, graph
databases, and runtime logs are deliberately ignored and are not canonical
repository artifacts.

## 11. Required next milestone

Remain in Milestone 0 and do only the following:

1. report the Paperclip recovery ordering defect upstream with a minimal test
   proving terminalized orphan runs release every associated environment lease;
2. propose an upstream-compatible pre-run enrichment contract that can persist
   a bounded context-artifact reference/digest and then delegate to a selected
   native adapter in the same Paperclip run;
3. upgrade to a fixed immutable Paperclip revision and repeat controller kill,
   lease, capability, backup/restore, and seam tests;
4. decide whether V1 uses MIT LiteLLM core Router or procures the current proxy
   license, then pin only that admitted deployment shape;
5. warm/validate the selected production embedding implementation and remediate
   CodeGraphContext image vulnerabilities before enabling those integrations.

Do not implement the actual Context Resolver, projections, capability compiler,
or V1 engineering workflows until items 1–3 pass.
