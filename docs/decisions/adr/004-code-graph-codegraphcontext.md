# ADR 004: Adopt CodeGraphContext as the single V1 structural graph

**Status:** Accepted with container/runtime POC gate

**Date:** 2026-09-15

## Context

Agents require symbol lookup, callers/callees, imports/dependencies, affected
paths, and incremental refresh for Java/Spring, JavaScript/TypeScript, and Go.
OpenSearch text/vector indexes do not replace structural traversal, and V1 must
not operate multiple overlapping graph systems.

## Decision

Adopt [CodeGraphContext](https://github.com/CodeGraphContext/CodeGraphContext)
0.6.13 at commit `2ef71b05a2ad1c5fd644c3ba52d77b502adaf1cf`
(MIT) as the one V1 graph engine. Run a pinned Linux container/service until the
Windows embedded Ladybug backend is proven. Expose a read-only, bounded AI
Factory adapter for symbol, callers, callees, dependencies, and affected paths;
do not expose raw Cypher to agents.

## Evidence

The source has Tree-sitter parsers/fixtures for Java, TypeScript/JavaScript, Go,
and many future languages; Java tests cover dependency injection, cross-file
calls, ORM mapping, and Spring Data repositories. Query tools include symbol
search, relationship traversal, callers/callees/call chains, imports, and
dependencies. Its watcher debounces file events and refreshes changed/deleted
nodes and outgoing relationships.

At the pinned commit, 32 Java/TypeScript parser and live watcher tests passed
with one skip, and the Go parser test passed. Full embedded indexing on this
Windows host failed because the Ladybug C API shared library could not load.
The package marks itself alpha, and large-repository caching, integrity recovery,
performance, and semantic impact work remain open upstream.

## Authority boundary

Git owns current source. CodeGraphContext owns only the derived graph for a
recorded Git revision. OpenSearch stores lightweight symbol/path/summary/ref
metadata. The Context Resolver must reject or label graph results whose revision
does not match the task's source revision.

## Alternatives

- **`isink17/codegraph`:** rejected because FSL-1.1 is not currently OSI open
  source and maintenance/adoption evidence is too thin.
- **Custom parser/graph:** rejected; it duplicates broad language and incremental
  indexing work.
- **Multiple graph engines:** rejected without a measured coverage benefit.

## Consequences

The thin adapter composes `affected_paths` from callers/importers/dependencies
because a complete semantic impact engine is not yet proven. Memory/buffer limits,
query depth, result count, index revision, and incremental latency are telemetry.

## Risks

Alpha maturity, broad dependencies, backend churn, native-library packaging,
large-repo performance, and graph corruption/rebuild behavior require a pinned
Linux-container POC on representative Java/Spring, TS, and Go repositories.

## Exit/replacement strategy

The graph is disposable. Delete/rebuild from Git or replace the adapter backend;
OpenSearch pointers are regenerated. No canonical data migration is required.
