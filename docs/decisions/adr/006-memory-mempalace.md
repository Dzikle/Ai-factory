# ADR 006: Adopt MemPalace as the single experiential-memory authority

**Status:** Accepted with proven single-writer/application-read-only profile

**Date:** 2026-09-15

## Milestone 0B embedding admission amendment — 2026-09-17

The intended local embedding path is now warmed and mechanics-admitted:
`embeddinggemma`, ONNX q8 CPU with two threads, 384-dimensional MRL vectors,
`sqlite_exact`. The exact `onnx-community/embeddinggemma-300m-ONNX` snapshot is
`5090578d9565bb06545b4552f76e6bc2c93e4a66`; model/tokenizer hashes are recorded
in `milestone0/dependencies.lock.yaml`. Restore/pre-warm that cache and use
`HF_HUB_OFFLINE=1` because upstream downloads otherwise follow mutable main.

Six real Java/TS/Go fixture documents ingested on the warmed SQLite path in
8.65 s. A semantic order-creation query returned relevant controller/service
paths with cosine scores 0.76/0.73/0.69 and zero BM25 contribution. Authenticated
MCP add/search retrieved the readiness lesson with similarity 0.676 and preserved
source path; the same drawer/search survived the next-day host/service restart
offline. This is a small semantic smoke test, **not** an organizational retrieval
quality benchmark. Authority, supersession, scoping, canonical precedence, and
the single-writer/application-read-only requirements remain unchanged.

## Milestone 0 amendment — 2026-09-15

The real 3.9.0 service passed one-writer exclusion, persistence, dependency-loss
recovery, export, restored search, and mutating-tool denial under application
`--read-only`. A filesystem read-only data mount is not a valid restore profile:
the service reports healthy but attempts to write lock/sync state under
`/data/.mempalace` and cannot open the palace. Restored replicas require writable
storage plus application read-only enforcement.

The default MiniLM configuration also reported healthy before its first write
started a roughly 79.3 MB model download and held the writer lease for more than
70 seconds. Admission readiness must include a warmed authenticated add/search
probe. A deterministic OpenAI-compatible embedder proved mechanics only; its
retrieval quality is not admitted.

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

Run one tested writer/team hub, back it up, restore replicas with application
read-only enforcement, and expose only the scoped AI Factory memory adapter
through Paperclip's governed gateway.

## Evidence

MemPalace stores verbatim content with wing/room, source/date, added-by, and
other provenance metadata; supports scoped search and agent diaries; and has a
temporal knowledge graph with valid-from/valid-to, invalidate, and atomic
supersede operations. Team mode supplies shared access with a single writer.

Targeted tests at the pinned commit passed for temporal supersession, persisted
source provenance, and the SQLite exact backend. Its current issue tracker also
contains serious writer-lease, write-loss, partial-index, HTTP conflict,
startup, split-brain, and destructive-sync reports, so operational acceptance is
conditional. The Milestone 0 service POC additionally proved writer exclusion,
export/restore, application read-only denial, service-loss recovery, and exact
provenance retrieval.

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

Before use, warm the selected embedding model, test large-store startup and
retrieval quality, keep a single writer, use application rather than filesystem
read-only restore, and enforce a narrow MCP allowlist. A failed memory service
degrades context but cannot block task truth or permit stale claims to become
canonical.

## Exit/replacement strategy

All callers use the AI Factory memory contract. Export memories with stable IDs,
scope, timestamps, source pointers, and supersession edges, import into one new
authority (OpenSearch Agentic Memory is the first fallback), repoint the adapter,
and rebuild the OpenSearch projection.
