# AIF-58 — ready for owner integration approval

The factory's native OpenCode Developer produced the correction; fresh Validator,
native OpenCode Reviewer and independent QA approved the same committed candidate.
The dispatcher repair supplied no website code. No website merge/push/deployment.

Candidate: `b7d35ccc67437a28d43446e6e88894e200920c63`; tree:
`9b5af0234779dfb6c030c462516acc19fff8705b`; snapshot base:
`0b8cb9647bf08cb8c269c1c89ad746d0db76d95c`.

## What changed

The mobile drawer copied the account section without its page-only styles/help
initialization. Its help action is now styled and opens the existing account
guide automatically, retaining the application's context path. Normal profile
help still works. Only known own-property tour names can trigger auto-opening.
No second importer, dependency change or backend write.

Four paths changed: `homespace/layout/layout.html`,
`homespace/assets/css/drawer-account.css`,
`homespace/assets/js/account-import-tour.js` (under
`src/main/webapp/WEB-INF/views/`) and
`src/test/js/account-import-help.browser.test.js`.

## Evidence

[Validator](validator.json) and [QA](qa/evidence.json) independently passed **5/5**:
360/390/412px layout, existing guide through its final step, unexpected/inherited
tour names rejected, non-root context path retained, ordinary account help.
Their saved bytes match the SHA-256 recorded in each actual Paperclip decision.
Local Git attributes preserve those bytes on Windows checkouts. Generated patch
context lines contain required leading spaces; whitespace checking is performed
on the actual candidate diff and repository edits, not on nested patch syntax.
The [dispatcher receipt](../handoff-repair-20261003.json) identifies all fresh runs,
including the Reviewer's first no-verdict run and successful automatic retry.

Screenshots: [360px](qa/drawer-help-360.png), [390px](qa/drawer-help-390.png),
[412px](qa/drawer-help-412.png), [existing guide final step](qa/tour-final-step.png).
These are a credential-free partial frontend snapshot, with real template/JS/CSS
but mocked HTTP/auth. They do not claim a full backend or production-site test.

## Integration boundary

Two ordered, generated [patches](patches/) preserve the Developer's initial fix
and follow-up allowlist correction. They are review artifacts, not approval to
apply them. The user's licitacija.mk checkout has unrelated existing changes:
inspect patch applicability there, preserve those changes and do not transplant
the partial snapshot as the repository's new root. Paperclip AIF-58 stays at
the human approval stage until the owner explicitly approves integration.
