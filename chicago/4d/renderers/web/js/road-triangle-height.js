// SPDX-License-Identifier: GPL-3.0-or-later
/** Cached ENU height of actual Float32 road triangles, including worn overlays.
 * The highest drawn triangle is conservative where a fade is transparent. This
 * never changes terrain/walker ground. Rebuild if static mesh transforms change. */
export function createRoadTriangleHeight(meshes, { cell_m = 4 } = {}) {
  if (!Array.isArray(meshes) || !Number.isFinite(cell_m) || cell_m <= 0) throw Error('road triangle height: meshes and positive cell size required');
  let triangleCount = 0, aliasedBytes = 0;
  const buffers = new Set();
  let surfaces = meshes.map(mesh => {
    mesh.updateWorldMatrix(true, false);
    const position = mesh.geometry.getAttribute('position'), index = mesh.geometry.index;
    if (!position || position.itemSize !== 3 || !position.array) throw Error('road triangle height: retained actual positions required');
    const count = index?.count ?? position.count;
    if (count % 3) throw Error('road triangle height: incomplete triangle');
    for (const attribute of [position, index]) if (attribute?.array && !buffers.has(attribute.array.buffer)) {
      buffers.add(attribute.array.buffer); aliasedBytes += attribute.array.buffer.byteLength;
    }
    const first = triangleCount; triangleCount += count / 3;
    return { position, index, count, first, matrix: Float64Array.from(mesh.matrixWorld.elements) };
  });
  buffers.clear();
  let scratch = new Float64Array(9), disposed = false, queries = 0;
  function readTriangle(surface, offset) {
    const p = surface.position, m = surface.matrix;
    for (let k = 0; k < 3; k++) {
      const i = surface.index ? surface.index.getX(offset + k) : offset + k;
      const x = p.getX(i), y = p.getY(i), z = p.getZ(i), j = k * 3;
      scratch[j] = m[0] * x + m[4] * y + m[8] * z + m[12];
      scratch[j + 1] = -(m[2] * x + m[6] * y + m[10] * z + m[14]);
      scratch[j + 2] = m[1] * x + m[5] * y + m[9] * z + m[13];
    }
  }
  function eachTriangle(visit) {
    for (const surface of surfaces) for (let offset = 0; offset < surface.count; offset += 3) {
      readTriangle(surface, offset); visit(surface.first + offset / 3);
    }
  }
  let minE = Infinity, minN = Infinity, maxE = -Infinity, maxN = -Infinity;
  eachTriangle(() => {
    minE = Math.min(minE, Math.floor(Math.min(scratch[0], scratch[3], scratch[6]) / cell_m));
    maxE = Math.max(maxE, Math.floor(Math.max(scratch[0], scratch[3], scratch[6]) / cell_m));
    minN = Math.min(minN, Math.floor(Math.min(scratch[1], scratch[4], scratch[7]) / cell_m));
    maxN = Math.max(maxN, Math.floor(Math.max(scratch[1], scratch[4], scratch[7]) / cell_m));
  });
  const cols = triangleCount ? maxE - minE + 1 : 0, rows = triangleCount ? maxN - minN + 1 : 0;
  const cells = cols * rows;
  if (!Number.isSafeInteger(cells) || cells > 1e6) throw Error('road triangle height: unexpected static road extent');
  // Flat typed buckets avoid per-cell Map keys, array objects and copied XYZ.
  let starts = new Uint32Array(cells + 1), ids, nonempty = 0;
  const visitCells = visit => {
    const e0 = Math.floor(Math.min(scratch[0], scratch[3], scratch[6]) / cell_m) - minE;
    const e1 = Math.floor(Math.max(scratch[0], scratch[3], scratch[6]) / cell_m) - minE;
    const n0 = Math.floor(Math.min(scratch[1], scratch[4], scratch[7]) / cell_m) - minN;
    const n1 = Math.floor(Math.max(scratch[1], scratch[4], scratch[7]) / cell_m) - minN;
    for (let n = n0; n <= n1; n++) for (let e = e0; e <= e1; e++) visit(n * cols + e);
  };
  eachTriangle(() => visitCells(cell => { if (!starts[cell + 1]) nonempty++; starts[cell + 1]++; }));
  for (let i = 1; i <= cells; i++) starts[i] += starts[i - 1];
  const references = starts[cells]; ids = new Uint32Array(references);
  eachTriangle(id => visitCells(cell => { ids[--starts[cell + 1]] = id; }));
  for (let i = 0; i < cells; i++) starts[i] = starts[i + 1];
  starts[cells] = references;
  function readId(id) {
    let lo = 0, hi = surfaces.length - 1;
    while (lo < hi) { const mid = Math.ceil((lo + hi) / 2); if (surfaces[mid].first <= id) lo = mid; else hi = mid - 1; }
    const surface = surfaces[lo]; readTriangle(surface, (id - surface.first) * 3);
  }
  return {
    heightAt(e, n) {
      if (disposed || !Number.isFinite(e) || !Number.isFinite(n) || !triangleCount) return null;
      queries++;
      const x = Math.floor(e / cell_m) - minE, y = Math.floor(n / cell_m) - minN;
      if (x < 0 || y < 0 || x >= cols || y >= rows) return null;
      const cell = y * cols + x; let height = null;
      for (let i = starts[cell]; i < starts[cell + 1]; i++) {
        readId(ids[i]); const p = scratch;
        const denominator = (p[4] - p[7]) * (p[0] - p[6]) + (p[6] - p[3]) * (p[1] - p[7]);
        if (Math.abs(denominator) < 1e-12) continue;
        const a = ((p[4] - p[7]) * (e - p[6]) + (p[6] - p[3]) * (n - p[7])) / denominator;
        const b = ((p[7] - p[1]) * (e - p[6]) + (p[0] - p[6]) * (n - p[7])) / denominator;
        const c = 1 - a - b;
        if (Math.min(a, b, c) < -1e-9) continue;
        const z = a * p[2] + b * p[5] + c * p[8]; height = height === null ? z : Math.max(height, z);
      }
      return height;
    },
    reading() { return { disposed, surfaces: surfaces.length, triangles: disposed ? 0 : triangleCount,
      grid_cells: disposed ? 0 : cells, nonempty_buckets: disposed ? 0 : nonempty,
      triangle_references: disposed ? 0 : references, queries,
      owned_buffer_bytes: disposed ? 0 : starts.byteLength + ids.byteLength + scratch.byteLength + surfaces.length * 16 * 8,
      aliased_geometry_bytes: disposed ? 0 : aliasedBytes, duplicated_xyz_bytes: 0 }; },
    dispose() { disposed = true; surfaces = []; starts = ids = scratch = null; },
  };
}
