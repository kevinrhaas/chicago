// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * rider-pose.js — a portable human seated in a saddle (T-3560).
 *
 * No figure carries a riding clip, so the rider is posed each frame from the figure's own
 * standing pose by two-bone reaching on the contract skeleton (the 56 bones every portable
 * human shares): the pelvis set on the saddle's seat, each leg reaching from the hip to its
 * stirrup iron with the knee forward and out round the horse's barrel, the heel down and the
 * toe a little out; each arm reaching from the shoulder to its rein hand with the elbow at the
 * side; the back a little forward of upright, more at the trot. Everything is rewritten from
 * the stored standing pose every frame, so nothing accumulates (three's mixer does not rewrite
 * a bone whose track never changes; driver-life.js and cab-passenger.js have the same rule).
 *
 * Targets are in the WORLD frame; the figure's root may hang anywhere (riding.js hangs it on
 * the horse's trunk bone, so the rider rises and falls with the horse's back).
 */
import * as THREE from 'three';

const NEED = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r',
  'foot_l', 'foot_r', 'upperarm_l', 'upperarm_r', 'lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'];

const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3(), _d = new THREE.Vector3();
const _q = new THREE.Quaternion(), _p = new THREE.Quaternion();
const wp = (bone, out = new THREE.Vector3()) => bone.getWorldPosition(out);

/** Turn `bone` in the world so that the direction `from` becomes `to` (both world vectors). */
function turnToward(bone, from, to) {
  if (from.lengthSq() < 1e-12 || to.lengthSq() < 1e-12) return;
  _q.setFromUnitVectors(from.clone().normalize(), to.clone().normalize());
  bone.parent.getWorldQuaternion(_p);
  const local = _p.clone().invert().multiply(_q).multiply(_p);
  bone.quaternion.premultiply(local);
  bone.updateMatrixWorld(true);
}

/**
 * Two links a -> b -> c reaching c to `target`, the middle joint bent toward `pole` (a world
 * direction). Returns how far short the reach fell (0 when it got there).
 */
export function reach(a, b, c, target, pole) {
  const pa = wp(a, _a), pb = wp(b, _b).clone(), pc = wp(c, _c).clone();
  const l1 = pa.distanceTo(pb), l2 = pb.distanceTo(pc);
  const to = target.clone().sub(pa), far = to.length();
  const d = THREE.MathUtils.clamp(far, Math.abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4);
  const dir = to.normalize();
  const cosA = THREE.MathUtils.clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1), sinA = Math.sqrt(1 - cosA * cosA);
  const perp = pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir)));
  if (perp.lengthSq() < 1e-10) perp.set(0, 1, 0).sub(dir.clone().multiplyScalar(dir.y));
  perp.normalize();
  const joint = pa.clone().addScaledVector(dir, cosA * l1).addScaledVector(perp, sinA * l1);
  turnToward(a, pb.clone().sub(pa), joint.clone().sub(pa));
  const nb = wp(b, _b).clone(), nc = wp(c, _c).clone();
  turnToward(b, nc.clone().sub(nb), target.clone().sub(nb));
  return Math.max(0, far - (l1 + l2));
}

/**
 * Bind to a figure (`scene` holds its bones, `root` is its root) standing in its first pose.
 * Returns null on a rig that is not the contract skeleton.
 */
export function createRiderPose(scene, root) {
  const bones = {};
  scene.traverse(o => { if (o.isBone && NEED.includes(o.name)) bones[o.name] = o; });
  if (!NEED.every(n => bones[n])) return null;
  scene.traverse(o => { if (o.isBone && !bones[o.name]) bones[o.name] = o; });
  root.updateMatrixWorld(true);
  const base = new Map(Object.values(bones).map(b => [b, b.quaternion.clone()]));
  const basePos = root.position.clone();
  // The figure's own frame: forward from heel to toe, up from pelvis to head, left = up x forward.
  const rootQ = root.getWorldQuaternion(new THREE.Quaternion()), rootInvQ = rootQ.clone().invert();
  const local = v => v.clone().applyQuaternion(rootInvQ);
  const toe = bones.ball_l ?? null;
  const fwdLocal = local(toe ? wp(toe).sub(wp(bones.foot_l)) : new THREE.Vector3(0, 0, 1)).setY(0).normalize();
  const upLocal = new THREE.Vector3(0, 1, 0);
  const leftLocal = new THREE.Vector3().crossVectors(upLocal, fwdLocal).normalize();
  const legLength = wp(bones.thigh_l).distanceTo(wp(bones.calf_l)) + wp(bones.calf_l).distanceTo(wp(bones.foot_l));
  const pelvisHeight = local(wp(bones.pelvis).sub(root.getWorldPosition(new THREE.Vector3()))).y;
  return {
    bones, legLength, pelvisHeight,
    /** The figure's forward, up and left (+x of a horse's near side) in its root's local frame. */
    axes: { forward: fwdLocal, up: upLocal, left: leftLocal },
    /**
     * Pose for this frame. `seat` = where the pelvis sits (world); `feet` / `hands` = { l, r }
     * world targets for the ankles and the palms; `forward` / `up` = the horse's world axes;
     * `lean` = radians forward of upright; `look` = radians the head turns (left +); `sway` =
     * radians the back rolls toward the left with the horse's stride; `nod` = radians the head
     * drops (riding.js riderLife).
     */
    apply({ seat, feet, hands, forward, up, lean = .08, look = 0, sway = 0, nod = 0, knee = { forward: .6, out: 1.2 }, thighRoll = 0 }) {
      for (const [b, q] of base) b.quaternion.copy(q);
      root.position.copy(basePos);
      root.updateMatrixWorld(true);
      // The seat: move the root so the pelvis is on it.
      const off = seat.clone().sub(wp(bones.pelvis));
      const parentInv = root.parent ? root.parent.matrixWorld.clone().invert() : new THREE.Matrix4();
      const rootWorld = root.getWorldPosition(new THREE.Vector3()).add(off);
      root.position.copy(rootWorld.applyMatrix4(parentInv));
      root.updateMatrixWorld(true);
      const side = new THREE.Vector3().crossVectors(up, forward).normalize(); // the horse's left
      // The back a little forward; the neck and head keep the eyes level.
      const tip = (bone, a) => {
        bone.parent.getWorldQuaternion(_p);
        _q.setFromAxisAngle(side, a);
        bone.quaternion.premultiply(_p.clone().invert().multiply(_q).multiply(_p));
        bone.updateMatrixWorld(true);
      };
      tip(bones.spine_01, lean * .5); tip(bones.spine_02, lean * .5);
      tip(bones.neck_01, -lean * .5); tip(bones.head, -lean * .5 + nod);
      if (sway) {
        // The back rolls with the stride from the waist up; the neck takes most of it back.
        const roll = (bone, a) => { bone.parent.getWorldQuaternion(_p); _q.setFromAxisAngle(forward, a); bone.quaternion.premultiply(_p.clone().invert().multiply(_q).multiply(_p)); bone.updateMatrixWorld(true); };
        roll(bones.spine_01, sway * .5); roll(bones.spine_02, sway * .5); roll(bones.neck_01, -sway * .7);
      }
      if (look) { bones.head.parent.getWorldQuaternion(_p); _q.setFromAxisAngle(up, look); bones.head.quaternion.premultiply(_p.clone().invert().multiply(_q).multiply(_p)); bones.head.updateMatrixWorld(true); }
      const short = {};
      for (const [s, sign] of [['l', 1], ['r', -1]]) {
        // Knee forward and out, round the barrel; then the heel down, toe a little out.
        const pole = forward.clone().multiplyScalar(knee.forward).addScaledVector(side, sign * knee.out).addScaledVector(up, -.1);
        short[`leg_${s}`] = reach(bones[`thigh_${s}`], bones[`calf_${s}`], bones[`foot_${s}`], feet[s], pole);
        // T-3644: the thigh rolled in about its own line, its flat laid to the saddle (a rider is
        // taught to turn the thigh in from the hip): a wide-hipped figure's inner thigh otherwise
        // stands in the barrel. The knee stays where it is; the shin is laid back on the iron.
        if (thighRoll) {
          const th = bones[`thigh_${s}`], ca = bones[`calf_${s}`], ft = bones[`foot_${s}`];
          const axis = wp(ca).sub(wp(th)).normalize();
          th.parent.getWorldQuaternion(_p);
          _q.setFromAxisAngle(axis, sign * thighRoll);
          th.quaternion.premultiply(_p.clone().invert().multiply(_q).multiply(_p));
          th.updateMatrixWorld(true);
          const knee = wp(ca).clone();
          turnToward(ca, wp(ft).clone().sub(knee), feet[s].clone().sub(knee));
        }
        const foot = bones[`foot_${s}`], ball = bones[`ball_${s}`];
        if (ball) {
          const want = forward.clone().addScaledVector(side, sign * .25).addScaledVector(up, .12).normalize();
          turnToward(foot, wp(ball).sub(wp(foot)), want);
        }
        // Elbow back at the side and a little out; the hand to the rein.
        const elbow = forward.clone().multiplyScalar(-1).addScaledVector(up, -.6).addScaledVector(side, sign * .35);
        short[`arm_${s}`] = reach(bones[`upperarm_${s}`], bones[`lowerarm_${s}`], bones[`hand_${s}`], hands[s], elbow);
      }
      return short;
    },
    /** Back to the figure's own standing pose. */
    release() { for (const [b, q] of base) b.quaternion.copy(q); root.position.copy(basePos); root.updateMatrixWorld(true); },
  };
}

/**
 * Where a rider's seat, irons and hands are on a fitted saddle (saddlery.js `fitTack`), as the
 * horse's trunk now rides. `fit` = saddle_horses.json `fit` (metres in the horse root's frame,
 * +z ahead, +x the near side). `world(root)` gives `apply`'s targets; `rootFrame(root, pose)`
 * gives the tack's `update` its irons and the solved hands, so the reins end in the hands.
 */
export function saddleTargets(tack, fit, { lean = fit.lean_walk_rad ?? .08, rise = 0, give = 0 } = {}) {
  const seat = tack.seat().add(new THREE.Vector3(0, fit.seat_above_m, fit.seat_back_m));
  const iron = side => tack.stirrupBar(side).add(new THREE.Vector3(side * fit.iron_out_m, -fit.leather_m, fit.iron_back_m));
  const ankle = side => iron(side).add(new THREE.Vector3(side * fit.ankle_out_m, fit.ankle_above_iron_m, -fit.ankle_behind_iron_m));
  // `rise`: the seat lifted out of the saddle (a rising trot); `give`: the hands carried forward
  // with the horse's head as it nods (riding.js riderLife). Both 0 is the fitted seat.
  const hand = side => seat.clone().add(new THREE.Vector3(side * fit.hands_apart_m / 2, fit.hands_above_m + rise * .5, fit.hands_ahead_m + give));
  const W = (root, v) => root.localToWorld(v.clone());
  return {
    seat, iron, hand, lean,
    world(root) {
      root.updateMatrixWorld(true);
      const q = root.getWorldQuaternion(new THREE.Quaternion());
      return { seat: W(root, seat.clone().add(new THREE.Vector3(0, rise, 0))), feet: { l: W(root, ankle(1)), r: W(root, ankle(-1)) }, hands: { l: W(root, hand(1)), r: W(root, hand(-1)) },
        forward: new THREE.Vector3(0, 0, 1).applyQuaternion(q), up: new THREE.Vector3(0, 1, 0).applyQuaternion(q), lean };
    },
    rootFrame(root, pose) {
      const grip = s => pose.bones[`middle_01_${s}`] ?? pose.bones[`hand_${s}`];
      const local = b => root.worldToLocal(b.getWorldPosition(new THREE.Vector3()));
      return { feet: { 1: iron(1), [-1]: iron(-1) }, hands: { 1: local(grip('l')), [-1]: local(grip('r')) } };
    },
  };
}
