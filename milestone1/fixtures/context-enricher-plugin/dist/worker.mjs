import { createInterface } from "node:readline";
import { createHash } from "node:crypto";

import { publishArtifact } from "./artifact.mjs";
import { buildContext, parseSearchResult } from "./context.mjs";

const DOCUMENT_PATH = "docs/implementation/IMPLEMENTATION_KICKOFF.md";
const ARTIFACT_DIR = "/paperclip/milestone1-context";

async function callMcp(server, method, params, id) {
  const response = await fetch(server.url, {
    method: "POST",
    headers: { authorization: `Bearer ${server.token}`, "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, ...(params ? { params } : {}) }),
  });
  const body = await response.text();
  if (!response.ok || body.length > 300_000) throw new Error("governed MCP call failed");
  let payload;
  try { payload = JSON.parse(body); } catch { throw new Error("invalid governed MCP response"); }
  if (payload.error) throw new Error("governed MCP rejected request");
  return payload.result;
}

async function enrich(params) {
  if (!params?.runId || !params?.workspace?.cwd) {
    throw new Error("run workspace is missing");
  }
  // A deterministic process validation stage needs no external lookup.
  if (params.adapterType === "process" && params.runtimeMcpServers?.length === 0) {
    const bytes = Buffer.from(JSON.stringify({ schemaVersion: 1, kind: "no-context", runId: params.runId }) + "\n");
    const digest = createHash("sha256").update(bytes).digest("hex");
    const ref = await publishArtifact(ARTIFACT_DIR, params.runId, bytes);
    return { artifact: { ref, sha256: digest, mediaType: "application/json", byteSize: bytes.length }, metadata: { reason: "deterministic-stage" } };
  }
  if (params.runtimeMcpServers?.length !== 1) {
    throw new Error("run workspace or governed search capability is missing");
  }
  const server = params.runtimeMcpServers[0];
  await callMcp(server, "initialize", {
    protocolVersion: "2025-03-26", capabilities: {},
    clientInfo: { name: "aif-git-context", version: "0.1.0" },
  }, 1);
  const listed = await callMcp(server, "tools/list", undefined, 2);
  const searchTools = (listed?.tools ?? []).filter((tool) => tool.name?.toLowerCase().endsWith(":searchindextool"));
  if (searchTools.length !== 1) throw new Error("exactly one governed search tool is required");
  const result = await callMcp(server, "tools/call", {
    name: searchTools[0].name,
    arguments: {
      index: "ai_factory_docs",
      size: 2,
      query_dsl: { query: { bool: { filter: [
        { term: { project_id: "ai-factory" } },
        { term: { repository_id: "ai-factory" } },
        { term: { path: DOCUMENT_PATH } },
        { term: { status: "canonical" } },
        { term: { source_system: "git" } },
      ] } } },
    },
  }, 3);
  const hit = parseSearchResult(result);
  const context = await buildContext({
    cwd: params.workspace.cwd, hit, runId: params.runId, expectedPath: DOCUMENT_PATH,
  });
  const ref = await publishArtifact(ARTIFACT_DIR, params.runId, context.bytes);
  return {
    promptMarkdown: `Read the verified, bounded first-task context at ${ref} (SHA-256 ${context.sha256}) before work. Git in the assigned workspace remains authoritative.`,
    artifact: {
      ref, sha256: context.sha256, mediaType: "application/json", byteSize: context.bytes.length,
    },
    metadata: {
      sourcePath: DOCUMENT_PATH,
      sourceRevision: context.package.sources[0].sourceRevision,
      contextBytes: context.bytes.length,
      mcpConnectionId: server.connectionId,
    },
  };
}

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", async (line) => {
  let request;
  try { request = JSON.parse(line); } catch {
    process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } })}\n`);
    return;
  }
  if (!("id" in request)) return;
  try {
    let result;
    if (request.method === "initialize") result = { ok: true, supportedMethods: ["health", "shutdown", "enrichRunContext"] };
    else if (request.method === "health") result = { status: "ok" };
    else if (request.method === "shutdown") result = { ok: true };
    else if (request.method === "enrichRunContext") result = await enrich(request.params);
    else throw new Error(`Unknown method: ${request.method}`);
    process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: request.id, result })}\n`);
    if (request.method === "shutdown") setImmediate(() => process.exit(0));
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: request.id, error: { code: -32000, message: error instanceof Error ? error.message : String(error) } })}\n`);
  }
});
