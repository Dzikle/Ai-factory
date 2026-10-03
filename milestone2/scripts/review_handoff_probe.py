"""Real API/process-adapter correction-loop regression; no model or product edits.

Creates a disposable company and task. Only its four process agents are started.
No manual stage wakeups, reconciliation, approval, or task-state SQL writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from uuid import uuid4

from milestone0.scripts.paperclip_admission import Client


WORKER = r"""
import { resolveRunIssueId } from '/paperclip/git-doc-validator-identity.mjs';
const role = process.argv[1];
const { PAPERCLIP_API_URL: api, PAPERCLIP_API_KEY: token,
        PAPERCLIP_RUN_ID: runId, PAPERCLIP_TASK_ID: configuredIssueId } = process.env;
if (!api || !token || !runId) throw Error('missing run identity');
const issueId = await resolveRunIssueId({ api, token, runId, configuredIssueId });
const headers = { authorization: `Bearer ${token}`, 'content-type': 'application/json',
                  'x-paperclip-run-id': runId };
const current = await fetch(`${api}/api/issues/${issueId}`, { headers });
if (!current.ok) throw Error(`issue lookup ${current.status}`);
const issue = await current.json();
const corrected = issue.title.endsWith(' [corrected]');
let patch;
if (role === 'developer') {
  const returning = issue.executionState?.status === 'changes_requested';
  patch = { status: 'done', comment: returning ? 'Corrected rejected candidate.' : 'Initial candidate ready.' };
  if (returning) patch.title = issue.title + ' [corrected]';
} else if (role === 'reviewer' && !corrected) {
  patch = { status: 'in_progress', comment: 'Regression: request one real correction round.' };
} else {
  patch = { status: 'done', comment: `Independent ${role} passed the current candidate.` };
}
const decision = await fetch(`${api}/api/issues/${issueId}`, {
  method: 'PATCH', headers, body: JSON.stringify(patch),
});
if (!decision.ok) throw Error(`decision rejected ${decision.status}`);
console.log(JSON.stringify({ role, runId, status: decision.status }));
"""


def run(state_path: Path, output: Path, timeout: int, existing_company_id: str | None = None) -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    client = Client(state["baseUrl"], state["boardApiKey"])

    def request(method: str, path: str, body=None):
        return client.request(method, path, body, expected=(200, 201, 202))[1]

    health = request("GET", "/api/health")
    if existing_company_id:
        company = request("GET", "/api/companies/" + existing_company_id)
        if not company["name"].startswith("Disposable review-handoff regression "):
            raise ValueError("Only this probe's disposable company may be reused")
        if request("GET", f"/api/companies/{existing_company_id}/agents"):
            raise ValueError("The reused company must have no agents")
    else:
        company = request("POST", "/api/companies", {
            "name": "Disposable review-handoff regression " + str(uuid4())[:8],
            "requireBoardApprovalForNewAgents": False,
        })
    company_id = company["id"]
    actors = {}
    result = {"schemaVersion": 1, "companyId": company_id,
              "revision": health.get("commit"), "manualStageWakeups": 0,
              "manualReconciliations": 0, "providerCalls": 0}
    try:
        for role in ("developer", "validator", "reviewer", "qa"):
            actor = request("POST", f"/api/companies/{company_id}/agents", {
                "name": "Regression " + role, "role": "engineer", "adapterType": "process",
                "adapterConfig": {"command": "node", "args": ["--input-type=module", "-e", WORKER, role],
                                  "timeoutSec": 30, "graceSec": 1},
                "runtimeConfig": {"heartbeat": {"enabled": True, "intervalSec": 0,
                                                  "wakeOnAssignment": True, "wakeOnDemand": True}},
            })
            actors[role] = actor["id"]
        stages = [{"id": str(uuid4()), "type": "review",
                   "participants": [{"type": "agent", "agentId": actors[role]}]}
                  for role in ("validator", "reviewer", "qa")]
        stages.append({"id": str(uuid4()), "type": "approval",
                       "participants": [{"type": "user", "userId": state["userId"]}]})
        issue = request("POST", f"/api/companies/{company_id}/issues", {
            "title": "Process correction-loop regression", "status": "todo",
            "assigneeAgentId": actors["developer"],
            "description": "Disposable process-adapter regression; no product files or provider calls.",
            "executionPolicy": {"stages": stages},
        })
        result.update(issueId=issue["id"], identifier=issue["identifier"], actors=actors)
        deadline = time.monotonic() + timeout
        settled_observations = 0
        runs = []
        while time.monotonic() < deadline:
            issue = request("GET", "/api/issues/" + issue["id"])
            execution = issue.get("executionState") or {}
            runs = request("GET", f"/api/companies/{company_id}/heartbeat-runs?limit=100")
            active = any(run["status"] in ("running", "queued", "scheduled_retry") for run in runs)
            terminal_observation = (execution.get("currentStageType") == "approval"
                                    or bool(issue.get("activeRecoveryAction"))) and not active
            settled_observations = settled_observations + 1 if terminal_observation else 0
            if settled_observations >= 3:
                break
            time.sleep(1)
        execution = issue.get("executionState") or {}
        # The list endpoint intentionally omits resultJson. Inspect each durable
        # run record instead of interpreting summary omission as a lost receipt.
        runs = [request("GET", "/api/heartbeat-runs/" + run["id"]) for run in runs]
        result.update(status=issue["status"], executionState=execution,
                      executionRunId=issue.get("executionRunId"), checkoutRunId=issue.get("checkoutRunId"),
                      activeRecoveryAction=issue.get("activeRecoveryAction"),
                      corrected=issue["title"].endswith(" [corrected]"))
        result["runs"] = [{key: run.get(key) for key in
                           ("id", "agentId", "status", "errorCode", "startedAt", "finishedAt")}
                          | {"issueHandoff": (run.get("resultJson") or {}).get("issueHandoff")}
                          for run in runs]
        handed_off = [run for run in result["runs"] if run["errorCode"] == "issue_reassigned"]
        result["handoffReceiptsPersisted"] = bool(handed_off) and all(
            (run["issueHandoff"] or {}).get("runId") == run["id"]
            and run["issueHandoff"].get("issueId") == issue["id"] for run in handed_off)
        chronological = sorted((run for run in result["runs"] if run["startedAt"]),
                               key=lambda run: run["startedAt"])
        result["noConcurrentTaskWriter"] = all(
            left["finishedAt"] and left["finishedAt"] <= right["startedAt"]
            for left, right in zip(chronological, chronological[1:]))
        result["passed"] = (result["corrected"] and execution.get("currentStageType") == "approval"
                            and len(execution.get("completedStageIds", [])) == 3
                            and not result["activeRecoveryAction"]
                            and result["handoffReceiptsPersisted"] and result["noConcurrentTaskWriter"]
                            and not result["executionRunId"] and not result["checkoutRunId"])
    finally:
        for actor_id in actors.values():
            request("POST", f"/api/agents/{actor_id}/pause", {})
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--company", help="Reuse the empty company from an uncertain setup response; never redispatch a task")
    args = parser.parse_args()
    result = run(args.state, args.output, args.timeout, args.company)
    print(json.dumps({k: result.get(k) for k in ("passed", "identifier", "revision", "status", "corrected")}))
    raise SystemExit(0 if result["passed"] else 1)
