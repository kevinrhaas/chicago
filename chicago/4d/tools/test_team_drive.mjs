// SPDX-License-Identifier: GPL-3.0-or-later
// T-3557: taking the reins of a driven team. Plain node, no deps: a loop with a fake assembly on a
// flat plane is taken, driven, steered, refused, handed back and saved, and the pure drive math
// (team-drive.js) is checked on its own.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { circleRoute, createTransportLoop, routeDistanceNear, routeFor } from '../renderers/web/js/transport-loop.js';
import { driveLimits, easeControls, easeReverse, bicycleStep, sampleOf, pursuitSteering, refineRouteDistance,
  wheelArcRatios, footprintOfPose, teamGroundPoints, createCarriagewayReader, KERB_ROOM_M } from '../renderers/web/js/team-drive.js';
import { overlaps, createCrossings } from '../renderers/web/js/transport-crossings.js';
import { createTownTransport } from '../renderers/web/js/town-transport.js';

let count = 0;
const ok = (cond, message) => { assert(cond, message); count++; };
const near = (a, b, eps = 1e-9, message = `${a} != ${b}`) => ok(Math.abs(a - b) <= eps, message);
const DEG = Math.PI / 180;
const angle = a => Math.atan2(Math.sin(a), Math.cos(a));

// --- pure math ---------------------------------------------------------------------------
const limits = driveLimits({ speed_m_s: 1.3, steering_limit_deg: 15, wheelbase_m: 2.3 });
near(limits.max_m_s, 1.5);
near(limits.steer_max_rad, 15 * DEG);
{
  // Straight: a metre forward along forward = (sin yaw, -cos yaw).
  const s = bicycleStep(sampleOf(0, 0, Math.PI / 2, 0), 0, 1, 2.3);
  near(s.e, 1); near(s.n, 0, 1e-12);
  // Full lock left for a quarter circle of the bicycle's radius: the yaw turns by exactly 90 degrees
  // and the axle ends one radius left and one radius ahead.
  const steer = 15 * DEG, r = 2.3 / Math.tan(steer);
  let t = sampleOf(0, 0, Math.PI / 2, 0); // facing east
  for (let i = 0; i < 100; i++) t = bicycleStep(t, steer, r * Math.PI / 2 / 100, 2.3);
  near(angle(t.yaw - Math.PI), 0, 1e-9, 'quarter turn left ends facing north');
  near(t.e, r, 1e-9); near(t.n, r, 1e-9);
  // Steering eases, rate-limited, to the lock and no further; speed eases to the cap and no further.
  let c = { speed: 0, steering: 0 };
  c = easeControls(c, { throttle: 1, steer: 1 }, limits, .05);
  ok(c.speed > 0 && c.speed <= limits.accel_m_s2 * .05 + 1e-12, 'speed eases up');
  ok(c.steering < 0 && -c.steering <= limits.steer_rate_rad_s * .05 + 1e-12, 'right steer is a negative (clockwise) angle, rate-limited');
  for (let i = 0; i < 400; i++) c = easeControls(c, { throttle: 1, steer: 1 }, limits, .05);
  near(c.speed, 1.5); near(c.steering, -limits.steer_max_rad);
  for (let i = 0; i < 400; i++) c = easeControls(c, { throttle: -1, steer: 0 }, limits, .05);
  near(c.speed, 0); near(c.steering, 0);
  // Pure pursuit: a target dead ahead is straight on, one behind turns round on full lock.
  near(pursuitSteering(sampleOf(0, 0, Math.PI / 2, 0), { e: 10, n: 0 }, limits), 0);
  near(Math.abs(pursuitSteering(sampleOf(0, 0, Math.PI / 2, 0), { e: -10, n: .1 }, limits)), limits.steer_max_rad);
  ok(pursuitSteering(sampleOf(0, 0, Math.PI / 2, 0), { e: 5, n: 3 }, limits) > 0, 'a target to the left turns left');
  // Nearest route distance.
  const circle = circleRoute({ center_enu_m: [0, 0], radius_m: 10 });
  const coarse = routeDistanceNear(circle, 0, 13);
  const fine = refineRouteDistance(circle, 0, 13, coarse.distance_m, .5, .1);
  near(fine.distance_m, circle.length / 4, 1e-3); near(fine.off_m, 3, 1e-6);
  // Wheels on a turn: the outer wheels roll further; the front further than the rear.
  const ratios = wheelArcRatios(.1, 1.2, 2);
  ok(ratios[1] > ratios[0] && ratios[3] > ratios[2] && ratios[2] > ratios[0], 'turning wheel arcs differ');
  // Footprints overlap where the envelopes meet.
  const env = [-1, -2, 1, 5];
  ok(overlaps(footprintOfPose({ e: 0, n: 0, yaw: 0 }, env), footprintOfPose({ e: 1.5, n: 0, yaw: 0 }, env)), 'touching footprints overlap');
  ok(!overlaps(footprintOfPose({ e: 0, n: 0, yaw: 0 }, env), footprintOfPose({ e: 2.5, n: 0, yaw: 0 }, env)), 'apart footprints do not');
}

// --- a driven loop -----------------------------------------------------------------------
const route = circleRoute({ center_enu_m: [0, 0], radius_m: 20 });
function setup({ clear = () => true, heightAt = () => 2, why = null, gate = null, road = null, row = {} } = {}) {
  const poses = [], advances = [];
  const assembly = { pose(p) { poses.push(p); }, advance(dt, ds) { advances.push({ dt, ds }); }, stop() {}, visible() {}, dispose() {} };
  const actor = createTransportLoop({ id: 'test', name: 'Driver', route, assembly,
    speed_m_s: 1.3, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [.3, 1.58, .65], heightAt, clear, why, gate, road, ...row });
  return { actor, poses, advances };
}
const frames = (actor, seconds, input = null, flags = {}) => {
  for (let t = 0; t < seconds - 1e-9; t += 1 / 30) {
    if (input && actor.mode === 'reins') actor.drive(typeof input === 'function' ? input(t) : input);
    actor.update(1 / 30, flags);
  }
};

{
  const { actor, advances } = setup();
  ok(actor.mode === 'route', 'starts on its round');
  ok(actor.blocked === null, 'not blocked on its round');
  // Seat: the fallback is the driver's seat mirrored across the team, eye .8 m above the cushion.
  const seat = actor.seat(), pose = actor.pose;
  near(seat.y, 2 + 1.58 + .8);
  near(seat.e, pose.e + Math.cos(pose.yaw) * -.3 + Math.sin(pose.yaw) * .65);
  near(seat.n, pose.n + Math.sin(pose.yaw) * -.3 - Math.cos(pose.yaw) * .65);
  near(seat.yaw_rad, pose.yaw); near(seat.heading_deg, actor.heading_deg);
  actor.stop('boarding');
  ok(actor.takeReins(), 'takes the reins');
  ok(actor.mode === 'reins' && actor.state === 'moving', 'reins: under the visitor, its journey live');
  near(actor.speed_m_s, 0);
  near(actor.pose.steering, Math.atan(2 / 20), 1e-12, 'the wheels stay where the round had them');
  frames(actor, 1, { throttle: 0, steer: 0 }); // let go: the wheels centre where it stands
  near(actor.pose.steering, 0, 1e-12);
  const yaw0 = actor.pose.yaw, dist0 = actor.snapshot().total_distance_m;
  // Walk on, straight: it goes straight ahead and the speed eases up to, and never past, 1.5 m/s.
  let topSpeed = 0;
  for (let i = 0; i < 300; i++) { actor.drive({ throttle: 1, steer: 0 }); actor.update(1 / 30); topSpeed = Math.max(topSpeed, actor.speed_m_s); }
  near(topSpeed, 1.5, 1e-9, 'speed capped at 1.5 m/s');
  ok(advances.every(a => a.dt <= .05 + 1e-12), 'ticks stay <= .05 s');
  // The team began on the circle's tangent, so straight ahead leaves the route.
  near(angle(actor.pose.yaw - yaw0), 0, 1e-6, 'straight on keeps the heading');
  ok(actor.snapshot().total_distance_m - dist0 > 10, 'it travelled');
  // Steer right: the heading turns clockwise (yaw decreases), the angle within the lock.
  const before = actor.snapshot(), yawBefore = actor.pose.yaw;
  let maxSteer = 0;
  for (let i = 0; i < 90; i++) { actor.drive({ throttle: 1, steer: 1 }); actor.update(1 / 30); maxSteer = Math.max(maxSteer, Math.abs(actor.pose.steering)); }
  ok(angle(actor.pose.yaw - yawBefore) < -10 * DEG, 'a right turn turns the team clockwise');
  ok(actor.pose.steering < 0, 'right steering is negative');
  ok(maxSteer <= 12 * DEG + 1e-12, `steering stays within its 12 degree lock (${maxSteer / DEG})`);
  near(maxSteer, 12 * DEG, 1e-9, 'and reaches it');
  const after = actor.snapshot();
  const turned = after.wheel_rotation_rad.map((r, i) => angle(r - before.wheel_rotation_rad[i]));
  ok(Math.abs(turned[0] - turned[1]) > 1e-3, 'rear wheels turn by different arcs on a turn');
  // Right turn: the left (outer, +x) wheels roll further.
  ok(turned[0] > turned[1], 'outer left rear rolls further on a right turn');
  // Input stale: no drive() calls and the team eases to a halt.
  for (let i = 0; i < 150; i++) actor.update(1 / 30);
  near(actor.speed_m_s, 0, 1e-12, 'no input: the team pulls up');
  near(actor.pose.steering, 0, 1e-12, 'no input: the wheels centre');
  ok(actor.snapshot().mode === 'reins', 'snapshot says the mode');
}

{
  // A refusing clear(): it pulls up, reports why, never throws, never moves; steering still turns.
  let refuse = false;
  const { actor } = setup({ clear: () => !refuse, why: () => refuse ? 'a wall' : null });
  actor.takeReins();
  frames(actor, 3, { throttle: 1, steer: 0 });
  refuse = true;
  const at = actor.at;
  assert.doesNotThrow(() => frames(actor, 1, { throttle: 1, steer: 0 })); count++;
  ok(actor.blocked === 'a wall', `blocked reports the wall (${actor.blocked})`);
  near(actor.speed_m_s, 0);
  assert.deepEqual(actor.at, at); count++;
  frames(actor, 1, { throttle: 0, steer: 1 });
  ok(actor.pose.steering < -5 * DEG, 'it can still be steered while pulled up');
  ok(actor.blocked === null, 'letting go of the reins clears the word');
  refuse = false;
  frames(actor, 1, { throttle: 1, steer: 1 });
  ok(Math.hypot(actor.at[0] - at[0], actor.at[1] - at[1]) > .05, 'it walks on once the way is clear');
}

{
  // Ground that throws (no rendered ground off the edge of a plateau): it pulls up, no throw.
  // The team starts at (20, 0) facing north on its counter-clockwise circle; the ground ends at
  // e = 14, and it is steered hard left, west, toward the edge.
  const { actor: west } = setup({ heightAt: e => e > 14 ? 2 : NaN });
  west.takeReins();
  assert.doesNotThrow(() => frames(west, 30, { throttle: 1, steer: -1 })); count++;
  ok(west.blocked === 'rough ground', `ground refusal word (${west.blocked})`);
  near(west.speed_m_s, 0);
  ok(west.pose.e > 14, 'it never drove off its ground');
  // A wheel step over 30 mm reads as the kerb.
  const { actor: kerb } = setup({ heightAt: (e, n) => n > 3 ? 2.1 : 2 });
  kerb.takeReins();
  assert.doesNotThrow(() => frames(kerb, 10, { throttle: 1, steer: 0 })); count++;
  ok(kerb.blocked === 'the kerb', `kerb word (${kerb.blocked})`);
  // An assembly pose that throws (horse support) is caught, the last pose kept.
  let fail = false;
  const poses = [];
  const assembly = { pose(p) { if (fail) throw Error('transport support: horse support exceeds 2-degree standing bound'); poses.push(p); }, advance() {}, stop() {} };
  const horse = createTransportLoop({ id: 'h', name: 'H', route, assembly, speed_m_s: 1.3, wheelbase_m: 2, track_m: 1.2,
    root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12, wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.5, .6], heightAt: () => 2 });
  horse.takeReins();
  frames(horse, 2, { throttle: 1, steer: 0 });
  fail = true;
  const at = horse.at;
  assert.doesNotThrow(() => frames(horse, 1, { throttle: 1, steer: 0 })); count++;
  ok(horse.blocked === 'rough ground', 'support refusal word');
  assert.deepEqual(horse.at, at); count++;
}

{
  // Hand back on an open plane: the driver steers it back and it rejoins its round in bounded time.
  for (const [label, drive] of [['beside the road', { throttle: 1, steer: 0 }], ['turned round', t => ({ throttle: 1, steer: t < 12 ? 1 : 0 })]]) {
    const { actor } = setup();
    actor.takeReins();
    frames(actor, 20, drive);
    const off = routeDistanceNear(route, ...actor.at).off_m;
    ok(off > 3, `${label}: it is well off its road (${off.toFixed(1)} m)`);
    ok(actor.handBack(), 'hands back');
    ok(actor.mode === 'returning', 'returning');
    let t = 0;
    while (actor.mode !== 'route' && t < 120) { actor.update(1 / 30); t += 1 / 30; }
    ok(actor.mode === 'route', `${label}: back on its round in ${t.toFixed(1)} s`);
    ok(actor.blocked === null, 'no longer blocked');
    // It goes on round from there, on the route.
    const total = actor.snapshot().total_distance_m;
    frames(actor, 5);
    near(actor.snapshot().total_distance_m - total, 5 * 1.3, 1e-6, 'its round resumes at its own pace');
    const p = route.at(actor.snapshot().distance_m);
    near(Math.hypot(actor.pose.e - (p.e + p.forwardE), actor.pose.n - (p.n + p.forwardN)), 0, 1e-9, `${label}: on its road`);
    console.log(`  hand back ${label}: ${off.toFixed(1)} m off, rejoined in ${t.toFixed(1)} s`);
  }
  // Not drawn while returning: put straight back at its nearest distance.
  const { actor } = setup();
  actor.takeReins();
  frames(actor, 10, { throttle: 1, steer: 0 });
  actor.handBack();
  const nearest = actor.snapshot().distance_m;
  actor.update(1 / 30, { drawn: false });
  ok(actor.mode === 'route', 'out of sight it rejoins at once');
  near(actor.snapshot().distance_m, nearest, 1e-6);
}

{
  // Snapshot of a driven team restores onto the route at its nearest distance.
  const { actor } = setup();
  actor.takeReins();
  frames(actor, 15, { throttle: 1, steer: .3 });
  const saved = actor.snapshot();
  ok(saved.mode === 'reins', 'saved while driven');
  ok(Number.isFinite(saved.distance_m) && saved.distance_m >= 0 && saved.distance_m < route.length, 'a route distance');
  // Its nearest: no route sample is nearer the live rear axle than the saved one.
  const rearAxle = [actor.pose.e - actor.pose.forwardE, actor.pose.n - actor.pose.forwardN];
  const savedAt = route.at(saved.distance_m), coarse = routeDistanceNear(route, ...rearAxle, .05);
  ok(Math.hypot(savedAt.e - rearAxle[0], savedAt.n - rearAxle[1]) <= coarse.off_m + 1e-6, 'saved at its nearest route distance');
  actor.dispose();
  const restored = setup({ row: { initial_distance_m: saved.distance_m, initial_total_distance_m: saved.total_distance_m,
    initial_wheel_rotation_rad: saved.wheel_rotation_rad, initial_state: saved.state } }).actor;
  ok(restored.mode === 'route', 'restored on its round');
  const p = route.at(saved.distance_m);
  near(Math.hypot(restored.pose.e - (p.e + p.forwardE), restored.pose.n - (p.n + p.forwardN)), 0, 1e-9, 'on the route');
}

{
  // The crossing gate is let go while driven and taken again on rejoin.
  let dropped = 0, rejoined = 0;
  const gate = { allow: (d, ds) => ds, moved() {}, drop() { dropped++; }, rejoin() { rejoined++; return rejoined > 1; }, waitingFor: 'other' };
  const { actor } = setup({ gate });
  actor.takeReins();
  ok(dropped === 1, 'the gate is dropped when the reins are taken');
  frames(actor, 4, { throttle: 1, steer: 0 });
  actor.handBack();
  actor.update(1 / 30, { drawn: false });
  ok(actor.mode === 'returning' && rejoined === 1, 'a held crossing keeps it from rejoining there');
  actor.update(1 / 30, { drawn: false });
  ok(actor.mode === 'route', 'then it rejoins');
  // The real keeper: rejoin inside a cluster another team holds is refused, outside allowed.
  const rowA = { id: 'a', root_ahead_of_rear_axle_m: 1, envelope_local_xz_m: [-1, -2, 1, 4] };
  const rowB = { id: 'b', root_ahead_of_rear_axle_m: 1, envelope_local_xz_m: [-1, -2, 1, 4] };
  const ra = circleRoute({ center_enu_m: [0, 0], radius_m: 20 }), rb = circleRoute({ center_enu_m: [30, 0], radius_m: 20 });
  const keeper = createCrossings([{ id: 'a', row: rowA, route: ra }, { id: 'b', row: rowB, route: rb }]);
  const ga = keeper.gateFor('a'), gb = keeper.gateFor('b');
  const cluster = keeper.state.get('b').clusters[0];
  ok(!!cluster, 'the two circles cross');
  gb.allow(cluster.start + .1, .01); // b inside its cluster: it holds it
  const ca = keeper.state.get('a').clusters[0];
  ok(ga.rejoin(ca.start + .5) === false && ga.waitingFor === 'b', 'rejoin inside a held cluster waits');
  ok(ga.rejoin(ca.end + 5) === true, 'rejoin clear of it goes');
}

{
  // Team-vs-team in town-transport: the driven team is an obstruction to the others, and they to it.
  const row = (id, center, phase) => ({ id, name: id, scene: 't', route: { center_enu_m: center, radius_m: 20, phase_rad: phase },
    speed_m_s: 1.3, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.5, .6], envelope_local_xz_m: [-1, -2, 1, 4] });
  const rows = [row('a', [0, 0], 0), row('b', [0, 0], 0.6)]; // b 12 m ahead of a, same circle
  const town = createTownTransport({ rows, sceneId: 't', heightAt: () => 2, clear: () => true,
    async makeAssembly() { return { root: {}, pose() {}, advance() {}, stop() {}, visible() {}, dispose() {} }; } });
  await town.ready();
  const a = town.actorById('a'), b = town.actorById('b');
  ok(a && b && town.actorById('nobody') === null, 'actorById');
  // b takes the reins and stops on the road; a runs into it and waits, then goes on when b leaves.
  b.takeReins();
  const camera = { x: 0, z: 0 };
  for (let i = 0; i < 30 * 20; i++) town.update(1 / 30, camera);
  ok(a.state === 'stopped' && a.reason === 'obstruction', 'a route team waits behind a driven one');
  const gap = Math.hypot(a.pose.e - b.pose.e, a.pose.n - b.pose.n);
  ok(!overlaps(footprintOfPose(a.pose, [-1, -2, 1, 4]), footprintOfPose(b.pose, [-1, -2, 1, 4])), `and does not run into it (${gap.toFixed(2)} m apart)`);
  // b drives straight on off the circle (tangent leaves outward); a resumes by itself.
  for (let i = 0; i < 30 * 15; i++) { b.drive({ throttle: 1, steer: 0 }); town.update(1 / 30, camera); }
  ok(a.state === 'moving', 'it goes on by itself once the driven team is out of the way');
  // And a driven team refuses to drive into a route team.
  b.handBack();
  let t = 0;
  while (b.mode !== 'route' && t < 120) { town.update(1 / 30, camera); t += 1 / 30; }
  ok(b.mode === 'route', 'b back on its round');
  const saved = town.snapshot();
  ok(saved.every(s => s.mode === 'route'), 'the scene snapshot says each mode');
  a.takeReins();
  // a is behind b on the same counter-clockwise circle (b ahead by up to a lap): hold the circle's
  // own lock and drive round at b's back until it is pulled up.
  const followCircle = -Math.atan(2 / 20) / (12 * DEG);
  let refusedByTeam = false, overlapped = false, extra = 60;
  for (let i = 0; i < 30 * 90 && extra > 0; i++) {
    a.drive({ throttle: 1, steer: followCircle }); b.stop('test');
    town.update(1 / 30, camera);
    refusedByTeam ||= a.blocked === 'another team';
    if (refusedByTeam) extra--; // keep pushing on the reins a while after it is pulled up
    overlapped ||= overlaps(footprintOfPose(a.pose, [-1, -2, 1, 4]), footprintOfPose(b.pose, [-1, -2, 1, 4]));
  }
  ok(refusedByTeam, 'driving into another team pulls up with "another team"');
  ok(!overlapped, 'the driven team never overlaps another, however it is pushed');
  near(a.speed_m_s, 0, 1e-12, 'it stands behind it');
  town.dispose();
}

{
  // Every driven team in every year (loops.json), on an open plane: taken, driven off its road on a
  // turn, handed back, and back on its round in bounded time, its seat on the cushion.
  const config = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));
  for (const row of config.rows) {
    const assembly = { pose() {}, advance() {}, stop() {} };
    const actor = createTransportLoop({ ...row, route: routeFor(row.route), assembly, heightAt: () => 0 });
    const seat = actor.seat();
    ok(seat && Number.isFinite(seat.e + seat.n + seat.y), `${row.id}: a seat`);
    actor.takeReins();
    frames(actor, 25, t => ({ throttle: 1, steer: t < 8 ? .8 : 0 }));
    const off = routeDistanceNear(routeFor(row.route), ...actor.at).off_m;
    actor.handBack();
    let t = 0;
    while (actor.mode !== 'route' && t < 240) { actor.update(1 / 30); t += 1 / 30; }
    ok(actor.mode === 'route', `${row.id}: back on its round (${t.toFixed(1)} s)`);
    console.log(`  ${row.id}: ${off.toFixed(1)} m off, rejoined in ${t.toFixed(1)} s`);
    actor.dispose();
  }
}

// --- backing up --------------------------------------------------------------------------
// The test team's footprint, sampled round its envelope every quarter metre (vehicle-root local).
const ENV = [-1, -2, 1, 4];
const perimeter = (() => {
  const pts = [], [x0, z0, x1, z1] = ENV;
  for (let x = x0; x <= x1 + 1e-9; x += .25) pts.push([x, z0], [x, z1]);
  for (let z = z0; z <= z1 + 1e-9; z += .25) pts.push([x0, z], [x1, z]);
  return pts;
})();
const printOf = p => perimeter.map(([x, z]) => [p.e + Math.cos(p.yaw) * x + Math.sin(p.yaw) * z, p.n + Math.sin(p.yaw) * x - Math.cos(p.yaw) * z]);
/** A wall: an axis-aligned box [w, s, e, n] the team's footprint may not enter. */
const wallClear = box => (from, to) => printOf(to).every(([e, n]) => !(e > box[0] && e < box[2] && n > box[1] && n < box[3]));
const inBox = (p, box) => printOf(p).some(([e, n]) => e > box[0] && e < box[2] && n > box[1] && n < box[3]);

{
  // pure: backing eases to at most .4 m/s, and comes to a stand when let go.
  let c = { speed: 0, steering: 0 };
  for (let i = 0; i < 200; i++) c = easeReverse(c, { throttle: -1, steer: 0 }, limits, .05);
  near(c.speed, -.4, 1e-12, 'backing is capped at .4 m/s');
  c = easeReverse(c, { throttle: 0, steer: 0 }, limits, .05);
  ok(c.speed > -.4 && c.speed < 0, 'let go, it eases to a stand');
  for (let i = 0; i < 20; i++) c = easeReverse(c, { throttle: 1, steer: 0 }, limits, .05);
  near(c.speed, 0, 0, 'walked on, backing stops (never forward from here)');
  // the bicycle model backs along its own heading, and backing on right lock swings the nose left.
  const b = bicycleStep(sampleOf(0, 0, 0, 0), -10 * DEG, -1, 2);
  ok(b.n > 0 && b.yaw > 0, 'backing on right lock: back along the heading, nose swings left (yaw up)');
}

{
  // Driven nose-first into a wall (north of it), the team can back out a few steps.
  const wall = [10, 12, 30, 13];
  const { actor, poses, advances } = setup({ clear: wallClear(wall), why: () => 'a wall' });
  actor.takeReins();
  frames(actor, 15, { throttle: 1, steer: 0 });
  ok(actor.blocked === 'a wall', `walked into the wall (${actor.blocked})`);
  const at = actor.at, rotation = actor.snapshot().wheel_rotation_rad, total = actor.snapshot().total_distance_m;
  frames(actor, 2, { throttle: 1, steer: 0 });
  assert.deepEqual(actor.at, at, 'pushing on into the wall goes nowhere'); count++;
  // A short pull is whoa, not back: it stands for about .4 s first.
  frames(actor, .3, { throttle: -1, steer: 0 });
  assert.deepEqual(actor.at, at, 'a short pull only stands it'); count++;
  ok(!actor.reversing, 'not yet backing');
  let topBack = 0, n0 = actor.pose.n, yaw0 = actor.pose.yaw;
  for (let i = 0; i < 30 * 6; i++) { actor.drive({ throttle: -1, steer: 0 }); actor.update(1 / 30); topBack = Math.max(topBack, actor.speed_m_s); }
  ok(actor.reversing, 'held pulled, it backs');
  ok(actor.pose.n < n0 - 1.5, `it backed away from the wall (${(n0 - actor.pose.n).toFixed(2)} m)`);
  near(topBack, .4, 1e-9, 'never faster than .4 m/s backing');
  ok(actor.speed_m_s >= 0, 'speed_m_s reads a pace, never negative');
  near(angle(actor.pose.yaw - yaw0), 0, 1e-6, 'straight back keeps its heading');
  ok(actor.snapshot().total_distance_m > total + 1.5, 'the travelled total counts the backed metres');
  const rolled = actor.snapshot().wheel_rotation_rad;
  frames(actor, .5, { throttle: -1, steer: 0 });
  // .2 m back: each wheel turns back by .2 m over its own radius.
  actor.snapshot().wheel_rotation_rad.forEach((r, i) => near(angle(r - rolled[i]), -.4 * .5 / [.7, .7, .5, .5][i], 2e-3, `wheel ${i} turns backwards by its arc`));
  ok(rotation.length === 4, 'four wheels');
  ok(advances.some(a => a.ds < 0) && advances.every(a => Number.isFinite(a.ds) && a.dt > 0), 'the gait is advanced by the signed metres');
  ok(poses.every(p => Number.isFinite(p.e + p.n + p.yaw + p.height + p.totalDistance) && p.wheelRotation.every(Number.isFinite)), 'no NaN in any pose');
  ok(poses.some(p => p.reversing === true), 'the pose says it is backing');
  // Backing on the right lock swings the nose left (counter-clockwise).
  const yawBack = actor.pose.yaw;
  frames(actor, 3, { throttle: -1, steer: 1 });
  ok(angle(actor.pose.yaw - yawBack) > 3 * DEG, 'backing on right lock swings the nose left');
  // Let go: it comes to a stand at once and stops backing.
  frames(actor, .5, { throttle: 0, steer: 0 });
  near(actor.speed_m_s, 0, 0, 'let go, the backing stops');
  ok(!actor.reversing, 'and it is no longer backing');
  // Then it walks on, turned away from the wall, and clear of it.
  const away = actor.at;
  frames(actor, 6, { throttle: 1, steer: -1 });
  ok(Math.hypot(actor.at[0] - away[0], actor.at[1] - away[1]) > 2, 'it walks on away from the wall');
  ok(poses.every(p => !inBox(p, wall)), 'and never once stood in the wall');
  // Walking on while backing stops the backing too (it stands before going forward).
  frames(actor, 1, { throttle: -1, steer: 0 }); frames(actor, 2, { throttle: -1, steer: 0 });
  ok(actor.reversing, 'backing again');
  actor.drive({ throttle: 1, steer: 0 }); actor.update(1 / 30);
  ok(actor.reversing && actor.speed_m_s < .4, 'walk on: it first eases out of the backing');
  frames(actor, 1, { throttle: 1, steer: 0 });
  ok(!actor.reversing, 'then the backing has stopped');
}

{
  // Backing has the same refusals: a wall behind pulls it up with the word, never a throw.
  const behind = [10, -30, 30, -1.6];
  const { actor } = setup({ clear: wallClear(behind), why: () => 'a wall' });
  actor.takeReins();
  const at = actor.at;
  assert.doesNotThrow(() => frames(actor, 10, { throttle: -1, steer: 0 })); count++;
  ok(actor.blocked === 'a wall', `backing into a wall is refused (${actor.blocked})`);
  near(actor.speed_m_s, 0, 0);
  ok(!inBox(actor.pose, behind) && actor.pose.n <= at[1], 'it backed up to the wall and no further');
}

// --- returning recovers from a nose-first wall ----------------------------------------------
{
  // An open plane with one wall across the way the team was driven. Handed back nose-first at
  // it, the driver wants full left lock and cannot go forward; he backs off and works round it.
  const wall = [18.5, 12, 30, 13];
  const { actor, poses } = setup({ clear: wallClear(wall), why: () => 'a wall' });
  actor.takeReins();
  frames(actor, 15, { throttle: 1, steer: 0 });
  ok(actor.blocked === 'a wall', 'nose-first at the wall');
  ok(actor.handBack(), 'hands back');
  let t = 0, backed = 0, episodes = 0, was = false;
  while (actor.mode !== 'route' && t < 240) {
    actor.update(1 / 30); t += 1 / 30;
    if (actor.reversing && !was) episodes++;
    was = actor.reversing; if (was) backed++;
  }
  ok(actor.mode === 'route', `returning recovers and rejoins its round (${t.toFixed(1)} s, ${episodes} back-ups)`);
  ok(episodes >= 1 && episodes <= 6, 'it backed off the wall, a bounded number of times');
  ok(poses.every(p => !inBox(p, wall)), 'never in the wall');
  // And it goes on round from there.
  const total = actor.snapshot().total_distance_m;
  frames(actor, 60);
  near(actor.snapshot().total_distance_m - total, 60 * 1.3, 1e-6, 'its round runs on, unrefused');
  console.log(`  nose-first wall: rejoined in ${t.toFixed(1)} s after ${episodes} back-up(s)`);
}
{
  // Everything refused (boxed in): bounded tries, then it waits where it stands, no throw;
  // the snap-when-not-drawn still puts it back once the road is clear.
  let boxed = false;
  const { actor } = setup({ clear: (from, to) => !boxed || Math.hypot(to.e - from.e, to.n - from.n) < 1e-12, why: () => 'a wall' });
  actor.takeReins();
  frames(actor, 4, { throttle: 1, steer: 0 });
  boxed = true;
  actor.handBack();
  const at = actor.at;
  let episodes = 0, was = false;
  assert.doesNotThrow(() => { for (let i = 0; i < 30 * 40; i++) { actor.update(1 / 30); if (actor.reversing && !was) episodes++; was = actor.reversing; } }); count++;
  ok(episodes === 6, `it tries six back-ups and no more (${episodes})`);
  ok(actor.mode === 'returning' && actor.blocked === 'a wall', 'then it waits, saying why');
  assert.deepEqual(actor.at, at); count++;
  boxed = false;
  actor.update(1 / 30, { drawn: false });
  ok(actor.mode === 'route', 'out of sight it is put back on its round');
}
{
  // A person in the way is waited for, never backed away from.
  let person = false;
  const { actor } = setup({ clear: (from, to) => !person || Math.hypot(to.e - from.e, to.n - from.n) < 1e-12, why: () => 'someone in the way' });
  actor.takeReins();
  frames(actor, 4, { throttle: 1, steer: 0 });
  person = true; actor.handBack();
  let backs = false;
  for (let i = 0; i < 30 * 10; i++) { actor.update(1 / 30); backs ||= actor.reversing; }
  ok(!backs && actor.blocked === 'someone in the way', 'a person in the way: the driver waits');
}

// --- the kerb ------------------------------------------------------------------------------
const teamRow = { wheelbase_m: 2, root_ahead_of_rear_axle_m: 1, track_m: 1.2, team_half_spacing_m: .65, horse_offset_m: [0, 0, 3.1] };
{
  // A fake north-south carriageway, 12 m kerb to kerb, the team in it going north at e = 20.
  const street = [[14, -60], [26, -60], [26, 60], [14, 60]];
  const reader = createCarriagewayReader([{ id: 'fake', polygon_local_m: street }]);
  const inside = ([e, n]) => e > 14 && e < 26 && n > -60 && n < 60;
  const { actor, poses } = setup({ road: pose => reader(teamRow, pose) });
  // On its own round's start it is on the road; a steady right turn walks it to the east kerb.
  actor.takeReins();
  assert.doesNotThrow(() => frames(actor, 30, { throttle: 1, steer: 1 })); count++;
  ok(actor.blocked === 'the kerb', `a hoof or wheel at the kerb is refused as the kerb (${actor.blocked})`);
  near(actor.speed_m_s, 0, 0, 'it pulls up there');
  const points = poses.flatMap(p => { const g = teamGroundPoints(teamRow, p); return [...g.wheels, ...g.hooves]; });
  ok(points.every(inside), 'no wheel or hoof ever left the carriageway');
  ok(points.some(([e]) => e > 25), 'it was turned right up to the kerb');
  // Swinging the team toward the kerb where it stands is refused too; away from it is not.
  const steer0 = actor.pose.steering;
  frames(actor, 1, { throttle: 0, steer: 1 });
  ok(poses.every(p => teamGroundPoints(teamRow, p).hooves.every(inside)), 'the team is never swung up the kerb');
  frames(actor, 2, { throttle: 0, steer: -1 });
  ok(actor.pose.steering > steer0, 'it can be turned away from the kerb');
  // Backing works within the carriageway too.
  frames(actor, 4, { throttle: -1, steer: 0 });
  ok(actor.reversing, 'and backed off it');
  // An unread carriageway (null) keeps today's rules.
  const { actor: unread } = setup({ road: () => null });
  unread.takeReins();
  frames(unread, 30, { throttle: 1, steer: 1 });
  ok(unread.blocked === null && unread.speed_m_s > 1, 'an unread carriageway refuses nothing');
  // A hoof is what leaves first: a road wide enough for the wheels' room but not the team's.
  const narrow = createCarriagewayReader([{ polygon_local_m: [[18.5, -60], [21.5, -60], [21.5, 60], [18.5, 60]] }]);
  const hoofOnly = { e: 20, n: 1, yaw: 0, steering: 0 };
  ok(narrow({ ...teamRow, horse_offset_m: undefined, team_half_spacing_m: undefined }, hoofOnly), 'the wheels alone fit');
  ok(!narrow({ ...teamRow, team_half_spacing_m: 1.2 }, hoofOnly), 'a hoof over the kerb refuses');
  ok(narrow(teamRow, hoofOnly), 'and the team fits');
  ok(!narrow(teamRow, { ...hoofOnly, steering: -15 * DEG }), 'a team swung on full lock puts a hoof over it');
  near(KERB_ROOM_M.wheel, .2); near(KERB_ROOM_M.hoof, .15);
}
{
  // The real 1904 carriageways (data/street_grid/1904.json): every 1904 road, posed at 5 cm
  // steps as transport-loop.js poses it, is on them (the round a team returns to is never
  // refused); a steady right turn off Hans's lane is refused as the kerb before a hoof leaves.
  const grid = JSON.parse(readFileSync(new URL('../data/street_grid/1904.json', import.meta.url)));
  const config = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));
  const reader = createCarriagewayReader(grid.carriageways);
  const roads = config.rows.filter(r => r.scene === '1904');
  // Hans's, the two more (T-3555) and the Glessner brougham on call (T-3557).
  ok(roads.length === 4, 'four 1904 teams');
  const onRoadStrict = createCarriagewayReader(grid.carriageways, { wheel_room_m: 0, hoof_room_m: 0 });
  for (const row of roads) {
    const r = routeFor(row.route);
    const preview = createTransportLoop({ ...row, route: r, assembly: { pose() {} }, heightAt: () => 0 });
    let refused = 0;
    for (let s = 0; s < r.length; s += .05) if (!reader(row, preview.previewAt(s))) refused++;
    ok(refused === 0, `${row.id}: its own road is never refused by the kerb rule (${refused})`);
    preview.dispose();
    const poses = [];
    const actor = createTransportLoop({ ...row, route: r, assembly: { pose(p) { poses.push(p); }, advance() {}, stop() {} },
      heightAt: () => 0, road: pose => reader(row, pose) });
    actor.takeReins();
    assert.doesNotThrow(() => frames(actor, 40, { throttle: 1, steer: 1 })); count++;
    ok(actor.blocked === 'the kerb', `${row.id}: a steady right turn is refused at the kerb (${actor.blocked})`);
    ok(poses.every(p => onRoadStrict(row, p)), `${row.id}: no wheel or hoof ever left the carriageway`);
    actor.handBack();
    let t = 0;
    while (actor.mode !== 'route' && t < 240) { actor.update(1 / 30); t += 1 / 30; }
    ok(actor.mode === 'route', `${row.id}: handed back from the kerb, it rejoins its round (${t.toFixed(1)} s)`);
    ok(poses.every(p => onRoadStrict(row, p)), `${row.id}: and never left the carriageway on the way`);
    console.log(`  ${row.id}: kerb refused the turn; back on its round in ${t.toFixed(1)} s`);
  }
}
{
  // town-transport passes its carriageway reader to each team, with the team's own row.
  const seen = [];
  const row = { id: 'k', name: 'k', scene: 't', route: { center_enu_m: [0, 0], radius_m: 20 }, speed_m_s: 1.3, wheelbase_m: 2,
    track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12, wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.5, .6] };
  const town = createTownTransport({ rows: [row], sceneId: 't', heightAt: () => 2, clear: () => true,
    carriageway: (r, pose) => { seen.push(r.id); return pose.e < 21.5; },
    async makeAssembly() { return { root: {}, pose() {}, advance() {}, stop() {}, visible() {}, dispose() {} }; } });
  await town.ready();
  const k = town.actorById('k');
  k.takeReins();
  for (let i = 0; i < 30 * 20; i++) { k.drive({ throttle: 1, steer: 1 }); town.update(1 / 30, { x: 0, z: 0 }); }
  ok(seen.length > 0 && seen.every(id => id === 'k'), 'the reader is asked with the team\'s own row');
  ok(k.blocked === 'the kerb', `town-transport: the kerb (${k.blocked})`);
  town.dispose();
}

// A slow page (a 3 fps phone, a hitch): the input given before a long frame still drives it.
{
  const { actor } = setup();
  actor.stop('boarding'); actor.takeReins();
  const d0 = actor.snapshot().total_distance_m;
  for (let i = 0; i < 20; i++) { actor.drive({ throttle: 1, steer: 0 }); actor.update(0.4); }
  ok(actor.snapshot().total_distance_m - d0 > 2, 'frames of 0.4 s still walk the team on');
  ok(actor.speed_m_s > 0.5, 'and it keeps its pace on a slow page');
  actor.dispose();
}

console.log(`T-3557 team drive: reins, steering, speed cap, refusals (wall, ground, kerb, support), backing, hand back (with backing off a wall), the carriageway kerb, save, gate, team-vs-team: ${count} checks PASS`);
