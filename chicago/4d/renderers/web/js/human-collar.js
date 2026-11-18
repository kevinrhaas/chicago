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
 * coat's neckline; `near` dresses the nearest level only; `byEye` is tucked but judged by eye,
 * not measured, by tools/test_human_collar.mjs.
 */
export const LAYERS = Object.freeze([
  // the maid's white collar band, apron bib, straps and their frills, over the black dress
  Object.freeze({ over: /^(white_collar|standing_collar)$/, under: /^(maid_bodice|plain_closed_bodice)$/, follow: true, poke: 0.015, max: 0.015, gap: 0.006 }),
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
  Object.freeze({ over: /^(child_collar|shirt_collar|pinafore_bib)$/, under: /^(child_jacket|frock_bodice|skeleton_jacket)$/ }),
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
    for (const m of at) {
      const name = pieceName(m, id);
      if (!FAIR.test(name) && !FAIR_NECK.test(name)) continue;
      const neck = FAIR_NECK.test(name) ? neckOf(m) : null;
      if (FAIR_NECK.test(name) && !neck) continue;
      const r = fairEdges(m, skin, { around: neck });
      if (r) report.push({ mesh: m.name, fair: name, ...r });
    }
    const pairs = [];
    const far = lod !== '0' && lod !== '';
    // A `near` layer is dressed at the nearest level only: a far level's frill, a few faces,
    // follows and clears its bodice worse than as drawn.
    for (const L of LAYERS) if (!(L.near && far)) for (const u of at) {
      if (!L.under.test(pieceName(u, id))) continue;
      const cov = at.filter((o) => o !== u && L.over.test(pieceName(o, id)));
      if (cov.length) pairs.push([L, u, cov]);
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
