// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { circleRoute, roundedBlockRoute, createTransportLoop, preflightTransportRoute, preflightTransportRouteAsync } from '../renderers/web/js/transport-loop.js';

let count = 0;
const near = (actual, expected, epsilon = 1e-9) => { assert(Math.abs(actual - expected) <= epsilon, `${actual} != ${expected}`); count++; };
const route = circleRoute({ center_enu_m: [100, 200], radius_m: 10 });
for (const s of [0, 1, 10, 30, route.length, route.length * 11 + 3]) {
  const p = route.at(s);
  near(Math.hypot(p.e - 100, p.n - 200), 10);
  // A tangent is perpendicular to the radius and has unit speed.
  near((p.e - 100) * p.forwardE + (p.n - 200) * p.forwardN, 0);
  near(Math.hypot(p.forwardE, p.forwardN), 1);
}
near(route.at(0).e, route.at(route.length).e);
near(route.at(0).n, route.at(route.length).n);
near(route.at(0).yaw, route.at(route.length).yaw);
const clockwise = circleRoute({ center_enu_m: [100, 200], radius_m: 10, clockwise: true });
near(clockwise.at(0).forwardN, -route.at(0).forwardN);
assert.throws(() => circleRoute({ center_enu_m: [0, NaN], radius_m: 10 })); count++;
assert.throws(() => circleRoute({ center_enu_m: [0, 0], radius_m: 1 })); count++;

function setup({ clear = () => true, heightAt = () => 2, chosenRoute = route } = {}) {
  const poses = [], advances = [], events = [];
  const assembly = { pose(p) { poses.push(p); }, advance(dt, ds) { advances.push({ dt, ds }); },
    visible(v) { events.push(['visible', v]); }, stop() { events.push(['stop']); }, dispose() { events.push(['dispose']); } };
  const actor = createTransportLoop({ id: 'test', name: 'Driver', route: chosenRoute, assembly,
    speed_m_s: 1, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.58, .65], heightAt, clear });
  return { actor, poses, advances, events };
}
const a = setup();
a.actor.update(.1);
near(a.actor.snapshot().total_distance_m, .1);
assert(a.advances.every(p => p.dt <= .05)); count++;
near(a.poses.at(-1).height, 2);
near(a.actor.snapshot().steering_rad, Math.atan(2 / 10));
// The left wheels trace the inner circles; exact arc distance, independent of frame count.
near(a.actor.snapshot().wheel_rotation_rad[0], .1 * 9.4 / 10 / .7);
near(a.actor.snapshot().wheel_rotation_rad[1], .1 * 10.6 / 10 / .7);
near(a.actor.snapshot().wheel_rotation_rad[2], .1 * (Math.hypot(10, 2) - .6) / 10 / .5);
near(a.actor.snapshot().wheel_rotation_rad[3], .1 * (Math.hypot(10, 2) + .6) / 10 / .5);
const stopped = a.actor.snapshot();
a.actor.stop(); a.actor.update(10);
assert.deepEqual(a.actor.snapshot().wheel_rotation_rad, stopped.wheel_rotation_rad); count++;
near(a.actor.snapshot().total_distance_m, stopped.total_distance_m);
assert.equal(a.actor.state, 'stopped'); count++;
assert(a.actor.resume()); a.actor.update(.1);
near(a.actor.snapshot().total_distance_m, .2);
for (const flags of [{ paused: true }, { reducedMotion: true }, { enabled: false }]) {
  a.actor.update(20, flags); near(a.actor.snapshot().total_distance_m, .2);
}
a.actor.update(10); near(a.actor.snapshot().total_distance_m, .45); // no ten-second teleport

// Render reach must not freeze town traffic forever at its initial far-side pose.
// Offscreen travel uses the identical bounded clearance, wheels and gait updates;
// becoming drawn again neither catches up a second time nor resets a phase.
const onScreen = setup(), offScreen = setup();
for (let i = 0; i < 400; i++) {
  onScreen.actor.update(.1);
  offScreen.actor.update(.1, { drawn: false });
}
const onJourney = onScreen.actor.snapshot(), offJourney = offScreen.actor.snapshot();
assert.equal(offScreen.actor.visible, false); count++;
assert.equal(offScreen.actor.pickDriverAt(), null); count++;
assert.deepEqual(offJourney.wheel_rotation_rad, onJourney.wheel_rotation_rad); count++;
near(offJourney.total_distance_m, 40, 1e-8);
near(offJourney.distance_m, onJourney.distance_m);
assert.deepEqual(offJourney.at_enu_m, onJourney.at_enu_m); count++;
assert.deepEqual(offScreen.advances, onScreen.advances); count++;
const beforeReappear = offScreen.actor.snapshot();
const advancesBeforeReappear = offScreen.advances.length;
offScreen.actor.update(0, { drawn: true });
assert.equal(offScreen.actor.visible, true); count++;
assert.deepEqual(offScreen.actor.snapshot().wheel_rotation_rad, beforeReappear.wheel_rotation_rad); count++;
assert.equal(offScreen.advances.length, advancesBeforeReappear); count++;
near(offScreen.actor.snapshot().total_distance_m, beforeReappear.total_distance_m);
for (const flags of [{ paused: true }, { reducedMotion: true }, { enabled: false }]) {
  offScreen.actor.update(.2, { ...flags, drawn: false });
  near(offScreen.actor.snapshot().total_distance_m, beforeReappear.total_distance_m);
}
offScreen.actor.stop(); offScreen.actor.update(.2, { drawn: false });
near(offScreen.actor.snapshot().total_distance_m, beforeReappear.total_distance_m);
assert(offScreen.actor.resume()); count++;
offScreen.actor.update(.1, { drawn: false }); onScreen.actor.update(.1);
assert.deepEqual(offScreen.actor.snapshot().at_enu_m, onScreen.actor.snapshot().at_enu_m); count++;
let farBlocked = false;
const farActor = setup({ clear: () => !farBlocked });
farActor.actor.update(.1, { drawn: false }); farBlocked = true;
farActor.actor.update(.1, { drawn: false });
assert.equal(farActor.actor.state, 'stopped'); count++;
assert.equal(farActor.actor.snapshot().reason, 'obstruction'); count++;
near(farActor.actor.snapshot().total_distance_m, .1);
assert.equal(farActor.actor.resume(), false); count++;
farBlocked = false; assert(farActor.actor.resume()); count++;
farActor.actor.update(.1, { drawn: false }); near(farActor.actor.snapshot().total_distance_m, .2);
assert.throws(() => a.actor.update(-1)); count++;
assert.throws(() => a.actor.update(Infinity)); count++;

let blocked = false;
const b = setup({ clear: () => !blocked });
b.actor.update(.2); blocked = true; const before = b.actor.snapshot();
b.actor.update(.1);
assert.equal(b.actor.state, 'stopped'); count++;
assert.equal(b.actor.snapshot().reason, 'obstruction'); count++;
near(b.actor.snapshot().total_distance_m, before.total_distance_m);
assert.equal(b.actor.canResume(), false); count++;
assert.equal(b.actor.resume(), false); count++;
blocked = false; assert(b.actor.resume()); count++;
b.actor.update(.1); near(b.actor.snapshot().total_distance_m, .3);
b.actor.dispose(); b.actor.dispose();
assert.equal(b.events.filter(e => e[0] === 'dispose').length, 1); count++;
assert.equal(b.actor.resume(), false); count++;
assert.equal(b.actor.visible, false); count++;
assert.throws(() => setup({ heightAt: () => null })); count++;
assert.throws(() => setup({ heightAt: e => e > 110 ? .1 : 0 })); count++;
assert.throws(() => setup({ clear: () => false }), /initial whole-team/); count++;

// A complete loop closes continuously and the driver remains a rigid vehicle-local
// offset. It does not jump to the route centre or drift at the loop seam.
const c = setup();
let remaining = route.length;
while (remaining > 1e-9) { const dt = Math.min(.25, remaining); c.actor.update(dt); remaining -= dt; }
const seamDistance = c.actor.snapshot().distance_m;
near(Math.min(seamDistance, route.length - seamDistance), 0, 1e-8);
near(c.actor.at[0], 110, 1e-8); near(c.actor.at[1], 201.65, 1e-8);
const cw = setup({ chosenRoute: clockwise }); cw.actor.update(.1);
assert(cw.actor.snapshot().wheel_rotation_rad[0] > cw.actor.snapshot().wheel_rotation_rad[1]); count++;
const block = roundedBlockRoute({ bounds_enu_m: [-60, -100, 60, 100], corner_radius_m: 18,
  origin_enu_m: [1000, -2000], rotation_rad: .011 });
const blockStart = block.at(0), blockEnd = block.at(block.length);
near(blockStart.e, blockEnd.e); near(blockStart.n, blockEnd.n);
near(blockStart.forwardE, blockEnd.forwardE); near(blockStart.forwardN, blockEnd.forwardN);
for (let s = 0; s <= block.length; s += .5) {
  const p = block.at(s), q = block.at(s + .0001);
  near(Math.hypot(p.forwardE, p.forwardN), 1);
  assert(Math.hypot(q.e - p.e, q.n - p.n) < .000101); count++;
  assert(Math.abs(p.curvature) <= block.maxCurvature + 1e-12); count++;
}
assert.throws(() => createTransportLoop({ id: 'too-sharp', name: 'test', route,
  assembly: { pose() {} }, speed_m_s: 1, wheelbase_m: 2.35, track_m: 1.21,
  root_ahead_of_rear_axle_m: 1.175, driver_local_m: [0, 1.58, .65],
  wheel_radii_m: [.685, .685, .535, .535], heightAt: () => 0, steering_limit_deg: 8 }), /steering limit/); count++;
const preflightRow = { id: 'preflight', name: 'route', speed_m_s: 1, wheelbase_m: 2,
  track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
  driver_local_m: [0, 1.58, .65], wheel_radii_m: [.7, .7, .5, .5] };
let obstructedPoseCalls = 0;
assert.throws(() => createTransportLoop({ ...preflightRow, route, heightAt: () => 0,
  clear: () => false, assembly: { pose() { obstructedPoseCalls++; } } }), /initial whole-team/);
assert.equal(obstructedPoseCalls, 0); count++;
const whole = preflightTransportRoute({ row: preflightRow, route, heightAt: () => 0, clear: () => true });
assert(whole.samples > 250 && whole.maximum_spacing_m <= .25); count++;
assert.throws(() => preflightTransportRoute({ row: preflightRow, route, heightAt: () => 0,
  clear: (a, b) => b.n < 209.9 }), /circuit obstruction/); count++;
assert.throws(() => preflightTransportRoute({ row: preflightRow, route,
  heightAt: (e, n) => n > 209.9 ? null : 0, clear: () => true }), /no rendered ground/); count++;

// Chunk size affects scheduling only: retain every route/ground/support reading,
// the initial yield, per-sample cancellation and all original physical failures.
const asyncRoute = circleRoute({ center_enu_m: [-367.5, -557.5], radius_m: 18 });
async function asynchronousReading(yieldEvery, { cancelAt = null, blockedAt = null } = {}) {
  const reads = [], supports = [], boundaries = [];
  let cancelled = false;
  const configuration = { row: preflightRow, route: asyncRoute,
    heightAt(e, n) { reads.push([e, n]); return 1.31; },
    clear() { return blockedAt === null || supports.length < blockedAt; },
    support(pose) { supports.push([pose.e, pose.n, pose.yaw]); if (supports.length === cancelAt) cancelled = true; } };
  const reading = preflightTransportRouteAsync(configuration, { yieldEvery,
    yieldControl() { boundaries.push(supports.length); return Promise.resolve(); }, cancelled: () => cancelled });
  assert.equal(reads.length, 0, 'initial yield must precede even the first ground read'); count++;
  assert.equal(supports.length, 0); count++;
  return { value: await reading, reads, supports, boundaries };
}
const async32 = await asynchronousReading(32), async128 = await asynchronousReading(128);
assert.deepEqual(async128.value, async32.value); count++;
assert.deepEqual(async128.reads, async32.reads); count++;
assert.deepEqual(async128.supports, async32.supports); count++;
assert.equal(async128.value.samples, 454); count++;
assert.equal(async32.boundaries.length, 15); count++;
assert.deepEqual(async128.boundaries, [0, 128, 256, 384]); count++;
for (const chunk of [32, 128]) {
  const cancelled = await asynchronousReading(chunk, { cancelAt: 13 });
  assert.equal(cancelled.value.status, 'CANCELED_ROUTE_READING_NOT_PASS'); count++;
  assert.equal(cancelled.supports.length, 13, 'cancellation is per sample, not per chunk'); count++;
  await assert.rejects(asynchronousReading(chunk, { blockedAt: 13 }), /circuit obstruction/); count++;
  await assert.rejects(preflightTransportRouteAsync({ row: preflightRow, route: asyncRoute,
    heightAt: () => null, clear: () => true }, { yieldEvery: chunk }), /no rendered ground/); count++;
}
await assert.rejects(preflightTransportRouteAsync({}, { yieldEvery: 129 }), /bounded preflight chunk/); count++;

console.log(`transport loop: ${count} checks PASS`);
