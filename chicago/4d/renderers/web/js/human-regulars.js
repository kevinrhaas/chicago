// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-regulars.js — the 1812 private wears the regulars' coat, not the coatee (T-3553).
 *
 * Kevin, 2026-11-17, on the catalogue review that laid the private of Heald's company beside
 * Krimmel's Philadelphia volunteers: "i think against the regulars? they are probably closer
 * to a regular and would have been outfitted with uniform?". So the private is judged against
 * what the repo's record says the U.S. regular infantry wore before the change of spring 1813,
 * not against the volunteers' facings and gaiters. The record is text, not a picture: the
 * change printed in 1813 and 1814 (us_1814_military_laws_and_regulations) says "The coat of
 * the infantry and artillery shall be uniformly blue, no red collars or cuffs: and no lace
 * shall be worn by any grade ... all the rank and file will wear coatees. The button holes of
 * these will be trimmed with tape on the collar only." Read backwards (as the figure already
 * reads it for the red collar and cuffs, the felt cap and the feather), two things the
 * figure did not have follow from it, and both are built here as inferences, not as
 * anything a source describes:
 *
 * The skirts. "All the rank and file will wear coatees" says the earlier coat was not one.
 * The export cut the private's tails to mid-thigh (0.70 m off the ground), the coatee's
 * length: what the change brought in. Here, below the hips (PIVOT_BELOW_HIP_M under the hip
 * joints, where the tails already hang straight), each tail is drawn down so its hem sits
 * HEM_ABOVE_KNEE_M above the knee joint (about 0.56 m off the ground): longer than the coatee,
 * a hand short of the officer's skirts at the bend of the knee (officer_1812.json). That the
 * coat was longer is inferred; how much longer is reconstructed, and the silhouette follows
 * Ogden's 1888 plate of the older pattern (period context, not evidence for 1812). The tails
 * keep their own cut-away taper, their rows, UVs and skin weights; only positions below the
 * pivot move, straight down, and their normals are scaled to match.
 *
 * The tape. "Trimmed with tape on the collar only" says the earlier coat's button holes were
 * trimmed with tape beyond the collar, on the breast, where a single-breasted coat's holes
 * are. The figure had none. Here a white tape loop is laid on each of the eight breast button
 * holes, from the button toward the wearer's left (the button-hole side of a man's coat).
 * Their presence is inferred; their form, length (TAPE.breast), white colour and one-sided
 * loop are reconstructed. The collar's own loops are not drawn: the exported collar falls
 * to a centimetre or less at the front, where they would sit (a leftover, not a claim). The
 * loops are strips cast onto the coat's own surface, TAPE.breast.standoff off it, under the
 * crossbelts, and skinned with the cloth they lie on. They
 * are added to the crossbelts' mesh (the same white, the same skeleton), so no draw call,
 * material, texture or program is added.
 *
 * Which bodies: REGULARS names the asset. Every man of the 1812 garrison wears it (the 38
 * of data/humans/instances/1812, NCOs and musicians recoloured by dress_1812_garrison.json),
 * and so does every soldier of the 1835 garrison (data/humans/inside_1835.json, recoloured
 * all blue by tools/town_people_1835.py): for them the coatee IS right, so a scene dated
 * AFTER_YEAR or later leaves the asset as exported. A store with no scene (the tools' stages)
 * dresses it as the 1812 private it is named for.
 *
 * Once per parse, before any figure is cloned (about 35 ms at LOD0 in node, under 10 at the
 * far levels). tools/test_human_regulars.mjs
 * measures it on the real exports at every level, standing and walking. Liberty L-regulars-3553.
 */
import * as THREE from 'three';

/** The bodies dressed as the pre-1813 regulars, by asset id (the meshes' name prefix). */
export const REGULARS = Object.freeze(['private_first_infantry_1812']);
/** A scene of this year or later keeps the coatee (the change of 1813). */
export const AFTER_YEAR = 1813;
/** The tails are drawn down from this far under the hip joints, to this far above the knee joint. */
export const PIVOT_BELOW_HIP_M = 0.015, HEM_ABOVE_KNEE_M = 0.045;
/** A breast tape loop: length along the cloth from the button's centre, height, distance off it, points along it, and where it starts (under the button's rim). */
export const TAPE = Object.freeze({
  breast: Object.freeze({ length: 0.08, height: 0.014, standoff: 0.0012, points: 7, fromCentre: 0.0055 }),
});
const DONE = Symbol('regulars');

const piece = (mesh, asset, name) => new RegExp(`^${asset}_${name}_lod\\d+$`).test(mesh.name);

/** The year a scene id names, or null. */
export function sceneYear(sceneId) {
  const m = /(1[6-9]\d\d|20\d\d)/.exec(String(sceneId ?? ''));
  return m ? Number(m[1]) : null;
}

function bindJoint(mesh, name) {
  const sk = mesh.skeleton, i = sk.bones.findIndex((b) => b?.name === name);
  return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert());
}
function bindPositions(mesh) {
  const pos = mesh.geometry.attributes.position, n = pos.count, P = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}

/** Draw the tails down below the pivot so the hem is `hemY` (bind space). Returns metres added. */
function lengthenTails(tails, pivotY, hemY) {
  const P = bindPositions(tails), n = P.length / 3;
  let oldHem = Infinity; for (let i = 0; i < n; i++) oldHem = Math.min(oldHem, P[i * 3 + 1]);
  if (!(oldHem < pivotY) || oldHem <= hemY + 1e-4) return 0;
  const k = (pivotY - hemY) / (pivotY - oldHem);
  const pos = tails.geometry.attributes.position, nor = tails.geometry.attributes.normal;
  const inv = new THREE.Matrix4().copy(tails.bindMatrix).invert(), v = new THREE.Vector3();
  const nb = new THREE.Matrix3().getNormalMatrix(tails.bindMatrix), ni = new THREE.Matrix3().getNormalMatrix(inv), nv = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const y = P[i * 3 + 1];
    if (y >= pivotY) continue;
    v.set(P[i * 3], pivotY - (pivotY - y) * k, P[i * 3 + 2]).applyMatrix4(inv);
    pos.setXYZ(i, v.x, v.y, v.z);
    // A stretch by k in y: normals by the inverse transpose, (nx, ny / k, nz).
    if (nor) { nv.fromBufferAttribute(nor, i).applyMatrix3(nb); nv.y /= k; nv.normalize().applyMatrix3(ni).normalize(); nor.setXYZ(i, nv.x, nv.y, nv.z); }
  }
  pos.needsUpdate = true; if (nor) nor.needsUpdate = true;
  tails.geometry.computeBoundingBox(); tails.geometry.computeBoundingSphere();
  return oldHem - hemY;
}

/** A surface to cast onto: its bind positions and triangles. */
function surfaceOf(mesh) {
  return { mesh, P: bindPositions(mesh), idx: mesh.geometry.index ? mesh.geometry.index.array : Uint32Array.from({ length: mesh.geometry.attributes.position.count }, (_, i) => i) };
}
const ea = new THREE.Vector3(), eb = new THREE.Vector3(), pv = new THREE.Vector3(), tv = new THREE.Vector3(), qv = new THREE.Vector3();
const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
/**
 * The outermost hit of a horizontal ray from far outside at (angle, y) toward the axis
 * point (cx, y, cz): its point, the outward face normal, and the corner nearest it.
 * Angle 0 is straight ahead (+z), positive toward +x (the wearer's left).
 */
function cast(surf, cx, cz, angle, y) {
  const dir = new THREE.Vector3(-Math.sin(angle), 0, -Math.cos(angle));
  const o = new THREE.Vector3(cx, y, cz).addScaledVector(dir, -1);
  let best = null, bt = Infinity;
  const { P, idx } = surf;
  for (let t = 0; t < idx.length; t += 3) {
    const a = idx[t], b = idx[t + 1], c = idx[t + 2];
    const y0 = P[a * 3 + 1], y1 = P[b * 3 + 1], y2 = P[c * 3 + 1];
    if ((y0 > y && y1 > y && y2 > y) || (y0 < y && y1 < y && y2 < y)) continue;
    A.fromArray(P, a * 3); B.fromArray(P, b * 3); C.fromArray(P, c * 3);
    ea.subVectors(B, A); eb.subVectors(C, A); pv.crossVectors(dir, eb);
    const det = ea.dot(pv); if (Math.abs(det) < 1e-12) continue;
    const id = 1 / det; tv.subVectors(o, A);
    const u = tv.dot(pv) * id; if (u < 0 || u > 1) continue;
    qv.crossVectors(tv, ea); const w = dir.dot(qv) * id; if (w < 0 || u + w > 1) continue;
    const d = eb.dot(qv) * id; if (d <= 0 || d >= bt) continue;
    bt = d;
    const nrm = new THREE.Vector3().crossVectors(ea, eb).normalize(); if (nrm.dot(dir) > 0) nrm.negate();
    best = { point: o.clone().addScaledVector(dir, d), normal: nrm, corners: [a, b, c], bary: [1 - u - w, u, w] };
  }
  return best;
}

/** One tape loop: two rows of `points` along an arc of `length` from `angle0` toward `sign`, at height `y`. */
function tapeLoop(surf, cx, cz, y, angle0, sign, { length, height, standoff, points, fromCentre = 0 }) {
  const mid = cast(surf, cx, cz, angle0, y); if (!mid) return null;
  const r = Math.hypot(mid.point.x - cx, mid.point.z - cz); if (!(r > 0.01)) return null;
  // The loop starts under the button's rim, so the button shows at its end.
  angle0 += sign * fromCentre / r;
  const span = (length - fromCentre) / r, rows = [];
  for (const dy of [height / 2, -height / 2]) {
    const row = [];
    for (let j = 0; j < points; j++) {
      const h = cast(surf, cx, cz, angle0 + sign * span * j / (points - 1), y + dy);
      if (!h) return null;
      row.push({ p: h.point.addScaledVector(h.normal, standoff), n: h.normal, corners: h.corners, bary: h.bary });
    }
    rows.push(row);
  }
  return rows;
}

/** Append tape loops to `host` (the crossbelts), skinned as the cloth each point lies on. */
function appendLoops(host, loops) {
  const g = host.geometry, n0 = g.attributes.position.count;
  const add = loops.reduce((s, l) => s + l.rows[0].length * 2, 0);
  if (!add) return 0;
  const inv = new THREE.Matrix4().copy(host.bindMatrix).invert(), ni = new THREE.Matrix3().getNormalMatrix(inv);
  // Component by component: a loaded attribute may be interleaved (its array is the whole buffer).
  const GET = ['getX', 'getY', 'getZ', 'getW'], SET = ['setX', 'setY', 'setZ', 'setW'];
  const grow = (attr) => {
    const out = new THREE.BufferAttribute(new attr.array.constructor((n0 + add) * attr.itemSize), attr.itemSize, attr.normalized);
    for (let i = 0; i < n0; i++) for (let c = 0; c < attr.itemSize; c++) out[SET[c]](i, attr[GET[c]](i));
    return out;
  };
  const names = Object.keys(g.attributes), next = Object.fromEntries(names.map((k) => [k, grow(g.attributes[k])]));
  const sameBones = (m) => m.skeleton.bones.length === host.skeleton.bones.length && m.skeleton.bones.every((b, i) => b === host.skeleton.bones[i]);
  const boneOf = (m, j) => (sameBones(m) ? j : Math.max(0, host.skeleton.bones.findIndex((b) => b.name === m.skeleton.bones[j]?.name)));
  const tris = [], v = new THREE.Vector3();
  let k = n0;
  for (const { rows, under } of loops) {
    const ga = under.geometry.attributes, start = k, len = rows[0].length;
    for (const row of rows) for (const q of row) {
      v.copy(q.p).applyMatrix4(inv); next.position.setXYZ(k, v.x, v.y, v.z);
      if (next.normal) { v.copy(q.n).applyMatrix3(ni).normalize(); next.normal.setXYZ(k, v.x, v.y, v.z); }
      if (next.uv) next.uv.setXY(k, 0.5, 0.5);
      if (next.skinIndex && next.skinWeight && ga.skinIndex && ga.skinWeight) {
        // The cloth's weights where the point lies: its triangle's corners blended by the hit, the four largest kept.
        const sum = new Map();
        q.corners.forEach((v, t) => { for (let c = 0; c < 4; c++) { const wt = ga.skinWeight[GET[c]](v) * q.bary[t]; if (wt > 0) { const j = boneOf(under, ga.skinIndex[GET[c]](v)); sum.set(j, (sum.get(j) ?? 0) + wt); } } });
        const top = [...sum].sort((x, y) => y[1] - x[1]).slice(0, 4), total = top.reduce((s, e) => s + e[1], 0) || 1;
        for (let c = 0; c < 4; c++) { next.skinIndex[SET[c]](k, top[c]?.[0] ?? 0); next.skinWeight[SET[c]](k, (top[c]?.[1] ?? 0) / total); }
      }
      k++;
    }
    // Wound to face out: compare the first quad's normal with the cloth's.
    const p = (i) => new THREE.Vector3().fromBufferAttribute(next.position, i);
    const fn = new THREE.Vector3().crossVectors(p(start + 1).sub(p(start)), p(start + len).sub(p(start)));
    const out = fn.dot(new THREE.Vector3().copy(rows[0][0].n).applyMatrix3(ni)) > 0;
    for (let j = 0; j < len - 1; j++) {
      const a = start + j, b = a + 1, c = start + len + j, d = c + 1;
      if (out) tris.push(a, b, c, b, d, c); else tris.push(a, c, b, b, c, d);
    }
  }
  for (const name of names) g.setAttribute(name, next[name]);
  if (g.index) {
    const old = g.index.array, total = n0 + add, Arr = total > 65535 ? Uint32Array : old.constructor;
    const idx = new Arr(old.length + tris.length); idx.set(old); idx.set(tris, old.length);
    g.setIndex(new THREE.BufferAttribute(idx, 1));
  }
  g.computeBoundingBox(); g.computeBoundingSphere();
  return add;
}

/** The breast's button holes: the buttons' centres, bottom to top. */
function buttonCentres(buttons) {
  const P = bindPositions(buttons), n = P.length / 3, order = Array.from({ length: n }, (_, i) => i).sort((a, b) => P[a * 3 + 1] - P[b * 3 + 1]);
  const groups = [];
  for (const i of order) {
    const g = groups.at(-1);
    if (g && P[i * 3 + 1] - g.top < 0.012) { g.sum.add(new THREE.Vector3().fromArray(P, i * 3)); g.n++; g.top = P[i * 3 + 1]; } else groups.push({ sum: new THREE.Vector3().fromArray(P, i * 3), n: 1, top: P[i * 3 + 1] });
  }
  return groups.map((g) => g.sum.divideScalar(g.n));
}

/**
 * Dress every pre-1813 regular under `root` (a parsed glTF scene) once. Returns what was done
 * ({ tails: metres added, loops }) or null when nothing applies.
 */
export function fitRegulars(root, { sceneId = null } = {}) {
  if (!root || root.userData?.[DONE]) return null;
  const year = sceneYear(sceneId);
  if (year !== null && year >= AFTER_YEAR) return null;
  const meshes = []; root.traverse((o) => o.isSkinnedMesh && meshes.push(o));
  let result = null;
  for (const asset of REGULARS) {
    const find = (name) => meshes.find((m) => piece(m, asset, name));
    const tails = find('coat_tails'), coat = find('coat_body'), buttons = find('coat_buttons'), belts = find('crossbelts');
    if (!tails || !coat || !belts) continue;
    root.userData[DONE] = true;
    const thighs = ['thigh_l', 'thigh_r'].map((b) => bindJoint(tails, b)), knees = ['calf_l', 'calf_r'].map((b) => bindJoint(tails, b));
    if (thighs.some((j) => !j) || knees.some((j) => !j)) continue;
    const hip = (thighs[0].y + thighs[1].y) / 2, knee = (knees[0].y + knees[1].y) / 2;
    const added = lengthenTails(tails, hip - PIVOT_BELOW_HIP_M, knee + HEM_ABOVE_KNEE_M);

    const loops = [];
    // The breast: one loop a button, toward +x (the wearer's left), about the body's own axis.
    const coatSurf = surfaceOf(coat), spine = ['spine_02', 'spine_03'].map((b) => bindJoint(coat, b)).filter(Boolean);
    const cz = spine.length ? spine.reduce((s, j) => s + j.z, 0) / spine.length : 0;
    if (buttons) for (const b of buttonCentres(buttons)) {
      const rows = tapeLoop(coatSurf, 0, cz, b.y, Math.atan2(b.x, b.z - cz), 1, TAPE.breast);
      if (rows) loops.push({ rows, under: coat });
    }
    appendLoops(belts, loops);
    result = { tails: added, loops: loops.length };
  }
  return result;
}
