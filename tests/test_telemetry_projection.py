from copy import deepcopy
import unittest
from unittest.mock import patch

from milestone4.project_telemetry import collect_documents, project


COMPANY = "f1251cc6-d826-4629-978c-ebcf3e6ba62a"
PROJECT = "856c35c2-b55a-4284-aa91-e7a627c1fe08"
ISSUE = "b83ef44c-09ab-4c92-8265-c946d85986d9"
ROSTER = {"schemaVersion": 1, "projectId": "ai-factory", "repositoryId": "ai-factory",
          "paperclipProjectId": PROJECT, "issues": ["AIF-49"]}


class Client:
    def __init__(self, issue=None):
        self.issue = issue or {"id": ISSUE, "companyId": COMPANY, "projectId": PROJECT,
                               "identifier": "AIF-49", "updatedAt": "2026-09-29T06:00:00Z"}

    def request(self, *args):
        return 200, self.issue


class TelemetryTests(unittest.TestCase):
    def test_native_scope_unknown_values_and_replay_are_preserved(self):
        report = {"observedAt": "now", "usage": {"reportedCostUsd": None, "knownReportedCostUsd": 0}}
        with patch("milestone4.project_telemetry.collect", return_value=report.copy()):
            first = collect_documents(Client(), {"companyId": COMPANY}, ROSTER)
        with patch("milestone4.project_telemetry.collect", return_value={**report, "observedAt": "later"}):
            second = collect_documents(Client(), {"companyId": COMPANY}, ROSTER)
        self.assertEqual(first, second)
        self.assertFalse(first[0]["canonical"])
        self.assertIn('"reportedCostUsd":null', first[0]["content"])
        self.assertNotIn('observedAt', first[0]["content"])

    def test_foreign_native_project_and_duplicate_roster_are_rejected(self):
        for client, roster in [(Client({"companyId": COMPANY, "projectId": ISSUE}), ROSTER),
                               (Client(), {**ROSTER, "issues": ["AIF-49", "AIF-49"]})]:
            with self.assertRaises(ValueError):
                collect_documents(client, {"companyId": COMPANY}, roster)

    def test_projection_replay_does_not_write(self):
        docs = [{"id": "one", "content": "native"}]
        class Reader:
            def request(self, *args):
                return {"hits": {"hits": [{"_id": "one", "_source": deepcopy(docs[0])}]}}
        self.assertEqual(project(Reader(), None, docs), 0)

    def test_bulk_failure_is_not_reported_as_success(self):
        class Reader:
            def request(self, *args):
                return {"hits": {"hits": []}}
        class Writer:
            def request(self, *args, **kwargs):
                return {"errors": True, "items": []}
        with self.assertRaises(RuntimeError):
            project(Reader(), Writer(), [{"id": "one"}])


if __name__ == "__main__":
    unittest.main()
