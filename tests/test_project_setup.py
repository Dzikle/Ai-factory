"""Project provisioning contract; only the external Paperclip boundary is doubled."""
import importlib.util
import unittest
from copy import deepcopy
from unittest.mock import patch


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

    def test_source_probe_admits_only_clean_pinned_checkout_as_controller_user(self):
        from milestone2.scripts.project_setup import probe_source

        completed = [
            type('Completed', (), {'stdout': '', 'stderr': '', 'returncode': 0})(),
            type('Completed', (), {'stdout': 'a' * 40 + '\n', 'stderr': '', 'returncode': 0})(),
        ]
        with patch('milestone2.scripts.project_setup.subprocess.run', side_effect=completed) as run:
            probe_source('paperclip', '/paperclip/source', 'a' * 40)

        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(command[:5], ['docker', 'exec', '--user', '1000:1000', 'paperclip'])
            self.assertNotIn('-c', command)
            self.assertFalse(any('safe.directory' in arg for arg in command))
        self.assertEqual(run.call_args_list[0].args[0][5:],
                         ['git', '-C', '/paperclip/source', 'status', '--porcelain'])
        self.assertEqual(run.call_args_list[1].args[0][5:],
                         ['git', '-C', '/paperclip/source', 'rev-parse', 'HEAD'])

    def test_source_probe_reports_dirty_or_wrong_revision_checkout(self):
        from milestone2.scripts.project_setup import probe_source

        for outputs, message in [
            ([type('Completed', (), {'stdout': ' M file.py\n', 'stderr': '', 'returncode': 0})()],
             'not clean'),
            ([type('Completed', (), {'stdout': '', 'stderr': '', 'returncode': 0})(),
              type('Completed', (), {'stdout': 'b' * 40 + '\n', 'stderr': '', 'returncode': 0})()],
             'pinned onboarding revision'),
        ]:
            with self.subTest(message=message), patch(
                    'milestone2.scripts.project_setup.subprocess.run', side_effect=outputs):
                with self.assertRaisesRegex(ValueError, message):
                    probe_source('paperclip', '/paperclip/source', 'a' * 40)

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

    def prepare_owned_upgrade(self):
        self.preset['project']['workspace'].update(sourceType='local_path', defaultRef='1' * 40, isPrimary=True)
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        original = deepcopy(self.preset['project'])
        self.preset['projectUpgrade'] = {'projectId': 'travel-project', 'from': original}
        self.client.projects[0]['workspaces'][0]['id'] = 'workspace'
        self.preset['project']['workspace']['cwd'] = '/paperclip/travel-ready-source'
        self.preset['project']['description'] = 'Owned travel setup with ready source'
        self.client.writes.clear()

    def test_explicit_owned_project_upgrade_keeps_ids_and_does_not_dispatch(self):
        self.prepare_owned_upgrade()
        preview = self.configure(self.client, self.state, self.preset, self.instructions)
        self.assertTrue(preview.get('projectUpgradeRequired'))
        self.assertEqual(self.client.writes, [])
        result = self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(result['projectId'], 'travel-project')
        self.assertEqual(self.client.projects[0]['workspaces'][0]['id'], 'workspace')
        self.assertEqual(self.client.projects[0]['workspaces'][0]['cwd'], '/paperclip/travel-ready-source')
        self.assertEqual(self.client.projects[0]['description'], 'Owned travel setup with ready source')
        self.assertFalse(any('/issues' in path or '/wakeup' in path for _, path, _ in self.client.writes))
        self.client.writes.clear()
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_owned_upgrade_can_complete_after_workspace_patch_only(self):
        self.prepare_owned_upgrade()
        self.client.projects[0]['workspaces'][0].update(self.preset['project']['workspace'])
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.projects[0]['description'], 'Owned travel setup with ready source')

    def test_upgrade_rejects_wrong_project_id_or_unrecognized_workspace_before_writes(self):
        for drift in ('id', 'workspace'):
            with self.subTest(drift=drift):
                self.setUp()
                self.prepare_owned_upgrade()
                if drift == 'id':
                    self.preset['projectUpgrade']['projectId'] = 'another-project'
                else:
                    self.client.projects[0]['workspaces'][0]['cwd'] = '/foreign'
                with self.assertRaises(ValueError):
                    self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
                self.assertEqual(self.client.writes, [])

    def test_upgrade_rejects_foreign_id_even_when_target_configuration_matches(self):
        self.prepare_owned_upgrade()
        self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.client.writes.clear()
        self.client.projects[0]['id'] = 'foreign-project'
        with self.assertRaises(ValueError):
            self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
        self.assertEqual(self.client.writes, [])

    def test_upgrade_does_not_recreate_a_missing_or_renamed_approved_project(self):
        for missing in (True, False):
            with self.subTest(missing=missing):
                self.setUp()
                self.prepare_owned_upgrade()
                if missing:
                    self.client.projects.clear()
                else:
                    self.client.projects[0]['name'] = 'Renamed'
                with self.assertRaises(ValueError):
                    self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
                self.assertEqual(self.client.writes, [])

    def test_upgrade_rejects_execution_workspace_drift_after_target_is_installed(self):
        for key, value in [('sourceType', 'remote_managed'), ('defaultRef', 'foreign-branch'),
                           ('isPrimary', False), ('name', 'Foreign workspace')]:
            with self.subTest(key=key):
                self.setUp()
                self.prepare_owned_upgrade()
                self.configure(self.client, self.state, self.preset, self.instructions, apply=True)
                self.client.writes.clear()
                self.client.projects[0]['workspaces'][0][key] = value
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
        if method == 'PATCH' and path == '/api/projects/travel-project/workspaces/workspace':
            self.projects[0]['workspaces'][0].update(deepcopy(body))
            return 200, deepcopy(self.projects[0]['workspaces'][0])
        if method == 'PATCH' and path == '/api/projects/travel-project':
            self.projects[0].update(deepcopy(body))
            return 200, deepcopy(self.projects[0])
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
