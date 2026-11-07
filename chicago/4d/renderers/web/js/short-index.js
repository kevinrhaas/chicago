/**
 * short-index.js — a phone's structure batches index with 16 bits (T-3408).
 *
 * three's BatchedMesh picks its index type from the vertices it is sized for:
 * `maxVertexCount > 65535` makes a Uint32Array index, anything smaller a
 * Uint16Array. Every index value is absolute in the batch (`vertexStart +
 * index`), and WebGL2 has no base vertex without an extension iOS does not
 * ship, so a batch over 65,535 vertices pays four bytes an index for every
 * triangle corner it holds, all of them.
 *
 * Measured on /1904/ at 390x780 (dev 4610867c3, 2026-11-06): eight structure
 * batches held 4.3 million of the town's 6.6 million structure vertices, and
 * their 6.4 million 32-bit indices were 25.6 MB of the phone's 188 MB of GPU
 * buffers. The same corners at 16 bits are 12.8 MB. Nothing drawn changes: the
 * same geometries, the same instances, the same material, the same triangles in
 * the same order within each batch. Only the batch they are drawn from does.
 *
 * So on a phone (`lowSpec`, buildings.js) a material bucket larger than that is
 * laid as several batches that share its material, depth material, compact plan
 * and tone scale, each at most `SHORT_INDEX_VERTICES` vertices:
 *
 *   - A PIECE KEEPS ITS TWINS. Its crests-only relief twin (T-3272), shadow twin
 *     (T-3286) and colour twin (T-3312) are instances in the piece's own batch
 *     and are swapped in by instance id, so a run is a piece and every twin of
 *     it, never less.
 *   - A STRUCTURE STAYS TOGETHER WHERE IT FITS. Its pieces are consecutive in
 *     the bucket, and the drawn cells of one mesh join into one draw only inside
 *     one batch (T-2927, batch-coalesce.js), so a structure is moved whole to a
 *     fresh batch rather than cut, unless it alone is larger than a batch.
 *   - ORDER IS KEPT. Each batch holds its entries in the bucket's own order, so
 *     every piece is added before its twins, as buildings.js needs.
 *   - A PIECE LARGER THAN A BATCH is laid alone and keeps its 32-bit index.
 *
 * The cost is a few more batches (eight became 71 on that phone, of 461), each
 * one multi-draw; the draws a visitor's frame makes are counted per entry
 * (T-2970), and those are unchanged. A desktop is never split.
 */

/** The most vertices a BatchedMesh may be sized for and still index in 16 bits. */
export const SHORT_INDEX_VERTICES = 65535;

/** The piece a twin stands in for, or the entry itself. */
export function pieceOf(entry) {
  return entry.twinOf || entry.shadowOf || entry.colourOf || entry;
}

const verticesOf = (entry) => entry.geo.getAttribute('position').count;

/**
 * `entries` cut into runs that each fit a 16-bit index, in order. One run (the
 * array itself) when they already fit.
 *
 * @param {Array<{ record: { id: string }, geo: object, twinOf?: object, shadowOf?: object, colourOf?: object }>} entries
 * @param {number} [limit]
 * @returns {Array<Array<object>>}
 */
export function shortIndexRuns(entries, limit = SHORT_INDEX_VERTICES) {
  let total = 0;
  for (const e of entries) total += verticesOf(e);
  if (total <= limit) return [entries];
  // Each piece's vertices with every twin of it.
  const unit = new Map();
  for (const e of entries) {
    const p = pieceOf(e);
    unit.set(p, (unit.get(p) ?? 0) + verticesOf(e));
  }
  // The pieces in order, as runs of one structure.
  const structures = [];
  for (const e of entries) {
    if (pieceOf(e) !== e) continue;
    const last = structures[structures.length - 1];
    if (last && last.id === e.record.id) { last.pieces.push(e); last.vertices += unit.get(e); }
    else structures.push({ id: e.record.id, pieces: [e], vertices: unit.get(e) });
  }
  const runOf = new Map();
  let run = 0; let held = 0;
  const place = (piece) => { runOf.set(piece, run); held += unit.get(piece); };
  const next = () => { if (held > 0) { run += 1; held = 0; } };
  for (const s of structures) {
    if (held + s.vertices <= limit) { for (const p of s.pieces) place(p); continue; }
    if (s.vertices <= limit) { next(); for (const p of s.pieces) place(p); continue; }
    for (const p of s.pieces) {
      if (held + unit.get(p) > limit) next();
      place(p);
    }
  }
  const runs = Array.from({ length: run + 1 }, () => []);
  for (const e of entries) runs[runOf.get(pieceOf(e))].push(e);
  return runs.filter((r) => r.length);
}
