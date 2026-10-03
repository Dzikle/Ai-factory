"""Canonical operational Agent Skills packages and sidecars."""

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "autonomy" / "contracts" / "v1"
SKILLS = ("repository-preflight", "verified-commit", "publication-status",
          "review-resolution", "deferred-finding", "scoped-audit")


def validate(name, document):
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(document)


class OperationalSkillTests(unittest.TestCase):
    def test_every_operational_skill_has_portable_markdown_and_valid_sidecar(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                directory = ROOT / "autonomy" / "skills" / name
                self.assertTrue((directory / "SKILL.md").is_file())
                sidecar = yaml.safe_load((directory / "ai-factory.yaml").read_text(encoding="utf-8"))
                validate("skill-sidecar", sidecar)
                self.assertEqual(name, sidecar["skill"])
                self.assertNotIn("runtime_grants", sidecar)

    def test_reviewer_skills_deny_write_and_publication_has_no_agent_grant(self):
        for name in ("review-resolution", "scoped-audit"):
            sidecar = yaml.safe_load((ROOT / "autonomy" / "skills" / name / "ai-factory.yaml").read_text())
            self.assertIn("repo.write", sidecar.get("denied_capabilities", []))
        sidecar = yaml.safe_load((ROOT / "autonomy" / "skills" / "publication-status" / "ai-factory.yaml").read_text())
        self.assertNotIn("repo.write", sidecar.get("required_capabilities", []))

    def test_skills_are_allowlisted_and_reuse_existing_commands(self):
        overlay = yaml.safe_load((ROOT / "autonomy" / "projects" / "examples" / "ai-factory.v1.yaml").read_text())
        for name in SKILLS:
            self.assertIn(name, overlay["allowed_skills"])
        commands = ("python -m milestone2.task", "python -m milestone2.publish preflight",
                    "python -m milestone2.publish publish", "python -m milestone3.check",
                    "python -m milestone2.program status")
        for name in SKILLS:
            text = (ROOT / "autonomy" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(any(command in text for command in commands), name)


if __name__ == "__main__":
    unittest.main()
