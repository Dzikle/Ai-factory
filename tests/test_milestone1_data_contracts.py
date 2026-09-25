"""Behavioral checks for the remaining Git-owned Milestone 1.1 contracts."""

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from milestone1 import validate_contracts


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "autonomy" / "contracts" / "v1"
DIGEST = "a" * 64


def validate(name: str, document: dict) -> None:
    path = SCHEMAS / f"{name}.schema.json"
    assert path.is_file(), f"missing contract {path}"
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)


class IntegrationDataContractTests(unittest.TestCase):
    def test_context_plan_requires_finite_domain_and_total_budgets(self) -> None:
        plan = {
            "schema_version": 1, "task_id": "T-1", "project_id": "ai-factory", "role": "developer",
            "total_budget": {"max_tokens": 600, "max_bytes": 2048},
            "queries": [
                {"domain": "docs", "purpose": "canonical_context", "text": "lease recovery",
                 "max_hits": 2, "max_tokens": 200, "max_bytes": 600,
                 "filters": {"project_id": "ai-factory", "statuses": ["canonical"]}},
                {"domain": "memory", "purpose": "historical_lessons", "text": "lease recovery",
                 "max_hits": 1, "max_tokens": 100, "max_bytes": 300,
                 "filters": {"project_id": "ai-factory", "statuses": ["active"]}},
            ],
        }
        validate("context-query-plan", plan)
        self.assertTrue(hasattr(validate_contracts, "check_context_budget"))
        self.assertEqual([], validate_contracts.check_context_budget(plan))
        plan["queries"][1]["max_tokens"] = 500
        self.assertIn("query token budgets exceed total", validate_contracts.check_context_budget(plan))
        plan["queries"][1]["max_tokens"] = 100
        plan["queries"][1]["filters"]["project_id"] = "another-project"
        self.assertIn("query memory escapes project ai-factory", validate_contracts.check_context_budget(plan))
        plan["queries"][1]["filters"]["project_id"] = "ai-factory"
        plan["queries"][1]["max_hits"] = 0
        with self.assertRaises(ValidationError):
            validate("context-query-plan", plan)

    def test_provenance_cannot_promote_memory_to_canonical_truth(self) -> None:
        source = {
            "schema_version": 1, "source_system": "mempalace", "source_id": "M-1",
            "source_uri": "memory://M-1", "source_version": "7", "observed_at": "2026-09-25T09:00:00Z",
            "authority": "historical", "status": "active", "canonical": False,
            "content_sha256": DIGEST,
        }
        validate("provenance-envelope", source)
        source["canonical"] = True
        with self.assertRaises(ValidationError):
            validate("provenance-envelope", source)
        source.update(source_system="git", authority="canonical")
        with self.assertRaises(ValidationError):
            validate("provenance-envelope", source)
        source["source_revision"] = "62760ac"
        validate("provenance-envelope", source)
        source["observed_at"] = "not-a-timestamp"
        with self.assertRaises(ValidationError):
            validate("provenance-envelope", source)

    def test_normalized_events_have_typed_task_run_review_qa_and_telemetry_payloads(self) -> None:
        base = {
            "schema_version": 1, "event_id": "E-1", "source_system": "paperclip",
            "source_id": "event-1", "source_version": "4", "recorded_at": "2026-09-25T09:00:00Z",
            "project_id": "ai-factory", "task_id": "T-1",
        }
        samples = [
            ("task", {"status": "in_progress"}),
            ("run", {"run_id": "R-1", "status": "completed", "agent_id": "A-dev"}),
            ("review", {"run_id": "R-2", "subject_run_id": "R-1", "reviewer_agent_id": "A-review", "verdict": "accepted"}),
            ("qa", {"run_id": "R-3", "subject_run_id": "R-1", "qa_agent_id": "A-qa", "verdict": "accepted"}),
            ("telemetry", {"run_id": "R-1", "metric": "tokens_input", "value": 125, "unit": "tokens"}),
        ]
        for kind, payload in samples:
            with self.subTest(kind=kind):
                validate("normalized-event", {**base, "kind": kind, "payload": payload})
        with self.assertRaises(ValidationError):
            validate("normalized-event", {**base, "kind": "review", "payload": {"verdict": "accepted"}})

    def test_memory_record_requires_original_evidence_and_retention(self) -> None:
        memory = {
            "schema_version": 1, "memory_id": "M-1", "project_id": "ai-factory", "scope": "project",
            "kind": "incident", "status": "active", "specialist_role": "qa",
            "content_ref": "memory://M-1", "content_sha256": DIGEST,
            "observed_at": "2026-09-25T09:00:00Z", "review_after": "2026-10-25T09:00:00Z",
            "retention_until": "2027-09-25T09:00:00Z", "supersedes": [],
            "source_refs": [{"source_system": "paperclip", "source_id": "R-1", "source_version": "1"}],
        }
        validate("memory-record", memory)
        memory["source_refs"] = []
        with self.assertRaises(ValidationError):
            validate("memory-record", memory)

    def test_promotion_contract_is_a_proposal_not_an_approval(self) -> None:
        proposal = {
            "schema_version": 1, "proposal_id": "P-1", "project_id": "ai-factory",
            "candidate_kind": "deterministic_check", "candidate_path": "checks/lease-recovery",
            "source_memory_ids": ["M-1", "M-2"], "evidence_refs": ["artifact://A-1"],
            "eval_refs": ["evals/lease-recovery-v1"], "status": "proposed",
        }
        validate("promotion-proposal", proposal)
        proposal["status"] = "approved"
        with self.assertRaises(ValidationError):
            validate("promotion-proposal", proposal)

    def test_model_policy_keeps_native_harness_outside_api_gateway(self) -> None:
        policy = {
            "schema_version": 1, "policy_id": "developer-standard", "task_class": "implementation",
            "risk": "normal", "role": "developer", "lane": "native_harness",
            "primary_binding_ref": "paperclip:developer-native", "fallback_binding_refs": ["paperclip:developer-alternate"],
            "max_attempts": 2, "gateway": "none", "escalation": "human_review",
        }
        validate("model-selection-policy", policy)
        policy["gateway"] = "litellm_core"
        with self.assertRaises(ValidationError):
            validate("model-selection-policy", policy)

    def test_validation_check_is_bounded_and_records_deterministic_invocation(self) -> None:
        check = {
            "schema_version": 1, "check_id": "unit-tests", "task_class": "implementation",
            "argv": ["python", "-m", "unittest"], "working_directory": ".",
            "timeout_seconds": 300, "expected_exit_code": 0,
        }
        validate("validation-check", check)
        check["timeout_seconds"] = 0
        with self.assertRaises(ValidationError):
            validate("validation-check", check)
        check["timeout_seconds"] = 300
        check["working_directory"] = "../outside-worktree"
        with self.assertRaises(ValidationError):
            validate("validation-check", check)

    def test_task_request_can_only_narrow_role_project_and_skill_capabilities(self) -> None:
        request = {
            "schema_version": 1, "task_id": "T-1", "project_id": "ai-factory", "role": "reviewer",
            "skill_ids": ["code-review"], "required_capabilities": ["repo.read"],
            "denied_capabilities": ["repo.merge"],
        }
        validate("task-capability-request", request)
        vocabulary, roles, project, skills = self.load_policy_bundle()
        self.assertTrue(hasattr(validate_contracts, "check_task_request"))
        self.assertEqual([], validate_contracts.check_task_request(request, vocabulary, roles, project, skills))
        request["required_capabilities"].append("repo.write")
        self.assertIn("task requires unavailable capability repo.write", validate_contracts.check_task_request(request, vocabulary, roles, project, skills))
        request["required_capabilities"].remove("repo.write")
        request["denied_capabilities"].append("validation.run")
        self.assertIn("task denies required skill capability validation.run", validate_contracts.check_task_request(request, vocabulary, roles, project, skills))
        request["runtime_grants"] = ["*"]
        with self.assertRaises(ValidationError):
            validate("task-capability-request", request)

    def test_review_and_qa_outcomes_cannot_self_approve(self) -> None:
        outcome = {
            "schema_version": 1, "kind": "review", "task_id": "T-1", "run_id": "R-2",
            "subject_run_id": "R-1", "actor_agent_id": "A-review", "subject_agent_id": "A-dev",
            "verdict": "accepted", "evidence_refs": ["artifact://review-1"],
            "recorded_at": "2026-09-25T09:00:00Z",
        }
        validate("quality-outcome", outcome)
        self.assertTrue(hasattr(validate_contracts, "check_quality_independence"))
        self.assertEqual([], validate_contracts.check_quality_independence(outcome))
        outcome["subject_agent_id"] = "A-review"
        self.assertIn("review actor must differ from implementer", validate_contracts.check_quality_independence(outcome))
        outcome["subject_agent_id"] = "A-dev"
        outcome["run_id"] = "R-1"
        self.assertIn("review run must differ from subject run", validate_contracts.check_quality_independence(outcome))

    @staticmethod
    def load_policy_bundle() -> tuple[dict, dict, dict, list[dict]]:
        import yaml

        vocabulary = yaml.safe_load((ROOT / "autonomy" / "capabilities" / "definitions.v1.yaml").read_text(encoding="utf-8"))
        roles = yaml.safe_load((ROOT / "autonomy" / "policies" / "roles.v1.yaml").read_text(encoding="utf-8"))
        project = yaml.safe_load((ROOT / "autonomy" / "projects" / "examples" / "ai-factory.v1.yaml").read_text(encoding="utf-8"))
        path = ROOT / "docs" / "implementation" / "pocs" / "agent-skills" / ".agents" / "skills" / "code-review" / "ai-factory.yaml"
        skills = [yaml.safe_load(path.read_text(encoding="utf-8"))]
        return vocabulary, roles, project, skills


if __name__ == "__main__":
    unittest.main()
