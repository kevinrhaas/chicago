// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { createInteractions, createInteractKey } from '../renderers/web/js/interact.js';
import { registerTransportInteraction } from '../renderers/web/js/transport-interactions.js';

class Key extends EventTarget {
  hidden = true;
  dataset = {};
  words = { textContent: '' };
  attrs = new Map();
  querySelector() { return this.words; }
  setAttribute(k, v) { this.attrs.set(k, v); }
}
const keys = new EventTarget(), button = new Key();
const said = [], calls = [];
let where = { e: 0, n: 0, bearing: 90, flying: false }, enabled = true, clear = true;
let at = [4, 0], visible = true, motion = 'moving';
const actor = {
  id: 'wagon-town-loop', name: 'Wagon driver',
  get at() { return at; }, get visible() { return visible; }, get state() { return motion; },
  canResume() { return clear; },
  stop(reason) { calls.push(['stop', reason]); motion = 'stopped'; return true; },
  resume() { calls.push(['resume']); motion = 'moving'; return true; },
};
const interactions = createInteractions();
const handle = registerTransportInteraction(interactions, actor);
assert.throws(() => registerTransportInteraction(interactions, actor), /already has an interaction/);
const key = createInteractKey({ interactions, keyEl: button, keys, where: () => where,
  enabled: () => enabled, say: text => said.push(text), isTyping: target => target?.typing === true });
const keyboard = extras => {
  const ev = new Event('keydown', { cancelable: true });
  Object.assign(ev, { code: 'KeyR', repeat: false, ...extras });
  keys.dispatchEvent(ev);
  return ev;
};

key.refresh();
assert.equal(button.hidden, false);
assert.equal(button.words.textContent, 'Stop driver');
assert.equal(button.dataset.thing, 'driver:wagon-town-loop');
assert.match(button.attrs.get('aria-label'), /Interact: Stop driver — Wagon driver/);
assert.equal(keyboard().defaultPrevented, true);
assert.deepEqual(calls, [['stop', 'interaction']]);
assert.equal(motion, 'stopped');
assert.equal(key.press().ok, false, 'a repeated press cannot race the running step');
interactions.update(0);
assert.equal(handle.thing.state, 'stopped');
assert.equal(button.words.textContent, 'Continue journey');
button.dispatchEvent(new Event('click', { cancelable: true }));
interactions.update(0);
assert.equal(motion, 'moving', 'the same touch/click key resumes the real controller');
assert.deepEqual(calls, [['stop', 'interaction'], ['resume']]);

// An obstacle introduced after paint is checked again when the action starts.
motion = 'stopped'; key.refresh(); clear = false;
key.press(); interactions.update(0);
assert.equal(motion, 'stopped');
assert.equal(handle.thing.state, 'stopped');
assert.equal(calls.length, 2);
assert.equal(button.words.textContent, 'Step back to let the wagon pass');
// T-3475: without the scene's half, Step back says why rather than silently doing nothing.
{
  const res = key.press();
  assert.equal(res.ok, false); assert.equal(res.refused, true);
  assert.equal(said.at(-1), 'No room to step aside here');
  assert.equal(calls.length, 2);
}
clear = true; key.refresh();
assert.equal(button.words.textContent, 'Continue journey');

at = [6.01, 0]; key.refresh();
assert.equal(button.hidden, true, 'offers follow the moving driver, not its original stand');
assert.equal(keyboard().defaultPrevented, false);
at = [3, 0]; where.flying = true; key.refresh();
assert.equal(button.hidden, true);
where.flying = false; enabled = false; key.refresh();
assert.equal(button.hidden, true);
enabled = true; visible = false; key.refresh();
assert.equal(button.hidden, true, 'a culled/hidden model cannot be interacted with');
visible = true; key.refresh();
keys.typing = true;
assert.equal(keyboard().defaultPrevented, false);
keys.typing = false;
for (const extras of [{ repeat: true }, { ctrlKey: true }, { metaKey: true }, { altKey: true }]) {
  assert.equal(keyboard(extras).defaultPrevented, false);
}
assert.equal(calls.length, 2);
handle.dispose(); key.refresh();
assert.equal(button.hidden, true);
assert.equal(interactions.nearest(0, 0), null);
assert.equal(interactions.act(handle.thing.id).ok, false);
const replacement = registerTransportInteraction(interactions, actor);
assert.equal(interactions.get(handle.thing.id), replacement.thing, 'a released actor can be remounted');
replacement.dispose();
key.dispose();

// T-3475 (Kevin: "the step back and let the wagon pass interaction did not work"): the
// press walks the visitor to the scene's clear stand, then the team goes on.
{
  const placed = [], planned = [], heard = [];
  let me = { e: 1, n: 0 }, room = true;
  motion = 'stopped'; clear = false; at = [3, 0]; visible = true; calls.length = 0;
  const engine = createInteractions();
  const giveRoom = {
    plan(a) { planned.push(a.id); return room ? { from: { ...me }, to: { e: 1, n: 3 } } : null; },
    place(e, n) { placed.push([e, n]); me = { e, n }; if (n >= 3) clear = true; },
  };
  const h = registerTransportInteraction(engine, actor, { giveRoom, vehicle: 'carriage' });
  const k = createInteractKey({ interactions: engine, keyEl: new Key(), where: () => ({ ...me, bearing: 90, flying: false }),
    say: text => heard.push(text) });
  k.refresh();
  assert.equal(h.thing.actions.stopped[0].label, 'Step back to let the carriage pass');
  room = false;
  assert.equal(k.press().refused, true, 'no clear stand: nothing moves');
  assert.deepEqual(placed, []); assert.equal(heard.at(-1), 'No room to step aside here');
  room = true;
  assert.equal(k.press().ok, true);
  assert.equal(motion, 'stopped', 'the team waits while the visitor steps aside');
  for (let i = 0; i < 10; i++) engine.update(.1);
  assert(placed.length >= 2, 'the visitor walks, not jumps');
  assert.deepEqual(placed.at(-1), [1, 3], 'and ends on the clear stand');
  for (let i = 1; i < placed.length; i++) assert(placed[i][1] >= placed[i - 1][1], 'steadily');
  assert.equal(motion, 'moving', 'then the carriage goes on');
  assert.deepEqual(calls, [['resume']]);
  assert.equal(heard.at(-1), 'The carriage goes on');
  assert.equal(h.thing.running, null);
  assert.equal(h.thing.state, 'moving');
  assert.throws(() => registerTransportInteraction(createInteractions(), actor, { giveRoom: { plan() {} } }));
  k.dispose(); h.dispose();
}
console.log('transport interactions: keyboard/touch stop-resume, moving reach, clearance, hidden/disposed and input guards PASS');

// A cold Find/Go to reads the real configured route/seat without importing a GLB.
{
  const { readFile } = await import('node:fs/promises');
  const { createTownTransport: createTownTransportDefault } = await import('../renderers/web/js/town-transport.js');
  // T-3542: Light draws its teams by default now; this journey is about a tier that retires
  // them, which any reach of 0 still is.
  const createTownTransport = (options) => createTownTransportDefault({ reach: { full: 90, balanced: 60, light: 0 }, ...options });
  const { circleRoute, roundedBlockRoute, createTransportLoop } = await import('../renderers/web/js/transport-loop.js');
  const config = JSON.parse(await readFile(new URL('../data/transport/driven/loops.json', import.meta.url), 'utf8'));
  const row = config.rows.find(r => r.scene === '1835');
  let assetCalls = 0;
  const makeTown = (detail = 'full', rows = [row], sceneId = '1835') => createTownTransport({
    rows, sceneId, detail, makeAssembly() { assetCalls++; throw Error('cold lookup must not load assets'); },
    heightAt: () => 0, clear: () => true, routeSupport: () => ({ valid: true }),
  });
  const town = makeTown();
  const route = row.route.kind === 'rounded_block' ? roundedBlockRoute(row.route) : circleRoute(row.route);
  const poses = [];
  const nativeActor = createTransportLoop({ ...row, route, heightAt: () => 0, clear: () => true,
    assembly: { pose: p => poses.push(p), advance() {}, visible() {}, stop() {}, dispose() {} } });
  const cold = town.driverAnchorForPerson(row.person_id);
  assert.deepEqual(cold.at, nativeActor.at, 'cold target is exactly the native rear-axle/root/driver-seat reading');
  assert.equal(cold.yaw_rad, nativeActor.snapshot().yaw_rad);
  assert.equal(cold.actor, null);
  assert.equal(town.actors.length, 0);
  assert.equal(assetCalls, 0);
  assert.equal(row.route.kind, 'circle');
  assert.equal(row.route.radius_m, 18);
  assert(Math.hypot(cold.at[0] + 349.5, cold.at[1] + 555.675) < 1e-9, 'printed source coordinates round the exact native seat reading by sub-nanometres');
  assert.equal(makeTown('balanced').driverAnchorForPerson(row.person_id).at[0], cold.at[0]);
  assert.equal(makeTown('light').driverAnchorForPerson(row.person_id), null);
  assert.equal(town.driverAnchorForPerson('unknown-person'), null);
  assert.equal(makeTown('full', [row], '1904').driverAnchorForPerson(row.person_id), null);
  const invalid = structuredClone(row); invalid.driver_instance.person_id = 'a-different-person';
  assert.equal(makeTown('full', [invalid]).driverAnchorForPerson(row.person_id), null);

  const source = await readFile(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  const begin = source.indexOf('  function goToTarget(target) {');
  const end = source.indexOf('  /** The future welcome picker', begin);
  assert(begin >= 0 && end > begin);
  const actualBody = source.slice(begin, end);
  const stand = { kind: 'intersection', local_e: 12, local_n: 34, label: 'Standing person' };
  const destinations = { resolve: () => stand, byId: () => null };
  const visits = [], announced = [];
  const makeGo = (runtime, blockedAt = () => false) => Function('api', 'jauntRuntime', 'travel', 'router', 'hud',
    'destinations', 'openBusiness', 'openBuilding', actualBody + '\nreturn goToTarget;')(
    { townTransport: runtime, humans: { external: () => null } }, null,
    { go: target => { visits.push(target); return target; } }, { blockedAt },
    { say: s => announced.push(s), setPanel() {}, selectTab() {} }, destinations, () => {}, () => {});
  const target = { kind: 'person', id: row.person_id, label: 'Otis Bardwell' };
  const found = makeGo(town)(target);
  assert.equal(found.kind, 'intersection');
  assert.equal(found.local_e, cold.at[0] + Math.cos(cold.yaw_rad) * 4);
  assert.equal(found.local_n, cold.at[1] + Math.sin(cold.yaw_rad) * 4);
  assert.equal(found.label, target.label);
  assert.equal(assetCalls, 0);
  assert.equal(town.actors.length, 0);
  assert.equal(makeGo(town, () => true)(target), false, 'cold stand still passes the existing router guard');

  town.actors.push(nativeActor);
  nativeActor.update(.25);
  const live = town.driverAnchorForPerson(row.person_id);
  assert.strictEqual(live.actor, nativeActor);
  assert.deepEqual(live.at, nativeActor.at);
  assert.notDeepEqual(live.at, cold.at, 'live actor takes precedence over the configured start');
  const liveFound = makeGo(town)(target);
  assert.equal(liveFound.local_e, live.at[0] + Math.cos(live.yaw_rad) * 4);
  assert.equal(liveFound.local_n, live.at[1] + Math.sin(live.yaw_rad) * 4);
  assert.equal(nativeActor.snapshot().reason, 'approach');
  const last = nativeActor.at;
  await town.setTier('light');
  assert.strictEqual(makeGo(town)(target), stand, 'Light preserves the existing standing-person fallback');
  assert.equal(town.actors.length, 0);
  await town.setTier('full');
  assert.deepEqual(town.driverAnchorForPerson(row.person_id).at, last, 'a retired journey resumes from its saved native distance');
  assert.equal(assetCalls, 0);
  assert.strictEqual(makeGo(town)({ kind: 'person', id: 'unknown-person' }), stand);
  town.dispose();
  assert.equal(town.driverAnchorForPerson(row.person_id), null);
  console.log('cold driver Find/Go to: actual route+seat, no asset load, live current pose, saved journey, Light/unknown fallbacks and router guards PASS');
}
