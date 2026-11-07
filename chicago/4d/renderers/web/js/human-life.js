// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-life.js — the people on foot are alive, not posed (T-3402).
 *
 * A figure standing in a yard or walking a street played its clip and blinked every
 * four seconds on the dot; it never looked at you, never settled onto a hip, and its
 * chest only moved as much as the clip's one-degree breath. Kevin, 2026-11-06, of the
 * figures: "he looks too smooth and not real ... set us on a path for all humans to look
 * photographic realistic". Hans on his box got this kind of layer in driver-life.js
 * (T-1790); this is its counterpart for everyone in humans.js, layered on top of
 * whatever the clip wrote this frame:
 *
 *   - breathing: the chest lifts and the shoulders rise with it, about 14 a minute
 *     standing and quicker on the walk, the head held level against it;
 *   - postural sway: a standing body is never still; a slow drift of the upper spine
 *     that no two people share;
 *   - weight shifts (standing): every few seconds the weight goes onto one leg. The
 *     pelvis tips down to the free side, the loaded leg stays straight and planted, the
 *     free knee softens to meet the lowered hip, and the spine counters so the shoulders
 *     and eyes stay level: the contrapposto of anyone waiting;
 *   - looking around: eyes lead with quick saccades and tiny fixational ones, the head
 *     and neck follow, the torso joins a wide look. Standing, a person looks down the
 *     street, to either side, at the ground, now and then into the distance; walking,
 *     mostly ahead and at the ground in front, with glances aside. A visitor who comes
 *     within a few metres in front is looked at, then let go, then looked at again;
 *   - blinks: an irregular 2-6 s, sometimes a double, and one with a big change of gaze
 *     (people blink as their eyes jump).
 *
 * All of it is additive on each bone's local frame and rebuilt from the clip's pose every
 * frame. Axes are read once, at bind, in the figure's own frame (up; forward, the way
 * the asset faces, +Z; and right, from the left hip to the right). Positive yaw turns to
 * the figure's left, positive pitch lifts the chin, positive roll tips to the right; the
 * same conventions as driver-life.js.
 *
 * `attend(point, seconds)` makes the figure look at a world point for a while: the
 * interaction layer calls it when a visitor comes up to someone.
 *
 * On the walk, with the gait layer (human-gait.js, applied before this one and owning the
 * pelvis and the legs) passed in as `gait`, the trunk walks with it (see TRUNK below): the
 * thorax turns back against the pelvis, the trunk counters the hip's drop and leans a
 * little into the speed, and the head is held steady in the world, so the gaze does not
 * wobble with the steps. Without it (`gait` null) the walk reads the feet as before.
 *
 * Deterministic: the only randomness is a PRNG seeded from the person, so a harness sees
 * the same motion on every load. It is reconstructed animation, not recorded behaviour
 * (liberty L-human-life-3402). No assets, textures or extra draw calls: a few dozen
 * quaternion multiplies a figure a frame, only inside humans.js's animation range.
 */
import * as THREE from 'three';
import { seededRandom } from './driver-life.js';

const DEG = Math.PI / 180;

/** A critically damped spring toward `target`; `omega` is its stiffness (1/s). */
function spring(s, target, omega, dt) {
  if (!(dt > 0)) return s.x;
  const x = s.x - target, e = Math.exp(-omega * dt), temp = (s.v + omega * x) * dt;
  s.v = (s.v - omega * temp) * e;
  s.x = target + (x + temp) * e;
  return s.x;
}
const S = (x = 0) => ({ x, v: 0 });
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

/** The bones this layer moves. A rig missing any CORE bone is left alone (null). */
const CORE = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head', 'clavicle_l', 'clavicle_r'];
const LEGS = ['thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r'];
const OPTIONAL = [...LEGS, 'eye_l', 'eye_r'];

/** What each behaviour state gets. `working` and `seated` keep their clip's body. */
export const LIFE_MODES = Object.freeze({
  standing: { breath: 1, sway: 1, weight: true, gaze: 1, visitor_m: 6 },
  talking: { breath: 1, sway: 1, weight: true, gaze: 0.7, visitor_m: 6 },
  walking: { breath: 1.25, sway: 0, weight: false, gaze: 0.8, visitor_m: 8 },
  working: { breath: 0.8, sway: 0.4, weight: false, gaze: 0.5, visitor_m: 4 },
  seated: { breath: 0.9, sway: 0.5, weight: false, gaze: 0.8, visitor_m: 5 },
});

/**
 * The trunk over the gait layer's pelvis. Walking at 1.2-1.4 m/s the pelvis turns a few
 * degrees each way with the stepping leg and the thorax turns back against it, so the
 * shoulders turn little in the world; the relative phase of the two moves toward
 * antiphase as the speed rises (van Emmerik & Wagenaar 1996; Murray, Drought & Kory 1964
 * measured both rotations in normal men). `counter` is the share of the pelvis's yaw the
 * thorax takes back relative to the pelvis, rising with speed from `min` to `max`
 * (reconstructed numbers inside those findings). The trunk also takes back most of the
 * pelvis's drop to the swing side, and leans forward a little more the faster the walk
 * (reconstructed: 2 deg at 1 m/s to 4 deg at 1.6). The head is stabilised in space, as
 * people's heads are on the walk (Pozzo, Berthoz & Lefort 1990): its yaw and roll take out
 * what the pelvis and thorax leave, and its pitch turns down as the body rises, so the
 * eyes stay on the same point of the way ahead (`fixation_m`, reconstructed).
 */
export const TRUNK = Object.freeze({
  counter: { min: 0.6, max: 1.0, at0: 0.55, perMS: 0.3 }, // k = clamp(at0 + perMS * speed): 0.91 at 1.2 m/s
  roll: 0.7, // share of the pelvis's roll the trunk takes back
  lean: { at1: 2, perMS: 3.3, min: 1.5, max: 4.5 }, // degrees of forward lean, by speed
  fixation_m: 2,
});
const fin = (x, d = 0) => (Number.isFinite(x) ? x : d);

/** One natural blink, 0..1..0 over its duration: a fast close and a slower open. */
function blinkCurve(t, dur = 0.2) {
  if (t < 0 || t >= dur) return 0;
  const close = dur * 0.35;
  return t < close ? Math.sin((t / close) * Math.PI / 2) : Math.cos(((t - close) / (dur - close)) * Math.PI / 2);
}

/**
 * The life of one figure. It outlives a LOD swap: `bind(scene)` attaches it to a new
 * body and keeps where it was looking and how it was standing. Returns null when the
 * first body is not the contract skeleton.
 */
export function createHumanLife({ id = 'human', scene = null } = {}) {
  const rand = seededRandom(`life:${id}`);
  const between = (a, b) => a + (b - a) * rand();

  // Body binding (replaced on a LOD swap).
  let bones = {}, axes = {}, held = {}, headHeight = 1.6, bound = false;
  const qa = new THREE.Quaternion();
  const turn = (name, yaw = 0, pitch = 0, roll = 0) => {
    const b = bones[name], ax = axes[name];
    if (!b) return;
    if (yaw) b.quaternion.multiply(qa.setFromAxisAngle(ax.up, yaw));
    if (pitch) b.quaternion.multiply(qa.setFromAxisAngle(ax.right, pitch));
    if (roll) b.quaternion.multiply(qa.setFromAxisAngle(ax.forward, roll));
  };

  function bind(next) {
    const found = {};
    next.traverse((o) => { if (o.isBone && (CORE.includes(o.name) || OPTIONAL.includes(o.name))) found[o.name] = o; });
    if (!CORE.every((n) => found[n])) { bound = false; return false; }
    next.updateMatrixWorld(true);
    const sceneInv = next.getWorldQuaternion(new THREE.Quaternion()).invert();
    const sceneInvM = next.matrixWorld.clone().invert();
    const at = (name) => found[name].getWorldPosition(new THREE.Vector3()).applyMatrix4(sceneInvM);
    // The figure's frame: up; right from the left hip to the right (or the clavicles);
    // forward = up x right, which is +Z for a contract asset.
    const up = new THREE.Vector3(0, 1, 0);
    const right = (found.thigh_l && found.thigh_r ? at('thigh_r').sub(at('thigh_l')) : at('clavicle_r').sub(at('clavicle_l')))
      .projectOnPlane(up);
    if (!(right.lengthSq() > 1e-6)) right.set(-1, 0, 0);
    right.normalize();
    const forward = up.clone().cross(right).normalize();
    axes = {};
    for (const [name, bone] of Object.entries(found)) {
      const q = sceneInv.clone().multiply(bone.getWorldQuaternion(new THREE.Quaternion())).invert();
      axes[name] = { up: up.clone().applyQuaternion(q), forward: forward.clone().applyQuaternion(q), right: right.clone().applyQuaternion(q) };
    }
    headHeight = at('head').y;
    // three's PropertyMixer writes a track only when its value changed, so a held
    // channel is not rewritten each frame: a bone still carrying last frame's output was
    // not touched by the clip and goes back to its base before this frame's layer.
    held = Object.fromEntries(Object.entries(found).map(([n, b]) =>
      [n, { base: b.quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) }]));
    const pelvis = found.pelvis;
    held.__pelvisPos = { base: pelvis.position.clone(), out: new THREE.Vector3(NaN, NaN, NaN) };
    // How far the pelvis must drop so the loaded leg stays on the ground as it tips.
    const hips = found.thigh_l && found.thigh_r ? at('thigh_r').sub(at('thigh_l')).length() / 2 : 0.1;
    hipHalf = hips;
    const toParent = sceneInv.clone().multiply(pelvis.parent.getWorldQuaternion(new THREE.Quaternion())).invert();
    pelvisUpLocal = up.clone().applyQuaternion(toParent);
    pelvisRightLocal = right.clone().applyQuaternion(toParent);
    legLen = found.thigh_l && found.foot_l ? at('thigh_l').distanceTo(at('foot_l')) : 0.86;
    pelvisUpScale = 1 / pelvis.parent.getWorldScale(new THREE.Vector3()).y;
    bones = found;
    bound = true;
    return true;
  }
  let hipHalf = 0.1, legLen = 0.86, pelvisUpScale = 1;
  let pelvisUpLocal = new THREE.Vector3(0, 1, 0), pelvisRightLocal = new THREE.Vector3(-1, 0, 0);

  const rebase = () => {
    for (const [n, h] of Object.entries(held)) {
      if (n === '__pelvisPos') continue;
      const q = bones[n].quaternion;
      if (q.equals(h.out)) q.copy(h.base); else h.base.copy(q);
    }
    const hp = held.__pelvisPos, p = bones.pelvis.position;
    if (p.equals(hp.out)) p.copy(hp.base); else hp.base.copy(p);
  };
  const settle = () => {
    for (const [n, h] of Object.entries(held)) {
      if (n === '__pelvisPos') h.out.copy(bones.pelvis.position); else h.out.copy(bones[n].quaternion);
    }
  };

  // State that survives a LOD swap.
  let time = rand() * 100;
  const breathRate = between(0.21, 0.26); // breaths a second standing, about 13-16 a minute
  const swayPhase = [rand() * 6.28, rand() * 6.28, rand() * 6.28];
  const gaze = { yaw: S(), pitch: S(), eyeYaw: S(), eyePitch: S(), torso: S() };
  let gazeTarget = { yaw: 0, pitch: -4 * DEG }, gazeHold = between(0.5, 2), gazeKind = 'ahead';
  let micro = { yaw: 0, pitch: 0 }, microNext = between(0.3, 0.9);
  let lookedAtVisitor = 0; // seconds since the visitor was last looked at
  let attention = null; // { point: Vector3, left: seconds }
  const weight = { side: S(), soft: S(), yaw: S() };
  let weightTarget = { side: between(-1, 1), yaw: between(-2, 2) * DEG }, weightHold = between(2, 6);
  let blinkNext = between(1, 4), blinkT = -1, blinkDur = 0.2, lastBlinkYaw = 0;
  let nodT = -1; // a small nod of greeting (T-3415), seconds into it
  const walkTwist = S();
  const walkLean = S(); // the trunk's forward lean on the walk, radians
  const vf = new THREE.Vector3();
  const v = new THREE.Vector3();

  const pickGaze = (mode, walking, seen) => {
    // A visitor close in front: looked at, but not stared at for ever.
    if (seen && seen.dist < mode.visitor_m && Math.abs(seen.yaw) < (walking ? 70 : 100) * DEG
        && rand() < (lookedAtVisitor > 6 ? 0.85 : 0.55)) {
      gazeKind = 'visitor'; gazeHold = between(1.6, 4.2); lookedAtVisitor = 0; return;
    }
    const r = rand(), g = mode.gaze;
    if (walking) {
      if (r < 0.5) { gazeKind = 'ahead'; gazeTarget = { yaw: between(-5, 5) * DEG, pitch: between(-14, -4) * DEG }; gazeHold = between(1.5, 4); }
      else if (r < 0.75) { gazeKind = 'ground'; gazeTarget = { yaw: between(-8, 8) * DEG, pitch: between(-26, -16) * DEG }; gazeHold = between(0.5, 1.2); }
      else { gazeKind = 'aside'; const s = rand() < 0.5 ? -1 : 1; gazeTarget = { yaw: s * between(18, 50) * g * DEG, pitch: between(-6, 6) * DEG }; gazeHold = between(0.6, 1.6); }
      return;
    }
    if (r < 0.32) { gazeKind = 'ahead'; gazeTarget = { yaw: between(-10, 10) * DEG, pitch: between(-5, 2) * DEG }; gazeHold = between(2, 5); }
    else if (r < 0.66) { gazeKind = 'aside'; const s = rand() < 0.5 ? -1 : 1; gazeTarget = { yaw: s * between(20, 65) * g * DEG, pitch: between(-6, 5) * DEG }; gazeHold = between(1, 3.2); }
    else if (r < 0.84) { gazeKind = 'ground'; gazeTarget = { yaw: between(-20, 20) * g * DEG, pitch: between(-24, -12) * DEG }; gazeHold = between(0.8, 2.2); }
    else { gazeKind = 'far'; const s = rand() < 0.5 ? -1 : 1; gazeTarget = { yaw: s * between(5, 35) * g * DEG, pitch: between(2, 9) * DEG }; gazeHold = between(1.5, 3.5); }
  };

  const life = {
    get bound() { return bound; },
    get bones() { return Object.keys(bones); },
    bind,
    /** A small nod, as with a greeting (human-actions.js asks for it). */
    nod() { if (nodT < 0) nodT = 0; return life; },
    /** Look at `point` (a world Vector3) for `seconds`; null lets go. */
    attend(point, seconds = 3) {
      attention = point ? { point: point.clone(), left: Math.max(0, seconds) } : null;
      if (attention) gazeHold = 0;
      return life;
    },
    /**
     * One frame on top of the clip's pose. `dt` is the seconds the clip advanced (0 holds
     * the pose); `state` the actor's behaviour state; `root` its root (position and
     * heading); `viewer` the visitor's eye in world space, or null; `gait` the gait
     * layer's state this frame (phase, weight, speed, pelvisYaw, pelvisRoll, bob), or null.
     */
    apply(dt, { state = 'standing', root = null, viewer = null, gait = null } = {}) {
      if (!bound) return;
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.1) : 0;
      const mode = LIFE_MODES[state] ?? LIFE_MODES.standing;
      const walking = state === 'walking';
      // The gait layer's share now (0 with none, and standing), and the pelvis it set. Its
      // yaw, roll and bob are taken at that share, so a gait at weight 0 changes nothing
      // whether or not it reports them faded.
      const gw = gait ? clamp(fin(gait.weight), 0, 1) : 0;
      const pYaw = gait ? fin(gait.pelvisYaw) * gw : 0, pRoll = gait ? fin(gait.pelvisRoll) * gw : 0, bob = gait ? fin(gait.bob) * gw : 0;
      const speed = gait ? fin(gait.speed, 1.25) : 0;
      time += dt;
      lookedAtVisitor += dt;
      rebase();

      // Where the visitor (or the thing attended to) is, in the figure's frame: the root
      // turns only about up, so undo its yaw instead of inverting a matrix.
      const toFigure = (p) => {
        if (!root || !p) return null;
        v.copy(p).sub(root.position).applyAxisAngle(THREE.Object3D.DEFAULT_UP, -root.rotation.y);
        v.y -= headHeight;
        const dist = v.length();
        return { dist, yaw: Math.atan2(v.x, v.z), pitch: Math.atan2(v.y, Math.hypot(v.x, v.z)) };
      };
      const seen = toFigure(viewer);
      if (attention) { attention.left -= dt; if (attention.left <= 0) { attention = null; gazeHold = 0; } }
      const attended = attention ? toFigure(attention.point) : null;

      // Gaze: a hold, then somewhere new to look.
      gazeHold -= dt;
      if (gazeHold <= 0 && !attended) pickGaze(mode, walking, seen);
      let target = gazeTarget;
      const follow = attended ?? (gazeKind === 'visitor' ? seen : null);
      if (follow) {
        if (Math.abs(follow.yaw) > 130 * DEG) { if (!attended) gazeHold = 0; }
        else target = { yaw: clamp(follow.yaw, -85 * DEG, 85 * DEG), pitch: clamp(follow.pitch, -30 * DEG, 25 * DEG) };
      } else if (gazeKind === 'visitor') gazeHold = 0;
      // Fixational micro-saccades: the eyes never rest exactly still.
      microNext -= dt;
      if (microNext <= 0) { micro = { yaw: between(-0.7, 0.7) * DEG, pitch: between(-0.5, 0.5) * DEG }; microNext = between(0.25, 0.9); }
      const ty = target.yaw, tp = target.pitch;
      const eyeYaw = spring(gaze.eyeYaw, ty + micro.yaw, 30, dt), eyePitch = spring(gaze.eyePitch, tp + micro.pitch, 30, dt);
      const headYaw = spring(gaze.yaw, ty, walking ? 5 : 4.2, dt), headPitch = spring(gaze.pitch, tp, walking ? 5 : 4.2, dt);
      const wide = walking ? 45 : 30;
      const torso = spring(gaze.torso, Math.abs(ty) > wide * DEG ? (ty - Math.sign(ty) * wide * DEG) * 0.5 : 0, 2.4, dt);

      // Weight shifts: onto one leg, then the other, then square, every few seconds.
      if (mode.weight) {
        weightHold -= dt;
        if (weightHold <= 0) {
          const r = rand();
          weightTarget = { side: r < 0.2 ? between(-0.25, 0.25) : (weight.side.x > 0 ? -1 : 1) * between(0.55, 1), yaw: between(-2.5, 2.5) * DEG };
          weightHold = between(4, 11);
        }
      }
      // The gait layer owns the pelvis and the legs while it drives: what is left of a
      // weight shift (its springs settle over a second after the walk starts) yields to it.
      const own = 1 - gw;
      const side = spring(weight.side, mode.weight ? weightTarget.side : 0, 1.3, dt) * own; // +1: weight on the RIGHT leg
      const wYaw = spring(weight.yaw, mode.weight ? weightTarget.yaw : 0, 1.1, dt) * own;

      // Breathing and sway.
      const rate = breathRate * mode.breath;
      const ph = time * 2 * Math.PI * rate;
      const breath = Math.sin(ph) + 0.18 * Math.sin(2 * ph + 0.6); // a quicker in, a longer out
      const sw = mode.sway;
      const swayRoll = sw * (0.35 * Math.sin(time * 0.37 + swayPhase[0]) + 0.2 * Math.sin(time * 0.71 + swayPhase[1])) * DEG;
      const swayPitch = sw * (0.3 * Math.sin(time * 0.29 + swayPhase[2]) + 0.15 * Math.sin(time * 0.83 + swayPhase[0])) * DEG;

      // The hips: carried a few centimetres over the loaded foot and tipped down to the
      // free side (weight right: right hip up, a negative roll). The legs are children of
      // the pelvis, so each thigh takes the roll back out and leans to keep its foot where
      // it was, and the pelvis drops by what the loaded hip rose: that leg stays planted.
      const tip = -side * 3 * DEG;
      const shift = side * 0.03, lean = Math.asin(clamp(shift / legLen, -0.2, 0.2));
      turn('pelvis', wYaw, 0, tip);
      if (bones.thigh_l && bones.thigh_r) {
        const p = bones.pelvis.position, rise = hipHalf * Math.abs(Math.sin(tip)) + legLen * (1 - Math.cos(lean));
        p.addScaledVector(pelvisUpLocal, -rise * pelvisUpScale).addScaledVector(pelvisRightLocal, shift * pelvisUpScale);
        // The free knee softens to meet its lowered hip, which drops twice the tip's rise.
        const drop = 2 * hipHalf * Math.abs(Math.sin(tip));
        // Knee forward k, shin back 2k, foot flat again: the leg shortens by about
        // legLen (1 - cos k). Positive pitch swings a hanging bone's lower end forward.
        const bend = Math.acos(clamp(1 - drop / legLen, 0, 1));
        for (const s of ['l', 'r']) {
          const free = s === 'l' ? side > 0 : side < 0;
          const k = free ? bend : 0;
          // A positive roll swings a hanging bone's lower end to the figure's left.
          turn(`thigh_${s}`, -wYaw, k, -tip + lean);
          if (k) turn(`calf_${s}`, 0, -2 * k, 0);
          turn(`foot_${s}`, 0, k, -lean);
        }
      }
      // Walking, the shoulders turn against the hips (T-3415): the chest follows the arm
      // that swings forward, which goes with the opposite leg. Read from where the feet
      // were last frame, so it follows any walk clip's stride and stops when they stop.
      let twistTarget = 0;
      if (walking && bones.foot_l && bones.foot_r && root) {
        const d = bones.foot_l.getWorldPosition(v).sub(bones.foot_r.getWorldPosition(vf))
          .dot(vf.set(0, 0, 1).applyAxisAngle(THREE.Object3D.DEFAULT_UP, root.rotation.y));
        twistTarget = clamp(d * 0.2, -0.09, 0.09); // about 4 deg at a 0.36 m lead
      }
      let twist = spring(walkTwist, twistTarget, 12, dt);
      // With the gait layer (TRUNK above), the thorax turns back by its share of the
      // pelvis's turn, from the phase (no lag); the feet's reading fades out as it fades in.
      // The trunk takes back most of the hip's roll, and leans into the speed.
      // (The lean eases, so a gait that goes away lets it go without a jerk.)
      let rollBack = 0;
      if (gait) {
        const c = TRUNK.counter, k = clamp(c.at0 + c.perMS * speed, c.min, c.max);
        twist = twist * own - k * pYaw;
        rollBack = -TRUNK.roll * pRoll;
      }
      const l = TRUNK.lean;
      const trunkLean = spring(walkLean, gw * clamp(l.at1 + l.perMS * (speed - 1), l.min, l.max) * DEG, 3, dt);
      // The spine counters the hips so the shoulders sit level; the chest breathes. The
      // walk's lean is a forward (negative) pitch, mostly low in the back.
      turn('spine_01', -wYaw * 0.4, swayPitch * 0.4 - trunkLean * 0.45, -tip * 0.45 + swayRoll * 0.3 + rollBack * 0.45);
      turn('spine_02', torso * 0.35 + twist * 0.4, breath * 0.9 * DEG * mode.breath + swayPitch * 0.4 - trunkLean * 0.35, -tip * 0.35 + swayRoll * 0.4 + rollBack * 0.35);
      turn('spine_03', torso * 0.65 - wYaw * 0.3 + twist * 0.6, breath * 0.55 * DEG + swayPitch * 0.2 - trunkLean * 0.2, -tip * 0.2 + swayRoll * 0.3 + rollBack * 0.2);
      let nod = 0;
      if (nodT >= 0) { nodT += dt; nod = nodT < 0.9 ? Math.sin(nodT / 0.9 * Math.PI) * 9 * DEG : 0; if (nodT >= 0.9) nodT = -1; }
      // The head is held level against the chest's breath, the hips and the sway. On the
      // gait layer's walk it is held steady in the world: it takes out the pelvis's turn and
      // roll that the thorax left, the trunk's lean, and pitches down as the body rises so
      // the eyes keep the same point of the way ahead (all 0 with no gait).
      const steadyRoll = -swayRoll * 0.6 - (pRoll + rollBack);
      const steadyPitch = -(breath * 1.1 * DEG + swayPitch) + trunkLean - Math.atan2(bob, TRUNK.fixation_m);
      const headTurn = headYaw - torso - twist - pYaw;
      turn('neck_01', headTurn * 0.4, headPitch * 0.35 + steadyPitch * 0.5 - nod * 0.4, steadyRoll * 0.5);
      turn('head', headTurn * 0.6, headPitch * 0.65 + steadyPitch * 0.5 - nod * 0.6, steadyRoll * 0.5 + headTurn * -0.05);
      // The eyes make what is left of the turn.
      const ey = clamp(eyeYaw - headYaw, -28 * DEG, 28 * DEG), ep = clamp(eyePitch - headPitch, -18 * DEG, 18 * DEG);
      turn('eye_l', ey, ep); turn('eye_r', ey, ep);
      // The shoulders lift with each breath.
      turn('clavicle_l', 0, 0, -breath * 0.8 * DEG * mode.breath);
      turn('clavicle_r', 0, 0, breath * 0.8 * DEG * mode.breath);

      // Blinks: irregular, sometimes doubled, and one when the gaze jumps.
      blinkNext -= dt;
      const jump = Math.abs(ty - lastBlinkYaw) > 25 * DEG;
      if (blinkT < 0 && (blinkNext <= 0 || (jump && rand() < 0.6))) {
        blinkT = 0; blinkDur = between(0.16, 0.26);
        blinkNext = rand() < 0.12 ? 0.3 : between(2, 6);
        lastBlinkYaw = ty;
      } else if (jump) lastBlinkYaw = ty;
      if (blinkT >= 0) { blinkT += dt; if (blinkT >= blinkDur) blinkT = -1; }
      settle();
    },
    /** The eyelids now, 0 open .. 1 shut, for humans.js to write into the face. */
    get blink() { return blinkT >= 0 ? blinkCurve(blinkT, blinkDur) : 0; },
    snapshot() {
      return {
        gaze: gazeKind, attending: !!attention, yaw_deg: +(gaze.yaw.x / DEG).toFixed(2), pitch_deg: +(gaze.pitch.x / DEG).toFixed(2),
        weight: +weight.side.x.toFixed(3), blink: +life.blink.toFixed(3),
      };
    },
  };
  if (scene && !bind(scene)) return null;
  return life;
}
