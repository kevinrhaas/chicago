#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { emptyState, reduce, currentStop, choicesFor, choiceStatus, choiceConsequence, resourceSummary,
  replaySession, createJaunts, SESSION_KEY, routeStops, legMode } from '../renderers/web/js/jaunts.js';

const fixture = id => JSON.parse(fs.readFileSync(new URL(`../data/jaunts/_fixtures/fixture-${id}.json`, import.meta.url)));
const shopping = fixture('shopping'), tavern = fixture('tavern'), plain = fixture('walk'), branch = fixture('branch');
const arrive = s => reduce(s, { type: 'ARRIVE', session: s.session, leg: s.leg });
const start = (jaunt, session = 1) => arrive(reduce(emptyState(), { type: 'START', jaunt, session }));
const chooseNext = (s, id, eventId) => arrive(reduce(reduce(s, { type: 'CHOOSE', id }), { type: 'NEXT', eventId }));
let tests = 0;
async function test(name, fn) { await fn(); ++tests; console.log(`PASS ${name}`); }

await test('three mechanic fixtures compile and the walker reaches every path', () => {
  const compiled = spawnSync('python3', ['tools/compile_jaunts.py', '--source', 'data/jaunts/_fixtures', '--output', '/tmp/c4d-jaunt-fixtures'], { encoding: 'utf8' });
  assert.equal(compiled.status, 0, compiled.stderr); assert.match(compiled.stdout, /JAUNTS PASS — 4 jaunts/);
  for (const id of ['fixture-shopping', 'fixture-tavern', 'fixture-walk']) {
    const run = spawnSync(process.execPath, ['tools/play_jaunt.mjs', id, '--all-paths'], { encoding: 'utf8' });
    assert.equal(run.status, 0, run.stderr); assert.match(run.stdout, /endings: .*effects committed: .*keepsakes awarded:/);
  }
  const deadDoc = structuredClone(plain), deadPath = `/tmp/c4d-jaunt-dead-${process.pid}.json`;
  deadDoc.id = 'fixture-dead-end'; deadDoc.stops = [structuredClone(deadDoc.stops[0])]; delete deadDoc.stops[0].next;
  fs.writeFileSync(deadPath, JSON.stringify(deadDoc));
  try {
    const dead = spawnSync(process.execPath, ['tools/play_jaunt.mjs', deadPath, '--all-paths'], { encoding: 'utf8' });
    assert.equal(dead.status, 1); assert.match(dead.stderr, /no viable move/);
  } finally { fs.unlinkSync(deadPath); }
});

await test('bounds clamp defensively and unaffordable or full choices stay disabled beside a viable path', () => {
  const extreme = structuredClone(shopping); extreme.stops[0].choices[0].effects[0].value = -500;
  let s = start(extreme); s = { ...s, choice: 'buy' }; s = reduce(s, { type: 'NEXT', eventId: 'purchase' });
  assert.equal(s.vars.money, 0); assert.equal(s.events.filter(e => e.id === 'purchase').length, 1);
  const poor = { ...start(shopping), vars: { money: 50, time: 0 } };
  assert.equal(choiceStatus(poor, currentStop(poor).choices[0]).available, false);
  assert.deepEqual(choicesFor(poor).map(c => c.id), ['browse']);
  const full = { ...start(shopping), inventory: ['parcel'] };
  assert.equal(choiceStatus(full, currentStop(full).choices[0]).available, false);
  assert.deepEqual(choicesFor(full).map(c => c.id), ['browse']);
});

await test('purchase event is committed once and Previous/Next never spends twice', () => {
  let s = chooseNext(start(branch), 'buy', 'purchase-1');
  assert.equal(s.vars.money, 75); assert.deepEqual(s.inventory, ['receipt']);
  const duplicate = reduce(s, { type: 'NEXT', eventId: 'purchase-1' }); assert.equal(duplicate, s);
  s = arrive(reduce(s, { type: 'PREV' })); s = arrive(reduce(s, { type: 'NEXT' }));
  assert.equal(s.vars.money, 75); assert.equal(s.events.filter(e => e.id === 'purchase-1').length, 1);
});

await test('Revise truncates the later route, replays resources and reaches another ending', () => {
  let s = chooseNext(start(branch), 'buy');
  s = arrive(reduce(s, { type: 'NEXT' }));
  s = arrive(reduce(s, { type: 'PREV' })); s = arrive(reduce(s, { type: 'PREV' }));
  s = reduce(s, { type: 'REVISE' });
  assert.equal(s.stopIndex, 0); assert.equal(s.vars.money, 100); assert.deepEqual(s.inventory, []);
  s = chooseNext(s, 'save'); s = arrive(reduce(s, { type: 'NEXT' }));
  assert.equal(reduce(s, { type: 'NEXT' }).outcome.id, 'saved');
});

await test('story time changes only through an explicit effect and plain outings expose no strip', () => {
  const before = start(shopping); let s = { ...before };
  s = reduce(s, { type: 'DETAIL' }); s = reduce(s, { type: 'RETURN' }); s = reduce(s, { type: 'MENU' }); s = reduce(s, { type: 'RESUME' });
  assert.equal(s.vars.time, 0); s = chooseNext(s, 'buy'); assert.equal(s.vars.time, 10);
  assert.deepEqual(resourceSummary(start(plain)), []);
  // The pilot's `preference` is branching bookkeeping: no chip, and its choices keep their own wording.
  const pilot = JSON.parse(fs.readFileSync(new URL('../data/jaunts/new-in-chicago.json', import.meta.url)));
  let p = start(pilot); while (!currentStop(p).choices?.length) p = arrive(reduce(p, { type: 'NEXT' }));
  assert.deepEqual(resourceSummary(p), []);
  for (const choice of currentStop(p).choices) assert.equal(choiceConsequence(p, choice), choice.consequence);
});

class MemoryStorage {
  constructor(value) { this.value = value; }
  getItem(key) { return key === SESSION_KEY ? this.value ?? null : null; }
  setItem(key, value) { if (key === SESSION_KEY) this.value = value; }
  removeItem(key) { if (key === SESSION_KEY) this.value = null; }
}
function rig(storage) {
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go() { return true; } };
  const docs = Object.fromEntries([shopping, tavern, plain, branch].map(doc => [doc.id, doc]));
  return createJaunts({ load: async id => docs[id], resolve: x => x,
    place: () => true, travel, enter: () => true, showMenu() {}, render() {}, openDetail() {}, closeDetail() {},
    onError(error) { throw error; }, storage });
}

await test('valid sessions replay while corrupt and version-mismatched saves are discarded with a note', async () => {
  let s = chooseNext(start(branch), 'buy');
  const valid = new MemoryStorage(JSON.stringify({ content_version: branch.content_version, jaunt: branch.id, events: s.events }));
  const resumed = rig(valid); assert.equal(await resumed.restore(), true); assert.equal(resumed.state.phase, 'menu'); assert.equal(resumed.state.vars.money, 75);
  s = arrive(reduce(s, { type: 'PREV' }));
  const history = replaySession(branch, { content_version: branch.content_version, jaunt: branch.id, events: s.events });
  assert.equal(history.stopIndex, 0); assert.equal(history.vars.money, 75);
  for (const value of ['{bad json', JSON.stringify({ content_version: 999, jaunt: branch.id, events: [] })]) {
    const storage = new MemoryStorage(value), runtime = rig(storage); assert.equal(await runtime.restore(), false);
    assert.match(runtime.state.notice, /discarded/); assert.equal(storage.value, null);
  }
  const unavailable = { getItem() { return null; }, setItem() { throw new Error('private'); }, removeItem() { throw new Error('private'); } };
  const memoryOnly = rig(unavailable); assert.equal(await memoryOnly.start(plain.id), true);
});

await test('T-3753: a stop of the route is jumped to straight, back or ahead, and replays to the same place', () => {
  // Five stops in a line, made from the walk fixture.
  const line = structuredClone(plain); line.id = 'fixture-line';
  const base = line.stops[0];
  line.stops = ['a', 'b', 'c', 'd', 'e'].map((id, i, all) => ({ ...structuredClone(base), id, next: all[i + 1] ?? '$end' }));
  let s = start(line);
  assert.deepEqual(routeStops(s).stops.map(x => `${x.id}:${x.state}`), ['a:here', 'b:ahead', 'c:ahead', 'd:ahead', 'e:ahead']);
  assert.equal(routeStops(s).open, false);
  s = reduce(s, { type: 'JUMP', stop: 'd' });
  assert.equal(s.phase, 'travelling'); assert.equal(s.instant, true, 'a jump goes as Skip the ride goes');
  assert.equal(legMode(s), 'instantly'); assert.equal(s.fromStopId, 'a', 'the leg starts where the visitor stood');
  assert.equal(currentStop(s).id, 'd'); assert.deepEqual(s.visited.map(v => v.id), ['a', 'b', 'c', 'd']);
  assert.equal(s.events.filter(e => e.type === 'decision').length, 3, 'a, b and c passed as Next stop passes them');
  s = arrive(s);
  assert.deepEqual(routeStops(s).stops.map(x => x.state), ['seen', 'seen', 'seen', 'here', 'ahead']);
  // Back to the first, then ahead to one already passed, then on to the end.
  s = arrive(reduce(s, { type: 'JUMP', stop: 'a' })); assert.equal(s.stopIndex, 0); assert.equal(s.visited.length, 4);
  s = arrive(reduce(s, { type: 'JUMP', stop: 'c' })); assert.equal(currentStop(s).id, 'c');
  assert.equal(reduce(s, { type: 'JUMP', stop: 'c' }), s, 'the stop the visitor is at is no jump');
  assert.equal(reduce(s, { type: 'JUMP', stop: 'nowhere' }), s);
  s = arrive(reduce(s, { type: 'JUMP', stop: 'e' })); assert.equal(currentStop(s).id, 'e');
  assert.equal(s.events.filter(e => e.type === 'decision').length, 4, 'd passed once, never twice');
  const saved = replaySession(line, { content_version: line.content_version, jaunt: line.id, events: s.events });
  assert.equal(saved.stopIndex, 4); assert.equal(currentStop(saved).id, 'e');
  assert.equal(reduce(s, { type: 'NEXT', closing: false }).phase, 'outcome', 'the jumped-to last stop still finishes');
  // From the flight to the start: stop 1 is Skip to the start; a later stop lands and goes on.
  const flying = reduce(emptyState(), { type: 'START', jaunt: line, session: 2 });
  assert.equal(reduce(flying, { type: 'JUMP', stop: 'a' }).phase, 'atStop');
  assert.equal(currentStop(reduce(flying, { type: 'JUMP', stop: 'c' })).id, 'c');
  // A choice decides the way on: its branches are not offered until it is made.
  let b = start(branch);
  assert.deepEqual(routeStops(b).stops.map(x => x.id), ['arrival']); assert.equal(routeStops(b).open, true);
  assert.equal(reduce(b, { type: 'JUMP', stop: 'store' }), b, 'no jump past a choice not made');
  b = reduce(b, { type: 'CHOOSE', id: 'buy' });
  assert.deepEqual(routeStops(b).stops.map(x => x.id), ['arrival', 'mail-corner', 'store']);
  b = arrive(reduce(b, { type: 'JUMP', stop: 'store' }));
  assert.equal(b.vars.money, 75, 'the choice picked is spent on the way'); assert.deepEqual(b.inventory, ['receipt']);
  assert.deepEqual(b.visited.map(v => v.id), ['arrival', 'mail-corner', 'store']);
  // A jaunt that branches twice, as authored: two stops known, then the next choice.
  const errands = JSON.parse(fs.readFileSync(new URL('../data/jaunts/errands-before-the-march.json', import.meta.url)));
  let r = reduce(start(errands), { type: 'CHOOSE', id: 'kinzies' });
  assert.deepEqual(routeStops(r).stops.map(x => x.id), ['the-order', 'kinzie', 'council']); assert.equal(routeStops(r).open, true);
});

await test('runtime fallback is visible when no declared ending matches', () => {
  const broken = structuredClone(tavern); broken.endings = [{ ...broken.endings[0], when: { var: 'sobriety', op: '<', value: 0 } }];
  const s = chooseNext(start(broken), 'abstain'); assert.equal(s.phase, 'outcome'); assert.equal(s.outcome.fallback, true);
});

assert.equal(new Set([shopping.id, tavern.id, plain.id]).size, 3);
assert.equal(replaySession(branch, { content_version: branch.content_version, jaunt: branch.id, events: chooseNext(start(branch), 'buy').events }).vars.money, 75);
console.log(`JAUNT MECHANICS PASS — ${tests} cases`);
