import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { resolveRunIssueId, resolveRunWorkspace } from '/paperclip/git-doc-validator-identity.mjs';
import { validateCommittedTask } from '/paperclip/git-handoff.mjs';
import { assertMobileWorkspace, mobileChildEnvironment, mobileCommands } from '/paperclip/licitacija-mobile-policy.mjs';

const mode = process.argv[2];
const commands = mobileCommands(mode);
const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId || !agentId) throw new Error('stage identity missing');
if (Number(process.versions.node.split('.')[0]) !== 24) throw new Error('Node 24 controller required');
const projectId = '25196096-52aa-4cb9-9c5e-7a07ec790602';
const headers = { authorization: `Bearer ${token}`, 'content-type': 'application/json' };
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
await assertMobileWorkspace(cwd);
async function assertStage() {
  const response = await fetch(`${api}/api/issues/${issueId}`, { headers });
  if (!response.ok) throw new Error('issue lookup failed');
  const issue = await response.json();
  if (issue.projectId !== projectId || issue.status !== 'in_review'
      || issue.executionState?.currentParticipant?.agentId !== agentId) throw new Error('stage ownership mismatch');
}
await assertStage();
const config = JSON.parse(await readFile('/paperclip/licitacija-mobile-stage-config.json', 'utf8'));
if (config.projectId !== projectId || !/^[a-f0-9]{40}$/.test(config.baseGitHead)) {
  throw new Error('mobile source identity missing');
}
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async snapshot => {
  execFileSync('git', ['merge-base', '--is-ancestor', config.baseGitHead, 'HEAD'], {
    cwd: snapshot, timeout: 10_000, maxBuffer: 256 * 1024,
  });
  const changed = execFileSync('git', ['diff', '--name-only', '-z', config.baseGitHead, 'HEAD'], {
    cwd: snapshot, timeout: 10_000, maxBuffer: 256 * 1024, encoding: 'utf8',
  }).split('\0').filter(Boolean);
  if (changed.some(file => !file.startsWith('mobile/'))) throw new Error('mobile task changed a non-mobile path');
  const packageJson = JSON.parse(await readFile(`${snapshot}/mobile/package.json`, 'utf8'));
  if (packageJson.name !== 'licitacija-mk-mobile') throw new Error('unexpected mobile package');
  const cache = await mkdtemp(path.join(os.tmpdir(), 'aif-mobile-npm-'));
  try {
    const env = mobileChildEnvironment(cache);
    const records = [];
    function run(args, timeout) {
      const startedAt = Date.now();
      const child = spawnSync('npm', args, { cwd: `${snapshot}/mobile`, env, encoding: 'utf8',
        timeout, maxBuffer: 1024 * 1024 });
      const record = { command: ['npm', ...args], exitCode: child.status,
        errorCode: child.error?.code ?? null, signal: child.signal ?? null,
        durationMs: Date.now() - startedAt, output: `${child.stdout ?? ''}\n${child.stderr ?? ''}`.slice(-12_000) };
      records.push(record);
      return record.exitCode === 0 && !record.errorCode;
    }
    let passed = run(['ci', '--ignore-scripts', '--no-audit', '--no-fund'], 180_000);
    const validationStartedAt = Date.now();
    for (const args of commands) {
      if (!passed) break;
      const remaining = 600_000 - (Date.now() - validationStartedAt);
      if (remaining <= 0) {
        records.push({ command: ['npm', ...args], exitCode: null, errorCode: 'AIF_TOTAL_TIMEOUT',
          signal: null, durationMs: 0, output: 'validation budget exhausted before command start' });
        passed = false;
        break;
      }
      passed = run(args, remaining);
    }
    execFileSync('git', ['diff', '--check'], { cwd: snapshot, timeout: 10_000, maxBuffer: 256 * 1024 });
    return { passed, baseGitHead: config.baseGitHead, canonicalSourceRevision: config.canonicalSourceRevision,
      childEnvironmentKeys: Object.keys(env).sort(), commands: records };
  } finally {
    await rm(cache, { recursive: true, force: true });
  }
});
const artifactDir = `/paperclip/licitacija-mobile-results/${runId}`;
await mkdir(artifactDir, { recursive: true });
const evidence = { schemaVersion: 1, issueId, runId, agentId, mode, ...handoff,
  validationSource: 'credential-free isolated committed copy', ...result,
  verdict: result.passed ? 'passed' : 'failed', nativeDeviceTesting: false };
const bytes = Buffer.from(JSON.stringify(evidence) + '\n');
const artifactPath = `${artifactDir}/evidence.json`;
await writeFile(artifactPath, bytes, { flag: 'wx' });
const digest = createHash('sha256').update(bytes).digest('hex');
await assertStage();
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: 'PATCH', headers: { ...headers, 'x-paperclip-run-id': runId },
  body: JSON.stringify({ status: result.passed ? 'done' : 'in_progress',
    comment: `Independent mobile ${mode} ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${digest}; credential-free committed copy; no live API, native device build, app-store publication or deployment. ${result.commands.map(r => r.output).join('\n').slice(-2_000)}` }),
});
if (!response.ok) throw new Error(`stage decision rejected ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
