/**
 * Keep a ground surface in one material batch while giving the frustum small
 * pieces to reject. Town-wide road and yard meshes used to submit every yard
 * and road behind the visitor whenever any part of that surface was visible.
 *
 * These are the original triangles, attributes and material, not an LOD:
 * whole triangles are assigned to a fixed 40 m world grid by their centre.
 * Each piece's bounds include every corner, including corners across a grid
 * edge. Three's BatchedMesh tests those bounds per instance and still submits
 * the material in one multi-draw, as buildings.js already does for roofs.
 */
import * as THREE from 'three';

const CELL_M = 40;

export function spatialBatch(geometry, material) {
  const position = geometry.getAttribute('position');
  const index = geometry.getIndex();
  const count = index ? index.count : position.count;
  if (count % 3 || geometry.groups.length > 1
      || Object.values(geometry.attributes).some((a) => a.isInterleavedBufferAttribute
        || a.isInstancedBufferAttribute)) {
    throw new Error('spatialBatch requires plain, single-material triangles');
  }
  if (!position.array || (index && !index.array)
      || Object.values(geometry.attributes).some((a) => !a.array)) {
    // upload-release.js let a phone drop these after upload; flag the geometry
    // `userData.rereadBeforeRelease` where it is built (T-2180).
    throw new Error('spatialBatch needs page arrays a phone has already released');
  }
  const chunks = new Map();
  for (let i = 0; i < count; i += 3) {
    const ids = [0, 1, 2].map((j) => index ? index.getX(i + j) : i + j);
    const x = ids.reduce((sum, j) => sum + position.getX(j), 0) / 3;
    const z = ids.reduce((sum, j) => sum + position.getZ(j), 0) / 3;
    const key = `${Math.floor(x / CELL_M)}:${Math.floor(z / CELL_M)}`;
    let chunk = chunks.get(key);
    if (!chunk) { chunk = []; chunks.set(key, chunk); }
    chunk.push(...ids);
  }
  const pieces = [];
  let vertices = 0;
  for (const ids of chunks.values()) {
    const unique = index ? [...new Set(ids)] : ids;
    const piece = new THREE.BufferGeometry();
    for (const [name, source] of Object.entries(geometry.attributes)) {
      const data = new source.array.constructor(unique.length * source.itemSize);
      for (let i = 0; i < unique.length; i++) {
        const from = unique[i] * source.itemSize;
        data.set(source.array.subarray(from, from + source.itemSize), i * source.itemSize);
      }
      piece.setAttribute(name, new THREE.BufferAttribute(data, source.itemSize, source.normalized));
    }
    if (index) {
      const local = new Map(unique.map((id, i) => [id, i]));
      piece.setIndex(ids.map((id) => local.get(id)));
    }
    pieces.push(piece);
    vertices += unique.length;
  }
  const batch = new THREE.BatchedMesh(pieces.length, vertices, index ? count : 0, material);
  for (const piece of pieces) {
    batch.addInstance(batch.addGeometry(piece));
    piece.dispose();
  }
  batch.computeBoundingBox();
  batch.computeBoundingSphere();
  batch.userData.spatialBatch = { cellM: CELL_M, pieces: pieces.length, triangles: count / 3 };
  return batch;
}
