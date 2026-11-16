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

// ---- T-3553 (the owner, 2026-11-16: "make sure there are interactive people"): a castmate is met.
{
  const fig = (instance) => { const a = { instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, path: null, greets: 0,
    root: { visible: true }, body: {}, person: instance.person_id ? { id: instance.person_id, name: 'Mr. A' } : null, proxy: { name: 'proxy' },
    setState() {}, place() {}, setIndoors(v) { a.indoors = v; }, turnTo(h) { a.heading = h; },
    setPosture(kind) { a.posture = kind === 'stand' ? null : { kind }; }, walkPath(pts) { a.path = pts; return true; },
    actions: { talking: false, setTalk(v) { a.actions.talking = v; }, greet() { a.greets++; } }, update() {}, dispose() { a.disposed = true; } };
    return a; };
  const humans = { shown: true, get: (id) => ({ instance: { id: `hi_${id}`, scene: '1812', appearance: { asset_id: 'x' } }, person: { id, name: 'Mr. A' } }), createActor: (i) => fig(i) };
  const st = createJauntStage({ humans, eye: () => ({ x: 0, y: 1.6, z: 0 }) });
  st.sync({ id: 'm', stage: { cast: [{ person: 'a', at: [0, 10], heading: 90 }, { extra: 'w', dress: 'potawatomi_man_1812', name: 'One of the warriors; name not recorded', at: [3, 10], pose: 'kneel' }] } }, { arrived: true });
  const [a, w] = st.cast;
  const ray = (target) => ({ intersectObjects: (objects) => (objects.includes(target.proxy) ? [{ object: target.proxy, distance: 9, point: null }] : []) });
  const hitA = st.pick(ray(a));
  assert.equal(hitA.personId, 'a'); assert.equal(hitA.name, 'Mr. A'); assert.equal(hitA.distance, 9);
  assert.equal(st.meet(hitA, { e: 0, n: 0 }), true, 'one standing free greets the visitor');
  assert.equal(a.greets, 1); assert.equal(Math.round(a.heading), 180, 'turned to the visitor');
  const hitW = st.pick(ray(w));
  assert.equal(hitW.personId, null); assert.equal(hitW.name, 'One of the warriors; name not recorded', 'an unnamed figure says who it stands for');
  assert.equal(st.meet(hitW, { e: 0, n: 0 }), false, 'one kneeling for the scene keeps their pose');
  assert.equal(w.greets, 0);
  w.indoors = true;
  assert.equal(st.pick(ray(w)), null, 'one out of sight is not met');
  assert.equal(st.pick(null), null);
  st.release();
}
console.log('PASS a castmate is picked as anyone of the town is, and one standing free turns and greets the visitor');

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
      for (const b of c.beats || []) assert.deepEqual(Object.keys(b).filter((k) => !['t', 'walk', 'pace', 'heading', 'face', 'pose', 'ease', 'talk', 'greet', 'hide', 'show', 'place', 'torch', 'ignite', 'cross', 'borne'].includes(k)), [],
        `${where}: a beat is only a move, a turn, a pose, a word of the hand, a way in or out, a boat crossed in, a bier carried, or a torch put to a building`);
      if ((c.beats || []).some((b) => b.torch || b.ignite)) assert.ok(st.stage.fire, `${where}: a torch only where the stop burns`);
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

// ---- the burning of the fort (the owner, 2026-11-16: "witness and also join the party and help
// light Fort Dearborn on fire"): the morning after the battle, before the gate; the young men of
// the gathering put brands to the buildings, the visitor may too, the magazine stands; and from
// Ouilmette's house an hour later the fort is still burning across the river. In both tellings.
for (const name of ['battle-of-fort-dearborn', 'battle-of-fort-dearborn-adults']) {
  const jaunt = read(`data/jaunts/${name}.json`), ids = jaunt.stops.map((x) => x.id);
  const burn = jaunt.stops.find((x) => x.id === 'the-burning');
  assert.ok(burn && ids.indexOf('the-burning') === ids.indexOf('kinzie-house') + 1 && burn.next === 'war-party', `${name}: the burning comes the morning after the battle, before the war party and the search at Ouilmette's`);
  assert.equal(burn.date, '1812-08-16', `${name}: on the 16th (Heald: 'The next morning')`);
  const fire = burn.stage.fire;
  assert.ok(fire.visitor && fire.open_gates && jaunt.liberties.includes(fire.liberty), `${name}: the visitor holds a brand; the burning is a declared liberty`);
  assert.deepEqual(fire.stands, ['first_fort_dearborn_magazine'], `${name}: the brick magazine 'alone defied the fire' (Quaife)`);
  for (const id of ['first_fort_dearborn_officers_barracks', 'first_fort_dearborn_blockhouse_nw', 'first_fort_dearborn_blockhouse_se', 'first_fort_dearborn_pickets_outer', 'first_fort_dearborn_pickets_inner'])
    assert.ok(fire.burns.includes(id), `${name}: ${id} burns`);
  assert.ok(!fire.burns.some((id) => /outer_(factory|agents|stable|bake|armourers|merchants|interpreters)/.test(id)), `${name}: the outbuildings no account burns are left standing`);
  const lit = burn.stage.cast.flatMap((c) => (c.beats || []).filter((b) => b.ignite).map((b) => ({ c, b })));
  assert.ok(lit.length >= 8 && new Set(lit.map((x) => x.b.ignite)).size >= 8, `${name}: the brands go to the barracks, the blockhouses and the pickets (${lit.length})`);
  for (const { c, b } of lit) {
    assert.ok(fire.burns.includes(b.ignite), `${name}: ${c.extra} lights what burns`);
    assert.ok((c.beats || []).some((x) => x.torch === true && x.t < b.t), `${name}: ${c.extra} carries a brand to it`);
    assert.ok(!c.person, `${name}: who carried which brand is not recorded, so the men are unnamed`);
  }
  assert.ok(Math.min(...lit.map((x) => x.b.t)) < 35, `${name}: the first fire is set within the first half minute`);
  assert.ok(castFor(burn, 'light').length >= 10, `${name}: a phone keeps the men with the brands`);
  const after = jaunt.stops.find((x) => x.id === 'ouilmette').stage.fire;
  assert.ok(after && !after.visitor && after.lit.length >= 9 && after.start_s >= 60, `${name}: from Ouilmette's the fort is still burning`);
}
// The stage hands the fire its buildings and the torches their moment: a castmate's ignite lights
// the building at the brand when the motion reaches the logs; the visitor's kindle only at a stop
// that offers it, once arrived; Watch again starts the fire over; and the stop let go gives it back.
{
  const calls = [];
  const burn = { active: false, start(spec) { this.active = true; calls.push(['start', spec.burns.length]); }, ignite(id, at) { calls.push(['ignite', id, !!at]); return true; },
    kindle(at) { calls.push(['kindle', at.x]); return { lit: 'b', name: 'barracks' }; }, holdTorch(on) { this.held = on; }, update(dt) { this.t = (this.t ?? 0) + dt; },
    clear() { this.active = false; calls.push(['clear']); }, flameNow() {}, snapshot() { return { burns: [] }; } };
  const fig = (instance) => ({ instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, body: {}, root: { visible: true, position: { x: 1, y: 0, z: -2, clone() { return { ...this, set(x, y, z) { return { x, y, z }; } }; } } },
    setState() {}, place() {}, setIndoors() {}, turnTo() {}, setPosture() {}, walkPath() { return true; }, update() {}, dispose() {}, actions: { wield() {}, act(k) { calls.push(['act', k]); } } });
  const humans = { shown: true, get: () => null, createActor: (i) => fig(i) };
  const stopFire = { id: 'b', stage: { caption: 'x', liberty: 'L-x', fire: { burns: ['b'], liberty: 'L-f', visitor: true }, cast: [
    { extra: 'm', dress: 'potawatomi_man_1812', at: [1, 2], beats: [{ t: 0.2, torch: true }, { t: 1, ignite: 'b' }] }] } };
  const st = createJauntStage({ humans, parent: { add() {} }, eye: () => ({ x: 0, y: 1.6, z: 0 }), fire: { create: () => burn }, view: () => null });
  st.sync(stopFire, { arrived: false });
  assert.equal(st.kindle({ x: 5 }), null, 'no torch for the visitor before they arrive');
  st.sync(stopFire, { arrived: true });
  st.update(1.2);
  assert.deepEqual(calls.filter((x) => x[0] !== 'clear'), [['start', 1], ['act', 'kindle']], 'the brand goes to the logs at its beat');
  st.update(0.5);
  assert.ok(calls.some((x) => x[0] === 'ignite' && x[1] === 'b' && x[2]), 'and the building catches at the brand as it reaches them');
  assert.ok(burn.held === true, 'the visitor holds a brand at a stop that offers one');
  assert.deepEqual(st.kindle({ x: 5 }), { lit: 'b', name: 'barracks' }, 'and may put it to a building');
  calls.length = 0;
  st.replay();
  assert.deepEqual(calls.slice(0, 2), [['clear'], ['start', 1]], 'Watch again starts the fire over');
  st.release();
  assert.ok(!burn.active, 'the stop let go gives the buildings back');
}
console.log('PASS the burning of the fort: the brands to the buildings, the visitor\'s torch, the magazine standing, in both tellings');

// ---- doors and gates (the owner, 2026-11-16: "people appear outside doors the doors don't open
// and close"; "The fort also they vanish through the door"; "the gate is not possible to cross").
// A castmate whose walk ends at a hung door goes on through it, holding it open while near and
// letting it go once in; one shown at a door comes out of it once it has opened; a stage's
// `open_gates` stand open while it plays and shut again when it is let go.
{
  const made = [];
  const fig = (instance) => {
    const a = { instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, body: {}, path: null, walks: [],
      root: { visible: true, position: { clone() { return { x: a.e, z: -a.n }; } } },
      setState() {}, place() {}, setIndoors(v) { a.indoors = v; }, turnTo() {}, setPosture() {}, update() {}, dispose() {},
      walkPath(pts, o = {}) { a.path = pts; a.walks.push(pts.map((q) => [q.e, q.n])); a.arrive = () => { a.path = null; const q = pts.at(-1); a.e = q.e; a.n = q.n; o.onArrive?.(); }; return true; } };
    made.push(a); return a;
  };
  const humans = { shown: true, get: () => null, createActor: (i) => fig(i) };
  const leaf = { e: 0, n: 0 };
  const passage = { id: 'h:front', held: new Set(), hold(k) { this.held.add(k); }, release(k) { this.held.delete(k); }, isOpen() { return this.held.size > 0; },
    way() { const w = [{ e: 0, n: -2 }, { e: 0, n: -1 }, leaf, { e: 0, n: 0.6 }]; w.door = 1; w.leaf = leaf; return w; } };
  const gateCalls = [];
  const gates = { open(ids) { gateCalls.push(['open', ...ids]); return () => gateCalls.push(['shut', ...ids]); } };
  const stopDoors = { id: 'd', stage: { caption: 'x', liberty: 'L-x', open_gates: ['x_green:s'], cast: [
    { extra: 'in', dress: 'potawatomi_man_1812', at: [6, -6], beats: [{ t: 0.5, walk: [[0, -1.6]], hide: true }] },
    { extra: 'out', dress: 'potawatomi_man_1812', at: [0, -1.4], hidden: true, beats: [{ t: 0.5, show: true }] },
  ] } };
  const st = createJauntStage({ humans, parent: { add() {} }, eye: () => ({ x: 0, y: 1.6, z: 0 }), doors: () => ({ passages: [passage] }), gates });
  st.sync(stopDoors, { arrived: true });
  assert.deepEqual(gateCalls, [['open', 'x_green:s']], 'the stage opens its gates as it begins');
  const [inn, out] = made;
  inn.e = 6; inn.n = -6; out.e = 0; out.n = -1.4; out.indoors = true;
  st.update(0.6);
  assert.deepEqual(inn.walks.at(-1).at(-1), [0, 0.6], 'a walk ending at the door goes on in, past its leaf');
  assert.ok(inn.walks.at(-1).some(([e, n]) => e === 0 && n === -1), '... by the place before it');
  assert.ok(passage.held.size >= 1, 'the door is held for the one coming out');
  st.update(0.05);
  assert.deepEqual(out.walks.at(-1)[0], [0, 0.6], 'the one shown at the door comes out from inside it once it is open');
  assert.ok(!out.indoors, '... and is out of doors');
  out.arrive(); st.update(0.05);
  inn.e = 0; inn.n = -1.5; st.update(0.05);
  assert.ok([...passage.held].some((k) => k.endsWith(':0')), 'the one going in holds the door while near it');
  inn.arrive(); st.update(0.1);
  assert.ok(inn.indoors, 'through it, they are in');
  st.update(0.5);
  assert.equal(passage.held.size, 0, 'and the door is let go behind them');
  st.release();
  assert.deepEqual(gateCalls.at(-1), ['shut', 'x_green:s'], 'the gates shut when the stop is let go');
}
console.log('PASS a staged figure goes in and out by a swinging door, and a stop opens and shuts its gates');

// A castmate crosses in a drawn boat, sitting in it, and steps ashore on the far bank; the boat
// is laid back when the stop is let go. The dead are carried on a bier at the bearers' hands, head
// first, and set down (the owner, 2026-11-16: "he just disappears in front of your eyes"; "they
// should be carrying the body by hand").
{
  const made = [];
  const fig = (instance) => {
    const a = { instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, body: {}, path: null, standY: null,
      root: { visible: true, position: { clone() { return { x: a.e, z: -a.n }; } } }, heightAt: () => 2,
      setState() {}, place() {}, setIndoors(v) { a.indoors = v; }, turnTo() {}, setPosture(k) { a.posture = { kind: k }; }, update() {}, dispose() {},
      walkPath(pts) { a.path = pts; return true; } };
    made.push(a); return a;
  };
  const humans = { shown: true, get: () => null, createActor: (i) => fig(i) };
  let restored = 0, t = 0;
  const handle = { get done() { return t >= 3; }, seat: () => ({ e: 10, n: 20 + t, y: 3, bearing: 0 }), stand: () => [10, 40], restore() { restored++; } };
  const boats = { carry: (id) => (id === 'p' ? handle : null) };
  const props = [];
  const bier = () => { const o = { position: { set(x, y, z) { o.at = [x, y, z]; } }, rotation: { set() {} }, removeFromParent() { o.gone = true; } }; props.push(o); return o; };
  const stopBoat = { id: 'b', stage: { caption: 'x', liberty: 'L-x', cast: [
    { extra: 'k', dress: 'trader_1812', at: [10, 18], beats: [{ t: 0.1, cross: 'p' }, { t: 5, place: [10, 40], walk: [[10, 44]] }] },
    { extra: 'dead', dress: 'trader_1812', at: [0, 0], pose: 'lie', beats: [{ t: 0.1, borne: ['f1', 'f2', 'r1', 'r2'] }, { t: 4, borne: false }] },
    { extra: 'f1', dress: 'trader_1812', at: [-0.45, 1.15] }, { extra: 'f2', dress: 'trader_1812', at: [0.45, 1.15] },
    { extra: 'r1', dress: 'trader_1812', at: [-0.45, -1.15] }, { extra: 'r2', dress: 'trader_1812', at: [0.45, -1.15] },
  ] } };
  const st = createJauntStage({ humans, parent: { add() {} }, eye: () => ({ x: 0, y: 1.6, z: 0 }), boats, bier });
  st.sync(stopBoat, { arrived: true });
  const [k, dead, f1, f2, r1, r2] = made;
  [[f1, -0.45, 1.15], [f2, 0.45, 1.15], [r1, -0.45, -1.15], [r2, 0.45, -1.15]].forEach(([x, e, n]) => { x.e = e; x.n = n; });
  st.update(0.2);
  assert.ok(k.posture?.kind === 'sit' && !k.indoors && k.e === 10 && k.n === 20, 'in the boat, sitting on its seat, in sight');
  assert.equal(k.standY, 3 - 0.92, 'feet below the seat\'s eye');
  t = 1.5; st.update(0.1);
  assert.equal(k.n, 21.5, 'carried across with it');
  t = 3; st.update(0.1);
  assert.deepEqual([k.e, k.n, k.posture.kind], [10, 40, 'stand'], 'over, they stand up on the far bank');
  assert.ok(props.length === 1 && Math.abs(dead.heading - 0) < 1e-9, 'a bier is made, the body lying head forward');
  assert.ok(Math.abs(dead.n - (0 - 0.86)) < 1e-9 && Math.abs(dead.standY - (2 + 0.8)) < 0.05, `the body lies on the bier at the bearers' hands (${dead.n}, ${dead.standY})`);
  [f1, f2, r1, r2].forEach((x) => { x.n += 5; });
  st.update(0.1);
  assert.ok(Math.abs(dead.n - (5 - 0.86)) < 1e-9 && Math.abs(props[0].at[2] + 5) < 1e-9, 'it goes where they go');
  for (let i = 0; i < 60; i++) st.update(0.1);
  assert.ok(dead.standY < 2 + 0.15, `set down, it comes to the ground (${dead.standY.toFixed(2)})`);
  st.release();
  assert.ok(restored === 1 && props[0].gone, 'let go, the boat is laid back and the bier taken away');
}
console.log('PASS a castmate crosses the river in a drawn boat, and the dead are carried on a bier');

// The 1812 story jaunts' people walk through gates, never through pickets (the owner, 2026-11-16:
// "they currently walk through the pickets"; "in the murder jaunt stop 2 people walk through the
// pickets of the house in front of the house"): every staged walk crosses the fort's two rows and
// the Kinzies' green only at a gate, and only one its stop opens (or the burning's, which opens all).
{
  const fences = ['first_fort_dearborn_pickets_outer', 'first_fort_dearborn_pickets_inner', 'kinzie_house_1812_green'].map((id) => {
    const sc = read(`data/sidecars/1812/${id}.json`), a = sc.attributes, pl = sc.placement;
    assert.equal(pl.rotation_deg ?? 0, 0, `${id} is square to the grid`);
    const xs = sc.footprint.polygon.map((p) => p[0]), ys = sc.footprint.polygon.map((p) => p[1]);
    const r = { e0: pl.local_e + Math.min(...xs), e1: pl.local_e + Math.max(...xs), n0: pl.local_n + Math.min(...ys), n1: pl.local_n + Math.max(...ys) };
    const over = a.gate_overrides?.value ?? {}, gates = {};
    for (const side of a.gate_sides.value) {
      const o = over[side], along = side === 'n' || side === 's';
      const mid = along ? (r.e0 + r.e1) / 2 : (r.n0 + r.n1) / 2;
      const off = o ? o.offset_m : (a.gate_offset_m?.value ?? 0);
      gates[side] = { at: mid + off, half: (o ? o.width_m : a.gate_width_m.value) / 2 };
    }
    return { id, r, gates };
  });
  const crossings = (p, q, { r }) => {
    const out = [];
    for (const [side, v, axis] of [['s', r.n0, 1], ['n', r.n1, 1], ['w', r.e0, 0], ['e', r.e1, 0]]) {
      if ((p[axis] - v) * (q[axis] - v) >= 0) continue;
      const t = (v - p[axis]) / (q[axis] - p[axis]), x = p[1 - axis] + t * (q[1 - axis] - p[1 - axis]);
      if (axis ? x >= r.e0 && x <= r.e1 : x >= r.n0 && x <= r.n1) out.push([side, x]);
    }
    return out;
  };
  let walks = 0;
  for (const name of ['battle-of-fort-dearborn', 'battle-of-fort-dearborn-adults', 'killing-of-jean-lalime', 'killing-of-jean-lalime-adults']) {
    for (const st of read(`data/jaunts/${name}.json`).stops) {
      const g = st.stage; if (!g) continue;
      const open = new Set(g.open_gates ?? []), all = !!g.fire?.open_gates;
      for (const id of open) assert.ok(fences.some((f) => id.startsWith(`${f.id}:`)) || /^[a-z0-9_]+:[nesw]$/.test(id), `${name}/${st.id}: ${id} names a gate`);
      for (const c of g.cast) {
        let p = c.at;
        for (const b of [...(c.beats ?? [])].sort((x, y) => x.t - y.t)) {
          if (Array.isArray(b.place)) p = b.place;
          for (const q of b.walk ?? []) {
            walks++;
            for (const f of fences) for (const [side, x] of crossings(p, q, f)) {
              const gate = f.gates[side];
              assert.ok(gate && Math.abs(x - gate.at) <= gate.half - 0.05, `${name}/${st.id}: ${c.person ?? c.extra} at ${b.t} s walks through ${f.id}'s ${side} pickets at ${x.toFixed(2)}, not its gate`);
              assert.ok(all || open.has(`${f.id}:${side}`), `${name}/${st.id}: ${c.person ?? c.extra} at ${b.t} s goes through ${f.id}'s ${side} gate, which the stop leaves shut`);
            }
            p = q;
          }
        }
      }
    }
  }
  assert.ok(walks > 500, `the walks were read (${walks})`);
}
console.log('PASS the 1812 story jaunts walk through gates, never through pickets');

// ---- the adults tellings (owner, 2026-11-15: "targeted at adults and shows everything incredibly
// graphically"): each a version of its students' jaunt for the adults audience, behind its
// warning, staging the fighting with weapons in the hand; and still no child struck or fallen,
// and no blow ever aimed at one. The students' jaunts above keep their beats to moves and words.
const schema = read('data/jaunts/schema.json');
const castSchema = schema.$defs.stop.properties.stage.properties.cast.items;
const ARMS = castSchema.properties.arm.enum, ACTS = castSchema.properties.beats.items.properties.act.enum;
const WOUNDS = castSchema.properties.beats.items.properties.wound.enum;
for (const [name, base] of [['battle-of-fort-dearborn-adults', 'battle-of-fort-dearborn'], ['killing-of-jean-lalime-adults', 'killing-of-jean-lalime']]) {
  const jaunt = read(`data/jaunts/${name}.json`), student = read(`data/jaunts/${base}.json`);
  assert.equal(jaunt.version_of, base, `${name}: a version of the students' ${base}`);
  assert.equal(jaunt.audience, 'adults', `${name}: for adults`);
  assert.ok(jaunt.content_warning?.length >= 40 && !jaunt.featured, `${name}: warned, and never featured`);
  assert.ok(student.audience !== 'adults' && !('content_warning' in student), `${base}: the students' telling stays theirs`);
  assert.ok(jaunt.liberties.includes('L-1812-adult-jaunts') && jaunt.liberties.includes('L-1812-staged-jaunts-3553'), `${name}: both stagings declared`);
  assert.deepEqual(jaunt.stops.map((s) => s.id), student.stops.map((s) => s.id), `${name}: the same stops as the students'`);
  let acts = 0, shots = 0, blows = 0, wounds = 0;
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
        if (b.wound) { assert.ok(WOUNDS.includes(b.wound), `${where}: ${b.wound} is a wound`); wounds++; }
      }
      // Whoever is struck bleeds where it lands (human-blood.js); and only someone struck, fallen or scalped does.
      const who = c.person ?? c.extra;
      if (beats.some((x) => x.act === 'struck')) assert.ok(beats.some((x) => x.wound), `${where}: ${who} is struck and bleeds`);
      if (beats.some((x) => x.wound)) {
        const down = [c.pose, ...beats.map((x) => x.pose)].some((p) => p === 'fallen' || p === 'lie');
        assert.ok(down || beats.some((x) => x.act === 'struck'), `${where}: ${who} bleeds only where struck or fallen`);
      }
      if (beats.some((x) => x.wound === 'scalp')) assert.ok(beats.some((x) => x.pose === 'fallen' || x.pose === 'lie'), `${where}: only the fallen are scalped (${who})`);
      if (c.person && young.test(c.person)) {
        const poses = [c.pose, ...beats.map((x) => x.pose)].filter(Boolean);
        assert.ok(!poses.includes('lie') && !poses.includes('fallen'), `${where}: no child is shown fallen (${c.person})`);
        assert.ok(!beats.some((x) => x.act || x.arm || x.wound), `${where}: no child is struck, armed or wounded (${c.person})`);
      }
    }
  }
  assert.ok(acts >= 5 && shots >= 1 && blows >= 1, `${name}: the fighting is staged (${acts} motions, ${shots} shots, ${blows} blows)`);
  assert.ok(wounds >= 4, `${name}: and its blood (${wounds} wounds)`);
}
const gate = read('data/jaunts/killing-of-jean-lalime-adults.json').stops.find((s) => s.id === 'the-gate').stage.cast;
const lalime = gate.find((c) => c.person === 'lalime_john'), kinzie = gate.find((c) => c.person === 'kinzie_john_elder');
assert.ok(lalime.beats.some((b) => b.act === 'fire') && lalime.beats.some((b) => b.arm === 'knife'), 'at the gate Lalime fires his pistol and draws his dirk (Porthier)');
assert.ok(kinzie.beats.some((b) => b.act === 'struck') && kinzie.beats.some((b) => b.act === 'stab'), 'Kinzie is hit, closes and stabs (Hubbard; Porthier)');
assert.ok(lalime.beats.some((b) => b.pose === 'lie') && castAt(kinzie, 600).hidden, 'Lalime lies where he fell; Kinzie goes');
assert.ok(lalime.beats.filter((b) => b.wound === 'body').length >= 3 && kinzie.beats.some((b) => b.wound === 'neck'), 'Lalime stabbed with his own knife; the ball cut the side of Kinzie\'s neck (Hubbard)');
console.log('PASS the adults tellings stage the fighting behind their warning, and still never strike or fell a child');

// ---- a wound beat bleeds the one hit (human-blood.js), from the side of the castmate armed nearest
// him, and waits for a figure still loading; Watch again washes it away.
{
  const calls = [];
  const blood = { createBloodFx: () => ({ wound: (actor, kind, o) => { calls.push([actor.instance.person_id ?? 'x', kind, o.from && [o.from.x, o.from.z]]); return true; },
    update() {}, clear() { calls.push(['clear']); }, visible: true, counts: { wounded: 0 } }) };
  const made = [];
  const fig = (instance) => {
    const a = { instance, e: 0, n: 0, heading: 0, posture: null, indoors: false, disposed: false, body: instance.person_id === 'v' ? null : {},
      root: { visible: true, position: { clone() { return { x: a.e, z: -a.n }; } } },
      setState() {}, place() {}, setIndoors() {}, turnTo() {}, setPosture() {}, walkPath() { return true; }, update() {}, dispose() { this.disposed = true; } };
    made.push(a); return a;
  };
  const humans = { shown: true, get: (id) => ({ instance: { id: `hi_${id}`, scene: '1812', appearance: { asset_id: 'x' } }, person: { id } }), createActor: (i) => fig(i) };
  const fights = { id: 'f', stage: { caption: 'x', liberty: 'L-x', cast: [
    { person: 'w', at: [3, 4], arm: 'tomahawk', beats: [{ t: 1, act: 'strike', face: 'u' }] },
    { person: 'u', at: [3, 5], beats: [{ t: 1.6, act: 'struck' }, { t: 1.6, wound: 'head' }] },
    { person: 'v', at: [40, 40], beats: [{ t: 2, wound: 'body' }] },
  ] } };
  const st = createJauntStage({ humans, parent: { add() {} }, eye: () => ({ x: 0, y: 1.6, z: 0 }), blood });
  st.sync(fights, { arrived: true });
  calls.length = 0;
  const [w, u, v] = made;
  w.e = 3; w.n = 4; u.e = 3; u.n = 5; v.e = 40; v.n = 40;
  st.update(1.7);
  assert.deepEqual(calls, [['u', 'head', [3, -4]]], 'struck at 1.6 s, the blood comes from the side of the man with the tomahawk');
  st.update(0.5);
  assert.equal(calls.length, 1, 'a figure still loading bleeds once it is drawn, not before');
  v.body = {};
  st.update(0.1);
  assert.deepEqual(calls.at(-1), ['v', 'body', [3, -4]], '... and then');
  st.replay();
  assert.ok(calls.some((c) => c[0] === 'clear'), 'Watch again washes the blood away');
}
console.log('PASS a wound beat bleeds the one hit, from the armed side, once the figure is drawn');
