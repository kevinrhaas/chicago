// SPDX-License-Identifier: GPL-3.0-or-later
/** ENU clearance for the whole declared vehicle/team envelope, not just a root point. */
const inside = (p, poly) => {
  let yes = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) yes = !yes;
  }
  return yes;
};
const cross = (a, b, p) => (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]);
const touches = (a, b, c, d) => {
  if (Math.max(a[0], b[0]) < Math.min(c[0], d[0]) || Math.max(c[0], d[0]) < Math.min(a[0], b[0])
    || Math.max(a[1], b[1]) < Math.min(c[1], d[1]) || Math.max(c[1], d[1]) < Math.min(a[1], b[1])) return false;
  return cross(a, b, c) * cross(a, b, d) <= 0 && cross(c, d, a) * cross(c, d, b) <= 0;
};
const overlap = (a, b) => a.some(p => inside(p, b)) || b.some(p => inside(p, a))
  || a.some((p, i) => b.some((q, j) => touches(p, a[(i + 1) % a.length], q, b[(j + 1) % b.length])));
const boundsOfPoints = points => points.reduce((b, p) => [Math.min(b[0], p[0]), Math.min(b[1], p[1]), Math.max(b[2], p[0]), Math.max(b[3], p[1])], [Infinity, Infinity, -Infinity, -Infinity]);
const boxesOverlap = (a, b) => a[0] <= b[2] && b[0] <= a[2] && a[1] <= b[3] && b[1] <= a[3];

export function transportEnvelope(pose, bounds) {
  const [left, back, right, front] = bounds;
  const c = Math.cos(pose.yaw), s = Math.sin(pose.yaw);
  return [[left, back], [right, back], [right, front], [left, front]].map(([x, z]) =>
    [pose.e + c * x + s * z, pose.n + s * x - c * z]);
}

/** `footprints` is the actual walker list; dynamic fort walls are read every time. */
export function createTransportClearance({ footprints, visitor = () => null,
  envelope_local_xz_m, visitor_radius_m = .35, margin_m = .15 }) {
  if (typeof footprints !== 'function' || typeof visitor !== 'function'
    || !Array.isArray(envelope_local_xz_m) || envelope_local_xz_m.length !== 4
    || !envelope_local_xz_m.every(Number.isFinite)) throw Error('transport clearance: current footprint/visitor readers and measured envelope required');
  const bounds = [...envelope_local_xz_m];
  bounds[0] -= margin_m; bounds[1] -= margin_m; bounds[2] += margin_m; bounds[3] += margin_m;
  if (bounds[0] >= bounds[2] || bounds[1] >= bounds[3] || visitor_radius_m < 0 || margin_m < 0) throw Error('transport clearance: invalid envelope');
  let lastBlocker = null;
  // Walker polygons are immutable readings; versions replace the polygon arrays.
  // The explicit invalidator also supports an editor that mutates vertices in place.
  let polygonBounds = new WeakMap();
  const polygonBox = poly => { let box = polygonBounds.get(poly); if (!box) { box = boundsOfPoints(poly); polygonBounds.set(poly, box); } return box; };
  function clear(from, to) {
    const length = Math.hypot(to.e - from.e, to.n - from.n);
    const turn = Math.atan2(Math.sin(to.yaw - from.yaw), Math.cos(to.yaw - from.yaw));
    const radius = Math.max(...bounds.map(Math.abs));
    const count = Math.max(1, Math.ceil((length + Math.abs(turn) * radius) / .1));
    const current = footprints(), person = visitor();
    if (!Array.isArray(current)) throw Error('transport clearance: actual footprint list missing');
    for (let sample = 0; sample <= count; sample++) {
      const t = sample / count;
      const pose = { e: from.e + (to.e - from.e) * t, n: from.n + (to.n - from.n) * t, yaw: from.yaw + turn * t };
      const box = transportEnvelope(pose, bounds);
      const boxBounds = boundsOfPoints(box);
      for (const fp of current) {
        if (fp.ground) continue;
        if (Array.isArray(fp.walls)) {
          for (const wall of fp.walls) {
            if (wall.blocks && !wall.blocks()) continue;
            const a = wall.a, b = wall.b, thickness = wall.half ?? wall.halfThickness ?? .05;
            if (!a || !b) throw Error(`transport clearance: malformed wall ${fp.id}`);
            const wallBox = [Math.min(a[0], b[0]) - thickness, Math.min(a[1], b[1]) - thickness,
              Math.max(a[0], b[0]) + thickness, Math.max(a[1], b[1]) + thickness];
            if (!boxesOverlap(boxBounds, wallBox)) continue;
            const dx = b[0] - a[0], dy = b[1] - a[1], norm = Math.hypot(dx, dy);
            if (norm <= 0) continue;
            const x = -dy / norm * thickness, y = dx / norm * thickness;
            const polygon = [[a[0] + x, a[1] + y], [b[0] + x, b[1] + y], [b[0] - x, b[1] - y], [a[0] - x, a[1] - y]];
            if (overlap(box, polygon)) { lastBlocker = fp.id; return false; }
          }
        } else if (fp.pts && boxesOverlap(boxBounds, polygonBox(fp.pts)) && overlap(box, fp.pts)) { lastBlocker = fp.id; return false; }
      }
      if (person && !person.flying) {
        const de = person.e - pose.e, dn = person.n - pose.n;
        const x = Math.cos(pose.yaw) * de + Math.sin(pose.yaw) * dn;
        const z = Math.sin(pose.yaw) * de - Math.cos(pose.yaw) * dn;
        const dx = Math.max(bounds[0] - x, 0, x - bounds[2]);
        const dz = Math.max(bounds[1] - z, 0, z - bounds[3]);
        if (Math.hypot(dx, dz) <= visitor_radius_m) { lastBlocker = 'visitor'; return false; }
      }
    }
    lastBlocker = null; return true;
  }
  Object.defineProperty(clear, 'lastBlocker', { get: () => lastBlocker });
  clear.invalidate = () => { polygonBounds = new WeakMap(); };
  return clear;
}
