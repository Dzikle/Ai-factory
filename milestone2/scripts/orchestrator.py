"""Persist a native Orchestrator plan and hand one coding task to Paperclip."""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from uuid import UUID

# Invoked with python -I and an absolute root-owned path. The assigned project
# and inherited PYTHONPATH must never control imports of this run-scoped helper.
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from milestone0.scripts.paperclip_admission import ApiError
from milestone1.paperclip_policy import engineering_execution_policy
from milestone2.scripts.assistant_reply import RunClient


MAX_SUMMARY = 5000
MAX_ACCEPTANCE_ITEMS = 30
MAX_ACCEPTANCE_TEXT = 2000
MAX_PLAN_BYTES = 32_000
MAX_ANSWER = 8000
TIERS = {"free": 0, "subscription": 1, "paid": 2}


def _uuid(value, name):
    try:
        parsed = str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{name} must be a UUID") from exc
    if parsed != value.lower():
        raise ValueError(f"{name} must be a canonical UUID")
    return parsed


def _text(value, name, limit, *, optional=False):
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > limit:
        raise ValueError(f"{name} must contain 1–{limit} UTF-8 bytes")
    return value.strip()


def _validate_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object")
    allowed = {"kind", "summary", "acceptance", "risk", "ux", "answer", "modelProfile"}
    if set(plan) - allowed:
        raise ValueError("Plan contains unsupported fields")
    if plan.get("kind") not in {"analysis", "coding"}:
        raise ValueError("Plan kind must be analysis or coding")
    summary = _text(plan.get("summary"), "summary", MAX_SUMMARY)
    if not isinstance(plan.get("acceptance"), list) or len(plan["acceptance"]) > MAX_ACCEPTANCE_ITEMS:
        raise ValueError("acceptance must be a list of at most 30 bounded strings")
    acceptance = [_text(item, "acceptance item", MAX_ACCEPTANCE_TEXT) for item in plan["acceptance"]]
    if plan.get("risk") not in {"low", "normal", "high"}:
        raise ValueError("risk must be low, normal, or high")
    if not isinstance(plan.get("ux"), bool):
        raise ValueError("ux must be a boolean")
    answer = _text(plan.get("answer"), "answer", MAX_ANSWER, optional=True)
    profile = plan.get("modelProfile")
    if profile is not None:
        profile = _text(profile, "modelProfile", 128)
    if plan["kind"] == "analysis" and answer is None:
        raise ValueError("analysis plans require an answer")
    cleaned = {"kind": plan["kind"], "summary": summary, "acceptance": acceptance,
               "risk": plan["risk"], "ux": plan["ux"]}
    if answer is not None:
        cleaned["answer"] = answer
    if profile is not None:
        cleaned["modelProfile"] = profile
    if len(_canonical(cleaned).encode("utf-8")) > MAX_PLAN_BYTES:
        raise ValueError("Plan exceeds the total size limit")
    return cleaned


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _registry(bindings, company_id, project_id):
    if not isinstance(bindings, dict):
        raise ValueError("Bindings registry must be an object")
    if _uuid(bindings.get("companyId"), "registry companyId") != company_id:
        raise ValueError("Bindings belong to another company")
    owner = _text(bindings.get("ownerUserId"), "ownerUserId", 255)
    projects = bindings.get("projects")
    project = projects.get(project_id) if isinstance(projects, dict) else None
    if not isinstance(project, dict):
        raise ValueError("Project is missing from bindings registry")
    roles = {key: _uuid(project.get(key), key) for key in
             ("orchestratorAgentId", "developerAgentId", "validatorAgentId", "reviewerAgentId")}
    if project.get("qaAgentId"):
        roles["qaAgentId"] = _uuid(project["qaAgentId"], "qaAgentId")
    return owner, project, roles


def _get_agents(client, company_id, agent_ids):
    agents = client.request("GET", f"/api/companies/{company_id}/agents")
    if not isinstance(agents, list):
        raise ValueError("Paperclip returned a malformed company agent list")
    by_id = {}
    for agent in agents:
        if isinstance(agent, dict) and agent.get("id") in agent_ids:
            agent_id = agent["id"]
            if agent_id in by_id:
                raise ValueError("Paperclip returned duplicate agent identities")
            by_id[agent_id] = agent
    for agent_id in agent_ids:
        agent = by_id.get(agent_id)
        if not isinstance(agent, dict) or agent.get("companyId") != company_id:
            raise ValueError("A configured workflow agent is missing or belongs to another company")
        if agent.get("status") not in {"idle", "running"}:
            raise ValueError(f"Configured workflow agent {agent_id} is not active")
    return by_id


def _select_profile(project, plan, agents):
    profiles = project.get("profiles", [])
    if profiles is None:
        profiles = []
    if not isinstance(profiles, list):
        raise ValueError("profiles must be a list")
    valid = []
    seen = set()
    for row in profiles:
        if not isinstance(row, dict) or row.get("qualified") is not True:
            continue
        if row.get("tier") not in TIERS:
            continue
        try:
            agent_id = _uuid(row.get("agentId"), "profile agentId")
            profile_id = _text(row.get("id"), "profile id", 128)
            model = _text(row.get("model"), "profile model", 256)
            adapter = _text(row.get("adapterType"), "profile adapterType", 64)
        except ValueError:
            continue
        agent = agents.get(agent_id, {})
        if (profile_id in seen or agent.get("status") not in {"idle", "running"}
                or agent.get("adapterType") != adapter):
            continue
        seen.add(profile_id)
        valid.append({"id": profile_id, "agentId": agent_id, "model": model,
                      "adapterType": adapter, "tier": row["tier"]})
    if not valid:
        raise ValueError("No qualified project developer profile is available")
    if plan["risk"] == "high" and not any(row["tier"] == "subscription" for row in valid):
        raise ValueError("High-risk plans require a qualified subscription profile")
    requested = plan.get("modelProfile")
    if requested is not None:
        choices = [row for row in valid if row["id"] == requested]
        if not choices:
            raise ValueError("Requested modelProfile is not a qualified project developer profile")
        if plan["risk"] == "high" and any(row["tier"] == "subscription" for row in valid) \
                and choices[0]["tier"] == "free":
            raise ValueError("High-risk plans must use a configured subscription profile")
        selected = choices[0]
        return selected, "requested qualified profile; high-risk tier constraint satisfied"
    tier_order = {"free": 0, "subscription": 1, "paid": 2}
    if plan["risk"] == "high" and any(row["tier"] == "subscription" for row in valid):
        selected = min((row for row in valid if row["tier"] == "subscription"), key=lambda row: row["id"])
        reason = "high-risk policy selected the configured subscription profile"
    else:
        selected = min(valid, key=lambda row: (tier_order[row["tier"]], row["id"]))
        reason = "qualified free-first policy"
    return selected, reason


def _document(client, issue_id, expected):
    path = f"/api/issues/{issue_id}/documents/plan"
    try:
        current = client.request("GET", path)
    except ApiError as exc:
        if exc.status != 404:
            raise
        current = None
    except HTTPError as exc:
        if exc.code != 404:
            raise
        current = None
    canonical = _canonical(expected)
    if current is not None:
        if not isinstance(current, dict) or not isinstance(current.get("body"), str) \
                or not current.get("latestRevisionId"):
            raise ValueError("Existing plan document is malformed; refusing to overwrite")
        try:
            existing = json.loads(current["body"])
        except ValueError as exc:
            raise ValueError("Existing plan document is malformed; refusing to overwrite") from exc
        if _canonical(existing) != canonical:
            raise ValueError("Existing plan conflicts with this run; refusing to overwrite")
        return current["latestRevisionId"], False
    payload = {"title": "plan", "format": "markdown", "body": canonical}
    try:
        created = client.request("PUT", path, payload)
    except (ApiError, ValueError) as exc:
        raise ValueError("Plan document create was not confirmed; inspect Paperclip before retrying") from exc
    if not isinstance(created, dict) or not created.get("latestRevisionId"):
        raise ValueError("Plan document create did not return latestRevisionId")
    return created["latestRevisionId"], True


def execute(client, context, bindings, plan):
    """Validate the active Orchestrator run, persist its plan, then answer or hand off."""
    context = {key: _uuid(context.get(key), key) for key in ("taskId", "agentId", "companyId", "runId")}
    plan = _validate_plan(plan)
    issue = client.request("GET", f"/api/issues/{context['taskId']}")
    if not isinstance(issue, dict) or issue.get("id") != context["taskId"]:
        raise ValueError("Paperclip returned a malformed issue")
    if issue.get("companyId") != context["companyId"]:
        raise ValueError("Issue belongs to another company")
    owner, project, roles = _registry(bindings, context["companyId"], issue.get("projectId"))
    if roles["orchestratorAgentId"] != context["agentId"]:
        raise ValueError("This run is not assigned to the project's Orchestrator")

    existing_plan, existing_revision = _read_plan(client, context["taskId"])
    profile = profile_reason = None
    if plan["kind"] == "coding":
        if issue.get("workMode") not in {None, "standard"}:
            raise ValueError("Ask and planning issues cannot be handed off for implementation")
        all_agents = client.request("GET", f"/api/companies/{context['companyId']}/agents")
        if not isinstance(all_agents, list):
            raise ValueError("Paperclip returned a malformed company agent list")
        eligible_agents = {row["id"]: row for row in all_agents if isinstance(row, dict)
                           and row.get("companyId") == context["companyId"] and row.get("id")}
        if existing_plan is not None:
            profile = existing_plan.get("selectedProfile")
            profile_reason = existing_plan.get("selectionRationale")
            if not isinstance(profile, dict) or not profile.get("id"):
                raise ValueError("Persisted plan has no qualified developer profile")
            current_profile, _ = _select_profile(project, {**plan, "modelProfile": profile["id"]}, eligible_agents)
            if current_profile != profile:
                raise ValueError("Persisted qualified profile binding has changed")
        else:
            profile, profile_reason = _select_profile(project, plan, eligible_agents)
        developer = profile["agentId"] if profile else roles["developerAgentId"]
        qa = roles.get("qaAgentId") if plan["ux"] else None
        if plan["ux"] and qa is None:
            raise ValueError("User-facing coding requires a configured QA binding")
        policy = engineering_execution_policy(developer, roles["validatorAgentId"],
                                             roles["reviewerAgentId"], owner, qa_agent_id=qa)
        agent_ids = {context["agentId"], developer, roles["validatorAgentId"], roles["reviewerAgentId"]}
        if qa:
            agent_ids.add(qa)
        _get_agents(client, context["companyId"], agent_ids)
        patch = {"assigneeAgentId": developer, "status": "todo", "executionPolicy": policy}
        if profile and profile["adapterType"] in {"codex_local", "opencode_local"}:
            patch["assigneeAdapterOverrides"] = {"adapterConfig": {"model": profile["model"]}}
        document = {"schemaVersion": 1, "runId": context["runId"], **plan,
                    "selectedProfile": profile, "selectionRationale": profile_reason,
                    "executionPolicy": policy}
    else:
        if issue.get("workMode") not in {None, "standard", "ask"}:
            raise ValueError("Analysis can finish only a standard or Ask issue")
        document = {"schemaVersion": 1, "runId": context["runId"], **plan}
        patch = {"status": "done", "comment": plan["answer"]}

    if existing_plan is not None:
        document["runId"] = existing_plan.get("runId")
        if _canonical(existing_plan) != _canonical(document):
            raise ValueError("Existing plan conflicts with this run; refusing to overwrite")
        if plan["kind"] == "coding":
            if (issue.get("assigneeAgentId") == patch["assigneeAgentId"]
                    and issue.get("executionPolicy") == policy
                    and issue.get("assigneeAdapterOverrides") == patch.get("assigneeAdapterOverrides")):
                return {"status": "replayed", "planRevisionId": existing_revision}
            if issue.get("assigneeAgentId") != context["agentId"] or issue.get("executionPolicy") is not None:
                raise ValueError("Persisted handoff plan conflicts with current issue ownership or policy")
        elif issue.get("status") == "done":
            return {"status": "replayed", "planRevisionId": existing_revision}

    if (issue.get("assigneeAgentId") != context["agentId"]
            or issue.get("executionRunId") != context["runId"]
            or issue.get("status") != "in_progress"):
        raise ValueError("Issue is not assigned and in progress under this run")
    if plan["kind"] == "coding" and issue.get("executionPolicy") is not None:
        raise ValueError("Issue already has an execution policy; refusing to replace native stages")
    if plan["kind"] == "analysis" and issue.get("executionPolicy") is not None:
        raise ValueError("Analysis cannot finish an issue with a coding policy")
    version = issue.get("statusVersion")
    if isinstance(version, bool) or not isinstance(version, int) or version < 0:
        raise ValueError("Issue has no valid native status/ownership version")
    patch["expectedStatusVersion"] = version
    revision, _ = _document(client, context["taskId"], document)
    updated = client.request("PATCH", f"/api/issues/{context['taskId']}", patch)
    expected_status = "todo" if plan["kind"] == "coding" else "done"
    if not isinstance(updated, dict) or updated.get("status") != expected_status:
        raise ValueError("Paperclip did not confirm the requested Orchestrator transition")
    if plan["kind"] == "coding" and (updated.get("assigneeAgentId") != patch["assigneeAgentId"]
                                      or updated.get("executionPolicy") != policy):
        raise ValueError("Paperclip did not confirm the requested coding handoff")
    return {"status": "handed_off" if plan["kind"] == "coding" else "answered",
            "planRevisionId": revision}


def _read_plan(client, issue_id):
    try:
        document = client.request("GET", f"/api/issues/{issue_id}/documents/plan")
    except ApiError as exc:
        if exc.status == 404:
            return None, None
        raise
    except HTTPError as exc:
        if exc.code == 404:
            return None, None
        raise
    if not isinstance(document, dict) or not isinstance(document.get("body"), str):
        raise ValueError("Existing plan document is malformed; refusing to overwrite")
    try:
        return json.loads(document["body"]), document.get("latestRevisionId")
    except ValueError as exc:
        raise ValueError("Existing plan document is malformed; refusing to overwrite") from exc


def _read_plan_revision(client, issue_id):
    _, revision = _read_plan(client, issue_id)
    if not revision:
        raise ValueError("Persisted plan has no revision identity")
    return revision


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", required=True, help="immutable runtime registry JSON")
    parser.add_argument("--plan", required=True, help="Orchestrator plan JSON")
    args = parser.parse_args(argv)
    context = {key: os.environ["PAPERCLIP_" + env] for key, env in
               (("agentId", "AGENT_ID"), ("companyId", "COMPANY_ID"), ("runId", "RUN_ID"))}
    client = RunClient(os.environ["PAPERCLIP_API_URL"], os.environ["PAPERCLIP_API_KEY"], context["runId"])
    context["taskId"] = os.environ.get("PAPERCLIP_TASK_ID")
    if not context["taskId"]:
        run = client.request("GET", f"/api/heartbeat-runs/{context['runId']}")
        if run.get("id") != context["runId"] or run.get("agentId") != context["agentId"]:
            raise ValueError("Run identity lookup does not match this agent")
        context["taskId"] = (run.get("contextSnapshot") or {}).get("issueId")
    for key in context:
        _uuid(context[key], key)
    bindings = json.loads(Path(args.bindings).read_text(encoding="utf-8-sig"))
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    print(json.dumps(execute(client, context, bindings, plan)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STOP: Orchestrator action not confirmed (%s); inspect Paperclip state before retrying."
              % type(exc).__name__)
        raise SystemExit(1)
