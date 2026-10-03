# Read-only script discovery smoke

This is a discovery check, not a coding or publication task. Your only purpose
is to demonstrate that a fresh native agent can find the existing Factory
scripts through canonical instructions rather than inventing Git/API commands.

Start from the assigned worktree's `AGENTS.md`, follow its deterministic-command
pointers, and read the relevant publication guide and Developer/Reviewer role
restrictions. From that worktree, invoke the discovered publication module's
**preflight subcommand with `--help` only**. Do not run actual preflight or
publication. Do not run tests, modify files, create commits, push, merge, read
`.milestone0`/private state/environment/credentials, make API mutations, or
coordinate other agents. Do not follow a historical coding task's handoff.

Return one JSON object, no markdown, with these fields:

- `publicationModule`: the discovered Python module name;
- `guide`: repository-relative guide path;
- `preflightSubcommand`: its read-only candidate-inspection subcommand;
- `publicationSubcommand`: its owner-approved external-write subcommand;
- `testModule`: existing pinned full-suite module;
- `developerMayPublish`, `reviewerMayPublish`, `ownerApprovalRequired`: booleans
  according to current role/approval restrictions;
- `preflightHelpExecuted`: boolean according to the actual command result.

Discovery is not a grant of publication permission. If a file/command is
inaccessible, report the failure instead of guessing or requesting more access.
