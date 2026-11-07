/**
 * T-3408 — a phone lays a structure bucket over 65,535 vertices as several batches
 * that each index in 16 bits, every piece with its twins, every structure whole where
 * it fits, in the bucket's own order.
 *
 *   node tools/test_short_index.mjs
 *
 * Built on the real three.js BatchedMesh (no WebGL needed): each run is laid into a
 * batch as buildings.js lays it, and the batch's index must be a Uint16Array while
 * the one batch the whole bucket made is a Uint32Array.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { shortIndexRuns, pieceOf, SHORT_INDEX_VERTICES } = await import(pathToFileURL(path.join(web, 'js/short-index.js')).href);

/** A piece of `n` vertices (a strip of triangles), owned by structure `id`. */
function piece(id, n) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(n * 3), 3));
  const index = [];
  for (let i = 0; i + 2 < n; i += 1) index.push(i, i + 1, i + 2);
  g.setIndex(index);
  return { record: { id }, geo: g };
}
const twin = (of, kind, n) => ({ ...piece(of.record.id, n), [kind]: of });
const verts = (run) => run.reduce((s, e) => s + e.geo.getAttribute('position').count, 0);
const lay = (run) => {
  const b = new THREE.BatchedMesh(run.length, verts(run), run.reduce((s, e) => s + e.geo.index.count, 0), new THREE.MeshBasicMaterial());
  const ids = new Map();
  for (const e of run) {
    // A twin is laid after its piece, as buildings.js reads the piece's instance id.
    if (pieceOf(e) !== e) assert.ok(ids.has(pieceOf(e)), 'a twin is laid after its piece, in the same batch');
    ids.set(e, b.addInstance(b.addGeometry(e.geo)));
  }
  return b;
};

// A small bucket stays one batch, the very array.
{
  const entries = [piece('a', 300), piece('b', 400)];
  const runs = shortIndexRuns(entries);
  assert.equal(runs.length, 1);
  assert.equal(runs[0], entries);
}

// A town-sized bucket: houses of several pieces, relief, shadow and colour twins
// appended as buildings.js appends them (crest twin after its piece; shadow then
// colour twins after every piece), one house larger than a batch, one piece too.
const entries = [];
const pieces = [];
const sizes = { a: [9000, 8000, 7000], b: [20000, 15000], c: [30000, 30000, 20000], d: [12000],
  big: [40000, 40000], huge: [70000], e: [500, 600, 700], f: [25000] };
for (const [id, list] of Object.entries(sizes)) {
  for (const n of list) {
    const p = piece(id, n);
    pieces.push(p);
    entries.push(p);
    if (id === 'b') entries.push(twin(p, 'twinOf', 300));
  }
}
for (const p of pieces) if (p.record.id !== 'e') entries.push(twin(p, 'shadowOf', 200));
for (const p of pieces) if (p.record.id !== 'd') entries.push(twin(p, 'colourOf', 400));
const whole = lay(entries);
assert.ok(whole.geometry.index.array instanceof Uint32Array, 'the whole bucket indexes in 32 bits');

const runs = shortIndexRuns(entries);
assert.ok(runs.length > 1);
// Every entry exactly once, and the order kept inside each run.
assert.equal(runs.flat().length, entries.length);
assert.equal(new Set(runs.flat()).size, entries.length);
const at = new Map(entries.map((e, i) => [e, i]));
for (const run of runs) for (let i = 1; i < run.length; i += 1) assert.ok(at.get(run[i - 1]) < at.get(run[i]), 'bucket order kept');
// Every twin in its piece's run.
const runOf = new Map();
runs.forEach((run, r) => run.forEach((e) => runOf.set(e, r)));
for (const e of entries) assert.equal(runOf.get(e), runOf.get(pieceOf(e)), 'a twin stays with its piece');
// A structure that fits a batch is never cut; one that does not is cut by pieces.
for (const id of ['a', 'b', 'd', 'e', 'f']) {
  assert.equal(new Set(entries.filter((e) => e.record.id === id).map((e) => runOf.get(e))).size, 1, `${id} kept whole`);
}
assert.ok(new Set(entries.filter((e) => e.record.id === 'c').map((e) => runOf.get(e))).size > 1, 'c is larger than a batch');
// Every run fits a 16-bit index except the one piece that alone is larger.
for (const run of runs) {
  const b = lay(run);
  const oversize = run.some((e) => pieceOf(e) === e && e.record.id === 'huge');
  if (oversize) {
    assert.equal(new Set(run.map(pieceOf)).size, 1, 'an oversized piece is laid alone');
    assert.ok(b.geometry.index.array instanceof Uint32Array);
  } else {
    assert.ok(verts(run) <= SHORT_INDEX_VERTICES);
    assert.ok(b.geometry.index.array instanceof Uint16Array, 'a run indexes in 16 bits');
  }
}
// The same corners, in fewer bytes.
const before = whole.geometry.index.array.byteLength;
const after = runs.reduce((s, run) => s + lay(run).geometry.index.array.byteLength, 0);
assert.ok(after < before * 0.7, `index bytes ${after} against ${before}`);

console.log(`short index: ${entries.length} entries in ${runs.length} batches, index ${before} -> ${after} bytes`);
