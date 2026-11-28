// SPDX-License-Identifier: GPL-3.0-or-later
// A compact clothing work grid must return the same point as a full scan. No mesh,
// query radius, cell size or ordering changes are allowed by this memory correction.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const three = new URL('renderers/web/vendor/three-0.185.1/three.core.js', here).href;
const source = (await fs.readFile(new URL('renderers/web/js/human-drape.js', here), 'utf8'))
  .replace("from 'three'", `from '${three}'`);
const { kit } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

// Independent oracle: examine every point inside the allowed cell cube. Equal
// distances follow the original shell, x/y/z, then source-vertex order.
function scan(P, cell, query, reach) {
  const lo = [0, 1, 2].map((axis) => {
    let m = Infinity; for (let i = axis; i < P.length; i += 3) m = Math.min(m, P[i]);
    return Number.isFinite(m) ? m - cell : -cell;
  });
  const q = query.map((v, axis) => Math.floor((v - lo[axis]) / cell));
  let best = Infinity, index = -1, order = null;
  for (let i = 0; i < P.length; i += 3) {
    const c = [0, 1, 2].map((axis) => Math.floor((P[i + axis] - lo[axis]) / cell));
    const ring = Math.max(...c.map((v, axis) => Math.abs(v - q[axis])));
    if (ring > reach) continue;
    const d = (P[i] - query[0]) ** 2 + (P[i + 1] - query[1]) ** 2 + (P[i + 2] - query[2]) ** 2;
    const rank = [ring, ...c, i], earlier = !order || rank.some((v, j) => v < order[j] && rank.slice(0, j).every((x, k) => x === order[k]));
    if (d < best || (d === best && earlier)) { best = d; index = i / 3; order = rank; }
  }
  return index;
}
let seed = 3747, count = 0;
const rand = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const fixtures = [[], [0, 0, 0], [0, 0, 0, 0, 0, 0], [-1, 0, 0, 1, 0, 0]];
for (const n of [31, 300, 2000]) {
  const shell = [], solid = [];
  for (let i = 0; i < n; i++) {
    const angle = rand() * 2 * Math.PI;
    shell.push(.4 * Math.cos(angle), 2 * rand(), .2 * Math.sin(angle));
    solid.push(.2 * rand(), .2 * rand(), .2 * rand());
  }
  fixtures.push(shell, solid);
}
for (const values of fixtures) for (const cell of [.01, .02, .03, .2]) {
  const P = Float64Array.from(values), near = kit.pointGrid(P, cell);
  const queries = [[0, 0, 0], [-4, -4, -4], [4, 4, 4]];
  for (let i = 0; i < 240; i++) queries.push([rand() - .5, 2.4 * rand() - .2, rand() - .5]);
  for (let i = 0; i < Math.min(P.length, 90); i += 3) queries.push([P[i], P[i + 1], P[i + 2]]);
  for (const q of queries) for (const reach of [0, 1, 4, 8]) {
    assert.equal(near(...q, reach), scan(P, cell, q, reach), JSON.stringify({ cell, q, reach })); count++;
  }
}
console.log(`OK: ${count} clothing nearest-point queries match an independent full scan, including sparse shells, dense fallback, bounds, reach, duplicate points and ties`);

// Run the real asset-store lifetime with small loader/pass stand-ins. The ordinary
// clothing tests exercise real exports; this checks who still owns their resources.
const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
const begin = humans.indexOf('export function createHumanAssets(');
const end = humans.indexOf('/** Hit proxy:', begin);
assert(begin >= 0 && end > begin);
const code = humans.slice(begin, end).replace(/^export /gm, '');
const dependencies = {
  globalThis: {}, THREE: {},
  createCheckpoint: () => () => null,
  shareImageSources() {},
  disposeVariants() {},
};
let current, fetches = 0, parses = 0, disposed = 0, stages = 0;
const header = new TextEncoder().encode(JSON.stringify({ extensionsUsed: [] }));
const bytes = new ArrayBuffer(20 + header.length);
new DataView(bytes).setUint32(12, header.length, true);
new Uint8Array(bytes, 20).set(header);
const material = { color: 'fixture' };
const scene = { traverse(f) { f({ geometry, material }); } };
const geometry = { attributes: { position: { array: new Float32Array([1, 2, 3]) } } };
const clips = [{ name: 'walk' }], metadata = { author: 'fixture' };
const shared = geometry.attributes.position.array;
const ensureLive = (root) => {
  assert.equal(current.parser, null, 'loader scratch is released before the first clothing slice');
  assert.equal(root, scene); assert.equal(geometry.attributes.position.array, shared); stages++;
};
for (const name of ['drapeGarments', 'fairOuter', 'refineTrims', 'settleOnBody', 'layOver', 'tuckPits', 'bindLayers', 'cullHidden']) {
  dependencies[name + 'Steps'] = function* (root) { ensureLive(root); yield; };
}
for (const name of ['dressCollars', 'easeSeats', 'fitCoats', 'fitSleeves', 'tailor1835', 'fitRegulars', 'fitFrockCoat', 'fitGown', 'fitWaist', 'engraveSilver']) dependencies[name] = ensureLive;
dependencies.disposeLoadedAsset = (asset) => {
  assert.equal(asset.scene, scene); assert.equal(asset.animations, clips); disposed++;
};
const factory = new Function(...Object.keys(dependencies), code + '\nreturn createHumanAssets;')(...Object.values(dependencies));
const assets = factory({ assetBase: new URL('https://fixture.invalid/assets/'),
  fetchImpl: async () => { fetches++; return { ok: true, arrayBuffer: async () => bytes }; },
  loader: { async parseAsync(input, base) {
    assert.equal(input, bytes, 'the exact fetched buffer reaches the loader');
    assert.equal(base, 'https://fixture.invalid/assets/humans/web/'); parses++;
    current = { parser: { binary: new Uint8Array(1048576) }, scene, scenes: [scene], animations: clips, asset: metadata };
    return current;
  } },
});
const first = assets.acquire('fixture', 0), second = assets.acquire('fixture', 0);
assert.equal(first, second, 'two users share the same source promise');
const [a, b] = await Promise.all([first, second]);
assert.equal(a, b); assert.equal(a.scene, scene); assert.equal(a.scenes[0], scene);
assert.equal(a.animations, clips); assert.equal(a.asset, metadata); assert.equal(a.parser, null);
scene.traverse((mesh) => assert.equal(mesh.material, material));
assert.equal(fetches, 1); assert.equal(parses, 1); assert.equal(stages, 18);
assets.release('fixture', 0); await Promise.resolve(); assert.equal(disposed, 0);
assert.deepEqual(assets.loaded, ['fixture.lod0']);
assets.release('fixture', 0); await Promise.resolve(); assert.equal(disposed, 1);
assert.deepEqual(assets.loaded, []);
await assets.acquire('fixture', 0); assert.equal(fetches, 2); assert.equal(parses, 2);
assets.release('fixture', 0); await Promise.resolve(); assert.equal(disposed, 2);
console.log('OK: shared human sources release parser scratch before clothing, preserve geometry/material/animation identity and metadata, and dispose only after the final user');

// Distinct sources may decode together; their long sliced clothing work must not
// keep multiple welded graphs live. Exercise the real store, including recovery
// after one source's clothing pass rejects.
let unblock, blocked = false, active = 0, peak = 0, decoded = 0;
const pause = new Promise((resolve) => { unblock = resolve; });
const jobs = { ...dependencies,
  createCheckpoint: () => () => { if (!blocked) { blocked = true; return pause; } return null; },
  disposeLoadedAsset() {},
};
for (const name of ['dressCollars', 'easeSeats', 'fitCoats', 'fitSleeves', 'tailor1835', 'fitRegulars', 'fitFrockCoat', 'fitGown', 'fitWaist', 'engraveSilver']) jobs[name] = () => {};
for (const name of ['drapeGarments', 'fairOuter', 'refineTrims', 'settleOnBody', 'layOver', 'tuckPits', 'bindLayers', 'cullHidden']) jobs[name + 'Steps'] = function* () {};
jobs.drapeGarmentsSteps = function* (root) {
  if (root.fail) throw Error('fixture clothing failure');
  active++; peak = Math.max(peak, active); yield;
};
jobs.cullHiddenSteps = function* () { active--; };
const make = new Function(...Object.keys(jobs), code + '\nreturn createHumanAssets;')(...Object.values(jobs));
const queued = make({ assetBase: new URL('https://fixture.invalid/assets/'),
  fetchImpl: async () => ({ ok: true, arrayBuffer: async () => bytes }),
  loader: { async parseAsync(input, base) { decoded++; return { parser: { input }, scene: { traverse() {} }, animations: [] }; } },
});
const both = Promise.all([queued.acquire('one', 0), queued.acquire('two', 0)]);
for (let i = 0; i < 30 && (decoded < 2 || active < 1); i++) await Promise.resolve();
assert.equal(decoded, 2, 'both source decodes complete while the first clothing pass waits');
assert.equal(active, 1, 'only one source clothing graph stays live');
assert.equal(peak, 1); unblock(); await both; assert.equal(active, 0); assert.equal(peak, 1);
queued.release('one', 0); queued.release('two', 0);
let attempts = 0;
const resilient = make({ assetBase: new URL('https://fixture.invalid/assets/'),
  fetchImpl: async () => ({ ok: true, arrayBuffer: async () => bytes }),
  loader: { async parseAsync() { return { parser: {}, scene: { fail: ++attempts === 1, traverse() {} }, animations: [] }; } },
});
const failed = resilient.acquire('bad', 0), next = resilient.acquire('good', 0);
await assert.rejects(failed, /fixture clothing failure/); await next;
assert.deepEqual(resilient.loaded, ['good.lod0'], 'a failed preparation cannot poison the next source or remain cached');
resilient.release('good', 0);
console.log('OK: source decoding stays parallel, clothing preparation holds one work graph, and rejection does not block the next source');
