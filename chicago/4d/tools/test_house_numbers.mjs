#!/usr/bin/env node
/**
 * T-3737 — the 1904 house numbers read the right way round, on the door, in one draw.
 *
 *     node tools/test_house_numbers.mjs
 *
 * Headless, on the committed data/house_numbers/1904.json and a made-up placement for every
 * structure it names (a turn and a shift each), with a canvas that measures figures and paints
 * nothing:
 *
 *   reads    each number's figures run left to right as a reader on the street sees them
 *            (facing the door, looking against its normal), in the order the number is written,
 *            centred on the spot, standing `height_m` tall, in the plane `normal` faces;
 *   placed   every quad is carried through the structure's own matrix (buildings.js `matrixOf`),
 *            so a figure lands where the spot lands under that placement, facing where the
 *            normal turns to; a structure with no placement is counted unplaced, never thrown;
 *   cheap    the whole district is ONE mesh with ONE material on one atlas texture, casts no
 *            shadow, and is folded away past REACH_M in its vertex stage;
 *   hands    each hand the file defines gets its own atlas row, a number reads only its own row,
 *            neighbours on a street are not all one hand, and the gilt is lit, not lamp-bright;
 *   inert    no data base and no list: an empty group, nothing fetched.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);

const THREE = await import('three');
const { createHouseNumbers, numberQuads, drawAtlas, REACH_M, EMISSIVE } = await import('../renderers/web/js/house-numbers.js');

// A canvas that measures each figure 0.55 of the font's size and paints nothing.
const fakeDocument = {
  createElement: () => ({
    width: 0, height: 0,
    getContext: () => ({
      font: '', clearRect() {}, strokeText() {}, fillText() {},
      measureText: () => ({ width: 54 * 0.55 }),
    }),
  }),
};

const doc = JSON.parse(fs.readFileSync(new URL('../data/house_numbers/1904.json', import.meta.url)));
let fails = 0;
const check = (name, fn) => {
  try { fn(); console.log(`  ok   ${name}`); } catch (e) { fails++; console.log(`  FAIL ${name}\n       ${e.message}`); }
};

// reads: a door facing +x (east), its reader looking west; the reader's right is -z.
const widths = Array(10).fill(0.55 * 54 / 64);
check('figures run left to right for a reader facing the door, centred, at their height', () => {
  const h = 0.15;
  const q = numberQuads('1815', [10, 4, -2], [1, 0, 0], h, widths);
  assert.equal(q.positions.length, 4 * 6 * 3, 'two triangles a figure');
  const xs = [], zs = [], ys = [];
  for (let i = 0; i < q.positions.length; i += 3) { xs.push(q.positions[i]); ys.push(q.positions[i + 1]); zs.push(q.positions[i + 2]); }
  assert.ok(xs.every((x) => Math.abs(x - 10) < 1e-9), 'every corner in the door plane');
  assert.ok(Math.abs(Math.min(...ys) - (4 - h / 2)) < 1e-9 && Math.abs(Math.max(...ys) - (4 + h / 2)) < 1e-9, 'the figures stand h tall about the spot');
  const firstFig = zs.slice(0, 6), lastFig = zs.slice(18, 24);
  // the reader's right is -z: the first figure ('1') has the largest z
  assert.ok(Math.min(...firstFig) > Math.max(...lastFig), 'the first figure is on the reader\'s left');
  const mid = (Math.max(...zs) + Math.min(...zs)) / 2;
  assert.ok(Math.abs(mid + 2) < 1e-9, 'the number is centred on the spot');
  // u runs with the reader's right: each figure's corner `a` (u0) is on its left
  assert.ok(q.uvs[0] < q.uvs[2], 'the atlas reads left to right on each quad');
});

check('each figure faces out along the normal (counter-clockwise seen from the street)', () => {
  const q = numberQuads('7', [0, 0, 0], [0, 0, 1], 0.1, widths);
  const p = (i) => new THREE.Vector3(q.positions[i * 3], q.positions[i * 3 + 1], q.positions[i * 3 + 2]);
  const n = new THREE.Vector3().subVectors(p(1), p(0)).cross(new THREE.Vector3().subVectors(p(2), p(0))).normalize();
  assert.ok(n.z > 0.99, `front face points along +z, got ${n.toArray()}`);
});

// placed + cheap: every structure gets a placement of its own
const placements = new Map();
doc.numbers.forEach((row, i) => {
  placements.set(row.structure, new THREE.Matrix4().compose(
    new THREE.Vector3(100 + i * 7, 3 + (i % 4) * 0.25, -50 - i * 3),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(0, (i * 37 % 360) * Math.PI / 180, 0)),
    new THREE.Vector3(1, 1, 1)));
});
const missing = doc.numbers[0].structure;
const buildings = { matrixOf: (id) => (id === missing ? null : placements.get(id) ?? null) };
const problems = [];
const layer = await createHouseNumbers({ doc, buildings, problems, document: fakeDocument });

check('one mesh, one material, one atlas, no shadow cast, folded past its reach', () => {
  const meshes = [];
  layer.group.traverse((o) => { if (o.isMesh) meshes.push(o); });
  assert.equal(meshes.length, 1);
  const m = meshes[0];
  assert.ok(!Array.isArray(m.material) && m.material.map?.isTexture, 'one material on one texture');
  assert.equal(m.castShadow, false);
  assert.ok(m.material.alphaTest > 0, 'figures are cut out of the atlas');
  const shader = { uniforms: {}, vertexShader: 'void main() {\n#include <project_vertex>\n}' };
  m.material.onBeforeCompile(shader);
  assert.equal(shader.uniforms.uNumberReach.value, REACH_M);
  assert.ok(/uNumberReach\) gl_Position/.test(shader.vertexShader), 'the vertex stage folds a far figure away');
  assert.equal(layer.census.draws, 1);
});

check('every number but the unplaced one is carried through its structure\'s own placement', () => {
  assert.equal(layer.census.numbers, doc.numbers.length);
  assert.deepEqual(layer.census.unplaced, [missing]);
  assert.equal(layer.census.placed, doc.numbers.length - 1);
  const pos = layer.mesh.geometry.getAttribute('position');
  const nrm = layer.mesh.geometry.getAttribute('normal');
  let at = 0;
  for (const row of doc.numbers) {
    if (row.structure === missing) continue;
    const m = placements.get(row.structure);
    const figs = row.number.length;
    const spot = new THREE.Vector3(...row.at).applyMatrix4(m);
    const wn = new THREE.Vector3(...row.normal).applyMatrix3(new THREE.Matrix3().getNormalMatrix(m)).normalize();
    const c = new THREE.Vector3();
    for (let k = 0; k < figs * 6; k++) c.add(new THREE.Vector3().fromBufferAttribute(pos, at + k));
    c.divideScalar(figs * 6);
    assert.ok(c.distanceTo(spot) < 0.2, `${row.number} ${row.street}: drawn ${c.distanceTo(spot).toFixed(3)} m off its spot`);
    const n = new THREE.Vector3().fromBufferAttribute(nrm, at);
    assert.ok(n.dot(wn) > 0.999, `${row.number}: faces where its door faces`);
    // the plane: every corner stands on the plane through the spot normal to wn
    for (let k = 0; k < figs * 6; k++) {
      const v = new THREE.Vector3().fromBufferAttribute(pos, at + k);
      assert.ok(Math.abs(v.clone().sub(spot).dot(wn)) < 1e-4, `${row.number}: a corner off the door's plane`);
    }
    at += figs * 6;
  }
  assert.equal(at, pos.count, 'nothing else is in the mesh');
});

check('each hand its own atlas row; a number samples only its own; not lamp-bright', () => {
  const atlas = drawAtlas(doc.hands, fakeDocument);
  const ids = Object.keys(doc.hands);
  assert.ok(ids.length >= 4, 'several hands');
  assert.equal(new Set(ids.map((id) => atlas.hands[id].row)).size, ids.length, 'a row a hand');
  const span = (row) => {
    const q = numberQuads('18', [0, 0, 0], [0, 0, 1], 0.1, atlas.hands[ids[row]].widths, atlas.hands[ids[row]].row);
    const vs = q.uvs.filter((_, i) => i % 2 === 1);
    return [Math.min(...vs), Math.max(...vs)];
  };
  for (let r = 0; r + 1 < ids.length; r++) {
    const [a0, a1] = span(r), [b0, b1] = span(r + 1);
    assert.ok(a1 <= 1 && b0 >= 0 && (b1 < a0 || a1 < b0), `rows ${r} and ${r + 1} overlap`);
  }
  assert.ok(EMISSIVE <= 0.25, `emissive ${EMISSIVE}: the figures glow`);
  for (const h of Object.values(doc.hands)) {
    const c = parseInt(h.fill.slice(1), 16);
    const lum = (0.2126 * (c >> 16) + 0.7152 * ((c >> 8) & 255) + 0.0722 * (c & 255)) / 255;
    assert.ok(lum < 0.85, `fill ${h.fill} is near white`);
  }
  const used = new Set(doc.numbers.map((r) => r.hand));
  assert.ok(used.size >= 4, `only ${used.size} hands used on the street`);
  assert.ok(layer.census.hands && Object.keys(layer.census.hands).length === used.size, 'census counts each hand');
});

const empty = await createHouseNumbers({ buildings });
check('no data base and no list: nothing drawn, nothing fetched', () => {
  assert.equal(empty.group.children.length, 0);
  assert.equal(empty.doc, null);
});

console.log(fails ? `house numbers: ${fails} FAIL` : 'house numbers: OK');
process.exit(fails ? 1 : 0);
