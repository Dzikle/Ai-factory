# AI Factory — Foundational Dependency Adoption Matrix

**Status:** Spike complete; Milestone 0 dependency admission blocked

**Owner:** adoption spike

**Decision date:** 2026-09-14

**Detailed architecture:** [`V1_ADOPTION_ARCHITECTURE.md`](V1_ADOPTION_ARCHITECTURE.md)

## Decision codes

```text
ADOPT     — canonical format/provider with no material integration gap
ADAPT     — selected behind a bounded adapter/plugin/configuration profile
REFERENCE — mine patterns/invariants; not a V1 runtime dependency
DEFER     — useful only after a named re-entry trigger; not V1
REJECT    — evaluated and not selected
```

No important candidate remains undecided.

## Final matrix

| Capability | Candidate and evaluated revision | Decision | Evidence-backed reason | Authority / V1 use |
| --- | --- | --- | --- | --- |
| Control plane | `paperclipai/paperclip` `5282cab`, release `v2026.831.1` | **ADAPT — NOT ADMITTED** | Durable primitives and process-loss recovery passed, but controller-loss recovery leaves an active ephemeral environment lease and the public external-adapter contract cannot transparently enrich then delegate to a native adapter in the same run. MIT, active 2026-09-14. | Intended sole operational authority only after an upstream-compatible fix and re-admission. [ADR 001](adr/001-control-plane-paperclip.md). |
| Durable workflow fallback | DBOS Python 2.31.1 `8e8ef52` | **DEFER** | Mature Postgres workflows, steps, queues, retries, recovery, messaging and scheduling would replace substantial greenfield code, but beside Paperclip it is a competing state machine. MIT, active 2026-09-14. | No V1 authority. Reconsider only as a mutually exclusive Paperclip replacement. |
| Portable skills | `agentskills/agentskills` `69ef37e`, `skills-ref` 0.1.0 | **ADOPT** | Standard `SKILL.md`, arbitrary string metadata, optional resources and progressive disclosure. Both AI Factory POC skills validate and load through metadata/prompt adapter styles. Apache-2.0, active 2026-08-09. | Format standard; Git owns skill content. [ADR 002](adr/002-skills-agent-skills.md). |
| Knowledge fabric | OpenSearch 3.8.x | **ADOPT** | Hybrid search, `_msearch`, Agentic Memory, agent tracing, and Search Relevance Workbench reduce custom retrieval/eval infrastructure. | Disposable organizational search/retrieval projection; never canonical truth. |
| Knowledge MCP | `opensearch-project/opensearch-mcp-server-py` 0.11.0 `fcb23ec` | **ADAPT** | Mapping/search/msearch and read filtering exist; 5 focused tests passed. Needs fixed-cluster configuration, a second allowlist, logical aliases, and stricter result budgets. Apache-2.0, active 2026-09-02. | Stateless read provider behind Paperclip gateway. [ADR 003](adr/003-opensearch-mcp.md). |
| MCP runtime/security | Paperclip governed MCP gateway (same `5282cab`) | **ADAPT — CONTROL PLANE BLOCKED** | Live allow/deny and post-run token revocation passed. Auto-bound broad application profiles are additive and must be removed before exact catalog-entry grants are effective. | Intended sole active MCP policy/catalog/approval/audit authority after Paperclip admission. |
| MCP alternative | ToolHive 0.49.0 `630354f` | **DEFER** | Strong container/process runtime, identities, Cedar/external PDP, secrets, registry, audit and OTel; duplicates Paperclip's catalog/policy/secrets/audit/runtime in V1. Apache-2.0, active 2026-09-14. | No V1 authority. Reconsider for untrusted third-party stdio isolation only after one policy authority is proven. |
| Execution/workspaces | Paperclip workspace and `sandbox_provider` interfaces | **ADAPT — NOT ADMITTED** | Workspace/run recovery works for an agent child-process kill, but controller-loss recovery leaked the source environment lease. | Intended sole task-workspace lifecycle owner after the lease gate passes. |
| Sandbox candidate | SWE-ReX 1.4.0 `5c995c3` | **DEFER** | Docker POC executed successfully, but Windows local import failed and Docker client needed undeclared `aiohttp`. No durable task/artifact authority; overlaps Paperclip lifecycle. MIT; evaluated source last committed 2026-03-02. | Reconsider only as a Paperclip `sandbox_provider`, never a workflow owner. |
| Heavier sandbox | E2B | **DEFER** | No measured V1 multi-tenant hostile-code requirement justifies another hosted dependency. | Trigger: threat model exceeds a tested Paperclip provider. |
| Structural graph | CodeGraphContext 0.6.13 `2ef71b0` | **ADAPT** | Exact Linux image passed Java/TS/Go symbol and caller MCP calls and full rebuild after volume loss. The measured update was a 64.01 s full reindex, module dependency lookup was weak, the MCP exposes destructive tools, and the source image reported 16 npm findings. | Single derived graph at a recorded Git revision; schedule rebuilds and expose only bounded reads. [ADR 004](adr/004-code-graph-codegraphcontext.md). |
| Structural graph alternative | `isink17/codegraph` 1.2.0 `cd7237e` | **REJECT** | Good apparent tool surface, but FSL-1.1 is not currently OSI open source and maintenance/adoption evidence is too small for a foundational component. | None. |
| API model gateway | LiteLLM 1.102.0 `b94b8bc` | **ADAPT — MIT CORE ONLY** | Exact-source core Router passed fallback, normalized usage, bounded total-upstream failure and recovery. The `proxy` extra directly installs proprietary `litellm-enterprise`, so the server proxy is not an open-source V1 dependency. | Embed MIT core Router behind the raw-API adapter; no durable authority. [ADR 005](adr/005-api-model-gateway-litellm.md). |
| Native agent runtimes | Paperclip native/ACP adapters | **ADAPT — CONTROL PLANE BLOCKED** | Preserve Codex/Claude/OpenCode/Gemini/Cursor harness tools, sessions, and runtime behavior. | After admission, Paperclip owns adapter session/run binding; native harnesses are not routed through LiteLLM. |
| Experiential memory | MemPalace 3.9.0 `38260df` | **ADAPT** | Real service passed single-writer exclusion, persistence, export/restore, application read-only denial and loss recovery. Default embedding readiness and filesystem read-only restore failed; production embedding quality remains untested. | Sole memory authority after warm-readiness and retrieval-quality gates; limited to memories/diaries/temporal facts. [ADR 006](adr/006-memory-mempalace.md). |
| Shared memory alternative | OpenSearch Agentic Memory 3.8 | **DEFER** | Capable session/working/long-term/history and fact consolidation, but primary use would make the projection cluster authoritative or require another journal; retention is experimental. | Mutually exclusive MemPalace fallback. |
| Dual memory | MemPalace specialist + OpenSearch primary shared memory | **REJECT** | Creates two write, retention, supersession, and retrieval authorities without measured value. | None. OpenSearch receives only a MemPalace projection. |
| Orchestration patterns | OpenAI Symphony 0.0.2 `e0ccc83` | **REFERENCE** | Deterministic workspace confinement, reconcile loop, bounded concurrency, backoff, cleanup, last-known-good config and re-check-after-success are useful invariants. Apache-2.0, active 2026-09-09. | No runtime authority. Patterns applied to Paperclip integration tests. |
| Agent controller patterns | OpenHands Software Agent SDK 1.47.0 `d8be029` | **REFERENCE** | Useful controller/event/runtime separation, but installing it duplicates Paperclip's chosen controller/runner. MIT, active 2026-09-14. | No runtime authority. |
| Eval runner | Promptfoo | **DEFER** | Native deterministic checks and OpenSearch Search Relevance Workbench are sufficient for V1. | Trigger: stable prompt/model regression suites need a dedicated runner. |
| Trace/eval platform | Phoenix | **DEFER** | Adds a redundant observability/eval store before a measured gap exists. | Trigger: native Paperclip/OpenSearch telemetry cannot answer a specific required workflow. |
| LLM observability | Langfuse | **DEFER** | Same redundant-store concern as Phoenix. | Same measured-gap trigger. |

## Paperclip acceptance classification

| Architectural requirement | Result | Evidence / boundary |
| --- | --- | --- |
| Logical agent identity independent from model/provider/runtime | **PASS** | Agent identity/role fields are separate from adapter/runtime/model configuration. |
| Task survives agent/process crash without original conversation | **PASS** | Both child-process and controller-container loss preserved durable task state; explicit reconciliation/resume produced successful successors. |
| Atomic claim, lease and stale-owner recovery | **BLOCKER** | Controller recovery terminalized the orphan run but left its ephemeral environment lease active with no expiry/release. |
| Persistent run/session/continuation state | **PASS** | Provider session IDs, continuation, liveness, retry lineage and run status are persisted. |
| Heartbeats/recurring execution | **PASS** | Wake queue, timers/routines, controller leases and bounded retry scheduling. |
| Budgets and cost accounting | **PASS** | Agent budgets and issue/project/run/provider/model-linked cost events. |
| Native and API agent adapters | **PASS** | Local/ACP/native adapters plus plugin launchers; API path may call LiteLLM. |
| Git workspaces/worktrees | **PASS** | Execution workspace records, isolated worktrees, branch/ref containment and cleanup. |
| Approvals and governance | **PASS** | Execution policies, approval rows and MCP approval/argument hashing. |
| Agent Skills compatibility and canonical portability | **ADAPT** | Paperclip can sync compatible directories, but Git—not Paperclip DB—must own skill content. |
| Secrets, artifacts and storage | **PASS** | Encrypted secret providers and local/S3 artifact storage abstractions. |
| Plugins/events sufficient for OpenSearch projection | **ADAPT** | Typed at-least-once events and jobs exist; alpha runtime needs idempotent consumer plus reconciliation fallback. |
| Inject Context Resolver before execution | **BLOCKER** | The external adapter can run pre-provider and call governed MCP, but cannot delegate to a registered native adapter or persist context mutation to the same run snapshot. |
| Query OpenSearch/memory before execution | **ADAPT** | Resolver runs through governed MCP/memory adapters before delegating to runtime. |
| Independent Reviewer and QA | **PASS** | Separate logical agents and execution-policy participants with independent profiles and review recovery. |
| Preserve AI Factory expert semantics | **PASS** | Generic roles/policies can carry our role names/stages without changing identity model. |
| Project task/run/telemetry events into OpenSearch | **ADAPT** | Plugin event/job surface plus durable reconciliation; OpenSearch remains non-authoritative. |
| Operational task truth without canonical project truth | **PASS** | Authority split is compatible; canonical Git/docs/memory remain external. |
| Avoid a long-term fork | **BLOCKER** | Current public surfaces are insufficient for the required seam; the fix must be upstream-compatible and re-tested. |

Milestone 0 found two architectural **BLOCKER** classifications at the pinned
Paperclip revision. Paperclip is not admitted and must not be privately forked;
the selected target architecture remains conditional on an upstream-compatible
fix and re-admission.

## Final source-of-truth summary

| Information | Authoritative owner | Projection/cache |
| --- | --- | --- |
| Canonical architecture/project rules | Git | OpenSearch docs |
| Task/run operational state | Paperclip database **after admission** | OpenSearch tasks/events/telemetry |
| Logical agent and active runtime/model binding | Paperclip database **after admission** | Git templates; OpenSearch metadata |
| Skills | Git Agent Skills packages | Paperclip installations; OpenSearch metadata |
| Experiential memory | MemPalace | OpenSearch memory view |
| Artifact bytes | Paperclip-configured durable storage provider | OpenSearch metadata |
| Telemetry | Paperclip database **after admission** | OpenSearch analytics and artifact logs |
| Code truth | Git | CodeGraphContext and OpenSearch code pointers |
| Structural code graph | CodeGraphContext at a recorded Git revision | OpenSearch symbol metadata |
| Active permissions/MCP audit | Paperclip gateway/database **after admission** | Git definitions; OpenSearch audit view |
| Model/eval/capability policy definitions | Git | Paperclip resolved bindings; OpenSearch results |

## Selected stack and custom work

The explicit stack, physical diagram, memory bake-off, failure/recovery and
replacement paths, custom AI Factory components, adapters, risk gates, POC
commands/results, and source links are in
[`V1_ADOPTION_ARCHITECTURE.md`](V1_ADOPTION_ARCHITECTURE.md). The foundational
decisions are recorded in [`adr/`](adr/).
