"""Historical advice must earn its place in bounded task context."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from milestone3.memory import MemPalace, projection_document, recall, validate_envelope


NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)


def lesson(blob="a" * 40):
    content = "Run tests in the pinned dependency environment; verify current Git first."
    digest = hashlib.sha256(content.encode()).hexdigest()
    return {"record": {
        "schema_version": 1, "memory_id": "pinned-tests-v1", "project_id": "ai-factory",
        "scope": "agent", "specialist_role": "developer", "kind": "lesson", "status": "active",
        "content_ref": "sha256:" + digest, "content_sha256": digest,
        "observed_at": "2026-09-28T00:00:00Z", "review_after": "2026-10-28T00:00:00Z",
        "retention_until": "2027-03-28T00:00:00Z", "supersedes": [],
        "source_refs": [{"source_system": "git", "source_id": "rules.md", "source_version": blob}],
    }, "content": content}


class Reader:
    def __init__(self, doc):
        self.doc = doc
        self.calls = []

    def request(self, method, path, body):
        self.calls.append((method, path, body))
        return {"hits": {"hits": [{"_source": self.doc}]}}


class Store:
    def __init__(self, envelope):
        self.envelope = envelope
        self.calls = []

    def get(self, drawer_id):
        self.calls.append(drawer_id)
        return deepcopy(self.envelope)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.cwd)], check=True)
        subprocess.run(["git", "-C", str(self.cwd), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.cwd), "config", "user.name", "Test"], check=True)
        (self.cwd / "rules.md").write_text("Current instructions\n")
        subprocess.run(["git", "-C", str(self.cwd), "add", "rules.md"], check=True)
        subprocess.run(["git", "-C", str(self.cwd), "commit", "-qm", "rules"], check=True)
        self.blob = subprocess.check_output(["git", "-C", str(self.cwd), "rev-parse", "HEAD:rules.md"], text=True).strip()
        self.envelope = lesson(self.blob)
        self.store = Store(self.envelope)
        self.reader = Reader(projection_document("drawer-1", self.envelope))

    def retrieve(self, **options):
        return recall(self.store, self.reader, cwd=self.cwd, project_id="ai-factory",
                      role="developer", query="test dependencies", now=NOW, **options)

    def test_verified_advice_is_bounded_labelled_and_separate_from_git(self):
        result = self.retrieve()
        self.assertEqual(result["status"], "used")
        self.assertEqual(result["memories"][0]["drawer_id"], "drawer-1")
        self.assertIn("Historical advice", result["prompt"])
        self.assertIn("Git", result["prompt"])
        self.assertIn(self.envelope["content"], result["prompt"])
        self.assertLessEqual(result["context_bytes"], 2400)
        self.assertGreater(result["estimated_tokens"], 0)
        method, path, body = self.reader.calls[0]
        self.assertEqual((method, path), ("POST", "/ai_factory_docs/_search"))
        self.assertIn({"term": {"source_system": "mempalace"}}, body["query"]["bool"]["filter"])
        self.assertIn({"term": {"project_id": "ai-factory"}}, body["query"]["bool"]["filter"])

    def test_stale_projection_does_not_reactivate_superseded_primary_memory(self):
        self.store.envelope["record"].update(status="superseded", superseded_by="new-lesson")
        result = self.retrieve()
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["prompt"], "")
        self.assertEqual(self.store.calls, ["drawer-1"])

    def test_other_project_or_role_is_not_disclosed_even_if_search_returns_it(self):
        for key, value in (("project_id", "other-project"), ("specialist_role", "reviewer")):
            with self.subTest(key=key):
                self.store.envelope = deepcopy(self.envelope)
                self.store.envelope["record"][key] = value
                self.assertEqual(self.retrieve()["prompt"], "")

    def test_changed_current_git_source_rejects_memory(self):
        (self.cwd / "rules.md").write_text("New instructions supersede old guidance\n")
        subprocess.run(["git", "-C", str(self.cwd), "add", "rules.md"], check=True)
        subprocess.run(["git", "-C", str(self.cwd), "commit", "-qm", "supersede"], check=True)
        self.assertEqual(self.retrieve()["prompt"], "")

    def test_dirty_current_source_rejects_memory_without_commit(self):
        (self.cwd / "rules.md").write_text("Uncommitted new instructions\n")
        self.assertEqual(self.retrieve()["prompt"], "")

    def test_assume_unchanged_flag_cannot_hide_modified_source(self):
        subprocess.run(["git", "-C", str(self.cwd), "update-index", "--assume-unchanged", "rules.md"], check=True)
        (self.cwd / "rules.md").write_text("Hidden uncommitted instructions\n")
        self.assertEqual(self.retrieve()["prompt"], "")

    def test_malformed_index_shapes_degrade_without_throwing(self):
        for response in ({"hits": {"hits": [{"_source": None}]}}, {"hits": None}, None):
            with self.subTest(response=response):
                self.reader.request = lambda *args, response=response: response
                result = self.retrieve()
                self.assertEqual(result["status"], "degraded")
                self.assertEqual(result["prompt"], "")

    def test_unverified_external_provenance_is_not_used(self):
        self.store.envelope["record"]["source_refs"].append({
            "source_system": "paperclip", "source_id": "task", "source_version": "decision"})
        self.reader.doc = projection_document("drawer-1", self.store.envelope)
        self.assertEqual(self.retrieve()["prompt"], "")
        result = self.retrieve(verify_external=lambda ref: ref["source_id"] == "task")
        self.assertEqual(result["status"], "used")

    def test_review_due_expired_or_future_memories_are_not_used(self):
        for field, value in (("review_after", "2026-09-27T00:00:00Z"),
                             ("retention_until", "2026-09-27T00:00:00Z"),
                             ("observed_at", "2026-09-29T00:00:00Z")):
            with self.subTest(field=field):
                self.store.envelope = deepcopy(self.envelope)
                self.store.envelope["record"][field] = value
                self.assertEqual(self.retrieve()["prompt"], "")

    def test_bad_digest_or_ref_is_rejected_before_projection(self):
        for key, value in (("content", "Forged advice"),):
            corrupted = deepcopy(self.envelope)
            corrupted[key] = value
            with self.assertRaises(ValueError):
                validate_envelope(corrupted)
        corrupted = deepcopy(self.envelope)
        corrupted["record"]["content_ref"] = "https://untrusted.example/lesson"
        with self.assertRaises(ValueError):
            projection_document("drawer-1", corrupted)

    def test_no_partial_context_escapes_if_primary_or_index_is_unavailable(self):
        for target in (self.store, self.reader):
            with self.subTest(target=type(target).__name__):
                name = "get" if target is self.store else "request"
                original = getattr(target, name)
                def unavailable(*args, **kwargs):
                    raise OSError("sensitive backend details")
                setattr(target, name, unavailable)
                result = self.retrieve()
                self.assertEqual(result["status"], "degraded")
                self.assertEqual(result["prompt"], "")
                self.assertNotIn("sensitive", json.dumps(result))
                setattr(target, name, original)

    def test_context_budget_rejects_whole_memory_not_truncated_provenance(self):
        result = self.retrieve(max_bytes=100)
        self.assertEqual(result["prompt"], "")
        self.assertEqual(result["context_bytes"], 0)

    def test_projection_is_metadata_only_and_cannot_become_canonical(self):
        doc = self.reader.doc
        self.assertFalse(doc["canonical"])
        self.assertEqual(doc["authority"], "historical")
        self.assertEqual(doc["source_uri"], "mempalace://drawer-1")
        self.assertNotIn(self.envelope["content"], doc["content"])


class MemPalaceBoundaryTests(unittest.TestCase):
    def test_same_logical_memory_cannot_supersede_itself(self):
        old, new = lesson(), lesson()
        new["record"]["supersedes"] = ["pinned-tests-v1"]
        store = MemPalace(None, writable=True)
        store.get = lambda drawer: deepcopy(old if drawer == "old" else new)
        with self.assertRaises(ValueError):
            store.supersede("old", "new")

    def test_completed_supersession_replay_survives_successor_supersession(self):
        old, new = lesson(), lesson()
        old["record"].update(status="superseded", superseded_by="pinned-tests-v2")
        new["record"].update(memory_id="pinned-tests-v2", status="superseded",
                            superseded_by="pinned-tests-v3", supersedes=["pinned-tests-v1"])
        store = MemPalace(None, writable=True)
        store.get = lambda drawer: deepcopy(old if drawer == "old" else new)
        self.assertEqual(store.supersede("old", "new"), old)

    def test_malformed_mcp_shapes_are_handled_errors(self):
        for response in (None, {"result": None}, {"result": {"content": [None]}},
                         {"result": {"content": [{"type": "text", "text": None}]}}):
            with self.subTest(response=response):
                class Transport:
                    def send(self, *args):
                        return response
                with self.assertRaises((RuntimeError, ValueError)):
                    MemPalace(Transport()).get("drawer-1")

    def test_read_only_adapter_cannot_issue_memory_mutations(self):
        class NeverCalled:
            def send(self, *args, **kwargs):
                raise AssertionError("Mutation reached transport")
        store = MemPalace(NeverCalled())
        with self.assertRaises(PermissionError):
            store.remember(lesson())
        with self.assertRaises(PermissionError):
            store.supersede("old", "new")


if __name__ == "__main__":
    unittest.main()
