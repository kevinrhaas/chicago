// SPDX-License-Identifier: GPL-3.0-or-later
// T-1790: the seated driver's motion layer (renderers/web/js/driver-life.js) on the
// real named 1904 driver export and its real seated clip, on the CPU (no WebGL).
// It must: bind to the contract skeleton; move (breathing, looks, weight); stay
// bounded (no accumulation through three's skip-unchanged track writes, a held
// frame holds); keep the hands near the reins' clip position; be deterministic.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const lifeSource = (await fs.readFile(new URL('renderers/web/js/driver-life.js', here), 'utf8')).replace("from 'three'", `from '${three}'`);
const { createDriverLife, seededRandom } = await import(data(lifeSource));

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

// The PRNG is a pure function of the id.
{ const a = seededRandom('x'), b = seededRandom('x'), c = seededRandom('y');
  const sa = [a(), a(), a()], sb = [b(), b(), b()];
  assert.deepEqual(sa, sb); assert.notDeepEqual(sa, [c(), c(), c()]); assert(sa.every(x => x >= 0 && x < 1)); }

// A rig that is not the contract skeleton is left alone.
assert.equal(createDriverLife({ root: new THREE.Group(), scene: new THREE.Group() }), null);

async function rig(lod, asset = 'anonymous_working_driver_1904') {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  const root = new THREE.Group(); root.rotation.y = Math.PI; root.add(gltf.scene);
  const mixer = new THREE.AnimationMixer(gltf.scene);
  mixer.clipAction(gltf.animations.find(a => a.name === 'sit_drive_look_v2')).play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bone = name => { let b = null; gltf.scene.traverse(o => { if (o.isBone && o.name === name) b = o; }); return b; };
  return { root, scene: gltf.scene, mixer, bone };
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
const facing = (head) => new THREE.Vector3(0, 0, 1).applyQuaternion(head.getWorldQuaternion(new THREE.Quaternion()));

for (const [asset, lod] of [['anonymous_working_driver_1904', 0], ['anonymous_working_driver_1904', 3], ['bardwell_otis_1835', 0]]) {
  const r = await rig(lod, asset);
  const head = r.bone('head'), hands = ['hand_l', 'hand_r'].map(r.bone);
  // Where the clip alone puts the hands and the head, at a few clip times.
  const clipHands = [], clipFacing = [];
  for (let k = 0; k < 8; k++) {
    r.mixer.setTime(k); r.root.updateMatrixWorld(true);
    clipHands.push(hands.map(world)); clipFacing.push(facing(head));
  }
  r.mixer.setTime(0); r.root.updateMatrixWorld(true);
  const life = createDriverLife({ root: r.root, scene: r.scene, id: 'pa1904_otis_f_r_c1900_hans_johnson', gaitCycle_m: 1.6 });
  assert(life, `LOD${lod}: the contract skeleton binds`);
  for (const n of ['pelvis', 'spine_02', 'neck_01', 'head', 'upperarm_l', 'lowerarm_r', 'hand_l']) assert(life.bones.includes(n), n);

  // Sixty seconds on the move at 1/30 s: track the head's facing and the hands.
  let dist = 0, minDot = 1, maxHandShift = 0;
  const yaws = new Set(), kinds = new Set();
  const viewer = new THREE.Vector3(3, 2.2, 4);
  for (let i = 0; i < 1800; i++) {
    const dt = 1 / 30; dist += 1.8 * dt;
    r.mixer.update(dt);
    life.apply(dt, { distance_m: dist, curvature: i > 900 && i < 1200 ? 1 / 18 : 0, moving: true }, i > 1500 ? viewer : null);
    r.root.updateMatrixWorld(true);
    const f = facing(head);
    for (const c of clipFacing) minDot = Math.min(minDot, f.dot(c));
    const now = hands.map(world);
    const nearest = Math.min(...clipHands.map(h => Math.max(h[0].distanceTo(now[0]), h[1].distanceTo(now[1]))));
    maxHandShift = Math.max(maxHandShift, nearest);
    const snap = life.snapshot();
    yaws.add(Math.round(snap.yaw_deg / 10)); kinds.add(snap.gaze);
    for (const q of r.scene.children.length ? [head.quaternion] : []) assert(Number.isFinite(q.x + q.y + q.z + q.w));
  }
  const spread = Math.acos(Math.min(1, minDot)) * 180 / Math.PI;
  assert(spread > 15, `LOD${lod}: he looks around (head turns ${spread.toFixed(1)} deg from the clip's facings)`);
  assert(spread < 100, `LOD${lod}: he does not crane round (${spread.toFixed(1)} deg)`);
  assert(yaws.size >= 4 && kinds.size >= 3, `LOD${lod}: several looks: ${[...kinds]}`);
  // The hands move to the lap and play the reins, but stay within reach of the clip's.
  assert(maxHandShift > 0.02 && maxHandShift < 0.22, `LOD${lod}: hands stay on the reins (${maxHandShift.toFixed(3)} m)`);

  // A held frame holds (dt 0 twice reproduces the pose: nothing accumulates through
  // channels the mixer does not rewrite).
  r.mixer.update(0); life.apply(0, { distance_m: dist, moving: false }); r.root.updateMatrixWorld(true);
  const a = hands.map(world).concat([facing(head)]);
  for (let i = 0; i < 20; i++) { r.mixer.update(0); life.apply(0, { distance_m: dist, moving: false }); }
  r.root.updateMatrixWorld(true);
  const b = hands.map(world).concat([facing(head)]);
  a.forEach((v, i) => assert(v.distanceTo(b[i]) < 1e-9, `LOD${lod}: a held frame holds (${i})`));
  console.log(`${asset} LOD${lod}: head turns up to ${spread.toFixed(1)} deg, ${kinds.size} kinds of look, hands within ${(maxHandShift * 100).toFixed(1)} cm of the clip: PASS`);
}

// Deterministic: two binds of the same person run the same motion.
{
  const runs = [];
  for (let k = 0; k < 2; k++) {
    const r = await rig(3);
    const life = createDriverLife({ root: r.root, scene: r.scene, id: 'same' });
    for (let i = 0; i < 300; i++) { r.mixer.update(1 / 30); life.apply(1 / 30, { distance_m: i * 0.06, moving: true }); }
    r.root.updateMatrixWorld(true);
    runs.push(r.bone('head').quaternion.toArray());
  }
  runs[0].forEach((x, i) => assert(Math.abs(x - runs[1][i]) < 1e-12, 'same person, same motion'));
}
console.log('driver life: PASS');
