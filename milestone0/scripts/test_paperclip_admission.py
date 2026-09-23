"""Local configuration tests for the live Paperclip admission driver."""

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
