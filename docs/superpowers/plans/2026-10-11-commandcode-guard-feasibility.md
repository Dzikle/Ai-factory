# Command Code Guard Safety and Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the settings-only Command Code candidate non-dispatchable and
produce reproducible offline evidence about the pinned native guard seam.

**Architecture:** Block the existing adapter and controller binding path first.
Test selected, hash-verified vendor functions without executing the CLI entry
point, then publish the exact supported/unsupported findings. This is the first
stage of the approved guard design, not a speculative implementation of an
unverified startup-confirmation interface.

**Tech Stack:** TypeScript/Vitest, Node.js 24+, existing Paperclip adapter-utils,
Node's VM/test APIs and already-installed Acorn 8.18.0 for offline source parsing;
Factory Python checks. No added dependencies or services.

**Spec:** [Approved native-guard design](../specs/2026-10-11-commandcode-native-guard-design.md).

## Global Constraints

- "Paperclip remains the sole operational authority."
- "Keep the existing 13-field admission binding."
- "Keep native warm sessions disabled."
- "No broad shell grant may stand in for that envelope."
- "CI continues to own the lockfile."
- "No installation, login, inference, image deployment or enabling is authorized by this draft."
- "Do not silently change pins or relax the contract."
- Command Code stays unsupported throughout this stage, including if some
  offline seam tests pass. No readiness flag enables it.
- Preserve existing trusted-local scope, credential/MCP containment, independent
  Tests/Reviewer and owner publication authority. Do not reopen local V1.
- No push, merge, registry registration, live task dispatch, credential access,
  controller replacement, volume/back-up removal or paid usage.

## Review Focus

1. An owner supplies `nativeGuardReady=true` or fabricated qualification context:
   adapter and controller still reject before process creation (Task 1).
2. A capability/availability request would overwrite settings before failing:
   blocked execution leaves settings and backup directories unchanged (Task 1).
3. A tool is registered after `setActiveTools([])` or on rebind: characterize the
   pinned native behavior, do not mistake the initial schema for enforcement
   (Task 2).
4. A native session hook throws or rejects asynchronously: establish whether the
   actual host halts or only logs; no fake-runtime passing result substitutes for
   this evidence (Task 2).
5. A source/parser artifact differs or a harness case is omitted: reject the
   artifact or label the condition unverified, never supported (Tasks 2–3).

## Checkouts, baseline and scope

Use existing linked worktrees, preserving unrelated changes:

- **F:** `C:/Users/User/OneDrive/Documents/GitHub/ai-factory/Ai-factory-milestone0`,
  branch `milestone1-contracts`, drafting baseline `4ad1d45`.
- **P:** `C:/Users/User/OneDrive/Documents/GitHub/ai-factory/Paperclip-milestone2`,
  branch `ai-factory/automatic-task-entry`, baseline
  `4665cb41ce3598429066fe91fc7ee4154abfd10b`.

Paths below are relative to the named root. Read both `AGENTS.md` files and their
required references before edits. Use `apply_patch`. No new worktree is necessary
unless existing work conflicts; do not reset unrelated files.

The owner approved this plan and selected inline execution on 2026-10-11. Native
execution implements locally in this session, followed by one fresh independent
source reviewer. Approval covers these source-stage tasks and local tests/commits,
not live operations. No subagent was dispatched to write or self-review this plan.

### Deliberate stage boundary

The design requires a real pre-prompt native confirmation and mandatory native
failure semantics. Neither interface has been verified. This stage implements
the unconditional safety gate and falsifiable feasibility evidence only.

If any gate fails or remains unverified, stop with the candidate unsupported and
present the exact gap. If all required native controls can be demonstrated,
prepare a second written implementation plan using those actual interfaces;
obtain its review before guard integration. Do not invent an ACP field or private
proof transport in this plan. This explicit split avoids planning production
code around an interface that may not exist.

## File map

- P `packages/adapters/commandcode-local/src/server/acp.ts`: unconditional typed
  launch refusal; preserve config/policy helpers as non-authorizing inspection.
- P `packages/adapters/commandcode-local/src/server/{execution.test.ts,test.ts,test.test.ts}`:
  blocked phases, no runtime/settings effects and truthful environment status.
- P `server/src/services/native-profile-binding.ts`: refuse current bindings for
  Command Code, matching existing unsupported Cline/managed-Claude handling.
- P new `server/src/services/native-profile-binding-unsupported.test.ts` and
  existing `server/src/__tests__/native-profile-admission.test.ts`: direct binding
  and admission-store regressions; no real DB/provider required.
- P new `scripts/commandcode-guard-source-audit.mjs` and `.test.mjs`: bounded,
  read-only pinned-function harness and offline characterization.
- P `packages/adapters/commandcode-local/src/server/{acp.ts,acp.test.ts}`:
  correct protected-home anchors with actual vendor-function evidence; still no
  supported execution path.
- F new `docs/implementation/COMMANDCODE_GUARD_FEASIBILITY_2026-10-11.md` and
  updates to `NATIVE_PROVIDER_{ADMISSION,SOURCE_VERIFICATION}.md`: findings,
  candidate hashes, test results and unsupported status.

No shared ACP lifecycle, schema, scheduler, runtime packaging, runtime pin,
lockfile, Dockerfile or Factory routing-code change is planned at this stage.

## Task 1: Block the unsafe candidate at both entry points

**Interfaces:** Keep `createCommandCodeAcpExecutor(options)` returning the current
`(ctx: AdapterExecutionContext) => Promise<AdapterExecutionResult>` signature.
Keep `resolveNativeBinding(...)` unchanged externally. Both reject with
`native_permission_unsupported`; no boolean override or test-only launch bypass.

- [ ] **Step 1: Add failing adapter tests using the existing `fixture()` in
  `execution.test.ts`.** Run valid Linux fixtures across ordinary, capabilities,
  availability and coding contexts. Include owner-supplied readiness/proof values.

```ts
it.each([undefined, "capabilities", "availability", "coding"])(
  "blocks phase %s before runtime creation or settings mutation", async phase => {
    const f = await fixture();
    const settings = path.join(f.ctx.config.nativeHome, ".commandcode/settings.json");
    const before = await fs.readFile(settings);
    Object.assign(f.ctx.config, { nativeGuardReady: true });
    Object.assign(f.ctx.context, {
      nativeQualificationPhase: phase,
      nativeGuardReady: true,
      nativeGuardConfirmation: { runId: f.ctx.runId, ready: true },
      nativeQualificationBasePolicy: {
        nativePolicy: f.ctx.config.nativePolicy, permissionMode: "deny-all",
        nativeSettingsDigest: f.ctx.config.nativeSettingsDigest,
      },
    });
    const result = await f.execute(f.ctx as never);
    expect(result).toMatchObject({ exitCode: 1,
      errorCode: "native_permission_unsupported", clearSession: true });
    expect(f.createRuntime).not.toHaveBeenCalled();
    expect(f.runtime.startTurn).not.toHaveBeenCalled();
    expect(await fs.readFile(settings)).toEqual(before);
    expect(await fs.stat(path.join(f.ctx.config.nativeHome, ".aif-native-policy"))
      .then(() => true).catch(() => false)).toBe(false);
    expect(result.usage).toBeUndefined();
    expect(result.costUsd).toBeUndefined();
  },
);
```

- [ ] **Step 2: Add a direct controller-binding test.** Create
  `native-profile-binding-unsupported.test.ts`; use the actual resolver, not its
  route-test mock. A DB sentinel must never be reached.

```ts
import { expect, it, vi } from "vitest";
import { resolveNativeBinding } from "./native-profile-binding.js";
it.each(["commandcode_local", "cline_local", "claude_local"])(
  "cannot form an admitted binding for %s", async adapterType => {
    const select = vi.fn(() => { throw new Error("unexpected DB access"); });
    await expect(resolveNativeBinding({ select } as never,
      { id: "agent", companyId: "company", adapterType,
        adapterConfig: { nativeGuardReady: true } },
      { nativeGuardReady: true }, "project"))
      .rejects.toThrow("native_permission_unsupported");
    expect(select).not.toHaveBeenCalled();
  },
);
```

- [ ] **Step 3: Run the new tests red** through the existing disposable Linux
  test helper described under Verification. Expected failures: the current
  Command Code executor can succeed and the binding resolver reaches the DB.
  A dependency/environment failure is not the expected red result.
- [ ] **Step 4: Replace only the executor's launch body** with the same typed
  unsupported pattern used by Cline, additionally clearing obsolete sessions.
  Remove imports used solely by the removed launch/overlay body. Retain policy
  helpers for inspection; they do not authorize a process.

```ts
export function createCommandCodeAcpExecutor(options: NativeAcpExecutorOptions = {}) {
  void options;
  return async (ctx: AdapterExecutionContext): Promise<AdapterExecutionResult> => {
    const result = await executeNativeAcp(ctx, async () => {
      throw new NativeProviderError("native_permission_unsupported");
    });
    return { ...result, clearSession: true };
  };
}
```

Extend the resolver's existing early unsupported list to
`["cline_local", "claude_local", "commandcode_local"]`. This happens before DB,
manifest or credential access, retaining the existing managed-provider boundary.

- [ ] **Step 5: Make environment inspection explicitly fail** even if a local
  executable exists. Keep local artifact/auth checks separate, but append this
  error after `inspectNativeEnvironment` and set `status: "fail"`:

```ts
{ code: "native_permission_unsupported", level: "error" as const,
  message: "Required native guard controls are not verified; execution is disabled." }
```

Test with `command: process.execPath`, exact model and deny-all permissions:
presence must not imply support; no command is executed. In the existing mocked
admission-store tests, add this case using their current `fakeDb`, `agent`, `id`
and `resolveNativeBinding` imports:

```ts
it("does not record dispatch proof when the native binding is unsupported", async () => {
  const f = fakeDb();
  vi.mocked(resolveNativeBinding).mockRejectedValue(new Error("native_permission_unsupported"));
  await expect(authorizeNativeDispatch(f.db, { agent: agent as never,
    config: {}, issueId: id(5), projectId: id(3), runId: id(30), runtimeSkills: [] }))
    .rejects.toThrow("native_permission_unsupported");
  expect(f.writes).toHaveLength(0);
});
```

The existing GET route already catches resolver failure and returns
`currentBinding: null`, `admitted: false`, `reason: "native_binding_unverified"`;
preserve that response contract. Do not add a new API shape.

- [ ] **Step 6: Replace old injected-runtime success assertions** with current
  unsupported assertions; do not leave tests expecting an unreachable successful
  overlay/model/probe path. Keep shared engine tests for model identity, Stop,
  settlement and usage. No hidden test factory may bypass the production gate.
- [ ] **Step 7: Run adapter, resolver, admission and shared-engine regressions**
  green. Inspect public failure output for fixture-secret text and confirm no
  settings/backups/runtime creation. Commit only the Task 1 P paths with message
  `fix: block unverified Command Code native containment`.

## Task 2: Reproduce pinned native semantics offline

**Interfaces:** New audit module exports
`readPinnedFunctions({ bundlePath, parserPath }): Promise<Map<string, string>>`,
`extractNamedFunctions(source, parser): Map<string, string>` and
`createOfflineModHost(functionSource): { host, context }`. No production
module imports it. The parser is an explicit existing local artifact; no package
installation or top-level vendor import occurs.

- [ ] **Step 1: Add failing source-harness tests** in the new `.test.mjs` file.
  Test tampered bundle rejection through `readPinnedFunctions`; test missing and
  duplicate names through the pure `extractNamedFunctions` helper. Parsing or
  uniqueness rejection both fail closed. Use only temporary synthetic files or
  strings for negative fixtures; never alter the audited archive. The expected bundle hash is
  `d976c2ad89f93a2b81af4d150dca99aeedfd679f15e8b8c032314e61e484da7b`.
- [ ] **Step 2: Implement read-only extraction.** Check a regular non-symlink
  bundle <=8 MiB, verify its SHA-256 before parsing, and load the existing Acorn
  module from the explicit path. Check parser version `8.18.0`. Parse as an ES
  module, then select exactly one top-level `FunctionDeclaration` each named
  `createModHost` and `anchorPathPattern`. Return source slices by AST offsets,
  unchanged. `readPinnedFunctions` calls `extractNamedFunctions` only after hash
  verification; the pure helper holds the following extraction code. Do not
  evaluate the full bundle or resolve its imports.

```js
const ast = parser.parse(source, { ecmaVersion: "latest", sourceType: "module" });
const functions = new Map();
for (const name of ["createModHost", "anchorPathPattern"]) {
  const matches = ast.body.filter(node => node.type === "FunctionDeclaration"
    && node.id?.name === name);
  if (matches.length !== 1) throw new Error("native_audit_function_missing");
  functions.set(name, source.slice(matches[0].start, matches[0].end));
}
return functions;
```

- [ ] **Step 3: Implement a closed offline VM fixture.** Evaluate only the
  selected verified function with a 1-second synchronous VM timeout and disabled
  string/WASM code generation. Do not provide `process`, `require`, imports,
  fetch, timers, filesystem, network, shell or provider services. VM is an offline
  test fixture for trusted pinned code, not a production sandbox claim.
  Import `vm` from `node:vm` in the module; use `node:assert/strict` and
  `node:test` in the adjacent tests. Use `node:fs/promises`, `node:crypto` and
  `node:url` for bounded reads, hashes and the explicit parser-module URL.

```js
const context = vm.createContext({
  __name: value => value,
  createModEventBus: () => ({ emit() {}, on: () => () => {} }),
  toDisposable: dispose => ({ dispose }),
  Ka: undefined, ja: "offline:", Va: 64,
  publishModStatus() {}, sanitizeStatusText: value => String(value),
  isModStatusRendered: () => false,
}, { codeGeneration: { strings: false, wasm: false } });
vm.runInContext(`${functionSource}; globalThis.host = createModHost({
  cwd: '/offline/project', runtime: { cwd: () => '/offline/project' }
});`, context, { timeout: 1000 });
return { host: context.host, context };
```

Do not invent no-op stubs for enforcement decisions. If an additional service is
required to exercise a condition, label that condition unverified instead of
manufacturing passing semantics. Bound the entire Node test invocation to 30
seconds in the disposable environment, in addition to per-VM deadlines.

- [ ] **Step 4: Add native-function characterization tests.** Register one
  fixture mod through the actual `host.register`, capturing its API. Supply a
  session whose `listToolNames` reads a mutable fixture list, whose `subscribe`
  returns an unsubscribe function, and whose `emit` captures diagnostics.

```js
let api;
const names = ["read_file", "agent", "ask_user_question", "run_command"];
const events = [];
await host.register({ name: "offline-guard", path: "/offline/guard.mjs",
  source: "fixture", factory: async value => { api = value; value.setActiveTools([]); } });
host.bind({ sessionId: "offline-session", listToolNames: () => [...names],
  subscribe: () => () => {}, emit: event => events.push(event) });
assert.deepEqual(Array.from(api.getActiveTools()), []);
for (const name of names) assert.equal(host.isToolEnabled(name), false);
names.push("mcp__late__tool");
assert.equal(host.isToolEnabled("mcp__late__tool"), true);
```

This expected `true` is a failing design requirement, although the
characterization test passes. Repeat with rebind to a new tool inventory. Test
both a synchronous throwing and an asynchronously rejecting `onSessionStart`
hook via `api.hooks`, `host.bind` and `await host.settle()`; check whether bind
returns normally and `mod_error` appears. Also test registration factory failure
and distinguish factory rejection from session-hook handling. Do not label
`isToolEnabled` a direct tool invocation: the full executor path remains
unverified unless separately traced and exercised without expanding the harness.

- [ ] **Step 5: Exercise the actual path-anchor function** in a separate closed
  VM exposing only `toPosix`. Use cwd `/offline/project`, home `/isolated/home`.
  Assert the existing single-slash rule anchors beneath cwd, whereas
  `//isolated/home/**` anchors to `/isolated/home/**`. Add adapter policy tests
  rejecting the old protected-home denies and accepting corrected ones under the
  existing strict managed-settings fixture. Replace the required denies with
  actual control-flow names and `Read(/${home}/**)`, `Write(/${home}/**)`,
  `Edit(/${home}/**)` (canonical home already starts with `/`). These secondary
  rules must not re-enable the executor or imply denial of exempt tools.
- [ ] **Step 6: Run harness and adapter tests.** From P, with the existing audit
  bundle and parser (paths are inputs, not fetched dependencies):

```powershell
$env:AIF_COMMANDCODE_AUDIT_BUNDLE = "$PWD/.superpowers/sdd/2026-10-11-native-provider-acp/commandcode-1.79.2-source-audit/package/dist/cli.mjs"
$env:AIF_COMMANDCODE_AUDIT_PARSER = "$PWD/node_modules/.pnpm/acorn@8.18.0/node_modules/acorn/dist/acorn.mjs"
node --test --test-timeout=30000 scripts/commandcode-guard-source-audit.test.mjs
```

No environment values are credentials. Missing artifacts produce an explicit
failed verification, not a skip or an automatic download. Record parser/bundle
hashes, exact named source ranges and case outcomes. Commit Task 2 P paths with
message `test: characterize pinned Command Code guard failure boundaries`.

## Task 3: Verify and publish the source-stage outcome

**Interfaces:** No new runtime interface. The feasibility report separates
`demonstrated`, `failed requirement` and `unverified` conditions; none grants
admission. Record source commit hashes and the retained CLI integrity from the
existing audit.

- [ ] **Step 1: Map every first-gate requirement to evidence.** Cover startup
  ordering/load failure, disabled direct execution/schema omission, dynamic
  registration/rebind, fresh native confirmation and in-turn failure behavior.
  A counterexample rejects the tested bare-filter/session-hook approach; it does
  not prove that every possible native integration is impossible or prove all
  remaining conditions. Current inspection predicts late-tool default enable
  and nonfatal session-hook errors; runtime characterization must establish the
  actual result. No assumption becomes a demonstrated outcome.
- [ ] **Step 2: Run focused verification and relevant broader checks** below.
  Record every command, exit code, scope, platform and limitation. Keep existing
  broad-suite/environment failures separate from green focused suites. Do not
  claim source support or PR/release readiness from a partial run.
- [ ] **Step 3: Obtain fresh independent source review** of the complete P diff
  and vendor evidence using the preserved Native method. Reviewers must inspect
  no-bypass controller/adapter gates, no settings/process side effects, artifact
  provenance and honest distinction between characterization and enforcement.
  Fix Important findings, rerun affected checks and preserve review provenance.
- [ ] **Step 4: Write F's feasibility report and update operator/source status.**
  State Command Code unsupported; Cline and managed Claude unchanged. Link the
  approved spec, audit and this plan. Do not overwrite historical test results
  or mark former candidate receipts as current qualification.
- [ ] **Step 5: Self-review document links, placeholders and staged file scope;
  run `git diff --check` in both checkouts.** Commit only the named F docs with
  message `docs: record Command Code guard feasibility and source block`.
- [ ] **Step 6: Hand off the result.** If any first-gate condition fails or is
  unverified, report the blocker and request a choice among retaining unsupported,
  another provider's separate controls, or an explicitly reviewed different pin.
  If every condition is demonstrated, present actual interfaces for a subsequent
  reviewed guard-integration plan. Do not install, qualify, enable or deploy.

## Verification commands and protected environment

For Linux-only policy/execution tests, reuse P's existing ignored helper:

```powershell
pwsh -NoProfile -File .superpowers/sdd/2026-10-11-native-provider-acp/task-4-verify.ps1
```

Before running, inspect the helper and add only the new binding-test file to its
read-only mounts and test list. It runs an existing disposable image
`b1ed65f02e37` with `--network none`, no live controller volume or provider
credentials, and read-only changed source mounts. Build outputs remain inside
the disposable container. Never replace a live service to run these checks.
The helper changes are ignored local execution bookkeeping, not deployed code.

The relevant suites are the Command Code/Cline adapter directories,
`server/src/services/native-profile-binding-unsupported.test.ts`,
`server/src/services/native-profile-admission.test.ts`,
`server/src/__tests__/native-profile-admission.test.ts`,
`packages/adapter-utils/src/native-provider-adapter.test.ts` and
`packages/adapter-utils/src/acpx-engine/native-provider.test.ts`. The existing
helper additionally typechecks server/adapter source and covers related source,
credential-generation, cancellation and artifact-binding tests.

Run existing shared lifecycle verification if changes unexpectedly reach that
surface; do not modify shared engine code merely to make an unsupported adapter
appear successful. P's full requested release checks remain `pnpm -r typecheck`,
`pnpm test:run` and `pnpm build`; report known Windows/build/DB limitations honestly
instead of broadening this change into environment repair.

From F, use the existing pinned command for complete Python regression:

```powershell
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.check
```

Source work must not mutate the protected controller, PostgreSQL container,
company/agents, dependency image pin, volumes, backups, credentials or pending
mobile owner approval. No inference or recurring monitor is part of verification.

## Design coverage and completion boundary

Task 1 satisfies the immediate hard-unsupported migration and no-bypass behavior.
Task 2 supplies pinned native evidence and the corrected secondary path rules.
Task 3 records unsupported/source status, reviews the source and preserves all
authorization/accounting boundaries.

The guard component, actual readiness transport, phase-specific MCP suppression,
policy/artifact binding changes, packaging and runtime Stop/resume proof are
intentionally **not implemented in this first stage**: they depend on the gate
whose absence triggered this revision. They require the second reviewed plan
only if feasibility succeeds. Existing engine behavior is preserved, not newly
certified. This stage's completion means a tested source block and a truthful
feasibility result; it never means the native-provider feature is complete.
