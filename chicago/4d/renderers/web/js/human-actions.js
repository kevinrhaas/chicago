// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-actions.js — what a person on foot does with their arms (T-3419).
 *
 * The figures' clips hold the arms in one place: the idle hangs them a little away
 * from the body, and the walk clip carries them stiff at the sides through the whole
 * stride (measured: the hands do not move a centimetre in a cycle). Kevin, 2026-11-06,
 * approving the photographic-humans plan: everyday actions, and a walk with arm swing.
 * This layer sits after the life layer (human-life.js, which owns the pelvis, spine,
 * head and eyes) and owns only the arms and hands:
 *
 *   - at rest, the arms hang in by the sides with the elbows soft;
 *   - standing, a person changes what they do with their hands every so often: hands
 *     on the hips, hands clasped behind the back, or just hanging;
 *   - a visitor who comes up in front is greeted with a hand to the brow (the working
 *     man's touch of the hat brim or forelock) and a small nod;
 *   - walking, the arms swing opposite to the legs, read from where the feet are, so the
 *     swing follows any walk clip's stride and stops when the feet stop.
 *
 * Hand placements are solved by two-bone IK in the figure's own frame, from landmarks
 * read off the body (the hips, the small of the back, the brow), so they fit any body
 * on the contract skeleton. Each pose blends in and out over most of a second.
 *
 * Talking in pairs, sweeping and carrying need a second person and props, and the
 * coat-tail sway needs coats: they follow with the wardrobe kit and the next people.
 * T-3481: carrying by the hand. A dress that carries something (a market basket) names
 * the hand and its hold in the GLB's wardrobe extras (`carry`): that arm is held there,
 * a little out from the skirt, in every state, and does not swing or take a pose.
 *
 * Deterministic (seeded from the person id), additive over the clip, rebuilt each frame.
 * Reconstructed motion: liberty L-human-actions-3415.
 */
import * as THREE from 'three';
import { seededRandom } from './driver-life.js';

const DEG = Math.PI / 180;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const SIDES = ['l', 'r'];
const FINGERS = ['index', 'middle', 'ring', 'pinky'];
const ARM = (s) => [`upperarm_${s}`, `lowerarm_${s}`, `hand_${s}`,
  ...FINGERS.flatMap((f) => ['01', '02', '03'].map((k) => `${f}_${k}_${s}`)), `thumb_01_${s}`, `thumb_02_${s}`];
const NEEDED = ['pelvis', 'spine_03', 'head', 'thigh_l', 'thigh_r', 'foot_l', 'foot_r', 'upperarm_l', 'upperarm_r',
  'lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'];

/** The standing hand poses a person moves between; `rest` is no IK at all. */
export const HAND_POSES = Object.freeze(['rest', 'hips', 'behind', 'clasp']);
// A woman in a full skirt (T-3434) never lets her hands hang, nor sets them on her hips: in
// both the hand sinks into the skirt's bell. She stands with them clasped in front at the
// waist, over the apron, or held at the waist behind.
export const SKIRT_POSES = Object.freeze(['clasp', 'behind']);

export function createHumanActions({ id = 'human', scene = null, greeting = 'brow', skirt = false, carry = null } = {}) {
  const rand = seededRandom(`actions:${id}`);
  const between = (a, b) => a + (b - a) * rand();
  let bones = {}, held = {}, bound = false, root = null, body = null;
  const L = {}; // landmarks and lengths, figure frame, from the bind pose
  const local = {}; // per-bone local axes: along the bone, and the palm's normal for hands
  const fig = { up: new THREE.Vector3(0, 1, 0), fwd: new THREE.Vector3(0, 0, 1), left: new THREE.Vector3(1, 0, 0) };
  // T-3481: the carrying hand's hold, figure frame (the dress module drew the thing it holds there).
  const vec = (a) => (Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? new THREE.Vector3(...a) : null);
  const hold = carry && SIDES.includes(carry.side) && vec(carry.wrist_from_shoulder) && vec(carry.fingers) && vec(carry.palm)
    ? { side: carry.side, offset: vec(carry.wrist_from_shoulder), pole: vec(carry.elbow_pole) ?? new THREE.Vector3(0.7, -0.1, -0.7),
      fingers: vec(carry.fingers), palm: vec(carry.palm), curl: Number.isFinite(carry.curl) ? carry.curl : 0.7, wrist: null }
    : null;

  function bind(next) {
    const found = {};
    next.traverse((o) => { if (o.isBone) found[o.name] = o; });
    if (!NEEDED.every((n) => found[n])) { bound = false; return false; }
    next.updateMatrixWorld(true);
    const inv = next.matrixWorld.clone().invert();
    const at = (n) => found[n].getWorldPosition(new THREE.Vector3()).applyMatrix4(inv);
    // The figure's frame, as human-life.js reads it: right from the left hip to the right.
    const right = at('thigh_r').sub(at('thigh_l')).projectOnPlane(fig.up);
    if (right.lengthSq() < 1e-6) { bound = false; return false; }
    fig.left.copy(right).normalize().negate();
    fig.fwd.copy(fig.up).cross(right.normalize()).normalize();
    for (const s of SIDES) {
      L[`upper_${s}`] = at(`lowerarm_${s}`).distanceTo(at(`upperarm_${s}`));
      L[`lower_${s}`] = at(`hand_${s}`).distanceTo(at(`lowerarm_${s}`));
      for (const n of [`upperarm_${s}`, `lowerarm_${s}`]) {
        const child = found[n === `upperarm_${s}` ? `lowerarm_${s}` : `hand_${s}`];
        local[n] = { along: child.position.clone().normalize() };
      }
      // A hand: along to the middle finger's knuckle, and its palm's normal, from the
      // knuckles' order: index to pinky across the hand, palm = along x across on the right
      // hand and across x along on the left (the mirror). Read from the skeleton, so it
      // holds whatever pose the clip has the hand in. T-3456 (owner, 2026-11-07: "are his
      // hands backwards? ... when i stand and let my hands loose, my thumbs point forward"):
      // the two products were the other way round, which is the BACK of the hand (in the
      // bind pose, palm down, they gave +Y), so every placed hand showed its back where its
      // palm was asked for: a hanging hand turned palm out, thumb back.
      const knuckle = found[`middle_01_${s}`];
      const along = knuckle ? knuckle.position.clone().normalize() : new THREE.Vector3(0, 1, 0);
      let palm = new THREE.Vector3(1, 0, 0);
      if (found[`index_01_${s}`] && found[`pinky_01_${s}`]) {
        const across = found[`pinky_01_${s}`].position.clone().sub(found[`index_01_${s}`].position);
        palm = s === 'r' ? along.clone().cross(across) : across.cross(along);
        if (palm.lengthSq() < 1e-10) palm.set(1, 0, 0);
        palm.addScaledVector(along, -palm.dot(along)).normalize();
      }
      local[`hand_${s}`] = { along, palm };
      // Which way about each finger's local X closes it toward the palm.
      const f2 = found[`index_02_${s}`], tip = found[`index_03_${s}`];
      if (f2 && tip) {
        const t0 = tip.position.clone().applyQuaternion(f2.quaternion);
        const t1 = tip.position.clone().applyQuaternion(f2.quaternion.clone().multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), 0.3)));
        // Both are in index_01's frame; carry the palm normal there through the chain.
        const toF1 = found[`index_01_${s}`].quaternion.clone().invert();
        local[`curl_${s}`] = t1.sub(t0).dot(palm.clone().applyQuaternion(toF1)) >= 0 ? 1 : -1;
      } else local[`curl_${s}`] = 1;
    }
    L.handLen = found.middle_03_r ? at('middle_03_r').distanceTo(at('hand_r')) + 0.025 : 0.17;
    const hipL = at('thigh_l'), hipR = at('thigh_r');
    L.hipHalf = hipL.distanceTo(hipR) / 2;
    L.pelvisY = at('pelvis').y;
    const eyes = found.eye_l && found.eye_r ? at('eye_l').add(at('eye_r')).multiplyScalar(0.5) : at('head').add(new THREE.Vector3(0, 0.05, 0.09));
    L.brow = eyes.add(new THREE.Vector3(0, 0.055, 0.035));
    L.backZ = Math.min(at('pelvis').z, at('spine_03').z) - 0.13; // the small of the back's surface, roughly
    L.frontZ = Math.max(at('pelvis').z, at('spine_03').z) + 0.19; // the front of a skirt and apron at the waist, roughly
    L.waistY = (at('pelvis').y + at('spine_03').y) / 2;
    if (hold) hold.wrist = at(`upperarm_${hold.side}`).add(hold.offset);
    held = {};
    for (const s of SIDES) for (const n of ARM(s)) if (found[n]) held[n] = { base: found[n].quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) };
    bones = found;
    body = next;
    bound = true;
    return true;
  }

  const rebase = () => { for (const [n, h] of Object.entries(held)) { const q = bones[n].quaternion; if (q.equals(h.out)) q.copy(h.base); else h.base.copy(q); } };
  const settle = () => { for (const [n, h] of Object.entries(held)) h.out.copy(bones[n].quaternion); };

  // Figure-frame vector → world, and the scene's world frame.
  const sceneQ = new THREE.Quaternion(), sceneM = new THREE.Matrix4();
  const toWorldDir = (v) => v.clone().applyQuaternion(sceneQ);
  const toWorldPos = (v) => v.clone().applyMatrix4(sceneM);
  const qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), va = new THREE.Vector3(), vb = new THREE.Vector3();

  /** Rotate bone `n` (blend `w`) so its `along` axis points along world `dir`. */
  function aim(n, dir, w) {
    const b = bones[n];
    b.parent.updateWorldMatrix(true, false);
    const parentQ = b.parent.getWorldQuaternion(qa);
    const worldQ = qb.copy(parentQ).multiply(b.quaternion);
    const cur = va.copy(local[n].along).applyQuaternion(worldQ);
    const delta = new THREE.Quaternion().setFromUnitVectors(cur.normalize(), vb.copy(dir).normalize());
    const target = delta.multiply(worldQ);
    const next = parentQ.clone().invert().multiply(target);
    b.quaternion.slerp(next, w);
  }

  /** Two-bone IK: put side `s`'s wrist at world `T`, the elbow toward world `pole`. */
  function reach(s, T, pole, w) {
    if (!(w > 1e-4)) return;
    const up = bones[`upperarm_${s}`];
    up.updateWorldMatrix(true, false);
    const S = up.getWorldPosition(new THREE.Vector3());
    const a = L[`upper_${s}`], b = L[`lower_${s}`];
    const d = T.clone().sub(S);
    const dist = clamp(d.length(), Math.abs(a - b) + 1e-3, a + b - 1e-3);
    d.normalize();
    const cosA = clamp((a * a + dist * dist - b * b) / (2 * a * dist), -1, 1);
    const n = pole.clone().addScaledVector(d, -pole.dot(d));
    if (n.lengthSq() < 1e-8) n.copy(toWorldDir(fig.up)).addScaledVector(d, -d.y);
    n.normalize();
    const E = S.clone().addScaledVector(d, a * cosA).addScaledVector(n, a * Math.sqrt(1 - cosA * cosA));
    const W = S.clone().addScaledVector(d, dist);
    aim(`upperarm_${s}`, E.clone().sub(S), w);
    up.updateMatrixWorld(true);
    const elbow = bones[`lowerarm_${s}`].getWorldPosition(new THREE.Vector3());
    aim(`lowerarm_${s}`, W.sub(elbow), w);
  }

  /** Turn hand `s` (blend `w`) so its fingers point along `fingers` and its palm faces `palm` (world). */
  function orientHand(s, fingers, palm, w) {
    if (!(w > 1e-4)) return;
    const h = bones[`hand_${s}`], ax = local[`hand_${s}`];
    h.parent.updateWorldMatrix(true, false);
    const parentQ = h.parent.getWorldQuaternion(new THREE.Quaternion());
    const f = fingers.clone().normalize(), p = palm.clone().addScaledVector(f, -palm.dot(f)).normalize();
    const basisTo = new THREE.Matrix4().makeBasis(f, p, f.clone().cross(p));
    const lf = ax.along, lp = ax.palm;
    const basisFrom = new THREE.Matrix4().makeBasis(lf, lp, lf.clone().cross(lp));
    const world = new THREE.Quaternion().setFromRotationMatrix(basisTo.multiply(basisFrom.transpose()));
    h.quaternion.slerp(parentQ.invert().multiply(world), w);
  }

  /** Curl side `s`'s fingers by `k` (0 open .. 1 a loose fist); additive about the knuckles. */
  function curl(s, k) {
    if (!(Math.abs(k) > 1e-4)) return;
    for (const f of FINGERS) for (const [seg, amt] of [['01', 0.8], ['02', 1], ['03', 0.6]]) {
      const b = bones[`${f}_${seg}_${s}`];
      if (!b) continue;
      // Each finger bends about its own local X, as the contract hand does (driver-life.js
      // bends them about the figure's right, which is the same axis in a hanging hand).
      b.quaternion.multiply(qa.setFromAxisAngle(new THREE.Vector3(1, 0, 0), local[`curl_${s}`] * k * amt * 60 * DEG));
    }
  }

  // State, kept across a LOD swap.
  let time = rand() * 50;
  let pose = skirt ? 'clasp' : 'rest', poseW = 1, prevPose = pose, poseHold = between(6, 14);
  let greet = -1, greetCool = 0, nodRequest = 0;
  const swing = { l: 0, r: 0 };
  let lastState = null;

  function choosePose() {
    const r = rand();
    prevPose = pose; poseW = 0;
    if (skirt) pose = pose !== 'clasp' && r < 0.65 ? 'clasp' : r < 0.9 ? 'behind' : 'clasp';
    else pose = pose !== 'rest' && r < 0.45 ? 'rest' : r < 0.72 ? 'hips' : r < 0.95 ? 'behind' : 'rest';
    poseHold = pose === 'rest' ? between(8, 20) : between(10, 26);
  }

  /** Where each pose puts the wrists, the elbows' pull and the hands, in figure terms. */
  function poseTargets(name, s) {
    const sx = s === 'l' ? 1 : -1; // +X is the figure's left
    if (skirt && name === 'clasp') {
      // Hands loosely together in front at the waist, over the apron, the right over the left.
      return { wrist: new THREE.Vector3(sx * 0.055, L.waistY - 0.05, L.frontZ + (s === 'r' ? 0.03 : 0.015)), pole: new THREE.Vector3(sx, -0.3, -0.3),
        fingers: new THREE.Vector3(-sx * 0.85, -0.3, 0.2), palm: new THREE.Vector3(0, 0.1, -1), curl: s === 'r' ? 0.3 : 0.45 };
    }
    if (skirt && name === 'behind') {
      return { wrist: new THREE.Vector3(sx * 0.045, L.waistY - 0.01, L.backZ - 0.06), pole: new THREE.Vector3(sx * 0.9, -0.25, -0.4),
        fingers: new THREE.Vector3(-sx, -0.35, -0.1), palm: new THREE.Vector3(0, 0.15, -1), curl: s === 'l' ? 0.55 : 0.25 };
    }
    if (name === 'hips') {
      return { wrist: new THREE.Vector3(sx * (L.hipHalf + 0.095), L.pelvisY + 0.07, -0.005), pole: new THREE.Vector3(sx, -0.1, -0.75),
        fingers: new THREE.Vector3(-sx * 0.15, -0.75, 0.62), palm: new THREE.Vector3(-sx, 0, 0), curl: 0.35 };
    }
    if (name === 'behind') {
      return { wrist: new THREE.Vector3(sx * 0.045, L.pelvisY - 0.04, L.backZ - 0.03), pole: new THREE.Vector3(sx * 0.9, -0.25, -0.4),
        fingers: new THREE.Vector3(-sx, -0.35, -0.1), palm: new THREE.Vector3(0, 0.15, -1), curl: s === 'l' ? 0.55 : 0.25 };
    }
    return null;
  }

  const api = {
    get bound() { return bound; },
    bind,
    get pose() { return pose; },
    /** Change the standing hand pose now (`rest`, `hips` or `behind`). */
    setPose(name) { if (HAND_POSES.includes(name) && (!skirt || SKIRT_POSES.includes(name)) && (skirt || name !== 'clasp') && name !== pose) { prevPose = pose; pose = name; poseW = 0; poseHold = between(10, 26); } return api; },
    /** Touch the brow in greeting now (the right hand), unless one is under way. */
    // A woman in a dress (T-3423) greets with the nod alone: the touch of the brim or
    // forelock is a man's.
    greet() { if (greeting === 'nod') { nodRequest = 1; return api; } if (greet < 0) { greet = 0; nodRequest = 1; } return api; },
    /** One-shot: true once after a greeting starts, for the life layer to nod. */
    takeNod() { const n = nodRequest; nodRequest = 0; return n > 0; },
    apply(dt, { state = 'standing', root: r = null, viewer = null } = {}) {
      if (!bound) return;
      root = r;
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.1) : 0;
      time += dt;
      rebase();
      body.updateWorldMatrix(true, false);
      body.getWorldQuaternion(sceneQ); sceneM.copy(body.matrixWorld);
      const standing = state === 'standing' || state === 'talking';
      const walking = state === 'walking';
      if (state !== lastState) { lastState = state; if (!standing) { pose = 'rest'; poseW = 1; } else if (skirt && pose === 'rest') { prevPose = 'rest'; pose = 'clasp'; poseW = 0; } }

      // The arms hang in by the sides, elbows soft: the base every pose starts from.
      for (const s of SIDES) {
        if (s === hold?.side) continue;
        const sx = s === 'l' ? 1 : -1;
        const inward = toWorldDir(fig.up.clone().multiplyScalar(-1).addScaledVector(fig.left, sx * (skirt ? 0.16 : 0.075))
          .addScaledVector(fig.fwd, 0.04));
        aim(`upperarm_${s}`, inward, 0.85);
        bones[`upperarm_${s}`].updateMatrixWorld(true);
        const forearm = toWorldDir(fig.up.clone().multiply(new THREE.Vector3(0, -1, 0)).addScaledVector(fig.left, sx * (skirt ? 0.12 : 0.03))
          .addScaledVector(fig.fwd, walking ? 0.32 : 0.2));
        aim(`lowerarm_${s}`, forearm, 0.85);
        // The hand hangs relaxed: fingers down and a little forward, palm to the thigh,
        // fingers loosely curled (the clip holds them open and turned out).
        bones[`lowerarm_${s}`].updateMatrixWorld(true);
        orientHand(s, toWorldDir(new THREE.Vector3(0, -1, walking ? 0.25 : 0.12)), toWorldDir(new THREE.Vector3(-sx, 0, -0.25)), 0.8);
        curl(s, 0.32);
      }

      // Walking: each arm swings opposite its own side's leg, as far as the stride is long.
      if (walking) {
        const fL = bones.foot_l.getWorldPosition(new THREE.Vector3()), fR = bones.foot_r.getWorldPosition(new THREE.Vector3());
        const d = fL.sub(fR).dot(toWorldDir(fig.fwd)); // + when the left foot leads (last frame's pose)
        for (const s of SIDES) {
          if (s === hold?.side) { swing[s] = 0; continue; }
          const target = clamp((s === 'l' ? -d : d) * 0.6, -0.3, 0.3); // radians of swing, forward +
          swing[s] += (target - swing[s]) * (1 - Math.exp(-14 * dt));
          const fwdSwing = Math.max(0, swing[s]);
          const up = bones[`upperarm_${s}`];
          up.parent.updateWorldMatrix(true, false);
          const axis = toWorldDir(fig.left).multiplyScalar(-1); // about the figure's right: + swings a hanging arm forward
          const pq = up.parent.getWorldQuaternion(new THREE.Quaternion());
          const wq = pq.clone().multiply(up.quaternion);
          wq.premultiply(new THREE.Quaternion().setFromAxisAngle(axis, swing[s]));
          up.quaternion.copy(pq.invert().multiply(wq));
          up.updateMatrixWorld(true);
          // The elbow bends more as the arm comes forward, and the forearm swings past it.
          const lo = bones[`lowerarm_${s}`];
          const lq = lo.parent.getWorldQuaternion(new THREE.Quaternion());
          const lw = lq.clone().multiply(lo.quaternion).premultiply(new THREE.Quaternion().setFromAxisAngle(axis, fwdSwing * 0.7));
          lo.quaternion.copy(lq.invert().multiply(lw));
        }
      } else { swing.l = 0; swing.r = 0; }

      // Standing: what the hands are doing.
      if (standing) {
        poseHold -= dt;
        if (poseHold <= 0 && greet < 0) choosePose();
        poseW = Math.min(1, poseW + dt / 0.9);
        const wIn = smooth(poseW), wOut = 1 - wIn;
        for (const s of SIDES) {
          if ((greet >= 0 && s === 'r') || s === hold?.side) continue;
          for (const [name, w] of [[prevPose, wOut], [pose, wIn]]) {
            const t = poseTargets(name, s);
            if (!t || !(w > 1e-3)) continue;
            reach(s, toWorldPos(t.wrist), toWorldDir(t.pole), w);
            bones[`lowerarm_${s}`].updateMatrixWorld(true);
            orientHand(s, toWorldDir(t.fingers), toWorldDir(t.palm), w * 0.9);
            curl(s, t.curl * w);
          }
        }
        // A visitor coming up in front is greeted, once in a while.
        greetCool -= dt;
        if (viewer && root && greet < 0 && greetCool <= 0) {
          const v = viewer.clone().sub(root.position).applyAxisAngle(THREE.Object3D.DEFAULT_UP, -root.rotation.y);
          const flat = Math.hypot(v.x, v.z), yaw = Math.atan2(v.x, v.z);
          if (flat < 4.2 && flat > 0.9 && Math.abs(yaw) < 55 * DEG) { api.greet(); greetCool = between(40, 70); }
        }
      }
      // The greeting: the right fingertips up to the brow (a touch of the brim or the
      // forelock), held a beat, and down. The wrist sits a hand's length below and outside
      // the brow, the fingers pointing up and in to it, the palm toward the face.
      if (greet >= 0) {
        greet += dt;
        const T = 1.7, w = greet < 0.5 ? smooth(greet / 0.5) : greet < 1.0 ? 1 : smooth((T - greet) / 0.7);
        // The touch is at the right corner of the brow, beside the eye, so the hand comes
        // up beside the face, never across it: fingers up and forward to the brim, palm in.
        const fingers = new THREE.Vector3(0.22, 0.88, 0.42).normalize();
        const touch = L.brow.clone().add(new THREE.Vector3(-0.072, 0.01, -0.005));
        const wrist = touch.addScaledVector(fingers, -L.handLen * 0.95);
        reach('r', toWorldPos(wrist), toWorldDir(new THREE.Vector3(-0.9, -0.35, 0.25)), w);
        bones.lowerarm_r.updateMatrixWorld(true);
        orientHand('r', toWorldDir(fingers), toWorldDir(new THREE.Vector3(1, 0.1, -0.3)), w);
        curl('r', 0.18 * w);
        // The rest of the right arm comes back from wherever its pose had it.
        if (greet >= T) greet = -1;
      }
      // T-3481: the carrying arm, held out a little from the skirt with what it carries.
      if (hold) {
        const s = hold.side;
        reach(s, toWorldPos(hold.wrist), toWorldDir(hold.pole), 1);
        bones[`lowerarm_${s}`].updateMatrixWorld(true);
        orientHand(s, toWorldDir(hold.fingers), toWorldDir(hold.palm), 1);
        curl(s, hold.curl);
      }
      settle();
    },
    snapshot() {
      return { pose, blend: +poseW.toFixed(3), greeting: greet >= 0, carrying: hold?.side ?? null, swing_l_deg: +(swing.l / DEG).toFixed(2), swing_r_deg: +(swing.r / DEG).toFixed(2) };
    },
  };
  if (scene && !bind(scene)) return null;
  return api;
}
