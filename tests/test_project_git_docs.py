"""One-shot command contract: committed overlay, separated ACLs, replay."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from milestone1 import project_git_docs


class SearchClient:
    def __init__(self, documents: dict):
        self.documents = documents
        self.calls = []

    def request(self, method, path, body=None, **_kwargs):
        self.calls.append((method, path))
        if method != "POST" or path != "/ai_factory_docs/_search":
            raise AssertionError("reader used outside search alias")
        hits = [
            {"_source": document, "sort": [doc_id]}
            for doc_id, document in sorted(self.documents.items())
            if document["project_id"] == body["query"]["bool"]["filter"][0]["term"]["project_id"]
        ]
        return {"hits": {"hits": hits}}


class BulkClient:
    def __init__(self, documents: dict):
        self.documents = documents
        self.calls = []

    def request(self, method, path, body=None, **_kwargs):
        self.calls.append((method, path))
        if method != "POST" or path != "/_bulk?refresh=wait_for":
            raise AssertionError("writer used outside bulk endpoint")
        lines = [json.loads(line) for line in body.splitlines()]
        for header, document in zip(lines[::2], lines[1::2]):
            self.documents[header["index"]["_id"]] = document
        return {"errors": False}


class ProjectGitDocsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.test")
        self.git("config", "user.name", "Fixture")
        (self.root / "docs").mkdir()
        (self.root / "docs/one.md").write_text("# One\nFirst\n", encoding="utf-8")
        (self.root / "overlay.yaml").write_text(
            "schema_version: 1\nproject_id: example\nrepositories:\n"
            "  - id: source\n    remote: https://example.test/source.git\n"
            "    canonical_paths: [docs/]\n",
            encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.documents = {}
        self.reader = SearchClient(self.documents)
        self.writer = BulkClient(self.documents)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def test_one_shot_replays_without_second_write(self):
        first = project_git_docs.project_once(
            self.root, "overlay.yaml", "source", self.reader, self.writer
        )
        self.assertEqual(1, first["writes"])
        self.assertEqual(1, len(self.documents))
        self.assertEqual(0, project_git_docs.project_once(
            self.root, "overlay.yaml", "source", self.reader, self.writer
        )["writes"])
        self.assertEqual(1, len(self.writer.calls))
        self.assertTrue(all(path == "/ai_factory_docs/_search" for _, path in self.reader.calls))
        self.assertEqual("# One\nFirst\n", next(iter(self.documents.values()))["content"])

    def test_accepts_a_canonical_file_path(self):
        (self.root / "overlay.yaml").write_text(
            "schema_version: 1\nproject_id: example\nrepositories:\n"
            "  - id: source\n    remote: https://example.test/source.git\n"
            "    canonical_paths: [docs/one.md]\n",
            encoding="utf-8",
        )
        self.git("add", "overlay.yaml")
        self.git("commit", "-qm", "use canonical file path")

        result = project_git_docs.project_once(
            self.root, "overlay.yaml", "source", self.reader, self.writer
        )

        self.assertEqual(1, result["documents"])
        self.assertEqual(1, result["writes"])

    def test_overlay_is_read_from_committed_git_not_uncommitted_file(self):
        (self.root / "overlay.yaml").write_text("not: the committed overlay\n", encoding="utf-8")
        self.assertEqual(1, project_git_docs.project_once(
            self.root, "overlay.yaml", "source", self.reader, self.writer
        )["writes"])

    def test_rejects_missing_repository_and_unsafe_overlay_path(self):
        for path, repo_id in (("overlay.yaml", "missing"), ("../overlay.yaml", "source")):
            with self.subTest(path=path, repo_id=repo_id), self.assertRaises(ValueError):
                project_git_docs.project_once(self.root, path, repo_id, self.reader, self.writer)
        self.assertEqual([], self.reader.calls)
        self.assertEqual([], self.writer.calls)

    def test_rejects_any_canonical_path_without_an_eligible_document(self):
        (self.root / "overlay.yaml").write_text(
            "schema_version: 1\nproject_id: example\nrepositories:\n"
            "  - id: source\n    remote: https://example.test/source.git\n"
            "    canonical_paths: [docs/, typo/]\n",
            encoding="utf-8",
        )
        self.git("add", "overlay.yaml")
        self.git("commit", "-qm", "add invalid canonical path")

        with self.assertRaisesRegex(ValueError, "typo/"):
            project_git_docs.project_once(
                self.root, "overlay.yaml", "source", self.reader, self.writer
            )

        self.assertEqual([], self.reader.calls)
        self.assertEqual([], self.writer.calls)

    def test_requires_separate_non_admin_runtime_credentials(self):
        env = {
            "AIF_DOCS_URL": "https://127.0.0.1:19200",
            "AIF_DOCS_READER_USER": "reader",
            "AIF_DOCS_READER_PASSWORD": "reader-secret",
            "AIF_DOCS_WRITER_USER": "writer",
            "AIF_DOCS_WRITER_PASSWORD": "writer-secret",
        }
        created = []

        def client(*args, **kwargs):
            created.append((args, kwargs))
            return self.reader if args[1] == "reader" else self.writer

        with patch.object(project_git_docs, "HttpClient", side_effect=client):
            result = project_git_docs.run(["--repo-root", str(self.root), "--overlay", "overlay.yaml", "--repository", "source"], env)
        self.assertEqual(1, result["writes"])
        self.assertEqual(["reader", "writer"], [call[0][1] for call in created])
        self.assertNotEqual(created[0][0][2], created[1][0][2])
        for missing in ("AIF_DOCS_WRITER_PASSWORD", "AIF_DOCS_READER_USER"):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                project_git_docs.run(["--repo-root", str(self.root), "--overlay", "overlay.yaml", "--repository", "source"], {k: v for k, v in env.items() if k != missing})
        with self.assertRaises(ValueError):
            project_git_docs.run(["--repo-root", str(self.root), "--overlay", "overlay.yaml", "--repository", "source"], {**env, "AIF_DOCS_WRITER_USER": "admin"})

    def test_projection_failure_propagates(self):
        class FailedWriter(BulkClient):
            def request(self, method, path, body=None, **kwargs):
                return {"errors": True, "items": [{"index": {"_id": "bad", "status": 403}}]}

        with self.assertRaises(RuntimeError):
            project_git_docs.project_once(
                self.root, "overlay.yaml", "source", self.reader, FailedWriter(self.documents)
            )

    def test_cli_returns_nonzero_without_credentials(self):
        env = {key: value for key, value in os.environ.items() if not key.startswith("AIF_DOCS_")}
        result = subprocess.run(
            [sys.executable, "-m", "milestone1.project_git_docs", "--repo-root", str(self.root),
             "--overlay", "overlay.yaml", "--repository", "source"],
            cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("credentials are required", result.stderr)


if __name__ == "__main__":
    unittest.main()
