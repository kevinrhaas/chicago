// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: a body's skin split finer where a person's hair stands out (renderers/web/js/human-fine.js).
// It must: keep the source's rows, in order, in every attribute; put each new vertex at the
// middle of one edge in every attribute and morph target; give it its ends' bones, summing to
// one; keep the surface closed across a seam in the texture coordinates; leave no edge of a
// triangle of hair longer than the record asks; split nothing where no hair stands; and free
// what it made with its source.
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { fineCells, fineGeometry, fineOf, FINE } = await import(new URL('renderers/web/js/human-fine.js', here));

// A sheet of 768 x 1024 in cells of 16: 48 across, 64 down, a bit a cell, the high bit first.
const SIZE = [768, 1024], COLS = 48, ROWS = 64;
const pack = set => {
  const bits = new Uint8Array(COLS * ROWS / 8);
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) if (set(x, y)) bits[(y * COLS + x) >> 3] |= 128 >> ((y * COLS + x) & 7);
  return Buffer.from(bits).toString('base64');
};
const block = set => ({ cell_px: 16, edge_m: .008, cells: pack(set) });
const upper = fineCells(block((x, y) => y < 32), SIZE);
assert.deepEqual([upper.cols, upper.rows, upper.edge_m, upper.bits.length], [COLS, ROWS, .008, 384]);
for (const bad of [null, {}, { cell_px: 16, edge_m: .008 }, { ...block(() => true), cell_px: 0 }, { ...block(() => true), edge_m: 0 }, { ...block(() => true), cells: 'AAAA' },
  { ...block(() => true), cells: '***' }, block(() => false)]) assert.equal(fineCells(bad, SIZE), null, JSON.stringify(bad)?.slice(0, 60));
assert.equal(fineCells(block(() => true), null), null, 'a sheet with no size has no cells');

// A head: a ball of 10 cm, its texture coordinates the whole sheet, with a seam down its back
// (the ball's own: a column of vertices drawn twice) and both poles drawn once a segment.
const LAYOUT = { uv: [[0, 0, 1, 1]], map: [[1, 1, 0, 0]] };
const ball = () => {
  const g = new THREE.SphereGeometry(.1, 12, 8);
  const n = g.attributes.position.count, ji = new Uint16Array(n * 4), jw = new Float32Array(n * 4), blink = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const y = g.attributes.position.getY(i), w = (y + .1) / .2;
    ji.set([0, 1, 2, 0], i * 4); jw.set([1 - w, w * .75, w * .25, 0], i * 4);
    blink.set([0, y * .1, 0], i * 3);
  }
  g.setAttribute('skinIndex', new THREE.BufferAttribute(ji, 4));
  g.setAttribute('skinWeight', new THREE.BufferAttribute(jw, 4));
  g.morphAttributes.position = [Object.assign(new THREE.BufferAttribute(blink, 3), { name: 'eyeBlinkLeft' })];
  g.morphTargetsRelative = true;
  g.computeBoundingSphere();
  return g;
};
const I = new THREE.Matrix4();
const places = (g, M = I) => {
  const p = g.attributes.position, v = new THREE.Vector3(), ids = new Map(), out = [];
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(M);
    const k = [v.x, v.y, v.z].map(x => Math.round(x / 2e-5)).join(',');
    if (!ids.has(k)) ids.set(k, ids.size);
    out.push(ids.get(k));
  }
  return out;
};
// How often each edge is drawn, by place: twice everywhere on a closed surface.
const edgeUse = (g, M = I) => {
  const at = places(g, M), use = new Map(), t = g.index.array;
  for (let i = 0; i < t.length; i += 3) for (let k = 0; k < 3; k++) {
    const a = at[t[i + k]], b = at[t[i + (k + 1) % 3]];
    if (a === b) continue;
    const key = a < b ? `${a}-${b}` : `${b}-${a}`;
    use.set(key, (use.get(key) ?? 0) + 1);
  }
  return [...use.values()];
};
const area = (g, M = I, name = 'position') => {
  const p = g.attributes[name], t = g.index.array, a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  let sum = 0;
  for (let i = 0; i < t.length; i += 3) {
    a.fromBufferAttribute(p, t[i]); b.fromBufferAttribute(p, t[i + 1]); c.fromBufferAttribute(p, t[i + 2]);
    if (name === 'uv') a.z = b.z = c.z = 0; else { a.applyMatrix4(M); b.applyMatrix4(M); c.applyMatrix4(M); }
    sum += b.sub(a).cross(c.sub(a)).length() / 2;
  }
  return sum;
};
const longest = (g, M, keep) => {
  const p = g.attributes.position, uv = g.attributes.uv, t = g.index.array, v = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  let most = 0;
  for (let i = 0; i < t.length; i += 3) {
    if (![0, 1, 2].every(k => keep(uv.getX(t[i + k]), uv.getY(t[i + k])))) continue;
    for (let k = 0; k < 3; k++) v[k].fromBufferAttribute(p, t[i + k]).applyMatrix4(M);
    most = Math.max(most, v[0].distanceTo(v[1]), v[1].distanceTo(v[2]), v[2].distanceTo(v[0]));
  }
  return most;
};

{
  const src = ball(), n0 = src.attributes.position.count, before = { index: Array.from(src.index.array), pos: Array.from(src.attributes.position.array) };
  assert(edgeUse(src).every(u => u === 2), 'the ball is closed');
  const fine = fineGeometry(src, { metres: I, layout: LAYOUT, cells: upper });
  assert(fine && fine !== src, 'the ball is split');
  const n = fine.attributes.position.count;
  assert(n > n0 * 3, `it has many more vertices (${n0} -> ${n})`);
  assert.deepEqual(fine.userData.chiFine, { of: n0, added: n - n0 });
  assert.deepEqual([Array.from(src.index.array), Array.from(src.attributes.position.array)], [before.index, before.pos], 'the source is not changed');
  for (const [name, a] of Object.entries(src.attributes)) {
    const f = fine.attributes[name];
    assert.equal(f.count, n, `${name} has a row a vertex`);
    assert.equal(f.itemSize, a.itemSize); assert.equal(f.normalized, a.normalized); assert.equal(f.array.constructor, a.array.constructor);
    assert.deepEqual(Array.from(f.array.subarray(0, n0 * a.itemSize)), Array.from(a.array), `${name}: the source's rows first, as they were`);
  }
  assert(edgeUse(fine).every(u => u === 2), 'still closed: every edge is drawn twice, the seam and the poles too');
  assert(Math.abs(area(fine) - area(src)) < 1e-9, 'its area is the same: every new vertex lies on an edge');
  assert(Math.abs(area(fine, I, 'uv') - area(src, I, 'uv')) < 1e-9, 'and so on the sheet');
  // The ball's texture coordinate v runs up from the south pole: the sheet's upper rows are its southern half.
  assert(longest(fine, I, (u, v) => v < .45) <= .008 + 1e-9, 'no edge of the hair is longer than asked');
  assert(longest(fine, I, (u, v) => v > .7) > .03, 'and where no hair stands the triangles are the source\'s');
  // Bones: each row sums to one, on bones its ends had; morph targets: the middle of the ends'.
  const ji = fine.attributes.skinIndex, jw = fine.attributes.skinWeight, blink = fine.morphAttributes.position[0];
  assert.equal(blink.name, 'eyeBlinkLeft'); assert.equal(blink.count, n);
  for (let i = n0; i < n; i++) {
    let sum = 0;
    for (let c = 0; c < 4; c++) { sum += jw.getComponent(i, c); assert(ji.getComponent(i, c) <= 2); }
    assert(Math.abs(sum - 1) < 1e-6, 'a new vertex\'s bones sum to one');
    const y = fine.attributes.position.getY(i), w = (y + .1) / .2;
    assert(Math.abs(blink.getY(i) - y * .1) < 1e-7, 'a morph target moves a new vertex as it moves its edge');
    // The ball's weights run straight with height, so a middle's are the height's too (bone 0 first where it is the strongest).
    const got = new Map([0, 1, 2, 3].map(c => [ji.getComponent(i, c), jw.getComponent(i, c)]).filter(([, x]) => x > 0));
    assert(Math.abs((got.get(0) ?? 0) - (1 - w)) < 1e-5 && Math.abs((got.get(1) ?? 0) - w * .75) < 1e-5 && Math.abs((got.get(2) ?? 0) - w * .25) < 1e-5, 'its bones are its ends\' together');
    assert(Math.abs(new THREE.Vector3().fromBufferAttribute(fine.attributes.normal, i).length() - 1) < 1e-6, 'a new normal has its length');
  }
  assert.equal(fine.boundingSphere, src.boundingSphere, 'the source\'s bounds hold');
  assert.equal(fine.morphTargetsRelative, true);
  // Nothing to split: no cells under it, edges short enough already, a geometry in groups, one with no index.
  assert.equal(fineGeometry(src, { metres: I, layout: { uv: [[2, 2, 3, 3]], map: [[1, 1, 0, 0]] }, cells: upper }), null, 'a body off the sheet is left');
  assert.equal(fineGeometry(src, { metres: new THREE.Matrix4().makeScale(.1, .1, .1), layout: LAYOUT, cells: upper }), null, 'a body whose edges are short already is left');
  assert.equal(fineGeometry(src, { metres: I, layout: LAYOUT, cells: null }), null);
  assert.equal(fineGeometry(Object.assign(ball(), { groups: [{ start: 0, count: 3, materialIndex: 0 }] }), { metres: I, layout: LAYOUT, cells: upper }), null, 'a geometry in groups is left');
  assert.equal(fineGeometry(ball().toNonIndexed(), { metres: I, layout: LAYOUT, cells: upper }), null, 'a geometry with no index is left');
  assert.equal(fineGeometry(fine, { metres: I, layout: LAYOUT, cells: upper }), null, 'a fine geometry has nothing left to split');
  // One round at a time: each halves the longest edge.
  const one = fineGeometry(src, { metres: I, layout: LAYOUT, cells: upper, rounds: 1 });
  assert(one.attributes.position.count < n && longest(one, I, (u, v) => v < .45) > .008, 'one round is not enough for a ball this coarse');
  assert(FINE.rounds >= 3, 'four centimetres come under eight millimetres in three rounds');

  // Kept: once a source and sheet, the fine one handed back as it is, freed with its source.
  const opts = { metres: I, layout: LAYOUT, cells: upper };
  const a = fineOf(src, 'sheet-a', opts), b = fineOf(src, 'sheet-a', opts), c = fineOf(src, 'sheet-b', opts);
  assert(a === b && a !== c && a !== src, 'one fine geometry a source and sheet');
  assert.equal(fineOf(a, 'sheet-a', opts), a, 'a fine geometry is not split again');
  assert.equal(fineOf(src, 'none', { ...opts, cells: null }), src, 'with nothing to split the source is worn');
  let freed = 0;
  a.addEventListener('dispose', () => freed++); c.addEventListener('dispose', () => freed++);
  src.dispose();
  assert.equal(freed, 2, 'its fine geometries are freed with the source');
  assert(fineOf(src, 'sheet-a', opts) !== a, 'and made again if it is worn again');
}

// A quantised export: whole numbers in a buffer its attributes share, scaled into metres by the
// bind matrices. The rows keep their kind, a middle is rounded, a weight row sums to 255.
{
  const f = ball(), n0 = f.attributes.position.count, q = new THREE.BufferGeometry();
  const S = 32767 / .1, inter = new Int16Array(n0 * 8), ib = new THREE.InterleavedBuffer(inter, 8);
  const w8 = new Uint8Array(n0 * 4), j8 = new Uint8Array(n0 * 4), uv16 = new Uint16Array(n0 * 2);
  for (let i = 0; i < n0; i++) {
    for (let c = 0; c < 3; c++) {
      inter[i * 8 + c] = Math.round(f.attributes.position.getComponent(i, c) * S);
      inter[i * 8 + 4 + c] = Math.round(f.attributes.normal.getComponent(i, c) * 32767);
    }
    uv16.set([Math.round(f.attributes.uv.getX(i) * 65535), Math.round(f.attributes.uv.getY(i) * 65535)], i * 2);
    const w = Math.round(f.attributes.skinWeight.getY(i) / .75 * 255);
    w8.set([255 - w, w, 0, 0], i * 4); j8.set([3, 5, 0, 0], i * 4);
  }
  q.setIndex(Array.from(f.index.array));
  q.setAttribute('position', new THREE.InterleavedBufferAttribute(ib, 3, 0, true));
  q.setAttribute('normal', new THREE.InterleavedBufferAttribute(ib, 3, 4, true));
  q.setAttribute('uv', new THREE.BufferAttribute(uv16, 2, true));
  q.setAttribute('skinIndex', new THREE.BufferAttribute(j8, 4));
  q.setAttribute('skinWeight', new THREE.BufferAttribute(w8, 4, true));
  const M = new THREE.Matrix4().makeScale(.1, .1, .1);   // a normalised whole number reads as -1..1
  const fine = fineGeometry(q, { metres: M, layout: LAYOUT, cells: upper });
  const n = fine.attributes.position.count;
  assert(n > n0 * 3);
  const p = fine.attributes.position, nr = fine.attributes.normal;
  assert(p.array instanceof Int16Array && p.normalized && !p.isInterleavedBufferAttribute && p.array.length === n * 3, 'the positions keep their kind, in an array of their own');
  for (let i = 0; i < n0; i++) for (let c = 0; c < 3; c++) {
    assert.equal(p.array[i * 3 + c], inter[i * 8 + c]); assert.equal(nr.array[i * 3 + c], inter[i * 8 + 4 + c]);
  }
  assert(edgeUse(fine, M).every(u => u === 2), 'closed, in whole numbers too');
  assert(Math.abs(area(fine, M) - area(q, M)) < 1e-6, 'and no larger');
  assert(longest(fine, M, (u, v) => v < .45) <= .008 + 1e-6);
  const jw = fine.attributes.skinWeight, ji = fine.attributes.skinIndex;
  assert(jw.array instanceof Uint8Array && jw.normalized && ji.array instanceof Uint8Array && !ji.normalized);
  for (let i = n0; i < n; i++) {
    assert.equal(jw.array[i * 4] + jw.array[i * 4 + 1] + jw.array[i * 4 + 2] + jw.array[i * 4 + 3], 255, 'a new vertex\'s weights sum to the whole');
    for (let c = 0; c < 4; c++) assert(jw.array[i * 4 + c] === 0 || [3, 5].includes(ji.array[i * 4 + c]), 'on its ends\' bones');
    assert(jw.array[i * 4] >= jw.array[i * 4 + 1], 'the strongest first');
    assert(Math.abs(Math.hypot(nr.array[i * 3], nr.array[i * 3 + 1], nr.array[i * 3 + 2]) - 32767) < 2, 'a new normal has its length');
  }
}

// Hair in one patch only: its triangles are split, their neighbours along the shared edges, and
// the rest of the head is the source's.
{
  const src = ball(), patch = fineCells(block((x, y) => x >= 10 && x < 14 && y >= 20 && y < 24), SIZE);
  const fine = fineGeometry(src, { metres: I, layout: LAYOUT, cells: patch }), all = fineGeometry(src, { metres: I, layout: LAYOUT, cells: upper });
  assert(fine && fine.attributes.position.count < all.attributes.position.count / 2, 'a patch of hair costs a patch of vertices');
  assert(edgeUse(fine).every(u => u === 2), 'closed where the fine triangles meet the coarse');
  assert(Math.abs(area(fine) - area(src)) < 1e-9);
}
console.log('human-fine: rows kept, middles in every attribute, closed across the seam, freed with the source');
