"""Task CLI boundary: native policy payloads, readable status, no second engine."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPANY = "00000000-0000-0000-0000-000000000010"
PROJECT = "00000000-0000-0000-0000-000000000020"
AGENTS = [f"00000000-0000-0000-0000-00000000000{i}" for i in range(1, 5)]
ISSUE = "00000000-0000-0000-0000-000000000030"


class TaskCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.requests = []
        self.agents = {agent: {"id": agent, "companyId": COMPANY, "status": "idle"} for agent in AGENTS}
        self.issue = {
            "id": ISSUE, "identifier": "AIF-47", "companyId": COMPANY,
            "title": "Projection preview", "status": "in_review",
            "description": "PRIVATE_DESCRIPTION_SENTINEL",
            "executionPolicy": {"stages": [{"id": "tests"}, {"id": "review"}, {"id": "approval"}]},
            "executionState": {"currentStageIndex": 2, "currentStageType": "approval",
                               "completedStageIds": ["tests", "review"]},
        }
        self.post_status = 201
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, value):
                content = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def do_GET(self):
                test.requests.append(("GET", self.path, None))
                if self.path.startswith("/api/agents/"):
                    self.respond(200, test.agents[self.path.rsplit("/", 1)[1]])
                elif self.path == f"/api/projects/{PROJECT}":
                    self.respond(200, {"id": PROJECT, "companyId": COMPANY})
                elif self.path == "/api/issues/AIF-47":
                    self.respond(200, test.issue)
                else:
                    self.respond(404, {"error": "unexpected path"})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                test.requests.append(("POST", self.path, body))
                if self.path != f"/api/companies/{COMPANY}/issues":
                    self.respond(404, {"error": "unexpected write"})
                elif test.post_status != 201:
                    self.respond(test.post_status, {"error": "PRIVATE_ERROR_SENTINEL"})
                else:
                    self.respond(201, {**body, "id": ISSUE, "companyId": COMPANY, "identifier": "AIF-48"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        Thread(target=self.server.serve_forever, kwargs={"poll_interval": .05}, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.state = {"baseUrl": f"http://127.0.0.1:{self.server.server_port}",
                      "companyId": COMPANY, "userId": "owner-1", "boardApiKey": "PRIVATE_TOKEN_SENTINEL"}
        self.workflow = {"projectId": PROJECT, "developerAgentId": AGENTS[0],
                         "validatorAgentId": AGENTS[1], "reviewerAgentId": AGENTS[2]}
        self.task = {"title": "Add useful task command", "description": "Acceptance: submit and show progress.",
                     "requestKey": "task-command-1"}

    def cli(self, *arguments):
        for name, value in (("state", self.state), ("workflow", self.workflow), ("task", self.task)):
            (self.directory / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-m", "milestone2.task", "--state", str(self.directory / "state.json"),
             "--json", *arguments], cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def submit(self, *flags):
        return self.cli("submit", "--workflow", str(self.directory / "workflow.json"),
                        "--task", str(self.directory / "task.json"), *flags)

    def test_dry_run_builds_native_policy_without_network_or_credentials(self):
        result = self.submit("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("backlog", payload["status"])
        self.assertEqual(PROJECT, payload["projectId"])
        self.assertEqual(AGENTS[0], payload["assigneeAgentId"])
        self.assertEqual("task-command-1", payload["idempotencyKey"])
        self.assertEqual([
            {"type": "review", "participants": [{"type": "agent", "agentId": AGENTS[1]}]},
            {"type": "review", "participants": [{"type": "agent", "agentId": AGENTS[2]}]},
            {"type": "approval", "participants": [{"type": "user", "userId": "owner-1"}]},
        ], payload["executionPolicy"]["stages"])
        self.assertEqual([], self.requests)
        self.assertNotIn("PRIVATE_TOKEN_SENTINEL", result.stdout + result.stderr)

    def test_submission_creates_one_backlog_issue_in_paperclip(self):
        result = self.submit()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("AIF-48", json.loads(result.stdout)["identifier"])
        writes = [request for request in self.requests if request[0] == "POST"]
        self.assertEqual(1, len(writes))
        self.assertEqual(f"/api/companies/{COMPANY}/issues", writes[0][1])
        self.assertEqual("backlog", writes[0][2]["status"])

    def test_start_submits_todo_without_running_a_local_scheduler(self):
        result = self.submit("--start")
        self.assertEqual(0, result.returncode, result.stderr)
        writes = [request for request in self.requests if request[0] == "POST"]
        self.assertEqual(1, len(writes))
        self.assertEqual("todo", writes[0][2]["status"])

    def test_start_does_not_silently_unpause_or_bypass_budget_stops(self):
        self.agents[AGENTS[2]]["status"] = "paused"
        result = self.submit("--start")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("paused", result.stderr)
        self.assertFalse(any(request[0] != "GET" for request in self.requests))

    def test_qa_adds_a_distinct_native_participant(self):
        self.workflow["qaAgentId"] = AGENTS[3]
        result = self.submit("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        stages = json.loads(result.stdout)["executionPolicy"]["stages"]
        self.assertEqual(4, len(stages))
        self.assertEqual(AGENTS[3], stages[2]["participants"][0]["agentId"])

    def test_self_review_is_rejected_before_submission(self):
        self.workflow["reviewerAgentId"] = AGENTS[0]
        result = self.submit()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], self.requests)

    def test_cross_company_agent_is_rejected_before_submission(self):
        self.agents[AGENTS[1]]["companyId"] = "other-company"
        result = self.submit()
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(any(request[0] == "POST" for request in self.requests))

    def test_missing_request_key_is_rejected_before_network(self):
        del self.task["requestKey"]
        result = self.submit()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], self.requests)

    def test_status_reads_native_approval_progress_without_private_content(self):
        result = self.cli("status", "AIF-47")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("in_review", report["status"])
        self.assertEqual("Owner approval", report["currentStage"])
        self.assertEqual(2, report["completedStages"])
        self.assertEqual(3, report["totalStages"])
        self.assertEqual([("GET", "/api/issues/AIF-47", None)], self.requests)
        self.assertNotIn("PRIVATE_DESCRIPTION_SENTINEL", result.stdout)
        self.assertNotIn("PRIVATE_TOKEN_SENTINEL", result.stdout + result.stderr)

    def test_status_rejects_an_issue_from_another_company(self):
        self.issue["companyId"] = "other-company"
        result = self.cli("status", "AIF-47")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Projection preview", result.stdout)

    def test_submission_error_is_redacted_and_not_automatically_retried(self):
        self.post_status = 503
        result = self.submit()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("503", result.stderr)
        self.assertNotIn("PRIVATE_ERROR_SENTINEL", result.stderr)
        self.assertNotIn("PRIVATE_TOKEN_SENTINEL", result.stderr)
        self.assertEqual(1, sum(request[0] == "POST" for request in self.requests))


if __name__ == "__main__":
    unittest.main()
