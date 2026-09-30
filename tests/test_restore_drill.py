import unittest

from milestone4.restore_drill import artifact_manifest


RUN = "e5f65f3c-0910-4b00-ab0e-0ddf28a019f6"
REF = "file:///paperclip/milestone1-context/" + RUN + ".json"


class RestoreManifestTests(unittest.TestCase):
    def test_malformed_run_rows_fail_without_an_unhandled_identity_error(self):
        for rows in ([None], [{}], [{"id": None}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                artifact_manifest(rows)
    def test_only_recorded_context_bytes_are_selected(self):
        rows = [{"id": RUN, "enrichment": {"version": 1, "entries": [
            {"artifact": {"ref": REF, "sha256": "a" * 64, "byteSize": 123}}
        ]}}]
        self.assertEqual([{"runId": RUN, "ref": REF, "path": REF.removeprefix("file://"),
                           "sha256": "a" * 64, "byteSize": 123}], artifact_manifest(rows))

    def test_external_or_traversing_artifact_cannot_escape_restored_volume(self):
        for ref in ["file:///etc/passwd", "file:///paperclip/milestone1-context/../secret.json",
                    "https://example.org/context.json"]:
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                artifact_manifest([{"id": RUN, "enrichment": {"version": 1, "entries": [
                    {"artifact": {"ref": ref, "sha256": "a" * 64, "byteSize": 123}}
                ]}}])

    def test_missing_digest_is_not_restore_evidence(self):
        with self.assertRaises(ValueError):
            artifact_manifest([{"id": RUN, "enrichment": {"version": 1, "entries": [
                {"artifact": {"ref": REF, "sha256": None, "byteSize": 123}}
            ]}}])


if __name__ == "__main__":
    unittest.main()
