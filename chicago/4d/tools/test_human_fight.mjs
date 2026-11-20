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

// ---- the blood (human-blood.js), on the same real figures: a wound stains the figure where the
// blow came from, on its own clothing, carried by the bone under it; its drops fall and lie on
// the ground; nothing pools under someone standing, and once they are down a pool spreads under
// the wound, not under the feet; a change of level keeps the stains on the same bones; a figure
// let go takes its stains; clear() washes it all away.
const BL = await import(data(await js('human-blood.js')));
{
  const a = BL.blotAlpha(7), b = BL.blotAlpha(7), c = BL.blotAlpha(8);
  assert.deepEqual(a, b, 'a blot is the same blot every time');
  assert.notDeepEqual(a, c, 'another seed, another blot');
  const at = (i, j) => a[(j * 64 + i) * 4 + 3];
  assert(at(32, 32) === 255 && at(0, 0) === 0 && at(63, 63) === 0, 'solid in the middle, clear at the corners');
}
const UPV = new THREE.Vector3(0, 1, 0);
for (const [asset, lod, clip] of [['bardwell_otis_1835', 0, 'idle_natural_v1'], ['bardwell_otis_1835', 3, 'idle'], ['c4d_fixture', 1, 'idle']]) {
  const name = `${asset} LOD${lod}`;
  const r = await rig(asset, lod, clip);
  r.root.rotation.order = 'YXZ';
  const parent = new THREE.Group(); parent.add(r.root); parent.updateMatrixWorld(true);
  const skinned = (scene) => { const m = []; scene.traverse((o) => { if (o.isSkinnedMesh) m.push(o); }); return m; };
  const actor = { root: r.root, body: { scene: r.scene, meshes: skinned(r.scene) }, posture: null, heightAt: () => 0.3, e: 4, n: 7, standY: null };
  const fx = BL.createBloodFx(parent);
  const ahead = new THREE.Vector3(0, 0, 1).applyAxisAngle(UPV, r.root.rotation.y);
  const from = r.root.position.clone().addScaledVector(ahead, 2);
  assert(fx.wound(actor, 'body', { from }), `${name}: wounded`);
  let n = fx.counts;
  assert(n.stains === 1 && n.drops === BL.WOUND.body.drops && n.pools === 0, `${name}: a stain and its drops (${JSON.stringify(n)})`);
  const stain = r.scene.getObjectByName('wound_body');
  assert(stain?.parent?.isBone && stain.parent.name === 'spine_03', `${name}: the stain is carried by the chest's bone (${stain?.parent?.name})`);
  const chest = figure(r, world(r.bone('spine_03'))), sp = figure(r, world(stain));
  assert(sp.z > chest.z + 0.04 && sp.z < chest.z + 0.32 && Math.abs(sp.y - chest.y) < 0.15, `${name}: on the front of the chest, toward the blow (${f3(sp)} by ${f3(chest)})`);
  const facing = new THREE.Vector3(0, 0, 1).transformDirection(stain.matrixWorld);
  assert(facing.dot(ahead) > 0.3, `${name}: laid on the surface, facing out toward the blow (${f3(facing)})`);
  // On the figure's own surface: a ray in along the stain's facing meets the body within 2 cm.
  const ray = new THREE.Raycaster(world(stain).addScaledVector(facing, 0.3), facing.clone().negate(), 0, 0.6);
  const hit = ray.intersectObjects(actor.body.meshes, false)[0];
  assert(hit && Math.abs(hit.distance - 0.3) < 0.02, `${name}: on the clothing itself (${hit?.distance?.toFixed(3)} m along a 0.3 m ray)`);
  // The drops fall and lie where they land, on the ground, round the figure.
  for (let t = 0; t < 2; t += 1 / 30) fx.update(1 / 30);
  n = fx.counts;
  assert(n.drops <= 1 && n.splats >= BL.WOUND.body.drops, `${name}: every drop thrown has landed; one still drips from him (${JSON.stringify(n)})`);
  for (const s of fx.splatsAt) {
    assert(Math.abs(s.y - 0.304) < 0.002, `${name}: a drop lies on the ground (${s.y.toFixed(3)})`);
    assert(Math.hypot(s.x - r.root.position.x, s.z - r.root.position.z) < 3, `${name}: near the figure (${f3(s)})`);
  }
  // A head wound and a scalping: on the head's bone, the scalping on the crown.
  fx.wound(actor, 'head', { from });
  const head = r.scene.getObjectByName('wound_head'), hb = figure(r, world(r.bone('head')));
  assert(head?.parent?.name === 'head' && figure(r, world(head)).z > hb.z + 0.03, `${name}: a blow to the head marks the face of the head`);
  fx.wound(actor, 'scalp', { from });
  const crown = figure(r, world(r.scene.getObjectByName('wound_scalp')));
  assert(crown.y > hb.y + 0.12 && Math.hypot(crown.x - hb.x, crown.z - hb.z) < 0.12, `${name}: a scalping is on the crown (${f3(crown)} by the head's bone ${f3(hb)})`);
  fx.update(0.1);
  assert.equal(fx.counts.pools, 0, `${name}: nothing pools under someone standing`);
  // Down, face down along the heading: a pool spreads under the chest, not the feet.
  actor.posture = { kind: 'fallen', w: 1 };
  r.root.rotation.x = Math.PI / 2; r.root.position.y = 0.42; r.root.updateMatrixWorld(true);
  fx.update(0.1);
  assert(fx.counts.pools >= 1, `${name}: once down, a pool`);
  for (let t = 0; t < BL.POOL_GROW_S + 1; t += 0.5) fx.update(0.5);
  const body = fx.pools.reduce((p, q) => (q.target > p.target ? q : p));
  const off = new THREE.Vector3(body.x - r.root.position.x, 0, body.z - r.root.position.z);
  assert(Math.abs(body.y - 0.306) < 0.01 && body.r > 0.4 && body.r <= 1.0 && Math.abs(body.r - body.target) < 1e-3, `${name}: spread to its size on the ground (r ${body.r.toFixed(2)} m)`);
  assert(off.dot(ahead) > 0.6 && off.length() < 1.8, `${name}: under the fallen body, not the feet (${off.dot(ahead).toFixed(2)} m along the heading)`);
  // A change of level: the stains go onto the same bones of the new body, where they were.
  const before = stain.position.clone();
  const r2 = await rig(asset, lod, clip);
  r.root.remove(r.scene); r.root.add(r2.scene);
  actor.body = { scene: r2.scene, meshes: skinned(r2.scene) };
  fx.update(0.1);
  assert(stain.parent?.isBone && stain.parent.name === 'spine_03' && r2.scene.getObjectById(stain.parent.id) && stain.position.distanceTo(before) < 1e-9,
    `${name}: after a change of level the stain is on the new body's chest`);
  assert.equal(fx.counts.stains, 3, `${name}: every stain kept`);
  // Let go: its stains go with it; the ground keeps its blood until the stop is left.
  actor.disposed = true; fx.update(0.1);
  n = fx.counts;
  assert(n.wounded === 0 && n.stains === 0 && !stain.parent && n.pools >= 1, `${name}: a figure let go takes its stains (${JSON.stringify(n)})`);
  fx.clear();
  n = fx.counts;
  assert(n.pools === 0 && n.splats === 0 && n.drops === 0 && !parent.getObjectByName('blood_pool'), `${name}: cleared, nothing left`);
}
{
  // Without a parent nothing is drawn and nothing breaks.
  const fx = BL.createBloodFx(null);
  assert.equal(fx.wound({ root: new THREE.Group() }, 'body'), false); fx.update(0.1); fx.clear();
}
console.log('blood and wounds on the real figures: PASS');

// ---- the burning of the fort (T-3553, the owner, 2026-11-16): a firebrand carried and put to the
// logs (human-fight.js torch, kindle), and the burn (fort-fire.js): a building catches where the
// brand touches it, blackens, falls in and leaves a heap; a neighbour catches from its heat; what
// stands is only smoked; and when the stage is let go every piece is given back as it was.
{
  const torch = FM.weaponGroup('torch');
  assert(torch && torch.userData.tip && torch.userData.tip.position.y > 0.45, 'a brand, its burning head at the top of the stick');
  assert(FM.MOTIONS.kindle.for.includes('torch') && FM.MOTIONS.kindle.hit > 0.3 && FM.MOTIONS.kindle.hit < FM.motionLength('kindle', 'torch'),
    'kindle: reached out to the logs, and the fire takes partway through');
  const reach = FM.fightTargets({ arm: 'torch', act: 'kindle', t: 1.0 });
  const ready = FM.fightTargets({ arm: 'torch' });
  assert(reach.r.at[2] > ready.r.at[2] + 0.2 && reach.r.at[1] < ready.r.at[1], 'the brand goes out and down to the wall, from carried high before the body');
  const F = await import(data(await js('fort-fire.js')));
  const batch = new THREE.BatchedMesh(10, 2000, 4000, new THREE.MeshStandardMaterial());
  const g1 = new THREE.BoxGeometry(6, 5, 4); g1.translate(0, 2.5, 0);
  const g2 = new THREE.BoxGeometry(3, 3, 3); g2.translate(0, 1.5, 0);
  const a = batch.addInstance(batch.addGeometry(g1)), b = batch.addInstance(batch.addGeometry(g2)), c = batch.addInstance(batch.addGeometry(g2));
  batch.setMatrixAt(b, new THREE.Matrix4().makeTranslation(9, 0, 0)); batch.setMatrixAt(c, new THREE.Matrix4().makeTranslation(-5.5, 0, 0));
  for (const i of [a, b, c]) batch.setColorAt(i, new THREE.Color(0.8, 0.7, 0.6));
  batch.userData.batchIndex = ['house', 'shed', 'magazine'];
  const scene = new THREE.Scene(); scene.add(batch);
  const gate = new THREE.Group(); gate.matrixAutoUpdate = false; scene.add(gate);
  let undone = 0;
  const fire = F.createFortFire({ parent: scene, buildings: () => ({ batches: [batch] }), groundAt: () => 0, extras: (id) => (id === 'house' ? [gate] : []),
    nameOf: (id) => `the ${id}`, setup: () => () => { undone++; } });
  fire.start({ burns: ['house', 'shed'], stands: ['magazine'], liberty: 'L-x', visitor: true });
  const cam = new THREE.PerspectiveCamera(); cam.position.set(0, 2, 30); cam.updateMatrixWorld();
  const paint = () => batch.getColorAt(a, new THREE.Color()).r, height = (i) => batch.getMatrixAt(i, new THREE.Matrix4()).elements[5];
  const at = (t) => { while (fire.clock < t - 1e-6) fire.update(0.25, cam); return fire.snapshot(); };
  assert.deepEqual(fire.kindle(new THREE.Vector3(60, 1, 0), 30), { none: 'far', nearest: 'the shed', distance: 50 }, 'too far from any building to set it alight');
  assert(fire.ignite('house', new THREE.Vector3(3, 1, 0)), 'the house catches at the brand');
  let s = at(20);
  assert(s.flames >= 6 && s.smoke > 20 && s.sparks > 20 && paint() < 0.75, `alight: flames, smoke and sparks, the logs darkening (${JSON.stringify({ ...s, burns: undefined })})`);
  assert(s.burns.find((x) => x.id === 'shed').lit === null, 'the shed has not caught yet');
  s = at(48);
  assert(s.burns.find((x) => x.id === 'shed').lit !== null, 'the heat carries to the shed beside it');
  assert(paint() < 0.1, `the house's logs are charred black (${paint().toFixed(3)})`);
  s = at(110);
  const house = s.burns.find((x) => x.id === 'house');
  assert(house.down === 1 && house.heap && height(a) === 0, 'the house has fallen in, and lies as a heap');
  assert(gate.matrix.elements[5] < 1 || !gate.visible, 'what hung on it (a gate) came down with it');
  const mag = s.burns.find((x) => x.id === 'magazine');
  assert(mag.char > 0.05 && height(c) === 1, `the magazine stands, smoked (${mag.char})`);
  const heap = scene.getObjectByName('fort-fire:heap:house');
  assert(heap && heap.scale.y > 0.99, 'the heap of charcoal and ash where it stood');
  s = at(260);
  assert(s.flames <= 2 && s.burns.every((x) => x.kind === 'stands' || x.down === 1), `burned out to ash, a little smoke still going up (${s.flames} flames, ${s.smoke} puffs)`);
  assert.deepEqual(fire.kindle(new THREE.Vector3(0, 1, 5)), { none: 'all' }, 'nothing left that will burn');
  fire.clear();
  assert(paint() === 0.800000011920929 && height(a) === 1 && batch.getMatrixAt(b, new THREE.Matrix4()).elements[12] === 9 && gate.visible && undone === 1,
    'let go: every piece back as it was, and the gates given back');
  assert(!scene.getObjectByName('fort-fire:heap:house'), 'and no heap left');
  // Already burning when the visitor comes: run on unseen to where it has got to.
  fire.start({ burns: ['house', 'shed'], liberty: 'L-x', lit: ['house'], start_s: 70 });
  s = fire.snapshot();
  assert(s.clock === 0 && s.burns.find((x) => x.id === 'house').lit < -60 && s.burns.find((x) => x.id === 'shed').lit !== null, 'a fire seen from the next stop is well on when the visitor comes');
  fire.dispose();
}
console.log('the burning of the fort: PASS');
