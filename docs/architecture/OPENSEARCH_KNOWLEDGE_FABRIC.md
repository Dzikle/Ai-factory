# AI Factory — OpenSearch Knowledge Fabric

**Status:** Canonical V1 decision

OpenSearch is a foundational service in AI Factory. It is introduced early because it reduces context drift, reduces repeated discovery, supports efficient multi-domain retrieval, and can operate over large volumes of organizational history.

It must run separately from any product/business search cluster.

## 1. Role

OpenSearch answers:

> What relevant knowledge, history, capability, memory, task evidence, or code metadata exists for this task?

It is **not** the source of truth for those records.

Canonical sources remain Paperclip's operational database, Git/canonical
documents, MemPalace, the artifact store, and code repositories. MemPalace was
selected by the completed memory bake-off; OpenSearch Agentic Memory is a
mutually exclusive fallback, not a concurrent primary store.

## 2. V1 logical indexes

Use versioned physical indexes with stable aliases. Exact shard counts/settings are environment-specific, but the logical model is canonical.

```text
ai_factory_docs_v1
  aliases: ai_factory_docs, ai_factory_docs_write

ai_factory_memory_v1
  aliases: ai_factory_memory, ai_factory_memory_write

ai_factory_tasks_v1
  aliases: ai_factory_tasks, ai_factory_tasks_write

ai_factory_events_v1
  aliases: ai_factory_events, ai_factory_events_write

ai_factory_telemetry_v1
  aliases: ai_factory_telemetry, ai_factory_telemetry_write

ai_factory_capabilities_v1
  aliases: ai_factory_capabilities, ai_factory_capabilities_write

ai_factory_code_metadata_v1
  aliases: ai_factory_code_metadata, ai_factory_code_metadata_write
```

Aliases are mandatory so mappings/embeddings/ranking can evolve without changing agent contracts.

## 3. Shared metadata envelope

Projected documents should carry a common provenance envelope where applicable:

```json
{
  "id": "...",
  "type": "...",
  "project_id": "...",
  "scope": "global|project|agent|task",
  "status": "experimental|active|canonical|deprecated|superseded",
  "version": "...",
  "source_system": "git|postgres|mempalace|artifact|codegraph|runtime",
  "source_id": "...",
  "source_uri": "...",
  "source_task_id": "...",
  "created_at": "...",
  "updated_at": "...",
  "canonical": false,
  "confidence": 0.0,
  "supersedes": [],
  "superseded_by": null,
  "tags": [],
  "title": "...",
  "content": "..."
}
```

Not every field applies to every domain, but provenance/status/scope must remain queryable.

## 4. Retrieval strategy

Prefer deterministic filtered retrieval before expensive agentic reasoning.

Baseline order:

```text
metadata filters
    +
BM25 / lexical search
    +
semantic/vector search where valuable
    +
hybrid ranking
    +
explicit multi-search context composition
```

The Context Resolver should issue multiple bounded searches rather than one vague search for all context.

Example:

```text
1. canonical docs for the affected subsystem
2. recent active/superseding architecture decisions
3. relevant incidents/memories
4. applicable skills/capabilities
5. similar tasks/reviews
6. relevant code-symbol metadata
```

## 5. Context composition

A normal agent should receive a bounded package, for example:

```text
3 canonical docs
2 relevant memories/incidents
1–3 applicable skills
recent related task/review outcomes
relevant code-symbol pointers
```

Then load original sources only when required.

This is one of the primary mechanisms for reducing token waste and drift.

## 6. Projection pipelines

Expected sources:

```text
Git/canonical docs ───────┐
Paperclip tasks/reviews ──┤
MemPalace metadata ───────┤
Runtime events/telemetry ─┤→ projection workers → OpenSearch
Capability registry ──────┤
CodeGraph metadata ───────┘
```

Projection failure must not corrupt source state.

Workers should be idempotent and replayable.

## 7. Task/history projection

The task index is for discovery/analysis, not workflow ownership.

Useful projected fields include:

- task type/classification;
- project;
- affected components;
- agent roles/models used;
- success/failure;
- retries/escalations;
- review findings;
- QA findings;
- token/cost totals;
- completion time;
- capability gaps;
- references to artifacts.

This enables later questions such as:

```text
Which task types repeatedly require frontier-model escalation?
Which failures consume the most tokens?
Which skill versions correlate with fewer reviewer defects?
Which capability gaps recur most often?
```

## 8. Memory projection

OpenSearch may index a summary/metadata representation of a MemPalace memory and retain a pointer to the original.

Do not assume a semantically relevant memory is still correct.

Search ranking should prefer active/non-superseded/current material and clearly expose historical provenance.

## 9. Code metadata projection

Do not attempt to replace CodeGraph with OpenSearch.

OpenSearch stores discoverable code metadata such as:

```text
symbol
module
path
summary
graph_ref
project
updated_at
```

When a symbol is selected, CodeGraph handles structural traversal and Git verifies current code.

## 10. Evaluation

Retrieval quality must be measurable.

Maintain query/eval sets containing:

```text
query
expected relevant records
records actually retrieved
records actually used by agent
final task outcome
```

Compare retrieval configurations before promoting ranking changes.

## 11. Rebuildability

All indexes are projections.

If OpenSearch is lost, rebuild from:

- Git/canonical documents;
- Paperclip task/control data;
- MemPalace metadata/memories;
- capability/skill manifests;
- code-graph metadata;
- durable telemetry/artifacts where retained.

Never place information in OpenSearch that has no durable source unless it is explicitly disposable telemetry.
