import path from "node:path";

const worktreeRoot = "/paperclip/m1-first-task-worktrees";

export async function resolveRunIssueId({ api, token, runId, configuredIssueId, fetchImpl = fetch }) {
  const response = await fetchImpl(`${api}/api/heartbeat-runs/${runId}/issues`, {
    headers: { authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Paperclip run issue lookup failed: ${response.status}`);
  const issues = await response.json();
  if (!Array.isArray(issues) || issues.length !== 1 || typeof issues[0]?.issueId !== "string") {
    throw new Error("validator run must have exactly one issue");
  }
  const issueId = issues[0].issueId;
  if (configuredIssueId && configuredIssueId !== issueId) throw new Error("run/task identity mismatch");
  return issueId;
}

export async function resolveRunWorkspace({ api, token, runId, issueId, agentId, fetchImpl = fetch }) {
  const response = await fetchImpl(`${api}/api/heartbeat-runs/${runId}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Paperclip run snapshot lookup failed: ${response.status}`);
  const run = await response.json();
  const cwd = run?.contextSnapshot?.paperclipWorkspace?.cwd;
  const relative = typeof cwd === "string" ? path.posix.relative(worktreeRoot, cwd) : "";
  if (run?.id !== runId || run?.agentId !== agentId ||
      run?.contextSnapshot?.issueId !== issueId || typeof cwd !== "string" ||
      !path.posix.isAbsolute(cwd) || !relative || relative.startsWith("..") ||
      path.posix.isAbsolute(relative)) {
    throw new Error("run snapshot identity or workspace mismatch");
  }
  return cwd;
}
