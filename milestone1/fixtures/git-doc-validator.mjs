// Narrow first-task validation participant; Paperclip owns the review decision.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import path from "node:path";
import { resolveRunIssueId, resolveRunWorkspace } from "./git-doc-validator-identity.mjs";
import { validateCommittedTask } from "./git-handoff.mjs";

const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId || !agentId) throw new Error("missing Paperclip run identity");
const headers = { authorization: `Bearer ${token}`, "content-type": "application/json" };
const me = await fetch(`${api}/api/agents/me`, { headers });
if (!me.ok || (await me.json()).id !== agentId) throw new Error("run identity mismatch");
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
const actualRoot = await realpath("/paperclip/m1-first-task-worktrees");
const actualCwd = await realpath(cwd);
if (!actualCwd.startsWith(`${actualRoot}/`)) throw new Error("validator worktree escapes its root");
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  const commandBytes = await readFile(path.join(snapshot, "milestone1/project_git_docs.py"));
  const testBytes = await readFile(path.join(snapshot, "tests/test_project_git_docs.py"));
  const check = spawnSync("python3", ["-m", "unittest", "tests.test_project_git_docs", "-v"], {
    cwd: snapshot, encoding: "utf8", timeout: 90_000, maxBuffer: 64 * 1024,
    env: { ...process.env, PYTHONPATH: `/paperclip/m1-python-libs:${snapshot}` },
  });
  return { commandBytes, testBytes, check };
});
const { commandBytes, testBytes, check } = result;
const passed = check.status === 0 && !check.error;
const evidence = {
  schemaVersion: 1, issueId, runId, agentId, cwd,
  check: "python3 -m unittest tests.test_project_git_docs -v",
  ...handoff,
  validationSource: "isolated_commit_copy",
  commandSha256: createHash("sha256").update(commandBytes).digest("hex"),
  testSha256: createHash("sha256").update(testBytes).digest("hex"),
  exitCode: check.status,
  errorCode: check.error?.code ?? null,
  output: `${check.stdout ?? ""}\n${check.stderr ?? ""}`.slice(-4000),
  verdict: passed ? "passed" : "failed",
};
const bytes = Buffer.from(JSON.stringify(evidence) + "\n");
const artifactDir = "/paperclip/milestone1-validation";
await mkdir(artifactDir, { recursive: true });
const artifactPath = path.join(artifactDir, `${runId}.json`);
try { await writeFile(artifactPath, bytes, { flag: "wx" }); }
catch (error) {
  if (error?.code !== "EEXIST" || !(await readFile(artifactPath)).equals(bytes)) throw error;
}
const digest = createHash("sha256").update(bytes).digest("hex");
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: "PATCH", headers: { ...headers, "x-paperclip-run-id": runId },
  body: JSON.stringify({
    status: passed ? "done" : "in_progress",
    comment: `Deterministic first-task validation ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${digest}`,
  }),
});
if (!response.ok) throw new Error(`Paperclip rejected validator decision: ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
