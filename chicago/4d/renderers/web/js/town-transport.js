// SPDX-License-Identifier: GPL-3.0-or-later
import { routeFor, createTransportLoop, preflightTransportRouteAsync, TransportSpawnObstructedError } from './transport-loop.js';
import { createCrossings, overlaps, footprintAt } from './transport-crossings.js';
import { footprintOfPose } from './team-drive.js';

const WHEELS = ['vehicle_wheel_rear_left', 'vehicle_wheel_rear_right',
  'vehicle_wheel_front_left', 'vehicle_wheel_front_right'];

// The horse root follows the real team pose, including its hitch offset. The
// vehicle root differs from the enclosing group for a teamster-led wagon.
function audioAnchors(root, vehicle, horse) {
  if (!root.visible || !vehicle.visible || !horse.root.visible) return null;
  const point = node => {
    const p = node.getWorldPosition(node.position.clone());
    return { x: p.x, y: p.y, z: p.z };
  };
  // The ordinary 250ms audio read needs only mechanical anchors. Hoof bones are
  // sampled lazily by the enabled hoof frame path (every year since T-3587), never by unrelated door audio.
  return { harness: point(horse.root), wagon: point(vehicle),
    get hoof() { return horse.audioHoofState?.() ?? null; } };
}

/**
 * Bind a separately owned, real GLTF scene, seated portable human and moving horse.
 * The loader retains responsibility for date/identity, contact and hitch validation;
 * this renderer does not substitute an ineligible person or idle-only horse.
 *
 * driver and horse are adapters: {root, update(dt, ...), dispose()}. horse.advance
 * consumes travelled metres at its own centre, not a camera speed or frame count.
 */
export function createDrivenAssembly({ vehicle, driver, horse, confidence,
  driverSeat_m, driverRootOffset_m = [0, 0, 0], horseOffset_m,
  disposeVehicle, hitch = null, patchMaterial = () => {}, passengers = [], door = null }) {
  if (!vehicle?.getObjectByName || !driver?.root || !horse?.root
    || (typeof horse.advance !== 'function' && typeof horse.poseVehicle !== 'function') || typeof horse.stop !== 'function'
    || typeof disposeVehicle !== 'function') throw Error('town transport: real vehicle, seated driver, distance-driven horse and ownership required');
  const seat = vehicle.getObjectByName('vehicle_seat_driver');
  if (!seat || !Array.isArray(driverSeat_m) || driverSeat_m.length !== 3
    || Math.hypot(...seat.position.toArray().map((n, i) => n - driverSeat_m[i])) > 1e-6) {
    throw Error('town transport: driver binding differs from the actual vehicle seat');
  }
  const wheels = WHEELS.map(name => vehicle.getObjectByName(name));
  const steer = vehicle.getObjectByName('vehicle_steer_front');
  if (wheels.some(node => !node) || !steer) throw Error('town transport: authored wheel and steering hierarchy required');
  for (const offset of [driverRootOffset_m, horseOffset_m]) {
    if (!Array.isArray(offset) || offset.length !== 3 || !offset.every(Number.isFinite)) throw Error('town transport: finite assembly offsets required');
  }
  const root = vehicle;
  // sit_drive contains a vehicle-local articulated pose. It is not translated to
  // its pelvis or seat a second time. Any registered vehicle-specific correction
  // belongs in driverRootOffset_m and is checked with the clothed body.
  driver.root.position.set(...driverRootOffset_m);
  horse.root.position.set(...horseOffset_m);
  root.add(driver.root, horse.root);
  // T-3557: people riding inside the cab (cab-passenger.js), on the vehicle as the driver is.
  for (const p of passengers) if (p?.root) root.add(p.root);
  root.traverse(node => {
    if (!node.isMesh || node.material?.visible === false) return;
    node.castShadow = true; node.receiveShadow = true;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      confidence?.patch?.(material); patchMaterial(material);
    }
  });
  const wheelRest = wheels.map(node => node.rotation.x), steerRest = steer.rotation.y;
  const horseRestYaw = horse.root.rotation.y;
  // The fore-carriage (Kevin, 2026-11-14: "allow it to make right turns"): the team is
  // hitched to the pole, and the pole to the front axle (draft-hitch.js re-seats it on a
  // pivot under vehicle_steer_front), so the horses swing with the axle about its king-pin
  // and stay abreast of the pole however sharp the turn. The pivot is the axle's place in
  // the vehicle's own frame.
  const pivot = steer.position.clone();
  for (let node = steer.parent; node && node !== root; node = node.parent) { node.updateMatrix(); pivot.applyMatrix4(node.matrix); }
  const swing = steering => {
    const c = Math.cos(steering), s = Math.sin(steering);
    const dx = horseOffset_m[0] - pivot.x, dz = horseOffset_m[2] - pivot.z;
    horse.root.position.set(pivot.x + c * dx + s * dz, horseOffset_m[1], pivot.z - s * dx + c * dz);
  };
  let priorHorse = null, stopped = true, disposed = false, visualReset = true;
  let lastPose = null, posed = false, reducedMotion = false;
  return {
    root, door, passengers,
    /** T-3557: prefers-reduced-motion for the door's swing (it is set, not swung). */
    setReducedMotion(on) { reducedMotion = !!on; },
    audioAnchors: () => disposed ? null : audioAnchors(root, vehicle, horse),
    pose(pose) {
      if (disposed) return;
      lastPose = pose; posed = true;
      root.position.set(pose.e, pose.height, -pose.n);
      // T-3557: over a carriage drive's kerb ramp the coach pitches with its axles; T-3558: on a
      // rutted earth street the wagon also leans with its wheels' ground (transport-loop.js).
      if (pose.pitch || pose.roll) root.rotation.set(pose.pitch ?? 0, pose.yaw, pose.roll ?? 0, 'YXZ'); else root.rotation.set(0, pose.yaw, 0, 'XYZ');
      steer.rotation.y = steerRest + pose.steering;
      swing(pose.steering);
      if (!horse.poseVehicle) {
        // A lone horse heads where its own place on the turning vehicle is going.
        const at = horse.root.position, rearAhead = at.z + pose.rootAhead;
        horse.root.rotation.y = horseRestYaw + Math.atan2(pose.curvature * rearAhead, 1 - pose.curvature * at.x);
      } else horse.root.rotation.y = horseRestYaw + pose.steering;
      wheels.forEach((node, i) => { node.rotation.x = wheelRest[i] + pose.wheelRotation[i]; });
      root.updateMatrixWorld(true);
      if (horse.poseVehicle) {
        horse.poseVehicle(pose); root.updateMatrixWorld(true);
        const connection = hitch?.update(pose);
        // On an admitted ramp, or in a rutted street's ruts (T-3558), the traces give a little
        // with the pitch; on a level road the bound stands.
        if (connection?.valid === false && !pose.ramp && !pose.rough) throw Error('town transport: actual hitch exceeds its declared connection bound');
        return;
      }
      const current = horse.root.getWorldPosition(horse.root.position.clone());
      if (priorHorse) {
        const distance = current.distanceTo(priorHorse);
        if (distance > 0) { horse.advance(distance); stopped = false; }
      }
      priorHorse = current;
      const connection = hitch?.update(pose);
      if (connection?.valid === false) throw Error('town transport: actual hitch exceeds its declared connection bound');
    },
    advance(dt) {
      if (dt > 0) stopped = false;
      // Legacy static clips retain their original vehicle clock. A qualified
      // looking clip instead consumes one independent visual frame below.
      if (!driver.updateVisual) driver.update?.(dt);
    },
    updateVisual(dt, { paused = false, viewer = null } = {}) {
      if (disposed || !driver.updateVisual) return;
      if (!Number.isFinite(dt) || dt < 0) throw Error('town transport: finite nonnegative driver visual time required');
      const held = paused || !root.visible;
      if (!held) horse.updateLod?.(viewer);
      // T-1790: the driver's motion layer reads the ride (travelled metres, the
      // turn) and whether the team is moving; a stopped carriage is still a ride.
      if (lastPose) driver.move?.(lastPose, posed && !stopped);
      driver.updateVisual(held || visualReset ? 0 : dt, held ? null : viewer);
      // T-3557: a cab's passengers and door move on the same visual clock.
      for (const p of passengers) p.update?.(held || visualReset ? 0 : dt, held ? null : viewer, lastPose, posed && !stopped);
      door?.update(held ? 0 : dt, { reducedMotion });
      visualReset = held;
      // The reins follow his hands. A moving carriage re-fits them in pose() next
      // frame; a stopped one is not posed, so they are re-fitted here.
      if (!posed && !held && lastPose && hitch) {
        root.updateMatrixWorld(true);
        const connection = hitch.update(lastPose);
        if (connection?.valid === false) throw Error('town transport: actual hitch exceeds its declared connection bound');
      }
      posed = false;
    },
    visible(value) {
      if (disposed) return;
      root.visible = value;
      if (!value && !stopped) { horse.stop(); stopped = true; }
    },
    stop() { if (!stopped) { horse.stop(); stopped = true; } },
    snapshot() { return { horse: horse.snapshot?.() ?? null, driver: driver.snapshot?.() ?? null, hitch: hitch?.snapshot?.() ?? null }; },
    dispose() {
      if (disposed) return;
      disposed = true; priorHorse = null;
      root.removeFromParent(); hitch?.dispose(); driver.dispose?.(); horse.dispose?.();
      for (const p of passengers) { p.dispose?.(); p.root?.removeFromParent(); }
      door?.dispose();
      // Remove independently owned skinned children before vehicle texture release.
      driver.root.removeFromParent(); horse.root.removeFromParent(); disposeVehicle();
    },
  };
}

/**
 * T-3497: a team led by a teamster ON FOOT, as an army wagon of 1812 was: he walks at the
 * near horse's head with a lead in his hand, and no one rides the wagon. The vehicle and its
 * horses are posed exactly as a driven assembly's; the teamster is an ordinary standing figure
 * (humans.js HumanActor, his own looks and walk) that his team tows: each frame he is put at
 * `walkerLocal_m` in the vehicle's frame, walking while the team moves and standing when it
 * stands. `walker` is that actor; he is drawn in world space beside the vehicle, not on it.
 */
export function createTeamsterAssembly({ root, vehicle, walker, horse, confidence, walkerLocal_m, horseOffset_m,
  disposeVehicle, hitch = null, patchMaterial = () => {} }) {
  if (!root?.add || root === vehicle || !vehicle?.getObjectByName || !walker?.root || typeof walker.update !== 'function'
    || typeof horse?.poseVehicle !== 'function' || typeof horse.stop !== 'function'
    || typeof disposeVehicle !== 'function') throw Error('town transport: real vehicle, teamster on foot, distance-driven team and ownership required');
  const wheels = WHEELS.map(name => vehicle.getObjectByName(name));
  const steer = vehicle.getObjectByName('vehicle_steer_front');
  if (wheels.some(node => !node) || !steer) throw Error('town transport: authored wheel and steering hierarchy required');
  for (const offset of [walkerLocal_m, horseOffset_m]) {
    if (!Array.isArray(offset) || offset.length !== 3 || !offset.every(Number.isFinite)) throw Error('town transport: finite assembly offsets required');
  }
  root.name = 'teamster-assembly';
  horse.root.position.set(...horseOffset_m);
  vehicle.add(horse.root);
  root.add(vehicle, walker.root);
  vehicle.traverse(node => {
    if (!node.isMesh || node.material?.visible === false) return;
    node.castShadow = true; node.receiveShadow = true;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      confidence?.patch?.(material); patchMaterial(material);
    }
  });
  const wheelRest = wheels.map(node => node.rotation.x), steerRest = steer.rotation.y;
  let stopped = true, disposed = false, lastPose = null, posed = false, target = null;
  walker.tow = () => target;
  const place = pose => {
    const [x, , z] = walkerLocal_m, c = Math.cos(pose.yaw), s = Math.sin(pose.yaw);
    target = { e: pose.e + c * x + s * z, n: pose.n + s * x - c * z,
      heading: ((180 - pose.yaw * 180 / Math.PI) % 360 + 360) % 360 };
  };
  return {
    root,
    walker,
    audioAnchors: () => disposed ? null : audioAnchors(root, vehicle, horse),
    pose(pose) {
      if (disposed) return;
      lastPose = pose; posed = true;
      vehicle.position.set(pose.e, pose.height, -pose.n); vehicle.rotation.y = pose.yaw;
      steer.rotation.y = steerRest + pose.steering;
      wheels.forEach((node, i) => { node.rotation.x = wheelRest[i] + pose.wheelRotation[i]; });
      vehicle.updateMatrixWorld(true);
      horse.poseVehicle(pose); vehicle.updateMatrixWorld(true);
      place(pose);
    },
    advance(dt) { if (dt > 0) stopped = false; },
    updateVisual(dt, { paused = false, viewer = null } = {}) {
      if (disposed) return;
      if (!Number.isFinite(dt) || dt < 0) throw Error('town transport: finite nonnegative teamster time required');
      const held = paused || !root.visible;
      if (!held) horse.updateLod?.(viewer);
      const moving = posed && !stopped && !held;
      const want = moving ? 'walking' : 'standing';
      if (walker.state !== want) walker.setState(want);
      if (viewer && !held) walker.update(dt, viewer);
      // The lead follows his hand, after he has walked this frame.
      if (lastPose && hitch && !held) {
        root.updateMatrixWorld(true);
        const connection = hitch.update(lastPose);
        if (connection?.valid === false) throw Error('town transport: actual hitch exceeds its declared connection bound');
      }
      posed = false;
    },
    visible(value) {
      if (disposed) return;
      root.visible = value;
      if (!value && !stopped) { horse.stop(); stopped = true; }
    },
    stop() { if (!stopped) { horse.stop(); stopped = true; } },
    snapshot() { return { horse: horse.snapshot?.() ?? null, driver: { on_foot: true, at: target }, hitch: hitch?.snapshot?.() ?? null }; },
    dispose() {
      if (disposed) return;
      disposed = true; walker.tow = null;
      root.removeFromParent(); hitch?.dispose(); horse.dispose?.(); walker.root.removeFromParent();
      disposeVehicle();
    },
  };
}

/** T-3497: outside a row's [from, to) local hours (`to` may pass midnight); no hour, never. */
export function offHours(hours, hour) {
  if (!Array.isArray(hours) || hours.length !== 2 || !hours.every(Number.isFinite) || !Number.isFinite(hour)) return false;
  const [from, to] = hours;
  return from <= to ? !(hour >= from && hour < to) : !(hour >= from || hour < to);
}

/** T-3557: a team's footprint for team-vs-team clearance (the row's whole team, pole and vehicle). */
const envelopeOf = row => Array.isArray(row?.envelope_local_xz_m) ? row.envelope_local_xz_m
  : Array.isArray(row?.envelope_measured_local_xz_m) ? row.envelope_measured_local_xz_m : null;
const TEAM_MARGIN_M = .3;
const OBSTACLE_M = .6;

/**
 * Kevin, 2026-11-16, of 1835: "we should have a lot of them running on loops around the city".
 * A row marked `streamed` is built only while it is near the visitor. The rest of the time it
 * is a ghost: a place on its road that keeps going at the team's pace, standing its stops and
 * keeping its hours, with no model, horse or teamster in memory. When a ghost comes within the
 * tier's reach plus `load_m` (nearest first, at most `cap` of them built at once) its team is
 * made there; when a built team is `drop_m` past the reach it is put away and goes on as a
 * ghost. A team the visitor rides, drives or has sent for is never put away. Ghosts do not give
 * way at crossings (nobody sees them); a ghost is not built where its team would stand on
 * another's, and waits for the next look. Light (and every phone) builds one at a time: the
 * first team costs a phone about 34 MB (measured 2026-11-17 on /1835/ at Light, far wagon), so
 * more is the phone thread's (T-3555) to buy back, with far stand-ins from `distant()`.
 */
const STREAM = { load_m: 35, drop_m: 70, cap: { full: 8, balanced: 6, light: 1 }, every_s: .5 };

/** A ghost's distance along its road after `dt` seconds, standing its stops on the way. */
export function advanceGhost(ghost, { length, speed_m_s, stops = [] }, dt) {
  let left = Math.max(0, dt);
  for (let guard = 0; left > 1e-9 && guard < 64; guard++) {
    if (ghost.dwell > 0) {
      const wait = Math.min(ghost.dwell, left);
      ghost.dwell -= wait; left -= wait;
      continue;
    }
    let ds = left * speed_m_s, arriving = null;
    for (const stop of stops) {
      const at = ((stop.distance_m % length) + length) % length;
      const ahead = ((at - ghost.distance) % length + length) % length;
      if (ahead > 1e-6 && ahead <= ds && (!arriving || ahead < arriving.ahead)) arriving = { stop, at, ahead };
    }
    if (arriving) ds = arriving.ahead;
    ghost.distance = ((ghost.distance + ds) % length + length) % length;
    ghost.total += ds; left -= ds / speed_m_s;
    if (arriving) { ghost.distance = arriving.at; ghost.dwell = arriving.stop.dwell_s; }
  }
  return ghost;
}

/** One instance per scene. The static parked layer remains independently owned.
 * `clearWhy(row)` (optional) names what last refused `clear(row, ...)`: 'visitor' or a footprint id.
 * `carriageway(row, pose)` (optional, T-3557): false when a wheel or hoof of that row's team at a
 * vehicle-root pose leaves the scene's carriageways, true on them, null while they are unread;
 * a driven team is refused the kerb by it. A scene without carriageway data passes none.
 * `obstacles()` (optional) lists what moves or stands in the street that a team must not drive
 * through (riding.js obstacles: saddle horses, town riders, stage horses), as { id, word, print }. */
export function createTownTransport({ rows, sceneId, makeAssembly, prepareAssembly = null, heightAt,
  clear, routeClear = clear, routeSupport = null, clearWhy = null, carriageway = null, detail = 'full',
  reach = { full: 90, balanced: 60, light: 45 }, problems = [], onActorsChanged = () => {},
  admit = null, pathHeightAt = null, stream = STREAM, obstacles = null }) {
  // T-3542: a tier draws the teams when its reach is above zero; since the owner's ruling
  // (2026-11-10) Light's is, so a phone keeps its horses, carriages and wagons, nearer.
  const draws = t => (reach[t] ?? 0) > 0;
  if (!Array.isArray(rows) || typeof makeAssembly !== 'function' || typeof clear !== 'function') throw Error('town transport: scene rows, assembly loader and clearance reader required');
  if (prepareAssembly !== null && typeof prepareAssembly !== 'function') throw Error('town transport: optional assembly preparation callback required');
  if (carriageway !== null && typeof carriageway !== 'function') throw Error('town transport: optional carriageway reader must be a function');
  // T-3557: `admit(row, from, to)` lets a driven team through what its road's rules refuse (the
  // Glessner coach house's open doorway and drive); `pathHeightAt` is the ground off the road.
  if (admit !== null && typeof admit !== 'function') throw Error('town transport: optional admission reader must be a function');
  // T-3557: a row `on_call` (the Glessner brougham, waiting at its door as a parked carriage)
  // is not loaded with the others: `summon(id)` brings it, `putAway(id)` lets it go again.
  const summoned = new Set();
  // T-3814: streamed rows a jaunt's stage has asked for, built wherever the visitor is and at any
  // hour (a stage takes them; a staged team keeps no hours), until the stage lets them go.
  const staging = new Set();
  const actors = [], roots = [];
  const saved = new Map();
  const pendingApproaches = new Map();
  const routeReadings = new Map(), deferred = new Map(), failed = new Set();
  const circuits = rows.filter(row => row.scene === sceneId).map(row => {
    const route = routeFor(row.route);
    const points = Array.from({ length: 65 }, (_, i) => route.at(route.length * i / 64));
    return { id: row.id, row, route, west: Math.min(...points.map(p => p.e)), east: Math.max(...points.map(p => p.e)),
      south: Math.min(...points.map(p => p.n)), north: Math.max(...points.map(p => p.n)) };
  });
  const rowById = new Map(circuits.map(circuit => [circuit.id, circuit.row]));
  // Streamed rows (STREAM above): each one's ghost, and the rows near enough to build now.
  const ghosts = new Map(circuits.filter(c => c.row.streamed).map(c => [c.id, {
    distance: ((c.row.initial_distance_m ?? 0) % c.route.length + c.route.length) % c.route.length,
    total: 0, dwell: 0 }]));
  const circuitById = new Map(circuits.map(circuit => [circuit.id, circuit]));
  // The first update chooses at once; nothing is built before the visitor has entered (ensureNear).
  let wanted = new Set(), streamClock = Infinity, streamCamera = null, entered = false;
  const ghostAt = id => {
    const circuit = circuitById.get(id), ghost = ghosts.get(id);
    return ghost ? circuit.route.at(ghost.distance) : null;
  };
  // Kevin, 2026-11-13: where two of the scene's teams can meet, one gives way to the other
  // (transport-crossings.js). Read from the routes alone, once, when the first team loads.
  let crossings = null;
  const crossingsFor = () => (crossings ??= circuits.length > 1 && circuits.every(c => Array.isArray(c.row.envelope_local_xz_m))
    ? createCrossings(circuits) : { gateFor: () => null, snapshot: () => ({}), zones: [] });
  // T-3557: while a team is driven (or steered home) it is an obstruction to the others, and
  // they to it. A route team pulled up only for a driven team goes on by itself once it can.
  const heldByTeam = new Set(), heldByHorse = new Set();
  const teamsClear = (row, self, from, to) => {
    const mine = envelopeOf(row);
    if (!mine) return true;
    const driven = !!self && self.mode !== 'route';
    let at = null, was = null;
    for (const other of actors) {
      if (other === self || other.id === row.id || other.disposed || (!driven && other.mode === 'route')) continue;
      const theirs = envelopeOf(rowById.get(other.id)), pose = other.pose;
      if (!theirs || !pose) continue;
      const print = footprintOfPose(pose, theirs, TEAM_MARGIN_M / 2);
      at ??= footprintOfPose(to, mine, TEAM_MARGIN_M / 2);
      if (!overlaps(at, print)) continue;
      // Already touching (the reins were taken there): it may only draw apart.
      was ??= footprintOfPose(from, mine, TEAM_MARGIN_M / 2);
      if (!overlaps(was, print) || Math.hypot(to.e - pose.e, to.n - pose.n) <= Math.hypot(from.e - pose.e, from.n - pose.n)) return false;
    }
    return true;
  };
  // Kevin, 2026-11-17: "i also just saw a carriage on its route drive through a horse, they
  // should either stop and wait for the horse to move". A team pulls up OBSTACLE_M short of a
  // horse in its way and goes on by itself once it has moved (heldByHorse, as heldByTeam); one
  // already touching may only draw apart.
  const obstacleClear = (row, from, to) => {
    let list = null;
    try { list = obstacles?.() ?? null; } catch { list = null; }
    if (!list?.length) return null;
    const mine = envelopeOf(row);
    if (!mine) return null;
    let at = null, was = null;
    for (const o of list) {
      const p = o?.print;
      if (!p) continue;
      at ??= footprintOfPose(to, mine, OBSTACLE_M);
      if (!overlaps(at, p)) continue;
      was ??= footprintOfPose(from, mine, OBSTACLE_M);
      const ce = (p.w + p.e) / 2, cn = (p.s + p.n) / 2;
      if (overlaps(was, p) && Math.hypot(to.e - ce, to.n - cn) > Math.hypot(from.e - ce, from.n - cn)) continue;
      return o.word ?? 'a horse';
    }
    return null;
  };
  const liveClear = row => {
    let self = null, word = null;
    const check = (from, to) => {
      word = null;
      let admitted = false;
      if (!clear(row, from, to)) {
        let blocker = null;
        try { blocker = clearWhy?.(row) ?? null; } catch { blocker = null; }
        // T-3557: off its round, a way the scene admits (the coach house's open doorway and
        // drive) passes the walls it crosses; never a visitor, nor another team.
        try { admitted = blocker !== 'visitor' && !!self && self.mode !== 'route' && admit?.(row, from, to) === true; } catch { admitted = false; }
        if (!admitted) {
          word = blocker === 'visitor' ? 'someone in the way' : 'a wall';
          heldByTeam.delete(row.id); heldByHorse.delete(row.id); return false;
        }
      }
      if (!teamsClear(row, self, from, to)) { word = 'another team'; heldByTeam.add(row.id); heldByHorse.delete(row.id); return false; }
      heldByTeam.delete(row.id);
      const horse = obstacleClear(row, from, to);
      if (horse) { word = horse; heldByHorse.add(row.id); return false; }
      heldByHorse.delete(row.id);
      // An admitted pose's hooves are the admitting way's to read (on its drive and floor). The
      // way admits a pose where no wall refuses it too: on the drive the horses are over the walk
      // and its ramp before the coach reaches the doorway, off the road's support domain.
      if (!admitted && self && self.mode !== 'route' && routeSupport && row.horse_offset_m) {
        let onWay = false;
        try { onWay = admit?.(row, from, to) === true; } catch { onWay = false; }
        if (!onWay) { try { routeSupport(row, to); } catch { word = 'rough ground'; return false; } }
      }
      return true;
    };
    return { check, why: () => word, bind(actor) { self = actor; } };
  };
  let disposed = false, tier = detail, load = null, generation = 0, loadGeneration = -1;
  let lastUpdate = null;
  const building = new Map(); // row id -> the load generation building it
  // A ghost is not made into a team where that team would stand on a built one's footprint.
  const ghostClear = id => {
    const row = rowById.get(id), circuit = circuitById.get(id), ghost = ghosts.get(id), mine = envelopeOf(row);
    if (!ghost || !mine) return true;
    const at = footprintAt(circuit.route, row, ghost.distance, TEAM_MARGIN_M);
    for (const other of actors) {
      const theirs = envelopeOf(rowById.get(other.id)), pose = other.pose;
      if (other.disposed || !theirs || !pose) continue;
      if (overlaps(at, footprintOfPose(pose, theirs, TEAM_MARGIN_M))) return false;
    }
    return true;
  };
  /** STREAM: move the ghosts, put away built teams gone far, and choose which to build. */
  const streamStep = (dt, cameraPosition, { paused, hidden, hour }) => {
    if (!ghosts.size || !cameraPosition) return;
    streamCamera = { x: cameraPosition.x, z: cameraPosition.z };
    const live = new Set(actors.map(actor => actor.id));
    if (!paused && !hidden && dt > 0) for (const [id, ghost] of ghosts) {
      if (live.has(id) || building.has(id)) continue;
      const row = rowById.get(id);
      if (offHours(row.hours, hour)) continue;
      ghost.held = false;
      advanceGhost(ghost, { length: circuitById.get(id).route.length, speed_m_s: row.speed_m_s, stops: row.stops ?? [] }, Math.min(dt, 1));
    }
    streamClock += dt;
    if (streamClock < (stream.every_s ?? .5)) return;
    streamClock = 0;
    const range = (reach[tier] ?? 0);
    const far = (e, n) => Math.hypot(e - streamCamera.x, -n - streamCamera.z);
    // Put away a built streamed team gone well past the reach, unless someone has it.
    for (const actor of [...actors]) {
      const row = rowById.get(actor.id);
      if (!row?.streamed || actor.mode !== 'route') continue;
      if (pendingApproaches.get(row.person_id)?.rowId === row.id || actor.reason === 'approach') continue;
      if (far(actor.at[0], actor.at[1]) <= range + (stream.drop_m ?? 70)) continue;
      const snap = actor.snapshot();
      saved.set(actor.id, snap);
      Object.assign(ghosts.get(actor.id), { distance: snap.distance_m, total: snap.total_distance_m, dwell: snap.dwell_s ?? 0, held: false });
      actors.splice(actors.indexOf(actor), 1);
      const r = roots.indexOf(actor.assembly?.root);
      if (r >= 0) roots.splice(r, 1);
      actor.dispose();
      onActorsChanged([...actors]);
    }
    // The nearest ghosts in reach, up to the tier's cap of built streamed teams.
    const cap = stream.cap?.[tier] ?? 4;
    const builtStreamed = actors.filter(actor => rowById.get(actor.id)?.streamed).map(actor => actor.id);
    const candidates = [];
    for (const [id] of ghosts) {
      if (live.has(id) || failed.has(id) || offHours(rowById.get(id).hours, hour)) continue;
      const at = ghostAt(id), d = far(at.e, at.n);
      if (d <= range + (stream.load_m ?? 35)) candidates.push([d, id]);
    }
    candidates.sort((a, b) => a[0] - b[0]);
    const next = new Set(candidates.slice(0, Math.max(0, cap - builtStreamed.length)).map(([, id]) => id));
    const fresh = [...next].some(id => !wanted.has(id));
    wanted = next;
    if (fresh && entered && draws(tier)) { load = null; void out.ready(); }
  };
  const out = {
    actors, roots,
    get audioSources() { return disposed ? [] : actors.map(actor => ({ ...actor.audioState, scene: sceneId })); },
    async ready() {
      if (disposed || !draws(tier)) return;
      if (load && loadGeneration === generation) return load;
      const ownGeneration = generation; loadGeneration = ownGeneration;
      load = (async () => {
        for (const row of rows) {
          if (disposed || ownGeneration !== generation) break;
          if (row.scene !== sceneId || failed.has(row.id) || actors.some(actor => actor.id === row.id)) continue;
          if (row.on_call && !summoned.has(row.id)) continue;
          // A streamed team is built when chosen, or when someone is on the way to its man.
          if (row.streamed && !staging.has(row.id) && ((!wanted.has(row.id) && pendingApproaches.get(row.person_id)?.rowId !== row.id)
            || building.get(row.id) === ownGeneration || !ghostClear(row.id))) continue;
          if (staging.has(row.id) && building.get(row.id) === ownGeneration) continue;
          let assembly;
          building.set(row.id, ownGeneration);
          try {
            const waiting = deferred.get(row.id);
            if (waiting && !clear(row, waiting, waiting)) continue;
            const prior = saved.get(row.id), ghost = ghosts.get(row.id);
            // A streamed team is made where its ghost has got to, going on from there.
            const liveRow = ghost && !ghost.held ? { ...row, initial_distance_m: ghost.distance,
              initial_total_distance_m: ghost.total, initial_state: 'moving', initial_dwell_s: ghost.dwell,
              ...(prior ? { initial_wheel_rotation_rad: prior.wheel_rotation_rad, initial_assembly_state: prior.assembly_state } : {}) }
              : prior ? { ...row, initial_distance_m: prior.distance_m,
              initial_total_distance_m: prior.total_distance_m, initial_wheel_rotation_rad: prior.wheel_rotation_rad,
              initial_state: prior.state, initial_assembly_state: prior.assembly_state,
              initial_dwell_s: prior.dwell_s ?? 0 } : row;
            const route = routeFor(row.route);
            if (row.horse_offset_m && !routeSupport) throw Error('town transport: actual whole-circuit horse support reader required');
            let routeReading = routeReadings.get(row.id);
            if (!routeReading && prepareAssembly) {
              // Eligible near-route JS imports can overlap the complete static read.
              // This optional warmup owns no models; the real factory remains authoritative.
              try { Promise.resolve(prepareAssembly(liveRow)).catch(() => {}); } catch { /* factory reports its actual dependency error after the route passes */ }
            }
            if (!routeReading) routeReading = await preflightTransportRouteAsync({ row, route, heightAt,
              clear: (from, to) => routeClear(row, from, to), support: routeSupport ? pose => routeSupport(row, pose) : null },
              { yieldEvery: 128, cancelled: () => disposed || ownGeneration !== generation || !draws(tier) });
            if (routeReading.status === 'CANCELED_ROUTE_READING_NOT_PASS'
              || disposed || ownGeneration !== generation || !draws(tier)) break;
            routeReadings.set(row.id, routeReading);
            assembly = await makeAssembly(liveRow);
            if (disposed || ownGeneration !== generation || !draws(tier)) { assembly.dispose(); break; }
            const reading = liveClear(row);
            const actor = createTransportLoop({ ...liveRow, route, assembly, heightAt,
              clear: reading.check, why: reading.why, gate: crossingsFor().gateFor(row.id),
              road: carriageway ? pose => carriageway(row, pose) : null,
              admit: admit ? (from, to) => admit(row, from, to) : null, pathHeightAt });
            reading.bind(actor);
            actor.updateVisual = assembly.updateVisual;
            actor.assembly = assembly;
            // Consume only after this generation owns a successfully created actor.
            const approach = pendingApproaches.get(row.person_id);
            if (approach?.rowId === row.id) {
              actor.stop('approach');
              pendingApproaches.delete(row.person_id);
            }
            deferred.delete(row.id);
            actors.push(actor); roots.push(assembly.root);
            actor.routeReading = routeReading;
            onActorsChanged([...actors]);
            if (lastUpdate) out.update(...lastUpdate);
          } catch (error) {
            assembly?.dispose();
            if (disposed || ownGeneration !== generation || !draws(tier)) break;
            // A typed spawn error from the static preflight is still fatal: only
            // the post-asset live visitor check may defer an otherwise qualified row.
            if (assembly && error instanceof TransportSpawnObstructedError) deferred.set(row.id, error.pose);
            else {
              if (pendingApproaches.get(row.person_id)?.rowId === row.id) pendingApproaches.delete(row.person_id);
              deferred.delete(row.id); failed.add(row.id); problems.push(`town transport ${row.id}: ${error.message}`);
            }
          } finally { if (building.get(row.id) === ownGeneration) building.delete(row.id); }
        }
      })();
      const ownLoad = load;
      try { return await ownLoad; }
      finally {
        // Completed successes/fatal refusals remain cached. A deferred row may
        // recheck clearance, but never preflight/reacquire while it is blocked.
        if (ownGeneration === generation && load === ownLoad && deferred.size) load = null;
      }
    },
    /** Called after the welcome closes. No asset or whole-route read begins until
     * the visitor actually approaches the circuit; Light remains the existing floor. */
    ensureNear(cameraPosition, enabled = true) {
      if (disposed || !enabled || !draws(tier)) return false;
      entered = true;
      const limit = (reach[tier] ?? 0) + 8;
      // A streamed row is near when its ghost is (STREAM); update() chooses which to build.
      const ghostNear = [...ghosts.keys()].some(id => {
        const p = ghostAt(id);
        return Math.hypot(p.e - cameraPosition.x, -p.n - cameraPosition.z) <= limit + (stream.load_m ?? 35);
      });
      const near = ghostNear || circuits.filter(circuit => !circuit.row.streamed).some(circuit => Math.hypot(
        Math.max(circuit.west - cameraPosition.x, 0, cameraPosition.x - circuit.east),
        Math.max(circuit.south + cameraPosition.z, 0, -cameraPosition.z - circuit.north)) <= limit);
      if (near) void out.ready();
      return near;
    },
    update(dt, cameraPosition, { paused = false, reducedMotion = false, hidden = false, visualDt = dt,
      elapsedFrame = false, motionFrame = true, hour = null } = {}) {
      if (disposed) return;
      // A visibility replay must not prime a new/restored journey's first real frame.
      lastUpdate = [0, cameraPosition, { paused, reducedMotion, hidden, visualDt: 0, elapsedFrame, motionFrame: false, hour }];
      const distance = reach[tier] ?? 0;
      if (!disposed && draws(tier)) {
        try { streamStep(dt, cameraPosition, { paused, hidden, hour }); }
        catch (error) { problems.push(`town transport streaming: ${error.message}`); }
      }
      for (const actor of actors) {
        const at = actor.at;
        const drawn = distance > 0 && Math.hypot(at[0] - cameraPosition.x, -at[1] - cameraPosition.z) < distance;
        // T-3497: a team with `hours` (its teamster's, as human-duties.js keeps them) is put
        // up outside them: not drawn, not moving, its place on the road kept for the morning.
        // T-3553: a team a jaunt's stage has taken keeps no hours: it is where the scene needs it.
        const away = hidden || (actor.mode !== 'staged' && offHours(rowById.get(actor.id)?.hours, hour));
        if ((heldByTeam.has(actor.id) || heldByHorse.has(actor.id)) && actor.mode === 'route' && actor.state === 'stopped'
          && actor.reason === 'obstruction' && !away && !paused && actor.canResume()) actor.resume();
        actor.assembly?.setReducedMotion?.(reducedMotion);
        actor.update(dt, { enabled: !away, drawn, paused, reducedMotion, elapsedFrame, motionFrame });
        // Synthetic visibility replays cannot prime the independent driver clock.
        if (!elapsedFrame || motionFrame) actor.updateVisual?.(visualDt, { paused: paused || reducedMotion || away, viewer: cameraPosition });
      }
    },
    async setTier(next) {
      tier = next;
      if (!draws(next)) {
        generation++; routeReadings.clear(); deferred.clear(); failed.clear();
        // An on-call team is put away (its stand's parked carriage takes its place), never saved.
        for (const actor of actors) {
          if (!rowById.get(actor.id)?.on_call) {
            const snap = actor.snapshot(), ghost = ghosts.get(actor.id);
            saved.set(actor.id, snap);
            // A streamed team put away by a tier comes back exactly as it was (`held`), unless
            // it has gone on unseen in the meantime.
            if (ghost) Object.assign(ghost, { distance: snap.distance_m, total: snap.total_distance_m, dwell: snap.dwell_s ?? 0, held: true });
          }
          actor.dispose();
        }
        summoned.clear();
        actors.length = 0; roots.length = 0; onActorsChanged([]);
        const pending = load; load = null;
        if (pending) await pending;
      }
      if (draws(next) && lastUpdate && !lastUpdate[2].paused
        && out.ensureNear(lastUpdate[1], true)) await out.ready();
      if (lastUpdate) out.update(...lastUpdate);
    },
    snapshot() { return actors.map(actor => actor.snapshot()); },
    /**
     * T-3555/T-3558: every team of the scene that is out on the road and not drawn near the
     * visitor, where it is: the streamed teams' ghosts, built teams beyond reach, and the rest
     * of the circuits at their kept or first places. For a far, cheap stand-in of the town's
     * traffic; nothing is loaded or read but the routes. `heading_deg` is clockwise from north.
     */
    distant(cameraPosition = null) {
      if (disposed) return [];
      const near = reach[tier] ?? 0, built = new Map(actors.map(actor => [actor.id, actor]));
      const hour = lastUpdate?.[2]?.hour ?? null, list = [];
      const heading = yaw => ((Math.atan2(Math.sin(yaw), -Math.cos(yaw)) * 180 / Math.PI) + 360) % 360;
      for (const { row, route } of circuits) {
        if (row.on_call || offHours(row.hours, hour)) continue;
        const kind = /brougham|carriage|coach/i.test(`${row.vehicle_file ?? ''} ${row.name ?? ''}`) ? 'carriage' : 'wagon';
        const actor = built.get(row.id);
        if (actor) {
          if (actor.disposed) continue;
          const at = actor.at;
          if (cameraPosition && near > 0 && Math.hypot(at[0] - cameraPosition.x, -at[1] - cameraPosition.z) < near) continue;
          list.push({ id: row.id, kind, e: at[0], n: at[1], heading_deg: heading(actor.snapshot().yaw_rad), moving: actor.state === 'moving' });
          continue;
        }
        const ghost = ghosts.get(row.id);
        const d = ghost?.distance ?? saved.get(row.id)?.distance_m ?? row.initial_distance_m ?? 0;
        const p = route.at(((d % route.length) + route.length) % route.length);
        list.push({ id: row.id, kind, e: p.e, n: p.n, heading_deg: heading(p.yaw), moving: !!ghost && !(ghost.dwell > 0) });
      }
      return list;
    },
    /**
     * T-3560: every team out on the road, as its footprint now and where its round takes it at
     * each of `times` seconds ahead (a team stopped or driven stays where it stands): for the
     * town's riders (riding.js) to give way to. Built teams and the streamed teams' ghosts.
     */
    footprintsAhead(times = [0], margin = 0) {
      if (disposed) return [];
      const hour = lastUpdate?.[2]?.hour ?? null, built = new Map(actors.map(actor => [actor.id, actor])), list = [];
      for (const { row, route } of circuits) {
        const envelope = envelopeOf(row);
        if (!envelope) continue;
        const actor = built.get(row.id);
        if (actor) {
          if (actor.disposed || !actor.pose || (actor.mode !== 'staged' && offHours(row.hours, hour))) continue;
          const snap = actor.snapshot();
          const pace = actor.mode === 'route' && actor.state === 'moving' && !(snap.dwell_s > 0) ? (actor.speed_m_s ?? row.speed_m_s ?? 0) : 0;
          list.push(times.map(t => (actor.mode === 'route' && pace ? footprintAt(route, row, snap.distance_m + pace * t, margin)
            : footprintOfPose(actor.pose, envelope, margin))));
          continue;
        }
        const ghost = ghosts.get(row.id);
        if (!ghost || row.on_call || offHours(row.hours, hour)) continue;
        const pace = ghost.dwell > 0 ? 0 : (row.speed_m_s ?? 0);
        list.push(times.map(t => footprintAt(route, row, ghost.distance + pace * t, margin)));
      }
      return list;
    },
    /** Where the scene's teams can meet, and who holds or waits at each (transport-crossings.js). */
    crossings() { return crossings ? { zones: crossings.zones.length, teams: crossings.snapshot() } : null; },
    pickDriverAt(ndc, camera) {
      let nearest = null;
      for (const actor of actors) {
        const hit = actor.pickDriverAt(ndc, camera);
        if (hit && (!nearest || hit.distance < nearest.distance)) nearest = hit;
      }
      return nearest;
    },
    /** T-3557: bring an on-call row's team (loaded where its row starts); resolves to its actor or null. */
    async summon(id) {
      const row = rowById.get(id);
      if (disposed || !row?.on_call || failed.has(id) || !draws(tier)) return null;
      const live = out.actorById(id);
      if (live) return live;
      summoned.add(id);
      load = null;
      await out.ready();
      return out.actorById(id);
    },
    /** T-3557: let an on-call team go (it is disposed; its parked carriage shows again). */
    putAway(id) {
      const row = rowById.get(id);
      if (!row?.on_call) return false;
      summoned.delete(id); saved.delete(id); deferred.delete(id);
      const i = actors.findIndex(actor => actor.id === id);
      if (i < 0) return false;
      const [actor] = actors.splice(i, 1);
      const r = roots.indexOf(actor.assembly?.root);
      if (r >= 0) roots.splice(r, 1);
      actor.dispose();
      onActorsChanged([...actors]);
      return true;
    },
    isOnCall(id) { return !!rowById.get(id)?.on_call; },
    /** T-3814: build a streamed row for a jaunt's stage now, wherever the visitor is and at any hour
     *  (a fire-night stop's wagon). Resolves to its actor or null. `release` lets it stream again. */
    async stageWant(id) {
      const row = rowById.get(id);
      if (disposed || !row || row.on_call || failed.has(id) || !draws(tier)) return null;
      const live = out.actorById(id);
      if (live) return live;
      if (!staging.has(id)) { staging.add(id); load = null; }
      await out.ready();
      return out.actorById(id);
    },
    stageRelease(id) { staging.delete(id); },
    /** T-3557: a scene's loaded team by its row id (the seat, the reins), or null. */
    actorById(id) { return disposed ? null : actors.find(actor => actor.id === id && !actor.disposed) ?? null; },
    driverForPerson(personId) { return actors.find(actor => actor.personId === personId) ?? null; },
    /** A Find/Go to target is available before the nearby model loads. This is a
     * route/seat reading, not a claim that a model has passed its ground reading. */
    driverAnchorForPerson(personId) {
      if (disposed || !['full', 'balanced'].includes(tier) || !personId) return null;
      const actor = out.driverForPerson(personId);
      if (actor && !actor.disposed) return { at: actor.at, yaw_rad: actor.snapshot().yaw_rad, actor };
      // An on-call team not brought round is not where its driver is (he stands at his post).
      const circuit = circuits.find(item => item.row.person_id === personId && (!item.row.on_call || summoned.has(item.id)));
      const row = circuit?.row;
      if (!row?.driver_asset || row.driver_instance?.person_id !== personId
        || row.driver_instance?.interaction?.selectable !== true
        || !Number.isFinite(row.root_ahead_of_rear_axle_m)
        || !Array.isArray(row.driver_local_m) || row.driver_local_m.length !== 3
        || !row.driver_local_m.every(Number.isFinite)) return null;
      const distance = ghosts.get(row.id)?.distance ?? saved.get(row.id)?.distance_m ?? row.initial_distance_m ?? 0;
      if (!Number.isFinite(distance)) return null;
      const rear = circuit.route.at(distance), yaw = rear.yaw;
      // The same two localToEnu translations as createTransportLoop.poseAt:
      // rear axle -> vehicle root -> the physical driver-seat point.
      const e = rear.e + Math.cos(yaw) * 0 + Math.sin(yaw) * row.root_ahead_of_rear_axle_m;
      const n = rear.n + Math.sin(yaw) * 0 - Math.cos(yaw) * row.root_ahead_of_rear_axle_m;
      return { at: [e + Math.cos(yaw) * row.driver_local_m[0] + Math.sin(yaw) * row.driver_local_m[2],
        n + Math.sin(yaw) * row.driver_local_m[0] - Math.cos(yaw) * row.driver_local_m[2]],
      yaw_rad: yaw, actor: null };
    },
    /** Keep a named Find request through lazy loading; cancellation never resumes
     * a driver already stopped by this or the shared Interact engine. */
    requestDriverApproach(personId) {
      const anchor = out.driverAnchorForPerson(personId);
      if (!anchor) return null;
      const circuit = circuits.find(item => item.row.person_id === personId
        && (!anchor.actor || item.id === anchor.actor.id));
      if (!circuit || failed.has(circuit.id)) return null;
      // Reject invalid/failed targets before replacing an earlier rendezvous.
      // A live stop must succeed before older unresolved intent is cleared.
      if (anchor.actor && !anchor.actor.stop('approach')) return null;
      pendingApproaches.clear();
      const request = { rowId: circuit.id };
      pendingApproaches.set(personId, request);
      const cancel = () => {
        if (pendingApproaches.get(personId) === request) pendingApproaches.delete(personId);
      };
      if (anchor.actor) cancel();
      return { cancel };
    },
    cancelDriverApproaches() { pendingApproaches.clear(); },
    stopPerson(personId) { return out.driverForPerson(personId)?.stop('approach') ?? false; },
    dispose() {
      if (disposed) return;
      disposed = true; generation++; pendingApproaches.clear(); routeReadings.clear(); deferred.clear(); failed.clear();
      for (const actor of actors) actor.dispose();
      actors.length = 0; roots.length = 0; lastUpdate = null;
    },
  };
  return out;
}
