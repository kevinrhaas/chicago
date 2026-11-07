// SPDX-License-Identifier: GPL-3.0-or-later
// T-3402: the people on foot are alive (renderers/web/js/human-life.js), on the real
// Otis Bardwell export and its real clips, and on the CI fixture, on the CPU (no WebGL).
// It must: bind to the contract skeleton and refuse anything else; breathe, sway, look
// around and shift its weight; keep both feet planted while it does (the loaded leg
// straight, the free knee softened, nothing sinking or sliding); look at a visitor close
// in front and never crane round at one behind; attend to a point when told; blink at an
// irregular natural interval; hold a held frame (no accumulation through three's
// skip-unchanged track writes); keep its state across a LOD swap; and be deterministic.
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
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const driverLife = data(await js('driver-life.js'));
const { createHumanLife, LIFE_MODES } = await import(data((await js('human-life.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));

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

// A rig that is not the contract skeleton is left alone.
assert.equal(createHumanLife({ id: 'x', scene: new THREE.Group() }), null);
for (const s of ['standing', 'walking', 'talking', 'working', 'seated']) assert(LIFE_MODES[s], `a mode for ${s}`);

/** The figure as humans.js stands it: a root turned to its heading, the body inside. */
async function rig(asset, lod, clip, heading = 0.7) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  const root = new THREE.Group(); root.position.set(4, 0.3, -7); root.rotation.y = heading; root.add(gltf.scene);
  const mixer = new THREE.AnimationMixer(gltf.scene);
  mixer.clipAction(gltf.animations.find(a => a.name === clip)).play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bone = name => { let b = null; gltf.scene.traverse(o => { if (o.isBone && o.name === name) b = o; }); return b; };
  return { root, scene: gltf.scene, mixer, bone, clip: gltf.animations.find(a => a.name === clip) };
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
const facing = (head) => new THREE.Vector3(0, 0, 1).applyQuaternion(head.getWorldQuaternion(new THREE.Quaternion()));
const ang = (a, b) => Math.acos(Math.min(1, a.dot(b) / a.length() / b.length())) * 180 / Math.PI;

for (const [asset, lod, clip] of [['bardwell_otis_1835', 0, 'idle_natural_v1'], ['bardwell_otis_1835', 3, 'idle'], ['c4d_fixture', 1, 'idle']]) {
  const r = await rig(asset, lod, clip);
  const head = r.bone('head'), feet = ['ball_l', 'ball_r', 'foot_l', 'foot_r'].map(r.bone);
  const life = createHumanLife({ id: `t3402:${asset}`, scene: r.scene });
  assert(life, `${asset} LOD${lod}: the contract skeleton binds`);
  for (const n of ['pelvis', 'spine_02', 'neck_01', 'head', 'thigh_l', 'calf_r', 'foot_l', 'eye_l']) assert(life.bones.includes(n), n);
  // A twin with no life, on the same clip, to measure against frame by frame.
  const twin = await rig(asset, lod, clip);
  const twinHead = twin.bone('head'), twinFeet = ['ball_l', 'ball_r', 'foot_l', 'foot_r'].map(twin.bone);

  let maxSlide = 0, maxSink = 0, maxLift = 0, maxTurn = 0, maxHips = 0, blinks = 0, prevBlink = 0;
  const kinds = new Set(), sides = new Set(), blinkAt = [];
  const dt = 1 / 30;
  for (let i = 0; i < 1800; i++) {
    r.mixer.update(dt); twin.mixer.update(dt);
    life.apply(dt, { state: 'standing', root: r.root, viewer: null });
    r.root.updateMatrixWorld(true); twin.root.updateMatrixWorld(true);
    feet.forEach((f, k) => {
      const a = world(f), b = world(twinFeet[k]);
      maxSlide = Math.max(maxSlide, Math.hypot(a.x - b.x, a.z - b.z));
      maxSink = Math.max(maxSink, b.y - a.y); maxLift = Math.max(maxLift, a.y - b.y);
    });
    maxTurn = Math.max(maxTurn, ang(facing(head), facing(twinHead)));
    maxHips = Math.max(maxHips, world(r.bone('pelvis')).distanceTo(world(twin.bone('pelvis'))));
    const s = life.snapshot();
    kinds.add(s.gaze); if (Math.abs(s.weight) > 0.4) sides.add(Math.sign(s.weight));
    if (s.blink > 0 && prevBlink === 0) { blinks++; blinkAt.push(i * dt); }
    prevBlink = s.blink;
    assert(Number.isFinite(head.quaternion.x + head.quaternion.w));
  }
  assert(maxTurn > 15 && maxTurn < 95, `${asset} LOD${lod}: looks around, not craning (head ${maxTurn.toFixed(1)} deg off the clip)`);
  assert(kinds.size >= 3, `${asset} LOD${lod}: several kinds of look: ${[...kinds]}`);
  assert(sides.size === 2, `${asset} LOD${lod}: the weight goes onto each leg in a minute`);
  assert(maxHips > 0.02 && maxHips < 0.05, `${asset} LOD${lod}: the hips carry over the loaded foot (${(maxHips * 100).toFixed(1)} cm)`);
  // Feet planted: the loaded leg straight on the ground, the free foot neither sunk nor slid.
  assert(maxSlide < 0.02, `${asset} LOD${lod}: feet do not slide (${(maxSlide * 100).toFixed(2)} cm)`);
  assert(maxSink < 0.006, `${asset} LOD${lod}: no foot sinks into the ground (${(maxSink * 1000).toFixed(1)} mm)`);
  assert(maxLift < 0.012, `${asset} LOD${lod}: no foot floats (${(maxLift * 1000).toFixed(1)} mm)`);
  // Blinks: natural count in a minute, irregular gaps.
  const gaps = blinkAt.slice(1).map((t, k) => t - blinkAt[k]);
  assert(blinks >= 8 && blinks <= 36, `${asset} LOD${lod}: ${blinks} blinks a minute`);
  assert(Math.max(...gaps) - Math.min(...gaps) > 1.5, `${asset} LOD${lod}: blinks are irregular`);

  // A visitor 2.5 m in front, a little to one side, at eye height: he is looked at.
  r.root.updateMatrixWorld(true);
  const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
  const left = new THREE.Vector3(1, 0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
  const eye = world(head);
  const visitor = eye.clone().addScaledVector(fwd, 2.3).addScaledVector(left, 1.0).add(new THREE.Vector3(0, 0.05, 0));
  let looking = 0;
  for (let i = 0; i < 900; i++) {
    r.mixer.update(dt); life.apply(dt, { state: 'standing', root: r.root, viewer: visitor }); r.root.updateMatrixWorld(true);
    if (ang(facing(head), visitor.clone().sub(world(head))) < 18) looking++;
  }
  assert(looking / 900 > 0.3, `${asset} LOD${lod}: looks at a visitor close in front (${(looking / 9).toFixed(0)}% of 30 s)`);
  // One behind him is not craned round at.
  const behind = eye.clone().addScaledVector(fwd, -2.5);
  let craned = 0;
  for (let i = 0; i < 600; i++) {
    r.mixer.update(dt); life.apply(dt, { state: 'standing', root: r.root, viewer: behind }); r.root.updateMatrixWorld(true);
    if (ang(facing(head), behind.clone().sub(world(head))) < 60) craned++;
  }
  assert.equal(craned, 0, `${asset} LOD${lod}: never cranes round at a visitor behind`);
  // attend(): told to look at a point off to his right, he does within a second and a half.
  const point = eye.clone().addScaledVector(fwd, 3).addScaledVector(left, -2.2).add(new THREE.Vector3(0, -0.4, 0));
  life.attend(point, 4);
  for (let i = 0; i < 45; i++) { r.mixer.update(dt); life.apply(dt, { state: 'standing', root: r.root }); }
  r.root.updateMatrixWorld(true);
  const off = ang(facing(head), point.clone().sub(world(head)));
  assert(off < 16, `${asset} LOD${lod}: attends to a point (${off.toFixed(1)} deg off)`);
  assert(life.snapshot().attending);
  life.attend(null);
  assert(!life.snapshot().attending);

  // A held frame holds.
  r.mixer.update(0); life.apply(0, { state: 'standing', root: r.root }); r.root.updateMatrixWorld(true);
  const a = [...feet.map(world), facing(head)];
  for (let i = 0; i < 20; i++) { r.mixer.update(0); life.apply(0, { state: 'standing', root: r.root }); }
  r.root.updateMatrixWorld(true);
  const b = [...feet.map(world), facing(head)];
  a.forEach((v, i) => assert(v.distanceTo(b[i]) < 1e-9, `${asset} LOD${lod}: a held frame holds (${i})`));
  console.log(`${asset} LOD${lod} ${clip}: head up to ${maxTurn.toFixed(1)} deg, ${kinds.size} kinds of look, hips ${(maxHips * 100).toFixed(1)} cm, feet within ${(maxSlide * 100).toFixed(2)} cm / sink ${(maxSink * 1000).toFixed(1)} mm / lift ${(maxLift * 1000).toFixed(1)} mm, ${blinks} blinks, visitor ${(looking / 9).toFixed(0)}%: PASS`);
}

// Walking: the gait's legs and pelvis are the clip's own; the head looks about.
{
  const r = await rig('bardwell_otis_1835', 1, 'walk'), twin = await rig('bardwell_otis_1835', 1, 'walk');
  const life = createHumanLife({ id: 'walker', scene: r.scene });
  const legs = ['pelvis', 'thigh_l', 'calf_r', 'foot_l', 'ball_r'];
  let maxLeg = 0, maxTurn = 0;
  for (let i = 0; i < 900; i++) {
    r.mixer.update(1 / 30); twin.mixer.update(1 / 30);
    life.apply(1 / 30, { state: 'walking', root: r.root });
    r.root.updateMatrixWorld(true); twin.root.updateMatrixWorld(true);
    for (const n of legs.slice(1)) maxLeg = Math.max(maxLeg, world(r.bone(n)).distanceTo(world(twin.bone(n))));
    maxTurn = Math.max(maxTurn, ang(facing(r.bone('head')), facing(twin.bone('head'))));
  }
  assert(maxLeg < 0.003, `walking: legs are the gait's (${(maxLeg * 1000).toFixed(2)} mm)`);
  assert(maxTurn > 10 && maxTurn < 70, `walking: glances about (${maxTurn.toFixed(1)} deg)`);
  console.log(`walking: legs within ${(maxLeg * 1000).toFixed(2)} mm of the gait, head up to ${maxTurn.toFixed(1)} deg: PASS`);
}

// A LOD swap keeps the life (where he looks, which leg he stands on).
{
  const r0 = await rig('bardwell_otis_1835', 0, 'idle'), r1 = await rig('bardwell_otis_1835', 2, 'idle');
  const life = createHumanLife({ id: 'swap', scene: r0.scene });
  for (let i = 0; i < 400; i++) { r0.mixer.update(1 / 30); life.apply(1 / 30, { root: r0.root }); }
  const before = life.snapshot();
  r1.root.remove(r1.scene); r0.root.add(r1.scene); r0.root.remove(r0.scene);
  assert(life.bind(r1.scene), 'rebinds to the next LOD');
  assert.deepEqual(life.snapshot(), before, 'the state carries across the swap');
  r1.mixer.update(1 / 30); life.apply(1 / 30, { root: r0.root });
  assert(Math.abs(life.snapshot().yaw_deg - before.yaw_deg) < 3, 'no snap after the swap');
}

// Deterministic: two binds of the same person run the same motion; two people differ.
{
  const runs = [];
  for (const id of ['same', 'same', 'other']) {
    const r = await rig('bardwell_otis_1835', 3, 'idle');
    const life = createHumanLife({ id, scene: r.scene });
    for (let i = 0; i < 300; i++) { r.mixer.update(1 / 30); life.apply(1 / 30, { root: r.root }); }
    r.root.updateMatrixWorld(true);
    runs.push(r.bone('head').quaternion.toArray());
  }
  runs[0].forEach((x, i) => assert(Math.abs(x - runs[1][i]) < 1e-12, 'same person, same motion'));
  assert(runs[0].some((x, i) => Math.abs(x - runs[2][i]) > 1e-4), 'two people move differently');
}
console.log('human life: PASS');
