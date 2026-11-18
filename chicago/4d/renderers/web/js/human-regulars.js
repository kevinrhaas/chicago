// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-regulars.js — the 1812 private wears the regulars' coat, not the coatee (T-3553).
 *
 * Kevin, 2026-11-17, on the catalogue review that laid the private of Heald's company beside
 * Krimmel's Philadelphia volunteers: "i think against the regulars? they are probably closer
 * to a regular and would have been outfitted with uniform?". So the private is judged against
 * what the repo's record says the U.S. regular infantry wore before the change of spring 1813,
 * not against the volunteers' facings and gaiters. The record is text, not a picture: the
 * change printed in 1813 and 1814 (us_1814_military_laws_and_regulations) says "The coat of
 * the infantry and artillery shall be uniformly blue, no red collars or cuffs: and no lace
 * shall be worn by any grade ... all the rank and file will wear coatees. The button holes of
 * these will be trimmed with tape on the collar only." Read backwards (as the figure already
 * reads it for the red collar and cuffs, the felt cap and the feather), two things the
 * figure did not have follow from it, and both are built here as inferences, not as
 * anything a source describes:
 *
 * The skirts. "All the rank and file will wear coatees" says the earlier coat was not one.
 * The export cut the private's tails to mid-thigh (0.70 m off the ground), the coatee's
 * length: what the change brought in. Here, below the hips (PIVOT_BELOW_HIP_M under the hip
 * joints, where the tails already hang straight), each tail is drawn down so its hem sits
 * HEM_ABOVE_KNEE_M above the knee joint (about 0.56 m off the ground): longer than the coatee,
 * a hand short of the officer's skirts at the bend of the knee (officer_1812.json). That the
 * coat was longer is inferred; how much longer is reconstructed, and the silhouette follows
 * Ogden's 1888 plate of the older pattern (period context, not evidence for 1812). The tails
 * keep their own cut-away taper, their rows, UVs and skin weights; only positions below the
 * pivot move, straight down, and their normals are scaled to match.
 *
 * The tape. "Trimmed with tape on the collar only" says the earlier coat's button holes were
 * trimmed with tape beyond the collar, on the breast, where a single-breasted coat's holes
 * are. The figure had none. Here a white tape loop is laid on each of the eight breast button
 * holes, from the button toward the wearer's left (the button-hole side of a man's coat).
 * Their presence is inferred; their form, length (TAPE.breast), white colour and one-sided
 * loop are reconstructed. The collar's own loops are not drawn: the exported collar falls
 * to a centimetre or less at the front, where they would sit (a leftover, not a claim). The
 * loops are strips cast onto the coat's own surface, TAPE.breast.standoff off it, under the
 * crossbelts, and skinned with the cloth they lie on. They
 * are added to the crossbelts' mesh (the same white, the same skeleton), so no draw call,
 * material, texture or program is added.
 *
 * The overalls (round 4). The record issues "two pair of woollen and two pair linen overalls"
 * and "one pair of half gaiters" (us_1812_rules_and_articles_albany, Sec. 8) and says nothing
 * of their cut. Both pictures of the set draw the legwear close to the leg (Krimmel's
 * pantaloons and gaiters, Ogden's gaiters), and overalls of the time were cut close and
 * buttoned or strapped over the shoe; the export drew them as the loose workwear shell, a
 * straight tube to the shoe, 3.6 cm off the knee and 5 cm off the ankle. So here, below the
 * fork (fading in over OVERALLS.forkFade), each leg's section is drawn in toward the leg and
 * the half gaiters inside it, to OVERALLS.ease off them (more at the knee for its bend; the hem
 * lies on the shoe), never to less than OVERALLS.minShare of its own width; beyond the rows
 * next to it the cloth runs on over a heel or knee in a cone rather than stepping out. The
 * close cut is inferred from the pictures; its amount is reconstructed. Only positions and
 * normals move, inward and level; the tails, drawn down over them, stay over them.
 *
 * Which bodies: REGULARS names the asset. Every man of the 1812 garrison wears it (the 38
 * of data/humans/instances/1812, NCOs and musicians recoloured by dress_1812_garrison.json),
 * and so does every soldier of the 1835 garrison (data/humans/inside_1835.json, recoloured
 * all blue by tools/town_people_1835.py): for them the coatee IS right, so a scene dated
 * AFTER_YEAR or later leaves the asset as exported, trousers too: no picture of the 1835
 * garrison is in the repository (no reference set, no source picture of the 1832 pattern), so
 * nothing says their legwear is wrong by its own pictures. A store with no scene (the tools' stages)
 * dresses it as the 1812 private it is named for.
 *
 * Once per parse, before any figure is cloned (60 to 120 ms at LOD0 in node with the overalls,
 * 30 to 45 at the far levels). tools/test_human_regulars.mjs
 * measures it on the real exports at every level, standing and walking. Liberty L-regulars-3553.
 */
import * as THREE from 'three';

/** The bodies dressed as the pre-1813 regulars, by asset id (the meshes' name prefix). */
export const REGULARS = Object.freeze(['private_first_infantry_1812']);
/** A scene of this year or later keeps the coatee (the change of 1813). */
export const AFTER_YEAR = 1813;
/** The tails are drawn down from this far under the hip joints, to this far above the knee joint. */
export const PIVOT_BELOW_HIP_M = 0.015, HEM_ABOVE_KNEE_M = 0.045;
/** A breast tape loop: length along the cloth from the button's centre, height, distance off it, points along it, and where it starts (under the button's rim). */
export const TAPE = Object.freeze({
  breast: Object.freeze({ length: 0.08, height: 0.014, standoff: 0.0012, points: 7, fromCentre: 0.0055 }),
});
/**
 * The overalls taken in to the leg: the cloth stands this far (metres) off the body or shoe
 * inside it at the thigh, the knee (more, for its bend), the calf and the ankle, and at the hem
 * below the ankle joint, where it lies on the shoe. Never drawn in to less than `minShare` of
 * its own section; the far levels' coarser rings stand `farEase` further off (they sag
 * between their points). The take-in fades in over `forkFade` below the fork.
 */
export const OVERALLS = Object.freeze({
  ease: Object.freeze({ thigh: 0.009, knee: 0.013, calf: 0.01, ankle: 0.009, hem: 0.005 }),
  minShare: 0.55, forkFade: 0.07, farEase: Object.freeze([0, 0, 0.004, 0.006]),
});
const DONE = Symbol('regulars');

const piece = (mesh, asset, name) => new RegExp(`^${asset}_${name}_lod\\d+$`).test(mesh.name);

/** The year a scene id names, or null. */
export function sceneYear(sceneId) {
  const m = /(1[6-9]\d\d|20\d\d)/.exec(String(sceneId ?? ''));
  return m ? Number(m[1]) : null;
}

function bindJoint(mesh, name) {
  const sk = mesh.skeleton, i = sk.bones.findIndex((b) => b?.name === name);
  return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert());
}
function bindPositions(mesh) {
  const pos = mesh.geometry.attributes.position, n = pos.count, P = new Float64Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}

/** Draw the tails down below the pivot so the hem is `hemY` (bind space). Returns metres added. */
function lengthenTails(tails, pivotY, hemY) {
  const P = bindPositions(tails), n = P.length / 3;
  let oldHem = Infinity; for (let i = 0; i < n; i++) oldHem = Math.min(oldHem, P[i * 3 + 1]);
  if (!(oldHem < pivotY) || oldHem <= hemY + 1e-4) return 0;
  const k = (pivotY - hemY) / (pivotY - oldHem);
  const pos = tails.geometry.attributes.position, nor = tails.geometry.attributes.normal;
  const inv = new THREE.Matrix4().copy(tails.bindMatrix).invert(), v = new THREE.Vector3();
  const nb = new THREE.Matrix3().getNormalMatrix(tails.bindMatrix), ni = new THREE.Matrix3().getNormalMatrix(inv), nv = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    const y = P[i * 3 + 1];
    if (y >= pivotY) continue;
    v.set(P[i * 3], pivotY - (pivotY - y) * k, P[i * 3 + 2]).applyMatrix4(inv);
    pos.setXYZ(i, v.x, v.y, v.z);
    // A stretch by k in y: normals by the inverse transpose, (nx, ny / k, nz).
    if (nor) { nv.fromBufferAttribute(nor, i).applyMatrix3(nb); nv.y /= k; nv.normalize().applyMatrix3(ni).normalize(); nor.setXYZ(i, nv.x, nv.y, nv.z); }
  }
  pos.needsUpdate = true; if (nor) nor.needsUpdate = true;
  tails.geometry.computeBoundingBox(); tails.geometry.computeBoundingSphere();
  return oldHem - hemY;
}

const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const CONE_ROWS = 4, CONE_SLOPE = 1.0;
const LEG_BONE =/^(thigh|calf|foot|ball)(_twist_\d+)?_([lr])$/;
/** Each vertex's leg ('l', 'r' or null) by its leg-bone weights (at least half). */
function legSide(mesh) {
  const names = mesh.skeleton.bones.map((b) => b?.name ?? ''), side = names.map((n) => LEG_BONE.exec(n)?.[3] ?? null);
  const si = mesh.geometry.attributes.skinIndex, sw = mesh.geometry.attributes.skinWeight, out = [];
  for (let i = 0; i < si.count; i++) {
    let l = 0, r = 0;
    for (let k = 0; k < 4; k++) { const s = side[si.getComponent(i, k)], w = sw.getComponent(i, k); if (s === 'l') l += w; else if (s === 'r') r += w; }
    out.push(l > 0.5 ? 'l' : r > 0.5 ? 'r' : null);
  }
  return out;
}

/**
 * Take the overalls in to the leg, once (bind space): each leg's section from below the fork
 * to the hem is drawn toward the leg and shoe inside it, to OVERALLS.ease off them, never to
 * less than OVERALLS.minShare of its own outline. Every layer at an angle and height (a hem's
 * turn-up inside the outline) is drawn in by the same share, so none crosses another; welded
 * copies move as one; normals are taken again from the moved faces. Returns
 * { moved: welded points moved, max: metres }.
 */
function takeInOveralls(mesh, inside, lod) {
  const at = (n) => bindJoint(mesh, n);
  const legs = {};
  for (const s of ['l', 'r']) { const H = at(`thigh_${s}`), K = at(`calf_${s}`), A = at(`foot_${s}`); if (!H || !K || !A) return null; legs[s] = { H, K, A }; }
  const O = legs.l.H.clone().add(legs.r.H).multiplyScalar(0.5);
  const U = O.clone().sub(legs.l.A.clone().add(legs.r.A).multiplyScalar(0.5)).normalize();
  const Lw = legs.l.H.clone().sub(legs.r.H); Lw.addScaledVector(U, -Lw.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(Lw, U).normalize();
  const scale = ((legs.l.H.distanceTo(legs.l.A) + legs.r.H.distanceTo(legs.r.A)) / 2) / 0.85;
  // Welded points (a UV seam's copies share a 0.05 mm cell) and triangles.
  const pos = mesh.geometry.attributes.position, n = pos.count, P = bindPositions(mesh);
  const groupOf = new Int32Array(n), first = [], keys = new Map();
  for (let i = 0; i < n; i++) {
    const k = `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`;
    let g = keys.get(k); if (g === undefined) { g = first.length; keys.set(k, g); first.push(i); }
    groupOf[i] = g;
  }
  const G = first.length, Q = first.map((i) => new THREE.Vector3().fromArray(P, i * 3)), sideV = legSide(mesh), sideG = first.map((i) => sideV[i]);
  const idx = mesh.geometry.index ? mesh.geometry.index.array : Uint32Array.from({ length: n }, (_, i) => i);
  // The fork: the lowest cloth at the middle, between the legs.
  let fork = Infinity;
  for (const q of Q) { const d = q.clone().sub(O); if (Math.abs(d.dot(Lw)) < 0.012 * scale && d.dot(U) < 0) fork = Math.min(fork, d.dot(U)); }
  if (!Number.isFinite(fork)) fork = -0.1 * scale;
  const BINS = 36, ROW = 0.01, reach = [1, 1, 2, 6][lod] ?? 6;
  const share = new Float64Array(G).fill(1), need = new Float64Array(G).fill(0), mine = new Uint8Array(G), polarG = new Array(G);
  for (const s of ['l', 'r']) {
    const { H, K, A } = legs[s];
    // The leg's axis: hip to knee to ankle, on below the ankle; h is height up it from the ankle.
    const down = A.clone().sub(K).normalize(), segs = [[A.clone().addScaledVector(down, 0.25), A], [A, K], [K, H]];
    const hK = K.distanceTo(A);
    const polar = (p) => {
      let best = null;
      for (let k = 0; k < 3; k++) {
        const [a, b] = segs[k], ab = b.clone().sub(a), len = ab.length(), ax = ab.divideScalar(len);
        const t = Math.min(len, Math.max(0, p.clone().sub(a).dot(ax))), c = a.clone().addScaledVector(ax, t), d = p.clone().sub(c), r = d.length();
        if (!best || r < best.r) {
          const u0 = F.clone().addScaledVector(ax, -F.dot(ax)).normalize(), w0 = new THREE.Vector3().crossVectors(ax, u0);
          const h = k === 0 ? t - 0.25 : k === 1 ? t : hK + t;
          best = { h, r, a: Math.atan2(d.dot(w0), d.dot(u0)), d };
        }
      }
      return best;
    };
    const binOf = (a) => ((Math.round((a / (2 * Math.PI)) * BINS) % BINS) + BINS) % BINS;
    const floor = new Map();
    for (const { P: pts, side } of inside) pts.forEach((p, i) => {
      if (side[i] !== s) return;
      const q = polar(p); if (q.r > 0.25 * scale) return;
      const k = `${binOf(q.a)},${Math.round(q.h / ROW)}`; floor.set(k, Math.max(floor.get(k) ?? 0, q.r));
    });
    // What is inside within `reach` rows, and beyond it a cone: the cloth runs on smoothly
    // over a heel or a knee rather than stepping out at it (CONE_SLOPE outward per metre).
    const floorAt = (a, h) => {
      const b = binOf(a), r = Math.round(h / ROW); let m = 0;
      for (let dr = -reach - CONE_ROWS; dr <= reach + CONE_ROWS; dr++) {
        const off = Math.max(0, Math.abs(dr) - reach) * ROW * CONE_SLOPE;
        for (let db = -2; db <= 2; db++) m = Math.max(m, (floor.get(`${(b + db + BINS) % BINS},${r + dr}`) ?? 0) - off);
      }
      return m;
    };
    const E = OVERALLS.ease, k8 = 0.08 * scale;
    const easeAt = (h) => {
      if (h < 0) return E.ankle + (E.hem - E.ankle) * smooth(-h / (0.03 * scale));
      if (h < k8) return E.ankle + (E.calf - E.ankle) * smooth(h / k8);
      if (h < hK - k8) return E.calf;
      if (h < hK) return E.calf + (E.knee - E.calf) * smooth((h - hK + k8) / k8);
      return E.knee + (E.thigh - E.knee) * smooth((h - hK) / k8);
    };
    const mineG = [];
    for (let g = 0; g < G; g++) {
      if (sideG[g] !== s) continue;
      const y = Q[g].clone().sub(O).dot(U); if (y >= fork) continue;
      const q = polar(Q[g]); if (q.r < 1e-4) continue;
      mineG.push(g); polarG[g] = { ...q, y };
    }
    const outer = new Map();
    for (const g of mineG) { const q = polarG[g], k = `${binOf(q.a)},${Math.round(q.h / ROW)}`; outer.set(k, Math.max(outer.get(k) ?? 0, q.r)); }
    const outerAt = (a, h) => { const b = binOf(a), r = Math.round(h / ROW); let m = 0; for (let db = -1; db <= 1; db++) for (let dr = -1; dr <= 1; dr++) m = Math.max(m, outer.get(`${(b + db + BINS) % BINS},${r + dr}`) ?? 0); return m; };
    for (const g of mineG) {
      const q = polarG[g], ro = Math.max(q.r, outerAt(q.a, q.h));
      const fade = smooth((fork - q.y) / (OVERALLS.forkFade * scale));
      const want = (floorAt(q.a, q.h) + (easeAt(q.h) + (OVERALLS.farEase[lod] ?? OVERALLS.farEase.at(-1))) * scale) / ro;
      need[g] = Math.min(1, want);
      share[g] = 1 - (1 - Math.min(1, Math.max(OVERALLS.minShare, want))) * fade;
      mine[g] = 1;
    }
  }
  // Smoothed over the cloth's neighbours (never tighter than its own clearance), so the
  // body's facets and the bins do not ripple it.
  const nbr = Array.from({ length: G }, () => new Set());
  for (let t = 0; t < idx.length; t += 3) { const q = [groupOf[idx[t]], groupOf[idx[t + 1]], groupOf[idx[t + 2]]]; for (let c = 0; c < 3; c++) { nbr[q[c]].add(q[(c + 1) % 3]); nbr[q[c]].add(q[(c + 2) % 3]); } }
  for (let it = 0; it < 3; it++) {
    const next = Float64Array.from(share);
    for (let g = 0; g < G; g++) { if (!mine[g] || !nbr[g].size) continue; let s = 0; for (const o of nbr[g]) s += share[o]; next[g] = Math.max(need[g], 0.5 * share[g] + 0.5 * s / nbr[g].size); }
    share.set(next);
  }
  const moved = new Uint8Array(G); let far = 0, count = 0;
  for (let g = 0; g < G; g++) {
    if (!mine[g] || share[g] >= 1 - 1e-4) continue;
    const q = polarG[g], d = q.r * (1 - share[g]);
    if (d < 2e-4) continue;
    Q[g].addScaledVector(q.d.clone().normalize(), -d); moved[g] = 1; far = Math.max(far, d); count++;
  }
  if (!count) return { moved: 0, max: 0 };
  // Back into the geometry, and the normals of the moved cloth from its faces.
  const inv = new THREE.Matrix4().copy(mesh.bindMatrix).invert(), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { const g = groupOf[i]; if (!moved[g]) continue; v.copy(Q[g]).applyMatrix4(inv); pos.setXYZ(i, v.x, v.y, v.z); }
  pos.needsUpdate = true;
  const nrm = mesh.geometry.attributes.normal;
  if (nrm) {
    const sum = Array.from({ length: G }, () => new THREE.Vector3()), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
    for (let t = 0; t < idx.length; t += 3) {
      const q = [groupOf[idx[t]], groupOf[idx[t + 1]], groupOf[idx[t + 2]]];
      if (!q.some((g) => moved[g])) continue;
      const fn = e1.subVectors(Q[q[1]], Q[q[0]]).cross(e2.subVectors(Q[q[2]], Q[q[0]]));
      for (const g of q) if (moved[g]) sum[g].add(fn);
    }
    const toBind = mesh.bindMatrix, nm = new THREE.Matrix3().getNormalMatrix(inv), old = new THREE.Vector3();
    let agree = 0;
    for (let i = 0; i < n; i++) { const g = groupOf[i]; if (moved[g]) agree += Math.sign(sum[g].dot(old.fromBufferAttribute(nrm, i).transformDirection(toBind))); }
    const sign = agree < 0 ? -1 : 1;
    for (let i = 0; i < n; i++) { const g = groupOf[i]; if (!moved[g] || sum[g].lengthSq() < 1e-20) continue; v.copy(sum[g]).multiplyScalar(sign).applyMatrix3(nm).normalize(); nrm.setXYZ(i, v.x, v.y, v.z); }
    nrm.needsUpdate = true;
  }
  mesh.geometry.computeBoundingBox(); mesh.geometry.computeBoundingSphere();
  return { moved: count, max: far };
}

/** A surface to cast onto: its bind positions and triangles. */
function surfaceOf(mesh) {
  return { mesh, P: bindPositions(mesh), idx: mesh.geometry.index ? mesh.geometry.index.array : Uint32Array.from({ length: mesh.geometry.attributes.position.count }, (_, i) => i) };
}
const ea = new THREE.Vector3(), eb = new THREE.Vector3(), pv = new THREE.Vector3(), tv = new THREE.Vector3(), qv = new THREE.Vector3();
const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
/**
 * The outermost hit of a horizontal ray from far outside at (angle, y) toward the axis
 * point (cx, y, cz): its point, the outward face normal, and the corner nearest it.
 * Angle 0 is straight ahead (+z), positive toward +x (the wearer's left).
 */
function cast(surf, cx, cz, angle, y) {
  const dir = new THREE.Vector3(-Math.sin(angle), 0, -Math.cos(angle));
  const o = new THREE.Vector3(cx, y, cz).addScaledVector(dir, -1);
  let best = null, bt = Infinity;
  const { P, idx } = surf;
  for (let t = 0; t < idx.length; t += 3) {
    const a = idx[t], b = idx[t + 1], c = idx[t + 2];
    const y0 = P[a * 3 + 1], y1 = P[b * 3 + 1], y2 = P[c * 3 + 1];
    if ((y0 > y && y1 > y && y2 > y) || (y0 < y && y1 < y && y2 < y)) continue;
    A.fromArray(P, a * 3); B.fromArray(P, b * 3); C.fromArray(P, c * 3);
    ea.subVectors(B, A); eb.subVectors(C, A); pv.crossVectors(dir, eb);
    const det = ea.dot(pv); if (Math.abs(det) < 1e-12) continue;
    const id = 1 / det; tv.subVectors(o, A);
    const u = tv.dot(pv) * id; if (u < 0 || u > 1) continue;
    qv.crossVectors(tv, ea); const w = dir.dot(qv) * id; if (w < 0 || u + w > 1) continue;
    const d = eb.dot(qv) * id; if (d <= 0 || d >= bt) continue;
    bt = d;
    const nrm = new THREE.Vector3().crossVectors(ea, eb).normalize(); if (nrm.dot(dir) > 0) nrm.negate();
    best = { point: o.clone().addScaledVector(dir, d), normal: nrm, corners: [a, b, c], bary: [1 - u - w, u, w] };
  }
  return best;
}

/** One tape loop: two rows of `points` along an arc of `length` from `angle0` toward `sign`, at height `y`. */
function tapeLoop(surf, cx, cz, y, angle0, sign, { length, height, standoff, points, fromCentre = 0 }) {
  const mid = cast(surf, cx, cz, angle0, y); if (!mid) return null;
  const r = Math.hypot(mid.point.x - cx, mid.point.z - cz); if (!(r > 0.01)) return null;
  // The loop starts under the button's rim, so the button shows at its end.
  angle0 += sign * fromCentre / r;
  const span = (length - fromCentre) / r, rows = [];
  for (const dy of [height / 2, -height / 2]) {
    const row = [];
    for (let j = 0; j < points; j++) {
      const h = cast(surf, cx, cz, angle0 + sign * span * j / (points - 1), y + dy);
      if (!h) return null;
      row.push({ p: h.point.addScaledVector(h.normal, standoff), n: h.normal, corners: h.corners, bary: h.bary });
    }
    rows.push(row);
  }
  return rows;
}

/**
 * Up to four weights normalised to one, and, for a normalised integer attribute (bytes), so
 * that their stored steps add to exactly its full scale: a vertex a step off (254 or 256 of 255)
 * is carried that much short or long by a rig that keeps each vertex's own total (human-skirt.js).
 */
export function quantWeights(ws, attr) {
  const total = ws.reduce((s, w) => s + w, 0) || 1, out = ws.map((w) => w / total);
  const max = attr?.normalized ? ({ Uint8Array: 255, Uint16Array: 65535 })[attr.array.constructor.name] : null;
  if (!max || !out.length) return out;
  const q = out.map((w) => Math.round(w * max)), diff = max - q.reduce((s, x) => s + x, 0);
  q[0] += diff;   // the largest takes the rounding
  return q.map((x) => x / max);
}

/** Append tape loops to `host` (the crossbelts), skinned as the cloth each point lies on. */
function appendLoops(host, loops) {
  const g = host.geometry, n0 = g.attributes.position.count;
  const add = loops.reduce((s, l) => s + l.rows[0].length * 2, 0);
  if (!add) return 0;
  const inv = new THREE.Matrix4().copy(host.bindMatrix).invert(), ni = new THREE.Matrix3().getNormalMatrix(inv);
  // Component by component: a loaded attribute may be interleaved (its array is the whole buffer).
  const GET = ['getX', 'getY', 'getZ', 'getW'], SET = ['setX', 'setY', 'setZ', 'setW'];
  const grow = (attr) => {
    const out = new THREE.BufferAttribute(new attr.array.constructor((n0 + add) * attr.itemSize), attr.itemSize, attr.normalized);
    for (let i = 0; i < n0; i++) for (let c = 0; c < attr.itemSize; c++) out[SET[c]](i, attr[GET[c]](i));
    return out;
  };
  const names = Object.keys(g.attributes), next = Object.fromEntries(names.map((k) => [k, grow(g.attributes[k])]));
  const sameBones = (m) => m.skeleton.bones.length === host.skeleton.bones.length && m.skeleton.bones.every((b, i) => b === host.skeleton.bones[i]);
  const boneOf = (m, j) => (sameBones(m) ? j : Math.max(0, host.skeleton.bones.findIndex((b) => b.name === m.skeleton.bones[j]?.name)));
  const tris = [], v = new THREE.Vector3();
  let k = n0;
  for (const { rows, under } of loops) {
    const ga = under.geometry.attributes, start = k, len = rows[0].length;
    for (const row of rows) for (const q of row) {
      v.copy(q.p).applyMatrix4(inv); next.position.setXYZ(k, v.x, v.y, v.z);
      if (next.normal) { v.copy(q.n).applyMatrix3(ni).normalize(); next.normal.setXYZ(k, v.x, v.y, v.z); }
      if (next.uv) next.uv.setXY(k, 0.5, 0.5);
      if (next.skinIndex && next.skinWeight && ga.skinIndex && ga.skinWeight) {
        // The cloth's weights where the point lies: its triangle's corners blended by the hit, the four largest kept.
        const sum = new Map();
        q.corners.forEach((v, t) => { for (let c = 0; c < 4; c++) { const wt = ga.skinWeight[GET[c]](v) * q.bary[t]; if (wt > 0) { const j = boneOf(under, ga.skinIndex[GET[c]](v)); sum.set(j, (sum.get(j) ?? 0) + wt); } } });
        const top = [...sum].sort((x, y) => y[1] - x[1]).slice(0, 4), qw = quantWeights(top.map((e) => e[1]), next.skinWeight);
        for (let c = 0; c < 4; c++) { next.skinIndex[SET[c]](k, top[c]?.[0] ?? 0); next.skinWeight[SET[c]](k, qw[c] ?? 0); }
      }
      k++;
    }
    // Wound to face out: compare the first quad's normal with the cloth's.
    const p = (i) => new THREE.Vector3().fromBufferAttribute(next.position, i);
    const fn = new THREE.Vector3().crossVectors(p(start + 1).sub(p(start)), p(start + len).sub(p(start)));
    const out = fn.dot(new THREE.Vector3().copy(rows[0][0].n).applyMatrix3(ni)) > 0;
    for (let j = 0; j < len - 1; j++) {
      const a = start + j, b = a + 1, c = start + len + j, d = c + 1;
      if (out) tris.push(a, b, c, b, d, c); else tris.push(a, c, b, b, c, d);
    }
  }
  for (const name of names) g.setAttribute(name, next[name]);
  if (g.index) {
    const old = g.index.array, total = n0 + add, Arr = total > 65535 ? Uint32Array : old.constructor;
    const idx = new Arr(old.length + tris.length); idx.set(old); idx.set(tris, old.length);
    g.setIndex(new THREE.BufferAttribute(idx, 1));
  }
  g.computeBoundingBox(); g.computeBoundingSphere();
  return add;
}

/** The breast's button holes: the buttons' centres, bottom to top. */
function buttonCentres(buttons) {
  const P = bindPositions(buttons), n = P.length / 3, order = Array.from({ length: n }, (_, i) => i).sort((a, b) => P[a * 3 + 1] - P[b * 3 + 1]);
  const groups = [];
  for (const i of order) {
    const g = groups.at(-1);
    if (g && P[i * 3 + 1] - g.top < 0.012) { g.sum.add(new THREE.Vector3().fromArray(P, i * 3)); g.n++; g.top = P[i * 3 + 1]; } else groups.push({ sum: new THREE.Vector3().fromArray(P, i * 3), n: 1, top: P[i * 3 + 1] });
  }
  return groups.map((g) => g.sum.divideScalar(g.n));
}

/**
 * Dress every pre-1813 regular under `root` (a parsed glTF scene) once. Returns what was done
 * ({ tails: metres added, loops }) or null when nothing applies.
 */
export function fitRegulars(root, { sceneId = null } = {}) {
  if (!root || root.userData?.[DONE]) return null;
  const year = sceneYear(sceneId);
  if (year !== null && year >= AFTER_YEAR) return null;
  const meshes = []; root.traverse((o) => o.isSkinnedMesh && meshes.push(o));
  let result = null;
  for (const asset of REGULARS) {
    const find = (name) => meshes.find((m) => piece(m, asset, name));
    const tails = find('coat_tails'), coat = find('coat_body'), buttons = find('coat_buttons'), belts = find('crossbelts');
    const overalls = find('linen_overalls'), body = find('body_0'), shoes = find('closed_shoes');
    if (!tails || !coat || !belts) continue;
    root.userData[DONE] = true;
    const thighs = ['thigh_l', 'thigh_r'].map((b) => bindJoint(tails, b)), knees = ['calf_l', 'calf_r'].map((b) => bindJoint(tails, b));
    if (thighs.some((j) => !j) || knees.some((j) => !j)) continue;
    const hip = (thighs[0].y + thighs[1].y) / 2, knee = (knees[0].y + knees[1].y) / 2;
    const added = lengthenTails(tails, hip - PIVOT_BELOW_HIP_M, knee + HEM_ABOVE_KNEE_M);
    // The overalls to the leg, round the body and shoes inside them.
    const lod = Number(/_lod(\d+)$/.exec(tails.name)?.[1] ?? 0);
    const inside = [body, shoes].filter(Boolean).map((m) => { const B = bindPositions(m); return { P: Array.from({ length: B.length / 3 }, (_, i) => new THREE.Vector3().fromArray(B, i * 3)), side: legSide(m) }; });
    const fit = overalls && body ? takeInOveralls(overalls, inside, lod) : null;

    const loops = [];
    // The breast: one loop a button, toward +x (the wearer's left), about the body's own axis.
    const coatSurf = surfaceOf(coat), spine = ['spine_02', 'spine_03'].map((b) => bindJoint(coat, b)).filter(Boolean);
    const cz = spine.length ? spine.reduce((s, j) => s + j.z, 0) / spine.length : 0;
    if (buttons) for (const b of buttonCentres(buttons)) {
      const rows = tapeLoop(coatSurf, 0, cz, b.y, Math.atan2(b.x, b.z - cz), 1, TAPE.breast);
      if (rows) loops.push({ rows, under: coat });
    }
    appendLoops(belts, loops);
    result = { tails: added, loops: loops.length, overalls: fit };
  }
  return result;
}
