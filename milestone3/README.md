# Milestone 3 — one useful memory

**Status: IN PROGRESS.** The supervised memory slice passes local regression and
real MemPalace/OpenSearch checks. The subsequent native coding task and final
owner-approved promotion must pass before this milestone closes.

## Implemented boundary

`memory.py` is policy and integration, not another memory engine. The existing
MemPalace service stores the complete versioned record and lesson text in one
logical drawer. OpenSearch's existing `ai_factory_docs` mapping receives only
metadata: identity, scope, lifecycle, digest, provenance and a MemPalace URI.
The existing Git projector filters `source_system=git`, so it does not reconcile
or overwrite these `source_system=mempalace` documents. No new index or service.

The trusted preparer searches at most three metadata candidates, reads the
authoritative drawer, checks status/review/retention, exact project/logical role,
content digest and source versions, and emits at most one 2,400-byte lesson.
Current checked-out Git bytes are hashed even if Git's `assume-unchanged` flag
hides changes. External provenance requires an explicit verifier; the local
Paperclip verifier checks the configured company, completed task and exact final
owner-approved decision. Any unavailable/malformed backend yields no advice.

```text
MemPalace record → metadata-only OpenSearch projection
                         ↓
trusted preparer → primary/source verification → bounded historical advice
                         ↓
Paperclip task description/run snapshot → original native adapter
                         ↓
independent tests → Reviewer → functional QA → owner approval
```

This is **supervised task preparation**, not a complete Context Resolver or an
automatic per-run memory refresh. A prepared task contains a historical snapshot;
prepare immediately before supervised dispatch, and re-prepare after any source
or memory change. Current task instructions and Git remain authoritative. No
queued/unattended freshness guarantee is claimed. Future run-time lookup must
use Paperclip-governed read-only MCP, not an agent-held MemPalace server token.

## First experience and proposed promotion

`fixtures/pinned-tests-lesson.json` is a reviewed capture input, not live memory
truth. It cites AIF-48's owner-approved decision and the committed Milestone 2
report: missing `jsonschema`/`PyYAML` caused repeated environment-only failures in
AIF-47/AIF-48. The live authority is MemPalace. The earlier incomplete wording
is retained as superseded history; a deliberately stale active OpenSearch
projection cannot reactivate it.

`tasks/pinned-check.json` proposes the smallest deterministic promotion: a
credential-free test entry point that checks the pinned dependencies before
running tests, or prints an actionable recovery command. The native Developer
may change only `milestone3/check.py` and `tests/test_check.py`. It cannot approve,
publish or merge its result. `fixtures/check-stage.mjs` reuses the established
Paperclip issue identity/committed-copy helpers for independent full-suite and
three black-box CLI QA checks; no separate stage state or scheduler.

## Local use

Use the existing pinned Python environment:

```powershell
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.cli --help
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.cli capture --lesson milestone3/fixtures/pinned-tests-lesson.json
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.cli project --drawer DRAWER_ID
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.cli recall --query 'Python test dependencies' --project ai-factory --role developer --task milestone3/tasks/pinned-check.json
```

Private inputs stay in the trusted preparer's environment: `AIF_MEMORY_TOKEN`,
optional `AIF_MEMORY_URL` (defaults to loopback port 18767), `AIF_PAPERCLIP_STATE`,
and the existing `AIF_DOCS_URL`, reader/writer user/password variables.
`AIF_DOCS_LOCAL_TEST=1` allows the existing self-signed **loopback-only** cluster.
Never place credentials in the fixture, task, report, agent configuration or
command-line arguments. Ordinary agents receive **no** MemPalace token or write
grant. The client-side writable flag is only an accident guard, not MCP security.

Capture is content-addressed/idempotent through MemPalace and verifies readback.
Do not replay old capture inputs after supersession: that operation fails readback
rather than reactivating history. Supersession requires a same-scope, distinct
successor with an explicit edge; matching completed transitions are idempotent
even if that successor is later superseded. Metadata projection is rebuildable
from each primary drawer; replay writes the same document, without a cursor DB.
Retention/review dates suppress retrieval; automated pruning is not implemented.

## Evidence — 2026-09-28

- Existing production MemPalace 3.9.0 image and offline embeddinggemma q8 cache
  were reused, with `sqlite_exact`, CPU/2 threads and 384 dimensions. Exact image,
  source and embedding snapshot pins remain in `milestone0/dependencies.lock.yaml`
  and `compose/mempalace-production-embedding.yaml`; no build or model download.
- Live current drawer: `drawer_ai-factory_engineering-lessons_6dd8217e3859401d9ca6aa20`;
  lesson SHA-256 `6e48bb8f31d90f395452cee7be3a9ca26489373ecb48ebe0fe6633d05d0f2e40`.
  Superseded predecessor: `drawer_ai-factory_engineering-lessons_7727ead0fc060c3126a908d0`.
  Both capture replay and supersession replay passed. Semantic search returned
  the real lesson; authoritative full-drawer read handled its two search chunks.
- Bounded recall: **1,253 UTF-8 bytes**, **314 estimated tokens** (bytes/4,
  not tokenizer/model billing). Wrong role/project, insufficient budget and the
  stale active predecessor projection produced zero lesson context.
- Actual MemPalace stop and actual OpenSearch stop each returned `degraded`,
  zero context, no credential details. Both restarted; AIF-48's native task,
  stage/decision identity and locks were unchanged. Source-byte/digest, review,
  expiry and malformed-response regressions are covered by deterministic tests.
- Independent review reproduced four edge cases; RED regressions preceded fixes
  for hidden dirty Git bytes, logical self-supersession, successor-status replay
  and malformed responses. Native-task use, provider token/cost accounting,
  approval and rollout/rollback are not yet claimed.

Later organizational retrieval-quality measurement and automatic freshness,
pruning, general projections and self-improvement are outside this first loop.
No performance/cost improvement is inferred from one retrieved lesson.
