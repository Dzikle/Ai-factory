# Native provider source verification — 2026-10-11

Current source checkpoint: the approved
[guard safety/feasibility stage](COMMANDCODE_GUARD_FEASIBILITY_2026-10-11.md)
hard-blocks Command Code execution and controller bindings, corrects secondary
path inspection, and reproduces native snapshot-filter/session-hook gaps offline.
Command Code, Cline and managed Claude remain unsupported. Current focused
verification is 150 tests plus 14 offline native-characterization cases after
the independent review-fix pass; broader
Paperclip checks remain non-green. No provider was enabled or deployed.
The source/support descriptions and review below are historical, not a usable
Command Code admission or approval of its unresolved native guard.

Follow-up: the [pinned containment audit](NATIVE_PROVIDER_CONTAINMENT_AUDIT_2026-10-11.md)
found two additional unresolved Important Command Code source-policy gaps after
the review below. That review is historical evidence, not approval of a currently
complete source contract. The revised design and its first source stage are now
approved; guard feasibility is still insufficient for qualification. The original
static audit ran no CLI or inference; the new offline harness executes only two
verified vendor functions, never the CLI entry point.

## Outcome and exact source

Reviewed disabled-by-default source candidate, not a release or live provider
approval. No native provider installation/login/inference, image build, push,
publication, production registration, controller rollout or admission was performed.
All three additional provider profiles remain disabled. Existing qualified Codex
fallback and historical OpenCode zero-work failure evidence are unchanged.

Paperclip branch `ai-factory/automatic-task-entry`:

- Baseline: `3f1194caa926084d1862ac4ce8690841a690c5b0`.
- Shared seams: `f913bcec27388703f18a91a68f7ca6da9a6b3688`.
- Cline package foundation: `0d51bb2a76ad08f87355737f27df40c3d0fe0050`.
- Command Code package: `6d02574a49886dc4d61df9141f6b601be9fc0662`.
- Controller admission: `3ab32d0ac0a648c5818279bf87f36c4bde8033d1`.
- Packaging: `3689694948d165646e7d57665f40dd09ab84d47b`.
- Reviewed safety corrections: `4665cb41ce3598429066fe91fc7ee4154abfd10b`.

Factory branch `milestone1-contracts`:

- Product baseline: `4d1c844d34e885d6262f839f1da08bcc7de8193f`.
- Approved implementation plan: `4283f43ded691e54a1a9b665aa9311ac2cc41615`.
- Routing: `83ab679b31d442c30e6e3da708426dbeaa73319b`.
- Operator: `f2272cba5182778b3a2ae50e9ac8d2c367b8cda6`.
- Reviewed preflight corrections: `de2c323ba4fd88bf8c5773231a78f46f1274e708`.

The documentation checkpoint containing this report follows these source commits;
its exact identity is obtained with `git log -1` rather than a self-referential hash.
Only local checkpoints were created. Historical task-helper completion ranges that
show identical BASE/HEAD were recorded before commits; the actual ranges above
supersede those bookkeeping artifacts, not their recorded test results.

## Independent source review and demonstrated corrections

`native_final_review` reviewed both scoped source ranges and their follow-up diffs.
Final verdict: approved with documented limitations; no remaining Critical or
Important findings in inspected corrections. An earlier reviewer exhausted its
usage without a completed verdict and is not counted as approval.

Initial Important findings were corrected with regression evidence: requested-model
cache fallback, uncontrolled Cline authority, typed post-turn authentication/quota/
entitlement failures, coding timeout bounds, unchanged/out-of-scope canary trees,
and accounting loss on policy restoration failure. Follow-up RED regressions
demonstrated three additional defects: Git status executing a clean filter before
config rejection, resumed ACPX retaining historical model options when fresh
metadata was omitted, and grants accepting a coding timeout above the fingerprinted
600-second authorization envelope. Their owning suites then passed after fixes.

Native sessions now require fresh backend config-option model evidence; missing
identity prevents inference, including reconnects. Public failed results remain
redacted without discarding completed usage/cost. Only the original availability
binding is revoked by typed authentication/quota/entitlement failure. The controller
captures a trusted empty canary baseline and verifies a clean changed single-commit
two-file candidate before stamping coding evidence. It rejects untrusted Git config
before any status filter can execute. These are source contracts, not live proofs.

The review retains one Minor limitation: busy same-key submit recovery requires
manual Paperclip inspection and retry after idle, using the same request key.
There is no automatic retry or alternate-provider selection.

## Fresh passing checks

Factory focused checks passed **63 tests**:

```powershell
& 'C:/Users/User/AppData/Roaming/uv/python/cpython-3.13-windows-x86_64-none/python.exe' -m unittest tests.test_native_provider_qualification tests.test_native_profile_contract tests.test_orchestrator tests.test_automatic_entry_setup
```

Factory full suite passed **371 tests, two skips**, exit 0:

```powershell
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m unittest discover -s tests
```

Pinned Factory handoff check also passed **371 tests, two skips**, exit 0
(134.911 seconds), with dependency versions checked first:

```powershell
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.check
```

Paperclip focused native/admission suite passed **145 tests in 19 files**, exit 0.
The helper command was:

```powershell
pwsh -NoProfile -File .superpowers/sdd/2026-10-11-native-provider-acp/task-4-verify.ps1
```

It ran only a disposable `docker run --rm --network none` using existing image
`b1ed65f02e37` (immutable digest
`sha256:b1ed65f02e37aaccd9566db0852d0440048aaf28f95fd86f94bd7b8109eb343a`),
with changed sources mounted read-only and no controller volumes or real provider
HOME. It used installed TypeScript/Vitest/esbuild directly, not online Corepack.
Adapter-utils built; server and Claude typechecked; both new plugins compiled with
browser CJS parser bundles. Test invocation inside that disposable environment:

```sh
node node_modules/vitest/vitest.mjs run --maxWorkers 1 --testTimeout 15000 \
  server/src/services/native-canary-source.test.ts \
  server/src/services/native-credential-generation.test.ts \
  server/src/services/native-profile-admission.test.ts \
  server/src/__tests__/native-profile-admission.test.ts \
  packages/adapters/claude-local/src/server/native-model-identity.test.ts \
  server/src/services/provider-bootstrap-fallback.test.ts \
  server/src/__tests__/heartbeat-native-runner-cancellation.test.ts \
  packages/adapter-utils/src/native-runtime-artifacts.test.ts \
  packages/adapter-utils/src/native-provider-contract.test.ts \
  packages/adapters/cline-local/src \
  packages/adapters/commandcode-local/src \
  packages/adapter-utils/src/native-provider-adapter.test.ts \
  packages/adapter-utils/src/acpx-engine/native-provider.test.ts
```

Each new plugin directory matched exactly `ui-parser.test.ts`,
`server/acp.test.ts`, `server/execution.test.ts`, and `server/test.test.ts`.
Both actual-wire model tests use a local fake ACP agent, not a provider CLI.

Shared regression helper passed **85 tests in nine files**, exit 0, including
Windows adapter-utils build/typecheck and the disposable Linux checks:

```powershell
pwsh -NoProfile -File .superpowers/sdd/2026-10-11-native-provider-acp/task-1-verify.ps1
```

Exact suite files: `packages/adapter-utils/src/native-provider-contract.test.ts`,
`packages/adapter-utils/src/published-exports.test.ts`, and under
`packages/adapter-utils/src/acpx-engine/`: `native-provider.test.ts`,
`execute-identity.test.ts`, `startup-cancellation.test.ts`, `operator-stop.test.ts`,
`run-fault-matrix.test.ts`, `session-reuse-store.test.ts`; plus
`server/src/adapters/plugin-loader.test.ts`. An initial rerun failed two wire tests
because the helper omitted their new fixture mount. Adding that read-only mount
produced the stated 85/85 pass. Counts overlap the 145-test run; do not add them.
Test harness budgets are 15 seconds/serial, without loosening runtime deadlines.

Packaging helper passed three Windows and three disposable Linux Node tests,
compiled both actual plugin exports, and executed registration twice against a
temporary HOME to confirm idempotency, exit 0:

```powershell
pwsh -NoProfile -File .superpowers/sdd/2026-10-11-native-provider-acp/task-6-verify.ps1
```

This is not production registration or an image build. Both repositories passed
`git diff --check` / staged whitespace checks. The generated catalogue content
changed incidentally during a broad build and was restored; it is not in the scoped
commit. Its normalized blob matches HEAD; index stat refresh is not a content change.

## Broader attempted checks — not passing release evidence

The required Paperclip handoff commands were attempted, not omitted:

- `pnpm -r typecheck`: exit 1; existing runner generated-protocol module errors and
  existing shared Unix `mkdir`/`cp` build commands fail on Windows. Changed server
  typecheck passes separately in the disposable Linux check; this does not make
  the recursive command green.
- `pnpm test:run`: exit 1, runner `spawnSync pnpm ENOENT` on Windows. The broad
  Vitest suite did not run to completion and is not claimed as passing.
- `pnpm build`: exit 1 at existing Unix shared build commands on Windows.
- `node --test scripts/native-provider-packaging.test.mjs scripts/acpx-patch-packaging.test.mjs`:
  19 tests, 17 passed, two failed: existing ACPX 0.13.1 patch blank-line validity
  and Windows server-staging `/C:/` URL pathname conversion. New packaging tests
  passed; the combined command did not.
- DB-backed `issue-stale-execution-lock-routes` and `budgets-service` attempts hit
  setup-hook timeouts; a root Linux attempt could not start embedded PostgreSQL
  as root. Skipped tests and failed hooks are not passing issue-override/DB proof.

No unrelated historical failures were repaired. Low disk prevented a new image
build/full Linux release exercise; the exact-image focused runs above are named
separately. Production database/controller resources and protected volumes were
not modified. CI owns `pnpm-lock.yaml`; it must be regenerated through CI before
a future frozen-lockfile build, not manually committed by this source task.

## Remaining implementation and owner gates

Cline's package foundation exists but **all managed launch is unsupported** until
an enforceable native home/project/tool containment contract is implemented.
Managed Claude dispatch is likewise unsupported; legacy unmanaged bootstrap is
unchanged. This checkpoint does not complete three usable provider integrations.
Command Code remains a compatibility candidate, not a qualified provider.

See [admission preparation and limits](NATIVE_PROVIDER_ADMISSION.md) and
[routing policy](NATIVE_PROVIDER_ROUTING.md). Actual candidate CLI enforcement,
authentication, quota, subscription entitlement, model behavior, native MCP tools,
coding correctness, independent Tests/Reviewer receipts, availability, restart/
restoration drills, billing/cost savings and production isolation were not proven
by the source reviewer or offline tests.

Task 7's source review/checkpoint is delivered with these limitations; the broader
release checks are not green and unsupported integrations remain incomplete.
Task 8 live login/inference/installation/build/publication/cutover requires separate
authorization, which has not been given. An approved source review does not grant
Paperclip admission or permission to begin that live work.

## Execution rulings and costs

- Reused approved feature checkouts to conserve disk; Paperclip isolation is
  branch-level rather than an additional worktree.
- Followed the repository's CI-owned lockfile rule instead of manually editing it;
  a future frozen-lockfile build depends on CI regeneration.
- Kept a separate ignored plan ledger per repository; exact review ranges require
  reconciliation across two records, corrected above.
- Trusted qualification phase only from protected controller context and recomputed
  effective binding; callers cannot self-request proof modes, requiring owner setup.
- Reused the shared normalization/redaction/execution kernel rather than adding a
  second runner; strict typed failures remain native-only and can reject candidates.
- Compiled browser CJS UI parsers because the external worker cannot evaluate ESM
  re-exports; there is one additional compiled artifact per plugin.
- Reused installed workspace dependency links and network-disabled disposable
  Linux layers with read-only source mounts; this avoids installs but does not prove
  a freshly resolved production dependency tree.
- Ran slow process tests serially with a 15-second test budget while preserving
  runtime deadlines; verification is slower and the initial timeout is not green.
- Used installed direct Node/TypeScript/Vitest entries after offline Corepack tried
  fetching pnpm; these runs do not exercise online package resolution.
- Preserved unsupported containment gates and delivered a limited source checkpoint
  instead of declaring release completion; Cline/managed Claude remain unusable and
  broader Paperclip checks still need a suitable environment.
- Retained this plan's ignored workspace/ledgers because the release completion
  contract is not met; they consume some local disk but preserve unfinished evidence.

Deferred Minor: busy same-key operator recovery remains manual inspection/retry
after idle, never a background retry or another generated request key.
