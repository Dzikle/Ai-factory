# AI Factory — MCP and Capability Model

**Status:** Canonical V1 decision

MCP/tool providers expose external capabilities to logical agents. Agents should not receive every available server or tool.

The runtime grants only the capabilities required by the current role, skill set, project, and task.

## 1. Capability-first model

Where semantics are stable, agents request capabilities such as:

```text
repo.read
repo.write
repo.branch.create
browser.navigate
browser.accessibility.scan
memory.search
memory.write
knowledge.search
knowledge.msearch
code.graph.search
artifact.read
artifact.write
cloud.logs.read
```

The runtime resolves an approved provider.

Examples:

```text
repo.read            → GitHub MCP / local Git
memory.search        → MemPalace
knowledge.search     → OpenSearch MCP
knowledge.msearch    → OpenSearch MCP
code.graph.search    → CodeGraph provider
browser.navigate     → browser/Playwright provider
```

Do not hide specialized provider semantics behind fake generic interfaces when they are materially different.

## 2. OpenSearch MCP

OpenSearch MCP is the primary agent-facing interface to the knowledge fabric.

V1 should support at minimum:

```text
knowledge.search
knowledge.msearch
knowledge.mapping.read
knowledge.index.metadata.read
```

Agent-facing access should default to read/query operations.

Projection/index writes should normally be performed by deterministic application services/workers rather than arbitrary agents.

This separation prevents agents from silently rewriting their own retrieval corpus.

## 3. Multi-search contract

The Context Resolver should be able to perform a single logical request composed of bounded subqueries, for example:

```yaml
queries:
  - domain: docs
    purpose: canonical_context
    limit: 3

  - domain: memory
    purpose: historical_lessons
    limit: 2

  - domain: tasks
    purpose: similar_prior_work
    limit: 3

  - domain: capabilities
    purpose: applicable_skills_tools
    limit: 5

  - domain: code_metadata
    purpose: likely_symbols
    limit: 10
```

The exact wire format is implementation-specific; the behavior is canonical.

## 4. Least privilege by role

Illustrative baseline:

### Orchestrator

```text
ALLOW
knowledge.search
knowledge.msearch
memory.search
repo.read metadata

DENY by default
repo.write
repo.merge
production operations
```

### Researcher

```text
ALLOW
knowledge.search
memory.search
repo.read
approved external research
artifact.write

DENY
repo.merge
production write
```

### Architect

```text
ALLOW
knowledge.search
knowledge.msearch
memory.search
code.graph.search
repo.read
artifact.write

DENY by default
repo.merge
production write
```

### Developer

```text
ALLOW
knowledge.search
memory.search
code.graph.search
repo.read
repo.write within assigned worktree/branch
artifact.write
required test/build tools

DENY
unapproved merge
production deploy
```

### Reviewer

```text
ALLOW
knowledge.search
memory.search
code.graph.search
repo.read
artifact.write

DENY
implementation write by default
repo.merge by default
```

### QA/UX

```text
ALLOW
knowledge.search
memory.search
repo.read
browser.navigate
artifact.write
approved test tooling

DENY
production mutation
implementation write by default
```

## 5. Skill-to-capability resolution

Skills declare required and optional capabilities.

Example:

```yaml
id: repository-impact-analysis
requires:
  - repo.read
  - code.graph.search
optional:
  - knowledge.search
  - memory.search
```

At spawn time:

```text
task
→ choose logical agent
→ resolve required skills
→ collect capability requirements
→ intersect with project policy
→ intersect with role policy
→ resolve approved providers
→ create scoped runtime session
```

If a required capability cannot be safely provided, the task should block or choose an alternate workflow rather than silently granting wider access.

## 6. Permissions are external to prompts

A prompt saying “do not deploy production” is insufficient.

The runtime/provider credential must make that action unavailable.

Credentials should be:

- scoped;
- short-lived where practical;
- project/environment specific;
- auditable;
- omitted from model-visible context when possible.

## 7. MCP/provider registry

The registry should track at least:

```text
provider id
capabilities supplied
risk level
read/write/admin classification
projects/environments allowed
required credentials
health/availability
version
status: experimental/active/deprecated
```

Do not install or activate a provider globally merely because one agent found it useful once.

## 8. Provider lifecycle

Candidate MCP/tool providers follow:

```text
DISCOVER
→ SECURITY REVIEW
→ EXPERIMENTAL
→ EVAL/CANARY
→ APPROVED
→ ACTIVE
→ DEPRECATED/REMOVED
```

The Process Optimizer may recommend a provider but may not automatically promote privileged providers into canonical use.

## 9. Auditability

Tool/MCP invocations that mutate external state must be journaled with:

```text
task id
agent run id
provider
capability
operation/idempotency key
result/external id
timestamp
```

Read-heavy discovery calls may be sampled/aggregated for telemetry, but enough data should remain to diagnose retrieval and permission problems.
