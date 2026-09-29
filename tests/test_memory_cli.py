"""Task preparation cannot leak credentials or become another dispatcher."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from milestone3.cli import attach_context


class MemoryCliTests(unittest.TestCase):
    def test_degraded_or_empty_memory_leaves_task_unchanged(self):
        task = {"title": "Task", "description": "Current requirements", "requestKey": "stable-task"}
        for status in ("degraded", "empty"):
            with self.subTest(status=status):
                self.assertEqual(attach_context(task, {"status": status}), task)

    def test_advice_does_not_replace_requirements_or_task_identity(self):
        task = {"title": "Task", "description": "Current requirements", "requestKey": "stable-task"}
        result = attach_context(task, {"status": "used", "prompt": "Historical advice"})
        self.assertEqual(result, {**task, "description": "Current requirements\n\nHistorical advice"})
        self.assertEqual(task["description"], "Current requirements")

    def test_help_does_not_require_credentials_or_services(self):
        result = subprocess.run([sys.executable, "-m", "milestone3.cli", "--help"],
                                capture_output=True, text=True, timeout=10, env={**os.environ, "AIF_MEMORY_TOKEN": ""})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("recall", result.stdout)
        self.assertIn("supersede", result.stdout)

    def test_unreachable_or_invalid_memory_is_safe_without_disclosing_token(self):
        marker = "test-secret-must-not-be-printed"
        for url in ("http://127.0.0.1:1/mcp", "http://not-a-loopback.example/mcp"):
            with self.subTest(url=url):
                result = subprocess.run([sys.executable, "-m", "milestone3.cli", "recall", "--query", "tests",
                                         "--project", "ai-factory", "--role", "developer"],
                                        capture_output=True, text=True, timeout=10,
                                        env={**os.environ, "AIF_MEMORY_TOKEN": marker, "AIF_MEMORY_URL": url})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(marker, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout), {"status": "degraded", "prompt": "", "memories": [],
                                                             "context_bytes": 0, "estimated_tokens": 0})


if __name__ == "__main__":
    unittest.main()
