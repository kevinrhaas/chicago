/**
 * flight-clearance.js — how high a flight must be to pass over what stands in its way (T-3734).
 *
 * The owner, 2026-11-23: "when you fly on the jaunts in 1904 and probably others you will
 * often clip fly though a building or chimney, when you fly if you run into a thing you
 * should fly over or around". Both of the flights a jaunt makes knew only the ground: the
 * timed glide (travel.glide) flew a fixed arc, none at all for a hop under 30 m, and the
 * steered Fly ride climbed while moving forward and came down an 18° slope across whatever
 * stood in front of the stand. The walker's own fly mode keeps 1.2 m off the terrain and
 * nothing else, which is right for a visitor flying by hand and wrong for a ride.
 *
 * So a flight asks this module, once when it sets off and a few times a second while it is
 * steered, how high the eye must be over a point: the top of the tallest thing drawn within
 * REACH_M of it (a building's whole drawn box, so its chimneys, towers and cresting), plus
 * ABOVE_M. The town is indexed once into coarse buckets of outlines and tops; nothing here
 * scans the town per frame, and the index is only rebuilt when the set of drawn structures
 * changes (a context city swapped for another detail, a building streamed in).
 *
 * Pure parts (the profile, the envelope) are exported for tools/test_flight_clearance.mjs.
 */

export const ABOVE_M = 3;     // the eye this far over the tallest point it passes
export const REACH_M = 3;     // … of anything this near its ground track (its walls and eaves)
export const END_M = 4;       // the stand a flight leaves or lands on is ground the walker stood on
export const SLOPE = 0.7;     // m of climb per m ahead: it rises before it reaches a building
const BUCKET_M = 32;

/** Distance from (e, n) to the polygon `pts` ([[e, n], …]); 0 inside. */
export function distanceToPolygon(e, n, pts) {
  let inside = false, best = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ae, an] = pts[j], [be, bn] = pts[i];
    if ((bn > n) !== (an > n) && e < ((ae - be) * (n - bn)) / (an - bn) + be) inside = !inside;
    const de = be - ae, dn = bn - an, len2 = de * de + dn * dn;
    const t = len2 > 0 ? Math.max(0, Math.min(1, ((e - ae) * de + (n - an) * dn) / len2)) : 0;
    best = Math.min(best, Math.hypot(e - (ae + de * t), n - (an + dn * t)));
  }
  return inside ? 0 : best;
}

/**
 * The index. `sources()` returns the obstacles as [{ pts: [[e, n], …], top }] where `top` is
 * the world height of the obstacle's highest point; `stamp()` a cheap value that changes when
 * they do. `ground(e, n)` is the walker's own surface, so the answer is in the same terms as a
 * flight's altitude (eye above the ground under it).
 */
export function createSkyline({ sources, stamp = () => 0, ground }) {
  let buckets = null, built = undefined;
  function build() {
    buckets = new Map();
    for (const o of sources() ?? []) {
      if (!o?.pts?.length || !Number.isFinite(o.top)) continue;
      let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
      for (const [e, n] of o.pts) { e0 = Math.min(e0, e); e1 = Math.max(e1, e); n0 = Math.min(n0, n); n1 = Math.max(n1, n); }
      if (![e0, e1, n0, n1].every(Number.isFinite)) continue;
      const rec = { pts: o.pts, top: o.top, e0: e0 - REACH_M, e1: e1 + REACH_M, n0: n0 - REACH_M, n1: n1 + REACH_M };
      for (let i = Math.floor(rec.e0 / BUCKET_M); i <= Math.floor(rec.e1 / BUCKET_M); i++) {
        for (let j = Math.floor(rec.n0 / BUCKET_M); j <= Math.floor(rec.n1 / BUCKET_M); j++) {
          const key = `${i},${j}`;
          let list = buckets.get(key);
          if (!list) buckets.set(key, list = []);
          list.push(rec);
        }
      }
    }
  }
  const out = {
    /** Rebuild if what is drawn has changed since the last flight. Call as a flight sets off. */
    refresh() {
      const now = stamp();
      if (buckets && now === built) return out;
      built = now;
      build();
      return out;
    },
    /** The eye height over the ground at (e, n) that clears everything within REACH_M; 0 if nothing. */
    needAt(e, n) {
      if (!buckets) out.refresh();
      const list = buckets.get(`${Math.floor(e / BUCKET_M)},${Math.floor(n / BUCKET_M)}`);
      if (!list) return 0;
      let top = -Infinity;
      for (const r of list) {
        if (r.top <= top || e < r.e0 || e > r.e1 || n < r.n0 || n > r.n1) continue;
        if (distanceToPolygon(e, n, r.pts) <= REACH_M) top = r.top;
      }
      if (top === -Infinity) return 0;
      const g = ground?.(e, n);
      return Math.max(0, top - (Number.isFinite(g) ? g : 0) + ABOVE_M);
    },
    get size() { let k = 0; for (const l of buckets?.values() ?? []) k += l.length; return k; },
  };
  return out;
}

/**
 * A flight's clearance along its ground track: `legs` are [[e, n], …] corners (from, via?, to).
 * Returns { length, step, need, lift } where need[i] is the eye height wanted at s = i * step
 * along the track (0 over the stands at either end) and lift[i] the envelope a camera can
 * fly: rising SLOPE m for every metre before a building and coming down as gently after it.
 */
export function clearanceProfile(needAt, legs, { step = 2, maxSamples = 1500 } = {}) {
  const lens = [];
  let length = 0;
  for (let i = 1; i < legs.length; i++) { const d = Math.hypot(legs[i][0] - legs[i - 1][0], legs[i][1] - legs[i - 1][1]); lens.push(d); length += d; }
  if (!(length > 0)) return { length: 0, step, need: [0], lift: [0] };
  const count = Math.min(maxSamples, Math.max(2, Math.ceil(length / step) + 1));
  const ds = length / (count - 1);
  const need = new Float32Array(count);
  for (let k = 0; k < count; k++) {
    const s = k * ds;
    if (s < END_M || s > length - END_M) continue;
    let at = s, leg = 0;
    while (leg < lens.length - 1 && at > lens[leg]) { at -= lens[leg]; leg++; }
    const t = lens[leg] > 0 ? Math.min(1, at / lens[leg]) : 0, a = legs[leg], b = legs[leg + 1];
    need[k] = needAt(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t);
  }
  return { length, step: ds, need, lift: envelope(need, ds) };
}

/** need dilated by SLOPE per metre both ways: lift[i] = max_j (need[j] - SLOPE |i - j| ds). O(n). */
export function envelope(need, ds, slope = SLOPE) {
  const n = need.length, lift = new Float32Array(n), fall = slope * ds;
  let run = 0;
  for (let i = 0; i < n; i++) { run = Math.max(need[i], run - fall); lift[i] = run; }
  run = 0;
  for (let i = n - 1; i >= 0; i--) { run = Math.max(need[i], run - fall); lift[i] = Math.max(lift[i], run); }
  return lift;
}

/** The profile's value at s metres along (linear between samples). */
export function profileAt(values, step, s) {
  if (!values?.length) return 0;
  const x = Math.max(0, Math.min(values.length - 1, s / step)), i = Math.floor(x), f = x - i;
  return i + 1 < values.length ? values[i] + (values[i + 1] - values[i]) * f : values[i];
}

/**
 * For a steered flight: the height wanted NOW so that the eye clears what lies `ahead` metres
 * on toward the stand, climbing at SLOPE — so it rises before it reaches a building. Points
 * within END_M of the stand are left out (the stand is ground the walker stands on).
 */
export function floorAhead(needAt, e, n, toE, toN, ahead, step = 3) {
  const horiz = Math.hypot(toE - e, toN - n);
  if (!(horiz > 0)) return 0;
  const ue = (toE - e) / horiz, un = (toN - n) / horiz, reach = Math.min(ahead, horiz - END_M);
  let floor = 0;
  for (let x = 0; x <= reach; x += step) floor = Math.max(floor, needAt(e + ue * x, n + un * x) - SLOPE * x);
  return floor;
}
