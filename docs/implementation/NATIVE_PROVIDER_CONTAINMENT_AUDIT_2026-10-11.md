# Native provider containment follow-up — 2026-10-11

## Result

Static inspection found two unresolved Important source-policy gaps in Command
Code's current candidate. Do not qualify or enable that candidate on the strength
of the earlier source review. This audit is not a live exploit, runtime test,
authentication or admission proof. Existing production routing is unchanged.

The requested next work remains completion of the provider feature, followed by
one useful independently verified Factory improvement and measured outcomes.
This record identifies why the first step needs a design revision, not another
control plane or a relaxed sentinel-only qualification.

## Exact inspected artifact

- Paperclip source: `4665cb41ce3598429066fe91fc7ee4154abfd10b`.
- Factory documentation checkpoint: `15a2e7f6575e0c15a93f4908b754751a5de4bfc0`.
- npm package: `command-code@1.79.2`.
- Tarball: <https://registry.npmjs.org/command-code/-/command-code-1.79.2.tgz>.
- SHA-512 integrity, matched against the existing installer pin:
  `sha512-e7seLyyriUJtK5MArViSVRekCmRP5VCZrHgoURWayH7agAwvsE+nq+c0rt1dzVs/iD/lc5cMZLu9I0+SZnPORA==`.
- `package/dist/cli.mjs` SHA-256:
  `d976c2ad89f93a2b81af4d150dca99aeedfd679f15e8b8c032314e61e484da7b`.

Only the archive and five regular data/source files were downloaded/extracted
under the ignored Paperclip plan workspace. No npm install, package scripts,
CLI execution, login, inference, image build or live mutation occurred.
Archive entries were listed before selecting files; no symlinks were extracted.
Relevant bundled references are `command-code-knowledge/reference/permissions.md`,
`command-code-knowledge/reference/hooks.md`, and `mod-builder/reference/api.md`.

## Findings

1. **Deny-all is not zero tools.** In the pinned bundle, `createPermissions`
   returns allow for `ask_user_question`, `agent` and `run_command` before
   matching deny rules. Thus the candidate's permissions-only no-tool overlay
   does not establish the required tool prohibition. Coding denies naming
   `task`/`ask_user` likewise do not constrain those actual control-flow tools.
   The injected test runtime never exercises this native permission evaluator.

2. **Credential path rules use the wrong anchor.** The pinned
   `anchorPathPattern` resolves one leading slash beneath the project cwd;
   two slashes anchor at filesystem root. The candidate currently requires
   `Read(${home}/**)`, `Write(${home}/**)` and `Edit(${home}/**)`, using the
   wrong native interpretation for an absolute home. These rules do not prove
   denial of that home. This finding does not demonstrate credential access;
   it invalidates the claimed policy check.

The current [permission documentation](https://commandcode.ai/docs/permissions)
agrees with these pinned-source observations. Documentation alone was not used
to infer behavior of version 1.79.2.

## Candidate remedy and review boundary

The native mod API exposes `getActiveTools`/`setActiveTools`; its bundled reference
describes disabled tools as absent from schemas and refused at execution. This is
a possible enforcement seam, not a completed or qualified guard. See the
[mod overview](https://commandcode.ai/docs/mods) for discovery, not acceptance.

Recommended design direction: one immutable Factory-owned native guard, with an
empty tool set for no-tool phases and an explicit governed set for coding;
correct filesystem-root deny anchors; reject every unmanaged mod/config source.
The guard must be required and bound to artifact/policy identity, not activated
by an owner boolean. Its initialization, missing/failed-load behavior, direct
disabled-tool execution and session resume must be proven before enabling it.
Prompt instructions, ACP approval alone and ordinary shell hooks are insufficient
evidence. Native tool filtering is not operating-system sandboxing.

Alternatives: retain Command Code as unsupported and work on another provider's
native controls first; or select a different explicitly reviewed CLI pin that
already exposes the necessary controls. Neither silently changes runtime pins
or substitutes an API/provider-output runner. Relaxing the no-tool requirement
is not an acceptable implementation shortcut.

The existing approved plan explicitly requires a design revision if plugin
integration cannot satisfy its contracts. No revised guard design, implementation
plan or live-operation envelope is approved by this audit. Product code was not
changed. Cline and managed Claude remain unsupported pending their own controls.
