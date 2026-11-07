#!/usr/bin/env node
/** T-3286 — the far shadow twin (renderers/web/js/far-shadow.js), on the CPU.
 * The real module, its browser import map resolved in Node: the twin's cut (it pays, it
 * never reaches past its bound, it never pools two confidences), and the sun-pass swap
 * (far pieces swap, near ones and a low sun do not, and everything is put back).
 * No browser, fixtures or artifact files.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const T = await import(vendor);
const asData = (text) => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64');
const read = (name) => fs.readFileSync(new URL(`../renderers/web/js/${name}`, import.meta.url), 'utf8')
  .replaceAll("from 'three'", 'from ' + JSON.stringify(vendor));
const casters = asData(read('shadow-casters.js'));
const M = await import(asData(read('far-shadow.js').replace("from './shadow-casters.js'", 'from ' + JSON.stringify(casters))));
const checks = []; const test = (name, fn) => { fn(); checks.push(name); console.log('PASS ' + name); };

/** A rippled sheet, `n` x `n` quads over `size` metres: fine relief the twin should drop. */
function sheet(n, size, confidenceAt = () => 0) {
  const pos = [], conf = [], index = [];
  for (let j = 0; j <= n; j++) for (let i = 0; i <= n; i++) {
    const x = size * i / n, z = size * j / n;
    pos.push(x, 0.004 * Math.sin(i * 1.7) * Math.cos(j * 1.3), z);
    conf.push(confidenceAt(x, z));
  }
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const a = j * (n + 1) + i, b = a + 1, c = a + n + 1, d = c + 1;
    index.push(a, c, b, b, c, d);
  }
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new T.Float32BufferAttribute(pos.map((_, k) => (k % 3 === 1 ? 1 : 0)), 3));
  g.setAttribute('_confidence', new T.Float32BufferAttribute(conf, 1));
  g.setIndex(index);
  return g;
}

test('a dense sheet pays: far fewer triangles, every attribute kept, index in range', () => {
  const g = sheet(100, 2), t = M.shadowTwin(g, M.CELL_M);
  assert(t, 'a 20,000-triangle sheet with 2 cm quads must get a twin');
  assert.equal(t.triangles, 20000);
  assert(t.twinTriangles <= t.triangles * M.KEEP_RATIO && t.triangles - t.twinTriangles >= M.MIN_SAVED);
  assert.equal(t.geo.getIndex().count, t.twinTriangles * 3);
  assert.deepEqual(Object.keys(t.geo.attributes).sort(), Object.keys(g.attributes).sort());
  const count = t.geo.getAttribute('position').count;
  for (const v of t.geo.getIndex().array) assert(v < count);
});

test('no piece vertex is farther than the reach from its twin vertex', () => {
  const g = sheet(60, 1.5), t = M.shadowTwin(g, M.CELL_M), reach = M.twinReachM(M.CELL_M);
  assert(t);
  const tp = t.geo.getAttribute('position'), p = g.getAttribute('position');
  for (let v = 0; v < p.count; v++) {
    let best = Infinity;
    for (let w = 0; w < tp.count; w++) {
      best = Math.min(best, Math.hypot(p.getX(v) - tp.getX(w), p.getY(v) - tp.getY(w), p.getZ(v) - tp.getZ(w)));
    }
    assert(best <= reach + 1e-6, `vertex ${v} is ${best} m from the twin, past ${reach}`);
  }
});

test('two confidences are never pooled, so the dither stays on its own side', () => {
  const g = sheet(100, 2, (x) => (x < 1 ? 0 : 0.9)), t = M.shadowTwin(g, M.CELL_M);
  assert(t);
  const tp = t.geo.getAttribute('position'), tc = t.geo.getAttribute('_confidence');
  for (let w = 0; w < tp.count; w++) {
    if (tc.getX(w) === 0) assert(tp.getX(w) < 1 + 1e-6); else assert(tp.getX(w) >= 1 - 1e-6);
  }
});

test('a coarse piece is left whole', () => {
  assert.equal(M.shadowTwin(new T.BoxGeometry(4, 6, 8), M.CELL_M), null);
  assert.equal(M.shadowTwin(sheet(20, 10), M.CELL_M), null, '800 triangles of 50 cm quads gain nothing');
});

test('?farshadow=0 turns it off; anything else leaves it on', () => {
  assert.equal(M.farShadowFromSearch('?farshadow=0'), false);
  assert.equal(M.farShadowFromSearch('?farshadow=1'), true);
  assert.equal(M.farShadowFromSearch(''), true);
});

/** One piece and its hidden twin in a batch, the shadow preparation stubbed to record what it saw. */
function rig() {
  const g = sheet(100, 2), t = M.shadowTwin(g, M.CELL_M);
  const batch = new T.BatchedMesh(2, g.getAttribute('position').count + t.geo.getAttribute('position').count,
    g.getIndex().count + t.geo.getIndex().count, new T.MeshBasicMaterial());
  const piece = batch.addInstance(batch.addGeometry(g)), twin = batch.addInstance(batch.addGeometry(t.geo));
  batch.setVisibleAt(twin, false);
  batch.updateMatrixWorld(true);
  const seen = [];
  batch.onBeforeShadow = function () { seen.push([this.getVisibleAt(piece), this.getVisibleAt(twin)]); };
  const sun = new T.Vector3(0.3, 0.9, 0.3).normalize();
  const state = { on: true, sun: () => sun, pairs: [{ piece, twin, reachM: M.twinReachM(), saved: t.triangles - t.twinTriangles }] };
  M.drawFarShadowAsTwins(batch, state);
  const renderer = { getDrawingBufferSize: (v) => v.set(1280, 800) };
  const shadow = (eye) => {
    const camera = new T.PerspectiveCamera(50, 1.6, 0.1, 2000);
    camera.position.set(...eye); camera.lookAt(1, 0, 1); camera.updateMatrixWorld(true);
    batch.onBeforeShadow(renderer, batch, camera, new T.OrthographicCamera(), batch.geometry, null, null);
  };
  return { batch, piece, twin, seen, state, shadow, sun, saved: state.pairs[0].saved };
}

test('far: the twin casts in the piece\'s place, and both are put back', () => {
  const r = rig(); r.shadow([1, 2, 300]);
  assert.deepEqual(r.seen, [[false, true]]);
  assert.equal(r.state.swapped, 1); assert.equal(r.state.saved, r.saved);
  assert.equal(r.batch.getVisibleAt(r.piece), true); assert.equal(r.batch.getVisibleAt(r.twin), false);
});

test('near, low sun, off, or a hidden piece: the piece casts whole', () => {
  let r = rig(); r.shadow([1, 2, 12]); assert.deepEqual(r.seen, [[true, false]]); assert.equal(r.state.swapped, 0);
  r = rig(); r.sun.set(1, 0.02, 0).normalize(); r.shadow([1, 2, 300]); assert.deepEqual(r.seen, [[true, false]]);
  r = rig(); r.state.on = false; r.shadow([1, 2, 300]); assert.deepEqual(r.seen, [[true, false]]);
  r = rig(); r.batch.setVisibleAt(r.piece, false); r.shadow([1, 2, 300]); assert.deepEqual(r.seen, [[false, false]]);
  assert.equal(r.batch.getVisibleAt(r.twin), false);
});

test('the bound is the screen: a looser maxPixels swaps nearer, a tighter one farther', () => {
  // 1 px at 1280x800, 50 degrees: P = 800 / (2 tan 25) = 858; reach 0.104 m over sin(elevation)
  const near = 0.104 * 858 / 0.9;
  let r = rig(); r.shadow([1, 2, 1 + near * 0.6]); assert.equal(r.state.swapped, 0);
  r = rig(); r.state.maxPixels = 4; r.shadow([1, 2, 1 + near * 0.6]); assert.equal(r.state.swapped, 1);
  r = rig(); r.state.maxPixels = 0.25; r.shadow([1, 2, 1 + near * 2]); assert.equal(r.state.swapped, 0);
});

console.log(`far shadow twin: ${checks.length} checks passed`);
