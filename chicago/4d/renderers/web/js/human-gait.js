// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-gait.js — people on foot walk like people (T-3472).
 *
 * Every figure's `walk` clip is the same baked study (tools/human_grounded_gait.py): a
 * mechanical flat-foot shuffle at 0.6 m/s with 0.36 m steps, the knees straight through
 * the whole stance, the sole lifted and set down flat with no heel strike or push-off,
 * and the pelvis carried level with a 5 mm bob. Kevin, 2026-11-07, following Frances
 * Glessner across her court: "their walking is not very natural". It is half the speed
 * and half the step of anyone in a period street film, and it is a pose fixture, not a
 * walk (its own extras say so).
 *
 * This layer replaces the clip's pelvis and legs while a figure walks, every frame, on
 * any body on the contract skeleton, from the shape of a real gait cycle:
 *
 *   - SPEED AND STRIDE for the person: a comfortable pace for their sex and age (men
 *     about 1.35 m/s, women 1.25, slower past 55) and a stride that scales with their
 *     height; a woman in a floor-length skirt takes a shorter step at a quicker cadence.
 *     humans.js walks the figure at `gait.speed`, so the steps and the ground agree.
 *   - THE PHASE IS DISTANCE, NOT TIME: it advances by the ground the figure covered over
 *     its stride, so a figure that slows to turn, or stops, takes shorter steps in time
 *     and its feet never slide.
 *   - THE STANCE FOOT IS PLANTED IN THE WORLD: at heel strike it is set down where the
 *     swing put it and held there, rolling over the heel (the foot comes down toes-up and
 *     slaps flat), flat through mid-stance, then the heel rises and the foot rolls over
 *     the ball with the toes left flat on the ground until toe-off. Turning, the planted
 *     foot stays put and the leg twists over it.
 *   - THE SWING FOLLOWS THE MEASURED JOINT CURVES: hip and knee flexion through swing
 *     (the knee folds to about 60 degrees just after toe-off and straightens before the
 *     heel lands) carry the foot forward relative to the hip; a smooth correction makes
 *     it leave exactly where the stance ended and land exactly where the next step goes,
 *     a little inside the hips (feet land close to one line) and toed out a few degrees.
 *   - THE PELVIS rides the legs: its height is whatever lets the leading stance knee bend
 *     as the curves say (about 15-20 degrees on loading, nearly straight at mid-stance),
 *     so it is lowest in double support and highest over the planted foot, a few cm of
 *     bob that comes out of the legs rather than a sine; it shifts a couple of cm over the
 *     stance foot, turns a few degrees with the leading leg and dips on the swing side.
 *   - STARTING AND STOPPING: a figure that sets off swings its first foot from where it
 *     stood; one that stops takes a closing step, setting each foot down under its hip,
 *     before the clip's standing pose takes over again.
 *
 * What it leaves: the upper body to the clip and to human-life.js (trunk, head) and
 * human-actions.js (arms), which read `phase`, `weight` and the pelvis motion from this
 * object; the skirt to human-skirt.js. No assets, textures or draw calls: about forty
 * quaternion multiplies a walking figure a frame, only inside the animation range.
 *
 * Grades: the joint curves and events are the means of a public gait dataset (Fukuchi et
 * al. 2018, young adults at 1.24 m/s), the speeds and steps by sex and age those of Oberg,
 * Karsznia & Oberg 1993 and Bohannon & Andrews 2011, the pelvis's motion the same dataset's;
 * data/humans/gait/ holds the tables, their sources and period films to judge by. How a
 * given person of 1812, 1835 or 1904 walked is not recorded: the gait is reconstructed
 * motion within those bounds (liberty L-human-gait-3472). Deterministic: the only
 * per-person variation is seeded from the person id.
 */
import * as THREE from 'three';

const DEG = Math.PI / 180;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const mod1 = (x) => ((x % 1) + 1) % 1;

/**
 * Normal adult walking at a comfortable speed, every 5 % of the cycle from the reference
 * foot's heel strike (21 values, the last = the first). Degrees: hip + flexion (thigh vs
 * pelvis), knee + flexion, ankle + dorsiflexion. Rounded means of the young adults walking at
 * 1.24 m/s in the public gait dataset of Fukuchi, Fukuchi & Duarte 2018 (PeerJ 6:e4640;
 * data/humans/gait/normative_gait.json); the layer uses the knee in stance, all three in swing.
 */
export const GAIT_CURVES = Object.freeze({
  hip: Object.freeze([30, 29, 28, 24, 18, 13, 7, 3, -1, -4, -7, -8, -4, 4, 14, 22, 28, 31, 32, 30, 30]),
  knee: Object.freeze([0, 6, 13, 14, 11, 8, 6, 4, 3, 4, 8, 15, 29, 47, 59, 61, 54, 39, 19, 2, 0]),
  ankle: Object.freeze([1, -4, -2, 2, 5, 7, 8, 10, 12, 13, 12, 6, -6, -13, -7, 0, 5, 6, 4, 1, 1]),
});

/** Events of the cycle (fractions) and the foot's roll. */
export const GAIT = Object.freeze({
  stance: 0.617,         // toe-off; the other foot strikes at 0.5 and leaves at 0.117
  footFlat: 0.13,        // the heel rocker ends: the forefoot is down
  heelOff: 0.40,         // the heel rises (the foot's angle passes -3 deg)
  strikeDeg: 22,         // the foot's angle to the ground at heel strike, toes up
  toeOffDeg: -50,        // and at toe-off, heel up (rolled over the ball, toes flat)
  pelvisTiltDeg: 7,      // the thigh's angle to the vertical is hip flexion less the pelvis's tilt
  toeOutDeg: 8,          // each foot turned out from the line of travel
});

/**
 * A person's walk: comfortable speed (m/s, ground), stride (m, two steps), step width and
 * the pelvis's motion. Bounded by the published adult means: men 1.3-1.45 m/s with a
 * stride of about 0.8-0.85 of their height, women 1.2-1.35 m/s and 0.75-0.8, both slower
 * and shorter past 55 (Murray 1964, 1970; Oberg et al. 1993). A floor-length skirt over a
 * corset shortens a woman's step and stiffens her hips (reconstructed: no measured study).
 */
export function gaitProfile({ sex = 'male', age = 35, height = 1.72, skirt = false, seed = 0.5 } = {}) {
  const female = sex === 'female' || skirt;
  const old = clamp((age - 50) / 25, 0, 1); // 0 to 50, 1 by 75
  const jitter = (seed - 0.5) * 0.08;       // two people never walk exactly alike
  const speed = (female ? 1.25 : 1.35) * (1 - 0.12 * old) * (skirt ? 0.92 : 1) * (1 + jitter * 0.6);
  const ratio = (female ? 0.78 : 0.83) * (1 - 0.08 * old) * (skirt ? 0.95 : 1) * (1 + jitter * 0.4);
  const stride = ratio * height;
  return {
    speed, stride, cadence: (2 * speed) / stride,
    stepWidth: female ? 0.083 : 0.095,
    pelvisYawDeg: 5.5 * (skirt ? 0.7 : 1) * (1 - 0.3 * old),
    pelvisRollDeg: 4.5 * (skirt ? 0.7 : 1) * (1 - 0.3 * old),
    lateral: female ? 0.022 : 0.02,
  };
}

/** A periodic Catmull-Rom through a 21-point table at cycle fraction `c`. */
export function curveAt(table, c) {
  const x = mod1(c) * 20, i = Math.floor(x), t = x - i;
  const p = (k) => table[((k % 20) + 20) % 20];
  const p0 = p(i - 1), p1 = p(i), p2 = p(i + 1), p3 = p(i + 2);
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t);
}

const BONES = ['pelvis', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r', 'ball_l', 'ball_r'];
const SIDES = ['l', 'r'];
const OFFSET = { l: 0, r: 0.5 };
const UP = Object.freeze(new THREE.Vector3(0, 1, 0));

function seedOf(id) {
  let h = 2166136261;
  for (const ch of `gait:${id}`) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return ((h >>> 0) % 10007) / 10007;
}

/**
 * The walk of one figure. `profile` is gaitProfile's input ({ sex, age, height, skirt });
 * `height` is the person's own in metres (else the body's, as drawn). Returns null when
 * `scene` is not a body on the contract skeleton. It outlives a LOD swap: `bind(scene)`
 * attaches it to the new body and the walk goes on where it was.
 */
export function createHumanGait({ id = 'human', scene = null, profile = {} } = {}) {
  const seed = seedOf(id);
  let P = gaitProfile({ ...profile, seed });
  let bones = {}, bound = false, body = null, held = {};
  const rest = {};                 // the bind pose in the body's own frame: { p, q } per bone
  const leg = { l: {}, r: {} };
  const right = new THREE.Vector3(-1, 0, 0), fwd = new THREE.Vector3(0, 0, 1);
  let unit = 1;                    // world metres per body unit (a person's height scales the body)

  /**
   * The bind pose in the body's frame, from the skin's inverse bind matrices (the clip has
   * moved the bones). Those live in the skin's own space, which for a quantised level is a
   * scale and an offset away from metres: the skeleton's root bone, which no walking or
   * standing clip moves, gives that map (as human-variation.js reads it).
   */
  let bindToBody = new THREE.Matrix4();
  function restPose(found, next) {
    let skel = null;
    next.traverse((o) => { if (!skel && o.isSkinnedMesh && o.skeleton?.bones?.includes(found.foot_l)) skel = o.skeleton; });
    if (!skel) return null;
    next.updateMatrixWorld(true);
    const inv = next.matrixWorld.clone().invert();
    bindToBody = inv.multiply(skel.bones[0].matrixWorld).multiply(skel.boneInverses[0]);
    const res = {}, m = new THREE.Matrix4(), sc = new THREE.Vector3();
    for (const n of BONES) {
      const i = skel.bones.indexOf(found[n]);
      if (i < 0) return null;
      const p = new THREE.Vector3(), q = new THREE.Quaternion();
      m.copy(skel.boneInverses[i]).invert().premultiply(bindToBody).decompose(p, q, sc);
      res[n] = { p, q };
    }
    return res;
  }

  /** Heel, ball and toe of a foot on the ground, from the skin weighted to it. */
  function footShape(next, s, A, B) {
    let minZ = Infinity, maxZ = -Infinity, minY = Infinity;
    const v = new THREE.Vector3();
    next.traverse((o) => {
      if (!o.isSkinnedMesh || !o.geometry?.attributes?.skinWeight) return;
      const g = o.geometry, pos = g.attributes.position, si = g.attributes.skinIndex, sw = g.attributes.skinWeight;
      const want = new Set([`foot_${s}`, `ball_${s}`].map((n) => o.skeleton.bones.findIndex((b) => b.name === n)).filter((i) => i >= 0));
      if (!want.size) return;
      for (let i = 0; i < pos.count; i++) {
        let w = 0;
        for (let k = 0; k < 4; k++) if (want.has(si.getComponent(i, k))) w += sw.getComponent(i, k);
        if (w < 0.6) continue;
        v.fromBufferAttribute(pos, i).applyMatrix4(o.bindMatrix).applyMatrix4(bindToBody);
        if (Math.abs(v.x - A.x) > 0.09) continue;
        minZ = Math.min(minZ, v.z); maxZ = Math.max(maxZ, v.z); minY = Math.min(minY, v.y);
      }
    });
    const ok = Number.isFinite(minZ) && maxZ - minZ > 0.15 && maxZ - minZ < 0.36 && minY < A.y;
    const sole = ok ? Math.max(0, minY) : 0;
    return {
      sole, length: ok ? maxZ - minZ : null,
      heel: new THREE.Vector3(A.x, sole, ok ? minZ + 0.015 : A.z - 0.06),
      ball: new THREE.Vector3(B.x, sole, B.z),
      toe: new THREE.Vector3(B.x, sole, ok ? maxZ - 0.01 : B.z + 0.07),
    };
  }

  function bind(next) {
    const found = {};
    next.traverse((o) => { if (o.isBone && BONES.includes(o.name)) found[o.name] = o; });
    if (!BONES.every((n) => found[n])) { bound = false; return false; }
    const r = restPose(found, next);
    if (!r) { bound = false; return false; }
    Object.assign(rest, r);
    const across = rest.thigh_r.p.clone().sub(rest.thigh_l.p).projectOnPlane(UP);
    if (!(across.lengthSq() > 1e-6)) { bound = false; return false; }
    right.copy(across.normalize());
    fwd.copy(UP).cross(right).normalize();
    for (const s of SIDES) {
      const H = rest[`thigh_${s}`].p, K = rest[`calf_${s}`].p, A = rest[`foot_${s}`].p, B = rest[`ball_${s}`].p;
      const L = leg[s];
      L.side = s === 'l' ? 1 : -1;                 // +1 left: the figure's left is -right
      L.l1 = H.distanceTo(K); L.l2 = K.distanceTo(A);
      L.hipOff = H.clone().sub(rest.pelvis.p);
      L.thighAlong = K.clone().sub(H).normalize();
      L.calfAlong = A.clone().sub(K).normalize();
      L.shape = footShape(next, s, A, B);
      L.ankle = A.clone();
      L.ankleUp = A.y - L.shape.sole;
      L.hipHeight = H.y - L.shape.sole;
      // From the ankle to each pivot, flat, in the rest frame.
      L.toHeel = L.shape.heel.clone().sub(A);
      // The forefoot rocker turns about the toe joint itself (the toes stay flat under it).
      L.toBall = B.clone().sub(A);
      L.toToe = L.shape.toe.clone().sub(A);
    }
    held = {};
    for (const n of BONES) held[n] = { base: found[n].quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) };
    held.__pos = { base: found.pelvis.position.clone(), out: new THREE.Vector3(NaN, NaN, NaN) };
    bones = found;
    body = next;
    next.updateMatrixWorld(true);
    unit = next.getWorldScale(new THREE.Vector3()).y || 1;
    // Stature from the hip joint's height (about 0.53 of it in adults), not the drawn box,
    // which a hat and its plumes would stretch.
    const drawn = ((rest.thigh_l.p.y + rest.thigh_r.p.y) / 2 - leg.l.shape.sole) / 0.53 * unit;
    const metres = Number.isFinite(profile.height) && profile.height > 0.8 ? profile.height : drawn > 0.8 ? drawn : 1.7;
    P = gaitProfile({ ...profile, height: metres, seed });
    bound = true;
    return true;
  }

  // The clip's values are the base each frame; what this layer wrote last frame is not
  // (three's mixer writes a track only when its value changes).
  const rebase = () => {
    for (const n of BONES) {
      const h = held[n], q = bones[n].quaternion;
      if (q.equals(h.out)) q.copy(h.base); else h.base.copy(q);
    }
    const h = held.__pos, p = bones.pelvis.position;
    if (p.equals(h.out)) p.copy(h.base); else h.base.copy(p);
  };
  const settle = () => {
    for (const n of BONES) held[n].out.copy(bones[n].quaternion);
    held.__pos.out.copy(bones.pelvis.position);
  };

  // ---- state that survives a LOD swap ----
  let mode = 'idle';          // idle | walk | close
  let phase = 0.78, weight = 0, walked = 0;
  let pelvisY = null, pelvisYV = 0, closeT = 0;
  let closing = [];           // the closing steps still to take: side names
  const now = { yaw: 0, roll: 0, bob: 0, lateral: 0 };
  const foot = () => ({ stance: true, plant: new THREE.Vector3(), yaw: 0, e0: new THREE.Vector3(), pitch0: 0, yaw0: 0, toe0: 0, u0: 0, lastC: 0, step: null });
  const feet = { l: foot(), r: foot() };

  // Scratch.
  const sceneM = new THREE.Matrix4(), sceneInv = new THREE.Matrix4(), sceneQ = new THREE.Quaternion(), sceneQInv = new THREE.Quaternion();
  const q1 = new THREE.Quaternion(), q2 = new THREE.Quaternion(), qh = new THREE.Quaternion(), qr = new THREE.Quaternion();
  const v1 = new THREE.Vector3(), v2 = new THREE.Vector3(), v3 = new THREE.Vector3(), vh = new THREE.Vector3();
  const mA = new THREE.Matrix4(), mB = new THREE.Matrix4();
  const out = Object.fromEntries(BONES.map((n) => [n, new THREE.Quaternion()]));
  const pelvisPos = new THREE.Vector3();
  const poses = { l: { A: new THREE.Vector3() }, r: { A: new THREE.Vector3() } };
  const land = new THREE.Vector3(), endFk = new THREE.Vector3(), fk = new THREE.Vector3();

  /** The foot's turn: `yaw` about up after `pitch` (toes up +) about the body's right. */
  const footTurn = (target, pitch, yaw) => target.setFromAxisAngle(UP, yaw).multiply(qr.setFromAxisAngle(right, pitch));

  /** The rolled foot's ankle, from its flat-foot ankle `A` and the pivot the roll is about. */
  function rolled(s, A, pitch, yaw, target) {
    const L = leg[s];
    const o = pitch >= 0 ? L.toHeel : L.toBall;   // the heel rocker, then the forefoot rocker
    footTurn(q1, pitch, yaw);
    q2.setFromAxisAngle(UP, yaw);
    // pivot = A + yaw(o); ankle = pivot + turn(-o)
    return target.copy(o).applyQuaternion(q2).add(A).add(v3.copy(o).negate().applyQuaternion(q1));
  }
  /** The inverse: the flat-foot ankle whose roll by `pitch` puts the ankle at `A`. */
  function unrolled(s, A, pitch, yaw, target) {
    const L = leg[s];
    const o = pitch >= 0 ? L.toHeel : L.toBall;
    footTurn(q1, pitch, yaw);
    q2.setFromAxisAngle(UP, yaw);
    return target.copy(A).sub(v3.copy(o).applyQuaternion(q2)).sub(v1.copy(o).negate().applyQuaternion(q1));
  }

  /** The swing's curves at cycle `c`: the ankle relative to its hip, and the foot's pitch. */
  function swingFK(s, c, target) {
    const L = leg[s];
    const a = (curveAt(GAIT_CURVES.hip, c) - GAIT.pelvisTiltDeg) * DEG;
    const k = curveAt(GAIT_CURVES.knee, c) * DEG;
    target.set(0, 0, 0)
      .addScaledVector(fwd, L.l1 * Math.sin(a) + L.l2 * Math.sin(a - k))
      .addScaledVector(UP, -(L.l1 * Math.cos(a) + L.l2 * Math.cos(a - k)));
    return (a - k) + curveAt(GAIT_CURVES.ankle, c) * DEG;
  }

  /**
   * Where the ankle is at heel strike, relative to the pelvis then (body frame): as far
   * ahead of the hip as the curves put it (thigh forward, knee nearly straight), in
   * proportion to how long this person's stride is for their leg, close to the line of
   * travel. The rest of the stance's ground passes behind the hip.
   */
  function landing(s, target) {
    const L = leg[s], stride = P.stride / unit;
    swingFK(s, 0, v2);
    const ahead = v2.dot(fwd) * clamp(stride / (1.566 * L.hipHeight), 0.8, 1.2);
    v1.set(0, 0, 0)
      .addScaledVector(right, -L.side * (P.stepWidth / unit) / 2)
      .addScaledVector(fwd, ahead);
    v1.y = L.shape.sole + L.ankleUp - rest.pelvis.p.y;
    rolled(s, v1, GAIT.strikeDeg * DEG, L.side * GAIT.toeOutDeg * DEG, target);
    // The roll about the heel draws the ankle back: put it where the curves have it.
    return target.addScaledVector(fwd, ahead + L.hipOff.dot(fwd) - target.dot(fwd));
  }

  /** The hip joint now (body frame), from the pelvis's place and turn. */
  const hipNow = (s, target) => target.copy(leg[s].hipOff)
    .applyQuaternion(qh.setFromAxisAngle(UP, now.yaw).multiply(q2.setFromAxisAngle(fwd, now.roll))).add(pelvisPos);

  const groundAnkle = (s) => leg[s].shape.sole + leg[s].ankleUp;

  /** A planted foot at cycle `c`: heel rocker, flat, then up over the ball. */
  function stancePose(s, c, pose) {
    const f = feet[s];
    let pitch = 0;
    if (c < GAIT.footFlat) pitch = GAIT.strikeDeg * DEG * (1 - smooth(c / GAIT.footFlat));
    else if (c > GAIT.heelOff) { const t = clamp((c - GAIT.heelOff) / (GAIT.stance - GAIT.heelOff), 0, 1); pitch = GAIT.toeOffDeg * DEG * t * t; }
    // Planted in the world across the ground; its height rides the figure's (steps, slopes).
    v2.copy(f.plant).applyMatrix4(sceneInv);
    v2.y = groundAnkle(s);
    rolled(s, v2, pitch, f.yaw, pose.A);
    pose.pitch = pitch; pose.yaw = f.yaw; pose.toe = pitch < 0 ? -pitch : 0;
    return pose;
  }

  /** Plant a foot whose ankle is at `A` (body frame) rolled by `pitch`, turned `yaw`. */
  function plantAt(s, A, pitch, yaw) {
    unrolled(s, A, pitch, yaw, v2);
    feet[s].plant.copy(v2).applyMatrix4(sceneM);
    feet[s].yaw = yaw;
  }

  /** Begin a swing at cycle `c` from the body-frame ankle `A` (rolled `pitch`, turned `yaw`). */
  function beginSwing(s, A, pitch, yaw, c) {
    const f = feet[s];
    f.stance = false;
    f.u0 = clamp((c - GAIT.stance) / (1 - GAIT.stance), 0, 0.95);
    const fkPitch = swingFK(s, c, fk);
    f.e0.copy(A).sub(hipNow(s, vh)).sub(fk);
    f.pitch0 = pitch - fkPitch;
    f.yaw0 = yaw;
    f.toe0 = pitch < 0 ? -pitch : 0;
  }

  /** A foot in the air at cycle `c`: the curves, corrected to leave and land where it must. */
  function swingPose(s, c, pose) {
    const f = feet[s], L = leg[s], A = pose.A;
    const u = clamp((c - GAIT.stance) / (1 - GAIT.stance), 0, 1);
    const m = smooth((u - f.u0) / Math.max(1e-3, 1 - f.u0));
    const fkPitch = swingFK(s, c, A);
    const H = hipNow(s, vh);
    landing(s, land).add(v1.set(pelvisPos.x, rest.pelvis.p.y, pelvisPos.z));
    const endPitch = swingFK(s, 1, endFk);
    // e1 = land - H - FK(1): at c = 1 the ankle is at the landing.
    A.add(H).addScaledVector(f.e0, 1 - m).add(v1.copy(land).sub(H).sub(endFk).multiplyScalar(m));
    const pitch = fkPitch + f.pitch0 * (1 - m) + (GAIT.strikeDeg * DEG - endPitch) * m;
    const yawEnd = L.side * GAIT.toeOutDeg * DEG;
    pose.yaw = f.yaw0 + (yawEnd - f.yaw0) * smooth(u * 1.5);
    pose.toe = f.toe0 * (1 - smooth(u / 0.3));
    pose.pitch = pitch;
    // Never through the ground: the heel, the ball's sole and the toe tip (bent up by
    // what is left of the push-off) stay above it, eased in after toe-off and out before
    // the heel strikes so the clearance never jumps.
    const ease = smooth(u / 0.15) * (1 - smooth((u - 0.82) / 0.14));
    if (ease > 0) {
      const yAt = (v, p) => v.y * Math.cos(p) + v.z * Math.sin(p);   // height after pitch p (toes up +)
      const ballY = yAt(L.toBall, pitch);
      const tipY = ballY + yAt(v1.copy(L.toToe).sub(L.toBall), pitch + pose.toe);
      const ballSoleY = yAt(v1.copy(L.toBall).setY(-L.ankleUp), pitch);
      const lowest = Math.min(yAt(L.toHeel, pitch), tipY, ballSoleY);
      const floor = L.shape.sole + 0.012 - lowest;
      if (A.y < floor) A.y += (floor - A.y) * ease;
    }
    return pose;
  }

  /** A closing step: the foot lifts and is set down under its own hip. */
  function stepPose(s, pose) {
    const st = feet[s].step, t = clamp(st.t / st.T, 0, 1), m = smooth(t);
    pose.A.lerpVectors(st.from, st.to, m);
    pose.A.y += Math.sin(Math.PI * t) * 0.06;
    pose.pitch = st.pitch * (1 - m) - Math.sin(Math.PI * t) * 6 * DEG;
    pose.yaw = st.yaw0 * (1 - m) + st.yaw1 * m;
    pose.toe = Math.max(0, -st.pitch) * (1 - smooth(t / 0.4));
    return pose;
  }

  function startWalking() {
    // Feet planted where they stand; the left foot in late swing, the right at mid-stance,
    // so the first step is the left's, from beside the right. (Called once the pelvis is
    // placed for the frame: the swing is measured from the hip.)
    body.updateMatrixWorld(true);
    for (const s of SIDES) {
      const f = feet[s];
      const A = bones[`foot_${s}`].getWorldPosition(new THREE.Vector3()).applyMatrix4(sceneInv);
      const c = mod1(phase - OFFSET[s]);
      f.lastC = c; f.step = null;
      if (c < GAIT.stance) { f.stance = true; A.y = groundAnkle(s); plantAt(s, A, 0, f.yaw); }
      else beginSwing(s, A, 0, f.yaw, c);
    }
    closing = [];
  }

  /** Stopping: the foot in the air (else the one further from its stand) steps under its hip, then the other. */
  function beginClose() {
    mode = 'close';
    closeT = 0;
    const gap = (s) => {
      if (!feet[s].stance) return 9;
      v1.copy(feet[s].plant).applyMatrix4(sceneInv);
      return Math.hypot(v1.x - leg[s].ankle.x, v1.z - leg[s].ankle.z);
    };
    closing = SIDES.slice().sort((a, b) => gap(b) - gap(a)).filter((s) => gap(s) > 0.05);
    nextStep();
  }
  function nextStep() {
    const s = closing.shift();
    if (!s) return;
    const f = feet[s], pose = poses[s];
    if (f.stance) stancePose(s, Math.min(f.lastC, GAIT.stance - 1e-3), pose);
    else swingPose(s, f.lastC, pose);
    const to = leg[s].ankle.clone(); to.y = groundAnkle(s);
    const from = pose.A.clone();
    f.step = { t: 0, T: clamp(0.28 + from.distanceTo(to) * 0.5, 0.3, 0.55), from, to, pitch: pose.pitch, yaw0: pose.yaw, yaw1: 0 };
    f.stance = false;
  }

  const api = {
    get bound() { return bound; },
    bind,
    /** 0..1: 0 = the left heel strikes, 0.5 = the right. */
    get phase() { return phase; },
    /** How much of the pose the gait writes now, 0..1. */
    get weight() { return weight; },
    get speed() { return P.speed; },
    get stride() { return P.stride; },
    get cadence() { return P.cadence; },
    get profile() { return P; },
    get mode() { return mode; },
    /** The pelvis now, for the trunk and arms: yaw (+ = turned left), roll (+ = top right),
     *  bob (m). Not faded by `weight`: the readers blend by it themselves. */
    get pelvisYaw() { return now.yaw; },
    get pelvisRoll() { return now.roll; },
    get bob() { return now.bob * unit; },
    /** How fast to move the figure, as a share of `speed`: it gathers pace over the first step. */
    get pace() { return mode === 'walk' ? clamp(0.5 + walked / (0.6 * P.stride), 0.5, 1) : 1; },
    /** Change who is walking (the person's record arrived). */
    setProfile(next) { Object.assign(profile, next); if (bound) bind(body); return api; },
    /**
     * One frame, after the mixer and before the life and arm layers. `moved` is the ground
     * distance (world metres) the figure's root covered since the last frame.
     */
    apply(dt, { state = 'standing', moved = 0 } = {}) {
      if (!bound) return;
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.1) : 0;
      rebase();
      body.updateWorldMatrix(true, false);
      sceneM.copy(body.matrixWorld);
      sceneInv.copy(sceneM).invert();
      body.getWorldQuaternion(sceneQ);
      sceneQInv.copy(sceneQ).invert();
      const walking = state === 'walking';
      let fresh = false;
      if (walking && mode !== 'walk') { mode = 'walk'; phase = 0.78; walked = 0; fresh = true; }
      else if (!walking && mode === 'walk') beginClose();
      if (mode === 'idle') { weight = 0; settle(); return; }

      if (mode === 'walk') {
        weight = Math.min(1, weight + dt / 0.2);
        const ds = Math.max(0, Number.isFinite(moved) ? moved : 0);
        walked += ds;
        phase = mod1(phase + ds / P.stride);
      } else closeT += dt;

      // ---- the pelvis: turned with the leading leg, dipped on the swing side, over the stance foot ----
      const w = mode === 'walk' ? 1 : 1 - smooth(closeT / 0.6);
      const ph = 2 * Math.PI * phase;
      now.yaw = -P.pelvisYawDeg * DEG * Math.cos(ph) * w;                     // left heel strike: left hip forward
      now.roll = P.pelvisRollDeg * DEG * Math.sin(ph + 2 * Math.PI * 0.07) * w; // left stance: the right side dips
      now.lateral = (P.lateral / unit) * Math.sin(ph + 2 * Math.PI * 0.0) * w;  // toward the left foot in its stance
      pelvisPos.copy(rest.pelvis.p).addScaledVector(right, -now.lateral);
      if (fresh) startWalking();

      // ---- the feet ----
      for (const s of SIDES) {
        const f = feet[s], pose = poses[s];
        if (mode === 'close') {
          if (f.step) {
            f.step.t += dt;
            stepPose(s, pose);
            pose.stance = false;
            if (f.step.t >= f.step.T) { plantAt(s, f.step.to, 0, 0); f.stance = true; f.lastC = GAIT.footFlat + 0.02; f.step = null; nextStep(); }
          } else if (f.stance) { stancePose(s, f.lastC, pose); pose.stance = true; pose.c = f.lastC; }
          else { swingPose(s, f.lastC, pose); pose.stance = false; }
          continue;
        }
        const c = mod1(phase - OFFSET[s]);
        if (f.stance && c >= GAIT.stance && f.lastC < GAIT.stance) {
          stancePose(s, GAIT.stance - 1e-4, pose);
          beginSwing(s, pose.A.clone(), pose.pitch, pose.yaw, c);
        } else if (!f.stance && c < f.lastC) {
          swingPose(s, 1 - 1e-4, pose);          // heel strike: set down where the swing put it
          f.stance = true;
          plantAt(s, pose.A, pose.pitch, pose.yaw);
        }
        f.lastC = c;
        pose.c = c;
        pose.stance = f.stance;
        if (f.stance) stancePose(s, c, pose); else swingPose(s, c, pose);
      }

      // ---- the pelvis height: as low as each supporting knee bends by the curves ----
      // (lowest in double support, highest over the planted foot: the bob is the legs')
      let hard = Infinity, sum = 0, any = false;
      const k = 0.005;
      const ys = [];
      for (const s of SIDES) {
        const p = poses[s], L = leg[s];
        let knee = null;
        if (mode === 'close') knee = p.stance ? 3 : null;
        else if (p.stance) knee = p.c <= 0.5 ? curveAt(GAIT_CURVES.knee, p.c) : 1;
        else if (p.c > 0.94) knee = 5 + (1 - p.c) * 40;
        if (knee === null) continue;
        // A foot about to land, or one pushing off behind, eases the hips down; neither pins them.
        const soft = !p.stance || (mode !== 'close' && p.c > 0.5);
        const d = Math.sqrt(L.l1 * L.l1 + L.l2 * L.l2 + 2 * L.l1 * L.l2 * Math.cos(knee * DEG));
        const H = hipNow(s, vh);
        const dx = p.A.x - H.x, dz = p.A.z - H.z;
        const y = p.A.y + Math.sqrt(Math.max(0, d * d - dx * dx - dz * dz)) - (H.y - pelvisPos.y);
        ys.push(y);
        if (!soft) hard = Math.min(hard, y);
        any = true;
      }
      const lo = Math.min(...ys);
      for (const y of ys) sum += Math.exp(-(y - lo) / k);
      let target = any ? lo - k * Math.log(sum) : rest.pelvis.p.y;
      target = clamp(target, rest.pelvis.p.y - 0.12 / unit, rest.pelvis.p.y + 0.004);
      if (mode === 'close') target += (rest.pelvis.p.y - target) * smooth((closeT - 0.2) / 0.8);
      if (pelvisY === null || !Number.isFinite(pelvisY)) { pelvisY = target; pelvisYV = 0; }
      const om = 28, x = pelvisY - target, e = Math.exp(-om * dt), tmp = (pelvisYV + om * x) * dt;
      pelvisYV = (pelvisYV - om * tmp) * e;
      pelvisY = target + (x + tmp) * e;
      if (Number.isFinite(hard)) pelvisY = Math.min(pelvisY, hard + 0.003);
      pelvisPos.y = pelvisY;
      now.bob = pelvisY - rest.pelvis.p.y;

      // ---- pose the bones (body frame), then write each as its parent's local ----
      out.pelvis.setFromAxisAngle(UP, now.yaw).multiply(q1.setFromAxisAngle(fwd, now.roll)).multiply(rest.pelvis.q);
      for (const s of SIDES) {
        const p = poses[s];
        const H = hipNow(s, new THREE.Vector3());
        solveLeg(s, H, p.A, (p.yaw + now.yaw) / 2, out[`thigh_${s}`], out[`calf_${s}`]);
        footTurn(out[`foot_${s}`], p.pitch, p.yaw).multiply(rest[`foot_${s}`].q);
        footTurn(out[`ball_${s}`], p.pitch + p.toe, p.yaw).multiply(rest[`ball_${s}`].q);
      }
      if (mode === 'close' && !closing.length && SIDES.every((s) => !feet[s].step) && closeT > 0.2) {
        weight = Math.max(0, weight - dt / 0.35);
        if (weight <= 0) { mode = 'idle'; pelvisY = null; settle(); return; }
      }

      const parentFig = q2.copy(sceneQInv).multiply(bones.pelvis.parent.getWorldQuaternion(q1));
      const local = (child, parent) => qh.copy(parent).invert().multiply(child);
      bones.pelvis.quaternion.slerp(local(out.pelvis, parentFig), weight);
      for (const s of SIDES) {
        bones[`thigh_${s}`].quaternion.slerp(local(out[`thigh_${s}`], out.pelvis), weight);
        bones[`calf_${s}`].quaternion.slerp(local(out[`calf_${s}`], out[`thigh_${s}`]), weight);
        bones[`foot_${s}`].quaternion.slerp(local(out[`foot_${s}`], out[`calf_${s}`]), weight);
        bones[`ball_${s}`].quaternion.slerp(local(out[`ball_${s}`], out[`foot_${s}`]), weight);
      }
      bones.pelvis.parent.updateWorldMatrix(true, false);
      mA.copy(bones.pelvis.parent.matrixWorld).invert().multiply(sceneM);
      bones.pelvis.position.lerp(v1.copy(pelvisPos).applyMatrix4(mA), weight);
      settle();
    },
    snapshot() {
      return { mode, phase: +phase.toFixed(4), weight: +weight.toFixed(3), speed: +P.speed.toFixed(3), stride: +P.stride.toFixed(3),
        cadence_steps_min: +(P.cadence * 60).toFixed(1), bob_m: +(now.bob * unit).toFixed(4),
        yaw_deg: +(now.yaw / DEG).toFixed(2), roll_deg: +(now.roll / DEG).toFixed(2), stance: { l: feet.l.stance, r: feet.r.stance } };
    },
  };

  /** Two-bone IK, body frame: hip `H`, ankle `T`, the knee forward over a foot turned `yaw`. */
  function solveLeg(s, H, T, yaw, thighQ, calfQ) {
    const L = leg[s];
    const d = v1.copy(T).sub(H);
    const dist = clamp(d.length(), Math.abs(L.l1 - L.l2) + 1e-4, L.l1 + L.l2 - 1e-5);
    d.normalize();
    const pole = v2.copy(fwd).applyAxisAngle(UP, yaw);
    const n = v3.copy(d).cross(pole);
    if (n.lengthSq() < 1e-8) n.copy(right).applyAxisAngle(UP, yaw);
    n.normalize();                                 // the knee's hinge: the leg's right
    const cosA = clamp((L.l1 * L.l1 + dist * dist - L.l2 * L.l2) / (2 * L.l1 * dist), -1, 1);
    const b = new THREE.Vector3().crossVectors(n, d).normalize();
    const E = new THREE.Vector3().copy(H).addScaledVector(d, L.l1 * cosA).addScaledVector(b, L.l1 * Math.sqrt(1 - cosA * cosA));
    const W = new THREE.Vector3().copy(H).addScaledVector(d, dist);
    align(thighQ, L.thighAlong, E.clone().sub(H), n).multiply(rest[`thigh_${s}`].q);
    align(calfQ, L.calfAlong, W.sub(E), n).multiply(rest[`calf_${s}`].q);
  }
  /** The rotation taking a rest bone (along `from`, hinge = the body's right) to along `to`, hinge `hinge`. */
  function align(q, from, to, hinge) {
    const f = from.clone().normalize(), r0 = right.clone().addScaledVector(f, -right.dot(f)).normalize();
    const t = to.clone().normalize(), r1 = hinge.clone().addScaledVector(t, -hinge.dot(t)).normalize();
    mA.makeBasis(f, r0, f.clone().cross(r0));
    mB.makeBasis(t, r1, t.clone().cross(r1));
    return q.setFromRotationMatrix(mB.multiply(mA.transpose()));
  }

  if (scene && !bind(scene)) return null;
  return api;
}
