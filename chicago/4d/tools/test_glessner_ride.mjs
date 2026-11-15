#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3557 (second half): the Glessner ride. The waiting Glessner brougham is asked for, its
 * door opens, the visitor sits INSIDE beside Mr. Glessner, Charles Nelson drives a round of
 * the block back to the door, and home to the coach house and out again. Checked here:
 *
 *   - the row (data/transport/driven/loops.json, tools/lay_driven_carriages_1904.mjs): on
 *     call, its stand the parked carriage's own root and bearing, its road on the carriageways
 *     (auditRoad), its crossings with Hans, Henry Windish and Joseph Daniels;
 *   - the round: from the stand, a lap, held at the stand again; with all four 1904 teams
 *     driving, nobody overlaps and every give-way ends;
 *   - the coach house (coach-house.js, its real layer on its record): the round pulls up
 *     where the drive leaves 18th Street, drives in over the drive and kerb (admitted by
 *     clearFor, never by the kerb rule or the walls), stands inside, backs out only until the
 *     whole team stands 3 m past the kerb in 18th Street, drives forward into the round's
 *     lane within the coach's lock, and goes on round to the stand;
 *   - one Mr. Glessner: riding, his standing figure is withheld from his day, his walk, his
 *     door and a tour's stops, and back when the carriage is put away;
 *   - the door (cab-door.js) cut from brougham-near.glb: no area lost, the doorway clear open,
 *     the leaf there shut;
 *   - Mr. Glessner (cab-passenger.js), his own figure on the coachmen's seated clip, bent to
 *     the cab: inside its roof, floor and walls; the visitor's eye clear of both;
 *   - the ride (transport-interactions.js): Get in opens the door, climbs in by the step and
 *     doorway to the cab seat, shuts it, and the round begins; Get out pulls up, opens, steps
 *     down to the walk; Stop, keyboard or touch, by the same actions; the box is still there.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
const { routeFor, routeDistanceNear, createTransportLoop } = await import('../renderers/web/js/transport-loop.js');
const { conflictZones, createCrossings, footprintAt, overlaps } = await import('../renderers/web/js/transport-crossings.js');
const { createCarriagewayReader } = await import('../renderers/web/js/team-drive.js');
const { createCabDoor } = await import('../renderers/web/js/cab-door.js');
const { seatInCab, passengerRoot, CAB_SEAT_POSE } = await import('../renderers/web/js/cab-passenger.js');
const { createTeamRide, registerTransportInteraction, RIDE_S } = await import('../renderers/web/js/transport-interactions.js');
const { createInteractions } = await import('../renderers/web/js/interact.js');
const { glessnerCoachPlan, takeDoorLeaf, planPoint, doorLeafMaterial } = await import('../renderers/web/js/house-doors.js');
const CH = await import('../renderers/web/js/coach-house.js');
const { footprintsFrom } = await import('../renderers/web/js/walker.js');
const { createTransportClearance } = await import('../renderers/web/js/transport-clearance.js');
const { buildRows, auditRoad } = await import('./lay_driven_carriages_1904.mjs');
const { wayJoin, clearOfKerb, exitWay } = await import('../renderers/web/js/town-transport-scene.js');

const ROOT = new URL('../', import.meta.url);
const read = p => JSON.parse(fs.readFileSync(new URL(p, ROOT), 'utf8'));
const wayLength = pts => pts.slice(1).reduce((sum, q, i) => sum + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks++; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const DEG = Math.PI / 180;
const ID = 'prairie_driven_brougham_glessner_1904', PARKED = 'prairie_parked_studebaker_brougham';
const lines = [];

const loops = read('data/transport/driven/loops.json');
const grid = read('data/street_grid/1904.json');
const rows1904 = loops.rows.filter(r => r.scene === '1904');
const row = rows1904.find(r => r.id === ID);
const parked = Object.values(read('data/transport/parked/placements.json').scenes).flat().find(r => r.id === PARKED);

// ---------------------------------------------------------------- the row
{
  ok(row && row.on_call === true && row.stand_in_for === PARKED, 'the Glessner brougham is on call, standing in for the parked one');
  ok(JSON.stringify(buildRows().rows.find(r => r.id === ID)) === JSON.stringify(row), 'loops.json holds the row the lay tool writes');
  ok(row.person_id === 'pa1904_glessner_john_j_c1900_charles_nelson' && row.replace_human_instance === 'hi_pa1904_glessner_john_j_c1900_charles_nelson_1904',
    'Charles Nelson drives it, his standing figure withheld while he does');
  ok(row.passengers.length === 1 && row.passengers[0].person_id === 'glessner_john_j' && row.passengers[0].instance_id === 'hi_glessner_john_j_1904'
    && row.passengers[0].asset_id === 'glessner_john_j_1904', 'Mr. Glessner rides inside as himself (his 1904 record and figure)');
  ok(row.horse_coat_row === PARKED && row.vehicle_finish?.seed && !['panels', 'timber', 'gear', 'quarter', 'upholstery', 'trim'].some(k => k in row.vehicle_finish),
    'the parked pair\'s own coats; the coach its own paint, as it stands, with only the road on it');
  ok(['garment_lower__highwaist_pantaloons', 'accessory__brass_livery_buttons'].every(k => row.driver_livery_colours[k]), 'his own breeches and buttons too, as he stands (the shared body never dyed)');
  ok(row.liberty === 'L-glessner-ride-3557' && fs.readFileSync(new URL('docs/LIBERTIES.md', ROOT), 'utf8').includes('### L-glessner-ride-3557 '),
    'its liberty is recorded');
  const road = routeFor(row.route), rear = road.at(row.initial_distance_m);
  const e = rear.e + Math.sin(rear.yaw) * row.root_ahead_of_rear_axle_m, n = rear.n - Math.cos(rear.yaw) * row.root_ahead_of_rear_axle_m;
  const parkedYaw = Math.PI - parked.bearing_deg * DEG;
  const off = Math.hypot(e - parked.at_local_enu_m[0], n - parked.at_local_enu_m[1]), turn = Math.abs(rear.yaw - parkedYaw) / DEG;
  ok(off < .002 && turn < .01 && Math.abs(rear.curvature) < 1e-9, `at its stand the driven coach is where the parked one is (${(off * 1000).toFixed(2)} mm, ${turn.toFixed(4)} degrees), on a straight`);
  ok(row.stops.length === 1 && row.stops[0].hold === true && row.stops[0].distance_m === row.initial_distance_m
    && row.initial_state === 'stopped' && row.initial_reason === 'stand', 'it starts held at that stand');
  const lock = auditRoad(row, grid);
  ok(lock <= 15 * DEG, 'every wheel and hoof on the carriageways, inside the brougham\'s lock');
  const streets = [...new Set(row.source_ids.filter(s => /^(prairie|e18th|e20th|indiana)/.test(s)))];
  lines.push(`row PASS: ${road.length.toFixed(1)} m clockwise (Prairie 18th-20th south, 20th west, Indiana north, 18th east), sharpest lock ${(lock / DEG).toFixed(1)} deg, `
    + `stand at the parked root within ${(off * 1000).toFixed(2)} mm / ${turn.toFixed(4)} deg${streets.length ? `, ${streets.length} street sources` : ''}`);
}

// ---------------------------------------------------------------- crossings, with all four driving
{
  const zones = conflictZones(rows1904.map(r => ({ id: r.id, row: r, route: routeFor(r.route) })));
  const mine = zones.filter(z => z.a === ID || z.b === ID);
  const partner = z => (z.a === ID ? z.b : z.a);
  ok(mine.some(z => partner(z) === 'prairie_driven_brougham_loop_1904') && mine.some(z => partner(z) === 'prairie_driven_brougham_north_loop_1904')
    && !mine.some(z => partner(z) === 'prairie_driven_brougham_south_loop_1904'), 'it gives way with Hans and Henry Windish; Joseph Daniels never meets it');
  // Driving its round (not held at its stand), for an hour with the other three.
  const driving = rows1904.map(r => (r.id === ID ? { ...r, stops: [], initial_state: 'moving', initial_reason: null } : r));
  const circuits = driving.map(r => ({ id: r.id, row: r, route: routeFor(r.route) }));
  const crossings = createCrossings(circuits);
  const actors = circuits.map(c => createTransportLoop({ ...c.row, route: c.route, heightAt: () => 0,
    assembly: { pose() {}, stop() {} }, gate: crossings.gateFor(c.id) }));
  const dt = .1, waits = [], open = new Map();
  let overlap = null;
  for (let f = 0; f * dt < 3600; f++) {
    for (const a of actors) a.update(dt);
    const prints = actors.map((a, i) => footprintAt(circuits[i].route, circuits[i].row, a.snapshot().distance_m, 0));
    for (let i = 0; i < actors.length; i++) for (let j = i + 1; j < actors.length; j++) if (overlaps(prints[i], prints[j])) overlap ??= { t: f * dt, a: actors[i].id, b: actors[j].id };
    for (const a of actors) {
      const w = a.givingWayTo;
      if (w && !open.has(a.id)) open.set(a.id, { t: f * dt, to: w });
      if (!w && open.has(a.id)) { const o = open.get(a.id); waits.push({ id: a.id, to: o.to, for_s: f * dt - o.t }); open.delete(a.id); }
    }
  }
  ok(overlap === null, `no two teams overlap: ${JSON.stringify(overlap)}`);
  const its = waits.filter(w => w.id === ID || w.to === ID);
  ok(its.length >= 2, `the Glessner brougham gives way and is given way to (${its.length})`);
  // Its side of 18th is Henry Windish's from Indiana to Prairie: the crossings hold that whole
  // stretch (with Hans's corners at either end) for whichever is in it, so the other may wait
  // as long as it takes a team to drive it (about 165 m at 1.1 m/s).
  ok(waits.every(w => w.for_s <= 180) && open.size <= 1, `every wait ends (longest ${Math.max(...waits.map(w => w.for_s)).toFixed(1)} s)`);
  const g = actors[driving.findIndex(r => r.id === ID)];
  ok(g.snapshot().total_distance_m > 3600 * row.speed_m_s * .8, `it keeps its pace (${g.snapshot().total_distance_m.toFixed(0)} m in an hour)`);
  lines.push(`crossings PASS: ${mine.length} zones with its round (${mine.map(z => partner(z).replace('prairie_driven_brougham_', '')).join(', ')}); an hour of all four: no overlap, `
    + `${its.length} of ${waits.length} give-ways its own, longest ${Math.max(...its.map(w => w.for_s)).toFixed(1)} s`);
}

// ---------------------------------------------------------------- the round from the stand, and back
{
  const lap = routeFor(row.route);
  const posed = [];
  const a = createTransportLoop({ ...row, route: lap, heightAt: () => 0, clear: () => true, assembly: { pose(p) { posed.push(p); }, stop() {} } });
  a.update(.1);
  ok(a.state === 'stopped' && a.reason === 'stand' && a.hasCab, 'loaded, it stands at the house');
  const cab = a.seat('cab'), box = a.seat('box');
  ok(near(cab.y, 1.296 + .58, 1e-9) && cab.kind === 'cab' && box.y > cab.y + .2, `the cab eye ${cab.y.toFixed(3)} m, under the box's ${box.y.toFixed(3)} m`);
  const door = a.toWorld([row.cab_stand_local_xz_m[0], 0, row.cab_stand_local_xz_m[1]]);
  const yaw = Math.PI - parked.bearing_deg * DEG;
  const [sx, sz] = row.cab_stand_local_xz_m;
  const want = [parked.at_local_enu_m[0] + Math.cos(yaw) * sx + Math.sin(yaw) * sz, parked.at_local_enu_m[1] + Math.sin(yaw) * sx - Math.cos(yaw) * sz];
  ok(Math.hypot(door.e - want[0], door.n - want[1]) < .01, 'the door\'s stand is the parked coach\'s kerbside door');
  ok(a.resume() && a.state === 'moving', 'Continue: the round begins');
  let t = 0;
  while (t < lap.length / row.speed_m_s + 60 && !(a.state === 'stopped' && a.reason === 'stand' && t > 30)) { a.update(.1); t += .1; }
  ok(a.state === 'stopped' && a.reason === 'stand' && near(a.snapshot().distance_m, row.initial_distance_m, 1e-6), `round the block and back to the door in ${t.toFixed(0)} s`);
  lines.push(`round PASS: from the stand, ${lap.length.toFixed(0)} m round the block back to the door in ${t.toFixed(0)} s at ${row.speed_m_s} m/s; held there`);
  a.dispose();
}

// ---------------------------------------------------------------- the coach house: in and out again
{
  const sidecar = read('data/sidecars/1904/glessner_house.json');
  const section = read('data/street_section/1904.json');
  const BASE = 4.33;
  const plan = glessnerCoachPlan(sidecar);
  // The two baked leaves (as tools/test_coach_house.mjs makes them from the record's plan).
  const dims = CH.coachDims(plan);
  const P3 = (d, s, y) => { const [u, v] = planPoint(plan, d, s); return [u, y, -v]; };
  const quad = (pos, a, b, c, d) => pos.push(...a, ...b, ...c, ...a, ...c, ...d);
  const mesh = (name, quads) => {
    const pos = []; for (const q of quads) quad(pos, ...q);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(pos.length / 3 * 2).fill(.5), 2));
    geo.setIndex([...Array(pos.length / 3).keys()]); geo.computeVertexNormals();
    return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name }));
  };
  const lo = plan.leaf.foot, hi = plan.leaf.top, dF = -.245;
  const painted = mesh('painted_wood', [
    [P3(dF, dims.mid + .2, lo + .3), P3(dF, dims.ls1 - .2, lo + .3), P3(dF, dims.ls1 - .2, hi - .3), P3(dF, dims.mid + .2, hi - .3)],
    [P3(dF, dims.mid + .13, lo), P3(dF, dims.ls0 + .17, lo), P3(dF, dims.ls0 + .17, lo + .24), P3(dF, dims.mid + .13, lo + .24)],
    [P3(dF, plan.man.s[0] + .1, lo + .3), P3(dF, plan.man.s[1] - .1, lo + .3), P3(dF, plan.man.s[1] - .1, plan.man.head - .1), P3(dF, plan.man.s[0] + .1, plan.man.head - .1)],
    [P3(dF, dims.mid + .13, plan.man.head + .1), P3(dF, dims.ls0 + .17, plan.man.head + .1), P3(dF, dims.ls0 + .17, hi - .2), P3(dF, dims.mid + .13, hi - .2)],
  ]);
  const record = { id: 'glessner_house', sidecar };
  const coach = takeDoorLeaf(record, painted, new THREE.Matrix4()).filter(x => x.doorId === plan.id);
  for (const piece of coach) piece.material = doorLeafMaterial(painted.material);
  const p = sidecar.placement;
  const { enuToWorld } = await import('../renderers/web/js/terrain.js');
  const { bearingToYaw } = await import('../renderers/web/js/angles.js');
  const matrix = new THREE.Matrix4().compose(enuToWorld(p.local_e, p.local_n, BASE),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(p.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1));
  const registry = new Map([['glessner_house', record]]);
  const footprints = footprintsFrom(registry);
  const problems = [];
  const house = CH.createCoachHouse({ registry, buildings: { matrixOf: id => (id === 'glessner_house' ? matrix : null), doorLeaves: new Map([[plan.id, coach]]) },
    footprints, decks: [], interactions: createInteractions(), visitor: () => null,
    carriageways: grid.carriageways, drives: section.carriage_drives.drives, reducedMotion: () => false, problems });
  ok(house && typeof house.drivePath === 'function', `the coach house is there to drive into: ${problems.join('; ')}`);
  const fullWay = house.drivePath({ from: row.coach_house.from, row });
  const way = wayJoin(row, fullWay);
  ok(way && way.joined_at > 0 && way.joined_at < fullWay.kerb_index, `the round runs beside the way in from ${way?.joined_at} of its ${fullWay.points_enu_m.length} points`);
  const reader = createCarriagewayReader(grid.carriageways);
  const inPoly = (e, n, poly) => { let y = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > n) !== (b[1] > n) && e < (b[0] - a[0]) * (n - a[1]) / (b[1] - a[1]) + a[0]) y = !y; } return y; };
  const onRoad = (e, n) => grid.carriageways.some(c => inPoly(e, n, c.polygon_local_m));
  const heightAt = (e, n) => (onRoad(e, n) ? BASE : null);
  const pathHeightAt = (e, n) => house.floorAt(e, n) ?? BASE + .15;
  const walls = createTransportClearance({ footprints: () => footprints, envelope_local_xz_m: row.envelope_local_xz_m });
  let admitted = 0, actor = null;
  const admit = (a, b) => house.clearFor(row, a, b) === true;
  const clear = (a, b) => {
    if (walls(a, b)) return true;
    if (actor && actor.mode !== 'route' && admit(a, b)) { admitted++; return true; }
    return false;
  };
  const posed = [];
  actor = createTransportLoop({ ...row, route: routeFor(row.route), heightAt, clear, admit, pathHeightAt,
    road: pose => reader(row, pose), assembly: { pose(q) { posed.push(q); }, stop() {} } });
  actor.update(.1);
  const [be, bn] = way.points_enu_m[0];
  const branch = actor.branchAt(be, bn, { within_m: 4 });
  ok(branch && branch.off_m < 1.5, `its round passes the way in ${branch?.off_m.toFixed(2)} m from where it leaves 18th Street`);
  actor.resume();
  let t = 0;
  const step = (until, limit, dt = .05) => { const t0 = t; while (!until() && t - t0 < limit) { actor.update(dt); house.update(dt); t += dt; } return t - t0; };
  step(() => actor.branched, 900);
  ok(actor.branched && actor.state === 'stopped' && actor.reason === 'branch', `round to the coach house's way and pulled up there (${t.toFixed(0)} s)`);
  const opened = house.open();
  step(() => house.state === 'open', 10);
  ok((await opened).ok, 'the leaves open first');
  let arrived = false;
  ok(actor.followPath(way.points_enu_m, { speed_m_s: .8, yaw_rad: way.yaw_rad, curvature_per_m: way.curvature_per_m, onArrive: () => { arrived = true; } }), 'in it goes');
  const tIn = step(() => arrived, 240);
  const inside = way.inside_enu_m;
  const rearNow = posed.at(-1);
  const rearE = rearNow.e - Math.sin(rearNow.yaw) * row.root_ahead_of_rear_axle_m, rearN = rearNow.n + Math.cos(rearNow.yaw) * row.root_ahead_of_rear_axle_m;
  ok(arrived && actor.way?.mode === 'parked' && actor.reason === 'parked', `it stands in the coach house (${tIn.toFixed(0)} s over the drive; blocked: ${actor.blocked})`);
  ok(Math.hypot(rearE - inside[0], rearN - inside[1]) < .15, `its rear axle at the stand inside (${Math.hypot(rearE - inside[0], rearN - inside[1]).toFixed(3)} m)`);
  ok(admitted > 10 && posed.some(q => q.ramp && q.pitch !== 0), `the doorway and the drive's kerb admitted (${admitted} steps clearFor's), the coach pitched over the ramp`);
  const shut = house.close(); step(() => house.state === 'shut', 10);
  ok((await shut).ok, 'the leaves shut behind it');
  // Out again.
  const open2 = house.open(); step(() => house.state === 'open', 10); await open2;
  // Out again (the lead, 2026-11-15): backed only until the whole team stands clear past the
  // kerb in 18th Street, then driven forward into the round's lane (town-transport-scene.js
  // clearOfKerb, exitWay: the same calls the scene's trip makes).
  let out = false;
  const until = clearOfKerb(row, way);
  ok(typeof until === 'function', 'the kerb line read off the way in');
  ok(until.past({ e: rearE, n: rearN, yaw: rearNow.yaw }) < 0, 'standing inside, the team is behind the kerb line');
  const tracedIn = wayLength(way.points_enu_m);
  ok(actor.backOut({ until, onArrive: () => { out = true; } }), 'it backs out the way it came');
  const tOut = step(() => out, 400);
  const q = actor.pose, rearB = { e: q.e - Math.sin(q.yaw) * row.root_ahead_of_rear_axle_m, n: q.n + Math.cos(q.yaw) * row.root_ahead_of_rear_axle_m, yaw: q.yaw };
  const backed = posed.filter(p => p.reversing).reduce((sum, p, i, all) => sum + (i ? Math.hypot(p.e - all[i - 1].e, p.n - all[i - 1].n) : 0), 0);
  const pastKerb = until.past(rearB);
  ok(out && actor.way?.mode === 'parked' && pastKerb >= 3 && pastKerb < 3.4, `backed out until the team stands ${pastKerb.toFixed(2)} m past the kerb (${tOut.toFixed(0)} s)`);
  ok(backed < 25 && backed < tracedIn / 3, `only ${backed.toFixed(1)} m backed, of the ${tracedIn.toFixed(1)} m it drove in`);
  const exit = exitWay(row, rearB);
  ok(exit && exit.lane_off_m > 3 && exit.turn_deg > 20, `a forward way into the lane: ${exit?.length_m.toFixed(1)} m, ${exit?.turn_deg.toFixed(0)} deg round to it from ${exit?.lane_off_m.toFixed(1)} m across`);
  const maxK = Math.max(...exit.curvature_per_m.map(Math.abs));
  ok(Math.atan(row.wheelbase_m * maxK) <= row.steering_limit_deg * DEG, `inside the coach's lock (${(Math.atan(row.wheelbase_m * maxK) / DEG).toFixed(1)} deg of ${row.steering_limit_deg})`);
  let forward = false;
  const nForward = posed.length;
  ok(actor.followPath(exit.points_enu_m, { speed_m_s: .9, yaw_rad: exit.yaw_rad, curvature_per_m: exit.curvature_per_m, onArrive: () => { forward = true; } }), 'then forward');
  const shutAgain = house.close();
  const tFwd = step(() => forward, 120);
  const fwd = posed.slice(nForward);
  ok(forward && fwd.length > 10 && fwd.every(p => !p.reversing), `forward into its lane in ${tFwd.toFixed(0)} s, no wheel or hoof refused`);
  step(() => house.state === 'shut', 10);
  ok((await shutAgain).ok, 'the leaves shut behind it as it drives off');
  const lane = routeFor(row.route), [ee, en] = exit.points_enu_m.at(-1), laneAt = lane.at(routeDistanceNear(lane, ee, en, .25).distance_m);
  const laneOff = Math.abs((ee - laneAt.e) * Math.cos(laneAt.yaw) + (en - laneAt.n) * Math.sin(laneAt.yaw));
  const qEnd = actor.pose, endOff = Math.abs((qEnd.e - Math.sin(qEnd.yaw) * row.root_ahead_of_rear_axle_m - laneAt.e) * Math.cos(laneAt.yaw) + (qEnd.n + Math.cos(qEnd.yaw) * row.root_ahead_of_rear_axle_m - laneAt.n) * Math.sin(laneAt.yaw));
  ok(laneOff < .01 && endOff < .05 && Math.abs(Math.atan2(Math.sin(qEnd.yaw - laneAt.yaw), Math.cos(qEnd.yaw - laneAt.yaw))) < DEG, `and in the round's own lane on its heading (way ${(laneOff * 100).toFixed(1)} cm, rear axle ${(endOff * 100).toFixed(1)} cm off it)`);
  ok(actor.handBack() && actor.mode === 'returning', 'and the coachman takes it on round');
  step(() => actor.mode === 'route', 120);
  ok(actor.mode === 'route', 'back on its round');
  step(() => actor.state === 'stopped' && actor.reason === 'stand', 900);
  ok(actor.reason === 'stand' && near(actor.snapshot().distance_m, row.initial_distance_m, 1e-6), `and round to the door again (${t.toFixed(0)} s in all)`);
  lines.push(`coach house PASS: from the ${row.coach_house.from}, ${fullWay.length_m.toFixed(1)} m way in (${wayLength(way.points_enu_m).toFixed(1)} m of it driven from where it leaves the round), ${tIn.toFixed(0)} s in over the drive (${admitted} steps admitted by clearFor, pitched on the kerb ramp), `
    + `rear axle ${Math.hypot(rearE - inside[0], rearN - inside[1]).toFixed(2)} m from the stand inside; out: ${backed.toFixed(1)} m backed in ${tOut.toFixed(0)} s to ${pastKerb.toFixed(1)} m past the kerb, then ${exit.length_m.toFixed(1)} m forward in ${tFwd.toFixed(0)} s into its lane (turn ${exit.turn_deg.toFixed(0)} deg on 10 m, glide ${exit.glide_m.toFixed(1)} m at ${exit.glide_deg} deg, ease on 20 m, lock ${(Math.atan(row.wheelbase_m * maxK) / DEG).toFixed(1)} deg), round to the door`);
  actor.dispose(); house.dispose?.();
}

// ---------------------------------------------------------------- the door, cut from the coach
MeshoptDecoder && await MeshoptDecoder.ready; globalThis.self ??= globalThis;
function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
    if (m.extensions) delete m.extensions.KHR_texture_transform;
  }
  delete doc.textures; delete doc.images; delete doc.samplers;
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
const loadGLB = file => new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(fs.readFileSync(new URL(file, ROOT))), '');
const vehicle = (await loadGLB(`renderers/web/${row.vehicle_file}`)).scene;
const door = createCabDoor(vehicle, row.cab_door);
const ray = new THREE.Raycaster();
const solids = () => { const list = []; vehicle.updateMatrixWorld(true); vehicle.traverse(o => { if (o.isMesh && !o.isSkinnedMesh && o.visible) list.push(o); }); return list; };
const hitAlong = (from, dir, far = 3) => { ray.set(from, dir.clone().normalize()); ray.far = far; return ray.intersectObjects(solids(), false)[0] ?? null; };
{
  ok(door.cut.leaf_triangles > 1000 && near(door.cut.area_cut_m2, door.cut.area_body_m2 + door.cut.area_leaf_m2, 1e-6),
    `the leaf is cut from the body with no area lost (${door.cut.area_cut_m2.toFixed(4)} = ${door.cut.area_body_m2.toFixed(4)} + ${door.cut.area_leaf_m2.toFixed(4)} m2)`);
  door.set(0);
  // Through the doorway forward of the open leaf (which stands back toward its rear hinge).
  const across = [[1.2, 0], [1.5, 0], [1.75, 0], [1.3, .1], [1.75, .1], [1.0, .1]];
  // Open, the leaf stands back toward its rear hinge: its free edge about z 0 at x -1.24.
  const through = [[1.0, .1], [1.3, .1], [1.75, .1], [1.5, .15], [1.2, .2]];
  const shutHits = across.filter(([y, z]) => { const h = hitAlong(new THREE.Vector3(-1.4, y, z), new THREE.Vector3(1, 0, 0), .85); return h && /door/.test(h.object.name); }).length;
  ok(shutHits === across.length, 'shut, the leaf closes the doorway');
  const opening = door.open(); let s = 0;
  while (door.state !== 'open' && s < 5) { door.update(1 / 30); s += 1 / 30; }
  ok(await opening && near(door.angle_deg, row.cab_door.open_deg, 1e-6) && near(s, row.cab_door.duration_s, .1), `open in ${s.toFixed(2)} s to ${door.angle_deg} degrees`);
  const openHits = through.filter(([y, z]) => { const h = hitAlong(new THREE.Vector3(-1.4, y, z), new THREE.Vector3(1, 0, 0), .85); return h && h.point.x < -.45; }).length;
  ok(openHits === 0, 'open, the doorway is clear from the walk to the seat, forward of the leaf');
  const closing = door.close(); door.update(.01, { reducedMotion: true });
  ok(await closing && door.state === 'shut', 'reduced motion: the door is set shut, not swung');
  lines.push(`door PASS: ${door.cut.meshes} body meshes cut, leaf ${door.cut.leaf_triangles} triangles, ${door.cut.area_leaf_m2.toFixed(3)} m2 of ${door.cut.area_cut_m2.toFixed(3)} m2 cut, no area lost; open ${row.cab_door.open_deg} deg in ${row.cab_door.duration_s} s, doorway clear; shut, closed`);
}

// ---------------------------------------------------------------- Mr. Glessner, and the visitor's eye
{
  const gl = await loadGLB('assets/humans/web/glessner_john_j_1904.lod0.glb');
  const drv = await loadGLB(`assets/humans/web/${row.driver_asset}.lod0.glb`);
  const clip = drv.animations.find(a => a.name === row.driver_clip);
  ok(clip, `the coachmen's seated clip ${row.driver_clip}`);
  const spec = row.passengers[0];
  const rider = new THREE.Group(); rider.add(gl.scene); vehicle.add(rider);
  rider.position.fromArray(passengerRoot({ seat_local_m: spec.seat_local_m, clip_seat_local_m: row.driver_seat_node_m, sink_m: spec.sink_m }));
  const mixer = new THREE.AnimationMixer(gl.scene); mixer.clipAction(clip).play(); mixer.update(0);
  vehicle.updateMatrixWorld(true);
  const seat = seatInCab(gl.scene, CAB_SEAT_POSE, rider);
  // Two frames as the loader runs them: restore, mixer, bend.
  for (let i = 0; i < 2; i++) { seat.restore(); mixer.update(1 / 30); seat.apply(); }
  vehicle.updateMatrixWorld(true);
  ok(seat.hidden.length >= 1, `his hat is off indoors (${seat.hidden.map(m => m.name).join(', ')})`);
  door.set(0);
  const toVehicle = new THREE.Matrix4().copy(vehicle.matrixWorld).invert();
  const points = [];
  gl.scene.traverse(o => {
    if (!o.isSkinnedMesh || !o.visible) return;
    o.skeleton.update();
    const v = new THREE.Vector3();
    for (let i = 0; i < o.geometry.attributes.position.count; i += 5) { o.getVertexPosition(i, v); v.applyMatrix4(o.matrixWorld).applyMatrix4(toVehicle); points.push(v.clone()); }
  });
  ok(points.length > 500, 'his figure, sampled');
  // Inside: the cab's own inner walls, read from its middle below the windows (the glass is
  // not drawn, so a ray out through a window finds nothing): every sampled point between them,
  // under the roof lining (an upward ray from it meets the cab) and over the seat or floor.
  const dirs = [new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, -1, 0)];
  const middle = new THREE.Vector3(0, 1.45, -.45);
  const wallAt = d => hitAlong(middle, new THREE.Vector3(...d), 2)?.point;
  const inner = { left: wallAt([1, 0, 0]).x, right: wallAt([-1, 0, 0]).x, front: wallAt([0, 0, 1]).z, back: wallAt([0, 0, -1]).z };
  let outside = 0, roof = Infinity, floor = Infinity, wall = Infinity, cushion = 0, cushionDepth = 0;
  for (const q of points) {
    // (The floor stops 5 cm short of the seat's riser, brougham-near.glb: a ray down that seam
    // finds nothing, so a point over it is read either side of it.)
    const upHit = hitAlong(q, dirs[0]);
    const downHit = hitAlong(q, dirs[1]) ?? hitAlong(q.clone().setZ(q.z + .07), dirs[1]) ?? hitAlong(q.clone().setZ(q.z - .07), dirs[1]);
    const within = q.x > inner.right && q.x < inner.left && q.z > inner.back && q.z < inner.front;
    // Into the cushion's front lip (the seat timber under the leather at 1.217 m): the underside
    // of his thighs sits into it, as a seated man sinks into a cushion; counted, not refused.
    if (upHit && !downHit && within && q.y > row.cab_seat_local_m[1] - .12 && q.z < -.55) { cushion++; cushionDepth = Math.max(cushionDepth, 1.217 - q.y); continue; }
    if (!upHit || !downHit || !within) { outside++; continue; }
    roof = Math.min(roof, upHit.distance); floor = Math.min(floor, downHit.distance);
    wall = Math.min(wall, q.x - inner.right, inner.left - q.x, q.z - inner.back, inner.front - q.z);
  }
  const escaped = outside;
  ok(cushion <= points.length * .005 && cushionDepth <= .04, `${cushion} points of him sit into the cushion's front lip, at most ${(cushionDepth * 100).toFixed(1)} cm`);
  ok(escaped === 0, `every point of him is inside the cab (${escaped} of ${points.length} not; walls x ${inner.right.toFixed(3)} to ${inner.left.toFixed(3)}, z ${inner.back.toFixed(3)} to ${inner.front.toFixed(3)})`);
  // The visitor's eye on the kerbside half of the seat.
  const eye = new THREE.Vector3(row.cab_seat_local_m[0], row.cab_seat_local_m[1] + row.cab_eye_m, row.cab_seat_local_m[2]);
  let eyeClear = Infinity;
  for (let a = 0; a < 26; a++) {
    const d = new THREE.Vector3(Math.cos(a * 2.4) * Math.sin(a * .121 + .1), Math.cos(a * .121 + .1), Math.sin(a * 2.4) * Math.sin(a * .121 + .1));
    const h = hitAlong(eye, d, 2); if (h) eyeClear = Math.min(eyeClear, h.distance);
  }
  const up = hitAlong(eye, new THREE.Vector3(0, 1, 0));
  const fromHim = Math.min(...points.map(q => q.distanceTo(eye)));
  ok(up && eyeClear >= .12 && up.distance >= .12, `the visitor's eye ${eyeClear.toFixed(3)} m clear of the cab (${up?.distance.toFixed(3)} m under the roof)`);
  ok(fromHim >= .2, `and ${fromHim.toFixed(2)} m from Mr. Glessner`);
  const head = Math.max(...points.map(q => q.y));
  lines.push(`seats PASS: Mr. Glessner bent to the cab (${seat.bones.length} bones, hat off), every sampled point inside; roof ${(roof * 100).toFixed(1)} cm over his head (top ${head.toFixed(3)} m), `
    + `walls ${(wall * 100).toFixed(1)} cm, ${cushion} points up to ${(cushionDepth * 100).toFixed(1)} cm into the cushion lip; visitor eye y ${eye.y.toFixed(3)} m (cushion ${row.cab_seat_local_m[1]} + ${row.cab_eye_m}), ${(eyeClear * 100).toFixed(1)} cm clear, roof ${(up.distance * 100).toFixed(1)} cm over, ${fromHim.toFixed(2)} m from him`);
}

// ---------------------------------------------------------------- the ride: get in, round, get out
{
  const lap = routeFor(row.route);
  const doorMock = { state: 'shut', f: 0, open() { this.want = 'open'; return Promise.resolve(true); }, close() { this.want = 'shut'; return Promise.resolve(true); },
    update(dt, { reducedMotion = false } = {}) {
      if (!this.want) return;
      this.f = reducedMotion ? (this.want === 'open' ? 1 : 0) : Math.max(0, Math.min(1, this.f + (this.want === 'open' ? 1 : -1) * dt / 1.6));
      this.state = this.f >= 1 ? 'open' : this.f <= 0 ? 'shut' : this.want === 'open' ? 'opening' : 'closing';
    } };
  const a = createTransportLoop({ ...row, route: lap, heightAt: () => 0, clear: () => true, assembly: { pose() {}, stop() {} } });
  a.assembly = { door: doorMock };
  let reduced = false;
  const eye = { e: a.toWorld?.([0, 0, 0])?.e ?? 0, n: 0, y: 1.6, bearing: 0 };
  a.update(.1);
  const outside = a.toWorld([row.cab_stand_local_xz_m[0], 0, row.cab_stand_local_xz_m[1]]);
  Object.assign(eye, { e: outside.e, n: outside.n, y: 1.6 });
  const boarded = [];
  const ride = createTeamRide({ visitor: () => eye, standFor: () => ({ e: outside.e, n: outside.n }), groundAt: () => 0, walkEye: () => 1.6,
    onBoard: (x, on) => boarded.push(on), reducedMotion: () => reduced });
  const ix = createInteractions();
  const handle = registerTransportInteraction(ix, a, { vehicle: 'carriage', driver: 'coachman', ride, rideName: row.ride_name,
    cab: { via: row.cab_via_local_m, stand: row.cab_stand_local_xz_m, with: row.passengers[0].short_name } });
  const run = (seconds, dt = 1 / 30) => { for (let s = 0; s < seconds; s += dt) { a.update(dt, { reducedMotion: reduced }); doorMock.update(dt, { reducedMotion: reduced }); ix.update(dt); } };
  const ids = () => ix.actionsOf(handle.thing).map(x => x.id);
  run(.1);
  ok(ids()[0] === 'get-in' && ids().includes('climb-up'), `at the door: ${ix.actionsOf(handle.thing).map(x => x.label).join(' / ')}`);
  ok(ix.actionsOf(handle.thing)[0].label === 'Get in beside Mr. Glessner', 'Get in beside Mr. Glessner');
  ok(ix.act(handle.thing.id, 'get-in').ok, 'Interact: Get in');
  run(RIDE_S.door + .1);
  ok(doorMock.state === 'open', 'the door opens first');
  run(RIDE_S.board + RIDE_S.door + .5);
  ok(ride.phase === 'seated' && ride.inCab && ride.seatKind === 'cab', 'seated inside the cab');
  ok(doorMock.state === 'shut', 'the door shut behind');
  ok(a.state === 'moving' && a.mode === 'route', 'and the round begins');
  const seatNow = ride.seatOf(a);
  ok(near(seatNow.y, 1.296 + .58, 1e-6), 'the eye held on the cab seat');
  ok(ids().includes('stop') && ids().includes('get-down') && !ids().includes('take-reins'), `inside: ${ix.actionsOf(handle.thing).map(x => x.label).join(' / ')}`);
  ok(ix.actionsOf(handle.thing).find(x => x.id === 'get-down').label === 'Get out', 'Get out, not Get down');
  run(20);
  // Stop, then Get out: pulled up, the door, down to the walk.
  ok(ix.act(handle.thing.id, 'stop').ok && a.state === 'stopped', 'Stop: the coachman pulls up');
  run(.2);
  ok(ix.act(handle.thing.id, 'get-down').ok, 'Get out');
  run(RIDE_S.pullUp + RIDE_S.door * 2 + RIDE_S.unboard + 1);
  ok(!ride.actor && !ride.inCab && boarded.at(-1) === false, 'out and down');
  ok(doorMock.state === 'shut', 'the door shut again');
  const land = ride.landing;
  const drop = a.toWorld([row.cab_stand_local_xz_m[0], 0, row.cab_stand_local_xz_m[1]]);
  ok(land && Math.hypot(land.e - drop.e, land.n - drop.n) < .05, 'on the walk by its door');
  // Reduced motion: in, and the team stands.
  reduced = true;
  run(.1);
  ok(ix.act(handle.thing.id, 'get-in').ok, 'reduced motion: Get in still');
  run(RIDE_S.pullUp + RIDE_S.board + 1);
  ok(ride.inCab && a.state === 'stopped', 'in, and the team stands');
  ok(ix.act(handle.thing.id, 'get-down').ok, 'and out again');
  run(RIDE_S.pullUp + RIDE_S.unboard + 1);
  ok(!ride.actor, 'down');
  reduced = false;
  // The box is still there: Climb up beside the coachman.
  run(.1);
  ok(ids().includes('climb-up'), 'Climb up beside the coachman is still offered');
  handle.dispose(); a.dispose();
  lines.push(`ride PASS: Get in beside Mr. Glessner (door ${RIDE_S.door}s, step and doorway ${RIDE_S.board}s, door shut, round on), Stop, Get out to the walk by the door; reduced motion stands; the box offered`);
}

// ---------------------------------------------------------------- Mr. Glessner is in one place
// The lead, 2026-11-15: while he rides in the cab, his own figure is withheld from wherever else
// 1904 draws him (his day, a door's Ask for, his front-walk greeting, a jaunt's host or stage),
// and he is back when the carriage is put away. The assembly takes him as it takes the coachman
// (driven-assembly-loader.js adoptPerson -> humans.withhold); this runs the real layer registry
// (humans.js), jaunt-hosts.js and house-errands.js against it.
{
  const row = read('data/transport/driven/loops.json').rows.find(r => r.id === ID);
  const [spec] = row.passengers;
  const standingRec = read('data/humans/instances/1904/hi_glessner_john_j_1904.json');
  ok(spec.instance_id === standingRec.id && spec.person_id === standingRec.person_id, 'the cab takes his own standing instance, by id');
  const loader = fs.readFileSync(new URL('renderers/web/js/driven-assembly-loader.js', ROOT), 'utf8');
  ok(/for \(const rider of riders\) restores\.push\(adoptPerson\(rider\.instance, rider\.actor\)\)/.test(loader)
    && /assembly\.dispose = \(\) => \{ dispose\(\);[^\n]*for \(const r of restores\.splice\(0\)\) r\?\.\(\)/.test(loader), 'the assembly withholds each passenger and gives them back on dispose');
  const source = fs.readFileSync(new URL('renderers/web/js/humans.js', ROOT), 'utf8');
  const start = source.indexOf('export function createHumanLayer('), end = source.indexOf('\n/**\n * THE SCENE PATH.', start);
  class Actor {
    constructor({ instance, identity, person }) {
      Object.assign(this, { instance, identity, person, id: instance.id, personId: instance.person_id, root: new THREE.Group(),
        body: {}, disposed: false, tier: 'full', e: instance.placement?.local_e ?? 0, n: instance.placement?.local_n ?? 0, heading: 0, indoors: false, walked: 0 });
    }
    update() {} dispose() { this.disposed = true; this.root.removeFromParent(); }
    walkPath() { this.walked++; return true; } setState() {} place() {} turnTo() {} stopPath() {} setIndoors(v) { this.indoors = v; }
  }
  const createLayer = new Function('THREE', 'HumanActor', 'createHumanAssets', 'humanRoleCard', 'HUMAN_TIERS',
    source.slice(start, end).replace('export function', 'function') + '\nreturn createHumanLayer;')(THREE, Actor, () => ({}), () => null, { full: [0], balanced: [1], light: [3] });
  const humans = createLayer({ assets: {} });
  const person = { id: 'glessner_john_j', name: 'John J. Glessner', household: 'hh_glessner_john_j' };
  const standing = humans.add(standingRec, { person });
  const rider = new Actor({ instance: { ...standingRec, behaviour: { state: 'seated' } }, identity: standing.identity, person });
  const { createJauntHosts } = await import('../renderers/web/js/jaunt-hosts.js');
  const { createHouseErrands } = await import('../renderers/web/js/house-errands.js');
  const interactions = createInteractions();
  const door = { id: 'glessner_house:front', actions: {}, get state() { return 'shut'; } };
  const errands = createHouseErrands({ humans, houseDoors: { get: id => (id === 'glessner_house:front' ? door : null), open() {}, close() {} }, interactions });
  const greet = errands.get('glessner_john_j');
  ok(greet && greet.at && greet.actions.out.some(x => x.id === 'greet'), 'on his front walk he can be greeted');
  const asksFor = () => { greet.state = 'home'; const offered = (door.actions.closed ?? []).some(x => x.id === 'ask:glessner_john_j'); greet.state = 'out'; return offered; };
  ok(asksFor(), 'at home, his door offers to ask for him');
  const tourHost = [{ person: 'glessner_john_j', local_e: 1390.9, local_n: -3226.7 }];
  // Asked for a ride: the assembly takes him into the cab.
  const giveBack = humans.withhold(spec.person_id, { instanceId: spec.instance_id, externalActor: rider });
  ok(standing.root.parent === null && humans.isHeld(standing) && humans.get('glessner_john_j') === rider, 'riding: his standing figure is out of the town, held, and Find finds him in the cab');
  ok(!humans.actors.includes(standing), 'his day no longer has him to advance or ask for (human-days skips a held figure)');
  ok(greet.at === null && !greet.actions.out.length && !greet.actions.home.length, 'no greeting him on the walk he is not on');
  ok(!asksFor(), 'nor asking for him at his door');
  assert.throws(() => humans.add({ ...standingRec, id: 'hi_inside_glessner_john_j' }, { person }), /already stands/);
  checks++;
  const hosts = createJauntHosts({ humans, days: null, router: { plan: () => null } });
  hosts.sync(tourHost, { stand: { e: 1390, n: -3222 }, arrived: true, cut: true });
  ok(hosts.active.length === 0 && hosts.waiting.includes('glessner_john_j') && rider.walked === 0 && !rider.jauntHost,
    'a tour stop waits for him; it never walks him out of the cab');
  // Put away at the stand: the carriage is disposed, and he is himself again.
  giveBack();
  ok(standing.root.parent === humans.group && !humans.isHeld(standing) && humans.get('glessner_john_j') === standing && humans.external('glessner_john_j') === null, 'put away: his figure is back where it stood');
  ok(greet.at && greet.actions.out.length && asksFor(), 'greeted on his walk, and asked for at his door, again');
  hosts.update(1);
  ok(hosts.active.includes('glessner_john_j') && hosts.waiting.length === 0, 'and the tour stop has him');
  hosts.release();
  lines.push('one Mr. Glessner PASS: riding, his standing figure is withheld (held, out of his day, no greeting, no Ask for at his door, no second figure, a tour host waits for him); put away, he is back, greeted and hosted');
}

for (const line of lines) console.log(line);
console.log(`T-3557 Glessner ride: ${checks} checks PASS`);
