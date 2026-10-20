/**
 * T-2927 — a structures batch joins the drawn cells of one mesh into one draw, and
 * draws exactly the triangles, with exactly the instance data, it drew before.
 *
 *   node tools/test_batch_coalesce.mjs
 *
 * Built on the real three.js BatchedMesh (no WebGL is needed: the multi-draw list is
 * made in `onBeforeRender`). Two structures, each a mesh cut into cells as
 * buildings.js cuts them; every case compares the list three makes alone with the
 * joined one, triangle by triangle, as (index element, matrix, colour, structure),
 * and for a blended batch in the order they are drawn.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { coalesceRuns, joinRuns } = await import(pathToFileURL(path.join(web, 'js/batch-coalesce.js')).href);

/** A row of `n` unit cells along x, each its own small indexed geometry. */
function cells(n, x0 = 0) {
  const out = [];
  for (let i = 0; i < n; i += 1) {
    const g = new THREE.PlaneGeometry(1, 1);
    g.translate(x0 + i + 0.5, 0, 0);
    out.push(g);
  }
  return out;
}

function build({ colours = null } = {}) {
  const pieces = [...cells(6), ...cells(4, 10)];
  const owners = [...Array(6).fill('a'), ...Array(4).fill('b')];
  const verts = pieces.reduce((s, g) => s + g.attributes.position.count, 0);
  const idx = pieces.reduce((s, g) => s + g.index.count, 0);
  const batch = new THREE.BatchedMesh(pieces.length, verts, idx, new THREE.MeshBasicMaterial());
  batch.userData.batchIndex = [];
  const ma = new THREE.Matrix4().makeTranslation(0, 0, -20);
  const mb = new THREE.Matrix4().makeTranslation(0, 0, -25);
  pieces.forEach((g, i) => {
    const id = batch.addInstance(batch.addGeometry(g));
    batch.setMatrixAt(id, owners[i] === 'a' ? ma : mb);
    batch.setColorAt(id, new THREE.Color(colours?.[i] ?? (owners[i] === 'a' ? 0xaa8866 : 0x6688aa)));
    batch.userData.batchIndex[id] = owners[i];
  });
  batch.updateMatrixWorld(true);
  return batch;
}

const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
camera.position.set(7, 0, 10);
camera.updateMatrixWorld(true);
camera.updateProjectionMatrix();

/** The triangles a list draws, as sorted strings: element, then its instance's data. */
function drawn(batch, sort = true) {
  const out = [];
  const idx = batch.geometry.getIndex();
  const bpe = idx.array.BYTES_PER_ELEMENT;
  const m = batch._matricesTexture.image.data;
  const c = batch._colorsTexture.image.data;
  for (let k = 0; k < batch._multiDrawCount; k += 1) {
    const inst = batch._indirectTexture.image.data[k];
    const data = [...m.slice(inst * 16, inst * 16 + 16), ...c.slice(inst * 4, inst * 4 + 4),
      batch.userData.batchIndex[inst]].join(',');
    const s = batch._multiDrawStarts[k] / bpe;
    for (let e = s; e < s + batch._multiDrawCounts[k]; e += 1) out.push(`${e}|${data}`);
  }
  return sort ? out.sort() : out;
}

function readBoth(setup = () => {}, material = null) {
  const plain = build(); setup(plain);
  plain.onBeforeRender(null, null, camera, plain.geometry, material ?? plain.material);
  const joined = build(); setup(joined);
  const stats = { joined: 0 };
  coalesceRuns(joined, stats);
  joined.onBeforeRender(null, null, camera, joined.geometry, material ?? joined.material);
  return { plain, joined, stats };
}

let failures = 0;
const check = (label, fn) => {
  try { fn(); console.log(`  ok   ${label}`); } catch (e) { failures += 1; console.log(`  FAIL ${label}\n       ${e.message}`); }
};

check('every cell in view: one draw per structure, the same triangles', () => {
  const { plain, joined, stats } = readBoth();
  assert.equal(plain._multiDrawCount, 10);
  assert.equal(joined._multiDrawCount, 2);
  assert.equal(stats.joined, 8);
  assert.deepEqual(drawn(joined), drawn(plain));
});

check('a hidden cell in the middle breaks the run, and stays hidden', () => {
  const { plain, joined } = readBoth((b) => b.setVisibleAt(2, false));
  assert.equal(plain._multiDrawCount, 9);
  assert.equal(joined._multiDrawCount, 3);
  assert.deepEqual(drawn(joined), drawn(plain));
});

check('a cell of another colour is not joined to its neighbours', () => {
  const { plain, joined } = readBoth((b) => b.setColorAt(3, new THREE.Color(0xff0000)));
  assert.equal(joined._multiDrawCount, 4);
  assert.deepEqual(drawn(joined), drawn(plain));
});

check('cells the frustum culls are culled exactly as before', () => {
  const { plain, joined } = readBoth((b) => {
    const m = new THREE.Matrix4().makeTranslation(0, 500, -20);
    for (const i of [4, 5]) b.setMatrixAt(i, m);
  });
  assert.equal(plain._multiDrawCount, 8);
  assert.equal(joined._multiDrawCount, 2);
  assert.deepEqual(drawn(joined), drawn(plain));
});

check('a blended batch draws every triangle in the order it drew it before', () => {
  for (const sorted of [true, false]) {
    const glass = new THREE.MeshBasicMaterial({ transparent: true });
    const { plain, joined } = readBoth((b) => { b.sortObjects = sorted; }, glass);
    assert.deepEqual(drawn(joined, false), drawn(plain, false), `sortObjects ${sorted}`);
    if (!sorted) assert.equal(joined._multiDrawCount, 2, 'kept in instance order, every run joins');
  }
});

check('the sun\'s pass (onBeforeShadow) is joined too', () => {
  const b = build();
  coalesceRuns(b);
  const sun = new THREE.OrthographicCamera(-50, 50, 50, -50, 0.1, 500);
  sun.position.set(5, 100, -20); sun.lookAt(5, 0, -20); sun.updateMatrixWorld(true);
  b.onBeforeShadow(null, b, camera, sun, b.geometry, new THREE.MeshDepthMaterial());
  assert.equal(b._multiDrawCount, 2);
});

check('a colour written after the first frame is seen on the next (the run groups are remade)', () => {
  const { plain, joined } = readBoth();
  for (const b of [plain, joined]) {
    b.setColorAt(3, new THREE.Color(0xff0000));
    b.onBeforeRender(null, null, camera, b.geometry, b.material);
  }
  assert.equal(joined._multiDrawCount, 4);
  assert.deepEqual(drawn(joined), drawn(plain));
});

check('joining again changes nothing, and a second frame joins the same', () => {
  const b = build();
  coalesceRuns(b);
  b.onBeforeRender(null, null, camera, b.geometry, b.material);
  const first = drawn(b);
  assert.equal(joinRuns(b, b.geometry, b.material), 0);
  b.onBeforeRender(null, null, camera, b.geometry, b.material);
  assert.deepEqual(drawn(b), first);
});

// What the join costs a frame, on this machine, at the size of 1904's structures
// (about 25,000 drawn cells): printed, not asserted.
{
  const n = 25000;
  const g = new THREE.PlaneGeometry(1, 1);
  const big = new THREE.BatchedMesh(n, n * 4, n * 6, new THREE.MeshBasicMaterial());
  big.userData.batchIndex = [];
  const gid = [];
  for (let i = 0; i < n; i += 1) gid.push(big.addGeometry(g));
  for (let i = 0; i < n; i += 1) {
    const id = big.addInstance(gid[i]);
    big.setMatrixAt(id, new THREE.Matrix4().makeTranslation(Math.floor(i / 50) % 100, Math.floor(i / 5000), -30));
    big.userData.batchIndex[id] = `s${Math.floor(i / 50)}`;
  }
  big.updateMatrixWorld(true);
  big.onBeforeRender(null, null, camera, big.geometry, big.material);
  const kept = big._multiDrawCount;
  const reps = 100;
  for (let r = 0; r < reps; r += 1) { big.onBeforeRender(null, null, camera, big.geometry, big.material); big._multiDrawCount = kept; }
  const t0 = performance.now();
  for (let r = 0; r < reps; r += 1) {
    big.onBeforeRender(null, null, camera, big.geometry, big.material);
    big._multiDrawCount = kept; // three's list as it left it, before the join
  }
  const three = (performance.now() - t0) / reps;
  coalesceRuns(big);
  for (let r = 0; r < reps; r += 1) big.onBeforeRender(null, null, camera, big.geometry, big.material);
  const t1 = performance.now();
  for (let r = 0; r < reps; r += 1) big.onBeforeRender(null, null, camera, big.geometry, big.material);
  const both = (performance.now() - t1) / reps;
  console.log(`  note ${kept} drawn cells: three's own list ${three.toFixed(2)} ms, with the join ${both.toFixed(2)} ms `
    + `(join ${(both - three).toFixed(2)} ms), ${big._multiDrawCount} draws after`);
}

if (failures) {
  console.log(`\nFAIL: ${failures} batch-coalesce check(s) failed`);
  process.exit(1);
}
console.log('\nOK: the drawn cells of one mesh join into one draw, drawing the same triangles');
