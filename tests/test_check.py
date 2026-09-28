"""Regression tests for the deterministic pinned test-environment check.

Avoids recursive test invocation: the default delegation path
(`python -m unittest discover -s tests -q`) is never executed here;
version lookup and subprocess execution are stubbed in-process, while
only --help/--print-command run out-of-process in an isolated interpreter.
"""

import subprocess
import sys
import unittest
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest import mock

CHECK = Path(__file__).resolve().parents[1] / "milestone3" / "check.py"
EXPECTED_COMMAND = (
    "uv run --offline --no-project "
    "--with jsonschema[format]==4.25.1 "
    "--with PyYAML==6.0.2 "
    "python -m unittest discover -s tests -q"
)

PINNED = {"jsonschema": "4.25.1", "PyYAML": "6.0.2"}


def run_isolated(*args):
    """Run check.py with no site packages, no PYTHONPATH, no credentials."""
    return subprocess.run(
        [sys.executable, "-I", "-S", str(CHECK), *args],
        capture_output=True, text=True, timeout=15, env={},
    )


def load_check():
    import milestone3.check as check

    return check


class CheckCommandTests(unittest.TestCase):
    def test_help_needs_no_dependencies_or_credentials(self):
        result = run_isolated("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--print-command", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_print_command_is_complete_on_one_line(self):
        result = run_isolated("--print-command")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, EXPECTED_COMMAND + "\n")
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_dependency_returns_exit_2_without_running_tests(self):
        check = load_check()

        def absent(dist):
            raise PackageNotFoundError(dist)

        with mock.patch.object(check, "version_of", side_effect=absent), mock.patch.object(
            check.subprocess, "run", side_effect=AssertionError("must not run tests")
        ):
            with mock.patch("sys.stderr") as _err, mock.patch("sys.stdout"):
                code = check.main([])
        self.assertEqual(code, 2)

    def test_missing_dependency_message_is_actionable(self):
        check = load_check()

        def absent(dist):
            raise PackageNotFoundError(dist)

        with mock.patch.object(check, "version_of", side_effect=absent), mock.patch.object(
            check.subprocess, "run", side_effect=AssertionError("must not run tests")
        ):
            import io

            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                code = check.main([])
        self.assertEqual(code, 2)
        message = err.getvalue()
        self.assertIn("jsonschema", message)
        self.assertIn("PyYAML", message)
        self.assertIn("uv run --offline --no-project", message)
        self.assertIn(EXPECTED_COMMAND, message)
        self.assertNotIn("Traceback", message)

    def test_mismatched_version_returns_exit_2_without_running_tests(self):
        check = load_check()

        def wrong(dist):
            return "0.0.0"

        with mock.patch.object(check, "version_of", side_effect=wrong), mock.patch.object(
            check.subprocess, "run", side_effect=AssertionError("must not run tests")
        ), mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            code = check.main([])
        self.assertEqual(code, 2)

    def test_matching_versions_delegate_to_this_interpreter_without_shell(self):
        check = load_check()

        def pinned(dist):
            return PINNED[dist]

        recorded = {}

        def fake_run(argv, **kwargs):
            recorded["argv"] = argv
            recorded["kwargs"] = kwargs
            completed = mock.Mock()
            completed.returncode = 3
            return completed

        with mock.patch.object(check, "version_of", side_effect=pinned), mock.patch.object(
            check.subprocess, "run", side_effect=fake_run
        ):
            code = check.main([])
        self.assertEqual(code, 3)
        self.assertEqual(
            recorded["argv"],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        )
        self.assertNotIn("shell", recorded["kwargs"])

    def test_matching_versions_propagate_success(self):
        check = load_check()

        def pinned(dist):
            return PINNED[dist]

        def fake_run(argv, **kwargs):
            completed = mock.Mock()
            completed.returncode = 0
            return completed

        with mock.patch.object(check, "version_of", side_effect=pinned), mock.patch.object(
            check.subprocess, "run", side_effect=fake_run
        ):
            code = check.main([])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
