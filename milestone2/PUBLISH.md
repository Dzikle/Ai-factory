# Script-first publication

`python -m milestone2.publish` replaces repeated manual Git preflight,
approved-tree publication and receipt commands. Python 3.11+, Git and (for
GitHub remotes) `gh` are the only requirements. No new service or task engine.
Run from the AI Factory repository root. Prefix with `uv run --offline
--no-project` if Python is available only through the existing runtime.

## Inputs and commands

Save a plan under an ignored directory such as `.milestone0/publication/`:

```json
{
  "schemaVersion": 1,
  "issueId": "00000000-0000-0000-0000-000000000030",
  "decisionId": "00000000-0000-0000-0000-000000000040",
  "remoteUrl": "git@github-private:Dzikle/example.git",
  "githubAccount": "Dzikle",
  "baseBranch": "main",
  "baseCommit": "1111111111111111111111111111111111111111",
  "candidateCommit": "2222222222222222222222222222222222222222",
  "branch": "fix/aif-58-example",
  "allowedPaths": ["frontend/index.html", "frontend/profile.html"]
}
```

These are **placeholders**, not approval or runnable task evidence. Supply the
actual completed Paperclip issue/last decision UUID, exact Git commits already
available in the target repository, exact origin push URL and reviewed path
scope. Do not use mutable refs for commit fields. No automatic fetch/import,
test execution or candidate discovery: the existing task's Validator/Reviewer
and optional QA must already have checked this candidate. The command verifies
completed native stages and owner approval; it does not independently prove
what every reviewer tested from those stage flags.

```powershell
python -m milestone2.publish preflight --repo C:/path/to/target-repo --plan .milestone0/publication/plan.json
```

Preflight validates the root, exact configured push URL, GitHub account (when
applicable), base ancestry, candidate tree, changed-path scope and whitespace.
It emits JSON with `planSha256`, `tree`, `patchSha256`, `changedPaths`,
`dirtyCheckout` and the exact `approvalText`. It is read-only; dirty local files
are reported, not staged/discarded or included in the candidate.

The owner records the emitted `approvalText` **as a standalone line in a
Paperclip comment on that issue**. Publication approval is explicit: a generic
"approved" status alone does not authorize pushing an arbitrary repository,
branch or commit. The plan digest binds all inputs, including the current
completed decision. Changing any input requires fresh approval. This script
never creates the approval comment or advances/approves a task itself.

```powershell
$env:AIF_PAPERCLIP_STATE = '.milestone0/path/to/existing-private-board-state.json'
python -m milestone2.publish publish --repo C:/path/to/target-repo --plan .milestone0/publication/plan.json --approval-comment 00000000-0000-0000-0000-000000000050 --receipt .milestone0/publication/receipt.json
```

Use the actual owner-authored comment UUID. The existing state file supplies
`baseUrl`, `companyId`, `userId`, `boardApiKey`; tokens never enter plans,
receipts or command arguments. Paperclip must be reachable for publication.
Non-loopback HTTP, embedded credentials and API redirects are refused.

For GitHub, the current `gh` account (or process-scoped `GH_TOKEN`) must match
`githubAccount`. No global account switch is performed. Accepted remotes are
credential-free HTTPS `github.com`, SSH `git@github.com:...`, or the existing
`git@github-private:...` alias. SSH credentials/alias resolution remain owned
by the operator's trusted SSH configuration; the `gh` check is not proof of
SSH key identity. An absolute **local bare repository** is also accepted for
offline tests; omit `githubAccount` in that case.

## What publication does

1. Revalidates the completed Paperclip decision and live owner comment.
2. Creates one deterministic Git commit with the **exact reviewed tree** and
   approved base as its sole parent. Its SHA differs from the native candidate;
   tree identity and a binary diff SHA-256 bind the bytes. Intermediate candidate
   history is intentionally not published. HEAD, branch, index and local files
   are not changed. Hooks/external diff helpers and ambient Git repository/index
   overrides are disabled; no tags are pushed.
3. Requires the remote base branch still to equal `baseCommit` before a new
   publication. The target must be new, or already contain this exact publication
   commit. Only `fix/`, `feat/`, `chore/`, `docs/`, `test/` branches are supported;
   no merge, protected/deployment-branch write or deployment is implemented.
   Git's **empty expected-ref lease** is a creation-only compare-and-set:
   `--force-with-lease=refs/heads/<feature>:`. It prevents a concurrent creator
   from being fast-forwarded; it never authorizes updating an existing ref.
4. Journals an uncertain push before sending it, then independently reads back
   the exact remote SHA. An error/lost response is not treated as proof of failure
   or retried blindly. Exact remote read-back is the success criterion.
5. Saves public evidence and posts an idempotently keyed Paperclip comment with
   `reopen`, `resume` and `interrupt` explicitly false. Reads back the receipt.
   Paperclip owns task/approval state; the local JSON is external-write evidence,
   not another task ledger. It must be outside the target checkout or Git-ignored.

## Results and recovery

Exit `0` with `status=recorded` means the exact remote commit and Paperclip
receipt were both observed. Other results exit nonzero; error output suppresses
raw Git/GitHub/API responses that may contain secrets.

| Saved status | Meaning / action |
| --- | --- |
| `push_uncertain` | A push was attempted or could have been attempted. Rerun the same plan: only an exact existing remote SHA permits continuation. If absent/different, stop and reconcile; no automatic repush. Preserve the receipt, check no prior process is still running, and prepare a fresh explicitly approved plan if another attempt is needed. |
| `pushed_receipt_pending` | Git push confirmed, Paperclip evidence not confirmed. Rerun the same plan after Paperclip recovers; it records evidence without pushing again. |
| `recorded` | Complete. Replaying reconciles the same commit/comment without duplicates. |

A receipt belonging to another plan is never overwritten. A bounded receipt
lookup covers at most 500 comments; larger histories require explicit
reconciliation instead of a blind POST. Paperclip's native `clientRequestId`
uniqueness handles comment replay; no custom server mutation is needed.

This is the owner-approved **trusted-local** profile. Publication authorization
is rechecked immediately before the push, but Paperclip approval revocation and
Git cannot be one atomic transaction. Do not concurrently edit/revoke the plan
while publishing. Repository/SSH configuration and operator environment remain
trusted. Branch-prefix checks cannot infer arbitrary project CI deployment
rules: select a non-deploying feature branch in the approved plan.

## Verification boundary

`tests/test_publish.py` exercises real temporary Git repositories and bare
remotes, with a small HTTP fixture only at the Paperclip boundary. It covers
scope/approval denial, dirty index/worktree preservation, unrelated-history
exclusion, competing branch creation, uncertain push reconciliation, receipt
replay and board-token redirect containment. GitHub account checks use a fake
external `gh` response. No real GitHub push or live Paperclip execution is
claimed by this test suite. No Docker service/image is started or changed.

```powershell
uv run --offline --no-project python -m unittest discover -s tests -p test_publish.py -v
uv run --offline --no-project --with 'jsonschema[format]==4.25.1' --with 'PyYAML==6.0.2' python -m milestone3.check
```

Later scripts should automate the next actually repeated mechanical step,
reusing existing commands. PR creation/merge/deployment, generic task workflows,
service lifecycle and automatic test-command generation are not part of this
first batch.

## Agent discovery — verified 2026-10-03

`AGENTS.md`, the autonomy index, role instructions and the deployed
Developer/Reviewer fixtures now point to these commands. The existing runtime
source and knowledge projection were refreshed, without rewriting old task
worktrees. A fresh native OpenCode run **AIF-60** discovered this guide and
successfully executed `python3 -m milestone2.publish preflight --help`. Its
structured answer retained the Developer/Reviewer no-publication restriction
and owner-approval requirement. This proves representative command discovery,
not every harness, permission isolation or live publication.
[Evidence and limits](results/script-discovery-20261003.json).

The read-only proof checker verifies saved native run identity, immutable
source revision, typed answers and actual completed CLI execution. It dispatches
no agent and performs no publication. Keep native logs and board credentials
private; the committed record contains only selected public evidence.

```powershell
python -m milestone2.scripts.script_discovery_proof --run .milestone0/script-discovery-live-inline-final-20261003/native-run.json --log .milestone0/script-discovery-live-inline-final-20261003/native-log.json --revision f2ccf4dc85e27991850a2ea734af3def1b9dc130
```
