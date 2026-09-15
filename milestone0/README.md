# Milestone 0 dependency admission harness

This directory contains only reproducible dependency-admission configuration,
fixtures, and evidence. It is not an AI Factory runtime implementation.

Every selected upstream is pinned in `dependencies.lock.yaml`. Container
profiles bind only to loopback and use project-specific names, ports, networks,
and volumes so they do not alter unrelated host services. Supply high-entropy
values through the named `AIF_M0_*` environment variables; never commit them.

The Paperclip context adapter and model endpoints are throwaway test doubles.
They exist to characterize extension and recovery behavior. They must not be
promoted into V1 components.

Admission results, exact commands, observed image IDs, fault injections, and
remaining blockers are recorded in
`docs/implementation/MILESTONE_0_DEPENDENCY_ADMISSION.md` after execution.

The current result is intentionally not a deployable V1 stack: Paperclip is
blocked at its pinned revision. The LiteLLM server config is retained only as
evidence of the evaluated proxy profile; the admitted raw-API mechanics probe
uses the MIT core Router and excludes the proprietary proxy dependency.
