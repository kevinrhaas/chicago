#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3495 (owner, 2026-11-07: "by default with the jaunts when going on them the people should
 * be hidden so that they don't interfere ... I am concerned about all these soldiers around the
 * fort hanging out 24 7"). While a jaunt is under way the everyday figures are held out of the
 * scene, but for the people its stop calls for (its `people`, then its person links); they all
 * come back when it ends, completes or goes to the menu. Settings > Show > People stays the
 * master switch. Node only: the controller with a counting crowd, and the actual human layer.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import { createJaunts, stopPeople, localsStop } from '../renderers/web/js/jaunts.js';

const fixture = id => JSON.parse(fs.readFileSync(new URL(`../data/jaunts/_fixtures/fixture-${id}.json`, import.meta.url)));

// ---- which people a stop calls for.
assert.deepEqual(stopPeople(null), []);
assert.deepEqual(stopPeople({ links: [{ kind: 'structure', id: 'x' }] }), [], 'a building link calls for nobody');
assert.deepEqual(stopPeople({ people: ['a', 'b'], links: [{ kind: 'person', id: 'b' }, { kind: 'person', id: 'c' }] }),
  ['a', 'b', 'c'], 'its own people first, then its person links, once each');
console.log('PASS a stop calls for its own people and the people its cards link');

// ---- T-3553 (the owner, 2026-11-16: "make sure there are people present ... in scene of jaunt
// all eras"): a stop with no stage and no hosts keeps the town's own people about its stand.
assert.equal(localsStop(null), null);
assert.deepEqual(localsStop({ id: 'a' }), { id: 'a' }, 'a plain stop keeps its neighbourhood');
assert.equal(localsStop({ id: 'b', stage: { cast: [{ person: 'x', at: [0, 0] }] } }), null, 'a staged stop is its own scene');
assert.equal(localsStop({ id: 'c', hosts: [{ person: 'x', local_e: 1, local_n: 1 }] }), null, 'a hosted stop is told by its hosts');
assert.deepEqual(localsStop({ id: 'd', stage: { cast: [] } }), { id: 'd', stage: { cast: [] } }, 'an empty stage plays nothing');
console.log('PASS a stop with no stage or hosts keeps the town about it');

// ---- the controller holds the crowd from the start to the end, stop by stop.
const walk = structuredClone(fixture('walk'));
walk.stops[0].people = ['peck_philip'];
walk.stops[1].links = [...(walk.stops[1].links || []), { kind: 'person', id: 'kinzie_juliette', label: 'Juliette Kinzie' }];
const calls = [], localsAsked = [];
const crowd = { hold: (ids, o = {}) => { calls.push(['hold', [...ids]]); localsAsked.push(o.locals?.id ?? null); }, restore: () => calls.push(['restore']) };
const rig = (extra = {}) => {
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go() { return true; } };
  return createJaunts({ load: async () => walk, resolve: x => x, place: () => true, enter: () => true, travel,
    showMenu() {}, render() {}, openDetail() {}, closeDetail() {}, onError(e) { throw e; }, storage: null, crowd, ...extra });
};
{
  calls.length = 0;
  const c = rig();
  assert.equal(await c.start(walk.id), true);
  assert.deepEqual(calls, [['hold', ['peck_philip']]], 'held at the start, keeping the first stop\'s people');
  assert.equal(localsAsked.at(-1), walk.stops[0].id, 'a plain stop asks for the people about it');
  c.next();   // travelling to the second stop: its people are the ones kept on the way in
  assert.deepEqual(calls.at(-1), ['hold', ['kinzie_juliette']]);
  const before = calls.length;
  c.straight();   // the same leg again: nothing to change
  assert.equal(calls.length, before, 'a stop already held is not held again');
  c.menu();
  assert.deepEqual(calls.at(-1), ['restore'], 'the Jaunts menu gives everyone back');
  c.resume();
  assert.deepEqual(calls.at(-1), ['hold', ['kinzie_juliette']], 'resuming holds them out again');
  c.end();
  assert.deepEqual(calls.at(-1), ['restore'], 'End gives everyone back');
  const ended = calls.length;
  c.explore();
  assert.equal(calls.length, ended, 'nothing held, nothing to give back');
}
{
  calls.length = 0;
  const c = rig();
  await c.start(walk.id);
  c.next();
  assert.equal(c.state.phase, 'travelling');
  c.explore();
  assert.deepEqual(calls.at(-1), ['restore'], 'leaving for free roam gives everyone back');
}
{
  // A flight to the first stop holds the crowd before landing.
  calls.length = 0;
  let land;
  const c = rig({ approach: () => ({ begin: cb => { land = cb.onArrive; return true; } }) });
  await c.start(walk.id);
  assert.equal(c.state.phase, 'opening');
  assert.deepEqual(calls, [['hold', ['peck_philip']]], 'held while flying in');
  land();
  assert.equal(c.state.phase, 'atStop');
  assert.equal(calls.length, 1, 'the landing keeps the same hold');
  c.end();
}
{
  // A completed outing gives everyone back.
  calls.length = 0;
  let arrive;
  const travel = { mode: 'walk', setMode(v) { this.mode = v; }, stop() {}, go(_t, cb) { arrive = () => cb.onArrive(cb.token); return true; } };
  const c = rig({ travel });
  await c.start(walk.id);
  c.next(); arrive();
  assert.equal(c.state.phase, 'atStop');
  c.next();
  assert.equal(c.state.phase, 'outcome');
  assert.deepEqual(calls.at(-1), ['restore'], 'Outing complete gives everyone back');
}
{
  // A crowd that throws never stops the outing.
  const c = rig({ crowd: { hold() { throw new Error('x'); }, restore() { throw new Error('y'); } } });
  assert.equal(await c.start(walk.id), true);
  c.end();
  assert.equal(c.state.jaunt, null);
}
console.log('PASS the controller holds the crowd from the first stop to End, menu or completion');

// ---- the actual human layer: held figures are neither drawn, advanced, met nor picked.
const THREE = await import(process.env.C4D_THREE_MODULE
  ? pathToFileURL(process.env.C4D_THREE_MODULE).href
  : new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href);
const source = fs.readFileSync(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
const start = source.indexOf('export function createHumanLayer('), stop = source.indexOf('\n/**\n * THE SCENE PATH.', start);
assert.ok(start >= 0 && stop > start, 'humans.js: createHumanLayer');
const updates = new Map();
class LayerActor {
  constructor({ instance: inst, identity, person }) {
    Object.assign(this, { instance: inst, identity, person, id: inst.id, personId: inst.person_id, recheck: 1,
      root: new THREE.Group(), proxy: new THREE.Mesh(new THREE.BoxGeometry(1, 2, 1)), body: {}, inRange: true, e: 0, n: 0 });
    this.proxy.userData.actor = this;
    this.root.add(this.proxy);
  }
  update() { updates.set(this.id, (updates.get(this.id) ?? 0) + 1); this.root.visible = true; }
  dispose() { this.root.removeFromParent(); }
}
const createLayer = new Function('THREE', 'HumanActor', 'createHumanAssets', 'humanRoleCard', 'HUMAN_TIERS', 'DRAW_M',
  `${source.slice(start, stop).replace(/^export /gm, '')}\nreturn createHumanLayer;`)(THREE, LayerActor, () => ({}), () => null, { full: [0] }, 140);
const layer = createLayer({ assets: {} });
const soldier = layer.add({ id: 'hi_soldier', person_id: 'p_soldier', interaction: { selectable: true, radius_m: 3 } }, { person: { id: 'p_soldier' } });
const peck = layer.add({ id: 'hi_peck', person_id: 'p_peck', interaction: { selectable: true, radius_m: 3 } }, { person: { id: 'p_peck' } });
soldier.root.position.set(0, 0, -5); peck.root.position.set(0, 0, -8);
soldier.n = 5; peck.n = 8;
const driver = new LayerActor({ instance: { id: 'hi_driver', person_id: 'p_driver' }, identity: { kind: 'person' } });
layer.withhold('p_driver', { externalActor: driver });
const camera = new THREE.PerspectiveCamera();
const left = [];
layer.on('leave', d => left.push(d.personId));
layer.group.updateMatrixWorld(true);
layer.update(0.05, camera, { e: 0, n: 4.5 });   // the visitor beside the soldier: met
assert.equal(layer.pickAt(null, camera)?.personId, 'p_soldier', 'before a jaunt, the nearest figure is picked');
assert.equal(layer.crowdKept, null);

assert.equal(layer.holdCrowd(['p_peck']), 1);
assert.deepEqual(layer.crowdKept, ['p_peck']);
assert.equal(soldier.root.visible, false, 'a held figure is not drawn');
assert.equal(peck.root.visible, true, 'a called-for figure still stands');
assert.equal(driver.root.visible, true, 'a seated driver belongs to his vehicle and is not held');
assert.deepEqual(left, ['p_soldier'], 'a held figure the visitor stood beside is left');
assert.equal(layer.isHeld(soldier), true); assert.equal(layer.isHeld(peck), false);
const before = { soldier: updates.get('hi_soldier'), peck: updates.get('hi_peck') };
layer.update(0.05, camera, { e: 0, n: 4.5 });
assert.equal(updates.get('hi_soldier'), before.soldier, 'a held figure is not advanced (and so not loaded)');
assert.equal(updates.get('hi_peck'), before.peck + 1, 'a called-for figure goes on');
assert.equal(soldier.root.visible, false);
assert.equal(layer.pickAt(null, camera)?.personId, 'p_peck', 'a held figure is not picked; the one behind it is');

layer.holdCrowd([]);   // a stop that calls for nobody
assert.equal(peck.root.visible, false);
assert.equal(layer.pickAt(null, camera), null, 'nobody kept, nobody picked');

// T-3553: a stop's neighbourhood: those within its reach stand, those beyond are held, and one
// who walks in or out is drawn or held from the next frame.
layer.holdCrowd([], { area: { e: 0, n: 0, r: 6, structure: 'x' } });
assert.deepEqual(layer.crowdArea, { e: 0, n: 0, r: 6, structure: 'x' });
assert.equal(layer.isHeld(soldier), false, 'within the stand\'s reach: about their day');
assert.equal(layer.isHeld(peck), true, 'beyond it: held');
assert.equal(peck.root.visible, false);
assert.equal(layer.keeps('anyone', 1, 1), true); assert.equal(layer.keeps('anyone', 10, 10), false); assert.equal(layer.keeps('anyone'), false);
layer.update(0.05, camera, { e: 0, n: 0 });
assert.equal(soldier.root.visible, true);
soldier.n = 9; layer.update(0.05, camera, { e: 0, n: 0 });
assert.equal(soldier.root.visible, false, 'walked out of reach: held');
soldier.n = 5; peck.n = 2; layer.update(0.05, camera, { e: 0, n: 0 });
assert.equal(soldier.root.visible && peck.root.visible, true, 'walked back in: drawn again');
layer.holdCrowd([]);   // the next stop is staged: nobody about it
assert.equal(layer.crowdArea, null);
assert.equal(soldier.root.visible || peck.root.visible, false);
soldier.n = 5; peck.n = 8;

layer.setShown(false);   // Settings > Show > People hidden, during the jaunt
assert.equal(layer.releaseCrowd(), true);
assert.equal(layer.releaseCrowd(), false, 'released twice is a no-op');
layer.update(0.05, camera);
assert.equal(layer.group.visible, false, 'the jaunt\'s end never undoes Settings > Show > People');
layer.setShown(true);
layer.update(0.05, camera);
assert.equal(soldier.root.visible && peck.root.visible, true, 'everyone is back once the jaunt lets go');
assert.equal(soldier.recheck, 0, 'released figures are rechecked on the next frame');
assert.equal(layer.isHeld(soldier), false);
assert.equal(layer.crowdArea, null);
assert.equal(layer.keeps('anyone'), true, 'nobody held: everyone may be about');
console.log('PASS the human layer holds the crowd out (not drawn, advanced, met or picked), keeps the called-for, the drivers and a stop\'s neighbourhood, and gives them back');
console.log('JAUNT CROWD PASS');
