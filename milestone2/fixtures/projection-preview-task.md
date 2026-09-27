# Second engineering task: read-only projection preview

Add `--dry-run` to the existing `python -m milestone1.project_git_docs` command.
This lets an operator inspect pending projection changes without giving the
command a writer credential. It is a bounded extension of the existing
one-shot projector, not a new service or workflow engine.

Acceptance criteria:

- Preview uses the committed overlay and Git revision, with the same repository,
  canonical-path, transport, source-identity and expected-revision checks as apply.
- Only URL and non-admin reader credentials are required in preview mode.
  Do not instantiate a writer or read/use its credentials in that mode.
- Use the existing reconciliation algorithm to count all planned upserts and
  stale-document tombstones. Do not implement a separate diff algorithm.
- Preview performs searches only: no bulk, indexing, alias, permission or other
  mutation request, even when writer credentials happen to be present.
- Output preserves project/repository/revision/document identity fields and adds
  `dry_run: true`, `planned_writes: N`, `writes: 0`. Never report planned writes
  as actual writes. A repeated preview must not change the observed index.
- Ordinary apply retains its existing output and behavior, still requiring
  separate non-admin reader/writer credentials; replay remains idempotent.
- Missing paths, mismatched revision and malformed search responses fail closed.
- Add focused tests first, record their expected RED failure, implement the
  minimum change, then run the targeted and complete Python suites.

Allowed code scope: `milestone1/project_git_docs.py`,
`milestone1/opensearch_projection.py`, `tests/test_project_git_docs.py`, and
`tests/test_opensearch_projection.py`. Do not change canonical policies,
dependencies, live credentials, infrastructure, task policy or QA fixtures.

Work only in the assigned Paperclip task worktree/branch. Commit only those
files once tests pass; do not push or merge. Use the installed Python packages
with `PYTHONPATH=/paperclip/m1-python-libs:$PWD python3 -m unittest ...`.
No production OpenSearch mutation is needed to implement this task.

Report the commit, RED/GREEN evidence and tests in a Paperclip issue comment.
Then submit status `done` using your run-scoped Paperclip credentials to hand
off to the existing Validator, separate Reviewer and independent functional QA.
This is not final human approval. Do not approve another participant's stage.

Never print credentials. Do not create further agents or perform other tasks.
