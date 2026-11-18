// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * board-climb.js — the visitor seen climbing up onto a carriage's box or into a wagon, and
 * down again (T-3560).
 *
 * Kevin, 2026-11-17: "when i stood at a carriage in 1904 and said get up next to the coachman
 * he just appeared on the wagon he should have a climb up sequence that shows him boarding that
 * applies all years". Climb up (transport-interactions.js) now draws the visitor as a period
 * figure of the year (data/transport/driven/boarding.json `figure`, an anonymous stand-in, as
 * the rider on a saddle horse is) who walks from where the visitor stood to the vehicle's side,
 * puts a foot on the front wheel's hub, a hand on the rail, steps up and sits on the seat. The
 * eye goes out beside the vehicle and watches him climb, then into the seat. Get down is the
 * same climb backwards, and a walk to a clear stand beside the team.
 *
 * Each vehicle's climb is a list of keys (`vehicles[].keys`, vehicle-root local metres: +z
 * ahead, +x the vehicle's left, y up from its wheels' ground): where the pelvis is, where each
 * foot's sole and each palm is, which way the figure faces (`face`, degrees right of the
 * vehicle's heading), how far forward he leans. A key without a pelvis or feet stands on the
 * ground at the stand; without a hand, the arm hangs; a limb named in `air` is on no hold (on its
 * way over something, or a hand on a knee). Between keys every point eases, and a
 * foot or hand that moves to a new hold is lifted over the way (`lift`, metres). A vehicle
 * that can be climbed from either side (`sides`) is climbed from the visitor's: the keys are
 * mirrored across its middle. The figure is posed by rider-pose.js's reaching on the contract
 * skeleton: the pelvis on its place, each leg from the hip to its foot, each arm to its hand.
 *
 * This file's plan (planBoard, boardAt, boardEye) is plain arithmetic, so the tests run it
 * without three.js; createBoardFigure is the drawn figure. A reconstructed motion
 * (docs/LIBERTIES.md L-board-climb-3560), never a claim about anyone's journey.
 */
import * as THREE from 'three';
import { createRiderPose } from './rider-pose.js';
import { enuToWorld } from './terrain.js';

const DEG = Math.PI / 180;
const smooth = t => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;
const turn = (from, to) => ((to - from + 540) % 360) - 180;
const wrap = h => ((h % 360) + 360) % 360;
/** Seconds the eye takes at the least to go out beside the vehicle, and back in to the seat (or
 *  the walk's end); and the pace it goes at the most on the way, on average (m/s). */
export const EYE_EASE_S = 0.9, EYE_M_S = 4.5;
/** Closer than this to the figure's head, the eye is inside him: he is not drawn. */
export const HIDE_NEAR_M = 0.75;
/** A foot or hand moving to a new hold is lifted this far over the way, unless the key says. */
const FOOT_LIFT_M = 0.1, HAND_LIFT_M = 0.05;
const LIMBS = ['foot_l', 'foot_r', 'hand_l', 'hand_r'];

/** The climb for a team's row: the first `vehicles` entry whose `match` is in its vehicle file. */
export function boardSpecFor(config, row, kind = 'box') {
  const file = `${row?.vehicle_file ?? ''}`;
  return (config?.vehicles ?? []).find(v => v.seat === kind && file.includes(v.match)) ?? null;
}

/** A key mirrored to the vehicle's right (side -1): x reflected across `centre` (the vehicle's
 *  middle, where its body is not quite on its root's), left and right swapped, the turn reversed. */
export function mirrorKey(key, side, centre = 0) {
  if (side !== -1) return key;
  const flip = p => (Array.isArray(p) ? [2 * centre - p[0], p[1], p[2]] : p);
  const out = { ...key, face: -(key.face ?? 0), pelvis: flip(key.pelvis) };
  out.foot_l = flip(key.foot_r); out.foot_r = flip(key.foot_l);
  out.hand_l = flip(key.hand_r); out.hand_r = flip(key.hand_l);
  if (key.lift) out.lift = { foot_l: key.lift.foot_r, foot_r: key.lift.foot_l, hand_l: key.lift.hand_r, hand_r: key.lift.hand_l };
  const other = { foot_l: 'foot_r', foot_r: 'foot_l', hand_l: 'hand_r', hand_r: 'hand_l' };
  if (Array.isArray(key.air)) out.air = key.air.map(l => other[l] ?? l);
  return out;
}

/**
 * The plan of one climb up (`mode: 'up'`) or down ('down'), in the world, while the team stands.
 *
 *   spec      a boarding.json `vehicles` entry
 *   toWorld   ([x, y, z]) => { e, n, y }: the team's vehicle-root local point in the world
 *   heading   the team's compass bearing (degrees)
 *   from      up: the visitor's eye { e, n, y, bearing, pitch }; where the walk starts
 *   seat      the seat eye { e, n, y } (ride.seatOf)
 *   land      down: where the walk ends ({ e, n }), else the stand
 *   ground    (e, n) => the ground's height, or NaN
 *   standable (e, n) => true where the eye may stand to watch
 *   figure    { pelvis_m, eye_m }: the figure's standing pelvis and eye over its soles
 *   walk_m_s  the walk's pace
 * Null when the spec has no keys, or the visitor's side is not one the vehicle is climbed from
 * and there is no way round.
 */
export function planBoard({ spec, toWorld, heading, from = null, seat = null, land = null, ground = () => NaN,
  standable = () => true, figure = { pelvis_m: 0.95, eye_m: 1.6 }, walk_m_s = 1.3, mode = 'up', local = null } = {}) {
  if (!spec?.keys?.length || typeof toWorld !== 'function' || !Number.isFinite(heading)) return null;
  const at = p => toWorld(p);
  const groundAt = (e, n, fallback) => { const g = ground(e, n); return Number.isFinite(g) ? g : fallback; };
  // The visitor's side: the one they stand on, if the vehicle is climbed from it; else its first.
  const sides = Array.isArray(spec.sides) && spec.sides.length ? spec.sides : [1];
  let side = sides[0];
  const visitorLocal = local && from ? local(from.e, from.n) : null;
  if (visitorLocal && sides.includes(Math.sign(visitorLocal[0]) || 1)) side = Math.sign(visitorLocal[0]) || 1;
  const centre = side === -1 ? spec.mirror_x_m ?? 0 : 0;
  const keys = spec.keys.map(k => mirrorKey(k, side, centre));
  const [sx, sz] = spec.stand_xz_m;
  const sideX = x => (side === -1 ? 2 * centre - x : x);
  const standLocal = [sideX(sx), 0, sz];
  const standW = at(standLocal);
  const stand = { e: standW.e, n: standW.n, y: groundAt(standW.e, standW.n, standW.y) };
  // The walk: straight to the stand, or round behind the vehicle from its other side.
  const walk = [];
  const start = mode === 'up' ? from : null;
  if (start && Number.isFinite(start.e)) {
    walk.push({ e: start.e, n: start.n });
    if (visitorLocal && Math.sign(visitorLocal[0]) !== side && Math.abs(visitorLocal[0]) > 0.2) {
      const rz = spec.rear_z_m ?? -2.4;
      for (const p of [[visitorLocal[0], 0, Math.min(rz, visitorLocal[1])], [sideX(Math.max(sx, 1.2)), 0, rz]]) { const w = at(p); walk.push({ e: w.e, n: w.n }); }
    }
    walk.push({ e: stand.e, n: stand.n });
  } else if (mode === 'down' && land && Number.isFinite(land.e)) {
    walk.push({ e: stand.e, n: stand.n }, { e: land.e, n: land.n });
  }
  let walk_m = 0;
  for (let i = 1; i < walk.length; i++) walk_m += Math.hypot(walk[i].e - walk[i - 1].e, walk[i].n - walk[i - 1].n);
  if (walk_m < 0.3) { walk.length = 0; walk_m = 0; }
  const walk_s = walk_m / Math.max(0.3, walk_m_s);
  const climb_s = Math.max(0.5, Number(spec.seconds) || 3);
  // Each key in the world: points through the vehicle, the facing as a compass bearing.
  const W = p => { if (!Array.isArray(p)) return null; const w = at(p); return { e: w.e, n: w.n, y: w.y }; };
  const world = keys.map(k => ({
    at: k.at, face: wrap(heading + (k.face ?? 0)), lean: k.lean ?? 0, knee: k.knee ?? null, lift: k.lift ?? {}, air: k.air ?? [],
    pelvis: W(k.pelvis), foot_l: W(k.foot_l), foot_r: W(k.foot_r), hand_l: W(k.hand_l), hand_r: W(k.hand_r),
  }));
  // The watch: out beside the stand and back along the vehicle, on ground the eye may stand on.
  const wm = spec.watch_m ?? { out: 2.4, up: 1.75, back: 2.6 };
  let watch = null;
  for (const k of [1, 0.7, 0.45]) {
    const w = at([sideX(sx + wm.out * k), 0, sz - wm.back * k]);
    let fine = false;
    try { fine = !!standable(w.e, w.n); } catch { fine = false; }
    if (fine) { watch = { e: w.e, n: w.n, y: groundAt(w.e, w.n, stand.y) + wm.up }; break; }
  }
  const T = walk_s + climb_s;
  const arrive = walk.length >= 2 ? (() => { const a = walk.at(-2), b = walk.at(-1); return wrap(Math.atan2(b.e - a.e, b.n - a.n) / DEG); })() : null;
  const landAt = mode === 'down' ? (walk.length ? walk.at(-1) : { e: stand.e, n: stand.n }) : null;
  return { mode, side, spec, stand, walk, walk_m, walk_s, climb_s, seconds: T, keys: world, watch, from, seat, figure,
    arrive, land: landAt, landY: landAt ? groundAt(landAt.e, landAt.n, stand.y) : null };
}

const along = (pts, d) => {
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], len = Math.hypot(b.e - a.e, b.n - a.n);
    if (d <= len || i === pts.length - 1) {
      const f = len > 1e-9 ? Math.min(1, d / len) : 1;
      return { e: lerp(a.e, b.e, f), n: lerp(a.n, b.n, f), heading: wrap(Math.atan2(b.e - a.e, b.n - a.n) / DEG) };
    }
    d -= len;
  }
  return { e: pts[0].e, n: pts[0].n, heading: 0 };
};

/** A standing figure's pelvis at (e, n), on the ground there. */
const standingPelvis = (plan, e, n) => ({ e, n, y: plan.stand.y + plan.figure.pelvis_m });

/**
 * The climb `c` (0..1, through the keys) as one pose: the pelvis, feet, hands (world points,
 * or null), how far each limb has gone to its rest (`rest`: 1 standing or hanging, 0 on its
 * point), facing and lean. The first key before any is the figure standing
 * at the stand as the walk left him.
 */
export function climbPose(plan, c) {
  const keys = plan.keys;
  const first = { at: 0, face: plan.arrive ?? keys[0].face, lean: 0, knee: null, lift: {}, pelvis: null, foot_l: null, foot_r: null, hand_l: null, hand_r: null };
  const list = keys[0].at > 0 ? [first, ...keys] : keys;
  let i = 0;
  while (i < list.length - 2 && c > list[i + 1].at) i++;
  const a = list[i], b = list[Math.min(i + 1, list.length - 1)];
  const f = b === a ? 1 : smooth((c - a.at) / Math.max(1e-6, b.at - a.at));
  // A limb between two holds eases from one to the other; to or from none (standing, hanging)
  // it keeps the hold it has and eases toward its rest by `rest` (0 the hold, 1 its rest).
  const rest = {};
  const point = (limb, pa, pb, lift) => {
    if (!pa && !pb) { rest[limb] = 1; return null; }
    if (!pa || !pb) { rest[limb] = pa ? f : 1 - f; return pa ?? pb; }
    rest[limb] = 0;
    const moved = Math.hypot(pb.e - pa.e, pb.n - pa.n, pb.y - pa.y) > 0.02;
    return { e: lerp(pa.e, pb.e, f), n: lerp(pa.n, pb.n, f), y: lerp(pa.y, pb.y, f) + (moved ? lift * Math.sin(Math.PI * f) : 0) };
  };
  const stand = plan.stand;
  const pa = a.pelvis ?? standingPelvis(plan, stand.e, stand.n), pb = b.pelvis ?? standingPelvis(plan, stand.e, stand.n);
  const out = {
    face: wrap(a.face + turn(a.face, b.face) * f), lean: lerp(a.lean, b.lean, f),
    knee: a.knee || b.knee ? (() => {
      const ka = a.knee ?? { forward: 0.6, out: 0.25, up: -0.1 }, kb = b.knee ?? { forward: 0.6, out: 0.25, up: -0.1 };
      return { forward: lerp(ka.forward, kb.forward, f), out: lerp(ka.out, kb.out, f), up: lerp(ka.up ?? -0.1, kb.up ?? -0.1, f) };
    })() : { forward: 0.6, out: 0.25, up: -0.1 },
    pelvis: { e: lerp(pa.e, pb.e, f), n: lerp(pa.n, pb.n, f), y: lerp(pa.y, pb.y, f) },
  };
  for (const limb of LIMBS) out[limb] = point(limb, a[limb], b[limb], b.lift?.[limb] ?? (limb.startsWith('foot') ? FOOT_LIFT_M : HAND_LIFT_M));
  out.rest = rest;
  return out;
}

/**
 * Where the figure is at `u` (0..1 of the whole plan): walking ({ stage: 'walk', e, n,
 * heading }) or climbing ({ stage: 'climb', ...climbPose }). Up walks first, then climbs;
 * down climbs (the keys backwards), then walks.
 */
export function boardAt(plan, u) {
  const t = Math.max(0, Math.min(1, u)) * plan.seconds;
  const walking = plan.mode === 'up' ? t < plan.walk_s : t > plan.climb_s;
  if (walking && plan.walk.length >= 2) {
    const s = plan.mode === 'up' ? t : t - plan.climb_s;
    return { stage: 'walk', ...along(plan.walk, Math.min(plan.walk_m, s / Math.max(1e-6, plan.walk_s) * plan.walk_m)) };
  }
  const c = plan.mode === 'up' ? (t - plan.walk_s) / plan.climb_s : 1 - t / plan.climb_s;
  return { stage: 'climb', ...climbPose(plan, Math.max(0, Math.min(1, c))) };
}

/** The figure's head (world) at a pose from boardAt: over the pelvis by the standing eye's rise. */
export function headOf(plan, pose) {
  if (pose.stage === 'walk') return { e: pose.e, n: pose.n, y: plan.stand.y + plan.figure.eye_m };
  return { e: pose.pelvis.e, n: pose.pelvis.n, y: pose.pelvis.y + (plan.figure.eye_m - plan.figure.pelvis_m) * (1 - 0.15 * pose.lean) };
}

const lookFrom = (eye, at) => {
  const de = at.e - eye.e, dn = at.n - eye.n, dy = at.y - eye.y, flat = Math.hypot(de, dn);
  return { bearing: wrap(Math.atan2(de, dn) / DEG), pitch: Math.atan2(dy, Math.max(1e-6, flat)) };
};

/**
 * The visitor's eye at `u`: up, from where they stood out to the watch (EYE_EASE_S), there
 * looking at the figure as he walks and climbs, and over the last EYE_EASE_S into the seat,
 * turning to the team's heading. Down: from the seat out to the watch, and at the end down to
 * the figure's eye where the walk ends. `hide` is true while the eye is inside him.
 * { e, n, y, bearing, pitch (radians), hide }.
 */
export function boardEye(plan, u, { heading = 0 } = {}) {
  const pose = boardAt(plan, u), head = headOf(plan, pose);
  const chest = { e: head.e, n: head.n, y: head.y - 0.45 };
  const t = Math.max(0, Math.min(1, u)) * plan.seconds, T = plan.seconds;
  const watch = plan.watch ?? (plan.mode === 'up' ? plan.from : null) ?? plan.seat;
  const startEye = plan.mode === 'up' ? plan.from : plan.seat;
  const endEye = plan.mode === 'up' ? plan.seat
    : { e: plan.land.e, n: plan.land.n, y: plan.landY + plan.figure.eye_m };
  // Out and in at no more than EYE_M_S on the way (EYE_EASE_S at the least).
  const dist = (a, b) => (a && b ? Math.hypot(a.e - b.e, a.n - b.n, a.y - b.y) : 0);
  const easeIn = Math.min(Math.max(EYE_EASE_S, dist(startEye, watch) / EYE_M_S), T * 0.35);
  const easeOut = Math.min(Math.max(EYE_EASE_S, dist(watch, endEye) / EYE_M_S), T * 0.35);
  const endLook = plan.mode === 'up' ? { bearing: wrap(heading), pitch: -0.08 }
    : { bearing: pose.stage === 'walk' ? pose.heading : wrap(heading), pitch: -0.05 };
  const startLook = plan.mode === 'up' ? { bearing: plan.from?.bearing ?? 0, pitch: plan.from?.pitch ?? 0 } : { bearing: wrap(heading), pitch: -0.08 };
  let eye, look;
  const blend = (la, lb, k) => ({ bearing: wrap(la.bearing + turn(la.bearing, lb.bearing) * k), pitch: lerp(la.pitch, lb.pitch, k) });
  if (t < easeIn && startEye) {
    const k = smooth(t / easeIn);
    eye = { e: lerp(startEye.e, watch.e, k), n: lerp(startEye.n, watch.n, k), y: lerp(startEye.y, watch.y, k) };
    look = blend(startLook, lookFrom(eye, chest), k);
  } else if (t > T - easeOut && endEye) {
    const k = smooth((t - (T - easeOut)) / easeOut);
    eye = { e: lerp(watch.e, endEye.e, k), n: lerp(watch.n, endEye.n, k), y: lerp(watch.y, endEye.y, k) };
    look = blend(lookFrom(eye, chest), endLook, k);
  } else {
    eye = { e: watch.e, n: watch.n, y: watch.y };
    look = lookFrom(eye, chest);
  }
  const near = Math.hypot(eye.e - head.e, eye.n - head.n, eye.y - head.y) < HIDE_NEAR_M;
  return { ...eye, bearing: look.bearing, pitch: look.pitch, hide: near || u >= 1 || (plan.mode === 'down' && u <= 0) };
}

/**
 * Bind a figure standing in its first pose (`scene` its bones, `root` its root at the origin,
 * unturned) for posing: rider-pose.js's reaching, and where its standing pose has its pelvis,
 * eye, ankles, feet and hands. Null on a rig that is not the contract skeleton.
 */
export function bindBoardFigure(scene, root) {
  root.updateMatrixWorld(true);
  const pose = createRiderPose(scene, root);
  if (!pose) return null;
  const y = b => b.getWorldPosition(new THREE.Vector3()).y - root.position.y;
  const ankle = (y(pose.bones.foot_l) + y(pose.bones.foot_r)) / 2;
  const eye = pose.bones.head ? y(pose.bones.head) + 0.07 : 1.6;
  // Where the standing pose has each foot and hand from the pelvis, in the figure's own frame
  // (x his left, z ahead: unturned he faces +z, as humans.js turns its figures).
  const p0 = pose.bones.pelvis.getWorldPosition(new THREE.Vector3()), rest = {};
  for (const s of ['l', 'r']) for (const part of ['foot', 'hand']) rest[`${part}_${s}`] = pose.bones[`${part}_${s}`].getWorldPosition(new THREE.Vector3()).sub(p0);
  return { pose, root, ankle_m: ankle, pelvis_m: y(pose.bones.pelvis), eye_m: eye, rest };
}

const V = p => enuToWorld(p.e, p.n, p.y, new THREE.Vector3());
const UP = new THREE.Vector3(0, 1, 0);
/**
 * Pose a bound figure (bindBoardFigure) at a climbing pose from boardAt: turned to its facing,
 * the pelvis on its place (never further from a planted foot than the leg reaches), each
 * ankle over its sole, each hand on its hold or hanging. Returns rider-pose's shortfalls.
 */
export function poseBoardFigure(fig, at) {
  const { pose, root } = fig;
  // Facing a compass bearing as the layer faces its figures (humans.js headingToYaw).
  const yaw = Math.PI - at.face * DEG;
  root.rotation.set(0, yaw, 0);
  const forward = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
  const left = new THREE.Vector3().crossVectors(UP, forward).normalize();
  const pelvis = V(at.pelvis);
  // Without a hold, a foot stands and a hand hangs where the standing pose has it.
  const rest = off => pelvis.clone().addScaledVector(left, off.x).addScaledVector(forward, off.z).add(new THREE.Vector3(0, off.y, 0));
  const toward = (limb, held, off) => {
    const w = at.rest?.[limb] ?? (at[limb] ? 0 : 1), free = rest(off);
    return held && w < 1 ? held.lerp(free, smooth(w)) : free;
  };
  const footOf = s => toward(`foot_${s}`, at[`foot_${s}`] ? V(at[`foot_${s}`]).add(new THREE.Vector3(0, fig.ankle_m, 0)) : null, fig.rest[`foot_${s}`]);
  const handOf = s => toward(`hand_${s}`, at[`hand_${s}`] ? V(at[`hand_${s}`]) : null, fig.rest[`hand_${s}`]);
  const feet = { l: footOf('l'), r: footOf('r') }, hands = { l: handOf('l'), r: handOf('r') };
  const reachM = pose.legLength * 0.97;
  for (let pass = 0; pass < 2; pass++) for (const s of ['l', 'r']) {
    const d = pelvis.clone().sub(feet[s]);
    if (d.length() > reachM) pelvis.copy(feet[s]).addScaledVector(d.normalize(), reachM);
  }
  return { short: pose.apply({ seat: pelvis, feet, hands, forward, up: UP, lean: at.lean, knee: at.knee }), feet, hands, pelvis };
}

/**
 * The drawn figure (three.js): a period figure of the year, made as the people layer makes its
 * figures (`humans().createActor`), posed each frame at the plan's `u`. One per scene.
 *   humans     () => the people layer       group   where the figure is drawn
 *   asset      () => the figure's asset id (the year's, or the visitor's own once chosen)
 *   lod        the level it is drawn at
 */
export function createBoardFigure({ humans = () => null, group = null, asset = () => null, lod = 1, why = '', liberty = '', problems = [] } = {}) {
  let fig = null, building = null, failed = false, plan = null, u = 0, walking = false;
  const hide = () => { if (fig) fig.actor.root.visible = false; };
  async function build() {
    const layer = humans();
    const id = asset();
    if (!layer?.createActor || !id || !group) throw Error('boarding: no people layer or figure');
    const instance = { id: 'visitor:boarding', contract_version: 1, display: 'shown', scene: null, appearance: { asset_id: id },
      placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' }, behaviour: { state: 'standing' },
      animation: { clip: 'idle', loop: true, phase: 0 }, lod: { policy: 'fixed', fixed: lod },
      interaction: { opens: 'none', selectable: false },
      provenance: { grade: 'reconstructed', basis: why, liberty } };
    const actor = layer.createActor(instance, { identity: { kind: 'anonymous', personId: null, person: null, profile: null, role: null } });
    try {
      await actor.setLod(lod);
      if (!actor.body) throw Error('boarding: the figure did not load');
      actor.play('idle', { fade: 0, time: 0 }); actor.body.mixer.update(0);
      actor.root.position.set(0, 0, 0); actor.root.rotation.set(0, 0, 0);
      group.add(actor.root);
      actor.root.updateMatrixWorld(true);
      const bound = bindBoardFigure(actor.body.scene, actor.root);
      if (!bound) throw Error('boarding: the figure is not the contract skeleton');
      for (const m of actor.body.meshes ?? []) m.frustumCulled = false;
      actor.root.visible = false;
      fig = { ...bound, actor, id };
      return fig;
    } catch (error) { actor.dispose(); actor.root.removeFromParent(); throw error; }
  }
  function posed(dt, cameraPosition) {
    const { actor } = fig;
    const at = boardAt(plan, u);
    if (at.stage === 'walk') {
      // Walking: the layer's own walk (its clip, gait and life), led along the plan's way.
      actor.tow = () => ({ e: at.e, n: at.n, heading: at.heading });
      if (!walking) { fig.pose.release(); actor.setState?.('walking'); walking = true; }
      actor.update(dt, cameraPosition ?? actor.root.position);
      return;
    }
    if (walking) { actor.tow = null; actor.setState?.('standing'); walking = false; }
    poseBoardFigure(fig, at);
    for (const m of actor.body.meshes ?? []) m.skeleton?.update?.();
  }
  return {
    get ready() { return !!fig && fig.id === asset(); },
    get figure() { return fig ? { pelvis_m: fig.pelvis_m, eye_m: fig.eye_m } : null; },
    get failed() { return failed; },
    /** Start loading the figure (once); resolves true when it can be drawn. */
    prepare() {
      if (fig && fig.id === asset()) return Promise.resolve(true);
      if (fig) { fig.actor.dispose(); fig.actor.root.removeFromParent(); fig = null; }
      if (!building) building = build().then(() => true, error => { failed = true; problems.push(`boarding: ${error.message}`); return false; }).finally(() => { building = null; });
      return building;
    },
    /** Draw the figure at `at` (0..1) of `p` from now on; null hides it. */
    show(p, at, { hidden = false } = {}) { plan = p; u = at; if (fig) fig.hidden = hidden; if (!p) hide(); },
    update(dt, cameraPosition = null) {
      if (!fig) return;
      if (!plan || fig.hidden) { hide(); if (walking) { fig.actor.tow = null; walking = false; } return; }
      try { posed(Number.isFinite(dt) ? dt : 0, cameraPosition); fig.actor.root.visible = true; }
      catch (error) { problems.push(`boarding: ${error.message}`); plan = null; hide(); }
    },
    dispose() { if (fig) { fig.actor.dispose(); fig.actor.root.removeFromParent(); fig = null; } plan = null; },
  };
}
