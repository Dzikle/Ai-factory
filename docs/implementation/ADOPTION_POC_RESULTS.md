# Adoption spike POC results

**Run dates:** 2026-09-14 through 2026-09-15

**Host:** Windows 11, Node 24.14.0, pnpm 9.15.4 (package-selected),
Python 3.13/3.14 through uv 0.12.8, Docker 29.1.3. Go was not installed.

Candidate checkouts were temporary and outside the AI Factory repository. Full
commit identifiers and decisions are in
[`../decisions/V1_ADOPTION_ARCHITECTURE.md`](../decisions/V1_ADOPTION_ARCHITECTURE.md).
The tests below are seam probes, not substitutes for the Milestone 0
production-like acceptance gates.

## Paperclip

After dependency installation in a short checkout path:

```powershell
pnpm exec vitest run `
  server/src/__tests__/issues-checkout-wakeup.test.ts `
  server/src/__tests__/adapter-session-codecs.test.ts `
  server/src/modules/wake-queue/domain/context.test.ts `
  server/src/services/recovery/review-path-recovery.test.ts `
  --reporter=dot
```

Result: 4 files, 26 tests passed.

```powershell
pnpm exec vitest run `
  server/src/__tests__/issue-stale-execution-lock-routes.test.ts `
  server/src/__tests__/recovery-stale-issue-lock-sweep.test.ts `
  --reporter=dot
```

Result on the final verification run: 2 files and 26 tests passed. An earlier
run had 11 tests pass, 15 host-skipped, and the embedded-Postgres suite time out
during `beforeAll`; startup/fault behavior therefore remains a Milestone 0
production-like fault-injection gate rather than being inferred from unit tests.

Installation observations:

- the long temporary path failed with `ENAMETOOLONG` in pnpm's patched ACP path;
- a short path passed that point but source postinstall failed without Windows
  symlink privilege, and an optional `cpu-features` native build could not find a
  compiler;
- enough dependencies linked to run the targeted unit/integration tests;
- V1 therefore targets a pinned supported container/server deployment, not a
  Windows source install.

## Agent Skills

From `agentskills/agentskills`:

```powershell
$skills = '<ai-factory>/docs/implementation/pocs/agent-skills/.agents/skills'
uv run --project skills-ref skills-ref validate "$skills/repository-discovery"
uv run --project skills-ref skills-ref validate "$skills/code-review"
uv run --project skills-ref skills-ref read-properties "$skills/repository-discovery"
uv run --project skills-ref skills-ref to-prompt `
  "$skills/repository-discovery" "$skills/code-review"
```

Result: both skills valid; namespaced metadata parsed; the prompt-catalog adapter
listed both names/descriptions/locations from the same canonical packages.

## Official OpenSearch MCP server

```powershell
uv run --python 3.13 pytest -q `
  tests/tools/test_tools.py::TestTools::test_get_index_mapping_tool `
  tests/tools/test_tools.py::TestTools::test_search_index_tool `
  tests/tools/test_tool_filters.py::TestAllowWriteCategories::test_allow_write_false_removes_write_only_tools `
  tests/opensearch/test_response_size_limiting.py::TestIntegrationScenarios::test_size_limit_calculation

uv run --python 3.13 pytest -q `
  tests/tools/test_tool_generator.py::TestToolGenerator::test_process_body
```

Result: 5 tests passed. The msearch test proved alternating JSON-array conversion
to newline-terminated NDJSON. Tests emitted Pydantic deprecation warnings and an
unknown pytest `timeout` configuration warning; neither changed the result.

A live OpenSearch cluster was not started for this bounded spike. Milestone 0
must prove index aliases, filtered hybrid DSL, `_msearch`, least-privilege users,
response bounds, and complete delete/rebuild against the pinned OpenSearch image.

## MemPalace

```powershell
uv run --python 3.13 pytest -q `
  tests/mcp/test_kg.py::TestKGTools::test_kg_supersede `
  tests/mcp/test_kg.py::TestKGTools::test_kg_add_forwards_source_provenance `
  tests/mcp/test_read_tools.py::TestReadTools::test_status_sqlite_exact_backend_has_no_hnsw_fields
```

Result: 3 tests passed. These directly cover temporal supersession, persisted
source provenance, and the exact-backend fallback used in the adoption argument.

## CodeGraphContext

```powershell
uv run --python 3.14 --extra dev pytest -q `
  tests/unit/parsers/test_java_parser.py `
  tests/unit/parsers/test_typescript_parser.py `
  tests/integration/test_watcher_live_events.py
```

Result: 32 passed, 1 skipped.

```powershell
uv run --python 3.14 --extra dev pytest -q `
  tests/unit/languages/test_go_cyclomatic_complexity.py
```

Result: 1 passed.

An attempted full golden index/export on Windows failed before indexing because
the Ladybug C API shared library was unavailable. The test's `-k go` expression
also matched every `test_language_golden` parameter, so all 21 golden cases
reported the same backend initialization failure; these are not counted as
parser failures. Milestone 0 uses the upstream Linux container/backend and must
measure an actual representative graph before admission.

## SWE-ReX

The host-local `LocalDeployment` import failed on Windows because the installed
`pexpect` module has no `spawn`. The Docker client initially failed because
`aiohttp` is imported but absent from the evaluated package dependencies. With
`aiohttp` injected only for the POC, the following flow succeeded:

```text
build upstream tests/swe_rex_test.Dockerfile as ai-factory-swerex-poc:1.4.0
DockerDeployment(image=..., pull="never").start()
runtime.execute(["sh", "-lc", "printf 42"])
is_alive()
stop()
```

Observed result:

```json
{"stdout":"42","exit_code":0,"alive":true}
```

Rich logging also emitted Windows code-page errors for an emoji prefix. The
successful container command proves the basic abstraction; the packaging and
duplicate-lifecycle findings support deferral rather than V1 adoption.

## Source-only evaluations

DBOS, ToolHive, LiteLLM, Symphony, and OpenHands were evaluated through current
source, tests, schemas, docs, releases, licenses, activity, and relevant issues.
No runtime POC was needed for DBOS because the selected architecture forbids a
concurrent workflow owner. Go was unavailable for ToolHive tests. LiteLLM was
not asked to proxy a native harness because that is explicitly outside its
selected boundary. Symphony and OpenHands are reference-only dependencies.
