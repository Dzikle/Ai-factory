import path from 'node:path';
import { realpath } from 'node:fs/promises';

const root = '/paperclip/m1-first-task-worktrees/travel-agent';

function isTaskChild(cwd) {
  if (typeof cwd !== 'string' || !path.posix.isAbsolute(cwd)) return false;
  const relative = path.posix.relative(root, cwd);
  return Boolean(relative) && relative !== '..' && !relative.startsWith('../')
    && !path.posix.isAbsolute(relative);
}

export async function assertTravelWorkspace(cwd, { realpathImpl = realpath } = {}) {
  if (!isTaskChild(cwd)) throw new Error('Travel Agent workspace scope mismatch');
  // Check before cloning: a lexical child can still redirect to another project.
  const [actualRoot, actualCwd] = await Promise.all([realpathImpl(root), realpathImpl(cwd)]);
  if (actualRoot !== root || !isTaskChild(actualCwd)) {
    throw new Error('Travel Agent workspace realpath mismatch');
  }
}
