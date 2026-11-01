/**
 * T-3286 — A FAR STRUCTURE CASTS ITS SHADOW FROM A COARSER COPY OF ITSELF.
 *
 * The sun's pass drew every structure piece inside its box whole, whatever its
 * distance from the visitor. Looking north up Prairie at Glessner from 60 m east
 * and 120 m south (T-3285's worst far stand, Full, 1280x800), the structures' sun
 * pass was 3,080,120 of the frame's 7.29 M triangles, in 1,191 pieces, and none of
 * those pieces is small: a house is about 25 of them, 16-64 px across on screen
 * there, so no piece can simply be left out. What a far piece CAN leave out is its
 * fine relief: Glessner's rusticated stone and tile courses, the mouldings and
 * frames of every neighbour, detail measured in millimetres that the shadow map
 * (a 0.117 m texel at `full`, world.js) cannot hold anyway.
 *
 * So each heavy piece gets a SHADOW TWIN, cut once at load by vertex clustering:
 * the piece's vertices are pooled in cells of CELL_M (and never across two
 * confidence values, so the depth material's dither stays where it was), each
 * pool becomes one vertex at its centroid, and every triangle whose three corners
 * do not land in three different pools is dropped. A twin is kept only where it
 * pays: at most KEEP_RATIO of the piece's triangles and at least MIN_SAVED fewer.
 * At CELL_M = 6 cm that is about a hundred pieces town-wide in 1904; Glessner's
 * 1.17 M sun-pass triangles at the far stand become about 25,000.
 *
 * THE TEST IS A BOUND ON THE SCREEN, taken from the VIEW camera. A twin vertex
 * sits at most sqrt(3) * CELL_M from every piece vertex it stands for (a centroid
 * of points in one cube), so a shadow edge it casts moves at most that far across
 * the light, and on the receiver at most that over the sine of the sun's height.
 * The piece is swapped for its twin in the sun's pass only where that movement
 * projects to at most MAX_PIXELS at the nearest view depth its shadow can land
 * on — the piece's bounding sphere swept down the sun's direction to
 * FLOOR_BELOW_M under its base, as shadow-casters.js sweeps it. Nearer than that,
 * or with the sun too low to bound the sweep, the piece casts whole as before.
 * It is an LOD of the shadow map, not a proof: an edge may move by up to a
 * pixel, and tools/qa_t3286_far_shadow.mjs reads every pixel of each held frame
 * back off and on to say how many did.
 *
 * The colour pass never draws a twin: it sits hidden the rest of the time, so
 * picking, the Confidence view and every reader of the batch see the piece
 * exactly as before, and the swap is undone the moment the shadow draw list is
 * prepared, the way shadow-casters.js and far-roof-relief.js do it.
 *
 * `?farshadow=0` turns it off, for the on/off pixel proof.
 */
import * as THREE from 'three';
import { FLOOR_BELOW_M } from './shadow-casters.js';

/** The clustering cell, in metres of the structure's own frame. */
export const CELL_M = 0.06;
/** The most a swapped shadow edge may move on screen, in pixels. */
export const MAX_PIXELS = 1;
/** A twin is kept only at or under this share of its piece's triangles... */
export const KEEP_RATIO = 0.5;
/** ...and only if it draws at least this many triangles fewer. */
export const MIN_SAVED = 500;
/** Below this sine of the sun's height the sweep grows without bound: cast whole. */
const LOW_SUN = 0.05;
/** The farthest a twin vertex sits from any vertex it stands for, per metre of cell. */
const CENTROID_REACH = Math.sqrt(3);

export function farShadowFromSearch(search) {
  try { return new URLSearchParams(search ?? '').get('farshadow') !== '0'; } catch { return true; }
}

/**
 * The clustered twin of one piece, or null when it would not pay.
 * @param {THREE.BufferGeometry} geo  an indexed, non-interleaved piece, in its own frame
 * @param {number} cell  the cell in the geometry's units (CELL_M over the placement's scale)
 */
export function shadowTwin(geo, cell) {
  const index = geo.getIndex();
  const position = geo.getAttribute('position');
  if (!index || !position || !(cell > 0)) return null;
  if (Object.values(geo.attributes).some((a) => a.isInterleavedBufferAttribute)) return null;
  const ix = index.array;
  const triangles = ix.length / 3;
  if (triangles < MIN_SAVED) return null;
  const confidence = geo.getAttribute('_confidence');
  const n = position.count;
  const pa = position.array;
  const stride = position.itemSize;
  const pool = new Int32Array(n);
  // A cell is three 15-bit axes and the confidence's byte (as packScalars stores it), one
  // exact integer under 2^53, so the pools key a Map by number: about a third of a
  // second for the 1904 town's every piece, where string keys took two.
  const keyOf = new Map();
  const first = [];
  const sum = [];
  let ox = Infinity, oy = Infinity, oz = Infinity;
  for (let v = 0; v < n; v++) {
    const o = v * stride;
    if (pa[o] < ox) ox = pa[o];
    if (pa[o + 1] < oy) oy = pa[o + 1];
    if (pa[o + 2] < oz) oz = pa[o + 2];
  }
  const AXIS = 32768;
  for (let v = 0; v < n; v++) {
    const o = v * stride;
    const x = pa[o], y = pa[o + 1], z = pa[o + 2];
    const cx = Math.floor((x - ox) / cell), cy = Math.floor((y - oy) / cell), cz = Math.floor((z - oz) / cell);
    if (cx >= AXIS || cy >= AXIS || cz >= AXIS) return null; // a piece over ~2 km: leave it whole
    const c = confidence ? Math.round(Math.min(1, Math.max(0, confidence.getX(v))) * 254) : 0;
    const key = ((c * AXIS + cx) * AXIS + cy) * AXIS + cz;
    let p = keyOf.get(key);
    if (p === undefined) {
      p = first.length;
      keyOf.set(key, p);
      first.push(v);
      sum.push(0, 0, 0, 0);
    }
    pool[v] = p;
    sum[p * 4] += x; sum[p * 4 + 1] += y; sum[p * 4 + 2] += z; sum[p * 4 + 3] += 1;
  }
  const pools = first.length;
  const kept = [];
  const seen = new Set();
  for (let t = 0; t < ix.length; t += 3) {
    const a = pool[ix[t]], b = pool[ix[t + 1]], c = pool[ix[t + 2]];
    if (a === b || b === c || a === c) continue;
    // one triangle per pooled corner set and winding: a duplicate adds no depth
    let r0 = a, r1 = b, r2 = c;
    if (b < a && b < c) { r0 = b; r1 = c; r2 = a; } else if (c < a && c < b) { r0 = c; r1 = a; r2 = b; }
    const key = (r0 * pools + r1) * pools + r2;
    if (key > Number.MAX_SAFE_INTEGER) return null; // over ~200,000 pools: leave it whole
    if (seen.has(key)) continue;
    seen.add(key);
    kept.push(a, b, c);
  }
  const twinTriangles = kept.length / 3;
  if (twinTriangles > triangles * KEEP_RATIO || triangles - twinTriangles < MIN_SAVED) return null;
  // only the pools a kept triangle uses
  const remap = new Int32Array(first.length).fill(-1);
  const order = [];
  for (let i = 0; i < kept.length; i++) {
    const p = kept[i];
    if (remap[p] < 0) { remap[p] = order.length; order.push(p); }
    kept[i] = remap[p];
  }
  const twin = new THREE.BufferGeometry();
  for (const [name, attr] of Object.entries(geo.attributes)) {
    const size = attr.itemSize;
    const data = new attr.array.constructor(order.length * size);
    for (let i = 0; i < order.length; i++) {
      const p = order[i];
      if (name === 'position') {
        // the centroid: inside the piece's own extent, so it quantizes on the structure's grid
        const w = sum[p * 4 + 3];
        data[i * 3] = sum[p * 4] / w; data[i * 3 + 1] = sum[p * 4 + 1] / w; data[i * 3 + 2] = sum[p * 4 + 2] / w;
      } else {
        // every other attribute is its pool's first vertex: the depth pass reads only
        // the confidence, and the pool never mixes two of those
        for (let k = 0; k < size; k++) data[i * size + k] = attr.array[first[p] * size + k];
      }
    }
    twin.setAttribute(name, new THREE.BufferAttribute(data, size, attr.normalized));
  }
  const fits16 = order.length <= 65535;
  twin.setIndex(new THREE.BufferAttribute(fits16 ? Uint16Array.from(kept) : Uint32Array.from(kept), 1));
  twin.userData = { ...geo.userData };
  return { geo: twin, triangles, twinTriangles, reach: CENTROID_REACH * cell };
}

/** The farthest a twin's shadow edge can sit from the piece's, in metres. */
export function twinReachM(cellM = CELL_M) {
  return CENTROID_REACH * cellM;
}

const _sphere = new THREE.Sphere();
const _m = new THREE.Matrix4();
const _size = new THREE.Vector2();
const _end = new THREE.Vector3();

/**
 * Hide each piece of `pairs` whose twin's error cannot exceed MAX_PIXELS anywhere its
 * shadow can land, and show its twin; returns the swapped pairs, for `restore`.
 */
function swapFar(batch, renderer, camera, sun, pairs, swapped, maxPixels) {
  renderer.getDrawingBufferSize(_size);
  const pixels = _size.y * camera.projectionMatrix.elements[5] / 2;
  const view = camera.matrixWorldInverse;
  const v = view.elements;
  // view depth of a world point is -(row 2 of the view matrix) . point
  const depth = (p) => -(v[2] * p.x + v[6] * p.y + v[10] * p.z + v[14]);
  for (const p of pairs) {
    if (!batch.getVisibleAt(p.piece)) continue;
    batch.getMatrixAt(p.piece, _m);
    batch.getBoundingSphereAt(batch.getGeometryIdAt(p.piece), _sphere)
      .applyMatrix4(_m).applyMatrix4(batch.matrixWorld);
    const r = _sphere.radius;
    _end.copy(_sphere.center).addScaledVector(sun, -(2 * r + FLOOR_BELOW_M) / sun.y);
    // depth is linear along the sweep, so the capsule's nearest point is at one end
    const nearest = Math.min(depth(_sphere.center), depth(_end)) - r;
    if (!(nearest > 0)) continue;
    // `reachM` is in metres: the cell was cut as CELL_M over the placement's own scale
    if (p.reachM * pixels / (sun.y * nearest) > maxPixels) continue;
    // follow the piece if anything moved it since load
    batch.getMatrixAt(p.twin, _mTwin);
    if (!_mTwin.equals(_m)) batch.setMatrixAt(p.twin, _m);
    batch.setVisibleAt(p.piece, false);
    batch.setVisibleAt(p.twin, true);
    swapped.push(p);
  }
  return swapped;
}
const _mTwin = new THREE.Matrix4();

function restore(batch, swapped) {
  for (const p of swapped) {
    batch.setVisibleAt(p.twin, false);
    batch.setVisibleAt(p.piece, true);
  }
}

/**
 * Wrap one batch's shadow preparation. `pairs` is filled as instances are added:
 * `{ piece, twin, reachM, saved }`, instance ids in this batch. Install AFTER
 * far-roof-relief.js (so a relief piece swapped here is never also crest-swapped:
 * that hook passes over a hidden piece) and BEFORE batch-frustum-box.js's narrow
 * phase, which only trusts the hook it wrapped.
 * @param {THREE.BatchedMesh} batch
 * @param {{on:boolean, sun:()=>THREE.Vector3|null, pairs:Array, maxPixels?:number, swapped?:number, saved?:number}} state
 *   `maxPixels` (default MAX_PIXELS) is the screen bound, for a harness that measures it.
 */
export function drawFarShadowAsTwins(batch, state) {
  const prepareShadow = batch.onBeforeShadow;
  const swapped = [];
  batch.onBeforeShadow = function (renderer, object, camera, shadowCamera, geometry, depthMaterial, group) {
    const sun = state.on && camera && state.pairs.length ? state.sun() : null;
    if (!sun || !(sun.y >= LOW_SUN)) {
      state.swapped = 0; state.saved = 0;
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    }
    swapFar(this, renderer, camera, sun, state.pairs, swapped, state.maxPixels ?? MAX_PIXELS);
    try {
      return prepareShadow.call(this, renderer, object, camera, shadowCamera, geometry, depthMaterial, group);
    } finally {
      state.swapped = swapped.length;
      let saved = 0;
      for (const p of swapped) saved += p.saved;
      state.saved = saved;
      restore(this, swapped);
      swapped.length = 0;
    }
  };
}
