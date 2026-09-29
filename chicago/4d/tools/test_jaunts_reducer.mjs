#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { emptyState, reduce, createJaunts, canNext } from '../renderers/web/js/jaunts.js';
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
console.log(`JAUNT REDUCER PASS — ${tests} cases`);
