# Milestone 1 Git contracts

`v1/` contains JSON Schema Draft 2020-12 contracts for the first policy-input
slice: project overlays, Agent Skills sidecars, logical capability definitions,
and role restrictions. The examples and POC skill sidecars are validated by
`tests/test_milestone1_contracts.py`.

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

Validate the first slice from the repository root:

```powershell
uv run --no-project --with 'jsonschema==4.25.1' --with 'PyYAML==6.0.2' python -m unittest discover -s tests -p 'test_milestone1_contracts.py' -v
```

The remaining Milestone 1.1 contracts (context/provenance/budgets, normalized
events, memory, model selection, and validation/review outcomes), Paperclip
policy materialization, and OpenSearch projectors are not implemented here.
