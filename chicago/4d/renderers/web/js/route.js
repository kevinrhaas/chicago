/**
 * route.js — the route planner behind auto-travel: "walk me to that building".
 *
 * WHY A GRID AND NOT A STREET GRAPH
 *
 * The obvious design is a graph of the 21 platted streets with the visitor
 * snapped onto the nearest one. It is wrong for this town. A visitor stands
 * ANYWHERE — on the prairie behind a lot, on a wharf deck, on a bridge, in the
 * middle of the public square — and the destination is a stand-off point beside
 * a building, which is off the street by definition. A street graph therefore
 * needs an on-ramp and an off-ramp for every trip, and each ramp has to solve
 * exactly the problem the graph was meant to avoid: getting from an arbitrary
 * point to another past buildings, banks and water. Sixty-six street segments
 * are also far too sparse to describe walkable ground in 1835: people cut
 * across lots and the lots are mostly grass. The honest model of the place is
 * "everything is walkable except buildings and the river", with streets as a
 * PREFERENCE rather than a topology — and that is a cost field, not a graph.
 *
 * So this is A* on a uniform 2 m grid over the heightfield extent, widened to
 * take in any footprint or street that lies past its edge (the terrain answers
 * a flat fallback there and the walker walks it). The grid is built lazily on
 * the first plan (the first `instantly` traveller never pays) and cached;
 * `invalidate()` throws it away. ~548k cells on dev (1022 × 536), about 8 MB of
 * typed arrays including the search scratch; the build samples the heightfield
 * ~1.1 million times and measured 50–150 ms of CPU in node (see REPORT).
 *
 * COST TABLE (per metre travelled; a move is charged the mean of its two cells)
 *
 *   street track (within track_width_m/2 of the drawn line)      0.35
 *   deck (bridge, wharf, plank walk — a floor over water or land) 0.40
 *   street corridor (within corridor_width_m/2 of the plat)      0.60
 *   open ground                                                    1.00
 *   blocked: inside a footprint inflated by radius + 0.6 m, or water without
 *            a deck, or outside the grid                            —
 *
 * The track is cheapest so a route follows the worn wagon path where one is
 * near, the corridor next so a route drifts toward the platted street before
 * it finds the track, and open ground costs full price so a straight line
 * across a lot is taken only when it is genuinely shorter than the street.
 * The octile heuristic is scaled by the cheapest class (0.35) so it stays
 * admissible: the route found is optimal under this table.
 *
 * WATER IS JUDGED AT THE CORNERS, NOT THE CENTRE. A 2 m cell whose centre is dry
 * but whose corner is river is a cell the walker cannot cross corner to corner:
 * the barrier (`terrain.walkHeight`, 4 m over water) stops it mid-cell. So the
 * heightfield is sampled at the grid NODES as well as the centres, and a cell
 * touching water at any of its five samples is blocked unless a deck covers it.
 * The string-pull then re-tests every wet cell it crosses at the exact sample
 * point — inside a deck polygon, or dry ground — because a bridge is narrower
 * than the cells that carry it and a chord across the river beside the planks
 * is the failure the first draft of this file produced.
 *
 * THE STEP RULE. The walker refuses a surface more than `stepUp` (0.35 m) above
 * where it stands and steps down freely (walker.js). The same test is applied
 * at expansion between neighbouring cell centres, which is what makes the
 * planner refuse a wharf deck a metre above the bank and accept the graded
 * approach earthworks to a bridge. On the natural heightfield it is nearly a
 * no-op — the town's whole relief is under 4 m — but it is what stops a route
 * from ending at an edge the walker will not climb.
 *
 * Contract (main.js): createRouter({ terrain, streets, footprints, decks, surfaceAt, cell })
 *   -> { plan(from, to), standOff(id, centre, radiusM), blockedAt(e, n), invalidate(), stats }
 *   plus harness aids: classAt(e, n), heightAt(e, n), warm(), built, bounds, cell.
 *
 * This module imports NOTHING, so the algorithm runs in node against a fixture;
 * `radius` / `stepUp` default to WALK.radius / WALK.stepUp and main.js may pass
 * the live values.
 */

/** Cost classes stored per cell. Kept small so the field is a Uint8Array. */
const CLS_OPEN = 0;
const CLS_CORRIDOR = 1;
const CLS_TRACK = 2;
const CLS_DECK = 3;
const CLS_BLOCKED = 255;

/** Per-metre cost by class (index = class). */
export const ROUTE_COST = Object.freeze({ open: 1.0, corridor: 0.6, track: 0.35, deck: 0.4 });
const COST = new Float32Array([ROUTE_COST.open, ROUTE_COST.corridor, ROUTE_COST.track, ROUTE_COST.deck]);
const MIN_COST = ROUTE_COST.track;
const CLASS_NAME = ['open', 'corridor', 'track', 'deck'];

/**
 * Below this the ground is under water — terrain.js's private SHORE_Y. Duplicated
 * here so ~1.1 million node samples can be classified without a second API call
 * each, and VERIFIED at build time against `terrain.isWater()` on a subsample:
 * if the two ever disagree the build falls back to asking the terrain for every
 * node (slower, still correct) and says so in `stats.shoreMismatch`.
 */
const SHORE_Y = -0.10;

const SQRT2 = Math.SQRT2;
const DEG = Math.PI / 180;

/** Point-in-polygon, ray casting. `pts` is [[e, n], ...]. Same test as walker.js. */
function inside(e, n, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const xi = pts[i][0], yi = pts[i][1];
    const xj = pts[j][0], yj = pts[j][1];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

/** Distance from (e, n) to segment a–b. */
function segDist(e, n, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy || 1e-9;
  let t = ((e - ax) * dx + (n - ay) * dy) / len2;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  return Math.hypot(e - (ax + dx * t), n - (ay + dy * t));
}

/** Distance from (e, n) to the nearest point on a polygon's boundary. */
function boundaryDist(e, n, pts) {
  let best = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const d = segDist(e, n, pts[j][0], pts[j][1], pts[i][0], pts[i][1]);
    if (d < best) best = d;
  }
  return best;
}

function bboxOf(pts) {
  let e0 = Infinity, e1 = -Infinity, n0 = Infinity, n1 = -Infinity;
  for (const p of pts) {
    if (p[0] < e0) e0 = p[0];
    if (p[0] > e1) e1 = p[0];
    if (p[1] < n0) n0 = p[1];
    if (p[1] > n1) n1 = p[1];
  }
  return { e0, e1, n0, n1 };
}

/**
 * A bilinear sampler over the loaded heightfield's own arrays — the same
 * arithmetic as `Heightfield.sample()` in terrain.js (row 0 south, column 0
 * west, clamped at the edges, `fallbackY` outside), inlined because the build
 * takes over a million samples and a method call with five property walks per
 * sample is most of a slow machine's budget. Returns null when the field is not
 * loaded, and the build then goes through the terrain API instead.
 */
function fieldSampler(hf) {
  if (!hf?.loaded || !hf.data || !(hf.cols > 1) || !(hf.rows > 1) || !(hf.cellM > 0)) return null;
  const data = hf.data, cols = hf.cols, rows = hf.rows, cellM = hf.cellM;
  const oe = hf.originE, on = hf.originN, fb = hf.fallbackY ?? 0;
  const maxX = cols - 1, maxY = rows - 1;
  return (e, n) => {
    const gx = (e - oe) / cellM;
    const gy = (n - on) / cellM;
    if (gx < 0 || gy < 0 || gx > maxX || gy > maxY) return fb;
    let x0 = gx | 0; if (x0 > cols - 2) x0 = cols - 2;
    let y0 = gy | 0; if (y0 > rows - 2) y0 = rows - 2;
    const fx = gx - x0, fy = gy - y0;
    const r0 = y0 * cols + x0, r1 = r0 + cols;
    return (data[r0] * (1 - fx) + data[r0 + 1] * fx) * (1 - fy)
         + (data[r1] * (1 - fx) + data[r1 + 1] * fx) * fy;
  };
}

/**
 * A binary min-heap over cell indices keyed by f. Lazy deletion: a cell may be
 * pushed more than once and the stale copies are skipped on pop because the
 * search marks cells closed. Typed arrays that grow by doubling, so a
 * cross-town search allocates a handful of times and then never again.
 */
function makeHeap(capacity = 4096) {
  let keys = new Float64Array(capacity);
  let vals = new Int32Array(capacity);
  let size = 0;
  function grow() {
    const k2 = new Float64Array(keys.length * 2);
    const v2 = new Int32Array(vals.length * 2);
    k2.set(keys); v2.set(vals);
    keys = k2; vals = v2;
  }
  return {
    get size() { return size; },
    clear() { size = 0; },
    push(key, val) {
      if (size === keys.length) grow();
      let i = size++;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (keys[p] <= key) break;
        keys[i] = keys[p]; vals[i] = vals[p];
        i = p;
      }
      keys[i] = key; vals[i] = val;
    },
    pop() {
      const top = vals[0];
      size--;
      if (size > 0) {
        const key = keys[size];
        const val = vals[size];
        let i = 0;
        for (;;) {
          let c = 2 * i + 1;
          if (c >= size) break;
          if (c + 1 < size && keys[c + 1] < keys[c]) c++;
          if (keys[c] >= key) break;
          keys[i] = keys[c]; vals[i] = vals[c];
          i = c;
        }
        keys[i] = key; vals[i] = val;
      }
      return top;
    },
  };
}

/**
 * @param {object} o
 * @param {object} o.terrain     createTerrain()'s object: surfaceHeight, isWater, heightfield
 * @param {object} o.streets     createStreets()'s object: records[] with path/drawn/widths
 * @param {Array<{id:string, pts:number[][]}>} o.footprints  walker obstacles (footprintsFrom)
 * @param {Array<{id:string, y:number, pts:number[][]}>} o.decks  walkable decks (decksFrom + layers)
 * @param {(e:number,n:number)=>number} [o.surfaceAt]  the walker's floor sampler (decks included)
 * @param {number} [o.cell=2]    grid pitch in metres
 * @param {number} [o.radius=0.34]  WALK.radius — the capsule half-width
 * @param {number} [o.stepUp=0.35]  WALK.stepUp — the plank-walk rule
 * @param {number} [o.inflate=0.6]  extra clearance around footprints beyond the radius
 */
export function createRouter({
  terrain = null, streets = null, footprints = [], decks = [], surfaceAt = null,
  cell = 2, radius = 0.34, stepUp = 0.35, inflate = 0.6,
} = {}) {
  const stats = {
    cells: 0, blocked: 0, streetCells: 0, deckCells: 0, fineCells: 0,
    buildMs: 0, lastPlanMs: 0, lastExpanded: 0, plans: 0,
    /** True when SHORE_Y disagreed with terrain.isWater() and the slow path ran. */
    shoreMismatch: false,
    /** 'field' when the heightfield arrays were sampled inline, else 'api'. */
    sampler: null,
  };
  /** The lazily built grid, or null. */
  let grid = null;

  // ---------------------------------------------------------------- build

  /** The metre bounds the grid covers: the heightfield, widened to take in any
   *  footprint or street that lies past its edge (the terrain answers a flat
   *  fallback there and the walker walks it, so the planner should too). */
  function bounds() {
    const hf = terrain?.heightfield;
    let e0, e1, n0, n1;
    if (hf?.loaded && hf.widthM > 0) {
      e0 = hf.originE; e1 = hf.originE + hf.widthM;
      n0 = hf.originN; n1 = hf.originN + hf.depthM;
    } else {
      e0 = -320; e1 = 320; n0 = -400; n1 = 400;
    }
    const take = (b, pad) => {
      if (!b || !Number.isFinite(b.e0) || !Number.isFinite(b.n0)) return;
      e0 = Math.min(e0, b.e0 - pad); e1 = Math.max(e1, b.e1 + pad);
      n0 = Math.min(n0, b.n0 - pad); n1 = Math.max(n1, b.n1 + pad);
    };
    for (const fp of footprints) if (fp?.pts?.length >= 3) take(bboxOf(fp.pts), 30);
    for (const d of decks) if (d?.pts?.length >= 3) take(bboxOf(d.pts), 30);
    for (const r of streets?.records ?? []) take(r.bounds, 10);
    return { e0, e1, n0, n1 };
  }

  function build() {
    const t0 = now();
    const b = bounds();
    const cols = Math.max(2, Math.ceil((b.e1 - b.e0) / cell));
    const rows = Math.max(2, Math.ceil((b.n1 - b.n0) / cell));
    const N = cols * rows;
    const cls = new Uint8Array(N);
    const hgt = new Float32Array(N);
    /** 1 where the cell needs EXACT tests: it touches water at any of its five
     *  samples, or a deck polygon's bbox touches it (a deck edge may cut through
     *  it). Cell-scale answers are trusted everywhere else. */
    const fine = new Uint8Array(N);
    const e0 = b.e0;
    const n0 = b.n0;
    const cE = (i) => e0 + (i + 0.5) * cell;
    const cN = (j) => n0 + (j + 0.5) * cell;

    const fast = fieldSampler(terrain?.heightfield);
    const surf = fast ?? (terrain?.surfaceHeight ? (e, n) => terrain.surfaceHeight(e, n) : () => 0);
    stats.sampler = fast ? 'field' : 'api';

    // Water classification: by SHORE_Y from the sampled height, verified against
    // the terrain's own isWater() on every 61st node; on any disagreement every
    // node is asked through the API instead.
    let waterOf = (e, n, h) => h < SHORE_Y;
    stats.shoreMismatch = false;
    if (terrain?.isWater) {
      const NC = cols + 1, NR = rows + 1;
      let mismatch = false;
      for (let k = 0; k < NC * NR && !mismatch; k += 61) {
        const e = e0 + (k % NC) * cell, n = n0 + ((k / NC) | 0) * cell;
        if (terrain.isWater(e, n) !== (surf(e, n) < SHORE_Y)) mismatch = true;
      }
      if (mismatch) { stats.shoreMismatch = true; waterOf = (e, n) => terrain.isWater(e, n); }
    }

    // 1. Node water flags — (cols+1) x (rows+1) samples at the cell corners —
    //    then per cell: the centre height, and blocked when the centre or any
    //    corner is water (a deck may unblock it below).
    const NC = cols + 1;
    const nodeWet = new Uint8Array(NC * (rows + 1));
    for (let j = 0; j <= rows; j++) {
      const n = n0 + j * cell;
      const row = j * NC;
      for (let i = 0; i <= cols; i++) {
        const e = e0 + i * cell;
        if (waterOf(e, n, surf(e, n))) nodeWet[row + i] = 1;
      }
    }
    for (let j = 0; j < rows; j++) {
      const n = cN(j);
      const row = j * cols;
      const nr0 = j * NC, nr1 = nr0 + NC;
      for (let i = 0; i < cols; i++) {
        const e = cE(i);
        const h = surf(e, n);
        const k = row + i;
        hgt[k] = h;
        if (nodeWet[nr0 + i] | nodeWet[nr0 + i + 1] | nodeWet[nr1 + i] | nodeWet[nr1 + i + 1]
            || waterOf(e, n, h)) {
          fine[k] = 1;
          cls[k] = CLS_BLOCKED;
        }
      }
    }

    // Cell index range covering a metre bbox, clamped to the grid.
    const span = (bb, pad) => ({
      i0: Math.max(0, Math.floor((bb.e0 - pad - e0) / cell)),
      i1: Math.min(cols - 1, Math.floor((bb.e1 + pad - e0) / cell)),
      j0: Math.max(0, Math.floor((bb.n0 - pad - n0) / cell)),
      j1: Math.min(rows - 1, Math.floor((bb.n1 + pad - n0) / cell)),
    });
    // Lower a cell's cost class; never touches a blocked cell.
    const lower = (k, c) => {
      const cur = cls[k];
      if (cur === CLS_BLOCKED) return;
      if (COST[c] < COST[cur]) cls[k] = c;
    };

    // 2. Decks: a floor the heightfield does not carry. Over water the deck
    //    unblocks the cell; over land it is simply a cheap surface. The height
    //    is the walker's own answer where main.js hands one over, so a plan
    //    ends on exactly the plank the boot will stand on; otherwise the same
    //    rule walker.surfaceAt() states (highest deck; over land the higher of
    //    deck and ground). A deck unblocks a wet cell only when its CENTRE is
    //    on the deck; the string-pull re-tests exact points on such cells.
    const deckBoxes = [];
    for (const d of decks) {
      if (!(d?.pts?.length >= 3) || typeof d.y !== 'number') continue;
      const bb = bboxOf(d.pts);
      deckBoxes.push({ pts: d.pts, y: d.y, ...bb });
      const s = span(bb, 0);
      for (let j = s.j0; j <= s.j1; j++) {
        const n = cN(j);
        for (let i = s.i0; i <= s.i1; i++) {
          const e = cE(i);
          const k = j * cols + i;
          fine[k] = 1;
          if (!inside(e, n, d.pts)) continue;
          if (surfaceAt) {
            hgt[k] = surfaceAt(e, n);
          } else if (cls[k] === CLS_BLOCKED) {
            hgt[k] = d.y;               // over water: the deck wins outright
          } else {
            hgt[k] = Math.max(hgt[k], d.y);
          }
          if (cls[k] === CLS_BLOCKED) cls[k] = CLS_DECK;
          else lower(k, CLS_DECK);
        }
      }
    }

    // 3. Streets. Corridor first (the platted right-of-way around `path`), then
    //    the worn track (around the drawn line, or the plat when none is drawn)
    //    which is cheaper and so wins where they overlap.
    const paint = (line, half, c) => {
      if (!Array.isArray(line) || line.length < 2) return;
      for (let s = 1; s < line.length; s++) {
        const ax = line[s - 1][0], ay = line[s - 1][1];
        const bx = line[s][0], by = line[s][1];
        const sp = span({
          e0: Math.min(ax, bx), e1: Math.max(ax, bx),
          n0: Math.min(ay, by), n1: Math.max(ay, by),
        }, half);
        for (let j = sp.j0; j <= sp.j1; j++) {
          const n = cN(j);
          for (let i = sp.i0; i <= sp.i1; i++) {
            if (segDist(cE(i), n, ax, ay, bx, by) <= half) lower(j * cols + i, c);
          }
        }
      }
    };
    const records = streets?.records ?? [];
    for (const r of records) paint(r.path, (r.corridor_width_m ?? 24.384) * 0.5, CLS_CORRIDOR);
    for (const r of records) paint(r.drawn ?? r.path, (r.track_width_m ?? 6) * 0.5, CLS_TRACK);

    // 4. Footprints, inflated by the capsule radius plus a margin so a planned
    //    point never sits where pushOut() would immediately move it. Per
    //    polygon over its own bbox — never every polygon per cell.
    const R = radius + inflate;
    for (const fp of footprints) {
      if (!(fp?.pts?.length >= 3)) continue;
      const s = span(bboxOf(fp.pts), R);
      for (let j = s.j0; j <= s.j1; j++) {
        const n = cN(j);
        for (let i = s.i0; i <= s.i1; i++) {
          const e = cE(i);
          if (inside(e, n, fp.pts) || boundaryDist(e, n, fp.pts) < R) cls[j * cols + i] = CLS_BLOCKED;
        }
      }
    }

    let blocked = 0, streetCells = 0, deckCells = 0, fineCells = 0;
    for (let k = 0; k < N; k++) {
      const c = cls[k];
      if (fine[k]) fineCells++;
      if (c === CLS_BLOCKED) blocked++;
      else if (c === CLS_TRACK || c === CLS_CORRIDOR) streetCells++;
      else if (c === CLS_DECK) deckCells++;
    }
    stats.cells = N; stats.blocked = blocked; stats.streetCells = streetCells;
    stats.deckCells = deckCells; stats.fineCells = fineCells;

    grid = {
      cols, rows, N, e0, n0, cls, hgt, fine, deckBoxes, surf, waterOf,
      // Search scratch, allocated once. `seen`/`done` are generation stamps so
      // a plan never clears 400k entries before it starts.
      g: new Float32Array(N), parent: new Int32Array(N),
      seen: new Uint32Array(N), done: new Uint32Array(N), gen: 0,
      heap: makeHeap(),
    };
    stats.buildMs = now() - t0;
    return grid;
  }

  function ensure() { return grid ?? build(); }

  // ---------------------------------------------------------------- lookups

  const cellI = (e) => Math.floor((e - grid.e0) / cell);
  const cellJ = (n) => Math.floor((n - grid.n0) / cell);
  const inGrid = (i, j) => i >= 0 && j >= 0 && i < grid.cols && j < grid.rows;
  const centreE = (i) => grid.e0 + (i + 0.5) * cell;
  const centreN = (j) => grid.n0 + (j + 0.5) * cell;

  /** Cell index for a metre point, or -1 outside the grid. */
  function indexAt(e, n) {
    const i = cellI(e), j = cellJ(n);
    return inGrid(i, j) ? j * grid.cols + i : -1;
  }

  /**
   * The nearest free cell to (e, n) within `maxCells` rings, searched ring by
   * ring and choosing the closest hit in the first ring that has one. Optional
   * `want` restricts the hit to one class (used to find the street track).
   */
  function nearestCell(e, n, maxCells, want = -1) {
    const ci = cellI(e), cj = cellJ(n);
    const { cols, rows, cls } = grid;
    for (let r = 0; r <= maxCells; r++) {
      let best = -1, bestD = Infinity;
      const i0 = ci - r, i1 = ci + r, j0 = cj - r, j1 = cj + r;
      for (let j = j0; j <= j1; j++) {
        if (j < 0 || j >= rows) continue;
        const ring = (j === j0 || j === j1);
        const step = ring ? 1 : (i1 - i0 || 1);
        for (let i = i0; i <= i1; i += step) {
          if (i < 0 || i >= cols) continue;
          const k = j * cols + i;
          const c = cls[k];
          if (want >= 0 ? c !== want : c === CLS_BLOCKED) continue;
          const d = Math.hypot(centreE(i) - e, centreN(j) - n);
          if (d < bestD) { bestD = d; best = k; }
        }
      }
      if (best >= 0) return best;
    }
    return -1;
  }

  /**
   * Straight-line walkability between two metre points, sampled every 0.5 m
   * over the blocked mask and the step rule — the same two tests the search
   * applied, so a pulled leg is never one the search would have refused.
   */
  function lineOfSight(ae, an, be, bn) {
    const len = Math.hypot(be - ae, bn - an);
    const steps = Math.max(1, Math.ceil(len / 0.5));
    const { cls, fine, hgt } = grid;
    let k = indexAt(ae, an);
    if (k < 0 || cls[k] === CLS_BLOCKED) return false;
    let prevH = fine[k] ? exactHeight(ae, an) : hgt[k];
    if (prevH === null) return false;
    for (let s = 1; s <= steps; s++) {
      const t = s / steps;
      const e = ae + (be - ae) * t, n = an + (bn - an) * t;
      k = indexAt(e, n);
      if (k < 0 || cls[k] === CLS_BLOCKED) return false;
      // Cells that touch water or a deck edge are judged at the exact point:
      // the planks or dry ground, at the height the boot would find. Elsewhere
      // the sampled ground is the walk surface.
      const h = fine[k] ? exactHeight(e, n) : grid.surf(e, n);
      if (h === null || h - prevH > stepUp) return false;
      prevH = h;
    }
    return true;
  }

  /**
   * The walk surface at an exact point, by walker.surfaceAt()'s rule over the
   * decks this grid knows: the highest covering deck wins outright over water
   * and against the ground over land; water with no deck is null (the walker's
   * barrier). Bbox-gated, so it is cheap on the few cells that need it.
   */
  function exactHeight(e, n) {
    let deckY = null;
    for (const d of grid.deckBoxes) {
      if (e < d.e0 || e > d.e1 || n < d.n0 || n > d.n1) continue;
      if ((deckY !== null && d.y <= deckY) || !inside(e, n, d.pts)) continue;
      deckY = d.y;
    }
    const ground = grid.surf(e, n);
    const water = grid.waterOf(e, n, ground);
    if (deckY === null) return water ? null : ground;
    return water ? deckY : Math.max(deckY, ground);
  }

  // ---------------------------------------------------------------- A*

  /** Offsets: di, dj, distance factor. Orthogonals first. */
  const DIRS = [
    [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
    [1, 1, SQRT2], [1, -1, SQRT2], [-1, 1, SQRT2], [-1, -1, SQRT2],
  ];

  function octile(i, j, gi, gj) {
    const dx = Math.abs(i - gi), dy = Math.abs(j - gj);
    return (dx > dy ? dx + (SQRT2 - 1) * dy : dy + (SQRT2 - 1) * dx) * cell * MIN_COST;
  }

  /** Search from cell `s` to cell `t`. Returns the cell index list or null. */
  function search(s, t) {
    const { cols, rows, cls, hgt, fine, g, parent, seen, done, heap } = grid;
    const gen = ++grid.gen;
    const gi = t % cols, gj = (t / cols) | 0;
    heap.clear();
    g[s] = 0; parent[s] = -1; seen[s] = gen;
    heap.push(octile(s % cols, (s / cols) | 0, gi, gj), s);
    let expanded = 0;

    while (heap.size) {
      const cur = heap.pop();
      if (done[cur] === gen) continue;
      done[cur] = gen;
      expanded++;
      if (cur === t) break;

      const ci = cur % cols, cj = (cur / cols) | 0;
      const hc = hgt[cur];
      const gc = g[cur];
      const costC = COST[cls[cur]];
      for (let d = 0; d < 8; d++) {
        const di = DIRS[d][0], dj = DIRS[d][1];
        const ni = ci + di, nj = cj + dj;
        if (ni < 0 || nj < 0 || ni >= cols || nj >= rows) continue;
        const nb = nj * cols + ni;
        const c = cls[nb];
        if (c === CLS_BLOCKED || done[nb] === gen) continue;
        // No corner cutting: a diagonal may not squeeze past a blocked
        // orthogonal neighbour — the capsule would clip the wall.
        if (d >= 4 && (cls[cj * cols + ni] === CLS_BLOCKED || cls[nj * cols + ci] === CLS_BLOCKED)) continue;
        // The step rule: up is limited, down is free.
        if (hgt[nb] - hc > stepUp) continue;
        // A move that touches a deck edge or the water's edge is walked at
        // the exact points between the two centres, not judged by them.
        if ((fine[cur] | fine[nb])
            && !lineOfSight(centreE(ci), centreN(cj), centreE(ni), centreN(nj))) continue;
        const ng = gc + DIRS[d][2] * cell * 0.5 * (costC + COST[c]);
        if (seen[nb] === gen && ng >= g[nb]) continue;
        seen[nb] = gen;
        g[nb] = ng;
        parent[nb] = cur;
        heap.push(ng + octile(ni, nj, gi, gj), nb);
      }
    }
    stats.lastExpanded = expanded;
    if (done[t] !== gen) return null;
    const out = [];
    for (let k = t; k !== -1; k = parent[k]) out.push(k);
    out.reverse();
    return out;
  }

  /**
   * Resolve a metre point to the cell the search should use: its own cell when
   * free, else the nearest free cell within `snapCells` rings (a visitor may be
   * standing against a wall; a footprint centre is blocked by definition).
   * Returns { k, e, n, snapped } or null when nothing free is near.
   */
  function anchor(p, snapCells = 4) {
    const k = indexAt(p.e, p.n);
    if (k >= 0 && grid.cls[k] !== CLS_BLOCKED) return { k, e: p.e, n: p.n, snapped: false };
    // Outside the grid: clamp toward the grid before searching.
    const e = Math.min(grid.e0 + grid.cols * cell - cell * 0.5, Math.max(grid.e0 + cell * 0.5, p.e));
    const n = Math.min(grid.n0 + grid.rows * cell - cell * 0.5, Math.max(grid.n0 + cell * 0.5, p.n));
    const nk = nearestCell(e, n, snapCells);
    if (nk < 0) return null;
    return { k: nk, e: centreE(nk % grid.cols), n: centreN((nk / grid.cols) | 0), snapped: true };
  }

  /**
   * String-pulling within runs of one cost class. A run of track cells is
   * straightened only against other track cells, so a street leg stays a
   * street leg instead of being pulled into a chord across the lots; an open
   * ground leg is straightened against the blocked mask alone, which is what
   * "cut across the grass" should mean.
   */
  function pull(pts) {
    if (pts.length <= 2) return pts;
    const out = [pts[0]];
    let a = 0;
    while (a < pts.length - 1) {
      const c = pts[a].c;
      let end = a;
      while (end + 1 < pts.length && pts[end + 1].c === c) end++;
      // Greedy forward: extend while the straight line stays walkable.
      let k = a + 1;
      while (k < end && lineOfSight(pts[a].e, pts[a].n, pts[k + 1].e, pts[k + 1].n)) k++;
      out.push(pts[k]);
      a = k;
    }
    return out;
  }

  // ---------------------------------------------------------------- API

  function now() {
    return (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
  }

  /**
   * @param {{e:number,n:number}} from
   * @param {{e:number,n:number}} to
   * @returns {{points:number[][], length_m:number}|null}
   */
  function plan(from, to) {
    if (!from || !to || !Number.isFinite(from.e) || !Number.isFinite(to.e)) return null;
    ensure();
    const t0 = now();
    stats.plans++;
    const a = anchor(from);
    const b = anchor(to);
    if (!a || !b) { stats.lastPlanMs = now() - t0; return null; }

    let cells;
    if (a.k === b.k) cells = [a.k];
    else {
      cells = search(a.k, b.k);
      if (!cells) { stats.lastPlanMs = now() - t0; return null; }
    }

    // Cell centres with their classes. The start is where the visitor actually
    // stands (a wall they lean on makes their cell blocked, but the few metres
    // to the snapped cell are theirs to walk); the goal is the snapped centre
    // when the asked-for point was blocked — nobody can be sent inside a wall.
    const { cols, cls } = grid;
    const pts = [{ e: from.e, n: from.n, c: cls[a.k] }];
    if (a.snapped) pts.push({ e: a.e, n: a.n, c: cls[a.k] });
    for (let i = 1; i < cells.length - 1; i++) {
      const k = cells[i];
      pts.push({ e: centreE(k % cols), n: centreN((k / cols) | 0), c: cls[k] });
    }
    pts.push({ e: b.e, n: b.n, c: cls[b.k] });

    const points = [];
    for (const p of pull(pts)) {
      const last = points[points.length - 1];
      if (last && Math.abs(last[0] - p.e) < 1e-6 && Math.abs(last[1] - p.n) < 1e-6) continue;
      points.push([p.e, p.n]);
    }
    let length = 0;
    for (let i = 1; i < points.length; i++) {
      length += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
    }
    stats.lastPlanMs = now() - t0;
    return { points, length_m: length };
  }

  /**
   * Where to stand to look at a building: `max(8, radiusM + 5)` m from its
   * centre toward the nearest street track (its front, in a town where every
   * building faces the road), tested unblocked; failing that the same distance
   * at 30° steps around; failing that the nearest free cell. No search.
   *
   * @param {string} id  the structure (unused by the geometry; kept for callers)
   * @param {{e:number,n:number}} centre
   * @param {number} radiusM
   * @returns {{e:number,n:number}}
   */
  /**
   * Which way a building FACES, as the router reads it: the bearing from its
   * centre to the nearest street track (radians, compass), or south-west when
   * no street is within 150 m — the walker's own default stance.
   */
  function frontBearing(centre) {
    ensure();
    const track = nearestCell(centre.e, centre.n, Math.ceil(150 / cell), CLS_TRACK);
    if (track < 0) return 200 * DEG;
    return Math.atan2(centreE(track % grid.cols) - centre.e, centreN((track / grid.cols) | 0) - centre.n);
  }

  /**
   * A free standing point in front of a building. `distance` (metres from the
   * centre) is the caller's when given — main.js's framing rule computes the one
   * that fits the whole building in view (T-0824) — else the old stand-off,
   * `max(8, radius + 5)`.
   */
  function standOff(id, centre, radiusM = 0, { distance = null } = {}) {
    if (!centre || !Number.isFinite(centre.e) || !Number.isFinite(centre.n)) return centre;
    ensure();
    const d = Number.isFinite(distance) && distance > 0 ? distance : Math.max(8, (Number(radiusM) || 0) + 5);
    const bearing = frontBearing(centre);
    // 0, +30, -30, +60, -60, … 180.
    for (let step = 0; step <= 6; step++) {
      for (const sign of (step === 0 || step === 6) ? [1] : [1, -1]) {
        const th = bearing + sign * step * 30 * DEG;
        const e = centre.e + Math.sin(th) * d;
        const n = centre.n + Math.cos(th) * d;
        const k = indexAt(e, n);
        if (k >= 0 && grid.cls[k] !== CLS_BLOCKED) return { e, n };
      }
    }
    const free = nearestCell(centre.e, centre.n, Math.ceil(60 / cell));
    if (free >= 0) return { e: centreE(free % grid.cols), n: centreN((free / grid.cols) | 0) };
    return { e: centre.e, n: centre.n };
  }

  /** True where the planner will not put a route: footprint, water, off-grid. */
  function blockedAt(e, n) {
    ensure();
    const k = indexAt(e, n);
    return k < 0 || grid.cls[k] === CLS_BLOCKED;
  }

  /** The cost class under a point, by name — a debugging aid for harnesses. */
  function classAt(e, n) {
    ensure();
    const k = indexAt(e, n);
    if (k < 0) return 'outside';
    const c = grid.cls[k];
    return c === CLS_BLOCKED ? 'blocked' : CLASS_NAME[c];
  }

  /** The walk surface the grid sampled under a point (NaN off-grid). */
  function heightAt(e, n) {
    ensure();
    const k = indexAt(e, n);
    return k < 0 ? NaN : grid.hgt[k];
  }

  function invalidate() { grid = null; }

  return {
    plan,
    standOff,
    frontBearing,
    blockedAt,
    classAt,
    heightAt,
    invalidate,
    /** Build the grid now rather than on the first plan (harness convenience). */
    warm() { ensure(); return stats; },
    stats,
    get cell() { return cell; },
    get built() { return grid !== null; },
    get bounds() {
      if (!grid) return null;
      return { e0: grid.e0, e1: grid.e0 + grid.cols * cell, n0: grid.n0, n1: grid.n0 + grid.rows * cell, cols: grid.cols, rows: grid.rows };
    },
  };
}
