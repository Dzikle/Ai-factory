# Milestone 3 — one useful memory

**Status: TRUSTED-LOCAL DEMONSTRATION COMPLETE (2026-09-29 local).** The owner
approved AIF-49's exact reviewed candidate; it is integrated into
`milestone1-contracts`. Fresh merged checks and isolated Git rollback/reapply
passed. This closes the supervised Milestone 3 loop, not full V1 or production
readiness. Milestone 4's first approved measurement slice is now integrated;
see [`../milestone4/README.md`](../milestone4/README.md) for its remaining gates.

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

## First experience and approved promotion

`fixtures/pinned-tests-lesson.json` is a reviewed capture input, not live memory
truth. It cites AIF-48's owner-approved decision and the committed Milestone 2
report: missing `jsonschema`/`PyYAML` caused repeated environment-only failures in
AIF-47/AIF-48. The live authority is MemPalace. The earlier incomplete wording
is retained as superseded history; a deliberately stale active OpenSearch
projection cannot reactivate it.

`tasks/pinned-check.json` specified the smallest deterministic promotion: a
credential-free test entry point that checks the pinned dependencies before
running tests, or prints an actionable recovery command. The native Developer
could change only `milestone3/check.py` and `tests/test_check.py`. It cannot approve,
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

## Self-enhancement lifecycle commands (V1)

Bounded context, verification, and maintenance operations live on their
owning modules; each is offline-safe unless stated otherwise.

```powershell
PYTHONPATH=/paperclip/m1-python-libs:$PWD python3 -m milestone3.context evidence --root . --program milestone2/tasks/self-enhancement-program.json --wave orchestration
PYTHONPATH=/paperclip/m1-python-libs:$PWD python3 -m milestone3.verification verify --contract .milestone0/self-enhancement/contract.json --root .
PYTHONPATH=/paperclip/m1-python-libs:$PWD python3 -m milestone3.maintenance maintenance-preview --root . --patch .milestone0/self-enhancement/patch.json
PYTHONPATH=/paperclip/m1-python-libs:$PWD python3 -m milestone3.check
```

`evidence` reads only the local Git checkout through bounded queries and
budgets. `verify` executes a validated contract (shell strings, absolute or
escaping working directories, duplicate check IDs, over-long timeouts, and
non-allowlisted environment values are rejected) and prints a compact digest
carrying hashes and excerpts, never full raw logs. `maintenance-preview`
dry-runs a knowledge patch: stale hashes and out-of-root targets are
rejected before anything is written.

## Evidence — 2026-09-28

- Existing production MemPalace 3.9.0 image and offline embeddinggemma q8 cache
  were reused, with `sqlite_exact`, CPU/2 threads and 384 dimensions. Exact image,
  source and embedding snapshot pins remain in `milestone0/dependencies.lock.yaml`
  and `milestone0/compose/mempalace-production-embedding.yaml`; no build or model download.
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
  and malformed responses. The quota-blocked Codex re-review was not counted as
  a pass; the separate native OpenCode Reviewer completed foundation re-review.

### Native later-task receipt

AIF-49 (`b83ef44c-09ab-4c92-8265-c946d85986d9`) is **done, 4/4 gates**. The actual
owner approval was recorded at `2026-09-29T00:42:52.429Z`, decision
`ca59d628-e234-4314-bda2-7ec4b4855e2f`, after the user's explicit approval and
fresh verification of the unchanged candidate, independent receipts and stage.
Candidate `68344b66c24cd3b506b26b65c99915a892660641`, tree
`ec31f82baf2c07b39f90fe3634df6064b8cac286`, adds only `milestone3/check.py` and
`tests/test_check.py` over foundation `14e304d253a69c3258139f723505b81725c387b4`.
The exact candidate is retained in the integration history; the native task
branch is preserved unchanged for audit. The checker targets the existing
supported Python 3.11+ environment and installs nothing.

| Stage | Native run | Verified result |
| --- | --- | --- |
| Developer | `19a5a140-99ce-4ccc-a985-7ddf9489acb5` | Explicit handoff cites the retrieved memory ID/digest; observed RED, then seven check-command regressions passed. |
| Independent tests | `2d6807e3-b4f7-4c08-906e-d5eddcf9e9f5` | 100 tests run: 98 passed, two opt-in live tests skipped; isolated committed copy. |
| Reviewer | `64d300d9-8a85-40ce-8bbb-670510c75b76` | Approved exact commit/tree, including the full memory foundation against `1c41e40`; no remaining Important/Critical finding. |
| Functional QA | `ccda0fb8-9671-4d54-9916-628d1cc40395` | 3/3 credential-free black-box checks passed, including missing-dependency failure before tests. |

The coordinator independently reran the candidate through `python -m
milestone3.check` in an isolated committed copy: 100 tests, 98 passed/two skipped,
then 3/3 QA. Saved test/QA bytes match their comments and issue/run/agent/commit/
tree identities. SHA-256: tests
`24d18190a282f0084bef440d334bd24bae4ee34bcba4f18a3354a0fc92727631`;
QA `1c0e7fb1eaa67b82facbb8e34a7668a3d55eccbbec4b786902f9743e8387720d`.

The same Developer run durably stores the memory prompt/refs in
`contextSnapshot.paperclipIssue.description`; its separately verified canonical
Git enrichment artifact is 3,545 bytes, SHA-256
`f5e6765ad86fda524a3d83dbe1f01ca57cee0a4dbd2edc408ef0236441a0ad25`.
These are distinct sources: memory advice was prepared before submission, not
fetched by a new automatic runtime resolver. With zero live runs, an actual
controller restart preserved the task's approval state and complete run snapshot
exactly, and all three saved context/test/QA artifacts retained their digests.
Checkout/execution locks remain clear. The pre-approval combined task/run snapshot digest was:
`8fd230886cd64ac8def0c4949f4405707bbd47e32c92043966d78b3f16cbd861`.

Operational limits are explicit: Paperclip initially materialized the worktree
at the older `1c41e40` checkpoint. Enrichment stopped those attempts before
provider work; retries were paused and only the untouched task branch was
fast-forwarded to `14e304d`. One incorrectly shaped manual wake lacked its issue
payload and also stopped before provider work; the corrected native wake used
`payload.issueId`. No provenance check, participant or approval policy was removed.
All four successful handoffs retain Paperclip's known `cancelled/issue_reassigned`
run semantics; durable stage decisions and independently checked receipts qualify
them. Native provider usage/cost fields are **unavailable**, not zero. Developer
and Reviewer used the existing `opencode/muse-spark-1.3-contributor-free` bindings;
no measured token/cost saving is claimed. The one-lesson/three-candidate recall
limit can miss relevant lessons as history grows; broader retrieval evaluation
and role-aware candidate indexing remain later work.

### Approved integration and rollback — 2026-09-29

Candidate merge `dee3cf46833378d91b12f0c1ef5bea3fda300910` preserves the original
native commit. Feature integration `a46ec83bb2788b5d6cb297b7fd3004792f2c90ce` on
the original `milestone1-contracts` branch has tree
`91954fec6eded14d29a65a5a5b97aeafadc62985`; its first parent is the previously
accepted `1c41e40d47337b5418b87ed70c7292694c61a272`. The primary `main` checkout
is unchanged. The subsequent closure commit changes only the existing reports.

Fresh merged validation: `python -m milestone3.check` ran **100 tests: 98 passed,
two opt-in live tests skipped**; functional CLI QA **3/3**; existing native
context/committed-handoff/identity Node regressions **26/26**. Fixture syntax and
`git diff --check` passed. No skipped test is counted as live evidence; earlier
real-service and restart receipts above remain the integration evidence.

An ignored isolated Git copy exercised full-feature `git revert -m 1 a46ec83`
and reapplication. Revert restored the exact prior accepted tree
`ccdf74d49fe53d294d57cefecccc46c81a079f01`; reapply restored the exact integration
tree and reran the 100-test checker successfully (two skips). A second isolated
check reverted/reapplied just the promotion merge and matched the exact
pre-promotion foundation and accepted trees. The live branch, task and memory
were not rolled back during these checks.

For a **subsequently approved promotion-only backout**, use
`git revert -m 1 dee3cf46833378d91b12f0c1ef5bea3fda300910`, then validate and update
the acceptance report before deploying. This removes only the checker and its
seven tests, retaining the memory slice and durable task history. A whole-feature
backout uses `git revert -m 1 a46ec83bb2788b5d6cb297b7fd3004792f2c90ce`; reconcile
later report edits rather than force-resetting Git. Neither command is automatic
or authorization to erase MemPalace/Paperclip records. Deploy accepted Git changes
through the existing source checkout and one-shot document projector; no new
image, service, migration, scheduler or approval mechanism is introduced.

Live rollout at closure checkpoint `d7c869a9cbcb6c51532911501359a080bc165edb`
also passed: the existing Paperclip source checkout was clean on
`milestone1-contracts`, with matching workspace `repoRef`/`defaultRef` and zero
live runs. Its credential-stripped checker ran 100 tests (two skips). The
existing one-shot projector updated 49 canonical Git documents; reader-only
replay planned zero writes. Primary-verified memory recall still selected the
same current drawer and returned 1,253 bytes. This receipt-only update changes
no approved code; advance the same source/projection to the final receipt commit.

Next: Milestone 4's bounded measurement of accepted-task quality, context use,
latency and available model telemetry against a baseline. No Milestone 4
implementation is included in this approval.

Later organizational retrieval-quality measurement and automatic freshness,
pruning, general projections and self-improvement are outside this first loop.
No performance/cost improvement is inferred from one retrieved lesson.
