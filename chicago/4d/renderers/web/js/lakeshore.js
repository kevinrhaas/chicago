/**
 * lakeshore.js — where the lake's sand is, as ONE rule the ground, the sward and
 * the trees all read (T-1819, piece 1 of the owner's T-1772).
 *
 * WHAT IT REPLACED. The beach (`z08_lakeshore`) and the sand prairie behind it
 * (`z09_sand_prairie`) were two `kind: "everywhere"` boxes, E +840..+1700 by
 * N -400..+400. The owner's report, 2026-09-30: a sharp beach boundary, and the
 * fort's sand stopping dead instead of carrying north and south along the lake.
 * Both were properties of the box. Its north and south edges were straight
 * east-west lines across the belt at N +/-400 — "the scene's own" bounds, the
 * records admit, "not the belt's" — so 600 m south of the fort the beach turned
 * into riverbank timber and mesic prairie along a ruled line, and its west edge
 * was a 100 m smoothstep along a meridian. A box cannot follow a shore.
 *
 * WHAT IT IS NOW. Two extent refinements, both carried in the zone RECORDS and
 * both evaluated by the functions in this file, so a record states the rule and
 * every reader answers the same question:
 *
 *   - `kind: "lake_shore"` — ground within `distance_m` of the LAKE's edge,
 *     measured west from it. The edge is not drawn by anyone: it is read off the
 *     committed heightfield at load (`lakeShoreLine`), so the beach goes where
 *     the modelled shore goes, sand bar and all, and moves when the terrain does.
 *   - `edge: { ramp_m, wander_m }` on a box — the box's sides stop being lines.
 *     z09's west side is the State Street break of slope (its record's own
 *     reasoning); it now wanders and ramps across it instead of being ruled.
 *
 * BOTH EDGES ARE IRREGULAR AND BROAD, ON PURPOSE. No survey drew either line —
 * the records say so (z09: "The north-south bounds are the scene's own, not the
 * belt's"; z08: "the beach continues well beyond it"). A hard edge would draw
 * that admission as a surveyed boundary, so the edge is a RAMP (`ramp_m` either
 * side of the stated distance) that WANDERS (`wander_m`, three incommensurate
 * sines at ~310 m, ~97 m and ~18 m: a shore-long swing, a blow-out scale and a
 * patch scale). The wander is shape, not evidence; the liberty says so.
 *
 * HOW THE GROUND AND THE PLANTS AGREE. The ground shader blends a zone's colour
 * by `bandWeight` — 1 inside, 0 outside, smooth across the ramp. The sward and
 * the trees ask `matches()` in flora.js, which DITHERS the same weight against a
 * positional hash (`ditherHash`): a point in the ramp belongs to the zone with
 * probability equal to the weight the ground drew there. So across a transition
 * the sand shows through more as the dune community's sparse cover takes over
 * from the prairie's closed one, and there is no line in either.
 *
 * `tools/validate.py` mirrors these functions (`_lake_shore_line`,
 * `_shore_wander`, `_dither_hash`) so the extent audit answers the renderer's
 * question; change one, change both.
 */

/** Below this the heightfield is under water — terrain.js's SHORE_Y. */
export const LAKE_SHORE_Y = -0.10;

/** The shore line's sample spacing along N, metres. 40 m carries the shore's
 *  real bends (the bar, the mouth's jetties are filled — see below) in 124
 *  samples over the 4,920 m field, which is 31 vec4 uniforms in the shader. */
export const SHORE_LINE_STEP_M = 40;

/** How far either side along N a row borrows a further-east shore from, metres.
 *  This is what carries the line ACROSS the river mouth: on the committed field
 *  the cut is about 200 m of N (-650..-450) where a row's easternmost land is
 *  the inner bank, up to 250 m back, and without the fill the beach would bulge
 *  up the river. 120 m either side spans it after the median below has widened
 *  it; the cost is that the line holds the bar's east face a little past the
 *  bar's north end, so the beach there is a few tens of metres narrower. */
const SHORE_FILL_M = 120;

/** How far either side along N a row's shore is taken as the MEDIAN of, metres,
 *  before the fill — so a few rows of land that are not the shore cannot be
 *  carried 120 m either way by the max. The committed e1834 field has one: at
 *  N -2160 a single row is land from the bank to the field's east edge, and the
 *  forty metres of rows north of it carry 10-120 m islets off the beach. A median over 41
 *  rows (+/-50 m) drops both and leaves the bar, which is hundreds of rows. */
const SHORE_MEDIAN_M = 50;

/**
 * The lake's edge as E for each 40 m of N, read off the heightfield: per grid
 * row, the easternmost node that is land; a median over +/-50 m to drop rows
 * that are not the shore; a running max over +/-120 m to bridge the mouth; a mean
 * over each 40 m sample's own rows to steady it.
 *
 * @param {{loaded:boolean, cols:number, rows:number, cellM:number, originE:number,
 *          originN:number, sample:(e:number,n:number)=>number}} hf
 * @returns {{n0:number, step:number, e:Float32Array}|null}
 */
export function lakeShoreLine(hf) {
  if (!hf?.loaded || !(hf.cols > 1 && hf.rows > 1)) return null;
  const { cols, rows, cellM, originE, originN } = hf;
  const raw = new Float64Array(rows).fill(NaN);
  for (let j = 0; j < rows; j++) {
    const n = originN + j * cellM;
    for (let i = cols - 1; i >= 0; i--) {
      const e = originE + i * cellM;
      if (hf.sample(e, n) >= LAKE_SHORE_Y) { raw[j] = e; break; }
    }
  }
  const wm = Math.max(1, Math.round(SHORE_MEDIAN_M / cellM));
  const steady = new Float64Array(rows).fill(NaN);
  for (let j = 0; j < rows; j++) {
    const v = [];
    for (let k = Math.max(0, j - wm); k <= Math.min(rows - 1, j + wm); k++) {
      if (Number.isFinite(raw[k])) v.push(raw[k]);
    }
    if (v.length) { v.sort((x, y) => x - y); steady[j] = v[(v.length - 1) >> 1]; }
  }
  const w = Math.max(1, Math.round(SHORE_FILL_M / cellM));
  const filled = new Float64Array(rows).fill(NaN);
  for (let j = 0; j < rows; j++) {
    let m = -Infinity;
    for (let k = Math.max(0, j - w); k <= Math.min(rows - 1, j + w); k++) {
      if (steady[k] > m) m = steady[k];
    }
    filled[j] = Number.isFinite(m) ? m : NaN;
  }
  const spanN = (rows - 1) * cellM;
  const count = Math.floor(spanN / SHORE_LINE_STEP_M) + 1;
  const out = new Float32Array(count);
  const half = SHORE_LINE_STEP_M / 2;
  let last = NaN;
  for (let k = 0; k < count; k++) {
    const nk = k * SHORE_LINE_STEP_M;
    const j0 = Math.max(0, Math.ceil((nk - half) / cellM));
    const j1 = Math.min(rows - 1, Math.floor((nk + half) / cellM));
    let s = 0;
    let c = 0;
    for (let j = j0; j <= j1; j++) if (Number.isFinite(filled[j])) { s += filled[j]; c++; }
    out[k] = c ? s / c : last;
    if (c) last = out[k];
  }
  // A leading gap (no land in the first rows) takes the first real value.
  const first = out.find((v) => Number.isFinite(v));
  if (first === undefined) return null;
  for (let k = 0; k < count && !Number.isFinite(out[k]); k++) out[k] = first;
  return { n0: originN, step: SHORE_LINE_STEP_M, e: out };
}

/** The lake's edge E at northing n, linear between samples, clamped at the ends. */
export function shoreE(line, n) {
  const last = line.e.length - 1;
  const t = Math.min(last, Math.max(0, (n - line.n0) / line.step));
  const i = Math.min(last - 1, Math.floor(t));
  const f = t - i;
  return line.e[i] * (1 - f) + line.e[i + 1] * f;
}

/** Metres west of the lake's edge — negative out on the water. */
export function shoreDistance(line, e, n) {
  return shoreE(line, n) - e;
}

/** The edge's wander as a unit signal, about -1..+1: a ~310 m swing along the
 *  shore, a ~97 m blow-out scale and an ~18 m patch scale. Identical in GLSL
 *  below and in tools/validate.py. */
export function shoreWander(e, n) {
  return 0.55 * Math.sin(0.0203 * n + 1.3)
       + 0.30 * Math.sin(0.0647 * n + 0.0211 * e + 0.7)
       + 0.15 * Math.sin(0.2731 * e - 0.2113 * n + 2.1);
}

function smoothstep(lo, hi, x) {
  if (!(hi > lo)) return x >= hi ? 1 : 0;
  const t = Math.min(1, Math.max(0, (x - lo) / (hi - lo)));
  return t * t * (3 - 2 * t);
}

/** 1 well inside a limit, 0 well past it, smooth over +/-ramp around it — for a
 *  quantity `x` that GROWS outward (a distance from the shore, a distance past a
 *  box side). */
export function bandWeight(x, limit, ramp) {
  return 1 - smoothstep(limit - ramp, limit + ramp, x);
}

/** A positional 0..1 draw, 0.5 m grain, so the same point always answers the same. */
export function ditherHash(e, n) {
  const a = Math.round(e * 2) | 0;
  const b = Math.round(n * 2) | 0;
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ 0x51ed270b;
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/**
 * How strongly an extent holds (e, n), 0..1, for the two refinements this file
 * owns — or null when the extent carries neither (the caller's own rule stands).
 * `kind: "lake_shore"` needs the line; without it the zone holds nothing, which
 * is the safe direction (no beach is drawn where no shore was read).
 */
export function softExtentWeight(x, e, n, line) {
  if (x?.kind === 'lake_shore') {
    if (!line) return 0;
    const [, far] = x.distance_m ?? [0, 0];
    const d = shoreDistance(line, e, n) + (x.wander_m ?? 0) * shoreWander(e, n);
    return bandWeight(d, far, x.ramp_m ?? 0);
  }
  if (x?.edge && x.box) {
    const r = x.edge.ramp_m ?? 0;
    const off = (x.edge.wander_m ?? 0) * shoreWander(e, n);
    const be = x.box.e;
    const bn = x.box.n;
    let w = 1;
    if (be) w *= bandWeight(be[0] - e + off, 0, r) * bandWeight(e - be[1] + off, 0, r);
    if (bn) w *= bandWeight(bn[0] - n + off, 0, r) * bandWeight(n - bn[1] + off, 0, r);
    return w;
  }
  return null;
}

/* -------------------------------------------------------------------------- */
/* the same rule as fragment code                                              */
/* -------------------------------------------------------------------------- */

/** The uniform the shader reads the line from: the samples packed four to a vec4. */
export function shoreUniform(line, THREE) {
  const v = [];
  for (let k = 0; k < line.e.length; k += 4) {
    const at = (i) => line.e[Math.min(line.e.length - 1, k + i)];
    v.push(new THREE.Vector4(at(0), at(1), at(2), at(3)));
  }
  return v;
}

const g = (v) => (Number.isInteger(v) ? v.toFixed(1) : String(v));

/** Declarations, spliced ahead of `main()`: the wander always, and the uniform
 *  and the shore functions when a line was read (no line, no lake_shore zone —
 *  terrain.js drops it, as `softExtentWeight` answers 0 for it). */
export function shoreGlslHead(line) {
  const wander = `
// lakeshore.js shoreWander.
float chiShoreWander(float e, float n) {
  return 0.55 * sin(0.0203 * n + 1.3)
       + 0.30 * sin(0.0647 * n + 0.0211 * e + 0.7)
       + 0.15 * sin(0.2731 * e - 0.2113 * n + 2.1);
}
`;
  if (!line) return wander;
  const vecs = Math.ceil(line.e.length / 4);
  return `${wander}
uniform vec4 uChiShore[${vecs}];
float chiShoreAt(int i) {
  vec4 v = uChiShore[i >> 2];
  int c = i & 3;
  return c == 0 ? v.x : (c == 1 ? v.y : (c == 2 ? v.z : v.w));
}
// The lake's edge E at northing n (lakeshore.js shoreE).
float chiShoreE(float n) {
  float t = clamp((n - ${g(line.n0)}) / ${g(line.step)}, 0.0, ${g(line.e.length - 1)});
  int i = min(int(floor(t)), ${line.e.length - 2});
  return mix(chiShoreAt(i), chiShoreAt(i + 1), t - float(i));
}
`;
}

/** A zone's weight `w` as GLSL, for the refinements above; null when the zone
 *  carries neither, so the caller keeps its own box code. Expects chiE, chiN. */
export function softExtentGlsl(x) {
  if (x?.kind === 'lake_shore') {
    const far = (x.distance_m ?? [0, 0])[1];
    const r = x.ramp_m ?? 0;
    return `float w = 1.0 - smoothstep(${g(far - r)}, ${g(far + r)},
        chiShoreE(chiN) - chiE + ${g(x.wander_m ?? 0)} * chiShoreWander(chiE, chiN));`;
  }
  if (x?.edge && x.box) {
    const r = x.edge.ramp_m ?? 0;
    const side = (expr) => `(1.0 - smoothstep(${g(-r)}, ${g(r)}, ${expr} + off))`;
    const terms = [];
    if (x.box.e) terms.push(side(`${g(x.box.e[0])} - chiE`), side(`chiE - ${g(x.box.e[1])}`));
    if (x.box.n) terms.push(side(`${g(x.box.n[0])} - chiN`), side(`chiN - ${g(x.box.n[1])}`));
    return `float off = ${g(x.edge.wander_m ?? 0)} * chiShoreWander(chiE, chiN);
    float w = ${terms.join('\n            * ') || '1.0'};`;
  }
  return null;
}
