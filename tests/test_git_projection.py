"""Git-to-OpenSearch projection invariants for the first Milestone 1.3 slice."""

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from milestone1.git_projection import collect_snapshot, plan_reconciliation


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class GitProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        git(self.root, "init", "-q")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "decision.md").write_text(
            "# Decision\n\nCurrent rule.\n", encoding="utf-8"
        )
        (self.root / "outside.md").write_text("# Outside\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(
            self.root, "-c", "user.name=Projection Test", "-c",
            "user.email=projection@example.invalid", "commit", "-qm", "initial",
        )

    def snapshot(self) -> list[dict]:
        return collect_snapshot(
            self.root,
            project_id="example",
            repository_id="repo-one",
            remote="https://example.invalid/repo.git",
            canonical_paths=["docs/"],
        )

    def test_snapshot_reads_only_committed_allowed_files_with_provenance(self) -> None:
        # A working-tree change or untracked file must not become canonical truth.
        (self.root / "docs" / "decision.md").write_text("# Uncommitted\n", encoding="utf-8")
        (self.root / "docs" / "draft.md").write_text("# Untracked\n", encoding="utf-8")

        snapshot = self.snapshot()

        self.assertEqual(1, len(snapshot))
        document = snapshot[0]
        self.assertEqual("Decision", document["title"])
        self.assertEqual("# Decision\n\nCurrent rule.\n", document["content"])
        self.assertEqual("example", document["project_id"])
        self.assertEqual("repo-one:docs/decision.md", document["source_id"])
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), document["source_revision"])
        self.assertEqual(
            hashlib.sha256(b"# Decision\n\nCurrent rule.\n").hexdigest(),
            document["content_sha256"],
        )
        self.assertEqual("git", document["source_system"])
        self.assertEqual("canonical", document["authority"])
        self.assertTrue(document["canonical"])
        self.assertEqual("canonical", document["status"])

    def test_stable_id_updates_in_place_and_deleted_path_becomes_stale(self) -> None:
        first = self.snapshot()[0]
        (self.root / "docs" / "decision.md").write_text(
            "# Decision\n\nUpdated rule.\n", encoding="utf-8"
        )
        git(self.root, "add", ".")
        git(
            self.root, "-c", "user.name=Projection Test", "-c",
            "user.email=projection@example.invalid", "commit", "-qm", "update",
        )
        second = self.snapshot()[0]

        self.assertEqual(first["id"], second["id"])
        self.assertNotEqual(first["source_revision"], second["source_revision"])
        self.assertEqual([{"op": "index", "document": second}], plan_reconciliation([second], [first]))
        self.assertEqual([], plan_reconciliation([second], [second]))

        git(self.root, "rm", "docs/decision.md")
        git(
            self.root, "-c", "user.name=Projection Test", "-c",
            "user.email=projection@example.invalid", "commit", "-qm", "delete",
        )
        deletion_revision = git(self.root, "rev-parse", "HEAD")
        actions = plan_reconciliation([], [second], revision=deletion_revision)
        self.assertEqual(1, len(actions))
        tombstone = actions[0]["document"]
        self.assertEqual("index", actions[0]["op"])
        self.assertEqual(second["id"], tombstone["id"])
        self.assertEqual("stale", tombstone["status"])
        self.assertFalse(tombstone["canonical"])
        self.assertEqual("", tombstone["content"])
        self.assertEqual(deletion_revision, tombstone["source_revision"])
        self.assertEqual(deletion_revision, tombstone["source_version"])
        self.assertEqual([], plan_reconciliation([], [tombstone], revision=deletion_revision))

    def test_rejects_path_escape_and_binary_content(self) -> None:
        with self.assertRaises(ValueError):
            collect_snapshot(
                self.root, project_id="example", repository_id="repo-one",
                remote="https://example.invalid/repo.git", canonical_paths=["../outside"],
            )
        (self.root / "docs" / "binary.md").write_bytes(b"\x00\x01")
        git(self.root, "add", ".")
        git(
            self.root, "-c", "user.name=Projection Test", "-c",
            "user.email=projection@example.invalid", "commit", "-qm", "binary",
        )
        with self.assertRaises(ValueError):
            self.snapshot()

    def test_rejects_non_utf8_committed_text(self) -> None:
        (self.root / "docs" / "invalid.md").write_bytes(b"# Invalid\n\xff")
        git(self.root, "add", ".")
        git(
            self.root, "-c", "user.name=Projection Test", "-c",
            "user.email=projection@example.invalid", "commit", "-qm", "invalid",
        )
        with self.assertRaisesRegex(ValueError, "non-UTF-8"):
            self.snapshot()


if __name__ == "__main__":
    unittest.main()
