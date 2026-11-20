// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-gown.js — a lady's walking suit of 1904 cut as its pictures show it (T-3553).
 *
 * The catalogue review of Frances Glessner in her 1904 day dress (data/people_match/subjects/
 * glessner_frances_m_1904.match.json), against the Met's 1902 black wool suit, the Easter
 * crowds on Fifth Avenue in 1904 and Mrs. Fairbanks at the cornerstone (F. B. Johnston), found
 * four things a visitor sees at once, and the owner approved fixing them (2026-11-17, "yes do
 * tailoring fixes"):
 *
 *   - the skirt was a bell from the hips, widest at the hem (83 cm across), and read as a
 *     crinoline; the pictures' gored skirts are close over the hips and flare from about the
 *     knee, nearly columnar to the ground;
 *   - it was a smooth shell; the Met skirt shows its gore seams and braid at the hem, and the
 *     Easter skirts break in folds at the hem;
 *   - the standing collar and the front read plain pale grey; the pictures show a tall cream
 *     lace collar and a lace jabot;
 *   - the sleeves ended plain at the wrist; Mrs. Fairbanks wears lace frills there.
 *
 * Here, once per loaded body (before any figure is cloned from it, as human-seat.js and
 * human-waist.js do), for the bodies GOWNS names:
 *
 *   1. the cut: the skirt's every point below HOLD under the hip joints is taken in toward
 *      the body's axis, angle by angle, onto a new outline: the hips' own radius there, plus
 *      a small share of the hem's ease down to the knee and the rest of it below, on a
 *      trumpet's curve (CUT). The hem stands 12 cm off the hips' line in front, 10 at the
 *      sides and 16 behind (a little sweep at the back) instead of 18 to 23 cm.
 *      Above HOLD (the waist, the hips and everything under the jacket's basque) nothing
 *      moves. Standing, the cloth is held CLEAR_M off the legs and shoes as drawn; the
 *      skirt's own driver (human-skirt.js) reads this shape at bind and keeps the legs inside
 *      it on the walk, so the hem breaks forward over the leading foot.
 *   2. the surface: GORES seams, each a valley between two low ridges (a seam pressed open,
 *      SEAM), from under the basque to the hem (the front gore centred, a seam down the
 *      back), deep enough that the light draws a line at three metres in black wool (round
 *      3 drew a 5 mm valley, which read only close up); and below the knee the flare
 *      falling into FLUTE soft folds, one or two to a gore, deeper toward the hem; normals
 *      are taken again from the faces (a hem's or a seam's hard edge kept hard), so the light
 *      draws them. Levels too coarse to carry a fold (fewer than FLUTE.minRing points round)
 *      take the cut only.
 *   3. trims, as fabric.js draws them and human-finery.js measures them, on the asset's own
 *      materials where a person's dress record does not set its own: the collar, the jabot
 *      and the front in cream lace, the shirtwaist's cloth brought up from grey to cream;
 *      braid round the skirt's hem and the coat's cuffs (the Met suit's).
 *   4. at the near levels, a frill of the same lace at each wrist: a short flared ring of
 *      cloth from inside the sleeve's end out over the wrist, skinned as the sleeve's hem is
 *      (human-sleeve.js made it one band) and carried toward the hand at its edge, so it
 *      turns with the wrist.
 *
 * Topology, UVs and skin weights of the asset's meshes are unchanged, except that the frill
 * (both wrists, 288 vertices at the near level, 224 at the next; none past 20 m, FRILL.maxLod)
 * is appended to the shirtwaist's collar piece, whose cloth it is and whose skeleton it shares,
 * as human-regulars.js appends its tape to the crossbelts: the collar's own vertices and
 * triangles come first, unchanged, and no mesh, draw call, material or texture is added (a
 * hundred ladies on Prairie Avenue wear this body; T-3555's phone budget). Cost: a few thousand
 * vertices per level, once per parse (10 to 25 ms in node, beside the 150 ms the coat and
 * sleeve passes take). Every number is a reconstructed authoring choice after the pictures
 * (liberty L-gown-3553 beside L418); no garment of Frances Glessner's is recorded, and every
 * lady who wears this body (the hundred ladies of Prairie Avenue in 1904) wears the cut.
 */
import * as THREE from 'three';
import { finerySpec, fineryNumbers } from './human-finery.js';

const CREAM = Object.freeze([1, 0.96, 0.8]);    // linear: a cream lace, its threads (the net between them draws darker)
const BRAID = Object.freeze([0.028, 0.028, 0.032]); // black silk braid, a little lighter and shinier than the wool

/** The bodies this cut is for, by asset id and their meshes' piece names. */
export const GOWNS = Object.freeze([Object.freeze({
  asset: 'glessner_frances_m_1904',
  skirt: 'gored_skirt',
  sleeves: 'lady_jacket_body',
  lace: 'garment_upper__lady_shirtwaist_white',
  // The piece the wrist frills are appended to: the shirtwaist's own cloth, on the body's skeleton.
  frillHost: 'lady_shirtwaist_collar',
  // The shirtwaist's cloth: its texture is a grey cream (198, 196, 184); this brings it to a
  // cream white under the town's light.
  cream: Object.freeze([1.42, 1.38, 1.27]),
  trims: Object.freeze({
    garment_upper__lady_shirtwaist_white: { trims: [{ kind: 'lace', from: 'top', at_m: 0.095, width_m: 0.19, rgb: CREAM }] },
    garment_lower__lady_skirt_black: { trims: [
      { kind: 'braid', from: 'hem', at_m: 0.045, width_m: 0.035, rgb: BRAID },
      { kind: 'braid', from: 'hem', at_m: 0.1, width_m: 0.022, rgb: BRAID }] },
    garment_outer__lady_jacket_black: { trims: [{ kind: 'braid', from: 'cuff', at_m: 0.03, width_m: 0.04, rgb: BRAID }] },
  }),
})]);

/** The cut, metres per 0.85 m of leg: nothing moves above HOLD under the hip joints; down to
 * the knee the outline takes `kneeShare` of the hem's ease, below it the rest on a curve of
 * `power`; the hem stands `ease` off the hips' line (front, side, back), and the cloth is
 * kept `clearM` off the legs and shoes as drawn. */
export const CUT = Object.freeze({ holdM: 0.17, kneeShare: 0.1, power: 1.6, ease: Object.freeze({ front: 0.12, side: 0.10, back: 0.16 }), clearM: 0.025 });
/** Gores round the skirt, the front one centred. Each seam is drawn as a seam pressed open
 * reads: the seam line a valley `depthM` deep, a ridge `lipM` proud one point of the ring to
 * either side of it (the turnings under the cloth), each `width` of a point of the ring wide,
 * the ridges coming in over `lipInM` under the hold line (so the hips keep their width);
 * the ring's points are what the light can draw, so the profile is laid in them, not in metres
 * (at the near level a seam falls on a column of points: 84 round, 12 to a gore). */
export const GORES = 7;
export const SEAM = Object.freeze({ depthM: 0.010, lipM: 0.005, width: 0.45, fadeM: 0.06, lipInM: 0.12 });
/** A seam's relief (metres per 0.85 m of leg, + outward) at `u` points of the ring from its line. */
export function seamRelief(u, lip = 1) {
  const a = u / SEAM.width, b = (Math.abs(u) - 1) / SEAM.width;
  return -SEAM.depthM * Math.exp(-a * a) + lip * SEAM.lipM * Math.exp(-b * b);
}
/** Folds of the flare below the knee: this deep (crest to mean) at the hem; two to a gore on a
 * level with 80 points round, one on a level with `minRing`, none below. */
export const FLUTE = Object.freeze({ depthM: 0.016, minRing: 40, fullRing: 80, power: 1.5 });
/** The wrist frill: from `insideM` inside the sleeve's end to `outM` past it, flaring `flareM`,
 * in `waves` ruffles `waveM` deep at its edge; its edge carried by the hand at `hand`. Drawn on
 * the levels up to `maxLod` (within 20 m): past that it is a pixel. */
export const FRILL = Object.freeze({ insideM: 0.012, outM: 0.035, flareM: 0.016, waves: 11, waveM: 0.004, tuckM: 0.004, hand: 0.8, maxLod: 1 });

const ADULT_LEG_M = 0.85;
const TAU = Math.PI * 2;
const BINS = 32, OBS_BINS = 48, OBS_ROW_M = 0.01;
const NEEDED = ['pelvis', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r'];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const pieceOf = (mesh, assetId) => (mesh.name ?? '').replace(`${assetId}_`, '').replace(/_lod\d*$/, '');
const lodOf = (mesh) => (mesh.name ?? '').match(/_lod(\d*)$/)?.[1] ?? '';

/** The body's frame at bind from a mesh's skeleton: O mid-hips, U up, L left, F forward. */
export function gownFrame(mesh) {
  const sk = mesh.skeleton, index = new Map(sk.bones.map((b, i) => [b?.name, i]));
  if (!NEEDED.every((n) => index.has(n))) return null;
  const at = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[index.get(n)].clone().invert());
  const hl = at('thigh_l'), hr = at('thigh_r'), al = at('foot_l'), ar = at('foot_r');
  const O = hl.clone().add(hr).multiplyScalar(0.5);
  const U = O.clone().sub(al.clone().add(ar).multiplyScalar(0.5));
  const scale = ((hl.distanceTo(al) + hr.distanceTo(ar)) / 2) / ADULT_LEG_M;
  U.normalize();
  const L = hl.clone().sub(hr); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  const knee = (at('calf_l').sub(O).dot(U) + at('calf_r').sub(O).dot(U)) / 2;
  return { O, U, L, F, scale, knee };
}

/** A mesh's vertices in the frame: x left, y up from the hips, z forward. */
function inFrame(mesh, fr) {
  const pos = mesh.geometry.attributes.position, n = pos.count, out = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(fr.O);
    out[i * 3] = v.dot(fr.L); out[i * 3 + 1] = v.dot(fr.U); out[i * 3 + 2] = v.dot(fr.F);
  }
  return out;
}

/** Every vertex at one place (a UV seam's copies) is one point. */
function weldGroups(P, n) {
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) {
    const k = `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`;
    let g = keys.get(k);
    if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); }
    groupOf[i] = g;
  }
  return { groupOf, first, G: first.length };
}

/** How far the legs and shoes reach from the axis, by angle and height (bind pose), dilated. */
function obstacles(meshes, fr, lo, hi) {
  const rows = Math.max(1, Math.ceil((hi - lo) / OBS_ROW_M) + 1), t = new Float32Array(rows * OBS_BINS);
  for (const m of meshes) {
    const P = inFrame(m, fr), n = P.length / 3;
    for (let i = 0; i < n; i++) {
      const y = P[i * 3 + 1];
      if (y < lo - 0.02 || y > hi + 0.02) continue;
      const r = Math.hypot(P[i * 3], P[i * 3 + 2]), row = clamp(Math.round((y - lo) / OBS_ROW_M), 0, rows - 1);
      const b = ((Math.floor((Math.atan2(P[i * 3], P[i * 3 + 2]) / TAU + 0.5) * OBS_BINS) % OBS_BINS) + OBS_BINS) % OBS_BINS;
      if (r > t[row * OBS_BINS + b]) t[row * OBS_BINS + b] = r;
    }
  }
  return (theta, y) => {
    const row = clamp(Math.round((y - lo) / OBS_ROW_M), 0, rows - 1), b = ((Math.floor((theta / TAU + 0.5) * OBS_BINS) % OBS_BINS) + OBS_BINS) % OBS_BINS;
    let m = 0;
    for (let dr = -2; dr <= 2; dr++) for (let db = -1; db <= 1; db++) {
      const rr = row + dr; if (rr < 0 || rr >= rows) continue;
      m = Math.max(m, t[rr * OBS_BINS + ((b + db + OBS_BINS) % OBS_BINS)]);
    }
    return m;
  };
}

/** The cloth's outer surface as drawn, by angle: its farthest point at each height, between heights linear. */
function envelope(gy, gt, gr, G) {
  const per = Array.from({ length: BINS }, () => []);
  const half = 1.5 * TAU / BINS;
  for (let g = 0; g < G; g++) {
    const b = ((Math.round((gt[g] / TAU) * BINS) % BINS) + BINS) % BINS;
    for (let d = -2; d <= 2; d++) {
      const k = (b + d + BINS) % BINS, c = (k / BINS) * TAU;
      let dt = Math.abs(gt[g] - c) % TAU; if (dt > Math.PI) dt = TAU - dt;
      if (dt <= half) per[k].push([gy[g], gr[g]]);
    }
  }
  const levels = per.map((pts) => {
    pts.sort((a, b) => a[0] - b[0]);
    const out = [];
    for (const [y, r] of pts) {
      const last = out[out.length - 1];
      if (last && y - last[0] < 0.004) { last[1] = Math.max(last[1], r); } else out.push([y, r]);
    }
    return out;
  });
  const at = (k, y) => {
    const L = levels[k];
    if (!L.length) return NaN;
    if (y <= L[0][0]) return L[0][1];
    if (y >= L[L.length - 1][0]) return L[L.length - 1][1];
    let i = 1; while (L[i][0] < y) i++;
    const a = L[i - 1], b = L[i];
    return a[1] + (b[1] - a[1]) * (y - a[0]) / (b[0] - a[0]);
  };
  return (theta, y) => {
    const f = ((theta / TAU) * BINS % BINS + BINS) % BINS, k0 = Math.floor(f) % BINS, k1 = (k0 + 1) % BINS, u = f - Math.floor(f);
    const a = at(k0, y), b = at(k1, y);
    if (!Number.isFinite(a)) return b;
    if (!Number.isFinite(b)) return a;
    return a * (1 - u) + b * u;
  };
}

/** The most points round any one ring of the cloth (a level's resolution round the body). */
function ringPoints(gy, G, lo, hi) {
  const rows = new Map();
  for (let g = 0; g < G; g++) {
    if (gy[g] < lo || gy[g] > hi) continue;
    const k = Math.round(gy[g] / 0.006);
    rows.set(k, (rows.get(k) ?? 0) + 1);
  }
  return Math.max(0, ...rows.values());
}

/** Where the gore seams run: each a meridian of the cloth's own points (a column of the ring)
 * nearest the seam's nominal angle (the front gore centred), so the valley falls on points the
 * light can draw rather than between two of them; the nominal angle where no column is found. */
export function seamLines(gy, gt, G, lo, hi, ring, gores = GORES) {
  const BIN = 0.25 * Math.PI / 180, NB = Math.round(TAU / BIN), hist = new Float64Array(NB);
  for (let g = 0; g < G; g++) if (gy[g] > lo && gy[g] < hi) hist[((Math.round((gt[g] + Math.PI) / BIN) % NB) + NB) % NB]++;
  const reach = Math.floor((TAU / Math.max(ring, 1)) / 2 / BIN);
  const lines = [];
  for (let k = 0; k < gores; k++) {
    const nominal = ((k + 0.5) * TAU / gores + Math.PI) % TAU - Math.PI, b0 = Math.round((nominal + Math.PI) / BIN);
    let best = -1, count = 0;
    for (let db = -reach; db <= reach; db++) {
      const b = ((b0 + db) % NB + NB) % NB, c = hist[b] + 0.5 * (hist[(b + 1) % NB] + hist[(b + NB - 1) % NB]);
      if (c > count || (c === count && Math.abs(db) < Math.abs(best - b0))) { count = c; best = b0 + db; }
    }
    lines.push(count > 2 ? best * BIN - Math.PI : nominal);
  }
  return lines;
}
const angleTo = (th, lines) => { let d = Infinity; for (const s of lines) { let a = Math.abs(th - s) % TAU; if (a > Math.PI) a = TAU - a; if (a < d) d = a; } return d; };

/** The hem's reach past the hips' line at angle theta (0 front, + left). */
export function easeAt(theta, ease = CUT.ease) {
  const c = Math.cos(theta);
  return ease.side + (ease.front - ease.side) * Math.max(c, 0) ** 2 + (ease.back - ease.side) * Math.max(-c, 0) ** 2;
}
/** Share of the hem's ease at u (0 the hold line, 1 the hem), the knee at uK. */
export function flareAt(u, uK, cut = CUT) {
  if (u <= 0) return 0;
  if (u <= uK) return cut.kneeShare * u / uK;
  return cut.kneeShare + (1 - cut.kneeShare) * ((u - uK) / (1 - uK)) ** cut.power;
}

/**
 * Cut one skirt in place onto the gored outline, with its seams and folds. `legs` are the
 * meshes it is kept off standing (the body, the shoes). Returns what it did, or null.
 */
export function cutSkirt(mesh, legs = []) {
  const fr = gownFrame(mesh);
  if (!fr) return null;
  const { O, U, L, F, scale } = fr;
  const geo = mesh.geometry, pos = geo.attributes.position, n = pos.count;
  const P = inFrame(mesh, fr), { groupOf, first, G } = weldGroups(P, n);
  const gx = new Float64Array(G), gy = new Float64Array(G), gz = new Float64Array(G), gr = new Float64Array(G), gt = new Float64Array(G);
  let yHem = Infinity;
  for (let g = 0; g < G; g++) {
    const i = first[g];
    gx[g] = P[i * 3]; gy[g] = P[i * 3 + 1]; gz[g] = P[i * 3 + 2];
    gr[g] = Math.hypot(gx[g], gz[g]); gt[g] = Math.atan2(gx[g], gz[g]);
    yHem = Math.min(yHem, gy[g]);
  }
  const yA = -CUT.holdM * scale;
  if (!(yA - yHem > 0.3 * scale)) return null;   // not a long skirt
  const ref = envelope(gy, gt, gr, G);
  const obs = obstacles(legs, fr, yHem, yA + 0.1);
  const clear = CUT.clearM * scale;
  const uK = clamp((yA - fr.knee) / (yA - yHem), 0.15, 0.7);
  const ring = ringPoints(gy, G, yHem + 0.02, yA);
  const flutes = ring >= FLUTE.fullRing ? 2 * GORES : ring >= FLUTE.minRing ? GORES : 0;
  const seams = ring >= FLUTE.minRing;
  const lines = seams ? seamLines(gy, gt, G, yHem + 0.02, yA, ring) : [];
  // Each fold a little different from the next, smoothly round the body (deterministic).
  const fluteGain = (th) => 1 + 0.2 * Math.sin(3 * th + 0.7) + 0.12 * Math.sin(5 * th + 2.1);
  const out = new Float64Array(G);
  let moved = 0, most = 0;
  const hem = { before: 0, after: 0 };
  for (let g = 0; g < G; g++) {
    const y = gy[g], th = gt[g], r = gr[g];
    out[g] = r;
    if (!(r > 1e-4)) continue;
    let rn = r;
    if (y < yA) {
      const R = ref(th, y), RA = ref(th, yA);
      const u = clamp((yA - y) / (yA - yHem), 0, 1);
      let T = RA + easeAt(th) * scale * flareAt(u, uK);
      T = Math.min(R, Math.max(T, obs(th, y) + clear));
      rn = r * (T / R);
    }
    // The surface: a seam's valley, and the flare's folds below the knee.
    let rel = 0;
    const fade = smooth((yA + SEAM.fadeM * scale - y) / (SEAM.fadeM * scale));
    if (seams && fade > 0) {
      rel += seamRelief(angleTo(th, lines) / (TAU / ring), smooth((yA - y) / (SEAM.lipInM * scale))) * scale * fade;
    }
    if (flutes && y < yA) {
      const u = clamp((yA - y) / (yA - yHem), 0, 1), w = Math.max(0, (u - uK) / (1 - uK)) ** FLUTE.power;
      if (w > 0) {
        // Folds between the seams: the valleys on the seams (and, two to a gore, its middle).
        rel -= FLUTE.depthM * scale * w * fluteGain(th) * Math.cos(flutes * (th - Math.PI / GORES));
      }
    }
    if (rel) {
      const floor = y < yA ? obs(th, y) + 0.6 * clear : 0;
      rn = Math.max(rn + rel, Math.min(rn, floor));
    }
    out[g] = rn;
    if (Math.abs(rn - r) > 1e-5) { moved++; most = Math.max(most, Math.abs(rn - r)); }
    if (y < yHem + 0.012) { hem.before = Math.max(hem.before, r); hem.after = Math.max(hem.after, rn); }
  }
  if (!moved) return { moved: 0, max_m: 0 };
  // Back into the bind space, then the geometry's own.
  const Binv = mesh.bindMatrix.clone().invert(), p = new THREE.Vector3();
  const lim = pos.normalized ? 1 : Infinity;
  const at = (g, k, v) => v.copy(O).addScaledVector(L, gx[g] * k).addScaledVector(U, gy[g]).addScaledVector(F, gz[g] * k);
  const NP = new Float64Array(G * 3);
  for (let g = 0; g < G; g++) {
    const k = gr[g] > 1e-4 ? out[g] / gr[g] : 1;
    at(g, k, p); NP[g * 3] = p.x; NP[g * 3 + 1] = p.y; NP[g * 3 + 2] = p.z;
  }
  for (let i = 0; i < n; i++) {
    const g = groupOf[i];
    p.set(NP[g * 3], NP[g * 3 + 1], NP[g * 3 + 2]).applyMatrix4(Binv);
    pos.setXYZ(i, clamp(p.x, -lim, lim), clamp(p.y, -lim, lim), clamp(p.z, -lim, lim));
  }
  pos.needsUpdate = true;
  renormal(geo, groupOf, G, NP, mesh.bindMatrix);
  geo.computeBoundingBox(); geo.computeBoundingSphere();
  return { moved, max_m: most, hem_before_m: hem.before, hem_after_m: hem.after, flutes, seams: seams ? GORES : 0, ring, seam_deg: lines.map((a) => Math.round(a * 1800 / Math.PI) / 10) };
}

/**
 * Normals from the moved faces (area-weighted, in the bind space), each point's copies
 * sharing one, but a face meets a vertex's normal only on that vertex's side of a hard edge
 * (a hem's turn, a fold's crease the asset drew): within 60 degrees of its own old normal.
 */
function renormal(geo, groupOf, G, NP, B) {
  const nrm = geo.attributes.normal, idx = geo.index, n = groupOf.length;
  if (!nrm) return;
  const Binv = B.clone().invert();
  const old = new Float32Array(n * 3), o = new THREE.Vector3();
  for (let i = 0; i < n; i++) { o.fromBufferAttribute(nrm, i).transformDirection(B); old[i * 3] = o.x; old[i * 3 + 1] = o.y; old[i * 3 + 2] = o.z; }
  const tri = idx ? idx.count / 3 : n / 3;
  // Faces at each vertex (by index), and each face's new normal, and its old one.
  const fn = new Float64Array(tri * 3), fo = new Float64Array(tri * 3);
  const vf = Array.from({ length: G }, () => []);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  for (let t = 0; t < tri; t++) {
    const v = [0, 1, 2].map((k) => (idx ? idx.getX(t * 3 + k) : t * 3 + k));
    const q = v.map((i) => groupOf[i]);
    a.set(NP[q[0] * 3], NP[q[0] * 3 + 1], NP[q[0] * 3 + 2]); b.set(NP[q[1] * 3], NP[q[1] * 3 + 1], NP[q[1] * 3 + 2]); c.set(NP[q[2] * 3], NP[q[2] * 3 + 1], NP[q[2] * 3 + 2]);
    e1.subVectors(b, a).cross(e2.subVectors(c, a));
    fn[t * 3] = e1.x; fn[t * 3 + 1] = e1.y; fn[t * 3 + 2] = e1.z;
    for (const i of v) { fo[t * 3] += old[i * 3]; fo[t * 3 + 1] += old[i * 3 + 1]; fo[t * 3 + 2] += old[i * 3 + 2]; }
    for (const g of new Set(q)) vf[g].push(t);
  }
  // The winding's outward side: the one the asset's normals agree with.
  let agree = 0;
  for (let t = 0; t < tri; t++) agree += Math.sign(fn[t * 3] * fo[t * 3] + fn[t * 3 + 1] * fo[t * 3 + 1] + fn[t * 3 + 2] * fo[t * 3 + 2]);
  const sign = agree < 0 ? -1 : 1, s = new THREE.Vector3(), w = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    o.set(old[i * 3], old[i * 3 + 1], old[i * 3 + 2]);
    s.set(0, 0, 0);
    for (const t of vf[groupOf[i]]) {
      w.set(fo[t * 3], fo[t * 3 + 1], fo[t * 3 + 2]);
      if (w.lengthSq() > 0 && w.normalize().dot(o) < 0.5) continue;
      s.x += fn[t * 3] * sign; s.y += fn[t * 3 + 1] * sign; s.z += fn[t * 3 + 2] * sign;
    }
    if (s.lengthSq() < 1e-20) continue;
    s.normalize().transformDirection(Binv);
    nrm.setXYZ(i, s.x, s.y, s.z);
  }
  nrm.needsUpdate = true;
}

/** The sleeve's end at one wrist, at bind: its centre, axis, the radius round it by angle and its weights. */
function sleeveEnd(mesh, side) {
  const sk = mesh.skeleton, index = new Map(sk.bones.map((b, i) => [b?.name, i]));
  const names = [`lowerarm_${side}`, `hand_${side}`];
  if (!names.every((n) => index.has(n))) return null;
  const at = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[index.get(n)].clone().invert());
  const e = at(names[0]), w = at(names[1]), ax = w.clone().sub(e), len = ax.length();
  ax.normalize();
  const pos = mesh.geometry.attributes.position, si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
  const arm = new Set([index.get(names[0]), index.get(names[1])]);
  const v = new THREE.Vector3(), d = new THREE.Vector3();
  const pts = [];
  let tEnd = -Infinity;
  for (let i = 0; i < pos.count; i++) {
    let aw = 0; for (let c = 0; c < 4; c++) if (arm.has(si.getComponent(i, c))) aw += sw.getComponent(i, c);
    if (aw < 0.5) continue;
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix);
    const t = d.subVectors(v, e).dot(ax);
    if (t < 0.4 * len) continue;
    pts.push([i, t, v.clone()]);
    tEnd = Math.max(tEnd, t);
  }
  const ring = pts.filter((p) => p[1] > tEnd - 0.006);
  if (ring.length < 4) return null;
  const c0 = new THREE.Vector3();
  for (const [, , q] of ring) c0.add(q);
  c0.multiplyScalar(1 / ring.length);
  c0.addScaledVector(ax, tEnd - d.subVectors(c0, e).dot(ax));
  // A frame round the arm: b1 up-ish, b2 across.
  const b1 = new THREE.Vector3(0, 1, 0); b1.addScaledVector(ax, -b1.dot(ax));
  if (b1.lengthSq() < 1e-6) b1.set(0, 0, 1).addScaledVector(ax, -ax.z);
  b1.normalize();
  const b2 = new THREE.Vector3().crossVectors(ax, b1).normalize();
  const around = ring.map(([i, , q]) => { d.subVectors(q, c0); return [Math.atan2(d.dot(b2), d.dot(b1)), Math.hypot(d.dot(b1), d.dot(b2)), i]; }).sort((p, q) => p[0] - q[0]);
  const radius = (phi) => {
    let best = around[0], bd = Infinity;
    for (const p of around) { let dd = Math.abs(p[0] - phi) % TAU; if (dd > Math.PI) dd = TAU - dd; if (dd < bd) { bd = dd; best = p; } }
    return best[1];
  };
  // The hem's weights (one set round the ring since human-sleeve.js), by bone index.
  const wsum = new Map();
  for (const [i] of ring) for (let c = 0; c < 4; c++) { const b = si.getComponent(i, c), x = sw.getComponent(i, c); if (x > 0) wsum.set(b, (wsum.get(b) ?? 0) + x); }
  return { c: c0, ax, b1, b2, radius, weights: wsum, hand: index.get(names[1]) };
}

/**
 * Append geometry given at bind (positions and normals in bind space, skin indices into `from`'s
 * skeleton) to `host`'s own, as human-regulars.js appends its tape to the crossbelts: the host
 * keeps its attributes' kinds (a quantized position stays quantized), its first vertices and
 * triangles as they were, and draws the new ones in the same call, material and texture.
 */
function appendToHost(host, from, { P, N, UV, SI, SW, index }) {
  const g = host.geometry, n0 = g.attributes.position.count, add = P.length / 3;
  const inv = host.bindMatrix.clone().invert(), ni = new THREE.Matrix3().getNormalMatrix(inv);
  // Component by component: a loaded attribute may be interleaved (its array is the whole buffer).
  const GET = ['getX', 'getY', 'getZ', 'getW'], SET = ['setX', 'setY', 'setZ', 'setW'];
  const grow = (attr) => {
    const out = new THREE.BufferAttribute(new attr.array.constructor((n0 + add) * attr.itemSize), attr.itemSize, attr.normalized);
    for (let i = 0; i < n0; i++) for (let c = 0; c < attr.itemSize; c++) out[SET[c]](i, attr[GET[c]](i));
    return out;
  };
  const names = Object.keys(g.attributes), next = Object.fromEntries(names.map((k) => [k, grow(g.attributes[k])]));
  const same = host.skeleton === from.skeleton || (host.skeleton.bones.length === from.skeleton.bones.length && host.skeleton.bones.every((b, i) => b === from.skeleton.bones[i]));
  const boneOf = (j) => (same ? j : Math.max(0, host.skeleton.bones.findIndex((b) => b.name === from.skeleton.bones[j]?.name)));
  const v = new THREE.Vector3();
  for (let i = 0; i < add; i++) {
    const k = n0 + i;
    v.fromArray(P, i * 3).applyMatrix4(inv); next.position.setXYZ(k, v.x, v.y, v.z);
    if (next.normal) { v.fromArray(N, i * 3).applyMatrix3(ni).normalize(); next.normal.setXYZ(k, v.x, v.y, v.z); }
    if (next.uv) next.uv.setXY(k, UV[i * 2], UV[i * 2 + 1]);
    if (next.skinIndex && next.skinWeight) for (let c = 0; c < 4; c++) { next.skinIndex[SET[c]](k, boneOf(SI[i * 4 + c])); next.skinWeight[SET[c]](k, SW[i * 4 + c]); }
  }
  for (const name of names) g.setAttribute(name, next[name]);
  const old = g.index ? g.index.array : Uint32Array.from({ length: n0 }, (_, i) => i), total = n0 + add;
  const Arr = total > 65535 ? Uint32Array : (old.constructor === Uint32Array ? Uint32Array : Uint16Array);
  const idx = new Arr(old.length + index.length); idx.set(old); idx.set(index.map((i) => i + n0), old.length);
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeBoundingBox(); g.computeBoundingSphere();
  host.boundingBox = null; host.boundingSphere = null;
  return { from: n0, vertices: add };
}

/** A lace frill at each wrist of `mesh` (a sleeved coat), appended to `host` (the shirtwaist's collar, on the same skeleton). */
export function frillWrists(mesh, host) {
  const lod = Number(lodOf(mesh)) || 0;
  if (lod > FRILL.maxLod || !host) return null;
  const cols = [36, 28][Math.min(1, lod)], rows = 3;
  const ends = ['l', 'r'].map((s) => sleeveEnd(mesh, s)).filter(Boolean);
  if (!ends.length) return null;
  const nv = ends.length * cols * (rows + 1);
  const P = new Float32Array(nv * 3), N = new Float32Array(nv * 3), UV = new Float32Array(nv * 2);
  const SI = new Uint16Array(nv * 4), SW = new Float32Array(nv * 4), index = [];
  const v = new THREE.Vector3(), nn = new THREE.Vector3();
  let k = 0;
  for (const end of ends) {
    const base = k;
    for (let rI = 0; rI <= rows; rI++) {
      const s = rI / rows, t = -FRILL.insideM + s * (FRILL.insideM + FRILL.outM), out = Math.max(0, t / FRILL.outM);
      for (let j = 0; j < cols; j++) {
        const phi = (j / cols) * TAU - Math.PI;
        const r = end.radius(phi) - FRILL.tuckM + (FRILL.tuckM + FRILL.flareM) * out ** 1.3 + FRILL.waveM * out * Math.sin(FRILL.waves * phi);
        const dir = end.b1.clone().multiplyScalar(Math.cos(phi)).addScaledVector(end.b2, Math.sin(phi));
        v.copy(end.c).addScaledVector(end.ax, t).addScaledVector(dir, r);
        nn.copy(dir).addScaledVector(end.ax, -(FRILL.tuckM + FRILL.flareM) / (FRILL.insideM + FRILL.outM)).normalize();
        P.set([v.x, v.y, v.z], k * 3); N.set([nn.x, nn.y, nn.z], k * 3); UV.set([j / cols, s], k * 2);
        // The sleeve hem's weights, carried toward the hand at the frill's edge.
        const h = FRILL.hand * out, mix = new Map();
        for (const [b, x] of end.weights) mix.set(b, (mix.get(b) ?? 0) + x * (1 - h));
        mix.set(end.hand, (mix.get(end.hand) ?? 0) + h * [...end.weights.values()].reduce((a, b) => a + b, 0));
        const top = [...mix].sort((p, q) => q[1] - p[1]).slice(0, 4), sum = top.reduce((a, p) => a + p[1], 0) || 1;
        top.forEach(([b, x], c) => { SI[k * 4 + c] = b; SW[k * 4 + c] = x / sum; });
        k++;
      }
    }
    for (let rI = 0; rI < rows; rI++) for (let j = 0; j < cols; j++) {
      const a = base + rI * cols + j, b = base + rI * cols + (j + 1) % cols, c = a + cols, d = b + cols;
      index.push(a, b, d, a, d, c);
    }
  }
  return { mesh: host.name, ...appendToHost(host, mesh, { P, N, UV, SI, SW, index }) };
}

/** Trims on the asset's materials, as human-finery.js numbers a person's, where none is set. */
function trimAll(root, trims, extra = () => []) {
  const done = [];
  for (const [name, raw] of Object.entries(trims)) {
    const by = new Map();
    root.traverse((o) => { if (o.isMesh && !Array.isArray(o.material) && o.material?.name === name) { if (!by.has(o.material)) by.set(o.material, []); by.get(o.material).push(o); } });
    for (const [material, meshes] of by) {
      if (material.userData?.chiFinery) continue;
      const more = extra(material);
      const spec = finerySpec(more.length ? { ...raw, trims: [...raw.trims, ...more] } : raw);
      if (!spec) continue;
      const numbers = fineryNumbers(spec, meshes, root);
      if (!numbers) continue;
      material.userData = { ...material.userData, chiFinery: numbers };
      done.push(name);
    }
  }
  return done;
}

/** Cut and trim every gown GOWNS names under `root` (a parsed body, before it is cloned), once. */
export function fitGown(root) {
  if (!root) return null;
  if (root.userData.chicagoGown) return root.userData.chicagoGown;
  const assetId = root.userData?.chicago4d_human?.asset_id ?? null;
  const spec = GOWNS.find((s) => s.asset === assetId);
  if (!spec) return null;
  const meshes = [];
  root.traverse((o) => { if (o.isSkinnedMesh && o.skeleton) meshes.push(o); });
  const report = { asset: assetId, skirts: [], frills: [], trims: [] };
  root.updateMatrixWorld(true);
  for (const skirt of meshes.filter((m) => pieceOf(m, assetId) === spec.skirt)) {
    const legs = meshes.filter((m) => lodOf(m) === lodOf(skirt) && /^(skin|footwear)/.test(materialName(m)));
    const r = cutSkirt(skirt, legs);
    if (r) report.skirts.push({ mesh: skirt.name, ...r });
  }
  for (const coat of meshes.filter((m) => pieceOf(m, assetId) === spec.sleeves)) {
    // The frill is the shirtwaist's cloth, drawn with its collar: no mesh, draw call or material added.
    const host = meshes.find((m) => lodOf(m) === lodOf(coat) && pieceOf(m, assetId) === spec.frillHost && materialName(m) === spec.lace);
    const frill = frillWrists(coat, host);
    if (frill) report.frills.push(frill);
  }
  // The shirtwaist's cloth up from grey to cream, then the trims; where a level carries the
  // frill, its lace runs round the whole ring at the wrists, as a cuff (out past the coat's end).
  const creamed = new Set();
  root.traverse((o) => { if (o.isMesh && materialName(o) === spec.lace && !creamed.has(o.material)) { o.material.color.setRGB(...spec.cream, THREE.LinearSRGBColorSpace); creamed.add(o.material); } });
  const frilled = new Set(report.frills.map((f) => root.getObjectByName(f.mesh)?.material).filter(Boolean));
  const cuff = { kind: 'lace', from: 'cuff', at_m: (FRILL.insideM + FRILL.outM) / 2, width_m: FRILL.insideM + FRILL.outM + 0.01, rgb: CREAM };
  report.trims = trimAll(root, spec.trims, (material) => (frilled.has(material) ? [cuff] : []));
  root.userData.chicagoGown = report;
  return report;
}
