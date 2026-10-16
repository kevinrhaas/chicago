/**
 * spatial-batch.js's triangle partition as a pure typed-array kernel (T-2599, the
 * first piece of T-2556's job system).
 *
 * It imports nothing, so a module worker can run it without the page's import map,
 * which some browsers do not apply inside a worker. Arrays in, arrays out: the main
 * thread wraps the result in `BufferGeometry` and the worker never sees three.
 *
 * **It is the partition `spatialPieces` always made, byte for byte**, and both
 * paths call it, so there is one partition and not two to keep in step. Whole
 * triangles go to a cell by their centre — the centre summed in corner order and
 * divided by three, exactly as before — cells come out in the order their first
 * triangle appears, an indexed piece keeps each vertex where it first appears in
 * the cell, and a piece's index is 16-bit unless a local index reaches 65535
 * (three's own `setIndex` rule). `tools/check_spatial_batch.mjs` holds it to the
 * implementation it replaced, on fixtures and on random geometry.
 */

// three's `denormalize` divisors; a signed type also clamps at -1.
const DENORMALIZE = new Map([
  [Uint32Array, [4294967295.0, false]], [Uint16Array, [65535.0, false]], [Uint8Array, [255.0, false]],
  [Int32Array, [2147483647.0, true]], [Int16Array, [32767.0, true]], [Int8Array, [127.0, true]],
]);

/** three's `denormalize`, so a normalized position is read as `getX` reads it. */
function reader(array, normalized) {
  if (!normalized || array.constructor === Float32Array) return (v) => v;
  const entry = DENORMALIZE.get(array.constructor);
  if (!entry) throw new Error('partitionTriangles: unsupported normalized position type');
  const [divisor, signed] = entry;
  return signed ? (v) => Math.max(v / divisor, -1) : (v) => v / divisor;
}

/**
 * @param {object} job
 * @param {{name: string, array: ArrayLike<number>, itemSize: number}[]} job.attributes
 * @param {number} job.positionAt   which of `attributes` is the position
 * @param {boolean} [job.positionNormalized]
 * @param {Uint16Array|Uint32Array|null} job.index
 * @param {number} job.count         index count, or position count when unindexed
 * @param {number} job.cellM
 * @param {number} job.heightM
 * @returns {{pieces: {arrays: ArrayLike<number>[], index: Uint16Array|Uint32Array|null}[]}}
 *          each piece's `arrays` in the order of `attributes`
 */
export function partitionTriangles({ attributes, positionAt, positionNormalized = false,
  index = null, count, cellM, heightM }) {
  const { array: pos, itemSize: ps } = attributes[positionAt];
  const read = reader(pos, positionNormalized);
  const chunks = new Map();
  for (let i = 0; i < count; i += 3) {
    const a = index ? index[i] : i;
    const b = index ? index[i + 1] : i + 1;
    const c = index ? index[i + 2] : i + 2;
    const x = (((0 + read(pos[a * ps])) + read(pos[b * ps])) + read(pos[c * ps])) / 3;
    const z = (((0 + read(pos[a * ps + 2])) + read(pos[b * ps + 2])) + read(pos[c * ps + 2])) / 3;
    const y = (((0 + read(pos[a * ps + 1])) + read(pos[b * ps + 1])) + read(pos[c * ps + 1])) / 3;
    const key = `${Math.floor(x / cellM)}:${Math.floor(z / cellM)}:${Math.floor(y / heightM)}`;
    let chunk = chunks.get(key);
    if (!chunk) { chunk = []; chunks.set(key, chunk); }
    chunk.push(a, b, c);
  }

  // An indexed piece takes each vertex once, where it first appears in the cell.
  // `seen` stamps a vertex with the cell that last took it, so no per-cell reset.
  const vertices = index ? Math.ceil(pos.length / ps) : 0;
  const seen = index ? new Int32Array(vertices).fill(-1) : null;
  const local = index ? new Uint32Array(vertices) : null;
  const pieces = [];
  let cell = 0;
  for (const ids of chunks.values()) {
    let unique = ids;
    let pieceIndex = null;
    if (index) {
      unique = [];
      for (const id of ids) {
        if (seen[id] !== cell) { seen[id] = cell; local[id] = unique.length; unique.push(id); }
      }
      pieceIndex = new (unique.length - 1 >= 65535 ? Uint32Array : Uint16Array)(ids.length);
      for (let i = 0; i < ids.length; i++) pieceIndex[i] = local[ids[i]];
    }
    const arrays = attributes.map(({ array, itemSize }) => {
      const data = new array.constructor(unique.length * itemSize);
      for (let i = 0; i < unique.length; i++) {
        const from = unique[i] * itemSize;
        for (let k = 0; k < itemSize; k++) data[i * itemSize + k] = array[from + k];
      }
      return data;
    });
    pieces.push({ arrays, index: pieceIndex });
    cell++;
  }
  return { pieces };
}
