/**
 * T-3331 — TIME OF DAY. The visitor's hour, and what the light does at it.
 *
 * The owner, 2026-11-03: "Cans we add a setting to control time of day? Would be
 * near if we could choose any time or any hour or roughly half hour or 10 min
 * interval? Or it could be 4 hour segments like daybreak, morning, daytime ...
 * default it to daytime in settings". So Settings › Show › Time of day offers both:
 * a slider over the whole day in 10-minute steps, and named times. `daytime` is the
 * scene's own hour (data/scenes/<year>.json `lighting.local_time`) and the default,
 * which draws exactly the frame that shipped before this setting existed.
 *
 * Hours are LOCAL MEAN SOLAR TIME at the town's longitude, the clock the scene's own
 * hour has always been written in (world.js `solarPosition`). No railway time
 * existed in 1812 or 1835, and a sundial's noon is what a reader of those hours
 * means; 1904's hours are given the same way so the three years agree.
 *
 * The named times that depend on the sun (daybreak, sunset, dusk) are solved
 * against the sun on the date in force — the scene's, the Season's, or a jaunt
 * stop's — so "sunset" in December is not the August sunset.
 *
 * This module is pure: names, the grade the light takes at a sun elevation, and
 * the small daylight broadcast that unlit layers (the far timber band) listen to.
 * world.js does the relighting; main.js wires the setting and `api.timeOfDay`.
 */

/** The named times, in the order Settings lists them. `at` is either a clock time
 *  or the sun event it is solved from (`rise`, `set`, `civil-dusk`). */
export const TIME_NAMES = [
  { id: 'daybreak', label: 'Daybreak', at: 'rise' },
  { id: 'morning', label: 'Morning', at: '09:00' },
  { id: 'daytime', label: 'Daytime', at: 'scene' },
  { id: 'afternoon', label: 'Afternoon', at: '16:00' },
  { id: 'sunset', label: 'Sunset', at: 'set' },
  { id: 'dusk', label: 'Dusk', at: 'civil-dusk' },
  { id: 'night', label: 'Night', at: '22:00' },
];
const NAME_IDS = new Set(TIME_NAMES.map((n) => n.id));

/** The sun's centre at the named daybreak and sunset, degrees (see resolveTime). */
export const SUN_EVENT_DEG = 1.0;

/** The slider's step: the owner's "10 min interval". */
export const STEP_MIN = 10;

/** 'HH:MM' -> minutes after midnight, or null. */
export function minutesOf(hhmm) {
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(hhmm ?? '').trim());
  if (!m) return null;
  const h = Number(m[1]); const mi = Number(m[2]);
  if (h > 23 || mi > 59) return null;
  return h * 60 + mi;
}

/** Minutes after midnight -> 'HH:MM', wrapped into the day. */
export function hhmmOf(minutes) {
  const m = ((Math.round(minutes) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
}

/** Whether `v` is something the setting accepts: a name or 'HH:MM'. */
export function isTimeValue(v) {
  return NAME_IDS.has(v) || minutesOf(v) !== null;
}

/**
 * The minute at which the sun crosses `elevationDeg`, rising (`rising` true) or
 * setting, found by a coarse scan and a bisection. `elevationAt(min)` is the sun's
 * height at that minute on the date in force. Null when it never crosses (it
 * always does at Chicago's latitude, but the caller is told rather than handed 0).
 */
export function crossing(elevationAt, elevationDeg, rising) {
  const step = 20;
  let prev = elevationAt(0) - elevationDeg;
  for (let t = step; t <= 1440; t += step) {
    const cur = elevationAt(t) - elevationDeg;
    const crossed = rising ? (prev < 0 && cur >= 0) : (prev >= 0 && cur < 0);
    if (crossed) {
      let lo = t - step; let hi = t;
      for (let i = 0; i < 12; i++) {
        const mid = (lo + hi) / 2;
        const v = elevationAt(mid) - elevationDeg;
        if ((v >= 0) === rising) hi = mid; else lo = mid;
      }
      return (lo + hi) / 2;
    }
    prev = cur;
  }
  return null;
}

/**
 * A setting value -> the clock time it stands for, on the slider's 10-minute grid.
 * Daybreak and sunset are drawn with the whole disc just clear of a level horizon
 * (its centre 1° up, SUN_EVENT_DEG): the almanac's sunrise and sunset put the centre
 * at -0.833°, which counts refraction this renderer does not draw, so the disc
 * would be under the ground on screen. Dusk is the end of civil twilight, the centre
 * at -6°, the hour lamps are wanted indoors.
 *
 * @param {string} value       a TIME_NAMES id or 'HH:MM'
 * @param {object} o
 * @param {string} o.sceneTime the scene's own hour, 'HH:MM'
 * @param {(min:number)=>number} o.elevationAt sun elevation in degrees at a minute
 * @returns {{hhmm:string, name:string|null}}
 */
export function resolveTime(value, { sceneTime, elevationAt }) {
  if (minutesOf(value) !== null) {
    const name = TIME_NAMES.find((n) => n.at === value)?.id ?? null;
    return { hhmm: hhmmOf(minutesOf(value)), name };
  }
  const named = TIME_NAMES.find((n) => n.id === value) ?? TIME_NAMES.find((n) => n.id === 'daytime');
  if (named.at === 'scene') return { hhmm: sceneTime, name: named.id };
  if (minutesOf(named.at) !== null) return { hhmm: named.at, name: named.id };
  const event = named.at === 'rise' ? crossing(elevationAt, SUN_EVENT_DEG, true)
    : named.at === 'set' ? crossing(elevationAt, SUN_EVENT_DEG, false)
      : crossing(elevationAt, -6, false);
  if (event === null) return { hhmm: sceneTime, name: named.id };
  // Daybreak rounds UP onto the grid and sunset DOWN, so each named view keeps the
  // sun's disc on the horizon rather than ten minutes under it.
  const snapped = named.at === 'rise' ? Math.ceil(event / STEP_MIN) * STEP_MIN
    : named.at === 'set' ? Math.floor(event / STEP_MIN) * STEP_MIN
      : Math.round(event / STEP_MIN) * STEP_MIN;
  return { hhmm: hhmmOf(snapped), name: named.id };
}

/** The vendored Sky shader's own sunIntensity, without its EE scale. */
function skyModelSun(el) {
  const zenith = (90 - el) * Math.PI / 180;
  return Math.max(0, 1 - Math.exp(-((1.6110731556870734 - zenith) / 1.5)));
}
/** The most the evening fill is raised. */
const ENV_BOOST_MAX = 4;

function smoothstep(a, b, x) {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}

/**
 * THE GRADE AT A SUN ELEVATION. Every number the relight needs, from one input.
 *
 * Built so that from 14° up EVERY factor is exactly its identity value (1 or 0):
 * the scene's own hours (1812 15:00 at 50°, 1835 12:30 at 70°, 1904 10:30 at 56°)
 * and the Season's winter 10:30 (about 21°) all sit above that, so the shipped
 * frames are unchanged to the bit — smoothstep returns exactly 0 and 1 at its edges.
 *
 *  - sunK   the sun's share of its full intensity. Falls through the last few
 *           degrees, where the long air path takes most of it, and is 0 once the
 *           disc is under the horizon.
 *  - warm   how far the sun's colour has moved to the low-sun orange.
 *  - nightK the night key's share: a cool light from high in the south-east.
 *  - fillK  the sky fill's share, down to a starlit floor.
 *  - adapt  exposure the dark-adapted eye adds, in linear units (1 = none).
 *  - glow   the twilight glow on the horizon toward the sun.
 *  - night  the night sky's own colour added under the sky model.
 *
 * THE NIGHT IS A LIBERTY (L-night-grade-3331). No moon, starlight or airglow is
 * measured for any of the three dates. The night key and the exposure the eye adds
 * are chosen so a visitor can walk the town by night and see its shapes, which is
 * roughly what a dark-adapted eye does under a clear sky; they are not a claim
 * that the night was that bright. Twilight's colours are the shape of a clear
 * evening, not a record of one.
 *
 * @param {number} el sun elevation in degrees
 */
export function gradeAt(el) {
  const sunK = smoothstep(-1, 6, el);
  const warm = 1 - smoothstep(1, 14, el);
  const nightK = 1 - smoothstep(-10, -0.6, el);
  const fillK = 1 - (1 - 0.035) * (1 - smoothstep(-12, 12, el));
  const adapt = 1 + (NIGHT_ADAPT - 1) * (1 - smoothstep(-4, 12, el));
  const glow = smoothstep(-15, -4, el) * (1 - smoothstep(-2, 6, el));
  const night = 1 - smoothstep(-2, 6, el);
  // How far the night sky's colour is still twilight blue (1) rather than night (0).
  const dusk = smoothstep(-11, -1, el);
  // The sky model's skylight collapses as the sun nears the horizon (its sunIntensity
  // falls to 3 % of noon's at 0° and to nothing at -2.3°), and the fill baked from
  // it collapses with it, though a real evening is lit by the sky long after the sun
  // has gone. envBoost puts the baked fill back toward the fill's share at that
  // height. Never below 1 (the night's own fill is the night sky's), exactly 1 from 14° up.
  const envBoost = el >= 14 ? 1
    : Math.min(ENV_BOOST_MAX, Math.max(1, (skyModelSun(14) / Math.max(skyModelSun(el), 0.02)) * fillK));
  return { sunK, warm, nightK, fillK, adapt, glow, night, dusk, envBoost };
}

/** How much the dark-adapted eye adds at full night: about 1.6 stops. */
export const NIGHT_ADAPT = 3.0;
/** The night key's intensity at full night, and its colour (cool, as the eye
 *  reads a clear night). Its direction is fixed, high in the south-east. */
export const NIGHT_KEY = 0.42;
export const NIGHT_KEY_COLOR = 0xa9bcff;
export const NIGHT_KEY_AZIMUTH = 150;
export const NIGHT_KEY_ELEVATION = 52;
/** The low sun's colour, which the noon colour moves toward under 14°. */
export const LOW_SUN_COLOR = 0xffa463;
/** The night sky in linear radiance before tone mapping, zenith and horizon. */
export const NIGHT_SKY_ZENITH = [0.0045, 0.0075, 0.0170];
export const NIGHT_SKY_HORIZON = [0.0110, 0.0150, 0.0240];
/** The twilight sky the night sky starts from at sunset, zenith and horizon, linear. */
export const DUSK_SKY_ZENITH = [0.020, 0.040, 0.095];
export const DUSK_SKY_HORIZON = [0.060, 0.065, 0.080];
/** The twilight glow on the horizon toward the sun, linear, at its strongest. */
export const TWILIGHT_GLOW = [0.200, 0.080, 0.030];

// ---- the daylight broadcast --------------------------------------------------
//
// A few layers are drawn unlit, in display space, against the daytime sky (the
// far timber band, trees.js). They do not see the sun or the fill, so they are told
// the grade instead: `display` is the factor their colour is multiplied by. One
// page draws one year, so a module-level list is enough.
const listeners = new Set();
let last = { display: 1, grade: gradeAt(90) };

/** Subscribe; called at once with the current state. Returns an unsubscribe. */
export function onDaylight(fn) {
  listeners.add(fn);
  try { fn(last); } catch { /* a listener's fault is its own */ }
  return () => listeners.delete(fn);
}

/** world.js publishes each relight here. */
export function publishDaylight(state) {
  last = state;
  for (const fn of listeners) {
    try { fn(state); } catch { /* as above */ }
  }
}

/**
 * T-3331 — the leaves' transmitted skylight, one uniform shared by every leaf
 * material (tree-surface.js, tree-instances.js). A thin leaf passes on a little of
 * the sky, which was a constant 0.22 of its colour: right by day, a glow by night.
 * It falls with the sky's fill and the sun, and is exactly 0.22 by day.
 */
const LEAF_SKY_DAY = 0.22;
export const LEAF_SKY = { value: LEAF_SKY_DAY };
onDaylight(({ grade, lift = 1 }) => {
  // T-3428: `lift` is the brightness aid's fill lift (world.js), 1 when it is off.
  LEAF_SKY.value = (grade.sunK === 1 && grade.fillK === 1 ? LEAF_SKY_DAY
    : LEAF_SKY_DAY * grade.fillK * (0.3 + 0.7 * grade.sunK)) * lift;
});
