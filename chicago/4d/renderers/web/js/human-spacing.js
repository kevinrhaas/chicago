// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-spacing.js — no two people in one place, standing or walking, in any year (T-3504).
 *
 * The owner, 2026-11-08, of two figures on the 1812 parade, one inside the other: *"there are
 * two people occupying the same space? Prevent that"*. Where a record puts a person is data; two
 * records can name one point (a talk's knot did, for all its people, until human-days.js stood
 * them in a ring), a day's walk can end where someone already stands, and two people walking can
 * meet. So after every layer has moved its figures for the frame (humans.js, human-duties.js,
 * human-days.js), this pass keeps each pair of drawn figures at least MIN_M apart (a body's width
 * and a little), centre to centre, by a small offset of its own (`actor.spaceE/spaceN`, which
 * humans.js `place()` adds to where the figure is meant to be):
 *
 *   - a pair nearer than MIN_M is pushed apart along the line between them (a pair on one point,
 *     along a direction seeded by the two ids, so it is the same on every load); a walker takes
 *     WALKER_SHARE of the push and a stander the rest, so a walker steps round a stander;
 *   - a figure the visitor can see moves at most RATE_M_S (a step aside, not a jump); one not
 *     drawn is settled at once (ITERATIONS a frame), so a visitor coming up finds them apart;
 *   - an offset is never more than MAX_M, and never into a building (`blockedAt`, when known);
 *   - a walker lets its offset go again as it walks on (RELAX_M_S), where that brings no one
 *     nearer than MIN_M; a stander keeps it (letting it go would slide them over the ground);
 *   - a figure on a walked path with heights of its own (a tread, a sill: `standY`), towed by a
 *     team, seated or indoors is never moved, but others keep clear of it.
 *
 * Only figures within REACH_M of the visitor are spaced: no one further off is seen. Cost: a hash
 * of those figures into 1 m cells and a look at the nine cells about each, ~2 us a figure.
 * Nothing here knows three.js or the DOM; tools/test_human_spacing.mjs drives it with stand-ins.
 */

/** Centre to centre, metres: two shoulders' width and a little. */
export const MIN_M = 0.62;
export const MAX_M = 1.4;
export const RATE_M_S = 0.9;
export const RELAX_M_S = 0.35;
export const WALKER_SHARE = 0.85;
export const REACH_M = 160;
export const ITERATIONS = 4;
const CELL = 1;

function hashAngle(key) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < key.length; i++) { h ^= key.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return (h / 4294967296) * Math.PI * 2;
}

/** Whether the figure is walking now (its own walk, a path under way). */
const walking = (a) => (a.path ? !a.path.arrived : a.state === 'walking');
/** Whether the figure may be moved at all. */
const fixed = (a) => a.standY != null || !!a.tow || a.state === 'seated';

/**
 * @param {object} o
 * @param {{ actors: object[], isHeld?: Function, external?: Function, shown?: boolean }} o.humans
 * @param {() => {e:number, n:number} | null} [o.visitor]   where the eye stands (local ENU)
 * @param {(e:number, n:number) => boolean} [o.blockedAt] true inside a building or water
 */
export function createHumanSpacing({ humans, visitor = () => null, blockedAt = null } = {}) {
  const stats = { figures: 0, pairs: 0, moved: 0, worst_m: 0 };
  const where = (a) => ({ e: a.e + (a.spaceE ?? 0), n: a.n + (a.spaceN ?? 0) });

  function gather() {
    const v = visitor();
    const list = [];
    for (const a of humans.actors) {
      if (a.disposed || a.indoors || !a.root) continue;
      if (humans.isHeld?.(a)) continue;
      if (humans.external?.(a.personId) === a) continue;     // a driver on his seat
      if (v && Math.hypot(a.e - v.e, a.n - v.n) > REACH_M) continue;
      a.spaceE ??= 0; a.spaceN ??= 0;
      if (fixed(a) && (a.spaceE || a.spaceN)) { a.spaceE = 0; a.spaceN = 0; a.place?.(); }
      list.push(a);
    }
    return list;
  }

  function cells(list) {
    const grid = new Map();
    for (const a of list) {
      const p = where(a);
      const k = `${Math.floor(p.e / CELL)},${Math.floor(p.n / CELL)}`;
      if (!grid.has(k)) grid.set(k, []);
      grid.get(k).push(a);
    }
    return grid;
  }
  function neighbours(grid, p) {
    const ce = Math.floor(p.e / CELL), cn = Math.floor(p.n / CELL), out = [];
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
      const c = grid.get(`${ce + i},${cn + j}`);
      if (c) out.push(...c);
    }
    return out;
  }

  /** One pass: the pushes each figure wants, applied within its limit. Returns pairs too near. */
  function pass(list, dt, settle) {
    const grid = cells(list);
    const push = new Map();
    let pairs = 0;
    for (const a of list) {
      const pa = where(a);
      for (const b of neighbours(grid, pa)) {
        if (b === a || a.id > b.id) continue;
        const pb = where(b);
        let de = pa.e - pb.e, dn = pa.n - pb.n;
        let d = Math.hypot(de, dn);
        if (d >= MIN_M) continue;
        pairs++;
        if (d < 1e-4) { const t = hashAngle(`${a.id}|${b.id}`); de = Math.sin(t); dn = Math.cos(t); d = 0; }
        else { de /= d; dn /= d; }
        const fa = fixed(a), fb = fixed(b);
        if (fa && fb) continue;
        const wa = fa ? 0 : walking(a) ? WALKER_SHARE : 1 - WALKER_SHARE;
        const wb = fb ? 0 : walking(b) ? WALKER_SHARE : 1 - WALKER_SHARE;
        const sa = wa / (wa + wb), sb = wb / (wa + wb);
        const over = MIN_M - d + 0.005;
        if (sa) { const q = push.get(a) ?? { e: 0, n: 0 }; q.e += de * over * sa; q.n += dn * over * sa; push.set(a, q); }
        if (sb) { const q = push.get(b) ?? { e: 0, n: 0 }; q.e -= de * over * sb; q.n -= dn * over * sb; push.set(b, q); }
      }
    }
    for (const [a, q] of push) {
      let { e, n } = q;
      const len = Math.hypot(e, n);
      const seen = a.root.visible && a.inRange;
      if (seen && settle) continue;           // a drawn figure takes one step a frame
      const most = seen ? RATE_M_S * dt : Infinity;
      if (len > most) { e *= most / len; n *= most / len; }
      let se = a.spaceE + e, sn = a.spaceN + n;
      const off = Math.hypot(se, sn);
      if (off > MAX_M) { se *= MAX_M / off; sn *= MAX_M / off; }
      if (blockedAt && blockedAt(a.e + se, a.n + sn) && !blockedAt(a.e + a.spaceE, a.n + a.spaceN)) continue;
      a.spaceE = se; a.spaceN = sn;
      a.place?.();
      stats.moved++;
    }
    return { pairs, grid };
  }

  /** Walkers let their step aside go again, where that brings nobody too near. */
  function relax(list, grid, dt) {
    for (const a of list) {
      if (!(a.spaceE || a.spaceN) || fixed(a)) continue;
      const seen = a.root.visible && a.inRange;
      if (seen && !walking(a)) continue;
      const off = Math.hypot(a.spaceE, a.spaceN);
      const k = seen ? Math.max(0, off - RELAX_M_S * dt) / off : 0;
      const se = a.spaceE * k, sn = a.spaceN * k;
      const p = { e: a.e + se, n: a.n + sn };
      let clear = true;
      for (const b of neighbours(grid, p)) {
        if (b === a) continue;
        const q = where(b);
        if (Math.hypot(p.e - q.e, p.n - q.n) < MIN_M) { clear = false; break; }
      }
      if (!clear) continue;
      a.spaceE = Math.abs(se) < 1e-4 ? 0 : se;
      a.spaceN = Math.abs(sn) < 1e-4 ? 0 : sn;
      a.place?.();
    }
  }

  return {
    stats,
    /** One frame, after every layer that moves figures. */
    update(dt) {
      if (!humans || humans.shown === false || !(dt >= 0)) return;
      const list = gather();
      stats.figures = list.length;
      stats.moved = 0;
      let last = null;
      // Figures not drawn are settled at once; a few passes take a crowd apart.
      for (let i = 0; i < ITERATIONS; i++) {
        last = pass(list, dt, i > 0);
        if (!last.pairs) break;
      }
      relax(list, last ? cells(list) : new Map(), dt);
      // How near the nearest pair stands now (for the harness).
      let worst = Infinity, pairs = 0;
      const grid = cells(list);
      for (const a of list) {
        const pa = where(a);
        for (const b of neighbours(grid, pa)) {
          if (b === a || a.id > b.id) continue;
          const pb = where(b), d = Math.hypot(pa.e - pb.e, pa.n - pb.n);
          if (d < worst) worst = d;
          if (d < MIN_M - 0.02) pairs++;
        }
      }
      stats.pairs = pairs;
      stats.worst_m = Number.isFinite(worst) ? +worst.toFixed(3) : null;
    },
    /** Where a figure stands now, offset and all (local ENU). */
    where,
  };
}
