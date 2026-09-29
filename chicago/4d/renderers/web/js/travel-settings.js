/** Shared motion settings: the controller and pure estimates read one definition. */
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const ARRIVAL_SETTLE_S = 0.5;

export const PACES = {
  instantly: { label: 'Instantly', hint: 'straight there, as before' },
  // Each ground pace has its own slider (T-0823): `settingKey` names the stored
  // value, `defaultSpeed` is what a fresh visitor gets, `maxSpeed` is the slider's
  // ceiling — 20, 30 and 60 mph, the owner's figures — and `sprintFactor` is what
  // Shift does to it (a run on foot, nothing on a wagon, a gallop on a horse),
  // capped at the ceiling. The gait names a slider shows are in GAITS below.
  walk: {
    label: 'Walk', verb: 'Walking to', eyeOffset: 0, turnRate: 150,
    settingKey: 'speed', defaultSpeed: 1.45, maxSpeed: 8.94, sprintFactor: 2.28,
    hint: 'your own two feet',
  },
  wagon: {
    label: 'Wagon', verb: 'Driving to', eyeOffset: 0.5, turnRate: 70,
    settingKey: 'wagonSpeed', defaultSpeed: 3.6, maxSpeed: 13.41, sprintFactor: 1,
    hint: 'a light wagon',
  },
  horse: {
    label: 'Horse', verb: 'Riding to', eyeOffset: 0.75, turnRate: 90,
    settingKey: 'horseSpeed', defaultSpeed: 6.5, maxSpeed: 26.82, sprintFactor: 1.7,
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

/** The slider value for a pace: the stored setting, clamped to the pace's range. */
export function paceSpeed(pace, settings = {}) {
  const p = typeof pace === 'string' ? PACES[pace] : pace;
  if (!p?.settingKey) return null;
  const stored = Number(settings[p.settingKey]);
  const base = Number.isFinite(stored) ? stored : p.defaultSpeed;
  return clamp(base, 0.5, p.maxSpeed);
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
  speed: 1.45,          // m/s — an unhurried walk
  sprintSpeed: 3.3,     // m/s — a jog, not a sprint
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
