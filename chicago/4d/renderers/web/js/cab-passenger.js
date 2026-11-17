// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3557: a person riding INSIDE the brougham's cab (Mr. Glessner, from his own 1904 record
 * and figure), seated beside the visitor.
 *
 * No portable figure carries a passenger's clip. The coachmen's seated clip
 * (`sit_drive_look_v2`, on the anonymous working driver's export) is played on his own
 * body: both are the contract skeleton (the same 56 bones), and the clip is a vehicle-local
 * articulated pose for the box seat. The cab is lower than the box is open: its cushion is
 * 0.75 m under the roof lining (brougham-near.glb, measured: cushion top 1.296 m, lining
 * 2.046 m above the wheels' ground at the seat; 0.373 m above the floor), less than a man
 * sitting upright (the clip's head top is 0.95 m over the cushion). So the clip is moved
 * onto the cab's seat (`root_local_m`) and bent there, each bend a world rotation about the
 * vehicle's lateral axis measured once on the clip's first pose and applied as a local
 * delta: thighs raised for the low seat, shins brought back to the floor, the back bent
 * forward from the lower spine, the neck and head lifted again to look ahead. Then each hand
 * is laid on its own thigh (`lap`: the arm turned to reach it, the hand palm down, fingers
 * toward the knee), each frame, so it stays there as he breathes. The hat is off indoors. tools/test_glessner_ride.mjs measures
 * the bent figure against the cab's own surfaces (roof, floor, walls).
 *
 * Bones whose clip tracks never change are not rewritten by three's mixer, so each frame the
 * bent bones are first put back to the clip's pose (`restore()`, before the mixer runs), then
 * bent again (`apply()`, after it): never a bend on the bend written the frame before, nor on
 * what a life layer added after it (driver-life.js has the same trap).
 */
import * as THREE from 'three';

const AXES = Object.freeze({ x: new THREE.Vector3(1, 0, 0), y: new THREE.Vector3(0, 1, 0), z: new THREE.Vector3(0, 0, 1) });
const DEG = Math.PI / 180;

/** The default bends (degrees about the vehicle's lateral axis unless a third entry names 'y' or 'z'; + tips a forward-pointing limb down). */
export const CAB_SEAT_POSE = Object.freeze({
  bends: Object.freeze([
    ['thigh_l', -44], ['thigh_r', -44],
    ['calf_l', 30], ['calf_r', 30],
    ['spine_01', 20], ['spine_02', 20],
    ['neck_01', -14], ['head', -14],
    ['upperarm_l', 5], ['upperarm_r', 5],
  ]),
  hide: '(headwear|hat)',
  // Kevin, 2026-11-17: "he also sits oddly with his arms under him". The coachman's clip holds
  // the reins forward, so bent to the low seat his hands hung down by his shins. Each hand is
  // laid on its own thigh instead (`lap`): the wrist over the thigh `along` the way from hip
  // to knee, `lift` above the thigh bone (the thigh's top and the wrist's own half-thickness)
  // and `inset` toward his middle, the elbow falling back and out (`pole`).
  lap: Object.freeze({ along: .72, lift: .085, inset: .02, turn_in: .15, pole: Object.freeze([1, -.6, -.4]) }),
});

const V = () => new THREE.Vector3();
/**
 * One arm's wrist onto `target` (world), by turning the upper arm and then the forearm in the
 * plane the elbow's `pole` (world direction) chooses. Lengths are the bones' own.
 */
function reach(upper, lower, hand, target, pole) {
  upper.updateWorldMatrix(true, true);
  const S = upper.getWorldPosition(V()), E = lower.getWorldPosition(V()), H = hand.getWorldPosition(V());
  const a = S.distanceTo(E), b = E.distanceTo(H);
  const toT = target.clone().sub(S), d = Math.min(Math.max(toT.length(), Math.abs(a - b) + 1e-4), a + b - 1e-4);
  const u = toT.normalize(), v = pole.clone().addScaledVector(u, -pole.dot(u));
  if (v.lengthSq() < 1e-10) return;
  v.normalize();
  const cos = Math.min(1, Math.max(-1, (a * a + d * d - b * b) / (2 * a * d)));
  const E2 = S.clone().addScaledVector(u, a * cos).addScaledVector(v, a * Math.sqrt(1 - cos * cos));
  const H2 = S.clone().addScaledVector(u, d);
  turn(upper, E.clone().sub(S).normalize(), E2.clone().sub(S).normalize());
  upper.updateWorldMatrix(false, true);
  const E1 = lower.getWorldPosition(V());
  turn(lower, hand.getWorldPosition(V()).sub(E1).normalize(), H2.sub(E1).normalize());
  lower.updateWorldMatrix(false, true);
}
/**
 * Lay a hand flat: its fingers (wrist to the middle knuckle) along `along`, the knuckles' line
 * (little finger to forefinger) toward `inward`, so the palm faces down onto the thigh.
 */
function layHand(hand, middle, index, pinky, along, inward) {
  hand.updateWorldMatrix(true, true);
  const basis = (f, s) => { f = f.clone().normalize(); s = s.clone().addScaledVector(f, -s.dot(f)).normalize();
    return new THREE.Matrix4().makeBasis(f, s, f.clone().cross(s)); };
  const from = basis(middle.getWorldPosition(V()).sub(hand.getWorldPosition(V())), index.getWorldPosition(V()).sub(pinky.getWorldPosition(V())));
  const to = basis(along, inward);
  const r = new THREE.Quaternion().setFromRotationMatrix(to.multiply(from.transpose()));
  const w = hand.getWorldQuaternion(new THREE.Quaternion());
  hand.quaternion.multiply(w.clone().invert().multiply(r).multiply(w));
  hand.updateWorldMatrix(false, true);
}
/** Turn `bone` so its world direction `from` points along `to`. */
function turn(bone, from, to) {
  const w = bone.getWorldQuaternion(new THREE.Quaternion());
  const r = new THREE.Quaternion().setFromUnitVectors(from, to);
  bone.quaternion.multiply(w.clone().invert().multiply(r).multiply(w));
}

/**
 * Bend a seated body (`scene`, its clip already applied at its first pose) per `pose`.
 * `frame` is the object whose axes are the vehicle's (the figure's root). Returns
 * { restore(), apply(), bones, hidden } — restore() before each mixer update, apply() after it
 * and before any life layer.
 */
export function seatInCab(scene, { bends = CAB_SEAT_POSE.bends, hide = CAB_SEAT_POSE.hide, lap = CAB_SEAT_POSE.lap } = {}, frame = scene) {
  const bones = new Map();
  scene.traverse(o => { if (o.isBone) bones.set(o.name, o); });
  frame.updateMatrixWorld(true);
  const frameInv = frame.getWorldQuaternion(new THREE.Quaternion()).invert();
  const deltas = [];
  for (const [name, deg, axis = 'x'] of bends) {
    const bone = bones.get(name);
    if (!bone) throw Error(`cab passenger: the contract skeleton has no ${name}`);
    frame.updateMatrixWorld(true);
    const bw = frameInv.clone().multiply(bone.getWorldQuaternion(new THREE.Quaternion()));
    if (!AXES[axis]) throw Error(`cab passenger: no axis ${axis}`);
    const r = new THREE.Quaternion().setFromAxisAngle(AXES[axis], deg * DEG);
    const d = bw.clone().invert().multiply(r).multiply(bw);
    bone.quaternion.multiply(d);
    deltas.push({ bone, d, base: null });
  }
  // Undo, so apply() owns every write from here on.
  for (let i = deltas.length - 1; i >= 0; i--) deltas[i].bone.quaternion.multiply(deltas[i].d.clone().invert());
  frame.updateMatrixWorld(true);
  const hidden = [];
  if (hide) {
    const re = new RegExp(hide, 'i');
    scene.traverse(o => { if (o.isMesh && re.test(o.name) && o.visible) { o.visible = false; hidden.push(o); } });
  }
  const need = n => { const b = bones.get(n); if (!b) throw Error(`cab passenger: the contract skeleton has no ${n}`); return b; };
  const arms = lap ? ['l', 'r'].map(s => ({ s, upper: need(`upperarm_${s}`), lower: need(`lowerarm_${s}`), hand: need(`hand_${s}`),
    thigh: need(`thigh_${s}`), calf: need(`calf_${s}`),
    middle: need(`middle_01_${s}`), index: need(`index_01_${s}`), pinky: need(`pinky_01_${s}`), base: [null, null, null] })) : [];
  const fq = new THREE.Quaternion(), mid = V(), side = V();
  return {
    bones: [...deltas.map(x => x.bone.name), ...arms.flatMap(a => [a.upper.name, a.lower.name, a.hand.name])], hidden,
    /** Before the mixer: each bent bone back to the clip's own pose of it. */
    restore() {
      for (let i = arms.length - 1; i >= 0; i--) { const a = arms[i]; if (a.base[0]) { a.upper.quaternion.copy(a.base[0]); a.lower.quaternion.copy(a.base[1]); a.hand.quaternion.copy(a.base[2]); } }
      for (const x of deltas) if (x.base) x.bone.quaternion.copy(x.base);
    },
    /** After the mixer: the clip's pose (kept for restore), bent. */
    apply() {
      for (const x of deltas) {
        x.base = (x.base ?? new THREE.Quaternion()).copy(x.bone.quaternion);
        x.bone.quaternion.multiply(x.d);
      }
      if (!arms.length) return;
      // The hands onto the thighs, where the bends have just put them.
      frame.updateMatrixWorld(true);
      frame.getWorldQuaternion(fq);
      const up = AXES.y.clone().applyQuaternion(fq), right = AXES.x.clone().applyQuaternion(fq);
      const [l, r] = arms.map(a => a.thigh.getWorldPosition(V()));
      mid.copy(l).add(r).multiplyScalar(.5);
      for (const a of arms) {
        a.base[0] = (a.base[0] ?? new THREE.Quaternion()).copy(a.upper.quaternion);
        a.base[1] = (a.base[1] ?? new THREE.Quaternion()).copy(a.lower.quaternion);
        a.base[2] = (a.base[2] ?? new THREE.Quaternion()).copy(a.hand.quaternion);
        const hip = a.thigh.getWorldPosition(V()), knee = a.calf.getWorldPosition(V());
        const target = hip.clone().lerp(knee, lap.along).addScaledVector(up, lap.lift);
        side.copy(hip).sub(mid).projectOnPlane(up).normalize();
        target.addScaledVector(side, -lap.inset);
        const out = side.dot(right) >= 0 ? 1 : -1;
        const pole = new THREE.Vector3(lap.pole[0] * out, lap.pole[1], lap.pole[2]).applyQuaternion(fq);
        reach(a.upper, a.lower, a.hand, target, pole);
        // The fingers down the thigh toward the knee, turned a little in, the palm on it.
        const thighDir = knee.clone().sub(hip).normalize();
        layHand(a.hand, a.middle, a.index, a.pinky, thighDir.addScaledVector(side, -lap.turn_in).normalize(), side.clone().negate());
      }
    },
  };
}

/**
 * The seat a passenger sits on, from the clip's: the box seat the clip was made for
 * (`clip_seat_local_m`, the driver's seat node) is moved onto the cab's (`seat_local_m`),
 * less the cushion's give (`sink_m`). Returns the figure root's place in the vehicle.
 */
export function passengerRoot({ seat_local_m, clip_seat_local_m, sink_m = 0 }) {
  if (![seat_local_m, clip_seat_local_m].every(p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite))) {
    throw Error('cab passenger: finite cab and clip seats required');
  }
  return [0, 1, 2].map(k => seat_local_m[k] - clip_seat_local_m[k] - (k === 1 ? sink_m : 0));
}
