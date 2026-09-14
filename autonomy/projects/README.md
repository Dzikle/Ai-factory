# Project Overlays

AI Factory core must remain project-independent.

Each project overlay may provide:

- repository bindings;
- project architecture and feature docs;
- allowed/default skills;
- allowed capability providers;
- deployment restrictions;
- secret/tool bindings;
- project-specific policies;
- acceptance rules;
- memory namespace;
- OpenSearch project filters.

Conceptually:

```text
Generic AI Factory
    +
Project Overlay
    =
Runnable project-specific engineering organization
```

Do not hard-code the first project's implementation conventions into the reusable core unless they are proven generic engineering rules.
