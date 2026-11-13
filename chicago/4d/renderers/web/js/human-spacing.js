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
 *     team, seated or indoors is never moved, but others keep clear of it;
 *   - T-3520 (owner, 2026-11-08: "people can stand and break the wall of the mat walls"): no one
 *     stands in a wall the walker does not keep (`keepOut`: the camps' lodges, [{ pts }] in local
 *     E/N). A figure whose body would reach into one is moved out past its edge by BODY_R_M, as a
 *     pair is moved apart (a step at a time when drawn; up to WALL_MAX_M, past MAX_M).
 *   - T-3554 (owner, 2026-11-13, of a maid standing half inside the bottom steps of a front stoop:
 *     "she cannot stand where there are stairs like that, no one should be able to"): no one
 *     stands in a stair. A figure standing (not walking, not on a way's treads) whose body reaches
 *     into one (`clearOf`, house-barriers.js: a stoop, its rails, a coping, a bay) is stepped out
 *     to the nearest place clear of it, as out of a wall; the passes after never push them back.
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
/** T-3520: a body's half-width, kept off a keep-out wall; and how far one may be moved off it. */
export const BODY_R_M = 0.3;
export const WALL_MAX_M = 6;
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
 * @param {(e:number, n:number) => ({e:number, n:number} | null)} [o.clearOf] T-3554: the nearest
 *        place a standing body is clear of every stair, or null where (e, n) already is
 */
/**
 * T-3520: where a point stands against a set of polygons: for one inside a polygon, or within
 * `r` of its edge, the nearest point `r` outside that edge. Returns null when clear of them all.
 */
export function keepOutOf(walls, e, n, r = BODY_R_M) {
  for (const w of walls) {
    if (e < w.box[0] - r || e > w.box[2] + r || n < w.box[1] - r || n > w.box[3] + r) continue;
    const P = w.pts;
    let inside = false, best = Infinity, be = 0, bn = 0, ne = 0, nn = 0;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
      const [x1, y1] = P[j], [x2, y2] = P[i];
      if ((y1 > n) !== (y2 > n) && e < (x2 - x1) * (n - y1) / (y2 - y1) + x1) inside = !inside;
      const dx = x2 - x1, dy = y2 - y1, L2 = dx * dx + dy * dy || 1e-12;
      const t = Math.max(0, Math.min(1, ((e - x1) * dx + (n - y1) * dy) / L2));
      const qe = x1 + t * dx, qn = y1 + t * dy, d = Math.hypot(e - qe, n - qn);
      if (d < best) { best = d; be = qe; bn = qn; const k = Math.hypot(dx, dy) || 1; ne = dy / k; nn = -dx / k; }
    }
    if (!inside && best >= r) continue;
    // Out along the edge's outward normal (the polygon's own winding, either way round).
    const cx = w.centre[0], cn = w.centre[1];
    if ((be - cx) * ne + (bn - cn) * nn < 0) { ne = -ne; nn = -nn; }
    return { e: be + ne * (r + 0.02), n: bn + nn * (r + 0.02) };
  }
  return null;
}
/** Polygons ready for keepOutOf: each with its bounding box and centre. */
export function wallsFrom(list) {
  return (list ?? []).filter((w) => Array.isArray(w?.pts) && w.pts.length >= 3).map((w) => {
    const es = w.pts.map((p) => p[0]), ns = w.pts.map((p) => p[1]);
    return { id: w.id, pts: w.pts, box: [Math.min(...es), Math.min(...ns), Math.max(...es), Math.max(...ns)],
      centre: [es.reduce((a, b) => a + b, 0) / es.length, ns.reduce((a, b) => a + b, 0) / ns.length] };
  });
}

export function createHumanSpacing({ humans, visitor = () => null, blockedAt = null, keepOut = [], clearOf = null } = {}) {
  const walls = wallsFrom(keepOut);
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
      const off = Math.hypot(se, sn), cap = walls.length && keepOutOf(walls, a.e, a.n) ? WALL_MAX_M : MAX_M;
      if (off > cap) { se *= cap / off; sn *= cap / off; }
      if (walls.length && keepOutOf(walls, a.e + se, a.n + sn) && !keepOutOf(walls, a.e + a.spaceE, a.n + a.spaceN)) continue;
      if (blockedAt && blockedAt(a.e + se, a.n + sn) && !blockedAt(a.e + a.spaceE, a.n + a.spaceN)) continue;
      if (clearOf && !walking(a) && clearOf(a.e + se, a.n + sn) && !clearOf(a.e + a.spaceE, a.n + a.spaceN)) continue;
      a.spaceE = se; a.spaceN = sn;
      a.place?.();
      stats.moved++;
    }
    return { pairs, grid };
  }

  /** T-3520: anyone whose body reaches into a keep-out wall is moved out past it. */
  function clearWalls(list, dt) {
    for (const a of list) {
      if (fixed(a)) continue;
      const p = where(a);
      // Out of one wall can be into the next lodge's: out of each in turn, a few at most.
      let q = keepOutOf(walls, p.e, p.n);
      if (!q) continue;
      for (let k = 0; k < 4; k++) { const r = keepOutOf(walls, q.e, q.n); if (!r) break; q = r; }
      let e = q.e - p.e, n = q.n - p.n;
      const len = Math.hypot(e, n), seen = a.root.visible && a.inRange;
      const most = seen ? RATE_M_S * dt : Infinity;
      if (len > most) { e *= most / len; n *= most / len; }
      let se = a.spaceE + e, sn = a.spaceN + n;
      const off = Math.hypot(se, sn);
      if (off > WALL_MAX_M) { se *= WALL_MAX_M / off; sn *= WALL_MAX_M / off; }
      a.spaceE = se; a.spaceN = sn;
      a.place?.();
      stats.moved++;
      stats.walls = (stats.walls ?? 0) + 1;
    }
  }

  /** T-3554: anyone standing in a stair is stepped out to the nearest place clear of it. */
  function clearStairs(list, dt) {
    for (const a of list) {
      if (fixed(a) || walking(a)) continue;
      const p = where(a);
      const q = clearOf(p.e, p.n);
      if (!q) continue;
      let e = q.e - p.e, n = q.n - p.n;
      const len = Math.hypot(e, n), seen = a.root.visible && a.inRange;
      const most = seen ? RATE_M_S * dt : Infinity;
      if (len > most) { e *= most / len; n *= most / len; }
      let se = a.spaceE + e, sn = a.spaceN + n;
      const off = Math.hypot(se, sn);
      if (off > WALL_MAX_M) { se *= WALL_MAX_M / off; sn *= WALL_MAX_M / off; }
      a.spaceE = se; a.spaceN = sn;
      a.place?.();
      stats.moved++;
      stats.stairs = (stats.stairs ?? 0) + 1;
    }
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
      let clear = !(walls.length && keepOutOf(walls, p.e, p.n)) && !(clearOf && !walking(a) && clearOf(p.e, p.n));
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
      stats.moved = 0; stats.walls = 0; stats.stairs = 0;
      let last = null;
      // Out of the walls first; the passes after never push anyone back into one.
      if (walls.length) clearWalls(list, dt);
      if (clearOf) clearStairs(list, dt);
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
