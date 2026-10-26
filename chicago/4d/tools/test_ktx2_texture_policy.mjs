import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
if (process.argv.slice(2).some(x => x !== '--self-test')) throw new Error('Only --self-test is supported');
const js = new URL('../renderers/web/js/ktx2.js', import.meta.url);
const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url);
const threeURL = new URL('three.core.js', vendor).href;
const THREE = await import(threeURL);
const dataModule = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64');
// Native constructor/mip layout, including the actual Basis RGBA32 fallback.
// Only decode delivery and support detection are doubles; no GPU/decode claim.
const colorURL = new URL('addons/math/ColorSpaces.js', vendor);
const colors = dataModule((await fs.readFile(colorURL, 'utf8')).replace("from 'three'", `from '${threeURL}'`));
const nativeURL = new URL('addons/loaders/KTX2Loader.js', vendor);
const nativeText = (await fs.readFile(nativeURL, 'utf8'))
  .replace(/from '([^']+)'/g, (_, spec) => `from '${spec === 'three' ? threeURL : spec === '../math/ColorSpaces.js' ? colors : new URL(spec, nativeURL).href}'`)
  .replaceAll('import.meta.url', JSON.stringify(nativeURL.href));
const { KTX2Loader: NativeKTX2Loader } = await import(dataModule(nativeText));
const { KHR_DF_PRIMARIES_BT709, KHR_DF_TRANSFER_SRGB } = await import(new URL('addons/libs/ktx-parse.module.js', vendor));
const container = { faceCount: 1, layerCount: 0, dataFormatDescriptor: [{ colorPrimaries: KHR_DF_PRIMARIES_BT709, transferFunction: KHR_DF_TRANSFER_SRGB }] };
function texture(size = 1024, levels = 11, rgba = false) {
  const mipmaps = Array.from({ length: levels }, (_, i) => {
    const width = Math.max(1, size >> i);
    return { width, height: width, data: new Uint8Array(rgba ? width * width * 4 : Math.ceil(width / 4) ** 2 * 16).fill(i + 1) };
  });
  return NativeKTX2Loader.prototype._createTextureFrom({ type: 'transcode', data: {
    faces: [{ mipmaps }], width: size, height: size,
    format: rgba ? THREE.RGBAFormat : THREE.RGBA_BPTC_Format,
    type: THREE.UnsignedByteType, dfdFlags: 0,
  } }, container);
}
const proposed = await fs.readFile(js, 'utf8');
let fixtureSequence = 0;
async function moduleFor(profile, disabled = false) {
  const fixtures = new Map();
  let decoder;
  class ControlledKTX2Loader extends NativeKTX2Loader {
    constructor() { super(); decoder = this; this.workerPool.workerStatus = 0; this.workerPool.workersResolve = [() => {}]; }
    detectSupport() { this.workerConfig = { dxtSupported: true }; return this; }
    load(url, onLoad, onProgress, onError) {
      const f = fixtures.get(url);
      if (f instanceof Error) { onError?.(f); return 'returned-error'; }
      onProgress?.({ loaded: 1 }); onLoad?.(f()); return 'returned-load';
    }
    loadAsync(url) { return new Promise((resolve, reject) => this.load(url, resolve, undefined, reject)); }
  }
  const marker = `__nativePolicyLoader${fixtureSequence++}`;
  globalThis[marker] = ControlledKTX2Loader;
  const code = proposed.replace("import * as THREE from 'three';", `import * as THREE from '${threeURL}';`)
    .replace("import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';", `const KTX2Loader = globalThis[${JSON.stringify(marker)}];`);
  let module;
  try { module = await import(dataModule(code)); } finally { delete globalThis[marker]; }
  module.initKTX2({}, { textures: profile, disabled });
  const gltf = { setKTX2Loader(l) { this.ktx2Loader = l; } };
  module.registerKTX2(gltf);
  return { module, fixtures, l: gltf.ktx2Loader, decoder };
}
let checks = 0;
const check = (condition, message) => { assert(condition, message); checks++; };
for (const profile of ['full', 'light']) {
  const { module, fixtures, l, decoder } = await moduleFor(profile);
  const raw = texture(), initialPayloads = raw.mipmaps.map(m => m.data.slice());
  fixtures.set('initial', () => raw); fixtures.set('reload', () => texture());
  const sheetRaw = texture(); fixtures.set('sheet', () => sheetRaw); fixtures.set('single', () => texture(1, 1));
  const load = url => new Promise((resolve, reject) => l.load(url, resolve, undefined, reject));
  const first = await load('initial'), reload = await load('reload'), sheet = await module.loadCompressed('sheet');
  const expected = profile === 'light' ? 512 : 1024, count = profile === 'light' ? 10 : 11;
  for (const image of [first, reload, sheet]) {
    check(image.image.width === expected, 'policy width'); check(image.image.height === expected, 'policy height'); check(image.mipmaps.length === count, 'policy mip count');
  }
  assert.deepEqual(first.mipmaps.map(m => [m.width, m.height]), reload.mipmaps.map(m => [m.width, m.height])); checks++;
  fixtures.set('clone', () => first.clone());
  const clone = await load('clone'); check(clone.image.width === expected, 'already-selected clone width'); check(clone.mipmaps.length === count, 'already-selected clone is not trimmed twice');
  const single = await load('single'); check(single.image.width === 1, 'single width'); check(single.mipmaps.length === 1, 'single mip');
  const originalBytes = initialPayloads.reduce((s, m) => s + m.byteLength, 0), kept = first.mipmaps.reduce((s, m) => s + m.data.byteLength, 0);
  check(kept === (profile === 'light' ? originalBytes - initialPayloads[0].byteLength : originalBytes), 'exact selected tail bytes');
  check(decoder.workerPool.workersResolve[0] === null, 'actual decoder idle pool reply released');
  let progress = 0; check(l.load('initial', () => {}, () => progress++) === 'returned-load', 'native load return forwarded'); check(progress === 1, 'progress forwarded');
  fixtures.set('error', new Error('decode refused')); let error;
  check(l.load('error', () => assert.fail('must not load'), undefined, e => error = e) === 'returned-error', 'error return forwarded'); check(error.message === 'decode refused', 'decode error forwarded');
  const again = await load('initial');
  check(first !== again && first.source === again.source, 'independent deliveries share stable selected Source');
  check(first.mipmaps.every((m, i) => m !== again.mipmaps[i]), 'delivery mip descriptors isolated');
  for (const mip of first.mipmaps) mip.data = new Uint8Array(0);
  check(raw.image.width === 1024 && raw.mipmaps.length === 11, 'raw cached full dimensions unmodified');
  check(raw.mipmaps.every((m, i) => Buffer.from(m.data).equals(Buffer.from(initialPayloads[i]))), 'raw cached full payload unmodified after delivered release');
  check(again.mipmaps.every(m => m.data.byteLength > 0), 'other delivery populated after release');
  const afterRelease = await load('initial'); check(afterRelease.source === again.source && afterRelease.mipmaps.every(m => m.data.byteLength > 0), 'cached re-delivery populated');
  const sheetAgain = await module.loadCompressed('sheet'); check(sheetAgain.image.width === expected && sheetAgain.mipmaps.length === count, 'cached library sheet not trimmed twice');
  console.log(JSON.stringify({ profile, initialWidth: again.image.width, reloadWidth: reload.image.width, sheetWidth: sheet.image.width, keptLevels: count, keptBytes: kept, originalBytes }));
}
for (const profile of ['full', 'light']) {
  const { fixtures, l, decoder } = await moduleFor(profile, true);
  const raw = texture(1024, 11, true); fixtures.set('rgba', () => raw);
  const result = await new Promise(r => l.load('rgba', r));
  check(raw.isCompressedTexture === true && raw.isDataTexture !== true && raw.format === THREE.RGBAFormat, 'native Basis RGBA32 fallback is CompressedTexture/RGBA, not DataTexture');
  check(result.image.width === (profile === 'light' ? 512 : 1024), 'RGBA fallback selected width');
  check(result.mipmaps.length === (profile === 'light' ? 10 : 11), 'RGBA fallback selected chain');
  check(Object.values(decoder.workerConfig).every(v => !v), 'original fallback decoder has all block targets disabled');
  check(result.mipmaps.every(m => m.data.byteLength === m.width * m.height * 4), 'actual RGBA mip bytes retained');
  check(raw.image.width === 1024 && raw.mipmaps.length === 11, 'RGBA decoder cache remains full');
  const again = await new Promise(r => l.load('rgba', r));
  check(result.source === again.source && result.mipmaps.every((m, i) => m !== again.mipmaps[i]), 'RGBA repeat source sharing and descriptor isolation');
}
console.log(`PASS ${checks} device texture policy checks. Actual pinned Three/KTX2 constructor layout; controlled decode delivery/support detection, no browser/GPU/appearance claim.`);
