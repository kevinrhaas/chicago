/** T-2037: refine distant-ground cells under emitted board crossings.
 * Shared edge samples keep coarse/fine neighbours joined. This changes only
 * the renderer mesh; the heightfield and walker stay authoritative.
 * `tolerance` triggers refinement from the coarse mesh's overrun at recorded
 * heightfield vertices. It is not a bound on bilinear interpolation between
 * those vertices. check_plank_ground.mjs verifies actual deck/mesh clearance.
 */
export function adaptiveGroundGrid(hf, stride = 6, tolerance = 0.025, footprints = []) {
  stride = Math.max(1, Math.floor(stride));
  const { cols, rows, cellM, originE, originN, data } = hf;
  const xs = [], ys = [];
  for (let c = 0; c < cols - 1; c += stride) xs.push(c);
  for (let r = 0; r < rows - 1; r += stride) ys.push(r);
  xs.push(cols - 1); ys.push(rows - 1);
  const w = xs.length - 1, h = ys.length - 1;
  const refined = new Uint8Array(w * h);
  // Restrict refinement to the surfaces that must remain above their ground.
  // Bounding cells are conservative; no deck vertex or walking height moves.
  const protectedCells = new Set();
  for (const {pts} of footprints || []) {
    if (!pts?.length) continue;
    const cs = pts.map(p => (p[0] - originE) / cellM / stride);
    const rs = pts.map(p => (p[1] - originN) / cellM / stride);
    for (let r = Math.max(0, Math.floor(Math.min(...rs))); r <= Math.min(h - 1, Math.floor(Math.max(...rs))); r++)
      for (let c = Math.max(0, Math.floor(Math.min(...cs))); c <= Math.min(w - 1, Math.floor(Math.max(...cs))); c++) protectedCells.add(r * w + c);
  }
  const height = (c, r) => data[r * cols + c];
  let refinedCells = 0, maxOverrun = 0;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    if (!protectedCells.has(j * w + i)) continue;
    const x0 = xs[i], x1 = xs[i + 1], y0 = ys[j], y1 = ys[j + 1];
    const a = height(x0, y0), b = height(x1, y0);
    const c = height(x0, y1), d = height(x1, y1);
    let error = 0;
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const u = (x - x0) / (x1 - x0), v = (y - y0) / (y1 - y0);
      const coarse = u + v <= 1 ? a + (b - a) * u + (c - a) * v
        : d + (c - d) * (1 - u) + (b - d) * (1 - v);
      error = Math.max(error, coarse - height(x, y));
    }
    maxOverrun = Math.max(maxOverrun, error);
    if (error > tolerance) { refined[j * w + i] = 1; refinedCells++; }
  }
  const position = [], index = [], vertices = new Map();
  const vert = (c, r) => {
    const key = r * cols + c;
    if (vertices.has(key)) return vertices.get(key);
    const id = position.length / 3;
    position.push(originE + c * cellM, height(c, r), -(originN + r * cellM));
    vertices.set(key, id);
    return id;
  };
  const fine = (i, j) => i >= 0 && i < w && j >= 0 && j < h && refined[j * w + i];
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const x0 = xs[i], x1 = xs[i + 1], y0 = ys[j], y1 = ys[j + 1];
    if (fine(i, j)) {
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
        const a = vert(x, y), b = vert(x + 1, y), c = vert(x, y + 1), d = vert(x + 1, y + 1);
        index.push(a, b, c, b, d, c);
      }
    } else if (fine(i, j - 1) || fine(i + 1, j) || fine(i, j + 1) || fine(i - 1, j)) {
      const edge = [];
      for (let x = x0; x < x1; x += fine(i, j - 1) ? 1 : x1 - x0) edge.push(vert(x, y0));
      for (let y = y0; y < y1; y += fine(i + 1, j) ? 1 : y1 - y0) edge.push(vert(x1, y));
      for (let x = x1; x > x0; x -= fine(i, j + 1) ? 1 : x1 - x0) edge.push(vert(x, y1));
      for (let y = y1; y > y0; y -= fine(i - 1, j) ? 1 : y1 - y0) edge.push(vert(x0, y));
      const c = (x0 + x1) / 2, r = (y0 + y1) / 2;
      const center = position.length / 3;
      position.push(originE + c * cellM, hf.sample(originE + c * cellM, originN + r * cellM), -(originN + r * cellM));
      for (let k = 0; k < edge.length; k++) index.push(center, edge[k], edge[(k + 1) % edge.length]);
    } else {
      const a = vert(x0, y0), b = vert(x1, y0), c = vert(x0, y1), d = vert(x1, y1);
      index.push(a, b, c, b, d, c);
    }
  }
  return { position: new Float32Array(position), index: new Uint32Array(index),
    stats: { cells: w * h, protectedCells: protectedCells.size, refinedCells, maxOverrun, triangles: index.length / 3, tolerance } };
}
