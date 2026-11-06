#!/usr/bin/env node
/**
 * T-3432: a jaunt flies to its start on a clock, opens on a welcome, shows a road note only
 * when there is time to read it, says when a stop is the last, and lands every interrupted
 * flight. Node only: the controller, the travel glide and the panel's pure helpers.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createJaunts, reduce, emptyState, isFinalStop } from '../renderers/web/js/jaunts.js';
import { createTravel, glideSeconds, glidePose, GLIDE_MAX_S } from '../renderers/web/js/travel.js';

// The panel module reads `document` only inside createJauntPanel, so its helpers load in node.
const { openingParagraphs, readableLines } = await import('../renderers/web/js/jaunt-panel.js');
const read = file => JSON.parse(fs.readFileSync(new URL(`../${file}`, import.meta.url)));
const DEG = Math.PI / 180;

// ---- the glide's clock: a hop, a crossing, the far side of town, never past the cap.
assert.equal(glideSeconds(3), 0, 'nothing to fly from where you stand');
assert.equal(glideSeconds(60), 3.5);
assert(glideSeconds(900) > 5 && glideSeconds(900) < GLIDE_MAX_S);
assert.equal(glideSeconds(5000), GLIDE_MAX_S);
assert(GLIDE_MAX_S <= 10, 'the owner: "maybe 5-10 seconds max"');
console.log('PASS glide seconds: 3.5 s for a hop, never more than', GLIDE_MAX_S, 's');

// ---- its path: starts and ends on the poses given, climbs before it moves, clears the town.
const from = { e: 0, n: 0, altitude: 1.68, yaw: 0, pitch: 0 }, to = { e: 600, n: 400, altitude: 1.68, yaw: 1.2, pitch: -0.1 };
for (const [t, want] of [[0, from], [1, to]]) {
  const p = glidePose(from, to, t);
  for (const k of ['e', 'n', 'altitude', 'pitch']) assert(Math.abs(p[k] - want[k]) < 1e-9, `${k} at t=${t}`);
  assert(Math.abs(Math.atan2(Math.sin(p.yaw - want.yaw), Math.cos(p.yaw - want.yaw))) < 1e-9, `yaw at t=${t}`);
}
const early = glidePose(from, to, 0.08);
assert.equal(early.e, 0, 'still over the start while it climbs'); assert(early.altitude > 10, 'up before along');
const mid = glidePose(from, to, 0.5);
assert(mid.altitude > 60, `over the roofs mid-way (${mid.altitude.toFixed(1)} m)`);
assert(mid.pitch < 0, 'looks a little down over the town');
console.log('PASS glide path: up, along, down, onto the given framing');

// ---- the controller under simulate(): lands exactly where the jump would have put you.
function rig() {
  const state = { e: 0, n: 0, yaw: 0, pitch: 0, groundY: 0, eyeY: 1.68, altitude: 0, flying: false, bob: 0, speed: 0 };
  const intent = { flying: false, forward: 0, strafe: 0, rise: 0, yawDelta: 0, pitchDelta: 0, sprint: false, moving: false, interact: false,
    clear() { Object.assign(this, { forward: 0, strafe: 0, rise: 0, yawDelta: 0, pitchDelta: 0, sprint: false, moving: false, interact: false }); } };
  const walker = { state, resettle() {}, update() {} };
  const poses = [];
  const travel = createTravel({ walker, intent, settings: {},
    setFly: on => { intent.flying = on; state.flying = on; },
    teleport: ({ local_e, local_n, altitude_m = null, yaw_deg = null, pitch_deg = null }) => {
      state.e = local_e; state.n = local_n;
      if (yaw_deg !== null) state.yaw = -yaw_deg * DEG;
      state.pitch = pitch_deg !== null ? pitch_deg * DEG : 0;
      state.altitude = altitude_m ?? 0; state.eyeY = 1.68 + (altitude_m ?? 0); state.flying = altitude_m !== null;
      poses.push({ ...state });
    } });
  return { state, intent, travel, poses };
}
{
  const { state, travel, poses } = rig();
  let arrived = 0;
  assert(travel.glide(from, to, { token: { leg: 1 }, onArrive: tok => { arrived++; assert.equal(tok.leg, 1); } }));
  assert.equal(travel.state.phase, 'gliding');
  const run = travel.simulate(30, 1 / 30);
  assert.equal(run.phase, 'idle'); assert.equal(arrived, 1);
  assert(run.seconds <= glideSeconds(Math.hypot(600, 400)) + 0.05, `glide took ${run.seconds.toFixed(2)} s`);
  assert.equal(state.e, to.e); assert.equal(state.n, to.n); assert.equal(state.flying, false);
  assert(Math.abs(state.pitch - to.pitch) < 1e-9 && Math.abs(Math.atan2(Math.sin(state.yaw - to.yaw), Math.cos(state.yaw - to.yaw))) < 1e-9);
  assert(Math.max(...poses.map(p => p.altitude)) > 60, 'it flew');
}
{
  // Stopped mid-air for any reason, a glide is landed, never left hanging.
  const { state, travel } = rig();
  let stopped = null;
  travel.glide(from, to, { token: { leg: 2 }, onStop: tok => { stopped = tok; } });
  travel.simulate(1, 1 / 30); assert.equal(travel.state.phase, 'gliding'); assert(state.altitude > 1);
  travel.stop('jaunt');
  assert.equal(stopped.reason, 'jaunt'); assert.equal(state.e, to.e); assert.equal(state.altitude, 0); assert.equal(state.flying, false);
}
{
  // The visitor's own first move lands it at once, as an arrival.
  const { state, intent, travel } = rig();
  let arrived = false;
  travel.glide(from, to, { token: {}, onArrive: () => { arrived = true; } });
  travel.simulate(0.5, 1 / 30);
  intent.moving = true; travel.update(1 / 30, intent);
  assert(arrived); assert.equal(state.e, to.e); assert.equal(travel.state.phase, 'idle');
}
{
  // Reduced motion, or nothing to fly: no glide, and nothing moved.
  const { state, travel } = rig();
  assert.equal(travel.glide(from, { ...from, e: 3 }, {}), false); assert.equal(state.e, 0); assert.equal(travel.state.phase, 'idle');
}
console.log('PASS glide controller: lands exactly, on time, when stopped and at the first move');

// ---- the jaunt: opening (flying, welcome up) → atStop at the landing; a jump without one.
const doc = read('data/jaunts/_fixtures/fixture-walk.json');
function controller(approach, renders = []) {
  const travel = { mode: 'walk', setMode(m) { this.mode = m; }, go: () => true, stop: () => { flight?.onStop?.({ ...flight.token, reason: 'jaunt' }); flight = null; } };
  let flight = null;
  const c = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel,
    render: s => renders.push(s.phase), showMenu() {}, closeDetail() {}, onError: e => { throw e; }, storage: null,
    approach: approach && (() => ({ begin: cb => { flight = cb; return approach(cb); } })) });
  return { c, flight: () => flight };
}
{
  const renders = [], { c, flight } = controller(() => true, renders);
  await c.start(doc.id);
  assert.equal(c.state.phase, 'opening', 'the welcome is up while it flies');
  assert.deepEqual(renders.slice(-1), ['opening']);
  flight().onArrive(flight().token);
  assert.equal(c.state.phase, 'atStop'); assert.equal(c.state.stopIndex, 0);
}
{
  const { c } = controller(() => false);
  await c.start(doc.id); assert.equal(c.state.phase, 'atStop', 'declined (reduced motion): a jump, as before');
  const plain = controller(null); await plain.c.start(doc.id); assert.equal(plain.c.state.phase, 'atStop', 'no approach: a jump');
}
{
  // Instantly is the visitor's own ask: no flight.
  let asked = false; const { c } = controller(() => { asked = true; return true; });
  await c.start(doc.id, { mode: doc.allowed_modes.includes('instantly') ? 'instantly' : doc.default_mode });
  if (doc.allowed_modes.includes('instantly')) { assert.equal(asked, false); assert.equal(c.state.phase, 'atStop'); }
}
{
  // The menu opened mid-flight lands it; Continue resumes at the stop, never in the air.
  const { c } = controller(() => true);
  await c.start(doc.id); c.menu();
  assert.equal(c.state.phase, 'menu'); assert.equal(c.state.resumePhase, 'atStop');
  assert(c.resume()); assert.equal(c.state.phase, 'atStop');
}
console.log('PASS jaunt start: flies with the welcome up, arrives on landing, jumps when asked or declined');

// ---- the last stop is known as the last.
let s = reduce(emptyState(), { type: 'START', jaunt: doc, session: 1 });
s = reduce(s, { type: 'ARRIVE', session: 1, leg: s.leg });
assert.equal(isFinalStop(s), false, 'stop 1 of a two-stop walk is not the last');
s = reduce(s, { type: 'NEXT' }); s = reduce(s, { type: 'ARRIVE', session: 1, leg: s.leg });
assert.equal(s.stopIndex, 1); assert.equal(isFinalStop(s), true, 'its second stop is');
const branching = { ...doc, stops: [{ ...doc.stops[0], next: null, choices: [{ id: 'a', label: 'A', next: doc.stops[1].id }, { id: 'b', label: 'B', next: '$end' }] }, doc.stops[1]] };
let b = reduce(reduce(emptyState(), { type: 'START', jaunt: branching, session: 1 }), { type: 'ARRIVE', session: 1, leg: 1 });
assert.equal(isFinalStop(b), false, 'a choice may still go on');
assert.equal(isFinalStop(reduce(b, { type: 'CHOOSE', id: 'b' })), true, 'until the choice made ends it');
console.log('PASS final stop: known on a walk and on a branching stop');

// ---- the welcome's background, and the road notes a leg leaves time to read.
assert.deepEqual(openingParagraphs({ opening: { text: 'JAUNT: MEET THE GLESSNER HOUSE. A summer morning, 1904.\n\nTen stops on foot.' } }),
  ['A summer morning, 1904.', 'Ten stops on foot.'], 'the title the welcome already heads is not repeated');
assert.deepEqual(openingParagraphs({ opening: { text: 'Dusk on 1 July 1835.' } }), ['Dusk on 1 July 1835.']);
const lines = [{ text: 'Passing the Green Tree Tavern, on your left.' }, { text: Array(60).fill('word').join(' ') }];
assert.equal(readableLines(lines, 0.5).length, 0, 'an instant leg shows none');
assert.equal(readableLines(lines, 6).length, 1, 'a short leg shows only what can be read, whole');
assert.equal(readableLines(lines, 40).length, 2);
assert.equal(readableLines(lines, undefined).length, 2, 'no estimate: every line');
for (const jaunt of fs.readdirSync(new URL('../data/jaunts/', import.meta.url)).filter(f => f.endsWith('.json'))) {
  const doc = read(`data/jaunts/${jaunt}`);
  if (doc.opening?.text) assert(openingParagraphs(doc).length >= 1, `${jaunt}: its welcome has a background`);
}
console.log('JAUNT START/FINISH PASS — glide clock, path and landings, welcome phase, final stop, readable road notes');
