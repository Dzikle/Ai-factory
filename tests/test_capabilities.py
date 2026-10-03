"""Capability health aggregation and admission decisions."""

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest

import yaml

from milestone2.capabilities import assess, load_manifests, main as capabilities_main


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "autonomy" / "capabilities" / "providers.v1.yaml"


def manifests() -> list:
    return load_manifests(MANIFESTS)


class CapabilityAssessmentTests(unittest.TestCase):
    def test_required_unhealthy_blocks_and_optional_unhealthy_degrades(self) -> None:
        blocked = assess(["repo.write"], ["knowledge.search"], manifests(), {"paperclip": "down", "opensearch": "down"})
        self.assertEqual("blocked", blocked["status"])
        degraded = assess(["repo.read"], ["knowledge.search"], manifests(), {"paperclip": "healthy", "opensearch": "down"})
        self.assertEqual("degraded", degraded["status"])
        self.assertEqual(["knowledge.search"], degraded["unavailable_optional"])

    def test_healthy_catalog_is_ready(self) -> None:
        ready = assess(["repo.read"], ["knowledge.search"], manifests(),
                       {"paperclip": "healthy", "opensearch-mcp": "healthy", "mempalace": "healthy"})
        self.assertEqual("ready", ready["status"])
        self.assertEqual([], ready["unavailable_required"])
        self.assertEqual([], ready["unavailable_optional"])

    def test_unknown_capability_never_falls_back_to_prompt_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown capability"):
            assess(["cloud.superuser"], [], manifests(), {})

    def test_disabled_capabilities_are_never_admitted(self) -> None:
        disabled = [item["capability"] for item in manifests() if item["status"] == "disabled"]
        self.assertTrue(disabled, "expected at least one disabled capability in the manifest")
        for capability in disabled:
            with self.subTest(capability=capability):
                result = assess([capability], [], manifests(), {"paperclip": "healthy"})
                self.assertEqual("blocked", result["status"])
                self.assertEqual([capability], result["unavailable_required"])

    def test_active_providers_share_logical_operation_fields(self) -> None:
        by_operation: dict = {}
        for item in manifests():
            if item["status"] != "active":
                continue
            self.assertTrue(item["operations"], f"{item['capability']} advertises no operations")
            for operation in item["operations"]:
                self.assertTrue(operation["request_fields"], f"{item['capability']} operation has no request fields")
                self.assertTrue(operation["result_fields"], f"{item['capability']} operation has no result fields")
                by_operation.setdefault(operation["name"], []).append(operation)
        for name, operations in by_operation.items():
            with self.subTest(operation=name):
                for other in operations[1:]:
                    self.assertEqual(operations[0]["request_fields"], other["request_fields"])
                    self.assertEqual(operations[0]["result_fields"], other["result_fields"])


class DoctorCommandTests(unittest.TestCase):
    def test_doctor_reports_aggregate_and_never_prints_credentials(self) -> None:
        probes = {"paperclip": "healthy", "opensearch-mcp": "down", "mempalace": "healthy",
                  "boardApiKey": "secret-value-that-must-never-print"}
        path = Path(self._probe_file(probes))
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = capabilities_main(["doctor", "--probes", str(path), "--required", "repo.read",
                                          "--optional", "knowledge.search"])
            self.assertEqual(0, code)
            self.assertIn("degraded", buffer.getvalue())
            self.assertNotIn("secret-value-that-must-never-print", buffer.getvalue())
        finally:
            path.unlink()

    def _probe_file(self, probes: dict) -> str:
        path = ROOT / ".milestone0" / "test-probes.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"probes": probes}), encoding="utf-8")
        return str(path)


if __name__ == "__main__":
    unittest.main()
