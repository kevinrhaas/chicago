/**
 * fire-mass.js — T-3802: where a named structure's flames may stand.
 *
 * The owner, 2026-11-27, at the Great Fire's Court House stop: "the fires sometimes appear
 * above the building". city-fire.js had read a named structure as the bounding box of all its
 * pieces. A piece is one material's mesh, so the Lockport stone piece of the Court House runs
 * from the 1853 house's walls to the top of its cupola: every cell of the house read 57 m tall,
 * the roof flames stood at 0.8 of the cupola's height, far over the wings, and the flames were
 * spread over the whole box, in the air beside a building that is a centre block and two wings.
 *
 * So a named structure is read as its MASS: a coarse plan of cells, each with the height of
 * its wall head and of its roof. Where the structure's record carries its composition (the
 * blocks and towers landmark_1871 builds it from: each block's plan box, storeys and roof, each
 * tower's stages), the mass is those parts, so a flame stands on the roof of the block it is
 * over and at a window no higher than that block's wall. Where it does not (a structure built
 * another way), the pieces' boxes are the fallback, read through a 3 x 3 median so one tall
 * thin piece does not lift its neighbours. Pure arithmetic (no three.js), so the gate tests it.
 *
 * World metres throughout: x east, y up, z = -north.
 */

/** Cells under this height above the foot are ground (steps, plinths, kerbs, low walls), not building. */
export const GROUND_M = 2.5;
const MAX_CELLS = 40000;

function inPoly(poly, x, z) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, zi] = poly[i], [xj, zj] = poly[j];
    if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
}

/**
 * The mass of a structure from prisms ({ poly: [[x, z], ...], wall, top } in world metres,
 * `wall` the wall head and `top` the roof over it): { cell, x0, z0, nx, nz, wall, top, base,
 * cells, eave, area }. `smooth` takes each cell's heights as the median of its building
 * neighbours (the boxes fallback).
 */
export function massOf(prisms, base, { smooth = false } = {}) {
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  for (const p of prisms) for (const [x, z] of p.poly) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); }
  if (!Number.isFinite(x0)) return null;
  let cell = 1.5;
  while (Math.ceil((x1 - x0) / cell) * Math.ceil((z1 - z0) / cell) > MAX_CELLS) cell *= 1.5;
  const nx = Math.max(1, Math.ceil((x1 - x0) / cell)), nz = Math.max(1, Math.ceil((z1 - z0) / cell));
  let wall = new Float32Array(nx * nz).fill(-Infinity), top = new Float32Array(nx * nz).fill(-Infinity);
  const raise = (j, p) => { if (p.wall > wall[j]) wall[j] = p.wall; if (p.top > top[j]) top[j] = p.top; };
  for (const p of prisms) {
    let px0 = Infinity, px1 = -Infinity, pz0 = Infinity, pz1 = -Infinity;
    for (const [x, z] of p.poly) { px0 = Math.min(px0, x); px1 = Math.max(px1, x); pz0 = Math.min(pz0, z); pz1 = Math.max(pz1, z); }
    const i0 = Math.max(0, Math.floor((px0 - x0) / cell)), i1 = Math.min(nx - 1, Math.floor((px1 - x0) / cell));
    const k0 = Math.max(0, Math.floor((pz0 - z0) / cell)), k1 = Math.min(nz - 1, Math.floor((pz1 - z0) / cell));
    let hit = false;
    for (let k = k0; k <= k1; k++) for (let i = i0; i <= i1; i++) {
      if (inPoly(p.poly, x0 + (i + 0.5) * cell, z0 + (k + 0.5) * cell)) { raise(k * nx + i, p); hit = true; }
    }
    // A part narrower than a cell still stands in the cell under its middle.
    if (!hit) {
      const i = Math.min(nx - 1, Math.max(0, Math.floor(((px0 + px1) / 2 - x0) / cell)));
      const k = Math.min(nz - 1, Math.max(0, Math.floor(((pz0 + pz1) / 2 - z0) / cell)));
      raise(k * nx + i, p);
    }
  }
  const building = (j) => top[j] - base > GROUND_M;
  if (smooth) {
    const med = (arr) => {
      const out = new Float32Array(arr.length).fill(-Infinity);
      for (let k = 0; k < nz; k++) for (let i = 0; i < nx; i++) {
        const j = k * nx + i;
        if (!building(j)) continue;
        const v = [];
        for (let dk = -1; dk <= 1; dk++) for (let di = -1; di <= 1; di++) {
          const ii = i + di, kk = k + dk;
          if (ii >= 0 && kk >= 0 && ii < nx && kk < nz && building(kk * nx + ii)) v.push(arr[kk * nx + ii]);
        }
        v.sort((a, b) => a - b);
        out[j] = v[Math.floor((v.length - 1) / 2)];
      }
      return out;
    };
    const t2 = med(top), w2 = med(wall);
    top = t2; wall = w2;
  }
  const cells = [];
  for (let j = 0; j < top.length; j++) if (top[j] - base > GROUND_M) cells.push(j);
  if (!cells.length) return null;
  const heights = cells.map((j) => wall[j] - base).sort((a, b) => a - b);
  // The main wall head: the height most of the plan stands at, not a tower's.
  const eave = heights[Math.floor(heights.length * 0.5)];
  return { cell, x0, z0, nx, nz, wall, top, base, cells, eave, area: cells.length * cell * cell };
}

/** The pieces' boxes ({ minX, maxX, minY, maxY, minZ, maxZ }) as prisms. */
export function boxPrisms(boxes) {
  return boxes.map((b) => ({ poly: [[b.minX, b.minZ], [b.maxX, b.minZ], [b.maxX, b.maxZ], [b.minX, b.maxZ]], wall: b.maxY, top: b.maxY }));
}

/**
 * A structure record's composition (attributes.composition.value: blocks and towers, in its
 * footprint's own metres) as world prisms over the ground at `groundY`. Null if it has none.
 */
export function compositionPrisms(sidecar, groundY) {
  const comp = sidecar?.attributes?.composition?.value, pl = sidecar?.placement;
  if (!comp || !pl || !Array.isArray(comp.blocks)) return null;
  const th = (pl.rotation_deg ?? 0) * Math.PI / 180, c = Math.cos(th), s = Math.sin(th);
  const at = (u, v) => { const e = (pl.local_e ?? 0) + u * c + v * s, n = (pl.local_n ?? 0) - u * s + v * c; return [e, -n]; };
  const out = [];
  for (const b of comp.blocks) {
    const [u0, v0, u1, v1] = b.box ?? [];
    if (![u0, v0, u1, v1].every(Number.isFinite)) continue;
    const head = (b.z0 ?? 0) + (b.storeys ?? []).reduce((a, h) => a + (Number(h) || 0), 0);
    const r = b.roof ?? {}, rise = r.kind && r.kind !== 'flat' ? Number(r.h) || 0 : 0.6;
    out.push({ poly: [at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1)], wall: groundY + head, top: groundY + head + rise * 0.5 });
  }
  for (const t of comp.towers ?? []) {
    const [u, v] = t.at ?? [];
    if (!Number.isFinite(u) || !Number.isFinite(v)) continue;
    let z = t.z0 ?? 0;
    for (const st of t.stages ?? []) {
      const w = Number(st.w) || 0, h = Number(st.h) || 0, hw = w / 2;
      if (w > 0 && h > 0) out.push({ poly: [at(u - hw, v - hw), at(u + hw, v - hw), at(u + hw, v + hw), at(u - hw, v + hw)], wall: groundY + z + h, top: groundY + z + h });
      z += h;
    }
  }
  return out.length ? out : null;
}

const isBuilding = (m, i, k) => i >= 0 && k >= 0 && i < m.nx && k < m.nz && m.top[k * m.nx + i] - m.base > GROUND_M;

/**
 * The emitters of a massed structure, in city-fire.js's shape: roof flames on cells' roofs,
 * window flames on the outer faces of wall cells, storey by storey up to each wall's head.
 * `r()` is the structure's seeded stream; `spacing` the detail level's window spacing.
 */
export function massEmitters(m, r, { spacing = 1, storeyM = 4 } = {}) {
  const C = m.cell, wins = [], roof = [];
  const S = Math.max(1, Math.round(m.eave / storeyM)), sh = m.eave / S;
  const centre = (j) => [m.x0 + ((j % m.nx) + 0.5) * C, m.z0 + (Math.floor(j / m.nx) + 0.5) * C];
  // Wall cells, their outward faces, every so many metres along the wall.
  const every = Math.max(1, Math.round(4.2 * spacing / C));
  const faces = [];
  for (const j of m.cells) {
    const i = j % m.nx, k = Math.floor(j / m.nx);
    for (const [di, dk] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      if (isBuilding(m, i + di, k + dk)) continue;
      if (((di ? k : i) % every) !== 0) continue;
      faces.push({ j, di, dk });
    }
  }
  for (const f of faces) {
    const [x, z] = centre(f.j), head = m.wall[f.j];
    for (let s = 0; ; s++) {
      const y = m.base + sh * (s + 0.25);
      if (y + 0.5 * sh > head) break;
      const hh = sh * (0.95 + 0.5 * r());
      wins.push({ x: x + f.di * (C / 2 + 0.3), z: z + f.dk * (C / 2 + 0.3), y, w: 2.1 + 0.9 * r(), h: Math.min(hh, head - y + 1), lag: 0.15 * s + 0.6 * r(), seed: r() * 100, roof: false });
    }
  }
  const nR = Math.max(1, Math.min(6, Math.round(m.area / 55)));
  for (let n = 0; n < nR; n++) {
    const j = m.cells[Math.floor(r() * m.cells.length)];
    const [x, z] = centre(j);
    roof.push({ x: x + (r() - 0.5) * C * 0.6, z: z + (r() - 0.5) * C * 0.6, y: m.top[j] - 0.3, w: Math.max(2.5, Math.min(14, Math.sqrt(m.area / nR) * 0.55)), h: Math.min(m.wall[j] - m.base, m.eave) * 0.55 + 3, lag: 0.25 + 0.6 * r(), seed: r() * 100, roof: true });
  }
  return { roof, wins, storeys: S };
}

/**
 * How far an emitter stands clear of a mass: metres in plan from the nearest building cell's
 * edge, and metres its foot stands over the highest roof within 1.5 m of it. Both ~0 when the
 * flame stands on the building.
 */
export function clearOf(e, m) {
  let plan = Infinity, over = Infinity;
  const C = m.cell;
  for (const j of m.cells) {
    const cx = m.x0 + ((j % m.nx) + 0.5) * C, cz = m.z0 + (Math.floor(j / m.nx) + 0.5) * C;
    const d = Math.hypot(Math.max(0, Math.abs(e.x - cx) - C / 2), Math.max(0, Math.abs(e.z - cz) - C / 2));
    if (d < plan) plan = d;
    if (d <= 1.5) over = Math.min(over, Math.max(0, e.y - m.top[j]));
  }
  return { plan, over: Number.isFinite(over) ? over : Infinity };
}
