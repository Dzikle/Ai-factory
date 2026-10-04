"""Post one bounded answer and finish only this run's assigned Ask question."""
import argparse
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from uuid import UUID


def reply(client, context, answer):
    if not answer.strip() or len(answer.encode('utf-8')) > 8000:
        raise ValueError('Answer must contain 1–8000 UTF-8 bytes')
    path = '/api/issues/' + context['taskId']
    issue = client.request('GET', path)
    if (issue.get('companyId') != context['companyId']
            or issue.get('assigneeAgentId') != context['agentId']
            or issue.get('workMode') != 'ask' or issue.get('executionPolicy') is not None):
        raise ValueError('Only an assigned Ask question without a coding policy may be finished')
    if issue.get('executionRunId') != context['runId'] or issue.get('status') != 'in_progress':
        raise ValueError('This question is not executing under this run')
    updated = client.request('PATCH', path, {'status': 'done', 'comment': answer.strip()})
    if updated.get('status') != 'done':
        raise ValueError('Paperclip did not confirm question completion')
    return {'status': 'answered'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RunClient:
    def __init__(self, base, token, run_id):
        parsed = urlsplit(base)
        if (parsed.scheme != 'http' or parsed.hostname not in {'localhost', '127.0.0.1', 'paperclip-fork'}
                or (parsed.hostname == 'paperclip-fork' and parsed.port != 3100)
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {'', '/'}):
            raise ValueError('Use the local Paperclip API, not an external host')
        self.base = base.rstrip('/')
        self.headers = {'Authorization': 'Bearer ' + token, 'X-Paperclip-Run-Id': run_id,
                        'Content-Type': 'application/json'}
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode('utf-8')
        request = Request(self.base + path, data=data, method=method, headers=self.headers)
        with self.opener.open(request, timeout=15) as response:
            return json.loads(response.read(256_001))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answer', required=True)
    args = parser.parse_args()
    context = {key: os.environ['PAPERCLIP_' + env] for key, env in (
        ('taskId', 'TASK_ID'), ('agentId', 'AGENT_ID'), ('companyId', 'COMPANY_ID'), ('runId', 'RUN_ID'))}
    for value in context.values():
        UUID(value)
    client = RunClient(os.environ['PAPERCLIP_API_URL'], os.environ['PAPERCLIP_API_KEY'], context['runId'])
    print(json.dumps(reply(client, context, args.answer)))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOP: question completion was not confirmed (%s). Do not retry or claim completion without checking Paperclip.'
              % type(exc).__name__)
        raise SystemExit(1)
