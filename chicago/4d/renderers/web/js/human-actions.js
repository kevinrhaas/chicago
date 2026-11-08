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
 *   - walking, the arms swing opposite to the legs. With the gait layer (human-gait.js,
 *     passed in as `gait`) the swing is driven from its phase and speed along measured
 *     arm curves (see ARM_SWING below); without it, read from where the feet are, so the swing follows
 *     any walk clip's stride and stops when the feet stop.
 *
 * Hand placements are solved by two-bone IK in the figure's own frame, from landmarks
 * read off the body (the hips, the small of the back, the brow), so they fit any body
 * on the contract skeleton. Each pose blends in and out over most of a second.
 *
 * A duty (human-duties.js, T-3490) can hold one standing pose (`hold`: a man in a rank, his
 * hands at his sides) and raise a talking hand (`setTalk`: a slow beat of the forearm before
 * him, palm half up), while the others in his knot look at him.
 *
 * Sweeping and carrying need props, and the
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
const CASCADE = Object.freeze({ index: 0.93, middle: 1, ring: 1.04, pinky: 1.08 });
// How a curl shares out along each finger: the knuckle, the middle joint and the last one.
// A loose hand bends about as much at the knuckle as at the middle joint, and the last joint
// half that; a hand bent mostly past the knuckle is a claw.
const FLEX = Object.freeze([['01', 1], ['02', 0.9], ['03', 0.45]]);
// How far each finger turns toward the index (degrees, + toward it) as the hand closes to 0.4.
const CONVERGE = Object.freeze({ index: -9, middle: 0, ring: 5, pinky: 11 });
// How much fuller across the fingers are drawn (see shapeHand).
const FINGER_FILL = 1.12;
// The relaxed thumb's three bones, each as (along the hand, toward the palm, toward the index).
// Its root bone goes only THUMB_ROOT of the way: turned all the way in from the model's flat
// hand, the web at the root of the thumb folds through itself and tears.
const THUMB_ROOT = 0.72;
const THUMB = Object.freeze([['01', [0.8, 0.45, 0.4]], ['02', [0.92, 0.32, -0.12]], ['03', [0.85, 0.42, -0.15]]]);
const ARM = (s) => [`upperarm_${s}`, `lowerarm_${s}`, `hand_${s}`,
  ...FINGERS.flatMap((f) => ['01', '02', '03'].map((k) => `${f}_${k}_${s}`)), `thumb_01_${s}`, `thumb_02_${s}`, `thumb_03_${s}`];
const NEEDED = ['pelvis', 'spine_03', 'head', 'thigh_l', 'thigh_r', 'foot_l', 'foot_r', 'upperarm_l', 'upperarm_r',
  'lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'];

/** The standing hand poses a person moves between; `rest` is no IK at all. */
export const HAND_POSES = Object.freeze(['rest', 'hips', 'behind', 'clasp']);
// A woman in a full skirt (T-3434) never lets her hands hang, nor sets them on her hips: in
// both the hand sinks into the skirt's bell. She stands with them clasped in front at the
// waist, over the apron, or held at the waist behind.
export const SKIRT_POSES = Object.freeze(['clasp', 'behind']);

/**
 * The arm swing on the gait layer's walk, read from motion capture rather than drawn as a
 * sine. Each arm swings with the opposite leg. `upper` is the upper arm against the
 * vertical over one cycle from the same side's heel strike (+ elbow ahead of the shoulder),
 * and `elbow` the elbow's flexion: Horst et al. 2019, 57 young adults
 * (data/humans/gait/normative_gait.json, alt.arm_vs_vertical_deg and
 * cycle_tables.elbow_flexion_deg). What the curves say, and the sine said wrongly:
 *   - the arm swings mostly BEHIND the body: from about 19 deg back to 6 forward of the
 *     vertical, so the hand comes only a little ahead of the thigh but well back of it;
 *   - the arm is furthest back just after its own heel strike and furthest forward at the
 *     other heel strike, and the elbow follows the shoulder late (its peak about 4 % of the
 *     cycle later), so the forearm trails the upper arm like a loose pendulum;
 *   - the elbow is never straight: about 20 deg at the back of the swing to about 50 at
 *     the front (the dataset's shoulder point is the acromion, which reads the elbow some
 *     8 deg too bent, `elbowOffset_deg`).
 * The swing is scaled from the measured range of each sex at its measured speed (`rom`:
 * women 31.2 deg at 1.49 m/s, men 22.4 at 1.40) to the walker's own speed, and less with
 * age (`older`, reconstructed: the decline is reported, Mirelman 2015, not tabled). The hand
 * hangs loose from the wrist and trails the forearm (`wristLag`, a fraction of the cycle),
 * fingers loosely curled (`curl`), the palm to the thigh and turning back as the arm goes
 * back (`palmBack`). A woman in a full skirt swings about half as far (a lady's
 * arm-swinging was "ill-breeding" to Hill's Manual, Chicago 1887; data/humans/gait/README.md)
 * and carries the arm out over the skirt's bell, a little outward as it comes forward,
 * never in toward it. The shapes are measured; the scalings, the wrist and the hand are
 * reconstructed (liberty L-human-gait-3472).
 */
export const ARM_SWING = Object.freeze({
  upper: Object.freeze([-19.4, -19.4, -18.0, -15.7, -12.8, -9.0, -5.0, -1.3, 1.9, 4.4, 5.8, 5.5, 3.4, 0.4, -2.1, -4.7, -8.1, -11.7, -15.0, -17.6, -19.0]),
  elbow: Object.freeze([22.6, 21.3, 20.4, 21.3, 23.9, 27.4, 32.4, 38.1, 43.8, 48.4, 51.0, 51.5, 49.8, 45.6, 39.6, 33.8, 29.9, 27.5, 25.9, 24.6, 23.2]),
  rom: Object.freeze({ female: [31.2, 1.49], male: [22.4, 1.40], all: [26.9, 1.44] }),
  elbowOffset_deg: 8, older: 0.3, wristLag: 0.06, wrist_deg: 6, curl: 0.4, palmBack: 0.35,
  // Two people never swing alike (reconstructed): each draws how far (`range`), how far back
  // the arm hangs (`mean_deg`), how bent the elbow (`elbow_deg`), and one arm a little more than the other (`side`).
  person: Object.freeze({ range: [0.85, 1.15], mean_deg: [-3, 3], elbow_deg: [-4, 4], side: [0.92, 1.08] }),
  inward: 0.25, skirt: { scale: 0.5, inward: -0.2 },
});
/** A periodic table of 21 values (0..100 % of the cycle, the last repeating the first) at cycle fraction `c`. */
function cycleAt(table, c) {
  const x = (((c % 1) + 1) % 1) * 20, i = Math.floor(x), t = x - i;
  const p = (k) => table[((k % 20) + 20) % 20];
  const p0 = p(i - 1), p1 = p(i), p2 = p(i + 1), p3 = p(i + 2);
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t);
}
const tableMean = (t) => t.slice(0, 20).reduce((a, b) => a + b, 0) / 20;
const UPPER_MEAN = tableMean(ARM_SWING.upper), UPPER_ROM = Math.max(...ARM_SWING.upper) - Math.min(...ARM_SWING.upper);
const ELBOW_MEAN = tableMean(ARM_SWING.elbow);
const fin = (x, d = 0) => (Number.isFinite(x) ? x : d);

export function createHumanActions({ id = 'human', scene = null, greeting = 'brow', skirt = false, carry = null } = {}) {
  const rand = seededRandom(`actions:${id}`);
  // This person's own arm swing (ARM_SWING.person), from its own stream so it moves no other draw.
  const own = (() => {
    const r = seededRandom(`arms:${id}`), p = ARM_SWING.person, pick = ([a, b]) => a + (b - a) * r();
    const range = pick(p.range), mean = pick(p.mean_deg), elbow = pick(p.elbow_deg), side = pick(p.side);
    return { range, mean, elbow, l: side, r: 2 - side };
  })();
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
      // Across the knuckles toward the index finger, square to the other two.
      let index = new THREE.Vector3(0, 0, 1);
      if (found[`index_01_${s}`] && found[`pinky_01_${s}`]) {
        index = found[`index_01_${s}`].position.clone().sub(found[`pinky_01_${s}`].position);
        index.addScaledVector(along, -index.dot(along)).addScaledVector(palm, -index.dot(palm)).normalize();
      }
      local[`hand_${s}`] = { along, palm, index };
      // The thumb's bones, each along to its child; the last, which has none, along its own
      // offset from its parent (the line of the bone before it).
      for (const [n, c] of [[`thumb_01_${s}`, `thumb_02_${s}`], [`thumb_02_${s}`, `thumb_03_${s}`]]) {
        if (found[n] && found[c] && found[c].position.lengthSq() > 1e-12) local[n] = { along: found[c].position.clone().normalize() };
      }
      const t3 = found[`thumb_03_${s}`];
      if (t3 && t3.position.lengthSq() > 1e-12) local[`thumb_03_${s}`] = { along: t3.position.clone().normalize().applyQuaternion(t3.quaternion.clone().invert()) };
      // Which way about each finger's local X closes it toward the palm.
      const f2 = found[`index_02_${s}`], tip = found[`index_03_${s}`];
      if (f2 && tip) {
        const t0 = tip.position.clone().applyQuaternion(f2.quaternion);
        const t1 = tip.position.clone().applyQuaternion(f2.quaternion.clone().multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), 0.3)));
        // Both are in index_01's frame; carry the palm normal there through the chain.
        const toF1 = found[`index_01_${s}`].quaternion.clone().invert();
        local[`curl_${s}`] = t1.sub(t0).dot(palm.clone().applyQuaternion(toF1)) >= 0 ? 1 : -1;
      } else local[`curl_${s}`] = 1;
      // Which way about each finger's local Z (square to the palm) turns it toward the index.
      const f1 = found[`index_01_${s}`];
      if (f1 && f2 && f2.position.lengthSq() > 1e-12) {
        const c0 = f2.position.clone().applyQuaternion(f1.quaternion);
        const c1 = f2.position.clone().applyQuaternion(f1.quaternion.clone().multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), 0.3)));
        local[`spread_${s}`] = c1.sub(c0).dot(index) >= 0 ? 1 : -1;
      } else local[`spread_${s}`] = 0;
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

  /**
   * Ask for side `s`'s fingers curled by `k` (0 open .. 1 a loose fist), blended in by `w`
   * over what was asked before in this frame: the hanging hand asks first, then the walk, a
   * pose, the talk, the greeting or a held thing each take over as far as their own weight.
   * The curl is laid on once, in shapeHand() at the end of the frame, so two askers never
   * add up (T-3496: the hanging hand's curl and the walk's together closed every walking
   * hand to 0.74, a claw).
   */
  function curl(s, k, w = 1) { if (w > 1e-4) handAsk[s].curl += (k - handAsk[s].curl) * Math.min(1, w); }
  /** Ask for side `s`'s thumb laid in along the index (0 as the clip has it .. 1), blended by `w`. */
  function thumbIn(s, k, w = 1) { if (w > 1e-4) handAsk[s].thumb += (k - handAsk[s].thumb) * Math.min(1, w); }
  const handAsk = { l: { curl: 0, thumb: 0 }, r: { curl: 0, thumb: 0 } };

  /** Lay side `s`'s asked curl and thumb on its fingers, once, at the end of the frame. */
  function shapeHand(s) {
    const k = handAsk[s].curl;
    // As a hand closes its fingers come together, toward the middle one (they point to the
    // root of the thumb): the bind pose holds them side by side, which curled reads as a fan.
    if (k > 1e-4 && local[`spread_${s}`]) for (const f of FINGERS) {
      const b = bones[`${f}_01_${s}`];
      if (b && CONVERGE[f]) b.quaternion.multiply(qa.setFromAxisAngle(new THREE.Vector3(0, 0, 1), local[`spread_${s}`] * CONVERGE[f] * Math.min(1, k / 0.4) * DEG));
    }
    if (Math.abs(k) > 1e-4) for (const f of FINGERS) for (const [seg, amt0] of FLEX) {
      const b = bones[`${f}_${seg}_${s}`];
      if (!b) continue;
      // A relaxed hand's cascade: each finger toward the little one a little more closed.
      const amt = amt0 * CASCADE[f];
      // Each finger bends about its own local X, as the contract hand does (driver-life.js
      // bends them about the figure's right, which is the same axis in a hanging hand).
      b.quaternion.multiply(qa.setFromAxisAngle(new THREE.Vector3(1, 0, 0), local[`curl_${s}`] * k * amt * 60 * DEG));
    }
    // The model's hand is a flat one with gaps between the fingers; a little fuller across,
    // they lie against each other as a loose hand's do. Set outright each frame (no other
    // layer scales a finger), about the finger's own axis, so it moves no joint.
    for (const f of FINGERS) bones[`${f}_01_${s}`]?.scale.set(FINGER_FILL, 1, 1.04);
    layThumb(s, handAsk[s].thumb);
    handAsk[s].curl = 0; handAsk[s].thumb = 0;
  }

  /**
   * Lay side `s`'s thumb in along the side of the index finger, a little round toward the
   * palm, as a hand hanging loose holds it (blend `w`). The clip holds it straight out from
   * the hand, which from the side reads as a thumb stuck out like a hitchhiker's. Each bone
   * is aimed in the hand's own frame (along the hand, toward the palm, toward the index), so
   * the tip comes to lie beside the index's middle joint, not into the palm or the finger.
   */
  function layThumb(s, w) {
    if (!(w > 1e-4) || !local[`thumb_01_${s}`]) return;
    const h = bones[`hand_${s}`], ax = local[`hand_${s}`];
    h.updateWorldMatrix(true, false);
    const hq = h.getWorldQuaternion(new THREE.Quaternion());
    const along = ax.along.clone().applyQuaternion(hq), palm = ax.palm.clone().applyQuaternion(hq), index = ax.index.clone().applyQuaternion(hq);
    for (const [seg, [a, p, i]] of THUMB) {
      const n = `thumb_${seg}_${s}`;
      if (!local[n]) continue;
      aimAlong(n, along.clone().multiplyScalar(a).addScaledVector(palm, p).addScaledVector(index, i), w * (seg === '01' ? THUMB_ROOT : 1));
      bones[n].updateMatrixWorld(true);
    }
  }
  /** Turn bone `n` so its own `local[n].along` points along world `dir` (blend `w`). */
  function aimAlong(n, dir, w) {
    const b = bones[n];
    if (!b || !local[n]) return;
    b.parent.updateWorldMatrix(true, false);
    const parentQ = b.parent.getWorldQuaternion(new THREE.Quaternion());
    const worldQ = parentQ.clone().multiply(b.quaternion);
    const cur = local[n].along.clone().applyQuaternion(worldQ).normalize();
    const target = new THREE.Quaternion().setFromUnitVectors(cur, dir.clone().normalize()).multiply(worldQ);
    b.quaternion.slerp(parentQ.invert().multiply(target), w);
  }

  // State, kept across a LOD swap.
  let time = rand() * 50;
  let pose = skirt ? 'clasp' : 'rest', poseW = 1, prevPose = pose, poseHold = between(6, 14);
  let greet = -1, greetCool = 0, nodRequest = 0;
  // T-3490: a pose held by a duty (a man in a rank, hands at his sides), and the talking hand.
  let heldPose = null, talking = false, talkW = 0;
  const talkSide = rand() < 0.8 ? 'r' : 'l';
  const swing = { l: 0, r: 0 };
  const gaitArm = { l: 0, r: 0 }; // the gait-driven shoulder swing now, radians, forward +
  const upDir = new THREE.Vector3(), foreDir = new THREE.Vector3(), bend = new THREE.Vector3();
  const wdir = new THREE.Vector3(), handDir = new THREE.Vector3(), palmDir = new THREE.Vector3();
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
    /** T-3490: hold one standing pose until released (null): a man in a rank stands with his hands at his sides. */
    hold(name) {
      if (name === null) { heldPose = null; poseHold = between(4, 10); return api; }
      if (!HAND_POSES.includes(name)) return api;
      heldPose = name;
      if (name !== pose) { prevPose = pose; pose = name; poseW = 0; }
      return api;
    },
    get held() { return heldPose; },
    /** T-3490: talking, one hand comes up before him and moves with what he says (no words: L1). */
    setTalk(on) { talking = !!on; return api; },
    get talking() { return talking; },
    /** Touch the brow in greeting now (the right hand), unless one is under way. */
    // A woman in a dress (T-3423) greets with the nod alone: the touch of the brim or
    // forelock is a man's.
    greet() { if (greeting === 'nod') { nodRequest = 1; return api; } if (greet < 0) { greet = 0; nodRequest = 1; } return api; },
    /** One-shot: true once after a greeting starts, for the life layer to nod. */
    takeNod() { const n = nodRequest; nodRequest = 0; return n > 0; },
    apply(dt, { state = 'standing', root: r = null, viewer = null, gait = null } = {}) {
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
        thumbIn(s, 0.8);
      }

      // Walking: each arm swings opposite its own side's leg, as far as the stride is long.
      // Read from the feet when there is no gait layer; with one, this fades out as the
      // gait's own swing (below) fades in.
      const gw = gait ? clamp(fin(gait.weight), 0, 1) : 0;
      if (walking) {
        const keep = gait ? 1 - gw : 1;
        const fL = bones.foot_l.getWorldPosition(new THREE.Vector3()), fR = bones.foot_r.getWorldPosition(new THREE.Vector3());
        const d = fL.sub(fR).dot(toWorldDir(fig.fwd)); // + when the left foot leads (last frame's pose)
        for (const s of SIDES) {
          if (s === hold?.side) { swing[s] = 0; continue; }
          const target = clamp((s === 'l' ? -d : d) * 0.6, -0.3, 0.3); // radians of swing, forward +
          swing[s] += (target - swing[s]) * (1 - Math.exp(-14 * dt));
          const amt = swing[s] * keep;
          if (keep === 0) continue;
          const fwdSwing = Math.max(0, amt);
          const up = bones[`upperarm_${s}`];
          up.parent.updateWorldMatrix(true, false);
          const axis = toWorldDir(fig.left).multiplyScalar(-1); // about the figure's right: + swings a hanging arm forward
          const pq = up.parent.getWorldQuaternion(new THREE.Quaternion());
          const wq = pq.clone().multiply(up.quaternion);
          wq.premultiply(new THREE.Quaternion().setFromAxisAngle(axis, amt));
          up.quaternion.copy(pq.invert().multiply(wq));
          up.updateMatrixWorld(true);
          // The elbow bends more as the arm comes forward, and the forearm swings past it.
          const lo = bones[`lowerarm_${s}`];
          const lq = lo.parent.getWorldQuaternion(new THREE.Quaternion());
          const lw = lq.clone().multiply(lo.quaternion).premultiply(new THREE.Quaternion().setFromAxisAngle(axis, fwdSwing * 0.7));
          lo.quaternion.copy(lq.invert().multiply(lw));
        }
      } else { swing.l = 0; swing.r = 0; }
      // The gait layer's walk: the swing from its phase (ARM_SWING above), blended by its
      // weight. Each arm is aimed outright in the figure's frame, the upper arm, then the
      // forearm from the elbow, then the hand along it, so the swing does not depend on
      // what the clip did with the arm.
      if (gait && gw > 1e-4) {
        const A = ARM_SWING, phase = fin(gait.phase), P = gait.profile ?? {};
        const [rom, at] = A.rom[P.female === true || skirt ? 'female' : P.female === false ? 'male' : 'all'];
        const speed = fin(gait.speed, at);
        // How far this walker swings against the measured mean, by speed (the swing grows
        // about in proportion to it) and age, and half that in a skirt.
        const k = clamp((rom / UPPER_ROM) * (speed / at) * (1 - A.older * clamp(fin(P.old), 0, 1)), 0.2, 1.6) * (skirt ? A.skirt.scale : 1);
        const abd = skirt ? 0.16 : 0.075, carry = skirt ? 0.12 : 0.03, inK = skirt ? A.skirt.inward : A.inward;
        for (const s of SIDES) {
          if (s === hold?.side) { gaitArm[s] = 0; continue; } // T-3481: the carrying arm is held, not swung
          const sx = s === 'l' ? 1 : -1, ks = k * own.range * own[s];
          const shoulderAt = (c) => (UPPER_MEAN + own.mean + (cycleAt(A.upper, c) - UPPER_MEAN) * ks) * DEG;
          const elbowAt = (c) => Math.max(6, ELBOW_MEAN - A.elbowOffset_deg + own.elbow + (cycleAt(A.elbow, c) - ELBOW_MEAN) * ks) * DEG;
          // The tables run from the same side's heel strike: the left at phase 0, the right at 0.5.
          const c = phase + (s === 'l' ? 0 : 0.5);
          const th = shoulderAt(c), elbow = elbowAt(c);
          gaitArm[s] = th;
          // The upper arm: down, swung about the figure's right, a little out from the side
          // (in a skirt, out over the bell), and in toward the front of the thigh as it comes forward.
          upDir.copy(fig.up).multiplyScalar(-Math.cos(th)).addScaledVector(fig.fwd, Math.sin(th))
            .addScaledVector(fig.left, sx * (abd - inK * Math.max(0, th))).normalize();
          // The elbow bends about the figure's right, square to the upper arm.
          bend.copy(fig.left).negate().addScaledVector(upDir, upDir.dot(fig.left)).normalize();
          foreDir.copy(upDir).applyAxisAngle(bend, elbow).addScaledVector(fig.left, sx * carry).normalize();
          aim(`upperarm_${s}`, wdir.copy(upDir).applyQuaternion(sceneQ), gw);
          bones[`upperarm_${s}`].updateMatrixWorld(true);
          aim(`lowerarm_${s}`, wdir.copy(foreDir).applyQuaternion(sceneQ), gw);
          bones[`lowerarm_${s}`].updateMatrixWorld(true);
          // The hand hangs loose from the wrist and trails: it points where the forearm
          // pointed a moment ago (flexing as the arm comes back, extending as it goes forward).
          const lagged = (shoulderAt(c - A.wristLag) + elbowAt(c - A.wristLag)) - (th + elbow);
          const wrist = clamp(A.wrist_deg * DEG + lagged, -14 * DEG, 18 * DEG);
          handDir.copy(foreDir).applyAxisAngle(bend, wrist).applyQuaternion(sceneQ);
          // Palm to the thigh, turning back as the arm goes behind (0 at the front, 1 at the back).
          const back = clamp((Math.max(...A.upper) - cycleAt(A.upper, c)) / UPPER_ROM, 0, 1);
          palmDir.copy(fig.left).multiplyScalar(-sx).addScaledVector(fig.fwd, -(0.12 + A.palmBack * back)).applyQuaternion(sceneQ);
          orientHand(s, handDir, palmDir, gw);
          // Fingers loosely closed and the thumb in along the index, as a walking hand is
          // carried (the clip holds them open, which reads as a hand held out).
          curl(s, A.curl, gw);
          thumbIn(s, 0.9, gw);
        }
      } else { gaitArm.l = 0; gaitArm.r = 0; }

      // Standing: what the hands are doing.
      if (standing) {
        poseHold -= dt;
        if (poseHold <= 0 && greet < 0 && !heldPose) choosePose();
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
            curl(s, t.curl, w);
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
      // T-3490: the talking hand. The forearm comes up before the body to the height of the
      // waistcoat's pockets, the palm half up and turned in, and beats with the talk: a slow
      // sway with a quicker small one over it, as a man's hand goes when he tells something.
      talkW += ((talking && standing ? 1 : 0) - talkW) * (1 - Math.exp(-3.2 * dt));
      if (talkW > 1e-3 && !(greet >= 0 && talkSide === 'r')) {
        const s = talkSide, sx = s === 'l' ? 1 : -1;
        const beat = Math.sin(time * 2.1) * 0.035 + Math.sin(time * 5.3 + 1.1) * 0.018;
        const wrist = new THREE.Vector3(sx * (L.hipHalf + 0.02 + Math.sin(time * 1.3) * 0.02), L.pelvisY + 0.2 + beat,
          0.26 + Math.sin(time * 1.7 + 0.4) * 0.03);
        const w = smooth(talkW);
        reach(s, toWorldPos(wrist), toWorldDir(new THREE.Vector3(sx, -0.7, -0.35)), w);
        bones[`lowerarm_${s}`].updateMatrixWorld(true);
        orientHand(s, toWorldDir(new THREE.Vector3(-sx * 0.25, 0.12 + beat, 1)), toWorldDir(new THREE.Vector3(-sx * 0.55, 0.8, 0)), w * 0.9);
        curl(s, 0.2, w);
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
        curl('r', 0.18, w);
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
      for (const s of SIDES) shapeHand(s);
      settle();
    },
    snapshot() {
      return { pose, blend: +poseW.toFixed(3), greeting: greet >= 0, carrying: hold?.side ?? null, held: heldPose, talking, talk_w: +talkW.toFixed(3), swing_l_deg: +(swing.l / DEG).toFixed(2), swing_r_deg: +(swing.r / DEG).toFixed(2),
        gait_l_deg: +(gaitArm.l / DEG).toFixed(2), gait_r_deg: +(gaitArm.r / DEG).toFixed(2) };
    },
  };
  if (scene && !bind(scene)) return null;
  return api;
}
