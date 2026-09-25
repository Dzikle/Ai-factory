"""OpenSearch request and failure behavior for the first projection slice."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from milestone1.opensearch_projection import (
    HttpClient,
    docs_index_definition,
    install_docs_index,
    reconcile_documents,
)

DOC_ID = "120a9f381db806512426505ed7dfb4f1d79ac822e78fa9efc12da110ad953588"


class Reader:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls: list[tuple] = []

    def request(self, method: str, path: str, body=None, **kwargs):
        self.calls.append((method, path, body))
        return self.responses.pop(0)


class Writer:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[tuple] = []

    def request(self, method: str, path: str, body=None, **kwargs):
        self.calls.append((method, path, body, kwargs))
        return self.response


class OpenSearchProjectionTests(unittest.TestCase):
    def test_http_client_sends_json_without_allowing_plaintext_remote_credentials(self) -> None:
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, self.headers.get("Authorization"), self.rfile.read(int(self.headers["Content-Length"]))))
                payload = b'{"acknowledged":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        client = HttpClient(f"http://127.0.0.1:{server.server_port}", "reader", "secret", insecure_localhost=True)
        self.assertEqual({"acknowledged": True}, client.request("POST", "/index/_search", {"size": 1}))
        self.assertEqual("/index/_search", received[0][0])
        self.assertEqual(b'{"size": 1}', received[0][2])
        self.assertTrue(received[0][1].startswith("Basic "))
        with self.assertRaises(ValueError):
            HttpClient("http://example.invalid:9200", "reader", "secret", insecure_localhost=True)
        with self.assertRaises(ValueError):
            HttpClient("https://example.invalid:9200?unexpected=1", "reader", "secret")

    def test_index_definition_has_versioned_aliases_and_filterable_provenance(self) -> None:
        definition = docs_index_definition()
        self.assertEqual({"ai_factory_docs": {}, "ai_factory_docs_write": {"is_write_index": True}}, definition["aliases"])
        properties = definition["mappings"]["properties"]
        for field in ("id", "project_id", "repository_id", "status", "source_system", "source_id", "source_revision", "authority"):
            self.assertEqual("keyword", properties[field]["type"])
        self.assertEqual("text", properties["content"]["type"])

    def test_install_creates_mapping_and_refuses_an_incompatible_existing_index(self) -> None:
        definition = docs_index_definition()
        compatible = Reader([
            {"acknowledged": True},
            {"ai_factory_docs_v1": {"mappings": definition["mappings"]}},
            {"ai_factory_docs_v1": {"aliases": definition["aliases"]}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs": {}}}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs_write": {"is_write_index": True}}}},
        ])
        install_docs_index(compatible)
        self.assertEqual(("PUT", "/ai_factory_docs_v1", definition), compatible.calls[0])

        incompatible = Reader([
            {"error": {"type": "resource_already_exists_exception"}},
            {"ai_factory_docs_v1": {"mappings": {"properties": {"id": {"type": "text"}}}}},
            {"ai_factory_docs_v1": {"aliases": definition["aliases"]}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs": {}}}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs_write": {"is_write_index": True}}}},
        ])
        with self.assertRaisesRegex(RuntimeError, "incompatible"):
            install_docs_index(incompatible)

    def test_install_refuses_alias_pointing_at_another_physical_index(self) -> None:
        definition = docs_index_definition()
        admin = Reader([
            {"error": {"type": "resource_already_exists_exception"}},
            {"ai_factory_docs_v1": {"mappings": definition["mappings"]}},
            {"ai_factory_docs_v1": {"aliases": definition["aliases"]}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs": {}}}, "ai_factory_docs_v0": {"aliases": {"ai_factory_docs": {}}}},
            {"ai_factory_docs_v1": {"aliases": {"ai_factory_docs_write": {"is_write_index": True}}}},
        ])
        with self.assertRaisesRegex(RuntimeError, "another physical index"):
            install_docs_index(admin)

    def test_reconcile_filters_own_project_and_emits_one_stable_upsert(self) -> None:
        document = {
            "id": DOC_ID, "project_id": "project-a", "repository_id": "repo-a",
            "path": "docs/a.md",
            "source_system": "git", "source_id": "repo-a:docs/a.md",
            "source_revision": "commit-2", "source_version": "blob-2",
            "status": "canonical", "canonical": True, "content": "new",
        }
        old = {**document, "source_revision": "commit-1", "source_version": "blob-1", "content": "old"}
        reader = Reader([{"hits": {"hits": [{"_source": old, "sort": [DOC_ID]}]}}])
        writer = Writer({"errors": False, "items": [{"index": {"_id": DOC_ID, "status": 200}}]})

        count = reconcile_documents(reader, writer, [document], "project-a", "repo-a", "commit-2")

        self.assertEqual(1, count)
        self.assertEqual("POST", reader.calls[0][0])
        self.assertEqual("/ai_factory_docs/_search", reader.calls[0][1])
        filters = reader.calls[0][2]["query"]["bool"]["filter"]
        self.assertIn({"term": {"project_id": "project-a"}}, filters)
        self.assertIn({"term": {"repository_id": "repo-a"}}, filters)
        self.assertIn({"term": {"source_system": "git"}}, filters)
        self.assertEqual("/_bulk?refresh=wait_for", writer.calls[0][1])
        lines = [json.loads(line) for line in writer.calls[0][2].splitlines()]
        self.assertEqual({"index": {"_index": "ai_factory_docs_write", "_id": DOC_ID}}, lines[0])
        self.assertEqual(document, lines[1])

    def test_noop_replay_issues_no_bulk_write(self) -> None:
        document = {"id": DOC_ID, "path": "docs/a.md", "project_id": "project-a", "repository_id": "repo-a", "source_system": "git", "source_id": "repo-a:docs/a.md", "status": "canonical"}
        reader = Reader([{"hits": {"hits": [{"_source": document, "sort": [DOC_ID]}]}}])
        writer = Writer({"errors": False})
        self.assertEqual(0, reconcile_documents(reader, writer, [document], "project-a", "repo-a", "commit-2"))
        self.assertEqual([], writer.calls)

    def test_malformed_search_response_fails_closed(self) -> None:
        reader = Reader([{"hits": {}}])
        writer = Writer({"errors": False})
        with self.assertRaisesRegex(RuntimeError, "malformed"):
            reconcile_documents(reader, writer, [], "project-a", "repo-a", "commit-2")
        self.assertEqual([], writer.calls)

    def test_search_after_reads_all_pages_before_retraction(self) -> None:
        first_page = [
            {"_source": {"id": f"doc-{number:03d}", "status": "stale"}, "sort": [f"doc-{number:03d}"]}
            for number in range(500)
        ]
        reader = Reader([{"hits": {"hits": first_page}}, {"hits": {"hits": []}}])
        writer = Writer({"errors": False})
        self.assertEqual(0, reconcile_documents(reader, writer, [], "project-a", "repo-a", "commit-2"))
        self.assertEqual(["doc-499"], reader.calls[1][2]["search_after"])
        self.assertEqual([], writer.calls)

    def test_bulk_item_failure_is_not_reported_as_success(self) -> None:
        document = {"id": DOC_ID, "path": "docs/a.md", "project_id": "project-a", "repository_id": "repo-a", "source_system": "git", "source_id": "repo-a:docs/a.md", "status": "canonical"}
        reader = Reader([{"hits": {"hits": []}}])
        writer = Writer({"errors": True, "items": [{"index": {"_id": DOC_ID, "status": 429, "error": {"type": "rejected_execution_exception"}}}]})
        with self.assertRaisesRegex(RuntimeError, DOC_ID):
            reconcile_documents(reader, writer, [document], "project-a", "repo-a", "commit-2")

    def test_rejects_mismatched_document_identity_before_any_search(self) -> None:
        document = {"id": "wrong-id", "path": "docs/a.md", "project_id": "project-a", "repository_id": "repo-a", "source_system": "git", "source_id": "repo-a:docs/a.md"}
        reader = Reader([])
        writer = Writer({"errors": False})
        with self.assertRaisesRegex(ValueError, "identity"):
            reconcile_documents(reader, writer, [document], "project-a", "repo-a", "commit-2")
        self.assertEqual([], reader.calls)
        self.assertEqual([], writer.calls)


if __name__ == "__main__":
    unittest.main()
