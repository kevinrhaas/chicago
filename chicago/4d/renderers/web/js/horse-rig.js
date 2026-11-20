// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * horse-rig.js — the driven current26 horse's gaits and distance levels (T-3559).
 *
 * GAITS. The walk (tools/horse_walk_v2.mjs, T-2803), the trot (the same tool, T-3559) and the
 * canter and gallop (the same tool, T-3560) are in-place clips played by travelled metres:
 * time = (metres / cycle_m mod 1) * duration. A horse carries them all; `createHorseGait`
 * blends them by pace (`gaitLevel`), each advanced by the SAME metres on its own cycle, so in
 * any gait a stance hoof moves back exactly as fast as the ground goes by. The walk stays as
 * delivered below WALK_TOP_M_S; the trot is full from TROT_FULL_M_S, the canter from
 * CANTER_FULL_M_S, the gallop from GALLOP_FULL_M_S.
 *
 * LEVELS. `horse-current26-mid.glb` and `-far.glb` (tools/transport/horse_lods/) are the near
 * horse's own skin, inverse binds and material names under fewer triangles and smaller maps.
 * `attachHorseLods` binds their meshes to a near clone's bones, so one skeleton, one gait and
 * one coat drive all three and a swap changes nothing but triangles and map size; the swap
 * distances keep a band between switching up and down so a horse at the line does not flicker.
 */
import * as THREE from 'three';

export const WALK_TOP_M_S = 1.6, TROT_FULL_M_S = 2.1, GAIT_CHANGE_S = .3;
/** T-3560 (Kevin, 2026-11-17: "gallop, run"): the canter and gallop bands (m/s). */
export const TROT_TOP_M_S = 3.6, CANTER_FULL_M_S = 4.2, CANTER_TOP_M_S = 6, GALLOP_FULL_M_S = 6.8;
/** Swap distances (m): beyond `mid` the mid mesh, beyond `far` the far; back inside less `band`. */
export const HORSE_LOD = Object.freeze({ mid: 22, far: 55, band: 3 });

const sha256Of = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(n => n.toString(16).padStart(2, '0')).join('');

/** An in-place gait clip, bound by its bytes to its file and by name, model and cycle to the horse. */
export async function loadGaitClip(url, { sha256, name, modelSha256, cycle_m }) {
  const response = await fetch(url);
  if (!response.ok) throw Error(`horse gait: HTTP${response.status}`);
  const bytes = await response.arrayBuffer();
  if (await sha256Of(bytes) !== sha256) throw Error('horse gait: clip differs from its binding');
  const clip = JSON.parse(new TextDecoder().decode(bytes));
  if (clip.schema !== 'chicago4d_inplace_walk_clip_v1' || clip.name !== name || clip.model_sha256 !== modelSha256
    || clip.cycle_m !== cycle_m || !(clip.duration_s > 0) || !Array.isArray(clip.tracks) || !clip.tracks.length) {
    throw Error('horse gait: clip lacks the in-place travel contract');
  }
  return clipFromJson(clip);
}

export function clipFromJson(clip) {
  return new THREE.AnimationClip(clip.name, clip.duration_s, clip.tracks.map(t => t.type === 'quaternion'
    ? new THREE.QuaternionKeyframeTrack(t.name, t.times, t.values) : new THREE.VectorKeyframeTrack(t.name, t.times, t.values)));
}

/** The trot's share at a pace (0 walk .. 1 trot), smooth between the two. */
export function trotShare(speed_m_s) { return band(speed_m_s, WALK_TOP_M_S, TROT_FULL_M_S); }
const band = (speed_m_s, from, full) => {
  const x = Math.min(1, Math.max(0, (Math.abs(speed_m_s) - from) / (full - from)));
  return x * x * (3 - 2 * x);
};
/**
 * The gait for a pace, as a level: 0 walk, 1 trot, 2 canter, 3 gallop, blended across each
 * band. The trot is whole from 2.1 to TROT_TOP_M_S, the canter from CANTER_FULL_M_S to
 * CANTER_TOP_M_S, the gallop from GALLOP_FULL_M_S.
 */
export function gaitLevel(speed_m_s) {
  return trotShare(speed_m_s) + band(speed_m_s, TROT_TOP_M_S, CANTER_FULL_M_S) + band(speed_m_s, CANTER_TOP_M_S, GALLOP_FULL_M_S);
}
export const GAIT_NAMES = Object.freeze(['walk', 'trot', 'canter', 'gallop']);

/**
 * Every gait on one horse's mixer. `advance(step_m, speed_m_s, dt)` moves each gait by the same
 * signed metres on its own cycle and eases the level toward the pace's; then the pose is
 * written (mixer.update(0)). Without a trot it is the walk alone, exactly as before.
 */
export function createHorseGait(root, { walk, walkCycle_m, trot = null, trotCycle_m = null, canter = null, canterCycle_m = null,
  gallop = null, gallopCycle_m = null, mixer = null, gait_m = 0, rest = false }) {
  if (!walk || !(walkCycle_m > 0) || (trot && !(trotCycle_m > 0)) || (canter && !(trot && canterCycle_m > 0))
    || (gallop && !(canter && gallopCycle_m > 0))) throw Error('horse gait: a walk and its cycle required (each faster gait needs the one below it)');
  mixer ??= new THREE.AnimationMixer(root);
  // The gaits a horse has, slowest first; a canter needs a trot below it, a gallop a canter.
  const gaits = [[walk, walkCycle_m], [trot, trotCycle_m], [canter, canterCycle_m], [gallop, gallopCycle_m]]
    .filter(([clip]) => clip).map(([clip, cycle]) => ({ clip, cycle, action: mixer.clipAction(clip).setLoop(THREE.LoopRepeat, Infinity).play() }));
  for (const g of gaits) { g.action.paused = true; g.action.setEffectiveWeight(g === gaits[0] ? 1 : 0); }
  const top = gaits.length - 1;
  // `rest`: a horse that stops stands square in its own rest pose (the GLB's, which the tack
  // was fitted to), the gaits' weights easing out over GAIT_CHANGE_S; a team keeps its walk.
  // `level` runs 0 (walk) .. 1 (trot) .. 2 (canter) .. 3 (gallop); between two whole levels
  // the two gaits are blended. With a walk and a trot alone it is the trot's share, as before.
  let distance = gait_m, level = 0, moving = rest ? 0 : 1;
  const phase = (d, c) => ((d / c) % 1 + 1) % 1;
  const weightOf = i => Math.max(0, 1 - Math.abs(level - i));
  const write = () => {
    for (const [i, g] of gaits.entries()) {
      g.action.time = phase(distance, g.cycle) * g.clip.duration;
      g.action.setEffectiveWeight(weightOf(i) * moving);
    }
    mixer.update(0);
  };
  write();
  return {
    mixer, walkAction: gaits[0].action, trotAction: gaits[1]?.action ?? null,
    canterAction: gaits[2]?.action ?? null, gallopAction: gaits[3]?.action ?? null,
    get distance() { return distance; },
    get trot() { return gaits[1] ? weightOf(1) : 0; },
    /** 0 walk .. 3 gallop, eased (only as far as this horse's gaits go). */
    get level() { return level; },
    /** The gait it is mostly in: 'walk', 'trot', 'canter' or 'gallop'. */
    get name() { return GAIT_NAMES[Math.round(level)]; },
    /** Where in its stride that gait is, 0..1 (a rider moves with it, riding.js riderLife). */
    get phase() { return phase(distance, gaits[Math.min(top, Math.round(level))].cycle); },
    /** 0 standing in the rest pose .. 1 in its gait (always 1 without `rest`). */
    get moving() { return moving; },
    /** Signed metres (backing is negative), the pace, and the frame's time for easing the blend. */
    advance(step_m, speed_m_s, dt = 0) {
      distance += Number.isFinite(step_m) ? step_m : 0;
      if (top > 0) {
        const want = Math.min(top, gaitLevel(speed_m_s));
        // At most a third of a second from one gait to the next: quick, but never a jump
        // between two leg orders. Without a clock (a first frame, a jump) it is the pace's.
        level = dt > 0 ? level + Math.max(-dt / GAIT_CHANGE_S, Math.min(dt / GAIT_CHANGE_S, want - level)) : want;
      }
      if (rest) {
        const want = Math.abs(speed_m_s) > .05 || Math.abs(step_m) > 1e-4 ? 1 : 0;
        moving = dt > 0 ? moving + Math.max(-dt / GAIT_CHANGE_S, Math.min(dt / GAIT_CHANGE_S, want - moving)) : want;
      }
      write();
    },
    dispose() { mixer.stopAllAction(); mixer.uncacheRoot(root); },
  };
}

/**
 * Bind the mid and far templates' meshes to a near clone (`root`, a SkeletonUtils clone of the
 * near horse) on its own bones, beside its own meshes. `templates` = { mid, far }: parsed GLTFs.
 * Returns { level, update(distance_m), set(level), dispose() }. The coat (horse-appearance.js)
 * is applied after this, so all three levels share one individual.
 */
export function attachHorseLods(root, templates, { sourceSha256, lod = HORSE_LOD } = {}) {
  const bones = new Map();
  root.traverse(n => { if (n.isBone) bones.set(n.name, n); });
  const near = [];
  root.traverse(n => { if (n.isSkinnedMesh) near.push(n); });
  const levels = { near, mid: [], far: [] };
  for (const level of ['mid', 'far']) {
    const template = templates?.[level];
    if (!template) continue;
    template.scene.updateMatrixWorld(true);
    template.scene.traverse(src => {
      if (!src.isSkinnedMesh) return;
      const twin = near.find(n => n.material?.name === src.material?.name);
      if (!twin) throw Error(`horse levels: no near mesh for ${src.material?.name}`);
      const skeleton = new THREE.Skeleton(src.skeleton.bones.map(b => {
        const bone = bones.get(b.name);
        if (!bone) throw Error(`horse levels: the near rig lacks ${b.name}`);
        return bone;
      }), src.skeleton.boneInverses.map(m => m.clone()));
      const mesh = new THREE.SkinnedMesh(src.geometry, src.material);
      mesh.name = `${src.name}:${level}`;
      mesh.position.copy(twin.position); mesh.quaternion.copy(twin.quaternion); mesh.scale.copy(twin.scale);
      mesh.bindMode = src.bindMode;
      mesh.bind(skeleton, src.bindMatrix.clone());
      mesh.frustumCulled = false; mesh.visible = false;
      mesh.castShadow = twin.castShadow; mesh.receiveShadow = twin.receiveShadow;
      mesh.userData.chicagoHorseLod = { level, source_sha256: sourceSha256 };
      twin.parent.add(mesh);
      levels[level].push(mesh);
    });
  }
  let current = 'near';
  const set = level => {
    if (!levels[level]?.length) level = level === 'far' && levels.mid.length ? 'mid' : 'near';
    if (level === current) return current;
    for (const [name, meshes] of Object.entries(levels)) for (const m of meshes) m.visible = name === level;
    current = level;
    return current;
  };
  return {
    levels,
    get level() { return current; },
    set,
    /** The level for a viewer `distance_m` away, with the band against flicker at a line. */
    update(distance_m) {
      if (!Number.isFinite(distance_m)) return current;
      const rank = { near: 0, mid: 1, far: 2 }[current];
      const want = distance_m > lod.far + (rank < 2 ? 0 : -lod.band) ? 'far'
        : distance_m > lod.mid + (rank < 1 ? 0 : -lod.band) ? 'mid' : 'near';
      return set(want);
    },
    dispose() {
      for (const level of ['mid', 'far']) for (const m of levels[level]) { m.skeleton.dispose(); m.removeFromParent(); }
    },
  };
}
