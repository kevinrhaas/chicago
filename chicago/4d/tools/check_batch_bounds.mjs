#!/usr/bin/env node
/**
 * check_batch_bounds.mjs — T-3173: a BatchedMesh's per-geometry bounds kept as
 * float32 figures (renderers/web/js/batch-bounds.js) answer every reader as the
 * Box3 and Sphere they replaced did, never smaller, and only while current.
 *
 *  1. every stored box CONTAINS three's own box and every stored sphere contains
 *     three's own sphere, each within a few float32 steps of it (rounded outward);
 *  2. the objects are gone from `_geometryInfo` (that is the saving), and a
 *     second compaction is a no-op;
 *  3. with the positions then let go, as a phone does (upload-release.js), the
 *     batch still answers both getters and three's per-instance frustum cull
 *     keeps every instance it kept before — nothing re-reads the arrays;
 *  4. `setGeometryAt` drops the row: the new geometry's bounds are three's,
 *     computed off its new positions; a geometry added after compaction is
 *     three's too; past the count both getters answer null, as three's do;
 *  5. the rounding helpers round the way they say, at 0, at negatives and at
 *     values float32 holds exactly.
 *
 * `--self-test` shows the check able to go red: a compaction that rounds to
 * nearest instead of outward must fail check 1 on the same batch.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const SELF_TEST = process.argv.includes('--self-test');
let source = await readFile(path.join(web, 'js/batch-bounds.js'), 'utf8');
if (SELF_TEST) {
  // The broken twin: nearest rounding, and the radius not grown for the centre's move.
  source = source.replace(/= floorF32\(/g, '= Math.fround(').replace(/= ceilF32\(max/g, '= Math.fround(max')
    .replace('ceilF32(radius + Math.hypot(cx - center.x, cy - center.y, cz - center.z))', 'Math.fround(radius)');
}
const { compactBatchBounds, floorF32, ceilF32 } = await import('data:text/javascript;base64,'
  + Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64'));

// A deterministic scatter of small indexed pieces with awkward (non-float32) corners.
let seed = 3173;
const rand = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
function piece() {
  const g = new THREE.BoxGeometry(0.01 + rand() * 0.3, 0.01 + rand() * 0.2, 0.01 + rand() * 0.25);
  const t = [rand() * 1.4 - 0.7, rand() * 1.4 - 0.7, rand() * 1.4 - 0.7].map((v) => v + 1e-9 / 3);
  g.translate(...t);
  g.rotateY(rand() * Math.PI);
  g.deleteAttribute('uv');
  return g;
}

const N = 400;
const geos = Array.from({ length: N }, piece);
const verts = geos.reduce((a, g) => a + g.getAttribute('position').count, 0);
const idx = geos.reduce((a, g) => a + g.getIndex().count, 0);
const batch = new THREE.BatchedMesh(N + 8, verts + 64, idx + 128, new THREE.MeshBasicMaterial());
for (const g of geos) batch.setMatrixAt(batch.addInstance(batch.addGeometry(g)), new THREE.Matrix4()
  .makeTranslation(rand() * 40 - 20, 0, rand() * 40 - 20).multiply(new THREE.Matrix4().makeScale(12, 12, 12)));

// three's own figures, as upload-release.js has them computed before the release.
const want = [];
for (let id = 0; id < N; id += 1) {
  want.push({ box: batch.getBoundingBoxAt(id, new THREE.Box3()).clone(),
    sphere: batch.getBoundingSphereAt(id, new THREE.Sphere()).clone() });
}
const ulp = (x) => Math.max(Math.abs(x), 1e-30) * 2 ** -22; // two float32 steps, generously

const rows = compactBatchBounds(batch);
let failures = 0;
const check = (name, fn) => {
  try { fn(); console.log(`ok   ${name}`); } catch (e) { failures += 1; console.log(`FAIL ${name}\n     ${e.message.split('\n')[0]}`); }
};

check('1. every stored box and sphere contains three\'s own, within float32 steps', () => {
  assert.equal(rows, N);
  for (let id = 0; id < N; id += 1) {
    const box = batch.getBoundingBoxAt(id, new THREE.Box3());
    const sph = batch.getBoundingSphereAt(id, new THREE.Sphere());
    const w = want[id];
    for (const k of ['x', 'y', 'z']) {
      assert.ok(box.min[k] <= w.box.min[k], `geometry ${id}: min.${k} ${box.min[k]} above three's ${w.box.min[k]}`);
      assert.ok(box.max[k] >= w.box.max[k], `geometry ${id}: max.${k} ${box.max[k]} below three's ${w.box.max[k]}`);
      assert.ok(w.box.min[k] - box.min[k] <= ulp(w.box.min[k]) && box.max[k] - w.box.max[k] <= ulp(w.box.max[k]),
        `geometry ${id}: box.${k} moved more than a float32 step`);
    }
    // The stored sphere holds three's: |c' - c| + r <= r'.
    const reach = sph.center.distanceTo(w.sphere.center) + w.sphere.radius;
    assert.ok(reach <= sph.radius, `geometry ${id}: sphere ${sph.radius} does not hold three's (needs ${reach})`);
    assert.ok(sph.radius - w.sphere.radius <= 4 * ulp(w.sphere.radius) + 4 * ulp(1), `geometry ${id}: radius grew too far`);
  }
});

check('2. the Box3 and Sphere objects are gone, and a second compaction is a no-op', () => {
  assert.ok(batch._geometryInfo.slice(0, N).every((gi) => gi.boundingBox === null && gi.boundingSphere === null));
  assert.equal(compactBatchBounds(batch), 0);
  assert.equal(batch.userData.compactBounds.rows, N);
  // six float32 a box, four a sphere, one byte of "stored": 41 bytes a geometry
  assert.equal(batch.userData.compactBounds.bytes, batch._geometryInfo.length * (24 + 16 + 1));
});

check('3. with the positions gone, the getters answer and the cull keeps what it kept', () => {
  const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
  cam.position.set(0, 8, 30); cam.lookAt(0, 0, 0); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
  const frustum = new THREE.Frustum().setFromProjectionMatrix(
    new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
  const m = new THREE.Matrix4(); const s = new THREE.Sphere();
  const keptBefore = want.map((w, id) => frustum.intersectsSphere(w.sphere.clone().applyMatrix4(batch.getMatrixAt(id, m))));
  const pos = batch.geometry.getAttribute('position');
  const arr = pos.array; pos.array = null; const ix = batch.geometry.index; const ia = ix.array; ix.array = new ia.constructor(0);
  try {
    for (let id = 0; id < N; id += 1) {
      assert.ok(batch.getBoundingBoxAt(id, new THREE.Box3()));
      const kept = frustum.intersectsSphere(batch.getBoundingSphereAt(id, s).applyMatrix4(batch.getMatrixAt(id, m)));
      if (keptBefore[id]) assert.ok(kept, `instance ${id} culled after compaction`);
    }
    // three's own per-object cull path, which calls the getters through `this`
    const scene = new THREE.Scene(); scene.add(batch);
    batch.perObjectFrustumCulled = true;
    batch.onBeforeRender({ info: { render: {} } }, scene, cam, batch.geometry, batch.material, null);
  } finally { pos.array = arr; ix.array = ia; }
  assert.ok(keptBefore.some(Boolean) && keptBefore.some((k) => !k), 'the camera should see some and miss some');
});

check('4. setGeometryAt drops the row; a later geometry and a stale id are three\'s', () => {
  const g = new THREE.BoxGeometry(0.05, 0.05, 0.05); g.deleteAttribute('uv'); g.translate(0.3, 0.3, 0.3);
  // same size as geometry 0's slot can hold? BoxGeometry pieces are 24 verts / 36 indices each.
  batch.setGeometryAt(0, g);
  const box = batch.getBoundingBoxAt(0, new THREE.Box3());
  assert.ok(Math.abs(box.min.x - 0.275) < 1e-6 && Math.abs(box.max.x - 0.325) < 1e-6, `row 0 still read the old figures: ${box.min.x}`);
  const later = batch.addGeometry(piece());
  assert.ok(batch.getBoundingSphereAt(later, new THREE.Sphere()).radius > 0);
  assert.equal(batch._geometryInfo[later].boundingSphere !== null, true, 'a later geometry caches as three does');
  assert.equal(batch.getBoundingBoxAt(batch._geometryCount + 3, new THREE.Box3()), null);
  assert.equal(batch.getBoundingSphereAt(batch._geometryCount + 3, new THREE.Sphere()), null);
});

check('5. the rounding helpers round outward and keep exact values', () => {
  for (const x of [0, 1, -1, 0.1, -0.1, 1 / 3, -1 / 3, 123456.789, -2.5e-7, 1e-40]) {
    assert.ok(floorF32(x) <= x && ceilF32(x) >= x, `${x}`);
    assert.equal(Math.fround(floorF32(x)), floorF32(x)); assert.equal(Math.fround(ceilF32(x)), ceilF32(x));
  }
  assert.equal(floorF32(0.5), 0.5); assert.equal(ceilF32(-0.5), -0.5); assert.equal(ceilF32(0), 0);
});

// Actual 1904 phone-tier yards: uploaded draw copies may go, while source
// templates, analytic cards, triangle picks, and subsequent rebuilds still work.
if (!SELF_TEST) {
  const { register } = await import('node:module');
  register('data:text/javascript,' + encodeURIComponent(`
    import { readFile } from 'node:fs/promises';
    export async function resolve(s,c,n) {
      if(s==='three') return {url:${JSON.stringify(threeURL)},shortCircuit:true};
      if(s.startsWith('three/addons/')) return {url:${JSON.stringify(new URL('./addons/', threeURL).href)}+s.slice(13),shortCircuit:true};
      return n(s,c);
    }
    export async function load(u,c,n) {
      if(u.startsWith('file:')&&u.endsWith('.js'))
        return {format:'module',source:await readFile(new URL(u),'utf8'),shortCircuit:true};
      return n(u,c);
    }
  `), import.meta.url);
  const { createFrontYards } = await import(pathToFileURL(path.join(web, 'js/front-yards.js')));
  const { releaseAfterUpload, RELEASE_KEEP } = await import(pathToFileURL(path.join(web, 'js/upload-release.js')));
  assert.deepEqual(RELEASE_KEEP['front-yards'], ['position', 'index']);
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async (url) => ({ ok: true, json: async () => JSON.parse(await readFile(new URL(url), 'utf8')) });
  const mats = Object.fromEntries(['woodMat', 'leafMat', 'woodDepth', 'leafDepth', 'woodDistance', 'leafDistance']
    .map((key) => [key, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })]));
  const scratch = [];
  const originalDispose = THREE.BufferGeometry.prototype.dispose;
  THREE.BufferGeometry.prototype.dispose = function () {
    scratch.push({ geometry: this, arrays: Object.values(this.attributes).filter((a) => a.array)
      .map((a) => ({ attr: a, array: a.array, copy: a.array.slice() })) });
    return originalDispose.call(this);
  };
  let yards;
  try {
    const problems = [];
    yards = await createFrontYards({ dataBase: pathToFileURL(path.join(root, 'data') + '/'), sceneId: '1904',
      terrain: { surfaceHeight: () => 1.31 }, detail: 'light', grownMaterials: mats, problems });
    THREE.BufferGeometry.prototype.dispose = originalDispose;
    assert.deepEqual(problems, []);
    assert.ok(yards.stats.plants > 0 && scratch.length > 0);
    const scene = new THREE.Scene(); scene.add(yards.group);
    const lot = yards.records.find((r) => r.shrubs?.some((s) => !(s[7] > 0)));
    const [e, n] = lot.shrubs.find((s) => !(s[7] > 0));
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.set(e, 6, -n + 6); camera.lookAt(e, 2, -n); camera.updateMatrixWorld();
    const ndc = new THREE.Vector2();
    const pickBefore = yards.pickAt(ndc, camera);
    assert.ok(pickBefore, 'actual planting must be picked before release');
    const ray = new THREE.Raycaster(); ray.setFromCamera(ndc, camera);
    const settle = () => { yards.update(0.7, camera); yards.settle(camera); scene.updateMatrixWorld(true); };
    settle();
    const hitsBefore = ray.intersectObject(yards.group, true).map((h) => h.distance);
    assert.ok(hitsBefore.length > 0, 'actual triangles must be raycast before release');
    const live = [];
    yards.group.traverse((o) => { if (o.geometry) live.push(o); });
    const kept = live.flatMap((o) => [o.geometry.attributes.position, o.geometry.index].filter(Boolean))
      .map((a) => ({ attr: a, array: a.array }));
    const first = releaseAfterUpload(scene);
    let releasedBytes = 0;
    for (const o of live) for (const a of Object.values(o.geometry.attributes)) {
      if (a.userData?.uploadReleased) { releasedBytes += a.array.byteLength; a.onUploadCallback(); assert.equal(a.array, null); }
    }
    assert.ok(releasedBytes > 0, 'actual uploaded page arrays must be released');
    for (const { attr, array } of kept) assert.equal(attr.array, array, 'position/index array identity retained');
    for (const { geometry, arrays } of scratch) {
      assert.ok(!geometry.userData.uploadReleased, 'source templates must not be marked');
      for (const { attr, array, copy } of arrays) { assert.equal(attr.array, array); assert.deepEqual(attr.array, copy); }
    }
    assert.equal(releaseAfterUpload(scene).bytes, first.bytes, 'repeated marking is idempotent');
    settle();
    assert.deepEqual(yards.pickAt(ndc, camera), pickBefore, 'analytic pick/card unchanged');
    assert.deepEqual(ray.intersectObject(yards.group, true).map((h) => h.distance), hitsBefore,
      'ordinary raycast must preserve hits with uploaded normal/uv arrays absent');
    const oldBatches = live.filter((o) => o.isBatchedMesh);
    let retired = 0;
    for (const b of oldBatches) b.geometry.addEventListener('dispose', () => { retired += 1; });
    await yards.setSeason('winter');
    assert.equal(retired, oldBatches.length, 'season rebuild disposes each retired batch geometry once');
    await yards.setDetail('balanced');
    settle();
    assert.ok(yards.group.children.some((o) => o.children.some((c) => c.isBatchedMesh)), 'rebuilt actual yard batches exist');
    releaseAfterUpload(scene);
    yards.group.traverse((o) => { for (const a of Object.values(o.geometry?.attributes ?? {}))
      if (a.array && a.userData?.uploadReleased) a.onUploadCallback(); });
    settle();
    assert.ok(yards.pickAt(ndc, camera), 'analytic planting pick survives season/detail rebuild and second upload');
    assert.doesNotThrow(() => ray.intersectObject(yards.group, true));
    const finalBatches = [];
    yards.group.traverse((o) => { if (o.isBatchedMesh) finalBatches.push(o); });
    let disposed = 0;
    for (const b of finalBatches) b.geometry.addEventListener('dispose', () => { disposed += 1; });
    yards.dispose(); yards = null;
    assert.equal(disposed, finalBatches.length, 'final batch geometries disposed once');
    console.log(`ok   6. actual front yards release ${releasedBytes} bytes; picks, templates, rebuild and disposal preserved`);
  } finally {
    THREE.BufferGeometry.prototype.dispose = originalDispose;
    globalThis.fetch = previousFetch;
    yards?.dispose();
    for (const m of Object.values(mats)) m.dispose();
  }
}

if (SELF_TEST) {
  if (failures === 0) { console.log('self-test FAIL: nearest rounding passed check 1'); process.exit(1); }
  console.log(`self-test ok: nearest rounding refused (${failures} check(s) red)`);
  process.exit(0);
}
if (failures) { console.log(`${failures} check(s) failed`); process.exit(1); }
console.log(`batch bounds: ${N} geometries compacted, every reader answered`);
