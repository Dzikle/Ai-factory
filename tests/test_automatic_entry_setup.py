"""Automatic task-entry provisioning safety and readiness tests."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

from milestone2.scripts.automatic_entry_setup import MODEL, configure


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
        "projects": {str(uuid4()): value for value in projects},
    }


class AutomaticEntrySetupTests(unittest.TestCase):
    def setUp(self):
        self.preset = preset(project("Alpha"))
        self.client = FixtureClient(self.preset)
        self.state = {"companyId": COMPANY}

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
            self.assertEqual(MODEL, profiles[0]["model"])
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
