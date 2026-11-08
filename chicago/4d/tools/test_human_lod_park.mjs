// SPDX-License-Identifier: GPL-3.0-or-later
// T-3439: a figure's distance levels are kept, parked, for a swap back, so walking about her
// never reloads her GLB, re-uploads her pictures, regrows her hair or recompiles her
// programs. Runs the actual HumanActor (humans.js) with real THREE roots; only the asset
// store and the body build are stand-ins. Also checks Settings > Show > People on the
// actual layer: hidden, nobody is updated or picked and a seated driver is hidden too.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const THREE = await import(process.env.C4D_THREE_MODULE
  ? pathToFileURL(process.env.C4D_THREE_MODULE).href
  : new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href);
const source = fs.readFileSync(new URL('../renderers/web/js/humans.js', import.meta.url), 'utf8');
const slice = (from, to) => {
  const start = source.indexOf(from), end = source.indexOf(to, start);
  assert.ok(start >= 0 && end > start, `humans.js: ${from}`);
  return source.slice(start, end).replace(/^export /gm, '');
};
const constants = slice('export const HUMAN_TIERS', '\n/**\n * The LOD to draw');
const actorSource = slice('export function chooseHumanLod(', '\nconst verbOf') + slice('const verbOf', '\n/**\n * Refcounted')
  + slice('const PROXY_GEOMETRY', '\n/**\n * THE ENGINE.');
const stubLife = () => ({ bound: true, bind() { return true; }, apply() {}, nod() {} });
const stubActions = () => ({ bound: true, bind() { return true; }, apply() {}, takeNod() { return false; } });
// T-3493: an older face's lids rest lower (human-skin.js restingLid); lift the real one.
const skin = fs.readFileSync(new URL('../renderers/web/js/human-skin.js', import.meta.url), 'utf8');
const lidSource = skin.match(/export const AGE = [^;]+;/)[0] + '\n' + skin.match(/export function restingLid\([\s\S]*?\n\}/)[0];
const restingLid = new Function(`${lidSource.replace(/^export /gm, '')}\nreturn restingLid;`)();
const stubGait = () => ({ bound: true, bind() { return true; }, apply() {}, speed: 1.3, pace: 1 });
const stubSkirt = () => null;
const HumanActor = new Function('THREE', 'createHumanLife', 'createHumanActions', 'createHumanGait', 'createHumanSkirt', 'enuToWorld', 'restingLid',
  `${constants}\n${actorSource}\nreturn HumanActor;`)(THREE, stubLife, stubActions, stubGait, stubSkirt,
  (e, n, h, out) => out.set(e, h, -n), restingLid);

// The asset store, counting what is parsed and let go.
const acquired = [], released = [];
const assets = {
  acquire(id, lod) { acquired.push(lod); return Promise.resolve({ lod }); },
  release(id, lod) { released.push(lod); },
};
let built = 0;
class TestActor extends HumanActor {
  build(gltf, lod) {
    built++;
    const scene = new THREE.Group();
    scene.name = `lod${lod}`;
    const mixer = new THREE.AnimationMixer(scene);
    const clip = new THREE.AnimationClip('idle', 2, []);
    return { lod, scene, meshes: [], faces: [], mixer, clips: new Map([['idle', clip]]), hair: null,
      action: null, oneShot: null, assetId: this.instance.appearance.asset_id };
  }
}
const instance = { id: 'hi_test', person_id: 'p_test', scene: '1904',
  placement: { local_e: 0, local_n: 0, heading_deg: 0 }, behaviour: { state: 'standing' },
  lod: { policy: 'auto' }, appearance: { asset_id: 'test_asset' } };
const actor = new TestActor({ instance, assets });

await actor.setLod(1);
const first1 = actor.body;
await actor.setLod(0);
const first0 = actor.body;
assert.equal(actor.parked.get(1), first1, 'the level left behind is parked, not let go');
assert.deepEqual(released, [], 'a swap lets go of nothing');
assert.equal(first1.scene.parent, null, 'a parked level is out of the scene');
// Back and forth across the 8 m band, as a visitor walking about her does.
for (let i = 0; i < 5; i++) { await actor.setLod(1); await actor.setLod(0); }
assert.deepEqual(acquired, [1, 0], 'each level is parsed once however often the band is crossed');
assert.equal(built, 2, 'each level is built (cloned, varied, haired) once');
assert.equal(actor.body, first0, 'the swap back draws the same body');
assert.equal(actor.counters.reused, 10);
assert.equal(actor.body.scene.parent, actor.root);
assert.equal(actor.root.children.filter((c) => /^lod/.test(c.name)).length, 1, 'one level drawn at a time');
assert.ok(actor.body.action?.isRunning(), 'the reused level plays its clip again');

// Every level is kept while in range: a courtyard walk spans three bands.
await actor.setLod(2);
assert.deepEqual([...actor.parked.keys()].sort(), [0, 1], 'levels 0 and 1 both stay parked under level 2');
await actor.setLod(0); await actor.setLod(2);
assert.deepEqual(acquired, [1, 0, 2], 'a walk across three bands parses each level once');
assert.deepEqual(released, []);

// A tier that no longer allows a level lets it go (Light draws 2 and 3 only).
actor.tier = 'light';
actor.update(.05, new THREE.Vector3(0, 0, 22));   // light's LOD2 band ends at 25 m (T-3463)
assert.equal(actor.parked.size, 0, 'Light lets go of parked levels 0 and 1');
assert.deepEqual(released.slice().sort(), [0, 1]);
actor.tier = 'full';

// Unused for PARK_S, a parked level is let go.
await actor.setLod(1);
actor.update(1, new THREE.Vector3(0, 0, 15));
assert.equal(actor.parked.size, 1);
const PARK_S = Number(constants.match(/PARK_S = (\d+)/)[1]);
actor.update(PARK_S + 1, new THREE.Vector3(0, 0, 15));
assert.equal(actor.parked.size, 0, 'a level unused for PARK_S is let go');
assert.deepEqual(released.slice().sort(), [0, 1, 2]);

// Out of draw range, every parked level goes; dispose lets go of the rest.
await actor.setLod(2);
assert.equal(actor.parked.size, 1);
actor.recheck = 0;
actor.update(.05, new THREE.Vector3(0, 0, 500));
assert.equal(actor.inRange, false);
assert.equal(actor.parked.size, 0, 'out of range, parked levels are let go');
actor.dispose();
assert.deepEqual(released.slice().sort(), acquired.slice().sort(), 'every level parsed is let go once per parse');
assert.equal(acquired.length, released.length, 'every parse is let go');

// Settings > Show > People, on the actual layer.
const layerSource = slice('export function createHumanLayer(', '\n/**\n * THE SCENE PATH.');
let updates = 0;
class LayerActor {
  constructor({ instance: inst, identity, person }) {
    Object.assign(this, { instance: inst, identity, person, id: inst.id, personId: inst.person_id,
      root: new THREE.Group(), proxy: new THREE.Mesh(new THREE.BoxGeometry(1, 2, 1)), body: {}, inRange: true, e: 0, n: 0 });
    this.proxy.userData.actor = this;
    this.root.add(this.proxy);
  }
  update() { updates++; }
  dispose() { this.root.removeFromParent(); }
}
const createLayer = new Function('THREE', 'HumanActor', 'createHumanAssets', 'humanRoleCard', 'HUMAN_TIERS', 'DRAW_M',
  `${layerSource}\nreturn createHumanLayer;`)(THREE, LayerActor, () => ({}), () => null, { full: [0] }, 140);
const layer = createLayer({ assets: {} });
const standing = layer.add({ id: 'hi_a', person_id: 'p_a', interaction: { selectable: true } }, { person: { id: 'p_a' } });
standing.root.position.set(0, 0, -5);
const driver = new LayerActor({ instance: { id: 'hi_b', person_id: 'p_b' }, identity: { kind: 'person' } });
const otherDriver = new LayerActor({ instance: { id: 'hi_c', person_id: 'p_c' }, identity: { kind: 'person' } });
layer.withhold('p_b', { externalActor: driver });
const camera = new THREE.PerspectiveCamera();
layer.group.updateMatrixWorld(true);
assert.ok(layer.pickAt(null, camera), 'shown, a figure is picked');
layer.update(.05, camera); assert.equal(updates, 1);
assert.equal(layer.setShown(false), false);
assert.equal(layer.group.visible, false);
assert.equal(driver.root.visible, false, 'a seated driver is hidden with the people');
layer.withhold('p_c', { externalActor: otherDriver });
assert.equal(otherDriver.root.visible, false, 'a driver seated while people are hidden is hidden too');
layer.update(.05, camera); assert.equal(updates, 1, 'hidden, nobody is updated (and so nobody loads)');
assert.equal(layer.pickAt(null, camera), null, 'hidden, nobody is picked');
layer.setShown(true);
assert.equal(driver.root.visible && otherDriver.root.visible && layer.group.visible, true);
layer.update(.05, camera); assert.equal(updates, 2);
console.log('PASS: distance levels are parked and reused, let go outside the tier, after PARK_S, out of range and on dispose; People hidden hides, stops and unpicks every figure and driver');
