// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-layover.js — what is worn over lies over (T-3553, round 7).
 *
 * The last word on the order of the layers, for every body at every level. Each piece of
 * clothing is drawn on its own, and wherever a piece worn under another comes out in front of
 * it (a waistcoat's edge through a coat, a shirt collar through a coat collar, a coat through
 * the crossbelts over it, the body's shoulder through a sleeve) the two surfaces cross and the
 * eye sees a torn edge: the one in front changes from point to point along a ragged line.
 * Here the piece worn over is moved out, at each of its points where the piece under it is in
 * front, to lie GAP_M over it, and the move is eased into the cloth round it over EASE_M so
 * the cloth rises over what is under it instead of being dented. Moves larger than REACH_M are
 * left alone (the two were not meant to meet: a lapel turned back over a coat's front).
 *
 * Which piece is over which: the drape's layer ranks (skin, shirts, lower garments, waistcoats,
 * coats; human-drape.js layerRank), with the riders (belts, crossbelts, straps, sashes) over all
 * of them, braces over the shirt and trousers but under a waistcoat or coat, other accessories
 * (a cartridge box, a bag, a chain) over the coats, neckwear over the shirt and waistcoat but
 * under a coat, and a shirt's tails over the trousers they hang outside. Pieces of one rank
 * are left to each other. A rider takes the skin weights of the cloth it lies on (blended over
 * the triangle under it), so it goes where that cloth goes as the figure moves.
 *
 * Runs after settleOnBody and before bindLayers and cullHidden, once per loaded body at every
 * level. Positions (and a rider's weights) only; no point, face or draw call is added.
 * Returns { laid: [{ mesh, over, points, max }], evened: [{ mesh, points }] } on
 * root.userData.chicagoLayover.
 */
import { kit, layerRank, OUTSIDE, LAMBDA, MU } from './human-drape.js';

const { weldMeshes, triangleGrid, graphNormals, writeBack, pointGrid } = kit;

/** Pieces worn over the cloth they lie on, whatever its rank. */
export const RIDER = /(cross_?belts?|_belt|belts?_|sash|_straps?(_|$)|sling|bandolier)/;
/** Braces are worn over the shirt and the trousers they hold up, under a waistcoat or a coat. */
export const BRACES = /(braces|suspenders)/;
/** Worn on the skin, under a sleeve or a cuff: gloves, mittens; hats and shoes keep their rank. */
export const ON_SKIN = /(glove|mitten|mitt|_hat|cap|bonnet|shoe|boot|stocking|sock)/;
/** Neckwear: a tie, a cravat, a stock lies over the shirt front and the waistcoat, under a coat. */
export const NECK = /(_tie(_|$)|four_in_hand|cravat|neckcloth|kerchief|stock(?!ing)|jabot|_bow(_|$))/;
/** The room left between a piece and what it is worn over; how far the cloth round a lifted
 * point eases up with it; the largest lift made; the passes (a lift can meet a third piece). */
export const GAP_M = 0.0015, EASE_M = 0.02, REACH_M = 0.012, PASSES = 2;
const LOOK = /^(garment_(upper|lower|outer)|accessory|footwear)__/;
const opaque = (m) => !m.material?.transparent && !(m.material?.alphaTest > 0) && m.material?.opacity !== 0;

/** The order a piece is drawn in: higher lies over lower. */
export function overRank(mesh) {
  const name = (mesh.name ?? '').replace(/_lod\d+$/, '');
  if (mesh.material?.name === 'skin') return 0;
  if (!LOOK.test(mesh.material?.name ?? '')) return -1;
  if (BRACES.test(name)) return 2.6;
  if (RIDER.test(name) && !/(frill|ruffle)/.test(name)) return 5;   // a strap's frill is laid by its own pass (human-trim.js)
  if (NECK.test(name)) return 3.5;   // over the shirt and the waistcoat's front, under a coat
  if (/^accessory__/.test(mesh.material?.name ?? '') && !ON_SKIN.test(name)) return 4.5;   // boxes, bags, chains: worn outside
  const r = layerRank(mesh);
  if (r === 1 && OUTSIDE.test(mesh.name)) return 2.5;   // shirt tails over the trousers
  return r;
}

/** Outline evening: every garment piece's open edges (a hem, a collar's edge, a belt's sides)
 * are relaxed along their line in the cloth's plane, OUTLINE_ITERS Taubin pairs, so an edge the
 * exporter left sawing from point to point runs straight; points shared with another piece (a
 * collar sewn to a coat) stay where they are. */
export const OUTLINE_ITERS = 6, SHARED_M = 0.0008;

function evenOutline(W, fixed) {
  const { P, G, edgeNb } = W;
  let moved = 0;
  for (let it = 0; it < OUTLINE_ITERS * 2; it++) {
    const N = graphNormals(P, W.tris, G), w = it % 2 ? MU : LAMBDA, Q = Float64Array.from(P);
    for (let g = 0; g < G; g++) {
      const l = edgeNb[g]; if (l.length !== 2 || fixed[g]) continue;
      let cx = (P[l[0] * 3] + P[l[1] * 3]) / 2 - P[g * 3], cy = (P[l[0] * 3 + 1] + P[l[1] * 3 + 1]) / 2 - P[g * 3 + 1], cz = (P[l[0] * 3 + 2] + P[l[1] * 3 + 2]) / 2 - P[g * 3 + 2];
      const o = cx * N[g * 3] + cy * N[g * 3 + 1] + cz * N[g * 3 + 2]; cx -= o * N[g * 3]; cy -= o * N[g * 3 + 1]; cz -= o * N[g * 3 + 2];
      Q[g * 3] += w * cx; Q[g * 3 + 1] += w * cy; Q[g * 3 + 2] += w * cz;
      if (it === 0) moved++;
    }
    P.set(Q);
  }
  return moved;
}

/** Ease a move into the cloth round it: each point moves as far as the farthest-moved point near
 * it less a slope (that point's move over EASE_M per metre along the cloth), so a move fades
 * out over EASE_M. */
function easeOut(W, move) {
  const ease = Float64Array.from(move), rate = new Float64Array(W.G);
  for (let g = 0; g < W.G; g++) rate[g] = move[g] / EASE_M;
  for (let it = 0; it < 24; it++) {
    let changed = false;
    for (let g = 0; g < W.G; g++) {
      for (const h of W.nb[g]) {
        if (!(ease[h] > 0)) continue;
        const e = Math.hypot(W.P[g * 3] - W.P[h * 3], W.P[g * 3 + 1] - W.P[h * 3 + 1], W.P[g * 3 + 2] - W.P[h * 3 + 2]);
        const v = ease[h] - rate[h] * e;
        if (v > ease[g] + 1e-7) { ease[g] = v; rate[g] = rate[h]; changed = true; }
      }
    }
    if (!changed) break;
  }
  return ease;
}

export function* layOverSteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.position && o.geometry.index && o.visible !== false && overRank(o) >= 0 && opaque(o)) skinned.push(o); });
  const report = { laid: [], evened: [] };
  root.userData.chicagoLayover = report;
  if (skinned.length < 2) return report;
  // Outlines first.
  const garments = skinned.filter((m) => overRank(m) > 0);
  const grids = new Map(skinned.map((o) => { const P = kit.bindPositions(o); return [o, { P, near: pointGrid(P, 0.01) }]; }));
  for (const mesh of garments) {
    yield;
    const W = weldMeshes([mesh]);
    const fixed = new Uint8Array(W.G);
    for (let g = 0; g < W.G; g++) {
      if (W.edgeNb[g].length !== 2) continue;
      const x = W.P[g * 3], y = W.P[g * 3 + 1], z = W.P[g * 3 + 2];
      for (const [o, { P, near }] of grids) {
        if (o === mesh) continue;
        const h = near(x, y, z, 1);
        if (h >= 0 && Math.hypot(P[h * 3] - x, P[h * 3 + 1] - y, P[h * 3 + 2] - z) < SHARED_M) { fixed[g] = 1; break; }
      }
    }
    const moved = evenOutline(W, fixed);
    if (!moved) continue;
    writeBack(W, null);
    report.evened.push({ mesh: mesh.name, points: moved });
  }
  // Riders and braces only: lifting a garment's own edge over the cloth under it (a waistcoat's
  // over a shirt) saws the edge where it crosses, so garments are left to bindLayers and cullHidden.
  const strap = (m) => overRank(m) >= 4.5 || BRACES.test(m.name ?? '');
  const order = skinned.filter(strap).sort((a, b) => overRank(a) - overRank(b));
  for (let pass = 0; pass < PASSES; pass++) {
    for (const mesh of order) {
      yield;
      const rank = overRank(mesh);
      const under = skinned.filter((u) => u !== mesh && overRank(u) < rank);
      if (!under.length) continue;
      const W = weldMeshes([mesh]), N = graphNormals(W.P, W.tris, W.G);
      const casts = under.map((u) => { const U = weldMeshes([u]); return { u, U, cast: triangleGrid(U.P, U.tris, 0.03), N: graphNormals(U.P, U.tris, U.G), near: pointGrid(U.P, 0.02) }; });
      yield;
      // How far each point must rise: the farthest any piece under it comes out in front.
      const lift = new Float64Array(W.G), on = new Array(W.G).fill(null);
      let any = 0;
      for (let g = 0; g < W.G; g++) {
        if ((g & 1023) === 1023) yield;
        const nx = N[g * 3], ny = N[g * 3 + 1], nz = N[g * 3 + 2];
        // start just behind the point, look out along its normal
        const x = W.P[g * 3] - nx * GAP_M, y = W.P[g * 3 + 1] - ny * GAP_M, z = W.P[g * 3 + 2] - nz * GAP_M;
        for (const c of casts) {
          const d = c.cast(x, y, z, nx, ny, nz, REACH_M + GAP_M);
          if (!Number.isFinite(d)) continue;
          // Only from behind: the point is inside the piece under it (the ray leaves that piece
          // through its outer face). A ray that meets a face from the front is a lining facing
          // the body, or a piece under it seen from outside: as it should be.
          const hx = x + nx * d, hy = y + ny * d, hz = z + nz * d, h = c.near(hx, hy, hz);
          if (h < 0 || c.N[h * 3] * nx + c.N[h * 3 + 1] * ny + c.N[h * 3 + 2] * nz <= 0.2) continue;
          // the piece under is in front of this point by d - GAP_M: rising d leaves it GAP_M over it
          if (d > lift[g]) { lift[g] = d; on[g] = c; }
        }
        if (lift[g] > 0) any++;
      }
      if (!any) continue;
      const ease = easeOut(W, lift);
      let points = 0, max = 0;
      for (let g = 0; g < W.G; g++) {
        const d = ease[g];
        if (!(d > 0)) continue;
        W.P[g * 3] += N[g * 3] * d; W.P[g * 3 + 1] += N[g * 3 + 1] * d; W.P[g * 3 + 2] += N[g * 3 + 2] * d;
        points++; if (d > max) max = d;
      }
      writeBack(W, null);
      // A rider goes where the cloth it lies on goes.
      if (rank === 5 || BRACES.test(mesh.name)) rideOn(mesh, W, N, casts);
      const over = [...new Set(on.filter(Boolean).map((c) => c.u.name))];
      const prior = report.laid.find((r) => r.mesh === mesh.name);
      if (prior) { prior.points += points; prior.max = Math.max(prior.max, max); for (const o of over) if (!prior.over.includes(o)) prior.over.push(o); }
      else report.laid.push({ mesh: mesh.name, over, points, max });
    }
  }
  return report;
}

/** A rider's points within reach of the cloth under them take that cloth's weights there. */
function rideOn(mesh, W, N, casts) {
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  if (!si || !sw) return;
  const names = mesh.skeleton.bones.map((b) => b.name), local = new Map(names.map((n, i) => [n, i]));
  const full = sw.normalized ? 255 : 1;
  for (let g = 0; g < W.G; g++) {
    const nx = N[g * 3], ny = N[g * 3 + 1], nz = N[g * 3 + 2];
    let best = Infinity, bc = null;
    for (const c of casts) {
      if (c.u.material?.name === 'skin') continue;
      const d = c.cast(W.P[g * 3] + nx * 0.002, W.P[g * 3 + 1] + ny * 0.002, W.P[g * 3 + 2] + nz * 0.002, -nx, -ny, -nz, 0.02);
      if (d < best) { best = d; bc = c; }
    }
    if (!bc) continue;
    const p = [W.P[g * 3] - nx * (best - 0.002), W.P[g * 3 + 1] - ny * (best - 0.002), W.P[g * 3 + 2] - nz * (best - 0.002)];
    const w = weightsAt(bc, p); if (!w) continue;
    const top = [...w].filter(([b]) => local.has(b)).sort((a, b) => b[1] - a[1]).slice(0, 4);
    const sum = top.reduce((a, [, x]) => a + x, 0); if (!(sum > 0)) continue;
    let q = top.map(([b, x]) => [local.get(b), x / sum]);
    if (full === 255) { const ints = q.map(([, x]) => Math.floor(x * 255)); let rest = 255 - ints.reduce((a, b) => a + b, 0); for (let k = 0; rest > 0; k = (k + 1) % ints.length, rest--) ints[k]++; q = q.map(([b], k) => [b, ints[k] / 255]); }
    for (const [part, i] of W.members[g]) { void part; for (let k = 0; k < 4; k++) { si.setComponent(i, k, q[k] ? q[k][0] : 0); sw.setComponent(i, k, q[k] ? q[k][1] : 0); } }
  }
  si.needsUpdate = true; sw.needsUpdate = true;
}

/** The cloth's weights (by bone name) at a point on it, blended over the triangle it lies on. */
function weightsAt(c, p) {
  const U = c.U;
  if (!c.tri) { c.tri = Array.from({ length: U.G }, () => []); for (let t = 0; t < U.tris.length; t += 3) for (let k = 0; k < 3; k++) c.tri[U.tris[t + k]].push(t); }
  const g = c.near(p[0], p[1], p[2]); if (g < 0) return null;
  let best = null, bestOut = Infinity;
  for (const t of c.tri[g]) {
    const [a, b, d] = [U.tris[t], U.tris[t + 1], U.tris[t + 2]].map((q) => [U.P[q * 3], U.P[q * 3 + 1], U.P[q * 3 + 2]]);
    const v0 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v1 = [d[0] - a[0], d[1] - a[1], d[2] - a[2]], v2 = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
    const d00 = v0[0] * v0[0] + v0[1] * v0[1] + v0[2] * v0[2], d01 = v0[0] * v1[0] + v0[1] * v1[1] + v0[2] * v1[2], d11 = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2];
    const d20 = v2[0] * v0[0] + v2[1] * v0[1] + v2[2] * v0[2], d21 = v2[0] * v1[0] + v2[1] * v1[1] + v2[2] * v1[2], den = d00 * d11 - d01 * d01 || 1e-12;
    const y = (d11 * d20 - d01 * d21) / den, z = (d00 * d21 - d01 * d20) / den, x = 1 - y - z, out = -Math.min(0, x, y, z);
    if (out < bestOut) { bestOut = out; best = [[U.tris[t], x], [U.tris[t + 1], y], [U.tris[t + 2], z]]; }
  }
  if (!best) return null;
  const u = c.u, si = u.geometry.attributes.skinIndex, sw = u.geometry.attributes.skinWeight, names = u.skeleton.bones.map((b) => b.name);
  const acc = new Map();
  for (const [q, w0] of best) {
    const w = Math.min(1, Math.max(0, w0)), [, i] = U.members[q][0];
    for (let k = 0; k < 4; k++) { const x = sw.getComponent(i, k); if (x > 0) { const b = names[si.getComponent(i, k)]; acc.set(b, (acc.get(b) ?? 0) + w * x); } }
  }
  return acc;
}

export const layOver = (root) => { const s = layOverSteps(root); for (;;) { const n = s.next(); if (n.done) return n.value; } };
