// SPDX-License-Identifier: GPL-3.0-or-later
// The adults jaunts (owner, 2026-11-15: "shows everything incredibly graphically"): weapons in
// the hand and the motions of a fight (renderers/web/js/human-fight.js), solved on the arms by
// human-actions.js, on the real Otis Bardwell export and the CI fixture, on the CPU. It must:
// leave a figure with no motions handed in exactly as before; hold a tomahawk at the ready
// before the body, its head above the fist; raise it up and back behind the head for a blow
// and bring it down ahead; thrust a knife out ahead; bring a pistol up to the aim, the barrel
// level and pointing ahead, and fire it once; shoulder a musket with both hands on it; clutch
// the body when struck; put the weapon down again; and lay each weapon in the hand it is held in.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find((k) => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const driverLife = data(await js('driver-life.js'));
const garrison = data(await js('human-garrison.js'));
const FM = await import(data((await js('human-fight.js')).replace("from './human-garrison.js'", `from '${garrison}'`)));
const { createHumanActions } = await import(data((await js('human-actions.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));

function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
  }
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
async function rig(asset, lod, clip, heading = 0.7) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  const root = new THREE.Group(); root.position.set(4, 0.3, -7); root.rotation.y = heading; root.add(gltf.scene);
  const mixer = new THREE.AnimationMixer(gltf.scene);
  mixer.clipAction(gltf.animations.find((a) => a.name === clip)).play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bone = (name) => { let b = null; gltf.scene.traverse((o) => { if (o.isBone && o.name === name) b = o; }); return b; };
  return { root, scene: gltf.scene, mixer, bone };
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
const figure = (r, p) => p.clone().sub(r.root.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), -r.root.rotation.y);
const figDir = (r, d) => d.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -r.root.rotation.y);
const run = (r, acts, seconds, opts) => {
  let shots = 0;
  for (let t = 0; t < seconds - 1e-9; t += 1 / 30) { r.mixer.update(1 / 30); acts.apply(1 / 30, opts); shots += acts.takeShot(); r.root.updateMatrixWorld(true); }
  return shots;
};
const f3 = (v) => v.toArray().map((x) => x.toFixed(2)).join(',');

// The motions are numbers before they are arms.
for (const act of FM.FIGHT_ACTS) assert(FM.MOTIONS[act], `a ${act} motion`);
assert.equal(FM.fightTargets({ arm: 'none' }), null, 'nothing held and nothing done: no targets');
assert.equal(FM.shotTime('fire', 'pistol') > 0 && FM.shotTime('strike', 'tomahawk'), null, 'a blow fires no shot');
for (const k of FM.WEAPON_KINDS.filter((k) => k !== 'none')) {
  const g = FM.weaponGroup(k);
  assert(g && g.children.length, `${k}: a weapon is drawn`);
  const box = new THREE.Box3().setFromObject(g), size = box.getSize(new THREE.Vector3());
  assert(size.y > 0.15 && size.y < 2.0, `${k}: its length along its axis is a ${k}'s (${size.y.toFixed(2)} m)`);
}
console.log('fight motions and weapons: PASS');

for (const [asset, lod, clip] of [['bardwell_otis_1835', 0, 'idle_natural_v1'], ['bardwell_otis_1835', 3, 'idle'], ['c4d_fixture', 1, 'idle']]) {
  const opts = (r) => ({ state: 'standing', root: r.root });
  // No motions handed in: exactly the arms as before, whatever it is told.
  {
    const a = await rig(asset, lod, clip), b = await rig(asset, lod, clip);
    const plain = createHumanActions({ id: `f:${asset}`, scene: a.scene }), told = createHumanActions({ id: `f:${asset}`, scene: b.scene });
    told.wield('tomahawk').act('strike');
    run(a, plain, 1.5, opts(a)); run(b, told, 1.5, opts(b));
    assert(world(a.bone('hand_r')).distanceTo(world(b.bone('hand_r'))) < 1e-9, `${asset} LOD${lod}: without the fight motions a figure never holds a weapon`);
  }
  const r = await rig(asset, lod, clip);
  const acts = createHumanActions({ id: `f:${asset}`, scene: r.scene, fightMotions: FM });
  const o = opts(r);
  const sh = figure(r, world(r.bone('upperarm_r'))), headY = figure(r, world(r.bone('head'))).y;
  run(r, acts, 1, o);
  // The tomahawk at the ready: the fist low before the body, the head of the haft above the fist.
  acts.wield('tomahawk');
  run(r, acts, 1.2, o);
  const grip0 = acts.gripFrame('r');
  const g = figure(r, grip0.pos), up = figDir(r, grip0.a);
  assert(g.z > 0.08 && g.y < sh.y - 0.2 && up.y > 0.3, `${asset} LOD${lod}: a tomahawk at the ready before the body, its head up (grip ${f3(g)}, axis ${f3(up)})`);
  // The blow: up and back over the shoulder, then down and ahead.
  acts.act('strike');
  run(r, acts, 0.4, o);
  const wind = figure(r, acts.gripFrame('r').pos), back = figDir(r, acts.gripFrame('r').a);
  assert(wind.y > sh.y && back.z < -0.3, `${asset} LOD${lod}: the tomahawk wound up above the shoulder, its head back (${f3(wind)}, axis ${f3(back)})`);
  run(r, acts, 0.24, o);
  const hit = figure(r, acts.gripFrame('r').pos);
  assert(hit.z > wind.z + 0.3 && hit.y < wind.y - 0.2, `${asset} LOD${lod}: the blow comes down ahead (${f3(hit)})`);
  run(r, acts, 0.8, o);
  assert.equal(acts.fight.act, null, `${asset} LOD${lod}: the blow is over`);
  // A knife thrust out ahead.
  acts.wield('knife'); run(r, acts, 0.8, o); acts.act('stab'); run(r, acts, 0.46, o);
  const thrust = figure(r, acts.gripFrame('r').pos);
  assert(thrust.z > sh.z + 0.38, `${asset} LOD${lod}: a knife thrust out ahead (${f3(thrust)})`);
  run(r, acts, 0.8, o);
  // A pistol brought up to the aim, level, and fired once.
  acts.wield('pistol'); run(r, acts, 0.8, o); acts.act('fire');
  const shots = run(r, acts, 1.4, o);
  const aim = acts.gripFrame('r'), barrel = figDir(r, aim.f), at = figure(r, aim.pos);
  assert.equal(shots, 1, `${asset} LOD${lod}: one shot`);
  assert(barrel.z > 0.93 && Math.abs(barrel.y) < 0.3 && at.z > sh.z + 0.4 && Math.abs(at.y - sh.y) < 0.15,
    `${asset} LOD${lod}: the pistol aimed ahead at the shoulder's height (grip ${f3(at)}, barrel ${f3(barrel)})`);
  // A musket shouldered, both hands on it: the left hand under the barrel ahead of the right.
  acts.wield('musket'); acts.act('aim'); run(r, acts, 1.4, o);
  const rf = acts.gripFrame('r'), lf = acts.gripFrame('l');
  const axis = figDir(r, rf.a), rp = figure(r, rf.pos), lp = figure(r, lf.pos);
  assert(axis.z > 0.95 && lp.z > rp.z + 0.25 && lp.distanceTo(rp.clone().addScaledVector(axis, 0.42)) < 0.12,
    `${asset} LOD${lod}: a musket at the shoulder, the left hand under the barrel (right ${f3(rp)}, left ${f3(lp)}, axis ${f3(axis)})`);
  // Struck: both hands to the body.
  acts.wield('none'); acts.act('struck'); run(r, acts, 1.0, o);
  const torso = figure(r, world(r.bone('spine_02')));
  for (const s of ['l', 'r']) {
    const h = figure(r, world(r.bone(`hand_${s}`)));
    assert(h.distanceTo(torso) < 0.33 && h.z > torso.z, `${asset} LOD${lod}: struck, the ${s} hand to the body (${f3(h)} by ${f3(torso)})`);
  }
  void headY;
}
console.log('human fight on the real figures: PASS');

// The weapon is laid in the hand: a tomahawk's head goes where the grip's thumb side points.
{
  const grp = new THREE.Group(), w = FM.weaponGroup('tomahawk'); grp.add(w);
  const frame = { pos: new THREE.Vector3(1, 2, 3), a: new THREE.Vector3(0, 1, 0), f: new THREE.Vector3(0, 0, 1), p: new THREE.Vector3(1, 0, 0), scale: 1 };
  FM.placeWeapon(w, frame);
  w.updateMatrixWorld(true);
  const head = new THREE.Vector3(0, 0.36, 0.06).applyMatrix4(w.matrixWorld);
  assert(head.y > 2.3 && head.z > 3.02, `the tomahawk's head above and ahead of the fist (${f3(head)})`);
  const p = FM.weaponGroup('pistol'); grp.add(p); FM.placeWeapon(p, frame);
  const z = FM.muzzleOf(p);
  assert(z && z.dir.z > 0.99 && z.at.z > 3.2, `a pistol's muzzle ahead along the hand (${f3(z.at)})`);
}
console.log('weapons laid in the hand: PASS');
