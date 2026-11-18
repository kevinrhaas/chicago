// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-frockcoat.js — John J. Glessner's frock coat cut as a 1904 frock coat (T-3553).
 *
 * The catalogue review of his 1904 day dress (data/people_match/subjects/glessner_john_j_1904,
 * the people_match rig, T-3417) laid our stills beside the pictures the figure was built
 * after (data/people_match/reference_sets/gentleman_1904.json: Glessner's own 1897 plate, the
 * 1904 Clinedinst print of Taft buttoned and Root open, the 1903 State Street stereograph) and
 * found the coat read as a cassock or an overcoat. The owner approved the tailoring fixes on
 * 2026-11-17 ("yes do tailoring fixes"). Five of them, here, once per loaded body (before any
 * figure is cloned from it, as human-seat.js and human-coat.js do), on every level:
 *
 *  1. Length. The skirts fell to 3 cm under the knee joint, and swinging, to the top of the
 *     calf; Taft's stop at the knee. They are shortened from the waist seam down, every
 *     point in proportion, so the hem lies HEM_ABOVE_KNEE_M above the knee joint.
 *  2. Waist. The coat stood straight from chest to hem. Every layer round the waist seam
 *     (coat body, skirts, waistcoat, trousers' top) is drawn toward the body in proportion
 *     to how far it stood off the skin, by WAIST.squeeze at the seam and fading over
 *     WAIST.up above and WAIST.down below it; layers keep their order (each WAIST.gap outside
 *     what is under it), the skirts hang from it. The near levels only: the far levels' cloth
 *     is too coarse to draw in without the waistcoat showing between its points.
 *  3. Front. Buttoned to the throat, the lapels piece lay black on black and the black
 *     waistcoat filled the opening, so only the collar and tie showed. The coat's opening
 *     is widened by up to FRONT.widen (nothing at the button and at the collar), the lapels
 *     piece moved out with its edge along the coat's own surface; the waistcoat's V is cut
 *     down to FRONT.apexAboveShirt above the foot of the shirt front and out to FRONT.slope,
 *     never closer than FRONT.showWaistcoat inside the coat's edge. Cloth inside an opening
 *     is folded back behind the layer under it (FRONT.sink), never removed, so the shirt
 *     front and tie show in a V inside the waistcoat, inside the lapels, as Root and Taft show.
 *  4. Collar. The standing collar stood 2.7 cm over the coat's collar and was drawn in the
 *     export's flat picture at 8-bit 202, the recipe's linear 0.8 written as if it were sRGB,
 *     so it read grey. It is raised by COLLAR.raise at the back and sides (nothing under the
 *     jaw), and the shirt's cloth is drawn in the recipe's own linear colour
 *     (data/humans/recipes/gentleman_1904.json colors_linear_rgba), without the picture.
 *  5. Vent. The skirts were one closed tube. A frock coat's back skirts are cut in two at a
 *     centre-back vent: the skirts' mesh is split along a line of its own edges up the
 *     middle of the back from the hem to VENT.belowSeam under the waist seam (new vertices
 *     on the right side, copies of their own in every attribute), the left side lapped
 *     VENT.lap over the right and VENT.out behind it at the top, the two hanging apart to
 *     VENT.open at the hem below VENT.openFrom of its length, flush again where the vent
 *     meets the cloth above it.
 *  6. Facings (round 4: "the lapels are black on black with no facing, so they read only by
 *     the V's outline"). Taft's lapels in the Clinedinst print are a lighter band than his
 *     coat, the sheen of a faced lapel; Root's show it along the roll. The lapels' front faces
 *     are copied FACING.lift over the cloth and drawn in the body's own silk, the tie's
 *     material (roughness 0.45 against the wool's 0.86), appended to the tie's mesh; their
 *     normals smoothed (silk shows every facet of a low cloth) and turned FACING.tilt up, as
 *     a lapel rolls out over the chest, so the facing catches the sky and the sun the coat's
 *     cloth does not. Every level.
 *  7. Hip buttons (round 4): two covered buttons at the back of the waist seam, HIP_BUTTONS.apart
 *     either side of the middle, over the top of the vent's pleats, as a frock coat has; small
 *     domes in the same silk, skinned as the coat's back there. Near levels.
 *
 * Topology changes only by the vent's split (the skirts gain one vertex per vertex on the
 * line) and by the silk appended to the tie's mesh (its own vertices and triangles first and
 * as drawn); UVs and skin weights are copied, never changed; the rest moves positions and the
 * normals of what moved (from the faces, each place's copies sharing one, turned as the
 * asset's own were). human-coat.js's closeVents finds no vent on this coat as drawn (its
 * skirts were closed), so the two never meet: wired after fitCoats, this lap is the vent's.
 * human-skirt.js reads the cloth at bind, after this, so its panels hang from the new hem.
 *
 * Keyed to the pieces of the one body that wears them (frock_coat_body, frock_coat_skirts,
 * frock_coat_lapels, a waistcoat and a shirt with a standing collar on the same level; the
 * silk where the level has a silk four-in-hand tie): in
 * 2026-11 only glessner_john_j_1904, worn by hi_glessner_john_j_1904 alone. A body without
 * them is left exactly as drawn.
 *
 * Cost: a few thousand vertices per level, once per parse (milliseconds); the silk adds 446
 * vertices to the tie at the near level, 258 at the next, 83 and 42 farther. No mesh,
 * texture, material, draw call or program. A reconstructed cut after the pictures (liberty
 * L-frockcoat-3553).
 */
import * as THREE from 'three';

const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';
const ADULT_LEG_M = 0.85;

/** The pieces, by name (the mesh is `<asset>_<piece>_lod<N>`). */
export const PIECES = Object.freeze({
  body: /(^|_)frock_coat_body$/, skirts: /(^|_)frock_coat_skirts$/, lapels: /(^|_)frock_coat_lapels$/,
  waistcoat: /(^|_)waistcoat(_[a-z]+)*$/, shirt: /(^|_)shirt_standing_collar$/, trousers: /(^|_)(straight_)?trousers$/,
});
/** 1. The hem this far above the knee joint (metres, per 0.85 m of leg). */
export const HEM_ABOVE_KNEE_M = 0.03;
/** 2. At the seam each layer keeps this share of how far it stood off the skin, and stays `gap`
 * outside everything under it; on levels up to `levels` (the far levels' cloth is too coarse to
 * draw in without the waistcoat coming through between its points: measured, they keep their waist). */
export const WAIST = Object.freeze({ squeeze: 0.5, up: 0.12, down: 0.08, gap: 0.003, levels: 1 });
/** 3. The front: the coat's edge out by `widen` at most; the waistcoat's V from `apexAboveShirt`
 * over the foot of the shirt front, `slope` out per metre up, `showWaistcoat` inside the coat's
 * edge at least; cloth inside an opening folded `sink` behind what lies under it, its edge
 * turning over `band`; the lapels kept `lift` over the coat they are moved onto. */
export const FRONT = Object.freeze({ widen: 0.006, apexAboveShirt: 0.012, slope: 0.9, showWaistcoat: 0.006, sink: 0.008, band: 0.008, rise: 0.08, collarFade: 0.06, lift: 0.005 });
/** 4. The collar raised `raise` behind and at the sides, nothing within `frontDeg` of the
 * front (the jaw), in full past `fullDeg`; the band under the top edge that stretches. */
export const COLLAR = Object.freeze({ raise: 0.018, frontDeg: 35, fullDeg: 75, band: 0.035, colour: Object.freeze([0.8, 0.8, 0.78]) });
/** 5. The vent: from the hem to `belowSeam` under the skirts' top; lapped `lap` each way and
 * the left `out` behind at the top, `open` apart at the hem below `openFrom` of its length,
 * the shift fading into each side over `fade` and to nothing at its top over `topFade`. */
export const VENT = Object.freeze({ belowSeam: 0.05, lap: 0.004, out: 0.005, open: 0.024, openFrom: 0.5, fade: 0.05, topFade: 0.04 });
/** 6. Silk facings: the lapels' front faced in the silk the tie is drawn in, `lift` over the
 * cloth (its own edges turned `turn` back toward it, so no gap shows at the lapel's edge), on
 * every level; the silk is the body's own silk-tie mesh, so no mesh, material or draw call. */
export const FACING = Object.freeze({ lift: 0.0012, minFront: 0.35, turn: 0.0008, smooth: 2, tilt: 0.3 });
/** 7. Hip buttons: two, at the waist seam over the top of the vent's pleats, `apart` either side
 * of the middle of the back, `radius` across and domed `dome`, covered in the facings' silk;
 * `rings` x `segments` points each, on the levels up to `levels`. */
export const HIP_BUTTONS = Object.freeze({ apart: 0.045, radius: 0.0085, dome: 0.0035, lift: 0.0008, segments: 12, rings: 3, levels: 1 });

/** The silk the facings and buttons are drawn in: the body's own silk tie. */
export const SILK = Object.freeze({ piece: /(^|_)four_in_hand_tie$/, material: /^accessory__silk_tie/ });

const pieceName = (mesh, assetId) => {
  let n = mesh.name ?? '';
  if (assetId && n.startsWith(`${assetId}_`)) n = n.slice(assetId.length + 1);
  return n.replace(/_lod\d*$/, '');
};
const lodOf = (o) => (o.name ?? '').match(/_lod(\d*)$/)?.[1] ?? '';

function bindJoint(sk, name) {
  const i = sk.bones.findIndex((b) => b?.name === name);
  return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert());
}
/** The body's frame at bind: O mid-hips, U up, L left, F forward; the knee's height; the scale. */
export function frameOf(sk) {
  const hl = bindJoint(sk, 'thigh_l'), hr = bindJoint(sk, 'thigh_r'), al = bindJoint(sk, 'foot_l'), ar = bindJoint(sk, 'foot_r');
  const kl = bindJoint(sk, 'calf_l'), kr = bindJoint(sk, 'calf_r'), neck = bindJoint(sk, 'neck_01');
  if (!hl || !hr || !al || !ar || !kl || !kr || !neck) return null;
  const O = hl.clone().add(hr).multiplyScalar(0.5), U = O.clone().sub(al.clone().add(ar).multiplyScalar(0.5)).normalize();
  const leg = (hl.distanceTo(al) + hr.distanceTo(ar)) / 2;
  const L = hl.clone().sub(hr); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  const knee = (kl.clone().sub(O).dot(U) + kr.clone().sub(O).dot(U)) / 2;
  const nk = neck.clone().sub(O);
  return { O, U, L, F, scale: leg / ADULT_LEG_M, knee, neck: [nk.dot(L), nk.dot(U), nk.dot(F)] };
}

/** A mesh in the body frame: X left, Y up from the hips, Z forward. */
function layerOf(mesh, fr) {
  const pos = mesh.geometry.attributes.position, n = pos.count, v = new THREE.Vector3();
  const X = new Float64Array(n), Y = new Float64Array(n), Z = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(fr.O);
    X[i] = v.dot(fr.L); Y[i] = v.dot(fr.U); Z[i] = v.dot(fr.F);
  }
  return { mesh, n, X, Y, Z, moved: new Uint8Array(n) };
}
function writeBack(ly, fr) {
  const pos = ly.mesh.geometry.attributes.position, Binv = ly.mesh.bindMatrix.clone().invert(), v = new THREE.Vector3();
  let any = false;
  for (let i = 0; i < ly.n; i++) {
    if (!ly.moved[i]) continue;
    v.copy(fr.O).addScaledVector(fr.L, ly.X[i]).addScaledVector(fr.U, ly.Y[i]).addScaledVector(fr.F, ly.Z[i]).applyMatrix4(Binv);
    pos.setXYZ(i, v.x, v.y, v.z); any = true;
  }
  if (!any) return;
  pos.needsUpdate = true;
  renormal(ly, fr);
  ly.mesh.geometry.computeBoundingBox(); ly.mesh.geometry.computeBoundingSphere();
}
/** Welded groups: a UV seam's copies of one place are one point. */
function groupsOf(ly) {
  const gid = new Int32Array(ly.n), ids = new Map();
  for (let i = 0; i < ly.n; i++) {
    const k = `${Math.round(ly.X[i] * 2e4)},${Math.round(ly.Y[i] * 2e4)},${Math.round(ly.Z[i] * 2e4)}`;
    let g = ids.get(k); if (g === undefined) ids.set(k, (g = ids.size)); gid[i] = g;
  }
  return { gid, G: ids.size };
}
/** The normals of what moved, from its faces (area-weighted), each place's copies that faced
 * the same way as drawn sharing one (a hard edge's copies keep theirs apart), turned to the
 * side the asset's own normals faced there. */
function renormal(ly, fr) {
  const geo = ly.mesh.geometry, nrm = geo.attributes.normal, idx = geo.index;
  if (!nrm || !idx) return;
  const nm = new THREE.Matrix3().getNormalMatrix(ly.mesh.bindMatrix), back = new THREE.Matrix3().getNormalMatrix(ly.mesh.bindMatrix.clone().invert());
  // Each vertex's normal as drawn, in the body frame.
  const ON = new Float64Array(ly.n * 3), v = new THREE.Vector3();
  for (let i = 0; i < ly.n; i++) {
    v.fromBufferAttribute(nrm, i).applyMatrix3(nm).normalize();
    ON[i * 3] = v.dot(fr.L); ON[i * 3 + 1] = v.dot(fr.U); ON[i * 3 + 2] = v.dot(fr.F);
  }
  const { gid } = groupsOf(ly), cl = new Int32Array(ly.n), heads = new Map();
  let C = 0;
  for (let i = 0; i < ly.n; i++) {
    const list = heads.get(gid[i]) ?? [];
    let c = -1;
    for (const [h, k] of list) if (ON[h * 3] * ON[i * 3] + ON[h * 3 + 1] * ON[i * 3 + 1] + ON[h * 3 + 2] * ON[i * 3 + 2] > 0.85) { c = k; break; }
    if (c < 0) { c = C++; list.push([i, c]); heads.set(gid[i], list); }
    cl[i] = c;
  }
  const moved = new Uint8Array(C);
  for (let i = 0; i < ly.n; i++) if (ly.moved[i]) moved[cl[i]] = 1;
  const sum = new Float64Array(C * 3), a = idx.array;
  for (let t = 0; t < a.length; t += 3) {
    const i0 = a[t], i1 = a[t + 1], i2 = a[t + 2];
    if (!moved[cl[i0]] && !moved[cl[i1]] && !moved[cl[i2]]) continue;
    const e1 = [ly.X[i1] - ly.X[i0], ly.Y[i1] - ly.Y[i0], ly.Z[i1] - ly.Z[i0]], e2 = [ly.X[i2] - ly.X[i0], ly.Y[i2] - ly.Y[i0], ly.Z[i2] - ly.Z[i0]];
    const n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    for (const i of [i0, i1, i2]) {
      // A face turned against the drawn normal there (the other side of a hard edge) is not counted.
      const c = cl[i], d = n[0] * ON[i * 3] + n[1] * ON[i * 3 + 1] + n[2] * ON[i * 3 + 2], sg = d < 0 ? -1 : 1;
      sum[c * 3] += sg * n[0]; sum[c * 3 + 1] += sg * n[1]; sum[c * 3 + 2] += sg * n[2];
    }
  }
  // The frame is right-handed (L x U = F), so a frame normal (x, y, z) is x L + y U + z F.
  const s = new THREE.Vector3();
  for (let i = 0; i < ly.n; i++) {
    const c = cl[i];
    if (!moved[c]) continue;
    s.set(0, 0, 0).addScaledVector(fr.L, sum[c * 3]).addScaledVector(fr.U, sum[c * 3 + 1]).addScaledVector(fr.F, sum[c * 3 + 2]);
    if (s.lengthSq() < 1e-20) continue;
    s.applyMatrix3(back).normalize();
    nrm.setXYZ(i, s.x, s.y, s.z);
  }
  nrm.needsUpdate = true;
}

/** A height field of a layer's front (Z, the most forward) over (X, Y) cells. */
function heightField(layers, keep, cell = 0.006) {
  const cells = new Map(), key = (ix, iy) => ix * 100003 + iy;
  for (const ly of layers) for (let i = 0; i < ly.n; i++) {
    if (!keep(ly, i)) continue;
    const k = key(Math.floor(ly.X[i] / cell), Math.floor(ly.Y[i] / cell));
    const c = cells.get(k);
    if (c === undefined || ly.Z[i] > c) cells.set(k, ly.Z[i]);
  }
  // The highest within one cell round (a conservative top: what is folded behind it stays behind).
  return (x, y) => {
    const ix = Math.floor(x / cell), iy = Math.floor(y / cell);
    let z = -Infinity;
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) { const c = cells.get(key(ix + a, iy + b)); if (c !== undefined && c > z) z = c; }
    return z;
  };
}
/** The front surface of a layer (for laying a piece along it): each cell's most forward point,
 * blended between cell centres. */
function surfaceField(ly, keep, cell = 0.008) {
  const cells = new Map(), key = (ix, iy) => ix * 100003 + iy;
  for (let i = 0; i < ly.n; i++) {
    if (!keep(i)) continue;
    const k = key(Math.floor(ly.X[i] / cell), Math.floor(ly.Y[i] / cell));
    if (!(cells.get(k) >= ly.Z[i])) cells.set(k, ly.Z[i]);
  }
  return (x, y) => {
    const fx = x / cell - 0.5, fy = y / cell - 0.5, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
    let sw = 0, sz = 0;
    for (const [a, b, w] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]]) {
      const z = cells.get(key(ix + a, iy + b)); if (z === undefined || w <= 0) continue; sw += w; sz += w * z;
    }
    return sw > 1e-6 ? sz / sw : NaN;
  };
}
/** Open (boundary) edges of a mesh, by welded group, as pairs of a representative vertex. */
function openEdges(ly) {
  const { gid } = groupsOf(ly), a = ly.mesh.geometry.index.array, W = 4194304, edges = new Map();
  for (let t = 0; t < a.length; t += 3) for (let k = 0; k < 3; k++) {
    const p = gid[a[t + k]], q = gid[a[t + (k + 1) % 3]];
    const e = p < q ? p * W + q : q * W + p;
    const c = edges.get(e); edges.set(e, c ? [c[0] + 1, c[1], c[2]] : [1, a[t + k], a[t + (k + 1) % 3]]);
  }
  const out = [];
  for (const [, c] of edges) if (c[0] === 1) out.push([c[1], c[2]]);
  return out;
}
/** A table y -> value, linearly interpolated, held flat past its ends. */
function table(rows) {
  rows.sort((p, q) => p[0] - q[0]);
  return (y) => {
    if (!rows.length) return NaN;
    if (y <= rows[0][0]) return rows[0][1];
    for (let i = 1; i < rows.length; i++) if (y <= rows[i][0]) { const [y0, v0] = rows[i - 1], [y1, v1] = rows[i]; return v0 + (v1 - v0) * (y - y0) / ((y1 - y0) || 1); }
    return rows[rows.length - 1][1];
  };
}
/** Rows of (y, mean value) from samples, binned every `step`. */
function binned(samples, step) {
  const bins = new Map();
  for (const [y, v] of samples) { const k = Math.round(y / step); const b = bins.get(k) ?? [0, 0, 0]; b[0] += y; b[1] += v; b[2]++; bins.set(k, b); }
  return [...bins.values()].map((b) => [b[0] / b[2], b[1] / b[2]]);
}

// ---- 1. length ------------------------------------------------------------------------------
function shorten(S, fr) {
  let top = -Infinity, hem = Infinity;
  for (let i = 0; i < S.n; i++) { top = Math.max(top, S.Y[i]); hem = Math.min(hem, S.Y[i]); }
  const want = fr.knee + HEM_ABOVE_KNEE_M * fr.scale;
  if (!(want > hem + 0.005) || !(want < top)) return { from: hem, to: hem, top };
  const k = (top - want) / (top - hem);
  for (let i = 0; i < S.n; i++) { S.Y[i] = top - (top - S.Y[i]) * k; S.moved[i] = 1; }
  return { from: hem, to: want, top };
}

// ---- 2. waist -------------------------------------------------------------------------------
function suppress(layers, skin, seam, fr) {
  const up = WAIST.up * fr.scale, down = WAIST.down * fr.scale, lo = seam - down, hi = seam + up;
  // The trunk's axis at each height (the middle of the skin front to back at the middle) and the
  // skin's radius round it, every 1 cm and 6 degrees (arms and hands, out level at bind, left out).
  const STEP = 0.01, AB = 60, rows = new Map();
  for (let i = 0; i < skin.n; i++) {
    const y = skin.Y[i]; if (y < lo - 0.03 || y > hi + 0.03 || Math.abs(skin.X[i]) > 0.1 * fr.scale) continue;
    const k = Math.round(y / 0.02), r = rows.get(k) ?? [Infinity, -Infinity, 0, 0];
    r[0] = Math.min(r[0], skin.Z[i]); r[1] = Math.max(r[1], skin.Z[i]); r[2] += y; r[3]++; rows.set(k, r);
  }
  const axis = table([...rows.values()].map((r) => [r[2] / r[3], (r[0] + r[1]) / 2]));
  const rk = (iy, ia) => iy * 1000 + ia;
  const angleBin = (x, z) => ((Math.round(Math.atan2(x, z) / (2 * Math.PI) * AB) % AB) + AB) % AB;
  // The outermost radius of some layers round the axis, every 1 cm and 6 degrees; asked of a
  // point, the most within a cell of it (so what is over it is held over all of it).
  const field = () => {
    const rad = new Map();
    const add = (ly) => {
      for (let i = 0; i < ly.n; i++) {
        const y = ly.Y[i]; if (y < lo - 2 * STEP || y > hi + 2 * STEP) continue;
        const z = ly.Z[i] - axis(y), r = Math.hypot(ly.X[i], z); if (r > 0.3 * fr.scale) continue;
        const k = rk(Math.round(y / STEP), angleBin(ly.X[i], z));
        if (!(rad.get(k) >= r)) rad.set(k, r);
      }
    };
    const at = (y, x, z) => {
      const iy = Math.round(y / STEP), ia = angleBin(x, z);
      let r = -Infinity;
      for (const dy of [0, 1, -1]) for (const da of [0, 1, -1]) { const v = rad.get(rk(iy + dy, (ia + da + AB) % AB)); if (v !== undefined && v > r) r = v; }
      return r;
    };
    return { add, at };
  };
  const skinF = field(); skinF.add(skin);
  // Everything already fitted that lies under the next layer: the skin, then each layer in turn.
  const underF = field(); underF.add(skin);
  const gap = WAIST.gap * fr.scale;
  let most = 0;
  const w = (y) => (y >= seam ? 1 - smooth((y - seam) / up) : 1 - smooth((seam - y) / down));
  for (const group of layers) {
    for (const ly of group) for (let i = 0; i < ly.n; i++) {
      const y = ly.Y[i]; if (y <= lo || y >= hi) continue;
      const c = axis(y), z = ly.Z[i] - c, r = Math.hypot(ly.X[i], z);
      if (r < 1e-4 || r > 0.35 * fr.scale) continue;
      const sR = skinF.at(y, ly.X[i], z);
      if (!(sR > 0) || r <= sR) continue;
      const f = 1 - (1 - WAIST.squeeze) * w(y);
      const r2 = Math.min(r, Math.max(sR + (r - sR) * f, underF.at(y, ly.X[i], z) + gap));
      if (r - r2 < 1e-5) continue;
      ly.X[i] *= r2 / r; ly.Z[i] = c + z * (r2 / r); ly.moved[i] = 1; most = Math.max(most, r - r2);
    }
    for (const ly of group) underF.add(ly);
  }
  return { seam, max_m: most };
}

// ---- 3. front -------------------------------------------------------------------------------
function openFront({ body, lapels, waistcoat, shirt }, fr) {
  const s = fr.scale, sink = FRONT.sink * s, band = FRONT.band * s;
  // The coat's opening edge as drawn: its open edges at the front, near the middle.
  const edgeRows = [];
  let topFront = -Infinity, button = Infinity;
  for (const [a, b] of openEdges(body)) for (const i of [a, b]) {
    if (body.Z[i] < 0.05 * s || Math.abs(body.X[i]) > 0.13 * s || body.Y[i] < 0.25 * s) continue;
    edgeRows.push([body.Y[i], Math.abs(body.X[i])]);
    topFront = Math.max(topFront, body.Y[i]); button = Math.min(button, body.Y[i]);
  }
  if (edgeRows.length < 4) return null;
  const E = table(binned(edgeRows, 0.01 * s));
  const rise = FRONT.rise * s, fade = FRONT.collarFade * s;
  const widen = (y) => FRONT.widen * s * smooth((y - button) / rise) * (1 - smooth((y - (topFront - fade)) / (fade - 0.01 * s)));
  const NE = (y) => E(y) + widen(y);
  // The shirt front's foot, at the middle.
  let shirtFoot = Infinity;
  for (let i = 0; i < shirt.n; i++) if (shirt.Z[i] > 0 && Math.abs(shirt.X[i]) < 0.03 * s && shirt.Y[i] > 0.25 * s) shirtFoot = Math.min(shirtFoot, shirt.Y[i]);
  const apex = shirtFoot + FRONT.apexAboveShirt * s;
  const WE = (y) => Math.min(FRONT.slope * (y - apex), NE(y) - FRONT.showWaistcoat * s);
  const shirtTop = heightField([shirt], (ly, i) => ly.Z[i] > 0);
  // The waistcoat's V: what lies inside it folds back behind the shirt.
  let wcMoved = 0;
  for (let i = 0; i < waistcoat.n; i++) {
    const y = waistcoat.Y[i], x = Math.abs(waistcoat.X[i]);
    if (waistcoat.Z[i] <= 0 || y < apex || y > topFront + 0.02 * s) continue;
    const e = WE(y); if (!(e > 0)) continue;
    const w = 1 - smooth((x - (e - band)) / band); if (!(w > 1e-3)) continue;
    const h = shirtTop(waistcoat.X[i], y); if (!(h > -Infinity)) continue;
    const z = Math.min(waistcoat.Z[i], h - sink);
    if (!(z < waistcoat.Z[i] - 1e-5)) continue;
    waistcoat.Z[i] += (z - waistcoat.Z[i]) * w; waistcoat.moved[i] = 1; wcMoved++;
  }
  // The coat's widened opening: what lies inside the new edge folds back behind the waistcoat or shirt.
  const under = heightField([shirt, waistcoat], (ly, i) => ly.Z[i] > 0);
  const coatFront = surfaceField(body, (i) => body.Z[i] > 0.05 * s && Math.abs(body.X[i]) < 0.2 * s);
  const coatTop = heightField([body], (ly, i) => ly.Z[i] > 0.05 * s && Math.abs(ly.X[i]) < 0.2 * s, 0.005);
  let coatMoved = 0;
  for (let i = 0; i < body.n; i++) {
    const y = body.Y[i], x = Math.abs(body.X[i]);
    if (body.Z[i] < 0.03 * s || y < button || y > topFront || x > 0.16 * s) continue;
    const d = widen(y); if (!(d > 1e-4)) continue;
    const w = 1 - smooth((x - NE(y)) / band); if (!(w > 1e-3)) continue;
    const h = under(body.X[i], y); if (!(h > -Infinity)) continue;
    const z = Math.min(body.Z[i], h - sink);
    if (!(z < body.Z[i] - 1e-5)) continue;
    body.Z[i] += (z - body.Z[i]) * w; body.moved[i] = 1; coatMoved++;
  }
  // The lapels move out with the edge, along the coat's own surface.
  let lapMoved = 0;
  for (let i = 0; i < lapels.n; i++) {
    const y = lapels.Y[i], d = widen(y); if (!(d > 1e-5)) continue;
    const x = lapels.X[i], x2 = x + Math.sign(x || 1) * d;
    const z0 = coatFront(x, y), z1 = coatFront(x2, y);
    lapels.X[i] = x2;
    if (Number.isFinite(z0) && Number.isFinite(z1)) lapels.Z[i] += z1 - z0;
    // Never under the coat it lies on (its own surface, as drawn, just under it).
    const top = coatTop(x2, y);
    if (top > -Infinity) lapels.Z[i] = Math.max(lapels.Z[i], top + FRONT.lift * s);
    lapels.moved[i] = 1; lapMoved++;
  }
  return { button, topFront, shirtFoot, apex, widen_m: FRONT.widen * s, moved: { waistcoat: wcMoved, coat: coatMoved, lapels: lapMoved } };
}

// ---- 4. collar ------------------------------------------------------------------------------
function standCollar(shirt, fr) {
  const s = fr.scale, [nx, , nz] = fr.neck;
  const deg = (i) => Math.abs(Math.atan2(shirt.X[i] - nx, shirt.Z[i] - nz)) * 180 / Math.PI;
  // The collar's top edge by angle round the neck (every 10 degrees).
  const top = new Map();
  let neckTop = -Infinity;
  for (let i = 0; i < shirt.n; i++) neckTop = Math.max(neckTop, shirt.Y[i]);
  for (let i = 0; i < shirt.n; i++) {
    if (shirt.Y[i] < neckTop - 0.08 * s || Math.abs(shirt.X[i] - nx) > 0.15 * s) continue;
    const k = Math.round(deg(i) / 10);
    if (!(top.get(k) >= shirt.Y[i])) top.set(k, shirt.Y[i]);
  }
  const topAt = (a) => { const k = a / 10, k0 = Math.floor(k), k1 = k0 + 1, t = k - k0; const v0 = top.get(k0) ?? top.get(k1), v1 = top.get(k1) ?? v0; return v0 + (v1 - v0) * t; };
  const raise = COLLAR.raise * s, bandM = COLLAR.band * s;
  let moved = 0;
  for (let i = 0; i < shirt.n; i++) {
    if (Math.abs(shirt.X[i] - nx) > 0.15 * s) continue;
    const a = deg(i), t = topAt(a); if (!Number.isFinite(t)) continue;
    const r = raise * smooth((a - COLLAR.frontDeg) / (COLLAR.fullDeg - COLLAR.frontDeg)); if (!(r > 1e-5)) continue;
    const y0 = t - bandM; if (shirt.Y[i] <= y0) continue;
    shirt.Y[i] += r * smooth((shirt.Y[i] - y0) / bandM); shirt.moved[i] = 1; moved++;
  }
  return { moved, raise_m: raise };
}
/** The shirt's cloth in the recipe's own linear colour, without the export's flat picture. */
function whiten(mesh) {
  const m = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  if (!m || m.userData?.chicagoFrockCollar) return false;
  m.map = null;
  m.color.setRGB(...COLLAR.colour, THREE.LinearSRGBColorSpace);
  m.userData = { ...(m.userData ?? {}), chicagoFrockCollar: true };
  m.needsUpdate = true;
  return true;
}

// ---- 5. vent --------------------------------------------------------------------------------
function splitVent(S, fr, top) {
  const s = fr.scale, geo = S.mesh.geometry, a = geo.index.array, n0 = S.n;
  const ventTop = top - VENT.belowSeam * s;
  let hem = Infinity;
  for (let i = 0; i < n0; i++) hem = Math.min(hem, S.Y[i]);
  if (!(ventTop - hem > 0.1 * s)) return null;
  // Each point's angle round the skirts' own axis from the middle of the back (+ to the left).
  const rows = new Map();
  for (let i = 0; i < n0; i++) { const k = Math.round(S.Y[i] / 0.02); const r = rows.get(k) ?? [Infinity, -Infinity, 0, 0]; r[0] = Math.min(r[0], S.Z[i]); r[1] = Math.max(r[1], S.Z[i]); r[2] += S.Y[i]; r[3]++; rows.set(k, r); }
  const axis = table([...rows.values()].map((r) => [r[2] / r[3], (r[0] + r[1]) / 2]));
  const phi = new Float64Array(n0);
  for (let i = 0; i < n0; i++) phi[i] = Math.atan2(S.X[i], -(S.Z[i] - axis(S.Y[i])));
  const below = (i) => S.Y[i] < ventTop && S.Z[i] < axis(S.Y[i]);
  // The cut runs along a column of the cloth's own points at one angle near the middle (the
  // lofted rings' nearest meridian), outer face, inner face and hem alike; a column some
  // triangle crosses is no cut. The nearest such column to the middle is taken.
  const TOL = 0.004, cands = [];
  for (let i = 0; i < n0; i++) if (below(i) && Math.abs(phi[i]) < 0.12) cands.push(phi[i]);
  cands.sort((p, q) => Math.abs(p) - Math.abs(q));
  let cut = null;
  for (const c of cands) {
    if (cut !== null && Math.abs(c - cut) < TOL) continue;
    let ok = true, onCut = 0, lowest = Infinity, highest = -Infinity;
    for (let i = 0; i < n0; i++) if (below(i) && Math.abs(phi[i] - c) < TOL) { onCut++; lowest = Math.min(lowest, S.Y[i]); highest = Math.max(highest, S.Y[i]); }
    if (onCut < 4 || lowest > hem + 0.01 * s || highest < ventTop - 0.06 * s) continue;
    for (let t = 0; t < a.length && ok; t += 3) {
      let l = false, r = false, any = false;
      for (let k = 0; k < 3; k++) { const i = a[t + k]; if (!below(i)) continue; any = true; if (phi[i] > c + TOL) l = true; else if (phi[i] < c - TOL) r = true; }
      if (any && l && r) ok = false;
    }
    if (ok) { cut = c; break; }
  }
  if (cut === null) return null;
  const onCut = (i) => below(i) && Math.abs(phi[i] - cut) < TOL;
  // The right side's triangles take new copies of the cut's points.
  const copyOf = new Map(), newIdx = a.slice();
  for (let t = 0; t < a.length; t += 3) {
    let touches = false, side = 0;
    for (let k = 0; k < 3; k++) { const i = a[t + k]; if (onCut(i)) touches = true; else side += phi[i] < cut ? -1 : 1; }
    if (!touches || side >= 0) continue; // the left side keeps the drawn points
    for (let k = 0; k < 3; k++) {
      const i = a[t + k]; if (!onCut(i)) continue;
      let j = copyOf.get(i);
      if (j === undefined) { j = n0 + copyOf.size; copyOf.set(i, j); }
      newIdx[t + k] = j;
    }
  }
  if (!copyOf.size) return null;
  const n1 = n0 + copyOf.size;
  // Every attribute grows by the copies, raw values copied (an interleaved one comes out plain).
  for (const [name, attr] of Object.entries(geo.attributes)) {
    const inter = !!attr.isInterleavedBufferAttribute, src = inter ? attr.data.array : attr.array;
    const stride = inter ? attr.data.stride : attr.itemSize, off = inter ? attr.offset : 0, k = attr.itemSize;
    const out = new src.constructor(n1 * k);
    for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) out[i * k + c] = src[i * stride + off + c];
    for (const [i, j] of copyOf) for (let c = 0; c < k; c++) out[j * k + c] = src[i * stride + off + c];
    geo.setAttribute(name, new THREE.BufferAttribute(out, k, attr.normalized));
  }
  const Idx = n1 > 65535 ? Uint32Array : a.constructor;
  geo.setIndex(new THREE.BufferAttribute(Idx.from(newIdx), 1));
  const grow = (A) => { const B = new Float64Array(n1); B.set(A); for (const [i, j] of copyOf) B[j] = A[i]; return B; };
  S.X = grow(S.X); S.Y = grow(S.Y); S.Z = grow(S.Z);
  const moved = new Uint8Array(n1); moved.set(S.moved); S.moved = moved; S.n = n1;
  // The cut's line across the back, and each point's side: the copies are the right's.
  const lineX = table(binned([...copyOf.keys()].map((i) => [S.Y[i], S.X[i]]), 0.01 * s));
  const right = new Uint8Array(n1);
  for (let i = 0; i < n1; i++) right[i] = i >= n0 ? 1 : onCut(i) ? 0 : phi[i] < cut ? 1 : 0;
  // Lapped at the top (left over right), apart at the hem.
  const len = ventTop - hem, fade = VENT.fade * s, topFade = VENT.topFade * s, lap = VENT.lap * s, out = VENT.out * s, open = VENT.open * s / 2;
  const sep = (y) => { const t = (ventTop - y) / len; return -lap + (lap + open) * smooth((t - VENT.openFrom) / (1 - VENT.openFrom)); };
  for (let i = 0; i < n1; i++) {
    if (S.Z[i] >= 0 || S.Y[i] > ventTop + 1e-6) continue;
    const y = S.Y[i], lx = lineX(y), dist = Math.abs(S.X[i] - lx);
    const f = (1 - smooth(dist / fade)) * smooth((ventTop - y) / topFade);
    if (!(f > 1e-4)) continue;
    const e = sep(y), target = right[i] ? -e : e;
    S.X[i] += (target - lx) * f;
    if (e < 0) S.Z[i] += (right[i] ? 0.4 : -1) * out * f * smooth(-e / lap);
    S.moved[i] = 1;
  }
  return { from: hem, to: ventTop, split: copyOf.size, cut_deg: cut * 180 / Math.PI };
}

// ---- 6, 7. silk: facings and hip buttons ---------------------------------------------------
/**
 * Append pieces given in the body frame (positions, normals; UVs and skin rows given) to
 * `host`, a skinned mesh of the same skeleton: its own vertices and triangles first and
 * unchanged, every attribute grown (an interleaved one comes out plain), no mesh, material
 * or draw call added. Returns the vertices added.
 */
function appendInto(host, fr, { P, N, UV, SI, SW, index }, boneOf = (j) => j) {
  const g = host.geometry, n0 = g.attributes.position.count, add = P.length / 3;
  if (!add) return 0;
  const inv = host.bindMatrix.clone().invert(), ni = new THREE.Matrix3().getNormalMatrix(inv), v = new THREE.Vector3();
  const next = {};
  for (const [name, attr] of Object.entries(g.attributes)) {
    const k = attr.itemSize, out = new THREE.BufferAttribute(new attr.array.constructor((n0 + add) * k), k, attr.normalized);
    for (let i = 0; i < n0; i++) for (let c = 0; c < k; c++) out.setComponent(i, c, attr.getComponent(i, c));
    next[name] = out;
  }
  for (let i = 0; i < add; i++) {
    const k = n0 + i;
    v.copy(fr.O).addScaledVector(fr.L, P[i * 3]).addScaledVector(fr.U, P[i * 3 + 1]).addScaledVector(fr.F, P[i * 3 + 2]).applyMatrix4(inv);
    next.position.setXYZ(k, v.x, v.y, v.z);
    if (next.normal) { v.set(0, 0, 0).addScaledVector(fr.L, N[i * 3]).addScaledVector(fr.U, N[i * 3 + 1]).addScaledVector(fr.F, N[i * 3 + 2]).applyMatrix3(ni).normalize(); next.normal.setXYZ(k, v.x, v.y, v.z); }
    if (next.uv) next.uv.setXY(k, UV[i * 2], UV[i * 2 + 1]);
    if (next.skinIndex && next.skinWeight) for (let c = 0; c < 4; c++) { next.skinIndex.setComponent(k, c, boneOf(SI[i * 4 + c])); next.skinWeight.setComponent(k, c, SW[i * 4 + c]); }
  }
  for (const [name, attr] of Object.entries(next)) g.setAttribute(name, attr);
  const old = g.index ? Array.from(g.index.array) : Array.from({ length: n0 }, (_, i) => i), total = n0 + add;
  const Idx = total > 65535 ? Uint32Array : (g.index?.array.constructor === Uint32Array ? Uint32Array : Uint16Array);
  g.setIndex(new THREE.BufferAttribute(Idx.from([...old, ...index.map((i) => i + n0)]), 1));
  g.computeBoundingBox(); g.computeBoundingSphere();
  host.boundingBox = null; host.boundingSphere = null;
  return add;
}
/** A mesh's normals in the body frame (each as drawn, or as renormalled after a move). */
function normalsOf(ly, fr) {
  const nrm = ly.mesh.geometry.attributes.normal, nm = new THREE.Matrix3().getNormalMatrix(ly.mesh.bindMatrix), v = new THREE.Vector3(), N = new Float64Array(ly.n * 3);
  for (let i = 0; i < ly.n; i++) { v.fromBufferAttribute(nrm, i).applyMatrix3(nm).normalize(); N[i * 3] = v.dot(fr.L); N[i * 3 + 1] = v.dot(fr.U); N[i * 3 + 2] = v.dot(fr.F); }
  return N;
}
/** Skin rows of vertex i of a geometry (four bone indices and weights). */
function skinRow(geo, i, SI, SW, k) {
  const si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight;
  for (let c = 0; c < 4; c++) { SI[k * 4 + c] = si ? si.getComponent(i, c) : 0; SW[k * 4 + c] = sw ? sw.getComponent(i, c) : c === 0 ? 1 : 0; }
}
/** The lapels' front faces, copied `lift` over them in the silk's mesh. */
function faceLapels(lapels, silk, fr) {
  const s = fr.scale, geo = lapels.mesh.geometry, a = geo.index.array, N = normalsOf(lapels, fr);
  const keep = [];
  for (let t = 0; t < a.length; t += 3) {
    const i0 = a[t], i1 = a[t + 1], i2 = a[t + 2];
    const e1 = [lapels.X[i1] - lapels.X[i0], lapels.Y[i1] - lapels.Y[i0], lapels.Z[i1] - lapels.Z[i0]], e2 = [lapels.X[i2] - lapels.X[i0], lapels.Y[i2] - lapels.Y[i0], lapels.Z[i2] - lapels.Z[i0]];
    const n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]], len = Math.hypot(...n);
    if (!(len > 1e-12)) continue;
    // Outward: the side the drawn normals face; the front face is the one turned toward the street.
    const dn = [0, 1, 2].reduce((acc, k) => acc + (N[a[t + k] * 3] * n[0] + N[a[t + k] * 3 + 1] * n[1] + N[a[t + k] * 3 + 2] * n[2]), 0);
    const fz = (dn < 0 ? -n[2] : n[2]) / len;
    if (fz >= FACING.minFront) keep.push(t);
  }
  if (!keep.length) return null;
  const map = new Map(), P = [], NN = [], UV = [], SI = [], SW = [], index = [];
  const uv = geo.attributes.uv;
  for (const t of keep) for (let k = 0; k < 3; k++) {
    const i = a[t + k];
    if (!map.has(i)) {
      const j = map.size; map.set(i, j);
      // Off the cloth along its own normal, turned to face forward.
      let nx = N[i * 3], ny = N[i * 3 + 1], nz = N[i * 3 + 2];
      if (nz < 0) { nx = -nx; ny = -ny; nz = -nz; }
      P.push(lapels.X[i] + nx * FACING.lift * s, lapels.Y[i] + ny * FACING.lift * s, lapels.Z[i] + nz * FACING.lift * s);
      NN.push(nx, ny, nz);
      UV.push(uv ? uv.getX(i) : 0, uv ? uv.getY(i) : 0);
      skinRow(geo, i, SI, SW, j);
    }
  }
  for (const t of keep) {
    // Wound as the front face faces: outward to the eye (the silk is double-sided either way).
    index.push(map.get(a[t]), map.get(a[t + 1]), map.get(a[t + 2]));
  }
  // The facing's own boundary turned back toward the cloth, so its edge meets the lapel's.
  const edges = new Map();
  for (let t = 0; t < index.length; t += 3) for (let k = 0; k < 3; k++) { const p = index[t + k], q = index[t + (k + 1) % 3], key = p < q ? `${p},${q}` : `${q},${p}`; edges.set(key, (edges.get(key) ?? 0) + 1); }
  const rim = new Set();
  for (const [key, c] of edges) if (c === 1) for (const v of key.split(',')) rim.add(Number(v));
  for (const j of rim) for (let c = 0; c < 3; c++) P[j * 3 + c] -= NN[j * 3 + c] * FACING.turn * s;
  smoothNormals(P, NN, index, FACING.smooth);
  // The lapel rolls out over the chest from its crease: its face turned `tilt` up toward the sky.
  for (let j = 0; j < NN.length / 3; j++) {
    const n = [NN[j * 3], NN[j * 3 + 1] + FACING.tilt, NN[j * 3 + 2]], l = Math.hypot(...n);
    for (let c = 0; c < 3; c++) NN[j * 3 + c] = n[c] / l;
  }
  return { P: Float64Array.from(P), N: Float64Array.from(NN), UV: Float32Array.from(UV), SI: Uint16Array.from(SI), SW: Float32Array.from(SW), index, faces: keep.length };
}
/**
 * The facing's normals from its own faces (area-weighted, a place's copies sharing one, turned
 * to the side the cloth's faced), then eased `passes` times toward their neighbours': silk shows
 * every facet of a low cloth's normals as a broken highlight, a pressed facing does not.
 */
function smoothNormals(P, N, index, passes) {
  const n = P.length / 3, gid = new Int32Array(n), ids = new Map();
  for (let i = 0; i < n; i++) { const k = `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`; let g = ids.get(k); if (g === undefined) ids.set(k, (g = ids.size)); gid[i] = g; }
  const G = ids.size, sum = new Float64Array(G * 3), nb = Array.from({ length: G }, () => new Set()), ref = new Float64Array(G * 3);
  for (let i = 0; i < n; i++) for (let c = 0; c < 3; c++) ref[gid[i] * 3 + c] += N[i * 3 + c];
  for (let t = 0; t < index.length; t += 3) {
    const [a, b, c] = [index[t], index[t + 1], index[t + 2]];
    const e1 = [0, 1, 2].map((k) => P[b * 3 + k] - P[a * 3 + k]), e2 = [0, 1, 2].map((k) => P[c * 3 + k] - P[a * 3 + k]);
    const f = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    const g = gid[a], sg = f[0] * ref[g * 3] + f[1] * ref[g * 3 + 1] + f[2] * ref[g * 3 + 2] < 0 ? -1 : 1;
    for (const i of [a, b, c]) { for (let k = 0; k < 3; k++) sum[gid[i] * 3 + k] += sg * f[k]; for (const j of [a, b, c]) if (gid[j] !== gid[i]) nb[gid[i]].add(gid[j]); }
  }
  const norm = (A) => { for (let g = 0; g < G; g++) { const l = Math.hypot(A[g * 3], A[g * 3 + 1], A[g * 3 + 2]); if (l > 1e-12) for (let k = 0; k < 3; k++) A[g * 3 + k] /= l; else for (let k = 0; k < 3; k++) A[g * 3 + k] = ref[g * 3 + k]; } };
  norm(sum);
  let cur = sum;
  for (let p = 0; p < passes; p++) {
    const next = new Float64Array(G * 3);
    for (let g = 0; g < G; g++) { for (let k = 0; k < 3; k++) next[g * 3 + k] = cur[g * 3 + k]; for (const h of nb[g]) for (let k = 0; k < 3; k++) next[g * 3 + k] += cur[h * 3 + k] / Math.max(1, nb[g].size); }
    norm(next); cur = next;
  }
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) N[i * 3 + k] = cur[gid[i] * 3 + k];
}
/** Two covered buttons at the back of the waist seam, over the top of the vent. */
function hipButtons(body, skirts, seam, fr) {
  const s = fr.scale, R = HIP_BUTTONS.radius * s, H = HIP_BUTTONS.dome * s, segs = HIP_BUTTONS.segments, rings = HIP_BUTTONS.rings;
  const NB = normalsOf(body, fr), P = [], N = [], UV = [], SI = [], SW = [], index = [], at = [];
  for (const side of [1, -1]) {
    const x0 = side * HIP_BUTTONS.apart * s;
    // The coat's back there: the farthest back of the body and the skirts' cloth within 1.5 cm.
    let z0 = Infinity, near = -1, nd = Infinity;
    for (const ly of [body, skirts]) for (let i = 0; i < ly.n; i++) {
      if (ly.Z[i] > 0 || Math.abs(ly.X[i] - x0) > 0.015 * s || Math.abs(ly.Y[i] - seam) > 0.015 * s) continue;
      z0 = Math.min(z0, ly.Z[i]);
    }
    for (let i = 0; i < body.n; i++) {
      if (body.Z[i] > 0) continue;
      const d = Math.hypot(body.X[i] - x0, body.Y[i] - seam, body.Z[i] - z0); if (d < nd) { nd = d; near = i; }
    }
    if (!Number.isFinite(z0) || near < 0) return null;
    // Its outward normal: the body's, averaged round the place.
    const n = [0, 0, 0];
    for (let i = 0; i < body.n; i++) if (body.Z[i] < 0 && Math.hypot(body.X[i] - x0, body.Y[i] - seam) < 0.03 * s) { const sg = NB[i * 3 + 2] > 0 ? -1 : 1; n[0] += sg * NB[i * 3]; n[1] += sg * NB[i * 3 + 1]; n[2] += sg * NB[i * 3 + 2]; }
    let ln = Math.hypot(...n); if (!(ln > 1e-6)) { n[0] = 0; n[1] = 0; n[2] = -1; ln = 1; }
    const nz = [n[0] / ln, n[1] / ln, n[2] / ln];
    // Two directions across the button: one level (across the back), one up it.
    const ux = [1, 0, 0], d1 = [ux[0] - nz[0] * nz[0], -nz[0] * nz[1], -nz[0] * nz[2]], l1 = Math.hypot(...d1);
    const a1 = d1.map((c) => c / l1), a2 = [nz[1] * a1[2] - nz[2] * a1[1], nz[2] * a1[0] - nz[0] * a1[2], nz[0] * a1[1] - nz[1] * a1[0]];
    const base = P.length / 3, c0 = [x0, seam, z0 - HIP_BUTTONS.lift * s];
    // A dome: its crown, then `rings` rings to its rim, and one more tucked under the rim.
    const ring = (rr, h, nr, nh) => { for (let k = 0; k < segs; k++) { const ph = (k / segs) * Math.PI * 2, cx = Math.cos(ph), cy = Math.sin(ph);
      for (let c = 0; c < 3; c++) { P.push(c0[c] + (a1[c] * cx + a2[c] * cy) * rr + nz[c] * h); }
      const nn = [0, 1, 2].map((c) => (a1[c] * cx + a2[c] * cy) * nr + nz[c] * nh), l = Math.hypot(...nn); N.push(nn[0] / l, nn[1] / l, nn[2] / l);
      UV.push(0.5 + 0.5 * cx * rr / R, 0.5 + 0.5 * cy * rr / R); skinRow(body.mesh.geometry, near, SI, SW, P.length / 3 - 1); } };
    for (let c = 0; c < 3; c++) P.push(c0[c] + nz[c] * H);
    N.push(...nz); UV.push(0.5, 0.5); skinRow(body.mesh.geometry, near, SI, SW, base);
    for (let r = 1; r <= rings; r++) { const t = r / rings, ang = t * Math.PI / 2 * 0.85; ring(R * Math.sin(ang) / Math.sin(Math.PI / 2 * 0.85), H * (Math.cos(ang) - Math.cos(Math.PI / 2 * 0.85)) / (1 - Math.cos(Math.PI / 2 * 0.85)), Math.sin(ang), Math.cos(ang)); }
    ring(R * 0.9, -HIP_BUTTONS.lift * s * 2, 0.6, -0.2);
    for (let k = 0; k < segs; k++) index.push(base, base + 1 + k, base + 1 + (k + 1) % segs);
    for (let r = 0; r < rings; r++) for (let k = 0; k < segs; k++) {
      const a = base + 1 + r * segs + k, b = base + 1 + r * segs + (k + 1) % segs, c = a + segs, d = b + segs;
      index.push(a, c, d, a, d, b);
    }
    at.push({ x: x0, y: seam, z: z0 });
  }
  return { P: Float64Array.from(P), N: Float64Array.from(N), UV: Float32Array.from(UV), SI: Uint16Array.from(SI), SW: Float32Array.from(SW), index, at };
}

/**
 * Cut one level's frock coat. `meshes` are that level's skinned meshes. Returns the report, or
 * null when the level has not got the pieces.
 */
export function fitFrockCoatLevel(meshes, assetId = null, lod = 0) {
  const by = {};
  for (const m of meshes) {
    const p = pieceName(m, assetId);
    for (const [k, re] of Object.entries(PIECES)) if (re.test(p) && /^garment/.test(materialName(m))) by[k] = m;
    if (materialName(m).split('__')[0] === 'skin') by.skin = m;
    if (SILK.piece.test(p) && SILK.material.test(materialName(m))) by.silk = m;
  }
  if (!by.body || !by.skirts || !by.lapels || !by.waistcoat || !by.shirt || !by.skin) return null;
  if (!by.skirts.geometry.index || !by.body.geometry.index) return null;
  const fr = frameOf(by.body.skeleton);
  if (!fr) return null;
  const L = {};
  for (const k of Object.keys(by)) if (k !== 'silk') L[k] = layerOf(by[k], fr);
  const report = {};
  report.length = shorten(L.skirts, fr);
  let seam = Infinity;
  for (let i = 0; i < L.body.n; i++) if (Math.abs(L.body.X[i]) < 0.25 * fr.scale) seam = Math.min(seam, L.body.Y[i]);
  seam = (seam + report.length.top) / 2;
  report.waist = lod > WAIST.levels ? null : suppress([[L.trousers].filter(Boolean), [L.waistcoat], [L.body, L.skirts]], L.skin, seam, fr);
  report.vent = splitVent(L.skirts, fr, report.length.top);
  report.front = openFront(L, fr);
  report.collar = standCollar(L.shirt, fr);
  for (const k of ['skirts', 'body', 'lapels', 'waistcoat', 'shirt', 'trousers']) if (L[k]) writeBack(L[k], fr);
  report.whitened = whiten(by.shirt);
  // 6, 7. In silk, appended to the silk tie's own mesh (same skeleton, its bones by name if not the same object).
  report.facing = null; report.buttons = null;
  if (by.silk && by.silk.geometry.index) {
    const same = by.silk.skeleton === by.lapels.skeleton;
    const boneOf = same ? (j) => j : (j) => Math.max(0, by.silk.skeleton.bones.findIndex((b) => b?.name === by.lapels.skeleton.bones[j]?.name));
    const face = faceLapels(L.lapels, by.silk, fr);
    if (face) report.facing = { faces: face.faces, vertices: appendInto(by.silk, fr, face, boneOf), mesh: by.silk.name };
    const btn = lod > HIP_BUTTONS.levels ? null : hipButtons(L.body, L.skirts, seam, fr);
    if (btn) report.buttons = { at: btn.at, vertices: appendInto(by.silk, fr, btn, boneOf), mesh: by.silk.name };
  }
  return report;
}

/** Every level of a loaded body, once (cloned figures share the result). */
export function fitFrockCoat(root) {
  if (!root) return null;
  if (root.userData.chicagoFrockCoat !== undefined) return root.userData.chicagoFrockCoat;
  const assetId = root.userData?.chicago4d_human?.asset_id ?? null;
  const levels = new Map();
  root.traverse((o) => {
    if (!o.isSkinnedMesh || !o.skeleton || !o.geometry?.attributes?.position) return;
    const k = lodOf(o); if (!levels.has(k)) levels.set(k, []); levels.get(k).push(o);
  });
  const report = [];
  for (const [lod, ms] of levels) { const r = fitFrockCoatLevel(ms, assetId, Number(lod) || 0); if (r) report.push({ lod, ...r }); }
  root.userData.chicagoFrockCoat = report.length ? report : null;
  return root.userData.chicagoFrockCoat;
}
