import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";

export const type = "aif_context_seam_poc";
export const label = "AI Factory Context Seam POC";
export const models = [{ id: "placeholder", label: "Placeholder" }];

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}

async function probeAssignedMcp(runtimeMcp, config) {
  const servers = runtimeMcp?.getServers?.() ?? [];
  const results = [];
  for (const server of servers) {
    let rpcId = 1;
    const call = async (method, params) => {
      const response = await fetch(server.url, {
        method: "POST",
        headers: {
          authorization: `Bearer ${server.token}`,
          "content-type": "application/json",
        },
        body: JSON.stringify({ jsonrpc: "2.0", id: rpcId++, method, ...(params ? { params } : {}) }),
      });
      const payload = await response.json().catch(() => ({}));
      return {
        status: response.status,
        toolNames: payload?.result?.tools?.map((tool) => tool.name) ?? null,
        reasonCode: payload?.error?.data?.reasonCode ?? null,
        isError: payload?.result?.isError ?? null,
      };
    };
    const initialized = await call("initialize", {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "aif-m0-context-seam", version: "0.0.0" },
    });
    const listed = await call("tools/list");
    const allowedTool = typeof config.allowedTool === "string" ? config.allowedTool : null;
    const deniedTool = typeof config.deniedTool === "string" ? config.deniedTool : null;
    const allowed = allowedTool
      ? await call("tools/call", {
          name: allowedTool,
          arguments: config.allowedToolArgs ?? {},
        })
      : null;
    const denied = deniedTool
      ? await call("tools/call", { name: deniedTool, arguments: {} })
      : null;
    results.push({
      name: server.name,
      connectionId: server.connectionId,
      initialized,
      listed,
      allowed,
      denied,
    });
  }
  return results;
}

export function createServerAdapter() {
  return {
    type,
    models,
    supportsLocalAgentJwt: true,
    runtimeToolDelivery: "invocation_context",
    async testEnvironment() {
      return {
        adapterType: type,
        status: "pass",
        testedAt: new Date().toISOString(),
        checks: [{ code: "admission_fixture_ready", level: "info", message: "Admission-only wrapper is ready" }],
      };
    },
    async execute(ctx) {
      const assignedMcp = await probeAssignedMcp(ctx.runtimeMcp, ctx.config);
      const contextPackage = {
        schemaVersion: 0,
        kind: "admission-placeholder",
        runId: ctx.runId,
        agentId: ctx.agent.id,
        taskId: ctx.context.taskId ?? ctx.context.issueId ?? null,
        sources: [{ authority: "fixture", revision: "milestone0" }],
        budget: { maxTokens: 64, suppliedTokens: 9 },
        content: "placeholder bounded context",
        assignedMcp,
      };
      const bytes = JSON.stringify(stable(contextPackage));
      const digest = createHash("sha256").update(bytes).digest("hex");
      const artifact = `/paperclip/milestone0-adapter-context/${ctx.runId}.json`;
      await mkdir("/paperclip/milestone0-adapter-context", { recursive: true });
      await writeFile(artifact, `${JSON.stringify({ ...contextPackage, digest }, null, 2)}\n`, { flag: "wx" });

      // Deliberately mutate only the invocation copy. The admission test checks
      // whether Paperclip's public adapter contract persists this into its
      // host-owned context_snapshot (it must not be assumed).
      ctx.context.aiFactoryContext = { artifact, digest, sources: contextPackage.sources, budget: contextPackage.budget };
      await ctx.onLog("stdout", `[aif-context-seam] artifact=${artifact} digest=${digest}\n`);
      ctx.onDispatch?.();
      await ctx.onLog("stdout", `[aif-context-seam] downstream-placeholder received=${contextPackage.content}\n`);
      return {
        exitCode: 0,
        signal: null,
        timedOut: false,
        summary: "Admission-only context wrapper completed",
        resultJson: {
          contextArtifact: artifact,
          contextDigest: digest,
          delegatedRuntime: "placeholder",
          assignedMcp,
        },
      };
    },
  };
}
