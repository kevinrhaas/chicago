// T-3311: a scene with no parked vehicles still boots. createParkedTransport()
// returns early for 1812 and 1880 (and when placements.json cannot be fetched),
// yet main.js boots it deferred (`loadWithin`), so its update() still calls
// load() on every frame. Until T-3311 that load() read `rows` from a `const`
// declared after the early return — a temporal-dead-zone ReferenceError that
// failed the 1812 boot ("Jump stalled") and timed out memory (1812, desktop).
// Usage: node tools/test_parked_transport_empty_scene.mjs --self-test
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
if (process.argv.slice(2).some((v) => v !== '--self-test')) throw Error('Only --self-test is supported');
const root = fileURLToPath(new URL('../', import.meta.url));
const vendor = pathToFileURL(`${root}renderers/web/vendor/three-0.185.1/`).href;
// The page's import map, as a resolve hook: 'three' and 'three/addons/…' to the vendored copy.
register(`data:text/javascript,${encodeURIComponent(`
export async function resolve(spec, ctx, next) {
  if (spec === 'three') return { url: ${JSON.stringify(`${vendor}three.module.js`)}, shortCircuit: true };
  if (spec.startsWith('three/addons/')) return { url: ${JSON.stringify(vendor)} + 'addons/' + spec.slice(13), shortCircuit: true };
  return next(spec, ctx);
}`)}`);
const THREE = await import('three');
const { createParkedTransport } = await import(pathToFileURL(`${root}renderers/web/js/parked-transport.js`).href);

const camera = new THREE.PerspectiveCamera();
const terrain = { surfaceHeight: () => 0 };
let checks = 0;
const cases = [
  ['1812, a scene with no parked vehicles', { sceneId: '1812' }],
  ['1880, a scene with no parked vehicles', { sceneId: '1880' }],
  ['1835 when placements.json fails', { sceneId: '1835', fetchFails: true }],
];
const realFetch = globalThis.fetch;
for (const [label, { sceneId, fetchFails }] of cases) {
  globalThis.fetch = async () => { if (fetchFails) return { ok: false, status: 404 }; throw Error(`fetched for ${sceneId}`); };
  const problems = [];
  const out = await createParkedTransport({ dataBase: 'http://127.0.0.1/data/', sceneId, terrain,
    detail: 'full', problems, loadWithin: 60 });
  for (let frame = 0; frame < 3; frame += 1) assert.doesNotThrow(() => out.update(camera), label);
  await out.setTier('balanced');
  assert.equal(out.instances.length, 0, `${label}: nothing placed`);
  assert.equal(out.pending, 0, `${label}: nothing pending, so a scripted view does not wait`);
  assert.equal(out.records.length, 0, `${label}: no records`);
  if (fetchFails) assert.match(problems.join('\n'), /parked transport: Placements HTTP 404/, `${label}: the failure is reported`);
  out.dispose();
  checks += 4 + (fetchFails ? 1 : 0);
}
globalThis.fetch = realFetch;
console.log(`parked transport empty scenes: ${checks} checks pass — 1812, 1880 and a failed placements fetch update, retier and dispose without a TDZ error (T-3311)`);
