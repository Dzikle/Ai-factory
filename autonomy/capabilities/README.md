# Capabilities and MCP / Tool Providers

Agents should receive only the external capabilities required for their current task.

Where semantics are stable, agents request logical capabilities rather than hard-coded providers.

Examples:

```text
repo.read
repo.write
browser.navigate
memory.search
memory.write
knowledge.search
knowledge.msearch
code.graph.search
artifact.read
artifact.write
cloud.logs.read
```

## Provider policy

AI Factory owns the logical capability vocabulary and role/skill permission policy.

Existing infrastructure should provide the runtime implementation whenever it satisfies the contract.

Current candidates:

```text
knowledge.search / knowledge.msearch
  → official OpenSearch MCP server

repo.read / repo.write
  → Git/local Git/provider integration

memory.search / memory.write
  → MemPalace through the AI Factory memory adapter

code.graph.search
  → CodeGraphContext through the AI Factory graph adapter

MCP server lifecycle / isolation / registry / policy
  → Paperclip governed MCP gateway

coding runtime / shell environment
  → Paperclip execution workspace / sandbox-provider contract
```

Do not build a custom OpenSearch MCP server or generic MCP process manager. The
spike found no blocking gap that justifies either in V1.

## Official OpenSearch MCP

`opensearch-project/opensearch-mcp-server-py` is the preferred agent-facing provider for the OpenSearch knowledge fabric.

V1 should validate at minimum:

```text
knowledge.search
knowledge.msearch
knowledge.mapping.read
knowledge.index.metadata.read
```

Agent-facing access defaults to read/query capabilities. Knowledge projection writes belong to deterministic services/workers or tightly scoped administrative paths, not arbitrary agents.

## ToolHive deferred boundary

ToolHive was evaluated for:

- server lifecycle;
- runtime isolation;
- identity/access policy;
- registry/tool discovery;
- secrets integration;
- audit and observability.

It is deferred because Paperclip now implements these responsibilities. Reconsider
ToolHive only when untrusted third-party stdio/container isolation provides
measured value, and only after proving that Paperclip remains the single active
policy/approval/audit authority.

## Do not over-abstract

Provider-specific operations should remain provider-specific when two tools do not actually mean the same thing. Avoid creating a generic abstraction more complicated than the underlying capabilities.

A logical capability abstraction must have a stable semantic contract, not merely hide provider names.

## Least privilege

Permissions are enforced outside prompts.

Example Reviewer:

```text
ALLOW
repo.read
knowledge.search
knowledge.msearch
code.graph.search
memory.search
artifact.write

DENY
repo.write
repo.merge
production.deploy
```

Example QA/UX:

```text
ALLOW
repo.read
knowledge.search
memory.search
browser.navigate
artifact.write

DENY
repo.merge
production.deploy
database.write
```

## Provider lifecycle

```text
candidate
→ experimental spike
→ validated
→ canonical provider
→ deprecated/replaced
```

New privileged providers require security review and demonstrated value before canonical adoption.

## Extension preference

When a candidate is close but incomplete, prefer:

```text
configuration
→ thin adapter
→ plugin/extension
→ upstream contribution
→ fork only as last resort
```
