/**
 * flora-zones.js — which community a point of ground belongs to (T-2695, the first
 * piece of T-2684's flora deal off the main thread).
 *
 * This is flora.js's zone finder, moved here unchanged: the finder, the extent
 * test, the blend band's grid and the polygon indexes it reads. It moved because a
 * spread pass now asks it on a worker as well as on the page, and the job pool's
 * module worker cannot import flora.js (three, a bare specifier). One text in one
 * module that both import, so the two answers cannot drift apart. It imports only
 * lakeshore.js and zone-blend.js, which import nothing.
 *
 * A worker cannot ask the page's terrain, so `heldGround` writes down the numbers
 * the finder reads — the heightfield's measured grid, the shore-distance fields,
 * the lake's shore line, the blend grid the page built and each community's
 * extent — and `groundZones` answers from them on the other side. It answers only
 * ON the measured grid, where the terrain's height is the grid's own bilinear
 * sample. Off it (the apron, the context coast, the fallback) a slot comes back
 * `ZONE_UNASKED` and the page asks its own finder, so no slot is ever answered
 * from a ground the page does not stand on.
 */
import { softExtentWeight, ditherHash } from './lakeshore.js';
import { blendPoint, blendBuffer, ZONE_BLEND, ZONE_BLEND_MAX_M } from './zone-blend.js';

/** A slot the worker did not answer (off the measured grid): the page asks. */
export const ZONE_UNASKED = 255;

/**
 * T-2695 — the finder's ground as plain numbers and records, for a worker. Null
 * when there is no measured grid or shore field to answer from; the page then
 * asks its own finder for every slot, as it did before.
 */
export function heldGround(zones, terrain, water, finder) {
  const hf = terrain?.heightfield;
  if (!hf?.loaded || !water?.held || !Number.isFinite(terrain.shoreY)
    || zones.length >= ZONE_UNASKED) return null;
  return {
    hf: { data: hf.data, cols: hf.cols, rows: hf.rows, cellM: hf.cellM,
      originE: hf.originE, originN: hf.originN, widthM: hf.widthM, depthM: hf.depthM },
    shoreY: terrain.shoreY,
    lakeShore: terrain.lakeShore ?? null,
    water: water.held,
    blend: finder.held,
    zones: zones.map((z) => ({ id: z.id, turf: z.turf, priority: z.priority, extent: z.extent })),
  };
}

/**
 * The other side of `heldGround`: a function from a point to its community's
 * place in the page's `zones` (1-based; 0 is no community), or `ZONE_UNASKED`
 * off the measured grid. The height is the measured grid's bilinear sample,
 * the same arithmetic as terrain.js `Heightfield.sample` inside its bounds, and
 * `flora.checkHeldZones` holds the two together on the page.
 */
export function groundZones(g) {
  const { data, cols, rows, cellM, originE, originN } = g.hf;
  const sample = (e, n) => {
    const gx = (e - originE) / cellM;
    const gy = (n - originN) / cellM;
    const x0 = Math.min(Math.floor(gx), cols - 2);
    const y0 = Math.min(Math.floor(gy), rows - 2);
    const fx = gx - x0;
    const fy = gy - y0;
    const r0 = y0 * cols;
    const r1 = r0 + cols;
    const h00 = data[r0 + x0], h10 = data[r0 + x0 + 1];
    const h01 = data[r1 + x0], h11 = data[r1 + x0 + 1];
    return (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy;
  };
  const isWater = (e, n) => sample(e, n) < g.shoreY;
  const terrain = { heightfield: { loaded: true, ...g.hf }, lakeShore: g.lakeShore,
    surfaceHeight: sample, isWater };
  const water = { distance: (e, n) => waterDistance(g.water, isWater, e, n) };
  const find = zoneFinder(g.zones, terrain, water, g.blend);
  const place = new Map(g.zones.map((z, i) => [z, i + 1]));
  return (e, n) => {
    const gx = (e - originE) / cellM;
    const gy = (n - originN) / cellM;
    if (!(gx >= 0 && gy >= 0 && gx <= cols - 1 && gy <= rows - 1)) return ZONE_UNASKED;
    return place.get(find(e, n)) ?? 0;
  };
}

/** Metres to the shore from (e, n): to the nearest water cell on land, to the
 *  nearest land cell in water, off flora.js `waterField`'s two chamfer fields. */
export function waterDistance(f, isWater, e, n) {
  const c = Math.round((e - f.e0) / f.cell);
  const r = Math.round((n - f.n0) / f.cell);
  if (c < 0 || r < 0 || c >= f.cols || r >= f.rows) return Infinity;
  const i = r * f.cols + c;
  return isWater(e, n) ? f.toLand[i] : f.toWater[i];
}

export function zoneFinder(zones, terrain, water, held = undefined) {
  // T-2125 (zone-blend.js): every extent is asked at the plant's point MOVED
  // across a wide, wandering band, so two communities meet in a margin that
  // thins over about 100 m rather than on the recorded line. Computed once per
  // question and shared by every zone it reaches; reused, never allocated.
  const q = { e: 0, n: 0, w: 0, d: 0 };
  const exact = (e, n) => {
    for (const z of zones) {
      if (matches(z.extent, e, n, terrain, water)) return z;
    }
    return null;
  };
  // Most of the ground is far from any edge, and there the moved question
  // gets the same answer as the plain one at a cost the plant layer pays
  // millions of times a deal (T-2096, T-2099). So the band is only asked for
  // where an edge is near: the plain answer on a BLEND_CELL_M grid, and every
  // cell within the band's reach of a cell answering differently is marked.
  // A patch laid over the town's own ground at a higher priority (the vacant
  // lots of T-2101) is bounded by lot lines, which were fenced and kept: it is
  // not blended either way, and it is one class with the town in the grid.
  const turf = zones.find((z) => z.turf) ?? null;
  const lots = turf ? zones.filter((z) => lotBound(z, turf)) : [];
  // T-2695: a worker is handed the grid the page built (`held`) rather than
  // building its own, which would be the boot's whole sweep again on every core.
  const grid = held !== undefined ? (held && gridFrom(held))
    : blendNearEdge(exact, terrain, turf && lots.length ? new Set(lots) : null, turf);
  const near = grid?.near ?? null;
  // THE TOWN'S MARGIN IS GRAZED (and the plant layer is not made dearer by it).
  // A prairie slot in the band beside the town's turf is handed to the turf at
  // a share that falls from TOWN_GRAZE at the recorded line to none at the band's
  // far side: the margin's prairie is thinner and shorter-cropped than the open
  // prairie, as grazed ground is, and the turf the ground paints there follows it
  // (the turf mask is this finder's own answer). A turf slot is the cheapest the
  // plant layer deals, so this keeps the band's cost at or under the hard edge's
  // (T-2096, T-2099), where a plain blend drew prairie cards over the town side.
  const gap = turf ? grid?.townGap ?? null : null;
  // A slot's answer never changes, and the plant layer re-deals the same
  // world-anchored slots every 0.6 m walked, so the answers are kept in a
  // direct-mapped cache keyed by the slot's own coordinates (T-2096). 64k
  // entries, about 1.1 MB; a collision only costs the question again.
  const CACHE = 1 << 16;
  const keyE = new Float64Array(CACHE).fill(NaN);
  const keyN = new Float64Array(CACHE);
  const val = new Uint8Array(CACHE);
  const byIndex = [null, ...zones];
  const indexOf = new Map(zones.map((z, i) => [z, i + 1]));
  const slot = (e, n) => {
    const h = Math.imul(Math.round(e * 8) | 0, 0x27d4eb2d) ^ Math.imul(Math.round(n * 8) | 0, 0x165667b1);
    return (h ^ (h >>> 15)) & (CACHE - 1);
  };
  function find(e, n) {
    const h = slot(e, n);
    if (keyE[h] === e && keyN[h] === n) return byIndex[val[h]];
    const z = answer(e, n);
    keyE[h] = e; keyN[h] = n; val[h] = z ? indexOf.get(z) : 0;
    return z;
  }
  /** T-2695: the blend grid's numbers, for `heldGround`. */
  find.held = grid?.held ?? null;
  /** T-2695: an answer a worker gave for (e, n) — `zones` place, 1-based, 0 for
   *  none — kept as if it had been asked here. The page asks its own finder only
   *  for the slots a worker could not answer in time, and those are mostly the
   *  slots the last passes already dealt: without this they would all miss. */
  find.remember = (e, n, z) => {
    const h = slot(e, n);
    keyE[h] = e; keyN[h] = n; val[h] = z;
  };
  return find;
  function answer(e, n) {
    if (near && !near(e, n)) return exact(e, n);
    for (const z of lots) {
      if (matches(z.extent, e, n, terrain, water)) return z;
    }
    blendPoint(e, n, q);
    let hit = null;
    for (const z of zones) {
      if (lots.length && lots.includes(z)) continue;
      if (matches(z.extent, e, n, terrain, water, q)) { hit = z; break; }
    }
    if (gap && hit && !hit.turf && hit.priority < turf.priority && hit.extent?.kind !== 'lake_shore') {
      const d = gap(e, n);
      if (d < ZONE_BLEND_MAX_M
        && ditherHash(e + 0.27, n - 0.41) < TOWN_GRAZE * (1 - d / ZONE_BLEND_MAX_M)) return turf;
    }
    return hit;
  }
}

/** T-2125: the share of prairie slots handed to the town's turf at its recorded
 *  edge; it falls to none at the far side of the band. */
const TOWN_GRAZE = 0.6;

/** A community whose edges this band does not blend: an elevation band, or an
 *  extent with its own soft ramp (lakeshore.js). */
function openClass(z) {
  const x = z.extent;
  return x?.kind === 'elevation_band' || x?.kind === 'lake_shore' || !!(x?.edge && x?.box);
}

/** A polygon community over the town's turf at a higher priority: a patch of
 *  the town bounded by its lot lines (T-2101's vacant lots), not blended. */
function lotBound(z, turf) {
  return !z.turf && z.extent?.kind === 'polygon' && z.priority > turf.priority;
}

/** T-2125: the grid `zoneFinder` reads to skip the band far from any edge. */
const BLEND_CELL_M = 24;
function blendNearEdge(exact, terrain, lots = null, turf = null) {
  const hf = terrain?.heightfield;
  if (!hf?.loaded || !(hf.widthM > 0 && hf.depthM > 0)) return null;
  const c = BLEND_CELL_M;
  const w = Math.ceil(hf.widthM / c) + 1;
  const h = Math.ceil(hf.depthM / c) + 1;
  const ids = new Map();
  const turfIds = new Set();
  const zone = new Uint16Array(w * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const z = exact(hf.originE + (i + 0.5) * c, hf.originN + (j + 0.5) * c);
      // The open communities are one class here: the prairies' elevation
      // bands are not blended, and the sand's soft extents ramp themselves
      // (T-1819), so the lines between them are no edge of this band's.
      const key = z ? (openClass(z) ? '~open' : lots?.has(z) ? turf.id : z.id) : '';
      if (z?.turf) turfIds.add(key);
      if (!ids.has(key)) ids.set(key, ids.size);
      zone[j * w + i] = ids.get(key);
    }
  }
  // A cell is at an edge when a neighbour answers differently; the band
  // reaches ZONE_BLEND_MAX_M plus a cell of slack either side of one.
  const edge = new Uint8Array(w * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const v = zone[j * w + i];
      if ((i + 1 < w && zone[j * w + i + 1] !== v) || (j + 1 < h && zone[(j + 1) * w + i] !== v)) {
        edge[j * w + i] = 1;
        if (i + 1 < w) edge[j * w + i + 1] = 1;
        if (j + 1 < h) edge[(j + 1) * w + i] = 1;
      }
    }
  }
  const r = Math.ceil(ZONE_BLEND_MAX_M / c) + 1;
  const row = new Uint8Array(w * h);
  for (let j = 0; j < h; j++) {
    let last = -Infinity;
    for (let i = 0; i < w; i++) { if (edge[j * w + i]) last = i; if (i - last <= r) row[j * w + i] = 1; }
    last = Infinity;
    for (let i = w - 1; i >= 0; i--) { if (edge[j * w + i]) last = i; if (last - i <= r) row[j * w + i] = 1; }
  }
  const mark = new Uint8Array(w * h);
  for (let i = 0; i < w; i++) {
    let last = -Infinity;
    for (let j = 0; j < h; j++) { if (row[j * w + i]) last = j; if (j - last <= r) mark[j * w + i] = 1; }
    last = Infinity;
    for (let j = h - 1; j >= 0; j--) { if (row[j * w + i]) last = j; if (last - j <= r) mark[j * w + i] = 1; }
  }
  // How far each cell lies from the TOWN'S edge (a turf cell beside one that is
  // not), in cells, by a two-pass chamfer, capped past the band.
  const turfOf = [...ids.keys()].map((id) => turfIds.has(id));
  const cap = r + 1;
  const dist = new Float32Array(w * h).fill(cap);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const t = turfOf[zone[j * w + i]];
      if ((i + 1 < w && turfOf[zone[j * w + i + 1]] !== t)
        || (j + 1 < h && turfOf[zone[(j + 1) * w + i]] !== t)) {
        dist[j * w + i] = 0;
        if (i + 1 < w) dist[j * w + i + 1] = 0;
        if (j + 1 < h) dist[(j + 1) * w + i] = 0;
      }
    }
  }
  const D = Math.SQRT2;
  const relax = (k, v) => { if (v < dist[k]) dist[k] = v; };
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const k = j * w + i;
      if (i > 0) relax(k, dist[k - 1] + 1);
      if (j > 0) {
        relax(k, dist[k - w] + 1);
        if (i > 0) relax(k, dist[k - w - 1] + D);
        if (i + 1 < w) relax(k, dist[k - w + 1] + D);
      }
    }
  }
  for (let j = h - 1; j >= 0; j--) {
    for (let i = w - 1; i >= 0; i--) {
      const k = j * w + i;
      if (i + 1 < w) relax(k, dist[k + 1] + 1);
      if (j + 1 < h) {
        relax(k, dist[k + w] + 1);
        if (i + 1 < w) relax(k, dist[k + w + 1] + D);
        if (i > 0) relax(k, dist[k + w - 1] + D);
      }
    }
  }
  return gridFrom({ e0: hf.originE, n0: hf.originN, c, w, h, mark, dist });
}

/** The two questions the blend grid answers, read off its numbers (T-2695: the
 *  page builds them once and a worker is handed the same numbers). */
function gridFrom(held) {
  const { e0, n0, c, w, h, mark, dist } = held;
  return {
    held,
    near: (e, n) => {
      const i = Math.floor((e - e0) / c);
      const j = Math.floor((n - n0) / c);
      if (i < 0 || j < 0 || i >= w || j >= h) return true;
      return mark[j * w + i] === 1;
    },
    /** Metres to the town's edge, bilinear between cell centres. */
    townGap: (e, n) => {
      const x = Math.min(w - 1.001, Math.max(0, (e - e0) / c - 0.5));
      const y = Math.min(h - 1.001, Math.max(0, (n - n0) / c - 0.5));
      const i = Math.floor(x);
      const j = Math.floor(y);
      const tx = x - i;
      const ty = y - j;
      const k = j * w + i;
      const a = dist[k] + (dist[k + 1] - dist[k]) * tx;
      const b = dist[k + w] + (dist[k + w + 1] - dist[k + w]) * tx;
      return (a + (b - a) * ty) * c;
    },
  };
}

/**
 * `include_polygons` — ground a community holds that its own extent rule cannot
 * reach, and the exact mirror of `exclude_polygons` below.
 *
 * It exists because one community's evidence is a PLACE and its extent is a
 * RULE, and the two stopped agreeing. `docs/research/02-flora.md` heads ZONE 3
 * "SLOUGH & SEDGE MEADOW (Public Square → Tremont House site → river at State
 * St)" — the public square named first, by name — while `z03_sedge_meadow`'s
 * committed extent is an elevation band, which can only find the square if the
 * terrain gives the square a basin, and dossier zone 15 is deferred and
 * unmodelled, so it does not. The band was not selecting against the block; it
 * could not see it. Fitting the band down to reach it would have moved the
 * community everywhere else in the box to solve one address.
 *
 * The box test still binds — a polygon outside a zone's declared box is refused
 * with everything else — and the exclusions still run last, so a hole cut in a
 * community stays a hole. Which ground this admits, and on what evidence, is a
 * claim in the zone record's own extent note, never a rule in here.
 */
export function matches(x, e, n, terrain, water, q = null) {
  if (!x) return false;
  // T-2125: `q` is where a polygon or a box is asked (zone-blend.js). The soft
  // extents below carry their own ramp and are asked at the plant's own point.
  const qe = q ? q.e : e;
  const qn = q ? q.n : n;
  // A box whose sides carry `edge` is soft (T-1819): its ramp reaches past the
  // stated line, so the hard clip would cut the ramp's outer half off.
  if (x.box && !x.edge) {
    const be = x.box.e;
    const bn = x.box.n;
    if (be && (qe < be[0] || qe > be[1])) return false;
    if (bn && (qn < bn[0] || qn > bn[1])) return false;
  }
  let ok = false;
  // THE LAKE'S SAND (T-1819): a band from the lake's edge, or a box with
  // wandering, ramped sides. lakeshore.js gives the weight the ground shader
  // blends the zone's colour by; it is dithered here against a positional draw,
  // so across a ramp a point belongs to the zone exactly as often as the ground
  // there shows its sand — the sward thins into the beach rather than stopping.
  const soft = softExtentWeight(x, e, n, terrain?.lakeShore ?? null);
  if (soft !== null) ok = soft > ditherHash(e, n);
  else switch (x.kind) {
    case 'everywhere':
      ok = true;
      break;
    case 'elevation_band': {
      // Not blended (T-2125): a band is a contour on ground with under two
      // metres of relief, so it already wanders with the swales, and blending
      // it would put the whole prairie inside an edge band.
      const y = terrain.surfaceHeight(e, n);
      ok = Array.isArray(x.elev_m) && y >= x.elev_m[0] && y <= x.elev_m[1];
      break;
    }
    case 'polygon':
      ok = Array.isArray(x.polygon) && pointInPolygon(x.polygon, qe, qn);
      break;
    case 'buffer': {
      if (x.of !== 'water') return false;
      const dist = water.distance(e, n);
      const band = x.distance_m ?? [0, 0];
      // T-2125: only a buffer that reaches far from the water spreads, and only
      // on its far side; the marsh stays at the water's edge.
      const far = band[1] + (q && band[1] >= ZONE_BLEND.buffer.from ? blendBuffer(q) : 0);
      ok = dist >= band[0] && dist <= far;
      break;
    }
    default:
      return false;
  }
  if (!ok) {
    for (const patch of ringsNear(x.include_polygons, qe, qn)) {
      if (pointInPolygon(patch, qe, qn)) { ok = true; break; }
    }
  }
  if (!ok) return false;
  for (const hole of ringsNear(x.exclude_polygons, qe, qn)) {
    if (pointInPolygon(hole, qe, qn)) return false;
  }
  return true;
}

/**
 * The rings of an extent's `include_polygons` / `exclude_polygons` list that can
 * hold (e, n), read from a bin index built once per list (T-2101). The vacant-lot
 * remnant holds 69 lot rings spread over the whole town, so walking the list ring
 * by ring put 69 box tests on every sward slot in town; a point now reads the one
 * bin it falls in. Same answer as the full walk: a ring is filed under every bin
 * its box touches. Keyed by the list's own array, which the records never mutate.
 */
const RINGS_BIN_M = 32;
const RINGS_INDEX = new WeakMap();
const NO_RINGS = [];
function ringsNear(list, e, n) {
  if (!list?.length) return NO_RINGS;
  if (list.length < 4) return list;
  let ix = RINGS_INDEX.get(list);
  if (!ix) {
    ix = new Map();
    for (const ring of list) {
      let e0 = Infinity; let e1 = -Infinity; let n0 = Infinity; let n1 = -Infinity;
      for (const [pe, pn] of ring) {
        if (pe < e0) e0 = pe; if (pe > e1) e1 = pe;
        if (pn < n0) n0 = pn; if (pn > n1) n1 = pn;
      }
      for (let i = Math.floor(e0 / RINGS_BIN_M); i <= Math.floor(e1 / RINGS_BIN_M); i++) {
        for (let j = Math.floor(n0 / RINGS_BIN_M); j <= Math.floor(n1 / RINGS_BIN_M); j++) {
          const k = ringsBin(i, j);
          if (!ix.has(k)) ix.set(k, []);
          ix.get(k).push(ring);
        }
      }
    }
    RINGS_INDEX.set(list, ix);
  }
  return ix.get(ringsBin(Math.floor(e / RINGS_BIN_M), Math.floor(n / RINGS_BIN_M))) ?? NO_RINGS;
}
/** A numeric bin key, so a lookup allocates no string. 65,536 bins a side at 32 m. */
function ringsBin(i, j) { return (i + 32768) * 65536 + (j + 32768); }

/**
 * The same even-odd test over an EDGE INDEX built once per ring (T-2091). Only an
 * edge whose northing span covers `n` can cross the ray, so each ring's edges are
 * binned by northing and a point reads one bin. The settled town's derived ring
 * has hundreds of vertices, and read edge by edge it cost about 30 us a lookup —
 * the sward asks millions per deal, and the smoke's census walks 82,000 — where the
 * index costs about 0.15 us and gives the identical answer (2.1 million points
 * compared on the committed rings, none differing). Keyed by the ring's own array,
 * which the records never mutate.
 */
const POLYGON_INDEX = new WeakMap();
function polygonIndex(pts) {
  let ix = POLYGON_INDEX.get(pts);
  if (ix) return ix;
  let e0 = Infinity; let e1 = -Infinity; let n0 = Infinity; let n1 = -Infinity;
  for (const [e, n] of pts) {
    if (e < e0) e0 = e; if (e > e1) e1 = e;
    if (n < n0) n0 = n; if (n > n1) n1 = n;
  }
  const bins = Math.max(1, Math.min(512, pts.length >> 1));
  const h = (n1 - n0) / bins || 1;
  const edges = Array.from({ length: bins }, () => []);
  const bin = (y) => Math.max(0, Math.min(bins - 1, Math.floor((y - n0) / h)));
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const edge = [pts[i][0], pts[i][1], pts[j][0], pts[j][1]];
    const b1 = bin(Math.max(pts[i][1], pts[j][1]));
    for (let b = bin(Math.min(pts[i][1], pts[j][1])); b <= b1; b++) edges[b].push(edge);
  }
  ix = { e0, e1, n0, n1, h, bins, edges };
  POLYGON_INDEX.set(pts, ix);
  return ix;
}

export function pointInPolygon(pts, e, n) {
  const ix = polygonIndex(pts);
  if (e < ix.e0 || e > ix.e1 || n < ix.n0 || n > ix.n1) return false;
  const list = ix.edges[Math.min(ix.bins - 1, Math.floor((n - ix.n0) / ix.h))];
  let inside = false;
  for (let k = 0; k < list.length; k++) {
    const [xi, yi, xj, yj] = list[k];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
