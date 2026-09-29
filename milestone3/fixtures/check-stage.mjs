// Reuse Paperclip's issue identity and committed-copy validation, not stage state.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveRunIssueId, resolveRunWorkspace } from "../../milestone1/fixtures/git-doc-validator-identity.mjs";
import { validateCommittedTask } from "../../milestone1/fixtures/git-handoff.mjs";

const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
const mode = process.argv[2];
if (!api || !token || !runId || !agentId || !["tests", "qa"].includes(mode)) throw new Error("missing check-stage identity");
const headers = { authorization: `Bearer ${token}`, "content-type": "application/json" };
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
const root = await realpath("/paperclip/m1-first-task-worktrees");
if (!(await realpath(cwd)).startsWith(`${root}/`)) throw new Error("stage worktree escapes its root");
async function requireStage() {
  const response = await fetch(`${api}/api/issues/${issueId}`, { headers });
  if (!response.ok) throw new Error("stage issue lookup failed");
  const issue = await response.json();
  if (issue.status !== "in_review" || issue.executionState?.currentParticipant?.agentId !== agentId) {
    throw new Error("this agent does not own the current stage");
  }
}
await requireStage();
const qaScript = fileURLToPath(new URL("./check_qa.py", import.meta.url));
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  const commandSha256 = createHash("sha256").update(await readFile(path.join(snapshot, "milestone3/check.py"))).digest("hex");
  const testSha256 = createHash("sha256").update(await readFile(path.join(snapshot, "tests/test_check.py"))).digest("hex");
  const check = spawnSync("python3", mode === "tests" ? ["-m", "unittest", "discover", "-s", "tests", "-q"] : [qaScript, "-v"], {
    cwd: snapshot, encoding: "utf8", timeout: 120_000, maxBuffer: 64 * 1024,
    env: { PATH: process.env.PATH, PYTHONPATH: `/paperclip/m1-python-libs:${snapshot}` },
  });
  return { check, commandSha256, testSha256 };
});
const passed = result.check.status === 0 && !result.check.error;
const evidence = {
  schemaVersion: 1, issueId, runId, agentId, ...handoff,
  validationSource: "isolated_commit_copy", check: `memory-promotion ${mode}`,
  commandSha256: result.commandSha256, testSha256: result.testSha256,
  qaScriptSha256: mode === "qa" ? createHash("sha256").update(await readFile(qaScript)).digest("hex") : null,
  exitCode: result.check.status, errorCode: result.check.error?.code ?? null,
  output: `${result.check.stdout ?? ""}\n${result.check.stderr ?? ""}`.slice(-6000),
  verdict: passed ? "passed" : "failed",
};
const bytes = Buffer.from(JSON.stringify(evidence) + "\n");
const artifactDir = "/paperclip/milestone3-validation";
await mkdir(artifactDir, { recursive: true });
const artifactPath = `${artifactDir}/${runId}.json`;
try { await writeFile(artifactPath, bytes, { flag: "wx" }); }
catch (error) { if (error?.code !== "EEXIST" || !(await readFile(artifactPath)).equals(bytes)) throw error; }
const sha256 = createHash("sha256").update(bytes).digest("hex");
await requireStage();
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: "PATCH", headers: { ...headers, "x-paperclip-run-id": runId },
  body: JSON.stringify({ status: passed ? "done" : "in_progress",
    comment: `Independent memory-promotion ${mode} ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${sha256}; credential-free committed-copy checks.`,
  }),
});
if (!response.ok) throw new Error(`Paperclip rejected stage decision: ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256 }));
