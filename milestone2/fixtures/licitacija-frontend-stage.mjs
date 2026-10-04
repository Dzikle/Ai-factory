import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolveRunIssueId, resolveRunWorkspace } from '/paperclip/git-doc-validator-identity.mjs';
import { validateCommittedTask } from '/paperclip/git-handoff.mjs';

const mode = process.argv[2];
const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId || !agentId || !['tests', 'qa'].includes(mode)) throw Error('stage identity missing');
const headers = { authorization: `Bearer ${token}`, 'content-type': 'application/json' };
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
async function assertStage() {
  const r = await fetch(`${api}/api/issues/${issueId}`, { headers });
  if (!r.ok) throw Error('issue lookup failed');
  const issue = await r.json();
  if (issue.status !== 'in_review' || issue.executionState?.currentParticipant?.agentId !== agentId) throw Error('stage ownership mismatch');
}
await assertStage();
const artifactDir = `/paperclip/licita-help/results/${runId}`;
await mkdir(artifactDir, { recursive: true });
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  const env = { PATH: process.env.PATH, HOME: '/tmp',
    AIF_PLAYWRIGHT_MODULE: '/app/node_modules/.pnpm/playwright@1.62.1/node_modules/playwright',
    AIF_BROWSER_CDP: 'http://192.168.65.254:19223',
    ...(mode === 'qa' ? { AIF_QA_ARTIFACT_DIR: artifactDir } : {}) };
  const r = spawnSync('node', ['--test', 'src/test/js/account-import-help.browser.test.js'], {
    cwd: snapshot, env, encoding: 'utf8', timeout: 150000, maxBuffer: 256 * 1024 });
  execFileSync('git', ['diff', '--check'], { cwd: snapshot });
  const testDigest = createHash('sha256').update(await readFile(`${snapshot}/src/test/js/account-import-help.browser.test.js`)).digest('hex');
  return { exitCode: r.status, output: `${r.stdout ?? ''}\n${r.stderr ?? ''}`.slice(-12000), errorCode: r.error?.code ?? null, testDigest };
});
const passed = result.exitCode === 0 && !result.errorCode;
const evidence = { schemaVersion: 1, issueId, runId, agentId, mode, ...handoff,
  validationSource: 'credential-free isolated committed copy', ...result, verdict: passed ? 'passed' : 'failed' };
const bytes = Buffer.from(JSON.stringify(evidence) + '\n');
const artifactPath = `${artifactDir}/evidence.json`;
await writeFile(artifactPath, bytes, { flag: 'wx' });
const digest = createHash('sha256').update(bytes).digest('hex');
await assertStage();
const r = await fetch(`${api}/api/issues/${issueId}`, { method: 'PATCH',
  headers: { ...headers, 'x-paperclip-run-id': runId },
  body: JSON.stringify({ status: passed ? 'done' : 'in_progress',
    comment: `Independent frontend ${mode} ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${digest}; actual local-browser checks; no production/backend requests. ${result.output.slice(-2000)}` }) });
if (!r.ok) throw Error(`stage decision rejected ${r.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
