// Test-only native process adapter for proving Paperclip's stage routing.
import process from "node:process";

for (const name of ["PAPERCLIP_AGENT_ID", "PAPERCLIP_RUN_ID", "PAPERCLIP_API_KEY", "PAPERCLIP_API_URL", "AIF_M1_STAGE_LABEL"]) {
  if (!process.env[name]) throw new Error(`missing ${name}`);
}
const headers = {
  authorization: `Bearer ${process.env.PAPERCLIP_API_KEY}`,
  "content-type": "application/json",
};
const identityResponse = await fetch(`${process.env.PAPERCLIP_API_URL}/api/agents/me`, { headers });
if (!identityResponse.ok || (await identityResponse.json()).id !== process.env.PAPERCLIP_AGENT_ID) {
  throw new Error("run JWT identity mismatch");
}
let issueId = process.env.PAPERCLIP_TASK_ID || process.env.PAPERCLIP_ISSUE_ID;
if (!issueId) {
  const runResponse = await fetch(`${process.env.PAPERCLIP_API_URL}/api/heartbeat-runs/${process.env.PAPERCLIP_RUN_ID}`, { headers });
  if (!runResponse.ok) throw new Error(`own run lookup failed: ${runResponse.status}`);
  const run = await runResponse.json();
  issueId = run.contextSnapshot?.issueId || run.contextSnapshot?.taskId;
}
if (!issueId) {
  console.log(JSON.stringify({ runId: process.env.PAPERCLIP_RUN_ID, skipped: "no_task" }));
  process.exit(0);
}
const response = await fetch(`${process.env.PAPERCLIP_API_URL}/api/issues/${issueId}`, {
  method: "PATCH",
  headers: { ...headers, "x-paperclip-run-id": process.env.PAPERCLIP_RUN_ID },
  body: JSON.stringify({
    status: "done",
    comment: `${process.env.AIF_M1_STAGE_LABEL} fixture decision from Paperclip run ${process.env.PAPERCLIP_RUN_ID}`,
  }),
});
if (!response.ok) throw new Error(`Paperclip rejected stage decision: ${response.status}`);
console.log(JSON.stringify({ issueId, actor: process.env.PAPERCLIP_AGENT_ID, runId: process.env.PAPERCLIP_RUN_ID, accepted: true }));
