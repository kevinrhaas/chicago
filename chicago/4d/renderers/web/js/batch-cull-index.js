/**
 * T-3731 — A STATIC BATCH'S CULL READS ITS BOUNDS ONCE, AND ASKS A WHOLE BLOCK AT A TIME.
 *
 * Measured on the owner's weak test PC class (i5-10400, UHD 630, `?device=weak`, 1904,
 * Balanced, 1920x1080, walking south down Prairie from 1600): the town is 129,844
 * BatchedMesh instances in 837 batches, 89,524 of them structure pieces and cells in
 * 712 batches, and their draw-list preparation was about 22 ms of the colour pass and
 * 22 ms of the sun's of a 73 ms frame — the frame was CPU-bound on it. three's own
 * `BatchedMesh.onBeforeRender` walks every instance of a batch in every pass: it reads
 * the instance's matrix out of the matrices texture, decodes its geometry's sphere
 * (batch-bounds.js keeps them packed), moves the sphere by the matrix, and tests it
 * against the six planes — for a structure, whose matrix and geometry never change
 * after load, the same arithmetic on the same numbers, frame after frame.
 *
 * So for a structure batch:
 *   - each instance's sphere in the batch's frame is computed ONCE, by the very calls
 *     three makes (`getMatrixAt`, `getBoundingSphereAt`, `Sphere.applyMatrix4`), and kept
 *     as doubles: the numbers three would have tested, bit for bit. The cache is made
 *     again whenever an instance is added or a matrix is written (each bumps the
 *     matrices texture's version), when a geometry is added, and when batch-bounds.js
 *     swaps the bounds getter;
 *   - the instances are pooled in CELL_M x CELL_M ground cells, each with the box that
 *     holds all of its spheres. A cell wholly behind one plane is passed over without
 *     touching its instances; a cell wholly inside all six keeps every visible one
 *     without testing it; only a cell across a plane tests its instances, by three's own
 *     test on three's own numbers. Both cell rulings are proofs (a sphere inside a box
 *     behind a plane is behind it; a sphere inside a box in front of every plane is in
 *     front of them all), with an EPS_M margin so float rounding can never decide one;
 *   - the kept list is sorted as three sorts it — by view depth, front to back (back to
 *     front for a blended batch), ties in instance order, which is what three's stable
 *     sort of a list pushed in instance order gives — so the multi-draw is the same
 *     entries in the same order, and every pixel is the same.
 *
 * Anything this does not prove the same is handed back to three: a custom sort (the view
 * filter's, the glass's), an array camera (WebXR), a wireframe material, an unsorted or
 * uncull'd batch. `?fastcull=0` turns it off for an on/off comparison of the same page.
 *
 * Only for batches whose instances never change geometry after load (buildings.js):
 * `setGeometryIdAt` bumps no version, so a batch that calls it must not use this.
 */
import * as THREE from 'three';

/** The ground cell instances are pooled in, metres of the batch's frame. */
export const CELL_M = 16;
/** A sphere bigger than this is tested on its own, not pooled. */
const LOOSE_RADIUS_M = CELL_M;
/** A cell ruling's margin: no float rounding in a cell's box comes near it. */
const EPS_M = 1e-3;

export const FAST_CULL_ON = (() => {
  try { return new URLSearchParams(globalThis.location?.search ?? '').get('fastcull') !== '0'; } catch { return true; }
})();
/** The live switch, for an A/B of one frame in one page (the probe flips `on`). */
export const fastCull = { on: FAST_CULL_ON };

const native = THREE.BatchedMesh.prototype.onBeforeRender;
const _m = new THREE.Matrix4();
const _s = new THREE.Sphere();
const _frustum = new THREE.Frustum();
const _pos = new THREE.Vector3();
const _fwd = new THREE.Vector3();

/**
 * Every instance's sphere in the batch's frame, and the cells they pool in, cached
 * until an instance, a matrix, a geometry or the bounds getter changes.
 * `cx, cy, cz, r` are exactly the sphere three's cull builds for that instance.
 */
export function cullIndexOf(batch) {
  const info = batch._instanceInfo;
  const n = info.length;
  const mv = batch._matricesTexture.version;
  const gn = batch._geometryInfo.length;
  const bounds = batch.getBoundingSphereAt;
  const compact = batch.userData.compactBounds ?? null;
  let c = batch.userData.cullIndex;
  if (c && c.n === n && c.mv === mv && c.gn === gn && c.bounds === bounds && c.compact === compact) return c;
  const cx = new Float64Array(n), cy = new Float64Array(n), cz = new Float64Array(n), r = new Float64Array(n);
  // each instance's index range, as three reads it off its geometry's row at the draw
  const drawStart = new Int32Array(n), drawCount = new Int32Array(n);
  const cellOf = new Map();
  const loose = [];
  for (let i = 0; i < n; i += 1) {
    if (!info[i].active) { r[i] = NaN; continue; }
    const row = batch._geometryInfo[info[i].geometryIndex];
    drawStart[i] = row.start; drawCount[i] = row.count;
    batch.getMatrixAt(i, _m);
    batch.getBoundingSphereAt(info[i].geometryIndex, _s).applyMatrix4(_m);
    cx[i] = _s.center.x; cy[i] = _s.center.y; cz[i] = _s.center.z; r[i] = _s.radius;
    if (!(_s.radius <= LOOSE_RADIUS_M) || ![_s.center.x, _s.center.y, _s.center.z].every(Number.isFinite)) {
      loose.push(i); continue;
    }
    const key = `${Math.floor(_s.center.x / CELL_M)},${Math.floor(_s.center.z / CELL_M)}`;
    const list = cellOf.get(key);
    if (list) list.push(i); else cellOf.set(key, [i]);
  }
  const cells = [...cellOf.values()];
  const cellCount = cells.length;
  const start = new Int32Array(cellCount + 1);
  const members = new Int32Array(cells.reduce((a, l) => a + l.length, 0));
  const box = new Float64Array(cellCount * 6);
  const rmax = new Float64Array(cellCount);
  let k = 0;
  cells.forEach((list, g) => {
    start[g] = k;
    let big = 0;
    let x0 = Infinity, y0 = Infinity, z0 = Infinity, x1 = -Infinity, y1 = -Infinity, z1 = -Infinity;
    for (const i of list) {
      members[k++] = i;
      big = Math.max(big, r[i]);
      x0 = Math.min(x0, cx[i] - r[i]); y0 = Math.min(y0, cy[i] - r[i]); z0 = Math.min(z0, cz[i] - r[i]);
      x1 = Math.max(x1, cx[i] + r[i]); y1 = Math.max(y1, cy[i] + r[i]); z1 = Math.max(z1, cz[i] + r[i]);
    }
    box.set([x0, y0, z0, x1, y1, z1], g * 6);
    rmax[g] = big;
  });
  start[cellCount] = k;
  c = { n, mv, gn, bounds, compact, cx, cy, cz, r, cellCount, start, members, box, rmax,
    loose: Int32Array.from(loose), drawStart, drawCount };
  batch.userData.cullIndex = c;
  return c;
}

/**
 * Which side of the planes a cell's box lies: -1 wholly behind one plane, 1 wholly in
 * front of all six, 0 across. `planes` is the frustum's, `b` the box's offset in `box`.
 */
export function cellSide(planes, box, b) {
  let inside = true;
  for (let p = 0; p < 6; p += 1) {
    const { normal: nv, constant: d } = planes[p];
    const nx = nv.x, ny = nv.y, nz = nv.z;
    const most = d + nx * (nx >= 0 ? box[b + 3] : box[b]) + ny * (ny >= 0 ? box[b + 4] : box[b + 1])
      + nz * (nz >= 0 ? box[b + 5] : box[b + 2]);
    if (most < -EPS_M) return -1;
    if (inside) {
      const least = d + nx * (nx >= 0 ? box[b] : box[b + 3]) + ny * (ny >= 0 ? box[b + 1] : box[b + 4])
        + nz * (nz >= 0 ? box[b + 2] : box[b + 5]);
      if (!(least > EPS_M)) inside = false;
    }
  }
  return inside ? 1 : 0;
}

/**
 * shadow-casters.js's ruling for a whole cell: -1 when every sphere in it, swept `reach`
 * along `down`, lies wholly behind one plane (so each piece's capsule does), 1 when the
 * box lies wholly in front of all six (so no piece's sphere is behind any), 0 otherwise.
 */
export function sweptCellSide(planes, box, b, dx, dy, dz, reach) {
  let inside = true;
  for (let p = 0; p < 6; p += 1) {
    const { normal: nv, constant: d } = planes[p];
    const nx = nv.x, ny = nv.y, nz = nv.z;
    const most = d + nx * (nx >= 0 ? box[b + 3] : box[b]) + ny * (ny >= 0 ? box[b + 4] : box[b + 1])
      + nz * (nz >= 0 ? box[b + 5] : box[b + 2]);
    const along = (nx * dx + ny * dy + nz * dz) * reach;
    if (most + (along > 0 ? along : 0) < -EPS_M) return -1;
    if (inside) {
      const least = d + nx * (nx >= 0 ? box[b] : box[b + 3]) + ny * (ny >= 0 ? box[b + 1] : box[b + 4])
        + nz * (nz >= 0 ? box[b + 2] : box[b + 5]);
      if (!(least > EPS_M)) inside = false;
    }
  }
  return inside ? 1 : 0;
}

/** three's `Frustum.intersectsSphere`, on the cached numbers, in its own order of operations. */
function sphereIn(planes, x, y, z, radius) {
  const negRadius = -radius;
  for (let p = 0; p < 6; p += 1) {
    const { normal: nv, constant: d } = planes[p];
    if (nv.x * x + nv.y * y + nv.z * z + d < negRadius) return false;
  }
  return true;
}

/**
 * One pass's working lists, shared by every batch (a pass prepares one batch at a time)
 * and grown to the largest batch: the kept instances, their depths and the sort's keys.
 */
const work = { size: 0, kept: null, z: null, order: null, spare: null, hi: null, lo: null };
function workFor(n) {
  if (work.size < n) {
    const size = Math.max(n, Math.ceil(work.size * 1.5), 1024);
    Object.assign(work, { size, kept: new Int32Array(size), z: new Float64Array(size),
      order: new Uint32Array(size), spare: new Uint32Array(size), hi: new Uint32Array(size), lo: new Uint32Array(size) });
  }
  return work;
}

const _f64 = new Float64Array(1);
const _u32 = new Uint32Array(_f64.buffer);
const _bucket = new Int32Array(257);
/** Below this many entries an insertion sort; above, a radix sort. */
const INSERTION_MAX = 48;

/**
 * The positions 0..k-1 of `w.kept` / `w.z` in three's draw order: by depth (front to back,
 * or back to front for a blended batch), equal depths in instance order. three sorts a
 * list it pushed in instance order with a stable sort on `a.z - b.z`, which is exactly
 * that order; this is the same total order, made without a comparator call per pair:
 * an insertion sort for a short list, a stable least-significant-digit radix sort of
 * (depth's IEEE bits made monotone, then instance) for a long one.
 */
export function sortByDepth(w, k, descending) {
  const { kept, z, hi, lo } = w;
  let order = w.order, spare = w.spare;
  for (let j = 0; j < k; j += 1) {
    // +0 for -0: the comparator holds them equal, the bits would not
    _f64[0] = (descending ? -z[j] : z[j]) + 0;
    let h = _u32[1], l = _u32[0];
    if (h & 0x80000000) { h = ~h >>> 0; l = ~l >>> 0; } else h = (h | 0x80000000) >>> 0;
    hi[j] = h; lo[j] = l;
    order[j] = j;
  }
  if (k <= INSERTION_MAX) {
    for (let a = 1; a < k; a += 1) {
      const p = order[a], ph = hi[p], pl = lo[p], pi = kept[p];
      let b = a - 1;
      while (b >= 0) {
        const q = order[b];
        if (hi[q] < ph || (hi[q] === ph && (lo[q] < pl || (lo[q] === pl && kept[q] < pi)))) break;
        order[b + 1] = q; b -= 1;
      }
      order[b + 1] = p;
    }
    return order.subarray(0, k);
  }
  // least significant first: the instance's three low bytes, then the depth's eight
  for (let pass = 0; pass < 11; pass += 1) {
    const src = pass < 3 ? kept : pass < 7 ? lo : hi;
    const shift = (pass < 3 ? pass : pass < 7 ? pass - 3 : pass - 7) * 8;
    _bucket.fill(0);
    for (let j = 0; j < k; j += 1) _bucket[((src[order[j]] >>> shift) & 255) + 1] += 1;
    // a digit every entry shares sorts nothing
    let trivial = false;
    for (let d = 1; d <= 256; d += 1) if (_bucket[d] === k) { trivial = true; break; } else if (_bucket[d]) break;
    if (trivial) continue;
    for (let d = 1; d <= 256; d += 1) _bucket[d] += _bucket[d - 1];
    for (let j = 0; j < k; j += 1) {
      const p = order[j];
      spare[_bucket[(src[p] >>> shift) & 255]++] = p;
    }
    const t = order; order = spare; spare = t;
  }
  return order.subarray(0, k);
}

/**
 * three's BatchedMesh.onBeforeRender for a static, sorted, frustum-culled batch, read
 * off the cache. The same multi-draw, entry for entry, as the prototype's.
 */
export function fastPrepare(renderer, scene, camera, geometry, material, group) {
  if (!fastCull.on || this.customSort !== null || !this.sortObjects || !this.perObjectFrustumCulled
      || camera.isArrayCamera || material.wireframe) {
    return native.call(this, renderer, scene, camera, geometry, material, group);
  }
  const index = geometry.getIndex();
  const bytesPerElement = index === null ? 1 : index.array.BYTES_PER_ELEMENT;
  const c = cullIndexOf(this);
  const info = this._instanceInfo;
  const multiDrawStarts = this._multiDrawStarts;
  const multiDrawCounts = this._multiDrawCounts;
  const indirectArray = this._indirectTexture.image.data;

  // the frustum, camera position and forward in the batch's frame, as three makes them
  _m.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse).multiply(this.matrixWorld);
  _frustum.setFromProjectionMatrix(_m, camera.coordinateSystem, camera.reversedDepth);
  _m.copy(this.matrixWorld).invert();
  _pos.setFromMatrixPosition(camera.matrixWorld).applyMatrix4(_m);
  _fwd.set(0, 0, -1).transformDirection(camera.matrixWorld).transformDirection(_m);
  const planes = _frustum.planes;
  const px = _pos.x, py = _pos.y, pz = _pos.z, fx = _fwd.x, fy = _fwd.y, fz = _fwd.z;
  const { cx, cy, cz, r, start, members, box, loose, drawStart, drawCount } = c;
  const w = workFor(c.n);
  const { kept, z } = w;

  // Each kept instance and its view depth, three's `_temp.subVectors(center, position).dot(forward)`.
  let k = 0;
  for (let g = 0; g < c.cellCount; g += 1) {
    const side = cellSide(planes, box, g * 6);
    if (side < 0) continue;
    for (let m = start[g], end = start[g + 1]; m < end; m += 1) {
      const i = members[m];
      const it = info[i];
      if (!it.visible || !it.active) continue;
      if (side > 0 || sphereIn(planes, cx[i], cy[i], cz[i], r[i])) {
        kept[k] = i; z[k] = (cx[i] - px) * fx + (cy[i] - py) * fy + (cz[i] - pz) * fz; k += 1;
      }
    }
  }
  for (let m = 0; m < loose.length; m += 1) {
    const i = loose[m];
    const it = info[i];
    if (!it.visible || !it.active) continue;
    if (sphereIn(planes, cx[i], cy[i], cz[i], r[i])) {
      kept[k] = i; z[k] = (cx[i] - px) * fx + (cy[i] - py) * fy + (cz[i] - pz) * fz; k += 1;
    }
  }
  // Instances made active after the cache (deleteInstance then addInstance bumps the
  // matrices' version, so the cache is new): nothing else can be missed.

  // three's stable sort of a list pushed in instance order: depth, then instance
  const sorted = sortByDepth(w, k, material.transparent);

  for (let j = 0; j < k; j += 1) {
    const i = kept[sorted[j]];
    multiDrawStarts[j] = drawStart[i] * bytesPerElement;
    multiDrawCounts[j] = drawCount[i];
    indirectArray[j] = i;
  }
  this._indirectTexture.needsUpdate = true;
  this._multiDrawCount = k;
  this._visibilityChanged = false;
}

/** Give a static batch the cached cull, beneath every wrapper installed after it. */
export function installFastCull(batch) {
  if (!batch?.isBatchedMesh || batch.onBeforeRender !== native) return false;
  batch.onBeforeRender = fastPrepare;
  return true;
}
