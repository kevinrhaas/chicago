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
      register() { return this; }
    }`)
  // ktx2.js imports three and the KTX2 loader, which need a browser; the GLTF stub
  // above has no textures to hand it, so registering is the identity here (T-2582).
  .replace("import { registerKTX2 } from './ktx2.js';", 'const registerKTX2 = (l) => l;')
  .replace("'./structure-versions.js'", JSON.stringify(pathToFileURL(
    path.join(ROOT, 'renderers/web/js/structure-versions.js')).href))
  .replace("'./shared-images.js'", JSON.stringify(pathToFileURL(
    path.join(ROOT, 'renderers/web/js/shared-images.js')).href));
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
const promotedRecord = { id: 'glessner_house', version: null, sidecar: {
  asset: 'gltf/glessner_house__as_built_1887.glb',
  asset_lods: { light: 'gltf/glessner_house__as_built_1887.light.glb' },
} };
check('the promoted default uses its own light asset in both lower tiers',
  ['light', 'balanced'].every(tier => loader.detailAssetPath(promotedRecord, tier)
    === promotedRecord.sidecar.asset_lods.light)
  && loader.detailAssetPath(promotedRecord, 'full') === promotedRecord.sidecar.asset);
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

  // T-3173: a no-bank application switch re-fetches through the existing HTTP
  // path. Use the real pinned GLTF geometry/material/sampler parser here; only
  // KTX2 image transcoding is a deterministic fixture (no GPU/browser claim).
  const threeURL = pathToFileURL(path.join(ROOT, 'renderers/web/vendor/three-0.185.1/three.core.js')).href;
  const realThree = await import(threeURL);
  const asModule = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
  const vendorPath = path.join(ROOT, 'renderers/web/vendor/three-0.185.1/addons');
  const bufferUtils = asModule(fs.readFileSync(path.join(vendorPath, 'utils/BufferGeometryUtils.js'), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
  const skeletonUtils = asModule(fs.readFileSync(path.join(vendorPath, 'utils/SkeletonUtils.js'), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
  const realGLTFURL = asModule(fs.readFileSync(path.join(vendorPath, 'loaders/GLTFLoader.js'), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${bufferUtils}'`)
    .replace("from '../utils/SkeletonUtils.js'", `from '${skeletonUtils}'`));
  const hadSelf = Object.hasOwn(globalThis, 'self'), oldSelf = globalThis.self;
  const hadFixture = Object.hasOwn(globalThis, '__T3173NoBankKtx2Fixture');
  const oldFixture = globalThis.__T3173NoBankKtx2Fixture;
  globalThis.self = globalThis;
  globalThis.__T3173NoBankKtx2Fixture = { load(url, onLoad, onProgress, onError) {
    // Read the real embedded/recovery Blob; byte255 is the explicit decoder-failure control.
    savedFetch(url).then(response => response.arrayBuffer()).then(buffer => {
      if (new Uint8Array(buffer)[0] === 255) throw new Error('controlled encoded KTX2 failure');
      const mipmaps = Array.from({ length: 9 }, (_, i) => ({ width: 256 >> i, height: 256 >> i,
        data: new Uint8Array(Math.max(16, (256 >> i) ** 2)).fill(i + 1) }));
      onLoad(new realThree.CompressedTexture(mipmaps, 256, 256, realThree.RGBA_BPTC_Format));
    }).catch(onError);
  } };
  try {
    const actualLoaderSource = fs.readFileSync(loaderPath, 'utf8')
      .replace("import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';", `import { GLTFLoader } from '${realGLTFURL}';`)
      .replace("import { registerKTX2 } from './ktx2.js';", 'const registerKTX2 = l => { l.setKTX2Loader(globalThis.__T3173NoBankKtx2Fixture); return l; };')
      .replace("'./structure-versions.js'", JSON.stringify(pathToFileURL(path.join(ROOT, 'renderers/web/js/structure-versions.js')).href))
      .replace("'./shared-images.js'", JSON.stringify(pathToFileURL(path.join(ROOT, 'renderers/web/js/shared-images.js')).href));
    const actualLoader = await import(asModule(actualLoaderSource));
    const makeGLB = scale => {
      const bin = Buffer.alloc(84);
      new Float32Array(bin.buffer, bin.byteOffset, 9).set([0, 0, 0, scale, 0, 0, 0, scale, 0]);
      new Float32Array(bin.buffer, bin.byteOffset + 36, 6).set([0, 0, 1, 0, 0, 1]);
      new Uint16Array(bin.buffer, bin.byteOffset + 60, 3).set([0, 1, 2]);
      const spec = { asset: { version: '2.0' }, buffers: [{ byteLength: 84 }],
        bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 36 }, { buffer: 0, byteOffset: 36, byteLength: 24 },
          { buffer: 0, byteOffset: 60, byteLength: 6 }, { buffer: 0, byteOffset: 68, byteLength: 16 }],
        accessors: [{ bufferView: 0, componentType: 5126, count: 3, type: 'VEC3', min: [0, 0, 0], max: [scale, scale, 0] },
          { bufferView: 1, componentType: 5126, count: 3, type: 'VEC2' }, { bufferView: 2, componentType: 5123, count: 3, type: 'SCALAR' }],
        images: [{ bufferView: 3, mimeType: 'image/ktx2' }], samplers: [{ wrapS: 10497, wrapT: 33071, magFilter: 9729, minFilter: 9987 }],
        textures: [{ sampler: 0, extensions: { KHR_texture_basisu: { source: 0 } } }],
        materials: [{ pbrMetallicRoughness: { baseColorTexture: { index: 0 }, roughnessFactor: .63, metallicFactor: .2 } }],
        meshes: [{ primitives: [{ attributes: { POSITION: 0, TEXCOORD_0: 1 }, indices: 2, material: 0 }] }],
        nodes: [{ name: 'NoBankFixture', mesh: 0 }], scenes: [{ nodes: [0] }], scene: 0,
        extensionsUsed: ['KHR_texture_basisu'], extensionsRequired: ['KHR_texture_basisu'] };
      const text = JSON.stringify(spec), json = Buffer.from(text + ' '.repeat((4 - text.length % 4) % 4));
      const bytes = Buffer.alloc(28 + json.length + bin.length);
      bytes.writeUInt32LE(0x46546c67, 0); bytes.writeUInt32LE(2, 4); bytes.writeUInt32LE(bytes.length, 8);
      bytes.writeUInt32LE(json.length, 12); bytes.writeUInt32LE(0x4e4f534a, 16); json.copy(bytes, 20);
      bytes.writeUInt32LE(bin.length, 20 + json.length); bytes.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(bytes, 28 + json.length);
      return bytes;
    };
    const fullBytes = makeGLB(1), lowerBytes = makeGLB(.5), noBankRequests = [], noBankHttpPolicies = [];
    let damageNext = false;
    globalThis.fetch = async (url, options = {}) => {
      const key = new URL(url).href.slice(root.href.length); noBankRequests.push(key);
      if (!key.endsWith('.glb')) return { ok: !!documents[key], status: 404, json: async () => documents[key] };
      noBankHttpPolicies.push(options.cache);
      const bytes = damageNext ? Buffer.from('damaged no-bank GLB') : key.endsWith('.light.glb') ? lowerBytes : fullBytes;
      damageNext = false;
      return { ok: true, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) };
    };
    const noBankScene = await actualLoader.loadScene('1904', { dataBase: root, assetBase: root }, {
      version: { id: 'glessner_house', label: 'v4' }, detail: 'full', keepAssetBytes: false, keepEncodedImages: 'compressed',
    });
    const noBankRecord = noBankScene.registry.get('glessner_house');
    const lower = await noBankScene.loadDetailAsset(noBankRecord, 'balanced');
    const returned = await noBankScene.loadDetailAsset(noBankRecord, 'full');
    const snapshot = gltf => {
      const mesh = gltf.scene.children[0], material = mesh.material, map = material.map;
      return { position: Array.from(mesh.geometry.attributes.position.array), uv: Array.from(mesh.geometry.attributes.uv.array),
        index: Array.from(mesh.geometry.index.array), roughness: material.roughness, metalness: material.metalness,
        wrapS: map.wrapS, wrapT: map.wrapT, minFilter: map.minFilter, magFilter: map.magFilter,
        colorSpace: map.colorSpace, flipY: map.flipY, format: map.format,
        image: [map.image.width, map.image.height], mips: map.mipmaps.map(m => [m.width, m.height, Buffer.from(m.data).toString('hex')]) };
    };
    const initialSnapshot = snapshot(noBankRecord.gltf), returnSnapshot = snapshot(returned.gltf);
    check('no-bank Full to Balanced to Full re-fetches every raw GLB without retaining a bank',
      noBankScene.bankedAssets === 0 && noBankRequests.filter(p => p.endsWith('.glb')).join(',')
      === [sidecar.asset, sidecar.asset_lods.light, sidecar.asset].join(',')
      && noBankScene.bytes === fullBytes.length * 2 + lowerBytes.length);
    check('no-bank real GLTF parser preserves exact Full geometry, UVs, indices, material and sampler on return',
      JSON.stringify(initialSnapshot) === JSON.stringify(returnSnapshot)
      && snapshot(lower.gltf).position[3] === .5 && initialSnapshot.position[3] === 1
      && initialSnapshot.wrapS === realThree.RepeatWrapping && initialSnapshot.wrapT === realThree.ClampToEdgeWrapping);
    check('no-bank reparsing owns fresh geometry/material objects while retaining stable structure and sidecar identity',
      noBankRecord.id === 'glessner_house' && noBankRecord.version.label === 'v4'
      && noBankRecord.sidecar.asset === sidecar.asset && noBankRecord.assetDetail === 'full'
      && noBankRecord.gltf !== returned.gltf && noBankRecord.gltf.scene.children[0].geometry !== returned.gltf.scene.children[0].geometry
      && noBankRecord.gltf.scene.children[0].material !== returned.gltf.scene.children[0].material
      && noBankRecord.gltf.parser === null && returned.gltf.parser === null && noBankScene.problems.length === 0);
    damageNext = true; let noBankFailure = null;
    try { await noBankScene.loadDetailAsset(noBankRecord, 'full'); } catch (error) { noBankFailure = error; }
    const repairedNoBank = await noBankScene.loadDetailAsset(noBankRecord, 'full');
    check('no-bank corrupt replacement reports its error and the next normal refetch restores exact Full without a bank',
      !!noBankFailure && noBankScene.bankedAssets === 0 && noBankRequests.filter(p => p.endsWith('.glb')).length === 5
      && JSON.stringify(snapshot(repairedNoBank.gltf)) === JSON.stringify(initialSnapshot)
      && noBankRecord.gltf === noBankScene.registry.get('glessner_house').gltf);
    check('no-bank refetch preserves the loader normal HTTP revalidation policy', noBankHttpPolicies.length === 5
      && noBankHttpPolicies.every(policy => policy === 'no-cache'));
    check('the public default bank still holds its two streams independently of the application no-bank choice', scene.bankedAssets === 2);
    // T-3173: actual released source payloads, not a userData marker, select the
    // established candidate reread/retire/discard path before the next manager.
    const sharedURL = pathToFileURL(path.join(ROOT, 'renderers/web/js/shared-images.js')).href;
    const residencySource = fs.readFileSync(path.join(ROOT, 'renderers/web/js/texture-residency.js'), 'utf8')
      .replace("from 'three'", `from '${threeURL}'`)
      .replace("from './shared-images.js'", `from '${sharedURL}'`)
      .replace("import { noteReleasedLevels } from './upload-release.js';", 'const noteReleasedLevels = () => {};');
    const { createTextureResidency, hasReleasedTextureLevels, hasRequiredSourceTextures } = await import(asModule(residencySource));
    const groupWith = texture => ({ scene: new realThree.Group().add(new realThree.Mesh(
      new realThree.BoxGeometry(1, 1, 1), new realThree.MeshBasicMaterial({ map: texture }))) });
    const compressed = () => new realThree.CompressedTexture([
      { width: 128, height: 128, data: new Uint8Array(16384) },
      { width: 64, height: 64, data: new Uint8Array(4096) }], 128, 128, realThree.RGBA_BPTC_Format);
    const markerless = compressed(), markerlessClone = markerless.clone(); markerless.mipmaps[0].data = new Uint8Array(0);
    check('released source detector reads empty raw and cloned compressed payloads without userData markers',
      !markerless.userData.releasedBytes && !markerlessClone.userData.releasedBytes
      && hasReleasedTextureLevels(groupWith(markerless)) && hasReleasedTextureLevels(groupWith(markerlessClone)));
    check('released source detector rejects regular, no-mip, live compressed and absent source cases',
      !hasReleasedTextureLevels(groupWith(new realThree.Texture({ width: 1, height: 1 })))
      && !hasReleasedTextureLevels(groupWith(new realThree.CompressedTexture([], 1, 1)))
      && !hasReleasedTextureLevels(groupWith(compressed())) && !hasReleasedTextureLevels(null));
    check('required source texture presence accepts compressed-to-RGBA fallback without relying on runtime IDs',
      hasRequiredSourceTextures(groupWith(compressed()), groupWith(new realThree.DataTexture(new Uint8Array(4), 1, 1))));
    const twoSlots = groupWith(compressed()); twoSlots.scene.add(twoSlots.scene.children[0].clone());
    check('required source texture presence rejects a missing map and a dropped duplicate slot',
      !hasRequiredSourceTextures(groupWith(compressed()), groupWith(null))
      && !hasRequiredSourceTextures(twoSlots, groupWith(compressed())));
    const movedBefore = groupWith(compressed()), movedAfter = groupWith(null);
    movedBefore.scene.add(groupWith(null).scene.children[0]); movedAfter.scene.add(groupWith(compressed()).scene.children[0]);
    for (const asset of [movedBefore, movedAfter]) for (const node of asset.scene.children) node.material.name = 'same';
    check('a same-name texture on another node cannot compensate for a missing required slot',
      !hasRequiredSourceTextures(movedBefore, movedAfter));
    const arrayBefore = groupWith(null), arrayAfter = groupWith(null);
    arrayBefore.scene.children[0].material = [new realThree.MeshBasicMaterial({ map: compressed() }), new realThree.MeshBasicMaterial()];
    arrayAfter.scene.children[0].material = [new realThree.MeshBasicMaterial(), new realThree.MeshBasicMaterial({ map: compressed() })];
    check('another material-array position cannot compensate for a missing required slot',
      !hasRequiredSourceTextures(arrayBefore, arrayAfter));
    const mainSource = fs.readFileSync(path.join(ROOT, 'renderers/web/js/main.js'), 'utf8');
    const rereadStart = mainSource.indexOf('  const rereadReleased = async (next, skipId) => {');
    const rereadEnd = mainSource.indexOf('  const inspectionSwitch =', rereadStart);
    const discardStart = mainSource.indexOf('  const discardDetail = (next) => {');
    const discardEnd = mainSource.indexOf('  /**', discardStart);
    if ([rereadStart, rereadEnd, discardStart, discardEnd].some(n => n < 0)) throw new Error('Actual main reread/discard definitions absent');
    const reread = new Function('loaded', 'hasReleasedTextureLevels', 'hasRequiredSourceTextures', `${mainSource.slice(rereadStart, rereadEnd)}; return rereadReleased;`)(
      noBankScene, hasReleasedTextureLevels, hasRequiredSourceTextures);
    const discard = new Function('disposeLoadedAsset', `${mainSource.slice(discardStart, discardEnd)}; return discardDetail;`)(actualLoader.disposeLoadedAsset);
    const neighbor = { ...noBankRecord, id: 'neighbor_house', sidecar: { ...noBankRecord.sidecar, asset: 'gltf/neighbor_house.glb' } };
    Object.assign(neighbor, await noBankScene.loadDetailAsset(neighbor, 'full'));
    const props = new WeakMap(), get = key => { if (!props.has(key)) props.set(key, {}); return props.get(key); };
    const renderer = { properties: { get }, initTexture(texture) { Object.assign(get(texture), { __webglTexture: {}, __version: texture.version }); } };
    const oldNeighborGLTF = neighbor.gltf, oldMap = oldNeighborGLTF.scene.children[0].material.map;
    const firstManager = createTextureResidency({ group: oldNeighborGLTF.scene, renderer, closeImages: false, releaseCompressedLevels: true });
    renderer.initTexture(oldMap); firstManager.prime(new realThree.Vector3());
    const firstTailBytes = firstManager.state.standInBytes;
    check('handoff fixture performs a real first production residency payload release and cache retirement',
      firstManager.state.released === 1 && firstTailBytes > 0 && oldMap.mipmaps.every(m => m.data.byteLength === 0)
      && hasReleasedTextureLevels(oldNeighborGLTF));
    firstManager.dispose();
    const brokenManager = createTextureResidency({ group: oldNeighborGLTF.scene, renderer, closeImages: false, releaseCompressedLevels: true });
    brokenManager.prime(new realThree.Vector3(1000, 0, 0));
    check('negative control reproduces zero-byte second-manager tail when the required reread is omitted',
      brokenManager.state.standInBytes === 0 && oldNeighborGLTF.scene.children[0].material.map.mipmaps.every(m => m.data.byteLength === 0));
    brokenManager.dispose();
    const phoneRow = { id: 'phone_released_house', sidecar: { asset: 'gltf/phone_released_house.glb' },
      assetDetail: 'full', sourceReleased: true, gltf: groupWith(new realThree.Texture({ width: 1, height: 1 })) };
    const regularRow = { id: 'regular_live_house', sidecar: { asset: 'gltf/regular_live_house.glb' },
      assetDetail: 'full', sourceReleased: false, gltf: groupWith(new realThree.Texture({ width: 1, height: 1 })) };
    const freshSkip = { ...noBankRecord, sourceReleased: true };
    const next = { registry: new Map([[neighbor.id, { ...neighbor }], [phoneRow.id, { ...phoneRow }],
      [regularRow.id, { ...regularRow }], [freshSkip.id, { ...freshSkip }]]) };
    const beforeReread = noBankRequests.length;
    await reread(next, freshSkip.id);
    const replacement = next.registry.get(neighbor.id);
    check('actual main reread extends old phone geometry selection, skips fresh Glessner and keeps regular live rows',
      noBankRequests.slice(beforeReread).filter(p => p.endsWith('.glb')).sort().join(',')
      === ['gltf/neighbor_house.glb', 'gltf/phone_released_house.glb'].sort().join(',')
      && next.registry.get(freshSkip.id).gltf === freshSkip.gltf && next.registry.get(regularRow.id).gltf === regularRow.gltf);
    check('actual main reread keeps new candidates and old retired owners separate before commit',
      next.reread.length === 2 && next.retired.length === 2 && next.retired.includes(oldNeighborGLTF)
      && replacement.gltf !== oldNeighborGLTF && neighbor.gltf === oldNeighborGLTF
      && !replacement.sourceReleased && !hasReleasedTextureLevels(replacement.gltf));
    const newMap = replacement.gltf.scene.children[0].material.map;
    const secondManager = createTextureResidency({ group: replacement.gltf.scene, renderer, closeImages: false, releaseCompressedLevels: true });
    renderer.initTexture(newMap); secondManager.prime(new realThree.Vector3());
    secondManager.tick(new realThree.Vector3(1000, 0, 0));
    const actualTail = replacement.gltf.scene.children[0].material.map;
    check('required real refetch/reparse makes second-manager far tail populated at every mip',
      secondManager.state.standInBytes === firstTailBytes && actualTail.mipmaps.length > 0
      && actualTail.mipmaps.every(m => m.data.byteLength > 0));
    secondManager.tick(new realThree.Vector3()); await new Promise(resolve => setTimeout(resolve, 0)); secondManager.tick(new realThree.Vector3());
    check('reread second manager returns through the existing encoded refill path without errors or a raw bank',
      replacement.gltf.scene.children[0].material.map === newMap && secondManager.state.retranscodes === 1
      && secondManager.state.pending === 0 && secondManager.state.problems.length === 0 && noBankScene.bankedAssets === 0);
    secondManager.dispose();
    for (const failureMode of ['encoded', 'corrupt-glb', 'http']) {
      const oldVisible = neighbor.gltf, failureEvents = [], failureCandidate = { registry: new Map([
        ['neighbor_house', { ...neighbor }],
        ['broken_house', { ...neighbor, id: 'broken_house', sidecar: { ...neighbor.sidecar, asset: 'gltf/broken_house.glb' } }],
      ]) };
      let oldDisposals = 0, candidateDisposals = 0, commits = 0, visible = oldVisible, badRequests = 0;
      oldVisible.scene.children[0].geometry.addEventListener('dispose', () => oldDisposals++);
      const previousFetch = globalThis.fetch;
      globalThis.fetch = async (url, options) => {
        if (!new URL(url).pathname.endsWith('/broken_house.glb')) return previousFetch(url, options);
        badRequests++;
        if (failureMode === 'http') return { ok: false, status: 404, statusText: 'controlled absent asset' };
        const badImage = failureMode === 'encoded' ? Buffer.from(fullBytes) : Buffer.from('corrupt candidate GLB');
        if (failureMode === 'encoded') badImage[badImage.length - 16] = 255;
        return { ok: true, arrayBuffer: async () => badImage.buffer.slice(badImage.byteOffset, badImage.byteOffset + badImage.byteLength) };
      };
      const failureSwitch = actualLoader.createLatestDetailSwitch({ initial: 'full',
        prepare: async () => {
          try { await reread(failureCandidate, 'glessner_house'); }
          catch (error) {
            for (const gltf of failureCandidate.reread) gltf.scene.children[0].geometry.addEventListener('dispose', () => candidateDisposals++);
            discard(failureCandidate); throw error;
          }
          return failureCandidate;
        }, commit: candidate => { commits++; visible = candidate; }, discard,
        onError: (error, wanted, kept) => failureEvents.push({ message: error.message, wanted, kept }) });
      try { await failureSwitch.set('balanced'); } finally { globalThis.fetch = previousFetch; }
      check(`failed actual ${failureMode} candidate preserves the visible world and discards successful partial rereads`,
        failureSwitch.current === 'full' && visible === oldVisible && commits === 0 && oldDisposals === 0
        && failureEvents.length === 1 && failureEvents[0].wanted === 'balanced' && failureEvents[0].kept === 'full'
        && (failureMode !== 'encoded' || /missing a required texture/.test(failureEvents[0].message))
        && (failureMode !== 'http' || badRequests === 2)
        && failureCandidate.reread.length === (failureMode === 'encoded' ? 2 : 1)
        && candidateDisposals === failureCandidate.reread.length && failureCandidate.retired.length === 0
        && failureCandidate.registry.get('neighbor_house').gltf === oldVisible,
        JSON.stringify({ current: failureSwitch.current, visibleOld: visible === oldVisible, commits, oldDisposals, failureEvents,
          reads: failureCandidate.reread.length, candidateDisposals, retired: failureCandidate.retired.length, badRequests }));
    }

  } finally {
    if (hadSelf) globalThis.self = oldSelf; else delete globalThis.self;
    if (hadFixture) globalThis.__T3173NoBankKtx2Fixture = oldFixture; else delete globalThis.__T3173NoBankKtx2Fixture;
  }

} finally { globalThis.fetch = savedFetch; }

console.log(`   self-test | ${failures.length} failure(s)`);
process.exit(failures.length ? 1 : 0);
