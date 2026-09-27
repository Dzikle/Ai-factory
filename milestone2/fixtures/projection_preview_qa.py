"""Independent black-box CLI acceptance checks, not the Developer's unit suite.

Run from the immutable source copy under test. Only a temporary Git repository
and loopback HTTP fixture are changed; no live OpenSearch credentials are used.
"""

import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


class ProjectionPreviewQA(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="aif-preview-qa-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.documents = {}
        self.requests = []
        self.malformed = False
        self.git("init", "-q")
        self.git("config", "user.email", "qa@example.invalid")
        self.git("config", "user.name", "Independent QA")
        (self.repo / "docs").mkdir()
        (self.repo / "docs/one.md").write_text("# One\nQA fixture\n", encoding="utf-8")
        (self.repo / "overlay.yaml").write_text(
            "schema_version: 1\nproject_id: qa-preview\nrepositories:\n"
            "  - id: source\n    remote: https://example.invalid/source.git\n"
            "    canonical_paths: [docs/]\n", encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-qm", "QA source")
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                owner.requests.append(self.path)
                if self.path == "/ai_factory_docs/_search":
                    query = json.loads(raw)
                    filters = query["query"]["bool"]["filter"]
                    owner.assertIn({"term": {"project_id": "qa-preview"}}, filters)
                    owner.assertIn({"term": {"repository_id": "source"}}, filters)
                    payload = {"hits": {}} if owner.malformed else {"hits": {"hits": [
                        {"_source": document, "sort": [key]}
                        for key, document in sorted(owner.documents.items())
                    ]}}
                elif self.path == "/_bulk?refresh=wait_for":
                    rows = [json.loads(line) for line in raw.splitlines()]
                    for header, document in zip(rows[::2], rows[1::2]):
                        owner.documents[header["index"]["_id"]] = document
                    payload = {"errors": False}
                else:
                    self.send_error(403)
                    return
                data = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, stderr=subprocess.PIPE).decode().strip()

    def command(self, *flags, writer=False):
        # Deliberately exclude all live model, Paperclip and OpenSearch secrets.
        env = {key: value for key, value in os.environ.items()
               if key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PYTHONPATH")}
        env.update(AIF_DOCS_URL=f"http://127.0.0.1:{self.server.server_port}",
                   AIF_DOCS_READER_USER="qa-reader", AIF_DOCS_READER_PASSWORD="fixture-only")
        if writer:
            env.update(AIF_DOCS_WRITER_USER="qa-writer", AIF_DOCS_WRITER_PASSWORD="fixture-writer")
        return subprocess.run([
            sys.executable, "-m", "milestone1.project_git_docs", "--repo-root", str(self.repo),
            "--overlay", "overlay.yaml", "--repository", "source", "--insecure-localhost", *flags,
        ], env=env, capture_output=True, text=True, timeout=20)

    def result(self, *flags, writer=False):
        result = self.command(*flags, writer=writer)
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_reader_only_preview_repeats_without_mutation(self):
        for _ in range(2):
            result = self.result("--dry-run")
            self.assertEqual((True, 1, 0), (result["dry_run"], result["planned_writes"], result["writes"]))
            self.assertEqual(self.git("rev-parse", "HEAD"), result["revision"])
        self.assertEqual({}, self.documents)
        self.assertEqual(["/ai_factory_docs/_search"] * 2, self.requests)

    def test_preview_counts_tombstone_and_ignores_available_writer(self):
        key = hashlib.sha256(b"qa-preview\0source\0docs/removed.md").hexdigest()
        self.documents[key] = {"id": key, "path": "docs/removed.md", "project_id": "qa-preview",
                               "repository_id": "source", "source_system": "git",
                               "source_id": "source:docs/removed.md", "status": "canonical", "content": "old"}
        before = copy.deepcopy(self.documents)
        result = self.result("--dry-run", writer=True)
        self.assertEqual((2, 0), (result["planned_writes"], result["writes"]))
        self.assertEqual(before, self.documents)
        self.assertEqual(["/ai_factory_docs/_search"], self.requests)

    def test_apply_then_preview_then_apply_replay(self):
        applied = self.result(writer=True)
        self.assertEqual(1, applied["writes"])
        self.assertNotIn("dry_run", applied)
        before = copy.deepcopy(self.documents)
        self.assertEqual(0, self.result("--dry-run")["planned_writes"])
        self.assertEqual(0, self.result(writer=True)["writes"])
        self.assertEqual(before, self.documents)
        self.assertEqual(1, self.requests.count("/_bulk?refresh=wait_for"))

    def test_wrong_revision_has_no_http_effect(self):
        result = self.command("--dry-run", "--expect-revision", "0" * 40)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("expected Git revision", result.stderr)
        self.assertEqual([], self.requests)

    def test_malformed_response_fails_without_write(self):
        self.malformed = True
        result = self.command("--dry-run", writer=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("malformed", result.stderr)
        self.assertEqual(["/ai_factory_docs/_search"], self.requests)
        self.assertEqual({}, self.documents)

    def test_apply_without_writer_still_fails_before_search(self):
        result = self.command()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("credentials", result.stderr)
        self.assertEqual([], self.requests)


if __name__ == "__main__":
    unittest.main()
