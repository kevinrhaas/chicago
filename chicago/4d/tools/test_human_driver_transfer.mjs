// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise the actual HumanLayer registry implementation with real THREE roots.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const THREE = await import(process.env.C4D_THREE_MODULE
  ? pathToFileURL(process.env.C4D_THREE_MODULE).href
  : new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href);
const source = fs.readFileSync(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
const start = source.indexOf('export function createHumanLayer(');
const end = source.indexOf('\n/**\n * THE SCENE PATH.', start);
assert.ok(start >= 0 && end > start);
let updates = 0, disposals = 0;
class Actor {
  constructor({ instance, identity, person }) {
    Object.assign(this, { instance, identity, person, id: instance.id, personId: instance.person_id,
      root: new THREE.Group(), body: {}, disposed: false, tier: 'full' });
  }
  update() { updates++; this.root.visible = true; }
  dispose() { this.disposed = true; disposals++; this.root.removeFromParent(); }
}
const createLayer = new Function('THREE', 'HumanActor', 'createHumanAssets', 'humanRoleCard', 'HUMAN_TIERS',
  source.slice(start, end).replace('export function', 'function') + '\nreturn createHumanLayer;')(
  THREE, Actor, () => ({}), () => null, { full: [0], balanced: [1], light: [3] });
const layer = createLayer({ assets: {} });
const instance = { id: 'hi_rc_bardwell_otis_1835', person_id: 'rc_bardwell_otis',
  interaction: { selectable: true, opens: 'resident_card' } };
const standing = layer.add(instance, { person: { id: instance.person_id } });
const vehicle = new THREE.Group(); vehicle.position.set(20, 1, -30);
const driver = new Actor({ instance, identity: standing.identity, person: standing.person });
driver.root.position.set(0, 1.58, .65); vehicle.add(driver.root);
// Use the real public position getter: a seated child must report world ENU.
const getter = source.match(/get position\(\) \{([\s\S]*?)\n  \}/);
assert.ok(getter);
Object.defineProperty(driver, 'position', { get: new Function('THREE', `return function() {${getter[1]}}`)(THREE) });
const restore = layer.withhold(instance.person_id, { instanceId: instance.id, externalActor: driver });
assert.equal(layer.count, 1);
assert.equal(layer.get(instance.person_id), driver);
assert.equal(layer.get(instance.id), driver);
assert.equal(layer.external(instance.person_id), driver);
assert.equal(layer.remove(instance.person_id), false, 'the standing layer cannot dispose a vehicle-owned driver');
assert.equal(driver.disposed, false);
assert.equal(layer.count, 1);
assert.deepEqual(driver.position, { e: 20, n: 29.35, y: 2.58 });
assert.equal(standing.root.parent, null);
assert.throws(() => layer.add(instance), /already stands/);
assert.throws(() => layer.withhold(instance.person_id), /already transferred/);
// The real standing LOD completion adds only under its existing actor root;
// completing such a load cannot reattach a withheld root to the scene.
await Promise.resolve().then(() => { standing.root.add(new THREE.Group()); standing.root.visible = true; });
layer.update(.05, { position: new THREE.Vector3() });
assert.equal(updates, 0, 'neither withheld standing nor assembly-owned driver is advanced twice');
assert.equal(standing.root.parent, null);
let opened = null;
layer.on('open', detail => { opened = detail; });
layer.select(instance.person_id);
assert.equal(opened.personId, instance.person_id);
assert.equal(opened.instanceId, instance.id);
layer.setTier('light');
restore(); restore();
assert.equal(layer.count, 1);
assert.equal(layer.get(instance.person_id), standing);
assert.equal(layer.external(instance.person_id), null);
assert.equal(standing.root.parent, layer.group);
assert.equal(standing.tier, 'light');
assert.equal(disposals, 0, 'transfer does not dispose the seated owner or restored actor');
const lateRestore = layer.withhold(instance.person_id, { instanceId: instance.id, externalActor: driver });
layer.dispose(); lateRestore();
assert.equal(layer.count, 0);
assert.equal(disposals, 1);
assert.equal(driver.disposed, false, 'vehicle retains sole seated-actor disposal ownership');
assert.equal(standing.root.parent, null);
// A later vehicle release owns the remaining seated actor exactly once, and
// cannot restore the original into a scene whose layer already disposed.
driver.dispose(); lateRestore();
assert.equal(disposals, 2);
assert.equal(driver.disposed, true);
assert.equal(standing.root.parent, null);
console.log('human driver transfer: one identity, real world position/card, no double update, late load isolation, exact restore/Light/disposal PASS');
