import assert from "node:assert/strict";
import { test } from "node:test";
import { resolveRunIssueId, resolveRunWorkspace } from "./git-doc-validator-identity.mjs";

const issue = { issueId: "issue-1", identifier: "AIF-42" };
const input = { api: "http://paperclip.test", token: "run-token", runId: "run-1" };

test("resolves the sole issue through the run-scoped API", async () => {
  const id = await resolveRunIssueId({ ...input, fetchImpl: async (url, options) => {
    assert.equal(url, "http://paperclip.test/api/heartbeat-runs/run-1/issues");
    assert.equal(options.headers.authorization, "Bearer run-token");
    return { ok: true, json: async () => [issue] };
  } });
  assert.equal(id, "issue-1");
});

test("rejects an ambiguous or missing run issue", async () => {
  for (const issues of [[], [issue, { issueId: "issue-2" }]]) {
    await assert.rejects(resolveRunIssueId({ ...input, fetchImpl: async () => ({
      ok: true, json: async () => issues,
    }) }), /exactly one issue/);
  }
});

test("rejects an optional task identity mismatch and API denial", async () => {
  await assert.rejects(resolveRunIssueId({ ...input, configuredIssueId: "other",
    fetchImpl: async () => ({ ok: true, json: async () => [issue] }),
  }), /identity mismatch/);
  await assert.rejects(resolveRunIssueId({ ...input,
    fetchImpl: async () => ({ ok: false, status: 403 }),
  }), /403/);
});

test("resolves only the Paperclip snapshot worktree for this run and issue", async () => {
  const cwd = "/paperclip/m1-first-task-worktrees/AIF-42-task";
  const actual = await resolveRunWorkspace({ ...input, issueId: "issue-1", agentId: "agent-1",
    fetchImpl: async (url, options) => {
      assert.equal(url, "http://paperclip.test/api/heartbeat-runs/run-1");
      assert.equal(options.headers.authorization, "Bearer run-token");
      return { ok: true, json: async () => ({ id: "run-1", agentId: "agent-1",
        contextSnapshot: { issueId: "issue-1", paperclipWorkspace: { cwd } },
      }) };
    },
  });
  assert.equal(actual, cwd);
});

test("rejects unrelated or outside workspaces", async () => {
  for (const [issueId, cwd] of [
    ["other", "/paperclip/m1-first-task-worktrees/AIF-42-task"],
    ["issue-1", "/paperclip/m1-first-task-worktrees-evil/task"],
  ]) {
    await assert.rejects(resolveRunWorkspace({ ...input, issueId: "issue-1", agentId: "agent-1",
      fetchImpl: async () => ({ ok: true, json: async () => ({ id: "run-1", agentId: "agent-1",
        contextSnapshot: { issueId, paperclipWorkspace: { cwd } },
      }) }),
    }), /snapshot identity or workspace mismatch/);
  }
});
