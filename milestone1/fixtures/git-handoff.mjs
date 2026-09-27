import { execFile as execFileCallback } from "node:child_process";
import { mkdtemp, realpath, rm } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);

export async function inspectGitHandoff({ cwd, expectedBranch, expectedHead = null }) {
  if (typeof expectedBranch !== "string" || !expectedBranch.trim()) {
    throw new Error("Paperclip task branch identity is required");
  }
  if (expectedHead !== null && !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(expectedHead)) {
    throw new Error("expected revision must be a full Git commit identity");
  }
  async function git(...args) {
    const { stdout } = await execFile("git", args, { cwd, encoding: "utf8", timeout: 10_000, maxBuffer: 256 * 1024 });
    return stdout.trim();
  }
  if (await realpath(await git("rev-parse", "--show-toplevel")) !== await realpath(cwd)) {
    throw new Error("assigned workspace is not the Git worktree root");
  }
  const branchName = await git("branch", "--show-current");
  if (branchName !== expectedBranch) throw new Error("Git branch differs from Paperclip task branch");
  if (await git("status", "--porcelain=v1", "--untracked-files=all")) {
    throw new Error("uncommitted work cannot be handed to review");
  }
  const gitHead = await git("rev-parse", "--verify", "HEAD^{commit}");
  if (expectedHead !== null && gitHead !== expectedHead) {
    throw new Error("Git revision changed during validation");
  }
  return {
    gitHead,
    gitTree: await git("rev-parse", `${gitHead}^{tree}`),
    branchName,
  };
}

export async function validateCommittedTask({ cwd, expectedBranch }, check) {
  const handoff = await inspectGitHandoff({ cwd, expectedBranch });
  const temporary = await mkdtemp(path.join(os.tmpdir(), "aif-validation-"));
  const snapshot = path.join(temporary, "source");
  const snapshotBranch = `validation-${randomUUID()}`;
  try {
    // A test input copy, not another operational worktree or source of truth.
    // No hardlinks: edits to the assigned checkout cannot alter this copy.
    await execFile("git", ["clone", "--no-hardlinks", "--no-checkout", "--", cwd, snapshot], {
      timeout: 30_000, maxBuffer: 256 * 1024,
    });
    await execFile("git", ["-c", `core.hooksPath=${path.join(temporary, "no-hooks")}`,
      "checkout", "-qb", snapshotBranch, handoff.gitHead], { cwd: snapshot, timeout: 10_000 });
    await inspectGitHandoff({ cwd: snapshot, expectedBranch: snapshotBranch, expectedHead: handoff.gitHead });
    const result = await check(snapshot);
    await inspectGitHandoff({ cwd: snapshot, expectedBranch: snapshotBranch, expectedHead: handoff.gitHead });
    await inspectGitHandoff({ cwd, expectedBranch, expectedHead: handoff.gitHead });
    return { handoff, result };
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
}
