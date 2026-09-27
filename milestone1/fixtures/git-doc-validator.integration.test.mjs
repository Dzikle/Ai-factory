// Opt-in: run only in a disposable container with no live Paperclip volume.
import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { randomUUID, createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const enabled = process.env.AIF_VALIDATOR_INTEGRATION === "1";
const script = fileURLToPath(new URL("./git-doc-validator.mjs", import.meta.url));
const root = "/paperclip/m1-first-task-worktrees";

async function exercise(t, scenario) {
  await mkdir(root, { recursive: true });
  const cwd = await mkdtemp(`${root}/validator-handoff-`);
  const runId = randomUUID();
  const artifact = `/paperclip/milestone1-validation/${runId}.json`;
  t.after(async () => {
    await rm(cwd, { recursive: true, force: true });
    await rm(artifact, { force: true });
  });
  function git(...args) { return execFileSync("git", args, { cwd, encoding: "utf8" }).trim(); }
  git("init", "-q", "-b", "AIF-test");
  git("config", "user.name", "Validator integration");
  git("config", "user.email", "validator@example.invalid");
  await mkdir(path.join(cwd, "milestone1"));
  await mkdir(path.join(cwd, "tests"));
  await writeFile(path.join(cwd, ".gitignore"), "__pycache__/\n");
  await writeFile(path.join(cwd, "milestone1/project_git_docs.py"), "# committed code\n");
  await writeFile(path.join(cwd, "tests/__init__.py"), "");
  const transientScript = `import sys\nfrom pathlib import Path\np=Path(${JSON.stringify(path.join(cwd, "milestone1/project_git_docs.py"))})\np.write_text('# transient outside edit\\n')\nprint('changed', flush=True)\nsys.stdin.readline()\np.write_text('# committed code\\n')\n`;
  const body = scenario === "source_transient" ? `child = subprocess.Popen([sys.executable, '-c', ${JSON.stringify(transientScript)}], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)\n        self.assertEqual(child.stdout.readline().strip(), 'changed')\n        try:\n            self.assertEqual(Path('milestone1/project_git_docs.py').read_text(), '# committed code\\n')\n        finally:\n            child.communicate('restore\\n', timeout=5)`
    : scenario === "source_dirty_during" ? `Path(${JSON.stringify(path.join(cwd, "milestone1/project_git_docs.py"))}).write_text('# concurrent edit\\n')`
    : scenario === "source_commit_during" ? `Path(${JSON.stringify(path.join(cwd, "milestone1/project_git_docs.py"))}).write_text('# concurrent commit\\n'); subprocess.run(['git', '-C', ${JSON.stringify(cwd)}, 'commit', '-qam', 'Concurrent change'], check=True)`
    : scenario === "test_failure" ? "self.fail('intentional test failure')"
    : scenario === "dirty_during" ? "Path('milestone1/project_git_docs.py').write_text('# changed during tests\\n')"
    : scenario === "commit_during" ? "Path('milestone1/project_git_docs.py').write_text('# new commit\\n'); subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qam', 'changed'], check=True)"
    : "self.assertTrue(True)";
  await writeFile(path.join(cwd, "tests/test_project_git_docs.py"),
    `import unittest, subprocess, sys\nfrom pathlib import Path\nclass TestTask(unittest.TestCase):\n    def test_task(self):\n        ${body}\n`);
  git("add", ".");
  git("commit", "-qm", "Test task");
  const head = git("rev-parse", "HEAD");
  const tree = git("rev-parse", "HEAD^{tree}");
  if (scenario === "dirty_before") {
    await writeFile(path.join(cwd, "uncommitted.txt"), "unfinished\n");
  }
  const decisions = [];
  const server = http.createServer(async (req, res) => {
    res.setHeader("content-type", "application/json");
    if (req.headers.authorization !== "Bearer fixture-only") { res.writeHead(403).end("{}"); return; }
    if (req.url === "/api/agents/me") { res.end(JSON.stringify({ id: "validator" })); return; }
    if (req.url === `/api/heartbeat-runs/${runId}/issues`) { res.end(JSON.stringify([{ issueId: "task" }])); return; }
    if (req.url === `/api/heartbeat-runs/${runId}`) {
      res.end(JSON.stringify({ id: runId, agentId: "validator", contextSnapshot: {
        issueId: "task", paperclipWorkspace: { cwd, branchName: scenario === "wrong_branch" ? "other-task" : "AIF-test" },
      } }));
      return;
    }
    if (req.url === "/api/issues/task" && req.method === "PATCH") {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      assert.equal(req.headers["x-paperclip-run-id"], runId);
      decisions.push(JSON.parse(Buffer.concat(chunks)));
      res.end("{}");
      return;
    }
    res.writeHead(404).end("{}");
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const child = spawn(process.execPath, [script], { env: {
    ...process.env, PAPERCLIP_API_URL: `http://127.0.0.1:${server.address().port}`,
    PAPERCLIP_API_KEY: "fixture-only", PAPERCLIP_AGENT_ID: "validator",
    PAPERCLIP_RUN_ID: runId, PAPERCLIP_TASK_ID: "task",
  }, stdio: ["ignore", "pipe", "pipe"] });
  let output = "";
  child.stdout.on("data", (chunk) => { output += chunk; });
  child.stderr.on("data", (chunk) => { output += chunk; });
  const timer = setTimeout(() => child.kill("SIGKILL"), 20_000);
  const code = await new Promise((resolve, reject) => { child.on("error", reject); child.on("close", resolve); });
  clearTimeout(timer);
  assert.ok(!output.includes("fixture-only"), "credentials must not appear in output");
  return { code, decisions, artifact, head, tree, output };
}

test("clean committed validation approves only its recorded commit/tree", { skip: !enabled }, async (t) => {
  const result = await exercise(t, "clean");
  assert.equal(result.code, 0, result.output);
  assert.equal(result.decisions.length, 1);
  assert.equal(result.decisions[0].status, "done");
  const bytes = await readFile(result.artifact);
  const evidence = JSON.parse(bytes);
  assert.equal(evidence.gitHead, result.head);
  assert.equal(evidence.gitTree, result.tree);
  assert.equal(evidence.branchName, "AIF-test");
  assert.ok(result.decisions[0].comment.includes(`gitHead=${result.head} gitTree=${result.tree}`));
  assert.ok(result.decisions[0].comment.includes(`sha256=${createHash("sha256").update(bytes).digest("hex")}`));
});

for (const scenario of ["dirty_before", "dirty_during", "commit_during", "source_dirty_during", "source_commit_during", "wrong_branch"]) {
  test(`${scenario} cannot submit a review-stage decision`, { skip: !enabled }, async (t) => {
    const result = await exercise(t, scenario);
    assert.notEqual(result.code, 0);
    assert.match(result.output, /uncommitted|revision changed|branch differs/);
    assert.deepEqual(result.decisions, []);
  });
}

test("failed tests request changes, not approval", { skip: !enabled }, async (t) => {
  const result = await exercise(t, "test_failure");
  assert.equal(result.code, 0, result.output);
  assert.equal(result.decisions.length, 1);
  assert.equal(result.decisions[0].status, "in_progress");
  assert.equal(JSON.parse(await readFile(result.artifact)).verdict, "failed");
});

test("a synchronized outside edit cannot change the committed bytes under test", { skip: !enabled }, async (t) => {
  const result = await exercise(t, "source_transient");
  assert.equal(result.code, 0, result.output);
  assert.equal(result.decisions.length, 1);
  assert.equal(result.decisions[0].status, "done");
  const evidence = JSON.parse(await readFile(result.artifact));
  assert.equal(evidence.gitHead, result.head);
  assert.equal(evidence.validationSource, "isolated_commit_copy");
});
