/**
 * Move (T-2651, DESIGN §07 M6): what the one picker and the one slider show.
 *
 * One picker — Walk, Run, Wagon, Horse, Fly — and one slider for the mode picked.
 * The slider's range, value and named speed follow the mode; Fly has no slider (its
 * speed grows with height). Go to's own question sits under it: Teleport, Ride there
 * (along the streets at the mode above) or Fly over, stored as the travel mode the
 * controller already reads ('instantly', a ground pace, or 'fly').
 *
 * Pure, so a test reads it without a page; js/hud.js paints what it returns.
 */
import { PACES, gaitName } from './travel.js';
import { formatSpeed } from './units.js';

/** The ground modes, in the picker's order and the pace chip's cycle. */
export const GROUND_MODES = ['walk', 'run', 'wagon', 'horse'];
/** Every choice on the picker. */
export const MOVE_MODES = [...GROUND_MODES, 'fly'];

export const groundPace = (pace) => (GROUND_MODES.includes(pace) ? pace : 'walk');
export const nextPace = (pace) => GROUND_MODES[(GROUND_MODES.indexOf(groundPace(pace)) + 1) % GROUND_MODES.length];

/** Go to's stored travel mode as one of the three choices under the picker. */
export function arriveOf(travelMode) {
  if (!(travelMode in PACES) || travelMode === 'instantly') return 'instantly';
  return travelMode === 'fly' ? 'fly' : 'ride';
}

/** The travel mode a choice stores: Ride there rides at the ground pace. */
export const travelModeFor = (arrive, pace) => (arrive === 'ride' ? groundPace(pace) : arrive === 'fly' ? 'fly' : 'instantly');

/** A ground pace's slider value: its stored setting, clamped to its range. */
export function speedOf(pace, settings = {}) {
  const p = PACES[groundPace(pace)];
  const v = Number(settings[p.settingKey]);
  return Math.max(p.minSpeed ?? 0.5, Math.min(p.maxSpeed, Number.isFinite(v) ? v : p.defaultSpeed));
}

/** "rattling along · 24.6 mph": the name of a speed, then the speed. */
export const speedWords = (pace, v, units) => `${gaitName(groundPace(pace), v)} · ${formatSpeed(v, units)}`;

/**
 * Everything the Move section shows, from the settings and whether you are flying:
 * `{ mode, pace, slider: { shown, key, min, max, value, label, readout }, note, arrive }`.
 */
export function moveView(settings = {}, { flying = false } = {}) {
  const pace = groundPace(settings.pace);
  const mode = flying ? 'fly' : pace;
  const p = PACES[pace];
  const value = speedOf(pace, settings);
  const cap = formatSpeed(p.maxSpeed, settings.units);
  const note = mode === 'fly'
    ? 'The higher you are, the faster you go.'
    : p.sprintFactor > 1
      ? `Shift hurries you: ×${p.sprintFactor}, never past the slider's top of ${cap}.`
      : `A wagon has no faster gear: Shift does nothing, and the slider tops out at ${cap}.`;
  return {
    mode,
    pace,
    slider: {
      shown: mode !== 'fly',
      key: p.settingKey,
      min: p.minSpeed ?? 0.5,
      max: p.maxSpeed,
      value,
      label: `${p.label} speed`,
      readout: speedWords(pace, value, settings.units),
    },
    note,
    arrive: arriveOf(settings.travelMode),
  };
}
