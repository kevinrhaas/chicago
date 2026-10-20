/** Shared motion settings: the controller and pure estimates read one definition. */
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const ARRIVAL_SETTLE_S = 0.5;

export const PACES = {
  instantly: { label: 'Instantly', hint: 'straight there, as before' },
  // Each ground pace has its own slider (T-0823): `settingKey` names the stored
  // value, `defaultSpeed` is what a fresh visitor gets, `maxSpeed` is the slider's
  // ceiling — 20, 30 and 60 mph, the owner's figures, raised by T-2945 to 30, 40 and
  // 80 mph so the faster defaults sit mid-slider — and `sprintFactor` is what
  // Shift does to it (a run on foot, nothing on a wagon, a gallop on a horse),
  // capped at the ceiling. The gait names a slider shows are in GAITS below.
  // T-2945 (owner, 2026-10-20: "default the walk speed to much faster like 10mph and
  // increase the relative speeds on everthing so its a bit faster"): walk 1.45 → 4.47 m/s
  // (10 mph), run 3.4 → 6.71 (15 mph), wagon 3.6 → 7.15 (16 mph), horse 6.5 → 11.18
  // (25 mph); walk < run < wagon < horse as before, sprint factors unchanged.
  // OLD_DEFAULTS keeps the figures they replace (hud.js reads an untouched stored one
  // as no choice).
  walk: {
    label: 'Walk', verb: 'Walking to', eyeOffset: 0, turnRate: 150,
    settingKey: 'speed', defaultSpeed: 4.47, maxSpeed: 13.41, sprintFactor: 2.28,
    hint: 'your own two feet',
  },
  // Running (T-2651): on foot, the walk's network and eye, with its own slider that
  // starts at a jog — `minSpeed` is the slider's floor — so Walk and Run are two
  // settings a visitor can flip between rather than one slider dragged back and forth.
  run: {
    label: 'Run', verb: 'Running to', eyeOffset: 0, turnRate: 150,
    settingKey: 'runSpeed', defaultSpeed: 6.71, minSpeed: 2.6, maxSpeed: 13.41, sprintFactor: 1.6,
    hint: 'on foot, at a run',
  },
  wagon: {
    label: 'Wagon', verb: 'Driving to', eyeOffset: 0.5, turnRate: 70,
    settingKey: 'wagonSpeed', defaultSpeed: 7.15, maxSpeed: 17.88, sprintFactor: 1,
    hint: 'a light wagon',
  },
  horse: {
    label: 'Horse', verb: 'Riding to', eyeOffset: 0.75, turnRate: 90,
    settingKey: 'horseSpeed', defaultSpeed: 11.18, maxSpeed: 35.76, sprintFactor: 1.7,
    // The gait figures are a canter's (2 strides a second at 6.5 m/s); updateBob
    // scales the beat with the speed the slider actually set.
    bob: { hz: 2.0, amp: 0.06, sprintHz: 1.6, sprintAmp: 0.09, atSpeed: 6.5 },
    hint: 'in the saddle; Shift to gallop',
  },
  fly: {
    label: 'Fly', verb: 'Flying to', turnRate: 120,
    /** Cruise height in metres for a trip of `d` metres: low for a hop, higher
     *  for a crossing so the whole route is in view. */
    cruise: (d) => Math.min(80, Math.max(20, 12 + 0.15 * d)),
    hint: 'up, across and down to the door',
  },
};

/** T-2945: the defaults the paces had before 2026-10-20, keyed by setting. */
export const OLD_PACE_DEFAULTS = Object.freeze({ speed: 1.45, runSpeed: 3.4, wagonSpeed: 3.6, horseSpeed: 6.5 });
/** The version of the pace defaults a stored settings object was last read under. */
export const PACE_DEFAULTS_VERSION = 2;

/**
 * T-2945: the HUD stores its whole settings object on any change, so most returning
 * visitors carry the old pace defaults without ever having touched a slider. The first
 * time a stored object is read under the new defaults, a speed EXACTLY equal to its old
 * default is read as no choice and dropped (the new default applies); anything else is
 * the visitor's own and is kept. `paceDefaults` records that the reading was made, so a
 * slider later set to one of those figures on purpose is kept too. Pure: returns a copy.
 */
export function migratePaceDefaults(saved) {
  const s = { ...(saved && typeof saved === 'object' ? saved : {}) };
  if (Number(s.paceDefaults) >= PACE_DEFAULTS_VERSION) return s;
  for (const [key, old] of Object.entries(OLD_PACE_DEFAULTS)) if (Number(s[key]) === old) delete s[key];
  s.paceDefaults = PACE_DEFAULTS_VERSION;
  return s;
}

/** The slider value for a pace: the stored setting, clamped to the pace's range. */
export function paceSpeed(pace, settings = {}) {
  const p = typeof pace === 'string' ? PACES[pace] : pace;
  if (!p?.settingKey) return null;
  const stored = Number(settings[p.settingKey]);
  const base = Number.isFinite(stored) ? stored : p.defaultSpeed;
  return clamp(base, p.minSpeed ?? 0.5, p.maxSpeed);
}

/**
 * A person on foot. The walker owns the model; these are the numbers it walks by,
 * and they live here because travel.js WRITES them (the pace sliders compose speed,
 * sprint and eye height in one place) while a pure estimate only reads them. Both
 * hold the one object walker.js re-exports, so a write is seen everywhere.
 */
export const WALK = {
  eyeHeight: 1.68,      // m — mid-19th-century adult male mean was near 1.72 m
  radius: 0.34,         // m — shoulder half-width for the push-out
  speed: 4.47,          // m/s — the Walk pace's default (T-2945; travel.js applyPace sets it)
  sprintSpeed: 10.19,   // m/s — that × the walk's sprint factor
  stepUp: 0.35,         // m — the plank-walk rule
  pitchLimit: 85 * (Math.PI / 180),
};

export const FLY = {
  speed: 14,            // m/s — crossing a 640 m scene should take ~45 s, not 7 min
  sprintSpeed: 46,
  riseSpeed: 11,        // m/s vertical, independent of look direction
  minClearance: 1.2,    // m above the terrain; you may skim, not tunnel
  maxAltitude: 900,     // m above the datum water surface
  /**
   * Horizontal speed multiplies with height. At 300 m up, ground features
   * subtend so little angle that 14 m/s reads as not moving at all — the
   * classic flight-sim problem where altitude makes the world feel frozen.
   * Capped so it stays controllable near the top.
   */
  altitudeGain: (y) => Math.min(6, 1 + Math.max(0, y) / 90),
};
