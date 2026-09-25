#!/usr/bin/env python3
"""Live Paperclip admission driver. Stores secrets/results only under ignored .milestone0."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import http.cookiejar
import json
import os
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path(
    os.environ.get("AIF_M0_PAPERCLIP_STATE_PATH", ROOT / ".milestone0" / "paperclip-state.json")
)
TEST_ROUND = os.environ.get("AIF_M0_PAPERCLIP_TEST_ROUND", "m0b-host-lease-v3")
CONTAINER_NAME = os.environ.get("AIF_M0_PAPERCLIP_CONTAINER", "aif-m0-paperclip-paperclip-1")


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
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if override_url := os.environ.get("AIF_M0_PAPERCLIP_BASE_URL"):
        state["baseUrl"] = override_url
    return state


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


def read_container_bytes(path: str) -> bytes:
    if not path.startswith("/paperclip/"):
        raise RuntimeError(f"refusing to read an unexpected container path: {path}")
    return subprocess.check_output(
        ["docker", "exec", CONTAINER_NAME, "cat", path]
    )


def assert_exact_search_profile(effective: object, profile_id: str, connection_id: str) -> None:
    if not isinstance(effective, dict):
        raise RuntimeError("effective capability response is not an object")
    profile_ids = {
        profile.get("id")
        for profile in effective.get("profiles", [])
        if isinstance(profile, dict)
    }
    if profile_ids != {profile_id}:
        raise RuntimeError(f"unexpected effective profiles: {sorted(str(item) for item in profile_ids)}")
    if effective.get("allowedToolNames") != ["SearchIndexTool"]:
        raise RuntimeError(
            f"effective tool set is not exact search-only: {effective.get('allowedToolNames')}"
        )
    installed_ids = {
        item.get("id") or item.get("connectionId")
        for item in effective.get("installedConnections", [])
        if isinstance(item, dict)
    }
    if connection_id not in installed_ids:
        raise RuntimeError(f"OpenSearch connection is not installed: {sorted(str(item) for item in installed_ids)}")


def find_issue_run(
    client: Client,
    company_id: str,
    agent_id: str,
    issue_id: str,
    *,
    statuses: set[str] | None = None,
    exclude_ids: set[str] | None = None,
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
            if run.get("id") not in (exclude_ids or set())
            and (
                run.get("nativeIssueId") == issue_id
                or (
                    isinstance(run.get("contextSnapshot"), dict)
                    and run["contextSnapshot"].get("issueId") == issue_id
                )
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
            "title": f"Milestone 0 child loss {TEST_ROUND}",
            "description": "Admission-only process failure and task continuity probe.",
            "status": "todo",
            "assigneeAgentId": agent_id,
            "idempotencyKey": f"{TEST_ROUND}-process-crash",
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
            "idempotencyKey": f"{TEST_ROUND}-process-crash-wake",
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
            CONTAINER_NAME,
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
    _, runs_before = client.request(
        "GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100"
    )
    previous_run_ids = {item["id"] for item in runs_before if isinstance(item, dict)} if isinstance(runs_before, list) else set()
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
        exclude_ids=previous_run_ids,
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
    client.request("PATCH", f"/api/issues/{issue['id']}", {"status": "cancelled"})
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
    configure_process_agent(client, agent_id, 300_000)
    client.request("POST", f"/api/agents/{agent_id}/pause", expected=(200,))
    _, issue = client.request(
        "POST",
        f"/api/companies/{company_id}/issues",
        {
            "title": f"Milestone 0 controller loss {TEST_ROUND}",
            "description": "Admission-only controller crash, orphan lease, and durable retry probe.",
            "status": "todo",
            "assigneeAgentId": agent_id,
            "idempotencyKey": f"{TEST_ROUND}-controller-orphan",
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
            "idempotencyKey": f"{TEST_ROUND}-controller-orphan-wake",
        },
        expected=(200, 202),
    )
    assert isinstance(wake, dict)
    run_id = wake.get("runId") or wake.get("id")
    if not isinstance(run_id, str):
        raise RuntimeError(f"orphan wake returned no run id: {wake}")
    run = wait_run_process(client, run_id)
    # The already-spawned child keeps its captured five-minute delay. A recovered
    # successor reads this 1s configuration after the controller restarts.
    configure_process_agent(client, agent_id, 1_000)
    state.pop("orphanSuccessorRunId", None)
    state.pop("orphanRecoverySuccessorRunId", None)
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
    _, runs_before = client.request(
        "GET", f"/api/companies/{company_id}/heartbeat-runs?agentId={agent_id}&limit=100"
    )
    preexisting_issue_run_ids = {
        item["id"]
        for item in runs_before
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and (
            item.get("nativeIssueId") == state["orphanIssueId"]
            or (
                isinstance(item.get("contextSnapshot"), dict)
                and item["contextSnapshot"].get("issueId") == state["orphanIssueId"]
            )
        )
    } if isinstance(runs_before, list) else set()
    if isinstance(active_recovery, dict):
        evidence = active_recovery.get("evidence")
        recovery_run_id = (
            evidence.get("runId")
            if isinstance(evidence, dict) and isinstance(evidence.get("runId"), str)
            else original_run_id
        )
        _, resolved_recovery = client.request(
            "POST",
            f"/api/issues/{state['orphanIssueId']}/recovery-actions/resolve",
            {
                "actionId": active_recovery["id"],
                "outcome": "restored",
                "sourceIssueStatus": "todo",
                "resolutionNote": "Admission operator verified the killed controller and its child are stopped; retry is safe.",
                "executionReconciliation": {
                    "runId": recovery_run_id,
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
            exclude_ids=preexisting_issue_run_ids,
            timeout=90,
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
    if successor:
        state["orphanRecoverySuccessorRunId"] = successor["id"]
        save_state(state)
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
            "idempotencyKey": f"{TEST_ROUND}-controller-orphan-resume",
        },
        expected=(200, 202),
    )
    assert isinstance(wake, dict)
    successor_run_id = wake.get("runId") or wake.get("id") or wake.get("executionRunId")
    if not isinstance(successor_run_id, str):
        raise RuntimeError(f"explicit resume returned no run id: {wake}")
    successor = wait_run(client, successor_run_id, timeout=90)
    if successor.get("status") != "succeeded":
        raise RuntimeError(f"explicit resume did not succeed: {summarize_run(successor)}")
    _, issue = client.request("GET", f"/api/issues/{issue_id}")
    client.request("PATCH", f"/api/issues/{issue_id}", {"status": "cancelled"})
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


def locking() -> None:
    state, client = state_client()
    agent_ids = [state["agents"]["developer"], state["agents"]["reviewer"]]
    for agent_id in agent_ids:
        client.request("POST", f"/api/agents/{agent_id}/pause")
    _, issue = client.request("POST", f"/api/companies/{state['companyId']}/issues", {
        "title": f"Milestone 0 atomic checkout {TEST_ROUND}",
        "status": "todo",
        "idempotencyKey": f"{TEST_ROUND}-atomic-checkout",
    }, expected=(200, 201))
    assert isinstance(issue, dict)

    def checkout(agent_id: str) -> tuple[int, object]:
        contender = Client(state["baseUrl"], state["boardApiKey"])
        return contender.request("POST", f"/api/issues/{issue['id']}/checkout", {
            "agentId": agent_id, "expectedStatuses": ["todo"],
        }, expected=(200, 409))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(checkout, agent_ids))
    if sorted(status for status, _ in outcomes) != [200, 409]:
        raise RuntimeError(f"atomic checkout did not select exactly one owner: {outcomes}")
    _, persisted = client.request("GET", f"/api/issues/{issue['id']}")
    winner = next(body for status, body in outcomes if status == 200)
    if not isinstance(persisted, dict) or not isinstance(winner, dict) or persisted.get("assigneeAgentId") != winner.get("assigneeAgentId"):
        raise RuntimeError("persisted checkout owner differs from the sole successful claimant")
    client.request("PATCH", f"/api/issues/{issue['id']}", {"status": "cancelled"})
    print(json.dumps(public({"issueId": issue["id"], "claimStatuses": [status for status, _ in outcomes],
                            "soleOwnerAgentId": persisted["assigneeAgentId"]}), indent=2, sort_keys=True))


def recovery_report() -> None:
    state, client = state_client()
    run_ids = [state[key] for key in (
        "processCrashRunId", "processCrashSuccessorRunId", "orphanRunId", "orphanSuccessorRunId", "orphanRecoverySuccessorRunId"
    ) if isinstance(state.get(key), str)]
    run_ids.extend(state.get("recoveryScenarioRunIds", []))
    tracked_ids = set(run_ids)
    issue_ids = {state[key] for key in ("processCrashIssueId", "orphanIssueId")}
    _, recent_runs = client.request("GET", f"/api/companies/{state['companyId']}/heartbeat-runs?limit=100")
    if not isinstance(recent_runs, list) or len(recent_runs) >= 100:
        raise RuntimeError("task-writer assertion requires an untruncated fixture run inventory")
    for issue_id in issue_ids:
        issue_runs = [item for item in recent_runs if isinstance(item, dict)
                      and (item.get("nativeIssueId") == issue_id
                           or (item.get("contextSnapshot") or {}).get("issueId") == issue_id)]
        intervals = sorted((datetime.fromisoformat(item["startedAt"].replace("Z", "+00:00")),
                            datetime.fromisoformat(item["finishedAt"].replace("Z", "+00:00")))
                           for item in issue_runs if item.get("startedAt") and item.get("finishedAt"))
        if any(current[0] < previous[1] for previous, current in zip(intervals, intervals[1:])):
            raise RuntimeError(f"overlapping task execution intervals: {issue_id}")
        run_ids.extend(item["id"] for item in issue_runs)
    run_ids = list(dict.fromkeys(run_ids))
    releases: dict[str, str] = {}
    report: list[dict] = []
    deadline = time.monotonic() + 360
    for run_id in run_ids:
        _, run = client.request("GET", f"/api/heartbeat-runs/{run_id}")
        if not isinstance(run, dict) or run.get("status") not in {"succeeded", "failed", "cancelled", "timed_out", "interrupted"}:
            raise RuntimeError(f"recovery left a nonterminal run: {run}")
        context = run.get("contextSnapshot", {})
        lease_id = context.get("paperclipEnvironment", {}).get("leaseId")
        if not isinstance(lease_id, str):
            if run_id not in tracked_ids and run.get("status") == "cancelled":
                report.append({"runId": run_id, "runStatus": "cancelled", "noLeaseAcquired": True})
                continue
            raise RuntimeError(f"run {run_id} has no durable environment lease identity")
        while True:
            _, lease = client.request("GET", f"/api/environment-leases/{lease_id}")
            if isinstance(lease, dict) and lease.get("releasedAt") and lease.get("status") not in {"active", "pending_cleanup"}:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(f"terminal run lease did not eventually release: {lease}")
            time.sleep(0.5)
        releases[lease_id] = lease["releasedAt"]
        report.append({"runId": run_id, "runStatus": run["status"], "leaseId": lease_id,
                       "leaseStatus": lease["status"], "releasedAt": lease["releasedAt"]})
    previous = state.get("verifiedLeaseReleases")
    if isinstance(previous, dict) and any(previous.get(key) not in {None, value} for key, value in releases.items()):
        raise RuntimeError(f"repeated recovery changed a release receipt: before={previous} after={releases}")
    for issue_key in ("processCrashIssueId", "orphanIssueId"):
        _, issue = client.request("GET", f"/api/issues/{state[issue_key]}")
        if not isinstance(issue, dict) or issue.get("executionRunId") or issue.get("checkoutRunId"):
            raise RuntimeError(f"terminal recovery left issue locks: {issue}")
        live = [item["id"] for item in recent_runs if isinstance(item, dict)
                and item.get("status") in {"queued", "running"}
                and (item.get("nativeIssueId") == state[issue_key]
                     or (item.get("contextSnapshot") or {}).get("issueId") == state[issue_key])]
        if live:
            raise RuntimeError(f"recovery left live task writers: {live}")
    state["verifiedLeaseReleases"] = releases
    state["recoveryScenarioRunIds"] = run_ids
    save_state(state)
    print(json.dumps(public({"allSourceAndSuccessorLeasesReleased": report,
                            "releaseReceiptsUnchanged": isinstance(previous, dict),
                            "issueLocksCleared": True, "noLiveTaskWriters": True,
                            "taskExecutionIntervalsDoNotOverlap": True}), indent=2, sort_keys=True))


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
    assert_exact_search_profile(effective, profile["id"], connection_id)

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
            "title": "Milestone 0B capability enforcement",
            "description": "Admission-only tool gateway boundary probe.",
            "status": "todo",
            "assigneeAgentId": developer_id,
            "idempotencyKey": f"{TEST_ROUND}-capability-enforcement",
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
    client.request("PATCH", f"/api/issues/{issue['id']}", {"status": "cancelled"})
    client.request("POST", f"/api/agents/{developer_id}/pause")

    seam_id = state["agents"]["seam"]
    client.request("POST", "/api/adapters/aif_context_seam_poc/reload")
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
    if seam_run.get("status") != "succeeded":
        raise RuntimeError(f"capability probe adapter failed: {summarize_run(seam_run)}")
    seam_result = seam_run.get("resultJson")
    probes = seam_result.get("assignedMcp") if isinstance(seam_result, dict) else None
    if not isinstance(probes, list) or len(probes) != 1:
        raise RuntimeError(f"capability probe did not receive one governed MCP server: {probes}")
    if probes[0].get("allowed", {}).get("status") != 200:
        raise RuntimeError(f"assigned search failed: {probes[0]}")
    denied = probes[0].get("denied", {})
    if denied.get("status") != 403 or denied.get("reasonCode") != "deny_default":
        raise RuntimeError(f"unassigned msearch was not denied exactly: {denied}")

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


def pre_run_enrichment() -> None:
    state, client = state_client()
    company_id = state["companyId"]
    developer_id = state["agents"]["developer"]
    connection_id = state["connectionId"]
    profile_id = state.get("capabilityProfileId")
    allowed_tool = state.get("allowedTool")
    denied_tool = state.get("deniedTool")
    if not all(isinstance(value, str) for value in (profile_id, allowed_tool, denied_tool)):
        raise RuntimeError("run the capability action before the enrichment action")

    try:
        _, installed_plugin = client.request(
            "POST",
            "/api/plugins/install",
            {
                "packageName": "/milestone0/context-enricher-plugin",
                "isLocalPath": True,
            },
            expected=(200,),
        )
    except ApiError as exc:
        if exc.status != 400 or "already installed" not in str(exc.body).lower():
            raise
        _, plugin_response = client.request("GET", "/api/plugins")
        plugin_items = (
            plugin_response.get("plugins", [])
            if isinstance(plugin_response, dict)
            else plugin_response
        )
        installed_plugin = next(
            item
            for item in plugin_items
            if isinstance(item, dict)
            and item.get("pluginKey") == "ai-factory.milestone0-context-enricher"
        )
    if not isinstance(installed_plugin, dict) or installed_plugin.get("status") != "ready":
        raise RuntimeError(f"context enricher plugin is not ready: {installed_plugin}")
    client.request(
        "PUT",
        f"/api/plugins/{installed_plugin['id']}/companies/{company_id}/run-context-enrichment",
        {"enabled": True},
        expected=(200,),
    )

    _, effective = client.request(
        "GET", f"/api/companies/{company_id}/tools/profiles/effective/agents/{developer_id}"
    )
    assert_exact_search_profile(effective, profile_id, connection_id)

    process_config = {
        "command": "node",
        "args": ["/milestone0/finite-agent.mjs"],
        "cwd": "/paperclip",
        "timeoutSec": 180,
        "graceSec": 2,
        "env": {
            "AIF_M0_EXPECT_ENRICHMENT": "1",
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
    _, agent = client.request("GET", f"/api/agents/{developer_id}")
    if not isinstance(agent, dict) or agent.get("adapterType") != "process":
        raise RuntimeError(f"native adapter selection changed: {agent}")

    _, issue = client.request(
        "POST",
        f"/api/companies/{company_id}/issues",
        {
            "title": f"Milestone 0 pre-run enrichment {TEST_ROUND}",
            "description": "Admission-only deterministic pre-run enrichment and native delegation probe.",
            "status": "todo",
            "assigneeAgentId": developer_id,
            "idempotencyKey": f"{TEST_ROUND}-pre-run-enrichment",
        },
        expected=(200, 201),
    )
    assert isinstance(issue, dict)
    client.request("POST", f"/api/agents/{developer_id}/resume")
    _, invoked = client.request(
        "POST",
        f"/api/agents/{developer_id}/wakeup",
        {
            "source": "assignment",
            "triggerDetail": "system",
            "reason": "issue_assigned",
            "payload": {"issueId": issue["id"], "mutation": "admission_pre_run_enrichment"},
            "idempotencyKey": f"{TEST_ROUND}-pre-run-enrichment-wake",
        },
        expected=(200, 202),
    )
    assert isinstance(invoked, dict)
    run_id = invoked.get("runId") or invoked.get("id")
    if isinstance(run_id, str):
        run = wait_run(client, run_id, timeout=120)
    else:
        run = find_issue_run(
            client,
            company_id,
            developer_id,
            issue["id"],
            statuses={"succeeded"},
            timeout=15,
        )
        run_id = run["id"]
    client.request("PATCH", f"/api/issues/{issue['id']}", {"status": "cancelled"})
    client.request("POST", f"/api/agents/{developer_id}/pause")
    _, run_detail = client.request("GET", f"/api/heartbeat-runs/{run_id}")
    if not isinstance(run_detail, dict):
        raise RuntimeError("enrichment run detail is not an object")
    run = run_detail
    if run.get("status") != "succeeded":
        raise RuntimeError(f"native adapter did not complete normally: {summarize_run(run)}")

    context = run.get("contextSnapshot")
    enrichment = context.get("paperclipRunContextEnrichment") if isinstance(context, dict) else None
    entries = enrichment.get("entries") if isinstance(enrichment, dict) else None
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise RuntimeError(f"durable enrichment record is missing or ambiguous: {enrichment}")
    entry = entries[0]
    artifact = entry.get("artifact") if isinstance(entry.get("artifact"), dict) else {}
    artifact_ref = artifact.get("ref")
    artifact_digest = artifact.get("sha256")
    if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:///paperclip/"):
        raise RuntimeError(f"unexpected artifact reference: {artifact_ref}")
    if not isinstance(artifact_digest, str):
        raise RuntimeError("artifact digest is missing")
    artifact_path = artifact_ref.removeprefix("file://")
    artifact_bytes = read_container_bytes(artifact_path)
    actual_digest = hashlib.sha256(artifact_bytes).hexdigest()
    if actual_digest != artifact_digest:
        raise RuntimeError(f"artifact digest mismatch: durable={artifact_digest} actual={actual_digest}")
    artifact_body = json.loads(artifact_bytes)
    if artifact_body.get("runId") != run_id or artifact_body.get("adapterType") != "process":
        raise RuntimeError(f"artifact does not identify the delegated run/adapter: {artifact_body}")

    assigned = artifact_body.get("assignedMcp")
    if not isinstance(assigned, list) or len(assigned) != 1:
        raise RuntimeError(f"enricher did not receive the exact governed MCP surface: {assigned}")
    probe = assigned[0]
    listed_names = probe.get("listed", {}).get("toolNames")
    expected_context_tools = {
        "paperclip_list_resources",
        "paperclip_read_resource",
        "paperclip_list_prompts",
        "paperclip_get_prompt",
    }
    if not isinstance(listed_names, list):
        raise RuntimeError(f"enricher MCP list is missing: {probe}")
    external_names = set(listed_names) - expected_context_tools
    if external_names != {allowed_tool} or denied_tool in listed_names:
        raise RuntimeError(f"enricher external MCP grant is not exact search-only: {probe}")
    if probe.get("allowed", {}).get("status") != 200 or probe.get("allowed", {}).get("isError") is not False:
        raise RuntimeError(f"enricher allowed call failed: {probe.get('allowed')}")
    denied = probe.get("denied", {})
    if denied.get("status") != 403 or denied.get("reasonCode") != "deny_default":
        raise RuntimeError(f"enricher broad MCP call was not denied: {denied}")

    native_record = json.loads(read_container_bytes(f"/paperclip/milestone0-runs/{run_id}.json"))
    if native_record.get("runId") != run_id or native_record.get("agentId") != developer_id:
        raise RuntimeError(f"native adapter did not execute as the same run: {native_record}")
    if native_record.get("consumedContext") != {"ref": artifact_ref, "sha256": artifact_digest}:
        raise RuntimeError("native fixture did not consume the exact durably identified context artifact")

    state.update(
        {
            "contextEnricherPluginId": installed_plugin["id"],
            "enrichmentIssueId": issue["id"],
            "enrichmentRunId": run_id,
            "enrichmentArtifactRef": artifact_ref,
            "enrichmentArtifactDigest": artifact_digest,
        }
    )
    save_state(state)
    print(
        json.dumps(
            public(
                {
                    "plugin": installed_plugin,
                    "effective": effective,
                    "selectedAdapter": agent.get("adapterType"),
                    "run": summarize_run(run),
                    "durableEnrichment": enrichment,
                    "artifactDigestVerified": actual_digest,
                    "artifact": artifact_body,
                    "nativeAdapterRecord": native_record,
                }
            ),
            indent=2,
            sort_keys=True,
        )
    )


def enrichment_report() -> None:
    state, client = state_client()
    run_id = state.get("enrichmentRunId")
    expected_ref = state.get("enrichmentArtifactRef")
    expected_digest = state.get("enrichmentArtifactDigest")
    if not all(isinstance(value, str) for value in (run_id, expected_ref, expected_digest)):
        raise RuntimeError("run pre-run-enrichment first")
    _, run = client.request("GET", f"/api/heartbeat-runs/{run_id}")
    if not isinstance(run, dict):
        raise RuntimeError("persisted run is not an object")
    context = run.get("contextSnapshot")
    enrichment = context.get("paperclipRunContextEnrichment") if isinstance(context, dict) else None
    entries = enrichment.get("entries") if isinstance(enrichment, dict) else None
    artifact = entries[0].get("artifact") if isinstance(entries, list) and len(entries) == 1 else None
    if not isinstance(artifact, dict):
        raise RuntimeError(f"persisted enrichment is missing after restart: {enrichment}")
    if artifact.get("ref") != expected_ref or artifact.get("sha256") != expected_digest:
        raise RuntimeError(f"persisted artifact identity changed after restart: {artifact}")
    artifact_bytes = read_container_bytes(expected_ref.removeprefix("file://"))
    actual_digest = hashlib.sha256(artifact_bytes).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError("persisted artifact content no longer matches the durable digest")
    print(
        json.dumps(
            public(
                {
                    "run": summarize_run(run),
                    "durableEnrichment": enrichment,
                    "artifactDigestVerifiedAfterRestart": actual_digest,
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
            "locking",
            "recovery-report",
            "pre-run-enrichment",
            "enrichment-report",
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
    elif args.action == "locking":
        locking()
    elif args.action == "recovery-report":
        recovery_report()
    elif args.action == "pre-run-enrichment":
        pre_run_enrichment()
    elif args.action == "enrichment-report":
        enrichment_report()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1)
