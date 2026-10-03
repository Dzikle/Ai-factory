"""Deterministic outcome reports from authoritative records."""

from pathlib import Path
import unittest

from milestone2.outcome_report import render_markdown, validate_candidate_lineage, validate_outcome_report


SECTIONS = ("Objective", "Candidate", "Changes", "Verification", "Independent Review",
            "External Evidence", "Authorization", "Knowledge Impact", "Deferred Findings",
            "Metrics", "Unresolved Items", "Rollback", "Next Disposition")


def sample_outcome(candidate_commit="a" * 40):
    return {
        "schemaVersion": 1,
        "objective": "Prove the one-authorization lifecycle on a docs-only wave.",
        "candidate": {"commit": candidate_commit, "tree": "b" * 40},
        "changes": [{"path": "docs/guide.md", "summary": "Clarify the lifecycle stages."}],
        "verification": {"candidate_commit": candidate_commit, "status": "passed",
                         "failed_checks": [], "missing_checks": []},
        "review": {"candidate_commit": candidate_commit, "verdict": "approve",
                   "reviewer": "independent-reviewer"},
        "external_evidence": [{"kind": "ci", "candidate_commit": candidate_commit, "status": "passed",
                               "uri": "https://ci.example.invalid/jobs/1"}],
        "authorization": {"digest": "c" * 64, "scope": "docs-only wave"},
        "knowledge_impact": "verify",
        "deferred_findings": [{"summary": "Stale diagram in README.", "severity": "low"}],
        "metrics": {"tests_run": 12, "tests_passed": 12, "usage": "unknown"},
        "unresolved_items": [],
        "rollback": "Revert the wave branch; no migration or deployment occurred.",
        "next_disposition": "Proceed to the next wave.",
        "status": "accepted",
    }


class OutcomeReportTests(unittest.TestCase):
    def test_candidate_identity_must_match_review_and_external_evidence(self):
        report = sample_outcome(candidate_commit="a" * 40)
        report["review"]["candidate_commit"] = "b" * 40
        self.assertIn("review candidate mismatch", validate_candidate_lineage(report))
        report = sample_outcome(candidate_commit="a" * 40)
        report["external_evidence"][0]["candidate_commit"] = "b" * 40
        self.assertIn("external evidence candidate mismatch", validate_candidate_lineage(report))
        report = sample_outcome(candidate_commit="a" * 40)
        report["verification"]["candidate_commit"] = "b" * 40
        self.assertIn("verification candidate mismatch", validate_candidate_lineage(report))
        self.assertEqual([], validate_candidate_lineage(sample_outcome()))

    def test_valid_report_renders_sections_in_fixed_order(self):
        report = sample_outcome()
        self.assertEqual([], validate_outcome_report(report))
        first, second = render_markdown(report), render_markdown(sample_outcome())
        self.assertEqual(first, second)
        positions = [first.index(f"## {section}") for section in SECTIONS]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("a" * 40, first)

    def test_reports_accept_only_validated_fields(self):
        report = sample_outcome()
        report["extra_field"] = "nope"
        with self.assertRaisesRegex(ValueError, "extra_field"):
            validate_outcome_report(report)
        report = sample_outcome()
        del report["rollback"]
        with self.assertRaisesRegex(ValueError, "rollback"):
            validate_outcome_report(report)
        report = sample_outcome()
        report["knowledge_impact"] = "rewrite-everything"
        with self.assertRaisesRegex(ValueError, "knowledge_impact"):
            validate_outcome_report(report)

    def test_outcome_document_round_trip_is_stable(self):
        import json

        report = sample_outcome()
        self.assertEqual(report, json.loads(json.dumps(report, sort_keys=True)))


if __name__ == "__main__":
    unittest.main()
