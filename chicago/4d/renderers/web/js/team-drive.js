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
    steer_max_rad, steer_rate_rad_s: Math.max(steer_max_rad / .75, 10 * DEG),
    wheelbase_m, min_radius_m,
    // Pure pursuit looks this far down the road; near it, a tracking law settles the team
    // onto the line over about `settle_m` of travel (critically damped).
    lookahead_m: Math.max(6, .6 * min_radius_m), settle_m: Math.max(3, .4 * min_radius_m),
  });
}

export const easeToward = (value, target, rate, dt) => value + clamp(target - value, -rate * dt, rate * dt);

/**
 * One eased control step. throttle -1..1 (>0 walk on, faster; <0 pull up; no reversing): the
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

/** Bicycle model on the rear axle: an exact arc of curvature tan(steering)/wheelbase. */
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
