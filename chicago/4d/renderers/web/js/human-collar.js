// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-collar.js — a collar, a strap or a belt lies OVER the cloth it is worn on (T-3553).
 *
 * The exporter cut each collar, strap and belt out of the faces of the garment it is worn
 * on, and at conversation distance the joins read as anything but a shirt collar: the maid's
 * white collar band and the cook's standing collar end in a stair of teeth a centimetre high
 * (their cut followed the faces' diagonals) that the black dress shows through; Peck's and the
 * trader's shirt points are ragged slivers; a soldier's or officer's standing collar has a
 * foot two or three centimetres deep that crosses the coat's neckline back and forth, so red
 * and blue (or blue and blue) interleave in a saw along the whole neck; the trader's white
 * neckcloth and his waistcoat interleave the same way; and on the walk the maid's broad strap
 * frills, the private's crossbelts and the collars, skinned to other bones than the cloth
 * beneath them, let that cloth rise through them.
 *
 * Here, once per loaded body (before any figure is cloned from it, as human-seat.js does), in
 * four passes per level:
 *  1. fairEdges: each listed piece's cut edges are faired, every edge point moved out across
 *     the edge to the outermost the edge reaches within FAIR_W of it, so the notches fill to
 *     the teeth (corners of the cut held; a far level whose edge would come out worse is left
 *     as drawn); the coat body's neckline is faired the same way;
 *  2. settleCollar: a standing collar's foot below the coat's neckline is folded up onto it,
 *     so the collar stands on the neckline instead of threading through it;
 *  3. followWeights: cloth worn on a garment takes that garment's skin weights where it lies
 *     on it (within FOLLOW_M, fading out by FOLLOW_FADE_M), so the two move as one cloth;
 *  4. tuckUnder: the cloth beneath (LAYERS) is tucked GAP_M inside what is worn over it,
 *     never nearer the skin than SKIN_GAP_M, fading out past the cover's edge.
 * Topology and UVs are unchanged; skin weights change only on the `follow` pieces. Identity,
 * colours and silhouettes are kept: nothing moves more than FAIR_MAX_M (fairing),
 * SETTLE_MAX_M (a collar's foot) or the layer's `max` (a tuck).
 *
 * Cost: a few hundred to a few thousand vertices per level on the bodies that have these
 * pieces, once per parse (tens to a few hundred milliseconds a body; none on the rest). No
 * new geometry, texture, draw call or program. A reconstructed fit, as the garments' own cut
 * is (liberty L-collars-3553).
 */
import * as THREE from 'three';

const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const pieceName = (mesh, assetId) => {
  let n = mesh.name ?? '';
  if (assetId && n.startsWith(`${assetId}_`)) n = n.slice(assetId.length + 1);
  return n.replace(/_lod\d*$/, '');
};
const lodOf = (o) => (o.name ?? '').match(/_lod(\d*)$/)?.[1] ?? '';
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };

/**
 * The layers: each `over` piece is worn over each `under` piece of the same body (names
 * matched whole). Options: `gap`, `poke`, `max` (metres) override GAP_M, POKE_M, MAX_M for the
 * tuck; `follow` reweights the over piece as the under one; `settle` stands a collar on the
 * coat's neckline; `cover` draws a collar down over the dress's stand (coverStand); `hug` closes
 * a child's collar at the front and draws it in to the neck (hugNeck); `near` dresses the
 * nearest level only; `byEye` is tucked but judged by eye, not measured, by
 * tools/test_human_collar.mjs.
 */
export const LAYERS = Object.freeze([
  // the maid's white collar band, apron bib, straps and their frills, over the black dress
  // (round 4: drawn down over the dress's whole stand first, `cover`, so it reads as a white
  // collar and not a sliver at the stand's top edge)
  Object.freeze({ over: /^(white_collar|standing_collar)$/, under: /^(maid_bodice|plain_closed_bodice)$/, cover: true, follow: true, poke: 0.015, max: 0.015, gap: 0.006 }),
  Object.freeze({ over: /^(apron_bib|apron_straps)$/, under: /^(maid_bodice|plain_closed_bodice)$/, near: true }),
  // the broad frills lie on the shoulder seam, where the dress's shoulder rises through them
  // (and are skinned as the dress beneath them, so they move with it on the walk)
  Object.freeze({ over: /^apron_strap_frills$/, under: /^maid_bodice$/, poke: 0.012, max: 0.012, gap: 0.008, follow: true, near: true }),
  // the private's crossbelts over his coat and the foot of his collar; a soldier's or officer's
  // standing collar settled on the coat it is sewn to, over the coat's neckline
  Object.freeze({ over: /^crossbelts$/, under: /^coat_body$/, follow: true }),
  // (where the belts pass the collar's foot the two lie nearly in one surface, and which shows
  // is read by eye, not measured: `byEye`)
  Object.freeze({ over: /^crossbelts$/, under: /^coat_collar_red$/, byEye: true }),
  Object.freeze({ over: /^(coat_collar|coat_collar_red)$/, under: /^coat_body$/, settle: true, follow: true, gap: 0.007 }),
  // the 1812 trader's neckcloth tucked into his waistcoat
  Object.freeze({ over: /^waistcoat_yellow$/, under: /^white_neckcloth$/ }),
  // the children's collars over the jacket or frock; the 1812 girl's pinafore bib over her frock
  // (round 4: the 1904 children's collars closed at the front and drawn in to the neck, `hug`)
  Object.freeze({ over: /^child_collar$/, under: /^(child_jacket|frock_bodice)$/, hug: true }),
  Object.freeze({ over: /^(shirt_collar|pinafore_bib)$/, under: /^(child_jacket|frock_bodice|skeleton_jacket)$/ }),
]);

/** Clearance kept between the under cloth and the cloth over it, metres. */
export const GAP_M = 0.003;
/** Searched this far either side of the under cloth for the cloth over it. */
export const REACH_M = 0.035;
/** The under cloth never comes nearer the skin than this. */
export const SKIN_GAP_M = 0.0015;
/** No point moves further than this. */
export const MAX_M = 0.008;
/** An under point further out than this through the cloth over it is not a poke but the cut. */
export const POKE_M = 0.005;
/** Beyond the edge of the cloth over it, the tuck fades over this many of the under cloth's own edges. */
export const MARGIN_EDGES = 1.5;
const CELL = 0.01;

function bindPositions(mesh) {
  const pos = mesh.geometry.attributes.position, n = pos.count, P = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function indexOf(mesh) {
  const g = mesh.geometry;
  if (g.index) return g.index.array;
  const a = new Uint32Array(g.attributes.position.count); for (let i = 0; i < a.length; i++) a[i] = i; return a;
}

/** Triangles of several meshes at bind, in a grid, for rays. */
function triGrid(meshes) {
  const P = [], T = [];
  let base = 0;
  for (const m of meshes) {
    const p = bindPositions(m), idx = indexOf(m);
    for (let i = 0; i < p.length; i++) P.push(p[i]);
    for (let i = 0; i < idx.length; i++) T.push(idx[i] + base);
    base += p.length / 3;
  }
  const map = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let t = 0; t < T.length / 3; t++) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let c = 0; c < 3; c++) for (let k = 0; k < 3; k++) { const x = P[T[t * 3 + c] * 3 + k]; lo[k] = Math.min(lo[k], x); hi[k] = Math.max(hi[k], x); }
    for (let a = Math.floor(lo[0] / CELL); a <= Math.floor(hi[0] / CELL); a++)
      for (let b = Math.floor(lo[1] / CELL); b <= Math.floor(hi[1] / CELL); b++)
        for (let c = Math.floor(lo[2] / CELL); c <= Math.floor(hi[2] / CELL); c++) {
          const k = key(a, b, c); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(t);
        }
  }
  return { P, T, map, key };
}
/** Every t in [-L, L] where o + t d meets the grid's triangles, with the hit triangle's |cos| to d. */
function cast(g, o, d, L) {
  const seen = new Set(), out = [];
  const steps = Math.ceil((2 * L) / (CELL * 0.5));
  for (let s = 0; s <= steps; s++) {
    const t = -L + (2 * L * s) / steps;
    const l = g.map.get(g.key(Math.floor((o[0] + d[0] * t) / CELL), Math.floor((o[1] + d[1] * t) / CELL), Math.floor((o[2] + d[2] * t) / CELL)));
    if (!l) continue;
    for (const tri of l) {
      if (seen.has(tri)) continue; seen.add(tri);
      const r = rayTri(g.P, g.T, tri, o, d);
      if (r && r[0] >= -L && r[0] <= L) out.push(r);
    }
  }
  return out;
}
function rayTri(P, T, t, o, d) {
  const a = T[t * 3] * 3, b = T[t * 3 + 1] * 3, c = T[t * 3 + 2] * 3;
  const e1x = P[b] - P[a], e1y = P[b + 1] - P[a + 1], e1z = P[b + 2] - P[a + 2];
  const e2x = P[c] - P[a], e2y = P[c + 1] - P[a + 1], e2z = P[c + 2] - P[a + 2];
  const px = d[1] * e2z - d[2] * e2y, py = d[2] * e2x - d[0] * e2z, pz = d[0] * e2y - d[1] * e2x;
  const det = e1x * px + e1y * py + e1z * pz;
  if (Math.abs(det) < 1e-14) return null;
  const inv = 1 / det, sx = o[0] - P[a], sy = o[1] - P[a + 1], sz = o[2] - P[a + 2];
  const u = (sx * px + sy * py + sz * pz) * inv; if (u < -1e-9 || u > 1 + 1e-9) return null;
  const qx = sy * e1z - sz * e1y, qy = sz * e1x - sx * e1z, qz = sx * e1y - sy * e1x;
  const v = (d[0] * qx + d[1] * qy + d[2] * qz) * inv; if (v < -1e-9 || u + v > 1 + 1e-9) return null;
  const nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
  const cos = Math.abs(nx * d[0] + ny * d[1] + nz * d[2]) / (Math.hypot(nx, ny, nz) || 1);
  return [(e2x * qx + e2y * qy + e2z * qz) * inv, cos];
}

/**
 * Tuck one under garment beneath the cloth worn over it: every point of it under that cloth
 * goes in (toward the skin, along its own outward normal) until it is GAP_M inside it, never
 * nearer the skin than SKIN_GAP_M; the tuck fades out past the cloth's edge over MARGIN_EDGES
 * of the under cloth's own edges, so no triangle reaching out from under the edge rises
 * through it. Returns { moved, max_m, short_m } or null.
 */
export function tuckUnder(under, covers, skin, { poke = POKE_M, max = MAX_M, gap = GAP_M } = {}) {
  if (!under?.isSkinnedMesh || !covers.length) return null;
  const geo = under.geometry, pos = geo.attributes.position, nrm = geo.attributes.normal, n = pos.count;
  if (!nrm) return null;
  const P = bindPositions(under), idx = indexOf(under);
  // Welded points: a UV seam's copies move as one.
  const keyOf = (i) => `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`;
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) { const k = keyOf(i); let g = keys.get(k); if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); } groupOf[i] = g; }
  const G = first.length;
  // Outward normal per point (bind space), the mean of its copies.
  const N = new Float64Array(G * 3), nb = new THREE.Matrix3().getNormalMatrix(under.bindMatrix), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(nrm, i).applyMatrix3(nb); const g = groupOf[i]; N[g * 3] += v.x; N[g * 3 + 1] += v.y; N[g * 3 + 2] += v.z; }
  for (let g = 0; g < G; g++) { const l = Math.hypot(N[g * 3], N[g * 3 + 1], N[g * 3 + 2]) || 1; N[g * 3] /= l; N[g * 3 + 1] /= l; N[g * 3 + 2] /= l; }
  const over = triGrid(covers), body = skin ? triGrid([skin]) : null;
  // In: away from the nearest skin (a rim's own normal points along the cloth, not out of it).
  const out = skinNear(skin);
  if (out) for (let g = 0; g < G; g++) {
    const i = first[g], d = out(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]);
    if (d && d[0] * N[g * 3] + d[1] * N[g * 3 + 1] + d[2] * N[g * 3 + 2] > -0.2) for (let k = 0; k < 3; k++) N[g * 3 + k] = d[k];
  }
  // How far each point must go in.
  const need = new Float64Array(G), room = new Float64Array(G).fill(max), covered = new Uint8Array(G);
  for (let g = 0; g < G; g++) {
    const i = first[g], o = [P[i * 3], P[i * 3 + 1], P[i * 3 + 2]], d = [N[g * 3], N[g * 3 + 1], N[g * 3 + 2]];
    const hits = cast(over, o, d, REACH_M).filter((h) => h[1] > 0.25);
    if (!hits.length) continue;
    const inner = Math.min(...hits.map((h) => h[0]));
    // Further out than POKE_M, the under cloth is not coming through: it lies over that piece
    // there by its cut (a collar's foot under a coat's front), and is left as it is.
    if (inner < -poke) continue;
    covered[g] = 1;
    need[g] = Math.max(0, gap - inner);
    if (body) {
      const s = cast(body, o, d, REACH_M).filter((h) => h[0] < 0).map((h) => -h[0]);
      if (s.length) room[g] = Math.max(0, Math.min(max, Math.min(...s) - SKIN_GAP_M));
    }
  }
  // The under cloth's own edge length, for the margin past the cover's edge.
  const nbr = Array.from({ length: G }, () => new Set());
  let elen = 0, ecount = 0;
  for (let t = 0; t < idx.length / 3; t++) {
    const q = [groupOf[idx[t * 3]], groupOf[idx[t * 3 + 1]], groupOf[idx[t * 3 + 2]]];
    for (let c = 0; c < 3; c++) {
      const a = q[c], b = q[(c + 1) % 3]; if (a === b) continue;
      if (!nbr[a].has(b)) { nbr[a].add(b); nbr[b].add(a); const ia = first[a], ib = first[b]; elen += Math.hypot(P[ia * 3] - P[ib * 3], P[ia * 3 + 1] - P[ib * 3 + 1], P[ia * 3 + 2] - P[ib * 3 + 2]); ecount++; }
    }
  }
  const margin = MARGIN_EDGES * (ecount ? elen / ecount : 0.01);
  // Spread the tuck past the cover's edge: Dijkstra-ish over the mesh from the covered points.
  const push = new Float64Array(G);
  for (let g = 0; g < G; g++) if (covered[g]) push[g] = Math.min(need[g], room[g]);
  const dist = new Float64Array(G).fill(Infinity), src = new Float64Array(G);
  const queue = [];
  for (let g = 0; g < G; g++) if (covered[g] && push[g] > 0) { dist[g] = 0; src[g] = push[g]; queue.push(g); }
  while (queue.length) {
    const g = queue.shift();
    for (const o of nbr[g]) {
      if (covered[o]) continue;
      const ia = first[g], ib = first[o];
      const dd = dist[g] + Math.hypot(P[ia * 3] - P[ib * 3], P[ia * 3 + 1] - P[ib * 3 + 1], P[ia * 3 + 2] - P[ib * 3 + 2]);
      if (dd > margin) continue;
      const val = src[g] * smooth(1 - dd / margin);
      if (val > push[o] + 1e-6 || dd < dist[o] - 1e-9) {
        if (val > push[o]) push[o] = Math.min(val, room[o]);
        if (dd < dist[o]) { dist[o] = dd; src[o] = src[g]; queue.push(o); }
      }
    }
  }
  let moved = 0, far = 0, short = 0;
  for (let g = 0; g < G; g++) {
    if (covered[g]) short = Math.max(short, need[g] - push[g]);
    if (push[g] < 1e-5) { push[g] = 0; continue; }
    moved++; far = Math.max(far, push[g]);
  }
  if (!moved) return { moved: 0, max_m: 0, short_m: short };
  // Move, in the geometry's own space.
  const Binv = under.bindMatrix.clone().invert(), p = new THREE.Vector3();
  const Q = new Float64Array(G * 3);
  for (let g = 0; g < G; g++) { const i = first[g]; for (let k = 0; k < 3; k++) Q[g * 3 + k] = P[i * 3 + k] - push[g] * N[g * 3 + k]; }
  for (let i = 0; i < n; i++) {
    const g = groupOf[i]; if (!push[g]) continue;
    p.set(Q[g * 3], Q[g * 3 + 1], Q[g * 3 + 2]).applyMatrix4(Binv);
    pos.setXYZ(i, p.x, p.y, p.z);
  }
  pos.needsUpdate = true;
  renormal(under, idx, groupOf, push, Q, Binv);
  geo.computeBoundingBox(); geo.computeBoundingSphere();
  return { moved, max_m: far, short_m: short };
}

/** The normals of moved points from their faces, each face turned to the side the point's old normal faced. */
function renormal(mesh, idx, groupOf, push, Q, Binv) {
  const nrm = mesh.geometry.attributes.normal, n = groupOf.length;
  const nb = new THREE.Matrix3().getNormalMatrix(mesh.bindMatrix), back = new THREE.Matrix3().getNormalMatrix(Binv);
  const old = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(nrm, i).applyMatrix3(nb).normalize(); old[i * 3] = v.x; old[i * 3 + 1] = v.y; old[i * 3 + 2] = v.z; }
  const sum = new Float64Array(n * 3);
  for (let t = 0; t < idx.length / 3; t++) {
    const c = [idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]], g = c.map((i) => groupOf[i]);
    if (!g.some((x) => push[x])) continue;
    const A = g[0] * 3, B = g[1] * 3, C = g[2] * 3;
    const e1 = [Q[B] - Q[A], Q[B + 1] - Q[A + 1], Q[B + 2] - Q[A + 2]], e2 = [Q[C] - Q[A], Q[C + 1] - Q[A + 1], Q[C + 2] - Q[A + 2]];
    const f = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    for (const i of c) {
      const s = Math.sign(f[0] * old[i * 3] + f[1] * old[i * 3 + 1] + f[2] * old[i * 3 + 2]) || 1;
      sum[i * 3] += s * f[0]; sum[i * 3 + 1] += s * f[1]; sum[i * 3 + 2] += s * f[2];
    }
  }
  // copies of one point share one normal only where they shared one before (a crease keeps its two)
  for (let i = 0; i < n; i++) {
    if (!push[groupOf[i]]) continue;
    v.set(sum[i * 3], sum[i * 3 + 1], sum[i * 3 + 2]);
    if (v.lengthSq() < 1e-24) continue;
    v.normalize().applyMatrix3(back).normalize();
    nrm.setXYZ(i, v.x, v.y, v.z);
  }
  nrm.needsUpdate = true;
}

/** Pieces whose cut edge is faired (a stair left where they were cut out of a garment's faces). */
export const FAIR = /^(white_collar|apron_bib|apron_straps|apron_strap_frills|coat_collar|coat_collar_red|crossbelts|child_collar|shirt_collar|pinafore_bib|standing_collar|shirt_collar_points)$/;
/** Garments whose neckline alone is faired (it lies over the foot of a collar sewn into it). */
export const FAIR_NECK = /^coat_body$/;
const NECK_R = 0.12;
function neckOf(mesh) {
  const sk = mesh.skeleton, i = sk?.bones.findIndex((b) => b?.name === 'neck_01');
  if (!(i >= 0)) return null;
  return { at: new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert()), r: NECK_R };
}
/** Fairing: the edge is read over this arc (metres, along it), filled out to the outermost
 * of it, and never moved more than FAIR_MAX_M; a turn sharper than CORNER_DEG over the window
 * is a corner of the cut and is held. */
export const FAIR_W = 0.016, FAIR_SIGMA = 0.01, THICK_M = 0.004, FAIR_MAX_M = 0.016, CORNER_DEG = 60;

/** Welded points of a mesh at bind: groups, positions, normals, and its boundary loops. */
export function weld(mesh) {
  const pos = mesh.geometry.attributes.position, nrm = mesh.geometry.attributes.normal, n = pos.count;
  const P0 = bindPositions(mesh), idx = indexOf(mesh);
  const keyOf = (i) => `${Math.round(P0[i * 3] * 2e4)},${Math.round(P0[i * 3 + 1] * 2e4)},${Math.round(P0[i * 3 + 2] * 2e4)}`;
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) { const k = keyOf(i); let g = keys.get(k); if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); } groupOf[i] = g; }
  const G = first.length, P = new Float64Array(G * 3), N = new Float64Array(G * 3);
  const nb = new THREE.Matrix3().getNormalMatrix(mesh.bindMatrix), v = new THREE.Vector3();
  for (let g = 0; g < G; g++) for (let k = 0; k < 3; k++) P[g * 3 + k] = P0[first[g] * 3 + k];
  if (nrm) for (let i = 0; i < n; i++) { v.fromBufferAttribute(nrm, i).applyMatrix3(nb); const g = groupOf[i]; N[g * 3] += v.x; N[g * 3 + 1] += v.y; N[g * 3 + 2] += v.z; }
  for (let g = 0; g < G; g++) { const l = Math.hypot(N[g * 3], N[g * 3 + 1], N[g * 3 + 2]) || 1; N[g * 3] /= l; N[g * 3 + 1] /= l; N[g * 3 + 2] /= l; }
  const edges = new Map(), third = new Map();
  for (let t = 0; t < idx.length / 3; t++) for (let c = 0; c < 3; c++) {
    const a = groupOf[idx[t * 3 + c]], b = groupOf[idx[t * 3 + (c + 1) % 3]], o = groupOf[idx[t * 3 + (c + 2) % 3]];
    if (a === b) continue;
    const k = a < b ? `${a},${b}` : `${b},${a}`;
    edges.set(k, (edges.get(k) ?? 0) + 1); third.set(k, o);
  }
  const adj = new Map();
  for (const [k, c] of edges) {
    if (c !== 1) continue;
    const [a, b] = k.split(',').map(Number);
    if (!adj.has(a)) adj.set(a, []); if (!adj.has(b)) adj.set(b, []);
    adj.get(a).push(b); adj.get(b).push(a);
  }
  const loops = [], seen = new Set();
  for (const s0 of adj.keys()) {
    if (seen.has(s0) || adj.get(s0).length !== 2) continue;
    const loop = [s0]; seen.add(s0);
    let prev = -1, cur = s0, closed = false;
    for (;;) {
      const nx = adj.get(cur).filter((x) => x !== prev);
      if (adj.get(cur).length !== 2) break;
      const next = nx[0];
      if (next === s0) { closed = true; break; }
      if (seen.has(next) || adj.get(next)?.length !== 2) break;
      loop.push(next); seen.add(next); prev = cur; cur = next;
    }
    if (closed && loop.length >= 6) loops.push(loop);
  }
  // Inward, for a boundary point: toward the third corner of its boundary edge's triangle.
  const inward = (a, b) => third.get(a < b ? `${a},${b}` : `${b},${a}`);
  return { groupOf, first, G, P, N, idx, loops, inward, boundary: adj };
}

/** Gaussian-smoothed closed curve and its tangent. Distance along it is measured the second
 * time round along the smoothed curve's own direction, so a stair's risers (steps across the
 * edge) add nothing to it. */
function smoothLoop(P, loop, sigma) {
  const m = loop.length;
  let s = new Float64Array(m + 1);
  for (let i = 0; i < m; i++) { const a = loop[i] * 3, b = loop[(i + 1) % m] * 3; s[i + 1] = s[i] + Math.hypot(P[b] - P[a], P[b + 1] - P[a + 1], P[b + 2] - P[a + 2]); }
  let C = null, T = null;
  for (let pass = 0; pass < 3; pass++) {
    const L = s[m];
    C = new Float64Array(m * 3);
    for (let i = 0; i < m; i++) {
      let w = 0; const acc = [0, 0, 0];
      for (let j = 0; j < m; j++) {
        let d = Math.abs(s[j] - s[i]); d = Math.min(d, L - d);
        if (d > 3 * sigma) continue;
        const wj = Math.exp(-(d * d) / (2 * sigma * sigma));
        for (let k = 0; k < 3; k++) acc[k] += wj * P[loop[j] * 3 + k];
        w += wj;
      }
      for (let k = 0; k < 3; k++) C[i * 3 + k] = acc[k] / w;
    }
    T = new Float64Array(m * 3);
    for (let i = 0; i < m; i++) {
      const a = (i - 1 + m) % m, b = (i + 1) % m;
      const t = [C[b * 3] - C[a * 3], C[b * 3 + 1] - C[a * 3 + 1], C[b * 3 + 2] - C[a * 3 + 2]], tl = Math.hypot(...t) || 1;
      for (let k = 0; k < 3; k++) T[i * 3 + k] = t[k] / tl;
    }
    const u = new Float64Array(m + 1);
    for (let i = 0; i < m; i++) {
      const a = loop[i] * 3, b = loop[(i + 1) % m] * 3, j = (i + 1) % m;
      const tx = T[i * 3] + T[j * 3], ty = T[i * 3 + 1] + T[j * 3 + 1], tz = T[i * 3 + 2] + T[j * 3 + 2], tl = Math.hypot(tx, ty, tz) || 1;
      u[i + 1] = u[i] + Math.max(0, ((P[b] - P[a]) * tx + (P[b + 1] - P[a + 1]) * ty + (P[b + 2] - P[a + 2]) * tz) / tl);
    }
    s = u;
  }
  return { s, L: s[m], C, T };
}

/** Nearest skin points, for the outward direction at a point of the cloth. */
function skinNear(skin) {
  if (!skin) return null;
  const P = bindPositions(skin), cell = 0.02, map = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let i = 0; i < P.length; i += 3) { const k = key(Math.floor(P[i] / cell), Math.floor(P[i + 1] / cell), Math.floor(P[i + 2] / cell)); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(i); }
  return (x, y, z) => {
    let best = Infinity, bi = -1;
    const a = Math.floor(x / cell), b = Math.floor(y / cell), c = Math.floor(z / cell);
    for (let r = 1; r <= 4 && bi < 0; r++) {
      for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) for (let k = -r; k <= r; k++) {
        const l = map.get(key(a + i, b + j, c + k)); if (!l) continue;
        for (const q of l) { const d = (P[q] - x) ** 2 + (P[q + 1] - y) ** 2 + (P[q + 2] - z) ** 2; if (d < best) { best = d; bi = q; } }
      }
    }
    if (bi < 0) return null;
    const v = [x - P[bi], y - P[bi + 1], z - P[bi + 2]], l = Math.hypot(...v);
    return l > 1e-5 ? v.map((t) => t / l) : null;
  };
}

/**
 * Fair one piece's cut edges. Where a collar, a strap or a belt was cut out of a garment's
 * faces, its edge follows the faces' diagonals: a stair of teeth a centimetre high that the
 * cloth beneath shows through. Along each boundary loop, every point is moved out across the
 * edge (square to the edge, in the cloth's surface: across the outward direction from the
 * body) to the outermost the edge reaches within FAIR_W of it, so the notches are filled to the
 * teeth and the edge runs smooth; a turn sharper than CORNER_DEG (a corner of the cut, a
 * collar's front opening) is held. The cloth's thickness (the cap round a thin slab's edge)
 * moves with its edge. Returns { moved, max_m, loops } or null.
 */
export function fairEdges(mesh, skin = null, { around = null } = {}) {
  if (!mesh?.isSkinnedMesh) return null;
  const W = weld(mesh), { P, loops, G } = W;
  const out = skinNear(skin);
  const shift = new Float64Array(G * 3), onLoop = new Uint8Array(G);
  // a grid of the piece's points, for the side the cloth lies on and the slab's thickness
  const cell = 0.01, grid = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let g = 0; g < G; g++) { const k = key(Math.floor(P[g * 3] / cell), Math.floor(P[g * 3 + 1] / cell), Math.floor(P[g * 3 + 2] / cell)); let l = grid.get(k); if (!l) grid.set(k, (l = [])); l.push(g); }
  const near = (x, y, z, r, f) => {
    const n = Math.ceil(r / cell), a = Math.floor(x / cell), b = Math.floor(y / cell), c = Math.floor(z / cell);
    for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) for (let k = -n; k <= n; k++) {
      const l = grid.get(key(a + i, b + j, c + k)); if (!l) continue;
      for (const g of l) { const d = Math.hypot(P[g * 3] - x, P[g * 3 + 1] - y, P[g * 3 + 2] - z); if (d <= r) f(g, d); }
    }
  };
  let moved = 0, far = 0;
  const loopShift = [];
  for (const loop of loops) {
    for (const g of loop) onLoop[g] = 1;
    if (around) {
      // only the loop round the neck: its middle within `around.r` of the neck joint
      const c = [0, 0, 0]; for (const g of loop) for (let k = 0; k < 3; k++) c[k] += P[g * 3 + k] / loop.length;
      if (Math.hypot(c[0] - around.at.x, c[1] - around.at.y, c[2] - around.at.z) > around.r) continue;
    }
    const m = loop.length, { s, L, C, T } = smoothLoop(P, loop, FAIR_SIGMA);
    if (L < 4 * FAIR_W) continue;
    // Across the edge, outward (away from the cloth): square to the smoothed edge and to the
    // outward direction from the body; turned away from the cloth near the point.
    const B = new Float64Array(m * 3), e = new Float64Array(m);
    for (let i = 0; i < m; i++) {
      const g = loop[i], x = P[g * 3], y = P[g * 3 + 1], z = P[g * 3 + 2];
      const c = [0, 0, 0]; let cn = 0;
      near(x, y, z, FAIR_W * 1.5, (q) => { c[0] += P[q * 3]; c[1] += P[q * 3 + 1]; c[2] += P[q * 3 + 2]; cn++; });
      let b = [x - c[0] / cn, y - c[1] / cn, z - c[2] / cn];
      const t = b[0] * T[i * 3] + b[1] * T[i * 3 + 1] + b[2] * T[i * 3 + 2];
      b = [b[0] - t * T[i * 3], b[1] - t * T[i * 3 + 1], b[2] - t * T[i * 3 + 2]];
      const bl = Math.hypot(...b) || 1; b = b.map((v) => v / bl);
      for (let k = 0; k < 3; k++) B[i * 3 + k] = b[k];
    }
    // smooth the direction along the edge (a riser's own point must not swing it)
    const Bs = new Float64Array(m * 3);
    for (let i = 0; i < m; i++) {
      const acc = [0, 0, 0];
      for (let j = 0; j < m; j++) {
        let d = Math.abs(s[j] - s[i]); d = Math.min(d, L - d);
        if (d > 2 * FAIR_SIGMA) continue;
        const w = Math.exp(-(d * d) / (2 * FAIR_SIGMA * FAIR_SIGMA));
        for (let k = 0; k < 3; k++) acc[k] += w * B[j * 3 + k];
      }
      const t = acc[0] * T[i * 3] + acc[1] * T[i * 3 + 1] + acc[2] * T[i * 3 + 2];
      for (let k = 0; k < 3; k++) acc[k] -= t * T[i * 3 + k];
      const l = Math.hypot(...acc) || 1;
      for (let k = 0; k < 3; k++) Bs[i * 3 + k] = acc[k] / l;
      const g = loop[i];
      e[i] = (P[g * 3] - C[i * 3]) * Bs[i * 3] + (P[g * 3 + 1] - C[i * 3 + 1]) * Bs[i * 3 + 1] + (P[g * 3 + 2] - C[i * 3 + 2]) * Bs[i * 3 + 2];
    }
    // The outermost the edge reaches near each point (smoothed); corners held.
    const env = new Float64Array(m), turn = new Float64Array(m);
    for (let i = 0; i < m; i++) {
      let hi = e[i];
      for (let j = 0; j < m; j++) { let d = Math.abs(s[j] - s[i]); d = Math.min(d, L - d); if (d <= FAIR_W) hi = Math.max(hi, e[j]); }
      env[i] = hi;
      let ia = i, ib = i, da = 0, db = 0;
      while (da < FAIR_W && ia !== (i + 1) % m) { const q = (ia - 1 + m) % m; da += ia === 0 ? s[m] - s[q] : s[ia] - s[q]; ia = q; }
      while (db < FAIR_W && ib !== (i - 1 + m) % m) { const q = (ib + 1) % m; db += q === 0 ? s[m] - s[ib] : s[q] - s[ib]; ib = q; }
      const dot = T[ia * 3] * T[ib * 3] + T[ia * 3 + 1] * T[ib * 3 + 1] + T[ia * 3 + 2] * T[ib * 3 + 2];
      turn[i] = Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI;
    }
    const envS = new Float64Array(m);
    for (let i = 0; i < m; i++) {
      let w = 0, acc = 0;
      for (let j = 0; j < m; j++) { let d = Math.abs(s[j] - s[i]); d = Math.min(d, L - d); if (d > 2 * FAIR_SIGMA) continue; const wj = Math.exp(-(d * d) / (2 * (FAIR_SIGMA / 2) ** 2)); acc += wj * env[j]; w += wj; }
      envS[i] = acc / w;
    }
    for (let i = 0; i < m; i++) {
      let d = Math.max(0, envS[i] - e[i]);
      d *= 1 - smooth((turn[i] - CORNER_DEG) / 20);
      d = Math.min(d, FAIR_MAX_M);
      if (d < 2e-4) continue;
      loopShift.push([loop[i], d * Bs[i * 3], d * Bs[i * 3 + 1], d * Bs[i * 3 + 2]]);
    }
  }
  // Each moved edge point carries the cloth within the slab's thickness of it (the cap and the
  // outer sheet's last row) with it; a point carried by two takes the larger.
  const best = new Float64Array(G).fill(Infinity);
  for (const [g, dx, dy, dz] of loopShift) {
    near(P[g * 3], P[g * 3 + 1], P[g * 3 + 2], THICK_M, (q, d) => {
      if (onLoop[q] && q !== g) return;
      const len = Math.hypot(dx, dy, dz);
      if (len > Math.hypot(shift[q * 3], shift[q * 3 + 1], shift[q * 3 + 2]) || (q === g && best[q] > 0)) {
        shift[q * 3] = dx; shift[q * 3 + 1] = dy; shift[q * 3 + 2] = dz; if (q === g) best[q] = 0;
      }
    });
  }
  for (let g = 0; g < G; g++) { const l = Math.hypot(shift[g * 3], shift[g * 3 + 1], shift[g * 3 + 2]); if (l > 1e-6) { moved++; far = Math.max(far, l); } }
  if (!moved) return { moved: 0, max_m: 0, loops: loops.length };
  // A coarse far level's edge has no stair to fair; where fairing would leave more steps than
  // the edge had (its few points swung across), the piece is left as drawn.
  const Q = Float64Array.from(P, (v, i) => v + shift[i]);
  const before = stepLength(P, loops), after = stepLength(Q, loops);
  if (after > before * 0.8) return { moved: 0, max_m: 0, loops: loops.length, kept: true };
  apply(mesh, W, shift);
  return { moved, max_m: far, loops: loops.length };
}

/** Total length of an edge's steps: boundary edges over 3 mm running more than 60 degrees off the
 * edge's course (1.5 cm either side; a corner, where the course itself turns, is not a step). */
function stepLength(P, loops) {
  let total = 0;
  for (const loop of loops) {
    const m = loop.length;
    const seg = loop.map((g, i) => { const b = loop[(i + 1) % m]; return [P[b * 3] - P[g * 3], P[b * 3 + 1] - P[g * 3 + 1], P[b * 3 + 2] - P[g * 3 + 2]]; });
    const len = seg.map((d) => Math.hypot(...d));
    for (let i = 0; i < m; i++) {
      if (len[i] < 0.003) continue;
      const fore = [0, 0, 0], aft = [0, 0, 0];
      for (let k = 1, s = 0; k < m && s < 0.015; k++) { const j = (i + k) % m; for (let c = 0; c < 3; c++) fore[c] += seg[j][c]; s += len[j]; }
      for (let k = 1, s = 0; k < m && s < 0.015; k++) { const j = (i - k + m) % m; for (let c = 0; c < 3; c++) aft[c] += seg[j][c]; s += len[j]; }
      const fl = Math.hypot(...fore), al = Math.hypot(...aft); if (fl < 1e-6 || al < 1e-6) continue;
      if ((fore[0] * aft[0] + fore[1] * aft[1] + fore[2] * aft[2]) / (fl * al) < Math.cos(40 * Math.PI / 180)) continue;
      const course = [fore[0] / fl + aft[0] / al, fore[1] / fl + aft[1] / al, fore[2] / fl + aft[2] / al], cl = Math.hypot(...course);
      if (Math.abs((seg[i][0] * course[0] + seg[i][1] * course[1] + seg[i][2] * course[2]) / (len[i] * cl)) < 0.5) total += len[i];
    }
  }
  return total;
}

/** Cloth worn on another takes its skin weights within FOLLOW_M of it, fading to its own by FOLLOW_FADE_M. */
export const FOLLOW_M = 0.015, FOLLOW_FADE_M = 0.03;
/**
 * Skin the cloth worn over a garment as that garment where it lies on it: each point within
 * FOLLOW_M of the garment beneath takes the weights of the garment's nearest point, fading back
 * to its own by FOLLOW_FADE_M, so the two move as one cloth (a frill on a shoulder whose dress
 * was weighted more to the arm than the frill was rose through it as the arm swung). Returns
 * { moved: points reweighted } or null.
 */
export function followWeights(over, under) {
  const si = over.geometry.attributes.skinIndex, sw = over.geometry.attributes.skinWeight;
  const ui = under.geometry.attributes.skinIndex, uw = under.geometry.attributes.skinWeight;
  if (!si || !sw || !ui || !uw || over.skeleton !== under.skeleton && over.skeleton?.bones.some((b, k) => under.skeleton?.bones[k] !== b)) return null;
  const Po = bindPositions(over), Pu = bindPositions(under), cell = 0.02, grid = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let j = 0; j < Pu.length / 3; j++) { const k = key(Math.floor(Pu[j * 3] / cell), Math.floor(Pu[j * 3 + 1] / cell), Math.floor(Pu[j * 3 + 2] / cell)); let l = grid.get(k); if (!l) grid.set(k, (l = [])); l.push(j); }
  let moved = 0;
  for (let i = 0; i < Po.length / 3; i++) {
    const x = Po[i * 3], y = Po[i * 3 + 1], z = Po[i * 3 + 2], a = Math.floor(x / cell), b = Math.floor(y / cell), c = Math.floor(z / cell);
    let best = Infinity, bj = -1;
    for (let p = -2; p <= 2; p++) for (let q = -2; q <= 2; q++) for (let r = -2; r <= 2; r++) {
      const l = grid.get(key(a + p, b + q, c + r)); if (!l) continue;
      for (const j of l) { const d = Math.hypot(Pu[j * 3] - x, Pu[j * 3 + 1] - y, Pu[j * 3 + 2] - z); if (d < best) { best = d; bj = j; } }
    }
    if (bj < 0 || best >= FOLLOW_FADE_M) continue;
    const f = 1 - smooth((best - FOLLOW_M) / (FOLLOW_FADE_M - FOLLOW_M));
    const mix = new Map();
    for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k) * (1 - f); if (w > 0) mix.set(si.getComponent(i, k), (mix.get(si.getComponent(i, k)) ?? 0) + w); }
    for (let k = 0; k < 4; k++) { const w = uw.getComponent(bj, k) * f; if (w > 0) mix.set(ui.getComponent(bj, k), (mix.get(ui.getComponent(bj, k)) ?? 0) + w); }
    const top = [...mix].sort((p, q) => q[1] - p[1]).slice(0, 4), sum = top.reduce((t, e) => t + e[1], 0) || 1;
    for (let k = 0; k < 4; k++) { si.setComponent(i, k, top[k]?.[0] ?? 0); sw.setComponent(i, k, (top[k]?.[1] ?? 0) / sum); }
    moved++;
  }
  si.needsUpdate = true; sw.needsUpdate = true;
  return { moved, max_m: 0 };
}

/** A standing collar's foot sits this far down over the coat's neckline. */
export const SEAT_OVERLAP_M = 0.004;
/** …and no point of it goes further up its cloth than this. */
export const SETTLE_MAX_M = 0.05;
/**
 * Settle a standing collar on the coat it is sewn to. The soldiers' and officers' collars were
 * cut with a foot two or three centimetres deep that runs down outside the coat at the back and
 * inside it at the sides and front, so the two cloths cross back and forth along the neck and
 * the line where they meet is a sawtooth of red and blue. Here the foot is folded up onto the
 * coat's own neckline: every point of the collar lower than SEAT_OVERLAP_M under the neckline
 * at its place round the neck goes up its own cloth to that height, so the collar's lower edge
 * runs level on the coat all round (and the coat is then tucked under it).
 */
export function settleCollar(collar, coat) {
  if (!collar?.isSkinnedMesh || !coat?.isSkinnedMesh) return null;
  const neck = neckOf(collar);
  if (!neck) return null;
  const C = weld(collar), K = weld(coat), at = neck.at;
  // the coat's neckline: its boundary loop round the neck, as height by angle
  const BINS = 72, top = new Float64Array(BINS).fill(NaN);
  const angleBin = (x, z) => ((Math.floor(((Math.atan2(x - at.x, z - at.z) + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;
  for (const loop of K.loops) {
    const c = [0, 0, 0]; for (const g of loop) for (let k = 0; k < 3; k++) c[k] += K.P[g * 3 + k] / loop.length;
    if (Math.hypot(c[0] - at.x, c[1] - at.y, c[2] - at.z) > NECK_R) continue;
    for (const g of loop) { const b = angleBin(K.P[g * 3], K.P[g * 3 + 2]), y = K.P[g * 3 + 1]; top[b] = Number.isNaN(top[b]) ? y : Math.min(top[b], y); }
  }
  // fill the bins the loop does not reach (a front opening) from their neighbours, then smooth
  for (let pass = 0; pass < BINS && top.some(Number.isNaN); pass++) {
    const prev = top.slice();
    for (let b = 0; b < BINS; b++) if (Number.isNaN(prev[b])) { const l = prev[(b + BINS - 1) % BINS], r = prev[(b + 1) % BINS]; const v = [l, r].filter((x) => !Number.isNaN(x)); if (v.length) top[b] = v.reduce((a, x) => a + x, 0) / v.length; }
  }
  if (top.some(Number.isNaN)) return null;
  const line = new Float64Array(BINS);
  for (let b = 0; b < BINS; b++) { let acc = 0, w = 0; for (let k = -3; k <= 3; k++) { const wk = Math.exp(-(k * k) / 4); acc += wk * top[(b + k + BINS) % BINS]; w += wk; } line[b] = acc / w - SEAT_OVERLAP_M; }
  // each point under the line goes up its own cloth: along the steepest way up its edges
  const nbr = Array.from({ length: C.G }, () => []);
  for (let t = 0; t < C.idx.length / 3; t++) for (let c = 0; c < 3; c++) {
    const a = C.groupOf[C.idx[t * 3 + c]], b = C.groupOf[C.idx[t * 3 + (c + 1) % 3]];
    if (a !== b) { nbr[a].push(b); nbr[b].push(a); }
  }
  const P = C.P, shift = new Float64Array(C.G * 3);
  let moved = 0, far = 0;
  for (let g = 0; g < C.G; g++) {
    const h = line[angleBin(P[g * 3], P[g * 3 + 2])];
    if (P[g * 3 + 1] >= h) continue;
    let cur = g, target = null;
    for (let step = 0; step < 12 && !target; step++) {
      let best = -1;
      for (const o of nbr[cur]) if (best < 0 || P[o * 3 + 1] > P[best * 3 + 1]) best = o;
      if (best < 0 || P[best * 3 + 1] <= P[cur * 3 + 1] + 1e-6) break;
      if (P[best * 3 + 1] >= h) {
        const t = (h - P[cur * 3 + 1]) / (P[best * 3 + 1] - P[cur * 3 + 1]);
        target = [0, 1, 2].map((k) => P[cur * 3 + k] + t * (P[best * 3 + k] - P[cur * 3 + k]));
      } else cur = best;
    }
    if (!target || Math.hypot(target[0] - P[g * 3], target[1] - P[g * 3 + 1], target[2] - P[g * 3 + 2]) > SETTLE_MAX_M) continue;
    for (let k = 0; k < 3; k++) shift[g * 3 + k] = target[k] - P[g * 3 + k];
    moved++; far = Math.max(far, Math.hypot(shift[g * 3], shift[g * 3 + 1], shift[g * 3 + 2]));
  }
  if (!moved) return { moved: 0, max_m: 0 };
  apply(collar, C, shift);
  return { moved, max_m: far };
}

/** Move welded points by a bind-space shift, then renormal the moved points from their faces. */
function apply(mesh, W, shift) {
  const { groupOf, G, P, idx } = W, pos = mesh.geometry.attributes.position, n = pos.count;
  const Binv = mesh.bindMatrix.clone().invert(), p = new THREE.Vector3();
  const Q = new Float64Array(G * 3), push = new Float64Array(G);
  for (let g = 0; g < G; g++) { for (let k = 0; k < 3; k++) Q[g * 3 + k] = P[g * 3 + k] + shift[g * 3 + k]; push[g] = Math.hypot(shift[g * 3], shift[g * 3 + 1], shift[g * 3 + 2]) > 1e-6 ? 1 : 0; }
  for (let i = 0; i < n; i++) {
    const g = groupOf[i]; if (!push[g]) continue;
    p.set(Q[g * 3], Q[g * 3 + 1], Q[g * 3 + 2]).applyMatrix4(Binv);
    pos.setXYZ(i, p.x, p.y, p.z);
  }
  pos.needsUpdate = true;
  renormal(mesh, idx, groupOf, push, Q, Binv);
  mesh.geometry.computeBoundingBox(); mesh.geometry.computeBoundingSphere();
}

// ---- round 4: the maid's white collar, her strap frills, the children's necklines ----------

/** The neck's axis at bind: the middle (x, z) of a garment's neckline, the open loop round the
 * neck joint (or of all its points above the joint when it has none). */
function neckAxis(W, neck) {
  let best = null;
  for (const loop of W.loops) {
    const c = [0, 0, 0]; for (const g of loop) for (let k = 0; k < 3; k++) c[k] += W.P[g * 3 + k] / loop.length;
    const d = Math.hypot(c[0] - neck.x, c[2] - neck.z) + Math.abs(c[1] - neck.y) * 0.5;
    if (Math.hypot(c[0] - neck.x, c[1] - neck.y, c[2] - neck.z) < 0.16 && (!best || d < best.d)) best = { d, x: c[0], z: c[2] };
  }
  return best;
}
const BINS = 72;
const angleOf = (x, z, ax) => Math.atan2(x - ax.x, z - ax.z);
const binAt = (th) => (((th + Math.PI) / (2 * Math.PI)) * BINS) % BINS;
/** A per-bin table read at a fractional bin, round the circle. */
const atBin = (T, fb) => { const i = Math.floor(fb), f = fb - i; return T[((i % BINS) + BINS) % BINS] * (1 - f) + T[(((i + 1) % BINS) + BINS) % BINS] * f; };
function smoothBins(T, sigma = 1.5) {
  const out = new Float64Array(BINS);
  for (let b = 0; b < BINS; b++) { let a = 0, w = 0; for (let k = -4; k <= 4; k++) { const x = T[(b + k + BINS) % BINS]; if (!Number.isFinite(x)) continue; const wk = Math.exp(-(k * k) / (2 * sigma * sigma)); a += wk * x; w += wk; } out[b] = w ? a / w : NaN; }
  return out;
}
function fillBins(T) {
  for (let pass = 0; pass < BINS && T.some((x) => !Number.isFinite(x)); pass++) {
    const prev = T.slice();
    for (let b = 0; b < BINS; b++) if (!Number.isFinite(prev[b])) { const v = [prev[(b + BINS - 1) % BINS], prev[(b + 1) % BINS]].filter(Number.isFinite); if (v.length) T[b] = v.reduce((a, x) => a + x, 0) / v.length; }
  }
  return T;
}

/** Per welded point of a band, its share of the way from its top edge (0) to its bottom edge
 * (1) over the cloth, or null when the band has not two edges. */
function edgeShare(W) {
  const comp = new Map(), runs = [];
  for (const s0 of W.boundary.keys()) {
    if (comp.has(s0)) continue;
    const run = [s0]; comp.set(s0, runs.length);
    for (let k = 0; k < run.length; k++) for (const o of W.boundary.get(run[k])) if (!comp.has(o)) { comp.set(o, runs.length); run.push(o); }
    runs.push(run);
  }
  if (runs.length < 2) return null;
  runs.sort((a, b) => b.length - a.length);
  const meanY = (r) => r.reduce((t, g) => t + W.P[g * 3 + 1], 0) / r.length;
  const [hi, lo] = meanY(runs[0]) > meanY(runs[1]) ? [runs[0], runs[1]] : [runs[1], runs[0]];
  const nbr = Array.from({ length: W.G }, () => new Map());
  for (let t = 0; t < W.idx.length / 3; t++) for (let c = 0; c < 3; c++) {
    const a = W.groupOf[W.idx[t * 3 + c]], b = W.groupOf[W.idx[t * 3 + (c + 1) % 3]];
    if (a === b) continue;
    const d = Math.hypot(W.P[a * 3] - W.P[b * 3], W.P[a * 3 + 1] - W.P[b * 3 + 1], W.P[a * 3 + 2] - W.P[b * 3 + 2]);
    nbr[a].set(b, d); nbr[b].set(a, d);
  }
  const reach = (src) => {
    const D = new Float64Array(W.G).fill(Infinity), q = [...src];
    for (const g of src) D[g] = 0;
    // a small band: a queue relaxed to rest is quick enough
    while (q.length) { const g = q.shift(); for (const [o, d] of nbr[g]) if (D[g] + d < D[o] - 1e-9) { D[o] = D[g] + d; q.push(o); } }
    return D;
  };
  const a = reach(hi), b = reach(lo), out = new Float64Array(W.G);
  for (let g = 0; g < W.G; g++) out[g] = Number.isFinite(a[g] + b[g]) && a[g] + b[g] > 0 ? a[g] / (a[g] + b[g]) : 0;
  for (const g of hi) out[g] = 0;
  for (const g of lo) out[g] = 1;
  return out;
}

/** Ease a band laid out round a neck (u angle, v height) until no face is turned over against
 * the rest: the points of turned faces and their neighbours averaged with their neighbours, an
 * edge point round the neck only. At most UNTANGLE_PASSES passes. */
const UNTANGLE_PASSES = 80;
const wrap = (d) => (d > Math.PI ? d - 2 * Math.PI : d < -Math.PI ? d + 2 * Math.PI : d);
function untangle(W, U, V, fixedV) {
  const T = W.idx.length / 3, tri = (t) => [0, 1, 2].map((c) => W.groupOf[W.idx[t * 3 + c]]);
  const nbr = Array.from({ length: W.G }, () => new Set());
  for (let t = 0; t < T; t++) { const q = tri(t); for (let c = 0; c < 3; c++) if (q[c] !== q[(c + 1) % 3]) { nbr[q[c]].add(q[(c + 1) % 3]); nbr[q[(c + 1) % 3]].add(q[c]); } }
  const sgn = (t) => { const [a, b, c] = tri(t); const x = (wrap(U[b] - U[a])) * (V[c] - V[a]) - (wrap(U[c] - U[a])) * (V[b] - V[a]); return Math.abs(x) < 1e-12 ? 0 : Math.sign(x); };
  let major = 0; for (let t = 0; t < T; t++) major += sgn(t);
  major = Math.sign(major) || 1;
  for (let pass = 0; pass < UNTANGLE_PASSES; pass++) {
    const bad = new Set();
    for (let t = 0; t < T; t++) if (sgn(t) === -major) for (const g of tri(t)) { bad.add(g); for (const o of nbr[g]) bad.add(o); }
    if (!bad.size) return pass;
    const u1 = U.slice(), v1 = V.slice();
    for (const g of bad) {
      if (!nbr[g].size) continue;
      let du = 0, dv = 0, n = 0;
      for (const o of nbr[g]) { if (fixedV[g] && !fixedV[o]) continue; du += wrap(U[o] - U[g]); dv += V[o] - V[g]; n++; }
      if (!n) continue;
      u1[g] = U[g] + 0.5 * du / n;
      if (!fixedV[g]) v1[g] = V[g] + 0.5 * dv / n;
    }
    U.set(u1); V.set(v1);
  }
  return UNTANGLE_PASSES;
}

/** A band round the neck: each point's normal from its faces, every face turned out from the
 * neck's axis (bind), copies of a point sharing one. */
function normalsOut(mesh, W, shift, ax) {
  const nrm = mesh.geometry.attributes.normal; if (!nrm) return;
  const Q = Float64Array.from(W.P, (v, i) => v + shift[i]), sum = new Float64Array(W.G * 3);
  for (let t = 0; t < W.idx.length / 3; t++) {
    const q = [0, 1, 2].map((c) => W.groupOf[W.idx[t * 3 + c]]), A = q[0] * 3, B = q[1] * 3, Cc = q[2] * 3;
    const e1 = [Q[B] - Q[A], Q[B + 1] - Q[A + 1], Q[B + 2] - Q[A + 2]], e2 = [Q[Cc] - Q[A], Q[Cc + 1] - Q[A + 1], Q[Cc + 2] - Q[A + 2]];
    const f = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    const mx = (Q[A] + Q[B] + Q[Cc]) / 3 - ax.x, mz = (Q[A + 2] + Q[B + 2] + Q[Cc + 2]) / 3 - ax.z, sg = f[0] * mx + f[2] * mz < 0 ? -1 : 1;
    for (const g of q) for (let k = 0; k < 3; k++) sum[g * 3 + k] += sg * f[k];
  }
  const back = new THREE.Matrix3().getNormalMatrix(mesh.bindMatrix.clone().invert()), v = new THREE.Vector3();
  for (let i = 0; i < nrm.count; i++) {
    const g = W.groupOf[i]; v.set(sum[g * 3], sum[g * 3 + 1], sum[g * 3 + 2]);
    if (v.lengthSq() < 1e-24) continue;
    v.normalize().applyMatrix3(back).normalize(); nrm.setXYZ(i, v.x, v.y, v.z);
  }
  nrm.needsUpdate = true;
}

/** The white collar over the dark stand: the collar runs from COVER.lip above the stand's top
 * down to the stand's foot (where the dress flares out by COVER.flare to the shoulders, between
 * COVER.minDepth and COVER.depth below its top), COVER.gap outside it. */
export const COVER = Object.freeze({ lip: 0.002, gap: 0.003, depth: 0.04, minDepth: 0.025, flare: 0.012, reach: 0.14 });
/**
 * Draw a collar cut as a narrow band at the top of a dress's standing collar down over the
 * whole stand. The maid's white collar was cut 6 to 18 mm deep at the top of a black stand
 * 4 to 5 cm high, so at three metres the dress's black stand read where the picture shows a
 * white collar at the throat (Kelley, 1904). Each point of the collar keeps its place round
 * the neck and its share of the way down the band; the band is stretched from just above the
 * stand's top to its foot, laid COVER.gap outside the dress, its thickness kept. Returns
 * { moved, max_m, depth_m } or null.
 */
export function coverStand(collar, dress) {
  if (!collar?.isSkinnedMesh || !dress?.isSkinnedMesh) return null;
  const neck = neckOf(dress);
  if (!neck) return null;
  const C = weld(collar), D = weld(dress), ax = neckAxis(D, neck.at);
  if (!ax) return null;
  // The dress's stand: per bin round the neck, its top, and its outermost radius by height.
  const STEP = 0.001, ROWS = 80, top = new Float64Array(BINS).fill(NaN);
  const near = [];
  for (let g = 0; g < D.G; g++) {
    const x = D.P[g * 3], y = D.P[g * 3 + 1], z = D.P[g * 3 + 2], r = Math.hypot(x - ax.x, z - ax.z);
    if (r > COVER.reach || y < neck.at.y - 0.1) continue;
    const b = Math.floor(binAt(angleOf(x, z, ax)));
    near.push([b, y, r]);
    if (!(top[b] >= y)) top[b] = y;
  }
  fillBins(top);
  if (top.some((x) => !Number.isFinite(x))) return null;
  const topS = smoothBins(top);
  // rTab[b][k]: the dress's outermost radius at k mm below that bin's top (within 3 mm, bins either side)
  const rTab = Array.from({ length: BINS }, () => new Float64Array(ROWS).fill(NaN));
  for (const [b, y, r] of near) for (const db of [-1, 0, 1]) {
    const bb = (b + db + BINS) % BINS;
    const k0 = Math.round((topS[bb] - y) / STEP);
    for (let k = k0 - 3; k <= k0 + 3; k++) if (k >= 0 && k < ROWS && !(rTab[bb][k] >= r)) rTab[bb][k] = r;
  }
  for (const row of rTab) {
    let last = NaN; for (let k = 0; k < ROWS; k++) { if (Number.isFinite(row[k])) last = row[k]; else row[k] = last; }
    last = NaN; for (let k = ROWS - 1; k >= 0; k--) { if (Number.isFinite(row[k])) last = row[k]; else row[k] = last; }
  }
  if (rTab.some((row) => !Number.isFinite(row[0]))) return null;
  // The stand's foot: the first height below the top where the dress flares out to the shoulder.
  const foot = new Float64Array(BINS);
  for (let b = 0; b < BINS; b++) {
    let k = Math.round(COVER.minDepth / STEP);
    while (k < Math.round(COVER.depth / STEP) && rTab[b][k] <= rTab[b][0] + COVER.flare) k++;
    foot[b] = topS[b] - k * STEP;
  }
  const footS = smoothBins(foot);
  const rAt = (fb, y) => {
    const i = Math.floor(fb), f = fb - i, q = (b) => { const row = rTab[((b % BINS) + BINS) % BINS], kk = Math.min(ROWS - 1, Math.max(0, (atBin(topS, fb) - y) / STEP)), k = Math.floor(kk), t = kk - k; return row[k] * (1 - t) + row[Math.min(ROWS - 1, k + 1)] * t; };
    return q(i) * (1 - f) + q(i + 1) * f;
  };
  // The collar: per bin its own top, bottom and innermost offset off the dress.
  const ct = new Float64Array(BINS).fill(NaN), cb = new Float64Array(BINS).fill(NaN), inner = new Float64Array(BINS).fill(NaN);
  const pts = [];
  for (let g = 0; g < C.G; g++) {
    const x = C.P[g * 3], y = C.P[g * 3 + 1], z = C.P[g * 3 + 2], fb = binAt(angleOf(x, z, ax)), b = Math.floor(fb);
    const off = Math.hypot(x - ax.x, z - ax.z) - rAt(fb, y);
    pts.push([g, fb, y, off]);
    if (!(ct[b] >= y)) ct[b] = y;
    if (!(cb[b] <= y)) cb[b] = y;
    if (!(inner[b] <= off)) inner[b] = off;
  }
  for (const T of [ct, cb, inner]) fillBins(T);
  if ([ct, cb, inner].some((T) => T.some((x) => !Number.isFinite(x)))) return null;
  const ctS = smoothBins(ct), cbS = smoothBins(cb), inS = smoothBins(inner);
  // Each point's share of the way down the band: by its distance over the cloth from the band's
  // top edge and from its bottom edge (the two largest runs of open edges, the higher the top), so
  // the cut's own teeth (a bottom edge that climbs to the top here and there) come out on the new
  // bottom line, not as notches; by height in its bin where the edges cannot be told apart.
  const share = edgeShare(C);
  // Laid out on the stand: round it (u, the angle) and down it (v, the height), plus the cloth's
  // own thickness off its inner face.
  const U = new Float64Array(C.G), V = new Float64Array(C.G), O = new Float64Array(C.G), edgeOf = new Uint8Array(C.G);
  let depth = Infinity;
  for (const [g, fb, y, off] of pts) {
    const t0 = atBin(ctS, fb), b0 = atBin(cbS, fb), T = Math.max(t0, atBin(topS, fb)) + COVER.lip, F = Math.min(b0, atBin(footS, fb));
    depth = Math.min(depth, T - F);
    const f = share ? share[g] : Math.min(1, Math.max(0, (t0 - y) / Math.max(1e-4, t0 - b0)));
    U[g] = angleOf(C.P[g * 3], C.P[g * 3 + 2], ax); V[g] = T - f * (T - F); O[g] = Math.max(0, off - atBin(inS, fb));
    edgeOf[g] = share && (share[g] === 0 || share[g] === 1) ? 1 : 0;
  }
  // The cut's stair laid out so leaves faces turned over (a riser's faces): eased out by
  // averaging each point with its neighbours (round; and down, but for the two edges, which keep
  // their height) until none is.
  untangle(C, U, V, edgeOf);
  const shift = new Float64Array(C.G * 3);
  let moved = 0, far = 0;
  for (const [g] of pts) {
    const th = U[g], fb = binAt(th), y1 = V[g], r1 = rAt(fb, Math.min(y1, atBin(topS, fb))) + COVER.gap + O[g];
    const q = [ax.x + r1 * Math.sin(th), y1, ax.z + r1 * Math.cos(th)];
    for (let k = 0; k < 3; k++) shift[g * 3 + k] = q[k] - C.P[g * 3 + k];
    const l = Math.hypot(shift[g * 3], shift[g * 3 + 1], shift[g * 3 + 2]);
    if (l > 1e-6) { moved++; far = Math.max(far, l); }
  }
  if (!moved) return { moved: 0, max_m: 0 };
  apply(collar, C, shift);
  // Its normals out from the neck: the cut's risers faced every way, and their points' old
  // normals would turn half the new band's shading inward (dark teeth on the white).
  normalsOut(collar, C, shift, ax);
  return { moved, max_m: far, depth_m: depth };
}

/** The strap frills: lifted off the dress, in full FRILL.to from the strap's edge, nothing
 * within FRILL.from of it. */
export const FRILL = Object.freeze({ lift: 0.012, from: 0.004, to: 0.03 });
/** Nearest point on a mesh's triangles at bind: (p) => { d, q } within `reach`. */
function nearestOn(mesh, reach) {
  const P = bindPositions(mesh), idx = indexOf(mesh), cell = 0.02, map = new Map(), key = (a, b, c) => `${a},${b},${c}`;
  for (let t = 0; t < idx.length / 3; t++) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let c = 0; c < 3; c++) for (let k = 0; k < 3; k++) { const x = P[idx[t * 3 + c] * 3 + k]; lo[k] = Math.min(lo[k], x); hi[k] = Math.max(hi[k], x); }
    for (let a = Math.floor(lo[0] / cell); a <= Math.floor(hi[0] / cell); a++) for (let b = Math.floor(lo[1] / cell); b <= Math.floor(hi[1] / cell); b++) for (let c = Math.floor(lo[2] / cell); c <= Math.floor(hi[2] / cell); c++) {
      const k = key(a, b, c); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(t);
    }
  }
  const tri = new THREE.Triangle(), a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), q = new THREE.Vector3(), p = new THREE.Vector3();
  const R = Math.ceil(reach / cell);
  return (x, y, z) => {
    p.set(x, y, z);
    let best = null; const seen = new Set(), ca = Math.floor(x / cell), cb = Math.floor(y / cell), cc = Math.floor(z / cell);
    for (let i = -R; i <= R; i++) for (let j = -R; j <= R; j++) for (let k = -R; k <= R; k++) {
      const l = map.get(key(ca + i, cb + j, cc + k)); if (!l) continue;
      for (const t of l) {
        if (seen.has(t)) continue; seen.add(t);
        tri.set(a.fromArray(P, idx[t * 3] * 3), b.fromArray(P, idx[t * 3 + 1] * 3), c.fromArray(P, idx[t * 3 + 2] * 3)).closestPointToPoint(p, q);
        const d = q.distanceTo(p); if (!best || d < best.d) best = { d, q: q.toArray() };
      }
    }
    return best && best.d <= reach ? best : null;
  };
}
/**
 * Stand the maid's strap frills off the dress, as a gathered frill stands: each point of the
 * frill FRILL.from or more from its strap goes out from the body by up to FRILL.lift, in full at
 * FRILL.to (not widened across: carried sideways, the frill's outer edge lands where the
 * dress's shoulder rises, and the dress comes through it). Drawn flat on the dress beside a plain white strap of the same white, the frill read
 * at three metres as part of a broad plain strap; standing off, it catches the light along its
 * own edge and shows a lit rim and a shadow against the black, as the frills over Kelley's
 * maid's shoulders do. Returns { moved, max_m } or null.
 */
export function liftFrill(frill, strap, skin) {
  if (!frill?.isSkinnedMesh || !strap?.isSkinnedMesh) return null;
  const W = weld(frill), at = nearestOn(strap, FRILL.to * 2), out = skinNear(skin);
  if (!out) return null;
  const shift = new Float64Array(W.G * 3);
  let moved = 0, far = 0;
  for (let g = 0; g < W.G; g++) {
    const x = W.P[g * 3], y = W.P[g * 3 + 1], z = W.P[g * 3 + 2], h = at(x, y, z);
    const d = h ? h.d : FRILL.to * 2, k = smooth((d - FRILL.from) / (FRILL.to - FRILL.from));
    if (!(k > 1e-3)) continue;
    const o = out(x, y, z); if (!o) continue;
    for (let c = 0; c < 3; c++) shift[g * 3 + c] = k * FRILL.lift * o[c];
    moved++; far = Math.max(far, k * FRILL.lift);
  }
  if (!moved) return { moved: 0, max_m: 0 };
  apply(frill, W, shift);
  return { moved, max_m: far };
}

/** A child's collar: its front edges brought together (the slit closed to HUG.meet), and its
 * inner edge drawn in to HUG.gap off the neck, faded out over HUG.band across the collar,
 * round the sides and back (from HUG.frontDeg off the front, in full 45 degrees on), only as
 * far as the garment's own neckline shows inside it (from HUG.below under its inner edge) and
 * HUG.over past that; the draw-in evened along the collar's edges over HUG.even passes. */
export const HUG = Object.freeze({ meet: 0.0005, fade: 0.035, gap: 0.005, band: 0.008, rise: 0.006, maxIn: 0.035, frontDeg: 25, below: 0.02, over: 0.006, even: 8 });
/**
 * The 1904 children's collars (an Eton collar on the boys, a broad round collar on the girls)
 * were drawn with a slit a centimetre or more wide down the front, where the jacket's placket
 * showed through dark, and with their inner edge two or three centimetres off the neck, so
 * between collar and neck a band of the jacket's or frock's own neckline showed dark above the
 * white. Here (1) each half's front edge is brought across to the middle, the shift fading out
 * over HUG.fade round the collar, and (2) the collar's inner part is drawn in toward the neck
 * until its inner edge lies HUG.gap off the skin (by no more than HUG.maxIn) and a little up
 * (HUG.rise), fading out over HUG.band across the collar, so the collar closes round the neck
 * as a collar does (with `pull: false`, only (1)). Returns { moved, max_m, slit_m, in_m } or null.
 */
export function hugNeck(collar, garment, skin, { pull: drawIn = true } = {}) {
  if (!collar?.isSkinnedMesh || !skin) return null;
  const neck = neckOf(collar);
  if (!neck) return null;
  const C = weld(collar), P = C.P.slice(), ax = neckAxis(C, neck.at) ?? { x: neck.at.x, z: neck.at.z };
  // (1) the slit: points in front of the axis; each half's edge, the nearest of it to the middle
  // (the exports cut it straight down, parallel to the middle).
  let rMean = 0;
  for (let g = 0; g < C.G; g++) rMean += Math.hypot(P[g * 3] - ax.x, P[g * 3 + 2] - ax.z) / C.G;
  const front = [];
  for (let g = 0; g < C.G; g++) if (P[g * 3 + 2] - ax.z > 0.5 * rMean) front.push(g);
  const edge = { 1: Infinity, [-1]: Infinity };
  for (const g of front) { const x = P[g * 3] - ax.x; edge[Math.sign(x) || 1] = Math.min(edge[Math.sign(x) || 1], Math.abs(x)); }
  let slit = 0;
  if (front.length && edge[1] > 0.002 && edge[-1] > 0.002 && edge[1] < 0.03 && edge[-1] < 0.03) {
    // Brought across, each point keeps its height off the garment's front beneath it (the
    // chest and the placket stand forward of where the edge lay).
    const under = garment?.isSkinnedMesh ? triGrid([garment]) : null, fwd = [0, 0, 1];
    const frontAt = (x, y, z) => { if (!under) return null; const h = cast(under, [x, y, z], fwd, 0.03).filter((q) => q[1] > 0.2); return h.length ? z + Math.max(...h.map((q) => q[0])) : null; };
    for (const g of front) {
      const x = P[g * 3] - ax.x, sd = Math.sign(x) || 1, h = edge[sd], w = 1 - smooth((Math.abs(x) - h) / HUG.fade), s = (h - HUG.meet) * w;
      if (!(s > 0)) continue;
      const z0 = frontAt(P[g * 3], P[g * 3 + 1], P[g * 3 + 2]);
      P[g * 3] -= sd * s; slit = Math.max(slit, s);
      const z1 = frontAt(P[g * 3], P[g * 3 + 1], P[g * 3 + 2]);
      if (z0 !== null && z1 !== null) P[g * 3 + 2] += Math.max(0, (z1 - z0));
    }
  }
  // (2) the inner edge to the neck: per bin, the collar's inner radius and the skin's inside it.
  const inner = new Float64Array(BINS).fill(NaN), innerY = new Float64Array(BINS).fill(NaN);
  for (let g = 0; g < C.G; g++) {
    const r = Math.hypot(P[g * 3] - ax.x, P[g * 3 + 2] - ax.z), b = Math.floor(binAt(angleOf(P[g * 3], P[g * 3 + 2], ax)));
    if (!(inner[b] <= r)) { inner[b] = r; innerY[b] = P[g * 3 + 1]; }
  }
  fillBins(inner); fillBins(innerY);
  const SP = bindPositions(skin), neckR = new Float64Array(BINS).fill(NaN);
  for (let i = 0; i < SP.length / 3; i++) {
    const x = SP[i * 3], y = SP[i * 3 + 1], z = SP[i * 3 + 2], b = Math.floor(binAt(angleOf(x, z, ax))), r = Math.hypot(x - ax.x, z - ax.z);
    if (!Number.isFinite(innerY[b]) || Math.abs(y - (innerY[b] + HUG.rise)) > 0.006 || r > inner[b] + 0.005) continue;
    if (!(neckR[b] >= r)) neckR[b] = r;
  }
  fillBins(neckR);
  if (neckR.some((x) => !Number.isFinite(x))) return null;
  // ...and the garment's own neckline showing inside the collar's opening (its cloth within
  // the opening and no lower than HUG.below under the collar's inner edge): only there, and
  // only as far as it shows (and HUG.over past it), is the collar drawn in. Where the
  // garment's neckline lies under the collar already (the back, as drawn), nothing moves.
  const showR = new Float64Array(BINS).fill(NaN);
  if (garment?.isSkinnedMesh) {
    const GP = bindPositions(garment);
    for (let i = 0; i < GP.length / 3; i++) {
      const x = GP[i * 3], y = GP[i * 3 + 1], z = GP[i * 3 + 2], b = Math.floor(binAt(angleOf(x, z, ax))), r = Math.hypot(x - ax.x, z - ax.z);
      if (!Number.isFinite(innerY[b]) || y < innerY[b] - HUG.below || r >= inner[b]) continue;
      if (!(showR[b] <= r)) showR[b] = r;
    }
  }
  const show = new Float64Array(BINS);
  for (let b = 0; b < BINS; b++) show[b] = Number.isFinite(showR[b]) ? inner[b] - showR[b] + HUG.over : 0;
  const inS = smoothBins(inner), nS = smoothBins(neckR, 1), shS = smoothBins(show, 2);
  let pull = 0;
  const PS = new Float64Array(C.G * 3);
  for (let g = 0; g < C.G; g++) {
    const x = P[g * 3] - ax.x, z = P[g * 3 + 2] - ax.z, r = Math.hypot(x, z), fb = binAt(Math.atan2(x, z));
    // (not at the front: there the collar's edge already meets the throat, and the garment's
    // front rises to it, so drawing the collar in there would lay it under the garment)
    const aside = smooth((Math.abs(Math.atan2(x, z)) * 180 / Math.PI - HUG.frontDeg) / 45);
    const room = aside * Math.min(HUG.maxIn, atBin(shS, fb), Math.max(0, atBin(inS, fb) - atBin(nS, fb) - HUG.gap));
    const t = 1 - smooth((r - atBin(inS, fb)) / HUG.band);
    if (!drawIn || !(t > 1e-3) || !(room > 1e-4)) continue;
    const r1 = r - room * t;
    PS[g * 3] = (x / r) * (r1 - r); PS[g * 3 + 2] = (z / r) * (r1 - r); PS[g * 3 + 1] = HUG.rise * t;
  }
  // The draw-in evened along the collar's edges (HUG.even passes, each edge point half to the
  // mean of its two neighbours on the edge), so the cut's own small steps at the collar's ends
  // are carried in with the edge round them instead of stretched.
  for (let it = 0; it < HUG.even; it++) {
    const prev = PS.slice();
    for (const [g, nb] of C.boundary) {
      if (nb.length !== 2) continue;
      for (let k = 0; k < 3; k++) PS[g * 3 + k] = 0.5 * prev[g * 3 + k] + 0.25 * (prev[nb[0] * 3 + k] + prev[nb[1] * 3 + k]);
    }
  }
  for (let g = 0; g < C.G; g++) { for (let k = 0; k < 3; k++) P[g * 3 + k] += PS[g * 3 + k]; pull = Math.max(pull, Math.hypot(PS[g * 3], PS[g * 3 + 2])); }
  const shift = new Float64Array(C.G * 3);
  let moved = 0, far = 0;
  for (let i = 0; i < shift.length; i++) shift[i] = P[i] - C.P[i];
  for (let g = 0; g < C.G; g++) { const l = Math.hypot(shift[g * 3], shift[g * 3 + 1], shift[g * 3 + 2]); if (l > 1e-6) { moved++; far = Math.max(far, l); } }
  if (!moved) return { moved: 0, max_m: 0, slit_m: 0, in_m: 0 };
  apply(collar, C, shift);
  return { moved, max_m: far, slit_m: slit, in_m: pull };
}

/** Tuck every listed under garment of a loaded body beneath the cloth worn over it, once. */
export function dressCollars(root) {
  if (!root) return null;
  if (root.userData.chicagoCollars) return root.userData.chicagoCollars;
  const assetId = root.userData?.chicago4d_human?.asset_id ?? null;
  const meshes = [];
  root.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); });
  const id = assetId ?? commonPrefix(meshes);
  const report = [];
  for (const lod of new Set(meshes.map(lodOf))) {
    const at = meshes.filter((m) => lodOf(m) === lod);
    const skin = at.find((m) => materialName(m) === 'skin') ?? null;
    const pairs = [];
    const far = lod !== '0' && lod !== '', nearTwo = lod === '0' || lod === '1' || lod === '';
    // A `near` layer is dressed at the nearest level only: a far level's frill, a few faces,
    // follows and clears its bodice worse than as drawn.
    for (const L of LAYERS) if (!(L.near && far)) for (const u of at) {
      if (!L.under.test(pieceName(u, id))) continue;
      const cov = at.filter((o) => o !== u && L.over.test(pieceName(o, id)));
      if (cov.length) pairs.push([L, u, cov]);
    }
    // Round 4: a child's collar closed at the front (and, at the two near levels, drawn in
    // round the neck: a far level's few faces drawn in come out stepped), before its edges are
    // faired (drawn in, the cut's own steps at the collar's ends stretch, and the fairing
    // smooths them out as it does any step).
    for (const [L, u, cov] of pairs) if (L.hug) for (const c of cov) {
      const q = hugNeck(c, u, skin, { pull: nearTwo });
      if (q) report.push({ mesh: c.name, hug: pieceName(c, id), on: pieceName(u, id), ...q });
    }
    for (const m of at) {
      const name = pieceName(m, id);
      if (!FAIR.test(name) && !FAIR_NECK.test(name)) continue;
      const neck = FAIR_NECK.test(name) ? neckOf(m) : null;
      if (FAIR_NECK.test(name) && !neck) continue;
      const r = fairEdges(m, skin, { around: neck });
      if (r) report.push({ mesh: m.name, fair: name, ...r });
    }
    // Round 4: a collar drawn down over its dress's stand (at the two near levels only: a far
    // level's collar, a few dozen faces, comes out ragged drawn down, and its dress's stand is
    // too sparse to read; left as drawn), and the strap frills stood off the dress (at the two
    // near levels: a far level's frill is a few faces, left as drawn), before anything is
    // reweighted or tucked.
    if (nearTwo) for (const [L, u, cov] of pairs) if (L.cover) for (const c of cov) {
      const q = coverStand(c, u);
      if (q) report.push({ mesh: c.name, cover: pieceName(c, id), on: pieceName(u, id), ...q });
    }
    if (nearTwo) {
      const straps = at.find((m) => pieceName(m, id) === 'apron_straps');
      for (const f of at.filter((m) => pieceName(m, id) === 'apron_strap_frills')) {
        const q = liftFrill(f, straps, skin);
        if (q) report.push({ mesh: f.name, lift: 'apron_strap_frills', ...q });
      }
    }
    // A collar is settled on its coat, and cloth that follows the garment beneath it is
    // reweighted, before anything is tucked under anything.
    for (const [L, u, cov] of pairs) for (const c of cov) {
      if (!L.settle) continue;
      const q = settleCollar(c, u);
      if (q) report.push({ mesh: c.name, settle: pieceName(c, id), on: pieceName(u, id), ...q });
    }
    for (const [L, u, cov] of pairs) for (const c of cov) {
      if (!L.follow) continue;
      const q = followWeights(c, u);
      if (q) report.push({ mesh: c.name, follow: pieceName(c, id), on: pieceName(u, id), ...q });
    }
    // Then in the order listed: what lies outermost first, so what goes under it goes under
    // where it now lies (the crossbelts, then the collar under them, then the coat under both).
    for (const [L, u, cov] of pairs) {
      const r = tuckUnder(u, cov, skin, { poke: L.poke ?? POKE_M, max: L.max ?? MAX_M, gap: L.gap ?? GAP_M });
      if (r) report.push({ mesh: u.name, under: pieceName(u, id), over: cov.map((c) => pieceName(c, id)), ...r });
    }
  }
  root.userData.chicagoCollars = report;
  return report;
}
function commonPrefix(meshes) {
  const body = meshes.find((m) => /_body_0_lod\d*$/.test(m.name));
  return body ? body.name.replace(/_body_0_lod\d*$/, '') : null;
}
