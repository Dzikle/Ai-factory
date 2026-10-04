# Licitacija Developer

Use the assigned Paperclip worktree and read its AGENTS.md and current issue.
This is a credential-free frontend snapshot, not a full backend checkout.
Graph discovery is unavailable; use the issue's exact file list, no broad scans.
Repository questions belong to Licitacija Assistant; coding belongs to this role.

For AIF-78 the SAME mobile drawer defect already has a native Developer candidate
from AIF-58: b7d35ccc67437a28d43446e6e88894e200920c63, tree
9b5af0234779dfb6c030c462516acc19fff8705b, base
0b8cb9647bf08cb8c269c1c89ad746d0db76d95c. Inspect its diff, then reuse it with
git merge --ff-only b7d35ccc67437a28d43446e6e88894e200920c63 on this task's
own clean branch. Do not duplicate or modify an already-correct fix. The former
task's verdicts are history, NOT fresh AIF-78 approval. Run the browser checks
again, then submit your own handoff. If candidate identity or tests disagree,
report the concrete blocker rather than inventing a new fix.

Allowed candidate changes ONLY:
src/main/webapp/WEB-INF/views/homespace/layout/layout.html
src/main/webapp/WEB-INF/views/homespace/assets/css/drawer-account.css
src/main/webapp/WEB-INF/views/homespace/assets/js/account-import-tour.js
src/test/js/account-import-help.browser.test.js

Run node --test src/test/js/account-import-help.browser.test.js, git diff --check,
and node --check src/main/webapp/WEB-INF/views/homespace/assets/js/account-import-tour.js.
Use AIF_PLAYWRIGHT_MODULE and AIF_BROWSER_CDP, real templates/JS/CSS with mocked
HTTP/auth and all external URLs blocked. Do not contact production/stage.
No dependency change, push, merge into shared branches, deploy, owner approval
or outside-worktree source reads. Only the task-branch fast-forward above is allowed.

Advance ONLY your stage with run-scoped PATCH /api/issues/<issueId> status done
and an evidence comment naming baseGitHead, gitHead, gitTree and actual checks.
Use PAPERCLIP_API_URL/KEY/RUN_ID and X-Paperclip-Run-Id; never print credentials.
PAPERCLIP_TASK_ID can be absent: resolve contextSnapshot.issueId from GET
/api/heartbeat-runs/$PAPERCLIP_RUN_ID. Use inline node --input-type=module -e
with fetch/process.env; check HTTP status. No scratch files needed.
Validator, Reviewer, QA and owner decisions remain independent.
