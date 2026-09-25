"""Opt-in live OpenSearch smoke for the Git document projection.

Uses the dedicated local Milestone 0 cluster, but writes only the new
ai_factory_docs_v1 index. It never deletes or changes Milestone 0 indexes.
"""

import os
from pathlib import Path
import unittest

import yaml

from milestone1.git_projection import collect_snapshot
from milestone1.opensearch_projection import HttpClient, install_docs_index, reconcile_documents


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("AIF_PROJECTION_LIVE_URL"), "live OpenSearch URL not configured")
class GitProjectionLiveTests(unittest.TestCase):
    def test_committed_docs_replay_without_duplication(self) -> None:
        password = os.environ["AIF_PROJECTION_LIVE_ADMIN_PASSWORD"]
        client = HttpClient(
            os.environ["AIF_PROJECTION_LIVE_URL"], "admin", password,
            insecure_localhost=True,
        )
        install_docs_index(client)
        overlay = yaml.safe_load((ROOT / "autonomy/projects/examples/ai-factory.v1.yaml").read_text(encoding="utf-8"))
        repository = overlay["repositories"][0]
        snapshot = collect_snapshot(
            ROOT, project_id=overlay["project_id"], repository_id=repository["id"],
            remote=repository["remote"], canonical_paths=repository["canonical_paths"],
        )
        self.assertGreater(len(snapshot), 10)
        first = reconcile_documents(client, client, snapshot, overlay["project_id"], repository["id"], snapshot[0]["source_revision"])
        self.assertGreaterEqual(first, 0)
        second = reconcile_documents(client, client, snapshot, overlay["project_id"], repository["id"], snapshot[0]["source_revision"])
        self.assertEqual(0, second)
        count = client.request("POST", "/ai_factory_docs/_count", {
            "query": {"bool": {"filter": [
                {"term": {"project_id": overlay["project_id"]}},
                {"term": {"repository_id": repository["id"]}},
                {"term": {"source_system": "git"}},
            ]}},
        })
        self.assertEqual(len(snapshot), count["count"])
        result = client.request("POST", "/ai_factory_docs/_search", {
            "query": {"term": {"source_id": "ai-factory:AGENTS.md"}}, "size": 1,
        })
        self.assertEqual(1, result["hits"]["total"]["value"])
        indexed = result["hits"]["hits"][0]["_source"]
        original = next(doc for doc in snapshot if doc["source_id"] == "ai-factory:AGENTS.md")
        self.assertEqual(original["source_revision"], indexed["source_revision"])
        self.assertEqual(original["content_sha256"], indexed["content_sha256"])

        if os.environ.get("AIF_PROJECTION_REBUILD") == "1":
            # Only remove this dedicated, rebuildable test index when it holds
            # exactly the committed snapshot we just verified.
            total = client.request("GET", "/ai_factory_docs_v1/_count")["count"]
            self.assertEqual(len(snapshot), total)
            client.request("DELETE", "/ai_factory_docs_v1")
            install_docs_index(client)
            rebuilt = reconcile_documents(client, client, snapshot, overlay["project_id"], repository["id"], snapshot[0]["source_revision"])
            self.assertEqual(len(snapshot), rebuilt)
            self.assertEqual(len(snapshot), client.request("GET", "/ai_factory_docs_v1/_count")["count"])


if __name__ == "__main__":
    unittest.main()
