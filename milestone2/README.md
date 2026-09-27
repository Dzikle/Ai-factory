# Milestone 2 — MCP supervision and native-catalog hardening

This is one reliability slice of Milestone 2, not the Milestone 2 exit. The
official OpenSearch MCP server remains the provider; Paperclip remains the
runtime catalog, profile, and run authority.

## Local deployment

- Source: `opensearch-project/opensearch-mcp-server-py` commit
  `fcb23ec17186ba905590fb06b2eeecb063bc54a7`, frozen `uv.lock`.
- Build: `docker compose -f milestone2/compose/opensearch-mcp.yaml build`.
- Start: supply `AIF_M2_OPENSEARCH_READER_PASSWORD` from a secret store, then
  `docker compose -f milestone2/compose/opensearch-mcp.yaml up -d --no-build`.
  The password belongs to the `aif_agent` reader user and **must differ** from
  the OpenSearch admin password. Never commit it or print it in logs.
- Local image ID: `sha256:c47f67f75b31370868424a9176784f8cf212d293507e70467911a2c9736cc4a8`.
  Publish an immutable owner-controlled image before remote deployment.
- The local admission cluster has a self-signed certificate, so this Compose
  profile disables TLS verification. A real deployment must supply a trusted
  CA and turn verification on.

Apply `config/opensearch-mcp-reader-role.json` as the OpenSearch Security role
`aif_agent_reader`, bound to the `aif_agent` user. It can search both the
historical admission alias and active Git-docs alias, but has no write action.
On 2026-09-26 the local reader password was rotated away from the previously
shared admin password. Live checks: current reader search 200, write 403;
the former shared password as `aif_agent` returns 401. The rotated value is
stored only in the running local container configuration, not this repository.

The active Paperclip connection is
`34e29b2e-e5f2-455e-ab47-b1187eb38537` at
`http://opensearch-mcp:9900/mcp`. Its cached catalog is exactly four tools.
Developer `7a134376-dd89-4006-97bb-eeba855e443d`, Reviewer
`74519fa4-15c6-437c-9694-5d2579b76356`, and the admission seam probe
have only `SearchIndexTool` in their effective profiles and only this
connection installed. When creating or changing installs, Paperclip may
auto-bind an additive `app:<connection-id>` profile; unbind its company and
agent grants **after the final install update**, then assert the effective
catalog. Do not regard the profile configuration alone as proof.

The former connection `61bc2d0d-11ba-41e3-a989-6d47f79576df` is disabled.
Its 19 remaining installations belong to paused admission/policy fixtures.
The former Windows host MCP process on port 19901 was stopped. A generic
Paperclip MCP connection's catalog refresh retained removed tools; changing
the upstream tool surface required a fresh connection instead of refreshing
the stale one. Revisit catalog retirement in the owner-maintained Paperclip
fork before attempting an in-place tool-surface contraction.

## Verification

Run `python milestone2/scripts/verify_opensearch_mcp.py --fault-inject
--paperclip-state .milestone0/fork-readmission-20260923/paperclip-state-readmission-20260925.json
--connection-id 34e29b2e-e5f2-455e-ab47-b1187eb38537
--agent-id 7a134376-dd89-4006-97bb-eeba855e443d
--agent-id 74519fa4-15c6-437c-9694-5d2579b76356` from the repository
root (put the command on one line). The state file is ignored and contains a
board key; never commit or display it. The test checks distinct reader/admin
secrets, direct four-tool catalog, two real searches, Paperclip's exact
catalog/profile/install state, and restart after killing the MCP child.

Run-scoped Paperclip probe `0d5050af-e948-4c75-a31b-054c9e7b856f` finished
`succeeded`: one governed server, allowed search HTTP 200, denied msearch
HTTP 403 with `deny_default`. After reader-secret rotation and another MCP
crash/restart, run `c60ea56e-4f8e-488c-b548-abb940753efc` repeated that
same result. The probe agent was paused afterward. Its Git
workspace was seeded from the already accepted AI Factory commit because the
globally enabled Milestone 1 pre-run plugin requires a Git source. This is a
test fixture, not a new Context Resolver or workflow implementation.

## Native Codex MCP catalog: fork image built, not deployed

Paperclip fork branch `ai-factory/milestone2-codex-mcp-headers`, commit
`c2f23c8102461a93cb07d294748c32f185d8ecdd`, changes its managed Codex
MCP writer from `headers` to Codex's supported `http_headers` field. A focused
regression failed before and passed after the change; the adapter typecheck
passed. Codex CLI 0.154.0 independently parsed `http_headers.Authorization`
but ignored `headers.Authorization`. The full test file on Windows had 29
passes and 24 unrelated symlink/permission failures; its Linux suite remains
to be run in the image build.

`scripts/verify_native_codex_mcp.mjs` asserts the exact Codex-visible server
names and recognized bearer headers without printing tokens. Feed it to the
controller with `docker exec -i <controller> node - <company-codex-home>
paperclip-projects paperclip-connections paperclip-assigned`. Against the
current image it correctly failed: five historical `native-*` servers were
also visible. The currently running image remains
`aif-paperclip-fork:62760ac` (`sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455`).
Do not disable historical gateways or claim corrected runtime authorization
until the patched image and a native run pass this assertion.

The attempted normal local source build did **not** produce an image. Docker
build record `var0uzzifz2e2eqio8n9vaydf` failed at the runner's generated
protocol-manifest check. The Windows checkout has CRLF working-tree bytes for
generated files whose Git blobs are LF. An exact Git-archive retry avoided
checkout conversion but missed Docker's package-install cache; it was stopped
at about 7 GB remaining host space to protect other running work. No live
controller, database, or storage was changed.

The owner fork's normal Linux Docker workflow now builds the same fix from
commit `d57c0b7c5cbd2e29c25363df7dc30531e44f5ad1`. The additional commit
normalizes mixed-case GitHub owner names for GHCR and skips the unrelated cloud
image on manual branch builds. [Run 36332581214](https://github.com/Dzikle/paperclip/actions/runs/36332581214)
passed both production architecture builds, manifest merge, and the published
image's PID-1 orphan-reaping check. Immutable multi-arch image:
`ghcr.io/dzikle/paperclip@sha256:95f6708217d9b34b10c9a3637d024e121a2bdaf6fa0008eb3fca5983b80f1676`.
This is a build result, **not** a local runtime admission or the active
Paperclip dependency pin. The Linux `codex-home.test.ts` suite was not run by
that Docker workflow.

Local Docker Desktop then failed to start its engine because its inference
manager could not remove a stale `dockerInference` runtime socket. No reset,
image/volume prune, or data deletion was performed. Once Docker is available,
take a paired Paperclip DB/storage backup before switching the controller to
the immutable image; then assert the exact effective native MCP catalog and
bearer headers and run a real native task. Until those gates pass, the admitted
image remains `aif-paperclip-fork:62760ac` and the fix is **not deployed**.

Still open: native-harness MCP home cleanup and live verification, reliable
Git handoff, and a second independently accepted task with conditional QA.
The trusted-only runner still has its isolated `seccomp=unconfined` exception.
