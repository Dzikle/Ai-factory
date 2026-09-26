# Milestone 2 — OpenSearch MCP supervision slice

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

Still open: native-harness MCP home cleanup, reliable Git handoff, and a
second independently accepted task with conditional QA. The trusted-only
runner still has its isolated `seccomp=unconfined` exception.
