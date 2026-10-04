import assert from 'node:assert/strict';
import { test } from 'node:test';
import { assertTravelWorkspace } from './travel-agent-workspace.mjs';

const root = '/paperclip/m1-first-task-worktrees/travel-agent';
const cwd = `${root}/AIF-test`;

test('accepts only a task child of the Travel Agent worktree directory', async () => {
  await assertTravelWorkspace(cwd, { realpathImpl: async (value) => value });
});

for (const rejected of ['/paperclip/m1-first-task-worktrees/other-project/AIF-test',
  `${root}-other/AIF-test`, root, `${root}/../other-project/AIF-test`, 'relative/path']) {
  test(`rejects ${rejected} before filesystem lookup or cloning`, async () => {
    let reads = 0;
    await assert.rejects(assertTravelWorkspace(rejected, {
      realpathImpl: async () => { reads += 1; throw new Error('must not read'); },
    }), /Travel Agent workspace/);
    assert.equal(reads, 0);
  });
}

test('rejects a symlink redirect to another project', async () => {
  await assert.rejects(assertTravelWorkspace(cwd, {
    realpathImpl: async (value) => value === cwd ? '/paperclip/other-project/task' : value,
  }), /Travel Agent workspace/);
});

test('rejects a redirected project root', async () => {
  await assert.rejects(assertTravelWorkspace(cwd, {
    realpathImpl: async (value) => `/redirected${value}`,
  }), /Travel Agent workspace/);
});
