// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3497: the ground a wagon and its team stand on in a scene of natural ground (1812).
 *
 * The heightfield is stored to the nearest 5 mm (int16 x .005) on a 2.5 m lattice and drawn
 * bilinear, so on the flattest sand plain its facets still fold by a few millimetres from
 * one cell to the next — more than the 2 mm a horse's planted hooves are allowed to rock
 * (transport-support.js). Paved 1904 streets never showed it; the 1812 plain does at every
 * few metres. This reads the same lattice through a uniform cubic B-spline: C2-smooth, so a
 * hoof box or a wheel base sees a plane, and within millimetres of the drawn facets on level
 * ground (the spline averages each node with its neighbours 1:4:1). It is a reading of the
 * committed field, not a new surface: nothing is drawn from it, and the rendered ground is
 * unchanged. On the trails the ground is drawn 2.2-2.6 cm higher still (yards.js drape), so
 * the wheels and hooves bed a little into the beaten earth, as they would.
 */
const B = t => {
  const t2 = t * t, t3 = t2 * t;
  return [(1 - t) ** 3 / 6, (3 * t3 - 6 * t2 + 4) / 6, (-3 * t3 + 3 * t2 + 3 * t + 1) / 6, t3 / 6];
};

/** `sample(e, n)` is the drawn ground at a lattice node; `grid` its { cellM, originE, originN }. */
export function createSmoothedGround({ sample, grid }) {
  if (typeof sample !== 'function' || !grid || ![grid.cellM, grid.originE, grid.originN].every(Number.isFinite) || grid.cellM <= 0) {
    throw Error('transport ground: a ground sampler and its lattice are required');
  }
  const { cellM, originE, originN } = grid;
  const nodes = new Map();
  const node = (i, j) => {
    const key = i * 1e6 + j;
    let h = nodes.get(key);
    if (h === undefined) {
      h = sample(originE + i * cellM, originN + j * cellM);
      if (nodes.size > 200000) nodes.clear();
      nodes.set(key, h);
    }
    return h;
  };
  return function smoothedHeight(e, n) {
    const gx = (e - originE) / cellM, gy = (n - originN) / cellM;
    if (!Number.isFinite(gx) || !Number.isFinite(gy)) return NaN;
    const i0 = Math.floor(gx), j0 = Math.floor(gy);
    const wx = B(gx - i0), wy = B(gy - j0);
    let h = 0;
    for (let b = 0; b < 4; b++) {
      let row = 0;
      for (let a = 0; a < 4; a++) row += wx[a] * node(i0 - 1 + a, j0 - 1 + b);
      h += wy[b] * row;
    }
    return h;
  };
}
