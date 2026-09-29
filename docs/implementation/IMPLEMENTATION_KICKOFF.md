# AI Factory — Integration-First V1 Implementation Plan

**Status:** Milestone 0 ADMITTED; Milestone 1 first-task proof complete; Milestones 2 and 3 trusted-local demonstrations COMPLETE; Milestone 4 first measurement slice VERIFIED, awaiting owner approval/integration (full Milestone 4, V1 and production gates remain incomplete)

**Adoption decision:** [`../decisions/V1_ADOPTION_ARCHITECTURE.md`](../decisions/V1_ADOPTION_ARCHITECTURE.md)

**Matrix:** [`../decisions/ADOPTION_MATRIX.md`](../decisions/ADOPTION_MATRIX.md)

The open-source adoption spike and Milestone 0 dependency admission are
complete. The owner-maintained `Dzikle/paperclip` fork at `62760ac9` passed
exact-image baseline migration and real Docker/PostgreSQL re-admission on
2026-09-25. V1 remains an integration project, not a greenfield orchestration
project. The owner closed the former upstream PRs; do not submit upstream work
without separate approval. See
[`MILESTONE_0_DEPENDENCY_ADMISSION.md`](MILESTONE_0_DEPENDENCY_ADMISSION.md).

## Delivery order — revised 2026-09-28

The earlier plan made every projection and policy integration a prerequisite
for the first working task. That was too much horizontal infrastructure before
user-visible proof. The dependency decisions and authority boundaries remain;
their implementation order changes. The first reviewed coding task is now
complete; make that loop easy to use before adding breadth.

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| 0 — admit dependencies | **Done** | Pinned Paperclip fork passed migration, crash/security/enrichment, and restore gates. |
| 1 — first runnable task | **Done** | AIF-42 completed Developer → Validator → Reviewer → human approval; AIF-43 survived a native child kill and resumed under a different native adapter. Evidence below. |
| 2 — usable engineering loop | **Local demo complete** | Reusable submission/status commands created AIF-48 and replayed its key; distinct tests, Reviewer, QA and owner approval completed; exact candidate integrated and reverified. |
| 3 — useful memory | **Local demo complete** | Real scoped memory informed AIF-49's deterministic checker; native tests, Reviewer, QA and actual owner approval completed; exact candidate integrated, merged checks and isolated Git rollback/reapply passed. |
| 4 — measure and operate | **Later** | Compare accepted-task quality/cost against a baseline; run bounded failure/rollback drills and promote improvements only through review. |

Every milestone must end with a runnable demonstration and recorded acceptance
evidence. Do not add an index, service, generic adapter, or framework merely to
complete a checklist; add it when the next demonstration needs it. A blocked
dependency is reported as a blocker, not disguised with a second authority or
an admin credential in the runtime. The current architecture remains the V1
target, but its full breadth is not the gate for the **first** useful task.

**Current owner decision — functionality first (2026-09-28):** Use the existing
Paperclip task/run ledger and native adapters, not a replacement engine. The
next bounded feature is a small task submission/status command reusing the
existing engineering execution policy. No new Docker build or framework is
required. Additional runner isolation, generic capability compilation, broad
event projections, image slimming and new fault/restore drills are deferred
until demonstrated need or production rollout. Known isolation gaps remain
documented; deferral is not a PASS. Keep credential containment, scoped MCP,
independent tests/review and explicit human integration approval. Enable only
agents selected for an actual task; the other admission fixtures stay paused.

## 1. Non-negotiable implementation boundaries

- Admitted Paperclip is the only operational task/run/workspace/MCP-policy
  authority. Pin the exact owner-fork revision, image ID and schema in the lock.
- Do not add DBOS or an AI Factory task database beside Paperclip.
- Git owns canonical docs, policy definitions, project overlays, evals, and Agent
  Skills packages.
- MemPalace is the only experiential-memory authority. OpenSearch receives a
  projection; OpenSearch Agentic Memory is not run concurrently.
- OpenSearch is disposable/rebuildable and never the workflow source of truth.
- Paperclip's governed MCP gateway is the V1 runtime/security layer. Do not add
  ToolHive unless its documented re-entry trigger is met.
- Paperclip's workspace and sandbox-provider contract owns execution lifecycle.
  SWE-ReX may later implement that provider contract; it may not own task state.
- CodeGraphContext is the single selected graph candidate, but current V1
  enablement is deferred pending compatible protobuf remediation/re-audit.
- LiteLLM's MIT core Router serves raw API model calls only. Its current server
  proxy extra is not admitted under the open-source decision. Native
  Codex/Claude/OpenCode/etc. runtimes use Paperclip adapters directly.
- Permissions are enforced by runtime credentials and Paperclip MCP profiles,
  never by prompt or Agent Skills `allowed-tools` text.
- Reviewer and QA are separate logical agents and policy participants; an
  implementer cannot self-approve.
- V1 may propose improvements. It cannot autonomously change canonical code,
  skills, policies, models, permissions, or deployment configuration.

## 2. Target package/integration seams

Names are descriptive; preserve boundaries even if the eventual repository
layout differs.

| Seam | Responsibility | Explicit non-responsibility |
| --- | --- | --- |
| `control-paperclip` | Paperclip client/plugin/launcher integration, status mapping, fault-test helpers | No task tables, scheduler, queue, or retry engine |
| `context-resolver` | Query plan, ranking, dedupe, provenance, freshness, source verification, hard context budget | No canonical storage or free-form index writes |
| `projection-opensearch` | Versioned mappings/aliases, idempotent projectors, replay/reconciliation | No workflow decisions |
| `knowledge-mcp-adapter` | Logical names, fixed aliases, source filters, bounded result shape | No replacement OpenSearch MCP server |
| `skills-policy` | Agent Skills validation, sidecar schema, role/capability/eval checks, Paperclip sync | No competing skill format or authorization engine |
| `capability-compiler` | Intersect role + skill + project + task policy and materialize Paperclip profiles/grants | No prompt-only grants |
| `codegraph-adapter` | Revision-aware bounded symbol/caller/dependency/affected-path operations and symbol projection | No parser/graph implementation |
| `memory-adapter` | MemPalace scoping, provenance, supersession, retention, projection, promotion proposals | No task/logstream/artifact authority |
| `model-routing` | Task/risk/eval-based runtime selection and LiteLLM API adapter | No provider-specific task state |
| `quality-evals` | Deterministic checks, Reviewer/QA contracts, scorecards, promotion/rollback gates | No autonomous canonical mutation |

## 3. Milestone 0 — dependency admission gates

This gate passed before production feature code began.

**Historical execution result (2026-09-15): BLOCKED.** Paperclip `5282cab` leaked an active
ephemeral environment lease after controller loss, and the public external
adapter could not enrich and then delegate to a registered native adapter in the
same run. Milestone 0B (2026-09-17) prepared/tested minimal fixes for recorded
host leases and an optional plugin enrichment hook. On 2026-09-23 the owner
chose to maintain both in `Dzikle/paperclip`. The exact fork image,
baseline-database migration, and full real re-admission passed on 2026-09-25;
sections 4–8 are now eligible to begin. This report did not implement them.

### 0.1 Pin and deploy Paperclip

1. Choose a supported container/server deployment and pin a commit/release plus
   image digest. Do not use a floating tag.
2. Configure durable PostgreSQL/PGlite, storage, secrets, backups, and health
   checks. Record schema/export/restore commands.
3. Create representative Developer, Reviewer, and QA logical agents whose
   identities remain unchanged while model/runtime bindings change.
4. Prove create → claim → workspace → finite run → persist → restart → reconcile
   → resume/reinvoke. Kill the model process and Paperclip process at controlled
   points.
5. Fault-inject stale checkout/execution owners, duplicate wakeups, silent output,
   review handoff, MCP token/session expiry, and projection redelivery. Assert one
   workspace writer and no lost task/side effect.
6. Reproduce or close the upstream issues listed in ADR 001 for the pinned build.
   Block admission on any correctness failure; upstream a fix rather than carrying
   a private fork.

### 0.2 Prove the pre-run seam

Use the proposed optional plugin enrichment stage (do not duplicate adapters):

```text
Paperclip creates/claims run
→ resolve placeholder bounded context
→ persist context artifact + digest/sources/budget in contextSnapshot
→ delegate to one native adapter
→ persist result
```

It passes only if no duplicate run state is needed. The owner-approved narrow
Paperclip fork carries the general pre-run hook; hold V1 feature implementation
until the exact fork image passes re-admission.

Baseline external wrapper failed. Milestone 0B's plugin hook persists a bounded
artifact reference/digest before the original selected native adapter dispatch
in the same run. The placeholder native process consumes those bytes; restart
checks the same durable digest. Do not implement the real Context Resolver
until the owner-fork revision is admitted.

### 0.3 Admit the data providers

- OpenSearch 3.8.x: pin image/digest, create dedicated cluster, versioned aliases,
  read-only agent account and write-only projector account; prove delete/rebuild.
- Official OpenSearch MCP 0.11.0: fixed single-cluster mode, explicit read tool
  allowlist, no Generic API, no dynamic credentials; verify server and Paperclip
  deny paths plus hard result limits.
- CodeGraphContext 0.6.13: use a pinned Linux container/backend; measure cold and
  one-file incremental indexing plus callers/dependencies on representative
  Java/Spring, TypeScript, and Go fixtures. Do not admit the failed Windows
  embedded profile.
- MemPalace 3.9.0: one-writer/team-hub profile, destructive sync disabled,
  concurrent-write/restart/export/backup/restore test, and scoped MCP grants.
- LiteLLM 1.102.0: provider contract test for one API agent, bounded call fallback,
  error mapping and usage reconciliation. Use the MIT core Router; the server
  `proxy` extra is not admitted as open source. Do not route a native harness
  through it.

Data-provider result: OpenSearch/MCP, MemPalace, CodeGraphContext, Agent Skills,
and LiteLLM core passed their bounded mechanics tests with the exact caveats in
the Milestone 0 report. CodeGraphContext's V1 enablement remains deferred by
its security gate; this does not reinstate the resolved Paperclip blocker.

Milestone 0B narrows that result: real offline MemPalace embedding readiness now
passes; LiteLLM's final V1 shape is embedded MIT core Router only (licensed proxy
DEFERRED); CodeGraphContext's current image is disabled until its mandatory
protobuf/bindings and runtime dependency security gates pass. No additional
memory, graph, gateway, scheduler, or workflow authority is introduced.

Milestone 0 exit evidence is committed in the pinned dependency manifest,
license/adoption decisions, POC/admission report, issue disposition, and
rollback record. Mandatory Paperclip correctness and seam gates passed on the
exact owner-fork image. Owner-controlled registry publication is required
before deployment beyond the validated local host.

## 4. Milestone 1 — first runnable engineering task

**Ready:** Milestone 0 is ADMITTED. Sections 1.1–1.3 record useful foundation
already built. Continue directly to the single-task slice in 1.4; do not finish
the entire projection catalog first.

**1.1 contract status (2026-09-25):** Initial versioned schemas and synthetic
boundary tests now cover the listed Git contract classes. The first slice
defined project overlays, Agent Skills sidecars, logical capabilities, and
deny-default role policy; the second added task scoping, context/provenance/
budgets, normalized events, memory/promotion, model policy, and validation/
review outcomes. Offline cross-field checks reject unavailable capabilities,
cross-project context, and self-review claims. These are not active Paperclip
grants or a real Context Resolver, and provider event-shape compatibility is
not yet proven. Section 1.2's policy mapping has since been live-probed and
1.3's first Git-documents projection passes a local OpenSearch proof. No real
coding task has passed the full loop. Milestone 1 is not complete.

### 1.1 Canonical Git contracts

Commit versioned schemas for:

- project overlays and canonical-source precedence;
- Agent Skills `ai-factory.yaml` sidecars;
- logical capability definitions and role/project/task intersections;
- context query plan, provenance envelope, per-domain and total budgets;
- normalized task/run/review/QA/telemetry events;
- memory provenance/supersession/retention and promotion proposals;
- model selection/fallback/escalation policy;
- deterministic validation and independent review outcomes.

These schemas describe integration data. They must not become a second task or
MCP permission store.

### 1.2 Paperclip policy templates

Materialize the first engineering execution policy:

```text
Developer implementation
→ deterministic validation
→ independent Reviewer
→ conditional independent QA/UX
→ integration approval
```

Use distinct logical agent IDs, read-oriented Reviewer/QA profiles, explicit
return-to-implementation transitions, and no-self-approval checks.

**1.2 policy mapping verified (2026-09-25, fork `62760ac`):**
`milestone1/paperclip_policy.py` creates one native `IssueExecutionPolicy` at
issue creation. Developer is the issue assignee, not a review stage. The first
`review` participant is a deterministic validator process, the next is a
separate Reviewer, optional QA/UX is another `review` participant, and the
last `approval` participant is a board user. The template rejects shared
Developer/validator/Reviewer/QA IDs and caps unattended changes-requested
rounds at three. Paperclip alone owns assignment, stage state, decisions,
comments, retries and human escalation; AI Factory stores no duplicate task
state. Do not reapply a freshly generated policy in the middle of a review:
Paperclip generates stage IDs at creation and a mid-flow edit can change them.

Live policy probes against the admitted Docker/PostgreSQL fork image:

| Gate | Evidence | Result |
| --- | --- | --- |
| Validation → Reviewer → QA → board approval stage | Issue `d0d3b3b3-e5ea-4a3c-b103-65a8094f0fe9` | Four distinct issue-bound agent runs in policy order; held at the board-user stage, then a **simulated board-key approval** completed it. No physical human approval was performed. |
| QA omitted | Issue `8c977c53-bf47-4ac1-88ac-fef30145073c` | Three distinct issue-bound runs; no QA stage or agent; final approval simulated with a board key. |
| Failed deterministic check | Issue `9628e0e4-f2b9-4b2b-a30e-5534755249f2` | Three failed checks returned to Developer (two resubmissions), then Paperclip escalated to a board user; Reviewer/QA received no issue-bound runs. Disposable issue cancelled after proof. |
| Reviewer/QA external access | Passing issue probe | Fresh agents had no external MCP grants. This safe routing probe does not alter the shared Milestone 0 connection/install list. A separate earlier exploratory run successfully configured `SearchIndexTool`-only effective profiles, but native Reviewer/QA runtime delivery remains for the real vertical slice. |
| Evidence integrity | Passing issue probe | Validation comment linked to its run and `file:///paperclip/...` artifact; container bytes matched SHA-256 and artifact fields matched issue, run, agent, target hash, exit code, and verdict. |

The two process-fixture scripts are **not** a production engineering workflow
pack. The validator only runs `node --check` on a mounted fixture; Reviewer/QA
fixtures make synthetic approvals rather than reviewing code. Artifact bytes
live in the disposable Paperclip test volume and are referenced by comments;
production artifact registration, real checks and real independent judgment
belong to the later vertical slice. Paperclip can mark a run `cancelled` when
that run's own issue update reassigns the issue; the durable execution decision
and issue state, not a simplistic run-success count, prove a stage advanced.
The process adapter's connection-intent broker is **not** the native named MCP
gateway. The repeatable probes assert deny-default effective profiles; the
exact native search-only gateway allow/deny behavior was separately proved in
Milestone 0, not by the process fixture. Reviewer native-adapter grants need
rechecking in Milestone 1; QA grants in Milestone 2. All probe agents are
paused in a `finally` block; failed fixtures are cancelled when possible and
cleanup errors are recorded. The probe checks the running image ID against
the admitted dependency lock before mutating test state. It does not repeat
the Milestone 0 database migration/schema admission.

Repeat focused checks:

```powershell
node --test milestone0/fixtures/paperclip/validation-agent.test.mjs
uv run --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m unittest discover -s tests -q
python -m milestone1.paperclip_policy_probe
$env:AIF_M1_INCLUDE_QA='0'; python -m milestone1.paperclip_policy_probe
python -m milestone1.paperclip_policy_failure_probe
```

The live probes require the ignored local Milestone 0 readmission state file,
the exact admitted Paperclip image, and its disposable Docker/PostgreSQL
environment; they are not CI tests.

### 1.3 OpenSearch projection foundation

**First Git-documents slice implemented (2026-09-25; broader projections moved
to later milestones):** `milestone1/git_projection.py` reads only committed
blobs from a project overlay's canonical paths. It emits stable per-path IDs,
Git commit and blob versions, SHA-256, status and source provenance. Full-snapshot
reconciliation upserts changes and marks removed paths stale; replay of an
unchanged snapshot issues no writes. `milestone1/opensearch_projection.py`
installs a strict `ai_factory_docs_v1` mapping with stable read/write aliases,
uses separate read/write clients, filters reconciliation to one project/repo,
and fails on malformed reads or failed bulk items. The live smoke against the
pinned local OpenSearch 3.8.0 cluster indexed the committed overlay documents,
then observed zero writes on replay and verified a retrieved Git revision and
content digest. A guarded delete/recreate/rebuild of only the verified
`ai_factory_docs_v1` test index restored the same document count from Git.
The first live smoke used the local test admin credential. A subsequent live
OpenSearch Security probe used temporary independent reader/writer principals
from `milestone1/opensearch_security.py`: allowed bulk indexing and filtered
search worked through the aliases, unchanged replay issued zero writes, and
forbidden read/write/admin/delete actions returned 403 (including writes to an
out-of-scope index and bulk delete). The reader has search only; the writer
has bulk/index only. Security checks require the underlying physical index in
each role even when the client uses an alias; the `_bulk` entry point requires
its cluster action. The test did not alter the Milestone 0 principals and
cleaned up its temporary users, roles and out-of-scope probe index. This proves
effective local permissions, **not** production credential provisioning or
scheduling. Git full scans are the replay/reconciliation mechanism for this
slice, not a second authoritative cursor. No Context Resolver or workflow was
implemented.

**For the first task:** use separate non-admin local reader/writer credentials
and a single serialized invocation of the existing Git-doc projector. Do not
build a generic projector scheduler. The runtime uses the read-only OpenSearch
MCP profile; administrator credentials are limited to setup/verification.

The full projection catalog is **not** a Milestone 1 gate. Add each source
when a runnable milestone consumes it:

```text
Git docs/ADRs/project overlays (first slice active)
Agent Skills/capability metadata
Paperclip tasks/runs/reviews/QA/costs/approvals/MCP audit
MemPalace memories and temporal status
CodeGraphContext symbol pointers
artifact metadata
```

For each activated source use deterministic IDs, source revision/version,
staleness or supersession, and source reconciliation. Event-driven sources need
durable replay/dead-letter evidence when introduced. Projection failure never
rolls back valid source state. An unactivated source needs no V1 index merely
to satisfy the diagram. CodeGraphContext stays disabled until its separate
security gate passes.

### 1.4 First runnable task — next implementation work

The first issue is a useful missing operation in this repository: add a
single-run Git-documents projection command in `milestone1/project_git_docs.py`
with `tests/test_project_git_docs.py`. It should call the existing snapshot and
reconciliation functions, accept the project overlay, require separate
non-admin reader/writer credentials, never install or administer an index, and
return a failing exit status on invalid input or projection failure. A second
run at the same Git revision must issue zero writes. The initial index can be
seeded by an explicit serialized invocation of existing code; the new command
is the real agent's coding task, not a synthetic approval fixture.

Run this issue in an isolated Paperclip worktree. Keep integration/merge and
final approval with the human; the earlier simulated board-key approval is
not production acceptance. Use Paperclip's native Codex adapter and the local
Codex CLI for this first slice; verify the adapter is available in the actual
Paperclip runtime before starting. Do not build model routing or wrapper
adapters. The initial task must not require QA/UX, memory, or code-graph access.

Build only the path the task exercises:

1. Create the Paperclip issue with the existing distinct Developer, validation,
   and Reviewer policy. Record a failing test for missing command behavior in
   the task branch before implementing it; then require a green replay test.
2. Project the relevant committed Git docs through the existing alias with a
   serialized run and non-admin credentials. Verify search returns the intended
   project/repository and current Git revision.
3. Use the admitted pre-run hook to perform one governed, filtered OpenSearch
   lookup. Verify selected canonical text against Git, enforce a hard total and
   per-source byte/token budget, and persist a context artifact reference and
   SHA-256 in the same run snapshot. Missing permissions, stale source, invalid
   digest, or budget overflow fail closed before native dispatch.
4. Dispatch the original native Developer adapter in Paperclip's assigned
   worktree. Run deterministic validation, then a different logical Reviewer
   with a read-oriented effective MCP profile. No implementer self-approval.
5. Record run ID, agent IDs, selected adapter, workspace/ref, context artifact
   digest, test and review results, and native cost/usage where available.
   Interrupt one active run, reconcile/resume it, and verify one task writer and
   durable, Git-verified context lineage without the original chat.

Show two checkpoints: **(A)** one complete Developer → validation → Reviewer
handoff with visible artifacts; **(B)** the same task class survives an
interruption. Milestone 1 exits only when both checkpoints pass on the pinned
Paperclip image with effective permissions observed at runtime. A process-only
fixture or configured policy without a native coding run does not count.

Current first-task progress (2026-09-26; **both checkpoints passed with the
artifact-lineage clarification below**):

- **A — reviewed task.** AIF-42's native Codex Developer run `71c101aa` wrote
  the command guard and tests in its isolated SSH worktree. Provider quota
  stopped the run before commit, so the operator verified and committed the
  two files as `d415175`; Paperclip Validator `8967c4e4` passed 8 tests and
  recorded artifact SHA-256 `1090fb98414f0890098296058c37ba8ac9d2d709ae8fa65b5aeeb3ca0ac4e7b8`.
  Independent Reviewer `fae9caca` approved its stage. The human approved the
  final Paperclip stage, leaving AIF-42 `done`; local merge `26237e5` placed
  the reviewed change on `milestone1-contracts`. The Developer's context
  artifact SHA-256 `0fcd5632b93828a55f24ac369561ffb176a32d54a85a25c15da892d13342eb20`
  matched stored bytes. Operator commit/handoff is explicit, not claimed as
  autonomous agent completion.
- **B — real native interruption.** AIF-43 used the same Git-documents task
  class and logical Developer `7a134376-dd89-4006-97bb-eeba855e443d` in
  workspace `890a248a-304a-48f5-ba17-e35bcd9d1269`. Codex run
  `b94304ba-0fb5-46ca-bbad-96e9b9410140` edited the two allowlisted files;
  its Codex child was killed. Paperclip terminalized the run and restored the
  exact two-file diff. The run's context artifact (3,542 bytes) at
  `file:///paperclip/milestone1-context/b94304ba-0fb5-46ca-bbad-96e9b9410140.json`
  retained SHA-256 `b7fe5bf05ee5bfb783de79a9c3a1ce283a8f0b0e8b0ba4be8ab5d06430b56f2a`;
  automatic same-execution retries retained that reference but stopped at a
  Codex-account provider quota. The unused delayed retry was cancelled and
  explicitly reconciled as `not_performed` through Paperclip's recovery API.
  Fresh native OpenCode run `dfb632d6-aa83-42f9-becc-c8956eff940f` then
  resumed the **same issue, logical agent, and Paperclip worktree** with a new
  model session, inspected the restored diff, reran 10/10 tests, made no new
  edits, and marked AIF-43 `done`. All 12 acquired leases have `releasedAt`,
  no run intervals overlap, and checkout/execution locks are clear. Its
  recorded cost was $0 (free model); token counts were 27,821 input and 1,459
  output. The Developer was returned to its original Codex configuration and
  paused after the test.
- **Context-lineage clarification.** A distinct successor execution gets a
  distinct run-scoped artifact ref/digest, not the same literal ref. Run
  `dfb632d6` retained ref
  `file:///paperclip/milestone1-context/dfb632d6-aa83-42f9-becc-c8956eff940f.json`
  and verified SHA-256 `2a40ca0238384926602cb8f5b208b2675279ebbeb197bea77335437fd5829b61`.
  Both artifact byte hashes match their snapshots; their context text and
  source metadata are identical, including canonical source SHA-256
  `3484209e5f92516f38eab66775e4e372e9e34a64d02b6f28180bfd2fde28963d`.
  This is safer than copying a possibly stale prior-run artifact blindly:
  same-run retries preserve the original ref, while a new run must reverify
  Git and persist its own provenance. No original conversation was supplied.
- **Validation and limits.** The local full suite passes 52 tests (two
  expected opt-in skips); the context fixture passes 10 tests. Live one-shot
  OpenSearch projection at `26237e5` wrote 49 canonical documents, then zero
  on guarded replay with separate non-admin credentials. Paperclip's effective
  external profile is deny-default with only `SearchIndexTool`. At this
  Milestone 1 checkpoint the host MCP process was not yet supervised; the
  Milestone 2 slice below replaces it. Native Codex's copied home still contains
  stale MCP stanzas with ignored headers. Narrow those before claiming a
  repeatable production runtime. The trusted-only runner still has an isolated
  `seccomp=unconfined` exception; it is not approved for untrusted repositories.

## 5. Milestone 2 — usable, repeatable engineering loop

**First reliability slice, 2026-09-26:** The official OpenSearch MCP server
`0.11.0`/`fcb23ec` now runs from pinned source and `uv.lock` in a supervised
Docker container, local image ID
`sha256:c47f67f75b31370868424a9176784f8cf212d293507e70467911a2c9736cc4a8`.
Its direct catalog is exactly `ListIndexTool`, `IndexMappingTool`,
`SearchIndexTool`, and `MsearchTool`; a killed server child restarted and
recovered real searches. Paperclip connection
`34e29b2e-e5f2-455e-ab47-b1187eb38537` has the same exact catalog.
Developer, Reviewer, and the admission seam probe have one installed
connection and only `SearchIndexTool` effective. Run
`0d5050af-e948-4c75-a31b-054c9e7b856f` proved a governed search 200 and
ungranted multi-search 403/`deny_default`; after reader-secret rotation and
another MCP restart, `c60ea56e-4f8e-488c-b548-abb940753efc` repeated it.
The old unsupervised host process
was stopped and its stale-catalog connection disabled; its remaining 19
installed agents are paused test fixtures, not active workflow agents.

The MCP reader role now covers the active `ai_factory_docs` alias and older
admission alias without write actions. Direct live checks returned search 200,
write 403. Its formerly shared admin password was rotated; the old password
for `aif_agent` now returns 401. The local self-signed cluster still disables
TLS verification; production needs a trusted CA and secret store. Generic Paperclip
catalog refresh did not retire removed tools, so this transition required a
fresh connection and explicit removal of auto-generated broad grants. The
reproducible deployment and test commands are in [`milestone2/README.md`](../../milestone2/README.md).
This completes **one Milestone 2 reliability slice**, not the Milestone 2 exit.
Next: clean native harness MCP entries, make Git handoff repeatable, then run
the second independently accepted task with conditional QA evidence.

**Native-catalog hardening deployed; final probe quota-blocked, 2026-09-27:** The owner Paperclip fork
commit `c2f23c81` corrects the managed Codex MCP header key to `http_headers`;
focused red/green test, adapter typecheck, and independent Codex CLI parsing
support it. Fork commit `d57c0b7c` also fixes GHCR naming for a mixed-case
owner; its normal Linux production-image workflow passed at immutable digest
`sha256:95f6708217d9b34b10c9a3637d024e121a2bdaf6fa0008eb3fca5983b80f1676`.
After a paired PostgreSQL/storage backup, this immutable image replaced the
local controller without replacing its volumes or changing its 283-row migration
journal. Linux adapter tests passed 53/53. The new native run regenerated the
Codex home: exactly three intended servers with recognized bearer headers;
the five stale entries disappeared without manual edits. MCP child-crash
recovery and effective search-only profiles passed again.

Read-only AIF-44 required fast-forwarding its clean probe worktree to the
already-indexed Git source because the project template's remote ref was stale.
Run `6f410fba-5852-4835-9722-a4df0e02ff30` then persisted verified context,
synced the home, and launched native Codex over SSH, but stopped with
`provider_quota` before a model-initiated search. Its artifact digest and terminal
lease release receipt survived controller restart. AIF-44 is blocked and the
Developer paused; retries are cancelled. The active candidate is recorded
separately from the unchanged Milestone 0 admitted/rollback pin. Resume the same
probe after quota becomes available; **do not count this as the native-search
gate or Milestone 2 exit**. See [`milestone2/README.md`](../../milestone2/README.md)
for backup hashes, exact versions, run evidence and remaining gates.

**Git handoff guard implemented, 2026-09-27:** Work continues independently of
the Codex quota. The Paperclip source checkout now fetches the owner GitHub
repository instead of its stale offline bundle; the native worktree policy is
unchanged. A newly created diagnostic worktree resolved the published source
commit without moving existing branches. The Git-doc Validator now rejects
dirty/wrong-branch handoffs, tests an isolated copy of the recorded commit,
checks for drift afterward, and records commit/tree identities for the separate
Reviewer. Nine real-process container integration cases and 28 Node tests
pass, including an outside edit/restore during testing. Runtime fixtures are
updated; live AIF-46 Validator smoke passed 10/10 tests with persisted commit/tree
evidence and clear locks. These are deterministic handoff safeguards, not a second accepted
native task or final merge enforcement; human integration remains required.
See [`milestone2/README.md`](../../milestone2/README.md) for precise evidence and
the remaining native-search/conditional-QA gates.

Start from the **working Milestone 1 task**, not a second greenfield workflow.
**Second task accepted and integrated (2026-09-27):** AIF-47 adds read-only
projection preview. Native OpenCode Developer and separate Reviewer, the existing
Validator, and independent functional CLI QA all recorded evidence for commit
`43a379add55538cdf8a2e3e87e5c7c25d045e28a`. The owner explicitly approved that
commit; Paperclip decision `172a5c0f-f97b-423e-bf76-4f4dba0c9047` completed the
human stage and issue. Merge `52dee7fa2d1d8b298dff8e43a56bca010fa4f558` integrates
it into `milestone1-contracts`. Post-merge validation: 59 Python tests run
(57 passed, two opt-in live skips), six independent QA cases and 29 Node tests
passed. Real reader-only previews exercised both unchanged and pending-refresh
states without writes. This closes the second accepted task and conditional
functional-QA slice, not all Milestone 2 gates. Launch fixes use verified Git text after
metadata-only governed retrieval and task-specific native OpenCode `--dir`;
they do not close the native Codex quota gate or generic runtime binding work.
See [`milestone2/README.md`](../../milestone2/README.md) for exact runs, artifacts,
limitations and the completed human approval stage.

**OpenCode directory binding and native-child credential containment deployed
(2026-09-28):** Owner-fork `6f19a0d07f02fdaaca4085b07bb32b3f7b260383` includes
the `379fe383` directory correction and a closed inherited-environment allowlist;
explicit run/project/provider bindings remain supported. Its normal published
image is pinned in the dependency lock and Compose override. Exact-image focused
tests pass 97/97, and real OpenCode 1.18.33 verifies task-directory binding and
secret-free child environments without inference. The exposed database password
was rotated with paired backups; the old credential fails SCRAM authentication,
the new one works, authoritative record hashes/schema are unchanged, and live
effective MCP checks pass. All six AIF-47 context artifacts still match their
stored hashes; the issue stays accepted and unlocked. This is environment/config
containment, not filesystem or hostile-code isolation. All agents remain paused
pending the relevant execution/access-boundary verification before their next
task. The Codex search probe is still quota-blocked and Milestone 2 is not complete.
See [`milestone2/README.md`](../../milestone2/README.md) for evidence and limitations.

The 2026-09-28 functionality-first decision supersedes the earlier requirement
to finish every hardening item before another local task. Immediate acceptance:
submit a task with the existing independent stages, show authoritative progress,
and run useful work without hand-written orchestration per task. The following
broader integrations remain the longer-term backlog, not prerequisites for that
trusted local demonstration:

1. Validate and sync the applicable Agent Skills packages. Compile the
   role/project/task/skill capability intersection into Paperclip MCP profiles;
   missing capabilities block, and effective catalogs—not configuration alone—
   prove deny-default access for Developer, Reviewer, and conditional QA.
2. **Completed for CLI functional QA by accepted AIF-47.** Add independent UX
   checks when a UI task genuinely requires them. Reuse the
   Paperclip execution policy; keep Developer, Reviewer, and QA as distinct
   logical agents with separate evidence and no self-approval.
3. Project Paperclip task/run/review/cost/artifact metadata needed for task
   history. Give these event-driven projectors durable replay/dead-letter and
   reconciliation behavior without making OpenSearch authoritative. Add skill/
   capability metadata only when the Resolver queries it. Keep one serialized
   writer per index/alias; do not add a separate scheduler or task database.
4. Broaden the Resolver from current Git docs to active decisions and related
   task/review history. Use filtered bounded queries, original-source checks,
   provenance/freshness labels, and one persisted context package. Do not wait
   for CodeGraphContext; while disabled, use Git and language-native search.
5. Repeat the same task class after controller loss and a native model/runtime
   binding change. Restore Paperclip plus artifact storage, delete/rebuild each
   **active** OpenSearch index from its named authority, and prove a duplicate
   event changes no document identity or task state.

Milestone 2 local-demo exit: reusable submission/progress commands and a useful
task through distinct Developer, tests, Reviewer, optional QA and human approval.
AIF-47 supplies the prior independent task/QA evidence. Full production
restore/rebuild, expanded catalogs and additional isolation remain deferred;
the local milestone does not claim production readiness.

**Local-demo acceptance (2026-09-28):** Existing services are running; the thin
submission/status CLI created AIF-48 and replayed its key without duplication.
Candidate `36bc6cc293f8e99b21c742858d05df7933ff4896` adds usable projection help;
fresh deterministic tests, independent Reviewer and six functional QA checks
passed on that same commit/tree. The owner explicitly approved AIF-48; native
decision `9b75e70e-1af8-477e-b488-52bbbe7603fa` completed all 4 stages and the
issue, with clear locks. Merge `b78b4c53e7808aab414dee2817a5c8a850dce69a`
integrates the exact candidate. Fresh merged verification: 72 Python tests run
(70 passed, two opt-in live skips), 6/6 independent functional QA checks and
26/26 context/handoff/identity Node tests. Artifact identities were independently
rechecked before approval. Source-ref, instruction-reread and test-library issues
were corrected without new infrastructure. Recovery of a cancelled handoff
needed explicit receipt reconciliation; its return-assignee/telemetry limitation
is recorded in [`milestone2/README.md`](../../milestone2/README.md). This closes
the revised trusted-local Milestone 2 exit, not unattended correction-loop,
native Codex quota, production isolation, or expanded projection/restore gates.
Milestone 3 may now start with one reviewed experiential-memory lesson; no
memory implementation was added by this integration.

## 6. Milestone 3 — experiential memory loop

**Current implementation:** [`../../milestone3/README.md`](../../milestone3/README.md)
records the first supervised slice. One real AIF-47/AIF-48 dependency-environment
lesson is held in the existing production MemPalace service; only metadata is
projected into the existing OpenSearch docs mapping. Primary status, current
Git bytes, exact owner-approved source decision, scope and retention are checked
before at most one 2,400-byte historical prompt is prepared. Real dependency-loss
tests degrade to no advice without modifying Paperclip task state. This is not
an automatic per-run freshness guarantee or a complete Context Resolver. The
native follow-up AIF-49 produced candidate `68344b66` and passed 100 tests
(98 passed/two skipped), full foundation/promotion re-review and 3/3 functional
QA. Actual controller restart preserved the task/run context and artifact digests.
The owner explicitly approved it on 2026-09-29; Paperclip records `done`, 4/4
gates, decision `ca59d628-e234-4314-bda2-7ec4b4855e2f`, with clear locks. Integration
`a46ec83bb2788b5d6cb297b7fd3004792f2c90ce` retains the original candidate on
`milestone1-contracts`. Fresh merged checks passed: 100 Python tests (two skips),
3 CLI QA checks and 26 Node regressions. Isolated Git revert/reapply matched exact
prior/accepted trees; the reapplied checker passed again. Rollback commands and
scope are recorded in the existing Milestone 3 report. This completes only the
supervised trusted-local demonstration; Milestone 4's separately approved measurement slice is now in progress.
Provider usage/cost is unavailable on cancelled handoff runs; the 314-token
memory estimate is context sizing, not a billed-model metric.

Add memory only after the engineering loop runs without it. Begin with **one**
real, reviewed lesson from a completed task or incident, not seven simulated
memories as a deployment gate. Keep MemPalace as the sole memory authority and
project only what the Resolver needs into OpenSearch. On a later task, prove
project/role scoping, source provenance, retrieval use, token cost, and that a
superseded memory cannot override current Git. A source lookup or memory
backend failure must degrade safely without changing task truth.

Then capture a repeated pattern and demonstrate one reviewed promotion:

```text
experience
→ repeated pattern with source evidence
→ reviewed Agent Skill or deterministic check in Git
→ eval
→ approval
→ versioned rollout/rollback
```

No automatic write to canonical Git is allowed in V1.

Use the seven adoption scenarios as later regression/evaluation cases, not as
prerequisites for the first task or first useful memory.

## 7. Milestone 4 — measurable improvement and bounded operations

**Current bounded slice (owner-approved 2026-09-29):**
[`../../milestone4/README.md`](../../milestone4/README.md). Read native task
quality/timing/usage through the existing CLI and run one serial pair of the
same small formatter task, with/without one verified memory lesson. No new
containers, stores or evaluation platform. Native Tests → Reviewer → QA → owner
gates remain required; candidate integration is not approved by scope approval.
Missing telemetry stays unknown. Both trials retain ordinary repository access
and canonical Git enrichment; only experiential advice differs. A single,
non-randomized pair cannot establish general improvement or savings.

AIF-50/AIF-51 each ran 133 Python tests (131 passed/two optional live skips),
passed independent Reviewer assessment and 9/9 presentation QA; both are 3/4 at the owner gate.
The memory trial added 1,254 description bytes and used 311.160 s active native
runtime versus 226.396 s for baseline; the baseline wall window includes a
supervised evaluator-correction hold. No causal speed/cost benefit is proven;
tokens/cost have zero covered runs and remain unknown. Recommend AIF-50's
smaller formatter, subject to explicit owner approval before accepted integration.

The broader items below remain backlog/exit criteria, **not work added to this
first slice**:

- Build retrieval query sets/judgments/experiments in OpenSearch Search Relevance
  Workbench and keep expected outcomes/promotion thresholds in Git.
- Project Paperclip native telemetry and calculate cost/latency/tokens per
  accepted correct task, first-pass review/QA rate, escaped defects, recovery
  success, duplicate effects, context size/use, stale-memory rejection, and
  model/skill version correlations.
- Implement bounded self-healing actions: retry idempotent reads, restart an MCP
  runtime slot, rebuild a disposable graph/index, rehydrate a workspace, or
  escalate. Every action is policy-constrained and audited.
- Run restore, dependency rollback, OpenSearch rebuild, MemPalace restore, and
  model/provider substitution drills.
- Add Promptfoo, Phoenix, Langfuse, ToolHive, SWE-ReX, DBOS, or another store only
  when a measured gap and the authority boundary are recorded in a new ADR.

Milestone 4 exits with paired runs of the same task class showing accepted
quality, context supplied/used, tokens, latency, and **cost per accepted
correct task** against a no-retrieval or earlier-version baseline. Record
failure drills and rollback evidence; do not claim improvement from cheaper
inference alone.

## 8. V1 completion test

A real coding task must demonstrate:

```text
Paperclip durable task/claim
→ stable logical expert + replaceable model/runtime
→ validated Agent Skills + least-privilege Paperclip MCP profile
→ bounded OpenSearch context with Git verification
→ task worktree/sandbox
→ deterministic checks
→ independent Reviewer
→ independent conditional QA/UX
→ durable outcome/artifacts/telemetry
→ replayable OpenSearch projection
→ forced interruption and model-change recovery
→ later scoped retrieval of the proven experience
```

CodeGraphContext is **not** a V1 completion gate while its security enablement
remains deferred. If it is later admitted, test it as a derived aid, not as code
truth. Conditional QA/UX is exercised by a task class that actually requires
it; the first non-UI task does not need a ceremonial QA stage.

The task fails V1 acceptance if it relies on the original chat, permits duplicate
workflow truth, silently bypasses MCP governance, treats memory/projection as
current truth, or cannot replace any selected dependency through its documented
adapter/restore path.

## 9. Explicit post-V1 deferrals

- autonomous canonical self-modification;
- multi-primary/global Paperclip deployment;
- untrusted multi-tenant hostile-code execution beyond a selected provider;
- ToolHive runtime substrate;
- DBOS control-plane replacement;
- SWE-ReX sandbox-provider implementation;
- OpenSearch Agentic Memory migration;
- E2B or other hosted sandbox;
- Promptfoo/Phoenix/Langfuse;
- more than one code graph;
- automatic memory-to-automation promotion without human review.
