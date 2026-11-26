// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553 round 5, the outer layer (the owner, 2026-11-25, on four close-ups: the coachman's
 * coat "is so form fitting", John's "suit lapels are awful ... his shoulder has a lump", the
 * maid's collar "is all jagged, and the way that apron lays is messy and does not look like
 * fabric").
 *
 * Coats, jackets and bodices are exported as shells a few millimetres off the skin, so they
 * carry the body's small forms (the chest's muscles, the shoulder blade, the spine's groove)
 * and every trim lying on them (lapels, collars, buttons, apron straps, belts) is a second
 * thin shell that steps and wobbles with them. This pass fairs each such garment the way
 * heavier cloth stands on a figure, then carries everything that lies on it:
 *
 *  1. Fair. The garment never comes nearer than the low-passed body plus its ease (so it
 *     spans the hollows), a coat may fall from the chest rather than follow the body in
 *     (`hang`), then outward-only and Taubin relaxing take the forms out, and its open edges
 *     are relaxed along their own line. It stays outside everything worn under it.
 *  2. Carry. Every piece that lies on the garment (a ray in from it meets the garment within
 *     RIDE_M) moves with the cloth under it, so a lapel, a button or a strap keeps its place
 *     and its standing; trims (lapels, revers, collars, straps, bibs, frills) are then relaxed
 *     themselves, edges along their line, and held RIDE_GAP_M off the cloth.
 *
 * Positions and normals change; topology, UVs, weights, meshes, materials and draw calls do
 * not. Runs after the tailoring passes (it fairs what they cut) and before settleOnBody,
 * bindLayers and cullHidden. Which garments and how much is a fit, not a measurement
 * (liberty L-drape-3553).
 */
import * as THREE from 'three';
import { kit, layerRank, LEFT_OFF, MIN_M, LAMBDA, MU } from './human-drape.js';

const { weldMeshes, pointGrid, triangleGrid, graphNormals, bodyFieldSteps, writeBack, kindOf, loopsOf, openingOf, distanceFrom, smoothCeiling } = kit;

/** Garments faired, by piece name, with their ease (metres off the low-passed body), how fast
 * they may come in going down (`hang`, metres per metre; none: they follow the figure). */
export const FAIRED = Object.freeze([
  { kind: 'coat', piece: /(coat_body|tailcoat_body)(_lod\d+)?$/, ease: 0.008, hang: 0.3 },
  { kind: 'jacket', piece: /(jacket_body|skeleton_jacket|child_jacket)(_lod\d+)?$/, ease: 0.006, hang: 0.4 },
  // A woman's bodice is cut to her figure and kept as cut; what lies on it is still laid on it.
  { kind: 'bodice', piece: /(bodice|short_gown_body|errand_shirtwaist|calico_blouse|calico_shirt_body)(_lod\d+)?$/, ease: 0, hang: 0, still: true },
]);
/** Pieces of a faired garment's cloth that are trims lying on it, not the garment itself. */
/** Riders pressed flat on the cloth under them (and what is faced on them). */
export const PRESS = /(lapels|revers)(_lod\d+)?$/;
export const PRESS_MAX_M = 0.005, PRESS_REACH_M = 0.05;
/** A rider point this near a pressed piece's point is a copy of it (a silk facing made from the
 * lapel's front faces): it keeps its place over that point exactly, and goes where it goes. */
export const COPY_M = 0.003;
/** Worn over every other garment at the waist: never a floor a garment is pushed out over. */
export const OVER_ALL = /(apron|pinafore)/;
export const TRIM = /(lapels|revers|collar|button|cuffs|waistcoat|neckband|frills?|_bow|strap|_bib|jabot|_ties|stock|belt|band)/;
/** A piece rides on the garment where a ray in from it meets the garment within RIDE_M; a
 * piece rides when RIDE_SHARE of its points do. Carried trims keep RIDE_GAP_M off the cloth. */
export const RIDE_M = 0.03, RIDE_SHARE = 0.3, RIDE_GAP_M = 0.0018, CARRY_FADE_M = [0.03, 0.07];
export const FAIR_FILL_ITERS = 40, FAIR_TAUBIN_ITERS = 30, FAIR_EDGE_ITERS = 16, CARRY_EVEN_ITERS = 24, LAY_EVEN_ITERS = 16;
const UNDER_GAP_M = 0.004, COVER_M = 0.09;
/** Distance along the cloth from a collar or cuff over which the fairing comes in. */
export const OPENING_RAMP_M = 0.08;
/** How far the fairing may press cloth in from where it was cut (metres). */
export const INWARD_M = 0.002;
/** No body point comes nearer the cloth than CLEAR_M along its normal, between the cloth's points too. */
export const CLEAR_M = 0.003;

/** Body points that come through between the cloth's points (a small form the cloth's points
 * straddle) push the nearest cloth points out until each clears by CLEAR_M. */
function* clearBody(W, B) {
  const { P, G } = W, near = pointGrid(P, 0.02);
  for (let pass = 0; pass < 3; pass++) {
    const cast = triangleGrid(P, W.tris, 0.03), push = new Float64Array(G);
    let any = 0;
    for (let b = 0; b < B.G; b++) {
      const x = B.P[b * 3], y = B.P[b * 3 + 1], z = B.P[b * 3 + 2], nx = B.N[b * 3], ny = B.N[b * 3 + 1], nz = B.N[b * 3 + 2];
      // The cloth inside the body point (it came through) or nearer than CLEAR_M outside it.
      const inside = cast(x + nx * 0.02, y + ny * 0.02, z + nz * 0.02, -nx, -ny, -nz, 0.03);
      if (!Number.isFinite(inside)) continue;
      const gap = 0.02 - inside;   // the cloth's height over the body point (negative: inside it)
      const need = Math.min(0.012, CLEAR_M - gap); if (need <= 0) continue;
      const g = near(x + nx * gap, y + ny * gap, z + nz * gap); if (g < 0) continue;
      for (const h of [g, ...W.nb[g]]) push[h] = Math.max(push[h], need * (h === g ? 1 : 0.6));
      any++;
    }
    if (!any) break;
    for (let g = 0; g < G; g++) if (push[g] > 0) { const a = Math.max(0, B.near(P[g * 3], P[g * 3 + 1], P[g * 3 + 2])) * 3; P[g * 3] += B.N[a] * push[g]; P[g * 3 + 1] += B.N[a + 1] * push[g]; P[g * 3 + 2] += B.N[a + 2] * push[g]; }
    yield;
  }
}

const smoothstep = (x) => { const t = Math.max(0, Math.min(1, x)); return t * t * (3 - 2 * t); };
const LOOK = /^(garment_(upper|lower|outer)|accessory|footwear)__/;

/** One Laplacian pass over a welded graph (`edges`: open edges only, along their line). */
function relax(W, w, { edges = false, outwardOnly = null, keep = null, scale = null } = {}) {
  const { P, G, nb, edgeNb } = W, Q = new Float64Array(P.length);
  for (let g = 0; g < G; g++) {
    const isEdge = edgeNb[g].length > 0;
    let list = null;
    if (edges) { if (isEdge && edgeNb[g].length === 2) list = edgeNb[g]; }
    else if (isEdge) { if (edgeNb[g].length === 2) list = edgeNb[g]; }
    else list = nb[g];
    if (!list || !list.length || (keep && keep[g])) { Q[g * 3] = P[g * 3]; Q[g * 3 + 1] = P[g * 3 + 1]; Q[g * 3 + 2] = P[g * 3 + 2]; continue; }
    let cx = 0, cy = 0, cz = 0; for (const h of list) { cx += P[h * 3]; cy += P[h * 3 + 1]; cz += P[h * 3 + 2]; }
    cx = cx / list.length - P[g * 3]; cy = cy / list.length - P[g * 3 + 1]; cz = cz / list.length - P[g * 3 + 2];
    if (outwardOnly) { const n = outwardOnly(g), o = cx * n[0] + cy * n[1] + cz * n[2]; if (o < 0) { cx -= o * n[0]; cy -= o * n[1]; cz -= o * n[2]; } }
    if (scale) { cx *= scale[g]; cy *= scale[g]; cz *= scale[g]; }
    Q[g * 3] = P[g * 3] + w * cx; Q[g * 3 + 1] = P[g * 3 + 1] + w * cy; Q[g * 3 + 2] = P[g * 3 + 2] + w * cz;
  }
  P.set(Q);
}

/** Fair a body's coats, jackets and bodices and carry what lies on them. Returns
 * { faired: [{ kind, meshes, points }], carried: [{ mesh, on }] } on root.userData.chicagoFair. */
export function* fairOuterSteps(root) {
  const skinned = []; root.updateMatrixWorld(true);
  root.traverse((o) => { if (o.isSkinnedMesh && o.geometry?.attributes?.position) skinned.push(o); });
  const body = skinned.find((m) => m.material?.name === 'skin'), report = { faired: [], carried: [], trimmed: [] };
  if (!body) return report;
  const worn = skinned.filter((m) => m !== body && LOOK.test(m.material?.name ?? ''));
  const groups = [];
  for (const m of worn) {
    const f = FAIRED.find((k) => k.piece.test(m.name)); if (!f || kindOf(m)) continue;
    const meshes = worn.filter((o) => o.material === m.material && !TRIM.test(o.name.replace(/_lod\d+$/, '')) && !kindOf(o));
    if (!meshes.includes(m)) meshes.push(m);
    if (groups.some((gr) => gr.meshes.some((o) => meshes.includes(o)))) continue;
    groups.push({ f, meshes, rank: Math.max(...meshes.map(layerRank)) });
  }
  if (!groups.length) return report;
  const B = yield* bodyFieldSteps(body);
  groups.sort((a, b) => a.rank - b.rank);
  const done = new Set();
  for (const grp of groups) {
    yield;
    const W = weldMeshes(grp.meshes), { P, G } = W, old = Float64Array.from(P);
    const anchor = new Int32Array(G);
    const reanchor = () => { for (let g = 0; g < G; g++) anchor[g] = Math.max(0, B.near(P[g * 3], P[g * 3 + 1], P[g * 3 + 2])); };
    reanchor();
    const offsetOf = (g) => { const a = anchor[g] * 3; return (P[g * 3] - B.P[a]) * B.N[a] + (P[g * 3 + 1] - B.P[a + 1]) * B.N[a + 1] + (P[g * 3 + 2] - B.P[a + 2]) * B.N[a + 2]; };
    // What lies on this garment (rides) and what it lies on (floors).
    const cast = triangleGrid(old, W.tris, 0.03);
    const riders = [], floors = [], ceilings = [];
    for (const m of worn) {
      if (grp.meshes.includes(m) || !m.geometry.index) continue;
      const Wm = weldMeshes([m]); let on = 0;
      const hit = new Uint8Array(Wm.G);
      for (let g = 0; g < Wm.G; g++) {
        const a = Math.max(0, B.near(Wm.P[g * 3], Wm.P[g * 3 + 1], Wm.P[g * 3 + 2])) * 3;
        if (Number.isFinite(cast(Wm.P[g * 3], Wm.P[g * 3 + 1], Wm.P[g * 3 + 2], -B.N[a], -B.N[a + 1], -B.N[a + 2], RIDE_M))) { hit[g] = 1; on++; }
      }
      if (on >= RIDE_SHARE * Wm.G && !done.has(m)) riders.push({ m, W: Wm, hit, share: on / Wm.G });
      // An apron or pinafore is worn over whatever is at the waist, never under it.
      else if (layerRank(m) <= grp.rank && layerRank(m) > 0 && !OVER_ALL.test(m.name)) floors.push(m);
      else if (layerRank(m) > grp.rank && !LEFT_OFF.test(m.name) && !/(headwear|plumes|basket)/.test(m.name)) ceilings.push(m);
      yield;
    }
    const floorCasts = floors.map((m) => { const Wf = weldMeshes([m]); return triangleGrid(Wf.P, Wf.tris, 0.03); });
    // Nothing is pressed in more than INWARD_M from where it was cut (the room a pose needs).
    const cut = new Float64Array(G); for (let g = 0; g < G; g++) cut[g] = offsetOf(g);
    const floor = new Float64Array(G);
    const floorNow = () => {
      for (let g = 0; g < G; g++) {
        const a = anchor[g] * 3; let under = -Infinity;
        for (const c of floorCasts) { const d = c(B.P[a], B.P[a + 1], B.P[a + 2], B.N[a], B.N[a + 1], B.N[a + 2], COVER_M); if (Number.isFinite(d) && d > under) under = d; }
        floor[g] = Math.max(MIN_M, under > -Infinity ? under + UNDER_GAP_M : 0, cut[g] - INWARD_M);
      }
    };
    floorNow();
    // Ceiling: room under what is worn over it and does not ride on it (a skirt's band over a
    // bodice's waist), coming out from under gently.
    const ceilCasts = ceilings.map((m) => { const Wc = weldMeshes([m]); return triangleGrid(Wc.P, Wc.tris, 0.03); });
    const ceil = new Float64Array(G).fill(Infinity);
    if (ceilCasts.length) {
      for (let g = 0; g < G; g++) {
        const a = anchor[g] * 3; let over = Infinity;
        for (const c of ceilCasts) over = Math.min(over, c(B.P[a], B.P[a + 1], B.P[a + 2], B.N[a], B.N[a + 1], B.N[a + 2], COVER_M));
        if (Number.isFinite(over)) ceil[g] = Math.max(MIN_M, over - UNDER_GAP_M);
      }
      smoothCeiling(W, ceil, 0.25);
    }
    // Openings that close on the figure (a collar's stand, a cuff) keep their cut: the fairing
    // comes in over OPENING_RAMP_M along the cloth.
    const shut = [];
    for (const loop of loopsOf(W)) { const t = openingOf(loop, W, B, anchor); if (t === 'collar' || t === 'cuff') shut.push(...loop); }
    const D = shut.length ? distanceFrom(W, shut) : new Float64Array(G).fill(Infinity);
    const free = new Float64Array(G); for (let g = 0; g < G; g++) free[g] = smoothstep(D[g] / OPENING_RAMP_M);
    // Pieces of the same cloth that are not the faired kind (a coat's skirt, hanging from the
    // waist over the legs) keep their cut: fairing them onto the legs opened a skirt's fronts.
    const pinned = new Uint8Array(G);
    for (let g = 0; g < G; g++) if (W.members[g].every(([part]) => !grp.f.piece.test(part.mesh.name))) { pinned[g] = 1; free[g] = 0; }
    yield;
    // 1. Target: never nearer than the low-passed body plus the ease, nor than it was cut.
    const target = new Float64Array(G);
    for (let g = 0; g < G; g++) {
      const a = anchor[g] * 3, smooth = (B.S[a] - B.P[a]) * B.N[a] + (B.S[a + 1] - B.P[a + 1]) * B.N[a + 1] + (B.S[a + 2] - B.P[a + 2]) * B.N[a + 2];
      const off = offsetOf(g);
      target[g] = Math.min(Math.max(floor[g], off, off + free[g] * (smooth + grp.f.ease - off)), Math.max(ceil[g], off));
    }
    if (grp.f.hang) {
      // Falling from the chest and the shoulder blades: going down the torso, the offset may
      // shrink by at most `hang` metres per metre.
      const torso = (g) => /^(spine|pelvis|root)/.test(B.names[B.bone[anchor[g]]] ?? '');
      const V = Float64Array.from(target), order = [...Array(G).keys()].filter(torso).sort((p, q) => P[q * 3 + 1] - P[p * 3 + 1]);
      for (let pass = 0; pass < 2; pass++) for (const g of order) for (const h of W.nb[g]) {
        if (!torso(h) || P[h * 3 + 1] >= P[g * 3 + 1]) continue;
        const v = V[g] - grp.f.hang * Math.hypot(P[g * 3] - P[h * 3], P[g * 3 + 1] - P[h * 3 + 1], P[g * 3 + 2] - P[h * 3 + 2]);
        if (v > V[h]) V[h] = Math.min(v, target[h] + 0.03 * free[h], ceil[h]);
      }
      target.set(V);
    }
    if (grp.f.still) target.set(cut); else for (let g = 0; g < G; g++) if (pinned[g]) target[g] = cut[g];
    for (let g = 0; g < G; g++) { const a = anchor[g] * 3, d = target[g] - offsetOf(g); P[g * 3] += B.N[a] * d; P[g * 3 + 1] += B.N[a + 1] * d; P[g * 3 + 2] += B.N[a + 2] * d; }
    const clamp = () => { for (let g = 0; g < G; g++) { const off = offsetOf(g), want = Math.max(floor[g], Math.min(off, Math.max(ceil[g], floor[g]))); if (want !== off) { const a = anchor[g] * 3, d = want - off; P[g * 3] += B.N[a] * d; P[g * 3 + 1] += B.N[a + 1] * d; P[g * 3 + 2] += B.N[a + 2] * d; } } };
    const nOf = (g) => { const a = anchor[g] * 3; return [B.N[a], B.N[a + 1], B.N[a + 2]]; };
    // 2. Relax: hollows filled, forms taken out, edges along their line.
    for (let it = 0; it < (grp.f.still ? 0 : FAIR_FILL_ITERS); it++) { relax(W, LAMBDA, { outwardOnly: nOf, scale: free }); clamp(); if (it % 8 === 7) yield; }
    for (let it = 0; it < (grp.f.still ? 0 : FAIR_TAUBIN_ITERS); it++) { relax(W, LAMBDA, { scale: free }); relax(W, MU, { scale: free }); clamp(); if (it % 10 === 9) { reanchor(); floorNow(); yield; } }
    for (let it = 0; it < (grp.f.still ? 0 : FAIR_EDGE_ITERS); it++) { relax(W, LAMBDA, { edges: true, keep: pinned }); relax(W, MU, { edges: true, keep: pinned }); }
    reanchor(); floorNow(); clamp();
    yield* clearBody(W, B);
    writeBack(W, grp.f.still ? null : graphNormals(P, W.tris, G));
    yield;
    // 3. Carry what lies on it, by the move of the cloth under each point.
    // Surfaces a piece may lie on: the garment, then each piece already carried (a lapel's silk
    // facing lies on the lapel, not on the coat under it). Riders go most-on first.
    const surfaces = [{ old, now: P, nb: W.nb, near: pointGrid(old, 0.02), cast: triangleGrid(P, W.tris, 0.03) }];
    const newCast = (ox, oy, oz, dx, dy, dz, far) => { let best = Infinity; for (const sf of surfaces) best = Math.min(best, sf.cast(ox, oy, oz, dx, dy, dz, far)); return best; };
    riders.sort((p, q) => q.share - p.share);
    for (const r of riders) {
      const { W: Wr, hit } = r, Pr = Wr.P, n = Wr.G, oldR = Float64Array.from(Pr);
      // The move of the cloth under each point, then evened out over the piece itself, so a
      // collar or a strap moves as one strip rather than following every point under it.
      const M = new Float64Array(n * 3), press = PRESS.test(r.m.name), onPress = new Uint8Array(n), copyOf = new Array(n).fill(null);
      for (let g = 0; g < n; g++) {
        const x = Pr[g * 3], y = Pr[g * 3 + 1], z = Pr[g * 3 + 2];
        let sf = null, b = -1, d0 = Infinity;
        for (const cand of surfaces) { const i = cand.near(x, y, z); if (i < 0) continue; const d = Math.hypot(cand.old[i * 3] - x, cand.old[i * 3 + 1] - y, cand.old[i * 3 + 2] - z); if (d < d0) { d0 = d; sf = cand; b = i; } }
        if (!sf) continue;
        if (sf.pressed && d0 < 0.02) onPress[g] = 1;
        if (sf.pressed && d0 < COPY_M) copyOf[g] = { sf, i: b, off: [x - sf.old[b * 3], y - sf.old[b * 3 + 1], z - sf.old[b * 3 + 2]] };
        const { old: O, now: Nw } = sf;
        let sx = 0, sy = 0, sz = 0, sw = 0;
        const ring = new Set([b]); for (const h of sf.nb[b]) { ring.add(h); for (const k of sf.nb[h]) ring.add(k); }
        for (const h of ring) { const d = Math.hypot(O[h * 3] - x, O[h * 3 + 1] - y, O[h * 3 + 2] - z), w = Math.exp(-((d / 0.012) ** 2)) + 1e-9; sx += w * (Nw[h * 3] - O[h * 3]); sy += w * (Nw[h * 3 + 1] - O[h * 3 + 1]); sz += w * (Nw[h * 3 + 2] - O[h * 3 + 2]); sw += w; }
        const k = hit[g] ? 1 : 1 - smoothstep((d0 - CARRY_FADE_M[0]) / (CARRY_FADE_M[1] - CARRY_FADE_M[0]));
        M[g * 3] = k * sx / sw; M[g * 3 + 1] = k * sy / sw; M[g * 3 + 2] = k * sz / sw;
      }
      const even = (F, iters) => { const T = new Float64Array(F.length), dim = F.length / n; for (let it = 0; it < iters; it++) { for (let g = 0; g < n; g++) { const l = Wr.nb[g]; for (let d = 0; d < dim; d++) { let s2 = 0; for (const h of l) s2 += F[h * dim + d]; T[g * dim + d] = l.length ? 0.5 * F[g * dim + d] + 0.5 * s2 / l.length : F[g * dim + d]; } } F.set(T); } };
      even(M, CARRY_EVEN_ITERS);
      for (let i = 0; i < n * 3; i++) Pr[i] += M[i];
      // Laid on the cloth: each point's height over the cloth under it is evened out over the
      // piece (never under RIDE_GAP_M), so a collar or a strap lies as one smooth strip instead
      // of rippling with the points under it; the points off the cloth follow their neighbours.
      const hgt = new Float64Array(n).fill(NaN), dir = new Float64Array(n * 3);
      for (let g = 0; g < n; g++) {
        const a = Math.max(0, B.near(Pr[g * 3], Pr[g * 3 + 1], Pr[g * 3 + 2])) * 3;
        dir[g * 3] = B.N[a]; dir[g * 3 + 1] = B.N[a + 1]; dir[g * 3 + 2] = B.N[a + 2];
      }
      even(dir, 6);
      for (let g = 0; g < n; g++) {
        const l = Math.hypot(dir[g * 3], dir[g * 3 + 1], dir[g * 3 + 2]) || 1; dir[g * 3] /= l; dir[g * 3 + 1] /= l; dir[g * 3 + 2] /= l;
        const pressed = press || onPress[g];
        if (!hit[g] && !pressed) continue;
        const h = newCast(Pr[g * 3] + dir[g * 3] * 0.02, Pr[g * 3 + 1] + dir[g * 3 + 1] * 0.02, Pr[g * 3 + 2] + dir[g * 3 + 2] * 0.02, -dir[g * 3], -dir[g * 3 + 1], -dir[g * 3 + 2], (pressed ? PRESS_REACH_M : RIDE_M) + 0.02);
        if (Number.isFinite(h)) hgt[g] = 0.02 - h;
      }
      // A lapel (and the silk faced on it) is pressed: it lies on the coat, never standing
      // more than PRESS_MAX_M off it (a lapel's top that stood up over the shoulder read as a lump).
      const cap = (g) => (press || onPress[g] ? PRESS_MAX_M + (onPress[g] && !press ? RIDE_GAP_M : 0) : Infinity);
      const lay = Float64Array.from(hgt, (h, g) => (Number.isFinite(h) ? Math.min(cap(g), Math.max(RIDE_GAP_M, h)) : NaN));
      for (let it = 0; it < LAY_EVEN_ITERS; it++) { const T = Float64Array.from(lay); for (let g = 0; g < n; g++) { if (!Number.isFinite(lay[g])) continue; let s2 = 0, c = 0; for (const h of Wr.nb[g]) if (Number.isFinite(lay[h])) { s2 += lay[h]; c++; } if (c) T[g] = Math.min(cap(g), Math.max(RIDE_GAP_M, 0.5 * lay[g] + 0.5 * s2 / c)); } lay.set(T); }
      const mv = new Float64Array(n), known = new Uint8Array(n);
      for (let g = 0; g < n; g++) if (Number.isFinite(hgt[g])) { mv[g] = lay[g] - hgt[g]; known[g] = 1; }
      for (let it = 0; it < LAY_EVEN_ITERS; it++) { const T = Float64Array.from(mv); for (let g = 0; g < n; g++) { if (known[g]) continue; let s2 = 0, c = 0; for (const h of Wr.nb[g]) { s2 += mv[h]; c++; } if (c) T[g] = s2 / c; } mv.set(T); }
      for (let g = 0; g < n; g++) for (let d = 0; d < 3; d++) Pr[g * 3 + d] += mv[g] * dir[g * 3 + d];
      for (let g = 0; g < n; g++) { const c = copyOf[g]; if (c) for (let d = 0; d < 3; d++) Pr[g * 3 + d] = c.sf.now[c.i * 3 + d] + c.off[d]; }
      // A pressed piece's ends that have no cloth under them at all (a lapel's top standing free
      // beside the neck, over the shoulder) are left out: they stood up as a lump.
      if (press || onPress.some((v) => v)) {
        const free = (g) => (copyOf[g] ? !copyOf[g].sf.kept[copyOf[g].i] : (press || onPress[g]) && !Number.isFinite(hgt[g]));
        const part = Wr.parts[0], idx = r.m.geometry.index.array, kept = [];
        for (let t = 0; t < idx.length; t += 3) if (!(free(part.group[idx[t]]) && free(part.group[idx[t + 1]]) && free(part.group[idx[t + 2]]))) kept.push(idx[t], idx[t + 1], idx[t + 2]);
        if (kept.length < idx.length) { r.m.geometry.setIndex(new THREE.BufferAttribute(new (idx.constructor)(kept), 1)); report.trimmed.push({ mesh: r.m.name, triangles: (idx.length - kept.length) / 3 }); }
      }
      // Normals as drawn: the piece moved as a strip, and its own normals were drawn from finer
      // cloth than its points (recomputing them shows every small wobble of the points).
      writeBack(Wr, null);
      const kept = new Uint8Array(n); { const part = Wr.parts[0], idx = r.m.geometry.index.array; for (let t = 0; t < idx.length; t++) kept[part.group[idx[t]]] = 1; }
      surfaces.push({ pressed: press, kept, old: oldR, now: Pr, nb: Wr.nb, near: pointGrid(oldR, 0.02), cast: triangleGrid(Pr, Wr.tris, 0.03) });
      done.add(r.m);
      report.carried.push({ mesh: r.m.name, on: +r.share.toFixed(2) });
      yield;
    }
    report.faired.push({ kind: grp.f.kind, meshes: grp.meshes.map((m) => m.name), points: G });
  }
  root.userData.chicagoFair = report;
  return report;
}

export function fairOuter(root) { const s = fairOuterSteps(root); for (;;) { const n = s.next(); if (n.done) return n.value; } }
