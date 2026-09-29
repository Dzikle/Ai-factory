"""The native stage guard checks committed bytes, including the signature."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = "def collect():\n    return 42\ndef format_scorecard(report):\n    return 'old'\n"


class ScorecardGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "milestone2").mkdir()
        self.target = self.repo / "milestone2/scorecard.py"
        self.target.write_text(ORIGINAL)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").strip()
        self.reference = self.repo / "reference.py"
        # Outside the committed candidate, as in the original mutable-source guard.
        self.reference.write_text(ORIGINAL)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True, stderr=subprocess.DEVNULL)

    def commit(self):
        self.git("add", "milestone2/scorecard.py")
        self.git("commit", "-qm", "fixture")

    def check(self, content):
        self.target.write_text(content)
        self.commit()
        guard = ROOT / "milestone4/fixtures/eval_guard.py"
        return subprocess.run([sys.executable, str(guard), self.base], cwd=self.repo,
                              capture_output=True, text=True, timeout=15)

    def test_body_only_change_is_allowed(self):
        self.assertEqual(0, self.check(ORIGINAL.replace("'old'", "'new'")).returncode)

    def test_default_argument_change_is_rejected(self):
        self.assertNotEqual(0, self.check(ORIGINAL.replace("(report)", "(report=collect())")).returncode)

    def test_decorator_change_is_rejected(self):
        self.assertNotEqual(0, self.check(ORIGINAL.replace("def format_scorecard", "@str\ndef format_scorecard")).returncode)

    def test_duplicate_definition_is_rejected(self):
        self.assertNotEqual(0, self.check(ORIGINAL + "def format_scorecard(report):\n    return 'new'\n").returncode)

    def test_mutable_reference_cannot_redefine_the_baseline(self):
        changed = ORIGINAL.replace("return 42", "return 43")
        self.reference.write_text(changed)
        self.assertNotEqual(0, self.check(changed).returncode)

    def test_moving_head_cannot_redefine_the_pinned_baseline(self):
        changed = ORIGINAL.replace("return 42", "return 44")
        self.assertNotEqual(0, self.check(changed).returncode)


if __name__ == "__main__":
    unittest.main()
