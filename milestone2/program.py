"""Submit and inspect one-authorized self-enhancement programs.

Paperclip remains the sole task, run, workspace, approval, and MCP-policy
authority. This module only prepares validated payloads, performs idempotent
writes owned by Paperclip, and reads back authoritative status. It never
grants runtime authority, stores credentials, or copies operator state into
task descriptions, documents, or workspaces.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

from milestone0.scripts.paperclip_admission import ApiError, Client
from milestone1.paperclip_policy import program_agent_id
from milestone1.validate_contracts import validate_self_enhancement
from milestone2.capabilities import DEFAULT_MANIFESTS, assess, load_manifests, read_probes
from milestone2.task import preflight as task_preflight
from milestone2.task import read_object, text, uuid


SCOPE_VERBS = ("implement", "verify", "review", "report", "maintain")
SIZES = ("small", "medium", "large")
RISKS = ("low", "normal", "high")
CHANGE_TYPES = ("read_only", "documentation", "code", "policy", "mixed")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*\Z")


def _identifier(value, label):
    if not isinstance(value, str) or not (1 <= len(value) <= 128) or not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{label} must be a bounded identifier, got {value!r}")
    return value


def program_execution_policy(developer_agent_id, validator_agent_id, reviewer_agent_id, *, qa_agent_id=None):
    """Child-wave policy: independent review stages, no human approval gate.

    Child waves inherit the owner-created program authorization receipt, so
    they carry no per-wave user confirmation stage. Final owner integration
    approval still happens on the parent program boundary.
    """
    agents = [program_agent_id(value) for value in (developer_agent_id, validator_agent_id, reviewer_agent_id)]
    if qa_agent_id is not None:
        agents.append(program_agent_id(qa_agent_id))
    if len(set(agents)) != len(agents):
        raise ValueError("Developer, validator, Reviewer and QA must be distinct Paperclip agents")
    stages = [
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[1]}]},
        {"type": "review", "participants": [{"type": "agent", "agentId": agents[2]}]},
    ]
    if qa_agent_id is not None:
        stages.append({"type": "review", "participants": [{"type": "agent", "agentId": agents[3]}]})
    return {"mode": "normal", "commentRequired": True, "maxReviewRounds": 3, "stages": stages}


def classify_task(*, intent, scope_verb, size, risk, change_type):
    """Map only validated contract fields to a deterministic execution mode.

    Classification never interprets free-form prose: every field must be a
    bounded contract value or a ValueError is raised. Read-only work is not
    started in an agent runtime and does not allocate a workspace. Small,
    low-risk, non-user-facing changes use the reduced verification profile
    but retain independent review; every other code change uses the full
    profile and an isolated workspace.
    """
    _identifier(intent, "intent")
    if scope_verb not in SCOPE_VERBS:
        raise ValueError(f"scope_verb must be one of {list(SCOPE_VERBS)}, got {scope_verb!r}")
    if size not in SIZES:
        raise ValueError(f"size must be one of {list(SIZES)}, got {size!r}")
    if risk not in RISKS:
        raise ValueError(f"risk must be one of {list(RISKS)}, got {risk!r}")
    if change_type not in CHANGE_TYPES:
        raise ValueError(f"change_type must be one of {list(CHANGE_TYPES)}, got {change_type!r}")
    if change_type == "read_only":
        return {"execution_mode": "read_only", "requires_workspace": False, "verification_profile": "reduced"}
    if size == "small" and risk == "low" and change_type == "documentation":
        return {"execution_mode": "reduced", "requires_workspace": True, "verification_profile": "reduced"}
    return {"execution_mode": "full", "requires_workspace": True, "verification_profile": "full"}


def authorization_digest(program):
    """Canonical SHA-256 over the scope that the owner authorized."""
    value = {
        "program_id": program["program_id"],
        "base_revision": program["base_revision"],
        "authorization": program["authorization"],
        "waves": program["waves"],
    }
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def wave_request_key(program, wave):
    """Stable per-wave idempotency key derived from the program request key."""
    return f"{program['request_key']}:{wave['id']}"


def parent_title(program):
    return f"Self-enhancement program {program['program_id']} ({program['request_key']})"


def wave_title(program, wave):
    return f"Self-enhancement wave {wave['id']} [{program['request_key']}]"


def _owner_user_id(state):
    if not isinstance(state, dict):
        raise ValueError("operator state must be a JSON object")
    if state.get("agentId") or state.get("runId"):
        raise ValueError("program submission requires the private operator state, not an agent/run identity")
    return text(state.get("userId"), "owner userId", 255)


def _validated_program(program, *, now):
    if not isinstance(program, dict):
        raise ValueError("program must be a JSON object")
    try:
        errors = validate_self_enhancement(program, now=now)
    except KeyError as exc:
        raise ValueError(f"program is missing required field {exc}") from exc
    if errors:
        raise ValueError(f"program authorization invalid: {'; '.join(errors)}")
    return program


def build_submission(state, workflow, program, *, start=False, now=None, health=None, capability_manifests=None):
    """Build every Paperclip payload without network or filesystem writes."""
    now = now or datetime.now(timezone.utc)
    owner = _owner_user_id(state)
    program = _validated_program(program, now=now)
    agents = {
        "developerAgentId": program_agent_id(workflow.get("developerAgentId")),
        "validatorAgentId": program_agent_id(workflow.get("validatorAgentId")),
        "reviewerAgentId": program_agent_id(workflow.get("reviewerAgentId")),
    }
    qa = program_agent_id(workflow["qaAgentId"]) if workflow.get("qaAgentId") else None
    policy = program_execution_policy(
        agents["developerAgentId"], agents["validatorAgentId"], agents["reviewerAgentId"], qa_agent_id=qa
    )
    project_id = uuid(workflow.get("projectId"), "projectId")
    digest = authorization_digest(program)
    decisions = {}
    for wave in program["waves"]:
        decisions[wave["id"]] = classify_task(
            intent=program["intent"],
            scope_verb=program["scope_verb"],
            size=wave["size"],
            risk=wave["risk"],
            change_type=wave["change_type"],
        )
    if start and any(decision["execution_mode"] == "read_only" for decision in decisions.values()):
        raise ValueError("refusing --start: a read-only program must not allocate an agent runtime or workspace")
    admission = None
    if health is not None:
        manifests = capability_manifests if capability_manifests is not None else load_manifests(DEFAULT_MANIFESTS)
        required = sorted({capability for wave in program["waves"] for capability in wave["required_capabilities"]})
        optional = sorted({capability for wave in program["waves"] for capability in wave["optional_capabilities"]} - set(required))
        admission = assess(required, optional, manifests, health)
    authorization_document = {"program": program, "digest": digest}
    if admission is not None:
        authorization_document["admission"] = admission
    parent = {
        "title": text(parent_title(program), "title", 200),
        "description": text(
            "Owner-authorized self-enhancement program.\n"
            f"Program: {program['program_id']} (request {program['request_key']}).\n"
            f"Spec: {program['spec_path']}.\n"
            f"Plan: {program['plan_path']}.\n"
            f"Base revision: {program['base_revision']}.\n"
            f"Authorization digest sha256:{digest}.",
            "description",
            200_000,
        ),
        "idempotencyKey": text(program["request_key"], "requestKey", 255),
        "projectId": project_id,
        "status": "backlog",
        "assigneeAgentId": agents["developerAgentId"],
        "executionPolicy": policy,
    }
    receipt = {
        "body": f"Authorized self-enhancement program sha256:{digest}",
        "clientRequestId": f"{program['request_key']}:authorization-receipt",
        "authorUserId": owner,
    }
    children = []
    for wave in program["waves"]:
        description = (
            f"Self-enhancement wave '{wave['id']}' of program {program['program_id']} "
            f"(request {program['request_key']}).\n"
            f"Authorization digest sha256:{digest}.\n"
            f"Verification profile: {wave['verification_profile']}."
        )
        if admission is not None and admission["status"] == "degraded" and admission["unavailable_optional"]:
            description += f"\nDegraded optional capabilities: {', '.join(admission['unavailable_optional'])}."
        children.append(
            {
                "title": text(wave_title(program, wave), "title", 200),
                "description": text(description, "description", 200_000),
                "idempotencyKey": text(wave_request_key(program, wave), "requestKey", 255),
                "projectId": project_id,
                "status": "backlog",
                "assigneeAgentId": agents["developerAgentId"],
                "executionPolicy": policy,
                "wave": wave["id"],
                "blockedByWaves": list(wave["blocked_by"]),
            }
        )
    return {
        "owner": owner,
        "projectId": project_id,
        "digest": digest,
        "policy": policy,
        "decisions": decisions,
        "admission": admission,
        "parent": parent,
        "authorizationDocument": authorization_document,
        "receipt": receipt,
        "children": children,
    }


def _check_replay(label, expected, actual, fields):
    for field in fields:
        if actual.get(field) != expected.get(field):
            raise ValueError(f"replay conflict on {label}: field {field} differs; refusing to overwrite")


def submit_program(client, company_id, state, workflow, program, *, start=False, now=None,
                   health=None, capability_manifests=None):
    """Idempotently create one parent plus four dependency-ordered children.

    Every write uses a stable idempotency key, document content, or
    clientRequestId, so rerunning after any interruption converges to the
    same five issue IDs and one receipt instead of duplicating them. Before
    accepting an existing object on replay, its project, parent, title,
    request key, document digest, blockers, and policy are compared; a
    conflict stops and is never overwritten.

    When component health is supplied, admission is assessed before dispatch:
    ``blocked`` leaves all children in backlog (the caller maps this to exit
    2); ``degraded`` is stored in the authorization document and child
    context and may start because every unavailable capability is optional.
    """
    now = now or datetime.now(timezone.utc)
    company_id = uuid(company_id, "companyId")
    plan = build_submission(state, workflow, program, start=start, now=now,
                            health=health, capability_manifests=capability_manifests)
    task_preflight(client, company_id, plan["parent"], start=False)

    _, parent = client.request("POST", f"/api/companies/{company_id}/issues", plan["parent"], expected=(200, 201))
    _check_replay("parent issue", plan["parent"], parent, ("projectId", "title", "idempotencyKey"))
    parent_id = parent["id"]

    document_path = f"/api/issues/{parent_id}/documents/authorization"
    try:
        _, document = client.request("PUT", document_path, {"content": plan["authorizationDocument"]}, expected=(200,))
    except (ApiError, ValueError) as exc:
        raise ValueError(f"authorization document conflict for parent {parent_id}; refusing to overwrite") from exc
    revision = document.get("revisionId")

    client.request("POST", f"/api/issues/{parent_id}/comments", plan["receipt"], expected=(200, 201))

    child_ids = []
    for child in plan["children"]:
        payload = {key: child[key] for key in ("title", "description", "idempotencyKey", "projectId", "status", "assigneeAgentId", "executionPolicy")}
        payload["parentId"] = parent_id
        _, issue = client.request("POST", f"/api/companies/{company_id}/issues", payload, expected=(200, 201))
        _check_replay(f"child wave {child['wave']}", {**payload, "parentId": parent_id}, issue,
                       ("projectId", "parentId", "title", "idempotencyKey"))
        _check_replay(f"child wave {child['wave']} policy", {"executionPolicy": child["executionPolicy"]}, issue, ("executionPolicy",))
        child_ids.append(issue["id"])

    wave_index = {child["wave"]: child_ids[position] for position, child in enumerate(plan["children"])}
    for position, child in enumerate(plan["children"]):
        expected_blockers = [wave_index[name] for name in child["blockedByWaves"]]
        _, current = client.request("GET", f"/api/issues/{child_ids[position]}")
        existing_blockers = current.get("blockedByIssueIds") or []
        if existing_blockers and existing_blockers != expected_blockers:
            raise ValueError(f"replay conflict on child wave {child['wave']}: blockers differ; refusing to overwrite")
        client.request("PATCH", f"/api/issues/{child_ids[position]}", {"blockedByIssueIds": expected_blockers}, expected=(200,))

    if start:
        _, first = client.request("GET", f"/api/issues/{child_ids[0]}")
        admission = plan["admission"]
        if first.get("status") != "todo" and (admission is None or admission["status"] != "blocked"):
            client.request("PATCH", f"/api/issues/{child_ids[0]}", {"status": "todo"}, expected=(200,))

    return {
        "parentId": parent_id,
        "digest": plan["digest"],
        "admission": plan["admission"],
        "parentUrlPath": f"/api/issues/{parent_id}",
        "authorizationDocumentRevision": revision,
        "waves": [
            {"id": issue_id, "wave": child["wave"], "title": child["title"], "urlPath": f"/api/issues/{issue_id}"}
            for issue_id, child in zip(child_ids, plan["children"])
        ],
    }


def read_program_status(client, parent_id, company_id):
    """Read the authoritative parent/child state without writes or secrets."""
    company_id = uuid(company_id, "companyId")
    _, parent = client.request("GET", f"/api/issues/{parent_id}")
    if not isinstance(parent, dict) or parent.get("companyId") != company_id:
        raise ValueError("parent issue does not belong to the configured company")
    try:
        _, document = client.request("GET", f"/api/issues/{parent_id}/documents/authorization")
        stored = document.get("content") or {}
        stored_program, stored_digest = stored.get("program"), stored.get("digest")
    except (ApiError, KeyError, AttributeError) as exc:
        raise ValueError("program authorization document is missing") from exc
    if not isinstance(stored_program, dict) or not stored_digest:
        raise ValueError("program authorization document is missing")
    expected_titles = {wave_title(stored_program, wave) for wave in stored_program.get("waves", [])}
    _, issues = client.request("GET", f"/api/companies/{company_id}/issues?projectId={parent.get('projectId')}")
    children = [row for row in issues if isinstance(row, dict) and row.get("parentId") == parent_id]
    if len(children) > 8:
        raise ValueError(f"program has {len(children)} children; at most 8 expected")
    seen = set()
    for row in children:
        if row.get("companyId") != company_id:
            raise ValueError("program child does not belong to the configured company")
        if row["id"] in seen:
            raise ValueError("duplicate program child ID")
        seen.add(row["id"])
        if row.get("title") not in expected_titles:
            raise ValueError(f"unexpected program child title: {row.get('title')!r}")
    return {
        "parentId": parent_id,
        "status": parent.get("status"),
        "digest": stored_digest,
        "waves": [
            {
                "id": row["id"],
                "identifier": row.get("identifier"),
                "status": row.get("status"),
                "blockedByIssueIds": row.get("blockedByIssueIds") or [],
            }
            for row in sorted(children, key=lambda row: row.get("title") or "")
        ],
    }


def _atomic_write_json(path, value):
    target = Path(path)
    tmp = target.with_name(f"{target.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=os.environ.get("AIF_PAPERCLIP_STATE"),
                        help="private Paperclip board state JSON; or AIF_PAPERCLIP_STATE")
    parser.add_argument("--json", action="store_true", help="print a compact machine-readable result")
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit", help="idempotently submit one authorized program (one parent, four waves)")
    submit.add_argument("--workflow", required=True, help="project and logical agent IDs JSON")
    submit.add_argument("--program", required=True, help="validated self-enhancement program JSON")
    submit.add_argument("--start", action="store_true", help="set the first unblocked wave to todo; agents must already be active")
    submit.add_argument("--dry-run", action="store_true", help="validate and show payloads without network or filesystem writes")
    submit.add_argument("--output", default=None, help="atomically write the submission receipt JSON here")
    submit.add_argument("--health", default=None, help="component probe results JSON for admission gating (doctor --output)")
    submit.add_argument("--manifests", default=str(DEFAULT_MANIFESTS), help="Git-owned capability provider manifests")
    status = commands.add_parser("status", help="show Paperclip's authoritative program status")
    status.add_argument("parent", help="parent program issue UUID")
    args = parser.parse_args(argv)
    try:
        if not args.state:
            raise ValueError("Set AIF_PAPERCLIP_STATE or pass --state with the private board state file")
        state = read_object(args.state)
        company_id = uuid(state.get("companyId"), "companyId")
        if args.command == "submit":
            workflow, program = read_object(args.workflow), read_object(args.program)
            manifests = load_manifests(args.manifests)
            health = read_probes(args.health, manifests) if args.health else None
            if args.dry_run:
                plan = build_submission(state, workflow, program, start=args.start,
                                        health=health, capability_manifests=manifests)
                print(json.dumps({**plan, "dryRun": True}, indent=2))
                return 0
            base_url = text(state.get("baseUrl"), "baseUrl", 2048)
            board_key = text(state.get("boardApiKey"), "boardApiKey", 4096)
            client = Client(base_url, board_key)
            result = submit_program(client, company_id, state, workflow, program, start=args.start,
                                    health=health, capability_manifests=manifests)
            if args.output:
                _atomic_write_json(args.output, result)
            if args.json:
                print(json.dumps(result))
            else:
                print(f"Program parent: {result['parentId']} (digest sha256:{result['digest']})")
                if result["admission"] is not None:
                    print(f"Admission: {result['admission']['status']}")
                for row in result["waves"]:
                    print(f"  wave {row['wave']}: {row['id']}")
            if args.start and result["admission"] is not None and result["admission"]["status"] == "blocked":
                print("Admission is blocked: required capabilities are unhealthy; all waves left in backlog.", file=sys.stderr)
                return 2
            return 0
        uuid(args.parent, "parent")
        client = Client(text(state.get("baseUrl"), "baseUrl", 2048), text(state.get("boardApiKey"), "boardApiKey", 4096))
        report = read_program_status(client, args.parent, company_id)
        if args.json:
            print(json.dumps(report))
        else:
            print(f"Program parent: {report['parentId']} — {report['status']}")
            for row in report["waves"]:
                print(f"  {row['identifier'] or row['id']} — {row['status']} (blocked by {len(row['blockedByIssueIds'])})")
        return 0
    except ApiError as error:
        print(f"Paperclip API returned {error.status}; no automatic retry. Resubmit with the same program requestKey.", file=sys.stderr)
    except URLError:
        print("Cannot reach Paperclip; check it is running and the state file baseUrl is correct.", file=sys.stderr)
    except ValueError as error:
        print(str(error), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
