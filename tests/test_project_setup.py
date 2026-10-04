"""Project provisioning contract; only the external Paperclip boundary is doubled."""
import importlib.util
import unittest
from copy import deepcopy


class ProjectSetupTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('milestone2.scripts.project_setup'),
                             'Project-scoped provisioning is not implemented')
        from milestone2.scripts.project_setup import configure
        self.configure = configure
        self.state = {'companyId': 'company'}
        self.preset = {
            'setupKey': 'travel-agent-v1',
            'project': {'name': 'Travel Agent', 'description': 'Owned travel setup',
                        'workspace': {'name': 'Travel source', 'cwd': '/paperclip/travel-agent-source',
                                      'repoRef': '1' * 40, 'metadata': {'setupKey': 'travel-agent-v1'}}},
            'agents': [
                {'name': 'Travel Agent Assistant', 'role': 'general', 'adapterType': 'codex_local',
                 'adapterConfig': {'cwd': '/paperclip/travel-agent-source', 'model': 'gpt-5.6-sol'},
                 'runtimeConfig': {'heartbeat': {'enabled': False, 'maxConcurrentRuns': 1}},
                 'metadata': {'setupKey': 'travel-agent-v1:assistant'}, 'instruction': 'assistant.md'}
            ],
            'contextPluginId': 'plugin',
        }
        self.instructions = {'assistant.md': 'Read only the assigned travel repository.'}
        self.client = FixtureClient()

    def test_preview_performs_no_writes(self):
        result = self.configure(self.client, self.state, self.preset, self.instructions)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(self.client.writes, [])

    def test_apply_creates_own_project_agents_and_preserves_other_context_scope(self):
        result = self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(result['projectId'], 'travel-project')
        self.assertEqual(result['agentIds'], {'Travel Agent Assistant': 'travel-assistant'})
        self.assertEqual(self.client.config['excludedProjectIds'], ['licitacija-project', 'travel-project'])
        self.assertTrue(self.client.config['preserveThisSetting'])
        self.assertEqual(self.client.agents[0]['instructionsBundle']['files']['AGENTS.md'],
                         'Read only the assigned travel repository.')
        self.assertFalse(any('/issues' in path or '/wakeup' in path for _, path, _ in self.client.writes))

    def test_replay_is_read_only_and_does_not_duplicate_resources(self):
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        result = self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(result['projectId'], 'travel-project')
        self.assertEqual(self.client.writes, [])
        self.assertEqual(len(self.client.projects), 1)
        self.assertEqual(len(self.client.agents), 1)

    def test_foreign_same_name_project_stops_before_writes(self):
        self.client.projects = [{'id': 'other', 'companyId': 'company', 'name': 'Travel Agent',
                                 'description': 'Someone else', 'workspaces': []}]
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_foreign_same_name_agent_stops_before_project_creation(self):
        self.client.agents = [{'id': 'other', 'name': 'Travel Agent Assistant', 'metadata': {}}]
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_unexpected_effective_mcp_catalog_stops_without_scope_change(self):
        self.client.allowed = ['unexpected:privileged-tool']
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.config['excludedProjectIds'], ['licitacija-project'])

    def test_existing_runtime_drift_is_not_silently_overwritten(self):
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        self.client.agents[0]['adapterConfig']['model'] = 'different'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_unexpected_credential_key_stops_replay_before_writes(self):
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        self.client.agents[0]['adapterConfig']['env'] = {'GH_TOKEN': '[redacted]'}
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_changed_managed_instructions_stop_replay_before_writes(self):
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        self.client.agents[0]['instructionsBundle']['files']['AGENTS.md'] = 'Publish without approval.'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_extra_instruction_file_stops_replay_before_writes(self):
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        self.client.agents[0]['instructionsBundle']['files']['extra.md'] = 'Unexpected instructions'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_process_roles_use_their_script_without_managed_llm_instructions(self):
        agent = self.preset['agents'][0]
        agent['adapterType'] = 'process'
        agent['adapterConfig'] = {'command': 'node', 'args': ['/paperclip/travel-agent-stage.mjs', 'tests']}
        agent.pop('instruction')
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertNotIn('instructionsBundle', self.client.agents[0])
        self.client.writes.clear()
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])


class FixtureClient:
    def __init__(self):
        self.projects, self.agents, self.writes, self.allowed = [], [], [], []
        self.config = {'excludedProjectIds': ['licitacija-project'], 'preserveThisSetting': True}

    def request(self, method, path, body=None, **kwargs):
        if method == 'GET':
            if path.endswith('/projects'):
                return 200, deepcopy(self.projects)
            if path.endswith('/agents'):
                return 200, deepcopy(self.agents)
            if path.endswith('/instructions-bundle'):
                if self.agents[0]['adapterType'] == 'process':
                    return 200, {'mode': None, 'entryFile': 'AGENTS.md', 'files': [], 'warnings': []}
                return 200, {'mode': 'managed', 'entryFile': 'AGENTS.md', 'warnings': [],
                             'files': [{'path': k} for k in self.agents[0]['instructionsBundle']['files']]}
            if path.endswith('/instructions-bundle/file?path=AGENTS.md'):
                return 200, {'content': self.agents[0]['instructionsBundle']['files']['AGENTS.md']}
            if '/effective/agents/' in path:
                return 200, {'allowedToolNames': self.allowed, 'allowedTools': self.allowed,
                             'installedConnections': []}
            if '/plugins/plugin/config?' in path:
                return 200, {'configJson': deepcopy(self.config)}
        self.writes.append((method, path, deepcopy(body)))
        if method == 'POST' and path.endswith('/projects'):
            project = deepcopy(body)
            workspace = project.pop('workspace')
            project.update(id='travel-project', companyId='company', workspaces=[workspace])
            self.projects.append(project)
            return 201, deepcopy(project)
        if method == 'POST' and path.endswith('/agents'):
            agent = {'id': 'travel-assistant', **deepcopy(body), 'companyId': 'company', 'status': 'idle'}
            self.agents.append(agent)
            return 201, deepcopy(agent)
        if method == 'POST' and path == '/api/plugins/plugin/config':
            self.config = deepcopy(body['configJson'])
            return 200, {'configJson': deepcopy(self.config)}
        raise AssertionError(f'Unexpected API operation: {method} {path}')
