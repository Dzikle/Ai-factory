"""Bounded owner-approved setup of one read-only assistant and existing AIF-77.

Paperclip owns all agent/run/task state. No scheduler, manual model invocation,
automatic wake retry, fixture activation, coding or publication is implemented.
"""
import argparse
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler

from milestone0.scripts.paperclip_admission import ApiError, Client
from milestone2.scripts.assistant_reply import NoRedirect

ISSUE_ID = '1b80354b-e406-429e-b452-54fa18aea88f'
PROJECT_ID = 'a5758cd0-d9c4-4f3f-a004-2194691f6ef3'
ROOT = Path(__file__).resolve().parents[2]


def configure(client, state, preset, *, apply=False):
    company = state['companyId']
    _, issue = client.request('GET', f'/api/issues/{ISSUE_ID}')
    _, project = client.request('GET', f'/api/projects/{PROJECT_ID}')
    if (issue.get('companyId') != company or project.get('companyId') != company
            or issue.get('projectId') != PROJECT_ID):
        raise ValueError('Target question/project does not match the selected company')
    if issue.get('executionRunId') or issue.get('checkoutRunId'):
        raise ValueError('Target question already has an active execution/checkout')
    if issue.get('executionPolicy') is not None:
        raise ValueError('A coding-policy task cannot be repurposed as this Ask question')
    _, agents = client.request('GET', f'/api/companies/{company}/agents')
    existing = [agent for agent in agents if agent.get('name') == preset['name']]
    if len(existing) > 1 or (existing and existing[0].get('metadata', {}).get('setupKey')
                            != preset['metadata']['setupKey']):
        raise ValueError('Same-name agent is not this setup; do not overwrite it')
    agent_id = existing[0]['id'] if existing else None
    needs_assignment = issue.get('assigneeAgentId') != agent_id or bool(issue.get('assigneeUserId')) or not agent_id
    if existing:
        if needs_assignment:
            raise ValueError('Existing agent requires operator runtime verification before any new assignment')
        if issue.get('workMode') != 'ask':
            raise ValueError('Existing assignment is not the authorized Ask question')
        return {'status': 'existing_no_changes', 'mutations': False, 'agentId': agent_id,
                'issueId': ISSUE_ID, 'runtimeConfigurationVerified': False}
    if needs_assignment and (issue.get('status') not in {'todo', 'backlog'} or issue.get('assigneeAgentId')):
        raise ValueError('Question is no longer unassigned pending work')
    if not apply:
        return {'status': 'ready', 'mutations': False, 'agentId': agent_id, 'issueId': ISSUE_ID}
    if not existing:
        _, agent = client.request('POST', f'/api/companies/{company}/agents', preset, expected=(201,))
        agent_id = agent['id']
    if needs_assignment:
        client.request('PATCH', f'/api/issues/{ISSUE_ID}', {
            'assigneeAgentId': agent_id, 'assigneeUserId': None, 'workMode': 'ask',
            'executionWorkspacePreference': 'shared_workspace',
            'executionWorkspaceSettings': {'mode': 'shared_workspace'},
        })
    return {'status': 'configured', 'agentId': agent_id, 'issueId': ISSUE_ID,
            'dispatch': 'Paperclip native assignment wake; no separate workflow engine'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Requires current owner authorization; may start AIF-77')
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding='utf-8-sig'))
    if state['baseUrl'] not in {'http://localhost:13101', 'http://127.0.0.1:13101'}:
        raise ValueError('Use this local authenticated Paperclip controller')
    preset = json.loads((ROOT / 'milestone2/config/licitacija-assistant.json').read_text())
    native = preset.pop('nativeConfig')
    preset['adapterConfig']['env']['OPENCODE_CONFIG_CONTENT'] = json.dumps(native)
    instructions = (ROOT / 'milestone2/fixtures/licitacija-assistant.md').read_text()
    preset['instructionsBundle'] = {'files': {'AGENTS.md': instructions}}
    client = Client(state['baseUrl'], state['boardApiKey'])
    client.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(client.cookies), NoRedirect())
    print(json.dumps(configure(client, state, preset, apply=args.apply)))


if __name__ == '__main__':
    try:
        main()
    except (ApiError, URLError, ValueError, OSError, KeyError, TypeError):
        print('STOP: setup not confirmed; inspect existing Paperclip agent/task state before retrying. No automatic retry or fixture activation.')
        raise SystemExit(1)
