// Run only in an ephemeral --network none container, without live volumes/secrets.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { execute } from "/app/packages/adapters/opencode-local/src/server/execute.ts";

const root = await fs.mkdtemp(path.join(os.tmpdir(), "aif-opencode-workspace-"));
const workspace = path.join(root, "task-workspace");
await fs.mkdir(workspace);
const stderr = [];
let invocation;
try {
  const result = await execute({
    runId: "aif-model-free-workspace-probe",
    agent: { id: "probe", companyId: "probe", name: "Workspace probe", adapterType: "opencode_local", adapterConfig: {} },
    runtime: { sessionId: null, sessionParams: null, sessionDisplayId: null, taskKey: null },
    config: {
      cwd: "/app",
      command: "opencode",
      model: "aif-nonexistent-provider/no-inference",
      timeoutSec: 20,
      graceSec: 1,
      dangerouslySkipPermissions: false,
      paperclipRuntimeSkills: [],
      env: {
        HOME: root,
        XDG_CONFIG_HOME: path.join(root, "config"),
        XDG_DATA_HOME: path.join(root, "data"),
        XDG_CACHE_HOME: path.join(root, "cache"),
        PWD: "/app",
        OPENCODE_ALLOW_ALL_MODELS: "1",
        PAPERCLIP_OPENCODE_PRINT_LOGS: "1",
        OPENCODE_CONFIG_CONTENT: JSON.stringify({ permission: "deny", plugin: [] }),
      },
    },
    context: { paperclipWorkspace: { cwd: workspace, source: "project_primary" } },
    onLog: async (stream, chunk) => { if (stream === "stderr") stderr.push(chunk); },
    onMeta: async (meta) => { invocation = meta; },
  });
  assert.equal(result.timedOut, false);
  assert.match(stderr.join(""), /ProviderModelNotFoundError|Model not found/);
  const nativeSessions = stderr.join("").split("\n")
    .filter((line) => /message=created id=ses_/.test(line))
    .map((line) => ({
      id: line.match(/ id=(\S+)/)?.[1],
      directory: line.match(/ directory=(\S+)/)?.[1],
    }));
  assert.equal(nativeSessions.length, 1, "expected one real native session before model rejection");
  assert.equal(nativeSessions[0].directory, workspace, "native session must bind to the task, not inherited PWD");
  assert.equal(invocation.cwd, workspace);
  assert.equal(invocation.adapterType, "opencode_local");
  assert.equal(result.sessionParams.cwd, workspace);
  console.log(JSON.stringify({
    passed: true,
    opencodeVersion: execFileSync("opencode", ["--version"], { encoding: "utf8" }).trim(),
    runId: "aif-model-free-workspace-probe",
    inheritedPwd: "/app",
    invocationCwd: invocation.cwd,
    nativeSession: nativeSessions[0],
    adapterSessionCwd: result.sessionParams.cwd,
    modelInvocation: "intentionally rejected before inference; network disabled",
  }));
} finally {
  await fs.rm(root, { recursive: true, force: true });
}
