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
 * forward from the lower spine, the neck and head lifted again to look ahead, the arms
 * forward toward the knees. The hat is off indoors. tools/test_glessner_ride.mjs measures
 * the bent figure against the cab's own surfaces (roof, floor, walls).
 *
 * Bones whose clip tracks never change are not rewritten by three's mixer, so each frame the
 * bent bones are first put back to the clip's pose (`restore()`, before the mixer runs), then
 * bent again (`apply()`, after it): never a bend on the bend written the frame before, nor on
 * what a life layer added after it (driver-life.js has the same trap).
 */
import * as THREE from 'three';

const X = new THREE.Vector3(1, 0, 0);
const DEG = Math.PI / 180;

/** The default bends (degrees about the vehicle's lateral axis; + tips a forward-pointing limb down). */
export const CAB_SEAT_POSE = Object.freeze({
  bends: Object.freeze([
    ['thigh_l', -44], ['thigh_r', -44],
    ['calf_l', 30], ['calf_r', 30],
    ['spine_01', 20], ['spine_02', 20],
    ['neck_01', -14], ['head', -14],
    ['upperarm_l', 5], ['upperarm_r', 5],
  ]),
  hide: '(headwear|hat)',
});

/**
 * Bend a seated body (`scene`, its clip already applied at its first pose) per `pose`.
 * `frame` is the object whose axes are the vehicle's (the figure's root). Returns
 * { restore(), apply(), bones, hidden } — restore() before each mixer update, apply() after it
 * and before any life layer.
 */
export function seatInCab(scene, { bends = CAB_SEAT_POSE.bends, hide = CAB_SEAT_POSE.hide } = {}, frame = scene) {
  const bones = new Map();
  scene.traverse(o => { if (o.isBone) bones.set(o.name, o); });
  frame.updateMatrixWorld(true);
  const frameInv = frame.getWorldQuaternion(new THREE.Quaternion()).invert();
  const deltas = [];
  for (const [name, deg] of bends) {
    const bone = bones.get(name);
    if (!bone) throw Error(`cab passenger: the contract skeleton has no ${name}`);
    frame.updateMatrixWorld(true);
    const bw = frameInv.clone().multiply(bone.getWorldQuaternion(new THREE.Quaternion()));
    const r = new THREE.Quaternion().setFromAxisAngle(X, deg * DEG);
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
  return {
    bones: deltas.map(x => x.bone.name), hidden,
    /** Before the mixer: each bent bone back to the clip's own pose of it. */
    restore() { for (const x of deltas) if (x.base) x.bone.quaternion.copy(x.base); },
    /** After the mixer: the clip's pose (kept for restore), bent. */
    apply() {
      for (const x of deltas) {
        x.base = (x.base ?? new THREE.Quaternion()).copy(x.bone.quaternion);
        x.bone.quaternion.multiply(x.d);
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
