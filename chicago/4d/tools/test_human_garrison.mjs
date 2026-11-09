// SPDX-License-Identifier: GPL-3.0-or-later
// T-3523: the 1812 garrison dressed by rank and armed (renderers/web/js/human-garrison.js), on
// the real private's and officer's exports, on the CPU, with the life and arm layers over the
// idle and walk clips. It must: draw a sergeant's two epaulettes and a corporal's one on the
// right, on top of the shoulders and outside the coat; draw an officer's sash round his waist
// and a lieutenant's epaulette on the left; hang a drummer's drum at his left thigh; put a
// musket in a held hand for the two carries, at the order with its butt by the right foot on
// the ground and the bayonet above the head, at the shoulder with the butt in the left hand and
// the muzzle up past the shoulder, clear of the head, and steady while he walks; and pile arms
// standing on the ground. And the dress file must say what place.py dressed each man in.
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
const G = await import(data(await js('human-garrison.js')));

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

const HEADING = 0.7;
async function dressed(asset, lod, garrison) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  const root = new THREE.Group(); root.position.set(4, 0.3, -7); root.rotation.y = HEADING; root.add(gltf.scene);
  root.updateMatrixWorld(true);
  const made = G.dressGarrison(gltf.scene, garrison, { lod });   // in the bind pose, as humans.js does
  const mixer = new THREE.AnimationMixer(gltf.scene);
  const clips = new Map(gltf.animations.map((a) => [a.name, a]));
  const idle = mixer.clipAction(clips.get('idle')); idle.play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bone = name => { let b = null; gltf.scene.traverse(o => { if (o.isBone && o.name === name) b = o; }); return b; };
  const life = createHumanLife({ id: `g:${asset}`, scene: gltf.scene });
  const acts = createHumanActions({ id: `g:${asset}`, scene: gltf.scene, carry: G.garrisonCarry(garrison) });
  const named = (n) => { let o = null; gltf.scene.traverse((x) => { if (!o && x.name === n) o = x; }); return o; };
  for (const g of made?.meshes ?? []) facesOut(g);
  return { root, scene: gltf.scene, mixer, clips, idle, bone, life, acts, made, named };
}
/**
 * Every one-sided piece is wound to face out as placed (its triangles' winding agrees with its
 * normals, through any mirror in its world matrix): a solid wound inside out shows its far
 * inner faces, and the drum or a stock looks hollow.
 */
function facesOut(obj) {
  obj.updateMatrixWorld(true);
  obj.traverse((o) => {
    if (!o.isMesh || o.material.side === THREE.DoubleSide) return;
    const pos = o.geometry.attributes.position, nor = o.geometry.attributes.normal, idx = o.geometry.index.array;
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
    let agree = 0, total = 0;
    for (let i = 0; i < idx.length; i += 3) {
      a.fromBufferAttribute(pos, idx[i]); b.fromBufferAttribute(pos, idx[i + 1]); c.fromBufferAttribute(pos, idx[i + 2]);
      const f = b.sub(a).cross(c.sub(a));
      if (f.lengthSq() < 1e-14) continue;
      n.fromBufferAttribute(nor, idx[i]).add(c.fromBufferAttribute(nor, idx[i + 1])).add(c.fromBufferAttribute(nor, idx[i + 2]));
      total += 1; if (f.dot(n) > 0) agree += 1;
    }
    const mirrored = o.matrixWorld.determinant() < 0;
    const share = mirrored ? 1 - agree / total : agree / total;
    assert(share > 0.97, `${o.name}: faces out (${(share * 100).toFixed(1)}% of ${total} triangles)`);
  });
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
const figure = (r, p) => p.clone().sub(r.root.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), -r.root.rotation.y);
const step = (r, dt, opts) => { r.mixer.update(dt); r.life.apply(dt, opts); r.acts.apply(dt, opts); r.root.updateMatrixWorld(true); };
/** A group's points, figure frame. */
function pointsOf(r, obj) {
  const out = [];
  obj.updateMatrixWorld(true);
  obj.traverse((o) => {
    if (!o.isMesh) return;
    const p = o.geometry.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) out.push(figure(r, v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld).clone()));
  });
  return out;
}
const span = (pts, k) => [Math.min(...pts.map((p) => p[k])), Math.max(...pts.map((p) => p[k]))];

// --- the sergeant at the order -------------------------------------------------------------
{
  const r = await dressed('private_first_infantry_1812', 0, { rank: 'sergeant', marks: ['epaulette_worsted_l', 'epaulette_worsted_r'], arms: 'order' });
  assert(r.acts, 'the arm layer binds');
  for (let i = 0; i < 90; i++) step(r, 1 / 30, { state: 'standing', root: r.root });
  const snap = r.acts.snapshot();
  assert.equal(snap.carrying, 'r', 'the right hand is held');
  for (const s of ['l', 'r']) {
    const ep = r.named(`garrison_epaulette_worsted_${s}`);
    assert(ep, `epaulette ${s} drawn`);
    const pts = pointsOf(r, ep), joint = figure(r, world(r.bone(`upperarm_${s}`)));
    const [y0, y1] = span(pts, 'y');
    assert(y1 > joint.y + 0.04 && y1 < joint.y + 0.12, `epaulette ${s} sits on the shoulder (top ${y1.toFixed(3)}, joint ${joint.y.toFixed(3)})`);
    assert(Math.max(...pts.map((p) => (s === 'l' ? p.x : -p.x))) > 0.12, `epaulette ${s} out over the shoulder`);
    console.log(`  epaulette ${s}: y ${y0.toFixed(3)}..${y1.toFixed(3)} joint ${joint.y.toFixed(3)}`);
  }
  const m = r.named('garrison_musket');
  assert(m, 'musket drawn');
  const pts = pointsOf(r, m), [y0, y1] = span(pts, 'y');
  const head = figure(r, world(r.bone('head')));
  console.log(`  order: musket y ${y0.toFixed(3)}..${y1.toFixed(3)}, head ${head.y.toFixed(3)}; foot of it at x ${pts.find((p) => p.y === y0).x.toFixed(3)} z ${pts.find((p) => p.y === y0).z.toFixed(3)}`);
  assert(y0 > -0.06 && y0 < 0.08, `at the order the butt is on the ground (${y0.toFixed(3)})`);
  assert(y1 > head.y + 0.05 && y1 < head.y + 0.45, `the bayonet stands above the head (${y1.toFixed(3)})`);
  const foot = pts.find((p) => p.y === y0);
  assert(foot.x < -0.1 && foot.x > -0.4, `by the right foot (x ${foot.x.toFixed(3)})`);
}

// --- a sentry at the shoulder, standing and walking ----------------------------------------
{
  const r = await dressed('private_first_infantry_1812', 0, { rank: 'private', arms: 'shoulder' });
  for (let i = 0; i < 90; i++) step(r, 1 / 30, { state: 'standing', root: r.root });
  assert.equal(r.acts.snapshot().carrying, 'l', 'the left hand is held');
  const m = r.named('garrison_musket');
  let pts = pointsOf(r, m);
  const head = figure(r, world(r.bone('head'))), sh = figure(r, world(r.bone('upperarm_l'))), hand = figure(r, world(r.bone('hand_l')));
  const [y0, y1] = span(pts, 'y');
  console.log(`  shoulder: musket y ${y0.toFixed(3)}..${y1.toFixed(3)}, hand ${hand.y.toFixed(3)}, shoulder ${sh.y.toFixed(3)}`);
  assert(Math.abs(y0 - (hand.y - 0.03)) < 0.15, `the butt is in the hand (${y0.toFixed(3)} vs hand ${hand.y.toFixed(3)})`);
  assert(y1 > head.y + 0.3, 'the muzzle and bayonet rise above the head');
  const near = Math.min(...pts.map((p) => p.distanceTo(head)));
  assert(near > 0.09, `clear of the head (${near.toFixed(3)} m)`);
  // Walking: the musket stays with the shoulder, not swinging.
  r.idle.stop(); r.mixer.clipAction(r.clips.get('walk')).play();
  const tops = [];
  for (let i = 0; i < 60; i++) { step(r, 1 / 30, { state: 'walking', root: r.root }); tops.push(span(pointsOf(r, m), 'z')[1]); }
  const swing = Math.max(...tops) - Math.min(...tops);
  console.log(`  shoulder, walking: musket front moves ${swing.toFixed(3)} m`);
  assert(swing < 0.12, `a shouldered musket does not swing (${swing.toFixed(3)} m)`);
}

// --- a drummer, an officer -----------------------------------------------------------------
{
  const r = await dressed('private_first_infantry_1812', 2, { rank: 'drummer', carry: 'drum' });
  for (let i = 0; i < 30; i++) step(r, 1 / 30, { state: 'standing', root: r.root });
  const d = r.named('garrison_drum');
  assert(d, 'drum drawn');
  const c = figure(r, world(d));
  console.log(`  drum centre ${c.x.toFixed(3)} ${c.y.toFixed(3)} ${c.z.toFixed(3)}`);
  assert(c.x > 0.05 && c.y > 0.45 && c.y < 0.85 && c.z > 0.05, 'the drum at the left thigh, in front');
  assert(!r.named('garrison_musket') && !r.acts.snapshot().carrying, 'a drummer carries no musket');
}
{
  const r = await dressed('officer_first_infantry_1812', 1, { rank: 'second lieutenant', marks: ['epaulette_bullion_l', 'sash_crimson'] });
  for (let i = 0; i < 30; i++) step(r, 1 / 30, { state: 'standing', root: r.root });
  const sash = r.named('garrison_sash'), ep = r.named('garrison_epaulette_bullion_l');
  assert(sash && ep, 'sash and left epaulette drawn');
  const pts = pointsOf(r, sash), pelvis = figure(r, world(r.bone('pelvis')));
  const ring = pts.filter((p) => p.y > pelvis.y);
  const [x0, x1] = span(ring, 'x'), [z0, z1] = span(ring, 'z');
  console.log(`  sash: x ${x0.toFixed(3)}..${x1.toFixed(3)} z ${z0.toFixed(3)}..${z1.toFixed(3)} y ${span(pts, 'y').map((v) => v.toFixed(3))}, pelvis ${pelvis.y.toFixed(3)}`);
  assert(x1 - x0 > 0.26 && x1 - x0 < 0.5 && z1 - z0 > 0.18, 'the sash goes round the waist');
  assert(figure(r, world(r.bone('upperarm_l'))).x > 0, 'left is +x');
}

// --- piled arms ----------------------------------------------------------------------------
{
  const g = G.armsPileGroup(3); g.updateMatrixWorld(true);
  facesOut(g);
  const box = new THREE.Box3().setFromObject(g);
  assert(box.min.y > -0.02 && box.min.y < 0.05 && box.max.y > 1.6 && box.max.y < 2.0, `a pile stands on the ground (${box.min.y.toFixed(3)}..${box.max.y.toFixed(3)})`);
}

// --- the dress file (place.py --check, gated on its own, keeps it current) says what each man wears ---
const file = JSON.parse(await fs.readFile(new URL('data/humans/variation/dress_1812_garrison.json', here), 'utf8'));
const persons = Object.entries(file.persons);
const by = (f) => persons.filter(([, p]) => f(p.garrison)).map(([id]) => id);
const sergeants = by((g) => g.rank === 'sergeant'), corporals = by((g) => g.rank === 'corporal');
assert(sergeants.length === 4 && sergeants.every((id) => file.persons[id].garrison.marks.length === 2), 'four sergeants, two epaulettes each');
assert(corporals.length === 2 && corporals.every((id) => file.persons[id].garrison.marks.join() === 'epaulette_worsted_r'), 'two corporals, one on the right');
assert(by((g) => g.carry === 'drum').length === 2 && by((g) => g.carry === 'fife').length === 2, 'two drummers, two fifers');
assert(by((g) => g.arms).length >= 7, 'the guard and the men under arms are armed');
assert(by((g) => g.pile).length === 1, 'one pile of arms');
assert(persons.every(([, p]) => p.garrison.grade === 'reconstructed' && p.garrison.liberty === 'L-1812-garrison-dress-3523' && p.worn), 'every record graded, with its liberty and words');
console.log(`human garrison: ${sergeants.length} sergeants, ${corporals.length} corporals, ${by((g) => g.arms).length} armed, ${persons.filter(([, p]) => p.asset === 'settler_1812').length} in fatigue dress: PASS`);
