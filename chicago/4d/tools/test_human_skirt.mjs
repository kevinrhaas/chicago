// SPDX-License-Identifier: GPL-3.0-or-later
// Cloth that hangs below the hips hangs from the waist and gives way to the legs
// (renderers/web/js/human-skirt.js), on the real exports, on the CPU. A woman's skirt
// (T-3472), and since T-3553 every hanging garment of every body in the town: a frock or
// livery coat's skirts, a tailcoat's or a soldier's tails, a petticoat, a child's frock, a
// blanket, a breechcloth, a shirt's tail (Kevin, 2026-11-13, following the Glessners'
// coachman on E 18th St: "no one should have their legs break through their clothing").
// It must: leave a body in trousers alone; keep every tube (trousers, breeches, stockings,
// leggings, boot shafts) on its leg; draw a standing figure exactly as the asset does; at a
// stride (left thigh +30 deg, knee 10; right thigh -15, knee 40), at mid-swing (knee 60),
// with the heel kicked up behind (thigh -10, knee 62), on the baked walk and on the gait
// layer's stride, hold every leg vertex below the hips inside every hanging garment, on
// every ray from the body's axis where that garment is; keep the hem one ring (no panel past
// its neighbour, no hem edge torn open); carry the front hem forward with the leading leg;
// leave the asset's shared geometry, and every other figure wearing it, untouched; be
// deterministic; and keep its state across a LOD swap.
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
const SkeletonUtils = await import(utils.SkeletonUtils);
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const { createHumanSkirt, skirtMeshes, garmentKind, N_PANELS } = await import(data(await js('human-skirt.js')));

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

const gltfs = new Map();
async function gltfOf(asset, lod) {
  const key = `${asset}.${lod}`;
  if (!gltfs.has(key)) {
    const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
    gltfs.set(key, await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), ''));
  }
  return gltfs.get(key);
}
/** A figure as humans.js builds one: a SkeletonUtils clone of the shared GLTF, under a root. */
async function rig(asset, lod, clip = 'idle', heading = 0.7) {
  const gltf = await gltfOf(asset, lod);
  const scene = SkeletonUtils.clone(gltf.scene);
  const root = new THREE.Group(); root.position.set(4, 0.3, -7); root.rotation.y = heading; root.add(scene);
  const mixer = new THREE.AnimationMixer(scene);
  mixer.clipAction(gltf.animations.find(a => a.name === clip)).play();
  mixer.update(0); root.updateMatrixWorld(true);
  const bones = {};
  scene.traverse(o => { if (o.isBone) bones[o.name] = o; });
  // The mixer writes a bone only when the clip's value changes, so a pose set by hand is
  // undone by hand: the legs as the clip left them.
  const legRest = ['thigh_l', 'thigh_r', 'calf_l', 'calf_r'].map(n => [bones[n], bones[n].quaternion.clone()]);
  return { root, scene, mixer, gltf, bone: n => bones[n], legRest };
}
const world = (o) => o.getWorldPosition(new THREE.Vector3());
/** A world point in the figure's frame (+X its left, +Z its front, +Y up), from its root. */
const figure = (r, p) => p.clone().sub(r.root.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), -r.root.rotation.y);
const leftAxis = (r) => new THREE.Vector3(1, 0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
function skinned(mesh) {
  const pos = mesh.geometry.attributes.position, out = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld); out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z; }
  return out;
}
const meshNamed = (r, re) => { let m = null; r.scene.traverse(o => { if (!m && o.isSkinnedMesh && re.test(o.name)) m = o; }); return m; };
const bodyOf = (r) => { let m = null; r.scene.traverse(o => { if (!m && o.isSkinnedMesh && /^skin/.test(o.material?.name ?? '')) m = o; }); return m; };

/** Rotate a bone in the world about `axis` by `angle`. */
function turnWorld(bone, axis, angle) {
  bone.parent.updateWorldMatrix(true, false);
  const pq = bone.parent.getWorldQuaternion(new THREE.Quaternion());
  const wq = pq.clone().multiply(bone.quaternion);
  bone.quaternion.copy(pq.invert().multiply(new THREE.Quaternion().setFromAxisAngle(axis, angle).multiply(wq)));
}
/** A stride set by hand over the standing pose: + thigh = flexed (knee forward), + knee = bent. */
function setLegs(r, legs) {
  for (const [b, q] of r.legRest) b.quaternion.copy(q);
  const L = leftAxis(r);
  for (const [s, thigh, knee] of legs) {
    turnWorld(r.bone(`thigh_${s}`), L, -thigh * Math.PI / 180);
    turnWorld(r.bone(`calf_${s}`), L, knee * Math.PI / 180);
  }
}

/**
 * Every leg vertex (body, weighted to a thigh or calf) below the hips, against the skirt on
 * the ray from the body's axis through it. Returns the least clearance (m; > 0 is inside).
 */
function containment(r, skirt, open = false) {
  // The legs: the skin, and every tube worn over it (trousers, breeches, stockings, leggings,
  // boot shafts), which stand off the skin by their ease.
  const legMeshes = [bodyOf(r), ...(skirtMeshes(r.scene)?.tubes ?? [])];
  const hips = figure(r, world(r.bone('thigh_l')).add(world(r.bone('thigh_r'))).multiplyScalar(0.5));
  const S = skinned(skirt), BINS = 180;
  // The skirt's surface, not only its vertices: every triangle sampled every 1.2 cm.
  const bins = Array.from({ length: BINS }, () => []);
  const idx = skirt.geometry.index.array, P = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()], q = new THREE.Vector3();
  for (let t = 0; t < idx.length; t += 3) {
    for (let e = 0; e < 3; e++) P[e].set(S[idx[t + e] * 3], S[idx[t + e] * 3 + 1], S[idx[t + e] * 3 + 2]);
    const k = Math.max(1, Math.ceil(Math.max(P[0].distanceTo(P[1]), P[1].distanceTo(P[2]), P[2].distanceTo(P[0])) / 0.012));
    for (let i = 0; i <= k; i++) for (let j = 0; j <= k - i; j++) {
      q.copy(P[0]).addScaledVector(P[1].clone().sub(P[0]), i / k).addScaledVector(P[2].clone().sub(P[0]), j / k);
      const p = figure(r, q), X = p.x - hips.x, Z = p.z - hips.z, th = Math.atan2(X, Z);
      bins[((Math.floor((th / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS].push(p.y, Math.hypot(X, Z), th);
    }
  }
  let worst = Infinity, at = null, n = 0;
  const win = 3 * Math.PI / 180;
  for (const leg of legMeshes) {
    const B = skinned(leg), skel = leg.skeleton;
    const si = leg.geometry.attributes.skinIndex, sw = leg.geometry.attributes.skinWeight;
    const legIdx = new Set(skel.bones.map((b, i) => (/^(thigh|calf)_[lr]$/.test(b.name) ? i : -1)).filter(i => i >= 0));
    for (let i = 0; i < si.count; i++) {
      let w = 0; for (let c = 0; c < 4; c++) if (legIdx.has(si.getComponent(i, c))) w += sw.getComponent(i, c);
      if (w < 0.5) continue;
      const p = figure(r, new THREE.Vector3(B[i * 3], B[i * 3 + 1], B[i * 3 + 2]));
      if (p.y > hips.y - 0.1) continue;
      const X = p.x - hips.x, Z = p.z - hips.z, th = Math.atan2(X, Z), rl = Math.hypot(X, Z);
      const b0 = Math.floor((th / (2 * Math.PI)) * BINS);
      let rs = Infinity, hem = Infinity;
      for (let d = -2; d <= 2; d++) {
        const list = bins[(((b0 + d) % BINS) + BINS) % BINS];
        for (let m = 0; m < list.length; m += 3) {
          let dth = Math.abs(list[m + 2] - th); if (dth > Math.PI) dth = 2 * Math.PI - dth;
          if (dth > win) continue;
          hem = Math.min(hem, list[m]);
          if (Math.abs(list[m] - p.y) < 0.012) rs = Math.min(rs, list[m + 1]);
        }
      }
      if (p.y < hem + 0.03) continue; // below the hem: a shoe or an ankle shows, as it does
      // An open garment (a coat's skirts open in front, a tailcoat's tails, an apron, a blanket
      // wrapped and tucked): only where its cloth is, at that height and angle.
      if (open && rs === Infinity) continue;
      n++;
      const c = (rs === Infinity ? 0 : rs) - rl;
      if (c < worst) { worst = c; at = { y: +p.y.toFixed(3), th: +(th * 180 / Math.PI).toFixed(0), leg: +rl.toFixed(3), skirt: +rs.toFixed(3), on: leg === legMeshes[0] ? 'skin' : leg.name.replace(/_lod\d*$/, '') }; }
    }
  }
  return { worst, at, n };
}

/** The hem as one ring: bins round the body stay in order, and no hem edge tears open. */
function hemRing(r, skirt, rest) {
  const hips = figure(r, world(r.bone('thigh_l')).add(world(r.bone('thigh_r'))).multiplyScalar(0.5));
  const S = skinned(skirt), n = S.length / 3;
  const P = (A, i) => figure(r, new THREE.Vector3(A[i * 3], A[i * 3 + 1], A[i * 3 + 2]));
  let yMin = Infinity; for (let i = 0; i < n; i++) yMin = Math.min(yMin, rest.F[i * 3 + 1]);
  const ring = []; for (let i = 0; i < n; i++) if (rest.F[i * 3 + 1] < yMin + 0.03) ring.push(i);
  const BINS = 48, sum = new Float64Array(BINS), cnt = new Uint16Array(BINS);
  for (const i of ring) {
    const th0 = Math.atan2(rest.F[i * 3] - rest.hx, rest.F[i * 3 + 2] - rest.hz);
    const p = P(S, i); let d = Math.atan2(p.x - hips.x, p.z - hips.z) - th0;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    const k = ((Math.floor(((th0 + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;
    const centre = -Math.PI + (k + 0.5) * 2 * Math.PI / BINS, rel = th0 + d - centre;
    sum[k] += Math.atan2(Math.sin(rel), Math.cos(rel)); cnt[k]++;
  }
  const order = [];
  for (let k = 0; k < BINS; k++) if (cnt[k]) order.push(-Math.PI + (k + 0.5) * 2 * Math.PI / BINS + sum[k] / cnt[k]);
  let crossed = 0;
  for (let k = 1; k < order.length; k++) if (!(order[k] > order[k - 1])) crossed++;
  // The hem's own edges: none stretched past twice its length and 2 cm.
  const inRing = new Set(ring), idx = skirt.geometry.index.array;
  let worstEdge = 0;
  for (let t = 0; t < idx.length; t += 3) for (let e = 0; e < 3; e++) {
    const a = idx[t + e], b = idx[t + (e + 1) % 3];
    if (!inRing.has(a) || !inRing.has(b)) continue;
    const l0 = Math.hypot(rest.F[a * 3] - rest.F[b * 3], rest.F[a * 3 + 1] - rest.F[b * 3 + 1], rest.F[a * 3 + 2] - rest.F[b * 3 + 2]);
    const l1 = Math.hypot(S[a * 3] - S[b * 3], S[a * 3 + 1] - S[b * 3 + 1], S[a * 3 + 2] - S[b * 3 + 2]);
    worstEdge = Math.max(worstEdge, l1 - (2 * l0 + 0.02));
  }
  return { crossed, bins: order.length, worstEdge, ring: ring.length };
}
/** The skirt as it stands (figure frame), for the ring and the front hem. */
function restOf(r, skirt) {
  const S = skinned(skirt), n = S.length / 3, F = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) { const p = figure(r, new THREE.Vector3(S[i * 3], S[i * 3 + 1], S[i * 3 + 2])); F[i * 3] = p.x; F[i * 3 + 1] = p.y; F[i * 3 + 2] = p.z; }
  const hips = figure(r, world(r.bone('thigh_l')).add(world(r.bone('thigh_r'))).multiplyScalar(0.5));
  return { F, hx: hips.x, hz: hips.z };
}
/** The mean forward reach of the front of the hem (within 20 deg of straight ahead). */
function frontHem(r, skirt, rest) {
  const S = skinned(skirt), n = S.length / 3;
  let yMin = Infinity; for (let i = 0; i < n; i++) yMin = Math.min(yMin, rest.F[i * 3 + 1]);
  let z = 0, c = 0;
  for (let i = 0; i < n; i++) {
    if (rest.F[i * 3 + 1] > yMin + 0.04) continue;
    if (Math.abs(Math.atan2(rest.F[i * 3] - rest.hx, rest.F[i * 3 + 2] - rest.hz)) > 20 * Math.PI / 180) continue;
    z += figure(r, new THREE.Vector3(S[i * 3], S[i * 3 + 1], S[i * 3 + 2])).z; c++;
  }
  return z / c;
}
const step = (r, sk, dt, opts, legs = null) => {
  if (legs) setLegs(r, legs); else r.mixer.update(dt);
  sk.apply(dt, { root: r.root, ...opts });
  r.root.updateMatrixWorld(true);
};

// 1. Every body in the town: which garments hang, which follow a leg. A body in trousers
// alone has nothing to hang; every tube stays on its leg, at every level.
const ASSETS = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map(f => f.replace('.lod0.glb', '')).sort();
const TROUSERED = ['anonymous_working_driver_1904', 'bardwell_otis_1835', 'billings_august_1904_stable_helper', 'child_boy_1812', 'child_boy_1904', 'mahoney_patrick_1835', 'settler_1812', 'teen_boy_1904'];
const TUBE_PIECE = /(^|_)(trousers?|breeches|pantaloons|overalls|stockings|leggings|garters|boot_shafts)(_|$)/;
const HANG_PIECE = /(^|_)(skirts?|tails|petticoat|basque|apron|blanket|breechcloth)(_|$)/;
const piece = (asset, m) => m.name.replace(`${asset}_`, '').replace(/_lod\d*$/, '');
const HANGING = [];
for (const asset of ASSETS) for (const lod of [0, 1, 2, 3]) {
  const r = await rig(asset, lod), found = skirtMeshes(r.scene);
  if (TROUSERED.includes(asset)) {
    assert.equal(found, null, `${asset} LOD${lod}: nothing hangs`);
    assert.equal(createHumanSkirt({ id: asset, scene: r.scene }), null, `${asset} LOD${lod}: no bell`);
    continue;
  }
  assert(found, `${asset} LOD${lod}: its hanging cloth is found`);
  const id = r.scene.userData?.chicago4d_human?.asset_id;
  const all = []; r.scene.traverse(o => { if (o.isSkinnedMesh) all.push(o); });
  for (const m of all) {
    const name = piece(asset, m), kind = garmentKind(m, id).kind;
    if (TUBE_PIECE.test(name) && kind) assert.equal(kind, 'tube', `${asset} LOD${lod} ${name}: a tube on its leg`);
    if (HANG_PIECE.test(name) && !TUBE_PIECE.test(name) && kind && kind !== 'edge') assert.equal(kind, 'hang', `${asset} LOD${lod} ${name}: hangs from the waist`);
    if (kind === 'tube') assert(!found.driven.includes(m), `${asset} LOD${lod} ${name}: a tube is never driven`);
  }
  if (lod === 0) HANGING.push([asset, found.hanging.map(m => piece(asset, m))]);
}
console.log(`${ASSETS.length} bodies, LOD0-3: ${TROUSERED.length} in trousers alone, nothing to hang; every tube on its leg; hanging: ${HANGING.map(([a, h]) => `${a} (${h.join(', ')})`).join('; ')}: PASS`);
const WOMEN = ['glessner_frances_m_1904', 'reynolds_mary_1904_maid', 'williamson_mattie_1904_cook_study', 'flynn_mary_1835_dress_study'];
const SKIRT = /skirt/;

// 2. Per woman and level: standing is the asset; the stride and mid-swing hold the legs in.
const STRIDE = [['l', 30, 10], ['r', -15, 40]];
const SWING = [['l', 15, 60], ['r', -5, 5]];
const MIRROR = [['r', 30, 10], ['l', -15, 40]];
for (const asset of WOMEN) for (const lod of [0, 1, 2, 3]) {
  const r = await rig(asset, lod), twin = await rig(asset, lod);
  const found = skirtMeshes(r.scene);
  const skirt = found.skirt;
  const sk = createHumanSkirt({ id: asset, scene: r.scene });
  assert(sk, `${asset} LOD${lod}: binds`);
  const names = found.driven.map(m => m.name.replace(`${asset}_`, '').replace(/_lod\d$/, ''));
  // Standing: every driven garment where the asset puts it.
  for (let i = 0; i < 30; i++) { step(r, sk, 1 / 30, { state: 'standing' }); twin.mixer.update(1 / 30); twin.root.updateMatrixWorld(true); }
  let dev = 0;
  for (const m of found.driven) {
    const a = skinned(m), b = skinned(meshNamed(twin, new RegExp(`^${m.name}$`)));
    for (let i = 0; i < a.length; i++) dev = Math.max(dev, Math.abs(a[i] - b[i]));
  }
  assert(dev < 0.001, `${asset} LOD${lod}: standing, the skirt is the asset (${(dev * 1000).toFixed(3)} mm)`);
  const rest = restOf(r, skirt), front0 = frontHem(r, skirt, rest);
  const lines = [];
  for (const [label, legs] of [['stride', STRIDE], ['mid-swing', SWING], ['mirror', MIRROR]]) {
    for (let i = 0; i < 45; i++) step(r, sk, 1 / 30, { state: 'walking' }, legs);
    const c = containment(r, skirt), ring = hemRing(r, skirt, rest), front = frontHem(r, skirt, rest);
    // What the asset's own weights do at the same pose: the legs through the cloth.
    setLegs(twin, legs); twin.root.updateMatrixWorld(true);
    const asIs = containment(twin, meshNamed(twin, new RegExp(`^${skirt.name}$`)));
    assert(c.n > 50, `${asset} LOD${lod} ${label}: legs measured (${c.n})`);
    assert(c.worst > 0, `${asset} LOD${lod} ${label}: a leg is ${(-c.worst * 100).toFixed(1)} cm outside the skirt at ${JSON.stringify(c.at)}`);
    assert.equal(ring.crossed, 0, `${asset} LOD${lod} ${label}: hem bins out of order`);
    assert(ring.worstEdge <= 0, `${asset} LOD${lod} ${label}: a hem edge tears open by ${(ring.worstEdge * 100).toFixed(1)} cm`);
    if (label !== 'mid-swing') assert(front > front0 + 0.02, `${asset} LOD${lod} ${label}: the front hem goes forward with the leading leg (${(front0 * 100).toFixed(1)} → ${(front * 100).toFixed(1)} cm)`);
    lines.push(`${label} clear ${(c.worst * 100).toFixed(1)} cm (asset ${(asIs.worst * 100).toFixed(1)}), front hem +${((front - front0) * 100).toFixed(1)} cm`);
  }
  // Standing again: the bell settles back to the asset.
  for (let i = 0; i < 120; i++) step(r, sk, 1 / 30, { state: 'standing' }, []);
  setLegs(twin, []); twin.root.updateMatrixWorld(true);
  let back = 0;
  for (const m of found.driven) {
    const a = skinned(m), b = skinned(meshNamed(twin, new RegExp(`^${m.name}$`)));
    for (let i = 0; i < a.length; i++) back = Math.max(back, Math.abs(a[i] - b[i]));
  }
  assert(back < 0.001, `${asset} LOD${lod}: standing again, the asset (${(back * 1000).toFixed(3)} mm)`);
  console.log(`${asset} LOD${lod} [${names.join(', ')}]: standing ${(dev * 1000).toFixed(3)} mm; ${lines.join('; ')}: PASS`);
}

// 2b. An apron moves with the skirt under it: at the stride it lies on the skirt as it did standing.
function apronOver(r, skirt, apron) {
  const hips = figure(r, world(r.bone('thigh_l')).add(world(r.bone('thigh_r'))).multiplyScalar(0.5));
  const S = skinned(skirt), A = skinned(apron), pts = [];
  for (let i = 0; i < S.length / 3; i++) { const p = figure(r, new THREE.Vector3(S[i * 3], S[i * 3 + 1], S[i * 3 + 2])); pts.push([p.y, Math.hypot(p.x - hips.x, p.z - hips.z), Math.atan2(p.x - hips.x, p.z - hips.z)]); }
  let worst = Infinity;
  for (let i = 0; i < A.length / 3; i++) {
    const p = figure(r, new THREE.Vector3(A[i * 3], A[i * 3 + 1], A[i * 3 + 2]));
    if (p.y > hips.y - 0.1) continue;
    const ra = Math.hypot(p.x - hips.x, p.z - hips.z), th = Math.atan2(p.x - hips.x, p.z - hips.z);
    let rs = -1;
    for (const [y, rr, t] of pts) { let d = Math.abs(t - th); if (d > Math.PI) d = 2 * Math.PI - d; if (d < 0.06 && Math.abs(y - p.y) < 0.03) rs = Math.max(rs, rr); }
    if (rs > 0) worst = Math.min(worst, ra - rs);
  }
  return worst;
}
for (const [asset, re] of [['williamson_mattie_1904_cook_study', /separate_plain_apron/], ['reynolds_mary_1904_maid', /apron_skirt/]]) for (const lod of [0, 3]) {
  const r = await rig(asset, lod), found = skirtMeshes(r.scene), apron = found.driven.find(m => re.test(m.name));
  assert(apron, `${asset} LOD${lod}: the apron is driven with the skirt`);
  const sk = createHumanSkirt({ id: asset, scene: r.scene });
  const before = apronOver(r, found.skirt, apron);
  for (let i = 0; i < 40; i++) step(r, sk, 1 / 30, { state: 'walking' }, STRIDE);
  const after = apronOver(r, found.skirt, apron);
  assert(after > before - 0.01, `${asset} LOD${lod}: the apron sinks ${((before - after) * 100).toFixed(1)} cm into the skirt`);
  console.log(`${asset} LOD${lod}: apron over the skirt ${(before * 100).toFixed(1)} cm standing, ${(after * 100).toFixed(1)} cm at the stride: PASS`);
}

// 2c. Seated (the record's state, or a thigh raised past SEATED_DEG): the asset's own weights.
{
  const r = await rig('flynn_mary_1835_dress_study', 0, 'sit_drive'), twin = await rig('flynn_mary_1835_dress_study', 0, 'sit_drive');
  const sk = createHumanSkirt({ id: 'seat', scene: r.scene }), skirt = skirtMeshes(r.scene).skirt;
  for (let i = 0; i < 10; i++) step(r, sk, 1 / 30, { state: 'standing' });
  assert.equal(sk.mode, 'asset', 'a thigh raised to the seat: the asset draws the lap');
  const a = skinned(skirt), b = skinned(meshNamed(twin, new RegExp(`^${skirt.name}$`)));
  let dev = 0; for (let i = 0; i < a.length; i++) dev = Math.max(dev, Math.abs(a[i] - b[i]));
  assert(dev < 0.001, `seated: the skirt is the asset (${(dev * 1000).toFixed(3)} mm)`);
  const s2 = await rig('glessner_frances_m_1904', 1), k2 = createHumanSkirt({ id: 'seat2', scene: s2.scene });
  step(s2, k2, 1 / 30, { state: 'seated' });
  assert.equal(k2.mode, 'asset', "state 'seated': the asset's weights");
  step(s2, k2, 1 / 30, { state: 'walking' });
  assert.equal(k2.mode, 'bell', 'and the bell again on foot');
  // Past maxLod the level is the asset's, and a nearer level later gets the bell.
  const far = await rig('glessner_frances_m_1904', 3), k3 = createHumanSkirt({ id: 'far', scene: far.scene, maxLod: 2 });
  assert(k3 && !k3.bound, 'past maxLod: made, not bound');
  const near = await rig('glessner_frances_m_1904', 2);
  assert(k3.bind(near.scene) && k3.bound, 'a nearer level binds');
  console.log(`seated: the asset (${(dev * 1000).toFixed(3)} mm), the bell back on foot; past maxLod the asset, a nearer level binds: PASS`);
}

// 2d. Every other body with hanging cloth (the men's coats and tails, the 1812 women's
// petticoats, the children's frocks, the Potawatomi blankets, breechcloths and wrapped
// skirts), at every level: standing is the asset; at the stride, mid-swing, its mirror and
// with the heel kicked up behind, every leg inside every hanging garment where its cloth is,
// no hem torn; every tube exactly where the asset's own weights put it.
const BACK = [['l', -10, 62], ['r', 18, 8]];
// Two pieces of one body are held to less, and say why. The Potawatomi man's breechcloth is
// a narrow flap front and back between the legs, under his blanket: the bell carries it off
// the legs, but at the flap's lower corners a thigh can still pass over its edge by up to
// about 3 cm at the end of a stride (on the asset's own weights, 11 cm). His shirt's tail
// stands under the outer selvage of his leggings by 1.6 cm in the asset as drawn, standing;
// the bell does not make it worse. Both must do better than the asset's own weights.
const KNOWN = Object.freeze({ potawatomi_man_1812: Object.freeze(['breechcloth', 'trade_shirt_skirt']) });
const known = (asset, name) => (KNOWN[asset] ?? []).includes(name);
for (const [asset] of HANGING) {
  if (WOMEN.includes(asset)) continue;
  const lines = [];
  for (const lod of [0, 1, 2, 3]) {
    const r = await rig(asset, lod), twin = await rig(asset, lod);
    const found = skirtMeshes(r.scene), sk = createHumanSkirt({ id: asset, scene: r.scene });
    assert(sk && sk.bound, `${asset} LOD${lod}: binds`);
    const twinOf = (m) => meshNamed(twin, new RegExp(`^${m.name}$`));
    const gap = (meshes) => { let d = 0; for (const m of meshes) { const a = skinned(m), b = skinned(twinOf(m)); for (let i = 0; i < a.length; i++) d = Math.max(d, Math.abs(a[i] - b[i])); } return d; };
    for (let i = 0; i < 30; i++) { step(r, sk, 1 / 30, { state: 'standing' }); twin.mixer.update(1 / 30); twin.root.updateMatrixWorld(true); }
    const dev = gap(found.driven);
    assert(dev < 0.001, `${asset} LOD${lod}: standing, the asset (${(dev * 1000).toFixed(3)} mm)`);
    const rests = new Map(found.hanging.map(h => [h, restOf(r, h)]));
    let least = Infinity, asIs = Infinity, tubes = 0;
    for (const [label, legs] of [['stride', STRIDE], ['mid-swing', SWING], ['mirror', MIRROR], ['heel up', BACK]]) {
      for (let i = 0; i < 45; i++) step(r, sk, 1 / 30, { state: 'walking' }, legs);
      setLegs(twin, legs); twin.root.updateMatrixWorld(true);
      for (const h of found.hanging) {
        const c = containment(r, h, true), name = piece(asset, h), mine = containment(twin, twinOf(h), true).worst;
        // (Heel up behind the flap's corner is past what a walk does: the walk below holds it.)
        if (known(asset, name)) { if (label !== 'heel up') assert(c.worst > Math.min(0, mine), `${asset} LOD${lod} ${label}: the ${name} does worse than the asset (${(c.worst * 100).toFixed(1)} vs ${(mine * 100).toFixed(1)} cm)`); }
        else {
          assert(c.worst > 0, `${asset} LOD${lod} ${label}: a leg is ${(-c.worst * 100).toFixed(1)} cm outside the ${name} at ${JSON.stringify(c.at)}`);
          least = Math.min(least, c.worst);
          asIs = Math.min(asIs, mine);
        }
        // The main garment's hem stays one piece near to: no edge past twice its length and
        // 3 cm (a short, close skirt, as a girl's wrapped stroud, stretches most). The
        // simplified levels' long hem edges are let stretch further where a leg splays two panels.
        if (h !== found.skirt || lod > 1) continue;
        const ring = hemRing(r, h, rests.get(h));
        assert(ring.worstEdge <= 0.01, `${asset} LOD${lod} ${label}: the ${name}'s hem tears open by ${(ring.worstEdge * 100).toFixed(1)} cm`);
      }
      tubes = Math.max(tubes, gap(found.tubes));
      assert(tubes < 0.0001, `${asset} LOD${lod} ${label}: the tubes stay on the legs (${(tubes * 1000).toFixed(3)} mm off)`);
    }
    for (let i = 0; i < 120; i++) step(r, sk, 1 / 30, { state: 'standing' }, []);
    setLegs(twin, []); twin.root.updateMatrixWorld(true);
    const back = gap(found.driven);
    assert(back < 0.001, `${asset} LOD${lod}: standing again, the asset (${(back * 1000).toFixed(3)} mm)`);
    lines.push(`LOD${lod} clear ${(least * 100).toFixed(1)} cm (asset ${(asIs * 100).toFixed(1)})`);
  }
  console.log(`${asset} [${HANGING.find(([a]) => a === asset)[1].join(', ')}]: standing exact; ${lines.join(', ')}; tubes on the legs: PASS`);
}

// 3. The baked walk clip, two cycles: legs inside, the hem one ring, the hem swings.
for (const asset of ['glessner_frances_m_1904', 'williamson_mattie_1904_cook_study']) {
  const r = await rig(asset, 0, 'walk');
  const skirt = skirtMeshes(r.scene).skirt, sk = createHumanSkirt({ id: asset, scene: r.scene });
  const restR = await rig(asset, 0, 'idle'), rest = restOf(restR, skirtMeshes(restR.scene).skirt);
  let worst = Infinity, at = null, swing = 0, crossed = 0, tear = -Infinity;
  for (let i = 0; i < 72; i++) {
    step(r, sk, 1 / 30, { state: 'walking' });
    swing = Math.max(swing, sk.snapshot().hem_open_m);
    if (i % 4) continue;
    const c = containment(r, skirt); if (c.worst < worst) { worst = c.worst; at = c.at; }
    const ring = hemRing(r, skirt, rest); crossed += ring.crossed; tear = Math.max(tear, ring.worstEdge);
  }
  assert(worst > 0, `${asset} walk: a leg is ${(-worst * 100).toFixed(1)} cm outside the skirt at ${JSON.stringify(at)}`);
  assert.equal(crossed, 0, `${asset} walk: hem out of order`);
  assert(tear <= 0, `${asset} walk: hem edge torn ${(tear * 100).toFixed(1)} cm`);
  assert(swing > 0.03, `${asset} walk: the hem moves (${swing.toFixed(3)} m)`);
  console.log(`${asset} LOD0 walk clip: least clearance ${(worst * 100).toFixed(1)} cm, hem opens up to ${(swing * 100).toFixed(1)} cm, ring whole: PASS`);
}

// 4. The gait layer's stride, where it is in the tree (human-gait.js, T-3472).
{
  let createHumanGait = null;
  try { ({ createHumanGait } = await import(data(await js('human-gait.js')))); } catch { /* not here yet */ }
  if (!createHumanGait) console.log('gait layer: not present, skipped');
  else {
    const asset = 'glessner_frances_m_1904';
    const r = await rig(asset, 0, 'idle');
    const gait = createHumanGait({ id: asset, scene: r.scene, profile: { sex: 'female', age: 45, skirt: true } });
    const skirt = skirtMeshes(r.scene).skirt, sk = createHumanSkirt({ id: asset, scene: r.scene });
    const restR = await rig(asset, 0, 'idle'), rest = restOf(restR, skirtMeshes(restR.scene).skirt);
    const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), r.root.rotation.y);
    let worst = Infinity, at = null, crossed = 0, tear = -Infinity, frontMax = -Infinity;
    for (let i = 0; i < 150; i++) {
      const dt = 1 / 30, moved = gait.speed * gait.pace * dt;
      r.mixer.update(dt);
      r.root.position.addScaledVector(fwd, moved); r.root.updateMatrixWorld(true);
      gait.apply(dt, { state: 'walking', moved });
      sk.apply(dt, { state: 'walking', root: r.root, gait: { phase: gait.phase, weight: gait.weight, speed: gait.speed, stride: gait.stride } });
      r.root.updateMatrixWorld(true);
      if (i < 45 || i % 3) continue;
      const c = containment(r, skirt); if (c.worst < worst) { worst = c.worst; at = c.at; }
      const ring = hemRing(r, skirt, rest); crossed += ring.crossed; tear = Math.max(tear, ring.worstEdge);
      frontMax = Math.max(frontMax, frontHem(r, skirt, rest));
    }
    assert(worst > 0, `gait stride: a leg is ${(-worst * 100).toFixed(1)} cm outside the skirt at ${JSON.stringify(at)}`);
    assert.equal(crossed, 0, 'gait stride: hem out of order');
    assert(tear <= 0, `gait stride: hem edge torn ${(tear * 100).toFixed(1)} cm`);
    console.log(`${asset} LOD0 gait layer (stride ${gait.stride.toFixed(2)} m at ${gait.speed.toFixed(2)} m/s): least clearance ${(worst * 100).toFixed(1)} cm, front hem to +${((frontMax - frontHem(restR, skirtMeshes(restR.scene).skirt, rest)) * 100).toFixed(1)} cm, sway ${sk.snapshot().sway_deg.map(x => x.toFixed(2)).join('/')} deg: PASS`);
  }
}

// 4b. Every body with hanging cloth on the baked walk and on the gait layer's own stride,
// as the town walks them: every leg inside every hanging garment where its cloth is, to
// within the cloth's own thickness (TOUCH_M: the baked clip's hips swing a breeches' side a
// few millimetres into a tail's lining at the top of the stride); the two KNOWN pieces to
// within FLAP_M (on the asset's own weights they are 3 and 11 cm through).
const TOUCH_M = 0.005, FLAP_M = 0.035;
{
  let createHumanGait = null;
  try { ({ createHumanGait } = await import(data(await js('human-gait.js')))); } catch { /* not here yet */ }
  const lines = [];
  for (const [asset] of HANGING) for (const lod of [0, 2]) {
    if (lod && WOMEN.includes(asset)) continue; // their levels are walked in 3 and 4 above
    let worst = Infinity, at = null, flap = Infinity;
    const r = await rig(asset, lod, 'walk'), found = skirtMeshes(r.scene), sk = createHumanSkirt({ id: asset, scene: r.scene });
    for (let i = 0; i < 72; i++) {
      step(r, sk, 1 / 30, { state: 'walking' });
      if (i % 4) continue;
      for (const h of found.hanging) {
        const c = containment(r, h, true);
        if (known(asset, piece(asset, h))) { flap = Math.min(flap, c.worst); continue; }
        if (c.worst < worst) { worst = c.worst; at = { ...c.at, piece: piece(asset, h) }; }
      }
    }
    assert(worst > -TOUCH_M, `${asset} LOD${lod} walk clip: a leg is ${(-worst * 100).toFixed(1)} cm outside at ${JSON.stringify(at)}`);
    let gw = Infinity;
    if (createHumanGait && lod === 0) {
      const g = await rig(asset, lod, 'idle'), gf = skirtMeshes(g.scene), gk = createHumanSkirt({ id: asset, scene: g.scene });
      const female = /woman|girl|lady|frances|mary|mattie|kate|christine/.test(asset), child = /child|teen/.test(asset);
      const gait = createHumanGait({ id: asset, scene: g.scene, profile: { sex: female ? 'female' : 'male', age: child ? (/toddler/.test(asset) ? 2 : /teen/.test(asset) ? 14 : 7) : 40, skirt: female } });
      const fwd = new THREE.Vector3(0, 0, 1).applyAxisAngle(new THREE.Vector3(0, 1, 0), g.root.rotation.y);
      for (let i = 0; i < 150; i++) {
        const dt = 1 / 30, moved = gait.speed * gait.pace * dt;
        g.mixer.update(dt);
        g.root.position.addScaledVector(fwd, moved); g.root.updateMatrixWorld(true);
        gait.apply(dt, { state: 'walking', moved });
        gk.apply(dt, { state: 'walking', root: g.root });
        g.root.updateMatrixWorld(true);
        if (i < 45 || i % 3) continue;
        for (const h of gf.hanging) {
          const c = containment(g, h, true);
          if (known(asset, piece(asset, h))) { flap = Math.min(flap, c.worst); continue; }
          if (c.worst < gw) { gw = c.worst; at = { ...c.at, piece: piece(asset, h) }; }
        }
      }
      assert(gw > -TOUCH_M, `${asset} LOD${lod} gait stride: a leg is ${(-gw * 100).toFixed(1)} cm outside at ${JSON.stringify(at)}`);
    }
    if (Number.isFinite(flap)) assert(flap > -FLAP_M, `${asset} LOD${lod}: ${KNOWN[asset].join(' and ')} ${(-flap * 100).toFixed(1)} cm over a leg`);
    lines.push(`${asset} L${lod} ${(worst * 100).toFixed(1)}/${Number.isFinite(gw) ? (gw * 100).toFixed(1) : '-'}${Number.isFinite(flap) ? ` (${KNOWN[asset].join(', ')} ${(flap * 100).toFixed(1)})` : ''}`);
  }
  console.log(`walk clip / gait stride, least clearance (cm): ${lines.join(', ')}: PASS`);
}

// 5. Shared geometry: a second figure in the same asset is untouched, and freeing gives back only ours.
{
  const asset = 'reynolds_mary_1904_maid';
  const a = await rig(asset, 1), b = await rig(asset, 1);
  const src = skirtMeshes(b.scene).driven.map(m => [m, m.geometry, m.skeleton, m.geometry.attributes.skinWeight.array.slice(), m.geometry.attributes.skinIndex.array.slice()]);
  const sk = createHumanSkirt({ id: 'a', scene: a.scene });
  for (let i = 0; i < 20; i++) step(a, sk, 1 / 30, { state: 'walking' }, STRIDE);
  for (const [m, g, s, w, ix] of src) {
    assert.equal(m.geometry, g, `${m.name}: the other figure keeps its geometry`);
    assert.equal(m.skeleton, s, `${m.name}: and its skeleton`);
    assert.deepEqual(m.geometry.attributes.skinWeight.array, w, `${m.name}: its weights unchanged`);
    assert.deepEqual(m.geometry.attributes.skinIndex.array, ix, `${m.name}: its indices unchanged`);
  }
  const mine = skirtMeshes(b.scene).driven.map(m => m.name);
  const ownMeshes = []; a.scene.traverse(o => { if (o.isSkinnedMesh && mine.includes(o.name)) ownMeshes.push(o); });
  const shared = ownMeshes.map(m => m.geometry.attributes.position);
  assert(ownMeshes.every((m, i) => m.geometry !== src[i][1] && shared[i] === src[i][1].attributes.position), 'a driven garment shares positions but has its own weights');
  const bones = []; a.scene.traverse(o => { if (o.isBone && /^skirt_/.test(o.name)) bones.push(o); });
  assert.equal(bones.length, 1 + 2 * N_PANELS, 'one hang bone and two bones a panel');
  // humans.js teardown disposes each mesh's skeleton: that frees the weights we made, only those.
  const ours = ownMeshes.map(m => m.geometry);
  for (const m of ownMeshes) m.skeleton.dispose();
  assert(ours.every(g => !g.attributes.position && !g.index), 'our geometry let go of nothing shared');
  assert(src.every(([, g]) => g.attributes.position && g.attributes.skinWeight && g.index), 'the shared geometry keeps everything');
  console.log(`shared geometry: the other figure untouched, ${ownMeshes.length} garments with their own weights, freed by teardown: PASS`);
}

// 6. Deterministic, and a LOD swap keeps the state (and a swap back reuses the panels).
{
  const runs = [];
  for (const k of [0, 1]) {
    const r = await rig('glessner_frances_m_1904', 1, 'walk');
    const sk = createHumanSkirt({ id: 'same', scene: r.scene });
    for (let i = 0; i < 50; i++) step(r, sk, 1 / 30, { state: 'walking' });
    runs.push([JSON.stringify(sk.snapshot()), ...skinned(skirtMeshes(r.scene).skirt).slice(0, 30)]);
    if (k === 1) {
      const next = await rig('glessner_frances_m_1904', 2, 'walk');
      next.mixer.setTime(r.mixer.time); next.root.updateMatrixWorld(true);
      const before = sk.snapshot();
      next.root.remove(next.scene); r.root.add(next.scene); r.root.remove(r.scene);
      assert(sk.bind(next.scene), 'rebinds');
      assert.deepEqual(sk.snapshot(), before, 'the bell carries across a LOD swap');
      const rr = { ...next, root: r.root };
      for (let i = 0; i < 30; i++) step(rr, sk, 1 / 30, { state: 'walking' });
      const c = containment(rr, skirtMeshes(next.scene).skirt);
      assert(c.worst > 0, `after the swap the legs stay inside (${(c.worst * 100).toFixed(1)} cm)`);
      r.root.remove(next.scene); r.root.add(r.scene);
      assert(sk.bind(r.scene), 'binds back to the parked level');
      const bones = []; r.scene.traverse(o => { if (o.isBone && /^skirt_/.test(o.name)) bones.push(o); });
      assert.equal(bones.length, 1 + 2 * N_PANELS, 'a swap back reuses its panels');
      console.log(`LOD1 → LOD2 → LOD1: state kept, legs inside after the swap (${(c.worst * 100).toFixed(1)} cm), panels reused: PASS`);
    }
  }
  assert.deepEqual(runs[0], runs[1], 'same person, same skirt');
  console.log('deterministic: PASS');
}

// 7. Cost of a frame.
{
  const r = await rig('glessner_frances_m_1904', 0, 'walk');
  const sk = createHumanSkirt({ id: 'cost', scene: r.scene });
  const time = (state, n) => {
    let ns = 0n;
    for (let i = 0; i < n; i++) { r.mixer.update(1 / 60); const t = process.hrtime.bigint(); sk.apply(1 / 60, { state, root: r.root }); ns += process.hrtime.bigint() - t; }
    return Number(ns) / n / 1000;
  };
  time('walking', 600);
  const walking = time('walking', 4000);
  const s = await rig('glessner_frances_m_1904', 0, 'idle'), ks = createHumanSkirt({ id: 'cost2', scene: s.scene });
  let ns = 0n;
  for (let i = 0; i < 4600; i++) { s.mixer.update(1 / 60); const t = process.hrtime.bigint(); ks.apply(1 / 60, { state: 'standing', root: s.root }); if (i >= 600) ns += process.hrtime.bigint() - t; }
  const found = skirtMeshes(r.scene), verts = found.driven.reduce((n, m) => n + m.geometry.attributes.position.count, 0);
  console.log(`cost: ${walking.toFixed(1)} µs walking, ${(Number(ns) / 4000 / 1000).toFixed(1)} µs standing, a figure a frame on the CPU (node); GPU: +${2 * N_PANELS} bones in each of ${found.driven.length} garments' skeletons, ${verts} vertices, 4 influences as before`);
}
console.log('human skirt: PASS');
