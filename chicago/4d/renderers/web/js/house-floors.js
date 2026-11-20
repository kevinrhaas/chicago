/**
 * house-floors.js — the stoops and porches a 1904 Prairie Avenue house builds outside its walls,
 * as floors the visitor climbs.
 *
 * The owner, 2026-11-14: *"I cants walk ups stairs to the door outside a house to interact and
 * see who is home ask them to come out"* and *"Anywhere there are stairs I should be able to
 * climb"*. The visitor's walk (walker.js) stands on the terrain and on decks; a house's stoop is
 * neither, so the ground ran on under its treads and the steps could not be climbed to the door.
 *
 * tools/prairie_barriers.py `floor` reads each house model for the tops one stands on outside
 * its walls (a stoop's treads and landing, a porch, a terrace, the doorway's reveal), reached
 * from the ground a step at a time, and the walls beside them (rails, cheek walls, piers, a top
 * too high or too narrow to stand on); tools/derive_doors_scene.py writes them into
 * data/humans/doors_1904.json as a `floor` per house: rectangles of 0.1 m cells of one height,
 * five integers each (i0 i1 j0 j1 half-open, then the top in centimetres over the model's ground),
 * `rects` the floor and `walls` the walls, on the model's plan (u = x, v = -z).
 *
 * floorDecks(rows, matrixOf) lays each as two walker decks over the house's drawn placement
 * (`matrixOf(id)`: the building's 4x4 matrix, column-major, as buildings.js draws it): the floor,
 * whose treads the walker's step rule climbs one at a time (and its step ease smooths), and the
 * walls, a metre over the floor beside them, which it turns back from as from any wall. A deck's
 * `heightAt(e, n)` answers from the grid, null where neither covers the point (the ground's).
 * The walls deck is marked `wall`: people (deck-surface.js) are never stood on it.
 *
 * Plain math, no renderer dependency; tools/test_house_floors.mjs runs it in node.
 */

function grid(f) {
  if (!f || !Number.isFinite(f.cell) || !Number.isInteger(f.ni) || !Number.isInteger(f.nj) || f.ni < 1 || f.nj < 1) return null;
  const read = (s) => {
    const k = typeof s === 'string' && s.trim() ? s.trim().split(/\s+/).map(Number) : [];
    return k.length % 5 || k.some((x) => !Number.isInteger(x)) ? null : k;
  };
  const floor = read(f.rects), walls = read(f.walls ?? '');
  if (!floor || !walls || !floor.length) return null;
  const fill = (k) => {
    const h = new Float32Array(f.ni * f.nj).fill(NaN);
    for (let r = 0; r < k.length; r += 5) {
      const [i0, i1, j0, j1, cm] = k.slice(r, r + 5);
      for (let i = Math.max(0, i0); i < Math.min(f.ni, i1); i++) {
        for (let j = Math.max(0, j0); j < Math.min(f.nj, j1); j++) h[i * f.nj + j] = cm / 100;
      }
    }
    return h;
  };
  return { floor: fill(floor), walls: walls.length ? fill(walls) : null };
}

/** The affine inverse of a column-major 4x4 (rotation, scale and translation; no projection). */
function invert(m) {
  const [a, b, c, , d, e, f, , g, h, i] = m;
  const det = a * (e * i - f * h) - d * (b * i - c * h) + g * (b * f - c * e);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-12) return null;
  const r = [
    (e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det,
    (f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det,
    (d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det,
  ];
  const [tx, ty, tz] = [m[12], m[13], m[14]];
  return { r, t: [-(r[0] * tx + r[3] * ty + r[6] * tz), -(r[1] * tx + r[4] * ty + r[7] * tz), -(r[2] * tx + r[5] * ty + r[8] * tz)] };
}

/** One house's floor as walker decks ({ id, y, pts, heightAt, wall? }), or []. */
export function houseFloorDecks(row, m) {
  const f = row?.floor;
  const g = grid(f);
  if (!g || !m || m.length !== 16) return [];
  const inv = invert(m);
  if (!inv) return [];
  const c = f.cell;
  const world = (u, y, v) => ({ e: m[0] * u + m[4] * y + m[8] * -v + m[12], y: m[1] * u + m[5] * y + m[9] * -v + m[13],
    n: -(m[2] * u + m[6] * y + m[10] * -v + m[14]) });
  // The plan rectangle the grid covers, its corners in local E/N.
  const ua = f.u0 - c / 2, ub = f.u0 + (f.ni - 0.5) * c, va = f.v0 - c / 2, vb = f.v0 + (f.nj - 0.5) * c;
  const pts = [[ua, va], [ub, va], [ub, vb], [ua, vb]].map(([u, v]) => { const w = world(u, 0, v); return [w.e, w.n]; });
  const base = world(f.u0, 0, f.v0).y;
  const lift = m[5];
  const cellOf = (e, n) => {
    // local E/N (world x = e, z = -n) back to the model's plan, at the ground's height
    const x = e, y = base, z = -n;
    const u = inv.r[0] * x + inv.r[3] * y + inv.r[6] * z + inv.t[0];
    const v = -(inv.r[2] * x + inv.r[5] * y + inv.r[8] * z + inv.t[2]);
    const i = Math.round((u - f.u0) / c), j = Math.round((v - f.v0) / c);
    return i < 0 || j < 0 || i >= f.ni || j >= f.nj ? -1 : i * f.nj + j;
  };
  const deck = (h, id, wall) => {
    let lo = Infinity;
    for (const y of h) if (y < lo) lo = y;
    const at = (e, n) => {
      const k = cellOf(e, n);
      const y = k < 0 ? NaN : h[k];
      return Number.isNaN(y) ? null : base + y * lift;
    };
    return { id, y: base + lo * lift, pts, heightAt: at, ...(wall ? { wall: true } : {}) };
  };
  const out = [deck(g.floor, `${row.structure}:floor`, false)];
  if (g.walls) out.push(deck(g.walls, `${row.structure}:floor-walls`, true));
  return out;
}

/** Every row's floor (doors_1904.json `structures` and `barriers`) as walker decks, for the
 *  houses drawn (`matrixOf(id)` -> column-major 4x4, or null for one not drawn). */
export function floorDecks(rows, matrixOf) {
  const out = [];
  for (const row of rows ?? []) {
    if (!row?.floor) continue;
    const m = matrixOf(row.structure);
    out.push(...houseFloorDecks(row, m ? Array.from(m) : null));
  }
  return out;
}

function insidePts(e, n, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [x, y] = pts[i], [a, b] = pts[j];
    if ((y > n) !== (b > n) && e < (a - x) * (n - y) / (b - y) + x) hit = !hit;
  }
  return hit;
}

/**
 * Many small decks (every house's floor, every back stoop's treads) as one, filed on a grid of
 * `cell` metres, so the walker and every drawn person's feet ask a few of them rather than all
 * (deck-surface.js walks every deck it is given). The highest that covers a point answers, by
 * its own `heightAt` or its `y`; null where none does. `wall` marks the merged walls deck.
 */
export function mergeDecks(list, id, { cell = 8, wall = false } = {}) {
  const parts = list.filter((d) => d?.pts?.length >= 3);
  if (!parts.length) return null;
  const files = new Map();
  let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity, lo = Infinity;
  for (const d of parts) {
    let a = Infinity, b = -Infinity, c = Infinity, f = -Infinity;
    for (const [e, n] of d.pts) { a = Math.min(a, e); b = Math.max(b, e); c = Math.min(c, n); f = Math.max(f, n); }
    const box = { d, a, b, c, f };
    e0 = Math.min(e0, a); e1 = Math.max(e1, b); n0 = Math.min(n0, c); n1 = Math.max(n1, f);
    if (Number.isFinite(d.y)) lo = Math.min(lo, d.y);
    for (let i = Math.floor(a / cell); i <= Math.floor(b / cell); i++) {
      for (let j = Math.floor(c / cell); j <= Math.floor(f / cell); j++) {
        const k = `${i},${j}`;
        if (!files.has(k)) files.set(k, []);
        files.get(k).push(box);
      }
    }
  }
  const heightAt = (e, n) => {
    const here = files.get(`${Math.floor(e / cell)},${Math.floor(n / cell)}`);
    if (!here) return null;
    let best = null;
    for (const { d, a, b, c, f } of here) {
      if (e < a || e > b || n < c || n > f || !insidePts(e, n, d.pts)) continue;
      const y = d.heightAt ? d.heightAt(e, n) : d.y;
      if (typeof y === 'number' && (best === null || y > best)) best = y;
    }
    return best;
  };
  return { id, y: Number.isFinite(lo) ? lo : 0, pts: [[e0, n0], [e1, n0], [e1, n1], [e0, n1]], heightAt, parts: parts.length,
    ...(wall ? { wall: true } : {}) };
}

/** The stairs' decks merged: [floors, walls] (either left out when empty). */
export function stairSurface(list) {
  return [mergeDecks(list.filter((d) => !d.wall), 'stairs:floors'), mergeDecks(list.filter((d) => d.wall), 'stairs:walls', { wall: true })]
    .filter(Boolean);
}
