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
import { partitionTriangles } from './jobs/spatial-kernel.js';
import { jobsOnWorkers, runJob } from './jobs/pool.js';
import { coalesceRuns } from './batch-coalesce.js';

const CELL_M = 40;

// The partition itself is jobs/spatial-kernel.js, a pure typed-array kernel the
// main thread and the job pool's workers share (T-2599). This side validates the
// geometry, hands the kernel its arrays and wraps the arrays it returns.
function partitionJob(geometry, { cellM = CELL_M, heightM = Infinity } = {}) {
  if (!(cellM > 0 && Number.isFinite(cellM)) || !(heightM > 0)) {
    throw new Error('spatialPieces requires positive cell dimensions');
  }
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
  const entries = Object.entries(geometry.attributes);
  return {
    entries,
    job: {
      attributes: entries.map(([name, a]) => ({ name, array: a.array, itemSize: a.itemSize })),
      positionAt: entries.findIndex(([name]) => name === 'position'),
      positionNormalized: position.normalized,
      index: index ? index.array : null,
      count, cellM, heightM,
    },
  };
}

function piecesOf(entries, { pieces }) {
  return pieces.map(({ arrays, index }) => {
    const piece = new THREE.BufferGeometry();
    entries.forEach(([name, source], i) => {
      piece.setAttribute(name, new THREE.BufferAttribute(arrays[i], source.itemSize, source.normalized));
    });
    if (index) piece.setIndex(new THREE.BufferAttribute(index, 1));
    return piece;
  });
}

// Buildings can use tighter 3D cells inside their existing material batches.
// Partition whole triangles, preserving their exact attributes and winding.
export function spatialPieces(geometry, cells = {}) {
  const { entries, job } = partitionJob(geometry, cells);
  return piecesOf(entries, partitionTriangles(job));
}

/**
 * `spatialPieces` on the job pool: the same pieces, partitioned off the main thread
 * where the page has workers. The inputs go over as COPIES (a geometry here may be
 * a view on a buffer another geometry shares) and the pieces come back by transfer.
 * A worker that fails costs this call nothing but time: it partitions here instead.
 */
export async function spatialPiecesAsync(geometry, cells = {}) {
  const { entries, job } = partitionJob(geometry, cells);
  if (!jobsOnWorkers()) return piecesOf(entries, await runJob('partitionTriangles', job));
  const transfer = [];
  const own = (array) => { const copy = array.slice(); transfer.push(copy.buffer); return copy; };
  const sent = { ...job,
    attributes: job.attributes.map((a) => ({ ...a, array: own(a.array) })),
    index: job.index && own(job.index) };
  try {
    return piecesOf(entries, await runJob('partitionTriangles', sent, { transfer }));
  } catch {
    return piecesOf(entries, partitionTriangles(job));
  }
}

/**
 * The batch of a partition's pieces, in their order. The pieces carry every
 * triangle of the source exactly once, so the source's index (or position) count
 * is theirs summed, and a partition read back from a file (T-2692's prebuilt
 * ground) batches exactly as one cut on this page does.
 */
export function batchPieces(pieces, material) {
  const indexed = !!pieces[0]?.getIndex();
  const count = pieces.reduce((sum, p) => sum
    + (indexed ? p.getIndex().count : p.getAttribute('position').count), 0);
  const vertices = pieces.reduce((sum, p) => sum + p.getAttribute('position').count, 0);
  const batch = new THREE.BatchedMesh(pieces.length, vertices, indexed ? count : 0, material);
  for (const piece of pieces) {
    batch.addInstance(batch.addGeometry(piece));
    piece.dispose();
  }
  batch.computeBoundingBox();
  batch.computeBoundingSphere();
  // T-2927: the drawn pieces that touch are drawn as one (batch-coalesce.js). The
  // grid is for the frustum to reject; from the air it rejects little, and every
  // piece kept was a draw of its own.
  coalesceRuns(batch);
  // The first upload sends the complete backing arrays. addGeometry's per-piece
  // partial-update records are then dead heap objects (as in buildings.js).
  // Later setGeometryAt calls still append their own real update ranges.
  for (const attribute of [...Object.values(batch.geometry.attributes), batch.geometry.index]) {
    attribute?.clearUpdateRanges();
  }
  batch.userData.spatialBatch = { cellM: CELL_M, pieces: pieces.length, triangles: count / 3 };
  return batch;
}

export function spatialBatch(geometry, material) {
  return batchPieces(spatialPieces(geometry), material);
}

/** `spatialBatch` with its partition on the job pool; the same batch, resolved. */
export async function spatialBatchAsync(geometry, material) {
  return batchPieces(await spatialPiecesAsync(geometry), material);
}
