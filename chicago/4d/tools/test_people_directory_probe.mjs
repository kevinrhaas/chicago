// SPDX-License-Identifier: GPL-3.0-or-later
// Execute the actual main.js directory closure with controlled response timing.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const main = fs.readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
const begin = main.indexOf('const peopleDirectory = (() => {');
const end = main.indexOf('\n  })();', begin);
assert(begin >= 0 && end > begin, 'Actual people-directory closure is present');
const source = main.slice(begin, end + '\n  })();'.length);
const tick = () => new Promise(resolve => setImmediate(resolve));
function directory(code, fetch, people = null) {
  return new Function('fetch', 'people', 'loaded', 'YEAR', 'bases', code + '\nreturn peopleDirectory;')(
    fetch, people, { scene: { id: '1904' } }, '1904', { dataBase: 'https://example.invalid/data/' });
}
async function delayedBody(code) {
  let finish, bodies = 0, requests = 0;
  const body = new Promise(resolve => { finish = resolve; });
  const probe = directory(code, async (url, options) => {
    requests++; assert.equal(String(url), 'https://example.invalid/data/sidecars/1904/people.json');
    assert.deepEqual(options, { method: 'HEAD', cache: 'no-cache' });
    return { ok: true, arrayBuffer() { bodies++; return body; } };
  });
  probe.ask(); probe.ask(); await tick();
  assert.equal(requests, 1, 'One native HEAD probe');
  assert.equal(bodies, 1, 'The actual zero-byte body is consumed');
  assert.equal(probe.known, false, 'Do not publish success before body completion');
  finish(new ArrayBuffer(0)); await tick();
  assert.equal(probe.known, true, 'Completed successful response enables People');
}
await delayedBody(source);
const unhandled = [], onUnhandled = error => unhandled.push(String(error));
process.on('unhandledRejection', onUnhandled);
try {
  let bodyCalls = 0;
  const failedBody = directory(source, async () => ({ ok: true, arrayBuffer() { bodyCalls++; return Promise.reject(Error('Controlled body failure')); } }));
  failedBody.ask(); await tick(); await tick();
  assert.equal(bodyCalls, 1); assert.equal(failedBody.known, false, 'Failed body keeps directory unavailable');
  const failedNetwork = directory(source, async () => { throw Error('Controlled network failure'); });
  failedNetwork.ask(); await tick(); assert.equal(failedNetwork.known, false);
  let notFoundBody = 0;
  const absent = directory(source, async () => ({ ok: false, async arrayBuffer() { notFoundBody++; return new ArrayBuffer(0); } }));
  absent.ask(); await tick(); assert.equal(notFoundBody, 1); assert.equal(absent.known, false);
  let existingRequests = 0;
  const existing = directory(source, () => { existingRequests++; throw Error('Existing data should not probe'); }, { persons: [] });
  existing.ask(); await tick(); assert.equal(existing.known, true); assert.equal(existingRequests, 0);
  let gets = 0;
  const payload = { persons: ['controlled'] };
  const loading = directory(source, async (url, options) => {
    gets++; assert.deepEqual(options, { cache: 'no-cache' }); return { ok: true, async json() { return payload; } };
  });
  const first = loading.load(), second = loading.load(); assert.equal(first, second, 'Existing GET cache remains shared');
  assert.equal(await first, payload); assert.equal(gets, 1);
  assert.deepEqual(unhandled, [], 'No rejected HEAD promise escapes the native catch');
} finally { process.off('unhandledRejection', onUnhandled); }
const controls = [];
for (const [name, change] of [
  ['Discarded HEAD body', text => text.replace('await r.arrayBuffer(); known = r.ok;', 'known = r.ok;')],
  ['Unawaited HEAD body', text => text.replace('await r.arrayBuffer(); known = r.ok;', 'r.arrayBuffer(); known = r.ok;')],
]) {
  const broken = change(source); assert.notEqual(broken, source, 'Control changes actual source');
  let rejected;
  try { await delayedBody(broken); } catch (error) { rejected = error.message; }
  assert(rejected, name + ' must be rejected'); controls.push({ name, rejected });
}
console.log(JSON.stringify({ pass: true, scope: 'Actual directory HEAD timing/body/error handling and unchanged GET cache; no browser claim', controls }, null, 2));
