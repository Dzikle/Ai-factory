// Test-only process adapter: deterministic check as a native Paperclip review participant.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import { join, relative, isAbsolute } from "node:path";
import process from "node:process";

const required = [
  "PAPERCLIP_AGENT_ID", "PAPERCLIP_RUN_ID",
  "PAPERCLIP_API_KEY", "PAPERCLIP_API_URL", "AIF_M1_CHECK_ROOT",
  "AIF_M1_CHECK_TARGET", "AIF_M1_ARTIFACT_DIR",
];
for (const name of required) {
  if (!process.env[name]) throw new Error(`missing ${name}`);
}

const headers = {
  authorization: `Bearer ${process.env.PAPERCLIP_API_KEY}`,
  "content-type": "application/json",
};
const identityResponse = await fetch(`${process.env.PAPERCLIP_API_URL}/api/agents/me`, { headers });
if (!identityResponse.ok) throw new Error(`identity lookup failed: ${identityResponse.status}`);
const identity = await identityResponse.json();
if (identity.id !== process.env.PAPERCLIP_AGENT_ID) throw new Error("run JWT identity mismatch");
let issueId = process.env.PAPERCLIP_TASK_ID || process.env.PAPERCLIP_ISSUE_ID;
if (!issueId) {
  const runResponse = await fetch(`${process.env.PAPERCLIP_API_URL}/api/heartbeat-runs/${process.env.PAPERCLIP_RUN_ID}`, { headers });
  if (!runResponse.ok) throw new Error(`own run lookup failed: ${runResponse.status}`);
  const run = await runResponse.json();
  issueId = run.contextSnapshot?.issueId || run.contextSnapshot?.taskId;
}
if (!issueId) {
  console.log(JSON.stringify({ runId: process.env.PAPERCLIP_RUN_ID, skipped: "no_task" }));
  process.exit(0);
}

const root = await realpath(process.env.AIF_M1_CHECK_ROOT);
const target = await realpath(process.env.AIF_M1_CHECK_TARGET);
const pathWithinRoot = relative(root, target);
if (!pathWithinRoot || pathWithinRoot === ".." || pathWithinRoot.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`) || isAbsolute(pathWithinRoot)) {
  throw new Error("validation target must be a file inside the configured check root");
}
const targetBytes = await readFile(target);
const check = spawnSync(process.execPath, ["--check", "--input-type=module"], {
  cwd: root,
  input: targetBytes,
  encoding: "utf8",
  timeout: 30_000,
  maxBuffer: 64 * 1024,
});
const passed = check.status === 0 && !check.error;
const evidence = {
  schemaVersion: 1,
  issueId,
  runId: process.env.PAPERCLIP_RUN_ID,
  agentId: identity.id,
  check: "node --check --input-type=module",
  target: pathWithinRoot.replaceAll("\\", "/"),
  targetSha256: createHash("sha256").update(targetBytes).digest("hex"),
  exitCode: check.status,
  errorCode: check.error?.code || null,
  output: (check.stderr || "").slice(0, 2000),
  verdict: passed ? "passed" : "failed",
};
const bytes = Buffer.from(`${JSON.stringify(evidence, null, 2)}\n`);
const artifactDir = process.env.AIF_M1_ARTIFACT_DIR;
const artifactPath = join(artifactDir, `${process.env.PAPERCLIP_RUN_ID}.json`);
await mkdir(artifactDir, { recursive: true });
try {
  await writeFile(artifactPath, bytes, { flag: "wx" });
} catch (error) {
  if (error.code !== "EEXIST" || !(await readFile(artifactPath)).equals(bytes)) throw error;
}
const digest = createHash("sha256").update(bytes).digest("hex");
const comment = `Deterministic validation ${evidence.verdict}: ${evidence.check} (${evidence.target}); evidence=file://${artifactPath} sha256=${digest}`;
const response = await fetch(`${process.env.PAPERCLIP_API_URL}/api/issues/${issueId}`, {
  method: "PATCH",
  headers: { ...headers, "x-paperclip-run-id": process.env.PAPERCLIP_RUN_ID },
  body: JSON.stringify({ status: passed ? "done" : "in_progress", comment }),
});
if (!response.ok) throw new Error(`Paperclip rejected validation decision: ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
