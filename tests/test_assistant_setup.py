"""Operator provisioning boundaries; native execution is a separate live check."""
import importlib.util
import unittest
from copy import deepcopy


class AssistantSetupTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('milestone2.scripts.assistant_setup'),
                             'The bounded assistant provisioning command is not implemented')
        from milestone2.scripts.assistant_setup import configure
        self.configure = configure
        self.state = {'companyId': 'company'}
        self.preset = {'name': 'Licitacija Assistant', 'metadata': {'setupKey': 'licitacija-read-only-v1'}}
        self.client = FixtureClient()

    def test_dry_run_has_no_writes(self):
        result = self.configure(self.client, self.state, self.preset, apply=False)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(self.client.writes, [])

    def test_apply_assigns_only_target_question_to_new_native_agent(self):
        result = self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(result['agentId'], 'assistant')
        self.assertEqual(self.client.issue['assigneeAgentId'], 'assistant')
        self.assertIsNone(self.client.issue['assigneeUserId'])
        self.assertEqual(self.client.issue['workMode'], 'ask')
        self.assertEqual(self.client.issue['executionWorkspacePreference'], 'shared_workspace')
        self.assertEqual([item[0] for item in self.client.writes], ['POST', 'PATCH'])

    def test_replay_does_not_create_or_reassign_again(self):
        self.configure(self.client, self.state, self.preset, apply=True)
        self.client.writes.clear()
        self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_running_task_prevents_all_writes(self):
        self.client.issue['executionRunId'] = 'active'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_foreign_project_prevents_all_writes(self):
        self.client.project['companyId'] = 'other'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_completed_unassigned_question_does_not_create_an_agent(self):
        self.client.issue['status'] = 'done'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_other_assignee_prevents_agent_creation(self):
        self.client.issue['assigneeAgentId'] = 'other-agent'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_same_name_unrelated_agent_is_not_overwritten(self):
        self.client.agents.append({'id': 'other', 'name': 'Licitacija Assistant', 'metadata': {}})
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_existing_agent_is_not_reused_for_new_assignment_without_runtime_verification(self):
        self.client.agents.append({'id': 'assistant', **deepcopy(self.preset),
                                   'adapterConfig': {'dangerouslySkipPermissions': True}})
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_coding_policy_cannot_be_repurposed_as_a_question(self):
        self.client.issue['executionPolicy'] = {'stages': []}
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_assigned_replay_must_still_be_ask_without_coding_policy(self):
        for update in [{'workMode': 'standard'}, {'executionPolicy': {'stages': []}}]:
            client = FixtureClient()
            self.configure(client, self.state, self.preset, apply=True)
            client.writes.clear()
            client.issue.update(update)
            with self.assertRaises(ValueError):
                self.configure(client, self.state, self.preset, apply=True)
            self.assertEqual(client.writes, [])


class FixtureClient:
    """Only the external API boundary is doubled; provisioning logic is real."""
    def __init__(self):
        from milestone2.scripts.assistant_setup import ISSUE_ID, PROJECT_ID
        self.issue = {'id': ISSUE_ID, 'companyId': 'company', 'projectId': PROJECT_ID,
                      'status': 'todo', 'assigneeUserId': 'human', 'assigneeAgentId': None,
                      'executionRunId': None, 'checkoutRunId': None}
        self.project = {'id': PROJECT_ID, 'companyId': 'company'}
        self.agents, self.writes = [], []

    def request(self, method, path, body=None, **kwargs):
        if method == 'GET':
            if path.endswith('/agents'):
                return 200, deepcopy(self.agents)
            if '/issues/' in path:
                return 200, deepcopy(self.issue)
            if '/projects/' in path:
                return 200, deepcopy(self.project)
        self.writes.append((method, path, deepcopy(body)))
        if method == 'POST' and path.endswith('/agents'):
            self.agents.append({'id': 'assistant', **deepcopy(body)})
            return 201, deepcopy(self.agents[-1])
        if method == 'PATCH' and '/issues/' in path:
            self.issue.update(deepcopy(body))
            return 200, deepcopy(self.issue)
        raise AssertionError(f'Unexpected operation: {method} {path}')
