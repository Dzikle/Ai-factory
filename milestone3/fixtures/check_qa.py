"""Independent black-box check-command QA; no credentials or dependency imports."""

from pathlib import Path
import subprocess
import sys
import unittest


class CheckCommandQA(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-S", str(Path("milestone3/check.py").resolve()), *args],
                              capture_output=True, text=True, timeout=15, env={})

    def test_help_needs_no_dependencies_or_service(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--print-command", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_recovery_command_is_complete_on_one_line(self):
        result = self.run_cli("--print-command")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("uv run --offline --no-project", lines[0])
        self.assertIn("jsonschema[format]==4.25.1", lines[0])
        self.assertIn("PyYAML==6.0.2", lines[0])
        self.assertIn("python -m unittest discover -s tests -q", lines[0])

    def test_missing_dependencies_fail_before_application_tests(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("jsonschema", result.stderr)
        self.assertIn("PyYAML", result.stderr)
        self.assertIn("uv run --offline --no-project", result.stderr)
        self.assertNotIn("Ran ", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
