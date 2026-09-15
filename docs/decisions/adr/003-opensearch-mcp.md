# ADR 003: Adopt the official OpenSearch MCP server behind a bounded adapter

**Status:** Accepted with adapter and security gates

**Date:** 2026-09-15

## Context

OpenSearch 3.x is the dedicated, rebuildable organizational knowledge fabric.
Agents need filtered search, multi-search, index/mapping metadata, and read-only
access, but AI Factory should not build another OpenSearch MCP server.

## Decision

Adopt `opensearch-project/opensearch-mcp-server-py` 0.11.0 at commit
`fcb23ec17186ba905590fb06b2eeecb063bc54a7` (Apache-2.0) in fixed-cluster,
single-mode, read-only configuration. Expose it only through Paperclip's governed
MCP gateway and a thin AI Factory adapter that maps logical capability names,
constrains aliases/indexes/source fields, and applies hard hit/byte/token limits.

Do not expose Generic API, write tools, dynamic cluster credentials, or agentic
memory write tools to ordinary agents.

## Evidence

The server implements index listing, mapping, search, multi-search, count,
explain, cluster metadata, optional Search Relevance Workbench, and OpenSearch
Agentic Memory tools. Search accepts Query DSL, so filtered and hybrid queries
are possible; Msearch accepts NDJSON or converts alternating JSON arrays.

Five targeted upstream tests passed for mapping, search, write filtering,
transport response-size limits, and msearch conversion. However, the default
transport ceiling is far larger than an agent context budget, multi-mode filter
limitations are tracked in issue #203, and a context-overflow circuit breaker is
open in #99.

OpenSearch 3.x already provides hybrid BM25/vector ranking, `_msearch`, Search
Relevance Workbench query/judgment/experiment support, Agentic Memory from 3.3,
agent tracing from 3.6, and experimental memory retention in 3.8. These reduce
custom search/eval infrastructure but do not change OpenSearch's projection role.

## Authority boundary

OpenSearch owns disposable index state only; the MCP server owns no durable
facts. Git, Paperclip, MemPalace, artifact storage, and Git-derived graph sources
remain authoritative. The adapter owns bounded context retrieval semantics, not
index truth or permissions. Paperclip owns active grants/audit.

## Alternatives

- **Custom OpenSearch MCP:** rejected; gaps are result shaping and logical naming,
  both smaller than another server.
- **Direct SDK access from every agent:** rejected; it scatters credentials,
  authorization, query bounds, and telemetry.
- **OpenSearch Agentic Memory as primary memory:** deferred by ADR 006.

## Consequences

Projection writers use application credentials outside agent profiles. Agents
get only read tools. Context Resolver performs multiple purpose-specific bounded
queries and verifies selected claims against original sources. Search Relevance
Workbench is used for retrieval evals.

## Risks

Tool filtering must be enforced twice (server and Paperclip), response limits
must be below token budgets, and hybrid DSL/version compatibility needs tests.
Least-privilege and startup issues in the upstream tracker are acceptance gates.

## Exit/replacement strategy

The logical `knowledge.*` contract and stable aliases isolate callers. Rebuild
indexes from canonical sources and swap either the MCP provider or search engine
without migrating OpenSearch as truth.
