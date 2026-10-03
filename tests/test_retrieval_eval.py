"""Judged retrieval must be bounded, scoped, and honest about stale projection."""

import unittest

from milestone4.retrieval_eval import evaluate, run


REV = "a" * 40
OLD = "b" * 40


def hit(path, *, revision=REV, project="ai-factory", repository="ai-factory"):
    return {"_id": path, "_source": {
        "path": path, "project_id": project, "repository_id": repository,
        "source_system": "git", "status": "canonical", "canonical": True,
        "source_revision": revision, "source_id": repository + ":" + path,
        "content_sha256": "c" * 64,
    }}


class Reader:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def request(self, method, path, body):
        self.calls.append((method, path, body))
        return {"hits": {"hits": self.pages.pop(0)}}


class RetrievalEvalTests(unittest.TestCase):
    def suite(self):
        return {"schemaVersion": 1, "projectId": "ai-factory",
                "repositoryId": "ai-factory", "cases": [
                    {"id": "authority", "query": "task run source of truth",
                     "relevantPaths": ["docs/architecture/STATE_AND_STORAGE.md"]},
                    {"id": "capabilities", "query": "least privilege MCP capability",
                     "relevantPaths": ["docs/architecture/MCP_AND_CAPABILITY_MODEL.md"]},
                ]}

    def test_judged_ranks_freshness_and_hard_query_scope(self):
        reader = Reader([
            [hit("AGENTS.md"), hit("docs/architecture/STATE_AND_STORAGE.md")],
            [hit("docs/architecture/MCP_AND_CAPABILITY_MODEL.md", revision=OLD)],
        ])
        report = evaluate(reader, self.suite(), expected_revision=REV, k=3)
        self.assertEqual(2, report["casesEvaluated"])
        self.assertEqual(1.0, report["recallAtK"])
        self.assertEqual(.75, report["meanReciprocalRank"])
        self.assertEqual(1, report["staleRelevantHits"])
        self.assertEqual([2, 1], [case["firstRelevantRank"] for case in report["cases"]])
        self.assertEqual(2, len(reader.calls))
        for method, path, body in reader.calls:
            self.assertEqual(("POST", "/ai_factory_docs/_search"), (method, path))
            self.assertEqual(3, body["size"])
            self.assertEqual([{"term": {"project_id": "ai-factory"}},
                              {"term": {"repository_id": "ai-factory"}},
                              {"term": {"source_system": "git"}},
                              {"term": {"status": "canonical"}},
                              {"term": {"canonical": True}}], body["query"]["bool"]["filter"])
            self.assertEqual(["path", "project_id", "repository_id", "source_system",
                              "status", "canonical", "source_revision", "source_id",
                              "content_sha256"], body["_source"])

    def test_cross_project_result_is_rejected_not_counted(self):
        reader = Reader([[hit("docs/architecture/STATE_AND_STORAGE.md", project="other")], []])
        with self.assertRaisesRegex(ValueError, "scope"):
            evaluate(reader, self.suite(), expected_revision=REV)

    def test_evaluation_answer_keys_are_excluded_from_queries_and_results(self):
        reader = Reader([[], []])
        evaluate(reader, self.suite(), expected_revision=REV)
        for _, _, body in reader.calls:
            self.assertEqual([{"prefix": {"path": "autonomy/evals/"}}], body["query"]["bool"].get("must_not"))
        with self.assertRaisesRegex(ValueError, "scope"):
            evaluate(Reader([[hit("autonomy/evals/git-docs-v1.json")]]), self.suite(), expected_revision=REV)

    def test_empty_and_unjudged_cases_do_not_create_fake_quality(self):
        suite = self.suite()
        suite["cases"][0]["relevantPaths"] = []
        with self.assertRaisesRegex(ValueError, "relevant"):
            evaluate(Reader([]), suite, expected_revision=REV)

    def test_duplicate_results_and_bad_revision_are_rejected(self):
        target = hit("docs/architecture/STATE_AND_STORAGE.md")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate(Reader([[target, target]]), self.suite(), expected_revision=REV)
        target["_source"]["source_revision"] = "not-a-revision"
        with self.assertRaisesRegex(ValueError, "provenance"):
            evaluate(Reader([[target]]), self.suite(), expected_revision=REV)

    def test_malformed_hits_container_fails_with_a_public_validation_error(self):
        class BrokenReader:
            def request(self, *_args):
                return {"hits": []}

        with self.assertRaisesRegex(ValueError, "Malformed"):
            evaluate(BrokenReader(), self.suite(), expected_revision=REV)

    def test_promotion_thresholds_reject_missing_or_stale_relevance(self):
        suite = self.suite()
        suite["thresholds"] = {"recallAtK": 1, "meanReciprocalRank": .5,
                               "staleRelevantHits": 0}
        report = evaluate(Reader([[hit("docs/architecture/STATE_AND_STORAGE.md")], []]),
                          suite, expected_revision=REV)
        self.assertFalse(report["passesThresholds"])
        report = evaluate(Reader([[hit("docs/architecture/STATE_AND_STORAGE.md")],
                                 [hit("docs/architecture/MCP_AND_CAPABILITY_MODEL.md")]]),
                          suite, expected_revision=REV)
        self.assertTrue(report["passesThresholds"])
        report = evaluate(Reader([[hit("docs/architecture/STATE_AND_STORAGE.md")],
                                 [hit("docs/architecture/MCP_AND_CAPABILITY_MODEL.md", revision=OLD)]]),
                          suite, expected_revision=REV)
        self.assertFalse(report["passesThresholds"])

    def test_live_entry_rejects_admin_or_missing_reader_before_network(self):
        import json
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            suite = Path(directory) / "suite.json"
            suite.write_text(json.dumps(self.suite()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reader"):
                run(suite, REV, environ={})
            with self.assertRaisesRegex(ValueError, "non-admin"):
                run(suite, REV, environ={"AIF_DOCS_URL": "http://127.0.0.1:1",
                                          "AIF_DOCS_READER_USER": "admin",
                                          "AIF_DOCS_READER_PASSWORD": "private"})


def cited(path, *, revision=REV):
    row = hit(path, revision=revision)
    row["_source"]["citation"] = f"git:{revision[:12]}:{path}"
    return row


class RetrievalEvalV2Tests(unittest.TestCase):
    def suite(self):
        return {"schemaVersion": 2, "projectId": "ai-factory",
                "repositoryId": "ai-factory", "cases": [
                    {"id": "authority", "query": "task run source of truth",
                     "queryType": "canonical_lookup", "expectedSources": ["git"],
                     "requiredAuthority": "canonical", "requireFresh": True,
                     "relevantPaths": ["docs/architecture/STATE_AND_STORAGE.md"]},
                    {"id": "memory", "query": "past retrieval failure lessons",
                     "queryType": "historical_lookup", "expectedSources": ["git"],
                     "requiredAuthority": "historical", "requireFresh": False,
                     "relevantPaths": ["docs/architecture/MCP_AND_CAPABILITY_MODEL.md"]},
                ]}

    def test_v2_reports_ranked_recall_citations_and_authority(self):
        reader = Reader([
            [cited("AGENTS.md"), cited("docs/architecture/STATE_AND_STORAGE.md")],
            [hit("docs/architecture/MCP_AND_CAPABILITY_MODEL.md")],
        ])
        report = evaluate(reader, self.suite(), expected_revision=REV, k=5)
        self.assertEqual(2, report["schemaVersion"])
        self.assertEqual(0.5, report["recallAt1"])
        self.assertEqual(1.0, report["recallAt3"])
        self.assertEqual(1.0, report["recallAt5"])
        self.assertEqual(0, report["cases"][0]["authorityViolations"])
        self.assertEqual(1, report["cases"][1]["authorityViolations"])
        self.assertEqual(1, report["missingCitations"])
        self.assertTrue(report["cases"][0]["requireFresh"])
        for _, _, body in reader.calls:
            self.assertIn("citation", body["_source"])

    def test_v1_suites_keep_schema_version_1_reports(self):
        reader = Reader([[hit("docs/architecture/STATE_AND_STORAGE.md")], []])
        report = evaluate(reader, {"schemaVersion": 1, "projectId": "ai-factory",
                                   "repositoryId": "ai-factory", "cases": [
                                       {"id": "authority", "query": "task run source of truth",
                                        "relevantPaths": ["docs/architecture/STATE_AND_STORAGE.md"]},
                                       {"id": "capabilities", "query": "least privilege",
                                        "relevantPaths": ["docs/architecture/MCP_AND_CAPABILITY_MODEL.md"]}]},
                          expected_revision=REV, k=3)
        self.assertEqual(1, report["schemaVersion"])
        self.assertNotIn("recallAt1", report)


if __name__ == "__main__":
    unittest.main()
