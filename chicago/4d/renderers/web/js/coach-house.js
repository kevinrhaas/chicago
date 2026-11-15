/**
 * coach-house.js — Glessner's coach house on Eighteenth Street: its two carriage leaves swing
 * open and shut, the man door in the left leaf opens for people, a dark plain room stands behind
 * them, and a carriage has a way in off the street (T-3557, the T-3564 half of it).
 *
 * The owner, 2026-11-12, of his photographs of the coach-house doors: *"the main coach house
 * door can open and a horse and carriage can enter according to normal standards of how that
 * would work ... i imagine there would be like a driveway to the coach house as well"*. T-3564
 * built the still parts (the leaves, house-doors.js `glessnerCoachPlan`; the carriage drive,
 * data/street_section/1904.json `carriage_drives`). This layer moves them.
 *
 * WHAT IS THE RECORD'S: the doorway (W 134.9-147.0, 12.6 ft to the lintel's soffit), the casing,
 * the leaves and the man door exactly as the generator bakes them (glessnerCoachPlan reads them);
 * the drive's line, width and ramp (carriage_drives); the street's carriageways (street_grid).
 *
 * WHAT IS OURS, docs/LIBERTIES.md L-glessner-coach-house-3557:
 *   - the hinges. Kevin's photographs 10 and 11 (chicago-evidence glessner-kevin-photos-2026-11-10)
 *     show no hinge knuckle, strap or pintle anywhere on the street face, and the leaves stand at
 *     the back of the reveal behind a casing that laps them, so each leaf hangs on its own jamb
 *     and swings INWARD (inferred); so does the man door, on the jamb side of its leaf (its latch
 *     is on its free, west edge in photograph 11). Inward is also how a door on a public walk had
 *     to swing. The angle (90 degrees) and the times (COACH_SWING_S, MAN_DOOR_SWING_S) are ours;
 *   - the room: a dark, plain carriage room ROOM_DEPTH_M deep behind the leaves and ROOM_SIDE_M
 *     past each jamb, so the opening reads as a room and a carriage and pair can stand inside.
 *     Nothing read draws the coach house's 1904 rooms;
 *   - the way in: from its own lane (keep right) a team drifts gently across toward the north
 *     kerb (DRIFT_RADIUS_M), turns in on TURN_RADIUS_M and comes straight over the drive for
 *     TURN_END_M before the doors, so it is square to them before the horses reach the lintel.
 *
 * HOW IT IS DRAWN. As house-doors.js does the front door: the buildings layer lifts the baked
 * leaf triangles (takeDoorLeaf, with the coach plan) and this layer hangs them on pivots at the
 * jambs. The man door is cut out of the east leaf's triangles along its own frame (cutGeometry)
 * and hung on a pivot inside that leaf's, so it turns with the leaf.
 *
 * THE API (main.js exposes it as `api.coachHouse`):
 *   open() / close()           -> Promise<{ ok, why? }>: the leaves swing (the man door shuts
 *                                 first); close is refused while anything stands in their swing
 *   state                      'shut' | 'opening' | 'open' | 'closing'
 *   manDoor.open() / close() / state   the man door, the same way (for people)
 *   drivePath({ from, row })   { points_enu_m, inside_enu_m, heading_in_deg, ... } the rear axle's
 *                              way from 18th Street's lane (from 'east', Prairie's end, westbound;
 *                              or 'west', eastbound) over the drive and through the doors to a
 *                              stand inside, drivable by the bicycle model under its 15-degree lock
 *   clearFor(row, from, to)    true where every pose from `from` to `to` (vehicle-root poses, as
 *                              transport-clearance.js reads them) lies on that way with the leaves
 *                              open, the team inside the doorway and the room, every wheel and
 *                              hoof on the carriageway, the drive or the room's floor
 *   floorAt(e, n)              the room's (and doorway's) floor height, else null
 *   setBlocker(fn)             fn(sweepPolygonEnu) -> a reason string (or true) while something
 *                              the ride knows of stands in the leaves' swing
 */
import * as THREE from 'three';
import { footprintToWorld } from './walker.js';
import { glessnerCoachPlan, leafPose, planPoint } from './house-doors.js';
import { teamGroundPoints, KERB_ROOM_M } from './team-drive.js';

export const COACH_SWING_S = 3.0;
export const MAN_DOOR_SWING_S = 1.2;
export const COACH_REACH_M = 3.5;
/** The room: this deep behind the leaves' back, this far past each jamb, its ceiling this far
 *  over the lintel's soffit. Deep enough for the brougham and its pair to stand clear of the
 *  leaves' swing (drivePath's stand), with a little over. */
export const ROOM_DEPTH_M = 9.0;
export const ROOM_SIDE_M = 1.3;
const ROOM_HEADROOM_M = 0.5;
/** The way in: the rear axle's turn (14.5 degrees of lock on the brougham's 2.3 m wheelbase,
 *  under its 15), how far out from the face it is straight again, the straight lead before. */
export const TURN_RADIUS_M = 8.9;
export const TURN_END_M = 5.9;
export const LEAD_M = 15;
/** The drift from the lane across to the turn's line, out by the far kerb: two arcs of this radius. */
export const DRIFT_RADIUS_M = 80;
export const PATH_STEP_M = 0.25;
/** A pose on the way: its rear axle this near the path and its heading this near the path's. */
export const PATH_TOL_M = 1.0;
const PATH_YAW_TOL = 30 * Math.PI / 180;
/** Room left between the team and the swing of the leaves at the stand, and round the team for
 *  clearFor (transport-clearance.js's own margin). */
const STAND_MARGIN_M = 0.15;
export const CLEAR_MARGIN_M = 0.15;
/** A walker's capsule (walker.js WALK.radius is 0.25; a little more). */
const VISITOR_RADIUS_M = 0.35;
/** The doors file's hard-coded Glessner team: the brougham rows of data/transport/driven/loops.json
 *  (the same Studebaker brougham, its measured envelope). Used where no row is given. */
export const BROUGHAM = Object.freeze({
  wheelbase_m: 2.3, root_ahead_of_rear_axle_m: 1.15, track_m: 1.34, team_half_spacing_m: 0.65,
  horse_offset_m: [0, 0, 3.08], steering_limit_deg: 15,
  envelope_measured_local_xz_m: [-1.1971540112566856, -1.8365528583526611, 1.1971540112566856, 4.622850165367126],
});
/** The vehicle's own half width (brougham-near.glb, accessor bounds x +/-0.86 m): what stands
 *  behind the front axle; ahead of it the team's measured envelope swings with the lock. */
export const BODY_HALF_M = 0.86;
const DEG = Math.PI / 180;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const wrapAngle = (a) => Math.atan2(Math.sin(a), Math.cos(a));

/** Point-in-polygon (ray casting) on [[x, y], ...]. */
export function insidePoly(x, y, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

// ---------------------------------------------------------------- the numbers of the doors

/** The doors' working numbers in the plan's (d, s) frame, from the plan. */
export function coachDims(plan) {
  const [j0, j1] = plan.jambs;
  const [ls0, ls1] = plan.leaf.s;
  const mid = (ls0 + ls1) / 2;
  const leafWidth = (ls1 - ls0) / 2;
  const back = plan.leaf.back;
  // An open leaf stands along its jamb: its thickness off the hinge line, its latch a little more.
  const thick = plan.leaf.front - plan.leaf.back + 0.01;
  const manWidth = plan.man ? plan.man.s[1] - plan.man.s[0] : 0;
  return {
    j0, j1, ls0, ls1, mid, leafWidth, back, thick, manWidth,
    casingFront: plan.leaf.front,
    roomFront: back - 0.01,
    roomBack: back - ROOM_DEPTH_M,
    r0: j0 - ROOM_SIDE_M, r1: j1 + ROOM_SIDE_M,
    leavesBack: back - leafWidth - 0.05,          // past the open leaves' free edges
    ceiling: plan.head + ROOM_HEADROOM_M,
  };
}

/** Whether (d, s) is where a carriage may stand inside the face: the doorway between the casings,
 *  between the open leaves, then the room. */
export function allowedInside(dims, d, s) {
  if (d > 0) return true;
  if (d >= dims.back) return s >= dims.ls0 && s <= dims.ls1;
  if (d >= dims.leavesBack) return s >= dims.ls0 + dims.thick && s <= dims.ls1 - dims.thick;
  return d >= dims.roomBack && s >= dims.r0 && s <= dims.r1;
}

// ---------------------------------------------------------------- the man door's cut

/**
 * Cut `geo` (a lifted leaf piece in the structure frame: x = u, y up, z = -v) along a rectangle
 * of the plan's (s, y): the triangles' parts inside it and outside it, as two non-indexed
 * geometries with every attribute carried (position, normal, uv, uv1), lerped along each cut
 * edge. The man door's own frame is the rectangle, so the leaf's stile and bottom rail behind it
 * go with it and the opening it leaves is clear.
 */
export function cutGeometry(geo, plan, rect) {
  const pos = geo.getAttribute('position');
  const names = ['position', 'normal', 'uv', 'uv1'].filter((n) => geo.getAttribute(n));
  const index = geo.getIndex();
  const count = index ? index.count : pos.count;
  const at = (i) => (index ? index.getX(i) : i);
  const sOf = (v) => (v.position[0] - plan.origin[0]) * plan.along[0] + (-v.position[2] - plan.origin[1]) * plan.along[1];
  const vert = (i) => {
    const v = {};
    for (const n of names) {
      const a = geo.getAttribute(n);
      v[n] = Array.from({ length: a.itemSize }, (_, c) => a.getComponent(i, c));
    }
    return v;
  };
  const lerp = (a, b, t) => {
    const v = {};
    for (const n of names) v[n] = a[n].map((x, c) => x + (b[n][c] - x) * t);
    if (v.normal) { const l = Math.hypot(...v.normal) || 1; v.normal = v.normal.map((x) => x / l); }
    return v;
  };
  /** Keep the part of a convex polygon where f >= 0. */
  const clip = (poly, f) => {
    const out = [];
    for (let i = 0; i < poly.length; i += 1) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const fa = f(a), fb = f(b);
      if (fa >= 0) out.push(a);
      if ((fa >= 0) !== (fb >= 0)) out.push(lerp(a, b, fa / (fa - fb)));
    }
    return out;
  };
  const [s0, s1] = rect.s, [y0, y1] = rect.y;
  const parts = { inside: [], outside: [] };
  const emit = (poly, list) => {
    for (let k = 1; k + 1 < poly.length; k += 1) list.push(poly[0], poly[k], poly[k + 1]);
  };
  for (let t = 0; t < count / 3; t += 1) {
    const tri = [vert(at(3 * t)), vert(at(3 * t + 1)), vert(at(3 * t + 2))];
    // Outside, piece by piece: left of s0; right of s1; below y0 and above y1 between them.
    emit(clip(tri, (v) => s0 - sOf(v)), parts.outside);
    let rest = clip(tri, (v) => sOf(v) - s0);
    emit(clip(rest, (v) => sOf(v) - s1), parts.outside);
    rest = clip(rest, (v) => s1 - sOf(v));
    emit(clip(rest, (v) => y0 - v.position[1]), parts.outside);
    rest = clip(rest, (v) => v.position[1] - y0);
    emit(clip(rest, (v) => v.position[1] - y1), parts.outside);
    emit(clip(rest, (v) => y1 - v.position[1]), parts.inside);
  }
  const build = (list) => {
    const g = new THREE.BufferGeometry();
    for (const n of names) {
      const size = list[0]?.[n]?.length ?? geo.getAttribute(n).itemSize;
      g.setAttribute(n, new THREE.Float32BufferAttribute(list.flatMap((v) => v[n]), size));
    }
    g.computeBoundingSphere();
    return g;
  };
  return { inside: build(parts.inside), outside: build(parts.outside) };
}

/** A geometry's triangles' total area (the test's conservation check). */
export function areaOf(geo) {
  const p = geo.getAttribute('position');
  const index = geo.getIndex();
  const n = index ? index.count : p.count;
  const at = (i) => (index ? index.getX(i) : i);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  let sum = 0;
  for (let t = 0; t < n / 3; t += 1) {
    a.fromBufferAttribute(p, at(3 * t)); b.fromBufferAttribute(p, at(3 * t + 1)); c.fromBufferAttribute(p, at(3 * t + 2));
    sum += b.sub(a).cross(c.sub(a)).length() / 2;
  }
  return sum;
}

// ---------------------------------------------------------------- the leaves' swing

/** The pivot turn (about +y, radians) of leaf `k` of `plan` at swing fraction t: inward. */
export function pivotTurn(plan, t, k = 0) {
  const map = ([d, s]) => [plan.outward[0] * d + plan.along[0] * s, plan.outward[1] * d + plan.along[1] * s];
  const [du, dv] = map(leafPose(plan, t, k).dir);
  const [su, sv] = map(leafPose(plan, 0, k).dir);
  return wrapAngle(Math.atan2(dv, du) - Math.atan2(sv, su));
}

/** The man door as a plan of its own (one leaf, hung on the jamb side of the east leaf). */
export function manPlan(plan) {
  if (!plan.man) return null;
  return { ...plan, pair: false, hinge: plan.man.hinge,
    leaf: { ...plan.leaf, s: plan.man.s, foot: plan.man.foot, top: plan.man.head } };
}

// ---------------------------------------------------------------- the room

/** A dark box behind the doors, faces turned inward, unlit (house-doors.js's vestibule, deeper). */
function roomGeometry(plan, dims) {
  const front = dims.roomFront, back = dims.roomBack;
  const s0 = dims.r0, s1 = dims.r1;
  const y0 = plan.sill - 0.002, y1 = dims.ceiling;
  const pos = [], col = [];
  const P = (d, s, y) => { const [u, v] = planPoint(plan, d, s); return [u, y, -v]; };
  // A little light by the doors, nearly none at the back.
  const shade = (d) => 0.006 + 0.03 * clamp((d - back) / (front - back), 0, 1) ** 1.5;
  const centre = P((front + back) / 2, (s0 + s1) / 2, (y0 + y1) / 2);
  const quad = (a, b, c, d4, ds) => {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ad = [d4[0] - a[0], d4[1] - a[1], d4[2] - a[2]];
    const nrm = [ab[1] * ad[2] - ab[2] * ad[1], ab[2] * ad[0] - ab[0] * ad[2], ab[0] * ad[1] - ab[1] * ad[0]];
    const mid = [0, 1, 2].map((k) => (a[k] + b[k] + c[k] + d4[k]) / 4 - centre[k]);
    const order = nrm[0] * mid[0] + nrm[1] * mid[1] + nrm[2] * mid[2] > 0
      ? [[a, ds[0]], [d4, ds[3]], [c, ds[2]], [a, ds[0]], [c, ds[2]], [b, ds[1]]]
      : [[a, ds[0]], [b, ds[1]], [c, ds[2]], [a, ds[0]], [c, ds[2]], [d4, ds[3]]];
    for (const [p, d] of order) { pos.push(...p); const g = shade(d); col.push(g, g * 0.88, g * 0.74); }
  };
  const along = [back, front, front, back];
  quad(P(back, s0, y0), P(front, s0, y0), P(front, s1, y0), P(back, s1, y0), along);           // floor
  quad(P(back, s0, y1), P(front, s0, y1), P(front, s1, y1), P(back, s1, y1), along);           // ceiling
  quad(P(back, s0, y0), P(front, s0, y0), P(front, s0, y1), P(back, s0, y1), along);           // side
  quad(P(back, s1, y0), P(front, s1, y0), P(front, s1, y1), P(back, s1, y1), along);           // side
  quad(P(back, s0, y0), P(back, s1, y0), P(back, s1, y1), P(back, s0, y1), [back, back, back, back]);
  // The street wall seen from inside: over the lintel, and beside each jamb.
  const f4 = [front, front, front, front];
  quad(P(front, s0, plan.head), P(front, s1, plan.head), P(front, s1, y1), P(front, s0, y1), f4);
  quad(P(front, s0, y0), P(front, dims.j0, y0), P(front, dims.j0, plan.head), P(front, s0, plan.head), f4);
  quad(P(front, dims.j1, y0), P(front, s1, y0), P(front, s1, plan.head), P(front, dims.j1, plan.head), f4);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeBoundingSphere();
  return geo;
}

// ---------------------------------------------------------------- the way in

/**
 * The doors' frame in ENU and the street before them: `origin` the doorway's middle on the face,
 * `out` the unit vector out of the face, `x` along the street to the right of `out` (east here);
 * `kerb` / `farKerb` the near and far kerb lines and `ramp` the drive's ramp foot, as distances
 * out from the face; `half` the drive's half width. Read from the drive record where it is given
 * (its line must agree with the doorway's), and the far kerb from the carriageways.
 */
export function streetFrame({ origin, out, drive = null, onRoad = null }) {
  const x = [out[1], -out[0]];
  let kerb = Number(drive?.ramp_from_m), ramp = Number(drive?.ramp_to_m);
  const at = (t) => [origin[0] + out[0] * t, origin[1] + out[1] * t];
  if (!Number.isFinite(kerb) && onRoad) {
    for (let t = 0; t < 30; t += 0.01) if (onRoad(...at(t))) { kerb = t; break; }
  }
  if (!Number.isFinite(ramp)) ramp = kerb;
  let farKerb = null;
  if (onRoad && Number.isFinite(kerb)) {
    for (let t = Math.max(kerb, ramp) + 0.5; t < 60; t += 0.01) if (!onRoad(...at(t))) { farKerb = t; break; }
  }
  return { origin, out, x, kerb, ramp, farKerb, half: Number(drive?.width_m) / 2 || null };
}

/**
 * The rear axle's way in, in the frame's local (x along the street, y out of the face) metres:
 * the lead in the lane; a gentle drift on two arcs of DRIFT_RADIUS_M (theta each) across to the
 * turn's own line, ye + R, out by the far kerb; the quarter-circle turn in; and straight over
 * the drive and through the doors to `stand` (negative: inside the face). A tighter swing away
 * from the doors and back would point the team over the far kerb as it came round. `from`
 * 'east' comes heading -x (westbound), 'west' heading +x (eastbound). Samples every PATH_STEP_M
 * with { x, y, phi (heading, radians from +x), k (curvature, + = left) }.
 */
export function localWay({ laneY, turnEnd = TURN_END_M, radius = TURN_RADIUS_M, stand, lead = LEAD_M, from = 'east', step = PATH_STEP_M, driftRadius = DRIFT_RADIUS_M }) {
  const R = radius, ye = turnEnd;
  const y1 = ye + R, RL = driftRadius, y0 = Math.min(laneY, y1);
  const theta = Math.acos(clamp(1 - (y1 - y0) / (2 * RL), -1, 1));
  const x1 = R + 2 * RL * Math.sin(theta);
  const out = [];
  const push = (x, y, phi, k) => out.push({ x, y, phi, k });
  const line = (ax, ay, bx, by, phi, first) => {
    const len = Math.hypot(bx - ax, by - ay), n = Math.max(1, Math.ceil(len / step));
    for (let i = first ? 0 : 1; i <= n; i += 1) push(ax + (bx - ax) * i / n, ay + (by - ay) * i / n, phi, 0);
  };
  const arc = (cx, cy, phiFrom, phiTo, k) => {
    // On a circle of radius 1/|k| about (cx, cy), heading phi: left turn (k > 0) has the centre to
    // the left, so the point is centre + R (sin phi, -cos phi); right turn, centre - R (...).
    const r = 1 / Math.abs(k), sgn = Math.sign(k), turn = phiTo - phiFrom;
    const n = Math.max(1, Math.ceil(Math.abs(turn) * r / step));
    for (let i = 1; i <= n; i += 1) {
      const phi = phiFrom + turn * i / n;
      push(cx + sgn * r * Math.sin(phi), cy - sgn * r * Math.cos(phi), phi, k);
    }
  };
  // Built for 'east' (heading -x, a left turn in), mirrored for 'west'.
  line(x1 + lead, y0, x1, y0, Math.PI, true);
  // Out to the turn's line, heading -x again at (R, ye + R); then round and in.
  if (theta > 1e-6) { arc(x1, y0 + RL, Math.PI, Math.PI - theta, -1 / RL); arc(R, y1 - RL, Math.PI - theta, Math.PI, 1 / RL); }
  arc(R, ye, Math.PI, 1.5 * Math.PI, 1 / R);
  line(0, ye, 0, stand, 1.5 * Math.PI, false);
  if (from === 'west') for (const p of out) { p.x = -p.x; p.phi = Math.PI - p.phi; p.k = -p.k; }
  // Exact arcs and joins: the sample heading is the arc's, the samples PATH_STEP_M apart or less.
  out.theta = theta;
  out.laneY = y0;
  return out;
}

/** Where the rear axle stands inside so the whole team is in the room and the leaves can shut. */
export function standDepth(plan, row = BROUGHAM) {
  const dims = coachDims(plan);
  const env = row.envelope_measured_local_xz_m ?? row.envelope_local_xz_m ?? BROUGHAM.envelope_measured_local_xz_m;
  const behind = -(env[1] + row.root_ahead_of_rear_axle_m);  // body behind the rear axle
  return dims.back - dims.leafWidth - STAND_MARGIN_M - behind;
}

// ---------------------------------------------------------------- a team's outline

/**
 * A team at a vehicle-root pose { e, n, yaw, steering } as two ENU polygons: the vehicle behind
 * its front axle (BODY_HALF_M either side, from the envelope's back), and ahead of it the team's
 * measured envelope swung with the lock about the front axle, as teamGroundPoints swings the
 * horses. `margin` grows both.
 */
export function teamOutline(row, pose, margin = 0) {
  const env = row.envelope_measured_local_xz_m ?? row.envelope_local_xz_m;
  const pivot = row.wheelbase_m - row.root_ahead_of_rear_axle_m;
  const cy = Math.cos(pose.yaw), sy = Math.sin(pose.yaw);
  const c = Math.cos(pose.steering ?? 0), sn = Math.sin(pose.steering ?? 0);
  const toEnu = ([x, z]) => [pose.e + cy * x + sy * z, pose.n + sy * x - cy * z];
  const swing = ([x, z]) => [c * x + sn * (z - pivot), pivot - sn * x + c * (z - pivot)];
  const half = Math.min(BODY_HALF_M, -env[0], env[2]) + margin;
  const body = [[-half, env[1] - margin], [half, env[1] - margin], [half, pivot], [-half, pivot]].map(toEnu);
  const fore = [[env[0] - margin, pivot], [env[2] + margin, pivot], [env[2] + margin, env[3] + margin], [env[0] - margin, env[3] + margin]]
    .map(swing).map(toEnu);
  return [body, fore];
}

/** Points along a polygon's edges every `step` metres, and a grid inside it. */
export function polygonSamples(poly, step = 0.05, grid = 0.25) {
  const out = [];
  for (let i = 0; i < poly.length; i += 1) {
    const a = poly[i], b = poly[(i + 1) % poly.length];
    const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
    for (let k = 0; k < n; k += 1) out.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]);
  }
  // The polygons are quadrilaterals: a bilinear grid over the first four corners.
  if (poly.length === 4) {
    const [p0, p1, p2, p3] = poly;
    const nu = Math.max(1, Math.ceil(Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / grid));
    const nv = Math.max(1, Math.ceil(Math.hypot(p3[0] - p0[0], p3[1] - p0[1]) / grid));
    for (let i = 1; i < nu; i += 1) for (let j = 1; j < nv; j += 1) {
      const u = i / nu, v = j / nv;
      out.push([0, 1].map((c) => (1 - u) * (1 - v) * p0[c] + u * (1 - v) * p1[c] + u * v * p2[c] + (1 - u) * v * p3[c]));
    }
  }
  return out;
}

// ---------------------------------------------------------------- the layer

/**
 * @param {object} o
 * @param {Map} o.registry              scene-loader's records (glessner_house, when in the scene)
 * @param {object} o.buildings          the buildings layer (matrixOf, doorLeaves)
 * @param {Array} [o.footprints]        walker.js footprints: Glessner's gets the doorway
 * @param {Array} [o.decks]             walker.js decks: the doorway's and room's floor join it
 * @param {object} [o.interactions]     interact.js engine: the doors and the man door are added
 * @param {() => ({e:number, n:number})|null} [o.visitor]  the visitor on foot (null aboard or flying)
 * @param {Array} [o.carriageways]      data/street_grid carriageways (polygon_local_m)
 * @param {Array} [o.drives]            data/street_section carriage_drives.drives
 * @param {() => boolean} [o.reducedMotion]  swing at once
 * @param {object} [o.confidence]
 * @param {string[]} [o.problems]
 * @returns the layer, or null when this scene has no Glessner coach house
 */
export function createCoachHouse({ registry, buildings, footprints = [], decks = [], interactions = null,
  visitor = null, carriageways = [], drives = [], reducedMotion = () => false, confidence = null, problems = [] } = {}) {
  const record = registry?.get?.('glessner_house');
  const plan = record?.sidecar ? glessnerCoachPlan(record.sidecar) : null;
  if (!plan) return null;
  const matrix = buildings?.matrixOf?.(record.id)?.clone?.() ?? null;
  if (!matrix) {
    problems.push(`${plan.id}: the coach house was not drawn — its doors stay shut`);
    return null;
  }
  const dims = coachDims(plan);
  const mplan = manPlan(plan);
  const toWorld = footprintToWorld(record.sidecar.placement);
  const pl = record.sidecar.placement ?? {};
  const th = (pl.rotation_deg ?? 0) * DEG, cth = Math.cos(th), sth = Math.sin(th);
  /** ENU to the structure frame (u, v): footprintToWorld's inverse. */
  const toPlanUV = (e, n) => {
    const de = e - (pl.local_e ?? 0), dn = n - (pl.local_n ?? 0);
    return [de * cth - dn * sth, de * sth + dn * cth];
  };
  const toDS = (e, n) => {
    const [u, v] = toPlanUV(e, n);
    const du = u - plan.origin[0], dv = v - plan.origin[1];
    return [du * plan.outward[0] + dv * plan.outward[1], du * plan.along[0] + dv * plan.along[1]];
  };
  const fromDS = (d, s) => toWorld(planPoint(plan, d, s));
  const v3 = new THREE.Vector3();
  const heightOf = (u, v, y) => { v3.set(u, y, -v).applyMatrix4(matrix); return v3.y; };

  // ---- the drawing
  const group = new THREE.Group();
  group.name = 'coach-house';
  const holder = new THREE.Group();
  holder.name = `coach-house:${plan.id}`;
  holder.matrixAutoUpdate = false;
  holder.matrix.copy(matrix);
  group.add(holder);
  const roomMaterial = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.FrontSide });
  roomMaterial.name = 'coach-house-room';
  const room = new THREE.Mesh(roomGeometry(plan, dims), roomMaterial);
  room.name = `coach-house-room:${plan.id}`;
  room.userData.structure_id = record.id;
  holder.add(room);
  const hingeUV = (p, k) => {
    const leaf = p.pair ? (k === 0 ? { s: [p.leaf.s[0], (p.leaf.s[0] + p.leaf.s[1]) / 2], hinge: 'left' }
      : { s: [(p.leaf.s[0] + p.leaf.s[1]) / 2, p.leaf.s[1]], hinge: 'right' }) : { s: p.leaf.s, hinge: p.hinge };
    return planPoint(p, p.leaf.back, leaf.hinge === 'right' ? leaf.s[1] : leaf.s[0]);
  };
  const pivots = [0, 1].map((k) => {
    const [hu, hv] = hingeUV(plan, k);
    const pivot = new THREE.Object3D();
    pivot.name = `coach-house-leaf:${k === 0 ? 'east' : 'west'}`;
    pivot.position.set(hu, 0, -hv);
    holder.add(pivot);
    return pivot;
  });
  const manPivot = new THREE.Object3D();
  manPivot.name = 'coach-house-man-door';
  if (mplan) {
    const [hu, hv] = hingeUV(mplan, 0), [eu, ev] = hingeUV(plan, 0);
    manPivot.position.set(hu - eu, 0, -(hv - ev));
    pivots[0].add(manPivot);
  }
  const owned = [];   // geometries this layer made (the man door's cut)
  const conf = { attested: 0, inferred: 0.5, reconstructed: 1 }[plan.grades.leaf] ?? 1;
  function addMesh(parent, geometry, material, hinge, name) {
    const n = geometry.getAttribute('position').count;
    if (!geometry.getAttribute('_confidence')) geometry.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(n).fill(conf), 1));
    if (confidence?.patch && !material.userData.confidencePatched) { confidence.patch(material); material.userData.confidencePatched = true; }
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(-hinge[0], 0, hinge[1]);
    mesh.name = name;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.structure_id = record.id;
    parent.add(mesh);
    return mesh;
  }
  /** The lifted leaf pieces, from the buildings layer, on their pivots; the man door cut out. */
  function hang(layer) {
    for (const pivot of [...pivots, manPivot]) for (const m of [...pivot.children]) if (m.isMesh) pivot.remove(m);
    for (const g of owned.splice(0)) g.dispose();
    const pieces = layer?.doorLeaves?.get(plan.id) ?? [];
    for (const piece of pieces) {
      const k = Math.min(piece.leaf ?? 0, 1);
      const hinge = hingeUV(plan, k);
      if (k === 0 && plan.man) {
        const cut = cutGeometry(piece.geometry, plan, { s: [plan.man.s[0] - 0.02, plan.man.s[1]], y: [plan.man.foot - 0.02, plan.man.head] });
        owned.push(cut.inside, cut.outside);
        if (cut.outside.getAttribute('position').count) addMesh(pivots[0], cut.outside, piece.material, hinge, `coach-house-leaf:east:${piece.material.name}`);
        if (cut.inside.getAttribute('position').count) addMesh(manPivot, cut.inside, piece.material, hingeUV(mplan, 0), `coach-house-man-door:${piece.material.name}`);
      } else {
        addMesh(pivots[k], piece.geometry, piece.material, hinge, `coach-house-leaf:${k === 0 ? 'east' : 'west'}:${piece.material.name}`);
      }
    }
    holder.updateMatrixWorld(true);
    return pieces.length;
  }
  if (!hang(buildings)) problems.push(`${plan.id}: its baked leaves were not found in the mesh — the doors stay shut`);

  // ---- the swing
  const leaves = { swing: 0, target: 0, waiters: [] };
  const man = { swing: 0, target: 0, waiters: [] };
  const ease = (t) => t * t * (3 - 2 * t);
  function pose() {
    const a = ease(leaves.swing), b = ease(man.swing);
    pivots[0].rotation.y = pivotTurn(plan, a, 0);
    pivots[1].rotation.y = pivotTurn(plan, a, 1);
    if (mplan) manPivot.rotation.y = pivotTurn(mplan, b, 0);
    holder.updateMatrixWorld(true);
  }
  pose();
  const stateOf = (x) => (x.swing <= 0 && x.target === 0 ? 'shut' : x.swing >= 1 && x.target === 1 ? 'open'
    : x.target === 1 ? 'opening' : 'closing');
  const settle = (x, result) => { for (const w of x.waiters.splice(0)) w(result); };

  // ---- where things stand
  const rectDS = (d0, d1, s0, s1) => [[d0, s0], [d1, s0], [d1, s1], [d0, s1]].map(([d, s]) => fromDS(d, s));
  const sweepLeaves = rectDS(dims.leavesBack - VISITOR_RADIUS_M, -0.1 + VISITOR_RADIUS_M, dims.ls0 - VISITOR_RADIUS_M, dims.ls1 + VISITOR_RADIUS_M);
  const sweepMan = plan.man ? rectDS(dims.back - dims.manWidth - 0.05 - VISITOR_RADIUS_M, -0.1 + VISITOR_RADIUS_M,
    plan.man.s[0] - VISITOR_RADIUS_M, plan.man.s[1] + VISITOR_RADIUS_M) : null;
  const inRoom = (e, n) => { const [d, s] = toDS(e, n); return d < dims.back && d >= dims.roomBack - 0.5 && s >= dims.r0 - 0.5 && s <= dims.r1 + 0.5; };
  let blocker = null;
  function refusal(which) {
    const here = visitor?.();
    if (here) {
      if (insidePoly(here.e, here.n, which === 'man' ? sweepMan : sweepLeaves)) return 'Step out of the doorway first';
      if (inRoom(here.e, here.n)) return 'Step out of the coach house first';
    }
    if (which === 'leaves' && blocker) {
      let why = null;
      try { why = blocker(sweepLeaves.map((p) => [...p])); } catch { why = null; }
      if (why) return typeof why === 'string' ? why : 'Something stands in the doorway';
    }
    return null;
  }
  const want = (x, target) => {
    if (x.target === target) return;
    x.target = target;
    // A swing turned round mid-way: whoever waited for the other end is told it did not get there.
    settle(x, { ok: false, why: target ? 'opened again' : 'closed again' });
  };
  const request = (x, target, which) => new Promise((resolve) => {
    if (x.target === target && x.swing === target) { resolve({ ok: true, already: true }); return; }
    if (!target) {
      const why = refusal(which);
      if (why) { resolve({ ok: false, refused: true, why }); return; }
    }
    if (which === 'man' && target && leaves.swing > 0) { resolve({ ok: false, refused: true, why: 'The coach-house doors stand open' }); return; }
    if (which === 'leaves' && target && man.swing > 0) {
      const why = refusal('man');
      if (why) { resolve({ ok: false, refused: true, why }); return; }
      want(man, 0);
    }
    want(x, target);
    x.waiters.push(resolve);
  });

  // ---- the Interact things
  const atDS = (d, s) => fromDS(d, s);
  const leavesThing = {
    id: plan.id, kind: 'door', structureId: record.id, name: plan.name, states: ['closed', 'open'], state: 'closed',
    at: atDS(0.6, dims.mid), spots: [atDS(dims.leavesBack - 0.6, dims.mid)], reach: COACH_REACH_M, plan,
    actions: {
      closed: [{ id: 'open', label: 'Open the coach-house doors', to: 'open',
        refuse: () => (man.swing > 0 ? refusal('man') : null),
        steps: [{ label: 'Opening', run: (t) => { if (t === 0) { if (man.swing > 0) want(man, 0); want(leaves, 1); } },
          until: () => leaves.swing >= 1 || leaves.target !== 1, timeout: 30 }] }],
      open: [{ id: 'close', label: 'Close the coach-house doors', to: 'closed', refuse: () => refusal('leaves'),
        steps: [{ label: 'Closing', run: (t) => { if (t === 0) want(leaves, 0); },
          until: () => leaves.swing <= 0 || leaves.target !== 0, timeout: 30 }] }],
    },
  };
  const manAt = plan.man ? atDS(0.6, (plan.man.s[0] + plan.man.s[1]) / 2) : null;
  const manInside = plan.man ? atDS(dims.back - 0.8, (plan.man.s[0] + plan.man.s[1]) / 2) : null;
  const manThing = plan.man ? {
    id: `${plan.id}:man`, kind: 'door', structureId: record.id, name: 'Coach-house man door', states: ['closed', 'open'], state: 'closed',
    // Offered only while the big leaves are shut: open, they are the way in.
    get at() { return leaves.swing <= 0 && leaves.target === 0 ? manAt : null; },
    get spots() { return leaves.swing <= 0 && leaves.target === 0 ? [manInside] : []; },
    reach: COACH_REACH_M, plan: mplan,
    actions: {
      closed: [{ id: 'open', label: 'Open door', to: 'open',
        refuse: () => (leaves.swing > 0 ? 'The coach-house doors stand open' : null),
        steps: [{ label: 'Opening', run: (t) => { if (t === 0) want(man, 1); }, until: () => man.swing >= 1 || man.target !== 1, timeout: 20 }] }],
      open: [{ id: 'close', label: 'Close door', to: 'closed', refuse: () => refusal('man'),
        steps: [{ label: 'Closing', run: (t) => { if (t === 0) want(man, 0); }, until: () => man.swing <= 0 || man.target !== 0, timeout: 20 }] }],
    },
  } : null;
  if (interactions) {
    interactions.add(leavesThing);
    if (manThing) interactions.add(manThing);
  }
  const sync = (thing, x) => {
    if (!thing || thing.running) return;
    if (x.swing <= 0 && x.target === 0) thing.state = 'closed';
    else if (x.swing >= 1 && x.target === 1) thing.state = 'open';
  };

  // ---- the walk: a doorway in Glessner's footprint (walker.js § doorways)
  const fp = footprints.find((f) => f.id === record.id);
  const polygon = Array.isArray(record.sidecar.footprint) ? record.sidecar.footprint : record.sidecar.footprint?.polygon;
  function dent(points) {
    // Into the face's edge of the footprint, in the polygon's own winding (house-doors.js notchedOutline).
    const a = planPoint(plan, 0, dims.j0), b = planPoint(plan, 0, dims.j1);
    const onSeg = (p, q, r) => {
      const dx = r[0] - q[0], dy = r[1] - q[1], len = Math.hypot(dx, dy) || 1;
      const cross = Math.abs((p[0] - q[0]) * dy - (p[1] - q[1]) * dx) / len;
      const t = ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / (len * len);
      return cross < 0.02 && t > 0 && t < 1;
    };
    for (let i = 0; i < polygon.length; i += 1) {
      const q = polygon[i], r = polygon[(i + 1) % polygon.length];
      if (!onSeg(a, q, r) || !onSeg(b, q, r)) continue;
      const forward = (b[0] - a[0]) * (r[0] - q[0]) + (b[1] - a[1]) * (r[1] - q[1]) > 0;
      let pts = points.map(([d, s]) => planPoint(plan, d, s));
      if (!forward) pts = pts.reverse();
      return [...polygon.slice(0, i + 1), ...pts, ...polygon.slice(i + 1)].map(toWorld);
    }
    return null;
  }
  const W = 0.05;   // a hand's breadth off each wall of the room
  const cf = dims.casingFront, rb = dims.roomBack + W, r0 = dims.r0 + W, r1 = dims.r1 - W;
  const outlines = Array.isArray(polygon) ? {
    shut: dent([[0, dims.j0], [cf, dims.j0], [cf, dims.j1], [0, dims.j1]]),
    man: plan.man ? dent([[0, dims.j0], [cf, dims.j0], [cf, plan.man.s[0] + dims.thick], [dims.back, plan.man.s[0] + dims.thick],
      [dims.back, r0], [rb, r0], [rb, r1], [dims.back, r1], [dims.back, plan.man.s[1]], [cf, plan.man.s[1]], [cf, dims.j1], [0, dims.j1]]) : null,
    leaves: dent([[0, dims.j0], [cf, dims.j0], [cf, dims.ls0 + dims.thick], [dims.leavesBack, dims.ls0 + dims.thick],
      [dims.leavesBack, r0], [rb, r0], [rb, r1], [dims.leavesBack, r1], [dims.leavesBack, dims.ls1 - dims.thick],
      [cf, dims.ls1 - dims.thick], [cf, dims.j1], [0, dims.j1]]),
  } : null;
  let walkOpen = null;   // the outline the visitor is walking in, held while they are inside
  function walkOutline() {
    const here = visitor?.();
    const inside = here ? inRoom(here.e, here.n) : false;
    let now = null;
    if (leaves.swing >= 1 && leaves.target === 1) now = outlines.leaves;
    else if (man.swing >= 0.9 && leaves.swing <= 0) now = outlines.man;
    if (now) walkOpen = now;
    // Shut with the visitor still inside (carried in aboard, the leaves closed behind): they keep
    // a way to the man door, which Interact offers from inside, rather than being put through a wall.
    else if (inside) walkOpen = walkOpen ?? outlines.man ?? outlines.leaves;
    else walkOpen = null;
    return walkOpen;
  }
  if (fp && outlines?.shut && outlines.leaves) {
    const zone = rectDS(dims.roomBack - 0.8, 0.8, dims.r0 - 0.8, dims.r1 + 0.8);
    const doorway = {
      id: plan.id, zone, shut: outlines.shut,
      get open() { return walkOutline() ?? outlines.shut; },
      isOpen: () => !!walkOutline(),
    };
    fp.doorways = [...(fp.doorways ?? []), doorway];
    footprints.wallsVersion = (footprints.wallsVersion ?? 0) + 1;
  } else {
    problems.push(`${plan.id}: its doorway is not on the footprint's face — a visitor cannot walk in`);
  }
  // The floor: the doorway's reveal and the room, at the sill, for the walker and floorAt.
  const sillY = heightOf(...planPoint(plan, 0, dims.mid), plan.sill);
  const floorDS = [[dims.back, 0.02, dims.j0, dims.j1], [dims.roomBack, dims.back + 0.001, dims.r0, dims.r1]];
  for (const [i, [d0, d1, s0, s1]] of floorDS.entries()) {
    decks.push({ id: `${plan.id}:${i ? 'room' : 'doorway'}`, y: sillY, pts: rectDS(d0, d1, s0, s1) });
  }
  const onFloor = (e, n) => { const [d, s] = toDS(e, n); return floorDS.some(([d0, d1, s0, s1]) => d >= d0 && d <= d1 && s >= s0 && s <= s1); };

  // ---- the way in
  const origin = fromDS(0, dims.mid);
  const o1 = fromDS(1, dims.mid);
  const out = [o1[0] - origin[0], o1[1] - origin[1]];
  const drive = (drives ?? []).find((x) => x?.structure === record.id && x?.kind === 'carriage_drive') ?? null;
  const roads = (Array.isArray(carriageways) ? carriageways : []).map((c) => c?.polygon_local_m ?? c)
    .filter((p) => Array.isArray(p) && p.length >= 3)
    .map((p) => ({ p, w: Math.min(...p.map((q) => q[0])), e: Math.max(...p.map((q) => q[0])), s: Math.min(...p.map((q) => q[1])), n: Math.max(...p.map((q) => q[1])) }));
  const onRoad = roads.length ? (e, n) => roads.some((q) => e >= q.w && e <= q.e && n >= q.s && n <= q.n && insidePoly(e, n, q.p)) : null;
  const frame = streetFrame({ origin, out, drive, onRoad });
  if (drive && Math.hypot(drive.origin[0] - origin[0], drive.origin[1] - origin[1]) > 0.1) {
    problems.push(`${plan.id}: the carriage drive's line (${drive.origin.join(', ')}) is not the doorway's — the way in follows the doorway`);
  }
  const drivePolys = drive ? [drive.flat, drive.ramp].filter((p) => Array.isArray(p) && p.length >= 3) : [];
  const onDrive = (e, n) => drivePolys.some((p) => insidePoly(e, n, p));
  const lanes = frame.farKerb ? { eastbound: frame.kerb + (frame.farKerb - frame.kerb) / 4, westbound: frame.kerb + 3 * (frame.farKerb - frame.kerb) / 4 } : null;
  const paths = new Map();
  /** The rear axle's way in (the header). */
  function drivePath({ from = 'east', row = BROUGHAM } = {}) {
    const key = `${from}|${row?.wheelbase_m}|${row?.root_ahead_of_rear_axle_m}|${(row?.envelope_measured_local_xz_m ?? row?.envelope_local_xz_m ?? []).join(',')}`;
    if (paths.has(key)) return paths.get(key);
    if (!lanes) return null;
    const stand = standDepth(plan, row);
    const laneY = from === 'west' ? lanes.eastbound : lanes.westbound;
    const local = localWay({ laneY, stand, from });
    const X = frame.x, Y = frame.out;
    const toEnu = (x, y) => [origin[0] + x * X[0] + y * Y[0], origin[1] + x * X[1] + y * Y[1]];
    const yawOf = (phi) => {
      const de = Math.cos(phi) * X[0] + Math.sin(phi) * Y[0], dn = Math.cos(phi) * X[1] + Math.sin(phi) * Y[1];
      return Math.atan2(de, -dn);
    };
    const points = local.map((p) => toEnu(p.x, p.y));
    const yaw = local.map((p) => yawOf(p.phi));
    const curvature = local.map((p) => p.k);
    let length = 0;
    for (let i = 1; i < points.length; i += 1) length += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
    const inside = points.at(-1);
    const inDir = [-Y[0], -Y[1]];
    const maxK = Math.max(...curvature.map(Math.abs));
    const result = Object.freeze({
      from, points_enu_m: points, inside_enu_m: inside,
      heading_in_deg: ((Math.atan2(inDir[0], inDir[1]) / DEG) + 360) % 360,
      yaw_in_rad: yawOf(1.5 * Math.PI),
      yaw_rad: yaw, curvature_per_m: curvature, length_m: length,
      // Where along it the rear axle crosses the face, and the kerb line.
      face_index: local.findIndex((p) => p.y <= 0), kerb_index: local.findIndex((p) => p.y <= frame.kerb),
      turn_radius_m: TURN_RADIUS_M, max_curvature_per_m: maxK,
      max_steering_deg: Math.atan((row?.wheelbase_m ?? BROUGHAM.wheelbase_m) * maxK) / DEG,
      stand_depth_m: -stand, lane_offset_m: laneY, drift_deg: local.theta / DEG,
    });
    paths.set(key, result);
    return result;
  }

  /** Is this vehicle-root pose of `row` on a way in (rear axle near it, heading with it)? */
  function onWay(row, p) {
    const ra = row.root_ahead_of_rear_axle_m;
    const re = p.e - Math.sin(p.yaw) * ra, rn = p.n + Math.cos(p.yaw) * ra;
    for (const from of ['east', 'west']) {
      const way = drivePath({ from, row });
      if (!way) continue;
      let best = Infinity, bi = -1;
      for (let i = 0; i < way.points_enu_m.length; i += 1) {
        const q = way.points_enu_m[i], d = (q[0] - re) ** 2 + (q[1] - rn) ** 2;
        if (d < best) { best = d; bi = i; }
      }
      if (Math.sqrt(best) <= PATH_TOL_M && Math.abs(wrapAngle(p.yaw - way.yaw_rad[bi])) <= PATH_YAW_TOL) return true;
    }
    return false;
  }
  const D = Math.SQRT1_2;
  const ring = (r) => [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r], [r * D, r * D], [-r * D, r * D], [r * D, -r * D], [-r * D, -r * D]];
  const groundOk = (e, n) => (onRoad?.(e, n) ?? false) || onDrive(e, n) || onFloor(e, n);
  /** One pose: on the way, inside the doorway and room, its wheels and hooves on what carries them. */
  function poseClear(row, p) {
    if (!onWay(row, p)) return false;
    let touches = false;
    for (const poly of teamOutline(row, p, CLEAR_MARGIN_M)) {
      for (const [e, n] of polygonSamples(poly)) {
        const [u, v] = toPlanUV(e, n);
        const [d, s] = toDS(e, n);
        if (d < frame.kerb) touches = true;
        if (Array.isArray(polygon) && insidePoly(u, v, polygon) && !allowedInside(dims, d, s)) return false;
      }
    }
    // Only a pose that reaches over the kerb line is the coach house's to admit.
    if (!touches) return false;
    if (onRoad) {
      const { wheels, hooves } = teamGroundPoints(row, p);
      for (const [list, room] of [[wheels, KERB_ROOM_M.wheel], [hooves, KERB_ROOM_M.hoof]]) {
        for (const [e, n] of list) if (!ring(room).every(([a, b]) => groundOk(e + a, n + b))) return false;
      }
    }
    return true;
  }
  /** The header: every pose from `from` to `to`, sampled as transport-clearance.js samples. */
  function clearFor(row, from, to = from) {
    if (!(leaves.swing >= 1 && leaves.target === 1)) return false;
    const env = row?.envelope_measured_local_xz_m ?? row?.envelope_local_xz_m ?? BROUGHAM.envelope_measured_local_xz_m;
    const r = { ...BROUGHAM, ...(row ?? {}), envelope_measured_local_xz_m: env };
    const length = Math.hypot(to.e - from.e, to.n - from.n);
    const turn = wrapAngle(to.yaw - from.yaw);
    const radius = Math.max(...env.map(Math.abs));
    const count = Math.max(1, Math.ceil((length + Math.abs(turn) * radius) / 0.1));
    const s0 = from.steering ?? 0, s1 = to.steering ?? s0;
    for (let i = 0; i <= count; i += 1) {
      const t = i / count;
      const p = { e: from.e + (to.e - from.e) * t, n: from.n + (to.n - from.n) * t, yaw: from.yaw + turn * t, steering: s0 + (s1 - s0) * t };
      if (!poseClear(r, p)) return false;
    }
    return true;
  }

  // ---- the frame
  function update(dt) {
    const instant = (() => { try { return !!reducedMotion(); } catch { return false; } })();
    // The man door shuts before the leaves swing; it opens only while they are shut.
    const leavesMay = leaves.target === 0 || man.swing <= 0;
    let moved = false;
    if (man.swing !== man.target && (man.target === 0 || leaves.swing <= 0)) {
      man.swing = instant ? man.target : clamp(man.swing + Math.sign(man.target - man.swing) * dt / MAN_DOOR_SWING_S, 0, 1);
      moved = true;
      if (man.swing === man.target) settle(man, { ok: true });
    }
    if (leavesMay && leaves.swing !== leaves.target) {
      leaves.swing = instant ? leaves.target : clamp(leaves.swing + Math.sign(leaves.target - leaves.swing) * dt / COACH_SWING_S, 0, 1);
      moved = true;
      if (leaves.swing === leaves.target) settle(leaves, { ok: true });
    }
    if (moved) pose();
    sync(leavesThing, leaves);
    sync(manThing, man);
  }

  return {
    group, plan, dims, frame, lanes,
    get state() { return stateOf(leaves); },
    get swing() { return leaves.swing; },
    open: () => request(leaves, 1, 'leaves'),
    close: () => request(leaves, 0, 'leaves'),
    manDoor: plan.man ? {
      get state() { return stateOf(man); },
      get swing() { return man.swing; },
      open: () => request(man, 1, 'man'),
      close: () => request(man, 0, 'man'),
    } : null,
    things: [leavesThing, manThing].filter(Boolean),
    /** The leaves' swing as an ENU polygon (with a visitor's radius round it). */
    sweep: () => sweepLeaves.map((p) => [...p]),
    setBlocker(fn) { blocker = typeof fn === 'function' ? fn : null; },
    drivePath,
    clearFor,
    floorAt: (e, n) => (onFloor(e, n) ? sillY : null),
    update(dt) { if (dt > 0) update(dt); },
    /** After the buildings layer is rebuilt (a detail switch): hang its leaves instead. */
    rebind(layer) {
      const m = layer?.matrixOf?.(record.id);
      if (m) { matrix.copy(m); holder.matrix.copy(m); }
      if (!hang(layer)) problems.push(`${plan.id}: the rebuilt house carries no coach-house leaves to hang`);
      pose();
    },
    dispose() {
      for (const g of owned.splice(0)) g.dispose();
      room.geometry.dispose();
      roomMaterial.dispose();
      for (const x of [leaves, man]) settle(x, { ok: false, why: 'gone' });
      if (interactions) for (const t of [leavesThing, manThing]) if (t) interactions.remove(t.id);
    },
  };
}
