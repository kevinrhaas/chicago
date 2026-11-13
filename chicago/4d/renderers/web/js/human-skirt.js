// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-skirt.js — hanging cloth hangs over the legs on the walk, never trousers in small.
 *
 * T-3472 made a woman's skirt one bell; T-3553 (Kevin: "no one should have their legs break
 * through their clothing") makes every hanging garment one: a frock coat's or a greatcoat's
 * skirts, a coachman's livery, a tailcoat's or a soldier's tails, an 1812 capote or shirt
 * tail, a blanket, a breechcloth, a girl's frock, as well as the women's skirts, aprons and
 * basques. The exporter skins them all to the pelvis and to each thigh and calf. Standing
 * that is right. On the walk each half follows its own leg, so the cloth parts like
 * trousers and the other knee or shin comes through it. Hanging cloth hangs from the waist
 * as one piece: the leading knee and shin push it forward and out, the hem comes after
 * with a little delay, the back trails, and the whole rides and sways with the hips.
 *
 * Which cloth: `garmentKind` sorts each leg-weighted garment as 'tube' (trousers, breeches,
 * stockings, leggings, boots: it is on its leg and keeps its own weights), 'hang' (it hangs
 * clear of the legs below the hips: by its piece name, or by the share of its low vertices
 * further than FAR_M from both legs' axes) or 'edge' (weighted to the legs only at the
 * hips: a bodice's or a waistcoat's lower edge, which rides the waist). A figure with no
 * hanging garment gets no bell. A coat (COAT_PIECE) takes the COAT style below.
 *
 * At bind, every hanging or edge garment of the figure gets its own copy of its skin weights (the positions,
 * normals and the rest stay shared with every other figure in the asset) and a skeleton
 * with N_PANELS procedural panels added under the pelvis: a waist bone at the skirt's own
 * waist at that angle round the body, and a hem bone below it at the knee. The cloth's
 * leg weights are taken off the thighs and calves and laid on the panels, by each
 * vertex's angle round the body (the two nearest panels) and its height (pelvis to the
 * waist bone over the hips, waist bone to hem bone across the knee). Each frame, after the
 * clip, the gait and the arm layers have posed the legs, it reads where the thighs, calves
 * and feet are (any leg pose: the baked walk, the gait layer's stride, a pose set by hand),
 * measures on 48 rays round the body how far each leg reaches past the cloth's rest
 * surface, and opens the panels just enough to hold every leg inside with MARGIN_M to
 * spare: the knee is taken by the waist bone, the shin and the toe by the hem bone. On top
 * of that contact, which is never late, the panels follow with a critically damped spring
 * (the hem slower than the waist), a push spreads to the neighbouring panels and moves the
 * whole bell a little, the hem trails with the pace, the bell hangs to gravity against
 * most of the pelvis's tilt and swings as a damped pendulum from the pelvis's own motion.
 *
 * Bounds. Standing, legs where the asset was drawn, every panel is exactly at rest and
 * the skirt is the asset as drawn (the panels are then rigid with the pelvis, which is
 * what the cloth's own weights give with the legs at rest). When the life layer settles
 * the weight onto one leg and softens the other knee, the bell keeps hanging (the asset's
 * own weights carried the hem a few cm with that knee: the trousers in small). Seated, or
 * with a thigh raised past SEATED_DEG, the asset's own leg weights come back (a lap is the
 * legs' job). The panels open at most MAX_WAIST_M at the knee and MAX_HEM_M at the hem;
 * the pendulum swings at most PENDULUM.maxDeg. Nothing else on the body moves.
 *
 * Cost: SAMPLES leg samples (the shin and the foot as three sections each, so a shin lying
 * across the hem is caught), each tested on the rays it covers only when it has moved from
 * where it was drawn, and 2 x N_PANELS + 1 bone rotations, a figure a frame on the CPU:
 * about 28 us walking and 10 us standing (node, one core). On the GPU each driven garment skins with 16
 * more bones in its skeleton, the same four influences a vertex. No draw calls, no textures;
 * a copy of the skin weights (8 bytes a vertex) for each driven garment of each figure.
 * `maxLod` leaves the levels past it as the asset draws them.
 *
 * Deterministic: no randomness, the state is springs only, and it carries across a LOD
 * swap (`bind(scene)`, the panels' displacements are in metres). Reconstructed motion:
 * how a given skirt moved is not recorded; the bell, the push, the lag and the sway are
 * modelled from how heavy wool and cotton skirts behave (liberty to be recorded by the
 * lead with this file).
 */
import * as THREE from 'three';

const DEG = Math.PI / 180;
const TAU = Math.PI * 2;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };

export const N_PANELS = 8;     // panels round the body
const RAYS = 48;               // azimuths the legs are measured on
const ROWS = 30;               // heights of the cloth's rest profile
export const MARGIN_M = 0.016; // the cloth kept off the leg
const HANG = 0.6;              // share of the pelvis's tilt the bell takes out (it hangs)
const SWING_MAX = 25 * DEG;    // the most pelvis tilt the hang answers
const T_HIPS = 0.2;            // share of the length (waist to hem) over which pelvis gives way to the panels
const T_KNEE = 0.13;           // half the share over which the waist bone gives way to the hem bone
const FLARE = 0.35;            // below the knee a pushed panel keeps this much of its cone
const SPREAD = 0.45;           // a panel's push carried to its neighbours
// A coat's skirts, a tailcoat's or a soldier's tails, a shirt's tail, a blanket or a
// breechcloth is not a bell: heavier and stiffer cloth, cut close, that a leg pushes aside
// where it presses and that falls straight back. It carries little of a push round the body,
// keeps no cone and follows quicker than a skirt, so a walking man's coat does not flare
// like a dress.
export const COAT = Object.freeze({ spread: 0.12, flare: 0, omega: Object.freeze({ waist: 26, hem: 18 }), trail: 0.4 });
const COAT_PIECE = /^(coat|tailcoat|tails?|livery|shirt|blanket|breechcloth|sash|turnbacks?)$/;
const SHIFT = 1.2;             // the whole bell follows the mean push this much (a closed one)
const OPEN_GAP = 140 * DEG;    // a garment with a gap wider than this round the body is open
const TRAIL = { perMS: 0.022, max: 0.035 }; // the hem trails with the pace (m per m/s)
const OMEGA = { waist: 16, hem: 9, pace: 4 }; // critically damped springs (1/s)
export const MAX_WAIST_M = 0.32, MAX_HEM_M = 0.45;
export const PENDULUM = Object.freeze({ omega: 4.2, zeta: 0.35, length: 0.7, maxDeg: 5, maxAccel: 6 });
export const SEATED_DEG = 70;  // a thigh raised past this: sitting, the asset's own weights
const STAND_DEG = 55;          // and back below this
const NEED_MIN = 0.002;        // a push under 2 mm is no push
const LEGS = ['thigh_l', 'thigh_r', 'calf_l', 'calf_r'];
const NEEDED = ['pelvis', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r'];
const SIDES = ['l', 'r'];
// Where on each leg the cloth is tested: along the thigh, the shin and the foot.
const ALONG = Object.freeze({ thigh: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], calf: [0.04, 0.15, 0.35, 0.55, 0.75, 0.92, 1], foot: [0.5, 1] });
// Each place on the shin and foot is tested as a ball, by three level sections of it: at its
// centre (the leg's whole girth) and above and below it (a shin swung back under a short
// skirt or a coat's skirts lies nearly level, and its calf reaches up into the cloth over it
// by its girth, where the cloth may be narrower). Offset up, share of radius. A thigh hangs
// near upright under the cloth, and its sections are its centre's.
const SECTIONS = Object.freeze([[0, 1], [0.6, 0.8], [-0.6, 0.8]]);
const CENTRE = Object.freeze([SECTIONS[0]]);
const SAMPLES = 2 * (ALONG.thigh.length + SECTIONS.length * (ALONG.calf.length + ALONG.foot.length));

const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const isSkin = (m) => materialName(m).split('__')[0] === 'skin';
const isShoe = (m) => /^footwear/.test(materialName(m));

const legWeighted = new WeakMap(); // source geometry -> bool (shared by every figure in the asset)
const owned = new WeakMap();       // a driven mesh -> its record here (the asset's geometry, our copy)
function hasLegWeights(mesh) {
  const g = owned.get(mesh)?.origGeometry ?? mesh.geometry;
  if (legWeighted.has(g)) return legWeighted.get(g);
  const si = g.attributes.skinIndex, sw = g.attributes.skinWeight, bones = (owned.get(mesh)?.origSkeleton ?? mesh.skeleton)?.bones ?? [];
  let found = false;
  if (si && sw) {
    const leg = new Set(bones.map((b, i) => (LEGS.includes(b?.name) ? i : -1)).filter((i) => i >= 0));
    for (let i = 0; i < si.count && !found; i++) for (let c = 0; c < 4; c++) if (leg.has(si.getComponent(i, c)) && sw.getComponent(i, c) > 0.01) { found = true; break; }
  }
  legWeighted.set(g, found);
  return found;
}

// T-3553: which garments hang from the waist and which follow a leg. A tube round one leg
// (trousers, breeches, pantaloons, overalls, stockings, leggings, garters, boot shafts) is
// the leg's own and stays on it, as the asset draws it. Cloth that hangs below the hips
// round or between the legs (a skirt, a petticoat, a frock or livery coat's skirts, a
// tailcoat's or a soldier's tails and turnbacks, a jacket's basque, an apron, a shirt's
// tail, a blanket, a breechcloth, a sash's ends) hangs from the waist and only gives way
// to the legs. Cloth weighted to the legs only at the hips (a coat's, waistcoat's,
// bodice's or shirt's lower edge, a belt) rides the waist with the hanging cloth sewn to
// it. The piece's name says it where it can; otherwise its shape: hanging cloth stands well
// off both legs, a tube never does (measured on every body in the town: tubes at most 5 %
// of their low vertices more than 13 cm from a leg's axis, hanging cloth 18 % or more).
const TUBE = /^(trouser|breech(es)?$|pantaloon|overall|stocking|legging|garter|boot|shaft|gaiter)/;
const HANGS = /^(skirt|tail|basque|apron|petticoat|blanket|breechcloth|turnback|gown|frock|sash|selvage|wrap|flap)/;
export const FAR_M = 0.13;      // a hanging vertex stands this far off both legs' axes (per 0.85 m of leg)
export const FAR_SHARE = 0.12;  // and this share of a garment's low vertices does
const LOW_M = 0.1;              // low: this far under the hips (per 0.85 m of leg)
const ADULT_LEG_M = 0.85;
const kinds = new WeakMap();    // source geometry -> { kind, low }

/** A garment's piece name, without the body's id and the level. */
function pieceName(mesh, assetId) {
  let n = mesh.name ?? '';
  if (assetId && n.startsWith(`${assetId}_`)) n = n.slice(assetId.length + 1);
  return n.replace(/_lod\d*$/, '');
}
const tokens = (name) => name.toLowerCase().split(/[_\s.-]+/).filter(Boolean);

/**
 * What a garment does over the legs: 'hang', 'tube', 'edge' (weighted to the legs only at the
 * hips), or null (skin, a shoe, or nothing on the legs). Cached per shared geometry.
 */
export function garmentKind(mesh, assetId = null) {
  const rec = owned.get(mesh), g = rec?.origGeometry ?? mesh.geometry, sk = rec?.origSkeleton ?? mesh.skeleton;
  if (kinds.has(g)) return kinds.get(g);
  let out = { kind: null, low: Infinity, length: 0, count: 0 };
  if (sk && !isSkin(mesh) && !isShoe(mesh) && hasLegWeights(mesh)) out = classify(mesh, g, sk, assetId);
  kinds.set(g, out);
  return out;
}
function classify(mesh, g, sk, assetId) {
  const index = new Map(sk.bones.map((b, i) => [b?.name, i]));
  if (!NEEDED.every((n) => index.has(n))) return { kind: null, low: Infinity, length: 0, count: 0 };
  const Ip = sk.boneInverses[index.get('pelvis')];
  const at = (n) => new THREE.Vector3().setFromMatrixPosition(new THREE.Matrix4().copy(Ip).multiply(sk.boneInverses[index.get(n)].clone().invert()));
  const hip = { l: at('thigh_l'), r: at('thigh_r') }, knee = { l: at('calf_l'), r: at('calf_r') }, ankle = { l: at('foot_l'), r: at('foot_r') };
  const O = hip.l.clone().add(hip.r).multiplyScalar(0.5);
  const U = O.clone().sub(ankle.l.clone().add(ankle.r).multiplyScalar(0.5));
  const leg = (hip.l.distanceTo(ankle.l) + hip.r.distanceTo(ankle.r)) / 2, scale = leg / ADULT_LEG_M;
  U.normalize();
  const M = new THREE.Matrix4().copy(Ip).multiply(mesh.bindMatrix);
  const pos = g.attributes.position, si = g.attributes.skinIndex, sw = g.attributes.skinWeight;
  const legIdx = new Set(LEGS.map((b) => index.get(b)));
  const v = new THREE.Vector3(), d = new THREE.Vector3(), ab = new THREE.Vector3();
  const segDist = (p, a, b) => { ab.subVectors(b, a); const t = clamp(d.subVectors(p, a).dot(ab) / ab.lengthSq(), 0, 1); return d.copy(a).addScaledVector(ab, t).distanceTo(p); };
  let low = 0, far = 0, least = Infinity, top = -Infinity;
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(M);
    const h = d.subVectors(v, O).dot(U);
    least = Math.min(least, h);
    let w = 0; for (let c = 0; c < 4; c++) if (legIdx.has(si.getComponent(i, c))) w += sw.getComponent(i, c);
    if (w > 0.01) top = Math.max(top, h);
    if (w <= 0.01 || h > -LOW_M * scale) continue;
    low++;
    let near = Infinity;
    for (const s of SIDES) near = Math.min(near, segDist(v, hip[s], knee[s]), segDist(v, knee[s], ankle[s]));
    if (near > FAR_M * scale) far++;
  }
  const words = tokens(pieceName(mesh, assetId)), material = materialName(mesh);
  const tube = words.some((t) => TUBE.test(t));
  let kind;
  if (!low) kind = tube || /^garment_lower/.test(material) ? 'tube' : 'edge';
  else if (tube) kind = 'tube';
  else kind = words.some((t) => HANGS.test(t)) || far / low >= FAR_SHARE ? 'hang' : 'tube';
  return { kind, low: least, length: top - least, count: low };
}

/**
 * The hanging cloth of a figure, and every garment that must move with it, or null when
 * nothing hangs below its hips (trousers alone). `skirt` is the main hanging garment (the longest, waist to hem, and fullest),
 * `hanging` all of them (the legs are kept inside every one), `driven` those and the
 * garments sewn to them at the waist; `tubes` stay on the legs.
 */
export function skirtMeshes(scene) {
  const all = [];
  scene?.traverse((o) => { if (o.isSkinnedMesh && o.skeleton) all.push(o); });
  const assetId = scene?.userData?.chicago4d_human?.asset_id ?? null;
  const kind = new Map(all.map((m) => [m, garmentKind(m, assetId)]));
  const hanging = all.filter((m) => kind.get(m).kind === 'hang');
  if (!hanging.length) return null;
  // The longest (within a fifth) and the fullest of them: a coat's skirts, not its turnbacks.
  const longest = Math.max(...hanging.map((m) => kind.get(m).length));
  const skirt = hanging.filter((m) => kind.get(m).length >= 0.8 * longest).reduce((a, m) => (kind.get(m).count > kind.get(a).count ? m : a));
  const driven = all.filter((m) => kind.get(m).kind === 'hang' || kind.get(m).kind === 'edge');
  const tubes = all.filter((m) => kind.get(m).kind === 'tube');
  return { skirt, hanging, driven, tubes, body: all.find(isSkin) ?? null };
}

const bindings = new WeakMap(); // scene -> its binding (kept while the scene is parked)

/** A critically damped spring on x (and v) toward `target`. */
function spring(x, v, i, target, omega, dt) {
  const d = x[i] - target, e = Math.exp(-omega * dt), temp = (v[i] + omega * d) * dt;
  v[i] = (v[i] - omega * temp) * e;
  x[i] = target + (d + temp) * e;
}

/**
 * Build the panels on one body. Returns the binding, or null when the body has no skirt or
 * not the contract's leg bones.
 */
function makeBinding(scene) {
  const found = skirtMeshes(scene);
  if (!found) return null;
  const { skirt, hanging, driven, body } = found;
  const sk = skirt.skeleton, index = new Map(sk.bones.map((b, i) => [b.name, i]));
  if (!NEEDED.every((n) => index.has(n))) return null;
  const bone = (n) => sk.bones[index.get(n)];
  const pelvis = bone('pelvis');
  // The bind pose in the pelvis's own frame (P), from the inverse bind matrices: the
  // figure may already be posed by its clip.
  const Ip = sk.boneInverses[index.get('pelvis')];
  const inP = (n) => new THREE.Matrix4().copy(Ip).multiply(sk.boneInverses[index.get(n)].clone().invert());
  const at = (n) => new THREE.Vector3().setFromMatrixPosition(inP(n));
  const hip = { l: at('thigh_l'), r: at('thigh_r') }, knee = { l: at('calf_l'), r: at('calf_r') }, ankle = { l: at('foot_l'), r: at('foot_r') };
  const ball = { l: index.has('ball_l') ? at('ball_l') : null, r: index.has('ball_r') ? at('ball_r') : null };
  // The figure's frame in P: up from the ankles to the hips, left from the right hip to the left.
  const O = hip.l.clone().add(hip.r).multiplyScalar(0.5);
  const U = O.clone().sub(ankle.l.clone().add(ankle.r).multiplyScalar(0.5)).normalize();
  const Lf = hip.l.clone().sub(hip.r); Lf.addScaledVector(U, -Lf.dot(U)).normalize();
  const Fw = new THREE.Vector3().crossVectors(Lf, U).normalize();
  const toF = (p, out) => { const x = p.x - O.x, y = p.y - O.y, z = p.z - O.z; out[0] = x * Lf.x + y * Lf.y + z * Lf.z; out[1] = x * U.x + y * U.y + z * U.z; out[2] = x * Fw.x + y * Fw.y + z * Fw.z; return out; };
  const fromF = (X, y, Z) => O.clone().addScaledVector(Lf, X).addScaledVector(U, y).addScaledVector(Fw, Z);
  // The pelvis's bind rotation in its parent (for the hang).
  const parentIdx = pelvis.parent?.isBone ? index.get(pelvis.parent.name) : undefined;
  const pelvisBindQ = new THREE.Quaternion();
  if (parentIdx !== undefined) new THREE.Matrix4().copy(sk.boneInverses[parentIdx]).multiply(Ip.clone().invert()).decompose(new THREE.Vector3(), pelvisBindQ, new THREE.Vector3());
  else pelvisBindQ.copy(pelvis.quaternion);
  const upParent = U.clone().applyQuaternion(pelvisBindQ);

  // Each driven mesh's vertices in the figure frame, at bind.
  const meshes = driven.map((mesh) => {
    const msk = mesh.skeleton, mIndex = new Map(msk.bones.map((b, i) => [b.name, i]));
    const Ipm = msk.boneInverses[mIndex.get('pelvis')];
    const M = new THREE.Matrix4().copy(Ipm).multiply(mesh.bindMatrix);
    const pos = mesh.geometry.attributes.position, n = pos.count, F = new Float32Array(n * 3), v = new THREE.Vector3(), f = [0, 0, 0];
    for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(M); toF(v, f); F[i * 3] = f[0]; F[i * 3 + 1] = f[1]; F[i * 3 + 2] = f[2]; }
    const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight;
    const legW = new Float32Array(n);
    const legIdx = new Set(LEGS.map((b) => mIndex.get(b)));
    for (let i = 0; i < n; i++) for (let c = 0; c < 4; c++) if (legIdx.has(si.getComponent(i, c))) legW[i] += sw.getComponent(i, c);
    return { mesh, F, legW, n, Ipm, mIndex };
  });
  // The hanging cloth, every layer of it (a coat's skirts over a waistcoat's, an apron over
  // a skirt, a blanket over a shirt's tail and a breechcloth): the legs stay inside them all.
  // The longest of them sets the bell's length, from the top of the cloth the legs carried
  // to its hem, and where the panels hang.
  const hangs = meshes.filter((m) => hanging.includes(m.mesh)), S = meshes.find((m) => m.mesh === skirt);
  let yTop = -Infinity, yHem = Infinity;
  for (let i = 0; i < S.n; i++) { const y = S.F[i * 3 + 1]; if (S.legW[i] > 0.01) yTop = Math.max(yTop, y); yHem = Math.min(yHem, y); }
  const kneeY = (toF(knee.l, [0, 0, 0])[1] + toF(knee.r, [0, 0, 0])[1]) / 2;
  const len = yTop - yHem;
  if (!(len > 0.12)) return null;
  const tMid = clamp((yTop - kneeY) / len, 0.35, 0.7);
  const yMid = yTop - tMid * len;
  const tB0 = tMid - T_KNEE, tB1 = tMid + T_KNEE, tA = Math.min(T_HIPS, tB0 - 0.02);
  const wA = (t) => smooth(t / tA), wB = (t) => smooth((t - tB0) / (tB1 - tB0));

  // The cloth's rest surface: least and mean radius on RAYS x ROWS cells.
  const dy = len / (ROWS - 1), cells = RAYS * ROWS;
  // The cloth's rest surface at each cell: the longest garment's, or a layer worn under it
  // (a shirt's tail or a breechcloth under a blanket), whichever is innermost there, since
  // that is the one a leg would come through first. A layer over it (an apron) is left out.
  const rMin = new Float32Array(cells).fill(Infinity), rSum = new Float32Array(cells), rN = new Uint16Array(cells);
  const cellOf = (H, i) => {
    const X = H.F[i * 3], y = H.F[i * 3 + 1], Z = H.F[i * 3 + 2];
    const row = Math.round((y - yHem) / dy); if (row < 0 || row >= ROWS) return -1;
    return row * RAYS + ((Math.round(Math.atan2(X, Z) / TAU * RAYS) % RAYS) + RAYS) % RAYS;
  };
  for (let i = 0; i < S.n; i++) {
    const c = cellOf(S, i); if (c < 0) continue;
    const r = Math.hypot(S.F[i * 3], S.F[i * 3 + 2]);
    rMin[c] = Math.min(rMin[c], r); rSum[c] += r; rN[c]++;
  }
  for (const H of hangs) {
    if (H === S) continue;
    const own = new Float32Array(cells).fill(Infinity);
    for (let i = 0; i < H.n; i++) { const c = cellOf(H, i); if (c >= 0) own[c] = Math.min(own[c], Math.hypot(H.F[i * 3], H.F[i * 3 + 2])); }
    let under = 0, over = 0;
    for (let c = 0; c < cells; c++) if (own[c] < Infinity && rMin[c] < Infinity) { if (own[c] < rMin[c] - 0.002) under++; else over++; }
    if (under > over) for (let c = 0; c < cells; c++) rMin[c] = Math.min(rMin[c], own[c]);
  }
  // Is the main garment closed round the body (a skirt, a petticoat, a buttoned frock coat)
  // or open (a tailcoat's tails, a soldier's coat skirts, a wrap): the widest gap in it round
  // the body, between a fifth and four fifths of its length. An open garment does not shift
  // as a whole with the legs' mean push: moving its edges sideways would slide them off the
  // leg beside them.
  const around = [];
  for (let i = 0; i < S.n; i++) { const t = (yTop - S.F[i * 3 + 1]) / len; if (t > 0.2 && t < 0.8) around.push(Math.atan2(S.F[i * 3], S.F[i * 3 + 2])); }
  around.sort((p, q) => p - q);
  let gap = around.length ? TAU - (around[around.length - 1] - around[0]) : TAU;
  for (let i = 1; i < around.length; i++) gap = Math.max(gap, around[i] - around[i - 1]);
  const closed = gap <= OPEN_GAP;
  const coat = tokens(pieceName(skirt, scene.userData?.chicago4d_human?.asset_id)).some((t) => COAT_PIECE.test(t));
  const rMean = new Float32Array(cells).fill(NaN);
  for (let c = 0; c < cells; c++) { if (rN[c]) rMean[c] = rSum[c] / rN[c]; if (rMin[c] === Infinity) rMin[c] = NaN; }
  fillGrid(rMin); fillGrid(rMean);
  const rowAt = (y) => clamp((y - yHem) / dy, 0, ROWS - 1);
  const look = (grid, j, y) => { const f = rowAt(y), i0 = Math.min(ROWS - 2, Math.floor(f)), a = f - i0; return grid[i0 * RAYS + j] * (1 - a) + grid[(i0 + 1) * RAYS + j] * a; };
  const lookAngle = (grid, theta, y) => { const f = ((theta / TAU) * RAYS % RAYS + RAYS) % RAYS, j0 = Math.floor(f) % RAYS, a = f - Math.floor(f); return look(grid, j0, y) * (1 - a) + look(grid, (j0 + 1) % RAYS, y) * a; };

  // The legs' girth along each bone, from the body as drawn (or a woman's, without one).
  const girth = legGirth(owned.get(skirt)?.origGeometry ?? skirt.geometry, [body, ...found.tubes].filter(Boolean), { hip, knee, ankle });
  // The legs as drawn: what the cloth already clears standing is never a push.
  const restExit = new Float32Array(cells).fill(-Infinity);
  const f3 = [0, 0, 0], c3 = new THREE.Vector3();
  for (const s of SIDES) {
    const segs = [[hip[s], knee[s], girth[s].thigh], [knee[s], ankle[s], girth[s].calf]];
    if (ball[s]) segs.push([ankle[s], ball[s], girth[s].foot]);
    for (const [a, b, g] of segs) {
      const steps = Math.max(2, Math.ceil(a.distanceTo(b) / 0.015));
      for (let q = 0; q <= steps; q++) {
        const u = q / steps; toF(c3.copy(a).lerp(b, u), f3);
        const rho = girthAt(g, u) + MARGIN_M, row = Math.round((f3[1] - yHem) / dy);
        if (row < 0 || row >= ROWS) continue;
        for (let j = 0; j < RAYS; j++) {
          const e = rayExit(f3[0], f3[2], rho, (j / RAYS) * TAU);
          if (e > restExit[row * RAYS + j]) restExit[row * RAYS + j] = e;
        }
      }
    }
  }
  const allow = new Float64Array(cells);
  for (let row = 0; row < ROWS; row++) for (let j = 0; j < RAYS; j++) {
    let e = -Infinity;
    for (let dr = 0; dr <= 0; dr++) for (let dj = 0; dj <= 0; dj++) {
      const r2 = row + dr; if (r2 < 0 || r2 >= ROWS) continue;
      e = Math.max(e, restExit[r2 * RAYS + ((j + dj + RAYS) % RAYS)]);
    }
    allow[row * RAYS + j] = Math.max(rMin[row * RAYS + j] - MARGIN_M, e);
  }

  // The panels: a waist bone on the cloth at the waist, a hem bone below it at the knee.
  const theta = Array.from({ length: N_PANELS }, (_, k) => (k / N_PANELS) * TAU);
  const dir = theta.map((t) => [Math.sin(t), Math.cos(t)]);
  const Wc = fromF(0, yTop, 0);
  const P = theta.map((t) => fromF(Math.sin(t) * lookAngle(rMean, t, yTop), yTop, Math.cos(t) * lookAngle(rMean, t, yTop)));
  const Q = theta.map((t) => fromF(Math.sin(t) * lookAngle(rMean, t, yMid), yMid, Math.cos(t) * lookAngle(rMean, t, yMid)));
  const H = theta.map((t) => fromF(Math.sin(t) * lookAngle(rMean, t, yHem), yHem, Math.cos(t) * lookAngle(rMean, t, yHem)));
  const hang = new THREE.Bone(); hang.name = 'skirt_hang'; hang.position.copy(Wc);
  const waist = [], hem = [];
  for (let k = 0; k < N_PANELS; k++) {
    const w = new THREE.Bone(); w.name = `skirt_waist_${k}`; w.position.copy(P[k]).sub(Wc); hang.add(w); waist.push(w);
    const h = new THREE.Bone(); h.name = `skirt_hem_${k}`; h.position.copy(Q[k]).sub(P[k]); w.add(h); hem.push(h);
  }
  pelvis.add(hang);
  hang.updateMatrixWorld(true);

  // Each driven mesh: its own skin weights on the panels, and a skeleton with them.
  const own = meshes.map((m) => rebind(m, { waist, hem, P, Q, yTop, yHem, len, wA, wB, pelvisIndex: m.mIndex.get('pelvis') }));
  // The ray weights: a ray's two panels, and how much of their push its cloth gets.
  const rayK = new Int32Array(RAYS * 2), rayGain = new Float64Array(RAYS), raySin = new Float64Array(RAYS), rayCos = new Float64Array(RAYS);
  const rowAllow = new Float64Array(ROWS).fill(Infinity);
  for (let row = 0; row < ROWS; row++) for (let j = 0; j < RAYS; j++) rowAllow[row] = Math.min(rowAllow[row], allow[row * RAYS + j]);
  for (let j = 0; j < RAYS; j++) {
    const f = (j / RAYS) * N_PANELS, k0 = Math.floor(f) % N_PANELS, k1 = (k0 + 1) % N_PANELS, a = f - Math.floor(f), th = (j / RAYS) * TAU;
    rayK[j * 2] = k0; rayK[j * 2 + 1] = k1;
    rayGain[j] = (1 - a) * Math.cos(th - theta[k0]) + a * Math.cos(th - theta[k1]);
    raySin[j] = Math.sin(th); rayCos[j] = Math.cos(th);
  }
  // The leg samples as drawn (the order sampleLegs makes them in): one that has not moved cannot push.
  const restS = new Float64Array(SAMPLES * 3);
  {
    let q = 0;
    const put = (a, b, along, g, secs) => {
      for (const u of along) {
        toF(c3.copy(a).lerp(b, u), f3);
        const rho = girthAt(g, u) + MARGIN_M;
        for (const [up] of secs) { restS[q++] = f3[0]; restS[q++] = f3[1] + up * rho; restS[q++] = f3[2]; }
      }
    };
    for (const s of SIDES) { put(hip[s], knee[s], ALONG.thigh, girth[s].thigh, CENTRE); put(knee[s], ankle[s], ALONG.calf, girth[s].calf, SECTIONS); put(ankle[s], ball[s] ?? ankle[s], ALONG.foot, girth[s].foot, SECTIONS); }
  }
  const binding = {
    scene, pelvis, restS, hang, waist, hem, own, bones: { thigh: {}, calf: {}, foot: {}, ball: {} },
    O, U, Lf, Fw, Wc, P, Q, H, dir, yTop, yHem, yMid, len, tMid, tA, tB0, tB1, wA, wB, allow, rMin, rMean, girth,
    rayK, rayGain, raySin, rayCos, rowAllow, pelvisBindQ, upParent, hasParent: parentIdx !== undefined, lod: scene.userData?.chicago4d_human?.lod ?? null,
    mode: 'bell', freed: false, shift: closed && !coat ? SHIFT : 0,
    spread: coat ? COAT.spread : SPREAD, flare: coat ? COAT.flare : FLARE, trail: coat ? COAT.trail : 1,
    omega: coat ? COAT.omega : OMEGA, coat,
  };
  for (const s of SIDES) {
    binding.bones.thigh[s] = bone(`thigh_${s}`); binding.bones.calf[s] = bone(`calf_${s}`); binding.bones.foot[s] = bone(`foot_${s}`);
    binding.bones.ball[s] = index.has(`ball_${s}`) ? bone(`ball_${s}`) : null;
  }
  // A torn-down body disposes its meshes' skeletons (humans.js teardown): free ours with it.
  for (const o of own) for (const skel of [o.skeleton, o.origSkeleton]) {
    const base = skel.dispose.bind(skel);
    skel.dispose = () => { base(); free(binding); };
  }
  return binding;
}

/** Fill the NaN cells of a RAYS x ROWS grid: round each row, then up and down the rows. */
function fillGrid(g) {
  for (let row = 0; row < ROWS; row++) {
    const have = [];
    for (let j = 0; j < RAYS; j++) if (Number.isFinite(g[row * RAYS + j])) have.push(j);
    if (!have.length || have.length === RAYS) continue;
    for (let j = 0; j < RAYS; j++) {
      if (Number.isFinite(g[row * RAYS + j])) continue;
      let a = have[have.length - 1], b = have[0];
      for (const h of have) { if (h < j) a = h; if (h > j) { b = h; break; } }
      const da = (j - a + RAYS) % RAYS, db = (b - j + RAYS) % RAYS, t = da / (da + db || 1);
      g[row * RAYS + j] = g[row * RAYS + a] * (1 - t) + g[row * RAYS + b] * t;
    }
  }
  for (let j = 0; j < RAYS; j++) {
    const have = [];
    for (let row = 0; row < ROWS; row++) if (Number.isFinite(g[row * RAYS + j])) have.push(row);
    if (!have.length) { for (let row = 0; row < ROWS; row++) g[row * RAYS + j] = 0.2; continue; }
    for (let row = 0; row < ROWS; row++) {
      if (Number.isFinite(g[row * RAYS + j])) continue;
      let a = -1, b = -1;
      for (const h of have) { if (h < row) a = h; if (h > row && b < 0) b = h; }
      g[row * RAYS + j] = a < 0 ? g[b * RAYS + j] : b < 0 ? g[a * RAYS + j] : g[a * RAYS + j] + (g[b * RAYS + j] - g[a * RAYS + j]) * (row - a) / (b - a);
    }
  }
}

/** Where a ray from the body's axis at angle `theta` (0 front, + to the left) leaves a disc. */
function rayExit(X, Z, rho, theta) {
  const sx = Math.sin(theta), cz = Math.cos(theta);
  const along = X * sx + Z * cz, perp = X * cz - Z * sx, d = rho * rho - perp * perp;
  return d < 0 ? -Infinity : along + Math.sqrt(d);
}

const GIRTH_BINS = 8;
const DEFAULT_GIRTH = { thigh: [0.085, 0.08, 0.075, 0.07, 0.065, 0.06, 0.057, 0.055], calf: [0.055, 0.057, 0.058, 0.055, 0.05, 0.045, 0.04, 0.036], foot: [0.045, 0.045, 0.042, 0.04, 0.038, 0.035, 0.032, 0.03] };
const girthCache = new WeakMap(); // the hanging cloth's geometry -> girth (one per body and level)

/**
 * The leg's radius along each bone: the most of the body's own skin about it, or of a tube
 * worn over it (loose trousers, breeches, leggings stand off the skin), binned.
 */
function legGirth(key, meshes, { hip, knee, ankle }) {
  const fallback = { l: { ...DEFAULT_GIRTH }, r: { ...DEFAULT_GIRTH } };
  if (!meshes.length) return fallback;
  if (girthCache.has(key)) return girthCache.get(key);
  const out = { l: { thigh: new Array(GIRTH_BINS).fill(0), calf: new Array(GIRTH_BINS).fill(0), foot: DEFAULT_GIRTH.foot.slice() }, r: { thigh: new Array(GIRTH_BINS).fill(0), calf: new Array(GIRTH_BINS).fill(0), foot: DEFAULT_GIRTH.foot.slice() } };
  const v = new THREE.Vector3(), ab = new THREE.Vector3(), av = new THREE.Vector3();
  for (const mesh of meshes) {
    const rec = owned.get(mesh), sk = rec?.origSkeleton ?? mesh.skeleton, geo = rec?.origGeometry ?? mesh.geometry;
    const idx = new Map(sk.bones.map((b, i) => [b.name, i]));
    if (!NEEDED.every((n) => idx.has(n))) continue;
    const M = new THREE.Matrix4().copy(sk.boneInverses[idx.get('pelvis')]).multiply(mesh.bindMatrix);
    const pos = geo.attributes.position, si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight;
    const of = new Map();
    for (const s of SIDES) { of.set(idx.get(`thigh_${s}`), [s, 'thigh', hip[s], knee[s]]); of.set(idx.get(`calf_${s}`), [s, 'calf', knee[s], ankle[s]]); }
    for (let i = 0; i < pos.count; i++) {
      let best = -1, bw = 0;
      for (let c = 0; c < 4; c++) { const w = sw.getComponent(i, c), b = si.getComponent(i, c); if (w > bw && of.has(b)) { bw = w; best = b; } }
      if (bw < 0.5) continue;
      const [s, part, a, b] = of.get(best);
      v.fromBufferAttribute(pos, i).applyMatrix4(M);
      ab.subVectors(b, a); av.subVectors(v, a);
      const u = av.dot(ab) / ab.lengthSq();
      if (u < 0 || u > 1.05) continue;
      const r = av.addScaledVector(ab, -clamp(u, 0, 1)).length();
      const bin = Math.min(GIRTH_BINS - 1, Math.floor(clamp(u, 0, 0.999) * GIRTH_BINS));
      if (r < 0.2) out[s][part][bin] = Math.max(out[s][part][bin], r);
    }
  }
  for (const s of SIDES) for (const part of ['thigh', 'calf']) {
    const g = out[s][part];
    for (let k = 0; k < GIRTH_BINS; k++) if (!(g[k] > 0.015)) g[k] = DEFAULT_GIRTH[part][k];
  }
  girthCache.set(key, out);
  return out;
}
/** A girth at `u` along its bone (the larger of the two bins about it). */
function girthAt(g, u) {
  const f = clamp(u, 0, 0.999) * GIRTH_BINS, k = Math.floor(f);
  return Math.max(g[k], g[Math.min(GIRTH_BINS - 1, k + (f - k > 0.5 ? 1 : 0))], g[Math.max(0, k - (f - k < 0.5 ? 1 : 0))]);
}

/** One garment on the panels: its own skin weights and a skeleton with the panel bones. */
function rebind(m, { waist, hem, P, Q, yTop, len, wA, wB, pelvisIndex }) {
  const { mesh, F, legW, n, Ipm } = m;
  const src = mesh.geometry, osk = mesh.skeleton, nb = osk.bones.length;
  const total = nb + 2 * N_PANELS;
  const si = src.attributes.skinIndex, sw = src.attributes.skinWeight;
  const IndexArray = total <= 256 ? Uint8Array : Uint16Array;
  const outI = new IndexArray(n * 4), outW = new Uint8Array(n * 4);
  const leg = new Set(LEGS.map((b) => m.mIndex.get(b)));
  const ids = [], ws = [];
  for (let i = 0; i < n; i++) {
    const X = F[i * 3], y = F[i * 3 + 1], Z = F[i * 3 + 2], t = (yTop - y) / len;
    ids.length = 0; ws.length = 0;
    if (legW[i] <= 1e-4 && t <= 0) {
      for (let c = 0; c < 4; c++) { ids.push(si.getComponent(i, c)); ws.push(sw.getComponent(i, c)); }
    } else {
      // What is not leg (the pelvis, as drawn) holds the cloth over the hips.
      let base = 0;
      for (let c = 0; c < 4; c++) { const b = si.getComponent(i, c), w = sw.getComponent(i, c); if (w > 0 && !leg.has(b)) base += w; }
      const a = wA(t), b = wB(t), keep = 1 - a;
      if (base > 1e-3) { for (let c = 0; c < 4; c++) { const bi = si.getComponent(i, c), w = sw.getComponent(i, c); if (w > 0 && !leg.has(bi)) { ids.push(bi); ws.push(keep * w / base); } } }
      else { ids.push(pelvisIndex); ws.push(keep); }
      const f = ((Math.atan2(X, Z) / TAU) * N_PANELS % N_PANELS + N_PANELS) % N_PANELS, k0 = Math.floor(f) % N_PANELS, k1 = (k0 + 1) % N_PANELS, s = f - Math.floor(f);
      ids.push(nb + k0, nb + k1, nb + N_PANELS + k0, nb + N_PANELS + k1);
      ws.push(a * (1 - b) * (1 - s), a * (1 - b) * s, a * b * (1 - s), a * b * s);
    }
    packWeights(ids, ws, outI, outW, i * 4);
  }
  const g = new THREE.BufferGeometry();
  g.name = `${src.name || mesh.name}~skirt`;
  g.setIndex(src.index);
  for (const [k, a] of Object.entries(src.attributes)) if (k !== 'skinIndex' && k !== 'skinWeight') g.setAttribute(k, a);
  g.morphAttributes = src.morphAttributes;
  g.morphTargetsRelative = src.morphTargetsRelative;
  for (const grp of src.groups) g.addGroup(grp.start, grp.count, grp.materialIndex);
  g.setAttribute('skinIndex', new THREE.BufferAttribute(outI, 4));
  g.setAttribute('skinWeight', new THREE.BufferAttribute(outW, 4, true));
  g.boundingBox = src.boundingBox; g.boundingSphere = src.boundingSphere;
  // Each panel bone's inverse bind: its rest place in the pelvis frame, then the mesh's own
  // pelvis inverse (which carries the mesh's quantisation), so at rest it is the pelvis.
  const inv = [...waist.map((_, k) => new THREE.Matrix4().makeTranslation(-P[k].x, -P[k].y, -P[k].z).multiply(Ipm)),
    ...hem.map((_, k) => new THREE.Matrix4().makeTranslation(-Q[k].x, -Q[k].y, -Q[k].z).multiply(Ipm))];
  const skeleton = new THREE.Skeleton([...osk.bones, ...waist, ...hem], [...osk.boneInverses, ...inv]);
  const out = { mesh, geometry: g, skeleton, origGeometry: src, origSkeleton: osk, shared: false };
  owned.set(mesh, out);
  mesh.parent?.traverse?.((o) => { if (o !== mesh && o.isSkinnedMesh && o.skeleton === osk) out.shared = true; });
  useBell(out, true);
  return out;
}

/** Up to four (bone, weight) pairs, the largest, as bytes that sum to exactly 255. */
function packWeights(ids, ws, outI, outW, o) {
  const pairs = [];
  for (let k = 0; k < ids.length; k++) {
    if (!(ws[k] > 1e-6)) continue;
    const p = pairs.find((q) => q[0] === ids[k]);
    if (p) p[1] += ws[k]; else pairs.push([ids[k], ws[k]]);
  }
  pairs.sort((a, b) => b[1] - a[1]);
  pairs.length = Math.min(4, pairs.length);
  const sum = pairs.reduce((s, p) => s + p[1], 0) || 1;
  let left = 255;
  for (let c = 0; c < 4; c++) {
    const p = pairs[c];
    const q = p ? Math.round((p[1] / sum) * 255) : 0;
    outI[o + c] = p ? p[0] : 0; outW[o + c] = q; left -= q;
  }
  outW[o] += left; // the rounding goes to the largest
}

function useBell(o, bell) {
  const geometry = bell ? o.geometry : o.origGeometry, skeleton = bell ? o.skeleton : o.origSkeleton;
  if (o.mesh.geometry === geometry && o.mesh.skeleton === skeleton) return;
  o.mesh.geometry = geometry;
  o.mesh.bind(skeleton, o.mesh.bindMatrix);
  // bind() sets the inverse from the bind matrix; an attached mesh keeps it as its world's.
  if (o.mesh.bindMode === THREE.AttachedBindMode) o.mesh.bindMatrixInverse.copy(o.mesh.matrixWorld).invert();
}

/** Let go of a binding's own GPU data: the weights, and the asset skeleton if only it used it. */
function free(b) {
  if (b.freed) return;
  b.freed = true;
  for (const o of b.own) {
    const g = o.geometry;
    // Only the attributes this file made are ours; the rest belong to every figure in the asset.
    for (const k of Object.keys(g.attributes)) if (k !== 'skinIndex' && k !== 'skinWeight') g.deleteAttribute(k);
    g.setIndex(null);
    g.morphAttributes = {};
    g.dispose();
    if (!o.shared) for (const s of [o.skeleton, o.origSkeleton]) if (o.mesh.skeleton !== s) THREE.Skeleton.prototype.dispose.call(s);
    owned.delete(o.mesh);
  }
  bindings.delete(b.scene);
}

/** Put a body back as the asset draws it, and take the panels off. */
function unbind(b) {
  for (const o of b.own) useBell(o, false);
  b.hang.removeFromParent();
  free(b);
}

/**
 * The skirt of one figure: null when the body wears none. `bind(scene)` attaches it to a
 * new LOD and keeps its state; `apply(dt, { state, root, gait })` runs after the clip, the
 * gait and the arm layers each frame.
 */
export function createHumanSkirt({ id = 'human', scene = null, maxLod = 3 } = {}) {
  void id; // nothing here is drawn at random: the same legs give the same skirt
  if (!scene || !(bindings.has(scene) || skirtMeshes(scene))) return null;
  let cur = null;
  // State, in metres and radians, carried across a LOD swap: per panel, the waist and hem
  // displacement (2 x 2 numbers: left, front) and their velocities; the pendulum; the pace.
  const X = new Float64Array(N_PANELS * 4), V = new Float64Array(N_PANELS * 4);
  const pend = { f: 0, l: 0, vf: 0, vl: 0 }, pace = { x: new Float64Array(1), v: new Float64Array(1) };
  const prev = { p: new THREE.Vector3(), v: new THREE.Vector3(), has: 0 };
  let mode = 'bell', seated = false;
  // Scratch, so a frame allocates nothing.
  const need = new Float64Array(N_PANELS * SAMPLES), sy = new Float64Array(SAMPLES), sX = new Float64Array(SAMPLES), sZ = new Float64Array(SAMPLES), sR = new Float64Array(SAMPLES);
  const gainQ = new Float64Array(SAMPLES), gainH = new Float64Array(SAMPLES);
  const reqQ = new Float64Array(N_PANELS), reqH = new Float64Array(N_PANELS), tgtQ = new Float64Array(N_PANELS), tgtH = new Float64Array(N_PANELS);
  const mT = new THREE.Matrix4(), mC = new THREE.Matrix4(), mF = new THREE.Matrix4(), mB = new THREE.Matrix4();
  const pHip = new THREE.Vector3(), pKnee = new THREE.Vector3(), pAnk = new THREE.Vector3(), pBall = new THREE.Vector3(), tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3();
  const qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), qK = new THREE.Quaternion(), qHang = new THREE.Quaternion(), qHangInv = new THREE.Quaternion(), qUp = new THREE.Quaternion();
  const qW = new THREE.Quaternion(), vA = new THREE.Vector3(), vB = new THREE.Vector3(), vC = new THREE.Vector3(), f3 = [0, 0, 0];
  const pw = new THREE.Vector3(), vel = new THREE.Vector3(), acc = new THREE.Vector3();

  function bind(next) {
    const lod = next?.userData?.chicago4d_human?.lod;
    cur = null;
    if (!next || (Number.isFinite(lod) && lod > maxLod)) return false;
    let b = bindings.get(next);
    if (!b || b.freed) { b = makeBinding(next); if (b) bindings.set(next, b); }
    if (!b) return false;
    cur = b;
    useCur(mode === 'bell');
    // Pose the new body from the state as it is; the state itself is left as it was.
    const keep = X.slice();
    pose(0);
    X.set(keep);
    return true;
  }
  function useCur(bell) { if (cur) for (const o of cur.own) useBell(o, bell); }

  /** The pelvis-frame matrix of a bone below the pelvis, from the local transforms. */
  function chain(bone, out) {
    bone.updateMatrix(); out.copy(bone.matrix);
    for (let p = bone.parent; p && p !== cur.pelvis; p = p.parent) { p.updateMatrix(); out.premultiply(p.matrix); }
    return out;
  }

  /** The legs now, sampled into the bell's frame. */
  function sampleLegs(b) {
    let n = 0;
    for (const s of SIDES) {
      chain(b.bones.thigh[s], mT); chain(b.bones.calf[s], mC); chain(b.bones.foot[s], mF);
      pHip.setFromMatrixPosition(mT); pKnee.setFromMatrixPosition(mC); pAnk.setFromMatrixPosition(mF);
      const hasBall = !!b.bones.ball[s];
      if (hasBall) pBall.setFromMatrixPosition(chain(b.bones.ball[s], mB));
      n = segment(b, pHip, pKnee, ALONG.thigh, b.girth[s].thigh, n, CENTRE);
      n = segment(b, pKnee, pAnk, ALONG.calf, b.girth[s].calf, n, SECTIONS);
      n = segment(b, pAnk, hasBall ? pBall : pAnk, ALONG.foot, b.girth[s].foot, n, SECTIONS);
    }
    return n;
  }
  function segment(b, a, c, along, g, n, secs) {
    for (let i = 0; i < along.length; i++) {
      const u = along[i];
      tmp.copy(a).lerp(c, u).sub(b.Wc).applyQuaternion(qHangInv).add(b.Wc);
      toFrame(b, tmp, f3);
      const rho = girthAt(g, u) + MARGIN_M;
      for (const [up, share] of secs) { sX[n] = f3[0]; sy[n] = f3[1] + up * rho; sZ[n] = f3[2]; sR[n] = share * rho; n++; }
    }
    return n;
  }

  function thighRaise(b) {
    let most = 0;
    for (const s of SIDES) {
      chain(b.bones.thigh[s], mT); chain(b.bones.calf[s], mC);
      pHip.setFromMatrixPosition(mT); pKnee.setFromMatrixPosition(mC);
      vA.subVectors(pHip, pKnee).normalize();
      most = Math.max(most, Math.acos(clamp(vA.dot(b.U), -1, 1)));
    }
    return most / DEG;
  }

  /** The hang: the pelvis's tilt since bind, mostly taken out, its turn kept; then the sway. */
  function hangRotation(b) {
    qK.identity();
    if (b.hasParent) {
      const now = b.pelvis.quaternion;
      qa.copy(b.pelvisBindQ).invert().premultiply(now);              // delta = now * bind^-1, in the parent
      const u = b.upParent, p = qa.x * u.x + qa.y * u.y + qa.z * u.z;
      qb.set(u.x * p, u.y * p, u.z * p, qa.w);                          // the twist about up
      if (qb.lengthSq() < 1e-12) qb.identity(); else qb.normalize();
      qUp.copy(qb).invert().premultiply(qa);                            // the swing = delta * twist^-1
      if (qUp.w < 0) qUp.set(-qUp.x, -qUp.y, -qUp.z, -qUp.w);
      const ang = 2 * Math.acos(clamp(qUp.w, -1, 1));
      if (ang > SWING_MAX) qUp.slerp(qW.identity(), 1 - SWING_MAX / ang);
      qUp.slerp(qW.identity(), HANG);                                    // keep 1 - HANG of it
      // K = now^-1 * swing' * twist * bind
      qK.copy(now).invert().multiply(qUp).multiply(qb).multiply(b.pelvisBindQ);
    }
    qa.setFromAxisAngle(b.Lf, -pend.f);
    qb.setFromAxisAngle(b.Fw, pend.l);
    qHang.copy(qK).multiply(qa).multiply(qb);
    qHangInv.copy(qHang).invert();
  }

  /** The pelvis's motion in the world: the pendulum and the pace. */
  function motion(b, dt) {
    b.pelvis.updateWorldMatrix(true, false);
    pw.setFromMatrixPosition(b.pelvis.matrixWorld);
    if (!(dt > 0)) return;
    let af = 0, al = 0, vf = 0;
    if (prev.has && pw.distanceTo(prev.p) < 1.5) {
      vel.subVectors(pw, prev.p).divideScalar(dt);
      b.pelvis.getWorldQuaternion(qW).invert();
      tmp2.copy(vel).applyQuaternion(qW).applyQuaternion(qHangInv);
      vf = tmp2.dot(b.Fw);
      if (prev.has > 1) {
        acc.subVectors(vel, prev.v).divideScalar(dt);
        const m = acc.length(); if (m > PENDULUM.maxAccel) acc.multiplyScalar(PENDULUM.maxAccel / m);
        tmp2.copy(acc).applyQuaternion(qW).applyQuaternion(qHangInv);
        af = tmp2.dot(b.Fw); al = tmp2.dot(b.Lf);
      }
      prev.v.copy(vel); prev.has = 2;
    } else prev.has = 1;
    prev.p.copy(pw);
    const { omega, zeta, length } = PENDULUM, max = PENDULUM.maxDeg * DEG;
    const steps = Math.max(1, Math.ceil(dt * 120)), h = dt / steps;
    for (let i = 0; i < steps; i++) {
      pend.vf += (-omega * omega * pend.f - 2 * zeta * omega * pend.vf - af / length) * h; pend.f += pend.vf * h;
      pend.vl += (-omega * omega * pend.l - 2 * zeta * omega * pend.vl - al / length) * h; pend.l += pend.vl * h;
    }
    if (Math.abs(pend.f) > max) { pend.f = Math.sign(pend.f) * max; pend.vf = 0; }
    if (Math.abs(pend.l) > max) { pend.l = Math.sign(pend.l) * max; pend.vl = 0; }
    spring(pace.x, pace.v, 0, Math.max(0, vf), OMEGA.pace, dt);
  }

  /** How far each panel must open at each leg sample (radial, m), from the rays. */
  function measure(b, n) {
    need.fill(0);
    const { allow, rayK, rayGain, raySin, rayCos, rowAllow, yHem, yTop, restS } = b;
    for (let s = 0; s < n; s++) {
      // Where it stood (the allowance clears it there): it cannot push by more than it moved.
      const ex = sX[s] - restS[s * 3], ey = sy[s] - restS[s * 3 + 1], ez = sZ[s] - restS[s * 3 + 2];
      if (ex * ex + ey * ey + ez * ez < NEED_MIN * NEED_MIN) continue;
      // A leg just under the hem still reaches into the cloth by its own girth (the calf of a
      // shin swung back under a coat's skirts): it pushes there with its section at the hem.
      let y = sy[s], rho = sR[s];
      if (y > yTop - 0.01) continue;
      const ye = Math.max(y, yHem + 0.01);
      if (ye !== y) {
        const dy = ye - y;
        if (Math.abs(dy) >= rho) continue;
        rho = Math.sqrt(rho * rho - dy * dy); y = ye; sy[s] = ye; sR[s] = rho;
      }
      const X = sX[s], Z = sZ[s], rc = Math.hypot(X, Z);
      const f = clamp((y - yHem) / ((yTop - yHem) / (ROWS - 1)), 0, ROWS - 1), i0 = Math.min(ROWS - 2, Math.floor(f)), fa = f - i0;
      // Deep inside the cloth on every ray: nothing to do (most of the leg, most frames).
      if (rc + rho < Math.min(rowAllow[i0], rowAllow[i0 + 1]) + NEED_MIN) continue;
      const phi = Math.atan2(X, Z), half = rc > rho ? Math.asin(rho / rc) : Math.PI;
      const j0 = Math.floor(((phi - half) / TAU) * RAYS), j1 = Math.ceil(((phi + half) / TAU) * RAYS);
      const jEnd = Math.min(j1, j0 + RAYS - 1);
      for (let jj = j0, j = ((j0 % RAYS) + RAYS) % RAYS; jj <= jEnd; jj++, j = j + 1 === RAYS ? 0 : j + 1) {
        const a = allow[i0 * RAYS + j] * (1 - fa) + allow[(i0 + 1) * RAYS + j] * fa;
        if (rc + rho - a < NEED_MIN) continue;
        const along = X * raySin[j] + Z * rayCos[j], perp = X * rayCos[j] - Z * raySin[j], disc = rho * rho - perp * perp;
        if (disc < 0) continue;
        const d = along + Math.sqrt(disc) - a;
        if (d < NEED_MIN) continue;
        const v = d / rayGain[j];
        for (let q = 0; q < 2; q++) { const k = rayK[j * 2 + q], c = k * SAMPLES + s; if (v > need[c]) need[c] = v; }
      }
    }
  }

  /** Each panel's least opening at the knee and at the hem that holds every sample. */
  function solve(b, n) {
    const { yTop, len, tMid, wA, wB } = b, lamH = 1 / tMid;
    // How much of the waist bone's and the hem bone's opening the cloth at each sample's height gets.
    for (let s = 0; s < n; s++) {
      const t = (yTop - sy[s]) / len, A = wA(t), Bw = wB(t), lam = t / tMid, mu = (t - tMid) / (1 - tMid);
      gainQ[s] = A * (1 - Bw) * lam + A * Bw * (lam - lamH * mu); gainH[s] = A * Bw * mu;
    }
    for (let k = 0; k < N_PANELS; k++) {
      let uQ = 0, uH = 0;
      for (let pass = 0; pass < 2; pass++) {
        for (let s = 0; s < n; s++) {
          const nd = need[k * SAMPLES + s]; if (!nd) continue;
          const a = gainQ[s], bb = gainH[s];
          if (bb > 0.5 * a && bb > 0.05) uH = Math.max(uH, (nd - a * uQ) / bb);
          else if (a > 0.05) uQ = Math.max(uQ, (nd - bb * uH) / a);
        }
      }
      reqQ[k] = clamp(uQ, 0, MAX_WAIST_M); reqH[k] = clamp(uH, 0, MAX_HEM_M);
    }
  }

  /** Set the bones from the state (no time passes). */
  function pose(dt) {
    const b = cur; if (!b) return;
    hangRotation(b);
    b.hang.quaternion.copy(qHang);
    const n = sampleLegs(b);
    measure(b, n); solve(b, n);
    const lamH = 1 / b.tMid;
    for (let k = 0; k < N_PANELS; k++) {
      const l = (k + N_PANELS - 1) % N_PANELS, r = (k + 1) % N_PANELS;
      tgtQ[k] = Math.max(reqQ[k], b.spread * Math.max(reqQ[l], reqQ[r]));
    }
    for (let k = 0; k < N_PANELS; k++) {
      const l = (k + N_PANELS - 1) % N_PANELS, r = (k + 1) % N_PANELS;
      tgtH[k] = Math.max(reqH[k], tgtQ[k] * (1 + b.flare * (lamH - 1)), b.spread * Math.max(reqH[l], reqH[r]));
    }
    // The whole bell follows its mean push, and the hem trails with the pace.
    let sQx = 0, sQz = 0, sHx = 0, sHz = 0;
    for (let k = 0; k < N_PANELS; k++) { const [dx, dz] = b.dir[k]; sQx += tgtQ[k] * dx; sQz += tgtQ[k] * dz; sHx += tgtH[k] * dx; sHz += tgtH[k] * dz; }
    const sh = b.shift / N_PANELS, trail = b.trail * Math.min(TRAIL.max, TRAIL.perMS * pace.x[0]);
    sQx *= sh; sQz *= sh; sHx *= sh; sHz = sHz * sh - trail; sQz -= trail * 0.5;
    // Nothing pushing and nothing still moving: the panels at rest (the asset as drawn).
    let still = trail === 0;
    for (let k = 0; k < N_PANELS && still; k++) if (tgtQ[k] || tgtH[k]) still = false;
    for (let i = 0; i < X.length && still; i++) if (X[i] || V[i]) still = false;
    if (still) {
      if (!b.atRest) { for (let k = 0; k < N_PANELS; k++) { b.waist[k].quaternion.identity(); b.hem[k].quaternion.identity(); } b.atRest = true; }
      return;
    }
    b.atRest = false;
    for (let k = 0; k < N_PANELS; k++) {
      const [dx, dz] = b.dir[k], o = k * 4;
      if (dt > 0) {
        spring(X, V, o, tgtQ[k] * dx + sQx, b.omega.waist, dt); spring(X, V, o + 1, tgtQ[k] * dz + sQz, b.omega.waist, dt);
        spring(X, V, o + 2, tgtH[k] * dx + sHx, b.omega.hem, dt); spring(X, V, o + 3, tgtH[k] * dz + sHz, b.omega.hem, dt);
      }
      // Contact is never late: the leg holds the panel out however the spring lags.
      hold(o, reqQ[k], MAX_WAIST_M, dx, dz); hold(o + 2, reqH[k], MAX_HEM_M, dx, dz);
      if (dt > 0 && !needsMotion(o)) for (let i = 0; i < 4; i++) { X[o + i] = 0; V[o + i] = 0; }
      // The waist bone swings P->Q onto Q + its displacement; the hem bone Q'->H onto H + its own.
      const Pk = b.P[k], Qk = b.Q[k], Hk = b.H[k];
      vA.subVectors(Qk, Pk); vB.copy(Qk).addScaledVector(b.Lf, X[o]).addScaledVector(b.Fw, X[o + 1]).sub(Pk);
      qa.setFromUnitVectors(vA.normalize(), vB.normalize());
      b.waist[k].quaternion.copy(qa);
      // Q' = P + R (Q - P); the hem's line from Q' to H + its displacement.
      vC.subVectors(Qk, Pk).applyQuaternion(qa).add(Pk);
      vB.copy(Hk).addScaledVector(b.Lf, X[o + 2]).addScaledVector(b.Fw, X[o + 3]).sub(vC);
      vA.subVectors(Hk, Qk);
      qb.setFromUnitVectors(vA.normalize(), vB.normalize());
      b.hem[k].quaternion.copy(qa).invert().multiply(qb);
    }
  }
  /** The panel held out to `req` along its own direction, and never past `max`. */
  function hold(i, req, max, dx, dz) {
    const rad = X[i] * dx + X[i + 1] * dz;
    if (rad < req) { X[i] += (req - rad) * dx; X[i + 1] += (req - rad) * dz; }
    const m = Math.hypot(X[i], X[i + 1]); if (m > max) { X[i] *= max / m; X[i + 1] *= max / m; }
  }
  const needsMotion = (o) => { for (let i = 0; i < 4; i++) if (Math.abs(X[o + i]) > 1e-5 || Math.abs(V[o + i]) > 1e-4) return true; return false; };

  function apply(dt, { state = 'standing', root = null, gait = null } = {}) {
    void root; void gait; // the legs and the pelvis say it all; the gait's numbers are not needed
    if (!cur) return;
    dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.1) : 0;
    const raise = thighRaise(cur);
    seated = state === 'seated' || (seated ? raise > STAND_DEG : raise > SEATED_DEG);
    const want = seated ? 'asset' : 'bell';
    if (want !== mode) {
      mode = want; useCur(mode === 'bell');
      if (mode === 'asset') { X.fill(0); V.fill(0); pend.f = pend.l = pend.vf = pend.vl = 0; }
      prev.has = 0; // the pelvis's last place is stale: no kick when the bell comes back
    }
    if (mode === 'asset') return;
    hangRotation(cur);
    motion(cur, dt);
    pose(dt);
  }

  const round = (x) => Math.round(x * 1e6) / 1e6;
  function snapshot() {
    let hem = 0;
    for (let k = 0; k < N_PANELS; k++) hem = Math.max(hem, Math.hypot(X[k * 4 + 2], X[k * 4 + 3]));
    return {
      bound: !!cur, mode, panels: N_PANELS, meshes: cur ? cur.own.length : 0,
      hem_open_m: round(hem), sway_deg: [round(pend.f / DEG), round(pend.l / DEG)], pace_ms: round(pace.x[0]),
      state: Array.from(X, round).concat(Array.from(V, round)),
    };
  }

  /** Let go of one body's panels (its teardown also does this, through the skeleton). */
  function release(target) {
    const b = bindings.get(target);
    if (!b) return;
    if (b === cur) cur = null;
    unbind(b);
  }

  const beyond = (sc) => Number.isFinite(sc?.userData?.chicago4d_human?.lod) && sc.userData.chicago4d_human.lod > maxLod;
  if (!bind(scene) && !beyond(scene)) return null;
  return {
    bind, apply, snapshot, release,
    /** Put the drawn body back as the asset draws it and stop. */
    dispose() { if (cur) release(cur.scene); },
    get bound() { return !!cur; },
    get mode() { return mode; },
    /** The bell's frame and panels (the test reads them). */
    get binding() { return cur; },
  };
}

/** A point in the pelvis frame to the figure frame (left, up, front) about the hips. */
function toFrame(b, p, out) {
  const x = p.x - b.O.x, y = p.y - b.O.y, z = p.z - b.O.z;
  out[0] = x * b.Lf.x + y * b.Lf.y + z * b.Lf.z; out[1] = x * b.U.x + y * b.U.y + z * b.U.z; out[2] = x * b.Fw.x + y * b.Fw.y + z * b.Fw.z;
  return out;
}
