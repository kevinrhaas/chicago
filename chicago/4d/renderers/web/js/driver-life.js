// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * driver-life.js — a seated driver who is alive on his box (T-1790).
 *
 * The seated clips (`sit_drive`, `sit_drive_look_v2`) hold one pose with a small
 * head glance; on the move Hans read as a statue with his arms out. Kevin, 2026-11-05:
 * "he is frozen, arms stiff, not looking around or shifting naturally". This layers
 * procedural motion on top of whatever the clip wrote this frame:
 *
 *   - breathing: chest and shoulders rise and fall, the head held steady against it;
 *   - the ride: the carriage's bumps and sway reach his pelvis and spine, and the
 *     head stabilises against them as a rider's does; he leans into a turn;
 *   - weight shifts: every few seconds he settles differently on the seat;
 *   - looking around: eyes lead, head and neck follow, the torso joins a wide look;
 *     mostly down the road over the horses, glancing at the houses and walks, into
 *     the turn before he takes it, and at a visitor standing close;
 *   - the reins: elbows in by his sides, hands lower at his lap, giving and taking
 *     with the horses' heads, and now and then shortening a rein;
 *   - blinking, where the LOD carries the eyelid morphs.
 *
 * All of it is additive on the bone's own local frame and rewritten from the clip's
 * pose every frame, so nothing accumulates. Rotation axes are taken once, at bind,
 * from the clip's first pose in the figure's own frame: up, forward (pelvis to
 * hands) and right (left hand to right hand). Positive yaw turns him to his left,
 * positive pitch lifts the chin / leans back, positive roll tips him to his right.
 *
 * Deterministic: the only randomness is a PRNG seeded from the person id, so a
 * harness sees the same motion on every load. It is reconstructed animation, not
 * recorded behaviour (liberty L-driven-town-circuits-2804 covers the driver).
 */
import * as THREE from 'three';

const DEG = Math.PI / 180;
const BLINK = ['eyeBlinkLeft', 'eyeBlinkRight'];

/** A small seeded PRNG (mulberry32) from a string id. */
export function seededRandom(id) {
  let h = 2166136261;
  for (const ch of String(id)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  let a = h >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

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

/** The bones this layer moves. A rig missing any of the core ones is left alone. */
const CORE = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head',
  'clavicle_l', 'clavicle_r', 'upperarm_l', 'upperarm_r', 'lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'];
const OPTIONAL = ['eye_l', 'eye_r',
  ...['index', 'middle', 'ring', 'pinky'].flatMap(f => ['01', '02', '03'].flatMap(k => [`${f}_${k}_l`, `${f}_${k}_r`])),
  'thumb_01_l', 'thumb_02_l', 'thumb_01_r', 'thumb_02_r'];

/**
 * Bind to a posed skeleton. `root` is the figure's root (the HumanActor root);
 * `scene` holds its bones. Call AFTER the seated clip has been applied once.
 * Returns null when the rig is not the contract skeleton.
 */
export function createDriverLife({ root, scene, id = 'driver', faces = [], gaitCycle_m = 1.6 }) {
  const bones = {};
  scene.traverse(o => { if (o.isBone && (CORE.includes(o.name) || OPTIONAL.includes(o.name))) bones[o.name] = o; });
  if (!CORE.every(n => bones[n])) return null;
  root.updateMatrixWorld(true);
  const rootInv = root.getWorldQuaternion(new THREE.Quaternion()).invert();
  const rootInvM = root.matrixWorld.clone().invert();
  const at = name => bones[name].getWorldPosition(new THREE.Vector3()).applyMatrix4(rootInvM);
  // The figure's own frame, read off the pose: up, forward to the hands, right hand side.
  const up = new THREE.Vector3(0, 1, 0);
  const hands = at('hand_l').add(at('hand_r')).multiplyScalar(0.5);
  const forward = hands.sub(at('pelvis')).projectOnPlane(up).normalize();
  const right = at('hand_r').sub(at('hand_l')).projectOnPlane(up);
  right.addScaledVector(forward, -right.dot(forward)).normalize();
  if (!(forward.lengthSq() > 0.5) || !(right.lengthSq() > 0.5)) return null;
  // Each bone's three axes in its own local frame, from its pose in the figure frame.
  const axes = {};
  for (const [name, bone] of Object.entries(bones)) {
    const q = rootInv.clone().multiply(bone.getWorldQuaternion(new THREE.Quaternion())).invert();
    axes[name] = { up: up.clone().applyQuaternion(q), forward: forward.clone().applyQuaternion(q),
      right: right.clone().applyQuaternion(q) };
  }
  // three's PropertyMixer writes a track only when its value changed, so a held
  // (two-key) channel is NOT rewritten each frame: a bone still carrying last
  // frame's output was not touched by the clip and goes back to its base first.
  const held = Object.fromEntries(Object.entries(bones).map(([n, b]) =>
    [n, { base: b.quaternion.clone(), out: new THREE.Quaternion(NaN, NaN, NaN, NaN) }]));
  const rebase = () => {
    for (const [n, h] of Object.entries(held)) {
      const q = bones[n].quaternion;
      if (q.equals(h.out)) q.copy(h.base); else h.base.copy(q);
    }
  };
  const settle = () => { for (const [n, h] of Object.entries(held)) h.out.copy(bones[n].quaternion); };
  const rand = seededRandom(id);
  const between = (a, b) => a + (b - a) * rand();
  const qa = new THREE.Quaternion();
  /** Turn `name` by yaw/pitch/roll (radians) about its figure-frame axes. */
  const turn = (name, yaw = 0, pitch = 0, roll = 0) => {
    const b = bones[name], ax = axes[name];
    if (!b) return;
    if (yaw) b.quaternion.multiply(qa.setFromAxisAngle(ax.up, yaw));
    if (pitch) b.quaternion.multiply(qa.setFromAxisAngle(ax.right, pitch));
    if (roll) b.quaternion.multiply(qa.setFromAxisAngle(ax.forward, roll));
  };

  // State.
  let time = rand() * 100, lastDistance = null;
  const speed = S(), lean = S(), turnLook = S();
  const gaze = { yaw: S(), pitch: S(), eyeYaw: S(), eyePitch: S(), torso: S() };
  let gazeTarget = { yaw: 0, pitch: -6 * DEG }, gazeHold = between(2, 5), gazeKind = 'road';
  const weight = { roll: S(), lean: S(), yaw: S() };
  let weightTarget = { roll: 0, lean: 0, yaw: 0 }, weightHold = between(4, 9);
  const rein = { l: S(), r: S() };
  let reinEvent = { side: null, t: 0 }, reinNext = between(8, 18);
  let blinkNext = between(2, 5), blinkT = -1;
  const lookAt = new THREE.Vector3();

  const pickGaze = (moving, viewer) => {
    // A visitor standing close, or close and in front: he looks at them.
    if (viewer && (viewer.dist < (moving ? 7 : 12)) && rand() < (moving ? 0.35 : 0.7)) {
      gazeKind = 'viewer'; gazeHold = between(1.5, 3.5); return;
    }
    const r = rand();
    if (moving && r < 0.45) { // back to the road, over the horses' ears
      gazeKind = 'road'; gazeTarget = { yaw: between(-6, 6) * DEG, pitch: between(-9, -3) * DEG };
      gazeHold = between(2.5, 6);
    } else if (r < 0.7) { // a house, a gate, the walk on one side
      gazeKind = 'side'; const side = rand() < 0.5 ? -1 : 1;
      gazeTarget = { yaw: side * between(25, 70) * DEG, pitch: between(-8, 6) * DEG };
      gazeHold = between(0.9, 2.6);
    } else if (r < 0.85) { // the horses: their heads, the traces
      gazeKind = 'horses'; gazeTarget = { yaw: between(-12, 12) * DEG, pitch: between(-20, -12) * DEG };
      gazeHold = between(0.8, 2);
    } else { // a long look, up at the trees or a far front
      gazeKind = 'far'; const side = rand() < 0.5 ? -1 : 1;
      gazeTarget = { yaw: side * between(10, 40) * DEG, pitch: between(2, 12) * DEG };
      gazeHold = between(1.5, 3.5);
    }
  };

  return {
    bones: Object.keys(bones),
    /**
     * Apply one frame on top of the clip's pose. `dt` is visual seconds (0 holds the
     * pose where it is); `motion` is { distance_m, curvature, moving }; `viewer` a
     * world-space position of the visitor's eye, or null.
     */
    apply(dt, { distance_m = null, curvature = 0, moving = false } = {}, viewer = null) {
      dt = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.1) : 0;
      time += dt;
      rebase();
      // How fast the box is going, from the travelled distance.
      let v = 0;
      if (Number.isFinite(distance_m) && lastDistance !== null && dt > 0) v = clamp((distance_m - lastDistance) / dt, 0, 6);
      if (Number.isFinite(distance_m)) lastDistance = distance_m;
      const vel = spring(speed, moving ? v : 0, 3, dt);
      const ride = clamp(vel / 1.6, 0, 1.4);
      const dist = Number.isFinite(distance_m) ? distance_m : 0;
      const step = dist / gaitCycle_m * 2 * Math.PI; // one horse stride per cycle

      // The visitor, in the figure's frame.
      let seen = null;
      if (viewer) {
        lookAt.copy(viewer).applyMatrix4(rootInvM.copy(root.matrixWorld).invert()).sub(at('neck_01'));
        const flat = Math.hypot(lookAt.dot(forward), lookAt.dot(right));
        const yaw = Math.atan2(-lookAt.dot(right), lookAt.dot(forward));
        seen = { dist: lookAt.length(), yaw, pitch: Math.atan2(lookAt.y, flat) };
        if (Math.abs(yaw) > 110 * DEG) seen = null; // behind him: he does not crane round
      }

      // Gaze: a hold, then a new place to look.
      gazeHold -= dt;
      if (gazeHold <= 0) pickGaze(moving && ride > 0.1, seen);
      let target = gazeTarget;
      if (gazeKind === 'viewer') {
        if (seen) target = { yaw: clamp(seen.yaw, -80 * DEG, 80 * DEG), pitch: clamp(seen.pitch, -25 * DEG, 20 * DEG) };
        else gazeHold = Math.min(gazeHold, 0);
      }
      // Into the turn before he takes it: a driver looks where the team is going.
      const into = spring(turnLook, clamp(curvature * 4.5, -0.45, 0.45) * (moving ? 1 : 0), 2.2, dt);
      const ty = clamp(target.yaw + (gazeKind === 'road' ? into : into * 0.4), -85 * DEG, 85 * DEG);
      const tp = target.pitch;
      // Eyes lead (fast), the head follows, the neck shares it, the torso joins a wide look.
      const eyeYaw = spring(gaze.eyeYaw, ty, 28, dt), eyePitch = spring(gaze.eyePitch, tp, 28, dt);
      const headYaw = spring(gaze.yaw, ty, 6.5, dt), headPitch = spring(gaze.pitch, tp, 6.5, dt);
      const torso = spring(gaze.torso, Math.abs(ty) > 35 * DEG ? (ty - Math.sign(ty) * 35 * DEG) * 0.45 : 0, 3, dt);

      // Weight shifts: settle differently on the seat every few seconds.
      weightHold -= dt;
      if (weightHold <= 0) {
        weightTarget = { roll: between(-2.6, 2.6) * DEG, lean: between(-3.5, 1.2) * DEG, yaw: between(-3, 3) * DEG };
        weightHold = between(5, 13);
      }
      const wRoll = spring(weight.roll, weightTarget.roll, 1.6, dt);
      const wLean = spring(weight.lean, weightTarget.lean, 1.6, dt);
      const wYaw = spring(weight.yaw, weightTarget.yaw, 1.4, dt);

      // Breathing, about 13 a minute, a little quicker and shallower on the move.
      const breath = Math.sin(time * 2 * Math.PI / (4.6 - ride * 0.6));
      // The ride: road roughness under four wheels and the team's stride in the shafts.
      const bump = ride * (0.55 * Math.sin(dist * 2.31 + 0.7) + 0.35 * Math.sin(dist * 5.17 + 2.1)
        + 0.25 * Math.sin(dist * 9.43));
      const sway = ride * (0.6 * Math.sin(step) + 0.25 * Math.sin(dist * 1.13 + 1.3));
      const bob = ride * Math.sin(2 * step + 0.4);
      // Lean into a turn against its lateral pull, v^2 k / g.
      const leanTurn = spring(lean, -Math.atan(vel * vel * curvature / 9.81) * 1.6, 2.5, dt);

      // Pelvis and spine: the seat moves him, the spine carries it up, the neck takes it out.
      turn('pelvis', wYaw * 0.5, wLean * 0.3 + bob * 0.5 * DEG, wRoll + sway * 0.9 * DEG + bump * 0.5 * DEG + leanTurn * 0.4);
      turn('spine_01', wYaw * 0.2, wLean * 0.35 + bob * 0.4 * DEG, -wRoll * 0.35 + leanTurn * 0.3);
      turn('spine_02', torso * 0.35 + wYaw * 0.15, breath * 0.9 * DEG + wLean * 0.35, -wRoll * 0.25 + leanTurn * 0.2);
      turn('spine_03', torso * 0.65 + wYaw * 0.15, breath * 0.6 * DEG, -wRoll * 0.2 - sway * 0.4 * DEG);
      // The head is held level against the pelvis' roll and pitch (what the eyes need).
      const steadyRoll = -(wRoll * 0.2 + sway * 0.5 * DEG + bump * 0.35 * DEG + leanTurn * 0.6);
      const steadyPitch = -(breath * 1.1 * DEG + wLean * 0.9 + bob * 0.6 * DEG);
      const headTurn = headYaw - torso;
      turn('neck_01', headTurn * 0.4, headPitch * 0.35 + steadyPitch * 0.5, steadyRoll * 0.5);
      turn('head', headTurn * 0.6, headPitch * 0.65 + steadyPitch * 0.5, steadyRoll * 0.5 + headTurn * -0.06);
      // Eyes lead the head: what is left of the turn after the head has made it.
      const ey = clamp(eyeYaw - headYaw, -25 * DEG, 25 * DEG), ep = clamp(eyePitch - headPitch, -15 * DEG, 15 * DEG);
      turn('eye_l', ey, ep); turn('eye_r', ey, ep);

      // Shoulders lift a touch with each breath.
      turn('clavicle_l', 0, 0, -breath * 0.7 * DEG);
      turn('clavicle_r', 0, 0, breath * 0.7 * DEG);

      // The reins. Elbows in by his sides, forearms down to his lap, wrists turned
      // thumb up as a driver holds a rein; then the give and take with the horses'
      // heads (two nods a stride) and, now and then, one hand shortening its rein.
      reinNext -= dt;
      if (reinNext <= 0 && moving) { reinEvent = { side: rand() < 0.5 ? 'l' : 'r', t: 0 }; reinNext = between(9, 20); }
      if (reinEvent.side) { reinEvent.t += dt; if (reinEvent.t > 1.4) reinEvent.side = null; }
      for (const side of ['l', 'r']) {
        const sgn = side === 'l' ? -1 : 1;
        const pull = reinEvent.side === side && reinEvent.t < 0.7 ? 1 : 0;
        const take = spring(rein[side], pull, 9, dt);
        const play = ride * Math.sin(2 * step + (side === 'l' ? 0 : 0.5));
        turn(`upperarm_${side}`, 0, (-10 + play * 1.3 + take * 7) * DEG, sgn * 9 * DEG);
        turn(`lowerarm_${side}`, sgn * 4 * DEG, (-8 - play * 1.6 - take * 9) * DEG, 0);
        turn(`hand_${side}`, 0, (6 + play * 2) * DEG, sgn * 22 * DEG);
        // A closed hand on the rein (T-3422: the photographed coachmen hold theirs in a fist).
        for (const f of ['index', 'middle', 'ring', 'pinky']) {
          const curl = (f === 'index' ? 72 : f === 'middle' ? 78 : f === 'ring' ? 82 : 86) * DEG;
          turn(`${f}_01_${side}`, 0, -curl * 0.9, 0);
          turn(`${f}_02_${side}`, 0, -curl * 1.15, 0);
          turn(`${f}_03_${side}`, 0, -curl * 0.7, 0);
        }
        turn(`thumb_01_${side}`, 0, 0, sgn * 18 * DEG);
        turn(`thumb_02_${side}`, 0, -35 * DEG, 0);
      }

      // Blinks, where the LOD carries the eyelids; a quick double now and then.
      if (faces.length) {
        blinkNext -= dt;
        if (blinkNext <= 0 && blinkT < 0) { blinkT = 0; blinkNext = rand() < 0.15 ? 0.35 : between(2.2, 6); }
        let w = 0;
        if (blinkT >= 0) { blinkT += dt; w = blinkT < 0.16 ? Math.sin(blinkT / 0.16 * Math.PI) : 0; if (blinkT >= 0.16) blinkT = -1; }
        for (const m of faces) for (const k of BLINK) {
          const i = m.morphTargetDictionary?.[k];
          if (i !== undefined) m.morphTargetInfluences[i] = w;
        }
      }
      settle();
    },
    snapshot() {
      return { gaze: gazeKind, yaw_deg: +(gaze.yaw.x / DEG).toFixed(2), pitch_deg: +(gaze.pitch.x / DEG).toFixed(2),
        weight_roll_deg: +(weight.roll.x / DEG).toFixed(2), speed_m_s: +speed.x.toFixed(3) };
    },
  };
}
