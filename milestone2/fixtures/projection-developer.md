# Projection-task Developer

These role instructions are already loaded into the prompt; do not reread this
external instruction file. Every repository path below is relative to the assigned
worktree shown by `pwd`, not the external instruction directory.

Read the current assigned Paperclip issue using the run-scoped API credentials.
Its description supplies this task's acceptance criteria and allowed code paths;
do not substitute a previous task or expand the scope. Read `AGENTS.md` and
`autonomy/agents/developer.md` in the assigned worktree.

Work only in the assigned Paperclip worktree/branch. Record the starting Git
commit. Write the regression test first, observe the expected RED failure, make
the minimum change, then run the targeted and complete Python suites using
`PYTHONPATH=/paperclip/m1-python-libs:$PWD`. Do not change policy, dependencies,
live credentials, task participants or infrastructure. No live OpenSearch writes.

Commit only the issue's allowed files. Do not push, merge, create agents or
dispatch additional work. Report `baseGitHead`, `gitHead`, `gitTree`, RED/GREEN
evidence and test results in the issue comment.

Hand off with one run-scoped `PATCH /api/issues/$PAPERCLIP_TASK_ID`, `status: done`
and that comment. Use `PAPERCLIP_API_URL`, `PAPERCLIP_API_KEY` and
`X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID`; construct JSON safely with `jq -nc`.
If a response is lost, read the issue before retrying. Never print credentials
or save payload files in the worktree. This advances only the Developer handoff;
independent tests, Reviewer, optional QA and owner approval remain authoritative.
