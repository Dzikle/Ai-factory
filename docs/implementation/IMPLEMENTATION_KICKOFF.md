# AI Factory — Integration-First V1 Implementation Plan

**Status:** Milestone 0 Paperclip gate ADMITTED; Milestone 1 may start (no V1 workflow implemented yet)

**Adoption decision:** [`../decisions/V1_ADOPTION_ARCHITECTURE.md`](../decisions/V1_ADOPTION_ARCHITECTURE.md)

**Matrix:** [`../decisions/ADOPTION_MATRIX.md`](../decisions/ADOPTION_MATRIX.md)

The open-source adoption spike and Milestone 0 dependency admission are
complete. The owner-maintained `Dzikle/paperclip` fork at `62760ac9` passed
exact-image baseline migration and real Docker/PostgreSQL re-admission on
2026-09-25. V1 remains an integration project, not a greenfield orchestration
project. The owner closed the former upstream PRs; do not submit upstream work
without separate approval. See
[`MILESTONE_0_DEPENDENCY_ADMISSION.md`](MILESTONE_0_DEPENDENCY_ADMISSION.md).

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

## 4. Milestone 1 — contracts, policy, and projections

**Ready:** Milestone 0 status is ADMITTED. Begin with contracts/policy and
projection boundaries; do not infer permission to implement all later V1
workflows at once.

**1.1 contract status (2026-09-25):** Initial versioned schemas and synthetic
boundary tests now cover the listed Git contract classes. The first slice
defined project overlays, Agent Skills sidecars, logical capabilities, and
deny-default role policy; the second added task scoping, context/provenance/
budgets, normalized events, memory/promotion, model policy, and validation/
review outcomes. Offline cross-field checks reject unavailable capabilities,
cross-project context, and self-review claims. These are not active Paperclip
grants or a real Context Resolver, and provider event-shape compatibility is
not yet proven. Section 1.2's policy mapping has since been live-probed below;
1.3 remains unimplemented. Milestone 1 is not complete.

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
Milestone 0, not by the process fixture. Reviewer/QA native-adapter runtime
grants need rechecking in the real Milestone 2 slice. All probe agents are
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

Implement versioned mappings/aliases and idempotent projectors for:

```text
Git docs/ADRs/project overlays
Agent Skills/capability metadata
Paperclip tasks/runs/reviews/QA/costs/approvals/MCP audit
MemPalace memories and temporal status
CodeGraphContext symbol pointers
artifact metadata
```

Use deterministic document IDs, source revision/version, tombstones or
supersession, replay cursor, dead-letter evidence, and periodic source
reconciliation. Projection failure never rolls back valid source state.

Milestone 1 exits when every index can be deleted and rebuilt from its named
authority and a duplicate event produces no duplicate document.

## 5. Milestone 2 — Context Resolver vertical slice

Implement one task class against one real repository.

1. Paperclip claims a code-change task atomically and binds a worktree.
2. Role/project/task policy selects the `repository-discovery` and appropriate
   implementation/review skills.
3. Capability compiler materializes a least-privilege Paperclip profile. A
   missing required capability blocks rather than widens access.
4. Context Resolver issues separate bounded OpenSearch searches for canonical
   docs, active decisions, relevant history, similar tasks/reviews, capability/
   skill metadata, and code symbols.
5. It optionally expands selected memories and graph relationships, verifies
   source claims in Git, filters superseded/stale records, and writes one bounded
   context-package artifact.
6. A native Developer adapter works only inside the assigned worktree.
7. Deterministic repository checks run and become artifacts/evidence.
8. A separate Reviewer receives task, diff, checks, and bounded context. A
   policy-selected QA agent runs separately when applicable.
9. Paperclip persists outcome/cost/artifact references and projectors update
   OpenSearch.
10. Kill the active Developer process and change its model binding; the task
    resumes from Paperclip state, context artifact, and workspace without the
    original conversation.

Milestone 2 acceptance:

- one authoritative task/run state throughout;
- no unauthorized tool appears in each role's MCP catalog;
- context stays inside configured per-domain and total limits;
- every supplied record has source, revision/time, status and provenance;
- stale memory cannot override Git;
- one process interruption recovers without duplicate side effects;
- Developer cannot mark its own review/QA accepted;
- OpenSearch loss does not prevent task-state recovery and its indexes rebuild.

## 6. Milestone 3 — experiential memory loop

Add memory only after Milestone 2 is stable.

1. Store the seven representative memory scenarios from the adoption decision.
2. Validate project/role/agent scoping, temporal supersession, provenance,
   retention/review dates, token impact, and exact-backend fallback.
3. Record which retrieved memories were supplied, used, rejected as stale, or
   contradicted by canonical sources.
4. Detect repeated evidence patterns and create a Paperclip improvement proposal.
5. Demonstrate one reviewed promotion:

```text
experience
→ repeated pattern with source evidence
→ reviewed Agent Skill or deterministic check in Git
→ eval
→ approval
→ versioned rollout/rollback
```

No automatic write to canonical Git is allowed in V1.

## 7. Milestone 4 — evaluation, self-healing, and operations

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

## 8. V1 completion test

A real coding task must demonstrate:

```text
Paperclip durable task/claim
→ stable logical expert + replaceable model/runtime
→ validated Agent Skills + least-privilege Paperclip MCP profile
→ bounded OpenSearch/Memory/CodeGraph context with Git verification
→ task worktree/sandbox
→ deterministic checks
→ independent Reviewer
→ independent conditional QA/UX
→ durable outcome/artifacts/telemetry
→ replayable OpenSearch projection
→ forced interruption and model-change recovery
→ later scoped retrieval of the proven experience
```

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
