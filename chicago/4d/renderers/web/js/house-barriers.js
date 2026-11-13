/**
 * house-barriers.js — what a 1904 Prairie Avenue house builds outside its walls that a person
 * must walk round (T-3554).
 *
 * The owner, 2026-11-12: "when people walk they dont cut themselves and swipe though a sidewalk
 * their dresses are wide ... their path sometimes cuts through a wall or barrier people should
 * not be able to walk through walls or barriers". A house's footprint keeps people out of its
 * walls (walker.js); its stoop, area and coping walls, iron railings and bays stand outside that
 * footprint. tools/prairie_barriers.py reads them off each house model (whatever the model builds
 * between a knee and a head over the ground) and tools/derive_doors_scene.py writes them into
 * data/humans/doors_1904.json as a `barrier` per house: plan rectangles of 0.1 m cells, four
 * integers each (i0 i1 j0 j1, half-open), cell (i, j) centred on u0 + i*cell, v0 + j*cell of the
 * model's plan (u = x, v = -z), turned into local E/N by the house's placement.
 *
 * The owner, 2026-11-13, of a maid standing half inside the bottom steps of a front stoop: "she
 * cannot stand where there are stairs like that, no one should be able to". A stoop's treads are
 * barriers from its bottom one up (prairie_barriers.py KNEE_M), the back yards' stoops and 1835's
 * street-front stoops are rows of their own (derive_doors_scene.py), and `clearOf` finds the
 * nearest place a body stands clear of them all: human-days.js planDay moves every standing place
 * there, and human-spacing.js steps anyone who still stands in one out of it.
 *
 * createHouseBarriers(rows) -> { near(e, n, r) , clearLeg(a, b, r), clearOf(e, n, r, ok), count }
 *   near      whether a body at (e, n) comes within r metres of a barrier
 *   clearLeg  whether walking a -> b ({e, n}) keeps r metres off every barrier the whole way
 *   clearOf   null where a body at (e, n) stands r metres off every barrier; else the nearest
 *             place ({e, n}) that does (and that `ok` allows), or null when none is in reach
 *
 * Plain math, no renderer dependency; tools/test_house_barriers.mjs runs it in node.
 */

/** A skirt's half-width: how far a walk keeps off a barrier (prairie_barriers.py SKIRT_M less
 *  the half-cell the data is read on). */
export const BARRIER_SKIRT_M = 0.3;
/** T-3554: where a body STANDS (a talk, a job, a wait), it keeps a skirt's hem off every barrier. */
export const BARRIER_STAND_M = 0.35;
/** clearOf looks this far out, a ring every CLEAR_STEP_M, CLEAR_BEARINGS places a ring. */
export const CLEAR_REACH_M = 4;
const CLEAR_STEP_M = 0.1;
const CLEAR_BEARINGS = 24;
const BAND_M = 1;          // the rectangles are filed by bands of u this deep
const STEP_M = 0.1;        // a leg is asked at points this far apart

function house(row) {
  const b = row?.barrier, pl = row?.placement;
  if (!b || !pl || typeof b.rects !== 'string' || !Number.isFinite(b.cell)) return null;
  const k = b.rects.trim().split(/\s+/).map(Number);
  if (k.length < 4 || k.length % 4 || k.some((x) => !Number.isInteger(x))) return null;
  const c = b.cell, n = k.length / 4;
  // Each rectangle in plan metres: [u0, u1, v0, v1].
  const rects = new Float64Array(n * 4);
  let ua = Infinity, ub = -Infinity, va = Infinity, vb = -Infinity;
  for (let r = 0; r < n; r++) {
    const u0 = b.u0 + (k[r * 4] - 0.5) * c, u1 = b.u0 + (k[r * 4 + 1] - 0.5) * c;
    const v0 = b.v0 + (k[r * 4 + 2] - 0.5) * c, v1 = b.v0 + (k[r * 4 + 3] - 0.5) * c;
    rects.set([u0, u1, v0, v1], r * 4);
    ua = Math.min(ua, u0); ub = Math.max(ub, u1); va = Math.min(va, v0); vb = Math.max(vb, v1);
  }
  const bands = new Map();
  for (let r = 0; r < n; r++) {
    for (let q = Math.floor(rects[r * 4] / BAND_M); q <= Math.floor(rects[r * 4 + 1] / BAND_M); q++) {
      if (!bands.has(q)) bands.set(q, []);
      bands.get(q).push(r);
    }
  }
  const th = ((pl.rotation_deg ?? 0) * Math.PI) / 180;
  return { e0: pl.local_e, n0: pl.local_n, cos: Math.cos(th), sin: Math.sin(th), rects, bands, box: [ua, ub, va, vb],
    seen: new Uint32Array(n), mark: 0 };
}

/** (e, n) in a house's plan: the inverse of walker.js's clockwise compass turn. */
function toPlan(h, e, n) {
  const de = e - h.e0, dn = n - h.n0;
  return [de * h.cos - dn * h.sin, de * h.sin + dn * h.cos];
}

let ask = 0;   // each question's stamp, so nothing is asked twice in it without a Set
function nearIn(h, e, n, r) {
  const [u, v] = toPlan(h, e, n);
  const [ua, ub, va, vb] = h.box;
  if (u < ua - r || u > ub + r || v < va - r || v > vb + r) return false;
  const R = h.rects, seen = h.seen;
  for (let q = Math.floor((u - r) / BAND_M); q <= Math.floor((u + r) / BAND_M); q++) {
    for (const k of h.bands.get(q) ?? []) {
      if (seen[k] === ask) continue;
      seen[k] = ask;
      const du = Math.max(R[k * 4] - u, 0, u - R[k * 4 + 1]);
      const dv = Math.max(R[k * 4 + 2] - v, 0, v - R[k * 4 + 3]);
      if (du * du + dv * dv < r * r || (du === 0 && dv === 0)) return true;
    }
  }
  return false;
}

/**
 * @param {object[]} rows  data/humans/doors_1904.json `structures` and `barriers` rows
 */
export function createHouseBarriers(rows = []) {
  const houses = (rows ?? []).map(house).filter(Boolean);
  // A coarse index of the houses by where they stand, 25 m cells of E/N.
  const G = 25, grid = new Map();
  for (const h of houses) {
    const [ua, ub, va, vb] = h.box;
    const corners = [[ua, va], [ub, va], [ub, vb], [ua, vb]].map(([u, v]) => [h.e0 + u * h.cos + v * h.sin, h.n0 - u * h.sin + v * h.cos]);
    const es = corners.map((p) => p[0]), ns = corners.map((p) => p[1]);
    for (let i = Math.floor(Math.min(...es) / G); i <= Math.floor(Math.max(...es) / G); i++) {
      for (let j = Math.floor(Math.min(...ns) / G); j <= Math.floor(Math.max(...ns) / G); j++) {
        const key = i * 100003 + j;
        if (!grid.has(key)) grid.set(key, []);
        grid.get(key).push(h);
      }
    }
  }
  function near(e, n, r = BARRIER_SKIRT_M) {
    if (!houses.length || !Number.isFinite(e) || !Number.isFinite(n)) return false;
    ask = (ask + 1) >>> 0 || 1;
    for (let i = Math.floor((e - r) / G); i <= Math.floor((e + r) / G); i++) {
      for (let j = Math.floor((n - r) / G); j <= Math.floor((n + r) / G); j++) {
        for (const h of grid.get(i * 100003 + j) ?? []) {
          if (h.mark === ask) continue;
          h.mark = ask;
          if (nearIn(h, e, n, r)) return true;
        }
      }
    }
    return false;
  }
  function clearLeg(a, b, r = BARRIER_SKIRT_M) {
    if (!houses.length) return true;
    const L = Math.hypot(b.e - a.e, b.n - a.n), steps = Math.max(1, Math.ceil(L / STEP_M));
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      if (near(a.e + (b.e - a.e) * t, a.n + (b.n - a.n) * t, r)) return false;
    }
    return true;
  }
  function clearOf(e, n, r = BARRIER_STAND_M, ok = null) {
    if (!houses.length || !near(e, n, r)) return null;
    // Out from (e, n), ring by ring; on each ring the bearings from north, so the answer is the
    // same on every load. A hair more than r, so the place found is not on the edge of it.
    for (let k = 1; k * CLEAR_STEP_M <= CLEAR_REACH_M + 1e-9; k++) {
      const d = k * CLEAR_STEP_M;
      let best = null;
      for (let b = 0; b < CLEAR_BEARINGS; b++) {
        const t = (2 * Math.PI * b) / CLEAR_BEARINGS;
        const q = { e: e + d * Math.sin(t), n: n + d * Math.cos(t) };
        if (near(q.e, q.n, r + 0.02) || (ok && !ok(q))) continue;
        best = q;
        break;
      }
      if (best) return best;
    }
    return null;
  }
  return { near, clearLeg, clearOf, count: houses.length, rects: houses.reduce((a, h) => a + h.rects.length / 4, 0) };
}
