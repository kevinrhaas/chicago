// SPDX-License-Identifier: GPL-3.0-or-later
// T-3586. One gust rhythm shared by everything that moves in the wind and by the
// wind you hear. Owner, 2026-11-13: "it would be nice if the wind sound worked with
// the trees so it would be noticeable, to see when the trees blow ... dont make the
// wind too loud or noticeable until its right", then "assume this applies in all years".
//
// A gust is a front that travels across the town from the south-west (the July
// south-westerly the fort's flags already fly in, flags.js WIND_FROM_DEG) at GUST.speed m/s. Its
// strength at a place and time is one smooth number in [GUST.min, 1]: 1 is the sway
// every tree and vine had before (so nothing ever swings farther than it did, and a
// wall vine stays off its wall, T-3383), and lulls between gusts are calmer. The
// same function is written once here in JS and once as GLSL (GUST_GLSL), so the
// crown you see bend is the gust you hear.
//
// The rhythm repeats every GUST.period seconds exactly (its three swells divide it),
// so the clock wraps with no seam and stays small enough for phone shader precision.
// Every number here is a listening and looking choice, not weather
// (L-wind-gusts-3586).
export const GUST = Object.freeze({
  min: 0.35, period: 240, speed: 7,
  // Unit vector the gust front travels toward, east/north: toward the north-east.
  dir: Object.freeze([0.82 / Math.hypot(0.82, 0.57), 0.57 / Math.hypot(0.82, 0.57)]),
  swells: Object.freeze([[48, 0.5, 0], [30, 0.3, 1.7], [20, 0.2, 4.1]]),
});

const TAU = Math.PI * 2;
let clock = 0;

/** Advance the shared clock once per frame (main.js). Returns the wrapped clock. */
export function advanceGust(dt) {
  if (Number.isFinite(dt) && dt > 0) clock = (clock + Math.min(dt, 1)) % GUST.period;
  return clock;
}
export const gustClock = () => clock;
/** For tests and tools only. */
export function setGustClock(t) { clock = ((Number(t) || 0) % GUST.period + GUST.period) % GUST.period; }

/** Gust strength in [GUST.min, 1] at world east `e`, north `n`, at clock `t`. */
export function gustAt(e = 0, n = 0, t = clock) {
  const s = t - (e * GUST.dir[0] + n * GUST.dir[1]) / GUST.speed;
  let v = 0;
  for (const [p, a, ph] of GUST.swells) v += a * Math.sin(TAU * s / p + ph);
  const k = 0.5 + 0.5 * v; // 0..1
  return GUST.min + (1 - GUST.min) * k * k;
}

/** The scene's own x/z (x = east, z = -north) convenience. */
export const gustAtScene = (x, z, t = clock) => gustAt(x, -z, t);

/** Shared uniform: the wrapped clock. Every patched material holds this object. */
export const uGustClock = { value: 0 };
export function syncGustUniform() { uGustClock.value = clock; return uGustClock; }

/** GLSL twin of gustAt, for a vertex shader with `uniform float uGustClock;`.
 *  `w` is the world position (three.js: x east, z = -north). */
export const GUST_GLSL = `
float chiTownGust(vec3 w) {
  float s = uGustClock - (w.x * ${GUST.dir[0].toFixed(4)} - w.z * ${GUST.dir[1].toFixed(4)}) / ${GUST.speed.toFixed(4)};
  float v = ${GUST.swells.map(([p, a, ph]) => `${a.toFixed(4)} * sin(${(TAU / p).toFixed(6)} * s + ${ph.toFixed(4)})`).join('\n    + ')};
  float k = 0.5 + 0.5 * v;
  return ${GUST.min.toFixed(4)} + ${(1 - GUST.min).toFixed(4)} * k * k;
}
`;

/** How the wind you hear follows the gust where you stand: 0.3x the old leaf-rustle
 *  level in a lull, 1.6x at a gust's top, so a gust is heard as the crowns bend while
 *  the average stays at or under the quiet town mix the owner set on 2026-11-11
 *  (0.012 in 1904 peaks at 0.019, against the 0.13 he found too strong). */
export const WIND_SOUND = Object.freeze({ lull: 0.3, peak: 1.6 });
export const windGustGain = g => WIND_SOUND.lull + (WIND_SOUND.peak - WIND_SOUND.lull)
  * Math.min(1, Math.max(0, (g - GUST.min) / (1 - GUST.min)));
