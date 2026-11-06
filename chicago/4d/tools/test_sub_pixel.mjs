#!/usr/bin/env node
/** T-3426 — at `light`, a structure piece whose whole bounding sphere lands within a pixel of
 * its centre is not drawn in the colour pass (renderers/web/js/sub-pixel.js). On the CPU, the
 * real module and the vendored three: a far speck is hidden inside the colour pass and a near
 * one, or a big far one, is not (with a control that the bound can be crossed both ways); the
 * sun's pass (scene null) and an `on: false` state touch nothing; a piece already hidden stays
 * hidden; and every piece is put back before the hook returns, so picking and every reader of
 * the batch see it. No browser, fixtures or artifact files.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const T = await import(vendor);
const asData = (text) => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64');
const read = (name) => fs.readFileSync(new URL(`../renderers/web/js/${name}`, import.meta.url), 'utf8')
  .replaceAll("from 'three'", 'from ' + JSON.stringify(vendor));
const P = await import(asData(read('sub-pixel.js')));
const checks = []; const test = (name, fn) => { fn(); checks.push(name); console.log('PASS ' + name); };

// A 780 px tall drawing buffer and a 60 degree camera at the origin looking down -z: one metre
// at depth d is 780 / (2 tan 30deg) / d pixels, about 675 / d.
const camera = new T.PerspectiveCamera(60, 390 / 780, 0.1, 5000);
camera.updateMatrixWorld(); camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
const renderer = { domElement: { height: 780 } };
const PIXELS = 780 * camera.projectionMatrix.elements[5] / 2;

/** A batch of unit-radius boxes (half-size h), one instance per entry `[h, z]`. */
function batchOf(entries) {
  const geos = entries.map(([h]) => new T.BoxGeometry(2 * h, 2 * h, 2 * h));
  const verts = geos.reduce((n, g) => n + g.attributes.position.count, 0);
  const idx = geos.reduce((n, g) => n + g.index.count, 0);
  const b = new T.BatchedMesh(entries.length, verts, idx, new T.MeshBasicMaterial());
  entries.forEach(([, z], i) => {
    const id = b.addInstance(b.addGeometry(geos[i]));
    b.setMatrixAt(id, new T.Matrix4().makeTranslation(0, 0, -z));
  });
  b.updateMatrixWorld();
  return b;
}
const scratch = { m: new T.Matrix4(), sphere: new T.Sphere() };
/** Install the hook over a recorder; the recorder sees what the colour pass would draw. */
function hooked(entries, state) {
  const b = batchOf(entries);
  const seen = [];
  b.onBeforeRender = function () { seen.push(entries.map((_, i) => this.getVisibleAt(i))); };
  P.skipSubPixelPieces(b, state, scratch);
  return { b, seen };
}
const scene = new T.Scene();
// a 5 cm box's sphere radius is sqrt(3) * 0.05 = 0.0866 m: at 1,000 m it projects to 0.06 px,
// at 20 m to 2.9 px. A 3 m box at 1,000 m projects to 3.5 px.
const SPECK = 0.05;
const r = (h, z) => Math.sqrt(3) * h * PIXELS / (z - Math.sqrt(3) * h);

test('the bound is one pixel of radius, the rule the colour twins keep', () => {
  assert.equal(P.MAX_RADIUS_PIXELS, 1);
  assert.ok(r(SPECK, 1000) < 1 && r(SPECK, 20) > 1 && r(3, 1000) > 1, 'the fixture straddles the bound');
});

test('a far speck is not drawn in the colour pass; a near speck and a big far piece are', () => {
  const state = { on: true, skipped: 0 };
  const { b, seen } = hooked([[SPECK, 1000], [SPECK, 20], [3, 1000]], state);
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  assert.deepEqual(seen[0], [false, true, true]);
  assert.equal(state.skipped, 1);
});

test('the bound can be crossed both ways: a looser limit hides the near speck, a zero one hides nothing', () => {
  const loose = { on: true, maxPixels: 5, skipped: 0 };
  const a = hooked([[SPECK, 1000], [SPECK, 20], [3, 1000]], loose);
  a.b.onBeforeRender(renderer, scene, camera, a.b.geometry, a.b.material, null);
  assert.deepEqual(a.seen[0], [false, false, false]);
  const none = { on: true, maxPixels: 0, skipped: 0 };
  const z = hooked([[SPECK, 1000], [SPECK, 20], [3, 1000]], none);
  z.b.onBeforeRender(renderer, scene, camera, z.b.geometry, z.b.material, null);
  assert.deepEqual(z.seen[0], [true, true, true]);
});

test('every piece is put back before the hook returns, so picking and readers see it', () => {
  const state = { on: true, skipped: 0 };
  const { b } = hooked([[SPECK, 1000], [SPECK, 2000], [3, 1000]], state);
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  assert.equal(state.skipped, 2);
  assert.deepEqual([0, 1, 2].map((i) => b.getVisibleAt(i)), [true, true, true]);
});

test('the sun\'s pass (no scene) and an off state touch nothing', () => {
  const sun = { on: true, skipped: 0 };
  const s = hooked([[SPECK, 1000]], sun);
  s.b.onBeforeRender(renderer, null, camera, s.b.geometry, s.b.material, null);
  assert.deepEqual(s.seen[0], [true]);
  const off = { on: false, skipped: 7 };
  const o = hooked([[SPECK, 1000]], off);
  o.b.onBeforeRender(renderer, scene, camera, o.b.geometry, o.b.material, null);
  assert.deepEqual(o.seen[0], [true]);
  assert.equal(off.skipped, 0);
});

test('a piece already hidden stays hidden, and is not counted or put back', () => {
  const state = { on: true, skipped: 0 };
  const { b, seen } = hooked([[SPECK, 1000], [3, 1000]], state);
  b.setVisibleAt(0, false);
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  assert.deepEqual(seen[0], [false, true]);
  assert.equal(state.skipped, 0);
  assert.equal(b.getVisibleAt(0), false);
});

test('a piece behind the camera or straddling it is drawn (nothing to collapse it against)', () => {
  const state = { on: true, skipped: 0 };
  const { b, seen } = hooked([[SPECK, -1000], [SPECK, 0.05]], state);
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  assert.deepEqual(seen[0], [true, true]);
});

test('the cached spheres follow a piece that moves', () => {
  const state = { on: true, skipped: 0 };
  const { b, seen } = hooked([[SPECK, 1000]], state);
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  b.setMatrixAt(0, new T.Matrix4().makeTranslation(0, 0, -20));
  b.onBeforeRender(renderer, scene, camera, b.geometry, b.material, null);
  assert.deepEqual(seen, [[false], [true]]);
});

test('?subpixel=0 turns it off; anything else leaves it on', () => {
  assert.equal(P.subPixelFromSearch('?subpixel=0'), false);
  assert.equal(P.subPixelFromSearch('?year=1835'), true);
  assert.equal(P.subPixelFromSearch(undefined), true);
});

console.log(`sub-pixel: ${checks.length} checks passed`);
