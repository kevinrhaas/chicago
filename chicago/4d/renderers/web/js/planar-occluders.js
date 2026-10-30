/** T-3152: the cells of a flat surface it is PROVEN to cover, for the T-2227 view filter.
 *
 * T-2227 hides a piece only when its whole box projects inside ONE backing triangle.
 * Glessner's walls are rock-faced granite over a flat mortar backing, and the backing is
 * cut into thousands of slivers round its openings, so from its own 18th Street stand the
 * court, south and east walls behind the north and west fronts were drawn whole although
 * nothing of them can be seen. This finds each large plane of one source mesh and the
 * cells of a fine grid on it that the plane's own triangles cover with no gap;
 * view-occlusion.js `planeOccluded` then casts a piece's box from the eye onto the plane
 * and hides it only when every cell under that shadow is one of them.
 *
 * The cover is proved, not sampled: see planarCoverPlanes and boundarySegments. A
 * spurious outline (an unmatched seam) can only refuse a cell, never admit one, and a
 * triangle more than `tol` off its plane is left out of it, which also only refuses.
 */

/**
 * The outline of a union of triangles in one plane, as segments: every stretch of a
 * triangle edge that has a triangle beside it on ONE side only. Edges are swept line by
 * line, so a seam where one panel's long edge meets a row of the next panel's vertices (a
 * T-junction) is interior wherever both sides are covered, and an outline wherever one is
 * not. A half-edge further than `seam` off its line's reference edge is its own line and so
 * an outline: a gap can only be kept, never closed, beyond that width. Below it a T-junction
 * vertex is taken as on the line — the assets' int16 positions put such vertices up to about
 * 1 mm off it in the drawn mesh already, so `seam` is the one tolerance this proof spends.
 * @param {number[][][]} halves  [a, b, c] per triangle edge ab, c its third corner (2-D)
 */
export function boundarySegments(halves, seam = 0.002) {
  const lines = new Map();
  for (const [a, b, c] of halves) {
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const len = Math.hypot(dx, dy);
    if (!(len > 1e-9)) continue;
    dx /= len; dy /= len;
    if (dx < -1e-12 || (Math.abs(dx) <= 1e-12 && dy < 0)) { dx = -dx; dy = -dy; }
    const off = dx * a[1] - dy * a[0];
    const k = `${Math.round(dx * 2000)},${Math.round(dy * 2000)},${Math.round(off * 200)}`;
    let g = lines.get(k);
    if (!g) { g = []; lines.set(k, g); }
    g.push({ a, b, c, len });
  }
  const out = [];
  for (const g of lines.values()) {
    // The longest edge is the line; anything off it by more than `seam` stands alone.
    let ref = g[0];
    for (const h of g) if (h.len > ref.len) ref = h;
    let dx = (ref.b[0] - ref.a[0]) / ref.len, dy = (ref.b[1] - ref.a[1]) / ref.len;
    if (dx < -1e-12 || (Math.abs(dx) <= 1e-12 && dy < 0)) { dx = -dx; dy = -dy; }
    const ox = ref.a[0], oy = ref.a[1];
    const offOf = (p) => dx * (p[1] - oy) - dy * (p[0] - ox);
    const events = [];
    for (const h of g) {
      if (Math.abs(offOf(h.a)) > seam || Math.abs(offOf(h.b)) > seam) { out.push([h.a, h.b]); continue; }
      const side = offOf(h.c) > 0 ? 0 : 1;
      if (Math.abs(offOf(h.c)) <= seam) { out.push([h.a, h.b]); continue; }
      let t0 = dx * (h.a[0] - ox) + dy * (h.a[1] - oy), t1 = dx * (h.b[0] - ox) + dy * (h.b[1] - oy);
      if (t0 > t1) [t0, t1] = [t1, t0];
      events.push([t0, side, 1], [t1, side, -1]);
    }
    // Every event at one parameter is applied before the state is read: at a T-junction
    // vertex one edge on a side ends exactly where the next begins, and nothing between.
    events.sort((p, q) => p[0] - q[0]);
    const cover = [0, 0];
    let start = null;
    for (let e = 0; e < events.length;) {
      const t = events[e][0];
      for (; e < events.length && events[e][0] === t; e++) cover[events[e][1]] += events[e][2];
      const oneSided = (cover[0] > 0) !== (cover[1] > 0);
      if (oneSided && start === null) start = t;
      if (!oneSided && start !== null) {
        out.push([[ox + dx * start, oy + dy * start], [ox + dx * t, oy + dy * t]]);
        start = null;
      }
    }
  }
  return out.map(([a, b]) => ({ a, b }));
}

function cross(ax, ay, az, bx, by, bz) {
  return [ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx];
}

/** Does the closed segment ab meet the closed axis-aligned rectangle [x0,x1]x[y0,y1]? */
export function segmentMeetsRect(ax, ay, bx, by, x0, y0, x1, y1) {
  if (Math.max(ax, bx) < x0 || Math.min(ax, bx) > x1 || Math.max(ay, by) < y0 || Math.min(ay, by) > y1) return false;
  if ((ax >= x0 && ax <= x1 && ay >= y0 && ay <= y1) || (bx >= x0 && bx <= x1 && by >= y0 && by <= y1)) return true;
  // Liang-Barsky clip: any parameter interval left means they meet.
  let t0 = 0, t1 = 1;
  const dx = bx - ax, dy = by - ay;
  for (const [p, q] of [[-dx, ax - x0], [dx, x1 - ax], [-dy, ay - y0], [dy, y1 - ay]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const r = q / p;
    if (p < 0) { if (r > t1) return false; if (r > t0) t0 = r; }
    else { if (r < t0) return false; if (r < t1) t1 = r; }
  }
  return t0 <= t1;
}

function inTriangle(t, x, y) {
  let pos = false, neg = false;
  for (let k = 0; k < 3; k++) {
    const a = t[k], b = t[(k + 1) % 3];
    const c = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]);
    if (c > 0) pos = true; else if (c < 0) neg = true;
  }
  return !(pos && neg);
}

/**
 * Every large plane of one mesh, with the cells of a `res` grid on it that its own
 * triangles are proven to cover. A cell is kept only when its centre lies in a triangle of
 * the plane and no outline segment (boundarySegments) meets the cell grown by `inset`: a
 * connected square that one covered point and no outline touches lies inside the union.
 * @param {ArrayLike<number>} position  xyz triples, the frame the planes come back in
 * @param {ArrayLike<number>|null} index
 * @returns {{normal:number[], d:number, u:number[], v:number[], umin:number, vmin:number,
 *   res:number, W:number, H:number, sat:Int32Array, cells:number, tol:number}[]}
 *   `sat` is the covered cells' summed-area table, (W+1) x (H+1), so a caller asks whether
 *   a whole range of cells is covered in four reads.
 */
export function planarCoverPlanes(position, index, {
  minPlaneArea = 16, tol = 0.005, res = 0.1, inset = 0.02, seam = 0.002, minCells = 400,
} = {}) {
  const count = index ? index.length : position.length / 3;
  const vtx = (i) => (index ? index[i] : i) * 3;
  // The plane of triangle i, as one number (not a string: this runs over every
  // triangle of a 1.4 M-triangle house), with its doubled area and summed normal in
  // scratch. One orientation per plane: a backing and its reverse are one surface.
  const sn = [0, 0, 0];
  let len = 0;
  const keyOf = (i) => {
    const a = vtx(i), b = vtx(i + 1), c = vtx(i + 2), p = position;
    const ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2];
    const wx = p[c] - p[a], wy = p[c + 1] - p[a + 1], wz = p[c + 2] - p[a + 2];
    let x = uy * wz - uz * wy, y = uz * wx - ux * wz, z = ux * wy - uy * wx;
    len = Math.hypot(x, y, z);
    if (!(len > 1e-9)) return null;
    const s = (Math.abs(x) > 1e-6 * len ? x : Math.abs(y) > 1e-6 * len ? y : z) < 0 ? -1 : 1;
    x *= s; y *= s; z *= s;
    sn[0] = x; sn[1] = y; sn[2] = z;
    const d = (x * p[a] + y * p[a + 1] + z * p[a + 2]) / len;
    return ((Math.round(x / len * 500) + 500) * 1001 + Math.round(y / len * 500) + 500) * 1001
      + Math.round(z / len * 500) + 500 + 1003003 * 1001 * (Math.round(d / tol) + 4e6);
  };
  // Only a plane holding a triangle of 0.25 m2 is a candidate: a large flat backing always
  // has some, and the granite's relief and the brick have almost none, so the full pass
  // below gathers triangles for a handful of planes rather than one per relief facet.
  const planes = new Map();
  for (let i = 0; i < count; i += 3) {
    const k = keyOf(i);
    if (k !== null && len >= 0.5 && !planes.has(k)) planes.set(k, { area: 0, n: [0, 0, 0], tris: [] });
  }
  if (!planes.size) return [];
  for (let i = 0; i < count; i += 3) {
    const k = keyOf(i);
    const e = k === null ? undefined : planes.get(k);
    if (!e) continue;
    e.area += len / 2; e.n[0] += sn[0]; e.n[1] += sn[1]; e.n[2] += sn[2]; e.tris.push(i);
  }
  const out = [];
  for (const plane of planes.values()) {
    if (plane.area < minPlaneArea) continue;
    const nl = Math.hypot(...plane.n), n = plane.n.map((x) => x / nl);
    // The plane through the area-weighted mean; every vertex of a kept triangle within tol.
    let dSum = 0, w = 0;
    for (const i of plane.tris) for (let k = 0; k < 3; k++) {
      const v = vtx(i + k); dSum += n[0] * position[v] + n[1] * position[v + 1] + n[2] * position[v + 2]; w++;
    }
    const d = dSum / w;
    const ref = Math.abs(n[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    let u = cross(ref[0], ref[1], ref[2], n[0], n[1], n[2]);
    const ul = Math.hypot(...u); u = u.map((x) => x / ul);
    const v2 = cross(n[0], n[1], n[2], u[0], u[1], u[2]);
    const to2 = (vi) => [
      u[0] * position[vi] + u[1] * position[vi + 1] + u[2] * position[vi + 2],
      v2[0] * position[vi] + v2[1] * position[vi + 1] + v2[2] * position[vi + 2]];
    const tris = [], halves = [];
    for (const i of plane.tris) {
      const vs = [vtx(i), vtx(i + 1), vtx(i + 2)];
      if (vs.some((vi) => Math.abs(n[0] * position[vi] + n[1] * position[vi + 1] + n[2] * position[vi + 2] - d) > tol)) continue;
      const t = vs.map(to2);
      tris.push(t);
      for (let k = 0; k < 3; k++) halves.push([t[k], t[(k + 1) % 3], t[(k + 2) % 3]]);
    }
    const boundary = boundarySegments(halves, seam);
    if (!tris.length) continue;
    let umin = Infinity, umax = -Infinity, vmin = Infinity, vmax = -Infinity;
    for (const t of tris) for (const q of t) {
      umin = Math.min(umin, q[0]); umax = Math.max(umax, q[0]); vmin = Math.min(vmin, q[1]); vmax = Math.max(vmax, q[1]);
    }
    const W = Math.ceil((umax - umin) / res) + 1, H = Math.ceil((vmax - vmin) / res) + 1;
    if (W * H > 4e6) continue;
    // Proposals: a cell is open when its centre is in a triangle and no boundary edge
    // crosses the cell (grown by the inset). Only the exact check below admits anything.
    const mask = new Uint8Array(W * H);
    for (const t of tris) {
      const x0 = Math.floor((Math.min(t[0][0], t[1][0], t[2][0]) - umin) / res), x1 = Math.ceil((Math.max(t[0][0], t[1][0], t[2][0]) - umin) / res);
      const y0 = Math.floor((Math.min(t[0][1], t[1][1], t[2][1]) - vmin) / res), y1 = Math.ceil((Math.max(t[0][1], t[1][1], t[2][1]) - vmin) / res);
      for (let gy = Math.max(0, y0); gy <= Math.min(H - 1, y1); gy++) for (let gx = Math.max(0, x0); gx <= Math.min(W - 1, x1); gx++) {
        if (!mask[gy * W + gx] && inTriangle(t, umin + (gx + 0.5) * res, vmin + (gy + 0.5) * res)) mask[gy * W + gx] = 1;
      }
    }
    for (const e of boundary) {
      const x0 = Math.floor((Math.min(e.a[0], e.b[0]) - inset - umin) / res), x1 = Math.floor((Math.max(e.a[0], e.b[0]) + inset - umin) / res);
      const y0 = Math.floor((Math.min(e.a[1], e.b[1]) - inset - vmin) / res), y1 = Math.floor((Math.max(e.a[1], e.b[1]) + inset - vmin) / res);
      for (let gy = Math.max(0, y0); gy <= Math.min(H - 1, y1); gy++) for (let gx = Math.max(0, x0); gx <= Math.min(W - 1, x1); gx++) {
        const cx0 = umin + gx * res - inset, cy0 = vmin + gy * res - inset;
        if (segmentMeetsRect(e.a[0], e.a[1], e.b[0], e.b[1], cx0, cy0, cx0 + res + 2 * inset, cy0 + res + 2 * inset)) mask[gy * W + gx] = 0;
      }
    }
    const sat = new Int32Array((W + 1) * (H + 1));
    let cells = 0;
    for (let gy = 0; gy < H; gy++) {
      let row = 0;
      for (let gx = 0; gx < W; gx++) {
        row += mask[gy * W + gx];
        sat[(gy + 1) * (W + 1) + gx + 1] = sat[gy * (W + 1) + gx + 1] + row;
      }
      cells += row;
    }
    if (cells < minCells) continue;
    out.push({ normal: n, d, u, v: v2, umin, vmin, res, W, H, sat, cells, tol });
  }
  return out;
}
