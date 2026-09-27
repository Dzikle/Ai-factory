// Independent functional QA for the projection CLI; Paperclip owns the stage.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolveRunIssueId, resolveRunWorkspace } from "../../milestone1/fixtures/git-doc-validator-identity.mjs";
import { validateCommittedTask } from "../../milestone1/fixtures/git-handoff.mjs";

const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId || !agentId) throw new Error("missing Paperclip run identity");
const headers = { authorization: `Bearer ${token}`, "content-type": "application/json" };
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
const root = await realpath("/paperclip/m1-first-task-worktrees");
if (!(await realpath(cwd)).startsWith(`${root}/`)) throw new Error("QA worktree escapes its root");
async function requireStage() {
  const response = await fetch(`${api}/api/issues/${issueId}`, { headers });
  if (!response.ok) throw new Error("QA issue lookup failed");
  const issue = await response.json();
  if (issue.status !== "in_review" || issue.executionState?.currentParticipant?.agentId !== agentId) {
    throw new Error("this agent does not own the current QA stage");
  }
}
await requireStage();
const script = fileURLToPath(new URL("./projection_preview_qa.py", import.meta.url));
const scriptSha256 = createHash("sha256").update(await readFile(script)).digest("hex");
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  return spawnSync("python3", [script, "-v"], {
    cwd: snapshot, encoding: "utf8", timeout: 100_000, maxBuffer: 64 * 1024,
    // No run, board, model or OpenSearch credential crosses into tested code.
    env: { PATH: process.env.PATH, PYTHONPATH: `/paperclip/m1-python-libs:${snapshot}` },
  });
});
const passed = result.status === 0 && !result.error;
const evidence = {
  schemaVersion: 1, issueId, runId, agentId, ...handoff,
  validationSource: "isolated_commit_copy", check: "independent projection preview CLI QA",
  scriptSha256, exitCode: result.status, errorCode: result.error?.code ?? null,
  output: `${result.stdout ?? ""}\n${result.stderr ?? ""}`.slice(-6000),
  verdict: passed ? "passed" : "failed",
};
const bytes = Buffer.from(JSON.stringify(evidence) + "\n");
const artifactDir = "/paperclip/milestone2-qa";
await mkdir(artifactDir, { recursive: true });
const artifactPath = `${artifactDir}/${runId}.json`;
try { await writeFile(artifactPath, bytes, { flag: "wx" }); }
catch (error) {
  if (error?.code !== "EEXIST" || !(await readFile(artifactPath)).equals(bytes)) throw error;
}
const sha256 = createHash("sha256").update(bytes).digest("hex");
await requireStage();
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: "PATCH", headers: { ...headers, "x-paperclip-run-id": runId },
  body: JSON.stringify({ status: passed ? "done" : "in_progress",
    comment: `Independent functional QA ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${sha256}; no live OpenSearch writes or credentials in CLI tests.`,
  }),
});
if (!response.ok) throw new Error(`Paperclip rejected QA decision: ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256 }));
