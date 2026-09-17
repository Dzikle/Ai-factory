import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { createInterface } from "node:readline";

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}

function reply(id, result) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, result })}\n`);
}

function fail(id, code, message) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } })}\n`);
}

async function callMcp(server, method, params, rpcId) {
  const response = await fetch(server.url, {
    method: "POST",
    headers: {
      authorization: `Bearer ${server.token}`,
      "content-type": "application/json"
    },
    body: JSON.stringify({ jsonrpc: "2.0", id: rpcId, method, ...(params ? { params } : {}) })
  });
  const payload = await response.json().catch(() => ({}));
  return {
    status: response.status,
    toolNames: payload?.result?.tools?.map((tool) => tool.name) ?? null,
    reasonCode: payload?.error?.data?.reasonCode ?? null,
    isError: payload?.result?.isError ?? null
  };
}

async function probeMcp(servers) {
  const results = [];
  for (const server of servers ?? []) {
    const initialized = await callMcp(server, "initialize", {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "aif-m0-context-enricher", version: "0.0.0" }
    }, 1);
    const listed = await callMcp(server, "tools/list", undefined, 2);
    const allowedTool = listed.toolNames?.find((name) => name.toLowerCase().endsWith(":searchindextool")) ?? null;
    const deniedTool = allowedTool
      ? `${allowedTool.slice(0, allowedTool.lastIndexOf(":") + 1)}msearchtool`
      : "definitely_not_granted";
    const allowed = allowedTool
      ? await callMcp(server, "tools/call", {
          name: allowedTool,
          arguments: {
            index: "aif_docs_current",
            query_dsl: {
              query: {
                bool: {
                  filter: [
                    { term: { project_id: "ai-factory" } },
                    { term: { status: "current" } }
                  ]
                }
              }
            },
            size: 2
          }
        }, 3)
      : null;
    const denied = await callMcp(server, "tools/call", {
      name: deniedTool,
      arguments: {}
    }, 4);
    results.push({
      name: server.name,
      connectionId: server.connectionId,
      initialized,
      listed,
      allowedTool,
      deniedTool,
      allowed,
      denied
    });
  }
  return results;
}

async function enrich(params) {
  const assignedMcp = await probeMcp(params.runtimeMcpServers);
  const contextPackage = stable({
    schemaVersion: 0,
    kind: "admission-placeholder",
    runId: params.runId,
    agentId: params.agentId,
    issueId: params.issueId,
    adapterType: params.adapterType,
    sources: [{ authority: "fixture", revision: "milestone0b" }],
    budget: { maxTokens: 64, suppliedTokens: 9 },
    content: "placeholder bounded context",
    assignedMcp
  });
  const bytes = JSON.stringify(contextPackage);
  const digest = createHash("sha256").update(bytes).digest("hex");
  const artifactPath = `/paperclip/milestone0-context/${params.runId}.json`;
  await mkdir("/paperclip/milestone0-context", { recursive: true });
  await writeFile(artifactPath, bytes, { flag: "wx" });
  return {
    promptMarkdown: `Use bounded context artifact file://${artifactPath} (sha256:${digest}).`,
    artifact: {
      ref: `file://${artifactPath}`,
      sha256: digest,
      mediaType: "application/json",
      byteSize: Buffer.byteLength(bytes)
    },
    metadata: {
      fixture: "placeholder-v1",
      governedMcpServerCount: assignedMcp.length
    }
  };
}

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", async (line) => {
  let request;
  try {
    request = JSON.parse(line);
  } catch {
    fail(null, -32700, "Parse error");
    return;
  }
  if (!("id" in request)) return;
  try {
    if (request.method === "initialize") {
      reply(request.id, { ok: true, supportedMethods: ["health", "shutdown", "enrichRunContext"] });
    } else if (request.method === "health") {
      reply(request.id, { status: "ok", message: "admission fixture ready" });
    } else if (request.method === "shutdown") {
      reply(request.id, { ok: true });
      setImmediate(() => process.exit(0));
    } else if (request.method === "enrichRunContext") {
      reply(request.id, await enrich(request.params));
    } else {
      fail(request.id, -32601, `Unknown method: ${request.method}`);
    }
  } catch (error) {
    fail(request.id, -32000, error instanceof Error ? error.message : String(error));
  }
});
