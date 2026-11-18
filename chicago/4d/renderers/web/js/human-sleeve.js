// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-sleeve.js — a sleeve's end moves as one band, and a glove fills the sleeve it ends in
 * (T-3553).
 *
 * Kevin, 2026-11-17: "No clothing breaks through in motion. Check walking and turning poses,
 * not only standing: ... the soldiers' stripes and trim on bending sleeves. Fix the garment
 * or its weights, not the camera."
 *
 * What the arms do in motion, measured on every export (tools/test_human_sleeve.mjs):
 *
 *   - The 1812 soldiers' and officers' cuff facings are drawn as a band continuing each
 *     coat sleeve to the wrist, joined ring to ring, both carried by the forearm where they
 *     meet; nothing of them comes through or opens at any elbow or wrist the figures take, at
 *     any level. They have no sleeve stripes or lace (the collar lace is the collar's).
 *   - A sleeve's end is skinned point by point from the skin under it, and round the wrist the
 *     skin is carried by the hand on its back and by the forearm on its palm side; so the ring
 *     of a sleeve's hem is carried by the hand at 0.05 at one point and 0.41 at the next, and
 *     when the walk's hand trails the forearm the hem pulls out into teeth (a shirt cuff's
 *     edge reads torn: the 1904 driver, Otis Bardwell, and every sleeve's hem a little).
 *   - The coachman's white gloves end two centimetres inside a livery sleeve five across, so
 *     with his forearm forward a visitor looks into the sleeve's mouth past the glove's edge
 *     and sees a band of bare wrist.
 *
 * Here, once per loaded body (before any figure is cloned from it, as human-seat.js does):
 *
 *   1. hems: every sleeve's open end at the wrist (a shirt's, a coat's, a facing's cuff) takes
 *      ONE set of weights round its ring, the ring's own average, faded back up the sleeve
 *      over HEM_M, so a hem is a stiff band and turns as one with the wrist; and a point of
 *      the hem more than TOOTH_M off the hem's own line (a tooth the decimated edge drew, up
 *      to MAX_TOOTH_M) is taken back along the arm to it. Only the hem's edge moves.
 *   2. gloves: a glove whose wrist ends inside a sleeve has its top BAND_M drawn EXTEND_M on
 *      up the forearm, inside the sleeve, its new edge eased most of the way (REACH) to
 *      LINING_M inside the lining and tapering back to the glove as drawn; the part drawn up
 *      takes the sleeve's own weights at its new place (one set round the arm), so it moves
 *      with the sleeve that hides it. Looking into the sleeve's mouth one sees glove, not
 *      skin. A reconstructed gauntlet (liberty L-sleeve-3553), never seen outside the sleeve.
 *
 * Topology and UVs are unchanged. Cost: a few thousand vertices per level, once per parse.
 * No geometry, texture, draw call or program is added.
 */
import * as THREE from 'three';

/** The hem band: up the sleeve from its end, metres per adult arm (shoulder to wrist ARM_M). */
export const HEM_M = 0.035;
/** A hem point further than TOOTH_M along the arm from the hem's fitted line is a tooth (or a
 * notch) of the edge and is taken back to within TOOTH_M of it, by no more than MAX_TOOTH_M. */
export const TOOTH_M = 0.002, MAX_TOOTH_M = 0.015;
/** A rim counts as the sleeve's end at the wrist when it lies within this of the wrist joint. */
export const WRIST_REACH_M = 0.07;
/** A glove ending inside a sleeve: its top BAND_M is drawn EXTEND_M up the forearm, its new
 * edge eased half way to LINING_M inside the sleeve's lining (by no more than MAX_EASE_M); the
 * glove's edge must lie at least MOUTH_M inside the sleeve's mouth. */
export const BAND_M = 0.02, EXTEND_M = 0.04, LINING_M = 0.005, MOUTH_M = 0.003, MAX_EASE_M = 0.02;
/** How far across the gap to the lining the glove's new edge is eased (a share of it). */
export const REACH = 0.8;
const ARM_M = 0.54;
const SKIP = /^(skin|hair|eyes|headwear|footwear)/;
const FINGER = /^(thumb|index|middle|ring|pinky)_\d+_[lr]$/;
const SIDES = ['l', 'r'];
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const lodOf = (o) => (o.name ?? '').match(/_lod(\d*)$/)?.[1] ?? '';

/** Is this mesh a piece of clothing (a garment or a worn accessory: gloves, cuffs, buttons). */
export function isCloth(mesh) {
  return !!(mesh?.isSkinnedMesh && mesh.skeleton && mesh.geometry?.attributes?.skinWeight
    && /^(garment|accessory)/.test(materialName(mesh)) && !SKIP.test(materialName(mesh)));
}

/** The arm chain at bind, from a mesh's own skeleton: per side shoulder S, elbow E, wrist W. */
function armsOf(mesh) {
  const sk = mesh.skeleton, index = new Map(sk.bones.map((b, i) => [b?.name, i]));
  const at = (n) => (index.has(n) ? new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[index.get(n)].clone().invert()) : null);
  const arms = {};
  for (const s of SIDES) {
    const S = at(`upperarm_${s}`), E = at(`lowerarm_${s}`), W = at(`hand_${s}`);
    if (!S || !E || !W) return null;
    arms[s] = { S, E, W, fore: W.clone().sub(E).normalize(), upper: S.clone().sub(E).normalize(), foreLen: E.distanceTo(W), scale: (S.distanceTo(E) + E.distanceTo(W)) / ARM_M };
  }
  return arms;
}
/** Where p lies along arm a: + past the elbow toward the wrist, - up the upper arm (metres). */
function along(a, p) {
  const v = p.clone().sub(a.E), f = v.dot(a.fore);
  return f >= 0 ? f : -Math.max(0, v.dot(a.upper));
}
/** p's offset square to the forearm (out from its axis). */
function radial(a, p) {
  const v = p.clone().sub(a.E);
  return v.addScaledVector(a.fore, -v.dot(a.fore));
}

const boneNames = (mesh) => mesh.skeleton.bones.map((b) => b?.name ?? '');
function readWeights(mesh, i, names) {
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight, out = {};
  for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); if (w > 0) { const n = names[si.getComponent(i, k)]; out[n] = (out[n] ?? 0) + w; } }
  return out;
}
/** Write a {boneName: weight} set into vertex i (the four largest, renormalised). */
function writeWeights(mesh, i, set, boneIndex) {
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  const top = Object.entries(set).filter(([n, w]) => w > 1e-4 && boneIndex.has(n)).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const sum = top.reduce((s, [, w]) => s + w, 0);
  if (!(sum > 0)) return;
  for (let k = 0; k < 4; k++) {
    si.setComponent(i, k, top[k] ? boneIndex.get(top[k][0]) : 0);
    sw.setComponent(i, k, top[k] ? top[k][1] / sum : 0);
  }
}
const mixWeights = (a, b, k) => {
  const out = {};
  for (const n of new Set([...Object.keys(a), ...Object.keys(b)])) out[n] = (1 - k) * (a[n] ?? 0) + k * (b[n] ?? 0);
  return out;
};

/** A mesh read once: bind positions (metres), welded points, open edges, arm sides. */
function survey(mesh) {
  if (mesh.userData.__sleeveSurvey) return mesh.userData.__sleeveSurvey;
  const geo = mesh.geometry, pos = geo.attributes.position, n = pos.count, idx = geo.index;
  const names = boneNames(mesh), side = new Array(n).fill(null), finger = new Uint8Array(n);
  const sideName = names.map((nm) => nm.match(/^(?:upperarm|lowerarm|hand|(?:thumb|index|middle|ring|pinky)_\d+)_([lr])$/)?.[1] ?? null);
  const si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight;
  for (let i = 0; i < n; i++) {
    let l = 0, r = 0, f = 0;
    for (let k = 0; k < 4; k++) {
      const b = si.getComponent(i, k), w = sw.getComponent(i, k);
      if (sideName[b] === 'l') l += w; else if (sideName[b] === 'r') r += w;
      if (FINGER.test(names[b])) f += w;
    }
    side[i] = l > 0.5 ? 'l' : r > 0.5 ? 'r' : null;
    finger[i] = f > 0.3 ? 1 : 0;
  }
  const P = new Array(n), v = new THREE.Vector3();
  const keyOf = (p) => `${Math.round(p.x * 2e4)},${Math.round(p.y * 2e4)},${Math.round(p.z * 2e4)}`;
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) {
    P[i] = v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).clone();
    const k = keyOf(P[i]); let g = keys.get(k);
    if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); }
    groupOf[i] = g;
  }
  const tri = idx ? idx.count / 3 : n / 3, corner = (t, c) => (idx ? idx.getX(t * 3 + c) : t * 3 + c);
  const edges = new Map();
  for (let t = 0; t < tri; t++) for (let c = 0; c < 3; c++) {
    const a = groupOf[corner(t, c)], b = groupOf[corner(t, (c + 1) % 3)];
    if (a === b) continue;
    const k = a < b ? a * 1048576 + b : b * 1048576 + a;
    edges.set(k, (edges.get(k) ?? 0) + 1);
  }
  const open = new Uint8Array(first.length), link = new Map();
  for (const [k, c] of edges) {
    if (c !== 1) continue;
    const a = Math.floor(k / 1048576), b = k % 1048576;
    open[a] = 1; open[b] = 1;
    for (const [x, y] of [[a, b], [b, a]]) { let l = link.get(x); if (!l) link.set(x, (l = [])); l.push(y); }
  }
  // The open edges' loops: each connected run of open edges, as its welded points.
  const loopOf = new Int32Array(first.length).fill(-1), loops = [];
  for (const g0 of link.keys()) {
    if (loopOf[g0] >= 0) continue;
    const loop = [g0], id = loops.length; loopOf[g0] = id;
    for (let k = 0; k < loop.length; k++) for (const o of link.get(loop[k])) if (loopOf[o] < 0) { loopOf[o] = id; loop.push(o); }
    loops.push(loop);
  }
  const out = { P, side, finger, groupOf, first, open, loops, names, tri, corner };
  mesh.userData.__sleeveSurvey = out;
  return out;
}

/** The open ends of a mesh at each wrist: per side { t (the rim's mean place along the arm),
 * groups (the rim's welded points) }, only for a sleeve (not a glove: it reaches the fingers). */
function wristEnds(mesh, arms) {
  const S = survey(mesh), ends = {};
  if (S.finger.some((f) => f)) return ends;
  for (const s of SIDES) {
    const a = arms[s], reach = WRIST_REACH_M * a.scale;
    // Each loop of open edges on this forearm that goes round the arm near the wrist; the
    // sleeve's end is the one nearest the hand (a cuff band's upper edge is not its hem).
    let best = null;
    for (const loop of S.loops) {
      const rim = [];
      for (const g of loop) {
        const i = S.first[g];
        if (S.side[i] !== s) continue;
        const t = along(a, S.P[i]);
        if (Math.abs(t - a.foreLen) <= reach && t > a.foreLen * 0.5) rim.push([g, t]);
      }
      if (rim.length < 6 || rim.length < 0.8 * loop.length) continue;
      const dirs = rim.map(([g]) => radial(a, S.P[S.first[g]]).normalize());
      const mean = dirs.reduce((m, d) => m.add(d), new THREE.Vector3()).divideScalar(dirs.length);
      if (mean.length() > 0.5) continue;
      const end = { t: rim.reduce((m, [, t]) => m + t, 0) / rim.length, lo: Math.min(...rim.map(([, t]) => t)), hi: Math.max(...rim.map(([, t]) => t)), groups: rim.map(([g]) => g) };
      if (!best || end.t > best.t) best = end;
    }
    if (best) ends[s] = best;
  }
  return ends;
}

/**
 * Give a sleeve's hem ring one set of weights, its own average, faded back over HEM_M.
 * Returns { vertices, sides, spread_before, spread_after } (the largest difference in hand
 * weight round the ring before and after), or null when the mesh has no sleeve end.
 */
export function bandHem(mesh) {
  const arms = armsOf(mesh);
  if (!arms) return null;
  const S = survey(mesh), ends = wristEnds(mesh, arms);
  if (!Object.keys(ends).length) return null;
  const names = S.names, boneIndex = new Map(names.map((n, i) => [n, i]));
  let count = 0, before = 0, after = 0, teeth = 0;
  const shiftAlong = new Map();
  for (const [s, end] of Object.entries(ends)) {
    const a = arms[s], hem = HEM_M * a.scale;
    // The ring's own weights, every welded point once.
    const ring = {};
    for (const g of end.groups) { const w = readWeights(mesh, S.first[g], names); for (const [n, x] of Object.entries(w)) ring[n] = (ring[n] ?? 0) + x / end.groups.length; }
    const hand = (w) => w[`hand_${s}`] ?? 0;
    const hs = end.groups.map((g) => hand(readWeights(mesh, S.first[g], names)));
    before = Math.max(before, Math.max(...hs) - Math.min(...hs));
    for (let i = 0; i < S.P.length; i++) {
      if (S.side[i] !== s) continue;
      const t = along(a, S.P[i]);
      // Full from the rim's highest point down; faded out over HEM_M above it.
      const k = smooth((t - (end.lo - hem)) / hem);
      if (!(k > 1e-3)) continue;
      writeWeights(mesh, i, mixWeights(readWeights(mesh, i, names), ring, k), boneIndex);
      count++;
    }
    const hs2 = end.groups.map((g) => hand(readWeights(mesh, S.first[g], names)));
    after = Math.max(after, Math.max(...hs2) - Math.min(...hs2));
    // The hem's line: its points round the arm fitted by a + b cos + c sin of the angle (a
    // straight or slanted cut); a point off that line by more than TOOTH_M (a tooth or a
    // notch of the decimated edge) is taken along the arm back to it.
    const u = new THREE.Vector3(0, 1, 0).addScaledVector(a.fore, -a.fore.y);
    if (u.lengthSq() < 1e-6) u.set(0, 0, 1).addScaledVector(a.fore, -a.fore.z);
    u.normalize();
    const w = new THREE.Vector3().crossVectors(a.fore, u);
    const pts = end.groups.map((g) => { const r = radial(a, S.P[S.first[g]]); return { g, th: Math.atan2(r.dot(w), r.dot(u)), t: along(a, S.P[S.first[g]]) }; });
    const fit = fitLine(pts), tooth = TOOTH_M * a.scale, most = MAX_TOOTH_M * a.scale;
    for (const p of pts) {
      const want = fit(p.th), d = p.t - want;
      if (Math.abs(d) <= tooth) continue;
      const move = Math.max(-most, Math.min(most, -(d - Math.sign(d) * tooth)));
      shiftAlong.set(p.g, a.fore.clone().multiplyScalar(move));
      teeth = Math.max(teeth, Math.abs(move));
    }
  }
  if (shiftAlong.size) {
    const pos = mesh.geometry.attributes.position, Binv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
    const moved = new Uint8Array(S.first.length);
    for (const g of shiftAlong.keys()) moved[g] = 1;
    for (let i = 0; i < S.P.length; i++) {
      const sh = shiftAlong.get(S.groupOf[i]); if (!sh) continue;
      v.copy(S.P[i]).add(sh).applyMatrix4(Binv); pos.setXYZ(i, v.x, v.y, v.z);
    }
    pos.needsUpdate = true;
    mesh.geometry.computeBoundingBox(); mesh.geometry.computeBoundingSphere();
  }
  mesh.geometry.attributes.skinIndex.needsUpdate = true;
  mesh.geometry.attributes.skinWeight.needsUpdate = true;
  return { vertices: count, sides: Object.keys(ends).length, spread_before: before, spread_after: after, teeth_m: teeth, teeth: shiftAlong.size };
}

/** Least squares t = a + b cos th + c sin th through {th, t} points: a function of th. */
function fitLine(pts) {
  const A = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], y = [0, 0, 0];
  for (const p of pts) {
    const r = [1, Math.cos(p.th), Math.sin(p.th)];
    for (let i = 0; i < 3; i++) { y[i] += r[i] * p.t; for (let j = 0; j < 3; j++) A[i][j] += r[i] * r[j]; }
  }
  // Solve by Cramer's rule (3 x 3); a ring that does not go round falls back to its mean.
  const det = (M) => M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0]) + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]);
  const D = det(A);
  if (Math.abs(D) < 1e-9) { const m = y[0] / Math.max(1, A[0][0]); return () => m; }
  const c = [0, 1, 2].map((k) => det(A.map((row, i) => row.map((x, j) => (j === k ? y[i] : x)))) / D);
  return (th) => c[0] + c[1] * Math.cos(th) + c[2] * Math.sin(th);
}

/** Ray against a set of triangles: the nearest hit within maxT as { t, tri, u, v } or null. */
function castRay(o, d, tris, P, maxT) {
  let best = null;
  const e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), p = new THREE.Vector3(), q = new THREE.Vector3(), s = new THREE.Vector3();
  for (const tr of tris) {
    const a = P[tr[0]], b = P[tr[1]], c = P[tr[2]];
    e1.subVectors(b, a); e2.subVectors(c, a); p.crossVectors(d, e2);
    const det = e1.dot(p);
    if (Math.abs(det) < 1e-12) continue;
    const inv = 1 / det; s.subVectors(o, a);
    const u = s.dot(p) * inv; if (u < 0 || u > 1) continue;
    q.crossVectors(s, e1);
    const v = d.dot(q) * inv; if (v < 0 || u + v > 1) continue;
    const t = e2.dot(q) * inv;
    if (t > 1e-5 && t < maxT && (!best || t < best.t)) best = { t, tri: tr, u, v };
  }
  return best;
}

/**
 * Carry a glove that ends inside a sleeve on up the forearm, inside the sleeve: its top band
 * (BAND_M of it) is drawn up EXTEND_M toward the elbow and eased out most of the way (REACH) to
 * the sleeve's lining at its new edge, tapering back to the glove as drawn at the foot of the band; the
 * part drawn up takes the sleeve's own weights at its new place, one set round the arm, so
 * it moves with the sleeve that hides it. `over` are the other cloth meshes of the same
 * level. Returns { moved, max_m } or null when the mesh is not such a glove.
 */
export function easeGlove(mesh, over) {
  const arms = armsOf(mesh);
  if (!arms) return null;
  const S = survey(mesh);
  if (!S.finger.some((f) => f)) return null; // only a glove: the layer that reaches the fingers
  const names = S.names, boneIndex = new Map(names.map((n, i) => [n, i]));
  const G = S.first.length, shift = new Array(G).fill(null), take = new Array(G).fill(null);
  let any = false;
  for (const s of SIDES) {
    const a = arms[s];
    // The glove's top edge on this side: its loop of open points up the forearm.
    let rimT = Infinity;
    for (const loop of S.loops) {
      const ts = loop.filter((g) => S.side[S.first[g]] === s).map((g) => along(a, S.P[S.first[g]]));
      if (ts.length < 6 || ts.some((t) => t < a.foreLen * 0.5 || t > a.foreLen + 0.02 * a.scale)) continue;
      rimT = Math.min(rimT, Math.min(...ts));
    }
    if (!Number.isFinite(rimT)) continue;
    // The sleeve this edge ends in: its wrist end lies below the glove's edge.
    let sleeve = null;
    for (const o of over) {
      const oa = armsOf(o); if (!oa) continue;
      const end = wristEnds(o, oa)[s];
      if (!end || end.lo <= rimT + MOUTH_M * a.scale) continue;
      const OS = survey(o), tris = [];
      for (let t = 0; t < OS.tri; t++) {
        const q = [OS.corner(t, 0), OS.corner(t, 1), OS.corner(t, 2)];
        if (q.some((i) => OS.side[i] === s && along(a, OS.P[i]) > rimT - (EXTEND_M + 0.03) * a.scale)) tris.push(q);
      }
      // The sleeve's weights at a place along the arm: one set, its ring's average there.
      const ringAt = (t0) => {
        const out = {}; let n = 0;
        for (let g = 0; g < OS.first.length; g++) {
          const i = OS.first[g];
          if (OS.side[i] !== s || Math.abs(along(a, OS.P[i]) - t0) > 0.006 * a.scale) continue;
          for (const [nm, x] of Object.entries(readWeights(o, i, OS.names))) out[nm] = (out[nm] ?? 0) + x;
          n++;
        }
        for (const nm of Object.keys(out)) out[nm] /= Math.max(1, n);
        return n ? out : null;
      };
      sleeve = { o, OS, end, tris, ringAt };
      break;
    }
    if (!sleeve) continue;
    const band = BAND_M * a.scale, top = rimT - EXTEND_M * a.scale;
    for (let g = 0; g < G; g++) {
      const i = S.first[g];
      if (S.side[i] !== s) continue;
      const p = S.P[i], t = along(a, p);
      if (t < rimT - 1e-4 || t > rimT + band) continue;
      const u = Math.max(0, (t - rimT) / band), t1 = top + u * (rimT + band - top);
      const q = p.clone().addScaledVector(a.fore, t1 - t);
      const dir = radial(a, q); if (dir.lengthSq() < 1e-10) continue; dir.normalize();
      const hit = castRay(q, dir, sleeve.tris, sleeve.OS.P, 0.05 * a.scale);
      const k = 1 - smooth(u);
      const out = hit ? Math.max(0, Math.min(MAX_EASE_M * a.scale, REACH * (hit.t - LINING_M * a.scale))) * k : 0;
      shift[g] = q.addScaledVector(dir, out).sub(p);
      take[g] = { w: sleeve.ringAt(t1), k };
      any = true;
    }
  }
  if (!any) return null;
  const pos = mesh.geometry.attributes.position, Binv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
  const moved = new Uint8Array(G);
  let count = 0, far = 0;
  for (let g = 0; g < G; g++) if (shift[g] && shift[g].length() > 1e-5) { moved[g] = 1; count++; far = Math.max(far, shift[g].length()); }
  for (let i = 0; i < S.P.length; i++) {
    const g = S.groupOf[i]; if (!moved[g]) continue;
    v.copy(S.P[i]).add(shift[g]).applyMatrix4(Binv);
    pos.setXYZ(i, v.x, v.y, v.z);
    if (take[g].w) writeWeights(mesh, i, mixWeights(readWeights(mesh, i, names), take[g].w, take[g].k), boneIndex);
  }
  pos.needsUpdate = true;
  mesh.geometry.attributes.skinIndex.needsUpdate = true;
  mesh.geometry.attributes.skinWeight.needsUpdate = true;
  renormal(mesh, S.groupOf, moved);
  mesh.geometry.computeBoundingBox(); mesh.geometry.computeBoundingSphere();
  return { moved: count, max_m: far };
}

/** Normals of the moved points again from their faces, each point's copies sharing one,
 * turned to the side the asset's own normals faced. */
function renormal(mesh, groupOf, moved) {
  const geo = mesh.geometry, nrm = geo.attributes.normal, pos = geo.attributes.position, idx = geo.index, n = pos.count;
  if (!nrm) return;
  const G = moved.length, sum = new Float64Array(G * 3);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  const tri = idx ? idx.count / 3 : n / 3;
  for (let t = 0; t < tri; t++) {
    const q = [0, 1, 2].map((k) => (idx ? idx.getX(t * 3 + k) : t * 3 + k));
    if (!q.some((i) => moved[groupOf[i]])) continue;
    a.fromBufferAttribute(pos, q[0]); b.fromBufferAttribute(pos, q[1]); c.fromBufferAttribute(pos, q[2]);
    const fn = e1.subVectors(b, a).cross(e2.subVectors(c, a));
    for (const i of q) { const g = groupOf[i]; if (moved[g]) { sum[g * 3] += fn.x; sum[g * 3 + 1] += fn.y; sum[g * 3 + 2] += fn.z; } }
  }
  const s = new THREE.Vector3(), old = new THREE.Vector3();
  let agree = 0;
  for (let i = 0; i < n; i++) { const g = groupOf[i]; if (!moved[g]) continue; old.fromBufferAttribute(nrm, i); s.set(sum[g * 3], sum[g * 3 + 1], sum[g * 3 + 2]); agree += Math.sign(s.dot(old)); }
  const sign = agree < 0 ? -1 : 1;
  for (let i = 0; i < n; i++) {
    const g = groupOf[i]; if (!moved[g]) continue;
    s.set(sum[g * 3], sum[g * 3 + 1], sum[g * 3 + 2]);
    if (s.lengthSq() < 1e-20) continue;
    s.multiplyScalar(sign).normalize();
    nrm.setXYZ(i, s.x, s.y, s.z);
  }
  nrm.needsUpdate = true;
}

/** Fit every sleeve's hem and every glove of a loaded body, once (cloned figures share it). */
export function fitSleeves(root) {
  if (!root) return null;
  if (root.userData.chicagoSleeveFit) return root.userData.chicagoSleeveFit;
  const cloth = [];
  root.traverse((o) => { if (isCloth(o)) cloth.push(o); });
  const report = [];
  for (const m of cloth) {
    const r = bandHem(m);
    if (r && r.vertices) report.push({ mesh: m.name, kind: 'hem', ...r });
  }
  // The gloves read the sleeves' hems as banded above.
  for (const m of cloth) {
    const r = easeGlove(m, cloth.filter((c) => c !== m && lodOf(c) === lodOf(m)));
    if (r && r.moved) report.push({ mesh: m.name, kind: 'glove', ...r });
  }
  for (const m of cloth) delete m.userData.__sleeveSurvey;
  root.userData.chicagoSleeveFit = report;
  return report;
}
