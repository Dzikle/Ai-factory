// Narrow first-task validation participant; Paperclip owns the review decision.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: issueId } = process.env;
if (!api || !token || !runId || !agentId || !issueId) throw new Error("missing Paperclip run identity");
const cwd = process.cwd();
if (!cwd.startsWith("/paperclip/m1-first-task-worktrees/")) {
  throw new Error(`validator is outside the issue worktree: ${cwd}`);
}
const headers = { authorization: `Bearer ${token}`, "content-type": "application/json" };
const me = await fetch(`${api}/api/agents/me`, { headers });
if (!me.ok || (await me.json()).id !== agentId) throw new Error("run identity mismatch");

const commandPath = path.join(cwd, "milestone1/project_git_docs.py");
const testPath = path.join(cwd, "tests/test_project_git_docs.py");
const commandBytes = await readFile(commandPath);
const testBytes = await readFile(testPath);
const check = spawnSync("python3", ["-m", "unittest", "tests.test_project_git_docs", "-v"], {
  cwd, encoding: "utf8", timeout: 90_000, maxBuffer: 64 * 1024,
  env: { ...process.env, PYTHONPATH: `/paperclip/m1-python-libs:${cwd}` },
});
const passed = check.status === 0 && !check.error;
const revision = spawnSync("git", ["rev-parse", "HEAD"], { cwd, encoding: "utf8" });
const evidence = {
  schemaVersion: 1, issueId, runId, agentId, cwd,
  check: "python3 -m unittest tests.test_project_git_docs -v",
  gitHead: revision.status === 0 ? revision.stdout.trim() : null,
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
    comment: `Deterministic first-task validation ${evidence.verdict}; evidence=file://${artifactPath} sha256=${digest}`,
  }),
});
if (!response.ok) throw new Error(`Paperclip rejected validator decision: ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
