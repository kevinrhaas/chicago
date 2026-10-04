/**
 * working-bank.js — T-1771, the worked river bank: South Water's river side as
 * trodden earth and mud, a bare haul apron behind every landing, sward left in
 * the unworn patches and no tree on a dock approach.
 *
 * The owner's ask, 2026-09-30: "South Water's river work areas should be worn
 * dirt, with low docks, smaller landings and ramps between river and street;
 * grass survives mainly in unworn patches." Until this layer the bank between
 * the street and the water was the terrain's own wet prairie, with the sward,
 * the marsh and the riverbank willows standing on it right up to the decks.
 *
 * WHAT IT DRAWS AND WHERE THE NUMBERS LIVE. `data/wharves/working_bank.json`
 * states the rule and every figure — the reach, the apron, the wear, the grass
 * patches, the tones — each marked reconstructed with what bounds it. This file
 * reads that record and derives the ground AT LOAD from three things already
 * committed: the heightfield (where the water starts), the street record (where
 * South Water's worked edge runs) and the wharf layer's drawn decks (where each
 * apron leads from). So a re-traced bank or a moved street moves the worked
 * ground with it, and nothing here can go stale behind them.
 *
 * HOW. The same method T-1797's ground strip proved (ground-strip.js): a mesh
 * draped on the heightfield a few centimetres up and pulled forward in depth,
 * whose shader paints the terrain's OWN prairie (`PRAIRIE_FRAGMENT`, imported,
 * not copied) and mixes the worn earth over it by a per-vertex wear. Where the
 * wear is zero the fragment is the terrain's fragment, so the edges have no
 * seam to hide. The fine grain is the strip's grit tile; the patches of
 * surviving grass are a seeded field computed the same way here and in the
 * shader (`patchField`), so the planter is told to leave bare exactly the
 * ground the shader draws bare.
 *
 * WHAT IT DOES NOT DO. It does not regrade the land: the bank's relief is the
 * committed heightfield's, and the "ramp" between a landing and the street is
 * that ground, worn — on South Water it rises and falls by less than two
 * decimetres between a deck and the street bed (T-1812's section), so no timber
 * ramp is invented for it. It draws no vessel, cargo or figure. It is one draw
 * call, graded reconstructed at every vertex, so it disappears with the
 * reconstructed tier and the bank goes back to the terrain's sward.
 */

import * as THREE from 'three';
import {
  PRAIRIE_FRAGMENT, WORLD_POS_VERT, prairieTexture, SWARD_HEAD, swardTexture, swardUniforms,
} from './terrain.js';
import { GRIT_TILE_PX, GRIT_TILE_M, gritTilePixels } from './ground-strip-mask.js';
import { WORKED_SHARE, ridgeHeight } from './streets.js';

/** Grid spacing of the draped mesh, metres, by scene detail. Half the
 *  heightfield's 2.5 m lattice at the two upper tiers, the lattice itself on
 *  `light`, which is the floor and pays the fewest triangles. */
const MESH_STEP_M = { full: 1.25, balanced: 1.25, light: 2.5 };
/** Above the heightfield, with polygon offset for the rest — the strip's lift. */
const LIFT_M = 0.04;
/**
 * ON THE STREET THE BANK LIES UNDER THE ROAD, NOT OVER IT (T-1987). At 4 cm
 * up it stood above the road's own 2.2 cm, and the two surfaces crossed
 * along their triangles' edges: the bank won in some, the road in others, and
 * the shoulder along South Water read as rows of square teeth from the air.
 * There it is laid on the cells' ridge — which the road is draped on and the
 * baked ground stays under by 4 mm at most — 5 mm up, on each cell's upper
 * diagonal so it follows that ridge rather than sagging through it. Road over
 * bank over ground, every time, with the polygon offsets to spare.
 */
const ON_STREET_LIFT_M = 0.005;
/** How finely the reach's columns are read off the heightfield, metres. */
const COLUMN_M = 0.5;
/** The step the waterline is marched in, landward to riverward. */
const MARCH_M = 0.5;
/** `aRoad` beyond any street: far enough that no cell can interpolate it below 0. */
const ROAD_FAR_M = 1000;
/** The edge the reach's own band feathers over, metres. */
const BAND_FEATHER_M = 1.0;

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * The surviving-grass field, 0..1: patches a few metres across. THE SAME
 * EXPRESSION AS `PATCH_GLSL` BELOW — keep the two in step; the planter reads
 * this one and the shader draws the other.
 */
export function patchField(e, n) {
  const a = Math.sin(e * 0.53 + 1.7) * Math.sin(n * 0.61 + 0.4);
  const b = Math.sin(e * 0.23 - n * 0.31 + 2.9);
  const c = Math.sin(e * 1.13 + n * 0.97 + 0.6);
  return 0.5 + 0.5 * (0.5 * a + 0.3 * b + 0.2 * c);
}

const PATCH_GLSL = /* glsl */`
  float wbPatch = 0.5 + 0.5 * (
      0.5 * sin(wbEN.x * 0.53 + 1.7) * sin(wbEN.y * 0.61 + 0.4)
    + 0.3 * sin(wbEN.x * 0.23 - wbEN.y * 0.31 + 2.9)
    + 0.2 * sin(wbEN.x * 1.13 + wbEN.y * 0.97 + 0.6));
`;

/** How much grass survives at a point of the band, 0..1. */
function grassAt(e, n, apron, rule) {
  if (rule.neverOnAprons && apron >= 1) return 0;
  const g = smooth(rule.above - rule.fade / 2, rule.above + rule.fade / 2, patchField(e, n));
  return g * (1 - apron);
}

/** sRGB 0-255 → the renderer's linear working space. */
function linearTone(rgb) {
  return new THREE.Color().setRGB(...rgb.map((v) => v / 255), THREE.SRGBColorSpace);
}

/** A polyline's northing at easting `e`, and the segment's slope there. Null
 *  outside it. The South Water line runs west to east without turning back. */
function lineAt(pts, e) {
  for (let i = 0; i + 1 < pts.length; i += 1) {
    const [a, b] = [pts[i], pts[i + 1]];
    const lo = Math.min(a[0], b[0]);
    const hi = Math.max(a[0], b[0]);
    if (e < lo || e > hi || hi === lo) continue;
    const t = (e - a[0]) / (b[0] - a[0]);
    return { n: a[1] + t * (b[1] - a[1]), cos: Math.abs(b[0] - a[0]) / Math.hypot(b[0] - a[0], b[1] - a[1]) };
  }
  return null;
}

/**
 * The reach as a table of columns: for each easting, where the worn band
 * starts (inside the street's worked edge) and where the river does. Read off
 * the heightfield once, at load.
 */
function readReach(reach, street, terrain, problems) {
  const pts = street?.drawn_track_local_enu_m ?? street?.path_local_enu_m;
  if (!Array.isArray(pts) || pts.length < 2) {
    problems.push(`working bank: ${reach.id} names street ${reach.street}, which is not drawn `
      + '— the reach is not laid');
    return null;
  }
  const share = WORKED_SHARE[street.traffic] ?? WORKED_SHARE.principal;
  const half = (street.corridor_width_m ?? 24.384) * share / 2;
  const side = reach.side === 'south' ? -1 : 1;
  const [e0, e1] = reach.e_m;
  const taper = reach.taper_m ?? 0;
  const from = Math.floor((e0 - taper) / COLUMN_M) * COLUMN_M;
  const cols = Math.ceil((e1 - from) / COLUMN_M) + 1;
  const lo = new Float32Array(cols).fill(NaN);
  const hi = new Float32Array(cols).fill(NaN);
  let laid = 0;
  for (let i = 0; i < cols; i += 1) {
    const e = from + i * COLUMN_M;
    const at = lineAt(pts, e);
    if (!at) continue;
    const start = at.n + side * (half + (reach.from_worked_edge_m ?? 0)) / Math.max(at.cos, 0.2);
    const edge = at.n + side * half / Math.max(at.cos, 0.2);
    // Where the street's own line or edge stands in water (a slip), the bank is
    // not this street's to wear.
    if (!(terrain.surfaceHeight(e, at.n) > 0) || !(terrain.surfaceHeight(e, edge) > 0)) continue;
    let n = edge;
    let reached = false;
    for (let k = 0; k * MARCH_M <= reach.max_depth_m; k += 1) {
      n = edge + side * k * MARCH_M;
      if (!(terrain.surfaceHeight(e, n) > 0)) { reached = true; break; }
    }
    if (!reached) continue;
    lo[i] = start;
    hi[i] = n;
    laid += 1;
  }
  if (!laid) {
    problems.push(`working bank: ${reach.id} found no dry bank between ${reach.street} and the water`);
    return null;
  }
  let nMin = Infinity;
  let nMax = -Infinity;
  for (let i = 0; i < cols; i += 1) {
    if (Number.isNaN(lo[i])) continue;
    nMin = Math.min(nMin, lo[i], hi[i]);
    nMax = Math.max(nMax, lo[i], hi[i]);
  }
  return {
    id: reach.id, street: reach.street, side, from, cols, lo, hi, e0, e1, taper, wear: reach.wear,
    half, track: Math.min(half, (street.track_width_m ?? 6) / 2), pts, laid,
    box: { e: [from, from + (cols - 1) * COLUMN_M], n: [nMin - 2, nMax + 2] },
  };
}

/** How far into the river the worked bank keeps its foot clear of emergent
 *  reeds, metres: the planters' answer only — the shader draws nothing there. */
const WATER_CLEAR_M = 4.0;

function reachWear(r, e, n, wet = false) {
  const i = Math.round((e - r.from) / COLUMN_M);
  if (i < 0 || i >= r.cols) return 0;
  const lo = r.lo[i];
  const hi = r.hi[i];
  if (Number.isNaN(lo)) return 0;
  const s = r.side;
  // Distance into the band from its landward start, and to the water.
  const into = (n - lo) * s;
  const toWater = (hi - n) * s;
  if (into < -BAND_FEATHER_M) return 0;
  if (wet && toWater < 0) {
    // In the river at the worked bank's foot: no reed stands where every
    // barrel landed was waded or poled ashore.
    return toWater >= -WATER_CLEAR_M ? r.wear : 0;
  }
  if (toWater < -BAND_FEATHER_M) return 0;
  const along = r.taper > 0
    ? smooth(r.e0 - r.taper, r.e0, e) * (1 - smooth(r.e1 - r.taper, r.e1, e))
    : 1;
  return r.wear * along * smooth(-BAND_FEATHER_M, 0, into) * smooth(-BAND_FEATHER_M, 0.5, toWater);
}

/**
 * One landing's haul apron in the deck's own frame: `u` along the heel, `v`
 * landward from it. On a street-backed bank it runs back to the street's
 * worked edge; elsewhere the record's landward reach.
 */
function readApron(w, rule, reach) {
  const q = w.deck_quad_local_enu_m;
  if (!Array.isArray(q) || q.length !== 4) return null;
  const [heelL, heelR, , faceL] = q;
  const mid = [(heelL[0] + heelR[0]) / 2, (heelL[1] + heelR[1]) / 2];
  const len = Math.hypot(heelR[0] - heelL[0], heelR[1] - heelL[1]);
  const ue = (heelR[0] - heelL[0]) / (len || 1);
  const un = (heelR[1] - heelL[1]) / (len || 1);
  const out = Math.hypot(faceL[0] - heelL[0], faceL[1] - heelL[1]) || 1;
  // Landward is the reverse of the deck's own outward direction.
  const le = -(faceL[0] - heelL[0]) / out;
  const ln = -(faceL[1] - heelL[1]) / out;
  let L = rule.landward;
  let toStreet = false;
  if (reach) {
    // March landward until the point is inside the street's worked width; a
    // dock whose street is out of reach keeps the record's landward figure.
    for (let v = 0; v <= 60; v += 0.5) {
      const e = mid[0] + le * v;
      const n = mid[1] + ln * v;
      const at = lineAt(reach.pts, e);
      if (at && Math.abs(n - at.n) * at.cos <= reach.half) { L = v; toStreet = true; break; }
    }
  }
  const halfLen = len / 2;
  const span = halfLen + rule.widen + rule.feather;
  // Two boxes: the planters' reaches under the deck and off its face, the
  // mesh's only as far as the dry ground the shader draws.
  const boxFrom = (b0) => {
    const corners = [];
    for (const [a, b] of [[-span, b0], [span, b0], [span, L + rule.feather], [-span, L + rule.feather]]) {
      corners.push([mid[0] + ue * a + le * b, mid[1] + un * a + ln * b]);
    }
    const es = corners.map((c) => c[0]);
    const ns = corners.map((c) => c[1]);
    return { e: [Math.min(...es), Math.max(...es)], n: [Math.min(...ns), Math.max(...ns)] };
  };
  return {
    id: w.structure_id, mid, ue, un, le, ln, L, halfLen, toStreet, out,
    box: boxFrom(-(out + WATER_CLEAR_M)), meshBox: boxFrom(-1),
  };
}

function apronWear(a, rule, e, n, wet = false) {
  if (e < a.box.e[0] || e > a.box.e[1] || n < a.box.n[0] || n > a.box.n[1]) return 0;
  const de = e - a.mid[0];
  const dn = n - a.mid[1];
  const u = de * a.ue + dn * a.un;
  const v = de * a.le + dn * a.ln;
  const f = rule.feather;
  // Under the deck and off its face, for the planters only: nothing roots
  // between the cribs or in the berth a boat lies in.
  if (wet && v < 0) {
    return v >= -(a.out + WATER_CLEAR_M) && Math.abs(u) <= a.halfLen + rule.widen ? rule.wear : 0;
  }
  const hw = a.halfLen + rule.widen * Math.min(1, Math.max(0, v / (a.L || 1)));
  return rule.wear * (1 - smooth(hw - f / 2, hw + f / 2, Math.abs(u)))
    * smooth(-1.0, 0, v) * (1 - smooth(a.L, a.L + f, v));
}

const FRAGMENT_HEAD = /* glsl */`
varying vec3 vChiWorld;
varying float vWear;
varying float vApron;
varying float vRoad;
varying float vTrack;
uniform sampler2D uGround;
uniform float uPrairieLuma;
${SWARD_HEAD}
uniform sampler2D uGrit;
uniform float uGritM;
uniform float uGritMean;
uniform vec3 uTrod;
uniform vec3 uRest;
uniform vec3 uMud;
uniform vec2 uPatch;
uniform vec2 uWet;
`;

const BANK_FRAGMENT = /* glsl */`
  // ---- T-1771 the working bank ------------------------------------------- //
  vec2 wbEN = vec2(vChiWorld.x, -vChiWorld.z);
${PATCH_GLSL}
  float wbGrass = smoothstep(uPatch.x - 0.5 * uPatch.y, uPatch.x + 0.5 * uPatch.y, wbPatch)
                * (1.0 - vApron);
  vec4 wbGrit = texture2D(uGrit, wbEN / uGritM);
  float wbGrain = wbGrit.r / max(uGritMean, 1e-6);
  // The trodden lanes: heaviest on an apron, wandering over the rest at a
  // metre's grain, so the bank is not one flat tone.
  float wbLane = 0.5 + 0.5 * sin(wbEN.x * 2.3 + wbEN.y * 1.7) * sin(wbEN.y * 2.9 - 0.8);
  float wbTraffic = clamp(0.7 * vApron + 0.45 * wbLane * (1.0 - 0.5 * vApron), 0.0, 1.0);
  vec3 wbEarth = mix(uRest, uTrod, wbTraffic) * mix(1.0, wbGrain, 0.6) * (0.93 + 0.14 * wbPatch);
  float wbWet = 1.0 - smoothstep(uWet.x, uWet.y, vChiWorld.y);
  wbEarth = mix(wbEarth, uMud * mix(1.0, wbGrain, 0.3), wbWet);
  float wbW = clamp(vWear * (1.0 - wbGrass), 0.0, 1.0);
  // ON THE STREET THE BANK GIVES ONLY ITS EARTH. The band feathers in over
  // the street's worked edge on purpose, to wear the shoulder's grass off, but
  // this mesh is opaque and stands 4 cm up where the street stands 2.2, so
  // wherever it drew the prairie (its feather, its surviving patches, every
  // 1.25 m cell that only one worn corner pulled in) it drew grass OVER the
  // street — square patches of it along South Water's river side, growing as
  // the owner walked up to them (2026-10-02). There, the street is what shows.
  //
  // And on the street it is earth over the shoulders, which is the grass it
  // was laid to wear off, ending on a line that wanders a metre either side of
  // the wheel track's edge with the ground's own patches. It used to end where
  // the per-vertex wear crossed one half: that contour followed the 1.25 m
  // cells and drew the bank's darker earth over the street as rows of square
  // teeth, seen from the air at Franklin (T-1987).
  if (vRoad < 0.0) {
    if (vTrack < 1.6 * wbPatch - 0.8) discard;
    wbW = 1.0;
  }
  diffuseColor.rgb = mix(chiPrairie, min(wbEarth, vec3(1.0)), wbW);
  float wbRough = mix(1.0, mix(0.96, 0.58, wbWet), wbW);
`;

const NORMAL_FRAGMENT = /* glsl */`
  // The grit's relief in a world tangent frame, as the ground strip draws it:
  // full on the dry earth, flattened where the mud has levelled it.
  vec2 wbGN = wbGrit.gb * 2.0 - 1.0;
  vec2 wbXY = wbGN * wbW * (1.0 - 0.7 * wbWet)
             + chiSwardXY * (1.0 - wbW);   // the sward's, where it draws prairie (T-2089)
  vec3 wbTn = normalize(vec3(wbXY, 1.0));
  vec3 wbEastV = normalize((viewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
  vec3 wbT = normalize(wbEastV - normal * dot(wbEastV, normal));
  vec3 wbB = cross(normal, wbT);
  normal = normalize(wbT * wbTn.x + wbB * wbTn.y + normal * wbTn.z);
`;

async function getJSON(url) {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return res.json();
}

/**
 * Build the working bank. Never throws: a record that does not load is a bank
 * that is not drawn, reported on `problems`, and the walk carries on.
 *
 * @param {object} o  dataBase (data/ root, the wharf layer's) · terrain ·
 *   streetRecords (the drawn streets) · wharves (the wharf layer's drawn decks)
 *   · confidence · problems · detail (`full` | `balanced` | `light`)
 */
export async function createWorkingBank({
  dataBase, terrain, streetRecords = [], wharves = [], confidence = null,
  problems = [], detail = 'full',
} = {}) {
  const group = new THREE.Group();
  group.name = 'working_bank';
  const stats = { drawn: false, triangles: 0, reaches: 0, columns: 0, aprons: 0,
    aproned: [], step_m: MESH_STEP_M[detail] ?? MESH_STEP_M.full };
  const handle = {
    group, stats, record: null, reaches: [], aprons: [],
    wearAt: () => 0, blocksGrowth: () => false, blocksTrees: () => false, dispose: () => {},
  };
  if (!dataBase || !terrain) {
    problems.push('working bank: no data base or no terrain — the bank is left as sward');
    return handle;
  }
  let record;
  try {
    const index = await getJSON(new URL('wharves/index.json', dataBase));
    const entry = (index.working_banks ?? [])[0];
    if (!entry?.file) return handle;
    record = await getJSON(new URL(`wharves/${entry.file}`, dataBase));
  } catch (err) {
    problems.push(`working bank: ${err.message} — the bank is left as sward`);
    return handle;
  }
  handle.record = record;

  const streets = new Map(streetRecords.map((s) => [s.id, s]));
  const reaches = [];
  for (const r of record.reaches ?? []) {
    const read = readReach(r, streets.get(r.street), terrain, problems);
    if (read) reaches.push(read);
  }
  const L = record.landings ?? {};
  const apronRule = {
    widen: L.apron_widen_m ?? 2, landward: L.apron_landward_m ?? 14,
    wear: L.wear ?? 1, feather: L.feather_m ?? 1.5,
  };
  const streetReach = reaches.find((r) => r.street === L.to_street) ?? null;
  const aprons = [];
  for (const w of wharves) {
    const a = readApron(w, apronRule, streetReach);
    if (a) aprons.push(a);
  }
  const G = record.grass_patches ?? {};
  const grassRule = { above: G.survive_above ?? 0.76, fade: G.fade_m ?? 0.22,
    keep: G.patch_keeps ?? 0.6, neverOnAprons: G.never_on_aprons !== false };
  const treeCut = record.trees?.cleared_above_wear ?? 0.35;
  handle.reaches = reaches;
  handle.aprons = aprons;
  stats.reaches = reaches.length;
  stats.columns = reaches.reduce((s, r) => s + r.laid, 0);
  stats.aprons = aprons.length;
  stats.aproned = aprons.map((a) => ({ id: a.id, to_street: a.toStreet, landward_m: +a.L.toFixed(2) }));

  /** The worn weight and the apron share at a point, 0..1 each. */
  const wearParts = (e, n, wet = false) => {
    let reach = 0;
    for (const r of reaches) {
      if (e < r.box.e[0] || e > r.box.e[1] || n < r.box.n[0] - WATER_CLEAR_M
        || n > r.box.n[1] + WATER_CLEAR_M) continue;
      reach = Math.max(reach, reachWear(r, e, n, wet));
    }
    let apron = 0;
    for (const a of aprons) apron = Math.max(apron, apronWear(a, apronRule, e, n, wet));
    return { wear: Math.max(reach, apron), apron };
  };
  handle.wearAt = (e, n) => wearParts(e, n).wear;

  // The planters. The sward gives way where the shader draws earth — a seeded
  // draw against the earth's own weight there, so it thins into the patches
  // rather than stopping on a line. No tree stands on the worn band at all.
  const hash = (e, n) => {
    const s = Math.sin(e * 127.1 + n * 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  handle.blocksGrowth = (e, n) => {
    const wet = terrain.surfaceHeight(e, n) <= 0;
    const { wear, apron } = wearParts(e, n, wet);
    if (wear <= 0) return false;
    // In the water at the worked foot nothing is spared; on the bank a patch
    // keeps most of its grass, not all of it — it is trodden round, not fenced.
    if (wet) return true;
    const bare = wear * (1 - grassRule.keep * grassAt(e, n, apron, grassRule));
    return hash(e, n) < bare;
  };
  handle.blocksTrees = (e, n) => wearParts(e, n).wear > treeCut;

  // The mesh: one grid per region at the tier's step, every vertex on the
  // heightfield the walker stands on, and only the cells the wear touches.
  const step = stats.step_m;
  const pos = [];
  const wearA = [];
  const apronA = [];
  // How far outside the worked width of the street the bank is worn from, in
  // metres across it: negative on the street. See `aRoad` in the shader.
  const roadLines = [];
  for (const r of reaches) {
    if (!roadLines.some((l) => l.pts === r.pts)) {
      roadLines.push({ pts: r.pts, half: r.half, track: r.track });
    }
  }
  const roadAt = (e, n, edge = 'half') => {
    let d = ROAD_FAR_M;
    for (const l of roadLines) {
      const at = lineAt(l.pts, e);
      if (at) d = Math.min(d, Math.abs(n - at.n) * at.cos - l[edge]);
    }
    return d;
  };
  // The same distance from the wheel track's edge: the street's own shoulders
  // lie between the two, and that is where the bank's earth may stand on it.
  const trackA = [];
  const roadA = [];
  const index = [];
  const regions = [...reaches.map((r) => r.box)];
  for (const a of aprons) {
    const m = a.meshBox;
    const inside = reaches.some((r) => m.e[0] >= r.box.e[0] && m.e[1] <= r.box.e[1]
      && m.n[0] >= r.box.n[0] && m.n[1] <= r.box.n[1]);
    if (!inside) regions.push(m);
  }
  for (const box of regions) {
    const e0 = Math.floor(box.e[0] / step) * step;
    const n0 = Math.floor(box.n[0] / step) * step;
    const nu = Math.ceil((box.e[1] - e0) / step);
    const nv = Math.ceil((box.n[1] - n0) / step);
    const base = pos.length / 3;
    const w = new Float32Array((nu + 1) * (nv + 1));
    for (let j = 0; j <= nv; j += 1) {
      const n = n0 + j * step;
      for (let i = 0; i <= nu; i += 1) {
        const e = e0 + i * step;
        const parts = wearParts(e, n);
        const road = roadAt(e, n);
        const y = road < 0 && terrain.inBounds?.(e, n)
          ? ridgeHeight(terrain, e, n) + ON_STREET_LIFT_M
          : terrain.surfaceHeight(e, n) + LIFT_M;
        pos.push(e, Number.isFinite(y) ? y : LIFT_M, -n);
        wearA.push(parts.wear);
        apronA.push(parts.apron);
        roadA.push(road);
        trackA.push(roadAt(e, n, 'track'));
        w[j * (nu + 1) + i] = parts.wear;
      }
    }
    for (let j = 0; j < nv; j += 1) {
      for (let i = 0; i < nu; i += 1) {
        const a = j * (nu + 1) + i;
        const b = a + 1;
        const c = a + nu + 1;
        const d = c + 1;
        if (Math.max(w[a], w[b], w[c], w[d]) <= 0.001) continue;
        // On the street, the upper of the two diagonals (see ON_STREET_LIFT_M).
        const Y = (k) => pos[(base + k) * 3 + 1];
        const onStreet = Math.min(roadA[base + a], roadA[base + b], roadA[base + c],
          roadA[base + d]) < 0;
        if (onStreet && Y(b) + Y(c) > Y(a) + Y(d)) {
          index.push(base + a, base + b, base + c, base + b, base + d, base + c);
        } else {
          index.push(base + a, base + b, base + d, base + a, base + d, base + c);
        }
      }
    }
  }
  if (!index.length) {
    problems.push('working bank: the record loaded and no worked ground was laid');
    return handle;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('aWear', new THREE.Float32BufferAttribute(wearA, 1));
  geo.setAttribute('aApron', new THREE.Float32BufferAttribute(apronA, 1));
  geo.setAttribute('aRoad', new THREE.Float32BufferAttribute(roadA, 1));
  geo.setAttribute('aTrack', new THREE.Float32BufferAttribute(trackA, 1));
  // Every vertex reconstructed: the whole layer is an invention bounded by the
  // town's own landings, and it goes when a visitor hides that tier.
  geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(
    new Float32Array(pos.length / 3).fill(1), 1));
  geo.setIndex(index);
  geo.computeVertexNormals();
  geo.computeBoundingSphere();

  const prairie = prairieTexture();
  const sward = swardTexture();
  const gritData = gritTilePixels();
  const gc = document.createElement('canvas');
  gc.width = gc.height = GRIT_TILE_PX;
  gc.getContext('2d').putImageData(new ImageData(gritData, GRIT_TILE_PX, GRIT_TILE_PX), 0, 0);
  const gritTex = new THREE.CanvasTexture(gc);
  gritTex.colorSpace = THREE.NoColorSpace;
  gritTex.wrapS = gritTex.wrapT = THREE.RepeatWrapping;
  gritTex.anisotropy = 4;
  let gritSum = 0;
  for (let i = 0; i < gritData.length; i += 4) gritSum += gritData[i];
  const gritMean = gritSum / (gritData.length / 4) / 255;

  const T = record.tones ?? {};
  const wet = record.wetness?.mud_below_m ?? [0.08, 0.3];
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  mat.name = 'working-bank';
  // Lifted a few centimetres and pulled forward in depth, so the terrain under
  // it never wins a fragment. The street ribbon pulls harder (streets.js) and
  // stays on top where the two meet at the worked edge.
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -2;
  mat.polygonOffsetUnits = -2;
  /**
   * A DECAL PAINTS THE GROUND; IT DOES NOT HIDE WHAT STANDS ON IT. Drawn
   * opaque, this layer wrote its offset depth, and `polygonOffsetFactor` grows
   * with the polygon's depth slope, which at the grazing angle a bank is seen
   * at is enormous. So beyond ~30 m from a walking eye the biased bank stood
   * in front of the river walk's boards (0.11 m up), the timber lost the depth
   * test, and the walk ended short of its real end and grew back toward the
   * visitor as they approached it (T-2098, the owner, 2026-10-04).
   *
   * The street ribbon and the yards are decals drawn this way already, and
   * the timber's own comment (frontage.js, T-0625) is why ordering rather than
   * a counter-bias is the repair: the bank joins the transparent list FIRST,
   * tests against the terrain with the same offset it always had, and writes
   * no depth, so the ribbon (renderOrder 0) still lies over it and the timber
   * (renderOrder 1) tests against the ground alone. Alpha stays 1; nothing
   * blends. Free: no geometry, pass or program changes.
   */
  mat.transparent = true;
  mat.depthWrite = false;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, {
      uGround: { value: prairie },
      uPrairieLuma: { value: prairie.userData.meanLinearLuma },
      ...swardUniforms(sward),
      uGrit: { value: gritTex }, uGritM: { value: GRIT_TILE_M }, uGritMean: { value: gritMean },
      uTrod: { value: linearTone(T.earth_trodden ?? [116, 103, 83]) },
      uRest: { value: linearTone(T.earth_rest ?? [98, 86, 66]) },
      uMud: { value: linearTone(T.mud ?? [64, 56, 44]) },
      uPatch: { value: new THREE.Vector2(grassRule.above, grassRule.fade) },
      uWet: { value: new THREE.Vector2(wet[0], wet[1]) },
    });
    shader.vertexShader = 'varying vec3 vChiWorld;\nattribute float aWear;\n'
      + 'attribute float aApron;\nattribute float aRoad;\nattribute float aTrack;\n'
      + 'varying float vWear;\nvarying float vApron;\nvarying float vRoad;\n'
      + 'varying float vTrack;\n'
      + shader.vertexShader.replace('#include <begin_vertex>',
        `#include <begin_vertex>${WORLD_POS_VERT}\n  vWear = aWear;\n  vApron = aApron;\n`
        + '  vRoad = aRoad;\n  vTrack = aTrack;');
    shader.fragmentShader = FRAGMENT_HEAD + shader.fragmentShader
      .replace('#include <map_fragment>', PRAIRIE_FRAGMENT + BANK_FRAGMENT)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = wbRough;')
      .replace('#include <normal_fragment_maps>', NORMAL_FRAGMENT);
  };
  confidence?.patch(mat);
  // Its own program cache key — see wharves.js: a patched material otherwise
  // shares a program with any other patched material that agrees with it.
  mat.customProgramCacheKey = () => 'chicago4d-working-bank';

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'working_bank';
  mesh.renderOrder = -1;            // under the ribbon and the timber (above)
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  group.add(mesh);

  stats.drawn = true;
  stats.triangles = index.length / 3;
  group.userData.census = stats;
  // The prairie tile is the terrain's as much as this layer's; it is not ours to free.
  handle.dispose = () => { geo.dispose(); mat.dispose(); gritTex.dispose(); sward.dispose(); };
  return handle;
}
