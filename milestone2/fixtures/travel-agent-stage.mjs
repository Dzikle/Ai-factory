import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolveRunIssueId, resolveRunWorkspace } from "/paperclip/git-doc-validator-identity.mjs";
import { validateCommittedTask } from "/paperclip/git-handoff.mjs";
import { assertTravelWorkspace } from "/paperclip/travel-agent-workspace.mjs";

const mode = process.argv[2];
const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token, PAPERCLIP_RUN_ID: runId,
  PAPERCLIP_AGENT_ID: agentId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId || !agentId || !["tests", "qa"].includes(mode)) {
  throw new Error("stage identity missing");
}
if (Number(process.versions.node.split(".")[0]) !== 24) throw new Error("Node 24 controller required");

const headers = { authorization: `Bearer ${token}`, "content-type": "application/json" };
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const { cwd, branchName } = await resolveRunWorkspace({ api, token, runId, issueId, agentId });
await assertTravelWorkspace(cwd);
async function assertStage() {
  const response = await fetch(`${api}/api/issues/${issueId}`, { headers });
  if (!response.ok) throw new Error("issue lookup failed");
  const issue = await response.json();
  if (issue.projectId !== "ccf950be-d486-4bbf-9817-72459fd9b315"
      || issue.status !== "in_review" || issue.executionState?.currentParticipant?.agentId !== agentId) {
    throw new Error("stage ownership mismatch");
  }
}

await assertStage();
const artifactDir = `/paperclip/travel-agent-results/${runId}`;
await mkdir(artifactDir, { recursive: true });
const upstreamMain = "fc5d95c2ce0e3606b26dc1d0f954143389cdcbdc";
const commands = mode === "tests"
  ? [["test"], ["typecheck"], ["migrations:check"]]
  : [["exec", "vitest", "run", "tests/agent-working.test.ts", "tests/agent-tools.test.ts",
      "tests/agent-conversation.test.ts", "tests/conversation.test.ts", "tests/booking.test.ts",
      "tests/search.test.ts"]];

const { handoff, result } = await validateCommittedTask({ cwd, expectedBranch: branchName }, async (snapshot) => {
  execFileSync("git", ["merge-base", "--is-ancestor", upstreamMain, "HEAD"], {
    cwd: snapshot, timeout: 10_000, maxBuffer: 256 * 1024,
  });
  const packageJson = JSON.parse(await readFile(`${snapshot}/package.json`, "utf8"));
  if (packageJson.packageManager !== "pnpm@9.15.5") throw new Error("unexpected packageManager");

  // This allowlist intentionally excludes every Paperclip, provider, registry and owner credential.
  // Synthetic and opt-in-live switches are disabled by being absent from the child environment.
  const env = { PATH: process.env.PATH, HOME: "/tmp", COREPACK_ENABLE_DOWNLOAD_PROMPT: "0", CI: "1" };
  const records = [];
  function run(args, timeout) {
    const startedAt = Date.now();
    const child = spawnSync("pnpm", args, {
      cwd: snapshot, env, encoding: "utf8", timeout, maxBuffer: 1024 * 1024,
    });
    const record = {
      command: ["pnpm", ...args], exitCode: child.status,
      errorCode: child.error?.code ?? null, signal: child.signal ?? null,
      durationMs: Date.now() - startedAt,
      output: `${child.stdout ?? ""}\n${child.stderr ?? ""}`.slice(-12_000),
    };
    records.push(record);
    return record.exitCode === 0 && !record.errorCode;
  }

  let passed = run(["install", "--frozen-lockfile", "--ignore-scripts"], 120_000);
  const validationStartedAt = Date.now();
  for (const args of commands) {
    if (!passed) break;
    const remaining = 600_000 - (Date.now() - validationStartedAt);
    if (remaining <= 0) {
      records.push({ command: ["pnpm", ...args], exitCode: null, errorCode: "AIF_TOTAL_TIMEOUT",
        signal: null, durationMs: 0, output: "validation budget exhausted before command start" });
      passed = false;
      break;
    }
    passed = run(args, remaining);
  }
  execFileSync("git", ["diff", "--check"], { cwd: snapshot, timeout: 10_000, maxBuffer: 256 * 1024 });
  return { passed, upstreamMain, packageManager: packageJson.packageManager,
    childEnvironmentKeys: Object.keys(env).sort(), commands: records };
});

const evidence = { schemaVersion: 1, issueId, runId, agentId, mode, ...handoff,
  validationSource: "credential-free isolated committed copy", ...result,
  verdict: result.passed ? "passed" : "failed" };
const bytes = Buffer.from(JSON.stringify(evidence) + "\n");
const artifactPath = `${artifactDir}/evidence.json`;
await writeFile(artifactPath, bytes, { flag: "wx" });
const digest = createHash("sha256").update(bytes).digest("hex");
const output = result.commands.map((record) => record.output).join("\n").slice(-2_000);

await assertStage();
const response = await fetch(`${api}/api/issues/${issueId}`, {
  method: "PATCH", headers: { ...headers, "x-paperclip-run-id": runId },
  body: JSON.stringify({ status: result.passed ? "done" : "in_progress",
    comment: `Independent travel-agent ${mode} ${evidence.verdict}; gitHead=${handoff.gitHead} gitTree=${handoff.gitTree}; evidence=file://${artifactPath} sha256=${digest}; credential-free isolated committed copy; no production, Docker, migrations, or live provider calls. ${output}` }),
});
if (!response.ok) throw new Error(`stage decision rejected ${response.status}`);
console.log(JSON.stringify({ verdict: evidence.verdict, artifactPath, sha256: digest }));
