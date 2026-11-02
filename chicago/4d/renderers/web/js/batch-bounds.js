/**
 * batch-bounds.js — a BatchedMesh's per-geometry bounds, kept in two typed
 * arrays instead of a Box3 and a Sphere apiece (T-3173).
 *
 * three.js caches each geometry's box and sphere on its `_geometryInfo` row the
 * first time an instance is culled, sorted or picked, and upload-release.js asks
 * for every one of them before a phone lets the positions go, so it never needs
 * them again. Each is a `Box3` (two `Vector3`s) and a `Sphere` (a `Vector3` and
 * a radius): five objects and ten numbers, and in Chrome's compressed heap every
 * one of those numbers is a boxed double of its own. On /1904/ at the phone's
 * tier that was 83,300 geometries and about 20 MB of the JS heap (a heap snapshot
 * read by holder, 2026-11-02, build c4923d59) — the largest single holder in it,
 * for forty bytes of figures a geometry.
 *
 * `compactBatchBounds(batch)` moves the figures into one Float32Array of six per
 * geometry (box min, max) and one of four (sphere centre, radius), drops the
 * objects, and gives the batch its own `getBoundingBoxAt` / `getBoundingSphereAt`
 * that read them back. Every reader of a geometry's bounds — three's own cull,
 * sort and raycast, and this renderer's (shadow-casters.js, gpu-pick.js,
 * view-occlusion.js, texture-residency.js, far-shadow.js) — goes through those
 * two methods, so nothing else has to know.
 *
 * ROUNDED OUTWARD, so the cull stays conservative: a box's min is rounded down
 * and its max up to the next float32, and a sphere's radius grows by however far
 * its centre moved in rounding, then up. A geometry's stored positions are
 * quantized to ±1 in its structure's frame (compact-attributes.js), so a float32
 * step there is a few nanometres; nothing can be culled that was drawn before.
 *
 * A row is only ever read back while it is current. `setGeometryAt` (which three
 * also calls when `addGeometry` reuses a deleted slot) drops the row, so three
 * computes that geometry's bounds afresh off its new positions, as it would have
 * (a deleted geometry keeps its row until then, as three keeps its cached box); a geometry added after the compaction has no row at all and
 * is three's as before. A row three set by hand afterwards (an `info.boundingBox`
 * that is not null) wins over the stored one, as it would have.
 */

import * as THREE from 'three';

const f32 = new Float32Array(1);
const u32 = new Uint32Array(f32.buffer);

/** The next float32 above `x` (x itself a float32, finite). */
function nextUp(x) {
  if (x === 0) { u32[0] = 1; return f32[0]; }
  f32[0] = x;
  u32[0] += x > 0 ? 1 : -1;
  return f32[0];
}

/** The next float32 below `x` (x itself a float32, finite). */
function nextDown(x) { return -nextUp(-x); }

/** `x` as a float32 no greater than it. */
export function floorF32(x) {
  const f = Math.fround(x);
  return f > x && Number.isFinite(f) ? nextDown(f) : f;
}

/** `x` as a float32 no less than it. */
export function ceilF32(x) {
  const f = Math.fround(x);
  return f < x && Number.isFinite(f) ? nextUp(f) : f;
}

/**
 * Move every computed box and sphere of `batch`'s geometries into typed arrays.
 * A geometry with no cached bounds yet is left to three. Returns how many rows
 * were stored (0 on a second call: a batch is compacted once).
 */
export function compactBatchBounds(batch) {
  const info = batch?._geometryInfo;
  if (!batch?.isBatchedMesh || !Array.isArray(info) || batch.userData.compactBounds) return 0;
  const n = info.length;
  const boxes = new Float32Array(n * 6);
  const spheres = new Float32Array(n * 4);
  const stored = new Uint8Array(n);
  let rows = 0;
  for (let id = 0; id < n; id += 1) {
    const gi = info[id];
    if (!gi || gi.active === false || !gi.boundingBox || !gi.boundingSphere) continue;
    const { min, max } = gi.boundingBox;
    const { center, radius } = gi.boundingSphere;
    // An empty box (min > max) or an unbounded sphere stays three's own.
    if (!(min.x <= max.x && min.y <= max.y && min.z <= max.z)) continue;
    if (![min.x, min.y, min.z, max.x, max.y, max.z, center.x, center.y, center.z, radius].every(Number.isFinite)) continue;
    const b = id * 6;
    boxes[b] = floorF32(min.x); boxes[b + 1] = floorF32(min.y); boxes[b + 2] = floorF32(min.z);
    boxes[b + 3] = ceilF32(max.x); boxes[b + 4] = ceilF32(max.y); boxes[b + 5] = ceilF32(max.z);
    const s = id * 4;
    const cx = Math.fround(center.x), cy = Math.fround(center.y), cz = Math.fround(center.z);
    spheres[s] = cx; spheres[s + 1] = cy; spheres[s + 2] = cz;
    spheres[s + 3] = ceilF32(radius + Math.hypot(cx - center.x, cy - center.y, cz - center.z));
    gi.boundingBox = null;
    gi.boundingSphere = null;
    stored[id] = 1;
    rows += 1;
  }
  const proto = THREE.BatchedMesh.prototype;
  // As three's own: past the count there is nothing; otherwise the row, active or not.
  const current = (self, id) => id < self._geometryCount && stored[id] === 1;
  batch.getBoundingBoxAt = function getBoundingBoxAtCompact(geometryId, target) {
    const gi = this._geometryInfo[geometryId];
    if (gi && gi.boundingBox === null && current(this, geometryId)) {
      const b = geometryId * 6;
      target.min.set(boxes[b], boxes[b + 1], boxes[b + 2]);
      target.max.set(boxes[b + 3], boxes[b + 4], boxes[b + 5]);
      return target;
    }
    return proto.getBoundingBoxAt.call(this, geometryId, target);
  };
  batch.getBoundingSphereAt = function getBoundingSphereAtCompact(geometryId, target) {
    const gi = this._geometryInfo[geometryId];
    if (gi && gi.boundingSphere === null && current(this, geometryId)) {
      const s = geometryId * 4;
      target.center.set(spheres[s], spheres[s + 1], spheres[s + 2]);
      target.radius = spheres[s + 3];
      return target;
    }
    return proto.getBoundingSphereAt.call(this, geometryId, target);
  };
  batch.setGeometryAt = function setGeometryAtCompact(geometryId, geometry) {
    if (geometryId < n) stored[geometryId] = 0;
    return proto.setGeometryAt.call(this, geometryId, geometry);
  };
  batch.userData.compactBounds = { rows, bytes: boxes.byteLength + spheres.byteLength + stored.byteLength };
  return rows;
}
