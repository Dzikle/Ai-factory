"""Independent presentation contract; run from an isolated candidate commit."""

from copy import deepcopy
import unittest

from milestone2.scorecard import format_scorecard


def report():
    return {
        "identifier": "AIF-TEST", "issueId": "test-issue", "status": "done", "runCount": 2,
        "failedRuns": 0, "recordedRetries": 0, "handoffCancellations": 2,
        "quality": {"ownerAccepted": True, "independentParticipants": True,
                    "completedStages": 4, "totalStages": 4},
        "timing": {"runtimeMs": 4000, "executionWindowMs": 5000,
                   "knownRuntimeMs": 4000, "coveredRuns": 2},
        "usage": {"inputTokens": None, "cachedInputTokens": None, "outputTokens": None,
                  "reportedCostUsd": None, "reportedCostPerOwnerAcceptedTaskUsd": None,
                  "coveredRuns": 0, "costCoveredRuns": 0, "knownInputTokens": 0,
                  "knownCachedInputTokens": 0, "knownOutputTokens": 0, "knownReportedCostUsd": 0},
        "nativeLedger": {"costCents": 0}, "private": "PRIVATE_SENTINEL",
    }


class ScorecardPresentationQA(unittest.TestCase):
    def test_task_and_quality_are_readable(self):
        text = format_scorecard(report())
        for line in ("Task: AIF-TEST (done)", "Owner accepted: yes", "Gates: 4/4",
                     "Runs: 2; failed: 0; retries: 0; handoff cancellations: 2"):
            self.assertIn(line, text)

    def test_missing_usage_is_unknown_not_free(self):
        text = format_scorecard(report())
        self.assertIn("Tokens: input unknown; cached unknown; output unknown; coverage: 0/2", text)
        self.assertIn("Reported cost: unknown USD; coverage: 0/2", text)

    def test_explicit_zero_remains_zero(self):
        value = report()
        value["usage"].update(inputTokens=0, cachedInputTokens=0, outputTokens=0,
                              reportedCostUsd=0, reportedCostPerOwnerAcceptedTaskUsd=0,
                              coveredRuns=2, costCoveredRuns=2)
        text = format_scorecard(value)
        self.assertIn("Tokens: input 0; cached 0; output 0; coverage: 2/2", text)
        self.assertIn("Reported cost: 0.000000 USD; coverage: 2/2", text)

    def test_partial_coverage_labels_known_subtotals(self):
        value = report()
        value["usage"].update(coveredRuns=1, costCoveredRuns=1, knownInputTokens=20,
                              knownCachedInputTokens=5, knownOutputTokens=3, knownReportedCostUsd=.25)
        text = format_scorecard(value)
        self.assertIn("Reported cost: unknown USD; coverage: 1/2", text)
        self.assertIn("Known subtotal: input 20; cached 5; output 3; reported 0.250000 USD", text)

    def test_partial_timings_do_not_become_complete_timings(self):
        value = report()
        value["timing"].update(runtimeMs=None, executionWindowMs=None, coveredRuns=1, knownRuntimeMs=2000)
        text = format_scorecard(value)
        self.assertIn("Runtime: unknown s; coverage: 1/2", text)
        self.assertIn("Execution window: unknown s", text)
        self.assertIn("Known runtime subtotal: 2.000 s", text)

    def test_pending_owner_and_unknown_independence(self):
        value = report()
        value["quality"].update(ownerAccepted=False, independentParticipants=None, completedStages=3)
        text = format_scorecard(value)
        self.assertIn("Owner accepted: no", text)
        self.assertIn("Independent participants: unknown", text)
        self.assertIn("Gates: 3/4", text)
        self.assertIn("Reported cost per owner-accepted task: unknown USD", text)

    def test_not_independent_and_missing_identifier(self):
        value = report()
        value["identifier"] = None
        value["quality"]["independentParticipants"] = False
        text = format_scorecard(value)
        self.assertIn("Task: test-issue (done)", text)
        self.assertIn("Independent participants: no", text)

    def test_no_mutation_private_dump_or_overstated_correctness(self):
        value = report()
        original = deepcopy(value)
        text = format_scorecard(value)
        self.assertEqual(original, value)
        self.assertNotIn("PRIVATE_SENTINEL", text)
        self.assertIn("Caution:", text)
        for qualifier in ("non-atomic", "not execution proof", "not invoice", "correctness"):
            self.assertIn(qualifier, text)


if __name__ == "__main__":
    unittest.main()
