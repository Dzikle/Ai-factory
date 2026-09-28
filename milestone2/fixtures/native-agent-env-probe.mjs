// Run inside the deployed controller with its real environment. Never log values.
// This probes env inheritance, not filesystem/proc isolation or model inference.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execute as executeOpenCode } from "/app/packages/adapters/opencode-local/src/server/execute.ts";
import { execute as executeProcess } from "/app/server/src/adapters/process/execute.ts";

const forbidden = ["DATABASE_URL", "PGPASSWORD", "BETTER_AUTH_SECRET",
  "PAPERCLIP_SECRETS_MASTER_KEY", "PAPERCLIP_AGENT_JWT_SECRET", "PRIVATE_BACKEND_CREDENTIAL"];
assert.ok(process.env.DATABASE_URL, "probe must exercise the real controller environment");
const root = await fs.mkdtemp(path.join(os.tmpdir(), "aif-native-env-"));
const observations = [];
const stderr = [];
try {
  const runtimeTools = {
    mcpEndpoint: "http://run-scoped-fixture/mcp", bearerToken: "fixture-run-token",
    expiresAt: "2099-01-01T00:00:00Z", tools: ["SearchIndexTool"], guidance: "Fixture only",
    rest: { connectionsSearch: "http://run-scoped-fixture/search", connectionRequest: "http://run-scoped-fixture/request" },
  };
  const base = {
    runId: "aif-environment-containment-probe",
    runtime: { sessionId: null, sessionParams: null, sessionDisplayId: null, taskKey: null },
    runtimeTools, authToken: "fixture-agent-run-jwt", context: {},
    onLog: async (stream, chunk) => { if (stream === "stderr") stderr.push(chunk); },
    onSpawn: async ({ pid }) => {
      const entries = (await fs.readFile(`/proc/${pid}/environ`, "utf8")).split("\0");
      const env = Object.fromEntries(entries.filter(Boolean).map(entry => {
        const split = entry.indexOf("=");
        return [entry.slice(0, split), entry.slice(split + 1)];
      }));
      const exposedNames = forbidden.filter(key => env[key] !== undefined);
      assert.deepEqual(exposedNames, [], "child inherited forbidden controller variable names");
      assert.equal(env.PAPERCLIP_API_KEY, base.authToken);
      assert.equal(env.PAPERCLIP_RUN_ID, base.runId);
      assert.equal(env.PAPERCLIP_RUNTIME_TOOLS_TOKEN, runtimeTools.bearerToken);
      assert.equal(env.PAPERCLIP_RUNTIME_TOOLS_MCP_URL, runtimeTools.mcpEndpoint);
      observations.push({ forbiddenPresent: exposedNames, runIdentity: true, governedToken: true });
    },
  };
  const agent = type => ({ id: "env-probe", companyId: "env-probe", name: "Environment probe", adapterType: type, adapterConfig: {} });
  const processResult = await executeProcess({ ...base, agent: agent("process"), config: {
    command: process.execPath, args: ["-e", "process.stdout.write('fixture-completed')"],
    cwd: root, timeoutSec: 10, graceSec: 1, env: { HOME: root },
  } });
  assert.equal(processResult.exitCode, 0);
  assert.equal(processResult.resultJson.stdout, "fixture-completed");
  const nativeResult = await executeOpenCode({ ...base, agent: agent("opencode_local"), config: {
    command: "opencode", cwd: root, model: "aif-nonexistent-provider/no-inference",
    paperclipRuntimeSkills: [], dangerouslySkipPermissions: false, timeoutSec: 20, graceSec: 1,
    env: { HOME: root, XDG_CONFIG_HOME: path.join(root, "config"), XDG_DATA_HOME: path.join(root, "data"),
      XDG_CACHE_HOME: path.join(root, "cache"), OPENCODE_ALLOW_ALL_MODELS: "1",
      PAPERCLIP_OPENCODE_PRINT_LOGS: "1",
      OPENCODE_DISABLE_AUTOUPDATE: "true", OPENCODE_CONFIG_CONTENT: JSON.stringify({ permission: "deny", plugin: [] }) },
  } });
  assert.equal(nativeResult.timedOut, false);
  assert.ok(/Model not found|ProviderModelNotFoundError/.test(stderr.join("")), "expected deliberate model rejection before inference");
  assert.equal(observations.length, 2, "expected process and original native OpenCode children");
  console.log(JSON.stringify({ passed: true, observations, nativeAdapter: "opencode_local",
    inference: "intentionally rejected before inference", durableRun: false, scope: "environment inheritance only" }));
} finally {
  await fs.rm(root, { recursive: true, force: true });
}
