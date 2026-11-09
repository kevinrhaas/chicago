// SPDX-License-Identifier: GPL-3.0-or-later
// T-3472: people on foot walk like people (renderers/web/js/human-gait.js), on the real
// exports, on the CPU. Over the baked walk clip it must: walk each person at their own
// pace and stride (men faster and longer than women, the old slower and shorter, a skirt
// shorter); keep the stance foot planted (the heel, then the sole, then the ball do not
// slide) and every sole vertex out of the ground and on it in mid-stance; bend the knee
// on loading and fold it in swing as the measured curves do; bob, sway and turn the
// pelvis by centimetres and degrees; take a closing step and hand back to the clip; hold
// its walk across a LOD swap; plant through a turn; and be deterministic.
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
const { createHumanGait, gaitProfile, curveAt, GAIT_CURVES } = await import(data(await js('human-gait.js')));

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

// The tables are whole cycles.
for (const k of Object.keys(GAIT_CURVES)) assert.equal(GAIT_CURVES[k][0], GAIT_CURVES[k][20], `${k} closes its cycle`);
assert.ok(Math.abs(curveAt(GAIT_CURVES.knee, 0.725) - 62) < 2, 'knee peak in swing');
assert.equal(createHumanGait({ id: 'x', scene: new THREE.Group() }), null, 'a non-contract rig is left alone');

// Profiles: bounded by the adult means.
{
  const man = gaitProfile({ sex: 'male', age: 35, height: 1.75 }), woman = gaitProfile({ sex: 'female', age: 35, height: 1.62 });
  const old = gaitProfile({ sex: 'male', age: 70, height: 1.75 }), lady = gaitProfile({ sex: 'female', age: 35, height: 1.62, skirt: true });
  for (const p of [man, woman, old, lady]) {
    assert.ok(p.speed > 0.95 && p.speed < 1.5, `speed ${p.speed}`);
    assert.ok(p.cadence * 60 > 95 && p.cadence * 60 < 125, `cadence ${p.cadence * 60}`);
  }
  assert.ok(man.speed > woman.speed && man.stride > woman.stride && old.speed < man.speed && old.stride < man.stride && lady.stride < woman.stride);
  console.log(`profiles: man ${man.speed.toFixed(2)} m/s ${man.stride.toFixed(2)} m ${(man.cadence * 60).toFixed(0)}/min, woman ${woman.speed.toFixed(2)} ${woman.stride.toFixed(2)} ${(woman.cadence * 60).toFixed(0)}, in a skirt ${lady.speed.toFixed(2)} ${lady.stride.toFixed(2)} ${(lady.cadence * 60).toFixed(0)}, at 70 ${old.speed.toFixed(2)} ${old.stride.toFixed(2)}: PASS`);
}

async function load(asset, lod = 0) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  return new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
}

/** Walk `asset` for `seconds` along a path (a straight line, or an arc of `turn` deg/s), then stop. */
async function walk(asset, { profile, seconds = 6, turn = 0, lod = 0, swapAt = null, scale = 1 } = {}) {
  let gltf = await load(asset, lod);
  const root = new THREE.Group(); root.position.set(3, 0.2, -2); root.rotation.y = 0.4; root.add(gltf.scene);
  gltf.scene.scale.setScalar(scale);
  let mixer = new THREE.AnimationMixer(gltf.scene);
  mixer.clipAction(gltf.animations.find(a => a.name === 'walk')).play(); mixer.update(0); root.updateMatrixWorld(true);
  const gait = createHumanGait({ id: asset, scene: gltf.scene, profile });
  assert.ok(gait?.bound, `${asset} binds`);
  const bones = () => { const B = {}; gltf.scene.traverse(o => { if (o.isBone) B[o.name] = o; }); return B; };
  let B = bones();
  // Sole vertices: the body's skin weighted to the feet.
  let soles = [];
  const pickSoles = () => {
    soles = [];
    gltf.scene.traverse(o => {
      if (!o.isSkinnedMesh) return;
      const sk = o.skeleton, si = o.geometry.attributes.skinIndex, sw = o.geometry.attributes.skinWeight, pos = o.geometry.attributes.position;
      const ids = { l: ['foot_l', 'ball_l'], r: ['foot_r', 'ball_r'] };
      for (let i = 0; i < pos.count; i += 3) for (const s of ['l', 'r']) {
        let w = 0;
        for (let k = 0; k < 4; k++) if (ids[s].includes(sk.bones[si.getComponent(i, k)]?.name)) w += sw.getComponent(i, k);
        if (w > 0.9) soles.push({ mesh: o, i, s });
      }
    });
  };
  pickSoles();
  const v = new THREE.Vector3();
  const dt = 1 / 60;
  const log = [];
  let state = 'standing', walked = 0;
  for (let f = 0; f < 60 * (seconds + 3); f++) {
    const t = f * dt;
    state = t > 0.4 && t < 0.4 + seconds ? 'walking' : 'standing';
    let moved = 0;
    if (state === 'walking') {
      moved = gait.speed * gait.pace * dt;
      root.rotation.y += turn * Math.PI / 180 * dt;
      root.position.add(new THREE.Vector3(Math.sin(root.rotation.y), 0, Math.cos(root.rotation.y)).multiplyScalar(moved));
      walked += moved;
    }
    if (swapAt !== null && Math.abs(t - swapAt) < dt / 2) {
      // A LOD swap: a new body, the same walk.
      root.remove(gltf.scene);
      gltf = await load(asset, 1); gltf.scene.scale.setScalar(scale); root.add(gltf.scene);
      mixer = new THREE.AnimationMixer(gltf.scene);
      mixer.clipAction(gltf.animations.find(a => a.name === 'walk')).play(); mixer.update(0);
      root.updateMatrixWorld(true);
      assert.ok(gait.bind(gltf.scene), 'rebinds on a LOD swap');
      B = bones(); pickSoles();
    }
    root.updateMatrixWorld(true);
    mixer.update(dt);
    gait.apply(dt, { state, root, moved });
    gltf.scene.updateMatrixWorld(true);
    const W = n => B[n].getWorldPosition(new THREE.Vector3());
    const knee = s => 180 - W('thigh_' + s).sub(W('calf_' + s)).angleTo(W('foot_' + s).sub(W('calf_' + s))) * 180 / Math.PI;
    let low = { l: Infinity, r: Infinity };
    if (f % 2 === 0) for (const p of soles) { p.mesh.getVertexPosition(p.i, v); p.mesh.localToWorld(v); low[p.s] = Math.min(low[p.s], v.y - root.position.y); }
    log.push({ t, state, snap: gait.snapshot(), phase: gait.phase, weight: gait.weight, mode: gait.mode,
      foot: { l: W('foot_l'), r: W('foot_r') }, ball: { l: W('ball_l'), r: W('ball_r') }, pelvis: W('pelvis').y - root.position.y,
      knee: { l: knee('l'), r: knee('r') }, low, root: root.position.clone(), rootYaw: root.rotation.y });
  }
  return { gait, log, walked };
}

const OFF = { l: 0, r: 0.5 };
function judge(name, run, { lodSwap = false, swingMax = 72, size = 1 } = {}) {
  const { gait, log } = run;
  const P = gait.profile;
  const steady = log.filter(r => r.mode === 'walk' && r.t > 1.6 && r.t < log.at(-1).t - 3.2 && r.weight === 1);
  assert.ok(steady.length > 120, `${name}: enough steady walking`);
  // Contact points: the ankle while the foot is flat, the ball while the heel rises.
  let flatSlide = 0, ballSlide = 0, sink = 0, float = 0;
  const plants = { l: [], r: [] };
  for (const s of ['l', 'r']) {
    let flat0 = null, ball0 = null;
    for (const r of steady) {
      const c = ((r.phase - OFF[s]) % 1 + 1) % 1;
      if (c > 0.12 && c < 0.31) { flat0 ??= r.foot[s]; flatSlide = Math.max(flatSlide, Math.hypot(r.foot[s].x - flat0.x, r.foot[s].z - flat0.z)); }
      else if (flat0) { plants[s].push(flat0); flat0 = null; }
      if (c > 0.36 && c < 0.58) { ball0 ??= r.ball[s]; ballSlide = Math.max(ballSlide, Math.hypot(r.ball[s].x - ball0.x, r.ball[s].z - ball0.z)); }
      else ball0 = null;
      if (Number.isFinite(r.low[s])) {
        sink = Math.min(sink, r.low[s]);
        if (c > 0.14 && c < 0.3) float = Math.max(float, r.low[s]);
      }
    }
  }
  assert.ok(flatSlide < 0.004, `${name}: the flat foot slides ${(flatSlide * 1000).toFixed(1)} mm`);
  assert.ok(ballSlide < 0.012, `${name}: the ball slides ${(ballSlide * 1000).toFixed(1)} mm as the heel rises`);
  assert.ok(sink > -0.012, `${name}: a sole vertex sinks ${(sink * 1000).toFixed(1)} mm`);
  assert.ok(float < 0.02, `${name}: the flat foot floats ${(float * 1000).toFixed(1)} mm`);
  // Steps: successive plants of opposite feet.
  const all = [...plants.l, ...plants.r];
  const steps = [];
  for (const s of ['l', 'r']) for (let i = 1; i < plants[s].length; i++) steps.push(plants[s][i].distanceTo(plants[s][i - 1]));
  const stride = steps.reduce((a, b) => a + b, 0) / Math.max(1, steps.length);
  assert.ok(all.length >= 4 && Math.abs(stride - P.stride) / P.stride < 0.06, `${name}: stride ${stride.toFixed(3)} vs ${P.stride.toFixed(3)}`);
  // Knees: loading flexion and the swing's fold; the pelvis's bob.
  const kneeAt = (lo, hi) => Math.max(...steady.filter(r => { const c = ((r.phase) % 1 + 1) % 1; return c > lo && c < hi; }).map(r => r.knee.l));
  const loading = kneeAt(0.05, 0.25), swing = kneeAt(0.62, 0.85);
  assert.ok(loading > 8 && loading < 32, `${name}: loading knee ${loading.toFixed(1)}`);
  assert.ok(swing > 50 && swing < swingMax, `${name}: swing knee ${swing.toFixed(1)}`);
  const pel = steady.map(r => r.pelvis), bob = Math.max(...pel) - Math.min(...pel);
  assert.ok(bob > 0.02 * size && bob < 0.06 * size, `${name}: pelvis bob ${(bob * 100).toFixed(1)} cm`);
  // Stopping: a closing step, both feet back under the hips, the clip's pose again.
  const end = log.at(-1);
  assert.equal(end.mode, 'idle', `${name}: back to the clip after the closing step`);
  const lastWalk = log.findLastIndex(r => r.state === 'walking'), idleAt = log.findIndex((r, i) => i > lastWalk && r.mode === 'idle');
  assert.ok(idleAt > 0 && (idleAt - lastWalk) / 60 < 2.2, `${name}: the closing step takes ${((idleAt - lastWalk) / 60).toFixed(2)} s`);
  console.log(`${name}: ${P.speed.toFixed(2)} m/s, stride ${stride.toFixed(2)} m (${(P.cadence * 60).toFixed(0)} steps/min), foot slide ${(flatSlide * 1000).toFixed(1)} mm flat / ${(ballSlide * 1000).toFixed(1)} on the ball, soles ${(sink * 1000).toFixed(1)}..${(float * 1000).toFixed(1)} mm, knee ${loading.toFixed(0)} deg loading / ${swing.toFixed(0)} in swing, bob ${(bob * 100).toFixed(1)} cm, stop ${((idleAt - lastWalk) / 60).toFixed(2)} s${lodSwap ? ', through a LOD swap' : ''}: PASS`);
}

judge('Frances Glessner (skirt, 56)', await walk('glessner_frances_m_1904', { profile: { sex: 'female', age: 56, skirt: true } }));
judge('John J. Glessner (61)', await walk('glessner_john_j_1904', { profile: { sex: 'male', age: 61 } }));
judge('Otis Bardwell', await walk('bardwell_otis_1835', { profile: { sex: 'male', age: 30 } }));
judge('Mary Reynolds (maid)', await walk('reynolds_mary_1904_maid', { profile: { sex: 'female', age: 25, skirt: true } }));
judge('Otis, 1.08 tall, across a LOD swap', await walk('bardwell_otis_1835', { profile: { sex: 'male', age: 30 }, swapAt: 3.0, scale: 1.08 }), { lodSwap: true });
// T-3520: the children walk as children. The toddler's body is under 0.8 m; read as an adult
// it was given a man's stride and walked on its knees. Its stride is a child's for its height,
// its knees bend as anyone's do, its pelvis stays at the height of its own legs.
{
  const toddler = gaitProfile({ sex: 'female', age: 3, height: 0.9 }), girl = gaitProfile({ sex: 'female', age: 8, height: 1.2 });
  assert.ok(toddler.speed > 0.6 && toddler.speed < 1.0 && toddler.stride > 0.45 && toddler.stride < 0.7 && toddler.cadence * 60 > 150, `toddler ${JSON.stringify(toddler)}`);
  assert.ok(girl.speed > 0.95 && girl.speed < 1.3 && girl.stride > 0.8 && girl.stride < 1.05, `girl ${JSON.stringify(girl)}`);
  for (const [asset, age] of [['child_toddler_1812', 3], ['child_girl_1812', 8], ['child_boy_1812', 8]]) {
    const run = await walk(asset, { profile: { sex: asset.includes('girl') ? 'female' : 'male', age } });
    // A small child's foot is long for its leg: it clears the ground by lifting its toes, and
    // the knee folds no further than anyone's (it folded to 85 degrees and read as kneeling).
    judge(`${asset} (${age})`, run, { swingMax: 72, size: run.log[0].pelvis / 0.95 });  // the bob in proportion to the legs
    const legs = run.log[0].pelvis, low = Math.min(...run.log.filter(r => r.mode === 'walk' && r.weight === 1).map(r => r.pelvis));
    assert.ok(low > 0.85 * legs, `${asset}: the pelvis drops to ${(low / legs * 100).toFixed(0)} % of its standing height (walking on its knees)`);
    const allKnee = Math.max(...run.log.filter(r => r.state === 'walking' || r.mode === 'close').map(r => Math.max(r.knee.l, r.knee.r)));
    assert.ok(allKnee < 72, `${asset}: a knee folds to ${allKnee.toFixed(0)} deg in a step (kneeling)`);
    assert.ok(run.gait.stride < 1.0 * (legs / 0.45), `${asset}: stride ${run.gait.stride.toFixed(2)} on hips ${legs.toFixed(2)} m high`);
  }
}

// A turn: the planted foot stays put while the body turns over it.
{
  const { log } = await walk('glessner_john_j_1904', { profile: { sex: 'male', age: 61 }, turn: 30 });
  let slide = 0;
  for (const s of ['l', 'r']) {
    let f0 = null;
    for (const r of log.filter(r => r.mode === 'walk' && r.t > 1.6 && r.weight === 1)) {
      const c = ((r.phase - OFF[s]) % 1 + 1) % 1;
      if (c > 0.12 && c < 0.31) { f0 ??= r.foot[s]; slide = Math.max(slide, Math.hypot(r.foot[s].x - f0.x, r.foot[s].z - f0.z)); } else f0 = null;
    }
  }
  assert.ok(slide < 0.006, `turning: flat foot slides ${(slide * 1000).toFixed(1)} mm`);
  console.log(`turning 30 deg/s: the flat foot slides ${(slide * 1000).toFixed(1)} mm: PASS`);
}

// T-3520: a nudge. People kept apart and out of the lodge walls are moved aside by the
// spacing layer, not by the walk; a planted foot left behind pulled a toddler's hips down to
// 13 % of their height, knees folded flat (the owner's "kneeling" child). The feet go with it.
for (const [asset, age, sex] of [['child_toddler_1812', 3, 'female'], ['bardwell_otis_1835', 30, 'male']]) {
  for (const kind of ['walking', 'stopping']) {
    const gltf = await load(asset, 2);
    const root = new THREE.Group(); root.add(gltf.scene);
    const mixer = new THREE.AnimationMixer(gltf.scene);
    mixer.clipAction(gltf.animations.find(a => a.name === 'walk')).play(); mixer.update(0); root.updateMatrixWorld(true);
    const gait = createHumanGait({ id: asset, scene: gltf.scene, profile: { sex, age } });
    const B = {}; gltf.scene.traverse(o => { if (o.isBone) B[o.name] = o; });
    const W = n => B[n].getWorldPosition(new THREE.Vector3());
    const knee = s => 180 - W('thigh_' + s).sub(W('calf_' + s)).angleTo(W('foot_' + s).sub(W('calf_' + s))) * 180 / Math.PI;
    let legs = null, low = Infinity, most = 0;
    const dt = 1 / 60, until = kind === 'walking' ? 4.5 : 1.5, at = kind === 'walking' ? 2 : 1.55;
    for (let f = 0; f < 60 * 6; f++) {
      const t = f * dt, state = t > 0.3 && t < until ? 'walking' : 'standing';
      let moved = 0;
      if (state === 'walking') { moved = gait.speed * gait.pace * dt; root.position.z += moved; }
      if (t > at && t < at + 0.3) root.position.x += 0.6 * dt / 0.3;   // shoved 0.6 m aside in 0.3 s
      root.updateMatrixWorld(true); mixer.update(dt); gait.apply(dt, { state, root, moved }); gltf.scene.updateMatrixWorld(true);
      const p = W('pelvis').y - root.position.y; legs ??= p;
      if (t > 0.5) { low = Math.min(low, p / legs); most = Math.max(most, knee('l'), knee('r')); }
    }
    assert.ok(low > 0.85, `${asset} nudged ${kind}: the pelvis drops to ${(low * 100).toFixed(0)} % (kneeling)`);
    assert.ok(most < 72, `${asset} nudged ${kind}: a knee folds to ${most.toFixed(0)} deg`);
    console.log(`${asset} nudged 0.6 m aside ${kind}: pelvis at least ${(low * 100).toFixed(0)} %, knee at most ${most.toFixed(0)} deg: PASS`);
  }
}

// Deterministic.
{
  const a = await walk('glessner_john_j_1904', { profile: { sex: 'male', age: 61 }, seconds: 2 });
  const b = await walk('glessner_john_j_1904', { profile: { sex: 'male', age: 61 }, seconds: 2 });
  assert.deepEqual(a.log.map(r => r.foot.l.toArray()), b.log.map(r => r.foot.l.toArray()), 'deterministic');
  console.log('deterministic: PASS');
}
console.log('human gait: PASS');
