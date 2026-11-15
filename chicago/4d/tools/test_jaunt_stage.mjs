#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553 (owner, 2026-11-14: "place all the right people at the right scenes from history so we
 * can witness the events ... you should be able to watch the event unfold"; and for students,
 * "Build-up and aftermath": no blow, shot or blood staged, the fallen lie still after). A jaunt
 * stop's `stage` is played by its people (renderers/web/js/jaunt-stage.js). Node only: the
 * beats by themselves, the controller with a recording adapter, the stage with stand-in figures,
 * and the two staged 1812 jaunts against their people and the ruling.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createJaunts, stagedIds, crowdKept } from '../renderers/web/js/jaunts.js';
import { createJauntStage, castAt, castFor, stageIds, stageLength, teamsFor, seatAt, POSES } from '../renderers/web/js/jaunt-stage.js';
import { createTransportLoop, routeFor } from '../renderers/web/js/transport-loop.js';

const read = (p) => JSON.parse(fs.readFileSync(new URL(`../${p}`, import.meta.url)));
const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 1e-6, `${msg}: ${a} vs ${b}`);

// ---- the beats by themselves.
const stop = { id: 's', stage: { caption: 'x', liberty: 'L-x', cast: [
  { person: 'a', at: [0, 0], heading: 0, beats: [{ t: 2, walk: [[0, 10], [10, 10]], pace: 2 }, { t: 30, hide: true }] },
  { person: 'b', at: [5, 5], pose: 'kneel', tier: 'desktop', beats: [{ t: 4, pose: 'stand' }, { t: 6, place: [50, 50], show: true }] },
  { extra: 'c', dress: 'potawatomi_man_1812', at: [1, 1], hidden: true, beats: [{ t: 1, show: true }, { t: 3, talk: true }] },
  { person: 'bad', at: ['x', 0] },
] } };
assert.deepEqual(stageIds(stop), ['a', 'b', 'bad']);
assert.deepEqual(stagedIds(stop), stageIds(stop), 'the controller and the stage agree on who is staged');
assert.deepEqual(castFor(stop).map((c) => c.person ?? c.extra), ['a', 'b', 'c'], 'a castmate with no mark is left out');
assert.deepEqual(castFor(stop, 'light').map((c) => c.person ?? c.extra), ['a', 'c'], 'Light leaves out the desktop-only crowd');
let s = castAt(stop.stage.cast[0], 0);
assert.deepEqual([s.e, s.n, s.heading, s.hidden], [0, 0, 0, false]);
s = castAt(stop.stage.cast[0], 4);            // 2 s at 2 m/s
near(s.n, 4, 'half way up the first leg'); near(s.heading, 0, 'walking north');
s = castAt(stop.stage.cast[0], 9);            // 14 m along: 4 m into the second leg
near(s.e, 4, 'round the corner'); near(s.n, 10, 'round the corner'); near(s.heading, 90, 'walking east');
s = castAt(stop.stage.cast[0], 40);
assert.deepEqual([s.e, s.n, s.hidden], [10, 10, true], 'at the end of the way, and gone in');
s = castAt(stop.stage.cast[1], 5);
assert.deepEqual([s.pose, s.e], ['stand', 5], 'risen from kneeling');
s = castAt(stop.stage.cast[1], 7);
assert.deepEqual([s.e, s.n, s.hidden], [50, 50, false], 'found across the river');
s = castAt(stop.stage.cast[2], 0.5);
assert.equal(s.hidden, true); assert.equal(castAt(stop.stage.cast[2], 3.5).talk, true);
near(stageLength(stop), 30, 'the stage runs to its last beat');
console.log('PASS a castmate stands, walks its way at its pace, turns, kneels and rises, hides, shows and is found elsewhere by its beats');

// ---- the controller: built on the way, played on arrival, kept out of the crowd, released at the end.
{
  const walk = read('data/jaunts/_fixtures/fixture-walk.json');
  walk.stops[0].stage = { caption: 'c', liberty: 'L-x', cast: [{ person: 'peck_philip', at: [0, 0] }] };
  walk.stops[0].people = ['peck_philip', 'kinzie_juliette'];
  walk.stops[1].stage = { caption: 'c', liberty: 'L-x', cast: [{ person: 'kinzie_juliette', at: [0, 0] }] };
  const calls = [], held = [];
  const stage = { sync: (st, o) => calls.push(['sync', st.id, o.arrived]), replay: () => { calls.push(['replay']); return true; }, release: () => calls.push(['release']) };
  const crowd = { hold: (ids) => held.push([...ids]), restore: () => held.push('restore') };
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go() { return true; } };
  const c = createJaunts({ load: async () => walk, resolve: (x) => x, place: () => true, enter: () => true, travel,
    showMenu() {}, render() {}, openDetail() {}, closeDetail() {}, onError(e) { throw e; }, storage: null, stage, crowd });
  await c.start(walk.id);
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[0].id, true], 'at the first stop its stage plays');
  assert.deepEqual(held.at(-1), ['kinzie_juliette'], 'the staged person is not kept in the crowd as well');
  assert.deepEqual(crowdKept(c.state), ['kinzie_juliette']);
  assert.equal(c.replay(), true, 'Watch again at a stop with a stage');
  assert.deepEqual(calls.at(-1), ['replay']);
  c.next();
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[1].id, false], 'on the way, the next stage is built but not played');
  assert.equal(c.replay(), false, 'nothing to watch again on the way');
  const n = calls.length;
  c.straight();
  assert.equal(calls.length, n, 'the same leg again changes nothing');
  c.menu();
  assert.deepEqual(calls.at(-1), ['release'], 'the menu takes the stage away');
  c.resume();
  assert.equal(calls.at(-1)[0], 'sync', 'resuming brings it back');
  c.end();
  assert.deepEqual(calls.at(-1), ['release'], 'End takes it away');
}
console.log('PASS the controller builds a stop\'s stage on the way, plays it on arrival, keeps the staged out of the crowd and takes it away at the end');

// ---- the stage with stand-in figures.
{
  const made = [];
  const actor = (instance) => ({ instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, path: null, walks: [], talking: false, greets: 0,
    root: { visible: true }, lod: 1, updates: 0,
    setState() {}, place() {}, setIndoors(v) { this.indoors = v; }, turnTo(h) { this.heading = h; },
    setPosture(kind, o) { this.posture = kind === 'stand' ? null : { kind, seconds: o.seconds }; },
    walkPath(pts, o) { this.walks.push({ pts, ...o }); this.path = pts; return true; },
    actions: { setTalk(v) { this.owner.talking = v; }, greet() { this.owner.greets++; } },
    update() { this.updates++; }, dispose() { this.disposed = true; } });
  const humans = { shown: true, get: (id) => (id === 'a' ? { instance: { id: 'hi_a', scene: '1812', appearance: { asset_id: 'x' } }, person: { id: 'a' } } : null),
    createActor(instance, o) { const a = actor(instance); a.actions.owner = a; a.identity = o.identity; made.push(a); return a; } };
  const resolve = (id) => (id === 'b' ? { instance: { id: 'in_b', scene: '1812', appearance: { asset_id: 'y' } }, person: { id: 'b' } } : null);
  let tier = 'full';
  const st = createJauntStage({ humans, resolve, tier: () => tier, eye: () => ({ x: 0, y: 1.6, z: 0 }) });
  st.sync(stop, { arrived: false });
  assert.equal(made.length, 3, 'a town figure, an inside-only figure and an unnamed one; no mark, no figure');
  const [a, b, c] = st.cast;
  assert.ok(a.instance.id.startsWith('stage:s:0:a') && a.instance.person_id === 'a', 'a figure of its own, never the town\'s');
  assert.deepEqual([b.e, b.n, b.posture?.kind], [5, 5, 'kneel'], 'in place and posed before the visitor arrives');
  assert.equal(c.indoors, true); assert.equal(c.identity.kind, 'extra'); assert.equal(c.instance.appearance.asset_id, 'potawatomi_man_1812');
  st.update(5);
  assert.equal(a.walks.length, 0, 'nothing plays until the visitor arrives');
  st.sync(stop, { arrived: true });
  st.update(2.5);
  assert.equal(a.walks.length, 1, 'the walk at 2 s'); assert.equal(a.walks[0].speed, 2); assert.equal(c.indoors, false, 'shown at 1 s');
  st.update(2);
  assert.equal(b.posture, null, 'risen at 4 s'); assert.equal(c.talking, true, 'talking at 3 s');
  st.update(2);
  assert.deepEqual([b.e, b.n, b.indoors], [50, 50, false], 'found across the river at 6 s');
  assert.ok(a.updates > 0, 'every figure updated each frame');
  assert.equal(st.replay(), true);
  assert.ok(made.slice(0, 3).every((x) => x.disposed), 'Watch again builds the stage afresh');
  assert.equal(st.clock, 0);
  tier = 'light';
  st.release();
  assert.ok(made.every((x) => x.disposed), 'released, every staged figure goes');
  st.sync(stop, { arrived: true });
  assert.deepEqual(st.cast.map((x) => x.instance.person_id ?? x.instance.appearance.asset_id), ['a', 'potawatomi_man_1812'], 'a phone draws the stage without its desktop-only crowd');
  humans.shown = false;
  st.update(0.1);
  assert.ok(st.cast.every((x) => x.root.visible === false), 'Settings > Show > People still hides them');
  st.sync({ id: 'none' });
  assert.equal(st.cast.length, 0, 'a stop with no stage takes the last one away');
}
console.log('PASS the stage makes its own figures, poses them, plays their beats on arrival, plays again, and drops the desktop crowd on phones');

// ---- a stage takes a town team: its wagon goes the stage's way, its riders sit in it (T-3553).
{
  // The town's own loop, taken: 'staged' moves only by the stage, turns its wheels by the ground
  // covered, refuses the reins, and goes back on its round where it left it.
  const posed = [];
  let advanced = 0, stopped = 0;
  const assembly = { pose(p) { posed.push(p); }, advance(dt, ds) { advanced += ds; }, stop() { stopped++; }, visible() {} };
  const loop = createTransportLoop({ id: 'fort', name: 'Fort wagon', route: routeFor({ kind: 'circle', center_enu_m: [0, 0], radius_m: 18 }), assembly,
    speed_m_s: 1.3, wheelbase_m: 2.35, track_m: 1.21, root_ahead_of_rear_axle_m: 1.175, driver_local_m: [1.3, 0, 4.4],
    wheel_radii_m: [0.685, 0.685, 0.535, 0.535], heightAt: (e) => e * 0.01, steering_limit_deg: 30 });
  const round = loop.pose;
  assert.equal(loop.stage(), true); assert.equal(loop.mode, 'staged');
  assert.equal(loop.takeReins(), false, 'the visitor cannot take the reins of a team in a scene');
  assert.equal(loop.stageTo({ e: 100, n: 50, heading_deg: 180, dt: 0.1 }), true);
  assert.deepEqual([loop.pose.e, loop.pose.n], [100, 50]);
  assert.ok(Math.abs(loop.heading_deg - 180) < 1e-9, 'it faces the way the stage says');
  loop.stageTo({ e: 100, n: 48.7, heading_deg: 180, dt: 1 });
  assert.ok(Math.abs(advanced - 1.3) < 1e-9, 'its gait goes by the ground it covers');
  const wheels = loop.snapshot().wheel_rotation_rad;
  assert.ok(Math.abs(wheels[0] - 1.3 / 0.685) < 1e-9 && Math.abs(wheels[2] - 1.3 / 0.535) < 1e-9, 'the wheels turn by it');
  assert.ok(loop.pose.height >= 100 * 0.01, 'on uneven ground it rides on its highest wheel, refused nowhere');
  loop.update(5, { drawn: true });
  assert.deepEqual([loop.pose.e, loop.pose.n], [100, 48.7], 'the frame never moves a staged team');
  loop.stageTo({ e: 100, n: 48.7, heading_deg: 180, dt: 1 });
  assert.ok(stopped > 0, 'standing, the team stands');
  assert.equal(loop.unstage(), true); assert.equal(loop.mode, 'route');
  assert.ok(Math.hypot(loop.pose.e - round.e, loop.pose.n - round.n) < 1e-9, 'given back, it is on its round where it left it');

  // The stage drives a stand-in team and seats a rider on it.
  const team = { mode: 'route', disposed: false, pose: null, places: [], released: 0,
    stage() { this.mode = 'staged'; return true; }, unstage() { this.mode = 'route'; this.released++; return true; },
    stageTo(p) { this.places.push(p); this.pose = { e: p.e, n: p.n, height: 2 }; return true; } };
  let loaded = 0, ready = false;
  const made = [];
  const humans = { shown: true, get: () => null,
    createActor(instance) { const a = { instance, e: 0, n: 0, heading: 0, standY: null, root: { visible: true }, path: null,
      setState() {}, place() {}, setIndoors() {}, setPosture(kind) { this.posture = kind; }, turnTo() {}, walkPath() {}, actions: {}, update() {}, dispose() { this.disposed = true; } };
      made.push(a); return a; } };
  const stop = { id: 'col', stage: { caption: 'x', liberty: 'L-x', cast: [
    { extra: 'girl', dress: 'garrison_child_1812', name: 'A girl', at: [0, 10], pose: 'sit', ride: { team: 'fort', seat: [0.24, 0.955, 1.05] } }],
  teams: [{ team: 'fort', at: [0, 10], heading: 180, beats: [{ t: 0, walk: [[0, -20]], pace: 1.3 }] }] } };
  assert.equal(teamsFor(stop).length, 1);
  assert.ok(stageLength(stop) > 23, 'a team\'s way counts in how long the scene plays');
  const st = createJauntStage({ humans, eye: () => ({ x: 0, y: 1.6, z: 0 }), teams: { get: (id) => (ready && id === 'fort' ? team : null), load: () => { loaded++; } } });
  st.sync(stop, { arrived: false });
  st.update(0.1);
  assert.equal(loaded, 1, 'a team not yet loaded is asked for');
  ready = true;
  st.update(0.1);
  assert.equal(team.mode, 'staged', 'then taken for the scene');
  assert.deepEqual([team.places.at(-1).e, team.places.at(-1).n], [0, 10], 'standing at its mark until the visitor arrives');
  st.sync(stop, { arrived: true });
  st.update(10);
  assert.ok(Math.abs(team.places.at(-1).n - (10 - 13)) < 1e-6, 'it goes the stage\'s way at its pace');
  const girl = made[0], seat = seatAt({ e: 0, n: -3, heading: 180, height: 2 }, [0.24, 0.955, 1.05]);
  assert.ok(Math.abs(girl.e - seat.e) < 1e-9 && Math.abs(girl.n - seat.n) < 1e-9 && Math.abs(girl.standY - 2.955) < 1e-9, 'the rider sits at her seat on it');
  assert.ok(Math.abs(seat.n - (-3 - 1.05)) < 1e-9 && Math.abs(seat.e - 0.24) < 1e-9, 'a seat ahead is ahead the way the team faces; +x is its left');
  assert.equal(girl.posture, 'sit');
  assert.equal(st.snapshot().teams[0].taken, true);
  st.release();
  assert.equal(team.mode, 'route', 'the scene over, the team goes back to its round');
}
console.log('PASS a stage takes a town team for its scene: the wagon goes the stage\'s way, its riders sit in it, and it goes back to its round after');

// ---- the staged 1812 jaunts: their people, their marks, and the ruling.
const people = new Set(read('data/sidecars/1812/people.json').people.map((p) => p.id));
// A wagon's driver is drawn on the wagon all day (data/transport/driven/loops.json): never cast.
const loops = fs.readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url), 'utf8');
const young = /child|infant|_son$|_daughter$|kinzie_(john_h|ellen|maria|robert)/;
for (const name of ['battle-of-fort-dearborn', 'killing-of-jean-lalime']) {
  const jaunt = read(`data/jaunts/${name}.json`);
  const staged = jaunt.stops.filter((st) => st.stage);
  assert.ok(staged.length >= 8, `${name}: its stops are staged`);
  assert.ok(jaunt.liberties.includes('L-1812-staged-jaunts-3553'), `${name}: the staging is a declared liberty`);
  for (const st of staged) {
    const where = `${name}/${st.id}`;
    const ids = stageIds(st);
    assert.equal(new Set(ids).size, ids.length, `${where}: nobody twice in one scene`);
    for (const id of ids) assert.ok(people.has(id), `${where}: ${id} is a person of 1812`);
    for (const id of ids) assert.ok(!loops.includes(`"${id}"`), `${where}: ${id} drives a wagon in town, so would be drawn twice`);
    const cast = st.stage.cast;
    assert.ok(castFor(st, 'light').length >= Math.min(cast.length, 2), `${where}: a phone keeps the scene's people`);
    assert.ok(castFor(st, 'light').length <= 90, `${where}: a phone's stage stays within its people (${castFor(st, 'light').length})`);
    for (const c of cast) {
      const poses = [c.pose, ...(c.beats || []).map((x) => x.pose)].filter(Boolean);
      for (const p of poses) assert.ok(POSES.includes(p), `${where}: ${p} is a pose`);
      if (c.person && young.test(c.person)) assert.ok(!poses.includes('lie'), `${where}: no child is ever shown fallen (${c.person})`);
      for (const b of c.beats || []) assert.deepEqual(Object.keys(b).filter((k) => !['t', 'walk', 'pace', 'heading', 'face', 'pose', 'ease', 'talk', 'greet', 'hide', 'show', 'place'].includes(k)), [],
        `${where}: a beat is only a move, a turn, a pose, a word of the hand or a way in or out`);
    }
    assert.ok(stageLength(st) < 300, `${where}: the scene plays out in minutes`);
  }
}
const battle = read('data/jaunts/battle-of-fort-dearborn.json');
const column = battle.stops.find((x) => x.id === 'river-mouth');
const anchorEN = [1150, -490];
const passed = castFor(column).filter((c) => c.person && (c.beats || []).some((b) => b.walk)).filter((c) => {
  const a = castAt(c, 0), z = castAt(c, 600);
  return a.n > anchorEN[1] && z.n < anchorEN[1];
});
assert.ok(passed.length >= 60, `the column comes down from the north and passes the visitor (${passed.length})`);
const bank = battle.stops.find((x) => x.id === 'the-bank');
const waiting = bank.stage.cast.filter((c) => ['prone', 'kneel', 'kneel2', 'crouch', 'sit'].includes(c.pose));
assert.ok(waiting.length >= 30, 'the warriors wait behind the bank lying, kneeling and crouched');
// The column's wagons (Kevin, 2026-11-14: the women and children in wagons): the town's two
// teams, driven by their own drivers, with the children and some of the women sitting in them.
const rows = JSON.parse(loops).rows;
for (const st of [column, bank]) {
  const taken = teamsFor(st).map((x) => x.team).sort();
  assert.deepEqual(taken, ['fort_wagon_loop_1812', 'shore_road_wagon_haul_1812'], `${st.id}: both of the town's wagons go with the column`);
  for (const id of taken) assert.ok(rows.some((r) => r.id === id && r.scene === '1812' && r.person_id), `${st.id}: ${id} is a team of 1812 with its own driver`);
  const riders = st.stage.cast.filter((c) => c.ride);
  assert.ok(riders.length >= 12, `${st.id}: the children and some women ride (${riders.length})`);
  assert.ok(riders.every((c) => taken.includes(c.ride.team) && c.pose === 'sit' && !c.tier), `${st.id}: every rider sits in a wagon the stage takes, on phones too`);
  assert.ok(riders.filter((c) => young.test(c.person)).length >= 10, `${st.id}: the children are in the wagons`);
  for (const team of taken) {
    const seats = riders.filter((c) => c.ride.team === team).map((c) => c.ride.seat.join());
    assert.equal(new Set(seats).size, seats.length, `${st.id}: one rider a seat in ${team}`);
  }
}
const wagonPassed = teamsFor(column).filter((c) => castAt(c, 0).n > anchorEN[1] && castAt(c, 600).n < anchorEN[1]);
assert.equal(wagonPassed.length, 2, 'the wagons come down from the north and pass the visitor with the column');
console.log('PASS the two 1812 story jaunts stage their own people, keep them on phones, pass the column by, and never show a child fallen');

// ---- the adults tellings (owner, 2026-11-15: "targeted at adults and shows everything incredibly
// graphically"): each a version of its students' jaunt for the adults audience, behind its
// warning, staging the fighting with weapons in the hand; and still no child struck or fallen,
// and no blow ever aimed at one. The students' jaunts above keep their beats to moves and words.
const schema = read('data/jaunts/schema.json');
const castSchema = schema.$defs.stop.properties.stage.properties.cast.items;
const ARMS = castSchema.properties.arm.enum, ACTS = castSchema.properties.beats.items.properties.act.enum;
for (const [name, base] of [['battle-of-fort-dearborn-adults', 'battle-of-fort-dearborn'], ['killing-of-jean-lalime-adults', 'killing-of-jean-lalime']]) {
  const jaunt = read(`data/jaunts/${name}.json`), student = read(`data/jaunts/${base}.json`);
  assert.equal(jaunt.version_of, base, `${name}: a version of the students' ${base}`);
  assert.equal(jaunt.audience, 'adults', `${name}: for adults`);
  assert.ok(jaunt.content_warning?.length >= 40 && !jaunt.featured, `${name}: warned, and never featured`);
  assert.ok(student.audience !== 'adults' && !('content_warning' in student), `${base}: the students' telling stays theirs`);
  assert.ok(jaunt.liberties.includes('L-1812-adult-jaunts') && jaunt.liberties.includes('L-1812-staged-jaunts-3553'), `${name}: both stagings declared`);
  assert.deepEqual(jaunt.stops.map((s) => s.id), student.stops.map((s) => s.id), `${name}: the same stops as the students'`);
  let acts = 0, shots = 0, blows = 0;
  for (const st of jaunt.stops.filter((s) => s.stage)) {
    const where = `${name}/${st.id}`;
    const ids = stageIds(st);
    assert.equal(new Set(ids).size, ids.length, `${where}: nobody twice in one scene`);
    for (const id of ids) assert.ok(people.has(id), `${where}: ${id} is a person of 1812`);
    assert.ok(castFor(st, 'light').length <= 90, `${where}: a phone's stage stays within its people (${castFor(st, 'light').length})`);
    assert.ok(stageLength(st) < 300, `${where}: the scene plays out in minutes`);
    const childIds = new Set(st.stage.cast.filter((c) => c.person && young.test(c.person)).map((c) => c.person));
    for (const c of st.stage.cast) {
      const beats = c.beats || [];
      if (c.arm) assert.ok(ARMS.includes(c.arm), `${where}: ${c.arm} is a weapon`);
      for (const b of beats) {
        if (b.arm) assert.ok(ARMS.includes(b.arm), `${where}: ${b.arm} is a weapon`);
        if (b.act) { assert.ok(ACTS.includes(b.act), `${where}: ${b.act} is a motion`); acts++; }
        if (b.act === 'fire') shots++;
        if (b.act === 'strike' || b.act === 'stab') blows++;
        if (['strike', 'stab', 'fire', 'aim'].includes(b.act) && typeof b.face === 'string') assert.ok(!childIds.has(b.face), `${where}: no blow or shot is aimed at a child (${b.face})`);
      }
      if (c.person && young.test(c.person)) {
        const poses = [c.pose, ...beats.map((x) => x.pose)].filter(Boolean);
        assert.ok(!poses.includes('lie') && !poses.includes('fallen'), `${where}: no child is shown fallen (${c.person})`);
        assert.ok(!beats.some((x) => x.act || x.arm), `${where}: no child is struck or armed (${c.person})`);
      }
    }
  }
  assert.ok(acts >= 5 && shots >= 1 && blows >= 1, `${name}: the fighting is staged (${acts} motions, ${shots} shots, ${blows} blows)`);
}
const gate = read('data/jaunts/killing-of-jean-lalime-adults.json').stops.find((s) => s.id === 'the-gate').stage.cast;
const lalime = gate.find((c) => c.person === 'lalime_john'), kinzie = gate.find((c) => c.person === 'kinzie_john_elder');
assert.ok(lalime.beats.some((b) => b.act === 'fire') && lalime.beats.some((b) => b.arm === 'knife'), 'at the gate Lalime fires his pistol and draws his dirk (Porthier)');
assert.ok(kinzie.beats.some((b) => b.act === 'struck') && kinzie.beats.some((b) => b.act === 'stab'), 'Kinzie is hit, closes and stabs (Hubbard; Porthier)');
assert.ok(lalime.beats.some((b) => b.pose === 'lie') && castAt(kinzie, 600).hidden, 'Lalime lies where he fell; Kinzie goes');
console.log('PASS the adults tellings stage the fighting behind their warning, and still never strike or fell a child');
