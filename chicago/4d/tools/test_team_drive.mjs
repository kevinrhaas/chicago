// SPDX-License-Identifier: GPL-3.0-or-later
// T-3557: taking the reins of a driven team. Plain node, no deps: a loop with a fake assembly on a
// flat plane is taken, driven, steered, refused, handed back and saved, and the pure drive math
// (team-drive.js) is checked on its own.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { circleRoute, createTransportLoop, routeDistanceNear, routeFor } from '../renderers/web/js/transport-loop.js';
import { driveLimits, easeControls, bicycleStep, sampleOf, pursuitSteering, refineRouteDistance,
  wheelArcRatios, footprintOfPose } from '../renderers/web/js/team-drive.js';
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
function setup({ clear = () => true, heightAt = () => 2, why = null, gate = null, row = {} } = {}) {
  const poses = [], advances = [];
  const assembly = { pose(p) { poses.push(p); }, advance(dt, ds) { advances.push({ dt, ds }); }, stop() {}, visible() {}, dispose() {} };
  const actor = createTransportLoop({ id: 'test', name: 'Driver', route, assembly,
    speed_m_s: 1.3, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [.3, 1.58, .65], heightAt, clear, why, gate, ...row });
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

console.log(`T-3557 team drive: reins, steering, speed cap, refusals (wall, ground, kerb, support), hand back, save, gate, team-vs-team: ${count} checks PASS`);
