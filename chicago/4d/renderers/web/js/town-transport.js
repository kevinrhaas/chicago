// SPDX-License-Identifier: GPL-3.0-or-later
import { routeFor, createTransportLoop, preflightTransportRouteAsync, TransportSpawnObstructedError } from './transport-loop.js';

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
  return { harness: point(horse.root), wagon: point(vehicle) };
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
  disposeVehicle, hitch = null, patchMaterial = () => {} }) {
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
  root.traverse(node => {
    if (!node.isMesh || node.material?.visible === false) return;
    node.castShadow = true; node.receiveShadow = true;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      confidence?.patch?.(material); patchMaterial(material);
    }
  });
  const wheelRest = wheels.map(node => node.rotation.x), steerRest = steer.rotation.y;
  const horseRestYaw = horse.root.rotation.y;
  let priorHorse = null, stopped = true, disposed = false, visualReset = true;
  let lastPose = null, posed = false;
  return {
    root,
    audioAnchors: () => disposed ? null : audioAnchors(root, vehicle, horse),
    pose(pose) {
      if (disposed) return;
      lastPose = pose; posed = true;
      root.position.set(pose.e, pose.height, -pose.n); root.rotation.y = pose.yaw;
      steer.rotation.y = steerRest + pose.steering;
      if (!horse.poseVehicle) {
        const rearAhead = horseOffset_m[2] + pose.rootAhead;
        horse.root.rotation.y = horseRestYaw + Math.atan2(pose.curvature * rearAhead, 1 - pose.curvature * horseOffset_m[0]);
      }
      wheels.forEach((node, i) => { node.rotation.x = wheelRest[i] + pose.wheelRotation[i]; });
      root.updateMatrixWorld(true);
      if (horse.poseVehicle) {
        horse.poseVehicle(pose); root.updateMatrixWorld(true);
        const connection = hitch?.update(pose);
        if (connection?.valid === false) throw Error('town transport: actual hitch exceeds its declared connection bound');
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
      // T-1790: the driver's motion layer reads the ride (travelled metres, the
      // turn) and whether the team is moving; a stopped carriage is still a ride.
      if (lastPose) driver.move?.(lastPose, posed && !stopped);
      driver.updateVisual(held || visualReset ? 0 : dt, held ? null : viewer);
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

/** One instance per scene. The static parked layer remains independently owned. */
export function createTownTransport({ rows, sceneId, makeAssembly, prepareAssembly = null, heightAt,
  clear, routeClear = clear, routeSupport = null, detail = 'full',
  reach = { full: 90, balanced: 60, light: 45 }, problems = [], onActorsChanged = () => {} }) {
  // T-3542: a tier draws the teams when its reach is above zero; since the owner's ruling
  // (2026-11-10) Light's is, so a phone keeps its horses, carriages and wagons, nearer.
  const draws = t => (reach[t] ?? 0) > 0;
  if (!Array.isArray(rows) || typeof makeAssembly !== 'function' || typeof clear !== 'function') throw Error('town transport: scene rows, assembly loader and clearance reader required');
  if (prepareAssembly !== null && typeof prepareAssembly !== 'function') throw Error('town transport: optional assembly preparation callback required');
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
  let disposed = false, tier = detail, load = null, generation = 0, loadGeneration = -1;
  let lastUpdate = null;
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
          let assembly;
          try {
            const waiting = deferred.get(row.id);
            if (waiting && !clear(row, waiting, waiting)) continue;
            const prior = saved.get(row.id);
            const liveRow = prior ? { ...row, initial_distance_m: prior.distance_m,
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
            const actor = createTransportLoop({ ...liveRow, route, assembly, heightAt,
              clear: (from, to) => clear(row, from, to) });
            actor.updateVisual = assembly.updateVisual;
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
          }
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
      const limit = (reach[tier] ?? 0) + 8;
      const near = circuits.some(circuit => Math.hypot(
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
      for (const actor of actors) {
        const at = actor.at;
        const drawn = distance > 0 && Math.hypot(at[0] - cameraPosition.x, -at[1] - cameraPosition.z) < distance;
        // T-3497: a team with `hours` (its teamster's, as human-duties.js keeps them) is put
        // up outside them: not drawn, not moving, its place on the road kept for the morning.
        const away = hidden || offHours(rowById.get(actor.id)?.hours, hour);
        actor.update(dt, { enabled: !away, drawn, paused, reducedMotion, elapsedFrame, motionFrame });
        // Synthetic visibility replays cannot prime the independent driver clock.
        if (!elapsedFrame || motionFrame) actor.updateVisual?.(visualDt, { paused: paused || reducedMotion || away, viewer: cameraPosition });
      }
    },
    async setTier(next) {
      tier = next;
      if (!draws(next)) {
        generation++; routeReadings.clear(); deferred.clear(); failed.clear();
        for (const actor of actors) { saved.set(actor.id, actor.snapshot()); actor.dispose(); }
        actors.length = 0; roots.length = 0; onActorsChanged([]);
        const pending = load; load = null;
        if (pending) await pending;
      }
      if (draws(next) && lastUpdate && !lastUpdate[2].paused
        && out.ensureNear(lastUpdate[1], true)) await out.ready();
      if (lastUpdate) out.update(...lastUpdate);
    },
    snapshot() { return actors.map(actor => actor.snapshot()); },
    pickDriverAt(ndc, camera) {
      let nearest = null;
      for (const actor of actors) {
        const hit = actor.pickDriverAt(ndc, camera);
        if (hit && (!nearest || hit.distance < nearest.distance)) nearest = hit;
      }
      return nearest;
    },
    driverForPerson(personId) { return actors.find(actor => actor.personId === personId) ?? null; },
    /** A Find/Go to target is available before the nearby model loads. This is a
     * route/seat reading, not a claim that a model has passed its ground reading. */
    driverAnchorForPerson(personId) {
      if (disposed || !['full', 'balanced'].includes(tier) || !personId) return null;
      const actor = out.driverForPerson(personId);
      if (actor && !actor.disposed) return { at: actor.at, yaw_rad: actor.snapshot().yaw_rad, actor };
      const circuit = circuits.find(item => item.row.person_id === personId);
      const row = circuit?.row;
      if (!row?.driver_asset || row.driver_instance?.person_id !== personId
        || row.driver_instance?.interaction?.selectable !== true
        || !Number.isFinite(row.root_ahead_of_rear_axle_m)
        || !Array.isArray(row.driver_local_m) || row.driver_local_m.length !== 3
        || !row.driver_local_m.every(Number.isFinite)) return null;
      const distance = saved.get(row.id)?.distance_m ?? row.initial_distance_m ?? 0;
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
