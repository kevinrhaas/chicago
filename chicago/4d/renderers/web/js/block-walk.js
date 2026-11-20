// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * block-walk.js — a walk round the block from someone's own front door (T-3573).
 *
 * The owner, 2026-11-12: *"if someone is in one of the houses and in town they should be able
 * to be go to find or followed and if they are in their house they come outside and do a daily
 * task outside so you can follow them, something meaningful like a walk around the block or
 * something else with some movement ideally"*. human-days.js `outing` brings them out; this
 * says where they walk.
 *
 * THE BLOCK. From the middle of their house, four lines are walked out square to its front
 * (the bearing their door faces, then right, back and left), each until it first meets one of
 * the ways the era lays (`ways`, route.js's surface classes: 1904's sidewalks; 1835's plank
 * walks and unpaved street corridors), no further than BLOCK_WALK.reach_m. Those four meetings
 * are the middles of the block's four sides as seen from the house; its corners are where the
 * sides cross (the front's distance out along the front, the right side's along the right…),
 * each moved onto a way within BLOCK_WALK.snap_m, else left to the router to turn. The walk is
 * front, front-right corner, right side, back-right corner, back, back-left corner, left side,
 * front-left corner, front again: round the block, by the router between each two (route.js,
 * which keeps a walker to the sidewalks). A side that is not met (the block runs on past the
 * reach, or there is no street behind the house) leaves the walk as a there-and-back along
 * the sides that are, round the corners it can reach. An alley is not a side: 1904's alleys
 * are not sidewalks, so a Prairie Avenue walk goes round by Indiana Avenue as Christine
 * Nelson's written errand does.
 *
 * NO BLOCK (1812, or a house with no way in front of it within reach): a walk about the place,
 * a ring of RING.points points out from the house, each one standing on open ground the walker
 * can stand on (`blockedAt`) and reached in a straight line from the one before
 * (`clearSegment`), the ones that are not dropped: the widest of RING.radii_m with three such
 * points, else (a barracks in the fort's yard) the ring with most, walked there and back; two
 * at least, or no walk.
 *
 * Nothing here knows THREE, the DOM or the day engine: it takes a router's `classAt`,
 * `blockedAt` and `clearSegment` and returns a human-days walk span's shape. Reconstructed:
 * nobody's walk on a given day is recorded (liberty L-t3573-step-out).
 */

export const BLOCK_WALK = Object.freeze({ reach_m: 320, step_m: 1.5, from_m: 2, snap_m: 9, min_m: 4 });
export const RING = Object.freeze({ radii_m: Object.freeze([38, 26, 18, 12]), points: 8, min_points: 3 });

/** The ways a walk round the block keeps to, by scene. */
export const BLOCK_WAYS = Object.freeze({
  1835: Object.freeze(['sidewalk', 'crossing', 'corridor']),
  1904: Object.freeze(['sidewalk', 'crossing']),
});

const RAD = Math.PI / 180;
const bearingOf = (de, dn) => ((Math.atan2(de, dn) / RAD) + 360) % 360;
const local = (p, heading) => (Number.isFinite(heading)
  ? { local_e: +p.e.toFixed(3), local_n: +p.n.toFixed(3), heading_deg: +(((heading % 360) + 360) % 360).toFixed(1) }
  : { local_e: +p.e.toFixed(3), local_n: +p.n.toFixed(3) });

/** The middle of a structure's footprints ({ pts: [[e, n], …] }[]): its bounding box's. */
export function footprintCentre(polygons) {
  let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
  for (const f of polygons ?? []) for (const [e, n] of f.pts ?? []) {
    if (e < e0) e0 = e; if (e > e1) e1 = e; if (n < n0) n0 = n; if (n > n1) n1 = n;
  }
  return Number.isFinite(e0) ? { e: (e0 + e1) / 2, n: (n0 + n1) / 2 } : null;
}

/**
 * Where a line out from `centre` along `deg` first meets a way: { e, n, d } or null.
 * The way must be at least BLOCK_WALK.min_m out (not the house's own front walk under its
 * door, which is open ground or the footprint in every scene but is checked all the same).
 */
function sideOf(centre, deg, isWay) {
  const se = Math.sin(deg * RAD), cn = Math.cos(deg * RAD);
  for (let d = BLOCK_WALK.from_m; d <= BLOCK_WALK.reach_m; d += BLOCK_WALK.step_m) {
    const e = centre.e + se * d, n = centre.n + cn * d;
    if (d >= BLOCK_WALK.min_m && isWay(e, n)) return { e, n, d };
  }
  return null;
}

/** The nearest point on a way within BLOCK_WALK.snap_m of `p`, else null. */
function snapTo(p, isWay) {
  if (isWay(p.e, p.n)) return { e: p.e, n: p.n };
  const step = 1;
  for (let r = step; r <= BLOCK_WALK.snap_m; r += step) {
    const k = Math.max(8, Math.round(2 * Math.PI * r / step));
    for (let i = 0; i < k; i++) {
      const a = (i / k) * 2 * Math.PI;
      const e = p.e + Math.sin(a) * r, n = p.n + Math.cos(a) * r;
      if (isWay(e, n)) return { e, n };
    }
  }
  return null;
}

/**
 * The walk round the block from a house: a human-days walk span's shape
 * `{ kind: 'block' | 'ring', round, at, via, to_point, length_m }`, or null (`round`: it
 * comes back to where it starts).
 *
 * @param {object} o
 * @param {{e:number, n:number}} o.centre         the middle of the house
 * @param {number} o.frontDeg                      the compass bearing its door faces out
 * @param {(e:number, n:number) => string} [o.classAt]   route.js's surface class by name
 * @param {string[]} [o.ways]                      the classes a block's sides are (BLOCK_WAYS)
 * @param {(e:number, n:number) => boolean} [o.blockedAt]
 * @param {(ae:number, an:number, be:number, bn:number) => boolean} [o.clearSegment]
 */
export function blockLoop({ centre, frontDeg = 0, classAt = null, ways = null, blockedAt = () => false, clearSegment = () => true } = {}) {
  if (!centre || !Number.isFinite(centre.e) || !Number.isFinite(centre.n)) return null;
  const front = Number.isFinite(frontDeg) ? frontDeg : 0;
  if (ways?.length && typeof classAt === 'function') {
    const isWay = (e, n) => ways.includes(classAt(e, n));
    const sides = [0, 1, 2, 3].map((k) => sideOf(centre, front + 90 * k, isWay));
    if (sides[0]) {
      // The corners in the house's own frame: u out of the front, v to the right.
      const ue = Math.sin(front * RAD), un = Math.cos(front * RAD);
      const ve = Math.sin((front + 90) * RAD), vn = Math.cos((front + 90) * RAD);
      const out = (k) => (sides[k] ? sides[k].d : null);
      const u = [out(0), null, out(2) == null ? null : -out(2), null];
      const v = [null, out(1), null, out(3) == null ? null : -out(3)];
      const corner = (a, b) => {
        const uu = u[a] ?? u[b], vv = v[a] ?? v[b];
        if (uu == null || vv == null) return null;
        return snapTo({ e: centre.e + ue * uu + ve * vv, n: centre.n + un * uu + vn * vv }, isWay);
      };
      const at = { e: sides[0].e, n: sides[0].n };
      const full = sides.every(Boolean);
      let path;
      if (full) {
        path = [at, corner(0, 1), sides[1], corner(1, 2), sides[2], corner(2, 3), sides[3], corner(3, 0), at];
      } else {
        // Out along the front one way round the corners it can reach, back past the door, and
        // out the other way: walked to and fro, it is the street front and its two ends.
        const right = sides[1] ? [corner(0, 1), sides[1], ...(sides[2] ? [corner(1, 2), sides[2]] : [])] : [];
        const left = sides[3] ? [corner(3, 0), sides[3], ...(sides[2] && !sides[1] ? [corner(3, 2), sides[2]] : [])] : [];
        path = [at, ...right, ...right.slice(0, -1).reverse(), ...(right.length ? [at] : []), ...left];
      }
      const pts = path.filter(Boolean).map((p) => ({ e: p.e, n: p.n }))
        .filter((p, i, all) => !i || Math.hypot(p.e - all[i - 1].e, p.n - all[i - 1].n) > 0.5);
      const length = pts.reduce((s, p, i) => (i ? s + Math.hypot(p.e - pts[i - 1].e, p.n - pts[i - 1].n) : 0), 0);
      if (pts.length >= 2 && length >= 20) {
        return { kind: 'block', round: full, at: local(pts[0], bearingOf(pts[1].e - pts[0].e, pts[1].n - pts[0].n)),
          via: pts.slice(1, -1).map((p) => local(p)), to_point: local(pts.at(-1)), length_m: +length.toFixed(1) };
      }
    }
  }
  // No block: a walk about the place, on the widest ring that has room for one.
  let best = null;
  for (const radius of RING.radii_m) {
    const ring = [];
    for (let k = 0; k < RING.points; k++) {
      const deg = front + (360 / RING.points) * k;
      const p = { e: centre.e + Math.sin(deg * RAD) * radius, n: centre.n + Math.cos(deg * RAD) * radius };
      if (blockedAt(p.e, p.n)) continue;
      const prev = ring.at(-1);
      if (prev && !clearSegment(prev.e, prev.n, p.e, p.n)) continue;
      ring.push(p);
    }
    if (!best || ring.length > best.length) best = ring;
    if (ring.length >= RING.min_points) break;
  }
  // Two places at least: there and back between them (the fort's yard, a lodge by the river).
  if (!best || best.length < 2) return null;
  const ring = best;
  const closes = ring.length >= RING.min_points && clearSegment(ring.at(-1).e, ring.at(-1).n, ring[0].e, ring[0].n);
  if (closes) ring.push({ ...ring[0] });
  const length = ring.reduce((s, p, i) => (i ? s + Math.hypot(p.e - ring[i - 1].e, p.n - ring[i - 1].n) : 0), 0);
  return { kind: 'ring', round: closes, at: local(ring[0], bearingOf(ring[1].e - ring[0].e, ring[1].n - ring[0].n)),
    via: ring.slice(1, -1).map((p) => local(p)), to_point: local(ring.at(-1)), length_m: +length.toFixed(1) };
}

/** What the walk is called on the person's card and in the HUD, by its kind and the hour. */
export function walkDoing(kind, hour) {
  if (kind === 'ring') return 'a walk about the place';
  if (Number.isFinite(hour) && (hour < 5 || hour >= 22)) return 'a late walk round the block';
  if (Number.isFinite(hour) && hour < 11.5) return 'a morning walk round the block';
  if (Number.isFinite(hour) && hour >= 17.5) return 'an evening walk round the block';
  return 'an errand round the block';
}
