#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { emptyState, reduce, createJaunts, canNext, legMode, shownMode, seasonOfDate, stopSeason, openingLight } from '../renderers/web/js/jaunts.js';
const fixture = id => JSON.parse(fs.readFileSync(new URL(`../data/jaunts/_fixtures/fixture-${id}.json`, import.meta.url)));
const branch = fixture('branch'), walk = fixture('walk');
const arrive = s => reduce(s, { type: 'ARRIVE', session: s.session, leg: s.leg });
const start = (jaunt = branch, session = 1) => arrive(reduce(emptyState(), { type: 'START', jaunt, session }));
let tests = 0;
async function test(name, fn) { await fn(); ++tests; console.log(`PASS ${name}`); }
await test('Previous and forward history are immutable and apply effects once', () => {
  let s = reduce(start(), { type: 'CHOOSE', id: 'buy' });
  const before = JSON.stringify(s);
  let next = arrive(reduce(s, { type: 'NEXT' }));
  assert.equal(JSON.stringify(s), before); assert.equal(next.vars.money, 75);
  next = arrive(reduce(next, { type: 'PREV' })); next = arrive(reduce(next, { type: 'NEXT' }));
  assert.equal(next.vars.money, 75); assert.deepEqual(next.inventory, ['receipt']);
  assert.equal(next.events.filter(e => e.type === 'decision').length, 1);
  assert.equal(new Set(next.events.map(e => e.id)).size, next.events.length);
});
await test('stale leg and replaced session callbacks are ignored', () => {
  let s = reduce(start(walk), { type: 'NEXT' });
  for (const type of ['ARRIVE', 'STOPPED', 'FAILED']) assert.equal(reduce(s, { type, session: s.session, leg: s.leg - 1 }), s);
  const replacement = start(walk, 2);
  assert.equal(reduce(replacement, { type: 'ARRIVE', session: s.session, leg: s.leg }), replacement);
});
await test('rapid Next creates one leg and arrival; Previous cancels mid-ride', () => {
  let s = reduce(start(walk), { type: 'NEXT' }); const leg = s.leg;
  for (let i = 0; i < 5; ++i) s = reduce(s, { type: 'NEXT' });
  assert.equal(s.leg, leg); assert.equal(s.visited.length, 2);
  const at = arrive(s); assert.equal(arrive(at), at);
  assert.equal(at.events.filter(e => e.type === 'arrival' && e.leg === leg).length, 1);
  const back = reduce(s, { type: 'PREV' }); assert.equal(back.stopIndex, 0); assert.equal(back.leg, leg + 1);
});
await test('required choices gate Next; two fixtures complete through the same reducer', () => {
  assert.equal(canNext(start()), false);
  for (const doc of [walk, branch]) {
    let s = start(doc);
    if (doc === branch) s = reduce(s, { type: 'CHOOSE', id: 'buy' });
    for (let i = 0; i < 5 && s.phase !== 'outcome'; ++i) s = arrive(reduce(s, { type: 'NEXT' }));
    assert.equal(s.phase, 'outcome'); assert.equal(s.events.filter(e => e.type === 'complete').length, 1);
  }
});
await test('Menu/Resume preserves stop and invalidates interrupted travel', () => {
  let s = reduce(start(walk), { type: 'NEXT' }); const old = s;
  s = reduce(s, { type: 'MENU' }); s = reduce(s, { type: 'RESUME' });
  assert.equal(s.stopIndex, old.stopIndex); assert(s.leg > old.leg);
  assert.equal(reduce(s, { type: 'ARRIVE', session: old.session, leg: old.leg }), s);
  s = arrive(s); s = reduce(reduce(s, { type: 'MENU' }), { type: 'RESUME' }); assert.equal(s.phase, 'atStop');
});
function rig(load = async id => id === 'walk' ? walk : branch) {
  let active, mode = 'horse', menus = 0, renders = 0;
  const retired = [];
  const travel = { get mode() { return mode; }, setMode(v) { mode = v; },
    go(target, hooks) { active = hooks; return true; },
    stop(reason) { const old = active; active = null; if (old) { retired.push(old); old.onStop({ ...old.token, reason }); } },
  };
  const controller = createJaunts({ load, resolve: x => x, place: () => true, enter: () => true, travel,
    render() { ++renders; }, showMenu() { ++menus; }, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  return { controller, travel, retired, get active() { return active; }, get menus() { return menus; }, get renders() { return renders; } };
}
await test('replacement and destroy release callbacks, timers and listeners', async () => {
  const originalTimeout = globalThis.setTimeout, originalInterval = globalThis.setInterval;
  const add = EventTarget.prototype.addEventListener, remove = EventTarget.prototype.removeEventListener;
  let timers = 0, listeners = 0;
  globalThis.setTimeout = (...args) => { ++timers; return originalTimeout(...args); };
  globalThis.setInterval = (...args) => { ++timers; return originalInterval(...args); };
  EventTarget.prototype.addEventListener = function(...args) { ++listeners; return add.apply(this, args); };
  EventTarget.prototype.removeEventListener = function(...args) { --listeners; return remove.apply(this, args); };
  try {
    const r = rig(); await r.controller.start('walk'); r.controller.next(); const old = r.active;
    assert.deepEqual(Object.keys(r.active).filter(k => k.startsWith('on')).sort(), ['onArrive', 'onRoute', 'onStop']);
    await r.controller.start('branch'); assert.equal(r.active, null);
    const state = r.controller.state; old.onArrive(old.token); assert.equal(r.controller.state, state);
    r.controller.choose('buy'); r.controller.next(); assert(r.active);
    r.controller.destroy(); assert.equal(r.active, null); assert.equal(timers, 0); assert.equal(listeners, 0);
  } finally { globalThis.setTimeout = originalTimeout; globalThis.setInterval = originalInterval;
    EventTarget.prototype.addEventListener = add; EventTarget.prototype.removeEventListener = remove; }
});
await test('End clears immediately, restores mode, and cannot be revived', async () => {
  const r = rig(); await r.controller.start('walk'); r.controller.next(); const old = r.active;
  r.controller.end(); assert.equal(r.controller.state.jaunt, null); assert.equal(r.active, null);
  assert.equal(r.travel.mode, 'horse'); assert.equal(r.menus, 1);
  old.onArrive(old.token); assert.equal(r.controller.state.jaunt, null);
});
await test('a late content load cannot replace the newer session', async () => {
  let release; const pending = new Promise(r => { release = r; });
  const r = rig(id => id === 'walk' ? pending : Promise.resolve(branch));
  const first = r.controller.start('walk'); await r.controller.start('branch');
  const before = r.controller.state, renders = r.renders; release(walk); await first;
  assert.equal(r.controller.state, before); assert.equal(r.renders, renders);
});
await test('live mode changes invalidate old travel without replaying choices', async () => {
  const r = rig(); await r.controller.start('branch'); r.controller.choose('buy'); r.controller.next();
  const before = r.controller.state, old = r.active;
  r.controller.setMode('fly');
  assert.equal(r.travel.mode, 'fly'); assert.equal(r.controller.state.stopIndex, before.stopIndex);
  assert.deepEqual(r.controller.state.vars, before.vars); assert.deepEqual(r.controller.state.inventory, before.inventory);
  assert.equal(r.controller.state.events.filter(e => e.type === 'decision').length, 1);
  assert(r.controller.state.leg > before.leg);
  old.onArrive(old.token); assert.equal(r.controller.state.phase, 'travelling');
  r.travel.stop('input'); assert.equal(r.controller.state.phase, 'paused'); assert.equal(r.travel.mode, 'horse');
  r.controller.resumeRide(); assert.equal(r.controller.state.phase, 'travelling'); assert.equal(r.travel.mode, 'fly');
  r.controller.straight(); assert.equal(r.travel.mode, 'instantly'); assert.equal(r.controller.state.mode, 'fly');
  r.active.onArrive(r.active.token); assert.equal(r.controller.state.phase, 'atStop');
  r.controller.end(); assert.equal(r.travel.mode, 'horse');
});
await test('T-3328: a stop with an hour sets it on arrival; a stop without, and the end, give it back', async () => {
  const doc = structuredClone(walk);
  doc.stops[0] = { ...doc.stops[0], hour: 'sunset', date: '1812-06-17', hour_evidence: [doc.stops[0].evidence[0]] };
  const calls = [];
  const hour = { set: (v, o) => { calls.push(['set', v, o.date, o.transient]); }, restore: () => { calls.push(['restore']); } };
  let active;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; }, stop() { active = null; } };
  const settle = () => new Promise(r => setTimeout(r, 0));
  const controller = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel, hour,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await controller.start('walk'); await settle();
  assert.deepEqual(calls, [['set', 'sunset', '1812-06-17', true]], 'the first stop sets its hour, transiently');
  controller.next(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.at(-1), ['restore'], 'a stop with no hour gives the visitor\'s own back');
  const n = calls.length; controller.prev(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.at(-1), ['set', 'sunset', '1812-06-17', true], 'Previous sets it again');
  controller.end(); await settle();
  assert.deepEqual(calls.at(-1), ['restore'], 'ending the jaunt gives it back');
  assert.equal(calls.length, n + 2);
  const quiet = createJaunts({ load: async () => walk, resolve: x => x, place: () => true, enter: () => true, travel, hour,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  calls.length = 0; await quiet.start('walk'); quiet.next(); active.onArrive(active.token); quiet.end(); await settle();
  assert.deepEqual(calls, [], 'a jaunt with no hours never touches the visitor\'s');
});
await test('T-3377: a jaunt\'s ambience holds its season for the outing and its hour at every stop without one', async () => {
  const doc = structuredClone(walk);
  doc.ambience = { hour: 'dusk', season: 'fall' };
  doc.stops[1] = { ...doc.stops[1], hour: 'night', hour_evidence: [doc.stops[1].evidence[0]] };
  const calls = [];
  const hour = { set: (v, o) => { calls.push(['hour', v, o.date, o.transient]); }, restore: () => { calls.push(['hour-back']); } };
  const season = { set: (v, o) => { calls.push(['season', v, o.transient]); }, restore: () => { calls.push(['season-back']); } };
  let active;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; }, stop() { active = null; } };
  const settle = () => new Promise(r => setTimeout(r, 0));
  const controller = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel, hour, season,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await controller.start('walk'); await settle();
  assert.deepEqual(calls, [['season', 'fall', true], ['hour', 'dusk', undefined, true]], 'the season first, then the hour solved on its day');
  controller.next(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.at(-1), ['hour', 'night', undefined, true], 'a stop\'s own hour outranks the jaunt\'s');
  controller.next(); if (active) { active.onArrive(active.token); await settle(); }
  if (controller.state.phase === 'atStop') assert.deepEqual(calls.at(-1), ['hour', 'dusk', undefined, true], 'the jaunt\'s hour comes back after');
  const sets = calls.filter(c => c[0] === 'season').length;
  controller.end(); await settle();
  assert.deepEqual(calls.slice(-2), [['hour-back'], ['season-back']], 'ending gives back the hour, then the season');
  assert.equal(sets, 1, 'the season is set once for the whole outing');
  calls.length = 0;
  const plain = createJaunts({ load: async () => walk, resolve: x => x, place: () => true, enter: () => true, travel, hour, season,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await plain.start('walk'); plain.next(); active.onArrive(active.token); plain.end(); await settle();
  assert.deepEqual(calls, [], 'a jaunt with no ambience never touches the visitor\'s light');
});
await test('T-3459: a dated stop holds its date\'s season from the first scene, and a later date in another season changes it', async () => {
  assert.deepEqual(['1812-01-02', '1812-03-10', '1812-04-06', '1812-05-31', '1812-06-17', '1812-08-15', '1812-09-01', '1812-11-30', '1812-12-25']
    .map(seasonOfDate), ['winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'fall', 'fall', 'winter']);
  assert.equal(seasonOfDate(undefined), null); assert.equal(seasonOfDate('1812-13-01'), null);
  const doc = structuredClone(walk);
  doc.stops[0] = { ...doc.stops[0], hour: 'sunset', date: '1812-04-06', hour_evidence: [doc.stops[0].evidence[0]] };
  doc.stops[1] = { ...doc.stops[1], hour: 'morning', date: '1812-08-10', hour_evidence: [doc.stops[1].evidence[0]] };
  assert.equal(stopSeason(doc, doc.stops[0]), 'spring');
  assert.deepEqual(openingLight(doc), { hour: 'sunset', season: 'spring' }, 'the menu and welcome name the first scene\'s light');
  assert.deepEqual(openingLight({ ...walk, ambience: { hour: 'dusk', season: 'fall' } }), { hour: 'dusk', season: 'fall' });
  assert.equal(openingLight(walk), null);
  const calls = [];
  const hour = { set: (v, o) => { calls.push(['hour', v, o.date, o.transient]); }, restore: () => { calls.push(['hour-back']); } };
  const season = { set: (v, o) => { calls.push(['season', v, o.transient]); }, restore: () => { calls.push(['season-back']); } };
  let active, flight;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; }, stop() { active = null; } };
  const settle = () => new Promise(r => setTimeout(r, 0));
  // The visitor's own Winter stands; the start flies in (T-3432), and the first scene is spring before it lands.
  const controller = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel, hour, season,
    approach: () => ({ begin: cb => { flight = cb; return true; } }),
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await controller.start('walk'); await settle();
  assert.equal(controller.state.phase, 'opening', 'still flying in');
  assert.deepEqual(calls, [['season', 'spring', true], ['hour', 'sunset', '1812-04-06', true]], 'spring and the stop\'s hour, on the way in');
  flight.onArrive(flight.token); await settle();
  assert.equal(calls.filter(c => c[0] === 'season').length, 1, 'landing does not set it again');
  controller.next(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.slice(-2), [['season', 'summer', true], ['hour', 'morning', '1812-08-10', true]], 'August is summer');
  controller.prev(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.slice(-2), [['season', 'spring', true], ['hour', 'sunset', '1812-04-06', true]], 'Previous takes April back');
  controller.end(); await settle();
  assert.deepEqual(calls.slice(-2), [['hour-back'], ['season-back']], 'ending gives the visitor\'s own light back');
  // An undated stop under an ambience keeps the jaunt's season; a dated one outranks it.
  calls.length = 0;
  const mixed = structuredClone(doc); mixed.ambience = { season: 'fall' }; delete mixed.stops[0].date;
  const c2 = createJaunts({ load: async () => mixed, resolve: x => x, place: () => true, enter: () => true, travel, hour, season,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await c2.start('walk'); await settle();
  assert.deepEqual(calls[0], ['season', 'fall', true]);
  c2.next(); active.onArrive(active.token); await settle();
  assert.deepEqual(calls.filter(c => c[0] === 'season').at(-1), ['season', 'summer', true]);
  c2.end(); await settle();
  // The hour does not wait for a season's woods to re-grow: a season that never finishes
  // still lets the stop's own hour and date land (the date moves when the season begins).
  calls.length = 0;
  const slow = { set: (v, o) => { calls.push(['season', v, o.transient]); return new Promise(() => {}); }, restore: () => { calls.push(['season-back']); } };
  const c3 = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel, hour, season: slow,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await c3.start('walk'); await settle();
  assert.deepEqual(calls, [['season', 'spring', true], ['hour', 'sunset', '1812-04-06', true]], 'the hour lands while spring is still growing');
  c3.end(); await settle();
});
await test('T-3355: a leg with its own mode rides that way on the default mode; a picked mode wins', async () => {
  const doc = structuredClone(walk);
  doc.legs = [{ note: 'A long ride.', evidence: [doc.stops[0].evidence[0]], mode: 'instantly' }];
  let active;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; }, stop() { active = null; } };
  const make = () => createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  const c = make(); await c.start('walk'); c.next();
  assert.equal(travel.mode, 'instantly', 'the authored leg goes Instantly');
  assert.equal(legMode(c.state), 'instantly'); assert.equal(c.state.mode, 'walk', 'the visitor\'s mode is untouched');
  active.onArrive(active.token); c.prev();
  assert.equal(travel.mode, 'instantly', 'going back over the same leg goes the same way');
  active.onArrive(active.token); c.end();
  const d = make(); await d.start('walk', { mode: 'horse' }); d.next();
  assert.equal(travel.mode, 'horse', 'a mode the visitor picked rides every leg');
  d.end();
  assert.equal(legMode({ ...emptyState(), jaunt: walk, mode: 'walk', visited: [{ id: 'mail-corner' }], fromStopId: 'arrival' }), 'walk',
    'a jaunt with no leg modes rides its own mode');
});
await test('T-3405: picking the jaunt\'s own mode on a leg that goes its own way is honoured, then and after', async () => {
  const doc = structuredClone(walk);
  doc.legs = [{ note: 'A long ride.', evidence: [doc.stops[0].evidence[0]], mode: 'instantly' }];
  let active;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, go(target, hooks) { active = hooks; return true; }, stop() { active = null; } };
  const c = createJaunts({ load: async () => doc, resolve: x => x, place: () => true, enter: () => true, travel,
    render() {}, showMenu() {}, openDetail() {}, closeDetail() {}, onError: e => { throw e; } });
  await c.start('walk');
  assert.equal(shownMode(c.state), 'instantly', 'at the stop, the picker names the next leg\'s own mode');
  c.next();
  assert.equal(travel.mode, 'instantly'); assert.equal(shownMode(c.state), 'instantly', 'the picker shows the leg as it travels');
  assert.equal(c.setMode('walk'), true, 'choosing Walk on a Walk jaunt is not ignored');
  assert.equal(travel.mode, 'walk', 'the leg is re-planned on foot');
  assert.equal(c.state.modeChosen, true); assert.equal(shownMode(c.state), 'walk');
  active.onArrive(active.token); c.prev();
  assert.equal(travel.mode, 'walk', 'and every later leg takes the pick');
  active.onArrive(active.token);
  const restarted = c.restart(); await restarted;
  assert.equal(c.state.modeChosen, true, 'a restart keeps the pick'); c.end();
  const saved = reduce(reduce(emptyState(), { type: 'START', jaunt: doc, session: 1, mode: 'walk' }), { type: 'MODE', mode: 'fly' });
  assert.equal(saved.modeChosen, true);
  const plain = reduce(emptyState(), { type: 'START', jaunt: doc, session: 1, mode: 'walk' });
  assert.equal(plain.modeChosen, false, 'a start on the default is not a pick');
  assert.equal(reduce(plain, { type: 'MODE', mode: 'walk' }).modeChosen, true, 'nor is it ignored when picked at the stop');
});
console.log(`JAUNT REDUCER PASS — ${tests} cases`);
