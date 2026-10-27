# AI Factory

AI Factory is a reusable software-engineering system under development. It coordinates coding agents around durable tasks, bounded context, scoped tools, and independent verification. The problem it addresses is the loss of task state and useful experience between model sessions: repeated repository discovery, repeated mistakes, excessive context, and work that cannot safely resume after interruption.

Logical agent roles remain stable while models and execution harnesses can change. Useful experience should progressively become reviewed skills, tools, tests, and deterministic automation. The primary success metric is **cost per accepted correct task**, supported by correctness, review acceptance, recovery, latency, and human-intervention metrics. These are goals to evaluate, not demonstrated performance gains.

## Current state

**Phase 1 — dependency admission and integration-first V1.** Phase 0.5, the open-source adoption spike, is complete. The [adoption matrix](docs/decisions/ADOPTION_MATRIX.md), [selected V1 architecture](docs/decisions/V1_ADOPTION_ARCHITECTURE.md), and [six ADRs](docs/decisions/adr/) record the binding selections, authority boundaries, deferrals, and admission gates.

This repository currently contains architecture and governance documents, role and registry contracts, dependency evaluation results, and two portable skill specimens. It does **not** yet contain an integrated V1 runtime or a production-ready deployment. The next milestone is **Milestone 0: dependency admission gates**, before substantial V1 feature implementation.

## North-star loop

```text
DO
↓
VERIFY
↓
RECOVER
↓
REMEMBER
↓
ANALYZE
↓
IMPROVE
↓
STANDARDIZE
↓
AUTOMATE
↓
DO BETTER NEXT TIME
```

## Architectural planes

The following describes the selected architecture and its contracts; integration remains planned.

| Plane | Responsibility | Selected boundary |
| --- | --- | --- |
| Control | Durable tasks/runs, ownership, scheduling, bounded retries, budgets, approvals, continuity, and side-effect evidence | Paperclip is the sole operational authority. No parallel AI Factory task engine or DBOS workflow layer. |
| Execution | Logical roles, replaceable models/harnesses, portable skills, scoped tools, and task workspaces | Paperclip adapters, governed MCP gateway, and workspace/`sandbox_provider` interfaces. AI Factory supplies engineering policy and context integration. |
| Knowledge | Current project truth, historical experience, retrieval, structural code discovery, and artifacts | Git, MemPalace, OpenSearch, CodeGraphContext, and artifact storage have distinct responsibilities, detailed below. |
| Quality | Deterministic validation, independent review, conditional QA/UX, and integration revalidation | Repository checks precede agent judgment. Separate Reviewer/QA identities and policies prevent self-approval. |
| Improvement | Analyze outcomes, detect recurring failures/capability gaps, evaluate changes, and promote proven improvements | Git-owned evals and promotion policy; Paperclip operational telemetry projected into OpenSearch. V1 proposes changes through review and approval. |

## Selected components and ownership

**ADOPT** means a selected format/provider without a material integration gap. **ADAPT** means a selection requiring a bounded adapter, plugin, or configuration profile. Selection does not mean operational admission. Versions below are the recorded evaluation baseline, not a claim about current upstream releases; exact commits and gates are in the [matrix](docs/decisions/ADOPTION_MATRIX.md).

| Component | Decision / evaluated version | Responsibility and limit |
| --- | --- | --- |
| Paperclip | **ADAPT**, `v2026.831.1` / `5282cab` | Owns task/run/lease state, logical agents and active runtime bindings, retries, budgets/costs, approvals, workspace lifecycle, artifact metadata, and MCP policy/audit. Its durable database is operational truth. |
| Agent Skills | **ADOPT**, specification / `skills-ref` 0.1.0 | Portable `SKILL.md` packages owned and versioned in Git. Namespaced metadata and optional `ai-factory.yaml` sidecars describe AI Factory policy. Paperclip installations are derived copies. |
| OpenSearch | **ADOPT**, 3.8.x | Dedicated, rebuildable knowledge and analytics projection across docs, memories, tasks, reviews, telemetry, capabilities, and code pointers. Owns no canonical task, memory, or project truth. |
| Official OpenSearch Python MCP server | **ADAPT**, 0.11.0 | Stateless retrieval provider behind Paperclip's gateway: fixed cluster, read-only tools, explicit allowlists, logical capability aliases, and hard result budgets. Projectors use separate write credentials. |
| CodeGraphContext | **ADAPT**, 0.6.13 | One derived structural graph at a recorded Git revision, exposed through bounded read operations. Pinned Linux container/backend is the selected deployment path; Git remains source-code truth. |
| LiteLLM | **ADAPT**, 1.102.0 | Provider translation, bounded per-call fallback/retry, and usage estimates for raw model APIs only. Owns no durable task state or final cost ledger. |
| MemPalace | **ADAPT**, 3.9.0 | Sole experiential-memory authority for scoped memories, diaries, provenance, and temporal supersession. Single-writer/team-hub profile; task coordination, logstream, and artifact features are excluded. OpenSearch receives a projection. |

Git owns canonical architecture, current code, skill content, policy definitions, project overlays, and eval definitions. Paperclip owns resolved operational bindings. Artifact bytes belong in its configured durable storage provider, with metadata and references in Paperclip; local disk is limited to the single-host V1 slice, with S3-compatible storage required before multi-host operation.

Paperclip's governed MCP gateway is the sole active catalog, permission, approval, audit, and MCP-runtime authority in the selected V1 design. Runtime credentials and network policy must prevent direct bypass; prompt instructions and skill metadata are not permission boundaries. Trusted-host execution starts with task-scoped Git worktrees. Untrusted execution requires a tested Paperclip sandbox provider before admission; a worktree alone does not provide that isolation.

### Deferred, rejected, and reference-only components

- **DBOS:** deferred as a mutually exclusive Paperclip replacement if continuity gates fail; never a concurrent workflow engine.
- **ToolHive:** deferred because it duplicates Paperclip's MCP responsibilities. Re-entry requires measured isolation value and proof of one policy/audit authority.
- **SWE-ReX:** deferred as a possible Paperclip sandbox provider. **E2B** is deferred until stronger hostile-code or multi-tenant isolation is justified.
- **OpenSearch Agentic Memory:** deferred as a mutually exclusive MemPalace replacement. Concurrent MemPalace/OpenSearch primary memory stores are rejected.
- **Promptfoo:** deferred until stable prompt/model regression suites justify a dedicated runner. **Phoenix and Langfuse:** deferred until native telemetry and OpenSearch leave a measured gap. V1 selects repository checks and OpenSearch Search Relevance Workbench for evaluation.
- **OpenAI Symphony and OpenHands Software Agent SDK:** reference patterns only, with no V1 runtime authority. **`isink17/codegraph`:** rejected on the evaluated license and maintainability evidence.

Activating a deferred component or expanding a dependency's authority requires a new evidence-backed decision. The reuse policy favors configuration, plugins, adapters, and upstream contributions; the selected integration does not authorize a long-lived private fork.

## How the V1 task loop is intended to work

1. **Claim and compose.** Paperclip durably claims a task and binds its workspace. An Orchestrator selects the necessary roles: Researcher/Architect when needed, Developer, independent Reviewer, and conditional QA/UX. A runnable agent combines a logical role, model/runtime binding, selected skills, allowed capabilities, project overlay, task packet, and bounded context.
2. **Resolve context and permissions.** An AI Factory pre-run adapter invokes the planned Context Resolver. It issues separate filtered OpenSearch searches for current docs/decisions, relevant history, skills/capabilities, and code pointers; expands memory or graph results when needed; and verifies selected claims against Git/original sources. It deduplicates results, labels provenance/freshness/supersession, enforces per-domain and total budgets, and persists the context artifact and digest. A capability compiler intersects role, skill, project, and task policy into Paperclip grants; missing required capabilities block execution.
3. **Execute through the appropriate lane.** Native coding harnesses such as Codex, Claude Code, and OpenCode retain their tools and session behavior through Paperclip native/ACP adapters. Raw API agents call LiteLLM. AI Factory owns explicit task/risk/eval-based selection and escalation policy; learned routing is deferred until sufficient telemetry exists. Paperclip owns task retries, while LiteLLM handles bounded retries within an API call.
4. **Verify and persist.** Deterministic build/test/static checks produce evidence before independent review. Reviewer and QA receive requirements, diff, checks, and bounded context rather than the implementer's full reasoning. Failed checks/review return work to implementation within retry limits; integration requires relevant revalidation. Paperclip persists outcomes, costs, and artifact references. Idempotent, replayable projectors update OpenSearch with reconciliation for missed or duplicated events.
5. **Recover and learn.** On interruption, Paperclip must reconcile run/lease ownership and retained workspace state, then safely resume an adapter session or reinvoke the logical agent with a different model using durable task state and context artifacts. External side effects require journaled operation keys/idempotency evidence. The original conversation must not be necessary. Reusable lessons enter scoped memory; repeated evidence may produce a reviewed skill, tool, or test proposal.

Retrieved relevance never confers authority. Historical memory cannot override current canonical sources, and graph results must carry their source revision. OpenSearch and graph indexes must be rebuildable; their loss must not destroy task continuity. These recovery and permission properties remain acceptance requirements to prove in the integrated system.

## Evidence and implementation limits

The [recorded POC results](docs/implementation/ADOPTION_POC_RESULTS.md) cover runs on 2026-09-14–15. Dependency checkouts were temporary and outside this repository. These probes support adoption decisions; they do not demonstrate an end-to-end AI Factory deployment.

| Area | Recorded evidence | Remaining limit |
| --- | --- | --- |
| Paperclip | 52 targeted checkout/context/session/review/recovery/stale-lock tests passed across two final runs | Kill/restart, liveness, duplicate wakeup, review, MCP expiry, and workspace fault injection remain admission gates. Windows source installation encountered path, symlink, and native-build failures. |
| Agent Skills | Two checked-in specimens, `repository-discovery` and `code-review`, validated; metadata reading and prompt-catalog loading passed | File-format/loader compatibility is proven; live two-harness execution and behavioral parity remain unproven. See the [specimens](docs/implementation/pocs/agent-skills/README.md). |
| OpenSearch MCP | Five targeted tests passed for mapping/search plumbing, write filtering, response sizing, and multi-search conversion | No live OpenSearch cluster was started. Hybrid queries, aliases, credentials, hard context limits, and delete/rebuild still need live validation. |
| CodeGraphContext | Java/TypeScript parser and watcher suite: 32 passed, one skipped; Go parser test: one passed | Full Windows embedded indexing failed on the Ladybug native library. Representative Linux graph indexing, accuracy, performance, and rebuild tests remain gates. |
| MemPalace | Three focused tests passed for temporal supersession, persisted provenance, and exact-backend status | Concurrent writes, restart, export, backup/restore, and denial of destructive sync remain operational gates. |
| Other evaluations | SWE-ReX executed a command in Docker after injecting an undeclared dependency; DBOS, ToolHive, LiteLLM, Symphony, and OpenHands received source/documentation evaluation | SWE-ReX remains deferred; source inspection is not runtime integration proof. |

The **AI Factory integration code remains to be built**: Context Resolver and canonical-source verifier, pre-run wrapper, projection schemas/workers, engineering workflow policies, project overlays, capability compiler, bounded knowledge/graph/memory adapters, model-selection and telemetry normalization, and quality/evaluation tooling. The kickoff's package names describe planned seams, not existing modules.

No accepted-task benchmark or reliability result for the complete system is recorded. Autonomous canonical self-modification, learned routing, arbitrary privileged tool installation, and unrestricted production changes are outside V1.

## Next milestone and V1 acceptance

[Milestone 0](docs/implementation/IMPLEMENTATION_KICKOFF.md#3-milestone-0--dependency-admission-gates) must:

- Pin and deploy supported dependency builds with durable storage, secrets, health checks, and backup/restore procedures.
- Prove Paperclip recovery and exclusive workspace ownership under injected failures; resolve or block on the recorded upstream correctness issues.
- Prove a pre-run context wrapper that persists a context artifact/snapshot and delegates to a native adapter without a core fork or duplicate run state.
- Admit OpenSearch/MCP, CodeGraphContext, MemPalace, and LiteLLM through live security, recovery, result-bound, and provider contract tests; commit the dependency manifest, license inventory, issue dispositions, results, and rollback versions.

After admission, the plan proceeds through contracts/policies/projections, a Context Resolver vertical slice, the experiential-memory loop, then evaluation and bounded self-healing. V1 acceptance requires one real coding task to pass deterministic checks and independent review, persist its outcome, recover from forced interruption and a model change without duplicate side effects, rebuild lost OpenSearch indexes, and make proven experience retrievable by a later task. This has not yet been demonstrated.

## Reading order

1. [Goals](autonomy/GOALS.md) and [Autonomy Index](autonomy/INDEX.md) — success criteria, current phase, and context router.
2. [Adoption Matrix](docs/decisions/ADOPTION_MATRIX.md) and [ADRs 001–006](docs/decisions/adr/) — binding decisions, evaluated revisions, rationale, and replacement boundaries.
3. [V1 Adoption Architecture](docs/decisions/V1_ADOPTION_ARCHITECTURE.md) — physical diagram, ownership, adapters, recovery sequences, and unresolved gates.
4. [Autonomous Engineering System](docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md) — full architectural contract across the five planes.
5. [Implementation Kickoff](docs/implementation/IMPLEMENTATION_KICKOFF.md) and [POC Results](docs/implementation/ADOPTION_POC_RESULTS.md) — milestone acceptance criteria and the limits of existing evidence.
6. [Governance](autonomy/GOVERNANCE.md) and [Open Source Adoption Strategy](docs/architecture/OPEN_SOURCE_ADOPTION_STRATEGY.md) — provenance, promotion, and reuse policy.

For focused detail, see [state/storage](docs/architecture/STATE_AND_STORAGE.md), [knowledge retrieval](docs/architecture/OPENSEARCH_KNOWLEDGE_FABRIC.md), and [capability enforcement](docs/architecture/MCP_AND_CAPABILITY_MODEL.md). Contributors and coding agents should read [AGENTS.md](AGENTS.md) before making changes. The [adoption spike](docs/implementation/ADOPTION_SPIKE.md) is retained as the completed spike's acceptance contract, not the current work phase.
