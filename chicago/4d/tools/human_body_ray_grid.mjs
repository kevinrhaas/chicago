// SPDX-License-Identifier: GPL-3.0-or-later
// Conservative broad phase only. Actual THREE.Ray.intersectTriangle still decides hits.
export function rayTriangleCandidates(grid, minimum, maximum, origin, direction, cell) {
  let enter = 0, exit = Infinity;
  for (let axis = 0; axis < 3; axis++) {
    if (Math.abs(direction[axis]) < 1e-15) {
      if (origin[axis] < minimum[axis] || origin[axis] > maximum[axis]) return [];
    } else {
      let a = (minimum[axis] - origin[axis]) / direction[axis];
      let b = (maximum[axis] - origin[axis]) / direction[axis];
      if (a > b) [a, b] = [b, a];
      enter = Math.max(enter, a); exit = Math.min(exit, b);
    }
  }
  if (!(exit >= enter)) return [];
  const position = origin.map((v, i) => v + direction[i] * enter);
  const coord = position.map(v => Math.floor(v / cell));
  const step = direction.map(v => Math.sign(v));
  const delta = direction.map(v => v === 0 ? Infinity : cell / Math.abs(v));
  const next = coord.map((v, i) => direction[i] === 0 ? Infinity
    : ((v + (step[i] > 0 ? 1 : 0)) * cell - origin[i]) / direction[i]);
  const candidates = new Set();
  const visit = c => { for (const id of grid.get(c.join(',')) ?? []) candidates.add(id); };
  visit(coord);
  // Include all cells touching the entry point. This is conservative for a ray
  // starting exactly on a face, edge or corner of the grid.
  const boundary = position.map((v, i) => Math.abs(v / cell - Math.round(v / cell)) < 1e-9 ? i : -1).filter(i => i >= 0);
  for (let mask = 1; mask < (1 << boundary.length); mask++) {
    const c = coord.slice();
    for (let i = 0; i < boundary.length; i++) if (mask & (1 << i)) c[boundary[i]]--;
    visit(c);
  }
  const limit = minimum.reduce((sum, v, i) => sum + Math.ceil((maximum[i] - v) / cell) + 2, 4);
  for (let iteration = 0; iteration < limit; iteration++) {
    const time = Math.min(...next);
    if (!Number.isFinite(time) || time > exit + 1e-10) return [...candidates];
    const axes = next.map((v, i) => Math.abs(v - time) < 1e-10 ? i : -1).filter(i => i >= 0);
    // Supercover traversal: all incident cells at simultaneous plane crossings
    // are visited, including the two side cells of an edge/corner crossing.
    for (let mask = 1; mask < (1 << axes.length); mask++) {
      const c = coord.slice();
      for (let i = 0; i < axes.length; i++) if (mask & (1 << i)) c[axes[i]] += step[axes[i]];
      visit(c);
    }
    for (const axis of axes) { coord[axis] += step[axis]; next[axis] += delta[axis]; }
  }
  throw Error('Conservative ray grid traversal exceeded its geometric cell bound');
}
