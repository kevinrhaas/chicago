// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553 round 5 (the owner, 2026-11-25: "the men are very bad ... ragged at points and peek
 * through when they move and hugs their bodies unnaturally like the linen outfits in 1812, you
 * should do a rethink on how clothing is applied so that this will render neatly as AAA gaming
 * but you can downscale it well").
 *
 * The exported garments are proxies fitted to the body a few millimetres off its skin (a shirt
 * 6 to 10 mm, trousers 13 to 25 mm, a waistcoat 15 to 20 mm), so cloth reads as a body suit:
 * the chest, the navel, the crotch and the seat show through linen and wool. This pass drapes
 * them instead, once per loaded body and level, the way a cloth rests on a figure:
 *
 *  1. Ease. Each draped garment stands off the body by its kind's ease (a full shirt more, a
 *     waistcoat little), drawn back to a snug fit at the openings that are gathered (a collar,
 *     a cuff, a waistband, a breeches' knee band) and under anything worn over it, so a shirt
 *     blouses where it shows and lies flat under a waistcoat.
 *  2. Tension. Cloth spans a hollow instead of following it: repeated outward-only relaxing
 *     fills the hollows between and under the chest, the spine's groove, the crease between the
 *     legs and the seat, while a gentle low-pass (Taubin, which does not shrink) takes out the
 *     small bumps; nothing ever goes nearer the body than MIN_M.
 *  3. Edges. Open edges are relaxed along their own line only, so a hem or a front edge runs
 *     clean instead of stepping like stairs, and keeps its length.
 *  4. Layers. A garment is draped after everything worn under it and stands outside it.
 *
 * Positions and normals change; topology, UVs, skin weights, meshes, materials and draw calls
 * do not. Every level of a body goes through the same pass from its own vertices, so the far
 * levels keep the near ones' silhouette. Which garments are draped and by how much is a fit,
 * not a measurement (liberty L-drape-3553).
 */
import * as THREE from 'three';

/** Draped kinds, by material name. `ease` is the stand-off (metres) where nothing gathers or
 * covers it (`easeArm` over the arms, for full sleeves); `gather` names the openings drawn snug (collar, cuff, waist, knee); `ramp` is how
 * far (metres along the cloth) from a gathered opening the ease takes to come in. */
export const KINDS = Object.freeze([
  // Frontier shirts of 1812 (tow linen, calico, check): cut full, a body's width and more, and
  // gathered at the neck and wrist, so they hang off the shoulders and blouse at the waist.
  { kind: 'shirt', full: true, mat: /^garment_upper__(shirt_(tow_linen|calico_blue|check_blue)_\d{4}|calico_shirt_madder_\d{4})$/, ease: 0.020, easeArm: 0.030, blouse: 0.012, hang: 0.2, folds: { cuff: 0.006, waist: 0.006, hem: 0.005 }, gather: ['collar', 'cuff'], ramp: 0.12 },
  { kind: 'shirt', mat: /^garment_upper__(shirt_(unbleached|striped)_\d{4}|shirt_linen)$/, ease: 0.011, easeArm: 0.024, blouse: 0.006, folds: { cuff: 0.004, waist: 0.004, hem: 0.003 }, gather: ['collar', 'cuff'], ramp: 0.12 },
  // Loose linen trousers (a labourer's, 1810s) hang straight from the seat and the knee.
  { kind: 'trousers', mat: /^garment_lower__trousers_linen_\d{4}$/, ease: 0.022, hang: 0.15, wave: 0.14, folds: { waist: 0.005, ankle: 0.005 }, gather: ['waist'], ramp: 0.16 },
  { kind: 'trousers', mat: /^garment_lower__(trousers_\w+|highwaist_pantaloons|skeleton_trousers_\w+|child_trousers_\d{4})$/, ease: 0.014, wave: 0.14, folds: { waist: 0.003, ankle: 0.003 }, gather: ['waist'], ramp: 0.16 },
  { kind: 'breeches', mat: /^garment_lower__(breeches_\w+|pantaloons_white_1812|overalls_linen_1812)$/, ease: 0.007, wave: 0.14, folds: { waist: 0.002, knee: 0.003 }, gather: ['waist', 'knee'], ramp: 0.12 },
  { kind: 'waistcoat', mat: /^garment_outer__waistcoat_\w+$/, ease: 0.005, folds: {}, gather: [], ramp: 0.08 },
]);
/** Folds: soft radial folds running out from each opening (a gathered neck, a cuff, a tucked
 * hem) FOLD_WAVE_M apart (a kind's `wave` where its cloth is cut coarser), fading over FOLD_REACH_M along the cloth; `folds` gives each
 * opening's depth (metres). A level whose edges are too long to draw them leaves them out. */
export const FOLD_WAVE_M = 0.09, FOLD_REACH_M = 0.16, FOLD_SHADE = 5;
/** Blousing: a shirt stands out above its tucked or loose hem (`blouse`, metres), most at
 * BLOUSE_AT_M up from the hem, gone by BLOUSE_TO_M. */
export const BLOUSE_AT_M = 0.07, BLOUSE_TO_M = 0.2;
/** No cloth hangs further off the body than this (metres). */
export const HANG_MAX_M = 0.06;

/** Nearest the body any draped cloth comes (metres), and the room kept under an outer layer. */
export const MIN_M = 0.004, UNDER_M = 0.004;
/** Relaxing: outward-only fill passes, then Taubin pairs, then edge passes. */
export const BODY_SMOOTH_ITERS = 30, FILL_ITERS = 60, TAUBIN_ITERS = 24, EDGE_ITERS = 12, LAMBDA = 0.5, MU = -0.53;
/** How far out from a body point a ray looks for a layer worn over it (metres). */
export const COVER_M = 0.09;
/** How fast cloth may stand off once out from under a layer (metres per metre along it). */
export const CEIL_SLOPE = 0.25, FLOOR_SLOPE = 0.25, SETTLE_ITERS = 3;

const smoothstep = (x) => { const t = Math.max(0, Math.min(1, x)); return t * t * (3 - 2 * t); };
const kindOf = (m) => KINDS.find((k) => k.mat.test(m?.material?.name ?? '')) ?? null;

/** Positions of a skinned mesh's vertices at bind, in one shared space. */
function bindPositions(mesh) {
  const pos = mesh.geometry.attributes.position, n = pos.count, P = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
const indexOf = (g) => g.index ? g.index.array : Uint32Array.from({ length: g.attributes.position.count }, (_, i) => i);

/** Weld several meshes into one graph of points (UV seams and pieces that meet become one point). */
function weldMeshes(meshes) {
  const parts = meshes.map((mesh) => ({ mesh, P: bindPositions(mesh), idx: indexOf(mesh.geometry) }));
  const keys = new Map(), P = [], members = [];
  for (const part of parts) {
    const n = part.P.length / 3; part.group = new Int32Array(n);
    for (let i = 0; i < n; i++) {
      // Exact weld key: positions to 0.05 mm, packed into one number (51 bits).
      const k = ((Math.round(part.P[i * 3] * 2e4) + 65536) * 131072 + (Math.round(part.P[i * 3 + 1] * 2e4) + 65536)) * 131072 + (Math.round(part.P[i * 3 + 2] * 2e4) + 65536);
      let g = keys.get(k);
      if (g === undefined) { g = P.length / 3; keys.set(k, g); P.push(part.P[i * 3], part.P[i * 3 + 1], part.P[i * 3 + 2]); members.push([]); }
      part.group[i] = g; members[g].push([part, i]);
    }
  }
  const G = P.length / 3, nb = Array.from({ length: G }, () => new Set()), edgeCount = new Map(), tris = [];
  for (const part of parts) for (let t = 0; t < part.idx.length; t += 3) {
    const a = part.group[part.idx[t]], b = part.group[part.idx[t + 1]], c = part.group[part.idx[t + 2]];
    if (a === b || b === c || a === c) continue;
    tris.push(a, b, c);
    for (const [x, y] of [[a, b], [b, c], [c, a]]) { nb[x].add(y); nb[y].add(x); const k = x < y ? x * G + y : y * G + x; edgeCount.set(k, (edgeCount.get(k) ?? 0) + 1); }
  }
  const edgeNb = Array.from({ length: G }, () => []);
  for (const [k, c] of edgeCount) if (c === 1) { const x = Math.floor(k / G), y = k % G; edgeNb[x].push(y); edgeNb[y].push(x); }
  return { parts, P: Float64Array.from(P), G, nb: nb.map((s) => Int32Array.from(s)), edgeNb, tris: Int32Array.from(tris), members };
}

/** A dense box of cells over points (padded by `pad` cells), with items listed per cell (CSR). */
function cellBox(P, cell, pad) {
  let lx = Infinity, ly = Infinity, lz = Infinity, hx = -Infinity, hy = -Infinity, hz = -Infinity;
  for (let i = 0; i < P.length; i += 3) { if (P[i] < lx) lx = P[i]; if (P[i] > hx) hx = P[i]; if (P[i + 1] < ly) ly = P[i + 1]; if (P[i + 1] > hy) hy = P[i + 1]; if (P[i + 2] < lz) lz = P[i + 2]; if (P[i + 2] > hz) hz = P[i + 2]; }
  if (!(lx <= hx)) { lx = ly = lz = 0; hx = hy = hz = 0; }
  const ox = lx - pad * cell, oy = ly - pad * cell, oz = lz - pad * cell;
  const nx = Math.floor((hx - ox) / cell) + pad + 1, ny = Math.floor((hy - oy) / cell) + pad + 1, nz = Math.floor((hz - oz) / cell) + pad + 1;
  return { ox, oy, oz, nx, ny, nz, cell, ix: (x) => Math.floor((x - ox) / cell), iy: (y) => Math.floor((y - oy) / cell), iz: (z) => Math.floor((z - oz) / cell) };
}
function listCells(box, count, cellsOf) {
  const n = box.nx * box.ny * box.nz, start = new Int32Array(n + 1);
  cellsOf((c) => { start[c + 1]++; });
  for (let c = 0; c < n; c++) start[c + 1] += start[c];
  const fill = start.slice(0, n), items = new Int32Array(start[n]);
  cellsOf((c, item) => { items[fill[c]++] = item; });
  return { start, items };
  void count;
}

/** A uniform grid over points, for nearest-point queries. */
function pointGrid(P, cell) {
  const box = cellBox(P, cell, 1), { nx, ny, nz } = box, n = P.length / 3;
  const { start, items } = listCells(box, n, (emit) => { for (let i = 0; i < n; i++) emit((box.ix(P[i * 3]) * ny + box.iy(P[i * 3 + 1])) * nz + box.iz(P[i * 3 + 2]), i); });
  return function nearest(x, y, z, reach = 4) {
    const cx = box.ix(x), cy = box.iy(y), cz = box.iz(z);
    let best = Infinity, bi = -1;
    for (let r = 0; r <= reach; r++) {
      for (let a = cx - r; a <= cx + r; a++) {
        if (a < 0 || a >= nx) continue;
        for (let b = cy - r; b <= cy + r; b++) {
          if (b < 0 || b >= ny) continue;
          const edgeAB = a === cx - r || a === cx + r || b === cy - r || b === cy + r;
          for (let c = cz - r; c <= cz + r; c += (edgeAB || r === 0) ? 1 : 2 * r) {
            if (c < 0 || c >= nz) continue;
            const k = (a * ny + b) * nz + c;
            for (let j = start[k], e = start[k + 1]; j < e; j++) { const i = items[j], dx = P[i * 3] - x, dy = P[i * 3 + 1] - y, dz = P[i * 3 + 2] - z, d = dx * dx + dy * dy + dz * dz; if (d < best) { best = d; bi = i; } }
          }
        }
      }
      if (bi >= 0 && Math.sqrt(best) < r * cell) break;
    }
    return bi;
  };
}

/** A uniform grid over triangles, for short rays (Möller–Trumbore). */
function triangleGrid(P, tris, cell) {
  const box = cellBox(P, cell, 4), { nx, ny, nz } = box, T = tris.length / 3;
  const { start, items } = listCells(box, T, (emit) => {
    for (let t = 0; t < tris.length; t += 3) {
      const a = tris[t] * 3, b = tris[t + 1] * 3, c = tris[t + 2] * 3;
      const x0 = box.ix(Math.min(P[a], P[b], P[c])), x1 = box.ix(Math.max(P[a], P[b], P[c]));
      const y0 = box.iy(Math.min(P[a + 1], P[b + 1], P[c + 1])), y1 = box.iy(Math.max(P[a + 1], P[b + 1], P[c + 1]));
      const z0 = box.iz(Math.min(P[a + 2], P[b + 2], P[c + 2])), z1 = box.iz(Math.max(P[a + 2], P[b + 2], P[c + 2]));
      for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) for (let z = z0; z <= z1; z++) emit((x * ny + y) * nz + z, t);
    }
  });
  const seen = new Int32Array(T + 1); let stamp = 0;
  /** Distance along (dx,dy,dz) (unit) from (ox,oy,oz) to the first triangle within `far`, or Infinity. */
  return function cast(ox, oy, oz, dx, dy, dz, far) {
    const steps = Math.ceil(far / (cell * 0.5)) + 1; let best = Infinity, last = -1;
    if (++stamp > 2e9) { seen.fill(0); stamp = 1; }
    for (let s = 0; s <= steps; s++) {
      const d = Math.min(far, s * cell * 0.5), x = box.ix(ox + dx * d), y = box.iy(oy + dy * d), z = box.iz(oz + dz * d);
      if (x < 0 || y < 0 || z < 0 || x >= nx || y >= ny || z >= nz) continue;
      const k = (x * ny + y) * nz + z; if (k === last) continue; last = k;
      for (let j = start[k], e = start[k + 1]; j < e; j++) {
        const tt = items[j]; if (seen[tt / 3] === stamp) continue; seen[tt / 3] = stamp;
        const a = tris[tt] * 3, b = tris[tt + 1] * 3, c = tris[tt + 2] * 3;
        const e1x = P[b] - P[a], e1y = P[b + 1] - P[a + 1], e1z = P[b + 2] - P[a + 2];
        const e2x = P[c] - P[a], e2y = P[c + 1] - P[a + 1], e2z = P[c + 2] - P[a + 2];
        const px = dy * e2z - dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y - dy * e2x;
        const det = e1x * px + e1y * py + e1z * pz; if (Math.abs(det) < 1e-12) continue;
        const inv = 1 / det, tx = ox - P[a], ty = oy - P[a + 1], tz = oz - P[a + 2];
        const u = (tx * px + ty * py + tz * pz) * inv; if (u < 0 || u > 1) continue;
        const qx = ty * e1z - tz * e1y, qy = tz * e1x - tx * e1z, qz = tx * e1y - ty * e1x;
        const v = (dx * qx + dy * qy + dz * qz) * inv; if (v < 0 || u + v > 1) continue;
        const h = (e2x * qx + e2y * qy + e2z * qz) * inv;
        if (h > 0 && h <= far && h < best) best = h;
      }
    }
    return best;
  };
}

/** Area-weighted normals of a welded graph's points. */
function graphNormals(P, tris, G) {
  const N = new Float64Array(G * 3);
  for (let t = 0; t < tris.length; t += 3) {
    const a = tris[t] * 3, b = tris[t + 1] * 3, c = tris[t + 2] * 3;
    const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2], vx = P[c] - P[a], vy = P[c + 1] - P[a + 1], vz = P[c + 2] - P[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    for (const g of [a, b, c]) { N[g] += nx; N[g + 1] += ny; N[g + 2] += nz; }
  }
  for (let g = 0; g < G; g++) { const l = Math.hypot(N[g * 3], N[g * 3 + 1], N[g * 3 + 2]) || 1; N[g * 3] /= l; N[g * 3 + 1] /= l; N[g * 3 + 2] /= l; }
  return N;
}

/** The body's points and outward normals at bind, with each point's main bone. */
const fields = new WeakMap();
function* bodyFieldSteps(body) {
  const known = fields.get(body); if (known) return known;
  const W = weldMeshes([body]), N = graphNormals(W.P, W.tris, W.G);
  yield;
  const bone = new Int32Array(W.G), si = body.geometry.attributes.skinIndex, sw = body.geometry.attributes.skinWeight;
  for (let g = 0; g < W.G; g++) {
    const [part, i] = W.members[g][0]; let best = -1, bw = -1;
    for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); if (w > bw) { bw = w; best = si.getComponent(i, k); } }
    bone[g] = best;
  }
  // The body low-passed (Taubin, no shrinking): the surface cloth is eased from, so cloth spans
  // the small forms (nipples, navel, the ribs and the bulge at the fork) instead of tracing them.
  const S = Float64Array.from(W.P), Q = new Float64Array(S.length);
  for (let it = 0; it < BODY_SMOOTH_ITERS * 2; it++) {
    const w = it % 2 ? MU : LAMBDA;
    for (let g = 0; g < W.G; g++) {
      const l = W.nb[g]; if (!l.length) { Q[g * 3] = S[g * 3]; Q[g * 3 + 1] = S[g * 3 + 1]; Q[g * 3 + 2] = S[g * 3 + 2]; continue; }
      let cx = 0, cy = 0, cz = 0; for (const h of l) { cx += S[h * 3]; cy += S[h * 3 + 1]; cz += S[h * 3 + 2]; }
      Q[g * 3] = S[g * 3] + w * (cx / l.length - S[g * 3]); Q[g * 3 + 1] = S[g * 3 + 1] + w * (cy / l.length - S[g * 3 + 1]); Q[g * 3 + 2] = S[g * 3 + 2] + w * (cz / l.length - S[g * 3 + 2]);
    }
    S.set(Q);
    if (it % 8 === 7) yield;
  }
  const field = { P: W.P, N, S, bone, G: W.G, near: pointGrid(W.P, 0.03), names: body.skeleton.bones.map((b) => b.name) };
  fields.set(body, field);
  return field;
}
const bodyField = (body) => runSteps(bodyFieldSteps(body));

/** Which opening a boundary loop is, read from the body bones under it. */
function openingOf(loopGroups, W, B, anchor) {
  const votes = new Map();
  for (const g of loopGroups) { const nm = B.names[B.bone[anchor[g]]] ?? ''; votes.set(nm, (votes.get(nm) ?? 0) + 1); }
  const top = [...votes].sort((a, b) => b[1] - a[1])[0]?.[0] ?? '';
  if (/^(neck|head|jaw)/.test(top)) return 'collar';
  if (/^(hand|lowerarm|thumb|index|middle|ring|pinky)/.test(top)) return 'cuff';
  if (/^(calf|foot|ball)/.test(top)) return 'ankle';
  if (/^(thigh)/.test(top)) return 'knee';
  if (/^(pelvis|spine|root)/.test(top)) return 'waist';
  return 'hem';
}

/** Boundary loops (as point lists) of a welded graph. */
function loopsOf(W) {
  const seen = new Uint8Array(W.G), loops = [];
  for (let s = 0; s < W.G; s++) {
    if (seen[s] || W.edgeNb[s].length === 0) continue;
    const loop = [], stack = [s]; seen[s] = 1;
    while (stack.length) { const g = stack.pop(); loop.push(g); for (const h of W.edgeNb[g]) if (!seen[h]) { seen[h] = 1; stack.push(h); } }
    loops.push(loop);
  }
  return loops;
}

/** Distance (metres along the cloth) from a set of seed points, by Dijkstra on the welded graph. */
function distanceFrom(W, seeds) {
  const D = new Float64Array(W.G).fill(Infinity), heap = [];
  const push = (g, d) => { heap.push([d, g]); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p][0] <= heap[i][0]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
  for (const g of seeds) { D[g] = 0; push(g, 0); }
  while (heap.length) {
    const [d, g] = pop(); if (d > D[g]) continue;
    for (const h of W.nb[g]) { const e = d + Math.hypot(W.P[g * 3] - W.P[h * 3], W.P[g * 3 + 1] - W.P[h * 3 + 1], W.P[g * 3 + 2] - W.P[h * 3 + 2]); if (e < D[h]) { D[h] = e; push(h, e); } }
  }
  return D;
}

/** A ceiling field made gentle: c(g) = min over h (c(h) + slope * path length), by Dijkstra. */
function smoothCeiling(W, C, slope) {
  const heap = [];
  const push = (g, d) => { heap.push([d, g]); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p][0] <= heap[i][0]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
  for (let g = 0; g < W.G; g++) if (Number.isFinite(C[g])) push(g, C[g]);
  while (heap.length) {
    const [d, g] = pop(); if (d > C[g]) continue;
    for (const h of W.nb[g]) { const e = d + slope * Math.hypot(W.P[g * 3] - W.P[h * 3], W.P[g * 3 + 1] - W.P[h * 3 + 1], W.P[g * 3 + 2] - W.P[h * 3 + 2]); if (e < C[h]) { C[h] = e; push(h, e); } }
  }
}

/** Write welded positions and normals back to every member vertex (bind space -> mesh space). */
function writeBack(W, N) {
  for (const part of W.parts) {
    const mesh = part.mesh, pos = mesh.geometry.attributes.position, nrm = mesh.geometry.attributes.normal;
    const Binv = mesh.bindMatrix.clone().invert(), nBack = new THREE.Matrix3().getNormalMatrix(Binv), v = new THREE.Vector3();
    const clampN = pos.normalized ? (x) => Math.max(-1, Math.min(1, x)) : (x) => x;
    for (let i = 0; i < pos.count; i++) {
      const g = part.group[i];
      v.set(W.P[g * 3], W.P[g * 3 + 1], W.P[g * 3 + 2]).applyMatrix4(Binv);
      pos.setXYZ(i, clampN(v.x), clampN(v.y), clampN(v.z));
      if (nrm && N) { v.set(N[g * 3], N[g * 3 + 1], N[g * 3 + 2]).applyMatrix3(nBack).normalize(); nrm.setXYZ(i, v.x, v.y, v.z); }
    }
    pos.needsUpdate = true; if (nrm && N) nrm.needsUpdate = true;
    mesh.geometry.computeBoundingSphere(); mesh.geometry.computeBoundingBox();
  }
}

/** Fold depths per point (or null): for each opening with a depth, folds radiate from it, as
 * many round it as fit FOLD_WAVE_M apart, fading over FOLD_REACH_M along the cloth. */
function foldsOf(W, loops, depths, wave = FOLD_WAVE_M) {
  const { P, G, tris } = W;
  let len = 0, n = 0; for (let t = 0; t < tris.length; t += 3) { const a = tris[t] * 3, b = tris[t + 1] * 3; len += Math.hypot(P[a] - P[b], P[a + 1] - P[b + 1], P[a + 2] - P[b + 2]); n++; }
  const edge = n ? len / n : Infinity;
  // A level needs four edges to a fold to draw it (full depth), and loses it by three.
  const lod = Math.max(0, Math.min(1, (wave / 3 - edge) / (wave / 3 - wave / 4)));
  if (lod <= 0) return null;
  const sources = [];
  for (const { loop, type } of loops) {
    const depth = depths[type]; if (!depth || loop.length < 6) continue;
    // The opening's plane: its centroid, and its normal from the points' spread (power iteration).
    let cx = 0, cy = 0, cz = 0; for (const g of loop) { cx += P[g * 3]; cy += P[g * 3 + 1]; cz += P[g * 3 + 2]; }
    cx /= loop.length; cy /= loop.length; cz /= loop.length;
    const C = [0, 0, 0, 0, 0, 0, 0, 0, 0];
    for (const g of loop) { const d = [P[g * 3] - cx, P[g * 3 + 1] - cy, P[g * 3 + 2] - cz]; for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i * 3 + j] += d[i] * d[j]; }
    const power = (v, deflate) => { for (let it = 0; it < 40; it++) { let w = [0, 1, 2].map((i) => C[i * 3] * v[0] + C[i * 3 + 1] * v[1] + C[i * 3 + 2] * v[2]); if (deflate) { const k = w[0] * deflate[0] + w[1] * deflate[1] + w[2] * deflate[2]; w = w.map((x, i) => x - k * deflate[i]); } const l = Math.hypot(...w) || 1; v = w.map((x) => x / l); } return v; };
    const e1 = power([1, 0.3, 0.2]), e2 = power([0.2, 1, 0.3], e1);
    let r = 0; for (const g of loop) { const d = [P[g * 3] - cx, P[g * 3 + 1] - cy, P[g * 3 + 2] - cz]; r += Math.hypot(d[0] * e1[0] + d[1] * e1[1] + d[2] * e1[2], d[0] * e2[0] + d[1] * e2[1] + d[2] * e2[2]); }
    r /= loop.length;
    const k = Math.max(3, Math.round((2 * Math.PI * r) / wave));
    sources.push({ loop, depth: depth * lod, c: [cx, cy, cz], e1, e2, k });
  }
  if (!sources.length) return null;
  // Nearest opening along the cloth, and how far.
  const dist = new Float64Array(G).fill(Infinity), label = new Int32Array(G).fill(-1), heap = [];
  const push = (g, d) => { heap.push([d, g]); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p][0] <= heap[i][0]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, rr = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (rr < heap.length && heap[rr][0] < heap[m][0]) m = rr; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
  sources.forEach((s, i) => { for (const g of s.loop) { dist[g] = 0; label[g] = i; push(g, 0); } });
  while (heap.length) {
    const [d, g] = pop(); if (d > dist[g] || d > FOLD_REACH_M) continue;
    for (const h of W.nb[g]) { const e = d + Math.hypot(P[g * 3] - P[h * 3], P[g * 3 + 1] - P[h * 3 + 1], P[g * 3 + 2] - P[h * 3 + 2]); if (e < dist[h]) { dist[h] = e; label[h] = label[g]; push(h, e); } }
  }
  const out = new Float64Array(G);
  for (let g = 0; g < G; g++) {
    const s = sources[label[g]]; if (!s || dist[g] >= FOLD_REACH_M) continue;
    const d = [P[g * 3] - s.c[0], P[g * 3 + 1] - s.c[1], P[g * 3 + 2] - s.c[2]];
    const th = Math.atan2(d[0] * s.e2[0] + d[1] * s.e2[1] + d[2] * s.e2[2], d[0] * s.e1[0] + d[1] * s.e1[1] + d[2] * s.e1[2]);
    // Right at the opening the folds are tight gathers; they open out and fade along the cloth.
    const fade = 1 - smoothstep(dist[g] / FOLD_REACH_M);
    out[g] = s.depth * fade * 0.5 * (1 - Math.cos(s.k * th));
  }
  return out;
}

/** Drape one garment (its welded graph) over the body and what is under it. */
function* drapeOne(W, kind, B, underCast, overCast, outside = null) {
  const { P, G, nb, edgeNb } = W;
  // Points of a piece worn outside the next layer (a shirt's skirt or tail over leggings or
  // trousers) take that layer as a floor, never as a ceiling.
  const overOf = (g) => (outside && outside.mask[g] ? outside.over : overCast), underOf = (g) => (outside && outside.mask[g] ? outside.under : underCast);
  // Anchor: the nearest body point, and the cloth's offset along its normal.
  const anchor = new Int32Array(G);
  const reanchor = () => { for (let g = 0; g < G; g++) anchor[g] = Math.max(0, B.near(P[g * 3], P[g * 3 + 1], P[g * 3 + 2])); };
  reanchor();
  const offsetOf = (g) => { const a = anchor[g] * 3; return (P[g * 3] - B.P[a]) * B.N[a] + (P[g * 3 + 1] - B.P[a + 1]) * B.N[a + 1] + (P[g * 3 + 2] - B.P[a + 2]) * B.N[a + 2]; };
  // Openings: gathered ones draw the ease in.
  const loops = loopsOf(W).map((loop) => ({ loop, type: openingOf(loop, W, B, anchor) })), seeds = [];
  for (const { loop, type } of loops) if (kind.gather.includes(type)) seeds.push(...loop);
  const D = seeds.length ? distanceFrom(W, seeds) : new Float64Array(G).fill(Infinity);
  const hems = []; if (kind.blouse) for (const { loop, type } of loops) if (type === 'waist' || type === 'hem') hems.push(...loop);
  const DH = hems.length ? distanceFrom(W, hems) : null;
  // Floor: nearest the cloth may come along the body normal (the body, or a draped layer under it).
  // Ceiling: room under whatever is worn over it.
  const floor = new Float64Array(G), ceil = new Float64Array(G).fill(Infinity), ease = new Float64Array(G);
  // The floor rises gently toward what is under the cloth (FLOOR_SLOPE), so cloth that runs past
  // an under layer's edge (a waistcoat over a trouser band) clears the edge rather than cutting it.
  const floorNow = () => {
    for (let g = 0; g < G; g++) {
      const a = anchor[g] * 3;
      // Only what lies under the cloth over it counts (coat buttons are not under a waistcoat).
      const oc = overOf(g), uc = underOf(g);
      const over = oc ? oc(B.P[a], B.P[a + 1], B.P[a + 2], B.N[a], B.N[a + 1], B.N[a + 2], COVER_M) : Infinity;
      const under = uc ? uc(B.P[a], B.P[a + 1], B.P[a + 2], B.N[a], B.N[a + 1], B.N[a + 2], Math.min(COVER_M, over)) : Infinity;
      floor[g] = -Math.max(MIN_M, Number.isFinite(under) ? under + UNDER_M : 0);
    }
    smoothCeiling(W, floor, FLOOR_SLOPE);
    for (let g = 0; g < G; g++) floor[g] = Math.max(MIN_M, -floor[g]);
  };
  floorNow();
  yield;
  for (let g = 0; g < G; g++) {
    const a = anchor[g] * 3, nx = B.N[a], ny = B.N[a + 1], nz = B.N[a + 2];
    const oc = overOf(g);
    const over = oc ? oc(B.P[a], B.P[a + 1], B.P[a + 2], nx, ny, nz, COVER_M) : Infinity;
    const off0 = offsetOf(g);
    // Cloth drawn through what is worn over it (a shirt's shoulder out through a coat) goes under it too.
    if (Number.isFinite(over)) ceil[g] = Math.max(MIN_M, over - UNDER_M);
    const t = Math.min(1, D[g] / kind.ramp), s = t * t * (3 - 2 * t);
    const arm = kind.easeArm != null && /^(upperarm|lowerarm)/.test(B.names[B.bone[anchor[g]]] ?? '');
    // The eased point: off the low-passed body by MIN_M and the kind's ease, read as an offset
    // from the true body; never nearer than the floor.
    const want = MIN_M + (arm ? kind.easeArm : kind.ease) * s;
    const smooth = (B.S[a] - B.P[a]) * nx + (B.S[a + 1] - B.P[a + 1]) * ny + (B.S[a + 2] - B.P[a + 2]) * nz;
    const blouse = DH ? kind.blouse * smoothstep(DH[g] / BLOUSE_AT_M) * (1 - smoothstep((DH[g] - BLOUSE_AT_M) / (BLOUSE_TO_M - BLOUSE_AT_M))) : 0;
    ease[g] = Math.max(floor[g], smooth + want + blouse);
    // A skirt or tail worn outside never comes in closer than it was cut: the leg moves under it.
    if (outside && outside.mask[g]) ease[g] = Math.max(ease[g], Math.min(off0, HANG_MAX_M + kind.ease));
  }
  // Hang: full cloth falls from where it is held (a shirt from the chest and shoulders, loose
  // trousers from the seat and thigh) instead of following the body in at the waist or the knee:
  // going down the cloth, its offset may shrink by at most `hang` metres per metre.
  if (kind.hang) {
    const holds = (g) => /^(spine|pelvis|thigh|calf|root)/.test(B.names[B.bone[anchor[g]]] ?? '');
    const V = Float64Array.from(ease), heap = [];
    const push = (g, d) => { heap.push([d, g]); let i = heap.length - 1; while (i > 0) { const q = (i - 1) >> 1; if (heap[q][0] <= heap[i][0]) break; [heap[q], heap[i]] = [heap[i], heap[q]]; i = q; } };
    const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
    for (let g = 0; g < G; g++) if (holds(g)) push(g, -V[g]);
    while (heap.length) {
      const [nd, g] = pop(); if (-nd < V[g]) continue;
      for (const h of nb[g]) {
        if (!holds(h) || P[h * 3 + 1] >= P[g * 3 + 1]) continue;
        const v = V[g] - kind.hang * Math.hypot(P[g * 3] - P[h * 3], P[g * 3 + 1] - P[h * 3 + 1], P[g * 3 + 2] - P[h * 3 + 2]);
        if (v > V[h]) { V[h] = v; push(h, -v); }
      }
    }
    for (let g = 0; g < G; g++) ease[g] = Math.max(ease[g], Math.min(V[g], HANG_MAX_M));
  }
  // Near the edge of what covers it, cloth comes out from under gradually (CEIL_SLOPE metres of
  // room per metre along the cloth), so a shirt does not stand proud right at a waistcoat's edge.
  smoothCeiling(W, ceil, CEIL_SLOPE);
  for (let g = 0; g < G; g++) ease[g] = Math.max(floor[g], Math.min(ease[g], ceil[g]));
  const clampG = (g) => {
    const a = anchor[g] * 3, off = offsetOf(g), want = Math.min(ceil[g], Math.max(floor[g], off));
    if (want !== off) { const d = want - off; P[g * 3] += B.N[a] * d; P[g * 3 + 1] += B.N[a + 1] * d; P[g * 3 + 2] += B.N[a + 2] * d; }
  };
  // 1. Ease: each point to its eased offset (in or out: a proxy traced the body's small forms).
  for (let g = 0; g < G; g++) {
    const a = anchor[g] * 3, d = ease[g] - offsetOf(g);
    P[g * 3] += B.N[a] * d; P[g * 3 + 1] += B.N[a + 1] * d; P[g * 3 + 2] += B.N[a + 2] * d;
  }
  const Q = new Float64Array(G * 3);
  const step = (g, w, outwardOnly, edge) => {
    const list = edge ? edgeNb[g] : nb[g]; if (!list.length) return;
    let cx = 0, cy = 0, cz = 0; for (const h of list) { cx += P[h * 3]; cy += P[h * 3 + 1]; cz += P[h * 3 + 2]; }
    cx = cx / list.length - P[g * 3]; cy = cy / list.length - P[g * 3 + 1]; cz = cz / list.length - P[g * 3 + 2];
    if (outwardOnly) {
      const a = anchor[g] * 3, o = cx * B.N[a] + cy * B.N[a + 1] + cz * B.N[a + 2];
      if (o < 0) { cx -= o * B.N[a]; cy -= o * B.N[a + 1]; cz -= o * B.N[a + 2]; }
    }
    Q[g * 3] = P[g * 3] + w * cx; Q[g * 3 + 1] = P[g * 3 + 1] + w * cy; Q[g * 3 + 2] = P[g * 3 + 2] + w * cz;
  };
  const isEdge = (g) => edgeNb[g].length > 0;
  const pass = (w, outwardOnly, edgesOnly) => {
    for (let g = 0; g < G; g++) {
      if (isEdge(g)) { if (edgeNb[g].length === 2) step(g, w, outwardOnly, true); else { Q[g * 3] = P[g * 3]; Q[g * 3 + 1] = P[g * 3 + 1]; Q[g * 3 + 2] = P[g * 3 + 2]; } }
      else if (edgesOnly) { Q[g * 3] = P[g * 3]; Q[g * 3 + 1] = P[g * 3 + 1]; Q[g * 3 + 2] = P[g * 3 + 2]; }
      else step(g, w, outwardOnly, false);
    }
    P.set(Q); for (let g = 0; g < G; g++) clampG(g);
  };
  // 2. Tension: hollows filled, then the small bumps taken out without shrinking.
  for (let it = 0; it < FILL_ITERS; it++) { pass(LAMBDA, true, false); if (it % 15 === 14) reanchor(); if (it % 6 === 5) yield; }
  for (let it = 0; it < TAUBIN_ITERS; it++) { pass(LAMBDA, false, false); pass(MU, false, false); if (it % 8 === 7) reanchor(); if (it % 3 === 2) yield; }
  // 3. Edges run clean along their own line.
  for (let it = 0; it < EDGE_ITERS; it++) { pass(LAMBDA, false, true); pass(MU, false, true); }
  yield;
  // 4. Settle on what is under it: the floor read again where each point now lies, then a light
  // smoothing, so no under layer comes through after the cloth has moved.
  for (let it = 0; it < SETTLE_ITERS; it++) { reanchor(); floorNow(); for (let g = 0; g < G; g++) clampG(g); if (it < SETTLE_ITERS - 1) { pass(LAMBDA, false, false); pass(MU, false, false); } yield; }
  // 5. Folds, last, so no smoothing takes them out; the floor and ceiling still hold.
  const fold = foldsOf(W, loops, kind.folds ?? {}, kind.wave ?? FOLD_WAVE_M);
  if (fold) {
    for (let g = 0; g < G; g++) if (fold[g] > 0) { const a = anchor[g] * 3; P[g * 3] += B.N[a] * fold[g]; P[g * 3 + 1] += B.N[a + 1] * fold[g]; P[g * 3 + 2] += B.N[a + 2] * fold[g]; clampG(g); }
    // Shading reads the folds FOLD_SHADE times deeper than they are built (what a game's
    // wrinkle map does): the light catches them without the cloth standing any further out.
    W.shadeP = Float64Array.from(P);
    for (let g = 0; g < G; g++) if (fold[g] > 0) { const a = anchor[g] * 3, d = fold[g] * (FOLD_SHADE - 1); W.shadeP[g * 3] += B.N[a] * d; W.shadeP[g * 3 + 1] += B.N[a + 1] * d; W.shadeP[g * 3 + 2] += B.N[a + 2] * d; }
  }
  return anchor;
}

/**
 * Drape a loaded body's garments (see the header). `root` is a parsed glTF scene; returns a
 * report { draped: [{ kind, meshes, points }] } and stores it on root.userData.chicagoDrape.
 */
export function* drapeGarmentsSteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.position) skinned.push(o); });
  const body = skinned.find((m) => m.material?.name === 'skin');
  const report = { draped: [] };
  if (!body) return report;
  // Garments grouped by kind and material; ordered inside-out: by layer (shirts, then trousers,
  // then waistcoats), and within a layer by how far off the body they sit.
  const groups = new Map();
  for (const m of skinned) { const k = kindOf(m); if (!k) continue; const key = m.material.name; if (!groups.has(key)) groups.set(key, { kind: k, meshes: [] }); groups.get(key).meshes.push(m); }
  if (!groups.size) return report;
  const B = yield* bodyFieldSteps(body);
  const list = [];
  for (const grp of groups.values()) {
    grp.W = weldMeshes(grp.meshes);
    let s = 0; for (let g = 0; g < grp.W.G; g++) { const a = B.near(grp.W.P[g * 3], grp.W.P[g * 3 + 1], grp.W.P[g * 3 + 2]) * 3; s += (grp.W.P[g * 3] - B.P[a]) * B.N[a] + (grp.W.P[g * 3 + 1] - B.P[a + 1]) * B.N[a + 1] + (grp.W.P[g * 3 + 2] - B.P[a + 2]) * B.N[a + 2]; }
    grp.mean = s / Math.max(1, grp.W.G); list.push(grp);
    yield;
  }
  list.sort((a, b) => (layerRank(a.meshes[0]) - layerRank(b.meshes[0])) || (a.mean - b.mean));
  // Everything that is not draped but is worn (coats, braces, other garments) bounds the cloth
  // by its layer: a piece of a lower rank (braces under a waistcoat) is a floor, a piece of a
  // higher rank (a coat over a shirt) a ceiling; pieces of the same rank are left to each other.
  // A piece some people leave off is never a ceiling (the cloth under it must stand alone).
  const fixed = skinned.filter((m) => m !== body && !kindOf(m) && /^(garment|accessory)/.test(m.material?.name ?? '') && layerRank(m) > 0);
  const fixedCasts = [1, 2, 3, 4].map((r) => { const ms = fixed.filter((m) => layerRank(m) === r && (r < 3 || !HIDEABLE.test(m.name))); if (!ms.length) return null; const W = weldMeshes(ms); return triangleGrid(W.P, W.tris, 0.03); });
  const doneCasts = [];
  // Under layers: the outermost one met (the floor is over all of them); over layers: the nearest.
  const outermost = (casts) => casts.length ? (ox, oy, oz, dx, dy, dz, far) => { let best = -Infinity; for (const c of casts) { const d = c(ox, oy, oz, dx, dy, dz, far); if (Number.isFinite(d) && d > best) best = d; } return best > -Infinity ? best : Infinity; } : null;
  const nearest = (casts) => casts.length ? (ox, oy, oz, dx, dy, dz, far) => { let best = Infinity; for (const c of casts) { const d = c(ox, oy, oz, dx, dy, dz, far); if (d < best) best = d; } return best; } : null;
  for (const [i, grp] of list.entries()) {
    const rank = layerRank(grp.meshes[0]);
    const below = fixedCasts.filter((c, k) => c && k + 1 < rank), above = fixedCasts.filter((c, k) => c && k + 1 > rank);
    const underCast = outermost([...doneCasts, ...below]);
    const laterCasts = list.slice(i + 1).filter((o) => !o.meshes.some((m) => HIDEABLE.test(m.name))).map((o) => ({ rank: layerRank(o.meshes[0]), cast: triangleGrid(o.W.P, o.W.tris, 0.03) }));
    const overCast = nearest([...laterCasts.map((o) => o.cast), ...above]);
    // A shirt's skirt or tail hangs over the leggings or trousers (rank 2): for its points they
    // are under, and only what is worn over both (a waistcoat, a coat) bounds it.
    let outside = null;
    if (rank === 1 && grp.W.parts.some((p) => OUTSIDE.test(p.mesh.name))) {
      const mask = new Uint8Array(grp.W.G);
      for (const part of grp.W.parts) if (OUTSIDE.test(part.mesh.name)) for (const g of part.group) mask[g] = 1;
      outside = {
        mask,
        under: outermost([...doneCasts, ...laterCasts.filter((o) => o.rank === 2).map((o) => o.cast), ...fixedCasts.filter((c, k) => c && k + 1 <= 2)]),
        over: nearest([...laterCasts.filter((o) => o.rank > 2).map((o) => o.cast), ...fixedCasts.filter((c, k) => c && k + 1 > 2)]),
      };
    }
    yield* drapeOne(grp.W, grp.kind, B, underCast, overCast, outside);
    writeBack(grp.W, graphNormals(grp.W.shadeP ?? grp.W.P, grp.W.tris, grp.W.G));
    doneCasts.push(triangleGrid(grp.W.P, grp.W.tris, 0.03));
    report.draped.push({ kind: grp.kind.kind, material: grp.meshes[0].material.name, meshes: grp.meshes.map((m) => m.name), points: grp.W.G });
  }
  root.userData.chicagoDrape = report;
  return report;
}

/** Pieces some people leave off (the `hide` lists of data/humans/variation and the looks):
 * never counted as cover, so what is under them is whole whether they are worn or not.
 * tools/test_human_drape.mjs fails when a data file hides a piece this does not name. */
export const HIDDEN_PIECES = Object.freeze([
  'silver_brooches', 'silver_arm_bands', 'blanket_stripes', 'blanket_wrap', 'trade_blanket',
  'legging_selvage', 'garters', 'lady_jacket_basque', 'lady_jacket_revers', 'waistcoat_brown',
  'cartridge_box_and_scabbard', 'sash_ends', 'epaulette_right', 'epaulette_left', 'neck_kerchief',
]);
export const HIDEABLE = new RegExp('(headwear|apron|_bib|_bow|frill|strap|skirts?(_|$)|jabot|neckerchief|cuffs|basket|pinafore|_ties|plumes)'
  + `|(^|_)(${HIDDEN_PIECES.join('|')})(_lod\\d+)?$`);
/** Exactly the pieces the data leaves off some people. */
export const LEFT_OFF = new RegExp(`(^|_)(${HIDDEN_PIECES.join('|')})(_lod\\d+)?$`);
/** A point is covered when every ray of a cone about its normal (the normal and CONE_N rays
 * tilted CONE_DEG off it) meets cover within COVERED_M (tilted rays: COVERED_M / cos); a
 * triangle is left out when its points, and every point within MARGIN_M along the cloth of
 * an uncovered one, are covered. The cone keeps openings (a waistcoat's front, an armhole, a
 * sleeve's end) whole however close the cloth lies across them; the margin keeps a band under
 * every edge for the cloth to lift off as the figure moves. */
export const COVERED_M = 0.08, LIFT_M = 0.0006, CONE_DEG = 50, CONE_N = 6, MARGIN_M = 0.02;
/** Which pieces may cover which: a mesh is covered only by a piece of a higher rank (skin under
 * shirts, shirts under trousers and braces, those under waistcoats, waistcoats under coats,
 * aprons, belts and wraps). Read from the piece's own name first (an 1812 coat is cut from a
 * garment_upper cloth, an officer's waistcoat shares his turnbacks' material), then its cloth. */
/** A shirt piece worn outside the trousers or leggings (hunting-shirt skirts, shirt tails). */
export const OUTSIDE = /_(skirt|tail)(_lod\d+)?$/;
export const OUTERWEAR = /(waistcoat)|(coat|jacket|tails|turnbacks|lapels|revers|basque|short_gown|blanket|apron|pinafore|belt|sash)/;
export function layerRank(mesh) {
  const n = mesh.material?.name ?? '';
  if (n === 'skin') return 0;
  if (!/^(garment_(upper|lower|outer)|accessory|footwear)__/.test(n)) return -1;
  const piece = OUTERWEAR.exec((mesh.name ?? '').replace(/_lod\d+$/, ''));
  if (piece) return piece[1] ? 3 : 4;
  if (/^garment_upper__/.test(n)) return 1;
  if (/^garment_outer__/.test(n)) return 4;
  return 2;
}

/**
 * Hidden-surface removal: the skin, and every garment worn under another, lose the triangles
 * that lie wholly under opaque cloth of a higher rank at bind, so nothing under the clothes
 * can come through them as the figure moves. Outer ranks go first, and cover counts only
 * where its own triangles were kept. Index buffers only; vertices, weights and materials
 * unchanged. Returns { culled: [{ mesh, before, after }] } and stores it on
 * root.userData.chicagoCull.
 */
export function* cullHiddenSteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.position && o.geometry.index && layerRank(o) >= 0) skinned.push(o); });
  const opaque = (m) => !m.material?.transparent && !(m.material?.alphaTest > 0) && m.material?.opacity !== 0;
  const canCover = (m) => layerRank(m) > 0 && !HIDEABLE.test(m.name) && opaque(m);
  const bind = new Map(skinned.map((m) => [m, bindPositions(m)]));
  const castOf = (m) => triangleGrid(bind.get(m), Int32Array.from(m.geometry.index.array), 0.03);
  const report = { culled: [] }, casts = new Map();
  const cos = Math.cos(CONE_DEG * Math.PI / 180), sin = Math.sin(CONE_DEG * Math.PI / 180), far = COVERED_M / cos;
  const order = skinned.filter((m) => layerRank(m) < 4).sort((p, q) => layerRank(q) - layerRank(p));
  for (const mesh of order) {
    yield;
    const rank = layerRank(mesh);
    const others = skinned.filter((c) => c !== mesh && canCover(c) && layerRank(c) > rank);
    if (!others.length) continue;
    for (const c of others) if (!casts.has(c)) casts.set(c, castOf(c));
    const hit = (x, y, z, dx, dy, dz, reach) => { for (const c of others) if (Number.isFinite(casts.get(c)(x, y, z, dx, dy, dz, reach))) return true; return false; };
    yield;
    const W = weldMeshes([mesh]), N = graphNormals(W.P, W.tris, W.G), covered = new Uint8Array(W.G);
    yield;
    for (let g = 0; g < W.G; g++) {
      if ((g & 511) === 511) yield;
      const nx = N[g * 3], ny = N[g * 3 + 1], nz = N[g * 3 + 2];
      const x = W.P[g * 3] + nx * LIFT_M, y = W.P[g * 3 + 1] + ny * LIFT_M, z = W.P[g * 3 + 2] + nz * LIFT_M;
      if (!hit(x, y, z, nx, ny, nz, COVERED_M)) continue;
      // Tangent frame about the normal, for the cone.
      let tx = Math.abs(nx) < 0.9 ? 1 : 0, ty = tx ? 0 : 1, tz = 0;
      const d = tx * nx + ty * ny + tz * nz; tx -= d * nx; ty -= d * ny; tz -= d * nz;
      const tl = Math.hypot(tx, ty, tz); tx /= tl; ty /= tl; tz /= tl;
      const bx = ny * tz - nz * ty, by = nz * tx - nx * tz, bz = nx * ty - ny * tx;
      let all = true;
      for (let k = 0; k < CONE_N && all; k++) {
        const a = (k / CONE_N) * Math.PI * 2, ca = Math.cos(a) * sin, sa = Math.sin(a) * sin;
        all = hit(x, y, z, nx * cos + tx * ca + bx * sa, ny * cos + ty * ca + by * sa, nz * cos + tz * ca + bz * sa, far);
      }
      covered[g] = all ? 1 : 0;
    }
    const seeds = []; for (let g = 0; g < W.G; g++) if (!covered[g]) seeds.push(g);
    const D = distanceFrom(W, seeds);
    const part = W.parts[0], idx = mesh.geometry.index.array, out = [];
    const gone = (g) => covered[g] && D[g] > MARGIN_M;
    for (let t = 0; t < idx.length; t += 3) {
      if (gone(part.group[idx[t]]) && gone(part.group[idx[t + 1]]) && gone(part.group[idx[t + 2]])) continue;
      out.push(idx[t], idx[t + 1], idx[t + 2]);
    }
    if (out.length === idx.length) continue;
    const Arr = idx.constructor; mesh.geometry.setIndex(new THREE.BufferAttribute(new Arr(out), 1));
    casts.delete(mesh);   // cover from here on counts only its kept triangles
    report.culled.push({ mesh: mesh.name, before: idx.length / 3, after: out.length / 3 });
  }
  root.userData.chicagoCull = report;
  return report;
}

/**
 * The last word on the body: after every tailoring pass (a taper, a pleat) has moved the cloth
 * again, no point of a draped garment lies nearer the body than MIN_M along the body's normal,
 * so no skin comes through between the passes. Positions only, of draped garments; returns
 * { settled: [{ mesh, points }] }.
 */
export function* settleOnBodySteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.position) skinned.push(o); });
  const body = skinned.find((m) => m.material?.name === 'skin'), report = { settled: [] };
  const draped = skinned.filter((m) => kindOf(m));
  if (!body || !draped.length) return report;
  const B = bodyField(body), W0 = B, N0 = B.N, near = B.near;
  for (const mesh of draped) {
    yield;
    const W = weldMeshes([mesh]); let moved = 0;
    for (let g = 0; g < W.G; g++) {
      const a = Math.max(0, near(W.P[g * 3], W.P[g * 3 + 1], W.P[g * 3 + 2])) * 3;
      const off = (W.P[g * 3] - W0.P[a]) * N0[a] + (W.P[g * 3 + 1] - W0.P[a + 1]) * N0[a + 1] + (W.P[g * 3 + 2] - W0.P[a + 2]) * N0[a + 2];
      if (off >= MIN_M) continue;
      const d = MIN_M - off; W.P[g * 3] += N0[a] * d; W.P[g * 3 + 1] += N0[a + 1] * d; W.P[g * 3 + 2] += N0[a + 2] * d; moved++;
    }
    if (!moved) continue;
    writeBack(W, null);   // a few millimetres: the normals (and the folds they shade) stand
    report.settled.push({ mesh: mesh.name, points: moved });
  }
  root.userData.chicagoSettle = report;
  return report;
}

/** Under another piece's cloth, a point takes that cloth's skin weights; past the cloth's edge
 * it blends back to its own over BAND_M along the inner cloth (skin: under the cloth only). */
export const BAND_M = 0.06, BIND_REACH_M = 0.03;

/**
 * Layers that move together. Each piece is skinned on its own, so a shirt under a waistcoat,
 * or trousers under its hem, bend with other bones in a stride and come out through it
 * however well they sit at bind. What layered clothing does in games: the cloth under a
 * piece follows that piece. Each point of every draped garment (shirts, trousers, breeches,
 * waistcoats; other pieces keep the weights their own passes gave them, and the skin is
 * hidden by cullHidden instead) that lies under opaque cloth of a higher rank (a ray out along
 * its normal meets it within BIND_REACH_M)
 * takes the skin weights of the nearest point of that cloth; past the cloth's edge a band
 * blends back to the point's own weights, so a shirt's visible front still bends with its own
 * bones while the part under the waistcoat's hem moves with the hem. Outer ranks go first, so
 * a chain (shirt under braces under waistcoat) follows the outermost. Weights only (four
 * influences, summing to the attribute's full scale); positions unchanged. Bodies with no
 * draped garment are left alone. Returns { bound: [{ mesh, points }] }, stored on
 * root.userData.chicagoBind.
 */
export function* bindLayersSteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.skinIndex && o.geometry?.attributes?.skinWeight && layerRank(o) >= 0) skinned.push(o); });
  const report = { bound: [] };
  if (!skinned.some((m) => kindOf(m))) { root.userData.chicagoBind = report; return report; }
  const opaque = (m) => !m.material?.transparent && !(m.material?.alphaTest > 0) && m.material?.opacity !== 0;
  const canCover = (m) => layerRank(m) > 0 && !HIDEABLE.test(m.name) && opaque(m);
  // One bone table by name: every piece's skeleton is the body's, but index by name to be sure.
  const boneIds = new Map(), boneOf = (m) => m.skeleton.bones.map((b) => { if (!boneIds.has(b.name)) boneIds.set(b.name, boneIds.size); return boneIds.get(b.name); });
  const weightsOf = (m) => {
    const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, map = boneOf(m), n = si.count;
    const I = new Int32Array(n * 4), Wt = new Float32Array(n * 4);
    for (let i = 0; i < n; i++) for (let k = 0; k < 4; k++) { I[i * 4 + k] = map[si.getComponent(i, k)] ?? 0; Wt[i * 4 + k] = sw.getComponent(i, k) / (sw.normalized ? 1 : 1); }
    return { I, Wt };
  };
  const info = new Map(skinned.map((m) => [m, { P: bindPositions(m), ...weightsOf(m) }]));
  const order = skinned.filter((m) => kindOf(m) && layerRank(m) < 4).sort((p, q) => layerRank(q) - layerRank(p));
  for (const mesh of order) {
    yield;
    const rank = layerRank(mesh), skin = mesh.material?.name === 'skin';
    const others = skinned.filter((c) => c !== mesh && canCover(c) && layerRank(c) > rank && c.geometry.index);
    if (!others.length) continue;
    const covers = others.map((c) => { const it = info.get(c); return { c, it, cast: triangleGrid(it.P, Int32Array.from(c.geometry.index.array), 0.03), near: pointGrid(it.P, 0.02) }; });
    yield;
    const W = weldMeshes([mesh]), N = graphNormals(W.P, W.tris, W.G);
    const from = new Int32Array(W.G).fill(-1), fromCover = new Array(W.G);
    for (let g = 0; g < W.G; g++) {
      if ((g & 1023) === 1023) yield;
      const x = W.P[g * 3], y = W.P[g * 3 + 1], z = W.P[g * 3 + 2], nx = N[g * 3], ny = N[g * 3 + 1], nz = N[g * 3 + 2];
      let best = Infinity, bc = null;
      for (const cv of covers) { const d = cv.cast(x + nx * LIFT_M, y + ny * LIFT_M, z + nz * LIFT_M, nx, ny, nz, BIND_REACH_M); if (d < best) { best = d; bc = cv; } }
      if (!bc) continue;
      const j = bc.near(x + nx * best, y + ny * best, z + nz * best);
      if (j >= 0) { from[g] = j; fromCover[g] = bc; }
    }
    // Past the edge: the nearest covered point (along the cloth) lends its source, faded by distance.
    const seeds = []; for (let g = 0; g < W.G; g++) if (from[g] >= 0) seeds.push(g);
    if (!seeds.length) continue;
    const D = skin ? null : distanceFrom(W, seeds);
    const src = new Int32Array(W.G).fill(-1);
    if (!skin) {
      // Carry each seed's source outward with the distance field (nearest seed by path).
      const heap = [], push = (g, d) => { heap.push([d, g]); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p][0] <= heap[i][0]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
      const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
      const dist = new Float64Array(W.G).fill(Infinity);
      for (const g of seeds) { dist[g] = 0; src[g] = g; push(g, 0); }
      while (heap.length) {
        const [d, g] = pop(); if (d > dist[g] || d > BAND_M) continue;
        for (const h of W.nb[g]) { const e = d + Math.hypot(W.P[g * 3] - W.P[h * 3], W.P[g * 3 + 1] - W.P[h * 3 + 1], W.P[g * 3 + 2] - W.P[h * 3 + 2]); if (e < dist[h]) { dist[h] = e; src[h] = src[g]; push(h, e); } }
      }
    } else for (const g of seeds) src[g] = g;
    const own = info.get(mesh), si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight, names = [...boneIds.keys()];
    const local = new Map(mesh.skeleton.bones.map((b, i) => [b.name, i]));
    const full = sw.normalized ? 255 : 1;   // Uint8 normalized: quantised to whole steps summing to 255
    let points = 0;
    for (let g = 0; g < W.G; g++) {
      const s = src[g]; if (s < 0) continue;
      const t = skin ? 1 : 1 - smoothstep(D[g] / BAND_M);
      if (t <= 0) continue;
      const cv = fromCover[s], j = from[s];
      points++;
      for (const [part, i] of W.members[g]) {
        const acc = new Map();
        for (let k = 0; k < 4; k++) { const w = own.Wt[i * 4 + k] * (1 - t); if (w > 0) acc.set(own.I[i * 4 + k], (acc.get(own.I[i * 4 + k]) ?? 0) + w); }
        for (let k = 0; k < 4; k++) { const w = cv.it.Wt[j * 4 + k] * t; if (w > 0) acc.set(cv.it.I[j * 4 + k], (acc.get(cv.it.I[j * 4 + k]) ?? 0) + w); }
        const top = [...acc].filter(([b]) => local.has(names[b])).sort((a, b) => b[1] - a[1]).slice(0, 4);
        const sum = top.reduce((a, [, w]) => a + w, 0) || 1;
        let q = top.map(([b, w]) => [b, w / sum]);
        if (full === 255) {
          const ints = q.map(([, w]) => Math.floor(w * 255)); let rest = 255 - ints.reduce((a, b) => a + b, 0);
          for (let k = 0; rest > 0; k = (k + 1) % ints.length, rest--) ints[k]++;
          q = q.map(([b], k) => [b, ints[k] / 255]);
        }
        for (let k = 0; k < 4; k++) { const e = q[k]; si.setComponent(i, k, e ? local.get(names[e[0]]) : 0); sw.setComponent(i, k, e ? e[1] : 0); }
        void part;
      }
    }
    if (!points) continue;
    si.needsUpdate = true; sw.needsUpdate = true;
    // What this mesh now lends to the ranks under it is its new weights.
    info.set(mesh, { P: own.P, ...weightsOf(mesh) });
    report.bound.push({ mesh: mesh.name, points });
  }
  root.userData.chicagoBind = report;
  return report;
}

/** Run a pass's steps to the end at once (tests, tools); humans.js runs them a slice at a time. */
export function runSteps(steps) { for (;;) { const n = steps.next(); if (n.done) return n.value; } }
export const drapeGarments = (root) => runSteps(drapeGarmentsSteps(root));
export const settleOnBody = (root) => runSteps(settleOnBodySteps(root));
export const bindLayers = (root) => runSteps(bindLayersSteps(root));
export const cullHidden = (root) => runSteps(cullHiddenSteps(root));
/** Shared helpers for the passes that build on the drape (human-fair.js). */
export const kit = Object.freeze({ weldMeshes, pointGrid, triangleGrid, graphNormals, bodyFieldSteps, writeBack, distanceFrom, loopsOf, bindPositions, kindOf, smoothCeiling, openingOf });
