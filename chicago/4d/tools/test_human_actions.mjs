// SPDX-License-Identifier: GPL-3.0-or-later
// T-3419 (from T-3415): what people on foot do with their arms (renderers/web/js/human-actions.js),
// over the life layer, on the real Otis Bardwell export and the CI fixture, on the CPU.
// It must: bind to the contract skeleton only; hang the arms in by the sides; put the
// hands on the hips and clasped behind the back where the poses say (two-bone IK, the
// hands outside the body); greet a visitor in front with a hand to the brow and a nod;
// swing the arms opposite the legs on the walk clip, as far as the stride; leave the
// legs and feet alone; hold a held frame; keep its state across a LOD swap; deterministic.
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
const { createHumanLife } = await import(data((await js('human-life.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));
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


assert.equal(createHumanActions({ id: 'x', scene: new THREE.Group() }), null, 'a non-contract rig is left alone');

async function rig(asset, lod, clip, heading = 0.7) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  const root = new THREE.Group(); root.position.set(4, 0.3, -7); root.rotation.y = heading; root.add(gltf.scene);
  const mixer = new THREE.AnimationMixer(gltf.scene);
  mixer.clipAction(gltf.animations.find(a => a.name === clip)).play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bone = name => { let b = null; gltf.scene.traverse(o => { if (o.isBone && o.name === name) b = o; }); return b; };
  return { root, scene: gltf.scene, mixer, bone };
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
/** A world point in the figure's frame (+X its left, +Z its front), from its root. */
const figure = (r, p) => p.clone().sub(r.root.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), -r.root.rotation.y);
const step = (r, life, acts, dt, opts) => { r.mixer.update(dt); life.apply(dt, opts); acts.apply(dt, opts); if (acts.takeNod()) life.nod(); r.root.updateMatrixWorld(true); };

for (const [asset, lod, clip] of [['bardwell_otis_1835', 0, 'idle_natural_v1'], ['bardwell_otis_1835', 3, 'idle'], ['c4d_fixture', 1, 'idle']]) {
  const r = await rig(asset, lod, clip), twin = await rig(asset, lod, clip);
  const life = createHumanLife({ id: `a:${asset}`, scene: r.scene }), acts = createHumanActions({ id: `a:${asset}`, scene: r.scene });
  assert(acts, `${asset} LOD${lod}: binds`);
  const opts = { state: 'standing', root: r.root };
  const hipHalf = world(r.bone('thigh_l')).distanceTo(world(r.bone('thigh_r'))) / 2;
  // Rest: the arms come in from the clip's splay, the hands still clear of the thighs.
  acts.setPose('rest');
  for (let i = 0; i < 60; i++) { step(r, life, acts, 1 / 30, opts); twin.mixer.update(1 / 30); }
  twin.root.updateMatrixWorld(true);
  const restX = Math.abs(figure(r, world(r.bone('hand_l'))).x), clipX = Math.abs(figure(twin, world(twin.bone('hand_l'))).x);
  assert(restX < clipX - 0.03 && restX > hipHalf + 0.05, `${asset} LOD${lod}: arms hang in (${clipX.toFixed(3)} → ${restX.toFixed(3)} m from the midline)`);
  // T-3456 (owner, 2026-11-07: "my thumbs point forward"): a hanging hand's thumb is ahead of
  // its little finger, and its palm (index knuckle side) faces the thigh, on both sides.
  for (const s of ['l', 'r']) {
    if (!r.bone(`thumb_02_${s}`) || !r.bone(`pinky_01_${s}`)) continue;
    const thumbZ = figure(r, world(r.bone(`thumb_02_${s}`))).z, pinkyZ = figure(r, world(r.bone(`pinky_01_${s}`))).z;
    assert(thumbZ > pinkyZ + 0.02, `${asset} LOD${lod}: the ${s} hand hangs thumb forward (thumb z ${thumbZ.toFixed(3)}, little finger z ${pinkyZ.toFixed(3)})`);
  }
  const feet0 = ['foot_l', 'foot_r'].map(n => world(r.bone(n)));
  // Hands on the hips.
  acts.setPose('hips');
  for (let i = 0; i < 75; i++) step(r, life, acts, 1 / 30, opts);
  for (const s of ['l', 'r']) {
    const sx = s === 'l' ? 1 : -1, w = figure(r, world(r.bone(`hand_${s}`))), e = figure(r, world(r.bone(`lowerarm_${s}`)));
    const pelvisY = figure(r, world(r.bone('pelvis'))).y;
    assert(sx * w.x > hipHalf + 0.05 && sx * w.x < hipHalf + 0.16 && Math.abs(w.y - pelvisY - 0.07) < 0.05 && Math.abs(w.z) < 0.06,
      `${asset} LOD${lod}: ${s} hand on the hip (${w.toArray().map(x => x.toFixed(3))})`);
    assert(sx * e.x > sx * w.x + 0.04 && e.z < w.z, `${asset} LOD${lod}: ${s} elbow out and back`);
  }
  // Hands behind the back.
  acts.setPose('behind');
  for (let i = 0; i < 75; i++) step(r, life, acts, 1 / 30, opts);
  const spineZ = figure(r, world(r.bone('pelvis'))).z;
  for (const s of ['l', 'r']) {
    const w = figure(r, world(r.bone(`hand_${s}`)));
    assert(w.z < spineZ - 0.12 && Math.abs(w.x) < 0.12, `${asset} LOD${lod}: ${s} hand behind the back (${w.toArray().map(x => x.toFixed(3))})`);
  }
  // A visitor 2.5 m in front is greeted: right hand to the brow, and a nod.
  const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
  const viewer = world(r.bone('head')).addScaledVector(fwd, 2.5);
  let greeted = false, nearest = 9;
  for (let i = 0; i < 90; i++) {
    step(r, life, acts, 1 / 30, { ...opts, viewer });
    if (acts.snapshot().greeting) {
      greeted = true;
      const brow = figure(r, world(r.bone('eye_l')).add(world(r.bone('eye_r'))).multiplyScalar(0.5)).add(new THREE.Vector3(-0.072, 0.065, 0.03));
      nearest = Math.min(nearest, figure(r, world(r.bone('middle_03_r'))).distanceTo(brow));
    }
  }
  assert(greeted && nearest < 0.07, `${asset} LOD${lod}: greets with the fingertips to the brow (${nearest.toFixed(3)} m)`);
  // The feet were never touched by the arms.
  ['foot_l', 'foot_r'].forEach((n, k) => assert(world(r.bone(n)).distanceTo(feet0[k]) < 0.03, `${asset} LOD${lod}: ${n} stays put`));
  // A held frame holds.
  step(r, life, acts, 0, opts);
  const a = ['hand_l', 'hand_r', 'lowerarm_l', 'index_03_r'].map(n => world(r.bone(n)));
  for (let i = 0; i < 10; i++) step(r, life, acts, 0, opts);
  ['hand_l', 'hand_r', 'lowerarm_l', 'index_03_r'].forEach((n, k) => assert(world(r.bone(n)).distanceTo(a[k]) < 1e-9, `${asset} LOD${lod}: held frame holds (${n})`));
  console.log(`${asset} LOD${lod}: arms in ${clipX.toFixed(2)}→${restX.toFixed(2)} m, hips, behind, fingertips ${nearest.toFixed(3)} m from the brow: PASS`);
}

// A figure in the dress assembly (T-3423) greets with the nod alone: no hand to the brow.
{
  const r = await rig('flynn_mary_1835_dress_study', 0, 'idle');
  const life = createHumanLife({ id: 'n', scene: r.scene }), acts = createHumanActions({ id: 'n', scene: r.scene, greeting: 'nod' });
  const opts = { state: 'standing', root: r.root };
  acts.setPose('rest');
  for (let i = 0; i < 60; i++) step(r, life, acts, 1 / 30, opts);
  const hand0 = world(r.bone('hand_r'));
  const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
  const viewer = world(r.bone('head')).addScaledVector(fwd, 2.5);
  let greeted = false, nodded = false, rise = 0;
  for (let i = 0; i < 90; i++) {
    r.mixer.update(1 / 30); life.apply(1 / 30, { ...opts, viewer }); acts.apply(1 / 30, { ...opts, viewer });
    if (acts.takeNod()) { nodded = true; life.nod(); }
    r.root.updateMatrixWorld(true);
    greeted ||= acts.snapshot().greeting;
    rise = Math.max(rise, world(r.bone('hand_r')).y - hand0.y);
  }
  assert(nodded && !greeted && rise < 0.12, `a dressed figure nods without raising the hand (nod ${nodded}, arm greeting ${greeted}, hand rose ${rise.toFixed(3)} m)`);
  console.log(`flynn_mary_1835_dress_study LOD0: nods, hand rose ${rise.toFixed(3)} m: PASS`);
}

// A woman in a full skirt (T-3434): her hands never hang into the skirt's bell. Kevin saw a
// hand sink into Mattie's skirt; every skirt pose keeps the hand and fingertips outside the
// skirt and apron (posed, skinned), and 'rest' is refused.
{
  const { SKIRT_POSES } = await import(data((await js('human-actions.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));
  const r = await rig('williamson_mattie_1904_cook_study', 0, 'idle');
  const life = createHumanLife({ id: 'skirt', scene: r.scene }), acts = createHumanActions({ id: 'skirt', scene: r.scene, greeting: 'nod', skirt: true });
  assert(acts, 'the 1904 woman binds');
  assert.equal(acts.pose, 'clasp', 'a woman in a skirt starts with her hands clasped, not hanging');
  acts.setPose('rest'); acts.setPose('hips');
  assert.equal(acts.pose, 'clasp', 'a woman in a skirt never lets her hands hang or sets them on her hips');
  const cloth = [];
  r.scene.traverse(o => { if (o.isSkinnedMesh && /^garment_(lower|outer)/.test(o.material?.name ?? '')) cloth.push(o); });
  assert(cloth.length >= 2, 'the skirt and apron are found');
  const pelvis = () => world(r.bone('pelvis'));
  const probes = ['hand', 'index_03', 'middle_03', 'ring_03', 'pinky_03', 'thumb_03'];
  for (const name of SKIRT_POSES) {
    acts.setPose(name);
    for (let i = 0; i < 75; i++) step(r, life, acts, 1 / 30, { state: 'standing', root: r.root });
    const axis = pelvis(), pts = [];
    for (const m of cloth) {
      const pos = m.geometry.attributes.position, v = new THREE.Vector3();
      for (let i = 0; i < pos.count; i += 1) { m.getVertexPosition(i, v); pts.push(v.clone().applyMatrix4(m.matrixWorld)); }
    }
    let worst = Infinity, at = '';
    for (const s of ['l', 'r']) for (const pr of probes) {
      const b = r.bone(`${pr}_${s}`);
      if (!b) continue;
      const p = world(b);
      let best = null, bd = Infinity;
      for (const q of pts) { const d = q.distanceToSquared(p); if (d < bd) { bd = d; best = q; } }
      if (!best || Math.sqrt(bd) > 0.08) continue;
      const out = best.clone().sub(axis).setY(0).normalize();
      const depth = p.clone().sub(best).dot(out);
      if (depth < worst) { worst = depth; at = `${pr}_${s}`; }
    }
    assert(worst > -0.012, `${name}: ${at} is ${(-worst * 100).toFixed(1)} cm inside the skirt`);
    console.log(`skirt pose ${name}: hands outside the skirt (closest ${Number.isFinite(worst) ? (worst * 100).toFixed(1) + ' cm' : 'clear'}): PASS`);
  }
}

// Walking: the arms swing opposite the legs, as far as the stride.
{
  const r = await rig('bardwell_otis_1835', 1, 'walk');
  const life = createHumanLife({ id: 'w', scene: r.scene }), acts = createHumanActions({ id: 'w', scene: r.scene });
  const opts = { state: 'walking', root: r.root };
  let corr = 0, n = 0, minZ = 9, maxZ = -9;
  for (let i = 0; i < 240; i++) {
    step(r, life, acts, 1 / 30, opts);
    if (i < 60) continue;
    const hz = figure(r, world(r.bone('hand_l'))).z, fz = figure(r, world(r.bone('foot_l'))).z - figure(r, world(r.bone('foot_r'))).z;
    corr += hz * fz; n++; minZ = Math.min(minZ, hz); maxZ = Math.max(maxZ, hz);
  }
  assert(corr / n < 0, 'walking: the left hand comes forward as the left foot goes back');
  assert(maxZ - minZ > 0.12 && maxZ - minZ < 0.45, `walking: the hand swings ${(maxZ - minZ).toFixed(3)} m`);
  console.log(`walking: left hand swings ${((maxZ - minZ) * 100).toFixed(1)} cm, opposite the left foot: PASS`);
}

// Deterministic, and a LOD swap keeps the pose.
{
  const runs = [];
  for (const k of [0, 1]) {
    const r = await rig('bardwell_otis_1835', 3, 'idle');
    const life = createHumanLife({ id: 'same', scene: r.scene }), acts = createHumanActions({ id: 'same', scene: r.scene });
    for (let i = 0; i < 900; i++) step(r, life, acts, 1 / 30, { root: r.root });
    runs.push([...world(r.bone('hand_l')).toArray(), acts.snapshot().pose]);
    if (k === 1) {
      const next = await rig('bardwell_otis_1835', 2, 'idle');
      const before = acts.snapshot();
      next.root.remove(next.scene); r.root.add(next.scene); r.root.remove(r.scene);
      assert(acts.bind(next.scene), 'rebinds');
      assert.deepEqual(acts.snapshot(), before, 'the pose carries across a LOD swap');
    }
  }
  assert.deepEqual(runs[0], runs[1], 'same person, same actions');
}
console.log('human actions: PASS');
