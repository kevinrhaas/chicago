// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-tailor-1835.js — the 1835 merchant's strapped trousers and the labourer's white,
 * gathered shirt sleeves (T-3553, the catalogue review of 2026-11-17).
 *
 * The owner, 2026-11-17, on the people-match catalogue: "yes do tailoring fixes". The review
 * laid each figure beside its period pictures (data/people_match/subjects/):
 *
 *   - Philip F. W. Peck, merchant (peck_philip_1835): the Met's coat and trousers of c.1833
 *     (Costume Institute 1981.210.4, 1982.316.11) are full trousers pleated into the
 *     waistband, tapering to straps under the shoes; ours were straight pale tubes from the
 *     hip to a wide hem, no pleats, no straps.
 *   - Patrick Mahoney, labourer (mahoney_patrick_1835): Mount's Raffle (1837), Weir's Wood
 *     Sawyer (1842) and Mount's Cider Making (1840-41) all draw white shirts, the full sleeves
 *     gathered at the wrist into a band with folds down the arm; ours was unbleached
 *     beige-grey, greyer than every picture, and its sleeves ran smooth to a plain wrist.
 *
 * Here, once per loaded body (before any figure is cloned from it, as human-seat.js does),
 * keyed to these two bodies' own pieces (TAILOR), at every level:
 *
 *   Peck's trousers (`full_trousers`)
 *     1. fullness: the front of the trousers, from just under the waistcoat's hem down the
 *        thighs, stands out up to FULL_M (a pleated top's fullness), most where the cloth
 *        faces forward, less at the sides, none behind (under the tails), tapering away down
 *        the thigh; never out through a garment worn over it (COVER_GAP_M inside it).
 *     2. taper: from the knee to TAPER_FULL_M above the ankle each leg's section is drawn in
 *        to TAPER_MIN of its width, never closer than CLEAR_M to the leg or shoe inside it,
 *        so the hem closes round the shoe and drapes on its instep as a strapped pair does.
 *     3. pleats (LOD0 and LOD1): PLEATS folds a side, laid on the cloth
 *        from under the waistcoat's hem down the front of the thigh, standing up to PLEAT_M
 *        and fading out above mid-thigh, each rising gently from the fly side and dropping
 *        steeply toward the hip (a fold laid toward the side seam, which throws a shadow
 *        line); skinned as the cloth under them is.
 *     4. straps (every level): a band of the trousers' cloth STRAP_W_M wide and STRAP_T_M
 *        thick under each shoe's waist, in front of the heel, from inside the hem down both
 *        sides of the shoe and through under its sole, riding the foot bone.
 *
 *   Round 4 (the catalogue's leftovers: "his pleats read only as faint creases at 3 m and the
 *   fullness is less than the Met c.1833 pair's ... the straps under his shoes are thin pale
 *   bands, hard to see from the front"): FULL_M 1.8 -> 3 cm, PLEAT_M 7 -> 12 mm with the
 *   folded profile, straps 1.9 cm by 2 mm -> 3 cm by 3 mm. A strap of the shoes' black
 *   (STRAP_LEATHER) was asked for, built and shot: on the black shoe it cannot be seen at all,
 *   so the strap stays the trousers' cloth, and with it each townsman's own trouser colour.
 *   From the front no strap can show: it passes under the shoe's waist, behind the ball.
 *   Mahoney's shirt (`shirt_full_sleeves`)
 *     5. colour: white linen, a warm white (LINEN_SRGB), not a blue-white, on the shirt's own
 *        flat picture (its colour scaled; the program unchanged). The 1835 townspeople who
 *        wear this body and carry their own shirt colour (human-looks.js dressCloth) keep it.
 *     6. wristbands (every level): a band BAND_M long round each wrist
 *        over the sleeve's end, the sleeve drawn in under it.
 *     7. gathers (LOD0 to LOD2): the sleeve's lower forearm blouses out over
 *        the band and is drawn into it in GATHER_FOLDS gathers, which run on up the forearm as
 *        soft folds fading out below the elbow; skinned as the sleeve under it, the band's
 *        own weights where it goes into the band. The sleeve under it stays inside it.
 *
 * Round 2's sleeve hems (human-sleeve.js fitSleeves) run first: the band and the gathers'
 * foot take the hem's one set of weights, which this does not change. Topology, UVs and skin
 * weights of the drawn garments are unchanged; their positions move only as described. The
 * pieces (3, 4, 6, 7) are appended to the garment's own mesh (T-3555: no mesh, draw call,
 * material or texture more per figure; human-regulars.js appends its breast tape the same
 * way), after its drawn vertices and triangles, skinned on its skeleton, so a cloned figure,
 * a person's colours and the cloth shader reach them as they reach the garment. Cost: once per parse, some 60 ms at LOD0 and under 15 at LOD2-3 on a desktop core
 * (casts against the garment, as human-sleeve.js does); LOD0 adds about 630 vertices to
 * Peck and 2,700 to Mahoney, no texture, no program. Reconstructed tailoring bounded by the
 * pictures named (liberty L-tailor-1835-3553).
 */
import * as THREE from 'three';

/** The bodies tailored, by asset id, and their pieces (mesh names without asset and level). */
export const TAILOR = Object.freeze({
  peck_philip_1835: Object.freeze({ trousers: 'full_trousers', shoes: 'closed_shoes', body: 'body_0', over: Object.freeze(['waistcoat_buff', 'tailcoat_body', 'tailcoat_tails', 'tailcoat_lapels', 'shirt_front_and_cuffs']) }),
  mahoney_patrick_1835: Object.freeze({ shirt: 'shirt_full_sleeves', body: 'body_0' }),
});
/** Mahoney's shirt's picture is one flat colour (sRGB 158, 147, 125: the unbleached linen the
 * body was built with; tools/test_human_tailor_1835.mjs pins the picture by its sha256). */
export const SHIRT_PICTURE_SRGB = Object.freeze([158, 147, 125]);
/** White linen as drawn: a warm white, the red over the blue (sRGB). */
export const LINEN_SRGB = Object.freeze([233, 228, 213]);

/** Fullness at the front of the hips, metres at most (round 4: 1.8 cm read as too little
 * beside the Met pair's, which balloon there). */
export const FULL_M = 0.03;
/** Never closer than this inside a garment worn over the trousers. */
export const COVER_GAP_M = 0.002;
/** Taper: each leg's section drawn in to TAPER_MIN from the knee down to TAPER_FULL_M above
 * the ankle (and held to the hem), never closer than CLEAR_M to the leg or shoe inside it, nor
 * than HEM_CLEAR_M to the shoe at the hem, below the ankle joint, where the cloth lies on it. */
export const TAPER_MIN = 0.62, TAPER_FULL_M = 0.07, CLEAR_M = 0.011, HEM_CLEAR_M = 0.005;
/** More clearance by level of detail (the far levels' coarser sections). */
export const FAR_CLEAR_M = Object.freeze([0, 0, 0.003, 0.006]);
/** Pleats: so many a side, standing up to PLEAT_M off the cloth, PLEAT_DOWN_M long, each
 * PLEAT_HALF_M (plus PLEAT_SPREAD_M at its foot) either side of its crest. Across a pleat the
 * cloth rises gently from the fly side to the crest (PLEAT_ACROSS, PLEAT_PROFILE) and drops
 * steeply on the side-seam side, a fold laid toward the hip, so it throws a shadow line. */
export const PLEATS = 3, PLEAT_M = 0.012, PLEAT_DOWN_M = 0.3, PLEAT_LIFT_M = 0.0015, PLEAT_HALF_M = 0.016, PLEAT_SPREAD_M = 0.008;
export const PLEAT_ACROSS = Object.freeze([-1, -0.4, 0.2, 0.6, 1]), PLEAT_PROFILE = Object.freeze([0, 0.33, 0.84, 1, 0]);
/** Straps: this wide along the foot, this thick, this far in front of the ankle joint (round
 * 4: 1.9 cm by 2 mm read as thin bands, hardly seen from the front). Of the trousers' cloth;
 * STRAP_LEATHER draws them in the shoes' black instead, built and shot in round 4 and not
 * kept: black on the black shoe, the strap could not be seen at all. */
export const STRAP_W_M = 0.03, STRAP_T_M = 0.003, STRAP_AT_M = 0.03, STRAP_LEATHER = false;
/** The wristband: this long up the arm, standing this far off the wrist. */
export const BAND_M = 0.035, BAND_EASE_M = 0.009, BAND_T_M = 0.003;
/** The gathers: so many folds round the arm, so deep at the band; the puff over the band
 * GATHER_M long; soft folds on up the forearm to FOLD_TOP_M past the elbow. */
export const GATHER_FOLDS = 9, GATHER_DEEP_M = 0.0045, FOLD_M = 0.0022, PUFF_M = 0.007, GATHER_M = 0.09, FOLD_TOP_M = 0.06, GATHER_LIFT_M = 0.002;

const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const lodOf = (o) => Number((o.name ?? '').match(/_lod(\d+)$/)?.[1] ?? 0);
const pieceOf = (o, assetId) => {
  let n = o.name ?? '';
  if (assetId && n.startsWith(`${assetId}_`)) n = n.slice(assetId.length + 1);
  return n.replace(/_lod\d*$/, '');
};
const srgbToLinear = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };

/** A mesh's bind positions (metres), welded points (a UV seam's copies move as one; with
 * `weld` false every vertex is its own), triangles. */
function survey(mesh, weld = true) {
  const geo = mesh.geometry, pos = geo.attributes.position, n = pos.count, idx = geo.index;
  const P = new Array(n), B = mesh.bindMatrix;
  const groupOf = new Int32Array(n), first = [], keys = weld ? new Map() : null;
  for (let i = 0; i < n; i++) {
    const p = P[i] = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(B);
    if (!weld) { groupOf[i] = i; first.push(i); continue; }
    // A numeric key per 0.05 mm cell (exact copies share it; the body is never this fine).
    const k = (Math.round(p.x * 2e4) + 32768) * 4294967296 + (Math.round(p.y * 2e4) + 32768) * 65536 + (Math.round(p.z * 2e4) + 32768);
    let g = keys.get(k);
    if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); }
    groupOf[i] = g;
  }
  const tris = [];
  const count = idx ? idx.count / 3 : n / 3;
  for (let t = 0; t < count; t++) tris.push(idx ? [idx.getX(t * 3), idx.getX(t * 3 + 1), idx.getX(t * 3 + 2)] : [t * 3, t * 3 + 1, t * 3 + 2]);
  return { P, groupOf, first, tris, n };
}
function bonePos(mesh, name) {
  const sk = mesh.skeleton, i = sk.bones.findIndex((b) => b?.name === name);
  return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert());
}
function weightsOf(mesh, i) {
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight, out = {};
  for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); if (w > 0) { const b = si.getComponent(i, k); out[b] = (out[b] ?? 0) + w; } }
  return out;
}
function mix(sets) {
  const out = {};
  for (const [set, k] of sets) for (const [b, w] of Object.entries(set)) out[b] = (out[b] ?? 0) + w * k;
  return out;
}

/** The nearest (or farthest) hit of a ray on a mesh's triangles within maxT: { t, tri, u, v }. */
function castRay(o, d, tris, P, maxT, farthest = false) {
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
    if (t > 1e-5 && t < maxT && (!best || (farthest ? t > best.t : t < best.t))) best = { t, tri: tr, u, v };
  }
  return best;
}
/** Triangles near a box (a faster cast over the part of a mesh that matters). */
function trisIn(tris, P, lo, hi) {
  return tris.filter((tr) => tr.some((i) => P[i].x >= lo.x && P[i].x <= hi.x && P[i].y >= lo.y && P[i].y <= hi.y && P[i].z >= lo.z && P[i].z <= hi.z));
}
/** The weights, UV and position at a hit, from its triangle's corners. */
function atHit(mesh, S, hit) {
  const [a, b, c] = hit.tri, wa = 1 - hit.u - hit.v;
  const uv = mesh.geometry.attributes.uv;
  return {
    weights: mix([[weightsOf(mesh, a), wa], [weightsOf(mesh, b), hit.u], [weightsOf(mesh, c), hit.v]]),
    uv: uv ? [uv.getX(a) * wa + uv.getX(b) * hit.u + uv.getX(c) * hit.v, uv.getY(a) * wa + uv.getY(b) * hit.u + uv.getY(c) * hit.v] : [0, 0],
  };
}

/** Turn every triangle to face `outward(centroid)` (a direction); returns the index list. */
function orient(index, P, outward) {
  const e1 = new THREE.Vector3(), e2 = new THREE.Vector3(), c = new THREE.Vector3();
  for (let t = 0; t < index.length; t += 3) {
    const a = P[index[t]], b = P[index[t + 1]], d = P[index[t + 2]];
    const fn = e1.subVectors(b, a).cross(e2.subVectors(d, a));
    c.copy(a).add(b).add(d).divideScalar(3);
    if (fn.dot(outward(c, t / 3)) < 0) { const x = index[t + 1]; index[t + 1] = index[t + 2]; index[t + 2] = x; }
  }
  return index;
}

/**
 * A new skinned piece of `src`'s cloth: bind positions P, triangles `index`, a weight set
 * {boneIndex: weight} and a UV per point; on src's skeleton, bind matrix and material, beside
 * it in the scene. Normals from its own faces.
 */
/** Append pieces to the garment's own mesh (T-3555: no draw call, material or texture more
 * per figure): each piece's bind points `P`, triangles `index` (its own numbering), weights `W`
 * ({bone: weight} on the garment's skeleton) and UVs (or none), its normals from its faces.
 * The drawn vertices and triangles keep their places at the front; the pieces' ranges are
 * recorded on the mesh (userData.chicagoTailor1835: drawn counts and each piece's vertex and
 * index range) for tools/test_human_tailor_1835.mjs. Component by component: a loaded
 * attribute may be interleaved. */
function appendPieces(host, pieces) {
  pieces = pieces.filter((p) => p && p.P.length && p.index.length);
  const g = host.geometry, n0 = g.attributes.position.count, i0 = g.index ? g.index.count : n0;
  const rec = host.userData.chicagoTailor1835 ??= { drawn: { vertices: n0, indices: i0 }, parts: {} };
  if (!pieces.length) return rec;
  const add = pieces.reduce((s, p) => s + p.P.length, 0), total = n0 + add;
  const GET = ['getX', 'getY', 'getZ', 'getW'], SET = ['setX', 'setY', 'setZ', 'setW'];
  const next = {};
  for (const [k, attr] of Object.entries(g.attributes)) {
    const out = new THREE.BufferAttribute(new attr.array.constructor(total * attr.itemSize), attr.itemSize, attr.normalized);
    for (let i = 0; i < n0; i++) for (let c = 0; c < attr.itemSize; c++) out[SET[c]](i, attr[GET[c]](i));
    next[k] = out;
  }
  const Binv = host.bindMatrix.clone().invert(), nm = new THREE.Matrix3().getNormalMatrix(Binv);
  const old = g.index ? Array.from(g.index.array.subarray(0, i0)) : Array.from({ length: n0 }, (_, i) => i);
  const tris = [], v = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  let k = n0;
  for (const { key, P, index, W, UV } of pieces) {
    const start = k, sum = P.map(() => new THREE.Vector3());
    for (let t = 0; t < index.length; t += 3) {
      const [a, b, c] = [index[t], index[t + 1], index[t + 2]];
      const fn = e1.subVectors(P[b], P[a]).cross(e2.subVectors(P[c], P[a]));
      sum[a].add(fn); sum[b].add(fn); sum[c].add(fn);
    }
    for (let i = 0; i < P.length; i++, k++) {
      v.copy(P[i]).applyMatrix4(Binv); next.position.setXYZ(k, v.x, v.y, v.z);
      if (next.normal) { v.copy(sum[i]).applyMatrix3(nm); if (v.lengthSq() > 0) v.normalize(); else v.set(0, 1, 0); next.normal.setXYZ(k, v.x, v.y, v.z); }
      if (next.uv) { const u = UV?.[i] ?? [0, 0]; next.uv.setXY(k, u[0], u[1]); }
      if (next.skinIndex && next.skinWeight) {
        const top = Object.entries(W[i]).filter(([, w]) => w > 1e-4).sort((x, y) => y[1] - x[1]).slice(0, 4);
        // Normalised to one, and for a byte attribute to exactly 255 steps (a rig that keeps
        // each vertex's own total, human-skirt.js, would carry one a step off short or long).
        const sw = top.reduce((s, [, w]) => s + w, 0) || 1, max = next.skinWeight.normalized ? ({ Uint8Array: 255, Uint16Array: 65535 })[next.skinWeight.array.constructor.name] : null;
        const q = top.map(([, w]) => w / sw);
        if (max && q.length) { const n = q.map((w) => Math.round(w * max)); n[0] += max - n.reduce((s, x) => s + x, 0); n.forEach((x, c) => { q[c] = x / max; }); }
        for (let c = 0; c < 4; c++) { next.skinIndex[SET[c]](k, top[c] ? Number(top[c][0]) : 0); next.skinWeight[SET[c]](k, q[c] ?? 0); }
      }
    }
    const indexStart = old.length + tris.length;
    for (const i of index) tris.push(start + i);
    rec.parts[key] = { start, count: P.length, indexStart, indexCount: index.length };
  }
  for (const [name, attr] of Object.entries(next)) g.setAttribute(name, attr);
  const Arr = total > 65535 ? Uint32Array : (g.index?.array.constructor ?? Uint16Array);
  const idx = new Arr(old.length + tris.length); idx.set(old); idx.set(tris, old.length);
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  // One draw: a garment loaded as one primitive has no groups; if it had, the last one runs on.
  if (g.groups.length) { const last = g.groups[g.groups.length - 1]; if (last.start + last.count >= old.length) last.count = idx.length - last.start; }
  g.computeBoundingBox(); g.computeBoundingSphere();
  return rec;
}

/** Write moved welded points back into the geometry, and their normals from their faces. */
function commit(mesh, S, Q, moved) {
  const geo = mesh.geometry, pos = geo.attributes.position, Binv = mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
  for (let i = 0; i < S.n; i++) {
    const g = S.groupOf[i];
    if (!moved[g]) continue;
    v.copy(Q[g]).applyMatrix4(Binv); pos.setXYZ(i, v.x, v.y, v.z);
  }
  pos.needsUpdate = true;
  const nrm = geo.attributes.normal;
  if (nrm) {
    const G = Q.length, sum = Array.from({ length: G }, () => new THREE.Vector3()), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
    for (const tr of S.tris) {
      const q = tr.map((i) => S.groupOf[i]);
      if (!q.some((g) => moved[g])) continue;
      const fn = e1.subVectors(Q[q[1]], Q[q[0]]).cross(e2.subVectors(Q[q[2]], Q[q[0]]));
      for (const g of q) if (moved[g]) sum[g].add(fn);
    }
    const toBind = mesh.bindMatrix, nm = new THREE.Matrix3().getNormalMatrix(Binv), old = new THREE.Vector3();
    let agree = 0;
    for (let i = 0; i < S.n; i++) { const g = S.groupOf[i]; if (!moved[g]) continue; old.fromBufferAttribute(nrm, i).transformDirection(toBind); agree += Math.sign(sum[g].dot(old)); }
    const sign = agree < 0 ? -1 : 1;
    for (let i = 0; i < S.n; i++) {
      const g = S.groupOf[i]; if (!moved[g] || sum[g].lengthSq() < 1e-20) continue;
      v.copy(sum[g]).multiplyScalar(sign).applyMatrix3(nm).normalize();
      nrm.setXYZ(i, v.x, v.y, v.z);
    }
    nrm.needsUpdate = true;
  }
  geo.computeBoundingBox(); geo.computeBoundingSphere();
}

// ---------------------------------------------------------------------------------------------
// Peck's trousers.

/** The legs at bind: per side the hip H, knee K, ankle A and ball B; pelvis O, up U, left L, forward F. */
function legsOf(mesh) {
  const at = (n) => bonePos(mesh, n);
  const legs = {};
  for (const s of ['l', 'r']) {
    const H = at(`thigh_${s}`), K = at(`calf_${s}`), A = at(`foot_${s}`), B = at(`ball_${s}`);
    if (!H || !K || !A || !B) return null;
    legs[s] = { H, K, A, B };
  }
  const O = legs.l.H.clone().add(legs.r.H).multiplyScalar(0.5);
  const U = O.clone().sub(legs.l.A.clone().add(legs.r.A).multiplyScalar(0.5)).normalize();
  const L = legs.l.H.clone().sub(legs.r.H); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  const scale = ((legs.l.H.distanceTo(legs.l.A) + legs.r.H.distanceTo(legs.r.A)) / 2) / 0.85;
  return { legs, O, U, L, F, scale };
}

/** Garments worn over the trousers, as a hash of their bind points (for the cover cap). */
function coverHash(meshes, cell = 0.015) {
  const map = new Map(), key = (x, y, z) => `${Math.floor(x / cell)},${Math.floor(y / cell)},${Math.floor(z / cell)}`;
  for (const m of meshes) for (const p of survey(m, false).P) {
    const k = key(p.x, p.y, p.z); let l = map.get(k); if (!l) map.set(k, (l = [])); l.push(p);
  }
  return (p, out = []) => {
    out.length = 0;
    const ix = Math.floor(p.x / cell), iy = Math.floor(p.y / cell), iz = Math.floor(p.z / cell);
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let c = -1; c <= 1; c++) { const l = map.get(`${ix + a},${iy + b},${iz + c}`); if (l) out.push(...l); }
    return out;
  };
}

/** 1. Fullness at the front of the hips, under the waistcoat's hem and down the thighs. */
function fullFront(mesh, S, Q, frame, over, wcLow) {
  const { U, F, scale } = frame, G = Q.length;
  const nrm = mesh.geometry.attributes.normal, n0 = Array.from({ length: G }, () => new THREE.Vector3()), v = new THREE.Vector3();
  for (let i = 0; i < S.n; i++) n0[S.groupOf[i]].add(v.fromBufferAttribute(nrm, i).transformDirection(mesh.bindMatrix));
  const top = wcLow, ramp = 0.06 * scale, hold = frame.O.dot(U) - 0.1 * scale, fade = frame.O.dot(U) - 0.4 * scale;
  const amount = new Float64Array(G), dir = n0.map((n) => n.clone().addScaledVector(U, -n.dot(U)).normalize());
  for (let g = 0; g < G; g++) {
    const y = Q[g].dot(U);
    if (y >= top || y <= fade) continue;
    const wy = smooth((top - y) / ramp) * (1 - smooth((hold - y) / (hold - fade)));
    // Most where the cloth faces forward, some at the sides of the hips (the tails cap it
    // there), none behind; and not over the fly, between the thighs' fronts.
    const wn = smooth((dir[g].dot(F) + 0.35) / 0.6) * smooth((Math.abs(Q[g].clone().sub(frame.O).dot(frame.L)) - 0.03 * scale) / (0.05 * scale));
    amount[g] = FULL_M * scale * wy * wn;
  }
  // Smoothed over the cloth's own neighbours, so the decimated facets do not ripple it.
  const nbr = Array.from({ length: G }, () => new Set());
  for (const tr of S.tris) { const q = tr.map((i) => S.groupOf[i]); for (let c = 0; c < 3; c++) { nbr[q[c]].add(q[(c + 1) % 3]); nbr[q[c]].add(q[(c + 2) % 3]); } }
  for (let it = 0; it < 3; it++) {
    const next = Float64Array.from(amount);
    for (let g = 0; g < G; g++) { if (!nbr[g].size) continue; let s = 0; for (const o of nbr[g]) s += amount[o]; next[g] = 0.5 * amount[g] + 0.5 * s / nbr[g].size; }
    for (let g = 0; g < G; g++) { const y = Q[g].dot(U); amount[g] = y >= top ? 0 : next[g]; }
  }
  const near = coverHash(over), list = [];
  const moved = new Uint8Array(G);
  for (let g = 0; g < G; g++) {
    let d = amount[g];
    if (!(d > 2e-4)) continue;
    // Never out through a garment worn over it: COVER_GAP_M inside any of it that was outside.
    for (const c of near(Q[g], list)) {
      const was = v.subVectors(c, Q[g]);
      const along = was.dot(dir[g]), off = Math.sqrt(Math.max(0, was.lengthSq() - along * along));
      if (along <= 1e-4 || off > 0.012) continue;
      d = Math.min(d, Math.max(0, along - COVER_GAP_M));
    }
    if (!(d > 2e-4)) continue;
    Q[g].addScaledVector(dir[g], d); moved[g] = 1;
  }
  return moved;
}

/** 2. The taper: each leg's section drawn in from the knee to the hem, round the leg and shoe. */
function taperLegs(S, Q, frame, inside, lod = 0) {
  const { legs, U, L, scale } = frame, G = Q.length, moved = new Uint8Array(G);
  const BINS = 36, ROW = 0.01;
  for (const s of ['l', 'r']) {
    const { K, A } = legs[s], sign = s === 'l' ? 1 : -1;
    const axis = K.clone().sub(A).normalize(), hK = K.clone().sub(A).dot(axis);
    const u0 = new THREE.Vector3().copy(frame.F).addScaledVector(axis, -frame.F.dot(axis)).normalize(), w0 = new THREE.Vector3().crossVectors(axis, u0);
    const polar = (p) => { const d = p.clone().sub(A), h = d.dot(axis); d.addScaledVector(axis, -h); return { h, r: d.length(), a: Math.atan2(d.dot(w0), d.dot(u0)), d }; };
    const binOf = (a) => ((Math.round((a / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;
    // What is inside the trousers on this leg: the body and the shoes, by angle and height.
    const floor = new Map();
    for (const P of inside) for (const p of P) {
      if (sign * p.clone().sub(frame.O).dot(L) <= 0.01 * scale) continue;
      const q = polar(p);
      if (q.h > hK + 0.05 || q.r > 0.3) continue;
      const k = `${binOf(q.a)},${Math.round(q.h / ROW)}`;
      floor.set(k, Math.max(floor.get(k) ?? 0, q.r));
    }
    // A far level's rings stand further apart: the leg between them is under the span too.
    const reach = [1, 1, 3, 6][lod] ?? 6;
    const floorAt = (a, h) => {
      const b = binOf(a), r = Math.round(h / ROW); let m = 0;
      for (let db = -2; db <= 2; db++) for (let dr = -reach; dr <= reach; dr++) m = Math.max(m, floor.get(`${(b + db + BINS) % BINS},${r + dr}`) ?? 0);
      return m;
    };
    const hStart = hK + 0.04 * scale, hFull = TAPER_FULL_M * scale;
    // The cloth's own outline at each angle and height (its outermost layer, a hem's turn-up
    // inside it): every layer there is drawn in by the same share, so none crosses another.
    const mineG = [];
    for (let g = 0; g < G; g++) {
      if (sign * Q[g].clone().sub(frame.O).dot(L) <= 0.005 * scale) continue;
      const q = polar(Q[g]);
      if (q.h < hStart && q.r > 1e-4) mineG.push([g, q]);
    }
    const outer = new Map();
    for (const [, q] of mineG) { const k = `${binOf(q.a)},${Math.round(q.h / ROW)}`; outer.set(k, Math.max(outer.get(k) ?? 0, q.r)); }
    const outerAt = (a, h) => {
      const b = binOf(a), r = Math.round(h / ROW); let m = 0;
      for (let db = -1; db <= 1; db++) for (let dr = -1; dr <= 1; dr++) m = Math.max(m, outer.get(`${(b + db + BINS) % BINS},${r + dr}`) ?? 0);
      return m;
    };
    for (const [g, q] of mineG) {
      const k = 1 - (1 - TAPER_MIN) * smooth((hStart - q.h) / (hStart - hFull));
      const ro = Math.max(q.r, outerAt(q.a, q.h));
      // Clear of the shin by CLEAR_M; at the hem, below the ankle, it lies on the shoe (HEM_CLEAR_M).
      // A simplified level's few rings sag between their points: it stands that much further off.
      const clear = (HEM_CLEAR_M + (CLEAR_M - HEM_CLEAR_M) * smooth(q.h / (0.04 * scale)) + (FAR_CLEAR_M[lod] ?? FAR_CLEAR_M.at(-1))) * scale;
      const share = Math.min(1, Math.max(k, (floorAt(q.a, q.h) + clear) / ro));
      const want = q.r * share;
      if (want >= q.r - 2e-4) continue;
      Q[g].addScaledVector(q.d.normalize(), want - q.r); moved[g] = 1;
    }
  }
  return moved;
}

/** 3. Pleats down the front of each thigh, from under the waistcoat's hem. */
function pleats(mesh, S, Q, frame, wcLow, lod) {
  const { legs, O, U, L, F, scale } = frame;
  const rows = lod === 0 ? 14 : 9, across = PLEAT_ACROSS;
  // The cloth as it now is, near the front of the hips and thighs.
  const P = S.P.map((_, i) => Q[S.groupOf[i]]);
  const y0 = wcLow - 0.003 * scale, y1 = y0 - PLEAT_DOWN_M * scale;
  // The cloth's triangles in front of the hips, each with its span in height, cast a row at a time.
  const span = [];
  for (const tr of S.tris) {
    const ys = tr.map((i) => P[i].dot(U)), lo = Math.min(...ys), hi = Math.max(...ys);
    if (hi < y1 - 0.03 || lo > y0 + 0.03 || !tr.some((i) => P[i].clone().sub(O).dot(F) > -0.02)) continue;
    span.push({ tr, lo, hi });
  }
  const rowTris = (y) => span.filter((x) => x.lo <= y + 0.004 && x.hi >= y - 0.004).map((x) => x.tr);
  const hipY = O.dot(U), lowY = hipY - 0.14 * scale;
  const pts = [], W = [], UV = [], index = [], outward = [];
  for (const s of ['l', 'r']) {
    const sign = s === 'l' ? 1 : -1, leg = legs[s];
    for (let k = 0; k < PLEATS; k++) {
      const top = (20 + 11 * k) * Math.PI / 180, bot = (-22 + 18 * k) * Math.PI / 180;
      const base = pts.length;
      for (let r = 0; r < rows; r++) {
        const v = r / (rows - 1), y = y0 + (y1 - y0) * v;
        const m = smooth((hipY - y) / (hipY - lowY));
        // The ray's origin goes from the middle of the hips to the leg's own axis below the fork.
        const o = O.clone().addScaledVector(U, y - O.dot(U)).lerp(leg.H.clone().addScaledVector(U, y - leg.H.dot(U)), m);
        const phi = top + (bot - top) * m;
        const H = PLEAT_M * scale * smooth(v / 0.1) * (1 - smooth((v - 0.2) / 0.8));
        const half = (PLEAT_HALF_M + PLEAT_SPREAD_M * v) * scale;
        const dirAt = (a) => new THREE.Vector3().addScaledVector(F, Math.cos(a)).addScaledVector(L, sign * Math.sin(a)).normalize();
        const tris = rowTris(y), crest = castRay(o, dirAt(phi), tris, P, 0.4, true);
        if (!crest) return null;
        across.forEach((u, j) => {
          const d = dirAt(phi + (u * half) / crest.t), hit = castRay(o, d, tris, P, 0.4, true) ?? crest;
          const [a, b, c] = hit.tri, wa = 1 - hit.u - hit.v;
          const at = P[a].clone().multiplyScalar(wa).addScaledVector(P[b], hit.u).addScaledVector(P[c], hit.v);
          const fn = new THREE.Vector3().subVectors(P[b], P[a]).cross(new THREE.Vector3().subVectors(P[c], P[a])).normalize();
          if (fn.dot(d) < 0) fn.negate();
          const lift = PLEAT_LIFT_M * scale + H * PLEAT_PROFILE[j];
          pts.push(at.addScaledVector(fn, lift));
          const h = atHit(mesh, S, hit); W.push(h.weights); UV.push(h.uv);
          outward.push(fn);
        });
      }
      const n = across.length;
      for (let r = 0; r < rows - 1; r++) for (let c = 0; c < n - 1; c++) {
        const a = base + r * n + c, b = a + 1, d = a + n, e = d + 1;
        index.push(a, d, b, b, d, e);
      }
    }
  }
  orient(index, pts, (_, t) => outward[index[t * 3]]);
  return { key: 'pleats', P: pts, index, W, UV };
}

/** 4. A strap under each shoe's waist, of the trousers' cloth, on the foot bone. */
function straps(mesh, S, Q, frame, shoes, lod) {
  const { legs, U, L, F, scale } = frame;
  const SH = survey(shoes, false), boneIdx = new Map(mesh.skeleton.bones.map((b, i) => [b?.name, i]));
  const P = S.P.map((_, i) => Q[S.groupOf[i]]);
  const pts = [], W = [], index = [], centre = [];
  const step = (lod >= 2 ? 0.012 : 0.006) * scale, w = (STRAP_W_M / 2) * scale, th = STRAP_T_M * scale;
  for (const s of ['l', 'r']) {
    const { A, B } = legs[s], sign = s === 'l' ? 1 : -1;
    const fwd = B.clone().sub(A); fwd.addScaledVector(U, -fwd.dot(U)).normalize();
    const lat = new THREE.Vector3().crossVectors(U, fwd).normalize().multiplyScalar(sign); // out, away from the other foot
    if (lat.dot(L) * sign < 0) lat.negate();
    const at = A.clone().addScaledVector(fwd, STRAP_AT_M * scale);
    const near = trisIn(SH.tris, SH.P, at.clone().addScaledVector(new THREE.Vector3(1, 1, 1), -0.2), at.clone().addScaledVector(new THREE.Vector3(1, 1, 1), 0.2));
    let sole = Infinity;
    for (const p of SH.P) if (sign * p.clone().sub(frame.O).dot(L) > 0) sole = Math.min(sole, p.dot(U));
    // The hem at each side of the shoe, at the strap: the trousers' lowest cloth there.
    const hemAt = (side) => {
      let lo = Infinity;
      const o = at.clone().addScaledVector(lat, side * 0.03 * scale);
      for (const p of P) { const d = p.clone().sub(o); if (Math.abs(d.dot(fwd)) < 0.02 * scale && d.dot(lat) * side > -0.01 * scale && sign * p.clone().sub(frame.O).dot(L) > 0) lo = Math.min(lo, p.dot(U)); }
      return lo;
    };
    const sideOf = (side, y) => {
      const o = at.clone().addScaledVector(U, y - at.dot(U)), hit = castRay(o, lat.clone().multiplyScalar(side), near, SH.P, 0.15, true);
      return hit ? hit.t : null;
    };
    // The path round the shoe's waist in the plane across the foot: down the outer side,
    // under the sole, up the inner side. Each point with its outward direction in the plane.
    const path = [];
    // The strap's outer face under the sole stays 1.2 mm above the sole: the far levels' sole
    // is the lowest point their quantized positions can hold.
    const bottom = sole + (0.002 + STRAP_T_M) * scale;
    for (const side of [1, -1]) {
      const topY = hemAt(side) + 0.012 * scale, list = [];
      let last = null;
      for (let y = topY; y > bottom; y -= step) { const r = sideOf(side, y) ?? last; if (r !== null) { list.push([y, r]); last = r; } }
      const rb = sideOf(side, bottom + 0.006 * scale) ?? last ?? 0.04 * scale;
      list.push([bottom, rb]);
      // Smoothed down the side, so the shoe's facets do not kink the strap.
      const sm = list.map(([y], i) => [y, (list[Math.max(0, i - 1)][1] + list[i][1] + list[Math.min(list.length - 1, i + 1)][1]) / 3]);
      const pts2 = sm.map(([y, r]) => ({ p: at.clone().addScaledVector(U, y - at.dot(U)).addScaledVector(lat, side * r), out: lat.clone().multiplyScalar(side) }));
      if (side === 1) path.push(...pts2); else path.push(...pts2.reverse());
      if (side === 1) {
        // Under the sole, across from the outer foot of the side to the inner.
        const ri = sideOf(-1, bottom + 0.006 * scale) ?? rb;
        for (let k = 1; k < 5; k++) { const f = k / 5; path.push({ p: at.clone().addScaledVector(U, bottom - at.dot(U)).addScaledVector(lat, rb * (1 - f) - ri * f), out: U.clone().negate() }); }
      }
    }
    // A closed flat section at each point of the path: inner and outer face, both edges.
    const base = pts.length, n = path.length;
    const cen = at.clone();
    // On the foot bone below the hem; inside it, where it is sewn on, the hem's own weights
    // (so the skirt rig and every other reader see a garment on the leg, and the top stays in).
    const foot = { [boneIdx.get(`foot_${s}`)]: 1 };
    const hemW = (p) => {
      let best = -1, bd = Infinity;
      for (let i = 0; i < P.length; i++) { const d = P[i].distanceToSquared(p); if (d < bd && sign * P[i].clone().sub(frame.O).dot(L) > 0) { bd = d; best = i; } }
      return best >= 0 ? weightsOf(mesh, best) : foot;
    };
    const hy = Math.min(hemAt(1), hemAt(-1));
    for (const { p, out } of path) {
      const k = smooth((p.dot(U) - (hy - 0.005 * scale)) / (0.017 * scale));
      const wts = k > 0 ? mix([[hemW(p), k], [foot, 1 - k]]) : foot;
      for (const [o, e] of [[0.0008, -1], [0.0008 + th, -1], [0.0008 + th, 1], [0.0008, 1]]) {
        pts.push(p.clone().addScaledVector(out, o * scale).addScaledVector(fwd, e * w));
        W.push(wts);
        centre.push(p.clone().addScaledVector(out, (0.0008 + th / 2) * scale));
      }
    }
    for (let k = 0; k < n - 1; k++) for (let c = 0; c < 4; c++) {
      const a = base + k * 4 + c, b = base + k * 4 + ((c + 1) % 4), d = a + 4, e = b + 4;
      index.push(a, b, d, b, e, d);
    }
    for (const k of [0, n - 1]) { const r = base + k * 4; index.push(r, r + 1, r + 2, r, r + 2, r + 3); }
    void cen;
  }
  // Outward: away from the strap's own middle line at that point of the path.
  orient(index, pts, (c, t) => c.clone().sub(centre[index[t * 3]]).add(c.clone().sub(centre[index[t * 3 + 1]])).add(c.clone().sub(centre[index[t * 3 + 2]])));
  return { key: 'straps', P: pts, index, W, UV: null };
}

/** Two meshes on one skeleton (bone for bone) and one bind: a piece's weights mean the same on both. */
const sameRig = (a, b) => a.skeleton.bones.length === b.skeleton.bones.length && a.skeleton.bones.every((x, i) => x === b.skeleton.bones[i]) && a.bindMatrix.equals(b.bindMatrix);

function tailorTrousers(root, assetId, spec, report) {
  const byLod = new Map();
  root.traverse((o) => {
    if (!o.isSkinnedMesh || !o.skeleton) return;
    const p = pieceOf(o, assetId), l = lodOf(o);
    if (!byLod.has(l)) byLod.set(l, {});
    const e = byLod.get(l);
    if (p === spec.trousers) e.trousers = o;
    else if (p === spec.shoes) e.shoes = o;
    else if (p === spec.body) e.body = o;
    else if (spec.over.includes(p)) (e.over ??= []).push(o);
  });
  for (const [lod, e] of byLod) {
    const mesh = e.trousers;
    if (!mesh || !e.shoes || !e.body) continue;
    const frame = legsOf(mesh);
    if (!frame) continue;
    const S = survey(mesh), Q = S.first.map((i) => S.P[i].clone());
    const over = e.over ?? [];
    // The waistcoat's hem at the front: where the trousers begin to show.
    let wcLow = Infinity;
    for (const m of over) {
      if (!/waistcoat/.test(pieceOf(m, assetId))) continue;
      for (const p of survey(m, false).P) { const d = p.clone().sub(frame.O); if (d.dot(frame.F) > 0 && Math.abs(Math.atan2(d.dot(frame.L), d.dot(frame.F))) < 0.7) wcLow = Math.min(wcLow, p.dot(frame.U)); }
    }
    if (!Number.isFinite(wcLow)) wcLow = frame.O.dot(frame.U) + 0.07 * frame.scale;
    const full = fullFront(mesh, S, Q, frame, over, wcLow);
    const taper = taperLegs(S, Q, frame, [survey(e.body, false).P, survey(e.shoes, false).P], lod);
    const moved = full.map((x, g) => x | taper[g]);
    const Q0 = S.first.map((i) => S.P[i]);
    commit(mesh, S, Q, moved);
    let far = 0, nf = 0, nt = 0;
    for (let g = 0; g < Q.length; g++) if (moved[g]) { far = Math.max(far, Q[g].distanceTo(Q0[g])); nf += full[g]; nt += taper[g]; }
    // The pleats and the straps in the trousers' own mesh (a strap of their cloth, in the
    // wearer's own trouser colour); with STRAP_LEATHER the straps go in the shoes' mesh
    // instead (one skeleton and bind for both, so the strap's weights carry over as they are).
    const strap = straps(mesh, S, Q, frame, e.shoes, lod), leather = STRAP_LEATHER && sameRig(mesh, e.shoes);
    const made = Object.keys(appendPieces(mesh, [lod <= 1 ? pleats(mesh, S, Q, frame, wcLow, lod) : null, leather ? null : strap]).parts);
    if (leather) made.push(...Object.keys(appendPieces(e.shoes, [strap]).parts));
    report.push({ mesh: mesh.name, kind: 'trousers', full: nf, taper: nt, max_m: far, added: made });
  }
}

// ---------------------------------------------------------------------------------------------
// Mahoney's shirt.

function armsOf(mesh) {
  const arms = {};
  for (const s of ['l', 'r']) {
    const E = bonePos(mesh, `lowerarm_${s}`), Wr = bonePos(mesh, `hand_${s}`);
    if (!E || !Wr) return null;
    const fore = Wr.clone().sub(E).normalize();
    const u = new THREE.Vector3(0, 1, 0).addScaledVector(fore, -fore.y);
    if (u.lengthSq() < 1e-6) u.set(0, 0, 1).addScaledVector(fore, -fore.z);
    u.normalize();
    arms[s] = { E, W: Wr, fore, u, w: new THREE.Vector3().crossVectors(fore, u), len: E.distanceTo(Wr) };
  }
  return arms;
}
/** Each vertex's arm side ('l', 'r' or null) by its arm and hand weights. */
function armSides(mesh, first) {
  const names = mesh.skeleton.bones.map((b) => b?.name ?? '');
  const sideOfBone = names.map((n) => (/^(upperarm|lowerarm|hand|thumb|index|middle|ring|pinky)(_\d+)?_(l|r)$/.exec(n)?.[3] ?? null));
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  return first.map((i) => {
    let l = 0, r = 0;
    for (let k = 0; k < 4; k++) { const b = sideOfBone[si.getComponent(i, k)], w = sw.getComponent(i, k); if (b === 'l') l += w; else if (b === 'r') r += w; }
    return l > 0.5 ? 'l' : r > 0.5 ? 'r' : null;
  });
}

/** Mahoney's shirt material drawn white linen (once): its colour over its flat picture. */
export function whitenShirt(material) {
  if (!material || material.userData.chicagoLinenWhite) return false;
  const lin = (rgb) => rgb.map(srgbToLinear), pic = lin(SHIRT_PICTURE_SRGB), want = lin(LINEN_SRGB);
  if (material.map) material.color.setRGB(want[0] / pic[0], want[1] / pic[1], want[2] / pic[2], THREE.LinearSRGBColorSpace);
  else material.color.setRGB(want[0], want[1], want[2], THREE.LinearSRGBColorSpace);
  material.userData.chicagoLinenWhite = true;
  return true;
}

function tailorShirt(root, assetId, spec, report) {
  const byLod = new Map();
  root.traverse((o) => {
    if (!o.isSkinnedMesh || !o.skeleton) return;
    const p = pieceOf(o, assetId), l = lodOf(o);
    if (!byLod.has(l)) byLod.set(l, {});
    if (p === spec.shirt) byLod.get(l).shirt = o;
    else if (p === spec.body) byLod.get(l).body = o;
  });
  for (const [lod, e] of byLod) {
    const mesh = e.shirt;
    if (!mesh || !e.body) continue;
    const white = whitenShirt(mesh.material);
    const arms = armsOf(mesh);
    if (!arms) continue;
    const S = survey(mesh), BS = survey(e.body, false), G = S.first.length;
    const sideG = armSides(mesh, S.first);
    const bodySide = armSides(e.body, BS.first);
    const Q = S.first.map((i) => S.P[i].clone()), moved = new Uint8Array(G), v0 = new THREE.Vector3();
    const sides = lod === 0 ? 48 : lod === 1 ? 32 : lod === 2 ? 18 : 12;
    const folds = lod <= 1;
    const rowsUp = lod === 0 ? 16 : lod === 1 ? 10 : 6;
    const bandPts = [], bandW = [], bandUV = [], bandIdx = [], bandCentre = [];
    const gPts = [], gW = [], gUV = [], gIdx = [], gCentre = [];
    for (const s of ['l', 'r']) {
      const a = arms[s];
      const polar = (p) => { const d = p.clone().sub(a.E), t = d.dot(a.fore); d.addScaledVector(a.fore, -t); return { t, r: d.length(), th: Math.atan2(d.dot(a.w), d.dot(a.u)), d }; };
      const mine = [];
      for (let g = 0; g < G; g++) if (sideG[g] === s) { const q = polar(S.P[S.first[g]]); if (q.t > 0) mine.push([g, q]); }
      if (!mine.length) continue;
      const tEnd = Math.max(...mine.map(([, q]) => q.t));
      if (tEnd < a.len * 0.7) continue;
      const tBand = tEnd - BAND_M, tTop = FOLD_TOP_M;
      // The sleeve's triangles on this forearm, for casting.
      // The sleeve's triangles on this forearm, each with its span along the arm, for casting a
      // ring at a time (only those that reach the ring's place).
      const tAt = S.P.map((p) => v0.subVectors(p, a.E).dot(a.fore));
      const tris = [];
      for (const tr of S.tris) {
        if (!tr.every((i) => sideG[S.groupOf[i]] === s)) continue;
        const lo = Math.min(tAt[tr[0]], tAt[tr[1]], tAt[tr[2]]), hi = Math.max(tAt[tr[0]], tAt[tr[1]], tAt[tr[2]]);
        if (hi > tTop - 0.03) tris.push({ tr, lo, hi });
      }
      const ringTris = new Map();
      const trisAt = (t) => { const k = Math.round(t * 500); let l = ringTris.get(k); if (!l) ringTris.set(k, (l = tris.filter((x) => x.lo <= t + 0.002 && x.hi >= t - 0.002).map((x) => x.tr))); return l; };
      const BINS = sides;
      const thOf = (k) => (k / BINS) * Math.PI * 2 - Math.PI;
      const dirAt = (th) => a.u.clone().multiplyScalar(Math.cos(th)).addScaledVector(a.w, Math.sin(th));
      const castAt = (t, th) => castRay(a.E.clone().addScaledVector(a.fore, t), dirAt(th), trisAt(t), S.P, 0.2, true);
      // The band: round the sleeve's end and the wrist inside it, a little eased, smoothed round.
      const rb = new Float64Array(BINS);
      for (const [, q] of mine) if (q.t >= tBand - 0.004) { const k = ((Math.round(((q.th + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS; rb[k] = Math.max(rb[k], q.r + 0.002); }
      for (let g = 0; g < BS.first.length; g++) {
        if (bodySide[g] !== s) continue;
        const q = polar(BS.P[BS.first[g]]);
        if (q.t < tBand - 0.005 || q.t > tEnd + 0.004) continue;
        const k = ((Math.round(((q.th + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS; rb[k] = Math.max(rb[k], q.r + BAND_EASE_M);
      }
      const mean = rb.reduce((x, y) => x + y, 0) / BINS;
      for (let k = 0; k < BINS; k++) if (!(rb[k] > 0)) rb[k] = mean;
      const rBand = Array.from(rb, (_, k) => { let m = 0; for (let d = -2; d <= 2; d++) m = Math.max(m, rb[(k + d + BINS) % BINS]); return m; });
      for (let it = 0; it < 2; it++) { const c = rBand.slice(); for (let k = 0; k < BINS; k++) rBand[k] = (c[(k + BINS - 1) % BINS] + 2 * c[k] + c[(k + 1) % BINS]) / 4; }
      // The band's weights: the sleeve's at its end, one set round the arm (fitSleeves').
      const ring = mix(mine.filter(([, q]) => q.t >= tBand).map(([g]) => [weightsOf(mesh, S.first[g]), 1 / Math.max(1, mine.filter(([, q]) => q.t >= tBand).length)]));
      const hemUV = (() => { const uv = mesh.geometry.attributes.uv; if (!uv) return [0, 0]; const i = S.first[mine.reduce((b, x) => (x[1].t > b[1].t ? x : b))[0]]; return [uv.getX(i), uv.getY(i)]; })();
      // Its section: inner and outer face, rolled at both edges (a closed ring).
      const bt = BAND_T_M, t0 = tBand, t1 = tEnd + 0.002;
      const sect = [[t0, -bt], [t0 + 0.002, 0], [t1 - 0.002, 0], [t1, -bt]];
      // Each face of the section (its foot, outer face, top, inner face) with its own points,
      // so the corners stay sharp and each face is lit as itself.
      const ns = sect.length;
      for (let j = 0; j < ns; j++) {
        const b0 = bandPts.length;
        for (const [t, dr] of [sect[j], sect[(j + 1) % ns]]) for (let k = 0; k < BINS; k++) {
          const th = thOf(k), r = rBand[k] + dr;
          bandPts.push(a.E.clone().addScaledVector(a.fore, t).addScaledVector(dirAt(th), r));
          bandW.push(ring); bandUV.push(hemUV); bandCentre.push(a.E.clone().addScaledVector(a.fore, (t0 + t1) / 2).addScaledVector(dirAt(th), rBand[k] - bt / 2));
        }
        for (let k = 0; k < BINS; k++) {
          const p = b0 + k, q = b0 + ((k + 1) % BINS), p2 = p + BINS, q2 = q + BINS;
          bandIdx.push(p, p2, q, q, p2, q2);
        }
      }
      // The gathers: the sleeve's own surface, eased off it, bloused over the band and drawn
      // into it in folds that run on up the forearm. Rows up from inside the band's top.
      const g0 = gPts.length, tFoot = tBand + 0.004, rowsT = [];
      const tPuff = tBand - GATHER_M;
      for (let j = 0; j <= 3; j++) rowsT.push(tFoot - (j / 3) * (0.004 + 0.016));            // into the band
      const tAbove = tBand - 0.016;
      for (let j = 1; j <= rowsUp; j++) rowsT.push(tAbove - (j / rowsUp) * (tAbove - tTop));
      const surfR = rowsT.map((t) => Array.from({ length: BINS }, (_, k) => castAt(Math.max(t, tTop), thOf(k))));
      for (let j = 0; j < rowsT.length; j++) {
        // Fill a missed cast from its neighbours round the arm.
        const row = surfR[j];
        for (let k = 0; k < BINS; k++) if (!row[k]) { for (let d = 1; d < BINS; d++) { const o = row[(k + d) % BINS] ?? row[(k - d + BINS) % BINS]; if (o) { row[k] = o; break; } } }
      }
      for (let j = 0; j < rowsT.length; j++) {
        const t = rowsT[j];
        const up = (tBand - t) / (tBand - tPuff);                     // 0 at the band's top, 1 at the puff's top
        const intoBand = t > tBand - 0.016;                           // the last 1.6 cm drawn into the band
        // Gathers deepest at the band, easing to the soft folds up the forearm, gone at the top.
        const fold = folds ? (intoBand ? GATHER_DEEP_M : GATHER_DEEP_M + (FOLD_M - GATHER_DEEP_M) * smooth(up)) : 0;
        const topFade = smooth((t - tTop) / 0.04);
        for (let k = 0; k < BINS; k++) {
          const th = thOf(k), hit = surfR[j][k];
          const rs = hit ? hit.t : rBand[k];
          const ripple = 0.5 + 0.5 * Math.cos(GATHER_FOLDS * th + 0.9 * Math.sin(3 * th) + 2.2 * up);
          let r;
          if (intoBand) {
            const f = smooth((tBand + 0.004 - t) / 0.02);                 // 0 inside the band, 1 at 1.6 cm above it
            r = rBand[k] - bt - 0.001 + f * (Math.max(rs, rBand[k]) + GATHER_LIFT_M + PUFF_M * 0.6 - (rBand[k] - bt - 0.001)) + fold * ripple * f;
          } else {
            const puff = PUFF_M * (1 - smooth((up - 0.35) / 0.65));
            r = Math.max(rs, rBand[k]) * (1 - smooth(up / 0.6)) + rs * smooth(up / 0.6) + (GATHER_LIFT_M + puff) * 1 + fold * ripple * topFade;
          }
          gPts.push(a.E.clone().addScaledVector(a.fore, t).addScaledVector(dirAt(th), r));
          let wts = ring, uv = hemUV;
          if (hit && !intoBand) { const h = atHit(mesh, S, hit); const kb = 1 - smooth((tBand - t) / 0.03); wts = mix([[h.weights, 1 - kb], [ring, kb]]); uv = h.uv; }
          gW.push(wts); gUV.push(uv); gCentre.push(a.E.clone().addScaledVector(a.fore, t));
        }
      }
      for (let j = 0; j < rowsT.length - 1; j++) for (let k = 0; k < BINS; k++) {
        const p = g0 + j * BINS + k, q = g0 + j * BINS + ((k + 1) % BINS), p2 = p + BINS, q2 = q + BINS;
        gIdx.push(p, p2, q, q, p2, q2);
      }
      // The sleeve stays inside: under the band, and under the gathers where they draw in.
      const gRows = rowsT.map((t, j) => ({ t, r: Array.from({ length: BINS }, (_, k) => gPts[g0 + j * BINS + k].clone().sub(a.E).addScaledVector(a.fore, -t).length()) }));
      const capAt = (t, th) => {
        const k = ((Math.round(((th + Math.PI) / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;
        if (t >= tFoot - 0.001) return rBand[k] - bt - 0.0015;
        let best = Infinity;
        for (let j = 0; j < gRows.length - 1; j++) {
          const A0 = gRows[j], A1 = gRows[j + 1];
          if (t <= A0.t && t >= A1.t) {
            const f = (A0.t - t) / Math.max(1e-6, A0.t - A1.t);
            for (let d = -1; d <= 1; d++) { const kk = (k + d + BINS) % BINS; best = Math.min(best, A0.r[kk] * (1 - f) + A1.r[kk] * f); }
            return best - 0.0015;
          }
        }
        return Infinity;
      };
      // ...but never onto the wrist inside it.
      const bodyFloor = new Map();
      for (let g = 0; g < BS.first.length; g++) {
        if (bodySide[g] !== s) continue;
        const q = polar(BS.P[BS.first[g]]); if (q.t < tTop || q.t > tEnd + 0.01) continue;
        const key = `${Math.round(q.t / 0.01)},${((Math.round(((q.th + Math.PI) / (2 * Math.PI)) * 24) % 24) + 24) % 24}`;
        bodyFloor.set(key, Math.max(bodyFloor.get(key) ?? 0, q.r));
      }
      const floorAt = (t, th) => { const b = ((Math.round(((th + Math.PI) / (2 * Math.PI)) * 24) % 24) + 24) % 24, r = Math.round(t / 0.01); let m = 0; for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) m = Math.max(m, bodyFloor.get(`${r + x},${(b + y + 24) % 24}`) ?? 0); return m; };
      for (const [g, q] of mine) {
        if (q.t < tTop) continue;
        const cap = Math.max(capAt(q.t, q.th), floorAt(q.t, q.th) + 0.002);
        if (q.r <= cap) continue;
        Q[g].addScaledVector(q.d.clone().normalize(), cap - q.r); moved[g] = 1;
      }
    }
    if (moved.some((x) => x)) commit(mesh, S, Q, moved);
    const pieces = [];
    if (bandPts.length) {
      orient(bandIdx, bandPts, (c, t) => c.clone().sub(bandCentre[bandIdx[t * 3]]));
      pieces.push({ key: 'wristbands', P: bandPts, index: bandIdx, W: bandW, UV: bandUV });
    }
    if (gPts.length && lod <= 2) {
      orient(gIdx, gPts, (c, t) => c.clone().sub(gCentre[gIdx[t * 3]]));
      pieces.push({ key: 'gathers', P: gPts, index: gIdx, W: gW, UV: gUV });
    }
    const made = Object.keys(appendPieces(mesh, pieces).parts);
    let pulled = 0; for (const x of moved) pulled += x;
    report.push({ mesh: mesh.name, kind: 'shirt', white, pulled, added: made });
  }
}

/** Tailor a loaded body, once (cloned figures share the result); [] for any other body. */
export function tailor1835(root) {
  if (!root) return null;
  if (root.userData.chicagoTailor1835) return root.userData.chicagoTailor1835;
  let assetId = root.userData?.chicago4d_human?.asset_id ?? null;
  if (!assetId) root.traverse((o) => { if (!assetId && o.isSkinnedMesh) assetId = Object.keys(TAILOR).find((id) => (o.name ?? '').startsWith(`${id}_`)) ?? null; });
  const spec = TAILOR[assetId], report = [];
  if (spec?.trousers) tailorTrousers(root, assetId, spec, report);
  if (spec?.shirt) tailorShirt(root, assetId, spec, report);
  root.userData.chicagoTailor1835 = report;
  return report;
}
