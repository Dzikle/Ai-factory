import { execFile as execFileCallback } from "node:child_process";
import { createHash } from "node:crypto";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

async function git(cwd, ...args) {
  const { stdout } = await execFile("git", ["-C", cwd, ...args], { maxBuffer: 1024 * 1024 });
  return stdout;
}

export function parseSearchResult(result) {
  if (result?.isError) throw new Error("governed search failed");
  if (!Array.isArray(result?.content) || result.content.length !== 1 || result.content[0]?.type !== "text") {
    throw new Error("invalid search result envelope");
  }
  const text = result.content[0].text;
  const start = typeof text === "string" ? text.indexOf("\n{") : -1;
  if (start < 0 || text.length > 256_000) throw new Error("invalid search result text");
  let parsed;
  try {
    parsed = JSON.parse(text.slice(start + 1));
  } catch {
    throw new Error("invalid search result JSON");
  }
  if (parsed?.hits?.total?.value !== 1 || parsed.hits.hits?.length !== 1) {
    throw new Error("search result must contain exactly one document");
  }
  const hit = parsed.hits.hits[0]?._source;
  if (!hit || typeof hit !== "object") throw new Error("invalid search result source");
  return hit;
}

export async function buildContext({
  cwd, hit, runId, expectedProjectId = "ai-factory", expectedRepositoryId = "ai-factory",
  expectedPath = hit?.path, maxArtifactBytes = 8192,
}) {
  if (!cwd || !runId || !expectedPath || !/^[\w./-]+$/.test(expectedPath) || expectedPath.includes("..")) {
    throw new Error("invalid context request");
  }
  if (hit.project_id !== expectedProjectId || hit.repository_id !== expectedRepositoryId) {
    throw new Error("search hit belongs to another project or repository");
  }
  if (hit.path !== expectedPath || hit.type !== "git_document" || hit.source_system !== "git") {
    throw new Error("search hit is not the expected Git document");
  }
  // The governed MCP gateway may redact fields whose names contain "auth".
  // Canonical authority is re-established below from the current Git blob.
  if (hit.status !== "canonical" || hit.canonical !== true) {
    throw new Error("search hit is not canonical");
  }
  if (hit.id !== sha256(Buffer.from(`${expectedProjectId}\0${expectedRepositoryId}\0${expectedPath}`))) {
    throw new Error("search hit has invalid identity");
  }
  const revision = (await git(cwd, "rev-parse", "HEAD")).toString("utf8").trim();
  try {
    await git(cwd, "merge-base", "--is-ancestor", hit.source_revision, revision);
  } catch {
    throw new Error("search hit revision is not an ancestor of the assigned Git workspace");
  }
  const blob = (await git(cwd, "rev-parse", `HEAD:${expectedPath}`)).toString("utf8").trim();
  if (hit.source_version !== blob) throw new Error("stale Git blob in search hit");
  const original = await git(cwd, "show", `HEAD:${expectedPath}`);
  if (sha256(original) !== hit.content_sha256 || original.toString("utf8") !== hit.content) {
    throw new Error("search content does not match canonical Git bytes");
  }
  const heading = "### 1.4 First runnable task";
  const start = hit.content.indexOf(heading);
  if (start < 0) throw new Error("required first-task section is missing");
  const next = hit.content.indexOf("\n## ", start + heading.length);
  const content = hit.content.slice(start, next < 0 ? undefined : next).trim() + "\n";
  const contextPackage = {
    schemaVersion: 1,
    kind: "git-doc-context",
    runId,
    sources: [{
      projectId: hit.project_id,
      repositoryId: hit.repository_id,
      path: hit.path,
      sourceRevision: hit.source_revision,
      verifiedAtRevision: revision,
      sourceVersion: blob,
      contentSha256: hit.content_sha256,
      authority: "canonical",
    }],
    content,
  };
  const bytes = Buffer.from(JSON.stringify(contextPackage) + "\n", "utf8");
  if (bytes.length > maxArtifactBytes) throw new Error("context artifact exceeds byte budget");
  return { package: contextPackage, bytes, sha256: sha256(bytes) };
}

export function formatContextPrompt(context, ref) {
  const prompt = `Verified bounded task context (artifact ${ref}; SHA-256 ${context.sha256}). Git in the assigned workspace remains authoritative.\n\n${context.package.content}`;
  if (Buffer.byteLength(prompt, "utf8") > 10_000) throw new Error("context prompt exceeds byte budget");
  return prompt;
}
