// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3557: taking the reins of a driven team (Kevin, 2026-11-14: "we wanted to be able to board
 * and drive the team around"). Pure planar math, no renderer, no input: transport-loop.js keeps
 * a live rear-axle sample and steps it with these functions while the visitor drives, and
 * while the driver steers the team back onto its own road.
 *
 * Frames are transport-loop.js's: ENU metres; `yaw` with forward = (sin yaw, -cos yaw); local
 * +x is the team's LEFT, so a positive steering angle and a positive curvature turn left. The
 * visitor's `steer` is +1 = right, the other way round, and is turned into an angle here.
 */
export const DRIVE_SPEED_CAP_M_S = 1.5;
/** Backing: at most this pace, after the reins are held pulled this long at a stand. */
export const REVERSE_CAP_M_S = .4, BACK_HOLD_S = .4;
const DEG = Math.PI / 180;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const wrap = (n, total) => ((n % total) + total) % total;
export const wrapAngle = a => Math.atan2(Math.sin(a), Math.cos(a));

/** A rear-axle sample in the shape route.at(s) returns. */
export function sampleOf(e, n, yaw, curvature) {
  const y = wrapAngle(yaw);
  return { e, n, forwardE: Math.sin(y), forwardN: -Math.cos(y), yaw: y, curvature };
}

/**
 * The limits a row's team is driven within. Top speed is the createTransportLoop cap (the horse
 * walk's stride limit), never under the row's own pace; the steering is the row's authored lock.
 */
export function driveLimits({ speed_m_s, steering_limit_deg, wheelbase_m }) {
  if (![speed_m_s, steering_limit_deg, wheelbase_m].every(Number.isFinite) || speed_m_s <= 0
    || steering_limit_deg <= 0 || steering_limit_deg >= 90 || wheelbase_m <= 0) throw Error('team drive: finite pace, steering limit and wheelbase required');
  const steer_max_rad = steering_limit_deg * DEG;
  const min_radius_m = wheelbase_m / Math.tan(steer_max_rad);
  return Object.freeze({
    max_m_s: Math.min(DRIVE_SPEED_CAP_M_S, Math.max(speed_m_s, DRIVE_SPEED_CAP_M_S)),
    route_m_s: Math.min(speed_m_s, DRIVE_SPEED_CAP_M_S),
    accel_m_s2: .5, ease_m_s2: .6, brake_m_s2: 1.5,
    // Backing a few steps (a teamster backs his team off a wall): slow, eased, and only after
    // the team has stood a moment with the reins pulled.
    reverse_m_s: REVERSE_CAP_M_S, reverse_accel_m_s2: .3, back_hold_s: BACK_HOLD_S,
    steer_max_rad, steer_rate_rad_s: Math.max(steer_max_rad / .75, 10 * DEG),
    wheelbase_m, min_radius_m,
    // Pure pursuit looks this far down the road; near it, a tracking law settles the team
    // onto the line over about `settle_m` of travel (critically damped).
    lookahead_m: Math.max(6, .6 * min_radius_m), settle_m: Math.max(3, .4 * min_radius_m),
  });
}

export const easeToward = (value, target, rate, dt) => value + clamp(target - value, -rate * dt, rate * dt);

/**
 * One eased control step. throttle -1..1 (>0 walk on, faster; <0 pull up; backing is easeReverse's): the
 * speed eases toward max(0, throttle) * max. steer -1..1 (+1 right): the steering angle eases,
 * rate-limited, toward the lock, and back to straight when let go.
 */
export function easeControls({ speed, steering }, { throttle = 0, steer = 0 } = {}, limits, dt) {
  const t = clamp(Number.isFinite(throttle) ? throttle : 0, -1, 1), s = clamp(Number.isFinite(steer) ? steer : 0, -1, 1);
  const target = Math.max(0, t) * limits.max_m_s;
  const rate = t < 0 ? limits.brake_m_s2 : target > speed ? limits.accel_m_s2 : limits.ease_m_s2;
  return {
    speed: clamp(easeToward(speed, target, rate, dt), 0, limits.max_m_s),
    steering: clamp(easeToward(steering, -s * limits.steer_max_rad, limits.steer_rate_rad_s, dt),
      -limits.steer_max_rad, limits.steer_max_rad),
  };
}

/**
 * One eased step while the team backs. throttle < 0 backs it, eased to -throttle * the reverse
 * cap; anything else (let go, walk on) eases it to a stand at the brake rate. The speed is
 * negative while backing. Steering is eased exactly as easeControls eases it.
 */
export function easeReverse({ speed, steering }, { throttle = 0, steer = 0 } = {}, limits, dt) {
  const t = clamp(Number.isFinite(throttle) ? throttle : 0, -1, 1), s = clamp(Number.isFinite(steer) ? steer : 0, -1, 1);
  const target = t < 0 ? t * limits.reverse_m_s : 0;
  const rate = target < speed ? limits.reverse_accel_m_s2 : limits.brake_m_s2;
  return {
    speed: clamp(easeToward(speed, target, rate, dt), -limits.reverse_m_s, 0),
    steering: clamp(easeToward(steering, -s * limits.steer_max_rad, limits.steer_rate_rad_s, dt),
      -limits.steer_max_rad, limits.steer_max_rad),
  };
}

/** Bicycle model on the rear axle: an exact arc of curvature tan(steering)/wheelbase (ds < 0 backs it). */
export function bicycleStep(sample, steering, ds, wheelbase_m) {
  const k = Math.tan(steering) / wheelbase_m, y0 = sample.yaw;
  if (Math.abs(k * ds) < 1e-9) return sampleOf(sample.e + Math.sin(y0) * ds, sample.n - Math.cos(y0) * ds, y0, k);
  const y1 = y0 + k * ds;
  return sampleOf(sample.e + (Math.cos(y0) - Math.cos(y1)) / k, sample.n + (Math.sin(y0) - Math.sin(y1)) / k, y1, k);
}

/** Each wheel's arc length per metre of the rear axle (rear left, rear right, front left, front right). */
export function wheelArcRatios(curvature, track_m, wheelbase_m) {
  return [0, 1, 2, 3].map(i => {
    const x = i % 2 === 0 ? track_m / 2 : -track_m / 2;
    return (i < 2 ? 1 : Math.hypot(1, wheelbase_m * curvature)) - curvature * x;
  });
}

/** The steering angle that puts the rear axle on an arc through `target` (pure pursuit). */
export function pursuitSteering(sample, target, limits) {
  const de = target.e - sample.e, dn = target.n - sample.n, ld = Math.hypot(de, dn);
  if (ld < 1e-6) return 0;
  const ahead = de * sample.forwardE + dn * sample.forwardN;
  const left = -de * sample.forwardN + dn * sample.forwardE;
  const alpha = Math.atan2(left, ahead);
  // Behind the team: turn round on full lock (sin(alpha) alone would barely turn at all).
  if (Math.abs(alpha) > Math.PI / 2) return (alpha >= 0 ? 1 : -1) * limits.steer_max_rad;
  return clamp(Math.atan(2 * Math.sin(alpha) / ld * limits.wheelbase_m), -limits.steer_max_rad, limits.steer_max_rad);
}

/** Where the team stands against its road: signed left offset and heading error at a route distance. */
export function routeError(route, sample, distance_m) {
  const r = route.at(distance_m);
  return { lateral_m: (sample.e - r.e) * -r.forwardN + (sample.n - r.n) * r.forwardE,
    heading_rad: wrapAngle(sample.yaw - r.yaw), curvature: r.curvature, rear: r };
}

/** Near the road: curvature feedforward plus a critically damped correction of offset and heading. */
export function trackingSteering(route, sample, distance_m, limits) {
  const { lateral_m, heading_rad, curvature } = routeError(route, sample, distance_m);
  const w = 1 / limits.settle_m;
  const k = curvature - w * w * lateral_m - 2 * w * Math.sin(heading_rad);
  return clamp(Math.atan(limits.wheelbase_m * k), -limits.steer_max_rad, limits.steer_max_rad);
}

/** The route distance nearest (e, n) within `half_m` of `around` (sampled, then narrowed). */
export function refineRouteDistance(route, e, n, around, half_m = 2, step_m = .25) {
  const d2 = s => { const p = route.at(s); return (p.e - e) ** 2 + (p.n - n) ** 2; };
  let best = around, bestD = d2(around);
  for (let s = around - half_m; s <= around + half_m + 1e-9; s += step_m) {
    const d = d2(s); if (d < bestD) { bestD = d; best = s; }
  }
  let lo = best - step_m, hi = best + step_m;
  for (let i = 0; i < 40 && hi - lo > 1e-4; i++) {
    const a = lo + (hi - lo) / 3, b = hi - (hi - lo) / 3;
    if (d2(a) <= d2(b)) hi = b; else lo = a;
  }
  const mid = (lo + hi) / 2, dm = d2(mid);
  if (dm < bestD) { best = mid; bestD = dm; }
  return { distance_m: wrap(best, route.length), off_m: Math.sqrt(bestD) };
}

/**
 * Where on its road the driver steers a team back to: the nearest place that is going its way.
 * The cost is the distance plus `heading_m` metres for facing fully against the road, so a
 * narrow out-and-back road is rejoined on the side the team already faces along.
 */
export function rejoinCost(route, sample, distance_m, heading_m = 8) {
  const r = route.at(distance_m);
  return Math.hypot(sample.e - r.e, sample.n - r.n) + heading_m * (1 - Math.cos(sample.yaw - r.yaw)) / 2;
}
export function bestRejoinDistance(route, sample, { step_m = .5, heading_m = 8 } = {}) {
  let best = 0, bestCost = Infinity;
  for (let s = 0; s < route.length; s += step_m) {
    const c = rejoinCost(route, sample, s, heading_m);
    if (c < bestCost) { bestCost = c; best = s; }
  }
  const fine = refineRouteDistance(route, sample.e, sample.n, best, step_m, .1);
  return { distance_m: fine.distance_m, off_m: fine.off_m, cost: rejoinCost(route, sample, fine.distance_m, heading_m) };
}

/**
 * The team's footprint at a vehicle-root pose (e, n, yaw), in the shape transport-crossings.js
 * footprintAt returns, so its `overlaps` can compare it with another team's.
 */
export function footprintOfPose(pose, envelope_local_xz_m, margin = 0) {
  const c = Math.cos(pose.yaw), sn = Math.sin(pose.yaw);
  const [x0, z0, x1, z1] = envelope_local_xz_m;
  const corners = [[x0 - margin, z0 - margin], [x1 + margin, z0 - margin], [x1 + margin, z1 + margin], [x0 - margin, z1 + margin]]
    .map(([x, z]) => [pose.e + c * x + sn * z, pose.n + sn * x - c * z]);
  const es = corners.map(p => p[0]), ns = corners.map(p => p[1]);
  return { corners, w: Math.min(...es), e: Math.max(...es), s: Math.min(...ns), n: Math.max(...ns) };
}

/** A pose or ground refusal, in the short word the visitor is shown. */
export function refusalWord(error) {
  const m = String(error?.message ?? error ?? '');
  if (/30mm|wheel plane/.test(m)) return 'the kerb';
  return 'rough ground';
}

/**
 * Where a team stands on the ground at a vehicle-root pose (e, n, yaw, steering): its four
 * wheel centres and, when the row has a team, eight hoof points of the two horses swung with
 * the front axle. The same points, in the same frame, that tools/lay_driven_carriages_1904.mjs
 * auditRoad walks each 1904 road with, so the live drive and the laid roads ask one question.
 */
export function teamGroundPoints(row, pose) {
  const L = row.wheelbase_m, ra = row.root_ahead_of_rear_axle_m, half = row.track_m / 2, pivot = L - ra;
  const c = Math.cos(pose.steering ?? 0), sn = Math.sin(pose.steering ?? 0);
  const cy = Math.cos(pose.yaw), sy = Math.sin(pose.yaw);
  const toEnu = ([x, z]) => [pose.e + cy * x + sy * z, pose.n + sy * x - cy * z];
  const wheels = [[half, -ra], [-half, -ra], [half * c, pivot - half * sn], [-half * c, pivot + half * sn]].map(toEnu);
  const hooves = [];
  if (Number.isFinite(row.team_half_spacing_m) && Array.isArray(row.horse_offset_m) && Number.isFinite(row.horse_offset_m[2])) {
    const swing = (x, z) => [c * x + sn * (z - pivot), pivot - sn * x + c * (z - pivot)];
    for (const side of [-1, 1]) for (const dz of [-.9, .9]) for (const dx of [-.2, .2]) {
      hooves.push(toEnu(swing(side * row.team_half_spacing_m + dx, row.horse_offset_m[2] + dz)));
    }
  }
  return { wheels, hooves };
}

const insidePoly = (e, n, poly) => {
  let yes = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > n) !== (b[1] > n) && e < (b[0] - a[0]) * (n - a[1]) / (b[1] - a[1]) + a[0]) yes = !yes;
  }
  return yes;
};
/**
 * The live kerb rule. Room to the kerb, metres: the laying tool's (wheel .25, hoof .2) less
 * 5 cm, so a laid road, posed anywhere between the tool's quarter-metre samples, is never
 * refused by it, while a wheel or hoof that is about to leave the carriageway is.
 */
export const KERB_ROOM_M = Object.freeze({ wheel: .2, hoof: .15 });
/**
 * `(row, pose) => boolean`: is every wheel and hoof of the team, each with its room, on a
 * carriageway? `carriageways` are polygons in ENU metres (data/street_grid/<scene>.json
 * carriageways[].polygon_local_m).
 */
export function createCarriagewayReader(carriageways, { wheel_room_m = KERB_ROOM_M.wheel, hoof_room_m = KERB_ROOM_M.hoof } = {}) {
  const polys = (Array.isArray(carriageways) ? carriageways : [])
    .map(c => c?.polygon_local_m ?? c)
    .filter(p => Array.isArray(p) && p.length >= 3 && p.every(q => Array.isArray(q) && Number.isFinite(q[0]) && Number.isFinite(q[1])))
    .map(p => ({ p, w: Math.min(...p.map(q => q[0])), e: Math.max(...p.map(q => q[0])),
      s: Math.min(...p.map(q => q[1])), n: Math.max(...p.map(q => q[1])) }));
  if (!polys.length) throw Error('team drive: carriageway polygons required');
  const D = Math.SQRT1_2;
  const ring = room => [[0, 0], [room, 0], [-room, 0], [0, room], [0, -room], [room * D, room * D], [-room * D, room * D], [room * D, -room * D], [-room * D, -room * D]];
  const wheelRing = ring(wheel_room_m), hoofRing = ring(hoof_room_m);
  const onRoad = (e, n) => polys.some(q => e >= q.w && e <= q.e && n >= q.s && n <= q.n && insidePoly(e, n, q.p));
  const discOn = ([e, n], r) => r.every(([de, dn]) => onRoad(e + de, n + dn));
  return (row, pose) => {
    const { wheels, hooves } = teamGroundPoints(row, pose);
    return wheels.every(p => discOn(p, wheelRing)) && hooves.every(p => discOn(p, hoofRing));
  };
}
