"""Readable format_scorecard contract: unknown is never zero; no mutation."""

from copy import deepcopy
import unittest

from milestone2.scorecard import format_scorecard


def make_report(**overrides):
    report = {
        "identifier": "AIF-TEST",
        "issueId": "test-issue",
        "status": "done",
        "runCount": 2,
        "failedRuns": 0,
        "recordedRetries": 0,
        "handoffCancellations": 2,
        "quality": {
            "ownerAccepted": True,
            "independentParticipants": True,
            "completedStages": 4,
            "totalStages": 4,
        },
        "timing": {
            "runtimeMs": 4000,
            "executionWindowMs": 5000,
            "knownRuntimeMs": 4000,
            "coveredRuns": 2,
        },
        "usage": {
            "inputTokens": None,
            "cachedInputTokens": None,
            "outputTokens": None,
            "reportedCostUsd": None,
            "reportedCostPerOwnerAcceptedTaskUsd": None,
            "coveredRuns": 0,
            "costCoveredRuns": 0,
            "knownInputTokens": 0,
            "knownCachedInputTokens": 0,
            "knownOutputTokens": 0,
            "knownReportedCostUsd": 0,
        },
    }
    for key, value in overrides.items():
        report[key] = value
    return report


class FormatScorecardTests(unittest.TestCase):
    def test_task_quality_and_runs_lines(self):
        text = format_scorecard(make_report())
        self.assertIsInstance(text, str)
        for line in (
            "Task: AIF-TEST (done)",
            "Owner accepted: yes",
            "Independent participants: yes",
            "Gates: 4/4",
            "Runs: 2; failed: 0; retries: 0; handoff cancellations: 2",
        ):
            self.assertIn(line, text)

    def test_unknown_usage_is_not_free(self):
        text = format_scorecard(make_report())
        self.assertIn(
            "Tokens: input unknown; cached unknown; output unknown; coverage: 0/2",
            text,
        )
        self.assertIn("Reported cost: unknown USD; coverage: 0/2", text)
        self.assertNotIn("PRIVATE_SENTINEL", text)

    def test_explicit_zero_remains_zero(self):
        value = make_report()
        value["usage"].update(
            inputTokens=0,
            cachedInputTokens=0,
            outputTokens=0,
            reportedCostUsd=0,
            reportedCostPerOwnerAcceptedTaskUsd=0,
            coveredRuns=2,
            costCoveredRuns=2,
        )
        text = format_scorecard(value)
        self.assertIn("Tokens: input 0; cached 0; output 0; coverage: 2/2", text)
        self.assertIn("Reported cost: 0.000000 USD; coverage: 2/2", text)

    def test_complete_usage_and_timing(self):
        value = make_report()
        value["usage"].update(
            inputTokens=50,
            cachedInputTokens=10,
            outputTokens=6,
            reportedCostUsd=0.5,
            reportedCostPerOwnerAcceptedTaskUsd=0.5,
            coveredRuns=2,
            costCoveredRuns=2,
            knownInputTokens=50,
            knownCachedInputTokens=10,
            knownOutputTokens=6,
            knownReportedCostUsd=0.5,
        )
        text = format_scorecard(value)
        self.assertIn("Tokens: input 50; cached 10; output 6; coverage: 2/2", text)
        self.assertIn("Reported cost: 0.500000 USD; coverage: 2/2", text)
        self.assertIn("Runtime: 4.000 s; coverage: 2/2", text)
        self.assertIn("Execution window: 5.000 s", text)
        self.assertIn("Known runtime subtotal: 4.000 s", text)
        self.assertIn(
            "Known subtotal: input 50; cached 10; output 6; reported 0.500000 USD",
            text,
        )
        self.assertIn(
            "Reported cost per owner-accepted task: 0.500000 USD", text
        )

    def test_partial_usage_labels_known_subtotal(self):
        value = make_report()
        value["usage"].update(
            coveredRuns=1,
            costCoveredRuns=1,
            knownInputTokens=20,
            knownCachedInputTokens=5,
            knownOutputTokens=3,
            knownReportedCostUsd=0.25,
        )
        text = format_scorecard(value)
        self.assertIn("Reported cost: unknown USD; coverage: 1/2", text)
        self.assertIn(
            "Known subtotal: input 20; cached 5; output 3; reported 0.250000 USD",
            text,
        )

    def test_partial_timing_does_not_become_complete(self):
        value = make_report()
        value["timing"].update(
            runtimeMs=None,
            executionWindowMs=None,
            coveredRuns=1,
            knownRuntimeMs=2000,
        )
        text = format_scorecard(value)
        self.assertIn("Runtime: unknown s; coverage: 1/2", text)
        self.assertIn("Execution window: unknown s", text)
        self.assertIn("Known runtime subtotal: 2.000 s", text)

    def test_pending_owner_and_unknown_independence(self):
        value = make_report()
        value["quality"].update(
            ownerAccepted=False, independentParticipants=None, completedStages=3
        )
        text = format_scorecard(value)
        self.assertIn("Owner accepted: no", text)
        self.assertIn("Independent participants: unknown", text)
        self.assertIn("Gates: 3/4", text)
        self.assertIn(
            "Reported cost per owner-accepted task: unknown USD", text
        )

    def test_non_independent_and_identifier_fallback(self):
        value = make_report()
        value["identifier"] = None
        value["quality"]["independentParticipants"] = False
        text = format_scorecard(value)
        self.assertIn("Task: test-issue (done)", text)
        self.assertIn("Independent participants: no", text)

    def test_no_mutation_private_dump_or_overstated_correctness(self):
        value = make_report()
        value["private"] = "PRIVATE_SENTINEL"
        value["nativeLedger"] = {"costCents": 0}
        original = deepcopy(value)
        text = format_scorecard(value)
        self.assertEqual(original, value)
        self.assertNotIn("PRIVATE_SENTINEL", text)
        self.assertNotIn("nativeLedger", text)
        self.assertIn("Caution:", text)
        for qualifier in (
            "non-atomic",
            "not execution proof",
            "not invoice",
            "correctness",
        ):
            self.assertIn(qualifier, text)


if __name__ == "__main__":
    unittest.main()
