"""Question completion must not gain general task or repository write access."""
import importlib.util
import unittest
from copy import deepcopy
from unittest.mock import patch


class AssistantReplyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('milestone2.scripts.assistant_reply'),
                             'The bounded native question-reply helper is missing')
        from milestone2.scripts.assistant_reply import reply
        self.reply = reply
        self.client = ReplyClient()
        self.context = {'taskId': 'question', 'agentId': 'assistant',
                        'companyId': 'company', 'runId': 'run'}

    def test_reply_finishes_only_the_active_assigned_ask_question(self):
        self.reply(self.client, self.context, 'I read the local homepage.')
        self.assertEqual(self.client.writes, [
            ('PATCH', '/api/issues/question', {'status': 'done', 'comment': 'I read the local homepage.'})])

    def test_foreign_or_coding_or_inactive_task_cannot_be_finished(self):
        for field, value in [('companyId', 'other'), ('assigneeAgentId', 'other'),
                             ('workMode', 'standard'), ('executionRunId', 'other'),
                             ('status', 'cancelled'), ('executionPolicy', {'stages': []})]:
            with self.subTest(field=field):
                client = ReplyClient()
                client.issue[field] = value
                with self.assertRaises(ValueError):
                    self.reply(client, self.context, 'An answer')
                self.assertEqual(client.writes, [])

    def test_blank_or_unbounded_answer_has_no_side_effects(self):
        for text in ['', '  ', 'a' * 8001]:
            with self.assertRaises(ValueError):
                self.reply(self.client, self.context, text)
        self.assertEqual(self.client.writes, [])

    def test_native_controller_service_name_is_accepted_but_external_hosts_are_not(self):
        from milestone2.scripts.assistant_reply import RunClient
        client = RunClient('http://paperclip-fork:3100', 'test-token', 'run')
        self.assertEqual(client.base, 'http://paperclip-fork:3100')
        for url in ['http://external.example:3100', 'http://localhost@external.example:3100',
                    'http://paperclip-fork:3100/elsewhere', 'https://paperclip-fork:3100']:
            with self.assertRaises(ValueError):
                RunClient(url, 'test-token', 'run')

    def test_unconfirmed_completion_is_not_reported_as_answered(self):
        client = ReplyClient()
        client.override_patch_status = 'in_review'
        with self.assertRaises(ValueError):
            self.reply(client, self.context, 'An answer')

    def test_already_done_question_does_not_claim_this_runs_answer_was_posted(self):
        self.client.issue.update(status='done', executionRunId=None)
        with self.assertRaises(ValueError):
            self.reply(self.client, self.context, 'An answer')
        self.assertEqual(self.client.writes, [])

    def test_native_bearer_request_ignores_ambient_http_proxy(self):
        from milestone2.scripts.assistant_reply import RunClient
        hosts = []

        class StopBeforeNetwork:
            debuglevel = 0

            def __init__(self, host, **kwargs):
                hosts.append(host)
                raise OSError('Test stops before opening a connection')

        with patch('urllib.request.getproxies', return_value={'http': 'http://external-proxy.example:3128'}), \
                patch('urllib.request.proxy_bypass', return_value=False), \
                patch('http.client.HTTPConnection', StopBeforeNetwork):
            client = RunClient('http://paperclip-fork:3100', 'test-token', 'run')
            with self.assertRaises(OSError):
                client.request('GET', '/api/issues/question')
        self.assertEqual(hosts, ['paperclip-fork:3100'])


class ReplyClient:
    def __init__(self):
        self.issue = {'id': 'question', 'companyId': 'company',
                      'assigneeAgentId': 'assistant', 'executionRunId': 'run',
                      'status': 'in_progress', 'workMode': 'ask', 'executionPolicy': None}
        self.writes = []

    def request(self, method, path, body=None):
        if method == 'GET':
            return deepcopy(self.issue)
        self.writes.append((method, path, deepcopy(body)))
        self.issue.update(body)
        if hasattr(self, 'override_patch_status'):
            self.issue['status'] = self.override_patch_status
        return deepcopy(self.issue)
