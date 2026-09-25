#!/usr/bin/env python3
"""Disposable live proof of native Paperclip issue execution stages.

Uses the admitted local Paperclip fixture. This is not a workflow runner: every
stage transition and decision remains authoritative in Paperclip.
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
import time
from uuid import uuid4

from milestone0.scripts.paperclip_admission import Client, ApiError, create_agent
from milestone1.paperclip_policy import engineering_execution_policy


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = Path(os.environ.get(
    "AIF_M1_PAPERCLIP_STATE_PATH",
    ROOT / ".milestone0" / "fork-readmission-20260923" / "paperclip-state-readmission-20260925.json",
))
RESULT_PATH = ROOT / ".milestone0" / (
    "milestone1-policy-no-qa-probe.json" if os.environ.get("AIF_M1_INCLUDE_QA") == "0"
    else "milestone1-policy-probe.json"
)


def issue(client: Client, issue_id: str) -> dict:
    _, value = client.request("GET", f"/api/issues/{issue_id}")
    if not isinstance(value, dict):
        raise RuntimeError("Paperclip returned a non-object issue")
    return value


def process_config(script: str, *, env: dict[str, str]) -> dict:
    return {
        "command": "node",
        "args": [f"/milestone0/{script}"],
        "cwd": "/paperclip",
        "timeoutSec": 90,
        "env": env,
    }


def admitted_image_id() -> str:
    lock = (ROOT / "milestone0" / "dependencies.lock.yaml").read_text(encoding="utf-8")
    match = re.search(r'^    fork_image_id: "(sha256:[a-f0-9]{64})"$', lock, re.MULTILINE)
    if not match:
        raise RuntimeError("Paperclip image pin is missing from the dependency lock")
    expected = match.group(1)
    actual = subprocess.check_output([
        "docker", "inspect", "aif-m0-paperclip-fork-paperclip-fork-1", "--format", "{{.Image}}",
    ], text=True).strip()
    if actual != expected:
        raise RuntimeError(f"running Paperclip image {actual} differs from admitted pin {expected}")
    return actual


def wait_for_board_approval_stage(client: Client, issue_id: str, user_id: str, stage_index: int, timeout: float = 120) -> dict:
    deadline = time.monotonic() + timeout
    last: dict = {}
    while time.monotonic() < deadline:
        last = issue(client, issue_id)
        state = last.get("executionState") or {}
        participant = state.get("currentParticipant") or {}
        if last.get("status") == "in_review" and state.get("currentStageIndex") == stage_index and participant.get("userId") == user_id:
            return last
        if last.get("status") in {"blocked", "cancelled", "done"}:
            raise RuntimeError(f"issue reached unexpected status {last['status']} before board approval stage; state={state}")
        time.sleep(.5)
    raise RuntimeError(f"timed out waiting for board approval stage: status={last.get('status')} state={last.get('executionState')}")


def assert_no_external_grants(client: Client, company_id: str, agents: dict[str, str]) -> dict:
    """Policy routing probe must not mutate the shared Milestone 0 MCP connection."""
    observed = {}
    for name, agent_id in agents.items():
        _, effective = client.request("GET", f"/api/companies/{company_id}/tools/profiles/effective/agents/{agent_id}")
        if effective.get("allowedToolNames") or effective.get("installedConnections"):
            raise AssertionError(f"{name} unexpectedly received external tools")
        observed[name] = effective.get("allowedToolNames", [])
    return observed


def issue_runs_for_agent(client: Client, company_id: str, agent_id: str, issue_id: str) -> list[dict]:
    # These agents are new to this one probe; the agent filter avoids an
    # unpaginated company-wide run snapshot and makes duplicate runs visible.
    _, runs = client.request("GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100")
    return [run for run in runs if (run.get("contextSnapshot") or {}).get("issueId") == issue_id]


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    company_id = state["companyId"]
    client = Client(state["baseUrl"], state["boardApiKey"])
    marker = uuid4().hex[:10]
    include_qa = os.environ.get("AIF_M1_INCLUDE_QA") != "0"
    agents: dict[str, str] = {}
    created: list[str] = []
    result: dict = {"paperclipRevision": "62760ac9fc69572866c8eed5ad714ab1ddd6cc23", "marker": marker}
    try:
        result["paperclipImageId"] = admitted_image_id()
        configs = {
            "developer": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "Developer"}),
            "validator": process_config("validation-agent.mjs", env={
                "AIF_M1_CHECK_ROOT": "/milestone0",
                "AIF_M1_CHECK_TARGET": "/milestone0/validation-pass.mjs",
                "AIF_M1_ARTIFACT_DIR": "/paperclip/milestone1-validation",
            }),
            "reviewer": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "Reviewer"}),
            "qa": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "QA"}),
        }
        if not include_qa:
            del configs["qa"]
        roles = {"developer": "engineer", "validator": "general", "reviewer": "general", "qa": "qa"}
        for name, config in configs.items():
            record = create_agent(client, company_id, {
                "name": f"M1 {name} policy fixture {marker}",
                "role": roles[name], "title": f"Disposable {name} policy gate",
                "adapterType": "process", "adapterConfig": config, "budgetMonthlyCents": 100,
            })
            agent_id = record["id"]
            created.append(agent_id)
            agents[name] = agent_id
        result["agents"] = agents
        result["effectiveExternalTools"] = assert_no_external_grants(client, company_id, agents)
        policy = engineering_execution_policy(
            agents["developer"], agents["validator"], agents["reviewer"], state["userId"],
            qa_agent_id=agents.get("qa"),
        )
        _, created_issue = client.request("POST", f"/api/companies/{company_id}/issues", {
            "title": f"Milestone 1.2 execution policy probe {marker}",
            "description": "Disposable native issue-policy integration proof; no production task.",
            "status": "todo", "assigneeAgentId": agents["developer"],
            "executionPolicy": policy, "idempotencyKey": f"m1-policy-probe-{marker}",
        }, expected=(200, 201))
        issue_id = created_issue["id"]
        result["issueId"] = issue_id
        pending = wait_for_board_approval_stage(client, issue_id, state["userId"], 3 if include_qa else 2)
        completed = (pending.get("executionState") or {}).get("completedStageIds") or []
        expected_stages = pending["executionPolicy"]["stages"]
        if completed != [stage["id"] for stage in expected_stages[:-1]]:
            raise AssertionError("Paperclip did not record every preceding stage before board approval")
        issue_runs = [
            {"id": run["id"], "agentId": run["agentId"], "status": run["status"]}
            for agent_id in agents.values()
            for run in issue_runs_for_agent(client, company_id, agent_id, issue_id)
        ]
        if len(issue_runs) != len(agents) or {run["agentId"] for run in issue_runs} != set(agents.values()):
            raise AssertionError(f"missing independent stage runs: {issue_runs}")
        result["runs"] = issue_runs
        run_by_agent = {run["agentId"]: run["id"] for run in issue_runs}
        _, comments = client.request("GET", f"/api/issues/{issue_id}/comments")
        comments_by_run = {comment.get("createdByRunId"): comment for comment in comments}
        if not all(run["id"] in comments_by_run for run in issue_runs):
            raise AssertionError("a stage actor did not leave a same-run Paperclip comment")
        expected_order = [agents["developer"], agents["validator"], agents["reviewer"]]
        if include_qa:
            expected_order.append(agents["qa"])
        ordered_comments = sorted(
            [comments_by_run[run["id"]] for run in issue_runs], key=lambda item: item["createdAt"]
        )
        observed_order = [next(run["agentId"] for run in issue_runs if run["id"] == item["createdByRunId"]) for item in ordered_comments]
        if observed_order != expected_order:
            raise AssertionError(f"Paperclip stage actor order differs from policy: {observed_order}")
        validation_comment = comments_by_run[run_by_agent[agents["validator"]]]["body"]
        match = re.search(r"evidence=file://(/paperclip/milestone1-validation/[^ ]+\.json) sha256=([a-f0-9]{64})", validation_comment)
        if not match or not validation_comment.startswith("Deterministic validation passed:"):
            raise AssertionError("validation decision lacks a content-addressed passing artifact")
        artifact_path, expected_digest = match.groups()
        artifact_bytes = subprocess.check_output([
            "docker", "exec", "aif-m0-paperclip-fork-paperclip-fork-1", "cat", artifact_path,
        ])
        if hashlib.sha256(artifact_bytes).hexdigest() != expected_digest:
            raise AssertionError("validation artifact bytes do not match the Paperclip decision comment")
        evidence = json.loads(artifact_bytes)
        target_digest = hashlib.sha256((ROOT / "milestone0" / "fixtures" / "paperclip" / "validation-pass.mjs").read_bytes()).hexdigest()
        if (
            evidence.get("issueId") != issue_id
            or evidence.get("runId") != run_by_agent[agents["validator"]]
            or evidence.get("agentId") != agents["validator"]
            or evidence.get("target") != "validation-pass.mjs"
            or evidence.get("targetSha256") != target_digest
            or evidence.get("exitCode") != 0
            or evidence.get("verdict") != "passed"
        ):
            raise AssertionError("validation artifact contents do not identify the passing issue/run/check")
        result["validationArtifact"] = {"path": artifact_path, "sha256": expected_digest}
        result["boardApprovalStageHeld"] = True
        _, approved = client.request("PATCH", f"/api/issues/{issue_id}", {
            "status": "done", "comment": "Milestone 1.2 disposable integration gate accepted after independent stages.",
        })
        if approved.get("status") != "done" or (approved.get("executionState") or {}).get("status") != "completed":
            raise AssertionError("simulated board approval did not complete the native issue policy")
        if (approved.get("executionState") or {}).get("completedStageIds") != [stage["id"] for stage in expected_stages]:
            raise AssertionError("Paperclip did not record the simulated board approval stage")
        result["simulatedBoardApprovalCompleted"] = True
        result["executionPolicy"] = approved.get("executionPolicy")
        result["executionState"] = approved.get("executionState")
        print(json.dumps({"pass": True, "issueId": issue_id, "runCount": len(issue_runs), "simulatedBoardApprovalCompleted": True}))
    except Exception as exc:
        result["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if result.get("issueId") and not result.get("simulatedBoardApprovalCompleted"):
            try:
                current = issue(client, result["issueId"])
                if current.get("title") == f"Milestone 1.2 execution policy probe {marker}" and current.get("status") not in {"done", "cancelled"}:
                    client.request("PATCH", f"/api/issues/{result['issueId']}", {
                        "status": "cancelled", "comment": "Disposable policy probe stopped after failure.",
                    })
            except Exception as exc:
                result.setdefault("cleanupErrors", []).append(f"issue: {type(exc).__name__}: {exc}")
        for agent_id in created:
            try:
                client.request("POST", f"/api/agents/{agent_id}/pause", expected=(200,))
            except ApiError as exc:
                result.setdefault("cleanupErrors", []).append(f"agent {agent_id}: {exc}")
        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
