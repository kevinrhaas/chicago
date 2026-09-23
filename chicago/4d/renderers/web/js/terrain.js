/**
 * terrain.js — the ground, the river, and the frame everything else is placed in.
 *
 * Three jobs:
 *
 *   1. Own the coordinate convention. The dataset speaks local ENU metres
 *      (`local_e` east, `local_n` north from the datum origin). three speaks
 *      Y-up right-handed. The mapping, fixed here once so nothing else guesses:
 *
 *          world.x = +local_e        east
 *          world.y = +elevation      up (Z = 0 at the summer-1835 lake surface)
 *          world.z = -local_n        north is -Z, the way a camera at yaw 0 looks
 *
 *      `yaw_deg` in the dataset is a compass bearing: 0 = north, 90 = east,
 *      clockwise. three's rotation about +Y runs the other way, so
 *      `object.rotation.y = -bearing`.
 *
 *   2. Sample ground height, bilinearly, out of `heightfield.bin` — the same
 *      grid `generators/terrain_gen.py` built the ground mesh from, so what the
 *      walker stands on and what the walker sees are the same surface. The
 *      generator measures that agreement by ray-casting the decimated mesh
 *      against the field and refuses to export if it drifts past 30 mm.
 *
 *   3. Put the river on the screen. The water needs no shoreline geometry: the
 *      water surface IS the plane Y = 0, which is the vertical datum, and the
 *      ground crosses that plane exactly along the bank line traced off the
 *      Wright 1834 survey. So the waterline you see is the traced waterline,
 *      drawn by the depth buffer rather than by a second outline that could
 *      drift out of step with it.
 *
 * Wading, and why `walkHeight()` is not `surfaceHeight()`
 * --------------------------------------------------------
 * The heightfield carries the real channel bed — about -12 ft in the main stem.
 * A walker whose eye is pinned to that surface walks into the river and ends up
 * looking at the world from under the water, which reads as a bug rather than
 * as a river. `walkHeight()` therefore reports the WALKABLE surface: dry ground
 * where there is dry ground, and a wall at the waterline where there is not, so
 * the walker stops at the water's edge the way a person without a boat does.
 * `surfaceHeight()` still reports the real surface, the mesh still draws it, and
 * the heightfield still stores it. This is a navigation rule, not a claim about
 * the terrain — the moment there is a boat or a bridge it should be revisited.
 *
 * Its one edge: a walker TELEPORTED into the channel stands on the barrier and
 * appears to float. Walking cannot get you there, and every camera anchor in the
 * scene file is on land, so it is unreachable in normal use — but see
 * docs/LIBERTIES.md L9 rather than rediscovering it.
 */

import * as THREE from 'three';
import { PRAIRIE_TILE_PX, prairieTilePixels, prairieTileMeanLuma } from './prairie-tile.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { HORIZON_HAZE } from './world.js';
import { loadMeshoptDecoder } from './scene-loader.js';

export const DEG = Math.PI / 180;

/** The vertical datum: the summer-1835 lake and river water surface. */
export const WATER_Y = 0;
/** Below this the ground is under water and the walker may not stand on it. */
const SHORE_Y = -0.10;
/** What `walkHeight()` reports over water: high enough that the walker's 0.35 m
 *  step-up rule refuses it from any bank in the dataset. */
const WATER_BARRIER_Y = 4.0;

/** T-0466's 36-tile rule was a measured answer for the former 2,020 × 800 m
 *  ground. T-0464 made the mesh 7,340 × 10,240 m, and T-1238 then gave it a
 *  visibility reach. At 5 × 8, however, a tile was about 1.3 km wide: its near
 *  corner kept a million-triangle field submitted long after most of that tile
 *  was haze. T-1245 measures the rule in metres instead. A tile side is at most
 *  240 m — about one eighth of the 1,883 m haze reach — so the reach can reject
 *  ground with bounded edge overdraw as the modelled box changes again. */
/** The grid the last ground build actually used, for the harness to read back.
 *  Written by tileGround(); read by `groundTiling()` and by nothing in the scene. */
let lastGroundTiling = null;

/** The culling grid the ground currently stands on, or null before one is built. */
export function groundTiling() { return lastGroundTiling; }

// A reach can only reject whole tiles. Hold each side to roughly one eighth of
// the 1,883 m haze reach so a boundary tile cannot buy hundreds of metres of
// detailed ground merely because one corner remains visible (T-1245).
const GROUND_TILE_TARGET_M = 240;
// The continuous low-detail field beneath the detailed tiles: 6 heightfield
// cells = 15 m on the committed field. It carries the terrain beyond the detail
// reach without carrying the expanded field's million triangles with it.
const GROUND_BASE_STEP = 6;
const GROUND_DETAIL_REACH_M = 600;

/**
 * THE GROUND'S REACH — how far out the ground is submitted at all (T-1154).
 *
 * The ground had no distance rule of any kind. Every other far-reaching layer
 * has one — the furniture its reach (T-0150), the wood its horizon cap, the
 * flora its falloff — and while the modelled box was 2,020 x 800 m the ground
 * did not need one: the whole of it was near. Two tickets moved that. T-1123
 * carried the ground north to Kinzie's Addition (809 x 661 samples) and T-0464
 * carried it south to Twenty-Second Street (809 x 1,969), so the box went from
 * 2,020 x 800 m to 2,020 x 4,920 m — 6.1 times the area at an unchanged 2.5 m
 * sample — in the eight days after the last desktop part-4 PASS. Measured on the
 * published mirror of `dev`, by hiding one scene layer at a time and reading
 * `renderer.info` back: at Lake and Market the ground alone is 994,528 of the
 * frame's 1,432,679 triangles at the `light` tier, and 96.7 per cent of the
 * WHOLE ground mesh is inside one downtown frustum. The culling grid is not the
 * problem — T-0466 already measured that, and 12 x 12 buys 58,287 triangles for
 * fifteen draw calls — because what the frustum is taking is not badly cut, it
 * is simply all of it, out to the camera's 3,000 m far plane.
 *
 * THE RULE IS THE HAZE, AND IT IS DERIVED RATHER THAN CHOSEN. `world.js` draws
 * the scene under `FogExp2`, whose surviving fraction of a surface's own colour
 * at distance d is exp(-(d * density)^2). Beyond the distance where that falls
 * under one part in `steps`, the surface cannot move an 8-bit channel: it is
 * already the horizon haze, to the last representable step. Solve it and the
 * reach is sqrt(ln steps) / density — 1,883 m at the scene's 0.00125, against a
 * fog the lighting note already calls "total by 1500 m" and a far plane at
 * 3,000. So this is not a cheapening of a tier a visitor chose: it is the
 * distance past which the ground is provably not drawn even when it is drawn,
 * and it is why the reach is applied at EVERY tier and not only at `light`.
 *
 * WHAT IT IS NOT. Nothing is un-built, re-graded or moved. The detailed ground
 * remains within 600 m and a continuous 15 m-sampled rendition of the same
 * heightfield carries the distance beyond it. `surfaceHeight` and
 * `walkableHeight` read the original 2.5 m field and never either mesh, so
 * footing, water, flora roots and every anchored record are untouched. Beyond
 * the outer haze reach even the skirt is withheld, exactly as T-1238 measured.
 *
 * @param {number} density  the scene fog's `FogExp2` density
 * @param {number} steps    how many representable steps the channel has
 * @returns {number} the reach in metres, or Infinity where there is no fog
 */
export function hazeReachM(density, steps = 255) {
  if (!(density > 0) || !(steps > 1)) return Infinity;
  return Math.sqrt(Math.log(steps)) / density;
}

/**
 * The culling grid for a ground of this shape (T-1245).
 *
 * A fixed tile count grows fixed kilometre-wide tiles when the ground expands.
 * The reach then cannot reject the far part of a tile whose near edge still lies
 * inside it. Bound each side in metres instead: the committed 7,340 × 10,240 m
 * mesh becomes 31 × 43, and any later extension adds tiles rather than silently
 * making every existing tile coarser.
 *
 * @param {number} spanX  the ground's east-west extent, metres
 * @param {number} spanZ  its north-south extent, metres
 * @returns {{cols: number, rows: number}} cuts along X and along Z
 */
export function groundTileGrid(spanX, spanZ, targetM = GROUND_TILE_TARGET_M) {
  if (!(spanX > 0) || !(spanZ > 0)) return { cols: 1, rows: 1 };
  return {
    cols: Math.max(1, Math.ceil(spanX / targetM)),
    rows: Math.max(1, Math.ceil(spanZ / targetM)),
  };
}

/** local ENU metres -> three world position. */
export function enuToWorld(e, n, y = 0, target = new THREE.Vector3()) {
  return target.set(e, y, -n);
}

/** three world position -> local ENU metres. */
export function worldToEnu(v) {
  return { e: v.x, n: -v.z, y: v.y };
}

/** dataset compass bearing (deg, 0 = N, clockwise) -> three yaw about +Y. */
export function bearingToYaw(deg) {
  return -deg * DEG;
}

/** three yaw about +Y -> dataset compass bearing, normalised to [0, 360). */
export function yawToBearing(yaw) {
  return ((-yaw / DEG) % 360 + 360) % 360;
}

/**
 * A regular grid of elevations, sampled bilinearly.
 *
 * Layout, which `generators/terrain_gen.py` writes and this reads: row-major
 * Float32 (or scaled Int16) samples, row 0 at the SOUTH edge, column 0 at the
 * WEST edge, `cell_m` metres apart, the sample at [0][0] sitting exactly on
 * (`origin_e`, `origin_n`) in local ENU metres.
 */
export class Heightfield {
  constructor() {
    this.loaded = false;
    this.cols = 0;
    this.rows = 0;
    this.cellM = 1;
    this.originE = 0;
    this.originN = 0;
    this.data = null;
    this.meta = null;
    /** Height used outside the grid and before anything is loaded. */
    this.fallbackY = 0;
  }

  get widthM() { return (this.cols - 1) * this.cellM; }
  get depthM() { return (this.rows - 1) * this.cellM; }

  /**
   * @param {object} meta  { cols, rows, cell_m, origin_e, origin_n, encoding?, scale?, offset? }
   * @param {ArrayBuffer} buffer  raw samples, row-major from the south-west corner
   */
  adopt(meta, buffer) {
    const cols = meta.cols | 0;
    const rows = meta.rows | 0;
    if (!(cols > 1 && rows > 1)) throw new Error('heightfield: cols/rows must be > 1');

    const encoding = meta.encoding || 'float32';
    let data;
    if (encoding === 'float32') {
      data = new Float32Array(buffer, 0, cols * rows);
    } else if (encoding === 'int16') {
      // Quantised metres: y = raw * scale + offset. The plan quantises to
      // <= 0.25 ft, which int16 carries comfortably over 15 ft of relief.
      const raw = new Int16Array(buffer, 0, cols * rows);
      const scale = meta.scale ?? 0.01;
      const offset = meta.offset ?? 0;
      data = new Float32Array(raw.length);
      for (let i = 0; i < raw.length; i++) data[i] = raw[i] * scale + offset;
    } else {
      throw new Error(`heightfield: unknown encoding '${encoding}'`);
    }
    if (data.length < cols * rows) {
      throw new Error(`heightfield: ${data.length} samples for a ${cols}x${rows} grid`);
    }

    this.cols = cols;
    this.rows = rows;
    this.cellM = meta.cell_m ?? meta.cellM ?? 1;
    this.originE = meta.origin_e ?? meta.originE ?? 0;
    this.originN = meta.origin_n ?? meta.originN ?? 0;
    this.data = data;
    this.meta = meta;
    this.loaded = true;
    return this;
  }

  async load(metaUrl, binUrl) {
    const meta = await (await fetch(metaUrl)).json();
    const buffer = await (await fetch(binUrl ?? new URL(meta.bin, metaUrl))).arrayBuffer();
    return this.adopt(meta, buffer);
  }

  /** True when (e, n) lies on the loaded grid. Outside it, `sample()` answers
   * with `fallbackY` rather than a measurement — callers that refine geometry
   * against the field (streets.js, T-0110) must not treat that constant as
   * ground truth, so this is the test that separates the two. */
  contains(e, n) {
    if (!this.loaded) return false;
    const gx = (e - this.originE) / this.cellM;
    const gy = (n - this.originN) / this.cellM;
    return gx >= 0 && gy >= 0 && gx <= this.cols - 1 && gy <= this.rows - 1;
  }

  /** Elevation in metres at local ENU (e, n). Bilinear; clamped at the edges. */
  sample(e, n) {
    if (!this.loaded) return this.fallbackY;
    const gx = (e - this.originE) / this.cellM;
    const gy = (n - this.originN) / this.cellM;
    if (gx < 0 || gy < 0 || gx > this.cols - 1 || gy > this.rows - 1) return this.fallbackY;

    const x0 = Math.min(Math.floor(gx), this.cols - 2);
    const y0 = Math.min(Math.floor(gy), this.rows - 2);
    const fx = gx - x0;
    const fy = gy - y0;
    const d = this.data;
    const r0 = y0 * this.cols;
    const r1 = r0 + this.cols;
    const h00 = d[r0 + x0], h10 = d[r0 + x0 + 1];
    const h01 = d[r1 + x0], h11 = d[r1 + x0 + 1];
    return (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy;
  }

  /** Surface normal by central differences — for slope limits and shading. */
  normal(e, n, target = new THREE.Vector3()) {
    if (!this.loaded) return target.set(0, 1, 0);
    const d = this.cellM;
    const dydE = (this.sample(e + d, n) - this.sample(e - d, n)) / (2 * d);
    const dydN = (this.sample(e, n + d) - this.sample(e, n - d)) / (2 * d);
    return target.set(-dydE, 1, dydN).normalize();
  }
}

/**
 * Load the terrain for one epoch: the heightfield the walker samples, the
 * ground mesh, and the water surface.
 *
 * Degrades in one step at a time. No heightfield means a flat plane at the
 * datum and a recorded problem; no ground GLB means a mesh built here from the
 * heightfield, which is the same surface by construction and costs one boot
 * frame. Nothing here silently renders a fiction.
 *
 * @param {object} o
 * @param {URL} o.dataBase        where data/ lives
 * @param {URL} o.assetBase       where the GLBs live
 * @param {string} o.epochId      terrain epoch, from the scene file
 * @param {object} [o.confidence] the confidence view, to patch the materials into
 * @param {string[]} [o.problems] collector, same list the scene loader writes to
 */
export async function createTerrain({
  dataBase, assetBase, epochId, confidence = null, problems = [],
} = {}) {
  const group = new THREE.Group();
  group.name = 'terrain';
  const heightfield = new Heightfield();
  const disposables = [];

  let meta = null;
  if (dataBase && epochId) {
    const metaUrl = new URL(`terrain/epochs/${epochId}/heightfield.json`, dataBase);
    try {
      meta = await (await fetchOk(metaUrl)).json();
      const bin = await (await fetchOk(new URL(meta.bin, metaUrl))).arrayBuffer();
      heightfield.adopt(meta, bin);
    } catch (err) {
      problems.push(`terrain ${epochId}: no heightfield (${err.message}) — `
        + 'the ground is a flat plane at the datum and the walker will not climb a bank');
      meta = null;
    }
  }

  // ---- the ground -------------------------------------------------------- //

  const groundMat = groundMaterial(await substrateZones(dataBase, problems));
  // `.map` is null here — the prairie tile is bound as a shader uniform, not as
  // the standard material map, so disposing `.map` disposed nothing and leaked
  // the canvas texture on every epoch change.
  disposables.push(groundMat, groundMat.userData.groundTex);
  confidence?.patch(groundMat);

  let ground = null;
  const groundPath = meta?.glb?.ground;
  if (groundPath && assetBase) {
    ground = await loadGlbMesh(new URL(groundPath, assetBase))
      .catch((err) => {
        problems.push(`terrain ${epochId}: ${groundPath} (${err.message}) — `
          + 'ground rebuilt from the heightfield instead');
        return null;
      });
  }
  let groundFit = null;
  if (ground) {
    confidence?.ensureAttribute(ground.geometry, `terrain ${epochId} ground`);
    // BEFORE tiling, which splits this geometry into the meshes that are drawn.
    // See conformGroundToField: the published GLB's heights are quantised onto a
    // 306 mm lattice and the town is anchored to the heightfield, so the ground a
    // visitor sees is read back off the field rather than off the compressor.
    groundFit = conformGroundToField(ground.geometry, heightfield);
    // 10 µm: four orders of magnitude inside the 30 mm the ground is held to,
    // and a comfortable margin over the 0.24 µm float32 storage costs.
    if (groundFit && groundFit.residual_max_m > 1e-5) {
      problems.push(`terrain ${epochId}: the ground mesh still departs from the heightfield by `
        + `${(groundFit.residual_max_m * 1000).toFixed(1)} mm after conforming — `
        + 'the road and the flora are drawn under the ground where it does');
    }
  } else {
    ground = new THREE.Mesh(gridGeometry(heightfield));
    ground.name = `terrain__${epochId ?? 'flat'}`;
    // Built from the field itself, so it is conformed by construction.
    groundFit = { vertices: ground.geometry.attributes.position.count, moved: 0,
                  correction_max_m: 0, residual_max_m: 0 };
  }
  ground.material = groundMat;
  ground.receiveShadow = true;
  ground.castShadow = false;
  // The ground was `frustumCulled = false` because one mesh wrapped around the
  // camera always intersects the frustum, so testing it could only ever cost time
  // or throw the floor away by mistake. True of one mesh; not true of the ground.
  // Cut it into tiles and the half of the world behind you stops being drawn —
  // see tileGround() for the measurements behind the grid below.
  const tiles = tileGround(ground, groundTileGrid);
  /** One banked WORLD bounding box per ground tile, for the reach below.
   *  Empty when the ground was too coarse to tile, which is the case the reach
   *  has nothing to say about: one mesh around the camera is always near. */
  const groundBounds = [];
  if (tiles) {
    for (const tile of tiles) {
      group.add(tile);
      disposables.push(tile.geometry);
    }
    // The source mesh is never added to the scene, so nothing else will dispose it.
    ground.geometry.dispose();
    ground = tiles[0];
  } else {
    // A ground too coarse to tile is small enough not to need it.
    ground.frustumCulled = false;
    group.add(ground);
    disposables.push(ground.geometry);
  }

  // One continuous, modest ground under the detailed tiles. The detail tiles
  // are exact near the visitor; this 15 m field carries the same heightfield at
  // distance, where fog and perspective make the baked 2.5 m sampling wasteful.
  // A 3 cm drop prevents z-fighting where both levels are present. Navigation,
  // flora and anchored records still sample `heightfield` itself, never this LOD.
  let groundBase = null;
  if (heightfield.loaded) {
    groundBase = new THREE.Mesh(gridGeometry(heightfield, GROUND_BASE_STEP), groundMat);
    groundBase.name = `terrain_base__${epochId ?? 'field'}`;
    groundBase.position.y = -0.03;
    groundBase.receiveShadow = true;
    groundBase.castShadow = false;
    groundBase.frustumCulled = true;
    group.add(groundBase);
    disposables.push(groundBase.geometry);
  }

  // ---- the water --------------------------------------------------------- //

  const waterMat = waterMaterial();
  disposables.push(waterMat, waterMat.normalMap);
  confidence?.patch(waterMat);

  let water = null;
  const waterPath = meta?.glb?.water;
  if (waterPath && assetBase) {
    // NOT swallowed. The fallback below is a flat square the size of the town,
    // and substituting it silently for the traced river is the difference
    // between a reconstruction and a flood — the failure has to reach the
    // problems list where the gate and the Evidence panel can see it.
    water = await loadGlbMesh(new URL(waterPath, assetBase)).catch((err) => {
      problems.push(`water: ${waterPath} did not load (${err.message}) — falling back to a `
        + 'flat plane at the datum, which is NOT the traced river');
      return null;
    });
  }
  if (!water) {
    const g = new THREE.PlaneGeometry(2400, 2400, 1, 1);
    g.rotateX(-Math.PI / 2);
    // The confidence channel is part of the contract even for a fallback mesh:
    // the water surface at the datum is the one DOCUMENTED thing in this layer.
    g.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(4), 1));
    water = new THREE.Mesh(g);
    water.name = `water__${epochId ?? 'flat'}`;
  } else {
    confidence?.ensureAttribute(water.geometry, `terrain ${epochId} water`);
  }
  water.material = waterMat;
  water.position.y = WATER_Y;
  water.receiveShadow = false;
  water.castShadow = false;
  water.frustumCulled = false;
  // Draw the water AFTER the ground so the depth buffer rejects the water
  // fragments the bank hides — which is most of them, this being a 640 m box
  // with a river through it rather than a lake.
  water.renderOrder = 1;
  group.add(water);
  disposables.push(water.geometry);

  let t = 0;

  // ---- the ground's reach (T-1154) --------------------------------------- //
  // Banked once, here, for the same reason the furniture's spheres are banked:
  // the per-frame test must do no matrix work and no allocation. A sphere was
  // deliberately conservative, but on a kilometre-wide ground tile its empty
  // corners extended the reach by hundreds of metres. The axis-aligned tile
  // boxes are exact for this unmoving grid, so the haze boundary tests the tile
  // itself rather than the circle wrapped around it (T-1245).
  if (tiles) {
    group.updateWorldMatrix(true, true);
    for (const tile of tiles) {
      if (!tile.geometry.boundingBox) tile.geometry.computeBoundingBox();
      const box = tile.geometry.boundingBox?.clone();
      if (!box) continue;
      box.applyMatrix4(tile.matrixWorld);
      const e = (box.min.x + box.max.x) / 2;
      const n = -(box.min.z + box.max.z) / 2;
      groundBounds.push({ mesh: tile, min: box.min, max: box.max,
                          overField: heightfield.contains(e, n) });
    }
  }
  /** The reach in force, in metres. `Infinity` draws every tile, which is what
   *  the ground did before this and what it still does until a scene with a fog
   *  sets one — see hazeReachM(). */
  let groundReachM = Infinity;
  let groundDrawn = groundBounds.length;
  let groundHeld = 0;

  return {
    group,
    mesh: ground,
    water,
    material: groundMat,
    waterMaterial: waterMat,
    heightfield,
    meta,
    epochId,
    loaded: heightfield.loaded,

    /** How far the ground a visitor SEES had to move to become the ground the
     * town is anchored to, and what is left over afterwards. The gate reads
     * `residual_max_m`; `correction_max_m` is the size of the fault repaired,
     * and it is a number worth watching rather than asserting, because it
     * belongs to the compressor and not to this renderer. */
    groundFit,

    /**
     * THE GROUND'S REACH (T-1154) — the setter, the reading and the per-frame
     * test. See hazeReachM() above for what the distance is and why.
     *
     * `reachCulled` is recorded on the mesh as well as counted, so a probe can
     * tell a tile held back for distance from one the frustum rejected: both
     * end up `visible === false` to three, and only one of them is this rule.
     */
    setGroundReach(m) {
      groundReachM = typeof m === 'number' && Number.isFinite(m) && m > 0 ? m : Infinity;
      return groundReachM;
    },
    /** What the reach is doing this frame: the distance, and the tile counts. */
    groundReach() {
      return { reachM: Number.isFinite(groundReachM) ? groundReachM : null,
               detailReachM: GROUND_DETAIL_REACH_M,
               baseTriangles: groundBase
                 ? groundBase.geometry.index.count / 3 : 0,
               tiles: groundBounds.length, drawn: groundDrawn, held: groundHeld };
    },
    /** Per frame, before the render: hold back the ground the haze has already
     *  finished. One subtraction and one comparison per tile, over the few dozen
     *  the grid comes to. */
    updateGroundReach(eye) {
      if (!groundBounds.length) return groundReachM;
      let drawn = 0;
      let held = 0;
      for (const bound of groundBounds) {
        // Exact squared distance from the eye to an axis-aligned box. A zero on
        // an axis means the eye is between that pair of faces. This keeps a tile
        // whenever ANY of its ground can be inside the reach, with no sphere's
        // empty corner buying it extra distance.
        const dx = Math.max(bound.min.x - eye.x, 0, eye.x - bound.max.x);
        const dy = Math.max(bound.min.y - eye.y, 0, eye.y - bound.max.y);
        const dz = Math.max(bound.min.z - eye.z, 0, eye.z - bound.max.z);
        const reach = bound.overField
          ? Math.min(groundReachM, GROUND_DETAIL_REACH_M) : groundReachM;
        const far = dx * dx + dy * dy + dz * dz > reach * reach;
        bound.mesh.visible = !far;
        bound.mesh.userData.reachCulled = far;
        if (far) held++; else drawn++;
      }
      groundDrawn = drawn;
      groundHeld = held;
      return groundReachM;
    },

    /** The one rendered terrain surface in metres at local ENU (e, n).
     * Buildings, streets, trees and plant roots all anchor to this sampler. */
    surfaceHeight(e, n) { return heightfield.sample(e, n); },

    /**
     * The WALKABLE surface: the rendered terrain on land, with the documented
     * navigation barrier over open water. See the note at the top of this file.
     */
    walkHeight(e, n) {
      const h = heightfield.sample(e, n);
      return h < SHORE_Y ? WATER_BARRIER_Y : h;
    },

    /** Backward-compatible names for older harnesses and external consumers. */
    height(e, n) {
      const h = heightfield.sample(e, n);
      return h < SHORE_Y ? WATER_BARRIER_Y : h;
    },
    groundHeight(e, n) { return heightfield.sample(e, n); },

    /** True where the terrain is below the water surface. */
    isWater(e, n) { return heightfield.sample(e, n) < SHORE_Y; },

    /** True where (e, n) is on the measured grid — where `surfaceHeight()` is
     * a sample rather than the out-of-bounds fallback (T-0110). */
    inBounds(e, n) { return heightfield.contains(e, n); },

    /** Drift the ripples. One line in the render loop; nothing else animates. */
    update(dt) {
      t += dt;
      const nm = waterMat.normalMap;
      if (nm) {
        nm.offset.set((t * 0.011) % 1, (t * 0.0068) % 1);
        nm.needsUpdate = false;      // offset is a uniform, not a re-upload
      }
    },

    dispose() {
      for (const d of disposables) d?.dispose?.();
    },
  };
}

async function fetchOk(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

/**
 * Cut the ground into a grid of tiles so frustum culling has something to bite on.
 *
 * The ground arrives as ONE mesh spanning the whole 2 km × 800 m box, and a single
 * mesh that surrounds the camera always intersects the frustum — so culling it can
 * never help, which is exactly why it was switched off. That was the correct
 * conclusion from a false premise: the premise is that the ground has to be one
 * mesh. Cut into tiles, each tile gets its own bounding sphere, and the ones behind
 * you stop being drawn.
 *
 * T-0466 first measured this on the former 247,527-triangle, 2,020 × 800 m ground.
 * T-1245 repeated the real-renderer comparison after the field grew to
 * 7,340 × 10,240 m: even 32 × 48 alone left the binding light stand at 957,505
 * triangles. The final 240 m rule works with the continuous 15 m base and 600 m
 * detailed reach above; `data/render/ground_detail_lod.json` keeps the rejected
 * grid-only readings and all six closing viewport/tier readings. Tiles remain cheap
 * draw calls (one shared material, no state change), not free ones, which is why the
 * same reading also holds them under the existing 215-call budget.
 *
 * The split is by triangle CENTROID, so no triangle is duplicated and no seam is
 * introduced: every triangle lands in exactly one tile and the surface is the same
 * surface. Every attribute travels with it — `_confidence` included, which the
 * confidence view reads, and which a naive position-only split would silently drop.
 */
function tileGround(mesh, grid) {
  const geo = mesh.geometry;
  const pos = geo.attributes.position;
  if (!pos) return null;
  const index = geo.index ? geo.index.array : null;
  const triCount = index ? index.length / 3 : pos.count / 3;

  geo.computeBoundingBox();
  const bb = geo.boundingBox;
  // The grid is asked for AFTER the box is known, because it is a function of the
  // box — see groundTileGrid(). `lastGroundTiling` is what the measurement harness
  // and `?debug=1` read back; nothing in the scene depends on it.
  const { cols, rows } = grid(bb.max.x - bb.min.x, bb.max.z - bb.min.z);
  lastGroundTiling = { cols, rows,
                       spanX: bb.max.x - bb.min.x, spanZ: bb.max.z - bb.min.z,
                       tileX: (bb.max.x - bb.min.x) / cols,
                       tileZ: (bb.max.z - bb.min.z) / rows };
  if (triCount < cols * rows * 4) return null;   // too coarse to be worth splitting

  const spanX = (bb.max.x - bb.min.x) / cols;
  const spanZ = (bb.max.z - bb.min.z) / rows;
  if (!(spanX > 0) || !(spanZ > 0)) return null;

  const px = pos.array;
  const buckets = new Map();
  for (let t = 0; t < triCount; t++) {
    const a = index ? index[t * 3] : t * 3;
    const b = index ? index[t * 3 + 1] : t * 3 + 1;
    const c = index ? index[t * 3 + 2] : t * 3 + 2;
    const cx = (px[a * 3] + px[b * 3] + px[c * 3]) / 3;
    const cz = (px[a * 3 + 2] + px[b * 3 + 2] + px[c * 3 + 2]) / 3;
    const col = Math.min(cols - 1, Math.max(0, Math.floor((cx - bb.min.x) / spanX)));
    const row = Math.min(rows - 1, Math.max(0, Math.floor((cz - bb.min.z) / spanZ)));
    const key = row * cols + col;
    let bucket = buckets.get(key);
    if (!bucket) { bucket = []; buckets.set(key, bucket); }
    bucket.push(a, b, c);
  }
  if (buckets.size < 2) return null;

  const names = Object.keys(geo.attributes);
  const tiles = [];
  for (const [key, verts] of [...buckets.entries()].sort((x, y) => x[0] - y[0])) {
    const tileGeo = new THREE.BufferGeometry();
    for (const name of names) {
      const src = geo.attributes[name];
      const size = src.itemSize;
      const out = new Float32Array(verts.length * size);
      for (let i = 0; i < verts.length; i++) {
        const v = verts[i];
        for (let k = 0; k < size; k++) out[i * size + k] = src.array[v * size + k];
      }
      tileGeo.setAttribute(name, new THREE.BufferAttribute(out, size));
    }
    tileGeo.computeBoundingSphere();
    const tile = new THREE.Mesh(tileGeo, mesh.material);
    tile.name = `${mesh.name || 'terrain'}__t${key}`;
    tile.receiveShadow = mesh.receiveShadow;
    tile.castShadow = mesh.castShadow;
    tile.frustumCulled = true;
    tiles.push(tile);
  }
  return tiles;
}

/**
 * A plain float copy of an attribute, whatever it was stored as.
 *
 * This is not tidiness. It is the fix for the bug that made the whole town
 * knee-high, twice, and it belongs anywhere geometry is transformed after it is
 * loaded.
 *
 * Under `KHR_mesh_quantization` a POSITION arrives as a *normalized*
 * `Int16Array`: the stored integer divided by 32767, so the attribute can only
 * represent values in [-1, 1], and the real metres come from the node's
 * dequantisation scale — 6.25 on the Sauganash. `BufferAttribute.applyMatrix4`
 * reads denormalised floats, transforms them, and writes the result *back into
 * the same normalized Int16Array*. So the moment the dequantisation matrix is
 * applied, every coordinate past one metre is clamped to 1: a twelve-metre
 * tavern becomes a two-metre box, and because the clamp is per-axis and the
 * building is not centred, its parts are pulled apart on the way.
 *
 * That single write-back is what both of this project's scale regressions were.
 * Discarding the node transform gave two-metre buildings; applying it gave
 * two-metre buildings in pieces. Float first, transform second — the quantised
 * form has already done its job by the time the bytes are off the wire.
 *
 * The terrain GLBs are float today, so this is prevention there rather than
 * repair; the day the bake starts compressing them, the ground would collapse
 * the same way and look like a flood, which is exactly how it read the first
 * time.
 */
export function toFloatAttribute(attr, itemSize = attr.itemSize) {
  const out = new Float32Array(attr.count * itemSize);
  const read = [attr.getX, attr.getY, attr.getZ, attr.getW];
  for (let i = 0; i < attr.count; i += 1) {
    for (let k = 0; k < itemSize; k += 1) out[i * itemSize + k] = read[k].call(attr, i);
  }
  return new THREE.BufferAttribute(out, itemSize);
}

/** Every attribute of a geometry in plain float form, ready to be transformed. */
export function dequantizeGeometry(geo) {
  for (const [name, attr] of Object.entries(geo.attributes)) {
    if (attr.normalized || !(attr.array instanceof Float32Array)) {
      geo.setAttribute(name, toFloatAttribute(attr));
    }
  }
  return geo;
}

/** Load a GLB and hand back its first mesh, detached from the loaded scene. */
async function loadGlbMesh(url) {
  const buffer = await (await fetchOk(url)).arrayBuffer();
  const loader = new GLTFLoader();
  // THE GROUND AND THE RIVER ARE COMPRESSED TOO, and this loader is not the one
  // scene-loader.js configures for the buildings.
  //
  // It went unnoticed because it was true and harmless for months: the terrain
  // GLBs were the only assets gltf-transform had never been run over, so a bare
  // loader could read them. The moment they were rebaked they came back
  // meshopt-compressed, this loader threw `setMeshoptDecoder must be called
  // before loading compressed files`, and both meshes fell back — the ground to
  // a grid rebuilt from the heightfield, which looks perfectly right, and the
  // WATER to a flat 2400 m square laid over the whole town. The river vanished
  // and the town read as flooded, which is exactly what a visitor reported.
  //
  // The decoder is shared with scene-loader's, so there is one instance and one
  // place that decides how compressed assets are read.
  loader.setMeshoptDecoder(await loadMeshoptDecoder());
  const gltf = await new Promise((resolve, reject) => {
    loader.parse(buffer, String(url), resolve, reject);
  });
  let found = null;
  gltf.scene.traverse((o) => { if (!found && o.isMesh) found = o; });
  if (!found) throw new Error('no mesh in the GLB');
  // BAKE the node transform into the geometry before flattening it. Resetting
  // position/rotation/scale to identity is the right normalisation for an
  // AUTHORED transform and catastrophic for an ENCODED one: under
  // `KHR_mesh_quantization` the dequantisation lives on the node as a scale and
  // a translation, so discarding it collapses the ground to a fraction of its
  // size and drops it under the water plane. Applying it first keeps the mesh
  // exactly where the file says while still handing back something at identity.
  found.updateWorldMatrix(true, false);
  // Float BEFORE the transform: a normalized integer attribute cannot hold a
  // metre, so applying the matrix into one clamps the mesh to a 2 m cube. See
  // toFloatAttribute above.
  found.geometry = dequantizeGeometry(found.geometry.clone());
  found.geometry.applyMatrix4(found.matrixWorld);
  found.removeFromParent();
  found.position.set(0, 0, 0);
  found.rotation.set(0, 0, 0);
  found.scale.set(1, 1, 1);
  found.updateMatrix();
  return found;
}

/**
 * The apron's termination reading, as one array per edge indexed the way the
 * boundary is.
 *
 * `heightfield.json` publishes it as runs — the sand bar is 34 consecutive
 * columns of the south edge — because that is how the generator found it and a
 * run states which landform it belongs to. A per-vertex loop wants a lookup, so
 * it is widened once here rather than searched 300,000 times. Where two runs
 * overlap (two landforms truncated at the same vertex, which no epoch has yet)
 * the shorter taper wins, matching the generator's own corner rule.
 *
 * @returns {{[edge: string]: {extent: Float32Array, baseY: Float32Array}}|null}
 *          null when the epoch truncates no landform, which is the mesh the
 *          skirt has always been.
 */
function skirtTerminations(hf) {
  const runs = hf?.meta?.skirt?.terminations;
  if (!runs) return null;
  const out = {};
  for (const [edge, list] of Object.entries(runs)) {
    if (!list?.length) continue;
    const count = (edge === 'south' || edge === 'north') ? hf.cols : hf.rows;
    const extent = new Float32Array(count);
    const baseY = new Float32Array(count);
    for (const run of list) {
      for (let k = 0; k < run.extent_m.length; k += 1) {
        const i = run.index0 + k;
        if (i < 0 || i >= count) continue;
        if (extent[i] > 0 && extent[i] <= run.extent_m[k]) continue;
        extent[i] = run.extent_m[k];
        baseY[i] = run.base_y[k];
      }
    }
    out[edge] = { extent, baseY };
  }
  return Object.keys(out).length ? out : null;
}

/**
 * Put the ground mesh's heights back on the heightfield the town is anchored to.
 *
 * THE MESH THAT SHIPS IS NOT THE MESH THE GENERATOR CHECKED. `terrain_gen.py`
 * ray-casts its decimated ground against the heightfield and refuses to export
 * past 30 mm, because "the walker's eye is pinned to the heightfield, so it would
 * visibly float or sink" — and the master it exports honours that to **2.5 mm**.
 * The file a browser loads is the derivative written afterwards by
 * `gltf-transform optimize` in `tools/bake.sh`, which quantises POSITION under
 * ONE UNIFORM node scale. That scale is set by the widest axis, and this mesh is
 * 5,120 m wide (a 2,020 m box plus 1.55 km of skirt) and 9.0 m tall, so at the
 * 14 bits it once shipped at the vertical lattice was **306 mm**. Measured on
 * those bytes by `tools/measure_terrain_fit.mjs`: rms 85 mm, max 228 mm. No
 * setting fixed it — 16 bits, which it ships at now, is the maximum the format
 * offers and still lands on 78 mm.
 *
 * That is the whole of R-BUG3c. The road is drawn 22 mm above the sampler
 * (`LIFT_M`) onto ground the compressor lifted by up to 228 mm, so near the
 * camera — where depth resolution is finest and the polygon offset cannot save it
 * — the roadway, the grass tufts and every rooted plant are simply underneath the
 * ground, at a constant radius, with the clean horizontal edge the owner
 * photographed twice.
 *
 * So the heights are read back off the field at load. Not a correction factor and
 * not a fudge: the heightfield is already the authority for collision, for
 * building anchoring, for flora roots and for street drape, and this makes the
 * surface a visitor SEES the same surface, by construction rather than by
 * tolerance. What the GLB is still trusted for is everything the field cannot
 * carry — the decimated topology, the normals, and the `_CONFIDENCE` channel the
 * ground dithers under.
 *
 * The skirt is carried, not flattened. It lies outside the modelled box, where
 * `sample()` returns its fallback rather than clamping, and snapping it to that
 * would drop 1.55 km of apron onto the water plane. Sampling at the clamped
 * position instead reproduces the generator's own rule for it — "carry each
 * boundary vertex outward, keeping its own height" — so the seam at the box edge
 * closes exactly.
 *
 * EXCEPT WHERE THE BOUNDARY IS A SECTION OF SOMETHING THAT ENDS (T-0939).
 * Carrying is right for ground that continues past the box, and the mainland's
 * does — its traced shore runs stop at the edge of the tracing window, which is
 * where the reading stopped and not where the land did. It is wrong for a
 * landform the box has CUT: the 1834 sand bar left the south edge at a constant
 * +1.21 m and was extruded 1.55 km south as a straight ribbon, three and a half
 * times longer than the 660 m island it is a section of, running to the haze
 * without a taper or an end. The only evidence that can say a landform ends is a
 * closed traced outline the box truncates, so `generators/terrain_gen.py`
 * publishes that reading into `heightfield.json` — per boundary vertex, how far
 * out its landform actually reaches (`extent_m`, off the ring) and the height of
 * the water it stands in (`base_y`). Here the ground falls from the boundary
 * height to `base_y` across `extent_m` and holds it beyond, which is the same
 * arithmetic the generator placed its vertices with. The factor is 1.0 at zero
 * outward distance, so the seam still closes exactly, and an epoch whose spec
 * truncates no landform publishes no terminations and is conformed exactly as
 * before.
 *
 * WHY READING BACK ONLY Y IS ENOUGH, WHICH IT WAS NOT UNTIL 2026-08-23. A height
 * is read at the vertex's SHIPPED (E, N), so a vertex the quantiser moved in
 * plan gets the field's answer for the wrong place — and the cost of that is
 * (slope × displacement), which is nothing on decimated prairie and was 77 mm on
 * the 60-90 % bank faces the east extension brought in, against the 22 mm the
 * road ribbon is lifted by. The repair is on the generator's side of the bake and
 * it removes the displacement rather than correcting it: `terrain_gen.py`
 * DERIVES the skirt margin so the quantiser's uniform scale makes its POSITION
 * rung an exact submultiple of the 2.5 m terrain grid (78.125 mm, the grid cell
 * over 32), which puts every ground vertex on a rung, so quantising rounds each
 * one to itself. Measured on the shipped bytes by
 * `tools/measure_terrain_horizontal.mjs --gate`, which `tools/check.sh` runs:
 * plan movement **0.0 mm**, and the drawn surface within 6.7 mm of the field at
 * all 259,689 of its sample points — the master's own decimation error, with the
 * compressor contributing nothing. See T-0152.
 *
 * @returns {{vertices: number, moved: number, correction_max_m: number,
 *            residual_max_m: number}|null} null when there is no field to conform to
 */
export function conformGroundToField(geometry, hf) {
  if (!hf?.loaded) return null;
  const pos = geometry.attributes.position;
  const eMin = hf.originE;
  const eMax = hf.originE + hf.widthM;
  const nMin = hf.originN;
  const nMax = hf.originN + hf.depthM;
  const term = skirtTerminations(hf);
  let moved = 0;
  let worst = 0;
  for (let i = 0; i < pos.count; i += 1) {
    // glTF is Y-up with +Z south, so ENU north is -z. Clamped into the box: see
    // the skirt note above.
    const outE = pos.getX(i);
    const outN = -pos.getZ(i);
    const e = Math.min(eMax, Math.max(eMin, outE));
    const n = Math.min(nMax, Math.max(nMin, outN));
    let y = hf.sample(e, n);
    if (term) {
      // How far this vertex stands outside each edge, and where along that edge
      // it sits. A corner is outside two of them; the deepest taper wins, which
      // is the landform that has ended by the furthest margin.
      const col = Math.round((e - eMin) / hf.cellM);
      const row = Math.round((n - nMin) / hf.cellM);
      let f = 0;
      let base = 0;
      const take = (side, idx, d) => {
        const t = term[side];
        if (!t || d <= 0 || idx < 0 || idx >= t.extent.length) return;
        const extent = t.extent[idx];
        if (!(extent > 0)) return;
        const g = Math.min(1, d / extent);
        if (g > f) { f = g; base = t.baseY[idx]; }
      };
      take('south', col, nMin - outN);
      take('north', col, outN - nMax);
      take('west', row, eMin - outE);
      take('east', row, outE - eMax);
      if (f > 0) y += (base - y) * f;
    }
    const d = Math.abs(y - pos.getY(i));
    if (d > 0) {
      moved += 1;
      if (d > worst) worst = d;
    }
    pos.setY(i, y);
  }
  pos.needsUpdate = true;
  // Re-read rather than assume: every vertex inside the box now holds the
  // sampler's own answer, so the residual is zero but for float32 storage —
  // measured at 0.24 µm on the committed ground — and anything larger means this
  // walked the wrong axis. The gate asserts it rather than trusting the loop.
  let residual = 0;
  for (let i = 0; i < pos.count; i += 1) {
    const e = pos.getX(i);
    const n = -pos.getZ(i);
    if (e < eMin || e > eMax || n < nMin || n > nMax) continue;
    residual = Math.max(residual, Math.abs(pos.getY(i) - hf.sample(e, n)));
  }
  return { vertices: pos.count, moved, correction_max_m: worst, residual_max_m: residual };
}

/**
 * Build the ground straight from the heightfield. Used when the baked GLB is
 * missing; identical surface, more triangles, and it means a missing asset
 * degrades to "slower" rather than to "no ground".
 */
function gridGeometry(hf, step = 1) {
  if (!hf.loaded) {
    const g = new THREE.PlaneGeometry(2400, 2400, 1, 1);
    g.rotateX(-Math.PI / 2);
    g.setAttribute('_confidence',
      new THREE.BufferAttribute(new Float32Array(4).fill(1), 1));
    return g;
  }
  const { cols, rows, cellM, originE, originN } = hf;
  const stride = Math.max(1, Math.floor(step));
  const sampleCols = [];
  const sampleRows = [];
  for (let c = 0; c < cols; c += stride) sampleCols.push(c);
  for (let r = 0; r < rows; r += stride) sampleRows.push(r);
  if (sampleCols.at(-1) !== cols - 1) sampleCols.push(cols - 1);
  if (sampleRows.at(-1) !== rows - 1) sampleRows.push(rows - 1);
  const outCols = sampleCols.length;
  const outRows = sampleRows.length;
  const pos = new Float32Array(outCols * outRows * 3);
  const conf = new Float32Array(outCols * outRows).fill(0.5);
  for (let rr = 0; rr < outRows; rr++) {
    const r = sampleRows[rr];
    for (let cc = 0; cc < outCols; cc++) {
      const c = sampleCols[cc];
      const vi = rr * outCols + cc;
      const i = vi * 3;
      const y = hf.data[r * cols + c];
      pos[i] = originE + c * cellM;
      pos[i + 1] = y;
      pos[i + 2] = -(originN + r * cellM);
      if (y < SHORE_Y) conf[vi] = 1.0;
    }
  }
  const idx = new Uint32Array((outCols - 1) * (outRows - 1) * 6);
  let k = 0;
  for (let r = 0; r < outRows - 1; r++) {
    for (let c = 0; c < outCols - 1; c++) {
      const a = r * outCols + c;
      // -Z is north, so the row-major grid is mirrored relative to ENU and the
      // winding has to be flipped to keep the normals up.
      idx[k++] = a; idx[k++] = a + outCols; idx[k++] = a + 1;
      idx[k++] = a + 1; idx[k++] = a + outCols; idx[k++] = a + outCols + 1;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('_confidence', new THREE.BufferAttribute(conf, 1));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  return g;
}

/* -------------------------------------------------------------------------- */
/* materials                                                                   */
/* -------------------------------------------------------------------------- */

const WORLD_POS_VERT = /* glsl */`
  vChiWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;
`;

/**
 * THE SUBSTRATE ZONES — the flora records the ground mesh is allowed to read.
 *
 * `groundMaterial` below documented its own limit and predicted this function:
 * "there is no plant-community record in `data/` for it to read yet ... When
 * those records land, the zone a point falls in belongs here — and the ground
 * stops being one green." The records landed. Every zone in `data/flora` carries
 * `ground.rgb` and `ground.wet_rgb`, and nothing was reading them for the mesh —
 * `data/flora/index.json`'s own `_doc` records the measurement, "ROADMAP K42
 * measured that no renderer file fetches this manifest for the ground at all:
 * terrain.js never opens data/flora." So the beach and the sand bar have been
 * drawn in the prairie's green for as long as they have had ground under them,
 * and the 2026-08-11 priority raise on z08/z09 could never have moved it:
 * priority decides which community PLANTS, and the mesh was not asking.
 *
 * ONLY BOX EXTENTS, AND THE REASON IS THE FRAGMENT SHADER. A zone's extent is a
 * box, a polygon, a water buffer or an elevation band. A box is the only one of
 * the four a per-fragment test evaluates exactly and in a handful of
 * instructions, and this shader runs over most of the screen — the file's own
 * one-texture-fetch rule is the same budget. The elevation bands are already
 * what the procedural path paints, keyed on the same height. THE LIMIT THIS
 * LEAVES, written down rather than discovered later: where a higher-priority
 * polygon or buffer zone overlaps a box — z04_marsh (70) reaches 8 m inland of
 * every waterline, including the beach inside z08 — the sward plants the marsh
 * and the mesh still shows the sand. That ground is a strip a few metres wide at
 * the harbour mouth; carrying the other three extent kinds is a separate piece
 * of work and not a silent omission.
 *
 * Read off the manifest rather than the ten zone records: the manifest
 * denormalises `extent`, `priority`, `ground_rgb`, `ground_wet_rgb` and
 * `plantable_in_scene`, and `tools/validate.py` fails the build if a copy
 * disagrees with the record it came from. One fetch, gated.
 *
 * Degrades to today's behaviour: no manifest, no zones, and the ground is the
 * prairie everywhere, with the problem recorded.
 */
async function substrateZones(dataBase, problems) {
  if (!dataBase) return [];
  let index = null;
  try {
    index = await (await fetchOk(new URL('flora/index.json', dataBase))).json();
  } catch (err) {
    problems.push(`terrain: no flora manifest (${err.message}) — the ground is `
      + 'the prairie tile everywhere, including the sand belt and the bar');
    return [];
  }
  const out = [];
  for (const z of index.zones || []) {
    const box = z.extent?.kind === 'everywhere' ? z.extent.box : null;
    if (!box) continue;
    // A community the scene does not plant does not paint the ground it does not
    // stand on either. z07_bur_oak_savanna is the one, 5.6 km SSW of the forks.
    if (z.plantable_in_scene === false) continue;
    if (!Array.isArray(z.ground_rgb) || !Array.isArray(z.ground_wet_rgb)) {
      problems.push(`terrain: flora zone ${z.id} has a box extent but records no `
        + 'ground colour — the mesh leaves it as prairie');
      continue;
    }
    out.push({
      id: z.id,
      priority: z.extent?.priority ?? z.priority ?? 0,
      e0: box.e[0], e1: box.e[1], n0: box.n[0], n1: box.n[1],
      // The records state sRGB 0-255; the shader works in the renderer's linear
      // space and `chiTex` arrives there already (the tile is SRGBColorSpace).
      // Converted explicitly rather than by a string parse, so the colour space
      // of a recorded triple is visible at the place it is read.
      dry: new THREE.Color().setRGB(...z.ground_rgb.map((v) => v / 255), THREE.SRGBColorSpace),
      wet: new THREE.Color().setRGB(...z.ground_wet_rgb.map((v) => v / 255), THREE.SRGBColorSpace),
    });
  }
  // Ascending, so the shader mixes the higher-priority zone in last and it wins
  // where two boxes overlap — the same order the sward resolves them in.
  out.sort((a, b) => a.priority - b.priority);
  return out;
}

/**
 * How far a zone's declared colour reaches past its own box edge, metres.
 *
 * Not zero, and the zone records say why: "No survey drew these lines" (z01),
 * "It is a reading of the terrain, not evidence, and a critic should treat the
 * line as ours" (z02), "The north-south bounds are the scene's own, not the
 * belt's" (z08, z09). A hard edge on the mesh would draw those admissions as a
 * surveyed boundary. The width is the terrain spec's own transition: z09's note
 * places the State Street break-of-slope band "between E +780 and +880", a 100 m
 * ramp whose midpoint is 830 — ten metres off this zone's own west edge at 840.
 * So the ramp across a box edge is that band's width, and at the one edge where
 * the sand meets the prairie it lands on the break of slope the terrain already
 * builds there.
 */
const ZONE_EDGE_RAMP_M = 50;

/**
 * The substrate zones as fragment code, generated from the records at material
 * build time rather than carried as uniforms.
 *
 * Ten zones is a scene constant, and the ones with box extents are two. Baking
 * them into the source costs the frame four smoothsteps per zone and no uniform
 * fetch, and — the reason that matters here — it costs EXACTLY NOTHING when
 * there are none: this returns an empty string, the prairie statements above are
 * the whole function, and the compiled shader is the one this file shipped
 * before the zones were read.
 *
 * WHAT A ZONE IS ALLOWED TO CHANGE. Its `ground.rgb` and `ground.wet_rgb`, and
 * nothing else. The grain is the prairie tile's, taken as LUMINANCE and divided
 * by the tile's own mean, so the sand carries the same texture relief at the
 * same relative strength and none of the tile's hue: a beach is mottled in tone,
 * not in colour, and the tile's khaki thatch is a prairie's dead litter. Because
 * the divisor is the tile's measured mean, the mean albedo inside a zone is the
 * recorded triple itself — the record is not scaled, tinted or approached, it is
 * what the ground averages.
 *
 * The community mosaic (`chiPatch`) is deliberately NOT carried onto a zone: its
 * own comment calls it "a swale-and-rise business at tens of metres", which is a
 * statement about prairie relief and not about sand.
 *
 * Clamped at 1.0 because an albedo cannot exceed it — a GUARD, and on the
 * committed records it never binds: the tile's brightest texel is 1.378 times
 * its mean and z08_lakeshore is the brightest zone, which puts the largest
 * product any channel reaches at 0.778. So the clamp costs the picture nothing
 * today and stops a future record whose triple is brighter from turning into a
 * flat white patch instead of an obviously-too-bright one. `tools/
 * measure_ground_albedo.mjs --gate` runs this same arithmetic over the same
 * pixels and holds every zone's mean to within one sRGB unit of its record;
 * it currently reports 0.00 on all four triples.
 */
function zoneGlsl(zones) {
  if (!zones.length) return '';
  const F = ZONE_EDGE_RAMP_M.toFixed(1);
  const f = (v) => (Number.isInteger(v) ? v.toFixed(1) : String(v));
  const v3 = (c) => `vec3(${c.r.toFixed(6)}, ${c.g.toFixed(6)}, ${c.b.toFixed(6)})`;
  const blocks = zones.map((z) => `
  // ${z.id} — priority ${z.priority}, e ${z.e0}..${z.e1}, n ${z.n0}..${z.n1}
  {
    float w = smoothstep(${f(z.e0 - ZONE_EDGE_RAMP_M)}, ${f(z.e0 + ZONE_EDGE_RAMP_M)}, chiE)
            * (1.0 - smoothstep(${f(z.e1 - ZONE_EDGE_RAMP_M)}, ${f(z.e1 + ZONE_EDGE_RAMP_M)}, chiE))
            * smoothstep(${f(z.n0 - ZONE_EDGE_RAMP_M)}, ${f(z.n0 + ZONE_EDGE_RAMP_M)}, chiN)
            * (1.0 - smoothstep(${f(z.n1 - ZONE_EDGE_RAMP_M)}, ${f(z.n1 + ZONE_EDGE_RAMP_M)}, chiN));
    vec3 c = mix(${v3(z.dry)}, ${v3(z.wet)}, chiWet);
    chiPrairie = mix(chiPrairie, diffuseColor.rgb * min(vec3(1.0), c * chiGrain), w);
  }`).join('\n');
  return `
  // ---- the substrate zones (${zones.map((z) => z.id).join(', ')}) ---------- //
  // Scene coordinates off world position: the ground is built at x = e and
  // z = -n (see gridGeometry), so this is the same frame the records use.
  float chiE = vChiWorld.x;
  float chiN = -vChiWorld.z;
  // The tile's relief as a scalar, normalised by its own measured mean, so a
  // zone's mean albedo is exactly what its record states. Mixed in ASCENDING
  // priority — the last zone written wins where two boxes overlap, which is the
  // order the sward resolves them in. The edges ramp over ${ZONE_EDGE_RAMP_M} m
  // because no survey drew them; see ZONE_EDGE_RAMP_M.
  float chiGrain = dot(chiTex, vec3(0.2126, 0.7152, 0.0722)) / max(uPrairieLuma, 1e-6);
${blocks}
`;
}

/**
 * Ground: a procedural prairie sampled in WORLD space, darkening to wet mud as
 * the surface approaches the water.
 *
 * World-space sampling rather than UVs, deliberately. The bake decimates the
 * ground wherever it is planar — which is most of it, this being Chicago — and
 * a UV set carried through a planar dissolve stretches across every dissolved
 * region. Sampling by world XZ cannot stretch, and it costs the GLB no
 * attribute at all.
 *
 * The wetness band is not decoration: dossier zone 11 puts a strip along the
 * South Division shore "where land and water mingled, covered with tall grass,
 * reeds and rushes" at +0.5 to +2.0 ft, and the heightfield puts that strip at
 * +1.25 ft. Keying the mud on elevation therefore paints exactly the zone the
 * source describes, and paints it narrow on the higher north and west banks —
 * which is also what the sources say.
 *
 * WHAT THE DRY BAND MAY AND MAY NOT DO. It used to multiply the high ground by
 * (1.12, 1.06, 0.85) across `smoothstep(0.55, 1.25)`. The committed heightfield
 * puts the whole west-side plain between 0.87 and 1.24 m — its own gradient audit
 * reports under 0.5 ft of relief per 300 ft — so that band was not selecting
 * anything: it applied at 77–92 % strength over the entire open prairie and
 * turned it straw. Straw is the October negative control, not July. The
 * replacement is a narrow, gentle mesic tint over the top of the actual
 * elevation range: enough that the driest ground is a lighter, yellower green
 * than the swales, nowhere near enough to senesce it.
 *
 * So what this paints is WETNESS, from the heightfield, and nothing else. It is
 * not a community map: there is no plant-community record in `data/` for it to
 * read yet, and a renderer that invented the boundary between wet and mesic
 * prairie would be filling a gap silently. When those records land, the zone a
 * point falls in belongs here — and the ground stops being one green.
 */
function groundMaterial(zones = []) {
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, roughness: 1, metalness: 0,
  });
  const tex = prairieTexture();
  mat.map = null;
  mat.userData.groundTex = tex;
  mat.userData.substrateZones = zones.map((z) => z.id);

  const prior = mat.onBeforeCompile;
  mat.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    shader.uniforms.uGround = { value: tex };
    shader.uniforms.uPrairieLuma = { value: tex.userData.meanLinearLuma };
    shader.vertexShader = 'varying vec3 vChiWorld;\n' + shader.vertexShader.replace(
      '#include <begin_vertex>', '#include <begin_vertex>' + WORLD_POS_VERT,
    );
    shader.fragmentShader = `
varying vec3 vChiWorld;
uniform sampler2D uGround;
uniform float uPrairieLuma;
` + shader.fragmentShader.replace('#include <map_fragment>', /* glsl */`
  // ONE texture fetch, deliberately. The ground covers most of the screen, so
  // every instruction here is paid a million times a frame; a second octave
  // fetched from the same texture at a different scale looked slightly better
  // and halved the frame rate under software rasterisation. The finer octaves
  // are therefore baked INTO that one texture (see prairieTexture) and the
  // patch-scale variation above the tile is arithmetic, which costs a fraction
  // of a filtered fetch.
  vec3 chiTex = texture2D(uGround, vChiWorld.xz * 0.0909).rgb;

  // Community mosaic — 42 m by 48 m, broken by a 15 m diagonal. The two sines
  // this replaces beat at ~200 m, a soft blur the size of a city block that read
  // as cloud shadow rather than as ground; prairie patchiness is a
  // swale-and-rise business at tens of metres, which is the scale the
  // heightfield's own relief works at. THREE sines total, one more than before
  // and no more: this runs once per ground fragment and the ground is most of
  // the screen, so the count is a budget, not a taste (the same reason there is
  // exactly one texture fetch above). Amplitude is held near +/-14 % — past that
  // the pattern competes with the sward instead of sitting under it.
  float chiPatch = sin(vChiWorld.x * 0.1496 + 1.7) * sin(vChiWorld.z * 0.1309)
                 + 0.6 * sin(vChiWorld.x * 0.3307 - vChiWorld.z * 0.2712 + 4.1);
  // Wet ground: the marshy shore strip, keyed on height above the datum.
  // Dossier zone 11 puts that strip at +0.5 to +2.0 ft and the heightfield puts
  // it at +1.25 ft, so elevation is the honest driver — it paints the mud wide
  // on the low South Division shore and narrow on the higher north and west
  // banks, which is what the sources say. The top of the band is pulled in to
  // 0.70 m so it stops at the foot of the plain (p25 of the land is 0.83 m)
  // instead of tinting it. It keys the SUBSTRATE zones too, between their own
  // two declared colours, so the reading is one rule and not two.
  float chiWet = 1.0 - smoothstep(0.05, 0.70, vChiWorld.y);

  // THE PRAIRIE PATH, arithmetically what it has always been — the three
  // statements below are the previous revision's, moved onto a local so the
  // substrate can be mixed against them. Where no zone covers a fragment the
  // weight is 0.0, and mix(a, b, 0.0) is a exactly, so "nothing outside the
  // zones moves" is a property of the code rather than a claim about a
  // screenshot. (No backticks in here: this is a JS template literal.)
  vec3 chiPrairie = diffuseColor.rgb * chiTex * (1.0 + 0.088 * chiPatch);
  chiPrairie = mix(chiPrairie,
                   chiPrairie * vec3(0.46, 0.42, 0.30) + vec3(0.042, 0.034, 0.020),
                   chiWet);
  // Drier mesic prairie on the rises. A July shift, not a September one: a few
  // per cent lighter and a few per cent less blue, so the crown of the plain
  // reads finer and yellower than the swale beside it and still reads green.
  chiPrairie *= mix(vec3(1.0), vec3(1.05, 1.03, 0.92),
                    smoothstep(0.95, 1.28, vChiWorld.y));

${zoneGlsl(zones)}
  diffuseColor.rgb = chiPrairie;
`);
  };
  mat.needsUpdate = true;
  return mat;
}

/**
 * Water: a silty prairie river, not a swimming pool.
 *
 * There is no environment map in this scene on purpose (see world.js — a PMREM
 * of the analytic sky swamped every albedo), so the water cannot get its look
 * from a reflection probe. It gets it from three cheap things instead: a
 * drifting ripple normal map, a low roughness so the single directional light
 * leaves a real sun glint, and a Fresnel term that turns the surface toward the
 * sky colour at grazing angles — which is most of what makes a flat plane read
 * as water when you are standing on the bank looking across it.
 */
function waterMaterial() {
  const mat = new THREE.MeshStandardMaterial({
    color: 0x3e4a38,
    roughness: 0.17,
    metalness: 0.0,
    normalMap: rippleTexture(),
    normalScale: new THREE.Vector2(0.55, 0.55),
  });
  // 2400 m of plane / 700 tiles = a 3.4 m ripple cell, which is the scale you
  // actually read from a bank. Mipmaps + anisotropy fade it to flat by the far
  // shore instead of aliasing into noise.
  mat.normalMap.wrapS = mat.normalMap.wrapT = THREE.RepeatWrapping;
  mat.normalMap.repeat.set(700, 700);
  mat.normalMap.anisotropy = 8;

  const prior = mat.onBeforeCompile;
  mat.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    // The same colour the far ground goes to (world.js HORIZON_HAZE), so the
    // river and the plain agree about what distance looks like — a hand-picked
    // grey-green here used to leave the water reading a season cooler than the
    // air above it.
    //
    // ONE conversion, not two. `new THREE.Color(hex)` already reads the hex as
    // sRGB and stores it in the renderer's linear working space
    // (ColorManagement.enabled is true by default since three r152), so the
    // `.convertSRGBToLinear()` that used to follow it applied the transfer
    // function a second time: the old 0x98a69d reached the shader as linear
    // (0.080,0.120,0.093) instead of (0.314,0.381,0.337) — 31 % of its intended
    // radiance. `outgoingLight` is linear at this point in the fragment, so what
    // the grazing angle mixed toward was not distance at all, it was a dark
    // olive: the far water read as a stain on the plain rather than as sky lying
    // on it, and the comment above it claimed the opposite in good faith.
    shader.uniforms.uSky = { value: new THREE.Color(HORIZON_HAZE) };
    shader.vertexShader = 'varying vec3 vChiWorld;\n' + shader.vertexShader.replace(
      '#include <begin_vertex>', '#include <begin_vertex>' + WORLD_POS_VERT,
    );
    shader.fragmentShader = `
varying vec3 vChiWorld;
uniform vec3 uSky;
` + shader.fragmentShader.replace('#include <opaque_fragment>', /* glsl */`
  {
    // Fresnel toward the sky, capped well short of 1. A full Fresnel makes the
    // whole river read as one slab of sky-blue paint from bank level, which is
    // where a visitor actually stands; capping it keeps the silt colour of a
    // prairie river in the mix all the way to the far shore.
    vec3 chiV = normalize(cameraPosition - vChiWorld);
    float chiF = pow(1.0 - clamp(dot(chiV, vec3(0.0, 1.0, 0.0)), 0.0, 1.0), 4.0);
    float chiRip = sin(vChiWorld.x * 0.42 + vChiWorld.z * 0.31) * 0.5 + 0.5;
    vec3 chiSky = uSky * (0.90 + 0.14 * chiRip);
    outgoingLight = mix(outgoingLight, chiSky, clamp(chiF, 0.0, 0.70));
  }
#include <opaque_fragment>
`);
  };
  mat.needsUpdate = true;
  return mat;
}

/**
 * The July ground: one 256 px tile of procedural prairie, drawn once into a
 * canvas. It is the ALBEDO of what lies under the sward — visible as itself
 * between the clumps, and standing in for the sward wholesale past the range
 * where flora.js still plants instances.
 *
 * The colour is a measurement, not a taste. In the two verified July
 * photographs, Illinois tallgrass in the last week of July sits around sRGB
 * (122,139,74) in the middle distance and (109,128,78) at the far edge of the
 * field — a yellow-green whose green channel leads its red by about fifteen.
 * Working that target back through this scene's light (measured off the render
 * itself: the sky fill plus sun multiply albedo by ×1.42 red, ×1.42 green,
 * ×1.63 blue) and its ACES + sRGB output chain asks for a mean albedo near sRGB
 * (95,107,62), which is what this tile averages. It lands at (119,134,75) in the
 * middle distance of `prairie_west` — within three or four units of the
 * photograph on every channel.
 *
 * What it replaces averaged (139,139,91) — red and green level, a khaki closer
 * in hue to `bar/mesic_remnant_2016-10-27.jpg`, the OCTOBER negative control,
 * than to either July photograph. That is the failure this ramp exists to fix,
 * so the numbers are written down rather than left as three literals.
 *
 * Four octaves, not two, and all four baked into the same tile so the shader
 * still costs exactly one fetch: 0.7 m clumps, 0.35 m tussocks, 0.17 m leaf
 * mass and a per-texel grain that mipmaps away into tone by twenty metres out.
 * A minority of dry thatch is mixed in — last season's litter is present under a
 * July sward, and the palette record keeps it to a minority, which is where it
 * stays: it tints about a quarter of the tile and reaches half strength nowhere,
 * moving the mean by roughly two units.
 *
 * The tile stays 256 px, i.e. 4 cm per texel over its 11 m footprint. Doubling
 * it bought nothing the eye can find past the first few metres — the octave
 * sizes are fractions of the tile and so do not change with resolution — and
 * cost the software rasteriser measurably, this being the one texture that
 * covers the screen. Detail here is bought in octaves, not in pixels.
 */
function prairieTexture() {
  const S = PRAIRIE_TILE_PX;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d');
  // The pixels are `prairie-tile.js`'s, so the tile a tool measures from Node is
  // the tile drawn here, texel for texel. The colour argument above is why they
  // are those pixels; that module only fills the buffer.
  const img = new ImageData(prairieTilePixels(), S, S);
  ctx.putImageData(img, 0, 0);

  const tex = new THREE.CanvasTexture(c);
  // The divisor that makes a substrate zone average exactly the triple its flora
  // record states — see zoneGlsl. Measured from the pixels, not a constant.
  tex.userData.meanLinearLuma = prairieTileMeanLuma(img.data);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  // Anisotropy stays at 4. Eight taps on a 512 px tile looked slightly cleaner
  // on the grazing mid-field and cost the software rasteriser half its frame
  // rate — the ground is most of the screen, so doubling its filter taps doubles
  // the most expensive fetch in the frame. Measured against this file's previous
  // revision on the `prairie_west` pose: 2.0 fps before, 1.0 with the eight taps,
  // 2.2 back at four on a 256 tile. One fps is enough to fail the smoke's "walk
  // intent moves the camera" check, which is wall-clock. Same lesson as the
  // one-fetch rule above; do not raise it without re-running that check.
  tex.anisotropy = 4;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** A drifting ripple normal map, generated once. */
function rippleTexture() {
  const S = 128;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(S, S);

  const h = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const u = (x / S) * Math.PI * 2;
      const v = (y / S) * Math.PI * 2;
      h[y * S + x] = Math.sin(u * 3 + Math.cos(v * 2) * 0.8) * 0.5
                   + Math.sin(v * 5 - u * 2) * 0.3
                   + Math.sin(u * 9 + v * 7) * 0.2;
    }
  }
  const at = (x, y) => h[((y + S) % S) * S + ((x + S) % S)];
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const dx = (at(x + 1, y) - at(x - 1, y)) * 0.5;
      const dy = (at(x, y + 1) - at(x, y - 1)) * 0.5;
      const len = Math.hypot(dx, dy, 1);
      const i = (y * S + x) * 4;
      img.data[i]     = Math.round((-dx / len * 0.5 + 0.5) * 255);
      img.data[i + 1] = Math.round((-dy / len * 0.5 + 0.5) * 255);
      img.data[i + 2] = Math.round((1 / len * 0.5 + 0.5) * 255);
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}
