#!/usr/bin/env node
/**
 * T-3526 — no yard earth under a dwelling, so the 1812 camp's lodges stand on the ground
 * from any distance instead of floating over a navy band.
 *
 * The owner, 2026-11-08: "the mat lodges seem to float above the ground from far away".
 * The yard surfaces carry polygonOffset -8/-32 and draw after the opaques, so at a grazing
 * view the camp's worn earth won the depth test against each lodge's foot and painted the
 * shaded ground under the lodge over it (yards.js § NO YARD EARTH UNDER A DWELLING). The
 * camp ground now states its dwellings and yards.js cuts its earth out from under them.
 * Headless, no browser:
 *
 *   record    the committed camp ground states one plan per dwelling the archetype lays
 *             (73 in 1812), each finite with positive half-axes, every one inside its own
 *             ground's worn patch;
 *   inside    read back through the mask as the GPU reads it (bilinear on the texel grid),
 *             every plan is cut at 80 % of its radius in sixteen directions, and kept at the
 *             lowest a lodge's foot can sit (1 - the _Dome's largest foot wobble), so the cut
 *             never shows round a foot; 2 m out it is far from any cut;
 *   texture   one byte a texel with unpackAlignment 1 (the default 4 failed black on an odd
 *             width and cut every yard in the box), linear filtering, no mipmaps, and a box
 *             that maps local E/N onto it;
 *   shader    the cut is compiled only with YARD_DWELLINGS, which declares its uniforms, and
 *             is spliced at the clipping planes; a scene with no dwellings builds no mask.
 *
 *   node tools/test_yard_dwelling_cut.mjs
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
const yards = await import('../renderers/web/js/yards.js');
const { dwellingsOf, dwellingMask, dwellingDistance, DWELLING_KEEP } = yards;

const root = new URL('..', import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, root), 'utf8'));
const camp = read('data/enclosures/1812/potawatomi_camp_1812_ground.json');

// lodge_camp _Dome's foot wobble: three harmonics of up to 0.035 / sqrt(k), k = 2, 3, 5.
const WOBBLE_MAX = [2, 3, 5].reduce((s, k) => s + 0.035 / Math.sqrt(k), 0);
const FOOT_MIN = 1 - WOBBLE_MAX;
let checks = 0;

// record
const list = dwellingsOf([camp]);
assert.equal(list.length, camp.ground.dwellings_local_enu_m.length);
assert.equal(list.length, 73, `1812 camp dwellings: ${list.length}`);
for (const d of list) {
  assert.equal(d.length, 6);
  assert.ok(d.every(Number.isFinite), `finite: ${d}`);
  assert.ok(d[2] > 1 && d[3] > 1 && d[2] < 5 && d[3] < 5, `half-axes: ${d}`);
  assert.ok([2, 2.8, 8].includes(d[5]), `exponent: ${d}`);
}
const inRing = (ring, e, n) => {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ei, ni] = ring[i]; const [ej, nj] = ring[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) inside = !inside;
  }
  return inside;
};
for (const d of list) {
  assert.ok(camp.ground.interior_local_enu_m.some((ring) => inRing(ring, d[0], d[1])),
    `dwelling at ${d[0]}, ${d[1]} stands on no worn patch`);
  checks += 1;
}

// inside, as the GPU reads the mask
assert.ok(DWELLING_KEEP < FOOT_MIN - 0.03, `keep ${DWELLING_KEEP} is not inside the lowest foot ${FOOT_MIN.toFixed(3)}`);
const mask = dwellingMask([camp]);
assert.ok(mask, 'no mask for the 1812 camp');
const { texture, box, width, height, texelM } = mask;
const data = texture.image.data;
const sample = (e, n) => {
  // texture2D on a LinearFilter texture: texel centres at (i + 0.5) / width.
  const u = (e - box.x) * box.z * width - 0.5;
  const v = (n - box.y) * box.w * height - 0.5;
  const i0 = Math.max(0, Math.min(width - 1, Math.floor(u)));
  const j0 = Math.max(0, Math.min(height - 1, Math.floor(v)));
  const i1 = Math.min(width - 1, i0 + 1); const j1 = Math.min(height - 1, j0 + 1);
  const fu = Math.max(0, Math.min(1, u - i0)); const fv = Math.max(0, Math.min(1, v - j0));
  const at = (i, j) => data[j * width + i] / 255;
  return (at(i0, j0) * (1 - fu) + at(i1, j0) * fu) * (1 - fv) + (at(i0, j1) * (1 - fu) + at(i1, j1) * fu) * fv;
};
const cut = (e, n) => sample(e, n) < 0.5;
for (const d of list) {
  const [ce, cn, hx, hy, axis, p] = d;
  const th = (axis * Math.PI) / 180;
  for (let k = 0; k < 16; k += 1) {
    const t = (2 * Math.PI * k) / 16;
    // a point on the plan's own superellipse at radius share s
    const c = Math.cos(t); const s = Math.sin(t);
    const lx = hx * Math.sign(c) * Math.abs(c) ** (2 / p);
    const ly = hy * Math.sign(s) * Math.abs(s) ** (2 / p);
    const at = (share, out = 0) => {
      const len = Math.hypot(lx, ly);
      const x = lx * share + (lx / len) * out; const y = ly * share + (ly / len) * out;
      return [ce + x * Math.cos(th) - y * Math.sin(th), cn + x * Math.sin(th) + y * Math.cos(th)];
    };
    assert.ok(cut(...at(0.8)), `dwelling ${ce}, ${cn}: earth drawn at 80 % of its plan (dir ${k})`);
    assert.ok(!cut(...at(FOOT_MIN)), `dwelling ${ce}, ${cn}: earth cut out to its foot (dir ${k})`);
    checks += 2;
    // 2 m out stays uncut unless another dwelling is nearer than that
    const far = at(1, 2);
    if (list.every((o) => o === d || dwellingDistance(o, ...far) > 0.5)) {
      assert.ok(!cut(...far), `dwelling ${ce}, ${cn}: earth cut 2 m outside it (dir ${k})`);
      checks += 1;
    }
  }
  assert.ok(cut(ce, cn), `dwelling ${ce}, ${cn}: earth drawn at its centre`);
}

// texture
assert.equal(texture.unpackAlignment, 1, 'mask rows must upload at 1-byte alignment');
assert.equal(texture.format, THREE.RedFormat);
assert.equal(texture.type, THREE.UnsignedByteType);
assert.equal(texture.magFilter, THREE.LinearFilter);
assert.equal(texture.minFilter, THREE.LinearFilter);
assert.equal(texture.generateMipmaps, false);
assert.equal(data.length, width * height);
assert.ok(texelM <= 0.5 + 1e-9, `texel ${texelM} m`);
assert.ok(width * height < 1.2e6, `mask ${width} x ${height} is over its budget`);

// shader
const src = fs.readFileSync(new URL('renderers/web/js/yards.js', root), 'utf8');
assert.match(src, /#ifdef YARD_DWELLINGS\s*\nuniform sampler2D uDwell;\s*\nuniform vec4 uDwellBox;\s*\n#endif/,
  'YARD_HEAD declares the cut\'s uniforms under its define');
assert.match(src, /replace\('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>\\n\$\{DWELLING_CUT\}`\)/,
  'the cut is spliced at the clipping planes');
assert.match(src, /if \(dwell\) mat\.defines = \{ \.\.\.\(mat\.defines \?\? \{\}\), YARD_DWELLINGS: '' \}/);
assert.equal(dwellingMask([]), null);
assert.equal(dwellingMask([{ ground: { treatment: 'worn_earth' } }]), null);
for (const f of fs.readdirSync(new URL('data/enclosures/', root)).filter((x) => x.endsWith('.json') && x !== 'index.json')) {
  const r = read(`data/enclosures/${f}`);
  assert.equal(dwellingsOf([r]).length, 0, `${f} states dwellings`);
}

console.log(`yard dwelling cut OK — ${list.length} dwellings, mask ${width} x ${height} at ${texelM} m, ${checks} checks`);
