// SPDX-License-Identifier: GPL-3.0-or-later
// T-3557 (Kevin, 2026-11-14: "we wanted to be able to board and drive the team around"): the
// Interact adapter's boarding half. Which actions each state offers, Climb up stopping and then
// resuming the round, the reins calling takeReins/handBack and the movement keys becoming the
// team's throttle and steering, Get down pulling a moving team up first and landing the visitor
// on a clear stand beside it, the visitor never strands (a team gone, hidden or flown from), and
// an actor without the drive API offering exactly today's actions.
//
//   node tools/test_transport_boarding.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createInteractions } from '../renderers/web/js/interact.js';
import { registerTransportInteraction, createTeamRide, canBoard, boardStand, riderOffTeam, RIDE_S }
  from '../renderers/web/js/transport-interactions.js';
import { DRIVE_SPEED_CAP_M_S } from '../renderers/web/js/team-drive.js';
import { createTransportClearance, transportEnvelope } from '../renderers/web/js/transport-clearance.js';

const ids = thing => (thing.actions[thing.state] ?? []).map(a => a.id);
const tick = (engine, seconds, dt = 0.05, each = () => {}) => {
  for (let t = 0; t < seconds - 1e-9; t += dt) { each(); engine.update(dt); }
};

/** A team on a straight road north, root at (0, n), yaw π (forward = +n). The seat is the row's. */
function makeActor({ drive = true, id = 'team', row }) {
  const calls = [];
  const yaw = Math.PI;
  const a = {
    id, name: 'Carriage driver', mode: 'route', state: 'moving', visible: true, disposed: false,
    n: 0, speed_m_s: 1.3, blocked: null, inputs: [],
    get at() { return [0, this.n + 0.76]; },
    get heading_deg() { return 0; },
    stop(why) { calls.push(['stop', why]); this.state = 'stopped'; this.speed_m_s = 0; return true; },
    canResume() { return true; },
    resume() { calls.push(['resume']); this.state = 'moving'; this.speed_m_s = 1.3; return true; },
    previewAt(s) { return { e: 0, n: s, yaw }; },
    snapshot() { return { distance_m: this.n, yaw_rad: yaw, mode: this.mode }; },
    calls,
  };
  if (drive) Object.assign(a, {
    seat() {
      const [x, y, z] = row.passenger_local_m;
      // transport-loop.js localToEnu: x -> (cos yaw, sin yaw), z -> (sin yaw, -cos yaw).
      return { e: Math.cos(yaw) * x + Math.sin(yaw) * z, n: a.n + Math.sin(yaw) * x - Math.cos(yaw) * z,
        y: y + row.passenger_eye_m, yaw_rad: yaw, heading_deg: 0 };
    },
    takeReins() { calls.push(['takeReins']); a.mode = 'reins'; a.state = 'moving'; return true; },
    handBack() { calls.push(['handBack']); a.mode = 'returning'; a.state = 'moving'; return true; },
    drive(input) { a.inputs.push(input); if (input.throttle < 0) a.speed_m_s = Math.max(0, a.speed_m_s - 0.5); },
  });
  return a;
}

/** A walker as crossings.holdVisitor and the ride both use it. */
function makeWalker(e = 3, n = 0) {
  const w = {
    state: { e, n, eyeY: 1.6, groundY: 0, altitude: 0, stepEase: 0, bob: 0, yaw: 0, pitch: 0, flying: false },
    applied: 0, teleports: [],
    get bearingDeg() { return ((-w.state.yaw * 180 / Math.PI) % 360 + 360) % 360; },
    apply() { w.applied++; },
    teleport({ local_e, local_n }) { w.teleports.push([local_e, local_n]); w.state.e = local_e; w.state.n = local_n; w.state.eyeY = 1.6; },
  };
  return w;
}

const config = JSON.parse(await readFile(new URL('../data/transport/driven/loops.json', import.meta.url), 'utf8'));
const brougham = config.rows.find(r => r.id === 'prairie_driven_brougham_loop_1904');

// Every driven row has a measured seat for the visitor, in the vehicle's own frame.
for (const row of config.rows) {
  assert(Array.isArray(row.passenger_local_m) && row.passenger_local_m.length === 3 && row.passenger_local_m.every(Number.isFinite), `${row.id}: passenger_local_m`);
  assert(row.passenger_eye_m > 0.6 && row.passenger_eye_m < 0.95, `${row.id}: seated eye height`);
  assert(/L-board-drive-3557/.test(row.passenger_basis ?? ''), `${row.id}: the seat is recorded as reconstructed play`);
  const [x, , z] = row.passenger_local_m, [l, b, r, f] = row.envelope_local_xz_m;
  assert(x > l && x < r && z > b && z < f, `${row.id}: the seat is inside the team's own envelope`);
  if (row.driver_mode !== 'on_foot') assert(Math.abs(x - row.driver_local_m[0]) >= 0.3, `${row.id}: beside the driver, not in his lap`);
  // The ride bar's short name: a phone at 390 px cut "Carriage driver on Pra…".
  assert(typeof row.ride_name === 'string' && row.ride_name.length >= 4 && row.ride_name.length <= 20, `${row.id}: a short ride_name`);
  assert(row.ride_name.length < row.name.length, `${row.id}: ride_name is shorter than its name`);
}
assert.equal(new Set(config.rows.map(r => r.ride_name)).size, config.rows.length, 'every team has its own ride name');
// The seat beside a seated driver clears his hat's brim however he turns his head (its widest
// radius about his head: W01 felt hat 0.19 m, brougham top hat 0.164 m, from the wardrobes'
// own hat meshes), and stays on the board or inside the box's side rail (x 0.515 m).
for (const [id, brim, inside] of [['western_hotel_driven_wagon_loop_1835', 0.19, 0.59],
  ['prairie_driven_brougham_loop_1904', 0.164, 0.515], ['prairie_driven_brougham_north_loop_1904', 0.164, 0.515],
  ['prairie_driven_brougham_south_loop_1904', 0.164, 0.515]]) {
  const row = config.rows.find(r => r.id === id), x = Math.abs(row.passenger_local_m[0] - row.driver_local_m[0]);
  assert(x - brim >= 0.17, `${id}: the eye clears his hat's brim (${(x - brim).toFixed(3)} m)`);
  assert(Math.abs(row.passenger_local_m[0]) < inside, `${id}: the seat is on the board`);
}
console.log('transport boarding: all six driven rows carry a measured passenger seat inside their envelope, clear of the driver\'s hat, and a short ride name PASS');

// 1. No drive API (today's actor), even with a ride: exactly today's actions.
{
  const engine = createInteractions(), ride = createTeamRide();
  const old = makeActor({ drive: false, row: brougham });
  assert.equal(canBoard(old), false);
  const h = registerTransportInteraction(engine, old, { ride });
  assert.deepEqual(ids(h.thing), ['stop']);
  old.state = 'stopped'; h.refresh();
  assert.deepEqual(ids(h.thing), ['continue']);
  old.canResume = () => false;
  assert.deepEqual(ids(h.thing), ['give-room']);
  h.dispose();
  // And a drive-API actor with no ride (an older scene binding) is just as it was.
  const plain = makeActor({ row: brougham });
  const p = registerTransportInteraction(createInteractions(), plain);
  assert.deepEqual(ids(p.thing), ['stop']);
  p.dispose();
  console.log('transport boarding: an actor without the drive API, or a scene without a ride, offers today\'s actions PASS');
}

// 2. Climb up: a moving team stops, the eye eases up onto the seat, the round goes on.
{
  const engine = createInteractions(), walker = makeWalker(2.5, 0.5), boarded = [];
  const actor = makeActor({ row: brougham });
  const ride = createTeamRide({
    visitor: () => ({ e: walker.state.e, n: walker.state.n, y: walker.state.eyeY, bearing: walker.bearingDeg }),
    standFor: a => boardStand({ actor: a, row: brougham }), groundAt: () => 0, walkEye: () => 1.6,
    onBoard: (a, on, why) => boarded.push([a.id, on, why]),
  });
  const h = registerTransportInteraction(engine, actor, { ride, vehicle: 'carriage', driver: 'coachman', reinsHint: () => 'Reins: keys' });
  assert.deepEqual(ids(h.thing), ['stop', 'climb-up']);
  assert.equal(h.thing.actions.moving[1].label, 'Climb up beside the coachman');
  actor.state = 'stopped'; h.refresh();
  assert.deepEqual(ids(h.thing), ['continue', 'climb-up']);
  actor.state = 'moving'; h.refresh();

  assert.equal(engine.act(h.thing, 'climb-up').ok, true);
  assert.deepEqual(actor.calls[0], ['stop', 'boarding'], 'a moving team pulls up before anyone climbs');
  assert.deepEqual(boarded, [['team', true, 'climb']], 'boarding is told at once (it ends a Go to or a follow)');
  assert.equal(ride.phase, 'climbing');
  const eyes = [];
  tick(engine, RIDE_S.climb / 2, 0.05, () => { ride.hold(walker, { eyeHeight: 1.6 }); eyes.push([walker.state.e, walker.state.n, walker.state.eyeY]); });
  assert(eyes.length > 5 && new Set(eyes.map(String)).size > 5, 'the climb is eased, not a jump');
  assert(Math.max(...eyes.map(p => p[2])) > 1.6, 'up over the wheel');
  // The press that comes the moment the visitor is seated works the seat: nothing of the climb
  // is left running to swallow it (a zero-second "Moving off" step did, for a frame).
  for (let i = 0; i < 100 && ride.phase !== 'seated'; i++) { ride.hold(walker, { eyeHeight: 1.6 }); engine.update(0.05); }
  assert.equal(ride.phase, 'seated');
  assert.equal(h.thing.running, null, 'seated, the climb is over in the same frame');
  assert.equal(engine.offer(h.thing).busy, false);
  assert.equal(ride.aboard, actor);
  assert.deepEqual(actor.calls.at(-1), ['resume'], 'then it goes on round');
  ride.hold(walker, { eyeHeight: 1.6 });
  const seat = actor.seat();
  assert.deepEqual([walker.state.e, walker.state.n, walker.state.eyeY], [seat.e, seat.n, seat.y], 'held on the seat');
  assert.equal(walker.state.groundY, seat.y - 1.6);
  // The team moves; the eye goes with it, every frame.
  actor.n += 1; ride.hold(walker, { eyeHeight: 1.6 });
  assert.equal(walker.state.n, actor.seat().n);
  // Aboard, the team is the nearest thing to work, and it offers the reins.
  assert.equal(engine.nearest(walker.state.e, walker.state.n, 0), h.thing);
  assert.deepEqual(ids(h.thing), ['take-reins', 'stop', 'get-down']);
  // Walking keys do not walk while aboard and not driving.
  const intent = { forward: 1, strafe: 1, rise: 0, sprint: true };
  assert.equal(ride.drive(intent), true);
  assert.deepEqual([intent.forward, intent.strafe, intent.sprint], [0, 0, false]);
  assert.equal(actor.inputs.length, 0, 'no drive input while the coachman has the reins');
  // A second team is not worked from the first one's seat.
  const other = makeActor({ id: 'other', row: brougham });
  const o = registerTransportInteraction(engine, other, { ride });
  assert.deepEqual(ids(o.thing), []);
  o.dispose();

  // 3. The reins: takeReins, the keys become throttle and steering (+1 right), handBack.
  assert.equal(engine.act(h.thing, 'take-reins').ok, true);
  engine.update(0);
  assert.deepEqual(actor.calls.at(-1), ['takeReins']);
  assert.equal(ride.driving, true);
  assert.deepEqual(ids(h.thing), ['hand-back', 'get-down']);
  // Taking the reins of a team on its round does not brake it: it walks on at its pace (1.3 of
  // the 1.5 m/s cap) until told otherwise.
  ride.drive({ forward: 0, strafe: 0 });
  assert(Math.abs(actor.inputs.at(-1).throttle - 1.3 / DRIVE_SPEED_CAP_M_S) < 1e-9, 'the reins taken, the team walks on as it was');
  assert.equal(actor.inputs.at(-1).steer, 0);
  const keys = { forward: 1, strafe: -1, rise: 0, sprint: false };
  ride.drive(keys);
  assert.deepEqual(actor.inputs.at(-1), { throttle: 1, steer: -1 }, 'W+A on the keys: full pace, turning');
  assert.deepEqual([keys.forward, keys.strafe], [0, 0], 'and they do not walk the visitor off the seat');
  ride.drive({ forward: 0, strafe: 0.5 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 1, steer: 0.5 }, 'let go, the team walks on at its pace');
  ride.drive({ forward: 0.6, strafe: 0 });
  ride.drive({ forward: 0, strafe: 0 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 0.6, steer: 0 }, "a stick's tilt is the pace it keeps");
  // A diagonal thumb: within 45° of straight ahead it sets the pace by how far it is pushed
  // (not by its forward share); held mostly sideways it only steers, the pace left as it was.
  ride.drive({ forward: 0.6, strafe: 0.5 });
  assert(Math.abs(actor.inputs.at(-1).throttle - Math.hypot(0.6, 0.5)) < 1e-9 && actor.inputs.at(-1).steer === 0.5, 'a forward-dominant stick: the pace is its push');
  ride.drive({ forward: 1, strafe: 0 });
  ride.drive({ forward: 0.38, strafe: 0.92 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 1, steer: 0.92 }, 'a sideways stick steers; the team keeps its full pace');
  ride.drive({ forward: -0.3, strafe: -0.9 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 1, steer: -0.9 }, 'sideways and a little back still only steers');
  ride.drive({ forward: 0, strafe: 0 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 1, steer: 0 });
  ride.drive({ forward: -1, strafe: 3 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: -1, steer: 1 }, 'a pull back is whoa (S+D too); steering clamped');
  ride.drive({ forward: -0.5, strafe: 0.2 });
  assert.equal(actor.inputs.at(-1).throttle, -1, 'held back, it is held back (standing, the team backs)');
  ride.drive({ forward: 0, strafe: 0 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 0, steer: 0 }, 'after whoa it stands');
  assert.equal(engine.act(h.thing, 'hand-back').ok, true);
  engine.update(0);
  assert.deepEqual(actor.calls.at(-1), ['handBack']);
  assert.deepEqual(ids(h.thing), ['take-reins', 'get-down'], 'while the driver takes it back, the reins can be taken again');
  actor.mode = 'route';

  // 4. Get down from under the reins: the team is pulled up first, then the visitor lands
  // on a clear stand beside it, and the driver takes his team home.
  engine.act(h.thing, 'take-reins'); engine.update(0);
  actor.speed_m_s = 1.3; const before = actor.inputs.length, handBacks = actor.calls.filter(c => c[0] === 'handBack').length;
  assert.equal(engine.act(h.thing, 'get-down').ok, true);
  assert.equal(ride.pullingUp, true);
  for (let i = 0; i < 10 && ride.phase === 'seated'; i++) { ride.drive({ forward: 1, strafe: 0 }); engine.update(0.05); }
  const pulled = actor.inputs.slice(before);
  assert(pulled.length >= 3 && pulled.every(input => input.steer === 0 && (input.throttle === -1 || input.throttle === 0)), 'pulled up, whatever keys are held');
  assert.equal(pulled[0].throttle, -1, 'whoa while it goes on');
  assert.equal(actor.speed_m_s, 0);
  assert.equal(ride.phase, 'alighting');
  ride.drive({ forward: -1, strafe: 1 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 0, steer: 0 }, 'climbing down, nothing is held back: a standing team is never backed under them');
  tick(engine, RIDE_S.alight + 0.1, 0.05, () => ride.hold(walker, { eyeHeight: 1.6 }));
  assert.equal(ride.actor, null);
  assert.deepEqual(boarded.at(-1), ['team', false, 'get-down']);
  assert.equal(actor.calls.filter(c => c[0] === 'handBack').length, handBacks + 1, 'the reins go back with the visitor');
  assert.equal(actor.mode, 'returning');
  ride.hold(walker, { eyeHeight: 1.6 });
  const [le, ln] = walker.teleports.at(-1);
  const box = transportEnvelope({ e: 0, n: actor.n, yaw: Math.PI }, brougham.envelope_local_xz_m);
  const inside = box.reduce((acc, p, i) => {
    const q = box[(i + 1) % 4];
    return acc && ((q[0] - p[0]) * (ln - p[1]) - (q[1] - p[1]) * (le - p[0])) >= 0;
  }, true) || box.reduce((acc, p, i) => {
    const q = box[(i + 1) % 4];
    return acc && ((q[0] - p[0]) * (ln - p[1]) - (q[1] - p[1]) * (le - p[0])) <= 0;
  }, true);
  assert.equal(inside, false, 'the visitor lands outside the team, not under it');
  assert(Math.abs(le) > 1 && Math.abs(ln - actor.n) < 3, 'beside it, not ahead of or behind it');
  assert.deepEqual(ids(h.thing).includes('climb-up'), true, 'down again, Climb up is offered again');
  h.dispose();
  console.log('transport boarding: climb up stops then resumes, held on the seat, reins/hand back, get down pulls up and lands beside the team PASS');
}

// 5. Get down from a team on its own round: it stops at once, the visitor gets down, it goes on.
{
  const engine = createInteractions(), walker = makeWalker(2.5, 0.5);
  const actor = makeActor({ row: brougham });
  const ride = createTeamRide({ visitor: () => ({ e: walker.state.e, n: walker.state.n, y: 1.6, bearing: 0 }),
    standFor: a => boardStand({ actor: a, row: brougham }), groundAt: () => 0 });
  const h = registerTransportInteraction(engine, actor, { ride });
  engine.act(h.thing, 'climb-up'); tick(engine, RIDE_S.climb + 0.3);
  assert.equal(ride.phase, 'seated'); assert.equal(actor.state, 'moving');
  actor.calls.length = 0;
  engine.act(h.thing, 'get-down');
  assert.deepEqual(actor.calls[0], ['stop', 'alighting'], 'a moving team pulls up first');
  tick(engine, RIDE_S.alight + 0.2, 0.05, () => ride.hold(walker, { eyeHeight: 1.6 }));
  ride.hold(walker, { eyeHeight: 1.6 });
  assert.equal(ride.actor, null);
  assert.equal(walker.teleports.length, 1);
  assert.deepEqual(actor.calls.at(-1), ['resume'], 'then it goes on round without them');
  // The stand is clear of the road ahead too, so the team is not held by them there.
  const [e, n] = walker.teleports[0];
  const clear = createTransportClearance({ footprints: () => [], visitor: () => ({ e, n }), envelope_local_xz_m: brougham.envelope_local_xz_m });
  assert.equal(clear(actor.previewAt(actor.n), actor.previewAt(actor.n + 10)), true);
  h.dispose();
}

// 6. A building beside the team: the stand is never inside it.
{
  const actor = makeActor({ row: brougham });
  const house = (e, n) => e < -1 && e > -20;   // a wall along the west side of the road
  const stand = boardStand({ actor, row: brougham, blockedAt: house });
  assert(stand && stand.e > 0, 'the visitor gets down on the open side');
  assert.equal(boardStand({ actor, row: brougham, blockedAt: () => true }), null, 'nowhere to stand: null, never a stand in a wall');
  console.log('transport boarding: get down from a round resumes it, the stand clears its road and is never in a building PASS');
}

// 7. Never stranded: a team gone, hidden or flown from puts the visitor down (or lets them fly).
{
  const setup = () => {
    const engine = createInteractions(), walker = makeWalker(2.5, 0.5);
    const actor = makeActor({ row: brougham });
    const ride = createTeamRide({ visitor: () => ({ e: 2.5, n: 0.5, y: 1.6, bearing: 0 }),
      standFor: a => boardStand({ actor: a, row: brougham }), groundAt: () => 0 });
    const h = registerTransportInteraction(engine, actor, { ride });
    engine.act(h.thing, 'climb-up'); tick(engine, RIDE_S.climb + 0.3);
    assert.equal(ride.phase, 'seated');
    return { engine, walker, actor, ride, h };
  };
  {
    const { walker, actor, ride } = setup();
    actor.visible = false;               // Carriages hidden, Confidence hiding reconstructed, put up for the night
    assert.equal(ride.hold(walker, { eyeHeight: 1.6 }), false);
    assert.equal(ride.actor, null);
    assert.equal(walker.teleports.length, 1, 'put down beside it');
    assert.equal(walker.state.eyeY, 1.6);
  }
  {
    const { walker, actor, ride, h } = setup();
    actor.takeReins();
    actor.disposed = true;               // a tier or year change retires the team
    h.dispose();
    assert.equal(ride.actor, null);
    assert(!actor.calls.some(c => c[0] === 'handBack'), 'a retired team is not driven again (its actor restores it onto its round)');
    ride.hold(walker, { eyeHeight: 1.6 });
    assert.equal(walker.teleports.length, 1);
  }
  {
    const { engine, walker, actor, ride, h } = setup();
    // Another team loading re-registers every team: the visitor stays aboard.
    h.dispose();
    assert.equal(ride.aboard, actor);
    const again = registerTransportInteraction(engine, actor, { ride });
    assert.deepEqual(ids(again.thing), ['take-reins', 'stop', 'get-down']);
    walker.state.flying = true;          // F: they take to the air from the seat
    assert.equal(ride.hold(walker, { eyeHeight: 1.6 }), false);
    assert.equal(ride.actor, null); assert.equal(walker.teleports.length, 0);
    again.dispose();
  }
  {
    const { engine, actor, ride, h } = setup();
    // A team re-registered mid-climb finishes the climb rather than hanging half way.
    ride.release('test', { land: false });
    engine.act(h.thing, 'climb-up'); tick(engine, RIDE_S.climb / 3);
    assert.equal(ride.phase, 'climbing');
    h.dispose();
    assert.equal(ride.phase, 'seated');
    assert.equal(ride.aboard, actor);
  }
  console.log('transport boarding: hidden, retired, re-registered and free-fly never strand the visitor PASS');
}

// 8. Reduced motion: aboard, the team stands, and the key says so.
{
  const engine = createInteractions(), said = [];
  engine.on((thing, event) => { if (event === 'done') said.push(thing.last?.said?.(thing)); });
  const actor = makeActor({ row: brougham });
  const ride = createTeamRide({ visitor: () => ({ e: 2.5, n: 0.5, y: 1.6, bearing: 0 }), reducedMotion: () => true });
  const h = registerTransportInteraction(engine, actor, { ride });
  engine.act(h.thing, 'climb-up'); tick(engine, RIDE_S.climb + 0.3);
  assert.equal(actor.state, 'stopped', 'not resumed under reduced motion');
  assert.match(said.at(-1), /reduced motion/);
  h.dispose();
}

// 8b. Reins taken from a team that stands: it stands until told to walk on. The ride bar's
// name is the row's short ride_name, else the team's own name; the bar lets a thumb through.
{
  const engine = createInteractions(), walker = makeWalker(2.5, 0.5);
  const actor = makeActor({ row: brougham });
  actor.state = 'stopped'; actor.speed_m_s = 0;
  const ride = createTeamRide({ visitor: () => ({ e: 2.5, n: 0.5, y: 1.6, bearing: 0 }) });
  const h = registerTransportInteraction(engine, actor, { ride, rideName: brougham.ride_name });
  assert.equal(h.thing.rideName, "Hans's brougham");
  assert.equal(registerTransportInteraction(createInteractions(), makeActor({ id: 'plain', row: brougham }), { ride: createTeamRide() }).thing.rideName,
    'Carriage driver', 'no ride_name: the team\'s own name');
  engine.act(h.thing, 'climb-up'); tick(engine, RIDE_S.climb + 0.1, 0.05, () => ride.hold(walker, { eyeHeight: 1.6 }));
  assert.equal(ride.phase, 'seated'); assert.equal(h.thing.running, null);
  actor.state = 'stopped'; actor.speed_m_s = 0;
  engine.act(h.thing, 'take-reins'); engine.update(0);
  actor.speed_m_s = 0;
  ride.drive({ forward: 0, strafe: 0.4 });
  assert.deepEqual(actor.inputs.at(-1), { throttle: 0, steer: 0.4 }, 'a standing team stays standing under the reins');
  h.dispose();
  const main = await readFile(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  assert.match(main, /interactions\.get\(`driver:\$\{a\.id\}`\)\?\.rideName/, 'main.js paints the ride bar with the short name');
  const css = await readFile(new URL('../renderers/web/css/drawer.css', import.meta.url), 'utf8');
  assert.match(css, /\.travel-banner\[data-kind="ride"\] \{ pointer-events: none; \}/, 'the ride bar passes a thumb through to the stick');
  assert.match(css, /\.travel-banner\[data-kind="ride"\] \.tb-stop \{ pointer-events: auto; \}/, 'its Get down key still takes a touch');
  console.log('transport boarding: the reins keep the pace the team had, a sideways stick only steers, the climb leaves nothing running, the bar names the team short PASS');
}

// 9. The team the visitor rides is not stopped by them; every other team still is.
{
  const ride = createTeamRide({ visitor: () => ({ e: 0, n: 0, y: 1.6, bearing: 0 }) });
  const actor = makeActor({ row: brougham });
  const visitor = () => ({ e: 0, n: 0.5 });
  const own = createTransportClearance({ footprints: () => [], visitor: riderOffTeam(ride, 'team', visitor), envelope_local_xz_m: brougham.envelope_local_xz_m });
  const theirs = createTransportClearance({ footprints: () => [], visitor: riderOffTeam(ride, 'other', visitor), envelope_local_xz_m: brougham.envelope_local_xz_m });
  const pose = { e: 0, n: 0, yaw: Math.PI };
  assert.equal(own(pose, pose), false, 'on foot in its road, the visitor holds it');
  ride.climb(actor, 0);
  assert.equal(own(pose, pose), true, 'aboard (from the first moment of the climb), they do not');
  assert.equal(theirs(pose, pose), false);
  assert.equal(theirs.lastBlocker, 'visitor');
  console.log('transport boarding: reduced motion stands the team; the rider is no obstruction to their own team only PASS');
}
