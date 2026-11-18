// SPDX-License-Identifier: GPL-3.0-or-later
// A coat closes under the arm and at the back vent (renderers/web/js/human-coat.js, T-3553
// round 2: "on coated men a gap opens at the armpit ... a thin sliver shows at the coat's
// back vent"). On the real exports, on the CPU, every body at every level.
//
// The armpit: the figure posed as it walks (the baked walk clip with the arm swing laid on
// it: hanging, 19 deg back with the elbow at 20, 6 deg forward with it at 50), every mesh
// rasterised orthographically round each armpit from five directions (from behind the side
// to in front of it), and the area where something that was under the outermost sleeved
// garment at bind (the skin, a shirt, a waistcoat) is the nearest thing to the eye. It must
// be at most GAP_MM2 in any view at the two near levels, and never more than drawn at the
// far ones. Only hidden layers move: the sleeved garment and everything outside it keep
// their positions, a moved vertex was inside that garment at bind, moved inward along its
// normal, no further than DEPTH_M, and no further from the armpit than the zone.
//
// The vent: the tails or skirts of every coat with a back vent, driven as humans.js drives
// them (the walk clip and human-skirt.js), seen from behind and at 25 and 50 deg either side,
// standing and through two strides: the area between the two sides, in the middle 5 cm of the
// back, where something further off shows through. It must be at most VENT_MM2 at the two
// near levels and a small part of what was drawn at the far ones (FAR_VENT_MM2 at most), from
// a vent that showed on every level.
//
// Topology, UVs and skin weights unchanged; once per loaded body; wired into humans.js's
// parse() before the waist is fitted. COAT_OLD=1 measures the exports as drawn (the code
// before this file): it fails, and prints what it finds.
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
// A module loaded from a data: URL cannot resolve its own relative imports (human-skirt.js reads
// './human-skeletons.js' since #2165), so they are pointed at the files beside it.
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8'))
  .replace("from 'three'", `from '${three}'`)
  .replace(/from '\.\/([\w.-]+\.js)'/g, (_, f) => `from '${new URL(`renderers/web/js/${f}`, here).href}'`);
const coat = await import(data(await js('human-coat.js')));
const { createHumanSkirt } = await import(data(await js('human-skirt.js')));
const OLD = process.env.COAT_OLD === '1';
const fitCoats = OLD ? () => null : coat.fitCoats;

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
const bytesOf = new Map();
async function load(asset, lod) {
  const key = `${asset}.${lod}`;
  if (!bytesOf.has(key)) bytesOf.set(key, geometryOnly(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytesOf.get(key).slice(0), '');
  gltf.scene.updateMatrixWorld(true);
  return gltf;
}

export const GAP_MM2 = 8, VENT_MM2 = 8, FAR_VENT_MM2 = 64;
const matName = (o) => (Array.isArray(o.material) ? o.material[0] : o.material)?.name ?? '';
const meshesOf = (scene) => { const out = []; scene.traverse((o) => { if (o.isSkinnedMesh && o.geometry.index) out.push(o); }); return out; };
const isSkin = (m) => matName(m).split('__')[0] === 'skin';
const isCloth = (m) => /^garment/.test(matName(m));

// ---- geometry helpers (the test's own; it shares nothing with the module but the exports) ----
function bindPos(mesh) {
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function posed(mesh) {
  mesh.skeleton.update();
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
/** Of a mesh's bind surface: nearest point to p within reach, signed along the side its normals face. */
function sideOf(mesh) {
  const P = bindPos(mesh), idx = mesh.geometry.index.array, T = idx.length / 3, cell = 0.03, grid = new Map(), nrm = mesh.geometry.attributes.normal;
  const sign = new Int8Array(T), a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3(), q = new THREE.Vector3(), tri = new THREE.Triangle();
  const nm = new THREE.Matrix3().getNormalMatrix(mesh.bindMatrix);
  for (let t = 0; t < T; t++) {
    const k3 = [0, 1, 2].map((k) => idx[t * 3 + k]);
    tri.set(a.fromArray(P, k3[0] * 3), b.fromArray(P, k3[1] * 3), c.fromArray(P, k3[2] * 3)).getNormal(q);
    n.set(0, 0, 0); for (const i of k3) n.add(new THREE.Vector3().fromBufferAttribute(nrm, i).applyMatrix3(nm));
    sign[t] = q.dot(n) >= 0 ? 1 : -1;
    const lo = [0, 1, 2].map((k) => Math.floor(Math.min(a.getComponent(k), b.getComponent(k), c.getComponent(k)) / cell));
    const hi = [0, 1, 2].map((k) => Math.floor(Math.max(a.getComponent(k), b.getComponent(k), c.getComponent(k)) / cell));
    for (let x = lo[0]; x <= hi[0]; x++) for (let y = lo[1]; y <= hi[1]; y++) for (let z = lo[2]; z <= hi[2]; z++) { const k = `${x},${y},${z}`; let l = grid.get(k); if (!l) grid.set(k, (l = [])); l.push(t); }
  }
  // The signed distance by one triangle; where the nearest point is shared (an edge, a corner), the triangle facing p most squarely.
  const by = (p, t) => {
    tri.set(a.fromArray(P, idx[t * 3] * 3), b.fromArray(P, idx[t * 3 + 1] * 3), c.fromArray(P, idx[t * 3 + 2] * 3)).closestPointToPoint(p, q);
    const d = q.distanceTo(p); tri.getNormal(n); return { d, s: n.multiplyScalar(sign[t]).dot(p.clone().sub(q)) };
  };
  return (p, reach) => {
    let best = null;
    const r = Math.ceil(reach / cell), cx = Math.floor(p.x / cell), cy = Math.floor(p.y / cell), cz = Math.floor(p.z / cell), seen = new Set();
    for (let x = cx - r; x <= cx + r; x++) for (let y = cy - r; y <= cy + r; y++) for (let z = cz - r; z <= cz + r; z++) for (const t of grid.get(`${x},${y},${z}`) ?? []) {
      if (seen.has(t)) continue; seen.add(t);
      const o = by(p, t);
      if (!best || o.d < best.d - 1e-6 || (o.d <= best.d + 1e-6 && Math.abs(o.s) > Math.abs(best.s))) best = { d: Math.min(o.d, best?.d ?? Infinity), s: o.s };
    }
    return !best || best.d > reach ? null : best;
  };
}
/** An orthographic id-buffer: which layer's triangle is nearest the eye at each pixel, and whether it was a hidden one. */
function idBuffer(layers, dir, up, centre, half, px) {
  const F = dir.clone().normalize(), R = new THREE.Vector3().crossVectors(up, F).normalize(), U = new THREE.Vector3().crossVectors(F, R);
  const N = Math.round(2 * half / px), depth = new Float64Array(N * N).fill(-Infinity), tag = new Int32Array(N * N).fill(-1), hidden = new Uint8Array(N * N);
  const pr = (P, i, o) => { const x = P[i * 3] - centre.x, y = P[i * 3 + 1] - centre.y, z = P[i * 3 + 2] - centre.z; o[0] = (x * R.x + y * R.y + z * R.z + half) / px; o[1] = (half - (x * U.x + y * U.y + z * U.z)) / px; o[2] = x * F.x + y * F.y + z * F.z; };
  const a = [0, 0, 0], b = [0, 0, 0], c = [0, 0, 0];
  for (const L of layers) for (let t = 0; t < L.idx.length / 3; t++) {
    pr(L.P, L.idx[t * 3], a); pr(L.P, L.idx[t * 3 + 1], b); pr(L.P, L.idx[t * 3 + 2], c);
    const x0 = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0]))), x1 = Math.min(N - 1, Math.ceil(Math.max(a[0], b[0], c[0])));
    const y0 = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1]))), y1 = Math.min(N - 1, Math.ceil(Math.max(a[1], b[1], c[1])));
    if (x0 > x1 || y0 > y1) continue;
    const den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]); if (Math.abs(den) < 1e-12) continue;
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const X = x + 0.5, Y = y + 0.5;
      const l0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den, l1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den, l2 = 1 - l0 - l1;
      if (l0 < -1e-6 || l1 < -1e-6 || l2 < -1e-6) continue;
      const z = l0 * a[2] + l1 * b[2] + l2 * c[2], k = y * N + x;
      if (z > depth[k]) { depth[k] = z; tag[k] = L.tag; hidden[k] = L.hidden ? L.hidden[t] : 0; }
    }
  }
  return { N, tag, hidden, depth };
}
function frameNow(scene) {
  const w = (n) => scene.getObjectByName(n).getWorldPosition(new THREE.Vector3());
  const O = w('thigh_l').add(w('thigh_r')).multiplyScalar(0.5), U = O.clone().sub(w('foot_l').add(w('foot_r')).multiplyScalar(0.5)).normalize();
  const L = w('thigh_l').sub(w('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize();
  return { O, U, L, F: new THREE.Vector3().crossVectors(L, U).normalize(), w };
}

// ---- the armpit ---------------------------------------------------------------------------
/** The sleeved garments (a blanket or shawl over the shoulders is not one), and the outermost of them at the armpits (inside the others least). */
function outerSleeve(scene) {
  const all = meshesOf(scene);
  if (!all.length) return null;
  const sk = all[0].skeleton, j = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[sk.bones.findIndex((b) => b.name === n)].clone().invert());
  // A sleeve: cloth down the upper arm, 10 cm and more out from the shoulder joint (a waistcoat's armhole is not one).
  const cloth = all.filter(isCloth).filter((m) => !/(^|_)(blanket|shawl|wrap|cloak|cape|mantle)(_|$)/.test(m.name)).filter((m) => {
    const P = bindPos(m), p = new THREE.Vector3(); let arm = 0;
    for (const s of ['l', 'r']) {
      const J = j(`upperarm_${s}`), A = j(`lowerarm_${s}`).sub(J).normalize();
      for (let i = 0; i < P.length / 3; i++) if (p.fromArray(P, i * 3).sub(J).dot(A) > 0.1) arm++;
    }
    return arm >= 20;
  });
  if (!cloth.length) return null;
  const pits = ['l', 'r'].map((s) => j(`upperarm_${s}`).add(new THREE.Vector3(0, -0.07, 0)));
  const sides = new Map(cloth.map((m) => [m, sideOf(m)]));
  let best = cloth[0], least = Infinity;
  for (const m of cloth) {
    const P = bindPos(m); let n = 0, inside = 0; const p = new THREE.Vector3();
    for (let i = 0; i < P.length / 3; i++) {
      p.fromArray(P, i * 3); if (Math.min(...pits.map((q) => q.distanceTo(p))) > 0.1) continue; n++;
      if (cloth.some((o) => o !== m && (sides.get(o)(p, 0.06)?.s ?? 1) < 0)) inside++;
    }
    if (n >= 20 && inside / n < least) { least = inside / n; best = m; }
  }
  // The outer garment's open edges (cuffs, neck, front, hem), welded across UV seams.
  const P = bindPos(best), idx = best.geometry.index.array, key = (i) => [0, 1, 2].map((k) => Math.round(P[i * 3 + k] * 2e4)).join(','), count = new Map();
  for (let t = 0; t < idx.length; t += 3) for (let k = 0; k < 3; k++) { const a = key(idx[t + k]), b = key(idx[t + (k + 1) % 3]), e = a < b ? `${a}|${b}` : `${b}|${a}`; count.set(e, (count.get(e) ?? 0) + 1); }
  const rim = []; for (const [e, c] of count) if (c === 1) for (const v of e.split('|')) rim.push(new THREE.Vector3(...v.split(',').map((x) => x / 2e4)));
  const rimFar = (p) => { let d = Infinity; for (const r of rim) d = Math.min(d, r.distanceToSquared(p)); return Math.sqrt(d); };
  return { outer: best, side: sides.get(best), rimFar };
}
/** Per triangle of each layer, whether it lay under the outer garment at bind (every corner inside it, within 5 cm, and 3 cm or more from its open edges). */
function hiddenTris(scene, found) {
  const out = new Map(), p = new THREE.Vector3();
  for (const m of meshesOf(scene)) {
    if (m === found.outer || !(isSkin(m) || isCloth(m))) continue;
    const P = bindPos(m), inside = new Uint8Array(P.length / 3);
    for (let i = 0; i < inside.length; i++) { p.fromArray(P, i * 3); inside[i] = (found.side(p, 0.05)?.s ?? 1) < -5e-4 && found.rimFar(p) > 0.03 ? 1 : 0; }
    const idx = m.geometry.index.array, h = new Uint8Array(idx.length / 3);
    for (let t = 0; t < h.length; t++) h[t] = inside[idx[t * 3]] & inside[idx[t * 3 + 1]] & inside[idx[t * 3 + 2]];
    out.set(m.name, h);
  }
  return out;
}
const POSES = [{ t: 0, swing: 0, elbow: 0 }, { t: 0, swing: -19, elbow: 20 }, { t: 0.5, swing: 6, elbow: 50 }];
function pose(gltf, { t, swing, elbow }) {
  const mixer = new THREE.AnimationMixer(gltf.scene), clip = gltf.animations.find((a) => a.name === 'walk');
  mixer.clipAction(clip).play(); mixer.setTime(t * clip.duration); gltf.scene.updateMatrixWorld(true);
  const fr = frameNow(gltf.scene), axis = fr.L.clone().negate();
  for (const s of ['l', 'r']) for (const [n, deg] of [[`upperarm_${s}`, s === 'l' ? swing : -swing], [`lowerarm_${s}`, elbow]]) {
    const b = gltf.scene.getObjectByName(n); b.parent.updateWorldMatrix(true, false);
    const pq = b.parent.getWorldQuaternion(new THREE.Quaternion()), wq = pq.clone().multiply(b.quaternion);
    b.quaternion.copy(pq.invert().multiply(new THREE.Quaternion().setFromAxisAngle(axis, deg * Math.PI / 180).multiply(wq))); b.updateMatrixWorld(true);
  }
  gltf.scene.updateMatrixWorld(true); mixer.stopAllAction();
}
/** The most hidden cloth or skin showing at either armpit, mm^2, over the poses and views. */
function armpitGap(gltf, hidden) {
  const ms = meshesOf(gltf.scene).filter((m) => !/^eyes/.test(matName(m)));
  let worst = 0, at = null;
  for (const p of POSES) {
    pose(gltf, p);
    const layers = ms.map((m, k) => ({ P: posed(m), idx: m.geometry.index.array, tag: k, hidden: hidden.get(m.name) }));
    // The window scales with the body (a child's armpit is nearer its waist).
    const fr = frameNow(gltf.scene), k = fr.w('upperarm_l').distanceTo(fr.w('upperarm_r')) / 0.4, px = 0.002, half = 0.11 * k;
    for (const s of ['l', 'r']) {
      const side = s === 'l' ? fr.L.clone() : fr.L.clone().negate();
      const centre = fr.w(`upperarm_${s}`).addScaledVector(fr.U, -0.09 * k).addScaledVector(side, -0.03 * k);
      for (const deg of [-60, -30, 0, 30, 60]) {
        const a = deg * Math.PI / 180, dir = side.clone().multiplyScalar(Math.cos(a)).addScaledVector(fr.F, Math.sin(a)).addScaledVector(fr.U, 0.2);
        const buf = idBuffer(layers, dir, fr.U, centre, half, px);
        // Under the shoulder only (the collar and the neck are another matter).
        let n = 0; for (let q = Math.round((half - 0.06 * k) / px) * buf.N; q < buf.hidden.length; q++) n += buf.hidden[q];
        const mm2 = n * px * px * 1e6;
        if (mm2 > worst) { worst = mm2; at = `${s} ${deg}deg swing ${p.swing}`; }
      }
    }
  }
  return { worst, at };
}

// ---- the vent ------------------------------------------------------------------------------
const VENTED = ['officer_first_infantry_1812', 'officer_first_infantry_1812_lieutenant', 'peck_philip_1835', 'private_first_infantry_1812', 'surgeons_mate_first_infantry_1812', 'trader_1812'];
const VIEWS = [[-50, 0.3], [-25, 0.15], [0, 0.15], [25, 0.15], [50, 0.3]]; // degrees round from behind, and up
/**
 * The most of anything else showing through the coat's back below the waist, mm^2, standing
 * and walking: a pixel of something further from the eye than the coat (its tails, skirts or
 * body, any piece of the tails' cloth) on both sides of it within 2.4 cm, across or up and
 * down, where that coat is the middle of its back below the waist (behind the hips, within
 * 5 cm of the middle, under 22 cm above them), the tails on one side at least: the vent, and
 * the top of it at the waist seam. Anything in front of the coat (a turnback, a
 * scabbard, a hand) is not, nor the cut-away front of a tailcoat seen from the side.
 */
function ventGap(gltf, tails) {
  const scene = SkeletonUtils.clone(gltf.scene), root = new THREE.Group(); root.add(scene);
  root.rotation.y = 0.7; root.position.set(3, 0, -2);
  const mixer = new THREE.AnimationMixer(scene);
  mixer.clipAction(gltf.animations.find((a) => a.name === 'walk')).play(); mixer.update(0); root.updateMatrixWorld(true);
  const sk = createHumanSkirt({ id: 'coat-test', scene });
  const ms = meshesOf(scene).filter((m) => !/^eyes/.test(matName(m)));
  const cloth = new Set(ms.filter((m) => tails.test(m.name)).map(matName));
  let worst = 0, at = null;
  for (let f = 0; f < 78; f++) {
    const standing = f < 18;
    if (!standing) mixer.update(1 / 30);
    sk?.apply(1 / 30, { state: standing ? 'standing' : 'walking', root }); root.updateMatrixWorld(true);
    if (f % 6 !== 5) continue;
    const fr = frameNow(scene), layers = ms.map((m) => ({ P: posed(m), idx: m.geometry.index.array, tag: tails.test(m.name) ? 1 : cloth.has(matName(m)) ? 3 : /^accessory/.test(matName(m)) ? 2 : 0 }));
    for (const [deg, up] of VIEWS) {
      const a = deg * Math.PI / 180, dir = fr.F.clone().negate().multiplyScalar(Math.cos(a)).addScaledVector(fr.L, Math.sin(a)).addScaledVector(fr.U, up);
      const px = 0.002, half = 0.36, centre = fr.O.clone().addScaledVector(fr.U, -0.08);
      const buf = idBuffer(layers, dir, fr.U, centre, half, px), N = buf.N, D = buf.depth;
      const R = new THREE.Vector3().crossVectors(fr.U, dir.clone().normalize()).normalize();
      const mid = Math.round((fr.O.clone().sub(centre).dot(R) + half) / px), band = Math.round(0.16 / px);
      // Only the vent: a coat pixel counts where it lies behind the hips, within 5 cm of the middle and under 22 cm above them.
      const Uv = new THREE.Vector3().crossVectors(dir.clone().normalize(), R), w = new THREE.Vector3();
      const back = (k) => {
        w.copy(centre).addScaledVector(R, (k % N + 0.5) * px - half).addScaledVector(Uv, half - (Math.floor(k / N) + 0.5) * px).addScaledVector(dir.clone().normalize(), D[k]).sub(fr.O);
        return -w.dot(fr.F) > 0.03 && Math.abs(w.dot(fr.L)) < 0.05 && w.dot(fr.U) < 0.22;
      };
      const coatAt = (k) => ((buf.tag[k] === 1 || buf.tag[k] === 3) && back(k) ? D[k] : -Infinity);
      let n = 0;
      for (let y = 12; y < N - 12; y++) for (let x = Math.max(12, mid - band); x <= Math.min(N - 13, mid + band); x++) {
        const k = y * N + x;
        if (buf.tag[k] !== 0) continue; // the coat itself, the sky, or a belt or box worn over it
        // The coat on both sides of it, the tails on one side at least.
        const pair = (step) => {
          let p = -Infinity, q = -Infinity, a = -1, b = -1;
          for (let j = 1; j <= 12; j++) {
            if (p === -Infinity && (p = coatAt(k - j * step)) > -Infinity) a = buf.tag[k - j * step];
            if (q === -Infinity && (q = coatAt(k + j * step)) > -Infinity) b = buf.tag[k + j * step];
          }
          return p > -Infinity && q > -Infinity && (a === 1 || b === 1) && D[k] < Math.min(p, q) - 0.003;
        };
        if (pair(1) || pair(N)) n++;
      }
      const mm2 = n * px * px * 1e6;
      if (mm2 > worst) { worst = mm2; at = `${standing ? 'standing' : `walking ${(f / 30).toFixed(1)} s`} ${deg}deg`; }
    }
  }
  return { worst, at };
}

// ---- every body, every level ----------------------------------------------------------------
const ASSETS = (await fs.readdir(new URL('assets/humans/web/', here))).filter((f) => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map((f) => f.replace('.lod0.glb', '')).sort();
// A sleeved garment a dress record may set aside would leave the thinned layers bare: none may be the outer one.
const hideable = new Set();
for (const f of await fs.readdir(new URL('data/humans/variation/', here))) {
  if (!f.endsWith('.json')) continue;
  const walk = (o) => { if (Array.isArray(o)) o.forEach(walk); else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) { if (k === 'hide' && Array.isArray(v)) v.forEach((h) => hideable.add(h)); else walk(v); } };
  walk(JSON.parse(await fs.readFile(new URL(`data/humans/variation/${f}`, here), 'utf8')));
}
const lines = [], failures = [];
let pits = 0, vents = 0;
const check = (ok, msg) => { if (!ok) failures.push(msg); };
for (const asset of ASSETS) {
  const res = [];
  for (const lod of [0, 1, 2, 3]) {
    const before = await load(asset, lod), after = await load(asset, lod);
    const snap = new Map(meshesOf(after.scene).map((m) => [m.name, { pos: m.geometry.attributes.position.array.slice(), uv: m.geometry.attributes.uv?.array.slice(), si: m.geometry.attributes.skinIndex.array.slice(), sw: m.geometry.attributes.skinWeight.array.slice(), idx: m.geometry.index.array.slice() }]));
    const report = fitCoats(after.scene);
    for (const m of meshesOf(after.scene)) {
      const s = snap.get(m.name), g = m.geometry;
      assert.deepEqual(g.attributes.skinIndex.array, s.si, `${asset} LOD${lod} ${m.name}: skin indices kept`);
      assert.deepEqual(g.attributes.skinWeight.array, s.sw, `${asset} LOD${lod} ${m.name}: skin weights kept`);
      if (s.uv) assert.deepEqual(g.attributes.uv.array, s.uv, `${asset} LOD${lod} ${m.name}: UVs kept`);
      assert.deepEqual(g.index.array, s.idx, `${asset} LOD${lod} ${m.name}: topology kept`);
    }
    if (!OLD) {
      const held = meshesOf(after.scene).map((m) => m.geometry.attributes.position.array.slice());
      assert.equal(coat.fitCoats(after.scene), report, `${asset} LOD${lod}: a second call returns the first report`);
      meshesOf(after.scene).forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, held[k], `${asset} LOD${lod} ${m.name}: a second call moved it`));
    }
    // The armpit.
    const found = outerSleeve(before.scene);
    if (found) {
      const piece = found.outer.name.replace(`${asset}_`, '').replace(/_lod\d*$/, '');
      assert(![...hideable].some((h) => piece === h), `${asset}: the outer sleeved garment ${piece} is one a dress record may hide`);
      if (!OLD) assert.equal(report.armpits?.outer, found.outer.name, `${asset} LOD${lod}: the module and the test agree which garment is outermost`);
      const hidden = hiddenTris(before.scene, found);
      // Only hidden layers moved: inward, under the outer garment, near the armpit, at most DEPTH_M.
      const sk = found.outer.skeleton, j = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[sk.bones.findIndex((b) => b.name === n)].clone().invert());
      const shoulders = j('upperarm_l').distanceTo(j('upperarm_r')) / 0.4, pitsAt = ['l', 'r'].map((s) => j(`upperarm_${s}`));
      for (const m of meshesOf(after.scene)) {
        const mb = meshesOf(before.scene).find((o) => o.name === m.name), Pa = bindPos(m), Pb = bindPos(mb), nrm = mb.geometry.attributes.normal;
        const nm = new THREE.Matrix3().getNormalMatrix(mb.bindMatrix), a = new THREE.Vector3(), b = new THREE.Vector3(), nv = new THREE.Vector3();
        for (let i = 0; i < Pa.length / 3; i++) {
          a.fromArray(Pa, i * 3); b.fromArray(Pb, i * 3);
          const d = a.distanceTo(b);
          if (d < 1e-6) continue;
          if (coat.isCoatSkirt(m)) continue; // the vent, below
          assert(m !== found.outer && (isSkin(m) || isCloth(m)), `${asset} LOD${lod} ${m.name}: moved, and it is not under the coat`);
          assert(d <= coat.DEPTH_M * shoulders + 1e-4, `${asset} LOD${lod} ${m.name}: moved ${(d * 1000).toFixed(1)} mm`);
          assert(Math.min(...pitsAt.map((q) => q.distanceTo(b))) < (coat.ZONE.fade + coat.ZONE.below) * shoulders + 0.01, `${asset} LOD${lod} ${m.name}: moved away from the armpit`);
          nv.fromBufferAttribute(nrm, i).applyMatrix3(nm).normalize();
          assert(a.clone().sub(b).dot(nv) < -0.99 * d + 1e-4, `${asset} LOD${lod} ${m.name}: a vertex moved other than inward`);
          assert((found.side(b, 0.07)?.s ?? 1) < 0, `${asset} LOD${lod} ${m.name}: a moved vertex was not under ${found.outer.name}`);
        }
      }
      const g0 = armpitGap(before, hidden), g1 = armpitGap(after, hidden);
      const near = lod <= 1;
      check(near ? g1.worst <= GAP_MM2 : g1.worst <= Math.max(GAP_MM2, g0.worst + 4), `${asset} LOD${lod} ${piece}: ${g1.worst.toFixed(0)} mm2 of what is under it shows at the armpit (${g1.at}; drawn ${g0.worst.toFixed(0)})`);
      res.push(`L${lod} pit ${g0.worst.toFixed(0)}→${g1.worst.toFixed(0)}`);
      pits++;
    }
    // The vent.
    const tails = meshesOf(before.scene).filter(coat.isCoatSkirt);
    if (VENTED.includes(asset)) {
      assert(OLD || report.vents.length === 1, `${asset} LOD${lod}: one vent closed (${report?.vents?.length})`);
      const re = new RegExp(`^(${tails.map((m) => m.name).join('|')})$`);
      const v0 = ventGap(before, re), v1 = ventGap(after, re);
      assert(v0.worst > 100, `${asset} LOD${lod}: the drawn vent shows (${v0.worst.toFixed(0)} mm2)`);
      check(v1.worst <= (lod <= 1 ? VENT_MM2 : Math.max(VENT_MM2, Math.min(FAR_VENT_MM2, 0.05 * v0.worst))), `${asset} LOD${lod}: ${v1.worst.toFixed(0)} mm2 shows through the back vent (${v1.at}; drawn ${v0.worst.toFixed(0)})`);
      res.push(`L${lod} vent ${v0.worst.toFixed(0)}→${v1.worst.toFixed(0)}`);
      vents++;
    } else if (!OLD) assert.equal(report.vents.length, 0, `${asset} LOD${lod}: no vent where none was found open (${report.vents.map((v) => v.mesh)})`);
  }
  if (res.length) lines.push(`${asset}: ${res.join(', ')} mm2`);
}
for (const l of lines) console.log(l);
if (failures.length) {
  for (const f of failures) console.log(`FAIL ${f}`);
  assert.fail(`${failures.length} coat faults${OLD ? ' (the exports as drawn, COAT_OLD=1)' : ''}`);
}
assert(pits >= 60, `sleeved bodies and levels measured: ${pits}`);
assert.equal(vents, VENTED.length * 4, `vented coats measured at every level`);
// Wired into humans.js's parse, before the waist (fitWaist stays straight before engraveSilver).
{
  const humans = await fs.readFile(process.env.HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fitCoats \} from '\.\/human-coat\.js';/.test(humans), 'humans.js imports fitCoats');
  assert(/const gltf = await loader\.parseAsync\(.*\);(?:(?!return gltf)[\s\S]){0,1200}fitCoats\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,400}fitWaist\(gltf\.scene\);\s*engraveSilver\(gltf\.scene\);\s*return gltf;/.test(humans), 'parse() fits the coats of the shared source, before the waist');
}
console.log(`human-coat: ${pits} sleeved body levels closed at the armpit, ${vents} vents lapped, standing and walking: PASS`);
