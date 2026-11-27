// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553 round 5, trims close to (the owner, 2026-11-25: the maid's "collar is all jagged",
 * John's "suit lapels are awful", the coachman's "collar does not look natural").
 *
 * Collars, lapels, revers, stocks, straps, bibs and frills were exported as coarse strips, a
 * few hundred triangles each, so close to they show flat facets and their outlines step like
 * saw teeth. At the nearest level only, each such trim is refined the way a game's close-up
 * mesh is: its open edges are relaxed along their own line, in the cloth's plane (the outline
 * runs clean, the strip does not lift), then it is subdivided once (Loop: every triangle into
 * four, new points placed on the smooth surface through the old ones, edges by the boundary
 * rule) and given smooth normals. UVs and skin weights are interpolated; the mesh, material and
 * draw call stay the same, and the far levels keep their own coarse strips (they are seen from
 * further than the facets read). Fit, not measurement (liberty L-drape-3553).
 */
import * as THREE from 'three';
import { kit, LAMBDA, MU } from './human-drape.js';

const { weldMeshes, bindPositions, graphNormals, loopsOf, triangleGrid, pointGrid, bodyFieldSteps, distanceFrom, writeBack } = kit;
import { layerRank } from './human-drape.js';

/** Ring collars and bands (two open edges, round the neck) rebuilt clean at every level: COLLAR_K
 * points round and COLLAR_ROWS across, by level. */
export const COLLAR = /(white_collar|standing_collar|cook_neckband|white_stock)(_lod\d+)?$/;
export const COLLAR_K = [96, 64, 32, 20], COLLAR_ROWS = [6, 4, 2, 1];
/** Low-pass of the two edges round the neck (in samples of COLLAR_K[0], Gaussian sigma). */
export const COLLAR_SMOOTH = { inner: 1.5, outer: 4 };
/** A rebuilt collar keeps COLLAR_GAP_M off whatever it lies on. */
export const COLLAR_GAP_M = 0.0018;

/** Rebuild one ring collar from its two edges: each edge read round the neck as height and
 * radius by angle, smoothed, and a clean band of rows laid between them, never nearer what it
 * lies on than COLLAR_GAP_M. Weights from the nearest old point; UVs at the old density. */
function rebuildCollar(mesh, casts, B, lod) {
  const geo = mesh.geometry, W = weldMeshes([mesh]), loops = loopsOf(W);
  if (loops.length !== 2) return null;
  const P = W.P, radius = (l, cx, cz) => l.reduce((s, g) => s + Math.hypot(P[g * 3] - cx, P[g * 3 + 2] - cz), 0) / l.length;
  let cx = 0, cz = 0; for (const g of loops[0].concat(loops[1])) { cx += P[g * 3]; cz += P[g * 3 + 2]; }
  cx /= loops[0].length + loops[1].length; cz /= loops[0].length + loops[1].length;
  const [inner, outer] = radius(loops[0], cx, cz) + Math.abs(meanY(loops[0], P) - 1e3) * 0 <= radius(loops[1], cx, cz) ? [loops[0], loops[1]] : [loops[1], loops[0]];
  const K = COLLAR_K[Math.min(lod, 3)], R = COLLAR_ROWS[Math.min(lod, 3)];
  // The old strip's profile, read across it: each old point's place from the neck edge (0) to
  // the outer edge (1), then each new point the weighted mean of the old ones near its angle
  // and place, so the stand and the fall keep their shape while the steps are taken out.
  const D0 = distanceFrom(W, inner), D1 = distanceFrom(W, outer);
  const G = W.G, th0 = new Float64Array(G), f0 = new Float64Array(G);
  for (let g = 0; g < G; g++) { th0[g] = Math.atan2(P[g * 3] - cx, P[g * 3 + 2] - cz); f0[g] = D0[g] / ((D0[g] + D1[g]) || 1); }
  const cols = K + 1, n = (R + 1) * cols, Pb = new Float64Array(n * 3);
  const sTh = (2 * Math.PI / K) * 1.5, sF = 0.6 / Math.max(2, R);
  const Y = new Float64Array((R + 1) * K), RR = new Float64Array((R + 1) * K);
  for (let j = 0; j <= R; j++) {
    const t = j / R;
    for (let k = 0; k < K; k++) {
      const th = -Math.PI + (k + 0.5) * 2 * Math.PI / K; let sy = 0, sr = 0, sw = 0;
      for (let g = 0; g < G; g++) {
        let dt = Math.abs(th0[g] - th); if (dt > Math.PI) dt = 2 * Math.PI - dt; if (dt > sTh * 3) continue;
        const w = Math.exp(-((dt / sTh) ** 2) - (((f0[g] - t) / sF) ** 2)); if (w < 1e-6) continue;
        sy += w * P[g * 3 + 1]; sr += w * Math.hypot(P[g * 3] - cx, P[g * 3 + 2] - cz); sw += w;
      }
      Y[j * K + k] = sw ? sy / sw : NaN; RR[j * K + k] = sw ? sr / sw : NaN;
    }
  }
  // The two edges themselves are read straight off their loops (by angle), so the collar
  // reaches as high on the neck and as far out as it was cut.
  for (const [j, loop] of [[0, inner], [R, outer]]) {
    const pts = loop.map((g) => ({ th: th0[g], y: P[g * 3 + 1], r: Math.hypot(P[g * 3] - cx, P[g * 3 + 2] - cz) })).sort((a, b) => a.th - b.th);
    for (let k = 0; k < K; k++) {
      const th = -Math.PI + (k + 0.5) * 2 * Math.PI / K;
      let i = pts.findIndex((p) => p.th >= th); if (i < 0) i = 0;
      const a = pts[(i - 1 + pts.length) % pts.length], b = pts[i];
      let span = b.th - a.th; if (span <= 0) span += 2 * Math.PI;
      let t = th - a.th; if (t < 0) t += 2 * Math.PI; t = Math.min(1, t / span);
      Y[j * K + k] = a.y + (b.y - a.y) * t; RR[j * K + k] = a.r + (b.r - a.r) * t;
    }
  }
  // Round the ring: the neck edge a little, the outer edge more (its saw teeth were the worst).
  for (let j = 0; j <= R; j++) {
    const sigma = (COLLAR_SMOOTH.inner + (COLLAR_SMOOTH.outer - COLLAR_SMOOTH.inner) * (j / R)) * K / COLLAR_K[0], w = Math.ceil(sigma * 3);
    for (const F of [Y, RR]) {
      const row = F.slice(j * K, j * K + K), out = new Float64Array(K);
      for (let k = 0; k < K; k++) { let s2 = 0, sw = 0; for (let d = -w; d <= w; d++) { const v = row[(k + d + K * 4) % K]; if (!Number.isFinite(v)) continue; const q = Math.exp(-(d * d) / (2 * sigma * sigma + 1e-9)); s2 += q * v; sw += q; } out[k] = sw ? s2 / sw : row[k]; }
      F.set(out, j * K);
    }
  }
  for (let j = 0; j <= R; j++) for (let c = 0; c < cols; c++) {
    const k = c % K, th = -Math.PI + (k + 0.5) * 2 * Math.PI / K, o = (j * cols + c) * 3;
    Pb[o] = cx + Math.sin(th) * RR[j * K + k]; Pb[o + 1] = Y[j * K + k]; Pb[o + 2] = cz + Math.cos(th) * RR[j * K + k];
  }
  // Laid clear of what it lies on, then evened round the ring.
  const lift = new Float64Array(n), dirs = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, B.near(Pb[i * 3], Pb[i * 3 + 1], Pb[i * 3 + 2])) * 3, nx = B.N[a], ny = B.N[a + 1], nz = B.N[a + 2];
    dirs[i * 3] = nx; dirs[i * 3 + 1] = ny; dirs[i * 3 + 2] = nz;
    let best = Infinity; for (const c of casts) best = Math.min(best, c(Pb[i * 3] + nx * 0.03, Pb[i * 3 + 1] + ny * 0.03, Pb[i * 3 + 2] + nz * 0.03, -nx, -ny, -nz, 0.06));
    if (Number.isFinite(best)) lift[i] = Math.min(0.006, Math.max(0, COLLAR_GAP_M - (0.03 - best)));
  }
  for (let it = 0; it < 4; it++) { const T = Float64Array.from(lift); for (let j = 0; j <= R; j++) for (let c = 0; c < cols; c++) { const k = c % K, i = j * cols + c, l = j * cols + (k + K - 1) % K, rr = j * cols + (k + 1) % K; T[i] = Math.max(lift[i], (lift[l] + lift[i] * 2 + lift[rr]) / 4); } lift.set(T); }
  for (let i = 0; i < n; i++) for (let d = 0; d < 3; d++) Pb[i * 3 + d] += lift[i] * dirs[i * 3 + d];
  for (let j = 0; j <= R; j++) for (let d = 0; d < 3; d++) { Pb[(j * cols + K) * 3 + d] = Pb[(j * cols) * 3 + d]; }
  // Triangles, facing away from the body.
  const tris = [];
  for (let j = 0; j < R; j++) for (let c = 0; c < K; c++) { const a = j * cols + c, b = a + 1, d = a + cols, e = d + 1; tris.push(a, d, b, b, d, e); }
  { const a = tris[0] * 3, b = tris[1] * 3, c = tris[2] * 3;
    const ux = Pb[b] - Pb[a], uy = Pb[b + 1] - Pb[a + 1], uz = Pb[b + 2] - Pb[a + 2], vx = Pb[c] - Pb[a], vy = Pb[c + 1] - Pb[a + 1], vz = Pb[c + 2] - Pb[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (nx * dirs[0] + ny * dirs[1] + nz * dirs[2] < 0) for (let t = 0; t < tris.length; t += 3) { const q = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = q; } }
  // UVs at the old density; weights from the nearest old point.
  const uvA = geo.attributes.uv; let du = 0, dp = 0;
  if (uvA) { const idx = geo.index.array; for (let t = 0; t < idx.length; t += 3) { const i = idx[t], j2 = idx[t + 1]; du += Math.hypot(uvA.getX(i) - uvA.getX(j2), uvA.getY(i) - uvA.getY(j2)); dp += Math.hypot(W.P[W.parts[0].group[i] * 3] - W.P[W.parts[0].group[j2] * 3], W.P[W.parts[0].group[i] * 3 + 1] - W.P[W.parts[0].group[j2] * 3 + 1], W.P[W.parts[0].group[i] * 3 + 2] - W.P[W.parts[0].group[j2] * 3 + 2]); } }
  const dens = dp > 0 ? du / dp : 1, uv = new Float32Array(n * 2);
  for (let j = 0; j <= R; j++) { let arc = 0; for (let c = 0; c < cols; c++) { const i = j * cols + c; if (c) { const q = i - 1; arc += Math.hypot(Pb[i * 3] - Pb[q * 3], Pb[i * 3 + 1] - Pb[q * 3 + 1], Pb[i * 3 + 2] - Pb[q * 3 + 2]); } uv[i * 2] = arc * dens; } }
  for (let c = 0; c < cols; c++) { let acc = 0; for (let j = 0; j <= R; j++) { const i = j * cols + c; if (j) { const q = i - cols; acc += Math.hypot(Pb[i * 3] - Pb[q * 3], Pb[i * 3 + 1] - Pb[q * 3 + 1], Pb[i * 3 + 2] - Pb[q * 3 + 2]); } uv[i * 2 + 1] = acc * dens; } }
  const oldBind = bindPositions(mesh), nearOld = pointGrid(oldBind, 0.02), si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight;
  const SI = new (si.array.constructor)(n * 4), SWt = new (sw.array.constructor)(n * 4);
  for (let i = 0; i < n; i++) { const o = Math.max(0, nearOld(Pb[i * 3], Pb[i * 3 + 1], Pb[i * 3 + 2], 8)); for (let k = 0; k < 4; k++) { SI[i * 4 + k] = si.getComponent(o, k); SWt[i * 4 + k] = sw.array[o * 4 + k] ?? 0; } }
  const Binv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3(), pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { v.set(Pb[i * 3], Pb[i * 3 + 1], Pb[i * 3 + 2]).applyMatrix4(Binv); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z; }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.setAttribute('skinIndex', new THREE.BufferAttribute(SI, 4));
  out.setAttribute('skinWeight', new THREE.BufferAttribute(SWt, 4, sw.normalized));
  out.setIndex(new THREE.BufferAttribute(Uint16Array.from(tris), 1));
  out.name = geo.name; out.userData = { ...geo.userData, chicagoRebuilt: { from: geo.index.count / 3, to: tris.length / 3 } };
  mesh.geometry = out;
  const W2 = weldMeshes([mesh]), N2 = graphNormals(W2.P, W2.tris, W2.G), nBack = new THREE.Matrix3().getNormalMatrix(Binv), nrm = out.attributes.normal;
  for (let i = 0; i < n; i++) { const g = W2.parts[0].group[i]; v.set(N2[g * 3], N2[g * 3 + 1], N2[g * 3 + 2]).applyMatrix3(nBack).normalize(); nrm.setXYZ(i, v.x, v.y, v.z); }
  out.computeBoundingBox(); out.computeBoundingSphere(); geo.dispose();
  return { from: geo.index.count / 3, to: tris.length / 3 };
}
const meanY = (l, P) => l.reduce((s, g) => s + P[g * 3 + 1], 0) / l.length;


/** Trims refined, by piece name, at the levels in REFINE_LODS. */
export const REFINE = /(lapels|revers|collar|stock|neckcloth|neckband|strap|frills?|four_in_hand_tie|waistcoat[a-z_0-9]*?)(_lod\d+)?$/;
export const REFINE_LODS = /_lod0$/;
/** Edge relaxing before subdividing (Taubin pairs along the outline, in the cloth's plane). */
export const OUTLINE_ITERS = 10;

/** Relax the open edges of a welded graph along their line, moving only in the surface's plane. */
function fairOutline(W, iters, only = null) {
  const { P, G, edgeNb } = W;
  for (let it = 0; it < iters * 2; it++) {
    const N = graphNormals(P, W.tris, G), w = it % 2 ? MU : LAMBDA, Q = Float64Array.from(P);
    for (let g = 0; g < G; g++) {
      const l = edgeNb[g]; if (l.length !== 2 || (only && !only[g])) continue;
      let cx = (P[l[0] * 3] + P[l[1] * 3]) / 2 - P[g * 3], cy = (P[l[0] * 3 + 1] + P[l[1] * 3 + 1]) / 2 - P[g * 3 + 1], cz = (P[l[0] * 3 + 2] + P[l[1] * 3 + 2]) / 2 - P[g * 3 + 2];
      const o = cx * N[g * 3] + cy * N[g * 3 + 1] + cz * N[g * 3 + 2]; cx -= o * N[g * 3]; cy -= o * N[g * 3 + 1]; cz -= o * N[g * 3 + 2];
      Q[g * 3] += w * cx; Q[g * 3 + 1] += w * cy; Q[g * 3 + 2] += w * cz;
    }
    P.set(Q);
  }
}

/** Loop-subdivide one skinned mesh once, positions on its welded surface (bind space). */
function subdivide(mesh) {
  const geo = mesh.geometry, W = weldMeshes([mesh]), part = W.parts[0];
  fairOutline(W, OUTLINE_ITERS);
  const { P, G, nb, edgeNb } = W;
  // Welded vertex rule.
  const VP = new Float64Array(G * 3);
  for (let g = 0; g < G; g++) {
    const e = edgeNb[g];
    if (e.length === 2) { for (let d = 0; d < 3; d++) VP[g * 3 + d] = 0.75 * P[g * 3 + d] + 0.125 * (P[e[0] * 3 + d] + P[e[1] * 3 + d]); continue; }
    if (e.length || !nb[g].length) { for (let d = 0; d < 3; d++) VP[g * 3 + d] = P[g * 3 + d]; continue; }
    const n = nb[g].length, beta = n === 3 ? 3 / 16 : 3 / (8 * n);
    for (let d = 0; d < 3; d++) { let s = 0; for (const h of nb[g]) s += P[h * 3 + d]; VP[g * 3 + d] = (1 - n * beta) * P[g * 3 + d] + beta * s; }
  }
  // Welded edge rule: the two opposite points of an inner edge pull it onto the surface.
  const opp = new Map(), key = (a, b) => (a < b ? a * G + b : b * G + a);
  for (let t = 0; t < W.tris.length; t += 3) for (let k = 0; k < 3; k++) {
    const a = W.tris[t + k], b = W.tris[t + (k + 1) % 3], c = W.tris[t + (k + 2) % 3], kk = key(a, b);
    (opp.get(kk) ?? opp.set(kk, []).get(kk)).push(c);
  }
  const edgePoint = (a, b, out, o) => {
    const l = opp.get(key(a, b));
    if (l && l.length === 2) for (let d = 0; d < 3; d++) out[o + d] = 0.375 * (P[a * 3 + d] + P[b * 3 + d]) + 0.125 * (P[l[0] * 3 + d] + P[l[1] * 3 + d]);
    else for (let d = 0; d < 3; d++) out[o + d] = 0.5 * (P[a * 3 + d] + P[b * 3 + d]);
  };
  // New vertices: the old ones, then one per original edge.
  const idx = geo.index.array, n0 = geo.attributes.position.count, edgeOf = new Map(), pairs = [];
  const mid = (i, j) => { const k = i < j ? i * n0 + j : j * n0 + i; let v = edgeOf.get(k); if (v === undefined) { v = n0 + pairs.length / 2; edgeOf.set(k, v); pairs.push(i, j); } return v; };
  const tris = [];
  for (let t = 0; t < idx.length; t += 3) {
    const a = idx[t], b = idx[t + 1], c = idx[t + 2], ab = mid(a, b), bc = mid(b, c), ca = mid(c, a);
    tris.push(a, ab, ca, ab, b, bc, ca, bc, c, ab, bc, ca);
  }
  const n1 = n0 + pairs.length / 2, Pb = new Float64Array(n1 * 3);
  for (let i = 0; i < n0; i++) { const g = part.group[i]; Pb[i * 3] = VP[g * 3]; Pb[i * 3 + 1] = VP[g * 3 + 1]; Pb[i * 3 + 2] = VP[g * 3 + 2]; }
  for (let e = 0; e < pairs.length / 2; e++) edgePoint(part.group[pairs[e * 2]], part.group[pairs[e * 2 + 1]], Pb, (n0 + e) * 3);
  // Attributes: positions (bind -> mesh space), uv averaged, skin weights merged (top four).
  const Binv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
  const pos = new Float32Array(n1 * 3);
  for (let i = 0; i < n1; i++) { v.set(Pb[i * 3], Pb[i * 3 + 1], Pb[i * 3 + 2]).applyMatrix4(Binv); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z; }
  const uvA = geo.attributes.uv, uv = uvA ? new Float32Array(n1 * 2) : null;
  if (uv) {
    for (let i = 0; i < n0; i++) { uv[i * 2] = uvA.getX(i); uv[i * 2 + 1] = uvA.getY(i); }
    for (let e = 0; e < pairs.length / 2; e++) { const i = pairs[e * 2], j = pairs[e * 2 + 1]; uv[(n0 + e) * 2] = (uv[i * 2] + uv[j * 2]) / 2; uv[(n0 + e) * 2 + 1] = (uv[i * 2 + 1] + uv[j * 2 + 1]) / 2; }
  }
  const si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight;
  const SI = new Uint16Array(n1 * 4), SW = new Float32Array(n1 * 4);
  for (let i = 0; i < n0; i++) for (let k = 0; k < 4; k++) { SI[i * 4 + k] = si.getComponent(i, k); SW[i * 4 + k] = sw.getComponent(i, k); }
  for (let e = 0; e < pairs.length / 2; e++) {
    const acc = new Map();
    for (const i of [pairs[e * 2], pairs[e * 2 + 1]]) for (let k = 0; k < 4; k++) { const w = SW[i * 4 + k]; if (w > 0) acc.set(SI[i * 4 + k], (acc.get(SI[i * 4 + k]) ?? 0) + w); }
    const top = [...acc].sort((p, q) => q[1] - p[1]).slice(0, 4), sum = top.reduce((s, x) => s + x[1], 0) || 1, o = (n0 + e) * 4;
    top.forEach(([b, w], k) => { SI[o + k] = b; SW[o + k] = w / sum; });
  }
  // Quantised to the original weight type, summing to its full scale.
  const WArr = sw.array.constructor, full = sw.normalized && WArr === Uint8Array ? 255 : sw.normalized && WArr === Uint16Array ? 65535 : 0;
  let skinWeight;
  if (full) {
    const q = new WArr(n1 * 4);
    for (let i = 0; i < n1; i++) {
      let s = 0; for (let k = 0; k < 4; k++) s += SW[i * 4 + k];
      let left = full, best = 0;
      for (let k = 0; k < 4; k++) { q[i * 4 + k] = Math.round((SW[i * 4 + k] / (s || 1)) * full); left -= q[i * 4 + k]; if (q[i * 4 + k] > q[i * 4 + best]) best = k; }
      q[i * 4 + best] += left;
    }
    skinWeight = new THREE.BufferAttribute(q, 4, true);
  } else skinWeight = new THREE.BufferAttribute(SW, 4);
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  if (uv) out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.setAttribute('skinIndex', new THREE.BufferAttribute(si.array.constructor === Uint8Array && n1 < 1e9 ? Uint8Array.from(SI) : SI, 4));
  out.setAttribute('skinWeight', skinWeight);
  out.setIndex(new THREE.BufferAttribute(n1 > 65535 ? Uint32Array.from(tris) : Uint16Array.from(tris), 1));
  out.userData = { ...geo.userData, chicagoRefined: { from: idx.length / 3, to: tris.length / 3 } };
  out.name = geo.name;
  // Smooth normals over the welded refined surface.
  out.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(n1 * 3), 3));
  mesh.geometry = out;
  const W2 = weldMeshes([mesh]), N2 = graphNormals(W2.P, W2.tris, W2.G), nBack = new THREE.Matrix3().getNormalMatrix(Binv), nrm = out.attributes.normal;
  for (let i = 0; i < n1; i++) { const g = W2.parts[0].group[i]; v.set(N2[g * 3], N2[g * 3 + 1], N2[g * 3 + 2]).applyMatrix3(nBack).normalize(); nrm.setXYZ(i, v.x, v.y, v.z); }
  out.computeBoundingBox(); out.computeBoundingSphere();
  geo.dispose();
  return { from: idx.length / 3, to: tris.length / 3 };
}


/** A frock coat's collar round the back of the neck, stand and fall, from one lapel's top to
 * the other's (the coat was cut open at the back neck and the lapels' tops stood free beside
 * the neck, read as a lump at the shoulder). Built in the lapels' own mesh. */
export const BACK_COLLAR = Object.freeze({ lapels: /frock_coat_lapels(_lod\d+)?$/, body: /frock_coat_body(_lod\d+)?$/, shirt: /shirt_standing_collar(_lod\d+)?$/,
  height: 0.028, fall: 0.022, gap: 0.004, span: 100, under: 4, taper: 25, K: [48, 32, 16, 10] });

/** Append points and triangles to a skinned mesh's geometry (attributes made plain). */
/** `laid`: the points added lie over the cloth outside this mesh's own layer (a lapel's silk
 * facing and the buttons, in the tie's mesh, lie on the coat): recorded as
 * geometry.userData.chicagoLaidFrom, the first of them. */
function appendGeometry(mesh, add, laid = false) {
  const geo = mesh.geometry, n0 = geo.attributes.position.count, n1 = n0 + add.P.length / 3;
  const out = new THREE.BufferGeometry(), v = new THREE.Vector3();
  const pos = new Float32Array(n1 * 3), nrm = new Float32Array(n1 * 3), uv = new Float32Array(n1 * 2);
  const si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight, SI = new (si.array.constructor)(n1 * 4), SW = new (sw.array.constructor)(n1 * 4);
  for (let i = 0; i < n0; i++) {
    v.fromBufferAttribute(geo.attributes.position, i); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
    if (geo.attributes.normal) { v.fromBufferAttribute(geo.attributes.normal, i); nrm[i * 3] = v.x; nrm[i * 3 + 1] = v.y; nrm[i * 3 + 2] = v.z; }
    if (geo.attributes.uv) { uv[i * 2] = geo.attributes.uv.getX(i); uv[i * 2 + 1] = geo.attributes.uv.getY(i); }
    for (let k = 0; k < 4; k++) { SI[i * 4 + k] = si.getComponent(i, k); SW[i * 4 + k] = sw.array[sw.isInterleavedBufferAttribute ? 0 : i * 4 + k]; }
  }
  if (sw.isInterleavedBufferAttribute) for (let i = 0; i < n0; i++) for (let k = 0; k < 4; k++) SW[i * 4 + k] = Math.round(sw.getComponent(i, k) * (sw.normalized ? 255 : 1));
  const Binv = mesh.bindMatrix.clone().invert(), nBack = new THREE.Matrix3().getNormalMatrix(Binv);
  for (let j = 0; j < add.P.length / 3; j++) {
    const i = n0 + j;
    v.set(add.P[j * 3], add.P[j * 3 + 1], add.P[j * 3 + 2]).applyMatrix4(Binv); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
    v.set(add.N[j * 3], add.N[j * 3 + 1], add.N[j * 3 + 2]).applyMatrix3(nBack).normalize(); nrm[i * 3] = v.x; nrm[i * 3 + 1] = v.y; nrm[i * 3 + 2] = v.z;
    uv[i * 2] = add.UV[j * 2]; uv[i * 2 + 1] = add.UV[j * 2 + 1];
    for (let k = 0; k < 4; k++) { SI[i * 4 + k] = add.SI[j * 4 + k]; SW[i * 4 + k] = add.SW[j * 4 + k]; }
  }
  const idx = Array.from(geo.index.array); for (const t of add.index) idx.push(t + n0);
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nrm, 3)); out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.setAttribute('skinIndex', new THREE.BufferAttribute(SI, 4)); out.setAttribute('skinWeight', new THREE.BufferAttribute(SW, 4, sw.normalized));
  out.setIndex(new THREE.BufferAttribute(n1 > 65535 ? Uint32Array.from(idx) : Uint16Array.from(idx), 1));
  out.name = geo.name; out.userData = { ...geo.userData };
  if (laid) out.userData.chicagoLaidFrom = Math.min(geo.userData?.chicagoLaidFrom ?? Infinity, n0);
  out.computeBoundingBox(); out.computeBoundingSphere();
  mesh.geometry = out; geo.dispose();
}

function buildBackCollar(lapels, body, shirt, lod, tops = null) {
  const C = BACK_COLLAR, Wb = weldMeshes([body]), Ws = weldMeshes([shirt]);
  // The coat's back neckline (its top, by angle) and the shirt collar's radius over it; round to
  // the lapels' gorges when they are known (a little past, under them).
  const K = C.K[Math.min(lod, 3)], taper = C.taper * Math.PI / 180;
  const span = tops?.length ? Math.max(...tops.map((p) => Math.PI - Math.atan2(Math.abs(p[0]), p[2]))) + C.under * Math.PI / 180 : C.span * Math.PI / 180;
  const sector = (W, th, w) => { let best = null; for (let g = 0; g < W.G; g++) { let d = Math.abs(Math.atan2(W.P[g * 3], W.P[g * 3 + 2]) - th); if (d > Math.PI) d = 2 * Math.PI - d; if (d > w) continue; if (!best || W.P[g * 3 + 1] > W.P[best * 3 + 1]) best = g; } return best; };
  const cols = K + 1, rows = 5, P = [], N = [], UV = [], SI = [], SW = [], index = [];
  const near = pointGrid(Wb.P, 0.02), part = Wb.parts[0], si = body.geometry.attributes.skinIndex, sw = body.geometry.attributes.skinWeight;
  const memberOf = new Int32Array(Wb.G); for (let i = 0; i < part.group.length; i++) memberOf[part.group[i]] = i;
  const ring = [];
  for (let c = 0; c < cols; c++) {
    const th = Math.PI - span + (2 * span) * (c / K), thw = ((th + Math.PI) % (2 * Math.PI)) - Math.PI;   // through the back (pi)
    const gb = sector(Wb, thw, 0.12), gs = sector(Ws, thw, 0.15);
    if (gb == null || gs == null) return null;
    const yb = Wb.P[gb * 3 + 1], rb = Math.hypot(Wb.P[gb * 3], Wb.P[gb * 3 + 2]), rs = Math.hypot(Ws.P[gs * 3], Ws.P[gs * 3 + 2]);
    const edge = Math.min(th - (Math.PI - span), (Math.PI + span) - th), k = Math.min(1, edge / taper), e = k * k * (3 - 2 * k);
    const h = C.height * (0.35 + 0.65 * e), f = C.fall * (0.35 + 0.65 * e);
    const rIn = Math.max(rs + C.gap, rb - 0.006);
    // Profile: the stand from the neckline up the shirt collar, then the fall turned back down over it.
    const prof = [[yb - 0.006, rIn], [yb + h * 0.5, rIn + 0.001], [yb + h, rIn + 0.003], [yb + h - 0.004, rIn + 0.008], [yb + h - f, rb + 0.006]];
    ring.push({ th: thw, prof, gb });
  }
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const { th, prof, gb } = ring[c], [y, rad] = prof[r];
    P.push(Math.sin(th) * rad, y, Math.cos(th) * rad);
    const o = memberOf[gb]; for (let k = 0; k < 4; k++) { SI.push(si.getComponent(o, k)); SW.push(sw.normalized && sw.array.constructor === Uint8Array ? Math.round(sw.getComponent(o, k) * 255) : sw.getComponent(o, k)); }
    UV.push(c / K * 0.5, r / (rows - 1) * 0.05);
  }
  // Normals: outward, from the ring's own surface.
  const Pa = Float64Array.from(P), n = Pa.length / 3, Nn = new Float64Array(n * 3);
  for (let r = 0; r < rows - 1; r++) for (let c = 0; c < K; c++) { const a = r * cols + c, b = a + 1, d = a + cols, e2 = d + 1; index.push(a, b, d, b, e2, d); }
  for (let t = 0; t < index.length; t += 3) { const a = index[t] * 3, b = index[t + 1] * 3, c = index[t + 2] * 3; const ux = Pa[b] - Pa[a], uy = Pa[b + 1] - Pa[a + 1], uz = Pa[b + 2] - Pa[a + 2], vx = Pa[c] - Pa[a], vy = Pa[c + 1] - Pa[a + 1], vz = Pa[c + 2] - Pa[a + 2]; const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; for (const q of [a, b, c]) { Nn[q] += nx; Nn[q + 1] += ny; Nn[q + 2] += nz; } }
  // Face away from the neck (the fall's outside is what shows).
  let out = 0; for (let i = 0; i < n; i++) out += Nn[i * 3] * Pa[i * 3] + Nn[i * 3 + 2] * Pa[i * 3 + 2];
  if (out < 0) { for (let t = 0; t < index.length; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; } for (let i = 0; i < Nn.length; i++) Nn[i] = -Nn[i]; }
  for (let i = 0; i < n; i++) { const l = Math.hypot(Nn[i * 3], Nn[i * 3 + 1], Nn[i * 3 + 2]) || 1; Nn[i * 3] /= l; Nn[i * 3 + 1] /= l; Nn[i * 3 + 2] /= l; }
  void near;
  appendGeometry(lapels, { P: Pa, N: Nn, UV, SI, SW, index });
  return { points: n, triangles: index.length / 3 };
}

/** Seams pressed into a coat: centre back, side backs and shoulders, each a shallow
 * groove (two narrow faces turned toward each other) laid just over the cloth in the coat's
 * own mesh and colour, so the light breaks along it as along a real seam. Found by rays from
 * the bind skeleton (shoulder joints, neck) onto the coat; a seam stops where the coat ends.
 * Near level only. Armholes are found from the coat's own skin, not by rays (the sleeve head is
 * too uneven drawn for a ray from the arm to find one clean line round it). */
export const SEAMED = /(frock_coat_body|coat_body|tailcoat_body)_lod0$/;
export const SEAM = Object.freeze({ half: 0.0016, lift: 0.0013, sink: 0.0004, tilt: 0.75, step: 0.008, gap: 0.03 });
/** Front buttons of a frock coat, silk-covered like its facings: down the closing from the
 * lapels' break to the waist seam. */
export const FRONT_BUTTONS = Object.freeze({ coat: /frock_coat_body(_lod\d+)?$/, lapels: /frock_coat_lapels(_lod\d+)?$/, silk: /four_in_hand_tie(_lod\d+)?$/,
  count: 3, radius: 0.0075, dome: 0.003, lift: 0.0009, segments: [16, 12], rings: [3, 2] });

/** Bind positions of named bones (`upperarm_l`, `neck_01`, ...) from a skinned mesh's skeleton. */
function bindJoints(mesh) {
  const out = {}, M = new THREE.Matrix4(), v = new THREE.Vector3();
  (mesh.skeleton?.bones ?? []).forEach((b, i) => { M.copy(mesh.skeleton.boneInverses[i]).invert(); v.setFromMatrixPosition(M); out[b.name] = [v.x, v.y, v.z]; });
  return out;
}
/** A surface sampler over one welded mesh: ray hits, nearest point's normal, skin row and uv. */
function surfaceOf(mesh) {
  const W = weldMeshes([mesh]), cast = triangleGrid(W.P, W.tris, 0.03), near = pointGrid(W.P, 0.02), N = graphNormals(W.P, W.tris, W.G);
  const part = W.parts[0], memberOf = new Int32Array(W.G);
  for (let i = 0; i < part.group.length; i++) memberOf[part.group[i]] = i;
  const geo = mesh.geometry, si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight, uv = geo.attributes.uv;
  const toByte = sw.normalized && sw.array.constructor === Uint8Array;
  let tri = null;
  return {
    W,
    hit(o, d, far = 0.5) { const h = cast(o[0], o[1], o[2], d[0], d[1], d[2], far); return Number.isFinite(h) ? [o[0] + d[0] * h, o[1] + d[1] * h, o[2] + d[2] * h] : null; },
    at(p) { const g = near(p[0], p[1], p[2]); return g < 0 ? null : { g, n: [N[g * 3], N[g * 3 + 1], N[g * 3 + 2]], v: memberOf[g] }; },
    skin(v, SI, SW) { for (let k = 0; k < 4; k++) { SI.push(si.getComponent(v, k)); SW.push(toByte ? Math.round(sw.getComponent(v, k) * 255) : sw.getComponent(v, k)); } },
    /** The skin under a point on the surface, blended over the triangle it lies on (a coarse
     * level's nearest point can be a hand's breadth off and bend another way). */
    skinAt(p, SI, SW) {
      const g = near(p[0], p[1], p[2]); if (g < 0) { SI.push(0, 0, 0, 0); SW.push(toByte ? 255 : 1, 0, 0, 0); return; }
      if (!tri) { tri = Array.from({ length: W.G }, () => []); for (let t = 0; t < W.tris.length; t += 3) for (let k = 0; k < 3; k++) tri[W.tris[t + k]].push(t); }
      let best = null, bestOut = Infinity;
      for (const t of tri[g]) {
        const [a, b, c] = [W.tris[t], W.tris[t + 1], W.tris[t + 2]].map((q) => [W.P[q * 3], W.P[q * 3 + 1], W.P[q * 3 + 2]]);
        const v0 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v1 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]], v2 = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
        const d00 = v0[0] * v0[0] + v0[1] * v0[1] + v0[2] * v0[2], d01 = v0[0] * v1[0] + v0[1] * v1[1] + v0[2] * v1[2], d11 = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2];
        const d20 = v2[0] * v0[0] + v2[1] * v0[1] + v2[2] * v0[2], d21 = v2[0] * v1[0] + v2[1] * v1[1] + v2[2] * v1[2], den = d00 * d11 - d01 * d01 || 1e-12;
        const y = (d11 * d20 - d01 * d21) / den, z = (d00 * d21 - d01 * d20) / den, x = 1 - y - z, out = -Math.min(0, x, y, z);
        if (out < bestOut) { bestOut = out; best = [[W.tris[t], x], [W.tris[t + 1], y], [W.tris[t + 2], z]]; }
      }
      if (!best) { this.skin(memberOf[g], SI, SW); return; }
      const acc = new Map();
      for (const [q, w0] of best) { const w = Math.min(1, Math.max(0, w0)), v = memberOf[q]; for (let k = 0; k < 4; k++) { const b = si.getComponent(v, k), x = sw.getComponent(v, k); if (x > 0) acc.set(b, (acc.get(b) ?? 0) + w * x); } }
      const top = [...acc.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4), sum = top.reduce((s2, e) => s2 + e[1], 0) || 1;
      if (toByte) { const q = top.map((e) => Math.round(e[1] / sum * 255)); q[0] += 255 - q.reduce((s2, v) => s2 + v, 0); for (let k = 0; k < 4; k++) { SI.push(top[k]?.[0] ?? 0); SW.push(top[k] ? q[k] : 0); } }
      else for (let k = 0; k < 4; k++) { SI.push(top[k]?.[0] ?? 0); SW.push(top[k] ? top[k][1] / sum : 0); }
    },
    uv(v, UV) { UV.push(uv ? uv.getX(v) : 0, uv ? uv.getY(v) : 0); },
  };
}
const unit = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

/** The seam paths of a coat as rays: each path is a list of [origin, direction]. */
function seamRays(J, S) {
  const ul = J.upperarm_l, ur = J.upperarm_r, nk = J.neck_01, pv = J.pelvis;
  if (!ul || !ur || !nk || !pv) return [];
  const paths = [], dy = 0.004, bottom = pv[1] + 0.05, armY = ul[1], zc = (ul[2] + ur[2]) / 2;
  // Centre back, waist to neck.
  { const p = []; for (let y = bottom; y < nk[1] + 0.02; y += dy) p.push([[0, y, zc], [0, 0, -1]]); paths.push(p); }
  for (const side of [1, -1]) {
    const ax = Math.abs(side > 0 ? ul[0] : ur[0]);
    // Side back: from the waist a hand's width off centre, curving out into the back of the armhole.
    { const p = [], top = armY - 0.045, xw = 0.36 * ax, xa = 0.8 * ax;
      for (let y = bottom; y <= top; y += dy) { const u = (y - bottom) / (top - bottom); p.push([[side * (xw + (xa - xw) * u * u * u), y, zc], [0, 0, -1]]); }
      paths.push(p); }
    // Shoulder: neck to shoulder point along the top, a little behind the middle.
    { const p = []; for (let x = 0.4 * ax; x <= 0.97 * ax; x += dy) p.push([[side * x, armY + 0.35, zc - 0.012], [0, -1, 0]]); paths.push(p); }
  }
  void S;
  return paths;
}

/** One seam's groove along `pts` (points on the coat), appended to the arrays; `closed` joins
 * its ends. Skin rows are blended over the coat's triangle under each point, so the groove
 * bends with the cloth (a nearest point's row let it dip in and out as a dashed line walking). */
function groove(S, pts, A, closed = false) {
  const C = SEAM, { P, N, UV, SI, SW, index } = A, base = P.length / 3, m = pts.length; let rows = 0;
  for (let i = 0; i < m; i++) {
    const p = pts[i], a = pts[closed ? (i - 1 + m) % m : Math.max(0, i - 1)], b = pts[closed ? (i + 1) % m : Math.min(m - 1, i + 1)], here = S.at(p);
    const n = here ? here.n : [0, 0, 1], t = unit([b[0] - a[0], b[1] - a[1], b[2] - a[2]]), sv = unit(cross(n, t));
    const nl = unit([n[0] - C.tilt * sv[0], n[1] - C.tilt * sv[1], n[2] - C.tilt * sv[2]]), nr = unit([n[0] + C.tilt * sv[0], n[1] + C.tilt * sv[1], n[2] + C.tilt * sv[2]]);
    // Four points a row: outer left, inner left, inner right, outer right (inner pair shares a place).
    const lift = (k) => [p[0] + n[0] * k, p[1] + n[1] * k, p[2] + n[2] * k];
    const ol = lift(C.lift), mid = lift(C.lift - C.sink), or = lift(C.lift);
    const sk = [], sw = []; S.skinAt(p, sk, sw);
    for (const [q, nn, off] of [[ol, nl, C.half], [mid, nl, 0], [mid, nr, 0], [or, nr, -C.half]]) {
      P.push(q[0] + sv[0] * off, q[1] + sv[1] * off, q[2] + sv[2] * off); N.push(...nn);
      SI.push(...sk); SW.push(...sw); if (here) S.uv(here.v, UV); else UV.push(0, 0);
    }
    rows++;
  }
  const segs = closed ? rows : rows - 1;
  for (let i = 0; i < segs; i++) { const a = base + i * 4, b = base + ((i + 1) % rows) * 4; index.push(a, a + 1, b, a + 1, b + 1, b, a + 2, a + 3, b + 2, a + 3, b + 3, b + 2); }
  return rows;
}

/** Points along a run of cloth at an even step. */
function evenStep(r, step) {
  const pts = [r[0]]; let acc = 0;
  for (let i = 1; i < r.length; i++) { acc += Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1], r[i][2] - r[i - 1][2]); if (acc >= step) { pts.push(r[i]); acc = 0; } }
  return pts;
}

/** Armholes: where the coat's cloth turns from the body's to the arm's (its skin half the arm's),
 * a closed line round each shoulder, evened along itself and laid back on the cloth. */
export const ARMHOLE = Object.freeze({ arm: /^(upperarm|lowerarm|hand)/, level: 0.5, even: 24, min: 0.25 });
function armholes(S, coat) {
  const W = S.W, part = W.parts[0], geo = coat.geometry, si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight, bones = coat.skeleton?.bones ?? [];
  const memberOf = new Int32Array(W.G).fill(-1); for (let i = 0; i < part.group.length; i++) if (memberOf[part.group[i]] < 0) memberOf[part.group[i]] = i;
  const armOf = (side) => { const a = new Float64Array(W.G), sfx = side > 0 ? '_l' : '_r'; for (let g = 0; g < W.G; g++) { const v = memberOf[g]; if (v < 0) continue; for (let k = 0; k < 4; k++) { const b = bones[si.getComponent(v, k)]; if (b && ARMHOLE.arm.test(b.name) && b.name.endsWith(sfx)) a[g] += sw.getComponent(v, k); } } return a; };
  const out = [];
  for (const side of [1, -1]) {
    const a = armOf(side), L = ARMHOLE.level, seg = new Map(), pt = new Map();
    const cut = (i, j) => { const k = i < j ? `${i}_${j}` : `${j}_${i}`; if (!pt.has(k)) { const f = (L - a[i]) / (a[j] - a[i]); pt.set(k, [0, 1, 2].map((d) => W.P[i * 3 + d] + (W.P[j * 3 + d] - W.P[i * 3 + d]) * f)); } return k; };
    for (let t = 0; t < W.tris.length; t += 3) {
      const v = [W.tris[t], W.tris[t + 1], W.tris[t + 2]], ks = [];
      for (let e = 0; e < 3; e++) { const i = v[e], j = v[(e + 1) % 3]; if ((a[i] < L) !== (a[j] < L)) ks.push(cut(i, j)); }
      if (ks.length === 2) { (seg.get(ks[0]) ?? seg.set(ks[0], []).get(ks[0])).push(ks[1]); (seg.get(ks[1]) ?? seg.set(ks[1], []).get(ks[1])).push(ks[0]); }
    }
    // The longest chain is the armhole.
    const seen = new Set(); let best = [];
    for (const k0 of seg.keys()) {
      if (seen.has(k0)) continue;
      const chain = [k0]; seen.add(k0); let cur = k0;
      for (;;) { const nx = (seg.get(cur) ?? []).find((k) => !seen.has(k)); if (!nx) break; chain.push(nx); seen.add(nx); cur = nx; }
      if (chain.length > best.length) best = chain;
    }
    if (best.length < 12) continue;
    const loop = best.map((k) => pt.get(k).slice()), m = loop.length;
    const closed = Math.hypot(...[0, 1, 2].map((d) => loop[0][d] - loop[m - 1][d])) < 0.02;
    for (let it = 0; it < ARMHOLE.even; it++) { const T = loop.map((p) => p.slice()); for (let i = 0; i < m; i++) { if (!closed && (i === 0 || i === m - 1)) continue; const p0 = loop[(i - 1 + m) % m], p1 = loop[(i + 1) % m]; for (let d = 0; d < 3; d++) T[i][d] = 0.5 * loop[i][d] + 0.25 * (p0[d] + p1[d]); } loop.splice(0, m, ...T); }
    // Back on the cloth: each point to the coat's surface under it, along the normal there.
    const on = loop.map((p) => { const at = S.at(p); if (!at) return p; const n = at.n, h = S.hit([p[0] + n[0] * 0.02, p[1] + n[1] * 0.02, p[2] + n[2] * 0.02], [-n[0], -n[1], -n[2]], 0.04); return h ?? p; });
    out.push({ pts: evenStep(on, SEAM.step), closed });
  }
  return out;
}

function buildSeams(coat, body) {
  const S = surfaceOf(coat), J = bindJoints(body), C = SEAM;
  const A = { P: [], N: [], UV: [], SI: [], SW: [], index: [] };
  let seams = 0;
  for (const path of seamRays(J, S)) {
    // Hits, then a resample at an even step along the cloth.
    const hits = [];
    for (const [o, d] of path) { const h = S.hit(o, d); hits.push(h); }
    const runs = []; let run = [];
    for (const h of hits) { if (h && (!run.length || Math.hypot(h[0] - run.at(-1)[0], h[1] - run.at(-1)[1], h[2] - run.at(-1)[2]) < C.gap)) run.push(h); else { if (run.length > 3) runs.push(run); run = h ? [h] : []; } }
    if (run.length > 3) runs.push(run);
    for (const r of runs) { const pts = evenStep(r, C.step); if (pts.length < 3) continue; groove(S, pts, A); seams++; }
  }
  for (const { pts, closed } of armholes(S, coat)) if (pts.length >= 8) { groove(S, pts, A, closed); seams++; }
  const { P, N, UV, SI, SW, index } = A;
  if (!index.length) return null;
  // Face outward: the triangles' winding toward their normals.
  const Pa = Float64Array.from(P);
  let agree = 0; for (let t = 0; t < index.length; t += 3) { const i0 = index[t] * 3, i1 = index[t + 1] * 3, i2 = index[t + 2] * 3; const f = cross([Pa[i1] - Pa[i0], Pa[i1 + 1] - Pa[i0 + 1], Pa[i1 + 2] - Pa[i0 + 2]], [Pa[i2] - Pa[i0], Pa[i2 + 1] - Pa[i0 + 1], Pa[i2 + 2] - Pa[i0 + 2]]); agree += Math.sign(f[0] * N[i0] + f[1] * N[i0 + 1] + f[2] * N[i0 + 2]); }
  if (agree < 0) for (let t = 0; t < index.length; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; }
  appendGeometry(coat, { P: Pa, N: Float64Array.from(N), UV, SI, SW, index });
  return { seams, points: Pa.length / 3 };
}

function buildFrontButtons(coat, lapels, silk, lod, brk0 = null) {
  const C = FRONT_BUTTONS, S = surfaceOf(coat), Wl = weldMeshes([lapels]);
  // The lapels' break (their lowest point in front) to the waist seam (the coat body's bottom in front).
  let brk = brk0 ?? Infinity; if (brk0 == null) for (let g = 0; g < Wl.G; g++) if (Wl.P[g * 3 + 2] > 0.05 && Math.abs(Wl.P[g * 3]) < 0.04) brk = Math.min(brk, Wl.P[g * 3 + 1]);
  let low = Infinity; for (let g = 0; g < S.W.G; g++) if (S.W.P[g * 3 + 2] > 0.05 && Math.abs(S.W.P[g * 3]) < 0.04) low = Math.min(low, S.W.P[g * 3 + 1]);
  if (!Number.isFinite(brk) || !Number.isFinite(low) || brk - low < 0.06) return null;
  const segs = C.segments[Math.min(lod, 1)], rings = C.rings[Math.min(lod, 1)], P = [], N = [], UV = [], SI = [], SW = [], index = [];
  const top = brk - 0.012, bot = low + 0.025;
  for (let b = 0; b < C.count; b++) {
    const y = top - (top - bot) * (b / (C.count - 1));
    const h = S.hit([0, y, 0], [0, 0, 1]); if (!h) continue;
    const here = S.at(h); if (!here) continue;
    const n = unit(here.n[2] > 0 ? here.n : [0, 0, 1]), e1 = unit(cross([0, 1, 0], n)), e2 = cross(n, e1);
    const base = P.length / 3;
    // A dome: centre, then rings out to the rim (the rim just over the cloth).
    for (let r = 0; r <= rings; r++) {
      const f = r / rings, rad = C.radius * Math.sin(f * Math.PI / 2), up = C.lift + C.dome * Math.cos(f * Math.PI / 2);
      const cnt = r === 0 ? 1 : segs;
      for (let k = 0; k < cnt; k++) {
        const a = (k / segs) * 2 * Math.PI, ca = Math.cos(a) * rad, sa = Math.sin(a) * rad;
        P.push(h[0] + n[0] * up + e1[0] * ca + e2[0] * sa, h[1] + n[1] * up + e1[1] * ca + e2[1] * sa, h[2] + n[2] * up + e1[2] * ca + e2[2] * sa);
        const tilt = Math.sin(f * Math.PI / 2) * 0.9, dir = [Math.cos(a), Math.sin(a)];
        N.push(...unit([n[0] + tilt * (e1[0] * dir[0] + e2[0] * dir[1]), n[1] + tilt * (e1[1] * dir[0] + e2[1] * dir[1]), n[2] + tilt * (e1[2] * dir[0] + e2[2] * dir[1])]));
        S.skin(here.v, SI, SW); UV.push(0.5, 0.5);
      }
    }
    for (let k = 0; k < segs; k++) index.push(base, base + 1 + k, base + 1 + (k + 1) % segs);
    for (let r = 1; r < rings; r++) for (let k = 0; k < segs; k++) {
      const a = base + 1 + (r - 1) * segs + k, b = base + 1 + (r - 1) * segs + (k + 1) % segs, c = a + segs, d = b + segs;
      index.push(a, c, b, b, c, d);
    }
  }
  if (!index.length) return null;
  const Pa = Float64Array.from(P);
  let agree = 0; for (let t = 0; t < index.length; t += 3) { const i0 = index[t] * 3, i1 = index[t + 1] * 3, i2 = index[t + 2] * 3; const f = cross([Pa[i1] - Pa[i0], Pa[i1 + 1] - Pa[i0 + 1], Pa[i1 + 2] - Pa[i0 + 2]], [Pa[i2] - Pa[i0], Pa[i2 + 1] - Pa[i0 + 1], Pa[i2 + 2] - Pa[i0 + 2]]); agree += Math.sign(f[0] * N[i0] + f[1] * N[i0 + 1] + f[2] * N[i0 + 2]); }
  if (agree < 0) for (let t = 0; t < index.length; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; }
  appendGeometry(silk, { P: Pa, N: Float64Array.from(N), UV, SI, SW, index }, true);
  return { buttons: C.count, points: Pa.length / 3 };
}

/** Pressed pieces (lapels, revers) move as the coat under them moves: each of their points takes
 * the skin rows of the nearest point of the coat's body (its shoulders evened first). Drawn, a
 * lapel's peak beside the neck was bound to the upper arm more than the coat under it was, and
 * swung out over the shoulder as the arm came down from the bind pose (a flap, read as a lump). */
export const PRESSED = Object.freeze([
  { piece: /frock_coat_lapels(_lod\d+)?$/, on: /frock_coat_body(_lod\d+)?$/ },
  { piece: /tailcoat_lapels(_lod\d+)?$/, on: /tailcoat_body(_lod\d+)?$/ },
  { piece: /lady_jacket_revers(_lod\d+)?$/, on: /lady_jacket_body(_lod\d+)?$/ },
]);
/** A drawn silk facing's point this near a drawn lapel's is a copy of it (human-frockcoat.js). */
export const FACING_COPY_M = 0.004;

/** Copy skin rows onto `target`'s vertices from the nearest vertex of `source` (bones matched by
 * name). Returns the vertices changed. */
function weightsFrom(target, source) {
  const Ps = bindPositions(source), near = pointGrid(Ps, 0.02), Pt = bindPositions(target);
  const ssi = source.geometry.attributes.skinIndex, ssw = source.geometry.attributes.skinWeight, tsi = target.geometry.attributes.skinIndex, tsw = target.geometry.attributes.skinWeight;
  const local = new Map(target.skeleton.bones.map((b, i) => [b.name, i])), sBones = source.skeleton.bones;
  let changed = 0;
  for (let i = 0; i < Pt.length / 3; i++) {
    const x = Pt[i * 3], y = Pt[i * 3 + 1], z = Pt[i * 3 + 2];
    const j = near(x, y, z); if (j < 0) continue;
    const row = [];
    for (let k = 0; k < 4; k++) { const nm = sBones[ssi.getComponent(j, k)]?.name, w = ssw.getComponent(j, k); if (nm && local.has(nm) && w > 0) row.push([local.get(nm), w]); }
    if (!row.length) continue;
    const sum = row.reduce((a, [, w]) => a + w, 0);
    let q = row.map(([b, w]) => [b, w / sum]);
    if (tsw.normalized && tsw.array.constructor === Uint8Array) { const ints = q.map(([, w]) => Math.floor(w * 255)); let rest = 255 - ints.reduce((a, b) => a + b, 0); for (let k = 0; rest > 0; k = (k + 1) % ints.length, rest--) ints[k]++; q = q.map(([b], k) => [b, ints[k] / 255]); }
    for (let k = 0; k < 4; k++) { const e = q[k]; tsi.setComponent(i, k, e ? e[0] : 0); tsw.setComponent(i, k, e ? e[1] : 0); }
    changed++;
  }
  if (changed) { tsi.needsUpdate = true; tsw.needsUpdate = true; }
  return changed;
}

/** A coat's skin rows evened round each shoulder: drawn, the sleeve head went from the body's
 * bones to the upper arm's within a centimetre or two, so bringing the arm down from the bind
 * pose folded the cloth at the shoulder's point into a ledge. Evened over the cloth within
 * `reach` of the shoulder joint (fading out over `fade`), it rounds over the shoulder instead. */
export const SHOULDERED = /(frock_coat_body|coat_body|tailcoat_body|jacket_body|skeleton_jacket|child_jacket)(_lod\d+)?$/;
export const SHOULDER_EVEN = Object.freeze({ reach: 0.07, fade: 0.06, iters: 24 });

function evenShoulders(coat, J) {
  const C = SHOULDER_EVEN, W = weldMeshes([coat]), part = W.parts[0], si = coat.geometry.attributes.skinIndex, sw = coat.geometry.attributes.skinWeight;
  const joints = ['upperarm_l', 'upperarm_r'].map((n) => J[n]).filter(Boolean);
  if (!joints.length) return 0;
  const memberOf = new Int32Array(W.G).fill(-1); for (let i = 0; i < part.group.length; i++) if (memberOf[part.group[i]] < 0) memberOf[part.group[i]] = i;
  const mask = new Float64Array(W.G);
  for (let g = 0; g < W.G; g++) { let d = Infinity; for (const j of joints) d = Math.min(d, Math.hypot(W.P[g * 3] - j[0], W.P[g * 3 + 1] - j[1], W.P[g * 3 + 2] - j[2])); mask[g] = 1 - Math.max(0, Math.min(1, (d - C.reach) / C.fade)); }
  const active = []; for (let g = 0; g < W.G; g++) if (mask[g] > 0) active.push(g);
  if (!active.length) return 0;
  let w = new Array(W.G).fill(null);
  const rowOf = (i) => { const m = new Map(); for (let k = 0; k < 4; k++) { const v = sw.getComponent(i, k); if (v > 0) m.set(si.getComponent(i, k), (m.get(si.getComponent(i, k)) ?? 0) + v); } return m; };
  const need = new Set(active); for (const g of active) for (const h of W.nb[g]) need.add(h);
  for (const g of need) w[g] = rowOf(memberOf[g]);
  for (let it = 0; it < C.iters; it++) {
    const next = w.slice();
    for (const g of active) {
      const acc = new Map(); let c = 0;
      for (const h of W.nb[g]) { if (!w[h]) continue; c++; for (const [b, v] of w[h]) acc.set(b, (acc.get(b) ?? 0) + v); }
      if (!c) continue;
      const out = new Map(), k = 0.5 * mask[g];
      for (const [b, v] of w[g]) out.set(b, v * (1 - k));
      for (const [b, v] of acc) out.set(b, (out.get(b) ?? 0) + k * v / c);
      next[g] = out;
    }
    w = next;
  }
  const byte = sw.normalized && sw.array.constructor === Uint8Array;
  for (const g of active) {
    let q = [...w[g]].sort((a, b) => b[1] - a[1]).slice(0, 4); const sum = q.reduce((a, [, v]) => a + v, 0) || 1; q = q.map(([b, v]) => [b, v / sum]);
    if (byte) { const ints = q.map(([, v]) => Math.floor(v * 255)); let rest = 255 - ints.reduce((a, b) => a + b, 0); for (let k = 0; rest > 0; k = (k + 1) % ints.length, rest--) ints[k]++; q = q.map(([b], k) => [b, ints[k] / 255]); }
    for (const [pp, i] of W.members[g]) { void pp; for (let k = 0; k < 4; k++) { const e = q[k]; si.setComponent(i, k, e ? e[0] : 0); sw.setComponent(i, k, e ? e[1] : 0); } }
  }
  si.needsUpdate = true; sw.needsUpdate = true;
  return active.length;
}

/** A lapel lies on the chest: drawn, the peaks of a frock coat's reached up over the top of the
 * shoulder beside the neck and showed from behind. Its triangles lying wholly out past half the
 * shoulders' span and above the collarbone joints are left out. */
function offShoulders(mesh, J) {
  const ul = J.upperarm_l, ur = J.upperarm_r, cl = J.clavicle_l ?? J.clavicle_r; if (!ul || !ur || !cl) return 0;
  const half = 0.25 * Math.abs(ul[0] - ur[0]), top = cl[1] + 0.01, P = bindPositions(mesh), idx = mesh.geometry.index.array, kept = [];
  const over = (i) => Math.abs(P[i * 3]) > half && P[i * 3 + 1] > top;
  for (let t = 0; t < idx.length; t += 3) if (!(over(idx[t]) && over(idx[t + 1]) && over(idx[t + 2]))) kept.push(idx[t], idx[t + 1], idx[t + 2]);
  if (kept.length === idx.length) return 0;
  mesh.geometry.setIndex(new THREE.BufferAttribute(new (idx.constructor)(kept), 1));
  return (idx.length - kept.length) / 3;
}

/** A frock coat's lapels cut again: drawn, each was some 120 points, folded and creased, with a
 * silk copy of its face that shone on every crease. Now each is a smooth strip laid on the coat
 * from the break (the top button) up the coat's own front edge to the gorge beside the neck,
 * widening to `width` across the chest and squared off at its point, rolled over at the front
 * edge, faced in silk all over (in the silk's mesh); the drawn lapels and their facings are
 * left out. Every level, at its own fineness. */
export const LAPEL = Object.freeze({ piece: /frock_coat_lapels(_lod\d+)?$/, coat: /frock_coat_body(_lod\d+)?$/, silk: /four_in_hand_tie(_lod\d+)?$/,
  width: 0.062, widest: 0.62, press: 6, point: 0.86, gorge: 0.22, front: 0.045, even: 6, rows: [44, 26, 14, 8], under: 0.003, fade: 0.012, drop: 0.006, silkRoughness: 0.6,
  across: [[-0.12, 0.0008], [0, 0.0034], [0.08, 0.0044], [0.22, 0.0038], [0.45, 0.0034], [0.7, 0.0033], [0.9, 0.0031], [1, 0.0016]], lods: [0, 0, 1, 2] });

/** Before refining: the drawn lapels and their silk facings left out. Returns the break height. */
function clearLapels(lapels, silk) {
  const Pl = bindPositions(lapels), near = pointGrid(Pl, 0.02), idxL = lapels.geometry.index.array;
  const used = new Uint8Array(Pl.length / 3); for (let t = 0; t < idxL.length; t++) used[idxL[t]] = 1;
  let brk = Infinity; for (let i = 0; i < used.length; i++) if (used[i] && Pl[i * 3 + 2] > 0.05 && Math.abs(Pl[i * 3]) < 0.04) brk = Math.min(brk, Pl[i * 3 + 1]);
  if (silk) {
    const Ps = bindPositions(silk), idx = silk.geometry.index.array, kept = [];
    const onLapel = (i) => { const j = near(Ps[i * 3], Ps[i * 3 + 1], Ps[i * 3 + 2]); return j >= 0 && used[j] && Math.hypot(Pl[j * 3] - Ps[i * 3], Pl[j * 3 + 1] - Ps[i * 3 + 1], Pl[j * 3 + 2] - Ps[i * 3 + 2]) < FACING_COPY_M; };
    for (let t = 0; t < idx.length; t += 3) if (!(onLapel(idx[t]) && onLapel(idx[t + 1]) && onLapel(idx[t + 2]))) kept.push(idx[t], idx[t + 1], idx[t + 2]);
    silk.geometry.setIndex(new THREE.BufferAttribute(new (idx.constructor)(kept), 1));
  }
  lapels.geometry.setIndex(new THREE.BufferAttribute(new (idxL.constructor)(0), 1));
  lapels.geometry.userData = { ...lapels.geometry.userData, chicagoRebuilt: { lapels: 'cut again' } };
  return brk;
}

/** After refining: the new lapels, in the silk's mesh. Returns { rows, points, tops } (tops: each
 * lapel's gorge, where the collar meets it). */
function cutLapels(coat, silk, brk, lod) {
  const C = LAPEL, S = surfaceOf(coat), W = S.W, rows = C.rows[Math.min(lod, 3)];
  const loops = loopsOf(W);
  const P = [], N = [], UV = [], SI = [], SW = [], index = [], tops = [], L = [], sides = [];
  const smooth = (A, it) => { for (let k = 0; k < it; k++) { const B = A.map((p) => p.slice()); for (let i = 1; i + 1 < A.length; i++) for (let d = 0; d < 3; d++) B[i][d] = 0.25 * A[i - 1][d] + 0.5 * A[i][d] + 0.25 * A[i + 1][d]; A.splice(0, A.length, ...B); } };
  for (const side of [1, -1]) {
    // The coat's front edge on this side, from the break up to the neck.
    let best = null;
    for (const l of loops) { const pts = l.filter((g) => side * W.P[g * 3] >= -0.002 && W.P[g * 3 + 2] > C.front && W.P[g * 3 + 1] >= brk - 0.004 && W.P[g * 3 + 1] < brk + 0.4); if (!best || pts.length > best.length) best = pts; }
    if (!best || best.length < 4) continue;
    const edge = best.map((g) => [W.P[g * 3], W.P[g * 3 + 1], W.P[g * 3 + 2]]).sort((a, b) => a[1] - b[1]);
    // Even steps along it.
    const len = [0]; for (let i = 1; i < edge.length; i++) len.push(len[i - 1] + Math.hypot(edge[i][0] - edge[i - 1][0], edge[i][1] - edge[i - 1][1], edge[i][2] - edge[i - 1][2]));
    const R = []; for (let r = 0; r <= rows; r++) { const want = len.at(-1) * r / rows; let i = 1; while (i < len.length - 1 && len[i] < want) i++; const f = (want - len[i - 1]) / Math.max(1e-9, len[i] - len[i - 1]); R.push([0, 1, 2].map((d) => edge[i - 1][d] + (edge[i][d] - edge[i - 1][d]) * Math.min(1, Math.max(0, f)))); }
    smooth(R, 12);
    const base = P.length / 3, cols = C.across.length, row = [];
    for (let r = 0; r <= rows; r++) {
      const u = r / rows, p = R[r], a = R[Math.max(0, r - 1)], b = R[Math.min(rows, r + 1)];
      const here = S.at(p); const nC = here ? here.n : [0, 0, 1];
      // Across: square to the edge as seen from in front.
      const t2 = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, o = [(b[1] - a[1]) / t2 * side, -(b[0] - a[0]) / t2 * side, 0];
      if (o[0] * side < 0) { o[0] = -o[0]; o[1] = -o[1]; }
      // Width: from nothing at the break to full across the chest, square at the point, then the
      // gorge up to the neck.
      const f = u < C.point ? (u < C.widest ? Math.sin((u / C.widest) * Math.PI / 2) ** 0.8 : 1) : 1 - (1 - C.gorge) * ((u - C.point) / (1 - C.point));
      const w = C.width * f;
      // A ruled strip from the front edge out to the cloth under the lapel's outer edge, bowed as
      // the chest bows under it (measured at its middle).
      const onCoat = (v) => { const q = [p[0] + o[0] * v * w, p[1] + o[1] * v * w, p[2]]; const h = S.hit([q[0], q[1], q[2] + 0.3], [0, 0, -1], 0.5); return h && h[2] > p[2] - 0.02 ? h : null; };
      const out = onCoat(1) ?? [p[0] + o[0] * w, p[1] + o[1] * w, p[2]], mid = onCoat(0.5);
      const atOut = S.at(out) ?? here, n = atOut ? atOut.n.slice() : nC.slice();
      const chord = [(p[0] + out[0]) / 2, (p[1] + out[1]) / 2, (p[2] + out[2]) / 2];
      const bow = mid ? Math.max(0, (mid[0] - chord[0]) * n[0] + (mid[1] - chord[1]) * n[1] + (mid[2] - chord[2]) * n[2]) : 0;
      row.push({ u, p, o, out: out.slice(), n, bow: [bow] });
    }
    // The lapel is pressed cloth, smooth along its length: its outer edge, its tilt and its bow
    // are evened row to row (the coat under it is set back beneath it after, so the facing no
    // longer follows the coat's every facet; drawn, it shone on each one as a lump).
    for (const key of ['out', 'n', 'bow']) { const A = row.map((q) => q[key]); for (let k = 0; k < Math.round(C.press * rows / C.rows[0]); k++) { const B = A.map((q) => q.slice()); for (let i = 1; i + 1 < A.length; i++) for (let d = 0; d < A[i].length; d++) B[i][d] = 0.25 * A[i - 1][d] + 0.5 * A[i][d] + 0.25 * A[i + 1][d]; A.splice(0, A.length, ...B); } row.forEach((q, i) => { q[key] = A[i]; }); }
    for (const q of row) { const l = Math.hypot(...q.n) || 1; q.n = q.n.map((x) => x / l); }
    for (const { u, p, o, out, n, bow: [bow] } of row) {
      for (const [v, lift] of C.across) {
        const vv = Math.max(0, v), b = bow * 4 * vv * (1 - vv) + lift;
        const x = [p[0] + (out[0] - p[0]) * vv + o[0] * Math.min(0, v) * 0.06, p[1] + (out[1] - p[1]) * vv + o[1] * Math.min(0, v) * 0.06, p[2] + (out[2] - p[2]) * vv];
        P.push(x[0] + n[0] * b, x[1] + n[1] * b, x[2] + n[2] * b); L.push(lift);
        S.skinAt(x, SI, SW);
        UV.push(0.05 + 0.4 * u, 0.05 + 0.1 * vv);
      }
      if (u === 1) tops.push(p);
    }
    // Each side wound to face out from the chest (the two sides mirror, so one was wound in:
    // its normals pointed into the coat and the cull took that whole lapel for covered).
    const t0 = index.length;
    for (let r = 0; r < rows; r++) for (let c = 0; c + 1 < cols; c++) { const i0 = base + r * cols + c, i1 = i0 + 1, i2 = i0 + cols, i3 = i2 + 1; index.push(i0, i2, i1, i1, i2, i3); }
    sides.push([t0, index.length]);
  }
  if (!index.length) return null;
  const Pa = Float64Array.from(P), n = Pa.length / 3;
  // Evened over the grid, then set again at its height over the coat: one smooth strip.
  { const nb = Array.from({ length: n }, () => new Set()); for (let t = 0; t < index.length; t += 3) for (let k = 0; k < 3; k++) for (const j of [index[t + (k + 1) % 3], index[t + (k + 2) % 3]]) if (Math.abs(j - index[t + k]) === C.across.length) nb[index[t + k]].add(j);
    for (let it = 0; it < C.even; it++) {
      const T = Float64Array.from(Pa);
      for (let i = 0; i < n; i++) { if (!nb[i].size) continue; let x = 0, y = 0, z = 0; for (const j of nb[i]) { x += Pa[j * 3]; y += Pa[j * 3 + 1]; z += Pa[j * 3 + 2]; } T[i * 3] = 0.5 * Pa[i * 3] + 0.5 * x / nb[i].size; T[i * 3 + 1] = 0.5 * Pa[i * 3 + 1] + 0.5 * y / nb[i].size; T[i * 3 + 2] = 0.5 * Pa[i * 3 + 2] + 0.5 * z / nb[i].size; }
      Pa.set(T);
    } }
  // Face outward (as the coat faces), side by side: the face normal of each triangle against the
  // coat's under it; a side that faces in is wound the other way.
  for (const [t0, t1] of sides) {
    let agree = 0;
    for (let t = t0; t < t1; t += 3) {
      const a = index[t] * 3, b = index[t + 1] * 3, c = index[t + 2] * 3;
      const ux = Pa[b] - Pa[a], uy = Pa[b + 1] - Pa[a + 1], uz = Pa[b + 2] - Pa[a + 2], vx = Pa[c] - Pa[a], vy = Pa[c + 1] - Pa[a + 1], vz = Pa[c + 2] - Pa[a + 2];
      const at = S.at([Pa[a], Pa[a + 1], Pa[a + 2]]); if (!at) continue;
      agree += (uy * vz - uz * vy) * at.n[0] + (uz * vx - ux * vz) * at.n[1] + (ux * vy - uy * vx) * at.n[2];
    }
    if (agree < 0) for (let t = t0; t < t1; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; }
  }
  const Nn = graphNormals(Pa, index, n);
  appendGeometry(silk, { P: Pa, N: Nn, UV, SI, SW, index }, true);
  // Faced in a faille's soft sheen, not a glaze: at the tie's drawn 0.45 each lapel shone as one
  // broad highlight, a blob on the chest (round 8).
  for (const m of [silk.material].flat()) if (m && 'roughness' in m) m.roughness = Math.max(m.roughness, C.silkRoughness);
  const sunk = sinkUnderLapels(S.W, Pa, index);
  return { rows, points: n, tops, sunk };
}

/** The coat under a lapel kept `LAPEL.under` beneath it: drawn coarse, the coat's facets bulged
 * up between the lapel's rows and came through the silk as dark shards (and the cull, finding
 * the silk covered there, cut it into shards; the owner, 2026-11-26: "Look how bad their lapels
 * are"). Each point of the coat lying under a lapel, seen from in front, is set back to
 * `under` behind the lapel's face there; out past the lapel's edge, by less, over `fade`. The
 * coat there is never seen. Positions only. Returns the points moved. */
function sinkUnderLapels(W, Pa, index) {
  const C = LAPEL, tris = [];
  for (let t = 0; t < index.length; t += 3) {
    const a = index[t] * 3, b = index[t + 1] * 3, c = index[t + 2] * 3;
    tris.push([Pa[a], Pa[a + 1], Pa[a + 2], Pa[b], Pa[b + 1], Pa[b + 2], Pa[c], Pa[c + 1], Pa[c + 2]]);
  }
  // The lapel's face, seen from in front: its height (z) over a point, and how far outside it lies.
  const faceAt = (x, y) => {
    let best = null, bestOut = Infinity;
    for (const q of tris) {
      const minX = Math.min(q[0], q[3], q[6]) - C.fade, maxX = Math.max(q[0], q[3], q[6]) + C.fade;
      const minY = Math.min(q[1], q[4], q[7]) - C.fade, maxY = Math.max(q[1], q[4], q[7]) + C.fade;
      if (x < minX || x > maxX || y < minY || y > maxY) continue;
      const v0x = q[3] - q[0], v0y = q[4] - q[1], v1x = q[6] - q[0], v1y = q[7] - q[1], v2x = x - q[0], v2y = y - q[1];
      const den = v0x * v1y - v1x * v0y; if (Math.abs(den) < 1e-12) continue;
      const b1 = (v2x * v1y - v1x * v2y) / den, b2 = (v0x * v2y - v2x * v0y) / den, b0 = 1 - b1 - b2;
      // how far outside, in metres (roughly: the most negative coordinate times the triangle's size)
      const size = Math.sqrt(Math.abs(den)), out = -Math.min(0, b0, b1, b2) * size;
      if (out < bestOut) {
        const c0 = Math.max(0, b0), c1 = Math.max(0, b1), c2 = Math.max(0, b2), cs = c0 + c1 + c2 || 1;
        bestOut = out; best = (c0 * q[2] + c1 * q[5] + c2 * q[8]) / cs;
        if (out === 0) break;
      }
    }
    return best === null || bestOut > C.fade ? null : { z: best, out: bestOut };
  };
  let moved = 0;
  for (let g = 0; g < W.G; g++) {
    const x = W.P[g * 3], y = W.P[g * 3 + 1], z = W.P[g * 3 + 2];
    const f = faceAt(x, y); if (!f || z < f.z - 0.05) continue;
    const want = f.z - C.under * (1 - smooth01(f.out / C.fade));
    if (z > want) { W.P[g * 3 + 2] = want; moved++; }
  }
  // A far level's coat faces are long: one whose corners all lie outside the lapel can still pass
  // in front of it between them. Each lapel point's coat face, seen from in front, is set back
  // under it, corners and all (twice over: setting one back can raise none).
  const T = W.tris, box = [];
  for (let t = 0; t < T.length; t += 3) {
    const a = T[t] * 3, b = T[t + 1] * 3, c = T[t + 2] * 3;
    box.push([Math.min(W.P[a], W.P[b], W.P[c]), Math.max(W.P[a], W.P[b], W.P[c]), Math.min(W.P[a + 1], W.P[b + 1], W.P[c + 1]), Math.max(W.P[a + 1], W.P[b + 1], W.P[c + 1])]);
  }
  const lowered = new Set();
  for (let pass = 0; pass < 2; pass++) {
    // each corner set back once a pass, by the most any face of it needs (summed, a corner
    // shared by many faces went back by all of them)
    const need = new Map();
    for (let i = 0; i < Pa.length / 3; i++) {
      const x = Pa[i * 3], y = Pa[i * 3 + 1], z = Pa[i * 3 + 2];
      for (let t = 0, k = 0; t < T.length; t += 3, k++) {
        const bx = box[k]; if (x < bx[0] || x > bx[1] || y < bx[2] || y > bx[3]) continue;
        const a = T[t] * 3, b = T[t + 1] * 3, c = T[t + 2] * 3;
        const v0x = W.P[b] - W.P[a], v0y = W.P[b + 1] - W.P[a + 1], v1x = W.P[c] - W.P[a], v1y = W.P[c + 1] - W.P[a + 1], v2x = x - W.P[a], v2y = y - W.P[a + 1];
        const den = v0x * v1y - v1x * v0y; if (Math.abs(den) < 1e-14) continue;
        const b1 = (v2x * v1y - v1x * v2y) / den, b2 = (v0x * v2y - v2x * v0y) / den, b0 = 1 - b1 - b2;
        if (b0 < 0 || b1 < 0 || b2 < 0) continue;
        const zc = b0 * W.P[a + 2] + b1 * W.P[b + 2] + b2 * W.P[c + 2];
        if (zc < z - 0.05 || zc <= z - C.under * 0.5) continue;
        const drop = Math.min(C.drop, zc - (z - C.under));
        for (const q of [a, b, c]) need.set(q, Math.max(need.get(q) ?? 0, drop));
      }
    }
    if (!need.size) break;
    for (const [q, d] of need) { W.P[q + 2] -= d; lowered.add(q); }
  }
  moved += lowered.size;
  if (moved) writeBack(W, null);
  return moved;
}
const smooth01 = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };

/** An apron's shoulder frills gathered as cloth: drawn, each was one flat sheet standing off the
 * strap like a wing ("the way that apron lays is messy and does not look like fabric"). Cut again
 * along the strap's outer edge, from where the drawn frill began in front to where it ended
 * behind (at least `span`, degrees round the shoulder, as drawn at the near level; the far
 * levels' drawn frills stop at the shoulder): a strip `width` wide laid out over the shoulder on the bodice under it, its outer edge
 * standing a little off (`stand`), gathered in folds `fold` long and `depth` deep (by level: none at the
 * farthest) that deepen toward the hem, and narrowing at its two ends. Weights are the bodice's under each point. */
export const RUFFLE = Object.freeze({ piece: /apron_strap_frills(_lod\d+)?$/, strap: /apron_straps(_lod\d+)?$/, on: /bodice(_lod\d+)?$/,
  width: 0.04, stand: 0.012, gap: [0.0025, 0.003, 0.006, 0.008], fold: 0.03, depth: [0.0045, 0.0035, 0.0015, 0], tuck: 0.12, ends: 0.12, K: [200, 120, 40, 20], rows: [6, 4, 3, 2],
  span: [-135, 90] });

const angleOf = (p, yc) => Math.atan2(p[2], p[1] - yc);

/** Before refining: the drawn frills left out. Returns, per side, their angular extent round the shoulder. */
function clearRuffles(frills, yc) {
  const P = bindPositions(frills), idx = frills.geometry.index.array, used = new Set(idx), ext = {};
  for (const i of used) { const side = Math.sign(P[i * 3]) || 1, a = angleOf([P[i * 3], P[i * 3 + 1], P[i * 3 + 2]], yc); const e = (ext[side] ??= [RUFFLE.span[0] * Math.PI / 180, RUFFLE.span[1] * Math.PI / 180]); e[0] = Math.min(e[0], a); e[1] = Math.max(e[1], a); }
  const uv = frills.geometry.attributes.uv; let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
  if (uv) for (const i of used) { u0 = Math.min(u0, uv.getX(i)); u1 = Math.max(u1, uv.getX(i)); v0 = Math.min(v0, uv.getY(i)); v1 = Math.max(v1, uv.getY(i)); }
  frills.geometry.setIndex(new THREE.BufferAttribute(new (idx.constructor)(0), 1));
  frills.geometry.userData = { ...frills.geometry.userData, chicagoRebuilt: { frills: 'gathered again' } };
  return { ext, uvBox: Number.isFinite(u0) ? [u0, u1, v0, v1] : [0, 1, 0, 1] };
}

function buildRuffles(frills, strap, under, lod, yc, cleared) {
  const C = RUFFLE, K = C.K[Math.min(lod, 3)], rows = C.rows[Math.min(lod, 3)], S = surfaceOf(under);
  const Ws = weldMeshes([strap]), loops = loopsOf(Ws), [u0, u1, v0, v1] = cleared.uvBox;
  const P = [], UV = [], SI = [], SW = [], index = [];
  const smooth = (A, it) => { for (let k = 0; k < it; k++) { const B = A.map((p) => p.slice()); for (let i = 1; i + 1 < A.length; i++) for (let d = 0; d < 3; d++) B[i][d] = 0.25 * A[i - 1][d] + 0.5 * A[i][d] + 0.25 * A[i + 1][d]; A.splice(0, A.length, ...B); } };
  for (const side of [1, -1]) {
    const ext = cleared.ext[side]; if (!ext) continue;
    // The strap's outer edge on this side: its outline's points farthest out, angle by angle.
    const bins = new Map();
    for (const l of loops) for (const g of l) {
      const p = [Ws.P[g * 3], Ws.P[g * 3 + 1], Ws.P[g * 3 + 2]]; if (side * p[0] <= 0) continue;
      const a = angleOf(p, yc); if (a < ext[0] - 0.05 || a > ext[1] + 0.05) continue;
      const k = Math.round(a / 0.05), b = bins.get(k); if (!b || side * p[0] > side * b[0]) bins.set(k, p);
    }
    const edge = [...bins.entries()].sort((a, b) => a[0] - b[0]).map((e) => e[1]);
    if (edge.length < 6) continue;
    smooth(edge, 2);
    const len = [0]; for (let i = 1; i < edge.length; i++) len.push(len[i - 1] + Math.hypot(edge[i][0] - edge[i - 1][0], edge[i][1] - edge[i - 1][1], edge[i][2] - edge[i - 1][2]));
    const total = len.at(-1), R = [];
    for (let c = 0; c <= K; c++) { const want = total * c / K; let i = 1; while (i < len.length - 1 && len[i] < want) i++; const f = Math.min(1, Math.max(0, (want - len[i - 1]) / Math.max(1e-9, len[i] - len[i - 1]))); R.push([0, 1, 2].map((d) => edge[i - 1][d] + (edge[i][d] - edge[i - 1][d]) * f)); }
    smooth(R, 6);
    const base = P.length / 3, cols = rows + 1, F = [];
    for (let c = 0; c <= K; c++) {
      const u = c / K, p = R[c], a = R[Math.max(0, c - 1)], b = R[Math.min(K, c + 1)];
      const t = unit([b[0] - a[0], b[1] - a[1], b[2] - a[2]]), at0 = S.at(p), n = at0 ? at0.n : [side, 0, 0];
      // Out from the strap, square to it, along the cloth.
      let d = [side, 0, 0]; const dn = d[0] * n[0] + d[1] * n[1] + d[2] * n[2]; d = [d[0] - dn * n[0], d[1] - dn * n[1], d[2] - dn * n[2]];
      const dt = d[0] * t[0] + d[1] * t[1] + d[2] * t[2]; d = unit([d[0] - dt * t[0], d[1] - dt * t[1], d[2] - dt * t[2]]);
      const endK = Math.min(1, Math.min(u, 1 - u) / C.ends), w = C.width * (0.25 + 0.75 * Math.sin(endK * Math.PI / 2));
      const s = total * u, wave = Math.sin(2 * Math.PI * s / C.fold);
      for (let r = 0; r <= rows; r++) {
        const v = -C.tuck + (1 + C.tuck) * r / rows, vv = Math.max(0, v);
        const q = [p[0] + d[0] * v * w, p[1] + d[1] * v * w, p[2] + d[2] * v * w];
        const hit = S.hit([q[0] + n[0] * 0.06, q[1] + n[1] * 0.06, q[2] + n[2] * 0.06], [-n[0], -n[1], -n[2]], 0.12);
        const at = hit ? S.at(hit) : null, nn = at ? at.n : n, foot = hit ?? q;
        const h = C.gap[Math.min(lod, 3)] + C.stand * vv ** 1.5 + C.depth[Math.min(lod, 3)] * wave * (0.2 + 0.8 * vv);
        F.push({ foot, nn, h });
        S.skinAt(foot, SI, SW);
        UV.push(u0 + (u1 - u0) * u, v0 + (v1 - v0) * vv);
      }
    }
    // The cloth under it evened along the strip (a drawn bodice is bumpy), then the folds laid on.
    for (let it = 0; it < 6; it++) { const T = F.map((f) => ({ ...f, foot: f.foot.slice(), nn: f.nn.slice() })); for (let c = 1; c < K; c++) for (let r = 0; r <= rows; r++) { const a = F[(c - 1) * cols + r], b = F[c * cols + r], e = F[(c + 1) * cols + r], t2 = T[c * cols + r]; for (let d = 0; d < 3; d++) { t2.foot[d] = 0.25 * a.foot[d] + 0.5 * b.foot[d] + 0.25 * e.foot[d]; t2.nn[d] = 0.25 * a.nn[d] + 0.5 * b.nn[d] + 0.25 * e.nn[d]; } } F.splice(0, F.length, ...T); }
    for (const { foot, nn, h } of F) { const m = unit(nn); P.push(foot[0] + m[0] * h, foot[1] + m[1] * h, foot[2] + m[2] * h); }
    for (let c = 0; c < K; c++) for (let r = 0; r < rows; r++) { const i0 = base + c * cols + r, i1 = i0 + 1, i2 = i0 + cols, i3 = i2 + 1; index.push(i0, i1, i2, i1, i3, i2); }
  }
  if (!index.length) return null;
  const Pa = Float64Array.from(P), n = Pa.length / 3, Nn = graphNormals(Pa, index, n);
  let agree = 0; for (let i = 0; i < n; i++) { const at = S.at([Pa[i * 3], Pa[i * 3 + 1], Pa[i * 3 + 2]]); if (at) agree += Nn[i * 3] * at.n[0] + Nn[i * 3 + 1] * at.n[1] + Nn[i * 3 + 2] * at.n[2]; }
  if (agree < 0) { for (let t = 0; t < index.length; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; } for (let i = 0; i < Nn.length; i++) Nn[i] = -Nn[i]; }
  appendGeometry(frills, { P: Pa, N: Nn, UV, SI, SW, index });
  return { points: n, triangles: index.length / 3 };
}

/** A livery coat's neck: drawn, its standing collar ended in front in two small hooks, and the
 * coat's V under the stock showed bare skin to the top button ("his collar does not look
 * natural"). The hooks are faired out (points of the collar's top edge standing more than `burr`
 * off the edge's own smoothed line or forward of the collar's front, and the cloth within
 * `reach` of them, pressed back and evened in place), and
 * the V is filled with a shirt front in the stock's linen, laid on the chest `lift` off the skin
 * from under the coat's edges (`under` past them each side) up under the stock. */
export const LIVERY = Object.freeze({ coat: /livery_coat_body(_lod\d+)?$/, stock: /white_stock(_lod\d+)?$/,
  burr: 0.004, reach: 0.015, iters: 12, lift: 0.0022, under: 0.014, below: 0.012, above: 0.008, rows: [14, 10, 6, 4], cols: [12, 8, 6, 4] });

function deburrNeck(coat) {
  const C = LIVERY, W = weldMeshes([coat]), loops = loopsOf(W);
  if (!loops.length) return 0;
  const mean = (l) => l.reduce((a, g) => a + W.P[g * 3 + 1], 0) / l.length, top = loops.reduce((a, l) => (mean(l) > mean(a) ? l : a));
  // The edge's own line, smoothed along it.
  const Q = Float64Array.from(W.P);
  for (let it = 0; it < 8; it++) { const T = Float64Array.from(Q); for (const g of top) { const l = W.edgeNb[g]; if (l.length !== 2) continue; for (let d = 0; d < 3; d++) T[g * 3 + d] = 0.5 * Q[g * 3 + d] + 0.25 * (Q[l[0] * 3 + d] + Q[l[1] * 3 + d]); } Q.set(T); }
  // And the front of the collar standing forward of the collar's own front line (its usual
  // depth there, by the lower third of the front edge's points).
  const fz = top.filter((g) => Math.abs(W.P[g * 3]) < 0.07 && W.P[g * 3 + 2] > 0.04).map((g) => W.P[g * 3 + 2]).sort((a, b) => a - b);
  const line = fz.length ? fz[Math.floor(fz.length / 3)] : Infinity;
  const seeds = top.filter((g) => Math.hypot(W.P[g * 3] - Q[g * 3], W.P[g * 3 + 1] - Q[g * 3 + 1], W.P[g * 3 + 2] - Q[g * 3 + 2]) > C.burr || (Math.abs(W.P[g * 3]) < 0.07 && W.P[g * 3 + 2] > line + C.burr));
  if (!seeds.length) return 0;
  const dist = distanceFrom(W, seeds), wgt = new Float64Array(W.G);
  let n = 0; for (let g = 0; g < W.G; g++) if (dist[g] < C.reach) { wgt[g] = 1 - dist[g] / C.reach; n++; }
  // Pressed back to the line first (front points only), then evened.
  for (let g = 0; g < W.G; g++) if (wgt[g] && Math.abs(W.P[g * 3]) < 0.07 && W.P[g * 3 + 2] > line + 0.002) W.P[g * 3 + 2] -= wgt[g] * (W.P[g * 3 + 2] - line - 0.002);
  for (let it = 0; it < C.iters; it++) {
    const T = Float64Array.from(W.P);
    for (let g = 0; g < W.G; g++) { if (!wgt[g]) continue; const l = W.edgeNb[g].length === 2 ? W.edgeNb[g] : W.nb[g]; if (!l.length) continue; for (let d = 0; d < 3; d++) { let a = 0; for (const h of l) a += W.P[h * 3 + d]; T[g * 3 + d] += 0.5 * wgt[g] * (a / l.length - W.P[g * 3 + d]); } }
    W.P.set(T);
  }
  writeBack(W, null);
  return n;
}

/** The cloth inside a coat's front V, between `y0` and `y1`: a patch laid on the chest `lift`
 * off the skin from under the coat's edges (`under` past them each side), in `into`'s mesh. */
function fillFront(coat, into, body, lod, y0, y1, reach = 0.06, under = LIVERY.under) {
  const C = LIVERY, W = weldMeshes([coat]), loops = loopsOf(W), S = surfaceOf(body);
  const mean = (l) => l.reduce((a, g) => a + W.P[g * 3 + 1], 0) / l.length, top = loops.reduce((a, l) => (mean(l) > mean(a) ? l : a));
  const front = top.filter((g) => W.P[g * 3 + 2] > 0.04 && Math.abs(W.P[g * 3]) < reach).map((g) => [W.P[g * 3], W.P[g * 3 + 1], W.P[g * 3 + 2]]);
  if (front.length < 6 || !(y1 > y0)) return null;
  const apex = Math.min(...front.map((p) => p[1]));
  // Each side's edge of the V as x by height.
  const edgeX = (side, y) => { let best = null; for (const p of front) { if (side * p[0] < -0.002) continue; const d = Math.abs(p[1] - y); if (!best || d < best[0]) best = [d, p[0]]; } return best ? best[1] : 0; };
  const rows = C.rows[Math.min(lod, 3)], cols = C.cols[Math.min(lod, 3)];
  const P = [], UV = [], SI = [], SW = [], index = [];
  for (let r = 0; r <= rows; r++) {
    const y = y0 + (y1 - y0) * r / rows, yy = Math.min(Math.max(y, apex), y1 + 0.02);
    const xl = Math.min(edgeX(-1, yy), -0.004) - under, xr = Math.max(edgeX(1, yy), 0.004) + under;
    for (let c = 0; c <= cols; c++) {
      const x = xl + (xr - xl) * c / cols, hit = S.hit([x, y, 0.4], [0, 0, -1], 0.6) ?? [x, y, 0.09], at = S.at(hit), n = at ? at.n : [0, 0, 1];
      P.push(hit[0] + n[0] * C.lift, hit[1] + n[1] * C.lift, hit[2] + n[2] * C.lift);
      S.skinAt(hit, SI, SW); UV.push(0.02 + 0.1 * c / cols, 0.02 + 0.1 * r / rows);
    }
  }
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { const i0 = r * (cols + 1) + c, i1 = i0 + 1, i2 = i0 + cols + 1, i3 = i2 + 1; index.push(i0, i1, i2, i1, i3, i2); }
  const Pa = Float64Array.from(P), n = Pa.length / 3, Nn = graphNormals(Pa, index, n);
  let agree = 0; for (let i = 0; i < n; i++) agree += Nn[i * 3 + 2];
  if (agree < 0) { for (let t = 0; t < index.length; t += 3) { const q = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = q; } for (let i = 0; i < Nn.length; i++) Nn[i] = -Nn[i]; }
  appendGeometry(into, { P: Pa, N: Nn, UV, SI, SW, index });
  return { points: n, triangles: index.length / 3 };
}

/** The lowest point, in front, of a piece (a stock's or a collar's bottom edge under the chin). */
function frontBottom(mesh) {
  const P = bindPositions(mesh); let y = Infinity;
  for (const i of new Set(mesh.geometry.index.array)) if (P[i * 3 + 2] > 0.03 && Math.abs(P[i * 3]) < 0.03) y = Math.min(y, P[i * 3 + 1]);
  return y;
}

function fillShirtFront(coat, stock, body, lod) {
  const C = LIVERY, W = weldMeshes([coat]), loops = loopsOf(W);
  const mean = (l) => l.reduce((a, g) => a + W.P[g * 3 + 1], 0) / l.length, top = loops.reduce((a, l) => (mean(l) > mean(a) ? l : a));
  const ys = top.filter((g) => W.P[g * 3 + 2] > 0.04 && Math.abs(W.P[g * 3]) < 0.06).map((g) => W.P[g * 3 + 1]);
  if (!ys.length) return null;
  const sb = frontBottom(stock), apex = Math.min(...ys);
  if (!Number.isFinite(sb) || sb <= apex) return null;
  return fillFront(coat, stock, body, lod, apex - C.below, sb + C.above);
}

/** A frock coat's waistcoat at the far levels: drawn there, its front was left open where the
 * drawn lapels lay over it; cut again, the lapels are narrower and the skin showed through. The
 * waistcoat is closed in its own cloth from under the coat's break up under the shirt collar. */
export const FAR_WAISTCOAT = Object.freeze({ coat: /frock_coat_body(_lod\d+)?$/, waistcoat: /waistcoat[a-z_0-9]*?(_lod\d+)?$/, collar: /shirt_standing_collar(_lod\d+)?$/, from: 2, below: 0.06, reach: 0.16, under: 0.025 });

/** A collar never comes up over the chin: drawn, a lady's high collar stood level all round at
 * the height of the underside of her chin and so covered it from in front. Round the neck, its
 * top is kept `clear` under the head's lowest skin there (the jaw and chin), the band between
 * `band` under that line and the top pressed down into it (texture and all, so lace stays lace). */
export const CHIN = Object.freeze({ pieces: /(collar|stock|neckband|neckcloth|jabot|ruff)(_lod\d+)?$/, clear: 0.012, band: 0.035, sectors: 36 });

/** The underside of the head round the neck, by angle: a function of (x, z) giving the lowest
 * height of the head's skin over that direction, or Infinity. */
function jawOf(body, J) {
  const nk = J.neck_01; if (!nk) return null;
  const C = CHIN, B = bindPositions(body), si = body.geometry.attributes.skinIndex, sw = body.geometry.attributes.skinWeight, bones = body.skeleton.bones;
  const low = new Array(C.sectors).fill(Infinity), sec = (x, z) => Math.floor(((Math.atan2(x - nk[0], z - nk[2]) + Math.PI) / (2 * Math.PI)) * C.sectors) % C.sectors;
  for (let i = 0; i < B.length / 3; i++) {
    let best = 0, bw = -1; for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); if (w > bw) { bw = w; best = si.getComponent(i, k); } }
    if (!/^(head|jaw)/.test(bones[best]?.name ?? '')) continue;
    if (Math.hypot(B[i * 3] - nk[0], B[i * 3 + 2] - nk[2]) > 0.11) continue;
    const k = sec(B[i * 3], B[i * 3 + 2]); low[k] = Math.min(low[k], B[i * 3 + 1]);
  }
  // Evened round the neck (a gap takes its neighbours').
  const sm = low.map((_, k) => { const a = [low[(k + C.sectors - 1) % C.sectors], low[k], low[(k + 1) % C.sectors]].filter(Number.isFinite); return a.length ? Math.min(...a) * 0.5 + a.reduce((x, y) => x + y, 0) / a.length * 0.5 : Infinity; });
  return (x, z) => sm[sec(x, z)];
}

function clearChin(mesh, jaw) {
  const C = CHIN, P = bindPositions(mesh), n = P.length / 3, pos = mesh.geometry.attributes.position, inv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
  // The piece's top by direction, then each point pressed into the band under the line.
  const top = new Map(), keyOf = (i) => Math.round(Math.atan2(P[i * 3], P[i * 3 + 2]) * C.sectors / (2 * Math.PI));
  for (let i = 0; i < n; i++) { const k = keyOf(i); top.set(k, Math.max(top.get(k) ?? -Infinity, P[i * 3 + 1])); }
  // ...and its radius at the band's foot there: what is pressed down comes no further out (a top
  // that flared forward under the chin would stand out as a shelf).
  const foot = new Map();
  for (let i = 0; i < n; i++) { const cap = jaw(P[i * 3], P[i * 3 + 2]) - C.clear; if (!Number.isFinite(cap) || Math.abs(P[i * 3 + 1] - (cap - C.band)) > 0.008) continue; const k = keyOf(i), r = Math.hypot(P[i * 3], P[i * 3 + 2]); (foot.get(k) ?? foot.set(k, []).get(k)).push(r); }
  const footOf = (k) => { const a = foot.get(k) ?? foot.get(k - 1) ?? foot.get(k + 1); if (!a) return Infinity; a.sort((x, y) => x - y); return a[a.length >> 1]; };
  let moved = 0;
  for (let i = 0; i < n; i++) {
    const cap = jaw(P[i * 3], P[i * 3 + 2]) - C.clear, t = top.get(keyOf(i)), y = P[i * 3 + 1];
    if (!Number.isFinite(cap) || !(t > cap)) continue;
    const base = cap - C.band; if (y <= base) continue;
    const ny = base + (y - base) * (cap - base) / Math.max(1e-6, t - base);
    const r = Math.hypot(P[i * 3], P[i * 3 + 2]), rf = footOf(keyOf(i)), k = r > rf + 0.003 ? (rf + 0.003) / r : 1;
    v.set(P[i * 3] * k, ny, P[i * 3 + 2] * k).applyMatrix4(inv); pos.setXYZ(i, v.x, v.y, v.z); moved++;
  }
  if (moved) { pos.needsUpdate = true; mesh.geometry.computeBoundingSphere(); }
  return moved;
}

/** A coat's neckline (its collar's top edge and front corners) faired along its line, every
 * level: drawn, the stand's front corners were notched. */
export const NECK_ITERS = 16;
function fairNeck(coat) {
  const W = weldMeshes([coat]), loops = loopsOf(W);
  if (!loops.length) return 0;
  const mean = (l) => l.reduce((a, g) => a + W.P[g * 3 + 1], 0) / l.length, top = loops.reduce((a, l) => (mean(l) > mean(a) ? l : a));
  const only = new Uint8Array(W.G); for (const g of top) only[g] = 1;
  fairOutline(W, NECK_ITERS, only);
  writeBack(W, null);
  return top.length;
}

/** Refine a body's trims at the near level. Returns { refined: [{ mesh, from, to }] }, stored on
 * root.userData.chicagoTrim. */
export function* refineTrimsSteps(root) {
  const list = [], report = { refined: [], rebuilt: [] };
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.index && o.geometry.attributes.skinWeight) skinned.push(o); });
  const body = skinned.find((m) => m.material?.name === 'skin');
  // Collars kept under the chin, every level.
  if (body) { const J = bindJoints(body), jaw = jawOf(body, J); if (jaw) for (const m of skinned.filter((x) => CHIN.pieces.test(x.name))) { yield; const k = clearChin(m, jaw); if (k) (report.chin ??= []).push({ mesh: m.name, points: k }); } }
  const collars = skinned.filter((m) => COLLAR.test(m.name));
  if (body && collars.length) {
    const B = yield* bodyFieldSteps(body);
    for (const mesh of collars) {
      yield;
      const rank = layerRank(mesh), lod = +((/_lod(\d+)$/.exec(mesh.name) ?? [0, 0])[1]);
      const under = skinned.filter((m) => m !== mesh && m.material !== mesh.material && (m === body || (layerRank(m) > 0 && layerRank(m) <= rank && !COLLAR.test(m.name))));
      const casts = under.map((m) => { const Wm = weldMeshes([m]); return triangleGrid(Wm.P, Wm.tris, 0.03); });
      const r = rebuildCollar(mesh, casts, B, lod);
      if (r) report.rebuilt.push({ mesh: mesh.name, ...r });
    }
  }
  // A frock coat's drawn lapels and facings left out before refining (cut again after).
  const tailor = [];
  for (const lapels of skinned.filter((m) => LAPEL.piece.test(m.name))) {
    const lod = (/_lod(\d+)$/.exec(lapels.name) ?? [0, 0])[1], sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
    const coat = skinned.find((m) => LAPEL.coat.test(m.name) && sfx(m)), silk = skinned.find((m) => LAPEL.silk.test(m.name) && sfx(m));
    if (!coat || !silk) continue;
    yield;
    tailor.push({ lapels, coat, silk, lod: +lod, brk: clearLapels(lapels, silk) });
  }
  // An apron's drawn shoulder frills left out before refining (gathered again after).
  const ruffles = [];
  if (body) { const yc = bindJoints(body).clavicle_l?.[1] - 0.23 || 1.2;
    for (const frills of skinned.filter((m) => RUFFLE.piece.test(m.name))) {
      const lod = (/_lod(\d+)$/.exec(frills.name) ?? [0, 0])[1], sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
      const strap = skinned.find((m) => RUFFLE.strap.test(m.name) && sfx(m)), under = skinned.find((m) => RUFFLE.on.test(m.name) && sfx(m));
      if (!strap || !under) continue;
      yield;
      ruffles.push({ frills, strap, under, lod: +lod, yc, cleared: clearRuffles(frills, yc) });
    } }
  // Lapels kept off the top of the shoulders before they are refined, so the cut's line is faired.
  if (body) {
    const J0 = bindJoints(body);
    for (const pr of PRESSED) for (const piece of skinned.filter((m) => pr.piece.test(m.name))) {
      if (tailor.some((t) => t.lapels === piece)) continue;
      yield;
      const cut = offShoulders(piece, J0);
      if (cut) (report.cut ??= []).push({ mesh: piece.name, triangles: cut });
    }
  }
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.index && o.geometry.attributes.skinWeight && REFINE.test(o.name) && REFINE_LODS.test(o.name) && !Object.keys(o.geometry.morphAttributes ?? {}).length && !o.geometry.userData?.chicagoRebuilt) list.push(o); });
  for (const mesh of list) { yield; const r = subdivide(mesh); report.refined.push({ mesh: mesh.name, ...r }); }
  // Shoulders evened in every coat, every level (before anything takes the coat's rows).
  if (body) { const J = bindJoints(body); for (const coat of skinned.filter((m) => SHOULDERED.test(m.name))) { yield; const n = evenShoulders(coat, J); if (n) (report.shouldered ??= []).push({ mesh: coat.name, points: n }); } }
  // The frock coat's new lapels.
  const tops = new Map();
  for (const t of tailor) { yield; const r = Number.isFinite(t.brk) ? cutLapels(t.coat, t.silk, t.brk, t.lod) : null; if (r) { tops.set(t.lapels, r.tops); (report.lapels ??= []).push({ mesh: t.silk.name, rows: r.rows, points: r.points }); } }
  // A frock coat's collar round the back.
  for (const lapels of skinned.filter((m) => BACK_COLLAR.lapels.test(m.name))) {
    const lod = +((/_lod(\d+)$/.exec(lapels.name) ?? [0, 0])[1]), sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
    const coat = skinned.find((m) => BACK_COLLAR.body.test(m.name) && sfx(m)), shirt = skinned.find((m) => BACK_COLLAR.shirt.test(m.name) && sfx(m));
    if (!coat || !shirt) continue;
    yield;
    const r = buildBackCollar(lapels, coat, shirt, lod, tops.get(lapels)); if (r) (report.collared ??= []).push({ mesh: lapels.name, ...r });
  }
  for (const coat of skinned.filter((m) => SHOULDERED.test(m.name))) { yield; const k = fairNeck(coat); if (k) (report.necklines ??= []).push({ mesh: coat.name, points: k }); }
  // A livery coat's collar hooks faired out and its V filled with a shirt front, every level.
  if (body) for (const coat of skinned.filter((m) => LIVERY.coat.test(m.name))) {
    const lod = +((/_lod(\d+)$/.exec(coat.name) ?? [0, 0])[1]), stock = skinned.find((m) => LIVERY.stock.test(m.name) && (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod);
    yield;
    const k = deburrNeck(coat); if (k) (report.deburred ??= []).push({ mesh: coat.name, points: k });
    if (!stock) continue;
    yield;
    const r = fillShirtFront(coat, stock, body, lod); if (r) (report.shirtFront ??= []).push({ mesh: stock.name, ...r });
  }
  // A frock coat's waistcoat closed at the far levels.
  if (body) for (const coat of skinned.filter((m) => FAR_WAISTCOAT.coat.test(m.name))) {
    const lod = +((/_lod(\d+)$/.exec(coat.name) ?? [0, 0])[1]); if (lod < FAR_WAISTCOAT.from) continue;
    const sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
    const wc = skinned.find((m) => FAR_WAISTCOAT.waistcoat.test(m.name) && sfx(m)), collar = skinned.find((m) => FAR_WAISTCOAT.collar.test(m.name) && sfx(m));
    const brk = tailor.find((t) => t.coat === coat)?.brk;
    if (!wc || !collar || !Number.isFinite(brk)) continue;
    yield;
    const r = fillFront(coat, wc, body, lod, brk - FAR_WAISTCOAT.below, frontBottom(collar) + LIVERY.above, FAR_WAISTCOAT.reach, FAR_WAISTCOAT.under); if (r) (report.waistcoatClosed ??= []).push({ mesh: wc.name, ...r });
  }
  // A frock coat's front buttons, and seams in every coat at the near level.
  for (const coat of skinned.filter((m) => FRONT_BUTTONS.coat.test(m.name))) {
    const lod = +((/_lod(\d+)$/.exec(coat.name) ?? [0, 0])[1]); if (lod > 1) continue;
    const sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
    const lapels = skinned.find((m) => FRONT_BUTTONS.lapels.test(m.name) && sfx(m)), silk = skinned.find((m) => FRONT_BUTTONS.silk.test(m.name) && sfx(m));
    if (!lapels || !silk) continue;
    yield;
    const r = buildFrontButtons(coat, lapels, silk, lod, tailor.find((t) => t.lapels === lapels)?.brk ?? null); if (r) (report.buttoned ??= []).push({ mesh: silk.name, ...r });
  }
  if (body) for (const coat of skinned.filter((m) => SEAMED.test(m.name) && !Object.keys(m.geometry.morphAttributes ?? {}).length)) {
    yield;
    const r = buildSeams(coat, body); if (r) (report.seamed ??= []).push({ mesh: coat.name, ...r });
  }
  for (const r of ruffles) { yield; const k = buildRuffles(r.frills, r.strap, r.under, r.lod, r.yc, r.cleared); if (k) (report.ruffled ??= []).push({ mesh: r.frills.name, ...k }); }
  // Pressed pieces bound to the coat under them, every level.
  for (const pr of PRESSED) for (const piece of skinned.filter((m) => pr.piece.test(m.name) && !tailor.some((t) => t.lapels === m))) {
    const lod = (/_lod(\d+)$/.exec(piece.name) ?? [0, 0])[1], sfx = (m) => (/_lod(\d+)$/.exec(m.name) ?? [0, 0])[1] == lod;
    const on = skinned.find((m) => pr.on.test(m.name) && sfx(m)); if (!on) continue;
    yield;
    (report.pressed ??= []).push({ mesh: piece.name, points: weightsFrom(piece, on) });
  }
  root.userData.chicagoTrim = report;
  return report;
}
export function refineTrims(root) { const s = refineTrimsSteps(root); for (;;) { const n = s.next(); if (n.done) return n.value; } }
void bindPositions;
