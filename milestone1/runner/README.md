# Isolated native Codex runner (Milestone 1 admission)

This image adds SSH and pinned Python test dependencies to the admitted
Paperclip/Codex image. Paperclip's built-in `codex_local` SSH transport copies
the task worktree and an allowlisted Codex home into `/runner/workspace`; the
runner does not mount the host repository, Paperclip storage, Docker socket,
database, or any model credential. Paperclip remains task/run/workspace owner.

The current local instance uses a dedicated `aif-m1-runner-net` bridge with only
Paperclip and this runner attached. The runner is non-root, drops all Linux
capabilities, has a read-only root filesystem, and uses tmpfs for the workspace,
home, `/tmp`, and `/run`. A named volume holds only the SSH host key and the
client *public* key. The SSH private client key is stored in Paperclip's secret
store. Host-key checking is strict. No port is published to the Windows host.

Docker's default seccomp profile prevents Codex's `bwrap` from creating a user
namespace. This **task-scoped, trusted-repository admission runner** therefore
uses `seccomp=unconfined`; the shared Paperclip controller does not. This is a
security tradeoff, not a general-purpose untrusted-code sandbox. Replace it
with a narrowly reviewed seccomp profile or a stronger sandbox provider before
untrusted repository execution. Codex's own sandbox remains enabled.

Local image: `aif-m1-codex-ssh-runner@sha256:b0bf27db91ddf5737b797f003a6ed570fec0191df0f35005c53c218c77ebfdd2`.
Base image: `aif-paperclip-fork:62760ac@sha256:2c574c948ce21a22cf6e8bbcf136b99b8e55bd2d460042ec69fa62bbbc224455`.
The runner image digest must be re-recorded after any rebuild.

Admission checks: Paperclip SSH environment probe; SSH from controller with
strict host-key checking; `codex sandbox -- sh -lc 'echo sandbox_ok'` in the
runner; `unshare -Ur true`; Python import of `yaml` and `jsonschema`; and
negative DNS lookup for the PostgreSQL service. These checks establish runner
mechanics. The separate AIF-42 native Developer/Validator/Reviewer proof and
AIF-43 child-kill/recovery proof are recorded in
`docs/implementation/IMPLEMENTATION_KICKOFF.md`; they do not remove the
trusted-repository-only seccomp exception or the need to supervise the MCP
service before repeatable production use.
