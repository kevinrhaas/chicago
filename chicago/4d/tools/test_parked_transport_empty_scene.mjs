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

// Actual town scene lifecycle: Light never imports/constructs assembly tools.
// Eligible loading crosses the real dynamic import boundary; sentinel factories
// stop before GLB/network work. This is startup/lifetime proof, not world contact.
{
  const { readFileSync } = await import('node:fs');
  globalThis.__townLazyTools = { imports: 0, loader: 0, hitch: 0, factory: 0 };
  const dynamicModules = {
    './driven-assembly-loader.js': `globalThis.__townLazyTools.imports++; export function createDrivenAssemblyLoader(){globalThis.__townLazyTools.factory++;throw Error('ELIGIBLE_LAZY_ASSEMBLY_SENTINEL');}`,
    './draft-hitch.js': `globalThis.__townLazyTools.imports++; export function createDraftHitchFactory(){globalThis.__townLazyTools.hitch++;return()=>{throw Error('Unexpected hitch assets');};}`,
    'three/addons/loaders/GLTFLoader.js': `export class GLTFLoader{constructor(){globalThis.__townLazyTools.loader++;}}`,
  };
  register(`data:text/javascript,${encodeURIComponent(`
    const modules=${JSON.stringify(dynamicModules)};
    export async function resolve(s,c,n){if(c.parentURL?.endsWith('/town-transport-scene.js')&&modules[s])return{url:'data:text/javascript,'+encodeURIComponent(modules[s]),shortCircuit:true};return n(s,c);}
  `)}`);
  const { mountTownTransport } = await import(new URL('../renderers/web/js/town-transport-scene.js', import.meta.url));
  const configRoot = new URL('../data/', import.meta.url);
  const previousFetch = globalThis.fetch; let directoryReads = 0, heightReads = 0, assetReads = 0;
  globalThis.fetch = async url => {
    const bytes = readFileSync(new URL(String(url)));
    return { ok: true, status: 200, json: async () => JSON.parse(bytes),
      arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) };
  };
  try {
    const directory = JSON.parse(readFileSync(new URL('sidecars/1904/people.json', configRoot)));
    const localProblems = [];
    const town = await mountTownTransport({ sceneId: '1904', dataBase: configRoot,
      getPeople: async () => { directoryReads++; return directory; },
      humans: { get assets() { assetReads++; return {}; }, withhold() { throw Error('Unexpected adoption'); } },
      heightAt: () => { heightReads++; return 0; }, footprints: () => [], visitor: () => null,
      interactions: { add() { throw Error('Unexpected Light interaction'); } }, detail: 'light', problems: localProblems });
    await town.ready(); town.ensureNear(new THREE.Vector3(1335, 5, 3340), true);
    assert.equal(town.driverAnchorForPerson('pa1904_otis_f_r_c1900_hans_johnson'), null, 'Light does not invent a mounted driver anchor');
    assert.deepEqual(globalThis.__townLazyTools, { imports: 0, loader: 0, hitch: 0, factory: 0 });
    assert.equal(directoryReads, 0); assert.equal(assetReads, 0); assert.equal(heightReads, 0);
    await town.setTier('balanced'); await town.ready();
    assert.deepEqual(globalThis.__townLazyTools, { imports: 2, loader: 1, hitch: 1, factory: 1 });
    assert.equal(directoryReads, 1); assert(localProblems.some(s => s.includes('ELIGIBLE_LAZY_ASSEMBLY_SENTINEL')));
    town.dispose();
  } finally { globalThis.fetch = previousFetch; delete globalThis.__townLazyTools; }
  console.log('actual Light town scene: zero assembly imports/factories/directory/height queries; eligible route opens deferred tools only then PASS');
}

// Execute main's actual town boot block with only the dynamic import boundary
// replaced. Unsupported scenes must not import/compile town modules or fetch config.
{
  const { readFileSync } = await import('node:fs');
  const { supportsTownTransport } = await import('../renderers/web/js/transport-scenes.js');
  const legacy = await import('../renderers/web/js/transport-loop.js');
  assert.equal(legacy.supportsTownTransport, supportsTownTransport, 'old export is the same tiny guard');
  for (const value of ['1835', '1904', 1835, 1904, new String('1835'), { toString: () => '1904' }])
    assert.equal(supportsTownTransport(value), true);
  for (const value of ['1812', '1880', '1905', null, undefined, false, {}, Symbol('1835')])
    assert.equal(supportsTownTransport(value), false);
  const coercionError = new Error('coercion');
  assert.throws(() => supportsTownTransport({ toString() { throw coercionError; } }), (e) => e === coercionError);
  const main = readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  assert(!/^import\s+.*(?:town-transport-scene|transport-loop)\.js/m.test(main), 'main has no eager town/loop import');
  assert(main.includes("import { supportsTownTransport } from './transport-scenes.js';"));
  const start = main.indexOf('  api.townTransport = null;\n  if (supportsTownTransport(YEAR)) {');
  assert(start >= 0, 'actual scene eligibility block found');
  const end = main.indexOf('\n\n  /** A structure', start);
  assert(end > start);
  const block = main.slice(start, end);
  assert.equal((block.match(/import\('\.\/town-transport-scene\.js'\)/g) ?? []).length, 1);
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const boot = new AsyncFunction('YEAR', 'api', 'bases', 'people', 'peopleDirectory', 'confidence', 'streetGrid',
    'profiledGroundHeight', 'terrain', 'decks', 'footprints', 'walker', 'interactions', 'detailLevel', 'coarse',
    'problems', 'scene3d', 'supportsTownTransport', 'importTown',
    block.replace("import('./town-transport-scene.js')", 'importTown()'));
  const previousFetch = globalThis.fetch;
  let configFetches = 0;
  globalThis.fetch = async () => { configFetches++; throw Error('Unexpected town config fetch'); };
  try {
    for (const year of ['1812', '1880', '1835', '1904']) {
      for (const failure of [null, 'import', 'mount', 'empty']) {
        const api = { humans: {} }, people = {}, directory = {}, confidence = {}, terrain = {}, decks = {},
          footprints = [], walker = { state: {} }, interactions = {}, bases = { dataBase: new URL('http://127.0.0.1/data/') };
        const problems = [], added = [], group = {}, calls = [];
        let imports = 0, directoryCalls = 0;
        const streetGrid = { carriagewayHeight: (e, n) => ['road', e, n] };
        const ground = (t, d, e, n) => { assert.equal(t, terrain); assert.equal(d, decks); return ['ground', e, n]; };
        const mountTownTransport = async (options) => { calls.push(options); if (failure === 'mount') throw Error('mount failure'); return failure === 'empty' ? null : { group }; };
        await boot(year, api, bases, people, { load() { directoryCalls++; return directory; } }, confidence,
          streetGrid, ground, terrain, decks, footprints, walker, interactions, 'balanced', false, problems,
          { add: (g) => added.push(g) }, supportsTownTransport,
          async () => { imports++; if (failure === 'import') throw Error('import failure'); return { mountTownTransport }; });
        const supported = supportsTownTransport(year);
        assert.equal(imports, supported ? 1 : 0);
        assert.equal(configFetches, 0, 'no imported/fetched town configuration on unsupported boot');
        assert.equal(directoryCalls, 0, 'mount receives an uncalled lazy directory callback');
        if (!supported) { assert.equal(api.townTransport, null); assert.deepEqual(calls, []); assert.deepEqual(added, []); assert.deepEqual(problems, []); continue; }
        if (failure === 'import' || failure === 'mount') {
          assert.equal(api.townTransport, null); assert.deepEqual(added, []);
          assert.deepEqual(problems, [`town transport: ${failure} failure`]);
        } else { assert.deepEqual(problems, []); assert.deepEqual(added, failure === 'empty' ? [] : [group]); }
        if (failure === 'import') continue;
        assert.equal(calls.length, 1); const options = calls[0];
        assert.deepEqual(Object.keys(options).sort(), ['sceneId', 'dataBase', 'people', 'getPeople', 'humans', 'confidence',
          'heightAt', 'footprints', 'visitor', 'interactions', 'detail', 'coarse', 'problems'].sort());
        assert.equal(options.sceneId, year); assert.equal(options.dataBase, bases.dataBase); assert.equal(options.people, people);
        assert.equal(options.humans, api.humans); assert.equal(options.confidence, confidence);
        assert.equal(options.interactions, interactions); assert.equal(options.detail, 'balanced'); assert.equal(options.coarse, false);
        assert.equal(options.problems, problems); assert.equal(options.footprints(), footprints); assert.equal(options.visitor(), walker.state);
        assert.equal(options.getPeople(), directory); assert.equal(directoryCalls, 1);
        assert.deepEqual(options.heightAt(2, 3), [year === '1904' ? 'road' : 'ground', 2, 3]);
      }
    }
  } finally { globalThis.fetch = previousFetch; }
  console.log('actual main town boot: unsupported zero imports/config/null; supported exact callbacks, group and errors; guard API retained PASS');
}
