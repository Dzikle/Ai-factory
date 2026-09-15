# ADR 006: Adopt MemPalace as the single experiential-memory authority

**Status:** Accepted with operational gates

**Date:** 2026-09-15

## Context

AI Factory needs specialist/episodic recall, shared lessons, provenance,
supersession, retention, and a path from repeated experience to reviewed skills,
tools, and deterministic automation. Memory must never override current Git or
task truth, and OpenSearch must remain a rebuildable projection.

The spike compared: (A) MemPalace authority with OpenSearch projection, (B)
OpenSearch Agentic Memory authority, and (C) both as primary specialist/shared
stores.

## Decision

Choose A. Adopt [MemPalace](https://github.com/mempalace/mempalace) 3.9.0 at
commit `38260df588968604186b525ecdffb41c140e5f61` (MIT) as the sole durable
experiential-memory authority. Project a scoped, provenance-rich search view
into OpenSearch. Restrict usage to drawers/search, specialist diaries, and
temporal facts/supersession. Disable/exclude MemPalace task launcher, logstream,
and artifact responsibilities.

Run one tested writer/team hub, back it up, and expose only the scoped AI Factory
memory adapter through Paperclip's governed gateway.

## Evidence

MemPalace stores verbatim content with wing/room, source/date, added-by, and
other provenance metadata; supports scoped search and agent diaries; and has a
temporal knowledge graph with valid-from/valid-to, invalidate, and atomic
supersede operations. Team mode supplies shared access with a single writer.

Targeted tests at the pinned commit passed for temporal supersession, persisted
source provenance, and the SQLite exact backend. Its current issue tracker also
contains serious writer-lease, write-loss, partial-index, HTTP conflict,
startup, split-brain, and destructive-sync reports, so operational acceptance is
conditional.

OpenSearch Agentic Memory (3.3+) offers session/working/long-term/history APIs,
fact consolidation, and namespace filters. Retention arrived experimentally in
3.8. Making it authoritative would violate the established disposable knowledge
cluster boundary or require another durable journal. Running it beside MemPalace
would create two memory authorities.

## Authority boundary

MemPalace owns experiential memories, diaries, and temporal fact history. It does
not own tasks, permissions, canonical docs/config, current source, logs, or
artifacts. OpenSearch is a projection. Context Resolver ranks canonical Git first,
filters current/non-superseded memory, labels history, and enforces a memory token
budget.

## Alternatives

- **OpenSearch Agentic Memory primary:** deferred as the replacement if
  MemPalace fails; not used concurrently.
- **Dual MemPalace/OpenSearch memory:** rejected due duplicate retention,
  supersession, writes, retrieval, and precedence.
- **Custom memory framework:** rejected because the remaining work is policy and
  integration, not storage/retrieval primitives.

## Consequences

AI Factory must implement scoped provenance requirements, retention/review dates,
OpenSearch projection, stale-memory handling, and promotion proposals. Repeated
memories become a governed task; only reviewed artifacts enter canonical Git as
a skill/tool/check/automation.

## Risks

Before use, test concurrent writes, process/host restart, backup/restore/export,
large-store startup, HNSW/exact fallback, and destructive sync denial at the
pinned commit. A failed memory service degrades context but cannot block task
truth or permit stale claims to become canonical.

## Exit/replacement strategy

All callers use the AI Factory memory contract. Export memories with stable IDs,
scope, timestamps, source pointers, and supersession edges, import into one new
authority (OpenSearch Agentic Memory is the first fallback), repoint the adapter,
and rebuild the OpenSearch projection.
