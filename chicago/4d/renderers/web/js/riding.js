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
 *   W / stick up        walk on (held); let go and it pulls up
 *   Shift with W, or    urge it on (Kevin, 2026-11-17: "gallop, run"): a trot at once, then a
 *     the stick pushed  canter, then a gallop, a pace for each second held (or each fresh
 *     right out         press); let go of Shift (ease the stick) and it keeps the pace it has
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
import { drapeRider, pressZone } from './rider-drape.js';
import { garmentKind } from './human-skirt.js';
import { routeFor } from './transport-loop.js';
import { footprintAt, overlaps } from './transport-crossings.js';
import { footprintOfPose } from './team-drive.js';

const DEG = Math.PI / 180;
export const LOAD_M = 90, DROP_M = 140;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const turn = (a, b) => ((b - a + 540) % 360) - 180;

/**
 * The town's riders (Kevin, 2026-11-17: "some appropriate number of people seasonally and by
 * time of day looping around town in a horse"): `config.riders`, written by
 * tools/lay_town_riders.mjs. Each goes round its round at its own pace while its hours and
 * seasons hold, built only near the visitor (REACH by detail, at most CAP at once) and kept as a
 * place on its round otherwise. A rider gives way: it pulls up rather than walk into the visitor,
 * another rider ahead of it, or a team it would meet in the next few seconds.
 */
/** A town rider asked to go faster: trot, canter, gallop (m/s; gear 0 is his round's walk). */
export const RIDER_GEARS_M_S = Object.freeze([null, 2.8, 5, 7.5]);
const ASK = ['a trot', 'a canter', 'a gallop'];
export const RIDER_REACH = { full: 75, balanced: 60, light: 45 }, RIDER_CAP = { full: 4, balanced: 3, light: 2 };
// Kevin, 2026-11-17: "there would be horses at the native camps": a camp's picket line holds up to
// ten, so more stand drawn at once than the four the stables needed (far ones at the far level).
export const SADDLE_CAP = { full: 7, balanced: 5, light: 3 };
const RIDER_ENVELOPE = [-.5, -1.2, .5, 1.75];   // horse and rider, left +x, ahead +z, plus a little
const AHEAD_S = [0, 1.5, 3];
const riderPrintRow = { envelope_local_xz_m: RIDER_ENVELOPE, root_ahead_of_rear_axle_m: 0 };
// Kevin, 2026-11-17: "i also just saw a carriage on its route drive through a horse". A rider
// with a team about to meet him (ahead or catching him up) pulls aside, right if the ground
// lets him, else left, and back to his line once it has gone by; the team waits for him.
// GIVE_WAY_M clears the widest team (1.95 m half width, loops.json) by its OBSTACLE_M .6 m.
export const GIVE_WAY_M = 3.4, GIVE_WAY_M_S = .9, GIVE_WAY_LOOK_M = 1.2, GIVE_WAY_BACK_S = 2;
/** A footprint moved by (de, dn). */
export const shiftPrint = (p, de, dn) => (!de && !dn ? p : { corners: p.corners.map(([e, n]) => [e + de, n + dn]),
  w: p.w + de, e: p.e + de, s: p.s + dn, n: p.n + dn });
/** ENU of `aside` metres to the right of a route point going (forwardE, forwardN). */
export const asideOf = (p, aside) => [(p.forwardN ?? -Math.cos(p.yaw)) * aside, -(p.forwardE ?? Math.sin(p.yaw)) * aside];

/** T-3497's rule: outside [from, to) local hours (`to` may pass midnight); no hour, never. */
export function offHours(hours, hour) {
  if (!Array.isArray(hours) || hours.length !== 2 || !hours.every(Number.isFinite) || !Number.isFinite(hour)) return false;
  const [from, to] = hours;
  return from <= to ? !(hour >= from && hour < to) : !(hour >= from || hour < to);
}

/**
 * Whether a dated row (a camp's horse: `dates: {from, to}`, 'YYYY-MM-DD', the camp's own days,
 * T-3527) is away on `date` (the date the Season or a jaunt sets). No dates or no date: never.
 */
export function offDate(row, date) {
  const d = date ? String(date).slice(0, 10) : '';
  if (!row?.dates || !/^\d{4}-\d\d-\d\d$/.test(d)) return false;
  return (!!row.dates.from && d < row.dates.from) || (!!row.dates.to && d > row.dates.to);
}

/**
 * A row's tack: the year's (`config.tack[scene]`), or a variant of it (`row.tack` names one of
 * `config.tack_variants`: its own `pattern`, `stirrup`, colours and saddle and bridle changes laid
 * over the year's). Kevin, 2026-11-17: the Potawatomi ride on their own pad saddles.
 */
export function tackFor(config, scene, row = null) {
  const base = config.tack?.[scene];
  const v = row?.tack ? config.tack_variants?.[row.tack] : null;
  if (!base || !v) return base;
  return { ...base, ...v.set, saddle: { ...base.saddle, ...v.saddle, cloth: { ...base.saddle.cloth, ...v.saddle?.cloth },
    flap: { ...base.saddle.flap, ...v.saddle?.flap } }, bridle: { ...base.bridle, ...v.bridle } };
}

/** Whether a rider row is out at `hour` in `season`. */
export const riderOut = (row, hour, season) => !offHours(row.hours, hour) && (!Array.isArray(row.seasons) || row.seasons.includes(season ?? 'summer'));

/** A rider's footprint at a distance on its round. */
export const riderPrint = (route, distance, margin = 0) => footprintAt(route, riderPrintRow, distance, margin);

/**
 * Why a rider at `distance` on `route` (going at `pace`) must pull up now, or null. `teams` are
 * lists of footprints at AHEAD_S; `others` the other riders ({ prints, at, ahead }); `visitor` a
 * footprint or null. It stops for what it would walk into within three seconds, never for what it
 * already touches (it walks clear of that), save the visitor, whom it never walks into. `aside`
 * is how far right of his round he rides (pulled aside for a team, GIVE_WAY_M).
 */
export function riderHeld({ route, distance, pace, teams = [], others = [], visitor = null, index = 0, aside = 0 }) {
  const mine = AHEAD_S.map(t => {
    const d = distance + pace * t, [de, dn] = asideOf(route.at(d), aside);
    return shiftPrint(riderPrint(route, d, .15), de, dn);
  });
  if (visitor && mine.some(p => overlaps(p, visitor))) return 'someone in the way';
  const meets = theirs => {
    if (overlaps(mine[0], theirs[0])) return false;
    for (let i = 1; i < AHEAD_S.length; i++) if (overlaps(mine[i], theirs[i])) return true;
    return false;
  };
  for (const prints of teams) if (meets(prints)) return 'a team';
  const here = route.at(distance), fwd = [here.forwardE ?? Math.sin(here.yaw), here.forwardN ?? -Math.cos(here.yaw)];
  for (const o of others) {
    if (!meets(o.prints)) continue;
    // The one behind gives way; head on, the lower index goes first.
    const ahead = (o.at[0] - here.e) * fwd[0] + (o.at[1] - here.n) * fwd[1] > 0;
    const meAhead = o.fwd ? (here.e - o.at[0]) * o.fwd[0] + (here.n - o.at[1]) * o.fwd[1] > 0 : false;
    if (ahead && !(meAhead && index < o.index)) return 'a rider';
  }
  return null;
}

/** The horse root's yaw for a compass bearing: its +z (ahead) to that bearing in the world. */
export const horseYaw = bearing => Math.PI - bearing * DEG;

/**
 * Whether a team is about to meet a rider on his own line (`look` metres wider than his
 * footprint): ahead of him, or coming up behind him. `teams` are footprint lists at AHEAD_S.
 */
export function teamMeets({ route, distance, pace, teams = [], look = GIVE_WAY_LOOK_M }) {
  const mine = AHEAD_S.map(t => riderPrint(route, distance + pace * t, look));
  return teams.some(prints => prints.some((p, i) => overlaps(mine[i] ?? mine[mine.length - 1], p)));
}

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
export function dismountSpot(pose, standable, { side_m = 1.6 } = {}) {
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

/** The four paces (m/s) a ridden horse is urged to: walk, trot, canter, gallop. */
export const pacesOf = R => [R.walk_m_s, R.trot_m_s, R.canter_m_s ?? R.trot_m_s, R.gallop_m_s ?? R.canter_m_s ?? R.trot_m_s];
export const PACE_NAMES = Object.freeze(['Walk', 'Trot', 'Canter', 'Gallop']);

/**
 * The reins: speed and bearing for one step. `cmd` = { forward: -1..1, turn: -1..1, gear: 0..3 }
 * from the keys or stick (gear: walk, trot, canter, gallop; the older `trot: bool` is gear 1).
 * Returns the new { speed, bearing } (no ground checks here).
 */
export function rein(state, cmd, dt, R) {
  const paces = pacesOf(R), gear = clamp(Math.round(cmd.gear ?? (cmd.trot ? 1 : 0)), 0, 3);
  let want = 0;
  if (cmd.forward > .15) want = paces[gear];
  else if (cmd.forward < -.15) want = state.speed > .2 ? 0 : -R.back_m_s;
  // Faster paces take longer to reach; pulling up from a gallop is quicker than getting there.
  const a = want > state.speed ? R.accel_m_s2 * (state.speed > R.trot_m_s ? R.accel_fast_share ?? 1 : 1) : R.brake_m_s2;
  let speed = state.speed + clamp(want - state.speed, -a * dt, a * dt);
  if (Math.abs(speed) < .01 && want === 0) speed = 0;
  // The faster it goes, the wider it turns.
  const rate = (speed > paces[2] - .4 ? (speed > paces[3] - .6 ? R.turn_gallop_deg_s ?? R.turn_trot_deg_s : R.turn_canter_deg_s ?? R.turn_trot_deg_s)
    : speed > R.walk_m_s + .2 ? R.turn_trot_deg_s : R.turn_deg_s) * (Math.abs(speed) < .1 ? .6 : 1);
  const bearing = (state.bearing + clamp(cmd.turn, -1, 1) * rate * dt * (speed < -.05 ? -1 : 1) + 360) % 360;
  return { speed, bearing };
}

/**
 * The urging: which pace the reins ask for now. `u` = { gear, urging, since } (kept by the
 * caller); `input` = { forward, urge, now } (urge: Shift held, or the stick pushed right out).
 * Urging steps up a pace at once (walk to trot), then another each R.urge_s it is held, and a
 * fresh press steps up at once; let go of it and the horse keeps the pace it has. Let go of the
 * reins (or pull up) and it stops, and goes on again at a walk.
 */
export function urgeStep(u, { forward = 0, urge = false, now = 0 }, R) {
  const every = R.urge_s ?? 1;
  let { gear = 0, urging = false, since = 0 } = u;
  if (forward > .15 && urge) {
    if (!urging || now - since >= every - 1e-9) { gear = Math.min(3, gear + 1); since = now; }
    urging = true;
  } else urging = false;
  if (!(forward > .15)) gear = 0;
  return { gear, urging, since };
}

/** How far the rider leans forward at a gait level (0 walk .. 3 gallop): `fit.lean_*_rad`. */
/**
 * How a rider moves with his horse this frame. Kevin, 2026-11-17: "the person looks pretty stiff
 * riding a horse i would think they would have some movement in their arms and body and i
 * suppose look around". At the walk his back rolls side to side with the stride and his hands
 * go with the horse's nodding head twice a stride; at the trot he rises out of the saddle once
 * a stride (the rising trot); at the canter and gallop his back rocks with the bound and his
 * hands give and take; standing, he breathes. Now and then he looks about (less at speed) and
 * back ahead. `life` is his own state (where he looks, when he looks again), moved on by `dt`
 * seconds at time `now`; `rand` a 0..1 source. `level`, `moving`, `phase`: horse-rig.js's gait.
 * Returns { lean, sway, rise, give, look, nod } for saddleTargets and rider-pose.js `apply`.
 */
export function riderLife(life, { level = 0, moving = 1, phase = 0, dt = 0, now = 0, rand = Math.random } = {}) {
  const w = i => Math.max(0, 1 - Math.abs(level - i)) * moving;
  const T = 2 * Math.PI, one = Math.sin(T * phase), two = Math.sin(2 * T * phase);
  const walk = w(0), trot = w(1), canter = w(2), gallop = w(3), still = 1 - moving;
  const breathe = Math.sin(now * T / 4.2);
  if (!(life.next > -Infinity)) life.next = now + 1 + rand() * 4;
  if (now >= life.next) {
    const away = rand() < .6;
    life.want = away ? (rand() * 2 - 1) * LOOK_MAX_RAD : 0;
    life.wantNod = away ? rand() * .2 - .08 : 0;
    life.next = now + (away ? 1.5 + rand() * 3 : 3 + rand() * 5);
  }
  // At a canter or a gallop he keeps his eyes mostly on the way ahead.
  const free = 1 - Math.min(1, canter + gallop) * .7, k = Math.min(1, Math.max(0, dt) * 2.2);
  life.look = (life.look ?? 0) + ((life.want ?? 0) * free - (life.look ?? 0)) * k;
  life.nod = (life.nod ?? 0) + ((life.wantNod ?? 0) - (life.nod ?? 0)) * k;
  return {
    lean: walk * .025 * two + canter * .08 * one + gallop * .05 * one + still * .012 * breathe,
    sway: walk * .045 * one + trot * .015 * one + canter * .02 * one + still * .01 * Math.sin(now * T / 7.3),
    rise: trot * RISE_M * (.5 - .5 * Math.cos(T * phase)),
    give: walk * .03 * two + canter * .05 * one + gallop * .06 * one + still * .008 * breathe,
    look: life.look, nod: life.nod,
  };
}
export const LOOK_MAX_RAD = .75, RISE_M = .035;
/** A small repeatable 0..1 source for one rider (his looks about). */
export const riderRand = seed => { let x = (seed >>> 0) || 1; return () => ((x = (x * 1664525 + 1013904223) >>> 0) / 4294967296); };
const hashOf = str => { let h = 2166136261; for (const c of String(str)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };

export function leanAt(fit, level) {
  const at = [fit.lean_walk_rad, fit.lean_trot_rad, fit.lean_canter_rad ?? fit.lean_trot_rad, fit.lean_gallop_rad ?? fit.lean_canter_rad ?? fit.lean_trot_rad];
  const i = clamp(Math.floor(level), 0, 2), f = clamp(level - i, 0, 1);
  return at[i] + (at[i + 1] - at[i]) * f;
}

/**
 * Mount the riding layer for a scene. Returns null where the scene has no saddle horse.
 * @param {object} o
 *   sceneId · dataBase (the data/ base URL) · moduleBase (renderers/web/) · interactions ·
 *   standable (e, n) · ground (e, n) · visitor () => walker.state · humans () => the people layer
 *   (createActor) · say (text) · reducedMotion () · coarse (a memory-saving device) ·
 *   onMount (on) · problems [] · hour () the scene's local hour · season () · detail () the
 *   scene-detail tier · hidden () riders put away (reconstructed things hidden, vehicles off) ·
 *   teams () the town's teams as footprint lists at AHEAD_S (town-transport.js footprintsAhead)
 */
export async function mountRiding({ sceneId, dataBase, moduleBase = new URL('../', import.meta.url), interactions = null,
  standable, ground, visitor, humans = () => null, say = () => {}, reducedMotion = () => false, coarse = false,
  onMount = () => {}, problems = [], hour = () => null, season = () => 'summer', detail = () => 'full',
  hidden = () => false, teams = () => [], date = () => null }) {
  sceneId = String(sceneId);
  const json = async file => { const r = await fetch(new URL(file, dataBase)); if (!r.ok) throw Error(`riding ${file}: HTTP${r.status}`); return r.json(); };
  const config = await json('transport/riding/saddle_horses.json');
  const rows = (config.rows ?? []).filter(r => r.scene === sceneId);
  const riderRows = (config.riders ?? []).filter(r => r.scene === sceneId);
  if ((!rows.length && !riderRows.length) || !config.tack?.[sceneId]) return null;
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
    // The walk, trot, canter and gallop (tools/horse_walk_v2.mjs), each bound by its bytes.
    const gaitClip = g => spec[`${g}_clip_file`] ? loadGaitClip(assetURL(spec[`${g}_clip_file`]), { sha256: spec[`${g}_clip_sha256`],
      name: spec[`${g}_clip`], modelSha256: spec.sha256, cycle_m: spec[`${g}_stride_m`] }) : null;
    clips ??= await Promise.all([
      loadGaitClip(assetURL(spec.walk_clip_file), { sha256: spec.walk_clip_sha256, name: spec.walk_clip, modelSha256: spec.sha256, cycle_m: spec.stride_m }),
      gaitClip('trot'), gaitClip('canter'), gaitClip('gallop'),
    ]).catch(error => { clips = null; throw error; });
    return { loader, recipe, clips };
  };

  // Each saddle horse: its row, where it stands now, and (when near) what draws it.
  const horses = rows.map(row => {
    const at = findStand(row.at[0], row.at[1], row.bearing_deg, ask) ?? { e: row.at[0], n: row.at[1], bearing: row.bearing_deg };
    return { row, pose: { ...at, y: 0 }, speed: 0, built: null, building: null, thing: null };
  });

  async function build(h) {
    const { loader: L, recipe: coats, clips: [walk, trot, canter, gallop] } = await tools();
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
      out.tack = fitTack(root, tackFor(config, sceneId, h.row));
      out.gait = createHorseGait(root, { walk, walkCycle_m: spec.stride_m, trot, trotCycle_m: spec.trot_stride_m,
        canter: trot && canter, canterCycle_m: spec.canter_stride_m, gallop: trot && canter && gallop, gallopCycle_m: spec.gallop_stride_m, rest: true });
      group.add(root);
      return out;
    } catch (error) { release(out); throw error; }
  }

  function release(b) {
    if (!b) return;
    b.rider?.drape?.dispose(); b.rider?.actor?.dispose(); b.rider?.actor?.root.removeFromParent();
    b.tack?.dispose(); b.coat?.dispose?.(); b.lods?.dispose(); b.gait?.dispose();
    if (b.root) { const skeletons = new Set(); b.root.traverse(n => { if (n.isSkinnedMesh) skeletons.add(n.skeleton); });
      for (const s of skeletons) s.dispose(); b.root.removeFromParent(); }
    for (const lease of b.leases ?? []) lease.release();
  }

  /** The year's period figure in the saddle (an anonymous stand-in), posed by rider-pose.js. */
  async function seatRider(h, { asset = config.rider.assets[sceneId], id = `rider:${h.row.id}`, why = config.rider.why } = {}) {
    const layer = humans();
    const b = h.built;
    if (!layer?.createActor || !b || b.rider) return b?.rider ?? null;
    const instance = { id, contract_version: 1, display: 'shown', scene: sceneId, appearance: { asset_id: asset },
      placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' }, behaviour: { state: 'seated' },
      animation: { clip: 'idle', loop: true, phase: 0 }, lod: { policy: 'fixed', fixed: coarse ? 2 : config.rider.lod },
      interaction: { opens: 'none', selectable: false },
      provenance: { grade: 'reconstructed', basis: why, liberty: config.liberty } };
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
      // Kevin, 2026-11-17: "People in long coats or blankets should be able to ride horses":
      // their hanging cloth lies on the horse (rider-drape.js), never through it.
      const meshes = []; actor.body.scene.traverse(n => { if (n.isSkinnedMesh) meshes.push(n); });
      const drape = drapeRider({ meshes, kindOf: m => garmentKind(m, asset).kind, tack: b.tack,
        seatHalfDeg: tackFor(config, sceneId, h.row).saddle.seat_half_angle_deg, press: pressZone(tackFor(config, sceneId, h.row).saddle) });
      b.rider = { actor, pose, drape };
      return b.rider;
    } catch (error) { actor.dispose(); actor.root.removeFromParent(); throw error; }
  }

  // ---- the town's riders (config.riders): a place on their rounds, built near the visitor
  const wrapOn = (route, d) => ((d % route.length) + route.length) % route.length;
  const riders = riderRows.map((row, index) => {
    const route = routeFor(row.route);
    return { row, index, route, distance: wrapOn(route, row.initial_distance_m ?? 0), speed: 0, gear: 0, held: null, out: true,
      pose: { e: 0, n: 0, bearing: 0, y: 0 }, built: null, building: null, cancel: false, failed: false,
      aside: 0, asideWant: 0, clearFor: 0, crab: 0 };
  });
  // His place on his round, `aside` metres right of it, turned a little toward a sidestep (`crab`).
  const onRound = r => {
    const p = r.route.at(r.distance), [de, dn] = asideOf(p, r.aside);
    r.pose.e = p.e + de; r.pose.n = p.n + dn;
    r.pose.bearing = ((Math.atan2(p.forwardE, p.forwardN) + r.crab) / DEG + 360) % 360;
    r.fwd = [p.forwardE, p.forwardN];
    return p;
  };
  // Which way he can pull aside here: right first, then left (further out where the near
  // ground is taken), or 0 where none has ground.
  const asideRoom = r => {
    for (const side of [GIVE_WAY_M, -GIVE_WAY_M, GIVE_WAY_M * 1.5, -GIVE_WAY_M * 1.5]) {
      let ok = true;
      for (const ahead of [0, 3]) {
        const p = r.route.at(wrapOn(r.route, r.distance + ahead)), [de, dn] = asideOf(p, side);
        const bearing = (Math.atan2(p.forwardE, p.forwardN) / DEG + 360) % 360;
        let why = 'in the way';
        try { why = blockedAt(p.e + de, p.n + dn, bearing, ask); } catch { why = 'in the way'; }
        if (why) { ok = false; break; }
      }
      if (ok) return side;
    }
    return 0;
  };
  for (const r of riders) onRound(r);
  // Kevin, 2026-11-17: "They would normally walk I think but you could direct them to gallop".
  // A town rider goes at his round's walk; asked (his Interact), he trots, canters or gallops
  // on, until asked for a walk again or he rides out of the visitor's reach.
  const paceOf = r => (r.gear > 0 ? RIDER_GEARS_M_S[r.gear] : r.row.speed_m_s);
  function startRider(r) {
    r.cancel = false;
    r.building = build(r).then(async b => {
      if (r.cancel) { release(b); return; }
      // The horse is not seen until its rider is up: no saddled horse walks its round alone.
      r.built = b; r.speed = paceOf(r); onRound(r); place(r); b.root.visible = false;
      // A rider sent away while he was being seated (the visitor went off) is not a failure.
      try { await seatRider(r, { asset: r.row.asset, id: `rider:${r.row.id}`, why: r.row.basis }); } catch (error) { if (!r.cancel && r.built === b) { problems.push(`riding: ${r.row.id}: ${error.message}`); r.failed = true; } }
      if (r.cancel || r.failed || !r.built?.rider) { release(r.built); r.built = null; return; }
      poseRider(r); b.root.visible = true;
    }).catch(error => { if (!r.cancel) { problems.push(`riding: ${r.row.id}: ${error.message}`); r.failed = true; } })
      .finally(() => { r.building = null; });
  }
  function stopRider(r) {
    r.gear = 0;
    if (r.building) r.cancel = true;
    if (r.built) { release(r.built); r.built = null; }
  }
  const square = (e, n, h) => ({ corners: [[e - h, n - h], [e + h, n - h], [e + h, n + h], [e - h, n + h]], w: e - h, e: e + h, s: n - h, n: n + h });
  const nearPrint = (p, e, n, r = 24) => p.w - r < e && e < p.e + r && p.s - r < n && n < p.n + r;

  // ---- the ride
  let riding = null;              // the horse being ridden
  const staged = new Set();       // the jaunt stage's horses (stageHorse)
  let held = false;               // the frame is held: start no new fetch
  let view = 'behind';            // 'behind' | 'saddle'
  let cmd = { forward: 0, turn: 0, gear: 0 }, urged = { gear: 0 };
  const clock = () => (globalThis.performance?.now?.() ?? Date.now()) / 1000;
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
    // He moves with his horse and looks about (riderLife), on his own clock.
    const g = b.gait, now = clock(), dt = h.lifeAt != null ? clamp(now - h.lifeAt, 0, .25) : 0;
    h.lifeAt = now; h.life ??= {}; h.lifeRand ??= riderRand(hashOf(h.row.id));
    const level = g.level ?? g.trot ?? 0;
    const L = reducedMotion?.() ? null : riderLife(h.life, { level, moving: g.moving ?? 1, phase: g.phase ?? 0, dt, now, rand: h.lifeRand });
    const t = saddleTargets(b.tack, fit, { lean: leanAt(fit, level) + (L?.lean ?? 0), rise: L?.rise ?? 0, give: L?.give ?? 0 });
    r.pose.apply({ ...t.world(b.root), look: L?.look ?? 0, sway: L?.sway ?? 0, nod: L?.nod ?? 0 });
    b.tack.update(t.rootFrame(b.root, r.pose));
    if (r.drape) { r.actor.root.updateMatrixWorld(true); r.drape.update(); }
  }

  const ride = {
    group, horses, config,
    get active() { return !!riding; },
    get horse() { return riding; },
    get speed() { return riding?.speed ?? 0; },
    get blocked() { return blocked; },

    /**
     * Every horse a moving team must not drive through, as { id, word, print } (footprints in
     * local ENU, team-drive.js footprintOfPose): the standing saddle and camp horses (not those
     * off their dates), the town riders drawn now (where they ride, pulled aside or not), the
     * jaunt stage's horses, and the visitor's own horse ('someone in the way').
     */
    obstacles() {
      const out = [];
      const print = (e, n, bearing) => footprintOfPose({ e, n, yaw: horseYaw(bearing) }, RIDER_ENVELOPE, 0);
      for (const h of horses) {
        if (h.away) continue;
        if (h === riding) { out.push({ id: `saddle-horse:${h.row.id}`, word: 'someone in the way', print: print(h.pose.e, h.pose.n, h.pose.bearing) }); continue; }
        // A standing horse's print is kept until it is moved (ridden off and left elsewhere).
        const key = `${h.pose.e},${h.pose.n},${h.pose.bearing}`;
        if (h.printKey !== key) { h.print = print(h.pose.e, h.pose.n, h.pose.bearing); h.printKey = key; }
        out.push({ id: `saddle-horse:${h.row.id}`, word: 'a horse', print: h.print });
      }
      for (const r of riders) if (r.built) out.push({ id: `rider:${r.row.id}`, word: 'a rider', print: print(r.pose.e, r.pose.n, r.pose.bearing) });
      for (const h of staged) if (h.placed && h.built?.root?.visible !== false) out.push({ id: h.row.id, word: 'a horse', print: print(h.pose.e, h.pose.n, h.pose.bearing) });
      return out;
    },
    get view() { return view; },
    get gait() { const g = riding?.built?.gait; return !riding ? null : !g?.moving ? 'standing' : g.name ?? (g.trot > .5 ? 'trot' : 'walk'); },
    /** The pace the reins ask for: 0 walk .. 3 gallop. */
    get gear() { return riding ? cmd.gear : null; },
    /** Saddle horses and riders still being fetched (a smoke waits for none before a capture). */
    get pending() { return horses.filter(h => h.building).length + riders.filter(r => r.building).length; },
    riders,
    /** The saddle and camp horses (rows, poses, built or not), read by the QA pictures. */
    horses,
    /** The town's riders now: who is out, where, built or not, and what holds them. */
    ridersNow() {
      return riders.map(r => ({ id: r.row.id, out: r.out, built: !!r.built, e: +r.pose.e.toFixed(2), n: +r.pose.n.toFixed(2),
        bearing: +r.pose.bearing.toFixed(1), speed: +r.speed.toFixed(2), held: r.held, failed: r.failed, aside: +r.aside.toFixed(2),
        gait: !r.built ? null : !r.built.gait.moving ? 'standing' : r.built.gait.name }));
    },
    /** What would hold a ridden horse standing at (e, n) facing `bearing` (a word), else null. */
    blockedAt(e, n, bearing) { return blockedAt(e, n, bearing, ask); },
    /** Every rider's round walked on the scene's ground, as a ridden horse is held (blockedAt). */
    auditRounds({ step = .5 } = {}) {
      return riders.map(r => {
        const bad = [];
        for (let s = 0; s < r.route.length; s += step) {
          const p = r.route.at(s), why = blockedAt(p.e, p.n, (Math.atan2(p.forwardE, p.forwardN) / DEG + 360) % 360, ask);
          if (why) bad.push({ s: +s.toFixed(1), e: +p.e.toFixed(1), n: +p.n.toFixed(1), why });
        }
        return { id: r.row.id, length_m: +r.route.length.toFixed(1), bad: bad.length, first: bad.slice(0, 12) };
      });
    },
    /** Every saddle horse's stand on the scene's ground: where it would be put, and how far that is from its row. */
    auditStands() {
      return horses.map(h => ({ id: h.row.id, at: h.row.at, stand: [+h.pose.e.toFixed(2), +h.pose.n.toFixed(2)],
        moved_m: +Math.hypot(h.pose.e - h.row.at[0], h.pose.n - h.row.at[1]).toFixed(2), blocked: blockedAt(h.row.at[0], h.row.at[1], h.row.bearing_deg, ask) }));
    },

    /** Up into the saddle. False if already riding, or the horse is not drawn yet. */
    async mount(h) {
      if (riding || !h?.built) return false;
      riding = h; h.speed = 0; blocked = null; lastBearing = null; eyeSmooth = null;
      cmd = { forward: 0, turn: 0, gear: 0 }; urged = { gear: 0 };
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
      const was = urged.gear;
      // Shift, or the stick pushed out past three quarters (controls/touch.js), urges. A key's
      // forward is a whole 1, so a full push is not itself an urge.
      urged = urgeStep(urged, { forward: f, urge: !!intent.sprint, now: clock() }, R);
      if (urged.gear !== was && f > .15) say(PACE_NAMES[urged.gear]);
      cmd = { forward: f, turn: s, gear: urged.gear };
      intent.forward = 0; intent.strafe = 0; intent.rise = 0; intent.sprint = false;
      return true;
    },

    /** One frame for every saddle horse and rider: load near ones, let far ones go, move them. */
    update(dt, cameraPosition = null, { paused = false } = {}) {
      // Held (the animation hold, the gate, a hidden page): nothing new is fetched, the way
      // the driven teams wait, so a held frame is the frame it was.
      held = !!paused;
      dt = Math.min(Math.max(dt, 0), .1);
      const v = visitor?.(), tier = coarse ? 'light' : (RIDER_REACH[detail?.()] ? detail() : 'full');
      // The saddle horses: the nearest few within reach are drawn.
      const cap = SADDLE_CAP[tier];
      let day = null; try { day = date?.() ?? null; } catch { /* undated */ }
      for (const h of horses) h.away = h !== riding && offDate(h.row, day);
      const order = horses.map(h => [h, h === riding ? -1 : v ? Math.hypot(v.e - h.pose.e, v.n - h.pose.n) : Infinity]).sort((a, b) => a[1] - b[1]);
      let drawn = 0;
      for (const [h, d] of order) {
        // A camp's horse is there only on its camp's days (the camp itself is drawn only then).
        const want = h === riding || (!h.away && d < LOAD_M && drawn < cap);
        if (want) drawn++;
        if (want && !h.built && !h.building && !held) {
          h.building = build(h).then(b => { h.built = b; place(h); b.tack.update(null); }).catch(error => { problems.push(`riding: ${error.message}`); })
            .finally(() => { h.building = null; });
        } else if (!want && h.built && h !== riding && (h.away || d > DROP_M || drawn >= cap)) { release(h.built); h.built = null; }
        if (h.thing) {
          h.thing.state = h === riding ? 'riding' : 'here';
          h.thing.at = h.away ? null : h === riding && v ? [v.e, v.n] : [h.pose.e, h.pose.n];
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
      ride.updateRiders(dt, cameraPosition, v, tier);
    },

    /** The town's riders: out by their hours and seasons, built near, going round, giving way. */
    updateRiders(dt, cameraPosition, v, tier) {
      if (!riders.length) return;
      let hr = null, sn = 'summer', away = false;
      try { hr = hour?.() ?? null; sn = season?.() ?? 'summer'; away = !!hidden?.(); } catch { /* the defaults */ }
      for (const r of riders) {
        r.out = !away && riderOut(r.row, hr, sn);
        if (!r.out) { stopRider(r); r.held = null; continue; }
        if (!r.built && !r.building) { r.distance = wrapOn(r.route, r.distance + paceOf(r) * dt); onRound(r); }
      }
      const at = v ? (riding ? riding.pose : v) : null;
      const visitorPrint = !at ? null : riding ? footprintOfPose({ e: at.e, n: at.n, yaw: horseYaw(riding.pose.bearing) }, RIDER_ENVELOPE, .1) : square(at.e, at.n, .45);
      let teamPrints = [];
      try { teamPrints = (riders.some(r => r.built || r.building) ? teams?.() : null) ?? []; } catch { teamPrints = []; }
      // The nearest few are built; one is not built where it would stand on a team or the visitor.
      const reach = RIDER_REACH[tier], cap = RIDER_CAP[tier];
      const near = riders.filter(r => r.out && !r.failed).map(r => [r, at ? Math.hypot(at.e - r.pose.e, at.n - r.pose.n) : Infinity]).sort((a, b) => a[1] - b[1]);
      let k = 0;
      for (const [r, d] of near) {
        if (r.built || r.building) { if (d < reach + 25 && k < cap) k++; else stopRider(r); continue; }
        if (d < reach && k < cap) {
          k++;
          if (held) continue;
          const here = riderPrint(r.route, r.distance, .3);
          if ((visitorPrint && overlaps(here, visitorPrint)) || teamPrints.some(p => overlaps(here, p[0]))) continue;
          startRider(r);
        }
      }
      const built = riders.filter(r => r.built);
      const others = built.map(r => ({ index: r.index, at: [r.pose.e, r.pose.n], fwd: r.fwd,
        prints: AHEAD_S.map(t => riderPrint(r.route, r.distance + (r.speed > .05 ? paceOf(r) * t : 0), .15)) }));
      for (const r of built) {
        const b = r.built;
        r.held = riderHeld({ route: r.route, distance: r.distance, pace: paceOf(r), index: r.index,
          teams: teamPrints.filter(p => nearPrint(p[0], r.pose.e, r.pose.n)),
          others: others.filter(o => o.index !== r.index && Math.hypot(o.at[0] - r.pose.e, o.at[1] - r.pose.n) < 20),
          visitor: visitorPrint && nearPrint(visitorPrint, r.pose.e, r.pose.n, 8) ? visitorPrint : null, aside: r.aside });
        // A team about to meet him on his line: he pulls aside (and stays there till it has gone by).
        const nearTeams = teamPrints.filter(p => nearPrint(p[0], r.pose.e, r.pose.n));
        if (nearTeams.length && teamMeets({ route: r.route, distance: r.distance, pace: paceOf(r), teams: nearTeams })) {
          r.clearFor = 0;
          if (!r.asideWant) r.asideWant = asideRoom(r);
        } else if (r.asideWant && (r.clearFor += dt) > GIVE_WAY_BACK_S) r.asideWant = 0;
        const lateral = clamp(r.asideWant - r.aside, -GIVE_WAY_M_S * dt, GIVE_WAY_M_S * dt);
        // While he steps aside for a team he keeps a slow walk on (barely on, the team close in
        // front of him), unless the visitor or a rider holds him.
        const stepping = Math.abs(lateral) > 1e-4;
        const want = r.held && !(stepping && r.held === 'a team') ? 0
          : stepping ? Math.min(paceOf(r), r.held ? .3 : GIVE_WAY_M_S) : paceOf(r);
        const a = want > r.speed ? R.accel_m_s2 : R.brake_m_s2 * 1.5;
        r.speed = Math.max(0, r.speed + clamp(want - r.speed, -a * dt, a * dt));
        if (r.speed < .02 && r.held && !stepping) r.speed = 0;
        const step = r.speed * dt;
        r.distance = wrapOn(r.route, r.distance + step);
        r.aside += lateral;
        r.crab = dt > 0 ? clamp(Math.atan2(lateral / dt, Math.max(r.speed, .6)), -.6, .6) : 0;
        onRound(r);
        b.gait.advance(Math.hypot(step, lateral), Math.max(r.speed, Math.abs(lateral) / Math.max(dt, 1e-3)), dt);
        place(r, dt);
        poseRider(r);
        if (cameraPosition) b.lods.update(b.root.getWorldPosition(new THREE.Vector3()).distanceTo(cameraPosition));
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
        landing = { ...to, bearing: h.pose.bearing }; // beside the horse, facing the way it faces
      }
      riding = null; h.speed = 0; blocked = null; lastBearing = null; cmd = { forward: 0, turn: 0, gear: 0 }; urged = { gear: 0 };
      const r = h.built?.rider;
      if (r) { r.pose.release(); r.drape?.dispose(); r.actor.dispose(); r.actor.root.removeFromParent(); h.built.rider = null; }
      h.built?.tack.update(null);
      onMount(h, false);
      if (land) say('Down from the saddle');
      return 'Down from the saddle';
    },

    /**
     * A horse for a jaunt's stage (Kevin, 2026-11-17: "maybe during the battle of fort Dearborn
     * they would have had horses"): a castmate who `mount`s rides it (jaunt-stage.js). Not one
     * of the scene's saddle horses: it is nobody's to mount, goes where the stage moves it, and
     * carries the stage's own figure (the person's face and dress), seated and draped as a town
     * rider is. `id` names it, `coat_row` picks its coat, `tack` a tack variant. Resolves to
     * { root, move({e, n, bearing, speed, eye}, dt), seat(actor, {asset, lod}), unseat(parent), seated,
     * visible, dispose() }; dispose() never disposes the castmate.
     */
    async stageHorse({ id, coat_row = id, tack = null } = {}) {
      const h = { row: { id: `stage:${id}`, coat_row, tack, name: 'A horse' }, pose: { e: 0, n: 0, bearing: 0, y: 0 }, speed: 0, built: null, placed: false };
      const b = h.built = await build(h);
      b.tack.update(null);
      staged.add(h);
      let gone = false, placed = false;
      const handle = {
        root: b.root,
        get seated() { return !!b.rider; },
        set visible(v) { b.root.visible = !!v; },
        /** Stand the horse at (e, n) facing `bearing`, going at `speed` (its gait from that). */
        move({ e, n, bearing, speed = 0, eye = null }, dt = 0) {
          if (gone) return;
          const step = placed ? Math.hypot(e - h.pose.e, n - h.pose.n) : 0;
          h.pose.e = e; h.pose.n = n; h.pose.bearing = bearing; h.speed = speed; placed = h.placed = true;
          b.gait.advance(step, speed, dt);
          place(h, dt);
          poseRider(h);
          if (eye) b.lods.update(b.root.getWorldPosition(new THREE.Vector3()).distanceTo(eye));
        },
        /** Up into the saddle: the stage's own figure, at its level (loaded if it is not yet). */
        async seat(actor, { asset = null, lod = coarse ? 2 : config.rider.lod } = {}) {
          if (gone || b.rider || !actor) return false;
          if (!actor.body || actor.lod !== lod) await actor.setLod?.(lod);
          if (gone || b.rider || !actor.body) return false;
          actor.play?.('idle', { fade: 0, time: 0 }); actor.body.mixer?.update(0);
          actor.root.position.set(0, 0, 0); actor.root.rotation.set(0, 0, 0);
          b.root.add(actor.root);
          actor.root.updateMatrixWorld(true);
          const pose = createRiderPose(actor.body.scene, actor.root);
          if (!pose) { actor.root.removeFromParent(); return false; }
          for (const m of actor.body.meshes ?? []) m.frustumCulled = false;
          const meshes = []; actor.body.scene.traverse(n => { if (n.isSkinnedMesh) meshes.push(n); });
          const drape = drapeRider({ meshes, kindOf: m => garmentKind(m, asset ?? actor.instance?.appearance?.asset_id).kind, tack: b.tack,
            seatHalfDeg: tackFor(config, sceneId, h.row).saddle.seat_half_angle_deg, press: pressZone(tackFor(config, sceneId, h.row).saddle) });
          b.rider = { actor, pose, drape, borrowed: true };
          poseRider(h);
          return true;
        },
        /** Down: the figure stood back in `parent` as it was, the horse's irons left hanging. */
        unseat(parent = null) {
          const r = b.rider;
          if (!r) return;
          b.rider = null;
          r.pose.release(); r.drape?.dispose();
          r.actor.root.removeFromParent();
          parent?.add?.(r.actor.root);
          r.actor.root.rotation.set(0, 0, 0);
          b.tack.update(null);
        },
        dispose() {
          if (gone) return;
          handle.unseat(null);
          gone = true; staged.delete(h); release(b); h.built = null;
        },
      };
      return handle;
    },

    dispose() {
      if (riding) ride.leave({ land: false });
      for (const h of horses) { release(h.built); h.built = null; }
      for (const r of riders) stopRider(r);
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
  // One Interact thing a town rider (while drawn): ask him on to a trot, a canter, a gallop, or
  // back to a walk. Kevin, 2026-11-17: "you could direct them to gallop etc".
  const GEAR_STATES = ['walk', 'trot', 'canter', 'gallop'];
  for (const r of riders) {
    const faster = { id: 'faster', get label() { return `Ask for ${ASK[Math.min(r.gear, 2)]}`; },
      refuse: () => (!r.built?.rider ? 'Too far' : r.gear >= 3 ? 'At a gallop already' : null),
      said: () => `${r.row.short_name ?? 'The rider'}: ${['walking', 'trotting on', 'cantering on', 'galloping off'][r.gear]}`,
      steps: [{ label: 'Asking', seconds: 0, run: t => { if (t >= 1 && r.built) r.gear = Math.min(3, r.gear + 1); } }] };
    const walkOn = { id: 'walk-on', label: 'Ask for a walk', refuse: () => (r.gear === 0 ? 'Walking already' : null),
      said: () => `${r.row.short_name ?? 'The rider'}: back to a walk`,
      steps: [{ label: 'Asking', seconds: 0, run: t => { if (t >= 1) r.gear = 0; } }] };
    r.thing = {
      id: `rider:${r.row.id}`, name: r.row.name, kind: 'rider', states: GEAR_STATES, reach: 6,
      get state() { return GEAR_STATES[r.gear]; }, set state(v) { /* the rider's own */ },
      get at() { return r.built?.rider ? [r.pose.e, r.pose.n] : null; },
      actions: { walk: [faster], trot: [faster, walkOn], canter: [faster, walkOn], gallop: [walkOn] },
    };
    interactions?.add(r.thing);
  }
  return ride;
}
