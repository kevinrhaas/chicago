// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-seat.js — trousers bridge the seat; they never trace the cleft (T-3553).
 *
 * The exporter builds every pair of trousers, breeches, pantaloons and overalls as a shell
 * a little off the body, and the body's own buttock cleft comes through into the cloth: from
 * behind, walking, the seat reads as two cheeks and the hollow between them, which no woven
 * cloth does (it spans the hollow from cheek to cheek, the seat seam lying across it). The
 * 1812 settler's linen pair was rebuilt at source for it (#1933, tools/human_linen_seat.py);
 * the 1835 labourer, Otis Bardwell, the 1812 engage, the 1904 driver, stable helper and boys
 * and the soldiers' and officers' pantaloons all still traced it.
 *
 * Here, once per loaded body (before any figure is cloned from it, as human-waist.js does),
 * every seat is bridged the same way the settler's was: in level rows from the fork up past
 * the top of the cleft, the rear of the section is taken to its upper convex hull (seen from
 * behind, the cloth stretched across), and only the vertices inside the hull move, straight
 * back onto it. The hull is the cloth's own outline, so nothing gets bigger than the cheeks
 * already make it; a row with no seat seam at the middle (below the fork, the two legs apart)
 * is left alone, and the bridge fades out over the last few centimetres at the fork and at
 * the top so neither edge makes a ridge. A vertex moves at most MAX_M. The normals of the
 * moved cloth are taken again from its own faces, so the light does not paint the hollow
 * back on. Cloth worn over the seat (a waistcoat's or shirt's hem, a coat, the band) stays
 * over it: the bridge stops COVER_GAP_M inside any garment that was outside the trousers. Topology, UVs and skin weights are unchanged: the bridge walks with the pelvis
 * and the thighs exactly as the hollow did, and the cloth over it spans it on the walk.
 *
 * Cost: a few thousand vertices per level, once per parse (a few milliseconds). No new
 * geometry, texture, draw call or program. A reconstructed ease, as the garments' own cut is
 * (liberty L-seat-3553 beside L418).
 */
import * as THREE from 'three';

/** A trouser-like garment, by its piece name; a waistband is the waist's, not the seat's. */
export const SEAT_PIECE = /(^|_)(trousers?|breeches|pantaloons|overalls)(_|$)/;
const NOT_SEAT = /(^|_)(band|waistband|braces|buttons?)(_|$)/;
/** Rows: this far apart, each reading the vertices within ROW_HALF of it. Per 0.85 m of leg. */
export const ROW_M = 0.008, ROW_HALF = 0.009;
/** The bridge runs from the fork up to this far above the hip joints, fading over FADE_M at each end. */
export const TOP_M = 0.11, FADE_TOP_M = 0.035, FADE_FORK_M = 0.03;
/** A vertex moves at most this far back (metres, per 0.85 m of leg): the hollow the bodies
 * draw is 4 to 5 cm deep at its foot. */
export const MAX_M = 0.06;
/** The fork is never sought lower than this under the hip joints (per 0.85 m of leg): a boy's
 * inner thighs meet at the middle further down. */
export const FORK_M = 0.17;
/** A row has a seat seam when the cloth has a vertex this near the middle, behind. */
const MID_M = 0.014;
/** The moved cloth relaxes over the bridge this many times, this far toward its neighbours. */
const RELAX_STEPS = 8, RELAX = 0.5;
/** Cloth worn over the seat (a waistcoat's or a shirt's hem, a coat, a waistband) stays over
 * it: the bridge stops this far inside any garment that was outside the trousers there. */
export const COVER_GAP_M = 0.002;
const COVER_CELL_M = 0.006, COVER_NEAR_M = 0.01;
const ADULT_LEG_M = 0.85;
const NEEDED = ['pelvis', 'thigh_l', 'thigh_r', 'foot_l', 'foot_r'];
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };

const pieceName = (mesh, assetId) => {
  let n = mesh.name ?? '';
  if (assetId && n.startsWith(`${assetId}_`)) n = n.slice(assetId.length + 1);
  return n.replace(/_lod\d*$/, '');
};
const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';

/** Is this mesh a seat to bridge: a lower garment named as trousers, not its band. */
export function isSeat(mesh, assetId = null) {
  if (!mesh?.isSkinnedMesh || !mesh.skeleton) return false;
  if (!/^garment_lower/.test(materialName(mesh))) return false;
  const name = pieceName(mesh, assetId);
  return SEAT_PIECE.test(name) && !NOT_SEAT.test(name);
}

/** The body's frame at bind, from the mesh's own skeleton: O mid-hips, U up, L left, F forward. */
function frameOf(mesh) {
  const sk = mesh.skeleton, index = new Map(sk.bones.map((b, i) => [b?.name, i]));
  if (!NEEDED.every((n) => index.has(n))) return null;
  const at = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[index.get(n)].clone().invert());
  const hl = at('thigh_l'), hr = at('thigh_r'), al = at('foot_l'), ar = at('foot_r');
  const O = hl.clone().add(hr).multiplyScalar(0.5);
  const U = O.clone().sub(al.clone().add(ar).multiplyScalar(0.5));
  const leg = (hl.distanceTo(al) + hr.distanceTo(ar)) / 2;
  U.normalize();
  const L = hl.clone().sub(hr); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  return { O, U, L, F, scale: leg / ADULT_LEG_M };
}

/** The upper convex hull of (x, rear) points, sorted by x. */
function upperHull(points) {
  points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const hull = [];
  for (const p of points) {
    while (hull.length >= 2) {
      const a = hull[hull.length - 2], b = hull[hull.length - 1];
      if ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -1e-12) break;
      hull.pop();
    }
    hull.push(p);
  }
  return hull;
}
function hullAt(hull, x) {
  if (!hull || hull.length < 2 || x < hull[0][0] || x > hull[hull.length - 1][0]) return null;
  for (let i = 1; i < hull.length; i++) {
    const a = hull[i - 1], b = hull[i];
    if (x <= b[0]) return a[1] + (b[1] - a[1]) * ((x - a[0]) / ((b[0] - a[0]) || 1));
  }
  return hull[hull.length - 1][1];
}

/**
 * Bridge one garment's seat in place. Returns { moved, max_m } (vertices moved and the
 * farthest), or null when the mesh is not a seat or has no fork.
 */
export function bridgeSeat(mesh, covers = []) {
  const fr = frameOf(mesh);
  if (!fr) return null;
  const { O, U, L, F, scale } = fr;
  const geo = mesh.geometry, pos = geo.attributes.position, n = pos.count;
  const B = mesh.bindMatrix, Binv = B.clone().invert();
  // Each vertex in the frame: x left, y up from the hips, r = how far behind (rear is +).
  const X = new Float32Array(n), Y = new Float32Array(n), R = new Float32Array(n), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(B).sub(O);
    X[i] = v.dot(L); Y[i] = v.dot(U); R[i] = -v.dot(F);
  }
  const rowM = ROW_M * scale, half = ROW_HALF * scale, mid = MID_M * scale;
  const top = TOP_M * scale;
  // The fork: the lowest row that still has cloth behind at the middle.
  let fork = Infinity, lowest = Infinity;
  const floor = -FORK_M * scale;
  for (let i = 0; i < n; i++) { lowest = Math.min(lowest, Y[i]); if (R[i] > 0 && Math.abs(X[i]) < mid && Y[i] < top && Y[i] >= floor) fork = Math.min(fork, Y[i]); }
  if (!Number.isFinite(fork) || fork <= lowest) return null;
  const rows = Math.max(2, Math.ceil((top - fork) / rowM) + 1);
  const hulls = new Array(rows).fill(null);
  for (let k = 0; k < rows; k++) {
    const y = fork + k * rowM, pts = [];
    let seam = false;
    for (let i = 0; i < n; i++) {
      if (R[i] <= 0 || Math.abs(Y[i] - y) > half) continue;
      pts.push([X[i], R[i]]);
      if (Math.abs(X[i]) < mid) seam = true;
    }
    if (seam && pts.length >= 3) hulls[k] = upperHull(pts);
  }
  const cap = coverCap(covers, { O, U, L, F }, fork - 0.02, top + 0.02);
  const fadeTop = FADE_TOP_M * scale, fadeFork = FADE_FORK_M * scale, maxM = MAX_M * scale;
  // Every vertex at one place (a UV seam's copies) is one point: it moves, relaxes and is lit
  // as one, so the seam never opens.
  const keyOf = (i) => `${Math.round(X[i] * 2e4)},${Math.round(Y[i] * 2e4)},${Math.round(R[i] * 2e4)}`;
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) {
    const k = keyOf(i);
    let g = keys.get(k);
    if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); }
    groupOf[i] = g;
  }
  const G = first.length, gx = new Float64Array(G), gy = new Float64Array(G), gr = new Float64Array(G), r0 = new Float64Array(G);
  const moved = new Uint8Array(G);
  // The farthest back each point may go: inside any garment drawn over it there.
  const most = new Float64Array(G).fill(Infinity);
  for (let g = 0; g < G; g++) {
    const i = first[g]; gx[g] = X[i]; gy[g] = Y[i]; gr[g] = r0[g] = R[i];
    most[g] = cap(gx[g], gy[g], r0[g]);
  }
  for (let g = 0; g < G; g++) {
    if (gr[g] <= 0 || gy[g] < fork || gy[g] > top) continue;
    const f = (gy[g] - fork) / rowM, k0 = Math.min(rows - 1, Math.floor(f)), k1 = Math.min(rows - 1, k0 + 1), a = f - k0;
    const h0 = hullAt(hulls[k0], gx[g]), h1 = hullAt(hulls[k1], gx[g]);
    const h = h0 !== null && h1 !== null ? h0 * (1 - a) + h1 * a : (h0 ?? h1);
    if (h === null) continue;
    const want = h - gr[g];
    if (!(want > 5e-4)) continue;
    const w = smooth((gy[g] - fork) / fadeFork) * smooth((top - gy[g]) / fadeTop);
    const d = Math.min(maxM, want, most[g] - gr[g]) * w;
    if (!(d > 2e-4)) continue;
    gr[g] += d; moved[g] = 1;
  }
  let count = 0;
  for (let g = 0; g < G; g++) count += moved[g];
  if (!count) return { moved: 0, max_m: 0 };
  // The cleft's walls overhang, so straight back they land folded over one another on the
  // bridge (thin slivers lit the wrong way). Relax the moved points across the bridge (side
  // to side and in depth, never up or down) among their neighbours, the cloth's edge round
  // them held where it is, never letting a point sink back under where the asset drew it.
  const idx = geo.index, tri = idx ? idx.count / 3 : n / 3;
  const corner = (t, c) => groupOf[idx ? idx.getX(t * 3 + c) : t * 3 + c];
  const nbr = Array.from({ length: G }, () => null);
  for (let t = 0; t < tri; t++) {
    const q = [corner(t, 0), corner(t, 1), corner(t, 2)];
    for (let c = 0; c < 3; c++) {
      const g = q[c];
      if (!moved[g]) continue;
      const set = nbr[g] ?? (nbr[g] = new Set());
      set.add(q[(c + 1) % 3]); set.add(q[(c + 2) % 3]);
    }
  }
  const tx = new Float64Array(G), ty = new Float64Array(G), tr = new Float64Array(G);
  for (let it = 0; it < RELAX_STEPS; it++) {
    for (let g = 0; g < G; g++) {
      if (!moved[g] || !nbr[g]?.size) continue;
      let sx = 0, sy = 0, sr = 0;
      for (const o of nbr[g]) { sx += gx[o]; sy += gy[o]; sr += gr[o]; }
      const m = nbr[g].size;
      tx[g] = gx[g] + RELAX * (sx / m - gx[g]); ty[g] = gy[g]; tr[g] = gr[g] + RELAX * (sr / m - gr[g]);
    }
    for (let g = 0; g < G; g++) if (moved[g] && nbr[g]?.size) { gx[g] = tx[g]; gy[g] = ty[g]; gr[g] = Math.max(r0[g], Math.min(most[g], tr[g])); }
  }
  // Relaxed across, a point may now lie under another part of a hem: held inside it there too.
  for (let g = 0; g < G; g++) if (moved[g]) gr[g] = Math.max(r0[g], Math.min(gr[g], cap(gx[g], gy[g], r0[g])));
  // Back into the bind space, then the geometry's own.
  const toBind = (g, out) => out.copy(O).addScaledVector(L, gx[g]).addScaledVector(U, gy[g]).addScaledVector(F, -gr[g]);
  const P = new Array(G);
  let far = 0;
  const v0 = new THREE.Vector3();
  for (let g = 0; g < G; g++) {
    if (!moved[g]) continue;
    P[g] = toBind(g, new THREE.Vector3());
    v0.copy(O).addScaledVector(L, X[first[g]]).addScaledVector(U, Y[first[g]]).addScaledVector(F, -R[first[g]]);
    far = Math.max(far, P[g].distanceTo(v0));
  }
  const p = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const g = groupOf[i];
    if (!moved[g]) continue;
    p.copy(P[g]).applyMatrix4(Binv);
    pos.setXYZ(i, p.x, p.y, p.z);
  }
  pos.needsUpdate = true;
  renormal(geo, { groupOf, moved, G, gx, gy, gr, X, Y, R, first, O, L, U, F, Binv });
  geo.computeBoundingBox(); geo.computeBoundingSphere();
  return { moved: count, max_m: far };
}

/** The normals of the moved points from their faces (area-weighted, in the bind space), each
 * point's copies sharing one, turned to the side the asset's own normals face there. */
function renormal(geo, { groupOf, moved, G, gx, gy, gr, X, Y, R, first, O, L, U, F, Binv }) {
  const nrm = geo.attributes.normal, idx = geo.index, n = groupOf.length;
  if (!nrm) return;
  const at = (g, out) => (moved[g]
    ? out.copy(O).addScaledVector(L, gx[g]).addScaledVector(U, gy[g]).addScaledVector(F, -gr[g])
    : out.copy(O).addScaledVector(L, X[first[g]]).addScaledVector(U, Y[first[g]]).addScaledVector(F, -R[first[g]]));
  const sum = new Float64Array(G * 3);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  const tri = idx ? idx.count / 3 : n / 3;
  for (let t = 0; t < tri; t++) {
    const q = [0, 1, 2].map((k) => groupOf[idx ? idx.getX(t * 3 + k) : t * 3 + k]);
    if (!q.some((g) => moved[g])) continue;
    at(q[0], a); at(q[1], b); at(q[2], c);
    const fn = e1.subVectors(b, a).cross(e2.subVectors(c, a));
    for (const g of q) if (moved[g]) { sum[g * 3] += fn.x; sum[g * 3 + 1] += fn.y; sum[g * 3 + 2] += fn.z; }
  }
  // The winding's outward side: the one the asset's normals agree with over the moved cloth.
  const toBind = Binv.clone().invert(), old = new THREE.Vector3(), s = new THREE.Vector3();
  let agree = 0;
  for (let i = 0; i < n; i++) {
    const g = groupOf[i];
    if (!moved[g]) continue;
    old.fromBufferAttribute(nrm, i).transformDirection(toBind);
    s.set(sum[g * 3], sum[g * 3 + 1], sum[g * 3 + 2]);
    agree += Math.sign(s.dot(old));
  }
  const sign = agree < 0 ? -1 : 1;
  for (let i = 0; i < n; i++) {
    const g = groupOf[i];
    if (!moved[g]) continue;
    s.set(sum[g * 3], sum[g * 3 + 1], sum[g * 3 + 2]);
    if (s.lengthSq() < 1e-20) continue;
    s.multiplyScalar(sign).normalize().transformDirection(Binv);
    nrm.setXYZ(i, s.x, s.y, s.z);
  }
  nrm.needsUpdate = true;
}

/** The garments drawn over the seat, each as the rear of its bind-pose cloth within
 * COVER_NEAR_M of a point (x, y) of the body frame: a function of (x, y, r0) giving the
 * farthest back a point of the seat that was at r0 may go, Infinity where nothing lies over it. */
function coverCap(covers, { O, U, L, F }, lo, hi) {
  const v = new THREE.Vector3();
  const key = (ix, iy) => ix * 100003 + iy;
  const grids = [];
  for (const c of covers) {
    const pos = c.geometry?.attributes?.position;
    if (!pos) continue;
    const cells = new Map();
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(c.bindMatrix).sub(O);
      const x = v.dot(L), y = v.dot(U), r = -v.dot(F);
      if (r <= 0 || y < lo || y > hi) continue;
      const k = key(Math.floor(x / COVER_CELL_M), Math.floor(y / COVER_CELL_M));
      let list = cells.get(k);
      if (!list) cells.set(k, (list = []));
      list.push(x, y, r);
    }
    if (cells.size) grids.push(cells);
  }
  // Within COVER_NEAR_M of the point, the least far back of the cloth that is over the seat
  // there (a sloping hem caps it where it lies), Infinity where none of it is.
  const over = (cells, x, y, r0) => {
    const ix = Math.floor(x / COVER_CELL_M), iy = Math.floor(y / COVER_CELL_M), r2 = COVER_NEAR_M ** 2;
    let lo = Infinity;
    for (let a = -2; a <= 2; a++) for (let b = -2; b <= 2; b++) {
      const list = cells.get(key(ix + a, iy + b));
      if (!list) continue;
      for (let q = 0; q < list.length; q += 3) {
        if (list[q + 2] <= r0 + 1e-3 || (list[q] - x) ** 2 + (list[q + 1] - y) ** 2 > r2) continue;
        lo = Math.min(lo, list[q + 2]);
      }
    }
    return lo;
  };
  // A garment under the trousers there (a tucked shirt) does not hold them in; one over them does.
  return (x, y, r0) => {
    let most = Infinity;
    for (const cells of grids) {
      const lo = over(cells, x, y, r0);
      if (lo < Infinity) most = Math.min(most, Math.max(r0, lo - COVER_GAP_M));
    }
    return most;
  };
}

/** Bridge every seat of a loaded body, once (cloned figures share the result). */
export function easeSeats(root) {
  if (!root) return null;
  if (root.userData.chicagoSeatEase) return root.userData.chicagoSeatEase;
  const assetId = root.userData?.chicago4d_human?.asset_id ?? null;
  const report = [];
  const meshes = [];
  const cloth = [];
  root.traverse((o) => {
    if (isSeat(o, assetId)) meshes.push(o);
    else if (o.isSkinnedMesh && /^garment/.test(materialName(o))) cloth.push(o);
  });
  const lodOf = (o) => (o.name ?? '').match(/_lod(\d*)$/)?.[1] ?? '';
  for (const m of meshes) {
    const r = bridgeSeat(m, cloth.filter((c) => lodOf(c) === lodOf(m)));
    if (r) report.push({ mesh: m.name, ...r });
  }
  root.userData.chicagoSeatEase = report;
  return report;
}
