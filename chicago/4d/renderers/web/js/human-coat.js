// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-coat.js — a coat closes under the arm and at the back vent (T-3553).
 *
 * Two faults on the men in coats, both in how the exports are drawn, neither in the cloth:
 *
 * The armpit. Every body is drawn and skinned with its arms out level (the bind pose), and
 * every figure walks with them hanging. Bringing an arm down folds the armpit, and linear
 * skinning folds each layer by its own weights: the body's skin there is shared between the
 * upper arm and the chest about half and half, the coat over it leans to the arm or to the
 * chest by a different share, and the cloth over the hollow stands 2 to 4 cm off the skin.
 * Hanging, the skin of the front and back folds of the armpit comes out through the coat by
 * up to 2.7 cm (Philip Peck's tailcoat, standing and at every swing of the arm), and from the
 * side a slit of bare skin shows between sleeve and body; under John Glessner's frock coat his
 * shirt comes through the same way. Every coat, livery, soldier's coat, jacket and sleeved
 * shirt in the town did it. Giving the layers under the coat the coat's own weights there does
 * not close it (measured: the coat's own fold is where it opens), so here, once per loaded
 * body, what lies under the outermost sleeved garment round each armpit (the body's skin, a
 * shirt, a waistcoat) is drawn thinner: moved in along its own normal by up to DEPTH_M, in
 * full within ZONE.full of a point ZONE.below under the shoulder joint and fading out by
 * ZONE.fade, and only where it was inside that garment, fully no nearer than EDGE_M to the
 * garment's open edges (a cuff, the neck, the front, the hem). The layers move in together,
 * so they keep their order, and none of it is ever seen: the garment over it is drawn exactly
 * as before, as the exporter already leaves the body out under a shirt.
 *
 * The vent. A tailcoat's tails, a soldier's coat tails and an officer's coat skirts are cut
 * in two at the middle of the back, and the exporter draws the two edges 8 mm apart from the
 * waist to the hem: from behind, standing or walking, a light line runs down the man's back
 * (his trousers, and his skin at the top). Here each such vent is closed the way a coat's
 * vent hangs, the left side lapped over the right: each edge goes across the middle by
 * VENT.lap, the left VENT.out behind the right (flush again where the vent's top meets the
 * waist seam), the shift fading into each side over VENT.fade. human-skirt.js drives both
 * sides by their angle round the body, so the two edges, now within a few degrees of each
 * other on the same panels, walk together.
 *
 * The fold (round 4). Hanging, the coat's own cloth at the front and back folds of the armpit
 * crumples: skinned point by point, neighbouring points lean to the arm and to the chest by
 * shares that jump, so about a ninth of the cloth round each armpit turns over on itself and
 * shades dark (the 1812 trader's green coat showed it most). For the coats listed in EASE_FOLD,
 * the outer garment's weights are evened out over its own surface round each armpit (FOLD:
 * repeated neighbour averaging, in full within `full` of a point `below` the shoulder joint,
 * fading out by `fade`), so the fold turns over a band of cloth instead of one row of points;
 * and what lies under it there (the thinned layers) takes the coat's new weights at its nearest
 * point, so it folds with the coat and stays under it. Only those weights change, and only at
 * the two near levels (a far level's few faces at the shoulder, smoothed, open round it; left
 * as drawn).
 *
 * Topology and UVs are unchanged; skin weights change only at the armpits of an EASE_FOLD coat
 * and the layers under it; positions move once per parse (about 25 to 45 ms at LOD0, under 20
 * at the far levels; the fold adds about 40 ms on the trader), before any figure is cloned. No
 * geometry, texture, draw call or program is added. tools/test_human_coat.mjs measures all three on every body at every level,
 * standing and walking. The lap's side, the thinned layers and the evened weights are
 * reconstructed (liberty L-coat-3553).
 */
import * as THREE from 'three';

const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const SIDES = ['l', 'r'];
const ADULT_SHOULDERS_M = 0.4, ADULT_LEG_M = 0.85;
const CELL = 0.03, TIE = 1e-6;

/** The armpit: a ball round a point `below` under each shoulder joint, in full within `full`, to nothing at `fade` (metres, per 0.4 m of shoulders). */
export const ZONE = Object.freeze({ below: 0.07, full: 0.09, fade: 0.14 });
/** What lies under the coat there moves in this far. */
export const DEPTH_M = 0.04;
/** Under the coat: inside it, with its cloth within REACH_M, and fully only this far from its open edges. */
export const REACH_M = 0.06, EDGE_M = 0.04;
/** A sleeved garment: this many vertices down an upper arm. A blanket or shawl
 * over the shoulders is not one: it is put on and set aside (dress records hide it), and
 * nothing under it may be thinned. */
const SLEEVE_MIN = 20, SLEEVE_OUT_M = 0.1, DRAPED = /(^|_)(blanket|shawl|wrap|cloak|cape|mantle)(_|$)/;
/** The vent: open edges within `near` of the middle of the back, down at least `minLength`;
 * closed with `lap` across the middle each way, the left `out` behind, fading over `fade`. */
export const VENT = Object.freeze({ near: 0.012, lap: 0.003, out: 0.003, fade: 0.06, minLength: 0.08 });
/** The fold: the coats whose weights are evened round the armpit (by the outer garment's material),
 * and how: `iterations` of neighbour averaging at `rate`, in full within `full` of a point `below`
 * the shoulder joint and fading out by `fade` (metres per 0.4 m of shoulders); a layer under the
 * coat takes the coat's weights at its nearest point within `near`, fading out by `far`. Only the
 * trader's coat so far: every coat folds the same way, but the other coated bodies are tailored
 * by modules of their own (human-tailor-1835.js, human-regulars.js, human-frockcoat.js) whose
 * fits read these weights, and are left to them. */
export const EASE_FOLD = /^garment_outer__tailcoat_green_1810$/;
export const FOLD = Object.freeze({ iterations: 100, rate: 0.7, below: 0.06, full: 0.09, fade: 0.15, near: 0.04, far: 0.06 });
const VENT_PIECE = /(^|_)(coat|tailcoat|frock|livery)(_|$)/, VENT_PART = /(^|_)(tails?|skirts?)(_|$)/;

function bindJoint(sk, name) {
  const i = sk.bones.findIndex((b) => b?.name === name);
  return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert());
}
function bindPositions(mesh) {
  const pos = mesh.geometry.attributes.position, n = pos.count, P = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
/** Each vertex's welded group (a UV seam's copies are one point), and the cloth's open edges between groups. */
function rimOf(P, idx) {
  const n = P.length / 3, gid = new Int32Array(n), ids = new Map();
  for (let i = 0; i < n; i++) {
    const k = `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`;
    let g = ids.get(k); if (g === undefined) ids.set(k, (g = ids.size)); gid[i] = g;
  }
  const W = 4194304, edges = new Map();
  for (let t = 0; t < idx.length / 3; t++) for (let k = 0; k < 3; k++) {
    const p = gid[idx[t * 3 + k]], q = gid[idx[t * 3 + (k + 1) % 3]];
    const e = p < q ? p * W + q : q * W + p;
    edges.set(e, (edges.get(e) ?? 0) + 1);
  }
  const open = [];
  for (const [e, c] of edges) if (c === 1) open.push([Math.floor(e / W), e % W]);
  const first = new Int32Array(ids.size).fill(-1);
  for (let i = 0; i < n; i++) if (first[gid[i]] < 0) first[gid[i]] = i;
  return { gid, open, first };
}

/** A garment's surface at bind: of any point, which side of it (s < 0 inside) and how far its nearest cloth is from an open edge. */
function surface(mesh) {
  const geo = mesh.geometry, idx = geo.index.array, T = idx.length / 3, P = bindPositions(mesh), n = P.length / 3;
  const grid = new Map(), key = (x, y, z) => `${x},${y},${z}`;
  for (let t = 0; t < T; t++) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let c = 0; c < 3; c++) for (let k = 0; k < 3; k++) { const x = P[idx[t * 3 + c] * 3 + k]; lo[k] = Math.min(lo[k], x); hi[k] = Math.max(hi[k], x); }
    for (let x = Math.floor(lo[0] / CELL); x <= Math.floor(hi[0] / CELL); x++)
      for (let y = Math.floor(lo[1] / CELL); y <= Math.floor(hi[1] / CELL); y++)
        for (let z = Math.floor(lo[2] / CELL); z <= Math.floor(hi[2] / CELL); z++) {
          const k = key(x, y, z); let l = grid.get(k); if (!l) grid.set(k, (l = [])); l.push(t);
        }
  }
  // The outward side of each triangle: the side the asset's own normals face.
  const pos = geo.attributes.position, nrm = geo.attributes.normal, sign = new Int8Array(T).fill(1);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), nn = new THREE.Vector3(), m = new THREE.Vector3();
  if (nrm) for (let t = 0; t < T; t++) {
    const i0 = idx[t * 3], i1 = idx[t * 3 + 1], i2 = idx[t * 3 + 2];
    a.fromBufferAttribute(pos, i0); b.fromBufferAttribute(pos, i1); c.fromBufferAttribute(pos, i2);
    const fn = e1.subVectors(b, a).cross(e2.subVectors(c, a));
    nn.fromBufferAttribute(nrm, i0).add(m.fromBufferAttribute(nrm, i1)).add(m.fromBufferAttribute(nrm, i2));
    sign[t] = fn.dot(nn) >= 0 ? 1 : -1;
  }
  // How far a vertex is from the cloth's open edges, as far as it matters (twice EDGE_M at most,
  // past any body's scaled edge zone), asked only of the corners of the triangles a query lands on.
  const { open, first } = rimOf(P, idx), rims = new Map(), RC = 2 * EDGE_M;
  for (const g of new Set(open.flat())) {
    const i = first[g], k = key(Math.floor(P[i * 3] / RC), Math.floor(P[i * 3 + 1] / RC), Math.floor(P[i * 3 + 2] / RC));
    let l = rims.get(k); if (!l) rims.set(k, (l = [])); l.push(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]);
  }
  const edgeDist = new Float32Array(n).fill(-1);
  const edgeOf = (i) => {
    if (edgeDist[i] >= 0) return edgeDist[i];
    const cx = Math.floor(P[i * 3] / RC), cy = Math.floor(P[i * 3 + 1] / RC), cz = Math.floor(P[i * 3 + 2] / RC);
    let d = RC * RC;
    for (let x = cx - 1; x <= cx + 1; x++) for (let y = cy - 1; y <= cy + 1; y++) for (let z = cz - 1; z <= cz + 1; z++) {
      const l = rims.get(key(x, y, z)); if (!l) continue;
      for (let k = 0; k < l.length; k += 3) d = Math.min(d, (l[k] - P[i * 3]) ** 2 + (l[k + 1] - P[i * 3 + 1]) ** 2 + (l[k + 2] - P[i * 3 + 2]) ** 2);
    }
    return (edgeDist[i] = Math.sqrt(d));
  };
  const tri = new THREE.Triangle(), q = new THREE.Vector3(), bary = new THREE.Vector3();
  const setTri = (t) => {
    const i0 = idx[t * 3], i1 = idx[t * 3 + 1], i2 = idx[t * 3 + 2];
    tri.set(a.set(P[i0 * 3], P[i0 * 3 + 1], P[i0 * 3 + 2]), b.set(P[i1 * 3], P[i1 * 3 + 1], P[i1 * 3 + 2]), c.set(P[i2 * 3], P[i2 * 3 + 1], P[i2 * 3 + 2]));
  };
  // Which side of the cloth p is on, by triangle t (whose closest point is in q): where the nearest point
  // is an edge or corner shared by several triangles, the one facing p most squarely decides.
  const facing = (p, t, out) => { setTri(t); tri.closestPointToPoint(p, q); tri.getNormal(out).multiplyScalar(sign[t]); return out.dot(m.subVectors(p, q)); };
  const fn = new THREE.Vector3();
  return (p, reach) => {
    let best = Infinity, bt = -1, bs = 0;
    const R = Math.ceil(reach / CELL), cx = Math.floor(p.x / CELL), cy = Math.floor(p.y / CELL), cz = Math.floor(p.z / CELL), seen = new Set();
    // Ring by ring of cells: once the nearest found is within the rings searched, no farther cell can hold a nearer one.
    for (let r = 0; r <= R; r++) {
      for (let x = cx - r; x <= cx + r; x++) for (let y = cy - r; y <= cy + r; y++) for (let z = cz - r; z <= cz + r; z++) {
        if (Math.max(Math.abs(x - cx), Math.abs(y - cy), Math.abs(z - cz)) !== r) continue;
        const l = grid.get(key(x, y, z)); if (!l) continue;
        for (const t of l) {
          if (seen.has(t)) continue; seen.add(t);
          setTri(t); tri.closestPointToPoint(p, q);
          const d = q.distanceTo(p);
          if (d < best - TIE) { best = d; bt = t; bs = facing(p, t, fn); }
          else if (d <= best + TIE) { const s = facing(p, t, fn); if (Math.abs(s) > Math.abs(bs)) { bt = t; bs = s; } best = Math.min(best, d); }
        }
      }
      if (best <= r * CELL) break;
    }
    if (bt < 0 || best > reach) return null;
    setTri(bt); tri.closestPointToPoint(p, q); tri.getBarycoord(q, bary);
    const s = bs;
    const edge = edgeOf(idx[bt * 3]) * bary.x + edgeOf(idx[bt * 3 + 1]) * bary.y + edgeOf(idx[bt * 3 + 2]) * bary.z;
    return { d: best, s, edge };
  };
}

/** Is this garment sleeved: enough of its cloth runs down an upper arm, SLEEVE_OUT_M and more
 * out from the shoulder joint (a waistcoat's armhole is at the joint). */
export function isSleeved(mesh) {
  const sk = mesh.skeleton, pos = mesh.geometry?.attributes?.position;
  if (!sk || !pos || DRAPED.test(mesh.name ?? '')) return false;
  const v = new THREE.Vector3();
  let arm = 0;
  for (const s of SIDES) {
    const J = bindJoint(sk, `upperarm_${s}`), E = bindJoint(sk, `lowerarm_${s}`);
    if (!J || !E) return false;
    const A = E.sub(J).normalize();
    for (let i = 0; i < pos.count && arm < SLEEVE_MIN; i++) if (v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(J).dot(A) > SLEEVE_OUT_M) arm++;
  }
  return arm >= SLEEVE_MIN;
}

/**
 * Thin what lies under the outermost sleeved garment round each armpit, in place. Returns
 * { outer, moved: [{ mesh, moved, max_m }] }, or null when the body has no sleeved garment.
 */
export function fitArmpits(root) {
  if (!root) return null;
  if (root.userData.chicagoArmpits !== undefined) return root.userData.chicagoArmpits;
  root.userData.chicagoArmpits = null;
  const all = [];
  root.traverse((o) => { if (o.isSkinnedMesh && o.skeleton && o.geometry?.index) all.push(o); });
  const body = all.find((m) => materialName(m).split('__')[0] === 'skin');
  const cloth = all.filter((m) => /^garment/.test(materialName(m)));
  const coats = cloth.filter(isSleeved);
  if (!body || !coats.length) return null;
  const sk = body.skeleton, J = { l: bindJoint(sk, 'upperarm_l'), r: bindJoint(sk, 'upperarm_r') };
  const hipL = bindJoint(sk, 'thigh_l'), hipR = bindJoint(sk, 'thigh_r'), neck = bindJoint(sk, 'neck_01');
  if (!J.l || !J.r || !hipL || !hipR || !neck) return null;
  const U = neck.clone().sub(hipL.clone().add(hipR).multiplyScalar(0.5)).normalize();
  const scale = J.l.distanceTo(J.r) / ADULT_SHOULDERS_M;
  const centre = { l: J.l.clone().addScaledVector(U, -ZONE.below * scale), r: J.r.clone().addScaledVector(U, -ZONE.below * scale) };
  const full = ZONE.full * scale, fade = (ZONE.fade - ZONE.full) * scale;
  const zoneOf = (p) => Math.max(...SIDES.map((s) => 1 - smooth((p.distanceTo(centre[s]) - full) / fade)));
  const reach = REACH_M * scale, edgeM = EDGE_M * scale, depth = DEPTH_M * scale;
  const surf = new Map(coats.map((m) => [m, surface(m)]));
  const v = new THREE.Vector3();
  // The outermost: the sleeved garment whose cloth at the armpits lies inside the others least.
  let outer = coats[0];
  if (coats.length > 1) {
    let least = Infinity;
    for (const m of coats) {
      const P = bindPositions(m);
      let inside = 0, count = 0;
      for (let i = 0; i < P.length / 3; i++) {
        v.set(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]);
        if (zoneOf(v) < 0.5) continue;
        count++;
        for (const o of coats) if (o !== m) { const r = surf.get(o)(v, reach); if (r && r.s < 0) { inside++; break; } }
      }
      if (count < SLEEVE_MIN) continue; // no cloth at the armpit (a shirt's cuffs alone)
      const share = inside / count;
      if (share < least) { least = share; outer = m; }
    }
  }
  const S = surf.get(outer), nm = new THREE.Matrix3(), nv = new THREE.Vector3();
  const report = { outer: outer.name, moved: [] };
  for (const mesh of [body, ...cloth]) {
    if (mesh === outer) continue;
    const geo = mesh.geometry, pos = geo.attributes.position, nrm = geo.attributes.normal, n = pos.count;
    if (!nrm) continue;
    const Binv = mesh.bindMatrix.clone().invert();
    nm.getNormalMatrix(mesh.bindMatrix);
    let moved = 0, most = 0;
    for (let i = 0; i < n; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix);
      const z = zoneOf(v);
      if (!(z > 1e-3)) continue;
      const r = S(v, reach);
      if (!r || !(r.s < 0)) continue;
      const share = z * smooth(r.edge / edgeM);
      if (!(share > 1e-3)) continue;
      nv.fromBufferAttribute(nrm, i).applyMatrix3(nm).normalize();
      v.addScaledVector(nv, -depth * share).applyMatrix4(Binv);
      pos.setXYZ(i, v.x, v.y, v.z);
      moved++; most = Math.max(most, depth * share);
    }
    if (!moved) continue;
    pos.needsUpdate = true;
    geo.computeBoundingBox(); geo.computeBoundingSphere();
    report.moved.push({ mesh: mesh.name, moved, max_m: most });
  }
  root.userData.chicagoArmpits = report;
  return report;
}

/** The body's frame at bind from a mesh's skeleton: O mid-hips, U up, L left, F forward. */
function bodyFrame(sk) {
  const hl = bindJoint(sk, 'thigh_l'), hr = bindJoint(sk, 'thigh_r'), al = bindJoint(sk, 'foot_l'), ar = bindJoint(sk, 'foot_r');
  if (!hl || !hr || !al || !ar) return null;
  const O = hl.clone().add(hr).multiplyScalar(0.5), U = O.clone().sub(al.clone().add(ar).multiplyScalar(0.5));
  const leg = (hl.distanceTo(al) + hr.distanceTo(ar)) / 2;
  U.normalize();
  const L = hl.clone().sub(hr); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  return { O, U, L, F, scale: leg / ADULT_LEG_M };
}

/** Is this a coat's tails or skirts, by its piece name. */
export function isCoatSkirt(mesh) {
  return /^garment/.test(materialName(mesh)) && VENT_PIECE.test(mesh.name ?? '') && VENT_PART.test(mesh.name ?? '');
}

/**
 * Close the back vent of every coat's tails or skirts, left over right, in place. Returns
 * [{ mesh, gap_m, from, to, moved }] (the vent as drawn, its ends' heights from the hips,
 * the vertices moved), empty when no coat has one.
 */
export function closeVents(root) {
  if (!root) return null;
  if (root.userData.chicagoVents) return root.userData.chicagoVents;
  const report = [];
  root.userData.chicagoVents = report;
  const meshes = [];
  root.traverse((o) => { if (o.isSkinnedMesh && o.skeleton && o.geometry?.index && isCoatSkirt(o)) meshes.push(o); });
  const v = new THREE.Vector3();
  for (const mesh of meshes) {
    const fr = bodyFrame(mesh.skeleton);
    if (!fr) continue;
    const { O, U, L, F, scale } = fr;
    const geo = mesh.geometry, pos = geo.attributes.position, n = pos.count;
    const X = new Float64Array(n), Y = new Float64Array(n), R = new Float64Array(n);
    for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(O); X[i] = v.dot(L); Y[i] = v.dot(U); R[i] = -v.dot(F); }
    const { open, first } = rimOf(bindPositions(mesh), geo.index.array);
    // The vent: open edges behind, near the middle, running down, on both sides of it.
    const near = VENT.near * scale, side = { l: [], r: [] };
    for (const [p, q] of open) {
      const a = first[p], b = first[q];
      if (R[a] <= 0 || R[b] <= 0 || Math.abs(X[a]) > near || Math.abs(X[b]) > near) continue;
      if (Math.sign(X[a]) !== Math.sign(X[b])) continue;
      if (Math.abs(Y[a] - Y[b]) < 0.5 * Math.hypot(X[a] - X[b], R[a] - R[b])) continue; // across, not down
      side[X[a] > 0 ? 'l' : 'r'].push(a, b);
    }
    const span = (list) => {
      let lo = Infinity, hi = -Infinity, x = 0;
      for (const i of list) { lo = Math.min(lo, Y[i]); hi = Math.max(hi, Y[i]); x += Math.abs(X[i]); }
      return { lo, hi, x: list.length ? x / list.length : 0 };
    };
    const sl = span(side.l), sr = span(side.r), lo = Math.max(sl.lo, sr.lo), hi = Math.min(sl.hi, sr.hi);
    if (!(hi - lo > VENT.minLength * scale)) continue;
    const fade = VENT.fade * scale, lap = VENT.lap * scale, out = VENT.out * scale;
    const Binv = mesh.bindMatrix.clone().invert();
    let moved = 0;
    for (let i = 0; i < n; i++) {
      if (R[i] <= 0 || Y[i] > hi + fade) continue;
      const left = X[i] > 0, edge = left ? sl.x : sr.x;
      const f = 1 - smooth((Math.abs(X[i]) - edge) / fade);
      if (!(f > 1e-4)) continue;
      const x = X[i] + (left ? -1 : 1) * (edge + lap) * f, r = R[i] + (left ? out * f * smooth((hi - Y[i]) / fade) : 0);
      v.copy(O).addScaledVector(L, x).addScaledVector(U, Y[i]).addScaledVector(F, -r).applyMatrix4(Binv);
      pos.setXYZ(i, v.x, v.y, v.z);
      moved++;
    }
    pos.needsUpdate = true;
    geo.computeBoundingBox(); geo.computeBoundingSphere();
    report.push({ mesh: mesh.name, gap_m: sl.x + sr.x, from: lo, to: hi, moved });
  }
  return report;
}

function weightsOf(m, i) {
  const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, w = new Map();
  for (let k = 0; k < 4; k++) { const x = sw.getComponent(i, k); if (x > 0) w.set(si.getComponent(i, k), (w.get(si.getComponent(i, k)) ?? 0) + x); }
  return w;
}
function writeWeights(m, i, w) {
  const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight;
  const top = [...w].filter((e) => e[1] > 1e-5).sort((a, b) => b[1] - a[1]).slice(0, 4), s = top.reduce((t, e) => t + e[1], 0) || 1;
  for (let k = 0; k < 4; k++) { si.setComponent(i, k, top[k]?.[0] ?? 0); sw.setComponent(i, k, (top[k]?.[1] ?? 0) / s); }
}
const mixed = (a, b, k) => { const out = new Map(); for (const n of new Set([...a.keys(), ...b.keys()])) out.set(n, (1 - k) * (a.get(n) ?? 0) + k * (b.get(n) ?? 0)); return out; };

/**
 * Even out the outer coat's weights round each armpit, and give what lies under it there the
 * coat's new weights (see the head of this file). Returns { mesh, points, under: [{ mesh, points }] }
 * or null when the body has no EASE_FOLD coat.
 */
export function easeFold(root) {
  if (!root) return null;
  const outerName = root.userData.chicagoArmpits?.outer;
  const all = [];
  root.traverse((o) => { if (o.isSkinnedMesh && o.skeleton && o.geometry?.index) all.push(o); });
  const m = all.find((o) => o.name === outerName);
  if (!m || !EASE_FOLD.test(materialName(m))) return null;
  // the two near levels only: a far level's coat is too coarse to smooth (its few faces at the
  // shoulder fold as one, and smoothed they open round the shoulder), so it is left as drawn
  const lod = +(/_lod(\d+)$/.exec(m.name)?.[1] ?? 0);
  if (lod > 1) return null;
  const sk = m.skeleton, P = bindPositions(m), n = P.length / 3, idx = m.geometry.index.array;
  const J = { l: bindJoint(sk, 'upperarm_l'), r: bindJoint(sk, 'upperarm_r') }, hipL = bindJoint(sk, 'thigh_l'), hipR = bindJoint(sk, 'thigh_r'), neck = bindJoint(sk, 'neck_01');
  if (!J.l || !J.r || !hipL || !hipR || !neck) return null;
  const U = neck.clone().sub(hipL.clone().add(hipR).multiplyScalar(0.5)).normalize(), scale = J.l.distanceTo(J.r) / ADULT_SHOULDERS_M;
  const c = SIDES.map((s) => J[s].clone().addScaledVector(U, -FOLD.below * scale));
  const zoneOf = (x, y, z) => 1 - smooth((Math.min(...c.map((q) => Math.hypot(q.x - x, q.y - y, q.z - z))) - FOLD.full * scale) / ((FOLD.fade - FOLD.full) * scale));
  const { gid } = rimOf(P, idx);
  let G = 0; for (let i = 0; i < n; i++) G = Math.max(G, gid[i] + 1);
  const nb = Array.from({ length: G }, () => new Set());
  for (let t = 0; t < idx.length / 3; t++) for (let k = 0; k < 3; k++) { const a = gid[idx[t * 3 + k]], b = gid[idx[t * 3 + (k + 1) % 3]]; if (a !== b) { nb[a].add(b); nb[b].add(a); } }
  // Welded points as one (a UV seam's copies keep one set of weights).
  let W = new Array(G).fill(null);
  const zone = new Float64Array(G);
  for (let i = 0; i < n; i++) { const g = gid[i]; if (W[g]) continue; zone[g] = zoneOf(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]); W[g] = weightsOf(m, i); }
  for (let it = 0; it < FOLD.iterations; it++) {
    W = W.map((w, g) => {
      if (!(zone[g] > 1e-3) || !nb[g].size) return w;
      const mean = new Map();
      for (const o of nb[g]) for (const [b, x] of W[o]) mean.set(b, (mean.get(b) ?? 0) + x / nb[g].size);
      return mixed(w, mean, FOLD.rate * zone[g]);
    });
  }
  let points = 0;
  for (let i = 0; i < n; i++) if (zone[gid[i]] > 1e-3) { writeWeights(m, i, W[gid[i]]); points++; }
  m.geometry.attributes.skinIndex.needsUpdate = true; m.geometry.attributes.skinWeight.needsUpdate = true;
  const report = { mesh: m.name, points, under: [] };
  // What lies under it there folds with it: the coat's new weights at its nearest point.
  const cell = 0.02, grid = new Map(), key = (a, b, d) => `${a},${b},${d}`;
  for (let i = 0; i < n; i++) {
    if (!(zone[gid[i]] > 1e-3)) continue;
    const k = key(Math.floor(P[i * 3] / cell), Math.floor(P[i * 3 + 1] / cell), Math.floor(P[i * 3 + 2] / cell));
    let l = grid.get(k); if (!l) grid.set(k, (l = [])); l.push(i);
  }
  const near = FOLD.near * scale, far = FOLD.far * scale, R = Math.ceil(far / cell);
  for (const u of all) {
    if (u === m || !/^(garment|skin)/.test(materialName(u)) || u.skeleton.bones.some((b, k) => sk.bones[k] !== b)) continue;
    const Q = bindPositions(u);
    let moved = 0;
    for (let i = 0; i < Q.length / 3; i++) {
      const x = Q[i * 3], y = Q[i * 3 + 1], z = Q[i * 3 + 2], zz = zoneOf(x, y, z);
      if (!(zz > 1e-3)) continue;
      let best = Infinity, bj = -1;
      const a = Math.floor(x / cell), b = Math.floor(y / cell), d = Math.floor(z / cell);
      for (let p = -R; p <= R; p++) for (let q = -R; q <= R; q++) for (let r = -R; r <= R; r++) {
        const l = grid.get(key(a + p, b + q, d + r)); if (!l) continue;
        for (const j of l) { const e = Math.hypot(P[j * 3] - x, P[j * 3 + 1] - y, P[j * 3 + 2] - z); if (e < best) { best = e; bj = j; } }
      }
      if (bj < 0 || best > far) continue;
      writeWeights(u, i, mixed(weightsOf(u, i), W[gid[bj]], zz * (1 - smooth((best - near) / (far - near)))));
      moved++;
    }
    if (!moved) continue;
    u.geometry.attributes.skinIndex.needsUpdate = true; u.geometry.attributes.skinWeight.needsUpdate = true;
    report.under.push({ mesh: u.name, points: moved });
  }
  return report;
}

/** All three, once per loaded body, before any figure is cloned (cloned figures share the result). */
export function fitCoats(root) {
  if (!root) return null;
  if (root.userData.chicagoCoats) return root.userData.chicagoCoats;
  const report = { armpits: fitArmpits(root), vents: closeVents(root) };
  report.fold = easeFold(root);
  root.userData.chicagoCoats = report;
  return report;
}
