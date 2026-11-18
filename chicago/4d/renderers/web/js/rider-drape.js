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
export function drapeRider({ meshes, kindOf = null, tack, seatHalfDeg = 45, press = null }) {
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
  const items = [];
  for (const mesh of meshes) {
    const draped = drapes(mesh, kindOf?.(mesh) ?? null);
    if (!draped && !(Z && mesh?.isSkinnedMesh)) continue;
    const body = draped ? GLSL_BODY : GLSL_PRESS;
    const uIn = { value: new THREE.Matrix4() }, uOut = { value: new THREE.Matrix4() };
    const was = mesh.material;
    const list = (Array.isArray(was) ? was : [was]).map((m) => {
      const c = m.clone();
      c.onBeforeCompile = (shader, renderer) => {
        m.onBeforeCompile?.call(c, shader, renderer);
        Object.assign(shader.uniforms, { drapeIn: uIn, drapeOut: uOut, drapeR: { value: tex }, drapeK: { value: K }, drapeP: { value: P },
          drapeZ: { value: Z ?? new THREE.Vector4() } });
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', `#include <common>\n${GLSL_HEAD}`)
          .replace('#include <skinning_vertex>', `#include <skinning_vertex>\n${body}`);
      };
      const key = m.customProgramCacheKey?.bind(m);
      c.customProgramCacheKey = () => `${key ? key() : ''}|rider-${draped ? 'drape' : 'press'}`;
      return c;
    });
    mesh.material = Array.isArray(was) ? list : list[0];
    items.push({ mesh, was, list, uIn, uOut });
  }
  if (!items.length) { tex.dispose(); return null; }
  const restNow = new THREE.Matrix4(), M = new THREE.Matrix4();
  return {
    meshes: items.map((i) => i.mesh),
    update() {
      // world -> the trunk's rest pose in the root frame -> the envelope's frame
      restNow.copy(tack.bodyRest).multiply(M.copy(body.matrixWorld).invert()).premultiply(toEnv);
      for (const it of items) {
        it.uIn.value.copy(restNow).multiply(it.mesh.matrixWorld);
        it.uOut.value.copy(it.uIn.value).invert();
      }
    },
    dispose() {
      for (const it of items) {
        if (it.mesh.material === (Array.isArray(it.was) ? it.list : it.list[0])) it.mesh.material = it.was;
        for (const c of it.list) c.dispose();
      }
      tex.dispose();
    },
  };
}
