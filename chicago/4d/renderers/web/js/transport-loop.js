// SPDX-License-Identifier: GPL-3.0-or-later
/** A rear-axle circle, measured in local ENU metres. No renderer or input ownership. */
import { driveLimits, easeControls, easeReverse, bicycleStep, sampleOf, wheelArcRatios, pursuitSteering,
  trackingSteering, routeError, refineRouteDistance, refusalWord, bestRejoinDistance, rejoinCost } from './team-drive.js';
// (routeDistanceNear is defined below and used by branchAt.)
const TAU = 2 * Math.PI;
/** T-3557: the most an admitted carriage drive's kerb ramp may tip the coach's wheels apart, metres. */
const RAMP_GAP_M = .3;
/**
 * T-3557: an open way (a coach house's drive) read as a road is read: at(s) gives the rear
 * axle's sample s metres along it. Its yaw and curvature are the given ones where the way
 * carries them (coach-house.js drivePath), else read off its points.
 */
export function wayOf(points) {
  const at = [0];
  for (let i = 1; i < points.length; i++) at.push(at[i - 1] + Math.hypot(points[i].e - points[i - 1].e, points[i].n - points[i - 1].n));
  const length = at.at(-1);
  const yawAt = i => {
    if (Number.isFinite(points[i].yaw)) return points[i].yaw;
    const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)];
    return Math.atan2(b.e - a.e, -(b.n - a.n));
  };
  const yaws = points.map((_, i) => yawAt(i));
  const ks = points.map((p, i) => {
    if (Number.isFinite(p.k)) return p.k;
    if (i === 0 || i === points.length - 1) return 0;
    const d = at[i + 1] - at[i - 1];
    let dy = yaws[i + 1] - yaws[i - 1]; dy = Math.atan2(Math.sin(dy), Math.cos(dy));
    return d > 1e-9 ? dy / d : 0;
  });
  return {
    length,
    at(s) {
      const x = Math.max(0, Math.min(length, s));
      let i = 0, j = at.length - 1;
      while (j - i > 1) { const m = (i + j) >> 1; if (at[m] <= x) i = m; else j = m; }
      const f = at[j] > at[i] ? (x - at[i]) / (at[j] - at[i]) : 0;
      let dy = yaws[j] - yaws[i]; dy = Math.atan2(Math.sin(dy), Math.cos(dy));
      const yaw = yaws[i] + dy * f;
      // Past either end, straight on.
      const over = s - x, e = points[i].e + (points[j].e - points[i].e) * f + Math.sin(yaw) * over;
      const n = points[i].n + (points[j].n - points[i].n) * f - Math.cos(yaw) * over;
      return { e, n, yaw, forwardE: Math.sin(yaw), forwardN: -Math.cos(yaw), curvature: over ? 0 : ks[i] + (ks[j] - ks[i]) * f };
    },
  };
}
const finite = (n, label) => { if (!Number.isFinite(n)) throw Error(`transport loop: finite ${label} required`); return n; };
const wrap = (n, total) => ((n % total) + total) % total;

export function circleRoute({ center_enu_m, radius_m, clockwise = false, phase_rad = 0 }) {
  if (!Array.isArray(center_enu_m) || center_enu_m.length !== 2) throw Error('transport loop: ENU centre required');
  center_enu_m.forEach(n => finite(n, 'centre'));
  finite(radius_m, 'radius'); finite(phase_rad, 'phase');
  if (radius_m < 6) throw Error('transport loop: circle radius must be at least 6 metres');
  const direction = clockwise ? -1 : 1;
  const length = TAU * radius_m;
  return Object.freeze({
    length, radius: radius_m, direction, maxCurvature: 1 / radius_m,
    at(distance) {
      finite(distance, 'distance');
      const theta = phase_rad + direction * wrap(distance, length) / radius_m;
      const forwardE = -direction * Math.sin(theta), forwardN = direction * Math.cos(theta);
      return {
        e: center_enu_m[0] + radius_m * Math.cos(theta),
        n: center_enu_m[1] + radius_m * Math.sin(theta),
        forwardE, forwardN,
        yaw: Math.atan2(forwardE, -forwardN),
        curvature: direction / radius_m,
      };
    },
  });
}

/**
 * The supplied assembly keeps its real hierarchy: four wheel nodes, steering axle,
 * seat-bound driver and a separately qualified horse motion adapter. No mesh is baked
 * or merged here. `clear` checks a swept interval of poses, including the whole team.
 */
export function roundedBlockRoute({ bounds_enu_m, corner_radius_m, clockwise = false,
  origin_enu_m = [0, 0], rotation_rad = 0 }) {
  if (!Array.isArray(bounds_enu_m) || bounds_enu_m.length !== 4 || !bounds_enu_m.every(Number.isFinite)) throw Error('transport loop: [west,south,east,north] lane bounds required');
  const [west, south, east, north] = bounds_enu_m, r = finite(corner_radius_m, 'corner radius');
  if (!Array.isArray(origin_enu_m) || origin_enu_m.length !== 2 || !origin_enu_m.every(Number.isFinite)) throw Error('transport loop: finite route origin required');
  finite(rotation_rad, 'route rotation');
  if (r < 6 || east - west <= 2 * r || north - south <= 2 * r) throw Error('transport loop: invalid rounded block');
  const pieces = [];
  const line = (a, b) => {
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const forwardE = (b[0] - a[0]) / length, forwardN = (b[1] - a[1]) / length;
    pieces.push({ length, at: s => ({ e: a[0] + forwardE * s, n: a[1] + forwardN * s, forwardE, forwardN, curvature: 0 }) });
  };
  const arc = (e, n, from) => pieces.push({ length: Math.PI * r / 2, at: s => {
    const a = from + s / r;
    return { e: e + r * Math.cos(a), n: n + r * Math.sin(a), forwardE: -Math.sin(a), forwardN: Math.cos(a), curvature: 1 / r };
  } });
  line([west + r, south], [east - r, south]); arc(east - r, south + r, -Math.PI / 2);
  line([east, south + r], [east, north - r]); arc(east - r, north - r, 0);
  line([east - r, north], [west + r, north]); arc(west + r, north - r, Math.PI / 2);
  line([west, north - r], [west, south + r]); arc(west + r, south + r, Math.PI);
  const length = pieces.reduce((sum, p) => sum + p.length, 0);
  return Object.freeze({ length, maxCurvature: 1 / r,
    at(distance) {
      finite(distance, 'distance');
      let s = wrap(clockwise ? -distance : distance, length), sample;
      for (const piece of pieces) {
        if (s <= piece.length) { sample = piece.at(s); break; }
        s -= piece.length;
      }
      if (!sample) sample = pieces[0].at(0);
      if (clockwise) { sample.forwardE *= -1; sample.forwardN *= -1; sample.curvature *= -1; }
      const cosine = Math.cos(rotation_rad), sine = Math.sin(rotation_rad);
      const e = origin_enu_m[0] + cosine * sample.e - sine * sample.n;
      const n = origin_enu_m[1] + sine * sample.e + cosine * sample.n;
      const forwardE = cosine * sample.forwardE - sine * sample.forwardN;
      const forwardN = sine * sample.forwardE + cosine * sample.forwardN;
      return { ...sample, e, n, forwardE, forwardN, yaw: Math.atan2(forwardE, -forwardN) };
    },
  });
}

/**
 * T-3497: a closed road of straight legs joined by tangent arcs — a track that follows the
 * ground's own paths (1812's worn trails) rather than a circle or a town block. `points_enu_m`
 * are the corners in driving order (the last joins back to the first); every corner is rounded
 * to `corner_radius_m`, or to its own `corner_radii_m[i]` where a wider bend is wanted. A
 * corner's arc must fit inside both of its legs, so a road too tight for its team is refused
 * here rather than drawn with a cusp. Left turns carry positive curvature, as the block's do.
 */
export function pathRoute({ points_enu_m, corner_radius_m, corner_radii_m = null }) {
  if (!Array.isArray(points_enu_m) || points_enu_m.length < 3
    || !points_enu_m.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite))) throw Error('transport loop: at least three finite path corners required');
  finite(corner_radius_m, 'corner radius');
  if (corner_radius_m < 6) throw Error('transport loop: path corner radius must be at least 6 metres');
  const count = points_enu_m.length;
  if (corner_radii_m !== null && (!Array.isArray(corner_radii_m) || corner_radii_m.length !== count
    || !corner_radii_m.every(r => Number.isFinite(r) && r >= corner_radius_m))) throw Error('transport loop: one corner radius per path corner, none under the path minimum');
  const corners = points_enu_m.map((p, i) => {
    const a = points_enu_m[(i + count - 1) % count], b = points_enu_m[(i + 1) % count];
    const inLength = Math.hypot(p[0] - a[0], p[1] - a[1]), outLength = Math.hypot(b[0] - p[0], b[1] - p[1]);
    if (inLength < 1e-6 || outLength < 1e-6) throw Error('transport loop: repeated path corner');
    const din = [(p[0] - a[0]) / inLength, (p[1] - a[1]) / inLength];
    const dout = [(b[0] - p[0]) / outLength, (b[1] - p[1]) / outLength];
    const turn = Math.atan2(din[0] * dout[1] - din[1] * dout[0], din[0] * dout[0] + din[1] * dout[1]);
    if (Math.abs(turn) > Math.PI * 0.95) throw Error('transport loop: a path corner turns back on itself');
    const r = corner_radii_m ? corner_radii_m[i] : corner_radius_m;
    const tangent = r * Math.tan(Math.abs(turn) / 2);
    return { p, din, dout, turn, r, tangent, outLength };
  });
  const pieces = [];
  corners.forEach((c, i) => {
    const next = corners[(i + 1) % count];
    if (c.tangent + next.tangent > c.outLength + 1e-9) throw Error(`transport loop: path corners ${i} and ${(i + 1) % count} are too close for their bends`);
    if (Math.abs(c.turn) > 1e-9) {
      const side = Math.sign(c.turn); // +1 left (counter-clockwise)
      const start = [c.p[0] - c.din[0] * c.tangent, c.p[1] - c.din[1] * c.tangent];
      const centre = [start[0] - side * c.din[1] * c.r, start[1] + side * c.din[0] * c.r];
      const a0 = Math.atan2(start[1] - centre[1], start[0] - centre[0]);
      pieces.push({ length: Math.abs(c.turn) * c.r, at: s => {
        const a = a0 + side * s / c.r;
        return { e: centre[0] + c.r * Math.cos(a), n: centre[1] + c.r * Math.sin(a),
          forwardE: -side * Math.sin(a), forwardN: side * Math.cos(a), curvature: side / c.r };
      } });
    }
    const from = [c.p[0] + c.dout[0] * c.tangent, c.p[1] + c.dout[1] * c.tangent];
    const length = c.outLength - c.tangent - next.tangent;
    if (length > 1e-9) pieces.push({ length, at: s => ({ e: from[0] + c.dout[0] * s, n: from[1] + c.dout[1] * s,
      forwardE: c.dout[0], forwardN: c.dout[1], curvature: 0 }) });
  });
  const length = pieces.reduce((sum, p) => sum + p.length, 0);
  const maxCurvature = Math.max(...corners.filter(c => Math.abs(c.turn) > 1e-9).map(c => 1 / c.r), 0);
  return Object.freeze({ length, maxCurvature: maxCurvature || 1 / corner_radius_m,
    at(distance) {
      finite(distance, 'distance');
      let s = wrap(distance, length), sample;
      for (const piece of pieces) {
        if (s <= piece.length) { sample = piece.at(s); break; }
        s -= piece.length;
      }
      if (!sample) sample = pieces[0].at(0);
      return { ...sample, yaw: Math.atan2(sample.forwardE, -sample.forwardN) };
    },
  });
}

/** The route a driven row names: circle, rounded block or (T-3497) a closed path. */
export function routeFor(route) {
  if (route?.kind === 'rounded_block') return roundedBlockRoute(route);
  if (route?.kind === 'path') return pathRoute(route);
  return circleRoute(route);
}

/** T-3497: the route distance nearest a place, for a stop named by where it is. */
export function routeDistanceNear(route, e, n, step_m = .25) {
  let best = 0, bestD = Infinity;
  for (let s = 0; s < route.length; s += step_m) {
    const p = route.at(s), d = Math.hypot(p.e - e, p.n - n);
    if (d < bestD) { bestD = d; best = s; }
  }
  return { distance_m: best, off_m: bestD };
}

/** A live spawn obstruction is recoverable; malformed ground/route/asset inputs are not.
 * Store only the finite clearance pose, so a retry needs no GLB or full route reading. */
export class TransportSpawnObstructedError extends Error {
  constructor(pose) {
    if (!pose || !['e', 'n', 'yaw', 'height'].every(key => Number.isFinite(pose[key]))) {
      throw Error('transport loop: finite deferred spawn pose required');
    }
    super('transport loop: initial whole-team footprint is obstructed');
    this.name = 'TransportSpawnObstructedError';
    this.pose = Object.freeze({ e: pose.e, n: pose.n, yaw: pose.yaw, height: pose.height });
  }
}

export function createTransportLoop({
  id, name, route, assembly, speed_m_s, wheelbase_m, track_m,
  root_ahead_of_rear_axle_m, driver_local_m, wheel_radii_m,
  heightAt, clear = () => true, initial_distance_m = 0, steering_limit_deg,
  initial_total_distance_m = 0, initial_wheel_rotation_rad = [0, 0, 0, 0], initial_state = 'moving', person_id = null,
  stops = [], initial_dwell_s = 0, gate = null,
  passenger_local_m = null, passenger_eye_m = .8, why = null, road = null,
  cab_seat_local_m = null, cab_eye_m = null, initial_reason = null, admit = null, pathHeightAt = null,
}) {
  if (!id || !name || typeof route?.at !== 'function' || !assembly?.pose) throw Error('transport loop: id, name, route and assembly required');
  if (typeof heightAt !== 'function' || typeof clear !== 'function') throw Error('transport loop: ground and clearance readers required');
  [speed_m_s, wheelbase_m, track_m, root_ahead_of_rear_axle_m, initial_distance_m, steering_limit_deg, route.maxCurvature].forEach(n => finite(n, 'vehicle measure'));
  if (speed_m_s <= 0 || speed_m_s > 1.5 || wheelbase_m <= 0 || track_m <= 0 || route.maxCurvature * track_m / 2 >= 1) throw Error('transport loop: invalid vehicle pace or geometry');
  if (steering_limit_deg <= 0 || steering_limit_deg >= 90 || Math.atan(wheelbase_m * route.maxCurvature) > steering_limit_deg * Math.PI / 180 + 1e-12) throw Error('transport loop: route exceeds authored vehicle steering limit');
  if (!Array.isArray(driver_local_m) || driver_local_m.length !== 3 || !driver_local_m.every(Number.isFinite)) throw Error('transport loop: physical driver anchor required');
  // T-3557: the seat a visitor climbs up to, beside the driver (vehicle-root local; y = the
  // cushion). A row that names none is read as the driver's seat mirrored across the team.
  const passenger = passenger_local_m ?? [-driver_local_m[0], driver_local_m[1], driver_local_m[2]];
  if (!Array.isArray(passenger) || passenger.length !== 3 || !passenger.every(Number.isFinite)
    || !Number.isFinite(passenger_eye_m) || passenger_eye_m < 0) throw Error('transport loop: finite passenger seat required');
  if (why !== null && typeof why !== 'function') throw Error('transport loop: an optional refusal reader must be a function');
  // T-3557: the scene's carriageways, where it has them: `road(pose)` is false when a wheel or a
  // hoof of the team at that vehicle-root pose would leave them (team-drive.js
  // createCarriagewayReader), true on them, null while unread. Asked only of a driven team.
  if (road !== null && typeof road !== 'function') throw Error('transport loop: an optional carriageway reader must be a function');
  if (!Array.isArray(wheel_radii_m) || wheel_radii_m.length !== 4 || !wheel_radii_m.every(r => Number.isFinite(r) && r > 0)) throw Error('transport loop: four wheel radii required');
  finite(initial_total_distance_m, 'saved travelled distance');
  if (!['moving', 'stopped'].includes(initial_state) || initial_total_distance_m < 0
    || !Array.isArray(initial_wheel_rotation_rad) || initial_wheel_rotation_rad.length !== 4
    || !initial_wheel_rotation_rad.every(Number.isFinite)) throw Error('transport loop: invalid saved journey');
  // T-3497: timed stops along the road (a wagon loading at a door). Each is a route distance
  // and a dwell; the team pulls up exactly there, stands, then goes on. Dwelling is still the
  // 'moving' journey — only a visitor's Stop or an obstruction makes it 'stopped'.
  if (!Array.isArray(stops) || !stops.every(s => Number.isFinite(s?.distance_m) && Number.isFinite(s?.dwell_s) && s.dwell_s >= 0)) throw Error('transport loop: stops need a finite distance and dwell');
  // T-3557 (the Glessner ride): the seat INSIDE a closed carriage's cab, where the row has one
  // (vehicle-root local: x, z the eye's place in plan, y the cushion), and the eye above it.
  if (cab_seat_local_m !== null && (!Array.isArray(cab_seat_local_m) || cab_seat_local_m.length !== 3
    || !cab_seat_local_m.every(Number.isFinite) || !(cab_eye_m > 0))) throw Error('transport loop: a cab seat needs a finite place and eye height');
  // `admit(from, to)`: true where something outside the road's own rules lets a driven pose
  // through (the Glessner coach house's open doorway and drive, coach-house.js clearFor): the
  // kerb rule gives way to it there, the ground is read by `pathHeightAt`, and the carriage
  // may pitch on its ramp. The walls it crosses are `clear`'s to admit (town-transport.js).
  if (admit !== null && typeof admit !== 'function') throw Error('transport loop: an optional admission reader must be a function');
  if (pathHeightAt !== null && typeof pathHeightAt !== 'function') throw Error('transport loop: an optional path ground reader must be a function');
  const stopList = stops.map(s => ({ ...s, distance_m: wrap(s.distance_m, route.length) }));
  finite(initial_dwell_s, 'saved dwell');
  // Kevin, 2026-11-13: where roads cross, one team waits for the other (transport-crossings.js).
  // The gate says how far this team may go; waiting there is still the 'moving' journey.
  if (gate !== null && (typeof gate?.allow !== 'function' || typeof gate.moved !== 'function')) throw Error('transport loop: a crossing gate needs allow and moved');
  let giving = false;
  let dwell = Math.max(0, initial_dwell_s), dwellingAt = dwell > 0 ? stopList.find(s => Math.abs(s.distance_m - wrap(initial_distance_m, route.length)) < 1e-6) ?? null : null;
  let distance = wrap(initial_distance_m, route.length), totalDistance = initial_total_distance_m;
  let state = initial_state, reason = initial_state === 'stopped' ? initial_reason : null, disposed = false, visible = false;
  let lastPose = null, motionReset = true, audioSpeed = 0;
  const wheelRotation = [...initial_wheel_rotation_rad];
  const localToEnu = (p, x, z) => [p.e + Math.cos(p.yaw) * x + Math.sin(p.yaw) * z,
    p.n + Math.sin(p.yaw) * x - Math.cos(p.yaw) * z];
  // The vehicle-root pose of a rear-axle sample: the route's (poseAt) or, while the team is
  // driven, the live one the bicycle model steps (T-3557), through the same ground reading.
  const poseOf = (rear, steering, s, ramp = false) => {
    const [e, n] = localToEnu(rear, 0, root_ahead_of_rear_axle_m);
    const origin = { ...rear, e, n };
    const frontX = track_m / 2 * Math.cos(steering);
    const frontZ = track_m / 2 * Math.sin(steering);
    const wheelLocal = [
      [track_m / 2, -root_ahead_of_rear_axle_m],
      [-track_m / 2, -root_ahead_of_rear_axle_m],
      [frontX, wheelbase_m - root_ahead_of_rear_axle_m - frontZ],
      [-frontX, wheelbase_m - root_ahead_of_rear_axle_m + frontZ],
    ];
    const ground = ramp && pathHeightAt ? (x, y) => { const h = heightAt(x, y); return Number.isFinite(h) ? h : pathHeightAt(x, y); } : heightAt;
    const grounds = wheelLocal.map(([x, z]) => ground(...localToEnu(origin, x, z)));
    if (!grounds.every(Number.isFinite)) throw Error('transport loop: no rendered ground beneath all four wheels');
    let height = Math.max(...grounds), wheelGap = height - Math.min(...grounds), pitch = 0;
    if (wheelGap > 0.03) {
      // T-3557: over a carriage drive's kerb ramp (admitted, never on the road) the coach
      // pitches with its axles: each axle on its own higher wheel, the root between them.
      if (!ramp || wheelGap > RAMP_GAP_M) throw Error('transport loop: wheel plane exceeds 30mm rendered-ground variation');
      const back = Math.max(grounds[0], grounds[1]), front = Math.max(grounds[2], grounds[3]);
      pitch = -Math.atan2(front - back, wheelbase_m);
      height = back + (front - back) * root_ahead_of_rear_axle_m / wheelbase_m;
      wheelGap = Math.max(Math.abs(grounds[0] - grounds[1]), Math.abs(grounds[2] - grounds[3]));
      if (wheelGap > RAMP_GAP_M) throw Error('transport loop: wheel plane exceeds the ramp bound');
    }
    return { ...origin, height, wheelGap, rootAhead: root_ahead_of_rear_axle_m,
      steering, ...(ramp ? { ramp: true, pitch } : {}),
      driverAt: localToEnu(origin, driver_local_m[0], driver_local_m[2]),
      distance: s, totalDistance,
    };
  };
  const poseAt = s => {
    const rear = route.at(s);
    return poseOf(rear, Math.atan(wheelbase_m * rear.curvature), s);
  };
  const readNext = ds => {
    const next = poseAt(wrap(distance + ds, route.length));
    return clear(lastPose ?? poseAt(distance), next) ? next : null;
  };
  const draw = () => {
    lastPose = poseAt(distance);
    assembly.pose({ ...lastPose, totalDistance, wheelRotation: [...wheelRotation] });
  };
  const spawn = poseAt(distance);
  if (!clear(spawn, spawn)) throw new TransportSpawnObstructedError(spawn);
  draw();

  // T-3557: the reins. 'route' is the round above, untouched. In 'reins' the visitor drives:
  // a live rear-axle sample (`rear`) is stepped by the bicycle model each <= .05 s tick and
  // posed through the same poseOf. In 'returning' the driver steers it back onto the road,
  // then it rejoins there. A refused step never throws and never moves: the team pulls up.
  // Backing: under the reins, a team standing with the reins held pulled for back_hold_s backs
  // (speed < 0, at most reverse_m_s); steered home, the driver backs it off a wall that has
  // refused him for RECOVER_AFTER_S, on the opposite lock, a few metres at a time.
  const limits = driveLimits({ speed_m_s, steering_limit_deg, wheelbase_m });
  const INPUT_STALE_S = .3, DEG = Math.PI / 180;
  const RECOVER_AFTER_S = 2, RECOVER_ATTEMPTS = 6, RECOVER_BACK_M = [2, 3, 4];
  let mode = 'route', blocked = null, rear = null, speed = 0, steering = 0;
  let control = { throttle: 0, steer: 0 }, inputAge = Infinity, tracking = false, searchAge = 0;
  let reversing = false, backHold = 0, recover = null, refusedFor = 0, attempts = 0;
  // T-3557: off the round on a given way (a coach house's drive): 'path' drives it forward,
  // 'backing' backs out along the way it came in, 'parked' stands at its end.
  let path = null, trace = [], branch = null, branchArrived = false;
  const refused = () => { try { return why?.() ?? null; } catch { return null; } };
  /** Would the team, at this rear-axle sample and steering, put a wheel or hoof over the kerb? */
  const offRoad = (sample, steer) => {
    if (!road) return false;
    const [e, n] = localToEnu(sample, 0, root_ahead_of_rear_axle_m);
    try { return road({ e, n, yaw: sample.yaw, steering: steer }) === false; } catch { return false; }
  };
  /** The vehicle-root pose of a rear sample, for the admission reader (no ground read). */
  const rootOf = (sample, steer) => { const [e, n] = localToEnu(sample, 0, root_ahead_of_rear_axle_m); return { e, n, yaw: sample.yaw, steering: steer }; };
  const admits = (sample, steer) => {
    if (!admit || mode === 'route') return false;
    try { return admit(lastPose, rootOf(sample, steer)) === true; } catch { return false; }
  };
  const nearestNow = () => {
    const coarse = routeDistanceNear(route, rear.e, rear.n, .5);
    return refineRouteDistance(route, rear.e, rear.n, coarse.distance_m, .5, .1);
  };
  /** Pose the assembly at a candidate; on a refusal re-pose the last good one and say so. */
  const commit = (pose, wheels, travelledTotal) => {
    try { assembly.pose({ ...pose, totalDistance: travelledTotal, wheelRotation: [...wheels] }); }
    catch {
      try { assembly.pose({ ...lastPose, totalDistance, wheelRotation: [...wheelRotation] }); } catch { /* the last good pose stands */ }
      return false;
    }
    lastPose = pose; return true;
  };
  /** One driven tick: steer to `nextSteer`, then roll `ds` metres (ds < 0 backs). Returns the
   *  signed metres travelled. Backing turns each wheel back by its own arc; the travelled total
   *  (and the driver's ride clock that reads it) counts the metres either way. */
  const driveTick = (tick, nextSteer, ds) => {
    const k = Math.tan(nextSteer) / wheelbase_m;
    if (ds !== 0) {
      const sample = bicycleStep(rear, nextSteer, ds, wheelbase_m), run = Math.abs(ds);
      let next = null, word = null;
      const admitted = admits(sample, nextSteer);
      if (!admitted && offRoad(sample, nextSteer)) word = 'the kerb';
      else try { next = { ...poseOf(sample, nextSteer, distance, admitted), reversing: ds < 0 }; } catch (error) { word = refusalWord(error); }
      if (next && !clear(lastPose, next)) { word = refused() ?? 'a wall'; next = null; }
      if (next) {
        const ratios = wheelArcRatios(k, track_m, wheelbase_m);
        const wheels = wheelRotation.map((r, i) => wrap(r + ds * ratios[i] / wheel_radii_m[i], TAU));
        assembly.advance?.(tick, ds);
        if (commit({ ...next, totalDistance: totalDistance + run }, wheels, totalDistance + run)) {
          rear = sample; steering = nextSteer; totalDistance += run;
          wheels.forEach((r, i) => { wheelRotation[i] = r; });
          blocked = null; return ds;
        }
        word = 'rough ground';
      }
      // Pulled up. The wheels may still be turned where the team stands.
      speed = 0; blocked = word; assembly.stop?.();
    }
    if (Math.abs(nextSteer - steering) > 1e-12) {
      const sample = sampleOf(rear.e, rear.n, rear.yaw, k);
      let next = null;
      // The team swings with the front axle: a lock that would walk a horse up the kerb is
      // refused where it stands (unless it already stands over it, and may turn off it).
      const admitted = admits(sample, nextSteer);
      if (!admitted && offRoad(sample, nextSteer) && !offRoad(rear, steering)) blocked = 'the kerb';
      else try { next = poseOf(sample, nextSteer, distance, admitted); } catch (error) { blocked = refusalWord(error); }
      if (next && commit(next, wheelRotation, totalDistance)) { rear = sample; steering = nextSteer; }
    }
    return 0;
  };
  /** Back on the road at its nearest distance: 'route' again, the crossing gate restored. */
  const rejoin = force => {
    let d = distance;
    if (force) d = nearestNow().distance_m;
    else {
      const err = routeError(route, rear, d);
      if (Math.abs(err.lateral_m) > .08 || Math.abs(err.heading_rad) > 1.5 * DEG
        || Math.abs(steering - Math.atan(wheelbase_m * err.curvature)) > 2.5 * DEG) return false;
    }
    let pose;
    try { pose = poseAt(d); } catch { return false; }
    if (!clear(force ? pose : lastPose, pose)) { if (!force) blocked = refused() ?? 'a wall'; return false; }
    if (gate?.rejoin && !gate.rejoin(d)) { blocked = 'another team'; return false; }
    if (!commit(pose, wheelRotation, totalDistance)) { gate?.drop?.(); return false; }
    distance = d; mode = 'route'; rear = null; speed = 0; steering = pose.steering;
    blocked = null; tracking = false; giving = false; motionReset = true; inputAge = Infinity;
    reversing = false; backHold = 0; recover = null; refusedFor = 0; attempts = 0;
    return true;
  };
  /** The driver's own hands on the reins: pure pursuit far off, a settling law near the road. */
  const returnInput = tick => {
    searchAge += tick;
    distance = refineRouteDistance(route, rear.e, rear.n, distance, 3).distance_m;
    if (searchAge >= 1) {
      // Another stretch of the road may have become the better one; switch only for a clear gain.
      searchAge = 0;
      const other = bestRejoinDistance(route, rear);
      if (other.cost < rejoinCost(route, rear, distance) - 2) { distance = other.distance_m; tracking = false; }
    }
    const err = routeError(route, rear, distance), off = Math.abs(err.lateral_m), turn = Math.abs(err.heading_rad);
    if (tracking ? off > 2.5 || turn > 40 * DEG : off < 1.5 && turn < 25 * DEG) tracking = !tracking;
    const want = tracking ? trackingSteering(route, rear, distance, limits)
      : pursuitSteering(rear, route.at(distance + limits.lookahead_m), limits);
    return { throttle: limits.route_m_s / limits.max_m_s, steer: -want / limits.steer_max_rad };
  };
  /** T-3557: the driver's hands on a given way (a coach house's drive): its own curvature fed
   *  forward, offset and heading corrected (trackingSteering, as a rejoining team keeps its
   *  road), slowing to a stand at its end. `remaining` is the metres of it left. */
  const pathInput = () => {
    path.s = refineRouteDistance(path.way, rear.e, rear.n, path.s, 2, .1).distance_m;
    const remaining = Math.max(0, path.way.length - path.s);
    const want = trackingSteering(path.way, rear, Math.min(path.s, path.way.length), limits);
    const v = Math.min(path.speed, Math.sqrt(2 * limits.brake_m_s2 * .5 * remaining));
    return { throttle: remaining <= 0 ? 0 : v / limits.max_m_s, steer: -want / limits.steer_max_rad, remaining };
  };
  /** T-3557: a given way that carries its own yaw and curvature (coach-house.js drivePath, made
   *  for the bicycle model) is driven exactly, as a road is: the rear axle on it, the lock its
   *  curvature's. Where the team leaves its own lane for it, the offset between them is eased
   *  out over `PATH_EASE_M` (a smooth lane change), so nothing jumps. */
  const PATH_EASE_M = 12;
  const pathSample = s1 => {
    const w = path.way.at(s1);
    const x = s1 - path.s0, u = Math.min(1, Math.max(0, x / PATH_EASE_M)), easing = x < PATH_EASE_M;
    // Offset (left of the way) and its first two derivatives along it: (1 - smoothstep).
    const f = 1 - u * u * (3 - 2 * u), df = easing ? -6 * u * (1 - u) / PATH_EASE_M : 0;
    const ddf = easing ? -(6 - 12 * u) / (PATH_EASE_M * PATH_EASE_M) : 0;
    const lat = path.lat0 * f, slope = path.lat0 * df, bend = path.lat0 * ddf;
    const yaw = w.yaw + Math.atan(slope);
    // Left of the way: (-forwardN, forwardE).
    const e = w.e - w.forwardN * lat, n = w.n + w.forwardE * lat;
    const k = w.curvature + bend * Math.pow(Math.cos(Math.atan(slope)), 3);
    return sampleOf(e, n, yaw, k);
  };
  const pathTick = tick => {
    const remaining = Math.max(0, path.way.length - path.s);
    const want = Math.min(path.speed, Math.sqrt(2 * limits.brake_m_s2 * .5 * remaining));
    speed = speed < want ? Math.min(want, speed + limits.accel_m_s2 * tick) : Math.max(want, speed - limits.brake_m_s2 * tick);
    const ds = Math.min(speed * tick, remaining);
    if (remaining <= .01) return { done: true, moved: 0 };
    if (ds <= 1e-9) { speed = Math.max(speed, .05); return { moved: 0 }; }
    const sample = pathSample(path.s + ds), nextSteer = Math.max(-limits.steer_max_rad, Math.min(limits.steer_max_rad, Math.atan(wheelbase_m * sample.curvature)));
    const admitted = admits(sample, nextSteer);
    let next = null, word = null;
    if (!admitted && offRoad(sample, nextSteer)) word = 'the kerb';
    else try { next = poseOf(sample, nextSteer, distance, admitted); } catch (error) { word = refusalWord(error); }
    if (next && !clear(lastPose, next)) { word = refused() ?? 'a wall'; next = null; }
    if (next) {
      const ratios = wheelArcRatios(sample.curvature, track_m, wheelbase_m);
      const wheels = wheelRotation.map((r, i) => wrap(r + ds * ratios[i] / wheel_radii_m[i], TAU));
      assembly.advance?.(tick, ds);
      if (commit({ ...next, totalDistance: totalDistance + ds }, wheels, totalDistance + ds)) {
        rear = sample; steering = nextSteer; totalDistance += ds; path.s += ds;
        wheels.forEach((r, i) => { wheelRotation[i] = r; });
        blocked = null; return { moved: ds };
      }
      word = 'rough ground';
    }
    // Held (someone in the way, the leaves not open): it waits there, and goes on when it can.
    speed = 0; blocked = word; assembly.stop?.();
    return { moved: 0 };
  };
  /** Back one tick along the way it came in (the trace of its own admitted poses), exactly. */
  const backTick = tick => {
    let want = limits.reverse_m_s * tick, moved = 0, k = trace.length - 1;
    while (k > 0 && moved < want) { moved += Math.hypot(trace[k].rear.e - trace[k - 1].rear.e, trace[k].rear.n - trace[k - 1].rear.n); k--; }
    if (k === trace.length - 1) return 0;
    const to = trace[k], admitted = admits(to.rear, to.steering);
    let next = null, word = null;
    try { next = { ...poseOf(to.rear, to.steering, distance, admitted), reversing: true }; } catch (error) { word = refusalWord(error); }
    if (next && !clear(lastPose, next)) { word = refused() ?? 'a wall'; next = null; }
    if (next) {
      const ratios = wheelArcRatios(Math.tan(to.steering) / wheelbase_m, track_m, wheelbase_m);
      const wheels = wheelRotation.map((r, i) => wrap(r - moved * ratios[i] / wheel_radii_m[i], TAU));
      assembly.advance?.(tick, -moved);
      if (commit({ ...next, totalDistance: totalDistance + moved }, wheels, totalDistance + moved)) {
        rear = to.rear; steering = to.steering; totalDistance += moved; speed = -moved / tick;
        wheels.forEach((r, i) => { wheelRotation[i] = r; });
        trace.length = k + 1; blocked = null;
        return moved;
      }
      word = 'rough ground';
    }
    speed = 0; blocked = word; assembly.stop?.();
    return 0;
  };
  const arrive = () => {
    const done = path?.onArrive;
    mode = 'parked'; speed = 0; state = 'stopped'; reason = 'parked'; motionReset = true; assembly.stop?.();
    if (path) path.done = true;
    try { done?.(); } catch { /* the caller's own */ }
  };
  const driveFrame = dt => {
    if (mode === 'parked') return 0;
    // The input given before this frame drives this frame, however long it is: aged first, a
    // frame slower than INPUT_STALE_S (a 3 fps phone, a hitch) dropped the reins every frame.
    const held = inputAge > INPUT_STALE_S ? { throttle: 0, steer: 0 } : control;
    inputAge += dt;
    if (mode === 'returning' && !visible && rejoin(true)) return 0;
    let remaining = Math.min(dt, .25), travelled = 0;
    while (remaining > 1e-10 && mode !== 'route' && mode !== 'parked') {
      const tick = Math.min(remaining, .05); remaining -= tick;
      if (mode === 'backing') {
        const moved = backTick(tick);
        travelled += moved;
        // Backed far enough (the caller's `until`: the team clear of a doorway): it stands there.
        let far = false;
        if (moved > 0 && path?.until) { try { far = !!path.until({ ...rear }); } catch { far = false; } }
        if (trace.length <= 1 || far) { arrive(); break; }
        continue;
      }
      if (mode === 'returning' && recover) {
        // The driver backs off what refused him: opposite lock, eased, and to a stand at the end.
        const stopping = speed * speed / (2 * limits.brake_m_s2);
        const eased = easeReverse({ speed, steering }, { throttle: recover.left_m > stopping + 1e-6 ? -1 : 0, steer: recover.steer }, limits, tick);
        speed = eased.speed;
        const moved = Math.abs(driveTick(tick, eased.steering, speed * tick));
        travelled += moved; recover.left_m -= moved;
        // Refused while backing, or backed far enough and stood: walk on toward the road again.
        if ((moved === 0 && speed === 0 && blocked) || (recover.left_m <= stopping + 1e-6 && speed === 0)) {
          recover = null; speed = 0; refusedFor = 0; searchAge = 1; tracking = false;
        }
        continue;
      }
      if (mode === 'path' && path.exact) {
        const r = pathTick(tick);
        travelled += r.moved;
        if (r.moved) trace.push({ rear: { ...rear }, steering });
        if (r.done) { arrive(); break; }
        continue;
      }
      const input = mode === 'returning' ? returnInput(tick) : mode === 'path' ? pathInput() : held;
      if (mode === 'path' && input.remaining <= .08 && speed <= .05) { arrive(); break; }
      let eased;
      if (mode === 'reins' && reversing) {
        // Backing under the reins: pulled, it backs; let go or walked on, it comes to a stand.
        const back = input.throttle < 0;
        eased = easeReverse({ speed, steering }, back ? input : { throttle: 0, steer: input.steer }, limits, tick);
        if (!back && eased.speed === 0) reversing = false;
      } else {
        eased = easeControls({ speed, steering }, input, limits, tick);
        if (mode === 'reins' && input.throttle < 0 && eased.speed === 0) {
          backHold += tick;
          if (backHold >= limits.back_hold_s - 1e-9) { reversing = true; backHold = 0; }
        } else backHold = 0;
      }
      speed = eased.speed;
      if (mode === 'reins' && speed === 0 && !reversing && !(input.throttle > 0)) blocked = null;
      const moved = driveTick(tick, eased.steering, speed * tick);
      travelled += Math.abs(moved);
      if (mode === 'path' && moved !== 0) trace.push({ rear: { ...rear }, steering });
      if (mode === 'returning') {
        // Nose-first at a wall on full lock, the pursuit alone never gets out: after
        // RECOVER_AFTER_S refused, back a few metres on the opposite lock (bounded tries).
        // A person in the way is waited for, never backed away from.
        if (moved === 0 && blocked && blocked !== 'someone in the way' && input.throttle > 0) {
          refusedFor += tick;
          if (refusedFor >= RECOVER_AFTER_S - 1e-9 && attempts < RECOVER_ATTEMPTS) {
            const side = input.steer !== 0 ? -Math.sign(input.steer) : (attempts % 2 ? 1 : -1);
            recover = { left_m: RECOVER_BACK_M[attempts % RECOVER_BACK_M.length], steer: side };
            attempts++; refusedFor = 0; speed = 0;
          }
        } else if (moved !== 0) refusedFor = 0;
        if (!recover && rejoin(false)) break;
      }
    }
    return travelled;
  };

  const out = {
    id, name, personId: person_id,
    get at() { return [...lastPose.driverAt]; },
    /** T-3404: the compass bearing the team faces (forward is +z of the vehicle root). */
    get heading_deg() { return ((180 - lastPose.yaw * 180 / Math.PI) % 360 + 360) % 360; },
    get state() { return state; },
    /** Why it was last stopped ('interaction', 'obstruction', ...), null while it goes. */
    get reason() { return reason; },
    /** The vehicle-root pose last drawn (read only): where its envelope stands now. */
    get pose() { return lastPose; },
    /** T-3557: 'route' (its own round), 'reins' (the visitor drives) or 'returning'. */
    get mode() { return mode; },
    /** True while the team backs (under the reins, or the driver backing it off a wall). */
    get reversing() { return mode !== 'route' && !disposed && (speed < 0 || (mode === 'reins' && reversing) || !!recover); },
    /** While driven: the short word for what pulled it up ('a wall', 'the kerb', ...), else null. */
    get blocked() { return mode === 'route' ? null : blocked; },
    /** The rear axle's current pace, m/s (never negative): the round's while it goes, the reins' while driven. */
    get speed_m_s() {
      if (disposed || state !== 'moving') return 0;
      if (mode !== 'route') return Math.abs(speed);
      return dwell > 0 || giving ? 0 : speed_m_s;
    },
    /** The visitor's eye on the seat beside the driver (world ENU; y the absolute eye height). */
    seat(kind = 'box') {
      if (disposed || !lastPose) return null;
      if (kind === 'cab') {
        if (!cab_seat_local_m) return null;
        const [e, n] = localToEnu(lastPose, cab_seat_local_m[0], cab_seat_local_m[2]);
        return { e, n, y: lastPose.height + cab_seat_local_m[1] + cab_eye_m, yaw_rad: lastPose.yaw, heading_deg: out.heading_deg, kind: 'cab' };
      }
      const [e, n] = localToEnu(lastPose, passenger[0], passenger[2]);
      return { e, n, y: lastPose.height + passenger[1] + passenger_eye_m, yaw_rad: lastPose.yaw, heading_deg: out.heading_deg };
    },
    takeReins() {
      if (disposed) return false;
      if (mode === 'reins') return true;
      if (mode === 'path' || mode === 'backing' || mode === 'parked') { path = null; trace = []; speed = Math.max(0, speed); }
      if (mode === 'route') {
        // Off the round: the crossing keeper lets go of whatever this team held.
        // It carries on at the pace it had: its round's, or standing if it stood.
        speed = state === 'moving' && dwell === 0 && !giving ? speed_m_s : 0;
        gate?.drop?.(); giving = false; dwell = 0; dwellingAt = null;
        const r = route.at(distance);
        rear = sampleOf(r.e, r.n, r.yaw, r.curvature); steering = lastPose.steering;
      }
      mode = 'reins'; state = 'moving'; reason = null; blocked = null; tracking = false;
      control = { throttle: 0, steer: 0 }; inputAge = Infinity; motionReset = true;
      reversing = false; backHold = 0; recover = null; refusedFor = 0; attempts = 0;
      // Read the road where it stands now, so a scene's carriageways are in hand before it moves.
      if (road && lastPose) { try { road(lastPose); } catch { /* unread: today's rules */ } }
      return true;
    },
    drive({ throttle = 0, steer = 0 } = {}) {
      if (disposed || mode !== 'reins') return false;
      control = { throttle: Number.isFinite(throttle) ? Math.max(-1, Math.min(1, throttle)) : 0,
        steer: Number.isFinite(steer) ? Math.max(-1, Math.min(1, steer)) : 0 };
      inputAge = 0;
      return true;
    },
    /**
     * T-3557: leave the round onto a given way (`points`, [{e, n}] or [[e, n]], for the rear
     * axle: a coach house's drive), driven by the driver at `speed_m_s`; at its end the team
     * stands ('parked') and `onArrive` is called. Refused (false) while the reins are the
     * visitor's or a way of fewer than two points is given.
     */
    followPath(points, { speed_m_s: pace = .8, onArrive = null, yaw_rad = null, curvature_per_m = null } = {}) {
      if (disposed || mode === 'reins' || !Array.isArray(points) || points.length < 2) return false;
      const pts = points.map((p, i) => ({ ...(Array.isArray(p) ? { e: p[0], n: p[1] } : { e: p.e, n: p.n }),
        yaw: yaw_rad?.[i], k: curvature_per_m?.[i] }));
      if (!pts.every(p => Number.isFinite(p.e) && Number.isFinite(p.n))) return false;
      if (mode === 'route') {
        gate?.drop?.(); giving = false; dwell = 0; dwellingAt = null;
        const r = route.at(distance);
        rear = sampleOf(r.e, r.n, r.yaw, r.curvature); steering = lastPose.steering; speed = 0;
      }
      path = { points: pts, way: wayOf(pts), s: 0, speed: Math.min(Math.max(pace, .2), limits.max_m_s), onArrive, done: false,
        exact: Array.isArray(yaw_rad) && Array.isArray(curvature_per_m), lat0: 0 };
      if (path.exact) {
        // Where the rear axle stands against the way's start: along it (taken up by starting
        // there), and to its left (eased out over the first metres).
        const w0 = path.way.at(0);
        path.s = path.s0 = Math.max(0, Math.min(path.way.length / 2, (rear.e - w0.e) * w0.forwardE + (rear.n - w0.n) * w0.forwardN));
        const w = path.way.at(path.s);
        path.lat0 = (rear.e - w.e) * -w.forwardN + (rear.n - w.n) * w.forwardE;
        if (Math.abs(path.lat0) > 3 || Math.abs(Math.atan2(Math.sin(rear.yaw - w.yaw), Math.cos(rear.yaw - w.yaw))) > 10 * Math.PI / 180) { path = null; return false; }
      }
      trace = [{ rear: { ...rear }, steering }];
      mode = 'path'; state = 'moving'; reason = null; blocked = null; tracking = false; motionReset = true;
      reversing = false; backHold = 0; recover = null; refusedFor = 0; attempts = 0;
      return true;
    },
    /** T-3557: back out along the way it came in, to where it left its road, or only until
     *  `until(rear)` (the rear-axle sample {e, n, yaw}) is true; then it stands there. Backed out
     *  part way, a second backOut() backs on along the rest. */
    backOut({ onArrive = null, until = null } = {}) {
      if (disposed || mode !== 'parked' || trace.length < 2) return false;
      path = { ...(path ?? { points: [] }), onArrive, done: false, until: typeof until === 'function' ? until : null };
      mode = 'backing'; state = 'moving'; reason = null; blocked = null; motionReset = true; speed = 0;
      return true;
    },
    /** T-3557: pull up where the round passes nearest (e, n), to leave it there (reason 'branch').
     *  Null when the round passes no nearer than `within_m`. */
    branchAt(e, n, { within_m = 4 } = {}) {
      if (disposed || mode !== 'route') return null;
      const near = routeDistanceNear(route, e, n, .25);
      if (near.off_m > within_m) return null;
      const d = refineRouteDistance(route, e, n, near.distance_m, .5, .05);
      branch = { label: 'branch', distance_m: wrap(d.distance_m, route.length), dwell_s: 0 };
      branchArrived = false;
      // Already standing there: arrived.
      if (Math.abs(wrap(branch.distance_m - distance + route.length / 2, route.length) - route.length / 2) < .05) {
        branch = null; branchArrived = true; state = 'stopped'; reason = 'branch';
      }
      return { distance_m: d.distance_m, off_m: d.off_m };
    },
    cancelBranch() { branch = null; branchArrived = false; },
    /** Where it is off its round: 'path' | 'backing' | 'parked' (with the way's end reached), else null. */
    get way() { return mode === 'path' || mode === 'backing' || mode === 'parked' ? { mode, done: !!path?.done, traced: trace.length } : null; },
    get branched() { return branchArrived && reason === 'branch' && state === 'stopped'; },
    /** A vehicle-root local point ([x, y, z], y up from the wheels' ground) in world ENU and height. */
    toWorld([x, y, z]) {
      if (disposed || !lastPose) return null;
      const [e, n] = localToEnu(lastPose, x, z);
      return { e, n, y: lastPose.height + y + (lastPose.pitch ? -Math.sin(lastPose.pitch) * z : 0) };
    },
    get hasCab() { return !!cab_seat_local_m; },
    handBack() {
      if (disposed || mode === 'route') return false;
      if (mode === 'path' || mode === 'backing' || mode === 'parked') {
        mode = 'reins'; path = null; trace = []; speed = Math.max(0, speed);
      }
      if (mode === 'reins') {
        mode = 'returning'; state = 'moving'; reason = null; tracking = false; searchAge = 0;
        reversing = false; backHold = 0; recover = null; refusedFor = 0; attempts = 0;
        if (speed < 0) speed = 0; // a backing team stands before the driver takes it on
        distance = bestRejoinDistance(route, rear).distance_m;
      }
      return true;
    },
    /** T-3497: the stop the team stands at, while it dwells there; null on the road. */
    get dwelling() { return dwell > 0 ? dwellingAt : null; },
    /** The team it is pulled up for at a crossing, while it waits; null on the road. */
    get givingWayTo() { return giving ? gate?.waitingFor ?? null : null; },
    get visible() { return visible && !disposed; },
    get disposed() { return disposed; },
    // Read only actual admitted motion, never the nominal journey state (which
    // remains 'moving' during a loading stop). Anchors belong to loaded meshes.
    get audioState() { return { id, moving: !disposed && visible && state === 'moving' && dwell === 0 && audioSpeed > 0,
      speed: audioSpeed, anchors: !disposed && visible ? assembly.audioAnchors?.() ?? null : null }; },
    pickDriverAt(...args) { return disposed || !visible ? null : assembly.pickDriverAt?.(...args) ?? null; },
    previewAt(s) { return poseAt(wrap(s, route.length)); },
    stop(why = 'interaction') {
      if (disposed) return false;
      state = 'stopped'; reason = why; motionReset = true; audioSpeed = 0; speed = 0;
      assembly.stop?.();
      return true;
    },
    canResume() {
      if (!disposed && mode !== 'route') return true; // the reins (or the driver) take it on
      return !disposed && !!readNext(speed_m_s * 0.25);
    },
    resume() {
      if (!out.canResume()) return false;
      state = 'moving'; reason = null; motionReset = true;
      return true;
    },
    update(dt, { enabled = true, paused = false, reducedMotion = false, drawn = true,
      elapsedFrame = false, motionFrame = true } = {}) {
      finite(dt, 'frame time');
      if (dt < 0) throw Error('transport loop: negative frame time');
      audioSpeed = 0;
      if (disposed) return;
      const wasVisible = visible;
      visible = enabled && drawn;
      if (elapsedFrame && visible && !wasVisible) motionReset = true;
      assembly.visible?.(visible);
      // T-3557: put up while being steered home (hidden, off hours): nobody sees it rejoin.
      if (mode === 'returning' && !enabled) rejoin(true);
      // Draw reach only culls rendering. A loaded journey keeps approaching the
      // visitor offscreen, with the same bounded ground/clearance and gait steps.
      // Scene holds, hidden tabs and reduced motion still suspend the journey.
      if (!enabled || paused || reducedMotion || state !== 'moving') {
        motionReset = true; assembly.stop?.(); return;
      }
      // Full visible elapsed time is opt-in; existing bounded-dt callers retain
      // their original contract. Never charge pre-Continue/held/admission time.
      if (elapsedFrame) {
        if (!motionFrame) return;
        if (motionReset) { motionReset = false; return; }
      }
      if (mode !== 'route') {
        const travelled = driveFrame(dt);
        if (state === 'moving' && dt > 0) audioSpeed = travelled / dt;
        return;
      }
      // T-3497: standing at a stop. The clock runs down here; the team stands (its
      // distance-driven gait holds its phase) until it is spent.
      if (dwell > 0) {
        dwell = Math.max(0, dwell - dt);
        assembly.stop?.();
        if (dwell > 0) return;
        motionReset = true;
        if (elapsedFrame) return;
      }
      // Bound the rear axle's per-frame advance, not the slow horse's elapsed
      // time. Speed 1 + update(10) still advances at most .25m. Every accepted
      // metre takes the same <= .05s clearance/ground/wheel/gait steps below.
      let remaining = Math.min(dt, elapsedFrame ? 0.25 / speed_m_s : 0.25), travelled = 0;
      while (remaining > 1e-10) {
        let tick = Math.min(remaining, 0.05), ds = tick * speed_m_s;
        // T-3497: pull up exactly at the next stop ahead (a stop just left lies behind).
        let arriving = null;
        for (const s of branch ? [...stopList, branch] : stopList) {
          const ahead = wrap(s.distance_m - distance, route.length);
          if (ahead > 1e-6 && ahead <= ds && (!arriving || ahead < arriving.ahead)) arriving = { stop: s, ahead };
        }
        if (arriving) { ds = arriving.ahead; tick = ds / speed_m_s; }
        if (gate) {
          const allowed = gate.allow(distance, ds);
          giving = allowed < ds - 1e-9;
          if (giving) {
            arriving = null;
            if (!(allowed > 1e-6)) { assembly.stop?.(); break; }
            ds = allowed; tick = ds / speed_m_s;
          }
        }
        const next = readNext(ds);
        if (!next) { out.stop('obstruction'); break; }
        // Exact rear/front arc lengths for the independent wheel centres. Spinning
        // all wheels by the root's distance would skid both axles on every turn.
        const curvature = route.at(distance + ds / 2).curvature;
        for (let i = 0; i < 4; i++) {
          const x = i % 2 === 0 ? track_m / 2 : -track_m / 2;
          const ratio = (i < 2 ? 1 : Math.hypot(1, wheelbase_m * curvature)) - curvature * x;
          wheelRotation[i] = wrap(wheelRotation[i] + ds * ratio / wheel_radii_m[i], TAU);
        }
        distance = next.distance; totalDistance += ds; travelled += ds;
        gate?.moved(ds);
        assembly.advance?.(tick, ds);
        draw(); remaining -= tick;
        if (arriving) {
          distance = arriving.stop.distance_m;
          // T-3557: a stand (`hold`) or a turning off the round (a branch) is stood at until
          // the journey is resumed or the team is taken off its road there.
          if (arriving.stop.hold || arriving.stop === branch) {
            state = 'stopped'; reason = arriving.stop === branch ? 'branch' : 'stand'; motionReset = true; assembly.stop?.();
            if (arriving.stop === branch) { branch = null; branchArrived = true; }
            break;
          }
          if (arriving.stop.dwell_s > 0) { dwell = arriving.stop.dwell_s; dwellingAt = arriving.stop; assembly.stop?.(); break; }
        }
      }
      if (state === 'moving' && dwell === 0 && dt > 0) audioSpeed = travelled / dt;
    },
    snapshot() {
      // T-3557: a driven team is saved at its nearest place on its own road, so a tier or year
      // change restores it onto the route, never off it.
      const onRoute = mode !== 'route' && rear ? nearestNow().distance_m : distance;
      return { id, state, reason, mode, ...(mode !== 'route' ? { blocked, speed_m_s: Math.abs(speed), reversing: out.reversing } : {}),
        visible: out.visible, disposed, distance_m: onRoute,
        total_distance_m: totalDistance, at_enu_m: out.at,
        assembly_state: assembly.snapshot?.() ?? null,
        yaw_rad: lastPose.yaw, steering_rad: lastPose.steering,
        wheel_rotation_rad: [...wheelRotation], wheel_gap_m: lastPose.wheelGap,
        dwell_s: dwell, dwelling: dwell > 0 ? dwellingAt?.label ?? null : null,
        ...(gate ? { giving_way_to: out.givingWayTo } : {}) };
    },
    dispose() {
      if (disposed) return;
      disposed = true; visible = false; state = 'disposed';
      gate?.drop?.();
      assembly.dispose?.();
    },
  };
  return out;
}

/** Read the actual rendered ground and static obstructions around the WHOLE circuit
 * before loading/exposing a model. Live visitor clearance is checked again per step. */
function* routePreflightSteps({ row, route, heightAt, clear, support = null, sample_spacing_m = .25 }) {
  finite(sample_spacing_m, 'route sampling distance');
  if (sample_spacing_m <= 0 || sample_spacing_m > .25) throw Error('transport loop: route samples must be at most .25m apart');
  const actor = createTransportLoop({ ...row, route, heightAt, clear, assembly: { pose() {} } });
  let before = actor.previewAt(0), samples = 0, maxWheelGap = 0;
  const count = Math.ceil(route.length / sample_spacing_m);
  try {
    for (let i = 0; i <= count; i++) {
      const pose = actor.previewAt(i / count * route.length);
      if (!clear(before, pose)) throw Error(`transport loop: circuit obstruction at ${i / count * route.length}m`);
      support?.(pose);
      maxWheelGap = Math.max(maxWheelGap, pose.wheelGap); samples++; before = pose;
      yield samples;
    }
    return { status: support ? 'RENDERED_ROUTE_STATIC_CLEARANCE_AND_SUPPORT_SAMPLES_PASS'
      : 'RENDERED_ROUTE_STATIC_CLEARANCE_SAMPLES_PASS_HORSE_SUPPORT_UNRUN', samples, horse_support_reader_used: !!support,
      maximum_spacing_m: route.length / count, maximum_wheel_gap_m: maxWheelGap,
      full_circuit_length_m: route.length, source_runtime_or_phone_frame_acceptance: false };
  } finally { actor.dispose(); }
}

export function preflightTransportRoute(configuration) {
  const steps = routePreflightSteps(configuration);
  let next;
  do { next = steps.next(); } while (!next.done);
  return next.value;
}

/** Prefer a prioritized continuation while still yielding to input/browser work.
 * Older engines retain the original timer path; neither path changes the samples. */
function yieldRouteTask() {
  const scheduler = globalThis.scheduler;
  return typeof scheduler?.yield === 'function'
    ? scheduler.yield()
    : new Promise(resolve => setTimeout(resolve, 0));
}

/** Cooperative version for an already entered town. It yields BEFORE the first
 * reading and between small chunks; main's first frame and welcome never wait on it. */
export async function preflightTransportRouteAsync(configuration, {
  yieldEvery = 32, yieldControl = yieldRouteTask,
  cancelled = () => false,
} = {}) {
  if (!Number.isInteger(yieldEvery) || yieldEvery <= 0 || yieldEvery > 128) throw Error('transport loop: bounded preflight chunk required');
  await yieldControl();
  if (cancelled()) return { status: 'CANCELED_ROUTE_READING_NOT_PASS' };
  const steps = routePreflightSteps(configuration);
  try {
    for (;;) {
      for (let i = 0; i < yieldEvery; i++) {
        if (cancelled()) return { status: 'CANCELED_ROUTE_READING_NOT_PASS' };
        const next = steps.next(); if (next.done) return next.value;
      }
      await yieldControl();
    }
  } finally { steps.return(); }
}

export { supportsTownTransport } from './transport-scenes.js';
