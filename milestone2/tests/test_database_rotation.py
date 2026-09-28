"""Credential transport regression: test sentinels only; no live service writes."""
import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("database_rotation", Path(__file__).parents[1] / "scripts/rotate_local_paperclip_database.py")
rotation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rotation)


class DatabaseRotationTests(unittest.TestCase):
    def test_password_is_stdin_only_and_auth_is_tcp(self):
        with patch.object(rotation.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"1\n", b"")) as run:
            self.assertTrue(rotation.tcp_auth("test-password-sentinel"))
        args, options = run.call_args
        self.assertNotIn("test-password-sentinel", " ".join(args[0]))
        self.assertIn("-h " + rotation.POSTGRES, " ".join(args[0]))
        self.assertNotIn("127.0.0.1", " ".join(args[0]))
        self.assertEqual(options["input"], b"test-password-sentinel\n")

    def test_failed_auth_does_not_print_driver_errors_or_credentials(self):
        with patch.object(rotation.subprocess, "run", return_value=subprocess.CompletedProcess([], 2, b"", b"private-driver-output")):
            self.assertFalse(rotation.tcp_auth("test-password-sentinel"))

    def test_docker_failure_does_not_include_stdin_or_stderr_in_exception(self):
        with patch.object(rotation.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"private-stdout", b"private-stderr")):
            with self.assertRaisesRegex(RuntimeError, r"Docker operation failed: exec \(exit 1\)") as failure:
                rotation.docker("exec", "fixture", stdin=b"test-password-sentinel")
        for private in ("test-password-sentinel", "private-stdout", "private-stderr"):
            self.assertNotIn(private, str(failure.exception))


if __name__ == "__main__":
    unittest.main()
