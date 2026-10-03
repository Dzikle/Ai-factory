"""A discovery claim needs native command evidence, not just a model's answer."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40
ANSWERS = {"publicationModule": "milestone2.publish", "guide": "milestone2/PUBLISH.md",
           "preflightSubcommand": "preflight", "publicationSubcommand": "publish",
           "testModule": "milestone3.check", "developerMayPublish": False,
           "reviewerMayPublish": False, "ownerApprovalRequired": True,
           "preflightHelpExecuted": True}


class ScriptDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.run = {"id": "native-run", "status": "succeeded", "resultJson": {"summary": json.dumps(ANSWERS)},
                    "runnerProfileJson": {"adapterDispatch": {"adapterType": "opencode_local"}},
                    "contextSnapshot": {"paperclipWorkspace": {"gitHead": REVISION}}}
        self.event = {"type": "tool_use", "part": {"tool": "bash", "state": {
            "status": "completed", "input": {"command": "python3 -m milestone2.publish preflight --help"},
            "output": "usage: publish.py preflight [-h] --repo REPO --plan PLAN"}}}
        self.log_run_id = "native-run"

    def check(self, events=None):
        records = [{"stream": "stdout", "chunk": json.dumps(event) + "\n"}
                   for event in (events if events is not None else [self.event])]
        log = {"runId": self.log_run_id, "store": "local_disk", "logRef": "native-log",
               "nextOffset": 500, "content": "\n".join(json.dumps(row) for row in records)}
        for name, value in [("run", self.run), ("log", log)]:
            (self.directory / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        return subprocess.run([sys.executable, "-m", "milestone2.scripts.script_discovery_proof",
                               "--run", str(self.directory / "run.json"),
                               "--log", str(self.directory / "log.json"), "--revision", REVISION],
                              cwd=ROOT, capture_output=True, text=True, timeout=15)

    def test_accepts_correct_answer_with_native_help_execution(self):
        result = self.check()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("PASS", json.loads(result.stdout)["status"])
        self.assertEqual("python3 -m milestone2.publish preflight --help", json.loads(result.stdout)["observedCommand"])

    def test_model_claim_without_actual_tool_execution_is_rejected(self):
        result = self.check([])
        self.assertNotEqual(0, result.returncode)
        self.assertIn("execution", result.stderr.lower())

    def test_native_snapshot_can_pin_source_with_full_immutable_repo_ref(self):
        self.run["contextSnapshot"]["paperclipWorkspace"] = {"repoRef": REVISION}
        result = self.check()
        self.assertEqual(0, result.returncode, result.stderr)
        self.run["contextSnapshot"]["paperclipWorkspace"]["repoRef"] = "main"
        self.assertNotEqual(0, self.check().returncode)

    def test_another_runs_command_log_is_not_discovery_proof(self):
        self.log_run_id = "a-different-native-run"
        result = self.check()
        self.assertNotEqual(0, result.returncode)

    def test_echoing_command_or_failed_help_is_not_execution_proof(self):
        for key, value in [("command", "echo python3 -m milestone2.publish preflight --help"),
                           ("output", "PRIVATE_ERROR_SENTINEL"), ("status", "error")]:
            with self.subTest(key=key):
                event = copy.deepcopy(self.event)
                state = event["part"]["state"]
                (state["input"] if key == "command" else state)[key] = value
                result = self.check([event])
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn("PRIVATE_", result.stderr)

    def test_wrong_revision_or_adapter_cannot_prove_current_native_discovery(self):
        original = copy.deepcopy(self.run)
        for key in ("revision", "adapter", "status"):
            with self.subTest(key=key):
                self.run = copy.deepcopy(original)
                if key == "revision":
                    self.run["contextSnapshot"]["paperclipWorkspace"]["gitHead"] = "b" * 40
                elif key == "adapter":
                    self.run["runnerProfileJson"]["adapterDispatch"]["adapterType"] = "process"
                else:
                    self.run["status"] = "failed"
                result = self.check()
                self.assertNotEqual(0, result.returncode)

    def test_permission_confusion_and_boolean_coercion_are_rejected(self):
        for key, value in [("developerMayPublish", True), ("reviewerMayPublish", True),
                           ("ownerApprovalRequired", False), ("developerMayPublish", 0)]:
            with self.subTest(key=key):
                self.run["resultJson"]["summary"] = json.dumps({**ANSWERS, key: value})
                result = self.check()
                self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
