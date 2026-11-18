// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * rider-drape.js — a rider's hanging cloth lies on the horse instead of going through it.
 *
 * Kevin, 2026-11-17: "People in long coats or blankets should be able to ride horses". The
 * figures are rigged to stand and walk: a frock coat's or a greatcoat's skirts, an officer's
 * tails, a capote, a blanket or a breechcloth hang from the waist, and astride they hang
 * straight down through the saddle and the horse's back (17 to 19 cm deep, T-3560). Real cloth
 * falls ON the horse: a coat's skirts lie over the cantle and the croup and down the flanks, a
 * breechcloth's flaps over the pommel and behind the seat.
 *
 * How. The horse's trunk is already measured as a polar envelope about its spine (saddlery.js
 * `polarEnvelope`, the one the saddle is fitted to). Each frame the rider's hanging cloth, after
 * the figure is skinned, is carried into the trunk's rest frame (where the envelope is). A point
 * of it that is inside the trunk, or that hangs under the barrel within its width, is laid on
 * the coat MARGIN_M out: a point in the upper part goes straight out from the spine to the
 * coat; a point below CLAMP_DEG round from the top (under the barrel) goes to the flank at
 * CLAMP_DEG, its own side. Over the saddle's seat (within the seat's half angle, the leather the
 * rider sits on) nothing moves: the rider's seat is the saddle's. Points outside the trunk and
 * clear of the barrel's width keep their place: the cloth beside the rider's legs hangs as it
 * hangs.
 *
 * Where. On the GPU, in the vertex shader of the rider's own copies of their garments'
 * materials (no other figure of the asset is touched), after skinning: the envelope is a small
 * texture (one texel a bin), the frame two matrices a mesh. `drapePoint` is the same rule on
 * the CPU, for the tests (tools/test_riding.mjs seats every rider and checks the cloth stays
 * out of the horse at every pace). Which cloth: every garment that is not a tube on a leg
 * (trousers, breeches, leggings, stockings, boots stay on the leg: a leg in the horse is a
 * fault of the seat, never hidden) and not skin or shoe.
 *
 * The leg on the saddle. Kevin's screenshot, 2026-11-17: a rider's thigh went through the saddle
 * cloth. A leg is never draped, but where it lies against the saddle (over the cloth and the
 * flaps, off the seat) a point of it a little inside the tack's outside (no deeper than
 * PRESS_DEPTH_M into the coat: deeper is a fault of the seat, left to be seen and to fail the
 * test) is pressed out onto it, as a leg is flattened against a saddle flap. `pressPoint` is its
 * CPU twin.
 *
 * Reconstructed: how a given coat lay on a given horse is not recorded; the rule is the
 * simplest that keeps cloth on the coat (liberty L-rider-drape-3560).
 */
import * as THREE from 'three';

const DEG = Math.PI / 180;
export const MARGIN_M = 0.014;  // the cloth lies this far off the coat
export const CLAMP_DEG = 105;   // below this far round from the top: laid on the flank here
const SCALE_M = 0.8;            // the texture's byte 255 is this radius
export const PRESS_DEPTH_M = 0.04;  // a leg point deeper in the coat than this is not pressed out
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

/**
 * Where the tack lies that a leg is pressed onto: from the cloth's back to its front (`s0`,
 * `s1`, envelope metres), off the seat (`seatHalfDeg`) down to the cloth's edge (`maxDeg`), its
 * outside `lift` metres off the coat. From a saddle spec (saddle_horses.json `tack.*.saddle`).
 */
export function pressZone(S) {
  const C = S.cloth ?? { behind_m: 0, ahead_m: 0, half_angle_deg: S.seat_half_angle_deg + (S.flap?.drop_deg ?? 40) };
  const flapEnd = S.flap ? S.seat_half_angle_deg - 4 + S.flap.drop_deg : 0;
  return { s0: S.cantle_z_m - C.behind_m, s1: S.pommel_z_m + C.ahead_m, seatHalfDeg: S.seat_half_angle_deg,
    maxDeg: Math.max(C.half_angle_deg, flapEnd), lift: S.flap ? .034 : .02 };
}
/** How far out a leg is pressed at (s, |phi|): the zone's lift, eased in at its edges. */
export function pressLift(z, s, a) {
  return z.lift * smooth(z.seatHalfDeg - 10, z.seatHalfDeg + 4, a) * smooth(z.maxDeg + 4, z.maxDeg - 10, a)
    * smooth(z.s0 - .02, z.s0 + .04, s) * smooth(z.s1 + .02, z.s1 - .04, s);
}

const materialName = (m) => (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? '';

/**
 * Whether a rider's skinned mesh drapes: not skin, not footwear, not a tube on a leg. `kind` is
 * human-skirt.js `garmentKind(mesh).kind` when known ('tube' never drapes).
 */
export function drapes(mesh, kind = null) {
  if (!mesh?.isSkinnedMesh) return false;
  const name = materialName(mesh);
  if (name.split('__')[0] === 'skin' || /^footwear/.test(name)) return false;
  return kind !== 'tube';
}

/**
 * The rule, on the CPU. `q` is a point in the trunk's rest frame less the envelope's origin
 * (x toward `env.side`, y toward `env.up`, z along `env.dir`); moved in place. Returns whether
 * it moved. `seatHalfDeg` is the saddle's seat half angle.
 */
export function drapePoint(q, env, { seatHalfDeg = 45, s0 = -0.7, s1 = 1, margin = MARGIN_M, clampDeg = CLAMP_DEG } = {}) {
  const x = q.dot(env.side), y = q.dot(env.up), s = q.dot(env.dir);
  if (s <= s0 + 0.02 || s >= s1 - 0.02) return false;
  const phi = Math.atan2(x, y) / DEG, a = Math.abs(phi), r = Math.hypot(x, y);
  if (a < seatHalfDeg && y > 0) return false;
  const sgn = x < 0 ? -1 : 1;
  const inside = r < env.radius(s, phi) + margin;
  const width = env.radius(s, sgn * clampDeg) * Math.sin(clampDeg * DEG);
  const under = a > clampDeg && Math.abs(x) < width + margin;
  if (!inside && !under) return false;
  const p2 = sgn * Math.min(a, clampDeg), r2 = env.radius(s, p2) + margin;
  const nx = Math.sin(p2 * DEG) * r2, ny = Math.cos(p2 * DEG) * r2;
  q.copy(env.dir).multiplyScalar(s).addScaledVector(env.up, ny).addScaledVector(env.side, nx);
  return true;
}

/**
 * The press on the CPU: `q` as in drapePoint; a leg point under the tack's outside (and not
 * deeper than PRESS_DEPTH_M in the coat) goes straight out onto it. Returns whether it moved.
 */
export function pressPoint(q, env, zone) {
  const x = q.dot(env.side), y = q.dot(env.up), s = q.dot(env.dir);
  const phi = Math.atan2(x, y) / DEG, a = Math.abs(phi), r = Math.hypot(x, y);
  const lift = pressLift(zone, s, a);
  if (!(lift > 1e-4)) return false;
  const R = env.radius(s, phi);
  if (!(r < R + lift && r > R - PRESS_DEPTH_M && r > 1e-4)) return false;
  const k = (R + lift) / r;
  q.copy(env.dir).multiplyScalar(s).addScaledVector(env.up, y * k).addScaledVector(env.side, x * k);
  return true;
}

// ---- T-3644: a side saddle's habit -------------------------------------------------------------
//
// Kevin's card, 2026-11-17: "Astride in 1812, sidesaddle later". Aside, both legs are on the near
// side, the right thigh forward over the fixed head; a standing figure's skirt, skinned to the
// thighs, goes up with them and leaves the legs bare. A woman riding aside wore a long skirt that
// fell over both knees and down the near side to below her foot, and on the off side over the
// saddle. So, on a side saddle, a figure's hanging cloth (its skirt, its apron: garmentKind
// 'hang' and what rides on it) is laid on a sheet that covers the legs: round the rider (HABIT.cols
// ways from the front, toward her left), from her hips over whatever of her legs is that way, as
// a cloth drawn over them (the upper outline of the legs, seen in that way's upright half-plane,
// widened by HABIT.margin_m) and then straight down to HABIT.below_foot_m under her lower foot. A
// vertex of the cloth goes to the sheet by where it was on the standing figure: its way round
// her body, and its depth under her hips over the longest hanging garment's (so a shorter apron
// stays a shorter apron, HABIT.lift_m outside the skirt). Over its first HABIT.blend of that depth
// it is eased in from where the figure's own skin puts it, so the waist is the figure's. After
// that the drape's own rule lays whatever is in the horse (the off side, the back) on its coat.
// The legs, skin and stockings stay as posed: under the sheet. `habitSheet` is the sheet, on the
// CPU (the tests use the same), the vertex shader reads it from a small float texture.
// Reconstructed: how a habit lay is drawn from the general shape, not from a record
// (liberty L-sidesaddle-3644).
export const HABIT = Object.freeze({ cols: 32, rows: 16, margin_m: 0.035, waist_m: 0.17, below_foot_m: 0.1, lift_m: 0.012, blend: 0.14 });
const HABIT_KINDS = new Set(['hang', 'ride']);
/** Whether a rider's mesh is laid on the habit (its hanging cloth, and what rides on that). */
export const habitCloth = (mesh, kind) => !!mesh?.isSkinnedMesh && HABIT_KINDS.has(kind) && drapes(mesh, kind);

/**
 * A garment's standing frame: bind-space position -> metres from the figure's hips, x to her
 * left, y up, z ahead. Returns { matrix, below } (`below`: how far its lowest point hangs under
 * the hips), or null on a mesh without the legs' bones.
 */
export function habitRest(mesh) {
  const sk = mesh?.skeleton;
  if (!sk) return null;
  const at = (n) => { const i = sk.bones.findIndex((b) => b?.name === n); return i < 0 ? null : new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert()); };
  const tl = at('thigh_l'), tr = at('thigh_r'), fl = at('foot_l'), fr = at('foot_r'), bl = at('ball_l');
  if (!tl || !tr || !fl || !fr) return null;
  const O = tl.clone().add(tr).multiplyScalar(0.5);
  const up = O.clone().sub(fl.clone().add(fr).multiplyScalar(0.5)).normalize();
  const fwd = bl ? bl.clone().sub(fl) : new THREE.Vector3(0, 0, 1);
  fwd.addScaledVector(up, -fwd.dot(up)).normalize();
  const left = new THREE.Vector3().crossVectors(up, fwd).normalize();
  const matrix = new THREE.Matrix4().makeBasis(left, up, fwd).transpose()
    .multiply(new THREE.Matrix4().makeTranslation(-O.x, -O.y, -O.z)).multiply(mesh.bindMatrix);
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3();
  let below = 0;
  for (let i = 0; i < pos.count; i++) below = Math.max(below, -v.fromBufferAttribute(pos, i).applyMatrix4(matrix).y);
  return { matrix, below };
}

/**
 * The legs as balls along their bones, in the envelope's frame (`toEnv`: world -> that frame):
 * [{ p, r }]. `bones` = rider-pose.js `bones`.
 */
export function legBalls(bones, toEnv) {
  const out = [], a = new THREE.Vector3(), b = new THREE.Vector3();
  const segs = [['thigh', 'calf', 0.085, 0.06, 8], ['calf', 'foot', 0.058, 0.045, 7], ['foot', 'ball', 0.045, 0.04, 2]];
  for (const s of ['l', 'r']) for (const [x, y, r0, r1, n] of segs) {
    const A = bones[`${x}_${s}`], B = bones[`${y}_${s}`];
    if (!A || !B) continue;
    A.getWorldPosition(a).applyMatrix4(toEnv); B.getWorldPosition(b).applyMatrix4(toEnv);
    if (y === 'ball') b.sub(a).multiplyScalar(1.6).add(a); // on to the toe
    for (let i = 0; i <= n; i++) { const t = i / n; out.push({ p: a.clone().lerp(b, t), r: r0 + (r1 - r0) * t }); }
  }
  return out;
}

/**
 * The habit's sheet from the legs (`balls`, legBalls) about her hips (`hips`, envelope frame):
 * HABIT.cols ways round (way j at j / cols of a turn from ahead toward her left, the near side),
 * HABIT.rows points each from the hips down to the hem. Into `out` (cols x rows x 2 RGBA floats:
 * the points, then their outward normals). Returns `out`.
 */
export function habitSheet(balls, hips, H = HABIT, out = new Float32Array(H.cols * H.rows * 2 * 4)) {
  const { cols, rows, margin_m: margin, waist_m: waist } = H;
  let low = Infinity;
  for (const b of balls) low = Math.min(low, b.p.y - b.r);
  const yHem = Math.min(hips.y - 0.3, low - H.below_foot_m);
  const slack = Math.PI / cols;
  for (let j = 0; j < cols; j++) {
    const th = (j / cols) * Math.PI * 2, sx = Math.sin(th), sz = Math.cos(th);
    const pts = [];
    let yStart = hips.y;
    for (const { p, r } of balls) {
      const dx = p.x - hips.x, dz = p.z - hips.z, d = Math.hypot(dx, dz);
      let D = Math.abs(Math.atan2(dx, dz) - th) % (Math.PI * 2); if (D > Math.PI) D = Math.PI * 2 - D;
      const sub = d > r ? Math.asin(r / d) : Math.PI / 2;
      if (D > sub + slack) continue;
      const rho = d * Math.cos(Math.min(D, Math.PI / 2)), rr = r + margin;
      for (let k = 0; k < 8; k++) {
        const a = (k / 8) * Math.PI * 2, q = [rho + rr * Math.cos(a), p.y + rr * Math.sin(a)];
        if (q[0] <= waist) yStart = Math.max(yStart, q[1]); else pts.push(q);
      }
    }
    // The upper outline from the hips out (a cloth drawn over the legs), then straight down.
    pts.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
    const hull = [[waist, yStart]];
    const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    for (const q of pts) {
      while (hull.length >= 2 && cross(hull[hull.length - 2], hull[hull.length - 1], q) >= 0) hull.pop();
      hull.push(q);
    }
    const last = hull[hull.length - 1];
    hull.push([last[0], Math.min(yHem, last[1] - 0.02)]);
    // Resampled by length into the rows.
    const len = [0];
    for (let i = 1; i < hull.length; i++) len.push(len[i - 1] + Math.hypot(hull[i][0] - hull[i - 1][0], hull[i][1] - hull[i - 1][1]));
    const total = len[len.length - 1] || 1;
    let k = 0;
    for (let i = 0; i < rows; i++) {
      const want = (i / (rows - 1)) * total;
      while (k < hull.length - 2 && len[k + 1] < want) k++;
      const seg = Math.max(1e-9, len[k + 1] - len[k]), f = Math.min(1, Math.max(0, (want - len[k]) / seg));
      const rho = hull[k][0] + (hull[k + 1][0] - hull[k][0]) * f, y = hull[k][1] + (hull[k + 1][1] - hull[k][1]) * f;
      const tr = hull[k + 1][0] - hull[k][0], ty = hull[k + 1][1] - hull[k][1], tl = Math.hypot(tr, ty) || 1;
      const nr = -ty / tl, ny = tr / tl; // the outward side of the outline
      const o = (i * cols + j) * 4, n = ((rows + i) * cols + j) * 4;
      out[o] = hips.x + sx * rho; out[o + 1] = y; out[o + 2] = hips.z + sz * rho; out[o + 3] = 1;
      out[n] = sx * nr; out[n + 1] = ny; out[n + 2] = sz * nr; out[n + 3] = 0;
    }
  }
  return out;
}

/** A point of the sheet (as the shader reads it): way `u` (0..1, wrapping), depth `t` (0..1). */
export function habitPoint(sheet, u, t, H = HABIT, out = new THREE.Vector3(), normal = null) {
  const { cols, rows } = H;
  const x = (((u % 1) + 1) % 1) * cols, y = Math.min(1, Math.max(0, t)) * (rows - 1);
  const i0 = Math.floor(x) % cols, i1 = (i0 + 1) % cols, fx = x - Math.floor(x);
  const j0 = Math.min(rows - 1, Math.floor(y)), j1 = Math.min(rows - 1, j0 + 1), fy = y - j0;
  const at = (i, j, c, base = 0) => sheet[((base + j) * cols + i) * 4 + c];
  const mix = (c, base) => (at(i0, j0, c, base) * (1 - fx) + at(i1, j0, c, base) * fx) * (1 - fy) + (at(i0, j1, c, base) * (1 - fx) + at(i1, j1, c, base) * fx) * fy;
  out.set(mix(0, 0), mix(1, 0), mix(2, 0));
  normal?.set(mix(0, rows), mix(1, rows), mix(2, rows));
  return out;
}

/**
 * A garment vertex on the habit (the CPU twin of the shader): `rest` its standing place
 * (habitRest's frame), `now` where the skin puts it (envelope frame), `L` the longest hanging
 * cloth's depth, `lift` its layer's. Moved in place; returns whether it moved.
 */
export function habitVertex(sheet, rest, now, L, lift = 0, H = HABIT) {
  const t = -rest.y / L;
  if (!(t > 0)) return false;
  const u = Math.atan2(rest.x, rest.z) / (Math.PI * 2) + 1;
  const n = new THREE.Vector3(), p = habitPoint(sheet, u, t, H, new THREE.Vector3(), n);
  p.addScaledVector(n.normalize(), lift);
  const w = smooth(0, H.blend, t);
  now.lerp(p, w);
  return true;
}

/** The envelope as a texture: phi across (wrapping), s down; a byte a bin, SCALE_M at 255. */
function envelopeTexture(env) {
  const { table, ns, na } = env;
  const data = new Uint8Array(ns * na);
  for (let i = 0; i < ns * na; i++) data[i] = Math.max(0, Math.min(255, Math.round(Math.max(0, table[i]) / SCALE_M * 255)));
  const tex = new THREE.DataTexture(data, na, ns, THREE.RedFormat, THREE.UnsignedByteType);
  tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.magFilter = tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
  tex.needsUpdate = true;
  return tex;
}

const GLSL_HEAD = /* glsl */`
uniform mat4 drapeIn;
uniform mat4 drapeOut;
uniform sampler2D drapeR;
uniform vec4 drapeK; // s0, ds, ns, na
uniform vec4 drapeP; // scale, margin, seat half angle, clamp angle (radians)
uniform vec4 drapeZ; // a leg's press: s0, s1, the cloth's edge (radians), lift (0: a cloth's drape)
float drapeSmooth(float a, float b, float x) { return smoothstep(0.0, 1.0, (x - a) / (b - a)); }
float drapeRad(float s, float phi) {
  float u = phi / 6.28318530718 + 0.5 / drapeK.w;
  float v = ((s - drapeK.x) / drapeK.y + 0.5) / drapeK.z;
  return texture2D(drapeR, vec2(u, v)).r * drapeP.x;
}
`;
const GLSL_HABIT_HEAD = /* glsl */`
uniform mat4 habitRest;
uniform vec4 habitK; // the longest hanging cloth's depth, this cloth's lift, cols, rows
uniform vec2 habitB; // the blend's depth
uniform sampler2D habitG;
vec3 habitTex(int i, int j) { return texelFetch(habitG, ivec2(i, j), 0).xyz; }
`;
const GLSL_HABIT = /* glsl */`
{
  vec3 hr = (habitRest * vec4(position, 1.0)).xyz;
  float ht = -hr.y / habitK.x;
  if (ht > 0.0) {
    int nc = int(habitK.z), nr = int(habitK.w);
    float hx = fract(atan(hr.x, hr.z) / 6.28318530718 + 1.0) * habitK.z, hy = clamp(ht, 0.0, 1.0) * (habitK.w - 1.0);
    int i0 = int(floor(hx)) % nc, i1 = (i0 + 1) % nc, j0 = min(nr - 1, int(floor(hy))), j1 = min(nr - 1, j0 + 1);
    float fx = hx - floor(hx), fy = hy - float(j0);
    vec3 hp = mix(mix(habitTex(i0, j0), habitTex(i1, j0), fx), mix(habitTex(i0, j1), habitTex(i1, j1), fx), fy);
    vec3 hn = mix(mix(habitTex(i0, j0 + nr), habitTex(i1, j0 + nr), fx), mix(habitTex(i0, j1 + nr), habitTex(i1, j1 + nr), fx), fy);
    hp += normalize(hn + vec3(0.0, 1e-6, 0.0)) * habitK.y;
    vec3 dq = (drapeIn * vec4(transformed, 1.0)).xyz;
    dq = mix(dq, hp, drapeSmooth(0.0, habitB.x, ht));
    transformed = (drapeOut * vec4(dq, 1.0)).xyz;
  }
}
`;
const GLSL_PRESS = /* glsl */`
{
  vec3 dq = (drapeIn * vec4(transformed, 1.0)).xyz;
  float a = abs(atan(dq.x, dq.y));
  float d10 = 0.174533, d4 = 0.069813;
  float lift = drapeZ.w * drapeSmooth(drapeP.z - d10, drapeP.z + d4, a) * drapeSmooth(drapeZ.z + d4, drapeZ.z - d10, a)
    * drapeSmooth(drapeZ.x - 0.02, drapeZ.x + 0.04, dq.z) * drapeSmooth(drapeZ.y + 0.02, drapeZ.y - 0.04, dq.z);
  if (lift > 0.0001) {
    float phi = atan(dq.x, dq.y);
    float R = drapeRad(dq.z, phi < 0.0 ? phi + 6.28318530718 : phi);
    float r = length(dq.xy);
    if (r < R + lift && r > R - ${PRESS_DEPTH_M.toFixed(4)} && r > 0.0001) {
      dq.xy *= (R + lift) / r;
      transformed = (drapeOut * vec4(dq, 1.0)).xyz;
    }
  }
}
`;
const GLSL_BODY = /* glsl */`
{
  vec3 dq = (drapeIn * vec4(transformed, 1.0)).xyz;
  float sEnd = drapeK.x + drapeK.y * (drapeK.z - 1.0);
  if (dq.z > drapeK.x + drapeK.y && dq.z < sEnd - drapeK.y) {
    float phi = atan(dq.x, dq.y);
    float a = abs(phi);
    if (!(a < drapeP.z && dq.y > 0.0)) {
      float sgn = dq.x < 0.0 ? -1.0 : 1.0;
      float r = length(dq.xy);
      bool inside = r < drapeRad(dq.z, phi < 0.0 ? phi + 6.28318530718 : phi) + drapeP.y;
      float cl = drapeP.w;
      float width = drapeRad(dq.z, sgn > 0.0 ? cl : 6.28318530718 - cl) * sin(cl);
      bool under = a > cl && abs(dq.x) < width + drapeP.y;
      if (inside || under) {
        float p2 = sgn * min(a, cl);
        float r2 = drapeRad(dq.z, p2 < 0.0 ? p2 + 6.28318530718 : p2) + drapeP.y;
        dq.xy = vec2(sin(p2), cos(p2)) * r2;
        transformed = (drapeOut * vec4(dq, 1.0)).xyz;
      }
    }
  }
}
`;

/**
 * Drape a seated rider's cloth over a fitted horse. `meshes`: the rider's skinned meshes;
 * `kindOf(mesh)` the garment kind (optional); `tack`: saddlery.js fitTack's api (its
 * `envelope`, `bodyBone`, `bodyRest`); `seatHalfDeg`. Returns { update(), dispose() }:
 * call update() each frame after the horse and the rider are posed and their matrices updated.
 */
export function drapeRider({ meshes, kindOf = null, tack, seatHalfDeg = 45, press = null, habit = null }) {
  const env = tack?.envelope, body = tack?.bodyBone;
  if (!env?.table || !body || !tack.bodyRest) return null;
  const tex = envelopeTexture(env);
  const K = new THREE.Vector4(env.s0, env.ds, env.ns, env.na);
  const P = new THREE.Vector4(SCALE_M, MARGIN_M, seatHalfDeg * DEG, CLAMP_DEG * DEG);
  // `press` (pressZone): the legs, skin and boots that lie on the saddle are pressed onto it.
  const Z = press ? new THREE.Vector4(press.s0, press.s1, press.maxDeg * DEG, press.lift) : null;
  // Root frame -> envelope frame (origin off, axes onto x side, y up, z along).
  const basis = new THREE.Matrix4().makeBasis(env.side, env.up, env.dir).transpose();
  const toEnv = basis.multiply(new THREE.Matrix4().makeTranslation(-env.origin.x, -env.origin.y, -env.origin.z));
  // T-3644: `habit` = { bones } (rider-pose.js) on a side saddle: the hanging cloth on the sheet.
  const habitOf = new Map();
  if (habit?.bones) {
    for (const mesh of meshes) {
      const kind = kindOf?.(mesh) ?? null;
      if (!habitCloth(mesh, kind)) continue;
      const rest = habitRest(mesh);
      if (rest) habitOf.set(mesh, { rest, layer: /garment_outer|apron/.test(materialName(mesh)) || kind === 'ride' ? 1 : 0 });
    }
  }
  const habitL = Math.max(0.3, ...[...habitOf.values()].map((h) => h.rest.below));
  const sheet = habitOf.size ? new Float32Array(HABIT.cols * HABIT.rows * 2 * 4) : null;
  const sheetTex = sheet ? new THREE.DataTexture(sheet, HABIT.cols, HABIT.rows * 2, THREE.RGBAFormat, THREE.FloatType) : null;
  if (sheetTex) { sheetTex.magFilter = sheetTex.minFilter = THREE.NearestFilter; sheetTex.generateMipmaps = false; }
  const items = [];
  for (const mesh of meshes) {
    const draped = drapes(mesh, kindOf?.(mesh) ?? null);
    if (!draped && !(Z && mesh?.isSkinnedMesh)) continue;
    const H = habitOf.get(mesh);
    const body = draped ? (H ? GLSL_HABIT + GLSL_BODY : GLSL_BODY) : GLSL_PRESS;
    const habitU = H ? { habitRest: { value: H.rest.matrix }, habitK: { value: new THREE.Vector4(habitL, H.layer * HABIT.lift_m, HABIT.cols, HABIT.rows) },
      habitB: { value: new THREE.Vector2(HABIT.blend, 0) }, habitG: { value: sheetTex } } : null;
    const uIn = { value: new THREE.Matrix4() }, uOut = { value: new THREE.Matrix4() };
    const was = mesh.material;
    const list = (Array.isArray(was) ? was : [was]).map((m) => {
      const c = m.clone();
      c.onBeforeCompile = (shader, renderer) => {
        m.onBeforeCompile?.call(c, shader, renderer);
        Object.assign(shader.uniforms, { drapeIn: uIn, drapeOut: uOut, drapeR: { value: tex }, drapeK: { value: K }, drapeP: { value: P },
          drapeZ: { value: Z ?? new THREE.Vector4() } }, habitU ?? {});
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', `#include <common>\n${GLSL_HEAD}${habitU ? GLSL_HABIT_HEAD : ''}`)
          .replace('#include <skinning_vertex>', `#include <skinning_vertex>\n${body}`);
      };
      const key = m.customProgramCacheKey?.bind(m);
      c.customProgramCacheKey = () => `${key ? key() : ''}|rider-${draped ? (H ? 'habit' : 'drape') : 'press'}`;
      return c;
    });
    mesh.material = Array.isArray(was) ? list : list[0];
    items.push({ mesh, was, list, uIn, uOut });
  }
  if (!items.length) { tex.dispose(); sheetTex?.dispose(); return null; }
  const restNow = new THREE.Matrix4(), M = new THREE.Matrix4();
  const hips = new THREE.Vector3(), hipR = new THREE.Vector3();
  return {
    meshes: items.map((i) => i.mesh),
    /** The habit's sheet as last laid (envelope frame), or null off a side saddle. */
    get sheet() { return sheet; },
    update() {
      // world -> the trunk's rest pose in the root frame -> the envelope's frame
      restNow.copy(tack.bodyRest).multiply(M.copy(body.matrixWorld).invert()).premultiply(toEnv);
      for (const it of items) {
        it.uIn.value.copy(restNow).multiply(it.mesh.matrixWorld);
        it.uOut.value.copy(it.uIn.value).invert();
      }
      if (sheet) {
        const B = habit.bones;
        B.thigh_l.getWorldPosition(hips).applyMatrix4(restNow);
        B.thigh_r.getWorldPosition(hipR).applyMatrix4(restNow);
        habitSheet(legBalls(B, restNow), hips.add(hipR).multiplyScalar(0.5), HABIT, sheet);
        sheetTex.needsUpdate = true;
      }
    },
    dispose() {
      for (const it of items) {
        if (it.mesh.material === (Array.isArray(it.was) ? it.list : it.list[0])) it.mesh.material = it.was;
        for (const c of it.list) c.dispose();
      }
      tex.dispose(); sheetTex?.dispose();
    },
  };
}
