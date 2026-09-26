import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { buildContext, parseSearchResult } from "./dist/context.mjs";
import { publishArtifact } from "./dist/artifact.mjs";

const section = "### 1.4 First runnable task\nImplement one command.\n\n## 5. Milestone 2\nLater.\n";

async function fixture(t) {
  const cwd = await mkdtemp(path.join(os.tmpdir(), "aif-m1-context-"));
  t.after(() => rm(cwd, { recursive: true, force: true }));
  execFileSync("git", ["init", "-q", cwd]);
  execFileSync("git", ["-C", cwd, "config", "user.email", "fixture@example.invalid"]);
  execFileSync("git", ["-C", cwd, "config", "user.name", "Fixture"]);
  await writeFile(path.join(cwd, "PLAN.md"), section);
  execFileSync("git", ["-C", cwd, "add", "PLAN.md"]);
  execFileSync("git", ["-C", cwd, "commit", "-qm", "fixture"]);
  const revision = execFileSync("git", ["-C", cwd, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  const blob = execFileSync("git", ["-C", cwd, "rev-parse", "HEAD:PLAN.md"], { encoding: "utf8" }).trim();
  const id = createHash("sha256").update("ai-factory\0ai-factory\0PLAN.md").digest("hex");
  const hit = {
    id, type: "git_document", project_id: "ai-factory", repository_id: "ai-factory",
    path: "PLAN.md", content: section, source_system: "git", source_id: "ai-factory:PLAN.md",
    source_revision: revision, source_version: blob, status: "canonical", canonical: true,
    authority: "canonical", content_sha256: createHash("sha256").update(section).digest("hex"),
  };
  return { cwd, hit };
}

test("verified current Git text becomes a bounded context artifact", async (t) => {
  const { cwd, hit } = await fixture(t);
  const result = await buildContext({ cwd, hit, runId: "run-1", maxArtifactBytes: 2048 });
  assert.equal(result.package.sources[0].sourceRevision, hit.source_revision);
  assert.equal(result.package.sources[0].contentSha256, hit.content_sha256);
  assert.match(result.package.content, /Implement one command/);
  assert.doesNotMatch(result.package.content, /Later\./);
  assert.equal(createHash("sha256").update(result.bytes).digest("hex"), result.sha256);
  assert.ok(result.bytes.length <= 2048);
});

test("stale or altered search hits fail closed", async (t) => {
  const { cwd, hit } = await fixture(t);
  await assert.rejects(buildContext({ cwd, hit: { ...hit, source_revision: "0".repeat(40) }, runId: "run-1" }), /revision/);
  await assert.rejects(buildContext({ cwd, hit: { ...hit, content: "tampered" }, runId: "run-1" }), /content/);
  await assert.rejects(buildContext({ cwd, hit: { ...hit, status: "superseded" }, runId: "run-1" }), /canonical/);
  await assert.rejects(buildContext({ cwd, hit: { ...hit, project_id: "other" }, runId: "run-1" }), /project/);
});

test("artifact budget overflow fails rather than silently truncating", async (t) => {
  const { cwd, hit } = await fixture(t);
  await assert.rejects(buildContext({ cwd, hit, runId: "run-1", maxArtifactBytes: 100 }), /budget/);
});

test("a later code commit does not stale an unchanged canonical document", async (t) => {
  const { cwd, hit } = await fixture(t);
  await writeFile(path.join(cwd, "code.py"), "print('new code')\n");
  execFileSync("git", ["-C", cwd, "add", "code.py"]);
  execFileSync("git", ["-C", cwd, "commit", "-qm", "code update"]);
  const current = execFileSync("git", ["-C", cwd, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  const result = await buildContext({ cwd, hit, runId: "review-run" });
  assert.equal(result.package.sources[0].sourceRevision, hit.source_revision);
  assert.equal(result.package.sources[0].verifiedAtRevision, current);
});

test("a redacted authority label is re-established from verified Git bytes", async (t) => {
  const { cwd, hit } = await fixture(t);
  const result = await buildContext({ cwd, hit: { ...hit, authority: "***REDACTED***" }, runId: "run-redacted" });
  assert.equal(result.package.sources[0].authority, "canonical");
});

test("official MCP search text must contain exactly one hit", async (t) => {
  const { hit } = await fixture(t);
  const payload = { hits: { total: { value: 1 }, hits: [{ _source: hit }] } };
  const response = { content: [{ type: "text", text: `Search results from ai_factory_docs (JSON format):\n${JSON.stringify(payload)}` }] };
  assert.deepEqual(parseSearchResult(response), hit);
  assert.throws(() => parseSearchResult({ content: [] }), /search result/);
  assert.throws(() => parseSearchResult({ isError: true, content: response.content }), /search failed/);
});

test("artifact publication is atomic and same-run retries are idempotent", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "aif-m1-artifact-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const bytes = Buffer.from("deterministic context\n");
  const ref = await publishArtifact(dir, "run-1", bytes);
  assert.equal(ref, await publishArtifact(dir, "run-1", bytes));
  assert.deepEqual(await readFile(path.join(dir, "run-1.json")), bytes);
  await assert.rejects(publishArtifact(dir, "run-1", Buffer.from("different")), /different artifact/);
});
