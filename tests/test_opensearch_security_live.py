"""Opt-in effective-permission probe against the pinned local OpenSearch cluster."""

import json
import os
from pathlib import Path
import secrets
import unittest
from uuid import uuid4

import yaml

from milestone1.git_projection import collect_snapshot
from milestone1.opensearch_projection import DOCS_INDEX, DOCS_READ_ALIAS, DOCS_WRITE_ALIAS, HttpClient, install_docs_index, reconcile_documents
from milestone1.opensearch_security import docs_reader_role, docs_writer_role


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("AIF_PROJECTION_LIVE_URL"), "live OpenSearch URL not configured")
class DocsSecurityLiveTests(unittest.TestCase):
    def test_real_reader_writer_profiles_allow_only_intended_actions(self) -> None:
        url = os.environ["AIF_PROJECTION_LIVE_URL"]
        admin = HttpClient(url, "admin", os.environ["AIF_PROJECTION_LIVE_ADMIN_PASSWORD"], insecure_localhost=True)
        install_docs_index(admin)

        suffix = uuid4().hex[:12]
        outside_index = f"aif-m1-security-outside-{suffix}"
        admin.request("PUT", f"/{outside_index}")
        self.addCleanup(admin.request, "DELETE", f"/{outside_index}", expected=(200, 404))
        reader_role = f"aif-m1-docs-reader-{suffix}"
        writer_role = f"aif-m1-docs-writer-{suffix}"
        reader_user = f"aif-m1-docs-reader-{suffix}"
        writer_user = f"aif-m1-docs-writer-{suffix}"
        reader_password = secrets.token_urlsafe(32)
        writer_password = secrets.token_urlsafe(32)

        for name, payload in ((reader_role, docs_reader_role()), (writer_role, docs_writer_role())):
            path = f"/_plugins/_security/api/roles/{name}"
            admin.request("PUT", path, payload)
            self.addCleanup(admin.request, "DELETE", path, expected=(200, 404))
        for name, role, password in (
            (reader_user, reader_role, reader_password),
            (writer_user, writer_role, writer_password),
        ):
            path = f"/_plugins/_security/api/internalusers/{name}"
            admin.request("PUT", path, {
                "password": password, "backend_roles": [], "opendistro_security_roles": [role],
            })
            self.addCleanup(admin.request, "DELETE", path, expected=(200, 404))

        reader = HttpClient(url, reader_user, reader_password, insecure_localhost=True)
        writer = HttpClient(url, writer_user, writer_password, insecure_localhost=True)
        overlay = yaml.safe_load((ROOT / "autonomy/projects/examples/ai-factory.v1.yaml").read_text(encoding="utf-8"))
        repository = overlay["repositories"][0]
        snapshot = collect_snapshot(
            ROOT, project_id=overlay["project_id"], repository_id=repository["id"],
            remote=repository["remote"], canonical_paths=repository["canonical_paths"],
        )
        document = next(item for item in snapshot if item["source_id"] == "ai-factory:AGENTS.md")
        bulk_body = "\n".join((
            json.dumps({"index": {"_index": DOCS_WRITE_ALIAS, "_id": document["id"]}}),
            json.dumps(document), "",
        ))

        bulk_result = writer.request("POST", "/_bulk?refresh=wait_for", bulk_body, content_type="application/x-ndjson")
        self.assertFalse(bulk_result["errors"], bulk_result["items"])
        search = reader.request("POST", f"/{DOCS_READ_ALIAS}/_search", {
            "size": 1, "query": {"term": {"id": document["id"]}},
        })
        self.assertEqual(1, search["hits"]["total"]["value"])
        self.assertEqual(document["content_sha256"], search["hits"]["hits"][0]["_source"]["content_sha256"])
        reconcile_documents(reader, writer, snapshot, overlay["project_id"], repository["id"], document["source_revision"])
        self.assertEqual(0, reconcile_documents(reader, writer, snapshot, overlay["project_id"], repository["id"], document["source_revision"]))

        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            reader.request("POST", "/_bulk", bulk_body, content_type="application/x-ndjson")
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            writer.request("POST", f"/{DOCS_READ_ALIAS}/_search", {"size": 0})
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            reader.request("POST", f"/{outside_index}/_search", {"size": 0})
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            reader.request("GET", f"/{DOCS_INDEX}/_mapping")
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            writer.request("GET", f"/{DOCS_INDEX}/_mapping")
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            writer.request("DELETE", f"/{DOCS_WRITE_ALIAS}/_doc/{document['id']}")
        outside_bulk = "\n".join((
            json.dumps({"index": {"_index": outside_index, "_id": "permission-probe"}}),
            json.dumps({"content": "must not be written"}), "",
        ))
        outside_result = writer.request("POST", "/_bulk", outside_bulk, content_type="application/x-ndjson")
        self.assertEqual(403, outside_result["items"][0]["index"]["status"])
        delete_probe = json.dumps({"delete": {"_index": DOCS_WRITE_ALIAS, "_id": f"permission-probe-{suffix}"}}) + "\n"
        delete_result = writer.request(
            "POST", "/_bulk", delete_probe, content_type="application/x-ndjson",
        )
        self.assertEqual(403, delete_result["items"][0]["delete"]["status"])


if __name__ == "__main__":
    unittest.main()
