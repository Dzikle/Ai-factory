"""Local configuration tests for the live Paperclip admission driver."""

import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("paperclip_admission.py")


class AdmissionStateIsolationTest(unittest.TestCase):
    def test_isolated_state_and_url_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_text(
                json.dumps({"boardApiKey": "test-only", "baseUrl": "http://127.0.0.1:13100"}),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "AIF_M0_PAPERCLIP_STATE_PATH": str(state_path),
                    "AIF_M0_PAPERCLIP_BASE_URL": "http://127.0.0.1:13101",
                    "AIF_M0_PAPERCLIP_CONTAINER": "aif-m0-paperclip-fork-paperclip-fork-1",
                },
            ):
                spec = importlib.util.spec_from_file_location("paperclip_admission_test", SCRIPT)
                assert spec and spec.loader
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                state, client = module.state_client()

            self.assertEqual(module.STATE_PATH, state_path)
            self.assertEqual(state["baseUrl"], "http://127.0.0.1:13101")
            self.assertEqual(client.base_url, "http://127.0.0.1:13101")
            self.assertEqual(client.token, "test-only")
            self.assertEqual(module.CONTAINER_NAME, "aif-m0-paperclip-fork-paperclip-fork-1")

    def test_repeated_recovery_accepts_cancelled_preparing_run_without_lease(self) -> None:
        spec = importlib.util.spec_from_file_location("paperclip_admission_test", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = {
            "id": "cancelled-run",
            "status": "cancelled",
            "errorCode": "cancelled",
            "executionStage": "preparing",
            "startedAt": "2026-09-25T10:54:50.011Z",
            "finishedAt": "2026-09-25T10:54:50.086Z",
            "contextSnapshot": {"issueId": "issue"},
            "resultJson": {"startupCancellation": {"beforeNativeSelection": False}},
        }
        state = {
            "companyId": "company",
            "processCrashIssueId": "issue",
            "orphanIssueId": "issue",
            "recoveryScenarioRunIds": ["cancelled-run"],
            "verifiedLeaseReleases": {},
        }

        class FakeClient:
            def request(self, method: str, path: str) -> tuple[int, object]:
                if (method, path) == ("GET", "/api/companies/company/heartbeat-runs?limit=100"):
                    return 200, [run]
                if (method, path) == ("GET", "/api/heartbeat-runs/cancelled-run"):
                    return 200, run
                if (method, path) == ("GET", "/api/issues/issue"):
                    return 200, {"executionRunId": None, "checkoutRunId": None}
                raise AssertionError(f"unexpected request: {method} {path}")

        output = io.StringIO()
        with patch.object(module, "state_client", return_value=(state, FakeClient())), \
             patch.object(module, "save_state"), redirect_stdout(output):
            module.recovery_report()

        report = json.loads(output.getvalue())
        self.assertEqual(
            report["allSourceAndSuccessorLeasesReleased"],
            [{"runId": "cancelled-run", "runStatus": "cancelled", "noLeaseAcquired": True}],
        )
        self.assertTrue(report["releaseReceiptsUnchanged"])


if __name__ == "__main__":
    unittest.main()
