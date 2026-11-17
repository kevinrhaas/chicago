// SPDX-License-Identifier: GPL-3.0-or-later
// Sleeves, cuffs and gloves in motion (renderers/web/js/human-sleeve.js, T-3553: "No clothing
// breaks through in motion. Check walking and turning poses, not only standing: ... the
// soldiers' stripes and trim on bending sleeves"). On the real exports, on the CPU, every body
// at every level, in six arm poses (standing; the walk's arm forward and back, the wrist
// trailing; the elbow at 90; a carry at 120; a hand raised), before and after:
//
//   - every sleeve's hem at the wrist lies on its own line (no tooth further than TOOTH_M off
//     it plus a millimetre, LOD0 and LOD1; never worse than drawn further out) and turns as
//     one band (one set of weights round it);
//   - looking into a sleeve's mouth past a glove that ends in it, the bare skin seen is gone
//     but for slivers at grazing lines of sight (SKIN_LEFT of what was drawn, LOD0 and LOD1;
//     never more than drawn further out);
//   - nothing comes through anything on the forearm and elbow that did not before: for every
//     pair of pieces there (skin under cloth, cloth under cloth: a cuff facing on its coat
//     sleeve, a glove under a sleeve), what comes through and can be seen is never more nor
//     deeper than drawn; pieces drawn joined (a cuff to its sleeve) stay joined; and the
//     1812 soldiers' and officers' cuff facings never come through or part from their
//     sleeves at all;
//   - topology and UVs are kept, positions move only at a hem's edge and a glove's top, and
//     the fit runs once per loaded body.
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
// SLEEVE_MODULE: another copy of the module (only to show this test fails on the old code).
const modulePath = process.env.SLEEVE_MODULE ?? new URL('renderers/web/js/human-sleeve.js', here);
const { fitSleeves, isCloth, TOOTH_M, MAX_TOOTH_M, EXTEND_M, MAX_EASE_M } = await import(data((await fs.readFile(modulePath, 'utf8')).replace("from 'three'", `from '${three}'`)));

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
async function load(asset, lod) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  gltf.scene.updateMatrixWorld(true);
  return gltf;
}

// ---- posing -----------------------------------------------------------------------------
const DEG = Math.PI / 180;
const rigOf = (scene) => { const b = {}; scene.traverse(o => { if (o.isBone) b[o.name] = o; }); return b; };
function figure(b) {
  const w = n => b[n].getWorldPosition(new THREE.Vector3());
  const O = w('thigh_l').add(w('thigh_r')).multiplyScalar(0.5);
  const U = O.clone().sub(w('foot_l').add(w('foot_r')).multiplyScalar(0.5)).normalize();
  const L = w('thigh_l').sub(w('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize();
  return { U, L, F: new THREE.Vector3().crossVectors(L, U).normalize() };
}
function aim(bone, child, dir) {
  bone.updateWorldMatrix(true, true);
  const a = bone.getWorldPosition(new THREE.Vector3()), c = child.getWorldPosition(new THREE.Vector3());
  const q = new THREE.Quaternion().setFromUnitVectors(c.sub(a).normalize(), dir.clone().normalize());
  const pq = bone.parent.getWorldQuaternion(new THREE.Quaternion());
  bone.quaternion.copy(pq.clone().invert().multiply(pq.multiply(bone.quaternion).premultiply(q)));
  bone.updateWorldMatrix(false, true);
}
/** Both arms as human-actions.js swings them: the upper arm `th` forward of hanging, the elbow
 * bent `elbow` about the figure's right, the hand `wrist` on from the forearm. */
export const POSES = {
  stand: { th: 0, elbow: 15, wrist: 0 },
  walk_front: { th: 25, elbow: 50, wrist: 12 },
  walk_back: { th: -25, elbow: 20, wrist: -14 },
  bend90: { th: 10, elbow: 90, wrist: 0 },
  carry120: { th: 20, elbow: 120, wrist: 15 },
  raised: { th: 70, elbow: 100, wrist: 0 },
};
function pose(scene, P) {
  rest(scene);
  const b = rigOf(scene); scene.updateMatrixWorld(true);
  const fr = figure(b);
  for (const s of ['l', 'r']) {
    const sx = s === 'l' ? 1 : -1;
    const up = fr.U.clone().multiplyScalar(-Math.cos(P.th * DEG)).addScaledVector(fr.F, Math.sin(P.th * DEG)).addScaledVector(fr.L, sx * 0.075).normalize();
    const bend = fr.L.clone().negate().addScaledVector(up, up.dot(fr.L)).normalize();
    const fore = up.clone().applyAxisAngle(bend, P.elbow * DEG).addScaledVector(fr.L, sx * 0.03).normalize();
    aim(b[`upperarm_${s}`], b[`lowerarm_${s}`], up);
    aim(b[`lowerarm_${s}`], b[`hand_${s}`], fore);
    aim(b[`hand_${s}`], b[`middle_01_${s}`], fore.clone().applyAxisAngle(bend, P.wrist * DEG));
  }
  scene.updateMatrixWorld(true);
}
function rest(scene) {
  if (!scene.userData.__rest) return; scene.traverse(o => { if (o.isBone && o.userData.__q0) o.quaternion.copy(o.userData.__q0); }); scene.updateMatrixWorld(true); }
function keepRest(scene) { scene.userData.__rest = true; scene.traverse(o => { if (o.isBone) o.userData.__q0 = o.quaternion.clone(); }); }

// ---- reading the meshes -----------------------------------------------------------------
const matName = m => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const pieceOf = (m, asset) => m.name.replace(`${asset}_`, '').replace(/_lod\d*$/, '');
function posed(mesh) {
  const p = mesh.geometry.attributes.position, out = new Array(p.count);
  for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3(); mesh.getVertexPosition(i, v); out[i] = v.applyMatrix4(mesh.matrixWorld); }
  return out;
}
/** Bind-pose positions (metres): the pose the skin weights were made in (a GLB's rest pose
 * need not be it). */
function bindPos(mesh) {
  const p = mesh.geometry.attributes.position, out = new Array(p.count);
  for (let i = 0; i < p.count; i++) out[i] = new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(mesh.bindMatrix);
  return out;
}
const ARM_BONE = /^(upperarm|lowerarm|hand|(?:thumb|index|middle|ring|pinky)_\d+)_([lr])$/;
function sides(mesh) {
  const names = mesh.skeleton.bones.map(b => b.name), si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  const side = names.map(n => n.match(ARM_BONE)?.[2] ?? null), finger = names.map(n => /^(thumb|index|middle|ring|pinky)_/.test(n));
  const out = [], fing = [];
  for (let i = 0; i < si.count; i++) {
    let l = 0, r = 0, f = 0;
    for (let k = 0; k < 4; k++) { const b = si.getComponent(i, k), w = sw.getComponent(i, k); if (side[b] === 'l') l += w; else if (side[b] === 'r') r += w; if (finger[b]) f += w; }
    out.push(l > 0.5 ? 'l' : r > 0.5 ? 'r' : null); fing.push(f > 0.3);
  }
  return { side: out, finger: fing };
}
/** Welded open-edge loops of a mesh (index lists of one vertex per welded point). */
function openLoops(mesh, P) {
  const idx = mesh.geometry.index, key = p => `${Math.round(p.x * 2e4)},${Math.round(p.y * 2e4)},${Math.round(p.z * 2e4)}`;
  const gid = new Map(), groupOf = P.map(p => { const k = key(p); if (!gid.has(k)) gid.set(k, gid.size); return gid.get(k); });
  const rep = new Map(); groupOf.forEach((g, i) => { if (!rep.has(g)) rep.set(g, i); });
  const E = new Map();
  for (let t = 0; t < idx.count / 3; t++) for (let c = 0; c < 3; c++) {
    const a = groupOf[idx.getX(t * 3 + c)], b = groupOf[idx.getX(t * 3 + (c + 1) % 3)];
    if (a === b) continue; const k = a < b ? `${a},${b}` : `${b},${a}`; E.set(k, (E.get(k) ?? 0) + 1);
  }
  const link = new Map();
  for (const [k, c] of E) if (c === 1) { const [a, b] = k.split(',').map(Number); for (const [x, y] of [[a, b], [b, a]]) { if (!link.has(x)) link.set(x, []); link.get(x).push(y); } }
  const seen = new Set(), loops = [];
  for (const g0 of link.keys()) {
    if (seen.has(g0)) continue;
    const loop = [g0]; seen.add(g0);
    for (let k = 0; k < loop.length; k++) for (const o of link.get(loop[k])) if (!seen.has(o)) { seen.add(o); loop.push(o); }
    loops.push(loop.map(g => rep.get(g)));
  }
  return loops;
}
/** The arm at bind (from boneInverses) and now (from the bones). */
function armAt(mesh, s, now) {
  const sk = mesh.skeleton, ix = new Map(sk.bones.map((b, i) => [b.name, i]));
  const at = n => now ? sk.bones[ix.get(n)].getWorldPosition(new THREE.Vector3()) : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[ix.get(n)].clone().invert());
  const S = at(`upperarm_${s}`), E = at(`lowerarm_${s}`), W = at(`hand_${s}`);
  return { E, W, fore: W.clone().sub(E).normalize(), len: E.distanceTo(W), scale: (S.distanceTo(E) + E.distanceTo(W)) / 0.54 };
}
const tOf = (a, p) => p.clone().sub(a.E).dot(a.fore);
/** Each sleeve's hem at each wrist: the open loop on the forearm nearest the hand, going round. */
function hems(mesh, bindP, sd) {
  const out = [];
  if (sd.finger.some(Boolean)) return out;
  const loops = openLoops(mesh, bindP);
  for (const s of ['l', 'r']) {
    const a = armAt(mesh, s, false);
    let best = null;
    for (const loop of loops) {
      const pts = loop.filter(i => sd.side[i] === s && Math.abs(tOf(a, bindP[i]) - a.len) <= 0.07 * a.scale && tOf(a, bindP[i]) > a.len * 0.5);
      if (pts.length < 6 || pts.length < 0.8 * loop.length) continue;
      const ts = pts.map(i => tOf(a, bindP[i]));
      const m = ts.reduce((x, y) => x + y, 0) / ts.length;
      if (!best || m > best.t) best = { s, t: m, lo: Math.min(...ts), pts };
    }
    if (best) out.push(best);
  }
  return out;
}
/** How far the hem's points lie off its own line now (the largest, metres): t fitted as
 * a + b cos + c sin of the angle round the forearm. */
function ragged(P, hem, a) {
  const u = new THREE.Vector3(0, 1, 0).addScaledVector(a.fore, -a.fore.y); if (u.lengthSq() < 1e-6) u.set(0, 0, 1).addScaledVector(a.fore, -a.fore.z); u.normalize();
  const w = new THREE.Vector3().crossVectors(a.fore, u);
  const pts = hem.pts.map(i => { const r = P[i].clone().sub(a.E); const t = r.dot(a.fore); r.addScaledVector(a.fore, -t); return { th: Math.atan2(r.dot(w), r.dot(u)), t }; });
  const A = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], y = [0, 0, 0];
  for (const p of pts) { const r = [1, Math.cos(p.th), Math.sin(p.th)]; for (let i = 0; i < 3; i++) { y[i] += r[i] * p.t; for (let j = 0; j < 3; j++) A[i][j] += r[i] * r[j]; } }
  const det = M => M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0]) + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]);
  const D = det(A), c = [0, 1, 2].map(k => det(A.map((row, i) => row.map((x, j) => (j === k ? y[i] : x)))) / D);
  return Math.max(...pts.map(p => Math.abs(p.t - (c[0] + c[1] * Math.cos(p.th) + c[2] * Math.sin(p.th)))));
}
function handSpread(mesh, hem) {
  const names = mesh.skeleton.bones.map(b => b.name), si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  const hs = hem.pts.map(i => { let h = 0; for (let k = 0; k < 4; k++) if (names[si.getComponent(i, k)] === `hand_${hem.s}`) h += sw.getComponent(i, k); return h; });
  return Math.max(...hs) - Math.min(...hs);
}

// ---- surfaces and rays ------------------------------------------------------------------
const _ab = new THREE.Vector3(), _ac = new THREE.Vector3(), _ap = new THREE.Vector3(), _bp = new THREE.Vector3(), _cp = new THREE.Vector3();
function closestOnTri(p, a, b, c, out) {
  _ab.subVectors(b, a); _ac.subVectors(c, a); _ap.subVectors(p, a);
  const d1 = _ab.dot(_ap), d2 = _ac.dot(_ap); if (d1 <= 0 && d2 <= 0) return out.copy(a);
  _bp.subVectors(p, b); const d3 = _ab.dot(_bp), d4 = _ac.dot(_bp); if (d3 >= 0 && d4 <= d3) return out.copy(b);
  const vc = d1 * d4 - d3 * d2; if (vc <= 0 && d1 >= 0 && d3 <= 0) return out.copy(a).addScaledVector(_ab, d1 / (d1 - d3));
  _cp.subVectors(p, c); const d5 = _ab.dot(_cp), d6 = _ac.dot(_cp); if (d6 >= 0 && d5 <= d6) return out.copy(c);
  const vb = d5 * d2 - d1 * d6; if (vb <= 0 && d2 >= 0 && d6 <= 0) return out.copy(a).addScaledVector(_ac, d2 / (d2 - d6));
  const va = d3 * d6 - d5 * d4; if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) return out.copy(b).addScaledVector(_cp.subVectors(c, b), (d4 - d3) / ((d4 - d3) + (d5 - d6)));
  const den = 1 / (va + vb + vc); return out.copy(a).addScaledVector(_ab, vb * den).addScaledVector(_ac, vc * den);
}
const triList = (mesh, keep) => { const idx = mesh.geometry.index, T = []; for (let t = 0; t < idx.count / 3; t++) { const q = [idx.getX(t * 3), idx.getX(t * 3 + 1), idx.getX(t * 3 + 2)]; if (keep(q, t)) T.push(q); } return T; };
/** Closest-point queries over triangles T of positions P; signed by winding times `sign`. */
function surface(P, T, sign, cell = 0.02) {
  const grid = new Map(), key = (x, y, z) => `${x},${y},${z}`;
  T.forEach((q, k) => {
    const lo = [0, 1, 2].map(d => Math.floor(Math.min(...q.map(i => P[i].getComponent(d))) / cell)), hi = [0, 1, 2].map(d => Math.floor(Math.max(...q.map(i => P[i].getComponent(d))) / cell));
    for (let x = lo[0]; x <= hi[0]; x++) for (let y = lo[1]; y <= hi[1]; y++) for (let z = lo[2]; z <= hi[2]; z++) { const kk = key(x, y, z); if (!grid.has(kk)) grid.set(kk, []); grid.get(kk).push(k); }
  });
  const q = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  return (p, reach) => {
    let bd = reach * reach, bt = -1; const best = new THREE.Vector3(), r = Math.ceil(reach / cell), seen = new Set();
    const cx = Math.floor(p.x / cell), cy = Math.floor(p.y / cell), cz = Math.floor(p.z / cell);
    for (let x = cx - r; x <= cx + r; x++) for (let y = cy - r; y <= cy + r; y++) for (let z = cz - r; z <= cz + r; z++) {
      for (const k of grid.get(key(x, y, z)) ?? []) { if (seen.has(k)) continue; seen.add(k); const [a, b, c] = T[k]; closestOnTri(p, P[a], P[b], P[c], q); const d = q.distanceToSquared(p); if (d < bd) { bd = d; bt = k; best.copy(q); } }
    }
    if (bt < 0) return null;
    const [a, b, c] = T[bt]; const n = e1.subVectors(P[b], P[a]).cross(e2.subVectors(P[c], P[a])).normalize();
    return { d: sign * Math.sign(n.dot(e1.subVectors(p, best)) || 1) * Math.sqrt(bd), at: best.clone() };
  };
}
function rays(list) {
  const F = [];
  for (const { P, T } of list) for (const [a, b, c] of T) F.push(P[a], P[b], P[c]);
  const e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), p = new THREE.Vector3(), s = new THREE.Vector3(), q = new THREE.Vector3();
  return (o, d, maxT) => {
    for (let k = 0; k < F.length; k += 3) {
      e1.subVectors(F[k + 1], F[k]); e2.subVectors(F[k + 2], F[k]); p.crossVectors(d, e2);
      const det = e1.dot(p); if (Math.abs(det) < 1e-12) continue;
      const inv = 1 / det; s.subVectors(o, F[k]); const u = s.dot(p) * inv; if (u < 0 || u > 1) continue;
      q.crossVectors(s, e1); const v = d.dot(q) * inv; if (v < 0 || u + v > 1) continue;
      const t = e2.dot(q) * inv; if (t > 1e-4 && t < maxT) return true;
    }
    return false;
  };
}
/** The winding's outward sign (against the asset's normals) and, per triangle, whether it
 * faces away from the arm's bones (a sleeve's or a cuff's outer wall, not its lining). */
function walls(mesh, P, arms) {
  const idx = mesh.geometry.index, nrm = mesh.geometry.attributes.normal, e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  let agree = 0;
  for (let t = 0; t < idx.count / 3; t += 2) { const [a, b, c] = [0, 1, 2].map(k => idx.getX(t * 3 + k)); agree += Math.sign(e1.subVectors(P[b], P[a]).cross(e2.subVectors(P[c], P[a])).dot(new THREE.Vector3().fromBufferAttribute(nrm, a))); }
  const sign = agree < 0 ? -1 : 1, out = new Uint8Array(idx.count / 3), m = new THREE.Vector3();
  const segs = []; for (const s of ['l', 'r']) { const J = arms[s]; for (let k = 0; k + 1 < J.length; k++) segs.push([J[k], J[k + 1]]); }
  for (let t = 0; t < idx.count / 3; t++) {
    const [a, b, c] = [0, 1, 2].map(k => idx.getX(t * 3 + k));
    m.copy(P[a]).add(P[b]).add(P[c]).multiplyScalar(1 / 3);
    const n = e1.subVectors(P[b], P[a]).cross(e2.subVectors(P[c], P[a])).multiplyScalar(sign);
    let bd = Infinity, rad = null;
    for (const [p0, p1] of segs) { const d = p1.clone().sub(p0), tt = Math.max(0, Math.min(1, m.clone().sub(p0).dot(d) / d.lengthSq())), cp = p0.clone().addScaledVector(d, tt), dd = m.distanceToSquared(cp); if (dd < bd) { bd = dd; rad = m.clone().sub(cp); } }
    out[t] = rad && n.dot(rad) > 0 ? 1 : 0;
  }
  return { sign, outer: out };
}

/**
 * One body at one level, posed: what comes through what on the forearm and elbow, seen.
 * `cov` (the pairs and the points of each the other covers at bind) is taken once, on the
 * scene as drawn; it is read the same way before and after.
 */
function coverage(scene, asset) {
  const pieces = [];
  scene.traverse(o => { if (o.isSkinnedMesh && /^(garment|accessory|skin)/.test(matName(o)) && !/eyes|hair/.test(o.name)) pieces.push(o); });
  const b = rigOf(scene), wp = n => b[n].getWorldPosition(new THREE.Vector3());
  const arms = { l: ['upperarm_l', 'lowerarm_l', 'hand_l', 'middle_01_l'].map(wp), r: ['upperarm_r', 'lowerarm_r', 'hand_r', 'middle_01_r'].map(wp) };
  const info = pieces.map(m => { const P = posed(m), sd = sides(m); return { m, P, sd, name: pieceOf(m, asset), w: walls(m, P, arms) }; }).filter(x => x.sd.side.some(Boolean));
  const zone = (x, i) => { const s = x.sd.side[i]; if (!s) return false; const a = armAt(x.m, s, true); return tOf(a, x.P[i]) >= -0.10 * a.scale; };
  const pairs = [];
  for (const I of info) for (const O of info) {
    if (I === O) continue;
    const T = triList(O.m, (q, t) => O.w.outer[t] && q.some(i => O.sd.side[i]));
    if (!T.length) continue;
    const near = surface(O.P, T, O.w.sign), cov = [];
    for (let i = 0; i < I.P.length; i++) { if (!zone(I, i)) continue; const q = near(I.P[i], 0.02); if (q && q.d < -1e-4) cov.push(i); }
    if (cov.length >= 3) pairs.push({ I: I.name, O: O.name, cov });
  }
  // Points drawn joined (a cuff's ring on its sleeve's), within half a millimetre at bind.
  const joins = [];
  for (const A of info) for (const B of info) {
    if (A.name >= B.name || /^body/.test(A.name) || /^body/.test(B.name)) continue;
    const list = [];
    for (let i = 0; i < A.P.length; i++) { if (!zone(A, i)) continue; for (let j = 0; j < B.P.length; j++) if (B.sd.side[j] && A.P[i].distanceToSquared(B.P[j]) < 2.5e-7) { list.push([i, j]); break; } }
    if (list.length >= 3) joins.push({ A: A.name, B: B.name, list });
  }
  return { pairs, joins };
}
function through(scene, asset, cov) {
  const byName = new Map();
  scene.traverse(o => { if (o.isSkinnedMesh) byName.set(pieceOf(o, asset), o); });
  const b = rigOf(scene), wp = n => b[n].getWorldPosition(new THREE.Vector3());
  const arms = { l: ['upperarm_l', 'lowerarm_l', 'hand_l', 'middle_01_l'].map(wp), r: ['upperarm_r', 'lowerarm_r', 'hand_r', 'middle_01_r'].map(wp) };
  const cache = new Map(), get = (n) => { if (!cache.has(n)) { const m = byName.get(n), P = posed(m), sd = sides(m); cache.set(n, { m, P, sd, w: walls(m, P, arms) }); } return cache.get(n); };
  const out = {};
  for (const { I, O, cov: pts } of cov.pairs) {
    const i0 = get(I), o0 = get(O);
    const near = surface(o0.P, triList(o0.m, (q, t) => o0.w.outer[t] && q.some(i => o0.sd.side[i])), o0.w.sign);
    const others = [];
    for (const n of byName.keys()) { if (n === I || /^body/.test(n)) continue; const x = byName.get(n); if (!(x.isSkinnedMesh && /^(garment|accessory)/.test(matName(x)))) continue; const g = get(n); others.push({ P: g.P, T: triList(g.m, q => q.some(i => g.sd.side[i])) }); }
    const seen = rays(others);
    let n = 0, worst = 0;
    for (const i of pts) {
      const q = near(i0.P[i], 0.04); if (!q || q.d <= 5e-4) continue;
      if (seen(i0.P[i], i0.P[i].clone().sub(q.at).normalize(), 0.08)) continue;
      n++; worst = Math.max(worst, q.d);
    }
    out[`${I}<${O}`] = { n, worst };
  }
  for (const { A, B, list } of cov.joins) {
    const a = get(A), c = get(B);
    out[`${A}|${B}`] = { gap: Math.max(...list.map(([i, j]) => a.P[i].distanceTo(c.P[j]))) };
  }
  return out;
}
/** Bare skin seen in a sleeve's mouth past a glove that ends in it: points of the body's
 * forearm inside the sleeve (not under the glove: within GLOVE_NEAR of it is the glove's to
 * show) that a visitor sees out through the mouth from one of VIEWS directions round the
 * figure, nothing of the sleeve, the glove or the body itself in the way. */
const GLOVE_NEAR = 0.004;
/** What may still be seen at LOD0 and LOD1, a share of what was drawn (slivers at the
 * mouth's very edge, at grazing lines of sight). */
const SKIN_LEFT = 0.15;
const VIEWS = [];
for (const el of [-25, 0, 20, 45]) for (let az = 0; az < 360; az += 30) VIEWS.push(new THREE.Vector3(Math.cos(el * DEG) * Math.cos(az * DEG), Math.sin(el * DEG), Math.cos(el * DEG) * Math.sin(az * DEG)));
function skinInMouth(scene, asset, sleeveHems) {
  let body = null; const cloth = [];
  scene.traverse(o => { if (!o.isSkinnedMesh) return; if (/^skin/.test(matName(o)) && /body/.test(o.name)) body = o; else if (/^(garment|accessory)/.test(matName(o))) cloth.push(o); });
  const gloves = cloth.filter(m => sides(m).finger.some(Boolean));
  if (!body || !gloves.length) return null;
  const B = posed(body), bs = sides(body);
  let n = 0;
  for (const { mesh, hem } of sleeveHems) {
    const P = posed(mesh), a = armAt(mesh, hem.s, true), ring = hem.pts.map(i => P[i]);
    const mouthT = Math.min(...ring.map(p => tOf(a, p)));
    const c = ring.reduce((m, p) => m.add(p), new THREE.Vector3()).divideScalar(ring.length);
    const glove = (m, Pm) => { const sd = sides(m); return { P: Pm, T: triList(m, q => q.some(i => sd.side[i] === hem.s && tOf(a, Pm[i]) > mouthT - 0.15 * a.scale)) }; };
    const near = (m, Pm) => ({ P: Pm, T: triList(m, q => q.some(i => Pm[i].distanceToSquared(c) < 0.0625)) });
    const G = gloves.map(m => glove(m, posed(m)));
    const onGlove = surface(G.flatMap(g => g.P), G.flatMap((g, k) => { const off = G.slice(0, k).reduce((x, y) => x + y.P.length, 0); return g.T.map(q => q.map(i => i + off)); }), 1);
    const mouthR = ring.reduce((m, p) => m + p.distanceTo(c), 0) / ring.length;
    const inSleeve = rays([{ P, T: triList(mesh, q => q.some(i => P[i].distanceToSquared(c) < 0.0625)) }]);
    // In the way: everything worn, and the body, within 25 cm of the sleeve's mouth.
    const blockers = rays([...cloth.map(m => near(m, m === mesh ? P : posed(m))), near(body, B)]);
    for (let i = 0; i < B.length; i++) {
      if (bs.side[i] !== hem.s) continue;
      const t = tOf(a, B[i]);
      if (t > mouthT - 0.003 || t < mouthT - 0.12 * a.scale) continue;
      if (onGlove(B[i], GLOVE_NEAR)) continue;
      // Inside the sleeve (straight out from the forearm the sleeve is met): skin outside it
      // is the through check's to count, not this one's.
      const out = B[i].clone().sub(a.E); out.addScaledVector(a.fore, -out.dot(a.fore));
      if (out.lengthSq() < 1e-10 || !inSleeve(B[i], out.normalize(), 0.06 * a.scale)) continue;
      // From the point toward the camera; the start nudged off the body's own surface.
      for (const v of VIEWS) {
        // Only a line of sight out through the mouth itself.
        const vf = v.dot(a.fore); if (vf < 1e-3) continue;
        const k = c.clone().sub(B[i]).dot(a.fore) / vf; if (k <= 0) continue;
        if (B[i].clone().addScaledVector(v, k).distanceTo(c) > mouthR) continue;
        if (!blockers(B[i].clone().addScaledVector(v, 0.002), v, 3)) { n++; break; }
      }
    }
  }
  return n;
}

// ---- the run ----------------------------------------------------------------------------
const ASSETS = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map(f => f.replace('.lod0.glb', '')).sort();
const ONLY = process.env.SLEEVE_ONLY ? new RegExp(process.env.SLEEVE_ONLY) : null;
const SOLDIER = /first_infantry_1812/;
const lines = [];
let hemsSeen = 0, glovesSeen = 0, soldierCuffs = 0;
for (const asset of ASSETS) {
  if (ONLY && !ONLY.test(asset)) continue;
  for (const lod of [0, 1, 2, 3]) {
    const before = await load(asset, lod), after = await load(asset, lod);
    const cloth = []; after.scene.traverse(o => { if (o.isSkinnedMesh && isCloth(o)) cloth.push(o); });
    const snap = cloth.map(m => ({ pos: m.geometry.attributes.position.array.slice(), uv: m.geometry.attributes.uv?.array.slice(), idx: m.geometry.index?.array.slice(), P: posed(m) }));
    const report = fitSleeves(after.scene);
    after.scene.updateMatrixWorld(true);
    // Topology and UVs kept; positions only at a hem's edge (along the arm, within
    // MAX_TOOTH_M) and a glove's top (within EXTEND_M and MAX_EASE_M).
    cloth.forEach((m, k) => {
      const s = snap[k], g = m.geometry;
      if (s.uv) assert.deepEqual(g.attributes.uv.array, s.uv, `${asset} LOD${lod} ${m.name}: UVs kept`);
      if (s.idx) assert.deepEqual(g.index.array, s.idx, `${asset} LOD${lod} ${m.name}: topology kept`);
      const P = posed(m), r = report.find(x => x.mesh === m.name && x.kind === 'glove'), sd = sides(m);
      for (let i = 0; i < P.length; i++) {
        const d = P[i].distanceTo(s.P[i]);
        if (d < 1e-5) continue;
        assert(sd.side[i], `${asset} LOD${lod} ${m.name}: a vertex off the arms moved ${(d * 1000).toFixed(1)} mm`);
        const a = armAt(m, sd.side[i], false);
        assert(d <= (r ? Math.hypot(EXTEND_M, MAX_EASE_M) : MAX_TOOTH_M) * a.scale + 1e-4, `${asset} LOD${lod} ${m.name}: a vertex moved ${(d * 1000).toFixed(1)} mm`);
      }
    });
    keepRest(before.scene); keepRest(after.scene);
    const res = [];
    // Hems.
    const hemList = [];
    for (const m of cloth) {
      const mb = before.scene.getObjectByName(m.name);
      const Pb = bindPos(mb), sd = sides(mb);
      for (const hem of hems(mb, Pb, sd)) hemList.push({ m, mb, hem });
    }
    let worst0 = 0, worst1 = 0, spread0 = 0, spread1 = 0;
    for (const P of Object.values(POSES)) {
      pose(before.scene, P); pose(after.scene, P);
      for (const { m, mb, hem } of hemList) {
        const r0 = ragged(posed(mb), hem, armAt(mb, hem.s, true)), r1 = ragged(posed(m), hem, armAt(m, hem.s, true));
        worst0 = Math.max(worst0, r0); worst1 = Math.max(worst1, r1);
        const a = armAt(m, hem.s, false);
        if (lod <= 1) assert(r1 <= (TOOTH_M + 0.001) * a.scale + 1e-4 || r1 <= r0 * 0.5, `${asset} LOD${lod} ${pieceOf(m, asset)}: the hem's edge lies ${(r1 * 1000).toFixed(1)} mm off its line (drawn ${(r0 * 1000).toFixed(1)})`);
        else assert(r1 <= r0 + 5e-4, `${asset} LOD${lod} ${pieceOf(m, asset)}: the hem's edge more ragged than drawn (${(r1 * 1000).toFixed(1)} mm, drawn ${(r0 * 1000).toFixed(1)})`);
      }
    }
    for (const { m, mb, hem } of hemList) {
      spread0 = Math.max(spread0, handSpread(mb, hem)); spread1 = Math.max(spread1, handSpread(m, hem));
      assert(handSpread(m, hem) <= 0.02, `${asset} LOD${lod} ${pieceOf(m, asset)}: its hem is not one band (hand weight ${handSpread(m, hem).toFixed(2)} apart round it)`);
      hemsSeen++;
    }
    if (hemList.length) res.push(`hems ${hemList.length}: edge ${(worst0 * 1000).toFixed(1)}→${(worst1 * 1000).toFixed(1)} mm off line, hand weight round it ${spread0.toFixed(2)}→${spread1.toFixed(2)}`);
    // Skin seen in a sleeve's mouth past a glove.
    const sleeveB = hemList.map(x => ({ mesh: x.mb, hem: x.hem })), sleeveA = hemList.map(x => ({ mesh: x.m, hem: x.hem }));
    let skin0 = 0, skin1 = 0, gl = false;
    for (const [name, P] of Object.entries(POSES)) {
      pose(before.scene, P); pose(after.scene, P);
      const s0 = skinInMouth(before.scene, asset, sleeveB), s1 = skinInMouth(after.scene, asset, sleeveA);
      if (s0 === null) break;
      gl = true; skin0 += s0; skin1 += s1;
      if (lod <= 1) assert(s1 <= SKIN_LEFT * s0, `${asset} LOD${lod} ${name}: ${s1} points of bare skin seen in a sleeve's mouth past the glove (drawn ${s0})`);
      else assert(s1 <= s0, `${asset} LOD${lod} ${name}: more bare skin seen in a sleeve's mouth than drawn (${s1}, drawn ${s0})`);
    }
    if (gl && sleeveB.length) { glovesSeen++; res.push(`skin seen past the glove ${skin0}→${skin1} points over the poses`); }
    // Nothing comes through on the forearm and elbow that did not before; joins stay joined.
    rest(before.scene); rest(after.scene);
    const cov = coverage(before.scene, asset);
    let more = 0, cuffs = 0;
    for (const [name, P] of Object.entries(POSES)) {
      pose(before.scene, P); pose(after.scene, P);
      const t0 = through(before.scene, asset, cov), t1 = through(after.scene, asset, cov);
      for (const [k, v1] of Object.entries(t1)) {
        const v0 = t0[k];
        if ('gap' in v1) {
          assert(v1.gap <= Math.max(v0.gap, 0.001) + 2e-4, `${asset} LOD${lod} ${name}: ${k} drawn joined part by ${(v1.gap * 1000).toFixed(1)} mm (drawn ${(v0.gap * 1000).toFixed(1)})`);
          if (SOLDIER.test(asset) && /cuffs/.test(k)) { assert(v1.gap <= 0.001, `${asset} LOD${lod} ${name}: the cuff facing parts from its sleeve by ${(v1.gap * 1000).toFixed(1)} mm`); cuffs++; }
          continue;
        }
        assert(v1.n <= v0.n + 1 && v1.worst <= Math.max(v0.worst, 0.002) + 5e-4, `${asset} LOD${lod} ${name}: ${k.replace('<', ' comes through ')} at ${v1.n} points, ${(v1.worst * 1000).toFixed(1)} mm (drawn ${v0.n}, ${(v0.worst * 1000).toFixed(1)} mm)`);
        if (v1.n > v0.n) more++;
        if (SOLDIER.test(asset) && /cuffs/.test(k) && !/^body/.test(k)) { assert.equal(v1.n, 0, `${asset} LOD${lod} ${name}: ${k} comes through at ${v1.n} points`); cuffs++; }
      }
    }
    if (SOLDIER.test(asset)) { soldierCuffs += cuffs; res.push(`cuff facings on their sleeves: ${cuffs} checks, none through or parted`); }
    // Once per loaded body.
    rest(after.scene);
    const held = cloth.map(m => m.geometry.attributes.position.array.slice());
    assert.equal(fitSleeves(after.scene), report, `${asset} LOD${lod}: the second call returns the first report`);
    cloth.forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, held[k], `${asset} LOD${lod} ${m.name}: a second call moved it`));
    if (res.length && (lod === 0 || process.env.SLEEVE_REPORT)) lines.push(`${asset} L${lod}: ${res.join('; ')}`);
  }
}
if (!ONLY) {
  assert(hemsSeen >= 50, `sleeve hems found: ${hemsSeen}`);
  assert(glovesSeen >= 2, `gloved sleeves found: ${glovesSeen}`);
  assert(soldierCuffs >= 90, `soldiers' cuff checks: ${soldierCuffs}`);
  // Wired into humans.js's parse, before any figure is cloned from it.
  const humans = await fs.readFile(process.env.SLEEVE_HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fitSleeves \} from '\.\/human-sleeve\.js';/.test(humans), 'humans.js imports fitSleeves');
  assert(/const gltf = await loader\.parseAsync\(.*\);[\s\S]{0,1200}fitSleeves\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,600}return gltf;/.test(humans), 'parse() fits the sleeves of the shared source');
}
for (const l of lines) console.log(l);
console.log(`${hemsSeen} sleeve hems, ${glovesSeen} gloved sleeves, ${soldierCuffs} soldiers' cuff checks over every body and level, six arm poses: nothing through, nothing parted: PASS`);
