#!/usr/bin/env node
// T-2568: the structures batch stores its per-vertex channels compact. This
// holds the formats to the precision compact-attributes.js promises, holds the
// plan to ONE format per batch, and shows a BatchedMesh takes the result.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/compact-attributes.js'), 'utf8');
const { compactPlan, compactGeometry, bytesPerVertex, strideOf, RULES } = await import('data:text/javascript;base64,'
  + Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64'));

function building(n, { uv = 1, tone = 0.9 } = {}) {
  const g = new THREE.BufferGeometry();
  const f = (k, fn) => new THREE.BufferAttribute(Float32Array.from({ length: n * k }, (_, i) => fn(i)), k);
  g.setAttribute('position', f(3, (i) => (i % 7) * 3.25 - 9));
  const normals = Float32Array.from({ length: n * 3 }, (_, i) => Math.sin(i * 1.7));
  for (let v = 0; v < n; v += 1) {
    const l = Math.hypot(normals[v * 3], normals[v * 3 + 1], normals[v * 3 + 2]) || 1;
    for (let k = 0; k < 3; k += 1) normals[v * 3 + k] /= l;
  }
  g.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
  g.setAttribute('uv', f(2, (i) => ((i * 0.137) % 1) * uv));
  g.setAttribute('color', f(3, (i) => tone - (Math.floor(i / 3) % 5) * 0.05));
  g.setAttribute('_roughness', f(1, () => 0.85));
  g.setAttribute('_confidence', f(1, (i) => [0, 0.5, 1][i % 3]));
  g.setIndex(Array.from({ length: n - (n % 3) }, (_, i) => i));
  return g;
}

// 0. Every rule writes a four-byte-aligned stride (Metal; see the module header),
//    and a rule that would not is refused rather than shipped.
for (const [name, rule] of Object.entries(RULES)) {
  const size = name.startsWith('uv') ? 2 : 3;
  assert.equal(strideOf(rule, size) % 4, 0, `${name}: ${strideOf(rule, size)}-byte stride`);
}
assert.throws(() => compactPlan([building(9)], { _roughness: { array: Uint8Array, min: 0, max: 1 } }),
  /stride/);
console.log('PASS alignment: every compact stride is a multiple of four bytes, and a narrower one is refused');

// 1. Precision: each channel within the bound its format promises, the rest untouched.
const a = building(30);
const before = Object.fromEntries(Object.entries(a.attributes).map(([k, v]) => [k, v.clone()]));
const was = bytesPerVertex(a);
const plan = compactPlan([a]);
assert.deepEqual([...plan.keys()].sort(), ['color', 'normal', 'uv']);
compactGeometry(a, plan);
const within = (name, bound) => {
  const old = before[name], now = a.getAttribute(name);
  for (let i = 0; i < old.count; i += 1) {
    for (let k = 0; k < old.itemSize; k += 1) {
      const d = Math.abs(old.getComponent(i, k) - now.getComponent(i, k));
      assert.ok(d <= bound, `${name}[${i}.${k}] moved ${d}, bound ${bound}`);
    }
  }
};
within('position', 0);
within('_roughness', 0);
within('_confidence', 0);
within('normal', 0.5 / 127 + 1e-9);
within('uv', 0.5 / 65535 + 1e-9);
within('color', 0.5 / 255 + 1e-9);
const colour = a.getAttribute('color');
assert.equal(colour.itemSize, 4);
for (let i = 0; i < colour.count; i += 1) assert.equal(colour.getW(i), 1, 'a padded colour is opaque');
assert.equal(a.getAttribute('normal').itemSize, 4, 'normals padded to four bytes');
const bpv = bytesPerVertex(a);
// 12 position + 4 normal + 4 uv + 4 tone + 4 roughness + 4 confidence.
assert.equal(bpv, 32);
console.log(`PASS compact formats: ${was} -> ${bpv} bytes a vertex, every channel within its format's bound`);

// 2. One plan per batch: a tiling uv anywhere keeps the whole batch's uv float,
//    a brightening tone keeps the tone float, and a NaN is never squeezed.
const shared = compactPlan([building(9), building(9, { uv: 4 })]);
assert.ok(!shared.has('uv') && shared.has('normal'));
assert.ok(!compactPlan([building(9), building(9, { tone: 1.08 })]).has('color'));
const nan = building(9); nan.getAttribute('normal').array[3] = NaN;
assert.ok(!compactPlan([nan]).has('normal'));
const missing = building(9); missing.deleteAttribute('uv');
assert.ok(!compactPlan([building(9), missing]).has('uv'));
console.log('PASS one plan per batch: out-of-range, NaN and missing channels stay as they arrived');

// 3. A BatchedMesh takes compacted geometry, keeps its formats, and stores an
//    instance colour exactly.
const parts = [building(30), building(60), building(90)];
const p2 = compactPlan(parts);
for (const g of parts) compactGeometry(g, p2);
const batch = new THREE.BatchedMesh(3, 180, 180, new THREE.MeshStandardMaterial());
for (const g of parts) batch.addInstance(batch.addGeometry(g));
assert.ok(batch.geometry.getAttribute('normal').array instanceof Int8Array);
assert.ok(batch.geometry.getAttribute('uv').array instanceof Uint16Array);
assert.ok(batch.geometry.getAttribute('color').normalized);
assert.ok(batch.geometry.getAttribute('_confidence').array instanceof Float32Array);
batch.setColorAt(0, new THREE.Color(0.25, 0.5, 0.75));
const back = batch.getColorAt(0, new THREE.Color());
assert.deepEqual([back.r, back.g, back.b], [0.25, 0.5, 0.75], 'instance colour is stored exactly');
batch.dispose();
console.log('PASS batch: BatchedMesh keeps the compact formats and the instance colour is exact');
