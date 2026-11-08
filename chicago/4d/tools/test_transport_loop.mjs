// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
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


// Prioritized default continuation changes scheduling only. These are Node CPU
// count/cancellation fixtures, never a substituted field in a rendered scene.
const current1904 = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url))).rows.find(row => row.scene === '1904');
const actualBlock = roundedBlockRoute(current1904.route);
async function defaultScheduleReading({ fallback = false, cancelAt = null, cancelBefore = false, rejectYield = false } = {}) {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'scheduler');
  const originalTimer = globalThis.setTimeout, reads = [], supports = [], boundaries = [];
  let timerCalls = 0, schedulerCalls = 0;
  const scheduler = { yield() {
    assert.equal(this, scheduler); count++;
    schedulerCalls++; boundaries.push(supports.length);
    return rejectYield ? Promise.reject(new Error('native scheduler rejection')) : Promise.resolve();
  } };
  try {
    Object.defineProperty(globalThis, 'scheduler', { configurable: true, writable: true,
      value: fallback ? { yield: null } : scheduler });
    globalThis.setTimeout = (fn, delay, ...args) => {
      assert.equal(fallback, true, 'supported scheduler must avoid timer fallback'); count++;
      assert.equal(delay, 0); count++;
      timerCalls++; boundaries.push(supports.length);
      return originalTimer(fn, delay, ...args);
    };
    const reading = preflightTransportRouteAsync({ row: current1904, route: actualBlock,
      heightAt(e, n) { reads.push([e, n]); return 1.31; }, clear: () => true,
      support(pose) { supports.push([pose.e, pose.n, pose.yaw]); } },
      { yieldEvery: 128, cancelled: () => cancelBefore || (cancelAt !== null && supports.length >= cancelAt) });
    assert.equal(reads.length, 0, 'initial cooperative yield precedes terrain reads'); count++;
    const value = await reading;
    return { value, reads, supports, boundaries, timerCalls, schedulerCalls };
  } finally {
    globalThis.setTimeout = originalTimer;
    if (descriptor) Object.defineProperty(globalThis, 'scheduler', descriptor);
    else delete globalThis.scheduler;
  }
}
const prioritized = await defaultScheduleReading(), timerFallback = await defaultScheduleReading({ fallback: true });
assert.deepEqual(prioritized.value, timerFallback.value); count++;
assert.deepEqual(prioritized.reads, timerFallback.reads); count++;
assert.deepEqual(prioritized.supports, timerFallback.supports); count++;
assert.equal(prioritized.value.samples, 3163); count++;
assert.deepEqual(prioritized.boundaries, Array.from({ length: 25 }, (_, i) => i * 128)); count++;
assert.deepEqual(timerFallback.boundaries, prioritized.boundaries); count++;
assert.equal(prioritized.schedulerCalls, 25); count++;
assert.equal(prioritized.timerCalls, 0); count++;
assert.equal(timerFallback.schedulerCalls, 0); count++;
assert.equal(timerFallback.timerCalls, 25); count++;
for (const cancelAt of [13, 128]) {
  const cancelled = await defaultScheduleReading({ cancelAt });
  assert.equal(cancelled.value.status, 'CANCELED_ROUTE_READING_NOT_PASS'); count++;
  assert.equal(cancelled.supports.length, cancelAt); count++;
  assert.deepEqual(cancelled.boundaries, cancelAt === 13 ? [0] : [0, 128]); count++;
}
const beforeAnyRead = await defaultScheduleReading({ cancelBefore: true });
assert.equal(beforeAnyRead.value.status, 'CANCELED_ROUTE_READING_NOT_PASS'); count++;
assert.equal(beforeAnyRead.reads.length, 0); count++;
assert.deepEqual(beforeAnyRead.boundaries, [0]); count++;
await assert.rejects(defaultScheduleReading({ rejectYield: true }), /native scheduler rejection/); count++;

console.log(`transport loop: ${count} checks PASS`);


// Full visible elapsed admission is deliberately opt-in: the established bounded
// dt callers and their no-ten-second-teleport assertions above remain unchanged.
{
  const elapsedSetup = (speed = .084375, clear = () => true) => {
    const poses = [], advances = [];
    const row = { id: 'elapsed-clock', name: 'Clock driver', scene: 'clock',
      speed_m_s: speed, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1,
      steering_limit_deg: 12, wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.58, .65],
      route: { center_enu_m: [0, 0], radius_m: 10 } };
    const actor = createTransportLoop({ ...row, route: circleRoute(row.route), heightAt: () => 0, clear,
      assembly: { pose(p) { poses.push(p); }, advance(dt, ds) { advances.push({ dt, ds }); },
        visible() {}, stop() {}, dispose() {} } });
    const frame = (dt, flags = {}) => actor.update(dt, { elapsedFrame: true, ...flags });
    return { actor, row, frame, poses, advances };
  };
  const run = deltas => {
    const a = elapsedSetup(); a.frame(0);
    for (const delta of deltas) a.frame(delta);
    return a;
  };
  const reference = run(Array(60).fill(1 / 60));
  for (const deltas of [Array(4).fill(.25), [.5, .5], [1], [.1, .55, .35]]) {
    const a = run(deltas), actual = a.actor.snapshot(), expected = reference.actor.snapshot();
    near(actual.total_distance_m, .084375);
    near(actual.distance_m, expected.distance_m);
    actual.wheel_rotation_rad.forEach((value, i) => near(value, expected.wheel_rotation_rad[i]));
    near(a.advances.reduce((sum, step) => sum + step.dt, 0), 1);
    assert(a.advances.every(step => step.dt <= .05 && step.ds <= .05 * .084375));
    assert.equal(a.poses.length, a.advances.length + 1, 'One pose per accepted swept step; no extra external travel');
    a.actor.dispose();
  }
  reference.actor.dispose();
  const atHalfFps = run([2]); near(atHalfFps.actor.snapshot().total_distance_m, .16875);
  const slow = run([10]); near(slow.actor.snapshot().total_distance_m, .25);
  assert(slow.advances.every(step => step.dt <= .05));
  const highSpeed = elapsedSetup(1); highSpeed.frame(0); highSpeed.frame(10);
  near(highSpeed.actor.snapshot().total_distance_m, .25, 1e-9);
  const legacy = elapsedSetup(1); legacy.actor.update(10);
  near(legacy.actor.snapshot().total_distance_m, .25); // exact original legacy intent
  for (const a of [atHalfFps, slow, highSpeed, legacy]) a.actor.dispose();

  for (const flag of [{ paused: true }, { enabled: false }, { reducedMotion: true }]) {
    const a = run([.5]), before = a.actor.snapshot();
    a.frame(30, flag); a.frame(30);
    near(a.actor.snapshot().total_distance_m, before.total_distance_m);
    assert.deepEqual(a.actor.snapshot().wheel_rotation_rad, before.wheel_rotation_rad);
    a.frame(.5); near(a.actor.snapshot().total_distance_m, before.total_distance_m + .0421875);
    a.actor.dispose();
  }
  for (const stoppedTick of [false, true]) {
    const a = run([.5]), before = a.actor.snapshot();
    a.actor.stop(); if (stoppedTick) a.frame(30);
    assert(a.actor.resume());
    // This models Continue running before transport.update in the same tick:
    // none of that tick's pre-action interval belongs to the resumed journey.
    a.frame(30); near(a.actor.snapshot().total_distance_m, before.total_distance_m);
    a.frame(.5); near(a.actor.snapshot().total_distance_m, before.total_distance_m + .0421875);
    a.actor.dispose();
  }
  const fresh = elapsedSetup();
  fresh.frame(0, { motionFrame: false }); fresh.frame(30);
  near(fresh.actor.snapshot().total_distance_m, 0, 1e-12);
  fresh.frame(.5); near(fresh.actor.snapshot().total_distance_m, .0421875);
  fresh.actor.stop(); assert(fresh.actor.resume());
  fresh.frame(0, { motionFrame: false }); fresh.frame(30);
  near(fresh.actor.snapshot().total_distance_m, .0421875, 1e-12);
  fresh.frame(.5); near(fresh.actor.snapshot().total_distance_m, .084375);
  fresh.actor.dispose();

  const reach = run([.5]); reach.frame(.5, { drawn: false });
  near(reach.actor.snapshot().total_distance_m, .084375, 1e-12);
  // An offscreen journey continues. Its first drawn frame rejects an interval
  // spanning the range boundary; a synthetic visibility replay cannot prime it.
  reach.frame(0, { drawn: true, motionFrame: false }); reach.frame(30);
  near(reach.actor.snapshot().total_distance_m, .084375, 1e-12);
  reach.frame(.5); near(reach.actor.snapshot().total_distance_m, .1265625);
  reach.actor.dispose();

  let obstruction = true;
  const blocked = elapsedSetup(1, (_from, to) => !obstruction || to.distance <= .12);
  blocked.frame(0); blocked.frame(10);
  near(blocked.actor.snapshot().total_distance_m, .1);
  assert.equal(blocked.actor.snapshot().reason, 'obstruction');
  near(blocked.advances.reduce((sum, step) => sum + step.ds, 0), .1);
  const wheelReference = elapsedSetup(1); wheelReference.actor.update(.1);
  assert.deepEqual(blocked.actor.snapshot().wheel_rotation_rad, wheelReference.actor.snapshot().wheel_rotation_rad);
  assert.equal(blocked.actor.resume(), false);
  obstruction = false; assert(blocked.actor.resume()); blocked.frame(10);
  near(blocked.actor.snapshot().total_distance_m, .1);
  blocked.frame(10); near(blocked.actor.snapshot().total_distance_m, .35);
  blocked.actor.dispose(); wheelReference.actor.dispose();

  // Exercise actual town admission and its synthetic lastUpdate replay, with
  // adapters only: no GPU, GLBs, browser, head/body asset or copied town logic.
  const { createTownTransport } = await import('../renderers/web/js/town-transport.js');
  const seed = elapsedSetup(); const row = seed.row; seed.actor.dispose();
  const visualCalls = [], movement = [];
  const town = createTownTransport({ rows: [row], sceneId: 'clock', heightAt: () => 0,
    clear: () => true, makeAssembly: async () => ({ root: {}, pose() {},
      advance(dt, ds) { movement.push({dt, ds}); }, visible() {}, stop() {}, dispose() {},
      updateVisual(dt) { visualCalls.push(dt); } }) });
  const camera = { x: 10, z: 0 };
  town.update(0, camera, { elapsedFrame: true, visualDt: 0 });
  await town.ready(); // replays lastUpdate with motionFrame:false
  town.update(30, camera, { elapsedFrame: true, visualDt: 30 });
  near(town.snapshot()[0].total_distance_m, 0);
  const beforeVisual = visualCalls.length;
  town.update(.5, camera, { elapsedFrame: true, visualDt: .5 });
  near(town.snapshot()[0].total_distance_m, .0421875);
  assert.equal(visualCalls.length, beforeVisual + 1, 'Driver visual clock receives one call, never each swept substep');
  assert.equal(visualCalls.at(-1), .5);
  assert(movement.length > 1);
  const actor = town.actors[0]; actor.stop(); const stoppedDistance = town.snapshot()[0].total_distance_m;
  town.update(.5, camera, { elapsedFrame: true, visualDt: .5 });
  near(town.snapshot()[0].total_distance_m, stoppedDistance);
  assert.equal(visualCalls.at(-1), .5, 'Independent seated looking still advances while stopped');
  town.dispose();
  console.log('elapsed transport: same configured low-FPS pace, .25m ceiling, swept obstruction, transition/range/admission reset and independent visual clock PASS');
}


// Execute main's actual new event bindings, clock and town forwarding: a pair
// of preference/hide events without any held tick must still discard old time.
{
  const main = readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  const required = (match, name) => { assert(match, `native ${name} missing`); return match[0]; };
  const clockBody = required(main.match(/function tick\([^\n]*\) \{([\s\S]*?)\n    if \(!gateOpen\)/), 'tick clock')
    .replace(/^function tick[^\n]*\{\n/, '').replace(/\n    if \(!gateOpen\)$/, '');
  const latch = required(main.match(/  let visualClockReset = true;\n  const resetVisualClock = [^\n]+/), 'visible latch');
  const media = required(main.match(/  const transportReducedMotion = window.matchMedia\([^\n]+\n  transportReducedMotion.addEventListener\([^\n]+/), 'motion preference binding');
  const forwarding = required(main.match(/api\.townTransport\?\.update\(visualDt, camera.position, \{[\s\S]*?\n    \}\);/), 'elapsed town forwarding');
  const hide = required(main.match(/onHideLevel: \(level, hide\) => \{[^}]*\},/), 'confidence hide callback')
    .replace(/^onHideLevel: \(level, hide\) => \{/, '').replace(/\s*\},$/, '');
  const listeners = [], calls = [], eye = {};
  const motion = { matches: false, addEventListener(name, fn) { assert.equal(name, 'change'); listeners.push(fn); } };
  const clock = { delta: 0, reads: 0, getDelta() { this.reads++; return this.delta; } };
  const confidence = { hidden: { reconstructed: false }, setHidden(level, value) { this.hidden[level] = !!value; } };
  // T-3439: Settings › Show › Carriages and horses hides the teams the way the Confidence view does.
  const shownLayers = { people: true, vehicles: true };
  const world = { sunTime: '12:30' }; // T-3497: the sun clock the teams' hours are read on
  const native = new Function('clock', 'document', 'window', 'api', 'camera', 'confidence', 'gateFrame', 'shownLayers', 'world', `
    let animationHold = false, gateOpen = false;
    ${latch}\n${media}
    return {tick() { ${clockBody}\n${forwarding} }, hide(level, hide) { ${hide} }};
  `)(clock, { hidden: false }, { matchMedia: () => motion },
    { townTransport: { update(dt, camera, options) { assert.strictEqual(camera, eye); calls.push({dt, options}); } } },
    { position: eye }, confidence, { invalidate() {} }, shownLayers, world);
  const tick = delta => { clock.delta = delta; const reads = clock.reads; native.tick(); assert.equal(clock.reads, reads + 1); return calls.at(-1); };
  assert.equal(tick(30).dt, 0);
  assert.equal(tick(.5).dt, .5);
  assert.equal(calls.at(-1).options.elapsedFrame, true);
  assert.equal(calls.at(-1).options.visualDt, .5);
  assert.equal(calls.at(-1).options.hour, 12.5);
  motion.matches = true; for (const listener of listeners) listener();
  motion.matches = false; for (const listener of listeners) listener();
  assert.equal(tick(30).dt, 0, 'Preference off/on without any held tick rebases the journey interval');
  assert.equal(tick(.5).dt, .5);
  native.hide('reconstructed', true); native.hide('reconstructed', false);
  assert.equal(tick(30).dt, 0, 'Confidence hide/show without any held tick rebases the journey interval');
  assert.equal(tick(.5).dt, .5);
  assert.equal(calls.at(-1).options.hidden, false);
  shownLayers.vehicles = false; tick(.5);
  assert.equal(calls.at(-1).options.hidden, true, 'Carriages and horses hidden (T-3439) hides and suspends every team');
  shownLayers.vehicles = true; tick(.5);
  assert.equal(calls.at(-1).options.hidden, false);
  console.log('native main elapsed forwarding and no-held-tick transport preference/confidence boundaries PASS');
}

// T-3497: closed paths, timed stops, and the 1812 fort wagons on the committed 1812 ground.
{
  const { pathRoute, routeFor, routeDistanceNear } = await import('../renderers/web/js/transport-loop.js');
  const { createSmoothedGround } = await import('../renderers/web/js/transport-ground.js');
  const { teamSupportAt, certifiedHorseSupportDomain } = await import('../renderers/web/js/transport-support.js');
  const { buildRows } = await import('./lay_driven_wagons_1812.mjs');
  let checks = 0;
  // A square path with filleted corners is closed, unit-speed and turns left at +1/R.
  const square = pathRoute({ points_enu_m: [[0, 0], [100, 0], [100, 100], [0, 100]], corner_radius_m: 20 });
  near(square.length, 4 * 60 + 2 * Math.PI * 20, 1e-6); checks++;
  for (const s of [0, 10, 70, 150, square.length - .1]) {
    const a = square.at(s), b = square.at(s + 1e-4);
    near(Math.hypot(b.e - a.e, b.n - a.n) / 1e-4, 1, 1e-3); checks++;
  }
  near(square.maxCurvature, 1 / 20, 1e-9); checks++;
  // It starts on the first corner's bend; the bends of a counter-clockwise square turn left.
  for (let k = 0; k < 4; k++) { near(square.at(k * (60 + 10 * Math.PI) + 5 * Math.PI).curvature, 1 / 20, 1e-9); checks++; }
  near(square.at(10 * Math.PI + 30).curvature, 0, 1e-12); checks++;
  near(square.at(0).e, square.at(square.length).e, 1e-9); checks++;
  assert.throws(() => pathRoute({ points_enu_m: [[0, 0], [10, 0], [10, 10], [0, 10]], corner_radius_m: 20 }), /too close/); checks++;
  assert.deepEqual(routeFor({ kind: 'path', points_enu_m: [[0, 0], [100, 0], [100, 100], [0, 100]], corner_radius_m: 20 }).length, square.length); checks++;
  const near50 = routeDistanceNear(square, 50, -1);
  near(near50.distance_m, 10 * Math.PI + 30, .25); near(near50.off_m, 1, .01); checks++;

  // A stop: the team pulls up exactly there, dwells while still moving, then goes on.
  const poses = [], events = [];
  const stopped = createTransportLoop({ id: 'stop', name: 'Teamster', route: square,
    assembly: { pose(p) { poses.push(p); }, visible() {}, stop() { events.push('stop'); }, dispose() {} },
    speed_m_s: 1, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [1.3, 0, 4], heightAt: () => 0,
    stops: [{ distance_m: 5, dwell_s: 3, label: 'door' }] });
  for (let i = 0; i < 20; i++) stopped.update(.5); // .25 m an update, so 5 m in 20
  near(stopped.snapshot().distance_m, 5, 1e-9); checks++;
  assert.equal(stopped.state, 'moving'); assert.equal(stopped.dwelling?.label, 'door'); checks++;
  assert(events.includes('stop')); checks++;
  for (let i = 0; i < 5; i++) stopped.update(.5);
  near(stopped.snapshot().distance_m, 5, 1e-9); checks++;
  for (let i = 0; i < 2; i++) stopped.update(.5);
  assert.equal(stopped.dwelling, null); assert(stopped.snapshot().distance_m > 5); checks++;
  assert.throws(() => createTransportLoop({ id: 'x', name: 'x', route: square, assembly: { pose() {} },
    speed_m_s: 1, wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 0, 0], heightAt: () => 0,
    stops: [{ distance_m: NaN, dwell_s: 3 }] }), /stops need/); checks++;

  // The laid rows are the committed rows, and each whole road holds wheels and hooves on the
  // committed 1812 ground (read as the scene reads it for transport: transport-ground.js).
  const config = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));
  assert.deepEqual(config.rows.filter(row => row.scene === '1812'), buildRows(), 'run node tools/lay_driven_wagons_1812.mjs'); checks++;
  const terrainDir = new URL('../data/terrain/epochs/e1830_natural/', import.meta.url);
  const hf = JSON.parse(readFileSync(new URL('heightfield.json', terrainDir)));
  const raw = new Int16Array(readFileSync(new URL('heightfield.bin', terrainDir)).buffer.slice(0));
  const cells = Float32Array.from(raw.subarray(0, hf.cols * hf.rows), v => v * hf.scale + hf.offset);
  const bilinear = (e, n) => {
    const gx = (e - hf.origin_e) / hf.cell_m, gy = (n - hf.origin_n) / hf.cell_m;
    const x0 = Math.min(Math.floor(gx), hf.cols - 2), y0 = Math.min(Math.floor(gy), hf.rows - 2), fx = gx - x0, fy = gy - y0;
    const r0 = y0 * hf.cols, r1 = r0 + hf.cols;
    return (cells[r0 + x0] * (1 - fx) + cells[r0 + x0 + 1] * fx) * (1 - fy) + (cells[r1 + x0] * (1 - fx) + cells[r1 + x0 + 1] * fx) * fy;
  };
  const ground = createSmoothedGround({ sample: bilinear, grid: { cellM: hf.cell_m, originE: hf.origin_e, originN: hf.origin_n } });
  const spec = config.horse_models.current26_walk_v2;
  const domain = certifiedHorseSupportDomain(spec, JSON.parse(readFileSync(new URL(`../data/${spec.support_domain.certificate_file}`, import.meta.url))));
  for (const row of config.rows.filter(r => r.scene === '1812')) {
    const route = routeFor(row.route);
    const reading = preflightTransportRoute({ row, route, heightAt: ground, clear: () => true,
      support: pose => teamSupportAt(row, pose, ground, domain) });
    assert.match(reading.status, /PASS/, `${row.id} on the 1812 ground`); checks++;
    assert(reading.maximum_wheel_gap_m < .03); checks++;
    for (const stop of row.stops) assert(stop.distance_m >= 0 && stop.distance_m < route.length && stop.dwell_s > 0); checks++;
  }
  // Hours: a team is put up outside its teamster's [from, to); no hour or no hours, never.
  const { offHours } = await import('../renderers/web/js/town-transport.js');
  assert.equal(offHours([5.5, 21], 12), false); assert.equal(offHours([5.5, 21], 21.5), true);
  assert.equal(offHours([5.5, 21], 3), true); assert.equal(offHours([22, 6], 23), false);
  assert.equal(offHours([22, 6], 12), true); assert.equal(offHours(null, 3), false);
  assert.equal(offHours([5.5, 21], null), false); checks += 7;
  console.log(`T-3497 paths, stops and 1812 wagon roads: ${checks} checks PASS`);
}
