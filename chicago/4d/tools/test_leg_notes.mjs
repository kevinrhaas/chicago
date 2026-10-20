#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { passingPlaces, legContext, claimPresentation } from '../renderers/web/js/jaunt-context.js';
import { createJaunts } from '../renderers/web/js/jaunts.js';
import { createTravel } from '../renderers/web/js/travel.js';
const read = file => JSON.parse(fs.readFileSync(new URL(`../${file}`, import.meta.url)));
const place = id => { const r = read(`data/sidecars/1835/${id}.json`); return { id, label: r.name, point: { e: r.placement.local_e, n: r.placement.local_n } }; };
const ids = ['green_tree_tavern', 'wolf_point_tavern', 'south_branch_raft_bridge', 'sauganash_hotel'];
const [green, wolf, bridge, sauganash] = ids.map(place);
// Explicit route fixture using scene positions, not a claim that A* always takes it.
const points = [[green.point.e, green.point.n], [wolf.point.e + 10, wolf.point.n - 10],
  [wolf.point.e + 10, wolf.point.n + 10], [wolf.point.e - 40, wolf.point.n + 10],
  [wolf.point.e - 40, bridge.point.n - 10], [bridge.point.e + 40, bridge.point.n - 10], [sauganash.point.e, sauganash.point.n]];
const passed = passingPlaces(points, ids.map(place), { exclude: [green.id, sauganash.id] });
assert.deepEqual(passed.map(p => p.id), [wolf.id, bridge.id]);
assert.deepEqual(passed.map(p => p.side), ['on your left', 'on your left']);
assert.deepEqual(passingPlaces([[0, 0], [100, 0]], [{ id: 'edge', point: { e: 50, n: -20 } }, { id: 'far', point: { e: 50, n: 20.01 } }]).map(p => [p.id, p.side]), [['edge', 'on your right']]);
// T-2946: walking south on the west walk of Prairie past Glessner. Its walls are 6 m west of
// the walk (on the right); the spot a ride frames it from is across the avenue, east of the
// walk, which used to read "on your left". The coach house on the alley is 45 m back and is
// a minor building: never a road note. A house across the avenue is 30 m off: not passed.
const south = [[0, 40], [0, -40]];
const box = (e0, n0, e1, n1) => [[e0, n0], [e1, n0], [e1, n1], [e0, n1]];
const glessner = { id: 'glessner_house', label: 'Glessner House, 1800 Prairie', point: { e: -21, n: 0 }, outline: box(-36, -15, -6, 15), stand: { e: 12, n: 0 } };
const coach = { id: 'coach', label: 'Coach house', point: { e: -55, n: 0 }, outline: box(-60, -5, -50, 5), minor: true };
const across = { id: 'across', label: 'Across', point: { e: 45, n: 0 }, outline: box(30, -10, 60, 10) };
assert.deepEqual(passingPlaces(south, [glessner, coach, across]).map(p => [p.id, p.side, Math.round(p.distance)]), [['glessner_house', 'on your right', 6]]);
assert.deepEqual(passingPlaces(south, [{ ...glessner, point: glessner.stand, outline: undefined }]).map(p => p.side), ['on your left'], 'the old framing point would read left');
assert.deepEqual(passingPlaces([[-50, 20], [50, 20]], [{ ...glessner, outline: box(-36, -15, -6, 15) }]).map(p => p.side), ['on your right'], 'eastbound on its north street, the house is on the right');
const note = legContext({ stops: [{ id: 'a' }, { id: 'b' }] }, 'a', 'b', south, [glessner], []);
assert.equal(note.lines[0].text, 'Passing Glessner House, 1800 Prairie, on your right.');
assert.equal(passingPlaces([[0, 0], [0, 0]], ids.map(place)).length, 0);
assert.equal(new Set(passed.map(p => p.id)).size, passed.length);
const doc = read('data/jaunts/_fixtures/fixture-walk.json');
let active, mode = 'horse', openedSignal, late, renders = 0;
const travel = { get mode() { return mode; }, setMode(m) { mode = m; },
  go(target, hooks) { active = hooks; hooks.onRoute({ ...hooks.token, points });
    if (mode === 'instantly') hooks.onArrive(hooks.token); return true; },
  stop(reason) { const old = active; active = null; old?.onStop({ ...old.token, reason }); } };
const controller = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true,
  travel, render() { renders++; }, showMenu() {}, closeDetail() {}, onError: e => { throw e; }, storage: null,
  estimate: () => ({ seconds: 120 }), contextForRoute: (s, r) => legContext(s.jaunt, s.fromStopId, s.visited[s.stopIndex].id, r.points, ids.map(place)),
  openDetail: async (link, { signal }) => { openedSignal = signal; await new Promise(resolve => { late = resolve; }); },
});
await controller.start('walk'); controller.next();
const before = structuredClone(controller.state), ride = active;
assert(controller.detail({ kind: 'source', id: 'test' })); await Promise.resolve();
assert.equal(controller.state.phase, 'detail'); assert.equal(active, null);
ride.onArrive(ride.token); assert.equal(controller.state.phase, 'detail');
assert.equal(controller.next(), false, 'reading during travel cannot commit a stop not yet reached');
for (let second = 0; second < 120; second++) assert.deepEqual(controller.state.vars, before.vars);
assert.deepEqual(controller.state.events, before.events); assert.deepEqual(controller.state.estimate, before.estimate);
controller.returnFromDetail(); assert.equal(openedSignal.aborted, true); assert.equal(controller.state.phase, 'travelling');
const returned = controller.state; late(); await Promise.resolve(); assert.equal(controller.state, returned);
controller.detail({ kind: 'person', id: 'test' }); await Promise.resolve();
controller.end(); const endRenders = renders; late(); await Promise.resolve();
assert.equal(controller.state.jaunt, null); assert.equal(openedSignal.aborted, true); assert.equal(renders, endRenders);
ride.onRoute({ ...ride.token, points }); assert.equal(renders, endRenders, 'retired route cannot consult an ended outing');
await controller.start('walk'); controller.next(); controller.straight();
assert.equal(controller.state.phase, 'atStop'); assert(controller.state.context.lines.length <= 2);
const walker = { state: { e: 0, n: 0, flying: false }, resettle() {} };
const flight = createTravel({ walker, intent: {}, settings: {}, structurePosition: () => ({ e: 100, n: 0 }),
  teleport: () => true, frame: () => true, setFly() {} });
let routeSeen = false, arrived = false;
flight.setMode('fly'); assert(flight.go({ kind: 'structure', id: 'test' }, { token: {}, onRoute: r => { routeSeen = true; assert.deepEqual(r.points, [[0, 0], [100, 0]]); } }));
assert(routeSeen); assert.equal(flight.state.phase, 'ascending'); flight.stop();
flight.setMode('instantly'); flight.go({ kind: 'structure', id: 'test' }, { token: {}, onRoute: () => { routeSeen = true; }, onArrive: () => { arrived = true; } });
assert(arrived);
assert.equal(claimPresentation({ confidence: 'reconstructed', speaker: 'A named person', text: 'Invented quotation' }).text, 'Unverified attribution withheld.');
assert.equal(claimPresentation({ confidence: 'attested', text: 'A documented claim' }).label, '[DOC]');
console.log('LEG NOTES PASS — order, side, boundary, pause, resources, cancellation, fly/instant and attribution');
