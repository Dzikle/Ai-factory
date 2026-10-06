import assert from 'node:assert/strict';
import { test } from 'node:test';

const policyUrl = new URL('./licitacija-mobile-policy.mjs', import.meta.url);
async function policy() {
  const available = await import(policyUrl).catch(() => null);
  assert.ok(available, 'Mobile stage policy must be implemented before roles are attached');
  return available;
}

const root = '/paperclip/m1-first-task-worktrees/licitacija-mobile';
const cwd = `${root}/AIF-test`;

test('mobile validation accepts its task child, not another project or the source root', async () => {
  const { assertMobileWorkspace } = await policy();
  await assertMobileWorkspace(cwd, { realpathImpl: async value => value });
  for (const other of [root, '/paperclip/licitacija-mobile-source', `${root}-other/AIF-test`,
    `${root}/../travel-agent/AIF-test`, 'relative/path']) {
    await assert.rejects(assertMobileWorkspace(other, {
      realpathImpl: async () => { throw new Error('unexpected filesystem access'); },
    }), /Mobile workspace scope/);
  }
});

test('mobile validation rejects symlink redirection before cloning', async () => {
  const { assertMobileWorkspace } = await policy();
  await assert.rejects(assertMobileWorkspace(cwd, {
    realpathImpl: async value => value === cwd ? '/paperclip/travel-agent/task' : value,
  }), /Mobile workspace realpath/);
  await assert.rejects(assertMobileWorkspace(cwd, {
    realpathImpl: async value => `/redirected${value}`,
  }), /Mobile workspace realpath/);
});

test('validation environment excludes controller, provider, and owner credentials', async () => {
  const { mobileChildEnvironment } = await policy();
  const env = mobileChildEnvironment('/tmp/test-cache', {
    PATH: '/test/bin', PAPERCLIP_API_KEY: 'private', GH_TOKEN: 'private',
    OPENAI_API_KEY: 'private', EXPO_PUBLIC_API_BASE_URL: 'https://production.invalid',
  });
  assert.deepEqual(Object.keys(env).sort(), ['CI', 'EXPO_NO_TELEMETRY', 'HOME', 'PATH',
    'npm_config_cache']);
  assert.equal(env.npm_config_cache, '/tmp/test-cache');
  assert.equal(env.EXPO_PUBLIC_API_BASE_URL, undefined);
});

test('invalid stage cannot fall through into QA execution', async () => {
  const { mobileCommands } = await policy();
  assert.throws(() => mobileCommands('deploy'), /Mobile validation mode/);
  assert.throws(() => mobileCommands(undefined), /Mobile validation mode/);
  assert.ok(mobileCommands('tests').length > 0);
  assert.ok(mobileCommands('qa').length > 0);
});
