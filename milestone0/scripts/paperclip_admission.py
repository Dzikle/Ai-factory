#!/usr/bin/env python3
"""Live Paperclip admission driver. Stores secrets/results only under ignored .milestone0."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".milestone0" / "paperclip-state.json"


class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, body: object) -> None:
        super().__init__(f"{method} {path} returned {status}: {str(body)[:800]}")
        self.status = status
        self.body = body


class Client:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(
        self,
        method: str,
        path: str,
        body: object | None = None,
        *,
        expected: tuple[int, ...] = (200,),
    ) -> tuple[int, object]:
        headers = {"Accept": "application/json", "Origin": "http://localhost:3100"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, method=method, headers=headers
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                status = response.status
                raw = response.read().decode(errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode(errors="replace")
        try:
            parsed: object = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        if status not in expected:
            raise ApiError(method, path, status, parsed)
        return status, parsed


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def public(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: public(item)
            for key, item in value.items()
            if key.lower() not in {"token", "apikey", "password", "secret"}
        }
    if isinstance(value, list):
        return [public(item) for item in value]
    return value


def create_agent(client: Client, company_id: str, body: dict) -> dict:
    _, result = client.request("POST", f"/api/companies/{company_id}/agents", body, expected=(201,))
    assert isinstance(result, dict)
    return result


def setup(base_url: str) -> None:
    if STATE_PATH.exists():
        raise RuntimeError(f"refusing to overwrite existing state: {STATE_PATH}")
    client = Client(base_url)
    email = f"milestone0-{uuid.uuid4().hex[:12]}@ai-factory.invalid"
    password = secrets.token_urlsafe(32)
    _, signup = client.request(
        "POST",
        "/api/auth/sign-up/email",
        {"email": email, "password": password, "name": "Milestone 0"},
    )
    _, bootstrap = client.request("POST", "/api/bootstrap/claim")
    _, access = client.request("GET", "/api/cli-auth/me")
    _, key = client.request("POST", "/api/board-api-keys", {"name": "milestone0-admission"}, expected=(201,))
    if not isinstance(key, dict) or not isinstance(key.get("token"), str):
        raise RuntimeError("Paperclip did not return the one-time board API key")

    client = Client(base_url, key["token"])
    _, company = client.request(
        "POST",
        "/api/companies",
        {"name": "AI Factory Milestone 0", "description": "Disposable dependency admission fixture"},
        expected=(201,),
    )
    assert isinstance(company, dict)
    company_id = company["id"]

    _, installed = client.request(
        "POST",
        "/api/adapters/install",
        {"packageName": "/milestone0/context-seam-adapter", "isLocalPath": True},
        expected=(201,),
    )
    _, adapters = client.request("GET", "/api/adapters")
    adapter_items = adapters if isinstance(adapters, list) else []
    adapter_types = [item.get("type") for item in adapter_items if isinstance(item, dict)]
    if "process" not in adapter_types:
        raise RuntimeError(f"process adapter is unavailable: {adapter_types}")
    if "aif_context_seam_poc" not in adapter_types:
        raise RuntimeError(f"external context seam adapter is unavailable: {adapter_types}")

    process_config = {
        "command": "node",
        "args": ["/milestone0/finite-agent.mjs"],
        "cwd": "/paperclip",
        "timeoutSec": 180,
        "env": {"AIF_M0_OUTPUT_DIR": "/paperclip/milestone0-runs"},
    }
    developer = create_agent(
        client,
        company_id,
        {
            "name": "Milestone 0 Developer",
            "role": "engineer",
            "title": "Developer admission fixture",
            "adapterType": "process",
            "adapterConfig": process_config,
            "budgetMonthlyCents": 100,
        },
    )
    reviewer = create_agent(
        client,
        company_id,
        {
            "name": "Milestone 0 Reviewer",
            "role": "general",
            "title": "Independent Reviewer",
            "adapterType": "process",
            "adapterConfig": process_config,
            "budgetMonthlyCents": 100,
        },
    )
    qa = create_agent(
        client,
        company_id,
        {
            "name": "Milestone 0 QA",
            "role": "qa",
            "title": "Independent QA",
            "adapterType": "process",
            "adapterConfig": process_config,
            "budgetMonthlyCents": 100,
        },
    )
    seam = create_agent(
        client,
        company_id,
        {
            "name": "Milestone 0 Context Seam",
            "role": "researcher",
            "title": "Pre-run extension fixture",
            "adapterType": "aif_context_seam_poc",
            "adapterConfig": {},
            "budgetMonthlyCents": 100,
        },
    )

    for agent in (developer, reviewer, qa, seam):
        client.request("POST", f"/api/agents/{agent['id']}/pause", expected=(200,))

    _, connection = client.request(
        "POST",
        f"/api/companies/{company_id}/tools/connections",
        {
            "applicationName": "OpenSearch Admission",
            "name": "OpenSearch read-only admission MCP",
            "connectionPurpose": "tool",
            "transport": "mcp_remote",
            "authKind": "none",
            "credentialPolicy": "shared",
            "ownership": "customer",
            "status": "active",
            "connectionKind": "managed",
            "config": {"url": "http://host.docker.internal:19901/mcp"},
            "transportConfig": {"url": "http://host.docker.internal:19901/mcp"},
            "enabled": True,
        },
        expected=(201,),
    )
    assert isinstance(connection, dict)
    connection_id = connection["id"]
    _, refreshed = client.request(
        "POST", f"/api/tool-connections/{connection_id}/catalog/refresh"
    )
    _, catalog = client.request("GET", f"/api/tool-connections/{connection_id}/catalog")

    state = {
        "baseUrl": base_url,
        "boardApiKeyId": key["id"],
        "boardApiKey": key["token"],
        "userId": access.get("userId") if isinstance(access, dict) else None,
        "companyId": company_id,
        "agents": {
            "developer": developer["id"],
            "reviewer": reviewer["id"],
            "qa": qa["id"],
            "seam": seam["id"],
        },
        "connectionId": connection_id,
        "createdAt": time.time(),
    }
    save_state(state)
    print(
        json.dumps(
            public(
                {
                    "signupStatus": "created",
                    "bootstrap": bootstrap,
                    "access": access,
                    "companyId": company_id,
                    "agents": state["agents"],
                    "adapterTypes": adapter_types,
                    "installed": installed,
                    "connection": connection,
                    "refresh": refreshed,
                    "catalog": catalog,
                    "statePath": str(STATE_PATH),
                }
            ),
            indent=2,
            sort_keys=True,
        )
    )


def state_client() -> tuple[dict, Client]:
    state = load_state()
    token = state.get("boardApiKey")
    base_url = state.get("baseUrl")
    if not isinstance(token, str) or not isinstance(base_url, str):
        raise RuntimeError("run setup first")
    return state, Client(base_url, token)


def gateway_name(application_key: str, connection_id: str, upstream_name: str) -> str:
    def slug(value: str) -> str:
        return "-".join(filter(None, __import__("re").split(r"[^a-z0-9]+", value.lower())))[:64]

    return f"mcp.{slug(application_key)}-{connection_id.replace('-', '')[:8]}:{slug(upstream_name)}"


def wait_run(client: Client, run_id: str, timeout: float = 90) -> dict:
    deadline = time.monotonic() + timeout
    last: dict = {}
    while time.monotonic() < deadline:
        _, result = client.request("GET", f"/api/heartbeat-runs/{run_id}")
        if isinstance(result, dict):
            last = result
            if result.get("status") in {"succeeded", "failed", "cancelled", "timed_out", "interrupted"}:
                return result
        time.sleep(0.5)
    raise RuntimeError(f"run {run_id} did not finish; last status={last.get('status')}")


def summarize_run(run: dict) -> dict:
    result = run.get("resultJson") if isinstance(run.get("resultJson"), dict) else {}
    return {
        "id": run.get("id"),
        "status": run.get("status"),
        "nativeIssueId": run.get("nativeIssueId"),
        "processPid": run.get("processPid"),
        "processGroupId": run.get("processGroupId"),
        "controllerBootId": run.get("controllerBootId"),
        "controllerLeaseExpiresAt": run.get("controllerLeaseExpiresAt"),
        "execution": run.get("execution"),
        "error": run.get("error"),
        "errorCode": run.get("errorCode"),
        "resultJson": result,
    }


def configure_process_agent(client: Client, agent_id: str, sleep_ms: int) -> None:
    client.request(
        "PATCH",
        f"/api/agents/{agent_id}",
        {
            "adapterConfig": {
                "command": "node",
                "args": ["/milestone0/finite-agent.mjs"],
                "cwd": "/paperclip",
                "timeoutSec": 180,
                "graceSec": 2,
                "env": {
                    "AIF_M0_OUTPUT_DIR": "/paperclip/milestone0-runs",
                    "AIF_M0_SLEEP_MS": str(sleep_ms),
                },
            },
            "replaceAdapterConfig": True,
        },
    )


def find_issue_run(
    client: Client,
    company_id: str,
    agent_id: str,
    issue_id: str,
    *,
    statuses: set[str] | None = None,
    timeout: float = 45,
) -> dict:
    deadline = time.monotonic() + timeout
    last_runs: list[dict] = []
    while time.monotonic() < deadline:
        _, response = client.request(
            "GET",
            f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100",
        )
        last_runs = [item for item in response if isinstance(item, dict)] if isinstance(response, list) else []
        matching = [
            run
            for run in last_runs
            if run.get("nativeIssueId") == issue_id
            or (
                isinstance(run.get("contextSnapshot"), dict)
                and run["contextSnapshot"].get("issueId") == issue_id
            )
        ]
        matching.sort(key=lambda run: str(run.get("createdAt") or ""), reverse=True)
        for run in matching:
            if statuses is None or run.get("status") in statuses:
                return run
        time.sleep(0.25)
    raise RuntimeError(
        f"no matching run for issue {issue_id}; recent statuses="
        f"{[(run.get('id'), run.get('status')) for run in last_runs[:8]]}"
    )


def wait_run_process(client: Client, run_id: str, timeout: float = 30) -> dict:
    deadline = time.monotonic() + timeout
    last: dict = {}
    while time.monotonic() < deadline:
        _, result = client.request("GET", f"/api/heartbeat-runs/{run_id}")
        if isinstance(result, dict):
            last = result
            if result.get("status") == "running" and isinstance(result.get("processPid"), int):
                return result
            if result.get("status") in {"succeeded", "failed", "cancelled", "timed_out"}:
                break
        time.sleep(0.1)
    raise RuntimeError(
        f"run {run_id} did not expose a live process; status={last.get('status')} "
        f"pid={last.get('processPid')}"
    )


def process_crash() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    agent_id = state["agents"]["developer"]
    configure_process_agent(client, agent_id, 30_000)
    client.request("POST", f"/api/agents/{agent_id}/pause", expected=(200,))
    _, issue = client.request(
        "POST",
        f"/api/companies/{company_id}/issues",
        {
            "title": "Milestone 0 killed child process v5",
            "description": "Admission-only process failure and task continuity probe.",
            "status": "todo",
            "assigneeAgentId": agent_id,
            "idempotencyKey": "milestone0-process-crash-v5",
        },
        expected=(200, 201),
    )
    assert isinstance(issue, dict)
    client.request("POST", f"/api/agents/{agent_id}/resume")
    _, wake = client.request(
        "POST",
        f"/api/agents/{agent_id}/wakeup",
        {
            "source": "assignment",
            "triggerDetail": "system",
            "reason": "issue_assigned",
            "payload": {"issueId": issue["id"], "mutation": "admission_process_crash"},
            "idempotencyKey": "milestone0-process-crash-wake-v5",
        },
        expected=(200, 202),
    )
    assert isinstance(wake, dict)
    run_id = wake.get("runId") or wake.get("id")
    if not isinstance(run_id, str):
        raise RuntimeError(f"process crash wake returned no run id: {wake}")
    run = wait_run_process(client, run_id)
    pid = run.get("processPid")
    if not isinstance(pid, int) or pid <= 0:
        raise RuntimeError(f"running process has no PID: {summarize_run(run)}")
    subprocess.run(
        [
            "docker",
            "exec",
            "aif-m0-paperclip-paperclip-1",
            "sh",
            "-lc",
            f"kill -9 {pid}",
        ],
        check=True,
    )
    terminal = wait_run(client, run["id"], timeout=60)
    _, recovery = client.request("GET", f"/api/issues/{issue['id']}/recovery-actions")
    active_recovery = recovery.get("active") if isinstance(recovery, dict) else None
    if not isinstance(active_recovery, dict):
        raise RuntimeError(f"failed run produced no active recovery action: {recovery}")
    configure_process_agent(client, agent_id, 1_000)
    _, resolved_recovery = client.request(
        "POST",
        f"/api/issues/{issue['id']}/recovery-actions/resolve",
        {
            "actionId": active_recovery["id"],
            "outcome": "restored",
            "sourceIssueStatus": "todo",
            "resolutionNote": "Admission operator verified the killed fixture process is stopped; retry is safe.",
            "executionReconciliation": {
                "runId": run["id"],
                "providerStopped": True,
                "actionOutcome": "mixed",
                "outcomeEvidence": (
                    "The fixture wrote its run artifact before sleeping, then PID termination was observed "
                    "and the container no longer contained that process. No issue mutation was performed."
                ),
            },
        },
    )
    successor = find_issue_run(
        client,
        company_id,
        agent_id,
        issue["id"],
        statuses={"succeeded"},
        timeout=45,
    )
    _, persisted_issue = client.request("GET", f"/api/issues/{issue['id']}")
    _, runs = client.request(
        "GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100"
    )
    issue_runs = [
        summarize_run(item)
        for item in runs
        if isinstance(item, dict)
        and (
            item.get("nativeIssueId") == issue["id"]
            or (
                isinstance(item.get("contextSnapshot"), dict)
                and item["contextSnapshot"].get("issueId") == issue["id"]
            )
        )
    ] if isinstance(runs, list) else []
    client.request("POST", f"/api/agents/{agent_id}/pause")
    state.update({
        "processCrashIssueId": issue["id"],
        "processCrashRunId": run["id"],
        "processCrashSuccessorRunId": successor["id"],
    })
    save_state(state)
    print(json.dumps(public({
        "killedPid": pid,
        "terminalRun": summarize_run(terminal),
        "activeRecoveryAction": active_recovery,
        "resolvedRecovery": resolved_recovery,
        "successorRun": summarize_run(successor),
        "persistedIssue": {
            "id": persisted_issue.get("id") if isinstance(persisted_issue, dict) else None,
            "status": persisted_issue.get("status") if isinstance(persisted_issue, dict) else None,
            "assigneeAgentId": persisted_issue.get("assigneeAgentId") if isinstance(persisted_issue, dict) else None,
        },
        "issueRuns": issue_runs,
    }), indent=2, sort_keys=True))


def process_reconcile() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    agent_id = state["agents"]["developer"]
    issue_id = state["processCrashIssueId"]
    run_id = state["processCrashRunId"]
    _, recovery = client.request("GET", f"/api/issues/{issue_id}/recovery-actions")
    active = recovery.get("active") if isinstance(recovery, dict) else None
    if not isinstance(active, dict):
        raise RuntimeError(f"no active recovery action for issue {issue_id}: {recovery}")
    configure_process_agent(client, agent_id, 1_000)
    client.request("POST", f"/api/agents/{agent_id}/resume")
    _, resolved = client.request(
        "POST",
        f"/api/issues/{issue_id}/recovery-actions/resolve",
        {
            "actionId": active["id"],
            "outcome": "restored",
            "sourceIssueStatus": "todo",
            "resolutionNote": "Admission operator verified the killed fixture process is stopped; retry is safe.",
            "executionReconciliation": {
                "runId": run_id,
                "providerStopped": True,
                "actionOutcome": "mixed",
                "outcomeEvidence": (
                    "The fixture wrote its run artifact before sleeping, then PID termination was observed "
                    "and the container no longer contained that process. No issue mutation was performed."
                ),
            },
        },
    )
    successor: dict | None = None
    try:
        successor = find_issue_run(
            client,
            company_id,
            agent_id,
            issue_id,
            statuses={"succeeded"},
            timeout=15,
        )
        if successor.get("id") == run_id:
            successor = None
    except RuntimeError:
        successor = None
    _, issue = client.request("GET", f"/api/issues/{issue_id}")
    client.request("POST", f"/api/agents/{agent_id}/pause")
    state["processCrashSuccessorRunId"] = successor.get("id") if successor else None
    save_state(state)
    print(json.dumps(public({
        "activeRecoveryAction": active,
        "resolved": resolved,
        "successorRun": summarize_run(successor) if successor else None,
        "persistedIssue": {
            "id": issue.get("id") if isinstance(issue, dict) else None,
            "status": issue.get("status") if isinstance(issue, dict) else None,
            "assigneeAgentId": issue.get("assigneeAgentId") if isinstance(issue, dict) else None,
            "executionRunId": issue.get("executionRunId") if isinstance(issue, dict) else None,
        },
    }), indent=2, sort_keys=True))


def orphan_prepare() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    agent_id = state["agents"]["developer"]
    configure_process_agent(client, agent_id, 60_000)
    client.request("POST", f"/api/agents/{agent_id}/pause", expected=(200,))
    _, issue = client.request(
        "POST",
        f"/api/companies/{company_id}/issues",
        {
            "title": "Milestone 0 controller orphan recovery v3",
            "description": "Admission-only controller crash, orphan lease, and durable retry probe.",
            "status": "todo",
            "assigneeAgentId": agent_id,
            "idempotencyKey": "milestone0-controller-orphan-v3",
        },
        expected=(200, 201),
    )
    assert isinstance(issue, dict)
    client.request("POST", f"/api/agents/{agent_id}/resume")
    _, wake = client.request(
        "POST",
        f"/api/agents/{agent_id}/wakeup",
        {
            "source": "assignment",
            "triggerDetail": "system",
            "reason": "issue_assigned",
            "payload": {"issueId": issue["id"], "mutation": "admission_controller_loss"},
            "idempotencyKey": "milestone0-controller-orphan-wake-v3",
        },
        expected=(200, 202),
    )
    assert isinstance(wake, dict)
    run_id = wake.get("runId") or wake.get("id")
    if not isinstance(run_id, str):
        raise RuntimeError(f"orphan wake returned no run id: {wake}")
    run = wait_run_process(client, run_id)
    # The already-spawned child keeps its captured 60s delay. A recovered
    # successor reads this 1s configuration after the controller restarts.
    configure_process_agent(client, agent_id, 1_000)
    state.update({"orphanIssueId": issue["id"], "orphanRunId": run["id"]})
    save_state(state)
    print(json.dumps(public({
        "issueId": issue["id"],
        "runningBeforeControllerLoss": summarize_run(run),
    }), indent=2, sort_keys=True))


def orphan_report() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    agent_id = state["agents"]["developer"]
    original_run_id = state["orphanRunId"]
    original = wait_run(client, original_run_id, timeout=120)
    _, recovery = client.request(
        "GET", f"/api/issues/{state['orphanIssueId']}/recovery-actions"
    )
    active_recovery = recovery.get("active") if isinstance(recovery, dict) else None
    resolved_recovery: object | None = None
    successor: dict | None = None
    if isinstance(active_recovery, dict):
        _, resolved_recovery = client.request(
            "POST",
            f"/api/issues/{state['orphanIssueId']}/recovery-actions/resolve",
            {
                "actionId": active_recovery["id"],
                "outcome": "restored",
                "sourceIssueStatus": "todo",
                "resolutionNote": "Admission operator verified the killed controller and its child are stopped; retry is safe.",
                "executionReconciliation": {
                    "runId": original_run_id,
                    "providerStopped": True,
                    "actionOutcome": "mixed",
                    "outcomeEvidence": (
                        "The controller container was killed after the fixture wrote its durable run artifact. "
                        "Container exit removed the child process; no issue mutation was performed."
                    ),
                },
            },
        )
        successor = find_issue_run(
            client,
            company_id,
            agent_id,
            state["orphanIssueId"],
            statuses={"succeeded"},
            timeout=45,
        )
    _, runs = client.request(
        "GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100"
    )
    issue_runs = [
        item
        for item in runs
        if isinstance(item, dict)
        and (
            item.get("nativeIssueId") == state["orphanIssueId"]
            or (
                isinstance(item.get("contextSnapshot"), dict)
                and item["contextSnapshot"].get("issueId") == state["orphanIssueId"]
            )
        )
    ] if isinstance(runs, list) else []
    _, issue = client.request("GET", f"/api/issues/{state['orphanIssueId']}")
    client.request("POST", f"/api/agents/{agent_id}/pause")
    print(json.dumps(public({
        "originalRun": summarize_run(original),
        "activeRecoveryAction": active_recovery,
        "resolvedRecovery": resolved_recovery,
        "successorRun": summarize_run(successor) if successor else None,
        "issueRuns": [summarize_run(run) for run in issue_runs],
        "persistedIssue": {
            "id": issue.get("id") if isinstance(issue, dict) else None,
            "status": issue.get("status") if isinstance(issue, dict) else None,
            "assigneeAgentId": issue.get("assigneeAgentId") if isinstance(issue, dict) else None,
        },
    }), indent=2, sort_keys=True))


def orphan_resume() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    agent_id = state["agents"]["developer"]
    issue_id = state["orphanIssueId"]
    configure_process_agent(client, agent_id, 1_000)
    client.request("POST", f"/api/agents/{agent_id}/resume")
    _, updated_issue = client.request(
        "PATCH", f"/api/issues/{issue_id}", {"status": "todo"}
    )
    _, wake = client.request(
        "POST",
        f"/api/agents/{agent_id}/wakeup",
        {
            "source": "assignment",
            "triggerDetail": "system",
            "reason": "issue_recovery_action_restored",
            "payload": {"issueId": issue_id, "mutation": "admission_orphan_resume"},
            "idempotencyKey": "milestone0-controller-orphan-resume-v3",
        },
        expected=(200, 202),
    )
    successor = find_issue_run(
        client,
        company_id,
        agent_id,
        issue_id,
        statuses={"succeeded"},
        timeout=45,
    )
    _, issue = client.request("GET", f"/api/issues/{issue_id}")
    client.request("POST", f"/api/agents/{agent_id}/pause")
    state["orphanSuccessorRunId"] = successor["id"]
    save_state(state)
    print(json.dumps(public({
        "updatedIssue": {
            "id": updated_issue.get("id") if isinstance(updated_issue, dict) else None,
            "status": updated_issue.get("status") if isinstance(updated_issue, dict) else None,
        },
        "wake": wake,
        "successorRun": summarize_run(successor),
        "persistedIssue": {
            "id": issue.get("id") if isinstance(issue, dict) else None,
            "status": issue.get("status") if isinstance(issue, dict) else None,
            "executionRunId": issue.get("executionRunId") if isinstance(issue, dict) else None,
        },
    }), indent=2, sort_keys=True))


def capability() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    developer_id = state["agents"]["developer"]
    connection_id = state["connectionId"]
    _, connection = client.request("GET", f"/api/tool-connections/{connection_id}")
    assert isinstance(connection, dict)
    try:
        _, application = client.request("GET", f"/api/tool-applications/{connection['applicationId']}")
    except ApiError as exc:
        if exc.status != 404:
            raise
        _, applications = client.request(
            "GET", f"/api/companies/{company_id}/tools/applications"
        )
        application_items = (
            applications.get("applications", []) if isinstance(applications, dict) else applications
        )
        application = next(
            item
            for item in application_items
            if isinstance(item, dict) and item.get("id") == connection["applicationId"]
        )
    assert isinstance(application, dict)
    application_key = application.get("applicationKey") or "opensearch-admission"
    allowed_tool = gateway_name(application_key, connection_id, "SearchIndexTool")
    denied_tool = gateway_name(application_key, connection_id, "MsearchTool")
    _, catalog_response = client.request(
        "GET", f"/api/tool-connections/{connection_id}/catalog"
    )
    catalog_items = (
        catalog_response.get("catalog", [])
        if isinstance(catalog_response, dict)
        else catalog_response
    )
    allowed_catalog_entry = next(
        item
        for item in catalog_items
        if isinstance(item, dict) and item.get("toolName") == "SearchIndexTool"
    )

    # Creating an MCP connection through the current board API also creates and
    # binds an app:<connection-id> company profile that grants every discovered
    # tool. Admission explicitly removes that convenience grant before proving
    # least privilege with the narrower agent profile below.
    _, existing_profiles = client.request(
        "GET", f"/api/companies/{company_id}/tools/profiles"
    )
    existing_profile_items = (
        existing_profiles.get("profiles", [])
        if isinstance(existing_profiles, dict)
        else existing_profiles
    )
    auto_profile = next(
        (
            item
            for item in existing_profile_items
            if isinstance(item, dict)
            and item.get("profileKey") == f"app:{connection_id}"
        ),
        None,
    )
    auto_profile_unbound: object = None
    if auto_profile is not None:
        has_company_binding = any(
            binding.get("targetType") == "company"
            and binding.get("targetId") == company_id
            for binding in auto_profile.get("bindings", [])
            if isinstance(binding, dict)
        )
        if has_company_binding:
            _, auto_profile_unbound = client.request(
                "POST",
                f"/api/companies/{company_id}/tools/profiles/{auto_profile['id']}/unbind",
                {"targetType": "company", "targetId": company_id},
            )

    _, profiles = client.request("GET", f"/api/companies/{company_id}/tools/profiles")
    profile_items = profiles.get("profiles", []) if isinstance(profiles, dict) else profiles
    profile = next(
        (
            item
            for item in profile_items
            if isinstance(item, dict)
            and item.get("profileKey") == "milestone0.opensearch.search-only"
        ),
        None,
    )
    if profile is None:
        _, profile = client.request(
            "POST",
            f"/api/companies/{company_id}/tools/profiles",
            {
                "profileKey": "milestone0.opensearch.search-only",
                "name": "Milestone 0 OpenSearch search only",
                "status": "active",
                "defaultAction": "deny",
                "entries": [
                    {
                        "selectorType": "catalog_entry",
                        "effect": "include",
                        "applicationId": application["id"],
                        "connectionId": connection_id,
                        "catalogEntryId": allowed_catalog_entry["id"],
                    }
                ],
            },
            expected=(201,),
        )
    assert isinstance(profile, dict)
    # Replace an earlier name-only fixture entry with the concrete catalog row.
    # Runtime MCP assignment resolves connections from concrete selectors; a
    # tool_name-only entry appears in policy output but does not produce a
    # deliverable named gateway in this Paperclip version.
    _, profile = client.request(
        "PATCH",
        f"/api/tool-profiles/{profile['id']}",
        {
            "entries": [
                {
                    "selectorType": "catalog_entry",
                    "effect": "include",
                    "applicationId": application["id"],
                    "connectionId": connection_id,
                    "catalogEntryId": allowed_catalog_entry["id"],
                }
            ]
        },
    )
    bindings = []
    for agent_id in (developer_id, state["agents"]["seam"]):
        try:
            _, binding = client.request(
                "POST",
                f"/api/companies/{company_id}/tools/profiles/{profile['id']}/bind",
                {"targetType": "agent", "targetId": agent_id, "priority": 100},
                expected=(201,),
            )
        except ApiError as exc:
            if exc.status != 409:
                raise
            binding = {"agentId": agent_id, "reused": True}
        bindings.append(binding)
    _, installs = client.request(
        "PUT",
        f"/api/tool-connections/{connection_id}/installs",
        {
            "installs": [
                {"targetType": "agent", "targetId": developer_id},
                {"targetType": "agent", "targetId": state["agents"]["seam"]},
            ]
        },
    )
    # Installation is a separate runtime-delivery requirement, but Paperclip
    # also auto-binds the generated full-application profile to each installed
    # agent. Remove those additive grants after install so the exact catalog
    # selector above remains the sole authority.
    _, profiles_after_install = client.request(
        "GET", f"/api/companies/{company_id}/tools/profiles"
    )
    profiles_after_install_items = (
        profiles_after_install.get("profiles", [])
        if isinstance(profiles_after_install, dict)
        else profiles_after_install
    )
    auto_profile_after_install = next(
        (
            item
            for item in profiles_after_install_items
            if isinstance(item, dict)
            and item.get("profileKey") == f"app:{connection_id}"
        ),
        None,
    )
    auto_agent_unbinds = []
    if auto_profile_after_install is not None:
        for agent_id in (developer_id, state["agents"]["seam"]):
            has_agent_binding = any(
                binding.get("targetType") == "agent"
                and binding.get("targetId") == agent_id
                for binding in auto_profile_after_install.get("bindings", [])
                if isinstance(binding, dict)
            )
            if has_agent_binding:
                _, unbound = client.request(
                    "POST",
                    f"/api/companies/{company_id}/tools/profiles/{auto_profile_after_install['id']}/unbind",
                    {"targetType": "agent", "targetId": agent_id},
                )
                auto_agent_unbinds.append(unbound)
    client.request("POST", f"/api/tool-connections/{connection_id}/health-check")
    _, effective = client.request(
        "GET", f"/api/companies/{company_id}/tools/profiles/effective/agents/{developer_id}"
    )

    process_config = {
        "command": "node",
        "args": ["/milestone0/finite-agent.mjs"],
        "cwd": "/paperclip",
        "timeoutSec": 180,
        "env": {
            "AIF_M0_OUTPUT_DIR": "/paperclip/milestone0-runs",
            "AIF_M0_ALLOWED_TOOL": allowed_tool,
            "AIF_M0_ALLOWED_TOOL_ARGS": json.dumps(
                {
                    "index": "aif_docs_current",
                    "query_dsl": {
                        "query": {
                            "bool": {
                                "filter": [
                                    {"term": {"project_id": "ai-factory"}},
                                    {"term": {"status": "current"}},
                                ]
                            }
                        }
                    },
                    "size": 2,
                },
                separators=(",", ":"),
            ),
            "AIF_M0_DENIED_TOOL": denied_tool,
        },
    }
    client.request(
        "PATCH",
        f"/api/agents/{developer_id}",
        {"adapterConfig": process_config, "replaceAdapterConfig": True},
    )
    _, issue = client.request(
        "POST",
        f"/api/companies/{company_id}/issues",
        {
            "title": "Milestone 0 capability enforcement",
            "description": "Admission-only tool gateway boundary probe.",
            "status": "todo",
            "assigneeAgentId": developer_id,
            "idempotencyKey": "milestone0-capability-enforcement-v1",
        },
        expected=(200, 201),
    )
    assert isinstance(issue, dict)
    client.request("POST", f"/api/agents/{developer_id}/resume")
    _, invoked = client.request(
        "POST", f"/api/agents/{developer_id}/heartbeat/invoke", expected=(200, 202)
    )
    assert isinstance(invoked, dict)
    run_id = invoked.get("runId") or invoked.get("id")
    if not isinstance(run_id, str):
        raise RuntimeError(f"heartbeat invoke returned no run id: {invoked}")
    run = wait_run(client, run_id)
    client.request("POST", f"/api/agents/{developer_id}/pause")

    seam_id = state["agents"]["seam"]
    seam_config = {
        "allowedTool": allowed_tool,
        "allowedToolArgs": {
            "index": "aif_docs_current",
            "query_dsl": {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"project_id": "ai-factory"}},
                            {"term": {"status": "current"}},
                        ]
                    }
                }
            },
            "size": 2,
        },
        "deniedTool": denied_tool,
    }
    client.request(
        "PATCH",
        f"/api/agents/{seam_id}",
        {"adapterConfig": seam_config, "replaceAdapterConfig": True},
    )
    client.request("POST", f"/api/agents/{seam_id}/resume")
    _, seam_invoked = client.request(
        "POST", f"/api/agents/{seam_id}/heartbeat/invoke", expected=(200, 202)
    )
    assert isinstance(seam_invoked, dict)
    seam_run_id = seam_invoked.get("runId") or seam_invoked.get("id")
    if not isinstance(seam_run_id, str):
        raise RuntimeError(f"seam heartbeat invoke returned no run id: {seam_invoked}")
    seam_run = wait_run(client, seam_run_id)
    client.request("POST", f"/api/agents/{seam_id}/pause")

    state.update(
        {
            "capabilityProfileId": profile["id"],
            "capabilityIssueId": issue["id"],
            "capabilityRunId": run_id,
            "seamRunId": seam_run_id,
            "allowedTool": allowed_tool,
            "deniedTool": denied_tool,
        }
    )
    save_state(state)
    print(
        json.dumps(
            public(
                {
                    "applicationKey": application_key,
                    "autoProfileUnbound": auto_profile_unbound,
                    "allowedTool": allowed_tool,
                    "deniedTool": denied_tool,
                    "profile": profile,
                    "bindings": bindings,
                    "installs": installs,
                    "autoAgentProfileUnbinds": auto_agent_unbinds,
                    "effective": effective,
                    "issueId": issue["id"],
                    "processAdapterRun": summarize_run(run),
                    "seamAdapterRun": summarize_run(seam_run),
                }
            ),
            indent=2,
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "setup",
            "capability",
            "process-crash",
            "process-reconcile",
            "orphan-prepare",
            "orphan-report",
            "orphan-resume",
        ],
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:13100")
    args = parser.parse_args()
    if args.action == "setup":
        setup(args.base_url)
    elif args.action == "capability":
        capability()
    elif args.action == "process-crash":
        process_crash()
    elif args.action == "process-reconcile":
        process_reconcile()
    elif args.action == "orphan-prepare":
        orphan_prepare()
    elif args.action == "orphan-report":
        orphan_report()
    elif args.action == "orphan-resume":
        orphan_resume()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1)
