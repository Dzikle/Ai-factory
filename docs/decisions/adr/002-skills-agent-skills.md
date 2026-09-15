# ADR 002: Adopt Agent Skills as the portable skill format

**Status:** Accepted

**Date:** 2026-09-15

## Context

AI Factory skills must be model/runtime agnostic, versioned, composable, lazily
loaded, and compatible with role/capability restrictions. A private skill schema
would reduce portability and duplicate an emerging external standard.

## Decision

Adopt the [Agent Skills specification](https://agentskills.io/specification) and
reference implementation at commit
`69ef37e9424c0a7ea9dd2293b559e43ec8176379` (`skills-ref` 0.1.0,
Apache-2.0). Canonical AI Factory skills are Git-tracked directories containing
`SKILL.md`. Paperclip synchronizes/installs them as runtime copies.

Use string-valued, namespaced `metadata` keys for compact discovery values and
an optional `ai-factory.yaml` sidecar for structured roles, required/optional/
denied capabilities, lifecycle, risk, and eval references. The sidecar extends
AI Factory policy without claiming to extend the external specification.

## Evidence

The format supports a required name/description, Markdown instructions, optional
scripts/references/assets, arbitrary string metadata, and progressive disclosure:
metadata at discovery, full `SKILL.md` on activation, resources on demand. The
reference client guide supports file-read and prompt/tool activation styles.

The POC supplies `repository-discovery` and `code-review`. Both validate with
`skills-ref`; `read-properties` and `to-prompt` consume the same canonical
packages. See `docs/implementation/pocs/agent-skills/`.

## Authority boundary

The specification owns package compatibility. Git owns AI Factory skill content
and versions. Paperclip rows/installations and OpenSearch documents are derived.
Paperclip's MCP gateway—not `allowed-tools`, prompts, or sidecar text—owns active
authorization.

## Alternatives

- **Custom AI Factory skill schema:** rejected; required metadata fits standard
  namespaced metadata plus an optional sidecar.
- **Paperclip-only database skills:** rejected as canonical source because they
  would reduce cross-runtime portability and reviewability.

## Consequences

Every runtime adapter needs only standard discovery/activation plus sidecar
policy validation. CI validates schema, references, capability existence, role
compatibility, version changes, and eval links. Skills remain selectively loaded.

## Risks

External clients differ in resource and `allowed-tools` support. AI Factory must
not assume a client enforces permissions. Sidecar evolution needs a versioned
schema and compatibility tests.

## Exit/replacement strategy

Skills remain readable Markdown directories. A new loader or future standard can
consume/export the same files; the capability sidecar is independently versioned.
