# AI Factory V1 Self-Enhancement Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the accepted trusted-local V1 so one owner-authorized program can implement, verify, review, report, and measure AI Factory enhancements without repeated approval at every internal stage.

**Architecture:** Paperclip remains the sole operational authority. A new operator-side program command creates one durable parent issue plus four dependency-ordered child waves, all bound to one validated authorization digest; the children use existing isolated workspaces, deterministic checks, independent agents, and Paperclip state. New Python modules add bounded capability admission, evidence packs, verification digests, reports, and maintenance primitives without adding a service or database.

**Tech Stack:** Python 3.11+ standard library, `jsonschema==4.25.1`, `PyYAML==6.0.2`, Paperclip HTTP API and native execution policies, OpenSearch 3.8.x through the existing bounded client/MCP deployment, MemPalace through the existing adapter, Agent Skills packages, `unittest`, Git.

**Spec:** `docs/superpowers/specs/2026-10-03-self-enhancement-lifecycle-design.md`

## Global Constraints

- Use the current AI Factory V1 and admitted Paperclip fork; do not add a second task, workflow, workspace, approval, or MCP-policy authority.
- The running controller never modifies its live checkout. All code changes occur in Paperclip task workspaces.
- One operator invocation authorizes the program. Child waves do not add human approval stages; remote publication, merge, deployment, and service restart remain unavailable unless the persisted envelope explicitly allows the exact action and an existing command supports it.
- Do not weaken `milestone2.publish`; its exact-candidate owner approval remains required until a separately reviewed capability replaces that boundary.
- Git owns schemas, policy, skills, eval definitions, and project overlays. Paperclip owns resolved task/run state. MemPalace remains the sole experiential-memory authority. OpenSearch remains a rebuildable projection.
- Use only existing dependencies and services. Do not activate deferred hooks, browser bridges, credential brokers, sandboxes, telemetry platforms, or code graph support.
- Every write is path-scoped, version-checked, idempotent where externally visible, and represented by durable evidence.
- Missing usage/cost stays unknown. Correctness and accepted-task evidence outrank token or price reduction.
- The implementation is one current-V1 issue containing the tasks below. The tasks are engineering checkpoints and commits, not separate owner-confirmation points.

## Review Focus

1. **Stale or widened authorization:** a changed digest, expired envelope, path escape, or action outside the envelope must block before child creation. Task 2 tests each case.
2. **Interrupted multi-write submission:** rerunning after parent creation, authorization-document write, child creation, or blocker wiring must converge without duplicate issues or comments. Task 2 tests replay after every boundary.
3. **Required versus optional capability loss:** required unhealthy capabilities block admission; optional ones produce an explicit degraded report and never disappear silently. Task 3 tests both outcomes.
4. **Candidate identity drift:** verification, review evidence, external evidence, and the outcome report must all name the same commit/tree; mismatches block acceptance. Task 5 tests drift.
5. **Destructive maintenance scope:** knowledge patches with stale hashes and resource cleanup outside factory-owned roots or with live references must be rejected. Task 6 tests all three conditions.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `autonomy/contracts/v1/self-enhancement.schema.json` | One versioned schema with `$defs` for program authorization, waves, capability health, verification, findings, reports, patches, resources, and knowledge sources |
| `autonomy/policies/self-enhancement.v1.yaml` | The four implementation waves, task classification, budgets, required capabilities, and stop conditions |
| `autonomy/capabilities/providers.v1.yaml` | Logical capability-to-provider manifests and degradation policy; never runtime credentials |
| `autonomy/knowledge/sources.v1.yaml` | Git, OpenSearch, and MemPalace source contracts and budgets |
| `milestone1/validate_contracts.py` | Cross-field validation for the new Git-owned contracts |
| `milestone2/program.py` | Operator CLI for idempotent parent/child program submission and authoritative status readback |
| `milestone2/capabilities.py` | Capability health aggregation and admission decision |
| `milestone2/outcome_report.py` | Deterministic Markdown/JSON report projection from authoritative records |
| `milestone3/context.py` | Bounded provider-neutral evidence-pack composition |
| `milestone3/verification.py` | Safe verification-contract execution and digest generation |
| `milestone3/maintenance.py` | Deferred findings, exact knowledge patches, and recoverable factory-resource cleanup |
| `autonomy/evals/verification.v1.json` | Full and reduced AI Factory verification profiles |
| `autonomy/evals/git-docs-v1.json` | Extended judged retrieval cases and thresholds |
| `autonomy/skills/*` | Canonical operational Agent Skills and AI Factory sidecars |
| `tests/test_self_enhancement_contracts.py` | Schema and cross-field contract tests |
| `tests/test_program.py` | Program submission, replay, hierarchy, authorization, and status tests |
| `tests/test_capabilities.py` | Health, admission, and degradation tests |
| `tests/test_context.py` | Evidence budgets, provenance, freshness, and adapter failure tests |
| `tests/test_verification.py` | Verification execution, reduction, divergence, identity, and digest tests |
| `tests/test_outcome_report.py` | Deterministic report rendering tests |
| `tests/test_maintenance.py` | Finding deduplication, patch, and cleanup safety tests |
| `tests/test_operational_skills.py` | Agent Skills package and sidecar checks |

### Task 1: Canonical lifecycle contracts and governance

**Files:**
- Create: `autonomy/contracts/v1/self-enhancement.schema.json`
- Create: `autonomy/policies/self-enhancement.v1.yaml`
- Create: `tests/test_self_enhancement_contracts.py`
- Modify: `milestone1/validate_contracts.py:4-120`
- Modify: `AGENTS.md:1-120`
- Modify: `autonomy/GOALS.md:1-97`
- Modify: `autonomy/GOVERNANCE.md:70-130`
- Modify: `docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md:450-540`

**Interfaces:**
- Consumes: existing JSON Schema test pattern and source-of-truth precedence.
- Produces: `validate_self_enhancement(document: dict, *, now: datetime) -> list[str]` and the canonical program policy consumed by Tasks 2-6.

- [ ] **Step 1: Write failing schema and cross-field tests**

```python
class SelfEnhancementContractTests(unittest.TestCase):
    def test_program_has_one_authorization_and_four_ordered_waves(self):
        document = sample_program()
        validate_schema(document)
        self.assertEqual([], validate_self_enhancement(document, now=NOW))
        self.assertEqual(
            ["orchestration", "context-knowledge", "verification-delivery", "continuous-operation"],
            [wave["id"] for wave in document["waves"]],
        )

    def test_expired_or_widened_authorization_is_rejected(self):
        document = sample_program()
        document["authorization"]["expires_at"] = "2026-10-02T00:00:00Z"
        self.assertIn("authorization expired", validate_self_enhancement(document, now=NOW))
        document = sample_program()
        document["authorization"]["allowed_paths"] = ["../outside"]
        with self.assertRaises(ValidationError):
            validate_schema(document)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_self_enhancement_contracts -v`

Expected: FAIL because the schema and `validate_self_enhancement` do not exist.

- [ ] **Step 3: Add the single schema and four-wave policy**

The top-level schema is a strict object with these required fields:

```json
{
  "schema_version": 1,
  "program_id": "ai-factory-self-enhancement-v1",
  "request_key": "self-enhancement-2026-10-03",
  "project_id": "ai-factory",
  "repository_id": "ai-factory",
  "intent": "self_enhancement",
  "scope_verb": "implement",
  "base_revision": "0000000000000000000000000000000000000000",
  "spec_path": "docs/superpowers/specs/2026-10-03-self-enhancement-lifecycle-design.md",
  "plan_path": "docs/superpowers/plans/2026-10-03-v1-self-enhancement-lifecycle.md",
  "authorization": {
    "allowed_paths": ["AGENTS.md", "autonomy/", "docs/", "milestone1/", "milestone2/", "milestone3/", "milestone4/", "tests/"],
    "allowed_actions": ["repo.read", "repo.write", "git.read", "git.diff.read", "validation.run", "knowledge.search", "memory.search", "artifact.write"],
    "remote_actions": [],
    "max_correction_rounds": 3,
    "expires_at": "2026-12-31T23:59:59Z"
  },
  "waves": []
}
```

Define strict `$defs` for `authorization`, `wave`, `capability_health`, `verification_contract`, `verification_digest`, `deferred_finding`, `outcome_report`, `knowledge_patch`, `resource_record`, and `knowledge_source`. All objects use `additionalProperties: false`; identifiers, relative paths, SHA-1/SHA-256 values, timestamps, actions, and finite numeric budgets have bounded patterns/ranges.

The policy file contains exactly four waves with the IDs asserted above. Each wave declares `size`, `risk`, `change_type`, `required_capabilities`, `optional_capabilities`, `context_budget`, `verification_profile`, `knowledge_impact`, and `blocked_by`. `intent` is a bounded identifier and `scope_verb` is one of `implement`, `verify`, `review`, `report`, or `maintain`; this is deterministic routing metadata, not a natural-language classifier.

- [ ] **Step 4: Add cross-field validation**

```python
def validate_self_enhancement(document: dict, *, now: datetime) -> list[str]:
    errors = []
    auth = document["authorization"]
    expires = datetime.fromisoformat(auth["expires_at"].replace("Z", "+00:00"))
    if expires <= now:
        errors.append("authorization expired")
    ids = [wave["id"] for wave in document["waves"]]
    if len(ids) != len(set(ids)):
        errors.append("wave IDs must be unique")
    known = set(ids)
    for wave in document["waves"]:
        unknown = set(wave["blocked_by"]) - known
        if unknown:
            errors.append(f"wave {wave['id']} has unknown blockers: {sorted(unknown)}")
        if wave["id"] in wave["blocked_by"]:
            errors.append(f"wave {wave['id']} blocks itself")
        if not set(wave["required_capabilities"]).issubset(auth["allowed_actions"]):
            errors.append(f"wave {wave['id']} exceeds authorization")
    return errors
```

- [ ] **Step 5: Reconcile canonical self-improvement language**

Update the listed canonical documents to use this distinction verbatim:

```text
Blind live self-modification remains prohibited. Governed self-hosted development is allowed when a current human authorization defines the repository, paths, actions, budgets, stop conditions, verification, independent review, publication boundary, and rollback. The running controller may not rewrite the live state that governs its own run.
```

Do not claim production readiness or automatic merge/deployment.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m unittest tests.test_self_enhancement_contracts tests.test_milestone1_contracts tests.test_milestone1_data_contracts -v`

Expected: PASS.

Run: `python -m milestone3.check`

Expected: PASS with the pinned environment.

- [ ] **Step 7: Commit**

```bash
git add AGENTS.md autonomy/GOALS.md autonomy/GOVERNANCE.md autonomy/contracts/v1/self-enhancement.schema.json autonomy/policies/self-enhancement.v1.yaml docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md milestone1/validate_contracts.py tests/test_self_enhancement_contracts.py
git commit -m "feat: define governed self-enhancement contracts"
```

### Task 2: One-authorization Paperclip program submission

**Files:**
- Create: `milestone2/program.py`
- Create: `milestone2/tasks/self-enhancement-program.json`
- Create: `tests/test_program.py`
- Modify: `milestone1/paperclip_policy.py:16-43`
- Modify: `milestone2/README.md`

**Interfaces:**
- Consumes: `validate_self_enhancement`, `milestone2.task.read_object/text/uuid`, and Paperclip `Client`.
- Produces: `classify_task(...) -> dict`, `authorization_digest(program) -> str`, `program_execution_policy(...) -> dict`, `submit_program(...) -> dict`, `read_program_status(...) -> dict`, and CLI commands `python -m milestone2.program submit|status`.

- [ ] **Step 1: Write failing program-policy and submission tests**

```python
def test_program_policy_has_independent_checks_without_repeated_user_gate(self):
    policy = program_execution_policy(DEV, VALIDATOR, REVIEWER, qa_agent_id=QA)
    self.assertEqual(["review", "review", "review"], [s["type"] for s in policy["stages"]])
    self.assertEqual(3, policy["maxReviewRounds"])

def test_submit_creates_one_parent_and_dependency_ordered_children(self):
    client = FakePaperclip()
    result = submit_program(client, COMPANY, STATE, WORKFLOW, sample_program(), start=True)
    self.assertEqual(1, len(client.parents))
    self.assertEqual(4, len(client.children))
    self.assertEqual([], client.children[0]["blockedByIssueIds"])
    self.assertEqual([client.children[0]["id"]], client.children[1]["blockedByIssueIds"])
    self.assertEqual(result, submit_program(client, COMPANY, STATE, WORKFLOW, sample_program(), start=True))

def test_routing_is_deterministic_and_read_only_work_has_no_workspace(self):
    decision = classify_task(intent="audit", scope_verb="report", size="small",
                             risk="low", change_type="read_only")
    self.assertEqual("read_only", decision["execution_mode"])
    self.assertFalse(decision["requires_workspace"])
    self.assertEqual("reduced", decision["verification_profile"])
```

Add replay cases that interrupt after parent creation, authorization-document creation, each child POST, blocker PATCH, and authorization receipt creation. Every replay must converge to the same five issue IDs and one receipt.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_program -v`

Expected: FAIL because `milestone2.program` and `program_execution_policy` do not exist.

- [ ] **Step 3: Add the child execution policy**

```python
def program_execution_policy(developer_agent_id, validator_agent_id, reviewer_agent_id, *, qa_agent_id=None):
    agents = [_agent_id(value) for value in (developer_agent_id, validator_agent_id, reviewer_agent_id)]
    if qa_agent_id is not None:
        agents.append(_agent_id(qa_agent_id))
    if len(set(agents)) != len(agents):
        raise ValueError("Developer, validator, Reviewer and QA must be distinct Paperclip agents")
    stages = [
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[1]}]},
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[2]}]},
    ]
    if qa_agent_id is not None:
        stages.append({"type": "review", "participants": [{"type": "agent", "agentId": agents[3]}]})
    return {"mode": "normal", "commentRequired": True, "maxReviewRounds": 3, "stages": stages}
```

`classify_task` maps only validated contract fields. Read-only work is not started in an agent runtime and does not allocate a workspace; small, low-risk, non-user-facing changes use the reduced verification profile but retain independent review; every other code change uses the full profile and isolated workspace. Classification never interprets free-form prose. This policy is usable only when `program.py` has verified the owner-created program authorization receipt. The existing `engineering_execution_policy` remains unchanged.

- [ ] **Step 4: Implement canonical digest and idempotent submission**

```python
def authorization_digest(program):
    value = {"program_id": program["program_id"], "base_revision": program["base_revision"],
             "authorization": program["authorization"], "waves": program["waves"]}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def wave_request_key(program, wave):
    return f"{program['request_key']}:{wave['id']}"
```

`submit_program` must:

1. validate the program and live project/agent scope;
2. POST an idempotent backlog parent issue using `program.request_key`;
3. PUT an `authorization` issue document containing canonical JSON plus the digest;
4. POST one owner-attributed receipt line `Authorized self-enhancement program sha256:<digest>` using a stable `clientRequestId`;
5. POST four child issues with `parentId`, stable per-wave request keys, the child policy, and the authorization document revision/digest in their description;
6. PATCH each child with `blockedByIssueIds` from the resolved prior waves;
7. set the first unblocked child to `todo` only when `--start` is supplied;
8. reject `--start` for any read-only classification rather than allocating a runtime;
9. return parent/child IDs, digest, and authoritative Paperclip URLs without secrets, and atomically write the same object when `--output` is supplied.

Before accepting an existing object on replay, compare its project, parent, title, request key, document digest, blockers, and policy. A conflict stops; it is never overwritten.

- [ ] **Step 5: Implement bounded status readback**

```python
def read_program_status(client, parent_id, company_id):
    _, parent = client.request("GET", f"/api/issues/{parent_id}")
    _, issues = client.request("GET", f"/api/companies/{company_id}/issues?projectId={parent['projectId']}")
    children = [row for row in issues if row.get("parentId") == parent_id]
    return {"parentId": parent_id, "status": parent.get("status"),
            "waves": [{"id": row["id"], "identifier": row.get("identifier"),
                       "status": row.get("status"), "blockedByIssueIds": row.get("blockedByIssueIds") or []}
                      for row in sorted(children, key=lambda row: row["title"])]}
```

Reject cross-company rows, more than eight children, duplicate IDs, unexpected child titles, or missing authorization document/digest.

- [ ] **Step 6: Add the concrete program manifest and CLI documentation**

The manifest uses the current committed revision and the exact four wave definitions from `autonomy/policies/self-enhancement.v1.yaml`. It allows no remote actions. Document dry-run, submit, start, replay, status, and `--output` in `milestone2/README.md`. Submission requires the private operator state containing the owner identity and board credential; reject agent/run identities and never copy that state into a task description, document, workspace, or runtime environment.

- [ ] **Step 7: Run tests and commit**

Run: `python -m unittest tests.test_program tests.test_paperclip_policy tests.test_task_cli -v`

Expected: PASS.

Run: `python -m milestone3.check`

Expected: PASS.

```bash
git add milestone1/paperclip_policy.py milestone2/program.py milestone2/tasks/self-enhancement-program.json milestone2/README.md tests/test_program.py
git commit -m "feat: submit one-authorized enhancement programs"
```

### Task 3: Capability manifests, admission, and diagnostic aggregation

**Files:**
- Create: `autonomy/capabilities/providers.v1.yaml`
- Create: `milestone2/capabilities.py`
- Create: `tests/test_capabilities.py`
- Modify: `autonomy/capabilities/README.md`
- Modify: `milestone2/program.py`

**Interfaces:**
- Consumes: wave required/optional capability IDs and externally supplied component probes.
- Produces: `assess(required, optional, manifests, health) -> dict` and `python -m milestone2.capabilities doctor`.

- [ ] **Step 1: Write failing admission and degradation tests**

```python
def test_required_unhealthy_blocks_and_optional_unhealthy_degrades(self):
    blocked = assess(["repo.write"], ["knowledge.search"], manifests(), {"paperclip": "down", "opensearch": "down"})
    self.assertEqual("blocked", blocked["status"])
    degraded = assess(["repo.read"], ["knowledge.search"], manifests(), {"paperclip": "healthy", "opensearch": "down"})
    self.assertEqual("degraded", degraded["status"])
    self.assertEqual(["knowledge.search"], degraded["unavailable_optional"])

def test_unknown_capability_never_falls_back_to_prompt_permission(self):
    with self.assertRaisesRegex(ValueError, "unknown capability"):
        assess(["cloud.superuser"], [], manifests(), {})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_capabilities -v`

Expected: FAIL because the provider manifest and evaluator do not exist.

- [ ] **Step 3: Add provider manifests**

Each manifest entry contains exactly:

```yaml
- capability: knowledge.search
  provider: opensearch-mcp
  effect: read
  operations: [bounded_search]
  health_probe: opensearch-mcp
  degradation: optional_unavailable
  max_result_bytes: 24000
  status: active
```

Include the active capabilities needed by the four waves. Disabled capabilities remain disabled and are never admitted.

- [ ] **Step 4: Implement aggregation and CLI**

```python
def assess(required, optional, manifests, health):
    catalog = {item["capability"]: item for item in manifests}
    unknown = (set(required) | set(optional)) - set(catalog)
    if unknown:
        raise ValueError(f"unknown capability: {sorted(unknown)}")
    unavailable_required = sorted(c for c in required if not _healthy(catalog[c], health))
    unavailable_optional = sorted(c for c in optional if not _healthy(catalog[c], health))
    status = "blocked" if unavailable_required else "degraded" if unavailable_optional else "ready"
    return {"schemaVersion": 1, "status": status,
            "unavailable_required": unavailable_required,
            "unavailable_optional": unavailable_optional,
            "providers": sorted({catalog[c]["provider"] for c in required + optional})}

def _healthy(manifest, health):
    return manifest["status"] == "active" and health.get(manifest["health_probe"]) == "healthy"
```

The doctor command reads component-owned JSON probe results from explicit files or stdin, emits one machine-readable aggregate plus a concise text view, and never prints credentials or calls paid model providers. Add a conformance test that every active provider declares the same logical request/result fields for its advertised operation; a provider-specific field may be optional but cannot silently replace a canonical one.

- [ ] **Step 5: Gate program start**

Before setting the first child to `todo`, `program.py` calls `assess`. `blocked` leaves all children in backlog and returns exit 2. `degraded` is stored in the parent authorization document and child context; it may start only if every unavailable capability is optional.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest tests.test_capabilities tests.test_program -v`

Expected: PASS.

```bash
git add autonomy/capabilities/providers.v1.yaml autonomy/capabilities/README.md milestone2/capabilities.py milestone2/program.py tests/test_capabilities.py
git commit -m "feat: gate programs on capability health"
```

### Task 4: Progressive context and provider-neutral evidence packs

**Files:**
- Create: `autonomy/knowledge/sources.v1.yaml`
- Create: `milestone3/context.py`
- Create: `tests/test_context.py`
- Modify: `milestone2/program.py`
- Modify: `autonomy/projects/examples/ai-factory.v1.yaml`

**Interfaces:**
- Consumes: context query plan, source adapters, project overlay, current Git revision, and total byte/token budget.
- Produces: `build_evidence_pack(request: dict, adapters: dict[str, SourceAdapter]) -> dict` and a persisted evidence-pack issue document per wave.

- [ ] **Step 1: Write failing evidence-pack tests**

```python
def test_pack_preserves_freshness_citations_and_total_budget(self):
    request = sample_request(max_bytes=900, max_tokens=225)
    pack = build_evidence_pack(request, {"git-docs": FakeSource(fresh=True), "memory": FakeSource(fresh=False)})
    self.assertLessEqual(pack["total_bytes"], 900)
    self.assertTrue(all(item["citation"] and item["source_uri"] for item in pack["items"]))
    self.assertEqual("historical", pack["items"][-1]["authority"])

def test_required_source_failure_blocks_but_optional_failure_is_visible(self):
    with self.assertRaisesRegex(EvidenceUnavailable, "git-docs"):
        build_evidence_pack(sample_request(required=["git-docs"]), {"git-docs": BrokenSource()})
    pack = build_evidence_pack(sample_request(optional=["memory"]), {"memory": BrokenSource()})
    self.assertEqual([{"source": "memory", "status": "unavailable"}], pack["degraded_sources"])
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_context -v`

Expected: FAIL because `milestone3.context` does not exist.

- [ ] **Step 3: Define source contracts**

`sources.v1.yaml` defines `git`, `opensearch-git-docs`, and `mempalace` with source identity, authority, read/write class, supported operations, citation fields, freshness method, result bounds, projection role, and degradation rule. No connection URL or credential is stored in Git.

- [ ] **Step 4: Implement the adapter protocol and pack builder**

```python
class SourceAdapter(Protocol):
    def query(self, *, text: str, filters: dict, max_hits: int, max_bytes: int) -> list[dict]: ...
    def verify(self, item: dict) -> dict: ...

class EvidenceUnavailable(RuntimeError):
    pass

def build_evidence_pack(request, adapters):
    selected, degraded, used = [], [], 0
    for query in request["queries"]:
        adapter = adapters.get(query["source"])
        if adapter is None:
            if query["required"]:
                raise EvidenceUnavailable(query["source"])
            degraded.append({"source": query["source"], "status": "unavailable"})
            continue
        try:
            rows = adapter.query(text=query["text"], filters=query["filters"],
                                 max_hits=query["max_hits"], max_bytes=query["max_bytes"])
        except Exception as exc:
            if query["required"]:
                raise EvidenceUnavailable(query["source"]) from exc
            degraded.append({"source": query["source"], "status": "unavailable"})
            continue
        for row in rows:
            verified = adapter.verify(row)
            size = len(verified["text"].encode("utf-8"))
            if used + size > request["total_budget"]["max_bytes"]:
                break
            selected.append(verified)
            used += size
    canonical = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()
    return {"schemaVersion": 1, "items": selected, "degraded_sources": degraded,
            "total_bytes": used, "estimated_tokens": (used + 3) // 4,
            "sha256": hashlib.sha256(canonical).hexdigest()}
```

Deduplicate by `(source_system, source_id, source_version, content_sha256)`, prefer canonical/current evidence over historical memory, and reject cross-project results before budgeting.

- [ ] **Step 5: Persist one evidence pack per wave**

During program submission, build and PUT an `evidence-<wave-id>` issue document before that child starts. The child description contains only the document ID/revision, digest, source summary, and budget—not raw unbounded results. A new run re-verifies current Git before use.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest tests.test_context tests.test_memory tests.test_retrieval_eval -v`

Expected: PASS.

```bash
git add autonomy/knowledge/sources.v1.yaml autonomy/projects/examples/ai-factory.v1.yaml milestone3/context.py milestone2/program.py tests/test_context.py
git commit -m "feat: compose bounded evidence packs"
```

### Task 5: Verification contracts, external evidence, and outcome reports

**Files:**
- Create: `autonomy/evals/verification.v1.json`
- Create: `milestone3/verification.py`
- Create: `milestone2/outcome_report.py`
- Create: `tests/test_verification.py`
- Create: `tests/test_outcome_report.py`
- Modify: `milestone2/program.py`
- Modify: `milestone2/scorecard.py:77-225`

**Interfaces:**
- Consumes: a Git-owned verification profile, candidate commit/tree, command runner, Paperclip review state, and optional external CI/review records.
- Produces: `run_contract(...) -> dict`, `validate_candidate_lineage(...) -> list[str]`, and `render_markdown(report) -> str`.

- [ ] **Step 1: Write failing verification and identity tests**

```python
def test_required_check_failure_and_missing_check_block_digest(self):
    digest = run_contract(full_contract(), ROOT, runner=FakeRunner({"unit": 1}))
    self.assertEqual("failed", digest["status"])
    self.assertEqual(["unit"], digest["failed_checks"])
    digest = run_contract(full_contract(), ROOT, runner=FakeRunner({}))
    self.assertEqual(["unit", "git-diff"], digest["missing_checks"])

def test_candidate_identity_must_match_review_and_external_evidence(self):
    report = sample_outcome(candidate_commit="a" * 40)
    report["review"]["candidate_commit"] = "b" * 40
    self.assertIn("review candidate mismatch", validate_candidate_lineage(report))
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_verification tests.test_outcome_report -v`

Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Add full and reduced verification profiles**

```json
{
  "schemaVersion": 1,
  "profiles": {
    "ai-factory-full": {
      "checks": [
        {"id": "git-diff", "argv": ["git", "diff", "--check"], "timeoutSeconds": 60, "required": true},
        {"id": "unit", "argv": ["python", "-m", "milestone3.check"], "timeoutSeconds": 900, "required": true}
      ]
    },
    "ai-factory-docs": {
      "eligibleChangeTypes": ["documentation"],
      "checks": [
        {"id": "git-diff", "argv": ["git", "diff", "--check"], "timeoutSeconds": 60, "required": true}
      ]
    }
  }
}
```

Reduced verification is valid only when every changed path is documentation and the program wave explicitly selects `ai-factory-docs`.

- [ ] **Step 4: Implement safe execution and compact digest**

```python
def run_contract(contract, root, *, runner=subprocess.run):
    results = []
    for check in contract["checks"]:
        completed = runner(check["argv"], cwd=root, capture_output=True,
                           timeout=check["timeoutSeconds"], shell=False)
        results.append({"id": check["id"], "exit_code": completed.returncode,
                        "stdout_sha256": sha256(completed.stdout).hexdigest(),
                        "stderr_sha256": sha256(completed.stderr).hexdigest()})
    failed = [row["id"] for row in results if row["exit_code"] != 0]
    return {"schemaVersion": 1, "status": "failed" if failed else "passed",
            "failed_checks": failed, "missing_checks": [], "results": results}
```

Reject shell strings, absolute working directories, path escapes, duplicate check IDs, timeouts over 1800 seconds, and environment values not in an explicit allowlist. Store full stdout/stderr as artifacts; the digest carries hashes, bounded excerpts, and references.

- [ ] **Step 5: Build deterministic outcome reports**

`outcome_report.py` accepts only validated fields and renders sections in this fixed order: Objective, Candidate, Changes, Verification, Independent Review, External Evidence, Authorization, Knowledge Impact, Deferred Findings, Metrics, Unresolved Items, Rollback, Next Disposition.

```python
def validate_candidate_lineage(report):
    expected = report["candidate"]["commit"]
    errors = []
    for label in ("verification", "review"):
        if report[label]["candidate_commit"] != expected:
            errors.append(f"{label} candidate mismatch")
    for row in report.get("external_evidence", []):
        if row["candidate_commit"] != expected:
            errors.append("external evidence candidate mismatch")
    return errors
```

Extend `scorecard.py` only to link the new report/digest coverage; do not infer correctness or fabricate missing costs.

- [ ] **Step 6: Attach contract and report references to each wave**

`program.py` stores a `verification-contract` document before a child starts and an `outcome` document after authoritative status shows all agent stages complete. A failed or divergent digest prevents the next blocked wave from becoming runnable.

- [ ] **Step 7: Run tests and commit**

Run: `python -m unittest tests.test_verification tests.test_outcome_report tests.test_scorecard tests.test_scorecard_format -v`

Expected: PASS.

Run: `python -m milestone3.check`

Expected: PASS.

```bash
git add autonomy/evals/verification.v1.json milestone3/verification.py milestone2/outcome_report.py milestone2/program.py milestone2/scorecard.py tests/test_verification.py tests/test_outcome_report.py
git commit -m "feat: add verification contracts and outcome reports"
```

### Task 6: Deferred findings, knowledge patches, retrieval regression, and resource lifecycle

**Files:**
- Create: `milestone3/maintenance.py`
- Create: `tests/test_maintenance.py`
- Modify: `milestone4/retrieval_eval.py:18-130`
- Modify: `tests/test_retrieval_eval.py:1-150`
- Modify: `autonomy/evals/git-docs-v1.json`

**Interfaces:**
- Consumes: validated finding, patch, resource, and retrieval-eval objects.
- Produces: `deduplicate_findings`, `preview_patch`, `apply_patch`, `plan_reclamation`, `quarantine_resources`, and expanded retrieval reports.

- [ ] **Step 1: Write failing maintenance safety tests**

```python
def test_patch_requires_current_hash_and_scoped_path(self):
    patch = sample_patch(path="docs/architecture/STATE_AND_STORAGE.md", expected_sha256="0" * 64)
    with self.assertRaisesRegex(ValueError, "source changed"):
        preview_patch(ROOT, patch)
    with self.assertRaisesRegex(ValueError, "outside assigned root"):
        preview_patch(ROOT, sample_patch(path="../outside.md"))

def test_cleanup_retains_referenced_or_foreign_resources(self):
    plan = plan_reclamation(sample_resources(), now=NOW, owned_root=ROOT / ".milestone0")
    self.assertEqual(["expired-unreferenced"], [row["id"] for row in plan["quarantine"]])
    self.assertEqual({"referenced", "foreign"}, {row["id"] for row in plan["retained"]})
```

Also test deferred-finding fingerprints deduplicate equivalent normalized evidence while preserving both origin task IDs.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_maintenance -v`

Expected: FAIL because `milestone3.maintenance` does not exist.

- [ ] **Step 3: Implement deferred findings and patch preconditions**

```python
def finding_fingerprint(finding):
    value = {key: finding[key] for key in ("project_id", "affected_components", "summary")}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def preview_patch(root, patch):
    root = Path(root).resolve(strict=True)
    target = (root / patch["path"]).resolve(strict=True)
    if root not in target.parents:
        raise ValueError("patch target is outside assigned root")
    original = target.read_bytes()
    if hashlib.sha256(original).hexdigest() != patch["expected_sha256"]:
        raise ValueError("knowledge source changed")
    text = original.decode("utf-8")
    if text.count(patch["old_text"]) != 1:
        raise ValueError("patch anchor must match exactly once")
    updated = text.replace(patch["old_text"], patch["new_text"], 1)
    return {"path": patch["path"], "before_sha256": patch["expected_sha256"],
            "after_sha256": hashlib.sha256(updated.encode()).hexdigest(), "updated_text": updated}
```

`apply_patch` requires a previously generated preview with matching before/after hashes, writes only inside the assigned task workspace, and returns an audit record. It does not commit, publish, or reindex automatically.

- [ ] **Step 4: Implement recoverable resource quarantine**

`plan_reclamation` accepts only resource records whose paths resolve below a declared AI Factory-owned root. A resource is reclaimable only when expired, reproducible or recoverable, unreferenced, and not protected. `quarantine_resources` atomically renames approved paths into `<owned-root>/quarantine/<plan-digest>/` and writes a manifest. It never recursively deletes.

- [ ] **Step 5: Expand retrieval evaluation without replacing the existing runner**

Add `queryType`, `expectedSources`, `requiredAuthority`, and `requireFresh` to judged cases. Preserve current `relevantPaths` compatibility for schema version 1; schema version 2 reports top-1/3/5 recall, reciprocal rank, stale hits, missing citations, and authority violations. Query results remain project-scoped and bounded.

- [ ] **Step 6: Run tests and commit**

Run: `python -m unittest tests.test_maintenance tests.test_retrieval_eval -v`

Expected: PASS.

Run: `python -m milestone3.check`

Expected: PASS.

```bash
git add milestone3/maintenance.py milestone4/retrieval_eval.py autonomy/evals/git-docs-v1.json tests/test_maintenance.py tests/test_retrieval_eval.py
git commit -m "feat: add safe maintenance and retrieval regression"
```

### Task 7: Canonical operational skill packages

**Files:**
- Create: `autonomy/skills/repository-preflight/SKILL.md`
- Create: `autonomy/skills/repository-preflight/ai-factory.yaml`
- Create: `autonomy/skills/verified-commit/SKILL.md`
- Create: `autonomy/skills/verified-commit/ai-factory.yaml`
- Create: `autonomy/skills/publication-status/SKILL.md`
- Create: `autonomy/skills/publication-status/ai-factory.yaml`
- Create: `autonomy/skills/review-resolution/SKILL.md`
- Create: `autonomy/skills/review-resolution/ai-factory.yaml`
- Create: `autonomy/skills/deferred-finding/SKILL.md`
- Create: `autonomy/skills/deferred-finding/ai-factory.yaml`
- Create: `autonomy/skills/scoped-audit/SKILL.md`
- Create: `autonomy/skills/scoped-audit/ai-factory.yaml`
- Create: `tests/test_operational_skills.py`
- Modify: `autonomy/skills/README.md`
- Modify: `autonomy/projects/examples/ai-factory.v1.yaml`

**Interfaces:**
- Consumes: existing deterministic commands and capabilities.
- Produces: six Agent Skills packages that describe procedures but never grant runtime authority.

- [ ] **Step 1: Write failing package tests**

```python
SKILLS = ("repository-preflight", "verified-commit", "publication-status",
          "review-resolution", "deferred-finding", "scoped-audit")

def test_every_operational_skill_has_portable_markdown_and_valid_sidecar(self):
    for name in SKILLS:
        directory = ROOT / "autonomy" / "skills" / name
        self.assertTrue((directory / "SKILL.md").is_file())
        sidecar = yaml.safe_load((directory / "ai-factory.yaml").read_text(encoding="utf-8"))
        validate("skill-sidecar", sidecar)
        self.assertEqual(name, sidecar["skill"])
        self.assertNotIn("runtime_grants", sidecar)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_operational_skills -v`

Expected: FAIL because the packages do not exist.

- [ ] **Step 3: Author the six bounded skills**

Every `SKILL.md` contains: trigger/intent, prerequisites, read-only preflight, exact existing command, expected evidence, failure recovery, authorization boundary, and related skill. Reuse these commands rather than spelling manual replacements:

```text
python -m milestone2.task
python -m milestone2.publish preflight
python -m milestone2.publish publish
python -m milestone3.check
python -m milestone2.program status
```

`publication-status` is read-only unless an operator supplies the existing exact publication approval inputs. `review-resolution` never dismisses findings without candidate-linked evidence. `deferred-finding` emits the Task 6 contract and does not create a full task automatically.

- [ ] **Step 4: Add sidecars and project allowlist**

Use `schema_version: 1`, `skill_version: 0.1.0`, `lifecycle: experimental`, exact roles, required/optional/denied capabilities, and eval refs. Reviewer skills deny `repo.write` and `repo.merge`; publication remains operator-only and does not receive an agent runtime grant.

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest tests.test_operational_skills tests.test_milestone1_contracts -v`

Expected: PASS.

```bash
git add autonomy/skills autonomy/projects/examples/ai-factory.v1.yaml tests/test_operational_skills.py
git commit -m "feat: add canonical operational skills"
```

### Task 8: Integrate, document, and prove the self-hosted lifecycle

**Files:**
- Modify: `milestone2/program.py`
- Modify: `milestone2/task.py:96-145`
- Modify: `milestone2/README.md`
- Modify: `milestone3/README.md`
- Modify: `autonomy/INDEX.md`
- Modify: `docs/implementation/IMPLEMENTATION_KICKOFF.md`
- Create: `milestone4/results/self-enhancement-v1-20261003.json` during the live proof
- Create: `tests/test_self_enhancement_cli.py`

**Interfaces:**
- Consumes: Tasks 1-7 and the existing V1 submission, check, review, scorecard, and publication commands.
- Produces: one discoverable CLI surface, one current-V1 bootstrap execution, and one successor-V1 program canary.

- [ ] **Step 1: Write failing black-box CLI tests**

```python
def test_help_is_credential_free_and_lists_whole_lifecycle_commands(self):
    result = subprocess.run([sys.executable, "-m", "milestone2.program", "--help"],
                            cwd=ROOT, capture_output=True, text=True)
    self.assertEqual(0, result.returncode)
    self.assertIn("submit", result.stdout)
    self.assertIn("status", result.stdout)
    self.assertIn("report", result.stdout)
    self.assertNotIn("AIF_PAPERCLIP_STATE", result.stderr)

def test_dry_run_performs_no_network_or_filesystem_write(self):
    result = run_cli("submit", "--program", PROGRAM, "--workflow", WORKFLOW, "--dry-run")
    self.assertEqual(0, result.returncode)
    self.assertEqual([], fixture.requests)
    self.assertEqual(before, snapshot_tree(TEMP_ROOT))
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_self_enhancement_cli -v`

Expected: FAIL until the final command surface is wired.

- [ ] **Step 3: Complete command wiring and documentation**

Expose `submit`, `status`, `doctor`, `evidence`, `verify`, `report`, and `maintenance-preview` through documented module commands. Keep mutating operations on their owning modules rather than building a second all-powerful CLI. `milestone2.task` prints a pointer to `milestone2.program` for program work.

Document the actual lifecycle as one command sequence:

```powershell
New-Item -ItemType Directory -Force -Path '.milestone0/self-enhancement' | Out-Null
python -m milestone2.capabilities doctor --output .milestone0/self-enhancement/health.json
python -m milestone2.program submit --workflow .milestone0/self-enhancement/workflow.json --program milestone2/tasks/self-enhancement-program.json --health .milestone0/self-enhancement/health.json --output .milestone0/self-enhancement/submission.json --start
$program = Get-Content -Raw -LiteralPath '.milestone0/self-enhancement/submission.json' | ConvertFrom-Json
python -m milestone2.program status $program.parentId
python -m milestone2.program report $program.parentId --output .milestone0/self-enhancement/outcome.md
python -m milestone3.check
```

The docs must state that `AIF_PAPERCLIP_STATE` already points to the current private operator state, and that `.milestone0/self-enhancement/workflow.json` contains the admitted current V1 project and distinct agent IDs. Both are ignored local inputs prepared once by the current operator, not additional approval steps, and neither may enter Git or a runtime workspace.

- [ ] **Step 4: Run the complete offline verification**

Run: `python -m milestone3.check`

Expected: all Python tests pass with only documented opt-in live skips.

Run: `node --test milestone0/fixtures/paperclip/validation-agent.test.mjs milestone1/fixtures/context-enricher-plugin/context.test.mjs milestone1/fixtures/git-doc-validator-identity.test.mjs milestone1/fixtures/git-doc-validator.integration.test.mjs milestone1/fixtures/git-handoff.test.mjs`

Expected: PASS.

- [ ] **Step 5: Execute the bootstrap through current V1**

Submit one current-V1 issue whose description references this spec and plan and whose allowed paths are exactly the files listed in Tasks 1-8. Use the existing workflow:

```text
Developer -> deterministic Validator -> independent Reviewer -> conditional QA -> one final owner integration approval
```

The Developer follows all plan tasks in one isolated workspace and commits after each task. Validator runs the pinned suite against the final candidate. Reviewer checks every task commit plus the final combined diff. QA exercises the public CLI help/dry-run/status/report behavior without credentials. Record any operator assistance explicitly.

- [ ] **Step 6: After approved integration, run the successor-V1 canary**

Use the newly implemented operator command once to create the four-wave program in a disposable/test Paperclip project. Verify:

- one parent, four children, correct blockers, and one authorization digest;
- no human approval stages on children;
- required-capability failure blocks before dispatch;
- an optional knowledge failure is visibly degraded;
- interruption/replay produces no duplicate issue, document, or receipt;
- verification/review identity drift blocks progression;
- the outcome report is reproducible;
- cleanup only quarantines an expired unreferenced factory-owned fixture.

Do not publish, merge, deploy, or restart services in the canary.

- [ ] **Step 7: Record truthful evidence and update the implementation ledger**

Write `milestone4/results/self-enhancement-v1-20261003.json` with exact source revision, parent/child IDs, run IDs, agent IDs, test counts, artifact digests, interruption receipt, known/unknown usage, and limitations. Update `IMPLEMENTATION_KICKOFF.md` without reopening M0-M4 or claiming production readiness.

- [ ] **Step 8: Commit final integration documentation**

```bash
git add milestone2/program.py milestone2/task.py milestone2/README.md milestone3/README.md autonomy/INDEX.md docs/implementation/IMPLEMENTATION_KICKOFF.md tests/test_self_enhancement_cli.py milestone4/results/self-enhancement-v1-20261003.json
git commit -m "docs: record V1 self-enhancement lifecycle proof"
```

## Execution Handoff

After this plan is approved, execute it through the current AI Factory V1 as one bootstrap issue. Do not implement Tasks 1-8 manually in this planning chat. The one final current-V1 integration approval is the bootstrap boundary; the successor-V1 canary then proves the approved one-authorization, no-per-wave-confirmation lifecycle without remote publication or deployment.
