// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * rider_drawn.mjs — a seated rider drawn, cloth panels and all, to see what shows (T-3644).
 *
 * Kevin, 2026-11-19 (1904, aside in the riding habit): "you can see her leg through the riding
 * habit". test_riding had held every point of her legs under the habit's sheet, and they were:
 * but the skirt is drawn with only so many vertices, and between two of them a flat panel cuts
 * across the sheet's bends, over a knee. Points cannot see that; a drawing can. This draws the
 * triangles (posed as the shaders pose them, laid by the caller) into a small depth buffer from a
 * few sides, flat, and counts the pixels of each kind that are nearest the eye: her bare legs
 * among them must be (almost) none.
 *
 *   drawnCounts(tris, { centre, views, size, scale })
 *     tris    [[a, b, c, kind]] (THREE.Vector3 corners in one frame, y up; kind a string)
 *     centre  the point the views look at; views [[name, azimuth°, elevation°]] (azimuth from
 *             +z toward +x); size the square image in pixels; scale pixels a metre.
 *   Returns { name: { kind: pixels } }.
 */
export function drawnCounts(tris, { centre, views, size = 260, scale = 300 }) {
  const out = {};
  const zb = new Float32Array(size * size), who = new Array(size * size);
  for (const [name, az, el] of views) {
    const a = az * Math.PI / 180, e = el * Math.PI / 180;
    const d = [Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e)];      // toward the eye
    const rl = Math.hypot(d[2], d[0]) || 1, rgt = [d[2] / rl, 0, -d[0] / rl];              // up x d
    const upv = [d[1] * rgt[2] - d[2] * rgt[1], d[2] * rgt[0] - d[0] * rgt[2], d[0] * rgt[1] - d[1] * rgt[0]];
    zb.fill(-Infinity); who.fill(undefined);
    const P = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    for (const [A, B, C, kind] of tris) {
      [A, B, C].forEach((p, i) => {
        const x = p.x - centre.x, y = p.y - centre.y, z = p.z - centre.z;
        P[i][0] = size / 2 + scale * (x * rgt[0] + y * rgt[1] + z * rgt[2]);
        P[i][1] = size / 2 - scale * (x * upv[0] + y * upv[1] + z * upv[2]);
        P[i][2] = x * d[0] + y * d[1] + z * d[2];
      });
      const den = (P[1][1] - P[2][1]) * (P[0][0] - P[2][0]) + (P[2][0] - P[1][0]) * (P[0][1] - P[2][1]);
      if (Math.abs(den) < 1e-12) continue;
      const x0 = Math.max(0, Math.floor(Math.min(P[0][0], P[1][0], P[2][0]))), x1 = Math.min(size - 1, Math.ceil(Math.max(P[0][0], P[1][0], P[2][0])));
      const y0 = Math.max(0, Math.floor(Math.min(P[0][1], P[1][1], P[2][1]))), y1 = Math.min(size - 1, Math.ceil(Math.max(P[0][1], P[1][1], P[2][1])));
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
        const l0 = ((P[1][1] - P[2][1]) * (x - P[2][0]) + (P[2][0] - P[1][0]) * (y - P[2][1])) / den;
        const l1 = ((P[2][1] - P[0][1]) * (x - P[2][0]) + (P[0][0] - P[2][0]) * (y - P[2][1])) / den, l2 = 1 - l0 - l1;
        if (l0 < 0 || l1 < 0 || l2 < 0) continue;
        const z = l0 * P[0][2] + l1 * P[1][2] + l2 * P[2][2], k = y * size + x;
        if (z > zb[k]) { zb[k] = z; who[k] = kind; }
      }
    }
    const n = {};
    for (const kind of who) if (kind) n[kind] = (n[kind] ?? 0) + 1;
    out[name] = n;
  }
  return out;
}
