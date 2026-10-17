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
 * The answers are a synthetic field (a hash of the texel's point), because the
 * question here is the keeper's arithmetic, not the town's; the town's own tile,
 * asked of the pool, is held to `nearField.build` at every critic station by
 * `tools/measure_near_field.mjs --walk`. `--self-test` breaks the keeper three
 * ways — a texel centre a texel off, a wrap a texel off, a strip not asked —
 * and requires each to be refused.
 */
import { FIELD_SPEC, fieldKeeper, buildField, sampleField, fieldWrap }
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

function makeKeeper({ off = 0, skip = false } = {}) {
  return fieldKeeper({
    spec: SPEC,
    // A reply that comes home later, as the pool's does.
    ask: () => new Promise((r) => setTimeout(() => r(null), 0)),
    finish(_got, { i0, j0, w, h }, e0, n0, tx, cls, height) {
      if (skip && w < size) return;
      const o = [0, 0, 0];
      for (let j = 0; j < h; j++) {
        for (let i = 0; i < w; i++) {
          at(e0 + (i0 + i + 0.5 + off) * tx, n0 + (j0 + j + 0.5) * tx, o);
          const k = j * w + i;
          cls[2 * k] = o[0]; cls[2 * k + 1] = o[1]; height[k] = o[2];
        }
      }
    },
  });
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
  k.update(0, 0);
  await k.settled();
  for (const [e, n, burst] of route()) {
    const before = k.stats.texels;
    k.update(e, n);
    if (burst) continue;
    await k.settled();
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

if (process.argv.includes('--self-test')) {
  const cases = [
    ['a texel centre a texel off', { off: 1 }, 0],
    ['a wrap a texel off', {}, 1],
    ['a strip not asked', { skip: true }, 0],
  ];
  let ok = true;
  for (const [what, opts, wrapOff] of cases) {
    const r = await walk(opts, wrapOff);
    console.log(`${r.bad.length ? 'refused' : 'PASSED (wrong)'}: ${what}${r.bad.length ? ` — ${r.bad[0]}` : ''}`);
    if (!r.bad.length) ok = false;
  }
  process.exit(ok ? 0 : 1);
}

const r = await walk();
for (const b of r.bad.slice(0, 12)) console.log(`FAIL ${b}`);
console.log(`${r.stats.recentres} re-centres landed (${r.stats.whole} whole), ${r.stats.texels} texels asked; `
  + `${r.bad.length ? `${r.bad.length} disagreement(s)` : 'the kept tile is the built tile after every one'}`);
process.exit(r.bad.length ? 1 : 0);
