# Native Provider ACP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable, qualified Claude Code, Cline and Command Code Developer runtimes to automatic free-first coding delegation.

**Architecture:** Reuse Paperclip's ACP executor and external adapter loader for two thin native packages; retain the existing Claude adapter. Paperclip owns execution and admission evidence, while Factory consumes exact qualified bindings. Deliver source support with every new profile disabled, then qualify and deploy only within a separately confirmed live-operation envelope.

**Tech Stack:** Python 3.11+/unittest, TypeScript/Vitest, Paperclip adapter-utils, patched ACPX 0.12.0, native CLIs, existing Linux/amd64 controller and PostgreSQL. No new scheduler, database, API-provider engine or isolation platform.

**Spec:** `docs/superpowers/specs/2026-10-11-native-provider-acp-design.md` (owner approved 2026-10-11).

## Global Constraints

- "Paperclip remains the sole authority for tasks, runs, locks, budgets, retries, sessions and stage transitions."
- "Their types are `cline_local` and `commandcode_local`."
- "Claude continues using `claude_local` and its existing execution engine."
- "Keep defaults disabled."
- "Qualification defaults: 60-second ACP handshake, 120-second no-tool availability probe, 600-second coding canary and at most two canary attempts per runtime."
- "Default unattended runs also have a finite 600-second timeout; larger task caps require explicit project configuration, not unbounded adapter defaults."
- "Cancellation has a finite 30-second settlement deadline before bounded host cleanup."
- "A probe must succeed within 15 minutes before owner admission."
- "No recurring inference monitor or implicit probe on every task is introduced."
- "Windows execution is not admitted by this Linux proof."
- "Do not prune existing volumes/backups or purchase plans to make rollout proceed."
- "No automatic integration/push/merge."
- Free → subscription → paid; high-risk requires subscription. Initial paid usage budget is **zero**.
- Preserve independent Tests/Reviewer/QA and owner integration approval; do not change intake bootstrap fallback or pending mobile approval.
- Missing usage/cost remains unknown/partial. Source tests do not prove login, live availability, coding quality or savings.

## Review Focus

1. A stale registry still names an agent whose credentials/config/admission changed: dispatch must revalidate against Paperclip and refuse the old binding (Tasks 4–5).
2. A resumed native session reports a different model from the requested override: no prompt/tools may start; retain the original selection audit and close the incompatible session (Tasks 1–3).
3. Command Code loads a same-name project/global MCP server: the governed identity must win by configuration isolation, or admission stays disabled (Task 3).
4. A missing native authentication flow writes arbitrary stderr or waits for input: bounded typed failure, no secret publication or login loop (Tasks 2–3 and 6).
5. A late handshake/Stop races with settlement or controller restart: exactly one cleanup, no orphan tools, duplicate dispatch or lost partial usage (Tasks 1 and 7–8).

## Workspaces, authority and execution envelope

Use these existing checkouts; do not create another checkout merely for planning:

- **Factory (F):** `C:/Users/User/OneDrive/Documents/GitHub/ai-factory/Ai-factory-milestone0`, branch `milestone1-contracts`. Product-source baseline `4d1c844d34e885d6262f839f1da08bcc7de8193f`; later commits are design/plan documents.
- **Paperclip (P):** `C:/Users/User/OneDrive/Documents/GitHub/ai-factory/Paperclip-milestone2`, branch `ai-factory/automatic-task-entry`, baseline `3f1194caa926084d1862ac4ce8690841a690c5b0`.

All file paths below are relative to the explicitly named F or P root. Line
anchors name current functions instead of brittle offsets in the large heartbeat
service. The executor must first read each repository's `AGENTS.md`; before P
edits read `doc/GOAL.md`, `doc/PRODUCT.md`, `doc/SPEC-implementation.md`,
`doc/DEVELOPING.md`, `doc/DATABASE.md` completely, as P requires. Recheck clean
status and preserve unrelated work. Use `apply_patch` for edits.

Plan approval plus execution-method selection authorizes local implementation,
offline tests and local commits for Tasks 1–7. It does **not** authorize push,
registry publication, live agent mutation, credential login, inference or
controller replacement. Task 8 is an explicit later owner/operator gate, not a
silent final step. No production dependencies are installed in this planning
turn. If the plugin path cannot satisfy the required contracts, report the exact
gap and request a design revision rather than switch to built-ins or CLI output.

Independent review is required. The plan recommends **Native** execution because
the engine, evidence and admission interfaces are tightly coupled; implement in
this session, then use one fresh capable reviewer for the complete source diff.
Subagent-driven execution is also available if the owner prefers per-task review.
The recommendation does not select or authorize that method for the owner.

## File and interface map

| Root / files | Responsibility |
| --- | --- |
| P `packages/adapter-utils/src/native-provider-contract.ts`, its test | Validated native launch contract, model identity, nonsecret binding fingerprint |
| P `packages/adapter-utils/src/acpx-engine/execute.ts`, `constants.ts`, new `native-provider.test.ts`, existing lifecycle tests | Small opt-in seams for model evidence, custom role skills and bounded cancellation; reuse the existing coordinator |
| P `packages/adapters/cline-local/{package.json,tsconfig.json,src/index.ts,src/server/acp.ts,src/server/test.ts,src/ui-parser.ts}` and adjacent tests | External plugin entry, Cline normalization, environment checks and shared UI event parser |
| P `packages/adapters/commandcode-local/{package.json,tsconfig.json,src/index.ts,src/server/acp.ts,src/server/test.ts,src/ui-parser.ts}` and adjacent tests | External plugin entry, Command Code normalization and isolated native policy |
| P `server/src/services/native-profile-admission.ts`, its test; `routes/agents.ts`; `services/heartbeat.ts`; `server/src/__tests__/native-profile-admission.test.ts` | Owner-only admission validation, dispatch revalidation and failure invalidation using existing agent metadata/run history |
| P `packages/adapters/claude-local/src/server/{execute.ts,parse.ts}` and targeted test | Capture actual native model evidence if available without changing the existing Claude engine |
| P `Dockerfile`, `pnpm-lock.yaml`, new `scripts/native-provider-packaging.test.mjs`, new `scripts/register-native-provider-adapters.ts` | Pinned packages and deterministic existing-plugin-store registration; no live startup downloads |
| F `milestone2/scripts/native_profile_contract.py`, its test | Parse Paperclip evidence and compare binding identities without a new state store |
| F `milestone2/scripts/{orchestrator.py,automatic_entry_setup.py}`, existing tests/config | New adapter selection, stale-binding rejection and owner provisioner preflight |
| F `milestone2/scripts/native_provider_qualification.py`, its test; `milestone2/fixtures/native-provider-canary.json` | Bounded operator qualification/preflight/report commands using Paperclip's existing task APIs |
| F `docs/implementation/NATIVE_PROVIDER_ADMISSION.md`, automatic-entry/model docs | Operator runbook, truthful status and release evidence |
| F `milestone0/dependencies.lock.yaml`, compose pin | Update only at authorized, proven rollout; unchanged during source implementation |

Dependencies: Task 1 → Tasks 2 and 3 → Task 4 → Task 5 → Task 6 → Task 7.
Task 8 consumes the reviewed source candidate and requires fresh operator authority.
No task creates a second execution path around Paperclip.

## Task 1: Prove the shared native ACP/plugin contract

**Files (P):** Create `packages/adapter-utils/src/native-provider-contract.ts`
and `.test.ts`; modify `packages/adapter-utils/src/acpx-engine/{execute.ts,constants.ts}`;
create `packages/adapter-utils/src/acpx-engine/native-provider.test.ts`;
extend `packages/adapter-utils/src/published-exports.test.ts` and
`server/src/adapters/plugin-loader.test.ts`.

**Interfaces:** Consume existing `AcpRuntime`, `AcpRuntimeHandle`,
`AdapterExecutionContext`, `AdapterExecutionResult`, `createAcpxEngineExecutor`.
Produce these exported helpers; the same names are used below:

```ts
export type NativeRuntime = "cline" | "command-code" | "claude";
export interface NativeBindingIdentity {
  companyId: string; agentId: string; projectId: string; cwd: string;
  adapterType: string; model: string; provider: string; accountRef: string;
  runtimePin: string; policyDigest: string; mcpDigest: string;
  instructionsDigest: string; credentialVersionRef: string;
}
export interface NativeModelIdentity {
  model: string; source: "acp_session_status" | "native_response";
}
export function nativeBindingFingerprint(binding: NativeBindingIdentity): string;
export function requireNativeModelIdentity(
  actual: unknown, expected: string,
  source: NativeModelIdentity["source"],
): NativeModelIdentity;
export function quoteNativeExecutable(executable: string): string;
```

Use SHA-256 over UTF-8 JSON with lexicographically sorted flat identity keys,
no whitespace, no ASCII escaping. Identity is validated nonempty text; cwd is
an absolute canonical Linux path. Digests are lowercase 64-character hex;
`runtimePin` is the verified package/version/integrity identifier. Secret values
never enter this structure; account and credential references are nonsecret.
Factory mirrors this exact encoding in Task 5 and a cross-language fixture pins it.

- [ ] **Step 1 — Add RED tests** for missing/mismatched model, unknown requested
  controls, startup-env conflict, UTF-8/path quoting, fingerprint changes and a
  resumed session changing model. No `startTurn` call may occur on failed identity.
  Add a plugin-loader test preserving native capability flags and an exports test
  for the built `acpx-engine/execute` subpath, not only source imports.

```ts
it("rejects absent and silently substituted models", () => {
  expect(() => requireNativeModelIdentity(undefined, "exact/model", "acp_session_status"))
    .toThrow("native_model_identity_missing");
  expect(() => requireNativeModelIdentity("other/model", "exact/model", "acp_session_status"))
    .toThrow("native_model_identity_mismatch");
  expect(requireNativeModelIdentity("exact/model", "exact/model", "acp_session_status"))
    .toEqual({ model: "exact/model", source: "acp_session_status" });
});
```

- [ ] **Step 2 — Run RED**, from P:

```powershell
pnpm exec vitest run packages/adapter-utils/src/native-provider-contract.test.ts packages/adapter-utils/src/acpx-engine/native-provider.test.ts server/src/adapters/plugin-loader.test.ts
```

Expected: failure for the missing helper/seam, not an unrelated launcher error.
If Windows pnpm launcher fails, use the same direct Vitest entry in the verified
Linux test environment; record the environmental failure separately.

- [ ] **Step 3 — Implement minimal helpers and opt-in engine seams.** Validate
  absolute executable paths; reject NUL/newline; quote single quotes correctly.
  Resolve real executable provenance in adapter preflight, not from task text.

```ts
export function quoteNativeExecutable(executable: string): string {
  if (!executable.startsWith("/") || /[\0\r\n]/.test(executable))
    throw new Error("native_command_invalid");
  return "'" + executable.replaceAll("'", "'\"'\"'") + "'";
}
export function requireNativeModelIdentity(
  actual: unknown, expected: string, source: NativeModelIdentity["source"],
): NativeModelIdentity {
  if (typeof actual !== "string" || !actual.trim())
    throw new Error("native_model_identity_missing");
  if (actual !== expected) throw new Error("native_model_identity_mismatch");
  return { model: actual, source };
}
```

Add `requireModelIdentity?: boolean` to `AcpxEngineExecutorOptions`; new adapters
set true. After `applySessionConfigOptions`, before the first `startTurn`, call
the existing `runtime.getStatus({handle, signal})`, require
`status.models.currentModelId`, and save `resultJson.nativeModelIdentity`.
Bound this check within the existing startup deadline; if unsupported, fail closed.
Recheck after the turn and on warm/resumed handles; post-turn drift is a failed
partial run, not permission to replay tools. Leave existing adapters unchanged
when the opt-in flag is false.

For an owner-authorized qualification context from Task 4, the same executor also
supports `nativeQualificationPhase="capabilities"`: perform bounded initialize/
new-session/control/identity checks, return their sanitized result through normal
settlement, and never call `startTurn`. An ordinary issue override cannot set this
flag. Availability/coding phases use normal native turns with their explicit
qualification caps; do not create a second protocol runner.

Add an opt-in `customSkillsMode?: "prompt"` using the engine's existing
selected runtime-skill entries and instruction pipeline. Read only materialized
selected instruction content, cap aggregate text at 32 KiB, include digests in
session identity, and supply it as instructions rather than scanning global CLI
skills. Reject unavailable selected entries; do not label tracked-but-unsupported
custom skills as loaded. Reuse existing safe-file/instruction resolvers.
Map the two new adapter types to ACP agent `custom` where closed mapping consumers
require it; executor `adapterType` remains their distinct native type.

- [ ] **Step 4 — Verify GREEN and lifecycle regression**, including failed status
  inspection closing the ledger once, late handshake arrival, Stop ignoring an
  unresponsive child and finite cancellation cleanup. Use existing
  `startup-cancellation.test.ts`, `operator-stop.test.ts`, `run-fault-matrix.test.ts`,
  `execute-identity.test.ts`, `session-reuse-store.test.ts`. Only opt-in runs gain
  the new contract. Confirm source and compiled subpath imports.
- [ ] **Step 5 — Commit only Task 1 files** in P:
  `git commit -m "feat: add verified native ACP integration seams"` after explicit
  staging and `git diff --cached --check`. Report plugin/export gaps before Task 2.

## Task 2: Add the Cline native ACP plugin

**Files (P):** Create `packages/adapters/cline-local/package.json`,
`tsconfig.json`, `src/index.ts`, `src/server/{acp.ts,acp.test.ts,test.ts,test.test.ts}`,
`src/ui-parser.ts`; modify `pnpm-lock.yaml` and dependency-manifest copy in
`Dockerfile`. Reuse Kimi's package TypeScript configuration and existing shared
ACP session/UI parser; do not copy its engine-selection or CLI fallback logic.

**Interfaces:** Consume Task 1 helpers and executor options. Produce
`buildClineAcpConfig(config: Record<string, unknown>): Record<string, unknown>`,
`createClineAcpExecutor(options?: Omit<AcpxEngineExecutorOptions,"adapterType"|"moduleDir"|"packageRootDir"|"requireModelIdentity"|"customSkillsMode">)`
returning the existing execute signature; root `createServerAdapter(): ServerAdapterModule`.

- [ ] **Step 1 — Add RED config/plugin tests.** Assert fixed ACP command, provider
  pin, selected exact model, 600-second timeout, explicit permissions, no inherited
  board/Git token, no `--auto-approve true` default, no task-provided command override,
  no generic-process fallback and bounded authentication-required failure.

```ts
it("launches pinned Cline without auto-approval", () => {
  const config = buildClineAcpConfig({
    command: "/opt/aif/bin/cline", model: "exact/model", provider: "owner-provider",
    permissionMode: "approve-reads", timeoutSec: 600,
  });
  expect(config.agent).toBe("custom");
  expect(config.agentCommand).toBe("'/opt/aif/bin/cline' --acp");
  expect(config.env).toMatchObject({ CLINE_PROVIDER: "owner-provider", CLINE_MODEL: "exact/model" });
  expect(config.nonInteractivePermissions).toBe("fail");
  expect(config.timeoutSec).toBe(600);
});
```

- [ ] **Step 2 — Run RED**: `pnpm exec vitest run packages/adapters/cline-local/src/server`.
  Expected missing plugin/config implementation. Inject the ACP runtime in tests;
  do not run Cline inference or Docker as a test side effect.
- [ ] **Step 3 — Implement package and normalization.** Package name
  `@aif/adapter-cline-local`, local version `0.1.0`, private; source root exports
  `createServerAdapter`, compiled package main `dist/index.js`, `./ui-parser`
  export and parser contract major `1`. Dependency `@paperclipai/adapter-utils`
  is `workspace:*`, so the controller uses its exact patched executor, not an npm
  copy with different ACPX. Build with the existing workspace TypeScript toolchain.

```ts
return {
  ...config, agent: "custom",
  agentCommand: quoteNativeExecutable(command) + " --acp",
  model, timeoutSec,
  permissionMode, nonInteractivePermissions: "fail", warmHandleIdleMs: 0,
  env: { ...resolvedEnv, CLINE_PROVIDER: provider, CLINE_MODEL: model },
};
```

In this normalization, `command/model/provider` are required nonempty configured
strings, `timeoutSec` is a finite positive integer (default 600, owner override
allowed), and `permissionMode` must be explicitly one of the engine's three
supported values. Reject conflicting `CLINE_PROVIDER/CLINE_MODEL`, custom
`agentCommand`, `acpAgentCommand`, engine switching and auto-approve launch flags.
`resolvedEnv` means server-resolved runtime secrets through the existing safe
environment projection, never raw host environment copying. Use an isolated
managed Cline credential/config location; if the pinned CLI cannot isolate
credentials/config without violating native login support, fail qualification.

`createServerAdapter` declares `type:"cline_local"`, `acp.agentId:"custom"`,
`runtimeToolDelivery:"native_mcp"`, `supportsLocalAgentJwt:true`,
`supportsInstructionsBundle:true`, and the shared session codec. Its executor
sets `requireModelIdentity:true`, `customSkillsMode:"prompt"`; its config schema
exposes owner provider/model/path, explicit permission mode and finite timeout.
No interactive login capability is advertised until a supported bounded flow is
proven. Environment checks report installed/protocol/auth status separately and
cannot produce coding-qualified status.
The complete ACP descriptor uses `skillsMode:"unsupported"` (no native directory
staging claim) and `prerequisites:{nodeRange:">=24.11.0",packages:[]}`. Role skills
are actually supplied through Task 1's bounded instruction injection, not falsely
advertised as the CLI's global native skills. Return all required descriptor fields.

- [ ] **Step 4 — Verify GREEN.** Cover model changes invalidating native resume,
  64 KiB output cap, stderr redaction, empty auth, auth expiry, denied approvals,
  unauthorized MCP, absent selected skill and token containment. Two explicit
  failed auth attempts must not create a login/retry loop. Run package typecheck
  and compile; validate its exported module using existing `validateAdapterModule`.
- [ ] **Step 5 — Commit scoped Task 2 files**: `git commit -m "feat: add Cline native ACP adapter plugin"`.

## Task 3: Add the Command Code native ACP plugin

**Files (P):** Create `packages/adapters/commandcode-local/package.json`,
`tsconfig.json`, `src/index.ts`, `src/server/{acp.ts,acp.test.ts,test.ts,test.test.ts}`,
`src/ui-parser.ts`; modify `pnpm-lock.yaml` and `Dockerfile` manifest copy.

**Interfaces:** Consume Task 1 contract. Produce
`buildCommandCodeAcpConfig(config: Record<string, unknown>): Record<string, unknown>`,
`createCommandCodeAcpExecutor` with the same option omissions/execute signature as
Cline, and root `createServerAdapter(): ServerAdapterModule`.

- [ ] **Step 1 — Add RED tests** for a verified absolute Command Code executable,
  fixed `acp` argument, requested model, explicit permissions/timeouts,
  unsupported effort rejection and one process per canonical project cwd.
  Add the Review Focus MCP-collision case and a fixture with unmanaged global hooks.

```ts
it("never launches the Windows command shell as Command Code", () => {
  expect(() => buildCommandCodeAcpConfig({
    command: "C:\\Windows\\System32\\cmd.exe", model: "exact/model",
    permissionMode: "approve-reads",
  })).toThrow("native_command_invalid");
});
it("uses only the fixed native ACP command", () => {
  expect(buildCommandCodeAcpConfig({
    command: "/opt/aif/bin/commandcode", model: "exact/model",
    permissionMode: "approve-reads",
  }).agentCommand).toBe("'/opt/aif/bin/commandcode' acp");
});
```

- [ ] **Step 2 — Run RED**: `pnpm exec vitest run packages/adapters/commandcode-local/src/server`.
  Expected missing normalization/policy implementation, with no external processes.
- [ ] **Step 3 — Implement plugin and native policy.** Private package
  `@aif/adapter-commandcode-local@0.1.0`, same source/build/export/parser contract,
  exact workspace adapter-utils and native capability flags as Task 2, with
  `type:"commandcode_local"`. Set `agent:"custom"`, fixed quoted command + ` acp`,
  selected model, explicit ACP permissions, `nonInteractivePermissions:"fail"`,
  finite timeout and no cross-project warm process reuse. Do not accept
  `agentCommand`, bypass flags or model defaults from task input.

Use native `dont-ask` mode and an owner-scoped native settings allowlist in the
isolated runtime config; ACP approval alone is not its complete permission engine.
For no-tool qualification the native policy is:

```json
{"permissions":{"defaultMode":"dont-ask","deny":["*"],"allow":[]}}
```

Coding uses explicit owner Developer allowances plus denies for publication and
credential paths, not a global bypass. Deny unexpected interactive question/
delegation flows where the CLI cannot constrain them; terminate at the finite
deadline instead of unattended approval. Configuration of modes/settings must
be demonstrated on the pinned CLI; unsupported controls return
`native_permission_unsupported`, never a guessed launch flag.

Isolate native user/config loading and verify the MCP catalogue presented to the
session. Inject a conflicting same-name backend server in the fixture; either
prevent that entry being loaded or refuse with `native_mcp_identity_mismatch`
before tools. A fixture's unknown hooks/server cannot be converted into authority.
These are compatibility gates, not new host-isolation promises. Native docs:
[permissions](https://commandcode.ai/docs/permissions),
[settings](https://commandcode.ai/docs/settings),
[ACP](https://commandcode.ai/docs/acp).

- [ ] **Step 4 — Verify GREEN** for MCP collision, rejected controls, model
  identity before prompt, resumed model drift, absent/expired login, scoped tokens,
  selected role instructions/skills and no same-handle reuse between cwd A/B.
  Missing account entitlement is not automatically paid or retried under another
  model. Compile, typecheck and validate the external module.
- [ ] **Step 5 — Commit scoped Task 3 files**: `git commit -m "feat: add Command Code native ACP adapter plugin"`.

## Task 4: Make native admission authoritative and revalidated

**Files (P):** Create `server/src/services/native-profile-admission.ts`,
`.test.ts` and `server/src/__tests__/native-profile-admission.test.ts`;
modify `server/src/routes/agents.ts` at owner update handling and
`server/src/services/heartbeat.ts` at effective-config construction/native result
settlement; modify Claude `src/server/{execute.ts,parse.ts}` and add
`src/server/native-model-identity.test.ts` only for actual model evidence capture.
Reuse existing agent metadata, run result JSON, issue documents and activity log;
no schema migration or new table.

**Interfaces:** Consume Task 1 identity/fingerprint and existing run records.
Produce `validateNativeAdmission(input: NativeAdmissionInput): NativeAdmission`,
`assertNativeDispatchAdmission(input: NativeDispatchAdmissionInput): void`,
`invalidateNativeAvailability(admission: NativeAdmission, runId: string, category: string): NativeAdmission`.
Define and export all three input/data types from the new service. Input includes
trusted current agent/project, actual run records and owner-authored evidence;
dispatch input includes effective adapter config, current build/runtime pin and
issue project. No adapter result alone may grant admission.

Admission data lives at `agent.metadata.nativeProviderAdmission`:

```ts
export interface NativeAdmission {
  schemaVersion: 1;
  binding: NativeBindingIdentity;
  bindingFingerprint: string;
  qualification: {
    runId: string; issueId: string; candidateTree: string;
    testsRunId: string; reviewerRunId: string;
    capabilityRunId: string;
  };
  availability: {
    runId: string; verifiedAt: string; available: boolean;
    invalidatedByRunId?: string; category?: string;
  };
}
export interface NativeAdmissionInput {
  currentBinding: NativeBindingIdentity;
  proposed: NativeAdmission;
  runs: Record<string, {
    id: string; agentId: string; companyId: string; status: string;
    resultJson: {
      nativeModelIdentity?: NativeModelIdentity;
      baseBindingFingerprint?: string; effectivePolicyDigest?: string;
    } | null;
  }>;
  actor: "owner" | "agent"; nowMs: number;
}
export interface NativeDispatchAdmissionInput {
  currentBinding: NativeBindingIdentity;
  admission: NativeAdmission | null;
}
```

Run results additionally provide their verified issue/project/stage/candidate
lineage through the existing authoritative queries; do not trust IDs embedded
in a proposed metadata object. `NativeAdmissionInput.runs` is the normalized run
evidence map loaded by the owner route, not supplied by the calling agent.

Avoid the qualification/admission bootstrap deadlock: owner-only
`agent.metadata.nativeProviderQualification` grants an isolated proof agent a
finite qualification scope, not production admission. Its schema is
`{schemaVersion:1,bindingFingerprint,issueIds,phase,expiresAt,maxAttempts:2}`,
where phase is capabilities/availability/coding, issue IDs are exact backlog
proof issues, and expiry is at most 30 minutes from owner authorization.
Dispatch permits only those issues, matching company/project/config fingerprint,
the phase's stricter policy and native Paperclip budget checks. It supplies the
protected qualification-phase context after validating scope. Normal tasks,
other issues, expired scopes and agent-authored grants remain refused. Proof
agents never enter Factory profiles until full owner admission. Clear this
scope and pause the proof agent after qualification. No general bypass is added.

Export the scope type and validator from this task as well:

```ts
export interface NativeQualificationScope {
  schemaVersion: 1; bindingFingerprint: string; issueIds: string[];
  phase: "capabilities" | "availability" | "coding";
  expiresAt: string; maxAttempts: 2;
}
export function assertNativeQualificationScope(input: {
  currentBinding: NativeBindingIdentity; scope: NativeQualificationScope;
  issueId: string; phase: NativeQualificationScope["phase"];
  nowMs: number; previousAttempts: number;
}): void;
```

Owner route bounds the expiry when granting it; dispatch checks expiry,
fingerprint, exact issue ID/phase and authoritative attempt count on every wake.
Add RED/GREEN tests proving that a proof issue can run before full admission but
another issue cannot, and an agent cannot edit the grant or phase. Qualification
budget, policy and credentials use the same existing dispatch controls.

Availability uses a restrictive no-tool overlay of the future coding binding.
Its result stores `baseBindingFingerprint` plus `effectivePolicyDigest`; validation
allows only the documented no-tool policy/120-second timeout to differ from the
base binding. Runtime/model/provider/account/credentials/cwd/MCP/instructions
must be identical. Coding proof uses the base policy. A caller-provided arbitrary
overlay is not qualification evidence and cannot grant admission.

- [ ] **Step 1 — Add RED tests**: agent cannot forge/clear admission; other
  company/project proof, same-agent independent review, failed native run,
  requested-only model, missing MCP proof, wrong candidate tree, stale/future
  timestamp and changed binding are rejected. A valid proof permits an idle
  exact native Developer binding only. Preserve unrelated metadata on writes.

```ts
function validAdmissionFixture(): NativeAdmission {
  const binding: NativeBindingIdentity = {
    companyId: "00000000-0000-4000-8000-000000000001",
    agentId: "00000000-0000-4000-8000-000000000002",
    projectId: "00000000-0000-4000-8000-000000000003",
    cwd: "/tmp/aif-native-test", adapterType: "cline_local", model: "exact/model",
    provider: "fixture", accountRef: "fixture-account", runtimePin: "fixture@1",
    policyDigest: "a".repeat(64), mcpDigest: "b".repeat(64),
    instructionsDigest: "c".repeat(64), credentialVersionRef: "fixture-secret-v1",
  };
  return {
    schemaVersion: 1, binding, bindingFingerprint: nativeBindingFingerprint(binding),
    qualification: {
      runId: "00000000-0000-4000-8000-000000000004",
      issueId: "00000000-0000-4000-8000-000000000005", candidateTree: "d".repeat(40),
      testsRunId: "00000000-0000-4000-8000-000000000006",
      reviewerRunId: "00000000-0000-4000-8000-000000000007",
      capabilityRunId: "00000000-0000-4000-8000-000000000008",
    },
    availability: {
      runId: "00000000-0000-4000-8000-000000000009",
      verifiedAt: "2026-10-11T12:00:00Z", available: true,
    },
  };
}
it("revokes availability without erasing historical qualification", () => {
  const admission = validAdmissionFixture();
  const next = invalidateNativeAvailability(admission, "failed-run", "authentication_required");
  expect(next.qualification).toEqual(admission.qualification);
  expect(next.availability).toMatchObject({
    available: false, invalidatedByRunId: "failed-run", category: "authentication_required",
  });
});
```

`validAdmissionFixture()` is defined in this test file, not shared live state:
use its literal offline UUIDs and Task 1 fingerprint with fixed-clock timestamps.
The run map supplies separate Tests/Reviewer agent IDs and verified candidate
tree lineage; test normalization and actual filesystem resolution use a temp cwd.
Every database/API dependency is injected or uses disposable test PostgreSQL.

- [ ] **Step 2 — Run RED**: `pnpm exec vitest run server/src/services/native-profile-admission.test.ts server/src/__tests__/native-profile-admission.test.ts packages/adapters/claude-local/src/server/native-model-identity.test.ts`.
- [ ] **Step 3 — Implement evidence validation.** Owner-only agent update handling
  validates the above subtree against same-company successful native runs,
  `resultJson.nativeModelIdentity`, exact binding fingerprint, shared candidate
  tree and independent Tests/Reviewer run lineage. Capability proof must identify
  the same runtime/config/MCP policy. Availability is within 900 seconds of
  admission, not in the future, and from the exact binding. Reject unknown schema,
  oversized evidence, missing fields and paid classification during this rollout.
  The current compiled runtime must match the proof pin.

```ts
if (run.status !== "succeeded" || run.companyId !== binding.companyId ||
    run.agentId !== binding.agentId ||
    run.resultJson?.nativeModelIdentity?.model !== binding.model)
  throw new Error("native_qualification_mismatch");
if (Date.parse(availability.verifiedAt) > nowMs ||
    nowMs - Date.parse(availability.verifiedAt) > 900_000)
  throw new Error("native_availability_stale");
```

Reject malformed dates before this comparison. Recompute fingerprint from
current effective config, native pin, instructions and MCP connections at the
last pre-dispatch boundary, not only in owner provisioning. A model override
outside that admission fails before execute; retained registry cannot override
revocation. Applicable bindings are the new native profiles, including newly
admitted Claude; legacy OpenCode/Codex bootstrap agents without this metadata
keep their existing independently proven behavior.

On typed auth/quota/entitlement failures, mark availability false in the existing
Paperclip settlement path with run ID and bounded category, activity log the
change, retain qualification and do not increment a second retry counter.
Only fresh owner-controlled admission/probe clears revocation. Handle a racing
credential rotation using a compare-against-original fingerprint write; an old
failure must not invalidate a newer admitted binding. Stop/ordinary tool errors
do not count as auth failure. No principal/config switching occurs.

Public failure categories are a closed set: `authentication_required`,
`quota_unavailable`, `entitlement_unavailable`, `native_model_unsupported`,
`native_model_identity_missing`, `native_model_identity_mismatch`,
`native_permission_unsupported`, `native_mcp_identity_mismatch`,
`native_transport_failed`, `native_timeout`, `native_failed`. Classify from native
typed failures; unknown/raw stderr never becomes a category or public summary.

Claude obtains `native_response` evidence from actual native response model
metadata where exposed; do not copy `config.model` into an actual-model field.
If no native evidence is exposed, record missing and leave Claude disabled.
Do not migrate its engine, alter login, or introduce `--bare`.

- [ ] **Step 4 — Verify GREEN**, owner-vs-agent access tests, stale-registry
  pre-dispatch rejection, credential-rotation race, native budget hard-stop,
  issue-lock settlement and original bootstrap-fallback regression. Activity/log
  payloads contain references/categories only, not native stdout or secrets.
- [ ] **Step 5 — Commit scoped Task 4 files**: `git commit -m "feat: validate and revoke native profile admission in Paperclip"`.

## Task 5: Bind Factory routing to the new native evidence

**Files (F):** Create `milestone2/scripts/native_profile_contract.py`,
`tests/test_native_profile_contract.py`; modify `milestone2/scripts/orchestrator.py`
at `_profile_selection`/pending revalidation, `automatic_entry_setup.py` at
`_model_catalog`/`_additional_profiles`/`SOURCES`, existing corresponding tests,
`milestone2/config/automatic-entry-projects.json`, model/automatic-entry docs.

**Interfaces:** Consume Task 4 metadata. Produce
`binding_fingerprint(binding: dict) -> str` (Task 1 encoding) and
`validate_profile_admission(profile: dict, agent: dict, project_id: str, cwd: str) -> dict`
returning sanitized evidence references or raising bounded `ValueError`.
Keep `_profile_selection(project, plan, agents)`'s existing return tuple and
`configure(client, state, preset, *, apply=False)` public signature.

- [ ] **Step 1 — Add RED tests** for both new adapters, disabled catalogue entries,
  revoked metadata, malformed/nonsecret identity, exact-model/cwd/config drift,
  no paid approval, high-risk subscription requirement, legacy pending plans,
  unchanged audit and cross-language UTF-8 fingerprint equality. Add Python tests
  before allowing adapters in `NATIVE_MODEL_ADAPTERS`.

```python
def test_new_native_profile_requires_authoritative_admission(self):
    row = {"id": "cline", "adapterType": "cline_local", "qualified": True,
           "bindingFingerprint": "a" * 64, "model": "exact/model"}
    agent = {"adapterType": "cline_local", "metadata": {}}
    with self.assertRaisesRegex(ValueError, "native_admission_missing"):
        validate_profile_admission(row, agent, "project-id", "/paperclip/source")
```

- [ ] **Step 2 — Run RED**, from F:

```powershell
uv run --offline --no-project python -m unittest tests.test_native_profile_contract tests.test_orchestrator tests.test_automatic_entry_setup
```

All provisioner tests patch runtime deployment and container readiness globally,
including RED tests. No fixture may fall through to real board writes/inference.

- [ ] **Step 3 — Implement minimal validation/integration.** Add
  `cline_local`/`commandcode_local` to the native set only after their plugins are
  implemented. Additional catalogue fields are `provider`, `accountRef`,
  `runtimePin`, `credentialVersionRef`; secret values remain forbidden. Binding
  references add `bindingFingerprint`; normalized profiles include this alongside
  `agentId`, `qualificationRunId`. Check every identity field against authoritative
  agent metadata and owner config; proof `usageJson.model` alone is insufficient.
  Recompute fingerprint over the validated identity and require exact equality.

```python
identity = admission.get("binding")
if not isinstance(identity, dict):
    raise ValueError("native_admission_missing")
if (admission.get("availability", {}).get("available") is not True
        or admission.get("bindingFingerprint") != binding_fingerprint(identity)
        or profile.get("bindingFingerprint") != admission.get("bindingFingerprint")):
    raise ValueError("native_admission_unavailable")
```

Normalize metadata `None`/non-dict without crashes. In `_profile_selection`, add
  `native_admission_missing`, `native_admission_unavailable` and
  `native_binding_mismatch` rejection codes; retain tier/order/request constraints.
  Pass the project ID/cwd explicitly in the internal validated project context,
  not by searching private operator state. Pending handoff revalidates the exact
  saved selection and never chooses another provider silently.

Keep disabled Cline/Command Code entries without invented provider/model/tier;
  owner must supply an exact proven profile to enable them. Keep Claude disabled.
  Dry-run/apply preflight validates **all** enabled project profiles before first
  board write or code-bundle deployment; include the new helper in `SOURCES`.
  Provisioning consumes admitted existing agents and does not create them per task.

- [ ] **Step 4 — Verify GREEN**, preserved legacy bootstrap and audit replay,
  analysis/Reviewer/QA unchanged, independent binding identities, full multi-project
  preflight and no hidden free-inference side effects. Update docs to distinguish
  source support from installed/authenticated/admitted state.
- [ ] **Step 5 — Commit scoped Task 5 files**: `git commit -m "feat: route coding through admitted native provider profiles"`.

## Task 6: Package pinned runtimes and a bounded qualification operator

**Files (P):** Modify `Dockerfile`; create
`scripts/register-native-provider-adapters.ts`,
`scripts/native-provider-packaging.test.mjs`; update `pnpm-lock.yaml` only for the
two workspace plugins. **Files (F):** Create
`milestone2/scripts/native_provider_qualification.py`,
`tests/test_native_provider_qualification.py`,
`milestone2/fixtures/native-provider-canary.json`,
`docs/implementation/NATIVE_PROVIDER_ADMISSION.md`.

**Interfaces:** Operator functions:
`preflight(client, request: dict) -> dict`,
`submit_qualification(client, request: dict, *, authorized: bool = False) -> dict`,
`collect_evidence(client, request: dict) -> dict`, CLI subcommands `preflight`,
`submit`, `report`. Inputs are a private request JSON filename and existing
operator state filename; never tokens/credentials on command lines. Reuse
`milestone2.task` payload/preflight/submission and engineering policy, not a new
task queue or Python-launched Cline/Command process.

**Candidate pins (registry metadata inspected 2026-10-11; not installed/proven):**

| Package | Version | npm integrity |
| --- | --- | --- |
| `cline` | `3.0.70` | `sha512-ekeGJ7YdVKL9p//KF0F5nxFXMvgSuhwPxvCUkS+SaBDJJoOUt+HMeJS+J+hkF3ezPekbSvpK1wCPGraZbAEO8A==` |
| `command-code` | `1.79.2` | `sha512-e7seLyyriUJtK5MArViSVRekCmRP5VCZrHgoURWayH7agAwvsE+nq+c0rt1dzVs/iD/lc5cMZLu9I0+SZnPORA==` |

Registry metadata lists Cline's `cline` binary and Command Code's `cmd`, `cmdc`,
`commandcode`, `command-code` binary aliases. Use a proven absolute binary path
and package hash, not a bare PATH lookup. Command Code declares Node `>=22`;
use the baseline Node 24.21.0. These pins are compatibility candidates, not a
claim that the current documentation applies to them. If a capability gate fails,
report the result; inspect/review a new exact candidate rather than install latest.
Metadata sources: [Cline registry](https://registry.npmjs.org/cline/3.0.70),
[Command Code registry](https://registry.npmjs.org/command-code/1.79.2).

- [ ] **Step 1 — Add RED operator/packaging tests.** `preflight` does GETs only,
  rejects paid calls, missing credential/model references, unavailable source,
  non-idle agents or another company's runs. `submit` requires explicit
  authorization, finite caps and idempotency key; third canary attempt is refused
  using Paperclip run lineage. Output is sanitized and bounded. Plugin registration
  preserves existing records and fails on unexpected conflicting packages.

```python
def test_dry_preflight_has_no_mutation_or_inference(self):
    receipt = preflight(self.client, self.request)
    self.assertEqual(False, receipt["mutations"])
    self.assertEqual([], self.client.writes)
    self.runtime_runner.assert_not_called()

def test_submit_needs_explicit_live_authority(self):
    with self.assertRaisesRegex(ValueError, "live_qualification_not_authorized"):
        submit_qualification(self.client, self.request)
    self.assertEqual([], self.client.writes)
```

Define fixture setup in this file: fake Client tracks `writes`, fixed clock,
  explicit UUID company/project/isolated proof agent and a mocked runtime runner
  patched to raise on accidental invocation. No import-time state/Docker lookup.

- [ ] **Step 2 — Run RED**:
  `uv run --offline --no-project python -m unittest tests.test_native_provider_qualification` (F)
  and `node --test scripts/native-provider-packaging.test.mjs` (P).
- [ ] **Step 3 — Implement operator and pinned packaging.** Default command is
  read-only preflight. Private request schema:

```json
{
  "schemaVersion": 1,
  "profileId": "cline",
  "phase": "availability",
  "budget": {"tier": "free", "maxPaidCents": 0, "timeoutSec": 120, "maxCanaryAttempts": 2},
  "permissionPolicy": "no_tools",
  "requestKey": "native-admission-cline-availability-1"
}
```

Actual request additionally requires UUID `companyId`, `projectId`, `agentId`,
  exact `model`, `provider`, `accountRef`, `runtimePin`, `bindingFingerprint`,
  dedicated `cwd`, and independent validator/reviewer IDs. The schema above is
  the fixed policy portion, not fabricated runnable live IDs. `phase` is one of
  `capabilities`, `availability`, `coding`; capabilities has no inference,
  availability permits at most one no-tool prompt per explicit request,
  coding at most two attempts total per binding. Reuse bounded task submission
  and stop through Paperclip; no polling scheduler or autonomous resubmission.
  Native authentication happens through the owner separately, never this helper.

Submit proof issues in backlog first, grant Task 4's owner-only exact issue scope,
then start through Paperclip. A failed grant leaves a harmless backlog issue and
no started native run; journal both IDs and reuse the same idempotency key on
recovery. Capabilities/availability proof issues do not run coding Tests/Reviewer
stages; only coding proof uses the existing engineering execution policy.

The canary fixture requests a change confined to a disposable trusted source
  branch: create a pure `add(a,b)` function and tests for positive/negative/zero
  inputs; no dependencies, network tools, publication, infrastructure or live
  project edits. Independent Tests and Reviewer examine the same candidate tree.
  Provide exact task description/allowed paths in the JSON fixture; owner
  integration remains pending unless explicitly approved. Tests exercise the
  helper's idempotency/durable references without making real canary submissions.

Build the two private plugin packages to `dist`; registration uses the existing
  `addAdapterPlugin` API with verified absolute compiled package paths and version
  `0.1.0`. Register through an owner-controlled command after packaging checks;
  do not auto-register dynamically fetched packages at every heartbeat/startup.
  `createServerAdapter` is exported at each package root. Prove that imports
  resolve compiled adapter-utils rather than missing source `.ts` in production.
  Do not depend on Paperclip's built-in name list to expose the plugins.

The Docker tool layer replaces touched native mutable installs with these exact
  versions and integrity checks. Preserve baseline Codex 0.161.0/OpenCode 1.18.35
  and record the installed Claude version before replacing its `@latest`; pin that
  verified baseline instead of upgrading it incidentally. Do not change unrelated
  tools. Generate/verifiably build the image in the authorized release environment,
  not on a low-space host without sufficient capacity. Offline source tests check
  manifest consistency; no image publication/cutover occurs in Tasks 1–7.

- [ ] **Step 4 — Verify GREEN**, CLI `--help` imports without secrets, no auth
  prompt/inference during capability checks, native plugin registration against
  a temporary Paperclip home only, package integrity mismatch rejection and
  truthful report fields: source/installed/authenticated/lastVerifiedAvailable/
  codingQualified/projectAdmitted. Failure receipts never include raw stderr.
- [ ] **Step 5 — Commit scoped Task 6 files**, separately per repository:
  P `git commit -m "build: package pinned native provider plugins"`;
  F `git commit -m "feat: add bounded native provider qualification operator"`.

## Task 7: Verify and review the disabled-by-default source candidate

**Files:** Tests/doc corrections only in the scoped files above; create F
`docs/implementation/NATIVE_PROVIDER_SOURCE_VERIFICATION.md` containing exact
commits, commands/results, known limits and source-vs-live status. No live pin or
admission config changes.

**Interfaces:** Consume Tasks 1–6; produce an exact reviewed source candidate,
not a deployed provider or a Paperclip owner approval.

- [ ] **Step 1 — Exercise missed failure races.** Add regression cases for all
  five Review Focus rows before correcting any discovered implementation defect.
  Include failed model inspection after a compatible warm hit, stale registry
  after owner rotation, partial auth failure after a tool, late handshake after
  Stop and repeated resume rejection. Observe RED for each new defect test.
- [ ] **Step 2 — Run focused GREEN checks** in F:

```powershell
uv run --offline --no-project python -m unittest tests.test_native_profile_contract tests.test_native_provider_qualification tests.test_orchestrator tests.test_automatic_entry_setup
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.check
```

In P run all new plugin/shared/admission suites plus original native fallback,
  issue override, session/Stop/settlement suites. Identify exact existing filenames
  with `rg --files` and include them in the recorded command; do not claim a suite
  by wildcard if it matched nothing. Run new packages and adapter-utils build/
  typecheck plus server/shared typecheck. Then attempt required P handoff checks:

```powershell
pnpm -r typecheck
pnpm test:run
pnpm build
node --test scripts/native-provider-packaging.test.mjs scripts/acpx-patch-packaging.test.mjs
```

Known historical Windows pnpm ENOENT/fixture EPERM, UI token violations and
  unfinished low-disk Linux full-suite results are not green baseline results.
  Capture exact failures; targeted exact-image proof remains separately named.
  Do not fix unrelated historical defects or erase them from the report.
- [ ] **Step 3 — Fix only demonstrated scoped failures**, with TDD regression,
  rerun the owning suite and full Factory checks after any source correction.
  Keep limits for absent model/permission/MCP capability closed, not weakened
  merely to get a native canary passing.
- [ ] **Step 4 — Obtain independent whole-source review** using the owner's
  selected execution method. Review exact F/P commit diffs, shared native seams,
  owner/agent admission permissions, credential containment and tests. Address
  Critical/Important findings before handoff. Explicitly record anything the
  reviewer cannot judge: live auth/quota, actual coding, tool isolation, image
  deployment/restart, billing and cost savings. None becomes a passed claim.
- [ ] **Step 5 — Commit verification/docs**:
  `git commit -m "docs: record native provider source verification and admission limits"`.
  Hand over reviewed exact commits, test evidence and a list of remaining owner
  actions. All three new provider catalogue profiles still disabled.

## Task 8: Owner-operated qualification and optional rollout (not yet authorized)

**Files (F):** During an authorized rollout only, update
`milestone0/dependencies.lock.yaml`,
`milestone0/compose/paperclip-fork-readmission.yaml`,
`milestone2/config/automatic-entry-projects.json` and
`docs/implementation/NATIVE_PROVIDER_ADMISSION.md`; private receipts stay ignored
under a new uniquely named `.milestone0/native-provider-admission-*` directory.

**Interfaces:** Consume the Task 7 reviewed source commit IDs, Task 6 operator
commands and existing owner-controlled publication/build/cutover procedures.
Produce exact image/registry/qualification references or a truthful blocked
runtime status. Unavailable providers do not block keeping existing routing usable.

- [ ] **Step 1 — Confirm the live envelope with the owner.** Require explicit
  exact source publication/build permission, target Linux controller, selected
  project/proof workspace, runtime/model/account references, credential setup,
  free/subscription call allowance and timeout/attempt caps. Paid cents stay zero.
  Native capability/no-tool/coding/Tests/Reviewer calls are separate counted runs;
  retries cannot evade the per-binding two-canary cap. Review actual subscription
  allowance before consuming it. Missing login/entitlement requires owner action,
  never a purchased fallback. Do not reinterpret source approval as this authority.
- [ ] **Step 2 — Read-only preflight.** Use existing task/provisioner help and the
  new operator `preflight --state <private-state-file> --request <private-request-file>`.
  These filenames are explicit required operator inputs, not shell substitutions
  or secrets. Resolve every target and report plan digest, mutations=false,
  exact candidate pins, active-run count and storage requirement before any writes.
  Existing authoritative tasks/approvals and protected volumes are out of scope.
- [ ] **Step 3 — Build/prove disposable image.** Publish only the owner-approved
  exact candidates in `Dzikle/paperclip`, using the existing fork workflow; never
  upstream. Record source label, manifest/image digests, CLI versions/integrity,
  plugin registration and schema identity. Run compiled imports/handshake,
  scoped credential/MCP faults and native Stop/restart/resume tests against
  disposable PostgreSQL/storage, with at most one session recreation after
  settlement. No proof from a mutable tag alone.
- [ ] **Step 4 — Qualify only supported runtimes.** Owner performs native login
  in scoped credential locations; no secret output is recorded. Operator uses
  `submit --authorize-live` with the explicit private request, then `report`.
  Verify no-tool availability and the bounded coding canary, actual model,
  independent same-tree Tests/Reviewer, authorized/unauthorized MCP and cleanup.
  Auth/unsupported-control/no-tool bypass failures leave that profile disabled.
  A second coding attempt is allowed only for a bounded explained correction,
  not repeated failed strategy. Pause isolated proof agents when finished.
  Run the admission availability probe after coding/independent review or repeat
  it only with an explicit newly authorized request if its 15-minute window
  expired. A proof for one project/cwd never admits another project/cwd; only
  explicitly proven project bindings may be enabled.
- [ ] **Step 5 — Cut over only with adequate disk and idle controller.** Verify
  a recoverable paired backup and preserve the exact rollback image/registry.
  Existing backup archive checks are not a new restore rehearsal. Do not prune
  to achieve free space. Apply verified owner admission, explicit project bindings,
  exact image/registry pins and one bounded live task; preserve existing principals
  and pending approvals. If not idle/capable/authorized, stop before cutover.
- [ ] **Step 6 — Prove durable behavior and rollback route.** Compare authoritative
  task/approval/lock/run lineage before/after restart, verify no duplicates/orphans
  and partial-usage retention. If failed, disable the new profiles and restore
  prior exact image/registry while retaining database/task artifacts. Never restore
  a database as ordinary rollback. Integration/push/merge of any coding candidate
  still follows its separate owner approval gate.
- [ ] **Step 7 — Record verified deployment status**, exact evidence IDs, disabled
  providers and remaining owner actions. Commit public sanitized evidence/pins
  only after verification; do not publish private operator state. Report source
  completion and live admission separately. No all-provider readiness or savings
  claim without actual evidence.

## Plan review / handoff

Self-review coverage: intent/baseline/reuse and native model control (Tasks 1–3),
credentials/permissions/MCP/skills (Tasks 1–4), authoritative qualification and
routing (Tasks 4–6), recovery/usage/error categories (Tasks 1, 4, 7–8), and
verification/immutable rollout/rollback/truthful status (Tasks 6–8). All five
Review Focus conditions have owning regression-test steps. No specification
requirement is silently treated as already live.

Written spec approved; this implementation plan awaits owner review and
execution-method selection. No product code, dependency installation, external
publication, live qualification or deployment occurred while writing it.
Approve source Tasks 1–7 and choose **Native** or **Subagent-driven**. Task 8
requires the later explicit live envelope even after source work is complete.
