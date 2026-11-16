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

// ---- the owner, 2026-11-16: openings read on the way in, closings shown before Outing complete.
const pace = await import('../renderers/web/js/jaunt-pace.js');
assert.equal(pace.clipSeconds({ bytes: 392506, output_format: 'mp3_44100_64' }).toFixed(1), '49.1', 'a 64 kbit/s clip: bytes / 8000');
assert.equal(pace.clipSeconds({ chars: 150 }), 10); assert.equal(pace.clipSeconds(null), null);
assert.equal(pace.openingFlightSeconds(null), null, 'no voice: the plain glide');
assert.equal(pace.openingFlightSeconds(49.1).toFixed(1), '48.1', 'landing a second before the narrator finishes');
assert.equal(pace.openingFlightSeconds(400), pace.OPENING_MAX_S);
assert.equal(pace.closingFlightSeconds(32.7).toFixed(2), '16.35', 'up to the last view in about half the ending');
assert.equal(pace.closingFlightSeconds(null), null);
{
  // A voiced opening is flown for its length, by way of a high look back over the town.
  const { state, travel, poses } = rig();
  const stand = { e: 0, n: 0, altitude: 1.68, yaw: 0, pitch: 0 }, start = { e: 300, n: -200, altitude: 1.68, yaw: 1, pitch: 0 };
  const via = pace.openingOverlook(stand, 48);
  assert(via.altitude > 60 && via.pitch < 0, 'the overlook is high and looks down');
  let landed = 0;
  assert(travel.glide(start, stand, { token: {}, onArrive: () => { landed++; } }, { seconds: 48, via }));
  const run = travel.simulate(120, 1 / 10);
  assert.equal(landed, 1); assert(Math.abs(run.seconds - 48) < 0.2, `flown for the voice's length (${run.seconds.toFixed(1)} s)`);
  assert(poses.some(p => Math.hypot(p.e - via.e, p.n - via.n) < 2 && Math.abs(p.altitude - via.altitude) < 2), 'it passes over the overlook');
  assert.equal(state.e, 0); assert.equal(state.flying, false, 'and lands at the start');
}
{
  // The closing flight ends in the air, on the view, and stays there.
  const { state, travel } = rig();
  const view = pace.closingView({ e: 100, n: 100, aim: { e: 100, n: 120 } });
  assert(Math.abs(view.e - 100) < 1e-9 && Math.abs(view.n - (100 - pace.CLOSING_VIEW.back_m)) < 1e-9, 'back behind the stand, away from what it frames');
  assert.equal(view.altitude, pace.CLOSING_VIEW.up_m); assert(view.pitch < 0);
  assert(travel.glide({ e: 100, n: 100, altitude: 1.68, yaw: 0, pitch: 0 }, view, { token: {} }, { seconds: 16, hover: true }));
  travel.simulate(30, 1 / 10);
  assert.equal(travel.state.phase, 'idle'); assert.equal(state.altitude, view.altitude, 'hovering over the place');
  assert.equal(state.flying, true);
}
{
  // The runtime: a voiceover lengthens the flight to the start; Skip to the Start lands it.
  let asked = null;
  const travel = { mode: 'walk', setMode(m) { this.mode = m; }, go: () => true, stop() {} };
  const c = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel,
    render() {}, showMenu() {}, closeDetail() {}, onError: e => { throw e; }, storage: null,
    voiceover: async (j, part) => (part === 'opening' ? 48 : null),
    approach: () => ({ begin: cb => { asked = cb.seconds; return true; } }), closing: { begin: () => true } });
  await c.start(doc.id);
  assert.equal(asked, 48, 'the approach is told how long the opening is read');
  assert.equal(c.state.phase, 'opening'); c.skip(); assert.equal(c.state.phase, 'atStop', 'skipped to the first stop');
}
{
  let begun = 0, completed = 0, menus = 0;
  const travel = { mode: 'walk', setMode(m) { this.mode = m; }, go: () => true, stop() {} };
  let arrive = null;
  const c = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true,
    travel: { ...travel, go: (t, cb) => { arrive = cb; return true; } },
    render() {}, showMenu() { menus++; }, closeDetail() {}, onError: e => { throw e; }, storage: null,
    onComplete: () => { completed++; }, closing: { begin: () => { begun++; return true; } } });
  await c.start(doc.id);
  c.next(); arrive.onArrive(arrive.token);
  assert.equal(c.state.stopIndex, 1); c.next();
  assert.equal(c.state.phase, 'closing', 'the final stop goes on to its closing scene');
  assert.equal(begun, 1, 'the closing flight begins'); assert.equal(completed, 1, 'the outing counts as finished');
  assert.equal(menus, 0, 'Outing complete waits');
  assert.equal(c.prev(), false, 'no going back from the closing');
  c.finish(); assert.equal(c.state.phase, 'outcome'); assert.equal(menus, 1); assert.equal(completed, 1, 'awarded once');
  // Without a closing adapter (the tests' harnesses), the last Next is Outing complete as before.
  let plain = reduce(emptyState(), { type: 'START', jaunt: doc, session: 1 });
  plain = reduce(plain, { type: 'ARRIVE', session: 1, leg: plain.leg }); plain = reduce(plain, { type: 'NEXT' });
  plain = reduce(plain, { type: 'ARRIVE', session: 1, leg: plain.leg }); plain = reduce(plain, { type: 'NEXT' });
  assert.equal(plain.phase, 'outcome');
  const closed = reduce(reduce(reduce(reduce(reduce(emptyState(), { type: 'START', jaunt: doc, session: 1 }), { type: 'ARRIVE', session: 1, leg: 1 }), { type: 'NEXT' }), { type: 'ARRIVE', session: 1, leg: 2 }), { type: 'NEXT', closing: true });
  assert.equal(closed.phase, 'closing');
  assert.equal(reduce(closed, { type: 'MENU' }).phase, 'outcome', 'the menu opened in the closing finishes it');
  assert.equal(reduce(closed, { type: 'END' }).phase, 'menu', 'End still ends');
}
{
  // The closing clock: a voiced ending ends the scene a moment after its voice; unvoiced, after its reading time.
  let t = 0, playing = false, ended = false, finished = 0, flying = true;
  const clock = pace.createClosingClock({ now: () => t, voice: { playing: () => playing, ended: () => ended }, flying: () => flying, finish: () => { finished++; } });
  const closingState = { phase: 'closing', session: 1, leg: 5, outcome: { text: Array(30).fill('word').join(' ') } };
  clock.update(closingState); assert(clock.active);
  t = 1; playing = true; clock.tick(); t = 20; flying = false; clock.tick(); assert.equal(finished, 0, 'while the voice speaks');
  t = 33; playing = false; ended = true; clock.tick(); assert.equal(finished, 0, 'held a moment after it');
  t = 33 + pace.CLOSING_HOLD_S; clock.tick(); assert.equal(finished, 1, 'then Outing complete');
  const quiet = pace.createClosingClock({ now: () => t, voice: { playing: () => false, ended: () => false }, finish: () => { finished++; } });
  t = 0; quiet.update({ ...closingState, leg: 9 });
  t = pace.readingSeconds(closingState.outcome.text) - 0.1; quiet.tick(); assert.equal(finished, 1, 'unvoiced: read first');
  t += 0.2; quiet.tick(); assert.equal(finished, 2, 'then Outing complete');
}
console.log('PASS openings and closings: flown while read, a closing scene, then Outing complete');
{
  // The owner, 2026-11-16: a quiet meter, the stop's scene in real time and the whole jaunt.
  const near = (a, b, msg) => assert(Math.abs(a - b) < 1e-9, `${msg}: ${a} vs ${b}`);
  let p = pace.sceneProgress([{ t: 10, d: 40 }, { t: 30, d: 60 }]);
  near(p.value, 0.25, 'the slowest part paces the scene'); near(p.left, 30, 'and the longest says what is left');
  assert.deepEqual(pace.sceneProgress([]), { value: 1, left: 0 }, 'a stop with nothing playing is done');
  p = pace.sceneProgress([{ t: 99, d: 40 }, null, { t: 2, d: 0 }]); near(p.value, 1, 'clamped, and empty parts ignored');
  let m = pace.meterReading({ phase: 'atStop', stopIndex: 1, count: 4, voice: { t: 15, d: 60 }, read: { t: 50, d: 41 }, stage: null });
  near(m.value, 0.25, 'a heard voice paces the scene, not the reading time'); near(m.left, 45, 'its time left');
  near(m.overall, (1 + 0.25) / 4, 'overall: stops behind plus this scene'); assert.equal(m.kind, 'scene');
  m = pace.meterReading({ phase: 'atStop', stopIndex: 1, count: 4, voice: { t: 1, d: 1 }, read: { t: 5, d: 41 }, stage: { t: 30, d: 90 } });
  near(m.value, 1 / 3, 'voice done, the stage still plays'); near(m.left, 60, 'the stage says what is left');
  m = pace.meterReading({ phase: 'atStop', stopIndex: 2, count: 4, voice: null, read: { t: 20.5, d: 41 } });
  near(m.value, 0.5, 'unheard: the reading time paces it');
  m = pace.meterReading({ phase: 'travelling', stopIndex: 2, count: 4, way: { t: 300, d: 400 } });
  assert.equal(m.kind, 'way'); near(m.value, 0.75, 'the way to the stop'); near(m.overall, 2 / 4, 'the way is not the scene'); assert.equal(m.left, 0, 'no clock on a walk (its estimate is on the card)');
  m = pace.meterReading({ phase: 'opening', stopIndex: 0, count: 4, glide: { t: 20, d: 64 }, way: { t: 1, d: 2 } });
  assert.equal(m.index, 0); near(m.value, 20 / 64, 'the opening flight, by its clock'); near(m.left, 44, 'with its time');
  m = pace.meterReading({ phase: 'closing', stopIndex: 3, count: 4 }); near(m.overall, 1, 'closing: all of it done');
  assert.equal(pace.meterReading({ phase: 'outcome', stopIndex: 3, count: 4 }), null, 'Outing complete has no meter');
  assert.equal(pace.meterReading({}), null);
  assert.equal(pace.clockText(0.4), ''); assert.equal(pace.clockText(42.2), '0:43'); assert.equal(pace.clockText(65), '1:05');
  // The stage's length is its last beat; the narration says where its voice is.
  const stageSrc = fs.readFileSync(new URL('../renderers/web/js/jaunt-stage.js', import.meta.url), 'utf8');
  assert.match(stageSrc, /get length\(\)/, 'jaunt-stage exposes its length');
  assert.match(fs.readFileSync(new URL('../renderers/web/js/narration.js', import.meta.url), 'utf8'), /\n    position\(jaunt, part, id\)/, 'the narration says how far its voice has spoken');
}
console.log('PASS meter: scene in real time, the jaunt as a row of stops');
console.log('JAUNT START/FINISH PASS — glide clock, path and landings, welcome phase, final stop, readable road notes, openings and closings, meter');
