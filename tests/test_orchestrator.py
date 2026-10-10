"""Run-scoped native Orchestrator planning and handoff contract tests."""
import json
import unittest
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from copy import deepcopy
from uuid import uuid4

from milestone2.scripts.orchestrator import execute


COMPANY, OWNER, ORCHESTRATOR, DEVELOPER, VALIDATOR, REVIEWER, QA, PROJECT, ISSUE, RUN = [
    str(uuid4()) for _ in range(10)
]


def fixture():
    bindings = {
        "companyId": COMPANY,
        "ownerUserId": OWNER,
        "projects": {
            PROJECT: {
                "orchestratorAgentId": ORCHESTRATOR,
                "developerAgentId": DEVELOPER,
                "validatorAgentId": VALIDATOR,
                "reviewerAgentId": REVIEWER,
                "qaAgentId": QA,
                "profiles": [
                    {"id": "cheap", "agentId": DEVELOPER, "model": "vendor/free",
                     "adapterType": "codex_local", "qualified": True, "tier": "free"},
                    {"id": "strong", "agentId": DEVELOPER, "model": "vendor/paid",
                     "adapterType": "codex_local", "qualified": True, "tier": "subscription"},
                ],
            }
        },
    }
    issue = {"id": ISSUE, "companyId": COMPANY, "projectId": PROJECT,
             "assigneeAgentId": ORCHESTRATOR, "status": "in_progress",
             "executionRunId": RUN, "executionPolicy": None, "workMode": "standard", "statusVersion": 7}
    agents = {agent_id: {"id": agent_id, "companyId": COMPANY, "status": "idle", "adapterType": "codex_local"}
              for agent_id in (ORCHESTRATOR, DEVELOPER, VALIDATOR, REVIEWER, QA)}
    agents[ORCHESTRATOR]["status"] = "running"
    plan = {"kind": "coding", "summary": "Implement bounded change", "acceptance": ["Works"],
            "risk": "normal", "ux": True}
    return bindings, issue, agents, plan


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.bindings, self.issue, self.agents, self.plan = fixture()
        self.client = MockClient(self.issue, self.agents)
        self.context = {"taskId": ISSUE, "agentId": ORCHESTRATOR, "companyId": COMPANY, "runId": RUN}

    def run_plan(self, plan=None, bindings=None):
        return execute(self.client, self.context, bindings or self.bindings, plan or self.plan)

    def test_coding_handoff_saves_versioned_plan_and_exact_native_policy(self):
        result = self.run_plan()
        doc = self.client.documents[ISSUE, "plan"]
        saved = json.loads(doc["body"])
        patch = self.client.issue_patches[-1]
        self.assertEqual("markdown", doc["format"])
        self.assertEqual(1, saved["schemaVersion"])
        self.assertEqual(RUN, saved["runId"])
        self.assertEqual(DEVELOPER, patch["assigneeAgentId"])
        self.assertEqual("todo", patch["status"])
        self.assertEqual([VALIDATOR, REVIEWER, QA, OWNER], [
            stage["participants"][0].get("agentId", stage["participants"][0].get("userId"))
            for stage in patch["executionPolicy"]["stages"]])
        self.assertEqual({"adapterConfig": {"model": "vendor/free"}},
                         patch["assigneeAdapterOverrides"])
        self.assertEqual("handed_off", result["status"])

    def test_analysis_is_recorded_then_answered_without_execution_policy(self):
        plan = {"kind": "analysis", "summary": "Inspect the issue", "acceptance": [],
                "risk": "low", "ux": False, "answer": "The issue is understood."}
        result = self.run_plan(plan)
        self.assertIn((ISSUE, "plan"), self.client.documents)
        self.assertEqual({"status": "done", "comment": plan["answer"], "expectedStatusVersion": 7}, self.client.issue_patches[-1])
        self.assertEqual("answered", result["status"])

    def test_native_ask_analysis_is_allowed_but_plan_has_no_policy(self):
        self.client.issue["workMode"] = "ask"
        self.run_plan({"kind": "analysis", "summary": "Inspect", "acceptance": [],
                      "risk": "low", "ux": False, "answer": "Done."})
        self.assertIsNone(self.client.issue.get("executionPolicy"))

    def test_replay_does_not_repeat_handoff_write(self):
        self.run_plan()
        writes = len(self.client.writes)
        result = self.run_plan()
        self.assertEqual(writes, len(self.client.writes))
        self.assertEqual("replayed", result["status"])

    def test_requested_profile_must_be_qualified_and_bound_to_project_developer(self):
        self.plan["modelProfile"] = "unknown"
        with self.assertRaises(ValueError):
            self.run_plan()
        self.assertEqual([], self.client.writes)

    def test_high_risk_prefers_subscription_and_accepts_only_allowed_request(self):
        self.plan.update(risk="high", modelProfile="strong")
        self.run_plan()
        self.assertEqual("vendor/paid", self.client.issue_patches[-1]["assigneeAdapterOverrides"]["adapterConfig"]["model"])

    def test_high_risk_fails_closed_when_subscription_is_unavailable(self):
        self.plan["risk"] = "high"
        self.bindings["projects"][PROJECT]["profiles"][1]["qualified"] = False
        with self.assertRaisesRegex(ValueError, "subscription"):
            self.run_plan()
        self.assertEqual([], self.client.writes)

    def test_ux_false_omits_qa_stage(self):
        self.plan["ux"] = False
        self.run_plan()
        stages = self.client.issue_patches[-1]["executionPolicy"]["stages"]
        self.assertEqual([VALIDATOR, REVIEWER, OWNER], [
            stage["participants"][0].get("agentId", stage["participants"][0].get("userId")) for stage in stages])

    def test_user_facing_plan_requires_a_qa_binding(self):
        del self.bindings["projects"][PROJECT]["qaAgentId"]
        with self.assertRaisesRegex(ValueError, "QA"):
            self.run_plan()
        self.assertEqual([], self.client.writes)

    def test_bad_binding_run_owner_status_or_preexisting_policy_has_no_writes(self):
        for index in range(6):
            bindings, issue, agents, plan = fixture()
            client = MockClient(issue, agents)
            context = {"taskId": ISSUE, "agentId": ORCHESTRATOR, "companyId": COMPANY, "runId": RUN}
            (client.issue.update(executionPolicy={"stages": []}) if index == 0 else
             client.issue.update(executionRunId=str(uuid4())) if index == 1 else
             client.issue.update(status="todo") if index == 2 else
             client.issue.update(assigneeAgentId=str(uuid4())) if index == 3 else
             bindings.update(companyId=str(uuid4())) if index == 4 else
             client.agents[REVIEWER].update(status="terminated"))
            with self.subTest(index=index), self.assertRaises(ValueError):
                execute(client, context, bindings, plan)
            self.assertEqual([], client.writes)

    def test_existing_conflicting_plan_and_changed_issue_after_handoff_are_never_overwritten(self):
        self.run_plan()
        old_body = self.client.documents[ISSUE, "plan"]["body"]
        self.plan["summary"] = "Different"
        with self.assertRaises(ValueError):
            self.run_plan()
        self.assertEqual(old_body, self.client.documents[ISSUE, "plan"]["body"])

    def test_replay_refuses_owner_changes_to_assignee_or_review_policy(self):
        self.run_plan()
        writes = len(self.client.writes)
        self.client.issue["assigneeAgentId"] = REVIEWER
        with self.assertRaisesRegex(ValueError, "ownership or policy"):
            self.run_plan()
        self.assertEqual(writes, len(self.client.writes))

    def test_plan_text_and_shape_are_strictly_bounded(self):
        for update in ({"summary": "x" * 5001}, {"acceptance": ["x" * 2001]},
                       {"answer": " "}, {"kind": "other"}, {"extra": True}):
            with self.subTest(update=next(iter(update))):
                plan = deepcopy(self.plan)
                plan.update(update)
                with self.assertRaises(ValueError):
                    self.run_plan(plan)
        self.assertEqual([], self.client.writes)

    def test_agent_company_and_active_status_are_checked_before_write(self):
        self.client.agents[QA]["companyId"] = str(uuid4())
        with self.assertRaises(ValueError):
            self.run_plan()
        self.assertEqual([], self.client.writes)

    def test_ask_and_planning_never_become_coding(self):
        for mode in ("ask", "planning"):
            self.client.issue["workMode"] = mode
            with self.assertRaises(ValueError):
                self.run_plan()
        self.assertEqual([], self.client.writes)

    def test_native_adapter_binding_can_differ_from_default_developer(self):
        free = str(uuid4())
        self.bindings["projects"][PROJECT]["profiles"][0].update(agentId=free, adapterType="opencode_local")
        self.client.agents[free] = {"id": free, "companyId": COMPANY, "status": "idle", "adapterType": "opencode_local"}
        self.run_plan()
        self.assertEqual(free, self.client.issue["assigneeAgentId"])

    def test_paused_free_binding_falls_back_without_mutating_an_agent(self):
        free = str(uuid4())
        self.bindings["projects"][PROJECT]["profiles"][0].update(agentId=free, adapterType="opencode_local")
        self.client.agents[free] = {"id": free, "companyId": COMPANY, "status": "paused", "adapterType": "opencode_local"}
        self.run_plan()
        saved = json.loads(self.client.documents[ISSUE, "plan"]["body"])
        self.assertEqual("strong", saved["selectedProfile"]["id"])
        self.assertTrue(all(path.startswith(f"/api/issues/{ISSUE}") for _, path, _ in self.client.writes))

    def test_profile_must_match_the_actual_native_adapter(self):
        self.bindings["projects"][PROJECT]["profiles"][0]["adapterType"] = "opencode_local"
        self.run_plan()
        self.assertEqual("vendor/paid", self.client.issue["assigneeAdapterOverrides"]["adapterConfig"]["model"])

    def test_no_qualified_profile_fails_closed_without_plan_or_handoff(self):
        for profiles in ([], [{"id": "lost", "qualified": False}]):
            self.bindings["projects"][PROJECT]["profiles"] = profiles
            with self.subTest(profiles=profiles), self.assertRaisesRegex(ValueError, "qualified"):
                self.run_plan()
            self.assertEqual([], self.client.writes)

    def test_trusted_launcher_ignores_project_module_and_sitecustomize(self):
        helper = Path(__file__).resolve().parents[1] / "milestone2/scripts/orchestrator.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "milestone2/scripts"
            package.mkdir(parents=True)
            for path in (root / "sitecustomize.py", root / "milestone2/__init__.py",
                         package / "__init__.py", package / "orchestrator.py"):
                path.write_text("raise RuntimeError('PROJECT_SHADOW_EXECUTED')\n")
            result = subprocess.run([sys.executable, "-I", str(helper), "--help"],
                                    cwd=root, capture_output=True, text=True, timeout=10,
                                    env={**os.environ, "PYTHONPATH": str(root)})
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("--bindings", result.stdout)
            self.assertNotIn("PROJECT_SHADOW_EXECUTED", result.stdout + result.stderr)

    def test_crash_after_plan_persistence_can_resume_under_a_new_run(self):
        original_request = self.client.request
        def fail_patch(method, path, body=None):
            if method == "PATCH":
                raise ConnectionError("controller lost before patch")
            return original_request(method, path, body)
        self.client.request = fail_patch
        with self.assertRaises(ConnectionError):
            self.run_plan()
        original_body = self.client.documents[ISSUE, "plan"]["body"]
        self.context["runId"] = str(uuid4())
        self.client.issue["executionRunId"] = self.context["runId"]
        self.client.request = original_request
        result = self.run_plan()
        self.assertEqual("handed_off", result["status"])
        self.assertEqual(original_body, self.client.documents[ISSUE, "plan"]["body"])
        self.assertEqual(1, sum(method == "PUT" for method, _, _ in self.client.writes))

    def test_pending_handoff_revalidates_persisted_profile_binding(self):
        original_request = self.client.request
        def fail_patch(method, path, body=None):
            if method == "PATCH":
                raise ConnectionError("controller lost before patch")
            return original_request(method, path, body)
        self.client.request = fail_patch
        with self.assertRaises(ConnectionError):
            self.run_plan()
        self.client.request = original_request
        self.client.agents[DEVELOPER]["adapterType"] = "opencode_local"
        writes = len(self.client.writes)
        with self.assertRaisesRegex(ValueError, "qualified"):
            self.run_plan()
        self.assertEqual(writes, len(self.client.writes))

    def test_handoff_has_a_native_optimistic_ownership_guard(self):
        self.run_plan()
        self.assertEqual(7, self.client.issue_patches[-1]["expectedStatusVersion"])


class MockClient:
    def __init__(self, issue, agents):
        self.issue = deepcopy(issue)
        self.agents = deepcopy(agents)
        self.documents = {}
        self.writes = []
        self.issue_patches = []
        self.last_result = None

    def request(self, method, path, body=None):
        if method == "GET" and path == f"/api/issues/{ISSUE}":
            return deepcopy(self.issue)
        if method == "GET" and path == f"/api/companies/{COMPANY}/agents":
            return deepcopy(list(self.agents.values()))
        if method == "GET" and path.startswith("/api/agents/"):
            return deepcopy(self.agents[path.rsplit("/", 1)[1]])
        if method == "GET" and path.startswith(f"/api/issues/{ISSUE}/documents/"):
            name = path.rsplit("/", 1)[1]
            if (ISSUE, name) not in self.documents:
                from milestone0.scripts.paperclip_admission import ApiError
                raise ApiError("GET", path, 404, {})
            return deepcopy(self.documents[ISSUE, name])
        if method == "PUT" and path == f"/api/issues/{ISSUE}/documents/plan":
            self.writes.append((method, path, deepcopy(body)))
            self.documents[ISSUE, "plan"] = {**deepcopy(body), "latestRevisionId": "revision-1"}
            return deepcopy(self.documents[ISSUE, "plan"])
        if method == "PATCH" and path == f"/api/issues/{ISSUE}":
            self.writes.append((method, path, deepcopy(body)))
            self.issue_patches.append(deepcopy(body))
            self.issue.update(deepcopy(body))
            if body.get("status") == "todo":
                self.issue["executionRunId"] = None
            self.last_result = {"status": "handed_off"}
            return deepcopy(self.issue)
        raise AssertionError((method, path, body))


if __name__ == "__main__":
    unittest.main()
