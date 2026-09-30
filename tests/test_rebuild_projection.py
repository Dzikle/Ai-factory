import json
import unittest
from unittest.mock import patch

from milestone4.rebuild_projection import index_snapshot, memory_snapshot, replace


class Transport:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def send(self, method, params):
        self.calls.append((method, params))
        return {"result": {"content": [{"type": "text", "text": json.dumps(next(self.pages))}]}}


class Store:
    def __init__(self, pages):
        self.client = Transport(pages)

    def get(self, drawer):
        return {"record": {"project_id": "ai-factory"}, "drawer": drawer}


class Admin:
    def __init__(self):
        self.calls = []

    def request(self, method, path, body=None, **kwargs):
        self.calls.append((method, path, body))
        if method == "POST" and path.startswith("/_bulk"):
            count = len(body.splitlines()) // 2
            return {"errors": False, "items": [{"index": {"status": 201}}] * count}
        return {}


class MissingReader:
    def request(self, *args, **kwargs):
        return {"error": {"type": "index_not_found_exception"}}


def page(drawers, total=None, offset=0):
    return {"total": len(drawers) if total is None else total, "count": len(drawers),
            "offset": offset, "drawers": [{"drawer_id": value, "wing": "ai-factory",
                                           "room": "engineering-lessons"} for value in drawers]}


class RebuildTests(unittest.TestCase):
    def test_enumeration_is_primary_scoped_and_bounded(self):
        store = Store([page(["one"], total=2), page(["two"], total=2, offset=1)])
        with patch("milestone4.rebuild_projection.projection_document", side_effect=lambda key, value: {"id": key}):
            self.assertEqual(memory_snapshot(store, "ai-factory"), [{"id": "one"}, {"id": "two"}])
        self.assertEqual(store.client.calls[1][1]["arguments"], {
            "wing": "ai-factory", "room": "engineering-lessons", "limit": 100, "offset": 1})

    def test_enumeration_rejects_scope_duplicates_missing_and_changing_pages(self):
        wrong = page(["one"])
        wrong["drawers"][0]["wing"] = "other"
        cases = [[wrong], [page(["one", "one"])], [page([], total=1)],
                 [page(["one"], total=2), page(["two"], total=3, offset=1)], [page([], total=201)]]
        for pages in cases:
            with self.subTest(pages=pages), self.assertRaises(ValueError), patch(
                "milestone4.rebuild_projection.projection_document", side_effect=lambda key, value: {"id": key}
            ):
                memory_snapshot(Store(pages), "ai-factory")

    def test_inventory_does_not_silently_truncate(self):
        class Reader:
            def request(self, *args):
                return {"hits": {"total": {"relation": "gte", "value": 1000}, "hits": []}}
        with self.assertRaises(ValueError):
            index_snapshot(Reader())

    def test_exact_rebuild_and_loss_probe(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        admin = Admin()
        with patch("milestone4.rebuild_projection.index_snapshot", side_effect=[docs, docs]), patch(
            "milestone4.rebuild_projection.install_docs_index"
        ) as install:
            result = replace(admin, MissingReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                             verify_sources=lambda: True)
        self.assertTrue(result["exactPrimaryReadback"])
        self.assertEqual(install.call_count, 2)
        self.assertEqual(admin.calls[0][:2], ("DELETE", "/ai_factory_docs_v1"))
        self.assertEqual(result["sources"], {"git": 1})

    def test_cross_scope_or_changed_primary_never_deletes(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        for existing, verify in [([{**docs[0], "source_system": "unknown"}], True), (docs, False)]:
            admin = Admin()
            with patch("milestone4.rebuild_projection.index_snapshot", return_value=existing), patch(
                "milestone4.rebuild_projection.install_docs_index"
            ), self.assertRaises(ValueError):
                replace(admin, MissingReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                        verify_sources=lambda: verify)
            self.assertFalse(admin.calls)

    def test_readback_mismatch_is_not_success(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        with patch("milestone4.rebuild_projection.index_snapshot", side_effect=[docs, [], []]), patch(
            "milestone4.rebuild_projection.install_docs_index"
        ), self.assertRaises(RuntimeError):
            replace(Admin(), MissingReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                    verify_sources=lambda: True)

    def test_unexpected_loss_response_recovers_once_but_does_not_pass(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        class DeniedReader:
            def request(self, *args, **kwargs):
                raise RuntimeError("HTTP 403")
        admin = Admin()
        with patch("milestone4.rebuild_projection.index_snapshot", side_effect=[docs, docs]), patch(
            "milestone4.rebuild_projection.install_docs_index"
        ), self.assertRaisesRegex(RuntimeError, "failed but projection recovered"):
            replace(admin, DeniedReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                    verify_sources=lambda: True)
        self.assertEqual(sum(call[0] == "DELETE" for call in admin.calls), 1)
        self.assertEqual(sum(call[1].startswith("/_bulk") for call in admin.calls), 1)

    def test_partial_bulk_recovered_without_second_delete(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        admin = Admin()
        original = admin.request
        failures = [True]
        def request(method, path, *args, **kwargs):
            result = original(method, path, *args, **kwargs)
            if path.startswith("/_bulk") and failures:
                failures.pop()
                return {"errors": True, "items": [{"index": {"status": 500}}]}
            return result
        admin.request = request
        with patch("milestone4.rebuild_projection.index_snapshot", side_effect=[docs, docs]), patch(
            "milestone4.rebuild_projection.install_docs_index"
        ), self.assertRaisesRegex(RuntimeError, "failed but projection recovered"):
            replace(admin, MissingReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                    verify_sources=lambda: True)
        self.assertEqual(sum(call[0] == "DELETE" for call in admin.calls), 1)
        self.assertEqual(sum(call[1].startswith("/_bulk") for call in admin.calls), 2)

    def test_non_object_api_response_still_attempts_bounded_recovery(self):
        docs = [{"id": "one", "project_id": "ai-factory", "repository_id": "ai-factory", "source_system": "git"}]
        class MalformedReader:
            def request(self, *args, **kwargs):
                return []
        admin = Admin()
        with patch("milestone4.rebuild_projection.index_snapshot", side_effect=[docs, docs]), patch(
            "milestone4.rebuild_projection.install_docs_index"
        ), self.assertRaisesRegex(RuntimeError, "failed but projection recovered"):
            replace(admin, MalformedReader(), docs, project_id="ai-factory", repository_id="ai-factory",
                    verify_sources=lambda: True)
        self.assertEqual(sum(call[0] == "DELETE" for call in admin.calls), 1)


if __name__ == "__main__":
    unittest.main()
