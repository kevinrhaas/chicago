/**
 * T-3731 — a structure batch's cull, read off bounds cached once and asked a ground
 * cell at a time, makes exactly the multi-draw three's own per-instance cull makes.
 *
 *   node tools/test_batch_cull_index.mjs
 *
 * Built on the real three.js BatchedMesh (no WebGL: the multi-draw list is made in
 * `onBeforeRender`). A town of a few thousand pieces in small clusters, some rotated and
 * scaled, a few spheres too big to pool, some hidden; then for hundreds of cameras —
 * perspective on foot and aloft, and orthographic as the sun's — every list three makes
 * alone is compared with the cached path's, entry by entry (start, count, instance) in
 * draw order, opaque and blended. And shadow-casters.js's swept-capsule ruling, piece by
 * piece against cell by cell. Then the cache's own keys: a written matrix, an added
 * instance, the bounds compaction, and a custom sort handed back to three.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendor = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(vendor);
// The real modules, their browser import map resolved for Node.
const asData = (text) => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64');
const read = (name, swaps = {}) => {
  let text = fs.readFileSync(path.join(web, 'js', name), 'utf8').replaceAll("from 'three'", `from ${JSON.stringify(vendor)}`);
  for (const [a, b] of Object.entries(swaps)) text = text.replaceAll(`'${a}'`, JSON.stringify(b));
  return asData(text);
};
const cullUrl = read('batch-cull-index.js');
const cull = await import(cullUrl);
const { castOnlyTowardView } = await import(read('shadow-casters.js', { './batch-cull-index.js': cullUrl }));
const { compactBatchBounds } = await import(read('batch-bounds.js'));

let seed = 3731;
const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2 ** 32; };
const between = (a, b) => a + (b - a) * rand();

function town({ transparent = false, count = 2400 } = {}) {
  const geos = [];
  for (let k = 0; k < 24; k += 1) {
    const g = new THREE.BoxGeometry(between(0.2, 6), between(0.2, 9), between(0.2, 6));
    g.translate(between(-2, 2), between(0, 4), between(-2, 2));
    geos.push(g);
  }
  // A couple of long pieces, bigger than a cell: tested on their own.
  geos.push(new THREE.BoxGeometry(80, 2, 3), new THREE.BoxGeometry(3, 40, 60));
  const verts = geos.reduce((s, g) => s + g.attributes.position.count, 0);
  const idx = geos.reduce((s, g) => s + g.index.count, 0);
  const batch = new THREE.BatchedMesh(count + 8, verts, idx,
    new THREE.MeshStandardMaterial({ transparent }));
  const ids = geos.map((g) => batch.addGeometry(g));
  batch.userData.batchIndex = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3();
  for (let i = 0; i < count; i += 1) {
    // houses in blocks along streets, as a town is
    const block = Math.floor(i / 25);
    const bx = (block % 12) * 60 - 360, bz = Math.floor(block / 12) * 70 - 280;
    p.set(bx + between(-25, 25), between(-1, 1), bz + between(-28, 28));
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), rand() < 0.5 ? 0 : between(0, Math.PI * 2));
    const k = rand() < 0.3 ? between(0.5, 2) : 1;
    s.set(k, k, k);
    const id = batch.addInstance(ids[i % 97 === 0 ? 24 + (i % 2) : Math.floor(rand() * 24)]);
    batch.setMatrixAt(id, m.compose(p, q, s));
    batch.userData.batchIndex[id] = `s${block}`;
    if (rand() < 0.08) batch.setVisibleAt(id, false);
  }
  batch.updateMatrixWorld(true);
  // Every geometry's sphere made first, as the town's first frame makes them: three's
  // lazy sphere uses the scratch vector its sort holds the camera in, so the one frame
  // that computes a sphere sorts by a clobbered depth (three's quirk, not the cache's).
  for (const id of ids) batch.getBoundingSphereAt(id, new THREE.Sphere());
  return batch;
}

function cameras(n) {
  const out = [];
  for (let k = 0; k < n; k += 1) {
    let cam;
    if (k % 4 === 3) {
      // the sun's box
      const h = between(40, 160);
      cam = new THREE.OrthographicCamera(-h, h, h, -h, 0.5, between(300, 900));
      cam.position.set(between(-300, 300), between(150, 400), between(-300, 300));
      cam.lookAt(cam.position.x + between(-100, 100), 0, cam.position.z + between(-100, 100));
    } else {
      cam = new THREE.PerspectiveCamera(between(40, 75), between(0.4, 2), 0.1, between(200, 2000));
      const aloft = k % 4 === 2;
      cam.position.set(between(-400, 400), aloft ? between(30, 200) : 1.6, between(-320, 320));
      const yaw = between(0, Math.PI * 2), pitch = aloft ? between(-1.2, -0.2) : between(-0.2, 0.2);
      cam.lookAt(cam.position.x + Math.sin(yaw), cam.position.y + Math.sin(pitch), cam.position.z + Math.cos(yaw));
    }
    cam.updateMatrixWorld(true);
    cam.updateProjectionMatrix();
    out.push(cam);
  }
  return out;
}

/** The multi-draw, in draw order. */
function list(batch) {
  const out = [];
  const d = batch._indirectTexture.image.data;
  for (let k = 0; k < batch._multiDrawCount; k += 1) out.push(`${batch._multiDrawStarts[k]}/${batch._multiDrawCounts[k]}/${d[k]}`);
  return out;
}

const native = THREE.BatchedMesh.prototype.onBeforeRender;
function both(batch, camera, material = batch.material) {
  native.call(batch, null, {}, camera, batch.geometry, material);
  const want = list(batch);
  cull.fastPrepare.call(batch, null, {}, camera, batch.geometry, material);
  const got = list(batch);
  return { want, got };
}

const cams = cameras(400);
let drawn = 0, culled = 0;
for (const transparent of [false, true]) {
  const batch = town({ transparent });
  for (const cam of cams) {
    const { want, got } = both(batch, cam);
    assert.deepEqual(got, want, `${transparent ? 'blended' : 'opaque'} list differs from three's`);
    drawn += want.length; culled += batch._instanceInfo.length - want.length;
  }
  // and under a moved batch frame
  batch.position.set(17, 0, -9); batch.rotation.y = 0.4; batch.updateMatrixWorld(true);
  for (const cam of cams.slice(0, 60)) {
    const { want, got } = both(batch, cam);
    assert.deepEqual(got, want, 'list differs under a moved batch');
  }
}
assert.ok(drawn > 10_000 && culled > 10_000, `cameras both keep and cull (${drawn} drawn, ${culled} culled)`);
console.log(`ok  ${cams.length} cameras, opaque and blended: every list three's, entry for entry (${drawn} drawn, ${culled} culled)`);

{
  // the cells were asked: most instances were never tested one by one
  const batch = town();
  const c = cull.cullIndexOf(batch);
  assert.ok(c.cellCount > 20 && c.loose.length > 0, 'pooled into cells, with the big pieces loose');
  let decided = 0, total = 0;
  const f = new THREE.Frustum();
  for (const cam of cams) {
    f.setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    for (let g = 0; g < c.cellCount; g += 1) {
      const n = c.start[g + 1] - c.start[g];
      total += n;
      if (cull.cellSide(f.planes, c.box, g * 6) !== 0) decided += n;
    }
  }
  assert.ok(decided / total > 0.6, `cells decide most instances untested (${(100 * decided / total).toFixed(0)}%)`);
  console.log(`ok  cells rule on ${(100 * decided / total).toFixed(0)}% of instances without testing them`);
}

{
  // the cache follows the batch: a written matrix, an added instance, compacted bounds
  const batch = town({ count: 600 });
  const cam = cams[0];
  for (let k = 0; k < 40; k += 1) batch.setMatrixAt(k, new THREE.Matrix4().makeTranslation(cam.position.x, 0, cam.position.z - 20));
  let { want, got } = both(batch, cam);
  assert.deepEqual(got, want, 'a written matrix is followed');
  batch.addInstance(0);
  batch.setMatrixAt(batch._instanceInfo.length - 1, new THREE.Matrix4().makeTranslation(cam.position.x, 0, cam.position.z - 10));
  ({ want, got } = both(batch, cam));
  assert.deepEqual(got, want, 'an added instance is followed');
  for (const c2 of cams.slice(0, 20)) native.call(batch, null, {}, c2, batch.geometry, batch.material);
  compactBatchBounds(batch);
  for (const c2 of cams.slice(0, 80)) {
    ({ want, got } = both(batch, c2));
    assert.deepEqual(got, want, 'compacted bounds are followed');
  }
  // a custom sort is three's to run
  batch.setCustomSort(function (l) { l.sort((a, b) => a.index - b.index); });
  ({ want, got } = both(batch, cam));
  assert.deepEqual(got, want, 'a custom sort is handed back to three');
  console.log('ok  the cache follows written matrices, added instances and compacted bounds; a custom sort stays three\'s');
}

{
  // shadow-casters.js: the cell ruling hides exactly the pieces the per-piece loop hides
  const readBatch = town();
  readBatch.customDepthMaterial = new THREE.MeshDepthMaterial();
  const sun = new THREE.Vector3();
  let compared = 0, hiddenTotal = 0;
  for (const cam of cams.filter((_, k) => k % 4 !== 3).slice(0, 120)) {
    sun.set(between(-1, 1), between(0.08, 1), between(-1, 1)).normalize();
    const shadowCam = cams[3];
    const read = (on) => {
      cull.fastCull.on = on;
      const batch = readBatch;
      const state = { on: true, sun: () => sun };
      batch.onBeforeShadow = THREE.BatchedMesh.prototype.onBeforeShadow;
      castOnlyTowardView(batch, state);
      batch.onBeforeShadow(null, batch, cam, shadowCam, batch.geometry, batch.customDepthMaterial);
      return { culled: state.culled, drawn: list(batch) };
    };
    const off = read(false), on = read(true);
    cull.fastCull.on = true;
    assert.equal(on.culled, off.culled, 'the same pieces left out of the sun');
    assert.deepEqual(on.drawn, off.drawn, 'the same sun list');
    compared += 1; hiddenTotal += off.culled;
  }
  assert.ok(hiddenTotal > 1000, `the sweep leaves pieces out (${hiddenTotal})`);
  console.log(`ok  ${compared} views: shadow-casters leaves out the same ${hiddenTotal} pieces cell by cell as piece by piece`);
}
{
  // the sort: three's stable comparator sort, on depths with ties, signed zeros and negatives
  for (const k of [0, 1, 2, 5, 47, 48, 49, 300, 5000]) {
    for (const descending of [false, true]) {
      const w = { kept: new Int32Array(k), z: new Float64Array(k), order: new Uint32Array(k), spare: new Uint32Array(k),
        hi: new Uint32Array(k), lo: new Uint32Array(k) };
      const items = [];
      for (let j = 0; j < k; j += 1) {
        const roll = rand();
        const zj = roll < 0.2 ? Math.floor(between(-4, 4)) : roll < 0.25 ? (rand() < 0.5 ? -0 : 0) : between(-900, 900);
        const id = Math.floor(rand() * 3_000_000);
        w.kept[j] = id; w.z[j] = zj; items.push({ id, z: zj });
      }
      const got = [...cull.sortByDepth(w, k, descending)].map((j) => w.kept[j]);
      const want = items.slice().sort((a, b) => a.id - b.id)
        .sort(descending ? (a, b) => b.z - a.z : (a, b) => a.z - b.z).map((x) => x.id);
      assert.deepEqual(got, want, `sort of ${k} (${descending ? 'back to front' : 'front to back'})`);
    }
  }
  console.log('ok  the depth sort is three\'s stable sort, ties and signed zeros included, short lists and long');
}

{
  // T-3728: each pass keeps its own list texture and sends it only when the list changed
  const batch = town({ count: 900 });
  cull.installFastCull(batch);
  const eye = cams[0], sun = cams[3];
  const pass = (cam) => {
    const before = cull.passLists.sent;
    batch.onBeforeRender(null, {}, cam, batch.geometry, batch.material);
    return { sent: cull.passLists.sent - before, texture: batch._indirectTexture, drawn: list(batch) };
  };
  const e1 = pass(eye), s1 = pass(sun), e2 = pass(eye), s2 = pass(sun);
  assert.equal(e1.sent + s1.sent, 2, 'each pass sends its list the first time');
  assert.notEqual(e1.texture, s1.texture, 'the eye and the sun keep a list texture each');
  assert.equal(e2.texture, e1.texture, 'the eye draws with its own texture again');
  assert.equal(e2.sent + s2.sent, 0, 'an unchanged list, eye or sun, is not sent again');
  assert.deepEqual(e2.drawn, e1.drawn, 'the eye list is the same list');
  assert.deepEqual(s2.drawn, s1.drawn, 'the sun list is the same list');
  assert.ok(s1.texture.version > 0 && s1.texture.image.width === e1.texture.image.width
    && s1.texture.format === e1.texture.format && s1.texture.type === e1.texture.type, 'a new pass texture is three\'s kind, and sent');
  // three's own list, made for the eye, is the list the eye texture holds
  native.call(batch, null, {}, eye, batch.geometry, batch.material);
  const want = list(batch);
  assert.deepEqual(pass(eye).drawn, want, 'after three wrote a list, the eye list is still three\'s');
  // a camera that moved sends its new list
  const moved = cams[1];
  pass(moved); const again = pass(moved);
  assert.equal(again.sent, 0, 'a third camera keeps its list too');
  let disposed = 0;
  for (const t of new Set([e1.texture, s1.texture, again.texture])) t.addEventListener('dispose', () => { disposed += 1; });
  batch.dispose();
  assert.equal(disposed, 3, 'every pass texture goes with the batch');
  console.log('ok  each pass keeps its own list texture and sends it only when it changed (T-3728)');
}

console.log('PASS — the cached cull draws what three draws');
