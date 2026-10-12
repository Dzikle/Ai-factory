# Plan persistence repair — 2026-10-12

## Scope and exact source

Owner-approved bounded, inline, source-only repair. No runtime, provider,
credential, task approval, database migration, image build/deployment, push or
merge. The deployed Factory and the historical AIF-84 plan remain unchanged.

- Paperclip baseline: `2d924f711cc2ecbe09dc5dace857862f7329a298`.
- Paperclip source: `884ca5586c4a15da5f0d76ee2cf9409d1e941f82`.
- Factory baseline: `093f4f56f8b7f42ff0de0d71c02be1b07ce078d7`.
- Factory source: `67aa4ab2ad44003514a38396d045147950605b9d`.
- Live Paperclip remains revision `3f1194caa926084d1862ac4ce8690841a690c5b0`,
  image `b1ed65f02e37`; these local fixes are not installed there.

## Defect and repair

Read-only smoke task AIF-84 completed its native run and saved a correct answer
in 76.426 seconds, but its `plan` revision could not be parsed as JSON. Paperclip's
document validator interpreted escaped newlines inside the canonical JSON body
as real line breaks. A no-write probe against the deployed compiled validator
confirmed valid input becoming invalid JSON.

Paperclip's `upsertIssueDocumentSchema` now validates a literal string with the
same 524,288-character limit. It preserves JSON escapes, code snippets, paths,
Unicode and actual line endings. Comment, task-description and thread-summary
newline normalization is unchanged. Document callers must supply actual desired
line breaks; a literal backslash-n is content, not a formatting instruction.
Storage, authorization, revision history and document format remain unchanged.

The Factory Orchestrator now performs a separate authoritative GET after PUT.
Before it marks analysis answered or assigns a Developer, the stored Markdown
document must have the acknowledged revision and exact canonical JSON body and
must parse. Missing, changed or corrupted storage blocks the transition. A
successful PUT echo alone is not enough. Existing valid plans retain semantic
replay compatibility, including legacy selection-audit absence. Corrupted old
plans fail closed without being overwritten or automatically repaired.

## Verification

| Check | Result |
| --- | --- |
| Baseline focused tests | Paperclip 30/30; Factory Orchestrator 35/35. |
| RED regressions | Paperclip two expected preservation failures; Factory four expected readback-guard failures. |
| Final focused GREEN | Paperclip 33/33; Factory Orchestrator 40/40; exit 0. |
| Complete pinned Factory check | 376 tests run, two optional skips, no failures; exit 0; 78.546 seconds. |
| Actual TypeScript validator → Python Orchestrator | Multiline/backslash/Unicode round trip, analysis completion and zero-write replay pass; no network or DB. |
| Linux actual validator | Exact string and JSON parse pass in a disposable `--rm --network none` container using the existing image and two read-only mounts; no controller volumes/credentials. |
| Shared package typecheck and real build | Both exit 0. |
| Complete Windows shared-package tests | Exit 1: 764 passed, nine failed, one unhandled error; 77 files; 40.16 seconds. |
| Paperclip root test attempt | Recorded separately below; not a whole-suite passing claim. |
| Scoped and staged whitespace checks | Exit 0. |

The unchanged shared-package failures are:

- `frontmatter-runner-contract.test.ts`: "keeps the standalone Runner parser and
  schema synchronized with production" (stale generated contract).
- `worktree-seed-source.test.ts`: "rejects a dangling config symlink instead of
  falling back to the named source" (EPERM); "fails closed when the declared
  config cannot be inspected" (ENOTDIR expectation); "rejects a dangling
  .paperclip symlink instead of falling back to the named source" (EPERM);
  "takes the named source when .paperclip is a symlink to a directory with no
  config" (EPERM).
- `worktree-port-registry.test.ts`: "does not reclaim a stale lock while its
  fallback ownership probe responds" (timeout); "reclaims an old lock after its
  owner process exits", "reclaims an old lock when its pid belongs to a different
  process", and "refreshes the lease while a synchronous critical section blocks
  the main thread" (rename EPERM). An additional rename rejection was unhandled.

The fresh `pnpm test:run` root attempt passed workspace-link preflight and started
real Vitest. It reached the explicit 180-second task budget without a final test
summary, assertion count or confirmed whole-suite exit. The watchdog stopped
only that attempt's process tree. This is incomplete verification, not a passing
run or an aggregate failure count. No new FAIL/case-summary lines were captured;
the complete shared-package failures above remain the fresh named evidence.
No claim is made that the previous run's 192 assertions are resolved. A subsequent
read-only dashboard health request still returned `ok`.

These failures were recorded, not fixed or skipped. The latest global typecheck
and build from the preceding repair stopped at missing Cargo and
capability-inventory parsing; they were not rerun here and are not green evidence.
The host retains its legacy pnpm metadata and Vite configuration warnings.

The cross-language probe initially decoded Node's UTF-8 output with Windows'
default encoding; explicitly selecting UTF-8 corrected that harness error. The
first disposable Linux probe omitted stdin attachment and did not run its
assertions; the rerun used `-i` and passed. Neither initial attempt is passing
product evidence. Helpers/logs remain in this task's ignored
`.superpowers/sdd/2026-10-12-plan-persistence/` areas, not sibling workspaces.

## Review and limitations

One read-only `plan_persistence_review` found no Critical, Important or Minor
defects in the four scoped source/test diffs and approved the source stage. It
independently passed eight focused in-memory Orchestrator cases; other results
above are implementer evidence. This is not merge, release or deployment approval.

Readback and issue PATCH remain separate requests. A concurrent document edit
after verification is not atomically prevented by this repair; the existing
status-version check protects issue state, not document revision. No transaction
or new API revision condition was added. Existing malformed-envelope validation
beyond this repair remains unchanged.

Actual database/concurrent persistence, repaired live smoke execution, deployed
artifact freshness, historical corrupt-record remediation, and UI/editor round
trips beyond the inspected API/storage paths are unverified here. Coding quality,
Tests/Reviewer/QA execution, provider fallback, provider admission, memory, costs,
security isolation and production readiness are outside this repair. No pending
AIF-82 approval or AIF-84 record was changed. Deployment and a fresh native smoke
test require separate authority and their own verification.
