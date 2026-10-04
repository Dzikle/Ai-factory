"""Deferred findings, exact knowledge patches, and recoverable cleanup."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import unittest

from milestone3.maintenance import (
    apply_patch,
    deduplicate_findings,
    finding_fingerprint,
    plan_reclamation,
    preview_patch,
    quarantine_resources,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 3, tzinfo=timezone.utc)


def sample_patch(path="docs/architecture/STATE_AND_STORAGE.md", expected_sha256="0" * 64):
    return {"path": path, "expected_sha256": expected_sha256,
            "old_text": "Self-improvement", "new_text": "Self-improvement"}


def sample_resources():
    return [
        {"id": "expired-unreferenced", "owner_task_id": "AIF-61", "path": "evidence/old.json",
         "expires_at": "2026-10-01T00:00:00Z", "referenced": False, "protected": False, "reproducible": True},
        {"id": "referenced", "owner_task_id": "AIF-61", "path": "evidence/live.json",
         "expires_at": "2026-10-01T00:00:00Z", "referenced": True, "protected": False, "reproducible": True},
        {"id": "foreign", "owner_task_id": "AIF-61", "path": "../outside.json",
         "expires_at": "2026-10-01T00:00:00Z", "referenced": False, "protected": False, "reproducible": True},
    ]


class MaintenanceSafetyTests(unittest.TestCase):
    def test_patch_requires_current_hash_and_scoped_path(self):
        patch = sample_patch(path="docs/architecture/STATE_AND_STORAGE.md", expected_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "source changed"):
            preview_patch(ROOT, patch)
        with self.assertRaisesRegex(ValueError, "outside assigned root"):
            preview_patch(ROOT, sample_patch(path="../outside.md"))

    def test_cleanup_retains_referenced_or_foreign_resources(self):
        plan = plan_reclamation(sample_resources(), now=NOW, owned_root=ROOT / ".milestone0")
        self.assertEqual(["expired-unreferenced"], [row["id"] for row in plan["quarantine"]])
        self.assertEqual({"referenced", "foreign"}, {row["id"] for row in plan["retained"]})

    def test_finding_fingerprints_deduplicate_but_preserve_origins(self):
        first = {"project_id": "ai-factory", "affected_components": ["retrieval"],
                 "summary": "Stale hits in judged eval.", "origin_task_ids": ["AIF-60"]}
        second = {"project_id": "ai-factory", "affected_components": ["retrieval"],
                  "summary": "Stale hits in judged eval.", "origin_task_ids": ["AIF-61"]}
        self.assertEqual(finding_fingerprint(first), finding_fingerprint(second))
        merged = deduplicate_findings([first, second])
        self.assertEqual(1, len(merged))
        self.assertEqual({"AIF-60", "AIF-61"}, set(merged[0]["origin_task_ids"]))

    def test_preview_apply_round_trip_is_exact_and_audited(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "note.md").write_text("alpha old_text omega\n", encoding="utf-8")
            digest = hashlib.sha256((root / "note.md").read_bytes()).hexdigest()
            patch = {"path": "note.md", "expected_sha256": digest,
                     "old_text": "old_text", "new_text": "new_text"}
            preview = preview_patch(root, patch)
            audit = apply_patch(root, patch, preview)
            self.assertEqual(preview["after_sha256"], audit["after_sha256"])
            self.assertEqual("alpha new_text omega\n", (root / "note.md").read_text(encoding="utf-8"))
            self.assertEqual(preview["updated_text"].encode("utf-8"), (root / "note.md").read_bytes())
            self.assertEqual(preview["after_sha256"],
                             hashlib.sha256((root / "note.md").read_bytes()).hexdigest())
            # CRLF content must round-trip byte-exact: write_text would
            # translate the LF in each CRLF pair again (CR CR LF) on Windows.
            (root / "crlf.md").write_bytes(b"alpha old_text omega\r\n")
            crlf_digest = hashlib.sha256((root / "crlf.md").read_bytes()).hexdigest()
            crlf_patch = {"path": "crlf.md", "expected_sha256": crlf_digest,
                          "old_text": "old_text", "new_text": "new_text"}
            crlf_preview = preview_patch(root, crlf_patch)
            crlf_audit = apply_patch(root, crlf_patch, crlf_preview)
            self.assertEqual(crlf_preview["after_sha256"], crlf_audit["after_sha256"])
            self.assertEqual(b"alpha new_text omega\r\n", (root / "crlf.md").read_bytes())
            self.assertNotIn(b"\r\r\n", (root / "crlf.md").read_bytes())
            (root / "note.md").write_text("someone else edited\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "re-preview"):
                apply_patch(root, patch, preview)

    def test_quarantine_moves_without_deleting(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            owned = Path(temp) / "factory"
            (owned / "evidence").mkdir(parents=True)
            (owned / "evidence" / "old.json").write_text("{}\n", encoding="utf-8")
            (owned / "evidence" / "live.json").write_text("{}\n", encoding="utf-8")
            records = [
                {"id": "expired-unreferenced", "owner_task_id": "AIF-61", "path": "evidence/old.json",
                 "expires_at": "2026-10-01T00:00:00Z", "referenced": False, "protected": False,
                 "reproducible": True},
                {"id": "referenced", "owner_task_id": "AIF-61", "path": "evidence/live.json",
                 "expires_at": "2026-10-01T00:00:00Z", "referenced": True, "protected": False,
                 "reproducible": True},
            ]
            plan = plan_reclamation(records, now=NOW, owned_root=owned)
            receipt = quarantine_resources(owned, plan["quarantine"])
            self.assertFalse((owned / "evidence" / "old.json").exists())
            self.assertTrue((owned / "evidence" / "live.json").exists())
            moved = Path(receipt["directory"]) / "expired-unreferenced"
            self.assertTrue(moved.exists())
            self.assertTrue((Path(receipt["directory"]) / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
