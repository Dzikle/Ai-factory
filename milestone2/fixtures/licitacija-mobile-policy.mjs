import path from 'node:path';
import { realpath } from 'node:fs/promises';

const root = '/paperclip/m1-first-task-worktrees/licitacija-mobile';
function isTaskChild(cwd) {
  if (typeof cwd !== 'string' || !path.posix.isAbsolute(cwd)) return false;
  const relative = path.posix.relative(root, cwd);
  return Boolean(relative) && relative !== '..' && !relative.startsWith('../')
    && !path.posix.isAbsolute(relative);
}

export async function assertMobileWorkspace(cwd, { realpathImpl = realpath } = {}) {
  if (!isTaskChild(cwd)) throw new Error('Mobile workspace scope mismatch');
  const [actualRoot, actualCwd] = await Promise.all([realpathImpl(root), realpathImpl(cwd)]);
  if (actualRoot !== root || !isTaskChild(actualCwd)) throw new Error('Mobile workspace realpath mismatch');
}

export function mobileChildEnvironment(cache, inherited = process.env) {
  return { PATH: inherited.PATH, HOME: '/tmp', CI: '1', EXPO_NO_TELEMETRY: '1', npm_config_cache: cache };
}

export function mobileCommands(mode) {
  if (mode === 'tests') return [['run', 'typecheck'], ['test'], ['run', 'lint']];
  if (mode === 'qa') return [['exec', '--', 'vitest', 'run',
    'src/api/client.test.ts', 'src/utils/safe-external-url.test.ts',
    'src/utils/native-image-upload.test.ts', 'src/utils/location-action.test.ts',
    'src/services/notification-routing.test.ts', 'src/lib/search-market-summary.test.ts']];
  throw new Error('Mobile validation mode is not supported');
}
