// SPDX-License-Identifier: GPL-3.0-or-later
/** A rear-axle circle, measured in local ENU metres. No renderer or input ownership. */
const TAU = 2 * Math.PI;
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
  stops = [], initial_dwell_s = 0,
}) {
  if (!id || !name || typeof route?.at !== 'function' || !assembly?.pose) throw Error('transport loop: id, name, route and assembly required');
  if (typeof heightAt !== 'function' || typeof clear !== 'function') throw Error('transport loop: ground and clearance readers required');
  [speed_m_s, wheelbase_m, track_m, root_ahead_of_rear_axle_m, initial_distance_m, steering_limit_deg, route.maxCurvature].forEach(n => finite(n, 'vehicle measure'));
  if (speed_m_s <= 0 || speed_m_s > 1.5 || wheelbase_m <= 0 || track_m <= 0 || route.maxCurvature * track_m / 2 >= 1) throw Error('transport loop: invalid vehicle pace or geometry');
  if (steering_limit_deg <= 0 || steering_limit_deg >= 90 || Math.atan(wheelbase_m * route.maxCurvature) > steering_limit_deg * Math.PI / 180 + 1e-12) throw Error('transport loop: route exceeds authored vehicle steering limit');
  if (!Array.isArray(driver_local_m) || driver_local_m.length !== 3 || !driver_local_m.every(Number.isFinite)) throw Error('transport loop: physical driver anchor required');
  if (!Array.isArray(wheel_radii_m) || wheel_radii_m.length !== 4 || !wheel_radii_m.every(r => Number.isFinite(r) && r > 0)) throw Error('transport loop: four wheel radii required');
  finite(initial_total_distance_m, 'saved travelled distance');
  if (!['moving', 'stopped'].includes(initial_state) || initial_total_distance_m < 0
    || !Array.isArray(initial_wheel_rotation_rad) || initial_wheel_rotation_rad.length !== 4
    || !initial_wheel_rotation_rad.every(Number.isFinite)) throw Error('transport loop: invalid saved journey');
  // T-3497: timed stops along the road (a wagon loading at a door). Each is a route distance
  // and a dwell; the team pulls up exactly there, stands, then goes on. Dwelling is still the
  // 'moving' journey — only a visitor's Stop or an obstruction makes it 'stopped'.
  if (!Array.isArray(stops) || !stops.every(s => Number.isFinite(s?.distance_m) && Number.isFinite(s?.dwell_s) && s.dwell_s >= 0)) throw Error('transport loop: stops need a finite distance and dwell');
  const stopList = stops.map(s => ({ ...s, distance_m: wrap(s.distance_m, route.length) }));
  finite(initial_dwell_s, 'saved dwell');
  let dwell = Math.max(0, initial_dwell_s), dwellingAt = dwell > 0 ? stopList.find(s => Math.abs(s.distance_m - wrap(initial_distance_m, route.length)) < 1e-6) ?? null : null;
  let distance = wrap(initial_distance_m, route.length), totalDistance = initial_total_distance_m;
  let state = initial_state, reason = null, disposed = false, visible = false;
  let lastPose = null, motionReset = true;
  const wheelRotation = [...initial_wheel_rotation_rad];
  const localToEnu = (p, x, z) => [p.e + Math.cos(p.yaw) * x + Math.sin(p.yaw) * z,
    p.n + Math.sin(p.yaw) * x - Math.cos(p.yaw) * z];
  const poseAt = s => {
    const rear = route.at(s);
    const [e, n] = localToEnu(rear, 0, root_ahead_of_rear_axle_m);
    const origin = { ...rear, e, n };
    const steering = Math.atan(wheelbase_m * rear.curvature);
    const frontX = track_m / 2 * Math.cos(steering);
    const frontZ = track_m / 2 * Math.sin(steering);
    const wheelLocal = [
      [track_m / 2, -root_ahead_of_rear_axle_m],
      [-track_m / 2, -root_ahead_of_rear_axle_m],
      [frontX, wheelbase_m - root_ahead_of_rear_axle_m - frontZ],
      [-frontX, wheelbase_m - root_ahead_of_rear_axle_m + frontZ],
    ];
    const grounds = wheelLocal.map(([x, z]) => heightAt(...localToEnu(origin, x, z)));
    if (!grounds.every(Number.isFinite)) throw Error('transport loop: no rendered ground beneath all four wheels');
    const height = Math.max(...grounds), wheelGap = height - Math.min(...grounds);
    if (wheelGap > 0.03) throw Error('transport loop: wheel plane exceeds 30mm rendered-ground variation');
    return { ...origin, height, wheelGap, rootAhead: root_ahead_of_rear_axle_m,
      steering,
      driverAt: localToEnu(origin, driver_local_m[0], driver_local_m[2]),
      distance: s, totalDistance,
    };
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

  const out = {
    id, name, personId: person_id,
    get at() { return [...lastPose.driverAt]; },
    /** T-3404: the compass bearing the team faces (forward is +z of the vehicle root). */
    get heading_deg() { return ((180 - lastPose.yaw * 180 / Math.PI) % 360 + 360) % 360; },
    get state() { return state; },
    /** T-3497: the stop the team stands at, while it dwells there; null on the road. */
    get dwelling() { return dwell > 0 ? dwellingAt : null; },
    get visible() { return visible && !disposed; },
    get disposed() { return disposed; },
    pickDriverAt(...args) { return disposed || !visible ? null : assembly.pickDriverAt?.(...args) ?? null; },
    previewAt(s) { return poseAt(wrap(s, route.length)); },
    stop(why = 'interaction') {
      if (disposed) return false;
      state = 'stopped'; reason = why; motionReset = true;
      assembly.stop?.();
      return true;
    },
    canResume() {
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
      if (disposed) return;
      const wasVisible = visible;
      visible = enabled && drawn;
      if (elapsedFrame && visible && !wasVisible) motionReset = true;
      assembly.visible?.(visible);
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
      let remaining = Math.min(dt, elapsedFrame ? 0.25 / speed_m_s : 0.25);
      while (remaining > 1e-10) {
        let tick = Math.min(remaining, 0.05), ds = tick * speed_m_s;
        // T-3497: pull up exactly at the next stop ahead (a stop just left lies behind).
        let arriving = null;
        for (const s of stopList) {
          const ahead = wrap(s.distance_m - distance, route.length);
          if (ahead > 1e-6 && ahead <= ds && (!arriving || ahead < arriving.ahead)) arriving = { stop: s, ahead };
        }
        if (arriving) { ds = arriving.ahead; tick = ds / speed_m_s; }
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
        distance = next.distance; totalDistance += ds;
        assembly.advance?.(tick, ds);
        draw(); remaining -= tick;
        if (arriving) {
          distance = arriving.stop.distance_m;
          if (arriving.stop.dwell_s > 0) { dwell = arriving.stop.dwell_s; dwellingAt = arriving.stop; assembly.stop?.(); break; }
        }
      }
    },
    snapshot() {
      return { id, state, reason, visible: out.visible, disposed, distance_m: distance,
        total_distance_m: totalDistance, at_enu_m: out.at,
        assembly_state: assembly.snapshot?.() ?? null,
        yaw_rad: lastPose.yaw, steering_rad: lastPose.steering,
        wheel_rotation_rad: [...wheelRotation], wheel_gap_m: lastPose.wheelGap,
        dwell_s: dwell, dwelling: dwell > 0 ? dwellingAt?.label ?? null : null };
    },
    dispose() {
      if (disposed) return;
      disposed = true; visible = false; state = 'disposed';
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
