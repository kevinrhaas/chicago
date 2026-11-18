// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * saddlery.js — a riding saddle, bridle, stirrups and reins fitted to the driven current26
 * horse's own body (T-3560).
 *
 * Nothing here is a stored mesh: every strap and panel is generated from the tack spec in
 * data/transport/riding/saddle_horses.json (`tack[year]`) and the horse's own skinned surface
 * at its rest pose, so the saddle sits on THIS horse's back and the bridle on its head. Two
 * polar envelopes are read once from the skin (the body's vertices about the spine, the
 * head's about the line from poll to muzzle): for a place along the axis and an angle round it,
 * how far out the coat is. A panel is that surface lifted by its thickness; a strap is a band
 * laid on it. The saddle, girth and stirrup bars ride the `horse_body` bone and the bridle the
 * `horse_head` bone, so they move with the trunk's bob and the head's nod. The stirrup leathers
 * and the reins are redrawn each frame between their bars or bit and the rider's feet and hands
 * (or, with nobody up, hang and lie on the neck).
 *
 * Shapes and colours are reconstructed period patterns, not a particular surviving saddle
 * (liberty L-riding-tack-3560 in docs/LIBERTIES.md).
 */
import * as THREE from 'three';

const DEG = Math.PI / 180;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/**
 * A polar envelope of `points` about the line origin + s * dir: for s along it and an angle phi
 * round it (0 toward `up`, + toward `side`), the farthest point out. Bins of `ds` metres and
 * `dphi` degrees; empty bins are filled from their neighbours.
 */
export function polarEnvelope(points, { origin, dir, up, ds = .02, dphi = 10, s0, s1 }) {
  const d = dir.clone().normalize(), u = up.clone().sub(d.clone().multiplyScalar(up.dot(d))).normalize();
  const w = new THREE.Vector3().crossVectors(u, d); // + phi toward w
  const ns = Math.max(2, Math.ceil((s1 - s0) / ds) + 1), na = Math.round(360 / dphi);
  const r = new Float32Array(ns * na).fill(-1);
  const q = new THREE.Vector3();
  for (const p of points) {
    q.copy(p).sub(origin);
    const s = q.dot(d), y = q.dot(u), x = q.dot(w);
    const i = Math.round((s - s0) / ds);
    if (i < 0 || i >= ns) continue;
    const a = ((Math.round(Math.atan2(x, y) / DEG / dphi) % na) + na) % na;
    const rr = Math.hypot(x, y);
    if (rr > r[i * na + a]) r[i * na + a] = rr;
  }
  // Fill holes: round the ring first, then along the axis.
  for (let pass = 0; pass < 6; pass++) for (let i = 0; i < ns; i++) for (let a = 0; a < na; a++) {
    if (r[i * na + a] >= 0) continue;
    const n = [r[i * na + (a + 1) % na], r[i * na + (a + na - 1) % na], i > 0 ? r[(i - 1) * na + a] : -1, i < ns - 1 ? r[(i + 1) * na + a] : -1].filter(v => v >= 0);
    if (n.length) r[i * na + a] = n.reduce((x, y) => x + y, 0) / n.length;
  }
  const radius = (s, phiDeg) => {
    const fi = clamp((s - s0) / ds, 0, ns - 1), i0 = Math.floor(fi), i1 = Math.min(ns - 1, i0 + 1), ti = fi - i0;
    const fa = (((phiDeg / dphi) % na) + na) % na, a0 = Math.floor(fa), a1 = (a0 + 1) % na, ta = fa - a0;
    const g = (i, a) => Math.max(0, r[i * na + a]);
    return (g(i0, a0) * (1 - ta) + g(i0, a1) * ta) * (1 - ti) + (g(i1, a0) * (1 - ta) + g(i1, a1) * ta) * ti;
  };
  return {
    radius,
    /** The point on the coat (lifted by `lift` metres) at s along the axis and phi degrees round it. */
    at(s, phiDeg, lift = 0, target = new THREE.Vector3()) {
      const rr = radius(s, phiDeg) + lift, a = phiDeg * DEG;
      return target.copy(origin).addScaledVector(d, s).addScaledVector(u, Math.cos(a) * rr).addScaledVector(w, Math.sin(a) * rr);
    },
    dir: d, up: u, side: w,
    // The bins themselves (rider-drape.js draws them as a texture): r[i * na + a], s = s0 + i * ds.
    origin: origin.clone(), table: r, ns, na, s0, ds, dphi,
  };
}

/** A grid surface: f(i/(nu-1), j/(nv-1)) -> Vector3; two-sided by material. */
function gridGeometry(nu, nv, f) {
  const pos = [], uv = [], idx = [], v = new THREE.Vector3();
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    f(i / (nu - 1), j / (nv - 1), v); pos.push(v.x, v.y, v.z); uv.push(i / (nu - 1), j / (nv - 1));
  }
  for (let i = 0; i < nu - 1; i++) for (let j = 0; j < nv - 1; j++) {
    const a = i * nv + j, b = a + nv;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

/** A flat strap (width w) through `pts` lying on a surface whose outward normals are `normals`. */
function strapGeometry(pts, normals, w, thick = .004) {
  const n = pts.length, pos = [], idx = [];
  const t = new THREE.Vector3(), side = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    t.subVectors(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)]).normalize();
    side.crossVectors(t, normals[i]).normalize().multiplyScalar(w / 2);
    const o = normals[i].clone().multiplyScalar(thick);
    for (const [s, h] of [[-1, 0], [1, 0], [1, 1], [-1, 1]]) {
      const p = pts[i].clone().addScaledVector(side, s).addScaledVector(o, h);
      pos.push(p.x, p.y, p.z);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < 4; k++) {
    const a = i * 4 + k, b = i * 4 + (k + 1) % 4, c = a + 4, d = b + 4;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

/** A round strap or line (radius rad) through `pts`, rebuilt in place when `into` is given. */
export function tubeThrough(pts, rad, into = null, sides = 5) {
  const n = pts.length, count = n * sides;
  const g = into ?? new THREE.BufferGeometry();
  let attr = g.getAttribute('position');
  if (!attr || attr.count !== count) {
    attr = new THREE.Float32BufferAttribute(new Float32Array(count * 3), 3);
    attr.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('position', attr);
    const idx = [];
    for (let i = 0; i < n - 1; i++) for (let k = 0; k < sides; k++) {
      const a = i * sides + k, b = i * sides + (k + 1) % sides;
      idx.push(a, a + sides, b, b, a + sides, b + sides);
    }
    g.setIndex(idx);
  }
  const t = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), ref = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < n; i++) {
    t.subVectors(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)]);
    if (t.lengthSq() < 1e-12) t.set(0, 0, 1); t.normalize();
    a.crossVectors(t, Math.abs(t.y) > .9 ? ref.set(1, 0, 0) : ref.set(0, 1, 0)).normalize();
    b.crossVectors(t, a);
    for (let k = 0; k < sides; k++) {
      const th = k / sides * Math.PI * 2;
      attr.setXYZ(i * sides + k, pts[i].x + (a.x * Math.cos(th) + b.x * Math.sin(th)) * rad,
        pts[i].y + (a.y * Math.cos(th) + b.y * Math.sin(th)) * rad, pts[i].z + (a.z * Math.cos(th) + b.z * Math.sin(th)) * rad);
    }
  }
  attr.needsUpdate = true;
  g.computeVertexNormals(); g.computeBoundingSphere();
  return g;
}

/** A hanging line from a to b with `sag` metres of droop at its middle, `n` points. */
export function catenary(a, b, sag, n = 12, out = []) {
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    (out[i] ??= new THREE.Vector3()).lerpVectors(a, b, t);
    out[i].y -= sag * 4 * t * (1 - t);
  }
  out.length = n;
  return out;
}

/**
 * Kevin, 2026-11-17: the tack had "no texture". Leather and felt carry a grain: a fine pore and a
 * broader mottle in the material's own object space (the straps have no UVs), darkening and
 * lightening the colour and roughening it a little. `grain` = [fine cycles a metre, broad cycles
 * a metre, colour depth, roughness depth]; none for metal. Every face is drawn both sides, so a
 * flap or strap seen from behind is never a hole.
 */
const GRAIN = { leather: [190, 28, .2, .18], felt: [420, 22, .12, .08], rawhide: [140, 18, .26, .2] };
const GRAIN_GLSL = `
varying vec3 vTackP;
float tackHash(vec3 p) { p = fract(p * .1031); p += dot(p, p.yzx + 33.33); return fract((p.x + p.y) * p.z); }
float tackNoise(vec3 p) {
  vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(tackHash(i), tackHash(i + vec3(1, 0, 0)), f.x), mix(tackHash(i + vec3(0, 1, 0)), tackHash(i + vec3(1, 1, 0)), f.x), f.y),
    mix(mix(tackHash(i + vec3(0, 0, 1)), tackHash(i + vec3(1, 0, 1)), f.x), mix(tackHash(i + vec3(0, 1, 1)), tackHash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}`;
export function material(hex, { rough = .7, metal = 0, grain = null } = {}) {
  const m = new THREE.MeshStandardMaterial({ color: new THREE.Color(hex), roughness: rough, metalness: metal, side: THREE.DoubleSide });
  const g = grain ? GRAIN[grain] : null;
  if (!g) return m;
  const f = x => x.toFixed(4);
  m.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vTackP;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvTackP = position;');
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `#include <common>\n${GRAIN_GLSL}`)
      .replace('#include <color_fragment>', `#include <color_fragment>
  float tackG = tackNoise(vTackP * ${f(g[0])}) * .55 + tackNoise(vTackP * ${f(g[1])}) * .45;
  diffuseColor.rgb *= 1.0 + ${f(g[2])} * (tackG - .5) * 2.0;`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
  roughnessFactor = clamp(roughnessFactor + ${f(g[3])} * (tackG - .5) * 2.0, .05, 1.0);`);
  };
  m.customProgramCacheKey = () => `tack-grain|${grain}`;
  m.userData.tackGrain = grain;
  return m;
}

/**
 * Points on the coat (at the current pose, in the root's frame) of the meshes whose material is
 * `materialName`, over the triangles whose corners mostly follow `boneNames`: each triangle
 * sampled on a barycentric grid, since the vertices alone are too sparse to read a surface from.
 */
function skinnedPoints(root, materialName, boneNames, steps = 4) {
  const out = [], v = new THREE.Vector3();
  root.updateMatrixWorld(true);
  const inv = root.matrixWorld.clone().invert();
  root.traverse(m => {
    if (!m.isSkinnedMesh || m.userData.chicagoHorseLod || m.material?.name !== materialName) return;
    m.skeleton.update();
    const sk = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, n = m.geometry.attributes.position.count;
    const wanted = new Set(m.skeleton.bones.map((b, i) => boneNames.includes(b.name) ? i : -1).filter(i => i >= 0));
    const keep = new Uint8Array(n), P = new Array(n);
    for (let i = 0; i < n; i++) {
      let best = -1, bw = 0;
      for (let c = 0; c < 4; c++) if (sw.getComponent(i, c) > bw) { bw = sw.getComponent(i, c); best = sk.getComponent(i, c); }
      keep[i] = wanted.has(best) ? 1 : 0;
      P[i] = m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld).applyMatrix4(inv).clone();
    }
    const index = m.geometry.index;
    for (let t = 0; t < index.count; t += 3) {
      const a = index.getX(t), b = index.getX(t + 1), c = index.getX(t + 2);
      if (keep[a] + keep[b] + keep[c] < 2) continue;
      for (let i = 0; i <= steps; i++) for (let j = 0; j <= steps - i; j++) {
        const k = steps - i - j;
        out.push(new THREE.Vector3().addScaledVector(P[a], i / steps).addScaledVector(P[b], j / steps).addScaledVector(P[c], k / steps));
      }
    }
  });
  return out;
}

/**
 * Fit `spec` (one year's tack) to a horse `root` (a near clone at its rest pose, before any clip
 * runs). Returns { group, seat, stirrupBar(side), bit(side), update(rider), dispose() } where
 * every place is in the horse root's frame and `update` redraws the leathers and reins.
 */
export function fitTack(root, spec, { body = 'Material_HorseMain4k00.png' } = {}) {
  const bones = {}; root.traverse(n => { if (n.isBone) bones[n.name] = n; });
  for (const b of ['horse_body', 'horse_head', 'horse_neck']) if (!bones[b]) throw Error(`saddlery: the horse lacks ${b}`);
  const S = spec.saddle, B = spec.bridle;
  // The trunk's coat: the body, and the tops of the shoulders and quarters the panels lie on.
  root.updateMatrixWorld(true);
  const bodyRest = root.matrixWorld.clone().invert().multiply(bones.horse_body.matrixWorld);
  const trunk = skinnedPoints(root, body, ['horse_body', 'horse_neck', 'fore_l_shoulder', 'fore_r_shoulder', 'hind_l_hip', 'hind_r_hip']);
  const heads = skinnedPoints(root, body, ['horse_head']);
  if (trunk.length < 500 || heads.length < 200) throw Error('saddlery: too little of the horse to fit to');
  const env = polarEnvelope(trunk, { origin: new THREE.Vector3(0, S.axis_y_m, 0), dir: new THREE.Vector3(0, 0, 1), up: new THREE.Vector3(0, 1, 0), s0: -.7, s1: 1 });
  const poll = new THREE.Vector3(...B.poll_m), muzzle = new THREE.Vector3(...B.muzzle_m);
  const headLen = poll.distanceTo(muzzle);
  const hen = polarEnvelope(heads, { origin: poll, dir: muzzle.clone().sub(poll), up: new THREE.Vector3(0, 1, .4), ds: .015, s0: -.05, s1: headLen + .02 });
  const hide = S.material === 'rawhide' ? 'rawhide' : 'leather';
  const mats = {
    leather: material(S.leather_hex, { rough: .55, grain: hide }), seat: material(S.seat_hex ?? S.leather_hex, { rough: .45, grain: hide }),
    cloth: material(S.cloth_hex, { rough: .95, grain: 'felt' }), metal: material(spec.metal_hex, { rough: .35, metal: .85 }),
    bridle: material(B.leather_hex, { rough: .55, grain: 'leather' }), girth: material(S.girth_hex ?? S.leather_hex, { rough: .8, grain: 'felt' }),
  };
  // Kevin, 2026-11-17: straps "slice through the horse". A point of a hanging strap (a stirrup
  // leather, a rein) inside the trunk or the neck is laid on the coat `lift` out instead.
  const necks = skinnedPoints(root, body, ['horse_neck']);
  // The neck's core: from over the top of the chest, inside the withers, up to just under the poll.
  const withers = new THREE.Vector3(0, S.axis_y_m + .2, S.pommel_z_m + .2), pollTop = poll.clone().add(new THREE.Vector3(0, -.08, 0));
  const neckLen = withers.distanceTo(pollTop);
  const nen = necks.length > 200 ? polarEnvelope(necks, { origin: withers, dir: pollTop.clone().sub(withers), up: new THREE.Vector3(0, 1, -.3), ds: .03, s0: -.05, s1: neckLen }) : null;
  const q0 = new THREE.Vector3();
  const outside = (e, p, lift, s0, s1) => {
    if (!e) return p;
    q0.copy(p).sub(e.origin);
    const s = q0.dot(e.dir);
    if (s < s0 || s > s1) return p;
    const y = q0.dot(e.up), x = q0.dot(e.side), phi = Math.atan2(x, y) / DEG;
    if (Math.hypot(x, y) < e.radius(s, phi) + lift) e.at(s, phi, lift, p);
    return p;
  };
  // The envelopes are the rest pose's; a point as the horse now stands is taken back to its
  // bone's rest frame, laid on, and brought forward again (frames() each update).
  const neckBoneRest = root.matrixWorld.clone().invert().multiply(bones.horse_neck.matrixWorld);
  const F4 = { bodyIn: new THREE.Matrix4(), bodyOut: new THREE.Matrix4(), neckIn: new THREE.Matrix4(), neckOut: new THREE.Matrix4(), inv: new THREE.Matrix4() };
  const frames = () => {
    F4.inv.copy(root.matrixWorld).invert();
    F4.bodyOut.copy(F4.inv).multiply(bones.horse_body.matrixWorld).multiply(new THREE.Matrix4().copy(bodyRest).invert());
    F4.bodyIn.copy(F4.bodyOut).invert();
    F4.neckOut.copy(F4.inv).multiply(bones.horse_neck.matrixWorld).multiply(new THREE.Matrix4().copy(neckBoneRest).invert());
    F4.neckIn.copy(F4.neckOut).invert();
  };
  const clear = (p, lift = .012) => {
    outside(env, p.applyMatrix4(F4.bodyIn), lift, -.68, .98).applyMatrix4(F4.bodyOut);
    return outside(nen, p.applyMatrix4(F4.neckIn), lift, .02, neckLen - .03).applyMatrix4(F4.neckOut);
  };
  const neckAt = (s, phi) => nen.at(s, phi, .016).applyMatrix4(F4.neckOut);
  const group = new THREE.Group(); group.name = 'tack';
  const onBody = new THREE.Group(); onBody.name = 'tack:body';
  const onHead = new THREE.Group(); onHead.name = 'tack:head';
  const free = new THREE.Group(); free.name = 'tack:free';
  const zc = S.cantle_z_m, zp = S.pommel_z_m, len = zp - zc;
  // The cloth under it all, then the seat, its two flaps and the girth.
  const C = S.cloth;
  onBody.add(new THREE.Mesh(gridGeometry(14, 22, (u, v, out) => {
    const s = zc - C.behind_m + u * (len + C.behind_m + C.ahead_m), phi = (v * 2 - 1) * C.half_angle_deg;
    return env.at(s, phi, .01 + .004 * Math.cos(phi * DEG), out);
  }), mats.cloth));
  const seatLift = (u, phi) => {
    const a = Math.abs(phi) / S.seat_half_angle_deg;
    return S.thickness_m + S.cantle_rise_m * smooth(.2, 0, u) * (1 - .5 * a * a) + S.pommel_rise_m * smooth(.75, 1, u) * (1 - a * a)
      + .008 * (1 - a * a);
  };
  onBody.add(new THREE.Mesh(gridGeometry(18, 15, (u, v, out) => {
    const s = zc + u * len, phi = (v * 2 - 1) * S.seat_half_angle_deg;
    return env.at(s, phi, seatLift(u, phi), out);
  }), mats.seat));
  const F = S.flap;
  for (const sideSign of [1, -1]) {
    onBody.add(new THREE.Mesh(gridGeometry(10, 12, (u, v, out) => {
      // u down the flap, v front to back; the lower edge rounded.
      const z0 = zc + len * F.from, z1 = zc + len * F.to, round = 1 - .35 * u * u;
      const mid = (z0 + z1) / 2 + F.rake_m * u, s = mid + (v - .5) * (z1 - z0) * round;
      const phi = sideSign * (S.seat_half_angle_deg - 4 + u * F.drop_deg);
      return env.at(s, phi, .024 + .004 * u, out);
    }), mats.leather));
  }
  // The girth: under the belly from flap to flap, a band G.width_m wide.
  const G = S.girth;
  onBody.add(new THREE.Mesh(gridGeometry(26, 2, (u, v, out) => {
    const phi = (S.seat_half_angle_deg + F.drop_deg - 8) + u * (360 - 2 * (S.seat_half_angle_deg + F.drop_deg - 8));
    return env.at(G.z_m + (v - .5) * G.width_m, phi, .014, out);
  }), mats.girth));
  if (S.crupper) {
    // A crupper: a strap from the cantle back along the spine to under the tail.
    const pts = [], nor = [];
    for (let i = 0; i <= 12; i++) { const s = zc - i / 12 * (zc - S.crupper.to_z_m); pts.push(env.at(s, 0, .012)); nor.push(env.up.clone()); }
    onBody.add(new THREE.Mesh(strapGeometry(pts, nor, .025), mats.leather));
  }
  if (S.breastplate) {
    // A breast strap round the chest, flap to flap, laid on the coat (never through the shoulders).
    const pts = [], nor = [], o = new THREE.Vector3(0, S.axis_y_m, 0), q = new THREE.Vector3();
    for (let i = 0; i <= 16; i++) {
      const t = i / 16, phi = -70 + 140 * t;
      const p = new THREE.Vector3(Math.sin(phi * DEG) * S.breastplate.half_width_m, S.breastplate.y_m - .05 * Math.cos(phi * DEG), S.breastplate.z_m + Math.cos(phi * DEG) * .12);
      q.copy(p).sub(o);
      const sAt = q.z, round = Math.atan2(q.x, q.y) / DEG, r = Math.hypot(q.x, q.y);
      if (r < env.radius(sAt, round) + .012) env.at(sAt, round, .012, p);
      pts.push(p); nor.push(p.clone().sub(env.at(sAt, round, 0)).normalize());
    }
    onBody.add(new THREE.Mesh(strapGeometry(pts, nor, .03), mats.leather));
  }
  // Seat, bars and the near and off stirrup bars in the root frame (the rider's places).
  const seat = env.at(zc + len * S.seat_at, 0, seatLift(S.seat_at, 0));
  const bar = side => env.at(zc + len * S.bar_at, side * (S.seat_half_angle_deg + 6), .03);
  // The bridle: crownpiece and throatlatch, browband, cheekpieces, cavesson, bit.
  const hs = f => f * headLen;
  const ring = (s, a0, a1, lift = .006, n = 24) => {
    const pts = [], nor = [];
    for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n, p = hen.at(s, a, lift); pts.push(p); nor.push(p.clone().sub(hen.at(s, a, 0)).normalize()); }
    return { pts, nor };
  };
  const path = (from, to, lift = .006, n = 14) => {
    const pts = [], nor = [];
    for (let i = 0; i <= n; i++) { const t = i / n, s = from[0] + (to[0] - from[0]) * t, a = from[1] + (to[1] - from[1]) * t, p = hen.at(s, a, lift);
      pts.push(p); nor.push(p.clone().sub(hen.at(s, a, 0)).normalize()); }
    return { pts, nor };
  };
  const strap = ({ pts, nor }, w = B.strap_m) => new THREE.Mesh(strapGeometry(pts, nor, w), mats.bridle);
  onHead.add(strap(ring(hs(B.crown_at), -180, 180)));
  onHead.add(strap(ring(hs(B.brow_at), -75, 75)));
  for (const sideSign of [1, -1]) onHead.add(strap(path([hs(B.crown_at), sideSign * 95], [hs(B.bit_at), sideSign * B.bit_angle_deg])));
  if (B.cavesson_at != null) onHead.add(strap(ring(hs(B.cavesson_at), -180, 180, .008), B.strap_m * 1.2));
  if (B.second_bit) for (const sideSign of [1, -1]) onHead.add(strap(path([hs(B.crown_at) + .02, sideSign * 100], [hs(B.bit_at) - .02, sideSign * (B.bit_angle_deg - 8)], .009)));
  const bitL = hen.at(hs(B.bit_at), B.bit_angle_deg, .012), bitR = hen.at(hs(B.bit_at), -B.bit_angle_deg, .012);
  const mouth = new THREE.Mesh(new THREE.CylinderGeometry(.006, .006, 1, 8), mats.metal);
  mouth.position.lerpVectors(bitL, bitR, .5); mouth.scale.y = bitL.distanceTo(bitR);
  mouth.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), bitR.clone().sub(bitL).normalize());
  onHead.add(mouth);
  for (const p of [bitL, bitR]) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(B.bit_ring_m, .004, 6, 16), mats.metal);
    r.position.copy(p); r.rotation.y = Math.PI / 2; onHead.add(r);
  }
  // Mount each part on its bone, keeping where it was drawn (the rest pose).
  root.updateMatrixWorld(true);
  const rootInv = root.matrixWorld.clone().invert();
  const mountOn = (part, bone) => {
    part.applyMatrix4(root.matrixWorld); // drawn in root space: to world, then the bone keeps it
    bone.attach(part);
  };
  mountOn(onBody, bones.horse_body); mountOn(onHead, bones.horse_head);
  // Points that ride bones: the seat and bars on the body, the bit rings on the head.
  const riding = (bone, p) => { const local = bone.worldToLocal(p.clone().applyMatrix4(root.matrixWorld)); return () => bone.localToWorld(local.clone()).applyMatrix4(rootInv.copy(root.matrixWorld).invert()); };
  const seatAt = riding(bones.horse_body, seat), barAt = { 1: riding(bones.horse_body, bar(1)), [-1]: riding(bones.horse_body, bar(-1)) };
  const bitAt = { 1: riding(bones.horse_head, bitL), [-1]: riding(bones.horse_head, bitR) };
  const neckRest = riding(bones.horse_body, env.at(zp + .06, 0, .03));
  // Leathers, irons and reins: redrawn between their ends each frame (root frame).
  const lines = { leather: [], rein: [] };
  for (const sideSign of [1, -1]) {
    const leather = new THREE.Mesh(new THREE.BufferGeometry(), mats.leather); free.add(leather);
    const iron = spec.stirrup === 'wood'
      ? new THREE.Mesh(new THREE.BoxGeometry(.11, .05, .09), material('#5a3d26', { rough: .8 }))
      : new THREE.Mesh(new THREE.TorusGeometry(.065, .007, 6, 18, Math.PI * 1.15), mats.metal);
    if (spec.stirrup !== 'wood') { const tread = new THREE.Mesh(new THREE.BoxGeometry(.11, .008, .05), mats.metal); tread.position.y = -.0; iron.add(tread); }
    free.add(iron);
    lines.leather.push({ side: sideSign, mesh: leather, iron });
    const rein = new THREE.Mesh(new THREE.BufferGeometry(), mats.bridle); free.add(rein);
    lines.rein.push({ side: sideSign, mesh: rein });
  }
  group.add(free);
  root.add(group);
  const scratch = [];
  const api = {
    group, parts: { onBody, onHead, free }, envelope: env, head: hen, spec,
    /** The trunk bone, and where it stood in the root's frame when the tack was fitted (the envelope's pose). */
    bodyBone: bones.horse_body, bodyRest,
    /** The middle of the seat, in the horse root's frame, as the trunk now rides. */
    seat: () => seatAt(),
    stirrupBar: side => barAt[side](),
    bit: side => bitAt[side](),
    /** Where a stirrup hangs with nobody up: under its bar, a leather's length down. */
    hanging: side => barAt[side]().add(new THREE.Vector3(side * .015, -S.leather_m, 0)),
    /**
     * Redraw leathers and reins. `rider` = { feet: { 1, -1 }, hands: { 1, -1 } } in the root
     * frame (the near side is +1, the horse's left), or null for an empty saddle.
     */
    update(rider = null) {
      root.updateMatrixWorld(true);
      frames();
      for (const l of lines.leather) {
        const top = barAt[l.side](), foot = rider?.feet?.[l.side] ?? api.hanging(l.side);
        const ironAt = rider ? foot.clone().add(new THREE.Vector3(0, -.015, 0)) : clear(foot, .03);
        const end = ironAt.clone().add(new THREE.Vector3(0, .06, 0)), way = [top];
        if (!rider) clear(end, .016);
        for (let i = 1; i < 8; i++) way.push(clear(top.clone().lerp(end, i / 8), .016));
        way.push(end);
        tubeThrough(way, .006, l.mesh.geometry, 4);
        l.iron.position.copy(ironAt).add(new THREE.Vector3(0, spec.stirrup === 'wood' ? 0 : .058, 0));
        l.iron.rotation.set(0, Math.PI / 2, spec.stirrup === 'wood' ? 0 : Math.PI);
      }
      for (const r of lines.rein) {
        const from = bitAt[r.side]();
        if (!rider && nen) {
          // Nobody up: the reins lie over the neck from the bit back to the withers, on the crest.
          const way = [from];
          for (let i = 1; i <= 12; i++) {
            const t = 1 - i / 12;
            way.push(clear(neckAt(t * (neckLen - .1) + .05, r.side * 38), .016));
          }
          tubeThrough(way, .0055, r.mesh.geometry, 4);
          continue;
        }
        const to = rider?.hands?.[r.side] ?? neckRest().add(new THREE.Vector3(r.side * .05, 0, 0));
        const way = catenary(from, to, rider ? .015 : .05, 14, scratch);
        for (let i = 1; i < way.length - 1; i++) clear(way[i], .012);
        tubeThrough(way, .0055, r.mesh.geometry, 4);
      }
    },
    dispose() {
      group.removeFromParent(); onBody.removeFromParent(); onHead.removeFromParent();
      for (const g of [group, onBody, onHead]) g.traverse(o => o.geometry?.dispose());
      for (const m of Object.values(mats)) m.dispose();
    },
  };
  api.update(null);
  return api;
}
