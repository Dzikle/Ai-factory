"""Verification contracts, safe execution, and compact digests."""

from pathlib import Path
from types import SimpleNamespace
import unittest

from milestone3.verification import (
    detect_divergence,
    digest_acceptance,
    load_profiles,
    resolve_profile,
    run_contract,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "autonomy" / "evals" / "verification.v1.json"


class FakeRunner:
    """Map exact argv tuples to exit codes; unknown argv means a missing check."""

    def __init__(self, exits):
        self.exits = {tuple(argv): code for argv, code in exits.items()}
        self.calls = []

    def __call__(self, argv, *, cwd, capture_output, timeout, shell):
        self.calls.append(list(argv))
        assert shell is False
        return SimpleNamespace(returncode=self.exits[tuple(argv)],
                               stdout=b"run output", stderr=b"")


def full_contract():
    return {
        "profile": "ai-factory-full",
        "candidate_commit": "a" * 40,
        "checks": [
            {"id": "git-diff", "argv": ["git", "diff", "--check"], "timeoutSeconds": 60, "required": True},
            {"id": "unit", "argv": ["python", "-m", "milestone3.check"], "timeoutSeconds": 900, "required": True},
        ],
    }


class VerificationTests(unittest.TestCase):
    def test_required_check_failure_and_missing_check_block_digest(self):
        digest = run_contract(full_contract(), ROOT, runner=FakeRunner({
            ("git", "diff", "--check"): 0, ("python", "-m", "milestone3.check"): 1}))
        self.assertEqual("failed", digest["status"])
        self.assertEqual(["unit"], digest["failed_checks"])
        digest = run_contract(full_contract(), ROOT, runner=FakeRunner({}))
        self.assertEqual(["git-diff", "unit"], digest["missing_checks"])
        self.assertTrue(digest_acceptance(digest))

    def test_passing_digest_has_hashes_not_raw_output(self):
        digest = run_contract(full_contract(), ROOT, runner=FakeRunner({
            ("git", "diff", "--check"): 0, ("python", "-m", "milestone3.check"): 0}))
        self.assertEqual("passed", digest["status"])
        self.assertEqual([], digest_acceptance(digest))
        for row in digest["results"]:
            self.assertEqual(64, len(row["stdout_sha256"]))
            self.assertLessEqual(len(row["stdout_excerpt"]), 500)
            self.assertNotIn("stdout", {key for key in row if key not in ("stdout_sha256", "stdout_excerpt")})

    def test_unsafe_contracts_are_rejected_before_execution(self):
        calls = []

        def runner(argv, *, cwd, capture_output, timeout, shell):
            calls.append(argv)
            raise AssertionError("must not execute")

        contract = full_contract()
        contract["checks"][0]["argv"] = "git diff --check"
        with self.assertRaisesRegex(ValueError, "argv"):
            run_contract(contract, ROOT, runner=runner)
        contract = full_contract()
        contract["checks"][0]["cwd"] = "/absolute/escape"
        with self.assertRaisesRegex(ValueError, "cwd"):
            run_contract(contract, ROOT, runner=runner)
        contract = full_contract()
        contract["checks"][0]["cwd"] = "../escape"
        with self.assertRaisesRegex(ValueError, "cwd"):
            run_contract(contract, ROOT, runner=runner)
        contract = full_contract()
        contract["checks"].append(dict(contract["checks"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            run_contract(contract, ROOT, runner=runner)
        contract = full_contract()
        contract["checks"][0]["timeoutSeconds"] = 1801
        with self.assertRaisesRegex(ValueError, "timeout"):
            run_contract(contract, ROOT, runner=runner)
        contract = full_contract()
        contract["checks"][0]["env"] = {"BOARD_API_KEY": "secret"}
        with self.assertRaisesRegex(ValueError, "env"):
            run_contract(contract, ROOT, runner=runner)
        self.assertEqual([], calls)

    def test_reduced_profile_requires_documentation_only_changes(self):
        profiles = load_profiles(PROFILES)
        self.assertIn("ai-factory-full", profiles)
        self.assertIn("ai-factory-docs", profiles)
        resolve_profile(profiles, "ai-factory-docs", changed_paths=["docs/guide.md", "README.md"])
        with self.assertRaisesRegex(ValueError, "documentation"):
            resolve_profile(profiles, "ai-factory-docs", changed_paths=["docs/guide.md", "milestone3/check.py"])

    def test_divergent_digest_is_detected_against_its_contract(self):
        contract = full_contract()
        digest = run_contract(contract, ROOT, runner=FakeRunner({
            ("git", "diff", "--check"): 0, ("python", "-m", "milestone3.check"): 0}))
        self.assertEqual([], detect_divergence(contract, digest))
        tampered = dict(digest, results=[digest["results"][0]])
        self.assertTrue(detect_divergence(contract, tampered))

    def test_wave_gate_blocks_progression_after_failure(self):
        from milestone3.verification import check_progression

        good = {"status": "passed", "failed_checks": [], "missing_checks": []}
        bad = {"status": "failed", "failed_checks": ["unit"], "missing_checks": []}
        self.assertEqual([], check_progression(["w1", "w2"], {"w1": good, "w2": good}))
        errors = check_progression(["w1", "w2"], {"w1": bad, "w2": good})
        self.assertTrue(any("w1" in error for error in errors))


def json_text(row):
    import json

    return json.dumps(row)


if __name__ == "__main__":
    unittest.main()
