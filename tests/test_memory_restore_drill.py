import unittest
from unittest.mock import Mock, patch
import os

from milestone4.memory_restore_drill import (
    cleanup_plan,
    drawer_manifest,
    validate_page,
    validate_source_config,
    validate_tool_catalog,
    _wait_memory,
    server_write_denied,
)
import hashlib


def drawer(drawer_id, wing="ai-factory", room="engineering-lessons", content="private lesson"):
    envelope = {"record": {"memory_id": drawer_id, "project_id": wing, "scope": "project",
                           "status": "active", "content_sha256": hashlib.sha256(content.encode()).hexdigest()},
                "content": content}
    return {"drawer_id": drawer_id, "wing": wing, "room": room, "envelope": envelope}


class MemoryRestoreDrillPureTests(unittest.TestCase):
    def test_memory_readiness_uses_injected_connect_memory(self):
        expected = object()
        connect_memory = Mock(return_value=expected)
        with patch.dict(os.environ, {}, clear=True):
            self.assertIs(expected, _wait_memory("http://127.0.0.1:1234/mcp", "test-token",
                                                  timeout=1, connect=connect_memory))
            connect_memory.assert_called_once_with()
            self.assertEqual("http://127.0.0.1:1234/mcp", os.environ["AIF_MEMORY_URL"])
            self.assertEqual("test-token", os.environ["AIF_MEMORY_TOKEN"])

    def test_source_container_must_match_the_exact_offline_production_profile(self):
        source = {"State": {"Running": True}, "Image": "image-id",
                  "Config": {"Cmd": ["serve", "--host", "0.0.0.0", "--port", "8765",
                                      "--backend", "sqlite_exact", "--palace", "/data/palace_sqlite"],
                             "Env": ["MEMPALACE_BACKEND=sqlite_exact",
                                     "MEMPALACE_EMBEDDING_MODEL=embeddinggemma",
                                     "MEMPALACE_EMBEDDING_DEVICE=cpu", "MEMPALACE_EMBEDDING_THREADS=2",
                                     "MEMPALACE_MCP_IDLE_HOURS=0",
                                     "MEMPALACE_PALACE_PATH=/data/palace_sqlite", "HF_HUB_OFFLINE=1",
                                     "MEMPALACE_MCP_HTTP_TOKEN=secret"]},
                  "Mounts": [{"Destination": "/data", "Name": "aif-m0-mempalace-embeddinggemma-data"}]}
        self.assertEqual("secret", validate_source_config(source, "image-id"))
        for broken in ({**source, "Image": "other"},
                       {**source, "State": {"Running": False}},
                       {**source, "Mounts": []}):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                validate_source_config(broken, "image-id")

    def test_read_only_catalog_keeps_recall_and_excludes_mutations(self):
        tools = [{"name": name} for name in (
            "mempalace_search", "mempalace_get_drawer", "mempalace_list_drawers",
            "mempalace_status")]
        self.assertIn("mempalace_status", validate_tool_catalog(tools, require_readonly=True))
        with self.assertRaises(ValueError):
            validate_tool_catalog(tools + [{"name": "mempalace_hook_settings"}], require_readonly=True)
        with self.assertRaises(ValueError):
            validate_tool_catalog(tools + [{"name": "future_unknown_mutation"}], require_readonly=True)
        with self.assertRaises(ValueError):
            validate_tool_catalog([{"name": "mempalace_search"}], require_readonly=True)

    def test_write_denial_requires_unknown_method_or_explicit_read_only_semantics(self):
        self.assertTrue(server_write_denied({"error": {"code": -32601, "message": "Method not found"}}))
        self.assertTrue(server_write_denied({"result": {"isError": True, "content": [
            {"type": "text", "text": "Unknown tool: mempalace_add_drawer"}]}}))
        self.assertFalse(server_write_denied({"error": {"code": -32602, "message": "Invalid params"}}))
        self.assertFalse(server_write_denied({"result": {"isError": True, "content": [
            {"type": "text", "text": "Invalid params: missing content"}]}}))
        self.assertFalse(server_write_denied({"result": {"isError": True, "content": [
            {"type": "text", "text": "Write refused in read-only mode"}]}}))
        self.assertTrue(server_write_denied({"error": {"code": -32003,
            "message": "Server is in read-only mode; this tool is disabled",
            "data": {"tool": "mempalace_add_drawer"}}}))
        self.assertFalse(server_write_denied({"error": {"code": -32003,
            "message": "Unauthorized", "data": {"tool": "mempalace_add_drawer"}}}))

    def test_page_shape_is_bounded_and_offset_consistent(self):
        page = {"total": 1, "count": 1, "offset": 0, "limit": 100,
                "drawers": [drawer("drawer-a")]}
        self.assertEqual([drawer("drawer-a")], validate_page(page, 0))
        for bad in (
            {**page, "count": 2},
            {**page, "offset": 1},
            {**page, "limit": 101},
            {**page, "drawers": [drawer(str(i)) for i in range(101)]},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_page(bad, 0)

    def test_manifest_accepts_only_expected_wing_and_room(self):
        rows = [drawer("one"), drawer("two")]
        result = drawer_manifest(rows)
        self.assertEqual(["one", "two"], [item["drawer_id"] for item in result])
        for row in (drawer("foreign", wing="other"), drawer("wrong-room", room="general")):
            with self.subTest(row=row), self.assertRaises(ValueError):
                drawer_manifest([row])

    def test_manifest_rejects_duplicate_or_malformed_drawers(self):
        for rows in ([drawer("same"), drawer("same")], [],
                     [{"drawer_id": "x", "wing": "ai-factory", "room": "engineering-lessons"}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                drawer_manifest(rows)

    def test_receipt_manifest_contains_digests_but_not_lesson_content(self):
        lesson = "marker-private-lesson-content"
        item = drawer_manifest([drawer("one", content=lesson)])[0]
        self.assertNotIn(lesson, repr(item))
        self.assertEqual(64, len(item["content_sha256"]))

    def test_cleanup_only_targets_resources_confirmed_created(self):
        plan = cleanup_plan({"container": True, "volume": False, "token_file": True})
        self.assertEqual(["container", "token_file"], [item[0] for item in plan])
        self.assertNotIn("source", repr(plan))


if __name__ == "__main__":
    unittest.main()
