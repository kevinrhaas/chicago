#!/usr/bin/env node
/**
 * The address-bar half of structure versions (T-1727), without a browser.
 *
 *   node tools/test_structure_versions.mjs [--self-test]   (the flag is accepted; every run is one)
 *
 * `renderers/web/js/structure-versions.js` decides what `?structure=<id>&version=<label>`
 * swaps. The ticket's rules for it are all decidable without WebGL, so they are held
 * here, on the committed versions index, in well under a second:
 *
 *   - no request, no fetch: a plain boot never reads the versions index (the boot
 *     payload must not grow);
 *   - a committed label swaps exactly that entry, and the row carries its sidecar path;
 *   - every miss — no ?structure=, an unknown id, an unknown label, a malformed label,
 *     an unreadable index — falls back to the default WITH a notice, never silently;
 *   - version=default is the canonical record, named as such in the HUD chip.
 *
 * The browser half (the swap in a booted scene, nothing else moving, both viewports) is
 * the release smoke's, in tools/smoke_renderer.mjs part 3.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const mod = await import(pathToFileURL(path.join(ROOT, 'renderers/web/js/structure-versions.js')));
const { readVersionRequest, resolveStructureVersion, versionBadge } = mod;

const failures = [];
const check = (name, cond, detail = '') => {
  console.log(`   self-test | ${cond ? 'ok  ' : 'FAIL'} ${name}${cond || !detail ? '' : ` — ${detail}`}`);
  if (!cond) failures.push(name);
};

const dataBase = pathToFileURL(path.join(ROOT, 'data') + '/');
const sceneIndex = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835/index.json'), 'utf8'));
const entries = sceneIndex.structures.map((r) => (typeof r === 'string' ? { id: r } : r));
let fetched = [];
const getJSON = async (url) => {
  fetched.push(String(url));
  return JSON.parse(fs.readFileSync(fileURLToPath(url), 'utf8'));
};
const resolve = async (search, ctx = {}) => {
  fetched = [];
  return resolveStructureVersion(readVersionRequest(search), {
    year: '1835', dataBase, entries, getJSON, ...ctx,
  });
};

// the committed index is what the smoke's fixture lives in
const vindex = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835/versions/index.json'), 'utf8'));
const fixture = vindex.structures?.bates_auction_room?.find((r) => r.label === 'fixture');
check('the committed versions index lists the smoke fixture, marked as a test fixture',
  fixture?.test_fixture === true && /versions\/bates_auction_room\/fixture\.json$/.test(fixture.sidecar),
  JSON.stringify(fixture));

let s = await resolve('?year=1835&anchor=fort');
check('no ?version= asks for nothing and fetches nothing', s.requested === null && s.active === null
  && fetched.length === 0 && versionBadge(s) === null, JSON.stringify({ s, fetched }));
s = await resolve('?structure=bates_auction_room');
check('?structure= alone asks for nothing yet (reserved for opening a structure)',
  s.requested === null && fetched.length === 0);

s = await resolve('?structure=bates_auction_room&version=fixture');
check('a committed label swaps exactly that structure, and names its sidecar',
  s.active?.id === 'bates_auction_room' && s.active?.label === 'fixture'
  && s.active?.sidecar === fixture?.sidecar && s.notice === null, JSON.stringify(s));
check('…fetching only the versions index, once', fetched.length === 1
  && /sidecars\/1835\/versions\/index\.json$/.test(fetched[0]), fetched.join(', '));
let b = versionBadge(s);
check('…and the HUD chip names the version and says it is a test fixture',
  b?.tone === 'active' && b.text === 'version fixture' && /test fixture/.test(b.title)
  && /Auction Room/.test(b.title), JSON.stringify(b));

s = await resolve('?structure=bates_auction_room&version=default');
b = versionBadge(s);
check('version=default shows the canonical record and the chip says so, with no fetch',
  s.active === null && s.explicitDefault && s.notice === null && fetched.length === 0
  && b?.tone === 'default' && b.text === 'version default', JSON.stringify({ s, b }));

const misses = [
  ['?version=fixture', /needs \?structure=/],
  ['?structure=no_such_house&version=v1', /No structure “no_such_house” in the 1835 scene/],
  ['?structure=Bad-Id!&version=v1', /No structure/],
  ['?structure=bates_auction_room&version=zzz', /No version “zzz” of .* — showing the default\. Versions: fixture\./],
  ['?structure=bates_auction_room&version=Hall_Plan', /is not a version label/],
  ['?structure=sauganash_hotel&version=v2', /has no committed versions — showing the default/],
];
for (const [search, re] of misses) {
  s = await resolve(search);
  b = versionBadge(s);
  check(`${search} falls back to the default and SAYS so`, s.active === null && re.test(s.notice ?? '')
    && b?.tone === 'notice' && b.text === 'default shown' && b.title === s.notice,
  JSON.stringify({ notice: s.notice, b }));
}
s = await resolve('?structure=bates_auction_room&version=fixture', {
  getJSON: async () => { throw new Error('404 Not Found'); },
});
check('an unreadable versions index falls back to the default and says why',
  s.active === null && /could not be read \(404 Not Found\)/.test(s.notice ?? ''), s.notice);

// T-1730. Exercise the actual loader/transaction code without WebGL. The one
// substituted dependency is GLTF's binary decoder; fetches, metadata resolution,
// byte-cache lifecycle, detail selection and latest-wins behavior remain real.
const loaderPath = path.join(ROOT, 'renderers/web/js/scene-loader.js');
const loaderSource = fs.readFileSync(loaderPath, 'utf8')
  .replace("import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';", `
    let parseSerial = 0;
    class GLTFLoader {
      parse(buffer, base, resolve, reject) {
        if (new DataView(buffer).getUint32(0, true) !== 0x46546c67) {
          reject(new Error('corrupt GLB fixture')); return;
        }
        resolve({ parseSerial: ++parseSerial, base, scene: {} });
      }
      setMeshoptDecoder() {}
    }`)
  .replace("'./structure-versions.js'", JSON.stringify(pathToFileURL(
    path.join(ROOT, 'renderers/web/js/structure-versions.js')).href));
const loader = await import(`data:text/javascript;base64,${Buffer.from(loaderSource).toString('base64')}`);
const lodRecord = { id: 'glessner_house', version: { label: 'v4' }, sidecar: {
  asset: 'gltf/versions/glessner_house/v4/house.glb',
  asset_lods: { light: 'gltf/versions/glessner_house/v4/house.light.glb' },
} };
check('v4 full keeps its high asset and BOTH lower tiers select its declared derivative',
  loader.detailAssetPath(lodRecord, 'full') === lodRecord.sidecar.asset
  && ['balanced', 'light'].every(level => loader.detailAssetPath(lodRecord, level)
    === lodRecord.sidecar.asset_lods.light));
check('a default, v3, unrelated structure or missing LOD retains its ordinary asset', [
  { ...lodRecord, version: null }, { ...lodRecord, version: { label: 'v3' } },
  { ...lodRecord, id: 'other_house' }, { ...lodRecord, sidecar: { asset: 'gltf/house.glb' } },
].every(record => loader.detailAssetPath(record, 'light') === record.sidecar.asset));
const publishedBases = { assetBase: new URL('https://example.test/data/'), sourceAssetLayout: false };
const sourceBases = { assetBase: new URL('https://example.test/assets/'), sourceAssetLayout: true };
check('LOD uses the published gltf address, the source web address, and respects explicit asset bases',
  loader.detailAssetUrl(lodRecord, 'light', publishedBases).href
    === 'https://example.test/data/gltf/versions/glessner_house/v4/house.light.glb'
  && loader.detailAssetUrl(lodRecord, 'light', sourceBases).href
    === 'https://example.test/assets/web/versions/glessner_house/v4/house.light.glb'
  && loader.detailAssetUrl(lodRecord, 'full', sourceBases).href
    === 'https://example.test/assets/gltf/versions/glessner_house/v4/house.glb'
  && !loader.resolveBases({ href: 'https://example.test/renderers/web/index.html?assets=/custom/',
    search: '?assets=/custom/' }).sourceAssetLayout);

const deferred = () => {
  let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve };
};
let events = [];
let preparation = deferred();
let switching = loader.createLatestDetailSwitch({ initial: 'light',
  prepare: async level => { events.push(`prepare:${level}`); await preparation.promise; return { level }; },
  commit: candidate => events.push(`commit:${candidate.level}`),
  discard: candidate => events.push(`discard:${candidate.level}`),
  onError: () => events.push('error'),
});
let first = switching.set('full');
await Promise.resolve();
let last = switching.set('light');
preparation.resolve();
await Promise.all([first, last]);
check('returning to the displayed tier discards an in-flight replacement without any commit',
  switching.current === 'light' && events.join(',') === 'prepare:full,discard:full', events.join(','));

events = []; preparation = deferred();
switching = loader.createLatestDetailSwitch({ initial: 'full',
  prepare: async level => { events.push(`prepare:${level}`); if (level === 'balanced') await preparation.promise;
    return { level }; },
  commit: candidate => events.push(`commit:${candidate.level}`),
  discard: candidate => events.push(`discard:${candidate.level}`),
  onError: () => events.push('error'),
});
first = switching.set('balanced'); await Promise.resolve(); last = switching.set('light');
preparation.resolve(); await Promise.all([first, last]);
check('the newest pending tier wins; its predecessor is disposed before it becomes visible',
  switching.current === 'light'
  && events.join(',') === 'prepare:balanced,discard:balanced,prepare:light,commit:light', events.join(','));

events = []; let refuse = true;
switching = loader.createLatestDetailSwitch({ initial: 'light',
  prepare: async level => { if (refuse) throw new Error('missing asset'); return { level }; },
  commit: candidate => events.push(`commit:${candidate.level}`), discard: () => events.push('discard'),
  onError: (error, wanted, kept) => events.push(`${wanted}:${kept}:${error.message}`),
});
await switching.set('full');
check('a failed replacement keeps the visible tier and reports requested and retained detail',
  switching.current === 'light' && events.join(',') === 'full:light:missing asset');
refuse = false; await switching.set('full');
check('the same failed request can be retried successfully',
  switching.current === 'full' && events.at(-1) === 'commit:full');

const disposed = { geometry: 0, material: 0, texture: 0, image: 0 };
const tex = { isTexture: true, dispose() { disposed.texture++; }, image: { close() { disposed.image++; } } };
const material = { map: tex, normalMap: tex, dispose() { disposed.material++; } };
const node = { geometry: { dispose() { disposed.geometry++; } }, material };
loader.disposeLoadedAsset({ scene: { traverse(fn) { fn(node); fn(node); } } });
check('retiring an asset disposes its unique source geometry, material, textures and bitmap exactly once',
  Object.values(disposed).every(n => n === 1), JSON.stringify(disposed));

const savedFetch = globalThis.fetch;
try {
  const json = Buffer.from(JSON.stringify({ asset: { version: '2.0' } }));
  const binary = Buffer.alloc(20 + json.length);
  binary.writeUInt32LE(0x46546c67, 0); binary.writeUInt32LE(json.length, 12); json.copy(binary, 20);
  const requests = [];
  let corruptNext = false;
  const root = new URL('https://example.test/data/');
  const sidecar = { ...lodRecord.sidecar, id: lodRecord.id };
  const documents = {
    'scenes/1904.json': { id: '1904' }, 'datum.json': {},
    'sidecars/1904/index.json': { structures: [{ id: lodRecord.id }] },
    'sidecars/1904/versions/index.json': { structures: { glessner_house: [
      { label: 'v4', sidecar: 'sidecars/1904/versions/glessner_house/v4.json' },
    ] } },
    'sidecars/1904/versions/glessner_house/v4.json': sidecar,
  };
  globalThis.fetch = async url => {
    const key = new URL(url).href.slice(root.href.length); requests.push(key);
    const payload = key.endsWith('.glb') && corruptNext ? Buffer.alloc(binary.length) : binary;
    if (key.endsWith('.glb')) corruptNext = false;
    return key.endsWith('.glb')
      ? { ok: true, arrayBuffer: async () => payload.buffer.slice(payload.byteOffset, payload.byteOffset + payload.byteLength) }
      : { ok: !!documents[key], status: 404, json: async () => documents[key] };
  };
  const scene = await loader.loadScene('1904', { dataBase: root, assetBase: root }, {
    version: { id: 'glessner_house', label: 'v4' }, detail: 'light',
  });
  const record = scene.registry.get('glessner_house');
  check('a light boot fetches only the light GLB while retaining canonical sidecar and version identity',
    scene.problems.length === 0 && record.version.label === 'v4'
    && record.sidecar.asset === sidecar.asset && record.assetUrl.endsWith('house.light.glb')
    && requests.filter(x => x.endsWith('.glb')).join(',') === sidecar.asset_lods.light, JSON.stringify(requests));
  const high = await scene.loadDetailAsset(record, 'full');
  const low = await scene.loadDetailAsset(record, 'balanced');
  const highAgain = await scene.loadDetailAsset(record, 'full');
  check('switching caches each fetched byte stream but reparses fresh material owners every time',
    requests.filter(x => x.endsWith('.glb')).length === 2
    && high.gltf !== highAgain.gltf && low.gltf !== record.gltf
    && high.gltf.parseSerial !== highAgain.gltf.parseSerial
    && scene.bytes === 2 * binary.length && record.assetDetail === 'light');
  corruptNext = true;
  const beforeRetry = requests.filter(x => x.endsWith('.glb')).length;
  const damaged = await loader.loadScene('1904', { dataBase: root, assetBase: root }, {
    version: { id: 'glessner_house', label: 'v4' }, detail: 'light',
  });
  const damagedRecord = damaged.registry.get('glessner_house');
  const repaired = await damaged.loadDetailAsset(damagedRecord, 'light');
  check('a 200 response with corrupt GLB bytes is evicted so a later retry fetches repaired data',
    damagedRecord.gltf === null && /corrupt GLB fixture/.test(damagedRecord.loadFailed)
    && !!repaired.gltf && repaired.assetUrl.endsWith('house.light.glb')
    && requests.filter(x => x.endsWith('.glb')).length === beforeRetry + 2);
} finally { globalThis.fetch = savedFetch; }

console.log(`   self-test | ${failures.length} failure(s)`);
process.exit(failures.length ? 1 : 0);
