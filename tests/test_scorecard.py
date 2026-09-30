"""Exercise the real CLI/API boundary: unknown is not zero; GETs only."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPANY = "00000000-0000-0000-0000-000000000010"
ISSUE = "00000000-0000-0000-0000-000000000030"
RUN_IDS = [f"00000000-0000-0000-0000-00000000004{i}" for i in range(2)]
STAGE_IDS = [f"00000000-0000-0000-0000-00000000005{i}" for i in range(4)]
AGENT_IDS = [f"00000000-0000-0000-0000-00000000006{i}" for i in range(4)]


class ScorecardCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.requests = []
        self.issue = {
            "id": ISSUE, "identifier": "AIF-49", "companyId": COMPANY,
            "status": "done", "description": "PRIVATE_DESCRIPTION_SENTINEL",
            "createdAt": "2026-09-28T00:00:00Z", "completedAt": "2026-09-28T00:10:00Z",
            "executionPolicy": {"stages": [
                {"id": sid, "type": "review" if index < 3 else "approval",
                 "participants": ([{"type": "agent", "agentId": AGENT_IDS[index]}]
                                  if index < 3 else [{"type": "user", "userId": "owner-1"}])}
                for index, sid in enumerate(STAGE_IDS)
            ]},
            "executionState": {"completedStageIds": STAGE_IDS.copy(),
                               "lastDecisionId": "00000000-0000-0000-0000-000000000070",
                               "lastDecisionOutcome": "approved", "changesRequestedCount": 0,
                               "returnAssignee": {"type": "agent", "agentId": AGENT_IDS[3]}},
        }
        self.runs = [{
            "id": rid, "companyId": COMPANY, "agentId": AGENT_IDS[3],
            "status": "cancelled", "errorCode": "issue_reassigned", "retryOfRunId": None,
            "startedAt": f"2026-09-28T00:00:0{index * 3}Z",
            "finishedAt": f"2026-09-28T00:00:0{index * 3 + 2}Z", "usageJson": None,
            "contextSnapshot": {"issueId": ISSUE, "private": "PRIVATE_CONTEXT_SENTINEL"},
            "stdoutExcerpt": "PRIVATE_OUTPUT_SENTINEL",
        } for index, rid in enumerate(RUN_IDS)]
        self.cost = {"issueId": ISSUE, "issueCount": 1, "includeDescendants": True,
                     "costCents": 0, "inputTokens": 0, "cachedInputTokens": 0,
                     "outputTokens": 0, "runCount": 2, "runtimeMs": 4000}
        self.api_failure = None
        self.rows_override = None
        self.activity = [{
            "companyId": COMPANY, "entityId": ISSUE, "entityType": "issue", "action": "issue.updated",
            "actorType": "agent", "actorId": AGENT_IDS[3], "runId": RUN_IDS[0],
            "details": {"executionState": {"currentStageIndex": 0, "currentStageId": STAGE_IDS[0],
                                            "completedStageIds": []}, "_previous": {"executionState": None}},
        }]
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, value):
                body = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                test.requests.append(("GET", self.path))
                if test.api_failure and self.path != "/api/issues/AIF-49":
                    self.respond(test.api_failure, {"error": "PRIVATE_ERROR_SENTINEL"})
                elif self.path == "/api/issues/AIF-49":
                    self.respond(200, test.issue)
                elif self.path == f"/api/issues/{ISSUE}/runs":
                    self.respond(200, test.rows_override if test.rows_override is not None else
                                 [{"runId": r["id"], "agentId": r["agentId"]} for r in test.runs])
                elif self.path == f"/api/issues/{ISSUE}/cost-summary":
                    self.respond(200, test.cost)
                elif self.path == f"/api/issues/{ISSUE}/activity":
                    self.respond(200, test.activity)
                elif self.path.startswith("/api/heartbeat-runs/"):
                    self.respond(200, next(r for r in test.runs if r["id"] == self.path.rsplit("/", 1)[1]))
                else:
                    self.respond(404, {"error": "Unexpected path"})

            def do_POST(self):
                test.requests.append(("POST", self.path))
                self.respond(405, {})

            do_PATCH = do_POST
            do_DELETE = do_POST

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        Thread(target=self.server.serve_forever, kwargs={"poll_interval": .05}, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.state = {"baseUrl": f"http://127.0.0.1:{self.server.server_port}", "companyId": COMPANY,
                      "userId": "owner-1", "boardApiKey": "PRIVATE_TOKEN_SENTINEL"}

    def cli(self, *, as_json=True):
        state_path = self.directory / "state.json"
        state_path.write_text(json.dumps(self.state), encoding="utf-8")
        return subprocess.run([sys.executable, "-m", "milestone2.task", "--state", str(state_path),
                               *(["--json"] if as_json else []), "scorecard", "AIF-49"],
                              cwd=ROOT, capture_output=True, text=True, timeout=15)

    def report(self):
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def measured(self):
        for index, run in enumerate(self.runs):
            run["status"] = "succeeded"
            run["usageJson"] = {"inputTokens": 20 + index * 10, "cachedInputTokens": 5,
                                "outputTokens": 3, "costUsd": .25, "costStatus": "reported",
                                "provider": "test-provider", "model": "test-model"}

    def test_recovery_return_owner_does_not_relabel_the_developer(self):
        self.issue["executionState"]["returnAssignee"]["agentId"] = AGENT_IDS[0]
        self.assertTrue(self.report()["quality"]["independentParticipants"])

    def test_missing_assignment_evidence_means_unknown_not_independent(self):
        self.activity = []
        self.assertIsNone(self.report()["quality"]["independentParticipants"])

    def test_activity_actor_must_match_the_linked_native_run(self):
        self.activity[0]["actorId"] = AGENT_IDS[0]
        self.assertIsNone(self.report()["quality"]["independentParticipants"])

    def test_missing_previous_state_is_not_a_proven_initial_handoff(self):
        self.activity[0]["details"]["_previous"] = {}
        self.assertIsNone(self.report()["quality"]["independentParticipants"])

    def test_foreign_activity_cannot_supply_assignment_evidence(self):
        self.activity[0]["entityId"] = "foreign"
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("scope", result.stderr)

    def test_empty_ledger_and_missing_usage_do_not_mean_free(self):
        report = self.report()
        self.assertIsNone(report["usage"]["inputTokens"])
        self.assertIsNone(report["usage"]["reportedCostUsd"])
        self.assertEqual(0, report["usage"]["coveredRuns"])
        self.assertEqual(2, report["runCount"])
        self.assertEqual(4000, report["timing"]["runtimeMs"])
        self.assertEqual(5000, report["timing"]["executionWindowMs"])

    def test_handoff_cancellation_does_not_negate_native_owner_acceptance(self):
        report = self.report()
        self.assertTrue(report["quality"]["ownerAccepted"])
        self.assertTrue(report["quality"]["independentParticipants"])
        self.assertEqual(2, report["handoffCancellations"])
        self.assertEqual(0, report["failedRuns"])

    def test_gets_are_issue_scoped_and_private_fields_are_not_exported(self):
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({("GET", "/api/issues/AIF-49"), ("GET", f"/api/issues/{ISSUE}/runs"),
                          ("GET", f"/api/issues/{ISSUE}/cost-summary"),
                          ("GET", f"/api/issues/{ISSUE}/activity"),
                          *[("GET", f"/api/heartbeat-runs/{rid}") for rid in RUN_IDS]}, set(self.requests))
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)

    def test_full_reported_coverage_preserves_measured_totals(self):
        self.measured()
        usage = self.report()["usage"]
        self.assertEqual(50, usage["inputTokens"])
        self.assertEqual(10, usage["cachedInputTokens"])
        self.assertEqual(6, usage["outputTokens"])
        self.assertEqual(.5, usage["reportedCostUsd"])
        self.assertEqual(.5, usage["reportedCostPerOwnerAcceptedTaskUsd"])
        self.assertEqual(2, usage["coveredRuns"])

    def test_explicit_reported_zero_is_not_missing(self):
        self.measured()
        for run in self.runs:
            run["usageJson"].update(inputTokens=0, cachedInputTokens=0, outputTokens=0, costUsd=0)
        self.assertEqual(0, self.report()["usage"]["reportedCostUsd"])

    def test_partial_usage_keeps_known_subtotal_but_withholds_total(self):
        self.measured()
        self.runs[1]["usageJson"] = None
        usage = self.report()["usage"]
        self.assertIsNone(usage["inputTokens"])
        self.assertIsNone(usage["reportedCostUsd"])
        self.assertEqual(20, usage["knownInputTokens"])
        self.assertEqual(.25, usage["knownReportedCostUsd"])
        self.assertEqual(1, usage["coveredRuns"])

    def test_interrupted_accounting_is_an_observed_subtotal_not_a_complete_total(self):
        self.measured()
        for run in self.runs:
            run.update(status="cancelled", errorCode="issue_reassigned")
            run["usageJson"]["usageCompleteness"] = "partial"
        usage = self.report()["usage"]
        self.assertIsNone(usage["inputTokens"])
        self.assertIsNone(usage["reportedCostUsd"])
        self.assertEqual(50, usage["knownInputTokens"])
        self.assertEqual(.5, usage["knownReportedCostUsd"])
        self.assertEqual(0, usage["coveredRuns"])
        self.assertEqual(0, usage["costCoveredRuns"])
        self.assertEqual(2, usage["partialCoveredRuns"])
        self.assertEqual(2, usage["partialCostCoveredRuns"])
        human = self.cli(as_json=False)
        self.assertEqual(0, human.returncode, human.stderr)
        self.assertIn("Observed partial accounting: usage 2; cost 2", human.stdout)

    def test_legacy_unmarked_cancelled_usage_is_not_verified_accounting(self):
        self.measured()
        for run in self.runs:
            run.update(status="cancelled", errorCode="issue_reassigned")
            run["usageJson"].update(inputTokens=0, cachedInputTokens=0,
                                     outputTokens=0, costUsd=0)
        usage = self.report()["usage"]
        self.assertEqual(0, usage["coveredRuns"])
        self.assertEqual(0, usage["costCoveredRuns"])
        self.assertEqual(0, usage["partialCoveredRuns"])
        self.assertIsNone(usage["reportedCostUsd"])
        self.assertIsNone(usage["reportedCostPerOwnerAcceptedTaskUsd"])

    def test_one_partial_record_prevents_a_mixed_complete_total(self):
        self.measured()
        self.runs[0]["usageJson"]["usageCompleteness"] = "complete"
        self.runs[1]["usageJson"]["usageCompleteness"] = "partial"
        usage = self.report()["usage"]
        self.assertIsNone(usage["outputTokens"])
        self.assertIsNone(usage["reportedCostPerOwnerAcceptedTaskUsd"])
        self.assertEqual(50, usage["knownInputTokens"])
        self.assertEqual(1, usage["coveredRuns"])
        self.assertEqual(1, usage["partialCoveredRuns"])

    def test_unrecognized_completeness_is_not_promoted_to_full_coverage(self):
        self.measured()
        self.runs[0]["usageJson"]["usageCompleteness"] = "unverified"
        usage = self.report()["usage"]
        self.assertIsNone(usage["inputTokens"])
        self.assertIsNone(usage["reportedCostUsd"])
        self.assertEqual(1, usage["coveredRuns"])
        self.assertEqual(30, usage["knownInputTokens"])

    def test_malformed_completeness_is_unknown_without_crashing(self):
        self.measured()
        self.runs[0]["usageJson"]["usageCompleteness"] = {"untrusted": True}
        usage = self.report()["usage"]
        self.assertIsNone(usage["inputTokens"])
        self.assertEqual(1, usage["coveredRuns"])
        self.assertEqual(30, usage["knownInputTokens"])

    def test_unpriced_zero_does_not_become_reported_free_cost(self):
        self.measured()
        self.runs[1]["usageJson"].update(costUsd=0, costStatus="unpriced")
        usage = self.report()["usage"]
        self.assertEqual(50, usage["inputTokens"])
        self.assertIsNone(usage["reportedCostUsd"])
        self.assertEqual(1, usage["costCoveredRuns"])

    def test_no_native_owner_gate_is_not_accepted_correctness(self):
        self.issue["executionPolicy"]["stages"] = []
        self.issue["executionState"]["completedStageIds"] = []
        report = self.report()
        self.assertFalse(report["quality"]["ownerAccepted"])
        self.assertIsNone(report["usage"]["reportedCostPerOwnerAcceptedTaskUsd"])

    def test_self_review_is_not_independent(self):
        self.issue["executionPolicy"]["stages"][1]["participants"][0]["agentId"] = AGENT_IDS[3]
        self.assertFalse(self.report()["quality"]["independentParticipants"])

    def test_distinct_stage_participants_are_required(self):
        self.issue["executionPolicy"]["stages"][1]["participants"][0]["agentId"] = AGENT_IDS[0]
        self.assertFalse(self.report()["quality"]["independentParticipants"])

    def test_live_run_does_not_produce_final_runtime_or_usage_totals(self):
        self.measured()
        self.runs[1].update(status="running", finishedAt=None)
        report = self.report()
        self.assertIsNone(report["timing"]["runtimeMs"])
        self.assertIsNone(report["usage"]["reportedCostUsd"])
        self.assertEqual(2000, report["timing"]["knownRuntimeMs"])

    def test_booleans_and_negative_or_nonfinite_usage_are_unknown(self):
        self.measured()
        self.runs[1]["usageJson"].update(inputTokens=True, outputTokens=-1, costUsd=float("nan"))
        report = self.report()
        self.assertIsNone(report["usage"]["inputTokens"])
        self.assertIsNone(report["usage"]["reportedCostUsd"])
        self.assertNotIn("NaN", json.dumps(report))

    def test_retries_count_lineage_not_pipeline_stages(self):
        self.runs[1].update(status="failed", errorCode="adapter_failed", retryOfRunId=RUN_IDS[0])
        report = self.report()
        self.assertEqual(1, report["recordedRetries"])
        self.assertEqual(1, report["failedRuns"])

    def test_descendant_summary_cannot_be_attributed_to_one_task(self):
        self.cost["issueCount"] = 2
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("descendant", result.stderr)

    def test_foreign_company_is_rejected_before_more_reads(self):
        self.issue["companyId"] = "foreign"
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([("GET", "/api/issues/AIF-49")], self.requests)
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)

    def test_duplicate_runs_cannot_double_count(self):
        self.rows_override = [{"runId": RUN_IDS[0], "agentId": AGENT_IDS[3]}] * 2
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("duplicate", result.stderr)

    def test_run_identity_mismatch_cannot_borrow_other_task_usage(self):
        self.runs[1]["contextSnapshot"]["issueId"] = "foreign"
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("scope", result.stderr)

    def test_api_denial_is_redacted_without_retry(self):
        self.api_failure = 403
        result = self.cli()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("403", result.stderr)
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)
        self.assertEqual(2, len(self.requests))

    def test_human_output_succeeds_without_exporting_private_data(self):
        result = self.cli(as_json=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("AIF-49", result.stdout)
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
