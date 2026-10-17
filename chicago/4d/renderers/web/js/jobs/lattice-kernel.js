/**
 * flora.js's lattice walk as a pure typed-array kernel (T-2604, the first piece of
 * T-2601's flora re-deal in the job pool).
 *
 * A flora pass walks the world-anchored lattice around the camera — every cell the
 * ring and the view cone can reach, each slot's stratified deal rank `u`, its
 * jittered position and the xorshift stream its placement goes on drawing from —
 * and then asks each slot the deal's questions (zone, water, floors, heights). The
 * walk is a third of what a pass spends at the throttled phone profile (T-2604's
 * reading: `scatter` 2.2 s of the 7.5 s of flora self time over a walk and a turn),
 * and it reads nothing but numbers, so it can run on a worker while the main thread
 * draws. This is that walk: camera and layer in, one slot per entry out.
 *
 * **It is `scatter` in flora.js, slot for slot.** That generator is still what every
 * one-frame pass runs, unchanged; a SPREAD pass (flora.js `runPass`) sends its walks
 * here and deals the slots that come back, so the two must agree to the last bit of
 * every double and every stream. They are two texts because a module worker cannot
 * import flora.js (it imports three, a bare specifier), and flora.js's `hash3`,
 * `stratum` and their helpers cannot move here, because a dozen tools read them out
 * of flora.js's own source. `tools/check_lattice_kernel.mjs` holds the two together:
 * it slices `scatter` and its helpers out of flora.js, walks both on fixtures and on
 * random cameras of every layer and draw, and refuses a single differing slot.
 *
 * What it does NOT do is the aerial frustum test (`cone.planes`): that asks the
 * terrain for a height, which lives on the main thread, so flora.js applies it to
 * the slots that come back, in the same order and at the same point of the walk.
 *
 * It imports nothing, for the reason spatial-kernel.js gives.
 */

// flora.js's constants, by the same names (check_lattice_kernel.mjs compares them).
const CONE_KEEP_M = 3.5;
const STRAT_SALT = 0x7f4a7c15;
const STRAT_BLOCK_SHIFT = 2;

/** Exported for zone-kernel.js `fieldRect` (T-2707), which keeps the verge's weeds by it. */
export function hash3(a, b, c) {
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ Math.imul(c, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

function frac(x) { return x - Math.floor(x); }

function feistel(x, half, key) {
  const mask = (1 << half) - 1;
  let l = (x >>> half) & mask;
  let r = x & mask;
  for (let i = 0; i < 4; i++) {
    const t = l ^ (hash3(r, key, i + 1) & mask);
    l = r;
    r = t;
  }
  return ((l << half) | r) >>> 0;
}

function stratum(idx, n, half, key, phase) {
  let x = idx;
  for (let guard = 0; guard < 24; guard++) {
    x = feistel(x, half, key);
    if (x < n) return frac((x + 0.5) / n + phase);
  }
  return frac((idx + 0.5) / n + phase);
}

function spread16(n) {
  let x = n & 0xffff;
  x = (x | (x << 8)) & 0x00ff00ff;
  x = (x | (x << 4)) & 0x0f0f0f0f;
  x = (x | (x << 2)) & 0x33333333;
  x = (x | (x << 1)) & 0x55555555;
  return x >>> 0;
}

function morton(c, r) {
  return ((spread16(r + 0x8000) << 1) | spread16(c + 0x8000)) >>> 0;
}

function vdc(i) {
  let x = i >>> 0;
  x = ((x & 0x55555555) << 1) | ((x >>> 1) & 0x55555555);
  x = ((x & 0x33333333) << 2) | ((x >>> 2) & 0x33333333);
  x = ((x & 0x0f0f0f0f) << 4) | ((x >>> 4) & 0x0f0f0f0f);
  x = ((x & 0x00ff00ff) << 8) | ((x >>> 8) & 0x00ff00ff);
  return (((x >>> 16) | (x << 16)) >>> 0) / 4294967296;
}

function blockPhase(c, r, n, globalShift) {
  return frac(globalShift + vdc(morton(c, r)) / n);
}

function stratumHalf(n) {
  let bits = 1;
  while ((1 << bits) < n) bits++;
  return (bits + 1) >> 1;
}

/** One xorshift32 step: flora.js `rngFrom`'s state update. */
function xorshift(s) {
  s ^= s << 13; s >>>= 0;
  s ^= s >>> 17;
  s ^= s << 5; s >>>= 0;
  return s;
}

/**
 * @param {object} job
 * @param {number} job.camE @param {number} job.camN  the pass's centre
 * @param {number} job.cell @param {number} job.perCell @param {number} job.radius
 * @param {number} job.inner @param {number} job.salt @param {string} job.draw
 *        `scatter`'s own arguments, by the same names
 * @param {{fe: number, fn: number, cos: number, margin?: number}|null} job.cone
 *        the horizontal view cone; its `planes`, if any, are the caller's to apply
 * @returns {{e: Float64Array, n: Float64Array, d: Float64Array, u: Float64Array,
 *   cellSeed: Uint32Array, rng: Uint32Array, rowEnd: Uint32Array}} one entry per
 *   slot the ring and the cone keep, in `scatter`'s order: its position, its
 *   distance from the centre, its deal rank, its cell's seed and the state of its
 *   stream after the two jitter draws (`rngFrom(rng[i])` goes on from there).
 *   `rowEnd[k]` is how many slots the first k + 1 rows of cells hold, so a caller
 *   can yield where `scatter` yields.
 */
export function latticeSlots({ camE, camN, cell, perCell, radius, inner, salt, draw, cone }) {
  const c0 = Math.floor((camE - radius) / cell);
  const c1 = Math.ceil((camE + radius) / cell);
  const r0 = Math.floor((camN - radius) / cell);
  const r1 = Math.ceil((camN + radius) / cell);
  const sub = Math.max(1, Math.round(Math.sqrt(perCell)));
  const rr = radius * radius;
  const ri = inner * inner;
  const strata = draw === 'strata';
  const wild = draw === 'wild';
  const shiftBits = STRAT_BLOCK_SHIFT;
  const span = 1 << shiftBits;
  const nSlots = span * span * perCell;
  const half = stratumHalf(nSlots);
  const globalShift = hash3(salt, STRAT_SALT, 0x9e3779b9) / 4294967296;
  const halfDiag = cell * Math.SQRT1_2;
  const margin2 = cone ? 2 * (cone.margin ?? 0) : 0;

  // Sized to the bounding square, the most the walk can keep, and trimmed at the end.
  const most = (c1 - c0 + 1) * (r1 - r0 + 1) * perCell;
  const E = new Float64Array(most);
  const N = new Float64Array(most);
  const D = new Float64Array(most);
  const U = new Float64Array(most);
  const SEED = new Uint32Array(most);
  const RNG = new Uint32Array(most);
  const rowEnd = new Uint32Array(r1 - r0 + 1);
  let m = 0;

  for (let r = r0; r <= r1; r++) {
    const ny0 = r * cell - camN, ny1 = (r + 1) * cell - camN;
    const ny = ny0 > 0 ? ny0 : ny1 < 0 ? -ny1 : 0;
    const fy = Math.max(Math.abs(ny0), Math.abs(ny1));
    for (let c = c0; c <= c1; c++) {
      const nx0 = c * cell - camE, nx1 = (c + 1) * cell - camE;
      const nx = nx0 > 0 ? nx0 : nx1 < 0 ? -nx1 : 0;
      if (nx * nx + ny * ny > rr) continue;
      const fx = Math.max(Math.abs(nx0), Math.abs(nx1));
      if (fx * fx + fy * fy < ri) continue;
      if (cone) {
        const ce = (c + 0.5) * cell - camE, cn = (r + 0.5) * cell - camN;
        const cd = Math.hypot(ce, cn);
        if (cd - halfDiag > CONE_KEEP_M) {
          const low = cone.cos >= 0 ? (cd - halfDiag) * cone.cos : (cd + halfDiag) * cone.cos;
          if (ce * cone.fe + cn * cone.fn + halfDiag < low - margin2 - 1e-6) continue;
        }
      }
      const cellSeed = hash3(c, r, salt);
      let blockHash = 0, shift = 0, base = 0, cellPhase = 0;
      if (strata) {
        const bc = c >> shiftBits;
        const br = r >> shiftBits;
        blockHash = hash3(bc, br, salt ^ STRAT_SALT);
        shift = blockPhase(bc, br, nSlots, globalShift);
        base = ((c - ((c >> shiftBits) << shiftBits)) * span
          + (r - ((r >> shiftBits) << shiftBits))) * perCell;
      } else {
        cellPhase = blockPhase(c, r, perCell, globalShift);
      }
      for (let k = 0; k < perCell; k++) {
        // rngFrom's seed rule, then its two jitter draws.
        let s = hash3(cellSeed, k, 0x68bc21eb) >>> 0 || 1;
        s = xorshift(s);
        const je = s / 4294967296;
        s = xorshift(s);
        const jn = s / 4294967296;
        const u = strata
          ? stratum(base + k, nSlots, half, blockHash, shift)
          : frac(k / perCell + cellPhase);
        const sx = k % sub;
        const sy = (k / sub) | 0;
        const e = (c + (wild ? je : (sx + je) / sub)) * cell;
        const n = (r + (wild ? jn : (sy + jn) / sub)) * cell;
        const d2 = (e - camE) ** 2 + (n - camN) ** 2;
        if (d2 > rr || d2 < ri) continue;
        const d = Math.sqrt(d2);
        if (cone && d > CONE_KEEP_M
          && ((e - camE) * cone.fe + (n - camN) * cone.fn) < d * cone.cos - margin2) continue;
        E[m] = e; N[m] = n; D[m] = d; U[m] = u; SEED[m] = cellSeed; RNG[m] = s;
        m++;
      }
    }
    rowEnd[r - r0] = m;
  }
  return { e: E.slice(0, m), n: N.slice(0, m), d: D.slice(0, m), u: U.slice(0, m),
    cellSeed: SEED.slice(0, m), rng: RNG.slice(0, m), rowEnd };
}
