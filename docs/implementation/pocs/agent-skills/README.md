# Agent Skills portability POC

This POC proves that AI Factory-specific policy metadata can coexist with the
external [Agent Skills specification](https://agentskills.io/specification)
without creating a competing skill format.

The canonical specimens are under `.agents/skills/`. Each `SKILL.md` uses only
standard frontmatter fields. Small, queryable values live under namespaced
`metadata` keys; structured policy lives in the optional `ai-factory.yaml`
sidecar. The sidecar is enforcement input for AI Factory and is not presented as
part of the external standard.

## Reproduce

From a checkout of `agentskills/agentskills` at commit
`69ef37e9424c0a7ea9dd2293b559e43ec8176379`:

```powershell
uv run --project skills-ref skills-ref validate <this-directory>/.agents/skills/repository-discovery
uv run --project skills-ref skills-ref validate <this-directory>/.agents/skills/code-review
uv run --project skills-ref skills-ref read-properties <this-directory>/.agents/skills/repository-discovery
uv run --project skills-ref skills-ref to-prompt <this-directory>/.agents/skills/repository-discovery <this-directory>/.agents/skills/code-review
```

The first two commands validate the canonical package. `read-properties`
demonstrates a file-reading harness that discovers metadata and lazily reads the
selected `SKILL.md`; `to-prompt` demonstrates a prompt-catalog adapter. Paperclip
uses the same directory shape for its skill sync/install path. In all cases the
full instructions are loaded only after selection.

`allowed-tools` is deliberately absent. It is experimental in Agent Skills and
must never be treated as the security boundary; Paperclip's governed MCP gateway
enforces the sidecar's logical capability requirements.
