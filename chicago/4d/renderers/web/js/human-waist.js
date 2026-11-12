// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-waist.js — a belt, and the cloth it holds, sit ON the body at the waist (T-3553).
 *
 * Kevin, 2026-11-12, walking the 1812 camps: "in 1812 the native belts do not wrap tightly,
 * they float as well as their bottom pants float around the waist". The Potawatomi man's
 * body (tools/human_potawatomi_man_1812.py) builds its belt round the white blanket wrapped
 * at the waist, and the blanket on a convex section 3 cm out from the body. More than half
 * the men of the camp set the blanket aside in the August heat (dress_1812_native.json hides
 * it), and their belt was left standing in the air where the blanket had been. Under it the
 * shirt's skirt (the shirt below the waist) began a couple of centimetres wider than the
 * shirt above it, a ledge all round. And each layer moved by its own bones: the shirt with
 * the spine, the skirt and blanket with the pelvis alone, the belt with the nearest skin
 * including the thighs. Turning and walking pulled them apart into hoops.
 *
 * Here, once per loaded body (before any figure is cloned from it, so every figure shares
 * the result and nothing is per person), the waist is refitted as one stack, the way a belt
 * pulls the cloth under it into its own line:
 *   - the cinch: round the shirt's own trunk (never its sleeves), the widest it reaches from
 *     CINCH_BELOW_M under the belt to the belt's top, angle by angle;
 *   - the skirt is on the cinch (EASE.skirt out) there, then drawn in to the shirt above it,
 *     easing back to its own cut over BLEND_M below HOLD_M from its top edge;
 *   - the blanket over the skirt (EASE.wrap more), the same way; where a simplified level
 *     runs one long panel from the cinch to a row well below, that row is drawn in until the
 *     panel passes under the belt, but never into the skirt;
 *   - the belt keeps its own section, roll and edges and is moved onto the cinch, outside
 *     the blanket (EASE.belt), so it is tight on the blanket of a man who wears one and a few
 *     millimetres off the shirt of a man who does not (the blanket's thickness);
 *   - at the waist every layer takes the skin weights of the shirt there, fading back to its
 *     own over BLEND_M, so the stack turns and walks as one.
 * Nothing below the blend moves. tools/test_human_waist.mjs measures it on all four levels,
 * standing, on the walk and at idle: the belt was 4.2 to 4.7 cm off the shirt, now about 1 cm
 * at worst on the full body (1.5 to 1.7 cm on the simplified ones), a few millimetres most of
 * the way round.
 *
 * Cost: positions and skin weights rewritten in place on a few thousand vertices per level,
 * once per parse (a few milliseconds). No new geometry, texture, draw call or program.
 * A reconstructed fit, as the garments' own cut and ease are (liberty L418 and the dress's).
 */
import * as THREE from 'three';
import { restMatrix } from './human-skin.js';

/** Which bodies have a belted waist, by their meshes' piece names. */
export const WAISTS = Object.freeze([
  Object.freeze({ asset: 'potawatomi_man_1812', shirt: 'trade_shirt', skirt: 'trade_shirt_skirt',
    wraps: Object.freeze(['blanket_wrap', 'blanket_stripes']), belt: 'leather_belt' }),
]);
/** Clearances, metres: skirt over the shirt, blanket over the skirt, belt over the blanket (or the skirt, by that much more). */
export const EASE = Object.freeze({ skirt: .003, wrap: .003, belt: .0025 });
/** Held fully drawn in from a layer's top edge down HOLD_M (the belt's height and a little), then easing back over BLEND_M. */
export const HOLD_M = .05, BLEND_M = .07;
/** The cinch runs this far below the belt (to the next row of the cloth under it); a cloth row is about ROW_M apart. */
export const CINCH_BELOW_M = .03, ROW_M = .05;
/** The blanket is held on the cinch no further down than the skirt beneath it. */
export const WRAP_BELOW_M = 0;
const BINS = 96, DY = .005;

const piece = (mesh, name) => new RegExp(`(^|_)${name}(_lod\\d+)?$`).test(mesh.name);
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const angleOf = (x, z) => Math.atan2(x, z);
const binOf = (a) => ((Math.floor(((a + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;

/** A mesh's positions in the body's bind pose, metres, relative to `root`. */
function bindPoints(mesh, root) {
  const R = restMatrix(mesh, root), p = mesh.geometry.attributes.position, v = new THREE.Vector3();
  const out = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(R); out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z; }
  return { R, pts: out, n: p.count };
}

/** Points over a mesh's surface (its vertices and a grid across each triangle), so a sparse
 * shell still has a point in every bin its cloth crosses. */
function surface(mesh, set, skip = null) {
  const idx = mesh.geometry.index, P = set.pts, out = [], N = 4;
  const tri = idx ? idx.count / 3 : set.n / 3;
  for (let f = 0; f < tri; f++) {
    const a = idx ? idx.getX(f * 3) : f * 3, b = idx ? idx.getX(f * 3 + 1) : f * 3 + 1, c = idx ? idx.getX(f * 3 + 2) : f * 3 + 2;
    if (skip && (skip[a] || skip[b] || skip[c])) continue;
    for (let i = 0; i <= N; i++) for (let j = 0; j <= N - i; j++) {
      const u = i / N, v = j / N, w = 1 - u - v;
      for (let k = 0; k < 3; k++) out.push(P[a * 3 + k] * u + P[b * 3 + k] * v + P[c * 3 + k] * w);
    }
  }
  return { pts: Float32Array.from(out), n: out.length / 3 };
}

/** The vertices a mesh's arms move more than its trunk does (a shirt's sleeves): the waist is
 * the body's, and a cuff hanging beside the hip is not under the belt. */
const ARM = /^(clavicle|upperarm|lowerarm|hand|thumb|index|middle|ring|pinky)/;
function sleeves(weights) {
  return weights.map((m) => { let arm = 0, all = 0; for (const [b, w] of m) { all += w; if (ARM.test(b)) arm += w; } return all > 0 && arm / all > .3; });
}

/** How far a set of points reaches from the body's axis, by height and angle; empty bins filled. */
function reach(sets, fill = true) {
  let lo = Infinity, hi = -Infinity;
  for (const s of sets) for (let i = 0; i < s.n; i++) { const y = s.pts[i * 3 + 1]; lo = Math.min(lo, y); hi = Math.max(hi, y); }
  if (!(hi > lo)) return null;
  const rows = Math.max(1, Math.ceil((hi - lo) / DY) + 1), t = new Float32Array(rows * BINS);
  for (const s of sets) for (let i = 0; i < s.n; i++) {
    const x = s.pts[i * 3], y = s.pts[i * 3 + 1], z = s.pts[i * 3 + 2];
    const k = Math.min(rows - 1, Math.floor((y - lo) / DY)) * BINS + binOf(angleOf(x, z));
    t[k] = Math.max(t[k], Math.hypot(x, z));
  }
  for (let r = 0; r < rows && fill; r++) {   // around each row: an empty bin takes its nearest filled ones
    const row = t.subarray(r * BINS, (r + 1) * BINS), had = Array.from(row, (v) => v > 0);
    if (!had.some(Boolean)) continue;
    for (let k = 0; k < BINS; k++) {
      if (had[k]) continue;
      let a = 1; while (!had[(k - a + BINS) % BINS]) a++;
      let b = 1; while (!had[(k + b) % BINS]) b++;
      row[k] = (row[(k - a + BINS) % BINS] * b + row[(k + b) % BINS] * a) / (a + b);
    }
  }
  for (let r = 0; r < rows && fill; r++) {   // an empty row takes its nearest filled row
    if (t[r * BINS] > 0) continue;
    for (let d = 1; d < rows; d++) {
      const s = [r - d, r + d].find((q) => q >= 0 && q < rows && t[q * BINS] > 0);
      if (s !== undefined) { t.copyWithin(r * BINS, s * BINS, (s + 1) * BINS); break; }
    }
  }
  return {
    lo, hi,
    at(a, y) {
      const r = Math.min(rows - 1, Math.max(0, Math.floor((Math.min(hi, Math.max(lo, y)) - lo) / DY)));
      const f = ((a + Math.PI) / (2 * Math.PI)) * BINS - .5, k0 = ((Math.floor(f) % BINS) + BINS) % BINS, u = f - Math.floor(f);
      const p = t[r * BINS + k0], q = t[r * BINS + (k0 + 1) % BINS];
      if (!fill) return Math.max(p, q);   // unfilled: what is there, and nothing across a gap
      return p * (1 - u) + q * u;
    },
  };
}

/** The skin weights of the nearest of `pool`'s points (bind metres) to (x, y, z). */
function nearestWeights(pool, x, y, z) {
  let best = -1, d = Infinity;
  for (let i = 0; i < pool.n; i++) {
    const dx = pool.pts[i * 3] - x, dy = pool.pts[i * 3 + 1] - y, dz = pool.pts[i * 3 + 2] - z;
    const e = dx * dx + dy * dy + dz * dz;
    if (e < d) { d = e; best = i; }
  }
  return best < 0 ? null : pool.w[best];
}

/** A mesh's four influences per vertex, as bone names (meshes need not share one skeleton). */
function influences(mesh) {
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight, bones = mesh.skeleton?.bones;
  if (!si || !sw || !bones) return null;
  const out = [];
  for (let i = 0; i < si.count; i++) {
    const m = new Map();
    for (let c = 0; c < 4; c++) { const w = sw.getComponent(i, c); if (w > 0) { const b = bones[si.getComponent(i, c)]?.name; if (b) m.set(b, (m.get(b) ?? 0) + w); } }
    out.push(m);
  }
  return out;
}

/** Write `(1-t)·own + t·to` as this vertex's four strongest influences. */
function blendWeights(mesh, i, own, to, t) {
  if (!to || t <= 0) return;
  const mix = new Map();
  for (const [b, w] of own) mix.set(b, (mix.get(b) ?? 0) + w * (1 - t));
  for (const [b, w] of to) mix.set(b, (mix.get(b) ?? 0) + w * t);
  const index = new Map(mesh.skeleton.bones.map((b, k) => [b.name, k]));
  const top = [...mix].filter(([b]) => index.has(b)).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const sum = top.reduce((s, q) => s + q[1], 0);
  if (!(sum > 0)) return;
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  for (let c = 0; c < 4; c++) {
    si.setComponent(i, c, top[c] ? index.get(top[c][0]) : 0);
    sw.setComponent(i, c, top[c] ? top[c][1] / sum : 0);
  }
  si.needsUpdate = sw.needsUpdate = true;
}

/** Move vertex i of a mesh to bind point (x, y, z), through the inverse of its rest matrix. */
function place(mesh, inv, i, x, y, z) {
  const v = new THREE.Vector3(x, y, z).applyMatrix4(inv);
  mesh.geometry.attributes.position.setXYZ(i, v.x, v.y, v.z);
  mesh.geometry.attributes.position.needsUpdate = true;
}

/**
 * Refit every belted waist under `root` (a parsed body, before it is cloned). Safe to call
 * twice: a fitted body is marked. Returns what it did, for a test or a probe, or null.
 */
export function fitWaist(root) {
  if (!root || root.userData.chicagoWaistFit) return root?.userData?.chicagoWaistFit ?? null;
  const meshes = [];
  root.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); });
  for (const spec of WAISTS) {
    const find = (name) => meshes.find((m) => piece(m, name) && m.name.startsWith(spec.asset));
    const shirt = find(spec.shirt), skirt = find(spec.skirt), belt = find(spec.belt);
    const wraps = spec.wraps.map(find).filter(Boolean);
    if (!shirt || !skirt || !belt) continue;
    root.updateMatrixWorld(true);
    const S = bindPoints(shirt, root), K = bindPoints(skirt, root), B = bindPoints(belt, root);
    const W = wraps.map((m) => ({ mesh: m, ...bindPoints(m, root) }));
    const shirtW = influences(shirt), skirtW = influences(skirt), beltW = influences(belt);
    if (!shirtW || !skirtW || !beltW) continue;
    const sleeve = sleeves(shirtW), torso = surface(shirt, S, sleeve);
    const shirtR = reach([torso]);
    let skirtTop = -Infinity; for (let i = 0; i < K.n; i++) skirtTop = Math.max(skirtTop, K.pts[i * 3 + 1]);
    // The shirt's weights round the waist only: the pool the nearest-point search walks.
    const pool = { pts: [], w: [] };
    for (let i = 0; i < S.n; i++) {
      const y = S.pts[i * 3 + 1];
      if (!sleeve[i] && y > skirtTop - HOLD_M - BLEND_M - .03 && y < skirtTop + .06) { pool.pts.push(S.pts[i * 3], y, S.pts[i * 3 + 2]); pool.w.push(shirtW[i]); }
    }
    pool.n = pool.w.length;
    if (!pool.n) continue;
    const report = { asset: spec.asset, skirt: 0, wraps: 0, belt: 0, widest_gap_before_m: 0 };
    // The cinch: under the belt, and a row of cloth below it, every layer is one upright ring
    // round the shirt's widest there (a belt pulls the cloth beneath it into its own line).
    let blo = Infinity, bhi = -Infinity;
    for (let i = 0; i < B.n; i++) { blo = Math.min(blo, B.pts[i * 3 + 1]); bhi = Math.max(bhi, B.pts[i * 3 + 1]); }
    const c0 = blo - CINCH_BELOW_M, c1 = bhi + .002;
    const ring = new Float32Array(BINS);
    for (let k = 0; k < BINS; k++) {
      const a = ((k + .5) / BINS) * 2 * Math.PI - Math.PI;
      for (let y = c0; y <= c1 + 1e-6; y += DY / 2) ring[k] = Math.max(ring[k], shirtR.at(a, y));
    }
    const cinch = (a) => { const f = ((a + Math.PI) / (2 * Math.PI)) * BINS - .5, k0 = ((Math.floor(f) % BINS) + BINS) % BINS, u = f - Math.floor(f); return ring[k0] * (1 - u) + ring[(k0 + 1) % BINS] * u; };
    const inCinch = (y, below = 0) => y >= c0 - below - 1e-6 && y <= c1 + .01;
    // 1. The skirt's top: cinched under the belt, then drawn in to the shirt above it, easing
    // back to its own cut over BLEND_M below HOLD_M.
    const kinv = K.R.clone().invert();
    for (let i = 0; i < K.n; i++) {
      const x = K.pts[i * 3], y = K.pts[i * 3 + 1], z = K.pts[i * 3 + 2];
      const t = smooth((y - (skirtTop - HOLD_M - BLEND_M)) / BLEND_M);
      if (t <= 0) continue;
      const a = angleOf(x, z), r = Math.hypot(x, z);
      const target = inCinch(y) ? cinch(a) + EASE.skirt : Math.max(cinch(a) + EASE.skirt, shirtR.at(a, Math.max(shirtR.lo + .005, y)) + EASE.skirt);
      const r2 = inCinch(y) ? target : r > target ? r - (r - target) * t : r;
      if (Math.abs(r2 - r) > 1e-6) { const g = r2 / r; K.pts[i * 3] = x * g; K.pts[i * 3 + 2] = z * g; place(skirt, kinv, i, x * g, y, z * g); report.skirt++; }
      blendWeights(skirt, i, skirtW[i], nearestWeights(pool, x, y, z), t);
    }
    const layer = reach([torso, surface(skirt, K)]);   // the shirt and the fitted skirt
    // The cloth from y down to the next row (and half a row up): a point is held clear of all
    // of it, so the flat panel between two rows never cuts into the skirt beneath.
    const below = (a, y) => { let m = 0; for (let yy = y - ROW_M; yy <= y + ROW_M / 2; yy += DY / 2) m = Math.max(m, layer.at(a, yy)); return m; };
    // 2. The blanket's top: on the cinch over the skirt, then over the skirt below it.
    for (const w of W) {
      const winv = w.R.clone().invert(), own = influences(w.mesh);
      let top = -Infinity; for (let i = 0; i < w.n; i++) top = Math.max(top, w.pts[i * 3 + 1]);
      for (let i = 0; i < w.n; i++) {
        const x = w.pts[i * 3], y = w.pts[i * 3 + 1], z = w.pts[i * 3 + 2];
        const t = smooth((y - (top - HOLD_M - BLEND_M)) / BLEND_M);
        if (t <= 0) continue;
        const a = angleOf(x, z), r = Math.hypot(x, z);
        const held = inCinch(y, WRAP_BELOW_M), target = held ? cinch(a) + EASE.skirt + EASE.wrap : below(a, y) + EASE.wrap;
        const r2 = held ? target : r > target ? r - (r - target) * t : r;
        if (Math.abs(r2 - r) > 1e-6) { const g = r2 / r; w.pts[i * 3] = x * g; w.pts[i * 3 + 2] = z * g; place(w.mesh, winv, i, x * g, y, z * g); report.wraps++; }
        if (own) blendWeights(w.mesh, i, own[i], nearestWeights(pool, x, y, z), t);
      }
      // A simplified level may run one long panel from the cinch straight to a row well below the
      // belt; its far end is drawn in until the panel passes under the belt's lower edge.
      const idx = w.mesh.geometry.index;
      const heldAt = (i) => inCinch(w.pts[i * 3 + 1], WRAP_BELOW_M);
      for (let pass = 0; pass < 2 && idx; pass++) for (let f = 0; f < idx.count; f += 3) {
        const tri = [idx.getX(f), idx.getX(f + 1), idx.getX(f + 2)];
        for (const u of tri) for (const v of tri) {
          if (u === v || !heldAt(u) || heldAt(v)) continue;
          const yu = w.pts[u * 3 + 1], yv = w.pts[v * 3 + 1];
          if (!(yu > blo && yv < blo)) continue;
          const ru = Math.hypot(w.pts[u * 3], w.pts[u * 3 + 2]), xv = w.pts[v * 3], zv = w.pts[v * 3 + 2], rv = Math.hypot(xv, zv);
          const at = (yu - blo) / (yu - yv), room = cinch(angleOf(xv, zv)) + EASE.skirt + EASE.wrap;
          // ...but never into the skirt beneath it there.
          const most = Math.max(ru + (room - ru) / at, below(angleOf(xv, zv), yv) + EASE.wrap);
          if (rv > most && most > 0) { const g = most / rv; w.pts[v * 3] = xv * g; w.pts[v * 3 + 2] = zv * g; place(w.mesh, winv, v, xv * g, yv, zv * g); report.wraps++; }
        }
      }
    }
    // 3. The belt: its own section (its roll and edges kept), moved onto the cinch, outside
    // the blanket's few millimetres whether or not it is worn.
    const base = new Float32Array(BINS).fill(Infinity);
    for (let i = 0; i < B.n; i++) { const k = binOf(angleOf(B.pts[i * 3], B.pts[i * 3 + 2])); base[k] = Math.min(base[k], Math.hypot(B.pts[i * 3], B.pts[i * 3 + 2])); }
    const binv = B.R.clone().invert(), lift = EASE.skirt + EASE.wrap + EASE.belt;
    // ...and outside the blanket's cloth over its height wherever a simplified level's long panel
    // runs out past the cinch (the blanket is drawn as it is fitted, between its vertices too).
    const wrapR = W.length ? reach(W.map((w) => surface(w.mesh, w)), false) : null;
    const over = new Float32Array(BINS);
    for (let k = 0; k < BINS; k++) {
      const a = ((k + .5) / BINS) * 2 * Math.PI - Math.PI;
      over[k] = cinch(a) + lift;
      if (wrapR) for (let y = blo; y <= bhi + 1e-6; y += DY / 2) if (y >= wrapR.lo && y <= wrapR.hi) over[k] = Math.max(over[k], wrapR.at(a, y) + EASE.belt);
    }
    const onto = (a) => { const f = ((a + Math.PI) / (2 * Math.PI)) * BINS - .5, k0 = ((Math.floor(f) % BINS) + BINS) % BINS, u = f - Math.floor(f); return over[k0] * (1 - u) + over[(k0 + 1) % BINS] * u; };
    for (let i = 0; i < B.n; i++) {
      const x = B.pts[i * 3], y = B.pts[i * 3 + 1], z = B.pts[i * 3 + 2];
      const a = angleOf(x, z), r = Math.hypot(x, z), b = base[binOf(a)];
      report.widest_gap_before_m = Math.max(report.widest_gap_before_m, b - cinch(a));   // the belt's inner face off the shirt
      const r2 = r - (b - onto(a));
      if (r2 > 0) { const g = r2 / r; place(belt, binv, i, x * g, y, z * g); report.belt++; }
      blendWeights(belt, i, beltW[i], nearestWeights(pool, x, y, z), 1);
    }
    report.belt_off_shirt_m = lift;
    for (const m of [skirt, belt, ...wraps]) { m.geometry.computeBoundingSphere(); m.geometry.computeBoundingBox(); }
    root.userData.chicagoWaistFit = report;
    return report;
  }
  return null;
}
