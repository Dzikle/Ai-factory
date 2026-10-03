"""One-authorization program submission and replay behavior."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

import yaml

from milestone2.program import (
    authorization_digest, classify_task, program_execution_policy,
    read_program_status, submit_program,
)


ROOT = Path(__file__).resolve().parents[1]
COMPANY = "00000000-0000-0000-0000-000000000010"
PROJECT = "00000000-0000-0000-0000-000000000020"
DEV, VALIDATOR, REVIEWER, QA = [f"00000000-0000-0000-0000-00000000000{i}" for i in range(1, 5)]


def sample_program() -> dict:
    policy = yaml.safe_load((ROOT / "autonomy/policies/self-enhancement.v1.yaml").read_text())
    return {
        "schema_version": 1, "program_id": "ai-factory-self-enhancement-v1",
        "request_key": "self-enhancement-test", "project_id": "ai-factory",
        "repository_id": "ai-factory", "intent": "self_enhancement", "scope_verb": "implement",
        "base_revision": "a" * 40, "spec_path": "docs/spec.md", "plan_path": "docs/plan.md",
        "authorization": {"allowed_paths": ["autonomy/", "milestone2/", "tests/"],
            "allowed_actions": ["repo.read", "repo.write", "git.read", "git.diff.read", "validation.run", "knowledge.search", "memory.search", "artifact.write"],
            "remote_actions": [], "max_correction_rounds": 3, "expires_at": "2026-12-31T23:59:59Z"},
        "waves": deepcopy(policy["waves"]),
    }


class FakePaperclip:
    def __init__(self):
        self.issues, self.documents, self.comments = {}, {}, []
        self.next_id = 1

    def request(self, method, path, payload=None, expected=None):
        if method == "GET" and path == f"/api/projects/{PROJECT}":
            return 200, {"id": PROJECT, "companyId": COMPANY}
        if method == "GET" and path.startswith("/api/agents/"):
            return 200, {"id": path.rsplit("/", 1)[1], "companyId": COMPANY, "status": "idle"}
        if method == "POST" and path == f"/api/companies/{COMPANY}/issues":
            for issue in self.issues.values():
                if issue.get("idempotencyKey") == payload["idempotencyKey"]:
                    return 200, deepcopy(issue)
            issue_id = f"00000000-0000-0000-0000-{self.next_id:012d}"
            self.next_id += 1
            issue = {**deepcopy(payload), "id": issue_id, "identifier": f"AIF-{self.next_id}", "companyId": COMPANY}
            self.issues[issue_id] = issue
            return 201, deepcopy(issue)
        if method == "PUT" and "/documents/" in path:
            key = path.rsplit("/", 1)[1]
            current = self.documents.get(key)
            if current and current["content"] != payload["content"]:
                raise ValueError("document conflict")
            value = current or {**deepcopy(payload), "id": f"doc-{key}", "revisionId": f"rev-{key}"}
            self.documents[key] = value
            return 200, deepcopy(value)
        if method == "POST" and path.endswith("/comments"):
            if not any(row.get("clientRequestId") == payload.get("clientRequestId") for row in self.comments):
                self.comments.append(deepcopy(payload))
            return 201, deepcopy(payload)
        if method == "PATCH" and path.startswith("/api/issues/"):
            issue = self.issues[path.split("/")[3]]
            issue.update(deepcopy(payload))
            return 200, deepcopy(issue)
        if method == "GET" and path.startswith("/api/issues/") and "/documents/" not in path:
            return 200, deepcopy(self.issues[path.rsplit("/", 1)[1]])
        if method == "GET" and path.startswith(f"/api/companies/{COMPANY}/issues"):
            return 200, list(deepcopy(self.issues).values())
        if method == "GET" and "/documents/authorization" in path:
            return 200, deepcopy(self.documents["authorization"])
        raise AssertionError((method, path, payload))


class ProgramTests(unittest.TestCase):
    def workflow(self):
        return {"projectId": PROJECT, "developerAgentId": DEV, "validatorAgentId": VALIDATOR,
                "reviewerAgentId": REVIEWER, "qaAgentId": QA}

    def test_program_policy_has_independent_checks_without_repeated_user_gate(self):
        policy = program_execution_policy(DEV, VALIDATOR, REVIEWER, qa_agent_id=QA)
        self.assertEqual(["review", "review", "review"], [s["type"] for s in policy["stages"]])
        self.assertEqual(3, policy["maxReviewRounds"])

    def test_routing_is_deterministic_and_read_only_work_has_no_workspace(self):
        decision = classify_task(intent="audit", scope_verb="report", size="small", risk="low", change_type="read_only")
        self.assertEqual("read_only", decision["execution_mode"])
        self.assertFalse(decision["requires_workspace"])
        self.assertEqual("reduced", decision["verification_profile"])
        with self.assertRaises(ValueError):
            classify_task(intent="free form prose!", scope_verb="report", size="small", risk="low", change_type="read_only")

    def test_digest_is_canonical_and_scope_sensitive(self):
        program = sample_program()
        digest = authorization_digest(program)
        self.assertEqual(64, len(digest))
        reordered = json.loads(json.dumps(program, sort_keys=True))
        self.assertEqual(digest, authorization_digest(reordered))
        reordered["authorization"]["allowed_paths"].append("docs/")
        self.assertNotEqual(digest, authorization_digest(reordered))

    def test_submit_creates_one_parent_and_dependency_ordered_children_and_replays(self):
        client = FakePaperclip()
        result = submit_program(client, COMPANY, {"userId": "owner"}, self.workflow(), sample_program(), start=True,
                                now=datetime(2026, 10, 3, tzinfo=timezone.utc))
        self.assertEqual(5, len(client.issues))
        children = [client.issues[row["id"]] for row in result["waves"]]
        self.assertEqual([], children[0]["blockedByIssueIds"])
        self.assertEqual([children[0]["id"]], children[1]["blockedByIssueIds"])
        self.assertEqual("todo", children[0]["status"])
        self.assertEqual(1, len(client.comments))
        self.assertEqual(result, submit_program(client, COMPANY, {"userId": "owner"}, self.workflow(), sample_program(), start=True,
                                                now=datetime(2026, 10, 3, tzinfo=timezone.utc)))

    def test_read_status_rejects_unexpected_or_cross_company_children(self):
        client = FakePaperclip()
        result = submit_program(client, COMPANY, {"userId": "owner"}, self.workflow(), sample_program(), start=False,
                                now=datetime(2026, 10, 3, tzinfo=timezone.utc))
        status = read_program_status(client, result["parentId"], COMPANY)
        self.assertEqual(4, len(status["waves"]))
        child = client.issues[result["waves"][0]["id"]]
        child["companyId"] = "another-company"
        with self.assertRaisesRegex(ValueError, "company"):
            read_program_status(client, result["parentId"], COMPANY)

    def test_start_rejects_read_only_program(self):
        program = sample_program()
        program["waves"][0].update(size="small", risk="low", change_type="read_only")
        with self.assertRaisesRegex(ValueError, "read-only"):
            submit_program(FakePaperclip(), COMPANY, {"userId": "owner"}, self.workflow(), program, start=True,
                           now=datetime(2026, 10, 3, tzinfo=timezone.utc))


class InterruptingPaperclip(FakePaperclip):
    """Fail exactly once at the nth request to simulate an interruption."""

    def __init__(self, fail_at):
        super().__init__()
        self.fail_at = fail_at
        self.calls = 0

    def request(self, method, path, payload=None, expected=None):
        self.calls += 1
        if self.calls == self.fail_at:
            self.fail_at = -1
            raise ConnectionError("simulated interruption")
        return super().request(method, path, payload, expected)


class ProgramReplayTests(unittest.TestCase):
    def workflow(self):
        return {"projectId": PROJECT, "developerAgentId": DEV, "validatorAgentId": VALIDATOR,
                "reviewerAgentId": REVIEWER, "qaAgentId": QA}

    def submit(self, client, **kwargs):
        return submit_program(client, COMPANY, {"userId": "owner"}, self.workflow(), sample_program(), start=True,
                              now=datetime(2026, 10, 3, tzinfo=timezone.utc), **kwargs)

    def test_interrupted_submission_replays_without_duplicates(self):
        # Full-run request indices: 1-5 scope reads, 6 parent, 7 document,
        # 8 receipt, 9-12 children, 13-20 blocker reads/writes, 21-22 start.
        expected = self.submit(FakePaperclip())
        for fail_at in (7, 8, 9, 10, 11, 12, 13, 16, 22):
            with self.subTest(fail_at=fail_at):
                client = InterruptingPaperclip(fail_at)
                with self.assertRaises(ConnectionError):
                    self.submit(client)
                result = self.submit(client)
                self.assertEqual(expected, result)
                self.assertEqual(5, len(client.issues))
                self.assertEqual(1, len(client.comments))


if __name__ == "__main__":
    unittest.main()
