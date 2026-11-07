/**
 * underpinning.js — a sill carried level over sloping ground (T-3492).
 *
 * buildings.js stands every structure on the LOWEST ground under its walls'
 * feet, which "buries a little of the uphill side, which is what a sill on a
 * slope actually does". A little. The owner, 2026-11-07, looking west at the
 * 1812 factory on the top of the river bank: "this house looks sunken in 1812".
 * The ground falls 0.93 m across its walls there, so bedded at its low corner
 * the factory's east front stood half a metre to nine-tenths of a metre in the
 * ground, over the foot of its door and its ground-floor sash.
 *
 * A builder on that bank carries the sill level on an underpinning: high on the
 * low side, a course or two on the high side, and a step up to the door. So a
 * phase that states `underpinning` (data/structures.schema.json) is raised by
 * buildings.js to `sill_clear_m` over the HIGHEST ground under its feet, and
 * this module builds, in the world frame and in one mesh for the scene:
 *
 *   - the WALL RUN: a stone strip under every edge of the footprint polygon, from
 *     below the lowest ground under the walls to the sill (local y = 0), standing
 *     a hand proud of the wall face;
 *   - a PIER under each foot that stands off the polygon — a gable stack, whose
 *     base would otherwise hang in the air on the low side;
 *   - a DOORSTEP up to each front door the compiler reads off the generator's own
 *     set-out (`placement.underpinning.doors`), from the ground before the door.
 *
 * The ground is the walker's (`terrain.surfaceHeight`), sampled where it is
 * needed, so a terrain change moves the stone with it; tools/check_sunken_sills.py
 * holds the records that ask for this to the committed heightfield. Every
 * dimension here is reconstructed (docs/LIBERTIES.md L-t3492-underpinnings-1812).
 */
import * as THREE from 'three';
import { resolveBases } from './scene-loader.js';
import { bearingToYaw } from './angles.js';

/** The random-rubble sheet the 1904 foundations were drawn with: field and lake
 *  stone in lime, the one stone fabric with its joints in the map. */
export const RUBBLE_SHEET = 'textures/prairie_1904_stone/foundation_rubble/';
/** How far the stone stands proud of the wall face, and how far in it reaches. */
export const PROUD_M = 0.06;
export const INSET_M = 0.40;
/** How far below the lowest ground the stone is carried, so no slope shows its foot. */
export const BURY_M = 0.35;
/** A foot this far off the polygon is a stack's (or a stoop's), not a wall's: the
 *  notched corner log ends stand 0.24 m proud, 0.34 m off a corner diagonally. */
export const OFF_WALL_M = 0.45;
/** Feet this close together are one stack. */
export const PIER_JOIN_M = 1.2;
/** The doorstep: the largest riser, the tread, and the reach past each jamb. */
export const STEP_RISE_M = 0.19;
export const STEP_TREAD_M = 0.32;
export const STEP_WING_M = 0.25;
/** Below this the door meets its ground and wants no step. */
export const STEP_MIN_M = 0.08;
/** Where the ground before a door is read: out from the face, past the stone. */
export const STEP_GROUND_AT_M = 0.6;
/** The tone the stone falls back to when its sheet does not load. */
const FALLBACK_RGB = [0.56, 0.53, 0.47];

/** footprint (u, v) -> the GLB's local (x, z): +y in Blender is north, which is -z. */
const toLocal = ([u, v]) => [u, -v];

/** The heights a building is stood at when it has an underpinning: `lo` and `hi`
 *  are the lowest and highest ground under its feet, `y` its sill. */
export function underpinnedHeight(lo, hi, sillClear) {
  return hi + sillClear;
}

function distToSegment(px, pz, ax, az, bx, bz) {
  const dx = bx - ax; const dz = bz - az;
  const len2 = dx * dx + dz * dz || 1e-12;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (pz - az) * dz) / len2));
  const qx = ax + dx * t; const qz = az + dz * t;
  return { d: Math.hypot(px - qx, pz - qz), qx, qz };
}

/** The polygon's signed area in (x, z): which way round it runs. */
function signedArea(ring) {
  let a = 0;
  for (let i = 0; i < ring.length; i += 1) {
    const [x0, z0] = ring[i]; const [x1, z1] = ring[(i + 1) % ring.length];
    a += x0 * z1 - x1 * z0;
  }
  return a / 2;
}

/**
 * The pieces, in the structure's own frame: boxes as
 * `{ corners: [[x, z] x4, counter-clockwise from above (see orient)], y0, y1 }`.
 * Pure: no THREE, no terrain — `ground(x, z)` gives the ground at a local point in
 * the building's frame, as a height relative to its sill (local y). Exported for
 * the test.
 */
export function underpinningPieces({ polygon, feet, doors = [], frontV = null, ground }) {
  const ring = polygon.map(toLocal);
  if (ring.length < 3) return { boxes: [], steps: 0, lowest: 0 };
  // Outward is to the right of travel for a ring counter-clockwise in (x, z) seen
  // from +y; flip when it runs the other way.
  const ccw = signedArea(ring) > 0;
  let lowest = Infinity;
  for (const [x, z] of ring) lowest = Math.min(lowest, ground(x, z));
  for (const [x, z] of feet) lowest = Math.min(lowest, ground(x, z));
  const y0 = lowest - BURY_M;
  const boxes = [];
  for (let i = 0; i < ring.length; i += 1) {
    const [ax, az] = ring[i]; const [bx, bz] = ring[(i + 1) % ring.length];
    const len = Math.hypot(bx - ax, bz - az);
    if (len < 1e-6) continue;
    const tx = (bx - ax) / len; const tz = (bz - az) / len;
    // the outward normal of this edge
    const nx = ccw ? tz : -tz; const nz = ccw ? -tx : tx;
    const ex = tx * PROUD_M; const ez = tz * PROUD_M;   // closes the corners
    const o = PROUD_M; const n = -INSET_M;
    const sx = ax - ex; const sz = az - ez; const fx = bx + ex; const fz = bz + ez;
    boxes.push({ y0, y1: 0, corners: orient([
      [sx + nx * n, sz + nz * n], [fx + nx * n, fz + nz * n],
      [fx + nx * o, fz + nz * o], [sx + nx * o, sz + nz * o]]) });
  }
  // Piers under the feet that stand off the walls: a gable stack's base.
  const off = [];
  for (const [x, z] of feet) {
    let best = { d: Infinity };
    for (let i = 0; i < ring.length; i += 1) {
      const [ax, az] = ring[i]; const [bx, bz] = ring[(i + 1) % ring.length];
      const hit = distToSegment(x, z, ax, az, bx, bz);
      if (hit.d < best.d) best = hit;
    }
    if (best.d > OFF_WALL_M && !inside(ring, x, z)) off.push({ x, z, qx: best.qx, qz: best.qz });
  }
  const clusters = [];
  for (const p of off) {
    const near = clusters.find((c) => c.some((q) => Math.hypot(q.x - p.x, q.z - p.z) <= PIER_JOIN_M));
    if (near) near.push(p); else clusters.push([p]);
  }
  for (const c of clusters) {
    const xs = c.flatMap((p) => [p.x, p.qx]); const zs = c.flatMap((p) => [p.z, p.qz]);
    const x0 = Math.min(...xs) - PROUD_M; const x1 = Math.max(...xs) + PROUD_M;
    const z0 = Math.min(...zs) - PROUD_M; const z1 = Math.max(...zs) + PROUD_M;
    boxes.push({ y0, y1: 0, corners: orient([[x0, z1], [x1, z1], [x1, z0], [x0, z0]]) });
  }
  // A doorstep up to each front door, from the ground before it.
  let steps = 0;
  if (Number.isFinite(frontV)) {
    const zFace = -frontV - PROUD_M;        // the front's stone face, in local z
    for (const [u0, u1] of doors) {
      const uc = (u0 + u1) / 2;
      const rise = -ground(uc, -frontV - STEP_GROUND_AT_M);
      if (!(rise > STEP_MIN_M)) continue;
      const risers = Math.max(2, Math.ceil(rise / STEP_RISE_M));
      const r = rise / risers;
      const xa = u0 - STEP_WING_M; const xb = u1 + STEP_WING_M;
      const foot = -rise - BURY_M;
      for (let j = 1; j < risers; j += 1) {
        const zOut = zFace - j * STEP_TREAD_M;   // the top step is one tread deep
        boxes.push({ y0: foot, y1: -j * r, corners: orient([[xa, zFace], [xb, zFace], [xb, zOut], [xa, zOut]]) });
        steps += 1;
      }
    }
  }
  return { boxes, steps, lowest };
}

/** The winding `pushBox` builds outward faces from: a NEGATIVE signed area in
 *  (x, z), which is counter-clockwise seen from above (+z runs south, toward the
 *  viewer of a map, so the (x, z) plane is mirrored seen from +y). */
function orient(c) {
  return signedArea(c) < 0 ? c : [c[0], c[3], c[2], c[1]];
}

function inside(ring, x, z) {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, zi] = ring[i]; const [xj, zj] = ring[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) hit = !hit;
  }
  return hit;
}

/**
 * Append one box's visible faces — four sides and the top — to the arrays, in the
 * world frame through `matrix`. UVs are metres over the sheet's tile: along a side
 * and up it, and across the top, so the stone keeps one size everywhere.
 */
function pushBox(box, matrix, tile, out) {
  const v = new THREE.Vector3();
  const w = (x, y, z) => { v.set(x, y, z).applyMatrix4(matrix); return [v.x, v.y, v.z]; };
  const quad = (p, uv) => {
    const base = out.pos.length / 3;
    for (const q of p) out.pos.push(...q);
    for (const t of uv) out.uv.push(t[0] / tile, t[1] / tile);
    out.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
  };
  const c = box.corners;
  let run = 0;
  for (let i = 0; i < 4; i += 1) {
    const [ax, az] = c[i]; const [bx, bz] = c[(i + 1) % 4];
    const len = Math.hypot(bx - ax, bz - az);
    // (a0, b0, b1, a1): its normal is (-dz, 0, dx), outward for orient()'s winding
    quad([w(ax, box.y0, az), w(bx, box.y0, bz), w(bx, box.y1, bz), w(ax, box.y1, az)],
      [[run, box.y0], [run + len, box.y0], [run + len, box.y1], [run, box.y1]]);
    run += len;
  }
  quad([w(c[0][0], box.y1, c[0][1]), w(c[1][0], box.y1, c[1][1]),
    w(c[2][0], box.y1, c[2][1]), w(c[3][0], box.y1, c[3][1])],
  [[c[0][0], c[0][1]], [c[1][0], c[1][1]], [c[2][0], c[2][1]], [c[3][0], c[3][1]]]);
}

async function loadRubble(assetBase) {
  const here = new URL(RUBBLE_SHEET, assetBase);
  const res = await fetch(new URL('material.json', here), { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} — ${new URL('material.json', here)}`);
  const doc = await res.json();
  const loader = new THREE.TextureLoader();
  const file = (map) => new URL(`${doc.id}_${map}_web.jpg`, here).href;
  const [map, normalMap, orm] = await Promise.all([
    loader.loadAsync(file('basecolor')), loader.loadAsync(file('normal_gl')), loader.loadAsync(file('orm'))]);
  for (const t of [map, normalMap, orm]) {
    t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8;
    t.colorSpace = THREE.NoColorSpace;
  }
  map.colorSpace = THREE.SRGBColorSpace;
  const tile = Array.isArray(doc.tile_m) ? Number(doc.tile_m[0]) : Number(doc.tile_m ?? 2);
  return { map, normalMap, orm, tile: Number.isFinite(tile) && tile > 0 ? tile : 2 };
}

/**
 * Build every underpinning in the scene as one mesh.
 * @param {Array<{ id: string, matrix: THREE.Matrix4, polygon: number[][],
 *   feet: number[][], doors: number[][], frontV: number|null,
 *   ground: (x: number, z: number) => number }>} entries
 * @returns {Promise<{ mesh: THREE.Mesh|null, problems: string[], census: object }>}
 */
export async function buildUnderpinnings(entries, { assetBase = null } = {}) {
  const census = { buildings: 0, boxes: 0, steps: 0, sheet: null, ids: [] };
  const problems = [];
  if (!entries.length) return { mesh: null, problems, census };
  let sheet = null;
  try {
    sheet = await loadRubble(assetBase ?? resolveBases().assetBase);
    census.sheet = 'foundation_rubble';
  } catch (err) {
    problems.push(`underpinning stone not bound — ${err.message}; drawn in its plain tone`);
  }
  const out = { pos: [], uv: [], idx: [] };
  const tile = sheet?.tile ?? 2;
  for (const e of entries) {
    const { boxes, steps } = underpinningPieces(e);
    for (const b of boxes) pushBox(b, e.matrix, tile, out);
    census.buildings += 1;
    census.boxes += boxes.length;
    census.steps += steps;
    census.ids.push(e.id);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(out.pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(out.uv, 2));
  geo.setIndex(out.idx);
  geo.computeVertexNormals();
  geo.computeBoundingBox();
  geo.computeBoundingSphere();
  const material = new THREE.MeshStandardMaterial({
    name: 'underpinning_fieldstone',
    color: sheet ? 0xffffff : new THREE.Color(...FALLBACK_RGB),
    roughness: sheet ? 1 : 0.9,
    metalness: 0,
    ...(sheet ? { map: sheet.map, normalMap: sheet.normalMap, roughnessMap: sheet.orm, aoMap: sheet.orm } : {}),
  });
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = 'underpinnings';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData.underpinnings = census.ids.slice();
  return { mesh, problems, census };
}

/** The local frame's ground, relative to a building's sill, as a closure. */
export function groundInFrame(terrain, e, n, rotationDeg, sillY) {
  const th = bearingToYaw(rotationDeg);
  const cos = Math.cos(th); const sin = Math.sin(th);
  return (lx, lz) => terrain.surfaceHeight(e + lx * cos + lz * sin, n + lx * sin - lz * cos) - sillY;
}
