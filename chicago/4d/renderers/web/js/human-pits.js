// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-pits.js — the cloth in the pit of the arm folds in under the arm (T-3553, round 7).
 *
 * Every body is modelled with its arms held out from its sides, and each point of its clothes
 * follows the bones it is weighted to. In the pit of the arm the cloth is weighted part to the
 * arm and part to the chest, and when the arm comes down to the side that band of cloth is
 * squeezed between the two: the sleeve's front and the side of the coat cross each other in
 * front of the arm, and the eye sees a torn, dark notch there (the 1904 coachman's livery coat
 * showed it most; Kevin, 2026-11-26: "Armpit is bad").
 *
 * Here every piece of clothing, and the body's skin under it, is posed where the figure holds
 * its arms (the body's own idle and walk, POSES points of each, averaged), and the cloth in each
 * pit (from PIT.from below the shoulder joint, within PIT.reach of it, on the chest's side of
 * the arm, PIT.outer) is tucked in towards the chest, level, by up to PIT.tuck where it is
 * weighted evenly to arm and chest and by less where it is weighted more to one: the sleeve and
 * the coat then meet in a fold under the arm, as cloth does, instead of crossing in front of it.
 * The tuck is carried back to the bind pose through each point's own blend of bones, so it
 * holds as the arm swings. Every layer is tucked by the same rule, so a shirt and the skin
 * under a sleeve go in with it, and a waistcoat under a coat's sleeve; a waistcoat with no
 * sleeve over it keeps its armholes as cut. Positions (and the normals round them) only; no point, face or
 * draw call is added, and weights are not changed.
 *
 * Runs once per loaded body at every level, after layOver and before bindLayers and cullHidden.
 * Returns { tucked: [{ mesh, points, max }] } on root.userData.chicagoPits.
 */
import { kit, layerRank } from './human-drape.js';

/** Points along each clip the figure is posed at. */
export const POSES = 4;
/** The pit of the arm, for an adult (scaled by the shoulders' width): cloth from `from` below
 * the shoulder joint, fully by `full`, within `reach` of it and no further than `outer` out
 * from it on the arm's outer side, is tucked in by up to `tuck`. */
export const PIT = Object.freeze({ from: 0.02, full: 0.06, reach: 0.12, outer: 0.07, tuck: 0.05 });
const ADULT_SHOULDERS_M = 0.4;
const LOOK = /^(garment_(upper|lower|outer)|accessory|footwear)__/;
const ARM = /^(upperarm|lowerarm|hand)_([lr])$/, TORSO = /^(spine|clavicle|neck|pelvis)/;
const smooth = (x) => { const t = Math.max(0, Math.min(1, x)); return t * t * (3 - 2 * t); };

/** Bone matrices (bone world × bone inverse) in each sampled pose, and each bone's mean place. */
function posesOf(root, skeleton, clips, THREE) {
  const mats = [], joints = new Map(), v = new THREE.Vector3();
  const bones = skeleton.bones, keep = bones.map((b) => [b.position.clone(), b.quaternion.clone(), b.scale.clone()]);
  const restore = () => { bones.forEach((b, i) => { b.position.copy(keep[i][0]); b.quaternion.copy(keep[i][1]); b.scale.copy(keep[i][2]); }); root.updateMatrixWorld(true); };
  const byName = new Map(bones.map((b) => [b.name, b]));
  for (const clip of clips) {
    if (!/(^|_)(idle|walk)/i.test(clip.name)) continue;
    const tracks = clip.tracks.map((t) => {
      const dot = t.name.lastIndexOf('.'), bone = byName.get(t.name.slice(0, dot)), prop = t.name.slice(dot + 1);
      return bone && /^(position|quaternion|scale)$/.test(prop) ? { bone, prop, it: t.createInterpolant() } : null;
    }).filter(Boolean);
    if (!tracks.length) continue;
    for (let k = 0; k < POSES; k++) {
      restore();
      for (const { bone, prop, it } of tracks) bone[prop].fromArray(it.evaluate((k + 0.5) / POSES * clip.duration));
      root.updateMatrixWorld(true);
      mats.push(bones.map((b, i) => new THREE.Matrix4().multiplyMatrices(b.matrixWorld, skeleton.boneInverses[i]).elements.slice()));
      for (const b of bones) (joints.get(b.name) ?? joints.set(b.name, new THREE.Vector3()).get(b.name)).add(v.setFromMatrixPosition(b.matrixWorld));
    }
  }
  restore();
  for (const j of joints.values()) j.divideScalar(Math.max(1, mats.length));
  return { mats, joints };
}

export function* tuckPitsSteps(root, clips = [], THREE = null) {
  clips ??= [];
  const report = { tucked: [] };
  if (!root || !THREE || !clips.length) return report;
  const meshes = [];
  root.traverse((o) => {
    if (!o.isSkinnedMesh || !o.geometry?.index || !o.geometry.attributes.skinWeight) return;
    if (o.material?.name === 'skin' || (LOOK.test(o.material?.name ?? '') && layerRank(o) >= 1)) meshes.push(o);
  });
  if (!meshes.length) return report;
  const sk = meshes[0].skeleton;
  const { mats: poses, joints } = posesOf(root, sk, clips, THREE);
  const J = (n) => joints.get(n);
  const spine = J('spine_03'), neck = J('neck_01'), pelvis = J('pelvis'), shoulders = { l: J('upperarm_l'), r: J('upperarm_r') };
  if (!poses.length || !spine || !neck || !pelvis || !shoulders.l || !shoulders.r) return report;
  const up = neck.clone().sub(pelvis).normalize(), scale = shoulders.l.distanceTo(shoulders.r) / ADULT_SHOULDERS_M;
  // level, from each shoulder joint in towards the spine
  const level = (x, y, z) => { const h = x * up.x + y * up.y + z * up.z; return [x - h * up.x, y - h * up.y, z - h * up.z]; };
  const inward = {};
  for (const s of ['l', 'r']) { const d = level(spine.x - shoulders[s].x, spine.y - shoulders[s].y, spine.z - shoulders[s].z), L = Math.hypot(...d) || 1; inward[s] = d.map((x) => x / L); }
  const armOf = sk.bones.map((b) => ARM.exec(b.name)?.[2] ?? null), torso = sk.bones.map((b) => TORSO.test(b.name));
  const m3 = new THREE.Matrix3(), v = new THREE.Vector3();
  // A piece with sleeves (some point all on the arm) is tucked; a piece without (a waistcoat) only
  // when a sleeved piece is worn over it, which takes it in with it; the skin always.
  const sleeved = (m) => {
    const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight;
    for (let i = 0; i < sw.count; i++) { let a = 0; for (let q = 0; q < 4; q++) if (armOf[si.getComponent(i, q)]) a += sw.getComponent(i, q); if (a > 0.97) return true; }
    return false;
  };
  const sleeves = new Map(meshes.map((m) => [m, m.material?.name !== 'skin' && sleeved(m)]));
  const outerSleeve = Math.max(-1, ...meshes.filter((m) => sleeves.get(m)).map((m) => layerRank(m)));
  yield;
  for (const mesh of meshes) {
    if (mesh.skeleton.bones.some((b, i) => sk.bones[i] !== b)) continue;
    if (mesh.material?.name !== 'skin' && !sleeves.get(mesh) && !(layerRank(mesh) < outerSleeve)) continue;
    const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
    const W = kit.weldMeshes([mesh]), G = W.G, moved = [];
    let max = 0;
    yield;
    for (let g = 0; g < G; g++) {
      if ((g & 2047) === 2047) yield;
      const i = W.members[g][0][1];
      let arm = 0, tot = 0, side = null;
      for (let q = 0; q < 4; q++) {
        const w = sw.getComponent(i, q), b = si.getComponent(i, q);
        if (!(w > 0)) continue;
        if (armOf[b]) { arm += w; tot += w; side = armOf[b]; } else if (torso[b]) tot += w;
      }
      if (!side) continue;
      const share = arm / tot; if (!(share > 0.05 && share < 0.95)) continue;
      // where the figure holds the point: its own blend of bones, averaged over the poses
      const M = new Float64Array(12);
      for (const B of poses) for (let q = 0; q < 4; q++) {
        const w = sw.getComponent(i, q); if (!(w > 0)) continue;
        const e = B[si.getComponent(i, q)], f = w / poses.length;
        for (let c = 0; c < 4; c++) for (let r = 0; r < 3; r++) M[c * 3 + r] += f * e[c * 4 + r];
      }
      const x = W.P[g * 3], y = W.P[g * 3 + 1], z = W.P[g * 3 + 2];
      const qx = M[0] * x + M[3] * y + M[6] * z + M[9], qy = M[1] * x + M[4] * y + M[7] * z + M[10], qz = M[2] * x + M[5] * y + M[8] * z + M[11];
      const jt = shoulders[side], dx = qx - jt.x, dy = qy - jt.y, dz = qz - jt.z, n = inward[side];
      const below = -(dx * up.x + dy * up.y + dz * up.z), far = Math.hypot(dx, dy, dz), inn = dx * n[0] + dy * n[1] + dz * n[2];
      const k = 4 * share * (1 - share)
        * smooth((below - PIT.from * scale) / ((PIT.full - PIT.from) * scale))
        * (1 - smooth((far - PIT.reach * scale) / (0.04 * scale)))
        * smooth((inn + PIT.outer * scale) / (PIT.outer * scale));
      if (!(k > 1e-3)) continue;
      const d = PIT.tuck * scale * k;
      m3.set(M[0], M[3], M[6], M[1], M[4], M[7], M[2], M[5], M[8]).invert();
      v.set(qx + n[0] * d - M[9], qy + n[1] * d - M[10], qz + n[2] * d - M[11]).applyMatrix3(m3);
      W.P[g * 3] = v.x; W.P[g * 3 + 1] = v.y; W.P[g * 3 + 2] = v.z;
      moved.push(g); max = Math.max(max, d);
    }
    if (!moved.length) continue;
    // write the moved points back, with normals from the cloth round them
    const pos = mesh.geometry.attributes.position, nrm = mesh.geometry.attributes.normal;
    const Binv = mesh.bindMatrix.clone().invert(), nBack = new THREE.Matrix3().getNormalMatrix(Binv);
    const clampN = pos.normalized ? (x) => Math.max(-1, Math.min(1, x)) : (x) => x;
    const N = kit.graphNormals(W.P, W.tris, G);
    for (const g of moved) for (const [, i] of W.members[g]) {
      v.set(W.P[g * 3], W.P[g * 3 + 1], W.P[g * 3 + 2]).applyMatrix4(Binv); pos.setXYZ(i, clampN(v.x), clampN(v.y), clampN(v.z));
      if (nrm) { v.set(N[g * 3], N[g * 3 + 1], N[g * 3 + 2]).applyMatrix3(nBack).normalize(); nrm.setXYZ(i, v.x, v.y, v.z); }
    }
    pos.needsUpdate = true; if (nrm) nrm.needsUpdate = true;
    mesh.geometry.computeBoundingSphere(); mesh.geometry.computeBoundingBox();
    report.tucked.push({ mesh: mesh.name, points: moved.length, max: +max.toFixed(4) });
    yield;
  }
  root.userData.chicagoPits = report;
  return report;
}

export const tuckPits = (root, clips, THREE) => { const s = tuckPitsSteps(root, clips, THREE); for (;;) { const n = s.next(); if (n.done) return n.value; } };
