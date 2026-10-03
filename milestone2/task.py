"""Submit and inspect Paperclip tasks; Paperclip owns dispatch and all state."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import URLError
from uuid import UUID

from milestone0.scripts.paperclip_admission import ApiError, Client
from milestone1.paperclip_policy import engineering_execution_policy


def read_object(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read JSON object from {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def text(value, label, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label} must be nonempty text of at most {limit} characters")
    return value.strip()


def uuid(value, label):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"{label} must be a Paperclip UUID") from error


def build_payload(state, workflow, task, *, start=False):
    agents = {name: uuid(workflow.get(name), name) for name in
              ("developerAgentId", "validatorAgentId", "reviewerAgentId")}
    qa = uuid(workflow["qaAgentId"], "qaAgentId") if workflow.get("qaAgentId") else None
    return {
        "title": text(task.get("title"), "title", 200),
        "description": text(task.get("description"), "description", 200_000),
        "idempotencyKey": text(task.get("requestKey"), "requestKey", 255),
        "projectId": uuid(workflow.get("projectId"), "projectId"),
        "status": "todo" if start else "backlog",
        "assigneeAgentId": agents["developerAgentId"],
        "executionPolicy": engineering_execution_policy(
            agents["developerAgentId"], agents["validatorAgentId"], agents["reviewerAgentId"],
            text(state.get("userId"), "owner userId", 255), qa_agent_id=qa,
        ),
    }


def preflight(client, company_id, payload, *, start):
    _, project = client.request("GET", f"/api/projects/{payload['projectId']}")
    if not isinstance(project, dict) or project.get("companyId") != company_id:
        raise ValueError("Project does not belong to the configured company")
    agents = [payload["assigneeAgentId"]] + [
        participant["agentId"] for stage in payload["executionPolicy"]["stages"]
        for participant in stage["participants"] if participant["type"] == "agent"
    ]
    for agent_id in agents:
        _, agent = client.request("GET", f"/api/agents/{agent_id}")
        if not isinstance(agent, dict) or agent.get("companyId") != company_id:
            raise ValueError("Workflow agent does not belong to the configured company")
        if agent.get("status") == "terminated":
            raise ValueError(f"Workflow agent {agent_id} is terminated")
        if start and agent.get("status") not in {"idle", "running"}:
            raise ValueError(f"Workflow agent {agent_id} is {agent.get('status')}; resume the selected agent in Paperclip before --start")


def progress(issue, company_id):
    if not isinstance(issue, dict) or issue.get("companyId") != company_id:
        raise ValueError("Issue does not belong to the configured company")
    state = issue.get("executionState") or {}
    stages = (issue.get("executionPolicy") or {}).get("stages") or []
    index = state.get("currentStageIndex")
    if issue.get("status") in {"done", "cancelled"}:
        current = "Complete" if issue["status"] == "done" else "Cancelled"
    elif state.get("currentStageType") == "approval":
        current = "Owner approval"
    elif isinstance(index, int) and 0 <= index < len(stages):
        current = {0: "Tests", 1: "Reviewer", 2: "QA"}.get(index, "Review")
    else:
        current = "Developer"
    return {
        "id": issue["id"], "identifier": issue.get("identifier"), "title": issue.get("title"),
        "status": issue.get("status"), "currentStage": current,
        "completedStages": len(state.get("completedStageIds") or []), "totalStages": len(stages),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=os.environ.get("AIF_PAPERCLIP_STATE"), help="private Paperclip board state JSON; or AIF_PAPERCLIP_STATE")
    parser.add_argument("--json", action="store_true", help="print a compact machine-readable result")
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit", help="attach the existing independent engineering policy")
    submit.add_argument("--workflow", required=True, help="project and logical agent IDs JSON")
    submit.add_argument("--task", required=True, help="title, description and stable requestKey JSON")
    submit.add_argument("--start", action="store_true", help="create a todo task for native dispatch; selected agents must already be active")
    submit.add_argument("--dry-run", action="store_true", help="show the payload without contacting Paperclip")
    submit.add_argument("--program-note", action="store_true",
                        help="print a pointer to milestone2.program for one-authorization multi-wave programs")
    status = commands.add_parser("status", help="show Paperclip's authoritative task progress")
    status.add_argument("issue", help="issue UUID or identifier, e.g. AIF-47")
    scorecard = commands.add_parser("scorecard", help="read native task quality, timings and usage coverage; no writes")
    scorecard.add_argument("issue", help="issue UUID or identifier, e.g. AIF-49")
    args = parser.parse_args(argv)
    try:
        if args.command == "submit" and args.program_note:
            print("For one-authorization self-enhancement programs "
                  "(one parent, four dependency-ordered waves), use python -m milestone2.program submit --help")
            return 0
        if not args.state:
            raise ValueError("Set AIF_PAPERCLIP_STATE or pass --state with the private board state file")
        state = read_object(args.state)
        company_id = uuid(state.get("companyId"), "companyId")
        if args.command == "submit":
            payload = build_payload(state, read_object(args.workflow), read_object(args.task), start=args.start)
            if args.dry_run:
                print(json.dumps(payload, indent=2))
                return 0
        else:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*-\d+|[a-fA-F0-9-]{36}", args.issue):
                raise ValueError("Use a Paperclip issue UUID or identifier")
        client = Client(text(state.get("baseUrl"), "baseUrl", 2048), text(state.get("boardApiKey"), "boardApiKey", 4096))
        if args.command == "submit":
            preflight(client, company_id, payload, start=args.start)
            _, issue = client.request("POST", f"/api/companies/{company_id}/issues", payload, expected=(200, 201))
        else:
            _, issue = client.request("GET", f"/api/issues/{args.issue}")
        if args.command == "scorecard":
            from milestone2.scorecard import collect, format_scorecard
            report = collect(client, issue, company_id)
            print(json.dumps(report, allow_nan=False) if args.json else format_scorecard(report))
            return 0
        report = progress(issue, company_id)
        if args.json:
            print(json.dumps(report))
        else:
            print(f"{report['identifier'] or report['id']} — {report['title']}")
            print(f"Status: {report['status']} | Stage: {report['currentStage']} | Gates: {report['completedStages']}/{report['totalStages']}")
            if args.command == "submit" and not args.start:
                print("Saved in backlog; no agents launched. Start it in Paperclip when ready.")
        return 0
    except ApiError as error:
        print(f"Paperclip API returned {error.status}; no automatic retry. Check the task before resubmitting with the same requestKey.", file=sys.stderr)
    except URLError:
        print("Cannot reach Paperclip; check it is running and the state file baseUrl is correct.", file=sys.stderr)
    except ValueError as error:
        print(str(error), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
