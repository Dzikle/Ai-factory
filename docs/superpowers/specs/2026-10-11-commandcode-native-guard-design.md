# Command Code native guard — design revision

Date: 2026-10-11

Status: Written spec and first-stage implementation plan approved by the owner
on 2026-10-11; inline execution selected. Live operations remain separately
unauthorized. The first-stage outcome is recorded in the
[feasibility report](../../implementation/COMMANDCODE_GUARD_FEASIBILITY_2026-10-11.md).

## Intent and scope

Complete the native-provider feature without weakening the Factory's tool,
credential, MCP or independent-review contracts. Provider breadth serves the
original goal: useful, independently verified engineering improvements with
measured outcomes, not a second execution platform.

This revision concerns only Command Code. It supplements the
[native-provider design](2026-10-11-native-provider-acp-design.md) and replaces
its permissions-only Command Code containment assumption. All other contracts
remain in force. Cline and managed Claude still require their own controls;
their support is not inferred from this design.

The deliverable is a feasibility-gated native guard and the existing adapter's
fail-closed integration. It does not promise that the selected CLI can meet the
contract. An evidence-backed unsupported result is a valid outcome of the first
gate, not completion of provider qualification.

No new scheduler, database authority, provider-output/API runner, vendor fork,
runtime pin, production sandbox or autonomous infrastructure mutation is in
scope. The existing owner-approved trusted-local profile remains the operating
boundary; tool filtering is not operating-system containment.

## Evidence and approaches

The [containment audit](../../implementation/NATIVE_PROVIDER_CONTAINMENT_AUDIT_2026-10-11.md)
records the exact inspected `command-code@1.79.2` tarball, integrity and bundle
hash. Static inspection found unconditional permission exemptions for
`ask_user_question`, `agent` and `run_command`, and an incorrect credential-home
path anchor in the candidate adapter. Injected-runtime tests did not exercise
those vendor semantics. These are unresolved findings, not demonstrated live
exploits or proof of successful guard enforcement.

Three approaches were considered:

- **Required Factory-owned native guard, recommended:** reuse the native mod
  tool-filtering seam, retaining native ACP execution and the existing controller.
  Its benefit is a small integration surface; its risk is unproven lifecycle and
  failure semantics. Support depends on the acceptance gates below.
- **Keep Command Code unsupported:** no containment claim or new integration;
  proceed with another provider's separate native-control design. This preserves
  safety but defers Command Code functionality.
- **Select another CLI pin:** potentially obtain stronger native controls, but
  requires an explicit pin decision and a fresh source audit. This draft does
  not authorize a version change.

Ordinary permission rules alone, prompt instructions, ACP approval rejection,
shell hooks alone and hidden API fallbacks are not acceptable substitutes.

## First gate: establish whether the native seam can satisfy the contract

Before implementing a supported launch path, prove all of the following against
the exact pinned vendor implementation, not just a replacement test runtime:

1. The Factory guard loads synchronously before any prompt or tool execution.
   Missing, invalid or failed initialization cannot leave a runnable session.
2. Disabling a tool prevents its direct execution as well as removing its model
   schema. This includes the three permission-exempt control-flow tools.
3. A newly registered tool, backend/client MCP tool, resumed session or reload
   cannot become usable before the same policy is applied. Unknown tools default
   to denied. No other mod can re-enable them.
4. The existing ACP integration can obtain a fresh, session-bound confirmation
   of the effective guard before sending the prompt. The confirmation must be
   causally tied to native initialization and the actual enforced tool set.
5. Guard faults during a turn stop execution; an exception that the native mod
   host merely logs and ignores is not fail-closed enforcement.

The native API exposes a possible tool-filtering seam. A sufficient startup
confirmation channel and mandatory failure semantics have **not** been verified.
This design does not invent a vendor config option, ACP status field or hook
guarantee. The gate must identify the precise existing native call path, ordering
and confirmation mechanism, and reproduce the failure cases without live model
inference. If any requirement lacks such a mechanism, retain a hard unsupported
launch/dispatch result, document the gap and return for a design decision.

An owner toggle, static manifest, prepared settings file, cached receipt,
successful ACP handshake or adapter-generated acknowledgement is not evidence
that the native guard loaded. A custom output parser, vendor patch or new runner
to manufacture that evidence requires a separately approved revision.

## Components and authority

Paperclip remains the sole operational authority. Reuse its existing run,
qualification, session, Stop and settlement paths.

- **Controller:** derives phase and authorized configuration from protected run
  context; recomputes the current binding. Task text, provider output and owner
  environment overrides cannot grant a guard mode or extra tool.
- **Command Code adapter:** validates the immutable runtime, canonical home and
  workspace; constructs the effective native policy; rejects unmanaged config,
  mods, hooks and MCP sources; refuses launch until the first gate is satisfied.
- **Factory-owned native guard:** applies one explicit allowed-tool set using
  the verified native enforcement seam. It is part of the compiled adapter
  artifact, not fetched at startup or discovered from the workspace.
- **Existing ACP engine:** verifies fresh model identity and effective guard
  confirmation before the prompt, and preserves existing cancellation and usage
  accounting. Guard enforcement belongs to the native execution path, not just
  to the engine's observation of output.
- **Existing admission service:** accepts separate capability, availability,
  coding, Tests and Reviewer evidence only for the exact current binding.

Do not add a parallel admission store or general-purpose permissions engine.
Keep guard-specific policy construction and validation in the Command Code
adapter; extend the shared engine only for the required pre-prompt proof seam.

## Phase policies

### Capability and availability probes

The effective tool set is empty. All native, control-flow and MCP tools must be
absent from schemas and refused at execution. Probes must not start MCP servers,
deliver MCP credentials or load hooks/mods other than the required guard. Merely
setting native permissions to deny-all is insufficient.

Capabilities retain the existing zero-inference contract. Availability retains
its separately budgeted no-tool inference contract. Necessary provider
authentication/metadata traffic is not called inference or a tool invocation;
it does not authorize another external action.

The base binding continues to identify the governed coding/MCP configuration.
The phase-specific effective descriptor identifies the deliberate no-tool/no-MCP
overlay. A probe cannot replace, weaken or silently rewrite the base policy.

### Coding

Use an explicit governed native tool set; deny unknown tools, delegation,
interactive questioning and generic nested command execution. In particular,
`agent`, `ask_user_question` and `run_command` remain disabled. Additional model
calls through delegation are not permitted under the existing coding budget.

Native file/shell tools, if authorized, remain subject to validated native
permissions and the existing workspace/canary envelope. No broad shell grant may
stand in for that envelope. Tests must exercise rejected command composition,
credential-home access and out-of-workspace operations using the actual native
permission evaluator. If those controls cannot enforce the approved policy, the
coding phase is unsupported even if the tool-filter gate passes.

The first live candidate remains the existing two-file, clean-baseline canary
with a single bounded commit, finite timeout and independent Tests/Reviewer
runs. General coding authority is not inferred from a canary result: any broader
tool, command or workspace policy changes the binding and requires renewed
qualification. This design adds no publication/push/merge authority.

### Native permission and MCP policy

Correct credential-home rules using the pinned filesystem-root interpretation:
for canonical home `/isolated/home`, the protected rules are
`Read(//isolated/home/**)`, `Write(//isolated/home/**)` and
`Edit(//isolated/home/**)`. Validate the actual evaluator's interpretation and
canonical path behavior; string presence alone is not a passing test.

Native permissions remain a second layer, not the guard's replacement. File-tool
denials do not prevent arbitrary shell/interpreter access, so no OS-level secret
isolation claim is made. Preserve existing credential containment and reject
unsupported permissions rather than claiming a safe arbitrary shell.

Coding MCP delivery remains run-scoped and explicit. Reject unmanaged backend
definitions and same-name backend/client collisions; native filtering must cover
the resolved tool identities, not only the initial advertised names. No-tools
phases suppress connections before server startup, not after tool registration.

## Identity, initialization and failure

Keep the existing 13-field admission binding. Its policy digest must cover the
guard contract version, immutable guard artifact identity, phase-policy mapping,
native permissions and explicit tool/MCP identity rules. Reuse the existing
compiled-plugin artifact-root hashing and runtime pin; do not create a competing
artifact authority. The emitted image manifest records the resulting identities.

For each new native process/session, protected run context provides the run ID,
binding fingerprint, phase and fresh nonce. After applying policy, the verified
native confirmation must match those values plus the actual effective tool-set
digest and pinned guard identity. This is a required validation contract, not a
claim that the vendor already exposes its transport. Missing, duplicate, stale,
replayed or mismatched confirmation prevents the prompt. Do not reuse a previous
process's proof on resume or count a receipt as runtime enforcement.

Require readiness within the existing bounded handshake deadline; do not extend
timeouts, retry automatically or fall back to another execution path. Keep
native warm sessions disabled. Stop terminates the native child through the
existing engine and settles the run even if initialization never completed.

Use the existing closed failure categories for unsupported permission/guard
controls, identity/MCP mismatch, transport failure and timeout. Diagnostics may
name a non-secret failed invariant, but must not expose credentials, settings
contents or raw provider output. Preserve observed usage and cost on all failure
paths; missing usage remains unknown/partial.

Any temporary probe overlay retains the existing private atomic backup and
compare-before-restore discipline. A failed guard must not cause an unsafe
restore, erase unexplained native edits or discard settlement evidence.

## Tests and acceptance

Tests are layered; each answers a different question:

1. **Pinned vendor semantics, first gate:** native initialization ordering,
   direct disabled-tool invocation, permission-exempt tools, late registration,
   load failure, hook exception behavior, restart/resume and effective-policy
   confirmation. Use an offline harness with inference/network/process side
   effects stubbed. Retain exact artifact provenance. A copied approximation of
   the evaluator is not equivalent evidence.
2. **Adapter/controller contracts:** protected phase derivation, guard/artifact
   tampering, unmanaged config/mod/MCP rejection, root-path rules, current-binding
   invalidation, no-MCP probes and pre-prompt refusal for every missing proof.
3. **ACP lifecycle and accounting:** initial/resumed identity, Stop during guard
   initialization and execution, bounded timeout, partial usage, failed probe
   restoration and no fallback/retry. Fake-runtime tests cover integration, not
   vendor enforcement.
4. **Immutable packaging:** guard included in the existing compiled artifact
   root, exact pinned CLI integrity, deterministic registry behavior, no runtime
   downloads. CI continues to own the lockfile.
5. **Regression and independent review:** rerun relevant provider/controller and
   Factory tests; report broad-suite failures separately. Independent source
   review must revisit both audit findings and the new guard failure boundary.

Source support requires gates 1–5 with evidence tied to the candidate hashes.
Passing source tests is not installed/authenticated/live qualification, release
acceptance, complete cost accounting or demonstrated savings. The historical
test counts and source review do not close the new findings.

## Rollout and authorization boundaries

The implementation plan must begin by making the existing candidate hard
unsupported before any guarded support path is admitted. A settings-only
candidate must not remain dispatchable while feasibility work proceeds. No live
profile or deployed controller is changed by drafting or source implementation.

Any later guard version/policy change invalidates old qualification through the
existing binding mechanism. Do not relabel or migrate old receipts as proof.
All three provider profiles remain disabled until their respective evidence and
owner approval gates are met.

Live operations remain the separately authorized Task 8 envelope: exact image,
provider/account/model/home, protected credentials, scoped MCP, budget, Stop
conditions, probe/canary/independent-review scope and rollback. No installation,
login, inference, image deployment or enabling is authorized by this draft.

If the native gate fails, record Command Code as unsupported and present the
remaining alternatives. Do not silently change pins or relax the contract. Once
provider work is genuinely qualified, return to one useful Factory improvement
and measure correctness, usage completeness, retries, latency and human
intervention under the existing engineering pipeline.

## Review handoff

Owner review should confirm the required guard approach, its conditional support
outcome and unchanged trusted-local/live boundaries. Written-spec approval
authorizes preparation of the implementation plan only. Implementation requires
review of that plan and selection of its execution method; live Task 8 authority
remains separate.
