"""Black-box CLI surface for the self-enhancement lifecycle."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEV, VALIDATOR, REVIEWER, QA = [f"00000000-0000-0000-0000-00000000000{i}" for i in range(1, 5)]


def run_cli(*argv, cwd=None):
    env = dict(os.environ)
    env.pop("AIF_PAPERCLIP_STATE", None)
    env["PYTHONPATH"] = os.pathsep.join([p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
                                        + ["/paperclip/m1-python-libs", str(ROOT)])
    return subprocess.run([sys.executable, "-m", "milestone2.program", *argv],
                          cwd=cwd or ROOT, capture_output=True, text=True, timeout=120, env=env)


def snapshot_tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(Path(root).rglob("*")) if path.is_file()}


class SelfEnhancementCliTests(unittest.TestCase):
    def test_help_is_credential_free_and_lists_whole_lifecycle_commands(self):
        result = subprocess.run([sys.executable, "-m", "milestone2.program", "--help"],
                                cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode)
        self.assertIn("submit", result.stdout)
        self.assertIn("status", result.stdout)
        self.assertIn("report", result.stdout)
        self.assertNotIn("AIF_PAPERCLIP_STATE", result.stderr)

    def test_dry_run_performs_no_network_or_filesystem_write(self):
        with tempfile.TemporaryDirectory() as temp:
            area = Path(temp)
            workflow = {"projectId": "00000000-0000-0000-0000-000000000020",
                        "developerAgentId": DEV, "validatorAgentId": VALIDATOR,
                        "reviewerAgentId": REVIEWER, "qaAgentId": QA}
            (area / "workflow.json").write_text(json.dumps(workflow), encoding="utf-8")
            before = snapshot_tree(area)
            result = run_cli("submit", "--program",
                             str(ROOT / "milestone2" / "tasks" / "self-enhancement-program.json"),
                             "--workflow", str(area / "workflow.json"), "--dry-run")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("dryRun", result.stdout)
            self.assertEqual(before, snapshot_tree(area))

    def test_owning_modules_expose_lifecycle_help(self):
        for module, command in (("milestone2.capabilities", "doctor"),
                                ("milestone3.context", "evidence"),
                                ("milestone3.verification", "verify"),
                                ("milestone3.maintenance", "maintenance-preview")):
            with self.subTest(module=module):
                env = dict(os.environ)
                env["PYTHONPATH"] = os.pathsep.join(
                    [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
                    + ["/paperclip/m1-python-libs", str(ROOT)])
                result = subprocess.run([sys.executable, "-m", module, command, "--help"],
                                        cwd=ROOT, capture_output=True, text=True, timeout=120, env=env)
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
