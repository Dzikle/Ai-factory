"""Owner-only, repeatable provisioning of native project intake and runtime bindings.

No task dispatch, background worker, secret copying, or workflow state store.
Private recovery backup must precede --apply. Every task transition stays native.
"""
import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from uuid import UUID
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler

from milestone0.scripts.paperclip_admission import Client
from milestone2.scripts.assistant_reply import NoRedirect
from milestone2.scripts import profile_readiness

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = "aif-m0-paperclip-fork-paperclip-fork-1"
MODEL = "opencode/nemotron-3.5-lightning-free"
SOURCES = ("milestone0/scripts/paperclip_admission.py", "milestone1/paperclip_policy.py",
           "milestone2/scripts/assistant_reply.py", "milestone2/scripts/orchestrator.py",
           "milestone2/scripts/profile_readiness.py")


def _free_agent_payload(project_id, project, instruction):
    return {
        "name": project["label"] + " Developer (Free)", "role": "engineer",
        "title": "Developer — qualified free native runtime",
        "adapterType": "opencode_local", "adapterConfig": {
            "cwd": project["cwd"], "model": MODEL, "extraArgs": ["--pure"],
            "timeoutSec": 600, "dangerouslySkipPermissions": False,
        },
        "runtimeConfig": {"heartbeat": {"enabled": False, "maxConcurrentRuns": 1},
            "providerFallback": {"adapterType":"codex_local", "model":"gpt-5.6-sol",
                "extraArgs":["--sandbox","workspace-write"],
                "qualificationRunId":project["subscriptionQualificationRunId"]}},
        "permissions": {"canCreateAgents": False, "canCreateSkills": False},
        "budgetMonthlyCents": 1000,
        "metadata": {"setupKey": "automatic-entry-v1:" + project_id + ":free-developer",
                     "logicalRole": "developer", "projectId": project_id},
        "instructionsBundle": {"files": {"AGENTS.md": instruction}},
    }


def _free_agent_matches(agent, expected, company):
    actual_config = agent.get("adapterConfig")
    expected_config = expected["adapterConfig"]
    if not isinstance(actual_config, dict):
        return False
    if any(actual_config.get(key) != value for key, value in expected_config.items()):
        return False
    if any(key not in expected_config and not key.startswith("instructions") for key in actual_config):
        return False
    desired_name = expected["name"]
    legacy_name = desired_name.removesuffix(" (Free)")
    runtime = agent.get("runtimeConfig")
    desired_runtime = expected["runtimeConfig"]
    runtime_matches = runtime == desired_runtime or runtime == {
        key:value for key,value in desired_runtime.items() if key != "providerFallback"}
    return (agent.get("companyId") == company
            and agent.get("status") not in {"running", "terminated"}
            and agent.get("name") in {desired_name, legacy_name, legacy_name + " 2"}
            and runtime_matches
            and all(agent.get(key) == expected[key] for key in (
                "role", "title", "adapterType", "permissions",
                "budgetMonthlyCents", "metadata")))


def _container_readiness_runner(args, **kwargs):
    """Run the no-tool probe in the same UID/runtime used by native agents."""
    env = kwargs.get("env") or {}
    native_config = env.get("OPENCODE_CONFIG_CONTENT")
    if not isinstance(native_config, str):
        raise ValueError("Readiness probe omitted its native permission configuration")
    return subprocess.run(
        ["docker", "exec", "--user", "1000:1000", "-i", "-e",
         "OPENCODE_CONFIG_CONTENT=" + native_config, CONTAINER, *args],
        input=kwargs.get("input"), capture_output=True, text=True,
        timeout=kwargs.get("timeout", 30), check=False,
    )


def _orchestrator_runtime(project, code_root, registry_path, available_ids, receipts):
    env = {"AIF_ORCHESTRATOR_HELPER": code_root + "/milestone2/scripts/orchestrator.py",
           "AIF_ORCHESTRATOR_BINDINGS": registry_path}
    free_receipt = next((row.get("category") for row in receipts
                         if row.get("profileId") == "free-opencode"), "not_probed")
    if "free-opencode" in available_ids:
        env["OPENCODE_CONFIG_CONTENT"] = json.dumps(native_config())
        return "opencode_local", {
            "cwd": project["cwd"], "model": MODEL,
            "extraArgs": ["--agent", "aif-orchestrator", "--pure"],
            "timeoutSec": 360, "dangerouslySkipPermissions": False, "env": env,
        }, "free-opencode", "free-opencode:available"
    if "codex-subscription" not in available_ids:
        raise ValueError("No qualified Orchestrator runtime is available")
    return "codex_local", {
        "cwd": project["cwd"], "model": "gpt-5.6-sol",
        "extraArgs": ["--sandbox", "read-only", "--add-dir", "/tmp", "-c",
                      'model_reasoning_effort="low"'],
        "timeoutSec": 360, "dangerouslyBypassApprovalsAndSandbox": False, "env": env,
    }, "codex-subscription", f"free-opencode:{free_receipt}; codex-subscription:prior-qualified"


def native_config():
    permission = {"*": "deny", "read": {"*": "allow", "*.env*": "deny", "**/.env*": "deny",
                  "**/auth.json": "deny", "**/google-services.json": "deny"},
                  "glob": "allow", "grep": "allow", "edit": {"*": "deny", "/tmp/aif-plan-*.json": "allow"},
                  "bash": {"*": "deny", "git rev-parse *": "allow", "git status *": "allow",
                           "git ls-files*": "allow", "git diff *": "allow",
                           "python3 -I /paperclip/aif-automatic-entry/*/milestone2/scripts/orchestrator.py *": "allow"},
                  "external_directory": {"*": "deny", "/tmp/aif-plan-*": "allow"}}
    return {"$schema": "https://opencode.ai/config.json", "permission": permission,
            "agent": {"aif-orchestrator": {"mode": "primary", "steps": 20, "permission": permission}}}


def docker(*args, stdin=None):
    result = subprocess.run(["docker", *args], input=stdin, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError("Docker provisioning failed; private output withheld")
    return result.stdout


def deploy_public_runtime(registry):
    files = {name: (ROOT / name).read_bytes() for name in SOURCES}
    code_sha = hashlib.sha256(b"".join(name.encode() + files[name] for name in sorted(files))).hexdigest()
    code_root = "/paperclip/aif-automatic-entry/" + code_sha[:16]
    registry_bytes = (json.dumps(registry, sort_keys=True, indent=2) + "\n").encode()
    registry_sha = hashlib.sha256(registry_bytes).hexdigest()
    registry_path = "/paperclip/aif-automatic-entry/registry-" + registry_sha + ".json"
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for name, data in {**{code_sha[:16] + "/" + k: v for k, v in files.items()},
                           "registry-" + registry_sha + ".json": registry_bytes}.items():
            member = tarfile.TarInfo(name); member.size = len(data); member.mode = 0o444
            member.uid = member.gid = 0
            archive.addfile(member, io.BytesIO(data))
    docker("exec", CONTAINER, "mkdir", "-p", "/paperclip/aif-automatic-entry")
    docker("exec", "-i", CONTAINER, "tar", "-xf", "-", "-C", "/paperclip/aif-automatic-entry", stdin=stream.getvalue())
    docker("exec", CONTAINER, "chmod", "755", "/paperclip/aif-automatic-entry")
    # Tar-created directories are root-owned, so run UID cannot replace helpers.
    docker("exec", "--user", "1000:1000", CONTAINER, "python3", "-c",
           "import sys; sys.path.insert(0,sys.argv[1]); import milestone2.scripts.orchestrator", code_root)
    return code_root, registry_path, code_sha, registry_sha


def configure(client, state, preset, *, apply=False):
    def request(method, path, body=None, **kwargs):
        return client.request(method, path, body, **kwargs)[1]
    if preset["companyId"] != state["companyId"]:
        raise ValueError("Provisioning company mismatch")
    company = state["companyId"]
    agents = request("GET", f"/api/companies/{company}/agents")
    by_id = {a["id"]: a for a in agents}
    registry = deepcopy(preset)
    qualification_id = preset.get("subscriptionQualificationRunId")
    try:
        qualification_id = str(UUID(qualification_id))
    except (ValueError,TypeError,AttributeError):
        raise ValueError("A verified native subscription qualification is required") from None
    prepared = []
    for project_id, project in registry["projects"].items():
        project["subscriptionQualificationRunId"] = qualification_id
        actual = request("GET", f"/api/projects/{project_id}")
        if actual.get("companyId") != company or not any(w.get("cwd") == project["cwd"] for w in actual.get("workspaces", [])):
            raise ValueError("Project source binding drifted")
        for key in ("orchestratorAgentId", "developerAgentId", "validatorAgentId", "reviewerAgentId", "qaAgentId"):
            a = by_id.get(project[key], {})
            if a.get("companyId") != company or a.get("status") in {"running", "terminated"}:
                raise ValueError("Project role is foreign, busy or terminated")
        old_developer = by_id[project["developerAgentId"]]
        if (old_developer.get("adapterType") != "codex_local"
                or old_developer.get("adapterConfig", {}).get("model") != "gpt-5.6-sol"
                or old_developer.get("adapterConfig", {}).get("cwd") != project["cwd"]):
            raise ValueError("Subscription runtime binding drifted")
        setup_key = "automatic-entry-v1:" + project_id + ":free-developer"
        existing = [a for a in agents if (a.get("metadata") or {}).get("setupKey") == setup_key]
        if len(existing) > 1:
            raise ValueError("Ambiguous free runtime binding")
        instruction = request("GET", f"/api/agents/{old_developer['id']}/instructions-bundle/file?path=AGENTS.md")["content"]
        expected = _free_agent_payload(project_id, project, instruction)
        if existing:
            free = existing[0]
            if not _free_agent_matches(free, expected, company):
                raise ValueError("Free runtime binding drifted")
        else:
            free = None
        prepared.append((project_id, project, old_developer, free, expected))
    qualification = request("GET", f"/api/heartbeat-runs/{qualification_id}")
    if (qualification.get("companyId") != company or qualification.get("status") != "succeeded"
        or (qualification.get("usageJson") or {}).get("model") != "gpt-5.6-sol"
        or ((qualification.get("runnerProfileJson") or {}).get("adapterDispatch") or {}).get("adapterType") != "codex_local"):
        raise ValueError("Successful native subscription qualification does not match the admitted runtime")
    if not apply:
        return {"status": "ready", "projectCount": len(registry["projects"]), "mutations": False}

    probe_profiles = [
        {"id": "free-opencode", "agentId": "pending", "adapterType": "opencode_local",
         "model": MODEL, "tier": "free", "qualified": True,
         "availabilityProbe": "opencode_no_tools"},
        {"id": "codex-subscription", "agentId": "existing", "adapterType": "codex_local",
         "model": "gpt-5.6-sol", "tier": "subscription", "qualified": True,
         "qualificationRunId":qualification_id},
    ]
    available, readiness_receipts = profile_readiness.qualify_available(
        probe_profiles, _container_readiness_runner)
    available_ids = {profile["id"] for profile in available}
    readiness_receipts.append({"profileId":"codex-subscription", "qualification":"verifiedNativeRunNotFreshProbe",
        "runId":qualification_id, "adapterType":"codex_local", "model":"gpt-5.6-sol"})

    for project_id, project, old_developer, free, expected in prepared:
        if free is None:
            # Creation has no configuration revision. Install the fallback in
            # a separate board PATCH so native dispatch can verify authority.
            creation = deepcopy(expected)
            creation["runtimeConfig"].pop("providerFallback")
            free = request("POST", f"/api/companies/{company}/agents", creation, expected=(201,))
            agents.append(free)
            by_id[free["id"]] = free
        elif free.get("name") != expected["name"]:
            free = request("PATCH", f"/api/agents/{free['id']}", {"name": expected["name"]})
            by_id[free["id"]] = free
        if free.get("runtimeConfig") != expected["runtimeConfig"]:
            free = request("PATCH", f"/api/agents/{free['id']}", {"runtimeConfig":expected["runtimeConfig"]})
            by_id[free["id"]] = free
        project["profiles"] = [
            {"id": "free-opencode", "agentId": free["id"], "adapterType": "opencode_local", "model": MODEL,
             "tier": "free", "qualified": "free-opencode" in available_ids,
             "availabilityProbe": "opencode_no_tools"},
            {"id": "codex-subscription", "agentId": old_developer["id"], "adapterType": "codex_local", "model": "gpt-5.6-sol",
             "tier": "subscription", "qualified": "codex-subscription" in available_ids},
        ]
        project["profileReadinessReceipts"] = deepcopy(readiness_receipts)
    code_root, registry_path, code_sha, registry_sha = deploy_public_runtime(registry)
    instruction = (ROOT / "milestone2/fixtures/orchestrator.md").read_text(encoding="utf-8")
    for project_id, project in registry["projects"].items():
        router = by_id[project["orchestratorAgentId"]]
        adapter, config, selected_profile, rationale = _orchestrator_runtime(
            project, code_root, registry_path, available_ids, readiness_receipts)
        config.update({k: v for k, v in router.get("adapterConfig", {}).items() if k.startswith("instructions")})
        runtime = deepcopy(router.get("runtimeConfig") or {})
        runtime.pop("providerFallback",None)
        if adapter == "opencode_local":
            runtime["providerFallback"] = {"adapterType":"codex_local", "model":"gpt-5.6-sol",
                "extraArgs":["--sandbox","read-only","--add-dir","/tmp"], "qualificationRunId":qualification_id}
        request("PATCH", f"/api/agents/{router['id']}", {"name": project["label"] + " Orchestrator", "title": "Orchestrator / Router",
                "adapterType": adapter, "adapterConfig": config, "runtimeConfig":runtime,
                "metadata": {**(router.get("metadata") or {}), "taskIntake": True,
                             "logicalRole": "orchestrator", "projectId": project_id,
                             "selectedProfileId": selected_profile,
                             "selectionRationale": rationale}})
        request("PUT", f"/api/agents/{router['id']}/instructions-bundle/file", {"path": "AGENTS.md", "content": instruction,
                                                                                  "clearLegacyPromptTemplate": True})
        request("PATCH", f"/api/projects/{project_id}", {"leadAgentId": router["id"]})
        for key, role in (("developerAgentId", "developer"), ("validatorAgentId", "tests"), ("reviewerAgentId", "reviewer"), ("qaAgentId", "qa")):
            a = by_id[project[key]]
            request("PATCH", f"/api/agents/{a['id']}", {"name": project["label"] + " " + role.title() + (" (Codex fallback)" if role == "developer" else ""),
                "metadata": {**(a.get("metadata") or {}), "logicalRole": role, "projectId": project_id,
                             "runtimeBindingHidden": role == "developer"}})
        for aid in [router["id"], *(p["agentId"] for p in project["profiles"]),
                    project["validatorAgentId"], project["reviewerAgentId"], project["qaAgentId"]]:
            actual = request("GET", f"/api/agents/{aid}")
            if actual.get("status") in {"paused", "error"}:
                request("POST", f"/api/agents/{aid}/resume", {})
    archived = []
    for a in agents:
        if a["status"] == "paused" and a["name"].startswith(("M1 ", "M2 ", "Milestone 0 ")):
            request("PATCH", f"/api/agents/{a['id']}", {"metadata": {**(a.get("metadata") or {}), "archived": True,
                    "archiveReason": "Historical admission fixture; records and audit preserved"}})
            archived.append(a["id"])
    return {"status": "configured", "projects": registry["projects"], "codeSha256": code_sha,
            "registrySha256": registry_sha, "registryPath": registry_path, "archivedFixtureAgentIds": archived,
            "taskDispatch": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8-sig"))
    if state["baseUrl"] not in {"http://localhost:13101", "http://127.0.0.1:13101"}:
        raise ValueError("Use the exact local controller")
    client = Client(state["baseUrl"], state["boardApiKey"])
    client.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(client.cookies), NoRedirect())
    preset = json.loads((ROOT / "milestone2/config/automatic-entry-projects.json").read_text())
    result = configure(client, state, preset, apply=args.apply)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "projects" and k != "archivedFixtureAgentIds"}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STOP: automatic entry provisioning not confirmed (%s); inspect private backup and live state." % type(exc).__name__)
        raise SystemExit(1)
