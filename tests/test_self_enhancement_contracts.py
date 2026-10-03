"""Contracts for the governed V1 self-enhancement lifecycle."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import yaml

from milestone1.validate_contracts import validate_self_enhancement


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "autonomy" / "contracts" / "v1" / "self-enhancement.schema.json"
POLICY = ROOT / "autonomy" / "policies" / "self-enhancement.v1.yaml"
NOW = datetime(2026, 10, 3, tzinfo=timezone.utc)
WAVE_IDS = ["orchestration", "context-knowledge", "verification-delivery", "continuous-operation"]


def sample_program() -> dict:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "program_id": "ai-factory-self-enhancement-v1",
        "request_key": "self-enhancement-2026-10-03",
        "project_id": "ai-factory",
        "repository_id": "ai-factory",
        "intent": "self_enhancement",
        "scope_verb": "implement",
        "base_revision": "0" * 40,
        "spec_path": "docs/superpowers/specs/2026-10-03-self-enhancement-lifecycle-design.md",
        "plan_path": "docs/superpowers/plans/2026-10-03-v1-self-enhancement-lifecycle.md",
        "authorization": {
            "allowed_paths": ["AGENTS.md", "autonomy/", "docs/", "milestone1/", "milestone2/", "milestone3/", "milestone4/", "tests/"],
            "allowed_actions": ["repo.read", "repo.write", "git.read", "git.diff.read", "validation.run", "knowledge.search", "memory.search", "artifact.write"],
            "remote_actions": [],
            "max_correction_rounds": 3,
            "expires_at": "2026-12-31T23:59:59Z",
        },
        "waves": deepcopy(policy["waves"]),
    }


def validate_schema(document: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)


class SelfEnhancementContractTests(unittest.TestCase):
    def test_program_has_one_authorization_and_four_ordered_waves(self) -> None:
        document = sample_program()
        validate_schema(document)
        self.assertEqual([], validate_self_enhancement(document, now=NOW))
        self.assertEqual(WAVE_IDS, [wave["id"] for wave in document["waves"]])

    def test_schema_defines_every_lifecycle_record(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue({
            "authorization", "wave", "capability_health", "verification_contract",
            "verification_digest", "deferred_finding", "outcome_report",
            "knowledge_patch", "resource_record", "knowledge_source",
        }.issubset(schema["$defs"]))

    def test_expired_or_widened_authorization_is_rejected(self) -> None:
        document = sample_program()
        document["authorization"]["expires_at"] = "2026-10-02T00:00:00Z"
        self.assertIn("authorization expired", validate_self_enhancement(document, now=NOW))
        document = sample_program()
        document["authorization"]["allowed_paths"] = ["../outside"]
        with self.assertRaises(ValidationError):
            validate_schema(document)

    def test_wave_references_are_unique_known_and_authorized(self) -> None:
        document = sample_program()
        document["waves"][1]["id"] = document["waves"][0]["id"]
        self.assertIn("wave IDs must be unique", validate_self_enhancement(document, now=NOW))
        document = sample_program()
        document["waves"][0]["blocked_by"] = ["missing"]
        self.assertIn("wave orchestration has unknown blockers: ['missing']", validate_self_enhancement(document, now=NOW))
        document = sample_program()
        document["waves"][0]["required_capabilities"] = ["cloud.superuser"]
        self.assertIn("wave orchestration exceeds authorization", validate_self_enhancement(document, now=NOW))

    def test_contracts_are_strict_and_bounded(self) -> None:
        document = sample_program()
        document["runtime_grants"] = ["*"]
        with self.assertRaises(ValidationError):
            validate_schema(document)
        document = sample_program()
        document["waves"][0]["context_budget"]["max_bytes"] = -1
        with self.assertRaises(ValidationError):
            validate_schema(document)

    def test_canonical_docs_use_governed_self_hosted_language(self) -> None:
        text = (
            "Blind live self-modification remains prohibited. Governed self-hosted development is allowed when a current human authorization defines the repository, paths, actions, budgets, stop conditions, verification, independent review, publication boundary, and rollback. The running controller may not rewrite the live state that governs its own run."
        )
        for relative in (
            "AGENTS.md", "autonomy/GOALS.md", "autonomy/GOVERNANCE.md",
            "docs/architecture/AUTONOMOUS_ENGINEERING_SYSTEM.md",
        ):
            with self.subTest(path=relative):
                self.assertIn(text, (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
