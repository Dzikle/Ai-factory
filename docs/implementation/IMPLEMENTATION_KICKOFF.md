# AI Factory — Integration-First V1 Implementation Plan

**Status:** Milestone 0 ADMITTED; Milestone 1 in progress, first runnable task next (no V1 workflow implemented yet)

**Adoption decision:** [`../decisions/V1_ADOPTION_ARCHITECTURE.md`](../decisions/V1_ADOPTION_ARCHITECTURE.md)

**Matrix:** [`../decisions/ADOPTION_MATRIX.md`](../decisions/ADOPTION_MATRIX.md)

The open-source adoption spike and Milestone 0 dependency admission are
complete. The owner-maintained `Dzikle/paperclip` fork at `62760ac9` passed
exact-image baseline migration and real Docker/PostgreSQL re-admission on
2026-09-25. V1 remains an integration project, not a greenfield orchestration
project. The owner closed the former upstream PRs; do not submit upstream work
without separate approval. See
[`MILESTONE_0_DEPENDENCY_ADMISSION.md`](MILESTONE_0_DEPENDENCY_ADMISSION.md).

## Delivery order — revised 2026-09-25

The earlier plan made every projection and policy integration a prerequisite
for the first working task. That was too much horizontal infrastructure before
user-visible proof. The dependency decisions and authority boundaries remain;
their implementation order changes. **The next deliverable is one real,
reviewed coding task, not another platform-completeness gate.**

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| 0 — admit dependencies | **Done** | Pinned Paperclip fork passed migration, crash/security/enrichment, and restore gates. |
| 1 — first runnable task | **Now** | The Git-documents command issue below goes through Paperclip, bounded Git-doc context, a native Developer, deterministic checks, and a different Reviewer. Show the run/artifacts and one interruption/resume. |
| 2 — harden and broaden | **Later** | Make the working loop repeatable: active-source projections, capability compilation, conditional QA, model-change recovery, and backup/rebuild. |
| 3 — useful memory | **Later** | One proven experience is stored with provenance, retrieved by a later task, and cannot override current Git. |
| 4 — measure and operate | **Later** | Compare accepted-task quality/cost against a baseline; run bounded failure/rollback drills and promote improvements only through review. |

Every milestone must end with a runnable demonstration and recorded acceptance
evidence. Do not add an index, service, generic adapter, or framework merely to
complete a checklist; add it when the next demonstration needs it. A blocked
dependency is reported as a blocker, not disguised with a second authority or
an admin credential in the runtime. The current architecture remains the V1
target, but its full breadth is not the gate for the **first** useful task.

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
   the same durable context reference without the original chat.

Show two checkpoints: **(A)** one complete Developer → validation → Reviewer
handoff with visible artifacts; **(B)** the same task class survives an
interruption. Milestone 1 exits only when both checkpoints pass on the pinned
Paperclip image with effective permissions observed at runtime. A process-only
fixture or configured policy without a native coding run does not count.

## 5. Milestone 2 — repeatable, hardened engineering loop

Start from the **working Milestone 1 task**, not a second greenfield workflow.
Add only capabilities required by a second representative task or a demonstrated
failure of the first:

1. Validate and sync the applicable Agent Skills packages. Compile the
   role/project/task/skill capability intersection into Paperclip MCP profiles;
   missing capabilities block, and effective catalogs—not configuration alone—
   prove deny-default access for Developer, Reviewer, and conditional QA.
2. Add a task class where independent QA/UX is genuinely required. Reuse the
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

Milestone 2 exits with a second accepted task, conditional QA evidence, a
model-change recovery receipt, effective role catalogs, and a successful
restore/rebuild of active projections. No inactive index is a prerequisite.

## 6. Milestone 3 — experiential memory loop

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
