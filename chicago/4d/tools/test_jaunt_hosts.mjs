#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3525 (owner, 2026-11-08: "this will be the first jaunt we will show people here ... have
 * john or frances welcome you and have everyone in the house explain their roles"): a stop's
 * `hosts` come to their marks while the visitor walks to it, turn to its stand, greet the
 * visitor on arrival, and go back about their day when the visitor walks on. Node only: the
 * controller with a recording adapter, jaunt-hosts.js with stand-in figures, and the real
 * human-days.js taking a person out of their day and giving them back.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createJaunts, stopPeople, hostIds, keptPeople } from '../renderers/web/js/jaunts.js';
import { createJauntHosts, markOf } from '../renderers/web/js/jaunt-hosts.js';
import { createHumanDays } from '../renderers/web/js/human-days.js';

const fixture = id => JSON.parse(fs.readFileSync(new URL(`../data/jaunts/_fixtures/fixture-${id}.json`, import.meta.url)));

// ---- who a stop keeps: its hosts with its people; on the way from a stop, its hosts too.
const s0 = { id: 'a', hosts: [{ person: 'john', local_e: 1, local_n: 2 }] }, s1 = { id: 'b', people: ['kate'], hosts: [{ person: 'mattie', local_e: 3, local_n: 4 }] };
assert.deepEqual(hostIds(s0), ['john']);
assert.deepEqual(stopPeople(s1), ['kate', 'mattie'], 'a stop keeps its people and its hosts');
const jaunt = { stops: [s0, s1] };
assert.deepEqual(keptPeople({ jaunt, visited: [{ id: 'a' }, { id: 'b' }], stopIndex: 1, phase: 'travelling', fromStopId: 'a' }), ['kate', 'mattie', 'john'],
  'walking on, the host who sent the visitor is kept until they arrive');
assert.deepEqual(keptPeople({ jaunt, visited: [{ id: 'a' }, { id: 'b' }], stopIndex: 1, phase: 'atStop', fromStopId: 'a' }), ['kate', 'mattie']);
assert.equal(markOf({ person: 'x', local_e: 'no', local_n: 1 }), null, 'a malformed mark is no mark');
console.log('PASS a stop keeps its hosts, and the last stop\'s hosts while walking on');

// ---- the controller brings the hosts of the stop ahead, greets on arrival, lets go at the end.
{
  const walk = structuredClone(fixture('walk'));
  walk.stops[0].hosts = [{ person: 'john', local_e: 1, local_n: 2 }];
  walk.stops[1].hosts = [{ person: 'mattie', local_e: 3, local_n: 4 }];
  const calls = [];
  const hosts = { sync: (stop, o) => calls.push(['sync', stop?.id ?? null, o.arrived]), release: () => calls.push(['release']) };
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go() { return true; } };
  const c = createJaunts({ load: async () => walk, resolve: x => x, place: () => true, enter: () => true, travel,
    showMenu() {}, render() {}, openDetail() {}, closeDetail() {}, onError(e) { throw e; }, storage: null, hosts });
  await c.start(walk.id);
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[0].id, true], 'at the first stop its host greets');
  c.next();
  assert.deepEqual(calls.at(-1), ['sync', walk.stops[1].id, false], 'walking on, the next stop\'s host comes to the mark');
  const n = calls.length;
  c.straight();
  assert.equal(calls.length, n, 'the same leg again changes nothing');
  c.end();
  assert.deepEqual(calls.at(-1), ['release'], 'End lets every host go');
}
console.log('PASS the controller brings each stop\'s hosts, greets on arrival and lets them go at the end');

// ---- jaunt-hosts.js: a figure with no day is walked to the mark, turned, greets, and walked back.
const figure = (id, extra = {}) => ({
  id, personId: id, e: 0, n: 0, heading: 90, state: 'standing', path: null, indoors: false, disposed: false,
  greets: 0, attended: 0,
  walkPath(pts, { endHeading, onArrive }) { this.path = { pts, endHeading, onArrive }; this.state = 'walking'; return true; },
  arrive() { const p = this.path; this.path = null; this.e = p.pts.at(-1).e; this.n = p.pts.at(-1).n; if (p.endHeading !== null) this.heading = p.endHeading; this.state = 'standing'; p.onArrive?.(this); },
  turnTo(h) { this.heading = h; return true; }, setState(s) { this.state = s; }, setIndoors(on) { this.indoors = on; }, place() {},
  life: { attend() { figure.attended++; } }, actions: { greet() { figure.greets++; } }, ...extra,
});
figure.greets = 0; figure.attended = 0;
{
  const john = figure('john'), walker = figure('walker', { route: [{ local_e: 0, local_n: 0 }, { local_e: 9, local_n: 0 }] });
  walker.state = 'walking';
  const humans = { get: id => ({ john, walker })[id] ?? null };
  const h = createJauntHosts({ humans, visitor: () => ({ e: 0, n: 10 }), eye: () => ({ x: 0, y: 1.6, z: 0 }) });
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 } });
  assert.ok(john.path, 'he walks to his mark');
  assert.equal(figure.greets, 0, 'no greeting before the visitor arrives');
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 }, arrived: true });
  assert.equal(figure.greets, 0, 'arrived first, he greets only once he stands at the mark');
  john.arrive();
  assert.equal(john.e, 0); assert.equal(john.n, 6);
  assert.ok(figure.greets === 1 && figure.attended === 1, 'at the mark he looks at the visitor and greets');
  assert.ok(Math.abs(john.heading - 0) < 1e-9, 'turned to the visitor (due north of him)');
  h.sync([{ person: 'john', local_e: 0, local_n: 6 }], { stand: { e: 0, n: 10 }, arrived: true });
  assert.equal(figure.greets, 1, 'a stop greets once');
  // The next stop's host is a route walker: off her route to the mark, and back on it after.
  h.sync([{ person: 'walker', local_e: 4, local_n: 4 }], { stand: { e: 4, n: 8 } });
  assert.ok(john.path, 'let go, he walks back to where he was taken from');
  john.arrive();
  assert.equal(john.n, 0, 'back where he stood');
  assert.deepEqual(h.active, ['walker']);
  walker.arrive();
  h.release();
  walker.arrive();
  assert.equal(walker.state, 'walking', 'back where she left it, she walks her route again');
  assert.deepEqual(h.active, []);
}
console.log('PASS a host with no day walks to the mark, greets once there, and goes back; a route walker resumes her route');

// ---- human-days.js: a host is taken out of their day, out of the house by its door, and given back.
{
  const kate = figure('kate', { instance: { behaviour: { day: [{ spans: [
    { from: 0, to: 24, indoors: true, where: 'house', doing: 'the kitchen' }] }] } } });
  kate.indoors = true;
  const humans = { actors: [kate], isHeld: () => false };
  const doors = { structures: [{ structure: 'house', name: 'House', doors: [
    { id: 'house:back', step: { local_e: 10, local_n: 0 }, leaf: { local_e: 10, local_n: -1 }, outward_deg: 0 },
    { id: 'house:front', step: { local_e: -10, local_n: 0 }, leaf: { local_e: -10, local_n: -1 }, outward_deg: 0 }] }] };
  const days = createHumanDays({ humans, hour: () => 10, date: () => '1904-04-15', doors, visitor: () => ({ e: 9, n: 8 }) });
  days.update(0.1);
  assert.equal(kate.indoors, true, 'her day has her in');
  assert.deepEqual(days.host('kate', { e: 9, n: 5 }, { heading: 0, onArrive: () => { kate.met = true; } }), { ok: true });
  assert.equal(kate.indoors, false, 'she comes out');
  assert.deepEqual([kate.path.pts[0].e, kate.path.pts[0].n], [10, 0], 'by the door nearest her mark');
  assert.equal(days.isHosted(kate), true);
  kate.arrive();
  assert.ok(kate.met && kate.e === 9 && kate.n === 5, 'and stands at it');
  for (let i = 0; i < 5; ++i) days.update(0.1);
  assert.equal(kate.path, null, 'her day leaves a host alone');
  assert.equal(days.host('nobody', { e: 0, n: 0 }).ok, false);
  assert.equal(days.unhost('kate'), true);
  days.update(0.1);
  assert.ok(kate.path, 'let go, she walks back to the house');
  assert.equal(kate.path.pts.at(-1).e, 10, 'to its nearest door');
  assert.equal(days.isHosted(kate), false);
}
console.log('PASS human-days takes a host out of her day, out by the nearest door, and gives her back');
console.log('JAUNT HOSTS PASS');
