from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from milestone4.read_only_eval import EXPECTED, answer, measurement, run, verified_context


class ReadOnlyEvalTests(unittest.TestCase):
    def test_only_the_exact_typed_answer_is_judged(self):
        self.assertEqual(answer(json.dumps(EXPECTED)), EXPECTED)
        self.assertEqual(answer("Earlier native text part.\n\n" + json.dumps(EXPECTED)), EXPECTED)
        with self.assertRaises(ValueError):
            answer(json.dumps(EXPECTED) + "\ntrailing unjudged output")
        for invalid in ({**EXPECTED, "extra": True}, {**EXPECTED, "memoryCanOverrideGit": "false"}, []):
            with self.assertRaises(ValueError):
                answer(json.dumps(invalid))

    def test_complete_native_usage_preserves_reported_free_cost(self):
        run = {"id": "run", "agentId": "agent", "status": "succeeded",
               "usageJson": {"inputTokens": 123, "cachedInputTokens": 10, "outputTokens": 50, "costUsd": 0},
               "startedAt": "2026-09-30T16:00:00Z", "finishedAt": "2026-09-30T16:00:01Z",
               "resultJson": {"result": json.dumps(EXPECTED)}}
        observed = measurement(run)
        self.assertEqual(observed["checksPassed"], 8)
        self.assertEqual(observed["usage"]["costUsd"], 0)
        self.assertEqual(observed["runtimeMs"], 1000)
        for key, value in (("status", "cancelled"), ("usageJson", {}),
                           ("usageJson", {**run["usageJson"], "usageCompleteness": "partial"})):
            bad = deepcopy(run)
            bad[key] = value
            with self.assertRaises(ValueError):
                measurement(bad)

    def test_canonical_context_rejects_stale_projection_before_execution(self):
        doc = {"id": "doc", "path": "docs/truth.md", "content": "Paperclip owns task state",
               "source_revision": "a" * 40, "content_sha256": "b" * 64}
        reader = Mock()
        reader.request.return_value = {"hits": {"hits": [{"_source": {**doc, "content": "stale"}}]}}
        with patch("milestone4.read_only_eval.collect_snapshot", return_value=[doc] * 3):
            with self.assertRaises(ValueError):
                verified_context(Path("."), reader, "a" * 40)

    def test_revision_mismatch_stops_before_context_or_native_mutation(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root / ".milestone0") as temporary:
            with patch("milestone4.read_only_eval.assert_quiescent"), \
                    patch("milestone4.read_only_eval.subprocess.check_output", return_value="a" * 40), \
                    patch("milestone4.read_only_eval.verified_context") as context, \
                    patch("milestone4.read_only_eval.Client") as client:
                with self.assertRaises(ValueError):
                    run("unused", Path(temporary) / "new", Mock(), "actor", expected_revision="b" * 40)
                context.assert_not_called()
                client.assert_not_called()

    def test_pause_failure_still_restores_configuration_and_checks_quiescence(self):
        root = Path(__file__).resolve().parents[1]
        original = {"cwd": "original", "env": {}}
        runtime = {"heartbeat": {"enabled": False}}
        client = Mock()
        def request(method, path, body=None, **kwargs):
            if method == "GET" and path == "/api/agents/actor":
                return 200, {"id": "actor", "companyId": "company", "status": "paused",
                             "adapterType": "opencode_local", "adapterConfig": original, "runtimeConfig": runtime}
            if method == "GET":
                return 200, {"allowedToolNames": ["SearchIndexTool"]}
            if path.endswith("/pause"):
                raise RuntimeError("pause failed")
            if path.endswith("/issues"):
                return 201, {"id": "issue", "identifier": "AIF-TEST"}
            if path.endswith("/wakeup"):
                return 202, {"id": "run"}
            return 200, {}
        client.request.side_effect = request
        with tempfile.TemporaryDirectory(dir=root / ".milestone0") as temporary:
            output = Path(temporary) / "new"
            with patch("milestone4.read_only_eval.assert_quiescent") as quiet, \
                    patch("milestone4.read_only_eval.subprocess.check_output", return_value="a" * 40), \
                    patch("milestone4.read_only_eval.verified_context", return_value="canonical"), \
                    patch("milestone4.read_only_eval.docker"), \
                    patch("milestone4.read_only_eval.read_object", return_value={
                        "baseUrl": "http://localhost", "boardApiKey": "test", "companyId": "company", "userId": "owner"}), \
                    patch("milestone4.read_only_eval.Client", return_value=client), \
                    patch("milestone4.read_only_eval.wait_run", side_effect=ValueError("failed native run")):
                with self.assertRaisesRegex(RuntimeError, "cleanup/quiescence"):
                    run("unused", output, Mock(), "actor")
                self.assertEqual(quiet.call_count, 2)
                client.request.assert_any_call("PATCH", "/api/agents/actor", {
                    "adapterConfig": original, "runtimeConfig": runtime, "replaceAdapterConfig": True})
                self.assertFalse((output / "receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
