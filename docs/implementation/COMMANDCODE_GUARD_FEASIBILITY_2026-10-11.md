# Command Code guard feasibility — 2026-10-11

## Outcome

The approved source safety/feasibility stage is implemented. Command Code is
hard-blocked at adapter execution and current-binding resolution with
`native_permission_unsupported`; executable presence now reports unsupported.
Ordinary, capabilities, availability and coding phases cannot start a runtime,
rewrite probe settings or override the block with a readiness flag/receipt.
Obsolete adapter sessions are cleared. No new usage/cost total is fabricated.

Offline execution of two exact pinned vendor functions reproduces unsafe
snapshot-filter and session-hook behavior. The tested bare filter/hook approach
does not meet the required guard contract. This does not prove every possible
native integration impossible, and it is not a live exploit or provider
qualification. Command Code remains unsupported; Cline and managed Claude
remain unsupported under their existing gates. Unmanaged Claude bootstrap,
qualified Codex fallback and disabled provider profiles are unchanged.

No provider CLI entry point, login, model inference, image build/deployment, provider
enabling, live agent/task mutation, push, merge or registry publication occurred.
Protected controller/database containers, image pins, credentials, volumes,
backups and pending mobile owner approval were not changed.

## Authority and exact source

- [Approved design](../superpowers/specs/2026-10-11-commandcode-native-guard-design.md).
- [Approved inline plan](../superpowers/plans/2026-10-11-commandcode-guard-feasibility.md).
- [Original pinned-source audit](NATIVE_PROVIDER_CONTAINMENT_AUDIT_2026-10-11.md).
- P baseline: `4665cb41ce3598429066fe91fc7ee4154abfd10b`.
- Hard-block commit: `28151cf375125fc910cf4aea3af809844053bb68`.
- Offline characterization/secondary-anchor commit:
  `d569f6e0edc71cecba5399b3db68e2cea8b67b87`.
- Single review-fix commit:
  `6b7749429b16ca7c72b43f9177fce44d52cd8d9d`.
- F plan/approval record: `761804947bfb9912134e34bd2ef17140d7a0fd68`.

The task wrapper runs in F while product commits are in P; its identical F
BASE/HEAD completion ranges are bookkeeping, not P source provenance. The P
commit ranges above identify the actual changes.

The existing `command-code@1.79.2` tarball's integrity remains
`sha512-e7seLyyriUJtK5MArViSVRekCmRP5VCZrHgoURWayH7agAwvsE+nq+c0rt1dzVs/iD/lc5cMZLu9I0+SZnPORA==`.
No package was installed or upgraded. Bundle SHA-256:
`d976c2ad89f93a2b81af4d150dca99aeedfd679f15e8b8c032314e61e484da7b`.

The audit harness refuses missing, nonregular, symlink, oversized or changed
bundle/parser inputs. It parses only after bundle verification and imports the
hash-verified standalone Acorn bytes, not a path reopened after hashing.
Synthetic extraction tests reuse that verified parser instance. A regression
replaces a temporary copy of the original parser path after verification and
confirms extraction still uses the verified bytes without executing replacement
code. The real parser artifact is never changed.
Acorn `8.18.0` SHA-256:
`953573b8fdab71599749ea5f2b33d3e760c2116178f9423ee7458dbe39d59453`.
Selected function ranges are zero-based JavaScript source-character offsets,
end-exclusive, extracted unchanged by the parser:

- `createModHost`: `201088..209830`, SHA-256
  `6e17b0b2393aae50d691321b2354835f5403dbf91d6e748c7ed1d611c57422c1`.
- `anchorPathPattern`: `799463..799847`, SHA-256
  `4cc159b6831b21df74499ae0431954370d8d5e0480780938b24c3968b124863f`.

Only those vendor functions execute in the offline VM fixture. No ambient
process, require, fetch, timers, filesystem, shell or provider services are
supplied. String/WASM code generation is disabled; synchronous evaluation has a
one-second deadline and the Node test invocation a 30-second deadline. This is
trusted pinned-code characterization, not an OS sandbox. Native async hooks are
created in the same VM realm as the host so its Promise checks retain real
semantics. Instrumentation stubs cover notices/event delivery, not enforcement
decisions. The Linux run uses a disposable network-disabled container without
provider credentials or controller volumes.

## First-gate evidence

| Requirement | Evidence | Status |
| --- | --- | --- |
| Mandatory pre-prompt initialization/load failure | Registration factory rejection propagates from `register`; session-start exceptions/rejections only log. Full CLI loader/order and failed-load disposition were not exercised. | Mandatory readiness unverified; session-hook approach fails. |
| Disabled schemas and direct execution refusal | Initially bound tools, including `agent`, `ask_user_question`, `run_command`, are absent from `getActiveTools` and false in `isToolEnabled`. | Filter predicate demonstrated; full emitted schemas/direct invocation unverified. |
| Unknown/late/resumed tools default denied | A late `mcp__late__tool` and a new rebound-session tool are enabled without reapplying policy. | Failed requirement for the tested snapshot filter. |
| Fresh native session/binding/phase confirmation before prompt | No sufficient native confirmation transport was demonstrated. A local receipt or successful handshake is not substituted. | Unverified; no supported launch path. |
| Native faults stop execution | Sync and same-realm async `onSessionStart` failures emit `mod_error`; bind/settle complete and tools remain enabled. In-turn hook/direct executor faults were not exercised. | Session-hook approach fails; in-turn guarantee unverified. |

The actual path-anchor function resolves a single leading slash below cwd and a
double leading slash at filesystem root. Secondary policy inspection now requires
`Read(/${home}/**)`, `Write(/${home}/**)`, `Edit(/${home}/**)`; canonical home already
starts with `/`. It uses actual control-flow tool names. Passing this settings
inspection cannot enable execution or establish enforcement of permission-exempt
tools. Complete file-rule evaluation, shell/interpreter containment and native
credential-access denial are not claimed by the anchor test.

## Fresh verification

- Initial hard-block red: 6 failed / 148 passed. Four adapter phases succeeded
  instead of refusing, environment returned `warn`, and the corrected valid-cost
  resolver fixture reached the DB sentinel. No dependency/import failure is
  counted as that controller/adapter regression evidence.
- Hard-block green: 148 tests / 20 files, Linux, exit 0.
- Corrected secondary policy red: 1 failed / 149 passed; corrected managed
  protected-home policy was rejected by the old inspection.
- Final focused green: 150 tests / 20 files, Linux, exit 0, including both
  corrected and old-anchor cases. Shared model identity, controller admission,
  canary provenance, credential generation, fallback and cancellation tests pass.
- Existing helper's server/Claude/new-plugin typechecks, adapter-utils/new-plugin
  compilation and browser parser bundles: exit 0 inside the disposable image.
- Initial offline characterization: 13/13 tests, exit 0 on Windows and Linux.
  After the review fix: 14/14 on both platforms, exit 0. Linux uses
  `docker run --rm --network none`, four read-only file mounts and existing image
  `b1ed65f02e37` (full immutable digest recorded in the previous source report).
- Factory pinned complete check: 371 tests, 2 skipped, exit 0, 120.780 seconds.
- Final review-fix Linux rerun: 150/150 focused tests, 20 files, plus 14/14
  characterization cases and the existing helper's typechecks/builds, exit 0.
- Windows environment test red: 1 failed / 1 passed because a Windows executable
  path is not a valid Linux-native path. Green: 1 passed / 1 skipped; actual
  executable-presence characterization is Linux-only, while unsupported status
  remains asserted on every platform. No Windows-native provider support claim.

Reproducible offline harness command from P, using the existing verified local
artifacts rather than installing a CLI/parser:

```powershell
$env:AIF_COMMANDCODE_AUDIT_BUNDLE = "$PWD/.superpowers/sdd/2026-10-11-native-provider-acp/commandcode-1.79.2-source-audit/package/dist/cli.mjs"
$env:AIF_COMMANDCODE_AUDIT_PARSER = "$PWD/node_modules/.pnpm/acorn@8.18.0/node_modules/acorn/dist/acorn.mjs"
node --test --test-timeout=30000 scripts/commandcode-guard-source-audit.test.mjs
```

This plan's isolated helper copies are `verify.ps1`, `verify-audit.ps1` and
`verify-task-2.ps1` under its ignored `2026-10-11-commandcode-guard-feasibility`
workspace. The first reuses the previously documented explicit read-only mounts,
adding the direct binding test; it runs the same focused suite plus typechecks.
The second mounts only the two audit scripts, bundle and parser, and supplies
their nonsecret artifact paths. The third runs both and propagates failures.
No previous plan scratch file was edited.

The Factory check command was:

```powershell
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.check
```

### Broader Paperclip checks remain non-green

Fresh `pnpm -r typecheck` and `pnpm build` exit 1 at the existing shared package
Unix `mkdir -p`/`cp` build command under Windows (`The syntax of the command is
incorrect`). Fresh `pnpm test:run` exits 1 before Vitest starts with
`spawnSync pnpm ENOENT`. The pnpm invocation also warns that legacy package.json
`pnpm` overrides/patch metadata is ignored by the host pnpm. No lock/dependency
repair or package installation was attempted. The disposable Linux tests use
existing dependency links; this is not a freshly resolved release tree.

The known Vite native-config warning also remains. No broad test-suite pass,
PR/release readiness, production acceptance, complete cost accounting or saving
is claimed. No shared ACP lifecycle code changed in this stage.

## Independent review

One fresh read-only review by `commandcode_guard_review` on `gpt-6-astra`/`xhigh`
examined P `4665cb41..d569f6e0`, the exact vendor slices and artifact hashes, and
the three draft F status documents. It found no Critical issue or production
launch/settings/accounting bypass. Its assessment was **request changes to the
source-stage evidence tooling**, not provider or release approval.

The Important finding was a raw parser-path import in test setup after the
verified import. The single fix pass removed it and shares the verified parser;
the new replacement-path regression failed before the fix and passes afterward.
The reviewer's Minor executable-presence finding was regraded Important after
the actual Windows failure was reproduced: it broke verification on the owner's
host. That case is now Linux-only with an all-platform unsupported assertion.
Both findings are fixed in the recorded review-fix commit; no deferred minor
findings remain and no second review was dispatched. Fresh regression results
verify the corrections; they are not a new independent approval.

The reviewer declined to judge full guard/readiness integration, emitted schemas,
direct execution, full loader ordering, in-turn failures, other-mod interference
and resume enforcement; complete permission evaluation, shell/interpreter
containment and credential isolation; and installation/authentication/inference,
deployment, qualification and release readiness. These remain unverified or
outside this stage, never supported by inference from the fixture. The reviewer
inspected recorded results but did not rerun suites: this is independent source
and provenance review, with fresh test evidence supplied by the implementer.

## Decisions and next boundary

The owner-approved first stage uses the existing clean, non-main P branch rather
than creating another worktree; status checks/scoped commits guard against mixed
changes. Wrong isolation could mix unrelated work. Verification helpers live in
this plan's own workspace rather than editing sibling scratch files; wrong mounts
could omit changed code, so explicit mount/test lists were checked. The approved
existing vendor artifact is reused read-only, with its exact hash verified; a
stale artifact would fail evidence verification rather than authorize execution.

The resolver test adds valid `nativeCostTier: free`, `maxPaidUsd: 0` so it reaches
the intended DB sentinel before the fix; an incomplete fixture could otherwise
mask gate ordering. Async hooks use the host VM's Promise realm; a wrong realm
could create a false vendor failure. Parser bytes are hash-pinned before import;
a wrong parser pin would reject the audit, never enable a provider.

This plan's ignored evidence workspace is retained because broad P verification
still blocks branch/release completion. It preserves command logs and helper
copies rather than deleting evidence of those failures; the cost is modest local
scratch retention. No worktree or user data was removed. The finishing workflow
stops before integration options, merge or push while the broad checks are red.

The source safety/feasibility stage can complete with this unsupported result.
The native-provider feature cannot. A supported guard/readiness interface,
phase-specific MCP suppression, binding/packaging changes and live qualification
remain unimplemented. There is no reason to implement a speculative proof
transport when the first gate is unsatisfied.

Next owner decision: retain Command Code as unsupported and prioritize another
provider's native-control design, or explicitly review another runtime pin or
native integration proposal. No automatic pin change, fallback runner or weaker
tool contract follows from this report. Live Task 8 authority remains separate.
