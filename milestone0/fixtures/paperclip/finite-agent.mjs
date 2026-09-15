import { appendFile, mkdir, writeFile } from "node:fs/promises";
import process from "node:process";

const required = [
  "PAPERCLIP_AGENT_ID",
  "PAPERCLIP_COMPANY_ID",
  "PAPERCLIP_RUN_ID",
  "PAPERCLIP_API_KEY",
  "PAPERCLIP_API_URL",
];
for (const name of required) {
  if (!process.env[name]) throw new Error(`missing ${name}`);
}

const headers = { authorization: `Bearer ${process.env.PAPERCLIP_API_KEY}` };
const identityResponse = await fetch(`${process.env.PAPERCLIP_API_URL}/api/agents/me`, { headers });
if (!identityResponse.ok) throw new Error(`identity lookup failed: ${identityResponse.status}`);
const identity = await identityResponse.json();
if (identity.id !== process.env.PAPERCLIP_AGENT_ID) throw new Error("run JWT identity mismatch");

async function statusOnly(path, init = {}) {
  const response = await fetch(`${process.env.PAPERCLIP_API_URL}${path}`, {
    ...init,
    headers: { ...headers, ...(init.headers || {}) },
  });
  await response.body?.cancel();
  return response.status;
}

const authorizationChecks = {
  ownIdentity: identityResponse.status,
  assignedIssue: process.env.PAPERCLIP_TASK_ID
    ? await statusOnly(`/api/issues/${process.env.PAPERCLIP_TASK_ID}`)
    : null,
  createCompany: await statusOnly("/api/companies", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: "forbidden-agent-created-company" }),
  }),
  runtimeToolsAdvertised: (process.env.PAPERCLIP_RUNTIME_TOOLS_AVAILABLE || "")
    .split(",")
    .filter(Boolean),
};

if (process.env.PAPERCLIP_RUNTIME_TOOLS_MCP_URL && process.env.PAPERCLIP_RUNTIME_TOOLS_TOKEN) {
  let rpcId = 1;
  const gatewayCall = async (method, params) => {
    const response = await fetch(process.env.PAPERCLIP_RUNTIME_TOOLS_MCP_URL, {
      method: "POST",
      headers: {
        authorization: `Bearer ${process.env.PAPERCLIP_RUNTIME_TOOLS_TOKEN}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: rpcId++, method, ...(params ? { params } : {}) }),
    });
    const payload = await response.json().catch(() => ({}));
    return {
      status: response.status,
      toolNames: payload?.result?.tools?.map((tool) => tool.name) || undefined,
      reasonCode: payload?.error?.data?.reasonCode || null,
      isError: payload?.result?.isError ?? null,
    };
  };
  authorizationChecks.gatewayList = await gatewayCall("tools/list");
  if (process.env.AIF_M0_ALLOWED_TOOL) {
    authorizationChecks.gatewayAllowed = await gatewayCall("tools/call", {
      name: process.env.AIF_M0_ALLOWED_TOOL,
      arguments: JSON.parse(process.env.AIF_M0_ALLOWED_TOOL_ARGS || "{}"),
    });
  }
  authorizationChecks.gatewayDenied = await gatewayCall("tools/call", {
    name: process.env.AIF_M0_DENIED_TOOL || "definitely_not_granted",
    arguments: {},
  });
}

const outputDir = process.env.AIF_M0_OUTPUT_DIR || "/paperclip/milestone0-runs";
await mkdir(outputDir, { recursive: true });
const record = {
  runId: process.env.PAPERCLIP_RUN_ID,
  agentId: identity.id,
  agentName: identity.name,
  companyId: identity.companyId,
  taskId: process.env.PAPERCLIP_TASK_ID || null,
  wakeReason: process.env.PAPERCLIP_WAKE_REASON || null,
  runtimeBinding: process.env.AIF_M0_RUNTIME_BINDING || "fixture-a",
  authorizationChecks,
  at: new Date().toISOString(),
};
await writeFile(`${outputDir}/${record.runId}.json`, `${JSON.stringify(record, null, 2)}\n`, { flag: "wx" });
await appendFile(`${outputDir}/effects.ndjson`, `${JSON.stringify(record)}\n`);

const sleepMs = Number(process.env.AIF_M0_SLEEP_MS || "0");
if (sleepMs > 0) await new Promise((resolve) => setTimeout(resolve, sleepMs));
console.log(JSON.stringify({ ok: true, ...record }));
