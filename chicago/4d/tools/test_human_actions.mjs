// SPDX-License-Identifier: GPL-3.0-or-later
// T-3419 (from T-3415): what people on foot do with their arms (renderers/web/js/human-actions.js),
// over the life layer, on the real Otis Bardwell export and the CI fixture, on the CPU.
// It must: bind to the contract skeleton only; hang the arms in by the sides; put the
// hands on the hips and clasped behind the back where the poses say (two-bone IK, the
// hands outside the body); greet a visitor in front with a hand to the brow and a nod;
// swing the arms opposite the legs on the walk clip, as far as the stride; leave the
// legs and feet alone; hold a held frame; keep its state across a LOD swap; deterministic;
// hold a carrying hand where the dress says, its basket clear of the skirt (T-3481).
// On the gait layer's walk (a stand-in `gait`): swing from its phase, opposite the leg, as far
// as the speed, elbow bent more in front, less in a skirt and clear of it, blended by its
// weight; and standing with no gait, exactly as before.
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

// T-3481: a woman carrying a market basket by the hand. The dress names the hold in the GLB's
// extras; that arm is held there walking and standing (no swing, no pose), the fingers round the
// handle, the basket clear of her skirt and off the ground, and the other arm still swings.
{
  const asset = 'nelson_christine_1904_errand';
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod0.glb`, here));
  const n = bytes.readUInt32LE(12), extras = JSON.parse(bytes.subarray(20, 20 + n)).scenes[0].extras.chicago4d_human;
  const carry = JSON.parse(extras.wardrobe_assembly_json).carry;
  assert(carry && carry.side === 'l', `${asset}: the dress names the carrying hand`);
  for (const state of ['walking', 'standing']) {
    const r = await rig(asset, 0, state === 'walking' ? 'walk' : 'idle');
    const life = createHumanLife({ id: 'carry', scene: r.scene }), acts = createHumanActions({ id: 'carry', scene: r.scene, greeting: 'nod', skirt: true, carry });
    assert(acts && acts.snapshot().carrying === 'l', `${asset}: carries in the left hand`);
    const basket = [], skirt = [];
    r.scene.traverse(o => { if (o.isSkinnedMesh && /^accessory__/.test(o.material?.name ?? '')) basket.push(o); if (o.isSkinnedMesh && /^garment_lower/.test(o.material?.name ?? '')) skirt.push(o); });
    assert(basket.length >= 1 && skirt.length === 1, `${asset}: the basket and the skirt are found`);
    const verts = (ms) => { const out = []; for (const m of ms) { const pos = m.geometry.attributes.position, v = new THREE.Vector3(); for (let i = 0; i < pos.count; i++) { m.getVertexPosition(i, v); out.push(figure(r, v.clone().applyMatrix4(m.matrixWorld))); } } return out; };
    let worstHold = 0, worstGap = Infinity, lowest = Infinity, grip = 0, rMin = 9, rMax = -9;
    for (let i = 0; i < 150; i++) {
      step(r, life, acts, 1 / 30, { state, root: r.root });
      if (i < 45 || i % 15) continue;
      const want = figure(r, world(r.bone('upperarm_l'))).add(new THREE.Vector3(...carry.wrist_from_shoulder));
      worstHold = Math.max(worstHold, figure(r, world(r.bone('hand_l'))).distanceTo(want));
      const b = verts(basket), sk = verts(skirt);
      lowest = Math.min(lowest, ...b.map(p => p.y));
      // Each basket point at the skirt's height is outside (further left than) the skirt there.
      for (const p of b) {
        let edge = -Infinity;
        for (const q of sk) if (Math.abs(q.y - p.y) < 0.03 && Math.abs(q.z - p.z) < 0.05 && q.x > 0) edge = Math.max(edge, q.x);
        if (edge > -Infinity) worstGap = Math.min(worstGap, p.x - edge);
      }
      // The fingers are round the handle: the middle finger's middle joint is at the basket's mesh.
      const knuckle = figure(r, world(r.bone('middle_02_l')));
      grip = Math.max(grip, Math.min(...b.map(p => p.distanceTo(knuckle))));
      const hz = figure(r, world(r.bone('hand_r'))).z; rMin = Math.min(rMin, hz); rMax = Math.max(rMax, hz);
    }
    assert(worstHold < 0.03, `${state}: the left wrist is held at the carry (${(worstHold * 100).toFixed(1)} cm off)`);
    assert(worstGap > 0.005, `${state}: the basket is clear of the skirt (${Number.isFinite(worstGap) ? (worstGap * 100).toFixed(1) + ' cm' : 'never level with it'})`);
    assert(lowest > 0.25, `${state}: the basket is off the ground (lowest ${lowest.toFixed(3)} m)`);
    assert(grip < 0.035, `${state}: the fingers are round the handle (${(grip * 100).toFixed(1)} cm)`);
    if (state === 'walking') assert(rMax - rMin > 0.1, `walking: the free right arm still swings (${(rMax - rMin).toFixed(3)} m)`);
    console.log(`${asset} ${state}: wrist ${(worstHold * 100).toFixed(1)} cm from the hold, basket ${(worstGap * 100).toFixed(1)} cm clear of the skirt, lowest ${lowest.toFixed(2)} m, grip ${(grip * 100).toFixed(1)} cm: PASS`);
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

// The gait layer's walk (human-gait.js passes `gait`): a stand-in gait stepped over cycles,
// phase 0 the LEFT heel strike and 0.5 the RIGHT. The left leg is forward at 0 and back at
// 0.5; the left arm must come forward as it goes back (at about 0.55, just after the right
// heel strike), swing some 20-30 deg at the shoulder, bend its elbow more at the front than
// at the back, and swing less in a skirt, clear of the skirt's bell.
const { ARM_SWING } = await import(data((await js('human-actions.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));
function standInGait({ speed = 1.25, cadence = 1.8, weight = 1 } = {}) {
  let t = 0;
  const g = { phase: 0, weight, speed, stride: 2 * speed / cadence, cadence, pelvisYaw: 0, pelvisRoll: 0, bob: 0 };
  return { g, step(dt) { t += dt; g.phase = (t * cadence / 2) % 1; } };
}
/** One arm in the figure's frame: the shoulder's flexion (+ forward) and the elbow's bend, degrees; the wrist. */
function arm(r, s) {
  const S = figure(r, world(r.bone(`upperarm_${s}`))), E = figure(r, world(r.bone(`lowerarm_${s}`))), W = figure(r, world(r.bone(`hand_${s}`)));
  const u = E.clone().sub(S), f = W.clone().sub(E);
  return { flex: Math.atan2(u.z, -u.y) * 180 / Math.PI, elbow: u.angleTo(f) * 180 / Math.PI, wrist: W };
}
async function gaitWalk(asset, { skirt = false, speed = 1.25, clip = 'walk', weight = 1 } = {}) {
  const r = await rig(asset, 1, clip);
  const life = createHumanLife({ id: 'g', scene: r.scene }), acts = createHumanActions({ id: 'g', scene: r.scene, skirt, greeting: skirt ? 'nod' : 'brow' });
  const gait = standInGait({ speed, weight });
  const opts = { state: 'walking', root: r.root, gait: gait.g };
  const rows = [];
  for (let i = 0; i < 240; i++) {
    gait.step(1 / 60); step(r, life, acts, 1 / 60, opts);
    if (i >= 120) rows.push({ phase: gait.g.phase, l: arm(r, 'l'), r: arm(r, 'r') });
  }
  return { r, life, acts, gait, opts, rows };
}
const corr = (a, b) => { const n = a.length, ma = a.reduce((x, y) => x + y) / n, mb = b.reduce((x, y) => x + y) / n; let sab = 0, sa = 0, sb = 0; a.forEach((x, k) => { sab += (x - ma) * (b[k] - mb); sa += (x - ma) ** 2; sb += (b[k] - mb) ** 2; }); return sab / Math.sqrt(sa * sb); };
const excursion = (rows, s) => { const v = rows.map(x => x[s].flex); return Math.max(...v) - Math.min(...v); };
{
  const { rows } = await gaitWalk('bardwell_otis_1835');
  const legL = rows.map(x => Math.cos(2 * Math.PI * x.phase)); // +1 with the left leg forward
  for (const s of ['l', 'r']) {
    const flex = rows.map(x => x[s].flex), sign = s === 'l' ? 1 : -1;
    const c = corr(flex, legL);
    assert(sign * c < -0.9, `gait: the ${s} arm swings opposite its own leg (r = ${c.toFixed(2)} with the left leg)`);
    const peak = rows[flex.indexOf(Math.max(...flex))].phase, want = s === 'l' ? 0.5 : 0;
    const after = ((peak - want + 1.5) % 1) - 0.5;
    assert(after > 0.01 && after < 0.1, `gait: the ${s} shoulder's flexion peaks just after the other heel strike (${after.toFixed(3)} of the cycle)`);
    const ex = excursion(rows, s), mean = (Math.max(...flex) + Math.min(...flex)) / 2;
    assert(ex > 20 && ex < 30, `gait: the ${s} shoulder swings ${ex.toFixed(1)} deg`);
    assert(Math.max(...flex) - mean > 8 && Math.max(...flex) - mean < 12.5, `gait: ±${(ex / 2).toFixed(1)} deg about ${mean.toFixed(1)}`);
    const front = rows[flex.indexOf(Math.max(...flex))][s], back = rows[flex.indexOf(Math.min(...flex))][s];
    assert(front.elbow > back.elbow + 10 && front.elbow > 26 && front.elbow < 40 && back.elbow > 10 && back.elbow < 22,
      `gait: the ${s} elbow bends more at the front (${back.elbow.toFixed(1)} → ${front.elbow.toFixed(1)} deg)`);
    // The hand goes further forward than back of where it hangs, and a little inward in front.
    const hz = rows.map(x => x[s].wrist.z), hx = rows.map(x => Math.abs(x[s].wrist.x));
    const zMid = (Math.max(...hz) + Math.min(...hz)) / 2;
    assert(front.wrist.z - zMid > 0.12 && front.wrist.z > 0.12, `gait: the ${s} hand comes forward (${front.wrist.z.toFixed(3)} m)`);
    assert(Math.abs(front.wrist.x) < Math.abs(back.wrist.x), `gait: the ${s} hand comes in in front (${Math.abs(back.wrist.x).toFixed(3)} → ${Math.abs(front.wrist.x).toFixed(3)} m)`);
    console.log(`gait: ${s} shoulder ${Math.min(...flex).toFixed(1)}..${Math.max(...flex).toFixed(1)} deg (${ex.toFixed(1)}), peak ${after.toFixed(3)} after the other heel strike, elbow ${back.elbow.toFixed(1)}→${front.elbow.toFixed(1)} deg, hand ${Math.min(...hz).toFixed(2)}..${Math.max(...hz).toFixed(2)} m: PASS`);
  }
  // Faster, further; slower, less.
  const slow = excursion((await gaitWalk('bardwell_otis_1835', { speed: 0.9 })).rows, 'l'), fast = excursion((await gaitWalk('bardwell_otis_1835', { speed: 1.6 })).rows, 'l');
  assert(slow < excursion(rows, 'l') && fast > excursion(rows, 'l') + 3, `gait: the swing grows with speed (${slow.toFixed(1)} / ${excursion(rows, 'l').toFixed(1)} / ${fast.toFixed(1)} deg)`);
  console.log(`gait: swing ${slow.toFixed(1)} / ${excursion(rows, 'l').toFixed(1)} / ${fast.toFixed(1)} deg at 0.9 / 1.25 / 1.6 m/s: PASS`);
  // Blended by the gait's weight: at half, about half the swing (on a clip whose feet are
  // still, so the feet's own reading adds nothing).
  const full = excursion((await gaitWalk('bardwell_otis_1835', { clip: 'idle' })).rows, 'l');
  const half = excursion((await gaitWalk('bardwell_otis_1835', { clip: 'idle', weight: 0.5 })).rows, 'l');
  assert(half > full * 0.35 && half < full * 0.65, `gait: blended by its weight (${half.toFixed(1)} of ${full.toFixed(1)} deg at 0.5)`);
  console.log(`gait: at weight 0.5 the swing is ${half.toFixed(1)} of ${full.toFixed(1)} deg: PASS`);
}
{
  // A woman in a full skirt swings about half as far, and her hands stay out of the bell.
  const man = excursion((await gaitWalk('bardwell_otis_1835')).rows, 'l');
  const w = await gaitWalk('williamson_mattie_1904_cook_study', { skirt: true });
  const her = excursion(w.rows, 'l');
  assert(Math.abs(her / man - ARM_SWING.skirt.scale) < 0.12, `gait: a skirt swings less (${her.toFixed(1)} vs ${man.toFixed(1)} deg)`);
  const cloth = [];
  w.r.scene.traverse(o => { if (o.isSkinnedMesh && /^garment_(lower|outer)/.test(o.material?.name ?? '')) cloth.push(o); });
  let worst = Infinity, at = '';
  for (let k = 0; k < 8; k++) {
    for (let i = 0; i < 8; i++) { w.gait.step(1 / 60); step(w.r, w.life, w.acts, 1 / 60, w.opts); }
    const axis = world(w.r.bone('pelvis')), pts = [];
    for (const m of cloth) {
      const pos = m.geometry.attributes.position, v = new THREE.Vector3();
      for (let i = 0; i < pos.count; i += 1) { m.getVertexPosition(i, v); pts.push(v.clone().applyMatrix4(m.matrixWorld)); }
    }
    for (const s of ['l', 'r']) for (const pr of ['hand', 'index_03', 'middle_03', 'ring_03', 'pinky_03', 'thumb_03']) {
      const b = w.r.bone(`${pr}_${s}`);
      if (!b) continue;
      const p = world(b);
      let best = null, bd = Infinity;
      for (const q of pts) { const d = q.distanceToSquared(p); if (d < bd) { bd = d; best = q; } }
      if (!best || Math.sqrt(bd) > 0.08) continue;
      const depth = p.clone().sub(best).dot(best.clone().sub(axis).setY(0).normalize());
      if (depth < worst) { worst = depth; at = `${pr}_${s} at phase ${w.gait.g.phase.toFixed(2)}`; }
    }
  }
  assert(worst > -0.012, `gait: ${at} is ${(-worst * 100).toFixed(1)} cm inside the skirt`);
  console.log(`gait: a skirt swings ${her.toFixed(1)} deg (${(her / man * 100).toFixed(0)} % of ${man.toFixed(1)}), hands outside the skirt (closest ${Number.isFinite(worst) ? (worst * 100).toFixed(1) + ' cm' : 'clear'}): PASS`);
}
{
  // Standing with no gait, a null gait or one at weight 0, the arms are the same to the bit.
  const out = [];
  for (const gait of [undefined, null, { phase: 0.37, weight: 0, speed: 1.3, stride: 1.4, cadence: 1.85, pelvisYaw: 0.05, pelvisRoll: 0.03, bob: 0.01 }]) {
    const r = await rig('bardwell_otis_1835', 3, 'idle');
    const life = createHumanLife({ id: 'n', scene: r.scene }), acts = createHumanActions({ id: 'n', scene: r.scene });
    const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
    for (let i = 0; i < 600; i++) {
      const viewer = i > 300 ? world(r.bone('head')).addScaledVector(fwd, 2.5) : null;
      step(r, life, acts, 1 / 30, gait === undefined ? { state: 'standing', root: r.root, viewer } : { state: 'standing', root: r.root, viewer, gait });
    }
    const q = []; r.scene.traverse(o => { if (o.isBone) q.push(...o.quaternion.toArray(), ...o.position.toArray()); });
    out.push(q);
  }
  assert.deepEqual(out[1], out[0], 'standing: a null gait changes nothing');
  assert.deepEqual(out[2], out[0], 'standing: a gait at weight 0 changes nothing');
  console.log('gait: standing with a null gait or one at weight 0 is the same to the bit: PASS');
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
