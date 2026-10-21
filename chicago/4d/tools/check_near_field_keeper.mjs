/**
 * T-2707 — THE KEPT FIELD TILE IS THE BUILT ONE, a strip at a time.
 *
 *   node tools/check_near_field_keeper.mjs [--self-test]
 *
 * `near-field.js` `fieldKeeper` keeps the near deal's field tile around a walker
 * and, on a re-centre, re-rasterises only the strip the step exposed, writing it
 * where the strip that fell off stood (a toroidal tile). This holds it, with no
 * browser and no town, to `buildField` — the whole tile asked at once — over a
 * walk that crosses every kind of re-centre (east, north, west, south, the four
 * diagonals, a jump of a whole tile, two steps queued behind one in flight):
 *
 *   1. after every landing the kept tile, read through its wrap, is the built
 *      tile at the same origin, byte for byte and float for float;
 *   2. `sampleField` reads the two the same at points across the tile;
 *   3. a straight step re-asks a quarter of the tile, a diagonal 7/16, the
 *      first and the jump the whole of it, and nothing else;
 *   4. `written` names exactly the texels the landing wrote.
 *
 * T-2969: the walk is taken three times — a whole tile landed in one slice (the
 * before), a band per slice (`sliceMs: 0`) and at the page's own budget — and
 * the pool's reply carries the heights, so a band read from the wrong rows of
 * it is a tile unlike the built one. A whole landing in bands takes exactly
 * size / LAND_BAND_ROWS slices and in one slice exactly one; and a tile adopted
 * while a whole one is still landing in bands is the adopted tile, the landing
 * dropped.
 *
 * The answers are a synthetic field (a hash of the texel's point), because the
 * question here is the keeper's arithmetic, not the town's; the town's own tile,
 * asked of the pool, is held to `nearField.build` at every critic station by
 * `tools/measure_near_field.mjs --walk`. `--self-test` breaks the keeper three
 * ways — a texel centre a texel off, a wrap a texel off, a strip not asked —
 * and a fourth, a whole tile landed in one slice where bands were asked for,
 * and requires each to be refused.
 */
import { FIELD_SPEC, LAND, LAND_BAND_ROWS, fieldKeeper, buildField, sampleField, fieldWrap }
  from '../renderers/web/js/near-field.js';

const SPEC = FIELD_SPEC;
const { size, texel, recentre } = SPEC;

function h32(a, b) {
  let h = Math.imul(a | 0, 0x27d4eb2d) ^ Math.imul(b | 0, 0x165667b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  return (h ^ (h >>> 13)) >>> 0;
}
/** The synthetic field: a class and flags from the point's hash, and a height
 *  that moves with the point, so a texel asked in the wrong place reads wrong. */
function at(e, n, out = [0, 0, 0]) {
  const h = h32(Math.round(e * 64), Math.round(n * 64));
  out[0] = h % 12;
  out[1] = (h >>> 8) & 15;
  out[2] = Math.sin(e * 0.37) * 3 + Math.cos(n * 0.21) * 2 + e * 1e-3;
  return out;
}

function makeKeeper({ off = 0, skip = false, sliceMs, liar = false } = {}) {
  const k = fieldKeeper({
    spec: SPEC,
    ...(sliceMs === undefined ? {} : { sliceMs: liar ? Infinity : sliceMs }),
    // A reply that comes home later, as the pool's does, carrying the heights
    // (row by row northward), which `finish` takes from it.
    ask: ({ i0, j0, w, h }, e0, n0, tx) => new Promise((r) => setTimeout(() => {
      const y = new Float32Array(w * h);
      const o = [0, 0, 0];
      for (let j = 0; j < h; j++) {
        for (let i = 0; i < w; i++) y[j * w + i] = at(e0 + (i0 + i + 0.5 + off) * tx, n0 + (j0 + j + 0.5) * tx, o)[2];
      }
      r({ y });
    }, 0)),
    finish(got, { i0, j0, w, h }, e0, n0, tx, cls, height) {
      if (skip && w < size) return;
      const o = [0, 0, 0];
      for (let j = 0; j < h; j++) {
        for (let i = 0; i < w; i++) {
          at(e0 + (i0 + i + 0.5 + off) * tx, n0 + (j0 + j + 0.5) * tx, o);
          const k = j * w + i;
          cls[2 * k] = o[0]; cls[2 * k + 1] = o[1]; height[k] = got.y[k];
        }
      }
    },
  });
  // `liar`: bands asked for, and the keeper quietly landing in one slice.
  if (liar) k.asked = sliceMs;
  return k;
}

/** Every way the kept tile can differ from the built one, counted. */
function compare(kept, wrapOff = 0) {
  const built = buildField(at, kept.e0, kept.n0, SPEC);
  const wi = kept.wi + wrapOff, wj = kept.wj;
  let texels = 0;
  for (let j = 0; j < size; j++) {
    for (let i = 0; i < size; i++) {
      const k = ((j + wj) % size) * size + (i + wi) % size;
      const b = j * size + i;
      if (kept.cls[2 * k] !== built.cls[2 * b] || kept.cls[2 * k + 1] !== built.cls[2 * b + 1]
        || kept.height[k] !== built.height[b]) texels++;
    }
  }
  const view = { ...kept, wi };
  let samples = 0;
  const a = [0, 0, 0], b = [0, 0, 0];
  for (let s = 0; s < 4000; s++) {
    const e = kept.e0 + ((h32(s, 7) % 1e6) / 1e6) * size * texel;
    const n = kept.n0 + ((h32(s, 11) % 1e6) / 1e6) * size * texel;
    sampleField(view, e, n, a);
    sampleField(built, e, n, b);
    if (a[0] !== b[0] || a[1] !== b[1] || a[2] !== b[2]) samples++;
  }
  return { texels, samples };
}

/** The walk: [east, north] camera points, each a step from the last. */
function route() {
  const pts = [];
  let e = 3.3, n = -2.1;
  const go = (de, dn, steps) => { for (let s = 0; s < steps; s++) { e += de; n += dn; pts.push([e, n, false]); } };
  go(1, 0, 20); go(0, 1, 20); go(-1, 0, 20); go(0, -1, 20);
  go(1, 1, 12); go(-1, 1, 12); go(-1, -1, 12); go(1, -1, 12);
  pts.push([e + 96, n - 40, false]);
  // Three steps in one breath: the middle one is queued and then superseded.
  pts.push([e + 104, n - 40, true], [e + 112, n - 40, true], [e + 120, n - 32, false]);
  return pts;
}

async function walk(opts = {}, wrapOff = 0) {
  const k = makeKeeper(opts);
  const bad = [];
  let prev = null;
  // T-2969: every whole landing's slices, against the count its budget sets.
  const budget = k.asked ?? k.sliceMs ?? LAND.sliceMs;
  const want = budget === 0 ? size / LAND_BAND_ROWS : budget === Infinity ? 1 : null;
  const sliced = async () => {
    const whole = k.stats.whole, slices = k.stats.slices;
    await k.settled();
    const got = k.stats.slices - slices;
    if (want !== null && k.stats.whole > whole && got !== want) {
      bad.push(`a whole tile landed in ${got} slice(s), not ${want}`);
    }
  };
  k.update(0, 0);
  await sliced();
  for (const [e, n, burst] of route()) {
    const before = k.stats.texels;
    k.update(e, n);
    if (burst) continue;
    await sliced();
    const t = k.tile;
    const c = compare(t, wrapOff);
    if (c.texels || c.samples) bad.push(`at (${e.toFixed(1)}, ${n.toFixed(1)}): ${c.texels} texels and ${c.samples} samples differ from the built tile`);
    if (prev && (t.e0 !== prev.e0 || t.n0 !== prev.n0)) {
      const di = Math.abs(t.e0 - prev.e0) / recentre, dj = Math.abs(t.n0 - prev.n0) / recentre;
      const asked = k.stats.texels - before;
      // Only a lone step's strip has one right size; a burst lands its own.
      const want = di >= 4 || dj >= 4 ? size * size
        : size * size - (size - di * 64) * (size - dj * 64);
      if (di <= 1 && dj <= 1 && asked !== want) bad.push(`step (${di}, ${dj}) re-asked ${asked} texels, not ${want}`);
      // `changed` is exactly the texels the landing wrote.
      const marked = new Uint8Array(size * size);
      let area = 0;
      for (const r of k.written) {
        for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) marked[y * size + x]++;
        area += r.w * r.h;
      }
      if (di <= 1 && dj <= 1 && (area !== want || marked.some((m) => m > 1))) bad.push(`step (${di}, ${dj}): written covers ${area} texels, not ${want} once each`);
    }
    prev = t;
  }
  const w = fieldWrap(prev.e0, prev.n0, SPEC);
  if (w.wi !== prev.wi || w.wj !== prev.wj) bad.push('the tile\'s wrap is not its origin\'s');
  return { bad, stats: k.stats };
}

/** T-2969: a whole tile adopted while another is landing in bands. */
async function adoptMidLanding() {
  const k = makeKeeper({ sliceMs: 0 });
  const bad = [];
  k.update(0, 0);
  await k.settled();
  const slices = k.stats.slices;
  k.update(500, 500);
  // Let the reply come home and the first bands land, then adopt.
  while (k.stats.slices < slices + 3) await new Promise((r) => setTimeout(r, 0));
  const built = buildField(at, 1000, 1000, SPEC);
  k.adopt(built);
  await k.settled();
  const t = k.tile;
  if (t.e0 !== 1000 || t.n0 !== 1000) bad.push(`the adopted tile was replaced by the landing at (${t.e0}, ${t.n0})`);
  else {
    const c = compare(t);
    if (c.texels || c.samples) bad.push(`adopted mid-landing: ${c.texels} texels differ from the built tile`);
  }
  if (k.stats.whole !== 1) bad.push(`${k.stats.whole - 1} landing(s) written after the adopt`);
  return bad;
}

if (process.argv.includes('--self-test')) {
  const cases = [
    ['a texel centre a texel off', { off: 1 }, 0],
    ['a wrap a texel off', {}, 1],
    ['a strip not asked', { skip: true }, 0],
    ['a whole tile landed in one slice where bands were asked for', { sliceMs: 0, liar: true }, 0],
  ];
  let ok = true;
  for (const [what, opts, wrapOff] of cases) {
    const r = await walk(opts, wrapOff);
    console.log(`${r.bad.length ? 'refused' : 'PASSED (wrong)'}: ${what}${r.bad.length ? ` — ${r.bad[0]}` : ''}`);
    if (!r.bad.length) ok = false;
  }
  process.exit(ok ? 0 : 1);
}

let failed = 0;
for (const [what, opts] of [['one slice a landing', { sliceMs: Infinity }],
  ['a band a slice', { sliceMs: 0 }], ['the page\'s budget', {}]]) {
  const r = await walk(opts);
  for (const b of r.bad.slice(0, 12)) console.log(`FAIL ${what}: ${b}`);
  console.log(`${what}: ${r.stats.recentres} re-centres landed (${r.stats.whole} whole) in ${r.stats.slices} slices, `
    + `${r.stats.texels} texels asked; `
    + `${r.bad.length ? `${r.bad.length} disagreement(s)` : 'the kept tile is the built tile after every one'}`);
  failed += r.bad.length;
}
const adopted = await adoptMidLanding();
for (const b of adopted) console.log(`FAIL ${b}`);
console.log(`adopted while a whole tile landed in bands: ${adopted.length ? 'WRONG' : 'the adopted tile, the landing dropped'}`);
failed += adopted.length;
process.exit(failed ? 1 : 0);
