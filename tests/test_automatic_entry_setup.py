"""Automatic task-entry provisioning safety and readiness tests."""
import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

from milestone2.scripts.automatic_entry_setup import configure


COMPANY = str(uuid4())
OWNER = "owner-user"


def project(label):
    return {
        "label": label,
        "cwd": "/paperclip/" + label.lower().replace(" ", "-") + "-source",
        "orchestratorAgentId": str(uuid4()),
        "developerAgentId": str(uuid4()),
        "validatorAgentId": str(uuid4()),
        "reviewerAgentId": str(uuid4()),
        "qaAgentId": str(uuid4()),
    }


def preset(*projects):
    return {
        "companyId": COMPANY,
        "ownerUserId": OWNER,
        "subscriptionQualificationRunId": str(uuid4()),
        "modelProfiles": json.loads((Path(__file__).resolve().parents[1] /
            "milestone2/config/automatic-entry-projects.json").read_text())["modelProfiles"],
        "projects": {str(uuid4()): value for value in projects},
    }


class AutomaticEntrySetupTests(unittest.TestCase):
    def add_native(self, adapter="cline_local"):
        from tests.test_native_profile_contract import fixture as native_fixture
        from milestone2.scripts.native_profile_contract import binding_fingerprint
        pid, configured = next(iter(self.preset["projects"].items()))
        profile, agent = native_fixture(adapter)
        aid, proof = str(uuid4()), str(uuid4())
        identity = agent["metadata"]["nativeProviderAdmission"]["binding"]
        identity.update(companyId=COMPANY, agentId=aid, projectId=pid, cwd=configured["cwd"])
        admission = agent["metadata"]["nativeProviderAdmission"]
        admission["bindingFingerprint"] = binding_fingerprint(identity)
        admission["qualification"]["runId"] = proof
        agent.update(id=aid, companyId=COMPANY)
        agent["adapterConfig"]["cwd"] = configured["cwd"]
        self.client.agents.append(agent)
        spec = next(row for row in self.preset["modelProfiles"] if row["id"] == ("cline" if adapter == "cline_local" else "command-code"))
        spec.update(enabled=True, model=identity["model"], tier="subscription", priority=20,
                    taskKinds=["coding"], risks=["normal", "high"])
        spec.update({key: identity[key] for key in ("provider", "accountRef", "runtimePin", "credentialVersionRef")})
        configured["profileBindings"] = {spec["id"]: {"agentId": aid, "qualificationRunId": proof, "bindingFingerprint": admission["bindingFingerprint"]}}
        return agent

    def test_admitted_profile_preflight_is_read_only_and_revocation_blocks_apply(self):
        for adapter in ("cline_local", "commandcode_local"):
            self.setUp()
            agent = self.add_native(adapter)
            self.assertEqual("ready", configure(self.client, self.state, self.preset)["status"])
            self.assertEqual([], self.client.writes)
            agent["nativeAdmissionState"]["admitted"] = False
            with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime") as deploy:
                with self.assertRaisesRegex(ValueError, "native_admission_unavailable"):
                    configure(self.client, self.state, self.preset, apply=True)
            deploy.assert_not_called()
            self.assertEqual([], self.client.writes)
    def setUp(self):
        self.preset = preset(project("Alpha"))
        self.client = FixtureClient(self.preset)
        self.state = {"companyId": COMPANY}
        # Provisioner tests may never execute Docker or real provider inference,
        # including a RED test whose preflight guard is not implemented yet.
        readiness = patch("milestone2.scripts.automatic_entry_setup._container_readiness_runner",
                          return_value=SimpleNamespace(returncode=1, stdout="", stderr=""))
        deployment = patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime",
                           return_value=("/code", "/registry.json", "sha", "sha"))
        readiness.start()
        deployment.start()
        self.addCleanup(readiness.stop)
        self.addCleanup(deployment.stop)

    def test_dry_run_performs_no_writes_or_runtime_deployment(self):
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime") as deploy:
            result = configure(self.client, self.state, self.preset, apply=False)
        self.assertEqual({"status": "ready", "projectCount": 1, "mutations": False}, result)
        self.assertEqual([], self.client.writes)
        deploy.assert_not_called()

    def test_apply_preflights_every_project_before_first_write(self):
        two = preset(project("Alpha"), project("Beta"))
        client = FixtureClient(two)
        second_id = list(two["projects"])[1]
        client.projects[second_id]["workspaces"][0]["cwd"] = "/wrong"
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime") as deploy:
            with self.assertRaisesRegex(ValueError, "source binding drifted"):
                configure(client, self.state, two, apply=True)
        self.assertEqual([], client.writes)
        deploy.assert_not_called()

    def test_existing_free_binding_requires_exact_runtime_contract(self):
        project_id, configured = next(iter(self.preset["projects"].items()))
        self.client.agents.append({
            "id": str(uuid4()), "companyId": COMPANY, "status": "idle",
            "name": "Alpha Developer", "adapterType": "opencode_local",
            "adapterConfig": {"cwd": configured["cwd"], "model": "wrong/model",
                              "dangerouslySkipPermissions": True},
            "metadata": {"setupKey": "automatic-entry-v1:" + project_id + ":free-developer"},
        })
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime") as deploy:
            with self.assertRaisesRegex(ValueError, "Free runtime binding drifted"):
                configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual([], self.client.writes)
        deploy.assert_not_called()

    def test_subscription_binding_drift_fails_before_mutation(self):
        configured = next(iter(self.preset["projects"].values()))
        developer = next(a for a in self.client.agents if a["id"] == configured["developerAgentId"])
        for adapter, model in (("opencode_local", "gpt-5.6-sol"), ("codex_local", "unqualified-model")):
            developer.update(adapterType=adapter, adapterConfig={"cwd":configured["cwd"], "model":model})
            with self.subTest(adapter=adapter, model=model), self.assertRaisesRegex(ValueError, "Subscription runtime binding drifted"):
                configure(self.client, self.state, self.preset, apply=True)
            self.assertEqual([], self.client.writes)

    def test_native_subscription_qualification_is_required_before_any_write(self):
        self.preset["subscriptionQualificationRunId"] = str(uuid4())
        self.client.qualification = {"companyId": COMPANY, "status": "failed",
            "usageJson": {"model": "gpt-5.6-sol"},
            "runnerProfileJson": {"adapterDispatch": {"adapterType": "codex_local"}}}
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime") as deploy:
            with self.assertRaisesRegex(ValueError, "native subscription qualification"):
                configure(self.client,self.state,self.preset,apply=True)
        self.assertEqual([],self.client.writes)
        deploy.assert_not_called()

    def test_apply_uses_fresh_readiness_and_persists_sanitized_receipts(self):
        deployed = {}

        def capture(registry):
            deployed.update(deepcopy(registry))
            return "/code", "/registry.json", "code-sha", "registry-sha"

        def unavailable(profiles, runner):
            self.assertEqual("opencode/nemotron-3.5-lightning-free", profiles[0]["model"])
            return [profiles[1]], [
                {"profileId": "codex-subscription", "qualification": "priorQualificationNotFreshInference"},
                {"profileId": "free-opencode", "category": "unavailable"},
            ]

        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime", side_effect=capture), \
                patch("milestone2.scripts.profile_readiness.qualify_available", side_effect=unavailable) as readiness:
            result = configure(self.client, self.state, self.preset, apply=True)

        readiness.assert_called_once()
        project_id = next(iter(self.preset["projects"]))
        saved = deployed["projects"][project_id]
        self.assertFalse(saved["profiles"][0]["qualified"])
        self.assertTrue(saved["profiles"][1]["qualified"])
        free_receipt = next(row for row in saved["profileReadinessReceipts"] if row.get("profileId") == "free-opencode")
        self.assertEqual("unavailable",free_receipt["category"])
        proof = next(row for row in saved["profileReadinessReceipts"] if row.get("qualification") == "verifiedNativeRunNotFreshProbe")
        self.assertEqual(self.preset["subscriptionQualificationRunId"],proof["runId"])
        self.assertNotIn("runner", repr(saved["profileReadinessReceipts"]))
        self.assertEqual("configured", result["status"])
        configured_project = next(iter(self.preset["projects"].values()))
        router = next(a for a in self.client.agents
                      if a["id"] == configured_project["orchestratorAgentId"])
        self.assertEqual("codex_local", router["adapterType"])
        self.assertEqual("gpt-5.6-sol", router["adapterConfig"]["model"])
        self.assertIn("read-only", router["adapterConfig"]["extraArgs"])
        self.assertEqual("codex-subscription", router["metadata"]["selectedProfileId"])
        self.assertIn("free-opencode:unavailable", router["metadata"]["selectionRationale"])

    def test_new_free_binding_installs_fallback_through_board_config_revision(self):
        # Agent creation does not create a config revision; native fallback
        # requires a later board-authored configuration change as authority.
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime",
                   return_value=("/code", "/registry.json", "code-sha", "registry-sha")), \
                patch("milestone2.scripts.profile_readiness.qualify_available",
                      side_effect=lambda profiles, _runner: (profiles, [])):
            configure(self.client, self.state, self.preset, apply=True)
        creation = next(row for row in self.client.writes
                        if row[0] == "POST" and row[1].endswith("/agents"))
        self.assertNotIn("providerFallback", creation[2]["runtimeConfig"])
        free = next(a for a in self.client.agents
                    if (a.get("metadata") or {}).get("setupKey", "").endswith(":free-developer"))
        revision = next(row for row in self.client.writes
                        if row[0] == "PATCH" and row[1] == f"/api/agents/{free['id']}"
                        and "runtimeConfig" in row[2])
        self.assertEqual(self.preset["subscriptionQualificationRunId"],
                         revision[2]["runtimeConfig"]["providerFallback"]["qualificationRunId"])

    def test_apply_then_dry_run_accepts_server_managed_instruction_fields_and_unique_name(self):
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime",
                   return_value=("/code", "/registry.json", "code-sha", "registry-sha")), \
                patch("milestone2.scripts.profile_readiness.qualify_available",
                      side_effect=lambda profiles, _runner: (profiles, [])):
            configure(self.client, self.state, self.preset, apply=True)
        self.client.writes.clear()

        try:
            result = configure(self.client, self.state, self.preset, apply=False)
        except ValueError as exc:
            self.fail(f"server-normalized managed fields broke replay: {exc}")

        self.assertEqual("ready", result["status"])
        self.assertEqual([], self.client.writes)
        free = next(a for a in self.client.agents
                    if (a.get("metadata") or {}).get("setupKey", "").startswith("automatic-entry-v1:"))
        self.assertEqual("Alpha Developer (Free)", free["name"])
        router = next(a for a in self.client.agents
                      if a["id"] == next(iter(self.preset["projects"].values()))["orchestratorAgentId"])
        self.assertEqual("opencode_local", router["adapterType"])
        self.assertEqual("free-opencode", router["metadata"]["selectedProfileId"])

    def test_catalog_controls_free_model_and_suitability_in_deployed_registry(self):
        self.preset["modelProfiles"][0].update(model="opencode/other-free", priority=7, risks=["low"])
        deployed = {}
        def capture(registry):
            deployed.update(deepcopy(registry))
            return "/code", "/registry.json", "sha", "sha"
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime", side_effect=capture), \
                patch("milestone2.scripts.profile_readiness.qualify_available", side_effect=lambda profiles, _: (profiles, [])):
            configure(self.client, self.state, self.preset, apply=True)
        project_id = next(iter(self.preset["projects"]))
        saved = deployed["projects"][project_id]["profiles"][0]
        self.assertEqual("opencode/other-free", saved["model"])
        self.assertEqual(7, saved["priority"])
        self.assertEqual(["low"], saved["risks"])
        free = next(a for a in self.client.agents if a["id"] == saved["agentId"])
        router_id = self.preset["projects"][project_id]["orchestratorAgentId"]
        router = next(a for a in self.client.agents if a["id"] == router_id)
        self.assertEqual("opencode/other-free", free["adapterConfig"]["model"])
        self.assertEqual("opencode/other-free", router["adapterConfig"]["model"])

    def test_disabled_requested_harnesses_are_reported_without_creating_agents(self):
        deployed = {}
        def capture(registry):
            deployed.update(deepcopy(registry))
            return "/code", "/registry.json", "sha", "sha"
        with patch("milestone2.scripts.automatic_entry_setup.deploy_public_runtime", side_effect=capture), \
                patch("milestone2.scripts.profile_readiness.qualify_available", side_effect=lambda profiles, _: (profiles, [])):
            configure(self.client, self.state, self.preset, apply=True)
        saved = next(iter(deployed["projects"].values()))["profiles"]
        disabled = {p["id"]: p for p in saved if p.get("enabled") is False}
        self.assertEqual({"claude", "cline", "command-code"}, set(disabled))
        self.assertTrue(all(p.get("qualified") is False for p in disabled.values()))
        self.assertEqual(1, sum(method == "POST" and path.endswith("/agents") for method, path, *_ in self.client.writes))

    def test_claude_profile_requires_matching_native_qualification_before_any_write(self):
        claude = next(p for p in self.preset["modelProfiles"] if p["id"] == "claude")
        claude.update(enabled=True, model="sonnet")
        configured = next(iter(self.preset["projects"].values()))
        aid, proof = str(uuid4()), str(uuid4())
        configured["profileBindings"] = {"claude": {"agentId": aid, "qualificationRunId": proof}}
        self.client.agents.append({"id": aid, "name": "Claude Developer", "companyId": COMPANY, "status": "idle", "adapterType": "claude_local",
                                   "adapterConfig": {"cwd": configured["cwd"], "model": "sonnet"}})
        request = self.client.request
        def api(method, path, body=None, **kwargs):
            if path == f"/api/heartbeat-runs/{proof}":
                return 200, {"id": proof, "agentId": aid, "companyId": COMPANY, "status": "succeeded",
                             "usageJson": {"model": "wrong"}, "runnerProfileJson": {"adapterDispatch": {"adapterType": "claude_local"}}}
            return request(method, path, body, **kwargs)
        self.client.request = api
        with self.assertRaisesRegex(ValueError, "qualification"):
            configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual([], self.client.writes)

    def test_legacy_usage_model_does_not_admit_claude(self):
        claude = next(p for p in self.preset["modelProfiles"] if p["id"] == "claude")
        claude.update(enabled=True, model="sonnet")
        configured = next(iter(self.preset["projects"].values()))
        aid, proof = str(uuid4()), str(uuid4())
        configured["profileBindings"] = {"claude": {"agentId": aid, "qualificationRunId": proof}}
        self.client.agents.append({"id": aid, "name": "Claude Developer", "companyId": COMPANY, "status": "idle", "adapterType": "claude_local",
                                   "adapterConfig": {"cwd": configured["cwd"], "model": "sonnet"}})
        request = self.client.request
        def api(method, path, body=None, **kwargs):
            if path == f"/api/heartbeat-runs/{proof}":
                return 200, {"id": proof, "agentId": aid, "companyId": COMPANY, "status": "succeeded",
                             "usageJson": {"model": "sonnet"}, "runnerProfileJson": {"adapterDispatch": {"adapterType": "claude_local"}}}
            return request(method, path, body, **kwargs)
        self.client.request = api
        deployed = {}
        def capture(registry):
            deployed.update(deepcopy(registry))
            return "/code", "/registry.json", "sha", "sha"
        with self.assertRaisesRegex(ValueError, "qualification"):
            configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual([], self.client.writes)
        self.assertEqual({}, deployed)

    def test_unsupported_enabled_harness_fails_before_any_write(self):
        next(p for p in self.preset["modelProfiles"] if p["id"] == "cline")["enabled"] = True
        with self.assertRaisesRegex(ValueError, "model|adapter|integrated"):
            configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual([], self.client.writes)

    def test_every_project_resumes_only_its_own_bootstrap_and_workflow_agents(self):
        two = preset(project("Alpha"), project("Beta"))
        client = FixtureClient(two)
        for agent in client.agents:
            agent["status"] = "paused"
        request = client.request
        def api(method, path, body=None, **kwargs):
            result = request(method, path, body, **kwargs)
            if method == "POST" and path.endswith("/agents"):
                result[1]["status"] = "paused"
                client.agents[-1]["status"] = "paused"
            return result
        client.request = api
        with patch("milestone2.scripts.profile_readiness.qualify_available", side_effect=lambda profiles, _: (profiles, [])):
            configure(client, self.state, two, apply=True)
        resumed = {path.split("/")[-2] for method, path, *_ in client.writes if method == "POST" and path.endswith("/resume")}
        self.assertEqual({a["id"] for a in client.agents}, resumed)


class FixtureClient:
    def __init__(self, configured):
        self.qualification = {"companyId": COMPANY, "status": "succeeded",
            "usageJson": {"model": "gpt-5.6-sol"},
            "runnerProfileJson": {"adapterDispatch": {"adapterType": "codex_local"}}}
        self.projects = {}
        self.agents = []
        self.writes = []
        for project_id, value in configured["projects"].items():
            self.projects[project_id] = {
                "id": project_id, "companyId": COMPANY,
                "workspaces": [{"cwd": value["cwd"]}],
            }
            for key in ("orchestratorAgentId", "developerAgentId", "validatorAgentId",
                        "reviewerAgentId", "qaAgentId"):
                agent_id = value[key]
                self.agents.append({
                    "id": agent_id, "companyId": COMPANY, "status": "idle",
                    "name": value["label"] + " Developer" if key == "developerAgentId" else key,
                    "role": "engineer", "title": key, "adapterType": "codex_local",
                    "adapterConfig": {"cwd": value["cwd"], "model": "gpt-5.6-sol"}, "metadata": {},
                })

    def request(self, method, path, body=None, **kwargs):
        if method == "GET" and "/native-provider-admission?projectId=" in path:
            agent = next(a for a in self.agents if a["id"] == path.split("/")[3])
            return 200, deepcopy(agent.get("nativeAdmissionState", {"schemaVersion": 1, "admitted": False}))
        if method == "GET" and path.startswith("/api/heartbeat-runs/"):
            return 200,deepcopy(self.qualification)
        if method == "GET" and path == f"/api/companies/{COMPANY}/agents":
            return 200, deepcopy(self.agents)
        if method == "GET" and path.startswith("/api/projects/"):
            return 200, deepcopy(self.projects[path.rsplit("/", 1)[1]])
        if method == "GET" and path.endswith("instructions-bundle/file?path=AGENTS.md"):
            return 200, {"content": "# Project instructions\n"}
        if method == "GET" and path.startswith("/api/agents/"):
            agent_id = path.rsplit("/", 1)[1]
            return 200, deepcopy(next(a for a in self.agents if a["id"] == agent_id))

        self.writes.append((method, path, deepcopy(body), deepcopy(kwargs)))
        if method == "POST" and path == f"/api/companies/{COMPANY}/agents":
            created_body = deepcopy(body)
            if any(a["name"] == created_body["name"] for a in self.agents):
                created_body["name"] += " 2"
            created_body["adapterConfig"].update({
                "instructionsFilePath": "/managed/AGENTS.md",
                "instructionsRootPath": "/managed",
                "instructionsEntryFile": "AGENTS.md",
                "instructionsBundleMode": "managed",
            })
            created = {"id": str(uuid4()), "companyId": COMPANY, "status": "idle", **created_body}
            self.agents.append(created)
            return 201, deepcopy(created)
        if method == "PATCH" and path.startswith("/api/agents/"):
            agent_id = path.rsplit("/", 1)[1]
            agent = next(a for a in self.agents if a["id"] == agent_id)
            agent.update(deepcopy(body))
            return 200, deepcopy(agent)
        if method == "PATCH" and path.startswith("/api/projects/"):
            project_id = path.rsplit("/", 1)[1]
            self.projects[project_id].update(deepcopy(body))
            return 200, deepcopy(self.projects[project_id])
        if method == "PUT" and path.endswith("/instructions-bundle/file"):
            return 200, {"ok": True}
        if method == "POST" and path.endswith("/resume"):
            return 200, {"ok": True}
        raise AssertionError((method, path, body, kwargs))


if __name__ == "__main__":
    unittest.main()
