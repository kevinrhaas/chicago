// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * riding.js — ride a horse (T-3560).
 *
 * The owner, 2026-11-17: "definite prioritize the horse riding". A saddle horse stands near
 * where the visitor arrives in each year (data/transport/riding/saddle_horses.json `rows`):
 * the driven teams' photographic horse (current26, with its mid and far levels, coat, walk and
 * trot: horse-rig.js), saddled and bridled for its year (saddlery.js), with a period figure in
 * the saddle while the visitor rides (rider-pose.js). Interact (R, or the key) on the horse:
 * Mount. Then the movement keys are the reins:
 *
 *   W / stick up        walk on (held); with Shift, or the stick pushed right up, trot
 *   S / stick down      stop; held from a stand, back a few steps
 *   A D / sideways      turn (a horse turns on the spot too, slowly)
 *   V, or Interact      the view: from behind the horse (the default) or from the saddle
 *   Get down            the travel bar's key, Interact's list, or flying (F)
 *
 * The horse goes only where a visitor could stand: every point round its body (the footprint
 * in `ride.footprint_m`) must be standable ground (not water, not inside a building's walls)
 * and not too steep; what stops it is said once ("Held: a wall"). Getting down puts the
 * visitor on standable ground on the near side, else the off side, else behind, else the
 * nearest found. Reduced motion: the eye does not rise and fall with the horse's back.
 *
 * The horse and its rider are loaded only when the visitor comes within LOAD_M of one, and
 * let go past DROP_M; phones load the capped near maps and the far level, as the teams do.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { loadMeshoptDecoder } from './scene-loader.js';
import { enuToWorld } from './terrain.js';
import { bearingToYaw } from './angles.js';
import { acquireDraftHorse, draftHorseTextureCap } from './draft-horse-assets.js';
import { loadHorseRecipe, applyHorseAppearance } from './horse-appearance.js';
import { attachHorseLods, createHorseGait, loadGaitClip } from './horse-rig.js';
import { fitTack } from './saddlery.js';
import { createRiderPose, saddleTargets } from './rider-pose.js';

const DEG = Math.PI / 180;
export const LOAD_M = 90, DROP_M = 140;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const turn = (a, b) => ((b - a + 540) % 360) - 180;

/** The horse root's yaw for a compass bearing: its +z (ahead) to that bearing in the world. */
export const horseYaw = bearing => Math.PI - bearing * DEG;

/** ENU of a point `x` to the horse's left (near side) and `z` ahead of (e, n) facing `bearing`. */
export function horseLocal(e, n, bearing, x, z) {
  const b = bearing * DEG, fe = Math.sin(b), fn = Math.cos(b);
  return { e: e + fe * z - fn * x, n: n + fn * z + fe * x };
}

/** The points round the horse's body that must stand on open ground. */
export function footprintPoints(e, n, bearing, fp) {
  const pts = [];
  for (const z of [-fp.behind, 0, fp.ahead * .5, fp.ahead]) for (const x of [-fp.half_width, fp.half_width]) pts.push(horseLocal(e, n, bearing, x, z));
  return pts;
}

/**
 * Why a horse cannot stand at (e, n, bearing), or null. `standable(e, n)` (main.js's, the
 * walker's own: not water, not inside walls), `ground(e, n)` the height a hoof stands on.
 */
export function blockedAt(e, n, bearing, { standable, ground, footprint, max_step_m = .45 }) {
  const pts = footprintPoints(e, n, bearing, footprint);
  let lo = Infinity, hi = -Infinity;
  for (const p of pts) {
    if (!standable(p.e, p.n)) return 'in the way';
    const h = ground(p.e, p.n);
    if (!Number.isFinite(h)) return 'no ground';
    lo = Math.min(lo, h); hi = Math.max(hi, h);
  }
  return hi - lo > max_step_m ? 'too steep' : null;
}

/** The nearest spot to (e, n) where a horse facing `bearing` can stand, searching outward. */
export function findStand(e, n, bearing, ask, { reach = 40, step = 1.5 } = {}) {
  if (!blockedAt(e, n, bearing, ask)) return { e, n, bearing };
  for (let r = step; r <= reach; r += step) {
    const k = Math.max(8, Math.round(2 * Math.PI * r / step));
    for (let i = 0; i < k; i++) {
      const a = i / k * 2 * Math.PI, pe = e + Math.sin(a) * r, pn = n + Math.cos(a) * r;
      for (const b of [bearing, bearing + 90, bearing - 90, bearing + 180]) if (!blockedAt(pe, pn, b, ask)) return { e: pe, n: pn, bearing: (b + 360) % 360 };
    }
  }
  return null;
}

/** Where the rider gets down: the near side, the off side, behind, ahead; else the nearest. */
export function dismountSpot(pose, standable, { side_m = 1.3 } = {}) {
  for (const [x, z] of [[side_m, -.2], [-side_m, -.2], [0, -2.4], [side_m, 1.2], [-side_m, 1.2], [0, 2.8]]) {
    const p = horseLocal(pose.e, pose.n, pose.bearing, x, z);
    if (standable(p.e, p.n)) return p;
  }
  for (let r = 2; r <= 30; r += 1) for (let i = 0; i < 24; i++) {
    const a = i / 24 * 2 * Math.PI, e = pose.e + Math.sin(a) * r, n = pose.n + Math.cos(a) * r;
    if (standable(e, n)) return { e, n };
  }
  return null;
}

/**
 * The reins: speed and bearing for one step. `cmd` = { forward: -1..1, turn: -1..1, trot: bool }
 * from the keys or stick. Returns the new { speed, bearing } (no ground checks here).
 */
export function rein(state, cmd, dt, R) {
  let want = 0;
  if (cmd.forward > .15) want = cmd.trot ? R.trot_m_s : R.walk_m_s;
  else if (cmd.forward < -.15) want = state.speed > .2 ? 0 : -R.back_m_s;
  const a = want > state.speed ? R.accel_m_s2 : R.brake_m_s2;
  let speed = state.speed + clamp(want - state.speed, -a * dt, a * dt);
  if (Math.abs(speed) < .01 && want === 0) speed = 0;
  const rate = (speed > R.walk_m_s + .2 ? R.turn_trot_deg_s : R.turn_deg_s) * (Math.abs(speed) < .1 ? .6 : 1);
  const bearing = (state.bearing + clamp(cmd.turn, -1, 1) * rate * dt * (speed < -.05 ? -1 : 1) + 360) % 360;
  return { speed, bearing };
}

/**
 * Mount the riding layer for a scene. Returns null where the scene has no saddle horse.
 * @param {object} o
 *   sceneId · dataBase (the data/ base URL) · moduleBase (renderers/web/) · interactions ·
 *   standable (e, n) · ground (e, n) · visitor () => walker.state · humans () => the people layer
 *   (createActor) · say (text) · reducedMotion () · coarse (a memory-saving device) ·
 *   onMount (on) · problems []
 */
export async function mountRiding({ sceneId, dataBase, moduleBase = new URL('../', import.meta.url), interactions = null,
  standable, ground, visitor, humans = () => null, say = () => {}, reducedMotion = () => false, coarse = false,
  onMount = () => {}, problems = [] }) {
  sceneId = String(sceneId);
  const json = async file => { const r = await fetch(new URL(file, dataBase)); if (!r.ok) throw Error(`riding ${file}: HTTP${r.status}`); return r.json(); };
  const config = await json('transport/riding/saddle_horses.json');
  const rows = (config.rows ?? []).filter(r => r.scene === sceneId);
  if (!rows.length || !config.tack?.[sceneId]) return null;
  const loops = await json('transport/driven/loops.json');
  const spec = loops.horse_models?.[config.horse_model];
  if (!spec?.walk_clip_file) throw Error('riding: the saddle horse model is not in the driven horses');
  const R = config.ride, fit = config.fit;
  const group = new THREE.Group(); group.name = 'riding';
  const assetURL = file => new URL(file, moduleBase).href;
  const ask = { standable, ground, footprint: R.footprint_m };
  let loader = null, recipe = null, clips = null;
  const tools = async () => {
    if (!loader) {
      loader = new GLTFLoader();
      loader.setMeshoptDecoder(await loadMeshoptDecoder());
    }
    recipe ??= await loadHorseRecipe(dataBase, loops.horse_appearance.recipe_file);
    clips ??= await Promise.all([
      loadGaitClip(assetURL(spec.walk_clip_file), { sha256: spec.walk_clip_sha256, name: spec.walk_clip, modelSha256: spec.sha256, cycle_m: spec.stride_m }),
      spec.trot_clip_file ? loadGaitClip(assetURL(spec.trot_clip_file), { sha256: spec.trot_clip_sha256, name: spec.trot_clip, modelSha256: spec.sha256, cycle_m: spec.trot_stride_m }) : null,
    ]).catch(error => { clips = null; throw error; });
    return { loader, recipe, clips };
  };

  // Each saddle horse: its row, where it stands now, and (when near) what draws it.
  const horses = rows.map(row => {
    const at = findStand(row.at[0], row.at[1], row.bearing_deg, ask) ?? { e: row.at[0], n: row.at[1], bearing: row.bearing_deg };
    return { row, pose: { ...at, y: 0 }, speed: 0, built: null, building: null, thing: null };
  });

  async function build(h) {
    const { loader: L, recipe: coats, clips: [walk, trot] } = await tools();
    const levels = Object.keys(spec.lods ?? {}).filter(level => level === 'far' || !draftHorseTextureCap());
    const leases = await Promise.all([spec, ...levels.map(l => spec.lods[l])].map(s => acquireDraftHorse({ url: assetURL(s.file), sha256: s.sha256,
      materialVariant: spec.material_variant, loader: L })));
    const out = { leases, root: null, lods: null, coat: null, gait: null, tack: null, rider: null, pose: null, targets: null };
    try {
      const root = out.root = cloneSkinned(leases[0].asset.scene);
      root.name = `saddle-horse:${h.row.id}`;
      root.traverse(n => { if (n.isMesh) { n.frustumCulled = false; n.castShadow = true; } });
      out.lods = attachHorseLods(root, Object.fromEntries(levels.map((l, i) => [l, leases[i + 1].asset])), { sourceSha256: spec.sha256 });
      out.coat = applyHorseAppearance(root, { recipe: coats, sourceSha: spec.sha256, scene: sceneId, row: h.row.coat_row ?? h.row.id, individual: 'left' });
      out.tack = fitTack(root, config.tack[sceneId]);
      out.gait = createHorseGait(root, { walk, walkCycle_m: spec.stride_m, trot, trotCycle_m: spec.trot_stride_m, rest: true });
      group.add(root);
      return out;
    } catch (error) { release(out); throw error; }
  }

  function release(b) {
    if (!b) return;
    b.rider?.actor?.dispose(); b.rider?.actor?.root.removeFromParent();
    b.tack?.dispose(); b.coat?.dispose?.(); b.lods?.dispose(); b.gait?.dispose();
    if (b.root) { const skeletons = new Set(); b.root.traverse(n => { if (n.isSkinnedMesh) skeletons.add(n.skeleton); });
      for (const s of skeletons) s.dispose(); b.root.removeFromParent(); }
    for (const lease of b.leases ?? []) lease.release();
  }

  /** The year's period figure in the saddle (an anonymous stand-in), posed by rider-pose.js. */
  async function seatRider(h) {
    const layer = humans();
    const b = h.built;
    if (!layer?.createActor || !b || b.rider) return b?.rider ?? null;
    const asset = config.rider.assets[sceneId];
    const instance = { id: `rider:${h.row.id}`, contract_version: 1, display: 'shown', scene: sceneId, appearance: { asset_id: asset },
      placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' }, behaviour: { state: 'seated' },
      animation: { clip: 'idle', loop: true, phase: 0 }, lod: { policy: 'fixed', fixed: coarse ? 2 : config.rider.lod },
      interaction: { opens: 'none', selectable: false },
      provenance: { grade: 'reconstructed', basis: config.rider.why, liberty: config.liberty } };
    const actor = layer.createActor(instance, { identity: { kind: 'anonymous', personId: null, person: null, profile: null, role: null } });
    try {
      await actor.setLod(coarse ? 2 : config.rider.lod);
      if (!actor.body || h.built !== b) throw Error('riding: the rider did not load');
      actor.play('idle', { fade: 0, time: 0 }); actor.body.mixer.update(0);
      actor.root.position.set(0, 0, 0); actor.root.rotation.set(0, 0, 0);
      b.root.add(actor.root);
      actor.root.updateMatrixWorld(true);
      const pose = createRiderPose(actor.body.scene, actor.root);
      if (!pose) throw Error('riding: the rider is not the contract skeleton');
      for (const m of actor.body.meshes ?? []) m.frustumCulled = false;
      b.rider = { actor, pose };
      return b.rider;
    } catch (error) { actor.dispose(); actor.root.removeFromParent(); throw error; }
  }

  // ---- the ride
  let riding = null;              // the horse being ridden
  let view = 'behind';            // 'behind' | 'saddle'
  let cmd = { forward: 0, turn: 0, trot: false };
  let blocked = null, lastBearing = null, landing = null, eyeSmooth = null;

  function place(h, dt = 0) {
    const b = h.built;
    if (!b) return;
    const p = h.pose;
    const front = horseLocal(p.e, p.n, p.bearing, 0, R.footprint_m.ahead * .6), back = horseLocal(p.e, p.n, p.bearing, 0, -R.footprint_m.behind * .7);
    const hf = ground(front.e, front.n), hb = ground(back.e, back.n), hc = ground(p.e, p.n);
    const y = [hf, hb, hc].filter(Number.isFinite);
    p.y = y.length ? Math.min(...y) + Math.max(0, (Math.max(...y) - Math.min(...y)) * .5) : (p.y ?? 0);
    const pitch = Number.isFinite(hf) && Number.isFinite(hb) ? Math.atan2(hf - hb, R.footprint_m.ahead * .6 + R.footprint_m.behind * .7) : 0;
    b.root.position.copy(enuToWorld(p.e, p.n, p.y));
    b.root.rotation.set(-clamp(pitch, -.35, .35), horseYaw(p.bearing), 0, 'YXZ');
    b.root.updateMatrixWorld(true);
  }

  function poseRider(h) {
    const b = h.built, r = b?.rider;
    if (!r) return;
    const lean = fit.lean_walk_rad + (fit.lean_trot_rad - fit.lean_walk_rad) * (b.gait.trot ?? 0);
    const t = saddleTargets(b.tack, fit, { lean });
    r.pose.apply(t.world(b.root));
    b.tack.update(t.rootFrame(b.root, r.pose));
  }

  const ride = {
    group, horses, config,
    get active() { return !!riding; },
    get horse() { return riding; },
    get speed() { return riding?.speed ?? 0; },
    get blocked() { return blocked; },
    get view() { return view; },
    get gait() { const g = riding?.built?.gait; return !riding ? null : !g?.moving ? 'standing' : g.trot > .5 ? 'trot' : 'walk'; },

    /** Up into the saddle. False if already riding, or the horse is not drawn yet. */
    async mount(h) {
      if (riding || !h?.built) return false;
      riding = h; h.speed = 0; blocked = null; lastBearing = null; eyeSmooth = null;
      cmd = { forward: 0, turn: 0, trot: false };
      view = 'behind';
      onMount(h, true);
      try { await seatRider(h); } catch (error) { problems.push(`riding: ${error.message}`); }
      if (riding === h) poseRider(h);
      return true;
    },

    toggleView() { if (riding) { view = view === 'behind' ? 'saddle' : 'behind'; say(view === 'saddle' ? 'From the saddle' : 'From behind'); } return view; },

    /** Before the walk: the movement keys are the reins while mounted. */
    drive(intent) {
      if (!riding || !intent) return false;
      const f = clamp(intent.forward ?? 0, -1, 1), s = clamp(intent.strafe ?? 0, -1, 1);
      cmd = { forward: f, turn: s, trot: f > .15 && (!!intent.sprint || f > .92) };
      intent.forward = 0; intent.strafe = 0; intent.rise = 0; intent.sprint = false;
      return true;
    },

    /** One frame for every saddle horse: load near ones, let far ones go, move the ridden one. */
    update(dt, cameraPosition = null) {
      dt = Math.min(Math.max(dt, 0), .1);
      const v = visitor?.();
      for (const h of horses) {
        const d = v ? Math.hypot(v.e - h.pose.e, v.n - h.pose.n) : Infinity;
        if (!h.built && !h.building && d < LOAD_M) {
          h.building = build(h).then(b => { h.built = b; place(h); b.tack.update(null); }).catch(error => { problems.push(`riding: ${error.message}`); })
            .finally(() => { h.building = null; });
        } else if (h.built && h !== riding && d > DROP_M) { release(h.built); h.built = null; }
        if (h.thing) {
          h.thing.state = h === riding ? 'riding' : 'here';
          h.thing.at = h === riding && v ? [v.e, v.n] : [h.pose.e, h.pose.n];
        }
      }
      for (const h of horses) {
        const b = h.built;
        if (!b) continue;
        if (h === riding) {
          const next = rein({ speed: h.speed, bearing: h.pose.bearing }, cmd, dt, R);
          const step = next.speed * dt, b2 = next.bearing;
          const ne = h.pose.e + Math.sin(b2 * DEG) * step, nn = h.pose.n + Math.cos(b2 * DEG) * step;
          const why = step || b2 !== h.pose.bearing ? blockedAt(ne, nn, b2, ask) : null;
          if (!why) { h.pose.e = ne; h.pose.n = nn; h.pose.bearing = b2; h.speed = next.speed; blocked = null; }
          else {
            // Stopped by what is ahead; a turn where it stands is still allowed if that is clear.
            if (b2 !== h.pose.bearing && !blockedAt(h.pose.e, h.pose.n, b2, ask)) h.pose.bearing = b2;
            if (why !== blocked) say(`Held: ${why}`);
            blocked = why; h.speed = 0;
          }
          b.gait.advance(why ? 0 : step, why ? 0 : h.speed, dt);
          place(h, dt);
          poseRider(h);
        } else if (b.gait.moving > 0) { b.gait.advance(0, 0, dt); }
        if (cameraPosition) {
          const at = b.root.getWorldPosition(new THREE.Vector3());
          b.lods.update(h === riding ? 0 : at.distanceTo(cameraPosition));
        }
      }
    },

    /** After the walk: the eye behind the horse or in the saddle. The view turns with the horse. */
    hold(walker, WALK) {
      const s = walker?.state;
      if (!s) return false;
      if (landing && !riding) {
        const l = landing; landing = null;
        walker.teleport({ local_e: l.e, local_n: l.n, yaw_deg: l.bearing, pitch_deg: 0 });
        return false;
      }
      if (!riding) return false;
      if (s.flying) { ride.leave({ land: false }); return false; }
      const h = riding, b = h.built, p = h.pose;
      if (!b) return false;
      const first = lastBearing === null;
      const bearing = first ? p.bearing : (walker.bearingDeg + turn(lastBearing, p.bearing) + 360) % 360;
      lastBearing = p.bearing;
      const still = reducedMotion();
      const seat = b.root.localToWorld(b.tack.seat());
      let e, n, y;
      if (view === 'saddle') {
        // The eye where the rider's is; with reduced motion, level over the ground, not the back.
        const raw = seat.y + R.eye_above_seat_m;
        const steady = p.y + (b.tack.spec.saddle.axis_y_m ?? 1.05) + .45 + R.eye_above_seat_m;
        eyeSmooth = still ? steady : raw;
        e = seat.x; n = -seat.z; y = eyeSmooth;
        if (b.rider) b.rider.actor.root.visible = false;
      } else {
        if (b.rider) b.rider.actor.root.visible = true;
        const look = p.y + R.camera.look_at_m;
        const bb = bearing * DEG, back = R.camera.behind_m;
        // Pulled in toward the horse while the spot behind is inside a wall.
        let k = back;
        for (; k > 1.2; k -= .4) if (standable(p.e - Math.sin(bb) * k, p.n - Math.cos(bb) * k)) break;
        e = p.e - Math.sin(bb) * k; n = p.n - Math.cos(bb) * k;
        const g = ground(e, n);
        y = Math.max(look + R.camera.above_m * (k / back), (Number.isFinite(g) ? g : p.y) + .6);
        if (first) s.pitch = -Math.atan2(R.camera.above_m + .3, back);
      }
      s.e = e; s.n = n; s.eyeY = y;
      s.groundY = y - (WALK?.eyeHeight ?? 1.6);
      s.altitude = 0; s.stepEase = 0; s.bob = 0;
      s.yaw = bearingToYaw(bearing);
      walker.apply();
      return true;
    },

    /** Get down on the near side (or the nearest standable ground). Returns the words said. */
    leave({ land = true } = {}) {
      if (!riding) return null;
      const h = riding;
      if (land) {
        const to = dismountSpot(h.pose, standable);
        if (!to) { say('Nowhere to get down here'); return null; }
        landing = { ...to, bearing: (h.pose.bearing + 90) % 360 };
      }
      riding = null; h.speed = 0; blocked = null; lastBearing = null; cmd = { forward: 0, turn: 0, trot: false };
      const r = h.built?.rider;
      if (r) { r.pose.release(); r.actor.dispose(); r.actor.root.removeFromParent(); h.built.rider = null; }
      h.built?.tack.update(null);
      onMount(h, false);
      if (land) say('Down from the saddle');
      return 'Down from the saddle';
    },

    dispose() {
      if (riding) ride.leave({ land: false });
      for (const h of horses) { release(h.built); h.built = null; }
      group.removeFromParent();
    },
  };

  // One Interact thing a horse: Mount, and while riding the view and Get down.
  for (const h of horses) {
    h.thing = {
      id: `saddle-horse:${h.row.id}`, name: h.row.name, kind: 'horse', states: ['here', 'riding'], state: 'here',
      at: [h.pose.e, h.pose.n], reach: R.mount_reach_m, rideName: h.row.short_name ?? h.row.name,
      actions: {
        here: [{
          id: 'mount', label: 'Mount', said: () => `Riding ${h.row.short_name ?? h.row.name}`,
          refuse: () => {
            if (riding) return 'Already riding';
            if (!h.built) return 'The horse is coming';
            return null;
          },
          steps: [{ label: 'Foot in the stirrup', seconds: reducedMotion() ? 0 : .7, run: t => { if (t >= 1) void ride.mount(h); } }],
        }],
        riding: [
          { id: 'view', label: 'Change the view', said: () => (view === 'saddle' ? 'From the saddle' : 'From behind'),
            refuse: () => (riding === h ? null : 'Not riding'), steps: [{ label: 'View', seconds: 0, run: t => { if (t >= 1) ride.toggleView(); } }] },
          { id: 'dismount', label: 'Get down', said: '',
            refuse: () => (riding === h ? null : 'Not riding'), steps: [{ label: 'Getting down', seconds: reducedMotion() ? 0 : .5, run: t => { if (t >= 1) ride.leave(); } }] },
        ],
      },
    };
    interactions?.add(h.thing);
  }
  return ride;
}
