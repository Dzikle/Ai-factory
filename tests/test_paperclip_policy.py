"""The Git template must map to one Paperclip-owned execution policy."""

import unittest
from uuid import uuid4

from milestone1.paperclip_policy import engineering_execution_policy


class EngineeringExecutionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.developer = str(uuid4())
        self.validator = str(uuid4())
        self.reviewer = str(uuid4())
        self.qa = str(uuid4())
        self.approver = "board-user-1"

    def policy(self, *, qa: bool = False) -> dict:
        return engineering_execution_policy(
            developer_agent_id=self.developer,
            validator_agent_id=self.validator,
            reviewer_agent_id=self.reviewer,
            qa_agent_id=self.qa if qa else None,
            approver_user_id=self.approver,
        )

    def test_standard_path_has_ordered_independent_gates(self) -> None:
        policy = self.policy()
        self.assertEqual("normal", policy["mode"])
        self.assertTrue(policy["commentRequired"])
        self.assertEqual(3, policy["maxReviewRounds"])
        self.assertEqual(["review", "review", "approval"], [s["type"] for s in policy["stages"]])
        self.assertEqual(
            [self.validator, self.reviewer],
            [s["participants"][0]["agentId"] for s in policy["stages"][:2]],
        )
        self.assertEqual(self.approver, policy["stages"][-1]["participants"][0]["userId"])
        self.assertNotIn("agentId", policy["stages"][-1]["participants"][0])

    def test_qa_is_an_additional_independent_review_stage(self) -> None:
        policy = self.policy(qa=True)
        self.assertEqual(["review", "review", "review", "approval"], [s["type"] for s in policy["stages"]])
        self.assertEqual(self.qa, policy["stages"][2]["participants"][0]["agentId"])

    def test_rejects_same_agent_in_two_roles(self) -> None:
        for duplicate in ("validator_agent_id", "reviewer_agent_id", "qa_agent_id"):
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                engineering_execution_policy(
                    developer_agent_id=self.developer,
                    validator_agent_id=self.developer if duplicate == "validator_agent_id" else self.validator,
                    reviewer_agent_id=self.validator if duplicate == "reviewer_agent_id" else self.reviewer,
                    qa_agent_id=self.reviewer if duplicate == "qa_agent_id" else self.qa,
                    approver_user_id=self.approver,
                )

    def test_rejects_missing_or_invalid_principals(self) -> None:
        with self.assertRaises(ValueError):
            engineering_execution_policy(self.developer, "not-a-guid", self.reviewer, self.approver)
        with self.assertRaises(ValueError):
            engineering_execution_policy(self.developer, self.validator, self.reviewer, " ")


if __name__ == "__main__":
    unittest.main()
