# AI Factory V1 Self-Enhancement Lifecycle

**Status:** Approved design; implementation planning pending

**Decision date:** 2026-10-03

**Scope:** Enhance the accepted trusted-local AI Factory V1 by using that V1 to implement and verify its own next capabilities.

## 1. Decision

AI Factory will use its existing V1 engineering loop as both the implementation platform and the first target of the next development program. This is **governed self-hosted development**, not unrestricted live self-modification.

One owner-authorized program will execute a complete lifecycle without requesting confirmation at every internal stage. Paperclip remains the sole task, run, workspace, approval, and MCP-policy authority. Work happens in isolated Git workspaces, passes deterministic validation and independent review, and is integrated or deployed only as permitted by the program's persisted authorization envelope.

The program consolidates the selected Synthesis ideas into four coherent implementation areas rather than creating one project per idea:

1. autonomous orchestration;
2. efficient context and knowledge;
3. verification and delivery;
4. continuous operation and measurement.

No second control plane, memory authority, knowledge authority, workflow engine, or provider-specific core is introduced.

## 2. Desired outcome

The enhanced factory must preserve the current product goal:

> A reusable autonomous engineering system that improves model effectiveness by reducing rediscovery, context waste, repeated mistakes, and avoidable reasoning while remaining model- and provider-agnostic.

The program succeeds when V1 can take a bounded enhancement objective for its own repository and autonomously carry it through context preparation, implementation, verification, independent review, bounded correction, durable reporting, and authorized publication without requiring the original conversation or repeated human confirmations.

Improvement is measured against correctness first, followed by reliability, accepted-task rate, token efficiency, cost per accepted correct task, latency, human intervention, security, and maintainability. Missing telemetry remains unknown; it is never interpreted as zero cost or proof of improvement.

## 3. Interpretation of self-enhancement

The running control plane must never overwrite the live checkout, database, policy, credentials, or runtime image that governs its current task.

Self-enhancement means:

```text
stable V1 controller
    -> owner-authorized improvement program
    -> isolated AI Factory Git workspace
    -> candidate implementation
    -> deterministic verification
    -> independent review and bounded repair
    -> authorized publication/integration/deployment
    -> measured successor V1
```

The successor may execute later work only after its candidate identity and verification evidence are durable. Recovery always starts from Paperclip state, Git, artifacts, and persisted context—not from an LLM conversation.

## 4. Authorization without repeated confirmation

The owner authorizes the program once. The authorization envelope is stored with the durable parent task and inherited by its implementation work, without silent expansion.

The envelope declares:

- target repository, branch family, and allowed paths;
- allowed local reads, writes, tests, commits, and workspace operations;
- whether remote push, pull-request creation, merge, deployment, or service restart is allowed;
- capability and credential scope;
- budget and maximum correction attempts;
- irreversible-action boundaries;
- expiry, revocation, and stop conditions.

An operation already covered by the envelope does not require another confirmation. The program pauses only when an operation is outside the envelope, an unapproved irreversible action is required, a safety/correctness gate remains failed after bounded repair, or a genuine product decision has materially different outcomes.

Authorization is a runtime constraint, not prompt text. Paperclip and its governed capability layer enforce it.

## 5. One end-to-end lifecycle

The program uses one durable lifecycle. The stages below are internal state transitions, not user approval checkpoints.

### 5.1 Admit

1. Record the objective, acceptance criteria, target revision, authorization envelope, and program budget.
2. Classify task size, risk, and change type.
3. Resolve required capabilities and query live component health.
4. Reject or explicitly degrade the task if a required capability is unavailable.

Small, eligible changes use a reduced workflow. Read-only work receives no code-writing workspace. Higher-risk changes receive the full quality path.

### 5.2 Assemble bounded context

The always-on context contains only task identity, authorization, safety/confidentiality constraints, and the required outcome contract. Workflow, project, knowledge, memory, and code context load progressively.

For knowledge-bearing tasks, the resolver first issues a bounded provider-neutral evidence request. The resulting evidence pack contains:

- freshness and authority labels;
- ranked passages or records;
- citations and original-source pointers;
- query and result budgets;
- explicit unknowns and degraded sources;
- a digest persisted with the run.

Current Git and canonical sources remain authoritative. OpenSearch is a rebuildable retrieval projection; MemPalace remains historical/experiential memory. Agents use bounded query operations rather than unrestricted index access.

### 5.3 Implement

Paperclip binds the task to an isolated workspace and dispatches the selected logical Developer through a replaceable runtime adapter. The implementation follows existing repository patterns and uses the selected operational skills and deterministic commands rather than re-deriving mechanical procedures.

The first operational skill set covers repository preflight, verified commit preparation, publication/status operations, review-resolution handling, deferred-finding capture, human-gated actions when the envelope requires them, and scoped audits. Skills remain canonical Agent Skills packages in Git and do not grant authority by themselves.

### 5.4 Verify, review, and repair

Every code-changing task receives a versioned verification contract derived from project policy, task class, and risk. It declares required checks, permitted reductions, evidence format, and acceptance conditions.

The validator records:

- checks requested and checks actually run;
- versions and relevant configuration;
- pass, fail, skip, and unavailable results;
- divergence from the requested contract;
- raw artifact references;
- a compact verification digest.

A separate Reviewer evaluates the same candidate revision and evidence. External CI or pull-request review evidence is attached durably to that candidate when applicable. Corrections return to implementation and repeat validation; they do not bypass it. Repair attempts are finite and Paperclip owns the retry count.

### 5.5 Accept and publish

When all required evidence is satisfied, the task becomes an accepted candidate. Publication, merge, deployment, and restart behavior follow the original authorization envelope. If an action is not authorized, the lifecycle stops once at that boundary with a complete ready-to-act report.

The authoritative record includes candidate commit/tree identity, verification digest, independent review result, external evidence, authorization used, side-effect receipts, and rollback instructions. A successful isolated candidate is revalidated after integration when integration occurred.

### 5.6 Learn, maintain, and continue

The lifecycle emits one normalized outcome report from authoritative records. Every code change declares its knowledge impact as `none`, `verify`, or `update`; any required update runs as separate post-acceptance maintenance work. Incidental discoveries become low-cost deferred findings rather than silently expanding scope:

```text
observation -> deferred finding -> triaged candidate -> approved task
```

Knowledge maintenance is separate from accepting the code candidate. Approved knowledge changes use stable targets, optimistic source-version checks, dry runs, minimal diffs, audit records, rebuild/reindex steps, and post-update verification.

Factory-owned temporary resources are retained or reclaimed according to explicit ownership, references, reproducibility, and retention policy. The program then measures the completed wave and continues automatically to the next ready wave under the same authorization envelope.

## 6. Consolidated implementation areas

### 6.1 Autonomous orchestration

This area implements:

- intent routing and explicit scope verbs;
- deterministic task-size classes and eligible reduced workflows;
- developer-readable stage presentation;
- durable authorization envelopes;
- runtime capability manifests;
- workflow admission and explicit degradation policies;
- capability-based routing;
- component-owned health probes with an aggregated diagnostic view;
- complete handoff contracts;
- no runtime/workspace allocation for purely read-only tasks.

Paperclip continues to own lifecycle state. These features extend policy resolution and pre-run enrichment rather than creating an AI Factory scheduler beside Paperclip.

### 6.2 Efficient context and knowledge

This area implements:

- knowledge-first bounded discovery before broad exploration;
- current-source verification, freshness, and citations;
- provider-neutral knowledge-source adapter contracts;
- lean always-on context with progressive loading;
- a bounded, inspectable `evidence_pack` composite operation;
- targeted structured knowledge patches;
- provider-independent retrieval regression testing.

Knowledge adapters declare source identity, authority, read/write behavior, authentication requirements, supported queries, citation shape, freshness semantics, result budgets, projection behavior, and degradation. Concrete adapters are implemented only when a real source is used.

Retrieval evaluation uses Git-owned judged queries and expected sources/facts, top-k relevance, citation and authority checks, freshness tests, access-scope tests, and regression comparisons after ranking/indexing changes. Stable cases are supplemented by reviewed failures from real work to reduce benchmark overfitting.

### 6.3 Verification and delivery

This area implements:

- the operational skill set;
- verification contracts and token-efficient digests;
- explicit reduced-check policy;
- detection of missing or divergent verification;
- durable external CI/pull-request review evidence;
- one normalized human-readable outcome report.

Raw evidence stays available for audit while compact digests enter model context. The design records equivalence of required evidence; it does not claim that local execution perfectly reproduces every CI environment.

### 6.4 Continuous operation

This area implements:

- deferred-finding capture, deduplication, triage, and promotion to approved work;
- lifecycle metadata for AI Factory-owned workspaces, caches, logs, temporary evidence, and generated artifacts;
- reference-aware retention and recoverable cleanup;
- truthful measurement of task outcomes and system cost.

It does not authorize general machine, user-directory, package, Docker, credential, or unrelated-repository cleanup.

## 7. Core data contracts

Git owns versioned schemas and policy definitions. Paperclip stores resolved operational instances and state. OpenSearch may project them for retrieval and analysis.

| Contract | Minimum semantics |
| --- | --- |
| Program authorization | Scope, capabilities, side effects, budgets, expiry, revocation, stop conditions |
| Task classification | Intent, change type, size, risk, required workflow, reduction eligibility |
| Capability manifest | Logical operations, read/write class, provider binding, health, limits, degradation |
| Context package | Query plan, selected evidence, provenance, freshness, budgets, original-source refs, digest |
| Verification contract | Required checks, allowed reductions, environment assumptions, acceptance conditions |
| Verification digest | Actual checks, results, omissions/divergence, artifact refs, candidate identity |
| Deferred finding | Origin, evidence, scope reason, severity, confidence, dependencies, duplicate link |
| Outcome report | Objective, candidate, changes, evidence, decisions, unresolved items, next disposition |
| Knowledge patch | Source/anchor, expected version, operation, dry run, diff, rebuild, verification |
| Resource record | Owner task, type, location, timestamps, retention, reproducibility, references, cleanup |
| Retrieval evaluation | Query, expected source/fact, scope, authority, ranking metrics, result version |

Schemas must stay provider-neutral and begin with fields exercised by the first vertical slice. They must not become duplicate workflow or permission stores.

## 8. Failure and recovery behavior

- Missing required authority or capability fails closed before execution.
- Optional knowledge, memory, or projection loss produces an explicit degraded state; it never fabricates evidence.
- A failed deterministic check returns to implementation before Reviewer execution.
- Reviewer or external findings return the same candidate lineage to a bounded correction loop.
- Process/model loss resumes or reinvokes from Paperclip state, the workspace, context digest, and artifacts.
- A changed source invalidates a proposed knowledge patch through its version precondition.
- A cleanup candidate with unknown ownership or live references is retained.
- Exhausted repair budget produces one durable blocked outcome with evidence and required next decision.
- Side effects remain journaled and idempotent so recovery cannot silently duplicate them.

## 9. Implementation program shape

The implementation plan will use four coherent waves matching section 6. This is not a new mandatory milestone hierarchy and does not reopen the accepted M0-M4 roadmap.

Each wave must deliver a working vertical improvement through the existing V1 task command, Paperclip policy, isolated workspace, `milestone3.check`, independent review, and existing publication machinery. V1 should run the implementation tasks against its own repository wherever its current capability is sufficient. Missing factory capability may be supplied by the operator only when recorded explicitly; the result must not be described as autonomous.

The parent program continues between waves without requesting new approval when the next work remains within its authorization envelope. A wave may contain a small number of dependency-ordered tasks, but there will be no task-per-module decomposition.

## 10. Verification strategy

The program requires:

1. schema/unit tests for each new contract and policy decision;
2. integration tests proving Paperclip remains the sole workflow and permission authority;
3. recovery tests across process/model interruption;
4. capability-manifest and degradation tests across at least the active native adapters;
5. verification-contract tests covering full, reduced, missing, and divergent checks;
6. retrieval regression tests for the active knowledge projection;
7. knowledge-patch conflict, dry-run, audit, and post-update tests;
8. outcome-report reproducibility from authoritative records;
9. resource-retention tests proving referenced/protected artifacts survive;
10. one end-to-end self-hosted AI Factory enhancement completed by V1 under a single program authorization.

Natural-language routing conformance testing remains deferred. The initial tests validate deterministic policy and capability behavior, not exact model phrasing.

## 11. Acceptance criteria

The whole-lifecycle implementation is accepted when:

- a single owner authorization launches the self-enhancement program;
- V1 implements a real enhancement in an isolated AI Factory workspace;
- no internal stage requires additional human confirmation unless the envelope is exceeded;
- interruption can resume without the original conversation;
- context is progressively loaded within persisted budgets and source precedence;
- required capabilities and health are checked before admission;
- deterministic evidence, independent review, and bounded correction operate on the same candidate lineage;
- the outcome report is reproducible from authoritative records;
- deferred findings and knowledge-maintenance work do not expand the accepted task silently;
- retrieval quality and post-integration checks show no regression;
- AI Factory-owned temporary resources follow explicit retention/cleanup policy;
- metrics report what is known and do not claim unmeasured savings;
- Paperclip, Git, MemPalace, OpenSearch, artifacts, and runtime adapters retain their documented authority boundaries;
- another supported model/runtime can execute the contracts without changing their semantics.

## 12. Explicitly deferred or excluded

This program does not implement:

- profile compilation or deterministic installation generation;
- broad deterministic hooks/enforcement;
- managed update packages;
- host-authenticated browser bridges;
- runtime browser/demo QA;
- repository documentation-style classification;
- credential/token brokering;
- natural-language routing conformance suites;
- a new specialist-agent system or Synthesis memory model;
- guided onboarding, reproducible sandbox distribution, or parallel ticket workspaces;
- Synthesis telemetry, audience-specific report templates, or local-model summarization;
- a separate promotion framework, typed knowledge-facet schema, or mandatory reconnaissance stage;
- a second merge subsystem or any second source of task/workflow truth.

Deferred items require a later evidence-backed decision and may not be activated implicitly by this program.

## 13. Required canonical updates during implementation

The implementation must update the existing canonical documents to distinguish prohibited blind self-modification from the newly approved governed self-hosted development model. At minimum, it must reconcile:

- `AGENTS.md`;
- `autonomy/GOALS.md`;
- `autonomy/GOVERNANCE.md`;
- `docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md`;
- `docs/implementation/IMPLEMENTATION_KICKOFF.md` or its successor implementation record.

The current explicit human decision and this approved design govern the implementation effort, but canonical documents must be brought back into agreement as part of the first wave.
