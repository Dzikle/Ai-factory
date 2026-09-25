import { createServer } from "node:http";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import test from "node:test";

const script = fileURLToPath(new URL("./validation-agent.mjs", import.meta.url));

async function exercise(source, expectedStatus, patchStatus = 200) {
  const directory = await mkdtemp(join(tmpdir(), "aif-validation-"));
  const target = join(directory, "target.mjs");
  const artifactDir = join(directory, "artifacts");
  await writeFile(target, source);
  const patches = [];
  const server = createServer(async (req, res) => {
    if (req.headers.authorization !== "Bearer scoped-token") {
      res.writeHead(401).end();
      return;
    }
    if (req.url === "/api/agents/me" && req.method === "GET") {
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ id: "validator-id" }));
      return;
    }
    if (req.url === "/api/issues/task-id" && req.method === "PATCH") {
      let body = "";
      for await (const chunk of req) body += chunk;
      patches.push(JSON.parse(body));
      res.writeHead(patchStatus, { "content-type": "application/json" });
      res.end(JSON.stringify(patchStatus === 200 ? { status: expectedStatus } : { error: "rejected" }));
      return;
    }
    res.writeHead(404).end();
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const port = server.address().port;
    const child = spawn(process.execPath, [script], {
      env: {
        ...process.env,
        PAPERCLIP_AGENT_ID: "validator-id",
        PAPERCLIP_RUN_ID: "validation-run",
        PAPERCLIP_TASK_ID: "task-id",
        PAPERCLIP_API_KEY: "scoped-token",
        PAPERCLIP_API_URL: `http://127.0.0.1:${port}`,
        AIF_M1_CHECK_ROOT: directory,
        AIF_M1_CHECK_TARGET: target,
        AIF_M1_ARTIFACT_DIR: artifactDir,
      },
    });
    let stderr = "";
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    const exitCode = await new Promise((resolve) => child.on("exit", resolve));
    if (patchStatus === 200) assert.equal(exitCode, 0, stderr);
    else assert.notEqual(exitCode, 0, "a rejected Paperclip decision cannot pass the run");
    assert.equal(patches.length, 1);
    assert.equal(patches[0].status, expectedStatus);
    assert.match(patches[0].comment, /sha256=[a-f0-9]{64}/);
    const bytes = await readFile(join(artifactDir, "validation-run.json"));
    assert.ok(patches[0].comment.includes(createHash("sha256").update(bytes).digest("hex")));
    const evidence = JSON.parse(bytes);
    assert.equal(evidence.verdict, expectedStatus === "done" ? "passed" : "failed");
    assert.equal(evidence.targetSha256, createHash("sha256").update(source).digest("hex"));
  } finally {
    await new Promise((resolve) => server.close(resolve));
    await rm(directory, { recursive: true, force: true });
  }
}

test("successful deterministic check advances only with content-addressed evidence", async () => {
  await exercise("export const answer = 42;\n", "done");
});

test("failed deterministic check requests changes rather than approving", async () => {
  await exercise("export const = ;\n", "in_progress");
});

test("Paperclip rejection fails the run, never reports success", async () => {
  await exercise("export const answer = 42;\n", "done", 422);
});
