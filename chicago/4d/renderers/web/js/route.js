import { deckHeightAt } from './deck-surface.js';
/**
 * route.js — the route planner behind auto-travel: "walk me to that building".
 *
 * Ground travel joins the dated street network by a collision-safe access leg,
 * follows that network, then takes a safe final approach. Walking prefers the
 * rendered sidewalks and plank walks; horses and wagons use the road tracks.
 * In 1835, unpaved street corridors connect incomplete stretches of plank walk.
 * In 1904, the street-grid carriageways, sidewalk bands and intersection ends
 * supply the network. No modern street grid is imported into an earlier era.
 *
 * A* runs on a cached grid. Footprints are expanded by the walker's capsule,
 * clearance and cell half-diagonal, so even thin walls between cell centres
 * remain obstacles. String-pulling tests every intervening cell's surface class
 * as well as collision clearance: a street bend cannot become a lawn shortcut.
 * Legacy callers without a mode can still request an unrestricted safe path.
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
 * This module has no renderer dependencies and runs in node against fixtures;
 * `radius` / `stepUp` default to WALK.radius / WALK.stepUp and main.js may pass
 * the live values.
 */

/** T-3405: how far either side of a fort gateway its lane is reopened (route.js 4c). */
const GATE_LANE_M = 12;
/** A gateway's span `{a, b}` as a passage lane: the strip GATE_LANE_M either side of it,
 *  its two long sides as walls (the shape lanesOf() gives inLane()), and the line through
 *  it a route is held to: `offset` metres along the span from its middle (gateLine). */
function gateLane({ a, b }, offset = 0) {
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
  const ne = -(b[1] - a[1]) / len * GATE_LANE_M, nn = (b[0] - a[0]) / len * GATE_LANE_M;
  const p = (q, k) => [q[0] + ne * k, q[1] + nn * k];
  const lane = [p(a, -1), p(b, -1), p(b, 1), p(a, 1)];
  const u = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
  return { lane, walls: [[lane[0], lane[3]], [lane[1], lane[2]]], u,
    mid: [(a[0] + b[0]) / 2 + u[0] * offset, (a[1] + b[1]) / 2 + u[1] * offset],
    normal: [ne / GATE_LANE_M, nn / GATE_LANE_M] };
}
/** T-3405: how far before and after a gateway a route is held to its middle. */
const GATE_APPROACH_M = 1.5;
/** Clearance at which a gateway's line is out in the open (gateLine). */
const OPEN_CLEAR_M = 2.5;
/** Segments ab and cd cross: the parameter t along ab where they do, else null. */
function crossAt(a, b, c, d) {
  const rx = b[0] - a[0], ry = b[1] - a[1], sx = d[0] - c[0], sy = d[1] - c[1];
  const den = rx * sy - ry * sx;
  if (Math.abs(den) < 1e-12) return null;
  const t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den, u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den;
  return t >= 0 && t <= 1 && u >= 0 && u <= 1 ? t : null;
}
/** A route through a gateway goes straight through it, square to it, on its line. */
function throughGates(points, spans, laneOf) {
  if (!spans.length) return points;
  const out = [points[0]];
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1], b = points[i];
    const hits = [];
    for (const g of spans) { const t = crossAt(a, b, g.a, g.b); if (t !== null) hits.push({ t, g }); }
    hits.sort((x, y) => x.t - y.t);
    for (const { g } of hits) {
      const lane = laneOf(g);
      if (!lane) continue;
      const side = Math.sign((b[0] - a[0]) * lane.normal[0] + (b[1] - a[1]) * lane.normal[1]) || 1;
      const at = k => [lane.mid[0] + lane.normal[0] * k * side, lane.mid[1] + lane.normal[1] * k * side];
      out.push(at(-GATE_APPROACH_M), at(GATE_APPROACH_M));
    }
    out.push(b);
  }
  return out;
}

/** T-3691: a world whose whole 1 m grid is over this many cells keeps a window instead (1812's
 *  whole grid is 19.3 M cells, 1835's 11.9 M; 1871's would be 124 M). */
export const WHOLE_GRID_MAX_CELLS = 24e6;
/** T-3691: the window's size in cells, 23 bytes each: 12 M is 3.5 km square at 1 m, ~280 MB. */
export const WINDOW_CELLS = 12e6;
/** T-3691: the bucket an extra layer's buildings are filed in for clearSegment's near test. */
const EXTRA_BUCKET_M = 40;
/** T-3691: a yard-to-yard walk this near the straight line is taken over the street round. */
const DIRECT_STRAIGHT_RATIO = 1.5;
/** T-3691: two points this near are tried straight across before the street round. */
const DIRECT_TRY_M = 80;
/** T-3691: how far inside the window's edges the visitor (and a walk's two ends) are held. */
const HOLD_MARGIN_M = 250;
/** T-3691: a building's stand is searched 150 m round its front: the window keeps that much. */
const PIN_MARGIN_M = 160;

/** Cost classes stored per cell. Kept small so the field is a Uint8Array. */
const CLS_OPEN = 0;
const CLS_CORRIDOR = 1;
const CLS_TRACK = 2;
const CLS_DECK = 3;
const CLS_WALK = 4;
const CLS_CROSSING = 5;
const CLS_BLOCKED = 255;

/** Per-metre cost by class (index = class). */
export const ROUTE_COST = Object.freeze({ open: 1.0, corridor: 0.6, track: 0.35, deck: 0.4 });
const COST = new Float32Array([ROUTE_COST.open, ROUTE_COST.corridor, ROUTE_COST.track, ROUTE_COST.deck, 0.35, 0.4]);
const MIN_COST = ROUTE_COST.track;
const CLASS_NAME = ['open', 'corridor', 'track', 'deck', 'sidewalk', 'crossing'];

/**
 * Below this the ground is under water — terrain.js's private SHORE_Y. Duplicated
 * here so ~1.1 million node samples can be classified without a second API call
 * each, and VERIFIED at build time against `terrain.isWater()` on a subsample:
 * if the two ever disagree the build falls back to asking the terrain for every
 * node (slower, still correct) and says so in `stats.shoreMismatch`.
 */
const SHORE_Y = -0.10;

/**
 * T-3263 — what a blocked view costs a stand, in the stand-off score's metres (a metre
 * off the wanted distance is 1, a metre along the street from the front's middle 4).
 * The house's own parkway trees, across the street, hide a tenth of a front from any
 * stand: that toll is only weighed. A trunk or post near the eye in the middle of the
 * frame (over VIEW_NEAR_BLOCKED), or more than VIEW_BLOCKED hidden in all, all but
 * refuses the stand, so a clear one a step or two along the walk wins.
 * tools/check_jaunt_views.mjs gates every 1904 jaunt stop against both.
 */
export const VIEW_BLOCKED = 0.3;
export const VIEW_NEAR_BLOCKED = 0.05;
const VIEW_COST = 20;
const VIEW_REFUSED = 400;

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

/**
 * T-3263 — how much of a building's street front an eye at `eye` cannot see for the
 * trunks and posts standing between them: the share (0..1) of the front's angular
 * width, from that eye, covered by any `occluder` ({ e, n, r }) on the street side of
 * the front and short of the eye. The owner, 2026-10-30, on a jaunt stop that put the
 * camera behind a parkway elm: "make sure that the stops are not right behind a tree,
 * that you can move and find a point that has a view of the house a few feet north or
 * south and look at it". A trunk two metres from the eye covers a fifth of a house
 * across the street; the same trunk in the house's own parkway covers a twentieth, and
 * that one no stand on this street can avoid. An eye inside an occluder sees nothing.
 *
 * `front` is `frontage()`'s answer: the middle of the street face, its compass
 * `bearing` (outward) and its `width`.
 */
export function frontBlocked(eye, front, occluders = [], options = {}) {
  return frontView(eye, front, occluders, options).hidden;
}

/** frontBlocked's two halves: `hidden`, the whole share, and `near`, the share the
 *  trunks and posts within `nearM` of the eye alone take — the "right behind a tree"
 *  the owner reported, which a step along the walk always cures. */
export function frontView(eye, front, occluders = [], { margin = 0.15, padDeg = 4, nearM = 8, frameDeg = 32 } = {}) {
  const none = { hidden: 0, near: 0 };
  if (!eye || !front || !occluders.length) return none;
  const ne = Math.sin(front.bearing), nn = Math.cos(front.bearing);
  const eyeOut = (eye.e - front.e) * ne + (eye.n - front.n) * nn;
  if (!(eyeOut > 0.5)) return none;
  const half = Math.max(1, front.width ?? 12) / 2;
  const toward = (e, n) => Math.atan2(e - eye.e, n - eye.n);
  const mid = toward(front.e, front.n);
  const rel = (a) => Math.atan2(Math.sin(a - mid), Math.cos(a - mid));
  const a = rel(toward(front.e + nn * half, front.n - ne * half));
  const b = rel(toward(front.e - nn * half, front.n + ne * half));
  // A little air either side of the house is part of seeing it: a trunk that grazes
  // a corner from a metre off still fills the side of the frame.
  const pad = padDeg * Math.PI / 180;
  const lo = Math.min(a, b) - pad, hi = Math.max(a, b) + pad;
  // And a trunk within `nearM` of the eye is in the way anywhere in the middle of the
  // frame (±frameDeg), off the house or not: a metre beside one it still fills the
  // picture. Its share counts three times against the house's, so the stand steps
  // clear of it rather than edging until it grazes the frame's middle.
  const frame = frameDeg * Math.PI / 180;
  const nearLo = Math.min(lo, -frame), nearHi = Math.max(hi, frame);
  const spans = [], nearSpans = [];
  for (const o of occluders) {
    const r = (o.r ?? 0.3) + margin;
    const d = Math.hypot(o.e - eye.e, o.n - eye.n);
    if (d <= r) return { hidden: 1, near: 1 };
    const out = (o.e - front.e) * ne + (o.n - front.n) * nn;
    if (out <= 0 || out >= eyeOut) continue;
    const c = rel(toward(o.e, o.n)), w = Math.asin(Math.min(1, r / d));
    const isNear = d < nearM;
    const s0 = Math.max(isNear ? nearLo : lo, c - w), s1 = Math.min(isNear ? nearHi : hi, c + w);
    if (s1 > s0) (isNear ? nearSpans : spans).push([s0, s1]);
  }
  const near = 3 * union(nearSpans) / (hi - lo);
  return { hidden: Math.min(1, union(spans) / (hi - lo) + near), near: Math.min(1, near) };
}

/** The total length of a set of [from, to] intervals, overlaps counted once. */
function union(spans) {
  spans.sort((p, q) => p[0] - q[0]);
  let covered = 0, end = -Infinity;
  for (const [s0, s1] of spans) {
    if (s1 <= end) continue;
    covered += s1 - Math.max(s0, end);
    end = s1;
  }
  return covered;
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
 * @param {number} [o.passageNeed=0]  the headroom a footprint's passage lane must clear to be
 *   walked (T-3264: the walker's eye plus its margin; a lower soffit stays a wall)
 * @param {(e:number,n:number)=>boolean} [o.standClear]  T-3691: false where a body may not
 *   stand (a 1904 house's stoop, area walls and railings, house-barriers.js); a side stand
 *   (standOff's second look) is never put there
 */
export function createRouter({
  terrain = null, streets = null, footprints = [], decks = [], surfaceAt = null,
  streetGrid = null, walks = [], occluders = null, standClear = null,
  cell = 2, radius = 0.34, stepUp = 0.35, inflate = 0.6, passageNeed = 0,
  maxCells = WHOLE_GRID_MAX_CELLS, windowCells = WINDOW_CELLS, focus = null, extra = null,
} = {}) {
  const stats = {
    cells: 0, blocked: 0, streetCells: 0, deckCells: 0, fineCells: 0,
    /** T-3691: true when the world is too big for one grid and a window round the visitor is kept. */
    windowed: false, recentres: 0, world: null,
    buildMs: 0, lastPlanMs: 0, lastExpanded: 0, plans: 0,
    /** True when SHORE_Y disagreed with terrain.isWater() and the slow path ran. */
    shoreMismatch: false,
    /** 'field' when the heightfield arrays were sampled inline, else 'api'. */
    sampler: null,
  };
  /** The lazily built grid, or null. */
  let grid = null;
  const fronts = new Map();
  const stands = new Map();
  /** T-3263 — the trunks and posts a stand must see past: `occluders` is an array of
   *  { e, n, r } or a function answering one (main.js reads the live tree layers). A
   *  new array is a new street, so the stands chosen against the old one are dropped. */
  let occludersSeen = null;
  function occluderList() {
    const list = (typeof occluders === 'function' ? occluders() : occluders) ?? [];
    if (list !== occludersSeen) { occludersSeen = list; stands.clear(); }
    return list;
  }

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
    for (const r of streetGrid?.carriageways ?? []) take(bboxOf(r.polygon_local_m ?? []), 30);
    return { e0, e1, n0, n1 };
  }

  // T-3691 (the owner, 2026-11-21, on his phone: the Great Fire and The Last Sunday would not
  // start): 1871's heightfield is 10.8 x 11.45 km, so the whole-world grid at 1 m was 124
  // million cells, 2.9 GB of arrays and 12 s, built by the first stand check of a jaunt. A world
  // over `maxCells` keeps a WINDOW instead: `windowCells` round the visitor (`focus()`, null
  // while flying), moved when the visitor nears its edge, its arrays reused. Off the window the
  // planner answers as it does before it is built: no plan (travel flies), nothing blocked.
  // 1812, 1835 and 1904 fit under `maxCells` and keep their whole grid, unchanged.
  let world = null, windowed = false, pool = null;
  function measureWorld() {
    if (world) return;
    world = bounds();
    const cols = Math.max(2, Math.ceil((world.e1 - world.e0) / cell));
    const rows = Math.max(2, Math.ceil((world.n1 - world.n0) / cell));
    windowed = cols * rows > maxCells;
    stats.windowed = windowed;
    stats.world = { ...world, cols, rows };
  }
  /** The window's metre bounds, centred on (e, n) as near as the world's edges allow. */
  function windowAt(e, n) {
    const want = Math.max(4, Math.floor(typeof windowCells === 'function' ? windowCells() : windowCells));
    const wc = Math.max(2, Math.ceil((world.e1 - world.e0) / cell)), wr = Math.max(2, Math.ceil((world.n1 - world.n0) / cell));
    const side = Math.floor(Math.sqrt(want));
    const cols = Math.min(wc, side), rows = Math.min(wr, Math.floor(want / cols));
    const fit = (c, lo, cells, total) => {
      const span = cells * cell, start = Math.round((c - span / 2 - lo) / cell) * cell + lo;
      return Math.min(Math.max(start, lo), lo + Math.max(0, total * cell - span));
    };
    const e0 = fit(e, world.e0, cols, wc), n0 = fit(n, world.n0, rows, wr);
    return { e0, e1: e0 + cols * cell, n0, n1: n0 + rows * cell, cols, rows };
  }
  const inWorld = (e, n) => e >= world.e0 && e < world.e1 && n >= world.n0 && n < world.n1;
  /** The points are well inside the window: HOLD_MARGIN_M (at most a quarter of its width)
   *  from each edge, except an edge that is the world's own (nothing past it to move toward). */
  function holds(g, ...pts) {
    const w = g.cols * cell, h = g.rows * cell, x1 = g.e0 + w, y1 = g.n0 + h;
    const me = Math.min(HOLD_MARGIN_M, w / 4), mn = Math.min(HOLD_MARGIN_M, h / 4);
    return pts.every(p => (g.e0 <= world.e0 || p.e >= g.e0 + me) && (x1 >= world.e1 || p.e <= x1 - me)
      && (g.n0 <= world.n0 || p.n >= g.n0 + mn) && (y1 >= world.n1 || p.n <= y1 - mn));
  }
  /** A walk the visitor asks for: the window is moved to hold both ends when it can (a
   *  leg under about 1.9 km on a phone, 2.9 km on a computer), so a jaunt's walk across
   *  downtown is walked; a longer one is flown. True when the grid holds both ends. */
  function cover(a, b) {
    measureWorld();
    if (!windowed) return false;
    const ok = (q) => Number.isFinite(q.e) && Number.isFinite(q.n) && inWorld(q.e, q.n);
    if (!ok(a) || !ok(b)) return false;
    if (grid && holds(grid, a, b)) return true;
    const w = windowAt((a.e + b.e) / 2, (a.n + b.n) / 2);
    if (!holds(w, a, b)) return false;
    if (grid) { stats.recentres++; fronts.clear(); stands.clear(); gateLines.clear(); }
    grid = null;
    build(w, w);
    return true;
  }

  /** T-3691: the extra layer's features within `b`, its buildings bucketed for near lookups. */
  function buildExtra(b) {
    const got = typeof extra === 'function' ? extra({ e0: b.e0 - 60, e1: b.e1 + 60, n0: b.n0 - 60, n1: b.n1 + 60 }) : null;
    if (!got) return null;
    const fps = (got.footprints ?? []).filter(f => f?.pts?.length >= 3);
    const buckets = new Map();
    for (const f of fps) {
      const bb = f.bbox ?? bboxOf(f.pts);
      for (let i = Math.floor(bb.e0 / EXTRA_BUCKET_M); i <= Math.floor(bb.e1 / EXTRA_BUCKET_M); i++) {
        for (let j = Math.floor(bb.n0 / EXTRA_BUCKET_M); j <= Math.floor(bb.n1 / EXTRA_BUCKET_M); j++) {
          const key = `${i},${j}`;
          if (!buckets.has(key)) buckets.set(key, []);
          buckets.get(key).push(f);
        }
      }
    }
    return { footprints: fps, streets: got.streets ?? [], walks: got.walks ?? [], buckets };
  }
  /** The street records the grid was painted with: the layer's own and any extra's. */
  const streetRecords = () => grid?.records ?? streets?.records ?? [];
  /** Every footprint whose box comes within `pad` of the box (e0..e1, n0..n1). */
  function footprintsIn(e0, e1, n0, n1, pad) {
    const out = footprints.filter(f => {
      const b = bboxOf(f.pts);
      return b.e1 + pad >= e0 && b.e0 - pad <= e1 && b.n1 + pad >= n0 && b.n0 - pad <= n1;
    });
    const ex = grid?.ex;
    if (!ex) return out;
    const seen = new Set();
    for (let i = Math.floor((e0 - pad) / EXTRA_BUCKET_M); i <= Math.floor((e1 + pad) / EXTRA_BUCKET_M); i++) {
      for (let j = Math.floor((n0 - pad) / EXTRA_BUCKET_M); j <= Math.floor((n1 + pad) / EXTRA_BUCKET_M); j++) {
        for (const f of ex.buckets.get(`${i},${j}`) ?? []) {
          if (seen.has(f)) continue;
          seen.add(f);
          const b = f.bbox ?? bboxOf(f.pts);
          if (b.e1 + pad >= e0 && b.e0 - pad <= e1 && b.n1 + pad >= n0 && b.n0 - pad <= n1) out.push(f);
        }
      }
    }
    return out;
  }

  function build(b = bounds(), dims = null) {
    const t0 = now();
    const cols = dims?.cols ?? Math.max(2, Math.ceil((b.e1 - b.e0) / cell));
    const rows = dims?.rows ?? Math.max(2, Math.ceil((b.n1 - b.n0) / cell));
    const N = cols * rows;
    // A moved window is the same size: its arrays are cleared and reused, never a second set
    // alongside the first (the GC need not keep up with a walk across the city).
    const reuse = windowed && pool?.N === N ? pool : null;
    if (reuse) { reuse.cls.fill(0); reuse.fine.fill(0); reuse.network.fill(0); reuse.seen.fill(0); reuse.done.fill(0); }
    const cls = reuse?.cls ?? new Uint8Array(N);
    const hgt = reuse?.hgt ?? new Float32Array(N);
    /** 1 where the cell needs EXACT tests: it touches water at any of its five
     *  samples, or a deck polygon's bbox touches it (a deck edge may cut through
     *  it). Cell-scale answers are trusted everywhere else. */
    const fine = reuse?.fine ?? new Uint8Array(N);
    // Bit 1: roadway/bridge; bit 2: footway/shoulder. Kept separate from cost:
    // lowering a cell's cost must never turn a sidewalk into a horse route.
    const network = reuse?.network ?? new Uint8Array(N);
    const e0 = b.e0;
    const n0 = b.n0;
    // T-3691: what a layer outside the registry lays within these bounds (1871's context city:
    // its buildings, which the walker meets, its streets and its plank walks and crossings).
    const ex = buildExtra(b);
    const records = ex ? [...(streets?.records ?? []), ...ex.streets] : (streets?.records ?? []);
    const allFootprints = ex ? footprints.concat(ex.footprints) : footprints;
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
      deckBoxes.push({ ...d, ...bb });
      const s = span(bb, 0);
      for (let j = s.j0; j <= s.j1; j++) {
        const n = cN(j);
        for (let i = s.i0; i <= s.i1; i++) {
          const e = cE(i);
          const k = j * cols + i;
          fine[k] = 1;
          if (!inside(e, n, d.pts)) continue;
          if (!String(d.id).includes('__footway') && !String(d.id).includes('wharf')) network[k] |= 3;
          if (surfaceAt) {
            hgt[k] = surfaceAt(e, n);
          } else if (cls[k] === CLS_BLOCKED) {
            hgt[k] = deckHeightAt(d, e, n); // over water: the sampled deck wins
          } else {
            hgt[k] = Math.max(hgt[k], deckHeightAt(d, e, n));
          }
          if (cls[k] === CLS_BLOCKED) cls[k] = CLS_DECK;
          else lower(k, CLS_DECK);
        }
      }
    }

    // 3. Streets. Corridor first (the platted right-of-way around `path`), then
    //    the worn track (around the drawn line, or the plat when none is drawn)
    //    which is cheaper and so wins where they overlap.
    const paint = (line, half, c, mask = 0) => {
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
            if (segDist(cE(i), n, ax, ay, bx, by) <= half) {
              lower(j * cols + i, c);
              if (c === CLS_CROSSING && cls[j * cols + i] !== CLS_BLOCKED) cls[j * cols + i] = c;
              network[j * cols + i] |= mask;
            }
          }
        }
      }
    };
    for (const r of records) paint(r.path, (r.corridor_width_m ?? 24.384) * 0.5, CLS_CORRIDOR, 2);
    for (const r of records) paint(r.drawn ?? r.path, (r.track_width_m ?? 6) * 0.5, CLS_TRACK, 1);
    const paintPolygon = (pts, c, mask) => {
      if (!pts?.length) return;
      const s = span(bboxOf(pts), 0);
      for (let j = s.j0; j <= s.j1; j++) for (let i = s.i0; i <= s.i1; i++) {
        if (!inside(cE(i), cN(j), pts)) continue;
        const k = j * cols + i;
        if (cls[k] !== CLS_BLOCKED) cls[k] = c;
        network[k] |= mask;
      }
    };
    for (const r of streetGrid?.carriageways ?? []) for (const q of r.quads_local_m ?? []) paintPolygon(q, CLS_TRACK, 1);
    for (const f of streetGrid?.faces ?? []) for (const q of f.bands?.walk ?? []) paintPolygon(q, CLS_WALK, 2);
    // Join sidewalk ends at intersections, including the short curb/parkway
    // gaps. These are navigation crossings, not new historical paving claims.
    const ends = (streetGrid?.faces ?? []).flatMap(f => (f.bands?.walk ?? []).flatMap(q => {
      const a = [(q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2];
      const b = [(q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2];
      return [{ p: a, other: b, face: f.id }, { p: b, other: a, face: f.id }];
    }));
    for (let i = 0; i < ends.length; i++) for (let j = i + 1; j < ends.length; j++) {
      const a = ends[i], b = ends[j], d = Math.hypot(a.p[0] - b.p[0], a.p[1] - b.p[1]);
      if (a.face === b.face || d < 0.1 || d > 26) continue;
      const len = Math.hypot(a.other[0] - a.p[0], a.other[1] - a.p[1]);
      const along = Math.abs(((b.p[0] - a.p[0]) * (a.other[0] - a.p[0])
        + (b.p[1] - a.p[1]) * (a.other[1] - a.p[1])) / (d * len));
      if (along < 0.15 || along > 0.98) paint([a.p, b.p], 0.8, CLS_CORRIDOR, 2);
    }
    for (const w of ex ? walks.concat(ex.walks) : walks) paint(w.centreline_local_enu_m, (w.width_m ?? 1.22) / 2,
      w.kind === 'board_crossing' ? CLS_CROSSING : CLS_WALK, 2);

    // 4. Footprints, inflated by the capsule radius plus a margin so a planned
    //    point never sits where pushOut() would immediately move it. Per
    //    polygon over its own bbox — never every polygon per cell.
    // Cover the whole cell, not only its centre: a thin wall or rotated corner
    // between centres must not disappear from the planner's blocked mask.
    const R = radius + inflate + cell * Math.SQRT1_2;
    for (const fp of allFootprints) {
      if (!(fp?.pts?.length >= 3)) continue;
      // T-3405: what the walker meets is what the planner refuses (walker.js pushOut).
      // A parade is ground; an enclosure (a fort's stockade, fort-gates.js) is its walls,
      // not its plan, and a gateway's span is planned as open: a walking ride opens a
      // shut gate as it comes to it (travel.js), the way a visitor would. The leaves of
      // an open gate stand out from their jambs and are walls like any other.
      if (fp.ground) continue;
      if (Array.isArray(fp.walls)) {
        for (const w of fp.walls) {
          if (w.span) continue;
          const r = R + (w.half ?? 0);
          const s = span(bboxOf([w.a, w.b]), r);
          for (let j = s.j0; j <= s.j1; j++) {
            const n = cN(j);
            for (let i = s.i0; i <= s.i1; i++) {
              const e = cE(i);
              if (segDist(e, n, w.a[0], w.a[1], w.b[0], w.b[1]) < r) cls[j * cols + i] = CLS_BLOCKED;
            }
          }
        }
        continue;
      }
      const s = span(bboxOf(fp.pts), R);
      for (let j = s.j0; j <= s.j1; j++) {
        const n = cN(j);
        for (let i = s.i0; i <= s.i1; i++) {
          const e = cE(i);
          if (inside(e, n, fp.pts) || boundaryDist(e, n, fp.pts) < R) cls[j * cols + i] = CLS_BLOCKED;
        }
      }
    }
    // 4b. T-3264: a passage the walker may use (walker.js laneAt: Glessner's carriage
    //    passage) is reopened through its footprint, cell centres held the capsule's
    //    width off the passage's side walls, so a route plans what the walker walks.
    for (const fp of allFootprints) {
      for (const lane of lanesOf(fp)) {
        const s = span(bboxOf(lane.lane), 0);
        for (let j = s.j0; j <= s.j1; j++) {
          const n = cN(j);
          for (let i = s.i0; i <= s.i1; i++) {
            const e = cE(i), k = j * cols + i;
            if (fine[k] || !inLane(lane, e, n, radius + inflate)) continue;
            cls[k] = CLS_OPEN;
          }
        }
      }
    }
    // 4c. T-3405: a fort's gateway (fort-gates.js) is often no wider than the walker's
    //    capsule plus the margins step 4 adds, and the 1812 fort's runs on between its
    //    two barracks (1.89 m). So each gateway is reopened as a channel about a cell wide
    //    down its middle, GATE_LANE_M either side of its span, wherever the cell is
    //    outside every other footprint; plan() then walks a route that uses it through
    //    the gateway's middle (throughGates), where the capsule clears both jambs.
    for (const fp of allFootprints) {
      for (const w of Array.isArray(fp.walls) ? fp.walls : []) {
        if (!w.span) continue;
        const lane = gateLine(w);
        if (!lane) continue;
        const box = bboxOf(lane.lane);
        const near = allFootprints.filter(f => {
          if (f.ground) return false;
          const b = bboxOf(f.pts);
          return b.e1 >= box.e0 && b.e0 <= box.e1 && b.n1 >= box.n0 && b.n0 <= box.n1;
        });
        const s = span(box, 0);
        for (let j = s.j0; j <= s.j1; j++) {
          const n = cN(j);
          for (let i = s.i0; i <= s.i1; i++) {
            const e = cE(i), k = j * cols + i;
            if (fine[k] || cls[k] !== CLS_BLOCKED || !inside(e, n, lane.lane)) continue;
            // Within half a cell's diagonal of the line, so a gateway askew to the grid
            // still makes a channel joined edge to edge, not corner to corner.
            if (Math.abs((e - lane.mid[0]) * lane.u[0] + (n - lane.mid[1]) * lane.u[1]) > cell * Math.SQRT1_2 + 1e-6) continue;
            // Never inside a building, nor inside a wall's own thickness.
            if (near.some(f => Array.isArray(f.walls)
              ? f.walls.some(x => !x.span && segDist(e, n, x.a[0], x.a[1], x.b[0], x.b[1]) < (x.half ?? 0))
              : inside(e, n, f.pts))) continue;
            cls[k] = CLS_OPEN;
          }
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
      cols, rows, N, e0, n0, cls, hgt, fine, network, deckBoxes, surf, waterOf,
      // Search scratch, allocated once. `seen`/`done` are generation stamps so
      // a plan never clears 400k entries before it starts.
      g: reuse?.g ?? new Float32Array(N), parent: reuse?.parent ?? new Int32Array(N),
      seen: reuse?.seen ?? new Uint32Array(N), done: reuse?.done ?? new Uint32Array(N), gen: 0,
      heap: makeHeap(),
      reach: [],   // T-3695: reach sets of plain searches that ran out (remember)
      records, ex,
    };
    if (windowed) pool = grid;
    stats.buildMs = now() - t0;
    return grid;
  }

  /** The grid, built (or, windowed, moved to the visitor) as needed. `at` is the point the
   *  caller asks about: the first window is built round it when there is no visitor to follow,
   *  and with `pin` (a building's stand or front, asked for by Go to) the window goes to it. */
  function ensure(at = null, pin = false) {
    measureWorld();
    if (!windowed) return grid ?? build(world);
    const ok = (q) => q && Number.isFinite(q.e) && Number.isFinite(q.n) && inWorld(q.e, q.n);
    let c = null;
    if (pin && ok(at)) {
      const m = PIN_MARGIN_M;
      if (grid && at.e >= grid.e0 + m && at.e <= grid.e0 + grid.cols * cell - m
        && at.n >= grid.n0 + m && at.n <= grid.n0 + grid.rows * cell - m) return grid;
      c = at;
    } else {
      const p = typeof focus === 'function' ? focus() : null;
      const centre = ok(p) ? p : null;
      if (grid && (!centre || holds(grid, centre))) return grid;
      c = centre ?? (ok(at) ? at : { e: (world.e0 + world.e1) / 2, n: (world.n0 + world.n1) / 2 });
    }
    const w = windowAt(c.e, c.n);
    if (grid) { stats.recentres++; fronts.clear(); stands.clear(); gateLines.clear(); }
    grid = null;
    return build(w, w);
  }

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
  function nearestCell(e, n, maxCells, want = -1, accept = null) {
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
          if (d >= bestD || (accept && !accept(centreE(i), centreN(j)))) continue;
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
  function lineOfSight(ae, an, be, bn, allowed = null) {
    const len = Math.hypot(be - ae, bn - an);
    const steps = Math.max(1, Math.ceil(len / 0.5));
    const { cls, fine, hgt } = grid;
    let k = indexAt(ae, an);
    if (k < 0 || cls[k] === CLS_BLOCKED || (allowed && !allowed(k))) return false;
    let prevH = fine[k] ? exactHeight(ae, an) : hgt[k];
    if (prevH === null) return false;
    for (let s = 1; s <= steps; s++) {
      const t = s / steps;
      const e = ae + (be - ae) * t, n = an + (bn - an) * t;
      k = indexAt(e, n);
      if (k < 0 || cls[k] === CLS_BLOCKED || (allowed && !allowed(k))) return false;
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
      if (!inside(e, n, d.pts)) continue;
      const y = deckHeightAt(d, e, n);
      if (typeof y === 'number' && (deckY === null || y > deckY)) deckY = y;
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

  /**
   * Search from cell `s` to cell `t`. Returns the cell index list or null.
   * T-3695: `limit` stops it after that many expansions; `searched` then says why a null
   * came back: 'limit', or 'exhausted' (every cell it may reach was expanded, which a
   * plain search records as a reach set, below), or 'found'.
   */
  function search(s, t, { allowed = null, cost = k => COST[grid.cls[k]], stopWhen = null, reverse = false, limit = Infinity } = {}) {
    const { cols, rows, cls, hgt, fine, g, parent, seen, done, heap } = grid;
    const gen = ++grid.gen;
    const plain = !allowed && !stopWhen;
    const kept = plain && limit < Infinity ? [] : null;   // a probe's few cells, kept as it goes
    const gi = t % cols, gj = (t / cols) | 0;
    const heuristic = (i, j) => stopWhen ? 0 : octile(i, j, gi, gj);
    heap.clear();
    g[s] = 0; parent[s] = -1; seen[s] = gen;
    heap.push(heuristic(s % cols, (s / cols) | 0), s);
    let expanded = 0, reached = false;
    searched = 'exhausted';

    while (heap.size) {
      if (expanded >= limit) { searched = 'limit'; break; }
      const cur = heap.pop();
      if (done[cur] === gen) continue;
      done[cur] = gen;
      expanded++;
      kept?.push(cur);
      if (stopWhen ? stopWhen(cur) : cur === t) { t = cur; reached = true; searched = 'found'; break; }

      const ci = cur % cols, cj = (cur / cols) | 0;
      const hc = hgt[cur];
      const gc = g[cur];
      const costC = cost(cur);
      for (let d = 0; d < 8; d++) {
        const di = DIRS[d][0], dj = DIRS[d][1];
        const ni = ci + di, nj = cj + dj;
        if (ni < 0 || nj < 0 || ni >= cols || nj >= rows) continue;
        const nb = nj * cols + ni;
        const c = cls[nb];
        if (c === CLS_BLOCKED || done[nb] === gen || (allowed && !allowed(nb))) continue;
        // No corner cutting: a diagonal may not squeeze past a blocked
        // orthogonal neighbour — the capsule would clip the wall.
        if (d >= 4 && (cls[cj * cols + ni] === CLS_BLOCKED || cls[nj * cols + ci] === CLS_BLOCKED)) continue;
        if (d >= 4 && allowed && (!allowed(cj * cols + ni) || !allowed(nj * cols + ci))) continue;
        // The step rule: up is limited, down is free.
        if ((reverse ? hc - hgt[nb] : hgt[nb] - hc) > stepUp) continue;
        // A move that touches a deck edge or the water's edge is walked at
        // the exact points between the two centres, not judged by them.
        if ((fine[cur] | fine[nb])
            && !(reverse ? lineOfSight(centreE(ni), centreN(nj), centreE(ci), centreN(cj))
              : lineOfSight(centreE(ci), centreN(cj), centreE(ni), centreN(nj)))) continue;
        const ng = gc + DIRS[d][2] * cell * 0.5 * (costC + cost(nb));
        if (seen[nb] === gen && ng >= g[nb]) continue;
        seen[nb] = gen;
        g[nb] = ng;
        parent[nb] = cur;
        heap.push(ng + heuristic(ni, nj), nb);
      }
    }
    stats.lastExpanded = expanded;
    if (!reached && searched === 'exhausted' && plain) remember(s, reverse, kept, gen, expanded);
    if (done[t] !== gen || (stopWhen && !stopWhen(t))) return null;
    const out = [];
    for (let k = t; k !== -1; k = parent[k]) out.push(k);
    out.reverse();
    return out;
  }

  // ------------------------------------------------- what cannot be reached (T-3695)

  /**
   * A plain search that runs out of cells has expanded every cell its start can walk to
   * (forward), or every cell that can walk to it (reverse): a reach set. Kept, it answers
   * later plans at once, exactly: with F the cells some seed reaches, a start in F cannot
   * reach a goal outside F (else the seed would, through it); with T the cells that reach a
   * seed, a start outside T cannot reach a goal in T. In 1812 two people's rounds asked for
   * a doorstep in a closed pocket of the fort over and over, every half second: each ask
   * expanded the 5.8 million cells of the town before giving up (2.5 s), so once the route
   * grid was built (opening the Jaunts list prices every card by route) frames took
   * seconds. `unreachable` is a lookup; nothing it refuses was ever found by a search.
   * Small sets are kept as the cells themselves, large ones as a bitset; a few of each.
   */
  let searched = 'found';
  const REACH_SMALL = 24, REACH_LARGE = 4, REACH_SMALL_CELLS = 65536;
  function remember(seed, reverse, kept, gen, expanded) {
    const sets = grid.reach;
    let has;
    if (kept && kept.length <= REACH_SMALL_CELLS) {
      const cells = new Set(kept);
      has = (k) => cells.has(k);
    } else {
      const { N, done } = grid;
      const bits = new Uint8Array((N + 7) >> 3);
      for (let k = 0; k < N; k++) if (done[k] === gen) bits[k >> 3] |= 1 << (k & 7);
      has = (k) => (bits[k >> 3] & (1 << (k & 7))) !== 0;
    }
    const entry = { reverse, has, large: !(kept && kept.length <= REACH_SMALL_CELLS), cells: expanded };
    const same = sets.filter((x) => x.large === entry.large);
    if (same.length >= (entry.large ? REACH_LARGE : REACH_SMALL)) sets.splice(sets.indexOf(same[0]), 1);
    sets.push(entry);
    stats.reachSets = sets.length;
  }
  function unreachable(a, b) {
    for (const x of grid.reach) {
      if (x.reverse ? (x.has(b) && !x.has(a)) : (x.has(a) && !x.has(b))) return true;
    }
    return false;
  }
  /** Cells a goal-side probe expands before the full search is left to decide. */
  const PROBE_CELLS = 4096;

  /**
   * Resolve a metre point to the cell the search should use: its own cell when
   * free, else the nearest free cell within `snapCells` rings (a visitor may be
   * standing against a wall; a footprint centre is blocked by definition).
   * Returns { k, e, n, snapped } or null when nothing free is near.
   */
  function anchor(p, snapCells = 4, reverse = false) {
    const k = indexAt(p.e, p.n);
    if (k >= 0 && grid.cls[k] !== CLS_BLOCKED) return { k, e: p.e, n: p.n, snapped: false };
    // T-3691: off a window but in the world is ground the planner has not looked at: no plan
    // (a straight line from the window's edge would cross whatever stands there).
    if (k < 0 && windowed && inWorld(p.e, p.n)) return null;
    // Outside the grid: clamp toward the grid before searching.
    const e = Math.min(grid.e0 + grid.cols * cell - cell * 0.5, Math.max(grid.e0 + cell * 0.5, p.e));
    const n = Math.min(grid.n0 + grid.rows * cell - cell * 0.5, Math.max(grid.n0 + cell * 0.5, p.n));
    const nk = nearestCell(e, n, snapCells, -1, (ce, cn) => reverse
      ? clearSegment(ce, cn, p.e, p.n) : clearSegment(p.e, p.n, ce, cn));
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
  function pull(pts, allowed = null) {
    if (pts.length <= 2) return pts;
    const out = [pts[0]];
    let a = 0;
    while (a < pts.length - 1) {
      const c = pts[a].c;
      let end = a;
      while (end + 1 < pts.length && pts[end + 1].c === c) end++;
      // Greedy forward: extend while the straight line stays walkable.
      let k = a + 1;
      // Matching endpoint classes did not previously constrain the intervening
      // cells: an L-shaped street could be pulled straight across its block.
      while (k < end && lineOfSight(pts[a].e, pts[a].n, pts[k + 1].e, pts[k + 1].n,
        i => grid.cls[i] === c && (!allowed || allowed(i)))) k++;
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
  /**
   * T-3405: the line a route takes through a gateway, as a gateLane(): the offset along
   * the span whose line, out either side until it is in the open, stands furthest from
   * every other footprint and wall (the 1835 south gate's west half is behind the guard
   * house's corner, and the way on runs between it and the store house). Null when no
   * line clears the capsule; cached per span.
   */
  const gateLines = new Map();
  function gateLine(w) {
    if (gateLines.has(w)) return gateLines.get(w);
    const half = Math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]) / 2;
    const reach = GATE_APPROACH_M + 0.5;
    const probe = gateLane(w);
    const box = bboxOf(probe.lane);
    const near = footprints.filter(f => {
      if (f.ground) return false;
      const b = bboxOf(f.pts);
      return b.e1 + 2 >= box.e0 && b.e0 - 2 <= box.e1 && b.n1 + 2 >= box.n0 && b.n0 - 2 <= box.n1;
    });
    const clearance = (e, n) => {
      let d = Infinity;
      for (const f of near) {
        if (Array.isArray(f.walls)) {
          for (const x of f.walls) if (!x.span && !(x.gate && x.blocks)) d = Math.min(d, segDist(e, n, x.a[0], x.a[1], x.b[0], x.b[1]) - (x.half ?? 0));
        } else d = Math.min(d, inside(e, n, f.pts) ? -1 : boundaryDist(e, n, f.pts));
      }
      return d;
    };
    let best = null, score = -Infinity;
    for (let o = -half + radius; o <= half - radius + 1e-9; o += 0.05) {
      const lane = gateLane(w, o);
      // Out from the span both ways, until the line is in the open (or the lane ends):
      // through a second row of pickets, or a passage between buildings, it must clear too.
      let worst = Infinity;
      for (const side of [1, -1]) {
        for (let t = 0; t <= GATE_LANE_M + 1e-9; t += 0.25) {
          const c = clearance(lane.mid[0] + lane.normal[0] * t * side, lane.mid[1] + lane.normal[1] * t * side);
          worst = Math.min(worst, c);
          if (c > OPEN_CLEAR_M && t > reach) break;
        }
      }
      // Ties go to the middle: the same clearance nearer the centre is the better line.
      if (worst > score + 0.02 || (Math.abs(worst - score) <= 0.02 && Math.abs(o) < Math.abs(best?.o ?? Infinity))) {
        score = Math.max(score, worst); best = { o, lane };
      }
    }
    const lane = best && score >= radius ? best.lane : null;
    gateLines.set(w, lane);
    return lane;
  }

  function plan(from, to, { mode = null } = {}) {
    if (![from?.e, from?.n, to?.e, to?.n].every(Number.isFinite)) return null;
    // T-3691: the visitor's own walk (it starts where they stand) may move the window to hold
    // both its ends; anyone else's plan is made in the window the visitor keeps.
    const me = windowed && typeof focus === 'function' ? focus() : null;
    if (!(me && Math.hypot(from.e - me.e, from.n - me.n) < 5 && cover(from, to))) ensure(from);
    const t0 = now();
    stats.plans++;
    const a = anchor(from);
    const b = anchor(to, 4, true);
    if (!a || !b) { stats.lastPlanMs = now() - t0; return null; }
    if (mode === 'run') mode = 'walk'; // running is on foot: the walker's network (T-2651)
    // T-3695: a goal a kept reach set rules out, or one in a small closed pocket (a look back
    // from it runs out of cells before PROBE_CELLS), is refused before any long search. Every
    // route of any mode is a walk the plain search allows, so the refusal holds for them all.
    if (a.k !== b.k) {
      if (unreachable(a.k, b.k)) { stats.refused = (stats.refused ?? 0) + 1; stats.lastPlanMs = now() - t0; return null; }
      if (!search(b.k, a.k, { reverse: true, limit: PROBE_CELLS }) && searched === 'exhausted') {
        stats.refused = (stats.refused ?? 0) + 1; stats.lastPlanMs = now() - t0; return null;
      }
    }

    let cells;
    const mask = mode === 'walk' ? 3 : 1;
    const onStreet = k => !!(grid.network[k] & mask);
    const hasStreets = streetRecords().length + (streetGrid?.carriageways?.length ?? 0) > 0;
    if (mode && hasStreets) {
      // Three legs: collision-safe access, a street-only journey, then access
      // to the requested destination. The backwards search respects step-up
      // in the direction the final approach will actually be walked.
      const preferred = k => mode === 'walk' ? !!(grid.network[k] & 2) : onStreet(k);
      const enter = search(a.k, a.k, { stopWhen: preferred, cost: () => 1 });
      const leave = search(b.k, b.k, { stopWhen: preferred, cost: () => 1, reverse: true });
      if (!enter || !leave) return null;
      // T-3264: two points off the network that are nearer each other than the street
      // is to them (two stands in one courtyard) are walked between directly: out to
      // the sidewalk and back in by the same gate is not a route. Tried only when the
      // straight line is shorter than the two access legs, so a ride between houses
      // that stand at their walks still keeps to the street.
      const access = (enter.length - 1) + (leave.length - 1);
      const straight = Math.hypot(b.e - a.e, b.n - a.n);
      const onFoot = mode === 'walk';
      if ((enter.length > 1 && leave.length > 1 && straight < access * cell) || (onFoot && straight < DIRECT_TRY_M)) {
        const direct = search(a.k, b.k);
        // T-3691 (the owner, 2026-11-21: "the default walk should follow sidewalks etc ...
        // unless possible to walk straight"): a way across the yards near as short as the
        // straight line is walked, not out to the walk and round the block.
        if (direct && (direct.length - 1 <= access
          || (onFoot && (direct.length - 1) * cell <= DIRECT_STRAIGHT_RATIO * straight + cell))) cells = direct;
      }
      if (!cells) {
        const middle = search(enter.at(-1), leave.at(-1), {
          allowed: onStreet,
          cost: k => mode === 'walk'
            ? (grid.cls[k] === CLS_WALK || grid.cls[k] === CLS_CROSSING ? 0.35 : grid.cls[k] === CLS_TRACK ? 8 : 1)
            : 0.35,
        });
        if (!middle) return null;
        cells = [...enter, ...middle.slice(1), ...leave.reverse().slice(1)];
      }
    }
    else if (a.k === b.k) cells = [a.k];
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
    if (!clearSegment(from.e, from.n, centreE(a.k % cols), centreN((a.k / cols) | 0))) return null;
    for (let i = 0; i < cells.length; i++) {
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
    const walked = throughGates(points, footprints.flatMap(f => Array.isArray(f.walls) ? f.walls.filter(w => w.span) : []), gateLine);
    let length = 0;
    for (let i = 1; i < walked.length; i++) {
      length += Math.hypot(walked[i][0] - walked[i - 1][0], walked[i][1] - walked[i - 1][1]);
    }
    stats.lastPlanMs = now() - t0;
    return { points: walked, length_m: length };
  }

  /** T-3264: the passages of a footprint that clear `passageNeed` (walker.js laneAt). */
  function lanesOf(fp) {
    return (fp?.passages ?? []).filter(l => l.clear >= passageNeed && l.lane?.length >= 3);
  }
  /** Inside a passage's lane and at least `clear` metres off each of its side walls. */
  function inLane(lane, e, n, clear) {
    return inside(e, n, lane.lane)
      && lane.walls.every(([[ax, ay], [bx, by]]) => segDist(e, n, ax, ay, bx, by) >= clear);
  }

  /** Exact capsule check for the short connection from an arbitrary start to
   * the grid, and for the controller's next step. No snapping across a wall. */
  function clearSegment(ae, an, be, bn) {
    ensure({ e: ae, n: an });
    const near = footprintsIn(Math.min(ae, be), Math.max(ae, be), Math.min(an, bn), Math.max(an, bn), radius);
    const steps = Math.max(1, Math.ceil(Math.hypot(be - ae, bn - an) / 0.2));
    let prev = exactHeight(ae, an);
    if (prev === null) return false;
    for (let i = 0; i <= steps; i++) {
      const e = ae + (be - ae) * i / steps, n = an + (bn - an) * i / steps;
      if (near.some(f => !f.ground && (Array.isArray(f.walls)
        // T-3405: an enclosure blocks at its walls, its gateways open (see build()).
        ? f.walls.some(w => !w.span && segDist(e, n, w.a[0], w.a[1], w.b[0], w.b[1]) < radius + (w.half ?? 0))
        : (inside(e, n, f.pts) || boundaryDist(e, n, f.pts) < radius)
          && !lanesOf(f).some(l => inLane(l, e, n, radius))))) return false;
      const h = exactHeight(e, n);
      if (h === null || h - prev > stepUp) return false;
      prev = h;
    }
    return true;
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
    ensure(centre, true);
    const track = nearestCell(centre.e, centre.n, Math.ceil(150 / cell), CLS_TRACK);
    if (track < 0) return 200 * DEG;
    return Math.atan2(centreE(track % grid.cols) - centre.e, centreN((track / grid.cols) | 0) - centre.n);
  }

  function frontage(id, centre) {
    const key = `${id}:${centre.e}:${centre.n}`;
    if (fronts.has(key)) return fronts.get(key);
    ensure(centre, true);
    // A corner house fronts its addressed parcel's street, which need not be
    // the closest street to its centroid (Glessner's long side is on 18th).
    const parcel = streetGrid?.parcels?.find(p => inside(centre.e, centre.n, p.polygon_local_m));
    const face = streetGrid?.faces?.find(f => f.id === parcel?.street_face);
    let road = null, roadDistance = Infinity;
    for (const r of streetRecords()) for (let i = 1; i < r.path.length; i++) {
      const d = segDist(centre.e, centre.n, ...r.path[i - 1], ...r.path[i]);
      if (d < roadDistance) { road = r; roadDistance = d; }
    }
    let bearing = frontBearing(centre);
    if (face) {
      const line = face.street_line_local_m;
      const a = line[0], b = line.at(-1);
      const de = b[0] - a[0], dn = b[1] - a[1], len = Math.hypot(de, dn);
      let e = -dn / len, n = de / len;
      if ((a[0] - centre.e) * e + (a[1] - centre.n) * n < 0) { e = -e; n = -n; }
      bearing = Math.atan2(e, n);
    }
    const normal = { e: Math.sin(bearing), n: Math.cos(bearing) };
    const fp = footprints.find(f => f.id === id);
    let depth = 0, lo = Infinity, hi = -Infinity;
    for (const [e, n] of fp?.pts ?? []) {
      depth = Math.max(depth, (e - centre.e) * normal.e + (n - centre.n) * normal.n);
      const along = (e - centre.e) * normal.n - (n - centre.n) * normal.e;
      lo = Math.min(lo, along); hi = Math.max(hi, along);
    }
    const mid = Number.isFinite(lo) ? (lo + hi) / 2 : 0;
    const result = { bearing, street: parcel?.street ?? road?.id ?? null, width: Number.isFinite(lo) ? hi - lo : 12,
      e: centre.e + normal.e * depth + normal.n * mid,
      n: centre.n + normal.n * depth - normal.e * mid };
    fronts.set(key, result);
    return result;
  }

  /**
   * A free standing point in front of a building. `distance` (metres from the
   * centre) is the caller's when given — main.js's framing rule computes the one
   * that fits the whole building in view (T-0824) — else the old stand-off,
   * `max(8, radius + 5)`.
   */
  function standOff(id, centre, radiusM = 0, { distance = null, mode = 'walk' } = {}) {
    if (!centre || !Number.isFinite(centre.e) || !Number.isFinite(centre.n)) return centre;
    ensure(centre, true);
    const d = Number.isFinite(distance) && distance > 0 ? distance : Math.max(8, (Number(radiusM) || 0) + 5);
    const all = occluderList();
    const key = `${id}:${centre.e}:${centre.n}:${d}:${mode}`;
    if (stands.has(key)) return stands.get(key);
    const front = frontage(id, centre);
    const bearing = front.bearing;
    // Only what stands within the search box can come between a candidate and the front.
    const near = all.filter(o => Math.abs(o.e - front.e) < 110 && Math.abs(o.n - front.n) < 110);
    // Look from the actual street, never a radius that happens to land on a
    // neighbouring lawn. Prefer the opposite sidewalk for a full facade view.
    const mask = mode === 'horse' || mode === 'wagon' ? 1 : 2;
    const ne = Math.sin(bearing), nn = Math.cos(bearing);
    const road = streetRecords().find(r => r.id === front.street);
    let best = null, score = Infinity;
    for (let j = Math.max(0, cellJ(front.n - 100)); j <= Math.min(grid.rows - 1, cellJ(front.n + 100)); j++) {
      for (let i = Math.max(0, cellI(front.e - 100)); i <= Math.min(grid.cols - 1, cellI(front.e + 100)); i++) {
        const k = j * grid.cols + i;
        if (grid.cls[k] === CLS_BLOCKED || !(grid.network[k] & mask)) continue;
        if (mask === 2 && streetGrid && grid.cls[k] !== CLS_WALK) continue;
        if (mask === 2 && (grid.cls[k] === CLS_TRACK || grid.cls[k] === CLS_CROSSING)) continue;
        const e = centreE(i), n = centreN(j), de = e - front.e, dn = n - front.n;
        const out = de * ne + dn * nn, along = Math.abs(de * nn - dn * ne);
        if (out < 3 || along > Math.max(3, out)) continue;
        // Stop at the same frontage, not at the next parallel street beyond a
        // row of houses. Visibility excludes occluding neighbours.
        if (streetGrid && front.street && !(streetGrid.faces ?? []).some(f => f.street === front.street
          && (f.bands?.walk ?? []).some(q => inside(e, n, q))) && mask === 2) continue;
        if (streetGrid && front.street && mask === 1 && !(streetGrid.carriageways ?? []).some(r => r.street === front.street
          && (r.quads_local_m ?? []).some(q => inside(e, n, q)))) continue;
        if (road) {
          const line = mask === 1 ? road.drawn ?? road.path : road.path;
          const half = (mask === 1 ? road.track_width_m ?? 6 : road.corridor_width_m ?? 24.384) / 2;
          if (!line.some((p, i) => i && segDist(e, n, ...line[i - 1], ...p) <= half)) continue;
        }
        let v = Math.abs(out - d) + along * 4 + (grid.cls[k] === CLS_WALK ? 0 : mask === 2 ? 1000 : 0);
        if (v >= score) continue;
        if (!clearView(e, n, front.e + ne * (radius + 0.1), front.n + nn * (radius + 0.1), id)) continue;
        // T-3263: a trunk or post between the eye and the front costs its share of the
        // front, and a stand it blocks badly loses to any clear one a few metres along
        // the walk — the house's own parkway trees, which every stand sees past, cost
        // only their share.
        const view = near.length ? frontView({ e, n }, front, near) : null;
        if (view) v += view.hidden * VIEW_COST + (view.near > VIEW_NEAR_BLOCKED || view.hidden > VIEW_BLOCKED ? VIEW_REFUSED : 0);
        if (v >= score) continue;
        score = v; best = { e, n, front, blocked: view?.hidden ?? 0 };
      }
    }
    if (best) { stands.set(key, best); return best; }
    // T-3691 (the owner, 2026-11-22, Pullman's Other Son at the Pullman conservatory: "one more
    // jaunt that ended in a blocked path"): a building behind another on its own lot — the palm
    // house behind the Pullman house — has no clear view from its parcel's street, and the ring
    // below stood the visitor on the house's front stoop, where the walk stopped against the
    // stone. Look from any street's walk that sees the side of it turned that way instead
    // (where the street grid draws its walks: 1904).
    const side = streetGrid && sideStand(id, centre, d, mask, all.filter(o => Math.abs(o.e - centre.e) < 110 && Math.abs(o.n - centre.n) < 110));
    if (side) { stands.set(key, side); return side; }
    // 0, +30, -30, +60, -60, … 180; the first with a clear view of the front, else the
    // first free one (T-3263).
    let free = null;
    for (let step = 0; step <= 6; step++) {
      for (const sign of (step === 0 || step === 6) ? [1] : [1, -1]) {
        const th = bearing + sign * step * 30 * DEG;
        const e = centre.e + Math.sin(th) * d;
        const n = centre.n + Math.cos(th) * d;
        const k = indexAt(e, n);
        if (k < 0 || grid.cls[k] === CLS_BLOCKED) continue;
        const view = near.length ? frontView({ e, n }, front, near) : null;
        if (!view || (view.near <= VIEW_NEAR_BLOCKED && view.hidden <= VIEW_BLOCKED)) return { e, n };
        free ??= { e, n };
      }
    }
    if (free) return free;
    const cellFree = nearestCell(centre.e, centre.n, Math.ceil(60 / cell));
    if (cellFree >= 0) return { e: centreE(cellFree % grid.cols), n: centreN((cellFree / grid.cols) | 0) };
    return { e: centre.e, n: centre.n };
  }

  /**
   * standOff's second look (T-3691): the same rule as the parcel street's (out near the
   * framing distance, little along, a clear and unshaded view), asked of every face of the
   * building — each outward edge normal of its footprint — from a public walk of ANY street
   * (a carriageway on horseback) within 100 m, seen clear of every other footprint. So the
   * Pullman palm house is seen head-on across its court from 18th Street, as J. W. Taylor
   * photographed it, not at a slant past the house. Null when no walk sees a face.
   */
  function sideStand(id, centre, d, mask, near) {
    const fp = footprints.find(f => f.id === id);
    const pts = fp?.pts ?? [];
    if (pts.length < 3) return null;
    let area = 0;
    for (let i = 0; i < pts.length; i++) {
      const [ae, an] = pts[i], [be, bn] = pts[(i + 1) % pts.length];
      area += ae * bn - be * an;
    }
    // Each face's outward bearing, from edges 2 m or longer, one per 10 degrees.
    const bearings = [];
    for (let i = 0; i < pts.length; i++) {
      const [ae, an] = pts[i], [be, bn] = pts[(i + 1) % pts.length];
      const len = Math.hypot(be - ae, bn - an);
      if (len < 2) continue;
      // Counter-clockwise (area > 0) puts the outside on the right of each edge.
      const oe = (area > 0 ? bn - an : an - bn) / len, on = (area > 0 ? ae - be : be - ae) / len;
      const b = Math.atan2(oe, on);
      if (!bearings.some(x => Math.abs(Math.atan2(Math.sin(x - b), Math.cos(x - b))) < 10 * DEG)) bearings.push(b);
    }
    const onPublic = (e, n) => (mask === 2
      ? (streetGrid?.faces ?? []).some(f => (f.bands?.walk ?? []).some(q => inside(e, n, q)))
      : (streetGrid?.carriageways ?? []).some(r => (r.quads_local_m ?? []).some(q => inside(e, n, q))));
    let best = null, score = Infinity;
    for (const bearing of bearings) {
      const ne = Math.sin(bearing), nn = Math.cos(bearing);
      let depth = -Infinity, lo = Infinity, hi = -Infinity;
      for (const [pe, pn] of pts) {
        depth = Math.max(depth, (pe - centre.e) * ne + (pn - centre.n) * nn);
        const along = (pe - centre.e) * nn - (pn - centre.n) * ne;
        lo = Math.min(lo, along); hi = Math.max(hi, along);
      }
      const mid = (lo + hi) / 2;
      const front = { bearing, street: null, width: hi - lo,
        e: centre.e + ne * depth + nn * mid, n: centre.n + nn * depth - ne * mid };
      for (let j = Math.max(0, cellJ(front.n - 100)); j <= Math.min(grid.rows - 1, cellJ(front.n + 100)); j++) {
        for (let i = Math.max(0, cellI(front.e - 100)); i <= Math.min(grid.cols - 1, cellI(front.e + 100)); i++) {
          const k = j * grid.cols + i;
          if (grid.cls[k] === CLS_BLOCKED || !(grid.network[k] & mask)) continue;
          if (mask === 2 && grid.cls[k] !== CLS_WALK) continue;
          const e = centreE(i), n = centreN(j), de = e - front.e, dn = n - front.n;
          const out = de * ne + dn * nn, along = Math.abs(de * nn - dn * ne);
          if (out < 3 || along > Math.max(3, out)) continue;
          let v = Math.abs(out - d) + along * 4;
          if (v >= score) continue;
          if (!onPublic(e, n)) continue;
          if (typeof standClear === 'function' && !standClear(e, n)) continue;
          if (!clearView(e, n, front.e + ne * (radius + 0.1), front.n + nn * (radius + 0.1), id)) continue;
          const view = near.length ? frontView({ e, n }, front, near) : null;
          if (view) v += view.hidden * VIEW_COST + (view.near > VIEW_NEAR_BLOCKED || view.hidden > VIEW_BLOCKED ? VIEW_REFUSED : 0);
          if (v >= score) continue;
          score = v; best = { e, n, front, blocked: view?.hidden ?? 0 };
        }
      }
    }
    return best;
  }

  function clearView(ae, an, be, bn, id) {
    const steps = Math.ceil(Math.hypot(be - ae, bn - an));
    return !footprints.some(f => f.id !== id && Array.from({ length: steps + 1 }, (_, i) => i / Math.max(1, steps))
      .some(t => inside(ae + (be - ae) * t, an + (bn - an) * t, f.pts)));
  }

  /** True where the planner will not put a route: footprint, water, off-grid. */
  function blockedAt(e, n) {
    ensure({ e, n });
    const k = indexAt(e, n);
    // T-3691: off a window, but in the world, the planner has not looked: as before it is built.
    if (k < 0) return !(windowed && inWorld(e, n));
    return grid.cls[k] === CLS_BLOCKED;
  }

  /** The cost class under a point, by name — a debugging aid for harnesses. */
  function classAt(e, n) {
    ensure({ e, n });
    const k = indexAt(e, n);
    if (k < 0) return 'outside';
    const c = grid.cls[k];
    return c === CLS_BLOCKED ? 'blocked' : CLASS_NAME[c];
  }

  /** The walk surface the grid sampled under a point (NaN off-grid). */
  function heightAt(e, n) {
    ensure({ e, n });
    const k = indexAt(e, n);
    return k < 0 ? NaN : grid.hgt[k];
  }

  function invalidate() { grid = null; fronts.clear(); stands.clear(); gateLines.clear(); }

  return {
    plan,
    clearSegment,
    standOff,
    frontBearing,
    frontage,
    blockedAt,
    classAt,
    heightAt,
    invalidate,
    /** T-3405 harness aid: the line a route takes through a gateway span, or null. */
    gateLine,
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
