#!/usr/bin/env node
/** T-3312 — the colour pass's far twin at `light` (renderers/web/js/far-colour.js, cut by
 * far-shadow.js's `shadowTwin(..., { byNormal: true })`), on the CPU. The real modules, their
 * browser import maps resolved in Node: the cut never pools two normals (with a control that
 * the sun's cut does, so the check can fail), every face over a cell survives, the swap is the
 * colour pass's only (never the sun's), far pieces swap and near ones do not, the twin wears
 * the piece's paint, the harness control hides both, and everything is put back.
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
const S = await import(asData(read('far-shadow.js').replace("from './shadow-casters.js'", 'from ' + JSON.stringify(casters))));
const C = await import(asData(read('far-colour.js')));
const checks = []; const test = (name, fn) => { fn(); checks.push(name); console.log('PASS ' + name); };

/**
 * A 2 m wall (normal +z) carrying `n` x `n` small studs, each a 2 cm cube's five faces (no back),
 * the studs written first:
 * the wall's large faces and the studs' fine ones meet in every cell, at four normals.
 */
function studdedWall(n = 30) {
  const pos = [], nor = [], index = [];
  const quad = (a, b, c, d, nv) => {
    const k = pos.length / 3;
    for (const p of [a, b, c, d]) { pos.push(...p); nor.push(...nv); }
    index.push(k, k + 1, k + 2, k, k + 2, k + 3);
  };
  const s = 0.02;
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const x = 0.03 + i * 2 / n, y = 0.03 + j * 2 / n;
    quad([x, y, 0], [x, y + s, 0], [x, y + s, s], [x, y, s], [-1, 0, 0]);
    quad([x + s, y, 0], [x + s, y, s], [x + s, y + s, s], [x + s, y + s, 0], [1, 0, 0]);
    quad([x, y, 0], [x, y, s], [x + s, y, s], [x + s, y, 0], [0, -1, 0]);
    quad([x, y + s, 0], [x + s, y + s, 0], [x + s, y + s, s], [x, y + s, s], [0, 1, 0]);
    quad([x, y, s], [x + s, y, s], [x + s, y + s, s], [x, y + s, s], [0, 0, 1]);
  }
  // the wall last, so a pool at its corner opens on a stud's vertex: the sun's cut then
  // hands the wall triangle a stud's normal, which is what the control shows
  quad([0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0], [0, 0, 1]);
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new T.Float32BufferAttribute(nor, 3));
  g.setAttribute('_confidence', new T.Float32BufferAttribute(new Array(pos.length / 3).fill(0), 1));
  g.setIndex(index);
  return g;
}
/** How many twin triangles carry corners of more than one normal. */
function mixed(twin) {
  const nm = twin.getAttribute('normal'), ix = twin.getIndex().array;
  let n = 0;
  for (let t = 0; t < ix.length; t += 3) {
    const key = (v) => `${nm.getX(v)},${nm.getY(v)},${nm.getZ(v)}`;
    if (new Set([key(ix[t]), key(ix[t + 1]), key(ix[t + 2])]).size > 1) n++;
  }
  return n;
}

test('the colour cut never pools two normals; the sun\'s cut does (the control)', () => {
  const g = studdedWall();
  const colour = S.shadowTwin(g, C.CELL_M, { byNormal: true, keepRatio: C.KEEP_RATIO });
  assert(colour, 'a studded wall must pay a colour twin');
  assert.equal(mixed(colour.geo), 0, 'a colour twin triangle is lit by one normal');
  const sun = S.shadowTwin(g, C.CELL_M, { keepRatio: 1 });
  assert(sun && mixed(sun.geo) > 0, 'the control: pooling without normals does mix them, so the check can fail');
});

test('the studs close up and the wall\'s two halves survive, every attribute kept, index in range', () => {
  const g = studdedWall(), t = S.shadowTwin(g, C.CELL_M, { byNormal: true, keepRatio: C.KEEP_RATIO });
  assert(t.twinTriangles <= t.triangles * C.KEEP_RATIO && t.triangles - t.twinTriangles >= S.MIN_SAVED);
  const nm = t.geo.getAttribute('normal');
  let wall = 0;
  for (const v of t.geo.getIndex().array) if (nm.getZ(v) === 1) wall++;
  assert(wall >= 6, 'the wall face, 2 m across, is kept');
  assert.deepEqual(Object.keys(t.geo.attributes).sort(), Object.keys(g.attributes).sort());
  const count = t.geo.getAttribute('position').count;
  for (const v of t.geo.getIndex().array) assert(v < count);
});

test('no normals, no colour twin; a coarse piece is left whole', () => {
  const g = studdedWall(); g.deleteAttribute('normal');
  assert.equal(S.shadowTwin(g, C.CELL_M, { byNormal: true }), null);
  assert.equal(S.shadowTwin(new T.BoxGeometry(4, 6, 8), C.CELL_M, { byNormal: true, keepRatio: C.KEEP_RATIO }), null);
});

test('?farcolour=0 turns it off; anything else leaves it on', () => {
  assert.equal(C.farColourFromSearch('?farcolour=0'), false);
  assert.equal(C.farColourFromSearch('?farcolour=1'), true);
  assert.equal(C.farColourFromSearch(''), true);
});

/** One piece and its hidden colour twin in a batch, the preparation stubbed to record what it saw. */
function rig() {
  const g = studdedWall(), t = S.shadowTwin(g, C.CELL_M, { byNormal: true, keepRatio: C.KEEP_RATIO });
  const batch = new T.BatchedMesh(2, g.getAttribute('position').count + t.geo.getAttribute('position').count,
    g.getIndex().count + t.geo.getIndex().count, new T.MeshBasicMaterial());
  const piece = batch.addInstance(batch.addGeometry(g)), twin = batch.addInstance(batch.addGeometry(t.geo));
  batch.setColorAt(piece, new T.Color(0.8, 0.2, 0.1)); batch.setColorAt(twin, new T.Color(0, 0, 0));
  batch.setVisibleAt(twin, false);
  batch.updateMatrixWorld(true);
  const seen = [], colours = [];
  batch.onBeforeRender = function () {
    seen.push([this.getVisibleAt(piece), this.getVisibleAt(twin)]);
    colours.push(this.getColorAt(twin, new T.Color()).getHexString());
  };
  const state = { on: true, pairs: [{ piece, twin, reachM: S.twinReachM(C.CELL_M), saved: t.triangles - t.twinTriangles }] };
  C.drawFarColourAsTwins(batch, state);
  const renderer = { getDrawingBufferSize: (v) => v.set(390, 780) };
  const view = (eye, scene = new T.Scene()) => {
    const camera = new T.PerspectiveCamera(60, 0.5, 0.1, 2000);
    camera.position.set(...eye); camera.lookAt(1, 1, 0); camera.updateMatrixWorld(true);
    batch.onBeforeRender(renderer, scene, camera, batch.geometry, batch.material, null);
  };
  return { batch, piece, twin, seen, colours, state, view, saved: state.pairs[0].saved };
}

test('far: the twin draws in the piece\'s place wearing its paint, and both are put back', () => {
  const r = rig(); r.view([1, 1, 400]);
  assert.deepEqual(r.seen, [[false, true]]);
  assert.equal(r.colours[0], new T.Color(0.8, 0.2, 0.1).getHexString());
  assert.equal(r.state.swapped, 1); assert.equal(r.state.saved, r.saved);
  assert.equal(r.batch.getVisibleAt(r.piece), true); assert.equal(r.batch.getVisibleAt(r.twin), false);
});

test('near, off, the sun\'s pass (no scene), or a hidden piece: the piece draws whole', () => {
  let r = rig(); r.view([1, 1, 20]); assert.deepEqual(r.seen, [[true, false]]); assert.equal(r.state.swapped, 0);
  r = rig(); r.state.on = false; r.view([1, 1, 400]); assert.deepEqual(r.seen, [[true, false]]);
  r = rig(); r.view([1, 1, 400], null); assert.deepEqual(r.seen, [[true, false]]);
  r = rig(); r.batch.setVisibleAt(r.piece, false); r.view([1, 1, 400]); assert.deepEqual(r.seen, [[false, false]]);
  assert.equal(r.batch.getVisibleAt(r.twin), false);
});

test('the bound is the screen pixel; the control hides both', () => {
  // 390x780 at 60 degrees: P = 780 / (2 tan 30) = 675.5; the reach is sqrt(3) x CELL_M
  const at = S.twinReachM(C.CELL_M) * 675.5 / C.MAX_PIXELS, radius = Math.hypot(1, 1, 0.02);
  let r = rig(); r.view([1, 1, (at + radius) * 0.95]); assert.equal(r.state.swapped, 0);
  r = rig(); r.view([1, 1, (at + radius) * 1.05]); assert.equal(r.state.swapped, 1);
  r = rig(); r.state.maxPixels = 4; r.view([1, 1, (at + radius) * 0.5]); assert.equal(r.state.swapped, 1);
  r = rig(); r.state.control = true; r.view([1, 1, 400]); assert.deepEqual(r.seen, [[false, false]]);
  assert.equal(r.batch.getVisibleAt(r.piece), true);
});

console.log(`far colour twin: ${checks.length} checks passed`);
