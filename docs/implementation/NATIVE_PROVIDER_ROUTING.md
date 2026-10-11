# Native provider profile selection

Source integration is not installation, authentication, availability, or coding
qualification. Cline and Command Code catalogue entries remain disabled and have
no guessed model, provider, account, or spending tier. Claude also remains disabled.
The existing OpenCode/Codex intake and Tests/Reviewer/QA bindings are unchanged.

Enabling an additional coding profile requires an already-provisioned isolated
Paperclip agent, an owner-authorized admission, and exact nonsecret references:
`provider`, `accountRef`, `runtimePin`, `credentialVersionRef`, and project
`profileBindings` containing `agentId`, `qualificationRunId`, `bindingFingerprint`.
Native profiles permit only free/subscription tiers with `maxPaidUsd: 0`.

Provisioning reads every enabled project's current controller admission before
deployment or the first board write. Routing reads
`GET /api/agents/:id/native-provider-admission?projectId=...`; this uses normal
company resource-read authorization, recomputes the current immutable runtime,
credential version, selected role instructions, policy, workspace, and MCP binding,
and performs no inference. Admission mutation remains owner-only. Python mirrors
the compact sorted-key UTF-8 SHA-256 contract but cannot grant admission itself.

The selected Developer must match current controller state and saved admission,
not just `usageJson.model` or a registry `qualified` flag. Pending plans revalidate
their original selection and preserve their original audit; they never silently
choose another provider. Free precedes subscription, high-risk work requires
subscription, and analysis/Tests/Reviewer/QA policy is unchanged.
