# Milestone 1 Git contracts

`v1/` contains JSON Schema Draft 2020-12 integration contracts for Milestone
1.1. The checked-in project and role examples, capability vocabulary, and POC
Agent Skills sidecars are validated by `tests/test_milestone1_contracts.py`;
data envelopes and negative boundary cases are exercised by
`tests/test_milestone1_data_contracts.py`.

| Contract | Intended consumer | Authority it does not replace |
| --- | --- | --- |
| `project-overlay`, `skill-sidecar`, `capability-definitions`, `role-policy`, `task-capability-request` | Future capability compiler and skill selection | Paperclip active MCP policy and Git source precedence |
| `context-query-plan`, `provenance-envelope` | Future Context Resolver | Git, Paperclip, MemPalace, and artifact original sources |
| `normalized-event` | Future Paperclip event projector | Paperclip task/run/review/cost ledger |
| `memory-record`, `promotion-proposal` | Future memory adapter and improvement proposals | MemPalace memory authority and human promotion approval |
| `model-selection-policy` | Future model selector | Paperclip active runtime/model binding |
| `validation-check`, `quality-outcome` | Future deterministic checks and independent review/QA | Paperclip execution policy and run identities |

These files define intent, not effective permissions. A future capability
compiler may intersect role, project, skill, and task restrictions and submit
the result to Paperclip. Paperclip remains the sole active MCP catalog,
credential, approval, and audit authority. No schema or sidecar can grant a
tool by itself. Missing required capabilities must block execution, never
broaden a profile. `code.graph.search` is defined but disabled while its
dependency remains under the separate security gate.

Current source precedence is fixed by `AGENTS.md` and governance. An overlay
may name canonical Git paths but cannot reorder authority or promote memory
or OpenSearch projection to canonical truth. The example overlay is a specimen,
not an installed runtime project.

The offline checks reject conflicting or unavailable capability references,
task requests that exceed project/role/skill policy, overcommitted context
budgets, cross-project query filters, and self-review claims. They do **not**
enforce runtime permissions, isolate workspaces, verify actual source freshness,
or run a workflow. Paperclip and the later integration adapters must enforce
those boundaries against the actual effective runtime catalog and source data.
In particular, the path shape in `validation-check` does not replace runtime
workspace-confinement checks; symlinks and mount boundaries need runtime proof.

Validate the first slice from the repository root:

```powershell
uv run --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m unittest discover -s tests -v
```

These are initial versioned contracts and synthetic fixtures. They have not
yet been exercised against real Paperclip/MemPalace event streams or a live
Context Resolver. The separate Milestone 1.2 native Paperclip issue-policy
mapping is documented in `docs/implementation/IMPLEMENTATION_KICKOFF.md`;
these schemas do not become Paperclip workflow state. Milestone 1.3 OpenSearch
projectors are not implemented here.
