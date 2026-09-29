// A bounded checker attached to existing native review stages, not a scheduler.
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
if (!api || !token || !runId || !agentId || !["tests", "qa"].includes(mode)) throw new Error("missing evaluation stage identity");
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
const source = fileURLToPath(new URL("../../", import.meta.url));
const qaScript = fileURLToPath(new URL("./scorecard_qa.py", import.meta.url));
const candidateFile = "milestone2/scorecard.py";
const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  const base = spawnSync("git", ["rev-parse", "HEAD"], { cwd: source, encoding: "utf8", timeout: 10_000 });
  if (base.status !== 0) throw new Error("evaluation base lookup failed");
  const baseGitHead = base.stdout.trim();
  const scopeScript = `import ast, pathlib, subprocess, sys
base, reference = sys.argv[1:]
subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],check=True,capture_output=True)
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],text=True).splitlines()
assert changed and set(changed)<= {'milestone2/scorecard.py','tests/test_scorecard_format.py'}, 'candidate scope changed'
def protected(p):
    tree=ast.parse(pathlib.Path(p).read_text())
    tree.body=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) or n.name!='format_scorecard']
    return ast.dump(tree,include_attributes=False)
assert protected('milestone2/scorecard.py')==protected(reference), 'collector was modified'
`;
  const env = { PATH: process.env.PATH, PYTHONPATH: `/paperclip/m1-python-libs:${snapshot}` };
  const scope = spawnSync("python3", ["-c", scopeScript, baseGitHead, path.join(source, candidateFile)], {
    cwd: snapshot, encoding: "utf8", timeout: 15_000, maxBuffer: 8192, env,
  });
  const check = scope.status === 0 && !scope.error ? spawnSync("python3",
    mode === "tests" ? ["-m", "unittest", "discover", "-s", "tests", "-q"] : [qaScript, "-v"], {
      cwd: snapshot, encoding: "utf8", timeout: 120_000, maxBuffer: 64 * 1024, env,
    }) : scope;
  return { check, baseGitHead, commandSha256: createHash("sha256").update(await readFile(path.join(snapshot, candidateFile))).digest("hex") };
});
const passed = result.check.status === 0 && !result.check.error;
const evidence = { schemaVersion: 1, issueId, runId, agentId, ...handoff,
  validationSource: "isolated_commit_copy", check: `scorecard ${mode}`,
  baseGitHead: result.baseGitHead, commandSha256: result.commandSha256,
  qaScriptSha256: mode === "qa" ? createHash("sha256").update(await readFile(qaScript)).digest("hex") : null,
  exitCode: result.check.status, errorCode: result.check.error?.code ?? null,
  output: `${result.check.stdout ?? ""}\n${result.check.stderr ?? ""}`.slice(-6000), verdict: passed ? "passed" : "failed" };
const bytes = Buffer.from(JSON.stringify(evidence) + "\n");
const artifactDir = "/paperclip/milestone4-validation";
await mkdir(artifactDir, { recursive: true });
const artifactPath = `${artifactDir}/${runId}.json`;
try { await writeFile(artifactPath, bytes, { flag: "wx" }); }
catch (error) { if (error?.code !== "EEXIST" || !(await readFile(artifactPath)).equals(bytes)) throw error; }
const sha256 = createHash("sha256").update(bytes).digest("hex");
await requireStage();
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: "PATCH", headers: { ...headers, "x-paperclip-run-id": runId },
  body: JSON.stringify({ status: passed ? "done" : "in_progress",
    comment: `Independent scorecard ${mode} ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${sha256}; isolated commit, stripped credentials. ${evidence.output}` }),
});
if (!response.ok) throw new Error(`native stage handoff failed: ${response.status}`);
console.log(JSON.stringify({ issueId, runId, stage: mode, verdict: evidence.verdict, artifactPath, sha256 }));
if (!passed) process.exitCode = 1;
