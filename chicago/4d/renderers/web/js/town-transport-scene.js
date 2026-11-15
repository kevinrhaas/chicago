// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import { createTownTransport } from './town-transport.js';
import { supportsTownTransport, routeFor, routeDistanceNear } from './transport-loop.js';
import { createTransportClearance, giveRoomStand } from './transport-clearance.js';
import { teamSupportAt, certifiedHorseSupportDomain } from './transport-support.js';
import { registerTransportInteractions, createTeamRide, boardStand, riderOffTeam } from './transport-interactions.js';
import { createCarriagewayReader } from './team-drive.js';

/** T-3557: the scenes whose carriageways are drawn curb to curb (street-grid.js reads the same
 *  file), so a driven team there is kept off the kerb by the rule the laid 1904 roads were
 *  walked with (tools/lay_driven_carriages_1904.mjs). 1812 and 1835 have none: their teams
 *  keep the ground and horse-support rules alone. */
const CARRIAGEWAY_FILES = Object.freeze({ 1904: 'street_grid/1904.json' });

/**
 * T-3557: where a team leaves its round for a way in (a coach house's drive): the first point
 * of the way its round runs beside, straight and the same way (not in a corner), within a
 * lane's width; the way from there. Null where the round runs beside it nowhere.
 */
export function wayJoin(row, way) {
  const road = routeFor(row.route), pts = way.points_enu_m;
  for (let i = 0; i < pts.length - 1 && i < (way.kerb_index ?? pts.length); i++) {
    const near = routeDistanceNear(road, pts[i][0], pts[i][1], .5), r = road.at(near.distance_m);
    const turn = Math.abs(Math.atan2(Math.sin(r.yaw - way.yaw_rad[i]), Math.cos(r.yaw - way.yaw_rad[i])));
    if (near.off_m <= 1.5 && turn < 1.5 * Math.PI / 180 && Math.abs(r.curvature) < 1e-6) {
      return { ...way, points_enu_m: pts.slice(i), yaw_rad: way.yaw_rad.slice(i), curvature_per_m: way.curvature_per_m.slice(i), joined_at: i };
    }
  }
  return null;
}

const wrapAngle = a => Math.atan2(Math.sin(a), Math.cos(a));

/**
 * T-3557: out of a coach house, the team backs only until all of it (its measured envelope,
 * the horses' heads to the coach's back) stands `clear_m` past the drive's kerb line, out in
 * the street. A predicate on the rear-axle sample {e, n, yaw} for backOut({ until }).
 * The kerb line runs through the way's kerb point along the round's lane there.
 */
export function clearOfKerb(row, way, { clear_m = 3 } = {}) {
  const pts = way.points_enu_m, at = (way.kerb_index ?? -1) - (way.joined_at ?? 0);
  if (!(at > 0 && at < pts.length)) return null;
  const road = routeFor(row.route), K = pts[at];
  const L = road.at(routeDistanceNear(road, K[0], K[1], .5).distance_m);
  const nE = Math.cos(L.yaw), nN = Math.sin(L.yaw);
  const side = Math.sign((pts[0][0] - K[0]) * nE + (pts[0][1] - K[1]) * nN) || 1;
  const [x0, z0, x1, z1] = row.envelope_measured_local_xz_m ?? row.envelope_local_xz_m;
  const ahead = row.root_ahead_of_rear_axle_m ?? 0;
  /** How far the nearest corner of the team stands past the kerb, street side positive. */
  const past = rear => {
    const c = Math.cos(rear.yaw), sn = Math.sin(rear.yaw);
    const e0 = rear.e + sn * ahead, n0 = rear.n - c * ahead;
    let least = Infinity;
    for (const x of [x0, x1]) for (const z of [z0, z1]) {
      const e = e0 + c * x + sn * z, n = n0 + sn * x - c * z;
      least = Math.min(least, side * ((e - K[0]) * nE + (n - K[1]) * nN));
    }
    return least;
  };
  const until = rear => past(rear) >= clear_m;
  until.past = past;
  return until;
}

/**
 * T-3557: from where the team stood after backing out (the rear-axle sample {e, n, yaw},
 * across the street from the coach house, facing on along it), the coachman drives forward
 * into the round's lane: a turn on `r1_m` until it heads within a few degrees of the lane, a
 * shallow straight down to it, an easing turn on `r2_m` into it, and `lane_m` along it, where
 * the round takes it on. Null where the round runs no straight lane ahead to take, or the team
 * does not stand to the lane's left heading on along it.
 */
export function exitWay(row, rear, { r1_m = 10, r2_m = 20, lane_m = 4, step_m = .25 } = {}) {
  const road = routeFor(row.route);
  const s0 = routeDistanceNear(road, rear.e, rear.n, .5).distance_m;
  const L = road.at(s0);
  const h = (rear.e - L.e) * Math.cos(L.yaw) + (rear.n - L.n) * Math.sin(L.yaw);
  const phi0 = wrapAngle(L.yaw - rear.yaw);
  const rMin = row.wheelbase_m / Math.tan((row.steering_limit_deg ?? 15) * Math.PI / 180);
  const r1 = Math.max(r1_m, rMin * 1.05), r2 = Math.max(r2_m, rMin * 1.05);
  if (!(h > 0) || !(phi0 > 0) || phi0 > Math.PI * 2 / 3) return null;
  const DEG = Math.PI / 180;
  for (const phi1 of [6, 8, 10, 15, 20, 30].map(d => d * DEG)) {
    if (phi1 >= phi0) break;
    const after = h - r1 * (Math.cos(phi1) - Math.cos(phi0));
    const d = (after - r2 * (1 - Math.cos(phi1))) / Math.sin(phi1);
    if (d < 0) continue;
    const legs = [[r1 * (phi0 - phi1), 1 / r1], [d, 0], [r2 * phi1, 1 / r2], [lane_m, 0]];
    const length = legs.reduce((sum, [len]) => sum + len, 0);
    // The lane it is to take: straight on along the round all the way.
    let straight = true;
    for (let s = s0; s <= s0 + length + 2; s += 1) if (Math.abs(road.at(s % road.length).curvature) > 1e-6) { straight = false; break; }
    if (!straight) continue;
    const points = [[rear.e, rear.n]], yaw = [rear.yaw], curvature = [legs[0][1]];
    let e = rear.e, n = rear.n, y = rear.yaw;
    for (const [len, k] of legs) {
      for (let done = 0; done < len - 1e-9;) {
        const ds = Math.min(step_m, len - done), mid = y + k * ds / 2;
        e += Math.sin(mid) * ds; n -= Math.cos(mid) * ds; y += k * ds; done += ds;
        points.push([e, n]); yaw.push(y); curvature.push(k);
      }
    }
    return { points_enu_m: points, yaw_rad: yaw, curvature_per_m: curvature, length_m: length,
      turn_deg: phi0 / DEG, glide_deg: phi1 / DEG, glide_m: d, lane_off_m: h };
  }
  return null;
}

/** Small scene binding; the first occupied GLB and whole-route reading stay lazy. */
export async function mountTownTransport({ sceneId, dataBase, people, getPeople = null, preparePersonCard = null, humans, confidence,
  heightAt, footprints, visitor, interactions, detail, coarse = false, problems = [],
  blockedAt = () => false, placeVisitor = null, configFile = 'transport/driven/loops.json',
  visitorEye = null, groundAt = () => NaN, walkEye = () => 1.6, onBoard = () => {}, reducedMotion = () => false,
  reinsHint = undefined, carriagewayFile = CARRIAGEWAY_FILES[String(sceneId)] ?? null,
  parked = null, coachHouse = () => null, pathHeightAt = null }) {
  if (!supportsTownTransport(sceneId)) return null;
  sceneId = String(sceneId);
  const json = async (file, expectedSHA256 = null) => {
    const response = await fetch(new URL(file, dataBase));
    if (!response.ok) throw Error(`town transport ${file}: HTTP${response.status}`);
    if (!expectedSHA256) return response.json();
    const bytes = await response.arrayBuffer();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
      .map(n => n.toString(16).padStart(2, '0')).join('');
    if (hash !== expectedSHA256) throw Error('town transport: support certificate bytes differ');
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  const config = await json(configFile);
  const supportByHorse = new Map();
  for (const [model, spec] of Object.entries(config.horse_models)) {
    if (spec.support_domain) {
      const cert = await json(spec.support_domain.certificate_file, spec.support_domain.certificate_sha256);
      supportByHorse.set(model, certifiedHorseSupportDomain(spec, cert));
    }
  }
  const modelFor = row => coarse && row.horse_model_light ? row.horse_model_light : row.horse_model;
  // The carriageways are read lazily (the grid file is ~400 KB): the first time a team is
  // driven, never at boot. Until they arrive (or if they cannot be read) the answer is null,
  // and the team keeps today's ground and support rules.
  let roadReader = null, roadLoad = null;
  const carriageway = carriagewayFile ? (row, pose) => {
    if (roadReader) return roadReader(row, pose);
    roadLoad ??= json(carriagewayFile)
      .then(grid => { roadReader = createCarriagewayReader(grid?.carriageways); })
      .catch(error => { problems.push(`town transport carriageways ${carriagewayFile}: ${error.message}`); });
    return null;
  } : null;
  const rows = config.rows.filter(row => row.scene === sceneId);
  const group = new THREE.Group(); group.name = 'town-transport';
  const moduleBase = new URL('../', import.meta.url);
  // Light/remote boot needs route metadata, never assembly modules or loaders.
  // Start these only for an ordinary eligible assembly, alongside its directory.
  let assemblyModules = null, assemblyTools = null;
  const prepareAssemblyModules = () => (assemblyModules ??= Promise.all([
    import('./driven-assembly-loader.js'), import('./draft-hitch.js'),
    import('three/addons/loaders/GLTFLoader.js'), import('./horse-appearance.js'),
  ]).catch(error => { assemblyModules = null; throw error; }));
  const getAssemblyTools = () => (assemblyTools ??= prepareAssemblyModules()
    .then(async ([{ createDrivenAssemblyLoader }, { createDraftHitchFactory }, { GLTFLoader }, { loadHorseRecipe }]) => {
    const loader = new GLTFLoader();
    return { createDrivenAssemblyLoader, coatRecipe: config.horse_appearance
      ? await loadHorseRecipe(dataBase, config.horse_appearance.recipe_file) : null, makeHitch: createDraftHitchFactory({ confidence, loadJSON: json,
      loadGLTF: file => loader.loadAsync(new URL(file, moduleBase).href) }) };
  }).catch(error => { assemblyTools = null; throw error; }));
  const makeByHorse = new Map(), live = new Map(), fixed = new Map();
  /** T-3475: Step back. The road the stopped team will drive next (GIVE_ROOM_AHEAD_M of it,
   *  from where it stands), and the nearest stand beside it the visitor can walk to. */
  const GIVE_ROOM_AHEAD_M = 30;
  const giveRoomFor = row => ({
    plan(actor) {
      const person = visitor();
      if (!person || person.flying) return null;
      const from = actor.snapshot().distance_m, poses = [];
      try {
        for (let s = 0; s <= GIVE_ROOM_AHEAD_M; s += .25) poses.push(actor.previewAt(from + s));
      } catch { return null; }
      // Stepping aside helps only when the visitor is what holds it: the road itself is clear.
      const road = clearance(fixed, row, false);
      if (!road(poses[0], poses[1])) return null;
      const to = giveRoomStand({ poses, envelope_local_xz_m: row.envelope_local_xz_m,
        at: { e: person.e, n: person.n }, blockedAt });
      return to ? { from: { e: person.e, n: person.n }, to } : null;
    },
    place: (e, n) => placeVisitor(e, n),
  });
  let registration = null, town;

  // ---- T-3557: the Glessner brougham, on call at its stand.
  // While the visitor rides, the parked carriage there (parked-transport.js `stand_in_for`) is
  // this driven row: the parked one, its stationary team and its standing coachman are hidden
  // while the driven one is loaded, and shown again once it is put away at the stand.
  const onCall = rows.filter(row => row.on_call);
  const IDLE_PUT_AWAY_S = 20;
  const idle = new Map();
  /** Home to the coach house and out again, the coachman's (one way at a time per row). */
  const trips = new Map();
  const tripOf = row => trips.get(row.id) ?? null;
  function homeFor(row) {
    const from = row.coach_house?.from ?? 'west';
    const wayOf = () => { const ch = house(); return typeof ch?.drivePath === 'function' ? ch.drivePath({ from, row }) : null; };
    return {
      isHome: a => a?.way?.mode === 'parked' && tripOf(row)?.phase === 'home',
      canGoHome: a => !!wayOf() && a?.mode === 'route' && !tripOf(row),
      whyNotHome(a) {
        if (ride.reducedMotion()) return 'Reduced motion: the team stands';
        if (!wayOf()) return 'The coach house is shut up';
        if (a?.mode !== 'route' || tripOf(row)) return `The coachman is busy`;
        return null;
      },
      whyNotOut(a) {
        if (ride.reducedMotion()) return 'Reduced motion: the team stands';
        return a?.way?.mode === 'parked' && tripOf(row)?.phase === 'home' ? null : 'It is not in';
      },
      goHome(a) {
        const full = wayOf();
        if (!full || !a) return false;
        const way = joinOf(row, full);
        if (!way) { problems.push(`town transport ${row.id}: its round runs beside the coach-house way nowhere`); return false; }
        const [e, n] = way.points_enu_m[0];
        if (!a.branchAt(e, n, { within_m: 2 })) { problems.push(`town transport ${row.id}: its round passes nowhere near the coach-house way`); return false; }
        if (a.state === 'stopped' && a.canResume()) a.resume();
        trips.set(row.id, { phase: 'to-branch', way, t: 0 });
        return true;
      },
      bringOut(a) {
        const trip = tripOf(row);
        if (!a || trip?.phase !== 'home') return false;
        trip.phase = 'opening-out'; trip.t = 0;
        void house()?.open?.();
        return true;
      },
      /** In the coach house it is worked from its doors' side of the room. */
      spot: a => (a?.way ? a.at : null),
    };
  }
  const joins = new Map();
  const joinOf = (row, way) => {
    const key = `${row.id}|${way.from}|${way.length_m}`;
    if (!joins.has(key)) joins.set(key, wayJoin(row, way));
    return joins.get(key);
  };
  /** Each frame: the coachman's trip on, one step at a time. */
  function stepTrips(dt) {
    for (const row of onCall) {
      const trip = tripOf(row), a = town.actorById(row.id);
      if (!trip) continue;
      if (!a) { trips.delete(row.id); continue; }
      trip.t += dt;
      const ch = house();
      switch (trip.phase) {
        case 'to-branch':
          if (a.branched) { trip.phase = 'opening'; trip.t = 0; void ch?.open?.(); }
          // Taken off its round meanwhile (the reins): the trip is off.
          else if (a.mode !== 'route') { a.cancelBranch(); trips.delete(row.id); }
          break;
        case 'opening':
          if (ch?.state === 'open') {
            const ok = a.followPath(trip.way.points_enu_m, { speed_m_s: .8, yaw_rad: trip.way.yaw_rad, curvature_per_m: trip.way.curvature_per_m,
              onArrive: () => { trip.phase = 'closing'; trip.t = 0; } });
            if (ok) trip.phase = 'in'; else trips.delete(row.id);
          } else if (trip.t > 15) { trips.delete(row.id); if (a.canResume()) a.resume(); }
          break;
        case 'in':
          if (a.mode !== 'path' && a.mode !== 'parked') trips.delete(row.id); // the reins were taken
          break;
        case 'closing':
          // The leaves shut once nothing stands in their swing; asked again until they do.
          if (ch && ch.state === 'open' && trip.t >= 0) { trip.t = -2; void ch.close().then(r => { if (!r?.ok) trip.t = 0; }); }
          if (!ch || ch.state === 'shut') trip.phase = 'home';
          break;
        case 'opening-out':
          if (ch?.state === 'open') {
            // Backed only until the whole team stands clear past the kerb, out in the street.
            const until = clearOfKerb(row, trip.way);
            if (a.backOut({ until, onArrive: () => { trip.phase = 'forward-out'; trip.t = 0; } })) trip.phase = 'out';
            else trips.delete(row.id);
          } else if (trip.t > 15) trip.phase = 'home';
          break;
        case 'out':
          if (a.mode !== 'backing' && a.mode !== 'parked') trips.delete(row.id); // the reins were taken
          break;
        case 'forward-out': {
          // Then forward into the round's lane, the leaves shut behind; where no forward way
          // fits, it backs on the rest of the way it came in.
          if (!trip.exit) {
            const p = a.pose, ahead = row.root_ahead_of_rear_axle_m ?? 0;
            const rear = p ? { e: p.e - Math.sin(p.yaw) * ahead, n: p.n + Math.cos(p.yaw) * ahead, yaw: p.yaw } : null;
            const way = rear ? exitWay(row, rear) : null;
            const done = () => { trip.exited = true; };
            trip.exit = way && a.followPath(way.points_enu_m, { speed_m_s: .9, yaw_rad: way.yaw_rad, curvature_per_m: way.curvature_per_m, onArrive: done })
              ? 'forward' : a.backOut({ onArrive: done }) ? 'back' : 'none';
            if (trip.exit === 'none') { trips.delete(row.id); break; }
          }
          if (ch && ch.state === 'open' && trip.t >= 0) { trip.t = -2; void ch.close().then(r => { if (!r?.ok) trip.t = 0; }); }
          if (trip.exited) { trip.phase = 'closing-out'; trip.t = 0; }
          else if (a.mode !== 'path' && a.mode !== 'backing' && a.mode !== 'parked') trips.delete(row.id);
          break;
        }
        case 'closing-out':
          // Back in its lane: the coachman drives on round to the stand; the leaves are shut behind.
          if (a.way) a.handBack();
          if (ch && ch.state === 'open' && trip.t >= 0) { trip.t = -2; void ch.close().then(r => { if (!r?.ok) trip.t = 0; }); }
          if (!ch || ch.state === 'shut' || ch.state === 'closing') trips.delete(row.id);
          break;
        default: break;
      }
    }
  }
  /** The leaves never shut on the team (coach-house.js setBlocker). */
  const insidePoly = (e, n, poly) => {
    let yes = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [ae, an] = poly[i], [be, bn] = poly[j];
      if ((an > n) !== (bn > n) && e < (be - ae) * (n - an) / (bn - an) + ae) yes = !yes;
    }
    return yes;
  };
  const teamIn = (row, pose, poly) => {
    const [x0, z0, x1, z1] = row.envelope_measured_local_xz_m ?? row.envelope_local_xz_m;
    const c = Math.cos(pose.yaw), sn = Math.sin(pose.yaw);
    const at = (x, z) => [pose.e + c * x + sn * z, pose.n + sn * x - c * z];
    for (let x = x0; x <= x1 + 1e-9; x += .25) for (let z = z0; z <= z1 + 1e-9; z += .25) {
      const [e, n] = at(x, z);
      if (insidePoly(e, n, poly)) return true;
    }
    return false;
  };
  let blockerBound = null;
  function bindBlocker() {
    const ch = house();
    if (!ch || blockerBound === ch || typeof ch.setBlocker !== 'function' || !onCall.some(r => r.coach_house)) return;
    blockerBound = ch;
    ch.setBlocker(poly => {
      for (const row of onCall) {
        const a = town.actorById(row.id), pose = a?.pose;
        if (pose && teamIn(row, pose, poly)) return `the ${row.ride_name ?? 'carriage'}`;
      }
      return null;
    });
  }
  /** The parked twin's place, door and coachman, as world ENU points. */
  const parkedSpots = row => {
    const st = parked?.standOf?.(row.stand_in_for);
    if (!st) return null;
    const yaw = Math.PI - st.bearing_deg * Math.PI / 180, [pe, pn] = st.at_local_enu_m;
    const local = (x, z) => [pe + Math.cos(yaw) * x + Math.sin(yaw) * z, pn + Math.sin(yaw) * x - Math.cos(yaw) * z];
    const door = row.cab_stand_local_xz_m ? local(...row.cab_stand_local_xz_m) : local(-1.4, 0);
    return { door, box: local(-1.4, row.driver_local_m?.[2] ?? .76), team: local(0, row.horse_offset_m?.[2] ?? 3.08), loaded: st.loaded };
  };
  // "Ask the coachman for a ride": Interact at the parked carriage or beside its coachman.
  const callThings = [];
  function registerCalls() {
    if (!interactions?.add) return;
    for (const row of onCall) {
      if (!row.stand_in_for || !parked?.standOf) continue;
      const driverId = `driver:${row.id}`;
      let summoning = null;
      const actor = () => town.actorById(row.id);
      const ready = () => { const a = actor(); return !!a && a.visible && !!interactions.get?.(driverId); };
      const chain = actionId => ({ label: 'Off', seconds: 0, run(t) {
        if (t !== 0 || !ready()) return;
        const res = interactions.act(driverId, actionId);
        if (!res.ok && res.why) problems.push(`town transport ${row.id}: ${res.why}`);
      } });
      const call = (id, label, actionId) => ({ id, label,
        refuse: () => (ride.actor ? 'Already aboard' : !parkedSpots(row)?.loaded ? 'The carriage is not here' : null),
        steps: [
          { label: 'Calling the coachman', timeout: 20,
            run(t) {
              if (t !== 0) return;
              spawning.add(row.id);
              summoning = town.summon(row.id).catch(error => { problems.push(`town transport ${row.id}: ${error.message}`); return null; })
                .finally(() => spawning.delete(row.id));
            },
            until: () => ready() },
          chain(actionId),
        ],
        said: () => (ready() ? '' : 'The coachman cannot bring it round just now') });
      const thing = {
        id: `call:${row.id}`, name: row.ride_name ?? row.name, kind: 'vehicle', reach: 6,
        states: ['waiting'], state: 'waiting',
        // Only while the parked carriage stands for it.
        get at() {
          if (actor() || ride.actor || parked.isStoodIn?.(row.stand_in_for)) return null;
          const spots = parkedSpots(row);
          return spots?.loaded ? spots.door : null;
        },
        get spots() { const p = parkedSpots(row); return p ? [p.box, p.team] : []; },
        actions: { waiting: [
          ...(row.cab_seat_local_m ? [call('ask-ride', 'Ask the coachman for a ride', 'get-in')] : []),
          call('ask-box', 'Climb up beside the coachman', 'climb-up'),
        ] },
      };
      interactions.add(thing);
      callThings.push(thing);
      void summoning;
    }
  }
  /** After each frame: the handover, the trips, and the put-away. */
  function afterUpdate(dt, cameraPosition) {
    bindBlocker();
    stepTrips(dt);
    for (const row of onCall) {
      if (!row.stand_in_for || !parked?.setStandIn) continue;
      const a = town.actorById(row.id);
      if (a && !parked.isStoodIn?.(row.stand_in_for)) parked.setStandIn(row.stand_in_for, false);
      if (!a) { if (parked.isStoodIn?.(row.stand_in_for)) parked.setStandIn(row.stand_in_for, true); idle.delete(row.id); continue; }
      // Got out of mid-round: the visitor lands by the cab's door, inside the team's clearance, so
      // the Down step's resume is refused; the coachman drives on round once they are clear of it
      // (else it stood in the street for good, never back at its stand to be put away).
      if (a.mode === 'route' && a.state === 'stopped' && a.reason === 'alighting' && ride.actor !== a
        && !interactions?.get?.(`driver:${row.id}`)?.running && !ride.reducedMotion() && a.canResume()) a.resume();
      // At its stand, nobody aboard, nothing running: after a while (or out of sight), put away.
      const resting = a.mode === 'route' && a.state === 'stopped' && a.reason === 'stand' && !tripOf(row)
        && ride.actor !== a && !interactions?.get?.(`driver:${row.id}`)?.running;
      const t = resting ? (idle.get(row.id) ?? 0) + dt : 0;
      idle.set(row.id, t);
      if (resting && (t >= IDLE_PUT_AWAY_S || !a.visible)) {
        idle.delete(row.id);
        if (town.putAway(row.id)) parked.setStandIn(row.stand_in_for, true);
      }
    }
    void cameraPosition;
  }
  // ---- end T-3557 on call
  /** T-3557: the visitor aboard a team (one at a time). The team they ride is not stopped by
   *  them; every other team still is. Get down finds a stand as Step back does. */
  const standFor = actor => boardStand({ actor, row: rows.find(r => r.id === actor?.id), blockedAt });
  const person = () => {
    const v = visitor();
    return v ? { e: v.e, n: v.n, y: v.eyeY ?? v.y, bearing: v.bearing } : null;
  };
  const ride = createTeamRide({ visitor: visitorEye ?? person, standFor, groundAt, walkEye, onBoard, reducedMotion });
  // T-3557: an on-call team brought round where its parked twin already stands is not refused
  // by the visitor who asked for it, beside its door (`spawning`, only while it is made).
  const spawning = new Set();
  const visitorFor = row => { const off = riderOffTeam(ride, row.id, visitor); return () => (spawning.has(row.id) ? null : off()); };
  const clearance = (cache, row, includeVisitor) => {
    if (!cache.has(row.id)) cache.set(row.id, createTransportClearance({ footprints,
      visitor: includeVisitor ? visitorFor(row) : () => null,
      envelope_local_xz_m: row.envelope_local_xz_m }));
    return cache.get(row.id);
  };
  // T-3557: the Glessner coach house (coach-house.js, api.coachHouse): its open doorway and
  // drive admit the team the road's kerb and walls refuse, never over a visitor.
  const house = () => { try { return coachHouse?.() ?? null; } catch { return null; } };
  const peopleClears = new Map();
  const peopleClear = row => {
    if (!peopleClears.has(row.id)) peopleClears.set(row.id, createTransportClearance({ footprints: () => [],
      visitor: riderOffTeam(ride, row.id, visitor), envelope_local_xz_m: row.envelope_local_xz_m }));
    return peopleClears.get(row.id);
  };
  const admit = (row, from, to) => {
    if (!row.coach_house || !from || !to) return false;
    const ch = house();
    if (typeof ch?.clearFor !== 'function' || ch.clearFor(row, from, to) !== true) return false;
    return peopleClear(row)(from, to);
  };
  town = createTownTransport({ rows, sceneId, heightAt, detail, problems, admit, pathHeightAt,
    prepareAssembly(row) {
      const modules = prepareAssemblyModules();
      // Optional scene UI preparation is metadata-only and cannot block assembly.
      try { Promise.resolve(preparePersonCard?.(row.person_id)).catch(() => {}); } catch { /* the real card route remains authoritative */ }
      return modules;
    },
    clear: (row, a, b) => clearance(live, row, true)(a, b),
    // T-3557: the word a driven team gives for what pulled it up (team-drive.js).
    clearWhy: row => clearance(live, row, true).lastBlocker,
    routeClear: (row, a, b) => clearance(fixed, row, false)(a, b),
    routeSupport: (row, pose) => teamSupportAt(row, pose, heightAt, supportByHorse.get(modelFor(row))),
    carriageway,
    async makeAssembly(row) {
      const model = modelFor(row);
      // Lazy eligible assembly only: Light/remote boot never fetches a district directory.
      const [directory, { createDrivenAssemblyLoader, makeHitch, coatRecipe }] = await Promise.all([
        Array.isArray(people?.people) ? people : getPeople?.(), getAssemblyTools(),
      ]);
      if (!Array.isArray(directory?.people)) throw Error('town transport: this scene named people directory is unavailable');
      if (!makeByHorse.has(model)) makeByHorse.set(model, createDrivenAssemblyLoader({
        sceneId, people: directory.people, profiles: config.profiles ?? [],
        humanAssets: humans.assets, confidence, heightAt, horseSpec: config.horse_models[model], horseSupportDomain: supportByHorse.get(model),
        makeHitch, coatRecipe, driverLod: coarse ? 3 : 0, rampHeightAt: pathHeightAt,
        // T-3497: a teamster on foot is the scene's own figure of him, made as the layer makes it.
        createWalker: typeof humans.createActor === 'function'
          ? (instance, identity) => humans.createActor(instance, { person: identity.person, identity }) : null,
        adoptPerson(instance, actor) {
          if (instance.person_id !== actor.personId) throw Error('town transport: driver identity mismatch');
          return humans.withhold(instance.person_id, { instanceId: instance.id, externalActor: actor });
        },
      }));
      // T-3497: phones and Light take a row's lighter level of the same vehicle, when it has one.
      return makeByHorse.get(model)(coarse && row.vehicle_file_light
        ? { ...row, vehicle_file: row.vehicle_file_light, vehicle_glb_sha256: row.vehicle_glb_sha256_light } : row);
    },
    onActorsChanged(actors) {
      registration?.dispose();
      registration = registerTransportInteractions(interactions, actors, actor => {
        const row = rows.find(r => r.id === actor.id);
        const carriage = /brougham|carriage/i.test(`${row?.vehicle_file ?? ''} ${row?.name ?? ''}`);
        const onFoot = row?.driver_mode === 'on_foot';
        return { vehicle: carriage ? 'carriage' : 'wagon',
          driver: carriage ? 'coachman' : onFoot ? 'teamster' : 'driver', onFoot, ride,
          rideName: row?.ride_name ?? null,
          // T-3557: a closed carriage's cab, and its coachman's way home and out again.
          cab: row?.cab_seat_local_m ? { via: row.cab_via_local_m ?? null, stand: row.cab_stand_local_xz_m ?? null,
            with: row.passengers?.[0]?.short_name ?? null } : null,
          home: row?.coach_house ? homeFor(row) : null,
          ...(reinsHint ? { reinsHint } : {}),
          giveRoom: row && placeVisitor ? giveRoomFor(row) : null };
      });
      if (town.roots.length) group.add(...town.roots);
    },
  });
  const dispose = town.dispose, update = town.update;
  registerCalls();
  Object.assign(town, { group, ride,
    refreshInteractions() { registration?.refresh(); },
    update(dt, cameraPosition, options) {
      update(dt, cameraPosition, options);
      try { afterUpdate(Number.isFinite(dt) ? dt : 0, cameraPosition); } catch (error) { problems.push(`town transport on call: ${error.message}`); }
    },
    dispose() {
      ride.release('gone'); registration?.dispose(); registration = null;
      for (const thing of callThings.splice(0)) interactions.remove?.(thing.id);
      if (blockerBound) { try { blockerBound.setBlocker(null); } catch { /* gone with its house */ } blockerBound = null; }
      for (const row of onCall) if (row.stand_in_for) parked?.setStandIn?.(row.stand_in_for, true);
      dispose(); group.removeFromParent();
    },
  });
  // T-3557: the coachman's trip home or out (the ride bar, the smoke and the console). Defined,
  // not assigned: Object.assign copies a getter's value once ({}), never the getter.
  Object.defineProperty(town, 'trips', { configurable: true, enumerable: true,
    get: () => Object.fromEntries([...trips].map(([id, trip]) => [id, trip.phase])) });
  return town;
}
