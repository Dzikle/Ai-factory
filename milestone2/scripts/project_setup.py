"""Owner-only project/role provisioning. No dispatch, workflow engine or source edits."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler

from milestone0.scripts.paperclip_admission import Client
from milestone2.scripts.assistant_reply import NoRedirect

ROOT = Path(__file__).resolve().parents[2]


def configure(client, state, preset, instructions, *, apply=False):
    company = state['companyId']
    project_body = deepcopy(preset['project'])
    _, projects = client.request('GET', f'/api/companies/{company}/projects')
    _, agents = client.request('GET', f'/api/companies/{company}/agents')
    matches = [p for p in projects if p.get('name') == project_body['name']]
    if len(matches) > 1:
        raise ValueError('Ambiguous project; operator reconciliation required')
    project = matches[0] if matches else None
    if project:
        workspaces = project.get('workspaces') or []
        wanted = project_body['workspace']
        if (project.get('companyId') != company or project.get('description') != project_body['description']
                or len(workspaces) != 1 or any(workspaces[0].get(k) != wanted.get(k)
                                               for k in ('cwd', 'repoRef', 'repoUrl', 'metadata'))
                or project.get('executionWorkspacePolicy') != project_body.get('executionWorkspacePolicy')):
            raise ValueError('Same-name project is foreign or configuration has drifted')
    owned = {}
    for desired in preset['agents']:
        found = [a for a in agents if a.get('name') == desired['name']]
        if len(found) > 1:
            raise ValueError('Ambiguous agent; operator reconciliation required')
        if desired['adapterType'] != 'process' and desired.get('instruction') not in instructions:
            raise ValueError('Managed role instructions missing')
        if found:
            current = found[0]
            config = current.get('adapterConfig') or {}
            if (current.get('companyId') != company
                    or current.get('metadata', {}).get('setupKey') != desired['metadata']['setupKey']
                    or current.get('adapterType') != desired['adapterType']
                    or current.get('status') == 'terminated'
                    or current.get('runtimeConfig') != desired['runtimeConfig']
                    or current.get('permissions') != desired.get('permissions')
                    or set(config.get('env') or {}) != set(desired['adapterConfig'].get('env') or {})
                    or any(config.get(k) != v for k, v in desired['adapterConfig'].items() if k != 'env')):
                raise ValueError('Same-name agent is foreign or runtime configuration has drifted')
            _, bundle = client.request('GET', f'/api/agents/{current["id"]}/instructions-bundle')
            if (bundle.get('warnings') or bundle.get('legacyPromptTemplateActive')
                    or bundle.get('legacyBootstrapPromptTemplateActive')):
                raise ValueError('Managed instruction bundle has drifted')
            if desired['adapterType'] == 'process':
                # Process adapters execute code, not managed LLM role instructions.
                if bundle.get('mode') is not None or bundle.get('files'):
                    raise ValueError('Unexpected process instruction bundle')
            else:
                if (bundle.get('mode') != 'managed' or bundle.get('entryFile') != 'AGENTS.md'
                        or [f.get('path') for f in bundle.get('files', [])] != ['AGENTS.md']):
                    raise ValueError('Managed instruction bundle has drifted')
                _, entry = client.request('GET', f'/api/agents/{current["id"]}/instructions-bundle/file?path=AGENTS.md')
                if entry.get('content') != instructions[desired['instruction']]:
                    raise ValueError('Managed role instructions have drifted')
            owned[desired['name']] = current
    plugin_path = f'/api/plugins/{preset["contextPluginId"]}/config'
    _, saved = client.request('GET', plugin_path + '?companyId=' + company)
    config = deepcopy((saved or {}).get('configJson') or {})
    excluded = config.get('excludedProjectIds', [])
    if not isinstance(excluded, list) or len(excluded) > 32:
        raise ValueError('Unexpected context scope; operator reconciliation required')
    if not apply:
        return {'status': 'ready', 'mutations': False, 'projectId': project['id'] if project else None,
                'agentIds': {name: a['id'] for name, a in owned.items()}}
    if project is None:
        _, project = client.request('POST', f'/api/companies/{company}/projects', project_body, expected=(201,))
    for desired in preset['agents']:
        if desired['name'] not in owned:
            body = deepcopy(desired)
            instruction = body.pop('instruction', None)
            if body['adapterType'] != 'process':
                body['instructionsBundle'] = {'files': {'AGENTS.md': instructions[instruction]}}
            _, owned[desired['name']] = client.request('POST', f'/api/companies/{company}/agents', body,
                                                     expected=(201,))
        _, effective = client.request('GET', f'/api/companies/{company}/tools/profiles/effective/agents/'
                                       + owned[desired['name']]['id'])
        if (effective.get('allowedToolNames') or effective.get('allowedTools')
                or effective.get('installedConnections')):
            raise ValueError('Unexpected effective external MCP catalog; do not dispatch')
    if project['id'] not in excluded:
        if len(excluded) >= 32:
            raise ValueError('Context exclusion limit reached; do not dispatch')
        config['excludedProjectIds'] = [*excluded, project['id']]
        client.request('POST', plugin_path, {'companyId': company, 'configJson': config})
    return {'status': 'configured', 'projectId': project['id'],
            'agentIds': {name: a['id'] for name, a in owned.items()},
            'effectiveExternalMcpTools': [], 'dispatch': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--preset', type=Path, required=True)
    parser.add_argument('--container', default='aif-m0-paperclip-fork-paperclip-fork-1')
    parser.add_argument('--apply', action='store_true', help='Requires current owner authorization')
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding='utf-8-sig'))
    if state['baseUrl'] not in {'http://localhost:13101', 'http://127.0.0.1:13101'}:
        raise ValueError('Use the local authenticated Paperclip controller')
    preset = json.loads(args.preset.read_text(encoding='utf-8-sig'))
    instructions = {}
    for agent in preset['agents']:
        if agent['adapterType'] == 'process':
            continue
        path = (ROOT / agent['instruction']).resolve()
        path.relative_to(ROOT)
        instructions[agent['instruction']] = path.read_text(encoding='utf-8')
    workspace = preset['project']['workspace']
    revision = subprocess.run(['docker', 'exec', args.container, 'git', '-C', workspace['cwd'],
                               'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=20, check=True)
    if revision.stdout.strip() != preset['expectedSourceRevision']:
        raise ValueError('Runtime source differs from the pinned onboarding revision')
    client = Client(state['baseUrl'], state['boardApiKey'])
    client.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(client.cookies), NoRedirect())
    print(json.dumps(configure(client, state, preset, instructions, apply=args.apply)))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOP: project setup not confirmed (%s). Inspect existing resources before replay; '
              'no automatic dispatch or retry.' % type(exc).__name__)
        raise SystemExit(1)
