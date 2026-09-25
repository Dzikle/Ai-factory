#!/usr/bin/env python3
"""Disposable live proof that failed validation returns to the implementer."""

from __future__ import annotations

import json
from pathlib import Path
import time
from uuid import uuid4

from milestone0.scripts.paperclip_admission import Client, ApiError, create_agent
from milestone1.paperclip_policy import engineering_execution_policy
from milestone1.paperclip_policy_probe import STATE_PATH, admitted_image_id, issue, issue_runs_for_agent, process_config


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / ".milestone0" / "milestone1-policy-failure-probe.json"


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    company_id = state["companyId"]
    client = Client(state["baseUrl"], state["boardApiKey"])
    marker = uuid4().hex[:10]
    result: dict = {"paperclipRevision": "62760ac9fc69572866c8eed5ad714ab1ddd6cc23", "marker": marker}
    created: list[str] = []
    try:
        result["paperclipImageId"] = admitted_image_id()
        configs = {
            "developer": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "Developer"}),
            "validator": process_config("validation-agent.mjs", env={
                "AIF_M1_CHECK_ROOT": "/milestone0",
                "AIF_M1_CHECK_TARGET": "/milestone0/validation-fail.txt",
                "AIF_M1_ARTIFACT_DIR": "/paperclip/milestone1-validation",
            }),
            "reviewer": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "Reviewer"}),
            "qa": process_config("stage-decision-agent.mjs", env={"AIF_M1_STAGE_LABEL": "QA"}),
        }
        roles = {"developer": "engineer", "validator": "general", "reviewer": "general", "qa": "qa"}
        agents = {}
        for name, config in configs.items():
            record = create_agent(client, company_id, {
                "name": f"M1 {name} failure fixture {marker}", "role": roles[name],
                "title": f"Disposable {name} failure gate", "adapterType": "process",
                "adapterConfig": config, "budgetMonthlyCents": 100,
            })
            agents[name] = record["id"]
            created.append(record["id"])
        result["agents"] = agents
        _, record = client.request("POST", f"/api/companies/{company_id}/issues", {
            "title": f"Milestone 1.2 failed validation probe {marker}",
            "description": "Disposable fail-closed review-stage test; no production task.",
            "status": "todo", "assigneeAgentId": agents["developer"],
            "executionPolicy": engineering_execution_policy(
                agents["developer"], agents["validator"], agents["reviewer"], state["userId"], qa_agent_id=agents["qa"],
            ),
            "idempotencyKey": f"m1-policy-failure-{marker}",
        }, expected=(200, 201))
        issue_id = record["id"]
        result["issueId"] = issue_id
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            current = issue(client, issue_id)
            execution = current.get("executionState") or {}
            participant = execution.get("currentParticipant") or {}
            if execution.get("changesRequestedCount", 0) >= 3 and participant.get("userId") == state["userId"]:
                break
            if current.get("status") in {"done", "cancelled", "blocked"}:
                raise RuntimeError(f"failed validation reached unexpected issue status {current['status']}")
            time.sleep(.5)
        else:
            raise RuntimeError("timed out waiting for Paperclip's bounded review escalation")
        if current["status"] != "in_review" or execution.get("currentStageIndex") != 0:
            raise AssertionError("validation failure did not remain at the validation stage")
        if execution.get("completedStageIds"):
            raise AssertionError("a failed check unexpectedly completed a review stage")
        _, comments = client.request("GET", f"/api/issues/{issue_id}/comments")
        failed = [item for item in comments if str(item.get("body", "")).startswith("Deterministic validation failed:")]
        developer = [item for item in comments if str(item.get("body", "")).startswith("Developer fixture decision")]
        if len(failed) < 3 or len(developer) < 3:
            raise AssertionError(f"Paperclip did not return failed validation to Developer three times: {len(failed)} / {len(developer)}")
        if any("validation passed" in str(item.get("body", "")) for item in comments):
            raise AssertionError("invalid syntax was incorrectly accepted")
        if any(str(item.get("body", "")).startswith(("Reviewer fixture", "QA fixture")) for item in comments):
            raise AssertionError("Reviewer/QA ran despite failed validation")
        runs_by_role = {
            name: issue_runs_for_agent(client, company_id, agent_id, issue_id)
            for name, agent_id in agents.items()
        }
        if runs_by_role["reviewer"] or runs_by_role["qa"]:
            raise AssertionError("Reviewer/QA received an issue-bound run despite failed validation")
        if {item.get("createdByRunId") for item in failed} != {run["id"] for run in runs_by_role["validator"]}:
            raise AssertionError("failed validation comments do not match validator runs")
        if {item.get("createdByRunId") for item in developer} != {run["id"] for run in runs_by_role["developer"]}:
            raise AssertionError("Developer resubmission comments do not match Developer runs")
        result["failedValidationDecisions"] = len(failed)
        result["developerResubmissions"] = len(developer) - 1
        result["escalatedToUser"] = state["userId"]
        result["changesRequestedCount"] = execution["changesRequestedCount"]
        _, cancelled = client.request("PATCH", f"/api/issues/{issue_id}", {
            "status": "cancelled", "comment": "Disposable failure gate verified; no implementation to integrate.",
        })
        result["closedFixtureStatus"] = cancelled.get("status")
        print(json.dumps({"pass": True, "issueId": issue_id, "failedChecks": len(failed), "developerResubmissions": len(developer) - 1}))
    except Exception as exc:
        result["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if result.get("issueId") and result.get("closedFixtureStatus") != "cancelled":
            try:
                current = issue(client, result["issueId"])
                if current.get("title") == f"Milestone 1.2 failed validation probe {marker}" and current.get("status") not in {"done", "cancelled"}:
                    _, cancelled = client.request("PATCH", f"/api/issues/{result['issueId']}", {
                        "status": "cancelled", "comment": "Disposable failed-validation probe stopped after failure.",
                    })
                    result["closedFixtureStatus"] = cancelled.get("status")
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
