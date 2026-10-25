/** Exact ground batching contracts, including Three's real per-instance cull.
 * CPU geometry/state checks; published pixels and frame costs stay smoke gates.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/spatial-batch.js'), 'utf8');
const jobsURL = pathToFileURL(path.join(web, 'js/jobs/')).href;
const { spatialBatch, spatialPieces, spatialBatchAsync, spatialPiecesAsync } = await import(
  'data:text/javascript;base64,' + Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)
    .replaceAll("from './jobs/", `from '${jobsURL}`)
    .replace("from './batch-coalesce.js'", `from '${pathToFileURL(path.join(web, 'js/batch-coalesce.js')).href}'`))
    .toString('base64'));

function triangles(geometry) {
  const attrs = Object.entries(geometry.attributes).sort(([a], [b]) => a.localeCompare(b));
  const index = geometry.getIndex();
  const count = index?.count ?? geometry.getAttribute('position').count;
  const out = [];
  for (let i = 0; i < count; i += 3) {
    out.push(JSON.stringify([0, 1, 2].map((j) => {
      const k = index ? index.getX(i + j) : i + j;
      return attrs.map(([name, a]) => [name, a.itemSize, a.normalized,
        [...a.array.slice(k * a.itemSize, (k + 1) * a.itemSize)]]);
    })));
  }
  return out.sort();
}

for (const indexed of [false, true]) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute([
    -2, 0, -20, 2, 0, -20, 0, 1, -20,
    -2, 0, 100, 2, 0, 100, 0, 1, 100,
    38, 0, -20, 42, 0, -20, 40, 1, -20,
  ], 3));
  geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute([0, .5, 1, 1, .5, 0, .5, 1, 0], 1));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 1, 0, 0, 1, 1, 1, 2, 1, 1, 2, 2, 2, 3, 2, 2, 3], 2));
  geometry.setAttribute('color', new THREE.Uint8BufferAttribute(
    Array.from({ length: 36 }, (_, i) => i * 7), 4, true));
  if (indexed) geometry.setIndex([0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 2, 1]);
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({ transparent: true, depthWrite: false });
  const batch = spatialBatch(geometry, material);
  assert.deepEqual(triangles(batch.geometry), triangles(geometry), 'every triangle, winding and attribute byte survives');
  assert.equal(batch.material, material, 'the material is shared unchanged');
  assert.equal(batch.material.depthWrite, false, 'a ground decal keeps its depth policy');
  assert.equal(batch.perObjectFrustumCulled, true);
  assert.equal(batch.userData.spatialBatch.pieces, 3);
  const identity = new THREE.Matrix4();
  for (let i = 0; i < 3; i++) {
    assert.deepEqual(batch.getMatrixAt(i, new THREE.Matrix4()).elements, identity.elements);
  }
  // A triangle straddling the fixed-grid edge keeps its corners in its bounds.
  const edge = batch.getBoundingBoxAt(2, new THREE.Box3());
  assert.equal(edge.min.x, 38); assert.equal(edge.max.x, 42);
  const camera = new THREE.OrthographicCamera(-60, 60, 60, -60, 1, 200);
  camera.updateMatrixWorld(); batch.updateMatrixWorld();
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 2, 'the piece behind the visitor is not submitted');
  batch.setVisibleAt(0, false);
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 1, 'the reach can hold one piece without hiding its tile');
  batch.setVisibleAt(0, true);
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 2, 'restoring the reach restores the exact pieces');
  camera.lookAt(0, 0, 100); camera.updateMatrixWorld();
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 1, 'turning round restores the ground behind the old view');
  const ray = new THREE.Raycaster(new THREE.Vector3(0, .3, 0), new THREE.Vector3(0, 0, -1));
  const original = new THREE.Mesh(geometry, material);
  original.updateMatrixWorld();
  const hits = (mesh) => ray.intersectObject(mesh).map((h) => [h.distance, ...h.point.toArray()]);
  assert.ok(hits(original).length, 'the pick probe intersects the ground fixture');
  assert.deepEqual(hits(batch), hits(original), 'batched ground answers the same pick points and distances');
  batch.dispose(); geometry.dispose(); material.dispose();
}
console.log('PASS spatial ground batch: indexed/nonindexed triangles, attributes, bounds, material, identity transforms, frustum and reversible reach');

// A building's upper storey shares x/z with its basement; vertical cells must
// separate them without changing any surface or losing a corner at a boundary.
for (const indexed of [false, true]) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([
    7, 0, 0, 9, 0, 0, 7, 1, 0,
    7, 8, 0, 9, 8, 0, 7, 9, 0,
  ], 3));
  for (const name of ['uv', 'uv1', '_confidence', '_roughness', '_grain', '_pane']) {
    g.setAttribute(name, new THREE.Float32BufferAttribute([0, .25, .5, .75, 1, 0], 1));
  }
  g.setAttribute('color', new THREE.Uint8BufferAttribute([1, 2, 3, 4, 5, 6], 1, true));
  if (indexed) g.setIndex([0, 1, 2, 3, 4, 5]);
  g.computeVertexNormals();
  const pieces = spatialPieces(g, { cellM: 8, heightM: 4 });
  assert.equal(pieces.length, 2);
  assert.deepEqual(pieces.flatMap(triangles).sort(), triangles(g));
  for (const p of pieces) {
    p.computeBoundingBox();
    assert.equal(p.boundingBox.min.x, 7);
    assert.equal(p.boundingBox.max.x, 9);
    assert.equal(p.boundingBox.max.y - p.boundingBox.min.y, 1);
    p.dispose();
  }
  assert.throws(() => spatialPieces(g, { cellM: 0 }));
  assert.throws(() => spatialPieces(g, { heightM: NaN }));
  g.dispose();
}
console.log('PASS building cells: vertical separation, exact triangles and all attributes, boundary corners');

// T-2599: the partition is jobs/spatial-kernel.js, shared by the main thread and the
// job pool's workers. Hold it BYTE FOR BYTE to the implementation it replaced (kept
// here verbatim as the reference), then hold the pool's two paths to it: the
// synchronous fallback, the real worker module behind a page-shaped Worker, and a
// worker that fails to start.
function referencePieces(geometry, { cellM = 40, heightM = Infinity } = {}) {
  const position = geometry.getAttribute('position');
  const index = geometry.getIndex();
  const count = index ? index.count : position.count;
  const chunks = new Map();
  for (let i = 0; i < count; i += 3) {
    const ids = [0, 1, 2].map((j) => index ? index.getX(i + j) : i + j);
    const x = ids.reduce((sum, j) => sum + position.getX(j), 0) / 3;
    const z = ids.reduce((sum, j) => sum + position.getZ(j), 0) / 3;
    const y = ids.reduce((sum, j) => sum + position.getY(j), 0) / 3;
    const key = `${Math.floor(x / cellM)}:${Math.floor(z / cellM)}:${Math.floor(y / heightM)}`;
    let chunk = chunks.get(key);
    if (!chunk) { chunk = []; chunks.set(key, chunk); }
    chunk.push(...ids);
  }
  const pieces = [];
  for (const ids of chunks.values()) {
    const unique = index ? [...new Set(ids)] : ids;
    const piece = new THREE.BufferGeometry();
    for (const [name, source] of Object.entries(geometry.attributes)) {
      const data = new source.array.constructor(unique.length * source.itemSize);
      for (let i = 0; i < unique.length; i++) {
        const from = unique[i] * source.itemSize;
        data.set(source.array.subarray(from, from + source.itemSize), i * source.itemSize);
      }
      piece.setAttribute(name, new THREE.BufferAttribute(data, source.itemSize, source.normalized));
    }
    if (index) {
      const local = new Map(unique.map((id, i) => [id, i]));
      piece.setIndex(ids.map((id) => local.get(id)));
    }
    pieces.push(piece);
  }
  return pieces;
}

function bytesOf(pieces) {
  const hex = (a) => `${a.constructor.name}:${Buffer.from(a.buffer, a.byteOffset, a.byteLength).toString('hex')}`;
  return pieces.map((p) => ({
    attributes: Object.entries(p.attributes).map(([name, a]) => [name, a.itemSize, a.normalized, hex(a.array)]),
    index: p.index ? hex(p.index.array) : null,
  }));
}

function seeded(seed) {
  return () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
}

/** Random triangles over a few cells, every attribute kind spatialBatch carries. */
function randomGeometry(seed, { indexed, vertices = 600, span = 200, offset = 0, normalizedPosition = false }) {
  const rand = seeded(seed);
  const g = new THREE.BufferGeometry();
  const tri = indexed ? vertices * 2 : vertices;
  if (normalizedPosition) {
    g.setAttribute('position', new THREE.BufferAttribute(
      Int16Array.from({ length: vertices * 3 }, () => Math.round((rand() * 2 - 1) * 32767)), 3, true));
  } else {
    g.setAttribute('position', new THREE.Float32BufferAttribute(
      Array.from({ length: vertices * 3 }, (_, i) => (rand() - 0.5) * (i % 3 === 1 ? 30 : span) + (i % 3 === 1 ? 0 : offset)), 3));
  }
  g.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from({ length: vertices * 3 }, rand), 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(Array.from({ length: vertices * 2 }, rand), 2));
  g.setAttribute('color', new THREE.Uint8BufferAttribute(
    Array.from({ length: vertices * 4 }, () => Math.floor(rand() * 256)), 4, true));
  g.setAttribute('_confidence', new THREE.Float32BufferAttribute(Array.from({ length: vertices }, rand), 1));
  if (indexed) g.setIndex(Array.from({ length: tri * 3 - (tri * 3) % 3 }, () => Math.floor(rand() * vertices)));
  else if (vertices % 3) throw new Error('fixture: unindexed vertices must be whole triangles');
  return g;
}

/** Triangles whose centres sit within float rounding of a 40 m cell edge, where the
 *  order and form of the centre's arithmetic decides the cell. */
function edgeGeometry(seed) {
  const rand = seeded(seed);
  const near = () => Math.fround(40 + (Math.floor(rand() * 9) - 4) * 2 ** -18);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(Array.from({ length: 3000 * 9 },
    (_, i) => (i % 3 === 0 ? near() : i % 3 === 2 ? (i % 9 === 2 ? 0.1 : near() - 40) : rand())), 3));
  return g;
}

const fixtures = [
  ['centres on a cell edge', edgeGeometry(7), {}],
  ['unindexed', randomGeometry(1, { indexed: false }), {}],
  ['indexed', randomGeometry(2, { indexed: true }), {}],
  ['indexed, building cells', randomGeometry(3, { indexed: true }), { cellM: 8, heightM: 4 }],
  ['unindexed, building cells', randomGeometry(4, { indexed: false, vertices: 900 }), { cellM: 8, heightM: 4 }],
  ['normalized Int16 position', randomGeometry(5, { indexed: true, normalizedPosition: true }), { cellM: 0.25 }],
  // One cell past 65535 vertices: three's setIndex makes the piece's index 32-bit.
  ['indexed, a 32-bit piece', randomGeometry(6, { indexed: true, vertices: 70002, span: 10, offset: 20 }), {}],
];
let samples = 0;
for (const [name, g, cells] of fixtures) {
  const want = bytesOf(referencePieces(g, cells));
  assert.deepEqual(bytesOf(spatialPieces(g, cells)), want, `${name}: the kernel's pieces are the reference's, byte for byte`);
  assert.deepEqual(bytesOf(await spatialPiecesAsync(g, cells)), want, `${name}: the pool's main-thread fallback is the same`);
  samples += want.length;
}
assert.ok(bytesOf(spatialPieces(fixtures.find(([n]) => n.includes('32-bit'))[1])).some((p) => p.index?.startsWith('Uint32Array')),
  'the 32-bit fixture really reaches a 32-bit index');
assert.ok(bytesOf(spatialPieces(fixtures[2][1])).every((p) => p.index?.startsWith('Uint16Array')));
{
  const [, g] = fixtures[2];
  const material = new THREE.MeshBasicMaterial();
  const sync = spatialBatch(g, material);
  const pooled = await spatialBatchAsync(g, material);
  assert.deepEqual(triangles(pooled.geometry), triangles(sync.geometry), 'spatialBatchAsync draws the same triangles');
  assert.deepEqual(pooled.userData.spatialBatch, sync.userData.spatialBatch);
  sync.dispose(); pooled.dispose(); material.dispose();
}
const { jobsState: nodeJobs } = await import(jobsURL + 'pool.js');
assert.equal(nodeJobs.mode, 'main thread', 'with no Worker the pool runs on the main thread');
assert.ok(nodeJobs.ran.sync >= fixtures.length + 1);
console.log(`PASS spatial kernel parity: ${fixtures.length} fixtures, ${samples} pieces byte-identical to the replaced partition; the main-thread fallback agrees`);

// The real worker module, behind a page-shaped `Worker` (module type, onmessage,
// transfer lists) built on node's worker_threads. A fresh pool instance per case.
{
  const { Worker: ThreadWorker } = await import('node:worker_threads');
  const made = [];
  class PageWorker {
    constructor(url, opts) {
      assert.equal(opts?.type, 'module', 'the pool asks for a module worker');
      const boot = `const { parentPort } = require('node:worker_threads');
        globalThis.self = globalThis;
        globalThis.postMessage = (m, t) => parentPort.postMessage(m, t);
        const queued = [];
        parentPort.on('message', (data) => (globalThis.onmessage ? globalThis.onmessage({ data }) : queued.push(data)));
        import(${JSON.stringify(url.href)}).then(() => { for (const data of queued.splice(0)) globalThis.onmessage({ data }); },
          (e) => parentPort.postMessage({ bootError: String(e) }));`;
      this.thread = new ThreadWorker(boot, { eval: true });
      this.thread.unref();
      this.thread.on('message', (data) => (data?.bootError
        ? this.onerror?.({ message: data.bootError, preventDefault() {} })
        : this.onmessage?.({ data })));
      made.push(this);
    }
    postMessage(m, transfer) { this.thread.postMessage(m, transfer); }
    terminate() { this.thread.terminate(); }
  }
  globalThis.Worker = PageWorker;
  const pooledSource = source.replace("from 'three'", `from '${threeURL}'`)
    .replace("from './jobs/pool.js'", `from '${jobsURL}pool.js?workers'`).replaceAll("from './jobs/", `from '${jobsURL}`)
    .replace("from './batch-coalesce.js'", `from '${pathToFileURL(path.join(web, 'js/batch-coalesce.js')).href}'`);
  const pooled = await import('data:text/javascript;base64,' + Buffer.from(pooledSource).toString('base64'));
  const pool = await import(jobsURL + 'pool.js?workers');
  for (const [name, g, cells] of fixtures) {
    assert.deepEqual(bytesOf(await pooled.spatialPiecesAsync(g, cells)), bytesOf(referencePieces(g, cells)),
      `${name}: the worker's pieces are the reference's, byte for byte`);
  }
  assert.equal(pool.jobsState.mode, 'workers');
  assert.equal(pool.jobsState.ran.worker, fixtures.length, 'every fixture was partitioned on a worker');
  assert.ok(pool.jobsState.workers >= 1 && pool.jobsState.workers <= 4);
  // What goes over by transfer is the caller's to lose, and comes back by transfer.
  const sent = new Float32Array([0, 0, 0, 1, 0, 0, 0, 0, 1]);
  const back = await pool.runJob('partitionTriangles', { attributes: [{ name: 'position', array: sent, itemSize: 3 }],
    positionAt: 0, index: null, count: 3, cellM: 40, heightM: Infinity }, { transfer: [sent.buffer] });
  assert.equal(sent.byteLength, 0, 'a transferred input is detached, not copied');
  assert.deepEqual([...back.pieces[0].arrays[0]], [0, 0, 0, 1, 0, 0, 0, 0, 1]);
  await assert.rejects(pool.runJob('noSuchJob', {}), /no job named noSuchJob/);
  for (const w of made) w.terminate();

  // A worker that cannot start: its job is rejected, the caller re-partitions on the
  // main thread from its own source, and every later job stays there.
  class BrokenWorker {
    constructor() { setTimeout(() => this.onerror?.({ message: 'module workers unsupported', preventDefault() {} }), 0); }
    postMessage() {}
    terminate() {}
  }
  globalThis.Worker = BrokenWorker;
  const brokenSource = pooledSource.replaceAll('pool.js?workers', 'pool.js?broken');
  const broken = await import('data:text/javascript;base64,' + Buffer.from(brokenSource).toString('base64'));
  const brokenPool = await import(jobsURL + 'pool.js?broken');
  const [name, g, cells] = fixtures[2];
  assert.deepEqual(bytesOf(await broken.spatialPiecesAsync(g, cells)), bytesOf(referencePieces(g, cells)),
    `${name}: a failed worker costs the caller nothing but time`);
  assert.equal(brokenPool.jobsState.mode, 'main thread');
  assert.match(brokenPool.jobsState.failed[0], /module workers unsupported/);
  assert.deepEqual(bytesOf(await broken.spatialPiecesAsync(g, cells)), bytesOf(referencePieces(g, cells)));
  delete globalThis.Worker;
}
console.log('PASS job pool: the real worker module partitions byte-identically, transfers both ways, rejects an unknown job, and a failed worker falls back to the main thread');

// A Float32/end-line nudge can cross the cell whose plane generated a cut.
// Exercise the shipped clipping/drape functions on a continuous, folded grid.
const streets = await readFile(path.join(web, 'js/streets.js'), 'utf8');
function body(name) {
  const start = streets.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `missing shipped ${name}`);
  const open = streets.indexOf('{', start + streets.slice(start).indexOf(')') + 1);
  let depth = 1, end = open + 1;
  for (; depth && end < streets.length; end++) {
    if (streets[end] === '{') depth++;
    if (streets[end] === '}') depth--;
  }
  return streets.slice(start, end);
}
const drape = Function('const LIFT_M=.022,WET_NUDGE_M=.02,WET_NUDGE_STEPS=12;\n'
  + ['cellAt','ridgeOf','ridgeHeight','clipConvex','halfPlane','ridgeDrape'].map(body).join('\n')
  + '\nreturn {ridgeDrape,ridgeHeight};')();
const field = {
  grid: {originE:0,originN:0,cellM:2.5},
  surfaceHeight: (e) => Math.abs(e-200)*.9,
  inBounds: () => true, isWater: () => false,
};
const laid = drape.ridgeDrape(field, [[199.9,0],[200.1,0],[200.1,2],[199.9,2]],
  () => [0,0], (e,n) => [e+.00003,n]);
assert.ok(laid?.tris.length, 'cut panels were emitted');
for (const [e,n,y] of laid.verts) {
  assert.equal(e,Math.fround(e),'the final end-line position is Float32');
  const drawnY=Math.fround(y)-.022;
  assert.ok(Math.abs(drawnY-field.surfaceHeight(e,n))<1e-5,
    `end-line rounding left the drawn road off its actual cell: ${drawnY-field.surfaceHeight(e,n)}`);
}
console.log('PASS ridge drape: final Float32/end-line positions stand on their actual cell');

// T-2227: equivalent GLTF Texture clones may share a draw only when sampling,
// exact material state and known shader closures agree. Unknown hooks isolate.
{
const T = THREE;
const keySource = await readFile(path.join(web, 'js/batch-material.js'), 'utf8');
const { textureKey, materialKey, captureHooks, registerPatch } = await import(
  'data:text/javascript;base64,' + Buffer.from(keySource.replace("from 'three'",
    `from '${threeURL}'`)).toString('base64'));
let checks = 0;
function check(fn) { fn(); checks++; }
const image = { width: 4, height: 4, data: new Uint8Array(64) };
const texture = new T.Texture(image), clone = texture.clone();
check(() => assert.equal(textureKey(texture), textureKey(clone)));
check(() => assert.notEqual(textureKey(texture), textureKey(new T.Texture(image))));
const uploaded = texture.clone(); uploaded.addEventListener('dispose', () => {});
check(() => assert.equal(textureKey(texture), textureKey(uploaded), 'GPU disposal bookkeeping is not sampler state'));
const circular = texture.clone(); circular.userData.self = circular;
check(() => assert.notEqual(textureKey(texture), textureKey(circular)));
for (const [name, value] of Object.entries({ channel: 1, mapping: T.CubeReflectionMapping,
  wrapS: T.RepeatWrapping, wrapT: T.MirroredRepeatWrapping, magFilter: T.NearestFilter,
  minFilter: T.NearestFilter, anisotropy: 4, format: T.RGFormat, internalFormat: 'RGBA8',
  type: T.FloatType, rotation: .2, generateMipmaps: false, premultiplyAlpha: true,
  flipY: false, unpackAlignment: 1, colorSpace: T.SRGBColorSpace, normalized: true })) {
  const different = texture.clone(); different[name] = value;
  check(() => assert.notEqual(textureKey(texture), textureKey(different), name));
}
for (const field of ['offset', 'repeat', 'center']) {
  const different = texture.clone(); different[field].x += .25;
  check(() => assert.notEqual(textureKey(texture), textureKey(different), field));
}
const manual = texture.clone(); manual.matrixAutoUpdate = false; manual.matrix.elements[6] = .1;
check(() => assert.notEqual(textureKey(texture), textureKey(manual)));
const moved = texture.clone(); moved.offset.x = .4;
const beforeMatrix = moved.matrix.toArray(); textureKey(moved);
check(() => assert.deepEqual(moved.matrix.toArray(), beforeMatrix));
const a = new T.MeshStandardMaterial({ map: texture, normalMap: texture });
const b = a.clone(); b.map = clone; b.normalMap = clone;
check(() => assert.equal(materialKey(a), materialKey(b)));
b.color.setRGB(.11, .22, .33); b.roughness = .2;
check(() => assert.equal(materialKey(a), materialKey(b)));
for (const [field, value] of Object.entries({ opacity: .4, transparent: true, metalness: .2,
  emissiveIntensity: .4, aoMapIntensity: .2, normalMapType: T.ObjectSpaceNormalMap,
  depthWrite: false, depthTest: false, colorWrite: false, stencilWrite: true, stencilRef: 4,
  alphaHash: true, alphaTest: .3, side: T.DoubleSide, shadowSide: T.BackSide,
  premultipliedAlpha: true, polygonOffset: true, polygonOffsetUnits: 3,
  clipIntersection: true, clipShadows: true, toneMapped: false })) {
  const different = a.clone(); different[field] = value;
  check(() => assert.notEqual(materialKey(a), materialKey(different), field));
}
const normal = a.clone(); normal.normalScale.set(.2, .9);
check(() => assert.notEqual(materialKey(a), materialKey(normal)));
const clipping = a.clone(); clipping.clippingPlanes = [new T.Plane(new T.Vector3(1, 0, 0), .2)];
check(() => assert.notEqual(materialKey(a), materialKey(clipping)));
const mapped = a.clone(); mapped.roughnessMap = texture;
const mappedDifferent = mapped.clone(); mappedDifferent.roughness -= .1;
check(() => assert.notEqual(materialKey(mapped), materialKey(mappedDifferent)));
const c1 = a.clone(), c2 = a.clone(); c1.emissive.setRGB(.100000001, 0, 0); c2.emissive.setRGB(.100000002, 0, 0);
check(() => assert.notEqual(materialKey(c1), materialKey(c2)));
function patched(value) {
  const m = a.clone(), prior = captureHooks(m);
  m.onBeforeCompile = shader => { shader.uniforms.testValue = { value }; };
  registerPatch(m, prior, 'test-patch', { value }); return m;
}
check(() => assert.equal(materialKey(patched(2)), materialKey(patched(2))));
check(() => assert.notEqual(materialKey(patched(2)), materialKey(patched(3))));
const unknown1 = a.clone(), unknown2 = a.clone();
unknown1.onBeforeCompile = () => {}; unknown2.onBeforeCompile = () => {};
check(() => assert.notEqual(materialKey(unknown1), materialKey(unknown2)));
unknown2.onBeforeCompile = unknown1.onBeforeCompile;
check(() => assert.notEqual(materialKey(unknown1), materialKey(unknown2)));
const replaced = patched(2); replaced.onBeforeCompile = () => {};
check(() => assert.notEqual(materialKey(patched(2)), materialKey(replaced)));
const physical = new T.MeshPhysicalMaterial({ clearcoat: .3, transmission: .4 });
const physicalOther = physical.clone(); physicalOther.clearcoat = .31;
check(() => assert.notEqual(materialKey(physical), materialKey(physicalOther)));
const snapshot = a.toJSON(); materialKey(a);
check(() => assert.deepEqual(a.toJSON(), snapshot));
console.log(`PASS: ${checks} inspection material/sampler isolation checks; published pixels remain the browser gate.`);
}

// T-2227: projected opaque backing must fail open at holes, near planes,
// changed transforms and evidence modes; the real Three draw list/picks survive.
{
const text = await readFile(path.join(web, 'js/view-occlusion.js'), 'utf8');
const { backingTriangles, projectOccluders, boxOccluded, createViewOcclusion } = await import(
  'data:text/javascript;base64,'+Buffer.from(text.replace("from 'three'",`from '${threeURL}'`)).toString('base64'));
const camera=new THREE.PerspectiveCamera(90,1,.1,100);camera.updateMatrixWorld();
const vp=new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
const wall=new THREE.BufferGeometry();wall.setAttribute('position',new THREE.Float32BufferAttribute([-10,-10,-5,10,-10,-5,0,10,-5],3));
const backing=backingTriangles(wall,new THREE.Matrix4());
assert.equal(backing.length,1);
const projected=projectOccluders(backing,camera,800,800);
assert.equal(projected.length,1);
const outside=backing.map(t=>({...t,points:t.points.map(p=>p.clone().multiplyScalar(2).add(new THREE.Vector3(100,0,0)))}));
assert.equal(projectOccluders(outside,camera,800,800).length,0,'off-screen area cannot consume candidate slots');
assert.equal(projectOccluders([...Array(70).fill(outside[0]),...backing],camera,800,800).length,1,
  'visible backing survives more than 64 larger off-screen triangles');
const box=(a,b)=>new THREE.Box3(new THREE.Vector3(...a),new THREE.Vector3(...b));
assert.ok(boxOccluded(box([-.2,-1.2,-10.2],[.2,-.8,-9.8]),vp,projected,800,800));
const wide=backing.map(t=>({...t,points:t.points.map(p=>new THREE.Vector3(p.x*10,p.y*10,p.z))}));
assert.equal(boxOccluded(box([9.8,-1.2,-10.2],[10.2,-.8,-9.8]),vp,
  projectOccluders(wide,camera,800,800),800,800),false,
  'viewport-crossing boxes fail open even behind a fully covering face');
const slanted=wall.clone();
const slope=slanted.attributes.position;
for(let i=0;i<slope.count;i++)slope.setZ(i,-7-.5*slope.getX(i));
const sloped=projectOccluders(backingTriangles(slanted,new THREE.Matrix4()),camera,800,800);
assert.ok(boxOccluded(box([-.2,-1.2,-9.2],[.2,-.8,-8.8]),vp,sloped,800,800),
  'actual wall plane accepts a box behind the near part of an angled wall');
assert.equal(boxOccluded(box([-.2,-1.2,-7.2],[.2,-.8,-6.8]),vp,sloped,800,800),false,
  'a box crossing the slanted plane is retained');
slanted.dispose();
for(const bounds of [box([-.2,-.2,-3],[.2,.2,-2]),box([-.2,-.2,-6],[.2,.2,-4]),
  box([-.2,-.2,-5.01],[.2,.2,-5.001]),box([-20,-2,-11],[20,2,-9]),
  box([-.1,-.1,-1],[.1,.1,1]),box([9,-.1,-10],[10,.1,-9]),
  box([9000,0,-10],[9001,1,-9])]) assert.equal(boxOccluded(bounds,vp,projected,800,800),false);
const crossing=backing.map(t=>({...t,points:[t.points[0],t.points[1],new THREE.Vector3(0,10,.01)]}));
assert.equal(projectOccluders(crossing,camera,800,800).length,1,
  'near-plane clipping keeps only the visible convex part of a real triangle');
assert.equal(boxOccluded(box([-.1,-.1,-1],[.1,.1,1]),vp,
  projectOccluders(crossing,camera,800,800),800,800),false,
  'clipping the occluder never permits a target box crossing the eye plane');
const back=backing.map(t=>({...t,side:THREE.BackSide}));
assert.equal(projectOccluders(back,camera,800,800).length,0);
const shadow=new THREE.OrthographicCamera(-15,15,15,-15,.1,100);shadow.updateMatrixWorld();
assert.equal(projectOccluders(backing,shadow,800,800).length,0);
// Two triangles with a gap may not be treated as one filled bounding rectangle.
const split=new THREE.BufferGeometry();split.setAttribute('position',new THREE.Float32BufferAttribute([
 -10,-10,-5,-.1,-10,-5,-.1,10,-5, .1,-10,-5,10,-10,-5,.1,10,-5],3));
assert.equal(boxOccluded(box([-.1,-.1,-10],[.1,.1,-9]),vp,
  projectOccluders(backingTriangles(split,new THREE.Matrix4()),camera,800,800),800,800),false);
const material=new THREE.MeshStandardMaterial({side:THREE.DoubleSide});
const cube=new THREE.BoxGeometry(.3,.3,.3);
const batch=new THREE.BatchedMesh(3,cube.attributes.position.count,cube.index.count,material);
const geometry=batch.addGeometry(cube);
for(const pos of [[0,-1,-10],[9,7,-12],[7,7,-8]])batch.setMatrixAt(batch.addInstance(geometry),new THREE.Matrix4().makeTranslation(...pos));
batch.sortObjects=false;batch.updateMatrixWorld();
const originalPositions=batch.geometry.attributes.position.array.slice();
let allowed=true,wallVisible=true;
backing[0].active=()=>wallVisible;
const renderer={info:{render:{frame:0}},getDrawingBufferSize:size=>size.set(800,800)};
const cull=createViewOcclusion({camera,renderer,triangles:backing,batches:[batch],allow:()=>allowed});
const draw=cam=>{renderer.info.render.frame++;batch.onBeforeRender(renderer,null,cam,batch.geometry,material);return batch._multiDrawCount;};
assert.equal(draw(camera),2);
assert.deepEqual([...batch._indirectTexture.image.data.slice(0,2)],[1,2],'ground insertion order survives filtering');
assert.equal(batch.getVisibleAt(0),true,'draw omission never changes pick visibility');
const ray=new THREE.Raycaster(new THREE.Vector3(0,-1,0),new THREE.Vector3(0,0,-1));
assert.ok(ray.intersectObject(batch).some(h=>h.batchId===0),'occluded geometry is still raycastable');
assert.equal(draw(shadow),3,'sun shadow retains every instance');
assert.equal(draw(camera),2,'shadow pass does not poison the next main draw');
material.polygonOffset=true;
assert.equal(draw(camera),3,'a depth-biased raster is not bounded by its geometry');
material.polygonOffset=false;
renderer.clippingPlanes=[new THREE.Plane(new THREE.Vector3(1,0,0),0)];
assert.equal(draw(camera),3,'global clipping can open a backing and fails open');
renderer.clippingPlanes=[];
allowed=false;assert.equal(draw(camera),3,'confidence/hidden-level modes fail open');
allowed=true;wallVisible=false;assert.equal(draw(camera),3,'a hidden backing cannot occlude');
wallVisible=true;assert.equal(draw(camera),2,'restored backing restores rejection');
cull.setEnabled(false);assert.equal(draw(camera),3);
cull.setEnabled(true);assert.equal(draw(camera),2);
batch.setMatrixAt(0,new THREE.Matrix4().makeTranslation(0,-1,-3));
assert.equal(draw(camera),3,'an instance moved in front of the wall reappears immediately');
assert.deepEqual(batch.geometry.attributes.position.array,originalPositions);
cull.dispose();assert.equal(batch.customSort,null);assert.equal(batch.sortObjects,false);
assert.equal(draw(camera),3,'disposing restores original drawing');
batch.dispose();cube.dispose();wall.dispose();split.dispose();material.dispose();
console.log('PASS opaque backing: conservative bounds, holes, near/depth edges, shadow isolation, evidence/visibility bypass, current transforms, exact geometry, picking and reversible lifetime');
}

// T-3152: a flat backing's proven cover hides a box only where its own triangles leave
// no gap — across a T-junction seam, never through an opening or a crack.
{
const text = await readFile(path.join(web, 'js/view-occlusion.js'), 'utf8');
const { planeOccluded, boxInView, createViewOcclusion } = await import(
  'data:text/javascript;base64,'+Buffer.from(text.replace("from 'three'",`from '${threeURL}'`)).toString('base64'));
const { planarCoverPlanes, boundarySegments } = await import(pathToFileURL(path.join(web, 'js/planar-occluders.js')).href);
// z = -5, 20 m square, a 2 m opening at x 2..4, y 2..4: four rectangles, so the left one's
// right edge meets the top and bottom ones' vertices (T-junctions) either side of the hole.
const rect=(x0,y0,x1,y1)=>[x0,y0,-5,x1,y0,-5,x1,y1,-5, x0,y0,-5,x1,y1,-5,x0,y1,-5];
const wallOf=(gap=0)=>[...rect(-10,-10,2,10),...rect(2+gap,-10,4,2),...rect(2+gap,4,4,10),...rect(4,-10,10,10)];
const worldPlane=(c)=>({...c,o:new THREE.Vector3(...c.normal.map(x=>x*c.d)),n:new THREE.Vector3(...c.normal),
  u:new THREE.Vector3(...c.u),v:new THREE.Vector3(...c.v),active:()=>true});
const [plane]=planarCoverPlanes(wallOf(),null).map(worldPlane);
assert.ok(plane && plane.cells>30000,'the wall is one plane with its cells proven');
assert.equal(planarCoverPlanes(wallOf(),null,{minPlaneArea:500}).length,0,'a small plane is not a cover');
const eye=new THREE.Vector3(),forward=new THREE.Vector3(0,0,-1),px=2/800;
const box=(a,b)=>new THREE.Box3(new THREE.Vector3(...a),new THREE.Vector3(...b));
const seam=box([3.8,-1.2,-10.2],[4.2,-.8,-9.8]);   // its shadow straddles x = 2 below the opening
assert.ok(planeOccluded(seam,eye,forward,.1,px,plane),'a T-junction seam covered on both sides hides');
assert.equal(planeOccluded(box([5.6,5.6,-10.2],[6.4,6.4,-9.8]),eye,forward,.1,px,plane),false,'seen through the opening');
assert.equal(planeOccluded(box([3.6,3.6,-10.2],[4.4,4.4,-9.8]),eye,forward,.1,px,plane),false,'its shadow overlaps the opening');
assert.equal(planeOccluded(box([-1,-1,-4],[1,1,-3]),eye,forward,.1,px,plane),false,'in front of the wall');
assert.equal(planeOccluded(box([-1,-1,-6],[1,1,-4.99]),eye,forward,.1,px,plane),false,'crossing the wall');
assert.equal(planeOccluded(box([-1,-1,-5.019],[1,1,-5.0101]),eye,forward,.1,px,plane),false,'inside the 2 cm depth gap');
assert.equal(planeOccluded(box([30,-1,-10.2],[30.4,-.8,-9.8]),eye,forward,.1,px,plane),false,'its shadow leaves the wall');
assert.equal(planeOccluded(seam,eye,forward,6,px,plane),false,'the cover is nearer than the near plane, so not drawn');
assert.equal(planeOccluded(box([-1,-1,-40],[1,1,-39]),new THREE.Vector3(0,0,-4.9),forward,.1,px,plane),false,'a grazing look is refused');
const [cracked]=planarCoverPlanes(wallOf(.01),null).map(worldPlane);
assert.equal(planeOccluded(seam,eye,forward,.1,px,cracked),false,'a 1 cm crack along the seam is an opening');
const [hairline]=planarCoverPlanes(wallOf(.001),null).map(worldPlane);
assert.ok(planeOccluded(seam,eye,forward,.1,px,hairline),'under the 2 mm seam tolerance a T-junction vertex is on its line');
// Two triangles sharing an edge from opposite sides leave it interior; one alone is outline.
const a=[0,0],b=[1,0],up=[.5,1],down=[.5,-1];
assert.equal(boundarySegments([[a,b,up],[b,a,down]]).length,0);
assert.equal(boundarySegments([[a,b,up],[b,a,up]]).length,1,'a fold, both on one side, is outline');
const camera=new THREE.PerspectiveCamera(90,1,.1,100);camera.updateMatrixWorld();
const vp=new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
assert.ok(boxInView(seam,vp,800,800));
assert.equal(boxInView(box([9,-1,-10],[11,1,-9]),vp,800,800),false,'a box crossing the viewport edge fails open');
const material=new THREE.MeshStandardMaterial({side:THREE.DoubleSide});
const cube=new THREE.BoxGeometry(.3,.3,.3);
const batch=new THREE.BatchedMesh(2,cube.attributes.position.count,cube.index.count,material);
const geometry=batch.addGeometry(cube);
for(const pos of [[4,-1,-10],[6,6,-10]])batch.setMatrixAt(batch.addInstance(geometry),new THREE.Matrix4().makeTranslation(...pos));
batch.sortObjects=false;batch.updateMatrixWorld();
let standing=true;plane.active=()=>standing;
const renderer={info:{render:{frame:0}},getDrawingBufferSize:size=>size.set(800,800)};
const cull=createViewOcclusion({camera,renderer,triangles:[],planes:[plane],batches:[batch]});
const draw=cam=>{renderer.info.render.frame++;batch.onBeforeRender(renderer,null,cam,batch.geometry,material);return batch._multiDrawCount;};
assert.equal(draw(camera),1,'the box behind the wall is left out; the one behind the opening stays');
assert.equal(cull.stats.planeCulled,1);
const shadow=new THREE.OrthographicCamera(-15,15,15,-15,.1,100);shadow.updateMatrixWorld();
assert.equal(draw(shadow),2,'the sun keeps both');
standing=false;assert.equal(draw(camera),2,'a cover that is not standing hides nothing');
standing=true;assert.equal(draw(camera),1);
cull.dispose();batch.dispose();cube.dispose();material.dispose();
console.log('PASS planar covers: T-junction seams hide, openings, cracks, near, depth and grazing fail open, sun and standing isolated');
}

{
const source=await readFile(path.join(web,'js/confidence.js'),'utf8');
const {opaqueConfidenceRange}=await import('data:text/javascript;base64,'+
  Buffer.from(source.replace("from 'three'",`from '${threeURL}'`)).toString('base64'));
const view={enabled:false,hidden:{attested:false,inferred:false,reconstructed:false}};
assert.ok(opaqueConfidenceRange([0,1],view));
view.enabled=true;
assert.ok(opaqueConfidenceRange([0,.5],view),'evidence tint preserves opaque backing');
assert.equal(opaqueConfidenceRange([0,.8],view),false,'dithered evidence cannot hide geometry');
view.hidden.reconstructed=true;
assert.ok(opaqueConfidenceRange([0,.5],view),'hiding a different tier preserves opaque backing');
view.hidden.inferred=true;
assert.equal(opaqueConfidenceRange([0,.5],view),false,'a partially hidden triangle fails open');
assert.ok(opaqueConfidenceRange([0,.249],view));
assert.equal(opaqueConfidenceRange([0,.25],view),false,'hidden band boundary is inclusive');
for(const range of [null,[NaN,.5],[0,Infinity],[.5,0],[-.1,0],[0,1.1]])
  assert.equal(opaqueConfidenceRange(range,view),false);
console.log('PASS opaque evidence ranges: tint, dither, hidden bands, interpolation and unknown values');
}

{
const text=await readFile(path.join(web,'js/season.js'),'utf8');
const {patchSeason,seasonPreservesSurface}=await import('data:text/javascript;base64,'+
  Buffer.from(text.replace("from 'three'",`from '${threeURL}'`)).toString('base64'));
const m=new THREE.MeshStandardMaterial(),hooks=()=>[m.onBeforeCompile,m.onBeforeRender,m.customProgramCacheKey];
const before=hooks();assert.equal(seasonPreservesSurface(m,before),false);
assert.ok(patchSeason(m));assert.ok(seasonPreservesSurface(m,before));
assert.equal(patchSeason(m),false);assert.ok(seasonPreservesSurface(m,before));
assert.equal(seasonPreservesSurface(m,[()=>{},...before.slice(1)]),false);
for(const name of ['onBeforeCompile','onBeforeRender','customProgramCacheKey']) {
  const saved=m[name];m[name]=()=>{};
  assert.equal(seasonPreservesSurface(m,before),false,'unknown '+name+' mutation fails open');m[name]=saved;
}
assert.ok(seasonPreservesSurface(m,before));m.dispose();
console.log('PASS season surface proof: only the exact color-only wrapper preserves captured hooks');
}
