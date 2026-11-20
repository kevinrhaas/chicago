/**
 * block-grow-scene.js — what "Watch a block grow" does to the loaded 1904 town (T-3676).
 *
 * block-grow.js decides, per year, which of a block's buildings stand, which are ghosts
 * and which are not built yet. This applies one year at a time to the town already in
 * memory and undoes it exactly:
 *
 *   - the buildings not standing are collapsed out of the batches (buildings.js setHeld,
 *     the zero matrix the dated 1812 camps use), with the hung doors that belong to them;
 *   - a ghost is drawn in its building's place as a pale box and outline, from the box the
 *     building itself drew (buildings.instanceBounds) through its own placement, so an
 *     undated house is shown as "here by 1904" without being shown as built;
 *   - the eye is raised over the block, from the street side, and put back where it was.
 *
 * `leave()` releases every hold, removes and disposes every ghost, and returns the eye:
 * the town is the town it was. Loaded on first use; nothing here runs at boot.
 */
import * as THREE from 'three';
import { stateAt, heldAt } from './block-grow.js';

const DEG = Math.PI / 180;
/** How steeply the raised view looks down on the block. */
export const VIEW_ELEVATION_DEG = 42;
const GHOST_FILL = 0xf3efe4;
const GHOST_EDGE = 0xffffff;

/** Where a point lands on the screen from an eye at `eye` looking at `at` (ENU metres). */
function ndc(eye, at, p, tanH, tanV) {
  const f = norm([at[0] - eye[0], at[1] - eye[1], at[2] - eye[2]]);
  const r = norm([f[1], -f[0], 0]);                     // f x up
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  const d = [p[0] - eye[0], p[1] - eye[1], p[2] - eye[2]];
  const z = dot(d, f);
  return z > 1 ? [dot(d, r) / (z * tanH), dot(d, u) / (z * tanV)] : [Infinity, Infinity];
}
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

/**
 * Where to stand to see the whole block: raised, from its street side, at the bearing
 * that frames it closest — across the street on a wide screen, along it on a tall one.
 * `points` carry `e`, `n`; `fovDeg` and `aspect` are the camera's; `reserve` is the
 * share of the screen the bar covers ({ left, right, bottom }, 0-1), kept clear of the block.
 */
export function viewOver(points, side, { fovDeg = 60, aspect = 1.6, reserve = {}, pad = 8 } = {}) {
  if (!points.length) return null;
  const es = points.map((p) => p.e), ns = points.map((p) => p.n);
  // `pad` reaches past the points to the buildings' walls (placement points) or not (box corners)
  const e0 = Math.min(...es) - pad, e1 = Math.max(...es) + pad, n0 = Math.min(...ns) - pad, n1 = Math.max(...ns) + pad;
  const corners = [];
  for (const e of [e0, e1]) for (const n of [n0, n1]) for (const h of [0, 18]) corners.push([e, n, h]);
  const at = [(e0 + e1) / 2, (n0 + n1) / 2, 6];
  const tanV = Math.tan((fovDeg * DEG) / 2), tanH = tanV * aspect;
  const left = -1 + 2 * Math.min(0.6, reserve.left ?? 0) + 0.06, right = 1 - 2 * Math.min(0.6, reserve.right ?? 0) - 0.06;
  const bottom = -1 + 2 * Math.min(0.6, reserve.bottom ?? 0) + 0.06, top = 0.9;
  // the frame's clear part is not centred on the screen: aim the eye so it is
  const fits = (eye, aim) => corners.every((c) => {
    const [x, y] = ndc(eye, aim, c, tanH, tanV);
    return x >= left && x <= right && y >= bottom && y <= top;
  });
  // the street is east of a west-side block and west of an east-side one
  const bearings = side === 'west' ? [100, 120, 140, 160, 175] : [260, 240, 220, 200, 185];
  const elev = VIEW_ELEVATION_DEG * DEG;
  let best = null;
  for (const b of bearings) {
    const dir = [Math.sin(b * DEG), Math.cos(b * DEG)];
    for (let dist = 70; dist <= 600; dist += 5) {
      const eye = [at[0] + dir[0] * dist * Math.cos(elev), at[1] + dir[1] * dist * Math.cos(elev), at[2] + dist * Math.sin(elev)];
      // shift the aim so the box's middle sits in the middle of the clear part
      const cx = (left + right) / 2, cy = (bottom + top) / 2;
      const f = norm([at[0] - eye[0], at[1] - eye[1], at[2] - eye[2]]);
      const yawShift = -Math.atan(cx * tanH), pitchShift = -Math.atan(cy * tanV);
      const yaw = Math.atan2(f[0], f[1]) + yawShift;
      const pitch = Math.asin(f[2]) + pitchShift;
      const aim = [eye[0] + Math.sin(yaw) * Math.cos(pitch) * 100, eye[1] + Math.cos(yaw) * Math.cos(pitch) * 100,
        eye[2] + Math.sin(pitch) * 100];
      if (!fits(eye, aim)) continue;
      if (!best || dist < best.dist) best = { dist, eye, yaw, pitch };
      break;
    }
  }
  if (!best) return null;
  return {
    local_e: best.eye[0], local_n: best.eye[1],
    yaw_deg: ((best.yaw / DEG) % 360 + 360) % 360,
    altitude_m: best.eye[2],
    pitch_deg: best.pitch / DEG,
  };
}

export function createBlockGrowScene({ scene3d, buildings, doorGroups = () => [], walker, hud, camera, registry,
  onHeld = () => {} }) {
  let block = null, saved = null, ghosts = null, held = [], year = null;
  const ghostMaterials = {
    fill: new THREE.MeshBasicMaterial({ color: GHOST_FILL, transparent: true, opacity: 0.22, depthWrite: false }),
    edge: new THREE.LineBasicMaterial({ color: GHOST_EDGE, transparent: true, opacity: 0.85 }),
  };
  const hiddenDoors = [];

  function boxOf(id, bounds) {
    const b = bounds[id], m = buildings().matrixOf(id);
    if (!b || !m) return null;
    const size = new THREE.Vector3(b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2] - b.min[2]);
    if (!(size.x > 0 && size.y > 0 && size.z > 0)) return null;
    const geo = new THREE.BoxGeometry(size.x, size.y, size.z);
    geo.translate((b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2);
    const g = new THREE.Group();
    g.name = `block-grow-ghost:${id}`;
    const fill = new THREE.Mesh(geo, ghostMaterials.fill);
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), ghostMaterials.edge);
    fill.renderOrder = 2; edges.renderOrder = 3;
    g.add(fill, edges);
    g.matrixAutoUpdate = false;
    g.matrix.copy(m);
    g.visible = false;
    return g;
  }

  function buildGhosts() {
    ghosts = new Map();
    const group = new THREE.Group();
    group.name = 'block-grow-ghosts';
    const bounds = buildings().instanceBounds();
    for (const m of block.members) {
      const g = boxOf(m.id, bounds);
      if (g) { ghosts.set(m.id, g); group.add(g); }
    }
    ghosts.group = group;
    scene3d.add(group);
  }

  function disposeGhosts() {
    if (!ghosts) return;
    scene3d.remove(ghosts.group);
    for (const g of ghosts.values()) g.traverse((o) => o.geometry?.dispose?.());
    ghosts = null;
  }

  /** The hung doors (house-doors.js, coach-house.js) of the held buildings go with them. */
  function holdDoors(ids) {
    for (const o of hiddenDoors.splice(0)) o.visible = true;
    const set = new Set(ids);
    for (const group of doorGroups()) {
      if (!group) continue;
      for (const child of group.children) {
        let owner = null;
        child.traverse((o) => { if (!owner && o.userData?.structure_id) owner = o.userData.structure_id; });
        const named = [...set].some((id) => child.name.startsWith(`house-door:${id}:`));
        if ((named || (owner && set.has(owner))) && child.visible) { child.visible = false; hiddenDoors.push(child); }
      }
      // the coach house is one group for one house: it goes whole
      if (group.name === 'coach-house') {
        let owner = null;
        group.traverse((o) => { if (!owner && o.userData?.structure_id) owner = o.userData.structure_id; });
        if (owner && set.has(owner) && group.visible) { group.visible = false; hiddenDoors.push(group); }
      }
    }
  }

  function apply() {
    const state = stateAt(block, year);
    held = heldAt(state);
    buildings().setHeld(held);
    holdDoors(held);
    const ghostIds = new Set(state.ghost);
    for (const [id, g] of ghosts ?? []) g.visible = ghostIds.has(id);
    onHeld(held);
    return state;
  }

  /** The block's footprint on the ground: each building's own drawn box, through its placement. */
  function points() {
    const bounds = buildings().instanceBounds?.() ?? {};
    const out = [];
    const v = new THREE.Vector3();
    for (const m of block.members) {
      const b = bounds[m.id], mat = buildings().matrixOf?.(m.id);
      if (b && mat) {
        for (const x of [b.min[0], b.max[0]]) for (const z of [b.min[2], b.max[2]]) {
          v.set(x, b.min[1], z).applyMatrix4(mat);
          out.push({ e: v.x, n: -v.z });
        }
        continue;
      }
      const p = registry.get(m.id)?.sidecar?.placement;
      if (p) out.push({ e: p.local_e, n: p.local_n });
    }
    return out;
  }

  /** The share of the screen the bar takes: the bottom on a phone, the left on a wide screen. */
  const reserveOf = () => {
    const w = globalThis.innerWidth ?? 1280, h = globalThis.innerHeight ?? 800;
    // block-grow.css: 46vh at the bottom of a phone; 400 px and its 16 px gutters on the right
    // (the Navigator's rail keeps the left)
    return w <= 600 ? { bottom: 0.48 } : { right: Math.min(0.45, 432 / w) };
  };

  return {
    get active() { return !!block; },
    get block() { return block; },
    get year() { return year; },
    get held() { return [...held]; },
    /** Enter on `b` at `y`: raise the eye over the block and draw that year. */
    enter(b, y) {
      if (block) this.leave({ keepView: true });
      block = b; year = y;
      const st = walker.state;
      saved ??= { e: st.e, n: st.n, bearingDeg: walker.bearingDeg, pitchDeg: st.pitch / DEG,
        flying: !!st.flying, altitude: st.altitude };
      buildGhosts();
      const view = viewOver(points(), block.side, { fovDeg: camera.fov, aspect: camera.aspect, reserve: reserveOf(), pad: 3 });
      if (view) { hud.setFly(true, { announce: false }); walker.teleport(view); }
      return apply();
    },
    setYear(y) { if (!block) return null; year = y; return apply(); },
    /** Put the hold back after the buildings were rebuilt (a detail change). */
    reapply() { if (block) apply(); },
    /** The town exactly as it was, and the eye back where it was. */
    leave({ keepView = false } = {}) {
      if (!block) return;
      buildings().setHeld([]);
      for (const o of hiddenDoors.splice(0)) o.visible = true;
      disposeGhosts();
      held = []; block = null; year = null;
      onHeld(held);
      if (!keepView && saved) {
        hud.setFly(saved.flying, { announce: false });
        walker.teleport({ local_e: saved.e, local_n: saved.n, yaw_deg: saved.bearingDeg,
          altitude_m: saved.flying ? saved.altitude : null, pitch_deg: saved.pitchDeg });
        saved = null;
      }
    },
    dispose() { this.leave(); ghostMaterials.fill.dispose(); ghostMaterials.edge.dispose(); },
  };
}
