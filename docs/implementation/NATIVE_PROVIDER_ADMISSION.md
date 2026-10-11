# Native provider admission — source candidate

No profile is enabled by this change. No new native CLI was installed, logged in,
called, or deployed. Cline `3.0.70` and Command Code `1.79.2` are compatibility
candidates, not proven runtimes. Existing-image Claude was inspected read-only as
`2.1.293`; packaging pins it without an incidental upgrade. Managed Claude proof
dispatch remains unsupported until its executor can enforce the same isolated home
and no-tool controls. Existing unmanaged bootstrap execution is unchanged.

Cline's managed executor now rejects every launch with
`native_permission_unsupported`, including qualification. Its package and config
normalizer are source foundations, not a usable native integration: unproven home
and project authority containment cannot be enabled by a caller configuration flag.
Managed Claude is likewise blocked at controller dispatch. Command Code remains a
disabled source candidate requiring all remaining release and live gates below.

## Preparation and binding

An owner separately prepares an isolated native home and disposable trusted source
workspace, authenticates using the pinned CLI's supported native login, and records
nonsecret account and credential-generation references. Do not copy a global home,
place credentials in catalogues, or use owner board/Git tokens as provider credentials.
No helper here performs login or writes credentials.

Controller configuration requires `command`, exact `model`, `provider`, `accountRef`,
`cwd`, `nativeHome`, `nativeExecutableDigest`, `runtimePin`, `nativeCostTier`
(`free` or `subscription`), `maxPaidUsd: 0`, explicit `permissionMode`, finite
`timeoutSec`, explicit selected skill versions, `nativeCredentialSecretId`,
`nativeCredentialFile`, and `credentialVersionRef`. Owner `env` must be absent or
empty; untracked alternate API keys, endpoints and native config overrides are refused.
Controller-governed scratch/Git/network environment remains intact in memory only.

The credential file must be canonical, private mode, a regular non-symlink file under
the dedicated home. The owner-created company secret's `providerMetadata` associates
`nativeHome`, `nativeCredentialFile`, `accountRef`, `adapterType`, and `generationRef`.
The generation is `fs:<dev>:<ino>:<birthtimeNs>:<ctimeNs>:<size>` from filesystem
metadata, not credential contents or a public credential hash. Its opaque reference
is `<secretId>:v<currentVersion>:<generationRef>`. Ordinary refresh, replacement, or
rotation invalidates the association and requires a new owner review/qualification.
This does not defend against a malicious root administrator rewriting filesystem
metadata; root controls the host already. Exact credential-file choice and native
account semantics must be verified against the installed candidate, not guessed.

Command Code additionally requires exact owner-prewritten `.commandcode/config.json`
and `.commandcode/settings.json`, `nativePolicy`, and `nativeSettingsDigest`.
Unexpected project/home MCP, hooks, plugins, feature-model or policy sources are
refused. Probe deny-all settings are atomically overlaid and restored; crash backups
remain private for owner recovery. Unknown edits are never overwritten. Neither
native policy nor this overlay substitutes for host containment.
If restoration fails after work, the failed result preserves recorded usage and
cost while withholding public raw provider output; the private backup is retained.

Native model evidence must come from one exact backend-reported model selection in
ACP session config options, not the requested model or a synthesized cache field.
On reconnect, persisted model authority is cleared before fresh backend metadata is
accepted. Missing fresh metadata fails closed before another prompt. Native warm
reuse is disabled; this does not change legacy adapter behavior.

Immutable `/opt/aif/native-runtime-pins.json` is generated at image build from exact
CLI and compiled plugin/shared/controller bytes. Runtime verification rejects
modified artifacts. The registration command uses existing `addAdapterPlugin`,
checks all compiled packages and conflicts first, and preserves other records.
It is an explicit owner command, not startup fetching/registration. Production
manifests materialize compiled exports. CI owns the workspace lockfile; regenerate
it through CI before any future frozen-lockfile image build.

## Bounded operator

Run `python -m milestone2.scripts.native_provider_qualification --help` for syntax.
Default `preflight` and `report` perform GETs only. Inputs are private `--state` and
`--request` JSON filenames; never command-line secrets. `submit` requires separate
`--authorize-live-qualification`. That authorization has **not** been given here.

The exact request contains schemaVersion 1, profileId, phase, companyId, projectId,
agentId, validatorAgentId, reviewerAgentId, ownerUserId, model, provider, accountRef,
runtimePin, bindingFingerprint, cwd, requestKey, permissionPolicy, and budget.
Budget is tier free/subscription, maxPaidCents 0, maxCanaryAttempts 2, timeoutSec
120 (capabilities/availability) or 600 (coding). PermissionPolicy is `no_tools`
or `coding_canary` respectively. Use real owner-confirmed IDs/references only.

Submission reuses Paperclip issue idempotency: backlog first, exact owner scope
second, start third. Failed grant leaves backlog without inference. Reuse the same
requestKey after inspecting Paperclip; do not invent another key as an automatic
retry. Run lineage and controller gates cap attempts at two per binding/phase.
The current helper requires an idle agent before submit. A busy same-key recovery
must be inspected in Paperclip and retried with that same key after idle; it does
not automatically recover or resubmit a running request. Read-only report accepts
a paused agent and does not authorize execution.
Capabilities performs zero turns; availability permits one no-tool prompt per
explicit issue. The helper has no polling scheduler, provider launcher or retry loop.

Coding uses `milestone2/fixtures/native-provider-canary.json` on a disposable
committed copy. The owner prepares a canonical standalone Git repository with an
empty committed baseline, no remotes, no shared Git storage, no untrusted local
Git configuration, and branch `aif-native-canary/<UUID>`. The exact baseline HEAD
is configured as `nativeCanaryBaseCommit` and included in the binding fingerprint.
Coding grant and dispatch require an integer base timeout of at most 600 seconds;
the read-only admission response exposes `codingSourceReady` for preflight.
After coding, the controller requires one clean commit directly above that
baseline, on the same branch, containing only regular tracked
`native_canary/add.py` and `native_canary/test_add.py`. Ignored or untracked dirt,
an unchanged candidate, extra paths and Git filters are refused. Git configuration
is checked before status can execute a filter. These checks prove bounded source
scope, not implementation correctness or operating-system containment.

Tests and Reviewer are independent agents in the existing ordered
engineering review stages and must approve the same candidate tree. Each writes a
run-authored immutable JSON receipt under `native-qualification-<runId>` with
schemaVersion, runId, agentId, issueId, phase tests/reviewer, candidateTree,
verdict passed, validationSource `credential-free isolated committed copy`.
The controller validates actual revision authorship, successful runs, stage
decisions, current bindings, zero-inference capability proof and fresh availability
(at most 15 minutes old at admission). Only the owner PATCHes final admission.

Authentication/quota/entitlement failure revokes availability for the original
binding without erasing historical qualification or invalidating a rotated newer
binding. Ordinary coding failure does not revoke availability. No alternate
provider or paid model is silently selected. Reports distinguish source,
artifact installation, unverified authentication, historical availability,
coding qualification and current project admission.

## Release gates still required

Offline tests are not live provider qualification. Future authorization must cover
CI lockfile generation, image build/integrity and artifact compatibility checks,
explicit registration, isolated owner login, pinned-native MCP/policy/model gates,
finite proof submissions and independent review. Push, publication, controller
cutover, owner integration, and restoration drills remain separately authorized.
