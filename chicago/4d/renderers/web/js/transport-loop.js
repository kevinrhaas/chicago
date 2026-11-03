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
  let distance = wrap(initial_distance_m, route.length), totalDistance = initial_total_distance_m;
  let state = initial_state, reason = null, disposed = false, visible = false;
  let lastPose = null;
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
    get state() { return state; },
    get visible() { return visible && !disposed; },
    get disposed() { return disposed; },
    pickDriverAt(...args) { return disposed || !visible ? null : assembly.pickDriverAt?.(...args) ?? null; },
    previewAt(s) { return poseAt(wrap(s, route.length)); },
    stop(why = 'interaction') {
      if (disposed) return false;
      state = 'stopped'; reason = why;
      assembly.stop?.();
      return true;
    },
    canResume() {
      return !disposed && !!readNext(speed_m_s * 0.25);
    },
    resume() {
      if (!out.canResume()) return false;
      state = 'moving'; reason = null;
      return true;
    },
    update(dt, { enabled = true, paused = false, reducedMotion = false, drawn = true } = {}) {
      finite(dt, 'frame time');
      if (dt < 0) throw Error('transport loop: negative frame time');
      if (disposed) return;
      visible = enabled && drawn;
      assembly.visible?.(visible);
      // Draw reach only culls rendering. A loaded journey keeps approaching the
      // visitor offscreen, with the same bounded ground/clearance and gait steps.
      // Scene holds, hidden tabs and reduced motion still suspend the journey.
      if (!enabled || paused || reducedMotion || state !== 'moving') { assembly.stop?.(); return; }
      let remaining = Math.min(dt, 0.25);
      while (remaining > 1e-10) {
        const tick = Math.min(remaining, 0.05), ds = tick * speed_m_s;
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
      }
    },
    snapshot() {
      return { id, state, reason, visible: out.visible, disposed, distance_m: distance,
        total_distance_m: totalDistance, at_enu_m: out.at,
        assembly_state: assembly.snapshot?.() ?? null,
        yaw_rad: lastPose.yaw, steering_rad: lastPose.steering,
        wheel_rotation_rad: [...wheelRotation], wheel_gap_m: lastPose.wheelGap };
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

/** Cooperative version for an already entered town. It yields BEFORE the first
 * reading and between small chunks; main's first frame and welcome never wait on it. */
export async function preflightTransportRouteAsync(configuration, {
  yieldEvery = 32, yieldControl = () => new Promise(resolve => setTimeout(resolve, 0)),
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
