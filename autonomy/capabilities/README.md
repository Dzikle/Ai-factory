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
code.graph.search
artifact.write
cloud.logs.read
```

A runtime registry may resolve those to GitHub/local Git, Playwright, MemPalace, CodeGraph, OpenSearch MCP, or another provider.

## Do not over-abstract

Provider-specific operations should remain provider-specific when two tools do not actually mean the same thing. Avoid creating a generic abstraction more complicated than the underlying capabilities.

## Least privilege

Permissions are enforced outside prompts.

Example Reviewer:

```text
ALLOW repo.read, code.graph.search, memory.search
DENY  repo.write, repo.merge, deployment.write
```

Example QA/UX:

```text
ALLOW repo.read, browser.navigate, artifact.write, memory.search
DENY  repo.merge, production.deploy, database.write
```

## Provider lifecycle

Candidate provider → experimental → validated → canonical → deprecated.

New privileged MCP/tool providers require security review and measured value before canonical adoption.
