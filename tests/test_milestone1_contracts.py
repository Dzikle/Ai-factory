"""Boundary tests for the first Git-owned Milestone 1 contracts."""

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError
import yaml

from milestone1.validate_contracts import check_consistency
from milestone1.git_projection import collect_snapshot


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "autonomy" / "contracts" / "v1"


def validate(name: str, document: dict) -> None:
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)


class CanonicalContractTests(unittest.TestCase):
    def test_first_task_plan_is_in_project_canonical_projection_scope(self) -> None:
        overlay = yaml.safe_load(
            (ROOT / "autonomy" / "projects" / "examples" / "ai-factory.v1.yaml").read_text(encoding="utf-8")
        )
        repository = overlay["repositories"][0]
        snapshot = collect_snapshot(
            ROOT, project_id=overlay["project_id"], repository_id=repository["id"],
            remote=repository["remote"], canonical_paths=repository["canonical_paths"],
        )
        self.assertIn("docs/implementation/IMPLEMENTATION_KICKOFF.md", {item["path"] for item in snapshot})

    def test_existing_agent_skills_sidecars_are_compatible(self) -> None:
        base = ROOT / "docs" / "implementation" / "pocs" / "agent-skills" / ".agents" / "skills"
        for skill in ("repository-discovery", "code-review"):
            with self.subTest(skill=skill):
                sidecar = yaml.safe_load((base / skill / "ai-factory.yaml").read_text(encoding="utf-8"))
                validate("skill-sidecar", sidecar)

    def test_skill_sidecar_cannot_grant_runtime_tools(self) -> None:
        sidecar = {
            "schema_version": 1,
            "skill": "repository-discovery",
            "skill_version": "0.1.0",
            "lifecycle": "experimental",
            "risk": "low",
            "roles": ["researcher"],
            "required_capabilities": ["repo.read"],
            "runtime_grants": ["*"],
        }
        with self.assertRaises(ValidationError):
            validate("skill-sidecar", sidecar)

    def test_project_overlay_is_scoped_and_cannot_override_source_precedence(self) -> None:
        overlay = yaml.safe_load(
            (ROOT / "autonomy" / "projects" / "examples" / "ai-factory.v1.yaml").read_text(encoding="utf-8")
        )
        validate("project-overlay", overlay)
        overlay["source_precedence"] = ["memory", "git"]
        with self.assertRaises(ValidationError):
            validate("project-overlay", overlay)

    def test_capability_vocabulary_defines_semantics_not_active_grants(self) -> None:
        vocabulary = yaml.safe_load(
            (ROOT / "autonomy" / "capabilities" / "definitions.v1.yaml").read_text(encoding="utf-8")
        )
        validate("capability-definitions", vocabulary)
        vocabulary["capabilities"][0]["provider_tool"] = "unscoped_admin"
        with self.assertRaises(ValidationError):
            validate("capability-definitions", vocabulary)

    def test_role_policy_is_deny_default_and_has_no_wildcard(self) -> None:
        policy = yaml.safe_load(
            (ROOT / "autonomy" / "policies" / "roles.v1.yaml").read_text(encoding="utf-8")
        )
        validate("role-policy", policy)
        policy["default"] = "allow"
        with self.assertRaises(ValidationError):
            validate("role-policy", policy)

    def test_checked_in_policy_references_are_consistent(self) -> None:
        vocabulary, roles, overlay, skills = self.load_bundle()
        self.assertEqual([], check_consistency(vocabulary, roles, overlay, skills))

    def test_unknown_capability_is_rejected_before_runtime_materialization(self) -> None:
        vocabulary, roles, overlay, skills = self.load_bundle()
        overlay["allowed_capabilities"].append("cloud.superuser")
        self.assertIn("project allows undefined capability cloud.superuser", check_consistency(vocabulary, roles, overlay, skills))

    def test_duplicate_capability_semantics_are_rejected(self) -> None:
        vocabulary, roles, overlay, skills = self.load_bundle()
        vocabulary["capabilities"].append({
            "id": "repo.read", "description": "Conflicting meaning", "effect": "admin", "lifecycle": "active"
        })
        self.assertIn("duplicate capability definition repo.read", check_consistency(vocabulary, roles, overlay, skills))

    def test_allow_deny_overlap_and_disabled_grant_are_rejected(self) -> None:
        vocabulary, roles, overlay, skills = self.load_bundle()
        roles["roles"]["reviewer"]["allowed_capabilities"].append("repo.write")
        overlay["allowed_capabilities"].append("code.graph.search")
        errors = check_consistency(vocabulary, roles, overlay, skills)
        self.assertIn("role reviewer both allows and denies repo.write", errors)
        self.assertIn("project allows disabled capability code.graph.search", errors)

    def test_skill_required_capability_must_survive_project_and_role_policy(self) -> None:
        vocabulary, roles, overlay, skills = self.load_bundle()
        overlay["allowed_capabilities"].remove("validation.run")
        errors = check_consistency(vocabulary, roles, overlay, skills)
        self.assertIn("skill code-review role reviewer lacks required capability validation.run in project policy", errors)

        overlay["allowed_capabilities"].append("validation.run")
        roles["roles"]["reviewer"]["allowed_capabilities"].remove("validation.run")
        errors = check_consistency(vocabulary, roles, overlay, skills)
        self.assertIn("skill code-review role reviewer lacks required capability validation.run in role policy", errors)

    @staticmethod
    def load_bundle() -> tuple[dict, dict, dict, list[dict]]:
        vocabulary = yaml.safe_load((ROOT / "autonomy" / "capabilities" / "definitions.v1.yaml").read_text(encoding="utf-8"))
        roles = yaml.safe_load((ROOT / "autonomy" / "policies" / "roles.v1.yaml").read_text(encoding="utf-8"))
        overlay = yaml.safe_load((ROOT / "autonomy" / "projects" / "examples" / "ai-factory.v1.yaml").read_text(encoding="utf-8"))
        base = ROOT / "docs" / "implementation" / "pocs" / "agent-skills" / ".agents" / "skills"
        skills = [yaml.safe_load((base / skill / "ai-factory.yaml").read_text(encoding="utf-8")) for skill in ("repository-discovery", "code-review")]
        return vocabulary, roles, overlay, skills


if __name__ == "__main__":
    unittest.main()
