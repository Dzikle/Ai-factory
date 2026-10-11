# Native provider integration through Paperclip ACP

Date: 2026-10-11. Architectural approach approved by the owner; written-spec
review pending. This document specifies a future implementation. It does not
claim deployment, runtime qualification, or authorize paid usage.

## Outcome and scope

The owner enters a task against a registered project. AI Factory classifies and
plans it, selects a suitable qualified free-first runtime, delegates coding, and
collects independent verification without requiring per-task model selection.
Add Claude Code, Cline and Command Code as selectable native Developer runtimes.
One-time owner credential setup is allowed; unattended tasks must not become
interactive login flows.

Paperclip remains the sole authority for tasks, runs, locks, budgets, retries,
sessions and stage transitions. Factory owns versioned routing configuration
and deterministic handoff policy. Logical roles do not become provider names.
Tests, Reviewer, QA and owner integration approval remain independent and
unchanged. Intake Orchestrators retain the admitted OpenCode/Codex bootstrap
pair; this extension does not reroute analysis answers or independent reviewers.

## Baseline and reusable capability

Factory source baseline is `4d1c844d34e885d6262f839f1da08bcc7de8193f`:
configurable coding routing and selection audit exist, but are not deployed.
Paperclip source/deployed baseline is
`3f1194caa926084d1862ac4ce8690841a690c5b0`, with deployed image
`ghcr.io/dzikle/paperclip@sha256:b1ed65f02e37aaccd9566db0852d0440048aaf28f95fd86f94bd7b8109eb343a`.
Current Claude catalogue entry is disabled pending native qualification;
Cline and Command Code are disabled because their adapters are absent.
Executable presence previously established Claude installation only, not login
or availability; Cline and Command Code were absent from the live Linux runtime.

The Paperclip checkout already contains:

- `packages/adapter-utils/src/acpx-engine`: native execution-target handling,
  governed MCP delivery, runtime sessions, cancellation and settlement.
- `packages/adapters/kimi-local/src/server/acp.ts`: a thin native backend
  normalization pattern invoking `createAcpxEngineExecutor`.
- `server/src/adapters/plugin-loader.ts`: external adapter registration through
  `createServerAdapter`, with existing adapter capabilities and UI parser support.

The engine's `custom_acp` mapping is not a registered generic adapter in this
baseline. The `acpx_local` registration is a retirement tombstone, not an
execution option. Neither may be presented as an already-working integration.

## Decision

Use two thin native adapter packages, registered through Paperclip's existing
plugin mechanism, backed by the shared ACP executor. Their types are
`cline_local` and `commandcode_local`. Ship pinned adapter packages with the
immutable controller build, not dynamically downloaded per task. Preserve
distinct adapter identity in native dispatch, receipts and session fingerprints.
Any required closed adapter-ID mapping or issue-scoped model-override support
belongs in the owner's existing Paperclip fork; it is a compatibility change,
not a second execution engine. First prove plugin loading and compiled executor
exports in a disposable exact-image environment. A missing plugin capability
must be documented and reviewed before substituting built-in registration.

Alternatives considered:

- CLI output adapters would retain native execution but duplicate protocol,
  session and cancellation parsing already available through ACP.
- Direct provider API calls would omit the requested native harnesses and create
  a different integration surface; they are outside this request.

Claude continues using `claude_local` and its existing execution engine. No
forced Claude ACP migration or new Claude adapter is required.

## Runtime and model bindings

| Runtime | Adapter | Native transport | Admission requirement |
| --- | --- | --- | --- |
| Claude Code | Existing `claude_local` | Existing native execution | Exact model, supported native credentials, coding qualification |
| Cline | New `cline_local` | `cline --acp`, stdio | Pinned provider/model, credentials, ACP compatibility and coding qualification |
| Command Code | New `commandcode_local` | `cmd acp`, stdio | Pinned model/account entitlement, credentials, ACP compatibility and coding qualification |

These are harnesses, not pricing tiers. An owner-configured profile binds runtime,
adapter, provider/account context where applicable, exact runtime model ID,
tier, task/risk allowlists and priority. A harness name never implies free use.
Model aliases or advertised catalogues do not establish exact resolved model
identity or account entitlement. Resolve and record the identity used by each
qualification; do not enable the default Claude `sonnet` alias without that
evidence.

Cline documents provider pinning through `CLINE_PROVIDER`, a new-session default
through `CLINE_MODEL`, native authentication reuse and session loading. Command
Code documents thread-local model selection and one project directory per ACP
process. These capabilities must be tested on the pinned CLIs; documentation
is not qualification. Sources: [Cline ACP](https://docs.cline.bot/usage/acp),
[Command Code ACP](https://commandcode.ai/docs/acp).

The adapter must apply the selected model before the first inference and verify
the effective identity from native session/provider evidence. The current
executor's usage model field can reflect the requested model; that field alone
is not proof of what a backend actually used. Startup environment and ACP model
controls must not conflict. Unsupported options, provider switches, unavailable
models, missing identity evidence or silent fallback fail admission closed.
Native usage may be partial/unknown; never fabricate tokens, costs or savings.

Commands are owner-controlled, resolved to proven pinned executables. No task
text supplies a launch command, environment secret or shell fragment. The engine
currently supports shell-form agent commands; construct any required command
only from fixed adapter arguments and safely quoted validated paths. The initial
target is the existing Linux controller. Windows `cmd.exe` must never be mistaken
for Command Code's `cmd`; Windows execution is not admitted by this Linux proof.

## Credentials, tools and permissions

Use supported native login state in dedicated runtime credential locations or
Paperclip secret references. The owner performs login through a trusted flow;
agents receive only their own runtime credentials and run-scoped Paperclip token.
Do not copy a global home directory, expose owner board/Git credentials, embed
keys in catalogues, or log secrets. Missing/revoked credentials produce a bounded
authentication-required result, not a hanging login or automatic purchase.
Keep Claude's supported authentication behavior; do not use `--bare` as a
subscription shortcut, because that mode requires API credentials rather than
normal login reuse. See [Claude automation](https://code.claude.com/docs/en/headless).

The existing owner-approved trusted-local profile remains the boundary. This
does not add a new production isolation prerequisite or claim host isolation.
Keep current credential containment and scoped MCP controls enforced outside
prompts. Preserve project instructions and selectively supplied role skills;
neither CLI may import unrelated global MCP servers, hooks or privileges.

Do not silently inherit ACP defaults `permissionMode=approve-all` and
`timeoutSec=0`. Adapter configuration requires an explicit permission policy,
finite timeout and noninteractive denial/failure for unresolved approvals.
No-tool availability probes deny writes, shell execution and external tool side
effects. Coding may use only the current trusted-local Developer capabilities;
any approve-all setting must be explicit within that accepted boundary, not a
claim of per-tool sandbox enforcement. Owner integration remains a separate gate.

Prove delivery of authorized run-scoped MCP credentials and denial of unauthorized
MCP access. Command Code's documented backend MCP entries override same-name
client entries; its native tools also retain their own permission engine. Require
an isolated native configuration and a same-name collision regression. If the
pinned CLI cannot prevent unmanaged MCP/config auto-loading or preserve the
governed server identity, keep that runtime disabled. ACP support alone is not
evidence that these controls work. Source: [Command Code ACP](https://commandcode.ai/docs/acp).

## Routing and qualification

Extend the existing catalogue validator, native adapter allowlist and issue-scoped
model override for the two registered types. Keep defaults disabled. Reuse
`profileBindings` per project rather than provisioning agents during dispatch.
Only an owner-controlled admission operation may create/configure a necessary
Developer binding. It must not rewrite Orchestrator/Tests/Reviewer/QA principals
or bulk-enable the existing admission agents. Proof agents are isolated and
paused after verification; they are not implicit production roles.

Qualification has three distinct levels: installed protocol-compatible runtime,
current bounded authenticated availability, and real coding with independent
Tests/Reviewer evidence. Availability alone never means coding-qualified.
Store authoritative run/artifact references in Paperclip and versioned binding
references in Factory; no readiness database or scheduler is introduced.
The admitted binding checks company, agent, adapter, provider/account reference,
model, cwd, runtime/config fingerprint and successful proof lineage. Changing
any material binding invalidates qualification. Do not store credential values
or a public credential hash in the fingerprint; use nonsecret secret/version
references. Authentication/quota failures invalidate current availability while
historical proof remains historical.
Availability receipts carry a probe timestamp and binding fingerprint. A probe
must succeed within 15 minutes before owner admission. Afterward report it as
last verified, not guaranteed current quota; normal dispatch failures mark the
binding unavailable in Paperclip until an owner-controlled fresh probe clears
it. No recurring inference monitor or implicit probe on every task is introduced.

Keep free → subscription → paid ordering, priority/ID tie-breaks, suitability
filters, high-risk subscription requirement, durable rejection reasons and
pending-handoff revalidation. Free eligibility requires evidence for the selected
provider/model entitlement, not marketing. Paid selection requires explicit
owner spending approval, configured limits and native Paperclip budget checks;
it remains disabled in the initial rollout. If usage cannot support reliable
paid-budget enforcement, that paid profile cannot be admitted.

Qualification defaults: 60-second ACP handshake, 120-second no-tool availability
probe, 600-second coding canary and at most two canary attempts per runtime.
These are proposed future caps, not authority to spend now. Provider costs and
live-call budgets must be approved in the implementation plan before inference.
Default unattended runs also have a finite 600-second timeout; larger task caps
require explicit project configuration, not unbounded adapter defaults.

## Recovery and observability

Reuse Paperclip's native session codec, startup/turn settlement, cancellation,
resource ledger and run history. Compatibility includes company, agent, issue,
canonical cwd, adapter/runtime pin, model/provider, permission and MCP identity.
Do not reuse a warm ACP process across projects. On incompatible configuration,
start a fresh session from durable task artifacts and the retained workspace;
do not transfer a private transcript to a different provider as a substitute.

Prove native Stop, timeout, duplex loss and controller restart: no duplicate
dispatch, no stale issue lock, no continuing orphan tool process, retained
partial usage and correct artifact lineage. Cancellation has a finite 30-second
settlement deadline before bounded host cleanup. A dead native session may be
recreated once from durable context only after prior-run settlement; ordinary
tool errors never trigger blind provider replay.

Use bounded public error categories for authentication, quota/entitlement,
unsupported model/control, permissions/MCP, transport, timeout and native failure.
Raw diagnostics remain private and redacted. Preserve original selection audit
and record any recovery decision. The existing proven OpenCode zero-work 403 →
Codex bootstrap fallback stays unchanged. Cline/Command Code errors do not gain
that exception without a separate zero-work proof and approved extension.

## Acceptance and rollout boundaries

Implementation must produce the following evidence before enabling a profile:

1. Offline adapter/protocol tests for commands, safe environment, plugin loading,
   model controls, missing auth, permissions/MCP collisions, session identity,
   cancellation, malformed responses, usage and bounded failures. Fixtures must
   not reach Docker, real inference or board mutation unexpectedly.
2. Factory router/provisioner regression checks, including disabled and revoked
   bindings, per-project cwd, paid denial, pending handoff and legacy plans.
3. Pinned CLI and ACP handshake checks in the exact Linux image; capability
   mismatches disable the runtime rather than drop controls silently.
4. Owner-budgeted no-tool availability and a small native coding canary per
   admitted runtime/model. Capture actual model identity, candidate/artifact
   hashes, independent Tests and Reviewer runs, scoped MCP proof and usage
   completeness. A sentinel response alone is insufficient.
5. Stop/restart/resume and isolation fault proofs in a disposable controller,
   followed by a bounded authorized live canary. Preserve all pending tasks,
   approvals and unrelated projects; no automatic integration/push/merge.

Run the pinned complete Factory checks and touched Paperclip typechecks/tests.
Record the exact Paperclip test boundary and pre-existing failures separately;
historical full-repository failures must not be relabeled green. Independent
review covers adapter contracts and routing, not just output formatting.

Later rollout requires a separately approved implementation plan and execution
method. Pin source, package versions/integrity, Linux image digest and registry
identity; update the dependency record only with verified evidence. Check idle
controller state, adequate disk and recoverable paired backups before cutover.
Do not prune existing volumes/backups or purchase plans to make rollout proceed.
Admit only proven profiles to explicitly configured projects; an unavailable
runtime stays disabled while the existing workflow remains usable.

Rollback restores the previous exact image and routing registry, disables the
new profiles and preserves authoritative tasks/artifacts. Session incompatibility
starts a fresh bounded native session. Database restore is not ordinary rollback
and requires separate owner authorization because it can discard new state.

Publish a per-runtime status separating source support, installed, authenticated,
currently available, coding-qualified and project-admitted. No claim of universal
readiness, lower cost per accepted task, production security, learned routing,
new control-plane ownership or complete interrupted-run accounting follows from
this extension. The existing accepted trusted-local V1 remains accepted; this is
a requested feature, not a reopened mandatory milestone.

## Written-spec review boundary

This spec has not yet been approved as a written artifact. Its next step is owner
review, then an implementation plan. No adapters, dependencies, credentials,
live routing, runtime installation or deployment are changed by this document.
