import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { inspectGitHandoff } from "./git-handoff.mjs";

function git(cwd, ...args) {
  return execFileSync("git", args, { cwd, encoding: "utf8" }).trim();
}

async function fixture(t) {
  const cwd = await mkdtemp(path.join(os.tmpdir(), "aif-git-handoff-"));
  t.after(() => rm(cwd, { recursive: true, force: true }));
  git(cwd, "init", "-q", "-b", "AIF-45-task");
  git(cwd, "config", "user.name", "Handoff test");
  git(cwd, "config", "user.email", "handoff@example.invalid");
  git(cwd, "config", "core.autocrlf", "false");
  await writeFile(path.join(cwd, "code.txt"), "committed\n");
  git(cwd, "add", "code.txt");
  git(cwd, "commit", "-qm", "Task change");
  return { cwd, expectedBranch: "AIF-45-task", head: git(cwd, "rev-parse", "HEAD") };
}

test("a clean committed task produces a reproducible commit/tree identity", async (t) => {
  const { cwd, expectedBranch, head } = await fixture(t);
  const result = await inspectGitHandoff({ cwd, expectedBranch });
  assert.equal(result.gitHead, head);
  assert.equal(result.gitTree, git(cwd, "rev-parse", "HEAD^{tree}"));
  assert.equal(result.branchName, expectedBranch);
  assert.deepEqual(await inspectGitHandoff({ cwd, expectedBranch, expectedHead: head }), result);
});

for (const state of ["unstaged", "staged", "untracked"]) {
  test(`rejects ${state} work instead of attributing tested bytes to HEAD`, async (t) => {
    const { cwd, expectedBranch } = await fixture(t);
    const file = state === "untracked" ? "new.txt" : "code.txt";
    await writeFile(path.join(cwd, file), "not committed\n");
    if (state === "staged") git(cwd, "add", file);
    await assert.rejects(inspectGitHandoff({ cwd, expectedBranch }), /uncommitted/);
  });
}

test("rejects a different branch even if its commit is identical", async (t) => {
  const { cwd, expectedBranch } = await fixture(t);
  git(cwd, "checkout", "-qb", "wrong-task");
  await assert.rejects(inspectGitHandoff({ cwd, expectedBranch }), /branch/);
});

test("rejects detached HEAD and missing Paperclip branch identity", async (t) => {
  const { cwd, expectedBranch, head } = await fixture(t);
  await assert.rejects(inspectGitHandoff({ cwd }), /branch/);
  git(cwd, "checkout", "--detach", "-q", head);
  await assert.rejects(inspectGitHandoff({ cwd, expectedBranch }), /branch/);
});

test("rejects a commit changed during validation even when the tree is clean", async (t) => {
  const { cwd, expectedBranch, head } = await fixture(t);
  await writeFile(path.join(cwd, "code.txt"), "new commit\n");
  git(cwd, "commit", "-qam", "Concurrent change");
  await assert.rejects(inspectGitHandoff({ cwd, expectedBranch, expectedHead: head }), /revision/);
});

test("rejects abbreviated or option-like expected revisions", async (t) => {
  const { cwd, expectedBranch, head } = await fixture(t);
  for (const expectedHead of [head.slice(0, 7), "--help", "HEAD"]) {
    await assert.rejects(inspectGitHandoff({ cwd, expectedBranch, expectedHead }), /revision/);
  }
});

test("does not accept a subdirectory as the assigned worktree root", async (t) => {
  const { cwd, expectedBranch } = await fixture(t);
  const { mkdir } = await import("node:fs/promises");
  const nested = path.join(cwd, "nested");
  await mkdir(nested);
  await assert.rejects(inspectGitHandoff({ cwd: nested, expectedBranch }), /root/);
});
