import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { verifyPreview } from './chicago-4d-preview-freshness.mjs';

const revision = '123456789';
async function fixture(t, mode) {
  const root = await mkdtemp(join(tmpdir(), 'preview-freshness-'));
  await mkdir(join(root, 'walk/js'), { recursive: true });
  const files = { 'build.json': JSON.stringify({ tier: 'dev', sha: revision }),
    'walk/js/humans.js': 'export const clothHuman = true;',
    'walk/js/fabric.js': 'export const fabric = true;',
    'walk/js/main.js': 'export const scene = true;',
    'walk/js/parked-transport.js': 'export const carriage = true;' };
  for (const [name, body] of Object.entries(files)) await writeFile(join(root, name), body);
  let rounds = 0;
  const seen = [];
  const server = createServer((request, response) => {
    const url = new URL(request.url, 'http://fixture');
    const name = url.pathname.replace('/4d/dev/', '');
    if (name === 'build.json') rounds++;
    seen.push({ name, noCache: request.headers['cache-control'], verify: url.searchParams.has('verify') });
    if (mode === 'http-error') { response.writeHead(503).end(); return; }
    const stale = mode === 'stale' || (mode === 'eventual' && rounds === 1);
    if (name === 'build.json' && stale) response.end(JSON.stringify({ tier: 'dev', sha: 'abcdef012' }));
    else if (name === 'walk/js/parked-transport.js' && mode === 'mixed') response.end('old parked carriage code');
    else response.end(files[name]);
  });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  t.after(async () => { await new Promise(done => server.close(done)); await rm(root, { recursive: true, force: true }); });
  return { root, origin: `http://127.0.0.1:${server.address().port}`, seen };
}

test('actual live marker and all four modules match generated artifact', async t => {
  const f = await fixture(t, 'fresh');
  const r = await verifyPreview({ origin: f.origin, previewRoot: f.root, timeoutMs: 1000, pollMs: 1 });
  assert.equal(r.status, 'PASS_LIVE_DEV_MATCHES_UPLOADED_PREVIEW');
  assert.equal(r.attempts.length, 1);
  assert.equal(f.seen.length, 5);
  assert.ok(f.seen.every(x => x.noCache === 'no-cache' && x.verify));
});

test('HTTP200 old build stays a failure', async t => {
  const f = await fixture(t, 'stale');
  const r = await verifyPreview({ origin: f.origin, previewRoot: f.root, timeoutMs: 60, pollMs: 10 });
  assert.equal(r.status, 'FAIL_LIVE_DEV_STALE_OR_UNVERIFIED');
  assert.ok(r.attempts.some(x => x.build?.sha === 'abcdef012'));
});

test('current marker with stale horse/carriage entrypoint still fails', async t => {
  const f = await fixture(t, 'mixed');
  const r = await verifyPreview({ origin: f.origin, previewRoot: f.root, timeoutMs: 60, pollMs: 10 });
  assert.equal(r.status, 'FAIL_LIVE_DEV_STALE_OR_UNVERIFIED');
  const completed = r.attempts.find(x => x.build?.sha === revision && x.modules['walk/js/parked-transport.js']);
  assert.ok(completed, 'at least one complete read proves current marker with old carriage code');
  assert.notEqual(completed.modules['walk/js/parked-transport.js'], r.expectedModules['walk/js/parked-transport.js']);
});

test('bounded polling accepts actual subsequent propagation', async t => {
  const f = await fixture(t, 'eventual');
  const r = await verifyPreview({ origin: f.origin, previewRoot: f.root, timeoutMs: 1000, pollMs: 1 });
  assert.equal(r.status, 'PASS_LIVE_DEV_MATCHES_UPLOADED_PREVIEW');
  assert.equal(r.attempts.length, 2);
});

test('server errors are unverified failure, not successful deployment proof', async t => {
  const f = await fixture(t, 'http-error');
  const r = await verifyPreview({ origin: f.origin, previewRoot: f.root, timeoutMs: 60, pollMs: 10 });
  assert.equal(r.status, 'FAIL_LIVE_DEV_STALE_OR_UNVERIFIED');
  assert.ok(r.attempts.every(x => x.errors.length === 5));
});

test('missing generated artifact and overlong polling are refused', async () => {
  await assert.rejects(verifyPreview({ origin: 'http://127.0.0.1', previewRoot: '/does-not-exist' }), /ENOENT/);
  await assert.rejects(verifyPreview({ origin: 'http://127.0.0.1', previewRoot: '/does-not-exist', timeoutMs: 120001 }), /120 seconds/);
});
