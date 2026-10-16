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
const {
  compactPlan, compactGeometry, bytesPerVertex, strideOf, RULES,
  positionScale, quantizePositions, structureFrameGLSL, POSITION_STEPS,
  packScalars, unpackScalar, toneScaleOf, SCALARS, SCALAR_CODES, SCALARS_GLSL,
} = await import('data:text/javascript;base64,'
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

// 4. T-2574: roughness, confidence, grain and the piece tone packed into ONE
//    four-byte attribute. Every value the dataset writes comes back exact, the
//    tone within half a step of its batch's scale, and the GLSL the shaders
//    decode with reads the same number as the readback.
const f32 = Math.fround;
function scalars(n, { tone = null, grain = null } = {}) {
  const g = building(n);
  g.deleteAttribute('color');
  const f = (fn) => new THREE.BufferAttribute(Float32Array.from({ length: n }, (_, i) => fn(i)), 1);
  g.setAttribute('_roughness', f((i) => [0.85, 0.9, 0.3, 0.95, 0.62, 1][i % 6]));
  if (tone) g.setAttribute('_tone', f(tone));
  if (grain) g.setAttribute('_grain', f(grain));
  return g;
}
const plain = scalars(30);
const toned = scalars(30, { tone: (i) => 0.8 + (i % 7) * 0.05, grain: (i) => [1, -1, 0.3, -0.3, 0][i % 5] });
const src = (g, name) => g.getAttribute(name)?.array.slice();
const kept = { plain: Object.fromEntries(['_roughness', '_confidence'].map((k) => [k, src(plain, k)])),
  toned: Object.fromEntries(['_roughness', '_confidence', '_grain', '_tone'].map((k) => [k, src(toned, k)])) };
assert.equal(toneScaleOf([plain]), 255, 'no tone: a scale of 255, so 1 is exactly 1');
const scale = toneScaleOf([plain, toned]);
assert.equal(scale, 231, 'the batch scale: the largest whole number fitting 1.1 in a byte');
packScalars(plain, scale);
packScalars(toned, scale);
for (const g of [plain, toned]) {
  for (const name of Object.keys(SCALAR_CODES)) assert.equal(g.getAttribute(name), undefined, `${name} source deleted`);
  const p = g.getAttribute(SCALARS);
  assert.ok(p.array instanceof Uint8Array && p.itemSize === 4 && !p.normalized);
}
for (const [g, k] of [[plain, kept.plain], [toned, kept.toned]]) {
  const p = g.getAttribute(SCALARS);
  for (let i = 0; i < p.count; i += 1) {
    for (const name of ['_roughness', '_confidence', '_grain']) {
      const want = k[name] ? k[name][i] : 0;
      assert.equal(f32(unpackScalar(p, name, i, scale)), want, `${name}[${i}] exact`);
    }
    const tone = k._tone ? k._tone[i] : 1;
    assert.ok(Math.abs(unpackScalar(p, '_tone', i, scale) - tone) <= 0.5 / scale + 1e-9, `_tone[${i}]`);
  }
}
assert.equal(unpackScalar(plain.getAttribute(SCALARS), '_tone', 0, scale), 1, 'untoned in a toned batch: exactly 1');
// NaN and the clamps the shader already applied.
const odd = scalars(3);
odd.getAttribute('_confidence').array.set([NaN, 1.4, -0.2]);
odd.getAttribute('_roughness').array.set([1.6, -1, 0.5]);
packScalars(odd, 255);
const o = odd.getAttribute(SCALARS);
assert.deepEqual([0, 1, 2].map((i) => unpackScalar(o, '_confidence', i)), [0, 1, 0]);
assert.deepEqual([0, 1, 2].map((i) => unpackScalar(o, '_roughness', i)), [1, 0, 0.5]);
// The shaders' GLSL and the readback are one decode.
const glsl = (expr, bytes, s) => Function(`return ${expr
  .replace(/_chiScalars\.([xyzw])/g, (_, l) => bytes['xyzw'.indexOf(l)])
  .replace(/chiToneScale/g, s)};`)();
const t = toned.getAttribute(SCALARS);
for (let i = 0; i < t.count; i += 1) {
  const bytes = [...t.array.slice(i * 4, i * 4 + 4)];
  for (const [lane, name] of [['roughness', '_roughness'], ['confidence', '_confidence'], ['grain', '_grain'], ['tone', '_tone']]) {
    assert.equal(glsl(SCALARS_GLSL[lane], bytes, scale), unpackScalar(t, name, i, scale), `${lane} GLSL = readback`);
  }
}
assert.match(SCALARS_GLSL.declare('void main(){}'), /^attribute vec4 _chiScalars;\n/);
assert.equal(SCALARS_GLSL.declare(SCALARS_GLSL.declare('x')), SCALARS_GLSL.declare('x'), 'declared once');
const both = compactPlan([plain, toned]);
for (const g of [plain, toned]) compactGeometry(g, both);
// 12 position + 4 normal + 4 uv + 4 packed scalars.
assert.equal(bytesPerVertex(toned), 24);
const sb = new THREE.BatchedMesh(2, 60, 60, new THREE.MeshStandardMaterial());
for (const g of [plain, toned]) sb.addInstance(sb.addGeometry(g));
const sa = sb.geometry.getAttribute(SCALARS);
assert.ok(sa.array instanceof Uint8Array && !sa.normalized && sa.itemSize === 4);
assert.deepEqual([...sa.array.slice(30 * 4, 30 * 4 + 4)], [...t.array.slice(0, 4)], 'the batch keeps the bytes');
sb.dispose();
console.log(`PASS packed scalars: four channels in four bytes (24 a vertex here), exact where the data is, GLSL = readback`);

// T-2575, in its own block: its names are its own.
{
// 5. T-2575: positions as Int16 x4 over one uniform scale per structure, the
//    scale in the instance matrix. Within half a step of where they were, on an
//    aligned stride, drawn where they were drawn, and two pieces of one
//    structure share a grid so a shared vertex never splits.
const wall = building(30);
const roof = building(30);
roof.getAttribute('position').array.forEach((v, i, arr) => { arr[i] = v * 0.5 + 41.7; });
roof.getAttribute('position').array[0] = wall.getAttribute('position').array[0];
const pieces = [wall, roof];
const was0 = pieces.map((g) => g.getAttribute('position').clone());
const scale = positionScale(pieces);
assert.ok(scale >= 41.7 && Number.isFinite(scale));
assert.equal(positionScale([new THREE.BufferGeometry().setAttribute('position',
  new THREE.BufferAttribute(new Float32Array(9), 3))]), 1, 'a structure with no extent gets 1');
const placement = new THREE.Matrix4().compose(new THREE.Vector3(-812.4, 3.1, 1530.9),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0.6431, 0)), new THREE.Vector3(1, 1, 1));
const instance = placement.clone().multiply(new THREE.Matrix4().makeScale(scale, scale, scale));
for (const g of pieces) quantizePositions(g, scale);
const step = scale / POSITION_STEPS;
for (const [k, g] of pieces.entries()) {
  const pos = g.getAttribute('position');
  assert.ok(pos.array instanceof Int16Array && pos.normalized && pos.itemSize === 4);
  assert.equal(strideOf({ array: Int16Array, pad: 4 }, 3) % 4, 0);
  for (let i = 0; i < pos.count; i += 1) {
    const local = new THREE.Vector3().fromBufferAttribute(was0[k], i);
    const drawn = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(instance);
    const d = drawn.distanceTo(local.clone().applyMatrix4(placement));
    assert.ok(d <= step * 0.5 * Math.sqrt(3) + 1e-4, `vertex ${k}.${i} drawn ${d} m off, half a step is ${step / 2}`);
  }
}
assert.deepEqual([wall, roof].map((g) => g.getAttribute('position').getX(0)),
  [wall.getAttribute('position').getX(0), wall.getAttribute('position').getX(0)], 'one grid per structure');
assert.equal(bytesPerVertex(wall) - bytesPerVertex(building(30)), 8 - 12, 'position 12 -> 8 bytes a vertex');
console.log(`PASS positions: Int16 x4 over +/-${scale.toFixed(2)} m, drawn within half a ${(step * 1000).toFixed(2)} mm step, one grid per structure`);

// 6. The scale is uniform because three corrects a batch normal by the matrix's
//    squared column lengths, assuming the stored normal is the stored
//    geometry's. Under a uniform scale that correction only shortens it: the lit
//    normal is the placement's rotation of the building's normal.
const bm = new THREE.Matrix3().setFromMatrix4(instance);
const placed = new THREE.Matrix3().setFromMatrix4(placement);
const e = bm.elements;
const colSq = [0, 1, 2].map((c) => e[c * 3] ** 2 + e[c * 3 + 1] ** 2 + e[c * 3 + 2] ** 2);
for (const n of [[1, 0, 0], [0, 1, 0], [0.6, 0, 0.8], [0.267, 0.534, 0.802]]) {
  const v = new THREE.Vector3(n[0] / colSq[0], n[1] / colSq[1], n[2] / colSq[2]).applyMatrix3(bm).normalize();
  const want = new THREE.Vector3(...n).normalize().applyMatrix3(placed);
  assert.ok(v.distanceTo(want) < 1e-6, `normal ${n} lit as ${v.toArray()}, want ${want.toArray()}`);
}
console.log('PASS normals: under the uniform dequantize scale three lights the building\'s own normal');

// 7. A relief patch gets the structure's frame back: the shader multiplies the
//    stored position by the length of the instance matrix's first column.
const glsl = structureFrameGLSL('chiP');
assert.match(glsl, /vec3 chiP = transformed \* length\( batchingMatrix\[ 0 \]\.xyz \);/);
assert.match(glsl, /#else\s+vec3 chiP = transformed;/);
assert.ok(Math.abs(new THREE.Vector3(e[0], e[1], e[2]).length() - scale) < scale * 1e-6);
console.log('PASS structure frame: the relief patches read metres in the structure\'s frame off the instance matrix');

// 8. A BatchedMesh keeps Int16 x4 normalized positions, and a ray through the
//    instance matrix hits the quantized building where the float one stood.
const box = new THREE.BoxGeometry(6, 9, 4).toNonIndexed();
box.translate(0, 4.5, 0);
box.deleteAttribute('uv');
box.computeBoundingBox(); // in metres, as buildings.js leaves it — and stale once quantized
box.computeBoundingSphere();
const boxScale = positionScale([box]);
quantizePositions(box, boxScale);
const one = new THREE.BatchedMesh(1, box.getAttribute('position').count, 0, new THREE.MeshBasicMaterial());
one.setMatrixAt(one.addInstance(one.addGeometry(box)),
  placement.clone().multiply(new THREE.Matrix4().makeScale(boxScale, boxScale, boxScale)));
assert.ok(one.geometry.getAttribute('position').array instanceof Int16Array);
assert.ok(one.geometry.getAttribute('position').normalized);
const held = one.getBoundingBoxAt(0, new THREE.Box3());
assert.ok(held.max.y <= 1 && held.min.y >= -1, `the batch holds the piece's bounds in stored units, not metres: ${held.max.y}`);
one.updateMatrixWorld(true);
const centre = new THREE.Vector3(0, 4.5, 0).applyMatrix4(placement);
const ray = new THREE.Raycaster(centre.clone().add(new THREE.Vector3(0, 20, 0)), new THREE.Vector3(0, -1, 0));
const hit = ray.intersectObject(one)[0];
assert.ok(hit && Math.abs(hit.point.y - (placement.elements[13] + 9)) < boxScale / POSITION_STEPS,
  `ray hit the roof at ${hit?.point.y}, want ${placement.elements[13] + 9}`);
one.dispose();
console.log('PASS batch: BatchedMesh keeps Int16 x4 positions and a pick lands on the roof through the instance matrix');
}
